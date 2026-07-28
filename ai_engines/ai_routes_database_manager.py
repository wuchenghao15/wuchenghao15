#!/usr/bin/env python3
"""
AI智能路由数据库管理系统
- 自动新建路由管理数据库
- 扫描并注册所有Flask路由（API+页面）到数据库
- 路由启用/禁用管理
- 路由访问统计与监控
- 路由权限配置管理
- 智能路由分类与标签
"""

import os
import sys
import json
import sqlite3
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 路由管理数据库路径
ROUTES_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')
ROUTES_MANAGEMENT_DB = os.path.join(ROUTES_DB_DIR, 'routes_management.db')


def get_routes_db_connection():
    """获取路由管理数据库连接"""
    conn = sqlite3.connect(ROUTES_MANAGEMENT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_routes_database():
    """初始化路由管理数据库"""
    conn = get_routes_db_connection()
    cursor = conn.cursor()

    # 路由注册表 - 存储所有路由（API + 页面）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT,
            route_path TEXT UNIQUE NOT NULL,
            endpoint TEXT,
            methods TEXT,
            route_type TEXT,
            category TEXT,
            sub_category TEXT,
            description TEXT,
            module TEXT,
            blueprint TEXT,
            template_used TEXT,
            is_enabled INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            require_login INTEGER DEFAULT 0,
            require_admin INTEGER DEFAULT 0,
            require_permission TEXT,
            cache_enabled INTEGER DEFAULT 0,
            cache_ttl INTEGER DEFAULT 0,
            total_accesses INTEGER DEFAULT 0,
            successful_accesses INTEGER DEFAULT 0,
            failed_accesses INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            last_accessed TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # 路由访问日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            route_path TEXT,
            method TEXT,
            user_id INTEGER,
            username TEXT,
            status_code INTEGER,
            response_time REAL,
            ip_address TEXT,
            user_agent TEXT,
            referrer TEXT,
            error_message TEXT,
            timestamp TEXT,
            FOREIGN KEY (route_id) REFERENCES routes(id)
        )
    ''')

    # 路由权限配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            role_name TEXT NOT NULL,
            permission TEXT DEFAULT 'allow',
            created_at TEXT,
            UNIQUE(route_id, role_name),
            FOREIGN KEY (route_id) REFERENCES routes(id)
        )
    ''')

    # 路由分组表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL,
            group_type TEXT,
            description TEXT,
            color TEXT DEFAULT '#3498db',
            icon TEXT DEFAULT 'fa-route',
            is_enabled INTEGER DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')

    # 路由标签表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT UNIQUE NOT NULL,
            tag_color TEXT DEFAULT '#95a5a6',
            description TEXT,
            created_at TEXT
        )
    ''')

    # 路由-标签关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_tag_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            UNIQUE(route_id, tag_id),
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (tag_id) REFERENCES route_tags(id)
        )
    ''')

    # 路由依赖关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            depends_on_route_id INTEGER NOT NULL,
            dependency_type TEXT DEFAULT 'redirect',
            created_at TEXT,
            UNIQUE(route_id, depends_on_route_id),
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (depends_on_route_id) REFERENCES routes(id)
        )
    ''')

    # 创建索引提升查询效率
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routes_path ON routes(route_path)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routes_endpoint ON routes(endpoint)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routes_category ON routes(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routes_type ON routes(route_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routes_enabled ON routes(is_enabled)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_logs_route_id ON route_access_logs(route_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_logs_timestamp ON route_access_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_perms_route_id ON route_permissions(route_id)')

    # 插入默认路由分组
    default_groups = [
        ('认证页面', 'page', '登录、注册等认证相关页面', '#e74c3c', 'fa-lock', 1),
        ('认证API', 'api', '认证相关API接口', '#c0392b', 'fa-key', 2),
        ('用户管理', 'mixed', '用户信息、角色管理', '#3498db', 'fa-users', 3),
        ('考试管理', 'mixed', '考试创建、管理、监控', '#9b59b6', 'fa-edit', 4),
        ('题库管理', 'mixed', '题目管理、导入导出', '#1abc9c', 'fa-question-circle', 5),
        ('AI引擎', 'api', 'AI员工、Agent、模型管理', '#f39c12', 'fa-robot', 6),
        ('系统管理', 'mixed', '系统配置、监控、维护', '#34495e', 'fa-cog', 7),
        ('数据分析', 'api', '数据统计、报表、分析', '#16a085', 'fa-chart-line', 8),
        ('Git同步', 'api', '代码同步、版本管理', '#8e44ad', 'fa-code-branch', 9),
        ('检索模型', 'api', '检索查询模型管理', '#27ae60', 'fa-search', 10),
        ('API数据库', 'api', 'API数据库管理', '#d35400', 'fa-database', 11),
        ('路由数据库', 'api', '路由数据库管理', '#2c3e50', 'fa-route', 12),
        ('首页导航', 'page', '系统首页和导航页面', '#2980b9', 'fa-home', 13),
        ('其他', 'mixed', '未分类的其他路由', '#95a5a6', 'fa-ellipsis-h', 99),
    ]

    for group in default_groups:
        cursor.execute('''
            INSERT OR IGNORE INTO route_groups
            (group_name, group_type, description, color, icon, is_enabled, display_order, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        ''', (group[0], group[1], group[2], group[3], group[4], group[5], datetime.now().isoformat()))

    # 插入默认标签
    default_tags = [
        ('公开', '#27ae60', '无需登录即可访问'),
        ('需登录', '#f39c12', '需要用户登录'),
        ('管理员', '#e74c3c', '需要管理员权限'),
        ('高频访问', '#3498db', '访问频率高'),
        ('低频访问', '#95a5a6', '访问频率低'),
        ('核心功能', '#9b59b6', '系统核心功能'),
        ('辅助功能', '#1abc9c', '系统辅助功能'),
    ]

    for tag in default_tags:
        cursor.execute('''
            INSERT OR IGNORE INTO route_tags (tag_name, tag_color, description, created_at)
            VALUES (?, ?, ?, ?)
        ''', (tag[0], tag[1], tag[2], datetime.now().isoformat()))

    conn.commit()
    conn.close()
    logger.info("路由管理数据库初始化完成: routes_management.db")


def categorize_route(route_path, endpoint='', methods=''):
    """根据路由路径自动分类"""
    path_lower = route_path.lower()
    endpoint_lower = (endpoint or '').lower()
    is_api = path_lower.startswith('/api/')

    # 认证相关
    if any(k in path_lower for k in ['/auth', '/login', '/register', '/logout', '/session']):
        return '认证API' if is_api else '认证页面'

    # 用户管理
    if any(k in path_lower for k in ['/user', '/profile', '/role', '/avatar']):
        return '用户管理'

    # 考试管理
    if any(k in path_lower for k in ['/exam', '/proctor', '/monitor', '/paper']):
        return '考试管理'

    # 题库管理
    if any(k in path_lower for k in ['/question', '/bank', '/topic', '/knowledge']):
        return '题库管理'

    # AI引擎
    if any(k in path_lower for k in ['/ai_employee', '/ai_agent', '/ai_engine']):
        return 'AI引擎'

    # 检索模型
    if any(k in path_lower for k in ['/search_model']):
        return '检索模型'

    # API数据库
    if any(k in path_lower for k in ['/api_database']):
        return 'API数据库'

    # 路由数据库
    if any(k in path_lower for k in ['/route_database', '/routes_database']):
        return '路由数据库'

    # 系统管理
    if any(k in path_lower for k in ['/system', '/config', '/version', '/health', '/status', '/admin']):
        return '系统管理'

    # 数据分析
    if any(k in path_lower for k in ['/stat', '/report', '/analytics', '/dashboard']):
        return '数据分析'

    # Git同步
    if any(k in path_lower for k in ['/git', '/sync', '/commit', '/push']):
        return 'Git同步'

    # 首页导航
    if path_lower in ['/', '/index', '/home'] or path_lower.startswith('/static'):
        return '首页导航'

    return '其他'


def detect_route_type(route_path):
    """检测路由类型"""
    if route_path.startswith('/api/'):
        return 'api'
    elif route_path.startswith('/static'):
        return 'static'
    elif route_path.endswith(('.js', '.css', '.png', '.jpg', '.ico')):
        return 'static'
    else:
        return 'page'


class AIRoutesDatabaseManager:
    """AI智能路由数据库管理器"""

    def __init__(self):
        self.routes = {}
        self.groups = {}
        self.stats = {
            'total_routes': 0,
            'enabled_routes': 0,
            'disabled_routes': 0,
            'api_routes': 0,
            'page_routes': 0,
            'static_routes': 0,
            'total_groups': 0,
            'total_accesses': 0
        }
        self._initialized = False

    def initialize(self):
        """初始化路由管理器"""
        init_routes_database()
        self._load_groups()
        self._initialized = True
        logger.info("AI路由数据库管理器初始化完成")

    def _load_groups(self):
        """加载路由分组"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM route_groups WHERE is_enabled = 1 ORDER BY display_order')
            groups = cursor.fetchall()
            conn.close()

            for group in groups:
                g = dict(group)
                self.groups[g['group_name']] = g
            self.stats['total_groups'] = len(self.groups)
        except Exception as e:
            logger.error(f"加载路由分组失败: {e}")

    def scan_and_register_routes(self, app):
        """扫描Flask应用的所有路由并注册到数据库"""
        registered_count = 0
        updated_count = 0

        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()

            for rule in app.url_map.iter_rules():
                if rule.endpoint == 'static':
                    continue

                route_path = rule.rule
                methods = ','.join(sorted([m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]))
                endpoint = rule.endpoint
                route_type = detect_route_type(route_path)
                category = categorize_route(route_path, endpoint, methods)

                # 提取模块名和蓝图
                if '.' in endpoint:
                    parts = endpoint.split('.')
                    module = parts[0]
                    blueprint = parts[0]
                else:
                    module = 'simple_start'
                    blueprint = None

                # 自动描述
                description = self._generate_description(route_path, endpoint, methods, route_type)

                # 自动判断权限要求
                require_login = 1 if route_type == 'api' or '/admin' in route_path else 0
                require_admin = 1 if '/admin' in route_path or 'super_admin' in endpoint else 0
                require_permission = 'admin' if require_admin else ('user' if require_login else None)

                # 尝试获取使用的模板
                template_used = self._detect_template(route_path, endpoint)

                # 插入或更新
                cursor.execute('''
                    INSERT INTO routes
                    (route_name, route_path, endpoint, methods, route_type, category,
                     description, module, blueprint, template_used, is_enabled, is_active,
                     require_login, require_admin, require_permission, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?, ?)
                    ON CONFLICT(route_path) DO UPDATE SET
                        methods=excluded.methods,
                        endpoint=excluded.endpoint,
                        route_type=excluded.route_type,
                        category=excluded.category,
                        description=excluded.description,
                        template_used=excluded.template_used,
                        updated_at=excluded.updated_at
                ''', (endpoint, route_path, endpoint, methods, route_type, category,
                      description, module, blueprint, template_used,
                      require_login, require_admin, require_permission,
                      datetime.now().isoformat(), datetime.now().isoformat()))

                if cursor.rowcount > 0:
                    if cursor.rowcount == 1:
                        registered_count += 1
                    else:
                        updated_count += 1

            conn.commit()
            conn.close()

            # 更新统计
            self._update_stats()

            logger.info(f"路由扫描完成: 新注册 {registered_count} 个, 更新 {updated_count} 个")
            return {
                'registered': registered_count,
                'updated': updated_count,
                'total': self.stats['total_routes']
            }
        except Exception as e:
            logger.error(f"扫描注册路由失败: {e}")
            return {'error': str(e)}

    def _generate_description(self, route_path, endpoint, methods, route_type):
        """根据路由路径生成描述"""
        parts = route_path.strip('/').split('/')
        last_part = parts[-1] if parts else route_path

        method_desc = {
            'GET': '查看',
            'POST': '提交',
            'PUT': '更新',
            'DELETE': '删除',
            'PATCH': '修改'
        }

        # 页面路由描述
        if route_type == 'page':
            if route_path in ['/', '/index', '/home']:
                return '系统首页'
            elif 'dashboard' in route_path.lower():
                return '仪表板页面'
            elif 'login' in route_path.lower():
                return '登录页面'
            elif 'register' in route_path.lower():
                return '注册页面'
            elif 'profile' in route_path.lower():
                return '个人资料页面'
            elif 'admin' in route_path.lower():
                return '管理后台页面'
            else:
                return f'{last_part} 页面'

        # API路由描述
        if 'login' in route_path.lower():
            return '用户登录接口'
        elif 'logout' in route_path.lower():
            return '用户登出接口'
        elif 'register' in route_path.lower():
            return '用户注册接口'
        elif 'status' in route_path.lower():
            return '获取状态信息'
        elif 'list' in route_path.lower():
            return '获取列表数据'
        elif 'create' in route_path.lower():
            return '创建新资源'
        elif 'delete' in route_path.lower() or 'disable' in route_path.lower():
            return '禁用/删除资源'
        elif 'update' in route_path.lower() or 'enable' in route_path.lower():
            return '更新/启用资源'
        elif 'search' in route_path.lower():
            return '搜索查询'
        else:
            action = method_desc.get(methods.split(',')[0], '访问') if methods else '访问'
            return f'{action} {last_part}'

    def _detect_template(self, route_path, endpoint):
        """检测路由使用的模板"""
        if route_path.startswith('/api/'):
            return None

        parts = route_path.strip('/').split('/')
        if not parts or parts[0] == '':
            return 'index.html'

        # 根据路径推测模板
        first_part = parts[0]
        if len(parts) > 1:
            return f'{first_part}/{parts[-1]}.html'
        return f'{first_part}.html'

    def _update_stats(self):
        """更新统计数据"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM routes')
            self.stats['total_routes'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM routes WHERE is_enabled = 1')
            self.stats['enabled_routes'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM routes WHERE is_enabled = 0')
            self.stats['disabled_routes'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM routes WHERE route_type = 'api'")
            self.stats['api_routes'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM routes WHERE route_type = 'page'")
            self.stats['page_routes'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM routes WHERE route_type = 'static'")
            self.stats['static_routes'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM route_access_logs')
            self.stats['total_accesses'] = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            logger.error(f"更新统计失败: {e}")

    def enable_route(self, route_id):
        """启用路由"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE routes SET is_enabled = 1, is_active = 1, updated_at = ? WHERE id = ?',
                           (datetime.now().isoformat(), route_id))
            conn.commit()
            conn.close()
            self._update_stats()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"启用路由失败: {e}")
            return False

    def disable_route(self, route_id):
        """禁用路由"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE routes SET is_enabled = 0, is_active = 0, updated_at = ? WHERE id = ?',
                           (datetime.now().isoformat(), route_id))
            conn.commit()
            conn.close()
            self._update_stats()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"禁用路由失败: {e}")
            return False

    def enable_all_routes(self):
        """启用所有路由"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE routes SET is_enabled = 1, is_active = 1, updated_at = ?',
                           (datetime.now().isoformat(),))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            self._update_stats()
            return count
        except Exception as e:
            logger.error(f"启用所有路由失败: {e}")
            return 0

    def get_status(self):
        """获取路由数据库状态"""
        self._update_stats()
        return {
            **self.stats,
            'initialized': self._initialized,
            'database_path': ROUTES_MANAGEMENT_DB
        }

    def get_routes_list(self, category=None, route_type=None, enabled_only=False):
        """获取路由列表"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()

            query = 'SELECT * FROM routes'
            conditions = []
            params = []

            if category:
                conditions.append('category = ?')
                params.append(category)
            if route_type:
                conditions.append('route_type = ?')
                params.append(route_type)
            if enabled_only:
                conditions.append('is_enabled = 1')

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY category, route_path'
            cursor.execute(query, params)
            routes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return routes
        except Exception as e:
            logger.error(f"获取路由列表失败: {e}")
            return []

    def get_route_groups(self):
        """获取路由分组"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.*, COUNT(r.id) as route_count
                FROM route_groups g
                LEFT JOIN routes r ON r.category = g.group_name
                WHERE g.is_enabled = 1
                GROUP BY g.id
                ORDER BY g.display_order
            ''')
            groups = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return groups
        except Exception as e:
            logger.error(f"获取路由分组失败: {e}")
            return []

    def get_category_stats(self):
        """获取分类统计"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, route_type, COUNT(*) as count,
                       SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled,
                       SUM(total_accesses) as total_accesses
                FROM routes
                GROUP BY category, route_type
                ORDER BY count DESC
            ''')
            stats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"获取分类统计失败: {e}")
            return []

    def log_route_access(self, route_id, route_path, method, status_code, response_time,
                         user_id=None, username=None, ip_address=None, error_message=None):
        """记录路由访问日志"""
        try:
            conn = get_routes_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO route_access_logs
                (route_id, route_path, method, user_id, username, status_code,
                 response_time, ip_address, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (route_id, route_path, method, user_id, username, status_code,
                  response_time, ip_address, error_message, datetime.now().isoformat()))

            # 更新路由统计
            if route_id:
                success = 1 if status_code and 200 <= status_code < 400 else 0
                cursor.execute('''
                    UPDATE routes SET
                        total_accesses = total_accesses + 1,
                        successful_accesses = successful_accesses + ?,
                        failed_accesses = failed_accesses + ?,
                        avg_response_time = (avg_response_time * (total_accesses - 1) + ?) / total_accesses,
                        last_accessed = ?
                    WHERE id = ?
                ''', (success, 1 - success, response_time, datetime.now().isoformat(), route_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录路由访问日志失败: {e}")


# 全局管理器实例
ai_routes_db_manager = AIRoutesDatabaseManager()


def init_routes_db_manager():
    """初始化路由数据库管理器"""
    return ai_routes_db_manager.initialize()


def scan_and_register_routes(app):
    """扫描并注册所有路由"""
    return ai_routes_db_manager.scan_and_register_routes(app)


def get_routes_db_status():
    """获取路由数据库状态"""
    return ai_routes_db_manager.get_status()


def get_routes_db_list(category=None, route_type=None, enabled_only=False):
    """获取路由列表"""
    return ai_routes_db_manager.get_routes_list(category, route_type, enabled_only)


def enable_route_in_db(route_id):
    """启用路由"""
    return ai_routes_db_manager.enable_route(route_id)


def disable_route_in_db(route_id):
    """禁用路由"""
    return ai_routes_db_manager.disable_route(route_id)


def enable_all_routes_in_db():
    """启用所有路由"""
    return ai_routes_db_manager.enable_all_routes()


if __name__ == "__main__":
    init_routes_db_manager()
    status = get_routes_db_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
