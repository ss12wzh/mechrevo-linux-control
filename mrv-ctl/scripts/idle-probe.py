#!/usr/bin/env python3
"""空闲功耗诊断 (需 root): idle-probe.py [秒数]
输出: 整体 CPU 利用率、各 RAPL 域功耗、C-state 驻留占比、各核频率、占用最高的进程"""
import glob
import subprocess
import sys
import time


def cpu_times():
    v = list(map(int, open("/proc/stat").readline().split()[1:]))
    return sum(v), v[3] + v[4]


def cstates():
    tot = {}
    for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpuidle/state*/"):
        name = open(p + "name").read().strip()
        tot[name] = tot.get(name, 0) + int(open(p + "time").read())
    return tot


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 5
    ncpu = len(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq"))
    doms = {open(d + "/name").read().strip(): d + "/energy_uj" for d in glob.glob("/sys/class/powercap/intel-rapl:*")}
    t0, i0 = cpu_times()
    e0 = {k: int(open(v).read()) for k, v in doms.items()}
    c0 = cstates()
    s = time.time()
    time.sleep(secs)
    t1, i1 = cpu_times()
    e1 = {k: int(open(v).read()) for k, v in doms.items()}
    c1 = cstates()
    dt = time.time() - s
    print(f"CPU 总利用率: {100 * (1 - (i1 - i0) / (t1 - t0)):.1f}% ({ncpu} 线程)")
    for k in doms:
        print(f"RAPL {k}: {(e1[k] - e0[k]) / dt / 1e6:.1f} W")
    print("C-state 驻留:", {n: f"{(c1[n] - c0[n]) / (dt * 1e6 * ncpu) * 100:.0f}%" for n in c1})
    fs = sorted(int(open(p).read()) // 1000 for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"))
    print("核心频率 MHz:", fs)
    print(subprocess.run(["ps", "-eo", "pcpu,comm", "--sort=-pcpu"], capture_output=True, text=True).stdout
          .splitlines()[:8])


if __name__ == "__main__":
    main()
