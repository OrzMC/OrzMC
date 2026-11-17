#!/usr/bin/env python3
"""统计玩家周边实体构成（计分板法，无副作用）

用法: python3 mcsm_entity_audit.py <玩家名> <半径> [中心X 中心Z]
  - 默认中心: (2.0, -13.5) 需按实际玩家位置改，或传 X Z 参数
  - 半径: 水平 ±R 格、全高度 (y=0..320) 的水平框（非 3D 球体！）

关键坑（1.20.5+ 实测）:
  1. type=A,type=B 多值 OR 失效返回 0 —— 必须每个类型单独一条命令
  2. distance=..N 是 3D 球体，高空玩家会漏掉下方地面实体 —— 用水平框
  3. dx/dz 必须配 y/dy（缺 y 默认 y=0 单层只返回 1）

输出: 日志中每条 `has N [eaudit]` 对应一个类型；末尾总数对照。
解析日志: 用「type= 命令 echo → 紧随其后的 has N」配对（容忍玩家聊天插入）。
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

player = sys.argv[1] if len(sys.argv) > 1 else "joker"
radius = float(sys.argv[2]) if len(sys.argv) > 2 else 32.0
cx = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
cz = float(sys.argv[4]) if len(sys.argv) > 4 else -13.5
cfg = get_mcsm_config()

_X0, _Z0 = cx - radius, cz - radius
_SEL = f"x={_X0},y=0.0,z={_Z0},dx={radius*2},dy=320.0,dz={radius*2}"

def cmd(c):
    mcsm_api_post(cfg, "api/protected_instance/command",
        {"daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"], "command": c})

cmd("scoreboard objectives add eaudit dummy")
time.sleep(2)

# 所有实体类型（单类型，Minecraft 1.21 全集；type 多值 OR 会失效！）
TYPES = [
    "villager", "wandering_trader", "zombie_villager", "iron_golem", "snow_golem",
    "painting", "item_frame", "glow_item_frame", "armor_stand",
    "block_display", "item_display", "text_display", "marker", "interaction",
    "minecart", "chest_minecart", "furnace_minecart", "tnt_minecart", "hopper_minecart",
    "boat", "chest_boat",
    "item", "experience_orb",
    "arrow", "spectral_arrow", "trident", "snowball", "egg", "ender_pearl",
    "fireball", "small_fireball", "wither_skull", "shulker_bullet", "potion",
    "experience_bottle", "fishing_bobber", "eye_of_ender",
    "zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", "witch",
    "slime", "phantom", "drowned", "husk", "stray", "blaze", "ghast", "magma_cube",
    "piglin", "piglin_brute", "zombified_piglin", "hoglin", "zoglin", "warden",
    "breeze", "bogged", "creaking",
    "chicken", "cow", "pig", "sheep", "horse", "rabbit", "wolf", "cat", "parrot",
    "llama", "bee", "fox", "panda", "turtle", "dolphin", "squid", "glow_squid",
    "goat", "axolotl", "frog", "tadpole", "allay", "mooshroom", "ocelot", "mule",
    "donkey", "skeleton_horse", "zombie_horse", "camel", "sniffer", "armadillo",
    "pufferfish", "salmon", "cod", "tropical_fish", "polar_bear", "strider",
    "trader_llama", "bat",
    "wither", "ender_dragon", "ravager", "vex", "evoker", "pillager", "vindicator",
    "illusioner", "shulker", "silverfish", "endermite", "guardian", "elder_guardian",
    "tnt", "end_crystal", "falling_block", "area_effect_cloud", "lightning_bolt",
    "leash_knot",
]

TYPES = list(dict.fromkeys(TYPES))  # 去重

for t in TYPES:
    cmd(f"scoreboard players set {player} eaudit 0")
    time.sleep(0.8)
    cmd(f"execute as {player} at @s run execute as @e[type={t},{_SEL}] run scoreboard players add {player} eaudit 1")
    time.sleep(0.8)
    cmd(f"scoreboard players get {player} eaudit")
    time.sleep(0.8)

# 总数对照（无 type 过滤）
cmd(f"scoreboard players set {player} eaudit 0")
time.sleep(1)
cmd(f"execute as {player} at @s run execute as @e[{_SEL}] run scoreboard players add {player} eaudit 1")
time.sleep(1)
cmd(f"scoreboard players get {player} eaudit")

print(f"✅ {len(TYPES)} 个类型 + 总数对照已统计（半径 {radius}，中心 {cx},{cz}）")
