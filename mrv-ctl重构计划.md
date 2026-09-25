# mrv-ctl 重构计划 v2

编写日期：2026-09-25
范围：`mrv-ctl/` 全部代码（`mrvd.py` / `mrvctl` / `mrv-gui` / 打包脚本）+ 两份设计文档
依据：源码逐行审阅 + 本机只读勘察（未写 EC、未改服务、未重启）+ `/home/test/下载` 参考资料 + 本机 `/usr/src/tuxedo-drivers-4.22.3` 源码

v2 相对 v1 的变化：根据你的回复定下了四个方向（第三节）；新增**风扇控制专项**（第六节）；补充了 tccd 冲突、acpi_call 并发、两套 DKMS 冲突的实证。

---

## 〇、结论

项目的**硬件勘察成果是扎实的**（EC 寄存器 0x0751/0x07B9/0x0741、WMI 命令端口、Mux 的 DGPS/IGPS、GPU 功耗墙实测结论），但**代码层处于"能演示、不可信"的状态**：

1. **风扇曲线和超温兜底都不起作用**：它们写 hwmon `pwm1/pwm2`，本机这两个文件是 `0444` 只读。`mrvd` 此刻报告 `fan_mode = curve`，实际风扇由 EC 固件控制。
2. **TUXEDO Control Center（tccd）和 mrvd 在抢同一批硬件**，有日志实证（第一节）。
3. **多处 UI 功能不生效**（灯效下拉、显卡模式三选、重复开关等）。
4. **工程基础缺失**：不是 git 仓库、无测试、单文件 800 行、两套安装方式、两套 tuxedo DKMS 互相冲突、版本号散落 5 处。

**策略：保留 Python + GTK3，先止血 → 拆分守护进程 → 攻风扇 → 换 D-Bus → 统一打包。** 风扇有一条具体可行的技术路线（第六节），需要你配合做一次 sudo 只读检查和一次受控写入实验。

---

## 一、现状盘点与实证

### 组件

| 组件 | 文件 | 行数 | 说明 |
|---|---|---|---|
| 守护进程 | `mrvd.py` | 798 | root；EC（acpi_call）/ hwmon / LED / Mux / 限充 / 遥测 / IPC 全在一个文件 |
| CLI | `mrvctl` | 130 | Unix socket 调 mrvd |
| GUI | `mrv-gui` | 758 | GTK3 + AppIndicator 托盘 + 悬浮窗 + 截屏"毛玻璃" |
| 安装 | `install.sh` / `build-deb.sh` / `debian/*` | ~180 | 两套安装路径 |

### 本机运行时实证（只读获取）

| 现象 | 证据 | 含义 |
|---|---|---|
| tccd 与 mrvd 抢 CPU 能效策略 | tccd 日志反复出现 `CpuWorker: Incorrect settings, reapplying profile` | mrvd 切档改 EPP，tccd 10 秒内又改回去 |
| tccd 在改性能档寄存器 | tccd 日志 `ODMProfileWorker: Using tuxedo-io`；mrvd `status` 读出 `profile = custom(0x20)` | 0x0751 当前值是 tccd 写的，mrvd 不认识，物理键检测联动也因此失效 |
| TCC 风扇控制同样不可用 | tccd 日志 `FanControlWorker: onStart: Fan API not available` | TCC 在本机没有 mrv-ctl 缺的能力 |
| tuxedo 驱动读不到机型 ID | 内核日志 `tuxedo_keyboard: Reading barebone ID failed`；mrvd 经 MMIO 读 0x0740 得 `0` | tuxedo 的特性探测整体失败，这是它风扇 API 不可用的直接原因 |
| 两套 tuxedo DKMS 冲突 | `dkms status`：`tuxedo-drivers/4.22.3`（带 "Diff between built and installed module" 警告）和 `tuxedo-mrv/1.0` 同时安装，模块同名；内核日志 `uniwill_wmi: Unknown symbol uniwill_add_interface` | 实际加载的是哪一份模块不确定 |
| 风扇 PWM 只读 | `/sys/class/hwmon/hwmon9/pwm1`、`pwm2` 权限 `0444` | 上游 `uniwill_laptop` 没有写回调 |
| 模块和配置有重复残留 | `/etc/modules-load.d/mrv.conf` 与 `mrv-ctl.conf` 并存；已装 deb 3.0.0，源码 3.1.0 | 两套安装方式都跑过 |
| GUI 以 root 运行 | `ps`：`root python3 /usr/bin/mrv-gui` | 见 S1-#7 |

