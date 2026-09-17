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


# ═══════════════════════════════════════════════════════════════════
# 仙女座 ↔ 规则引擎 自动版本 bump 桥接 (v1.1.0 新增, MT_RULE_VERSION §3.2)
# ═══════════════════════════════════════════════════════════════════

def _auto_bump_from_events(db_path: Optional[str] = None) -> list[dict]:
    """扫描仙女座/规则引擎事件表, 判定是否触发自动版本 bump.

    读取:
      - mt_ai_self_evolution_log        自演化错误 spike
      - mt_andromeda_rule_knowledge      规则分块增量
      - mt_eigenflux_comm_messages      安全告警消息
      - mt_permission_audit_detail      越权案例
      - mt_andromeda_employee_registry  AI 员工健康度

    每 300s 由 sys_rule_enforcer daemon 调用一次.
    触发阈值按 MT_RULE_VERSION §3.2 事件清单定义.

    Returns:
      [{'bump': 'patch'|'minor'|'major', 'label': str, 'reason': str, 'data': dict}, ...]
      调用方负责实际写 mt_rule_changelog + bump VERSION 文件.
    """
    import os
    results: list[dict] = []

    if db_path is None:
        db_path = os.environ.get(
            "MTSCOS_DB_PATH",
            os.path.join(os.path.dirname(__file__), "..", "..", "database", "app.db"),
        )
    try:
        c = sqlite3.connect(str(db_path), timeout=10)
    except Exception as exc:  # noqa: BLE001
        print(f"[rule_version] _auto_bump_from_events: DB 连接失败 {exc}")
        return results

    def _safe_exec(sql: str) -> int:
        try:
            row = c.execute(sql).fetchone()
            return int(row[0]) if row else 0
        except Exception:  # noqa: BLE001
            return 0

    # ── 触发源 1: 自演化错误 spike ──
    evo_err = _safe_exec(
        "SELECT COUNT(*) FROM mt_ai_self_evolution_log "
        "WHERE created_at > datetime('now', '-24 hours') "
        "AND (lower(result_summary) LIKE '%error%' "
        "OR lower(stage_name) LIKE '%fail%' "
        "OR trigger_type IN ('error_spike', 'manual_force_fix'))"
    )
    if evo_err >= 3:
        results.append({
            "bump": "patch", "label": "[EVOLUTION-FIX]",
            "reason": f"仙女座自演化 24h 内 {evo_err} 次错误 spike (阈值 3)",
            "data": {"source": "mt_ai_self_evolution_log", "count_24h": evo_err, "threshold": 3},
        })

    # ── 触发源 2: rule_knowledge 分块增量 ──
    rk_new = _safe_exec(
        "SELECT COUNT(*) FROM mt_andromeda_rule_knowledge "
        "WHERE last_ingested > datetime('now', '-7 days')"
    )
    if rk_new >= 50:
        results.append({
            "bump": "minor", "label": "[RULE-REFRESH]",
            "reason": f"mt_andromeda_rule_knowledge 7 天内新增 {rk_new} 条分块 (阈值 50)",
            "data": {"source": "mt_andromeda_rule_knowledge", "count_7d": rk_new, "threshold": 50},
        })

    # ── 触发源 3: EigenFlux 安全告警 ──
    sf_alert = _safe_exec(
        "SELECT COUNT(*) FROM mt_eigenflux_comm_messages "
        "WHERE created_at > datetime('now', '-24 hours') "
        "AND (lower(message) LIKE '%security%' OR lower(message) LIKE '%vikey%' "
        "OR lower(message) LIKE '%breach%' OR lower(message) LIKE '%fail-closed%')"
    )
    if sf_alert >= 10:
        results.append({
            "bump": "patch", "label": "[SECURITY]",
            "reason": f"EigenFlux 24h 内 {sf_alert} 条安全告警 (阈值 10)",
            "data": {"source": "mt_eigenflux_comm_messages", "count_24h": sf_alert, "threshold": 10},
        })

    # ── 触发源 4: 越权案例 ──
    perm_breach = _safe_exec(
        "SELECT COUNT(*) FROM mt_permission_audit_detail "
        "WHERE created_at > datetime('now', '-7 days') AND "
        "(action_result='denied' OR result IN ('breach','suspicious'))"
    )
    if perm_breach >= 5:
        results.append({
            "bump": "patch", "label": "[PERM-FIX]",
            "reason": f"mt_permission_audit_detail 7d 内 {perm_breach} 条越权/拒绝案例 (阈值 5)",
            "data": {"source": "mt_permission_audit_detail", "count_7d": perm_breach, "threshold": 5},
        })

    # ── 触发源 5: AI 员工健康度 ──
    emp_abnormal = _safe_exec(
        "SELECT COUNT(*) FROM mt_andromeda_employee_registry "
        "WHERE status NOT IN ('active','standby','healthy') AND status IS NOT NULL"
    )
    if emp_abnormal >= 20:
        results.append({
            "bump": "patch", "label": "[EMPLOYEE-HEAL]",
            "reason": f"mt_andromeda_employee_registry {emp_abnormal} 名 AI 员工状态异常 (阈值 20)",
            "data": {"source": "mt_andromeda_employee_registry", "count": emp_abnormal, "threshold": 20},
        })

    # ── 触发源 6: mt_rule_violation_alert 告警风暴 ──
    rule_alert = _safe_exec(
        "SELECT COUNT(*) FROM mt_rule_violation_alert "
        "WHERE created_at > datetime('now', '-24 hours')"
    )
    if rule_alert >= 20:
        results.append({
            "bump": "patch", "label": "[RULE-FIX]",
            "reason": f"mt_rule_violation_alert 24h 内 {rule_alert} 条告警 (阈值 20)",
            "data": {"source": "mt_rule_violation_alert", "count_24h": rule_alert, "threshold": 20},
        })

    c.close()
    return results


