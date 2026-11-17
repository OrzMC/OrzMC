#!/usr/bin/env python3
"""LoginSecurity → AuthMe 数据迁移脚本（SQLite→SQLite）
- 复制玩家密码哈希（BCrypt 直接复用，无需重置密码）
- 复制 ip / 注册时间 / 最后登录时间
- 跳过空密码玩家（记录到报告）
用法:
  python3 migrate_loginsecurity_to_authme.py
  python3 migrate_loginsecurity_to_authme.py --ls-db <LoginSecurity.db> --authme-db <authme.db> [--dry-run]
"""
import sqlite3, sys, time, os

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args

    def get_arg(flag, default):
        for i, a in enumerate(args):
            if a == flag and i + 1 < len(args):
                return args[i + 1]
        return default

    ls_db = os.path.expanduser(get_arg("--ls-db", "~/minecraft-server/plugins/LoginSecurity/LoginSecurity.db"))
    authme_db = os.path.expanduser(get_arg("--authme-db", "~/folia-test/plugins/AuthMe/authme.db"))

    if not os.path.exists(ls_db):
        print(f"❌ 源数据库不存在: {ls_db}")
        sys.exit(1)
    if not os.path.exists(authme_db):
        print(f"❌ 目标数据库不存在: {authme_db}")
        sys.exit(1)

    ls = sqlite3.connect(ls_db)
    au = sqlite3.connect(authme_db)

    # 读取 LoginSecurity 玩家
    rows = ls.execute("""
        SELECT last_name, password, ip_address, registration_date, last_login
        FROM ls_players
        WHERE password IS NOT NULL AND password != ''
    """).fetchall()
    print(f"源数据: {len(rows)} 个有效玩家（已过滤空密码）")

    # 已有 AuthMe 账号（防覆盖）
    existing = set(r[0] for r in au.execute("SELECT username FROM authme").fetchall())
    print(f"AuthMe 已有账号: {len(existing)}")

    # 检查 BCRYPT 格式
    bad = []
    for r in rows:
        if not r[1].startswith("$2"):
            bad.append(r[0])
    if bad:
        print(f"⚠️ 非 BCrypt 格式玩家（将跳过）: {bad}")

    now = int(time.time())
    inserted = 0
    skipped = 0
    for name, pwd, ip, regdate, lastlogin in rows:
        if name in existing:
            skipped += 1
            continue
        if not pwd.startswith("$2"):
            skipped += 1
            continue
        # AuthMe regdate/lastlogin 是 unix 时间戳
        reg_ts = int(regdate) if regdate else now
        login_ts = int(lastlogin) if lastlogin else 0
        if not dry:
            au.execute("""
                INSERT INTO authme (username, realname, password, ip, lastlogin, regip, regdate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, name, pwd, ip or "127.0.0.1", login_ts, ip or "127.0.0.1", reg_ts))
        inserted += 1

    if not dry:
        au.commit()

    print(f"\n{'[dry-run] ' if dry else '✅ '}迁移结果: 插入 {inserted}, 跳过 {skipped}（已存在/空密码/非bcrypt）")
    if not dry:
        print(f"AuthMe 现有账号总数: {au.execute('SELECT COUNT(*) FROM authme').fetchone()[0]}")

    ls.close(); au.close()

if __name__ == "__main__":
    main()