机型信息：DMI `board_name = CANGLONG Series-M6DR55xx`，BIOS `N.1.16MRO13`，内核 `7.0.0-34-generic`。现成的 cTGP 接口有两个，当前值都是 `0`：`/sys/devices/platform/INOU0000:00/ctgp_offset`（上游驱动）和 `/sys/devices/platform/tuxedo_nvidia_power_ctrl/ctgp_offset`（tuxedo）。

---

## 二、问题清单（按严重度）

### S1 — 安全 / 数据正确性

| # | 问题 | 位置 |
|---|---|---|
| 1 | **超温兜底无效**：`hw_write("pwm1", PWM_MAX)` 写只读文件必然失败；风扇曲线同理；`status` 仍报告 `fan_mode: curve` | `mrvd.py` 356–373、640 |
| 2 | **acpi_call 并发无锁**：`/proc/acpi/call` 是全局单缓冲，`ec_call` 先写后读；mrvd 的 IPC、档位轮询、风扇、AC 轮询 4 个线程同时调用时，一个线程可能读到另一个线程的结果，导致读回校验误判或档位误检测 | `mrvd.py` 56–60 |
| 3 | **systemd "双保险"是空操作**：`ExecStopPost` 只是 `cat pwm1 > /dev/null` | `mrvd.service` 12 |
| 4 | **IPC 无鉴权**：socket `chmod 0666`，任何本地用户都能切 Mux、改限充 | `mrvd.py` 719 |
| 5 | **与 tccd 双写入者冲突**（见第一节实证） | 系统层 |
| 6 | **fail-closed 只做了一半**：基线只存不用；读回失败不回滚、不锁定；`release_manual()`（风扇交还 auto）用不校验的 `ec_write` | `mrvd.py` 81–87、105–110、273–277 |
| 7 | **GUI 以 root 运行，并把整屏截图写到 `/tmp`**（任何用户可读）；Wayland 下抓屏会失败 | `mrv-gui` 469–485 |
| 8 | **状态文件竞态**：`state_update` 读-改-写无锁，多线程并发会丢更新 | `mrvd.py` 126–129 |

### S2 — 功能 bug

| # | 问题 | 位置 |
|---|---|---|
| 9 | IPC `kbd` 分支丢掉 `effect`，GUI 的"单色 / 流畅彩虹 / 关闭"下拉完全无效 | `mrvd.py` 679–680 |
| 10 | Mux 三选只有两种状态（`igpu` 和 `standard` 都映射成 `0`）；GUI 从不查询当前 Mux 状态 | `mrvd.py` 700；`mrv-gui` 553–635 |
| 11 | "离电自动关灯"出现两次，"更多开关"里那个必然失败 | `mrv-gui` 355–362、394–396 |
| 12 | 切档位强行覆盖用户的灯光和风扇设置；`set_profile` 后轮询线程会再触发一次联动 | `mrvd.py` 178–197、254–268 |
| 13 | `mrvctl status` 在 `current_limit_w` 为 `None` 时崩溃 | `mrvctl` 47 |
| 14 | deb 缺 `python3-pil` 依赖，新机 GUI 启动即 `ImportError` | `debian/control`；`mrv-gui` 22 |
| 15 | 托盘图标文件不在 deb 里 | `build-deb.sh` |
| 16 | 无托盘时关窗只是隐藏，之后无法找回也无法退出 | `mrv-gui` 736–738 |
| 17 | 限充 EC 读失败时显示 `100%`，掩盖故障 | `mrvd.py` 639 |

### S3 — 架构 / 性能

- IPC 单线程串行，单次 `recv` 无分帧；`status` 调两次 `nvidia-smi`（超时合计 13s），GUI 每 2 秒刷新 → 守护进程大部分时间卡在 `nvidia-smi` 上，还会**持续唤醒独显**、阻止它进入省电状态。
- 全局可变状态，无法单测；`status()` 里文件句柄未关闭；`probe_features` 有死代码（482 行）。
- GUI 直接读 sysfs 绕过守护进程；用 `ToggleButton` 模拟单选。
- 硬编码 `AC0` / `BAT0` / `INOU0000:00` / `\_SB.PCI0.SBRG.EC0`。

