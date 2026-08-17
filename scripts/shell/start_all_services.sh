#!/bin/bash

# 启动所有服务的脚本
# 使用系统守护进程管理器来监控和管理服务

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

log "开始启动MTSCOS AI系统服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    log "错误: Python 3 未安装"
    exit 1
fi

# 检查psutil
if ! python3 -c "import psutil" &> /dev/null; then
    log "安装 psutil..."
    pip3 install psutil
fi

# 停止可能正在运行的服务
log "停止现有服务..."
python3 system_watchdog.py stop 2>/dev/null || true
sleep 3

# 启动系统守护进程
log "启动系统守护进程管理器..."
bash start_watchdog.sh

# 等待服务启动
log "等待服务启动..."
sleep 5

# 显示服务状态
log "服务状态:"
python3 system_watchdog.py status

log "系统服务启动完成！"
log "守护进程日志: watchdog.log"
log "查看状态: python3 system_watchdog.py status"
log "停止服务: python3 system_watchdog.py stop"
