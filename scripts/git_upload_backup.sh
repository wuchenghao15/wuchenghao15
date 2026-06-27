#!/bin/bash
# Git上传和备份脚本 - 使用Git管理AI员工

echo "🚀 MTSCOS AI Git上传和备份流程"
echo "================================"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 项目根目录
PROJECT_ROOT="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project"
cd "$PROJECT_ROOT"

# 1. 检查Git状态
echo "📡 1. 检查Git仓库状态..."
if [ -d ".git" ]; then
    echo "   ✅ Git仓库已初始化"
    
    # 检查远程仓库
    REMOTE_COUNT=$(git remote | wc -l | tr -d ' ')
    if [ "$REMOTE_COUNT" -eq 0 ]; then
        echo "   ⚠️ 未配置远程仓库"
        echo "   💡 建议: git remote add origin <your-github-repo-url>"
    else
        echo "   ✅ 远程仓库配置:"
        git remote -v
    fi
    
    # 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    echo "   📌 当前分支: $CURRENT_BRANCH"
    
    # 检查未提交的更改
    UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
    echo "   📝 待提交文件数: $UNCOMMITTED"
    
    if [ "$UNCOMMITTED" -gt 0 ]; then
        echo "   📋 未提交文件列表:"
        git status --short | head -20
    fi
else
    echo "   ❌ Git仓库未初始化"
    echo "   💡 正在初始化Git仓库..."
    git init
    echo "   ✅ Git仓库已创建"
fi

echo ""

# 2. 添加所有更改
echo "📦 2. 添加所有更改到Git..."
if [ "$UNCOMMITTED" -gt 0 ]; then
    git add -A
    echo "   ✅ 已添加 $UNCOMMITTED 个文件"
else
    echo "   ℹ️ 无待提交文件"
fi

echo ""

# 3. 自动提交
echo "💾 3. 自动提交更改..."
COMMIT_MESSAGE="自动提交 @ $(date '+%Y-%m-%d %H:%M:%S') | AI员工批量修复系统 + Git管理系统 + 中英双语README"
if [ "$UNCOMMITTED" -gt 0 ]; then
    git commit -m "$COMMIT_MESSAGE"
    echo "   ✅ 提交成功"
    echo "   提交信息: $COMMIT_MESSAGE"
else
    echo "   ℹ️ 无需提交"
fi

echo ""

# 4. 创建备份分支
echo "🎯 4. 创建备份分支..."
BACKUP_BRANCH="backup/$(date '+%Y%m%d_%H%M%S')"
git branch "$BACKUP_BRANCH"
echo "   ✅ 备份分支已创建: $BACKUP_BRANCH"

echo ""

# 5. 推送到远程仓库
echo "🚀 5. 推送到GitHub远程仓库..."
if [ "$REMOTE_COUNT" -gt 0 ]; then
    echo "   💡 推送命令:"
    echo "   git push -u origin $CURRENT_BRANCH"
    
    # 执行推送
    PUSH_RESULT=$(git push -u origin "$CURRENT_BRANCH" 2>&1)
    
    if echo "$PUSH_RESULT" | grep -q "error"; then
        echo "   ⚠️ 推送可能失败:"
        echo "$PUSH_RESULT"
        echo ""
        echo "   💡 可能的解决方案:"
        echo "   1. 检查远程仓库URL是否正确"
        echo "   2. 检查是否有权限推送"
        echo "   3. 手动推送: git push origin $CURRENT_BRANCH"
    else
        echo "   ✅ 推送成功"
        echo "$PUSH_RESULT"
    fi
else
    echo "   ⚠️ 未配置远程仓库，跳过推送"
    echo ""
    echo "   💡 配置远程仓库步骤:"
    echo "   1. 在GitHub创建仓库: https://github.com/new"
    echo "   2. 添加远程仓库: git remote add origin <your-repo-url>"
    echo "   3. 推送代码: git push -u origin $CURRENT_BRANCH"
fi

echo ""

# 6. 显示最近的提交
echo "📊 6. 显示最近的提交..."
git log --oneline -5

echo ""

# 7. 生成Git操作日志
echo "📝 7. 生成Git操作日志..."
LOG_FILE="$PROJECT_ROOT/git_operations.log"
{
    echo "=== Git操作日志 ==="
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "操作: 自动提交 + 推送 + 备份"
    echo "提交信息: $COMMIT_MESSAGE"
    echo "备份分支: $BACKUP_BRANCH"
    echo "当前分支: $CURRENT_BRANCH"
    echo "提交文件数: $UNCOMMITTED"
    echo ""
    echo "=== 提交历史 ==="
    git log --oneline -10
} >> "$LOG_FILE"
echo "   ✅ 操作日志已保存到: git_operations.log"

echo ""
echo "================================"
echo "✅ Git上传和备份流程完成！"
echo "================================"
echo ""
echo "📌 重要提醒:"
echo "   • 代码已备份到本地分支: $BACKUP_BRANCH"
echo "   • 如需推送到GitHub，请先配置远程仓库"
echo "   • 操作日志保存在: git_operations.log"
echo ""
echo "🌐 GitHub仓库创建指南:"
echo "   1. 访问 https://github.com/new"
echo "   2. 创建仓库 MTSCOS_AI_Project"
echo "   3. 运行: git remote add origin https://github.com/YOUR_USERNAME/MTSCOS_AI_Project.git"
echo "   4. 推送: git push -u origin $CURRENT_BRANCH"
echo ""