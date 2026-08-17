#!/bin/bash

# 停止所有服务的脚本
# 使用系统守护进程管理器来停止服务

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

log "开始停止MTSCOS AI系统服务..."

# 使用系统守护进程管理器停止服务
log "使用守护进程管理器停止所有服务..."
python3 system_watchdog.py stop

# 清理残留进程
log "清理残留进程..."
for process in "app.py" "service_manager" "ai_agent_service" "ai_cluster_manager" "ai_brain_service"; do
    PIDS=$(ps aux | grep "$process" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        for PID in $PIDS; do
            log "强制停止进程: $PID ($process)"
            kill -9 $PID 2>/dev/null || true
        done
    fi
done

# 清理PID文件
log "清理PID文件..."
rm -rf "$PROJECT_DIR/pids"

# 显示当前运行的服务
log "当前运行的服务："
ps aux | grep -E "(app.py|service_manager|ai_agent)" | grep -v grep || log "没有相关服务在运行"

log "所有服务停止完成！"
