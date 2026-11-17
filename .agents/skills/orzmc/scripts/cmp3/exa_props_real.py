#!/usr/bin/env python3
"""Exaroton：server.properties 真实文件内容（去 JSON 包装）"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/server.properties/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()

# 尝试解析 JSON 并取 text
try:
    d = json.loads(raw)
    text = d.get("text", raw)
    print("[JSON 解析成功，text 字段长度]", len(text))
except Exception as e:
    text = raw
    print("[非 JSON]", e)

print("=== text 字段内 online-mode 行 ===")
for line in text.splitlines():
    if "online-mode" in line or "enforce-secure" in line:
        print(" ", line.strip())

print("=== 原始响应前 200 字符 ===")
print(raw[:200])
