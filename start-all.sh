#!/bin/bash

# MTSCOS AI 项目启动脚本
# 同时启动 Node.js 服务器和 Python 服务器

echo "🚀 MTSCOS AI 项目启动脚本"
echo "===================================="

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python 3 未安装"
    exit 1
fi

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装"
    exit 1
fi

# 创建日志目录
mkdir -p Logs

echo "📁 准备启动服务..."

# 启动 Python 服务器
echo "🐍 启动 Python 服务器..."
python3 src/python/server.py > Logs/python-server.log 2>&1 &
PYTHON_PID=$!
echo "✅ Python 服务器已启动，PID: $PYTHON_PID"

# 等待 Python 服务器启动
sleep 2

# 启动 Node.js 服务器
echo "📡 启动 Node.js 服务器..."
node src/app.js > Logs/node-server.log 2>&1 &
NODE_PID=$!
echo "✅ Node.js 服务器已启动，PID: $NODE_PID"

# 等待服务器启动
sleep 3

echo "===================================="
echo "📋 服务启动状态"
echo "===================================="
echo "🐍 Python 服务器: http://localhost:8081"
echo "📡 Node.js 服务器: http://localhost:8080"
echo "===================================="
echo "🔍 健康检查地址:"
echo "   - Node.js: http://localhost:8080/api/health"
echo "   - Python: http://localhost:8081/python/api/health"
echo "===================================="
echo "📁 日志文件:"
echo "   - Node.js: Logs/node-server.log"
echo "   - Python: Logs/python-server.log"
echo "   - Python 错误: Logs/python-server-error.log"
echo "===================================="
echo "✅ 所有服务启动完成！"

# 保存 PID 到文件
echo $PYTHON_PID > .python.pid
echo $NODE_PID > .node.pid

echo "📝 PID 文件已保存"
echo "   - Python PID: .python.pid"
echo "   - Node PID: .node.pid"
echo "===================================="
echo "💡 提示: 使用 ./stop-all.sh 停止所有服务"
