#!/usr/bin/env python3
"""MCSM：上传新装插件到 plugins/（floodgate 等）
用法: python3 mcsm_upload_plugins.py floodgate.jar [其他.jar ...]
"""
import sys, os, time, hashlib, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

cfg = get_mcsm_config()
HOST = cfg["url"].split("//")[1].split(":")[0]
PLUGINS = os.path.expanduser("~/minecraft-server/plugins")

FILES = sys.argv[1:] if len(sys.argv) > 1 else ["floodgate.jar"]

for fname in FILES:
    local_path = os.path.join(PLUGINS, fname)
    if not os.path.exists(local_path):
        print(f"  ❌ 本地文件不存在: {fname}")
        continue
    jar = open(local_path, "rb").read()
    print(f"上传 {fname} ({len(jar)//1024}KB, sha256={hashlib.sha256(jar).hexdigest()[:12]}) -> plugins/ ...")

    d = mcsm_api_post(cfg, "api/files/upload",
                      {"upload_dir": "/plugins", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
    if not d or d.get("status") != 200:
        print(f"  ❌ 凭证失败: {str(d)[:100]}")
        continue
    addr = d["data"]["addr"].replace("localhost", HOST)
    url = f"http://{addr}/upload/{d['data']['password']}"

    boundary = "----hb-" + str(int(time.time()))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
    body += b"Content-Type: application/java-archive\r\n\r\n"
    body += jar
    body += f"\r\n--{boundary}--\r\n".encode()

    try:
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=300) as r:
            print(f"  ✅ 上传响应: {r.read().decode()[:60]}")
    except Exception as e:
        print(f"  ❌ 上传失败: {e}")
    time.sleep(3)
