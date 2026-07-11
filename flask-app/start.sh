#!/bin/bash
# MTSCOS AI 系统启动脚本

cd "$(dirname "$0")"

PYTHON_PATH="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"

echo "========================================"
echo "MTSCOS AI 系统启动脚本"
echo "========================================"

echo ""
echo "[1/3] 停止现有进程..."
pkill -f "/Library/Developer/CommandLineTools/.*Python.*app.py" 2>/dev/null || true
sleep 2
echo "      已停止所有app.py进程"

echo ""
echo "[2/3] 启动Flask应用..."
nohup $PYTHON_PATH app.py > /tmp/mtscos_app.log 2>&1 &
FLASK_PID=$!
echo "      Flask进程PID: $FLASK_PID"

echo ""
echo "[3/3] 等待启动完成..."
MAX_WAIT=60
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8888/api/server-time > /dev/null 2>&1; then
        echo "      ✓ Flask应用已启动成功!"
        echo "      访问地址: http://localhost:8888"
        break
    fi
    WAIT_COUNT=$((WAIT_COUNT + 1))
    sleep 1
    if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
        echo "      ✗ Flask应用启动超时!"
        echo "      查看日志: cat /tmp/mtscos_app.log"
        exit 1
    fi
done

echo ""
echo "========================================"
echo "系统启动完成!"
echo "========================================"
echo ""
echo "运行中的服务:"
echo "  - Flask应用: http://localhost:8888"
echo "  - VersionAgentAI: 系统版本管理"
echo "  - AutomationPlanAgent: 自动化计划拓展"
echo ""
echo "查看启动日志: cat /tmp/mtscos_app.log"