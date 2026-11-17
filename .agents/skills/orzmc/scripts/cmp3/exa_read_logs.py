#!/usr/bin/env python3
"""Exaroton：读取服务器日志尾部"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/logs/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
d = json.loads(raw)
data = d.get("data")
if isinstance(data, str):
    print(data[-800:])
elif isinstance(data, dict):
    print(json.dumps(data, ensure_ascii=False)[-800:])
else:
    print(str(data)[-800:])
