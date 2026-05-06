#!/bin/bash

# MTSCOS 系统恢复脚本
# 用于从ISO镜像恢复系统

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    local level=1
    local message=2
    local color
    
    case level in
        "info") color=BLUE ;;
        "success") color=GREEN ;;
        "warning") color=YELLOW ;;
        "error") color=RED ;;
        *) color=NC ;;
    esac
    
    echo -e "[$level]\033[0m $message"
}

main() {
    print_message "info" "MTSCOS 系统恢复"
    print_message "info" "=================================="
    
    local backup_source="$1"
    local restore_target="$2"
    
    if [ -z "$backup_source" ] || [ -z "$restore_target" ]; then
        print_message "error" "用法: $0 <备份源> <恢复目标目录>"
        exit 1
    fi
    
    if [ ! -d "$backup_source" ]; then
        print_message "error" "备份源不存在"
        exit 1
    fi
    
    if [ ! -d "$restore_target" ]; then
        print_message "warning" "恢复目标目录不存在，创建中..."
        mkdir -p "$restore_target"
    fi
    
    print_message "info" "开始从 $backup_source 恢复到 $restore_target"
    
    # 同步文件
    rsync -avz "$backup_source/" "$restore_target/"
    
    if [ $? -eq 0 ]; then
        print_message "success" "系统恢复成功"
        print_message "info" "请运行 ./init_system.sh 完成初始化"
    else
        print_message "error" "系统恢复失败"
        exit 1
    fi
}

main "$@"
