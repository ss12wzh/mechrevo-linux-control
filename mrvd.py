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
import re
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

import mrvmodel

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
# 键盘 RGB / 亮度 (上游 uniwill-acpi / tuxedo uniwill_leds; 须走 WKBC, ECRW 对本机无效)
EC_REG_BIOS_OEM_2 = 0x0782
EC_REG_RGB_TRIGGER = 0x0767
EC_REG_RGB_RED = 0x0769
EC_REG_RGB_GREEN = 0x076A
EC_REG_RGB_BLUE = 0x076B
EC_REG_KBD_STATUS = 0x078C
EC_BIT_ENABLE_CHINA_MODE = 0x40   # BIOS_OEM_2: 启用键盘灯相关中国区逻辑
EC_BIT_RGB_APPLY = 0x20           # TRIGGER: 应用 RGB 颜色
EC_BIT_RGB_RAINBOW = 0x80         # TRIGGER: 彩虹动画
EC_BIT_KBD_APPLY = 0x10           # KBD_STATUS: 应用亮度
EC_KBD_BRIGHTNESS_SHIFT = 5       # KBD_STATUS bit7:5 = 亮度档 (0-4)
EC_KBD_BRIGHTNESS_LEVELS = 4      # force=1 时与上游 kbd_led_max_brightness 一致
EC_WHITELIST = {
    EC_REG_PROFILE, EC_REG_CHARGE,
    EC_REG_BIOS_OEM_2, EC_REG_RGB_TRIGGER,
    EC_REG_RGB_RED, EC_REG_RGB_GREEN, EC_REG_RGB_BLUE, EC_REG_KBD_STATUS,
}

PROFILE_BITS = {"office": 0xA0, "balanced": 0x00, "boost": 0x10}
PROFILE_CLEAR = 0xB0
FAN_BOOST_BIT = 0x40        # 全速模式; 本机唯一实测有效的风扇写控制 (docs/probe/fan-experiment-3-direct.log)

GUARD_POLL = 2.0            # 温度采样周期 (秒)
GUARD_DEFAULT = {"enabled": True, "on": 88, "off": 78}   # 高温自动强冷: 超过 on 开启, 回落到 off 关闭
PWM_MAX = 200               # 对外亮度/颜色 API 上限 (GUI 仍用 0-200)
KBD_RGB_EC_MAX = 50         # EC RGB 通道实际上限 (与上游 uniwill KBD_LED_MAX_INTENSITY 一致)

# EC 按档位给出的 NVPCF 平台参数 (只读, 单位 W; DSDT 中乘 8 后写入 NPCF)
EC_REG_CTWA = 0x0788        # GPU cTGP 基础功耗 -> NPCF.ACBT
EC_REG_DBAP = 0x07D5        # Dynamic Boost -> NPCF.AMAT
EC_REG_ETPP = 0x07F7        # 平台总处理功耗 TPP -> NPCF.ATPP
# CPU 功耗墙: EC 非自定义模式下 APL1/APL2 (0x0783/0x0784) 为 0, 由固件内部决定, 无寄存器可读;
# 数值来自本机校准 (mrvctl calibrate) 或已验证机型档案 (data/models.json), 见 mrvmodel

# 状态灯条 (lightbar), 不是键盘背光; 仅作旧路径探测备用
LED_STATUS = "/sys/class/leds/uniwill:multicolor:status"
# 上游较新内核才会注册; 本机 7.0 uniwill 模块无此节点, 键盘灯改走 EC/WKBC
LED_KBD = "/sys/class/leds/uniwill:multicolor:kbd_backlight"
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


EC_VIA_WKBC = False         # DSDT 提供 \_SB.AMW0.WKBC (OEM WMI 写 EC 的命令通道) 时启用


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
    # 离电时 EC 可能清 bit7 只留 bit5 (0x20) / 仅留 bit7 (0x80), 都属于静音档
    return {0xA0: "office", 0x80: "office", 0x20: "office",
            0x10: "boost", 0x00: "balanced"}.get(
        bits, f"custom(0x{v:02X})")


# 档位联动: 功耗墙由 EC 固件随档位位切换; 这里附带 CPU EPP / 睿频与灯效.
# EPP 不影响满载功耗 (A/B 实测); 静音档关睿频让轻负载下空闲功耗 46 -> 39.5 W (后台 ToDesk 编码时实测)
PROFILE_ACTIONS = {
    "office": {"epp": "power", "cpu_boost": False, "kbd_brightness": 30, "kbd_rainbow": False},
    "balanced": {"epp": "balance_performance", "cpu_boost": True, "kbd_brightness": 80, "kbd_rainbow": False},
    "boost": {"epp": "performance", "cpu_boost": True, "kbd_brightness": 150, "kbd_rainbow": True},
}
CPU_BOOST_PATH = "/sys/devices/system/cpu/cpufreq/boost"


def apply_cpu_boost(on: bool) -> bool:
    try:
        with open(CPU_BOOST_PATH, "w") as f:
            f.write("1" if on else "0")
        return True
    except OSError:
        return False


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


def apply_profile_actions(name: str, kbd=True):
    """应用档位联动 (CPU/灯效); kbd=False 时不动键盘灯, 保留用户手动调过的亮度"""
    act = PROFILE_ACTIONS.get(name)
    if not act:
        return
    if act.get("epp"):
        apply_epp(act["epp"])
    if "cpu_boost" in act:
        apply_cpu_boost(act["cpu_boost"])
    if kbd:
        kbd_set(brightness=act.get("kbd_brightness", 0),
                effect=("rainbow" if act.get("kbd_rainbow") else "solid"))
    log(f"档位联动已应用: {name} (EPP={act.get('epp')}, 睿频={'开' if act.get('cpu_boost', True) else '关'})")


# set_profile 与物理键轮询共享"最近一次已联动的档位", 避免同一次切换联动两遍;
# 同一把锁也串行化所有对 0x0751 的读改写 (档位位与风扇强冷位同在一个寄存器)
_profile_lock = threading.RLock()
_profile_seen = None


def set_profile(name, link=True, kbd=True):
    """link=False: 只切 EC 档位位, 不做任何联动 (校准用); kbd=False: 联动 CPU 但不动键盘灯 (开机恢复用)"""
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
            if link:
                apply_profile_actions(name, kbd=kbd)
    log(f"性能模式 -> {name}: {'OK' if ok else 'FAIL'}")
    return {"ok": ok, "profile": name if ok else None}


