# OrzMC

专门对Minecraft进行Geek的工程项目，包含多个子项目。

## 目录结构

```bash
.
├── AGENTS.md                   # AI 智能体协作单一事实源（仓库性质 / 铁律 / 子模块登记表）
├── app                         # Git子模块：Swift语言开发相关库以及一个macOS/iOS应用程序
├── CONTRIBUTING.md             # 人/机贡献指南（子模块工作流 / 提交规范 / PR 流程）
├── deploy                      # Git子模块：Docker 容器化部署方案（MCSManager / EasyBot / MariaDB / Gatus）
├── docs                        # 伞级文档（文档索引 + 进行中的跨仓方案）
├── HANDOFF.md                  # 跨会话/跨设备交接文档（当前状态 / 下一步 / 会话日志）
├── images                      # README.md 引用的图片资源
├── LICENSE                     # 开源代码许可证
├── plugin                      # Git子模块：自研PaperMC插件 OrzMC
├── profile                     # Git子模块：GitHub 组织主页配置
├── proxy                       # Git子模块：FRP 跨网中转方案（解决跨运营商延迟高/拒连问题）
├── python                      # Git子模块：OrzMC CLI Python源码
├── README.md                   # README.md
├── scripts                     # Minecraft 服务器运维的一些工具脚本
├── site                        # Git子模块：运行PaperMC私服的主页
├── skins                       # Minecraft 玩家皮肤
├── tools                       # Git子模块合集：自研与上游的工具插件
│   ├── DeathChest              # 死亡掉落箱子插件
│   ├── EzShops                 # 商店插件
│   ├── GetMeHome               # 家的传送插件
│   ├── LoginSecurity           # 登录认证插件
│   ├── OrzMCBackup             # 世界优化与备份工具（CLI + 库）
│   ├── rust-thanos             # Rust 编写的区块清理工具
│   └── thanos                  # PHP 编写的区块清理工具
└── webmc                       # Git子模块：主要探索使用Web浏览器连接服务器玩耍的可能性
```

## 协作与文档

本仓库是**产品伞**：子模块改代码，父仓库只 bump 指针。开始改动前请先读：

- [AGENTS.md](AGENTS.md) —— AI 智能体协作事实源（三条铁律、子模块登记表、协作流程）
- [HANDOFF.md](HANDOFF.md) —— 跨会话/跨设备交接文档（当前状态、下一步、会话日志）
- [CONTRIBUTING.md](CONTRIBUTING.md) —— 人/机贡献指南
- [docs/README.md](docs/README.md) —— 伞级文档导航（含各子模块文档入口）
- [docs/product-unification-plan.md](docs/product-unification-plan.md) —— 客户端/服务端工具统一化推进计划

![logo](images/server_member.jpg)
