#!/usr/bin/env python3
"""Exaroton：下载 Geyser-Spigot.jar 并算 sha256（对比本地）"""
import urllib.request, json, os, hashlib

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot.jar/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=120).read()
print("Exaroton Geyser jar:", len(raw), "B, sha256:", hashlib.sha256(raw).hexdigest()[:16])

import os
local = os.path.expanduser("~/minecraft-server/plugins/Geyser-Spigot.jar")
lraw = open(local, "rb").read()
print("本地 Geyser jar:", len(lraw), "B, sha256:", hashlib.sha256(lraw).hexdigest()[:16])
print("相同:", hashlib.sha256(raw).hexdigest() == hashlib.sha256(lraw).hexdigest())
