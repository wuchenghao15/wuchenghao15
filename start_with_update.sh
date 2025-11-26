#!/bin/bash

# MTSCOS AI Project - 增强版启动脚本
# 版本: v2.0
# 描述: 项目启动入口，提供启动管理功能并集成自动更新机制

set -e

# 项目配置
PROJECT_NAME="MTSCOS AI Project"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUICK_START_SCRIPT="$PROJECT_DIR/Scripts/quick_start.sh"
LOG_FILE="$PROJECT_DIR/Logs/startup.log"
UPDATE_CHECK_FILE="$PROJECT_DIR/.last-update"
UPDATE_SCRIPT="$PROJECT_DIR/Scripts/update.sh"
VERSION_FILE="$PROJECT_DIR/VERSION"
SERVER_PID_FILE="$PROJECT_DIR/Logs/server.pid"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log() {
    local level="INFO"
    local color="$BLUE"
    
    if [[ "$1" == "ERROR" ]]; then
        level="ERROR"
        color="$RED"
        shift
    elif [[ "$1" == "WARNING" ]]; then
        level="WARNING"
        color="$YELLOW"
        shift
    elif [[ "$1" == "SUCCESS" ]]; then
        level="SUCCESS"
        color="$GREEN"
        shift
    fi
    
    local message="$1"
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S') - $level]${NC} $message"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $level: $message" >> "$LOG_FILE"
}

# 显示欢迎信息
show_welcome() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "              $PROJECT_NAME"
    echo "           增强版启动与更新管理工具"
    echo "=================================================="
    echo -e "${NC}"
    
    # 显示当前版本
    if [[ -f "$VERSION_FILE" ]]; then
        local version=$(cat "$VERSION_FILE")
        echo -e "当前版本: ${GREEN}$version${NC}"
    fi
    echo ""
}

# 检查环境
check_environment() {
    log "检查运行环境..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log ERROR "Node.js 未安装"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log ERROR "npm 未安装"
        exit 1
    fi
    
    # 检查快速启动脚本
    if [[ ! -f "$QUICK_START_SCRIPT" ]]; then
        log ERROR "快速启动脚本不存在: $QUICK_START_SCRIPT"
        exit 1
    fi
    
    # 创建必要目录
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$PROJECT_DIR/Backups/updates"
    
    log SUCCESS "环境检查通过"
}

# 检查更新
check_update() {
    log "检查更新..."
    
    # 检查更新间隔 (24小时)
    local update_interval=$((24 * 60 * 60))
    local last_update=0
    
    # 读取上次更新时间
    if [[ -f "$UPDATE_CHECK_FILE" ]]; then
        last_update=$(cat "$UPDATE_CHECK_FILE")
    fi
    
    # 计算时间差
    local current_time=$(date +%s)
    local time_diff=$((current_time - last_update))
    
    # 如果距离上次检查时间不到更新间隔，跳过检查
    if [[ $time_diff -lt $update_interval ]]; then
        local hours_left=$(((update_interval - time_diff) / 3600))
        log WARNING "距离下次自动检查更新还有 $hours_left 小时"
        return 0
    fi
    
    # 更新检查时间
    echo "$current_time" > "$UPDATE_CHECK_FILE"
    
    # 检查是否有更新脚本
    if [[ -f "$UPDATE_SCRIPT" ]]; then
        log "运行更新检查脚本..."
        bash "$UPDATE_SCRIPT" check
        local update_available=$?
        
        if [[ $update_available -eq 0 ]]; then
            log SUCCESS "当前已是最新版本"
            return 0
        elif [[ $update_available -eq 1 ]]; then
            log WARNING "有可用更新"
            return 1
        else
            log ERROR "更新检查失败"
            return 2
        fi
    else
        # 模拟检查更新逻辑
        log WARNING "更新脚本不存在，使用基础检查"
        
        # 这里可以添加其他更新检查逻辑
        # 例如检查远程版本、Git仓库状态等
        
        # 模拟有更新可用
        log WARNING "模拟检测到更新可用（实际环境中需要实现真实的更新检查逻辑）"
        return 1
    fi
}