def apply_auto_bumps(db_path: Optional[str] = None) -> list[str]:
    """扫描事件表 + 自动 bump + 写 mt_rule_changelog.

    Returns: 本次实际执行的 bump 描述列表 (如 ['patch [EVOLUTION-FIX]'])
    """
    events = _auto_bump_from_events(db_path)
    applied: list[str] = []
    if not events:
        return applied

    # 取最高优先级 bump (major > minor > patch)
    priority = {"major": 3, "minor": 2, "patch": 1}
    highest = sorted(events, key=lambda e: priority.get(e["bump"], 0), reverse=True)[0]
    change_type = highest["bump"].upper()  # PATCH / MINOR / MAJOR
    label = highest["label"]
    reason = highest["reason"]

    try:
        # 读当前 VERSION
        import os as _os
        ver_path = _os.path.join(
            _os.path.dirname(__file__), "..", "..", "VERSION"
        )
        if not _os.path.exists(ver_path):
            return applied
        with open(ver_path) as f:
            cur_ver = f.read().strip()
        new_ver = bump_version(cur_ver, change_type)

        # 写 VERSION + 自动 changelog
        with open(ver_path, "w") as f:
            f.write(new_ver + "\n")

        # 自动写一条 mt_rule_changelog (proposer=仙女座引擎)
        try:
            from .rule_db import RuleDB
            db = RuleDB()
            record_changelog(
                rule_db=db,
                rule_id="MT_RULE_VERSION",
                rule_file="版本升级规则.md",
                from_version=cur_ver,
                to_version=new_ver,
                change_type=change_type,
                change_summary=f"{label} {reason}",
                approved_by_7step=0,  # 自动 bump 不需要人工 7 步, 但会触发告警
                proposer=f"Andromeda 自演化 (auto_bump_{change_type.lower()})",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[rule_version] apply_auto_bumps: changelog 写入失败 {exc}")

        # 追加触发事件摘要到 VERSION 文件 (方便审计)
        applied.append(f"{change_type.lower()} {label}: {reason[:80]}")
        print(f"[rule_version] ✅ 自动 bump {cur_ver} → {new_ver} {label}: {reason[:60]}")

    except Exception as exc:  # noqa: BLE001
        print(f"[rule_version] apply_auto_bumps 失败: {exc}")

    return applied
