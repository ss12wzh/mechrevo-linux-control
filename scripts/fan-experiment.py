#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uniwill EC 自定义风扇表受控写入实验 (需 root)

用法:
  sudo fan-experiment.py run [--via wmi|mmio] [--log 文件]   自定义风扇表实验
  sudo fan-experiment.py direct [--log 文件]                   全速模式 + 直接写 PWM 实验
  sudo fan-experiment.py manual [--log 文件]                   置 0x0741 bit0 (AP 接管) 后重试风扇表 / 直接 PWM
  sudo fan-experiment.py table --speed N [--log 文件]          AP 接管 + 单调单区间表, 探测转速字段刻度
  sudo fan-experiment.py real --speed N --split 0|1 [--log]   AP 接管 + 16 段连续曲线
  sudo fan-experiment.py level [--log 文件]                    0x0751 USER 模式下切换 FAN_LEVEL 7/4/1
  sudo fan-experiment.py restore [--delay 秒]                 按基线恢复 (看门狗/手动)

直接控制 (tuxedo 的旧式 fan control):
  0x0751 bit6 置 1 进入全速模式, EC 停止自动曲线; 0x1804 / 0x1809 为两个风扇的 PWM (0-200,
  hwmon pwm = 值 * 255 / 200); 地址超过 0xFFF, 只能走 WKBC/RECM 命令通道; 清 bit6 即交还 EC

写入通道:
  mmio  \\_SB.INOU.ECRW, 直接改 EC 共享 RAM (0xFED50000), EC 固件不感知 — 第 1 次实验证明对风扇表无效
  wmi   \\_SB.AMW0.WKBC, 填 EC0 命令寄存器 (LDAT/HDAT/CMDL/CMDH) 置 WFLG, 由 EC 固件执行写入;
        即 tuxedo uniwill_write_ec_ram 经 WMI 走到的同一段 ACPI 代码
  读回一律用 MMIO (与命令通道 RECM 读数已核对一致)

寄存器 (依据 tuxedo-drivers uniwill_keyboard.h 的 universal EC fan control):
  0x078E bit6  能力位 (本机已探测为 1)
  0x0751 bit6  全速模式, 必须为 0
  0x07C5 bit7  两个风扇分别使用两张表
  0x07C6 bit2  启用 0x0Fxx 自定义表
  0x0F00/0x0F10/0x0F20  CPU 风扇 16 区间: 结束温度 / 起始温度 / 转速 (0-200)
  0x0F30/0x0F40/0x0F50  GPU 风扇同上

安全:
  - 基线 (所有将改动的位与整张表) 先存盘到 BASELINE_FILE
  - 独立会话的看门狗进程 WATCHDOG_S 秒后无条件恢复, 主进程崩溃/被杀也会执行
  - 第一次写满速表 (只会更凉), 第二次写不低于当前转速的中速表
  - 任一时刻温度 >= TEMP_ABORT 立即恢复; 每次写入读回校验, 不一致立即恢复
  - 与 mrvd 共用 /run/mrvd/acpi_call.lock, 不与守护进程交错访问 /proc/acpi/call
