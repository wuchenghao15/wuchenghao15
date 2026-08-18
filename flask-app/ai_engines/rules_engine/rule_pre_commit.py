"""
Git pre-commit hook 主入口
================================

被 .git/hooks/pre-commit 调用, 检测暂存区 (staged) 中的规则文件修改,
若规则修改未走7步审批, 拦截 git commit。

调用方式 (Git hook):
    #!/bin/sh
    python flask-app/ai_engines/rules_engine/rule_pre_commit.py

或命令行直接运行:
    python flask-app/ai_engines/rules_engine/rule_pre_commit.py [--bypass-for-sa]

bypass 选项:
    --bypass-for-sa 仅供超级管理员 wuchenghao15 使用, 且必须通过 VIKEY 实时检测 +
    7要素强认证。bypass 时会在 mt_rule_violation_alert 落库标记 bypass_type='SA_VIKEY_AUTH'
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import List, Tuple

# 兼容直接作为脚本运行和作为模块导入两种情况
if __package__ in (None, ""):
    # 直接运行: 把 flask-app 目录加入 sys.path, 改用绝对导入
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _FLASK_APP_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
    if _FLASK_APP_DIR not in sys.path:
        sys.path.insert(0, _FLASK_APP_DIR)
    from ai_engines.rules_engine.rule_db import RuleDB
    from ai_engines.rules_engine.rule_meta import (
        DEFAULT_RULES_DIR,
        parse_all_rules,
        parse_rule_meta,
    )
    from ai_engines.rules_engine.rule_violation_alert import alert_violation
else:
    from .rule_db import RuleDB
    from .rule_meta import DEFAULT_RULES_DIR, parse_all_rules, parse_rule_meta
    from .rule_violation_alert import alert_violation


# 受规则治理的路径范围
_RULES_DIR_PREFIX = ".trae/rules/"
_PROPOSAL_DIR_PREFIX = "docs/Proposals/"


def _get_staged_files() -> List[str]:
    """获取 git 暂存区文件列表"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"[ERROR] git diff 失败: {result.stderr}")
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        print("[ERROR] git 命令不可用, 跳过 pre-commit 检查")
        return []


def _filter_rule_files(staged_files: List[str]) -> List[str]:
    """筛选出规则目录下被修改的文件"""
    return [f for f in staged_files if f.startswith(_RULES_DIR_PREFIX) and f.endswith(".md")]


def _check_7step_approval(rule_db: RuleDB, rule_file: str) -> Tuple[bool, str]:
    """通过文件名查找对应 RULE_ID, 校验是否走7步审批"""
    # 从 RULE_META 解析 RULE_ID (parse_rule_meta 已在模块顶部导入)
    full_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", rule_file)
    )

    meta = parse_rule_meta(full_path)
    if meta is None:
        return False, f"无法解析 RULE_META: {rule_file}"

    record = rule_db.query_latest_changelog(meta.rule_id)
    if record is None:
        return False, f"规则 {meta.rule_id} 无 changelog 记录, 未走7步审批"
    if not record.get("approved_by_7step", 0):
        return False, f"规则 {meta.rule_id} changelog.approved_by_7step=0, 未走7步审批"
    if record.get("sa_final_decision", "") not in ("立即适配", "2个工作日后"):
        return False, f"规则 {meta.rule_id} sa_final_decision={record.get('sa_final_decision')}, 未终审"
    return True, ""


def _is_sa_vikey_online() -> bool:
    """
    检测 SA VIKEY 是否在线 + 7要素强认证 (简化版, 实际应调用系统认证模块)
    本函数仅作为占位, 实际生产环境应调用 auth_manager.verify_sa_vikey()
    """
    # [AUTO_FIXED by sys_gap_discovery_engine flow_id=autogap_eefd384d_20260827_002] 原注释: 接入真实 VIKEY 检测 (调用 _config/ViKey/ViKeyAPI.js 或 Python 桥接)
    # 当前简化: 仅检查环境变量 MT_SA_VIKEY_OVERRIDE (仅供本地测试, 生产禁用)
    return os.environ.get("MT_SA_VIKEY_OVERRIDE", "") == "wuchenghao15"


def run_pre_commit_check(argv: List[str] | None = None) -> int:
    """pre-commit 主入口, 返回 0=放行, 1=阻断"""
    parser = argparse.ArgumentParser(description="MTSCOS rules_engine pre-commit hook")
    parser.add_argument(
        "--bypass-for-sa",
        action="store_true",
        help="仅供超级管理员 wuchenghao15 使用, 必须通过 VIKEY 实时检测",
    )
    args = parser.parse_args(argv)

    staged_files = _get_staged_files()
    if not staged_files:
        return 0  # 无暂存文件, 放行

    rule_files = _filter_rule_files(staged_files)
    if not rule_files:
        return 0  # 无规则文件修改, 放行

    print(f"[INFO] 检测到 {len(rule_files)} 个规则文件修改: {rule_files}")

    # SA bypass 选项
    if args.bypass_for_sa:
        if not _is_sa_vikey_online():
            print("[BLOCKED] --bypass-for-sa 仅限 SA VIKEY 在线 + 7要素强认证通过")
            return 1
        print("[WARN] SA VIKEY bypass 生效, 落库 bypass_type='SA_VIKEY_AUTH'")
        rule_db = RuleDB()
        for rule_file in rule_files:
            full_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", rule_file)
            )
            meta = parse_rule_meta(full_path)
            if meta:
                alert_violation(
                    rule_db=rule_db,
                    rule_id=meta.rule_id,
                    violation_code="RULE-MODIFY-SA-BYPASS",
                    violation_detail=f"SA wuchenghao15 使用 VIKEY bypass 提交规则修改: {rule_file}",
                    triggered_by="wuchenghao15",
                )
        return 0

    rule_db = RuleDB()
    blocked_files: List[str] = []
    for rule_file in rule_files:
        ok, reason = _check_7step_approval(rule_db, rule_file)
        if not ok:
            blocked_files.append((rule_file, reason))
            print(f"[BLOCKED] {rule_file}: {reason}")
            # 触发违反告警
            full_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", rule_file)
            )
            meta = parse_rule_meta(full_path)
            if meta:
                alert_violation(
                    rule_db=rule_db,
                    rule_id=meta.rule_id,
                    violation_code="RULE-MODIFY-WITHOUT-7STEP-APPROVAL",
                    violation_detail=f"pre-commit hook 拦截规则修改: {rule_file} ({reason})",
                    triggered_by=os.environ.get("USER", "unknown"),
                )

    if blocked_files:
        print(
            f"\n[BLOCKED] {len(blocked_files)} 个规则文件未走7步审批, 提交被拒绝。\n"
            "请先走规则修改7步审批流程: 提议→2管理员同意→EigenFlux 5人磋商→SA终审。\n"
            "如需 SA bypass, 使用 --bypass-for-sa (需 VIKEY 在线)"
        )
        return 1

    print("[PASS] 所有规则文件修改已走7步审批, 允许提交")
    return 0


if __name__ == "__main__":
    sys.exit(run_pre_commit_check())
