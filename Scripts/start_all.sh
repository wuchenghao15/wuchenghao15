#!/bin/bash

# MTSCOS AI Project 启动脚本 v2.0
# 集成DeepSeek和本地项目引擎

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 定义关键路径
MAIN_SERVER="$PROJECT_DIR/JavaScript/server.js"
CONFIG_FILE="$PROJECT_DIR/JavaScript/config.js"
NODE_MODULES="$PROJECT_DIR/node_modules"
LOG_DIR="$PROJECT_DIR/Logs"
SCRIPTS_DIR="$PROJECT_DIR/Scripts"
MONITORING_DIR="$PROJECT_DIR/Staging/Scripts/monitoring"

# 定义日志文件
MAIN_LOG="$LOG_DIR/start_all.log"
SERVER_LOG="$LOG_DIR/node_server.log"
DEEPSEEK_LOG="$LOG_DIR/deepseek.log"
ERROR_LOG="$LOG_DIR/errors.log"  # 异常日志
REPAIR_LOG="$LOG_DIR/repairs.log"  # 修复操作日志

# 定义PID文件
SERVER_PID="$LOG_DIR/server.pid"
MONITOR_PID="$LOG_DIR/monitor.pid"
DEEPSEEK_PID="$LOG_DIR/deepseek.pid"

# 日志函数
log() {
    local message="$1"
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] $message" | tee -a "$MAIN_LOG"
}

success_log() {
    log "${GREEN}✓ $1${NC}"
}

error_log() {
    log "${RED}✗ $1${NC}"
    # 记录异常日志
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] ERROR: $1" >> "$ERROR_LOG"
}

warning_log() {
    log "${YELLOW}! $1${NC}"
    # 记录异常日志（警告级别）
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] WARNING: $1" >> "$ERROR_LOG"
}

info_log() {
    log "${BLUE}ℹ $1${NC}"
}

# 记录修复操作日志
repair_log() {
    local operation="$1"
    local result="$2"
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] OPERATION: $operation | RESULT: $result" >> "$REPAIR_LOG"
    info_log "修复操作: $operation | 结果: $result"
}

