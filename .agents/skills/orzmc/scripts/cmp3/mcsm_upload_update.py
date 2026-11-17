#!/usr/bin/env python3
"""MCSM：上传插件 jar 到 plugins/update/（Paper 热更新目录）
用法: python3 mcsm_upload_update.py [jar1.jar jar2.jar ...]
  不带参数则上传本地 ~/minecraft-server/plugins/ 下与 MCSM 版本不同的插件
凭据: 从 ~/.hermes/.env 读取（MCSM_API_KEY / MCSM_DAEMON_ID / MCSM_INSTANCE_ID / MCSM_URL）
"""
import urllib.request, json, urllib.parse, os, time, hashlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

cfg = get_mcsm_config()
MCSM_HOST = cfg["url"].split("//")[1].split(":")[0]  # 从 URL 提取主机名
LOCAL_DIR = os.path.expanduser("~/minecraft-server/plugins")

# 默认上传列表：可自定义（如 5 个落后插件）
DEFAULT_FILES = ["deathchest.jar", "GriefPrevention.jar", "OrzMC-1.0.13-pr.153.394.jar",
                 "worldguard-bukkit-7.0.18.jar", "Geyser-Spigot.jar"]

FILES = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

for fname in FILES:
    local_path = os.path.join(LOCAL_DIR, fname)
    if not os.path.exists(local_path):
        print(f"  ❌ 本地文件不存在: {fname}")
        continue
    jar_data = open(local_path, "rb").read()
    print(f"上传 {fname} ({len(jar_data)//1024}KB, sha256={hashlib.sha256(jar_data).hexdigest()[:12]})...")

    # 获取上传凭证（plugins/update 目录）
    d = mcsm_api_post(cfg, "api/files/upload",
                      {"upload_dir": "/plugins/update", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
    if not d or d.get("status") != 200:
        print(f"  ❌ 凭证失败: {json.dumps(d, ensure_ascii=False)[:100]}")
        continue
    addr = d["data"]["addr"].replace("localhost", MCSM_HOST)
    url = f"http://{addr}/upload/{d['data']['password']}"

    # multipart 上传
    boundary = "----hb-" + str(int(time.time()))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode()
    body += b"Content-Type: application/java-archive\r\n\r\n"
    body += jar_data
    body += f"\r\n--{boundary}--\r\n".encode()

    try:
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = r.read().decode("utf-8", errors="replace")
        print(f"  ✅ 上传响应: {resp[:80]}")
    except Exception as e:
        print(f"  ❌ 上传失败: {e}")
    time.sleep(3)
