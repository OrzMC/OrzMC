#!/usr/bin/env python3
"""两端配置拉取 v4（2026-09-09 迁移后：本地端退役，MCSM = Windows {SERVER_NAME} 栈）
清单 = MCSM 实例 API 递归扫描（真源，非本地目录）；Exaroton + MCSM 拉同名配置。
结构: <dir>/server.properties, <dir>/bukkit.yml, ..., <dir>/config_paper-global.yml (核心平铺)
      <dir>/plugins/<插件目录>/<相对路径> (插件配置保留目录结构)
"""
import sys, os, json, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mcsm_env import (get_mcsm_local_config, get_exaroton_config,
                      mcsm_scan_plugin_configs_cached, mcsm_sign, mcsm_fetch_stream)
from exa_file import get_file as exa_get  # GET 自动解包 JSON/裸文本

EXA_OUT = "/tmp/exa_configs2"
MCSM_OUT = "/tmp/mcsm_configs2"          # MCSM({SERVER_NAME}, Windows 栈) = 基准端（2026-09-09 起）
CORE = ["server.properties", "bukkit.yml", "spigot.yml", "commands.yml", "wepif.yml"]
CORE_MAP = {  # 云上路径 → 本地平铺名
    "config/paper-global.yml": "config_paper-global.yml",
    "config/paper-world-defaults.yml": "config_paper-world-defaults.yml",
}

# ---------- Exaroton ----------
def exa_cfg():
    e = get_exaroton_config()
    return e["api_key"], e["server_id"]

def fetch_exa(files):
    api_key, sid = exa_cfg()
    os.makedirs(f"{EXA_OUT}/plugins", exist_ok=True)
    print("=== Exaroton 配置拉取 ===")
    ok = fail = 0
    for path, local in CORE_MAP.items():
        try:
            content = exa_get(path, api_key, sid)
            open(f"{EXA_OUT}/{local}", "w").write(content)
            print(f"  ✅ {path} ({len(content)}B)"); ok += 1
        except Exception as e:
            print(f"  ⚠️  {path}: {str(e)[:50]}"); fail += 1
        time.sleep(1)
    for f in CORE:
        try:
            content = exa_get(f, api_key, sid)
            open(f"{EXA_OUT}/{f}", "w").write(content)
            print(f"  ✅ {f} ({len(content)}B)"); ok += 1
        except Exception as e:
            print(f"  ⚠️  {f}: {str(e)[:50]}"); fail += 1
        time.sleep(1)
    def dl(rel):
        try:
            content = exa_get(f"plugins/{rel}", api_key, sid)
            dst = f"{EXA_OUT}/plugins/{rel}"
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "w").write(content)
            return (rel, "ok", len(content))
        except Exception as e:
            return (rel, "err", str(e)[:40])
    with ThreadPoolExecutor(max_workers=4) as ex:
        for rel, st, info in ex.map(dl, files):
            if st == "ok":
                ok += 1
            else:
                fail += 1
                print(f"  ⚠️  plugins/{rel}: {info}")
    print(f"Exaroton 完成: ok={ok} fail={fail} → {EXA_OUT}\n")

# ---------- MCSM（{SERVER_NAME} Windows 栈，2026-09-09 起 = 巡检 MCSM 端）----------
def fetch_mcsm(files, cfg=None, out_dir=None, label="MCSM({SERVER_NAME})"):
    """MCSM 配置拉取（串行 + 退避规避面板限流）"""
    if cfg is None:
        cfg = get_mcsm_local_config()
    if out_dir is None:
        out_dir = MCSM_OUT
    if os.path.exists(out_dir):
        import shutil; shutil.rmtree(out_dir)
    os.makedirs(f"{out_dir}/plugins", exist_ok=True)
    print(f"=== {label} 配置拉取 ===")
    # 统一任务清单: (MCSM 源路径, 落盘相对路径)
    tasks = [(f"/{path}", local) for path, local in CORE_MAP.items()]
    tasks += [(f"/{f}", f) for f in CORE]
    tasks += [(f"/plugins/{rel}", f"plugins/{rel}") for rel in files]
    ok = fail = 0
    failed = []
    # ⚠️ 两阶段模型（2026-09-09 老板源码级实证）：
    #   阶段1 签发凭据 = 面板硬编码限流 speedLimit(3)（普通用户同账号 3s 窗口 1 次，500「冷却中」）→ 串行 + 冷却等待
    #   阶段2 文件流 = 无并发限制（多 password 并行实测 200）→ 可安全并发拉流
    print("  阶段1/2: 串行签发凭据（限流 3s/次）→ 并行拉流")
    creds = []
    for task in tasks:
        src, dst = task
        cred = mcsm_sign(cfg, src)
        if cred:
            creds.append((src, dst, cred))
        else:
            fail += 1
            failed.append(src)
            print(f"  ⚠️  {src}: 签发失败（限流重试耗尽）")
        time.sleep(3.1)  # speedLimit 3s 窗口：每次签发后等待

    def pull(item):
        src, dst, cred = item
        data = mcsm_fetch_stream(cfg, cred, src.split("/")[-1])
        if data is not None and data[:2] != b"PK":
            return src, dst, True, data
        return src, dst, False, None

    with ThreadPoolExecutor(max_workers=10) as ex:
        for src, dst, ok_f, data in ex.map(pull, creds):
            if ok_f:
                full = f"{out_dir}/{dst}"
                os.makedirs(os.path.dirname(full), exist_ok=True)
                open(full, "wb").write(data)
                ok += 1
            else:
                fail += 1
                failed.append(src)
                print(f"  ⚠️  {src}: 拉流失败")
    print(f"{label} 完成: ok={ok} fail={fail} → {out_dir} (签发串行+拉流并行×10)")
    if failed:
        print(f"失败清单({len(failed)}): {', '.join(failed)}")

def fetch_all():
    """两端：Exaroton(API) + MCSM({SERVER_NAME} API)。清单 = MCSM 端 API 扫描（带缓存）"""
    files = mcsm_scan_plugin_configs_cached(get_mcsm_local_config())
    print(f"配置清单: {len(files)} 个插件配置文件\n")
    print("并发: Exaroton + MCSM({SERVER_NAME})\n")
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(fetch_exa, files)
        f2 = ex.submit(fetch_mcsm, files)
        f1.result()
        f2.result()
    print("=== 两端全部完成 ===\n")
    return files

if __name__ == "__main__":
    fetch_all()
