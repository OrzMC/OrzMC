#!/usr/bin/env python3
"""MCSM 批量改配置文件模板（PUT /api/files/ 写回）
用法: 复制到 scripts/cmp3/ 同目录（依赖 mcsm_env.py），修改 apply_file 列表后运行
方法: 读原文件 → 精确替换 → PUT 写回（保留原行尾）→ 重启生效
已验证: 2026-08-03 批量改 7 配置文件 + Start.bat（JVM 内存 4G→8G）全部成功
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

def mcsm_read(path):
    data = mcsm_download(cfg, f"/{path}")
    if data is None or data[:2] == b"PK":
        return None
    return data.decode("utf-8", errors="replace")

def mcsm_write(path, content):
    """PUT /api/files/ body {"target": path, "text": content}
    ⚠️ 三要点：① 必须带 daemonId+uuid（只带 apikey → 403）
    ② 只能写已存在的文件（新文件路径 → 500 Illegal access path）
    ③ body 字段是 text（用 content 返回 200 但不生效）"""
    import urllib.request, urllib.parse
    params = {"apikey": cfg["apikey"], "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]}
    url = cfg["url"] + "api/files/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="PUT",
        data=json.dumps({"target": f"/{path}", "text": content}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
            return d.get("status") == 200
    except Exception as e:
        print(f"  ❌ 写入异常: {e}")
        return False

def apply_file(path, replacements, desc):
    """replacements: [(old, new, tag), ...]"""
    content = mcsm_read(path)
    if content is None:
        print(f"❌ {path}: 读取失败")
        return
    print(f"\n📄 {path}")
    for old, new, tag in replacements:
        if old not in content:
            print(f"  ⚠️ {tag}: 未找到 {old!r}")
            continue
        content = content.replace(old, new, 1)
        print(f"  ✅ {tag}: {old!r} → {new!r}")
    if mcsm_write(path, content):
        print(f"  ✅ {path} 写入成功（需重启生效）")
    else:
        print(f"  ❌ {path} 写入失败")
    time.sleep(3)  # 避免触发面板冷却

if __name__ == "__main__":
    # ===== 在此编辑你的修改列表 =====
    apply_file("server.properties", [
        ("max-tick-time=600000", "max-tick-time=60000", "示例"),
    ], "示例")
    # ===== 编辑结束 =====
    print("\n=== 完成 ===")
