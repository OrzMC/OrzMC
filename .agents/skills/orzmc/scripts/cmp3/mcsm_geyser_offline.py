#!/usr/bin/env python3
"""MCSM：Geyser auth-type 改为 offline（下载→改→上传覆盖）"""
import sys, os, time, hashlib, urllib.request, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download, mcsm_api_post

cfg = get_mcsm_config()
HOST = cfg["url"].split("//")[1].split(":")[0]

# 1. 下载当前 config
data = mcsm_download(cfg, "/plugins/Geyser-Spigot/config.yml")
if not data:
    print("❌ 下载失败")
    sys.exit(1)
text = data.decode("utf-8", errors="replace")
new_text, n = re.subn(r"^(\s*)auth-type: (offline|online|floodgate)", r"\1auth-type: offline", text, flags=re.M)
print(f"替换 {n} 处 -> offline")
if n == 0:
    for l in text.splitlines():
        if "auth-type" in l:
            print("当前:", l.strip())
    sys.exit(1)

# 2. 上传覆盖
content = new_text.encode("utf-8")
print(f"上传覆盖 config.yml ({len(content)}B, sha256={hashlib.sha256(content).hexdigest()[:12]})")
d = mcsm_api_post(cfg, "api/files/upload",
                  {"upload_dir": "/plugins/Geyser-Spigot", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
if not d or d.get("status") != 200:
    print(f"❌ 凭证失败: {str(d)[:100]}")
    sys.exit(1)
addr = d["data"]["addr"].replace("localhost", HOST)
url = f"http://{addr}/upload/{d['data']['password']}"
boundary = "----hb-" + str(int(time.time()))
body = b""
body += f"--{boundary}\r\n".encode()
body += f'Content-Disposition: form-data; name="file"; filename="config.yml"\r\n'.encode()
body += b"Content-Type: application/octet-stream\r\n\r\n"
body += content
body += f"\r\n--{boundary}--\r\n".encode()
try:
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as r:
        print(f"✅ 上传响应: {r.read().decode()[:80]}")
except Exception as e:
    print(f"❌ 上传失败: {e}")
