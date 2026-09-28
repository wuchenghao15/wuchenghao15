#!/bin/bash
# 仙女座后台状态页 — 一键启动 + 自动守护
PORT=8889
RUN_DIR="$HOME/.mtscos/run"
mkdir -p "$RUN_DIR"
PID_FILE="$RUN_DIR/andromeda_status_page.pid"
APP_DIR="$(cd "$(dirname "$0")/flask-app" && pwd)"
WATCHDOG_LOG="$RUN_DIR/status_watchdog.log"
STATUS_OUT="$RUN_DIR/andromeda_status.out.log"
STATUS_ERR="$RUN_DIR/andromeda_status.err.log"

check() {
    local pid=$(cat $PID_FILE 2>/dev/null)
    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        echo "✅ 状态页 PID=$pid 端口=$PORT"
        return 0
    fi
    echo "❌ 状态页没在跑"
    [ -f $PID_FILE ] && rm -f $PID_FILE
    return 1
}

stop() {
    local pid=$(cat $PID_FILE 2>/dev/null)
    [ -n "$pid" ] && kill $pid 2>/dev/null && sleep 1 && kill -9 $pid 2>/dev/null
    rm -f $PID_FILE
    lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
    echo "✅ 已停"
}

start() {
    # 清旧
    local old=$(cat $PID_FILE 2>/dev/null)
    [ -n "$old" ] && kill -0 $old 2>/dev/null && kill -9 $old 2>/dev/null
    lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
    rm -f $PID_FILE
    sleep 0.5
    
    # 启动 (set -e 关闭, 避免错误退出)
    set +e
    cd "$APP_DIR" || return 1
    nohup python3 -u engines/andromeda_status_page.py > "$STATUS_OUT" 2> "$STATUS_ERR" &
    local newpid=$!
    echo $newpid > $PID_FILE
    disown $newpid 2>/dev/null
    
    sleep 2
    if kill -0 $newpid 2>/dev/null; then
        echo "[$(date +%H:%M:%S)] ✅ 启动 PID=$newpid 端口=$PORT" >> $WATCHDOG_LOG
        return 0
    else
        echo "[$(date +%H:%M:%S)] ❌ 启动失败" >> $WATCHDOG_LOG
        tail -3 "$STATUS_ERR" >> $WATCHDOG_LOG
        return 1
    fi
}

watch() {
    # 守护模式: 每 5s 检查, 死了自动拉
    # 关键: trap + 脱离终端, 避免被 SIGTERM/SIGHUP 带走
    trap '' SIGTERM SIGHUP SIGINT
    echo "[$(date +%H:%M:%S)] 👁️ 守护启动 (check_interval=5s)" >> $WATCHDOG_LOG
    
    while true; do
        local pid=$(cat $PID_FILE 2>/dev/null)
        if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
            # 死了, 看看是真死还是 pid_file 脏
            local port_pid=$(lsof -ti:$PORT 2>/dev/null | head -1)
            if [ -z "$port_pid" ]; then
                echo "[$(date +%H:%M:%S)] 💥 检测到崩溃 → 重启" >> $WATCHDOG_LOG
                start
            else
                # 端口还在但 pid_file 脏, 修正
                echo $port_pid > $PID_FILE
            fi
        fi
        sleep 5
    done
}

case "${1:-start}" in
    check) check ;;
    stop) stop ;;
    start) start ;;
    watch) watch ;;
    *) echo "usage: $0 [start|check|stop|watch]"; exit 1 ;;
esac
