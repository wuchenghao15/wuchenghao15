#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print(f"[SIMPLE START] Starting at {time.strftime('%Y-%m-%d %H:%M:%S')}")

from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import threading
from db_manager import connect, get_db_for_table
from version_manager import get_current_version, get_version, get_all_versions, get_version_history, check_upgrade_available, get_version_comparison, record_upgrade
from git_sync import git_sync_manager

_ai_employees_loaded = False
_ai_employees_status = None

def load_ai_employees_background():
    global _ai_employees_loaded, _ai_employees_status
    try:
        from ai_engines.all_ai_employees_loader import load_all_ai_employees, get_all_ai_employees_status
        _ai_employees_status = load_all_ai_employees()
        _ai_employees_loaded = True
    except Exception as e:
        _ai_employees_status = {'error': str(e)}
        _ai_employees_loaded = True

threading.Thread(target=load_ai_employees_background, daemon=True).start()

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
    version_data = {'version': '7.2.0', 'major_version': 7, 'minor_version': 2, 'patch_version': 0, 
                    'build_number': '20260709001', 'build_date': '2026-07-09', 'codename': 'Comprehensive Enhancement Edition', 'status': 'stable'}
    
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
    try:
        conn = connect('system')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT version FROM system_version LIMIT 1')
                result = cursor.fetchone()
                version = result[0] if result else '7.2.0'
            except:
                version = '7.2.0'
            conn.close()
        else:
            version = '7.2.0'
    except:
        version = '7.2.0'
    return jsonify({'status': 'healthy', 'version': version})

@app.route('/api/server-time')
def api_server_time():
    return jsonify({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 
                    'unix_timestamp': int(time.time())})

@app.route('/api/system/status')
def api_system_status():
    status = {
        'version': '7.2.0',
        'codename': 'Comprehensive Enhancement Edition',
        'status': 'running',
        'database_count': 17,
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
    version_data = {'version': '7.2.0', 'major_version': 7, 'minor_version': 2, 'patch_version': 0, 
                    'build_number': '20260709001', 'build_date': '2026-07-09', 'codename': 'Comprehensive Enhancement Edition', 'status': 'stable'}
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
    version_data = {'version': '7.2.0', 'major_version': 7, 'minor_version': 2, 'patch_version': 0, 
                    'build_number': '20260709001', 'build_date': '2026-07-09', 'codename': 'Comprehensive Enhancement Edition', 'status': 'stable'}
    
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
        stats['version'] = '7.2.0'
        stats['codename'] = 'Comprehensive Enhancement Edition'
        
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

@app.route('/exam_system')
@require_login
def exam_system():
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'email': session.get('email'),
        'user_id': session.get('user_id')
    }
    return render_template('exam_system.html', user=user_info, version='7.2.0')

@app.route('/teacher')
@require_login  
def teacher_dashboard():
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'email': session.get('email'),
        'user_id': session.get('user_id')
    }
    return render_template('teacher_dashboard.html', user=user_info, version='7.2.0')

@app.route('/admin_app/settings')
@require_login
def admin_settings():
    user_info = {
        'username': session.get('username'),
        'role': session.get('role'),
        'email': session.get('email'),
        'user_id': session.get('user_id')
    }
    return render_template('admin_settings.html', user=user_info, version='7.2.0')

@app.route('/api/users', methods=['GET'])
@require_login
def api_users():
    try:
        conn = connect('auth')
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, role, email, created_at FROM users ORDER BY created_at DESC')
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row['id'],
                    'username': row['username'],
                    'role': row['role'],
                    'email': row['email'],
                    'created_at': row['created_at']
                })
            conn.close()
            return jsonify({'success': True, 'data': users})
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/exams', methods=['GET'])
@require_login
def api_exams():
    try:
        conn = connect('exam')
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, description, status, created_at FROM exams ORDER BY created_at DESC')
            exams = []
            for row in cursor.fetchall():
                exams.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'status': row['status'],
                    'created_at': row['created_at']
                })
            conn.close()
            return jsonify({'success': True, 'data': exams})
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/questions/count', methods=['GET'])
@require_login
def api_question_count():
    try:
        conn = connect('question')
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM questions')
            count = cursor.fetchone()[0]
            conn.close()
            
            cursor.execute('SELECT subject, COUNT(*) FROM questions GROUP BY subject')
            subjects = []
            for row in cursor.fetchall():
                subjects.append({'subject': row[0], 'count': row[1]})
            
            return jsonify({'success': True, 'data': {'total': count, 'subjects': subjects}})
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/version')
def api_system_version():
    try:
        conn = connect('system')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT version FROM system_version LIMIT 1')
                result = cursor.fetchone()
                if result:
                    db_version = result[0]
                else:
                    db_version = '7.2.0'
            except:
                db_version = '7.2.0'
            conn.close()
        else:
            db_version = '7.2.0'
    except:
        db_version = '7.2.0'
    
    version_data = {
        'version': db_version,
        'major_version': int(db_version.split('.')[0]),
        'minor_version': int(db_version.split('.')[1]),
        'patch_version': int(db_version.split('.')[2]) if len(db_version.split('.')) > 2 else 0,
        'build_number': '',
        'build_date': '2026-07-06',
        'codename': 'Distributed Database Edition',
        'status': 'stable',
        'description': f'版本 {db_version}，支持13个分布式数据库，543+路由，460+API接口'
    }
    return jsonify({'success': True, 'data': version_data})

