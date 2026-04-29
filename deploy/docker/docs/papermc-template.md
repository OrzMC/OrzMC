# PaperMC 实例模板建议

本文档用于配合 `deploy/docker/.env.example.full`，帮助在 `MCSManager` 中创建 `PaperMC` Docker 实例。

## 建议的模板拆分

- `PaperMC Test`
  - 使用 `PAPERMC_TEST_*` 参数
  - 面向功能验证、插件测试、临时活动服
- `PaperMC Prod`
  - 使用 `PAPERMC_PROD_*` 参数
  - 面向正式生存服

## 必填字段

| 字段 | 测试服示例 | 正式服示例 | 说明 |
|---|---|---|---|
| 实例名 | `papermc-test` | `papermc-main` | 同时建议作为目录名和容器名 |
| 显示名 | `OrzMC Test` | `OrzMC Main` | 面板显示名称 |
| 镜像名 | `eclipse-temurin:21-jre` | `eclipse-temurin:21-jre` | 已验证可运行的 Java 21 基础镜像 |
| 服务端口 | `25566` | `25565` | 测试服避开正式服默认端口 |
| 端口映射 | `25566:25566` | `25565:25565` | 宿主机到容器映射 |
| 服务目录 | `/srv/orzmc/instances/papermc-test/server` | `/srv/orzmc/instances/papermc-main/server` | 持久化世界、插件、配置 |
| 挂载定义 | `/srv/orzmc/instances/papermc-test/server:/server` | `/srv/orzmc/instances/papermc-main/server:/server` | 核心数据挂载 |
| Java 版本 | `21` | `21` | 根据目标 Paper 版本选择 |
| 最小内存 | `2G` | `4G` | 测试服保守，正式服更稳妥 |
| 最大内存 | `2G` | `4G` | 建议与最小值一致，降低抖动 |
| 启动命令 | `java ${PAPERMC_JVM_OPTS} -Xms${PAPERMC_TEST_MEMORY_MIN} -Xmx${PAPERMC_TEST_MEMORY_MAX} -jar ${PAPERMC_SERVER_JAR_NAME} --nogui` | `java ${PAPERMC_JVM_OPTS} -Xms${PAPERMC_PROD_MEMORY_MIN} -Xmx${PAPERMC_PROD_MEMORY_MAX} -jar ${PAPERMC_SERVER_JAR_NAME} --nogui` | 实际录入时可直接替换成固定字符串 |
| Minecraft 版本 | `1.21.1` | `1.21.1` | 业务版本 |
| Jar 文件名 | `paper.jar` | `paper.jar` | 镜像内实际服务端文件名 |
| 接受 EULA | `true` | `true` | 必须开启 |
| 正版验证 | `true` | `true` | 按服务器策略调整 |
| MOTD | `OrzMC Test Server` | `OrzMC Survival Server` | 列表描述 |
| 最大玩家数 | `10` | `20` | 按定位调整 |

## 建议固定字段

| 字段 | 推荐值 | 说明 |
|---|---|---|
| 运行方式 | `docker` | 与当前容器化架构保持一致 |
| 镜像拉取策略 | `IfNotPresent` | 避免无意中升级镜像 |
| 工作目录 | `/server` | 与挂载定义保持一致 |
| 重启策略 | `unless-stopped` | 平台层统一约定 |
| 协议 | `tcp` | Minecraft 默认 |
| 监听地址 | `0.0.0.0` | 允许容器监听全部地址 |
| 网络模式 | `bridge` | 与平台层编排一致 |
| 挂载模式 | `rw` | 运行目录必须可写 |
| 运行 UID/GID | `1000/1000` | 与宿主机持久化目录权限保持一致 |
| 额外 JVM 参数 | `-XX:+UseG1GC -XX:+ParallelRefProcEnabled` | 作为起步参数 |
| 停止命令 | `stop` | 适配 Minecraft 控制台 |
| 控制台编码 | `UTF-8` | 避免日志乱码 |
| Ready 关键字 | `Done` | 用于判断启动完成 |
| 更新策略 | `manual` | 服务端和插件升级建议手动确认 |

## 已验证的最小可运行组合

以下组合已经在本地 `macOS + Docker Desktop + MCSManager Docker 实例` 模式下验证通过：

- 镜像：`eclipse-temurin:21-jre`
- 工作目录：`/server`
- 宿主机服务目录：`<server-dir>`
- 启动命令：`java -XX:+UseG1GC -XX:+ParallelRefProcEnabled -Xms2G -Xmx2G -jar paper.jar --nogui`
- 端口映射：`25566:25566/tcp`（测试服） / `25565:25565/tcp`（正式服）
- `paper.jar`：预先下载到宿主机服务目录
- `eula.txt`：预先写入 `eula=true`

建议的最小宿主机预置文件：

- `paper.jar`
- `eula.txt`
- `server.properties`

## Docker 模式注意事项

- 如果 `cwd` 已经指向宿主机服务目录，且容器工作目录设为 `/server`，MCSManager 会自动把工作目录挂到容器内。
- 不要再把同一个宿主机目录通过 `extraVolumes` 重复挂载到 `/server`，否则会报错：`Duplicate mount point: /server`。
- 如果要额外挂载备份目录或导入目录，请确保容器目标路径与工作目录挂载目标不同，例如 `/backups`、`/import`。

## 选填字段

| 字段 | 建议 | 说明 |
|---|---|---|
| RCON 开关 | 默认 `false` | 没有远程控制需求时先关闭 |
| RCON 端口 | `25576/25575` | 测试服和正式服分开 |
| 备份目录 | `.../backups` | 建议尽早规划 |
| 导入目录 | `.../import` | 用于导入地图或插件 |
| CPU 限额 | `2/4` | 按宿主机资源分配 |
| 难度 | `normal` | 按玩法调整 |
| 默认模式 | `survival` | 按玩法调整 |
| 视距 | `8/10` | 正式服可略高 |
| 模拟距离 | `6/8` | 配合视距控制性能 |
| PvP | `true` | 按服务器规则调整 |
| 白名单 | `false` | 活动或内测期可切换为 `true` |
| 出生点保护 | `16` | 常用起始值 |
| 自动备份 | `true` | 正式服强烈建议开启 |
| 备份计划 | `0 6 * * *` / `0 5 * * *` | 测试服和正式服错峰备份 |
| 维护窗口 | `04:00-05:00` / `03:00-05:00` | 用于约束计划维护时段 |
| 地图模板 | `default-test` / `default-survival` | 仅在有初始化模板时使用 |
| QQ Bot 联动 | `false` | 后续再扩展 |

## 建议的录入顺序

1. 先录入实例名、镜像、端口、目录和内存
2. 再录入 `MOTD`、玩家数、`online-mode`
3. 最后补备份、RCON、维护窗口等运维项

## 第一阶段建议

- 先只创建 `PaperMC Test`
- 验证 `启动 / 停止 / 重启 / 数据持久化 / 插件目录 / 日志目录`
- 跑通后再按同样模板创建 `PaperMC Prod`
