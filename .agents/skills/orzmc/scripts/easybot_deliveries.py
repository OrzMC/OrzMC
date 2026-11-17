#!/usr/bin/env python3
"""EasyBot 投递诊断（0.0.33+ 版）：调用 API 查询最近投递状态。

0.0.33 起投递记录迁移到 messages 表（outbound_deliveries 停止写入）；
且 SQLite WAL 模式下 docker cp 单文件会漏最近提交 → 改用 API 查询。
用法: python3 easybot_deliveries.py [条数] [base_url]
依赖: python3（urllib 标准库）；admin 密码从 /Users/Shared/orzmc/.env 读取
（2026-09-03 EasyBot 迁入 orzmc 生产栈：默认 base 改公网 easybot.{SERVER_NAME}.cn，
密码源改 $DATA_ROOT/.env；CF 边缘按 UA 拦截 → 内置浏览器 UA）
"""
import json
import sys
import urllib.request
import datetime
import os

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8
BASE = sys.argv[2] if len(sys.argv) > 2 else 'https://easybot.{SERVER_NAME}.cn'

# 读 admin 密码（优先 orzmc 栈 .env，fallback 旧 deploy-kit .env）
password = None
for env_path in ('/Users/Shared/orzmc/.env',):
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('EASYBOT_ADMIN_PASSWORD='):
                    password = line.split('=', 1)[1].strip("'\"")
                    break
    if password:
        break
if not password:
    print('✗ 未找到 admin 密码（/Users/Shared/orzmc/.env 无 EASYBOT_ADMIN_PASSWORD）')
    sys.exit(2)


def api(method, path, data=None, key=None):
    req = urllib.request.Request(f'{BASE}{path}', method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')  # CF 边缘按 UA 拦截 urllib 默认 UA
    if key:
        req.add_header('Authorization', f'Bearer {key}')
    body = json.dumps(data).encode() if data is not None else None
    with urllib.request.urlopen(req, body, timeout=15) as r:
        return json.loads(r.read() or b'{}')


key = api('POST', '/admin/login', {'password': password})['key']
msgs = api('GET', f'/api/v1/messages?limit={N}', key=key)['messages']

print(f'最近 {len(msgs)} 条投递（时间 平台 状态 内容）:')
for m in msgs:
    ts = datetime.datetime.fromtimestamp(m['timestamp'] / 1000).strftime('%H:%M:%S')
    res = (m.get('raw_data') or {}).get('result') or {}
    ok = res.get('success')
    role = (m.get('role') or '').lower()
    is_out = role == 'assistant'
    mark = '✅' if ok else ('❌' if is_out else '◌')
    text = (m.get('text') or '').replace('\n', '⏎')[:44]
    print(f'{ts} {mark} {m["platform"]:7s} [{"出" if is_out else "入"}] | {text}')
    if not ok and is_out:
        print(f'      error={res.get("error") or res.get("error_code")}')
