#!/usr/bin/env python3
"""解析 PaperMC 官网下载页，提取最新 STABLE 构建的下载信息。

新 API 机制（2026-08 实测）：
- api.papermc.io/v2 已完全废弃（sunset）
- 下载页内嵌 React flight JSON，包含每个构建的 sha256
- 下载直链: https://fill-data.papermc.io/v1/objects/{sha256}/{jar名}

用法:
  python3 parse_papermc.py [paper|folia]  # 最新 STABLE 构建（默认 paper）
  python3 parse_papermc.py --all      # 列出所有版本的最新构建
输出（默认）: <jar文件名> <sha256>
（下载直链: https://fill-data.papermc.io/v1/objects/{sha256}/{jar名}）
"""
import re, sys, urllib.request

PROJECT = "paper"
for arg in sys.argv[1:]:
    if arg in ("paper", "folia"):
        PROJECT = arg
        break

PAGE_URL = f"https://papermc.io/downloads/{PROJECT}"

def fetch_page():
    req = urllib.request.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract_json(html):
    """从页面内嵌 JSON 中提取 builds 数组。"""
    # 页面用 HTML 实体编码（&quot;），先还原
    html = html.replace("&quot;", '"').replace("\\u003d", "=").replace("\\u0026", "&")
    matches = []
    # 匹配 name + sha256 组合（React flight 序列化格式）
    for fm in re.finditer(r'"name":\[0,"(' + PROJECT + r'-[^"]+\.jar)"\].*?"sha256":\[0,"([a-f0-9]{64})"\]', html):
        matches.append((fm.group(1), fm.group(2)))
    return matches

def main():
    try:
        html = fetch_page()
    except Exception as e:
        print(f"ERROR: 无法获取页面: {e}", file=sys.stderr)
        sys.exit(1)

    builds = extract_json(html)
    if not builds:
        print("ERROR: 未能从页面解析出构建信息（页面结构可能已变化）", file=sys.stderr)
        sys.exit(1)

    # 去重（内嵌数据会重复出现）
    seen = {}
    for name, sha in builds:
        m = re.match(rf"{PROJECT}-(\d+\.\d+)-(\d+)\.jar", name)
        if m:
            ver, bid = m.group(1), int(m.group(2))
            seen.setdefault(ver, []).append((bid, name, sha))

    if "--all" in sys.argv:
        for ver in sorted(seen):
            for bid, name, sha in sorted(seen[ver], reverse=True)[:3]:
                print(f"{name} {sha}")
        return

    # 默认最新版本的最高构建
    latest_ver = sorted(seen)[-1]
    top = sorted(seen[latest_ver], reverse=True)[0]
    print(f"{top[1]} {top[2]}")
    print(f"VERSION={latest_ver} BUILD={top[0]}", file=sys.stderr)

if __name__ == "__main__":
    main()
