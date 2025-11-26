#!/bin/bash

# MTSCOS AI 系统自动服务启动脚本
# 用于启动所有自动检测、修复、维护和监控服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MTSCOS AI 系统自动服务启动脚本  ${NC}"
echo -e "${GREEN}========================================${NC}"

# 配置文件路径
CONFIG_PATH="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json"
BASE_PATH="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Staging"
LOG_DIR="$BASE_PATH/Logs"
SCRIPTS_DIR="$BASE_PATH/Scripts"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

echo -e "${YELLOW}开始启动自动服务...${NC}"

# 检查配置文件
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG_PATH${NC}"
    echo -e "${YELLOW}请先创建配置文件再运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 配置文件检查通过${NC}"

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: Node.js 未安装${NC}"
    echo -e "${YELLOW}请先安装Node.js再运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js 检查通过${NC}"

# 启动环境监控脚本
start_monitor() {
    MONITOR_SCRIPT="$SCRIPTS_DIR/monitoring/environment-monitor.js"
    if [ -f "$MONITOR_SCRIPT" ]; then
        echo -e "${YELLOW}启动环境监控服务...${NC}"
        # 检查进程是否已在运行
        if pgrep -f "node.*environment-monitor.js" &> /dev/null; then
            echo -e "${YELLOW}环境监控服务已在运行${NC}"
        else
            nohup node "$MONITOR_SCRIPT" > "$LOG_DIR/environment-monitor.log" 2>&1 &
            MONITOR_PID=$!
            echo -e "${GREEN}✓ 环境监控服务已启动 (PID: $MONITOR_PID)${NC}"
        fi
    else
        echo -e "${YELLOW}警告: 环境监控脚本不存在: $MONITOR_SCRIPT${NC}"
    fi
}

# 启动自动检测与修复引擎
start_detection_engine() {
    DETECTION_SCRIPT="$SCRIPTS_DIR/monitoring/auto-detection-repair.js"
    if [ -f "$DETECTION_SCRIPT" ]; then
        echo -e "${YELLOW}启动自动检测与修复引擎...${NC}"
        # 检查进程是否已在运行
        if pgrep -f "node.*auto-detection-repair.js" &> /dev/null; then
            echo -e "${YELLOW}自动检测与修复引擎已在运行${NC}"
        else
            nohup node "$DETECTION_SCRIPT" start > "$LOG_DIR/auto-detection.log" 2>&1 &
            DETECTION_PID=$!
            echo -e "${GREEN}✓ 自动检测与修复引擎已启动 (PID: $DETECTION_PID)${NC}"
        fi
    else
        echo -e "${YELLOW}警告: 自动检测脚本不存在: $DETECTION_SCRIPT${NC}"
    fi
}

# 启动环境维护脚本
start_maintenance() {
    MAINTENANCE_SCRIPT="$SCRIPTS_DIR/maintenance/environment-maintenance.js"
    if [ -f "$MAINTENANCE_SCRIPT" ]; then
        echo -e "${YELLOW}启动环境维护服务...${NC}"
        # 检查进程是否已在运行
        if pgrep -f "node.*environment-maintenance.js" &> /dev/null; then
            echo -e "${YELLOW}环境维护服务已在运行${NC}"
        else
            nohup node "$MAINTENANCE_SCRIPT" > "$LOG_DIR/environment-maintenance.log" 2>&1 &
            MAINTENANCE_PID=$!
            echo -e "${GREEN}✓ 环境维护服务已启动 (PID: $MAINTENANCE_PID)${NC}"
        fi
    else
        echo -e "${YELLOW}警告: 环境维护脚本不存在: $MAINTENANCE_SCRIPT${NC}"
    fi
}

# 创建PID文件记录服务进程ID
create_pid_file() {
    PID_FILE="$BASE_PATH/service-pids.txt"
    echo "# 服务进程ID记录 - 创建时间: $(date)" > "$PID_FILE"
    echo "# 请勿手动修改此文件" >> "$PID_FILE"
    echo "" >> "$PID_FILE"
    
    if [ ! -z "$MONITOR_PID" ]; then
        echo "MONITOR_PID=$MONITOR_PID" >> "$PID_FILE"
    fi
    if [ ! -z "$DETECTION_PID" ]; then
        echo "DETECTION_PID=$DETECTION_PID" >> "$PID_FILE"
    fi
    if [ ! -z "$MAINTENANCE_PID" ]; then
        echo "MAINTENANCE_PID=$MAINTENANCE_PID" >> "$PID_FILE"
    fi
    
    echo -e "${GREEN}✓ 服务进程ID已记录到: $PID_FILE${NC}"
}

