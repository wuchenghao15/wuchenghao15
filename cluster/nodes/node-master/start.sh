#!/bin/bash
# 主节点启动脚本
echo "启动主节点..."
cd /Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
export NODE_ID="node-master"
export NODE_ROLE="master"
export SERVER_PORT=8443
python3 flask-app/start_server.py
