# mrv-ctl（开发者说明）

项目介绍、安装与使用见仓库根目录 [README](../README.md)；用户说明书见 [`说明书.md`](说明书.md)；硬件结论见 [`docs/hardware.md`](docs/hardware.md)。

## 目录结构

| 路径 | 内容 |
|---|---|
| `mrvd.py` | root 守护进程：EC 读写仲裁、性能模式、风扇、限充、灯效、MUX、遥测、IPC |
| `mrvmodel.py` | 机型适配：识别、档案匹配、能力门槛、功耗墙校准存储 |
| `mrvctl` | 命令行客户端 |
| `mrv-gui` | GTK3 图形界面（普通用户运行） |
| `data/models.json` | 已验证机型档案 |
| `mrvd.service`、`debian/`、`build-deb.sh`、`install.sh` | 打包与安装 |
| `scripts/` | 探测、实验与测量工具（见下） |
| `docs/` | 硬件笔记、ACPI 表、实验与测量数据 |

## 构建与安装

```bash
bash build-deb.sh              # 产物: dist/mrv-ctl_<版本>_all.deb
sudo ./install.sh              # 构建并安装
```

版本号在 `debian/control` 与 `mrv-gui` 的 `VERSION` 两处，发布时同步修改。

## 开发调试

```bash
python3 -m pyflakes mrvd.py mrvmodel.py mrvctl mrv-gui     # 静态检查
MRV_GUI_DEBUG=1 python3 ./mrv-gui                          # 从源码运行 GUI，输出刷新日志
python3 scripts/gui-debug.py ./mrv-gui                     # 收到 SIGUSR1 时打印所有线程栈
sudo systemctl stop mrvd && sudo python3 mrvd.py           # 从源码运行守护进程
```

守护进程日志：`journalctl -u mrvd -f`。

## IPC 协议

Unix socket `/run/mrvd/mrvd.sock`，每个连接发送一个 JSON 请求、读到对端关闭为止得到一个 JSON 响应。
读操作（`status`、`mux query`）任何用户可调用；其余需要 root 或 `sudo` / `admin` / `wheel` / `mrv` 组成员。

| op | 参数 | 说明 |
|---|---|---|
| `status` | — | 整机状态，含 `features`（机型能力）、`platform`（平台参数）、`calibration` |
| `profile` | `value`: office / balanced / boost | 切换性能档 |
| `fan` | `value`: auto / boost | 风扇模式 |
| `fan_guard` | `enabled`, `on`, `off` | 高温自动强冷 |
| `charge` | `value`: 20–100 | 充电上限 |
| `kbd` | `brightness`, `rgb`, `effect` | 键盘灯 |
| `toggle` | `name`, `value` | INOU 开关（白名单） |
| `ac_led_off` | `value` | 离电自动关灯 |
| `mux` | `value`: query / dgpu / standard，`confirm` | 独显直连 |
| `calibrate` | — | 启动功耗墙校准，进度见 `status.calibration` |

## 脚本

| 脚本 | 权限 | 用途 |
|---|---|---|
| `probe-readonly.sh` | root | 只读导出 EC 能力位与自定义风扇表 |
| `fan-experiment.py` | root | 受控风扇写入实验：基线存盘、独立看门狗、超温 / 低转速中止 |
| `perf-bench.sh` | 用户（内部 sudo） | 各档 CPU / GPU 满载测量 |
| `perf-ab.sh` | 用户（内部 sudo） | EC 档位位与 EPP 的 A/B 对照 |
| `perf-sample.py` | root | 每秒采样 RAPL / 频率 / 温度 / GPU / EC 参数 |
| `perf-report.py` | 用户 | 把采样数据汇总成 Markdown 表 |
| `idle-probe.py` | root | 空闲功耗诊断：利用率、RAPL 各域、C-state、频率、进程 |
| `shot.py`、`xclick.py` | 用户 | X11 截图（`--screen` 含桌面背景）与模拟点击，用于 GUI 冒烟测试 |
| `gui-debug.py` | 用户 | 可诊断方式启动 GUI |

涉及 EC 写入的脚本都与 mrvd 共用 `/run/mrvd/acpi_call.lock`。

## 新增机型档案

在 `data/models.json` 追加一项：`match`（`board_prefix`，可选 `vendor` / `cpu_contains` / `gfid`）、`verified`（BIOS、日期、数据来源）、`cpu_ppt_w`（`mrvctl calibrate` 结果）。只写实机测过的数值。
