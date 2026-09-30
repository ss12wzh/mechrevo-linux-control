# MechRevo Linux 控制台（暂名 mrv-ctl）设计方案 v1.0

设计日期：2026-09-24
测试设备：本机机械革命苍龙系列（MECHREVO CANGLONG Series）实机勘察
对标产品：L-Mechrevo（Windows 托盘控制台）+ NvpwrControl 4090mod（Windows TGP 解锁器）

---

## 〇、本机实测勘察结论（全部为实机验证，非推测）

| 项目 | 实测结果 | 对设计的意义 |
|---|---|---|
| 机型/平台 | MECHREVO 苍龙系列（CANGLONG），AMD Ryzen 9 8945HX + RTX 5060 Laptop | 40/50 系游戏本，正是目标机型 |
| GPU 功耗现状 | `nvidia-smi -q -d POWER`：Current/Default **50W**，**Max 115W**（OEM 上限） | 「功耗锁 50W」问题实锤；115W 与 NvpwrControl 文档中 5050/5060/5070 的 OEM 115W 档完全吻合 |
| NVIDIA 驱动 | 595.91.07（Ubuntu 官方 apt 源，open 内核模块） | 可用 nvidia-powerd / NVML 生态 |
| DSDT EC 协议 | `_SB.INOU.ECRR/ECRW` 存在，经 `0xFED50000 + offset` MMIO 读写 EC RAM | 与 Wujie 14XA 逆向笔记**完全一致**，Uniwill INOU 协议确认，EC 读写通道有固件官方入口 |
| WMI 设备 | `ABBC0F6A ~ ABBC0F72` 全套 Uniwill WMI GUID（含 603E9613 事件 GUID） | 与 tuxedo-drivers 的 `uniwill_wmi` 完全匹配，**大概率可直接复用** |
| NVPCF | DSDT 含 `NPCF`（NVIDIA Platform Control Framework）设备 + `ATPP`（平台总功耗预算，按机型 ID 写 0x258~0x640）+ `PWDB`（Dynamic Boost ACPI 写入 DBEN/AMAT） | SBIOS **原生支持** Dynamic Boost 平台接口，nvidia-powerd 路线可行 |
| 性能模式 | DSDT `PMSF()` 方法按 `CSTM`（自定义模式标志）/`TBME`/`UFME` 切换，联动 `ATPP` 和 EC；EC 有 `_Q83/_Q84/_Q9C` 查询 | 性能模式（办公/平衡/狂暴）走 EC/ACPI 官方逻辑，不需要硬逆向 |
| nvidia-powerd | `/usr/bin/nvidia-powerd` 存在，可直接运行，**但 systemd unit 缺失**（Ubuntu 打包已知坑） | 只需补一个 unit 文件即可启用 Dynamic Boost |
| ec_sys | `modprobe ec_sys` 成功，`/sys/kernel/debug/ec/ec0` 可读 | EC RAM 读写通道之一可用 |
| platform_profile | 内核 6.8（7.0.0-34-generic HWE）未暴露 `/sys/firmware/acpi/platform_profile` | 需要 out-of-tree 驱动（tuxedo-drivers DKMS）或自研模块补齐 |
| 电池限充 | 无 `charge_control_end_threshold` 标准接口 | 需走 EC 寄存器（Uniwell 机型通用做法） |

**结论：本机是标准 Uniwill 准系统 + NVPCF 双通道齐全的机型，Linux 侧控制台的全部硬件通道均已确认存在。**

---

## 一、设计目标与范围

### 目标
1. 在 Ubuntu 24.04 上复刻 L-Mechrevo 的核心功能：性能模式切换、GPU TGP 解锁、风扇曲线、键盘背光、电池限充。
2. 解决「装 Ubuntu 后独显锁 50W」的核心痛点，目标至少恢复 OEM 115W 档。
3. 借鉴 NvpwrControl 的 **fail-closed 安全设计**（基线保存 → 分阶段写入 → 读回验证 → 失败回滚）。

