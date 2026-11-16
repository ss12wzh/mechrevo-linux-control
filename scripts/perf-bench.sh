#!/bin/bash
# 各性能档性能释放对比 (以普通用户运行, 采样时 sudo 调 perf-sample.py)
# 用法: perf-bench.sh <输出前缀> [档位...]      例: perf-bench.sh docs/perf/before office balanced boost
# 环境变量: CPU_S (CPU 满载秒数, 默认 45)  GPU_S (GPU 负载秒数, 默认 40)  COOL_S (冷却秒数, 默认 30)
set -u
cd "$(dirname "$0")/.."
PREFIX=$1; shift
PROFILES=${*:-office balanced boost}
CPU_S=${CPU_S:-45}; GPU_S=${GPU_S:-40}; COOL_S=${COOL_S:-30}
OUT="$PREFIX.jsonl"
mkdir -p "$(dirname "$OUT")"; : > "$OUT"

sample() { if [ -n "${SUDO_PASS:-}" ]; then echo "$SUDO_PASS" | sudo -S -p "" python3 scripts/perf-sample.py "$@"; else sudo python3 scripts/perf-sample.py "$@"; fi; }
cleanup() { pkill -u "$(id -u)" -f '^openssl speed' 2>/dev/null; pkill -u "$(id -u)" -x glmark2 2>/dev/null; }
trap cleanup EXIT

for p in $PROFILES; do
    mrvctl profile "$p" >/dev/null || { echo "切档 $p 失败"; exit 1; }
    sleep 5
    echo "== $p: CPU 满载 ${CPU_S}s"
    openssl speed -multi "$(nproc)" -seconds $((CPU_S + 5)) -bytes 16384 sha256 >/dev/null 2>&1 &
    sleep 1
    sample --seconds "$CPU_S" --label "$p/cpu" --out "$OUT"
    cleanup; sleep "$COOL_S"

    echo "== $p: GPU 负载 ${GPU_S}s"
    __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
        glmark2 --off-screen --size 3840x2160 -b terrain --run-forever >/dev/null 2>&1 &
    sleep 3
    sample --seconds "$GPU_S" --label "$p/gpu" --out "$OUT"
    cleanup; sleep "$COOL_S"
done
echo "结果: $OUT"
