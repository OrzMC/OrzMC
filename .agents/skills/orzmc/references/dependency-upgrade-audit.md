# 插件依赖升级核查（发版前审计，2026-08-07 实测方法）

发版前核查全部依赖是否最新、评估升级风险的标准流程。

## 批量查最新版本（终端外网受限，仅 Maven Central/Plugin Portal 可达）

Maven Central `maven-metadata.xml` 的 `<latest>`/`<release>` 标签**经常缺失**——可靠做法是拉 `<version>` 列表过滤预发布：

```bash
# 单个：取版本列表（过滤 alpha/beta/rc/snapshot/preview/dev）
curl -s "https://repo1.maven.org/maven2/<group-path>/<artifact>/maven-metadata.xml" \
  | grep -oE "<version>[^<]+</version>" | sed 's/<[^>]*>//g' | grep -vE "alpha|beta|rc|snapshot|preview|dev" | tail -3
```

| 依赖来源 | 正确路径 | 备注 |
|:--|:--|:--|
| 常规 Maven 依赖 | `repo1.maven.org/maven2/<g>/<a>/maven-metadata.xml` | group 路径**含子组全路径**（`com/squareup/okhttp3/mockwebserver` 不是 `com/squareup/okhttp3`） |
| **Paper API** | `repo.papermc.io/repository/maven-public/io/papermc/paper/paper-api/maven-metadata.xml` | **不在** Maven Central（Central 返回 404） |
| Gradle 插件 | `plugins.gradle.org/m2/<plugin-id>/<plugin-id>.gradle.plugin/maven-metadata.xml` | 如 `com.gradleup.shadow/com.gradleup.shadow.gradle.plugin`；版本列表尾部常有 `-Beta/-RC` 需过滤取正式版 |

## LP API 版本兼容结论（5.4 → 5.5 实测）

- LP API 官方声明**语义化版本**：主版本不变（5.x 内）= 向后兼容承诺，minor 升级无 breaking change
- 「5.4 编译 ↔ 5.5.x 运行时」是官方设计支持的组合：**服务端 LP 插件可自由升级**（软依赖 `required:false` 声明了兼容）
- 编译依赖 `net.luckperms:api` **只在需要新 API 特性时升**（track 相关核心接口 5.0 起未变）；必须升级的信号 = API 主版本 6.x
- **已执行**（2026-08-07，commit a4fb5b0，随 1.0.16 发版）：`api:5.4 → 5.5`（compileOnly + testImplementation 两处）+ junit-jupiter 6.1.2→6.1.3 + mockbukkit-v26.1.2 4.114.0→4.115.0——全绿后部署本地服 `$p d/u` 实测 promote/demote SUCCESS
- 实证法：临时改 gradle 版本 → `compileJava compileTestJava test` 全绿即兼容；部署后 `$p d/u` 实测 LP 真实组

## 升级验证协议（按序执行）

1. 改版本 → `./gradlew spotlessApply test`（快失败）
2. `./gradlew check shadowJar`（含 MockBukkit 集成测试 + JaCoCo）
3. 部署本地服 → Done 无缺失告警 → 关键路径冒烟（$p/$v/$l）

## MockBukkit = paper-api 编译版本升级的瓶颈（本会话实测）

- MockBukkit artifact 命名跟随 Paper 版本：`org.mockbukkit.mockbukkit:mockbukkit-v26.1.2:4.115.0`（**没有** `mockbukkit-v26.2`）
- **MockBukkit 未跟进新 Paper 版本时，paper-api 编译版本升不上去**：升级 26.2 后集成测试 `AssemblyIntegrationTest` 挂 `java.util.ServiceConfigurationError: io.papermc.paper.registry.RegistryAccess: Provider ...RegistryAccessMock could not be instantiated`（MockBukkit 按旧版 API 实现的类初始化失败）
- 结论：**升 paper-api 前先查 MockBukkit 有没有对应 artifact**；没有就保持编译版本，等 MockBukkit 跟进（代码一般无需改动，只改 `gradle.properties` 一行）。同线内 MockBukkit patch 升级（4.114.0→4.115.0）可顺手做。
