#!/bin/bash
# build-deb.sh — 构建 mrv-ctl deb 包到 dist/
set -e
cd "$(dirname "$0")"
VER=$(grep -oP '(?<=^Version: ).*' debian/control)
PKG="mrv-ctl_${VER}_all"
ROOT="$(mktemp -d)/${PKG}"

mkdir -p "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/opt/mrv" "$ROOT/lib/systemd/system" \
         "$ROOT/usr/share/icons/hicolor/256x256/apps" "$ROOT/usr/share/mrv-ctl"

install -m 755 mrvd.py      "$ROOT/opt/mrv/mrvd.py"
install -m 644 mrvmodel.py  "$ROOT/opt/mrv/mrvmodel.py"
install -m 644 data/models.json "$ROOT/usr/share/mrv-ctl/models.json"
install -m 755 mrvctl       "$ROOT/usr/bin/mrvctl"
install -m 755 mrv-gui      "$ROOT/usr/bin/mrv-gui"
install -m 644 mrvd.service "$ROOT/lib/systemd/system/mrvd.service"
install -m 644 icons/mrv-ctl.png "$ROOT/usr/share/icons/hicolor/256x256/apps/mrv-ctl.png"

install -m 644 debian/control  "$ROOT/DEBIAN/control"
install -m 755 debian/postinst "$ROOT/DEBIAN/postinst"
install -m 755 debian/prerm    "$ROOT/DEBIAN/prerm"

mkdir -p dist
dpkg-deb --build --root-owner-group "$ROOT" dist/
rm -rf "$(dirname "$ROOT")"
echo "产物: dist/${PKG}.deb"
