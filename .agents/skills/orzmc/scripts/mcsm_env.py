"""mcsm_env —— Windows 本机适配器（2026-11-16 迁移落地）

背景：运维端从 Mac 迁到 Windows（测试服宿主）后，配置/版本巡检**不再需要面板 files API、
也不再需要 ssh win**：实例目录就在本机 `E:/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>`。
本模块用「本地文件系统」实现原来那套面板接口的最小集合，
让 `mc_version_check.py` / `orzmc_config_audit.py` 等脚本**不改调用方**即可跑。

对外 API（与旧面板版同名同语义）：
    get_mcsm_local_config() -> dict(instance_id=paper uuid, base=实例根, instance_map=...)
    get_mcsm_config()       -> 远端国内服面板配置（保留兼容，不常用）
    get_exaroton_config()   -> {'api_key','server_id'}（读 .env）
    mcsm_list(cfg, path)    -> [(name, typ)]  typ 1=文件 0=目录
    mcsm_scan_plugin_configs(_cached)(cfg) -> ['Geyser-Spigot/config.yml', ...]
    mcsm_download(cfg, path) -> bytes（本地直读）

⚠️ 与旧版差异：所有路径都是**本机路径**，不再有 3s 限流、502、签发失败这些坑。
"""
from __future__ import annotations
import sys
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
import os
import pathlib

DEFAULT_ROOT = "E:/orzmc/mcsmanager/daemon/data/InstanceData"
PAPER_UUID = "716c2fb712154c36ba5ab0f1480d3f87"
FOLIA_UUID = "8A932DD47F4D42AAAD6A6A9A5FAD2A91"


def _load_env() -> dict:
    """读 Hermes .env（Windows: %LOCALAPPDATA%\\hermes\\.env；兼容 Mac 路径）"""
    env = {}
    cands = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(pathlib.Path(la) / "hermes" / ".env")
    cands.append(pathlib.Path.home() / ".hermes" / ".env")
    for p in cands:
        if p.is_file():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    for k, v in env.items():
        os.environ.setdefault(k, v)
    return env


def get_mcsm_local_config() -> dict:
    """本机实例配置（本地直读版：instance_id 默认 = paper 实例）"""
    env = _load_env()
    root = env.get("ORZMC_INSTANCE_ROOT", DEFAULT_ROOT)
    return {
        "base": root,
        "instance_id": env.get("MCSM_LOCAL_INSTANCE_ID", PAPER_UUID),
        "instance_map": {
            "paper": env.get("MCSM_LOCAL_INSTANCE_ID", PAPER_UUID),
            "folia": env.get("ORZMC_FOLIA_UUID", FOLIA_UUID),
        },
        "mode": "local",
    }


def get_mcsm_config() -> dict:
    """国内服（远程 MCSM）配置——保留兼容；本机巡检不用它"""
    env = _load_env()
    return {
        "url": env.get("MCSM_URL", ""),
        "api_key": env.get("MCSM_API_KEY", ""),
        "daemon_id": env.get("MCSM_DAEMON_ID", ""),
        "instance_id": env.get("MCSM_INSTANCE_ID", ""),
    }


def get_exaroton_config() -> dict:
    env = _load_env()
    return {"api_key": env.get("EXAROTON_API_KEY", ""), "server_id": env.get("EXAROTON_SERVER_ID", "")}


# ---------------- 面板接口的本地等价实现 ----------------
def _inst_dir(cfg: dict) -> pathlib.Path:
    return pathlib.Path(cfg["base"]) / cfg["instance_id"]


def mcsm_list(cfg: dict, target: str, file_name: str = "", page: int = 0, page_size: int = 500):
    """列实例内目录 → [(name, typ)]（typ 1=文件 0=目录）"""
    rel = (target or "/").strip("/")
    p = _inst_dir(cfg) / rel if rel else _inst_dir(cfg)
    out = []
    if not p.is_dir():
        return out
    for entry in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        out.append((entry.name, 1 if entry.is_file() else 0))
    return out


SKIP_DIRS = {"userdata", "homes", "data", "players", "backups", "logs", "cache", "worlds", "messages"}
SKIP_FILES = {"ops.json", "whitelist.json", "banned-players.json", "banned-ips.json",
              "usercache.json", "permissions.yml", "help.yml"}


def mcsm_scan_plugin_configs(cfg: dict, skip_dirs=None, skip_files=None, max_depth=4):
    """递归扫描 plugins/ 下配置文件相对路径（相对 plugins/）——本地直读，秒级"""
    sk_dirs = skip_dirs or SKIP_DIRS
    sk_files = skip_files or SKIP_FILES
    base = _inst_dir(cfg) / "plugins"
    out = []
    if not base.is_dir():
        return out
    for p in base.rglob("*"):
        try:
            rel = p.relative_to(base)
        except ValueError:
            continue
        if len(rel.parts) - 1 > max_depth:
            continue
        if any(part in sk_dirs for part in rel.parts[:-1]):
            continue
        if p.is_file() and p.suffix.lower() in (".yml", ".yaml") and p.name not in sk_files:
            out.append(str(rel).replace(os.sep, "/"))
    return sorted(out)


def mcsm_scan_plugin_configs_cached(cfg: dict, max_age: int = 7 * 86400):
    """本地直读无需缓存，保持同名便于调用方复用"""
    return mcsm_scan_plugin_configs(cfg)


def mcsm_download(cfg: dict, path: str, retries: int = 1) -> bytes:
    """本地直读文件字节（等价旧面板 download）"""
    rel = path.strip("/")
    return (_inst_dir(cfg) / rel).read_bytes()


def mcsm_sign(*args, **kwargs):
    raise RuntimeError("本地适配器：不需要面板签发（mcsm_sign）")


def mcsm_fetch_stream(*args, **kwargs):
    raise RuntimeError("本地适配器：不需要面板拉流（mcsm_fetch_stream）")


def mcsm_api_post(*args, **kwargs):
    raise RuntimeError("本地适配器：不需要面板 API（mcsm_api_post）")


def cmd_status(uuid: str = "") -> dict:
    """实例是否在跑（本地：看 MCSM 容器是否存在）——供巡检脚本判活"""
    import subprocess
    short = (uuid or PAPER_UUID)[:8]
    name = "MCSM-" + short
    try:
        r = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", name],
                           capture_output=True, text=True, timeout=20)
        return {"container": name, "status": (r.stdout or "").strip() or "missing"}
    except Exception as e:
        return {"container": name, "status": "unknown", "error": str(e)[:80]}


if __name__ == "__main__":
    cfg = get_mcsm_local_config()
    print(json.dumps({"cfg": cfg, "plugins_cfg_count": len(mcsm_scan_plugin_configs(cfg)),
                      "status": cmd_status()}, ensure_ascii=False, indent=1))
