#!/bin/bash
# 负载均衡器启动脚本
echo "启动负载均衡器..."

cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project

# 设置环境变量
export LOAD_BALANCER_PORT=8080
export LOAD_BALANCER_ALGORITHM=round_robin

# 启动负载均衡器
python3 cluster/load_balancer.py &

echo "负载均衡器已启动"
echo "监听端口: $LOAD_BALANCER_PORT"
echo "算法: $LOAD_BALANCER_ALGORITHM"
echo "API地址: http://localhost:${LOAD_BALANCER_PORT}/api/load-balancer"
