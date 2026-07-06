# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, session
import sqlite3
import os
import hashlib
import base64
import time
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

def verify_password(stored_password, provided_password):
    """验证密码"""
    try:
        stored_bytes = base64.b64decode(stored_password)
        if len(stored_bytes) == 32:
            provided_hash = hashlib.sha256(provided_password.encode()).digest()
            return stored_bytes == provided_hash
        if stored_password == provided_password:
            return True
        if len(stored_bytes) > 32:
            salt = stored_bytes[:16]
            stored_hash = stored_bytes[16:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
            return stored_hash == provided_hash
    except Exception:
        pass
    return stored_password == provided_password

def get_user_by_username(username):
    """从数据库获取用户信息"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
        if user:
            columns = ['id', 'username', 'email', 'password', 'role', 'created_at', 'updated_at', 'is_active', 'super_admin_approved', 'hardware_admin_approved', 'avatar']
            return dict(zip(columns, user))
    except Exception:
        pass
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        data = {}
        try:
            json_data = request.get_json(force=False, silent=True)
            if json_data:
                data.update(json_data)
        except Exception:
            pass
        if not data:
            form_data = request.form.to_dict()
            if form_data:
                data.update(form_data)
        if not data:
            args_data = request.args.to_dict()
            if args_data:
                data.update(args_data)
        if not data and request.data:
            try:
                import json
                data = json.loads(request.data.decode('utf-8'))
            except Exception:
                pass

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': '参数错误'}), 400

        username = data.get('username')
        password = data.get('password')

        if not password or len(password) < 3:
            return jsonify({'success': False, 'message': '密码长度不足'}), 400

        user = get_user_by_username(username)
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        if not verify_password(user['password'], password):
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

        if not user.get('is_active'):
            return jsonify({'success': False, 'message': '账号未激活，请等待管理员审批'}), 403

        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user['id']}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        session['session_id'] = session_id
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['email'] = user['email']
        session['login_time'] = datetime.now().isoformat()
        session['login_ip'] = request.remote_addr
        session.permanent = True
        session['login_attempts'] = 0
        session['logged_in'] = True

        try:
            from app.utils.role_router import get_smart_redirect_url
            redirect_url = get_smart_redirect_url(user['role'])
        except ImportError:
            role_redirects = {
                'student': '/exam_system',
                'student_vip': '/exam_system',
                'designer': '/arduino',
                'teacher': '/teacher',
                'admin': '/settings',
                'super_admin': '/super_admin_dashboard',
                'hardware_admin': '/hardware/dashboard',
                'hardware_vikey_admin': '/hardware/dashboard'
            }
            redirect_url = role_redirects.get(user['role'], '/dashboard')

        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'email': user['email']
            },
            'redirect_url': redirect_url
        }), 200

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """登出页面"""
    return render_template('logout.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        data = {}
        try:
            json_data = request.get_json(force=False, silent=True)
            if json_data:
                data.update(json_data)
        except Exception:
            pass
        if not data:
            form_data = request.form.to_dict()
            if form_data:
                data.update(form_data)
        if not data and request.data:
            try:
                import json
                data = json.loads(request.data.decode('utf-8'))
            except Exception:
                pass

        if not data or 'username' not in data or 'password' not in data or 'email' not in data:
            return jsonify({'success': False, 'message': '参数错误：缺少必要信息'}), 400

        username = data.get('username').strip()
        password = data.get('password')
        email = data.get('email').strip()
        confirm_password = data.get('confirm_password', '')

        if len(username) < 3:
            return jsonify({'success': False, 'message': '用户名至少需要3个字符'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度不足'}), 400

        if password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的密码不一致'}), 400

        if not data.get('agree_user_agreement'):
            return jsonify({'success': False, 'message': '请阅读并同意用户注册协议'}), 400

        if not data.get('agree_security_agreement'):
            return jsonify({'success': False, 'message': '请阅读并同意安全信息协议'}), 400

        if not data.get('agree_usage_agreement'):
            return jsonify({'success': False, 'message': '请阅读并同意网站使用授权协议'}), 400

        existing_user = get_user_by_username(username)
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已被使用'}), 400

        salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        stored_password = base64.b64encode(salt + hashed).decode('utf-8')

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password, role, is_active, super_admin_approved, hardware_admin_approved)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username, email, stored_password, 'student', 0, 0, 0))
                conn.commit()
                user_id = cursor.lastrowid
            
            return jsonify({
                'success': True,
                'message': '注册成功！请等待管理员审批后才能登录',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'role': 'student',
                    'status': 'pending_approval'
                }
            }), 201
        except Exception as e:
            return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

    return render_template('register.html')
