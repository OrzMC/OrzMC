#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
LOCAL_PROJECT_ROOT="${REPO_ROOT}/deploy/docker"
ENV_TEMPLATE_FILE="${SCRIPT_DIR}/.env.local.example"
ENV_FILE="${SCRIPT_DIR}/.env.local"
COMPOSE_FILE="${SCRIPT_DIR}/compose.yaml"

ensure_env_file() {
    if [ ! -f "$ENV_TEMPLATE_FILE" ]; then
        echo "模板文件不存在: $ENV_TEMPLATE_FILE" >&2
        exit 1
    fi

    sed "s#<LOCAL_PROJECT_ROOT>#${LOCAL_PROJECT_ROOT}#g" "$ENV_TEMPLATE_FILE" > "$ENV_FILE"
}

read_env_value() {
    local key="$1"
    grep "^${key}=" "$ENV_FILE" | cut -d '=' -f 2-
}

ensure_data_dirs() {
    local data_root
    data_root="$(read_env_value DATA_ROOT)"

    if [ -z "$data_root" ]; then
        echo "无法从 .env.local 读取 DATA_ROOT" >&2
        exit 1
    fi

    mkdir -p \
        "${data_root}/caddy/data" \
        "${data_root}/caddy/config" \
        "${data_root}/mcsmanager/web/data" \
        "${data_root}/mcsmanager/web/logs" \
        "${data_root}/mcsmanager/daemon/data" \
        "${data_root}/mcsmanager/daemon/logs" \
        "${data_root}/napcat/qq" \
        "${data_root}/napcat/config" \
        "${data_root}/napcat/plugins" \
        "${data_root}/instances/papermc-main/server" \
        "${data_root}/instances/papermc-main/backups"
}

print_access_info() {
    local domain_mcs_web domain_qqbot https_port
    domain_mcs_web="$(read_env_value DOMAIN_MCS_WEB)"
    domain_qqbot="$(read_env_value DOMAIN_QQBOT)"
    https_port="$(read_env_value PROXY_HTTPS_PORT)"

    echo "访问地址:"
    echo "MCSManager Web: https://${domain_mcs_web}:${https_port}"
    echo "NapCat WebUI: https://${domain_qqbot}:${https_port}"
}

compose_cmd() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

cmd_init() {
    ensure_env_file
    ensure_data_dirs
    echo "已生成本地配置文件: $ENV_FILE"
    echo "使用的仓库路径: $LOCAL_PROJECT_ROOT"
    echo "已初始化本地数据目录: $(read_env_value DATA_ROOT)"
}

cmd_start() {
    cmd_init
    compose_cmd up -d
    echo "本地服务已启动"
    print_access_info
}

cmd_stop() {
    ensure_env_file
    compose_cmd down --remove-orphans
    echo "本地服务已停止并清理容器与网络"
    echo "已保留本地数据目录和 .env.local"
}

cmd_status() {
    ensure_env_file
    print_access_info
    echo
    echo "容器状态:"
    compose_cmd ps
}

usage() {
    cat <<'EOF'
用法:
  ./local.sh init
  ./local.sh start
  ./local.sh stop
  ./local.sh status
EOF
}

case "${1:-}" in
    init)
        cmd_init
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    *)
        usage
        exit 1
        ;;
esac
