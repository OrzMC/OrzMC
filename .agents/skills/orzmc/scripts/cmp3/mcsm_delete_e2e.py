#!/usr/bin/env python3
"""MCSM 新删除脚本端到端测试：上传测试文件 → mcsm_delete.py 删除 → 验证"""
import sys, os, time, urllib.request, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post, mcsm_download

cfg = get_mcsm_config()
HOST = cfg["url"].split("//")[1].split(":")[0]
HERE = os.path.dirname(os.path.abspath(__file__))

# 1. 上传测试文件
content = b"delete test\n"
d = mcsm_api_post(cfg, "api/files/upload",
                  {"upload_dir": "/plugins", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
if not d or d.get("status") != 200:
    print("❌ 凭证失败")
    sys.exit(1)
addr = d["data"]["addr"].replace("localhost", HOST)
url = f"http://{addr}/upload/{d['data']['password']}"
boundary = "----hb-" + str(int(time.time()))
body = b""
body += f"--{boundary}\r\n".encode()
body += b'Content-Disposition: form-data; name="file"; filename="api_probe_del2.txt"\r\n'
body += b"Content-Type: application/octet-stream\r\n\r\n"
body += content
body += f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
with urllib.request.urlopen(req, timeout=60) as r:
    print("1. 上传测试文件:", r.status)

time.sleep(2)
# 2. 确认存在
data = mcsm_download(cfg, "/plugins/api_probe_del2.txt")
print("2. 上传确认:", f"✅ {len(data)}B" if data else "❌ 未找到")

# 3. 用新删除脚本删除
print("3. 调用 mcsm_delete.py ...")
r = subprocess.run([sys.executable, os.path.join(HERE, "mcsm_delete.py"), "/plugins/api_probe_del2.txt"],
                   capture_output=True, text=True, timeout=120)
print(r.stdout[-500:])
if r.returncode != 0:
    print("stderr:", r.stderr[-200:])
