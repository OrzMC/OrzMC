#!/usr/bin/env python3
"""审查变化跟踪 v2：精确对比两份报告的差异项（key 级别），输出增删变化"""
import sys, re

def extract(path):
    """返回 {文件: set(差异项字符串)} — 差异项 = key|本地|Exa|MCSM"""
    result = {}
    cur_file = None
    in_table = False
    for line in open(path, encoding='utf-8'):
        s = line.rstrip()
        if s.startswith('### '):
            m = re.match(r'### [❌✅ℹ️] (.+?) — (?:差异|三端)', s)
            if m:
                cur_file = m.group(1).strip()
                result.setdefault(cur_file, set())
                in_table = False
                continue
        if s.startswith('| key |'):
            in_table = True
            continue
        if in_table and s.startswith('| '):
            cols = [c.strip() for c in s.strip('|').split('|')]
            if len(cols) == 4:
                result.setdefault(cur_file, set()).add('|'.join(cols))
        elif s.startswith('  - `'):
            m = re.match(r'  - `([^`]+)`：本地=`([^`]*)` Exa=`([^`]*)` MCSM=`([^`]*)`', s)
            if m and cur_file:
                result.setdefault(cur_file, set()).add('|'.join([m.group(1), m.group(2), m.group(3), m.group(4)]))
    return result

if __name__ == '__main__':
    old = extract(sys.argv[1])
    new = extract(sys.argv[2])
    all_files = sorted(set(old) | set(new))
    print(f"对比: {sys.argv[1].split('/')[-1]} → {sys.argv[2].split('/')[-1]}\n")
    for f in all_files:
        o, n = old.get(f, set()), new.get(f, set())
        added = n - o
        removed = o - n
        if not added and not removed:
            continue
        print(f"【{f}】")
        for a in sorted(added):
            print(f"  🆕 {a}")
        for r in sorted(removed):
            print(f"  🗑️ {r}")
        if not added and not removed:
            pass
    # 汇总
    unchanged = [f for f in all_files if old.get(f, set()) == new.get(f, set())]
    print(f"\n=== 汇总：{len(all_files)} 个差异文件，其中 {len(unchanged)} 个差异项完全未变 ===")
    print("未变文件:", ', '.join(unchanged))
