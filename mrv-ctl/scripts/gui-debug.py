#!/usr/bin/env python3
"""以可诊断方式启动 GUI (开发用): 收到 SIGUSR1 时把所有线程的 Python 调用栈写到 stderr"""
import faulthandler
import runpy
import signal
import sys

faulthandler.register(signal.SIGUSR1, all_threads=True)
sys.argv = [sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/mrv-gui"]
runpy.run_path(sys.argv[0], run_name="__main__")
