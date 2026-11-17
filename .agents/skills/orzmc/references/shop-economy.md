# 商店经济防刷（EzShops 实例）

> 合并自：minecraft-shop-economy-hardening（2026-08-30 并入 orzmc 统一技能后删除独立技能）
> 触发：玩家用红石机械/刷怪塔/自动农田无限产出物品卖商店刷钱；商店插件价格审计；反作弊插件选型。
> 方法论通用（QSR/ShopGUI+/EzShops 等），EzShops 为本地实测实例。

## 核心结论（2026-08-29 定稿：生存服 smp 模式全堵）

**⚠️⚠️ `sell:`/`buy:` 字段 = 单价（每 1 个物品），不是「每 amount 个」**（2026-08-29 bot 实测实证：ender_pearl sell=0.4 → 卖 8 个得 $3.20=0.4×8）。`amount` 只是 GUI 批量单位。⚠️ 曾全盘误读（以为 0.1/16个=0.006/个，实际 0.1/个，高 16 倍）→ 压价目标全部偏高 8-16 倍，**「smp 天然防刷」结论即来自此误解，已被 bot 实测推翻**（熟牛肉真实单价 1.75/个→牧场 1000/时=1750 元/时；原木 1.0/个→树场 500/时；鳕鱼 0.96/个→钓鱼机 1000/时）。**定价审计必须以 bot 实测卖出价校准，不能纯读配置心算**（验收 bot 方法见下）。

**动态定价/全局兜底方案对「无限可再生物品」无效**：价格有下限（min-multiplier）+ 商店无限收购 → 只降速不封顶（骨粉压到 0.00625/个 × 无限量 = 24h 挂机仍有被动收入）。**纯禁卖只适用于监狱服**（只靠挖矿变现）。

**⚠️ 2026-08-29 最终决策（纯禁卖方案，PR #1 feat/economy-anti-farm，零 Java 代码）**：商店只收购「挖矿原料 + 稀有探索掉落」，一切可再生/可自动化/合成套利商品一律禁卖（`sell: -1.0`，buy 全保留，玩家正常购买）。落地：保留可卖 18 条（煤/原矿×3/钻石/青金石/红石/石英/紫水晶/黑曜石 + 远古残骸/下界合金碎片/海洋之心/重核/重锤）；禁卖 194 条（mob_drops 全 9、铁/金锭、压价 0.1 全升级禁卖 145 条、审计新增 32 条、特惠默认 3 条）；只买不卖 18 条（附魔书 9 + 刷怪笼 9）。撤销：prison 日限额 512（回 main）、smp 全套同步（线上只加载 prison）、Java 动态定价兜底。**验证：本地打包成功 + 测试服部署 bot 实测**。

**纯禁卖判据（通用）**：商店只收购「挖矿原料 + 不可再生探索掉落」；一切可再生/可自动化/合成套利 → `sell: -1.0`（buy 全保留）。保留清单：coal / raw_copper / raw_iron / raw_gold / diamond / lapis / redstone / quartz / obsidian + ancient_debris / netherite_scrap / heart_of_the_sea / heavy_core / mace。判据不是「是否可再生」而是「是否符合服玩法定位」。⚠️ **amethyst 不在保留清单**（budding amethyst 无限再生=可持续农场）——「挖矿产物」直觉会误判它不可再生。

## 漏洞分类学（逐类排查）

| # | 漏洞类型 | 案例 | 修复 |
|:--|:--|:--|:--|
| 1 | **合成套利**（买原料→合成→卖产物）| 骨头 buy 1.5 → 1 骨头合成 3 骨粉 → 卖 1.5×3=4.5（**200%**）；石头→石砖 140% | 产物 sell ≤ Σ(原料 buy×数量)；或禁卖 |
| 2 | **特惠轮换后门** | daily_specials rotation 高价回收常规禁卖品（铁锭 4.5/个、烈焰棒 48/个、腐肉 9.5/个）| 特惠条目 sell 同步 -1.0（buy 保留促销）|
| 3 | **农场产物高价卖** | food 分类熟牛肉 1.09/个、金胡萝卜 1.31/个（自动屠宰/农田）| 全禁卖（2026-08-29 起不再压价）|
| 4 | **合成件绕禁卖** | 禁铁锭后漏斗 23.75/个（=8 铁锭）、CRAFTER 45/个 | 红石合成件全禁卖 |
| 5 | 合成块 9:1 | 铁块/金块/煤块 | 检查 buy 原料×9 vs 块 sell |
| 6 | 村民交易（已定案）| 绿宝石 35/个（村民农场无限；mining+valuables **两处条目都禁**）| **禁卖**（同物品多分类条目要全部处理）|
| 7 | **加工品合成套利（原料压价没用）** | tuff 加工品：6 tuff（值 0.6）→ chiseled_tuff 卖 24 = **40x 杠杆**；polished_tuff/tuff_bricks 等全系 | 加工品全禁卖，只留原料级挖矿产物 |
| 8 | **可再生建材** | 木板×8/沙子/沙砾/黏土/砖/陶瓦/土/玻璃/岩浆块 | 禁卖（树场/刷沙机/泥浆机全渠道）|
| 9 | 试炼农场 | breeze_rod / wind_charge / trial_key / ominous_trial_key | 禁卖（试炼刷怪笼可自动化，高价不免疫）|
| 10 | 繁殖 | armadillo_scute / wolf_armor | 禁卖（犰狳可繁殖）|
| 11 | **特惠默认条目后门** | daily_specials 默认（CARROT / HONEY_BOTTLE / BONE_MEAL）| farming-frenzy items 留空 → 继承 rotation-defaults → **改 defaults 即全局生效**；骨粉=骷髅农场产物 |

