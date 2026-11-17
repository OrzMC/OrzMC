#!/usr/bin/env python3
"""MCSM 配置对齐修改（2026-08-11 用户决策：第一类零风险项）
修改项（只写文件，不重启——有玩家在线，等无玩家窗口重启生效）：
  1. config/paper-global.yml:       proxies.velocity.online-mode: true → false
  2. config/paper-world-defaults.yml: disable-unloaded-chunk-enderpearl-exploit: false → true
  3. server.properties:             resource-pack-prompt="" → 空
"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

def read(path):
    data = mcsm_download(cfg, path)
    return data.decode("utf-8") if data is not None else None

def write(path, text):
    url = cfg["url"] + "api/files/?" + urllib.parse.urlencode({
        "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"], "apikey": cfg["apikey"]})
    req = urllib.request.Request(url, method="PUT",
        data=json.dumps({"target": path, "text": text}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    return d.get("status") == 200

CHANGES = [
    ("/config/paper-global.yml",
     "  velocity:\n    enabled: false\n    online-mode: true",
     "  velocity:\n    enabled: false\n    online-mode: false"),
    ("/config/paper-world-defaults.yml",
     "disable-unloaded-chunk-enderpearl-exploit: false",
     "disable-unloaded-chunk-enderpearl-exploit: true"),
    ("/server.properties",
     'resource-pack-prompt=""',
     "resource-pack-prompt="),
]

for path, old, new in CHANGES:
    txt = read(path)
    if txt is None:
        print(f"  ❌ {path}: 读失败")
        continue
    if old not in txt:
        print(f"  ⚠️ {path}: 未找到 `{old[:40]}...`（跳过）")
        continue
    txt2 = txt.replace(old, new, 1)
    if write(path, txt2):
        # 回读验证
        back = read(path)
        ok = back is not None and new in back
        print(f"  {'✅' if ok else '❌'} {path}: 已修改（回读验证{'通过' if ok else '失败'}）")
    else:
        print(f"  ❌ {path}: PUT 失败")
