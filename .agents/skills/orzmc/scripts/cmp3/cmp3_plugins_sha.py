#!/usr/bin/env python3
"""三端插件 jar sha256 对比（本地 vs Exaroton vs MCSM）
用法: python3 cmp3_plugins_sha.py [jar1.jar ...]
  不带参数则对比本地 ~/minecraft-server/plugins/ 全部插件
凭据: 从 ~/.hermes/.env 读取
"""
import urllib.request, json, os, hashlib, urllib.parse, time, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, get_exaroton_config, mcsm_api_post

ecfg = get_exaroton_config()
mcfg = get_mcsm_config()
EXA_BASE = "https://api.exaroton.com/v1"
UA = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {ecfg['api_key']}"}
MCSM_HOST = mcfg["url"].split("//")[1].split(":")[0]

LOCAL_DIR = os.path.expanduser("~/minecraft-server/plugins")

def sha256(data):
    return hashlib.sha256(data).hexdigest()[:16]

def exa_download(fname):
    req = urllib.request.Request(f"{EXA_BASE}/servers/{ecfg['server_id']}/files/data/plugins/{fname}/", headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def mcsm_download(fname):
    d = mcsm_api_post(mcfg, "api/files/download",
                      {"file_name": f"/plugins/{fname}", "daemonId": mcfg["daemon_id"], "uuid": mcfg["instance_id"]})
    if not d or d.get("status") != 200:
        return None
    addr = d["data"]["addr"].replace("localhost", MCSM_HOST)
    fn = urllib.parse.quote(fname)
    url = f"http://{addr}/download/{d['data']['password']}/{fn}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except Exception:
        return None

# 默认对比全部本地插件
if len(sys.argv) > 1:
    PLUGINS = sys.argv[1:]
else:
    PLUGINS = sorted(os.listdir(LOCAL_DIR))
    PLUGINS = [f for f in PLUGINS if f.endswith(".jar")]

print(f"{'插件':<45} {'本地':<18} {'Exaroton':<18} {'MCSM':<18} 一致?")
print("-" * 105)
diff_count = 0
for fname in PLUGINS:
    local_path = os.path.join(LOCAL_DIR, fname)
    local_sha = sha256(open(local_path, "rb").read()) if os.path.exists(local_path) else "缺失"
    try:
        exa_sha = sha256(exa_download(fname))
    except Exception:
        exa_sha = "下载失败"
    try:
        mcsm_sha = sha256(mcsm_download(fname))
    except Exception:
        mcsm_sha = "下载失败"
    same = "✅" if local_sha == exa_sha == mcsm_sha else "❌"
    if same == "❌":
        diff_count += 1
    print(f"{fname:<45} {local_sha:<18} {exa_sha:<18} {mcsm_sha:<18} {same}")
    sys.stdout.flush()
    time.sleep(2)  # Cloudflare 风控

print(f"\n共 {len(PLUGINS)} 个插件，{diff_count} 个不一致")
