#!/bin/bash

# 确保所有Python进程都被杀死
echo "正在杀死所有Python进程..."
pkill -f 'python3'
sleep 2

# 启动集群节点
echo "正在启动集群节点..."

# 启动节点1（端口8888）
echo "启动节点1 - 端口8888..."
nohup python3 start_server.py --port 8888 --node-id node-1 --node-role worker > server-8888.log 2>&1 &
sleep 2

# 启动节点2（端口8889）
echo "启动节点2 - 端口8889..."
nohup python3 start_server.py --port 8889 --node-id node-2 --node-role worker > server-8889.log 2>&1 &
sleep 2

# 启动节点3（端口8890）
echo "启动节点3 - 端口8890..."
nohup python3 start_server.py --port 8890 --node-id node-3 --node-role worker > server-8890.log 2>&1 &
sleep 5

# 等待所有服务启动
echo "等待服务启动..."
sleep 5

# 测试集群是否成功启动
echo "正在测试集群节点是否成功启动..."

# 测试节点1
curl -s http://localhost:8888/health > /dev/null
if [ $? -eq 0 ]; then
    echo "节点1 (8888): 运行正常"
else
    echo "节点1 (8888): 启动失败"
    exit 1
fi

# 测试节点2
curl -s http://localhost:8889/health > /dev/null
if [ $? -eq 0 ]; then
    echo "节点2 (8889): 运行正常"
else
    echo "节点2 (8889): 启动失败"
    exit 1
fi

# 测试节点3
curl -s http://localhost:8890/health > /dev/null
if [ $? -eq 0 ]; then
    echo "节点3 (8890): 运行正常"
else
    echo "节点3 (8890): 启动失败"
    exit 1
fi

echo "集群启动成功！"
echo "负载均衡地址: http://localhost:80"
echo "各节点地址:"
echo "  - 节点1: http://localhost:8888"
echo "  - 节点2: http://localhost:8889"
echo "  - 节点3: http://localhost:8990"
