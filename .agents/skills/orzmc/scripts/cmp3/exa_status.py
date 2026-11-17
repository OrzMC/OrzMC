#!/usr/bin/env python3
"""Exaroton：服务器最终状态确认"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["data"]
status_map = {0: "OFFLINE", 1: "LOADING", 2: "STARTING", 3: "ONLINE", 4: "SAVING", 5: "STOPPING", 6: "RESTARTING", 7: "CRASHED"}
print("Exaroton:", status_map.get(d["status"]), "| 玩家:", d.get("players", {}).get("count", 0) if isinstance(d.get("players"), dict) else "?")