def profile_watch_loop():
    """物理键检测: 固件自行切换 EC 档位而不通知 Linux, 这里轮询感知并联动"""
    global _profile_seen
    while True:
        if sleeping.is_set():
            time.sleep(1)
            continue
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
            if sleeping.is_set():
                self.stop_evt.wait(GUARD_POLL)
                continue
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
def _kbd_ensure_china_mode():
    """上游 uniwill_kbd_led_init 会置 ENABLE_CHINA_MODE; 否则部分机型不响应键盘灯写入"""
    cur = ec_read(EC_REG_BIOS_OEM_2)
    if cur is None:
        return False
    if cur & EC_BIT_ENABLE_CHINA_MODE:
        return True
    return ec_write(EC_REG_BIOS_OEM_2, cur | EC_BIT_ENABLE_CHINA_MODE)


def _brightness_to_level(brightness: int) -> int:
    """API 0-200 → EC 亮度档 0-4"""
    b = max(0, min(int(brightness), PWM_MAX))
    if b <= 0:
        return 0
    return max(1, min(EC_KBD_BRIGHTNESS_LEVELS,
                      round(b * EC_KBD_BRIGHTNESS_LEVELS / PWM_MAX)))


def _level_to_brightness(level: int) -> int:
    level = max(0, min(int(level), EC_KBD_BRIGHTNESS_LEVELS))
    return 0 if level <= 0 else round(level * PWM_MAX / EC_KBD_BRIGHTNESS_LEVELS)


def _rgb_api_to_ec(v) -> int:
    return max(0, min(KBD_RGB_EC_MAX, round(int(v) * KBD_RGB_EC_MAX / PWM_MAX)))


def _rgb_ec_to_api(v) -> int:
    return max(0, min(PWM_MAX, round(int(v) * PWM_MAX / KBD_RGB_EC_MAX)))


def _kbd_write_brightness(level: int) -> bool:
    """写亮度档; 清 POWER_OFF, 置 APPLY (与上游 uniwill_kbd_led_write_brightness 一致)"""
    level = max(0, min(int(level), EC_KBD_BRIGHTNESS_LEVELS))
    cur = ec_read(EC_REG_KBD_STATUS)
    if cur is None:
        return False
    # 保留 bit0 (白灯机型标志) 与 turbo 位, 清 bit1 POWER_OFF
    low = (cur & 0x0D)
    new = low | (level << EC_KBD_BRIGHTNESS_SHIFT) | EC_BIT_KBD_APPLY
    return ec_write(EC_REG_KBD_STATUS, new)


def _kbd_apply_rgb(r_api, g_api, b_api) -> bool:
    """API 色域 → EC 0-50, 写三通道并脉冲 APPLY。0,0,0 会被固件当成恢复默认, 改成 1,1,1。"""
    r, g, b = _rgb_api_to_ec(r_api), _rgb_api_to_ec(g_api), _rgb_api_to_ec(b_api)
    if r == g == b == 0:
        r = g = b = 1
    if not (ec_write(EC_REG_RGB_RED, r) and ec_write(EC_REG_RGB_GREEN, g)
            and ec_write(EC_REG_RGB_BLUE, b)):
        return False
    # APPLY 为脉冲位, 写 1 即可; 不要先整寄存器清 0 (会挤掉固件 RGB 模式)
    return ec_write(EC_REG_RGB_TRIGGER, EC_BIT_RGB_APPLY)


def kbd_read() -> dict:
    """从 EC 读键盘灯状态; RGB 换算回 GUI 0-200 色域"""
    st = ec_read(EC_REG_KBD_STATUS)
    r, g, b = ec_read(EC_REG_RGB_RED), ec_read(EC_REG_RGB_GREEN), ec_read(EC_REG_RGB_BLUE)
    trig = ec_read(EC_REG_RGB_TRIGGER)
    if st is None:
        return {"kbd_rgb": None, "kbd_brightness": None, "kbd_rainbow": False}
    level = min((st >> EC_KBD_BRIGHTNESS_SHIFT) & 0x7, EC_KBD_BRIGHTNESS_LEVELS)
    rgb = None
    if None not in (r, g, b):
        # EC 可能已是 0-50, 也可能被旧版写成 0-200; 按实际值归一
        def norm(x):
            return _rgb_ec_to_api(x) if x <= KBD_RGB_EC_MAX else max(0, min(PWM_MAX, x))
        rgb = f"{norm(r)} {norm(g)} {norm(b)}"
    return {
        "kbd_rgb": rgb,
        "kbd_brightness": str(_level_to_brightness(level)),
        "kbd_rainbow": bool(trig is not None and (trig & EC_BIT_RGB_RAINBOW)),
    }


_kbd_cache = {"t": 0.0, "v": None}
KBD_TTL = 2.5                   # status 轮询用: 一次读 5 个 EC 寄存器, 2.5s 内复用


def kbd_read_cached() -> dict:
    now = time.time()
    if _kbd_cache["v"] is not None and now - _kbd_cache["t"] < KBD_TTL:
        return _kbd_cache["v"]
    v = kbd_read()
    _kbd_cache.update(t=now, v=v)
    return v


