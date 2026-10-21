#!/usr/bin/env python3
"""合规文案单一来源同步器。

**单一事实源**：
  - `docs/compliance/compliance.json`（免责声明 / 责任主体 / 联系方式等）
  - `docs/compliance/privacy.md`（隐私政策正文）

把上面两者的内容渲染并写入各引用位置：
  - 标记块（Markdown/HTML，标记 `ORZMC:COMPLIANCE:BEGIN/END`）：README、官网页脚
  - 整文件生成：Swift `Game/Compliance.swift`、Python `orzmc/_compliance.py`、官网 `content/privacy.md`

用法：
  python3 scripts/sync_compliance.py            # 写入（默认）
  python3 scripts/sync_compliance.py --check     # 只校验是否漂移（CI 用；漂移退出 1）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CANON_DIR = REPO / "docs" / "compliance"
CANON_JSON = CANON_DIR / "compliance.json"
CANON_PRIVACY = CANON_DIR / "privacy.md"

BEGIN = "ORZMC:COMPLIANCE:BEGIN"
END = "ORZMC:COMPLIANCE:END"
# 标记块会落进 5 个**不同仓库**的 README / 页脚里(父仓库 + python + swift/app + OrzMCKit + site),
# 所以注释里不能写「本仓库的 scripts/…」——子仓库里根本没有这两个路径,读代码/issue 的人会以为
# 生成器缺失(2026-10-21 的 OrzMCApp#32 就是这么误报的)。写清是父仓库的路径。
GENERATED_NOTE = (
    "auto-generated; do not edit by hand. Single source: docs/compliance/ + "
    "scripts/sync_compliance.py in the OrzMC/OrzMC umbrella repo"
)

# 标记块目标：(相对路径, 注释风格) —— 注释风格 md/html 共用 HTML 注释
BLOCK_TARGETS: list[tuple[str, str]] = [
    ("README.md", "md"),
    ("python/README.md", "md"),
    ("swift/app/README.md", "md"),
    ("swift/lib/OrzMCKit/README.md", "md"),
    ("site/layouts/partials/site-footer.html", "html"),
]

# 整文件生成目标
SWIFT_COMPLIANCE = "swift/lib/OrzMCKit/Sources/Game/Compliance.swift"
PY_COMPLIANCE = "python/orzmc/orzmc/_compliance.py"
SITE_PRIVACY = "site/content/privacy.md"


def load_canon() -> dict[str, str]:
    return json.loads(CANON_JSON.read_text(encoding="utf-8"))


def md_block(c: dict[str, str]) -> str:
    return (
        f"<!-- {BEGIN} ({GENERATED_NOTE}) -->\n"
        f"> **{c['disclaimer_en']}**\n"
        ">\n"
        f"> {c['disclaimer_zh']}\n"
        ">\n"
        f"> {c['trademark_zh']}\n"
        ">\n"
        f"> 联系：[GitHub 组织]({c['contact_url']}) ｜ 隐私政策：{c['privacy_url']}\n"
        f"<!-- {END} -->"
    )


def html_block(c: dict[str, str]) -> str:
    contact = c.get("contact_url", f"https://github.com/{c['owner']}")
    return (
        f"<!-- {BEGIN} ({GENERATED_NOTE}) -->\n"
        '<div class="site-footer__compliance">\n'
        f'  <p class="site-footer__line">{c["disclaimer_en"]}</p>\n'
        f'  <p class="site-footer__line">{c["disclaimer_zh"]}</p>\n'
        '  <p class="site-footer__links">\n'
        f'    <a href="{c["privacy_url"]}">隐私政策</a>\n'
        '    <span class="site-footer__sep" aria-hidden="true">·</span>\n'
        f'    <a href="{contact}" target="_blank" rel="noopener noreferrer">GitHub 组织</a>\n'
        '  </p>\n'
        '</div>\n'
        f"<!-- {END} -->"
    )


def swift_file(c: dict[str, str]) -> str:
    d = json.dumps(c["disclaimer_en"], ensure_ascii=False)
    dz = json.dumps(c["disclaimer_zh"], ensure_ascii=False)
    tz = json.dumps(c["trademark_zh"], ensure_ascii=False)
    contact = json.dumps(c["contact_url"], ensure_ascii=False)
    privacy = json.dumps(c["privacy_url"], ensure_ascii=False)
    website = json.dumps(c["website"], ensure_ascii=False)
    return f"""// 本文件由 scripts/sync_compliance.py 生成；请改父仓库 docs/compliance/compliance.json 后重新生成。
import Foundation

