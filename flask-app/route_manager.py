# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
路由管理系统 - 负责路由规则的自动添加、保存和加载
"""

# JSON import removed - using database
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Tuple
from flask import Flask
import re

class RouteManager:
    """路由管理器,负责路由规则的自动添加、保存和加载"""

    def __init__(self, app: Flask = None, db_path: str = "app.db"):
        self.app = app
        self.db_path = db_path
        self.route_rules = []
        self._init_database()

    def _init_database(self):
        """Initialize database, create route rules table"""
        with sqlite3.connect(self.db_path) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            # 创建路由规则表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_path TEXT UNIQUE NOT NULL,
            rule_type TEXT DEFAULT 'static',
            handler_name TEXT,
            methods TEXT DEFAULT '["GET"]',
            validation_employee_id TEXT,
            routing_employee_id TEXT,
            requires_auth INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()

    def scan_existing_routes(self) -> List[Dict[str, Any]]:
        """扫描Flask应用中已有的路由

        Returns:
            路由规则列表
        """
        if not self.app:
            return []

        routes = []
        for rule in self.app.url_map.iter_rules():
            # 跳过静态文件路由
            if 'static' in rule.endpoint:
                continue

            route_path = str(rule)
            methods = [method for method in rule.methods if method not in ['HEAD', 'OPTIONS']]

            routes.append({
                'route_path': route_path,
                'rule_type': self._detect_rule_type(route_path),
                'handler_name': rule.endpoint,
                'methods': str(methods),
                'requires_auth': 1 if '/auth/' in route_path else 0,
                'priority': 0,
                'is_active': 1
            })

        return routes

    def _detect_rule_type(self, route_path: str) -> str:
        """检测路由类型

        Args:
            route_path: 路由路径

        Returns:
            路由类型:static, dynamic, variable
        """
        if '<' in route_path or '>' in route_path:
            return 'dynamic'
        elif re.search(r'\d+', route_path):
            return 'variable'
        else:
            return 'static'

    def save_routes_to_db(self, routes: List[Dict[str, Any]]) -> int:
        """将路由规则保存到数据库

        Args:
            routes: 路由规则列表

        Returns:
            保存的路由数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            saved_count = 0
            for route in routes:
                # 检查路由是否已存在
                cursor.execute("SELECT id FROM route_rules WHERE route_path = ?", (route['route_path'],))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有路由
                    cursor.execute('''
                    UPDATE route_rules
                    SET rule_type = ?, handler_name = ?, methods = ?, requires_auth = ?,
                    priority = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE route_path = ?
                    ''', (
                        route['rule_type'], route['handler_name'], route['methods'],
                        route['requires_auth'], route['priority'], route['is_active'],
                        route['route_path']
                    ))
                else:
                    # 插入新路由
                    cursor.execute('''
                    INSERT INTO route_rules
                    (route_path, rule_type, handler_name, methods, requires_auth, priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        route['route_path'], route['rule_type'], route['handler_name'],
                        route['methods'], route['requires_auth'], route['priority'],
                        route['is_active']
                    ))
                saved_count += 1
            
            conn.commit()
        return saved_count

    def load_routes_from_db(self) -> List[Dict[str, Any]]:
        """从数据库加载路由规则

        Returns:
            路由规则列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, route_path, rule_type, handler_name, methods,
            validation_employee_id, routing_employee_id, requires_auth,
            priority, is_active, created_at, updated_at
            FROM route_rules
            WHERE is_active = 1
            ORDER BY priority DESC
            ''')
            routes = []
            for row in cursor.fetchall():
                route = {
                    'id': row[0],
                    'route_path': row[1],
                    'rule_type': row[2],
                    'handler_name': row[3],
                    'methods': eval(row[4]),
                    'validation_employee_id': row[5],
                    'routing_employee_id': row[6],
                    'requires_auth': row[7],
                    'priority': row[8],
                    'is_active': row[9],
                    'created_at': row[10],
                    'updated_at': row[11]
                }
                routes.append(route)
        return routes

    def add_route_rule(self, route_path: str, handler_name: str, methods: List[str] = None,
                       validation_employee_id: str = None, routing_employee_id: str = None,
                       requires_auth: int = 0, priority: int = 0) -> bool:
        """添加新的路由规则

        Args:
            route_path: 路由路径
            handler_name: 处理函数名称
            methods: 请求方法列表
            validation_employee_id: 验证AI员工ID
            routing_employee_id: 路由AI员工ID
            requires_auth: 是否需要认证
            priority: 优先级

        Returns:
            添加成功返回True,失败返回False
        """
        if not route_path or not handler_name:
            return False

        methods = methods or ['GET']
        rule_type = self._detect_rule_type(route_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                INSERT INTO route_rules
                (route_path, rule_type, handler_name, methods, validation_employee_id,
                routing_employee_id, requires_auth, priority, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    route_path, rule_type, handler_name, str(methods),
                    validation_employee_id, routing_employee_id, requires_auth, priority
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # 路由已存在
                return False
            except Exception as e:
                print(f"添加路由规则失败: {e}")
                return False

    def update_route_rule(self, route_id: int, updates: Dict[str, Any]) -> bool:
        """更新路由规则

        Args:
            route_id: 路由ID
            updates: 更新的字段

        Returns:
            更新成功返回True,失败返回False
        """
        if not updates:
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                # 构建更新语句
                update_fields = []
                update_values = []

                for key, value in updates.items():
                    if key in ['route_path', 'rule_type', 'handler_name', 'methods',
                              'validation_employee_id', 'routing_employee_id',
                              'requires_auth', 'priority', 'is_active']:
                        if key == 'methods':
                            value = str(value)
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)

                if not update_fields:
                    return False

                update_values.append(route_id)
                update_sql = f'''
                    UPDATE route_rules
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                '''

                cursor.execute(update_sql, update_values)
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"更新路由规则失败: {e}")
                return False

    def delete_route_rule(self, route_id: int) -> bool:
        """删除路由规则

        Args:
            route_id: 路由ID

        Returns:
            删除成功返回True,失败返回False
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM route_rules WHERE id = ?", (route_id,))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"删除路由规则失败: {e}")
                return False

    def sync_routes(self) -> Tuple[int, int]:
        """同步现有路由到数据库

        Returns:
            (路由总数, 保存数量)
        """
        routes = self.scan_existing_routes()
        saved_count = self.save_routes_to_db(routes)
        return len(routes), saved_count

    def get_all_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由规则

        Returns:
            所有路由规则列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, route_path, rule_type, handler_name, methods,
            priority, is_active, created_at, updated_at
            FROM route_rules
            ORDER BY priority DESC
            ''')
            
            routes = []
            for row in cursor.fetchall():
                route = {
                    'id': row[0],
                    'route_path': row[1],
                    'rule_type': row[2],
                    'handler_name': row[3],
                    'methods': eval(row[4]) if row[4] else [],
                    'priority': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
                routes.append(route)
        return routes

    def get_route_by_path(self, route_path: str) -> Dict[str, Any]:
        """根据路由路径获取路由规则

        Args:
            route_path: 路由路径

        Returns:
            路由规则,不存在返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT id, route_path, rule_type, handler_name, methods,
            validation_employee_id, routing_employee_id, requires_auth,
            priority, is_active, created_at, updated_at
            FROM route_rules
            WHERE route_path = ? AND is_active = 1
            ''', (route_path,))
            
            row = cursor.fetchone()
            if not row:
                return None

            return {
                'id': row[0],
                'route_path': row[1],
                'rule_type': row[2],
                'handler_name': row[3],
                'methods': eval(row[4]) if row[4] else [],
                'validation_employee_id': row[5],
                'routing_employee_id': row[6],
                'requires_auth': row[7],
                'priority': row[8],
                'is_active': row[9],
                'created_at': row[10],
                'updated_at': row[11]
            }

    def bind_ai_employees(self, route_path: str, validation_employee_id: str = None,
                         routing_employee_id: str = None) -> bool:
        """绑定AI员工到路由

        Args:
            route_path: 路由路径
            validation_employee_id: 验证AI员工ID
            routing_employee_id: 路由AI员工ID

        Returns:
            绑定成功返回True,失败返回False
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                UPDATE route_rules
                SET validation_employee_id = ?, routing_employee_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE route_path = ?
                ''', (validation_employee_id, routing_employee_id, route_path))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"绑定AI员工失败: {e}")
                return False


_route_manager = None

def get_route_manager(app: Flask = None, db_path: str = "app.db") -> RouteManager:
    """获取路由管理器实例

    Args:
        app: Flask应用实例

    Returns:
        路由管理器实例
    """
    global _route_manager
    if _route_manager is None:
        _route_manager = RouteManager(app, db_path)
    elif app and not _route_manager.app:
        _route_manager.app = app
    return _route_manager
