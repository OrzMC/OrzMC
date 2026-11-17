#!/usr/bin/env python3
"""MCSM：用 0 字节空文件覆盖占位 jar（测试 Paper 是否忽略空文件不报错）"""
import sys, os, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

cfg = get_mcsm_config()
HOST = cfg["url"].split("//")[1].split(":")[0]

# 0 字节空文件
content = b""

for fname in ["floodgate.jar", "DeathChest.jar"]:
    print(f"覆盖 {fname} (0B) -> plugins/")
    d = mcsm_api_post(cfg, "api/files/upload",
                      {"upload_dir": "/plugins", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
    if not d or d.get("status") != 200:
        print(f"  ❌ 凭证失败: {str(d)[:80]}")
        continue
    addr = d["data"]["addr"].replace("localhost", HOST)
    url = f"http://{addr}/upload/{d['data']['password']}"
    boundary = "----hb-" + str(int(time.time()))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += content
    body += f"\r\n--{boundary}--\r\n".encode()
    try:
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"  ✅ 上传响应: {r.read().decode()[:60]}")
    except Exception as e:
        print(f"  ❌ 上传失败: {e}")
    time.sleep(2)
