#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询 LoginSecurity.db 玩家注册/登录状态：python3 check_lsdb.py [db路径] [玩家名]
- db 默认 <服务器>/plugins/LoginSecurity/LoginSecurity.db（第 1 参可覆盖）
- 第 2 参玩家名可选；不传则列出全部已注册玩家
用法示例:
  python3 check_lsdb.py ~/minecraft-server/plugins/LoginSecurity/LoginSecurity.db joker
  python3 check_lsdb.py ~/minecraft-server/plugins/LoginSecurity/LoginSecurity.db
"""
import sqlite3
import sys
import os

DEFAULT_DB = os.path.expanduser(
    "~/minecraft-server/plugins/LoginSecurity/LoginSecurity.db"
)
DB = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
PLAYER = sys.argv[2] if len(sys.argv) > 2 else None

if not os.path.exists(DB):
    print(f"ERROR: 数据库不存在: {DB}")
    sys.exit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 列出表结构（不同版本表名可能不同）
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("表:", tables)

# 找玩家表（常见: players / loginsecurity）
player_table = None
for t in tables:
    if "player" in t.lower() or "login" in t.lower():
        player_table = t
        break
if not player_table:
    print("ERROR: 未找到玩家表")
    sys.exit(1)

cur.execute(f"PRAGMA table_info({player_table})")
cols = [r[1] for r in cur.fetchall()]
print(f"表 {player_table} 字段: {cols}")

if PLAYER:
    cur.execute(f"SELECT * FROM {player_table} WHERE LOWER(player_name)=LOWER(?)", (PLAYER,))
    rows = cur.fetchall()
else:
    cur.execute(f"SELECT * FROM {player_table}")
    rows = cur.fetchall()

print(f"\n共 {len(rows)} 条记录:")
for row in rows:
    # 脱敏：不打印密码哈希
    d = dict(zip(cols, row))
    safe = {k: v for k, v in d.items() if "pass" not in k.lower() and "salt" not in k.lower()}
    print(safe)

conn.close()
