#!/bin/bash
set -euo pipefail

# MTSCOS AI 项目启动脚本
# 同时启动 Node.js 服务器和 Python 服务器

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
LOG_DIR="Logs"
PYTHON_PID_FILE=".python.pid"
NODE_PID_FILE=".node.pid"
PYTHON_LOG_FILE="${LOG_DIR}/python-server.log"
NODE_LOG_FILE="${LOG_DIR}/node-server.log"

# 服务端口配置
PYTHON_PORT=8081
NODE_PORT=8080

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

# 函数：停止服务
stop_services() {
    print_message "info" "停止所有服务..."

    # 停止 Python 服务器
    if [ -f "$PYTHON_PID_FILE" ]; then
        local python_pid=$(cat "$PYTHON_PID_FILE")
        if is_process_running "$python_pid"; then
            kill "$python_pid" 2>/dev/null || true
            sleep 1
            if is_process_running "$python_pid"; then
                kill -9 "$python_pid" 2>/dev/null || true
            fi
        fi
        rm "$PYTHON_PID_FILE"
    fi

    # 停止 Node.js 服务器
    if [ -f "$NODE_PID_FILE" ]; then
        local node_pid=$(cat "$NODE_PID_FILE")
        if is_process_running "$node_pid"; then
            kill "$node_pid" 2>/dev/null || true
            sleep 1
            if is_process_running "$node_pid"; then
                kill -9 "$node_pid" 2>/dev/null || true
            fi
        fi
        rm "$NODE_PID_FILE"
    fi

    print_message "success" "所有服务已停止"
}

# 函数：显示服务状态
show_status() {
    print_message "info" "服务状态检查..."

    echo -e "${BLUE}===================================${NC}"
    echo -e "${YELLOW}服务状态${NC}"
    echo -e "${BLUE}===================================${NC}"

    # 检查 Python 服务器
    if [ -f "$PYTHON_PID_FILE" ]; then
        local pid=$(cat "$PYTHON_PID_FILE")
        if is_process_running "$pid"; then
            print_message "success" "Python 服务器: 运行中, PID: $pid"
            echo -e "${YELLOW}地址:${NC} http://localhost:${PYTHON_PORT}"
        else
            print_message "warning" "Python 服务器: PID文件存在但进程不存在"
            rm "$PYTHON_PID_FILE"
        fi
    else
        print_message "warning" "Python 服务器: 未运行"
    fi

    # 检查 Node.js 服务器
    if [ -f "$NODE_PID_FILE" ]; then
        local pid=$(cat "$NODE_PID_FILE")
        if is_process_running "$pid"; then
            print_message "success" "Node.js 服务器: 运行中, PID: $pid"
            echo -e "${YELLOW}地址:${NC} http://localhost:${NODE_PORT}"
        else
            print_message "warning" "Node.js 服务器: PID文件存在但进程不存在"
            rm "$NODE_PID_FILE"
        fi
    else
        print_message "warning" "Node.js 服务器: 未运行"
    fi

    echo -e "${BLUE}===================================${NC}"
}

