#!/bin/bash
# ╔══════════════════════════════════════════════════════════╗
# ║  MTSCOS AI v23.0.0-Andromeda-Nova — 启动/停止脚本         ║
# ║  用法: ./mtscos.sh {start|stop|restart|status|log}       ║
# ╚══════════════════════════════════════════════════════════╝
set -e

# 路径探测优先级:
# 1) DEPLOY_DIR 环境变量显式指定
# 2) mtscos.sh 所在目录 (脚本直接放 DEPLOY_DIR 下)
# 3) $HOME/mtscos 兜底
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -n "${DEPLOY_DIR:-}" ]; then
    DEPLOY_DIR="$DEPLOY_DIR"
elif [ -d "$SCRIPT_DIR/flask-app" ]; then
    DEPLOY_DIR="$SCRIPT_DIR"
elif [ -d "$HOME/mtscos/flask-app" ]; then
    DEPLOY_DIR="$HOME/mtscos"
elif [ -d "$HOME/flask-app" ]; then
    DEPLOY_DIR="$HOME"
else
    DEPLOY_DIR="$SCRIPT_DIR"
fi
APP_DIR="$DEPLOY_DIR/flask-app"
PID_FILE="/tmp/mtscos.pid"
LOG_FILE="/tmp/mtscos.log"
PORT=8888
HOST="0.0.0.0"  # Linux 上必须 0.0.0.0, macOS 可用 '::'
export MTSCOS_SKIP_EF_STARTUP_SCAN=1

# ===== 辅助函数 =====
_venv_activate() {
    # 兼容两种 venv 位置
    if [ -f "$APP_DIR/venv/bin/activate" ]; then
        source "$APP_DIR/venv/bin/activate"
    elif [ -f "$APP_DIR/.venv/bin/activate" ]; then
        source "$APP_DIR/.venv/bin/activate"
    fi
}

_is_running() {
    local pid
    pid=$(_read_pid) || return 1
    kill -0 "$pid" 2>/dev/null
}

_read_pid() {
    if [ -f "$PID_FILE" ]; then
        local p
        p=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$p" ]; then
            echo "$p"
            return 0
        fi
    fi
    # fallback: pgrep
    pgrep -f "server_real_db.*app.run" 2>/dev/null | head -1 || true
}

_listen_port() {
    (ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null) | grep ":${PORT} " | grep -q LISTEN 2>/dev/null
}

# ===== 子命令 =====
cmd_start() {
    if _is_running; then
        local pid=$(_read_pid)
        echo "🟢  MTSCOS AI 已在运行 (PID=$pid)"
        return 0
    fi
    if _listen_port; then
        echo "⚠️  端口 $PORT 被占用, 但 PID 文件没写 — 先 stop 再 start"
        cmd_stop
    fi

    echo "🚀  启动 MTSCOS AI v23.0.0-Andromeda-Nova"
    echo "    目录:   $APP_DIR"
    echo "    监听:   $HOST:$PORT"
    echo "    日志:   $LOG_FILE"

    cd "$APP_DIR"
    _venv_activate

    # 强制 host=0.0.0.0 (绕过 server_real_db.py 里的 host='::' IPv6-only)
    nohup python3 -c "
import server_real_db as srd
srd.app.run(host='$HOST', port=$PORT, threaded=True)
" > "$LOG_FILE" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$PID_FILE"

    # 等待 + 验证
    for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
        sleep 1
        local code
        code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${PORT}/ 2>/dev/null || echo '000')
        if [ "$code" != "000" ]; then
            local ip
            ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
            echo ""
            echo "════════════════════════════════════════════════"
            echo "🎉  启动成功!  PID=$new_pid  HTTP $code"
            echo ""
            echo "🌐  访问:   http://${ip}:${PORT}/"
            echo "📄  日志:   tail -f $LOG_FILE"
            echo "🛑  停止:   $0 stop"
            echo "♻️  重启:   $0 restart"
            echo "════════════════════════════════════════════════"
            return 0
        fi
    done

    # 失败
    echo ""
    echo "❌  启动失败 (12 秒内没响应)"
    echo ""
    echo "最近 30 行日志:"
    tail -30 "$LOG_FILE"
    echo ""
    echo "排查:"
    echo "  1. tail -100 $LOG_FILE"
    echo "  2. ps aux | grep python3"
    echo "  3. ss -tlnp | grep $PORT"
    return 1
}