# 执行更新
do_update() {
    log "执行更新..."
    
    # 停止服务
    log "停止服务以准备更新..."
    "$QUICK_START_SCRIPT" stop || true
    
    # 创建备份
    local backup_dir="$PROJECT_DIR/Backups/updates/$(date '+%Y%m%d_%H%M%S')"
    log "创建更新备份: $backup_dir"
    mkdir -p "$backup_dir"
    
    # 备份关键文件
    cp -r "$PROJECT_DIR/JavaScript" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/HTML" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/CSS" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/assets" "$backup_dir/" 2>/dev/null || true
    cp "$PROJECT_DIR/package.json" "$backup_dir/" 2>/dev/null || true
    if [[ -f "$VERSION_FILE" ]]; then
        cp "$VERSION_FILE" "$backup_dir/" 2>/dev/null || true
    fi
    
    # 检查是否有更新脚本
    if [[ -f "$UPDATE_SCRIPT" ]]; then
        log "运行更新脚本..."
        if bash "$UPDATE_SCRIPT" update; then
            log SUCCESS "更新成功"
            
            # 更新版本文件（如果更新脚本没有更新）
            if [[ -f "$VERSION_FILE" ]]; then
                local new_version="$(date '+%Y%m%d.%H%M%S')"
                echo "$new_version" > "$VERSION_FILE"
                log "版本已更新至: $new_version"
            fi
            
            return 0
        else
            log ERROR "更新失败，尝试回滚..."
            
            # 简单回滚逻辑
            if [[ -d "$backup_dir/JavaScript" ]]; then
                cp -r "$backup_dir/JavaScript/"* "$PROJECT_DIR/JavaScript/" 2>/dev/null || true
            fi
            
            log WARNING "已尝试回滚，可能需要手动检查修复"
            return 1
        fi
    else
        # 模拟更新过程
        log "模拟更新过程（实际环境中需要实现真实的更新逻辑）"
        
        # 更新版本文件
        local new_version="$(date '+%Y%m%d.%H%M%S')"
        echo "$new_version" > "$VERSION_FILE"
        log "版本已模拟更新至: $new_version"
        
        log SUCCESS "模拟更新完成"
        return 0
    fi
}

# 启动服务
start_service() {
    log "启动服务..."
    "$QUICK_START_SCRIPT" start
}

# 停止服务
stop_service() {
    log "停止服务..."
    "$QUICK_START_SCRIPT" stop
}

# 重启服务
restart_service() {
    log "重启服务..."
    "$QUICK_START_SCRIPT" restart
}

# 查看状态
check_status() {
    log "检查服务状态..."
    "$QUICK_START_SCRIPT" status
}

# 环境检查
check_env() {
    log "执行环境检查..."
    "$QUICK_START_SCRIPT" check
}

# 初始化项目
init_project() {
    log "初始化项目..."
    "$QUICK_START_SCRIPT" init
}

# 打开管理界面
open_interface() {
    log "打开管理界面..."
    
    # 检查服务是否运行
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        log ERROR "服务未运行，请先启动服务"
        return 1
    fi
    
    # 根据操作系统打开浏览器
    case "$(uname -s)" in
        Darwin*)    open "http://localhost:3000" ;;        
        Linux*)     xdg-open "http://localhost:3000" 2>/dev/null || firefox "http://localhost:3000" 2>/dev/null || echo -e "${YELLOW}请手动打开: http://localhost:3000${NC}" ;;        
        CYGWIN*|MINGW*|MSYS*) start "http://localhost:3000" ;;        
        *)          echo -e "${YELLOW}请手动打开: http://localhost:3000${NC}" ;;        
    esac
}

# 查看日志
view_logs() {
    log "显示最近日志..."
    if [[ -f "$LOG_FILE" ]]; then
        tail -20 "$LOG_FILE"
    else
        log ERROR "日志文件不存在: $LOG_FILE"
    fi
}

