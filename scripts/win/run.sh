#!/usr/bin/env bash
# 在远程 Windows 真机（ssh host: win）上执行 PowerShell。
# 自动用 -EncodedCommand(base64/UTF-16LE) 绕过 bash→ssh→PowerShell 的引号与 `&` 陷阱
# （win 默认 shell 是 PowerShell，`&` 会被当作后台运算符）。
#
# 用法:
#   scripts/win/run.sh -c 'Get-PSDrive E | Select-Object Used,Free'
#   scripts/win/run.sh -f scripts/win/verify-download.ps1
#   echo 'Get-Date' | scripts/win/run.sh
#
# 约定: 所有验证产物放在收敛工作根 E:\orzmc-verify\（bin/ minecraft/ tmp/ logs/）。
#       清理: scripts/win/run.sh -c 'Remove-Item -Recurse -Force E:\orzmc-verify'
#       ⚠️ E:\orzmc 是生产部署目录（caddy/cloudflared/database/mcsmanager），不要动。
set -euo pipefail

HOST="${ORZMC_WIN_HOST:-win}"

case "${1:-}" in
  -c) src="${2:?需要 PowerShell 字符串}" ;;
  -f) src="$(cat "${2:?需要脚本路径}")" ;;
  "") src="$(cat)" ;;
  -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
  *) echo "用法: $0 -c '<ps>' | -f <file.ps1> | (stdin)" >&2; exit 2 ;;
esac

prelude='$ProgressPreference="SilentlyContinue";[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);'
enc="$(printf '%s' "$prelude$src" | python3 -c 'import sys,base64;print(base64.b64encode(sys.stdin.buffer.read().decode("utf-8").encode("utf-16-le")).decode())')"
exec ssh -o BatchMode=yes "$HOST" "powershell -NoProfile -EncodedCommand $enc"