@app.route('/api/system/version/detail/<version>')
@require_login
def api_system_version_detail(version):
    version_data = get_version(version)
    if version_data:
        return jsonify({'success': True, 'data': version_data})
    return jsonify({'success': False, 'message': '版本不存在'}), 404

@app.route('/api/system/version/all')
@require_login
def api_system_version_all():
    versions = get_all_versions()
    return jsonify({'success': True, 'data': versions})

@app.route('/api/system/version/history')
@require_login
def api_system_version_history():
    history = get_version_history()
    return jsonify({'success': True, 'data': history})

@app.route('/api/system/version/check')
def api_system_version_check():
    current_version = get_current_version()['version']
    result = check_upgrade_available(current_version)
    return jsonify({'success': True, 'data': result})

@app.route('/api/system/version/compare')
@require_login
def api_system_version_compare():
    version1 = request.args.get('v1', '5.0.0')
    version2 = request.args.get('v2', '7.2.0')
    comparison = get_version_comparison(version1, version2)
    if comparison:
        return jsonify({'success': True, 'data': comparison})
    return jsonify({'success': False, 'message': '版本信息不存在'}), 404

@app.route('/api/system/resources')
def api_system_resources():
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_percent': disk.percent,
            'disk_total': disk.total,
            'disk_used': disk.used
        }
        return jsonify({'success': True, 'data': resources})
    except ImportError:
        return jsonify({'success': True, 'data': {'message': 'psutil not installed'}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/health/detailed')
def api_system_health_detailed():
    health = {
        'overall': 'healthy',
        'databases': [],
        'services': []
    }
    
    databases = ['auth', 'exam', 'question', 'learning', 'system', 'ai', 
                 'physics', 'math', 'admin', 'proctor', 'user', 'log', 'other']
    
    for db_name in databases:
        try:
            conn = connect(db_name)
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                health['databases'].append({
                    'name': db_name,
                    'status': 'healthy',
                    'tables': table_count
                })
            else:
                health['databases'].append({
                    'name': db_name,
                    'status': 'unavailable',
                    'tables': 0
                })
        except Exception as e:
            health['databases'].append({
                'name': db_name,
                'status': 'error',
                'error': str(e)
            })
    
    health['services'].append({
        'name': 'authentication',
        'status': 'running'
    })
    health['services'].append({
        'name': 'exam_system',
        'status': 'running'
    })
    health['services'].append({
        'name': 'question_bank',
        'status': 'running'
    })
    health['services'].append({
        'name': 'learning_system',
        'status': 'running'
    })
    
    if all(db['status'] == 'healthy' for db in health['databases']):
        health['overall'] = 'healthy'
    else:
        health['overall'] = 'degraded'
    
    return jsonify({'success': True, 'data': health})

@app.route('/api/roles')
@require_login
def api_roles():
    roles = [
        {'id': 'super_admin', 'name': '超级管理员', 'description': '最高权限，管理所有系统功能'},
        {'id': 'admin', 'name': '管理员', 'description': '管理系统配置和用户'},
        {'id': 'hardware_admin', 'name': '硬件管理员', 'description': '管理硬件认证和配置'},
        {'id': 'teacher', 'name': '教师', 'description': '管理教学和考试'},
        {'id': 'student', 'name': '学生', 'description': '参加考试和学习'},
        {'id': 'researcher', 'name': '研究员', 'description': '进行教研分析'},
        {'id': 'designer', 'name': '设计师', 'description': '开发和设计功能'}
    ]
    return jsonify({'success': True, 'data': roles})

@app.route('/api/permissions')
@require_login
def api_permissions():
    permissions = [
        {'id': 'view_dashboard', 'name': '查看仪表盘', 'group': 'dashboard'},
        {'id': 'manage_users', 'name': '管理用户', 'group': 'user_management'},
        {'id': 'manage_exams', 'name': '管理考试', 'group': 'exam_management'},
        {'id': 'manage_questions', 'name': '管理题库', 'group': 'question_management'},
        {'id': 'manage_system', 'name': '管理系统', 'group': 'system_management'},
        {'id': 'view_reports', 'name': '查看报表', 'group': 'reporting'},
        {'id': 'manage_backups', 'name': '管理备份', 'group': 'backup_management'},
        {'id': 'manage_ai', 'name': '管理AI', 'group': 'ai_management'}
    ]
    return jsonify({'success': True, 'data': permissions})

@app.route('/api/logs/recent')
@require_login
def api_recent_logs():
    try:
        conn = connect('log')
        if conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT id, user_id, action, ip_address, created_at FROM system_logs ORDER BY created_at DESC LIMIT 20')
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'action': row['action'],
                        'ip_address': row['ip_address'],
                        'created_at': row['created_at']
                    })
            except:
                logs = []
            conn.close()
            return jsonify({'success': True, 'data': logs})
        return jsonify({'success': False, 'message': '数据库连接失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/list')
@require_login
def api_database_list():
    databases = [
        {'name': 'auth', 'description': '认证数据库', 'size': '135KB'},
        {'name': 'exam', 'description': '考试数据库', 'size': '2.7MB'},
        {'name': 'question', 'description': '题库数据库', 'size': '669MB'},
        {'name': 'learning', 'description': '学习数据库', 'size': '634KB'},
        {'name': 'system', 'description': '系统数据库', 'size': '50MB'},
        {'name': 'ai', 'description': 'AI引擎数据库', 'size': '622KB'},
        {'name': 'physics', 'description': '物理题库', 'size': '65KB'},
        {'name': 'math', 'description': '数学题库', 'size': '90KB'},
        {'name': 'admin', 'description': '管理数据库', 'size': '1.3MB'},
        {'name': 'proctor', 'description': '监考数据库', 'size': '61KB'},
        {'name': 'user', 'description': '用户数据库', 'size': '811KB'},
        {'name': 'log', 'description': '日志数据库', 'size': '98MB'},
        {'name': 'other', 'description': '其他数据', 'size': '86MB'}
    ]
    return jsonify({'success': True, 'data': databases})

@app.route('/api/cluster/status')
@require_login
def api_cluster_status():
    cluster = {
        'name': 'mtscos-cluster',
        'status': 'active',
        'nodes': [
            {'id': 'node-master', 'host': '127.0.0.1', 'port': 8888, 'role': 'master', 'status': 'online'},
            {'id': 'node-worker-1', 'host': '127.0.0.1', 'port': 8889, 'role': 'worker', 'status': 'offline'},
            {'id': 'node-worker-2', 'host': '127.0.0.1', 'port': 8890, 'role': 'worker', 'status': 'offline'}
        ],
        'health_check_interval': 15,
        'data_sync_interval': 30
    }
    return jsonify({'success': True, 'data': cluster})

@app.route('/api/ai/engines')
@require_login
def api_ai_engines():
    engines = [
        {'id': 'knowledge_graph', 'name': '知识图谱引擎', 'status': 'running', 'description': '知识点关联与推理'},
        {'id': 'reward_system', 'name': '奖励成就引擎', 'status': 'running', 'description': '积分/徽章/等级/成就'},
        {'id': 'wrong_question', 'name': '错题本引擎', 'status': 'running', 'description': '错题分析与智能重练'},
        {'id': 'prediction', 'name': '学习预测引擎', 'status': 'running', 'description': '成绩预测/退学风险/趋势分析'},
        {'id': 'tutor', 'name': 'AI助教引擎', 'status': 'running', 'description': '智能答疑/概念解释'},
        {'id': 'collaboration', 'name': '协作学习引擎', 'status': 'running', 'description': '学习小组/同伴互助'},
        {'id': 'proctoring', 'name': '智能监考引擎', 'status': 'running', 'description': '诚信监控/异常检测'},
        {'id': 'assessment', 'name': '智能评估引擎', 'status': 'running', 'description': '6维评估/成长轨迹'}
    ]
    return jsonify({'success': True, 'data': engines})

@app.route('/api/ai/models')
@require_login
def api_ai_models():
    models = [
        {'id': 'model-1', 'name': 'MTSCOS-LLM-Base', 'version': '1.0.0', 'status': 'active', 'description': '基础大语言模型'},
        {'id': 'model-2', 'name': 'MTSCOS-LLM-Advanced', 'version': '2.0.0', 'status': 'active', 'description': '高级大语言模型'},
        {'id': 'model-3', 'name': 'MTSCOS-Embedding', 'version': '1.5.0', 'status': 'active', 'description': '文本嵌入模型'},
        {'id': 'model-4', 'name': 'MTSCOS-QA', 'version': '1.2.0', 'status': 'active', 'description': '问答模型'},
        {'id': 'model-5', 'name': 'MTSCOS-Code', 'version': '1.0.0', 'status': 'active', 'description': '代码生成模型'}
    ]
    return jsonify({'success': True, 'data': models})

@app.route('/api/backup/list')
@require_login
def api_backup_list():
    backups = [
        {'id': 'backup-1', 'name': 'Full Backup 2026-07-06', 'date': '2026-07-06 15:00:00', 'size': '820MB', 'status': 'completed'},
        {'id': 'backup-2', 'name': 'Daily Backup 2026-07-05', 'date': '2026-07-05 23:00:00', 'size': '815MB', 'status': 'completed'},
        {'id': 'backup-3', 'name': 'Weekly Backup 2026-07-04', 'date': '2026-07-04 00:00:00', 'size': '810MB', 'status': 'completed'}
    ]
    return jsonify({'success': True, 'data': backups})

@app.route('/api/notification/list')
@require_login
def api_notification_list():
    notifications = [
        {'id': 1, 'title': '系统升级通知', 'content': '系统已升级至v7.2.0全面增强版本', 'type': 'info', 'read': False, 'created_at': '2026-07-09 10:00:00'},
        {'id': 2, 'title': '数据库备份提醒', 'content': '上次备份时间: 2026-07-06 15:00:00', 'type': 'warning', 'read': True, 'created_at': '2026-07-06 09:00:00'},
        {'id': 3, 'title': '新用户注册', 'content': '有3位新用户注册', 'type': 'success', 'read': True, 'created_at': '2026-07-05 18:00:00'}
    ]
    return jsonify({'success': True, 'data': notifications})

@app.route('/api/route/list')
@require_login
def api_route_list():
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        routes.append({
            'path': str(rule),
            'methods': methods,
            'endpoint': rule.endpoint
        })
    return jsonify({'success': True, 'data': routes})

@app.route('/api/statistics/overview')
@require_login
def api_statistics_overview():
    try:
        stats = {}
        
        conn = connect('auth')
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['user_count'] = cursor.fetchone()[0]
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_login) = DATE('now')")
                stats['today_logins'] = cursor.fetchone()[0]
            except:
                stats['today_logins'] = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')")
                stats['today_registers'] = cursor.fetchone()[0]
            except:
                stats['today_registers'] = 0
            cursor.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
            stats['role_distribution'] = [{'role': row[0], 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
        
        conn = connect('exam')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM exams')
                stats['exam_count'] = cursor.fetchone()[0]
            except:
                stats['exam_count'] = 0
            try:
                cursor.execute('SELECT COUNT(*) FROM exam_results')
                stats['exam_result_count'] = cursor.fetchone()[0]
            except:
                stats['exam_result_count'] = 0
            conn.close()
        
        conn = connect('question')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM questions')
                stats['question_count'] = cursor.fetchone()[0]
            except:
                stats['question_count'] = 0
            try:
                cursor.execute('SELECT subject, COUNT(*) FROM questions GROUP BY subject')
                stats['subject_distribution'] = [{'subject': row[0], 'count': row[1]} for row in cursor.fetchall()]
            except:
                stats['subject_distribution'] = []
            conn.close()
        
        conn = connect('learning')
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM learning_records')
                stats['learning_record_count'] = cursor.fetchone()[0]
            except:
                stats['learning_record_count'] = 0
            try:
                cursor.execute('SELECT COUNT(*) FROM wrong_questions')
                stats['wrong_question_count'] = cursor.fetchone()[0]
            except:
                stats['wrong_question_count'] = 0
            conn.close()
        
        import subprocess
        try:
            result = subprocess.run(['grep', '-r', '@app.route', '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py'], capture_output=True, text=True)
            app_route_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            stats['route_count'] = max(app_route_count, len([r for r in app.url_map.iter_rules()]))
        except:
            stats['route_count'] = len([r for r in app.url_map.iter_rules()])
        
        try:
            conn = connect('system')
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT version FROM system_version LIMIT 1')
                    result = cursor.fetchone()
                    stats['version'] = result[0] if result else '7.2.0'
                except:
                    stats['version'] = '7.2.0'
                conn.close()
            else:
                stats['version'] = '7.2.0'
        except:
            stats['version'] = '7.2.0'
        
        stats['database_count'] = 13
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/git/status')
@require_login
def api_git_status():
    result = git_sync_manager.get_status()
    if result['success']:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error', '获取状态失败')}), 500

@app.route('/api/git/log')
@require_login
def api_git_log():
    limit = request.args.get('limit', 10, type=int)
    result = git_sync_manager.get_log(limit=limit)
    if result['success']:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error', '获取日志失败')}), 500

@app.route('/api/git/sync', methods=['POST'])
@require_login
def api_git_sync():
    data = request.get_json() or {}
    commit_message = data.get('message')
    result = git_sync_manager.sync(commit_message)
    if result['success']:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error', result.get('message', '同步失败'))}), 500

@app.route('/api/git/auto_sync', methods=['POST'])
@require_login
def api_git_auto_sync():
    result = git_sync_manager.auto_sync()
    if result['success']:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error', result.get('message', '自动同步失败'))}), 500

@app.route('/api/git/pull', methods=['POST'])
@require_login
def api_git_pull():
    data = request.get_json() or {}
    remote = data.get('remote', 'origin')
    branch = data.get('branch', 'main')
    result = git_sync_manager.pull(remote, branch)
    if result['success']:
        return jsonify({'success': True, 'data': {'message': '拉取成功', 'output': result.get('stdout', '')}})
    return jsonify({'success': False, 'error': result.get('stderr', '拉取失败')}), 500

@app.route('/api/git/commit', methods=['POST'])
@require_login
def api_git_commit():
    data = request.get_json() or {}
    message = data.get('message')
    add_result = git_sync_manager.add_all()
    if not add_result['success']:
        return jsonify({'success': False, 'error': add_result.get('stderr', '添加文件失败')}), 500
    
    commit_result = git_sync_manager.commit(message)
    if commit_result['success']:
        return jsonify({'success': True, 'data': {'message': '提交成功', 'output': commit_result.get('stdout', '')}})
    return jsonify({'success': False, 'error': commit_result.get('stderr', '提交失败')}), 500

@app.route('/api/git/push', methods=['POST'])
@require_login
def api_git_push():
    data = request.get_json() or {}
    remote = data.get('remote', 'origin')
    branch = data.get('branch', 'main')
    result = git_sync_manager.push(remote, branch)
    if result['success']:
        return jsonify({'success': True, 'data': {'message': '推送成功', 'output': result.get('stdout', '')}})
    return jsonify({'success': False, 'error': result.get('stderr', '推送失败')}), 500

@app.route('/api/ai_employees/status')
@require_login
def api_ai_employees_status():
    global _ai_employees_loaded, _ai_employees_status
    if not _ai_employees_loaded:
        return jsonify({'success': True, 'data': {'loading': True, 'message': 'AI员工正在加载中...'}})
    return jsonify({'success': True, 'data': _ai_employees_status})

@app.route('/api/ai_employees/list')
@require_login
def api_ai_employees_list():
    global _ai_employees_status
    if not _ai_employees_status:
        return jsonify({'success': False, 'message': 'AI员工尚未加载'}), 500
    return jsonify({'success': True, 'data': _ai_employees_status.get('employees', [])})

@app.route('/api/ai_agents/list')
@require_login
def api_ai_agents_list():
    global _ai_employees_status
    if not _ai_employees_status:
        return jsonify({'success': False, 'message': 'AI员工尚未加载'}), 500
    return jsonify({'success': True, 'data': _ai_employees_status.get('agents', [])})

@app.route('/api/automation/tasks')
@require_login
def api_automation_tasks():
    global _ai_employees_status
    if not _ai_employees_status:
        return jsonify({'success': False, 'message': 'AI员工尚未加载'}), 500
    return jsonify({'success': True, 'data': _ai_employees_status.get('tasks', [])})

@app.route('/api/ai_employees/db_count')
@require_login
def api_ai_employees_db_count():
    try:
        from ai_engines.all_ai_employees_loader import get_ai_db_employee_count
        count = get_ai_db_employee_count()
        if count:
            return jsonify({'success': True, 'data': count})
        return jsonify({'success': False, 'message': '获取数据库统计失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai_employees/enable/<emp_id>', methods=['POST'])
@require_login
def api_enable_ai_employee(emp_id):
    try:
        from ai_engines.all_ai_employees_loader import enable_ai_employee
        result = enable_ai_employee(emp_id)
        if result:
            global _ai_employees_status
            from ai_engines.all_ai_employees_loader import get_all_ai_employees_status
            _ai_employees_status = get_all_ai_employees_status()
            return jsonify({'success': True, 'message': 'AI员工已启用'})
        return jsonify({'success': False, 'message': 'AI员工不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai_employees/disable/<emp_id>', methods=['POST'])
@require_login
def api_disable_ai_employee(emp_id):
    try:
        from ai_engines.all_ai_employees_loader import disable_ai_employee
        result = disable_ai_employee(emp_id)
        if result:
            global _ai_employees_status
            from ai_engines.all_ai_employees_loader import get_all_ai_employees_status
            _ai_employees_status = get_all_ai_employees_status()
            return jsonify({'success': True, 'message': 'AI员工已禁用'})
        return jsonify({'success': False, 'message': 'AI员工不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai_agents/enable/<agent_id>', methods=['POST'])
@require_login
def api_enable_ai_agent(agent_id):
    try:
        from ai_engines.all_ai_employees_loader import enable_ai_agent
        result = enable_ai_agent(agent_id)
        if result:
            global _ai_employees_status
            from ai_engines.all_ai_employees_loader import get_all_ai_employees_status
            _ai_employees_status = get_all_ai_employees_status()
            return jsonify({'success': True, 'message': 'AI Agent已启用'})
        return jsonify({'success': False, 'message': 'AI Agent不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai_agents/disable/<agent_id>', methods=['POST'])
@require_login
def api_disable_ai_agent(agent_id):
    try:
        from ai_engines.all_ai_employees_loader import disable_ai_agent
        result = disable_ai_agent(agent_id)
        if result:
            global _ai_employees_status
            from ai_engines.all_ai_employees_loader import get_all_ai_employees_status
            _ai_employees_status = get_all_ai_employees_status()
            return jsonify({'success': True, 'message': 'AI Agent已禁用'})
        return jsonify({'success': False, 'message': 'AI Agent不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai_employees/enable_all', methods=['POST'])
@require_login
def api_enable_all_ai_employees():
    try:
        from ai_engines.all_ai_employees_loader import enable_all_ai_employees, enable_all_ai_agents
        emp_count = enable_all_ai_employees()
        agent_count = enable_all_ai_agents()
        global _ai_employees_status
        from ai_engines.all_ai_employees_loader import get_all_ai_employees_status
        _ai_employees_status = get_all_ai_employees_status()
        return jsonify({'success': True, 'data': {
            'enabled_employees': emp_count,
            'enabled_agents': agent_count
        }, 'message': f'已启用 {emp_count} 个AI员工和 {agent_count} 个AI Agent'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== AI智能检索查询模型 ====================
_search_models_initialized = False

def _init_search_models_background():
    """后台初始化检索模型系统"""
    global _search_models_initialized
    try:
        from ai_engines.ai_search_query_model import init_search_models
        init_search_models()
        _search_models_initialized = True
        print(f"[SEARCH MODELS] 初始化完成")
    except Exception as e:
        print(f"[SEARCH MODELS] 初始化失败: {e}")
        _search_models_initialized = True

threading.Thread(target=_init_search_models_background, daemon=True).start()

@app.route('/api/search_models/status')
@require_login
def api_search_models_status():
    """获取检索模型系统状态"""
    try:
        from ai_engines.ai_search_query_model import get_search_model_status
        status = get_search_model_status()
        status['initialized'] = _search_models_initialized
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/list')
@require_login
def api_search_models_list():
    """获取所有检索模型列表"""
    try:
        from ai_engines.ai_search_query_model import get_search_models_list
        models = get_search_models_list()
        return jsonify({'success': True, 'data': models, 'total': len(models)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/create', methods=['POST'])
@require_login
def api_create_search_model():
    """创建自定义检索模型"""
    try:
        from ai_engines.ai_search_query_model import create_search_model
        data = request.get_json() or {}
        model_name = data.get('model_name')
        target_table = data.get('target_table')
        model_type = data.get('model_type', 'auto')
        index_fields = data.get('index_fields', [])
        optimization_strategy = data.get('optimization_strategy', 'auto')

        if not model_name or not target_table:
            return jsonify({'success': False, 'message': '缺少模型名称或目标表'}), 400

        result = create_search_model(model_name, target_table, model_type,
                                     index_fields, optimization_strategy)
        if result:
            return jsonify({'success': True, 'message': f'检索模型 {model_name} 创建成功'})
        return jsonify({'success': False, 'message': '创建失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/execute', methods=['POST'])
@require_login
def api_execute_search_query():
    """使用检索模型执行查询"""
    try:
        from ai_engines.ai_search_query_model import execute_search_query
        data = request.get_json() or {}
        table_name = data.get('table_name')
        query_sql = data.get('query_sql')
        params = data.get('params')
        model_name = data.get('model_name')

        if not table_name or not query_sql:
            return jsonify({'success': False, 'message': '缺少表名或查询SQL'}), 400

        result = execute_search_query(table_name, query_sql, params, model_name)
        return jsonify({
            'success': True,
            'data': {
                'count': result.get('count', 0),
                'execution_time': result.get('execution_time', 0),
                'index_used': result.get('index_used'),
                'model_used': result.get('model_used')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/optimize', methods=['POST'])
@require_login
def api_optimize_search_models():
    """优化所有检索模型"""
    try:
        from ai_engines.ai_search_query_model import optimize_all_search_models
        count = optimize_all_search_models()
        return jsonify({'success': True, 'data': {'optimized_count': count},
                        'message': f'已优化 {count} 个检索模型'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/adaptations')
@require_login
def api_search_model_adaptations():
    """获取模型适配历史"""
    try:
        from ai_engines.ai_search_query_model import search_model_manager
        adaptations = search_model_manager.get_adaptations_history()
        return jsonify({'success': True, 'data': adaptations, 'total': len(adaptations)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search_models/indexes')
@require_login
def api_search_model_indexes():
    """获取索引推荐"""
    try:
        from ai_engines.ai_search_query_model import search_model_manager
        recommendations = search_model_manager.get_index_recommendations()
        return jsonify({'success': True, 'data': recommendations, 'total': len(recommendations)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== AI智能API数据库管理 ====================
_api_db_initialized = False
_api_db_scan_result = None

def _init_api_db_background():
    """后台初始化API数据库并扫描注册API"""
    global _api_db_initialized, _api_db_scan_result
    try:
        from ai_engines.ai_api_database_manager import init_api_db_manager, scan_and_register_apis
        # 初始化数据库
        init_api_db_manager()
        # 扫描并注册所有API
        _api_db_scan_result = scan_and_register_apis(app)
        _api_db_initialized = True
        print(f"[API DB] 初始化完成: {_api_db_scan_result}")
    except Exception as e:
        print(f"[API DB] 初始化失败: {e}")
        _api_db_initialized = True

threading.Thread(target=_init_api_db_background, daemon=True).start()

@app.route('/api/api_database/status')
@require_login
def api_api_database_status():
    """获取API数据库状态"""
    try:
        from ai_engines.ai_api_database_manager import get_api_db_status
        status = get_api_db_status()
        status['initialized'] = _api_db_initialized
        status['scan_result'] = _api_db_scan_result
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/apis')
@require_login
def api_api_database_apis():
    """获取API数据库中所有API列表"""
    try:
        from ai_engines.ai_api_database_manager import get_api_db_apis_list
        category = request.args.get('category')
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        apis = get_api_db_apis_list(category, enabled_only)
        return jsonify({'success': True, 'data': apis, 'total': len(apis)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/groups')
@require_login
def api_api_database_groups():
    """获取API分组"""
    try:
        from ai_engines.ai_api_database_manager import ai_api_db_manager
        groups = ai_api_db_manager.get_api_groups()
        return jsonify({'success': True, 'data': groups, 'total': len(groups)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/category_stats')
@require_login
def api_api_database_category_stats():
    """获取API分类统计"""
    try:
        from ai_engines.ai_api_database_manager import ai_api_db_manager
        stats = ai_api_db_manager.get_category_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/enable/<int:api_id>', methods=['POST'])
@require_login
def api_api_database_enable(api_id):
    """启用单个API"""
    try:
        from ai_engines.ai_api_database_manager import enable_api_in_db
        result = enable_api_in_db(api_id)
        if result:
            return jsonify({'success': True, 'message': f'API {api_id} 已启用'})
        return jsonify({'success': False, 'message': 'API不存在或启用失败'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/disable/<int:api_id>', methods=['POST'])
@require_login
def api_api_database_disable(api_id):
    """禁用单个API"""
    try:
        from ai_engines.ai_api_database_manager import disable_api_in_db
        result = disable_api_in_db(api_id)
        if result:
            return jsonify({'success': True, 'message': f'API {api_id} 已禁用'})
        return jsonify({'success': False, 'message': 'API不存在或禁用失败'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/enable_all', methods=['POST'])
@require_login
def api_api_database_enable_all():
    """启用所有API"""
    try:
        from ai_engines.ai_api_database_manager import enable_all_apis_in_db
        count = enable_all_apis_in_db()
        return jsonify({'success': True, 'data': {'enabled_count': count},
                        'message': f'已启用 {count} 个API'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/api_database/rescan', methods=['POST'])
@require_login
def api_api_database_rescan():
    """重新扫描并注册所有API"""
    try:
        from ai_engines.ai_api_database_manager import scan_and_register_apis
        result = scan_and_register_apis(app)
        global _api_db_scan_result
        _api_db_scan_result = result
        return jsonify({'success': True, 'data': result,
                        'message': f'扫描完成: 新注册 {result.get("registered", 0)} 个, 更新 {result.get("updated", 0)} 个'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== AI智能路由数据库管理 ====================
_routes_db_initialized = False
_routes_db_scan_result = None

def _init_routes_db_background():
    """后台初始化路由数据库并扫描注册路由"""
    global _routes_db_initialized, _routes_db_scan_result
    try:
        from ai_engines.ai_routes_database_manager import init_routes_db_manager, scan_and_register_routes
        # 初始化数据库
        init_routes_db_manager()
        # 扫描并注册所有路由
        _routes_db_scan_result = scan_and_register_routes(app)
        _routes_db_initialized = True
        print(f"[ROUTES DB] 初始化完成: {_routes_db_scan_result}")
    except Exception as e:
        print(f"[ROUTES DB] 初始化失败: {e}")
        _routes_db_initialized = True

threading.Thread(target=_init_routes_db_background, daemon=True).start()

@app.route('/api/routes_database/status')
@require_login
def api_routes_database_status():
    """获取路由数据库状态"""
    try:
        from ai_engines.ai_routes_database_manager import get_routes_db_status
        status = get_routes_db_status()
        status['initialized'] = _routes_db_initialized
        status['scan_result'] = _routes_db_scan_result
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/routes')
@require_login
def api_routes_database_routes():
    """获取路由数据库中所有路由列表"""
    try:
        from ai_engines.ai_routes_database_manager import get_routes_db_list
        category = request.args.get('category')
        route_type = request.args.get('route_type')
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        routes = get_routes_db_list(category, route_type, enabled_only)
        return jsonify({'success': True, 'data': routes, 'total': len(routes)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/groups')
@require_login
def api_routes_database_groups():
    """获取路由分组"""
    try:
        from ai_engines.ai_routes_database_manager import ai_routes_db_manager
        groups = ai_routes_db_manager.get_route_groups()
        return jsonify({'success': True, 'data': groups, 'total': len(groups)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/category_stats')
@require_login
def api_routes_database_category_stats():
    """获取路由分类统计"""
    try:
        from ai_engines.ai_routes_database_manager import ai_routes_db_manager
        stats = ai_routes_db_manager.get_category_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/enable/<int:route_id>', methods=['POST'])
@require_login
def api_routes_database_enable(route_id):
    """启用单个路由"""
    try:
        from ai_engines.ai_routes_database_manager import enable_route_in_db
        result = enable_route_in_db(route_id)
        if result:
            return jsonify({'success': True, 'message': f'路由 {route_id} 已启用'})
        return jsonify({'success': False, 'message': '路由不存在或启用失败'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/disable/<int:route_id>', methods=['POST'])
@require_login
def api_routes_database_disable(route_id):
    """禁用单个路由"""
    try:
        from ai_engines.ai_routes_database_manager import disable_route_in_db
        result = disable_route_in_db(route_id)
        if result:
            return jsonify({'success': True, 'message': f'路由 {route_id} 已禁用'})
        return jsonify({'success': False, 'message': '路由不存在或禁用失败'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/enable_all', methods=['POST'])
@require_login
def api_routes_database_enable_all():
    """启用所有路由"""
    try:
        from ai_engines.ai_routes_database_manager import enable_all_routes_in_db
        count = enable_all_routes_in_db()
        return jsonify({'success': True, 'data': {'enabled_count': count},
                        'message': f'已启用 {count} 个路由'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routes_database/rescan', methods=['POST'])
@require_login
def api_routes_database_rescan():
    """重新扫描并注册所有路由"""
    try:
        from ai_engines.ai_routes_database_manager import scan_and_register_routes
        result = scan_and_register_routes(app)
        global _routes_db_scan_result
        _routes_db_scan_result = result
        return jsonify({'success': True, 'data': result,
                        'message': f'扫描完成: 新注册 {result.get("registered", 0)} 个, 更新 {result.get("updated", 0)} 个'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080, help='端口号')
args = parser.parse_args()

print(f"[SIMPLE START] Server running on http://0.0.0.0:{args.port}")
print(f"[SIMPLE START] Routes: {len([r for r in app.url_map.iter_rules()])}")
app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)