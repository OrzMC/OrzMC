# OrzMC 运维端（Hermes 侧）落在 Windows 宿主：职责边界 / cron 清单 / 脚本手术纪律

> 适用：所有「巡检、升级、配置审查、版本核对、交付打包」类工作。服务本体跑在 Windows docker 栈，**运维端也从 Mac Hermes 整体搬到 Windows Hermes**，现在 Mac 只读。
> 本文件是 runbook；总是生效的规则在 SKILL.md，本文件给的是细节与验收口径。

## 0. 先确认你在哪个端干活

| 面 | 位置 | 纪律 |
|:--|:--|:--|
| 服务本体 | Windows docker（`orzmc-velocity`/`orzmc-caddy`/`orzmc-easybot` + MCSM 栈）+ 两实例 `InstanceData/<uuid>` | 未变 |
| 巡检/升级/审计/版本核对 | **Windows** `%LOCALAPPDATA%\hermes\scripts\` | 本机直读，**零 SSH、零面板 files API** |
| 技能真源 | **Windows** `%LOCALAPPDATA%\hermes\skills\gaming\orzmc` | Mac 同名目录是只读镜像；改完以 `SKILL.md` sha256 一致 + `skill_self_check.py` PASS 为交付 |
| 凭据 | **Windows** `.env`（orzmc 全部键直搬 + `.bak-<时间戳>`） | 值不入报告/记忆，用 `[REDACTED]` |
| 构建（插件/单测/JaCoCo） | **Windows** Temurin JDK 25 + Gradle（`E:/orzmc/tools`）+ 仓库克隆 `E:/orzmc/src/OrzMC` | 不再依赖 Mac |
| 交付 | **`S:\` 直写**（业务上 = Mac 的「下载」共享）→ 兜底 `E:/orzmc/deliver/` | 验收用真实文件 + 两侧 sha256 |

## 1. Windows 端 cron（8 条，其中 1 条退役）

| job | 计划 | 脚本 |
|:--|:--|:--|
| `orzmc-config-audit` | 周一 09:05 | `orzmc_config_audit.py` |
| `orzmc-version-check` | 周一 09:10 | `mc_version_check.py` |
| `orzmc-weekly-patrol` | 周一 09:15 | `orzmc_weekly_patrol.py` |
| `orzmc-entry-probe` | 30m | `orzmc_entry_probe.py` |
| `orzmc-nethernet-advertise-sync` | 5m | `nethernet_advertise_cron.py` |
| `orzmc-route-guard` | 10m | `orzmc_route_guard.py` |
| `gateway-session-guard` | 5m | `gateway_session_guard.py` |
| ~~`orzmc-bisync-watchdog`~~ | — | **已删除**（单真源后退役）：job 已 `cron remove`，脚本移到 `scripts/_archive-<日期>/`；回滚需先恢复脚本再重建 job |

新 job 用 CLI 建时记得 `--deliver origin`：**CLI 创建默认 `deliver=local`**，boss 收不到报告（静默失败态）。建完 `cron list` 确认 `Deliver:` 行。

## 2. 本地适配器取代面板 API

`mcsm_env.py` 把过去走 MCSM 面板接口的东西全部改成**本机文件系统直读**：`mcsm_list` / `mcsm_scan_plugin_configs` / `mcsm_download` 直接读 `InstanceData/<uuid>/`。收益：没有 3s 限流、没有签发失败、没有 502，秒级完成。

⚠️ 旧的「面板 files API 慢 → 改走 SSH 直读」经验在 Windows 本机上**已经过时**：本机进程直接读盘即可，`ssh win` 只在跨端编排时才有意义。

## 3. 在 Windows 上做「脚本手术」的纪律（踩过血的）

1. **编码**：不清楚源文件编码时，一律 `data.decode("utf-8", errors="surrogateescape")` → 改 → `text.encode("utf-8", errors="surrogateescape")`。用 `errors="replace"` 读回会**不可逆销毁**中文（一条命令废 6 个脚本）。纯 ASCII 插入直接在字节流上做。
2. **UTF-8 guard**：模块级才生效，`import sys` 必须在模块级；插错位置会被 guard 自己的 `except Exception: pass` 静默吞掉。统一跑 `scripts/fix_utf8_guard.py --dir <脚本目录>`（`--check` 只体检）。
3. **改动前后都要编译**：批量 `py_compile` 全目录，`COMPILE_BAD=0` 才算过关。
4. **告警脚本必须自测告警路径**：复制一份注入假 fail，确认 stdout 出现预期告警且 stderr 为空；收尾删临时脚本 + 清 `state/*.json`，再跑生产版确认静默。
5. **误伤救援**：Windows Hermes 的迁移前全量备份 `E:/orzmc/backup/hermes-pre-migration-<ts>.zip`（含 scripts/skills/cron/memories/.env）就是恢复源；从 zip 里按 `scripts/<文件名>` 取原字节还原，再重新做字节安全修改。
6. **批量容器/进程检查**：PowerShell 里 `& a & b` 会变成后台 job（看起来成功、实际未执行）→ 多步用 `;` 串行，或用 `.ps1` 文件跑。
7. **从备份还原后必须重放自己施加的补丁**：还原只回到备份时刻，之后打的业务补丁（如探针口径改动）会丢。还原后 `grep` 自己的标记串（新增变量名 / 日志关键字）确认补丁在位，缺了就重放，再跑自测。
8. **多步操作拆成单条小命令**：把「heredoc 改文件 + `tar`/`scp` 推送 + 远程 PowerShell」混成一条复合命令时，一次审批超时/被拦就是**全盘未执行**，且很容易误以为已生效（后续又基于错前提继续）。审批敏感动作分开发；被 BLOCKED 时不换路重试，等确认后按原样重发。

## 4. 交付到 S: 盘的验收口径

- 链路：cron（Windows Hermes 进程所在 session）→ `orzmc_paths.deliver_dir()` 首选 `S:\` → 落点回读 → **两侧 sha256 一致**才算通。通用工具：`scripts/deliver_file.py <源文件> [--as 名] [--json]`（cron 的 `--script` 不接受参数，包一层一次性脚本再挂 job）。
- `scripts/deliver_selftest.py` 做真实文件闭环（日志 `E:/orzmc/reports/deliver-selftest.log`）；`scripts/deliver_probe.py` 只做目录级探活。
- 写不进看错误码：`WinError 1326` = **该会话**没有可用 SMB 凭据（`cmdkey /list` 在该会话为空即证实）；`WinError 5` 才是权限/路径问题。⚠️ 凭据与盘符映射**按登录会话生效**：实测 cron（交互会话）对 `S:\` 与 UNC 均 `writable=True`，而同一时刻 `ssh win`（Session 0）报 1326 并回退 `E:/orzmc/deliver`。→ **交付验证必须由 cron（一次性 no_agent job）执行**，SSH 里测出「不可写」不代表 cron 不可写（反之亦然）。
- 目录可写 ≠ 交付成功：探针自己有 bug（如 `p / "x_%s" % pid` 优先级错）会把可写目录报成不可写，结论必须用真实文件哈希闭环。

## 5. 验收证据（那一轮实跑的基线）

- 配置审查：`STATUS ✅ SUCCESS`，基准 99 件（核心 7 + 插件 92）vs Exaroton 79 件；报告落 `E:/orzmc/reports/` + 交付目录。
- 版本巡检：全表正常，`folia-26.3-8(STABLE)` 与部署一致。
- 连通性：`proxy` 模式，入口 `Velocity 1.7.2-26.3` + NetherNet `/v1/join` 200 + 后端 RCON 双关（实例刻意停止属预期），exit 0。
- 构建链：`gradlew test` + `integrationTest` + `jacocoTestReport` 全链路跑通（2272 用例，覆盖率 INSTRUCTION 85.3 / BRANCH 73.5 / METHOD 86.4 / CLASS 95.5）。
  - ⚠️ 唯一失败是 **POSIX 路径敏感用例**（断言 `endsWith("/world")`，Windows 路径是 `\world` → 断言翻转）；同 commit CI 全绿 ⇒ 属测试可移植性，不是工具链能力问题。

## 6. 回滚

- Windows：解压迁移前备份 zip 即还原 scripts/skills/cron/memories/.env；`.env` 另有 `.bak-<时间戳>`。
- Mac：脚本在 `~/.hermes/scripts/.archive-<日期>/`，cron 只是 paused（未删）→ `resume` 两条 job 即可复活旧链路。
