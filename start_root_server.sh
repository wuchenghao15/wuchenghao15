#!/bin/bash

# 根服务器启动脚本

echo "[根服务器启动脚本] 开始启动根服务器..."

# 设置工作目录
cd "$(dirname "$0")"

echo "[根服务器启动脚本] 当前工作目录: $(pwd)"

# 杀掉可能占用端口的进程
echo "[根服务器启动脚本] 检查并杀掉可能占用端口8888的进程..."
PORT=8888
PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "[根服务器启动脚本] 发现占用端口$PORT的进程: $PID，正在杀掉..."
    kill -9 $PID 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[根服务器启动脚本] 成功杀掉占用端口$PORT的进程"
    else
        echo "[根服务器启动脚本] 杀掉进程失败，可能需要管理员权限"
    fi
else
    echo "[根服务器启动脚本] 端口$PORT未被占用"
fi

# 设置环境变量
export FLASK_SKIP_DOTENV=1
export MODEL_PATH="./models"

echo "[根服务器启动脚本] 正在启动根服务器..."
echo "[根服务器启动脚本] 启动命令: nohup python3 start_server.py --node-role master --node-id root-1 --port 8888 --host 0.0.0.0 > root_server.log 2>&1 &"

# 启动根服务器
nohup python3 start_server.py --node-role master --node-id root-1 --port 8888 --host 0.0.0.0 > root_server.log 2>&1 &

# 等待5秒，确保服务器有足够时间启动
sleep 5

# 检查服务器是否成功启动
PORT=8888
PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "[根服务器启动脚本] 根服务器已成功启动，进程ID: $PID"
    echo "[根服务器启动脚本] 服务器日志: root_server.log"
    echo "[根服务器启动脚本] 根服务器访问地址: http://127.0.0.1:$PORT"
    echo "[根服务器启动脚本] 健康检查地址: http://127.0.0.1:$PORT/health"
    echo "[根服务器启动脚本] AI集群API地址: http://127.0.0.1:$PORT/api/ai-cluster"
    echo "[根服务器启动脚本] 根服务器启动成功！"
else
    echo "[根服务器启动脚本] 根服务器启动失败，请查看日志: root_server.log"
    cat root_server.log
    exit 1
fi