### 明确不做（v1）
- 275W 级超规格 TGP（NvpwrControl 明确未建立契约，Linux 侧同样不碰）
- 独显直连 Mux 切换（需重启 + 无标准接口，暂缓）
- 灯条/Logo 灯等外设型功能（协议私有度高）
- 任何绕过驱动签名/安全启动的机制

---

## 二、总体架构（三层）

```text
┌─────────────────────────────────────────────────────────┐
│  UI 层                                                   │
│  mrvctl (CLI, 优先)  +  mrv-tray (GTK4 托盘, P2)        │
├─────────────────────────────────────────────────────────┤
│  守护进程层  mrvd (systemd service + D-Bus)              │
│  · 风扇曲线引擎（16点，带超时回退 auto 兜底）              │
│  · 遥测采集（CPU/GPU 温度功耗 → hwmon/nvml）              │
│  · 模式状态机 + 写入仲裁（唯一写入者，防冲突）              │
├─────────────────────────────────────────────────────────┤
│  内核层                                                  │
│  ① tuxedo-drivers (DKMS, uniwill_wmi)  —— 性能模式/风扇/灯│
│  ② ec_sys (read) / uniwill EC RAM (write) —— 限充等      │
│  ③ nvidia-powerd (NVPCF/NVML) —— Dynamic Boost          │
└─────────────────────────────────────────────────────────┘
```

**关键决策：优先复用 tuxedo-drivers，不重复造内核轮子。** 理由：本机 WMI GUID 全套匹配；tuxedo 的 `uniwill_wmi` 已实现 performance_profile、风扇转速读写、键盘背光、限充；有 DKMS 打包与中文社区 fork。自研内核模块仅在 tuxedo 覆盖不到的寄存器时作为补充（用 `ec_sys` 或小型 out-of-tree 模块）。

---

## 三、功能模块设计

### 3.1 性能模式（办公 / 平衡 / 狂暴）— P0

- **通道**：本机 DSDT 的 `PMSF()` 由 `CSTM/TBME/UFME` 标志驱动，对应 Uniwill 标准 EC 寄存器（性能模式寄存器，wujie 系项目实测为 0x7A6：0x8 长续航 / 0x18 平衡 / 0x28 狂暴——**需本机 acpi_call 首验**）。
- **实现顺序**：
  1. P0 验证：`modprobe acpi_call` 后调 `_SB.INOU.ECRW(0x7A6, 0x28)`，观察 EC `_Q83/_Q84/_Q9C` 事件与风扇/TGP 变化；
  2. 正式：加载 tuxedo-drivers 后走 `platform_profile` 标准接口暴露三档；
  3. `mrvd` 将三档映射为：办公（`low-power`）/ 平衡（`balanced`）/ 狂暴（`performance`）。
- **验收**：切狂暴档后 `nvidia-smi -q -d POWER` 的 Current Limit 明显上移。

### 3.2 GPU 功耗解锁（核心痛点，50W → 115W+）— P0/P1

Linux 侧没有 Nvpwr.sys 那种直接改 nvlddmkm 内核对象的路径，改用三条并行通道（均为官方/固件 sanctioned 通道）：

| 通道 | 作用 | 动作 |
|---|---|---|
| ① nvidia-powerd (NVPCF) | Dynamic Boost 25W 档位协商 | 补写 systemd unit 并启用（二进制已在，仅缺 unit——实测可直接运行） |
| ② EC 狂暴模式 | 放开 EC 侧 TGP 窗口（联动 `ATPP` 平台功耗预算 0x258~0x640） | 3.1 的性能模式切换自动带动 |
| ③ nvidia-smi / NVML | 运行时功耗帽设置（若本机未封 `-pl`） | P1 实测；Max 115W 档由 ①② 解锁 |

- **目标**：狂暴档 + Dynamic Boost 下达到 OEM 设计上限（5060 Laptop 理论 115W 基础 + 25W DB）。
- **不做**：NvpwrControl 的 120–140W 超上限档与 XMG 250W 契约。Windows 侧该功能依赖对 nvlddmkm 运行时对象的直接改写（root+0x3D14/3D18/3D24 等），在 Linux 上没有对应且风险可控的入口；若后续社区出现 Linux 等价物，作为 P3 评估。
- **验收**：FurMark/glmark 压力测试下 `nvidia-smi` 功耗稳定 ≥115W，重启后状态可复现。

