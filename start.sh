#!/bin/bash
set -euo pipefail

# MTSCOS AI 项目统一启动脚本
# 管理所有服务的启动和配置

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
LOG_DIR="Logs"
PID_FILE=".mtscos_ai_launcher.pid"
LAUNCHER_SCRIPT="mtscos_ai_launcher.py"
LOG_FILE="${LOG_DIR}/mtscos_ai_launcher.log"

# 服务配置
MAIN_PORT=8080
PYTHON_PORT=8082
MONITOR_PORT=8083

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

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
}

# 函数：检查命令是否存在
check_command() {
    local cmd="$1"
    local desc="${2:-$1}"
    if ! command -v "$cmd" &>/dev/null; then
        print_message "error" "$desc 未安装"
        exit 1
    fi
}

# 函数：检查进程是否运行
is_process_running() {
    local pid="$1"
    if ps -p "$pid" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：检查端口是否被占用
check_port() {
    local port="$1"
    if lsof -i:"$port" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：显示帮助信息
show_help() {
    echo -e "${GREEN}MTSCOS AI 项目统一启动脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -s, --stop      停止服务"
    echo "  -r, --restart   重启服务"
    echo "  -S, --status    查看服务状态"
    echo ""
}

# 函数：停止服务
stop_service() {
    print_message "info" "停止 MTSCOS AI 启动器..."

    if [ ! -f "$PID_FILE" ]; then
        print_message "warning" "PID文件不存在，检查是否有进程在运行"
        
        # 尝试查找Python启动器进程
        local pid=$(pgrep -f "$LAUNCHER_SCRIPT" 2>/dev/null | head -1)
        if [ -n "$pid" ]; then
            print_message "info" "发现进程，PID: $pid"
            kill "$pid" 2>/dev/null || true
            sleep 2
            if ! pgrep -f "$LAUNCHER_SCRIPT" >/dev/null 2>&1; then
                print_message "success" "服务已停止"
                return 0
            else
                print_message "error" "无法停止服务进程"
                return 1
            fi
        fi
        
        print_message "warning" "服务未运行"
        return 1
    fi

    local pid=$(cat "$PID_FILE")

    if is_process_running "$pid"; then
        kill "$pid"
        sleep 2
        
        if is_process_running "$pid"; then
            print_message "warning" "强制终止进程"
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        rm "$PID_FILE"
        print_message "success" "服务已停止，PID: $pid"
        return 0
    else
        print_message "warning" "PID文件存在但进程不存在"
        rm "$PID_FILE"
        return 1
    fi
}

# 函数：显示服务状态
show_status() {
    print_message "info" "服务状态检查..."

    local is_running=false
    local pid=""

    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if is_process_running "$pid"; then
            is_running=true
        else
            print_message "warning" "PID文件存在但进程不存在"
            rm "$PID_FILE"
        fi
    else
        pid=$(pgrep -f "$LAUNCHER_SCRIPT" 2>/dev/null | head -1)
        if [ -n "$pid" ]; then
            is_running=true
        fi
    fi

    if [ "$is_running" = true ]; then
        print_message "success" "服务运行中，PID: $pid"
        
        echo ""
        echo -e "${BLUE}端口状态:${NC}"
        for port in $MAIN_PORT $PYTHON_PORT $MONITOR_PORT; do
            if check_port "$port"; then
                print_message "success" "端口 $port: 已占用"
            else
                print_message "warning" "端口 $port: 未占用"
            fi
        done
    else
        print_message "warning" "服务未运行"
    fi
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--stop)
                stop_service
                exit 0
                ;;
            -r|--restart)
                stop_service
                sleep 1
                ;;
            -S|--status)
                show_status
                exit 0
                ;;
            *)
                print_message "error" "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done

    print_message "info" "🚀 MTSCOS AI 项目启动脚本"
    print_message "info" "===================================="

    # 检查 Python 是否安装
    check_command "python3" "Python 3"

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 显示服务配置
    echo ""
    print_message "info" "📋 服务配置:"
    echo -e "${BLUE}--------------------------------${NC}"
    echo -e "${YELLOW}主服务器:${NC} http://localhost:${MAIN_PORT}"
    echo -e "${YELLOW}Python服务器:${NC} http://localhost:${PYTHON_PORT}"
    echo -e "${YELLOW}监控服务:${NC} http://localhost:${MONITOR_PORT}"

    # 显示统一入口
    echo ""
    print_message "info" "🔗 统一入口:"
    echo -e "${BLUE}--------------------------------${NC}"
    echo -e "${YELLOW}维护入口:${NC} http://localhost:${MAIN_PORT}/api/health"
    echo -e "${YELLOW}后台入口:${NC} http://localhost:${PYTHON_PORT}/python/dashboard"
    echo -e "${YELLOW}检测入口:${NC} http://localhost:${MONITOR_PORT}/api/health"
    echo -e "${YELLOW}调试入口:${NC} http://localhost:${MAIN_PORT}/api/health"
    echo -e "${YELLOW}API接入入口:${NC} http://localhost:${MAIN_PORT}/api/auth"
    echo -e "${YELLOW}AI入口:${NC} http://localhost:${PYTHON_PORT}/python/api/ai"

    # 停止现有服务
    if [ -f "$PID_FILE" ]; then
        print_message "warning" "检测到已有服务运行，先停止..."
        stop_service
        sleep 1
    fi

    # 启动主启动器
    echo ""
    print_message "info" "🚀 启动 MTSCOS AI 多线程后台启动器..."

    # 进入项目根目录
    cd "$SCRIPT_DIR"

    # 检查启动器脚本是否存在
    if [ ! -f "$LAUNCHER_SCRIPT" ]; then
        print_message "warning" "启动器脚本不存在: $LAUNCHER_SCRIPT"
        print_message "info" "将使用 Python HTTP 服务器作为备用启动方式..."
        python3 -m http.server "$MAIN_PORT" >> "$LOG_FILE" 2>&1 &
    else
        nohup python3 "$LAUNCHER_SCRIPT" > "$LOG_FILE" 2>&1 &
    fi

    # 保存 PID
    echo $! > "$PID_FILE"

    # 等待服务启动
    local max_wait=5
    local wait_count=0
    while [ $wait_count -lt $max_wait ]; do
        local pid=$(cat "$PID_FILE")
        if is_process_running "$pid"; then
            break
        fi
        sleep 1
        ((wait_count++))
    done

    # 验证启动是否成功
    local pid=$(cat "$PID_FILE")
    if is_process_running "$pid"; then
        echo ""
        print_message "success" "✅ MTSCOS AI 多线程后台启动器已启动!"
        echo ""
        print_message "info" "📊 系统状态检查:"
        echo -e "${BLUE}--------------------------------${NC}"
        echo -e "${YELLOW}启动器日志:${NC} ${LOG_FILE}"
        echo ""
        print_message "info" "🎯 访问入口:"
        echo -e "${BLUE}--------------------------------${NC}"
        echo -e "${YELLOW}首页:${NC} http://localhost:${MAIN_PORT}/html/index.html"
        echo -e "${YELLOW}后台管理:${NC} http://localhost:${PYTHON_PORT}/python/dashboard"
        echo -e "${YELLOW}监控面板:${NC} http://localhost:${MONITOR_PORT}/api/monitor/clients"
        echo ""
        print_message "info" "💡 提示: 使用 '$0 -s' 或 './stop-all.sh' 停止所有服务"
    else
        print_message "error" "❌ 服务启动失败，请查看日志: ${LOG_FILE}"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 运行主函数
main "$@"