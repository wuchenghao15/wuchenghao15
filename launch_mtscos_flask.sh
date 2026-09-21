#!/bin/bash
# ──────────────────────────────────────────────────────────────
# com.mtscos.server8888  launcher (给 launchd 调用)
# ------------------------------------------------------------------
# macOS launchd 守护化 Flask HTTP Server (modular_start.py)
# 特性:
#   - 退出码 2 = 永久失败不重启 (SECURE mode)
#   - 退出码 其他 = KeepAlive 自动重启
#   - OLLAMA_HOST=11435 (正确端口)
#   - 绝对路径, 不依赖 CWD 猜测
# ──────────────────────────────────────────────────────────────

set -uo pipefail

PROJECT_ROOT="$HOME/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
FLASK_DIR="$PROJECT_ROOT/flask-app"
PYTHON="/opt/homebrew/bin/python3"
SCRIPT="$FLASK_DIR/modular_start.py"
LOG_DIR="$PROJECT_ROOT/_runtime/logs"

# 环境变量 (launchd 进程环境和交互式 shell 不同, 显式配好)
export OLLAMA_HOST="http://localhost:11435"
export PYTHONIOENCODING="utf-8"
export MTSCOS_SKIP_EF_STARTUP_SCAN="1"
export MTSCOS_SERVER_PORT="8888"
export MTSCOS_BIND_HOST="::"

# Ollama 健康检查 (3s 超时) — 没起来就等它, 不盲目启动 Flask
for attempt in 1 2 3 4 5; do
    if curl -s --max-time 3 http://localhost:11435/api/tags >/dev/null 2>&1; then
        break
    fi
    echo "[launcher] Ollama not ready, waiting 5s (attempt $attempt/5)" >> "$LOG_DIR/launchd_server8888.stderr.log"
    sleep 5
done

# 端口 8888 已被占? 杀掉残留 (launchd 重启时可能有僵尸)
if lsof -ti :8888 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[launcher] Port 8888 occupied, killing residual..." >> "$LOG_DIR/launchd_server8888.stderr.log"
    lsof -ti :8888 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 切到 flask-app 目录跑 modular_start.py
cd "$FLASK_DIR"
echo "[launcher] START $(date '+%Y-%m-%d %H:%M:%S') python=$PYTHON script=$SCRIPT" >> "$LOG_DIR/launchd_server8888.stderr.log"

exec "$PYTHON" -u "$SCRIPT"
# launchd 托管后进程不退出; 退出码由 KeepAlive 处理
