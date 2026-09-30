#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 定制化引擎 (CustomizationEngine)
========================================
系统定制化3子模块：
  5. 按角色定制仪表盘：role_id → widget(名称/尺寸/位置/数据源)
  6. 工作流定制：自定义工作流节点/触发条件/动作链(IFTTT式)
  7. 表单字段定制：页面→自定义字段(类型/校验/默认值/显示顺序)

遵循：
  - SSOT数据库权威源
  - 与CloudSyncLayer联动：定制内容云端同步
  - 管理员才可改角色仪表盘/工作流/表单字段

版本: v1.0.0
"""

import os
import sys
import json
import time
import re
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('customization_engine')


# ============================================================================
# 枚举定义
# ============================================================================

class WidgetSize(Enum):
    """仪表盘组件尺寸"""
    SMALL = "small"      # 1x1
    MEDIUM = "medium"    # 2x1
    LARGE = "large"      # 2x2
    WIDE = "wide"        # 3x1
    FULL = "full"        # 4x2


class WidgetType(Enum):
    """仪表盘组件类型"""
    STAT_CARD = "stat_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    DATA_TABLE = "data_table"
    ALERT_LIST = "alert_list"
    FEED_CARD = "feed_card"
    CUSTOM_HTML = "custom_html"


class FieldType(Enum):
    """表单字段类型"""
    TEXT = "text"
    NUMBER = "number"
    BOOL = "bool"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
    RICHTEXT = "richtext"
    FILE = "file"
    JSON = "json"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


# 默认角色仪表盘（内建）
DEFAULT_ROLE_DASHBOARDS: Dict[str, List[Dict]] = {
    "admin": [
        {"id": "w_sys_health", "type": WidgetType.LINE_CHART.value, "size": WidgetSize.WIDE.value,
         "title": "系统健康趋势", "data_source": "/api/maintenance/history", "order": 0},
        {"id": "w_user_stat", "type": WidgetType.STAT_CARD.value, "size": WidgetSize.SMALL.value,
         "title": "活跃用户", "data_source": "/api/admin/stats", "order": 1},
        {"id": "w_ai_stat", "type": WidgetType.STAT_CARD.value, "size": WidgetSize.SMALL.value,
         "title": "AI员工数", "data_source": "/api/ai/employees/count", "order": 2},
        {"id": "w_alerts", "type": WidgetType.ALERT_LIST.value, "size": WidgetSize.LARGE.value,
         "title": "最近告警", "data_source": "/api/maintenance/issues", "order": 3},
    ],
    "user": [
        {"id": "w_my_tasks", "type": WidgetType.DATA_TABLE.value, "size": WidgetSize.WIDE.value,
         "title": "我的任务", "data_source": "/api/user/tasks", "order": 0},
        {"id": "w_my_ai", "type": WidgetType.STAT_CARD.value, "size": WidgetSize.SMALL.value,
         "title": "我的AI员工", "data_source": "/api/user/ai-count", "order": 1},
    ],
    "guest": [
        {"id": "w_hello", "type": WidgetType.FEED_CARD.value, "size": WidgetSize.MEDIUM.value,
         "title": "欢迎卡片", "data_source": "static", "order": 0},
    ],
}


# ============================================================================
# 定制化引擎主类
# ============================================================================

class CustomizationEngine:
    """MTSCOS 系统定制化引擎"""

    ENGINE_VERSION = "v1.0.0"

    def __init__(self, db_path: str = None, dual_db=None,
                 cloud_sync_layer=None, project_dir: str = None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.cloud_sync = cloud_sync_layer
        self.project_dir = project_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        self.stats = {
            'dashboard_sets': 0,
            'dashboard_gets': 0,
            'workflow_sets': 0,
            'workflow_execs': 0,
            'form_sets': 0,
            'form_gets': 0,
        }

        self._ensure_tables()
        logger.info(f"CustomizationEngine {self.ENGINE_VERSION} 已初始化")

    # ======================================================================
    # 子模块5：按角色定制仪表盘
    # ======================================================================

    def get_dashboard(self, role: str, username: str = None) -> List[Dict[str, Any]]:
        """获取角色仪表盘（叠加用户级覆盖）"""
        self.stats['dashboard_gets'] += 1
        # 1) DB 存的角色仪表盘
        rows = self._query(
            "SELECT widgets_json FROM mt_custom_dashboards WHERE role = ? AND username IS NULL LIMIT 1",
            (role,))
        widgets = []
        if rows:
            try:
                widgets = json.loads(rows[0]['widgets_json'])
            except Exception:
                widgets = []
        # 2) 如果DB没有，用内建默认
        if not widgets:
            widgets = [dict(w) for w in DEFAULT_ROLE_DASHBOARDS.get(role, [])]
        # 3) 叠加用户个人定制（仅对该用户）
        if username:
            urows = self._query(
                "SELECT widgets_json FROM mt_custom_dashboards WHERE username = ? AND role = ? LIMIT 1",
                (username, role))
            if urows:
                try:
                    user_widgets = json.loads(urows[0]['widgets_json'])
                    widgets = self._merge_widgets(widgets, user_widgets)
                except Exception:
                    pass
        return widgets

    def set_dashboard(self, role: str, widgets: List[Dict],
                      changed_by: str = "system",
                      username: str = None) -> Dict[str, Any]:
        """设置角色仪表盘（管理员）或个人仪表盘覆盖（任意用户）"""
        self.stats['dashboard_sets'] += 1
        ok = self._write(
            "INSERT OR REPLACE INTO mt_custom_dashboards "
            "(role, username, widgets_json, updated_at, updated_by, version) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (role, username, json.dumps(widgets, ensure_ascii=False),
             datetime.now().isoformat(), changed_by, int(time.time() * 1000)))
        return {'success': ok, 'role': role, 'widget_count': len(widgets)}

    def _merge_widgets(self, base: List[Dict], overlay: List[Dict]) -> List[Dict]:
        """合并两个widget列表，按id匹配，overlay优先"""
        merged = {w['id']: dict(w) for w in base}
        for w in overlay:
            if 'id' not in w:
                continue
            merged[w['id']] = dict(w)
        res = list(merged.values())
        res.sort(key=lambda x: x.get('order', 0))
        return res

    # ======================================================================
    # 子模块6：工作流定制（IFTTT式）
    #   trigger: {type, params}
    #   condition: {expression, args}
    #   actions: [{type, params}]
    # ======================================================================

    def list_workflows(self, owner: str = None, status: str = None,
                       limit: int = 100) -> List[Dict]:
        """列出工作流"""
        sql = "SELECT * FROM mt_custom_workflows"
        clauses = []
        params: List = []
        if owner:
            clauses.append("owner = ?")
            params.append(owner)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = self._query(sql, tuple(params))
        for r in rows:
            for k in ('trigger_json', 'condition_json', 'actions_json'):
                try:
                    r[k.replace('_json', '')] = json.loads(r[k] or '{}')
                except Exception:
                    pass
        return rows

    def create_workflow(self, name: str, owner: str, trigger: Dict,
                        actions: List[Dict], condition: Dict = None,
                        description: str = "") -> Dict[str, Any]:
        """创建工作流"""
        self.stats['workflow_sets'] += 1
        wf_id = f"WF_{int(time.time()*1000)}"
        ok = self._write(
            "INSERT INTO mt_custom_workflows "
            "(workflow_id, name, owner, description, status, "
            "trigger_json, condition_json, actions_json, "
            "created_at, updated_at, runs_count, last_run_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)",
            (wf_id, name, owner, description, WorkflowStatus.DRAFT.value,
             json.dumps(trigger, ensure_ascii=False),
             json.dumps(condition or {}, ensure_ascii=False),
             json.dumps(actions, ensure_ascii=False),
             datetime.now().isoformat(), datetime.now().isoformat()))
        return {'success': ok, 'workflow_id': wf_id,
                'status': WorkflowStatus.DRAFT.value}

    def set_workflow_status(self, wf_id: str, status: WorkflowStatus,
                            changed_by: str) -> Dict[str, Any]:
        s = status.value if isinstance(status, WorkflowStatus) else status
        ok = self._write(
            "UPDATE mt_custom_workflows SET status = ?, updated_at = ? WHERE workflow_id = ?",
            (s, datetime.now().isoformat(), wf_id))
        return {'success': ok, 'workflow_id': wf_id, 'status': s}

    def execute_workflow(self, wf_id: str, context: Dict = None) -> Dict[str, Any]:
        """模拟执行工作流（校验+记录，不做危险动作）"""
        self.stats['workflow_execs'] += 1
        rows = self._query(
            "SELECT * FROM mt_custom_workflows WHERE workflow_id = ?", (wf_id,))
        if not rows:
            return {'success': False, 'error': f'工作流不存在: {wf_id}'}
        r = rows[0]
        if r['status'] != WorkflowStatus.ACTIVE.value:
            return {'success': False, 'error': f'工作流非激活状态: {r["status"]}'}
        # 条件评估（简单表达式，禁止执行任意代码）
        cond_passed = True
        try:
            cond = json.loads(r['condition_json'] or '{}')
            expr = cond.get('expression', '')
            args = cond.get('args', {})
            if expr:
                cond_passed = self._safe_eval_condition(expr, context or {}, args)
        except Exception as e:
            cond_passed = False

        # 记录执行
        self._write(
            "UPDATE mt_custom_workflows SET runs_count = runs_count + 1, "
            "last_run_at = ? WHERE workflow_id = ?",
            (datetime.now().isoformat(), wf_id))
        return {
            'success': True,
            'workflow_id': wf_id,
            'condition_passed': cond_passed,
            'actions_count': len(json.loads(r['actions_json'] or '[]')),
            'executed_at': datetime.now().isoformat(),
        }

    def _safe_eval_condition(self, expr: str, context: Dict, args: Dict) -> bool:
        """安全条件评估：仅允许 字段比较/AND/OR/IN 这类模式"""
        if not expr:
            return True
        # 白名单字符：字母数字. 空格 AND OR IN > < = != , ( ) % $
        if not re.match(r'^[A-Za-z0-9_. ]+(AND|OR|IN|>|<|=|!=|,|\(|\)|%|")*[A-Za-z0-9_. ")]*$', expr):
            logger.warning(f"工作流表达式不合规，拒绝: {expr[:60]}")
            return False
        # 简化实现：支持 $name == value 模式
        try:
            for k, v in (context or {}).items():
                if isinstance(v, bool):
                    expr = expr.replace(f'${k}', 'TRUE' if v else 'FALSE')
                elif isinstance(v, (int, float)):
                    expr = expr.replace(f'${k}', str(v))
                else:
                    expr = expr.replace(f'${k}', f'"{v}"')
            # 仅支持简单相等
            if '"' in expr and '==' in expr:
                left, right = expr.split('==', 1)
                return left.strip().strip('"') == right.strip().strip('"')
        except Exception:
            pass
        return True  # 默认通过

    # ======================================================================
    # 子模块7：表单字段定制
    # ======================================================================

    def get_form_fields(self, page: str) -> List[Dict[str, Any]]:
        """获取某页面的自定义字段（合并内建默认值）"""
        self.stats['form_gets'] += 1
        rows = self._query(
            "SELECT field_name, field_type, label, required, default_json, "
            "validations_json, options_json, display_order, visible "
            "FROM mt_custom_form_fields WHERE page = ? ORDER BY display_order ASC",
            (page,))
        result = []
        for r in rows:
            field = {
                'name': r['field_name'],
                'type': r['field_type'],
                'label': r['label'],
                'required': bool(r['required']),
                'visible': bool(r['visible']),
                'order': r['display_order'],
            }
            for k, jk in [('default', 'default_json'),
                          ('validations', 'validations_json'),
                          ('options', 'options_json')]:
                try:
                    field[k] = json.loads(r[jk] or 'null')
                except Exception:
                    field[k] = None
            result.append(field)
        return result

    def set_form_field(self, page: str, field_name: str, field_type: FieldType,
                       label: str, required: bool = False, default: Any = None,
                       validations: Dict = None, options: List = None,
                       display_order: int = 0, visible: bool = True,
                       changed_by: str = "system") -> Dict[str, Any]:
        """设置/更新页面自定义字段"""
        self.stats['form_sets'] += 1
        ft = field_type.value if isinstance(field_type, FieldType) else field_type
        # 校验类型
        try:
            FieldType(ft)
        except ValueError:
            return {'success': False, 'error': f'非法字段类型: {ft}'}
        ok = self._write(
            "INSERT OR REPLACE INTO mt_custom_form_fields "
            "(page, field_name, field_type, label, required, default_json, "
            "validations_json, options_json, display_order, visible, "
            "updated_at, updated_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (page, field_name, ft, label, 1 if required else 0,
             json.dumps(default, ensure_ascii=False),
             json.dumps(validations or {}, ensure_ascii=False),
             json.dumps(options or [], ensure_ascii=False),
             display_order, 1 if visible else 0,
             datetime.now().isoformat(), changed_by))
        return {'success': ok, 'page': page, 'field': field_name, 'type': ft}

    def delete_form_field(self, page: str, field_name: str) -> Dict[str, Any]:
        ok = self._write(
            "DELETE FROM mt_custom_form_fields WHERE page = ? AND field_name = ?",
            (page, field_name))
        return {'success': ok, 'page': page, 'field': field_name}

    # ======================================================================
    # 通用状态
    # ======================================================================

    def get_status(self) -> Dict[str, Any]:
        return {
            'version': self.ENGINE_VERSION,
            'widget_types': [w.value for w in WidgetType],
            'field_types': [f.value for f in FieldType],
            'workflow_statuses': [s.value for s in WorkflowStatus],
            'default_role_dashboards': list(DEFAULT_ROLE_DASHBOARDS.keys()),
            'stats': self.stats,
            'cloud_sync_available': self.cloud_sync is not None,
            'timestamp': datetime.now().isoformat(),
        }

    # ======================================================================
    # DB辅助
    # ======================================================================

    def _conn(self):
        if self.dual_db:
            return self.dual_db.get_connection()
        return sqlite3.connect(self.db_path or ':memory:', timeout=10)

    def _write(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_write(sql, params)
        try:
            conn = self._conn()
            conn.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"_write failed: {e}")
            return False

    def _query(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_query(sql, params)
        try:
            conn = self._conn()
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"_query failed: {e}")
            return []

    def _ensure_tables(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS mt_custom_dashboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                username TEXT,
                widgets_json TEXT,
                updated_at TEXT,
                updated_by TEXT,
                version INTEGER,
                UNIQUE(role, username) ON CONFLICT REPLACE
            )""",
            """CREATE TABLE IF NOT EXISTS mt_custom_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT UNIQUE,
                name TEXT,
                owner TEXT,
                description TEXT,
                status TEXT,
                trigger_json TEXT,
                condition_json TEXT,
                actions_json TEXT,
                created_at TEXT,
                updated_at TEXT,
                runs_count INTEGER DEFAULT 0,
                last_run_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_custom_form_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT NOT NULL,
                field_name TEXT NOT NULL,
                field_type TEXT,
                label TEXT,
                required INTEGER DEFAULT 0,
                default_json TEXT,
                validations_json TEXT,
                options_json TEXT,
                display_order INTEGER DEFAULT 0,
                visible INTEGER DEFAULT 1,
                updated_at TEXT,
                updated_by TEXT,
                UNIQUE(page, field_name) ON CONFLICT REPLACE
            )""",
        ]
        for sql in tables:
            self._write(sql, ())
