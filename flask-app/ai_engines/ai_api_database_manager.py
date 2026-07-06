#!/usr/bin/env python3
"""
AI智能API数据库管理系统
- 自动新建API管理数据库
- 扫描并注册所有API路由到数据库
- API启用/禁用管理
- API调用统计与监控
- API权限配置管理
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

# API管理数据库路径
API_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases')
API_MANAGEMENT_DB = os.path.join(API_DB_DIR, 'api_management.db')


def get_api_db_connection():
    """获取API管理数据库连接"""
    conn = sqlite3.connect(API_MANAGEMENT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_api_database():
    """初始化API管理数据库"""
    conn = get_api_db_connection()
    cursor = conn.cursor()

    # API注册表 - 存储所有API路由
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_name TEXT,
            api_path TEXT UNIQUE NOT NULL,
            endpoint TEXT,
            methods TEXT,
            category TEXT,
            description TEXT,
            module TEXT,
            blueprint TEXT,
            is_enabled INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            require_auth INTEGER DEFAULT 1,
            require_admin INTEGER DEFAULT 0,
            rate_limit INTEGER DEFAULT 100,
            cache_enabled INTEGER DEFAULT 0,
            cache_ttl INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            successful_calls INTEGER DEFAULT 0,
            failed_calls INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            last_called TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # API调用日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id INTEGER,
            api_path TEXT,
            method TEXT,
            user_id INTEGER,
            status_code INTEGER,
            response_time REAL,
            request_size INTEGER,
            response_size INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            error_message TEXT,
            timestamp TEXT,
            FOREIGN KEY (api_id) REFERENCES apis(id)
        )
    ''')

    # API权限配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id INTEGER NOT NULL,
            role_name TEXT NOT NULL,
            permission TEXT DEFAULT 'allow',
            created_at TEXT,
            UNIQUE(api_id, role_name),
            FOREIGN KEY (api_id) REFERENCES apis(id)
        )
    ''')

    # API分组表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#3498db',
            icon TEXT DEFAULT 'fa-cube',
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT
        )
    ''')

    # API参数定义表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id INTEGER NOT NULL,
            param_name TEXT NOT NULL,
            param_type TEXT,
            param_location TEXT,
            required INTEGER DEFAULT 0,
            description TEXT,
            default_value TEXT,
            validation_rule TEXT,
            FOREIGN KEY (api_id) REFERENCES apis(id)
        )
    ''')

    # 创建索引提升查询效率
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apis_path ON apis(api_path)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apis_category ON apis(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apis_enabled ON apis(is_enabled)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_api_id ON api_call_logs(api_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_call_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_perms_api_id ON api_permissions(api_id)')

    # 插入默认API分组
    default_groups = [
        ('认证管理', '用户登录、注册、权限认证相关API', '#e74c3c', 'fa-lock'),
        ('用户管理', '用户信息管理、角色管理相关API', '#3498db', 'fa-users'),
        ('考试管理', '考试创建、管理、监控相关API', '#9b59b6', 'fa-edit'),
        ('题库管理', '题目管理、导入导出相关API', '#1abc9c', 'fa-question-circle'),
        ('AI引擎', 'AI员工、Agent、模型相关API', '#f39c12', 'fa-robot'),
        ('系统管理', '系统配置、监控、维护相关API', '#34495e', 'fa-cog'),
        ('数据分析', '数据统计、报表、分析相关API', '#16a085', 'fa-chart-line'),
        ('Git同步', '代码同步、版本管理相关API', '#8e44ad', 'fa-code-branch'),
        ('检索模型', '检索查询模型管理相关API', '#27ae60', 'fa-search'),
        ('其他', '未分类的其他API', '#95a5a6', 'fa-ellipsis-h'),
    ]

    for group in default_groups:
        cursor.execute('''
            INSERT OR IGNORE INTO api_groups (group_name, description, color, icon, is_enabled, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (group[0], group[1], group[2], group[3], datetime.now().isoformat()))

    conn.commit()
    conn.close()
    logger.info("API管理数据库初始化完成: api_management.db")


def categorize_api(api_path, endpoint=''):
    """根据API路径自动分类"""
    path_lower = api_path.lower()
    endpoint_lower = (endpoint or '').lower()

    if any(k in path_lower for k in ['/auth', '/login', '/register', '/logout', '/session']):
        return '认证管理'
    elif any(k in path_lower for k in ['/user', '/profile', '/role']):
        return '用户管理'
    elif any(k in path_lower for k in ['/exam', '/proctor', '/monitor']):
        return '考试管理'
    elif any(k in path_lower for k in ['/question', '/bank', '/topic']):
        return '题库管理'
    elif any(k in path_lower for k in ['/ai_employee', '/ai_agent', '/ai_engine', '/search_model']):
        return 'AI引擎'
    elif any(k in path_lower for k in ['/system', '/config', '/version', '/health', '/status']):
        return '系统管理'
    elif any(k in path_lower for k in ['/git', '/sync', '/commit', '/push']):
        return 'Git同步'
    elif any(k in path_lower for k in ['/stat', '/report', '/analytics', '/dashboard']):
        return '数据分析'
    elif any(k in path_lower for k in ['/search_model']):
        return '检索模型'
    else:
        return '其他'


class AIApiDatabaseManager:
    """AI智能API数据库管理器"""

    def __init__(self):
        self.apis = {}
        self.groups = {}
        self.stats = {
            'total_apis': 0,
            'enabled_apis': 0,
            'disabled_apis': 0,
            'total_groups': 0,
            'total_calls': 0
        }
        self._initialized = False

    def initialize(self):
        """初始化API管理器"""
        init_api_database()
        self._load_groups()
        self._initialized = True
        logger.info("AI API数据库管理器初始化完成")

    def _load_groups(self):
        """加载API分组"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_groups WHERE is_enabled = 1')
            groups = cursor.fetchall()
            conn.close()

            for group in groups:
                g = dict(group)
                self.groups[g['group_name']] = g
            self.stats['total_groups'] = len(self.groups)
        except Exception as e:
            logger.error(f"加载API分组失败: {e}")

    def scan_and_register_apis(self, app):
        """扫描Flask应用的所有路由并注册到数据库"""
        registered_count = 0
        updated_count = 0

        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()

            for rule in app.url_map.iter_rules():
                if rule.endpoint == 'static':
                    continue

                api_path = rule.rule
                methods = ','.join(sorted([m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]))
                endpoint = rule.endpoint
                category = categorize_api(api_path, endpoint)

                # 提取模块名
                module = endpoint.split('.')[0] if '.' in endpoint else 'simple_start'
                blueprint = endpoint.split('.')[0] if '.' in endpoint else None

                # 自动描述
                description = self._generate_description(api_path, endpoint, methods)

                # 自动判断是否需要认证
                require_auth = 1 if '/api/' in api_path else 0
                require_admin = 1 if '/admin' in api_path or 'super_admin' in endpoint else 0

                # 插入或更新
                cursor.execute('''
                    INSERT INTO apis (api_name, api_path, endpoint, methods, category, description,
                                     module, blueprint, is_enabled, is_active, require_auth, require_admin,
                                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)
                    ON CONFLICT(api_path) DO UPDATE SET
                        methods=excluded.methods,
                        endpoint=excluded.endpoint,
                        category=excluded.category,
                        description=excluded.description,
                        updated_at=excluded.updated_at
                ''', (endpoint, api_path, endpoint, methods, category, description,
                      module, blueprint, require_auth, require_admin,
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

            logger.info(f"API扫描完成: 新注册 {registered_count} 个, 更新 {updated_count} 个")
            return {
                'registered': registered_count,
                'updated': updated_count,
                'total': self.stats['total_apis']
            }
        except Exception as e:
            logger.error(f"扫描注册API失败: {e}")
            return {'error': str(e)}

    def _generate_description(self, api_path, endpoint, methods):
        """根据API路径生成描述"""
        # 提取最后一段作为名称
        parts = api_path.strip('/').split('/')
        last_part = parts[-1] if parts else api_path

        # 根据HTTP方法生成描述
        method_desc = {
            'GET': '获取',
            'POST': '创建/提交',
            'PUT': '更新',
            'DELETE': '删除',
            'PATCH': '修改'
        }

        # 根据路径关键词生成描述
        if 'login' in api_path.lower():
            return '用户登录接口'
        elif 'logout' in api_path.lower():
            return '用户登出接口'
        elif 'register' in api_path.lower():
            return '用户注册接口'
        elif 'status' in api_path.lower():
            return '获取状态信息'
        elif 'list' in api_path.lower():
            return '获取列表数据'
        elif 'create' in api_path.lower():
            return '创建新资源'
        elif 'delete' in api_path.lower():
            return '删除资源'
        elif 'update' in api_path.lower():
            return '更新资源'
        elif 'search' in api_path.lower():
            return '搜索查询'
        elif 'export' in api_path.lower():
            return '导出数据'
        elif 'import' in api_path.lower():
            return '导入数据'
        elif 'dashboard' in api_path.lower():
            return '仪表板页面'
        else:
            action = method_desc.get(methods.split(',')[0], '访问') if methods else '访问'
            return f'{action} {last_part}'

    def _update_stats(self):
        """更新统计数据"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM apis')
            self.stats['total_apis'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM apis WHERE is_enabled = 1')
            self.stats['enabled_apis'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM apis WHERE is_enabled = 0')
            self.stats['disabled_apis'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM api_call_logs')
            self.stats['total_calls'] = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            logger.error(f"更新统计失败: {e}")

    def enable_api(self, api_id):
        """启用API"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE apis SET is_enabled = 1, is_active = 1, updated_at = ? WHERE id = ?',
                           (datetime.now().isoformat(), api_id))
            conn.commit()
            conn.close()
            self._update_stats()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"启用API失败: {e}")
            return False

    def disable_api(self, api_id):
        """禁用API"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE apis SET is_enabled = 0, is_active = 0, updated_at = ? WHERE id = ?',
                           (datetime.now().isoformat(), api_id))
            conn.commit()
            conn.close()
            self._update_stats()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"禁用API失败: {e}")
            return False

    def enable_all_apis(self):
        """启用所有API"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE apis SET is_enabled = 1, is_active = 1, updated_at = ?',
                           (datetime.now().isoformat(),))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            self._update_stats()
            return count
        except Exception as e:
            logger.error(f"启用所有API失败: {e}")
            return 0

    def get_status(self):
        """获取API数据库状态"""
        self._update_stats()
        return {
            **self.stats,
            'total_groups': self.stats['total_groups'],
            'initialized': self._initialized,
            'database_path': API_MANAGEMENT_DB
        }

    def get_apis_list(self, category=None, enabled_only=False):
        """获取API列表"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()

            query = 'SELECT * FROM apis'
            conditions = []
            params = []

            if category:
                conditions.append('category = ?')
                params.append(category)
            if enabled_only:
                conditions.append('is_enabled = 1')

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY category, api_path'
            cursor.execute(query, params)
            apis = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return apis
        except Exception as e:
            logger.error(f"获取API列表失败: {e}")
            return []

    def get_api_groups(self):
        """获取API分组"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.*, COUNT(a.id) as api_count
                FROM api_groups g
                LEFT JOIN apis a ON a.category = g.group_name
                WHERE g.is_enabled = 1
                GROUP BY g.id
                ORDER BY g.id
            ''')
            groups = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return groups
        except Exception as e:
            logger.error(f"获取API分组失败: {e}")
            return []

    def get_category_stats(self):
        """获取分类统计"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, COUNT(*) as count,
                       SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled,
                       SUM(total_calls) as total_calls
                FROM apis
                GROUP BY category
                ORDER BY count DESC
            ''')
            stats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"获取分类统计失败: {e}")
            return []

    def log_api_call(self, api_id, api_path, method, status_code, response_time,
                     user_id=None, ip_address=None, error_message=None):
        """记录API调用日志"""
        try:
            conn = get_api_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO api_call_logs
                (api_id, api_path, method, user_id, status_code, response_time,
                 ip_address, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (api_id, api_path, method, user_id, status_code, response_time,
                  ip_address, error_message, datetime.now().isoformat()))

            # 更新API统计
            if api_id:
                success = 1 if status_code and 200 <= status_code < 400 else 0
                cursor.execute('''
                    UPDATE apis SET
                        total_calls = total_calls + 1,
                        successful_calls = successful_calls + ?,
                        failed_calls = failed_calls + ?,
                        avg_response_time = (avg_response_time * (total_calls - 1) + ?) / total_calls,
                        last_called = ?
                    WHERE id = ?
                ''', (success, 1 - success, response_time, datetime.now().isoformat(), api_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录API调用日志失败: {e}")


# 全局管理器实例
ai_api_db_manager = AIApiDatabaseManager()


def init_api_db_manager():
    """初始化API数据库管理器"""
    return ai_api_db_manager.initialize()


def scan_and_register_apis(app):
    """扫描并注册所有API"""
    return ai_api_db_manager.scan_and_register_apis(app)


def get_api_db_status():
    """获取API数据库状态"""
    return ai_api_db_manager.get_status()


def get_api_db_apis_list(category=None, enabled_only=False):
    """获取API列表"""
    return ai_api_db_manager.get_apis_list(category, enabled_only)


def enable_api_in_db(api_id):
    """启用API"""
    return ai_api_db_manager.enable_api(api_id)


def disable_api_in_db(api_id):
    """禁用API"""
    return ai_api_db_manager.disable_api(api_id)


def enable_all_apis_in_db():
    """启用所有API"""
    return ai_api_db_manager.enable_all_apis()


if __name__ == "__main__":
    init_api_db_manager()
    status = get_api_db_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
