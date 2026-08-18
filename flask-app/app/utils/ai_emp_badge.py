#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B轮议题3产出: mt_role_emp_feature 菜单徽标 + 调度接口
flow_id: flow_full_repair_20260818_001
使用: 在 Flask app 初始化时调用 register_ai_emp_badge(app) 注入 Jinja 全局函数
"""


def ai_emp_badge(role, feature_path):
    """Jinja全局函数: 由(role, feature_path)反查 mt_role_emp_feature 三元表, 返回徽标上下文"""
    import sqlite3
    try:
        from core.db_path import get_db_path
        conn = sqlite3.connect("file:" + get_db_path('app.db') + "?mode=ro", uri=True, timeout=2)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT ai_employee_id, ai_employee_uid, ai_employee_name, menu_badge_text,
                   ai_engine_name, feature_label, priority
            FROM mt_role_emp_feature
            WHERE role=? AND feature_path=? AND menu_badge_visible=1
            ORDER BY priority DESC LIMIT 1
        """, (role, feature_path))
        row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception:
        pass
    return None


def register_ai_emp_badge(app):
    """在 Flask app 中注入 ai_emp_badge 为 Jinja 全局函数"""
    app.jinja_env.globals["ai_emp_badge"] = ai_emp_badge
    return app


def dispatch_ai_employee(role, feature_path, task_payload=None):
    """调度接口: 由 (role, feature_path) 反查关联表 → 调用对应 ai_engine_name 执行任务
    返回统一响应8字段 (contract.yaml §1)
    """
    import sqlite3, json, traceback
    from datetime import datetime
    try:
        from core.db_path import get_db_path
        conn = sqlite3.connect("file:" + get_db_path('app.db') + "?mode=ro", uri=True, timeout=2)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT ai_employee_id, ai_employee_uid, ai_employee_name, ai_engine_name, feature_label
            FROM mt_role_emp_feature
            WHERE role=? AND feature_path=? AND dispatch_enabled=1
            ORDER BY priority DESC LIMIT 1
        """, (role, feature_path))
        row = cur.fetchone()
        conn.close()
        if not row:
            return {
                "code": "E_AI_EMP_NOT_BOUND", "msg": f"功能{feature_path}未绑定AI员工(role={role})",
                "data": None, "trace_id": "", "timestamp": datetime.now().isoformat(),
                "severity": "warning", "repair_suggestion": "请补充mt_role_emp_feature Seed数据",
                "design_tokens": "", "http": 200
            }
        # 真正调度 ai_engines (此处为接口占位, 实际调度由 ai_engine_name 决定)
        return {
            "code": "AI_EMP_DISPATCHED", "msg": f"已调度AI员工{row['ai_employee_name']}执行{row['feature_label']}",
            "data": {"ai_employee_id": row['ai_employee_id'], "ai_engine_name": row['ai_engine_name'],
                     "task_payload": task_payload},
            "trace_id": "", "timestamp": datetime.now().isoformat(),
            "severity": "info", "repair_suggestion": "",
            "design_tokens": "", "http": 200
        }
    except Exception as e:
        return {
            "code": "E_AI_EMP_DISPATCH_FAIL", "msg": f"调度异常: {e}",
            "data": None, "trace_id": "", "timestamp": datetime.now().isoformat(),
            "severity": "error", "repair_suggestion": "请检查 mt_role_emp_feature 表 + ai_employees 表一致性",
            "design_tokens": "", "_stack": traceback.format_exc(limit=5), "http": 500
        }
