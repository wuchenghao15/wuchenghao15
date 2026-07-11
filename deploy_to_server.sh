#!/bin/bash
set -e

SERVER_IP="192.168.31.105"
SERVER_USER="wuchenghao15"
SERVER_PASS="LoginMe.1988$"
PROJECT_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
REMOTE_DIR="/home/wuchenghao15/mtscos_project"
FLASK_PORT="8888"

echo "======================================"
echo "  MTSCOS AI 项目部署脚本"
echo "  目标服务器: ${SERVER_IP}"
echo "======================================"

echo ""
echo "[1/6] 检查远程服务器连接..."
if ping -c 1 -W 3 "$SERVER_IP" > /dev/null; then
    echo "✓ 服务器 ${SERVER_IP} 可访问"
else
    echo "✗ 服务器 ${SERVER_IP} 不可访问，请检查网络连接"
    exit 1
fi

echo ""
echo "[2/6] 创建远程项目目录..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "
    mkdir -p $REMOTE_DIR
    mkdir -p $REMOTE_DIR/flask-app
    echo '目录创建完成'
"

echo ""
echo "[3/6] 传输项目文件到远程服务器..."
echo "正在传输 flask-app 目录..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no -r "$PROJECT_DIR/flask-app/" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

echo "正在传输核心文件..."
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no "$PROJECT_DIR/VERSION" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"
sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no "$PROJECT_DIR/README.md" "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

echo "✓ 文件传输完成"

echo ""
echo "[4/6] 配置远程服务器环境..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "
    export DEBIAN_FRONTEND=noninteractive
    
    echo '更新系统包...'
    sudo apt-get update -y -qq
    
    echo '安装 Python3 和虚拟环境...'
    sudo apt-get install -y -qq python3 python3-venv python3-pip
    
    echo '创建 Python 虚拟环境...'
    rm -rf $REMOTE_DIR/venv
    python3 -m venv $REMOTE_DIR/venv
    
    echo '激活虚拟环境并安装依赖...'
    $REMOTE_DIR/venv/bin/python -m pip install --upgrade pip -q
    $REMOTE_DIR/venv/bin/python -m pip install -r $REMOTE_DIR/flask-app/requirements.txt -q
    
    echo '环境配置完成'
"

echo ""
echo "[5/6] 启动 Flask 服务..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "
    echo '停止可能存在的旧服务...'
    pkill -f 'flask' || true
    pkill -f 'python.*app.py' || true
    sleep 2
    
    echo '启动 Flask 服务...'
    cd $REMOTE_DIR/flask-app
    nohup $REMOTE_DIR/venv/bin/python app.py > $REMOTE_DIR/flask-app/app.log 2>&1 &
    
    sleep 5
    
    echo '检查服务状态...'
    if pgrep -f 'python.*app.py' > /dev/null; then
        echo '✓ Flask 服务已启动'
        echo '日志位置: $REMOTE_DIR/flask-app/app.log'
    else
        echo '✗ Flask 服务启动失败'
        cat $REMOTE_DIR/flask-app/app.log
        exit 1
    fi
"

echo ""
echo "[6/6] 验证服务是否正常运行..."
sleep 3
response=$(sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "curl -s http://localhost:$FLASK_PORT/ -o /dev/null -w '%{http_code}' || echo '000'")

if [ "$response" = "200" ]; then
    echo "✓ 服务验证成功！HTTP状态码: $response"
    echo ""
    echo "======================================"
    echo "  部署完成！"
    echo "======================================"
    echo "项目路径: $REMOTE_DIR"
    echo "服务地址: http://$SERVER_IP:$FLASK_PORT"
    echo "虚拟环境: $REMOTE_DIR/venv"
    echo "日志文件: $REMOTE_DIR/flask-app/app.log"
    echo ""
    echo "管理命令:"
    echo "  查看日志: tail -f $REMOTE_DIR/flask-app/app.log"
    echo "  停止服务: pkill -f 'python.*app.py'"
    echo "  重启服务: cd $REMOTE_DIR/flask-app && nohup $REMOTE_DIR/venv/bin/python app.py > app.log 2>&1 &"
else
    echo "✗ 服务验证失败！HTTP状态码: $response"
    echo "请检查服务日志: $REMOTE_DIR/flask-app/app.log"
    exit 1
fi