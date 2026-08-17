# -*- coding: utf-8 -*-
"""
AI员工：路由修复专家
负责批量检测和修复路由冲突、权限配置错误、404等问题
"""

import os
import json
import logging
from datetime import datetime
import sqlite3
from flask import Flask

logger = logging.getLogger(__name__)

class RouteFixerAI:
    """路由修复AI员工"""
    
    def __init__(self, db_path, app=None):
        self.db_path = db_path
        self.app = app
        self.employee_id = "route_fixer_001"
        self.employee_name = "路由修复专家"
        self.specialty = "路由冲突检测、权限配置修复、404错误处理"
        self.fix_count = 0
        self.report_count = 0
        
    def analyze_routes(self):
        """分析路由问题"""
        issues = []
        
        if not self.app:
            logger.warning("Flask应用未初始化，无法分析路由")
            return issues
        
        # 检查路由重复
        route_map = {}
        for rule in self.app.url_map.iter_rules():
            route_path = str(rule)
            endpoint = rule.endpoint
            
            if route_path in route_map:
                # 发现重复路由
                issues.append({
                    'type': 'duplicate_route',
                    'route': route_path,
                    'endpoints': [route_map[route_path], endpoint],
                    'description': f'路由重复: {route_path} 有多个endpoint',
                    'priority': 'high',
                    'auto_fix': True
                })
            else:
                route_map[route_path] = endpoint
        
        # 检查关键路由是否存在
        critical_routes = [
            '/super_admin_dashboard',
            '/admin_dashboard',
            '/admin_center',
            '/hardware/dashboard',
            '/exam_system',
            '/test_system',
            '/learning_system'
        ]
        
        for route in critical_routes:
            if route not in route_map:
                issues.append({
                    'type': 'missing_route',
                    'route': route,
                    'description': f'关键路由缺失: {route}',
                    'priority': 'critical',
                    'auto_fix': True
                })
        
        return issues
    
    def auto_fix_route(self, issue):
        """自动修复路由问题"""
        if issue['type'] == 'missing_route':
            # 添加缺失的路由
            route_path = issue['route']
            
            # 根据路由类型添加处理函数
            if route_path == '/hardware/dashboard':
                self._add_hardware_dashboard_route()
                self.fix_count += 1
                return True
            
        return False
    
    def _add_hardware_dashboard_route(self):
        """添加硬件管理员仪表盘路由"""
        if not self.app:
            return
        
        try:
            # 检查路由是否已存在
            for rule in self.app.url_map.iter_rules():
                if str(rule) == '/hardware/dashboard':
                    logger.info("/hardware/dashboard 路由已存在")
                    return
            
            # 添加路由
            @self.app.route('/hardware/dashboard')
            def hardware_dashboard():
                from flask import session, redirect, render_template
                role = session.get('role', 'guest')
                if role in ['hardware_admin', 'hardware_vikey_admin', 'super_admin', 'system_admin']:
                    return redirect('/super_admin_dashboard')
                return redirect('/dashboard')
            
            logger.info("成功添加 /hardware/dashboard 路由")
            self.fix_count += 1
        
        except Exception as e:
            logger.error(f"添加路由失败: {e}")
    
    def batch_fix_routes(self):
        """批量修复路由"""
        logger.info(f"[{self.employee_name}] 开始批量修复路由...")
        
        # 分析所有问题
        all_issues = self.analyze_routes()
        
        logger.info(f"[{self.employee_name}] 发现 {len(all_issues)} 个路由问题")
        
        # 自动修复问题
        fixed_count = 0
        for issue in all_issues:
            if issue['auto_fix']:
                if self.auto_fix_route(issue):
                    fixed_count += 1
        
        logger.info(f"[{self.employee_name}] 成功修复 {fixed_count} 个路由问题")
        
        # 上报修复结果到数据库
        self.report_to_database(all_issues, fixed_count)
        
        return {
            'total_issues': len(all_issues),
            'fixed_count': fixed_count,
            'employee': self.employee_name,
            'specialty': self.specialty
        }
    
    def report_to_database(self, issues, fixed_count):
        """上报修复结果到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建AI员工修复报告表
            cursor.execute('''
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
            ''')
            
            # 插入修复报告
            for issue in issues:
                cursor.execute('''
                INSERT INTO ai_employee_fix_reports 
                (employee_id, employee_name, specialty, issue_type, issue_description, fix_method, fixed, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.employee_id,
                    self.employee_name,
                    self.specialty,
                    issue['type'],
                    issue['description'],
                    '自动修复' if issue['auto_fix'] else '需要人工处理',
                    issue['auto_fix'],
                    json.dumps(issue)
                ))
            
            conn.commit()
            conn.close()
            
            self.report_count += len(issues)
            logger.info(f"[{self.employee_name}] 已上报 {len(issues)} 个路由修复报告到数据库")
        
        except Exception as e:
            logger.error(f"[{self.employee_name}] 上报数据库失败: {e}")


def init_route_fixer_ai(db_path, app=None):
    """初始化路由修复AI员工"""
    return RouteFixerAI(db_path, app)


# 创建全局实例
route_fixer_ai = None


def get_route_fixer_ai(app=None):
    """获取路由修复AI员工实例"""
    global route_fixer_ai
    if route_fixer_ai is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        route_fixer_ai = RouteFixerAI(db_path, app)
    return route_fixer_ai