# 自动修复函数
auto_repair() {
    local error_type="$1"
    local error_details="$2"
    local repair_result="FAILED"
    
    info_log "尝试自动修复: $error_type"
    
    case "$error_type" in
        "FILE_NOT_FOUND")
            # 尝试修复文件不存在的问题
            if [[ "$error_details" == *"node_modules"* ]]; then
                # 重新安装依赖
                info_log "重新安装依赖..."
                cd "$PROJECT_DIR" || return 1
                rm -rf "$NODE_MODULES"
                npm install >> "$MAIN_LOG" 2>&1
                if [ $? -eq 0 ]; then
                    repair_result="SUCCESS"
                fi
            elif [[ "$error_details" == *"config.js"* ]]; then
                # 尝试从备份恢复配置文件
                if [ -f "$CONFIG_FILE.bak" ]; then
                    info_log "从备份恢复配置文件..."
                    cp "$CONFIG_FILE.bak" "$CONFIG_FILE"
                    if [ $? -eq 0 ]; then
                        repair_result="SUCCESS"
                    fi
                fi
            elif [[ "$error_details" == *"server.js"* ]]; then
                # 检查是否有备用服务器文件
                if [ -f "$MAIN_SERVER.bak" ]; then
                    info_log "从备份恢复服务器文件..."
                    cp "$MAIN_SERVER.bak" "$MAIN_SERVER"
                    if [ $? -eq 0 ]; then
                        repair_result="SUCCESS"
                    fi
                fi
            fi
            ;;
            
        "SERVER_START_FAILED")
            # 尝试修复服务器启动失败的问题
            info_log "重启服务器..."
            stop_main_server
            start_main_server
            if [ $? -eq 0 ]; then
                repair_result="SUCCESS"
            fi
            ;;
            
        "DEPENDENCY_INSTALL_FAILED")
            # 尝试修复依赖安装失败的问题
            info_log "清理并重新安装依赖..."
            cd "$PROJECT_DIR" || return 1
            rm -rf "$NODE_MODULES" package-lock.json
            npm install >> "$MAIN_LOG" 2>&1
            if [ $? -eq 0 ]; then
                repair_result="SUCCESS"
            fi
            ;;
            
        "MONITORING_START_FAILED")
            # 尝试修复监控服务启动失败的问题
            info_log "重启监控服务..."
            stop_monitoring
            start_monitoring
            if [ $? -eq 0 ]; then
                repair_result="SUCCESS"
            fi
            ;;
            
        "DEEPSEEK_START_FAILED")
            # 尝试修复DeepSeek服务启动失败的问题
            info_log "重启DeepSeek服务..."
            stop_deepseek
            start_deepseek
            if [ $? -eq 0 ]; then
                repair_result="SUCCESS"
            fi
            ;;
            
        "PID_FILE_ERROR")
            # 修复PID文件错误
            info_log "清理无效PID文件..."
            rm -f "$SERVER_PID" "$MONITOR_PID" "$DEEPSEEK_PID"
            repair_result="SUCCESS"
            ;;
            
        "SERVER_NOT_RUNNING")
            # 修复服务未运行的问题
            info_log "检测到服务未运行，尝试启动..."
            
            # 根据错误详情判断要启动哪个服务
            if [[ "$error_details" == *"主服务器"* ]]; then
                stop_main_server 2>/dev/null
                start_main_server
                if [ $? -eq 0 ]; then
                    repair_result="SUCCESS"
                fi
            elif [[ "$error_details" == *"监控服务"* ]]; then
                stop_monitoring 2>/dev/null
                start_monitoring
                if [ $? -eq 0 ]; then
                    repair_result="SUCCESS"
                fi
            elif [[ "$error_details" == *"DeepSeek"* ]]; then
                stop_deepseek 2>/dev/null
                start_deepseek
                if [ $? -eq 0 ]; then
                    repair_result="SUCCESS"
                fi
            fi
            ;;
            
        "STARTUP_PROGRESS_INCOMPLETE")
            # 修复启动进度未达到100%的问题
            info_log "启动进度未达到100%，尝试重新启动整个项目..."
            
            # 检查重试次数，避免无限循环
            if [ -z "$REPAIR_RETRY_COUNT" ]; then
                export REPAIR_RETRY_COUNT=0
            fi
            
            if [ $REPAIR_RETRY_COUNT -ge 2 ]; then
                error_log "已达到最大重试次数 ($REPAIR_RETRY_COUNT)，无法完成自动修复"
                repair_result="FAILED"
                return 1
            fi
            
            # 增加重试计数
            export REPAIR_RETRY_COUNT=$((REPAIR_RETRY_COUNT + 1))
            info_log "当前重试次数: $REPAIR_RETRY_COUNT"
            
            # 停止所有服务
            stop_all_services 2>/dev/null
            
            # 重启所有服务，但设置标志避免重复输出
            export REPAIR_MODE="true"
            start_all
            repair_result=$([ $? -eq 0 ] && echo "SUCCESS" || echo "FAILED")
            
            # 重置标志和重试计数
            unset REPAIR_MODE
            if [ "$repair_result" == "SUCCESS" ]; then
                export REPAIR_RETRY_COUNT=0
            fi
            ;;
            
        *)
            info_log "无法识别的错误类型，跳过自动修复"
            repair_result="NOT_SUPPORTED"
            ;;
    esac
    
    repair_log "$error_type" "$repair_result"
    return $([[ "$repair_result" == "SUCCESS" ]] && echo 0 || echo 1)
}

