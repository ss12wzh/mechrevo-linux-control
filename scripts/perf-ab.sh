#!/bin/bash
# A/B 对照: 区分 "EC 档位位" 与 "CPU EPP" 对功耗墙的影响, 以及 MMIO / WKBC 写入通道是否被 EC 感知
# 用法: SUDO_PASS=... perf-ab.sh <输出前缀>     (测试期间停止 mrvd, 结束后恢复静音档并重启 mrvd)
set -u
cd "$(dirname "$0")/.."
OUT="$1.jsonl"; mkdir -p "$(dirname "$OUT")"; : > "$OUT"
LOAD_S=${LOAD_S:-20}; COOL_S=${COOL_S:-20}

S() { if [ -n "${SUDO_PASS:-}" ]; then echo "$SUDO_PASS" | sudo -S -p "" "$@"; else sudo "$@"; fi; }
acpi() { S bash -c "exec 9>>/run/mrvd/acpi_call.lock; flock 9; echo '$1' > /proc/acpi/call; tr -d '\0' < /proc/acpi/call"; }
mode_mmio() { acpi "\\_SB.INOU.ECRW 0x0751 0x$1" >/dev/null; }
mode_wkbc() { acpi "\\_SB.AMW0.WKBC 0x51 0x07 0x$1 0x00" >/dev/null; }
epp() { S bash -c "for f in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do echo $1 > \$f; done"; }
run() {
    sleep 3
    echo "== $1 (0x0751=$(acpi '\_SB.INOU.ECRR 0x0751'), EPP=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference))"
    openssl speed -multi "$(nproc)" -seconds $((LOAD_S + 3)) -bytes 16384 sha256 >/dev/null 2>&1 &
    sleep 1
    S python3 scripts/perf-sample.py --seconds "$LOAD_S" --label "$1" --out "$OUT" | sed 's/"gpu_w.*"ec_last"/ … "ec_last"/'
    pkill -u "$(id -u)" -f '^openssl speed'; sleep "$COOL_S"
}
trap 'pkill -u "$(id -u)" -f "^openssl speed"' EXIT

S systemctl stop mrvd
mode_wkbc 00; epp balance_performance; run "A0 WKBC平衡 + EPP均衡"
mode_mmio 10;                          run "A1 MMIO狂暴 + EPP均衡"
mode_wkbc 10;                          run "A2 WKBC狂暴 + EPP均衡"
mode_wkbc A0; epp performance;         run "A3 WKBC静音 + EPP性能"
mode_wkbc 00; epp power;               run "A4 WKBC平衡 + EPP节能"
mode_wkbc A0
S systemctl start mrvd
echo "结果: $OUT"
