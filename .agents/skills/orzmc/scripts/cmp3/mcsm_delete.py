#!/usr/bin/env python3
"""MCSM 通用删除脚本（DELETE /api/files/ 实测可用 2026-08-06）

用法:
  python3 mcsm_delete.py /plugins/floodgate.jar /plugins/floodgate /plugins/DeathChest.jar
  python3 mcsm_delete.py --dry-run /plugins/xxx.jar    # 只打印不执行

说明: 旧方案"上传 0B/占位覆盖"已废弃（MCSM 实际支持 DELETE）。
  实测 DELETE /api/files/?daemonId={d}&uuid={i} body {"targets":[...]} → 200。
  删后会自动真实 GET 验证（daemon 偶发假 200）。
"""
import sys, os, json, time, urllib.request, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

DRY_RUN = "--dry-run" in sys.argv
paths = [a for a in sys.argv[1:] if not a.startswith("--")]
if not paths:
    print("用法: python3 mcsm_delete.py [--dry-run] /路径1 /路径2 ...")
    sys.exit(1)

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def api_del(targets):
    url = f"{BASE}/api/files/?{urllib.parse.urlencode({'apikey': KEY, 'daemonId': DID, 'uuid': IID})}"
    req = urllib.request.Request(url, method="DELETE",
                                 data=json.dumps({"targets": targets}).encode())
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()[:300])
    except Exception as e:
        return -1, str(e)[:150]

print("=== MCSM 删除 ===")
if DRY_RUN:
    print("DRY-RUN 模式，仅预览：")
    for p in paths:
        print(f"  🗑️ 将删除: {p}")
    sys.exit(0)

# 删除前存在性检查（真实 GET 下载：None=不存在）
for p in paths:
    exists = mcsm_download(cfg, p) is not None
    print(f"  {'✅' if exists else '❌'} {p}: {'存在' if exists else '不存在'}")

st, resp = api_del(paths)
print(f"\nDELETE /api/files/ → {st} | {json.dumps(resp, ensure_ascii=False)[:100]}")

# 删后验证（真实 GET 下载）
time.sleep(2)
print("\n=== 删后验证 ===")
ok = True
for p in paths:
    still = mcsm_download(cfg, p) is not None
    print(f"  {'⚠️ 仍在!' if still else '✅ 已删除'} {p}")
    if still:
        ok = False
print("\n结果:", "✅ 全部删除成功" if ok else "❌ 有残留（daemon 假 200，需重试或面板手动删）")
