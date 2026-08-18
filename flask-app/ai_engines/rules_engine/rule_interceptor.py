"""
Flask before_request 规则拦截器
================================

强制执行规则约束, 拦截:
1. 未走7步审批的规则文件修改 (POST /api/rules/*)
2. 规则违反事件 (基于 mt_iron_rule_violations 触发)
3. §14 MT_IR_D1~D8 铁律违反 (含 flow_id 校验, 状态转移校验)

拦截原则:
- bypass_allowed=False, 禁止任何人绕过 (含超级管理员 wuchenghao15)
- 拦截仅作用于规则修改相关路由, 非规则路由 0 开销
- 违反触发后自动投喂 EigenFlux + AI脑库
"""

from __future__ import annotations

import json
from typing import Callable, Optional

from .rule_db import RuleDB
from .rule_violation_alert import alert_violation


# 需要拦截的规则修改路由前缀
_RULE_MODIFY_PREFIXES = (
    "/api/rules/",
    "/api/rule/",
    "/api/admin/rule",
    "/api/dev_flow/rule",
    "/admin/rule",
)

# 公开 API 白名单 (不拦截)
_PUBLIC_PATHS = {
    "/",
    "/login",
    "/auth/login",
    "/static/",
    "/api/homepage/stats",
    "/api/health",
}


class RuleInterceptor:
    """Flask before_request 规则拦截器"""

    def __init__(self, rule_db: Optional[RuleDB] = None):
        self.rule_db = rule_db or RuleDB()

    def _is_rule_modify_request(self, path: str, method: str) -> bool:
        """判断是否为规则修改请求"""
        if method not in ("POST", "PUT", "PATCH", "DELETE"):
            return False
        return any(path.startswith(prefix) for prefix in _RULE_MODIFY_PREFIXES)

    def _is_public_path(self, path: str) -> bool:
        """判断是否为公开路径"""
        if path in _PUBLIC_PATHS:
            return True
        return path.startswith("/static/") or path.startswith("/api/homepage/")

    def _check_7step_approval(self, rule_id: str) -> bool:
        """检查规则修改是否已走7步审批 (mt_rule_changelog.approved_by_7step=1)"""
        record = self.rule_db.query_latest_changelog(rule_id)
        if record is None:
            # 无 changelog 记录, 视为未走审批
            return False
        return bool(record.get("approved_by_7step", 0))

    def intercept(self, path: str, method: str, body: Optional[dict] = None) -> Optional[dict]:
        """
        拦截入口 (供 Flask before_request 调用)
        返回 None 表示放行, 返回 dict 表示拦截响应
        """
        if self._is_public_path(path):
            return None

        if not self._is_rule_modify_request(path, method):
            return None

        # 规则修改请求: 必须提供 rule_id + approved_by_7step=1
        body = body or {}
        rule_id = body.get("rule_id") or body.get("ruleId") or ""
        if not rule_id:
            return {
                "status": "BLOCKED",
                "code": "RULE-MODIFY-WITHOUT-RULE-ID",
                "message": "规则修改请求必须携带 rule_id",
                "http_status": 400,
            }

        if not self._check_7step_approval(rule_id):
            # 触发违反告警
            alert_violation(
                rule_db=self.rule_db,
                rule_id=rule_id,
                violation_code="RULE-MODIFY-WITHOUT-7STEP-APPROVAL",
                violation_detail=f"规则 {rule_id} 修改未走7步审批流程 (path={path}, method={method})",
                triggered_by=body.get("operator", "unknown"),
            )
            return {
                "status": "BLOCKED",
                "code": "RULE-MODIFY-WITHOUT-7STEP-APPROVAL",
                "message": f"规则 {rule_id} 修改未走7步审批流程, 禁止操作",
                "http_status": 403,
            }

        return None

    def check_iron_rule_violation(self, violation_code: str, rule_id: str, detail: str, operator: str = "unknown") -> None:
        """§14 铁律违反检测 (供外部调用)"""
        alert_violation(
            rule_db=self.rule_db,
            rule_id=rule_id,
            violation_code=violation_code,
            violation_detail=detail,
            triggered_by=operator,
        )


def register_interceptor(app, rule_db: Optional[RuleDB] = None) -> RuleInterceptor:
    """注册 Flask before_request 拦截器"""
    interceptor = RuleInterceptor(rule_db=rule_db)

    try:
        from flask import request, jsonify
    except ImportError:
        print("[WARN] Flask 未安装, 拦截器无法注册")
        return interceptor

    @app.before_request
    def _rules_engine_before_request():
        path = request.path
        method = request.method
        if method not in ("POST", "PUT", "PATCH", "DELETE"):
            return None

        try:
            body = request.get_json(silent=True) or {}
        except Exception:  # noqa: BLE001
            body = {}

        result = interceptor.intercept(path, method, body)
        if result is not None:
            http_status = result.pop("http_status", 403)
            return jsonify(result), http_status
        return None

    return interceptor
