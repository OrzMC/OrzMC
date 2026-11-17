#!/usr/bin/env python3
"""精确统计玩家周边实体（每个类型单独一条命令）
⚠️ Minecraft 1.20.5+ type= 参数不支持逗号多值 OR，必须单类型
用法: python3 mcsm_entity_audit.py <玩家名> <半径>
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

player = sys.argv[1] if len(sys.argv) > 1 else "joker"
radius = float(sys.argv[2]) if len(sys.argv) > 2 else 32.0
cfg = get_mcsm_config()

# 水平区域模式（推荐）：以玩家位置为中心 ±radius，全高度
# 用法: python3 mcsm_entity_audit.py joker 32 box
# 需要 player_pos.py 提供坐标，或手动指定 X Z
import json as _json
_center = {"x": 2.0, "z": -13.5}  # 手动指定中心（或从玩家实时获取）
if len(sys.argv) > 4:
    _center = {"x": float(sys.argv[3]), "z": float(sys.argv[4])}
_X, _Z = _center["x"], _center["z"]
_X0, _Z0 = _X - radius, _Z - radius
_SEL = f"x={_X0},y=0.0,z={_Z0},dx={radius*2},dy=320.0,dz={radius*2}"

def cmd(c):
    mcsm_api_post(cfg, "api/protected_instance/command",
        {"daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"], "command": c})

cmd("scoreboard objectives add eaudit dummy")
time.sleep(2)

# 所有实体类型（单类型，Minecraft 1.21 全集）
TYPES = [
    # 村民/守卫
    "villager", "wandering_trader", "zombie_villager", "iron_golem", "snow_golem",
    # 装饰
    "painting", "item_frame", "glow_item_frame", "armor_stand",
    # display 实体（1.19.4+，客户端渲染大头）
    "block_display", "item_display", "text_display", "marker", "interaction",
    # 载具
    "minecart", "chest_minecart", "furnace_minecart", "tnt_minecart", "hopper_minecart",
    "boat", "chest_boat",
    # 掉落/经验
    "item", "experience_orb",
    # 投射物
    "arrow", "spectral_arrow", "trident", "snowball", "egg", "ender_pearl",
    "fireball", "small_fireball", "wither_skull", "shulker_bullet", "potion",
    "experience_bottle", "fishing_bobber", "eye_of_ender",
    # 常见怪
    "zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", "witch",
    "slime", "phantom", "drowned", "husk", "stray", "blaze", "ghast", "magma_cube",
    "piglin", "piglin_brute", "zombified_piglin", "hoglin", "zoglin", "warden",
    "breeze", "bogged", "creaking",
    # 动物
    "chicken", "cow", "pig", "sheep", "horse", "rabbit", "wolf", "cat", "parrot",
    "llama", "bee", "fox", "panda", "turtle", "dolphin", "squid", "glow_squid",
    "goat", "axolotl", "frog", "tadpole", "allay", "mooshroom", "ocelot", "mule",
    "donkey", "skeleton_horse", "zombie_horse", "camel", "sniffer", "armadillo",
    "pufferfish", "salmon", "cod", "tropical_fish", "polar_bear", "strider",
    "trader_llama", "bat",
    # BOSS/灾厄
    "wither", "ender_dragon", "ravager", "vex", "evoker", "pillager", "vindicator",
    "illusioner", "shulker", "silverfish", "endermite", "guardian", "elder_guardian",
    # 杂项
    "tnt", "end_crystal", "falling_block", "area_effect_cloud", "lightning_bolt",
    "leash_knot", "trident",
]

# 去重
TYPES = list(dict.fromkeys(TYPES))

# 统计：每个类型单独命令
for t in TYPES:
    cmd(f"scoreboard players set {player} eaudit 0")
    time.sleep(0.8)
    cmd(f"execute as {player} at @s run execute as @e[type={t},{_SEL}] run scoreboard players add {player} eaudit 1")
    time.sleep(0.8)
    cmd(f"scoreboard players get {player} eaudit")
    time.sleep(0.8)

# 总实体（对照）
cmd(f"scoreboard players set {player} eaudit 0")
time.sleep(1)
cmd(f"execute as {player} at @s run execute as @e[{_SEL}] run scoreboard players add {player} eaudit 1")
time.sleep(1)
cmd(f"scoreboard players get {player} eaudit")

print(f"✅ {len(TYPES)} 个类型 + 总数对照 已统计（半径 {radius}）")
