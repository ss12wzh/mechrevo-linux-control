#!/usr/bin/env python3
"""按窗口标题或 0x 开头的窗口 ID 截取 X11 窗口 (开发用): shot.py <标题|0xID> <输出.png>"""
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
pb = Gdk.pixbuf_get_from_window(w, 0, 0, w.get_width(), w.get_height())
pb.savev(out, "png", [], [])
print(out, w.get_width(), w.get_height())