def kbd_set(brightness=None, rgb=None, effect=None) -> dict:
    """键盘灯经 WKBC 写 EC。亮度变化必须重 APPLY 颜色, 否则固件会掉出 RGB 模式变成「调亮度=换色」。"""
    out = {"ok": True, "max": PWM_MAX}
    if not _kbd_ensure_china_mode():
        return {"ok": False, "error": "无法启用键盘灯 (EC BIOS_OEM_2)"}

    want_rgb = None  # API 色域, 末尾统一 APPLY
    if rgb is not None and effect != "rainbow":
        want_rgb = [max(0, min(int(x), PWM_MAX)) for x in rgb]

    if effect is not None:
        if effect == "rainbow":
            if not ec_write(EC_REG_RGB_TRIGGER, EC_BIT_RGB_RAINBOW):
                out["ok"], out["error"] = False, "写彩虹模式失败"
            else:
                out["effect"] = "rainbow"
                want_rgb = None  # 彩虹时固件接管颜色
                if brightness is None:
                    cur = ec_read(EC_REG_KBD_STATUS)
                    if cur is not None and ((cur >> EC_KBD_BRIGHTNESS_SHIFT) & 0x7) == 0:
                        brightness = 100
        elif effect == "solid":
            # 只清彩虹位, 避免 TRIGGER 整清破坏 RGB 模式
            trig = ec_read(EC_REG_RGB_TRIGGER) or 0
            if trig & EC_BIT_RGB_RAINBOW:
                ec_write(EC_REG_RGB_TRIGGER, trig & ~EC_BIT_RGB_RAINBOW & 0xFF)
            out["effect"] = "solid"
            # 未带新颜色则读回当前色, 后面再 APPLY 一次稳住 RGB 模式
            if want_rgb is None:
                cur = kbd_read().get("kbd_rgb")
                if cur:
                    want_rgb = [int(x) for x in cur.split()[:3]]
        elif effect == "off":
            trig = ec_read(EC_REG_RGB_TRIGGER) or 0
            if trig & EC_BIT_RGB_RAINBOW:
                ec_write(EC_REG_RGB_TRIGGER, trig & ~EC_BIT_RGB_RAINBOW & 0xFF)
            brightness = 0
            want_rgb = None
            out["effect"] = "off"
        else:
            return {"ok": False, "error": f"未知灯效 {effect}"}

    # 只调亮度时也必须重 APPLY 当前颜色, 否则固件把亮度档当成调色板
    if want_rgb is None and brightness is not None and effect != "off" and effect != "rainbow":
        cur = kbd_read().get("kbd_rgb")
        if cur:
            want_rgb = [int(x) for x in cur.split()[:3]]

    if want_rgb is not None:
        if _kbd_apply_rgb(*want_rgb):
            out["rgb"] = want_rgb
            if brightness is None:
                cur = ec_read(EC_REG_KBD_STATUS)
                if cur is not None and ((cur >> EC_KBD_BRIGHTNESS_SHIFT) & 0x7) == 0:
                    brightness = 100
        else:
            out["ok"], out["error"] = False, "写 RGB 失败"

    if brightness is not None:
        level = _brightness_to_level(brightness)
        if _kbd_write_brightness(level):
            out["brightness"] = _level_to_brightness(level)
            # 亮度写完再脉冲一次 APPLY, 锁定 RGB 模式
            if want_rgb is not None and effect != "rainbow":
                ec_write(EC_REG_RGB_TRIGGER, EC_BIT_RGB_APPLY)
        else:
            out["ok"], out["error"] = False, "写键盘亮度失败"

    _kbd_cache["t"] = 0.0               # 写完失效, 下一次 status 立即读到新值
    if out.get("ok"):
        saved = dict(load_state().get("kbd") or {})
        for k in ("brightness", "rgb", "effect"):
            if k in out:
                saved[k] = out[k]
        state_update(kbd=saved)         # 睡眠/开机后按此恢复
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
def nvidia_driver_ok() -> bool:
    """nvidia 模块是否已加载 (缺 /proc/driver/nvidia/version 时 nvidia-smi 必失败)"""
    return os.path.exists("/proc/driver/nvidia/version")


def gpu_name() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=8).stdout.strip()
        name = out.splitlines()[0] if out else ""
        # 驱动缺失时 nvidia-smi 会把报错打到 stdout, 不能当成型号
        if not name or "NVIDIA-SMI has failed" in name or name.startswith("NVIDIA-SMI"):
            return ""
        return name.replace("NVIDIA GeForce ", "").replace(" GPU", "")
    except Exception:
        return ""


def probe_features(dsdt: dict) -> dict:
    """多机型适配: 识别 -> 档案 -> 门槛 -> 校准 (mrvmodel); sysfs 能力按存在性探测, UI 按此自适应"""
    inou = INOU_DIR
    ident = mrvmodel.identity(ec_read)
    model = mrvmodel.match_model(ident, mrvmodel.load_models())
    ppt_source, ppt = mrvmodel.cpu_ppt(ident, model)
    gates = mrvmodel.gates(ident, dsdt, ec_read(EC_REG_PROFILE) is not None)
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
        "identity": ident,
        "model": {"id": model["id"], "name": model["name"]} if model else None,
        "dsdt": dsdt,
        "gates": gates,
        "profile": gates["profile"]["ok"],
        "charge": gates["charge"]["ok"],
        "fan": bool(HW),
        # 键盘灯走 EC/WKBC; 状态灯条 sysfs 不是键盘。SUPPORT_2 bit2 = RGB_KEYBOARD
        "rgb": ec_read(EC_REG_KBD_STATUS) is not None and bool((ec_read(0x0766) or 0) & 0x04),
        "rainbow": True,           # 彩虹经 EC TRIGGER bit7, 不依赖可能无效的 sysfs
        "breathing": os.path.exists(f"{inou}/breathing_in_suspend"),
        "fn_lock": os.path.exists(f"{inou}/fn_lock"),
        "super_key": os.path.exists(f"{inou}/super_key_enable"),
        "logo_light": os.path.isdir(LED_STATUS),  # 状态灯条存在则可供后续扩展
        "fan_boost": gates["fan_boost"]["ok"],
        "ec_channel": "wkbc" if EC_VIA_WKBC else "mmio",
        "cpu_model": ident["cpu"],
        "gpu_name": gpu_name(),
        "gpu_driver": nvidia_driver_ok(),
        # cpuinfo_max_freq 在关睿频后变成基础频率; amd_pstate_max_freq 始终是最高睿频
        "cpu_max_mhz": (v := read_text("/sys/devices/system/cpu/cpu0/cpufreq/amd_pstate_max_freq")
                        or read_text("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")) and int(v) // 1000,
        "cpu_ppt_table": ppt,
        "cpu_ppt_source": ppt_source,
    }
    # mux: DSDT 门槛 + EFI OemMagicVariable (真正存直连/混合的地方)
    out = acpi_method(f"{MUX_PATH}.DGPS") if gates["mux"]["ok"] else "Error: gated"
    efi_ok = os.path.exists(EFI_MUX_VAR)
    feats["mux"] = efi_ok or (not out.startswith("Error") and out.lower() in (
        "0x0", "0x1", "0x2", "0xaa", "0x55"))
    feats["mux_efi"] = efi_ok
    feats["mux_modes"] = list(MUX_MODE_BYTE.keys()) if efi_ok else []
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
                cur = kbd_read().get("kbd_brightness")
                if cur and str(cur).isdigit():
                    state_update(kbd_restore=int(cur))
                kbd_set(brightness=0)
                log("离电: 关闭背光")
        self.last_ac = ac


ac_led_guard = None


# ================================================================ 混合模式 · 离电独显休眠 (RTD3)
# 本模具无 ACPI _PR3 (D3cold 不可用), nvidia-smi drain 也不会真正断电;
# 能做到的是让驱动空闲时把 GPU 挂进 D3hot (RTD3), 并避免我们的轮询把刚睡下的独显唤醒。
BATTERY_IGPU_FLAG = f"{RUN_DIR}/battery-igpu"
hybrid_battery_igpu = None
sleeping = threading.Event()        # logind PrepareForSleep 期间置位


