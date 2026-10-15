#!/usr/bin/env python3
"""CLI 命令面 manifest 校验（规范 `cli-surface.md` §8.3，路线 A 第一步）。

1. 自检 manifest 结构（离线，纯 stdlib）：
     python3 scripts/verify/surface.py --self-check

2. 与某实现的 `capabilities --json` **只读对比**（默认**不阻断**，仅报告漂移）：
     python3 scripts/verify/surface.py --implementation python \\
       --command "uv run --directory python orzmc --json capabilities"
     python3 scripts/verify/surface.py --implementation swift --capabilities /tmp/caps.json

   加 `--strict` 时：发现漂移退出 1（供命令面收敛完成后接入 CI）。

对比语义：
- 以 manifest 命令 `options[].name`（选项 `--x`、位置参数裸名）为规范；`aliases` 视为同一选项。
- 实现侧 `capabilities` 的选项名/别名与之任一相交即视为命中。
- `required` / `flag` / 已知 `type` 不一致即漂移；实现未提供 `type`（null）则跳过类型比较。
- 实现侧多出的选项若命中 `globalOptions`（如 `--root-dir`）不算漂移（全局选项可在各命令暴露）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "docs" / "spec" / "cli-surface.json"

_TYPES = {"string", "integer", "boolean", "number"}
_TYPE_ALIASES = {
    "str": "string",
    "text": "string",
    "string": "string",
    "int": "integer",
    "integer": "integer",
    "bool": "boolean",
    "boolean": "boolean",
    "flag": "boolean",
    "float": "number",
    "double": "number",
    "number": "number",
}


def key_of(name: str) -> str:
    """选项 `--x` → `x`；短名 `-x` → `x`；位置参数名原样。"""
    if name.startswith("--"):
        return name[2:]
    return name.lstrip("-")


def normalize_type(value: object) -> str | None:
    if value is None:
        return None
    return _TYPE_ALIASES.get(str(value).lower())


# ---------------------------------------------------------------- 载入
def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest 顶层应为 object")
    return data


def parse_capabilities(payload: object) -> list[dict[str, Any]]:
    """接受完整信封 `{ok,data:{commands}}`、`data` 对象、或 `{commands}`。"""
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), dict):
            payload = payload["data"]
        commands = payload.get("commands")
        if isinstance(commands, list):
            return [c for c in commands if isinstance(c, dict)]
    raise ValueError("capabilities JSON 缺少 commands 列表")


def capabilities_from_file(path: Path) -> list[dict[str, Any]]:
    return parse_capabilities(json.loads(path.read_text(encoding="utf-8")))


def capabilities_from_command(command: str) -> list[dict[str, Any]]:
    proc = subprocess.run(command, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败（exit={proc.returncode}）：{proc.stderr.strip()[:400]}")
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return parse_capabilities(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    raise ValueError("命令输出里找不到 capabilities JSON")


# ---------------------------------------------------------------- 选项归一
def manifest_option(entry: dict[str, Any]) -> dict[str, Any]:
    name = str(entry["name"])
    keys = {key_of(name)} | {key_of(str(a)) for a in entry.get("aliases", [])}
    return {
        "name": name,
        "keys": keys,
        "type": normalize_type(entry.get("type")),
        "flag": bool(entry.get("flag")),
        "required": bool(entry.get("required")),
        "argument": bool(entry.get("argument")),
    }


def impl_option(entry: dict[str, Any]) -> dict[str, Any]:
    names = [str(n) for n in (entry.get("names") or [])]
    long = next((n for n in names if n.startswith("--")), None)
    argument = entry.get("kind") == "argument" or long is None
    name = long if long else (names[0] if names else "")
    return {
        "name": name,
        "keys": {key_of(n) for n in names} | {key_of(name)},
        "type": normalize_type(entry.get("type")),
        "flag": bool(entry.get("flag")),
        "required": bool(entry.get("required")),
        "argument": argument,
    }


def match_options(
    expected: list[dict[str, Any]], actual: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[tuple[dict[str, Any], dict[str, Any]]]]:
    matched: set[int] = set()
    missing: list[dict[str, Any]] = []
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    # 位置参数按**出现顺序**匹配（名字是实现细节，不参与比较）。
    want_args = [w for w in expected if w["argument"]]
    got_args = [(i, g) for i, g in enumerate(actual) if g["argument"]]
    for index, want in enumerate(want_args):
        if index < len(got_args):
            i, got = got_args[index]
            matched.add(i)
            pairs.append((want, got))
        else:
            missing.append(want)
    # 具名选项按长名/别名匹配。
    for want in expected:
        if want["argument"]:
            continue
        found = next(
            (
                i
                for i, got in enumerate(actual)
                if i not in matched and not got["argument"] and want["keys"] & got["keys"]
            ),
            None,
        )
        if found is None:
            missing.append(want)
        else:
            matched.add(found)
            pairs.append((want, actual[found]))
    extra = [got for i, got in enumerate(actual) if i not in matched]
    return missing, extra, pairs


# ---------------------------------------------------------------- 对比
def compare(manifest: dict[str, Any], capabilities: list[dict[str, Any]], implementation: str) -> dict[str, Any]:
    global_keys = {key_of(str(o["name"])) for o in manifest.get("globalOptions", [])}
    expected_commands = {str(c["name"]): c for c in manifest.get("commands", [])}
    actual_commands = {str(c.get("name")): c for c in capabilities if c.get("name")}

    report: dict[str, Any] = {
        "implementation": implementation,
        "missingCommands": sorted(set(expected_commands) - set(actual_commands)),
        "extraCommands": sorted(set(actual_commands) - set(expected_commands)),
        "commands": [],
    }
    for name in sorted(set(expected_commands) & set(actual_commands)):
        expected = [manifest_option(o) for o in expected_commands[name].get("options", [])]
        actual = [impl_option(o) for o in actual_commands[name].get("options", [])]
        missing, extra, pairs = match_options(expected, actual)
        # 实现多出的全局选项不是漂移
        extra = [o for o in extra if not (o["keys"] & (global_keys - {key_of(name)}))]
        mismatches: list[dict[str, Any]] = []
        for want, got in pairs:
            if want["argument"] != got["argument"]:
                mismatches.append({"option": want["name"], "kind": "argument", "expected": want["argument"], "actual": got["argument"]})
            if want["flag"] != got["flag"]:
                mismatches.append({"option": want["name"], "kind": "flag", "expected": want["flag"], "actual": got["flag"]})
            # 选项的 required 由运行时报错强制（ConsoleKit 无法表达），只对位置参数比较。
            if want["argument"] and want["required"] != got["required"]:
                mismatches.append({"option": want["name"], "kind": "required", "expected": want["required"], "actual": got["required"]})
            if want["type"] and got["type"] and want["type"] != got["type"]:
                mismatches.append({"option": want["name"], "kind": "type", "expected": want["type"], "actual": got["type"]})
        if missing or extra or mismatches:
            report["commands"].append(
                {
                    "name": name,
                    "missingOptions": [o["name"] for o in missing],
                    "extraOptions": [o["name"] for o in extra],
                    "mismatches": mismatches,
                }
            )
    return report


def issue_count(report: dict[str, Any]) -> int:
    return len(report["missingCommands"]) + len(report["extraCommands"]) + sum(
        len(c["missingOptions"]) + len(c["extraOptions"]) + len(c["mismatches"]) for c in report["commands"]
    )


def apply_deviations(report: dict[str, Any], deviations: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """剔除 manifest 中**已声明**的差异（收敛 backlog），返回（未声明差异报告, 已声明数）。

    deviations 形如::
        {"missingCommands": [...], "extraCommands": [...],
         "options": {"<command>": {"missing": [...], "extra": [...], "mismatches": [["--opt", "flag"], ...]}}}
    """
    declared = 0
    missing_commands: list[str] = []
    extra_commands: list[str] = []
    for name in report["missingCommands"]:
        if name in set(deviations.get("missingCommands", [])):
            declared += 1
        else:
            missing_commands.append(name)
    for name in report["extraCommands"]:
        if name in set(deviations.get("extraCommands", [])):
            declared += 1
        else:
            extra_commands.append(name)

    options = deviations.get("options", {})
    commands: list[dict[str, Any]] = []
    for command in report["commands"]:
        dev = options.get(command["name"], {})
        declared_missing = set(dev.get("missing", []))
        declared_extra = set(dev.get("extra", []))
        declared_mismatch = {tuple(x) for x in dev.get("mismatches", [])}
        missing, extra, mismatches = [], [], []
        for name in command["missingOptions"]:
            if name in declared_missing:
                declared += 1
            else:
                missing.append(name)
        for name in command["extraOptions"]:
            if name in declared_extra:
                declared += 1
            else:
                extra.append(name)
        for item in command["mismatches"]:
            if (item["option"], item["kind"]) in declared_mismatch:
                declared += 1
            else:
                mismatches.append(item)
        if missing or extra or mismatches:
            commands.append(
                {"name": command["name"], "missingOptions": missing, "extraOptions": extra, "mismatches": mismatches}
            )
    unexpected = {
        "implementation": report["implementation"],
        "missingCommands": missing_commands,
        "extraCommands": extra_commands,
        "commands": commands,
    }
    return unexpected, declared


def print_report(report: dict[str, Any]) -> None:
    impl = report["implementation"]
    total = issue_count(report)
    print(f"[surface] 实现 {impl!r} 与 manifest 对比：{total} 处差异")
    for name in report["missingCommands"]:
        print(f"  - 缺少命令: {name}")
    for name in report["extraCommands"]:
        print(f"  + 多出命令: {name}")
    for command in report["commands"]:
        print(f"  {command['name']}:")
        for name in command["missingOptions"]:
            print(f"    - 缺少选项: {name}")
        for name in command["extraOptions"]:
            print(f"    + 多出选项: {name}")
        for item in command["mismatches"]:
            print(
                f"    ! {item['option']} {item['kind']}: 期望 {item['expected']}，实际 {item['actual']}"
            )
    if total == 0:
        print("  ✓ 完全一致")


# ---------------------------------------------------------------- manifest 自检
def self_check(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest.get("specVersion"), str):
        errors.append("缺少 specVersion")
    globals_ = manifest.get("globalOptions")
    if not isinstance(globals_, list):
        errors.append("globalOptions 应为列表")
        globals_ = []
    commands = manifest.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("commands 应为非空列表")
        commands = []

    def check_option(where: str, option: Any) -> None:
        if not isinstance(option, dict):
            errors.append(f"{where}: 选项应为 object")
            return
        name = option.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"{where}: 选项缺少 name")
            return
        if not option.get("argument") and not name.startswith("--"):
            errors.append(f"{where}: 选项 {name} 应为 -- 长名或标记 argument")
        if normalize_type(option.get("type")) not in _TYPES:
            errors.append(f"{where}: 选项 {name} 的 type 非法：{option.get('type')!r}")
        for field in ("flag", "required", "argument"):
            if field in option and not isinstance(option[field], bool):
                errors.append(f"{where}: 选项 {name} 的 {field} 应为 bool")
        enum = option.get("enum")
        if enum is not None and (not isinstance(enum, list) or not all(isinstance(e, str) for e in enum)):
            errors.append(f"{where}: 选项 {name} 的 enum 应为字符串列表")

    for option in globals_:
        check_option("globalOptions", option)
    seen_commands: set[str] = set()
    for command in commands:
        if not isinstance(command, dict) or not isinstance(command.get("name"), str):
            errors.append("命令缺少 name")
            continue
        name = command["name"]
        if name in seen_commands:
            errors.append(f"命令名重复: {name}")
        seen_commands.add(name)
        options = command.get("options", [])
        if not isinstance(options, list):
            errors.append(f"命令 {name}: options 应为列表")
            continue
        seen_keys: set[str] = set()
        for option in options:
            check_option(f"命令 {name}", option)
            if isinstance(option, dict) and isinstance(option.get("name"), str):
                key = key_of(option["name"])
                if key in seen_keys:
                    errors.append(f"命令 {name}: 选项名重复 {option['name']}")
                seen_keys.add(key)

    # deviations 自检：只校验 missing 引用的选项确实存在于 manifest（防笔误）。
    option_keys: dict[str, set[str]] = {}
    for command in commands:
        if not isinstance(command, dict) or not isinstance(command.get("name"), str):
            continue
        option_keys[command["name"]] = {
            key_of(o["name"])
            for o in command.get("options", [])
            if isinstance(o, dict) and isinstance(o.get("name"), str)
        }
    deviations = manifest.get("deviations")
    if deviations is not None:
        if not isinstance(deviations, dict):
            errors.append("deviations 应为 object")
        else:
            for impl_name, impl in deviations.items():
                if impl_name == "note" or not isinstance(impl, dict):
                    continue
                for cmd_name, entry in (impl.get("options") or {}).items():
                    if cmd_name not in option_keys:
                        errors.append(f"deviations.{impl_name}.options: 未知命令 {cmd_name}")
                        continue
                    for missing in entry.get("missing", []):
                        if key_of(str(missing)) not in option_keys[cmd_name]:
                            errors.append(f"deviations.{impl_name}.{cmd_name}: missing 引用未知选项 {missing}")
    return errors


# ---------------------------------------------------------------- CLI
def main() -> int:
    parser = argparse.ArgumentParser(description="CLI 命令面 manifest 校验（规范 §8.3）")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--self-check", action="store_true", help="仅自检 manifest 结构")
    parser.add_argument("--implementation", default="impl", help="实现名（报告用）")
    parser.add_argument("--capabilities", type=Path, help="capabilities JSON 文件")
    parser.add_argument("--command", help="打印 capabilities --json 的命令（与 --capabilities 二选一）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    parser.add_argument("--strict", action="store_true", help="发现差异时退出 1（默认不阻断）")
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"::error::无法读取 manifest：{exc}")
        return 1

    errors = self_check(manifest)
    if errors:
        for error in errors:
            print(f"::error::manifest: {error}")
        return 1
    if args.self_check:
        print(f"[ok] manifest 结构自检通过（{len(manifest['commands'])} 个命令）")
        return 0

    if not args.capabilities and not args.command:
        parser.error("需要 --self-check、--capabilities 或 --command 之一")

    try:
        capabilities = (
            capabilities_from_file(args.capabilities) if args.capabilities else capabilities_from_command(args.command)
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"::error::无法获取 capabilities：{exc}")
        return 1

    report = compare(manifest, capabilities, args.implementation)
    deviations = manifest.get("deviations", {}).get(args.implementation, {})
    unexpected, declared = apply_deviations(report, deviations)
    if args.json:
        print(json.dumps({"unexpected": unexpected, "declaredCount": declared}, ensure_ascii=False, indent=2))
    else:
        print_report(unexpected)
        if declared:
            print(f"  （已声明差异 {declared} 处，见 cli-surface.json `deviations.{args.implementation}`）")
    return 1 if args.strict and issue_count(unexpected) else 0


if __name__ == "__main__":
    sys.exit(main())
