#!/usr/bin/env python3
"""MCSM：列出实例根目录文件（磁盘占用分析）"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
base = {"apikey": cfg["apikey"], "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]}

for tgt in ["/", "\\", "", "."]:
    p = dict(base)
    if tgt:
        p["target"] = tgt
    url = cfg["url"] + "api/files/list?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers={
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
            data = d.get("data")
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
                print(f"target={tgt!r}: {len(items)} 项")
                total = sum(it.get("size", 0) for it in items)
                print(f"总计: {total/1024/1024:.1f}MB")
                for it in sorted(items, key=lambda x: x.get("size", 0), reverse=True)[:15]:
                    size = it.get("size", 0)
                    if size > 1024*1024:
                        print(f"  {size/1024/1024:>9.1f}MB  {it.get('name')}")
                break
            else:
                print(f"target={tgt!r}: status={d.get('status')} data={str(d.get('data'))[:150]}")
    except Exception as e:
        print(f"target={tgt!r}: ❌ {e}")
