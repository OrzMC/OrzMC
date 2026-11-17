#!/usr/bin/env python3
"""OrzMC 玩家入场监听（改完配置后验证「玩家到底能不能进」）

原理：基岩玩家经 Geyser 进服后，**Java 侧在线人数也会 +1**（Geyser 桥接）。
所以同时采两个源：
  · Java Status Ping 在线人数（任何玩家都会体现在这里）
  · 基岩 NetherNet 信令 /v1/join 在线人数（Geyser 自己数的基岩玩家）
任一上升即说明「有玩家成功进入」。

用法:
  python3 conn_watch.py                         # {SERVER_HOST}:25565，监听 180s
  python3 conn_watch.py --host dev.{SERVER_NAME}.cn --java 25565 --bedrock 19132
  python3 conn_watch.py --duration 600 --interval 10
  python3 conn_watch.py --json                  # 每轮一行 JSON（供脚本消费）
  python3 conn_watch.py -h

退出码: 0=期间检测到玩家 / 1=未检测到 / 2=参数错误 / 3=数据源不可用
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import connectivity_check as cc
except Exception as e:  # pragma: no cover
    print("无法加载 connectivity_check.py：%s" % e, file=sys.stderr)
    sys.exit(2)


def resolve(host):
    if cc._is_ip_literal(host):
        return host
    ips = cc.resolve(host)
    if isinstance(ips, str):
        return None
    ip = ips[0]
    if cc.is_fake_ip(ip):
        real = cc.doh_resolve(host)
        if real:
            return real[0]
        return None
    return ip


def main():
    ap = argparse.ArgumentParser(description="监听玩家入场（Java + 基岩双源）")
    ap.add_argument("--host", default="{SERVER_HOST}")
    ap.add_argument("--java", type=int, default=25565)
    ap.add_argument("--bedrock", type=int, default=19132)
    ap.add_argument("--duration", type=int, default=180, help="总时长秒（默认 180）")
    ap.add_argument("--interval", type=int, default=10, help="采样间隔秒（默认 10）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    ip = resolve(a.host)
    if not ip:
        print("DNS 解析失败或被 TUN 劫持且 DoH 失败，无法继续", file=sys.stderr)
        return 3

    if not a.json:
        print("目标 %s (%s) | Java %d / 基岩 %d | 监听 %ds，每 %ds 采样"
              % (a.host, ip, a.java, a.bedrock, a.duration, a.interval), flush=True)
        print("现在请让玩家连接；出现「✅」即表示成功进入\n", flush=True)

    t0 = time.time()
    last = None
    hit = False
    errs = 0
    while time.time() - t0 < a.duration:
        try:
            js = cc.java_status(ip, a.java, timeout=6)
            jp, jm, jv = js.get("players"), js.get("max"), js.get("version")
        except Exception as e:
            jp, jm, jv = None, None, "ERR:%s" % str(e)[:30]
            errs += 1
        try:
            nn = cc.nethernet_join(ip, a.bedrock, timeout=6)
            gp = nn.get("players") if nn.get("ok") else None
        except Exception:
            gp = None
            errs += 1

        rec = dict(t=time.strftime("%H:%M:%S"), java_online=jp, java_max=jm,
                   java_version=jv, bedrock_online=gp, elapsed=int(time.time() - t0))

        if isinstance(jp, int) and jp > 0:
            hit = True

        if a.json:
            print(json.dumps(rec, ensure_ascii=False), flush=True)
        else:
            changed = (jp, gp) != last
            mark = "✅" if (isinstance(jp, int) and jp > 0) else "  "
            if changed or rec["elapsed"] % 60 < a.interval:
                print("%s [%s] Java在线=%s/%s | 基岩在线=%s | %s"
                      % (mark, rec["t"], jp, jm, gp, jv), flush=True)
            last = (jp, gp)
        time.sleep(a.interval)

    if a.json:
        print(json.dumps(dict(result="hit" if hit else "miss", samples=int(a.duration / a.interval),
                              errors=errs), ensure_ascii=False))
    else:
        print("\n结果：" + ("✅ 检测到玩家成功进入" if hit else "未检测到玩家进入（窗口内无人连接）"))
    if hit:
        return 0
    return 3 if errs and not hit and errs >= max(1, a.duration // a.interval) else 1


if __name__ == "__main__":
    sys.exit(main())