# 显示系统信息
show_system_info() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "                   系统信息"
    echo "=================================================="
    echo -e "${NC}"
    
    echo -e "${BLUE}项目信息:${NC}"
    echo "  项目名称: $PROJECT_NAME"
    echo "  项目目录: $PROJECT_DIR"
    echo "  启动脚本: $QUICK_START_SCRIPT"
    
    if [[ -f "$VERSION_FILE" ]]; then
        echo "  当前版本: $(cat "$VERSION_FILE")"
    fi
    
    # 显示上次更新时间
    if [[ -f "$UPDATE_CHECK_FILE" ]]; then
        local last_update=$(cat "$UPDATE_CHECK_FILE")
        local last_update_str=$(date -r "$last_update" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d "@$last_update" '+%Y-%m-%d %H:%M:%S')
        echo "  上次更新检查: $last_update_str"
    fi
    
    echo ""
    
    echo -e "${BLUE}环境信息:${NC}"
    echo "  Node.js: $(node --version)"
    echo "  npm: $(npm --version)"
    echo "  操作系统: $(uname -s)"
    echo "  当前目录: $(pwd)"
    echo ""
    
    echo -e "${BLUE}服务信息:${NC}"
    # 检查服务是否运行
    if [[ -f "$SERVER_PID_FILE" ]]; then
        local pid=$(cat "$SERVER_PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && ps -p "$pid" >/dev/null 2>&1; then
            echo -e "  状态: ${GREEN}运行中${NC} (PID: $pid)"
            
            # 检查端口
            if curl -s http://localhost:3000 >/dev/null 2>&1; then
                echo -e "  端口状态: ${GREEN}可访问${NC} (http://localhost:3000)"
            else
                echo -e "  端口状态: ${YELLOW}不可访问${NC}"
            fi
        else
            echo -e "  状态: ${RED}未运行${NC} (PID文件无效)"
        fi
    else
        # 检查是否有进程在运行
        if pgrep -f "login-api-server-test.js" >/dev/null 2>&1; then
            echo -e "  状态: ${YELLOW}运行中${NC} (无PID文件)"
        else
            echo -e "  状态: ${RED}未运行${NC}"
        fi
    fi
    
    echo ""
    
    echo -e "${BLUE}资源信息:${NC}"
    if [[ -d "$PROJECT_DIR/node_modules" ]]; then
        echo "  node_modules: $(du -sh "$PROJECT_DIR/node_modules" 2>/dev/null | cut -f1 || echo "未知")"
    fi
    if [[ -d "$PROJECT_DIR/Logs" ]]; then
        echo "  日志目录: $(du -sh "$PROJECT_DIR/Logs" 2>/dev/null | cut -f1 || echo "未知")"
    fi
    if [[ -d "$PROJECT_DIR/Backups" ]]; then
        echo "  备份目录: $(du -sh "$PROJECT_DIR/Backups" 2>/dev/null | cut -f1 || echo "未知")"
    fi
}

# 强制检查更新
force_check_update() {
    log "强制检查更新..."
    # 删除更新检查文件以强制检查
    rm -f "$UPDATE_CHECK_FILE"
    check_update
    local update_available=$?
    
    if [[ $update_available -eq 1 ]]; then
        echo -e "${YELLOW}发现可用更新，是否立即更新? [y/N]: ${NC}"
        read -r update_now
        if [[ "$update_now" == "y" || "$update_now" == "Y" ]]; then
            do_update
        else
            log "已取消更新"
        fi
    elif [[ $update_available -eq 0 ]]; then
        log SUCCESS "当前已是最新版本"
    fi
}

# 显示主菜单
show_menu() {
    echo -e "${BLUE}"
    echo "请选择操作:"
    echo "1) 启动服务"
    echo "2) 停止服务"
    echo "3) 重启服务"
    echo "4) 查看状态"
    echo "5) 环境检查"
    echo "6) 初始化项目"
    echo "7) 打开管理界面"
    echo "8) 查看日志"
    echo "9) 系统信息"
    echo "u) 检查更新"
    echo "0) 退出"
    echo -e "${NC}"
    echo -n "请输入选项: "
}

# 主循环
main_loop() {
    while true; do
        show_menu
        read -r choice
        
        case "$choice" in
            1) start_service ;;
            2) stop_service ;;
            3) restart_service ;;
            4) check_status ;;
            5) check_env ;;
            6) init_project ;;
            7) open_interface ;;
            8) view_logs ;;
            9) show_system_info ;;
            u|U) force_check_update ;;
            0) 
                log SUCCESS "退出程序"
                exit 0
                ;;
            *)
                log ERROR "无效选项: $choice"
                ;;
        esac
        
        echo ""
        echo -n "按回车键继续..."
        read -r
        echo ""
    done
}

# 主函数
main() {
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 显示欢迎信息
    show_welcome
    
    # 检查环境
    check_environment
    
    # 自动检查更新（如果没有命令行参数）
    if [[ $# -eq 0 ]]; then
        log "自动检查更新..."
        check_update
        local update_available=$?
        
        if [[ $update_available -eq 1 ]]; then
            echo -e "\n${YELLOW}发现可用更新，是否立即更新? [y/N]: ${NC}"
            read -r update_now
            if [[ "$update_now" == "y" || "$update_now" == "Y" ]]; then
                do_update
            fi
            echo ""
        fi
    fi
    
    # 如果有命令行参数，直接执行
    if [[ $# -gt 0 ]]; then
        case "$1" in
            start) start_service ;;
            stop) stop_service ;;
            restart) restart_service ;;
            status) check_status ;;
            check) check_env ;;
            init) init_project ;;
            open) open_interface ;;
            info) show_system_info ;;
            update) force_check_update ;;
            *) 
                log ERROR "未知命令: $1"
                echo -e "可用命令: start, stop, restart, status, check, init, open, info, update"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # 进入主循环
    main_loop
}

# 执行主函数
main "$@"