# 检查所有服务状态
check_services() {
    echo -e "${YELLOW}\n检查服务状态...${NC}"
    
    # 检查环境监控服务
    if pgrep -f "node.*environment-monitor.js" &> /dev/null; then
        echo -e "${GREEN}✓ 环境监控服务: 运行中${NC}"
    else
        echo -e "${RED}✗ 环境监控服务: 未运行${NC}"
    fi
    
    # 检查自动检测与修复引擎
    if pgrep -f "node.*auto-detection-repair.js" &> /dev/null; then
        echo -e "${GREEN}✓ 自动检测与修复引擎: 运行中${NC}"
    else
        echo -e "${RED}✗ 自动检测与修复引擎: 未运行${NC}"
    fi
    
    # 检查环境维护服务
    if pgrep -f "node.*environment-maintenance.js" &> /dev/null; then
        echo -e "${GREEN}✓ 环境维护服务: 运行中${NC}"
    else
        echo -e "${RED}✗ 环境维护服务: 未运行${NC}"
    fi
}

# 注册服务到开机启动（仅在支持的系统上）
setup_auto_start() {
    if [ "$1" == "--auto-start" ]; then
        echo -e "${YELLOW}\n配置开机自启动...${NC}"
        
        # 获取当前脚本的绝对路径
        CURRENT_SCRIPT="$(realpath "$0")"
        
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            echo -e "${YELLOW}检测到 macOS 系统${NC}"
            LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"
            PLIST_FILE="$LAUNCHAGENTS_DIR/com.mtscos.auto.services.plist"
            
            # 创建LaunchAgents目录
            mkdir -p "$LAUNCHAGENTS_DIR"
            
            # 创建plist文件
            cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mtscos.auto.services</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$CURRENT_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/auto-start.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/auto-start-error.log</string>
</dict>
</plist>
EOF
            
            echo -e "${GREEN}✓ 已创建开机自启动配置: $PLIST_FILE${NC}"
            echo -e "${YELLOW}提示: 要加载此配置，请运行: launchctl load $PLIST_FILE${NC}"
            
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            echo -e "${YELLOW}检测到 Linux 系统${NC}"
            SYSTEMD_DIR="$HOME/.config/systemd/user"
            SERVICE_FILE="$SYSTEMD_DIR/mtscos-auto-services.service"
            
            # 创建systemd目录
            mkdir -p "$SYSTEMD_DIR"
            
            # 创建service文件
            cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MTSCOS AI Auto Services
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash $CURRENT_SCRIPT
Restart=on-failure
RestartSec=10
StandardOutput=append:$LOG_DIR/auto-start.log
StandardError=append:$LOG_DIR/auto-start-error.log

[Install]
WantedBy=default.target
EOF
            
            echo -e "${GREEN}✓ 已创建systemd服务配置: $SERVICE_FILE${NC}"
            echo -e "${YELLOW}提示: 要启用并启动此服务，请运行:${NC}"
            echo -e "${YELLOW}systemctl --user daemon-reload${NC}"
            echo -e "${YELLOW}systemctl --user enable mtscos-auto-services.service${NC}"
            echo -e "${YELLOW}systemctl --user start mtscos-auto-services.service${NC}"
        else
            echo -e "${YELLOW}不支持的系统类型，跳过开机自启动配置${NC}"
        fi
    fi
}

