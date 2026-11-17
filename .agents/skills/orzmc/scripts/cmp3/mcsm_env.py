#!/usr/bin/env python3
"""MCSM 凭据加载（统一入口，从 ~/.hermes/.env 读取，禁止硬编码）
用法: from mcsm_env import get_mcsm_config, get_exaroton_config
"""
import os

ENV_FILE = os.path.expanduser("~/.hermes/.env")

def _load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE):
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def get_mcsm_config():
    """返回 MCSM 连接配置字典（远程 Win11 面板）"""
    env = _load_env()
    return {
        "url": env.get("MCSM_URL", "http://{SERVER_HOST}:23333/"),
        "apikey": env.get("MCSM_API_KEY", ""),
        "daemon_id": env.get("MCSM_DAEMON_ID", ""),
        "instance_id": env.get("MCSM_INSTANCE_ID", ""),
    }

def get_mcsm_local_config():
    """本机 MCSM 栈（mcs.{SERVER_NAME}.cn，本地测试服双实例；2026-09-03 迁移后成为三端审查「本地端」）"""
    env = _load_env()
    return {
        "url": env.get("MCSM_LOCAL_URL", "https://mcs.{SERVER_NAME}.cn/"),
        "apikey": env.get("MCSM_LOCAL_API_KEY", ""),
        "daemon_id": env.get("MCSM_LOCAL_DAEMON_ID", ""),
        "instance_id": env.get("MCSM_LOCAL_INSTANCE_ID", ""),
    }

def get_exaroton_config():
    """返回 Exaroton 连接配置字典"""
    env = _load_env()
    return {
        "api_key": env.get("EXAROTON_API_KEY", ""),
        "server_id": env.get("EXAROTON_SERVER_ID", "{API_TOKEN}"),
    }

def mcsm_api_post(cfg, path, params, retries=3, timeout=20):
    """MCSM API POST 请求（带重试，含限流 status 感知）"""
    import urllib.request, urllib.parse, json, time
    url = cfg["url"] + path + "?" + urllib.parse.urlencode({**params, "apikey": cfg["apikey"]})
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=b"{}", method="POST")
            req.add_header("Content-Type", "application/json; charset=utf-8")
            req.add_header("X-Requested-With", "XMLHttpRequest")
            req.add_header("User-Agent", "Mozilla/5.0")  # {SERVER_NAME} 面板中间件拦 Python UA（2026-09-09 实测）
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
                # 面板限流/错误也重试（500/429）
                if isinstance(d, dict) and d.get("status") in (200, None):
                    return d
        except Exception:
            pass
        if i < retries - 1:
            time.sleep(3)
    return None

def _daemon_host(cfg, addr):
    """从下载凭据 addr 解析 daemon 主机名（兼容 localhost:24444 / wss://host:443 / http(s)://host:port）"""
    import re
    m = re.match(r"^(?:wss?://)?([^/:]+)(?::\d+)?$", addr)
    host = m.group(1) if m else addr
    if host == "localhost":
        host = cfg["url"].split("//")[1].split(":")[0]
    return host

def mcsm_sign(cfg, path, retries=8):
    """签发一次性下载凭据（两步法第 1 步），返回 {password, addr} 或 None。
    ⚠️ 面板硬编码限流 speedLimit(3)：普通用户同账号 3s 窗口仅放行 1 次，超发 500「冷却中」
       （管理员绕过；2026-09-09 老板源码级实证）。故本函数串行 + 冷却退避 3.5s。
    """
    import time
    for i in range(retries):
        d = mcsm_api_post(cfg, "api/files/download",
                          {"file_name": path, "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]})
        if d and d.get("status") == 200 and d.get("data", {}).get("password"):
            data = d["data"]
            return {"password": data["password"], "addr": data.get("addr", "")}
        time.sleep(3.5)  # 限流冷却
    return None

def mcsm_fetch_stream(cfg, cred, fname, retries=3):
    """凭签发 password 直连 daemon 拉流（两步法第 2 步）。
    ⚠️ 文件流本身无并发限制（老板实测多 password 并行 200）——可安全并发调用。
    返回 bytes 或 None。
    """
    import urllib.request, urllib.parse, time
    host = _daemon_host(cfg, cred.get("addr", ""))
    fn = urllib.parse.quote(fname)
    url = f"https://{host}/download/{cred['password']}/{fn}"
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i < retries - 1:
                time.sleep(2)
    return None

def mcsm_download(cfg, path, retries=4):
    """单文件完整下载（两步：签发 + 拉流）——单文件/无并发场景使用。
    批量并发场景请用 fetch3 的两阶段模型（串行签发 + 并行拉流）。
    """
    cred = mcsm_sign(cfg, path)
    if not cred:
        return None
    return mcsm_fetch_stream(cfg, cred, path.split("/")[-1])

def mcsm_list(cfg, target, file_name="", page=0, page_size=100):
    """MCSM 列目录（REST GET /api/files/list），返回 [(name, type), ...]
    type: 0=目录 1=文件；file_name 是过滤词（空=列全部，新面板已无需过滤词）
    内置重试：list 偶发 500/断连（面板限流或 Remote end closed），退避重试 3 次
    """
    import urllib.request, urllib.parse, json, time
    params = {"file_name": file_name, "daemonId": cfg["daemon_id"],
              "uuid": cfg["instance_id"], "target": target,
              "page": page, "page_size": page_size, "apikey": cfg["apikey"]}
    url = cfg["url"] + "api/files/list?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0"})  # 面板中间件拦 Python UA
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode())
            if d.get("status") != 200:
                time.sleep(1.5 * (attempt + 1))
                continue
            data = d.get("data") or {}
            items = data.get("items") or data.get("data") or []
            # 兼容两种字段形态（list: {items:[...]} 实测；个别版本 {data:[...]})
            if isinstance(items, dict):
                items = items.get("items") or items.get("data") or []
            out = []
            for it in items:
                if isinstance(it, dict):
                    out.append((it.get("name") or it.get("fileName") or "", int(it.get("type", 1))))
            return out
        except Exception:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    return []

