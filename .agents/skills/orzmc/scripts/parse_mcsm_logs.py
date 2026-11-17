#!/usr/bin/env python3
"""解析 MCSM outputlog：输出最近 N 行日志"""
import json, sys, re

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    raw = sys.stdin.read()
    try:
        d = json.loads(raw)
    except Exception:
        print("❌ 日志获取失败")
        sys.exit(1)
    if d.get("status") != 200:
        print(f"❌ API 错误: {d.get('data', 'unknown')}")
        sys.exit(1)
    log = d["data"]
    # 剥离 ANSI 控制字符
    log = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', log)
    log = log.replace('\x1b[?25l', '').replace('\x1b[?25h', '').replace('\x1b[0K', '')
    lines = [l.strip() for l in log.split('\r') if l.strip() and l.strip() != '>']
    print('\n'.join(lines[-n:]))

if __name__ == '__main__':
    main()
