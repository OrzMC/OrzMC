#!/usr/bin/env python3
"""MCSM 补拉失败的配置文件（串行，避免并发触发冷却）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

MCSM_OUT = "/tmp/mcsm_configs2"
# 失败清单（从 fetch3.log 提取）
FAILED = [
    "DeathChest/config.yml", "Essentials/config.yml", "Essentials/custom_items.yml",
    "Essentials/upgrades-done.yml", "Essentials/worth.yml", "EzShops/player-shops.yml",
    "EzShops/shop-rotations.yml", "EzShops/shop/prison/categories/daily_specials.yml",
    "EzShops/shop/prison/categories/enchantments.yml", "EzShops/shop/prison/categories/fishing.yml",
    "EzShops/shop/prison/categories/mining.yml", "EzShops/shop/prison/categories/redstone.yml",
    "EzShops/shop/prison/categories/valuables.yml", "EzShops/shop/prison/rotations/daily-specials.yml",
    "EzShops/shop/smp/categories/building.yml", "EzShops/shop/smp/categories/decorations.yml",
    "EzShops/shop/smp/categories/farming.yml", "EzShops/shop/smp/categories/food.yml",
    "EzShops/shop/smp/categories/mob_drops.yml", "EzShops/shop/smp/categories/wood.yml",
    "EzShops/shop/smp/menu.yml", "EzShops/stock-gui.yml", "EzShops/stock-prices.yml",
    "EzShops/transactions.yml", "GetMeHome/config.yml", "GetMeHome/delay.yml",
    "Geyser-Spigot/config.yml", "GriefPreventionData/config.yml", "LoginSecurity/database.yml",
    "LuckPerms/config.yml", "OrzMC/ip_blacklist.yml", "OrzMC/portals.yml", "OrzMC/templates.yml",
    "SkinsRestorer/config.yml", "ViaRewind/config.yml", "ViaVersion/config.yml",
]

cfg = get_mcsm_config()
ok = fail = 0
for rel in FAILED:
    data = mcsm_download(cfg, f"/plugins/{rel}")
    if data is not None and data[:2] != b"PK":
        dst = f"{MCSM_OUT}/plugins/{rel}"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(data)
        print(f"  ✅ {rel} ({len(data)}B)"); ok += 1
    else:
        print(f"  ❌ {rel}"); fail += 1
    time.sleep(3)
print(f"\n补拉完成: ok={ok} fail={fail}")
