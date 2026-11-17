#!/usr/bin/env python3
"""Exaroton：Geyser auth-type 改为 offline"""
import urllib.request, json, os, re

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
BASE = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot/config.yml/"

def api(method="GET", data=None, ctype=None):
    req = urllib.request.Request(BASE, headers={"Authorization": "Bearer " + key, "User-Agent": "Mozilla/5.0"}, method=method)
    if data is not None:
        if ctype:
            req.add_header("Content-Type", ctype)
        req.data = data
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

raw = api().decode("utf-8", errors="replace")
try:
    text = json.loads(raw).get("text", raw)
except Exception:
    text = raw

new_text, n = re.subn(r"^(\s*)auth-type: (offline|online|floodgate)", r"\1auth-type: offline", text, flags=re.M)
print(f"替换 {n} 处 -> offline")

resp = api("PUT", json.dumps({"text": new_text}).encode(), "application/json")
print("PUT:", resp.decode()[:80])
