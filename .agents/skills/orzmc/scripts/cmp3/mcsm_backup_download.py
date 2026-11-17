#!/usr/bin/env python3
"""MCSM：备份 + 下载所有待修改配置文件（修改前快照）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
BACKUP = os.environ.get("MCSM_BACKUP_DIR", "/tmp/mcsm_backup")
os.makedirs(BACKUP, exist_ok=True)

FILES = [
    "server.properties",
    "spigot.yml",
    "config/paper-global.yml",
    "plugins/Essentials/config.yml",
    "plugins/ViaVersion/config.yml",
    "plugins/OrzMC/templates.yml",
    "plugins/DeathChest/config.yml",
    "plugins/LoginSecurity/config.yml",
    "Start.bat",
]

for path in FILES:
    data = mcsm_download(cfg, f"/{path}")
    if data is None:
        print(f"❌ {path}: 下载失败")
        continue
    # 判断是否为文本（非 jar 魔数）
    if data[:2] == b"PK":
        print(f"⚠️  {path}: 返回 jar 数据？跳过")
        continue
    text = data.decode("utf-8", errors="replace")
    # 保存到备份目录（保留目录结构）
    local = os.path.join(BACKUP, path.replace("/", "_"))
    open(local, "w", encoding="utf-8").write(text)
    print(f"✅ {path}: {len(text)}B → {local}")
    time.sleep(2)

print(f"\n备份目录: {BACKUP}")
