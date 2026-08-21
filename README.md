# OrzMC

专门对Minecraft进行Geek的工程项目，包含多个子项目。

## 目录结构

```bash
.
├── app                         # Git子模块：Swift语言开发相关库以及一个macOS/iOS应用程序
├── deploy                      # Git子模块：Docker 容器化部署方案（MCSManager / EasyBot / MariaDB / Gatus）
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

![logo](images/server_member.jpg)
