#!/usr/bin/env python3
"""
merge_worlds.py — 以 chunk 槽位粒度合并两个世界目录，恢复"全量最新"状态。

背景：OrzMCBackup 优化备份（--inhabited-time-seconds 阈值）会删除低活跃 chunk，
导致其 region 文件是"部分占用"的。把这类 region 同名覆盖到全量备份上会产生空洞。
本脚本以全量备份为底，把优化备份中存在的 chunk（较新数据）逐槽覆盖上去，
空槽用全量备份填充，entities/poi 与 region 锁步合并，从而不丢任何旧数据。

用法:
  python merge_worlds.py --base <full-old-world> --patch <optimized-new-world> --out <output>
可选:
  --force   允许覆盖已存在的输出目录
  --verify  合并完成后复核输出，报告槽位并集校验
"""
import argparse
import os
import shutil
import struct
import sys


class MCA:
    """只读 Anvil region 文件(.mca)。不解压 chunk，保持原始字节。"""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        if len(self.data) < 8192:
            raise ValueError(f"文件过小，不是有效的 .mca: {path}")
        loc = self.data[:4096]
        self.loc = []
        self.ts = []
        for i in range(1024):
            off = (loc[i * 4] << 16) | (loc[i * 4 + 1] << 8) | loc[i * 4 + 2]
            size = loc[i * 4 + 3]
            self.loc.append((off, size))
            self.ts.append(struct.unpack(">I", self.data[4096 + i * 4 : 4096 + i * 4 + 4])[0])

    def present(self, i):
        return self.loc[i][1] > 0

    def slot(self, i):
        """返回该槽位 chunk 的 (原始payload字节, 时间戳)，槽位为空/损坏返回 None。"""
        off, size = self.loc[i]
        if size == 0:
            return None
        start = off * 4096
        if start + 5 > len(self.data):
            return None
        ln = struct.unpack(">I", self.data[start : start + 4])[0]
        if ln <= 0 or start + 4 + ln > len(self.data):
            return None
        return self.data[start : start + 4 + ln], self.ts[i]


def write_mca(path, slots):
    """slots: [(槽位, payload字节, 时间戳)]，写出 sector 对齐的 .mca。全空则返回 False。"""
    if not slots:
        return False
    slots = sorted(slots, key=lambda s: s[0])
    loc = bytearray(4096)
    ts = bytearray(4096)
    body = bytearray()
    for slot, payload, timestamp in slots:
        abs_sector = 2 + (len(body) // 4096)  # 文件起始(含8KB头)的绝对扇区号
        size_sectors = (len(payload) + 4095) // 4096
        if size_sectors > 255:
            raise ValueError(f"chunk 超过 region 格式上限: {path}")
        loc[slot * 4] = (abs_sector >> 16) & 0xFF
        loc[slot * 4 + 1] = (abs_sector >> 8) & 0xFF
        loc[slot * 4 + 2] = abs_sector & 0xFF
        loc[slot * 4 + 3] = size_sectors & 0xFF
        struct.pack_into(">I", ts, slot * 4, timestamp)
        body.extend(payload)
        pad = (-len(body)) % 4096
        if pad:
            body.extend(b"\x00" * pad)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(loc)
        f.write(ts)
        f.write(body)
    return True


def merge_linked(base, patch, out, dim_rel, name, kind, sources, stats):
    """entities/poi 与 region 锁步合并。sources: 每槽来源 'patch'/'base'/None。"""
    b_ep = os.path.join(base, dim_rel, kind, name)
    p_ep = os.path.join(patch, dim_rel, kind, name)
    o_ep = os.path.join(out, dim_rel, kind, name)
    base_ep = MCA(b_ep) if os.path.exists(b_ep) else None
    patch_ep = MCA(p_ep) if os.path.exists(p_ep) else None
    if base_ep is None and patch_ep is None:
        return
    slots = []
    for i, s in enumerate(sources):
        if s == "patch" and patch_ep is not None:
            v = patch_ep.slot(i)
            if v is not None:
                slots.append((i, v[0], v[1]))
        elif s == "base" and base_ep is not None:
            v = base_ep.slot(i)
            if v is not None:
                slots.append((i, v[0], v[1]))
    if write_mca(o_ep, slots):
        stats["linked_" + kind] += 1
    elif os.path.exists(o_ep):
        # 合并后全空：删除 copytree 留下的 base 旧副本，避免 patch 来源槽位残留旧实体。
        os.remove(o_ep)


def merge_region(base, patch, out, relpath, stats):
    src = os.path.join(patch, relpath)
    base_src = os.path.join(base, relpath)
    out_dst = os.path.join(out, relpath)
    name = os.path.basename(relpath)
    dim_rel = os.path.dirname(os.path.dirname(relpath))  # .../dimensions/minecraft/overworld
    if not os.path.exists(base_src):
        # patch 独有的 region：直接复制 region + 其 entities/poi 兄弟文件
        shutil.copy2(src, out_dst)
        stats["copied"] += 1
        for kind in ("entities", "poi"):
            p = os.path.join(patch, dim_rel, kind, name)
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(out, dim_rel, kind, name))
                stats["copied"] += 1
        return
    base_mca = MCA(base_src)
    patch_mca = MCA(src)
    sources = []
    for i in range(1024):
        if patch_mca.present(i):
            sources.append("patch")
        elif base_mca.present(i):
            sources.append("base")
        else:
            sources.append(None)
    region_slots = []
    for i, s in enumerate(sources):
        if s == "patch":
            v = patch_mca.slot(i)
            if v is not None:
                region_slots.append((i, v[0], v[1]))
        elif s == "base":
            v = base_mca.slot(i)
            if v is not None:
                region_slots.append((i, v[0], v[1]))
    write_mca(out_dst, region_slots)
    stats["merged_regions"] += 1
    stats["patch_slots"] += sum(1 for s in sources if s == "patch")
    stats["base_slots"] += sum(1 for s in sources if s == "base")
    for kind in ("entities", "poi"):
        merge_linked(base, patch, out, dim_rel, name, kind, sources, stats)


