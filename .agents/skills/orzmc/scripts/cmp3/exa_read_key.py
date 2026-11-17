#!/usr/bin/env python3
"""Exaroton：读取 floodgate key.pem 内容"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/floodgate/key.pem/"
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
    print("key.pem 内容:", repr(text[:200]))
except Exception as e:
    print("读取失败:", str(e)[:100])
