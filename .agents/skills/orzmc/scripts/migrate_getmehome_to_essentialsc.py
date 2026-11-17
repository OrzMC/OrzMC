#!/usr/bin/env python3
"""GetMeHome → EssentialsC 数据迁移脚本
- 源: homes.yml (YAML)
- 目标: EssentialsC homes.db (SQLite)
- 结构映射: GetMeHome {uuid: {n: 名字, h: {home名: {w, c:[x,y,z], y:[yaw,pitch]}}}}
         → EssentialsC homes(uuid, name, world, x, y, z, yaw, pitch)
- 同名冲突策略: 目标已存在同名 home 时跳过（保留目标数据）
用法:
  python3 migrate_getmehome_to_essentialsc.py [--dry-run]
  python3 migrate_getmehome_to_essentialsc.py --yml <homes.yml> --db <homes.db> [--dry-run]
"""
import sqlite3, sys, os

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args

    def get_arg(flag, default):
        for i, a in enumerate(args):
            if a == flag and i + 1 < len(args):
                return args[i + 1]
        return default

    homes_yml = os.path.expanduser(get_arg("--yml", "~/minecraft-server/plugins/GetMeHome/homes.yml"))
    homes_db = os.path.expanduser(get_arg("--db", "~/folia-test/plugins/EssentialsC/databases/homes.db"))

    if not os.path.exists(homes_yml):
        print(f"❌ 源文件不存在: {homes_yml}")
        sys.exit(1)
    if not os.path.exists(homes_db):
        print(f"❌ 目标数据库不存在: {homes_db}")
        sys.exit(1)

    try:
        import yaml
    except ImportError:
        print("需要 PyYAML: pip3 install pyyaml")
        sys.exit(1)

    with open(homes_yml) as f:
        data = yaml.safe_load(f)

    players = {k: v for k, v in data.items() if k != "names" and isinstance(v, dict)}

    au = sqlite3.connect(homes_db)
    existing = set((r[0], r[1]) for r in au.execute("SELECT uuid, name FROM homes").fetchall())

    total_homes = 0
    inserted = 0
    skipped_exist = 0
    skipped_invalid = 0
    errors = []

    for uuid, p in players.items():
        homes = p.get("h", {}) if isinstance(p, dict) else {}
        name = p.get("n", uuid)
        if not homes:
            continue
        for hname, hdata in homes.items():
            total_homes += 1
            if not isinstance(hdata, dict):
                skipped_invalid += 1
                continue
            world = hdata.get("w", "world")
            coords = hdata.get("c", [])
            rot = hdata.get("y", [0, 0])
            if len(coords) != 3:
                skipped_invalid += 1
                errors.append(f"{name}/{hname}: 坐标异常 {coords}")
                continue
            x, y, z = coords
            yaw = rot[0] if len(rot) > 0 else 0
            pitch = rot[1] if len(rot) > 1 else 0
            key = (uuid, hname)
            if key in existing:
                skipped_exist += 1
                continue
            if not dry:
                au.execute("INSERT INTO homes (uuid, name, world, x, y, z, yaw, pitch) VALUES (?,?,?,?,?,?,?,?)",
                           (uuid, hname, world, x, y, z, yaw, pitch))
            inserted += 1

    if not dry:
        au.commit()

    print(f"源数据: {len(players)} 玩家, {total_homes} home")
    print(f"{'[dry-run] ' if dry else ''}插入: {inserted}, 跳过(目标已存在): {skipped_exist}, 跳过(数据异常): {skipped_invalid}")
    if errors[:5]:
        print("异常样本:", errors[:5])
    if not dry:
        print(f"EssentialsC homes 总数: {au.execute('SELECT COUNT(*) FROM homes').fetchone()[0]}")
    else:
        print("(dry-run 未写入)")
    au.close()

if __name__ == "__main__":
    main()