### S4 — 工程 / 打包 / 文档

- 不是 git 仓库；`.deb` 产物在源码目录。
- 两套安装方式路径冲突；两套 tuxedo DKMS 冲突。
- `postinst` 往其他包的路径写文件（`/usr/lib/systemd/system/nvidia-powerd.service`、`/usr/share/dbus-1/system.d/`），卸载不清理；`.desktop` 现场生成未打包。
- `mrvd.service` 的 `After=` / `WantedBy=` 自相矛盾；`ConditionPathExists=/proc/acpi/call` 会让服务静默不启动。
- `gen-icon.py` 构建时直接写 `/usr/share/icons`。
- 版本号散落且不一致。设计文档过时（性能档寄存器仍写 `0x7A6`，内核写成 6.8）。

---

## 三、已定方向

### 3.1 与 TUXEDO Control Center 的关系 → mrv-ctl 做唯一控制者，移除 TCC

理由（都有本机实证）：

- TCC 在本机**没有提供 mrv-ctl 缺的任何能力**：风扇 API 不可用、机型 ID 读取失败。
- TCC 和 mrvd 已经在**实际互相覆盖**：CPU 策略来回改；性能档被写成 mrvd 不认识的值。
- 为了让 TCC 在 MECHREVO 上加载，维护着一份打补丁的 tuxedo DKMS，还和官方 tuxedo-drivers 冲突，每次内核升级都有风险。
- mrv-ctl 用到的键盘灯、Fn 锁、彩虹、睡眠呼吸灯、温度、转速都由**内核自带的 `uniwill_laptop`** 提供（`/sys/devices/platform/INOU0000:00/`），不依赖 tuxedo。

TCC 独有、mrv-ctl 暂时没有的：CPU 频率上限 / 调速器细调、显示器 YCbCr 兼容开关。前者在阶段 4 视需要补到档位联动里；后者与本项目无关。

执行时全程**不需要重启**：`systemctl disable --now tccd` → 按依赖顺序 `rmmod` tuxedo 模块 → 卸载 `tuxedo-control-center` 与两份 tuxedo DKMS。操作前先确认 `uniwill_laptop` 提供的接口都还在。

### 3.2 风扇 → 尽量实现，单独立项（第六节）

### 3.3 GUI 毛玻璃 → 纯 CSS 半透明，不再截屏

这也是 GUI 改为普通用户运行的前提。

### 3.4 技术栈 → Python + GTK3

你问到的那个 exe（`NvpwrControl.exe`）是这样的：

| | NvpwrControl（Windows） | mrv-ctl（Linux） |
|---|---|---|
| UI | C++ 原生 Win32，自绘深色主题（`app/main.cpp` 1461 行 + `ui_theme.h`），单 exe 约 600KB | Python + GTK3 |
| CLI | `NvpwrCtl.exe`（C++） | `mrvctl`（Python） |
| 特权后端 | 自写 Windows 内核驱动 `Nvpwr.sys`（`driver/driver.c` 1329 行），UI 通过 IOCTL 调它，协议定义放在共享头文件 `shared/nvpwr_ioctl.h` | root 守护进程 `mrvd` |
| 调功耗的方式 | 在内核里直接改 NVIDIA 驱动的内部运行时对象（绑定驱动 616.92 的内存偏移） | 只用官方 / 固件提供的通道 |
| 使用门槛 | 必须关 Secure Boot + 开 Windows 测试签名模式，且锁死 NVIDIA 驱动版本 | 无 |

结论：

- **它的核心手段 Linux 上没有对应物**（README 第 115W 结论依然成立），所以换成 C++/Rust 也换不来功耗解锁。
- **它值得学的是工程做法**，已吸收进本计划：UI / CLI / 后端共用一份协议定义；每个子系统在第一次写入前各自存基线，后续任一步失败就把所有已改的子系统都回滚；固定日志前缀；一键打包诊断信息的脚本（`collect-debug.ps1`）。
- mrv-ctl 的瓶颈是硬件 I/O，不是计算性能；Python + GTK3 在 Ubuntu 上零额外依赖，现有逻辑能直接复用。GTK4 不支持现在用的 AppIndicator 托盘，所以留在 GTK3。
- **唯一可能要写 C 的地方**：如果风扇最终需要访问 `0xFFF` 以上的 EC 地址（第六节的备选路线），会写一个小型 DKMS 内核模块。

