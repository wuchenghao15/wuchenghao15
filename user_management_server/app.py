# -*- coding: utf-8 -*-
"""MTSCOS AI Project - User Management Server"""

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

try:
    from config import Config
except ImportError:
    print("Warning: config.py not found, using default config")
    class Config:
        DATABASE_PATH = 'users.db'
        SECRET_KEY = 'default-secret-key'
        JWT_EXPIRATION = 3600
        RATE_LIMIT_ENABLED = False
        RATE_LIMIT_PER_MINUTE = 60
        RATE_LIMIT_PER_HOUR = 1000
        IP_WHITELIST_ENABLED = False
        IP_WHITELIST = []
        DEBUG = False
        HTTPS_ENABLED = False
        SSL_CERT_PATH = None
        SSL_KEY_PATH = None
        SECURE_HEADERS = {}

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={"/*": {"origins": "*"}})

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT DEFAULT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            method TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            request_time TEXT DEFAULT CURRENT_TIMESTAMP,
            response_time REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_jwt(user_id, username, role):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

def verify_jwt(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def generate_api_key():
    """Generate API key"""
    return secrets.token_hex(32)

rate_limit_store = {}

def rate_limit(func):
    """Rate limit decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not app.config.get('RATE_LIMIT_ENABLED', False):
            return func(*args, **kwargs)
        
        ip = request.remote_addr
        current_time = time.time()
        
        if ip not in rate_limit_store:
            rate_limit_store[ip] = {'requests': [], 'last_cleanup': current_time}
        
        cleanup_time = current_time - 3600
        rate_limit_store[ip]['requests'] = [r for r in rate_limit_store[ip]['requests'] if r > cleanup_time]
        
        minute_ago = current_time - 60
        minute_requests = [r for r in rate_limit_store[ip]['requests'] if r > minute_ago]
        if len(minute_requests) >= app.config.get('RATE_LIMIT_PER_MINUTE', 60):
            return jsonify({'success': False, 'message': 'Rate limit exceeded'}), 429
        
        if len(rate_limit_store[ip]['requests']) >= app.config.get('RATE_LIMIT_PER_HOUR', 1000):
            return jsonify({'success': False, 'message': 'Rate limit exceeded'}), 429
        
        rate_limit_store[ip]['requests'].append(current_time)
        return func(*args, **kwargs)
    return wrapper

def ip_whitelist(func):
    """IP whitelist decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not app.config.get('IP_WHITELIST_ENABLED', False):
            return func(*args, **kwargs)
        
        ip = request.remote_addr
        if ip not in app.config.get('IP_WHITELIST', []):
            return jsonify({'success': False, 'message': 'IP not allowed'}), 403
        
        return func(*args, **kwargs)
    return wrapper

def log_access(func):
    """Access log decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = request.path
        method = request.method
        
        response = func(*args, **kwargs)
        
        response_time = time.time() - start_time
        status_code = response[1] if isinstance(response, tuple) else 200
        
        try:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO access_logs (ip_address, method, endpoint, status_code, response_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (request.remote_addr, method, endpoint, status_code, response_time))
            conn.commit()
            conn.close()
        except Exception:
            pass
        
        return response
    return wrapper

def require_api_key(func):
    """API key verification decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'success': False, 'message': 'API key required'}), 401
        
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM api_keys WHERE key = ? AND is_active = 1 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        ''', (api_key,))
        key = cursor.fetchone()
        conn.close()
        
        if not key:
            return jsonify({'success': False, 'message': 'Invalid API key'}), 401
        
        return func(*args, **kwargs)
    return wrapper

@app.route('/api/keys', methods=['POST'])
@ip_whitelist
def create_api_key():
    """Create API key"""
    description = request.json.get('description', '')
    expires_at = request.json.get('expires_at')
    api_key = generate_api_key()
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_keys (key, description, expires_at)
        VALUES (?, ?, ?)
    ''', (api_key, description, expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'api_key': api_key})

@app.route('/api/keys', methods=['GET'])
@rate_limit
@ip_whitelist
def get_api_keys():
    """Get all API keys"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, key, description, is_active, created_at, expires_at FROM api_keys')
    keys = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'keys': [{'id': k[0], 'key': k[1], 'description': k[2], 'is_active': k[3], 'created_at': k[4], 'expires_at': k[5]} for k in keys]
    })

@app.route('/api/users', methods=['POST'])
@log_access
@rate_limit
def create_user():
    """Create user"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'message': 'Username must be 3-20 characters'}), 400
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return jsonify({'success': False, 'message': 'Invalid username format'}), 400
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
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
    """Get user info"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[3],
            'is_active': user[4],
            'created_at': user[5]
        }
    })

@app.route('/api/users', methods=['GET'])
@require_api_key
@log_access
@rate_limit
@ip_whitelist
def get_all_users():
    """Get all users"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, is_active, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'users': [
            {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'is_active': user[4],
                'created_at': user[5]
            }
            for user in users
        ]
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_api_key
@log_access
@rate_limit
@ip_whitelist
def update_user(user_id):
    """Update user info"""
    data = request.json
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    update_fields = []
    update_values = []
    
    if 'username' in data:
        update_fields.append('username = ?')
        update_values.append(data['username'])
    if 'email' in data:
        update_fields.append('email = ?')
        update_values.append(data['email'])
    if 'password' in data:
        update_fields.append('password = ?')
        update_values.append(hash_password(data['password']))
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
    
    conn.close()
    return jsonify({'success': True, 'message': 'User updated successfully'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@log_access
@ip_whitelist
def delete_user(user_id):
    """Delete user"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/auth/login', methods=['POST'])
@log_access
@ip_whitelist
def login():
    """User login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'success': False, 'message': 'Missing username or password'}), 400
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, role, is_active FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    if hash_password(password) != user[2]:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    token = generate_jwt(user[0], user[1], user[3])
    
    return jsonify({
        'success': True,
        'token': token,
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
    """Verify JWT token"""
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    payload = verify_jwt(token)
    if not payload:
        return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }
    })

@app.route('/health', methods=['GET'])
@ip_whitelist
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'User Management Server'})

@app.after_request
def add_secure_headers(response):
    """Add secure headers"""
    for header, value in app.config.get('SECURE_HEADERS', {}).items():
        response.headers[header] = value
    return response

if __name__ == '__main__':
    if app.config.get('HTTPS_ENABLED'):
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            ssl_context=(app.config['SSL_CERT_PATH'], app.config['SSL_KEY_PATH'])
        )
    else:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=app.config.get('DEBUG', False)
        )
