#!/usr/bin/env python3
"""Exaroton：读取 Geyser config.yml 全文（files/data GET）"""
import urllib.request, json, os, sys

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot/config.yml/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
try:
    raw = urllib.request.urlopen(req, timeout=30).read().decode()
    try:
        d = json.loads(raw)
        text = d.get("text", raw)
    except Exception:
        text = raw
    # 输出关键行
    for line in text.splitlines():
        ls = line.strip()
        if ls.startswith("auth-type") or ls.startswith("floodgate-key-file"):
            print("  ", ls)
    print("  [总行数]", len(text.splitlines()))
except Exception as e:
    print("读取失败:", str(e)[:100])
