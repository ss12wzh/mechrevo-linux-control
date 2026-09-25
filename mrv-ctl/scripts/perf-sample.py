#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能释放采样器 (需 root: RAPL energy_uj 与 EC 读取)

用法: sudo perf-sample.py --seconds N --label 名称 --out 文件.jsonl
每秒一条: CPU 封装功耗 (RAPL 差分) / 平均与最高频率 / Tctl, GPU 功耗 / 频率 / 利用率 / 温度 / 生效上限,
风扇转速, EC 模式位与功耗参数. 结束时追加一条 summary 并打印.
"""

import fcntl
import glob
import json
import subprocess
import sys
import time

RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"
ACPI_CALL = "/proc/acpi/call"
LOCK_FILE = "/run/mrvd/acpi_call.lock"
EC_REGS = {"mode": 0x0751, "cume": 0x0727, "apl1": 0x0783, "apl2": 0x0784, "apl4": 0x0785,
           "aptc": 0x0786, "ctwa": 0x0788, "dbap": 0x07D5, "etpp": 0x07F7}


def ec_read(addr):
    with open(LOCK_FILE, "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        with open(ACPI_CALL, "w") as f:
            f.write(f"\\_SB.INOU.ECRR 0x{addr:04X}")
        with open(ACPI_CALL) as f:
            out = f.read().replace("\x00", "").strip()
    return int(out, 16) & 0xFF if out.startswith("0x") else None


def hwmon(name):
    for p in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            with open(f"{p}/name") as f:
                if f.read().strip() == name:
                    return p
        except OSError:
            pass
    return None


def rint(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def gpu():
    fields = "power.draw,clocks.sm,utilization.gpu,temperature.gpu,enforced.power.limit"
    try:
        out = subprocess.run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        vals = [v.strip() for v in out.split(",")]
        conv = [float(v) if v.replace(".", "", 1).isdigit() else None for v in vals]
        return dict(zip(("gpu_w", "gpu_mhz", "gpu_util", "gpu_temp", "gpu_limit_w"), conv))
    except Exception:
        return {}


def main():
    args = sys.argv[1:]
    seconds = int(args[args.index("--seconds") + 1])
    label = args[args.index("--label") + 1]
    out_path = args[args.index("--out") + 1]
    k10 = hwmon("k10temp")
    uw = hwmon("uniwill")
    freqs = sorted(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"))

    rows = []
    e0, t0 = rint(RAPL), time.time()
    with open(out_path, "a") as out:
        for i in range(seconds):
            time.sleep(max(0.0, t0 + i + 1 - time.time()))
            e1, t1 = rint(RAPL), time.time()
            fs = [v / 1000 for v in (rint(p) for p in freqs) if v]
            row = {"label": label, "t": i + 1,
                   "cpu_w": round((e1 - e0) / (t1 - (t0 + i)) / 1e6, 1) if e0 is not None and e1 >= e0 else None,
                   "cpu_mhz_avg": round(sum(fs) / len(fs)) if fs else None,
                   "cpu_mhz_max": round(max(fs)) if fs else None,
                   "tctl": (v := rint(f"{k10}/temp1_input")) and v / 1000 if k10 else None,
                   "fan1": rint(f"{uw}/fan1_input") if uw else None,
                   "fan2": rint(f"{uw}/fan2_input") if uw else None}
            e0 = e1
            row.update(gpu())
            if i % 5 == 0:
                row["ec"] = {k: ec_read(a) for k, a in EC_REGS.items()}
            rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()

        def avg(key, part):
            vals = [r[key] for r in part if r.get(key) is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        def mx(key, part):
            vals = [r[key] for r in part if r.get(key) is not None]
            return max(vals) if vals else None

        head, tail = rows[:10], rows[-15:]
        summary = {"label": label, "summary": True, "seconds": seconds,
                   "cpu_w_peak10s": mx("cpu_w", head), "cpu_w_tail15s": avg("cpu_w", tail),
                   "cpu_mhz_tail15s": avg("cpu_mhz_avg", tail), "tctl_max": mx("tctl", rows),
                   "gpu_w_tail15s": avg("gpu_w", tail), "gpu_w_max": mx("gpu_w", rows),
                   "gpu_mhz_tail15s": avg("gpu_mhz", tail), "gpu_limit_w": mx("gpu_limit_w", rows),
                   "gpu_temp_max": mx("gpu_temp", rows), "fan1_tail": avg("fan1", tail),
                   "ec_last": next((r["ec"] for r in reversed(rows) if "ec" in r), None)}
        out.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
