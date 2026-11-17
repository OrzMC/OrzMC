#!/usr/bin/env python3
"""Analyze scanned command blocks: categorize commands, types, trigger modes."""
import json, sys, re
from collections import Counter

DISABLED_CMDS = {'bossbar','clone','data','datapack','debug','function','item','loot',
    'reload','return','ride','rotate','schedule','scoreboard','spectate','spreadplayers',
    'tag','team','teammsg','tick','trigger','perf','save-all','saveall','restart'}

def first_word(cmd):
    if not cmd: return ''
    cmd = cmd.strip().lstrip('/')
    m = re.match(r'([a-z0-9_:\-]+)', cmd)
    return m.group(1) if m else ''

def main(path):
    blocks = json.load(open(path))
    if not blocks:
        print('NO command blocks found in world.')
        return
    n = len(blocks)
    print(f'=== {n} command blocks found ===')
    types = Counter(b.get('id','?') for b in blocks)
    print('\nby block type:', dict(types))
    autos = Counter(b.get('auto', -1) for b in blocks)
    print('by auto mode (1=always active, 0=needs redstone):', dict(autos))
    dims = Counter(b.get('dim','?') for b in blocks)
    print('by dimension:', dict(dims))

    cmds = []
    for b in blocks:
        c = b.get('Command','')
        cmds.append(c)
    firsts = Counter(first_word(c) for c in cmds)
    print('\nby first command word (top 30):')
    for w, cnt in firsts.most_common(30):
        print(f'  {w}: {cnt}')

    disabled_use = {w: cnt for w, cnt in firsts.items() if w in DISABLED_CMDS}
    if disabled_use:
        print('\n⚠️ commands depending on Folia-DISABLED commands:', disabled_use)
        dep = sum(disabled_use.values())
        print(f'  ({dep}/{n} blocks use disabled commands — these cannot be emulated)')
    else:
        print('\n✅ no command blocks use Folia-disabled commands')

    # region concentration
    regions = Counter(b.get('region','?') for b in blocks)
    print('\nby region (top 15):')
    for r, cnt in regions.most_common(15):
        xs = [b.get('x') for b in blocks if b.get('region')==r]
        zs = [b.get('z') for b in blocks if b.get('region')==r]
        print(f'  {r}: {cnt} blocks, x~{min(xs) if xs else 0}-{max(xs) if xs else 0}, z~{min(zs) if zs else 0}-{max(zs) if zs else 0}')

    # sample every unique command
    print('\nunique commands:')
    seen = set()
    for b in blocks:
        c = b.get('Command','')
        key = (c, b.get('id'))
        if key in seen: continue
        seen.add(key)
        print(f'  [{b.get("id","?")}] {c[:160]}')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/cmdblocks.json')
