#!/bin/bash

# 系统守护进程启动脚本
# 用于启动系统守护进程管理器，自动监控和重启服务

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
PID_DIR="$PROJECT_DIR/pids"
WATCHDOG_PID_FILE="$PID_DIR/watchdog.pid"

log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

# 检查是否已运行
if [ -f "$WATCHDOG_PID_FILE" ]; then
    pid=$(cat "$WATCHDOG_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        log "系统守护进程已在运行 (PID: $pid)"
        exit 0
    else
        log "发现僵尸PID文件，正在清理..."
        rm -f "$WATCHDOG_PID_FILE"
    fi
fi

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

# 创建PID目录
mkdir -p "$PID_DIR"

# 启动守护进程
log "启动系统守护进程..."
cd "$PROJECT_DIR"
nohup python3 system_watchdog.py start > watchdog.log 2>&1 &

# 等待启动
sleep 2

# 检查是否启动成功
if [ -f "$WATCHDOG_PID_FILE" ]; then
    pid=$(cat "$WATCHDOG_PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        log "系统守护进程启动成功 (PID: $pid)"
        log "日志文件: watchdog.log"
        log "运行状态: python3 system_watchdog.py status"
        exit 0
    fi
fi

log "系统守护进程启动失败"
exit 1
