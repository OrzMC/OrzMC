# Java 测试编译陷阱（2026-08-11 从 java-test-pitfalls 技能合并）

> 场景：写/修 OrzMC 系插件 Java 单元测试时的编译错误、javac 警告、GitHub Actions warnings 排查。

## 触发条件

- `when(mock.method()).thenReturn(x)` 编译报「找不到合适的方法」且错误信息含 `CAP#1` / `? extends` 捕获
- 想用 `@SuppressWarnings` 消警告但 CI 还在报
- CI 日志出现 `##[warning]`（unchecked / rawtypes 类），Checks 区和 Files changed 行内都有 ⚠️ 标记

## Pitfall 1：Mockito thenReturn 与通配符泛型捕获

**症状**：mock 的 API 返回 `Collection<? extends Player>`（Bukkit `getOnlinePlayers()` 等），写：

```java
java.util.Collection<? extends Player> online = List.of(p1);
when(mock.getOnlinePlayers()).thenReturn(online);  // 编译错
```

javac 报：`thenReturn(Collection<CAP#1>) 找不到合适的方法`——`when()` 捕获出 CAP#1，`thenReturn` 期望的 `OngoingStubbing<Collection<? extends Player>>` 是另一个捕获 CAP#2，两个捕获互不匹配。

**修复**：改用 `doReturn`（接受 raw Object，绕开泛型捕获推断）：

```java
java.util.Collection<? extends Player> online = List.of(p1);
doReturn(online).when(mock).getOnlinePlayers();   // ✅
```

- `doReturn` 不产生 unchecked 警告（它签名是 `OngoingStubbing<T> doReturn(Object)`）
- 需要 `import static org.mockito.Mockito.doReturn;`
- 注意：`Collection<Player>`（无通配符）也不行——`thenReturn` 要求精确匹配捕获类型

## Pitfall 2：@SuppressWarnings 注解位置

**症状**：`@SuppressWarnings({"unchecked", "rawtypes"})` 标在局部变量声明上，但 CI 仍报 unchecked 警告。

**原因**：局部变量声明上的注解**只抑制该声明本身**，不覆盖后续语句。典型场景：

```java
@SuppressWarnings({"unchecked", "rawtypes"})   // ❌ 无效：只盖住这行声明
java.util.Collection online = List.of(p1);
when(mock.getOnlinePlayers()).thenReturn(online);  // ⚠️ 警告发生在这行
```

**正确修法（优先级从高到低）**：
1. 消除 raw type 本身（改泛型类型）——最干净，见 Pitfall 1 的 `? extends` + doReturn 组合
2. `@SuppressWarnings` 移到**方法级**或直接标在出警告的**语句上**
3. 确认警告真正产生的位置：`./gradlew compileTestJava 2>&1 | grep warning` 看行号，别只看注解在哪

## Pitfall 3：GitHub Actions 编译警告排查与清零

**事实**：javac 的 `-Xlint` 警告（unchecked/rawtypes/deprecation）在 GitHub Actions 日志里以 `##[warning]` 行出现，会同时显示在：
- Checks 页面的 warning 数
- PR **Files changed 里对应代码行的 ⚠️ 行内标记**（用户常把这两处叫「PR 的 Alerts」）

**排查流程**：
1. `gh run view <RUN_ID> --log | grep "##\[warning\]"` 定位警告文件与行号
2. 本地复现：`./gradlew compileJava compileTestJava` 看警告（本地 JDK 与 CI 的 `-Xlint` 默认开关一致时行号对齐）
3. 修复后重跑 CI，**验证清零**：`gh run view <NEW_RUN_ID> --log | grep -c "##\[warning\]"` 应为 0

**注意**：`@SuppressWarnings("removal")` / `("deprecation")` 的既有注解不是问题；只清本次新增的 unchecked/rawtypes。

## 跑单个测试类（多模块工程必踩）

```bash
./gradlew test --tests "*WorldMaintenanceServiceTest*"        # ❌ 多模块下会失败
./gradlew :test --tests "*WorldMaintenanceServiceTest*"       # ✅ 只跑根项目
```

