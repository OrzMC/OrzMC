#!/usr/bin/env python3
"""GrimAC 最近作弊记录查询（含处理方式判定）

数据源：
  1. 违规记录: ~/minecraft-server/plugins/GrimAC/data/history.v1.db（grim_violations JOIN grim_players/grim_checks，[log] 通道持久化）
  2. 处理方式: 服务器日志（latest.log + 归档 .gz）中 GrimAC 触发的 kick 记录
     （Essentials 控制台执行 /kick + 处罚文案关键词），时间窗 ±10s 内匹配

用法：
  python3 grim_history.py [--limit 20] [--player 名字] [--hours 24] [--kicked-only] [--config]

示例：
  python3 grim_history.py                     # 最近 20 条违规
  python3 grim_history.py --player GrimTest99 # 只看某玩家
  python3 grim_history.py --kicked-only       # 只看被踢的
  python3 grim_history.py --config            # 附带当前处罚配置摘要
"""
import argparse
import gzip
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta

DB = os.path.expanduser("~/minecraft-server/plugins/GrimAC/data/history.v1.db")
LOGS_DIR = os.path.expanduser("~/minecraft-server/logs")
PUNISH = os.path.expanduser("~/minecraft-server/plugins/GrimAC/punishments.yml")
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

# GrimAC 处罚 kick 特征（Essentials 控制台执行 + 处罚文案关键词）
KICK_RE = re.compile(r"CONSOLE issued server command: /kick (\S+) (.*)")
TRIGGER_WORDS = ("作弊", "违规", "数据包", "连点", "战斗", "碰撞箱", "击退", "击杀")

CATEGORY_OF = {
    "grim.prediction.": "Simulation", "grim.groundspoof.": "Simulation", "grim.timer.": "Simulation",
    "grim.velocity.": "Knockback",
    "grim.post.": "Post",
    "grim.badpackets.": "BadPackets", "grim.crash.": "BadPackets", "grim.packetorder.": "BadPackets",
    "grim.combat.hitboxes": "Hitboxes", "grim.combat.reach": "Reach",
    "grim.breaking.": "Misc", "grim.scaffolding.": "Misc", "grim.multiactions.": "Misc",
    "grim.multiinteract.": "Misc", "grim.vehicle.": "Misc", "grim.elytra.": "Misc",
    "grim.sprint.": "Misc", "grim.chat.": "Misc", "grim.exploit.": "Misc",
    "grim.aim.": "Combat",
    "grim.autoclicker.": "Autoclicker",
}


def human_time(ms):
    if not ms:
        return "-"
    return datetime.fromtimestamp(ms / 1000, TZ).strftime("%m-%d %H:%M:%S")


def load_punishment_map():
    """读 punishments.yml → {类别: kick消息}（按缩进层级解析：类别=2空格，kick=6空格）"""
    m = {}
    if not os.path.exists(PUNISH):
        return m
    cur_cat = None
    for line in open(PUNISH, encoding="utf-8"):
        if re.match(r"^  (\w+):", line):          # 类别行（缩进 2）
            cur_cat = line.strip()[:-1]
        elif cur_cat and re.match(r'^      - "\d+:\d+ kick ', line):  # kick 命令（缩进 6）
            m[cur_cat] = line.split("kick", 1)[1].strip().rstrip('",')
    return m


