#!/bin/bash
# 启动整个集群
echo "启动MTSCOS集群..."

# 启动主节点
echo "启动主节点..."
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cluster/nodes/node-master
bash start.sh &
sleep 3

# 启动工作节点1
echo "启动工作节点1..."
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cluster/nodes/node-worker-1
bash start.sh &
sleep 2

# 启动工作节点2
echo "启动工作节点2..."
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/cluster/nodes/node-worker-2
bash start.sh &

echo "集群启动完成！"
echo "主节点: http://localhost:8443"
echo "工作节点1: http://localhost:8444"
echo "工作节点2: http://localhost:8445"
