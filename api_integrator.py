#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API整合系统 - 强化优化所有API"""

import os
# JSON support removed - using database
import sqlite3
import logging
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_integrator')

class APIIntegrator:
    def __init__(self):
        self.db_path = 'app.db'
        self.api_registry = {}
        self.rate_limits = {}
        self.init_api_database()
        self.load_api_config()
    
    def init_api_database(self):
        """初始化API数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS api_endpoints')
        cursor.execute('DROP TABLE IF EXISTS api_versions')
        cursor.execute('DROP TABLE IF EXISTS api_access_logs')
        cursor.execute('DROP TABLE IF EXISTS api_metrics')
        cursor.execute('DROP TABLE IF EXISTS api_keys')
        
        cursor.execute('''
            CREATE TABLE api_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id TEXT UNIQUE NOT NULL,
                path TEXT UNIQUE NOT NULL,
                method TEXT,
                version TEXT DEFAULT 'v1',
                handler TEXT,
                description TEXT,
                requires_auth INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 100,
                status TEXT DEFAULT 'active',
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE api_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                release_date TEXT,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE api_access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                endpoint_id TEXT,
                path TEXT,
                method TEXT,
                user_id TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                timestamp TEXT,
                ip_address TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id TEXT,
                metric_type TEXT,
                value REAL,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                user_id TEXT,
                name TEXT,
                permissions TEXT,
                expires_at TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("API数据库初始化完成")
    
    def load_api_config(self):
        """加载API配置"""
        self.api_registry = {
            # 认证API
            'auth_login': {
                'endpoint_id': 'auth_login',
                'path': '/api/auth/login',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AuthController.login',
                'description': '用户登录',
                'requires_auth': 0,
                'rate_limit': 50
            },
            'auth_logout': {
                'endpoint_id': 'auth_logout',
                'path': '/api/auth/logout',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AuthController.logout',
                'description': '用户登出',
                'requires_auth': 1,
                'rate_limit': 100
            },
            'auth_refresh': {
                'endpoint_id': 'auth_refresh',
                'path': '/api/auth/refresh',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AuthController.refresh',
                'description': '刷新Token',
                'requires_auth': 1,
                'rate_limit': 50
            },
            
            # 用户API
            'users_list': {
                'endpoint_id': 'users_list',
                'path': '/api/users',
                'method': 'GET',
                'version': 'v1',
                'handler': 'UserController.index',
                'description': '获取用户列表',
                'requires_auth': 1,
                'rate_limit': 100
            },
            'users_create': {
                'endpoint_id': 'users_create',
                'path': '/api/users',
                'method': 'POST',
                'version': 'v1',
                'handler': 'UserController.create',
                'description': '创建用户',
                'requires_auth': 1,
                'rate_limit': 50
            },
            'users_get': {
                'endpoint_id': 'users_get',
                'path': '/api/users/{id}',
                'method': 'GET',
                'version': 'v1',
                'handler': 'UserController.show',
                'description': '获取用户详情',
                'requires_auth': 1,
                'rate_limit': 200
            },
            'users_update': {
                'endpoint_id': 'users_update',
                'path': '/api/users/{id}',
                'method': 'PUT',
                'version': 'v1',
                'handler': 'UserController.update',
                'description': '更新用户',
                'requires_auth': 1,
                'rate_limit': 50
            },
            
            # 评估API
            'assessments_list': {
                'endpoint_id': 'assessments_list',
                'path': '/api/assessments',
                'method': 'GET',
                'version': 'v1',
                'handler': 'AssessmentController.index',
                'description': '获取评估列表',
                'requires_auth': 1,
                'rate_limit': 100
            },
            'assessments_create': {
                'endpoint_id': 'assessments_create',
                'path': '/api/assessments',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AssessmentController.create',
                'description': '创建评估',
                'requires_auth': 1,
                'rate_limit': 50
            },
            'assessments_take': {
                'endpoint_id': 'assessments_take',
                'path': '/api/assessments/{id}/take',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AssessmentController.take',
                'description': '参加评估',
                'requires_auth': 1,
                'rate_limit': 20
            },
            
            # 题库API
            'questions_list': {
                'endpoint_id': 'questions_list',
                'path': '/api/questions',
                'method': 'GET',
                'version': 'v1',
                'handler': 'QuestionController.index',
                'description': '获取题目列表',
                'requires_auth': 1,
                'rate_limit': 200
            },
            'questions_create': {
                'endpoint_id': 'questions_create',
                'path': '/api/questions',
                'method': 'POST',
                'version': 'v1',
                'handler': 'QuestionController.create',
                'description': '创建题目',
                'requires_auth': 1,
                'rate_limit': 50
            },
            
            # AI API
            'ai_experts': {
                'endpoint_id': 'ai_experts',
                'path': '/api/ai/experts',
                'method': 'GET',
                'version': 'v1',
                'handler': 'AIController.experts',
                'description': '获取AI专家列表',
                'requires_auth': 1,
                'rate_limit': 100
            },
            'ai_enhance': {
                'endpoint_id': 'ai_enhance',
                'path': '/api/ai/enhance',
                'method': 'POST',
                'version': 'v1',
                'handler': 'AIController.enhance',
                'description': '增强AI能力',
                'requires_auth': 1,
                'rate_limit': 10
            },
            
            # 系统API
            'system_health': {
                'endpoint_id': 'system_health',
                'path': '/api/system/health',
                'method': 'GET',
                'version': 'v1',
                'handler': 'SystemController.health',
                'description': '健康检查',
                'requires_auth': 0,
                'rate_limit': 1000
            },
            'system_stats': {
                'endpoint_id': 'system_stats',
                'path': '/api/system/stats',
                'method': 'GET',
                'version': 'v1',
                'handler': 'SystemController.stats',
                'description': '系统统计',
                'requires_auth': 1,
                'rate_limit': 50
            }
        }
        
        self.register_all_endpoints()
        self.register_api_versions()
    
    def register_all_endpoints(self):
        """注册所有API端点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for endpoint_id, config in self.api_registry.items():
            cursor.execute('''
                INSERT OR REPLACE INTO api_endpoints
                (endpoint_id, path, method, version, handler, description, 
                 requires_auth, rate_limit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint_id,
                config['path'],
                config['method'],
                config['version'],
                config['handler'],
                config['description'],
                config['requires_auth'],
                config['rate_limit'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        logger.info("所有API端点已注册")
    
    def register_api_versions(self):
        """注册API版本"""
        versions = [
            {'version': 'v1', 'status': 'active', 'release_date': '2026-04-01', 'description': '初始版本'},
            {'version': 'v2', 'status': 'beta', 'release_date': '2026-04-15', 'description': '测试版本'}
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for version in versions:
            cursor.execute('''
                INSERT OR REPLACE INTO api_versions
                (version, status, release_date, description)
                VALUES (?, ?, ?, ?)
            ''', (version['version'], version['status'], version['release_date'], version['description']))
        
        conn.commit()
        conn.close()
    
    def generate_api_key(self, user_id: str, name: str = 'default') -> str:
        """生成API密钥"""
        api_key = hashlib.sha256(f"{user_id}{int(time.time())}{os.urandom(16)}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys
            (api_key, user_id, name, permissions, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            api_key,
            user_id,
            name,
            str(['read', 'write']),
            (datetime.now() + timedelta(days=365)).isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Dict:
        """验证API密钥"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, permissions, expires_at, status 
            FROM api_keys WHERE api_key = ?
        ''', (api_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'valid': False, 'reason': 'invalid_key'}
        
        user_id, permissions, expires_at, status = result
        
        if status != 'active':
            return {'valid': False, 'reason': 'key_inactive'}
        
        if datetime.now() > datetime.fromisoformat(expires_at):
            return {'valid': False, 'reason': 'key_expired'}
        
        return {'valid': True, 'user_id': user_id, 'permissions': permissions}
    
    def check_rate_limit(self, endpoint_id: str, client_id: str) -> bool:
        """检查速率限制"""
        endpoint = self.api_registry.get(endpoint_id)
        if not endpoint:
            return True
        
        limit = endpoint['rate_limit']
        key = f"{endpoint_id}:{client_id}"
        
        now = time.time()
        if key not in self.rate_limits:
            self.rate_limits[key] = {'count': 0, 'window_start': now}
        
        window = self.rate_limits[key]
        
        # 每分钟窗口
        if now - window['window_start'] > 60:
            window['count'] = 0
            window['window_start'] = now
        
        if window['count'] >= limit:
            return False
        
        window['count'] += 1
        return True
    
    def log_api_access(self, request_id: str, endpoint_id: str, path: str, method: str, 
                      user_id: str = None, status_code: int = 200, response_time_ms: float = 0,
                      ip_address: str = None):
        """记录API访问日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_access_logs
            (request_id, endpoint_id, path, method, user_id, status_code, response_time_ms, timestamp, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_id, endpoint_id, path, method, user_id, status_code,
            response_time_ms, datetime.now().isoformat(), ip_address
        ))
        
        conn.commit()
        conn.close()
    
    def process_request(self, request: Dict) -> Dict:
        """处理API请求"""
        request_id = self.generate_request_id()
        path = request.get('path', '')
        method = request.get('method', 'GET')
        api_key = request.get('headers', {}).get('X-API-Key', '')
        ip_address = request.get('client_ip', 'unknown')
        
        # 查找端点
        endpoint = self.find_endpoint(path, method)
        
        if not endpoint:
            return {'status': 'error', 'status_code': 404, 'message': '端点不存在'}
        
        # 检查速率限制
        if not self.check_rate_limit(endpoint['endpoint_id'], ip_address):
            return {'status': 'error', 'status_code': 429, 'message': '请求过于频繁'}
        
        # 检查认证
        if endpoint['requires_auth']:
            if not api_key:
                return {'status': 'error', 'status_code': 401, 'message': '需要认证'}
            
            key_valid = self.validate_api_key(api_key)
            if not key_valid['valid']:
                return {'status': 'error', 'status_code': 403, 'message': '认证失败'}
            
            user_id = key_valid['user_id']
        else:
            user_id = None
        
        # 模拟处理
        start_time = time.time()
        time.sleep(0.01)  # 模拟处理时间
        response_time_ms = (time.time() - start_time) * 1000
        
        # 记录日志
        self.log_api_access(request_id, endpoint['endpoint_id'], path, method, user_id, 200, response_time_ms, ip_address)
        
        return {
            'status': 'success',
            'status_code': 200,
            'request_id': request_id,
            'endpoint': endpoint['description'],
            'response_time_ms': response_time_ms
        }
    
    def find_endpoint(self, path: str, method: str) -> Optional[Dict]:
        """查找端点"""
        for endpoint in self.api_registry.values():
            # 简单路径匹配
            pattern = endpoint['path']
            if '{' in pattern:
                # 带参数的路径
                pattern_parts = pattern.split('/')
                path_parts = path.split('/')
                if len(pattern_parts) == len(path_parts):
                    match = True
                    for p, q in zip(pattern_parts, path_parts):
                        if p.startswith('{') and p.endswith('}'):
                            continue
                        if p != q:
                            match = False
                            break
                    if match and endpoint['method'] == method:
                        return endpoint
            else:
                if endpoint['path'] == path and endpoint['method'] == method:
                    return endpoint
        
        return None
    
    def generate_request_id(self) -> str:
        """生成请求ID"""
        return f"req_{int(time.time() * 1000)}{hashlib.md5(os.urandom(8)).hexdigest()[:6]}"
    
    def generate_api_documentation(self) -> str:
        """生成API文档"""
        docs = []
        
        for endpoint in sorted(self.api_registry.values(), key=lambda x: x['path']):
            docs.append(f"""
## {endpoint['method']} {endpoint['path']}

**ID**: {endpoint['endpoint_id']}
**版本**: {endpoint['version']}
**认证**: {'需要' if endpoint['requires_auth'] else '不需要'}
**限流**: {endpoint['rate_limit']}/分钟

### 描述
{endpoint['description']}

### 处理程序
{endpoint['handler']}
            """)
        
        return "\n".join(docs)
    
    def generate_api_report(self):
        """生成API报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM api_endpoints')
        endpoint_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM api_endpoints WHERE status = "active"')
        active_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM api_access_logs')
        access_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM api_keys WHERE status = "active"')
        key_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(response_time_ms) FROM api_access_logs')
        avg_response_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        print("\n" + "="*80)
        print("          API整合系统报告")
        print("="*80)
        
        print(f"\nAPI端点统计:")
        print(f"  端点总数: {endpoint_count}")
        print(f"  活跃端点: {active_count}")
        print(f"  访问次数: {access_count}")
        print(f"  API密钥: {key_count}")
        print(f"  平均响应时间: {avg_response_time:.2f}ms")
        
        print("\nAPI分类:")
        categories = {
            '认证': ['auth_login', 'auth_logout', 'auth_refresh'],
            '用户': ['users_list', 'users_create', 'users_get', 'users_update'],
            '评估': ['assessments_list', 'assessments_create', 'assessments_take'],
            '题库': ['questions_list', 'questions_create'],
            'AI': ['ai_experts', 'ai_enhance'],
            '系统': ['system_health', 'system_stats']
        }
        
        for category, endpoints in categories.items():
            count = len([e for e in endpoints if e in self.api_registry])
            print(f"  {category}: {count} 个端点")
        
        print("\n安全功能:")
        print(f"  ✅ API密钥认证")
        print(f"  ✅ 速率限制")
        print(f"  ✅ 端点权限控制")
        print(f"  ✅ 访问日志记录")
        print(f"  ✅ 版本控制")
        
        print("\n" + "="*80)
        print("  API整合系统完成！")
        print("="*80)
    
    def run_api_demo(self):
        """运行API演示"""
        print("="*80)
        print("          API整合系统")
        print("="*80)
        
        print("\n[1/3] 注册API端点...")
        self.register_all_endpoints()
        print(f"  ✓ 已注册 {len(self.api_registry)} 个端点")
        
        print("\n[2/3] 测试API请求...")
        
        test_requests = [
            {'method': 'GET', 'path': '/api/system/health', 'client_ip': '192.168.1.100'},
            {'method': 'POST', 'path': '/api/auth/login', 'client_ip': '192.168.1.100'},
            {'method': 'GET', 'path': '/api/users', 'client_ip': '192.168.1.100', 'headers': {'X-API-Key': 'test-key'}}
        ]
        
        for request in test_requests:
            result = self.process_request(request)
            status = '✅' if result['status'] == 'success' else '❌'
            print(f"  {status} {request['method']} {request['path']}")
            if result['status'] == 'success':
                print(f"    请求ID: {result['request_id']}")
                print(f"    响应时间: {result['response_time_ms']:.2f}ms")
        
        print("\n[3/3] 生成API报告...")
        self.generate_api_report()

def main():
    integrator = APIIntegrator()
    integrator.run_api_demo()

if __name__ == "__main__":
    main()