---

## 四、重构原则

- 每个 UI 上能点的功能都**真实生效**；不生效的就隐藏或标"不支持"。
- 守护进程是 EC / 风扇 / 灯 / 性能档的**唯一写入者**。
- fail-closed 做完整：基线 → 写入 → 读回 → 失败回滚 + 锁定该功能。
- 硬件访问层可替换为假实现，核心逻辑能在无硬件的环境里测试。
- 不追求超上限 TGP；EC 可写地址只在风扇专项里按协议扩充（第六节）。
- **所有步骤不重启电脑**；Mux 切换（需重启）只做代码与单测；不执行 `systemctl restart dbus`（会杀图形会话，改用 `systemctl kill -s HUP dbus`）。
- 需要 root 的操作由我写好脚本，你在终端用 `sudo` 执行（我当前的 shell 是普通用户）。

---

## 五、目标结构

```text
mrv-ctl/
├── pyproject.toml                 # 版本号唯一来源
├── src/mrv/
│   ├── __init__.py
│   ├── protocol.py                # CLI / GUI / 守护进程共用的方法名、字段、错误码
│   ├── hw/                        # 唯一碰 /proc /sys 的地方
│   │   ├── acpi_call.py           # 进程内锁 + flock，串行化 /proc/acpi/call
│   │   ├── ec.py                  # EcBackend 接口 + AcpiCallEc + FakeEc（测试用）
│   │   ├── ec_txn.py              # 白名单 + 基线 + 读回 + 回滚 + 功能锁定
│   │   ├── fan_table.py           # EC 16 区间风扇表的编码 / 校验 / 读写（第六节）
│   │   ├── hwmon.py               # 温度 / 转速（只读）
│   │   ├── led.py
│   │   ├── power_supply.py        # 自动发现 AC* / BAT*
│   │   ├── nvidia.py              # NVML 优先，nvidia-smi 兜底，不唤醒独显
│   │   └── acpi.py                # DGPS / IGPS
│   ├── model/
│   │   ├── probe.py               # DMI + BIOS + 能力位 → 机型配置
│   │   └── profiles/canglong-m6dr55.toml
│   ├── daemon/
│   │   ├── main.py                # 启动、信号、sd_notify、看门狗
│   │   ├── state.py               # 带锁 StateStore，原子写，schema 版本
│   │   ├── profile.py             # 性能档 + 可配置联动
│   │   ├── fan.py                 # 风扇模式状态机（auto / 固件曲线 / 用户曲线）
│   │   ├── thermal.py             # 超温保护
│   │   ├── telemetry.py           # 后台采样 + 缓存
│   │   └── dbus_service.py        # com.mechrevo.Control1
│   ├── cli.py
│   └── gui/ (app.py, widgets.py, fan_editor.py, style.css)
├── scripts/
│   ├── probe-readonly.sh          # 只读能力探测（sudo 执行）
│   ├── fan-experiment.sh          # 风扇受控写入实验（sudo 执行，自带看门狗）
│   └── collect-debug.sh           # 一键打包诊断信息
├── data/                          # service、D-Bus / polkit、.desktop、图标
├── debian/
└── tests/
```

IPC：**D-Bus 系统总线 + polkit**（`python3-gi` 自带 `Gio.DBus`，不加依赖）。

| 操作 | polkit 策略 |
|---|---|
| 读状态 | 任何人 |
| 性能档、键盘灯、Fn 锁等开关 | 当前活动会话用户免密 |
| 限充、风扇曲线 | 当前活动会话用户免密，其他情况需管理员 |
| Mux 切换 | 每次都要管理员密码 |

---

## 六、风扇控制专项

### 6.1 为什么现在写不进去

| 通道 | 状态 |
|---|---|
| 上游 `uniwill_laptop` hwmon `pwm1/pwm2` | 只读，驱动没有写回调 |
| tuxedo `/dev/tuxedo_io` 的风扇写入 | 依赖 tuxedo 特性探测；本机机型 ID 读取失败，探测整体失败，风扇 API 不可用 |
| mrvd 当前实现 | 写上面那个只读 hwmon，全部失败 |

