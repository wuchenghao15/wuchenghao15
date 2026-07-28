#!/bin/bash
# Git别名配置脚本
# 配置常用的Git别名

echo "配置Git别名..."

# 基本别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --oneline --graph --all --decorate'

# 状态别名
git config --global alias.ss 'status -s'
git config --global alias.sb 'branch -vv'

# 日志别名
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
git config --global alias.ll "log --pretty=format:'%C(yellow)%h%Creset %s %C(red)%ad%Creset %C(green)%an%Creset' --date=short"
git config --global alias.lc 'log --graph --all --decorate --oneline'

# 差异别名
git config --global alias.ds 'diff --staged'
git config --global alias.dc 'diff --cached'

# 提交别名
git config --global alias.cm 'commit -m'
git config --global alias.ca 'commit --amend'
git config --global alias.cam 'commit --amend -m'

# 分支别名
git config --global alias.bv 'branch -vv'
git config --global alias.bd 'branch -d'
git config --global alias.bD 'branch -D'
git config --global alias.bco 'checkout -b'

# 远程别名
git config --global alias.rv 'remote -v'
git config --global alias.ra 'remote add'
git config --global alias.rr 'remote remove'

# 暂存别名
git config --global alias.sa 'stash push'
git config --global alias.sp 'stash pop'
git config --global alias.sl 'stash list'
git config --global alias.sd 'stash drop'

# 清理别名
git config --global alias.cleanf 'clean -fd'
git config --global alias.cleand 'clean -fd -n'

# 其他别名
git config --global alias.undo 'reset --soft HEAD~1'
git config --global alias.redo 'reset HEAD@{1}'
git config --global alias.unstage 'reset HEAD --'
git config --global alias.current 'branch --show-current'
git config --global alias.contributors 'shortlog --summary --numbered'

echo "✅ Git别名配置完成"
echo ""
echo "常用别名:"
echo "  git st          - 查看状态"
echo "  git co          - 切换分支"
echo "  git br          - 查看分支"
echo "  git ci          - 提交"
echo "  git lg          - 美观的日志"
echo "  git ss          - 简短状态"
echo "  git ds          - 查看暂存的差异"
echo "  git cm          - 快速提交"
echo "  git bco         - 创建并切换分支"
echo "  git sa          - 暂存更改"
echo "  git sp          - 恢复暂存"
echo "  git undo        - 撤销上次提交"
echo "  git current     - 显示当前分支"
echo "  git contributors - 显示贡献者"
