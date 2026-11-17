#!/usr/bin/env python3
"""MCSM：验证 plugins/update/ 文件已正确上传（真实 GET 读回 sha256 对比本地）
用法: python3 mcsm_verify_update.py [jar1.jar ...]
  不带参数则验证默认 5 个插件
"""
import urllib.request, json, urllib.parse, os, time, hashlib, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post, mcsm_download

cfg = get_mcsm_config()
LOCAL_DIR = os.path.expanduser("~/minecraft-server/plugins")
DEFAULT_FILES = ["deathchest.jar", "GriefPrevention.jar", "OrzMC-1.0.13-pr.153.394.jar",
                 "worldguard-bukkit-7.0.18.jar", "Geyser-Spigot.jar"]
FILES = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

print("=== 验证 plugins/update/ 文件 ===")
all_ok = True
for fname in FILES:
    data = mcsm_download(cfg, f"/plugins/update/{fname}")
    local_path = os.path.join(LOCAL_DIR, fname)
    if not os.path.exists(local_path):
        print(f"  ❌ 本地缺失: {fname}")
        all_ok = False
        continue
    local_sha = hashlib.sha256(open(local_path, "rb").read()).hexdigest()
    if data and data[:2] == b"PK":
        remote_sha = hashlib.sha256(data).hexdigest()
        ok = remote_sha == local_sha
        if not ok:
            all_ok = False
        print(f"  {fname}: {'✅ 完整一致' if ok else '❌ sha 不同'} ({len(data)}B)")
    else:
        all_ok = False
        print(f"  {fname}: ❌ 读取失败或非 jar")
    sys.stdout.flush()
    time.sleep(3)
print(f"\n{'✅ 全部验证通过' if all_ok else '❌ 有文件异常'}")
