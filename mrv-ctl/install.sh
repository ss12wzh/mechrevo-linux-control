#!/bin/bash
# mrv-ctl 安装脚本 — 机械革命苍龙系列 Ubuntu 24.04
# 依赖: acpi-call-dkms, 内核 uniwill_laptop 驱动 (>= 6.12 自带)
set -e

if [ "$(id -u)" != 0 ]; then
    echo "请用 sudo 运行"; exit 1
fi

echo "== 1/5 依赖 =="
apt-get install -y acpi-call-dkms >/dev/null 2>&1 || true
modprobe acpi_call 2>/dev/null || echo "WARN: acpi_call 加载失败, 性能模式将不可用"

echo "== 2/5 内核 uniwill_laptop 驱动 (force, 适配非 TUXEDO 品牌) =="
modprobe uniwill_laptop force=1 2>/dev/null \
    || echo "WARN: uniwill_laptop 加载失败, 风扇/背光接口不可用"
# 持久化: 开机自动 force 加载
cat > /etc/modprobe.d/mrv-uniwill.conf <<'EOF'
# mrv-ctl: 强制在 MECHREVO(Uniwill 准系统) 上加载 uniwill_laptop
options uniwill_laptop force=1
EOF
cat > /etc/modules-load.d/mrv.conf <<'EOF'
acpi_call
uniwill_laptop
EOF

echo "== 3/5 程序文件 =="
install -d /opt/mrv
install -m 755 "$(dirname "$0")/mrvd.py" /opt/mrv/mrvd.py
install -m 755 "$(dirname "$0")/mrvctl" /usr/local/bin/mrvctl

echo "== 4/5 systemd 服务 =="
install -m 644 "$(dirname "$0")/mrvd.service" /etc/systemd/system/mrvd.service
systemctl daemon-reload
systemctl enable --now mrvd

echo "== 5/5 完成 =="
sleep 2
systemctl --no-pager status mrvd | head -4
echo
echo "试用: mrvctl status"
echo "     mrvctl profile boost   # 狂暴模式"
