#!/usr/bin/env python3
"""MCSM：抓前端 JS 找文件管理真实 API 调用 + 验证 list 空是否路径问题"""
import sys, os, json, urllib.request, urllib.parse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return -1, str(e)[:150]

# 1. 抓面板首页 HTML，找 JS bundle 路径
st, html = get(f"{BASE}/")
print(f"面板首页: {st}, {len(html)}B")
js_refs = re.findall(r'src="([^"]+\.js[^"]*)"', html)[:5]
print("JS 引用:", js_refs)

# 2. 从 JS 里找 files/list 相关调用
for js in js_refs:
    url = js if js.startswith("http") else BASE + js
    st, js_content = get(url)
    if st == 200 and "files" in js_content:
        # 找 list 相关
        hits = re.findall(r'["\'](/api/files/[^"\']*)["\']', js_content)[:10]
        if hits:
            print(f"\n{js}: 找到端点 {hits}")
        # 找 page_size 相关参数名
        pg = re.findall(r'["\'](page_size|pageSize|page)["\']', js_content)[:5]
        if pg:
            print(f"  分页参数: {pg}")
