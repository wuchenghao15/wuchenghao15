#!/bin/bash
# 工作节点1启动脚本
echo "启动工作节点1..."
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
export NODE_ID="node-worker-1"
export NODE_ROLE="worker"
export SERVER_PORT=8444
python3 flask-app/start_server.py
