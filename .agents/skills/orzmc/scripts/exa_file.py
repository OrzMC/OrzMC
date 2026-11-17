#!/usr/bin/env python3
"""Exaroton 配置文件读写共享模块（2026-08-10 修复 JSON 包装污染）

⚠️ 铁律（2026-08-09/10 实测）：
- **PUT files/data/{path}/ 必须发裸文本/裸字节**（Content-Type text/plain 或 octet-stream）
- **严禁 JSON 包装 `{"text": ...}`** —— 会被原样存为文件内容，插件 YAML 解析静默回退默认值，
  配置文件尾残留 `{"text"="..."}` 垃圾块（Exaroton server.properties 已中招，见三端差异审计）
- GET files/data/{path}/ 可能返回裸文本或 JSON 包装（`{"text":"..."}`，两种都实测过）
  → 统一 try json.loads + 检查 text 键解包
"""
import urllib.request, json, os, time

def _load_env():
    """读 Hermes .env；跨平台（2026-11-16 迁移 Windows 后修复 FileNotFoundError）

    顺序：%LOCALAPPDATA%\\hermes\\.env（Windows）→ ~/.hermes/.env（Mac）。
    都不存在时返回空 dict（**不再抛异常**——调用方若已显式传 api_key/sid 就不该因为找不到 .env 而失败）。
    """
    import pathlib
    cands = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(pathlib.Path(la) / "hermes" / ".env")
    cands.append(pathlib.Path.home() / ".hermes" / ".env")
    env = {}
    for p in cands:
        if p.is_file():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    for k, v in env.items():
        os.environ.setdefault(k, v)
    return env

def get_exa_config():
    env = _load_env()
    return {
        "api_key": env.get("EXAROTON_API_KEY", ""),
        "server_id": env.get("EXAROTON_SERVER_ID", "{API_TOKEN}"),
    }

def exa_headers(api_key):
    return {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {api_key}"}

def get_file(path, api_key=None, sid=None):
    """GET 文件内容，兼容裸文本 / JSON 包装（解包 text 字段）"""
    cfg = get_exa_config()
    api_key = api_key or cfg["api_key"]
    sid = sid or cfg["server_id"]
    url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/{path}/"
    req = urllib.request.Request(url, headers=exa_headers(api_key))
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    try:
        d = json.loads(raw)
        if isinstance(d, dict) and "text" in d:
            return d["text"]
    except Exception:
        pass
    return raw

def put_file(path, content, api_key=None, sid=None, ctype="text/plain"):
    """PUT 文件内容 —— **必须裸文本**（禁 JSON 包装）"""
    cfg = get_exa_config()
    api_key = api_key or cfg["api_key"]
    sid = sid or cfg["server_id"]
    if isinstance(content, str):
        content = content.encode("utf-8")
    url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/{path}/"
    req = urllib.request.Request(url, data=content, method="PUT")
    for k, v in exa_headers(api_key).items():
        req.add_header(k, v)
    req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode("utf-8", errors="replace")

if __name__ == "__main__":
    # 自检：读回 server.properties 验证无 JSON 残留
    cfg = get_exa_config()
    print(f"EXAROTON_KEY={'已设置' if cfg['api_key'] else '缺失!'} SID={cfg['server_id']}")
    txt = get_file("server.properties")
    marker = '{"text"'
    print(f"server.properties: {len(txt)}B, JSON残留={marker in txt}")