cmd_stop() {
    local pid
    pid=$(_read_pid) || true
    if [ -z "$pid" ]; then
        echo "🟡  没找到运行中的进程"
        # 清理端口占用
        local pids
        pids=$(lsof -ti :${PORT} 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "    但端口 $PORT 被占用, 清理: $pids"
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 1
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
        return 0
    fi

    echo "🛑  停止 MTSCOS AI (PID=$pid)..."
    kill "$pid" 2>/dev/null || true

    # 优雅关 3s, 强杀
    for i in 1 2 3; do
        sleep 1
        if ! kill -0 "$pid" 2>/dev/null; then
            rm -f "$PID_FILE"
            echo "    ✅ 已停止"
            return 0
        fi
    done
    echo "    强杀..."
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "    ✅ 已停止 (SIGKILL)"
}

cmd_restart() {
    echo "♻️  重启 MTSCOS AI"
    cmd_stop
    sleep 1
    cmd_start
}

cmd_status() {
    local pid=$(_read_pid) || true
    local http="000"
    if [ -n "$pid" ]; then
        http=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${PORT}/ 2>/dev/null || echo '000')
    fi
    local app_exists=$([ -d "$APP_DIR" ] && echo '✅' || echo '❌ 不存在')
    local venv_exists=$([ -f "$APP_DIR/venv/bin/activate" ] && echo '✅' || echo '❌ 没建')
    local db_exists=""
    for candidate in \
        "$DEPLOY_DIR/_runtime/databases/Database/mtscos.db" \
        "$HOME/mtscos/_runtime/databases/Database/mtscos.db" \
        "$APP_DIR/_runtime/databases/Database/mtscos.db"; do
        if [ -f "$candidate" ]; then db_exists="✅ $(ls -lh "$candidate" | awk '{print $5}')"; break; fi
    done
    [ -z "$db_exists" ] && db_exists="❌ 未找到"

    echo "╔══════════════════════════════════════════════╗"
    echo "║  MTSCOS AI v23.0.0-Andromeda-Nova            ║"
    echo "╠══════════════════════════════════════════════╣"
    if [ -z "$pid" ]; then
        echo "║  状态:    ❌ 未运行                           ║"
    else
        echo "║  状态:    🟢 运行中 (HTTP $http)              ║"
        echo "║  PID:     $pid"
    fi
    echo "║  端口:    $PORT ($HOST)"
    echo "║  部署:    $DEPLOY_DIR"
    echo "║  flask-app: $app_exists"
    echo "║  venv:    $venv_exists"
    echo "║  数据库:  $db_exists"
    echo "║  日志:    $LOG_FILE"
    echo "╚══════════════════════════════════════════════╝"
}

cmd_log() {
    echo "📄  tail -f $LOG_FILE  (Ctrl+C 退出)"
    tail -f "$LOG_FILE"
}

# ===== 分发 =====
case "${1:-start}" in
    start|run|up)     cmd_start ;;
    stop|down)        cmd_stop ;;
    restart|reload)   cmd_restart ;;
    status|ps)        cmd_status ;;
    log|logs|tail)    cmd_log ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        echo ""
        echo "  start    启动 (PID 文件: $PID_FILE)"
        echo "  stop     停止 (SIGTERM → SIGKILL)"
        echo "  restart  重启"
        echo "  status   查看状态 + HTTP 健康"
        echo "  log      tail -f 日志"
        exit 1
        ;;
esac