# OrzMC 工程审查与整改记录

> **状态**：核心整改已合入，验收与持续改进未完成 ｜ **最后更新**：2026-11-02
> **范围**：父仓库组合及自研核心链路抽样（App、Swift 引擎/基础库、Python CLI、插件和部署），不是对全部子模块的逐行审计或安全认证。最新状态以 `HANDOFF.md` §1、Git 和关联 PR 为准。

项目已有明确的产品伞与子仓库边界、跨语言契约及一致性样例、独立可测的 App 模块和多平台 CI。主要改进集中在失败路径可靠性、依赖组合可复现、真实验收缺口与文档状态。

| 领域 | 审查发现与整改 | 证据 |
|---|---|---|
| 认证 | Python 与 Swift 刷新失败时只在明确 `invalid_grant` 才清会话；先在跨进程锁内保存轮换令牌。Swift POSIX 临时文件从创建起限制权限，锁路径随状态目录 | OrzPythonMC #109、OrzMCKit #104；Windows ACL 仍取决于目录配置 |
| 协议 | App 超时路径通过 `shutdown` 中断读取，由 IO 线程关闭 socket；RCON 多包改为独立结束探针，避免固定等待导致截断 | OrzMCApp #128、#131；非标准代理和不发送空响应的服务端尚未受控实测 |
| 控制台 | MCSManager 实时日志增量拆行、保留行标识，修复多字节和 CRLF 截断；公共容器和跟随状态留在 OrzSwiftKit，Minecraft 文本语义留在 App | OrzMCApp #130；OrzSwiftKit #22；PR 含模拟器前后截图 |
| 构建与版本 | App 锁定版本的构建/发布与上游 HEAD 探测分车道；模拟器冒烟进入 CI；父仓库校验 App 提交锁文件与自有 Swift gitlink | OrzMCApp #129、#132；`scripts/verify/check.py` |
| 测试与文档 | 修正 Python Rich 测试依赖 `TERM=dumb` 的问题，以及 Windows 目录锁测试依赖修改目录时间的问题；历史 CLI 方向显式标记为已替代 | OrzPythonMC #109、OrzMCKit #105；`two-cli-strategy.md` 是现行分工 |

## 未完成与持续工作

- 维护者按既定安排统一真机验收；`testStatusBadgeKeepsSpinningAfterReentering` 的真机判据、exaroton 停止秒数和大字号巡检仍未闭环。
- 控制台通用输入和远程跟随策略尚未统一；应在有明确共同行为和回归测试时逐步收敛，不把供应商差异放进基础 UI 层。
- 大型模型/视图按后续功能变更逐步拆分并补测试，不按文件行数机械拆分。
- Windows 凭据 ACL、RCON 非标准服务端兼容性和 Thread Sanitizer 尚未在本次完成实测；CI 通过不代表这些路径已验证。