### 3.3 风扇曲线 — P1

- **通道**：tuxedo-drivers 的 uniwill 风扇接口（CPU/GPU 两路 PWM + 转速遥测）；若本机 EC 世代（GFID）不在 tuxedo 支持列表，回退方案 = 参照 wujie-fan-control 用 EC RAM 直写。
- **引擎**（在 `mrvd` 内，不在内核）：
  - 16 点温度→占空比曲线（对齐 L-Mechrevo 的 16 点曲线格式）；
  - **安全兜底（不可关闭）**：写入后 N 秒内无有效读回 → 自动回 EC auto 模式；守护进程异常退出由 systemd `ExecStopPost` 恢复 auto；温度超阈值 95°C → 强制 100% PWM。
- **验收**：断电/杀进程后风扇回 auto；曲线写入后转速读回一致。

### 3.4 键盘背光 — P1

- 单色亮度：tuxedo-drivers 已覆盖（Uniwill 通用）。
- RGB（若有）：tuxedo 的 uniwill LED 接口或 ite_829x 路线，按实测机型再定。

### 3.5 电池限充 — P2

- 通道：Uniwill EC 限充寄存器（tuxedo-drivers 部分机型已实现，暴露为 `/sys/class/power_supply/BAT0/charge_control_end_threshold`）。
- 若 tuxedo 未覆盖本机：在自研补充模块中写 EC，并同样暴露标准 sysfs 接口（保持与内核生态一致，不搞私有 ioctl）。

### 3.6 守护进程 mrvd — P1

- systemd service（`Type=notify`，`Restart=on-failure`）；
- D-Bus 接口（`com.mechrevo.control`）：`SetProfile / GetStatus / SetFanCurve / SetChargeThreshold`；
- **写入仲裁**：所有 EC/WMI 写操作只允许经 mrvd（单一写入者原则，避免 tuxedo CC / 其他工具打架）；
- 状态持久化：`/var/lib/mrvd/state.json`，开机按上次模式恢复；
- 日志：journald + JSONL 事件日志（模式切换、写入、读回验证、回滚全部记录，参照 NvpwrControl 的 `[NVPWR]` 日志风格）。

### 3.7 CLI 与 UI — P1/P2

- `mrvctl`（Rust 或 Go，单二进制）：`mrvctl profile performance`、`mrvctl fan set <curve>`、`mrvctl status`；
- P2：GTK4 托盘（Rust + libadwaita），布局对标 L-Mechrevo：模式三键 + TGP 滑条 + 风扇曲线编辑器 + 限充开关。

---

## 四、安全设计（借鉴 NvpwrControl 的 fail-closed 原则）

1. **基线先行**：每次会话首次写入前保存 EC 相关寄存器原始值（SaveBaseline 对应物）。
2. **读回验证**：每笔 EC 写入后读回比对，不一致即回滚并锁定该功能。
3. **白名单寄存器**：只写经过本机验证的寄存器地址，未知寄存器一律拒绝（不提供通用 EC 写命令给普通用户）。
4. **风扇独立守护**：风扇兜底逻辑放在 mrvd 顶层信号处理器 + systemd 停机钩子，双保险。
5. **BIOS 版本绑定**：配置文件按 `BIOS 版本 + GFID + MOID（机型 ID）` 区分，DSDT 变化即拒绝写入并提示重新校准。
6. **不碰的东西**：EC 固件更新区、电池充放电参数区、未知地址段。

---

## 五、实施路线

| 阶段 | 内容 | 工作量 | 出口标准 |
|---|---|---|---|
| **P0 协议验证**（本周） | ① acpi_call 验证 0x7A6 三档切换 + 观察风扇/TGP 联动；② 补 nvidia-powerd unit 并确认 DB 生效；③ 装 tuxedo-drivers DKMS 测试性能模式/风扇/背光接口覆盖度；④ 试 `nvidia-smi -pl 115` | 2–4 天 | 狂暴档下 nvidia-smi 功耗上限 ≥115W，全程无风扇失控 |
| **P1 MVP** | mrvd + mrvctl：模式切换（含开机恢复）、nvidia-powerd 集成、风扇曲线（含兜底）、键盘背光 | 2–3 周 | 本机日常可用，压力测试 24h 稳定 |
| **P2 完整版** | 电池限充、GTK 托盘、遥测面板、多机型配置框架（按 GFID/MOID 分档） | 1–2 月 | 覆盖 L-Mechrevo 功能清单核心项 |
| **P3 生态** | PPA 打包、其他 40/50 系机型众测、（评估）Linux 侧超上限 TGP 的可行入口 | 持续 | — |

