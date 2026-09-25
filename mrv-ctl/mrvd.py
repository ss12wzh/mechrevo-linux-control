#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mrvd — 机械革命苍龙系列 Linux 控制台守护进程

功能: 性能模式 (EC 0x0751) / 电池限充 (EC 0x07B9) / RGB 键盘灯 / INOU 平台开关 /
      独显直连 Mux (DGPS/IGPS, 需重启生效) / 遥测

风扇: 手动强冷 + 高温自动强冷 (0x0751 bit6 全速模式, 迟滞), 其余时间由 EC 固件曲线控制

安全:
  - EC 写白名单 + 基线 + 写后读回; 写入走 WKBC 命令通道; /proc/acpi/call 串行化 (线程锁 + flock)
  - IPC 按 SO_PEERCRED 鉴权: 读状态任何人, 写操作需 root 或 sudo/mrv 组
"""

import fcntl
import grp
import json
import os
import pwd
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

RUN_DIR = "/run/mrvd"
SOCK_PATH = f"{RUN_DIR}/mrvd.sock"
ACPI_LOCK_FILE = f"{RUN_DIR}/acpi_call.lock"
STATE_DIR = "/var/lib/mrvd"
STATE_FILE = f"{STATE_DIR}/state.json"
BASELINE_FILE = f"{STATE_DIR}/baseline.json"
ACPI_CALL = "/proc/acpi/call"

# EC 寄存器白名单 (0x0741 bit0 由内核 uniwill_laptop 管理, 不在此列)
# 0x0751: DSDT 称 bit4 TBME (狂暴) / bit7 UFME (办公静音), 都为 0 即平衡; 上游驱动称 MANUAL_FAN_CTRL
# (bit4 TURBO / bit5 HIGH / bit6 BOOST / bit7 USER). EC 固件据此切换 CPU 功耗墙与 NVPCF 平台参数,
# 并自行触发 SCI (_Q83/_Q84/_Q9C) 通知 NVIDIA 驱动 (docs/perf/2-ab.jsonl, 3-downward.jsonl)
EC_REG_PROFILE = 0x0751
EC_REG_CHARGE = 0x07B9
EC_WHITELIST = {EC_REG_PROFILE, EC_REG_CHARGE}

PROFILE_BITS = {"office": 0xA0, "balanced": 0x00, "boost": 0x10}
PROFILE_CLEAR = 0xB0
FAN_BOOST_BIT = 0x40        # 全速模式; 本机唯一实测有效的风扇写控制 (docs/probe/fan-experiment-3-direct.log)

GUARD_POLL = 2.0            # 温度采样周期 (秒)
GUARD_DEFAULT = {"enabled": True, "on": 88, "off": 78}   # 高温自动强冷: 超过 on 开启, 回落到 off 关闭
PWM_MAX = 200               # multi_intensity 各通道上限

# EC 按档位给出的 NVPCF 平台参数 (只读, 单位 W; DSDT 中乘 8 后写入 NPCF)
EC_REG_CTWA = 0x0788        # GPU cTGP 基础功耗 -> NPCF.ACBT
EC_REG_DBAP = 0x07D5        # Dynamic Boost -> NPCF.AMAT
EC_REG_ETPP = 0x07F7        # 平台总处理功耗 TPP -> NPCF.ATPP

# 各档 CPU 封装功耗墙实测值 (W). EC 非自定义模式下 APL1/APL2 (0x0783/0x0784) 为 0, 功耗墙由固件内部决定,
# 无寄存器可读, 只能按机型记录实测结果 (docs/perf/*.jsonl, openssl 32 进程满载稳态)
MEASURED_CPU_PPT = {
    "CANGLONG Series-M6DR55": {"office": 45, "balanced": 87, "boost": 130},
}

LED_DIR = "/sys/class/leds/uniwill:multicolor:status"
INOU_DIR = "/sys/devices/platform/INOU0000:00"
HWMON_DIR = "/sys/class/hwmon"
# 允许客户端开关的 INOU sysfs 属性 (白名单, 其他属性如 ctgp_offset 不对外开放)
TOGGLES = ("fn_lock", "super_key_enable", "breathing_in_suspend", "touchpad_toggle_enable")

log = lambda msg: print(f"[mrvd] {time.strftime('%H:%M:%S')} {msg}", flush=True)


# ================================================================ acpi_call EC
# /proc/acpi/call 是全局单缓冲: 写表达式与读结果之间不能被任何其他调用插入,
# 进程内用线程锁, 跨进程 (探测/实验脚本) 用 flock
_acpi_lock = threading.Lock()


def ec_call(expr: str) -> str:
    if not os.path.exists(ACPI_CALL):
        return "Error: acpi_call 未加载"
    with _acpi_lock:
        os.makedirs(RUN_DIR, exist_ok=True)
        with open(ACPI_LOCK_FILE, "a") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            with open(ACPI_CALL, "w") as f:
                f.write(expr)
            with open(ACPI_CALL) as f:
                return f.read().replace("\x00", "").strip()


def ec_read(addr: int):
    out = ec_call(f"\\_SB.INOU.ECRR 0x{addr:04X}")
    if out.startswith("0x"):
        try:
            return int(out, 16) & 0xFF
        except ValueError:
            return None
    return None


def has_wkbc() -> bool:
    """DSDT 是否提供 \\_SB.AMW0.WKBC (OEM WMI 写 EC 的命令通道)"""
    try:
        with open("/sys/firmware/acpi/tables/DSDT", "rb") as f:
            return b"WKBC" in f.read()
    except OSError:
        return False


EC_VIA_WKBC = False


def ec_write(addr: int, value: int) -> bool:
    """优先走 WKBC 命令通道 (由 EC 固件执行写入, 与 OEM 软件一致);
    MMIO 直写只改共享 RAM, EC 固件不一定感知 (风扇表实验已证实)"""
    if addr not in EC_WHITELIST:
        log(f"REFUSE 非白名单 EC 地址 0x{addr:04X}")
        return False
    if EC_VIA_WKBC:
        out = ec_call(f"\\_SB.AMW0.WKBC 0x{addr & 0xFF:02X} 0x{addr >> 8:02X} 0x{value:02X} 0x00")
        return not out.startswith("Error")
    out = ec_call(f"\\_SB.INOU.ECRW 0x{addr:04X} 0x{value:02X}")
    return out.startswith("0x")


def ec_write_verified(addr: int, value: int, mask: int = 0xFF) -> bool:
    if not ec_write(addr, value):
        return False
    time.sleep(0.05)
    back = ec_read(addr)
    return back is not None and (back & mask) == (value & mask)


def acpi_method(path: str, arg: str = None):
    """调用任意 ACPI 方法 (用于 DGPS/IGPS)"""
    expr = f"{path} {arg}" if arg is not None else path
    out = ec_call(expr)
    return out


# ================================================================ 状态持久化
def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def save_baseline(key, value):
    base = _load_json(BASELINE_FILE)
    base.setdefault(key, value)
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(base, f, indent=2)


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def load_state():
    return _load_json(STATE_FILE)


_state_lock = threading.Lock()


def state_update(**kv):
    with _state_lock:
        st = load_state()
        st.update(kv)
        save_state(st)
        return st


# ================================================================ hwmon
def find_uniwill_hwmon():
    for d in os.listdir(HWMON_DIR):
        try:
            with open(f"{HWMON_DIR}/{d}/name") as f:
                if f.read().strip() == "uniwill":
                    return f"{HWMON_DIR}/{d}"
        except OSError:
            continue
    return ""


HW = ""


def hw_read(name):
    try:
        with open(f"{HW}/{name}") as f:
            return f.read().strip()
    except OSError:
        return None


# ================================================================ 性能模式
def get_profile():
    v = ec_read(EC_REG_PROFILE)
    if v is None:
        return "unknown"
    bits = v & PROFILE_CLEAR
    return {0xA0: "office", 0x10: "boost", 0x00: "balanced"}.get(
        bits, f"custom(0x{v:02X})")


# 档位联动: 功耗墙由 EC 固件随档位位切换; 这里只附带 CPU EPP 与灯效.
# EPP 不影响满载功耗 (A/B 实测), 只影响轻负载时的频率策略与能耗
PROFILE_ACTIONS = {
    "office": {"epp": "power", "kbd_brightness": 30, "kbd_rainbow": False},
    "balanced": {"epp": "balance_performance", "kbd_brightness": 80, "kbd_rainbow": False},
    "boost": {"epp": "performance", "kbd_brightness": 150, "kbd_rainbow": True},
}


def apply_epp(value: str) -> bool:
    """设置 CPU 能效偏好 (amd-pstate-epp / intel_pstate)"""
    base = "/sys/devices/system/cpu"
    ok = False
    for d in os.listdir(base):
        if not d.startswith("cpu") or not d[3:].isdigit():
            continue
        p = f"{base}/{d}/cpufreq/energy_performance_preference"
        if os.path.exists(p):
            try:
                with open(p, "w") as f:
                    f.write(value)
                ok = True
            except OSError:
                pass
    return ok


def apply_profile_actions(name: str):
    """应用档位联动 (CPU/灯效)"""
    act = PROFILE_ACTIONS.get(name)
    if not act:
        return
    if act.get("epp"):
        apply_epp(act["epp"])
    kbd_set(brightness=act.get("kbd_brightness", 0),
            effect=("rainbow" if act.get("kbd_rainbow") else "solid"))
    log(f"档位联动已应用: {name} (EPP={act.get('epp')})")


# set_profile 与物理键轮询共享"最近一次已联动的档位", 避免同一次切换联动两遍;
# 同一把锁也串行化所有对 0x0751 的读改写 (档位位与风扇强冷位同在一个寄存器)
_profile_lock = threading.RLock()
_profile_seen = None


def set_profile(name):
    global _profile_seen
    if name not in PROFILE_BITS:
        return {"ok": False, "error": f"未知档位 {name}"}
    with _profile_lock:
        cur = ec_read(EC_REG_PROFILE)
        if cur is None:
            return {"ok": False, "error": "EC 读失败"}
        save_baseline("profile_reg", f"0x{cur:02X}")
        target = (cur & ~PROFILE_CLEAR & 0xFF) | PROFILE_BITS[name]
        ok = ec_write_verified(EC_REG_PROFILE, target, PROFILE_CLEAR)
        if ok:
            _profile_seen = name
            state_update(profile=name)
            apply_profile_actions(name)
    log(f"性能模式 -> {name}: {'OK' if ok else 'FAIL'}")
    return {"ok": ok, "profile": name if ok else None}


def profile_watch_loop():
    """物理键检测: 固件自行切换 EC 档位而不通知 Linux, 这里轮询感知并联动"""
    global _profile_seen
    while True:
        try:
            with _profile_lock:
                cur = get_profile()
                if cur != _profile_seen:
                    if _profile_seen is not None and cur in PROFILE_BITS:
                        log(f"检测到档位变化 {_profile_seen} -> {cur} (物理键/外部), 应用联动")
                        state_update(profile=cur)
                        apply_profile_actions(cur)
                    _profile_seen = cur
        except Exception as e:
            log(f"WARN profile watch: {e}")
        time.sleep(3)


# ================================================================ 风扇
# 本机实测 (docs/probe/fan-experiment-*.log): hwmon pwm 只读; EC 自定义风扇表、0x1804/0x1809 直写、
# FAN_LEVEL 均无效; 唯一有效的写控制是 0x0751 bit6 全速模式, 且须经 WKBC 命令通道写入
def fan_boost_get():
    v = ec_read(EC_REG_PROFILE)
    return None if v is None else bool(v & FAN_BOOST_BIT)


def fan_boost_set(on: bool) -> bool:
    with _profile_lock:
        cur = ec_read(EC_REG_PROFILE)
        if cur is None:
            return False
        target = (cur | FAN_BOOST_BIT) if on else (cur & ~FAN_BOOST_BIT & 0xFF)
        if target == cur:
            return True
        return ec_write_verified(EC_REG_PROFILE, target, FAN_BOOST_BIT)


class ThermalGuard(threading.Thread):
    """用户强冷 + 高温自动强冷 (迟滞); 任一为真即置全速模式, 否则交还 EC 固件曲线.
    每个周期都按期望值校正 EC 状态, 休眠唤醒或外部改写后自动恢复."""

    def __init__(self):
        super().__init__(daemon=True)
        st = load_state()
        self.stop_evt = threading.Event()
        self.lock = threading.Lock()
        self.user_boost = bool(st.get("fan_boost"))
        self.guard = {**GUARD_DEFAULT, **(st.get("fan_guard") or {})}
        self.auto_active = False
        self.ec_boost = None

    def current_temp(self):
        vals = [float(v) / 1000 for n in ("temp1_input", "temp2_input") if (v := hw_read(n))]
        return max(vals) if vals else None

    def wanted(self):
        return self.user_boost or self.auto_active

    def apply(self):
        want = self.wanted()
        cur = fan_boost_get()
        if cur is not None and cur != want:
            ok = fan_boost_set(want)
            log(f"风扇全速模式 -> {'开' if want else '关'}: {'OK' if ok else 'FAIL'}")
            cur = fan_boost_get()
        self.ec_boost = cur

    def run(self):
        while not self.stop_evt.is_set():
            try:
                temp = self.current_temp()
                with self.lock:
                    g = self.guard
                    if not g["enabled"] or temp is None:
                        if self.auto_active:
                            log("高温自动强冷已停用")
                        self.auto_active = False
                    elif not self.auto_active and temp >= g["on"]:
                        self.auto_active = True
                        log(f"!! 温度 {temp:.0f}°C >= {g['on']}°C, 自动开启强冷")
                    elif self.auto_active and temp <= g["off"]:
                        self.auto_active = False
                        log(f"温度回落到 {temp:.0f}°C <= {g['off']}°C, 交还 EC 固件曲线")
                    self.apply()
            except Exception as e:
                log(f"WARN ThermalGuard: {e}")
            self.stop_evt.wait(GUARD_POLL)

    def set_user(self, on: bool) -> dict:
        with self.lock:
            self.user_boost = on
            state_update(fan_boost=on)
            self.apply()
            ok = self.ec_boost == self.wanted()
        return {"ok": ok, "mode": self.mode(), **({} if ok else {"error": "EC 写入失败"})}

    def set_guard(self, enabled=None, on=None, off=None) -> dict:
        with self.lock:
            g = dict(self.guard)
            if enabled is not None:
                g["enabled"] = bool(enabled)
            if on is not None:
                g["on"] = int(on)
            if off is not None:
                g["off"] = int(off)
            if not (60 <= g["off"] < g["on"] <= 95):
                return {"ok": False, "error": "需满足 60 <= 关闭温度 < 开启温度 <= 95"}
            self.guard = g
            state_update(fan_guard=g)
        return {"ok": True, "fan_guard": g}

    def mode(self):
        if self.user_boost:
            return "boost"
        return "auto-boost" if self.auto_active else "auto"

    def shutdown(self):
        """退出时撤销自动强冷 (仍在高温则保留, 宁可吵不可热); 用户强冷保持原样"""
        self.stop_evt.set()
        with self.lock:
            temp = self.current_temp()
            if self.auto_active and not self.user_boost and (temp is None or temp < self.guard["on"]):
                self.auto_active = False
                self.apply()
                log("退出: 撤销自动强冷")


# ================================================================ RGB 灯效
def led_write(name, value):
    try:
        with open(f"{LED_DIR}/{name}", "w") as f:
            f.write(value)
        return True
    except OSError as e:
        log(f"WARN led 写 {name}: {e}")
        return False


def kbd_set(brightness=None, rgb=None, effect=None) -> dict:
    out = {"ok": True}
    inou = INOU_DIR
    if effect is not None:
        # effect: solid=单色(关闭固件彩虹) rainbow=流畅彩虹 off=全灭
        p = f"{inou}/rainbow_animation"
        if not os.path.exists(p):
            out["ok"], out["error"] = False, "固件不支持彩虹动画"
        else:
            if effect == "rainbow":
                with open(p, "w") as f:
                    f.write("1")
                out["effect"] = "rainbow"
            elif effect == "solid":
                with open(p, "w") as f:
                    f.write("0")
                out["effect"] = "solid"
            elif effect == "off":
                with open(p, "w") as f:
                    f.write("0")
                if led_write("brightness", "0"):
                    out["effect"] = "off"
                else:
                    out["ok"] = False
    if rgb is not None:
        if effect != "rainbow":          # 彩虹模式下固件接管颜色, 写了会闪回
            r, g, b = (max(0, min(int(x), PWM_MAX)) for x in rgb)
            if led_write("multi_intensity", f"{r} {g} {b}"):
                out["rgb"] = [r, g, b]
            else:
                out["ok"] = False
    if brightness is not None:
        try:
            with open(f"{LED_DIR}/max_brightness") as f:
                mx = int(f.read().strip())
            v = max(0, min(int(brightness), mx))
            if led_write("brightness", str(v)):
                out["brightness"] = v
                out["max"] = mx
            else:
                out["ok"] = False
        except OSError as e:
            out["ok"], out["error"] = False, str(e)
    return out


def toggle_sysfs(name: str, enable: bool) -> dict:
    """INOU 平台小开关 (fn_lock/super_key/breathing 等)"""
    if name not in TOGGLES:
        return {"ok": False, "error": f"不允许的开关 {name}"}
    p = f"{INOU_DIR}/{name}"
    if not os.path.exists(p):
        return {"ok": False, "error": f"不支持 {name}"}
    try:
        with open(p, "w") as f:
            f.write("1" if enable else "0")
        return {"ok": True, name: enable}
    except OSError as e:
        return {"ok": False, "error": str(e)}


# ================================================================ 机型能力探测
def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    name = line.split(":", 1)[1].strip()
                    return name.split(" w/ ")[0].replace(" with Radeon Graphics", "")
    except OSError:
        pass
    return ""


def gpu_name() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=8).stdout.strip()
        name = out.splitlines()[0] if out else ""
        return name.replace("NVIDIA GeForce ", "").replace(" GPU", "")
    except Exception:
        return ""


def probe_features() -> dict:
    """40/50 系多机型兼容: 探测本机支持的硬件能力, UI 按此自适应"""
    inou = INOU_DIR
    dmi = "/sys/class/dmi/id"
    def dmi_read(n):
        try:
            with open(f"{dmi}/{n}") as f:
                return f.read().strip()
        except OSError:
            return ""
    feats = {
        "product": dmi_read("product_name") or "Uniwill Platform",
        "vendor": dmi_read("sys_vendor"),
        "barebone_id": ec_read(0x0740),
        "profile": ec_read(EC_REG_PROFILE) is not None,
        "charge": ec_read(EC_REG_CHARGE) is not None,
        "fan": bool(HW),
        "rgb": os.path.exists(f"{LED_DIR}/multi_intensity"),
        "rainbow": os.path.exists(f"{inou}/rainbow_animation"),
        "breathing": os.path.exists(f"{inou}/breathing_in_suspend"),
        "fn_lock": os.path.exists(f"{inou}/fn_lock"),
        "super_key": os.path.exists(f"{inou}/super_key_enable"),
        "logo_light": False,       # lightbar 寄存器需实测, 默认隐藏
        "fan_boost": ec_read(EC_REG_PROFILE) is not None,
        "ec_channel": "wkbc" if EC_VIA_WKBC else "mmio",
        "cpu_model": cpu_model(),
        "gpu_name": gpu_name(),
        "cpu_max_mhz": (v := read_text("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"))
                       and int(v) // 1000,
        "cpu_ppt_table": cpu_ppt_table(),
    }
    # mux 能力: DGPS 查询成功即支持
    out = acpi_method(f"{MUX_PATH}.DGPS")
    feats["mux"] = not out.startswith("Error") and out in ("0x0", "0x1", "0x2", "0xaa", "0x55")
    return feats


# ================================================================ 离电关灯
class AcLedGuard:
    """可选: 拔电自动关背光, 插电恢复"""
    def __init__(self):
        self.enabled = load_state().get("ac_led_off", False)
        self.last_ac = None

    def poll(self):
        if not self.enabled:
            self.last_ac = None
            return
        try:
            with open("/sys/class/power_supply/AC0/online") as f:
                ac = f.read().strip() == "1"
        except OSError:
            return
        if self.last_ac is not None and ac != self.last_ac:
            if ac:
                kbd_set(brightness=load_state().get("kbd_restore", 100))
                log("插电: 恢复背光")
            else:
                cur = read_text(f"{LED_DIR}/brightness")
                if cur and cur.isdigit():
                    state_update(kbd_restore=int(cur))
                kbd_set(brightness=0)
                log("离电: 关闭背光")
        self.last_ac = ac


ac_led_guard = None


# ================================================================ Mux
MUX_PATH = "\\_SB.PCI0.SBRG.EC0"


def mux_query() -> dict:
    out = acpi_method(f"{MUX_PATH}.DGPS")
    mapping = {"0x0": "dGPU(独显直连)", "0x1": "iGPU(混合输出)", "0x2": "查询成功但状态未知"}
    return {"ok": not out.startswith("Error"),
            "raw": out, "state": mapping.get(out, out)}


def mux_switch(mode: int) -> dict:
    """mode: 1=独显直连(PEGP 常开), 0=混合(可下电)"""
    out = acpi_method(f"{MUX_PATH}.IGPS", str(mode))
    ok = not out.startswith("Error")
    return {"ok": ok, "raw": out,
            "note": "切换后需重启系统完成显示输出切换" if ok else "ACPI 调用失败"}


# ================================================================ 限充
def set_charge_limit(pct):
    if not (20 <= pct <= 100):
        return {"ok": False, "error": "限充阈值需在 20-100 之间"}
    cur = ec_read(EC_REG_CHARGE)
    if cur is None:
        return {"ok": False, "error": "EC 读失败"}
    save_baseline("charge_reg", f"0x{cur:02X}")
    ok = ec_write_verified(EC_REG_CHARGE, pct & 0x7F, 0x7F)
    if ok:
        state_update(charge_limit=pct)
    return {"ok": ok, "limit": pct}


# ================================================================ 实时遥测
import glob as _glob

RAPL_PATH = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj"
_last_energy = None
_last_energy_t = 0.0


def cpu_info():
    """CPU 频率 (MHz) + 封装功耗 (RAPL 差分)"""
    freqs = []
    for p in _glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"):
        try:
            with open(p) as f:
                freqs.append(int(f.read().strip()) / 1000)     # kHz -> MHz
        except (OSError, ValueError):
            continue
    info = {"freq_avg_mhz": None, "freq_max_mhz": None, "power_w": None}
    if freqs:
        info["freq_avg_mhz"] = round(sum(freqs) / len(freqs))
        info["freq_max_mhz"] = round(max(freqs))

    global _last_energy, _last_energy_t
    try:
        with open(RAPL_PATH) as f:
            e = int(f.read().strip())
        now = time.time()
        if _last_energy is not None and now > _last_energy_t:
            duj = e - _last_energy
            if duj >= 0:                                        # 计数器回绕保护
                info["power_w"] = round(duj / (now - _last_energy_t) / 1e6, 1)
        _last_energy, _last_energy_t = e, now
    except (OSError, ValueError):
        pass
    return info


_gpu_limits = {"t": 0.0, "v": {}}
_nv_pci = None


def nvidia_pci_dir():
    global _nv_pci
    if _nv_pci is None:
        _nv_pci = ""
        for p in _glob.glob("/sys/bus/pci/devices/*"):
            try:
                with open(f"{p}/vendor") as f, open(f"{p}/class") as g:
                    if f.read().strip() == "0x10de" and g.read().strip().startswith("0x03"):
                        _nv_pci = p
                        break
            except OSError:
                continue
    return _nv_pci


def gpu_suspended() -> bool:
    """独显 runtime suspend 时调用 nvidia-smi 会把它唤醒, 耗电"""
    p = nvidia_pci_dir()
    if not p:
        return False
    try:
        with open(f"{p}/power/runtime_status") as f:
            return f.read().strip() == "suspended"
    except OSError:
        return False


def gpu_info():
    """GPU 功耗 + 显存 + 频率 + 利用率"""
    if gpu_suspended():
        return {"suspended": True}
    out = {}
    try:
        csv = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,clocks.sm,"
             "utilization.gpu,power.draw,power.max_limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5).stdout.strip()
        f = [x.strip() for x in csv.split(",")]
        if len(f) >= 6:
            out.update({"mem_used_mb": float(f[0]), "mem_total_mb": float(f[1]),
                        "clock_mhz": float(f[2]), "util_pct": float(f[3]),
                        "draw_w": float(f[4]), "max_limit_w": float(f[5])})
    except Exception:
        pass
    if not out:
        return {"error": "nvidia-smi 不可用"}

    # 功耗墙上/下限用 -q 补齐 (CSV 的 power.limit 在笔记本上恒为 N/A); 变化很慢, 缓存 60s
    now = time.time()
    if now - _gpu_limits["t"] > 60:
        try:
            q = subprocess.run(["nvidia-smi", "-q", "-d", "POWER"],
                               capture_output=True, text=True, timeout=8).stdout
            def grab(key):
                for line in q.splitlines():
                    if key in line:
                        try:
                            return float(line.split(":")[1].strip().split()[0])
                        except (IndexError, ValueError):
                            return None
            _gpu_limits["v"] = {"current_limit_w": grab("Current Power Limit"),
                                "max_limit_w": grab("Max Power Limit")}
            _gpu_limits["t"] = now
        except Exception:
            pass
    for k, v in _gpu_limits["v"].items():
        if out.get(k) is None:
            out[k] = v
    return out


def read_text(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def charge_limit():
    """0x07B9 低 7 位为限充百分比, 0 表示未设置 (充满); 读失败返回 None"""
    v = ec_read(EC_REG_CHARGE)
    if v is None:
        return None
    return (v & 0x7F) or 100


def cpu_ppt_table() -> dict:
    board = read_text("/sys/class/dmi/id/board_name") or ""
    return next((v for k, v in MEASURED_CPU_PPT.items() if board.startswith(k)), {})


def platform_info(profile: str) -> dict:
    return {"tpp_w": ec_read(EC_REG_ETPP), "db_w": ec_read(EC_REG_DBAP), "ctgp_base_w": ec_read(EC_REG_CTWA),
            "cpu_ppt_w": FEATURES_CACHE.get("cpu_ppt_table", {}).get(profile)}


def status():
    profile = get_profile()
    st = {
        "profile": profile,
        "platform": platform_info(profile),
        "gpu": gpu_info(),
        "cpu": cpu_info(),
        "fan1_rpm": (v := hw_read("fan1_input")) and int(v),
        "fan2_rpm": (v := hw_read("fan2_input")) and int(v),
        "pwm1": (v := hw_read("pwm1")) and int(v),
        "cpu_temp": (v := hw_read("temp1_input")) and float(v) / 1000,
        "gpu_temp": (v := hw_read("temp2_input")) and float(v) / 1000,
        "charge_limit_pct": charge_limit(),
        "fan_mode": guard.mode(),
        "fan_boost_ec": guard.ec_boost,
        "fan_guard": guard.guard,
        "overheat_guard": guard.auto_active,
        "kbd_rgb": read_text(f"{LED_DIR}/multi_intensity"),
        "kbd_brightness": read_text(f"{LED_DIR}/brightness"),
        "kbd_rainbow": read_text(f"{INOU_DIR}/rainbow_animation") == "1",
        "toggles": {n: read_text(f"{INOU_DIR}/{n}") == "1" for n in TOGGLES
                    if os.path.exists(f"{INOU_DIR}/{n}")},
        "battery": battery_info(),
        "ac_led_off": ac_led_guard.enabled if ac_led_guard else False,
        "features": FEATURES_CACHE,
    }
    return st


def battery_info():
    out = {}
    for key, name in (("capacity_pct", "capacity"), ("status", "status"), ("cycles", "cycle_count")):
        try:
            with open(f"/sys/class/power_supply/BAT0/{name}") as f:
                v = f.read().strip()
            out[key] = int(v) if key != "status" else v
        except (OSError, ValueError):
            out[key] = None
    try:
        with open("/sys/class/power_supply/AC0/online") as f:
            out["ac_online"] = f.read().strip() == "1"
    except OSError:
        out["ac_online"] = None
    return out


# ================================================================ IPC
def handle_cmd(cmd):
    op = cmd.get("op")
    if op == "status":
        return status()
    if op == "profile":
        return set_profile(cmd.get("value", ""))
    if op == "charge":
        return set_charge_limit(int(cmd.get("value", 0)))
    if op == "kbd":
        return kbd_set(cmd.get("brightness"), cmd.get("rgb"), cmd.get("effect"))
    if op == "fan":
        val = cmd.get("value", "auto")
        if val in ("auto", "boost"):
            return guard.set_user(val == "boost")
        return {"ok": False, "error": "fan 取值: auto | boost (本机不支持自定义曲线)"}
    if op == "fan_guard":
        return guard.set_guard(cmd.get("enabled"), cmd.get("on"), cmd.get("off"))
    if op == "mux":
        sub = cmd.get("value", "query")
        if sub == "query":
            return mux_query()
        if sub == "igpu":
            return {"ok": False, "error": "集显模式 (独显完全断电) 本机尚未实现"}
        if sub in ("dgpu", "standard"):
            if not cmd.get("confirm"):
                return {"ok": False,
                        "error": "Mux 切换会下电/上电独显, 请加 confirm:true 并准备重启"}
            return mux_switch(1 if sub == "dgpu" else 0)
        return {"ok": False, "error": "mux 子命令: query|dgpu|standard"}
    if op == "toggle":
        return toggle_sysfs(cmd.get("name", ""), bool(cmd.get("value")))
    if op == "ac_led_off":
        enable = bool(cmd.get("value"))
        state_update(ac_led_off=enable)
        ac_led_guard.enabled = enable
        return {"ok": True, "ac_led_off": enable}
    return {"ok": False, "error": f"未知操作 {op}"}


# 写操作仅允许 root 或这些组的成员 (按 /etc/group 判断, 新加组无需重新登录)
WRITE_GROUPS = ("sudo", "admin", "wheel", "mrv")


def is_read_only(cmd) -> bool:
    op = cmd.get("op")
    return op == "status" or (op == "mux" and cmd.get("value", "query") == "query")


def uid_may_write(uid: int) -> bool:
    if uid == 0:
        return True
    try:
        pw = pwd.getpwuid(uid)
    except KeyError:
        return False
    for name in WRITE_GROUPS:
        try:
            g = grp.getgrnam(name)
        except KeyError:
            continue
        if pw.pw_gid == g.gr_gid or pw.pw_name in g.gr_mem:
            return True
    return False


def recv_json(conn):
    buf = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            raise ValueError("请求不完整")
        buf += chunk
        try:
            return json.loads(buf.decode())
        except ValueError:
            if len(buf) > 1 << 20:
                raise ValueError("请求过大")


def handle_conn(conn):
    try:
        conn.settimeout(10)
        creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        _pid, uid, _gid = struct.unpack("3i", creds)
        try:
            cmd = recv_json(conn)
            if not isinstance(cmd, dict):
                raise ValueError("请求格式错误")
            if not is_read_only(cmd) and not uid_may_write(uid):
                resp = {"ok": False, "error": "权限不足: 需要 root 或 sudo/mrv 组成员"}
                log(f"REFUSE uid={uid} op={cmd.get('op')}")
            else:
                resp = handle_cmd(cmd)
        except Exception as e:
            resp = {"ok": False, "error": str(e)}
        conn.sendall(json.dumps(resp).encode())
    except OSError:
        pass
    finally:
        conn.close()


def serve():
    os.makedirs(RUN_DIR, exist_ok=True)
    if os.path.exists(SOCK_PATH):
        os.unlink(SOCK_PATH)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    os.chmod(SOCK_PATH, 0o666)
    srv.listen(8)
    log(f"IPC 就绪: {SOCK_PATH}")
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle_conn, args=(conn,), daemon=True).start()


# ================================================================ main
guard = None
FEATURES_CACHE = {}


def ac_poll_loop():
    """离电关灯轮询 (10s 周期)"""
    while True:
        try:
            ac_led_guard.poll()
        except Exception as e:
            log(f"WARN AcLedGuard: {e}")
        time.sleep(10)


def restore_on_boot():
    st = load_state()
    time.sleep(3)
    prof = st.get("profile")
    if prof in PROFILE_BITS:
        r = set_profile(prof)
        log(f"开机恢复性能模式 {prof}: {r.get('ok')}")
    if st.get("fan_curve"):
        state_update(fan_curve=None)     # 旧版用户态曲线的残留状态


def main():
    global HW, guard, ac_led_guard, EC_VIA_WKBC
    if os.geteuid() != 0:
        print("mrvd 需要 root 运行", file=sys.stderr)
        sys.exit(1)
    HW = find_uniwill_hwmon()
    if not HW:
        log("WARN 未找到 uniwill hwmon")
    else:
        log(f"hwmon: {HW}")
    EC_VIA_WKBC = has_wkbc()
    log(f"EC 写入通道: {'WKBC 命令通道' if EC_VIA_WKBC else 'MMIO 直写 (DSDT 无 WKBC)'}")

    guard = ThermalGuard()
    ac_led_guard = AcLedGuard()

    def on_term(sig, frame):
        log(f"收到信号 {sig}, 收尾...")
        guard.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    FEATURES_CACHE.update(probe_features())
    log(f"机型能力: {json.dumps(FEATURES_CACHE, ensure_ascii=False)}")

    guard.start()
    threading.Thread(target=restore_on_boot, daemon=True).start()
    threading.Thread(target=ac_poll_loop, daemon=True).start()
    threading.Thread(target=profile_watch_loop, daemon=True).start()
    serve()


if __name__ == "__main__":
    main()
