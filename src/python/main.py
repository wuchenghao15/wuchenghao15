"""
MTSCOS AI 智能管理系统 - Python后端服务
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from dataclasses import dataclass, field, asdict
from enum import Enum

# Flask支持（可选）
try:
    from flask import Flask, request, jsonify, g, send_file
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask未安装，运行轻量模式")


# ============================================================
# 配置管理
# ============================================================

@dataclass
class Config:
    """系统配置"""
    VERSION: str = "4.4.0"
    BUILD: str = "20260622"
    DB_PATH: str = "data/mtscos.db"
    SECRET_KEY: str = secrets.token_hex(32)
    ENCRYPTION_KEY: str = secrets.token_hex(32)
    
    # AI员工配置
    MAX_AI_EMPLOYEES: int = 100
    DEFAULT_EFFICIENCY: float = 95.0
    DEFAULT_WORKLOAD: float = 30.0
    
    # 性能配置
    CACHE_TTL: int = 300  # 5分钟
    MAX_CACHE_SIZE: int = 1000
    REQUEST_TIMEOUT: int = 30
    
    # 安全配置
    PASSWORD_MIN_LENGTH: int = 8
    SESSION_TIMEOUT: int = 3600  # 1小时
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION: int = 300  # 5分钟


config = Config()


# ============================================================
# 数据库管理器
# ============================================================

class DatabaseManager:
    """数据库管理器 - SQLite实现"""
    
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        self.db_path = db_path or config.DB_PATH
        self.db_path = os.path.join(os.path.dirname(__file__), '..', self.db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()
        self._initialized = True
        print(f"✅ 数据库初始化完成: {self.db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        self.conn.executescript('''
            -- 用户表
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                permissions TEXT DEFAULT '[]',
                security_question TEXT,
                security_answer TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                last_login INTEGER,
                login_attempts INTEGER DEFAULT 0,
                locked_until INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            );
            
            -- AI员工表
            CREATE TABLE IF NOT EXISTS ai_employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                capabilities TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                efficiency REAL DEFAULT 95.0,
                workload REAL DEFAULT 30.0,
                task_count INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            
            -- 数据记录表
            CREATE TABLE IF NOT EXISTS data_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            
            -- 同步记录表
            CREATE TABLE IF NOT EXISTS sync_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                created_at INTEGER NOT NULL,
                completed_at INTEGER
            );
            
            -- 日志表
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                context TEXT,
                created_at INTEGER NOT NULL
            );
            
            -- 系统配置表
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
            
            -- 创建索引
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_ai_employees_category ON ai_employees(category);
            CREATE INDEX IF NOT EXISTS idx_data_records_collection ON data_records(collection);
            CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
            CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at);
        ''')
        self.conn.commit()
    
    def add(self, collection: str, data: Dict[str, Any]) -> int:
        """添加数据"""
        if collection == 'users':
            return self._add_user(data)
        elif collection == 'ai_employees':
            return self._add_ai_employee(data)
        else:
            return self._add_generic(collection, data)
    
    def _add_user(self, data: Dict) -> int:
        """添加用户"""
        cursor = self.conn.execute('''
            INSERT INTO users (user_id, username, password_hash, email, role, 
                             security_question, security_answer, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('user_id', f"user_{int(time.time())}"),
            data['username'],
            data['password_hash'],
            data.get('email'),
            data.get('role', 'user'),
            data.get('security_question'),
            data.get('security_answer'),
            int(time.time()),
            int(time.time())
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def _add_ai_employee(self, data: Dict) -> int:
        """添加AI员工"""
        cursor = self.conn.execute('''
            INSERT INTO ai_employees (employee_id, name, title, description, category,
                                    capabilities, efficiency, workload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('employee_id', f"emp_{int(time.time())}"),
            data['name'],
            data['title'],
            data.get('description', ''),
            data.get('category', 'general'),
            json.dumps(data.get('capabilities', [])),
            data.get('efficiency', config.DEFAULT_EFFICIENCY),
            data.get('workload', config.DEFAULT_WORKLOAD),
            int(time.time()),
            int(time.time())
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def _add_generic(self, collection: str, data: Dict) -> int:
        """通用添加"""
        cursor = self.conn.execute('''
            INSERT INTO data_records (collection, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (collection, json.dumps(data), int(time.time()), int(time.time())))
        self.conn.commit()
        return cursor.lastrowid
    
    def get(self, collection: str, id: int) -> Optional[Dict]:
        """获取单条数据"""
        if collection == 'users':
            row = self.conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
        elif collection == 'ai_employees':
            row = self.conn.execute('SELECT * FROM ai_employees WHERE id = ?', (id,)).fetchone()
        else:
            row = self.conn.execute('SELECT * FROM data_records WHERE id = ? AND collection = ?', 
                                   (id, collection)).fetchone()
        return dict(row) if row else None
    
    def get_all(self, collection: str, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有数据"""
        if collection == 'users':
            query = 'SELECT * FROM users WHERE 1=1'
            params = []
            if filters:
                if filters.get('username'):
                    query += ' AND username = ?'
                    params.append(filters['username'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(filters['is_active'])
            query += f' LIMIT {limit} OFFSET {offset}'
            rows = self.conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        elif collection == 'ai_employees':
            query = 'SELECT * FROM ai_employees WHERE 1=1'
            params = []
            if filters:
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
            query += f' LIMIT {limit} OFFSET {offset}'
            rows = self.conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        else:
            rows = self.conn.execute(
                'SELECT * FROM data_records WHERE collection = ? LIMIT ? OFFSET ?',
                (collection, limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def update(self, collection: str, id: int, data: Dict) -> bool:
        """更新数据"""
        if collection == 'users':
            fields = ', '.join([f"{k} = ?" for k in data.keys()])
            self.conn.execute(
                f'UPDATE users SET {fields}, updated_at = ? WHERE id = ?',
                list(data.values()) + [int(time.time()), id]
            )
        elif collection == 'ai_employees':
            fields = ', '.join([f"{k} = ?" for k in data.keys()])
            self.conn.execute(
                f'UPDATE ai_employees SET {fields}, updated_at = ? WHERE id = ?',
                list(data.values()) + [int(time.time()), id]
            )
        else:
            self.conn.execute(
                'UPDATE data_records SET data = ?, updated_at = ? WHERE id = ? AND collection = ?',
                (json.dumps(data), int(time.time()), id, collection)
            )
        self.conn.commit()
        return self.conn.total_changes > 0
    
    def delete(self, collection: str, id: int) -> bool:
        """删除数据"""
        if collection == 'users':
            self.conn.execute('DELETE FROM users WHERE id = ?', (id,))
        elif collection == 'ai_employees':
            self.conn.execute('DELETE FROM ai_employees WHERE id = ?', (id,))
        else:
            self.conn.execute('DELETE FROM data_records WHERE id = ? AND collection = ?', (id, collection))
        self.conn.commit()
        return self.conn.total_changes > 0
    
    def add_log(self, level: str, message: str, context: Dict = None):
        """添加日志"""
        self.conn.execute(
            'INSERT INTO logs (level, message, context, created_at) VALUES (?, ?, ?, ?)',
            (level, message, json.dumps(context) if context else None, int(time.time()))
        )
        self.conn.commit()
    
    def get_logs(self, level: str = None, limit: int = 100) -> List[Dict]:
        """获取日志"""
        query = 'SELECT * FROM logs WHERE 1=1'
        params = []
        if level:
            query += ' AND level = ?'
            params.append(level)
        query += f' ORDER BY created_at DESC LIMIT {limit}'
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """获取数据库统计"""
        stats = {}
        for table in ['users', 'ai_employees', 'data_records', 'logs']:
            count = self.conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            stats[table] = count
        return stats


# ============================================================
# 加密工具
# ============================================================

class Encryption:
    """加密工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', 
                                       password.encode('utf-8'), 
                                       salt.encode('utf-8'), 
                                       100000)
        return f"{salt}${hash_obj.hex()}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, hash_value = password_hash.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)
            return hash_obj.hex() == hash_value
        except:
            return False
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """生成令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_data(data: str) -> str:
        """数据哈希"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


# ============================================================
# AI调度器
# ============================================================

class AIDispatcher:
    """AI员工调度器"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def dispatch_task(self, task: Dict) -> Dict:
        """分配任务到AI员工"""
        category = task.get('category', 'general')
        required_skills = task.get('required_skills', [])
        
        # 获取可用员工
        employees = self.db.get_all('ai_employees', {
            'category': category,
            'status': 'active'
        })
        
        if not employees:
            employees = self.db.get_all('ai_employees', {'status': 'active'})
        
        if not employees:
            return {'success': False, 'error': '无可用AI员工'}
        
        # 选择负载最低的员工
        best_employee = min(employees, key=lambda e: e.get('workload', 100))
        
        # 更新员工负载
        self.db.update('ai_employees', best_employee['id'], {
            'workload': min(100, best_employee.get('workload', 0) + 10),
            'task_count': best_employee.get('task_count', 0) + 1
        })
        
        return {
            'success': True,
            'employee': best_employee,
            'task_id': f"task_{int(time.time())}"
        }
    
    def get_team_stats(self) -> Dict:
        """获取团队统计"""
        employees = self.db.get_all('ai_employees')
        if not employees:
            return {'total': 0, 'avg_efficiency': 0, 'avg_workload': 0}
        
        return {
            'total': len(employees),
            'active': len([e for e in employees if e.get('status') == 'active']),
            'avg_efficiency': sum(e.get('efficiency', 0) for e in employees) / len(employees),
            'avg_workload': sum(e.get('workload', 0) for e in employees) / len(employees),
            'total_tasks': sum(e.get('task_count', 0) for e in employees)
        }


# ============================================================
# Flask应用（可选）
# ============================================================

if FLASK_AVAILABLE:
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    
    # 全局实例
    db = DatabaseManager()
    ai_dispatcher = AIDispatcher(db)
    
    # 请求日志中间件
    @app.before_request
    def log_request():
        g.start_time = time.time()
        db.add_log('info', f'{request.method} {request.path}')
    
    @app.after_request
    def log_response(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            db.add_log('info', f'{request.method} {request.path} - {response.status_code} ({duration:.2f}s)')
        return response
    
    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'ok',
            'version': config.VERSION,
            'uptime': time.time()
        })
    
    # 认证API
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        users = db.get_all('users', {'username': username})
        if not users:
            return jsonify({'success': False, 'error': '用户不存在'}), 401
        
        user = users[0]
        if not Encryption.verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': '密码错误'}), 401
        
        token = Encryption.generate_token()
        db.update('users', user['id'], {'last_login': int(time.time())})
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {k: v for k, v in user.items() if k != 'password_hash'}
        })
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if len(password) < config.PASSWORD_MIN_LENGTH:
            return jsonify({'success': False, 'error': f'密码至少{config.PASSWORD_MIN_LENGTH}位'}), 400
        
        password_hash = Encryption.hash_password(password)
        user_id = db.add('users', {
            'username': username,
            'password_hash': password_hash,
            'email': data.get('email'),
            'security_question': data.get('security_question'),
            'security_answer': data.get('security_answer')
        })
        
        return jsonify({'success': True, 'user_id': user_id})
    
    # 用户API
    @app.route('/api/users')
    def get_users():
        users = db.get_all('users')
        return jsonify([{k: v for k, v in u.items() if k != 'password_hash'} for u in users])
    
    @app.route('/api/users/<int:user_id>')
    def get_user(user_id):
        user = db.get('users', user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        return jsonify({k: v for k, v in user.items() if k != 'password_hash'})
    
    # AI员工API
    @app.route('/api/ai/employees')
    def get_employees():
        employees = db.get_all('ai_employees')
        return jsonify(employees)
    
    @app.route('/api/ai/employees', methods=['POST'])
    def add_employee():
        data = request.get_json()
        employee_id = db.add('ai_employees', data)
        return jsonify({'success': True, 'employee_id': employee_id})
    
    @app.route('/api/ai/dispatch', methods=['POST'])
    def dispatch():
        task = request.get_json()
        result = ai_dispatcher.dispatch_task(task)
        return jsonify(result)
    
    @app.route('/api/ai/team-stats')
    def team_stats():
        return jsonify(ai_dispatcher.get_team_stats())
    
    # 数据API
    @app.route('/api/data/<collection>')
    def get_data(collection):
        data = db.get_all(collection)
        return jsonify(data)
    
    @app.route('/api/data/<collection>', methods=['POST'])
    def add_data(collection):
        data = request.get_json()
        record_id = db.add(collection, data)
        return jsonify({'success': True, 'id': record_id})
    
    @app.route('/api/data/<collection>/<int:record_id>', methods=['PUT'])
    def update_data(collection, record_id):
        data = request.get_json()
        success = db.update(collection, record_id, data)
        return jsonify({'success': success})
    
    @app.route('/api/data/<collection>/<int:record_id>', methods=['DELETE'])
    def delete_data(collection, record_id):
        success = db.delete(collection, record_id)
        return jsonify({'success': success})
    
    # 日志API
    @app.route('/api/logs')
    def get_logs():
        level = request.args.get('level')
        limit = int(request.args.get('limit', 100))
        logs = db.get_logs(level, limit)
        return jsonify(logs)
    
    # 统计API
    @app.route('/api/stats')
    def get_stats():
        return jsonify(db.get_stats())


# ============================================================
# 主程序
# ============================================================

def run_standalone_server(port: int = 5000):
    """运行独立服务器（无Flask）"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           MTSCOS AI 智能管理系统 - Python后端             ║
╠══════════════════════════════════════════════════════════╣
║  版本: {config.VERSION:<50}  ║
║  构建: {config.BUILD:<50}  ║
║  数据库: {config.DB_PATH:<47}  ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    db = DatabaseManager()
    
    # 初始化示例数据
    existing = db.get_all('ai_employees')
    if not existing:
        print("📝 初始化示例AI员工...")
        sample_employees = [
            {'name': '系统架构师', 'title': '首席架构师', 'category': 'core', 'description': '系统架构设计专家'},
            {'name': 'AI团队协调总监', 'title': '协调总监', 'category': 'core', 'description': 'AI团队协作管理'},
            {'name': '安全专家', 'title': '安全工程师', 'category': 'security', 'description': '系统安全专家'},
            {'name': '数据分析师', 'title': '数据专家', 'category': 'data', 'description': '数据分析专家'},
        ]
        for emp in sample_employees:
            emp['employee_id'] = f"emp_{int(time.time())}_{emp['name']}"
            db.add('ai_employees', emp)
        print(f"✅ 已添加 {len(sample_employees)} 个示例AI员工")
    else:
        print(f"📊 已有 {len(existing)} 个AI员工")
    
    print("✅ 系统就绪！")
    print(f"📌 提示: 安装Flask后运行 'python main.py --flask' 启用完整API服务")
    
    # 简单的命令行交互
    while True:
        try:
            cmd = input("\n命令> ").strip()
            if cmd == 'help':
                print("""
可用命令:
  stats      - 显示系统统计
  employees  - 显示AI员工列表
  logs       - 显示最近日志
  exit      - 退出程序
  help      - 显示帮助
                """)
            elif cmd == 'stats':
                print(json.dumps(db.get_stats(), indent=2))
            elif cmd == 'employees':
                for emp in db.get_all('ai_employees'):
                    print(f"  [{emp['id']}] {emp['name']} - {emp['title']}")
            elif cmd == 'logs':
                for log in db.get_logs(limit=10):
                    print(f"  [{log['level']}] {log['message'][:60]}")
            elif cmd == 'exit':
                print("👋 再见！")
                break
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MTSCOS AI 智能管理系统')
    parser.add_argument('--flask', action='store_true', help='启用Flask API服务')
    parser.add_argument('--port', type=int, default=5000, help='服务端口')
    args = parser.parse_args()
    
    if args.flask and FLASK_AVAILABLE:
        print(f"🚀 启动Flask服务: http://0.0.0.0:{args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=True)
    else:
        run_standalone_server()
