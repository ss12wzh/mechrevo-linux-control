#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 mrv-ctl 应用图标: 深灰圆角方块 + 白色 M (视觉对标 L-Mechrevo 图标风格)"""
import os
import sys

import cairo

SIZES = [16, 32, 48, 64, 128, 256]
OUT_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons"),
    "/usr/share/icons/hicolor",
]


def draw(size):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(s)
    r = size * 0.22                                  # 圆角半径
    cr.set_source_rgb(0.169, 0.169, 0.169)           # #2b2b2b
    cr.move_to(r, 0)
    cr.line_to(size - r, 0); cr.arc(size - r, r, r, -1.5708, 0)
    cr.line_to(size, size - r); cr.arc(size - r, size - r, r, 0, 1.5708)
    cr.line_to(r, size); cr.arc(r, size - r, r, 1.5708, 3.1416)
    cr.line_to(0, r); cr.arc(r, r, r, 3.1416, 4.7124)
    cr.close_path()
    cr.fill()

    cr.set_source_rgb(1, 1, 1)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(size * 0.62)
    ext = cr.text_extents("M")
    cr.move_to((size - ext.width) / 2 - ext.x_bearing,
               (size - ext.height) / 2 - ext.y_bearing)
    cr.show_text("M")
    return s


def main():
    for d in OUT_DIRS:
        if d.startswith("/usr") and os.geteuid() != 0:
            continue
        for size in SIZES:
            sub = f"{d}/{size}x{size}/apps" if d.startswith("/usr") else d
            os.makedirs(sub, exist_ok=True)
            name = "mrv-ctl.png"
            draw(size).write_to_png(f"{sub}/{name}")
    print("图标已生成")


if __name__ == "__main__":
    main()
