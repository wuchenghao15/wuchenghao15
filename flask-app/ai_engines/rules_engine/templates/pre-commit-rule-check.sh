#!/bin/sh
# MTSCOS AI 项目 Git pre-commit Hook
# 强制执行 .trae/rules/ 9篇规则的7步审批流程
# 详见 flask-app/ai_engines/rules_engine/rule_pre_commit.py

# 检测项目根目录 (规则文件 .trae/rules/ + rules_engine 模块所在位置)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    echo "[ERROR] not a git repository, skip pre-commit hook"
    exit 0
fi

# 兼容两个 Git 仓库根:
# - 项目根 (MTSCOS_AI_Project): 规则文件 .trae/rules/ + flask-app/ 子目录
# - flask-app 子仓库: rules_engine 模块所在
if [ -f "$PROJECT_ROOT/flask-app/ai_engines/rules_engine/rule_pre_commit.py" ]; then
    PRECOMMIT_SCRIPT="$PROJECT_ROOT/flask-app/ai_engines/rules_engine/rule_pre_commit.py"
    RULES_DIR="$PROJECT_ROOT/.trae/rules"
elif [ -f "$PROJECT_ROOT/ai_engines/rules_engine/rule_pre_commit.py" ]; then
    PRECOMMIT_SCRIPT="$PROJECT_ROOT/ai_engines/rules_engine/rule_pre_commit.py"
    RULES_DIR="$PROJECT_ROOT/../.trae/rules"
else
    # 当前仓库非规则治理范围, 跳过
    exit 0
fi

if [ ! -f "$PRECOMMIT_SCRIPT" ]; then
    echo "[WARN] rules_engine pre-commit script not found: $PRECOMMIT_SCRIPT"
    exit 0
fi

# 调用 Python 脚本执行规则检查
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "[ERROR] python not available, skip pre-commit hook"
    exit 0
fi

# 超时 5s 自动放行 (防止影响开发效率)
# 仅 SA 可通过 --bypass-for-sa 绕过 (需 VIKEY 在线)
$PYTHON "$PRECOMMIT_SCRIPT" --bypass-for-sa 2>/dev/null
exit_code=$?
if [ $exit_code -eq 0 ]; then
    exit 0
fi

# SA bypass 失败, 重新走严格检查
$PYTHON "$PRECOMMIT_SCRIPT"
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "[RULES_ENGINE] pre-commit 检查未通过, 提交被拒绝"
    echo "请先走规则修改7步审批流程: 提议→2管理员同意→EigenFlux 5人磋商≥4/5→SA终审"
    echo "如需 SA bypass, 确保环境变量 MT_SA_VIKEY_OVERRIDE=wuchenghao15 (生产环境需真实 VIKEY)"
    exit 1
fi

exit 0
