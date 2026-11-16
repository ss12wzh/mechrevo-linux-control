# 硬件笔记

验证机型：机械革命苍龙 `CANGLONG Series-M6DR55xx`（Ryzen 9 8945HX + RTX 5060 Laptop，BIOS `N.1.16MRO13`，EC 平台代际 GFID = 23），
Ubuntu 24.04 + 内核 7.0 HWE + NVIDIA 595。本文所有结论都来自这台机器的实测，其它机型需要重新验证。

寄存器语义以主线内核 `drivers/platform/x86/uniwill/uniwill-acpi.c`、tuxedo-drivers 与本机 DSDT（`docs/acpi/`）为准。

## EC 访问通道

| 通道 | ACPI 方法 | 范围 | 用途 |
|---|---|---|---|
| MMIO | `\_SB.INOU.ECRR` / `ECRW`（0xFED50000 + 偏移） | 0x0000–0x0FFF | 直接读写 EC 共享 RAM；mrv-ctl 用它**读** |
| 命令通道 | `\_SB.AMW0.WKBC(地址低, 地址高, 数据低, 数据高)` / `\_SB.PCI0.SBRG.EC0.RECM` | 全 16 位地址 | 填 EC0 命令寄存器（0x8A–0x8E）并置 `WFLG`，由 EC 固件执行写入；OEM 软件经 WMI 走的就是这段代码；mrv-ctl 用它**写** |

- 两个通道读到的值一致。
- 风扇表写入：MMIO 直写被 EC 完全忽略，必须走命令通道。性能模式位：两个通道都有效。
- `/proc/acpi/call` 是全局单缓冲，任何并发调用都必须串行化（mrvd 与脚本共用 `/run/mrvd/acpi_call.lock`）。
- WMI 入口：`\_SB.AMW0.WMBC(_, 4, buf)` → `OEMG`。子命令：`0x0000` 写 / `0x0100` 读 / `0x0200` SCMD / `0x0300` IGPS·DGPS / `0x0400` TjMax / `0x0500` CTAF·PMSF。

## 寄存器表

| 地址 | 名称 | 含义 | 本机结论 |
|---|---|---|---|
| 0x0727 bit6 | CUME | 自定义性能模式 | 为 0；APL1/APL2 仅在自定义模式下生效（未实现） |
| 0x0727 bit7 | — | PL4 以半瓦计 | 为 0 |
| 0x0740 | PROJECT_ID | 机型 ID | 读出 0，tuxedo-drivers 因此识别失败 |
| 0x0741 bit0 | ENABLE_MANUAL_CTRL | 应用接管；内核驱动加载时置位、卸载时清除 | mrv-ctl 不写；旧版会误清 |
| 0x0743–0x0746 | CTGP_DB_* | cTGP / TPP / Dynamic Boost 偏移（本机 0x07 / 0 / 0xFF / 25） | 未使用 |
| 0x0751 bit4 | TBME（上游称 FAN_MODE_TURBO） | 狂暴 | 见"性能模式" |
| 0x0751 bit5 | 上游称 FAN_MODE_HIGH | 静音档写入值 0xA0 的一部分 | — |
| 0x0751 bit6 | FAN_MODE_BOOST | 风扇全速 | **有效**，mrv-ctl 的强冷 |
| 0x0751 bit7 | UFME（上游称 FAN_MODE_USER） | 办公 / 静音 | 见"性能模式" |
| 0x0751 bit0–2 | FAN_LEVEL | 风扇等级 | 被固件忽略 |
| 0x075B / 0x075C | PWM_1 / PWM_2 | 风扇占空比读数（0–200），hwmon `pwm1/2` 的来源 | 只读 |
| 0x0783–0x0786 | APL1 / APL2 / APL4 / APTC | CPU PL1 / PL2 / PL4 / 温度墙 | 非自定义模式下为 0 |
| 0x0788 | CTWA | GPU cTGP 基础功耗（W）→ NPCF.ACBT | 各档均为 50 |
| 0x078E bit6 | UNIVERSAL_FAN_CTRL | 能力位 | 为 1，但自定义风扇表实际不可用 |
| 0x07B9 bit0–6 | CHARGE_CTRL | 充电上限（%），0 = 不限 | 有效 |
| 0x07C5 bit7 / 0x07C6 bit2 | SPLIT_TABLES / ENABLE_UNIVERSAL_FAN_CTRL | 双表分离 / 启用自定义风扇表 | 启用后 GPU 风扇被置 0 |
| 0x07D2 bit0–4 | GFID | EC 平台代际 | 23 |
| 0x07D5 | DBAP | Dynamic Boost（W）→ NPCF.AMAT | 静音 / 平衡 5，狂暴 15 |
| 0x07F7 | ETPP | 平台总处理功耗 TPP（W）→ NPCF.ATPP | 静音 / 平衡 55，狂暴 105 |
| 0x0F00–0x0F5F | 风扇表 | CPU / GPU 各 16 区间：结束温度 / 起始温度 / 转速 | 格式未破解 |
| 0x1801 / 0x1804 / 0x1809 | ITE EC 硬件 PWM | 周期 200 / 风扇 1 / 风扇 2 占空比 | 被 EC 风扇回路持续覆盖 |
| 0x181E–0x1821 | ITE 转速计数 | RPM = 2156250 / 计数 | 与 hwmon 一致 |

## 性能模式

DSDT 的 `PMSC()` 按 `0x0751` 换算模式：只有 TBME = 狂暴，只有 UFME = 办公，两个都为 0 = 平衡，`CUME` = 自定义。
EC 固件在模式位变化后切换 CPU 功耗墙，并自行触发 SCI（`_Q83` / `_Q84` / `_Q9C`），把 cTGP 基础值、Dynamic Boost、TPP 通知 NVIDIA 驱动。
mrv-ctl 写入值与 tuxedo-drivers 一致：静音 `0xA0`、平衡 `0x00`、狂暴 `0x10`。

