#!/bin/bash

# MTSCOS AI Project - 整合启动脚本 v2.0
# 整合所有启动、管理、维护功能

# 脚本目录定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"  # 直接使用脚本所在目录作为项目根目录
LOG_DIR="${PROJECT_DIR}/Logs"
JS_DIR="${PROJECT_DIR}/JavaScript"
HTML_DIR="${PROJECT_DIR}/HTML"
CSS_DIR="${PROJECT_DIR}/CSS"
SERVICES_CONFIG_DIR="${PROJECT_DIR}/Scripts/Services_Config"

# 确保日志目录存在
mkdir -p "${LOG_DIR}"

# 定义颜色
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
PURPLE="\033[0;35m"
NC="\033[0m" # No Color

# 日志函数
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] INFO: $1" >> "${LOG_DIR}/mtscos_manager.log"
}

success_log() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] SUCCESS: $1" >> "${LOG_DIR}/mtscos_manager.log"
}

error_log() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $1" >> "${LOG_DIR}/mtscos_manager.log"
}

warning_log() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] WARNING: $1" >> "${LOG_DIR}/mtscos_manager.log"
}

# 美化标题输出
print_title() {
    local title="$1"
    local length=${#title}
    local padding=$(( (60 - length) / 2 ))

    echo -e "${CYAN}"
    echo "=============================================================="
    printf "%*s%s%*s\n" $padding "" "$title" $padding ""
    echo "=============================================================="
    echo -e "${NC}"
}

# 进度条函数
display_progress() {
    local current=$1
    local total=$2
    local title=$3
    local width=50

    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))

    # 构建进度条
    local bar="${GREEN}"
    for ((i=0; i<filled; i++)); do
        bar="${bar}█"
    done
    bar="${bar}${YELLOW}"
    for ((i=0; i<empty; i++)); do
        bar="${bar}░"
    done
    bar="${bar}${NC}"

    # 清除当前行并显示进度条
    echo -ne "\r${title} [${percentage}%] ${bar} "

    # 如果完成，添加换行
    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# 环境检查
check_environment() {
    print_title "环境检查"
    log "开始环境检查..."
    
    local total_steps=5
    local current_step=0
    
    # 检查Node.js
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查Node.js"
    if ! command -v node >/dev/null 2>&1; then
        error_log "Node.js未安装! 请先安装Node.js"
        return 1
    fi
    local node_version=$(node -v 2>/dev/null)
    log "Node.js版本: $node_version"
    
    # 检查npm
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查npm"
    if ! command -v npm >/dev/null 2>&1; then
        error_log "npm未安装! Node.js安装可能不完整"
        return 1
    fi
    local npm_version=$(npm -v 2>/dev/null)
    log "npm版本: $npm_version"
    
    # 检查package.json
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查package.json"
    if [ ! -f "${PROJECT_DIR}/package.json" ]; then
        error_log "package.json文件不存在"
        return 1
    fi
    
    # 检查node_modules
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查node_modules"
    if [ ! -d "${PROJECT_DIR}/node_modules" ]; then
        log "node_modules目录不存在，准备安装依赖..."
        if ! npm install --prefix "${PROJECT_DIR}"; then
            error_log "依赖安装失败"
            return 1
        fi
        success_log "依赖安装成功"
    fi
    
    # 检查必要目录
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查必要目录"
    mkdir -p "${JS_DIR}" "${HTML_DIR}" "${CSS_DIR}" "${LOG_DIR}" "${PROJECT_DIR}/Temp" "${PROJECT_DIR}/Results" "${PROJECT_DIR}/Uploads" "${PROJECT_DIR}/Users"
    
    display_progress $total_steps $total_steps "环境检查完成"
    success_log "环境检查完成"
    return 0
}

# 启动服务
start_service() {
    print_title "启动服务"
    log "开始启动服务..."
    
    # 检查环境
    if ! check_environment; then
        error_log "环境检查失败，无法启动服务"
        return 1
    fi
    
    # 启动主服务器
    log "启动主服务器..."
    if node "${JS_DIR}/server.js" > "${LOG_DIR}/server.log" 2>&1 & then
        local server_pid=$!
        echo $server_pid > "${LOG_DIR}/server.pid"
        success_log "主服务器启动成功 (PID: $server_pid)"
        log "服务器访问地址: http://localhost:8000"
    else
        error_log "主服务器启动失败"
        return 1
    fi
    
    success_log "服务启动完成!"
    return 0
}

