#!/usr/bin/env python3
"""扫描 Bukkit 插件目录下所有 jar 的 plugin.yml，列出 default: true 的权限。

用法: python3 scan_default_perms.py [plugins目录，默认 ~/minecraft-server/plugins]

产出：按插件分组的 default:true 权限清单——这些权限即使 LP 组未显式设置节点，
所有玩家（含 default）实际可用（LP 尊重插件权限默认值）。
注意：WE/WG 等插件权限在代码注册（plugin.yml 无 permissions 段），不在此列。
"""
import zipfile, yaml, os, glob, sys

plugins_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/minecraft-server/plugins')
results = {}
for jar in sorted(glob.glob(os.path.join(plugins_dir, '*.jar'))):
    name = os.path.basename(jar)
    try:
        with zipfile.ZipFile(jar) as z:
            if 'plugin.yml' not in z.namelist():
                continue
            data = yaml.safe_load(z.read('plugin.yml'))
    except Exception:
        continue
    perms = data.get('permissions') or {}
    true_perms = [p for p, pd in perms.items()
                  if isinstance(pd, dict) and pd.get('default') is True]
    if true_perms:
        results[name] = true_perms

for plugin, perms in sorted(results.items()):
    print(f"=== {plugin}（{len(perms)} 个 default:true）===")
    for p in perms:
        print(f"  {p}")
