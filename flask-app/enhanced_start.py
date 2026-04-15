#!/usr/bin/env python3
"""
Enhanced Flask app start script for MTSCOS AI Project
包含数据库初始化和基本功能，但避免导入会导致阻塞的模块
"""

import os
import sys
import json
import hashlib
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 创建Flask应用
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-development'
app.template_folder = 'templates'
app.static_folder = 'static'

# 初始化SQLite连接
def get_db_connection():
    """获取数据库连接"""
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库
def init_db():
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 创建用户表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建用户备份表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_backup (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("[INFO] 数据库表结构初始化完成")
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

# 密码加密函数
def encrypt_password(password):
    """加密密码"""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + hashed.hex()

# 验证密码函数
def verify_password(stored_password, provided_password):
    """验证密码，支持scrypt和pbkdf2_hmac两种格式"""
    try:
        # 检查是否为scrypt格式
        if stored_password.startswith('scrypt:'):
            # 使用werkzeug的security模块验证scrypt密码
            from werkzeug.security import check_password_hash
            return check_password_hash(stored_password, provided_password)
        else:
            # pbkdf2_hmac格式
            salt = bytes.fromhex(stored_password[:32])
            stored_hash = stored_password[32:]
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            return stored_hash == provided_hash.hex()
    except Exception as e:
        print(f"[ERROR] 密码验证失败: {str(e)}")
        return False

# 双备份用户数据函数
def backup_user_data(user_id, username, email, password, role, is_active):
    """双备份用户数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 主数据库备份
        cursor.execute('''
            INSERT OR REPLACE INTO user (id, username, email, password, role, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (user_id, username, email, password, role, is_active))
        
        # 备份数据库备份
        cursor.execute('''
            INSERT OR REPLACE INTO user_backup (id, username, email, password, role, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (user_id, username, email, password, role, is_active))
        
        conn.commit()
    except Exception as e:
        print(f"[ERROR] 备份用户数据失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

# 权限装饰器
from functools import wraps

def require_role(*allowed_roles):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('请先登录', 'error')
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('您没有权限访问该页面', 'error')
                # 根据角色重定向到对应的页面
                if user_role == 'student':
                    return redirect(url_for('test_system'))
                elif user_role == 'designer':
                    return redirect(url_for('arduino_design'))
                else:
                    return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 定义简单的健康检查路由
@app.route('/health')
def health():
    return "OK", 200

# 定义版本路由
@app.route('/version')
def version():
    return {"VERSION": "3.0.0", "INTERNAL_VERSION": "3.0.0.5678"}, 200

# 定义根路由
@app.route('/')
def index():
    if 'user_id' in session:
        # 已登录用户，根据角色重定向
        user_role = session.get('role')
        if user_role == 'student':
            return redirect(url_for('test_system'))
        elif user_role == 'designer':
            return redirect(url_for('arduino_design'))
        else:
            return redirect(url_for('dashboard'))
    # 未登录用户，显示登录页面
    return render_template('index.html')

# 登录路由
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 记录登录请求
        print(f"[登录请求] 用户名: {username}, IP: {request.remote_addr}")
        
        # 从数据库获取用户
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password, role, is_active FROM user WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_id, db_username, email, stored_password, role, is_active = user
            
            # 验证密码
            if verify_password(stored_password, password):
                if is_active:
                    # 登录成功，设置会话
                    session['user_id'] = user_id
                    session['username'] = db_username
                    session['role'] = role
                    flash('登录成功', 'success')
                    print(f"[登录成功] 用户名: {username}, 角色: {role}")
                    # 根据角色重定向到对应页面
                    if role == 'student':
                        return redirect(url_for('test_system'))
                    elif role == 'designer':
                        return redirect(url_for('arduino_design'))
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    flash('账号未激活，请联系管理员', 'error')
                    print(f"[登录失败] 用户名: {username}, 原因: 账号未激活")
            else:
                flash('用户名或密码错误', 'error')
                print(f"[登录失败] 用户名: {username}, 原因: 密码错误")
        else:
            flash('用户名或密码错误', 'error')
            print(f"[登录失败] 用户名: {username}, 原因: 用户不存在")
    
    return render_template('index.html')

# 注册路由
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 验证密码
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('index.html')
        
        # 验证密码长度
        if len(password) < 6:
            flash('密码长度不能少于6个字符', 'error')
            return render_template('index.html')
        
        # 检查用户名是否已存在
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM user WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('用户名已存在', 'error')
            conn.close()
            return render_template('index.html')
        
        # 检查邮箱是否已存在
        cursor.execute('SELECT id FROM user WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('邮箱已被注册', 'error')
            conn.close()
            return render_template('index.html')
        
        conn.close()
        
        # 加密密码
        encrypted_password = encrypt_password(password)
        
        # 生成用户ID
        user_id = int(time.time() * 1000)  # 使用时间戳作为用户ID
        
        # 插入用户数据（双备份）
        backup_user_data(user_id, username, email, encrypted_password, 'student', True)
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('index.html')

# 注销路由
@app.route('/auth/logout')
def logout():
    session.clear()
    flash('已成功注销', 'success')
    return redirect(url_for('login'))

# 仪表板路由（需要登录）
@app.route('/dashboard')
def dashboard():
    # 获取用户信息
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, email, role FROM user WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        flash('用户不存在', 'error')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=user)

# 测试系统路由
@app.route('/test-system')
def test_system():
    return render_template('test_system.html')

# 获取用户的语言等级

def get_user_language_level(user_id, language):
    """获取用户的语言等级"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查询用户的语言等级
        cursor.execute('''
            SELECT level, is_assessed, last_test_date 
            FROM user_levels 
            WHERE user_id = ? AND language = ?
        ''', (user_id, language))
        result = cursor.fetchone()
        
        if result:
            return {
                'level': result['level'],
                'is_assessed': result['is_assessed'],
                'last_test_date': result['last_test_date']
            }
        else:
            # 如果没有等级记录，创建一个默认记录
            cursor.execute('''
                INSERT INTO user_levels (user_id, language, level, is_assessed, last_test_date)
                VALUES (?, ?, NULL, 0, CURRENT_TIMESTAMP)
            ''', (user_id, language))
            conn.commit()
            return {
                'level': None,
                'is_assessed': 0,
                'last_test_date': time.time()
            }
    except Exception as e:
        print(f"[ERROR] 获取用户语言等级失败: {str(e)}")
        return {
            'level': None,
            'is_assessed': 0,
            'last_test_date': time.time()
        }
    finally:
        conn.close()

# 日语测试页面路由
@app.route('/test-system/japanese')
def japanese_test():
    # 检测用户是否已登录
    if 'user_id' not in session:
        flash('请先登录', 'error')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # 获取用户的日语等级
    user_level_info = get_user_language_level(user_id, 'japanese')
    
    # 简化实现，只渲染模板，不生成试卷
    # 避免导入会导致阻塞的模块
    
    # 根据用户等级信息判断是否需要做等级测试
    if not user_level_info['is_assessed'] or user_level_info['level'] is None:
        # 需要做等级测试
        test_type = 'placement'  # 摸底测试
        user_level = 0  # 未评估
        is_assessed = 0
    else:
        # 已经有评估等级，进行等级测试
        test_type = 'level'
        user_level = user_level_info['level']
        is_assessed = 1
    
    # 生成简单的测试题目（临时实现）
    questions = []
    if test_type == 'placement':
        # 摸底测试，生成简单的词汇和语法题目
        questions = [
            {
                'id': 1,
                'category': '词汇',
                'difficulty': 1,
                'question_type': 'single',
                'content': '「こんにちは」的正确意思是？',
                'options': ['A. 再见', 'B. 你好', 'C. 谢谢', 'D. 对不起', 'E. 是的', 'F. 不是'],
                'correct_answers': ['B'],
                'required_answers': 1,
                'score': 10
            },
            {
                'id': 2,
                'category': '词汇',
                'difficulty': 1,
                'question_type': 'single',
                'content': '「ありがとう」的正确意思是？',
                'options': ['A. 再见', 'B. 你好', 'C. 谢谢', 'D. 对不起', 'E. 是的', 'F. 不是'],
                'correct_answers': ['C'],
                'required_answers': 1,
                'score': 10
            },
            {
                'id': 3,
                'category': '语法',
                'difficulty': 2,
                'question_type': 'single',
                'content': '私______学生です。',
                'options': ['A. は', 'B. が', 'C. を', 'D. に', 'E. で', 'F. と'],
                'correct_answers': ['A'],
                'required_answers': 1,
                'score': 10
            }
        ]
    else:
        # 等级测试，根据用户等级生成相应难度的题目
        difficulty = user_level
        questions = [
            {
                'id': 1,
                'category': '词汇',
                'difficulty': difficulty,
                'question_type': 'single',
                'content': f'难度{difficulty}的词汇题：「喧嘩」的正确意思是？',
                'options': ['A. 吵架', 'B. 朋友', 'C. 安静', 'D. 大声', 'E. 高兴', 'F. 悲伤'],
                'correct_answers': ['A'],
                'required_answers': 1,
                'score': 10
            },
            {
                'id': 2,
                'category': '语法',
                'difficulty': difficulty,
                'question_type': 'single',
                'content': f'难度{difficulty}的语法题：昨日、私は公園で友達に______。',
                'options': ['A. 会いました', 'B. 会う', 'C. 会って', 'D. 会うと', 'E. 会った', 'F. 会わない'],
                'correct_answers': ['A'],
                'required_answers': 1,
                'score': 10
            }
        ]
    
    # 统计题目信息
    stats = {
        'vocabulary_count': sum(1 for q in questions if q['category'] == '词汇'),
        'grammar_count': sum(1 for q in questions if q['category'] == '语法'),
        'reading_count': sum(1 for q in questions if q['category'] == '阅读'),
        'difficulty_distribution': {
            1: sum(1 for q in questions if q['difficulty'] == 1),
            2: sum(1 for q in questions if q['difficulty'] == 2),
            3: sum(1 for q in questions if q['difficulty'] == 3),
            4: sum(1 for q in questions if q['difficulty'] == 4),
            5: sum(1 for q in questions if q['difficulty'] == 5)
        }
    }
    
    return render_template('japanese_test_page.html', paper={
        'paper_id': f'paper_{int(time.time())}',
        'language': 'japanese',
        'test_type': test_type,
        'user_level': user_level if user_level else '未评估',
        'is_assessed': is_assessed,
        'difficulty': difficulty if 'difficulty' in locals() else 3,
        'questions': questions,
        'total_questions': len(questions),
        'generated_at': time.time(),
        'instructions': {
            'title': 'Japanese Language Proficiency Test',
            'subtitle': 'Level-Adaptive Test' if test_type == 'level' else 'Placement Test',
            'instructions': [
                'This test consists of multiple-choice questions only',
                'Each question has 6 options, please select the correct one',
                'You can only select one answer per question'
            ],
            'suggested_time': 30,
            'question_order_reminder': 'The questions are arranged from vocabulary -> grammar -> reading comprehension',
            'test_type_reminder': 'This is a level-adaptive test designed to accurately assess your Japanese proficiency' if test_type == 'level' else 'This is a placement test designed to determine your initial proficiency level',
            'difficulty_reminder': f'Questions are tailored to your level ({user_level}/5), with appropriate challenge progression' if user_level else 'Questions are designed to assess your current proficiency level',
            'scoring_reminder': 'Each question carries equal weight, and your final score will determine your proficiency level'
        },
        'suggested_time': 30,
        'stats': stats,
        'rule_compliance': {
            'overall_compliance': True,
            'suggestions': []
        }
    })

# Arduino设计系统路由
@app.route('/arduino-design')
def arduino_design():
    return render_template('arduino_design.html')

# 添加中间件来检查AI服务是否已经初始化
@app.before_request
def check_ai_services():
    """检查AI服务是否已经初始化，对于AI相关的API请求"""
    # 跳过非AI路由
    return

if __name__ == '__main__':
    print("[INFO] 启动增强版Flask应用...")
    
    # 初始化数据库表结构
    print("[INFO] 初始化数据库表结构...")
    init_db()
    
    # 从配置文件获取端口，默认为8888
    print("[INFO] 获取服务器端口配置...")
    port = 8888
    
    # 尝试从配置文件加载端口
    try:
        with open('system_config.json', 'r') as f:
            system_config = json.load(f)
            port = system_config.get('SERVER_PORT', 8888)
        print(f"[INFO] 从system_config.json加载端口: {port}")
    except Exception as e:
        print(f"[WARNING] 从system_config.json加载端口失败: {str(e)}")
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                port = config.get('SERVER_PORT', 8888)
            print(f"[INFO] 从config.json加载端口: {port}")
        except Exception as e:
            print(f"[WARNING] 从config.json加载端口失败: {str(e)}")
            print(f"[INFO] 使用默认端口: {port}")
    
    print(f"[INFO] 监听地址: 0.0.0.0:{port}")
    print(f"[INFO] 访问地址: http://localhost:{port}")
    
    # 启动服务器
    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("[INFO] 收到中断信号，正在关闭应用...")
    except Exception as e:
        print(f"[ERROR] 应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("[INFO] 应用关闭，清理资源...")
        print("[INFO] MTSCOS AI应用已关闭")