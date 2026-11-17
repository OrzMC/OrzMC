#!/usr/bin/env python3
"""EzShops 商店套利审计：价格表（按 material 收集）+ MC 合成配方交叉检测。
用法: python3 shop_arbitrage_check.py <shop/prison|shop/smp 目录> [--full]
输出: 合成套利组合（产物 sell×乘数 vs 原料 buy 成本）+ 特惠轮换条目价格。
依赖: 仅标准库。改配置请用文本级正则（PyYAML 转储会破坏 {translate:...}）。
"""
import yaml, glob, sys

CATS = sys.argv[1]
FULL = "--full" in sys.argv

# 收集价格表：按 material 字段（特惠条目 key 是展示名，按 key 会漏）
items = {}
for f in sorted(glob.glob(f"{CATS}/categories/*.yml")):
    d = yaml.safe_load(open(f))
    for cat_key, cat in d.get("categories", {}).items():
        for k, v in cat.get("items", {}).items():
            if v.get("buy") is not None and v.get("sell") is not None:
                mat = v.get("material", k).upper()
                amt = v.get("amount", 1)
                items[mat] = {"cat": f.split("/")[-1], "buy": v["buy"] / amt,
                              "sell": v["sell"] / amt, "sell_tot": v["sell"]}

# 特惠轮换条目（daily_specials rotation-defaults + rotations/*.yml options）
rot_items = {}
for rf in glob.glob(f"{CATS}/categories/daily_specials.yml") + glob.glob(f"{CATS}/rotations/*.yml"):
    try:
        d = yaml.safe_load(open(rf))
    except Exception:
        continue
    def walk(o):
        if isinstance(o, dict):
            if o.get("material") and o.get("sell") is not None:
                rot_items[o["material"].upper()] = o["sell"]
            for v in o.values():
                walk(v)
    walk(d)

# 合成配方：产物 -> [(原料, 数量)]；乘数在下方注释标注
RECIPES = {
    "BONE_MEAL": [("BONE", 1)],  # x3
    "STONE_BRICKS": [("STONE", 4)],  # x4
    "COOKIE": [("WHEAT", 2), ("COCOA_BEANS", 1)],  # x8
    "GLASS": [("SAND", 1)],
    "BRICKS": [("CLAY", 4)],
    "STONE": [("COBBLESTONE", 1)],
    "QUARTZ_BLOCK": [("QUARTZ", 4)],
    "AMETHYST_BLOCK": [("AMETHYST_SHARD", 4)],
    "IRON_BLOCK": [("IRON_INGOT", 9)],
    "GOLD_BLOCK": [("GOLD_INGOT", 9)],
    "DIAMOND_BLOCK": [("DIAMOND", 9)],
    "EMERALD_BLOCK": [("EMERALD", 9)],
    "COAL_BLOCK": [("COAL", 9)],
    "REDSTONE_BLOCK": [("REDSTONE", 9)],
    "OAK_PLANKS": [("OAK_LOG", 1)],  # x4
    "BONE_BLOCK": [("BONE_MEAL", 9)],
    "HAY_BLOCK": [("WHEAT", 9)],
    "MELON": [("MELON_SLICE", 9)],
}
MULT = {"BONE_MEAL": 3, "STONE_BRICKS": 4, "COOKIE": 8, "OAK_PLANKS": 4}

print(f"== 商店物品数: {len(items)} | 特惠轮换条目: {len(rot_items)} ==")
print("\n== 合成套利 ==")
for prod, recipe in sorted(RECIPES.items()):
    if prod not in items:
        continue
    ps = items[prod]["sell"] * MULT.get(prod, 1)
    cost, missing = 0.0, []
    for mat, n in recipe:
        if mat in items:
            cost += items[mat]["buy"] * n
        else:
            missing.append(mat)
    if missing:
        print(f"  {prod}: 原料缺 {missing} → 无套利路径")
        continue
    profit = ps - cost
    mark = "🔥 套利!" if profit > 0.01 else "✅"
    print(f"  {prod}: 成本={cost:.2f} 收益={ps:.2f} 利润={profit:.2f} {mark}")

print("\n== 特惠轮换高价条目（>0.5/个 且 常规已压价/禁卖则可疑）==")
for mat, sell in sorted(rot_items.items()):
    if sell > 0.5:
        note = f"常规: {items[mat]['sell']:.4f}" if mat in items else "常规不在商店"
        print(f"  {mat}: 特惠卖={sell}/个（{note}）")

if FULL:
    print("\n== sell/buy ≥0.7（套利温床）==")
    for k, v in sorted(items.items()):
        if v["buy"] > 0 and v["sell"] > 0 and v["sell"] / v["buy"] >= 0.7:
            print(f"  {k}: 卖/买={v['sell']/v['buy']:.2f}")
