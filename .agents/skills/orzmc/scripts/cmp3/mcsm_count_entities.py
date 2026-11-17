#!/usr/bin/env python3
"""统计玩家周边实体数量（计分板法，无副作用）
用法: python3 mcsm_count_entities.py <玩家名>
"""
import sys, os, time, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

player = sys.argv[1] if len(sys.argv) > 1 else "joker"
cfg = get_mcsm_config()
RADIUS = 32  # 客户端渲染半径（视距内）

def cmd(c):
    d = mcsm_api_post(cfg, "api/protected_instance/command",
        {"daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"], "command": c})
    return d.get("status") == 200

# 1. 初始化计分板（幂等，已存在则报错忽略）
for obj in ["nearby_total", "nearby_item", "nearby_mob", "nearby_deco"]:
    cmd(f"scoreboard objectives add {obj} dummy")
time.sleep(2)

# 2. 重置计数
for obj in ["nearby_total", "nearby_item", "nearby_mob", "nearby_deco"]:
    cmd(f"execute as {player} at @s run scoreboard players set {player} {obj} 0")
time.sleep(2)

# 3. 统计：以玩家位置为基准，RADIUS 内各类实体数
#    总实体（含玩家自身）
cmd(f"execute as {player} at @s run execute as @e[distance=..{RADIUS}] run scoreboard players add {player} nearby_total 1")
time.sleep(2)
# 掉落物
cmd(f"execute as {player} at @s run execute as @e[type=item,distance=..{RADIUS}] run scoreboard players add {player} nearby_item 1")
time.sleep(2)
# 生物（排除玩家/掉落物/装饰）
cmd(f"execute as {player} at @s run execute as @e[type=!player,type=!item,type=!painting,type=!item_frame,type=!armor_stand,type=!minecart,type=!boat,distance=..{RADIUS}] run scoreboard players add {player} nearby_mob 1")
time.sleep(2)
# 装饰类（画/展示框/盔甲架）
cmd(f"execute as {player} at @s run execute as @e[type=painting,type=item_frame,type=armor_stand,distance=..{RADIUS}] run scoreboard players add {player} nearby_deco 1")
time.sleep(2)

# 4. 获取 joker 当前位置
cmd(f"execute as {player} at @s run data get entity @s Pos")
time.sleep(2)

# 5. 读取结果
for obj in ["nearby_total", "nearby_item", "nearby_mob", "nearby_deco"]:
    cmd(f"scoreboard players get {player} {obj}")
    time.sleep(2)

print("✅ 统计命令已全部发送，等待日志输出")
