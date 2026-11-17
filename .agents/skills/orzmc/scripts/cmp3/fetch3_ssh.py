#!/usr/bin/env python3
"""MCSM 配置 SSH 直读（兜底通道，2026-11-02）

背景：面板 files API 的「签发 + 拉流」在慢响应/大文件时会 502/截断（2026-11-02 实测 59/59 全 502），
导致配置审查降级甚至假阴性。SSH 直读 Windows 实例目录是当前最可靠、最快的通道。

产出布局与 fetch3_configs.fetch_mcsm 完全一致：
  /tmp/mcsm_configs2/{server.properties,bukkit.yml,...,config_paper-global.yml, plugins/<插件>/<文件>}

用法：
  python3 fetch3_ssh.py            # 拉全量（核心 + 插件配置）
  python3 fetch3_ssh.py --check    # 只自检通道可用性（打印文件数）
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from mcsm_env import get_mcsm_local_config, mcsm_scan_plugin_configs_cached
except Exception as e:  # pragma: no cover
    print("mcsm_env 加载失败：%s" % e)
    raise

OUT = "/tmp/mcsm_configs2"
RAW = "/tmp/mcsm_ssh_raw"
SSH = "win"
WIN_TMP = "E:/orzmc/tmp"
PAPER_UUID = "716c2fb712154c36ba5ab0f1480d3f87"
INST_DIR = "E:/orzmc/mcsmanager/daemon/data/InstanceData/" + PAPER_UUID

CORE = ["server.properties", "bukkit.yml", "spigot.yml", "commands.yml", "wepif.yml"]
CORE_MAP = {"config/paper-global.yml": "config_paper-global.yml",
            "config/paper-world-defaults.yml": "config_paper-world-defaults.yml"}


def run(cmd, timeout=180):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    check_only = "--check" in sys.argv
    print("=== MCSM 配置 SSH 直读 ===")
    cfg = get_mcsm_local_config()
    files = mcsm_scan_plugin_configs_cached(cfg)
    print("清单（面板扫描）: %d 个插件配置文件" % len(files))

    src = list(CORE_MAP.keys()) + CORE + ["plugins/" + f for f in files]
    # 去重并过滤明显不存在的（bsdtar 遇缺失会报错但继续）
    src = sorted(set(src))
    print("待拉取: %d 个路径" % len(src))
    if check_only:
        rc, out = run(["ssh", "-o", "ConnectTimeout=8", SSH, "echo ok"])
        print("SSH 通道:", "OK" if rc == 0 else "FAIL " + out[:80])
        return 0 if rc == 0 else 1

    rc, out = run(["ssh", "-o", "ConnectTimeout=8", SSH,
                   "powershell -NoProfile -Command \"New-Item -ItemType Directory -Force -Path %s | Out-Null\"" % WIN_TMP],
                  timeout=60)
    if rc != 0:
        print("建临时目录失败:", out[:100])
        return 1

    # 用清单文件避免命令行过长
    listfile = "/tmp/mcsm_ssh_list.txt"
    with open(listfile, "w", encoding="utf-8") as f:
        f.write("\n".join(src) + "\n")
    rc, out = run(["scp", "-o", "ConnectTimeout=10", listfile, "%s:%s/cfg_list.txt" % (SSH, WIN_TMP)], timeout=90)
    if rc != 0:
        print("上传清单失败:", out[:100])
        return 1

    remote_tar = "%s/cfg.tar" % WIN_TMP
    ps1 = "/tmp/_mcsm_pack.ps1"
    ps1_body = "\n".join([
        "$ErrorActionPreference = 'Continue'",
        "Set-Location '%s'" % INST_DIR,
        "if (Test-Path '%s') { Remove-Item '%s' -Force }" % (remote_tar, remote_tar),
        "& tar -cf '%s' -T '%s/cfg_list.txt' 2>$null" % (remote_tar, WIN_TMP),
        "if (Test-Path '%s') { Write-Output ('TAR_OK ' + (Get-Item '%s').Length) } else { Write-Output 'TAR_FAIL' }"
        % (remote_tar, remote_tar),
        "",
    ])
    open(ps1, "w", encoding="utf-8").write(ps1_body)
    run(["scp", "-o", "ConnectTimeout=10", ps1, "%s:%s/_mcsm_pack.ps1" % (SSH, WIN_TMP)], timeout=90)
    rc, out = run(["ssh", "-o", "ConnectTimeout=10", SSH,
                   "powershell -NoProfile -ExecutionPolicy Bypass -File %s/_mcsm_pack.ps1" % WIN_TMP], timeout=300)
    if "TAR_OK" not in out:
        print("Windows 打包失败:", out.strip()[:200])
        return 1
    print("Windows 打包: %s" % out.strip().splitlines()[-1][:60])

    if os.path.isdir(RAW):
        shutil.rmtree(RAW)
    os.makedirs(RAW, exist_ok=True)
    local_tar = "/tmp/mcsm_ssh_cfg.tar"
    rc, out = run(["scp", "-o", "ConnectTimeout=10", "%s:%s" % (SSH, remote_tar), local_tar], timeout=300)
    if rc != 0:
        print("下载 tar 失败:", out[:120])
        return 1
    rc, out = run(["tar", "-xf", local_tar, "-C", RAW], timeout=180)
    if rc != 0:
        print("解包失败:", out[:120])
        return 1

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "plugins"), exist_ok=True)
    n = 0
    # 核心：平铺名映射
    for cloud, flat in CORE_MAP.items():
        s = os.path.join(RAW, cloud)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(OUT, flat))
            n += 1
    for f in CORE:
        s = os.path.join(RAW, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(OUT, f))
            n += 1
    # 插件：保留目录结构
    praw = os.path.join(RAW, "plugins")
    if os.path.isdir(praw):
        for rel in files:
            s = os.path.join(praw, rel)
            if os.path.isfile(s):
                d = os.path.join(OUT, "plugins", rel)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                n += 1
    print("落地: %d 个配置文件 → %s" % (n, OUT))
    # 清理远端临时文件
    run(["ssh", "-o", "ConnectTimeout=8", SSH,
         "cmd /c \"del /q %s\\cfg.tar %s\\cfg_list.txt 2>nul & echo cleaned\""
         % (WIN_TMP.replace("/", "\\"), WIN_TMP.replace("/", "\\"))], timeout=60)
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
