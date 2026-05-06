#!/bin/bash

# 验证bak文件整理结果脚本
echo "=== 验证备份文件整理结果 ==="
echo "检查时间: $(date)"
echo ""

BASE_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
BACKUP_DIR="${BASE_DIR}/整理后的备份文件"
ORG_REPORT="${BASE_DIR}/bak_organize_report.json"
FIXED_REPORT="${BASE_DIR}/bak_organize_report_fixed.json"

echo "整理后备份目录: ${BACKUP_DIR}"
echo "原始报告文件: ${ORG_REPORT}"
echo "修复版报告文件: ${FIXED_REPORT}"
echo ""

# 检查整理后的备份文件目录是否存在
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "错误: 整理后的备份文件目录不存在!"
    exit 1
fi

# 函数: 统计目录下的文件数量
count_files() {
    local dir="$1"
    find "${dir}" -type f | wc -l
}

# 函数: 递归统计每个分类目录下的文件数量
count_by_category() {
    local root_dir="$1"
    echo "按分类统计文件数量:"
    echo "---------------------------------------------"
    
    local total_files=0
    
    for category in "${root_dir}"/*; do
        if [ -d "${category}" ]; then
            local category_name=$(basename "${category}")
            local category_count=$(count_files "${category}")
            echo "${category_name}: ${category_count} 个文件"
            total_files=$((total_files + category_count))
            
            # 进一步按日期统计
            echo "  按日期细分:"
            for date_dir in "${category}"/*; do
                if [ -d "${date_dir}" ]; then
                    local date_name=$(basename "${date_dir}")
                    local date_count=$(count_files "${date_dir}")
                    echo "    - ${date_name}: ${date_count} 个文件"
                fi
            done
            echo ""
        fi
    done
    
    echo "---------------------------------------------"
    echo "总文件数量: ${total_files}"
    echo ""
    
    return ${total_files}
}

# 函数: 显示最新的报告文件摘要
show_report_summary() {
    if [ -f "${FIXED_REPORT}" ]; then
        echo "修复版报告摘要:"
        echo "---------------------------------------------"
        cat "${FIXED_REPORT}" | grep -E '"start_time"|"end_time"|"duration"|"total_files"|"organized_files"|"errors"'
        echo ""
        echo "按类型统计:"
        cat "${FIXED_REPORT}" | grep -A 15 '"by_type"'
        echo "---------------------------------------------"
        echo ""
    elif [ -f "${ORG_REPORT}" ]; then
        echo "原始报告摘要:"
        echo "---------------------------------------------"
        cat "${ORG_REPORT}" | grep -E '"start_time"|"end_time"|"duration"|"total_files"|"organized_files"|"errors"'
        echo ""
        echo "按类型统计:"
        cat "${ORG_REPORT}" | grep -A 15 '"by_type"'
        echo "---------------------------------------------"
        echo ""
    else
        echo "警告: 未找到整理报告文件!"
        echo ""
    fi
}

# 函数: 检查文件类型和命名
check_file_types() {
    echo "检查部分文件样本:"
    echo "---------------------------------------------"
    
    # 从每个分类中获取一些文件样本
    for category in "${BACKUP_DIR}"/*; do
        if [ -d "${category}" ]; then
            local category_name=$(basename "${category}")
            echo "${category_name} 样本文件:"
            
            # 查找最近的日期目录
            latest_date=$(ls -d "${category}"/*/ 2>/dev/null | sort -r | head -n 1)
            
            if [ -n "${latest_date}" ]; then
                # 显示该日期目录中的前5个文件
                local file_count=0
                for file in "${latest_date}"/*; do
                    if [ -f "${file}" ]; then
                        local file_name=$(basename "${file}")
                        local file_size=$(du -h "${file}" | cut -f1)
                        echo "  - ${file_name} (${file_size})"
                        file_count=$((file_count + 1))
                        if [ ${file_count} -ge 5 ]; then
                            break
                        fi
                    fi
                done
                
                if [ ${file_count} -eq 0 ]; then
                    echo "  无文件"
                fi
            else
                echo "  无日期目录"
            fi
            
            echo ""
        fi
    done
    
    echo "---------------------------------------------"
    echo ""
}

# 函数: 检查目录结构
check_directory_structure() {
    echo "目录结构检查:"
    echo "---------------------------------------------"
    
    # 使用tree命令显示目录结构，但限制深度
    find "${BACKUP_DIR}" -type d -maxdepth 3 | sort
    
    echo "---------------------------------------------"
    echo ""
}

# 函数: 检查空目录
check_empty_directories() {
    echo "空目录检查:"
    echo "---------------------------------------------"
    
    local empty_dirs=$(find "${BACKUP_DIR}" -type d -empty | wc -l)
    echo "空目录数量: ${empty_dirs}"
    
    if [ ${empty_dirs} -gt 0 ]; then
        echo "空目录列表:"
        find "${BACKUP_DIR}" -type d -empty | sort
    fi
    
    echo "---------------------------------------------"
    echo ""
}

# 主函数
echo "1. 目录结构检查"
check_directory_structure

echo "2. 按分类统计文件数量"
count_by_category "${BACKUP_DIR}"
total_organized=$?

echo "3. 检查文件类型样本"
check_file_types

echo "4. 空目录检查"
check_empty_directories

echo "5. 报告文件摘要"
show_report_summary

# 总结
echo "=== 验证总结 ==="
echo "总整理文件数量: ${total_organized}"
echo "备份文件目录: ${BACKUP_DIR}"
echo "验证完成!"