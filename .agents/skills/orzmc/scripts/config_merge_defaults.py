#!/usr/bin/env python3
"""插件升级：按新版默认定义迁移配置（新定义补键 + 旧自定义值保留 + 注释保留）

场景：jar 升级后「升级二进制 ≠ 升级配置」——新版本新增的配置键在旧盘缺缺失，
启动时健康检查报「缺失: xxx.yyy」。本工具把**新版 jar 内的默认配置定义**作为权威键集，
合并进**实例现有配置**：缺失键按新默认补齐、既有键保留实例自定义值、不删除任何既有键。
默认用 ruamel.yaml 往返加载 → **实例文件的注释/顺序原样保留**（第三方插件常带注释文档）。

用法：
  # 从 jar 提取默认配置（可选 helper）
  python3 config_merge_defaults.py --extract <a.jar> --extract-dir defaults/
  # 预览差异（不写文件）
  python3 config_merge_defaults.py --default defaults/ --target <实例配置目录> [--dry-run]
  # 生成合并结果到 out/（供上传）
  python3 config_merge_defaults.py --default defaults/ --target <实例目录> --out out/
  # 第三方插件单文件模式
  python3 config_merge_defaults.py --default-file a_config.yml --target-file b_config.yml --out-file merged.yml
退出码：0=无缺失键 / 1=有缺失键（已写出合并文件时同样返回 1，便于 CI 判定）
"""
import argparse
import copy
import json
import os
import sys
import zipfile

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
    _yaml = YAML()
    _yaml.preserve_quotes = True
    _yaml.width = 4096
except ImportError:  # pragma: no cover
    _yaml = None

import yaml as _pyyaml


def load_rt(path):
    """往返加载（保注释）；ruamel 缺失时退化为 PyYAML（丢注释，需 --allow-comment-loss）"""
    with open(path, encoding="utf-8") as fh:
        if _yaml is not None:
            return _yaml.load(fh)
        return _pyyaml.safe_load(fh)


def dump_rt(data, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        if _yaml is not None:
            _yaml.dump(data, fh)
        else:
            _pyyaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


def safe_default(path):
    with open(path, encoding="utf-8") as fh:
        return _pyyaml.safe_load(fh)


def walk_defaults(default, target, prefix, added, conflicts, extras, parent_target=None):
    """把 default 的键集合并进 target（就地修改）；返回 None"""
    for key, dval in default.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if not isinstance(target, CommentedMap) and not hasattr(target, "get"):
            continue
        if key not in target:
            target[key] = copy.deepcopy(dval)
            added.append(path)
            continue
        tval = target[key]
        if isinstance(dval, dict) and isinstance(tval, dict):
            walk_defaults(dval, tval, path, added, conflicts, extras)
        elif isinstance(dval, dict) and not isinstance(tval, dict):
            conflicts.append({"path": path, "reason": "默认是映射但实例是标量", "instance": repr(tval)[:80]})
        # 标量/列表：保留实例值，不覆盖（自定义）
    if parent_target is not None:
        return


def collect_paths(data, prefix=""):
    out = set()
    if isinstance(data, dict):
        for k, v in data.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.add(p)
            out |= collect_paths(v, p)
    return out


def collect_extras(default, target, prefix, extras):
    """实例有、新版默认没有的键（保留 + 报告，绝不删）"""
    if not isinstance(default, dict) or not isinstance(target, dict):
        return
    for key, tval in target.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if key not in default:
            extras.append(path)
            continue
        collect_extras(default[key], tval, path, extras)


def merge_file(default_path, target_path, out_path=None, dry_run=False):
    """返回 (report_dict, merged_written_path_or_None)"""
    ddef = safe_default(default_path)
    if not os.path.exists(target_path):
        return {"file": os.path.basename(default_path), "status": "实例无此文件（跳过）"}, None
    target = load_rt(target_path)
    if target is None:
        return {"file": os.path.basename(default_path), "status": "实例文件为空（跳过）"}, None
    added, conflicts, extras = [], [], []
    if isinstance(ddef, dict) and isinstance(target, dict):
        walk_defaults(ddef, target, "", added, conflicts, extras)
        collect_extras(ddef, target, "", extras)
    report = {"file": os.path.basename(target_path), "added": sorted(added),
              "conflicts": conflicts, "extras_not_in_default": sorted(extras)}
    if not added and not conflicts:
        report["status"] = "✅ 无缺失键"
        return report, None
    report["status"] = f"⚠️ 补 {len(added)} 键" + (f" / {len(conflicts)} 冲突" if conflicts else "")
    if out_path and not dry_run:
        dump_rt(target, out_path)
        return report, out_path
    return report, None


def extract_jar_defaults(jar, outdir):
    os.makedirs(outdir, exist_ok=True)
    zf = zipfile.ZipFile(jar)
    got = []
    for n in zf.namelist():
        if n.endswith((".yml", ".yaml")) and not n.startswith("META-INF") and "/" not in n:
            with open(os.path.join(outdir, n), "wb") as fh:
                fh.write(zf.read(n))
            got.append(n)
    return got


def main():
    ap = argparse.ArgumentParser(description="插件升级配置迁移（新定义补键 + 旧值保留）")
    ap.add_argument("--default", help="新版本默认配置目录")
    ap.add_argument("--target", help="实例配置目录（只读，结果写 --out）")
    ap.add_argument("--out", help="合并结果输出目录")
    ap.add_argument("--default-file")
    ap.add_argument("--target-file")
    ap.add_argument("--out-file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", help="报告落盘路径")
    ap.add_argument("--extract", help="从 jar 提取默认配置")
    ap.add_argument("--extract-dir", default="defaults")
    args = ap.parse_args()

    if args.extract:
        print("提取:", extract_jar_defaults(args.extract, args.extract_dir))
        return 0

    reports = []
    if args.default_file:
        rep, out = merge_file(args.default_file, args.target_file,
                              args.out_file or (os.path.join(args.out, "merged.yml") if args.out else None), args.dry_run)
        reports.append(rep)
        print(f"  {rep['file']}: {rep['status']}")
    else:
        for fn in sorted(os.listdir(args.default)):
            if not fn.endswith((".yml", ".yaml")):
                continue
            out_path = os.path.join(args.out, fn) if args.out else None
            rep, written = merge_file(os.path.join(args.default, fn), os.path.join(args.target, fn), out_path, args.dry_run)
            reports.append(rep)
            mark = "→ " + written if written else ""
            print(f"  {rep['status']:<22} {rep['file']:<24} {mark}")
            if rep.get("added"):
                print("        补键:", ", ".join(rep["added"][:12]) + (" ..." if len(rep["added"]) > 12 else ""))
            if rep.get("conflicts"):
                print("        冲突:", json.dumps(rep["conflicts"], ensure_ascii=False)[:200])
            if rep.get("extras_not_in_default"):
                print("        保留的实例独有键:", ", ".join(rep["extras_not_in_default"][:10]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(reports, fh, ensure_ascii=False, indent=1)
        print("报告:", args.json)
    need = any(r.get("added") or r.get("conflicts") for r in reports)
    return 1 if need else 0


if __name__ == "__main__":
    sys.exit(main())