### 6.2 可行路线（按优先级）

**路线 A（首选）：EC 自定义风扇表，由固件执行**

依据 tuxedo-drivers 源码（`uniwill_keyboard.h` 中的 `has_universal_ec_fan_control` / `uw_init_fan` / `uw_set_fan_auto`）：

- 能力位：EC `0x078E` bit6 = 1 表示支持"通用 EC 风扇控制"。
- 启用：`0x07C5` bit7（两个风扇分别用两张表）+ `0x07C6` bit2（启用 0x0Fxx 自定义表）；前提是 `0x0751` bit6（全速模式）为 0。
- 表结构：每个风扇 16 个区间，CPU 风扇 `0x0F00` 结束温度 / `0x0F10` 起始温度 / `0x0F20` 转速；GPU 风扇相同结构在 `0x0F30` / `0x0F40` / `0x0F50`；转速 0–200（200 = 100%）。
- 恢复固件曲线：清掉两个启用位。

tuxedo 的用法是把表压成"一个大区间 + 用户态实时改转速"，守护进程一旦崩溃，风扇就停在最后那个转速。**我们不这样做**，而是把用户曲线直接编码成完整的 16 区间表，让 EC 固件自己执行：

- 守护进程崩溃、被杀、系统卡死时，风扇**照样按曲线转**，天然 fail-safe。
- 不需要每 2 秒轮询写入，没有振荡问题，也不用"缓降"逻辑。
- 和 L-Mechrevo 的 16 点曲线直接对应。
- **强制约束（用户不可关）**：最后一个区间必须覆盖到 ≥ 100°C 且转速 = 200；任何区间转速不得低于该温度下的安全下限。

这些地址都在 `0x0–0xFFF` 以内，mrvd 现在用的 MMIO 通道（`_SB.INOU.ECRW`）能访问到。README 里写"0x0F00 写入时序未破译"，指的是走 WMI 命令端口的那条路；MMIO 通道写这段地址还**没有测过**，这正是实验要验证的。

**路线 B（备选）：旧式直接转速控制**

`0x0751` bit6 置 1 进入全速模式，再写 `0x1804` / `0x1809` 设定转速。地址超出 `0xFFF`，MMIO 通道够不着，需要 WMI 命令端口，可能要写一个小内核模块。需要守护进程持续维持（tuxedo 每 50 分钟要重启一次控制），崩溃后风扇卡在固定转速，安全性比路线 A 差。

**路线 C（兜底）：粗粒度风扇档位**

`0x07A5` 的 FAN_QUIET（bit2）/ OVERBOOST（bit4）/ HIGH_POWER（bit7）位，做成"安静 / 标准 / 强冷"三档。

**路线 D（长期）**：给上游 `uniwill_laptop` 贡献风扇写入支持，或持续跟踪主线进展。

### 6.3 验证步骤

**第 1 步：只读探测（需要你 sudo 执行，无风险）**

我写 `scripts/probe-readonly.sh`，只调用 `ECRR` 读取：`0x078E`（能力位）、`0x0751`、`0x07C5`、`0x07C6`、`0x07A5`，以及 `0x0F00–0x0F5F` 整张表的当前内容。脚本运行前会先暂停 mrvd 的轮询（避免第二节 S1-#2 的并发问题），结束后恢复。

判断：
- `0x078E` bit6 = 1 → 走路线 A。
- = 0 → 路线 A 可能不适用，转路线 C，同时评估路线 B。

**第 2 步：受控写入实验（需要你单独确认后 sudo 执行）**

只在第 1 步支持路线 A 时进行。实验脚本 `scripts/fan-experiment.sh` 的安全设计：

1. 先把所有将要改动的寄存器和整张表的原值保存到文件。
2. 启动一个独立的看门狗进程：**45 秒后无条件恢复**（清启用位 + 回写原表），脚本本身被 Ctrl+C 或崩溃都会触发。
3. **只往"更凉"的方向测**：第一次写入的表所有区间都是 200（满速）。确认转速明显上升 = 写入生效；满速最多是吵，不会过热。
4. 第二次写一张"中等转速"的表（仍然不低于当前实测转速），确认转速跟着表变。
5. 恢复并读回，确认和原值完全一致。
6. 整个过程每秒记录温度、转速、寄存器值到日志。