def verify(base, patch, out):
    """复核输出 region 槽位数 == |patch ∪ base|。"""
    issues = 0
    checked = 0
    for root, _dirs, files in os.walk(out):
        if os.path.basename(root) != "region":
            continue
        for f in files:
            if not f.endswith(".mca"):
                continue
            rel = os.path.relpath(os.path.join(root, f), out)
            b = os.path.join(base, rel)
            p = os.path.join(patch, rel)
            ob = os.path.join(out, rel)
            if not os.path.exists(b):
                continue  # patch 独有，复制即可
            bm = MCA(b)
            pm = MCA(p) if os.path.exists(p) else None
            om = MCA(ob)
            expected = sum(
                1
                for i in range(1024)
                if (pm is not None and pm.present(i)) or bm.present(i)
            )
            got = om.loc and sum(1 for off, size in om.loc if size > 0)
            checked += 1
            if got != expected:
                issues += 1
                print(f"  槽位不一致: {rel} 期望={expected} 实际={got}")
    print(f"verify: 检查 {checked} 个共同 region，{issues} 个不一致")
    return issues


def main():
    ap = argparse.ArgumentParser(description="合并全量备份与 OrzMCBackup 优化备份")
    ap.add_argument("--base", required=True, help="全量备份（旧）目录")
    ap.add_argument("--patch", required=True, help="优化备份（新，部分 region）目录")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--force", action="store_true", help="允许覆盖已存在的输出目录")
    ap.add_argument("--verify", action="store_true", help="合并后复核")
    args = ap.parse_args()

    base = os.path.abspath(args.base)
    patch = os.path.abspath(args.patch)
    out = os.path.abspath(args.out)

    for d, label in ((base, "base"), (patch, "patch")):
        if not os.path.isdir(d):
            sys.exit(f"{label} 目录不存在或不可访问: {d}")
    if out == base or out == patch or os.path.commonpath([out, base]) == out or os.path.commonpath([out, patch]) == out:
        sys.exit("out 目录不能等于或包含 base/patch，也不能被 base/patch 包含")
    if not os.path.isdir(os.path.dirname(out)):
        sys.exit(f"out 的父目录不存在: {os.path.dirname(out)}")
    if os.path.exists(out):
        if not args.force:
            sys.exit(f"输出目录已存在，使用 --force 覆盖: {out}")
        shutil.rmtree(out)

    stats = {"merged_regions": 0, "copied": 0, "patch_slots": 0, "base_slots": 0,
             "linked_entities": 0, "linked_poi": 0, "overlay": 0}

    print(f"复制 base -> out ...")
    shutil.copytree(base, out, ignore=shutil.ignore_patterns("session.lock"))

    print(f"处理 patch 覆盖与合并 ...")
    for root, _dirs, files in os.walk(patch):
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(src, patch)
            rel_dir = os.path.dirname(rel)
            if f.endswith(".mca") and os.path.basename(rel_dir) in ("region", "entities", "poi"):
                if os.path.basename(rel_dir) == "region":
                    merge_region(base, patch, out, rel, stats)
                # entities/poi 在 merge_region 内与 region 一起处理
            else:
                dst = os.path.join(out, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                stats["overlay"] += 1

    lock = os.path.join(out, "session.lock")
    if os.path.exists(lock):
        os.remove(lock)

    print("完成：")
    print(f"  合并 region 数: {stats['merged_regions']}")
    print(f"  直接复制文件数: {stats['copied']}")
    print(f"  patch 槽位(8-15 新数据): {stats['patch_slots']}")
    print(f"  base 填充槽位(8-12): {stats['base_slots']}")
    print(f"  entities 锁步合并: {stats['linked_entities']}  poi 锁步合并: {stats['linked_poi']}")
    print(f"  杂项覆盖数: {stats['overlay']}")

    if args.verify:
        print("开始复核 ...")
        issues = verify(base, patch, out)
        if issues:
            sys.exit(f"复核发现 {issues} 处不一致")
        print("复核通过。")


if __name__ == "__main__":
    main()
