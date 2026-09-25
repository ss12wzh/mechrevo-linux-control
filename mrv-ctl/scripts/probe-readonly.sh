#!/bin/bash
# 只读探测 Uniwill EC 能力位与自定义风扇表（仅调用 ECRR，不写任何寄存器）
# 用法: sudo scripts/probe-readonly.sh [输出文件]
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "需要 root" >&2; exit 1; }
[ -w /proc/acpi/call ] || { echo "acpi_call 未加载" >&2; exit 1; }

OUT="${1:-probe-$(date +%Y%m%d-%H%M%S).txt}"

# /proc/acpi/call 是全局单缓冲：与 mrvd 共用同一把 flock，探测期间独占
mkdir -p /run/mrvd
exec 9>>/run/mrvd/acpi_call.lock
flock 9

ecrr() {
    local addr=$1 v prev="" same=0
    for _ in 1 2 3 4 5; do
        echo "\\_SB.INOU.ECRR 0x$addr" > /proc/acpi/call
        v=$(tr -d '\0' < /proc/acpi/call)
        if [ "$v" = "$prev" ]; then same=1; break; fi
        prev=$v
    done
    [ $same = 1 ] && echo "$v" || echo "UNSTABLE($v)"
}

bit() { printf '%d' $(( ($1 >> $2) & 1 )); }

{
    echo "# mrv-ctl EC 只读探测 $(date -Is)"
    echo "# board=$(cat /sys/class/dmi/id/board_name) bios=$(cat /sys/class/dmi/id/bios_version) kernel=$(uname -r)"
    echo
    echo "## 单寄存器"
    for a in 0740 0741 0743 0744 0745 0746 0751 078E 07A5 07A6 07B9 07C5 07C6; do
        echo "0x$a = $(ecrr $a)"
    done
    echo
    cap=$(ecrr 078E); c5=$(ecrr 07C5); c6=$(ecrr 07C6); m=$(ecrr 0751)
    if [[ $cap == 0x* && $c5 == 0x* && $c6 == 0x* && $m == 0x* ]]; then
        echo "## 解读"
        echo "通用 EC 风扇控制能力 (0x078E bit6) = $(bit $((cap)) 6)"
        echo "双表分离 (0x07C5 bit7)             = $(bit $((c5)) 7)"
        echo "自定义表启用 (0x07C6 bit2)          = $(bit $((c6)) 2)"
        echo "全速模式 (0x0751 bit6)              = $(bit $((m)) 6)"
    fi
    echo
    echo "## 自定义风扇表 0x0F00-0x0F5F（每行 16 区间）"
    for row in 0F0 0F1 0F2 0F3 0F4 0F5; do
        line=""
        for i in 0 1 2 3 4 5 6 7 8 9 A B C D E F; do
            v=$(ecrr "${row}${i}")
            [[ $v == 0x* ]] && line+=$(printf '%3d ' $((v))) || line+="  ? "
        done
        case $row in
            0F0) name="CPU 结束温度";; 0F1) name="CPU 起始温度";; 0F2) name="CPU 转速    ";;
            0F3) name="GPU 结束温度";; 0F4) name="GPU 起始温度";; 0F5) name="GPU 转速    ";;
        esac
        echo "0x${row}0 $name: $line"
    done
    echo
    echo "## hwmon"
    for f in /sys/class/hwmon/hwmon*/name; do
        [ "$(cat "$f")" = uniwill ] || continue
        d=$(dirname "$f")
        for n in temp1_input temp2_input fan1_input fan2_input pwm1 pwm2; do
            echo "$n = $(cat "$d/$n" 2>/dev/null)"
        done
    done
} | tee "$OUT"
echo "已保存: $OUT" >&2