**机制**：`--tests` 过滤器会应用到**每一个**子项目，子项目（如 `:orzmc-api`）里没有该测试类 → 报
`Execution failed for task ':orzmc-api:test' > No tests found for given includes: [...]` → **BUILD FAILED**。
这句报错极易误读为「测试类不存在/被删」，实际只是过滤器越界。跑单类定位红测时一律带模块限定任务名。

## 跨平台断言：别把 `/` 写死进断言

**症状**：某个测试在 Linux/macOS CI 上全绿，在 Windows 上必挂，报 `expected: <false> but was: <true>`。

**根因形态**：断言里拿路径分隔符做后缀判断，如 `msg.trim().endsWith("/world")` —— Windows 的上报路径是 `...\world`，`endsWith("/world")` 恒 false，判据被静默翻转。

**修复（判据看语义不看分隔符）**：取上报路径的**最后一段**再比名字，两种分隔符都兼容：

```java
String reported = msg.trim();
String tail = reported.substring(reported.lastIndexOf('/') + 1);
tail = tail.substring(tail.lastIndexOf('\\') + 1);
inputIsContainer.set(!"world".equals(tail));
```

**修这类测试的验证纪律（缺一条都不算通过）**：
1. **原失败环境**实跑该测试类（Windows）→ 绿；
2. **POSIX 端**实跑同一测试类（macOS/Linux）→ 仍绿（证明没把原意图改掉）；
3. 查**同 commit 的 CI**：全绿 ⇒ 说明这是「测试可移植性问题」而不是产品回归，PR 描述里写清这一点，别让人误以为是功能 bug。

## 验证步骤

```bash
./gradlew spotlessApply test          # 全量测试
./gradlew check                       # 完整门禁（含集成测试）
# 推送后：
gh run view <id> --log | grep -c "##\[warning\]"   # 期望 0
```

## 关联陷阱（同领域）

- **删配置/删代码时 grep 全引用面**：record 字段、解析器、测试构造器、健康检查（类型校验 + 建议校验常分两处）都要同步删，漏一处编译即挂
- **patch YAML 删段后必须回读结构**：误把相邻段键名改掉的 patch 事故，`grep -n "^\s\s\w*:"` 验证段结构

---

# 以下由独立技能 bukkit-plugin-testing 合并入（2026-09-12）

> 来源：2026-08-19 OrzMC 插件补测实战（maintenance/paging/ws/review/teleport 五模块 34%→59%~97%，总覆盖 82.2%→85.4%）。

## 分层测试原则（本类任务）

1. **分层测试**：业务状态机/纯逻辑 → 单测（mock 端口）；平台行为（Bukkit 事件、LP 授权、网络链路）→ MockBukkit 集成测试或真实服 E2E。单测测不了的（依赖 Bukkit 注册表）明确留给上层，别硬 mock。
2. **覆盖率缺口定位**：`build/reports/jacoco/test/jacocoTestReport.xml` 按 package→class 解析 INSTRUCTION 计数，找低覆盖类的具体方法再补测（避免边际浪费）。
3. **补测后必须重跑 jacoco 验证提升**，并保持全量 `./gradlew test` 绿。

## Mockito 运行时陷阱（编译能过但运行报错）

### UnfinishedStubbingException
- `doAnswer(inv -> null).when(mock).runAsync(any())`（void 方法返回 null 的 lambda）→ 报 UnfinishedStubbing → **void 方法用 `doNothing()`**
- `when(mockA.method()).thenReturn(mockB.other())` —— stubbing 进行中调用另一 mock 方法 → 同错 → **先存变量**：`X v = mockB.other(); when(mockA.method()).thenReturn(v);`

### Stub 匹配顺序（后声明优先）
- `when(m.get(a,b,c)).thenReturn(A)`（anyInt 兜底）+ 后声明的精确 `when(m.get(10,64,20)).thenReturn(B)` → 精确参数命中 B ✓；**顺序反了精确 stub 被兜底覆盖**。兜底先声明、精确后声明。