**第 3 步：实现**

- `hw/fan_table.py`：曲线 → 16 区间表的编码器（温度点按 5°C 离散化，保证单调、覆盖到 ≥ 100°C）+ 校验 + 读回。
- `daemon/fan.py` 状态机：`auto`（固件默认）↔ `custom`（用户曲线表）。切换都走事务（存基线 → 写表 → 读回 → 启用 → 读回），任何一步失败就回到 `auto` 并锁定该功能。
- 超温保护：用户曲线本身带满速兜底区间；再加一层"温度超过阈值就清启用位、交还固件曲线"。
- 休眠唤醒后重新校验表内容（EC 可能会重置）。
- GUI：16 点曲线编辑器（CPU / GPU 两条），预设"安静 / 均衡 / 强冷"。

### 6.4 出口标准

- 路线 A 成功：用户曲线写入后，负载下转速跟随曲线；`kill -9 mrvd` 后风扇仍按曲线转；执行 `mrvctl fan auto` 后恢复固件行为；休眠唤醒后曲线仍然生效。
- 路线 A 不成功：在文档里写明原因，交付路线 C 的三档风扇，并给出路线 B 的工作量评估。

---

## 七、分阶段实施

### 阶段 0：止血 + 建基线（约 1–2 天）

1. `git init`，现状作为首个提交；产物移到 `dist/` 并加入 `.gitignore`。
2. **清理冲突（需你 sudo 执行我写的脚本，不重启）**：停用并卸载 tccd / TCC；卸载两套 tuxedo DKMS 与已加载的 tuxedo 模块；清理重复的 `modules-load.d` 配置。完成后确认 `INOU0000:00` 下的接口都还在。
3. 修纯代码 bug：S2 #9、#11、#13、#14、#17。
4. **给 `/proc/acpi/call` 加全局锁**（S1-#2），这一步是后面风扇实验的前提。
5. 风扇：守护进程启动时检测 `pwm1` 是否可写；不可写就停用曲线引擎，`status` 如实报告 `fan_control: unsupported`，GUI 隐藏曲线入口。README 同步改为"❌ 暂不可用（专项进行中）"。
6. socket 临时改 `0660` + `mrv` 组。删掉空的 `ExecStopPost`，修正 `After=`。
7. 运行 `scripts/probe-readonly.sh`（风扇专项第 1 步）。

出口标准：tccd 不再运行，mrvd 日志里没有被覆盖的迹象；GUI 每个可点的控件都有真实效果或明确报错；拿到风扇能力位的读数。

### 阶段 1：守护进程拆分 + 可测试（约 1 周）

1. 按第五节拆分，消灭全局变量（用 `Context` 对象注入依赖）。
2. `EcBackend` + `FakeEc`（可注入"读回不一致 / 超时"故障）；`ec_txn.py` 实现完整事务，失败回写基线并锁定功能（`mrvctl unlock <功能>` 解除）。
3. `StateStore` 加锁 + 原子写 + schema 版本，旧 `state.json` 自动迁移。
4. 遥测后台采样 + 缓存；NVIDIA 改用 NVML，只在独显已唤醒时查询。
5. 档位联动移入机型配置、可逐项关闭；用户手动设过的灯光不被档位覆盖；修掉重复触发。
6. Mux：只读 DGPS，确认返回值含义；GUI 按真实可用的状态数显示按钮。
7. 单测覆盖：EC 事务回滚、白名单拒绝、状态迁移、联动去重、机型探测、风扇表编码。

出口标准：无硬件环境下 `pytest` 全绿；本机替换运行后 `mrvctl status` 字段与重构前一致（已修的 bug 除外）。

### 阶段 2：风扇专项实施（约 1–2 周，可与阶段 1 后半段并行）

按第六节第 2、3 步执行。

### 阶段 3：D-Bus + polkit，GUI 降权（约 1 周）

1. 实现 `com.mechrevo.Control1`：`GetStatus / SetProfile / SetChargeLimit / SetKeyboard / SetToggle / SetFanCurve / MuxQuery / MuxSwitch`，信号 `StatusChanged / ProfileChanged`（GUI 由轮询改为订阅，物理性能键即时反映）。
2. polkit 动作按第五节分级；CLI、GUI 改走 D-Bus；删除 Unix socket。
3. GUI 以普通用户运行：纯 CSS 半透明，不截屏；所有状态经守护进程获取；真单选控件；无托盘时关窗即退出。
4. `Type=notify` + `WatchdogSec`。

