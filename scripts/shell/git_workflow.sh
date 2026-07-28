#!/bin/bash
# Git工作流脚本
# 提供常用的Git工作流操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印帮助信息
print_help() {
    echo "Git工作流脚本"
    echo ""
    echo "用法: ./git_workflow.sh <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  feature <name>     - 创建功能分支"
    echo "  bugfix <name>      - 创建修复分支"
    echo "  release <version>  - 创建发布分支"
    echo "  finish             - 完成当前分支（合并到main）"
    echo "  sync               - 同步远程仓库"
    echo "  save <message>     - 保存当前工作（stash）"
    echo "  restore            - 恢复保存的工作"
    echo "  cleanup            - 清理已合并的分支"
    echo "  status             - 查看状态"
    echo "  log                - 查看日志"
    echo "  undo               - 撤销上次提交"
    echo "  amend <message>    - 修改上次提交"
}

# 创建功能分支
create_feature() {
    local name=$1
    if [ -z "$name" ]; then
        echo -e "${RED}错误: 请提供分支名称${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}创建功能分支: feature/$name${NC}"
    git checkout main
    git pull origin main
    git checkout -b "feature/$name"
    echo -e "${GREEN}✅ 功能分支已创建: feature/$name${NC}"
}

# 创建修复分支
create_bugfix() {
    local name=$1
    if [ -z "$name" ]; then
        echo -e "${RED}错误: 请提供分支名称${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}创建修复分支: bugfix/$name${NC}"
    git checkout main
    git pull origin main
    git checkout -b "bugfix/$name"
    echo -e "${GREEN}✅ 修复分支已创建: bugfix/$name${NC}"
}

# 创建发布分支
create_release() {
    local version=$1
    if [ -z "$version" ]; then
        echo -e "${RED}错误: 请提供版本号${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}创建发布分支: release/$version${NC}"
    git checkout main
    git pull origin main
    git checkout -b "release/$version"
    echo -e "${GREEN}✅ 发布分支已创建: release/$version${NC}"
}

# 完成当前分支
finish_branch() {
    local current_branch=$(git branch --show-current)
    
    if [ "$current_branch" = "main" ]; then
        echo -e "${RED}错误: 不能在main分支上执行此操作${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}完成分支: $current_branch${NC}"
    
    # 提交所有更改
    git add -A
    if ! git diff --cached --quiet; then
        echo -e "${YELLOW}请输入提交信息:${NC}"
        read -r message
        git commit -m "$message"
    fi
    
    # 切换到main并合并
    git checkout main
    git pull origin main
    git merge "$current_branch"
    
    # 推送到远程
    git push origin main
    
    # 删除本地分支
    git branch -d "$current_branch"
    
    echo -e "${GREEN}✅ 分支已完成并合并到main${NC}"
}

# 同步远程仓库
sync_repo() {
    echo -e "${BLUE}同步远程仓库...${NC}"
    git fetch --all
    git pull --all
    echo -e "${GREEN}✅ 同步完成${NC}"
}

# 保存当前工作
save_work() {
    local message=$1
    if [ -z "$message" ]; then
        message="WIP: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    echo -e "${BLUE}保存当前工作...${NC}"
    git stash push -m "$message"
    echo -e "${GREEN}✅ 工作已保存: $message${NC}"
}

# 恢复保存的工作
restore_work() {
    echo -e "${BLUE}恢复保存的工作...${NC}"
    git stash pop
    echo -e "${GREEN}✅ 工作已恢复${NC}"
}

# 清理已合并的分支
cleanup_branches() {
    echo -e "${BLUE}清理已合并的分支...${NC}"
    git branch --merged main | grep -v "^\*\|main" | xargs -n 1 git branch -d
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 查看状态
show_status() {
    echo -e "${BLUE}Git状态:${NC}"
    echo ""
    echo -e "${YELLOW}分支:${NC}"
    git branch -vv
    echo ""
    echo -e "${YELLOW}状态:${NC}"
    git status -s
    echo ""
    echo -e "${YELLOW}远程:${NC}"
    git remote -v
}

# 查看日志
show_log() {
    echo -e "${BLUE}提交日志:${NC}"
    git log --oneline --graph --all --decorate -20
}

# 撤销上次提交
undo_commit() {
    echo -e "${YELLOW}撤销上次提交...${NC}"
    git reset --soft HEAD~1
    echo -e "${GREEN}✅ 上次提交已撤销（更改保留在暂存区）${NC}"
}

# 修改上次提交
amend_commit() {
    local message=$1
    if [ -z "$message" ]; then
        echo -e "${RED}错误: 请提供提交信息${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}修改上次提交...${NC}"
    git add -A
    git commit --amend -m "$message"
    echo -e "${GREEN}✅ 提交已修改${NC}"
}

# 主函数
main() {
    if [ $# -lt 1 ]; then
        print_help
        exit 0
    fi
    
    local command=$1
    shift
    
    case $command in
        feature)
            create_feature "$@"
            ;;
        bugfix)
            create_bugfix "$@"
            ;;
        release)
            create_release "$@"
            ;;
        finish)
            finish_branch
            ;;
        sync)
            sync_repo
            ;;
        save)
            save_work "$@"
            ;;
        restore)
            restore_work
            ;;
        cleanup)
            cleanup_branches
            ;;
        status)
            show_status
            ;;
        log)
            show_log
            ;;
        undo)
            undo_commit
            ;;
        amend)
            amend_commit "$@"
            ;;
        help|--help|-h)
            print_help
            ;;
        *)
            echo -e "${RED}未知命令: $command${NC}"
            print_help
            exit 1
            ;;
    esac
}

main "$@"
