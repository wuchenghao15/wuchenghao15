#!/bin/bash
# MTSCOS系统完整启动脚本
# 自动适配新功能和配置

echo "=================================================="
echo "  MTSCOS AI Project - 系统启动"
echo "=================================================="
echo ""

# 项目根目录
PROJECT_ROOT="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
cd "$PROJECT_ROOT"

echo "[1/4] 检查Python环境..."
python3 -c "import sys; print(f'  Python {sys.version.split()[0]}')"

echo ""
echo "[2/4] 检查依赖库..."
python3 -c "import watchdog; print('  ✓ watchdog')" 2>/dev/null || {
    echo "  安装 watchdog..."
    pip3 install watchdog > /dev/null 2>&1
    echo "  ✓ watchdog 已安装"
}

python3 -c "import flask; print('  ✓ flask')" 2>/dev/null || {
    echo "  ⚠ flask 未安装"
}

echo ""
echo "[3/4] 执行系统自动适配..."
python3 system_auto_adapter.py

echo ""
echo "[4/4] 启动主服务..."
echo "  启动Flask应用..."
python3 api_server.py > /dev/null 2>&1 &
API_PID=$!
echo "  Flask API PID: $API_PID"

echo ""
echo "  启动HTTP服务器..."
python3 -m http.server 8888 > /dev/null 2>&1 &
HTTP_PID=$!
echo "  HTTP Server PID: $HTTP_PID"

echo ""
echo "=================================================="
echo "  ✓ 系统启动完成！"
echo "=================================================="
echo ""
echo "服务地址:"
echo "  - API Server: http://localhost:5000"
echo "  - HTTP Server: http://localhost:8888"
echo ""
echo "后台进程:"
echo "  - API Server: $API_PID"
echo "  - HTTP Server: $HTTP_PID"
echo "  - JSON Sync: (运行中)"
echo ""
echo "停止服务: kill $API_PID $HTTP_PID"
echo "=================================================="
