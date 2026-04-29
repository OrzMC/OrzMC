#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/compose.yaml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "未找到 compose 文件: $COMPOSE_FILE" >&2
    exit 1
fi

source_image_for_service() {
    case "$1" in
        reverse-proxy) echo "caddy:2-alpine" ;;
        mcsmanager-web) echo "githubyumao/mcsmanager-web:latest" ;;
        mcsmanager-daemon) echo "githubyumao/mcsmanager-daemon:latest" ;;
        napcat) echo "mlikiowa/napcat-docker:latest" ;;
        *)
            return 1
            ;;
    esac
}

if [ "$#" -eq 0 ]; then
    SERVICES=("reverse-proxy" "mcsmanager-web" "mcsmanager-daemon" "napcat")
else
    SERVICES=("$@")
fi

for service in "${SERVICES[@]}"; do
    if ! source_image_for_service "$service" >/dev/null; then
        echo "不支持的服务名: $service" >&2
        echo "可选服务: reverse-proxy mcsmanager-web mcsmanager-daemon napcat" >&2
        exit 1
    fi
done

for service in "${SERVICES[@]}"; do
    image_ref="$(source_image_for_service "$service")"
    echo "拉取镜像: ${service} -> ${image_ref}"
    docker pull "$image_ref" >/dev/null
done

python3 - "$COMPOSE_FILE" "${SERVICES[@]}" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

compose_file = Path(sys.argv[1])
services = sys.argv[2:]
source_images = {
    "reverse-proxy": "caddy:2-alpine",
    "mcsmanager-web": "githubyumao/mcsmanager-web:latest",
    "mcsmanager-daemon": "githubyumao/mcsmanager-daemon:latest",
    "napcat": "mlikiowa/napcat-docker:latest",
}

text = compose_file.read_text()
updated = text
changes = []

for service in services:
    image_ref = source_images[service]
    digests = subprocess.check_output(
        [
            "docker",
            "image",
            "inspect",
            image_ref,
            "--format",
            "{{join .RepoDigests \"\\n\"}}",
        ],
        text=True,
    ).strip().splitlines()
    if not digests:
        raise SystemExit(f"未找到镜像摘要: {image_ref}")

    repo = image_ref.split(":")[0]
    digest_ref = next((item for item in digests if item.startswith(repo + "@")), digests[0])

    pattern = rf"(^  {re.escape(service)}:\n(?:    .*\n)*?    image: ).*$"
    match = re.search(pattern, updated, flags=re.MULTILINE)
    if not match:
        raise SystemExit(f"未在 compose.yaml 中找到服务: {service}")

    old_line = match.group(0).splitlines()[-1].strip()
    updated = re.sub(pattern, rf"\1{digest_ref}", updated, count=1, flags=re.MULTILINE)
    changes.append((service, old_line.removeprefix("image: ").strip(), digest_ref))

compose_file.write_text(updated)

for service, old, new in changes:
    state = "未变化" if old == new else "已更新"
    print(f"{service}: {state}")
    print(f"  old: {old}")
    print(f"  new: {new}")
PY

echo
echo "摘要更新完成。建议下一步执行："
echo "  git diff -- deploy/docker/compose.yaml"
echo "  git add deploy/docker/compose.yaml && git commit -m 'chore: update docker image digests'"
echo "  docker compose --env-file .env.local up -d"
