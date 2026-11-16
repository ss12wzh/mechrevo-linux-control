#!/bin/bash
# mrv-ctl 安装: 构建 deb 并安装 (唯一安装路径, 避免与手工安装的文件冲突)
set -e
cd "$(dirname "$0")"

if [ "$(id -u)" != 0 ]; then
    echo "请用 sudo 运行"; exit 1
fi

bash build-deb.sh
apt-get install -y "./dist/$(ls -t dist | grep -m1 '\.deb$')"
