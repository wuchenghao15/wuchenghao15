#!/bin/bash

# 启动所有服务的脚本

# 设置工作目录
cd "$(dirname "$0")"

# 输出带时间戳的日志
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

log "开始启动MTSCOS AI系统服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    log "错误: Python 3 未安装"
    exit 1
fi

# 检查是否有虚拟环境
if [ -d "venv" ]; then
    log "使用虚拟环境"
    VENV_ACTIVATE="venv/bin/activate"
else
    log "未找到虚拟环境，使用系统Python"
    VENV_ACTIVATE=""
fi

# 启动服务管理脚本
log "启动服务管理脚本"
if [ -n "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE"
    nohup python3 -m app.services.service_manager > service_manager.log 2>&1 &
else
    nohup python3 -m app.services.service_manager > service_manager.log 2>&1 &
fi

# 等待服务管理器启动
sleep 3

# 启动Flask应用
log "启动Flask应用"
if [ -n "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE"
    nohup python3 app.py > flask_app.log 2>&1 &
else
    nohup python3 app.py > flask_app.log 2>&1 &
fi

# 记录进程ID
log "记录进程ID"
ps aux | grep -E "(service_manager|app.py)" | grep -v grep > process_ids.log

log "所有服务启动完成！"
log "服务日志："
log "- 服务管理器: service_manager.log"
log "- Flask应用: flask_app.log"
log "- 进程ID: process_ids.log"

# 显示当前运行的服务
log "当前运行的服务："
ps aux | grep -E "(service_manager|app.py)" | grep -v grep
