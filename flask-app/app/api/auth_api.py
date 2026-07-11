# -*- coding: utf-8 -*-
"""认证API - 处理登录、注册等认证请求"""
from flask import Blueprint, request, session
import sqlite3
import os
import hashlib
import base64
from typing import Optional
from app.utils.session_manager import get_session_manager
from app.utils.role_router import get_role_router
from app.utils.api_response import (
    success_response,
    validation_error,
    authentication_error,
    business_error,
    system_error
)
from app.exceptions import AuthenticationException, ValidationException, BusinessException

auth_api = Blueprint('auth_api', __name__)

DATABASE_PATH_LEGACY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'app.db'
)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH_LEGACY)
    conn.row_factory = sqlite3.Row
    return conn

def verify_password(stored_password: str, provided_password: str) -> bool:
    """验证密码 - 支持PBKDF2和SHA-256哈希"""
    try:
        stored_bytes = base64.b64decode(stored_password)
        
        if len(stored_bytes) == 32:
            provided_hash = hashlib.sha256(provided_password.encode()).digest()
            return stored_bytes == provided_hash
        
        if len(stored_bytes) > 32:
            salt = stored_bytes[:16]
            stored_hash = stored_bytes[16:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
            return stored_hash == provided_hash
            
    except Exception:
        pass
    
    return stored_password == provided_password

@auth_api.route('/api/auth/login', methods=['POST'])
def login():
    """处理登录请求"""
    conn = None
    try:
        data = request.get_json() or request.form
        
        if not data:
            raise ValidationException(message='请求数据为空')
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            raise ValidationException(message='用户名或密码不能为空')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            raise AuthenticationException(message='用户名或密码错误')
        
        stored_password = user['password']
        
        if verify_password(stored_password, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            sm = get_session_manager()
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
            sm.create_session(user['id'], user['username'], user['role'], ip_address, user_agent)
            
            router = get_role_router()
            redirect_path = router.get_redirect_path(user['role'])
            role_info = router.get_role_info(user['role'])
            
            return success_response(data={
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'role_name': role_info['name'],
                    'role_description': role_info['description']
                },
                'redirect': redirect_path,
                'sidebar_items': role_info['sidebar_items']
            }, message='登录成功')
        else:
            raise AuthenticationException(message='用户名或密码错误')
            
    except ValidationException as e:
        return validation_error(e.message)
    except AuthenticationException as e:
        return authentication_error(e.message)
    except Exception as e:
        return system_error(f'登录失败: {str(e)}')
    finally:
        if conn:
            conn.close()

@auth_api.route('/api/auth/logout', methods=['POST'])
def logout():
    """处理登出请求"""
    try:
        session.clear()
        return success_response(message='登出成功')
    except Exception as e:
        return system_error(f'登出失败: {str(e)}')

@auth_api.route('/api/auth/register', methods=['POST'])
def register():
    """处理注册请求"""
    conn = None
    try:
        data = request.get_json() or request.form
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        
        if not username or not password:
            raise ValidationException(message='用户名和密码不能为空')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            raise BusinessException(message='用户名已存在')
        
        cursor.execute("""
            INSERT INTO users (username, password, email, role) 
            VALUES (?, ?, ?, 'user')
        """, (username, f'pbkdf2:sha256:260000${username}${password}', email))
        
        conn.commit()
        
        return success_response(message='注册成功', code=201)
        
    except ValidationException as e:
        return validation_error(e.message)
    except BusinessException as e:
        return business_error(e.message)
    except Exception as e:
        return system_error(f'注册失败: {str(e)}')
    finally:
        if conn:
            conn.close()

@auth_api.route('/api/auth/user', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    if 'user_id' in session:
        return success_response(data={
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        })
    else:
        return authentication_error('未登录')