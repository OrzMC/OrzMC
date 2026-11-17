#!/usr/bin/env python3
"""执行恢复 v2（2026-08-10 用户决策：以 text 原始内容为准）
- paper-global.yml / paper-world-defaults.yml: 残留块解包 = 完整原始配置(超集) → 覆盖
- server.properties: 残留块是旧快照(force-gamemode=true 等废弃值) → 保留当前真实段，仅删残留行
"""
import sys, os, yaml, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exa_file import get_file, put_file

def recover_via_yaml(text):
    d = yaml.safe_load(text)
    if isinstance(d, dict) and 'text' in d:
        raw = d['text']
        return raw.replace('\\n', '\n').replace('\\=', '=').replace('\\"', '"').replace('\\\\', '\\')
    return None

DRY = '--dry-run' in sys.argv

# ---- 1. yml 文件：用残留块解包覆盖 ----
for path in ['config/paper-global.yml', 'config/paper-world-defaults.yml']:
    text = get_file(path)
    orig = recover_via_yaml(text)
    if orig is None:
        print(f'⚠️  {path}: 未找到残留块')
        continue
    try:
        yaml.safe_load(orig)
        print(f'== {path}: 解包 {len(orig.splitlines())} 行 YAML OK')
    except Exception as e:
        print(f'❌ {path}: 解包 YAML 失败 {str(e)[:60]}')
        continue
    if DRY:
        continue
    code, resp = put_file(path, orig)
    print(f'   PUT {code}')
    back = get_file(path)
    marker = 'text:' in back
    print(f'   复验: 残留={"有!" if marker else "无 ✅"}, {len(back)}B, 含残留块行数={sum(1 for l in back.splitlines() if l.startswith("text:"))}')

# ---- 2. server.properties：删残留行，保留真实段 ----
path = 'server.properties'
text = get_file(path)
lines = text.splitlines()
keep = [l for l in lines if '{"text"' not in l]
clean = '\n'.join(keep) + ('\n' if keep else '')
print(f'== {path}: 删除残留行 {len(lines) - len(keep)} 行, 保留 {len(keep)} 行')
if not DRY:
    code, resp = put_file(path, clean)
    print(f'   PUT {code}')
    back = get_file(path)
    marker = '{"text"' in back
    print(f'   复验: 残留={"有!" if marker else "无 ✅"}, {len(back)}B')

print(f'\n{"[DRY-RUN] 未写回" if DRY else "恢复完成"}')