def _ac_online() -> bool | None:
    try:
        with open("/sys/class/power_supply/AC0/online") as f:
            return f.read().strip() == "1"
    except OSError:
        return None


def gpu_runtime_status():
    """sysfs 读独显运行时电源状态 (纯读, 不会唤醒独显)"""
    p = nvidia_pci_dir()
    return read_text(f"{p}/power/runtime_status") if p else None


class HybridBatteryIgpu:
    """混合模式下: 离电 → 强制 RTD3 并停止 GPU 轮询; 插电 → 恢复正常轮询"""

    def __init__(self):
        self.enabled = load_state().get("hybrid_battery_igpu", True)
        self.active = False
        self.last_ac = None
        self.last_msg = ""

    def _in_hybrid(self) -> bool:
        mode, raw, _ = _efi_mux_read()
        if mode == "standard":
            return True
        if mode is None and raw is None:
            # EFI 读不到时, 以已保存意图为准
            return load_state().get("mux_mode", "standard") == "standard"
        return False

    @staticmethod
    def _enforce_rtd3() -> int:
        """把 10de 设备的 power/control 设为 auto, 允许运行时挂起; 返回设备数"""
        n = 0
        for p in _glob.glob("/sys/bus/pci/devices/*"):
            try:
                if read_text(f"{p}/vendor") != "0x10de":
                    continue
                with open(f"{p}/power/control", "w") as f:
                    f.write("auto")
                try:
                    with open(f"{p}/power/autosuspend_delay_ms", "w") as f:
                        f.write("1000")
                except OSError:
                    pass
                n += 1
            except OSError:
                continue
        return n

    def _enter(self):
        """离电: 允许独显 RTD3 休眠 (drain 不会断电, 运行时 IGPS 有黑屏风险, 均已移除)"""
        n = self._enforce_rtd3()
        os.makedirs(RUN_DIR, exist_ok=True)
        try:
            open(BATTERY_IGPU_FLAG, "w").write("1\n")
        except OSError:
            pass
        self.active = True
        self.last_msg = f"RTD3 {n} 个设备 auto" if n else "未找到 NVIDIA 设备"
        log(f"离电独显休眠: {self.last_msg}")

    def _leave(self):
        """插电: 恢复正常遥测轮询 (power/control 保持 auto, 空闲仍可休眠)"""
        try:
            os.remove(BATTERY_IGPU_FLAG)
        except OSError:
            pass
        self.active = False
        self.last_msg = "插电恢复轮询"
        log("插电: 恢复独显遥测轮询")

    def poll(self):
        if sleeping.is_set():
            return
        ac = _ac_online()
        if ac is None:
            return
        if not self.enabled or not self._in_hybrid():
            if self.active:
                self._leave()
            self.last_ac = ac
            return
        # 首次或电源变化
        if self.last_ac is None:
            if not ac:
                self._enter()
            self.last_ac = ac
            return
        if ac != self.last_ac:
            if ac:
                self._leave()
            else:
                self._enter()
        self.last_ac = ac

    def set_enabled(self, enable: bool) -> dict:
        self.enabled = bool(enable)
        state_update(hybrid_battery_igpu=self.enabled)
        ac = _ac_online()
        if self.enabled and self._in_hybrid() and ac is False:
            self._enter()
        elif not self.enabled and self.active:
            self._leave()
        return {"ok": True, "hybrid_battery_igpu": self.enabled,
                "active": self.active, "detail": self.last_msg}


# ================================================================ Mux (显卡模式)
# 本机与蛟龙等同模具: 重启生效的模式存在 EFI 变量 OemMagicVariable, 偏移 0x62
#   0x00=混合输出  0x01=独显直连  0x02=集显(节能; 部分 BIOS 支持)
# ACPI DGPS 只反映独显电源是否在线, 不能区分直连/混合; IGPS 运行时改 BLSC 有黑屏风险, 不调用
MUX_PATH = "\\_SB.PCI0.SBRG.EC0"
EFI_MUX_GUID = "9f33f85c-13ca-4fd1-9c4a-96217722c593"
EFI_MUX_VAR = f"/sys/firmware/efi/efivars/OemMagicVariable-{EFI_MUX_GUID}"
EFI_MUX_MODE_OFF = 0x62          # 蛟龙文档写 0x66, 对照其 hex 样例实际差在 0x62
MUX_MODE_BYTE = {"standard": 0x00, "dgpu": 0x01, "igpu": 0x02}
MUX_MODE_NAME = {
    "igpu": "集显",
    "standard": "混合输出",
    "dgpu": "独显输出",
}
MUX_BYTE_TO_MODE = {v: k for k, v in MUX_MODE_BYTE.items()}


def _efi_mux_read() -> tuple:
    """返回 (mode_key|None, raw_byte|None, error|None)"""
    if not os.path.exists(EFI_MUX_VAR):
        return None, None, "未找到 OemMagicVariable (非 UEFI 或机型不支持)"
    try:
        data = open(EFI_MUX_VAR, "rb").read()
    except OSError as e:
        return None, None, f"读 EFI 变量失败: {e}"
    if len(data) < 4 + EFI_MUX_MODE_OFF + 1:
        return None, None, f"OemMagicVariable 长度异常 ({len(data)})"
    raw = data[4 + EFI_MUX_MODE_OFF]
    return MUX_BYTE_TO_MODE.get(raw), raw, None


def _efi_mux_write(mode: str) -> dict:
    """只改模式字节, 保留本机其余 EFI 载荷 (不可套用其它机型整包 hex)"""
    if mode not in MUX_MODE_BYTE:
        return {"ok": False, "error": f"未知模式 {mode}"}
    if not os.path.exists(EFI_MUX_VAR):
        return {"ok": False, "error": "未找到 OemMagicVariable"}
    try:
        subprocess.run(["chattr", "-i", EFI_MUX_VAR], capture_output=True, check=False)
    except FileNotFoundError:
        pass
    try:
        with open(EFI_MUX_VAR, "rb") as f:
            data = bytearray(f.read())
        if len(data) < 4 + EFI_MUX_MODE_OFF + 1:
            return {"ok": False, "error": f"OemMagicVariable 长度异常 ({len(data)})"}
        # 备份一次, 便于回滚
        bak = STATE_DIR + "/OemMagicVariable.bak"
        os.makedirs(STATE_DIR, exist_ok=True)
        if not os.path.exists(bak):
            with open(bak, "wb") as f:
                f.write(data)
        data[4 + EFI_MUX_MODE_OFF] = MUX_MODE_BYTE[mode]
        with open(EFI_MUX_VAR, "wb") as f:
            f.write(data)
        # 读回确认
        with open(EFI_MUX_VAR, "rb") as f:
            back = f.read()
        got = back[4 + EFI_MUX_MODE_OFF]
        if got != MUX_MODE_BYTE[mode]:
            return {"ok": False, "error": f"写入未生效 (读回 0x{got:02X})"}
        return {"ok": True, "mux_mode": mode, "efi_byte": got}
    except PermissionError:
        return {"ok": False, "error": "写 EFI 变量权限不足 (需 root)"}
    except OSError as e:
        return {"ok": False, "error": str(e)}


