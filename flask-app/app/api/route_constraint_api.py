#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由约束引擎 API
"""
import sqlite3
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from app.middlewares.route_constraint_engine import (
    get_constraint_engine, with_constraint_check
)

logger = logging.getLogger('route_constraint_api')

constraint_api_bp = Blueprint('route_constraint_api', __name__, url_prefix='/api/constraint')


def get_db():
    conn = sqlite3.connect('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    conn.row_factory = sqlite3.Row
    return conn


@constraint_api_bp.route('/check', methods=['POST'])
def check_constraint():
    """检查指定路径和上下文的约束"""
    try:
        data = request.get_json() or {}
        path = data.get('path', request.path)
        method = data.get('method', 'GET')
        user_context = data.get('user_context', {
            'user_id': request.cookies.get('user_id'),
            'role': request.cookies.get('role', 'guest')
        })

        engine = get_constraint_engine()
        result = engine.check_route_constraints(path, method, user_context)

        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"约束检查失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@constraint_api_bp.route('/summary', methods=['GET'])
def get_constraint_summary():
    """获取约束引擎的整体摘要"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 访问控制规则
        cursor.execute("SELECT COUNT(*) FROM access_control_rules WHERE is_active = 1")
        ac_count = cursor.fetchone()[0]

        # 规则约束
        cursor.execute("SELECT COUNT(*) FROM rule_constraints WHERE is_active = 1")
        rc_count = cursor.fetchone()[0]

        # 系统规则
        cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
        sr_count = cursor.fetchone()[0]

        # 按角色分组的访问控制
        cursor.execute("""
            SELECT role_name, COUNT(*) as count
            FROM access_control_rules
            WHERE is_active = 1
            GROUP BY role_name
        """)
        ac_by_role = [dict(row) for row in cursor.fetchall()]

        # 按分类分组的约束
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM rule_constraints
            WHERE is_active = 1
            GROUP BY category
        """)
        rc_by_category = [dict(row) for row in cursor.fetchall()]

        # 按类型分组的系统规则
        cursor.execute("""
            SELECT rule_type, COUNT(*) as count
            FROM system_rules
            WHERE is_active = 1
            GROUP BY rule_type
        """)
        sr_by_type = [dict(row) for row in cursor.fetchall()]

        # 约束执行统计
        cursor.execute("""
            SELECT COUNT(*) FROM rule_execution_logs
            WHERE execution_time > datetime('now', '-7 days')
        """)
        try:
            recent_executions = cursor.fetchone()[0]
        except Exception:
            recent_executions = 0

        conn.close()

        return jsonify({
            'success': True,
            'summary': {
                'access_control_rules': {
                    'total': ac_count,
                    'by_role': ac_by_role
                },
                'rule_constraints': {
                    'total': rc_count,
                    'by_category': rc_by_category
                },
                'system_rules': {
                    'total': sr_count,
                    'by_type': sr_by_type
                },
                'recent_executions_7d': recent_executions
            }
        })
    except Exception as e:
        logger.error(f"获取约束摘要失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@constraint_api_bp.route('/conflicts', methods=['GET'])
def detect_conflicts():
    """检测约束之间的潜在冲突"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        conflicts = []

        # 冲突1: 同一角色多个重叠路径规则
        cursor.execute("""
            SELECT role_name, resource_path, allowed_methods
            FROM access_control_rules
            WHERE is_active = 1
            ORDER BY role_name, priority ASC
        """)
        rules = [dict(row) for row in cursor.fetchall()]

        for i, r1 in enumerate(rules):
            for r2 in rules[i+1:]:
                if r1['role_name'] == r2['role_name']:
                    # 检查路径是否重叠
                    if r1['resource_path'] == r2['resource_path']:
                        try:
                            m1 = set(json.loads(r1['allowed_methods'] or '[]'))
                            m2 = set(json.loads(r2['allowed_methods'] or '[]'))
                        except Exception:
                            continue
                        if m1 != m2:
                            conflicts.append({
                                'type': 'duplicate_path_different_methods',
                                'severity': 'high',
                                'role': r1['role_name'],
                                'path': r1['resource_path'],
                                'rule1_methods': list(m1),
                                'rule2_methods': list(m2),
                                'message': f"角色 {r1['role_name']} 的路径 {r1['resource_path']} 有多个规则定义了不同的方法"
                            })

        # 冲突2: 约束优先级冲突
        cursor.execute("""
            SELECT constraint_key, priority, is_active
            FROM rule_constraints
            WHERE is_active = 1
            ORDER BY priority ASC
        """)
        constraints = [dict(row) for row in cursor.fetchall()]

        seen_keys = {}
        for c in constraints:
            if c['constraint_key'] in seen_keys:
                if seen_keys[c['constraint_key']]['priority'] == c['priority']:
                    conflicts.append({
                        'type': 'same_priority_duplicate',
                        'severity': 'medium',
                        'constraint': c['constraint_key'],
                        'priority': c['priority'],
                        'message': f"约束 {c['constraint_key']} 有多个相同优先级的实例"
                    })
            seen_keys[c['constraint_key']] = c

        # 冲突3: 业务规则矛盾（如维护模式 + 硬件认证必需）
        cursor.execute("""
            SELECT rule_code, rule_value FROM system_rules
            WHERE rule_code IN ('SYS_MAINTENANCE_MODE', 'HW_AUTH_REQUIRED')
            AND is_active = 1
        """)
        business_rules = {row['rule_code']: row['rule_value'] for row in cursor.fetchall()}

        # 这两个规则本身不矛盾，只是提示同时启用

        conn.close()

        return jsonify({
            'success': True,
            'conflicts_count': len(conflicts),
            'conflicts': conflicts
        })
    except Exception as e:
        logger.error(f"冲突检测失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@constraint_api_bp.route('/trace', methods=['GET'])
def get_constraint_trace():
    """获取最近的约束执行轨迹"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 尝试从 rule_execution_logs 读取
        try:
            cursor.execute("""
                SELECT * FROM rule_execution_logs
                ORDER BY execution_time DESC LIMIT 50
            """)
            traces = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            traces = []

        # 如果为空，从 access_logs 读取
        if not traces:
            try:
                cursor.execute("""
                    SELECT path, user_id, username, role, method, result, access_time as created_at
                    FROM access_logs
                    ORDER BY access_time DESC LIMIT 50
                """)
                traces = [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                traces = []

        conn.close()
        return jsonify({
            'success': True,
            'count': len(traces),
            'traces': traces
        })
    except Exception as e:
        logger.error(f"获取约束轨迹失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@constraint_api_bp.route('/interaction-matrix', methods=['GET'])
def get_interaction_matrix():
    """获取路由逻辑和权限约束的交互矩阵"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 获取所有路径
        cursor.execute("SELECT DISTINCT resource_path FROM access_control_rules WHERE is_active = 1")
        paths = [row['resource_path'] for row in cursor.fetchall()]

        # 获取所有角色
        cursor.execute("SELECT DISTINCT role_name FROM access_control_rules WHERE is_active = 1")
        roles = [row['role_name'] for row in cursor.fetchall()]

        # 获取所有约束分类
        cursor.execute("SELECT DISTINCT category FROM rule_constraints WHERE is_active = 1")
        categories = [row['category'] for row in cursor.fetchall()]

        # 构建交互矩阵
        matrix = []
        for path in paths:
            row = {'path': path, 'roles': {}, 'constraints': {}}
            for role in roles:
                cursor.execute("""
                    SELECT allowed_methods FROM access_control_rules
                    WHERE is_active = 1 AND resource_path = ? AND role_name = ?
                """, (path, role))
                r = cursor.fetchone()
                if r:
                    try:
                        methods = json.loads(r['allowed_methods'] or '[]')
                    except Exception:
                        methods = []
                    row['roles'][role] = {
                        'allowed': True,
                        'methods': methods
                    }
                else:
                    row['roles'][role] = {'allowed': False, 'methods': []}
            matrix.append(row)

        conn.close()

        return jsonify({
            'success': True,
            'roles': roles,
            'paths': paths,
            'categories': categories,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取交互矩阵失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