## 审计方法（脚本模式）

1. **价格表**：读 `shop/<mode>/categories/*.yml`，**按 `material` 字段收集**（特惠条目 key 是展示名如 `premium_pick`，按 key 收集会漏！）→ **sell/buy 本身就是单价**（不要再除以 amount！amount 仅 GUI 单位）
2. **配方字典**：MC 常见合成（bone→bone_meal×3、stone→stone_bricks、wheat→bread/cookie、9:1 块、原木→木板×4…）→ 产物 sell×乘数 vs Σ(原料 buy) 交叉检查
3. **sell/buy 比率**：≥0.9 = 套利温床；压价区应趋近 0
4. **特惠/轮换检查**：`daily_specials.yml` 的 `rotation-defaults.items` + `rotations/*.yml` 各 option 的 `items` 覆盖——**逐条查**（最容易漏的高价回收口）
5. 改配置用**文本级正则替换 sell 行**（PyYAML 转储会破坏 `{translate:...}` 结构）；⚠️ **item 缩进不统一**：普通 categories items=6 空格、rotation-defaults 下（daily_specials.yml）=8 空格 → 固定前缀匹配会漏文件（实测踩坑）。用**块级定位**：正则 `^\s*([a-z0-9_]+):\s*$` 匹配 item id 行 → 向后扫到「缩进 ≤ item 缩进的非空行」= 块结束 → 块内找 sell 行替换；改后 `yaml.safe_load` 全量验证 + 重启看 `Shop configuration loaded: N item(s)` 无错误 + **生成配置 vs 仓库模板逐条 yaml 比对**（等价验证，比只看日志稳）

> 审计脚本：`scripts/shop_arbitrage_check.py <shop/prison|shop/smp 目录> [--full]`——价格表（按 material 收集）+ 合成配方套利检测 + 特惠轮换高价条目扫描。

## Bot 实测验收（定价校准必做，2026-08-29 沉淀）

配置改完必须 bot 实测卖出价校准（纯读配置心算不可靠——sell=单价语义曾致评估全错）。模式：`~/minecraft-bot/econ-verify.js`（登录 → 等 RCON give → 逐物品 equip 主手 → `/sellhand` → `bot.on('message')` 捕获响应：禁卖提示 `That item cannot be sold` / 卖出金额 `Sold Nx X for $Y`）。
- **RCON give 必须玩家在线**（离线 give 对新建账号不生效，报 No player was found）→ 脚本登录后轮询背包等物品（过滤 written_book 新手指南），期间补 give
- **防重登冷却**：GriefPrevention3D `Spam.LoginCooldownSeconds` 默认 60s，连续登录被踢 `You must wait X seconds before logging-in again` → 重试前 sleep 60+
- 新账号自动 `/register` 幂等（测试服密码 orztest2026）；已注册账号密码不符会卡未登录（背包不可见）——直接换新账号
- **批量 >99 测试用 `/sellinventory`**（不是 /sellall——该命令不存在；sellinventory=卖背包全部可卖物，单次触发 >99 序列化路径）；脚本：`~/minecraft-bot/econ-sellall.js`（等 give → /sellinventory → 退出）；先 `minecraft:clear <玩家>` 清残留物品再 give，避免干扰
- 验收矩阵：禁卖品（预期 That item cannot be sold）+ 压价品（实测单价必须 = 配置 sell）+ 正常品（钻石等保留价）+ 批量 >99（无序列化警告）+ transactions.yml 落盘

## EzShops 机制坑（源码实证）

