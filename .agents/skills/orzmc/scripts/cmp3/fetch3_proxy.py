#!/usr/bin/env python3
"""代理侧配置拉取（2026-11-16，ADR-036「统一代理入口」后）

背景：测试服入口自 2026-11-12 起是 **orzmc-velocity**（Velocity + Geyser-Velocity + EaglerXServer）：
    两个 MCSM 实例不再发布 Java/基岩端口，实例内 Geyser-Spigot 被自动停用
    （日志 `Geyser is disabled due to Velocity`）→ **实例内那份 config.yml 是废纸**。
    配置审查若继续比对它，会每周报一堆假差异（transport/webrtc-port/advertise-addresses）。

做法：SSH 直读 Windows 宿主 `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml`
    （该目录 = 容器 bind mount `E:/orzmc/eagler/proxy -> /srv`），
    落到 `/tmp/mcsm_configs2/plugins/Geyser-Spigot/config.yml` —— **与 Exa 侧同名对齐**，
    这样 cmp3 的「同路径比对」直接就是「生效中的入口 Geyser 配置 vs Exa 入口 Geyser 配置」。

自动识别运行模式（两种模式互斥，不做人为切换）：
    proxy    代理侧配置文件存在 → 用它覆盖实例内副本，标记 .geyser_source=proxy
    direct   代理侧不存在（旧双实例直连）→ 保留实例内副本，标记 .geyser_source=instance

输出（供 orzmc_config_audit.sh 解析）：
    PROXY_MODE=proxy|direct|unknown
    GEYSER_SOURCE=<文件路径>
    GEYSER_BYTES=<字节数>

用法：
    python3 fetch3_proxy.py            # 拉取并落地（自动识别模式）
    python3 fetch3_proxy.py --check    # 只探测模式，不落地
    python3 fetch3_proxy.py --json     # 机器可读
退出码：0=正常（含 direct 回退）/ 1=异常（SSH 不可用等）
"""
import base64
import json
import os
import subprocess
import sys

OUT = "/tmp/mcsm_configs2"
SSH = "win"
# 代理容器 bind mount：E:/orzmc/eagler/proxy -> /srv（2026-11-16 实查 docker inspect）
PROXY_PLUGINS = "E:/orzmc/eagler/proxy/plugins"
PROXY_GEYSER_CFG = PROXY_PLUGINS + "/Geyser-Velocity/config.yml"
INSTANCE_TARGET = os.path.join(OUT, "plugins", "Geyser-Spigot", "config.yml")
SOURCE_MARK = os.path.join(OUT, ".geyser_source")


def run(cmd, timeout=90):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def ps(cmd):
    """经 ssh 跑一条简单 PowerShell（单层引号，避免三层嵌套）"""
    return run(["ssh", "-o", "ConnectTimeout=10", SSH,
                'powershell -NoProfile -Command "%s"' % cmd], timeout=120)


def remote_exists(path):
    rc, out = ps("if (Test-Path -LiteralPath '%s') { 'YES' } else { 'NO' }" % path)
    return rc == 0 and "YES" in out


def remote_read_b64(path):
    """base64 取文件字节：避开 Windows 控制台 GBK 编码把内容弄坏"""
    rc, out = ps("[Convert]::ToBase64String([IO.File]::ReadAllBytes('%s'))" % path)
    if rc != 0:
        raise IOError("ssh 读取失败: %s" % out.strip()[:120])
    b64 = "".join(out.split())
    if not b64:
        raise IOError("远端返回空内容")
    return base64.b64decode(b64)


def write_mark(value):
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(SOURCE_MARK, "w", encoding="utf-8") as f:
            f.write(value + "\n")
    except Exception:
        pass


def main():
    check_only = "--check" in sys.argv
    as_json = "--json" in sys.argv

    result = dict(mode="unknown", source=None, bytes=0, note="")
    rc, _ = run(["ssh", "-o", "ConnectTimeout=8", SSH, "echo ok"], timeout=30)
    if rc != 0:
        result["mode"] = "unknown"
        result["note"] = "SSH 通道不可用（win 主机）"
        if as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("PROXY_MODE=unknown")
            print("⚠️ %s" % result["note"])
        return 1

    if remote_exists(PROXY_GEYSER_CFG):
        result["mode"] = "proxy"
        result["source"] = PROXY_GEYSER_CFG
        if not check_only:
            try:
                data = remote_read_b64(PROXY_GEYSER_CFG)
            except Exception as e:
                result["mode"] = "unknown"
                result["note"] = str(e)[:120]
                if as_json:
                    print(json.dumps(result, ensure_ascii=False))
                else:
                    print("PROXY_MODE=unknown")
                return 1
            os.makedirs(os.path.dirname(INSTANCE_TARGET), exist_ok=True)
            with open(INSTANCE_TARGET, "wb") as f:
                f.write(data)
            write_mark("proxy")
            result["bytes"] = len(data)
            result["note"] = "入口 Geyser = 代理侧 Geyser-Velocity（实例内 Geyser-Spigot 已停用）"
    else:
        result["mode"] = "direct"
        result["source"] = INSTANCE_TARGET
        result["bytes"] = os.path.getsize(INSTANCE_TARGET) if os.path.isfile(INSTANCE_TARGET) else 0
        write_mark("instance")
        result["note"] = "代理侧配置不存在 → 按旧双实例直连模式，沿用实例内 Geyser-Spigot 副本"

    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("PROXY_MODE=%s" % result["mode"])
        print("GEYSER_SOURCE=%s" % result["source"])
        print("GEYSER_BYTES=%d" % result["bytes"])
        print("ℹ️  %s" % result["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