def mux_query() -> dict:
    """以 EFI 模式字节为准; DGPS 仅作独显电源补充信息"""
    mode, efi_byte, err = _efi_mux_read()
    dgps = acpi_method(f"{MUX_PATH}.DGPS")
    dgps_l = dgps.lower() if isinstance(dgps, str) else str(dgps)
    if err and mode is None:
        # EFI 不可读时回退到已保存意图
        saved = load_state().get("mux_mode")
        if saved in MUX_MODE_NAME:
            return {"ok": True, "mux_mode": saved, "state": MUX_MODE_NAME[saved],
                    "raw": dgps, "efi_byte": None, "warning": err}
        return {"ok": False, "error": err, "raw": dgps}
    state = MUX_MODE_NAME.get(mode, f"未知(0x{efi_byte:02X})" if efi_byte is not None else "未知")
    power = None
    if dgps_l == "0xaa":
        power = "独显电源在线"
    elif dgps_l == "0x55":
        power = "独显已下电"
    return {"ok": True, "mux_mode": mode, "state": state, "efi_byte": efi_byte,
            "raw": dgps, "dgpu_power": power,
            "battery_igpu_active": bool(hybrid_battery_igpu and hybrid_battery_igpu.active)}


def mux_switch(mode: str) -> dict:
    """写入 EFI 显卡模式, 需重启生效。mode: igpu|standard|dgpu"""
    r = _efi_mux_write(mode)
    if r.get("ok"):
        state_update(mux_mode=mode)
        r["state"] = MUX_MODE_NAME[mode]
        r["note"] = f"已设为{MUX_MODE_NAME[mode]}, 请立刻重启使显示输出切换生效"
        if mode == "igpu":
            r["note"] += " (集显依赖 BIOS 是否识别 0x02; 若重启后仍非集显, 请在 BIOS 中确认或切回混合)"
    return r


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
    """查找 NVIDIA 显示 PCI 设备; 首次未枚举到时允许后续重试"""
    global _nv_pci
    if _nv_pci:
        return _nv_pci
    found = ""
    for p in _glob.glob("/sys/bus/pci/devices/*"):
        try:
            with open(f"{p}/vendor") as f, open(f"{p}/class") as g:
                if f.read().strip() == "0x10de" and g.read().strip().startswith("0x03"):
                    found = p
                    break
        except OSError:
            continue
    if found:
        _nv_pci = found
    return found


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


def _smi_float(s):
    """nvidia-smi 字段可能是 N/A / [N/A]; 解析失败返回 None 而不是整包失败"""
    s = (s or "").strip()
    if not s or s.upper() in ("N/A", "[N/A]", "N/A W"):
        return None
    try:
        return float(s.split()[0])
    except ValueError:
        return None


_gpu_cache = {"t": 0.0, "v": None}
GPU_TTL_ACTIVE = 4.0            # 有负载时正常刷新
GPU_TTL_IDLE = 30.0             # 空闲: 拉长间隔, 给 RTD3 留出休眠窗口
GPU_TTL_BATTERY = 90.0          # 离电休眠策略生效时更激进


def _gpu_ttl():
    v = _gpu_cache["v"] or {}
    if v.get("suspended") or v.get("error"):
        return 15.0
    idle = (v.get("util_pct") or 0) < 1 and (v.get("draw_w") or 0) < 5
    if idle:
        if hybrid_battery_igpu and hybrid_battery_igpu.active:
            return GPU_TTL_BATTERY
        return GPU_TTL_IDLE
    return GPU_TTL_ACTIVE


def gpu_info():
    """GPU 功耗 + 显存 + 频率 + 利用率 (缓存 + 空闲降频, 避免把 RTD3 睡下的独显唤醒)"""
    now = time.time()
    if _gpu_cache["v"] is not None and now - _gpu_cache["t"] < _gpu_ttl():
        return _gpu_cache["v"]
    out = _gpu_info()
    _gpu_cache.update(t=now, v=out)
    return out


def _gpu_info():
    """实际读取 (每次都会调 nvidia-smi)"""
    if gpu_suspended():
        return {"suspended": True}
    if hybrid_battery_igpu and hybrid_battery_igpu.active:
        # 离电集显策略生效: 仍可读则附带标记, 读失败则视为省电中
        pass
    out = {}
    try:
        csv = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,clocks.sm,"
             "utilization.gpu,power.draw,power.max_limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5).stdout.strip()
        # 驱动未就绪时 stdout 空、stderr 有错误信息
        if not csv or csv.upper().startswith("NVIDIA-SMI"):
            return {"error": "nvidia-smi 不可用"}
        f = [x.strip() for x in csv.split(",")]
        if len(f) >= 6:
            keys = ("mem_used_mb", "mem_total_mb", "clock_mhz", "util_pct",
                    "draw_w", "max_limit_w")
            for k, raw in zip(keys, f[:6]):
                v = _smi_float(raw)
                if v is not None:
                    out[k] = v
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


# 满载负载: 每个逻辑核一个子进程做 sha256; 60 秒后自行退出, 守护进程异常时也不会留下负载
_LOAD_CODE = ("import hashlib, time\nd = b'x' * 16384\nend = time.time() + 60\n"
              "while time.time() < end:\n    hashlib.sha256(d).digest()\n")


