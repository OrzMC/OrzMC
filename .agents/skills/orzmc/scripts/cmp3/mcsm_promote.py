#!/usr/bin/env python3
"""MCSM：批量插件推广（删旧 OrzMC + 传新 jar 到 update/plugins/）
用法: python3 mcsm_promote.py
"""
import sys, os, time, hashlib, json, urllib.request, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
MCSM_HOST = cfg["url"].split("//")[1].split(":")[0]
PLUGINS = os.path.expanduser("~/minecraft-server/plugins")


def get_upload_addr(upload_dir):
    d = mcsm_api_post(cfg, "api/files/upload",
                      {"upload_dir": upload_dir, "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
    if not d or d.get("status") != 200:
        print(f"  ❌ 凭证失败: {json.dumps(d, ensure_ascii=False)[:100]}")
        return None
    addr = d["data"]["addr"].replace("localhost", MCSM_HOST)
    return f"http://{addr}/upload/{d['data']['password']}"


def upload(fname, upload_dir):
    local_path = os.path.join(PLUGINS, fname)
    if not os.path.exists(local_path):
        print(f"  ❌ 本地文件不存在: {fname}")
        return
    jar = open(local_path, "rb").read()
    print(f"上传 {fname} ({len(jar)//1024}KB, sha256={hashlib.sha256(jar).hexdigest()[:12]}) -> {upload_dir}/ ...")
    url = get_upload_addr(upload_dir)
    if not url:
        return
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


from mcsm_env import mcsm_api_post

# 1. 删旧 OrzMC 1.0.13（防新旧并存）
print("① 删除旧 OrzMC-1.0.13-pr.153.394.jar（plugins/）")
d = mcsm_api_post(cfg, "api/files/delete",
                  {"file_name": "/plugins/OrzMC-1.0.13-pr.153.394.jar", "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
print(f"   {'✅ ' + str(d)[:80] if d else '❌ 删除失败'}")

# 2. 传 OrzMC 1.0.14-dev.237 到 update/
upload("OrzMC-1.0.14-dev.237.jar", "/plugins/update")

# 3. 传 floodgate 到 plugins/（新装）
upload("floodgate.jar", "/plugins")
