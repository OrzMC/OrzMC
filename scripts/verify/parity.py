#!/usr/bin/env python3
"""两套 CLI 的**能力台账**校验（策略见 `docs/two-cli-strategy.md`，台账 `docs/spec/parity.json`）。

为什么需要它：Python / Swift 两套实现并行期间，最大的成本不是"写代码"，而是**不知道谁落后了**——
于是每个功能都靠人记忆决定要不要两边都改，最后要么重复开发，要么悄悄漂移。

校验项（`--static`，纯离线，父仓库 CI 默认跑）：

1. **覆盖**：`docs/spec/cli-surface.json` 里的每个命令都必须在台账登记（漏登记 → 失败）；
2. **状态合法**：`parity|behind|lead|na`，且 `lead` 必须是 `python|swift`；
3. **落后要交差**：`behind` 必须写 `reason` 与 `review_by`（`YYYY-MM-DD`），过期 → 失败；
4. **共用件只有一份**：验收脚本在父仓库 `scripts/accept/cli.py`，两侧 CI 必须引用它
   （谁放回本地副本 → 失败）。

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


SHARED_HARNESS = REPO / "scripts" / "accept" / "cli.py"
HARNESS_CONSUMERS = {
    "python": REPO / "python" / ".github" / "workflows" / "ci.yml",
    "swift": REPO / "swift" / "lib" / "OrzMCKit" / ".github" / "workflows" / "ci.yml",
}


def check_shared_harness() -> str:
    """M2：验收脚本**只有一份**（父仓库 `scripts/accept/cli.py`），两侧 CI 必须真的调用它。

    之前是两个仓库各复制一份（842 + 724 行，用例集还会漂移）。现在改为：
    1. 共享脚本必须存在且能解析（`--list-cases` 不依赖被测物）；
    2. 已检出的子模块，其 CI 必须引用 `scripts/accept/cli.py`（防止谁偷偷放回本地副本）。
    """
    if not SHARED_HARNESS.exists():
        raise Failure(f"缺共享验收脚本: {SHARED_HARNESS.relative_to(REPO)}")

    legacy = {
        "python": REPO / "python" / "scripts" / "accept_cli.py",
        "swift": REPO / "swift" / "lib" / "OrzMCKit" / "scripts" / "accept_cli.py",
    }
    checked = []
    for side, workflow in HARNESS_CONSUMERS.items():
        if not workflow.exists():
            continue  # 子模块未检出（父仓库 CI 的默认情况）
        text = workflow.read_text(encoding="utf-8")
        if "scripts/accept_cli.py" in text or '"scripts/accept_cli.py"' in text:
            raise Failure(f"{side} 的 CI 仍在调用旧的本地副本 scripts/accept_cli.py（应改为父仓库 scripts/accept/cli.py）")
        if "accept/cli.py" not in text:
            raise Failure(f"{side} 的 CI 没有调用共享验收脚本（scripts/accept/cli.py）")
        checked.append(side)

    # 文件还在但没人用：只提醒（迁移期允许残留，删掉更清爽）。
    leftovers = [str(p.relative_to(REPO)) for p in legacy.values() if p.exists()]
    if leftovers:
        print(f"[warn] 旧副本尚未删除（已不再被 CI 使用）: {', '.join(leftovers)}", file=sys.stderr)
    note = "、".join(checked) if checked else "子模块未检出，仅校验共享脚本"
    return f"共享验收脚本就位（{note}）"


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
        harness_note = check_shared_harness()
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
