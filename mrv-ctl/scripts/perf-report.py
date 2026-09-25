#!/usr/bin/env python3
"""把 perf-sample.py 输出的 jsonl 汇总成 Markdown 表格: perf-report.py 文件.jsonl [...]"""
import json
import sys


def fmt(v, suffix=""):
    return "—" if v is None else f"{v:g}{suffix}"


print("| 测试 | CPU 稳态 | CPU 峰值 | CPU 频率 | Tctl 最高 | GPU 稳态 | GPU 生效上限 | 风扇 | EC 模式 / TPP / DB |")
print("|---|---|---|---|---|---|---|---|---|")
for path in sys.argv[1:]:
    for line in open(path):
        d = json.loads(line)
        if not d.get("summary"):
            continue
        e = d.get("ec_last") or {}
        ec = f"0x{e['mode']:02X} / {e['etpp']} / {e['dbap']}" if e.get("mode") is not None else "—"
        print(f"| {d['label']} | {fmt(d['cpu_w_tail15s'], ' W')} | {fmt(d['cpu_w_peak10s'], ' W')} "
              f"| {fmt(d['cpu_mhz_tail15s'], ' MHz')} | {fmt(d['tctl_max'], '°C')} | {fmt(d['gpu_w_tail15s'], ' W')} "
              f"| {fmt(d['gpu_limit_w'], ' W')} | {fmt(d['fan1_tail'])} | {ec} |")
