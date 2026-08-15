#!/bin/bash

# 停止所有服务的脚本

# 设置工作目录
cd "$(dirname "$0")"

# 输出带时间戳的日志
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

log "开始停止MTSCOS AI系统服务..."

# 停止Flask应用
log "停止Flask应用"
FLASK_PIDS=$(ps aux | grep "app.py" | grep -v grep | awk '{print $2}')
if [ -n "$FLASK_PIDS" ]; then
    for PID in $FLASK_PIDS; do
        log "停止Flask应用进程: $PID"
        kill -9 $PID
    done
else
    log "Flask应用未运行"
fi

# 停止服务管理器
log "停止服务管理器"
SERVICE_PIDS=$(ps aux | grep "service_manager" | grep -v grep | awk '{print $2}')
if [ -n "$SERVICE_PIDS" ]; then
    for PID in $SERVICE_PIDS; do
        log "停止服务管理器进程: $PID"
        kill -9 $PID
    done
else
    log "服务管理器未运行"
fi

# 清理进程ID文件
if [ -f "process_ids.log" ]; then
    rm process_ids.log
    log "清理进程ID文件"
fi

# 显示当前运行的服务
log "当前运行的服务："
ps aux | grep -E "(service_manager|app.py)" | grep -v grep

log "所有服务停止完成！"