/// Minecraft Usage Guidelines 要求的声明与联系方式（单一事实源）。
public enum Compliance {{
    public static let disclaimer = {d}
    public static let disclaimerZh = {dz}
    public static let trademarkZh = {tz}
    public static let contactURL = {contact}
    public static let privacyURL = {privacy}
    public static let website = {website}

    /// 免责声明文本（英文 / 中文 / 商标各占一行；CLI 页脚与 `--json` 同源）。
    public static var text: String {{
        [disclaimer, disclaimerZh, trademarkZh].joined(separator: "\\n")
    }}
}}
"""


def python_file(c: dict[str, str]) -> str:
    d = json.dumps(c["disclaimer_en"], ensure_ascii=False)
    dz = json.dumps(c["disclaimer_zh"], ensure_ascii=False)
    tz = json.dumps(c["trademark_zh"], ensure_ascii=False)
    contact = json.dumps(c["contact_url"], ensure_ascii=False)
    privacy = json.dumps(c["privacy_url"], ensure_ascii=False)
    website = json.dumps(c["website"], ensure_ascii=False)
    return f'''"""Minecraft Usage Guidelines 声明与联系方式（单一事实源）。

本文件由 scripts/sync_compliance.py 生成；请改父仓库 docs/compliance/compliance.json 后重新生成。
"""

from __future__ import annotations

DISCLAIMER_EN = {d}
DISCLAIMER_ZH = {dz}
TRADEMARK_ZH = {tz}
CONTACT_URL = {contact}
PRIVACY_URL = {privacy}
WEBSITE = {website}


def disclaimer_text() -> str:
    """免责声明文本（英文 / 中文 / 商标各占一行；CLI 页脚与 ``--json`` 同源）。"""
    return "\\n".join((DISCLAIMER_EN, DISCLAIMER_ZH, TRADEMARK_ZH))


# 兼容旧名: 2.9.x 之前导出 ``disclaimer_line``,返回同一段文本
disclaimer_line = disclaimer_text
'''


def site_privacy(c: dict[str, str]) -> str:
    body = CANON_PRIVACY.read_text(encoding="utf-8").strip()
    # 页面主标题由布局按 frontmatter title 渲染；去掉正文首行 H1，避免同页双 <h1>。
    if body.startswith("# "):
        nl = body.find("\n")
        body = body[nl + 1 :].lstrip("\n") if nl >= 0 else ""
    return (
        "---\n"
        'title: "隐私政策"\n'
        "toc: true\n"
        f"# 本页由 scripts/sync_compliance.py 从 docs/compliance/privacy.md 生成，请勿直接编辑。\n"
        "---\n\n"
        f"{body}\n"
    )


def render_block(kind: str, c: dict[str, str]) -> str:
    return html_block(c) if kind == "html" else md_block(c)


def replace_block(text: str, block: str, path: Path) -> str:
    bi = text.find(BEGIN)
    ei = text.find(END)
    if bi < 0 or ei < 0 or ei < bi:
        raise SystemExit(f"{path}: 缺少 `{BEGIN}` / `{END}` 标记")
    line_start = text.rfind("\n", 0, bi) + 1
    line_end = text.find("\n", ei)
    line_end = len(text) if line_end < 0 else line_end
    return text[:line_start] + block + text[line_end:]


def planned_changes(c: dict[str, str]) -> tuple[dict[Path, str], list[str]]:
    out: dict[Path, str] = {}
    skipped: list[str] = []
    for rel, kind in BLOCK_TARGETS:
        p = REPO / rel
        if not p.exists():  # 子模块未检出（如父仓库 CI）时跳过
            skipped.append(rel)
            continue
        out[p] = replace_block(p.read_text(encoding="utf-8"), render_block(kind, c), p)
    for rel, render in ((SWIFT_COMPLIANCE, swift_file), (PY_COMPLIANCE, python_file), (SITE_PRIVACY, site_privacy)):
        p = REPO / rel
        if not p.parent.exists():
            skipped.append(rel)
            continue
        out[p] = render(c)
    return out, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="合规文案单一来源同步器")
    ap.add_argument("--check", action="store_true", help="只校验是否漂移（不写入）")
    args = ap.parse_args()

    c = load_canon()
    changes, skipped = planned_changes(c)
    drift = []
    for path, content in changes.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            drift.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    note = f"（跳过未检出 {len(skipped)} 处）" if skipped else ""
    if args.check:
        if drift:
            print("::error::合规文案与 docs/compliance/ 不一致（运行 python3 scripts/sync_compliance.py 同步）：")
            for p in drift:
                print(f"  - {p.relative_to(REPO)}")
            return 1
        print(f"[ok] 合规文案一致（{len(changes)} 处引用）{note}")
        return 0

    print(f"[ok] 已同步合规文案（{len(drift)} 处更新，共 {len(changes)} 处引用）{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
