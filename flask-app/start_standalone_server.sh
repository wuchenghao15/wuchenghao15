#!/bin/bash

# 完全独立的服务器启动脚本
echo "[独立服务器启动脚本] 开始启动完全独立的服务器..."

# 设置工作目录
cd "$(dirname "$0")"

echo "[独立服务器启动脚本] 当前工作目录: $(pwd)"

# 杀掉可能占用端口的进程
echo "[独立服务器启动脚本] 检查并杀掉可能占用端口8888的进程..."
PORT=8888
PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "[独立服务器启动脚本] 发现占用端口$PORT的进程: $PID，正在杀掉..."
    kill -9 $PID 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[独立服务器启动脚本] 成功杀掉占用端口$PORT的进程"
    else
        echo "[独立服务器启动脚本] 杀掉进程失败，可能需要管理员权限"
    fi
else
    echo "[独立服务器启动脚本] 端口$PORT未被占用"
fi

# 设置环境变量
export FLASK_SKIP_DOTENV=1

# 直接启动服务器，不使用复杂的环境变量
echo "[独立服务器启动脚本] 正在启动完全独立的服务器..."
echo "[独立服务器启动脚本] 启动命令: nohup python3 standalone_server.py > standalone_server.log 2>&1 &"

# 启动服务器
nohup python3 standalone_server.py > standalone_server.log 2>&1 &

# 等待3秒，确保服务器有足够时间启动
sleep 3

# 检查服务器是否成功启动
PORT=8888
PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "[独立服务器启动脚本] 完全独立的服务器已成功启动，进程ID: $PID"
    echo "[独立服务器启动脚本] 服务器日志: standalone_server.log"
    echo "[独立服务器启动脚本] 服务器访问地址: http://127.0.0.1:$PORT"
    echo "[独立服务器启动脚本] 健康检查地址: http://127.0.0.1:$PORT/health"
    echo "[独立服务器启动脚本] 服务器启动成功！"
    echo "[独立服务器启动脚本] 支持的路由:"
    echo "  - http://127.0.0.1:$PORT/ (首页)"
    echo "  - http://127.0.0.1:$PORT/auth/login (登录页)"
    echo "  - http://127.0.0.1:$PORT/auth/register (注册页)"
    echo "  - http://127.0.0.1:$PORT/auth/logout (登出)"
    echo "[独立服务器启动脚本] 注意：这是一个完全独立的服务器，不依赖复杂的AI组件，适合简单测试和演示。"
else
    echo "[独立服务器启动脚本] 服务器启动失败，请查看日志: standalone_server.log"
    cat standalone_server.log
    exit 1
fi