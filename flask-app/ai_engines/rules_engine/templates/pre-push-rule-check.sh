#!/bin/sh
# MTSCOS AI 项目 Git pre-push Hook (Layer-4)
# 强制执行 §14 IRON_RULE 12步骤开发流程
# 未完成12步骤的开发活动禁止推送 (mt_dev_flow_session.final_status='DONE')
#
# 详见 .trae/rules/§14强制开发12步骤独立约束规则.md
#
# 接收 stdin: <local ref> <local sha> <remote ref> <remote sha> 每行一组

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$PROJECT_ROOT" ]; then
    exit 0
fi

# 定位 Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    exit 0
fi

# 读取推送的 ref 信息
while read -r local_ref local_sha remote_ref remote_sha; do
    # 只检查 branch 推送
    case "$remote_ref" in
        refs/heads/*) ;;
        *) continue ;;
    esac

    # 获取本次推送的 commit 列表
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # 新分支: 检查所有 commits
        range="$local_sha"
    else
        range="${remote_sha}..${local_sha}"
    fi

    # 检查每个 commit 的 message 是否含 flow_id
    commits=$(git rev-list "$range" 2>/dev/null)
    for commit in $commits; do
        msg=$(git log -1 --format='%B' "$commit" 2>/dev/null)
        # 提取 flow_id (格式: flow_id=xxx 或 [flow:xxx])
        flow_id=$(echo "$msg" | grep -oE 'flow_id=[a-zA-Z0-9_]+' | head -1 | cut -d= -f2)
        if [ -z "$flow_id" ]; then
            flow_id=$(echo "$msg" | grep -oE '\[flow:[a-zA-Z0-9_]+\]' | head -1 | sed 's/\[flow://;s/\]//')
        fi

        if [ -n "$flow_id" ]; then
            # 检查 mt_dev_flow_session.final_status
            result=$($PYTHON -c "
import sqlite3, os, sys
db = os.path.join('$PROJECT_ROOT', '_runtime', 'databases', 'Database', 'app.db')
if not os.path.exists(db):
    sys.exit(0)
try:
    conn = sqlite3.connect(db, timeout=3)
    row = conn.execute(
        'SELECT final_status FROM mt_dev_flow_session WHERE flow_id=?',
        ('$flow_id',)
    ).fetchone()
    conn.close()
    if row and row[0] == 'DONE':
        sys.exit(0)
    else:
        print('NOT_DONE')
        sys.exit(1)
except Exception:
    sys.exit(0)
" 2>/dev/null)
            rc=$?
            if [ $rc -ne 0 ]; then
                echo ""
                echo "[RULES_ENGINE] pre-push 拦截: §14 IRON_RULE 违反"
                echo "  commit: ${commit:0:12}"
                echo "  flow_id: $flow_id"
                echo "  原因: 12步骤开发流程未完成 (final_status != DONE)"
                echo "  解决: 完成12步骤后再推送, 或通过7步审批获取 bypass"
                echo ""
                exit 1
            fi
        fi
    done
done

exit 0