# 进度条函数
show_progress() {
    local progress=$1
    local total=$2
    local percentage=$((progress * 100 / total))
    local bar_length=50
    local filled_length=$((percentage * bar_length / 100))
    
    local bar=""
    for ((i=0; i<filled_length; i++)); do
        bar="$bar#"
    done
    for ((i=filled_length; i<bar_length; i++)); do
        bar="$bar-"
    done
    
    echo -ne "\rProgress: [${CYAN}$bar${NC}] ${percentage}%"
}

# 环境检查函数
check_environment() {
    log "检查环境..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        error_log "未找到 Node.js"
        auto_repair "NODEJS_NOT_FOUND" "Node.js 命令未找到"
        # 再次检查
        if ! command -v node &> /dev/null; then
            error_log "自动修复失败：Node.js 仍未找到"
            return 1
        fi
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        error_log "未找到 npm"
        auto_repair "NPM_NOT_FOUND" "npm 命令未找到"
        # 再次检查
        if ! command -v npm &> /dev/null; then
            error_log "自动修复失败：npm 仍未找到"
            return 1
        fi
    fi
    
    # 显示版本
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    success_log "Node.js $NODE_VERSION 已安装"
    success_log "npm $NPM_VERSION 已安装"
    
    return 0
}

# 安装依赖
install_dependencies() {
    info_log "检查项目依赖..."
    
    if [ ! -d "$NODE_MODULES" ]; then
        warning_log "node_modules目录不存在，正在安装依赖..."
        cd "$PROJECT_DIR" || exit 1
        npm install >> "$MAIN_LOG" 2>&1
        if [ $? -eq 0 ]; then
            success_log "依赖安装完成"
        else
            error_log "依赖安装失败，请检查网络连接和package.json文件"
            auto_repair "DEPENDENCY_INSTALL_FAILED" "依赖安装失败，尝试重新安装"
            # 再次检查依赖是否安装成功
            if [ ! -d "$NODE_MODULES" ]; then
                error_log "自动修复失败：依赖仍未安装"
                return 1
            fi
            success_log "自动修复成功：依赖安装完成"
        fi
    else
        # 检查是否需要更新依赖
        warning_log "正在检查依赖更新..."
        cd "$PROJECT_DIR" || exit 1
        npm outdated >> "$MAIN_LOG" 2>&1
        if [ $? -eq 0 ]; then
            success_log "依赖已更新"
        else
            warning_log "依赖更新检查失败，继续使用现有依赖"
        fi
    fi
    return 0
}

