# 上下文脏数据根因链（joker / TestMember 案例实录）

OrzMC 权限系统二期（LP track 四级：default→member→builder→admin）实测复现与修复。

## 症状

1. `$p d joker`（降到 default）后游戏内 `/rank` 仍显示「建造者」
2. `$p d` 报 `AMBIGUOUS_CALL`（LP 无法判定降级位置），旧代码一律提示「已在最低等级」
3. TestMember 曾有 track 节点重叠（builder + member 并存）

## 表象排查（走弯路）

- 先以为是无上下文叠加组（`parent add` 手动加的 builder）→ 清理后症状部分缓解
- 实际上 joker 还有 **world=world 上下文**的 builder + member 组（带
  essentials:afk/jailed/muted/vanished + gamemode=creative 完整上下文快照）
- LP 命令删带完整上下文的节点：`parent remove <组>` 和 `--context world=world` 都删不掉
  （LP 报「joker 沒有從環境 world=world 中繼承 builder」——需要全部 context 键精确匹配）

## 根因（代码层）

一期实现 `promote/demote` 用 `contextsFor(user)`：

```java
private ImmutableContextSet contextsFor(User user) {
    Optional<ImmutableContextSet> ctx = api().getContextManager().getContext(user);
    return ctx.orElseGet(ImmutableContextSet::empty);
}
```

玩家在线时 `getContext(user)` 返回当前完整上下文（world/gamemode/essentials 等）→
LP 把 track 节点带完整上下文快照落库。玩家离线操作时上下文为空 → global 节点。
两种节点混存 → `currentTrackGroup` 判定错乱 + `promote/demote` 报 AMBIGUOUS_CALL。

## 修复（统一 global）

```java
private static ImmutableContextSet globalContext() {
    return ImmutableContextSet.empty(); // 惰性：不能静态 final 初始化（测试类加载炸）
}

private static QueryOptions queryOptionsGlobal() {
    return QueryOptions.builder(QueryMode.CONTEXTUAL).context(globalContext()).build();
}
```

- `track.promote/demote(user, globalContext())` — 操作统一 global
- `user.getInheritedGroups(queryOptionsGlobal())` — 查询统一 global（isInGroup / currentTrackGroup）
- `$p u` 新玩家（ADDED_TO_FIRST_GROUP 且 groupTo=链首）：再 promote 一次直达 member
- AMBIGUOUS_CALL → WARNING 日志 + `lp user X parent info` 指引
- $p 失败提示合并：「已达边界或权限数据异常（详见服务器日志）」

## 验证结果

- `$p d joker`：AMBIGUOUS_CALL → REMOVED_FROM_FIRST_GROUP（正常链底语义）
- `$p u joker`（不在 track）：ADDED_TO_FIRST_GROUP → 连续 promote SUCCESS →「已将 joker 升级为成员」
- 存量 world 上下文脏节点不再影响 global 判定，可不强清

## 文档同步教训（同一轮）

方案文档 + 验收文档与实现逐节核对流程：
1. 文件清单（8.1）逐文件对照实际签名/键数（ReviewHandler boolean、TemplateKeys 11 键）
2. 命令表对照实际注册（/rank demote 已删、/apply admin 新增、$h/$cmd ? 帮助）
3. 决策记录（8.3）补充实战教训（叠加组规范、global 上下文根因）
4. 验收文档「问题表」保留历史 + 追加新问题（不覆盖，防止丢证据）

## 相关测试 mock 关键点

- `ImmutableContextSet.empty()` 静态工厂依赖 ContextManager.getContextSetFactory()
- `QueryOptions.builder()` 依赖 ContextManager.queryOptionsBuilder(mode)
- 测试 mock 链：factory.immutableEmpty() → emptyCtx（isEmpty=true）；
  cm.queryOptionsBuilder(any()) → qob；qob.context(any()) → qob；qob.build() → qo；
  qo.context() → emptyCtx