# 停止所有服务
stop_services() {
    echo -e "${YELLOW}\n停止所有服务...${NC}"
    
    # 检查PID文件
    PID_FILE="$BASE_PATH/service-pids.txt"
    if [ -f "$PID_FILE" ]; then
        # 读取PID并停止进程
        if grep -q "MONITOR_PID=" "$PID_FILE"; then
            MONITOR_PID=$(grep "MONITOR_PID=" "$PID_FILE" | cut -d'=' -f2)
            if [ ! -z "$MONITOR_PID" ] && kill -0 "$MONITOR_PID" 2>/dev/null; then
                kill "$MONITOR_PID" 2>/dev/null || true
                echo -e "${GREEN}✓ 已停止环境监控服务 (PID: $MONITOR_PID)${NC}"
            fi
        fi
        
        if grep -q "DETECTION_PID=" "$PID_FILE"; then
            DETECTION_PID=$(grep "DETECTION_PID=" "$PID_FILE" | cut -d'=' -f2)
            if [ ! -z "$DETECTION_PID" ] && kill -0 "$DETECTION_PID" 2>/dev/null; then
                kill "$DETECTION_PID" 2>/dev/null || true
                echo -e "${GREEN}✓ 已停止自动检测与修复引擎 (PID: $DETECTION_PID)${NC}"
            fi
        fi
        
        if grep -q "MAINTENANCE_PID=" "$PID_FILE"; then
            MAINTENANCE_PID=$(grep "MAINTENANCE_PID=" "$PID_FILE" | cut -d'=' -f2)
            if [ ! -z "$MAINTENANCE_PID" ] && kill -0 "$MAINTENANCE_PID" 2>/dev/null; then
                kill "$MAINTENANCE_PID" 2>/dev/null || true
                echo -e "${GREEN}✓ 已停止环境维护服务 (PID: $MAINTENANCE_PID)${NC}"
            fi
        fi
        
        # 删除PID文件
        rm -f "$PID_FILE"
    fi
    
    # 强制停止可能存在的进程
    echo -e "${YELLOW}清理残留进程...${NC}"
    pkill -f "node.*environment-monitor.js" 2>/dev/null || true
    pkill -f "node.*auto-detection-repair.js" 2>/dev/null || true
    pkill -f "node.*environment-maintenance.js" 2>/dev/null || true
    
    echo -e "${GREEN}✓ 所有服务已停止${NC}"
}

# 重启所有服务
restart_services() {
    echo -e "${YELLOW}\n重启所有服务...${NC}"
    stop_services
    sleep 2
    start_all_services
}

# 启动所有服务
start_all_services() {
    start_monitor
    start_detection_engine
    start_maintenance
    create_pid_file
    check_services
    setup_auto_start "$1"
    
    echo -e "${GREEN}\n========================================${NC}"
    echo -e "${GREEN}  所有自动服务启动完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  - 停止服务: $0 stop"
    echo -e "  - 重启服务: $0 restart"
    echo -e "  - 查看状态: $0 status"
}

# 显示服务状态
show_status() {
    echo -e "${GREEN}\n========================================${NC}"
    echo -e "${GREEN}  MTSCOS AI 系统服务状态${NC}"
    echo -e "${GREEN}========================================${NC}"
    check_services
    
    # 显示最新日志信息
    echo -e "${YELLOW}\n最新日志信息:${NC}"
    if [ -f "$LOG_DIR/environment-monitor.log" ]; then
        echo -e "${GREEN}环境监控日志:${NC}"
        tail -n 3 "$LOG_DIR/environment-monitor.log" || echo "无法读取日志"
    fi
    
    if [ -f "$LOG_DIR/auto-detection.log" ]; then
        echo -e "${GREEN}\n自动检测日志:${NC}"
        tail -n 3 "$LOG_DIR/auto-detection.log" || echo "无法读取日志"
    fi
    
    if [ -f "$LOG_DIR/environment-maintenance.log" ]; then
        echo -e "${GREEN}\n环境维护日志:${NC}"
        tail -n 3 "$LOG_DIR/environment-maintenance.log" || echo "无法读取日志"
    fi
    
    echo -e "${GREEN}\n========================================${NC}"
}

# 主函数 - 根据命令行参数执行不同操作
main() {
    # 设置脚本执行权限
    chmod +x "$0"
    
    case "$1" in
        "start")
            start_all_services "$2"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services "$2"
            ;;
        "status")
            show_status
            ;;
        *)
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}  MTSCOS AI 系统自动服务管理脚本  ${NC}"
            echo -e "${GREEN}========================================${NC}"
            echo -e "${YELLOW}用法: $0 [command] [options]${NC}"
            echo -e ""
            echo -e "${GREEN}命令:${NC}"
            echo -e "  start    - 启动所有自动服务"
            echo -e "  stop     - 停止所有自动服务"
            echo -e "  restart  - 重启所有自动服务"
            echo -e "  status   - 查看服务状态"
            echo -e ""
            echo -e "${GREEN}选项:${NC}"
            echo -e "  --auto-start  - 配置开机自启动（仅在支持的系统上）"
            echo -e ""
            echo -e "${YELLOW}示例:${NC}"
            echo -e "  $0 start         # 启动所有服务"
            echo -e "  $0 start --auto-start  # 启动服务并配置开机自启动"
            echo -e "  $0 stop          # 停止所有服务"
            echo -e "  $0 status        # 查看服务状态"
            echo -e "${GREEN}========================================${NC}"
            ;;
    esac
}

# 执行主函数
main "$@"