# 函数：显示帮助信息
show_help() {
    echo -e "${GREEN}MTSCOS AI 项目启动脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -s, --stop      停止所有服务"
    echo "  -r, --restart   重启所有服务"
    echo "  -S, --status    查看服务状态"
    echo ""
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
                stop_services
                exit 0
                ;;
            -r|--restart)
                stop_services
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
    print_message "info" "==================================="

    # 检查 Python 是否安装
    check_command "python3" "Python 3"

    # 检查 Node.js 是否安装
    check_command "node" "Node.js"

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 检查并停止已有服务
    if [ -f "$PYTHON_PID_FILE" ] || [ -f "$NODE_PID_FILE" ]; then
        print_message "warning" "检测到已有服务运行，先停止..."
        stop_services
        sleep 1
    fi

    print_message "info" "📁 准备启动服务..."

    # 启动 Python 服务器
    print_message "info" "🐍 启动 Python 服务器..."
    
    # 检查端口是否被占用
    if check_port "$PYTHON_PORT"; then
        local pid=$(lsof -ti:"$PYTHON_PORT" 2>/dev/null | head -1)
        print_message "warning" "端口 $PYTHON_PORT 已被占用，尝试停止进程 PID: $pid"
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 检查服务器脚本是否存在
    local python_script="src/python/server.py"
    if [ -f "$python_script" ]; then
        python3 "$python_script" > "$PYTHON_LOG_FILE" 2>&1 &
    else
        print_message "warning" "Python服务器脚本不存在: $python_script"
        print_message "info" "使用 Python HTTP 服务器作为备用..."
        python3 -m http.server "$PYTHON_PORT" > "$PYTHON_LOG_FILE" 2>&1 &
    fi

    PYTHON_PID=$!
    print_message "success" "Python 服务器已启动，PID: $PYTHON_PID"

    # 等待 Python 服务器启动
    sleep 2

    # 启动 Node.js 服务器
    print_message "info" "📡 启动 Node.js 服务器..."

    # 检查端口是否被占用
    if check_port "$NODE_PORT"; then
        local pid=$(lsof -ti:"$NODE_PORT" 2>/dev/null | head -1)
        print_message "warning" "端口 $NODE_PORT 已被占用，尝试停止进程 PID: $pid"
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 检查 Node.js 脚本是否存在
    local node_script="src/app.js"
    if [ -f "$node_script" ]; then
        node "$node_script" > "$NODE_LOG_FILE" 2>&1 &
    else
        print_message "warning" "Node.js服务器脚本不存在: $node_script"
        print_message "info" "跳过 Node.js 服务器启动..."
        NODE_PID=""
    fi

    if [ -n "${NODE_PID:-}" ]; then
        print_message "success" "Node.js 服务器已启动，PID: $NODE_PID"
    fi

    # 等待服务器启动
    sleep 3

    # 保存 PID 到文件
    echo "$PYTHON_PID" > "$PYTHON_PID_FILE"
    if [ -n "${NODE_PID:-}" ]; then
        echo "$NODE_PID" > "$NODE_PID_FILE"
    fi

    # 验证服务是否正常运行
    echo ""
    echo -e "${BLUE}===================================${NC}"
    echo -e "${YELLOW}服务启动状态${NC}"
    echo -e "${BLUE}===================================${NC}"

    # 检查 Python 服务器
    if is_process_running "$PYTHON_PID"; then
        echo -e "${GREEN}✓ Python 服务器:${NC} http://localhost:${PYTHON_PORT}"
    else
        echo -e "${RED}✗ Python 服务器:${NC} 启动失败"
        print_message "error" "Python服务器启动失败，请查看日志: $PYTHON_LOG_FILE"
        stop_services
        exit 1
    fi

    # 检查 Node.js 服务器
    if [ -n "${NODE_PID:-}" ] && is_process_running "$NODE_PID"; then
        echo -e "${GREEN}✓ Node.js 服务器:${NC} http://localhost:${NODE_PORT}"
    elif [ -n "${NODE_PID:-}" ]; then
        echo -e "${RED}✗ Node.js 服务器:${NC} 启动失败"
        print_message "warning" "Node.js服务器启动失败，请查看日志: $NODE_LOG_FILE"
    else
        echo -e "${YELLOW}~ Node.js 服务器:${NC} 未启动（脚本不存在）"
    fi

    echo -e "${BLUE}===================================${NC}"
    echo -e "${YELLOW}健康检查地址:${NC}"
    echo -e "   - Node.js: http://localhost:${NODE_PORT}/api/health"
    echo -e "   - Python: http://localhost:${PYTHON_PORT}/python/api/health"
    echo -e "${BLUE}===================================${NC}"
    echo -e "${YELLOW}日志文件:${NC}"
    echo -e "   - Node.js: ${NODE_LOG_FILE}"
    echo -e "   - Python: ${PYTHON_LOG_FILE}"
    echo -e "${BLUE}===================================${NC}"

    print_message "success" "✅ 所有服务启动完成！"

    echo -e "${YELLOW}📝 PID 文件已保存${NC}"
    echo -e "   - Python PID: ${PYTHON_PID_FILE}"
    echo -e "   - Node PID: ${NODE_PID_FILE}"
    echo -e "${BLUE}===================================${NC}"
    print_message "info" "💡 提示: 使用 './stop-all.sh' 或 '$0 -s' 停止所有服务"
}

# 运行主函数
main "$@"