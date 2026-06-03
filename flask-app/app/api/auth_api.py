# -*- coding: utf-8 -*-
"""认证API - 处理登录、注册等认证请求"""
from flask import Blueprint, request, jsonify, session, current_app
import sqlite3
import os
import json

auth_api = Blueprint('auth_api', __name__)

def get_db_connection():
    """获取数据库连接"""
    # 使用绝对路径指向flask-app目录下的app.db
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@auth_api.route('/api/login', methods=['POST'])
def login():
    """处理登录请求"""
    try:
        data = request.get_json() or request.form
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名或密码不能为空'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 验证密码(简化验证)
        stored_password = user['password']
        
        # 简单密码验证
        if stored_password.endswith(password):
            # 登录成功
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@auth_api.route('/api/logout', methods=['POST'])
def logout():
    """处理登出请求"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'登出失败: {str(e)}'}), 500

@auth_api.route('/api/register', methods=['POST'])
def register():
    """处理注册请求"""
    try:
        data = request.get_json() or request.form
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return jsonify({'success': False, 'message': '用户名已存在'}), 409
        
        # 创建用户(简化密码存储)
        cursor.execute("""
            INSERT INTO users (username, password, email, role) 
            VALUES (?, ?, ?, 'user')
        """, (username, f'pbkdf2:sha256:260000${username}${password}', email))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': '注册成功'}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@auth_api.route('/api/user', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'role': session['role']
            }
        })
    else:
        return jsonify({'success': False, 'message': '未登录'}), 401
