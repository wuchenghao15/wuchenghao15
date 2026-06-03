#!/bin/bash
set -euo pipefail

# MTSCOS 系统初始化脚本
# 用于系统首次启动时的配置和设置

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
LOG_FILE="logs/init.log"
DATABASE_PATH="mtscos.db"
VERSION_FILE="VERSION"
ENV_FILE=".env"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# 确保日志目录存在
mkdir -p logs

# 函数：打印消息
print_message() {
    local level="$1"
    local message="$2"
    local color

    case "$level" in
        "info") color=$BLUE ;;
        "success") color=$GREEN ;;
        "warning") color=$YELLOW ;;
        "error") color=$RED ;;
        *) color=$NC ;;
    esac

    echo -e "${color}[${level}]${NC} ${message}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}" >> "$LOG_FILE"
}

# 函数：检查命令是否存在
check_command() {
    local cmd="$1"
    local desc="${2:-$1}"
    if ! command -v "$cmd" &>/dev/null; then
        print_message "error" "$desc 未安装，请先安装"
        exit 1
    fi
}

# 函数：检查系统环境
check_environment() {
    print_message "info" "检查系统环境..."

    # 检查Python版本
    check_command "python3" "Python 3"
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_message "success" "Python 已安装: $PYTHON_VERSION"

    # 检查端口
    if lsof -i:8888 >/dev/null 2>&1; then
        print_message "warning" "端口 8888 已被占用"
    else
        print_message "success" "端口 8888 可用"
    fi

    # 检查目录结构
    print_message "info" "检查目录结构..."

    # 确保必要的目录存在
    local dirs=(
        "frontend/assets/css/page_styles"
        "frontend/assets/js"
        "frontend/assets/images"
        "frontend/components"
        "frontend/pages"
        "data"
        "backups"
        "docs"
        "logs"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done

    print_message "success" "目录结构检查完成"

    return 0
}

# 函数：初始化数据库
initialize_database() {
    print_message "info" "初始化数据库..."

    local db_manager="database_manager.py"
    
    if [ ! -f "$db_manager" ]; then
        print_message "error" "数据库管理器文件不存在: $db_manager"
        return 1
    fi

    print_message "info" "运行数据库管理器..."
    
    if ! python3 "$db_manager" >> "$LOG_FILE" 2>&1; then
        print_message "error" "数据库初始化失败，请查看日志: $LOG_FILE"
        return 1
    fi

    print_message "success" "数据库初始化成功"
    return 0
}

# 函数：创建必要的文件
create_files() {
    print_message "info" "创建必要的文件..."

    # 创建版本文件
    if [ ! -f "$VERSION_FILE" ]; then
        echo "1.0.0" > "$VERSION_FILE"
        print_message "success" "创建版本文件: 1.0.0"
    else
        print_message "info" "版本文件已存在"
    fi

    # 创建环境配置文件
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# MTSCOS 配置
PORT=8888
HOST=0.0.0.0
DATABASE=mtscos.db
EOF
        print_message "success" "创建环境配置文件"
    else
        print_message "info" "环境配置文件已存在"
    fi

    # 创建前端页面目录
    mkdir -p frontend/pages
    print_message "success" "文件创建完成"
}

# 函数：设置权限
set_permissions() {
    print_message "info" "设置文件权限..."

    # 设置脚本执行权限
    local scripts=(
        "start_server.sh"
        "start.sh"
        "start-all.sh"
        "stop-all.sh"
        "cluster_manager.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            chmod +x "$script"
        fi
    done

    print_message "success" "权限设置完成"
}

# 函数：显示系统信息
show_system_info() {
    print_message "info" "系统信息..."

    local version="未知"
    if [ -f "$VERSION_FILE" ]; then
        version=$(cat "$VERSION_FILE")
    fi

    echo -e "${BLUE}==================================${NC}"
    echo -e "${GREEN}MTSCOS 系统初始化完成${NC}"
    echo -e "${BLUE}==================================${NC}"
    echo -e "${YELLOW}系统版本:${NC} $version"
    echo -e "${YELLOW}数据库:${NC} $DATABASE_PATH"
    echo -e "${YELLOW}服务器端口:${NC} 8888"
    echo -e "${YELLOW}访问地址:${NC} http://localhost:8888"
    echo -e "${BLUE}==================================${NC}"

    echo -e "${GREEN}使用方法:${NC}"
    echo -e "  ${YELLOW}./start_server.sh start${NC} - 启动服务器"
    echo -e "  ${YELLOW}./start_server.sh stop${NC} - 停止服务器"
    echo -e "  ${YELLOW}./start_server.sh status${NC} - 查看状态"
    echo -e "  ${YELLOW}./start_server.sh restart${NC} - 重启服务器"
    echo -e "  ${YELLOW}./start_server.sh init${NC} - 初始化数据库"
    echo -e "${BLUE}==================================${NC}"
}

# 函数：显示帮助信息
show_help() {
    echo -e "${GREEN}MTSCOS 系统初始化脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -f, --force     强制重新初始化（覆盖现有配置）"
    echo "  -v, --verbose   详细输出模式"
    echo ""
}

# 主函数
main() {
    local force_init=false
    local verbose=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                force_init=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                print_message "error" "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_message "info" "MTSCOS 系统初始化"
    print_message "info" "=================================="

    # 检查环境
    if ! check_environment; then
        print_message "error" "环境检查失败"
        exit 1
    fi

    # 创建必要的文件
    create_files

    # 初始化数据库
    if [ "$force_init" = true ] || [ ! -f "$DATABASE_PATH" ]; then
        if ! initialize_database; then
            print_message "error" "数据库初始化失败"
            exit 1
        fi
    else
        print_message "info" "数据库已存在，跳过初始化"
    fi

    # 设置权限
    set_permissions

    # 显示系统信息
    show_system_info

    print_message "success" "系统初始化完成"
    print_message "info" "您可以使用 ./start_server.sh start 启动服务器"
}

# 运行主函数
main "$@"