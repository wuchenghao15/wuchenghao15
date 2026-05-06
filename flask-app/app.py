#!/usr/bin/env python3
"""
MTSCOS AI Project Main Application
"""

import os
import sys
import logging
import traceback
import argparse
import sqlite3
from datetime import datetime
from flask import jsonify, render_template, request, redirect

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置默认的MODEL_PATH环境变量
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

# 创建Flask应用
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['JSON_AS_ASCII'] = False

# 配置CORS支持
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# 导入并注册硬件管理路由蓝图
from app.routes.hardware_routes import hardware_bp
app.register_blueprint(hardware_bp)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def verify_password(stored_password, provided_password):
    """验证密码 - 支持多种哈希方式"""
    import hashlib
    import base64
    
    try:
        # 尝试PBKDF2验证
        stored_bytes = base64.b64decode(stored_password)
        if len(stored_bytes) == 32:
            # 可能是直接的SHA-256哈希
            provided_hash = hashlib.sha256(provided_password.encode()).digest()
            return stored_bytes == provided_hash
        
        # 尝试简单比较（用于测试）
        if stored_password == provided_password:
            return True
            
        # PBKDF2格式：salt + hash
        if len(stored_bytes) > 32:
            salt = stored_bytes[:16]
            stored_hash = stored_bytes[16:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
            return stored_hash == provided_hash
            
    except Exception as e:
        logger.error(f"密码验证错误: {e}")
    
    # 默认：直接比较（支持明文密码的用户）
    return stored_password == provided_password

def get_user_by_username(username):
    """从数据库获取用户信息"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            columns = ['id', 'username', 'email', 'password', 'role', 'created_at', 'updated_at', 'is_active', 'super_admin_approved', 'hardware_admin_approved', 'avatar']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return None

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录路由 - 后台API接口，不直接显示给用户
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 尝试从多种来源获取数据
        data = {}
        
        # 1. 尝试JSON格式
        try:
            json_data = request.get_json(force=False, silent=True)
            if json_data:
                data.update(json_data)
        except:
            pass
        
        # 2. 尝试表单格式
        if not data:
            form_data = request.form.to_dict()
            if form_data:
                data.update(form_data)
        
        # 3. 尝试查询参数
        if not data:
            args_data = request.args.to_dict()
            if args_data:
                data.update(args_data)
        
        # 4. 尝试原始数据
        if not data and request.data:
            try:
                import json
                data = eval(request.data.decode('utf-8'))
            except:
                pass
        
        logger.info(f"登录请求数据: {data}")
        
        if data and 'username' in data and 'password' in data:
            username = data.get('username')
            password = data.get('password')
            
            # 从数据库查询用户
            user = get_user_by_username(username)
            
            if user:
                # 验证密码
                if verify_password(user['password'], password):
                    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user['id']}"
                    logger.info(f"用户 {username} 登录成功")
                    return jsonify({
                        'success': True, 
                        'message': '登录成功', 
                        'session_id': session_id,
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'role': user['role'],
                            'email': user['email']
                        }
                    })
                else:
                    logger.warning(f"用户 {username} 密码错误")
                    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            else:
                logger.warning(f"用户 {username} 不存在")
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        return jsonify({'success': False, 'message': '参数错误: 缺少用户名或密码'}), 400
    
    # GET请求重定向到主页，登录页面由前端处理
    return redirect('/')

# 注册路由 - 后台API接口
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 尝试从多种来源获取数据
        data = {}
        
        try:
            json_data = request.get_json(force=False, silent=True)
            if json_data:
                data.update(json_data)
        except:
            pass
        
        if not data:
            data.update(request.form.to_dict())
        
        if data and 'username' in data and 'password' in data:
            # 创建用户
            import hashlib
            import base64
            hashed_password = base64.b64encode(hashlib.sha256(data['password'].encode()).digest()).decode()
            
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                    (data['username'], f"{data['username']}@example.com", hashed_password, 'user')
                )
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'message': '注册成功'})
            except Exception as e:
                logger.error(f"注册失败: {e}")
                return jsonify({'success': False, 'message': '注册失败'}), 500
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    # GET请求重定向到主页，注册页面由前端处理
    return redirect('/')

# 仪表板路由
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# 超级管理员仪表板
@app.route('/super_admin_dashboard')
def super_admin_dashboard():
    return render_template('super_admin_dashboard.html')



# 管理员中心
@app.route('/admin_center')
def admin_center():
    return render_template('admin_center.html')

# 智能仪表板（教师）
@app.route('/smart_dashboard')
def smart_dashboard():
    return render_template('smart_dashboard.html')

# 健康检查
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# 系统状态
@app.route('/api/system/status')
def system_status():
    return jsonify({'status': 'running', 'version': '4.5.5', 'timestamp': datetime.now().isoformat()})

# 用户信息API
@app.route('/api/user/<username>')
def get_user(username):
    user = get_user_by_username(username)
    if user:
        # 不返回密码
        user.pop('password', None)
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'message': '用户不存在'}), 404

# 调试路由
@app.route('/debug/routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'rule': str(rule),
            'endpoint': rule.endpoint,
            'methods': list(rule.methods)
        })
    return jsonify(routes)

# 在线考试页面路由
@app.route('/exam')
def exam_page():
    return render_template('exam_page.html')

# 考试系统路由
@app.route('/exam_system')
def exam_system():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE is_active = 1 ORDER BY name')
    exams = cursor.fetchall()
    
    exam_list = []
    for exam in exams:
        exam_list.append({
            'id': exam['id'],
            'name': exam['name'],
            'description': exam['description'],
            'duration': exam['duration'],
            'total_questions': exam['total_questions'],
            'passing_score': exam['passing_score'],
            'language': exam['language'],
            'difficulty_level': exam['difficulty_level'],
            'exam_type': exam['exam_type'],
            'audio_type': exam['audio_type']
        })
    
    conn.close()
    
    return render_template('exam_system.html', exams=exam_list)

# 获取考试列表API
@app.route('/api/exams', methods=['GET'])
def get_exams():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE is_active = 1 ORDER BY name')
    exams = cursor.fetchall()
    
    exam_list = []
    for exam in exams:
        exam_list.append({
            'id': exam['id'],
            'name': exam['name'],
            'description': exam['description'],
            'duration': exam['duration'],
            'total_questions': exam['total_questions'],
            'passing_score': exam['passing_score'],
            'language': exam['language'],
            'difficulty_level': exam['difficulty_level'],
            'exam_type': exam['exam_type'],
            'audio_type': exam['audio_type']
        })
    
    conn.close()
    
    return jsonify({'success': True, 'data': exam_list})

# 删除考试API
@app.route('/api/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    
    if not exam:
        conn.close()
        return jsonify({'success': False, 'message': '考试不存在'}), 404
    
    try:
        cursor.execute('DELETE FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
        cursor.execute('DELETE FROM ai_generated_questions WHERE exam_id = ?', (exam_id,))
        cursor.execute('DELETE FROM exam_sessions WHERE exam_id = ?', (exam_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '考试删除成功'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 获取考试题目API
@app.route('/api/exams/<int:exam_id>/questions', methods=['GET'])
def get_exam_questions(exam_id):
    from app.ai.exam_expert_generator import enhanced_exam_generator
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    conn.close()
    
    if not exam:
        return jsonify({'success': False, 'message': '考试不存在'}), 404
    
    language = exam['language'] if exam['language'] else '日语'
    difficulty = exam['difficulty_level'] if exam['difficulty_level'] else '中级'
    exam_type = exam['exam_type'] if exam['exam_type'] else 'standard'
    total_questions = exam['total_questions'] if exam['total_questions'] else 10
    voice_type = exam['audio_type'] if exam['audio_type'] else 'standard'
    
    questions = enhanced_exam_generator.generate_questions_with_audio(
        language=language,
        difficulty=difficulty,
        exam_type=exam_type,
        question_count=total_questions,
        voice_type=voice_type
    )
    
    return jsonify({'success': True, 'data': questions})

# 获取单个考试详情API
@app.route('/api/exams/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM t_a4394fa841fb07b4 WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    
    conn.close()
    
    if exam:
        exam_data = {
            'id': exam['id'],
            'name': exam['name'],
            'description': exam['description'],
            'duration': exam['duration'],
            'total_questions': exam['total_questions'],
            'passing_score': exam['passing_score'],
            'language': exam['language'],
            'difficulty_level': exam['difficulty_level'],
            'exam_type': exam['exam_type'],
            'audio_type': exam['audio_type']
        }
        return jsonify({'success': True, 'data': exam_data})
    else:
        return jsonify({'success': False, 'message': '考试不存在'}), 404

# 创建考试API
@app.route('/api/exams', methods=['POST'])
def create_exam():
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'message': '缺少考试名称'}), 400
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO t_a4394fa841fb07b4 
        (name, description, duration, total_questions, passing_score, is_active, language, difficulty_level, exam_type, audio_type)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
    ''', (
        data.get('name'),
        data.get('description', ''),
        data.get('duration', 60),
        data.get('total_questions', 50),
        data.get('passing_score', 60.0),
        data.get('language', '中文'),
        data.get('difficulty_level', '中级'),
        data.get('exam_type', 'standard'),
        data.get('audio_type')
    ))
    
    conn.commit()
    exam_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'message': '考试创建成功', 'exam_id': exam_id})

# 测试路由
@app.route('/test')
def test():
    return jsonify({'status': 'success', 'message': '系统运行正常'})

# ============================================
# 备份管理API
# ============================================
# 文件整理页面路由
@app.route('/file_organizer')
def file_organizer():
    return render_template('file_organizer.html')

@app.route('/backup_manager')
def backup_manager():
    import os
    from datetime import datetime
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_root = os.path.join(project_root, 'backups')
    iso_directory = os.path.join(backup_root, 'iso')
    db_backup_directory = os.path.join(backup_root, 'database')
    config_backup_directory = os.path.join(backup_root, 'config')
    
    os.makedirs(backup_root, exist_ok=True)
    os.makedirs(iso_directory, exist_ok=True)
    os.makedirs(db_backup_directory, exist_ok=True)
    os.makedirs(config_backup_directory, exist_ok=True)
    
    iso_files = []
    if os.path.exists(iso_directory):
        for f in os.listdir(iso_directory):
            if f.endswith('.iso'):
                filepath = os.path.join(iso_directory, f)
                filesize = os.path.getsize(filepath)
                size_str = f"{filesize / (1024 * 1024):.2f} MB"
                iso_files.append({'name': f, 'path': filepath, 'size': size_str})
    
    last_backup_time = '从未备份'
    backup_files = []
    if os.path.exists(backup_root):
        for root, dirs, files in os.walk(backup_root):
            for f in files:
                filepath = os.path.join(root, f)
                mtime = os.path.getmtime(filepath)
                backup_files.append((mtime, filepath))
        
        if backup_files:
            latest_mtime = max(f[0] for f in backup_files)
            last_backup_time = datetime.fromtimestamp(latest_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    total_backups = sum(len(files) for _, _, files in os.walk(backup_root))
    db_backups = len([f for f in os.listdir(db_backup_directory) if os.path.isfile(os.path.join(db_backup_directory, f))]) if os.path.exists(db_backup_directory) else 0
    
    total_size = 0
    for root, dirs, files in os.walk(backup_root):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    
    if total_size < 1024:
        size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.2f} KB"
    else:
        size_str = f"{total_size / (1024 * 1024):.2f} MB"
    
    backup_paths = {
        'backup_root': backup_root,
        'iso_directory': iso_directory,
        'db_backup_directory': db_backup_directory,
        'config_backup_directory': config_backup_directory,
        'project_root': project_root,
        'last_backup_time': last_backup_time
    }
    
    stats = {
        'total_backups': total_backups,
        'iso_count': len(iso_files),
        'total_size': size_str,
        'db_backups': db_backups
    }
    
    return render_template('backup_manager.html', 
                           backup_paths=backup_paths,
                           iso_files=iso_files,
                           stats=stats)

@app.route('/api/backup/create', methods=['GET'])
def create_backup():
    import os
    import shutil
    from datetime import datetime
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_root = os.path.join(project_root, 'backups')
    db_backup_directory = os.path.join(backup_root, 'database')
    config_backup_directory = os.path.join(backup_root, 'config')
    
    os.makedirs(db_backup_directory, exist_ok=True)
    os.makedirs(config_backup_directory, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    db_source = os.path.join(project_root, 'flask-app', 'mtscos.db')
    db_dest = os.path.join(db_backup_directory, f'mtscos_{timestamp}.db')
    if os.path.exists(db_source):
        shutil.copy2(db_source, db_dest)
    
    config_source = os.path.join(project_root, 'flask-app', 'config.py')
    config_dest = os.path.join(config_backup_directory, f'config_{timestamp}.py')
    if os.path.exists(config_source):
        shutil.copy2(config_source, config_dest)
    
    return jsonify({'success': True, 'message': '备份创建成功', 'timestamp': timestamp})

@app.route('/api/backup/create-iso', methods=['GET'])
def create_iso():
    return jsonify({'success': True, 'message': 'ISO镜像生成功能已预留，可通过工具如mkisofs实现'})

@app.route('/api/backup/clean', methods=['GET'])
def clean_backups():
    import os
    from datetime import datetime, timedelta
    
    backup_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    cutoff_date = datetime.now() - timedelta(days=30)
    deleted_count = 0
    
    for root, dirs, files in os.walk(backup_root):
        for f in files:
            filepath = os.path.join(root, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff_date:
                os.remove(filepath)
                deleted_count += 1
    
    return jsonify({'success': True, 'message': f'清理完成，共删除 {deleted_count} 个旧备份文件'})

# ============================================
# 文件整理和路径修复API
# ============================================
@app.route('/api/file/organize')
def organize_files():
    import subprocess
    result = subprocess.run(
        ['python3', 'file_organizer.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True,
        timeout=300
    )
    response = jsonify({
        'success': True,
        'message': '文件整理完成',
        'output': result.stdout
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/file/fix-paths')
def fix_paths():
    import subprocess
    result = subprocess.run(
        ['python3', 'path_fixer.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True
    )
    return jsonify({
        'success': True,
        'message': '路径修复完成',
        'output': result.stdout
    })

@app.route('/api/file/recommendations')
def get_fix_recommendations():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, description, action, priority, file_path, details, status
        FROM file_organization_log
        WHERE status = 'pending'
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            id DESC
        LIMIT 100
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    recommendations = []
    for row in rows:
        try:
            details = json.loads(row['details']) if row['details'] else {}
        except:
            details = {'raw': row['details']}
        recommendations.append({
            'type': row['type'],
            'description': row['description'],
            'action': row['action'],
            'priority': row['priority'],
            'file_path': row['file_path'],
            'details': details,
            'status': row['status']
        })
    
    return jsonify({
        'success': True,
        'count': len(recommendations),
        'recommendations': recommendations
    })

@app.route('/api/file/categories')
def get_file_categories():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category, COUNT(*) as count, SUM(file_size) as total_size
        FROM file_category_index
        WHERE status = 'active'
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    categories = []
    for row in rows:
        total_size = row['total_size'] or 0
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        
        categories.append({
            'name': row['category'],
            'file_count': row['count'],
            'total_size': size_str
        })
    
    return jsonify({
        'success': True,
        'categories': categories
    })

# ============================================
# AI考试系统API
# ============================================

# 开始考试会话
@app.route('/api/exam/start', methods=['POST'])
def start_exam_api():
    data = request.get_json()
    exam_id = data.get('exam_id')
    user_id = data.get('user_id', 1)  # 默认用户ID
    
    if not exam_id:
        return jsonify({'success': False, 'message': '缺少考试ID'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.start_exam_session(exam_id, user_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'开始考试失败: {str(e)}'}), 500

# 提交答题
@app.route('/api/exam/answer', methods=['POST'])
def submit_answer_api():
    data = request.get_json()
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')
    
    if not session_id or question_id is None or user_answer is None:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.submit_exam_answer(
            session_id, question_id, user_answer, correct_answer
        )
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交答案失败: {str(e)}'}), 500

# 结束考试并获取AI分析
@app.route('/api/exam/finish', methods=['POST'])
def finish_exam_api():
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': '缺少会话ID'}), 400
    
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.finish_exam_session(session_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'结束考试失败: {str(e)}'}), 500

# 获取AI教师反馈
@app.route('/api/exam/teacher-feedback', methods=['POST'])
def get_teacher_feedback_api():
    data = request.get_json()
    user_id = data.get('user_id', 1)
    exam_id = data.get('exam_id')
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'message': '缺少会话ID'}), 400
    
    try:
        from app.ai.smart_teacher_ai import smart_teacher
        result = smart_teacher.generate_personalized_feedback(user_id, exam_id, session_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取反馈失败: {str(e)}'}), 500

# 获取用户考试历史
@app.route('/api/exam/history/<int:user_id>', methods=['GET'])
def get_exam_history_api(user_id):
    try:
        from app.ai.exam_system_integrator import exam_system_integrator
        result = exam_system_integrator.get_user_exam_history(user_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取历史失败: {str(e)}'}), 500

# AI生成题目测试
@app.route('/api/test-ai-questions', methods=['GET'])
def test_ai_questions_api():
    language = request.args.get('language', '日语')
    difficulty = request.args.get('difficulty', '初级')
    exam_type = request.args.get('type', 'standard')
    count = int(request.args.get('count', 5))
    
    try:
        from app.ai.exam_expert_generator import enhanced_exam_generator
        questions = enhanced_exam_generator.generate_questions(
            language, difficulty, exam_type, count
        )
        
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成题目失败: {str(e)}'}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8888, help='端口号')
    args = parser.parse_args()

    print(f"[INFO] 启动MTSCOS AI应用...")
    print(f"[INFO] 数据库路径: {DATABASE_PATH}")
    print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)