#!/usr/bin/env python3
"""截取 X11 窗口 (开发用): shot.py <标题|0xID> <输出.png> [--screen]
--screen: 从屏幕 (根窗口) 按窗口位置裁切, 包含合成后的桌面背景, 用于检查透明 / 阴影效果"""
import subprocess
import sys

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gdk, GdkX11

title, out = sys.argv[1], sys.argv[2]
if title.startswith("0x"):
    xid = int(title, 16)
else:
    info = subprocess.run(["xwininfo", "-name", title], capture_output=True, text=True).stdout
    xid = next(int(line.split()[3], 16) for line in info.splitlines() if "Window id:" in line)
w = GdkX11.X11Window.foreign_new_for_display(GdkX11.X11Display.get_default(), xid)
if "--screen" in sys.argv:
    _, x, y = w.get_origin()
    pb = Gdk.pixbuf_get_from_window(Gdk.get_default_root_window(), x, y, w.get_width(), w.get_height())
else:
    pb = Gdk.pixbuf_get_from_window(w, 0, 0, w.get_width(), w.get_height())
pb.savev(out, "png", [], [])
print(out, pb.get_width(), pb.get_height())
