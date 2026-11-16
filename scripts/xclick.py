#!/usr/bin/env python3
"""用 XTest 在屏幕物理坐标处模拟一次左键点击 (开发用 GUI 冒烟测试): xclick.py <x> <y>"""
import ctypes
import sys
import time

x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
xtst = ctypes.cdll.LoadLibrary("libXtst.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XFlush.argtypes = [ctypes.c_void_p]
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
xtst.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
xtst.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]

x, y = int(sys.argv[1]), int(sys.argv[2])
dpy = x11.XOpenDisplay(None)
if not dpy:
    sys.exit("无法连接 X 显示")
xtst.XTestFakeMotionEvent(dpy, -1, x, y, 0)
x11.XFlush(dpy)
time.sleep(0.15)
xtst.XTestFakeButtonEvent(dpy, 1, 1, 0)
x11.XFlush(dpy)
time.sleep(0.06)
xtst.XTestFakeButtonEvent(dpy, 1, 0, 0)
x11.XFlush(dpy)
x11.XCloseDisplay(dpy)
