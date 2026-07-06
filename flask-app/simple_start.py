#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"[SIMPLE START] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")

from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from db_manager import connect, get_db_for_table

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.secret_key = 'mtscos_ai_secret_key_2026'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)

def verify_password(stored_password, provided_password):
    import hashlib
    import base64
    
    try:
        if stored_password.startswith('pbkdf2:'):
            parts = stored_password.split('$')
            if len(parts) == 3:
                algo_parts = parts[0].split(':')
                if len(algo_parts) >= 3:
                    algo = algo_parts[1]
                    iterations = int(algo_parts[2])
                    salt = parts[1].encode()
                    stored_hash = parts[2].encode()
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

@app.route('/')
def index():
    version_data = {'version': '6.0.0', 'major_version': 6, 'minor_version': 0, 'patch_version': 0, 
                    'build_number': '', 'build_date': '2026-07-06', 'codename': 'Distributed Database Edition', 'status': 'stable'}
    
    system_notice = None
    try:
        conn = connect('system')
        if conn:
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
            conn.close()
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

@app.route('/auth/login', methods=['POST'])
def login():
    print(f"[DEBUG] Login request received at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Content-Type: {request.headers.get('Content-Type', 'Not set')}")
    
    data = {}
    
    try:
        json_data = request.get_json(force=False, silent=True)
        print(f"[DEBUG] JSON data: {json_data}")
        if json_data:
            data.update(json_data)
    except Exception as e:
        print(f"[DEBUG] JSON parse error: {e}")
    
    if not data:
        form_data = request.form.to_dict()
        print(f"[DEBUG] Form data: {form_data}")
        data.update(form_data)
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    print(f"[DEBUG] Username: {username}")
    print(f"[DEBUG] Password provided: {'Yes' if password else 'No'}")
    print(f"[DEBUG] Remember: {remember}")
    
    if not username or not password:
        print(f"[DEBUG] Missing username or password")
        return jsonify({'success': False, 'message': '用户名或密码不能为空'}), 400
    
    try:
        print(f"[DEBUG] Connecting to auth database")
        conn = connect('auth')
        if not conn:
            print(f"[DEBUG] Failed to connect to auth database")
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"[DEBUG] Executing query for username: {username}")
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        print(f"[DEBUG] User found: {'Yes' if user else 'No'}")
        
        if not user:
            print(f"[DEBUG] User not found in database")
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        stored_password = user['password']
        print(f"[DEBUG] Stored password length: {len(stored_password)}")
        print(f"[DEBUG] Stored password starts with: {stored_password[:20]}...")
        
        verify_result = verify_password(stored_password, password)
        print(f"[DEBUG] Password verify result: {verify_result}")
        
        if not verify_result:
            print(f"[DEBUG] Password verification failed")
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
        
        print(f"[DEBUG] Login successful, redirecting to: {redirect_url}")
        
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
        print(f"[DEBUG] Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '登录失败'}), 500

@app.route('/api/health')
def api_health():
    return jsonify({'status': 'healthy', 'version': '6.0.0'})

@app.route('/api/server-time')
def api_server_time():
    return jsonify({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 
                    'unix_timestamp': int(time.time())})

@app.route('/api/system/status')
def api_system_status():
    status = {
        'version': '6.0.0',
        'codename': 'Distributed Database Edition',
        'status': 'running',
        'database_count': 13,
        'databases': ['auth', 'exam', 'question', 'learning', 'system', 'ai', 
                      'physics', 'math', 'admin', 'proctor', 'user', 'log', 'other'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(status)

@app.route('/api/user/info')
def api_user_info():
    if 'logged_in' in session and session['logged_in']:
        return jsonify({
            'success': True,
            'user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role'),
                'email': session.get('email')
            }
        })
    else:
        return jsonify({'success': False, 'message': '未登录'}), 401

@app.route('/api/user/ip')
def api_user_ip():
    try:
        ip = request.remote_addr
        return jsonify({
            'success': True,
            'ip': ip,
            'message': '获取成功'
        })
    except Exception as e:
        return jsonify({'success': True, 'ip': '127.0.0.1', 'message': '获取失败，使用默认值'})

@app.route('/login')
def login_page():
    version_data = {'version': '6.0.0', 'major_version': 6, 'minor_version': 0, 'patch_version': 0, 
                    'build_number': '', 'build_date': '2026-07-06', 'codename': 'Distributed Database Edition', 'status': 'stable'}
    return render_template('login.html', version=version_data['version'], version_info=version_data)

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/hardware/dashboard')
@require_login
def hardware_dashboard():
    role = session.get('role', 'guest')
    if role in ['hardware_admin', 'hardware_vikey_admin', 'super_admin', 'system_admin']:
        return redirect('/super_admin_dashboard')
    return redirect('/dashboard')

@app.route('/super_admin_dashboard')
@require_login
def super_admin_dashboard():
    version_data = {'version': '6.0.0', 'major_version': 6, 'minor_version': 0, 'patch_version': 0, 
                    'build_number': '', 'build_date': '2026-07-06', 'codename': 'Distributed Database Edition', 'status': 'stable'}
    
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'email': session.get('email'),
        'user_id': session.get('user_id')
    }
    
    return render_template('super_admin_dashboard.html', 
                          user=user_info,
                          version=version_data['version'],
                          version_info=version_data,
                          latest_version=version_data)

@app.route('/dashboard')
@require_login
def dashboard():
    role = session.get('role', 'guest')
    if role in ['admin', 'super_admin']:
        return redirect('/super_admin_dashboard')
    elif role == 'hardware_admin':
        return redirect('/hardware/dashboard')
    elif role == 'teacher':
        return redirect('/teacher')
    elif role == 'designer':
        return redirect('/arduino')
    elif role == 'student':
        return redirect('/exam_system')
    else:
        return redirect('/exam_system')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/admin/dashboard_stats', methods=['GET'])
@require_login
def get_dashboard_stats_public():
    try:
        stats = {}
        
        conn = connect('auth')
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['user_count'] = cursor.fetchone()[0]
            conn.close()
        else:
            stats['user_count'] = 0
        
        stats['route_count'] = len([r for r in app.url_map.iter_rules()])
        
        conn = connect('log')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM session_logs')
                stats['active_users'] = cursor.fetchone()[0]
            except:
                stats['active_users'] = 0
            conn.close()
        else:
            stats['active_users'] = 0
        
        conn = connect('exam')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM exams')
                stats['exams_count'] = cursor.fetchone()[0]
            except:
                stats['exams_count'] = 0
            conn.close()
        else:
            stats['exams_count'] = 0
        
        conn = connect('question')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM questions')
                stats['questions_count'] = cursor.fetchone()[0]
            except:
                stats['questions_count'] = 0
            conn.close()
        else:
            stats['questions_count'] = 0
        
        stats['database_count'] = 13
        stats['databases'] = ['auth', 'exam', 'question', 'learning', 'system', 'ai', 
                             'physics', 'math', 'admin', 'proctor', 'user', 'log', 'other']
        stats['version'] = '6.0.0'
        stats['codename'] = 'Distributed Database Edition'
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        print(f"Error in dashboard_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080, help='端口号')
args = parser.parse_args()

print(f"[SIMPLE START] Server running on http://0.0.0.0:{args.port}")
app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)