#!/bin/bash

# 启动根服务器脚本
# 用于启动MTSCOS AI系统的根服务器

echo "[根服务器启动脚本] 正在准备启动根服务器..."

# 检查是否存在配置文件
CONFIG_FILE="root_server_config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "[根服务器启动脚本] 找到配置文件: $CONFIG_FILE"
    echo "[根服务器启动脚本] 使用配置文件启动根服务器..."
    # 复制配置文件到flask-app目录
    cp "$CONFIG_FILE" "flask-app/config.json"
    echo "[根服务器启动脚本] 配置文件已复制到flask-app/config.json"
fi

# 杀死所有Python进程，确保没有其他服务器在运行
echo "[根服务器启动脚本] 正在杀死所有Python进程..."
pkill -f 'python3'
sleep 2

# 进入flask-app目录
echo "[根服务器启动脚本] 进入flask-app目录..."
cd flask-app

# 启动根服务器
echo "[根服务器启动脚本] 正在启动根服务器..."
echo "[根服务器启动脚本] 根服务器将运行在端口8888"
echo "[根服务器启动脚本] 根服务器角色: master"
echo "[根服务器启动脚本] 集群模式: enabled"
echo "[根服务器启动脚本] 调试模式: disabled"

# 使用nohup启动根服务器，并将日志输出到root_server.log
nohup python3 start_server.py --port 8888 --node-id root-node --node-role master > root_server.log 2>&1 &

# 等待服务器启动
echo "[根服务器启动脚本] 等待根服务器启动..."
sleep 10

# 检查服务器是否启动成功
echo "[根服务器启动脚本] 检查根服务器是否启动成功..."
if curl -s http://localhost:8888/health > /dev/null; then
    echo "[根服务器启动脚本] ✅ 根服务器启动成功!"
    echo "[根服务器启动脚本] 根服务器地址: http://localhost:8888"
    echo "[根服务器启动脚本] 健康检查端点: http://localhost:8888/health"
    echo "[根服务器启动脚本] 集群API: http://localhost:8888/api/cluster/status"
    echo "[根服务器启动脚本] 日志文件: flask-app/root_server.log"
    echo "[根服务器启动脚本] 根服务器已成功启动!"
else
    echo "[根服务器启动脚本] ❌ 根服务器启动失败!"
    echo "[根服务器启动脚本] 请检查日志文件: flask-app/root_server.log"
    echo "[根服务器启动脚本] 运行以下命令查看日志: tail -n 100 flask-app/root_server.log"
    exit 1
fi

# 提供使用说明
echo ""
echo "[根服务器启动脚本] 使用说明:"
echo "1. 查看根服务器日志: tail -n 100 flask-app/root_server.log"
echo "2. 停止根服务器: pkill -f 'start_server.py --port 8888'"
echo "3. 检查根服务器状态: curl http://localhost:8888/api/cluster/status"
echo "4. 检查集群节点: curl http://localhost:8888/api/cluster/nodes/healthy"
echo ""
echo "[根服务器启动脚本] 根服务器启动完成!"
