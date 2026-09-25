#!/bin/bash
# build-deb.sh — 构建 mrv-ctl deb 包
set -e
cd "$(dirname "$0")"
VER=$(grep -oP '(?<=^Version: ).*' debian/control)
PKG="mrv-ctl_${VER}_all"
STAGE="/tmp/${PKG}/DEBIAN"

rm -rf "/tmp/${PKG}" && mkdir -p "$STAGE" "/tmp/${PKG}/usr/bin" "/tmp/${PKG}/opt/mrv" "/tmp/${PKG}/lib/systemd/system"

install -m 755 mrvd.py    "/tmp/${PKG}/opt/mrv/mrvd.py"
install -m 755 mrvctl     "/tmp/${PKG}/usr/bin/mrvctl"
install -m 755 mrv-gui    "/tmp/${PKG}/usr/bin/mrv-gui"
install -m 644 mrvd.service "/tmp/${PKG}/lib/systemd/system/mrvd.service"

cp debian/control    "$STAGE/control"
cp debian/postinst   "$STAGE/postinst"; chmod 755 "$STAGE/postinst"
cp debian/prerm      "$STAGE/prerm";    chmod 755 "$STAGE/prerm"

dpkg-deb --build --root-owner-group "/tmp/${PKG}" .
echo "产物: ${PKG}.deb"
