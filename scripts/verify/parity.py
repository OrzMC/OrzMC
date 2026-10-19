#!/usr/bin/env python3
"""两套 CLI 的**能力台账**校验（策略见 `docs/two-cli-strategy.md`，台账 `docs/spec/parity.json`）。

为什么需要它：Python / Swift 两套实现并行期间，最大的成本不是"写代码"，而是**不知道谁落后了**——
于是每个功能都靠人记忆决定要不要两边都改，最后要么重复开发，要么悄悄漂移。

校验项（`--static`，纯离线，父仓库 CI 默认跑）：

1. **覆盖**：`docs/spec/cli-surface.json` 里的每个命令都必须在台账登记（漏登记 → 失败）；
2. **状态合法**：`parity|behind|lead|na`，且 `lead` 必须是 `python|swift`；
3. **落后要交差**：`behind` 必须写 `reason` 与 `review_by`（`YYYY-MM-DD`），过期 → 失败；
4. **共用件不漂移**：两个 `scripts/accept_cli.py` 的**用例集合**必须一致（缺/多 → 失败）。

动态校验（可选，需要两边的 `capabilities --json` 输出）：

5. **声明即事实**：台账写 `parity` 的实现，其 capabilities 必须真的有该命令（缺 → 失败）；
   写 `na` 的实现则**不得**出现该命令（出现 → 失败）。

用法:
    python3 scripts/verify/parity.py                    # 静态校验（CI 默认）
    python3 scripts/verify/parity.py --python-caps p.json --swift-caps s.json   # 追加动态校验
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "docs" / "spec" / "cli-surface.json"
LEDGER = REPO / "docs" / "spec" / "parity.json"
HARNESSES = {
    "python": REPO / "python" / "scripts" / "accept_cli.py",
    "swift": REPO / "swift" / "lib" / "OrzMCKit" / "scripts" / "accept_cli.py",
}

STATUSES = {"parity", "behind", "lead", "na"}
LEADS = {"python", "swift"}
CASE_RE = re.compile(r'^@case\(\s*"([^"]+)"\s*,\s*"([^"]+)"')


class Failure(Exception):
    pass


def load_json(path: Path) -> dict:
    if not path.exists():
        raise Failure(f"缺文件: {path.relative_to(REPO)}")
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_commands() -> list[str]:
    data = load_json(MANIFEST)
    return [str(item["name"]) for item in data.get("commands", [])]


def check_coverage(commands: list[str], ledger: dict) -> None:
    entries = ledger.get("commands", {})
    missing = [name for name in commands if name not in entries]
    if missing:
        raise Failure(f"台账缺登记: {', '.join(missing)}（docs/spec/parity.json）")
    extra = [name for name in entries if name not in commands]
    if extra:
        raise Failure(f"台账登记了 manifest 里没有的命令: {', '.join(extra)}")


def check_statuses(ledger: dict) -> None:
    today = dt.date.today()
    for name, entry in ledger.get("commands", {}).items():
        lead = entry.get("lead")
        if lead not in LEADS:
            raise Failure(f"{name}: lead 必须是 python|swift，实际 {lead!r}")
        for side in LEADS:
            status = entry.get(side)
            if status not in STATUSES:
                raise Failure(f"{name}: {side} 状态非法 {status!r}（可选 {sorted(STATUSES)}）")
            if side == lead and status != "lead":
                raise Failure(f"{name}: lead={lead} 的一侧状态应为 lead，实际 {status!r}")
            if side != lead and status == "lead":
                raise Failure(f"{name}: 非 lead 的一侧（{side}）不能标 lead")
            if status == "behind":
                reason = entry.get("reason")
                review = entry.get("review_by")
                if not reason:
                    raise Failure(f"{name}: {side}=behind 必须写 reason")
                if not review:
                    raise Failure(f"{name}: {side}=behind 必须写 review_by（YYYY-MM-DD）")
                try:
                    due = dt.date.fromisoformat(str(review))
                except ValueError as exc:
                    raise Failure(f"{name}: review_by 不是合法日期: {review!r}") from exc
                if due < today:
                    raise Failure(f"{name}: {side}=behind 已过期（review_by {review}），该补齐或改台账")


def harness_cases(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        raise Failure(f"缺验收脚本: {path.relative_to(REPO)}")
    cases: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CASE_RE.match(line.strip())
        if match:
            cases.add((match.group(1), match.group(2)))
    return cases


def allowed_exclusive(ledger: dict) -> dict[str, set[tuple[str, str]]]:
    """台账里登记的「实现独有用例」（`sharedArtifacts.harnessCases.{pythonOnly,swiftOnly}`）。"""
    block = (ledger.get("sharedArtifacts") or {}).get("harnessCases") or {}
    out: dict[str, set[tuple[str, str]]] = {}
    for side in LEADS:
        key = f"{side}Only"
        entries = block.get(key) or {}
        if not isinstance(entries, dict):
            raise Failure(f"parity.json 的 sharedArtifacts.harnessCases.{key} 必须是对象（用例 → 原因）")
        out[side] = {tuple(item.split("/", 1)) for item in entries}
    return out


def check_harness_parity(ledger: dict) -> str:
    sets = {side: harness_cases(path) for side, path in HARNESSES.items()}
    allowed = allowed_exclusive(ledger)
    problems: list[str] = []
    for side, other in (("python", "swift"), ("swift", "python")):
        exclusive = sets[side] - sets[other]
        declared = allowed[side]
        undeclared = exclusive - declared
        stale = declared - exclusive
        if undeclared:
            problems.append(
                f"  仅 {side} 有（未在 parity.json 登记）: "
                + ", ".join(f"{g}/{n}" for g, n in sorted(undeclared))
            )
        if stale:
            problems.append(
                f"  {side} 台账登记但实际已不存在（清理台账）: "
                + ", ".join(f"{g}/{n}" for g, n in sorted(stale))
            )
    if problems:
        raise Failure(
            "两个验收脚本的用例集合不一致（判据必须同一份）:\n"
            + "\n".join(problems)
            + "\n  处理：补齐较少的一侧、两侧同时删掉，或在 parity.json 的 "
            "sharedArtifacts.harnessCases 里登记「实现独有」并写原因。"
        )
    shared = sets["python"] & sets["swift"]
    exclusive = len(allowed["python"]) + len(allowed["swift"])
    return f"验收用例一致（共享 {len(shared)} 例，已登记的实现独有 {exclusive} 例）"


def commands_in_caps(path: Path) -> set[str]:
    data = load_json(path)
    payload = data.get("data", data)
    commands = payload.get("commands", [])
    return {str(item["name"]) for item in commands}


def check_declared_vs_actual(ledger: dict, caps: dict[str, Path]) -> None:
    actual = {side: commands_in_caps(path) for side, path in caps.items()}
    for name, entry in ledger.get("commands", {}).items():
        for side, present in actual.items():
            status = entry.get(side)
            if status == "parity" and name not in present:
                raise Failure(f"{name}: 台账标 {side}=parity，但 {side} 的 capabilities 里没有该命令")
            if status == "na" and name in present:
                raise Failure(f"{name}: 台账标 {side}=na，但 {side} 的 capabilities 里有该命令（台账或实现需更新）")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="两套 CLI 能力台账校验")
    parser.add_argument("--python-caps", type=Path, help="Python 侧 `--json capabilities` 的输出文件")
    parser.add_argument("--swift-caps", type=Path, help="Swift 侧 `--json capabilities` 的输出文件")
    args = parser.parse_args(argv)

    ledger = load_json(LEDGER)
    commands = manifest_commands()

    try:
        check_coverage(commands, ledger)
        check_statuses(ledger)
        harness_note = check_harness_parity(ledger)
        caps = {}
        if args.python_caps:
            caps["python"] = args.python_caps
        if args.swift_caps:
            caps["swift"] = args.swift_caps
        if caps:
            check_declared_vs_actual(ledger, caps)
    except Failure as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    behind = [
        f"{name}:{side}"
        for name, entry in ledger["commands"].items()
        for side in LEADS
        if entry.get(side) == "behind"
    ]
    suffix = f"；落后登记 {len(behind)} 条" if behind else ""
    dynamic = "（含 capabilities 比对）" if args.python_caps or args.swift_caps else ""
    print(f"[ok] 能力台账一致：{len(commands)} 个命令 / {harness_note}{suffix}{dynamic}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
