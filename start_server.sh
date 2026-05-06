#!/bin/bash

# MTSCOS 优化启动脚本
# 增强版启动脚本，支持数据库初始化、系统检查和服务管理
# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
PORT=8888
HOST=0.0.0.0
DATABASE_PATH="mtscos.db"
LOG_FILE="logs/server.log"

# 确保日志目录存在
mkdir -p logs

# 函数：打印消息
print_message() {
    local level=$1
    local message=$2
    local color
    
    case $level in
        "info") color=$BLUE ;;
        "success") color=$GREEN ;;
        "warning") color=$YELLOW ;;
        "error") color=$RED ;;
        *) color=$NC ;;
    esac
    
    echo -e "${color}[${level}]${NC} ${message}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}" >> "$LOG_FILE"
}

# 函数：检查数据库
check_database() {
    print_message "info" "检查数据库状态..."
    
    if [ -f "$DATABASE_PATH" ]; then
        print_message "success" "数据库文件存在"
        return 0
    else
        print_message "warning" "数据库文件不存在，需要初始化"
        return 1
    fi
}

# 函数：初始化数据库
initialize_database() {
    print_message "info" "初始化数据库..."
    
    if [ -f "database_manager.py" ]; then
        print_message "info" "运行数据库管理器..."
        python3 database_manager.py >> "$LOG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            print_message "success" "数据库初始化成功"
            return 0
        else
            print_message "error" "数据库初始化失败"
            return 1
        fi
    else
        print_message "error" "数据库管理器文件不存在"
        return 1
    fi
}

# 函数：检查端口
check_port() {
    print_message "info" "检查端口 $PORT..."
    
    if lsof -i:$PORT > /dev/null 2>&1; then
        print_message "warning" "端口 $PORT 已被占用"
        return 1
    else
        print_message "success" "端口 $PORT 可用"
        return 0
    fi
}

# 函数：启动服务器
start_server() {
    print_message "info" "启动服务器在 ${HOST}:${PORT}..."
    
    # 启动Python内置服务器
    python3 -m http.server $PORT --bind $HOST >> "$LOG_FILE" 2>&1 &
    
    SERVER_PID=$!
    print_message "success" "服务器已启动，PID: $SERVER_PID"
    
    # 保存PID到文件
    echo $SERVER_PID > "server.pid"
    
    # 等待服务器启动
    sleep 2
    
    # 验证服务器是否运行
    if ps -p $SERVER_PID > /dev/null; then
        print_message "success" "服务器运行正常"
        print_message "info" "访问地址: http://${HOST}:${PORT}"
        return 0
    else
        print_message "error" "服务器启动失败"
        return 1
    fi
}

# 函数：停止服务器
stop_server() {
    print_message "info" "停止服务器..."
    
    if [ -f "server.pid" ]; then
        SERVER_PID=$(cat "server.pid")
        
        if ps -p $SERVER_PID > /dev/null; then
            kill $SERVER_PID
            print_message "success" "服务器已停止，PID: $SERVER_PID"
            rm "server.pid"
            return 0
        else
            print_message "warning" "服务器PID文件存在但进程不存在"
            rm "server.pid"
            return 1
        fi
    else
        print_message "warning" "服务器PID文件不存在"
        return 1
    fi
}

# 函数：重启服务器
restart_server() {
    print_message "info" "重启服务器..."
    
    stop_server
    sleep 1
    start_server
}

# 函数：显示状态
show_status() {
    print_message "info" "服务器状态..."
    
    if [ -f "server.pid" ]; then
        SERVER_PID=$(cat "server.pid")
        
        if ps -p $SERVER_PID > /dev/null; then
            print_message "success" "服务器运行中，PID: $SERVER_PID"
            print_message "info" "访问地址: http://${HOST}:${PORT}"
        else
            print_message "error" "服务器PID文件存在但进程不存在"
            rm "server.pid"
        fi
    else
        print_message "warning" "服务器未运行"
    fi
    
    # 检查数据库状态
    check_database
}

# 主函数
main() {
    print_message "info" "MTSCOS 服务器管理"
    print_message "info" "=================================="
    
    case $1 in
        "start")
            # 检查端口
            if ! check_port; then
                print_message "error" "端口检查失败"
                exit 1
            fi
            
            # 检查并初始化数据库
            if ! check_database; then
                if ! initialize_database; then
                    print_message "error" "数据库初始化失败"
                    exit 1
                fi
            fi
            
            # 启动服务器
            start_server
            ;;
            
        "stop")
            stop_server
            ;;
            
        "restart")
            restart_server
            ;;
            
        "status")
            show_status
            ;;
            
        "init")
            initialize_database
            ;;
            
        *)
            echo -e "${YELLOW}用法:${NC} $0 {start|stop|restart|status|init}"
            echo -e "${BLUE}选项:${NC}"
            echo -e "  start   - 启动服务器"
            echo -e "  stop    - 停止服务器"
            echo -e "  restart - 重启服务器"
            echo -e "  status  - 显示服务器状态"
            echo -e "  init    - 初始化数据库"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"