class Calibrator(threading.Thread):
    """本机实测各档 CPU 功耗墙 (对应 NvpwrControl 的动态 OEM 基线: 基线在运行时取得, 不写死).
    每档: 切档 -> 等待 -> 满载 -> 取稳态段 RAPL 封装功耗 -> 冷却; 结束后恢复原档位, 结果按机型+BIOS 存盘"""
    SETTLE_S, RAMP_S, MEASURE_S, COOL_S = 5, 8, 12, 15
    TEMP_ABORT = 99.0

    def __init__(self):
        super().__init__(daemon=True)
        self.state = {"running": True, "step": "准备", "result": None, "error": None}

    def _energy(self):
        with open(RAPL_PATH) as f:
            return int(f.read().strip()), time.time()

    def run(self):
        orig = get_profile()
        procs, result = [], {}
        try:
            apply_cpu_boost(True)       # 静音档联动会关睿频, 测功耗墙时必须打开, 否则高档测不到上限
            for i, prof in enumerate(PROFILE_BITS):
                self.state["step"] = f"{prof} {i + 1}/{len(PROFILE_BITS)}"
                if not set_profile(prof, link=False).get("ok"):
                    raise RuntimeError(f"切换到 {prof} 失败")
                time.sleep(self.SETTLE_S)
                procs = [subprocess.Popen([sys.executable, "-c", _LOAD_CODE]) for _ in range(os.cpu_count() or 1)]
                time.sleep(self.RAMP_S)
                e0, t0 = self._energy()
                for _ in range(self.MEASURE_S):
                    time.sleep(1)
                    temp = guard.current_temp()
                    if temp is not None and temp >= self.TEMP_ABORT:
                        raise RuntimeError(f"温度 {temp:.0f}°C 过高, 中止校准")
                e1, t1 = self._energy()
                result[prof] = round((e1 - e0) / (t1 - t0) / 1e6)
                for p in procs:
                    p.kill()
                procs = []
                log(f"校准 {prof}: CPU 功耗墙 ≈{result[prof]} W")
                time.sleep(self.COOL_S)
            ident = FEATURES_CACHE["identity"]
            mrvmodel.save_calibration(ident, result)
            FEATURES_CACHE.update(cpu_ppt_table=result, cpu_ppt_source="calibrated")
            self.state["result"] = result
        except Exception as e:
            self.state["error"] = str(e)
            log(f"校准失败: {e}")
        finally:
            for p in procs:
                p.kill()
            if orig in PROFILE_BITS:
                set_profile(orig, link=False)
                apply_cpu_boost(PROFILE_ACTIONS[orig].get("cpu_boost", True))
            self.state.update(running=False, step="完成" if not self.state["error"] else "失败")


calibrator = None


def start_calibration() -> dict:
    global calibrator
    gate = FEATURES_CACHE.get("gates", {}).get("calibrate", {})
    if not gate.get("ok"):
        return {"ok": False, "error": gate.get("why") or "不支持校准"}
    if calibrator and calibrator.state["running"]:
        return {"ok": False, "error": "校准正在进行"}
    calibrator = Calibrator()
    calibrator.start()
    return {"ok": True, "calibration": calibrator.state}


_platform_cache = {"t": 0.0, "profile": None, "v": None}
PLATFORM_TTL = 5.0              # EC 平台参数变化很慢 (切档才变), 5s 内复用


def platform_info(profile: str) -> dict:
    now = time.time()
    if (_platform_cache["v"] is not None and _platform_cache["profile"] == profile
            and now - _platform_cache["t"] < PLATFORM_TTL):
        return _platform_cache["v"]
    v = {"tpp_w": ec_read(EC_REG_ETPP), "db_w": ec_read(EC_REG_DBAP),
         "ctgp_base_w": ec_read(EC_REG_CTWA),
         "cpu_ppt_w": FEATURES_CACHE.get("cpu_ppt_table", {}).get(profile),
         "cpu_ppt_source": FEATURES_CACHE.get("cpu_ppt_source")}
    _platform_cache.update(t=now, profile=profile, v=v)
    return v


# ================================================================ 睡眠/唤醒
def restore_after_resume():
    """开机/唤醒后 EC 可能被固件重置: 重放档位、限充、键盘灯与 INOU 开关"""
    st = load_state()
    prof = st.get("profile")
    if prof in PROFILE_BITS:
        r = set_profile(prof, kbd=False)
        log(f"恢复性能档位 {prof}: {r.get('ok')}")
    limit = st.get("charge_limit")
    if isinstance(limit, int):
        set_charge_limit(limit)
    kbd = st.get("kbd") or {}
    if kbd:
        r = kbd_set(brightness=kbd.get("brightness"), rgb=kbd.get("rgb"),
                    effect=kbd.get("effect") or "solid")
        log(f"恢复键盘灯: {r.get('ok')}")
    for name, val in (st.get("toggles") or {}).items():
        toggle_sysfs(name, bool(val))
    if ac_led_guard:
        ac_led_guard.poll()


def sleep_watch_loop():
    """订阅 logind PrepareForSleep: 睡前冻结采样/EC 轮询, 醒后重放设置"""
    try:
        from gi.repository import Gio, GLib
    except Exception as e:
        log(f"WARN 无法加载 Gio, 跳过睡眠监听: {e}")
        return

    def on_prepare(_conn, _sender, _path, _iface, _signal, params):
        try:
            going = bool(params.unpack()[0])
        except Exception:
            return
        if going:
            sleeping.set()
            if sampler:
                sampler.paused.set()
            log("系统即将睡眠: 冻结采样与 EC 轮询")
        else:
            log("系统已唤醒: 恢复设置")
            time.sleep(2)               # 等 EC/驱动就绪
            try:
                restore_after_resume()
            except Exception as e:
                log(f"WARN 唤醒恢复失败: {e}")
            finally:
                if sampler:
                    sampler.paused.clear()
                sleeping.clear()

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        bus.signal_subscribe("org.freedesktop.login1", "org.freedesktop.login1.Manager",
                             "PrepareForSleep", "/org/freedesktop/login1", None,
                             Gio.DBusSignalFlags.NONE, on_prepare)
        log("已订阅 logind 睡眠/唤醒事件")
        GLib.MainLoop().run()
    except Exception as e:
        log(f"WARN 睡眠监听失败: {e}")


