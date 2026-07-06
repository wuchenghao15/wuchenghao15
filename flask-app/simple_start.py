#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"[SIMPLE START] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")

from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.secret_key = 'mtscos_ai_secret_key_2026'

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

@app.route('/')
def index():
    version_data = {'version': '5.3.0', 'major_version': 5, 'minor_version': 3, 'patch_version': 0, 
                    'build_number': '', 'build_date': '2026-07-06', 'codename': 'Enhanced Permission Edition', 'status': 'stable'}
    
    system_notice = None
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content FROM system_notices 
                WHERE status = 'active' 
                ORDER BY priority DESC, created_at DESC 
                LIMIT 1
            """)
            notice = cursor.fetchone()
            if notice:
                system_notice = notice['content']
    except Exception as e:
        print(f"Error getting system notice: {e}")
    
    return render_template('index.html',
                          version=version_data['version'],
                          version_info=version_data,
                          latest_version=version_data,
                          system_notice=system_notice)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

def verify_password(stored_password, provided_password):
    import hashlib
    import base64
    
    try:
        if stored_password.startswith('pbkdf2:'):
            parts = stored_password.split('$')
            if len(parts) == 3:
                algorithm_info = parts[0]
                salt = parts[1].encode()
                stored_hash = parts[2].encode()
                
                algo_parts = algorithm_info.split(':')
                if len(algo_parts) >= 3:
                    algo = algo_parts[1]
                    iterations = int(algo_parts[2])
                    provided_hash = hashlib.pbkdf2_hmac(algo, provided_password.encode(), salt, iterations)
                    return stored_hash == base64.b64encode(provided_hash).decode()
            return False
        
        if stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$'):
            try:
                import bcrypt
                return bcrypt.checkpw(provided_password.encode(), stored_password.encode())
            except ImportError:
                return False
        
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
        
        if stored_password == provided_password:
            return True
            
    except Exception as e:
        print(f"Password verify error: {e}")
    
    return stored_password == provided_password


@app.route('/auth/login', methods=['POST'])
def login():
    data = {}
    
    try:
        json_data = request.get_json(force=False, silent=True)
        if json_data:
            data.update(json_data)
    except:
        pass
    
    if not data:
        data.update(request.form.to_dict())
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名或密码不能为空'}), 400
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            if not verify_password(user['password'], password):
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user['role']
            session['user_id'] = user['id']
            session['email'] = user['email']
            
            if isinstance(remember, str):
                remember = remember.lower() in ['true', '1', 'yes', 'on']
            
            if remember:
                session.permanent = True
                from datetime import timedelta
                app.permanent_session_lifetime = timedelta(days=30)
            
            redirect_url = '/'
            role = user['role']
            
            if role in ['admin', 'super_admin']:
                redirect_url = '/admin_app/settings'
            elif role == 'hardware_admin':
                redirect_url = '/hardware/dashboard'
            elif role == 'teacher' or role == 'teacher_admin':
                redirect_url = '/teacher'
            elif role == 'designer':
                redirect_url = '/arduino'
            elif role == 'student' or role == 'student_vip':
                redirect_url = '/exam_system'
            elif role == 'researcher':
                redirect_url = '/dashboard'
            else:
                redirect_url = '/exam_system'
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'email': user['email']
                },
                'redirect': redirect_url
            })
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': '登录失败'}), 500

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080, help='端口号')
args = parser.parse_args()

print(f"[SIMPLE START] Server running on http://0.0.0.0:{args.port}")
app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)
