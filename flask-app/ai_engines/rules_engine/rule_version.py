"""
规则版本化与变更日志
================================

提供规则版本号 bump 算法 + mt_rule_changelog 表写入逻辑。

版本号规则 (vMAJOR.MINOR.PATCH):
- MAJOR (vX.0.0): 新增/删除整章规则
- MINOR (v0.X.0): 新增条款或修改强制条款
- PATCH (v0.0.X): 文档表述优化/错别字
- META:         仅更新 RULE_META, 版本号不动
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

from .rule_db import RuleDB


CHANGE_TYPE_MAJOR = "MAJOR"
CHANGE_TYPE_MINOR = "MINOR"
CHANGE_TYPE_PATCH = "PATCH"
CHANGE_TYPE_META = "META"


@dataclass
class RuleVersion:
    """规则版本号对象"""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> "RuleVersion":
        """从字符串解析版本号 (兼容 v 前缀)"""
        cleaned = version_str.lstrip("v").strip()
        parts = cleaned.split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        return cls(major=major, minor=minor, patch=patch)

    def to_string(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def bump(self, change_type: str) -> "RuleVersion":
        """根据变更类型 bump 版本号"""
        if change_type == CHANGE_TYPE_MAJOR:
            return RuleVersion(major=self.major + 1, minor=0, patch=0)
        if change_type == CHANGE_TYPE_MINOR:
            return RuleVersion(
                major=self.major, minor=self.minor + 1, patch=0
            )
        if change_type == CHANGE_TYPE_PATCH:
            return RuleVersion(
                major=self.major, minor=self.minor, patch=self.patch + 1
            )
        if change_type == CHANGE_TYPE_META:
            return RuleVersion(major=self.major, minor=self.minor, patch=self.patch)
        raise ValueError(f"未知变更类型: {change_type}")


def bump_version(current_version: str, change_type: str) -> str:
    """便捷函数: 给定当前版本和变更类型, 返回新版本号字符串"""
    return RuleVersion.parse(current_version).bump(change_type).to_string()


def record_changelog(
    rule_db: RuleDB,
    rule_id: str,
    rule_file: str,
    from_version: str,
    to_version: str,
    change_type: str,
    change_summary: str,
    change_diff: Optional[str] = None,
    approved_by_7step: int = 0,
    sa_final_decision: Optional[str] = None,
    sa_vikey_verified: int = 0,
    proposer: str = "AI管理员",
    eigenflux_panel_json: Optional[str] = None,
    admin_approvers_json: Optional[str] = None,
    effective_at: Optional[str] = None,
    is_secret_withdrawn: int = 0,
) -> int:
    """写入 mt_rule_changelog 表, 返回 change_id

    若规则修改未走7步审批 (approved_by_7step=0), 强制告警 (但不阻断调用方)
    """
    if approved_by_7step == 0:
        # 触发告警: 规则修改未走7步审批
        try:
            from .rule_violation_alert import alert_violation

            alert_violation(
                rule_db=rule_db,
                rule_id=rule_id,
                violation_code="RULE-MODIFY-WITHOUT-7STEP-APPROVAL",
                violation_detail=f"规则 {rule_id} ({rule_file}) 修改未走7步审批流程",
                triggered_by=proposer,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] 触发规则修改告警失败: {exc}")

    return rule_db.insert_rule_changelog(
        rule_id=rule_id,
        rule_file=rule_file,
        from_version=from_version,
        to_version=to_version,
        change_type=change_type,
        change_summary=change_summary,
        change_diff=change_diff or "",
        approved_by_7step=approved_by_7step,
        sa_final_decision=sa_final_decision or "",
        sa_vikey_verified=sa_vikey_verified,
        proposer=proposer,
        eigenflux_panel_json=eigenflux_panel_json or "",
        admin_approvers_json=admin_approvers_json or "",
        effective_at=effective_at,
        is_secret_withdrawn=is_secret_withdrawn,
    )
