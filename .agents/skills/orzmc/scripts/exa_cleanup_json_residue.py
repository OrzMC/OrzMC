#!/usr/bin/env python3
"""清理 Exaroton 配置文件尾部的 JSON 包装残留块（text: "..." 或 {"text": "..."}）

背景（2026-08-10 定位）：早期 exa_apply_config.py 用 JSON 包装 PUT 写配置，
被原样存为文件内容 → 文件尾残留 `text: "..."`（YAML 形式）或 `{"text"="..."}`（properties 形式）
垃圾块。Paper 解析时前段真实配置有效，残留块变成垃圾 key 无害，但文件脏且易误判。

用法:
  python3 exa_cleanup_json_residue.py <path> [--dry-run]
示例:
  python3 exa_cleanup_json_residue.py config/paper-world-defaults.yml --dry-run
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exa_file import get_file, put_file

def find_residue(text):
    """返回 (起始行号, 结束行号, 类型) 或 None"""
    lines = text.splitlines()
    # 类型1: YAML `text: "..."` 折叠块（以 text: 开头，含 \\n 转义）
    for i, line in enumerate(lines):
        if line.startswith('text: "') and ('\\n' in line or '\\=' in line):
            # 找块结束：后续行以 \\ 续行，直到某行不再以 \\ 结尾
            j = i
            while j < len(lines) and lines[j].rstrip().endswith('\\'):
                j += 1
            # j 指向续行链的最后一个 \\ 行；块含 text: 行到 j
            return (i, j, 'yaml-text-block')
    # 类型2: `{"text"="..."}` 单行（server.properties 污染）
    for i, line in enumerate(lines):
        if '{"text"' in line and ('\\n' in line or '\\=' in line):
            return (i, i, 'json-text-line')
    return None

def strip_residue(text, dry_run=False):
    loc = find_residue(text)
    if not loc:
        return text, None
    start, end, kind = loc
    lines = text.splitlines()
    # 清理：删除 start..end 行；若前面有空行也清掉
    del_start = start
    while del_start > 0 and lines[del_start - 1].strip() == '':
        del_start -= 1
    kept = lines[:del_start] + lines[end + 1:]
    # 尾部空行清理
    while kept and kept[-1].strip() == '':
        kept.pop()
    new_text = '\n'.join(kept) + '\n'
    # 安全校验：清理后仍是合法 YAML（若原文件是 yaml）
    return new_text, (start + 1, end + 1, kind)

if __name__ == '__main__':
    path = sys.argv[1]
    dry = '--dry-run' in sys.argv
    text = get_file(path)
    new_text, info = strip_residue(text, dry)
    if not info:
        print(f'✅ {path}: 无 JSON 残留（{len(text)}B）')
        sys.exit(0)
    s, e, kind = info
    print(f'⚠️ {path}: 发现 {kind} 残留 行 {s}-{e}（{len(text)}B → {len(new_text)}B）')
    if dry:
        print('  [dry-run] 未写回。确认后去掉 --dry-run 执行清理。')
        sys.exit(0)
    # 写回前 YAML 校验
    try:
        import yaml
        d = yaml.safe_load(new_text)
        print(f'  清理后 YAML ✅ 顶层键: {list(d.keys())[:8]}')
    except Exception as ex:
        print(f'  ❌ 清理后 YAML 解析失败（中止，不写回）: {str(ex)[:100]}')
        sys.exit(1)
    code, resp = put_file(path, new_text)
    print(f'  PUT {code}')
    back = get_file(path)
    print(f'  复验: 残留={"有" if find_residue(back) else "无"}，大小 {len(back)}B')
