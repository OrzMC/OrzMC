# orzmc 技能变更记录存档（< 2.3.2）

> 从 SKILL.md 外置（2026-11-10 整理）。近 3 条留在 SKILL.md。

| 版本 | 日期 | 变更 |
|:--|:--|:--|
| 2.3.1 | 2026-11-09 | **巡检工具三缺陷修复**（均实测验证）：① `orzmc_config_audit.sh` 的 `$MCSM_N）` 全角括号在 bash 3.2 下 unbound → 全脚本改为 `${VAR}` 形式（脚本化扫描拦截）② `nethernet_advertise_sync.py` 的 `advertise-addresses` 正则只认单行，而 Geyser 重启会把值重写成「键一行、值一行」→ 每轮误判为漂移；改为 `read_advertised()/set_advertised()` 兼容单行 flow / 分行 flow / 块列表（4 形态单测通过）③ `orzmc_quality_report.py`：单测失败会连带 `integrationTest` 不跑（实测只剩 test 目录）、缺 jacoco 报告时 `trend(None, prev)` 抛 TypeError、`jacocoTestReport` 依赖 `:test` 导致覆盖率永远刷新不了 → 拆成三段独立跑（`-x test -x integrationTest` 断开依赖）+ None 保护 + 陈旧数据标注；实测输出「单测 ❌ · 集成 ✅ · 覆盖率 ✅」，覆盖率从陈旧 77% 刷新为真实 81.9%。另：**Exaroton 只分配单端口** → `both` 模式在 Exa 不可行，只能 `nethernet` 单端口 + `clone-remote-port: true` + advertise 写「对外端口」（2026-11-09 已按此改 Exa：`clone-remote-port: true`、`advertise-addresses: ["{SERVER_NAME}.exaroton.me:39742"]`，改前备份在 `~/.hermes/tmp/exa-bak-20261109/`）；同日 Exa `OrzMC prison.cell_location` 对齐测试服值。**国内服生产基岩 2026-11-09 已恢复并实测**：`both` 模式 RakNet 75ms + NetherNet 117ms 双通、外部 TCP 3/3、FAIL 0；paper 的 3 份 `upgrade-bak`（135.9MB）已清空，folia 保留 2 份 | |
| 2.3.0 | 2026-11-02 | **技能整理 + NetherNet 生产端定案**：生产端从 `nethernet` 单端口切到 **`both`**（`webrtc-port: 19134`，`advertise-addresses: ["<域名>:19134"]`），实测 RakNet 39~66ms + NetherNet 80~116ms 双通；新增 §5.0 三端现状速查表、§5.5 IP/域名/留空三写法取舍（**宿主机跑 Clash 时必须写数字 IP**）；§5.2 端口清单转为「已放通核对表」；清理变更记录重复行（两条 2.2.0 合并）；三端拓扑/定时任务清单补 Windows 端 Hermes（job `8582a0f31644`） |
| 2.2.1 | 2026-11-02 | **纠正「域名必须 HTTPS」的错误结论**（域名+无证书实测可连；两端 TLS 探测一致）；生产端真因 = STUN 下发地址错，改显式 `advertise-addresses` 后恢复；`connectivity_check.py` 降噪（RakNet 无应答 / 无 HTTPS 信令记 ℹ️ 不记 WARN）；新增 `scripts/conn_watch.py` 玩家入场监听（改完网络配置后验「玩家到底能不能进」）；`both` 模式 `advertise-addresses` 端口必须等于 `webrtc-port` |
| 2.2.0 | 2026-11-02 | **版本纪律定档**（插件只跟 release / 核心只升 STABLE+BETA / OrzMC 豁免，含「先按 version_type 过滤再比版本」坑）；**巡检扩为五部分**（+健康体检 +统一连通性体检）；`connectivity_check.py`（Java + 基岩 RakNet/NetherNet 双协议 + HTTPS 信令 + 外部节点，自动绕 TUN fake-IP）与 `conn_watch.py`（玩家入场监听）；配置审查接 SSH 直读兜底；TPS 改读 `latest.log`（兼容 Folia 分区）；NetherNet 文档按 2.12.1 实装键名重写；Exaroton 文件 API 端点纠正 + `exa_sync_plugins.py` |
| 2.1.1 | 2026-10-20 | NetherNet 实测闭环：`both` 模式双通道验证通过；~~确认「域名入口必须 HTTPS」~~ **（该结论已被 2.2.1 推翻：域名 + 无证书实测可正常进服，仅弹一次 TOFU）**；新增动态公网 IP 同步脚本 `nethernet_advertise_sync.py` + cron `orzmc-nethernet-advertise-sync`；防火墙放行脚本 `bedrock_nethernet_ports.ps1` |
| 2.1.0 | 2026-10-19 | 全面 review：30 篇专题/历史文档补齐分组索引（0 孤儿 0 死链）；7783 字「插件基线」巨型条目外置为 `references/plugin-baseline-legacy.md`（零信息丢失）；修正 26.3 口径（ALPHA→STABLE、Folia 26.3 已出、Geyser 已可用）；新增「脚本位置约定」 |
| 2.0.7 | 2026-10-19 | 第四轮测试服升级基线（Paper 26.3-205 / WE 7.4.6 / WG 7.0.20 / Geyser 2.12.0）+ 新增 `references/nethernet.md`（NetherNet 迁移）+ 升级包交付规范 §2g + Exaroton 核心面板托管事实 |
| 2.0.6 | 2026-09 | 第三轮升级（26.3 实验态）+ 多处巡检/权限/商店知识合并 |
