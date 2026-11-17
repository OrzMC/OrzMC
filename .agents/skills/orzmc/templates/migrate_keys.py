#!/usr/bin/env python3
"""配置迁移模板：行级正则把旧配置 key 值迁移到新重建配置（保留注释/格式）。
⚠️ 行级匹配只命中第一个出现——多段同键名（如多个平台段各有 enabled/admin_group/admin_dm）
   时只迁首段，其余段需按段处理（手动 patch 或传父段缩进过滤）。
用法: python3 migrate_keys.py <旧配置> <新配置> <key> [<key> ...]
"""
import re
import sys


def migrate_key(backup_file: str, new_file: str, key: str) -> bool:
    old_lines = open(backup_file, encoding="utf-8").read().split("\n")
    new_lines = open(new_file, encoding="utf-8").read().split("\n")

    old_val = None
    for ln in old_lines:
        m = re.match(rf"^(\s*{re.escape(key)}\s*:\s*)(.*)$", ln)
        if m:
            old_val = m.group(2)
            break
    if old_val is None:
        print(f"跳过（旧文件无此键）: {key}")
        return False

    for i, ln in enumerate(new_lines):
        m = re.match(rf"^(\s*{re.escape(key)}\s*:\s*)(.*)$", ln)
        if m:
            new_lines[i] = m.group(1) + old_val
            open(new_file, "w", encoding="utf-8").write("\n".join(new_lines))
            print(f"✅ {key} → {old_val.strip()[:50]}")
            return True
    print(f"⚠️ 新文件无此键: {key}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    old_f, new_f = sys.argv[1], sys.argv[2]
    for k in sys.argv[3:]:
        migrate_key(old_f, new_f, k)
