#!/usr/bin/env python3
"""解析 MCSM outputlog：提取当前在线玩家列表"""
import json, sys, re

def main():
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

    online = 0
    names = []
    for i, l in enumerate(lines):
        m = re.search(r'当前在线\((\d+)/\d+\)', l)
        if m:
            online = int(m.group(1))
            names = []
            for l2 in lines[i+1:i+40]:
                s = l2.strip()
                if re.match(r'^[A-Za-z0-9_]{1,16}( 生存模式| 创造模式| 冒险模式| 旁观模式|\(op\) 生存模式|\(op\) 创造模式)', s):
                    names.append(s.split()[0])
                elif s.startswith('[') or '在线' in s:
                    break

    print(f'在线: {online} 人')
    if names:
        print('玩家:', ', '.join(names))
    else:
        print('（日志中未解析到玩家名）')

if __name__ == '__main__':
    main()
