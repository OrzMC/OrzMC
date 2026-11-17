#!/usr/bin/env python3
"""生成 LP 权限同步命令清单（方案①：文档唯一权威，2026-08-12）

从 OrzMC/plugin/docs/permission-groups.md 的 L0-L3 权限表自动生成
`lp group <组> permission set <节点> true|false` 命令清单 —— 替代手工维护
minecraft-bot/perm_commands.txt。改权限 = 只改文档，清单永远派生。

用法:
  python3 gen_perm_commands.py [doc路径]           # 输出到 stdout
  python3 gen_perm_commands.py [doc路径] -o 文件    # 输出到文件

解析规则:
  - 章节头 `## L0 default / L1 member / L2 builder / L3 admin`（其后表格即该组节点）
  - 表格行首格为反引号权限节点；第三列含 "false" → 设 false（其余 true）
  - 输出含：父链命令（幂等）、高危节点注释；不解析验收/验证等非 L0-L3 表格
"""
import argparse
import re
import sys
from datetime import datetime

DEFAULT_DOC = "/Users/bot/OrzMC/plugin/docs/permission-groups.md"
GROUP_MAP = {"L0": "default", "L1": "member", "L2": "builder", "L3": "admin"}
SECTION_RE = re.compile(r"^## (L[0-3]) (\w+)")
HIGH_RISK = "高危节点（明确不授予任何组）：*、luckperms.*、minecraft.command.op、bukkit.command.op、essentials.stop、essentials.reload"


def parse(doc_path):
    """返回 [(level, group, [(node, value), ...]), ...]"""
    with open(doc_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    sections = []
    cur = None
    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            cur = [m.group(1), GROUP_MAP[m.group(1)], []]
            sections.append(cur)
            continue
        if cur and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].startswith("`") and cells[0].endswith("`"):
                node = cells[0].strip("`")
                value = "false" if "false" in cells[2] else "true"
                cur[2].append((node, value))
    return [(lv, g, rows) for lv, g, rows in sections]


def render(sections):
    out = []
    out.append("# ============================================================")
    out.append("# 权限组配置命令（自动生成，勿手改）")
    out.append("# 唯一权威来源：OrzMC/plugin/docs/permission-groups.md")
    out.append(f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append("# 用法：逐条执行本清单（lp group <组> permission set <节点> true|false）")
    out.append("# 同步前：lp export 备份；同步后：lp group <组> permission check <节点> 验证")
    out.append("# 继承链（parent）：member→default、builder→member、admin→builder（LuckPermsBootstrap 自动校正）")
    out.append(f"# {HIGH_RISK}")
    out.append("# ============================================================")
    out.append("")
    out.append("# ---- 继承链（幂等，重复执行无副作用）----")
    out.append("lp group member parent set default")
    out.append("lp group builder parent set member")
    out.append("lp group admin parent set builder")
    out.append("")
    for level, group, rows in sections:
        out.append(f"# ---- L{level[1]} {group}（{len(rows)} 项）----")
        for node, value in rows:
            out.append(f"lp group {group} permission set {node} {value}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="从 permission-groups.md 生成 LP 权限命令清单")
    parser.add_argument("doc", nargs="?", default=DEFAULT_DOC, help="权限文档路径（默认插件仓库）")
    parser.add_argument("-o", "--output", help="输出到文件（缺省输出 stdout）")
    args = parser.parse_args()
    content = render(parse(args.doc))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已生成 {args.output}（{len([l for l in content.splitlines() if l.startswith('lp group') and 'permission set' in l and 'parent' not in l])} 条权限 set 命令）")
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
