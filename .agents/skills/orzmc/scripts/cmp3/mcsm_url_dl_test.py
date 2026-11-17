#!/usr/bin/env python3
"""MCSM download_from_url 实测：URL 直传到实例
源码: filemananger_router.ts POST /api/files/download_from_url
  body {url, file_name} + query {uuid, daemonId} → daemon file/download_from_url
注意: daemon 在 Windows 服务器上，外网 URL 可达性取决于那台机器
"""
import sys, os, json, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def api(path, params=None, method="GET", body=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode()[:300])
        except Exception:
            return e.code, {}
    except Exception as e:
        return -1, {"error": str(e)[:150]}

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

# 选一个小而稳的 URL——GitHub raw 一个已知文件（或本站资源）
# 用 GitHub raw 的 MCSManager README（小文件）
url = "https://raw.githubusercontent.com/MCSManager/Daemon/master/README.md"
fname = "/api_probe_url.md"

print(f"=== download_from_url 实测 ===")
print(f"  URL: {url}")
print(f"  保存: {fname}")
st, d = api("/api/files/download_from_url", P, "POST", {"url": url, "file_name": fname})
print(f"  调用: {st} | {json.dumps(d, ensure_ascii=False)[:150]}")

# 异步任务，等待下载完成
for i in range(6):
    time.sleep(5)
    data = mcsm_download(cfg, fname)
    if data:
        print(f"  ✅ 下载完成 ({i+1}*5s): {len(data)}B")
        print(f"  内容前80字符: {data[:80]!r}")
        break
    print(f"  等待中... ({i+1}*5s)")
else:
    print("  ❌ 30s 后仍未下载完成（URL 可能被墙或文件名路径问题）")

# 清理
st, d = api("/api/files/", P, "DELETE", {"targets": [fname]})
print(f"\n清理: {st}")
