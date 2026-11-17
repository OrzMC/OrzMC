#!/usr/bin/env python3
"""Exaroton 配置文件安全读-改-写回（2026-08-09 实测翻车后固化）

问题：GET /files/data/{path}/ 可能返回裸文本或 JSON 包装（{"text":"..."}），
把 JSON 包装原样正则替换后 PUT 回写会损坏配置。
用法：
  python3 fix_exaroton_cfg.py <path> '<正则>|<替换>' [--check-key <key>]
示例：
  python3 fix_exaroton_cfg.py plugins/EzShops/config.yml 'type:\s*jaloquent|type: yaml'
"""
import sys, os, json, re, yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exa_file import get_file, put_file


def safe_get(path):
    """GET 并解包（裸文本或 JSON 包装都处理）"""
    raw = get_file(path)
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and 'text' in obj:
            print(f'[{path}] 检测到 JSON 包装，已解包 ({len(obj["text"])}B)')
            return obj['text']
    except Exception:
        pass
    print(f'[{path}] 已是纯文本 ({len(raw)}B)')
    return raw


def main():
    path = sys.argv[1]
    pattern, repl = sys.argv[2].split('|', 1)
    text = safe_get(path)
    # 改前校验
    try:
        d = yaml.safe_load(text)
        print(f'改前 YAML ✅ 顶层键: {list(d.keys())[:6]}')
    except Exception as e:
        print(f'改前 YAML ❌ {str(e)[:120]}（中止，先人工检查内容）')
        sys.exit(1)
    new = re.sub(r'(?m)' + pattern, repl, text, count=1)
    if new == text:
        print('⚠️ 正则无匹配，内容未变化')
        sys.exit(2)
    # 改后校验
    try:
        d2 = yaml.safe_load(new)
        print(f'改后 YAML ✅')
    except Exception as e:
        print(f'改后 YAML ❌ {str(e)[:120]}（中止，不写回）')
        sys.exit(1)
    code, body = put_file(path, new)
    print(f'PUT {path}: {code}')
    # 复验
    back = safe_get(path)
    print(f'复验: {"✅ 一致" if back == new else "❌ 不一致"}')
    if '--check-key' in sys.argv:
        k = sys.argv[sys.argv.index('--check-key') + 1]
        try:
            print(f'  {k} =', yaml.safe_load(back).get(k))
        except Exception:
            pass


if __name__ == '__main__':
    main()
