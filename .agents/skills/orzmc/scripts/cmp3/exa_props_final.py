#!/usr/bin/env python3
"""Exaroton：server.properties 原始响应全文（不解析，直接找 online-mode）"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/server.properties/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()

# raw 是纯文本还是 JSON？
stripped = raw.lstrip()
print("首字符:", repr(stripped[0]))
if stripped.startswith("{"):
    print(">>> 是 JSON 包装")
    d = json.loads(raw)
    text = d.get("text", "")
    print("text 字段前 100:", repr(text[:100]))
    # text 可能是转义属性（\n 分隔）
    if "\\n" in text:
        for part in text.split("\\n"):
            if "online-mode" in part or "enforce-secure" in part:
                print("  text 内:", part)
    else:
        for line in text.splitlines():
            if "online-mode" in line or "enforce-secure" in line:
                print("  text 内:", line)
else:
    print(">>> 是纯文本文件")
    for line in raw.splitlines():
        if "online-mode" in line or "enforce-secure" in line:
            print("  文件内:", line)