---

## 六、P0 验证清单（明天可执行的命令级计划）

```bash
# 1. 性能模式验证（狂暴档）
sudo modprobe acpi_call
echo '\_SB.INOU.ECRR(0x7A6)' > /proc/acpi/call; cat /proc/acpi/call  # 读当前档
echo '\_SB.INOU.ECRW(0x7A6, 0x28)' > /proc/acpi/call                 # 切狂暴
nvidia-smi -q -d POWER | grep -E "Current|Max Power"                  # 看上限变化
# 注意：先确认 0x7A6 在本机 GFID 世代有效；失败值立即回写原值

# 2. nvidia-powerd 修复
sudo tee /usr/lib/systemd/system/nvidia-powerd.service <<'EOF'
[Unit]
Description=NVIDIA Power Daemon
After=multi-user.target
[Service]
Type=simple
ExecStart=/usr/bin/nvidia-powerd
Restart=always
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now nvidia-powerd
nvidia-smi -q -d POWER | grep -i boost  # 确认 Dynamic Boost 生效

# 3. tuxedo-drivers 覆盖度测试
git clone https://github.com/tuxedocomputers/tuxedo-drivers && cd tuxedo-drivers
make && sudo make install                # 或直接用 tuxedo-control-center 仓库的 deb
ls /sys/bus/platform/drivers/uniwill_wmi/  # 确认绑定
cat /sys/firmware/acpi/platform_profile_choices  # 期待出现 low-power/balanced/performance

# 4. 风扇/背光/限充接口清点
grep -r . /sys/class/hwmon/hwmon*/fan*_input 2>/dev/null
ls /sys/class/leds/ | grep -i "uniwill\|kbd"
cat /sys/class/power_supply/BAT0/charge_control_end_threshold 2>/dev/null
```

---

## 七、风险与对策

| 风险 | 对策 |
|---|---|
| EC 写错寄存器致风扇停转 | 白名单 + 兜底回 auto + systemd 停机钩子（见第四节） |
| 0x7A6 等寄存器随 EC 固件漂移 | 配置按 BIOS 版本 + GFID 绑定，校验失败拒绝写入 |
| tuxedo-drivers 对本机 GFID 世代覆盖不全 | P0 第 3 步先行实测；缺口部分用 ec_sys/自研小模块补 |
| nvidia-powerd 与 nvidia 驱动版本耦合 | unit 中加 `nvidia-persistenced` 联动；驱动升级纳入回归项 |
| 内核升级破坏 DKMS | 只用 DKMS 标准打包，CI 里加 6.8/6.11/HWE 双内核测试 |

---

## 八、与两个 Windows 项目的功能对照

| L-Mechrevo / NvpwrControl 功能 | 本方案对应 | 阶段 |
|---|---|---|
| 性能模式三档 | EC/WMI（PMSF）→ platform_profile | P0 |
| GPU TGP 目标（5060: 115W OEM 档） | 狂暴档 + nvidia-powerd DB | P0/P1 |
| TGP 120–140W 超上限（Nvpwr 私有路径） | 不做（Linux 无安全入口） | — |
| Dynamic Boost | nvidia-powerd（NVPCF，SBIOS 已支持） | P0 |
| 16 点风扇曲线 | mrvd 引擎 + tuxedo 接口 | P1 |
| 键盘背光 | tuxedo-drivers | P1 |
| 电池限充 | EC → 标准 sysfs | P2 |
| 遥测面板 | mrvd 遥测 + UI | P2 |
| 读写基线/回滚 | mrvd fail-closed 状态机 | P1 |
