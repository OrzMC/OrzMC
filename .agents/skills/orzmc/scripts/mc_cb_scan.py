#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft 命令方块全量扫描与报告生成工具（纯标准库，零依赖，可移植）。

用法:
    mc_cb_scan.py scan   --world <地图目录> --out <csv文件> [--dims overworld,the_end,the_nether] [--jobs N]
    mc_cb_scan.py report --csv <csv文件>    --out <md文件>  [--cluster-threshold 256] [--max-coord 1000000]
    mc_cb_scan.py run    --world <地图目录> --out-dir <目录> [--jobs N]

原理:
    - 直接解析维度下的 region(.mca) 文件头，逐个读取存在的区块
    - 用自定义流式 NBT 解析器只提取区块根节点的 block_entities 列表，
      跳过体积庞大的区块体(Sections)数据，从而大幅提速
    - 输出: ① 全量 CSV(坐标/类型/完整指令/触发方式等)
            ② 自动生成的 Markdown 梳理报告(统计/集群/指令分类/异常/迁移要点)
"""
import argparse, csv, gzip, os, re, sys, time, zlib
from collections import Counter

VERSION = "1.0.0"
CB_IDS = ("command_block", "chain_command_block", "repeating_command_block")

# ---------------------------------------------------------------------------
# 一、NBT / region 文件读取（纯标准库）
# ---------------------------------------------------------------------------

def _read_str(data, pos):
    ln = int.from_bytes(data[pos:pos + 2], 'big')
    return data[pos + 2:pos + 2 + ln].decode('utf-8', 'replace'), pos + 2 + ln


def _skip_payload(data, pos, t):
    """跳过某个标签的负载（名字已被消费）。t 为标签类型。"""
    if t == 1: return pos + 1
    if t == 2: return pos + 2
    if t == 3: return pos + 4
    if t == 4: return pos + 8
    if t == 5: return pos + 4
    if t == 6: return pos + 8
    if t == 7:
        n = int.from_bytes(data[pos:pos + 4], 'big'); return pos + 4 + n
    if t == 8:
        ln = int.from_bytes(data[pos:pos + 2], 'big'); return pos + 2 + ln
    if t == 9:
        et = data[pos]; n = int.from_bytes(data[pos + 1:pos + 5], 'big'); pos += 5
        for _ in range(n):
            pos = _skip_payload(data, pos, et)
        return pos
    if t == 10:
        return _skip_compound(data, pos)
    if t == 11:
        n = int.from_bytes(data[pos:pos + 4], 'big'); return pos + 4 + 4 * n
    if t == 12:
        n = int.from_bytes(data[pos:pos + 4], 'big'); return pos + 4 + 8 * n
    raise ValueError("unknown tag type %d" % t)


def _skip_compound(data, pos):
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return pos
        _, pos = _read_str(data, pos)
        pos = _skip_payload(data, pos, t)


def _parse_list_of_compounds(data, pos):
    et = data[pos]; n = int.from_bytes(data[pos + 1:pos + 5], 'big'); pos += 5
    out = []
    if et != 10:
        for _ in range(n):
            pos = _skip_payload(data, pos, et)
        return out, pos
    for _ in range(n):
        d, pos = _parse_compound(data, pos)
        out.append(d)
    return out, pos


def _parse_compound(data, pos):
    d = {}
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return d, pos
        name, pos = _read_str(data, pos)
        if t == 1: v = data[pos]; pos += 1
        elif t == 2: v = int.from_bytes(data[pos:pos + 2], 'big', signed=True); pos += 2
        elif t == 3: v = int.from_bytes(data[pos:pos + 4], 'big', signed=True); pos += 4
        elif t == 4: v = int.from_bytes(data[pos:pos + 8], 'big', signed=True); pos += 8
        elif t == 5: v = None; pos += 4
        elif t == 6: v = None; pos += 8
        elif t == 7:
            nn = int.from_bytes(data[pos:pos + 4], 'big'); v = data[pos + 4:pos + 4 + nn]; pos += 4 + nn
        elif t == 8:
            ln = int.from_bytes(data[pos:pos + 2], 'big'); v = data[pos + 2:pos + 2 + ln].decode('utf-8', 'replace'); pos += 2 + ln
        elif t == 9:
            v, pos = _parse_list_of_compounds(data, pos)
        elif t == 10:
            v, pos = _parse_compound(data, pos)
        elif t == 11:
            nn = int.from_bytes(data[pos:pos + 4], 'big'); pos += 4 + 4 * nn; v = None
        elif t == 12:
            nn = int.from_bytes(data[pos:pos + 4], 'big'); pos += 4 + 8 * nn; v = None
        else:
            raise ValueError("unknown tag type %d" % t)
        d[name] = v
    return d, pos


def extract_block_entities(data):
    """从解压后的区块 NBT 根字节中提取 block_entities 列表。"""
    pos = 0
    if data[pos] != 10:
        return []
    pos += 1
    _, pos = _read_str(data, pos)
    while True:
        t = data[pos]; pos += 1
        if t == 0:
            return []
        name, pos = _read_str(data, pos)
        if name == "block_entities" and t == 9:
            lst, _ = _parse_list_of_compounds(data, pos)
            return lst
        pos = _skip_payload(data, pos, t)


def read_chunk_raw(path, off_sector):
    """从 region 文件读取并解压单个区块。"""
    with open(path, 'rb') as f:
        f.seek(off_sector * 4096)
        head = f.read(5)
        if len(head) < 5:
            return None
        length = int.from_bytes(head[0:4], 'big')
        ctype = head[4]
        payload = f.read(length - 1)
    if ctype == 1:
        return gzip.decompress(payload)
    if ctype == 2:
        return zlib.decompress(payload)
    if ctype == 3:
        return payload
    return None


# ---------------------------------------------------------------------------
# 二、扫描
# ---------------------------------------------------------------------------

CSV_HEADER = ["dimension", "region_file", "x", "y", "z", "type_id", "Command",
              "auto", "ConditionalMode", "CustomName", "powered",
              "TrackOutput", "successCount", "LastOutput"]

# Folia 迁移相关：被禁用/不支持的指令集合（与 scripts/analyze_cmdblocks.py 保持一致）
DISABLED_CMDS = {'bossbar', 'clone', 'data', 'datapack', 'debug', 'function', 'item', 'loot',
    'reload', 'return', 'ride', 'rotate', 'schedule', 'scoreboard', 'spectate', 'spreadplayers',
    'tag', 'team', 'teammsg', 'tick', 'trigger', 'perf', 'save-all', 'saveall', 'restart'}


def find_region_dirs(world):
    dirs = []
    base = os.path.join(world, "dimensions", "minecraft")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            reg = os.path.join(base, d, "region")
            if os.path.isdir(reg):
                dirs.append((d, reg))
    legacy = os.path.join(world, "region")
    if os.path.isdir(legacy):
        dirs.append(("overworld", legacy))
    return dirs


def _clean_customname(v):
    if not v:
        return ""
    s = str(v)
    m = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', s)
    return m.group(1) if m else s


def scan_region_file(dim, path):
    """扫描单个 region 文件，返回命令方块行字典列表。"""
    rows = []
    with open(path, 'rb') as f:
        loc = f.read(4096)
    for i in range(1024):
        b = loc[i * 4:i * 4 + 4]
        off = int.from_bytes(b[0:3], 'big')
        if off == 0:
            continue
        raw = read_chunk_raw(path, off)
        if raw is None:
            continue
        for be in extract_block_entities(raw):
            bid = str(be.get("id", ""))
            base = bid.split(":")[-1]
            if base in CB_IDS:
                rows.append({
                    "dimension": dim,
                    "region_file": os.path.basename(path),
                    "x": be.get("x", ""), "y": be.get("y", ""), "z": be.get("z", ""),
                    "type_id": base,
                    "Command": str(be.get("Command", "")),
                    "auto": be.get("auto", ""),
                    "ConditionalMode": be.get("conditionMet", ""),
                    "CustomName": _clean_customname(be.get("CustomName")),
                    "powered": be.get("powered", ""),
                    "TrackOutput": be.get("TrackOutput", ""),
                    "successCount": be.get("SuccessCount", ""),
                    "LastOutput": str(be.get("LastOutput", "")),
                })
    return rows


def scan_world(world, dims=None, jobs=1, progress_every=300, log=print):
    region_dirs = find_region_dirs(world)
    if dims:
        keep = set(x.strip() for x in dims.split(",") if x.strip())
        region_dirs = [(d, r) for d, r in region_dirs if d in keep]
    if not region_dirs:
        raise SystemExit("未找到任何维度 region 目录: %s" % world)
    log("维度: " + ", ".join(d for d, _ in region_dirs))

    tasks = []  # (dim, filepath)
    for dim, regdir in region_dirs:
        for fn in sorted(f for f in os.listdir(regdir) if f.endswith(".mca")):
            tasks.append((dim, os.path.join(regdir, fn)))

    t0 = time.time()
    total_rows = []
    if jobs > 1 and len(tasks) > 1:
        import multiprocessing as mp
        with mp.Pool(jobs) as pool:
            # 分批提交以便输出进度
            for n, res in enumerate(pool.imap_unordered(_worker, tasks, chunksize=20), 1):
                total_rows.extend(res)
                if n % progress_every == 0:
                    log("[scan] %d/%d region | %d CB | %.0fs"
                        % (n, len(tasks), len(total_rows), time.time() - t0))
    else:
        for n, (dim, path) in enumerate(tasks, 1):
            total_rows.extend(scan_region_file(dim, path))
            if n % progress_every == 0:
                log("[scan] %d/%d region | %d CB | %.0fs"
                    % (n, len(tasks), len(total_rows), time.time() - t0))
    log("扫描完成: %d region, %d 个命令方块, %.0fs" % (len(tasks), len(total_rows), time.time() - t0))
    return total_rows


def _worker(task):
    dim, path = task
    return scan_region_file(dim, path)


def write_csv(rows, out):
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# 三、分析与报告
# ---------------------------------------------------------------------------

def _cat(cmd):
    c = cmd.strip()
    if not c:
        return "(空命令)"
    if c.startswith("/"):
        c = c[1:]
    if c.startswith("minecraft:"):
        c = c.split(":", 1)[1]
    return c.split()[0]


def _dist(a, b):
    return max(abs(a[i] - b[i]) for i in range(3))


def analyze(rows, cluster_threshold=256, max_coord=1000000):
    stats = {
        "total": len(rows),
        "dim": Counter(r["dimension"] for r in rows),
        "types": Counter(r["type_id"] for r in rows),
        "auto": Counter(str(r["auto"]) for r in rows),
        "condition": Counter(str(r["ConditionalMode"]) for r in rows),
        "powered": Counter(str(r["powered"]) for r in rows),
        "named": sum(1 for r in rows if str(r["CustomName"]).strip()),
        "selectors": Counter(),
        "area_selectors": 0,
        "categories": Counter(),
        "disabled_use": Counter(),   # 命中 Folia 禁用指令的命令
        "clusters": [],
        "anomalies": [],
        "outliers": [],
    }
    # 选择器
    for r in rows:
        c = r["Command"]
        for tok in ("@a", "@e", "@p", "@s", "@r", "@n", "@initiator", "@c"):
            if tok in c:
                stats["selectors"][tok] += 1
        cl = c.lower()
        if "dx=" in cl or "distance=" in cl:
            stats["area_selectors"] += 1
        fw = _cat(c)
        stats["categories"][fw] += 1
        if fw in DISABLED_CMDS:
            stats["disabled_use"][fw] += 1

    # 异常: /op 提权
    for r in rows:
        if re.match(r"^\s*/?\s*op\b", r["Command"]):
            stats["anomalies"].append(("OP提权", (r["x"], r["y"], r["z"]), r["Command"][:60]))
    # 异常: 超大坐标 (损坏/残留)
    for r in rows:
        try:
            x, z = int(r["x"]), int(r["z"])
        except (ValueError, TypeError):
            continue
        if abs(x) > max_coord or abs(z) > max_coord:
            stats["outliers"].append((r["dimension"], r["region_file"], r["x"], r["y"], r["z"]))
    # 异常: 超大跨度 fill
    for r in rows:
        m = re.search(r"\bfill\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", r["Command"])
        if m:
            x1, y1, z1, x2, y2, z2 = (int(m.group(i)) for i in range(1, 7))
            span = max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))
            if span > 200:
                stats["anomalies"].append(("超大fill(跨度%d)" % span, (r["x"], r["y"], r["z"]), r["Command"][:70]))

    # 空间聚类（剔除超大坐标异常点）
    ow = [r for r in rows if r["dimension"] == "overworld"]
    sane = [r for r in ow if (lambda p: abs(p) <= max_coord)(int(r["x"])) and abs(int(r["z"])) <= max_coord]
    clusters = []
    for r in sane:
        p = (int(r["x"]), int(r["y"]), int(r["z"]))
        placed = False
        for cl in clusters:
            if _dist(cl["ref"], p) <= cluster_threshold:
                cl["rows"].append(r)
                cl["ref"] = p
                placed = True
                break
        if not placed:
            clusters.append({"ref": p, "rows": [r]})
    clusters.sort(key=lambda x: -len(x["rows"]))
    for cl in clusters:
        rs = cl["rows"]
        cl["bbox"] = (min(int(r["x"]) for r in rs), max(int(r["x"]) for r in rs),
                      min(int(r["y"]) for r in rs), max(int(r["y"]) for r in rs),
                      min(int(r["z"]) for r in rs), max(int(r["z"]) for r in rs))
        cl["cmds"] = Counter(_cat(r["Command"]) for r in rs)
    stats["clusters"] = clusters
    return stats


def render_report(stats, world="", csv_path="", cluster_threshold=256, max_coord=1000000):
    L = []
    a = L.append
    a("# Minecraft 命令方块全量梳理报告")
    a("")
    a("> 生成时间：%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    if world:
        a("> 扫描地图：`%s`" % world)
    if csv_path:
        a("> 原始数据：`%s`" % csv_path)
    a("> 由 `mc_cb_scan.py` 自动生成")

    a("")
    a("## 一、总体统计")
    a("")
    a("| 项目 | 数值 |")
    a("|---|---|")
    a("| **命令方块总数** | **%d** |" % stats["total"])
    a("| 按维度 | %s |" % ", ".join("%s:%d" % (k, v) for k, v in stats["dim"].most_common()))
    a("| 按类型 | %s |" % ", ".join("%s:%d" % (k, v) for k, v in stats["types"].most_common()))
    a("| auto(0=需红石,1=持续) | %s |" % ", ".join("`%s`:%d" % (k, v) for k, v in stats["auto"].most_common()))
    a("| 自定义命名 | %d |" % stats["named"])
    sel = ", ".join("`%s`:%d" % (k, v) for k, v in stats["selectors"].most_common())
    a("| 选择器使用 | %s |" % (sel or "无"))
    a("| 区域/距离选择器(dx=/distance=) | %d |" % stats["area_selectors"])

    a("")
    a("### 触发方式（auto）")
    a("")
    a("| auto | 数量 | 含义 |")
    a("|---|---|---|")
    a("| `0` | %d | 需红石信号触发 |" % stats["auto"].get("0", 0))
    a("| `1` | %d | 持续激活 |" % stats["auto"].get("1", 0))
    a("")
    a("> 条件模式说明：新版格式命令方块由区块方块状态控制是否条件执行，方块实体内的 `conditionMet` 为运行时状态而非配置项。")

    a("")
    a("## 二、地理位置与功能集群")
    a("")
    a("按空间聚类（阈值 %d 格），剔除超大坐标异常点后：" % cluster_threshold)
    a("")
    if stats["clusters"]:
        a("| # | 数量 | 中心坐标 | bbox (x/y/z) | 指令构成(Top) |")
        a("|---|---|---|---|---|")
        for i, cl in enumerate(stats["clusters"][:20], 1):
            bb = cl["bbox"]
            top = ", ".join("%s:%d" % (k, v) for k, v in cl["cmds"].most_common(6))
            a("| C%d | %d | (%d,%d,%d) | x[%d,%d] y[%d,%d] z[%d,%d] | %s |"
              % (i, len(cl["rows"]), cl["ref"][0], cl["ref"][1], cl["ref"][2],
                 bb[0], bb[1], bb[2], bb[3], bb[4], bb[5], top))
    else:
        a("（无有效命令方块集群）")

    a("")
    a("## 三、指令内容分类")
    a("")
    a("| 指令类型 | 数量 |")
    a("|---|---|")
    for k, v in stats["categories"].most_common():
        a("| `%s` | %d |" % (k, v))

    a("")
    a("## 四、数据异常与风险项")
    a("")
    if not stats["anomalies"] and not stats["outliers"]:
        a("未检测到异常。")
    if stats["anomalies"]:
        a("| 类型 | 位置 | 内容 |")
        a("|---|---|---|")
        for kind, pos, content in stats["anomalies"]:
            a("| %s | (%s,%s,%s) | `%s` |" % (kind, pos[0], pos[1], pos[2], content))
    if stats["outliers"]:
        a("")
        a("**超大坐标异常点（可能为损坏/残留数据，%d 个）**：坐标绝对值超过 %d 的命令方块，需核实是否误合入。" % (len(stats["outliers"]), max_coord))
        by = Counter(o[1] for o in stats["outliers"])
        for reg, n in by.most_common():
            a("- `%s`: %d 个" % (reg, n))

    a("")
    a("## 五、迁移评估要点（输入性）")
    a("")
    a("1. 命令方块全部为脉冲型、纯原版指令：Folia 对原版命令机制本身支持，无常驻循环需重写。")
    a("2. 重点关注 %d 条区域/距离选择器指令（dx=/distance=）：Folia 分区线程模型下跨区块实体扫描行为与 Paper 有差异，需逐个验证。" % stats["area_selectors"])
    a("3. `@e` 全实体扫描（%d 处）：Folia 下语义与开销需测试。" % stats["selectors"].get("@e", 0))
    a("4. 跨维度传送（`execute in ... run teleport`）：需在 Folia 下验证跨维度处理。")
    a("5. 被禁的插件指令不存储于命令方块，需结合服务端插件清单/报错日志定位。")
    a("6. 迁移前建议先处理第四节风险项（OP提权、异常坐标、超大fill）。")
    if stats["disabled_use"]:
        a("")
        a("### 命中 Folia 禁用指令集的命令方块（%d 个）" % sum(stats["disabled_use"].values()))
        a("")
        a("以下命令方块的首条指令落在 Folia 禁用/不支持指令集合内，需重点评估替换方案：")
        a("")
        a("| 禁用指令 | 出现次数 |")
        a("|---|---|")
        for k, v in stats["disabled_use"].most_common():
            a("| `%s` | %d |" % (k, v))
    a("")
    a("---")
    a("*生成命令：`mc_cb_scan.py`（纯标准库，详见同目录 README.md）*")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# 四、CLI
# ---------------------------------------------------------------------------

def cmd_scan(args):
    if not os.path.isdir(args.world):
        raise SystemExit("地图目录不存在: %s" % args.world)
    t0 = time.time()
    rows = scan_world(args.world, dims=args.dims, jobs=args.jobs, log=print)
    write_csv(rows, args.out)
    print("CSV 已写入: %s (%d 行, %.0fs)" % (args.out, len(rows), time.time() - t0))


def cmd_report(args):
    with open(args.csv, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    stats = analyze(rows, cluster_threshold=args.cluster_threshold, max_coord=args.max_coord)
    md = render_report(stats, csv_path=args.csv, cluster_threshold=args.cluster_threshold, max_coord=args.max_coord)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print("报告已写入: %s (%d 个命令方块)" % (args.out, stats["total"]))


def cmd_run(args):
    os.makedirs(args.out_dir, exist_ok=True)
    csv_path = os.path.join(args.out_dir, "command_blocks.csv")
    md_path = os.path.join(args.out_dir, "命令方块梳理报告.md")
    # 扫描
    rows = scan_world(args.world, dims=args.dims, jobs=args.jobs, log=print)
    write_csv(rows, csv_path)
    stats = analyze(rows, cluster_threshold=args.cluster_threshold, max_coord=args.max_coord)
    md = render_report(stats, world=args.world, csv_path=csv_path,
                       cluster_threshold=args.cluster_threshold, max_coord=args.max_coord)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("完成:")
    print("  CSV  : %s (%d 行)" % (csv_path, len(rows)))
    print("  报告 : %s" % md_path)


def build_parser():
    p = argparse.ArgumentParser(prog="mc_cb_scan", description="Minecraft 命令方块全量扫描与报告生成（纯标准库）")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="扫描地图 -> CSV")
    s.add_argument("--world", required=True, help="世界目录（含 dimensions/ 或 region/）")
    s.add_argument("--out", required=True, help="输出 CSV 路径")
    s.add_argument("--dims", help="限定维度，逗号分隔，如 overworld,the_end")
    s.add_argument("--jobs", type=int, default=1, help="并行进程数(默认1)")
    s.set_defaults(func=cmd_scan)

    r = sub.add_parser("report", help="CSV -> Markdown 报告")
    r.add_argument("--csv", required=True, help="输入 CSV")
    r.add_argument("--out", required=True, help="输出 MD 路径")
    r.add_argument("--cluster-threshold", type=int, default=256)
    r.add_argument("--max-coord", type=int, default=1000000)
    r.set_defaults(func=cmd_report)

    run = sub.add_parser("run", help="扫描+报告 一步完成")
    run.add_argument("--world", required=True)
    run.add_argument("--out-dir", required=True)
    run.add_argument("--dims")
    run.add_argument("--jobs", type=int, default=1)
    run.add_argument("--cluster-threshold", type=int, default=256)
    run.add_argument("--max-coord", type=int, default=1000000)
    run.set_defaults(func=cmd_run)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
