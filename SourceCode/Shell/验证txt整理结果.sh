#!/bin/bash
# 验证txt文件整理结果脚本

BASE_DIR="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/整理后的文本文件"
echo "===== TXT文件整理结果验证 ====="
echo "验证时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

echo "各分类目录文件数量统计:"
echo "----------------------"

# 遍历各分类目录
for category in "$BASE_DIR"/*; do
    if [ -d "$category" ]; then
        dir_name=$(basename "$category")
        file_count=$(find "$category" -type f -name "*.txt" | wc -l)
        echo "$dir_name: $file_count 个文件"
    fi
done

echo ""
echo "总文件数: $(find "$BASE_DIR" -type f -name "*.txt" | wc -l)"
echo ""

# 查看报告文件内容
echo "整理报告摘要:"
echo "----------------------"
cat "$BASE_DIR/../txt_organize_report.json"
echo ""
echo "===== 验证完成 ====="