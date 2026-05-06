#!/bin/bash

# MTSCOS AI 项目停止脚本
# 停止所有运行的服务

echo "🛑 MTSCOS AI 项目停止脚本"
echo "===================================="

# 停止 MTSCOS AI 启动器
if [ -f ".mtscos_ai_launcher.pid" ]; then
    LAUNCHER_PID=$(cat .mtscos_ai_launcher.pid)
    echo "🚀 停止 MTSCOS AI 启动器，PID: $LAUNCHER_PID"
    kill $LAUNCHER_PID 2>/dev/null
    rm -f .mtscos_ai_launcher.pid
    echo "✅ MTSCOS AI 启动器已停止"
else
    echo "⚠️ MTSCOS AI 启动器 PID 文件不存在"
fi

# 停止 Python 服务器
if [ -f ".python.pid" ]; then
    PYTHON_PID=$(cat .python.pid)
    echo "🐍 停止 Python 服务器，PID: $PYTHON_PID"
    kill $PYTHON_PID 2>/dev/null
    rm -f .python.pid
    echo "✅ Python 服务器已停止"
else
    echo "⚠️ Python 服务器 PID 文件不存在"
fi

# 停止 Node.js 服务器
if [ -f ".node.pid" ]; then
    NODE_PID=$(cat .node.pid)
    echo "📡 停止 Node.js 服务器，PID: $NODE_PID"
    kill $NODE_PID 2>/dev/null
    rm -f .node.pid
    echo "✅ Node.js 服务器已停止"
else
    echo "⚠️ Node.js 服务器 PID 文件不存在"
fi

# 清理临时文件
echo "🧹 清理临时文件..."

# 检查是否还有进程在运行
echo "🔍 检查服务状态..."

# 检查 MTSCOS AI 启动器进程
LAUNCHER_PROCS=$(ps aux | grep "mtscos_ai_launcher.py" | grep -v grep | wc -l)
if [ $LAUNCHER_PROCS -gt 0 ]; then
    echo "⚠️ 仍有 MTSCOS AI 启动器进程在运行"
    ps aux | grep "mtscos_ai_launcher.py" | grep -v grep
else
    echo "✅ 所有 MTSCOS AI 启动器进程已停止"
fi

# 检查 Python 进程
PYTHON_PROCS=$(ps aux | grep "src/python/server.py" | grep -v grep | wc -l)
if [ $PYTHON_PROCS -gt 0 ]; then
    echo "⚠️ 仍有 Python 进程在运行"
    ps aux | grep "src/python/server.py" | grep -v grep
else
    echo "✅ 所有 Python 进程已停止"
fi

# 检查 Node.js 进程
NODE_PROCS=$(ps aux | grep "src/app.js" | grep -v grep | wc -l)
if [ $NODE_PROCS -gt 0 ]; then
    echo "⚠️ 仍有 Node.js 进程在运行"
    ps aux | grep "src/app.js" | grep -v grep
else
    echo "✅ 所有 Node.js 进程已停止"
fi

# 检查监控服务进程
MONITOR_PROCS=$(ps aux | grep "src/monitoring/monitor.js" | grep -v grep | wc -l)
if [ $MONITOR_PROCS -gt 0 ]; then
    echo "⚠️ 仍有监控服务进程在运行"
    ps aux | grep "src/monitoring/monitor.js" | grep -v grep
else
    echo "✅ 所有监控服务进程已停止"
fi

echo "===================================="
echo "✅ 所有服务已停止！"
echo "===================================="