def mcsm_scan_plugin_configs(cfg, skip_dirs=None, skip_files=None, max_depth=4):
    """递归扫描 MCSM 实例 plugins/ 下全部配置文件相对路径（相对 plugins/）
    替代迁移前「本地目录直读扫描」——数据源 = 巡检目标端本身（2026-09-09 两端模型）
    """
    SKIP_DIRS = skip_dirs or {"userdata", "homes", "data", "players", "backups",
                              "logs", "cache", "worlds", "messages"}
    SKIP_FILES = skip_files or {"ops.json", "whitelist.json", "banned-players.json",
                                "banned-ips.json", "usercache.json", "permissions.yml", "help.yml"}
    out = []

    def walk(rel_dir, depth):
        if depth > max_depth:
            return
        items = mcsm_list(cfg, f"/plugins/{rel_dir}".rstrip("/") or "/plugins")
        for name, typ in items:
            if typ == 0:  # 目录
                if name in SKIP_DIRS:
                    continue
                walk(f"{rel_dir}/{name}" if rel_dir else name, depth + 1)
            else:  # 文件
                if name.endswith((".yml", ".yaml")) and name not in SKIP_FILES:
                    out.append(f"{rel_dir}/{name}" if rel_dir else name)
    walk("", 1)
    return sorted(out)

import json as _json, os as _os, time as _time
_MANIFEST = "/tmp/mcsm_cfg_manifest.json"

def mcsm_scan_plugin_configs_cached(cfg, max_age=7 * 86400):
    """scan 带缓存：files/list 账号限流（~3s/次），全量递归 ~70 请求 ≈ 3.5min；
    缓存命中时仅 1 次顶层 list 校验（插件目录名未变 = 清单仍准）→ scan 开销 ~3s。
    校验失败/缓存过期/顶层变化 → 全量重扫并刷新缓存。
    """
    top_names = []
    try:
        top = mcsm_list(cfg, "/plugins")
        top_names = sorted(n for n, _t in top if n)
    except Exception:
        top_names = []
    if top_names and _os.path.exists(_MANIFEST):
        try:
            m = _json.load(open(_MANIFEST))
            if m.get("top") == top_names and _time.time() - m.get("ts", 0) < max_age:
                print(f"配置清单缓存命中: {len(m['files'])} 个（顶层目录一致）")
                return m["files"]
        except Exception:
            pass
    files = mcsm_scan_plugin_configs(cfg)
    try:
        _json.dump({"ts": _time.time(), "top": top_names, "files": files},
                   open(_MANIFEST, "w"))
        print(f"配置清单已扫描并缓存: {len(files)} 个")
    except Exception:
        print(f"配置清单已扫描: {len(files)} 个（缓存写入失败）")
    return files

if __name__ == "__main__":
    c = get_mcsm_config()
    print(f"MCSM_URL={c['url']} API_KEY={'已设置' if c['apikey'] else '缺失!'} "
          f"DAEMON={c['daemon_id'][:8]}... INSTANCE={c['instance_id'][:8]}...")
    e = get_exaroton_config()
    print(f"EXAROTON_KEY={'已设置' if e['api_key'] else '缺失!'} SID={e['server_id']}")
