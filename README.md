# mechrevo-linux-control

**机械革命（Uniwill 准系统）游戏本的 Linux 控制台** —— 在 Ubuntu 上找回 Windows 官方控制台的性能模式、独显功耗、风扇强冷、键盘 RGB、电池限充与独显直连。

> Linux control center for MECHREVO (Uniwill barebone) gaming laptops: performance profiles, NVIDIA Dynamic Boost, fan boost, keyboard RGB, charge limit and MUX — with every hardware claim backed by on-device measurements.

| 概览 | 控制 |
|---|---|
| ![概览](mrv-ctl/assets/ui-preview.png) | ![控制](mrv-ctl/assets/ui-preview-controls.png) |

---

## 为什么需要它

机械革命 40/50 系游戏本装上 Ubuntu 后有三个典型问题：

- **独显被锁在 50W**：Ubuntu 的 NVIDIA 驱动包缺少 `nvidia-powerd` 的 systemd unit 和 D-Bus 策略，Dynamic Boost 不工作。
- **没有官方控制台**：性能模式、风扇、灯效、限充只能在 Windows 的官方控制台（GCU 服务）里调。
- **现成方案不适配**：TUXEDO Control Center 在这类机器上读不到机型 ID，风扇 API 不可用，还会和其它工具互相覆盖设置。

mrv-ctl 直接对接固件已经提供的通道（EC 寄存器、DSDT 方法、内核 `uniwill_laptop` 驱动、`nvidia-powerd`），不依赖 Windows 服务，也不修改 NVIDIA 驱动。

## 功能