### argThat 可能收到 null
- `when(m.get(argThat(l -> l.getX()==1)))` 的 lambda 会收到 null 参数 → NPE → 必须 `argThat(l -> l != null && ...)`。

### 模拟「异步进行中」状态（互斥/并发测试）
- 立即执行 mock（`doAnswer(inv -> { run(inv.getArgument(0)); return null; })`）会让异步任务同步跑完 → 无法断言「进行中」。**模拟进行中 = runAsync 配 `doNothing()`（不执行）**；断言用计数器（`AtomicInteger` 在 stub 里递增）而非 verify 精确次数（业务内部可能多次调用同一方法）。

## Bukkit API mock 限制（注册表依赖）

| API | 纯 JUnit 行为 | 对策 |
|:--|:--|:--|
| `Material.isSolid()`（及 Sound 枚举静态初始化） | 依赖 Bukkit 注册表，未初始化返回 false/抛错 | 成功路径断言留 E2E/集成测试；单测只测不依赖注册表的分支 |
| `Material.isAir()` / `DANGEROUS.contains(...)`（EnumSet） | 不依赖注册表，可测 | 用 DANGEROUS 方块（LAVA/FIRE）测拦截分支 |
| `Block.isAir()` | **不存在**（isAir 是 Material 的方法） | 编译错误时检查是不是 mock 错了对象 |
| mock `Vector` | `clone()` 返回 null（mock 不执行真实方法）→ NPE | **用真实 `new Vector(x,y,z)`**（clone/normalize/dot 全真实工作） |
| `Location.getBlock()` | 实现可能走 `World.getBlockAt(Location)` 重载（非 int 重载） | 两种重载都 stub；或 `thenAnswer` 按 `l.getBlockX/Y/Z()` 坐标分发 |

## Jacoco 覆盖率提升工作流

```bash
# 1. 定位缺口
python3 -c "
import xml.etree.ElementTree as ET
t = ET.parse('build/reports/jacoco/test/jacocoTestReport.xml')
for p in t.getroot().findall('package'):
    if '目标模块' in p.attrib['name']:
        for c in p.findall('class'):
            m=cv=0
            for ctr in c.findall('counter'):
                if ctr.attrib['type']=='INSTRUCTION':
                    m,cv=int(ctr.attrib['missed']),int(ctr.attrib['covered'])
            if m+cv: print(f'{cv/(m+cv)*100:6.1f}%  {c.attrib[\"name\"].split(\"/\")[-1]}')"
# 2. 补测 → 3. ./gradlew test jacocoTestReport 验证 → 4. 全量 test 回归
```

## Bukkit 单测额外 Pitfalls（本轮实战）

- **测试断言别用 `String.includes(正则对象)`**：waitMessage 类工具若用 `includes()` 接收正则会被 toString 成 `/.../` 字符串永不匹配 —— 断言工具要显式支持正则（`typeof === 'string' ? includes : test`）。
- **单页分页也会调度 runLater**：断言「N 次延迟任务」前先读源码确认行为，别凭直觉写。
- **后台任务（gradle 构建/长扫描）用 background=true 并行**，用 wait/poll 交错推进多线工作。
- **测试源码里 `\u` 序列会触发 javac Unicode 转义（注释里也一样炸）**：javac 词法阶段处理 `\uXXXX`，注释写 `\uZZZZ` 或 `\\uXXXX`（连续反斜杠第二个 `\`+u 仍构成转义）都报「非法的 Unicode 逃逸」。构造含反斜杠的测试夹具字符串用拼接：`String b = "\\"; ("level-name=" + b + "uZZZZ\n")`；注释就写「非法 Unicode 转义」避开字样。实例：OrzMC #217 测试写非法 server.properties 触发 `Properties.load` 的 IllegalArgumentException。
- 补测后 spotlessApply 可能改格式，提交前跑一次。
