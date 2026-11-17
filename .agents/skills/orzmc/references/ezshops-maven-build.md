# EzShops 本地构建与部署（2026-08-09）

本地维护仓库 `~/OrzMC/tools/EzShops`（monorepo submodule，上游修复：common 重复键移除、messages_zh 完整本地化）。构建 Maven。

## 构建命令

```bash
~/apache-maven-3.9.16/bin/mvn clean package -Dmaven.test.skip=true
# 产物：target/EzShops-2.5.9.jar（shaded 4.2MB）← 部署用
#      target/original-EzShops-2.5.9.jar（原始瘦包）
```

- 测试编译与 MockBukkit/Paper datacomponent API 冲突 → 必须 `-Dmaven.test.skip=true`（`-DskipTests` 仍编译测试代码，会失败）
- 依赖可直连 Maven Central，无需镜像

## jaker 1.0.7 macOS 大小写坑（关键）

**错误**：`Invalid packaging for parent POM com.github.EzFramework.Jaker:jaker:1.0.7, must be "pom" but is "jar"`

**根因**：jaker 的 pom 引用 parent `Jaker:1.0.7`（大写）而自身 artifactId 小写 `jaker`。macOS APFS 文件系统大小写不敏感 → `Jaker/` 与 `jaker/` 目录/文件名冲突 → parent 自引用死循环；且传递子模块（jaker-bench/jaker-data-de/en-GB 等）的 parent 都引用 `jaker`，其 packaging 默认 jar 必须为 pom 才能当 parent。

**修复**（直接改本地缓存 pom）：`~/.m2/repository/com/github/EzFramework/Jaker/jaker/1.0.7/jaker-1.0.7.pom`

1. 删除 `<parent>` 段（Jaker 1.0.7 自引用）
2. `<modelVersion>` 后加 `<packaging>pom</packaging>`
3. 删除同目录 `*.sha1` 和 `_remote.repositories`（防止 Maven 校验失败重下覆盖修改）
4. 重新构建（在线/离线均可）

## 部署（全新安装）

1. 停服
2. `rm -rf plugins/EzShops plugins/EzShops-*.jar`——**必须删旧目录**，否则 EzShops 输出 "Skipping bundled default category files for existing mode directories"，不生成新配置、语言不刷新
3. `cp target/EzShops-2.5.9.jar plugins/`
4. 启动 → 生成全新配置 → 改 `plugins/EzShops/config.yml` 的 `language: zh`
5. 重启 → 验证

## 验证清单

- 日志 `duplicate keys found : common` WARN = 0（重复键修复生效）
- `Shop configuration loaded: 207 item(s) across 13 categories`
- `language: zh` 生效（商店界面中文）
- 本地无 MySQL 时 `Failed to initialise Jaloquent... falling back to YAML` 属正常降级（交易走 YAML 存储）
- TeamsAPI not found = 可选依赖缺失，正常（团队商店禁用）
