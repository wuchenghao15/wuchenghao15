#!/bin/bash

# 批量修复JavaScript文件中的Date.now().catch()错误
# 作者: 系统修复工具
# 日期: $(date)

echo "开始批量修复JavaScript文件中的Date.now().catch()错误..."

# 定义要修复的文件列表
files=(
    "assets/js/api-server.js"
    "assets/js/common-utils.js"
    "assets/js/unified-api-client-v3.js"
    "assets/js/security-module.js"
    "assets/js/theme-manager.js"
    "assets/js/error_handler.js"
    "assets/js/deepseek-monitor.js"
    "assets/js/captcha-service.js"
    "assets/js/deepseek-routes.js"
    "assets/js/login-api-client.js"
    "assets/js/anti_hotlink.js"
    "assets/js/tv_player.js"
    "assets/js/system_mechanisms.js"
    "assets/js/mtscos-utils.js"
    "assets/js/css-auto-loader.js"
    "assets/js/login-api-server.js"
    "assets/js/unified-auth-manager.js"
    "assets/js/unified_page_functions.js"
    "assets/js/unified-version-manager-v3.js"
    "assets/js/captcha_manager.js"
    "assets/js/login-script.js"
    "assets/js/utils/project-updater.js"
    "assets/js/smart_auto_trigger.js"
    "assets/js/intelligent-monitoring-system.js"
    "assets/js/unified-project-manager.js"
    "assets/js/api-client.js"
    "assets/js/data-transfer-monitor.js"
    "assets/js/session-manager.js"
    "assets/js/index-script.js"
    "assets/js/deepseek-ai.js"
)

# 计数器
total_fixes=0

# 遍历所有文件进行修复
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "正在修复文件: $file"
        
        # 创建备份
        cp "$file" "$file.backup.$(date +%s)"
        
        # 使用sed进行批量替换
        # 替换 Date.now().catch(error => console.error(...)) 为 Date.now()
        sed -i '' 's/Date\.now()\.catch(error => console\.error([^)]*))//g' "$file"
        
        # 清理可能的多余逗号和空格
        sed -i '' 's/, *)/, )/g' "$file"
        sed -i '' 's/, )/)/g' "$file"
        sed -i '' 's/,  *,/,/g' "$file"
        
        # 统计修复数量
        fixes_in_file=$(grep -c "Date.now()" "$file" 2>/dev/null || echo "0")
        total_fixes=$((total_fixes + fixes_in_file))
        
        echo "✓ 修复完成: $file (包含 $fixes_in_file 处Date.now调用)"
    else
        echo "⚠ 文件不存在: $file"
    fi
done

echo ""
echo "=========================================="
echo "修复完成!"
echo "总计修复文件数: ${#files[@]}"
echo "总计Date.now调用数: $total_fixes"
echo "=========================================="

# 验证修复结果
echo ""
echo "验证修复结果..."

# 检查是否还有未修复的.catch()错误
remaining_errors=$(find assets/js -name "*.js" -exec grep -l "Date\.now()\.catch" {} \; 2>/dev/null | wc -l)

if [ "$remaining_errors" -eq 0 ]; then
    echo "✓ 所有Date.now().catch()错误已修复完成!"
else
    echo "⚠ 仍有 $remaining_errors 个文件包含未修复的Date.now().catch()错误"
fi

echo ""
echo "修复后的文件已创建备份，如需回滚可使用.backup文件。"
echo "建议重启服务器以应用修复。"