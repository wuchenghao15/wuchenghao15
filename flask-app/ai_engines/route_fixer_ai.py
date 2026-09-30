# -*- coding: utf-8 -*-
r"""
AI员工：路由修复专家
负责批量检测和修复路由冲突、权限配置错误、404等问题
r"""

import os
import json
import logging
from datetime import datetime
import sqlite3
from flask import Flask

logger = logging.getLogger(__name__)

class RouteFixerAI:
    r"""路由修复AI员工r"""

    def __init__(self, db_path, app=None):
        self.db_path = db_path
        self.app = app
        self.employee_id = r"route_fixer_001"
        self.employee_name = r"路由修复专家"
        self.specialty = r"路由冲突检测、权限配置修复、404错误处理"
        self.fix_count = 0
        self.report_count = 0

    def analyze_routes(self):
        r"""分析路由问题r"""
        issues = []

        if not self.app:
            logger.warning(r"Flask应用未初始化，无法分析路由")
            return issues

        # 检查路由重复
        route_map = {}
        for rule in self.app.url_map.iter_rules():
            route_path = str(rule)
            endpoint = rule.endpoint

            if route_path in route_map:
                # 发现重复路由
                issues.append({
                    r'type': r'duplicate_route',
                    r'route': route_path,
                    r'endpoints': [route_map[route_path], endpoint],
                    r'description': fr'路由重复: {route_path} 有多个endpoint',
                    r'priority': r'high',
                    r'auto_fix': True
                })
            else:
                route_map[route_path] = endpoint

        # 检查关键路由是否存在
        critical_routes = [
            r'/super_admin_dashboard',
            r'/admin_dashboard',
            r'/admin_center',
            r'/hardware/dashboard',
            r'/exam_system',
            r'/test_system',
            r'/learning_system'
        ]

        for route in critical_routes:
            if route not in route_map:
                issues.append({
                    r'type': r'missing_route',
                    r'route': route,
                    r'description': fr'关键路由缺失: {route}',
                    r'priority': r'critical',
                    r'auto_fix': True
                })

        return issues

    def auto_fix_route(self, issue):
        r"""自动修复路由问题r"""
        if issue[r'type'] == r'missing_route':
            # 添加缺失的路由
            route_path = issue[r'route']

            # 根据路由类型添加处理函数
            if route_path == r'/hardware/dashboard':
                self._add_hardware_dashboard_route()
                self.fix_count += 1
                return True

        return False

    def _add_hardware_dashboard_route(self):
        r"""添加硬件管理员仪表盘路由r"""
        if not self.app:
            return

        try:
            # 检查路由是否已存在
            for rule in self.app.url_map.iter_rules():
                if str(rule) == r'/hardware/dashboard':
                    logger.info(r"/hardware/dashboard 路由已存在")
                    return

            # 添加路由
            @self.app.route(r'/hardware/dashboard')
            def hardware_dashboard():
                from flask import session, redirect, render_template
                role = session.get(r'role', r'guest')
                if role in [r'hardware_admin', r'hardware_vikey_admin', r'super_admin', r'system_admin']:
                    return redirect(r'/super_admin_dashboard')
                return redirect(r'/dashboard')

            logger.info(r"成功添加 /hardware/dashboard 路由")
            self.fix_count += 1

        except Exception as e:
            logger.error(fr"添加路由失败: {e}")

    def batch_fix_routes(self):
        r"""批量修复路由r"""
        logger.info(fr"[{self.employee_name}] 开始批量修复路由...")

        # 分析所有问题
        all_issues = self.analyze_routes()

        logger.info(fr"[{self.employee_name}] 发现 {len(all_issues)} 个路由问题")

        # 自动修复问题
        fixed_count = 0
        for issue in all_issues:
            if issue[r'auto_fix']:
                if self.auto_fix_route(issue):
                    fixed_count += 1

        logger.info(fr"[{self.employee_name}] 成功修复 {fixed_count} 个路由问题")

        # 上报修复结果到数据库
        self.report_to_database(all_issues, fixed_count)

        return {
            r'total_issues': len(all_issues),
            r'fixed_count': fixed_count,
            r'employee': self.employee_name,
            r'specialty': self.specialty
        }

    def report_to_database(self, issues, fixed_count):
        r"""上报修复结果到数据库r"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建AI员工修复报告表
            cursor.execute(r'''
            CREATE TABLE IF NOT EXISTS ai_employee_fix_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                specialty TEXT,
                issue_type TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                fix_method TEXT,
                fixed BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                additional_info TEXT
            )
            r''')

            # 插入修复报告
            for issue in issues:
                cursor.execute(r'''
                INSERT INTO ai_employee_fix_reports
                (employee_id, employee_name, specialty, issue_type, issue_description, fix_method, fixed, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                r''', (
                    self.employee_id,
                    self.employee_name,
                    self.specialty,
                    issue[r'type'],
                    issue[r'description'],
                    r'自动修复' if issue[r'auto_fix'] else r'需要人工处理',
                    issue[r'auto_fix'],
                    json.dumps(issue)
                ))

            conn.commit()
            conn.close()

            self.report_count += len(issues)
            logger.info(fr"[{self.employee_name}] 已上报 {len(issues)} 个路由修复报告到数据库")

        except Exception as e:
            logger.error(fr"[{self.employee_name}] 上报数据库失败: {e}")


def init_route_fixer_ai(db_path, app=None):
    r"""初始化路由修复AI员工r"""
    return RouteFixerAI(db_path, app)


# 创建全局实例
route_fixer_ai = None


def get_route_fixer_ai(app=None):
    r"""获取路由修复AI员工实例r"""
    global route_fixer_ai
    if route_fixer_ai is None:
        db_path = r'/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        route_fixer_ai = RouteFixerAI(db_path, app)
    return route_fixer_ai