def status():
    profile = get_profile()
    tel = sampler.snapshot() if sampler else {}
    # 温度/风扇/占空比由采样线程每 2s 读一次 (uniwill hwmon 单次是一笔 12-24ms 的 EC 事务);
    # 快照超过 5s 未更新 (采样线程异常) 才回退到直读, 保证不会永远拿不到数
    hw = tel.get("hw") if tel and time.time() - tel.get("ts", 0) < 5 else None

    def hw_val(key, name, div=1):
        if hw is not None and key in hw:    # 快照里有该字段 (即便读失败) 就不再直读
            return hw[key]
        v = hw_read(name)
        try:
            return float(v) / div
        except (TypeError, ValueError):
            return None

    st = {
        "profile": profile,
        "platform": platform_info(profile),
        "cpu_boost": read_text(CPU_BOOST_PATH) == "1" if os.path.exists(CPU_BOOST_PATH) else None,
        "gpu": gpu_info(),
        "gpu_runtime": gpu_runtime_status(),
        "cpu": cpu_info(),
        "fan1_rpm": hw_val("fan1_rpm", "fan1_input"),
        "fan2_rpm": hw_val("fan2_rpm", "fan2_input"),
        "pwm1": hw_val("pwm1", "pwm1"),
        "cpu_temp": hw_val("cpu_temp", "temp1_input", 1000),
        "gpu_temp": hw_val("gpu_temp", "temp2_input", 1000),
        "charge_limit_pct": charge_limit(),
        "fan_mode": guard.mode(),
        "fan_boost_ec": guard.ec_boost,
        "fan_guard": guard.guard,
        "overheat_guard": guard.auto_active,
        "toggles": {n: read_text(f"{INOU_DIR}/{n}") == "1" for n in TOGGLES
                    if os.path.exists(f"{INOU_DIR}/{n}")},
        "battery": battery_info(),
        "ac_led_off": ac_led_guard.enabled if ac_led_guard else False,
        "hybrid_battery_igpu": hybrid_battery_igpu.enabled if hybrid_battery_igpu else False,
        "battery_igpu_active": hybrid_battery_igpu.active if hybrid_battery_igpu else False,
        "calibration": calibrator.state if calibrator else None,
        "features": FEATURES_CACHE,
        "telemetry": tel,
    }
    st.update(kbd_read_cached())
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


# ================================================================ 资源采样 (本机性能监测)
# 2 秒周期读 /proc 与电池 sysfs, 差分算出占用率与速率; 快照经 status 下发给 GUI 曲线 (仅内存态, 不落盘)
DISK_RE = re.compile(r"^(?:sd[a-z]+|vd[a-z]+|nvme\d+n\d+|mmcblk\d+)$")


def _usage_pct(cur, prev):
    """(忙 jiffies, 总 jiffies) 差分 -> 占用率 %; 无前值返回 None"""
    if not cur or not prev:
        return None
    dbusy, dtotal = cur[0] - prev[0], cur[1] - prev[1]
    if dtotal <= 0:
        return None
    return round(max(0.0, min(1.0, dbusy / dtotal)) * 100, 1)


class ResourceSampler(threading.Thread):
    """CPU 合计/每核占用 · 内存 · 每盘读写速率与利用率 · 每网卡收发速率 · 电池侧功率"""

    INTERVAL = 2.0

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_evt = threading.Event()
        self.paused = threading.Event()     # 睡眠期间暂停采样
        self.lock = threading.Lock()
        self._prev = {}
        self.snap = {}

    def snapshot(self):
        """最近一次采样快照 (整体替换, 调用方只读)"""
        with self.lock:
            return self.snap

    # ---------------- /proc / sysfs 读数 ----------------
    @staticmethod
    def _cpu_times():
        """(合计, 每核) 的 (忙, 总) jiffies; 失败返回 (None, [])"""
        rows = []
        try:
            with open("/proc/stat") as f:
                for line in f:
                    if not line.startswith("cpu"):
                        break
                    nums = [int(x) for x in line.split()[1:]]
                    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
                    rows.append((sum(nums) - idle, sum(nums)))
        except (OSError, ValueError, IndexError):
            return None, []
        return (rows[0] if rows else None), rows[1:]

    @staticmethod
    def _meminfo():
        """{MemTotal/MemAvailable/SwapTotal/SwapFree: MB}; 缺项返回 None"""
        want = ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")
        vals = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    key, sep, rest = line.partition(":")
                    if key in want:
                        vals[key] = int(rest.split()[0]) // 1024
        except (OSError, ValueError, IndexError):
            return None
        return vals if all(k in vals for k in want) else None

    @staticmethod
    def _diskstats():
        """{盘名: (读扇区, 写扇区, 累计 IO 毫秒)}; 只取整盘 (排除分区/loop/ram)"""
        out = {}
        try:
            with open("/proc/diskstats") as f:
                for line in f:
                    p = line.split()
                    if len(p) < 14 or not DISK_RE.match(p[2]):
                        continue
                    out[p[2]] = (int(p[5]), int(p[9]), int(p[12]))
        except (OSError, ValueError):
            pass
        return out

    @staticmethod
    def _netdev():
        """{网卡: (接收字节, 发送字节)}; 跳过 lo"""
        out = {}
        try:
            with open("/proc/net/dev") as f:
                for line in f:
                    name, sep, rest = line.partition(":")
                    name = name.strip()
                    if not sep or name == "lo":
                        continue
                    p = rest.split()
                    if len(p) >= 9:
                        out[name] = (int(p[0]), int(p[8]))
        except (OSError, ValueError):
            pass
        return out

    @staticmethod
    def _battery_power():
        """电池侧功率 W: 放电为正, 充电为负; 满/未充电/读不到为 None"""
        v = read_text("/sys/class/power_supply/BAT0/voltage_now")
        i = read_text("/sys/class/power_supply/BAT0/current_now")
        status = read_text("/sys/class/power_supply/BAT0/status")
        if not v or not i:
            return None
        try:
            w = abs(float(v) * float(i)) / 1e12
        except ValueError:
            return None
        if status == "Discharging":
            return round(w, 1)
        if status == "Charging":
            return round(-w, 1)
        return None

    @staticmethod
    def _hwmon():
        """温度/风扇/占空比快照。uniwill hwmon 每个字段都是一次 EC 事务
        (temp ~12ms, fan ~24ms), 放在采样线程里读, status 直接用最近快照"""
        def num(name, div=1):
            v = hw_read(name)
            try:
                x = float(v) / div
            except (TypeError, ValueError):
                return None
            return round(x, 1) if div != 1 else int(x)

        return {"cpu_temp": num("temp1_input", 1000), "gpu_temp": num("temp2_input", 1000),
                "fan1_rpm": num("fan1_input"), "fan2_rpm": num("fan2_input"),
                "pwm1": num("pwm1")}

    # ---------------- 采样 ----------------
    def _once(self):
        now = time.time()
        cpu_t, core_t = self._cpu_times()
        cur = {"cpu": cpu_t, "cores": core_t, "mem": self._meminfo(),
               "disk": self._diskstats(), "net": self._netdev()}
        prev = self._prev
        self._prev = dict(cur, t=now)

        snap = {"ts": round(now, 3), "mem": None, "disk": [], "net": [], "battery_w": None,
                "cpu": {"total_pct": None, "core_pct": []}}

        mem = cur["mem"]
        if mem:
            snap["mem"] = {"total_mb": mem["MemTotal"],
                           "used_mb": mem["MemTotal"] - mem["MemAvailable"],
                           "swap_total_mb": mem["SwapTotal"],
                           "swap_used_mb": mem["SwapTotal"] - mem["SwapFree"]}

        dt = now - prev.get("t", 0)
        if dt > 0:
            snap["cpu"]["total_pct"] = _usage_pct(cpu_t, prev.get("cpu"))
            snap["cpu"]["core_pct"] = [_usage_pct(c, p)
                                       for c, p in zip(core_t, prev.get("cores") or [])]
            prev_disk, prev_net = prev.get("disk") or {}, prev.get("net") or {}
            for name, c in cur["disk"].items():
                row = {"name": name, "util_pct": None, "read_bps": None, "write_bps": None}
                p = prev_disk.get(name)
                if p:
                    row["util_pct"] = round(max(0.0, min(100.0, (c[2] - p[2]) / (dt * 1000) * 100)), 1)
                    row["read_bps"] = round(max(0, c[0] - p[0]) * 512 / dt)
                    row["write_bps"] = round(max(0, c[1] - p[1]) * 512 / dt)
                snap["disk"].append(row)
            snap["disk"].sort(key=lambda r: r["name"])
            for name, c in cur["net"].items():
                row = {"name": name, "rx_bps": None, "tx_bps": None}
                p = prev_net.get(name)
                if p:
                    row["rx_bps"] = round(max(0, c[0] - p[0]) / dt)
                    row["tx_bps"] = round(max(0, c[1] - p[1]) / dt)
                snap["net"].append(row)
            snap["net"].sort(key=lambda r: r["name"])
        else:
            # 首轮: 只有盘/网卡名单, 速率留 None 等下一轮差分
            snap["disk"] = [{"name": n, "util_pct": None, "read_bps": None, "write_bps": None}
                            for n in sorted(cur["disk"])]
            snap["net"] = [{"name": n, "rx_bps": None, "tx_bps": None}
                           for n in sorted(cur["net"])]

        snap["battery_w"] = self._battery_power()
        snap["hw"] = self._hwmon()
        with self.lock:
            self.snap = snap

    def run(self):
        while not self.stop_evt.is_set():
            if not self.paused.is_set():
                try:
                    self._once()
                except Exception as e:
                    log(f"WARN ResourceSampler: {e}")
            self.stop_evt.wait(self.INTERVAL)


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
        if sub in ("igpu", "dgpu", "standard"):
            if not cmd.get("confirm"):
                return {"ok": False,
                        "error": "显卡模式切换需重启生效, 请加 confirm:true 并准备重启"}
            return mux_switch(sub)
        return {"ok": False, "error": "mux 子命令: query|igpu|standard|dgpu"}
    if op == "toggle":
        name, val = cmd.get("name", ""), bool(cmd.get("value"))
        r = toggle_sysfs(name, val)
        if r.get("ok"):
            t = dict(load_state().get("toggles") or {})
            t[name] = val
            state_update(toggles=t)     # 睡眠/开机后按此恢复
        return r
    if op == "calibrate":
        return start_calibration()
    if op == "ac_led_off":
        enable = bool(cmd.get("value"))
        state_update(ac_led_off=enable)
        ac_led_guard.enabled = enable
        return {"ok": True, "ac_led_off": enable}
    if op == "hybrid_battery_igpu":
        if not hybrid_battery_igpu:
            return {"ok": False, "error": "未初始化"}
        return hybrid_battery_igpu.set_enabled(bool(cmd.get("value")))
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
sampler = None