# 启动主服务器
start_main_server() {
    info_log "启动主服务器..."
    
    if [ ! -f "$MAIN_SERVER" ]; then
        error_log "主服务器文件不存在: $MAIN_SERVER"
        return 1
    fi
    
    # 检查服务器是否已在运行
    if [ -f "$SERVER_PID" ]; then
        local pid=$(cat "$SERVER_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            warning_log "主服务器已在运行 (PID: $pid)"
            return 0
        else
            warning_log "找到PID文件但进程不存在，删除PID文件"
            rm -f "$SERVER_PID"
        fi
    fi
    
    # 启动服务器
    cd "$PROJECT_DIR" || exit 1
    nohup node "$MAIN_SERVER" > "$SERVER_LOG" 2>&1 &
    local server_pid=$!
    
    # 检查服务器是否成功启动
    sleep 3
    if ps -p "$server_pid" > /dev/null 2>&1; then
        echo "$server_pid" > "$SERVER_PID"
        success_log "主服务器启动成功 (PID: $server_pid)"
        return 0
    else
        error_log "主服务器启动失败，请查看日志: $SERVER_LOG"
        auto_repair "SERVER_START_FAILED" "主服务器启动失败，尝试重新启动"
        # 再次检查
        if [ ! -f "$SERVER_PID" ]; then
            error_log "自动修复失败：主服务器仍未启动"
            return 1
        fi
        success_log "自动修复成功：主服务器已启动"
        return 0
    fi
}

# 启动环境监控服务
start_monitoring() {
    info_log "启动环境监控服务..."
    
    local monitor_script="$MONITORING_DIR/environment-monitor.js"
    if [ ! -f "$monitor_script" ]; then
        error_log "监控脚本不存在: $monitor_script"
        auto_repair "FILE_NOT_FOUND" "监控服务文件 $monitor_script 未找到"
        # 再次检查
        if [ ! -f "$monitor_script" ]; then
            error_log "自动修复失败：监控服务文件仍未找到"
            return 1
        fi
    fi
    
    # 检查监控服务是否已在运行
    if [ -f "$MONITOR_PID" ]; then
        local pid=$(cat "$MONITOR_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            warning_log "监控服务已在运行 (PID: $pid)"
            return 0
        else
            warning_log "找到PID文件但进程不存在，删除PID文件"
            rm -f "$MONITOR_PID"
        fi
    fi
    
    # 启动监控服务
    cd "$PROJECT_DIR" || exit 1
    nohup node "$monitor_script" > "$LOG_DIR/monitor.log" 2>&1 &
    local monitor_pid=$!
    
    # 检查监控服务是否成功启动
    sleep 2
    if ps -p "$monitor_pid" > /dev/null 2>&1; then
        echo "$monitor_pid" > "$MONITOR_PID"
        success_log "监控服务启动成功 (PID: $monitor_pid)"
        return 0
    else
        error_log "监控服务启动失败，请查看日志: $LOG_DIR/monitor.log"
        auto_repair "MONITORING_START_FAILED" "监控服务启动失败，尝试重新启动"
        # 再次检查
        if [ ! -f "$MONITOR_PID" ] || ! ps -p "$(cat "$MONITOR_PID" 2>/dev/null)" > /dev/null 2>&1; then
            error_log "自动修复失败：监控服务仍未启动"
            return 1
        fi
        success_log "自动修复成功：监控服务已启动"
        return 0
    fi
}

# 启动DeepSeek服务
start_deepseek() {
    info_log "启动DeepSeek服务..."
    
    # 检查DeepSeek是否已配置
    local deepseek_script="$PROJECT_DIR/Staging/Scripts/deepseek-engine.js"
    if [ ! -f "$deepseek_script" ]; then
        error_log "DeepSeek脚本不存在: $deepseek_script"
        auto_repair "FILE_NOT_FOUND" "DeepSeek服务文件 $deepseek_script 未找到"
        # 再次检查
        if [ ! -f "$deepseek_script" ]; then
            error_log "自动修复失败：DeepSeek脚本仍未找到"
            return 1
        fi
    fi
    
    # 检查DeepSeek服务是否已在运行
    if [ -f "$DEEPSEEK_PID" ]; then
        local pid=$(cat "$DEEPSEEK_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            warning_log "DeepSeek服务已在运行 (PID: $pid)"
            return 0
        else
            warning_log "找到PID文件但进程不存在，删除PID文件"
            rm -f "$DEEPSEEK_PID"
        fi
    fi
    
    # 启动DeepSeek服务
    cd "$PROJECT_DIR" || exit 1
    nohup node "$deepseek_script" > "$DEEPSEEK_LOG" 2>&1 &
    local deepseek_pid=$!
    
    # 检查DeepSeek服务是否成功启动
    sleep 2
    if ps -p "$deepseek_pid" > /dev/null 2>&1; then
        echo "$deepseek_pid" > "$DEEPSEEK_PID"
        success_log "DeepSeek服务启动成功 (PID: $deepseek_pid)"
        return 0
    else
        error_log "DeepSeek服务启动失败，请查看日志: $DEEPSEEK_LOG"
        auto_repair "DEEPSEEK_START_FAILED" "DeepSeek服务启动失败，尝试重新启动"
        # 再次检查
        if [ ! -f "$DEEPSEEK_PID" ] || ! ps -p "$(cat "$DEEPSEEK_PID" 2>/dev/null)" > /dev/null 2>&1; then
            error_log "自动修复失败：DeepSeek服务仍未启动"
            return 1
        fi
        success_log "自动修复成功：DeepSeek服务已启动"
        return 0
    fi
}

# 停止主服务器
stop_main_server() {
    info_log "停止主服务器..."
    
    if [ -f "$SERVER_PID" ]; then
        local pid=$(cat "$SERVER_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" > /dev/null 2>&1
            # 等待进程停止
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" > /dev/null 2>&1
                warning_log "主服务器已强制停止 (PID: $pid)"
            else
                success_log "主服务器已停止 (PID: $pid)"
            fi
        else
            warning_log "主服务器进程不存在 (PID: $pid)"
        fi
        rm -f "$SERVER_PID"
    else
        warning_log "未找到主服务器PID文件"
    fi
    return 0
}

# 停止监控服务
stop_monitoring() {
    info_log "停止监控服务..."
    
    if [ -f "$MONITOR_PID" ]; then
        local pid=$(cat "$MONITOR_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" > /dev/null 2>&1
            # 等待进程停止
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" > /dev/null 2>&1
                warning_log "监控服务已强制停止 (PID: $pid)"
            else
                success_log "监控服务已停止 (PID: $pid)"
            fi
        else
            warning_log "监控服务进程不存在 (PID: $pid)"
        fi
        rm -f "$MONITOR_PID"
    else
        warning_log "未找到监控服务PID文件"
    fi
    return 0
}

# 停止DeepSeek服务
stop_deepseek() {
    info_log "停止DeepSeek服务..."
    
    if [ -f "$DEEPSEEK_PID" ]; then
        local pid=$(cat "$DEEPSEEK_PID")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" > /dev/null 2>&1
            # 等待进程停止
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" > /dev/null 2>&1
                warning_log "DeepSeek服务已强制停止 (PID: $pid)"
            else
                success_log "DeepSeek服务已停止 (PID: $pid)"
            fi
        else
            warning_log "DeepSeek服务进程不存在 (PID: $pid)"
        fi
        rm -f "$DEEPSEEK_PID"
    else
        warning_log "未找到DeepSeek服务PID文件"
    fi
    return 0
}

# 停止所有服务
stop_all_services() {
    info_log "停止所有服务..."
    stop_deepseek
    stop_monitoring
    stop_main_server
    success_log "所有服务已停止"
    return 0
}

# 检查所有服务状态
check_all_services() {
    info_log "检查服务状态..."
    
    echo -e "\n${CYAN}=== MTSCOS AI Project 服务状态 ===${NC}"
    
    local services_running=0
    local total_services=3
    
# 通用PID文件处理函数
manage_pid_file() {
    local service_name=$1
    local running_pid=$2
    local pid_file_path=$3
    
    # 检查并更新PID文件
    if [ -f "$pid_file_path" ]; then
        local pid_file=$(cat "$pid_file_path" 2>/dev/null)
        if [ "$pid_file" != "$running_pid" ]; then
            # PID已更改，更新PID文件
            echo "$running_pid" > "$pid_file_path"
            warning_log "$service_name PID已更新，旧PID: $pid_file，新PID: $running_pid"
        fi
    else
        # 创建PID文件
        echo "$running_pid" > "$pid_file_path"
        info_log "$service_name PID文件已创建: $pid_file_path"
    fi
}

# 检查单个服务的状态
check_single_service() {
    local service_name=$1
    local service_script=$2
    local pid_file=$3
    local error_prefix=$4
    local running_pid
    
    running_pid=$(pgrep -f "node $service_script")
    if [ -n "$running_pid" ]; then
        # 服务正在运行
        echo -e "${GREEN}✓ $service_name: 运行中 (PID: $running_pid)${NC}"
        ((services_running++))
        
        # 管理PID文件
        manage_pid_file "$service_name" "$running_pid" "$pid_file"
        return 0
    else
        # 服务未运行
        if [ -f "$pid_file" ]; then
            echo -e "${RED}✗ $service_name: 已停止 (PID文件存在但进程不存在)${NC}"
            error_log "$service_name PID文件存在，但进程未运行"
            auto_repair "PID_FILE_ERROR" "$error_prefix PID文件无效"
        else
            echo -e "${RED}✗ $service_name: 未运行${NC}"
            error_log "$service_name未运行 (无PID文件)"
            auto_repair "SERVER_NOT_RUNNING" "$error_prefix未运行"
        fi
        return 1
    fi
}

# 在check_all_services函数中的服务检查部分
    # 检查主服务器
    check_single_service "主服务器" "$MAIN_SERVER" "$SERVER_PID" "主服务器"
    
    # 检查监控服务
    local monitor_script="$MONITORING_DIR/environment-monitor.js"
    check_single_service "监控服务" "$monitor_script" "$MONITOR_PID" "监控服务"
    
    # 检查DeepSeek服务
    local deepseek_script="$PROJECT_DIR/Staging/Scripts/deepseek-engine.js"
    check_single_service "DeepSeek服务" "$deepseek_script" "$DEEPSEEK_PID" "DeepSeek服务"
    
    echo -e "${CYAN}=================================${NC}\n"
    
    # 在自动修复后重新检查服务状态，确保services_running变量准确
    local services_running_after_repair=0
    local total_services=3
    
    # 重新检查所有服务状态以获取最新情况
    local main_server_running_pid=$(pgrep -f "node $MAIN_SERVER")
    local monitor_script="$MONITORING_DIR/environment-monitor.js"
    local monitor_running_pid=$(pgrep -f "node $monitor_script")
    local deepseek_script="$PROJECT_DIR/Staging/Scripts/deepseek-engine.js"
    local deepseek_running_pid=$(pgrep -f "node $deepseek_script")
    
    [ -n "$main_server_running_pid" ] && ((services_running_after_repair++))
    [ -n "$monitor_running_pid" ] && ((services_running_after_repair++))
    [ -n "$deepseek_running_pid" ] && ((services_running_after_repair++))
    
    # 更新services_running变量
    services_running=$services_running_after_repair
    
    # 如果有服务未运行，记录为异常
    if [ $services_running -lt $total_services ]; then
        error_log "部分服务未运行: $services_running/$total_services 个服务正常运行"
    else
        success_log "所有服务均正常运行"
    fi
    
    return 0
}

# 执行系统健康检查
run_health_check() {
    info_log "执行系统健康检查..."
    
    # 检查配置文件
    if [ ! -f "$CONFIG_FILE" ]; then
        error_log "配置文件不存在: $CONFIG_FILE"
        auto_repair "FILE_NOT_FOUND" "配置文件 $CONFIG_FILE 不存在"
        # 再次检查
        if [ ! -f "$CONFIG_FILE" ]; then
            error_log "自动修复失败：配置文件仍不存在"
            return 1
        fi
    fi
    success_log "配置文件存在: $CONFIG_FILE"
    
    # 检查主服务器文件
    if [ ! -f "$MAIN_SERVER" ]; then
        error_log "主服务器文件不存在: $MAIN_SERVER"
        auto_repair "FILE_NOT_FOUND" "主服务器文件 $MAIN_SERVER 不存在"
        # 再次检查
        if [ ! -f "$MAIN_SERVER" ]; then
            error_log "自动修复失败：主服务器文件仍不存在"
            return 1
        fi
    fi
    success_log "主服务器文件存在: $MAIN_SERVER"
    
    # 检查日志目录
    if [ ! -d "$LOG_DIR" ]; then
        error_log "日志目录不存在，正在创建..."
        mkdir -p "$LOG_DIR"
        if [ $? -ne 0 ]; then
            error_log "创建日志目录失败，尝试修复..."
            auto_repair "DIRECTORY_CREATE_FAILED" "日志目录 $LOG_DIR 创建失败"
            if [ ! -d "$LOG_DIR" ]; then
                error_log "自动修复失败：日志目录仍未创建"
                return 1
            fi
        fi
        success_log "日志目录已创建: $LOG_DIR"
    else
        success_log "日志目录存在: $LOG_DIR"
    fi
    
    success_log "系统健康检查完成"
    return 0
}

# 清理临时文件
cleanup_temp() {
    info_log "清理临时文件..."
    
    local temp_dirs=("$PROJECT_DIR/Temp" "$PROJECT_DIR/Staging/Temp")
    for temp_dir in "${temp_dirs[@]}"; do
        if [ -d "$temp_dir" ]; then
            rm -rf "$temp_dir"/*
            success_log "清理临时目录: $temp_dir"
        fi
    done
    
    return 0
}

# 主启动函数
start_all() {
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${PURPLE}        MTSCOS AI Project 启动脚本 v2.0        ${NC}"
    echo -e "${PURPLE}===============================================${NC}\n"
    
    # 设置总进度步骤数
    local total_steps=6
    local current_step=0
    local overall_progress=0
    
    # 步骤1: 检查Node.js和npm环境
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 检查Node.js和npm环境 (${overall_progress}%)${NC}"
    
    if ! check_environment; then
        error_log "环境检查失败，无法启动项目"
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "环境检查失败，启动进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    # 步骤2: 执行系统健康检查
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 执行系统健康检查 (${overall_progress}%)${NC}"
    
    if ! run_health_check; then
        error_log "系统健康检查失败，无法启动项目"
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "系统健康检查失败，启动进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    # 步骤3: 安装依赖
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 安装依赖 (${overall_progress}%)${NC}"
    
    if ! install_dependencies; then
        error_log "依赖安装失败，无法启动项目"
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "依赖安装失败，启动进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    # 步骤4: 清理临时文件
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 清理临时文件 (${overall_progress}%)${NC}"
    
    if ! cleanup_temp; then
        warning_log "清理临时文件时出现问题"
        # 清理临时文件失败不中断启动，但记录警告
    fi
    
    # 步骤5: 启动所有服务
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 启动所有服务 (${overall_progress}%)${NC}"
    
    local services_started=0
    local max_start_attempts=3
    local attempt=0
    local total_services=3
    
    while [ $services_started -lt $total_services ] && [ $attempt -lt $max_start_attempts ]; do
        ((attempt++))
        services_started=0
        
        echo -e "${CYAN}--- 启动尝试 $attempt/$max_start_attempts ---${NC}"
        
        # 启动主服务器
        if start_main_server; then
            ((services_started++))
            echo -e "${GREEN}✓ 主服务器启动成功${NC}"
        else
            echo -e "${RED}✗ 主服务器启动失败${NC}"
        fi
        
        # 启动监控服务
        if start_monitoring; then
            ((services_started++))
            echo -e "${GREEN}✓ 监控服务启动成功${NC}"
        else
            echo -e "${RED}✗ 监控服务启动失败${NC}"
        fi
        
        # 启动DeepSeek服务
        if start_deepseek; then
            ((services_started++))
            echo -e "${GREEN}✓ DeepSeek服务启动成功${NC}"
        else
            echo -e "${RED}✗ DeepSeek服务启动失败${NC}"
        fi
        
        # 如果有服务未启动，等待并重试
        if [ $services_started -lt $total_services ]; then
            warning_log "部分服务启动失败，成功: $services_started/$total_services"
            warning_log "尝试第 $attempt/$max_start_attempts 次重新启动..."
            sleep 3
        else
            break
        fi
    done
    
    echo -e "${CYAN}--- 启动尝试完成 ---${NC}"
    
    # 使用pgrep重新检查实际运行的服务数量
    local actual_running_services=0
    [ -n "$(pgrep -f "node $MAIN_SERVER")" ] && ((actual_running_services++))
    [ -n "$(pgrep -f "node $MONITORING_DIR/environment-monitor.js")" ] && ((actual_running_services++))
    [ -n "$(pgrep -f "node $PROJECT_DIR/Staging/Scripts/deepseek-engine.js")" ] && ((actual_running_services++))
    
    # 更新services_started变量为实际运行的服务数量
    services_started=$actual_running_services
    
    if [ $services_started -lt $total_services ]; then
        error_log "部分服务启动失败，成功: $services_started/$total_services"
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "启动进度未达到100%，当前进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    success_log "所有服务已成功启动: $services_started/$total_services"
    
    # 步骤6: 检查所有服务状态
    ((current_step++))
    overall_progress=$((current_step * 100 / total_steps))
    echo -e "${BLUE}步骤 $current_step/$total_steps: 检查所有服务状态 (${overall_progress}%)${NC}"
    
    if ! check_all_services; then
        error_log "服务状态检查失败"
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "服务状态检查失败，启动进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    # 最终进度检查
    if [ $overall_progress -ne 100 ]; then
        error_log "启动进度未达到100%，当前进度: ${overall_progress}%"
        if auto_repair "STARTUP_PROGRESS_INCOMPLETE" "启动未完全完成，当前进度: ${overall_progress}%"; then
            return 0
        else
            return 1
        fi
    fi
    
    # 仅在非修复模式下显示最终启动信息
    if [ -z "$REPAIR_MODE" ]; then
        echo -e "${PURPLE}===============================================${NC}"
        echo -e "${GREEN}项目启动完成！100%${NC}"
        echo -e "${BLUE}主服务器日志: $SERVER_LOG${NC}"
        echo -e "${BLUE}DeepSeek日志: $DEEPSEEK_LOG${NC}"
        echo -e "${PURPLE}===============================================${NC}\n"
    fi
    
    return 0
}

# 重启所有服务
restart_all() {
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${PURPLE}        MTSCOS AI Project 重启服务        ${NC}"
    echo -e "${PURPLE}===============================================${NC}\n"
    
    stop_all_services
    sleep 2
    start_all
    
    return $?
}

# 显示帮助信息
show_help() {
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${PURPLE}        MTSCOS AI Project 启动脚本 v2.0        ${NC}"
    echo -e "${PURPLE}===============================================${NC}\n"
    echo -e "${CYAN}用法: ${WHITE}$0 [命令]${NC}"
    echo -e "\n${CYAN}可用命令:${NC}"
    echo -e "${WHITE}  start    ${NC} - 启动所有服务"
    echo -e "${WHITE}  stop     ${NC} - 停止所有服务"
    echo -e "${WHITE}  restart  ${NC} - 重启所有服务"
    echo -e "${WHITE}  status   ${NC} - 检查服务状态"
    echo -e "${WHITE}  health   ${NC} - 执行系统健康检查"
    echo -e "${WHITE}  cleanup  ${NC} - 清理临时文件"
    echo -e "${WHITE}  help     ${NC} - 显示帮助信息"
    echo -e "\n${PURPLE}===============================================${NC}\n"
    return 0
}

# 主函数
main() {
    # 设置脚本权限
    chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null
    
    # 检查命令行参数
    if [ $# -eq 0 ]; then
        # 默认执行启动操作
        start_all
        exit $?
    fi
    
    case "$1" in
        start)
            start_all
            exit $?
            ;;
        stop)
            echo -e "${PURPLE}===============================================${NC}"
            echo -e "${PURPLE}        MTSCOS AI Project 停止服务        ${NC}"
            echo -e "${PURPLE}===============================================${NC}\n"
            stop_all_services
            exit $?
            ;;
        restart)
            restart_all
            exit $?
            ;;
        status)
            check_all_services
            exit $?
            ;;
        health)
            run_health_check
            exit $?
            ;;
        cleanup)
            cleanup_temp
            exit $?
            ;;
        help)
            show_help
            exit 0
            ;;
        *)
            error_log "无效的命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"