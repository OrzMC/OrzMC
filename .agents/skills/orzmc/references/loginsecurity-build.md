# LoginSecurity 构建与 AuthModeChangedEvent 排查（2026-08-10）

仓库：OrzMC monorepo `tools/LoginSecurity` 子模块（master 分支；`OrzMC/tools/` 下）。

## 构建（Gradle，不是 Maven！）

- **`./gradlew shadowJar`** → 产物 `build/libs/LoginSecurity-3.3.2-SNAPSHOT.jar`（~300KB）
- ⚠️ **pom.xml 是陈旧残留**（spigot-api 1.13.2）——`mvn package` 必然失败（`程序包 io.papermc.paper.event.player 不存在`、`LoggingFilter 构造器无法应用` 等）。构建工具一律看 `gradlew` + `build.gradle.kts`
- 提交 `c6ba6a1 migrate to papermc 26.2 and java 25`（2026-08-09）迁移了构建到 Paper 26.2 + Java 25；**同步 monorepo 到最新后再构建**（旧代码编译不过）
- Gradle 仓库配置：阿里云镜像 + spigotmc snapshots + jitpack（build.gradle.kts 内已配，无需手工镜像）

## AuthModeChangedEvent 报错（基岩玩家登录时）

现象（本地/MCSM 均见，仅基岩玩家触发）：
```
LoginSecurity ERROR: Could not pass event AuthModeChangedEvent
java.lang.IllegalArgumentException: name cannot be null
  at PlayerSession.getPlayer(PlayerSession.java:138)  // Bukkit.getPlayer(profile.getLastName())
  at PlayerListener.onAuthChange(PlayerListener.java:209)
  at PlayerSession.lambda$performAction$4(PlayerSession.java:192)  // 异步任务
```

根因（源码实证）：
- `performAction`（sync=true）用 `runTaskAsynchronously` 触发 `AuthModeChangedEvent`
- `onAuthChange` 调 `session.getPlayer()` → `Bukkit.getPlayer(profile.getLastName())`
- **时序竞争**：异步事件触发时 `onPlayerJoin` 里的 `profile.setLastName(player.getName())` 还没执行 → lastName 为 null → `Bukkit.getPlayer(null)` 抛 IllegalArgumentException
- Geyser 转发的登录流程时序更易错位，所以只有基岩玩家触发

**无害**：`onAuthChange` 只做版本更新检查（checkUpdates），异常后玩家正常进服。仅日志刷屏。

修复（如需）：`PlayerSession.getPlayer()` 加 null 防御：
```java
public Player getPlayer() {
    final String lastName = profile.getLastName();
    if (lastName == null) return null;   // onAuthChange 已有 player==null 短路
    return Bukkit.getPlayer(lastName);
}
```
补丁在 feature 分支开发，验证后合入（遵循用户开发流程）。