| 功能 | 状态 | 说明 |
|---|---|---|
| 独显功耗解锁 50W → 115W | ✅ | 安装时自动修复 `nvidia-powerd`（NVPCF / Dynamic Boost） |
| 性能模式 静音 / 平衡 / 狂暴 | ✅ 实测生效 | EC 固件按档位切换 CPU 功耗墙并通知 NVIDIA 驱动；静音档额外关闭 CPU 睿频 |
| 风扇强冷 | ✅ | EC 全速模式，2 秒内 2900 → 4690 RPM |
| 高温自动强冷 | ✅ | 默认 ≥ 88°C 全速、≤ 78°C 交还 EC 曲线，阈值可调 |
| 键盘灯 | ✅ | 亮度、RGB 颜色、彩虹动画、离电自动关灯 |
| 电池限充 | ✅ | 20–100% |
| 独显直连（MUX） | 🧪 实验 | 标准 / 直连切换，重启生效；集显模式未实现 |
| 功耗墙校准 | ✅ | `mrvctl calibrate` 在本机实测各档 CPU 功耗墙 |
| Fn 锁定 / 超级键 / 睡眠呼吸灯 | ✅ | 按机型能力自动显示 |
| 自定义风扇曲线 | ❌ | 本机 EC 不支持，7 次受控实验的结论见 [硬件笔记](mrv-ctl/docs/hardware.md#风扇控制) |
| 独显超过 115W | ❌ | Linux 下没有安全通道（Windows 上的做法是改 NVIDIA 驱动内部对象） |

界面有托盘常驻、可拖动的悬浮窗（CPU / GPU 温度与 GPU 功耗），以及完整的命令行工具。

## 实测性能释放

验证机型：机械革命苍龙（`CANGLONG Series-M6DR55xx`，Ryzen 9 8945HX + RTX 5060 Laptop，BIOS `N.1.16MRO13`），Ubuntu 24.04 + 内核 7.0 HWE + NVIDIA 595。

| 档位 | CPU 满载稳态 / 峰值 | CPU 频率 | Tctl 最高 | 独显负载功耗 | 独显功耗上限 |
|---|---|---|---|---|---|
| 静音 | 45.6 / 45.8 W | 2064 MHz | 66°C | 90.6 W | 105 W |
| 平衡 | 86.9 / 86.9 W | 4281 MHz | 80°C | 83.9 W | 85 W |
| 狂暴 | 122.7 / 130.7 W | 4656 MHz | 97°C | 94.4 W | 115 W |

CPU 负载为 `openssl speed` 32 进程 45 秒，独显负载为 `glmark2` 4K 离屏渲染 40 秒。原始数据在 [`mrv-ctl/docs/perf/`](mrv-ctl/docs/perf/)，测试方法和 A/B 对照见 [硬件笔记](mrv-ctl/docs/hardware.md#性能模式)。

## 支持机型

| 机型 | 状态 |
|---|---|
| 机械革命 苍龙（M6DR55xx, R9 8945HX + RTX 5060） | ✅ 完整实测 |
| 其它机械革命 / Uniwill 准系统游戏本 | ⚠️ 未验证：能装，功能按探测结果开放，不套用任何功耗数值 |

mrv-ctl 启动时会识别机型（DMI、BIOS、EC 平台代际、CPU、GPU），并按 DSDT 里是否存在对应的 ACPI 方法决定开放哪些功能。可以用 `mrvctl info` 查看本机的识别结果。欢迎提交新机型，流程见 [参与贡献](#参与贡献)。

## 安装

### 环境要求

- Ubuntu 24.04（其它 Debian 系发行版未测试）
- 内核自带 `uniwill_laptop` 驱动（主线 6.19 起；Ubuntu 24.04 HWE 7.0 已包含）
- NVIDIA 官方驱动（含 `nvidia-powerd`）
- 依赖：`acpi-call-dkms`、`python3-gi`、`gir1.2-gtk-3.0`、`gir1.2-ayatanaappindicator3-0.1`（安装时自动拉取）

### 从源码安装

```bash
git clone https://github.com/ss12wzh/mechrevo-linux-control.git
cd mechrevo-linux-control/mrv-ctl
sudo ./install.sh          # 构建 deb 并安装，不需要重启
```

安装后会自动：加载 `acpi_call` 与 `uniwill_laptop`、配置开机自动加载、启用守护进程 `mrvd`、修复 `nvidia-powerd`、添加桌面入口和托盘自启动。

卸载：`sudo apt remove mrv-ctl`

> **不要和 TUXEDO Control Center 同时使用。** 两者都会写 EC、CPU 策略和键盘灯，会互相覆盖。mrv-ctl 需要的接口全部由内核自带的 `uniwill_laptop` 提供，不需要 `tuxedo-drivers`。

## 使用

### 图形界面

从应用菜单打开 **mrv-ctl 机械革命控制台**，或运行 `mrv-gui`。

- **概览**：GPU 功耗、CPU / GPU / 风扇 / 电池实时状态，CPU 功耗条按当前档位的功耗墙计算。
- **控制**：风扇强冷与高温自动强冷、显卡模式、充电上限、键盘灯、Fn 锁定等开关。
- 顶部标签切换性能档；右下角设置菜单里有窗口置顶、悬浮窗、校准功耗墙。

### 命令行

```bash
mrvctl status                      # 整机状态
mrvctl profile office|balanced|boost
mrvctl fan boost                   # 强冷（全速）
mrvctl fan auto                    # 交还 EC 固件曲线
mrvctl fan guard on 88 78          # 高温自动强冷：≥88°C 开，≤78°C 关
mrvctl kbd 150                     # 键盘灯亮度 0-200
mrvctl kbd color 0 120 200         # RGB 颜色
mrvctl kbd effect rainbow          # solid | rainbow | off
mrvctl charge 80                   # 充电上限
mrvctl mux query                   # 独显直连状态
mrvctl mux dgpu --yes              # 切换到独显直连（重启生效）
mrvctl info                        # 机型识别 / 档案 / 能力门槛
mrvctl calibrate                   # 本机实测各档 CPU 功耗墙（约 2 分钟，会满载 CPU）
```

写操作需要 root 或 `sudo` / `mrv` 组成员，读状态任何用户都可以。

## 工作原理

```text
mrv-gui (GTK3, 普通用户)      mrvctl (CLI)
          └────────┬───────────┘
                   │  Unix socket /run/mrvd/mrvd.sock（SO_PEERCRED 鉴权）
                   ▼
          mrvd（root 守护进程）
           ├─ 机型适配  mrvmodel: 识别 → 档案 → 能力门槛 → 本机校准
           ├─ 性能模式  EC 0x0751 档位位 + CPU EPP / 睿频联动
           ├─ 风扇      EC 全速模式 + 高温自动强冷（迟滞）
           ├─ 限充      EC 0x07B9
           ├─ 键盘灯    内核 uniwill_laptop multicolor LED
           └─ 独显直连  DSDT DGPS / IGPS
                   │
     acpi_call（\_SB.AMW0.WKBC 命令通道 / \_SB.INOU.ECRR 读）
     uniwill_laptop（温度、转速、灯效）   nvidia-powerd（Dynamic Boost）
```

EC 写入走 OEM 软件同样使用的 WMI 命令通道（由 EC 固件执行写入），读取走 MMIO。寄存器、DSDT 方法与各项实验结论见 [硬件笔记](mrv-ctl/docs/hardware.md)。

## 安全设计

- **EC 写白名单**：只允许写性能模式寄存器与限充寄存器，其它地址一律拒绝；每次写入读回校验。
- **不越界**：不写 EC 固件区、不改 NVIDIA 驱动、不绕过安全启动；没有实机证据的数值不开放。
- **`/proc/acpi/call` 串行化**：线程锁 + 跨进程 `flock`，避免并发调用读到别人的结果。
- **最小权限**：GUI 以普通用户运行；守护进程按调用方 uid 鉴权；sysfs 开关有白名单。
- **风扇兜底**：高温自动强冷由守护进程持续校正；守护进程退出时仍在高温则保持全速。
- **所有硬件实验可复现可回滚**：实验脚本先存基线，再起独立看门狗，超温 / 低转速立即中止并恢复。

## 已知限制

- 自定义风扇曲线在已验证机型上不可用（EC 不读自定义风扇表），只有强冷 / 自动两种风扇模式。
- 独显功耗上限最高到 OEM 标称的 115W。
- 独显直连切换未在压力下长期验证；集显模式（独显完全断电）未实现。
- 静音档在有持续后台负载（如远程桌面软件编码）时仍会贴着 45W 功耗墙，这是真实功耗，原因分析见 [硬件笔记](mrv-ctl/docs/hardware.md#静音档空闲为什么贴着功耗墙)。

## 文档

| 文档 | 内容 |
|---|---|
| [`mrv-ctl/说明书.md`](mrv-ctl/说明书.md) | 面向用户的使用说明书 |
| [`mrv-ctl/docs/hardware.md`](mrv-ctl/docs/hardware.md) | EC 寄存器、DSDT 方法、性能 / 风扇实验结论 |
| [`mrv-ctl/CHANGELOG.md`](mrv-ctl/CHANGELOG.md) | 版本变更记录 |
| [`mrv-ctl/README.md`](mrv-ctl/README.md) | 开发者说明：目录结构、构建、调试脚本 |
| [`docs/重构计划.md`](docs/重构计划.md) | 重构计划与各阶段进展 |
| [`docs/设计方案-v1.md`](docs/设计方案-v1.md) | 最初的设计方案（部分结论已被实测推翻，保留作记录） |

## 参与贡献

**提交新机型**最有价值：

1. 安装后运行 `mrvctl info`，确认各功能门槛；
2. 运行 `mrvctl calibrate` 测出各档 CPU 功耗墙；
3. 用 `mrv-ctl/scripts/probe-readonly.sh`（只读）导出 EC 能力位；
4. 在 Issue 里附上以上输出，或直接修改 [`mrv-ctl/data/models.json`](mrv-ctl/data/models.json) 提交 PR。

涉及 EC 写入的新功能，请先用只读探测和带看门狗的受控实验（参考 `mrv-ctl/scripts/fan-experiment.py`）拿到证据。

## 致谢

- [tuxedocomputers/tuxedo-drivers](https://github.com/tuxedocomputers/tuxedo-drivers) 与主线内核 `drivers/platform/x86/uniwill/`：Uniwill EC 寄存器语义
- [L-Mechrevo](https://github.com/LiangyuLu-lly/L-Mechrevo)：Windows 侧功能清单与自定义模式经验
- NvpwrControl：fail-closed 写入事务与多机型适配思路
- [jpy794/wujie-fan-control](https://github.com/jpy794/wujie-fan-control)、[bavelee/Mechrevo-Fan-Control](https://github.com/bavelee/Mechrevo-Fan-Control)、[xuwd1/mechrevo-wujie14-kmod](https://github.com/xuwd1/mechrevo-wujie14-kmod)：机械革命 EC 逆向资料
- [Javis603/token-monitor](https://github.com/Javis603/token-monitor)：界面设计语言

## 许可证

本项目以 [MIT 许可证](LICENSE) 发布，以下文件除外（另见 [NOTICE](NOTICE)）：

- `mrv-ctl/docs/archive/tuxedo-mrv-1.0.patch`：基于 tuxedo-drivers 的补丁，沿用其 GPL-2.0-or-later 许可证；
- `mrv-ctl/docs/acpi/`：从验证机导出的 ACPI 表，版权归设备厂商所有，仅供研究参考。

## 免责声明

本项目与机械革命（MECHREVO）及其代工厂无任何关系。调整功耗、风扇与 EC 寄存器存在风险，可能影响稳定性和硬件寿命，请自行评估。本软件按"现状"提供，不提供任何担保。
