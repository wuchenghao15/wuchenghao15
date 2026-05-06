# -*- coding: utf-8 -*-
# MTSCOS AI Project - User Management Server
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import os
import jwt
import hashlib
import secrets
import re
import time
import functools

# 导入配置
from config import Config

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={"/*": {"origins": "*"}})  # 允许跨域请求

# 数据库初始化
def init_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            super_admin_approved INTEGER DEFAULT 0,
            hardware_admin_approved INTEGER DEFAULT 0,
            avatar TEXT DEFAULT NULL
        )
    ''')

    # 创建API密钥表
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ''')

    # 创建访问日志表
        CREATE TABLE IF NOT EXISTS access_logs (
            ip_address TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            request_time TEXT DEFAULT CURRENT_TIMESTAMP,
            response_time REAL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# 初始化数据库

# 工具函数
def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_jwt(user_id, username, role):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def verify_jwt(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_api_key():
    """生成API密钥"""
    return secrets.token_hex(32)

# 速率限制存储
rate_limit_store = {}
# 速率限制装饰器
def rate_limit(func):
    """速率限制装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not app.config['RATE_LIMIT_ENABLED']:
            return func(*args, **kwargs)

        ip = request.remote_addr
        current_time = time.time()

        # 初始化速率限制数据
        if ip not in rate_limit_store:
            rate_limit_store[ip] = {
                'requests': [],
                'last_cleanup': current_time
            }

        # 清理旧的请求记录
        cleanup_time = current_time - 3600  # 保留1小时内的请求
        rate_limit_store[ip]['requests'] = [r for r in rate_limit_store[ip]['requests'] if r > cleanup_time]

        # 检查每分钟限制
        minute_ago = current_time - 60
        minute_requests = [r for r in rate_limit_store[ip]['requests'] if r > minute_ago]
        if len(minute_requests) >= app.config['RATE_LIMIT_PER_MINUTE']:
            return jsonify({'success': False, 'message': '请求过于频繁，请稍后再试'}), 429

        # 检查每小时限制
        if len(rate_limit_store[ip]['requests']) >= app.config['RATE_LIMIT_PER_HOUR']:
            return jsonify({'success': False, 'message': '请求过于频繁，请稍后再试'}), 429

        # 记录当前请求
        rate_limit_store[ip]['requests'].append(current_time)

        return func(*args, **kwargs)
    return wrapper

# IP白名单装饰器
    """IP白名单装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not app.config['IP_WHITELIST_ENABLED']:

        ip = request.remote_addr
        if ip not in app.config['IP_WHITELIST']:
            return jsonify({'success': False, 'message': 'IP地址不在允许列表中'}), 403

    return wrapper
# 访问日志装饰器
def log_access(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        # 获取请求信息
        endpoint = request.path
        method = request.method

        response = func(*args, **kwargs)


        # 保存日志到数据库
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor.execute('''
            VALUES (?, ?, ?, ?, ?)
        conn.commit()
        conn.close()

        return response
    return wrapper

# API密钥验证装饰器
def require_api_key(func):
    """验证API密钥"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
            return jsonify({'success': False, 'message': 'API密钥缺失'}), 401
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor.execute('''
            SELECT id FROM api_keys WHERE key = ? AND is_active = 1 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        key = cursor.fetchone()
        conn.close()
        if not key:
            return jsonify({'success': False, 'message': '无效的API密钥'}), 401

        return func(*args, **kwargs)

# 路由 - API密钥管理
@app.route('/api/keys', methods=['POST'])
@ip_whitelist
    """创建API密钥"""
    description = request.json.get('description', '')
    expires_at = request.json.get('expires_at')
    api_key = generate_api_key()

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('''
        INSERT INTO api_keys (key, description, expires_at)
        VALUES (?, ?, ?)
    conn.commit()
    conn.close()


@app.route('/api/keys', methods=['GET'])
@rate_limit
@ip_whitelist
    """获取所有API密钥"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('SELECT id, key, description, is_active, created_at, expires_at FROM api_keys')
    keys = cursor.fetchall()
    conn.close()

# 路由 - 用户管理
@app.route('/api/users', methods=['POST'])
@log_access
@rate_limit
def create_user():
    """创建用户"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    # 验证输入
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': '用户名长度必须在3-20个字符之间'}), 400
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return jsonify({'success': False, 'message': '用户名必须以字母开头，只能包含字母、数字、下划线和连字符'}), 400

    # 邮箱验证
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'success': False, 'message': '请输入有效的邮箱地址'}), 400

    # 密码验证
    if len(password) < 8:
        return jsonify({'success': False, 'message': '密码长度不能少于8个字符'}), 400

    # 检查用户名是否已存在
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    hashed_password = hash_password(password)
    cursor.execute('''
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, ?)
    ''', (username, email, hashed_password, role))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'user_id': user_id, 'username': username})

@app.route('/api/users/<int:user_id>', methods=['GET'])
@log_access
@rate_limit
@ip_whitelist
def get_user(user_id):
    """获取用户信息"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    return jsonify({
        'success': True,
        'user': {
            'id': user[0],
            'email': user[2],
            'role': user[3],
            'is_active': user[4],
        }
    })

@app.route('/api/users', methods=['GET'])
@require_api_key
@log_access
@rate_limit
@ip_whitelist
def get_all_users():
    """获取所有用户"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    return jsonify({
        'success': True,
        'users': [
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'is_active': user[4],
                'created_at': user[5]
            }
            for user in users
        ]

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_api_key
@log_access
@rate_limit
@ip_whitelist
def update_user(user_id):
    """更新用户信息"""
    data = request.json
    conn = sqlite3.connect(Config.DATABASE_PATH)

    # 检查用户是否存在
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 更新用户信息
    update_values = []

    if 'username' in data:
        update_fields.append('username = ?')
        update_values.append(data['username'])
    if 'email' in data:
        update_fields.append('email = ?')
        update_values.append(data['email'])
    if 'password' in data:
        update_fields.append('password = ?')
    if 'role' in data:
        update_fields.append('role = ?')
        update_values.append(data['role'])
    if 'is_active' in data:
        update_fields.append('is_active = ?')
        update_values.append(data['is_active'])
    if 'avatar' in data:
        update_fields.append('avatar = ?')
        update_values.append(data['avatar'])

    if update_fields:
        update_query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        update_values.append(user_id)
        cursor.execute(update_query, update_values)
        conn.commit()

    return jsonify({'success': True, 'message': '用户信息更新成功'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@log_access
@ip_whitelist
    """删除用户"""

    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 删除用户
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.close()
    return jsonify({'success': True, 'message': '用户删除成功'})

# 路由 - 认证
@app.route('/api/auth/login', methods=['POST'])
@log_access
@ip_whitelist
def login():
    """用户登录"""
    username = data.get('username')

    if not all([username, password]):
        return jsonify({'success': False, 'message': '缺少用户名或密码'}), 400

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor.execute('SELECT id, username, password, role, is_active FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    if hash_password(password) != user[2]:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    # 生成JWT令牌
    token = generate_jwt(user[0], user[1], user[3])

    return jsonify({
        'success': True,
        'user': {
            'id': user[0],
            'username': user[1],
            'role': user[3]
        }
    })

@app.route('/api/auth/verify', methods=['POST'])
@log_access
@ip_whitelist
def verify_token():
    """验证JWT令牌"""
    token = request.json.get('token')
    if not token:
        return jsonify({'success': False, 'message': '缺少令牌'}), 400

    payload = verify_jwt(token)
    if not payload:
        return jsonify({'success': False, 'message': '无效或过期的令牌'}), 401

        'success': True,
        'user': {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }

@app.route('/health', methods=['GET'])
@ip_whitelist
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'User Management Server'})

# 安全头中间件
@app.after_request
def add_secure_headers(response):
    """添加安全头"""
    for header, value in app.config['SECURE_HEADERS'].items():
    return response

    if app.config['HTTPS_ENABLED']:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,  # 生产环境关闭调试模式
            ssl_context=(app.config['SSL_CERT_PATH'], app.config['SSL_KEY_PATH'])
        )
    else:
        # 使用HTTP运行
            host='0.0.0.0',
            port=5001,
            debug=app.config['DEBUG']