# 停止服务
stop_service() {
    print_title "停止服务"
    log "开始停止服务..."
    
    # 停止主服务器
    if [ -f "${LOG_DIR}/server.pid" ]; then
        local server_pid=$(cat "${LOG_DIR}/server.pid")
        if kill -15 $server_pid 2>/dev/null; then
            log "等待服务器停止..."
            sleep 3
            if kill -0 $server_pid 2>/dev/null; then
                kill -9 $server_pid 2>/dev/null
                log "强制停止服务器"
            fi
            rm -f "${LOG_DIR}/server.pid"
            success_log "主服务器已停止"
        else
            warning_log "服务器进程不存在或已停止"
            rm -f "${LOG_DIR}/server.pid"
        fi
    else
        warning_log "没有找到服务器PID文件"
    fi
    
    success_log "服务停止完成!"
    return 0
}

# 重启服务
restart_service() {
    print_title "重启服务"
    if stop_service; then
        sleep 2
        start_service
    else
        error_log "停止服务失败，无法重启"
        return 1
    fi
}

# 查看状态
check_status() {
    print_title "服务状态"
    
    echo -e "${BLUE}项目信息:${NC}"
    echo "  项目名称: MTSCOS AI Project"
    echo "  项目目录: $PROJECT_DIR"
    echo ""
    
    echo -e "${BLUE}环境信息:${NC}"
    echo "  Node.js: $(node --version 2>/dev/null || echo "未安装")"
    echo "  npm: $(npm --version 2>/dev/null || echo "未安装")"
    echo "  操作系统: $(uname -s)"
    echo "  当前目录: $(pwd)"
    echo ""
    
    echo -e "${BLUE}服务信息:${NC}"
    if [ -f "${LOG_DIR}/server.pid" ]; then
        local server_pid=$(cat "${LOG_DIR}/server.pid")
        if ps -p $server_pid > /dev/null 2>&1; then
            echo -e "  主服务器: ${GREEN}运行中${NC} (PID: $server_pid)"
            echo "  访问地址: http://localhost:8000"
        else
            echo -e "  主服务器: ${RED}已停止${NC} (PID文件存在但进程不存在)"
            rm -f "${LOG_DIR}/server.pid"
        fi
    else
        echo -e "  主服务器: ${RED}未运行${NC}"
    fi
    echo ""
    
    echo -e "${BLUE}资源信息:${NC}"
    if [ -d "${PROJECT_DIR}/node_modules" ]; then
        echo "  node_modules: $(du -sh "${PROJECT_DIR}/node_modules" 2>/dev/null | cut -f1)"
    fi
    if [ -d "${PROJECT_DIR}/Logs" ]; then
        echo "  日志目录: $(du -sh "${PROJECT_DIR}/Logs" 2>/dev/null | cut -f1)"
    fi
}

# 清理系统
clean_system() {
    print_title "清理系统"
    log "开始清理系统..."
    
    local total_steps=4
    local current_step=0
    
    # 清理旧日志
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "清理旧日志"
    find "${LOG_DIR}" -name "*.log" -type f -mtime +30 -delete 2>/dev/null
    
    # 清理临时文件
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "清理临时文件"
    rm -rf "${PROJECT_DIR}/Temp/*" 2>/dev/null
    
    # 清理快照
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "清理快照"
    rm -rf "${PROJECT_DIR}/.snapshots/*" 2>/dev/null
    
    # 清理JavaScript监控日志
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "清理JavaScript监控日志"
    rm -rf "${LOG_DIR}/JavaScript监控/*" 2>/dev/null
    
    display_progress $total_steps $total_steps "清理完成"
    success_log "系统清理完成!"
}

# 更新系统
update_system() {
    print_title "更新系统"
    log "开始更新系统..."
    
    # 检查git
    if ! command -v git >/dev/null 2>&1; then
        error_log "git未安装，无法更新系统"
        return 1
    fi
    
    # 拉取最新代码
    log "拉取最新代码..."
    if git -C "${PROJECT_DIR}" pull; then
        success_log "代码更新成功"
    else
        error_log "代码更新失败"
        return 1
    fi
    
    # 安装依赖
    log "安装最新依赖..."
    if npm install --prefix "${PROJECT_DIR}"; then
        success_log "依赖更新成功"
    else
        error_log "依赖更新失败"
        return 1
    fi
    
    # 更新版本号
    local new_version="$(date +"%Y%m%d.%H%M%S")"
    echo "$new_version" > "${PROJECT_DIR}/VERSION"
    echo "$new_version" > "${PROJECT_DIR}/Scripts/VERSION"
    
    success_log "系统更新完成! 新版本号: $new_version"
    return 0
}

