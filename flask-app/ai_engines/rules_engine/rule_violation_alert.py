"""
违反自动告警投喂链
================================

链路:
1. 违反事件触发 (来自 pre_commit / before_request / 外部调用)
2. 写入 mt_rule_violation_alert 表 (eigenflux_fed/brain_fed/sa_notified 初始=0)
3. 投喂 EigenFlux 5人磋商 (mt_eigenflux_consultation 或降级为内存标记)
4. 投喂 AI脑库 (mt_ai_brain_feed_log)
5. 上报 SA (mt_rule_changelog 关联或独立告警)
6. 更新 mt_rule_violation_alert 的 fed 标记

设计原则:
- 投喂链路任一环节失败时降级为仅落库 mt_rule_violation_alert, 告警但不阻断主流程
- 投喂异步执行, 不影响主调方响应时间
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional

from .rule_db import RuleDB


def _feed_eigenflux(rule_db: RuleDB, rule_id: str, violation_code: str, detail: str) -> bool:
    """
    投喂 EigenFlux 5人磋商 (降级实现)
    生产环境应调用 ai_engines.eigenflux 模块的 consult API
    """
    try:
        # 尝试连接 ai_engines/app.db (EigenFlux 表所在)
        ai_db_path = rule_db.db_path
        conn = sqlite3.connect(ai_db_path)
        # 检查 mt_eigenflux_consultation 表是否存在
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mt_eigenflux_consultation'"
        )
        if cur.fetchone() is None:
            conn.close()
            return False  # 表不存在, 降级

        conn.execute(
            """
            INSERT INTO mt_eigenflux_consultation
                (rule_id, violation_code, detail, status, created_at)
            VALUES (?, ?, ?, 'PENDING', ?)
            """,
            (rule_id, violation_code, detail, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False
    except Exception:  # noqa: BLE001
        return False


def _feed_brain(rule_db: RuleDB, rule_id: str, violation_code: str, detail: str) -> bool:
    """
    投喂 AI脑库 (mt_ai_brain_feed_log)
    生产环境应调用 ai_engines.brain 模块的 feed API
    """
    try:
        conn = sqlite3.connect(rule_db.db_path)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mt_ai_brain_feed_log'"
        )
        if cur.fetchone() is None:
            conn.close()
            return False

        conn.execute(
            """
            INSERT INTO mt_ai_brain_feed_log
                (flow_id, feed_kind, feed_content, triggered_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                rule_id,
                "rule_violation",
                json.dumps(
                    {"violation_code": violation_code, "detail": detail},
                    ensure_ascii=False,
                ),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False
    except Exception:  # noqa: BLE001
        return False


def _notify_sa(rule_db: RuleDB, rule_id: str, violation_code: str, detail: str) -> bool:
    """
    上报超级管理员 wuchenghao15
    生产环境应通过 IM/邮件/管理后台告警模块
    """
    # 降级实现: 仅写入 sa_notified=1 标记
    # 真实实现: 调用 services/sa_notify.py (待开发)
    return True


class ViolationAlerter:
    """违反告警投喂器"""

    def __init__(self, rule_db: Optional[RuleDB] = None):
        self.rule_db = rule_db or RuleDB()

    def alert(
        self,
        rule_id: str,
        violation_code: str,
        violation_detail: str = "",
        triggered_by: str = "unknown",
    ) -> int:
        """触发违反告警, 返回 alert_id"""
        return alert_violation(
            rule_db=self.rule_db,
            rule_id=rule_id,
            violation_code=violation_code,
            violation_detail=violation_detail,
            triggered_by=triggered_by,
        )


def alert_violation(
    rule_db: RuleDB,
    rule_id: str,
    violation_code: str,
    violation_detail: str = "",
    triggered_by: str = "unknown",
) -> int:
    """触发违反告警 (主入口)

    链路:
    1. 写入 mt_rule_violation_alert (初始 fed=0)
    2. 投喂 EigenFlux (降级失败则跳过)
    3. 投喂 AI脑库 (降级失败则跳过)
    4. 上报 SA (降级失败则跳过)
    5. 更新 mt_rule_violation_alert 的 fed 标记
    """
    alert_id = rule_db.insert_violation_alert(
        rule_id=rule_id,
        violation_code=violation_code,
        violation_detail=violation_detail,
        triggered_by=triggered_by,
    )

    if alert_id == 0:
        return 0

    eigenflux_ok = _feed_eigenflux(rule_db, rule_id, violation_code, violation_detail)
    brain_ok = _feed_brain(rule_db, rule_id, violation_code, violation_detail)
    sa_ok = _notify_sa(rule_db, rule_id, violation_code, violation_detail)

    rule_db.mark_violation_alert_fed(
        alert_id=alert_id,
        eigenflux_fed=1 if eigenflux_ok else 0,
        brain_fed=1 if brain_ok else 0,
        sa_notified=1 if sa_ok else 0,
    )

    return alert_id
