"""
MTSCOS AI 项目规则强制执行引擎 (rules_engine)
================================================

职责:
- 解析 .trae/rules/ 9篇规则的 RULE_META 元数据块
- 提供 Flask before_request 拦截器, 强制执行规则约束
- 提供 Git pre-commit hook, 拦截未走7步审批的规则修改
- 提供规则完整性自检 CLI, 输出9篇规则覆盖率报告
- 提供违反自动告警投喂链 (EigenFlux + AI脑库)
- 维护规则版本化与变更日志 (mt_rule_changelog)

强制约束 (用户权限.md §3.3 + §14 IRON_RULE):
- 任何规则修改必须走7步审批流程
- 任何代码变更必须有合法 flow_id (§14 MT_IR_D1)
- bypass_allowed = False, 禁止绕过 (含超级管理员)
- 违反记录自动落库 mt_iron_rule_violations + mt_rule_violation_alert
"""

from .rule_meta import RuleMeta, parse_all_rules, validate_rule_meta
from .rule_version import RuleVersion, bump_version, record_changelog
from .rule_db import RuleDB, init_tables
from .rule_interceptor import RuleInterceptor, register_interceptor
from .rule_pre_commit import run_pre_commit_check
from .rule_integrity_scanner import run_integrity_scan
from .rule_violation_alert import ViolationAlerter, alert_violation
from .dev_activity_preflight import (
    preflight_check,
    preflight_for_ai_chat,
    preflight_for_cli,
    preflight_for_api_route,
)

__version__ = "v1.3.0"
__all__ = [
    "RuleMeta",
    "parse_all_rules",
    "validate_rule_meta",
    "RuleVersion",
    "bump_version",
    "record_changelog",
    "RuleDB",
    "init_tables",
    "RuleInterceptor",
    "register_interceptor",
    "run_pre_commit_check",
    "run_integrity_scan",
    "ViolationAlerter",
    "alert_violation",
    "preflight_check",
    "preflight_for_ai_chat",
    "preflight_for_cli",
    "preflight_for_api_route",
]

# 9篇规则代码注册表 (RULE_ID → 文件名)
RULE_REGISTRY = {
    "MT_IRON_RULE_12STEPS": "§14强制开发12步骤独立约束规则.md",
    "MT_RULE_DEV": "开发规则.md",
    "MT_RULE_DESIGN": "设计规范.md",
    "MT_RULE_PERM": "用户权限.md",
    "MT_RULE_AI_OPS": "AI系统操作规范.md",
    "MT_RULE_SYS_OPS": "系统操作规范.md",
    "MT_RULE_PARAM": "系统参数数据规范与操作规范.md",
    "MT_RULE_SRC_MOD": "源码修改准则参考与思路方案.md",
    "MT_RULE_QBANK": "题库管理规范与准则.md",
}
