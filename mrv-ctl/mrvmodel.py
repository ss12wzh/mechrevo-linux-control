# -*- coding: utf-8 -*-
"""
机型适配: 识别 -> 档案匹配 -> 能力门槛 -> 运行时校准

思路参考 NvpwrControl (下载/40.50+SeriesTDP):
  - 识别型号再选档案 (DetectNvidiaGpuName -> DetectProfile), 档案只放实机验证过的数值
  - 高风险功能加硬门槛 (设备 ID / 驱动版本 / 结构校验), 这里对应 DSDT 方法存在性与 EC 平台代际
  - 可调范围和基线在运行时回读 (Pstates20 范围 / 动态 OEM 基线), 这里对应 EC 实时平台参数与本机校准
  - 没有证据的值不外推: 未知机型不套用任何功耗墙数值
"""

import json
import os
import time

MODELS_PATHS = ("/usr/share/mrv-ctl/models.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "models.json"))
CALIB_FILE = "/var/lib/mrvd/calibration.json"
DSDT = "/sys/firmware/acpi/tables/DSDT"
# 功能所依赖的 ACPI 方法; DSDT 里有这个名字才开放对应功能
DSDT_METHODS = ("ECRR", "ECRW", "WKBC", "RKBC", "PMSF", "PLIM", "DGPS", "IGPS")
EC_REG_GFID = 0x07D2        # 低 5 位: EC 平台代际 (DSDT 中 PMSF / Mux 按它分支)


def read_text(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def dsdt_methods() -> dict:
    try:
        with open(DSDT, "rb") as f:
            blob = f.read()
    except OSError:
        return {m: None for m in DSDT_METHODS}
    return {m: m.encode() in blob for m in DSDT_METHODS}


def cpu_model() -> str:
    for line in (read_text("/proc/cpuinfo") or "").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip().split(" w/ ")[0].replace(" with Radeon Graphics", "")
    return ""


def gpu_pci_id():
    base = "/sys/bus/pci/devices"
    for d in sorted(os.listdir(base)):
        if read_text(f"{base}/{d}/vendor") == "0x10de" and (read_text(f"{base}/{d}/class") or "").startswith("0x03"):
            return read_text(f"{base}/{d}/device")
    return None


def identity(ec_read) -> dict:
    dmi = "/sys/class/dmi/id"
    gfid = ec_read(EC_REG_GFID)
    return {
        "vendor": read_text(f"{dmi}/sys_vendor") or "",
        "product": read_text(f"{dmi}/product_name") or "",
        "board": read_text(f"{dmi}/board_name") or "",
        "bios": read_text(f"{dmi}/bios_version") or "",
        "gfid": None if gfid is None else gfid & 0x1F,
        "cpu": cpu_model(),
        "gpu_pci": gpu_pci_id(),
    }


def identity_key(ident: dict) -> str:
    """校准结果的归属: 同一主板 + 同一 BIOS + 同一 CPU; BIOS 升级后自动失效"""
    return f"{ident['board']}|{ident['bios']}|{ident['cpu']}"


def load_models() -> list:
    for p in MODELS_PATHS:
        try:
            with open(p) as f:
                return json.load(f)
        except (OSError, ValueError):
            continue
    return []


def match_model(ident: dict, models: list):
    for m in models:
        rule = m.get("match", {})
        if "board_prefix" in rule and not ident["board"].startswith(rule["board_prefix"]):
            continue
        if "vendor" in rule and ident["vendor"] != rule["vendor"]:
            continue
        if "cpu_contains" in rule and rule["cpu_contains"] not in ident["cpu"]:
            continue
        if "gfid" in rule and ident["gfid"] != rule["gfid"]:
            continue
        return m
    return None


def _load_calib() -> dict:
    try:
        with open(CALIB_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def load_calibration(ident: dict):
    return _load_calib().get(identity_key(ident))


def save_calibration(ident: dict, cpu_ppt: dict):
    data = _load_calib()
    data[identity_key(ident)] = {"cpu_ppt_w": cpu_ppt, "time": time.strftime("%F %T"), "identity": ident}
    os.makedirs(os.path.dirname(CALIB_FILE), exist_ok=True)
    tmp = CALIB_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CALIB_FILE)


def cpu_ppt(ident: dict, model) -> tuple:
    """(来源, {档位: 瓦}); 本机校准优先于内置档案, 都没有则不给数值"""
    cal = load_calibration(ident)
    if cal and cal.get("cpu_ppt_w"):
        return "calibrated", cal["cpu_ppt_w"]
    if model and model.get("cpu_ppt_w"):
        return "model", model["cpu_ppt_w"]
    return None, {}


def gates(ident: dict, dsdt: dict, ec_ok: bool) -> dict:
    """每个功能是否开放及原因 (对应 NvpwrControl 在写入前的平台 / 能力门槛)"""
    def gate(ok, why):
        return {"ok": bool(ok), "why": "" if ok else why}
    ec_write = dsdt.get("WKBC") or dsdt.get("ECRW")
    return {
        "profile": gate(ec_ok and ec_write, "EC 不可读写 (缺少 acpi_call 或 ECRR/ECRW)"),
        "fan_boost": gate(ec_ok and ec_write, "EC 不可读写"),
        "charge": gate(ec_ok and ec_write, "EC 不可读写"),
        "mux": gate(dsdt.get("DGPS") and dsdt.get("IGPS") and ident.get("gfid"),
                    "DSDT 缺少 DGPS/IGPS 或 EC 平台代际为 0"),
        "calibrate": gate(os.path.exists("/sys/class/powercap/intel-rapl:0/energy_uj") and ec_ok,
                          "没有 RAPL 封装功耗计数器"),
    }
