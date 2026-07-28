#!/bin/bash
# MTSCOS AI System - 启动所有后台服务
# 支持启动Flask应用、Git同步、自动备份、影子节点等后台服务

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

PYTHON="python3"

echo "========================================"
echo "  MTSCOS AI System - 启动所有后台服务"
echo "========================================"

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
                kill -9 "$pid" 2>/dev/null
            fi
        fi
        rm -f "$pid_file"
    fi
}

start_service() {
    local service_name=$1
    local script_path=$2
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo "  启动 $service_name..."
    
    stop_service "$service_name"
    
    cd "$PROJECT_DIR"
    nohup "$PYTHON" "$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "    ✓ $service_name 启动成功 (PID: $pid)"
    else
        echo "    ✗ $service_name 启动失败"
        rm -f "$pid_file"
    fi
}

start_module() {
    local service_name=$1
    local class_name=$2
    local module_path=$3
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo "  启动 $service_name..."
    
    stop_service "$service_name"
    
    cd "$PROJECT_DIR"
    nohup "$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from $module_path import $class_name
service = $class_name()
if hasattr(service, 'start'):
    service.start()
else:
    logging.info('$class_name has no start method, initialized only')
" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "    ✓ $service_name 启动成功 (PID: $pid)"
    else
        echo "    ✓ $service_name 初始化完成 (无需后台运行)"
        rm -f "$pid_file"
    fi
}

echo ""
echo "[1] 启动Flask主应用..."
start_service "flask_app" "app.py"

echo ""
echo "[2] 启动自动调度器..."
start_service "auto_scheduler" "auto_scheduler.py"

echo ""
echo "[3] 启动后台服务模块..."

start_module "git_auto_sync" "GitAutoSync" "app.git_auto_sync"
start_module "auto_backup" "AutoBackupService" "app.auto_backup_service"
start_module "shadow_node" "ShadowNodeManager" "app.shadow_node_manager"
start_module "operation_recorder" "OperationRecorder" "app.operation_recorder"
start_module "gray_release" "GrayReleaseService" "app.gray_release_service"
start_module "checkpoint" "CheckpointService" "app.checkpoint_service"
start_module "history_data" "HistoryDataService" "app.history_data_service"

echo ""
echo "========================================"
echo "  后台服务启动完成"
echo "========================================"
echo ""
echo "运行中的服务:"
echo "----------------------------------------"
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        service_name=$(basename "$pid_file" .pid)
        if kill -0 "$pid" 2>/dev/null; then
            echo "  ✓ $service_name (PID: $pid)"
        else
            echo "  ✗ $service_name (未运行)"
            rm -f "$pid_file"
        fi
    fi
done

echo ""
echo "日志目录: $LOG_DIR"
echo "PID目录: $PID_DIR"
echo ""
echo "停止服务: ./stop_all.sh"
echo "查看状态: ./status.sh"