"""

import fcntl
import json
import os
import signal
import subprocess
import sys
import time

ACPI_CALL = "/proc/acpi/call"
LOCK_FILE = "/run/mrvd/acpi_call.lock"
BASELINE_FILE = "/var/lib/mrvd/fan-table-baseline.json"

REG_CAP, CAP_BIT = 0x078E, 1 << 6
REG_MODE, FULLFAN_BIT = 0x0751, 1 << 6
REG_SPLIT, SPLIT_BIT = 0x07C5, 1 << 7
REG_ENABLE, ENABLE_BIT = 0x07C6, 1 << 2
CPU_END, CPU_START, CPU_SPEED = 0x0F00, 0x0F10, 0x0F20
GPU_END, GPU_START, GPU_SPEED = 0x0F30, 0x0F40, 0x0F50
TABLE = list(range(0x0F00, 0x0F60))
REG_FAN1, REG_FAN2 = 0x1804, 0x1809
REG_AP_OEM, MANUAL_BIT = 0x0741, 1 << 0    # 上游 uniwill_laptop 初始化时置位, 卸载时清除
RPM_FLOOR = 1500                           # 低于此转速视为停转风险, 立即中止
USER_BIT, LEVEL_BITS = 1 << 7, 0x07        # 0x0751: FAN_MODE_USER / FAN_LEVEL_MASK (上游驱动定义)
LEVEL_MASK = USER_BIT | LEVEL_BITS

WATCHDOG_S = 90
TEMP_ABORT = 90.0
FULL = 200
MID = 170            # 不低于当前固件转速 (当前 pwm 约 130-165)
OBSERVE_S = 12


VIA = "wmi"


class Abort(Exception):
    pass


# ------------------------------------------------------------ EC 访问
def acpi(expr):
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    with open(LOCK_FILE, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        with open(ACPI_CALL, "w") as f:
            f.write(expr)
        with open(ACPI_CALL) as f:
            return f.read().replace("\x00", "").strip()


def rd(addr):
    if addr > 0xFFF:
        expr = f"\\_SB.PCI0.SBRG.EC0.RECM 0x{addr & 0xFF:02X} 0x{addr >> 8:02X}"
    else:
        expr = f"\\_SB.INOU.ECRR 0x{addr:04X}"
    out = ""
    for _ in range(3):
        out = acpi(expr)
        if out.startswith("0x"):
            return int(out, 16) & 0xFF
        time.sleep(0.02)
    raise Abort(f"读 0x{addr:04X} 失败: {out}")


def wr(addr, val):
    if VIA == "wmi":
        # WKBC 成功时不改 AC00, 返回值可能残留上次失败的 0xFE 标记, 只以读回为准
        out = acpi(f"\\_SB.AMW0.WKBC 0x{addr & 0xFF:02X} 0x{addr >> 8:02X} 0x{val:02X} 0x00")
        if out.startswith("Error"):
            raise Abort(f"WKBC 写 0x{addr:04X} 失败: {out}")
    else:
        if addr > 0xFFF:
            raise Abort(f"MMIO 通道不能访问 0x{addr:04X}")
        out = acpi(f"\\_SB.INOU.ECRW 0x{addr:04X} 0x{val:02X}")
        if not out.startswith("0x"):
            raise Abort(f"写 0x{addr:04X} 失败: {out}")
    back = None
    for _ in range(5):
        time.sleep(0.01)
        back = rd(addr)
        if back == val:
            return
    raise Abort(f"读回不一致 0x{addr:04X}: 写 0x{val:02X} 读 0x{back:02X}")


def set_bit(addr, bit, on):
    cur = rd(addr)
    new = (cur | bit) if on else (cur & ~bit & 0xFF)
    if new != cur:
        wr(addr, new)


# ------------------------------------------------------------ 基线 / 恢复
def snapshot():
    return {"time": time.strftime("%F %T"), "via": VIA,
            "split": rd(REG_SPLIT), "enable": rd(REG_ENABLE),
            "table": [rd(a) for a in TABLE]}


def restore(base):
    """只动实验改过的位. 直接控制: 清全速模式位交还 EC; 风扇表: 先关自定义表, 再还原双表位, 最后回写表"""
    if base.get("kind") == "direct":
        set_bit(REG_MODE, FULLFAN_BIT, bool(base["mode"] & FULLFAN_BIT))
        return
    if base.get("kind") == "level":
        cur = rd(REG_MODE)
        want = (cur & ~LEVEL_MASK & 0xFF) | (base["mode"] & LEVEL_MASK)
        if want != cur:
            wr(REG_MODE, want)
        return
    set_bit(REG_ENABLE, ENABLE_BIT, bool(base["enable"] & ENABLE_BIT))
    set_bit(REG_SPLIT, SPLIT_BIT, bool(base["split"] & SPLIT_BIT))
    for a, v in zip(TABLE, base["table"]):
        if rd(a) != v:
            wr(a, v)
    if base.get("kind") == "manual":
        set_bit(REG_MODE, FULLFAN_BIT, bool(base["mode"] & FULLFAN_BIT))
        set_bit(REG_AP_OEM, MANUAL_BIT, bool(base["ap_oem"] & MANUAL_BIT))


def verify(base):
    if base.get("kind") == "direct":
        mode = rd(REG_MODE)
        return (mode & FULLFAN_BIT) == (base["mode"] & FULLFAN_BIT), {"mode": mode}
    if base.get("kind") == "level":
        mode = rd(REG_MODE)
        return (mode & LEVEL_MASK) == (base["mode"] & LEVEL_MASK), {"mode": f"0x{mode:02X}"}
    now = snapshot()
    ok = (now["table"] == base["table"]
          and (now["enable"] & ENABLE_BIT) == (base["enable"] & ENABLE_BIT)
          and (now["split"] & SPLIT_BIT) == (base["split"] & SPLIT_BIT))
    if base.get("kind") == "manual":
        now["mode"], now["ap_oem"] = rd(REG_MODE), rd(REG_AP_OEM)
        ok = ok and (now["mode"] & FULLFAN_BIT) == (base["mode"] & FULLFAN_BIT) \
            and (now["ap_oem"] & MANUAL_BIT) == (base["ap_oem"] & MANUAL_BIT)
    return ok, now


# ------------------------------------------------------------ 风扇表
def write_table(cpu_speed, gpu_speed, gpu_end=120, filler=FULL):
    """tuxedo 的单区间布局: 区间 0 覆盖 0-115°C 用给定转速, 其余 15 个区间为 116°C 以上的占位
    (tuxedo 原样 GPU 区间 0 结束温度为 120, 与后续区间不单调)"""
    rows = {CPU_END: 115, CPU_START: 0, CPU_SPEED: cpu_speed,
            GPU_END: gpu_end, GPU_START: 0, GPU_SPEED: gpu_speed}
    for addr, val in rows.items():
        if rd(addr) != val:
            wr(addr, val)
    for i in range(1, 16):
        for end, start, speed in ((CPU_END, CPU_START, CPU_SPEED), (GPU_END, GPU_START, GPU_SPEED)):
            for addr, val in ((end + i, 116 + i), (start + i, 115 + i), (speed + i, filler)):
                if rd(addr) != val:
                    wr(addr, val)


# ------------------------------------------------------------ 观测
def hwmon_dir():
    for d in sorted(os.listdir("/sys/class/hwmon")):
        p = f"/sys/class/hwmon/{d}"
        try:
            with open(f"{p}/name") as f:
                if f.read().strip() == "uniwill":
                    return p
        except OSError:
            pass
    raise Abort("找不到 uniwill hwmon")


def sample(hw):
    def rv(n):
        try:
            with open(f"{hw}/{n}") as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return None
    t1, t2 = rv("temp1_input"), rv("temp2_input")
    return {"t": round(time.time(), 1),
            "cpu": t1 and t1 / 1000, "gpu": t2 and t2 / 1000,
            "fan1": rv("fan1_input"), "fan2": rv("fan2_input"),
            "pwm1": rv("pwm1"), "pwm2": rv("pwm2")}


def observe(hw, phase, seconds, log):
    rows = []
    for _ in range(seconds):
        s = sample(hw)
        s["phase"] = phase
        rows.append(s)
        log(f"  [{phase}] CPU {s['cpu']}°C GPU {s['gpu']}°C  fan {s['fan1']}/{s['fan2']} RPM  pwm {s['pwm1']}/{s['pwm2']}",
            s)
        if max(s["cpu"] or 0, s["gpu"] or 0) >= TEMP_ABORT:
            raise Abort(f"温度 {max(s['cpu'], s['gpu'])}°C 达到中止阈值")
        if phase != "恢复后" and min(s["fan1"] or 0, s["fan2"] or 0) < RPM_FLOOR:
            raise Abort(f"风扇转速 {s['fan1']}/{s['fan2']} RPM 低于 {RPM_FLOOR}, 疑似停转")
        time.sleep(1)
    return rows


def avg(rows, key, last=None):
    vals = [r[key] for r in (rows[-last:] if last else rows) if r[key] is not None]
    return sum(vals) / len(vals) if vals else 0


# ------------------------------------------------------------ 主流程
def make_logger(log_path):
    logf = open(log_path, "a")

    def log(msg, data=None):
        line = f"{time.strftime('%T')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        if data is not None:
            logf.write("   " + json.dumps(data, ensure_ascii=False) + "\n")
        logf.flush()
    return log


def arm(base, log):
    """基线存盘 + 启动独立会话看门狗 + 信号转为 Abort; 返回看门狗进程"""
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(base, f)
    log(f"写入通道 {VIA}; 基线已保存 {BASELINE_FILE}", base)
    dog = subprocess.Popen([sys.executable, os.path.abspath(__file__), "restore", "--delay", str(WATCHDOG_S)],
                           start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"看门狗 pid={dog.pid}: {WATCHDOG_S}s 后无条件恢复")

    def on_signal(sig, frame):
        raise Abort(f"收到信号 {sig}")
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    return dog


def disarm(base, dog, hw, log, result):
    log("== 恢复基线")
    try:
        restore(base)
        ok, now = verify(base)
        result["restored"] = ok
        log(f"   读回校验: {'一致' if ok else '不一致!'} {now if base.get('kind') == 'direct' else ''}")
    except Exception as e:
        log(f"!! 恢复失败, 看门狗将在到期时重试: {e}")
    else:
        dog.kill()
        log("   看门狗已取消")
    try:
        observe(hw, "恢复后", 8, log)
    except Abort as e:
        log(f"!! {e}")
    log(f"结果: {json.dumps(result, ensure_ascii=False)}")


def pwm_of(ec_val):
    return ec_val * 255 / 200


def run_direct(log_path):
    log = make_logger(log_path)
    if rd(REG_MODE) & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = {"kind": "direct", "time": time.strftime("%F %T"), "via": VIA,
            "mode": rd(REG_MODE), "fan1": rd(REG_FAN1), "fan2": rd(REG_FAN2)}
    dog = arm(base, log)
    result = {"fullfan_effective": None, "pwm170_follows": None, "pwm130_follows": None, "restored": None}
    try:
        log("== 基线观测")
        r0 = observe(hw, "基线", 4, log)

        log("== 阶段 1: 置 0x0751 bit6 (全速模式)")
        set_bit(REG_MODE, FULLFAN_BIT, True)
        r1 = observe(hw, "全速模式", 8, log)
        result["fullfan_effective"] = avg(r1, "fan1", last=3) > avg(r0, "fan1") + 800
        log(f"   主风扇 {avg(r0, 'fan1'):.0f} -> {avg(r1, 'fan1', last=3):.0f} RPM, "
            f"EC 0x1804={rd(REG_FAN1)} 0x1809={rd(REG_FAN2)}")

        for key, val in (("pwm170_follows", 170), ("pwm130_follows", 130)):
            log(f"== 写 0x1804 / 0x1809 = {val} (期望 hwmon pwm≈{pwm_of(val):.0f})")
            wr(REG_FAN1, val)
            wr(REG_FAN2, val)
            r = observe(hw, f"PWM {val}", 10, log)
            got = avg(r, "pwm1", last=3)
            result[key] = abs(got - pwm_of(val)) <= 12
            log(f"   hwmon pwm1 末 3 秒均值 {got:.0f}, 主风扇 {avg(r, 'fan1', last=3):.0f} RPM, "
                f"EC 0x1804={rd(REG_FAN1)}: {'跟随' if result[key] else '未跟随'}")
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def run_manual(log_path):
    log = make_logger(log_path)
    if rd(REG_MODE) & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = snapshot()
    base.update(kind="manual", mode=rd(REG_MODE), ap_oem=rd(REG_AP_OEM))
    dog = arm(base, log)
    result = {"manual_bit_side_effect": None, "table_full_effective": None, "table_mid_follows": None,
              "direct_170_follows": None, "restored": None}
    try:
        log("== 基线观测")
        r0 = observe(hw, "基线", 4, log)
        base_rpm = avg(r0, "fan1")

        log(f"== 阶段 A: 置 0x0741 bit0 (当前 0x{base['ap_oem']:02X})")
        set_bit(REG_AP_OEM, MANUAL_BIT, True)
        ra = observe(hw, "AP 接管", 5, log)
        result["manual_bit_side_effect"] = round(avg(ra, "fan1", last=2) - base_rpm)

        log("== 阶段 B: 写满速表并启用 (WMI)")
        set_bit(REG_SPLIT, SPLIT_BIT, True)
        write_table(FULL, FULL)
        set_bit(REG_ENABLE, ENABLE_BIT, True)
        rb = observe(hw, "表满速", 10, log)
        full_rpm = avg(rb, "fan1", last=3)
        result["table_full_effective"] = full_rpm > base_rpm + 800
        log(f"   主风扇 {base_rpm:.0f} -> {full_rpm:.0f} RPM")

        if result["table_full_effective"]:
            log(f"== 阶段 C: 写中速表 ({MID})")
            write_table(MID, MID)
            rc = observe(hw, "表中速", 10, log)
            mid_rpm = avg(rc, "fan1", last=3)
            result["table_mid_follows"] = mid_rpm < full_rpm - 300
            log(f"   主风扇 {full_rpm:.0f} -> {mid_rpm:.0f} RPM")
        else:
            log("== 阶段 D: 关自定义表, 直接写 0x1804/0x1809 = 170 (不开全速模式)")
            set_bit(REG_ENABLE, ENABLE_BIT, False)
            for reg in (REG_FAN1, REG_FAN2):
                acpi(f"\\_SB.AMW0.WKBC 0x{reg & 0xFF:02X} 0x{reg >> 8:02X} 0xAA 0x00")
            log(f"   写后立即读 0x1804={rd(REG_FAN1)} 0x1809={rd(REG_FAN2)}")
            rd_ = observe(hw, "直写170", 8, log)
            got = avg(rd_, "pwm1", last=3)
            result["direct_170_follows"] = abs(got - pwm_of(170)) <= 12
            log(f"   hwmon pwm1 末 3 秒 {got:.0f} (期望 {pwm_of(170):.0f}), 0x1804={rd(REG_FAN1)}")
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def write_table_real(speed):
    """16 个连续真实区间: 区间 i 覆盖 [20+6i, 26+6i), 最后一个到 116°C; 两张表同值"""
    for i in range(16):
        for end, start, spd in ((CPU_END, CPU_START, CPU_SPEED), (GPU_END, GPU_START, GPU_SPEED)):
            for addr, val in ((start + i, 20 + 6 * i), (end + i, 26 + 6 * i), (spd + i, speed)):
                if rd(addr) != val:
                    wr(addr, val)


def run_real(log_path, speed, split):
    """AP 接管位 + 16 段真实曲线, 可选是否分离两张表"""
    log = make_logger(log_path)
    if rd(REG_MODE) & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = snapshot()
    base.update(kind="manual", mode=rd(REG_MODE), ap_oem=rd(REG_AP_OEM))
    dog = arm(base, log)
    result = {"speed_value": speed, "split": split, "cpu_pwm": None, "gpu_pwm": None, "restored": None}
    try:
        log("== 基线观测")
        observe(hw, "基线", 4, log)
        set_bit(REG_AP_OEM, MANUAL_BIT, True)
        log(f"== 写 16 段连续曲线 (20-116°C, 转速 {speed}), 双表分离={split}; 启用")
        set_bit(REG_SPLIT, SPLIT_BIT, bool(split))
        write_table_real(speed)
        set_bit(REG_ENABLE, ENABLE_BIT, True)
        r = observe(hw, f"曲线{speed}", 15, log)
        result["cpu_pwm"], result["gpu_pwm"] = round(avg(r, "pwm1", last=3)), round(avg(r, "pwm2", last=3))
        log(f"   末 3 秒 hwmon pwm: CPU {result['cpu_pwm']} GPU {result['gpu_pwm']} (期望 {pwm_of(speed):.0f}); "
            f"EC 0x1804={rd(REG_FAN1)} 0x1809={rd(REG_FAN2)}")
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def run_level(log_path, levels):
    """0x0751 USER 模式下改 FAN_LEVEL (低 3 位), 观察风扇是否按等级变化"""
    log = make_logger(log_path)
    mode = rd(REG_MODE)
    if mode & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = {"kind": "level", "time": time.strftime("%F %T"), "via": VIA, "mode": mode}
    dog = arm(base, log)
    result = {"base_mode": f"0x{mode:02X}", "levels": {}, "restored": None}
    try:
        log(f"== 基线观测 (0x0751=0x{mode:02X})")
        r0 = observe(hw, "基线", 4, log)
        result["levels"]["base"] = round(avg(r0, "pwm1"))
        for lv in levels:
            val = (rd(REG_MODE) & ~LEVEL_BITS & 0xFF) | USER_BIT | lv
            log(f"== FAN_LEVEL={lv}: 写 0x0751=0x{val:02X}")
            wr(REG_MODE, val)
            r = observe(hw, f"等级{lv}", 6, log)
            result["levels"][lv] = {"pwm1": round(avg(r, "pwm1", last=2)), "pwm2": round(avg(r, "pwm2", last=2)),
                                    "fan1": round(avg(r, "fan1", last=2))}
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def run_table(log_path, speed):
    """AP 接管位 + 单调单区间表, 用指定转速值探测转速字段刻度"""
    log = make_logger(log_path)
    if rd(REG_MODE) & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = snapshot()
    base.update(kind="manual", mode=rd(REG_MODE), ap_oem=rd(REG_AP_OEM))
    dog = arm(base, log)
    result = {"speed_value": speed, "cpu_pwm": None, "gpu_pwm": None, "restored": None}
    try:
        log("== 基线观测")
        observe(hw, "基线", 4, log)
        set_bit(REG_AP_OEM, MANUAL_BIT, True)
        log(f"== 写单调单区间表, 区间 0 转速 {speed}, 占位区间同值; 启用")
        set_bit(REG_SPLIT, SPLIT_BIT, True)
        write_table(speed, speed, gpu_end=115, filler=speed)
        set_bit(REG_ENABLE, ENABLE_BIT, True)
        r = observe(hw, f"表{speed}", 15, log)
        result["cpu_pwm"], result["gpu_pwm"] = round(avg(r, "pwm1", last=3)), round(avg(r, "pwm2", last=3))
        log(f"   末 3 秒 hwmon pwm: CPU {result['cpu_pwm']} GPU {result['gpu_pwm']} "
            f"(若刻度 0-200 期望 {pwm_of(speed):.0f}, 若 0-100 期望 {min(255, speed * 255 / 100):.0f}); "
            f"EC 0x1804={rd(REG_FAN1)} 0x1809={rd(REG_FAN2)}")
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def run(log_path):
    log = make_logger(log_path)
    if not rd(REG_CAP) & CAP_BIT:
        sys.exit("0x078E bit6 = 0, 本机不支持通用 EC 风扇控制, 不做实验")
    if rd(REG_MODE) & FULLFAN_BIT:
        sys.exit("0x0751 全速模式位已置, 不做实验")
    hw = hwmon_dir()
    base = snapshot()
    dog = arm(base, log)

    result = {"full_effective": None, "mid_follows": None, "restored": None}
    try:
        log("== 基线观测")
        r0 = observe(hw, "基线", 4, log)

        log(f"== 阶段 1: 写满速表 ({FULL}/200) 并启用")
        set_bit(REG_MODE, FULLFAN_BIT, False)
        set_bit(REG_SPLIT, SPLIT_BIT, True)
        write_table(FULL, FULL)
        set_bit(REG_ENABLE, ENABLE_BIT, True)
        log(f"   已写入: split=0x{rd(REG_SPLIT):02X} enable=0x{rd(REG_ENABLE):02X}")
        r1 = observe(hw, "满速", OBSERVE_S, log)
        base_rpm, full_rpm = avg(r0, "fan1"), avg(r1, "fan1", last=4)
        result["full_effective"] = full_rpm > base_rpm + 800
        log(f"   主风扇 {base_rpm:.0f} -> {full_rpm:.0f} RPM: {'生效' if result['full_effective'] else '未见明显变化'}")

        if result["full_effective"]:
            log(f"== 阶段 2: 写中速表 ({MID}/200)")
            write_table(MID, MID)
            r2 = observe(hw, "中速", OBSERVE_S, log)
            mid_rpm = avg(r2, "fan1", last=4)
            result["mid_follows"] = mid_rpm < full_rpm - 300
            log(f"   主风扇 {full_rpm:.0f} -> {mid_rpm:.0f} RPM: {'跟随表变化' if result['mid_follows'] else '未跟随'}")
    except Abort as e:
        log(f"!! 中止: {e}")
    finally:
        disarm(base, dog, hw, log, result)
    return 0 if result["restored"] else 1


def watchdog(delay):
    global VIA
    time.sleep(delay)
    with open(BASELINE_FILE) as f:
        base = json.load(f)
    VIA = base.get("via", "wmi")
    for _ in range(5):
        try:
            restore(base)
            if verify(base)[0]:
                return 0
        except Abort:
            pass
        time.sleep(1)
    return 1


def main():
    global VIA
    if os.geteuid() != 0:
        sys.exit("需要 root")
    args = sys.argv[1:]
    if not args or args[0] not in ("run", "direct", "manual", "table", "real", "level", "restore"):
        sys.exit(__doc__)
    if args[0] == "restore":
        delay = float(args[args.index("--delay") + 1]) if "--delay" in args else 0
        sys.exit(watchdog(delay))
    if "--via" in args:
        VIA = args[args.index("--via") + 1]
        if VIA not in ("wmi", "mmio"):
            sys.exit("--via 只能是 wmi 或 mmio")
    log_path = args[args.index("--log") + 1] if "--log" in args else f"fan-experiment-{time.strftime('%Y%m%d-%H%M%S')}.log"
    if args[0] == "direct":
        VIA = "wmi"
        sys.exit(run_direct(log_path))
    if args[0] == "manual":
        VIA = "wmi"
        sys.exit(run_manual(log_path))
    if args[0] == "table":
        VIA = "wmi"
        speed = int(args[args.index("--speed") + 1]) if "--speed" in args else 100
        if not 60 <= speed <= 200:
            sys.exit("--speed 限定 60-200")
        sys.exit(run_table(log_path, speed))
    if args[0] == "real":
        VIA = "wmi"
        speed = int(args[args.index("--speed") + 1]) if "--speed" in args else 150
        split = int(args[args.index("--split") + 1]) if "--split" in args else 1
        if not 120 <= speed <= 200:
            sys.exit("--speed 限定 120-200 (不低于当前固件转速)")
        sys.exit(run_real(log_path, speed, split))
    if args[0] == "level":
        VIA = "wmi"
        sys.exit(run_level(log_path, [7, 4, 1]))
    sys.exit(run(log_path))


if __name__ == "__main__":
    main()