出口标准：普通用户 `mrvctl profile boost` 成功、`mrvctl mux dgpu` 弹密码；`mrv-gui` 不再是 root；`/tmp` 下没有截图文件。

### 阶段 4：GPU 与 CPU 补充调研（约 3–5 天，低优先级）

- 两个现成的 `ctgp_offset` 接口走的是驱动路径，可能会通知 NVPCF 重新协商，和 README 里直写 EC `0x0744` 的效果不一定相同，值得复测一次（不承诺结果）。
- 把 TCC 原有的 CPU 频率上限 / 调速器设置按需补进档位联动。

### 阶段 5：打包统一（约 3 天）

1. 删除 `install.sh`，只保留 deb。
2. 标准 debhelper（`rules`、`changelog`、`install`、`conffiles`、`postrm`），`dh-python` 安装 Python 包。
3. `.desktop`、图标、service、D-Bus / polkit 作为静态文件打包；图标在构建目录生成。
4. nvidia-powerd 修复文件放 `/etc/`，`purge` 时清理；已有同名 unit 就跳过。
5. 升级迁移：清理 `/etc/modules-load.d/mrv.conf`、`/opt/mrv/`、`/usr/local/bin/mrvctl` 等旧残留。
6. 去掉 `ConditionPathExists`，改为运行时探测并在 `status` 里报告。
7. `lintian` 干净。

出口标准：本机从 3.0.0 升级无需重启、无残留；`apt purge` 后系统干净。

### 阶段 6：文档（约 1 天）

- README 重写：功能矩阵只写实测结果；安装、卸载、排错。
- 两份旧设计文档归档到 `docs/archive/`；新写 `docs/hardware.md` 汇总寄存器结论（含风扇表）。
- `CONTRIBUTING.md`：其他机型如何提交 `probe-readonly.sh` 的输出。

---

## 八、测试与验证

- **单测**（无硬件）：`FakeEc` + 用临时目录伪造的 sysfs 树。
- **本机回归**：每阶段结束跑 `scripts/smoke.sh`（`status`、切一次档位再切回、调一次灯光，比较前后输出）。不含 Mux 切换，不重启。
- **静态检查**：`ruff` + `mypy`（`hw/`、`daemon/` 用严格模式）。
- **打包**：`lintian` + 在容器里演练安装 → 升级 → 卸载。

---

## 九、风险

| 风险 | 对策 |
|---|---|
| 风扇写入实验中 EC 行为异常 | 只往"更凉"方向测；独立看门狗 45 秒无条件恢复；全程记录；基线存盘 |
| MMIO 通道写 `0x0Fxx` 不被 EC 接受 | 转路线 C 交付三档风扇，评估路线 B |
| 卸载 TCC 后丢失某个没注意到的功能 | 卸载前逐项核对 `INOU0000:00` 接口和 GUI 功能；保留 TCC 的 deb 以便回装 |
| 重构期间守护进程回归，把档位或限充写错 | `FakeEc` 先跑通；本机保留旧 deb 可随时回退 |
| D-Bus 策略错误导致服务起不来 | 只用 `HUP` 重载 dbus；socket 版本保留到 D-Bus 版验证通过 |
| 内核升级改变 `uniwill_laptop` 接口 | 能力在运行时探测，机型配置只描述寄存器 |

---

## 十、工作量汇总

| 阶段 | 内容 | 估时 |
|---|---|---|
| 0 | 止血、清理 TCC 冲突、acpi_call 加锁、风扇只读探测 | 1–2 天 |
| 1 | 守护进程拆分 + 单测 | 1 周 |
| 2 | 风扇专项 | 1–2 周（与阶段 1 部分并行） |
| 3 | D-Bus + polkit + GUI 降权 | 1 周 |
| 4 | GPU / CPU 补充调研 | 3–5 天 |
| 5 | 打包统一 | 3 天 |
| 6 | 文档 | 1 天 |
| **合计** | | **约 5–6 周** |

需要你配合的时间点：阶段 0 执行清理脚本和只读探测脚本（各一次 sudo）；阶段 2 确认并执行风扇写入实验（一次 sudo）。
