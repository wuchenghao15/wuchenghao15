#!/bin/bash
set -euo pipefail

# MTSCOS AI 集群管理脚本
# 用于管理集群的启动、停止、状态监控等操作

# 配置
FLASK_APP_DIR="flask-app"
START_SCRIPT="start_server.py"
LOG_DIR="logs"

# 集群节点配置
NODES=(
    "8888 node-1 worker"
    "8889 node-2 worker"
    "8890 node-3 worker"
)

# 颜色配置
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# 函数：打印日志
log() {
    echo -e "${BLUE}[CLUSTER MANAGER]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[CLUSTER MANAGER]${NC} $1"
}

log_error() {
    echo -e "${RED}[CLUSTER MANAGER]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[CLUSTER MANAGER]${NC} $1"
}

# 函数：检查命令是否存在
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "命令 $cmd 不存在，请安装后重试"
        exit 1
    fi
}

# 函数：检查进程是否运行
is_process_running() {
    local pid="$1"
    if ps -p "$pid" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：检查端口是否被占用
check_port() {
    local port="$1"
    if lsof -i:"$port" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：获取端口对应的进程PID
get_pid_by_port() {
    local port="$1"
    lsof -ti:"$port" 2>/dev/null | head -1
}

# 初始化
init() {
    log "初始化集群管理脚本..."

    # 检查必要命令
    check_command "python3"
    check_command "curl"
    check_command "pkill"

    # 创建日志目录
    mkdir -p "${FLASK_APP_DIR}/${LOG_DIR}"

    log_success "初始化完成"
}

# 启动集群
start_cluster() {
    log "正在启动集群..."

    # 检查Flask应用目录
    if [ ! -d "$FLASK_APP_DIR" ]; then
        log_error "Flask应用目录不存在: $FLASK_APP_DIR"
        exit 1
    fi

    # 检查启动脚本是否存在
    if [ ! -f "${FLASK_APP_DIR}/${START_SCRIPT}" ]; then
        log_warning "启动脚本不存在: ${FLASK_APP_DIR}/${START_SCRIPT}"
        log_warning "将使用 Python HTTP 服务器作为备用"
    fi

    # 停止现有服务
    log "正在停止现有服务..."
    stop_cluster

    # 进入Flask应用目录
    cd "$FLASK_APP_DIR" || { log_error "无法进入Flask应用目录"; exit 1; }

    # 启动每个节点
    for node in "${NODES[@]}"; do
        read -r port node_id node_role <<< "$node"
        
        # 检查端口是否被占用
        if check_port "$port"; then
            log_warning "端口 $port 已被占用，尝试停止占用进程"
            local pid=$(get_pid_by_port "$port")
            if [ -n "$pid" ]; then
                kill "$pid" 2>/dev/null || true
                sleep 1
            fi
        fi

        log "启动节点 $node_id - 端口 $port..."
        
        if [ -f "$START_SCRIPT" ]; then
            nohup python3 "$START_SCRIPT" --port "$port" --node-id "$node_id" --node-role "$node_role" > "${LOG_DIR}/server-${port}.log" 2>&1 &
        else
            nohup python3 -m http.server "$port" > "${LOG_DIR}/server-${port}.log" 2>&1 &
        fi
        
        sleep 2
    done

    # 等待服务启动
    log "等待服务启动..."
    sleep 5

    # 测试集群是否成功启动
    test_cluster

    log_success "集群启动完成！"
}

# 停止集群
stop_cluster() {
    log "正在停止集群..."

    # 杀死所有相关Python进程
    local pids
    pids=$(pgrep -f "python3.*server" 2>/dev/null)
    if [ -n "$pids" ]; then
        kill $pids 2>/dev/null || true
        sleep 2
        
        # 检查是否还有进程
        pids=$(pgrep -f "python3.*server" 2>/dev/null)
        if [ -n "$pids" ]; then
            log_warning "强制终止剩余进程"
            kill -9 $pids 2>/dev/null || true
        fi
    fi

    log_success "集群已停止"
}

# 重启集群
restart_cluster() {
    log "正在重启集群..."
    stop_cluster
    start_cluster
}

# 查看集群状态
status_cluster() {
    log "正在检查集群状态..."

    local all_healthy=true

    for node in "${NODES[@]}"; do
        read -r port node_id node_role <<< "$node"
        log "检查节点 $node_id - 端口 $port..."

        # 检查节点是否正在运行
        if check_port "$port"; then
            local pid=$(get_pid_by_port "$port")
            # 测试健康状态
            if curl -s -f http://localhost:"$port"/health >/dev/null 2>&1; then
                log_success "节点 $node_id (${port}): 运行正常, PID: $pid"
            else
                log_error "节点 $node_id (${port}): 端口占用但健康检查失败, PID: $pid"
                all_healthy=false
            fi
        else
            log_error "节点 $node_id (${port}): 未运行"
            all_healthy=false
        fi
    done

    # 检查负载均衡器
    log "检查负载均衡器状态..."
    if check_port 80; then
        log_success "负载均衡器 (80): 运行正常"
    else
        log_warning "负载均衡器 (80): 未运行"
        log_warning "请确保Nginx已正确配置并启动"
    fi

    if [ "$all_healthy" = true ]; then
        log_success "集群状态: 健康"
    else
        log_error "集群状态: 不健康，部分节点存在问题"
    fi
}

# 测试集群
test_cluster() {
    log "正在测试集群节点是否成功启动..."

    local all_passed=true

    for node in "${NODES[@]}"; do
        read -r port node_id node_role <<< "$node"
        
        local max_retries=3
        local retry_count=0
        
        while [ $retry_count -lt $max_retries ]; do
            if curl -s -f http://localhost:"$port"/health >/dev/null 2>&1; then
                log_success "节点 $node_id (${port}): 运行正常"
                break
            fi
            ((retry_count++))
            sleep 2
        done

        if [ $retry_count -ge $max_retries ]; then
            log_error "节点 $node_id (${port}): 启动失败"
            all_passed=false
        fi
    done

    if [ "$all_passed" = true ]; then
        log_success "集群测试通过！"
        log_success "负载均衡地址: http://localhost:80"
        log "各节点地址:"
        for node in "${NODES[@]}"; do
            read -r port node_id node_role <<< "$node"
            log "  - $node_id: http://localhost:${port}"
        done
    else
        log_error "集群测试未通过，部分节点启动失败"
        exit 1
    fi
}

# 查看集群日志
tail_logs() {
    log "正在查看集群日志..."

    cd "$FLASK_APP_DIR" || { log_error "无法进入Flask应用目录"; exit 1; }

    for node in "${NODES[@]}"; do
        read -r port node_id node_role <<< "$node"
        log "=== 节点 $node_id (${port}) 日志 ==="
        if [ -f "${LOG_DIR}/server-${port}.log" ]; then
            tail -n 20 "${LOG_DIR}/server-${port}.log"
        else
            log_warning "日志文件不存在: ${LOG_DIR}/server-${port}.log"
        fi
        echo ""
    done
}

# 添加节点
add_node() {
    log "添加节点功能开发中..."
}

# 移除节点
remove_node() {
    log "移除节点功能开发中..."
}

# 显示帮助
show_help() {
    echo -e "${GREEN}MTSCOS AI 集群管理脚本${NC}"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start      启动集群"
    echo "  stop       停止集群"
    echo "  restart    重启集群"
    echo "  status     查看集群状态"
    echo "  test       测试集群连接"
    echo "  logs       查看集群日志"
    echo "  add        添加节点（开发中）"
    echo "  remove     移除节点（开发中）"
    echo "  help       显示帮助信息"
    echo ""
}

# 主函数
main() {
    init

    case "${1:-}" in
        start)
            start_cluster
            ;;
        stop)
            stop_cluster
            ;;
        restart)
            restart_cluster
            ;;
        status)
            status_cluster
            ;;
        test)
            test_cluster
            ;;
        logs)
            tail_logs
            ;;
        add)
            add_node
            ;;
        remove)
            remove_node
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            show_help
            exit 1
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"