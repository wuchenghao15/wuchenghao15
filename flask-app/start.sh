
#!/bin/bash
# MTSCOS AI Project - 启动脚本
# 支持单节点和集群模式

set -e

echo "=========================================="
echo "MTSCOS AI Project - 启动脚本"
echo "=========================================="

# 检查是否安装了Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "用法: $0 [模式] [选项]"
    echo
    echo "模式:"
    echo "  start           启动单节点模式（默认）"
    echo "  start-cluster   启动集群模式（3节点）"
    echo "  stop            停止服务"
    echo "  stop-cluster    停止集群服务"
    echo "  restart         重启服务"
    echo "  restart-cluster 重启集群服务"
    echo "  logs            查看服务日志"
    echo "  status          查看服务状态"
    echo "  build           重新构建镜像"
    echo "  clean           清理所有数据"
    echo "  help            显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 start                     # 启动单节点服务"
    echo "  $0 start-cluster             # 启动集群服务"
    echo "  $0 logs -f                   # 实时查看日志"
    echo "  $0 status                    # 查看服务状态"
}

# 获取命令参数
COMMAND=${1:-help}

# 处理命令
case "$COMMAND" in
    start)
        echo "启动 MTSCOS AI Project (单节点模式)..."
        
        # 创建必要的目录
        mkdir -p data logs ssl backups redis-data
        
        # 如果SSL目录为空，生成自签名证书
        if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
            echo "生成自签名SSL证书..."
            openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365 -subj "/CN=localhost"
        fi
        
        # 启动单节点服务
        docker-compose up -d
        
        echo "服务启动完成！"
        echo "访问地址: https://localhost"
        echo "API地址: https://localhost/api"
        echo "健康检查: https://localhost/health"
        ;;
    
    start-cluster)
        echo "启动 MTSCOS AI Project (集群模式)..."
        
        # 创建必要的目录
        mkdir -p data logs ssl backups redis-data postgres-data prometheus/data grafana/data
        
        # 如果SSL目录为空，生成自签名证书
        if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
            echo "生成自签名SSL证书..."
            openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365 -subj "/CN=localhost"
        fi
        
        # 启动集群服务（3节点 + 负载均衡）
        docker-compose -f docker-compose.cluster.yml up -d
        
        echo "集群服务启动完成！"
        echo "访问地址: https://localhost"
        echo "API地址: https://localhost/api"
        echo "健康检查: https://localhost/health"
        echo "Prometheus: http://localhost:9090"
        echo "Grafana: http://localhost:3000"
        echo "节点列表: mtscos-app-1, mtscos-app-2, mtscos-app-3"
        ;;
    
    stop)
        echo "停止 MTSCOS AI Project (单节点模式)..."
        docker-compose down
        echo "服务已停止"
        ;;
    
    stop-cluster)
        echo "停止 MTSCOS AI Project (集群模式)..."
        docker-compose -f docker-compose.cluster.yml down
        echo "集群服务已停止"
        ;;
    
    restart)
        echo "重启 MTSCOS AI Project (单节点模式)..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    restart-cluster)
        echo "重启 MTSCOS AI Project (集群模式)..."
        $0 stop-cluster
        sleep 2
        $0 start-cluster
        ;;
    
    logs)
        echo "查看服务日志..."
        if [ -f "docker-compose.cluster.yml" ]; then
            docker-compose -f docker-compose.cluster.yml logs ${@:2}
        else
            docker-compose logs ${@:2}
        fi
        ;;
    
    status)
        echo "查看服务状态..."
        if [ -f "docker-compose.cluster.yml" ]; then
            docker-compose -f docker-compose.cluster.yml ps
        else
            docker-compose ps
        fi
        ;;
    
    build)
        echo "重新构建镜像..."
        docker-compose build --no-cache
        echo "镜像构建完成"
        ;;
    
    clean)
        echo "警告: 此操作将删除所有数据！"
        read -p "确定要继续吗? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "停止服务..."
            docker-compose down -v
            docker-compose -f docker-compose.cluster.yml down -v 2>/dev/null || true
            echo "删除数据目录..."
            rm -rf data/ logs/ ssl/ backups/ redis-data/ postgres-data/ prometheus/ grafana/
            echo "清理完成"
        else
            echo "操作已取消"
        fi
        ;;
    
    help)
        show_help
        ;;
    
    *)
        echo "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac

echo "=========================================="
