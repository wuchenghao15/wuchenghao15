#!/bin/bash
# MTSCOS AI System - 统一管理脚本
# 用法: ./mtscos.sh [start|stop|status|restart|help]

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
PID_DIR="$PROJECT_DIR/pids"
PYTHON_PATH="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"

# 服务列表
SERVICES=("flask_app" "auto_scheduler" "git_auto_sync" "auto_backup" "shadow_node" "operation_recorder" "gray_release" "checkpoint" "history_data")

show_help() {
    echo "========================================"
    echo "  MTSCOS AI System - 统一管理脚本"
    echo "========================================"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start    启动所有服务"
    echo "  stop     停止所有服务"
    echo "  status   查看服务状态"
    echo "  restart  重启所有服务"
    echo "  help     显示此帮助信息"
    echo ""
}

# 启动Flask应用
start_flask() {
    echo "[启动] Flask应用..."
    pkill -f "/Library/Developer/CommandLineTools/.*Python.*app.py" 2>/dev/null || true
    sleep 2
    nohup $PYTHON_PATH "$PROJECT_DIR/app.py" > /tmp/mtscos_app.log 2>&1 &
    local flask_pid=$!
    mkdir -p "$PID_DIR"
    echo "$flask_pid" > "$PID_DIR/flask_app.pid"
    echo "  Flask进程PID: $flask_pid"

    # 等待启动完成
    local wait_count=0
    while [ $wait_count -lt 60 ]; do
        if curl -s http://localhost:8888/api/server-time > /dev/null 2>&1; then
            echo "  ✓ Flask应用已启动"
            return 0
        fi
        wait_count=$((wait_count + 1))
        sleep 1
    done
    echo "  ✗ Flask应用启动超时"
    echo "  查看日志: cat /tmp/mtscos_app.log"
    return 1
}

# 停止单个服务
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  停止 $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                echo "    强制终止..."
                kill -9 "$pid" 2>/dev/null
            fi
            echo "    ✓ 已停止"
        else
            echo "  $service_name 未运行"
        fi
        rm -f "$pid_file"
    else
        echo "  $service_name 未启动"
    fi
}

# 停止所有服务
stop_all() {
    echo "========================================"
    echo "  停止所有服务"
    echo "========================================"
    for svc in "${SERVICES[@]}"; do
        stop_service "$svc"
    done
    # 额外停止Flask进程
    pkill -f "/Library/Developer/CommandLineTools/.*Python.*app.py" 2>/dev/null || true
    echo ""
    echo "========================================"
    echo "  所有服务已停止"
    echo "========================================"
}

# 启动所有服务
start_all() {
    echo "========================================"
    echo "  启动所有服务"
    echo "========================================"
    start_flask
    echo ""
    echo "运行中的服务:"
    echo "  - Flask应用: http://localhost:8888"
    echo "  - VersionAgentAI: 系统版本管理"
    echo "  - AutomationPlanAgent: 自动化计划拓展"
    echo ""
    echo "查看日志: cat /tmp/mtscos_app.log"
}

# 查看状态
show_status() {
    echo "========================================"
    echo "  MTSCOS AI System - 服务状态"
    echo "========================================"
    echo ""

    running_count=0
    total_count=0

    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            total_count=$((total_count + 1))
            pid=$(cat "$pid_file")
            service_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                running_count=$((running_count + 1))
                echo "  ✓ $service_name (PID: $pid)"
            else
                echo "  ✗ $service_name (PID: $pid - 已停止)"
            fi
        fi
    done

    if [ $total_count -eq 0 ]; then
        echo "  没有运行中的服务"
    else
        echo ""
        echo "  运行中: $running_count / $total_count"
    fi

    echo ""
    echo "Flask应用状态:"
    if curl -s http://localhost:8888/api/system/monitor/status > /dev/null 2>&1; then
        echo "  ✓ Flask应用运行正常 (端口8888)"
    else
        echo "  ✗ Flask应用未运行"
    fi
    echo ""
    echo "========================================"
}

# 主逻辑
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    restart)
        stop_all
        echo ""
        sleep 2
        start_all
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