def scan_logs(player, ts_ms, window=10):
    """在日志（latest + 归档）里找该玩家在 ts 前后 window 秒内的 GrimAC kick"""
    player_l = player.lower()
    t_lo, t_hi = ts_ms - window * 1000, ts_ms + window * 1000
    files = []
    if os.path.exists(os.path.join(LOGS_DIR, "latest.log")):
        files.append(os.path.join(LOGS_DIR, "latest.log"))
    files += sorted(
        os.path.join(LOGS_DIR, f) for f in os.listdir(LOGS_DIR) if f.endswith(".log.gz")
    )
    for f in files:
        try:
            lines = gzip.open(f, "rt", errors="replace") if f.endswith(".gz") else open(f, errors="replace")
            with lines as fh:
                for line in fh:
                    m = KICK_RE.search(line)
                    if not m or m.group(1).lower() != player_l:
                        continue
                    if not any(w in m.group(2) for w in TRIGGER_WORDS):
                        continue
                    # 解析日志时间 [HH:MM:SS] → 与 ts 比较（跨天保守匹配：取最近一天内）
                    tm = re.search(r"\[(\d{2}):(\d{2}):(\d{2})\]", line)
                    if not tm:
                        continue
                    h, mi, sec = int(tm.group(1)), int(tm.group(2)), int(tm.group(3))
                    base = datetime.fromtimestamp(ts_ms / 1000, TZ).replace(
                        hour=h, minute=mi, second=sec, microsecond=0
                    )
                    # 若解析时间比违规时间晚 12h+，可能是前一天 → 减一天
                    for cand in (base, base - timedelta(days=1)):
                        if abs(cand.timestamp() * 1000 - ts_ms) <= window * 1000:
                            return m.group(2)
        except Exception:
            continue
    return None


def query(limit, player, hours):
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cur = conn.cursor()
    sql = """
        SELECT p.current_name, c.stable_key, c.display, v.vl, v.occurred_at,
               s.client_brand, s.client_version_pvn
        FROM grim_violations v
        JOIN grim_players p ON v.player_uuid = p.uuid
        JOIN grim_checks c ON v.check_id = c.check_id
        LEFT JOIN grim_sessions s ON v.session_id = s.session_id
    """
    conds, args = [], []
    if player:
        conds.append("LOWER(p.current_name) = LOWER(?)")
        args.append(player)
    if hours:
        conds.append("v.occurred_at >= ?")
        args.append(int((datetime.now(timezone.utc).timestamp() - hours * 3600) * 1000))
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY v.occurred_at DESC LIMIT ?"
    args.append(limit)
    cur.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    return rows


def render(rows, kicked_only):
    out, kicked = [], 0
    for name, key, display, vl, ts, brand, pvn in rows:
        reason = scan_logs(name, ts)
        if kicked_only and not reason:
            continue
        status = f"🔴 踢出（{reason[:36]}）" if reason else "🟡 告警/记录"
        cat = next((v for k, v in CATEGORY_OF.items() if key.startswith(k)), "?")
        out.append(
            f"{human_time(ts)}  {name:<14} {display:<16} VL={vl:<5.0f} {cat:<11} {status}"
        )
        if reason:
            kicked += 1

    print(f"== GrimAC 最近作弊记录（{len(rows)} 条，其中踢出 {kicked} 条）==")
    print(f"{'时间':<17}{'玩家':<16}{'检测':<18}{'VL':<7}{'类别':<13}处理")
    print("-" * 100)
    for line in out:
        print(line)
    if not out:
        print("（无记录）")


def show_config():
    m = load_punishment_map()
    print("\n== 当前处罚配置摘要（punishments.yml）==")
    for cat, msg in m.items():
        print(f"  {cat:<14} → kick 消息: {msg}")


def main():
    ap = argparse.ArgumentParser(description="GrimAC 最近作弊记录查询（含处理方式判定）")
    ap.add_argument("--limit", type=int, default=20, help="显示条数（默认 20）")
    ap.add_argument("--player", help="按玩家名过滤（不区分大小写）")
    ap.add_argument("--hours", type=float, help="只看最近 N 小时（默认全部）")
    ap.add_argument("--kicked-only", action="store_true", help="只看被踢出的记录")
    ap.add_argument("--config", action="store_true", help="附带当前处罚配置摘要")
    args = ap.parse_args()

    # 被踢过滤需后处理，多拉一些再筛
    fetch = args.limit * 5 if args.kicked_only else args.limit
    rows = query(fetch, args.player, args.hours)
    render(rows, args.kicked_only)
    if args.config:
        show_config()


if __name__ == "__main__":
    main()