0. **结算取价机制（反刷审计必读）**：`ShopTransactionService` 结算用 `priceKey = item.priceId() != null ? priceId : material().name()` 全局 priceMap 取价——**特惠/轮换槽位的 sell 配置不参与结算（只展示）**，实付 = 该 material 在其它分类（food/mob_drops 等）的条目价。推论：① 改特惠 sell 无效（展示层），真正生效的改动必须在 material 键唯一的常规条目；② 特惠条目 key 是 itemId（premium_pick）而非 material → material 无全局条目（如 BONE_MEAL）→ estimateBulkTotal 返回 -1 → 买/卖报 invalid price（存量 bug，**删条目规避**）；③ **重复 material 键互相覆盖**（如 emerald 在 mining+valuables）→ 后加载覆盖 → 显示价 ≠ 实付价（显示 360 实扣 400）——同物品多分类条目必须全部处理
1. **`game-mode` 决定一切**：`game-mode: prison` → 只加载 `shop/prison/` 分类；日限额 `daily-sell-limits.limits` 按 mode 匹配（只配 smp 时 prison 模式=无限额裸奔）
2. **条目无 `dynamic-pricing` 段 = 不开动态定价**（parseDynamicSettings 返回 null）；全局 `defaults` 只兜底「已配段但缺字段」，不自动启用
3. **升级跳过捆绑模板**：`shop/<mode>/categories/` 目录存在 → 日志 `Skipping bundled default category files` → jar 内新模板不覆盖。**模板改动升级必须删 `plugins/EzShops/shop/`**（保留 config.yml 的 language: zh、db/ 交易记录、messages/）
4. **交易记录不落盘 = 三层根因链（✅ 2026-08-29 全部修复，逐个排查）**：
   - ① **序列化崩溃**：一次卖 >99 个（批量 256）→ `ShopTransactionPersistenceListener.onSale` 序列化 count=256 的 ItemStack → MC 26.2 codec 越界（`[1;99]`）→ 交易成功但记录持久化失败。修复：持久化前 `clone() + setAmount(1)`（meta 保留，数量走 `TransactionRecord.quantity` 独立字段）
   - ② **命令/批量卖出不记录（插件缺陷，三个入口全查）**：`/sellhand` 走 `sell(Material)` **无 callEvent**、`sellDirect`（Quick Sell）无 callEvent、**`sellInventory`（/sellinventory 批量卖）自己实现批量卖出也无事件** → onSale 不触发 → 零记录（无报错）；只有 GUI 菜单卖出走 `sell(Item)`。修复：每个成功路径都补 callEvent；sellInventory 在 deposit 成功后**按物品循环发事件**。⚠️ bot 验收只测 sellhand 会漏 sellinventory——**批量卖出落盘也要验证**（give 128 → /sellinventory → transactions.yml 应出现 `|128|6.4|` 记录）
   - ③ **存储配置**：`player-shops.storage.type` 默认 `jaloquent`（指向 MySQL）——无 MySQL 时 transaction repository 连接失败，记录静默丢失（player-shops 组件会 fallback YAML 但 transaction repo 不回退，日志只有启动时一条 `Failed to initialise Jaloquent for player shops`）。**改 `yaml`**（transactions.yml 落盘，格式 `epochMs|SALE|uuid|qty|total|itemYaml`）；模板 config.yml 默认也应改 yaml 避免 MySQL 依赖
   - **排查方法论**：printStackTrace 的 stderr 可能不进 latest.log（log4j 重定向）→ 无堆栈 ≠ 没执行；用 `System.out.println("[DEBUG]...")` 插桩（stdout 必进日志，Paper 会 Nag 提醒改用 logger——验证后移除）；`javap -c` 反编译验证部署 jar 与源码一致
5. 配置改动 4 处同步：本地 Paper/Folia 部署端 + 仓库模板 `src/main/resources/shop/{prison,smp}`；Exaroton/MCSM 生产端升级：停服(0 玩家) → 删 shop/ → 换 jar → 启动重新生成 → 验证铁锭 sell=-1.0
6. **内嵌库类缺失 → catch Throwable 而非 Exception（2026-08-29 bStats 实测）**：MetricsComponent `new Metrics(plugin, 27734)` 只 catch `IllegalStateException` → bStats 部分 shade 缺失时 `NoClassDefFoundError: ...CustomChart`（**Error 不是 Exception，漏网**）→ 定时任务每次抛异常刷日志 + 触发 OrzMC exception_alert 群通知。修复：catch `Throwable`（含 NoClassDefFoundError）+ 服务端 `plugins/bStats/config.yml` `enabled: false` 双保险。排查法：`unzip -l jar | grep bstats` 确认类在 jar 里 ≠ 能加载（NoClassDefFoundError 是链式缺失/加载失败）
