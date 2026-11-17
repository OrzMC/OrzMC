#!/usr/bin/env python3
"""MCSM：删除指定插件文件（DELETE /api/files/delete，body {"targets":[...]}）
用法: python3 mcsm_delete_file.py /plugins/OrzMC-1.0.13-pr.153.394.jar
"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
path = sys.argv[1] if len(sys.argv) > 1 else "/plugins/OrzMC-1.0.13-pr.153.394.jar"
print(f"删除 {path} ...")
url = cfg["url"] + "/api/files/delete?" + urllib.parse.urlencode(
    {"apikey": cfg["apikey"], "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
req = urllib.request.Request(url, data=json.dumps({"targets": [path]}).encode(), method="DELETE")
req.add_header("Content-Type", "application/json; charset=utf-8")
req.add_header("X-Requested-With", "XMLHttpRequest")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("响应:", r.read().decode()[:200])
except Exception as e:
    print("❌ 请求失败:", e)