# 查看日志
view_logs() {
    print_title "查看日志"
    
    echo -e "${BLUE}可用日志文件:${NC}"
    local logs=( $(find "${LOG_DIR}" -name "*.log" | sort) )
    
    for i in "${!logs[@]}"; do
        echo "  $((i+1))) $(basename "${logs[$i]}")"
    done
    
    echo -n "请选择要查看的日志 (0退出): "
    read -r choice
    
    if [ "$choice" -eq "0" ] 2>/dev/null; then
        return 0
    fi
    
    local index=$((choice-1))
    if [ "$index" -ge 0 ] && [ "$index" -lt "${#logs[@]}" ]; then
        local log_file="${logs[$index]}"
        echo -e "\n${YELLOW}显示日志: ${log_file}${NC}"
        echo -e "${BLUE}按Ctrl+C退出查看${NC}"
        tail -50 -f "${log_file}"
    else
        error_log "无效的选择"
    fi
}

# 显示主菜单
show_menu() {
    print_title "MTSCOS AI Project 管理中心"
    echo -e "${BLUE}"
    echo "请选择操作:"
    echo "1) 启动服务"
    echo "2) 停止服务"
    echo "3) 重启服务"
    echo "4) 查看状态"
    echo "5) 环境检查"
    echo "6) 清理系统"
    echo "7) 更新系统"
    echo "8) 查看日志"
    echo "9) 系统信息"
    echo "0) 退出"
    echo -e "${NC}"
    echo -n "请输入选项 [0-9]: "
}

# 显示系统信息
show_system_info() {
    print_title "系统信息"
    
    echo -e "${BLUE}项目信息:${NC}"
    echo "  项目名称: MTSCOS AI Project"
    echo "  项目版本: $(cat "${PROJECT_DIR}/VERSION" 2>/dev/null || echo "未知")"
    echo "  项目目录: $PROJECT_DIR"
    echo ""
    
    echo -e "${BLUE}环境信息:${NC}"
    echo "  Node.js: $(node --version 2>/dev/null || echo "未安装")"
    echo "  npm: $(npm --version 2>/dev/null || echo "未安装")"
    echo "  OS: $(uname -s) $(uname -r)"
    echo "  CPU: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || lscpu | grep "Model name" | cut -d: -f2 | xargs)"
    echo "  Memory: $(sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1024/1024/1024 " GB"}' || free -h | grep Mem | awk '{print $2}')"
    echo ""
    
    echo -e "${BLUE}目录结构:${NC}"
    echo "  JavaScript: ${JS_DIR}"
    echo "  HTML: ${HTML_DIR}"
    echo "  CSS: ${CSS_DIR}"
    echo "  Logs: ${LOG_DIR}"
    echo "  Scripts: ${PROJECT_DIR}/Scripts"
}

# 主循环
main_loop() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) start_service ;;
            2) stop_service ;;
            3) restart_service ;;
            4) check_status ;;
            5) check_environment ;;
            6) clean_system ;;
            7) update_system ;;
            8) view_logs ;;
            9) show_system_info ;;
            0) print_title "退出系统" ; echo -e "${CYAN}感谢使用 MTSCOS AI Project!${NC}" ; break ;;
            *) echo -e "${RED}无效的选择，请重新输入${NC}" ;;
        esac
        
        echo -e "\n${PURPLE}按Enter键继续...${NC}"
        read -r
    done
}

# 自我修复机制
self_repair() {
    print_title "自我修复机制"
    log "开始自我修复..."
    
    local total_steps=3
    local current_step=0
    
    # 检查必要文件
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "检查必要文件"
    
    # 检查package.json
    if [ ! -f "${PROJECT_DIR}/package.json" ]; then
        error_log "package.json文件不存在，无法修复"
        return 1
    fi
    
    # 检查server.js
    if [ ! -f "${JS_DIR}/server.js" ]; then
        error_log "server.js文件不存在，无法修复"
        return 1
    fi
    
    # 修复权限
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "修复文件权限"
    chmod -R 755 "${PROJECT_DIR}/Scripts"/*.sh
    chmod -R 755 "${JS_DIR}"/*.js
    
    # 清理并重建目录
    current_step=$((current_step + 1))
    display_progress $current_step $total_steps "重建目录结构"
    mkdir -p "${JS_DIR}" "${HTML_DIR}" "${CSS_DIR}" "${LOG_DIR}" "${PROJECT_DIR}/Temp" "${PROJECT_DIR}/Results" "${PROJECT_DIR}/Uploads" "${PROJECT_DIR}/Users"
    
    display_progress $total_steps $total_steps "修复完成"
    success_log "自我修复完成!"
    return 0
}

# 主函数
main() {
    # 如果有参数，直接执行对应的功能
    case "$1" in
        start) start_service ; exit $? ;;
        stop) stop_service ; exit $? ;;
        restart) restart_service ; exit $? ;;
        status) check_status ; exit $? ;;
        check) check_environment ; exit $? ;;
        clean) clean_system ; exit $? ;;
        update) update_system ; exit $? ;;
        logs) view_logs ; exit $? ;;
        info) show_system_info ; exit $? ;;
        repair) self_repair ; exit $? ;;
        *) main_loop ;;
    esac
}

# 执行主函数
main "$@"