def ac_poll_loop():
    """离电关灯 / 离电独显休眠 轮询 (5s 周期, 拔电要尽快生效)"""
    while True:
        if sleeping.is_set():
            time.sleep(1)
            continue
        try:
            ac_led_guard.poll()
        except Exception as e:
            log(f"WARN AcLedGuard: {e}")
        try:
            if hybrid_battery_igpu:
                hybrid_battery_igpu.poll()
        except Exception as e:
            log(f"WARN HybridBatteryIgpu: {e}")
        time.sleep(5)


def restore_on_boot():
    time.sleep(3)
    try:
        restore_after_resume()
    except Exception as e:
        log(f"WARN 开机恢复失败: {e}")
    if load_state().get("fan_curve"):
        state_update(fan_curve=None)     # 旧版用户态曲线的残留状态


def main():
    global HW, guard, ac_led_guard, hybrid_battery_igpu, EC_VIA_WKBC, sampler
    if os.geteuid() != 0:
        print("mrvd 需要 root 运行", file=sys.stderr)
        sys.exit(1)
    HW = find_uniwill_hwmon()
    if not HW:
        log("WARN 未找到 uniwill hwmon")
    else:
        log(f"hwmon: {HW}")
    dsdt = mrvmodel.dsdt_methods()
    EC_VIA_WKBC = bool(dsdt.get("WKBC"))
    log(f"EC 写入通道: {'WKBC 命令通道' if EC_VIA_WKBC else 'MMIO 直写 (DSDT 无 WKBC)'}")

    guard = ThermalGuard()
    ac_led_guard = AcLedGuard()
    hybrid_battery_igpu = HybridBatteryIgpu()
    sampler = ResourceSampler()
    log(f"混合离电集显: {'开' if hybrid_battery_igpu.enabled else '关'}")

    def on_term(sig, frame):
        log(f"收到信号 {sig}, 收尾...")
        guard.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    FEATURES_CACHE.update(probe_features(dsdt))
    m = FEATURES_CACHE.get("model")
    log(f"机型: {m['name'] if m else '未收录 (仅开放探测到的能力, 不套用任何功耗数值)'}; "
        f"CPU 功耗墙来源: {FEATURES_CACHE.get('cpu_ppt_source') or '无'}")
    log(f"机型能力: {json.dumps(FEATURES_CACHE, ensure_ascii=False)}")

    guard.start()
    sampler.start()
    threading.Thread(target=restore_on_boot, daemon=True).start()
    threading.Thread(target=ac_poll_loop, daemon=True).start()
    threading.Thread(target=profile_watch_loop, daemon=True).start()
    threading.Thread(target=sleep_watch_loop, daemon=True).start()
    serve()


if __name__ == "__main__":
    main()
