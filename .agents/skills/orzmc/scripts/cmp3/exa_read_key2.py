#!/usr/bin/env python3
"""Exaroton：下载 key.pem 原始字节并显示大小/魔数"""
import urllib.request, json, os, base64

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/floodgate/key.pem/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
try:
    raw = urllib.request.urlopen(req, timeout=30).read()
    print("原始字节数:", len(raw))
    print("前 50 字节 hex:", raw[:50].hex())
    # 尝试解析 JSON 包装
    try:
        d = json.loads(raw)
        if isinstance(d, dict) and "text" in d:
            t = d["text"]
            print("JSON text 类型:", type(t), "长度:", len(t) if isinstance(t, str) else "?")
            if isinstance(t, str):
                print("text 前 60:", repr(t[:60]))
    except Exception as e:
        print("非 JSON 包装:", str(e)[:50])
except Exception as e:
    print("读取失败:", str(e)[:100])
