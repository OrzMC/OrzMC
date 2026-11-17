#!/usr/bin/env python3
"""从 Exaroton 配置的 text 残留块解出原始完整内容，与当前真实段对比（以原始为准）

用法:
  python3 exa_recover_from_residue.py <path> [--apply] [--json-line]
  --apply     解包后 PUT 覆盖（默认 dry-run 只展示差异）
  --json-line 残留是 {"text"="..."} 单行（server.properties 形式）
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exa_file import get_file, put_file


def unescape(s):
    """解 Exaroton 残留块的转义：\\n -> 换行, \\= -> =, \\\" -> \", \\\\ -> \\"""
    return (s.replace('\\n', '\n').replace('\\=', '=')
             .replace('\\"', '"').replace('\\\\', '\\'))


def extract_yaml_text_block(text):
    """从 `text: "..."` YAML 折叠块解出原始内容"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('text: "') or line.startswith("text: '"):
            quote = line[6]
            buf = line[len('text: '):]
            if buf.startswith('"') or buf.startswith("'"):
                buf = buf[1:]
            j = i + 1
            while j < len(lines):
                nxt = lines[j].lstrip('\\ ')
                buf += '\n' + nxt
                if buf.count(quote) % 2 == 1 and buf.rstrip().endswith(quote):
                    break
                j += 1
            buf = buf.rstrip()
            if buf.endswith(quote):
                buf = buf[:-1]
            return unescape(buf), (i + 1, j + 1)
    return None, None


def extract_json_text_line(text):
    """从 `{"text"="..."}` 单行解出原始内容"""
    for line in text.splitlines():
        if '{"text"' in line:
            m = re.search(r'"text"="(.*)"\}', line, re.S)
            if m:
                return unescape(m.group(1)), None
    return None, None


def diff_keys(a, b):
    """a=原始(权威), b=当前真实段。返回 (仅原始有, 仅当前有)"""
    def keyset(s):
        return set(re.findall(r'^\s*([\w.-]+):', s, re.M))
    ka, kb = keyset(a), keyset(b)
    return sorted(ka - kb), sorted(kb - ka)


if __name__ == '__main__':
    path = sys.argv[1]
    apply_mode = '--apply' in sys.argv
    json_line = '--json-line' in sys.argv
    text = get_file(path)
    if json_line:
        orig, loc = extract_json_text_line(text)
        kind = 'json-line'
    else:
        orig, loc = extract_yaml_text_block(text)
        kind = 'yaml-text-block'
    if orig is None:
        print(f'OK {path}: 无残留块，无需恢复')
        sys.exit(0)
    lines = text.splitlines()
    if kind == 'yaml-text-block':
        cur = '\n'.join(lines[:loc[0] - 1]).strip()
    else:
        cur = '\n'.join(lines[:-1]).strip() if len(lines) > 1 else ''
    only_orig, only_cur = diff_keys(orig, cur)
    print(f'== {path} ({kind}, 残留行 {loc})')
    print(f'  原始(残留块解包): {len(orig.splitlines())} 行, 当前真实段: {len(cur.splitlines())} 行')
    print(f'  仅原始有的键({len(only_orig)}): {only_orig[:12]}')
    print(f'  仅当前有的键({len(only_cur)}): {only_cur[:12]}')
    if not apply_mode:
        print('  [dry-run] 加 --apply 才写回')
        sys.exit(0)
    try:
        import yaml
        d = yaml.safe_load(orig)
        print(f'  原始 YAML OK 顶层键: {list(d.keys())[:8]}')
    except Exception as ex:
        print(f'  FAIL 原始 YAML 解析失败（中止）: {str(ex)[:100]}')
        sys.exit(1)
    code, resp = put_file(path, orig)
    print(f'  PUT {code}')
    back = get_file(path)
    marker = 'text:' in back or '{"text"' in back
    print(f'  复验: 残留={"有" if marker else "无"}, 大小 {len(back)}B')
