#!/bin/bash

# 自动整理归类文件脚本 (版本: 2.0)
# 功能：扫描目录中的bak、py、txt文件，按日期或类型归类，并显示进度条

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
BASE_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
OUTPUT_DIR="${BASE_DIR}/整理后的备份文件"
LOG_FILE="${BASE_DIR}/Logs/备份工具/$(date +"%Y-%m-%d")_organize_files.log"

# 支持的文件类型
SUPPORTED_TYPES=("*.bak" "*.py" "*.txt")

# 创建输出目录和日志目录
mkdir -p "${OUTPUT_DIR}/按日期"
mkdir -p "${OUTPUT_DIR}/按类型"
mkdir -p "$(dirname "${LOG_FILE}")"

# 日志函数
log() {
    local message="$1"
    # 先输出到终端（保持颜色）
    echo -e "${message}"
    # 移除颜色代码后写入日志
    local clean_message="${message}"
    # 更健壮的颜色代码移除
    clean_message=$(echo "${clean_message}" | sed 's/\x1b\[[0-9;]*[mK]//g')
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${clean_message}" >> "${LOG_FILE}"
}

# 进度条函数
show_progress() {
    local progress=$1
    local total=$2
    # 防止除零错误
    if [[ $total -eq 0 ]]; then
        percentage=0
    else
        percentage=$((progress * 100 / total))
    fi
    local bar_length=50
    local filled_length=$((percentage * bar_length / 100))
    
    # 使用字符串操作构建进度条，避免printf格式问题
    local bar=""
    for ((i=0; i<filled_length; i++)); do
        bar+="#"
    done
    for ((i=filled_length; i<bar_length; i++)); do
        bar+="-"
    done
    
    # 使用echo -ne显示进度条
    echo -ne "\r${BLUE}[${bar}]${NC} ${percentage}% (${progress}/${total}) 文件处理中..."
}

# 统计目标文件
count_target_files() {
    local total=0
    log "${YELLOW}正在扫描支持的文件类型...${NC}"
    
    # 使用find命令递归查找所有支持的文件类型，排除输出目录
    target_files=()
    
    for pattern in "${SUPPORTED_TYPES[@]}"; do
        log "${BLUE}正在搜索 ${pattern} 文件...${NC}"
        while IFS= read -r -d '' file; do
            # 排除输出目录中的文件
            if [[ "$file" != "${OUTPUT_DIR}"* ]]; then
                target_files+=("$file")
            fi
        done < <(find "${BASE_DIR}" -type f -name "$pattern" -print0 2>/dev/null)
    done
    
    total=${#target_files[@]}
    log "${GREEN}找到 ${total} 个支持的文件${NC}"
    return $total
}

# 按日期归类文件
organize_by_date() {
    local file=$1
    local date_dir
    
    # 获取文件修改日期（兼容不同系统）
    if [[ "$(uname)" == "Darwin" ]]; then
        mod_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$file")
    else
        mod_date=$(date -r "$file" +"%Y-%m-%d")
    fi
    
    date_dir="${OUTPUT_DIR}/按日期/${mod_date}"
    mkdir -p "$date_dir" 2>/dev/null || true
    
    # 安全地复制文件
    if cp "$file" "${date_dir}/$(basename "$file")" 2>/dev/null; then
        # 仅在详细日志模式下记录每个文件
        if [[ "$VERBOSE" == "true" ]]; then
            log "${BLUE}已将 $(basename "$file") 复制到 ${mod_date} 目录${NC}"
        fi
        return 0
    else
        log "${RED}复制 $(basename "$file") 失败${NC}"
        return 1
    fi
}

# 按类型归类文件
organize_by_type() {
    local file=$1
    local type_dir
    local filename=$(basename "$file")
    local ext="unknown"
    
    # 提取文件类型（根据bak前的扩展名）
    if [[ "$filename" == *.bak ]]; then
        # 移除.bak后缀
        temp=${filename%.bak}
        # 获取原始扩展名
        if [[ "$temp" == *.* ]]; then
            ext=${temp##*.}
        fi
    fi
    
    type_dir="${OUTPUT_DIR}/按类型/${ext}"
    mkdir -p "$type_dir" 2>/dev/null || true
    
    # 安全地复制文件
    if cp "$file" "${type_dir}/$(basename "$file")" 2>/dev/null; then
        return 0
    else
        log "${RED}复制 $(basename "$file") 到类型目录失败${NC}"
        return 1
    fi
}

# 主函数
main() {
    # 解析参数
    VERBOSE=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            *)
                log "${YELLOW}未知参数: $1${NC}"
                shift
                ;;
        esac
    done
    
    log "${GREEN}========================================${NC}"
    log "${GREEN}开始整理文件 (版本: 2.0) - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    log "${GREEN}========================================${NC}"
    log "${BLUE}支持的文件类型: ${SUPPORTED_TYPES[*]}${NC}"
    
    # 统计文件
    target_files=()
    for pattern in "${SUPPORTED_TYPES[@]}"; do
        log "${YELLOW}正在扫描 ${pattern} 文件...${NC}"
        while IFS= read -r -d '' file; do
            # 排除输出目录中的文件
            if [[ "$file" != "${OUTPUT_DIR}"* ]]; then
                target_files+=("$file")
            fi
        done < <(find "${BASE_DIR}" -type f -name "$pattern" -print0 2>/dev/null)
    done
    
    total_count=${#target_files[@]}
    log "${GREEN}找到 ${total_count} 个支持的文件${NC}"
    
    if [[ $total_count -eq 0 ]]; then
        log "${YELLOW}没有找到支持的文件，退出${NC}"
        exit 0
    fi
    
    # 处理文件
    local processed=0
    local success=0
    local failed=0
    
    log "${YELLOW}开始处理文件，请稍候...${NC}"
    
    for file in "${target_files[@]}"; do
        processed=$((processed + 1))
        
        # 显示进度条
        show_progress $processed $total_count
        
        # 按日期和类型归类
        if organize_by_date "$file" && organize_by_type "$file"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
        
        # 避免进度条更新过快
        if [[ $processed -lt $total_count ]]; then
            # 每10个文件更新一次进度，提高大文件处理效率
            if [[ $((processed % 10)) -eq 0 || $processed -eq $total_count ]]; then
                sleep 0.01
            fi
        fi
    done
    
    # 完成
    printf "\n\n"
    log "${GREEN}========================================${NC}"
    log "${GREEN}文件整理完成！${NC}"
    log "${GREEN}总共处理: ${total_count} 个文件${NC}"
    log "${GREEN}成功: ${success} 个文件${NC}"
    if [[ $failed -gt 0 ]]; then
        log "${RED}失败: ${failed} 个文件${NC}"
    fi
    log "${GREEN}输出目录: ${OUTPUT_DIR}${NC}"
    log "${GREEN}日志文件: ${LOG_FILE}${NC}"
    log "${GREEN}========================================${NC}"
}

# 执行主函数
main