最终验收（`scripts/perf-bench.sh`，CPU = `openssl speed` 32 进程 45 秒，GPU = `glmark2 --off-screen --size 3840x2160 -b terrain` 40 秒，数据 `docs/perf/4-final.jsonl`）：

| 档位 | CPU 满载稳态 / 峰值 | CPU 频率 | Tctl 最高 | GPU 负载功耗 | GPU 生效上限 | EC TPP / 动态加速 |
|---|---|---|---|---|---|---|
| 静音 | 45.6 / 45.8 W | 2064 MHz | 66°C | 90.6 W | 105 W | 55 / 5 W |
| 平衡 | 86.9 / 86.9 W | 4281 MHz | 80°C | 83.9 W | 85 W | 55 / 5 W |
| 狂暴 | 122.7 / 130.7 W | 4656 MHz | 97°C | 94.4 W | 115 W | 105 / 15 W |

- **CPU 功耗墙只由 EC 档位决定**。A/B 对照（`docs/perf/2-ab.jsonl`）：静音位 + EPP `performance` 仍为 45.7 W，平衡位 + EPP `power` 仍为 86.8 W。
- **GPU 上限升档、降档都会跟随**（`docs/perf/3-downward.jsonl`，狂暴 → 静音 → 平衡：115 → 105 → 85 W）。
- **静音档 GPU 上限高于平衡档**：两档 TPP 相同，静音档 CPU 被压在 45 W，Dynamic Boost 把省下的预算分给 GPU。
- 狂暴档 45 秒稳态低于峰值，是 Tctl 97°C 温度墙所致。
- 更早的"切档无差异"结论是测错了：当时的 GPU 负载只有约 14 W，没有碰到任何功耗墙。
- `nvidia-smi -pl` 被驱动拒绝；超过 115 W 没有安全通道。
- 本机校准（`mrvctl calibrate`）结果 46 / 87 / 132 W，与上表一致。

### 静音档空闲为什么贴着功耗墙

测量时后台有 ToDesk 远程桌面持续占用约 130% CPU（屏幕采集与编码），加上 Cursor / Xorg，32 线程里始终有约 5 个在忙。
这类轻线程负载会被推到最高睿频，再叠加 8945HX（桌面级 Dragon Range）IO die 本身二三十瓦的基础功耗，就顶到了静音档的墙。

温度证实这是真实功耗而不是读数问题：同样的"空闲"，平衡档 Tctl 85°C，静音档 64°C。
（RAPL `core` 域只统计单个核心，满载时也只有 1–2 W，不能用来判断。）

静音档联动关闭 CPU 睿频后，同样后台负载下空闲功耗 46 → 38–40 W。再往下需要减少后台负载，例如把远程桌面软件改为硬件编码。

### CPU 功耗墙的其它通道（未使用）

- `\_SB.PCI0.SBRG.EC0.PLIM(参数ID, 值)` → `\_SB.ALIB(0x0C, …)`：AMD DPTCi，可下发 STAPM / PPT / 温度限制。DSDT 内无调用者，留给 OEM 软件。
- 自定义模式：置 `CUME` 后写 APL1/APL2/APL4。L-Mechrevo 的实机经验是必须先切到自定义模式才能写入。

## 风扇控制

7 次受控实验（`scripts/fan-experiment.py`，日志 `docs/probe/fan-experiment-*.log`）。每次都先存基线、起独立看门狗、超温或低转速立即中止，写入逐一读回；全部恢复成功。

| # | 方案 | 结果 |
|---|---|---|
| 1 | 自定义风扇表，MMIO 写 | 写入读回一致，EC 忽略 |
| 2 | 自定义风扇表，命令通道写 | 同上 |
| 3 | 0x0751 bit6 全速模式 + 写 0x1804/0x1809 | **全速模式有效**（2 秒 2900 → 4690 RPM，清位 3 秒内恢复）；0x1804 被 EC 覆盖 |
| 4 | 置 0x0741 bit0 后启用自定义风扇表 | EC 开始响应，但 GPU 风扇 PWM 被置 0（低转速保护中止） |
| 5 | 同上，转速值改为 100 | 同上，排除刻度问题 |
| 6 | 16 段连续曲线，分离 / 不分离两张表 | 分离：GPU 风扇置 0；不分离：两个风扇都不理会 |
| 7 | 0x0751 USER 模式下改 FAN_LEVEL | 被忽略 |

结论：自定义风扇表在这台 EC 上的读表逻辑与 tuxedo-drivers 的布局不一致，未破解；可用的只有全速模式。
mrv-ctl 据此提供"手动强冷 + 高温自动强冷"。

- 内核 `uniwill_laptop` 的 hwmon `pwm1/2` 为只读（驱动只注册了读回调）。
- tuxedo-drivers 在本机读不到机型 ID，特性探测失败，它的风扇 API 从未真正写过表。
- 无界系列（wujie-fan-control）用的 ITE XRAM 地址（0xD130 等）在本机固件布局不同，不能照搬；硬件 PWM / 转速寄存器布局相同。

## 其它

- `systemctl restart dbus` 会杀掉图形会话；改 D-Bus 配置用 `systemctl kill -s HUP dbus`。
- 独显 runtime suspend 时调用 `nvidia-smi` 会把它唤醒，mrvd 在独显休眠时不查询。
- `cpuinfo_max_freq` 在关闭睿频后变为基础频率，最高睿频读 `amd_pstate_max_freq`。
