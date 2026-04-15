#!/usr/bin/env python3
"""
极简启动脚本，只启动Flask应用并包含所有必要路由
"""

from flask import Flask, render_template, request, jsonify, session, make_response, flash, redirect, url_for
import os
import secrets
import time
import uuid
import sqlite3
import hashlib
import base64
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)

# 设置模板和静态文件夹
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')

if os.path.exists(templates_dir):
    app.template_folder = templates_dir
    print(f"[INFO] 使用模板文件夹: {templates_dir}")
else:
    print(f"[WARNING] 模板文件夹不存在: {templates_dir}")

if os.path.exists(static_dir):
    app.static_folder = static_dir
    print(f"[INFO] 使用静态文件夹: {static_dir}")
else:
    print(f"[WARNING] 静态文件夹不存在: {static_dir}")

# 配置Flask应用
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = secrets.token_urlsafe(64)
app.config['DATABASE'] = 'app.db'

# 监控AI - 前后端交互信息监控
class InteractionMonitor:
    """交互监控AI，用于监控前后端交互信息"""
    
    def __init__(self):
        self.request_count = 0
        self.start_time = datetime.now()
    
    def log_request(self, request):
        """记录请求信息"""
        self.request_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_ip = request.remote_addr
        method = request.method
        path = request.path
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # 记录请求参数
        if method == 'GET':
            params = dict(request.args)
        elif method == 'POST':
            params = dict(request.form)
        else:
            params = {}
        
        print(f"\033[94m[监控AI] {timestamp} | 请求 #{self.request_count} | {client_ip} | {method} {path}")
        print(f"\033[92m[监控AI]   用户代理: {user_agent}")
        print(f"\033[92m[监控AI]   请求参数: {params}")
    
    def log_response(self, response):
        """记录响应信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_code = response.status_code
        content_length = response.headers.get('Content-Length', 'Unknown')
        
        print(f"\033[94m[监控AI] {timestamp} | 响应 | 状态码: {status_code} | 内容长度: {content_length}")
    
    def log_error(self, error):
        """记录错误信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\033[91m[监控AI] {timestamp} | 错误 | {error}")

# 创建监控AI实例
monitor_ai = InteractionMonitor()

# 添加请求监控钩子
@app.before_request
def before_request_hook():
    """请求前钩子，记录请求信息"""
    monitor_ai.log_request(request)

# 添加响应监控钩子
@app.after_request
def after_request_hook(response):
    """响应后钩子，记录响应信息"""
    monitor_ai.log_response(response)
    return response

# 添加错误监控钩子
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理，记录错误信息"""
    monitor_ai.log_error(str(e))
    return str(e), 500

# 定义根路由
@app.route('/')
def index():
    """根路由，实现基于角色的重定向
    学生：直接跳转到语言测试系统
    管理员、超级管理员、硬件管理员：跳转到仪表盘
    """
    try:
        # 检查用户是否已登录
        if session.get('logged_in', False) and session.get('user_id'):
            try:
                # 连接数据库获取最新用户信息
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id, username, email, password, role, is_active FROM users WHERE id = ?',
                    (session['user_id'],)
                )
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    user_id, username, email, hashed_password, role, is_active = user
                    
                    # 更新会话信息
                    session['user_id'] = user_id
                    session['username'] = username
                    session['email'] = email
                    session['role'] = role
                    session['logged_in'] = is_active == 1
                    
                    # 如果用户已被禁用，清除会话
                    if is_active != 1:
                        session.clear()
                        return render_template(
                            'index.html', 
                            logged_in=False, 
                            error="该账户已被禁用，请联系管理员"
                        )
                    
                    # 基于角色的重定向
                    if role == 'student':
                        # 学生直接跳转到语言测试系统
                        return redirect(url_for('language_test'))
                    elif role in ['admin', 'super_admin', 'hardware_admin']:
                        # 管理员跳转到仪表盘
                        return render_template(
                            'index.html',
                            logged_in=True,
                            username=username,
                            user_id=user_id,
                            email=email,
                            role=role,
                            session_id=session.get('session_id', '')
                        )
                    else:
                        # 其他角色默认跳转到仪表盘
                        return render_template(
                            'index.html',
                            logged_in=True,
                            username=username,
                            user_id=user_id,
                            email=email,
                            role=role,
                            session_id=session.get('session_id', '')
                        )
                else:
                    # 用户不存在，清除会话
                    session.clear()
            except Exception as db_error:
                print(f"[ERROR] 从数据库获取用户信息失败: {db_error}")
        
        # 默认显示登录页面
        return render_template(
            'index.html',
            logged_in=False,
            username='',
            user_id='',
            email='',
            role='',
            session_id=''
        )
    except Exception as e:
        print(f"[ERROR] 渲染index.html失败: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/health')
def health():
    """健康检查路由"""
    try:
        # 检查数据库连接
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        conn.close()
        
        # 检查JSON同步服务状态
        json_sync_status = "running" if hasattr(app, 'json_sync_service') else "stopped"
        
        return jsonify({
            "status": "OK",
            "version": "3.0.0",
            "database": "connected",
            "json_sync": json_sync_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": str(e),
            "version": "3.0.0",
            "database": "disconnected",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/version')
def version():
    return jsonify({"VERSION": "3.0.0"}), 200

@app.route('/system/monitor')
def system_monitor():
    """系统监控路由"""
    try:
        from system_optimization import SystemOptimizer
        optimizer = SystemOptimizer()
        resource_stats = optimizer.monitor_system_resources()
        
        return jsonify({
            "status": "OK",
            "resource_stats": resource_stats,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/system/optimize')
def system_optimize():
    """系统优化路由"""
    try:
        from system_optimization import SystemOptimizer
        optimizer = SystemOptimizer()
        result = optimizer.run_full_optimization()
        
        return jsonify({
            "status": "OK" if result else "PARTIAL",
            "message": "系统优化完成" if result else "系统优化部分项目失败",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # 简单的输入验证
        if not username or not password:
            return "用户名和密码都是必填的", 400
        
        try:
            # 连接数据库
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            # 根据用户名查询用户
            cursor.execute('SELECT id, username, email, password, role, is_active FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            # 如果用户名不存在，尝试获取第一个用户（兼容旧逻辑）
            if not user:
                cursor.execute('SELECT id, username, email, password, role, is_active FROM users LIMIT 1')
                user = cursor.fetchone()
            
            conn.close()
            
            if user:
                user_id, db_username, email, hashed_password, role, is_active = user
                
                # 密码验证逻辑 - 简化版，只检查密码是否正确
                password_valid = False
                
                try:
                    # 尝试直接比较密码（如果数据库中存储的是明文密码）
                    if password == hashed_password:
                        password_valid = True
                    else:
                        # 尝试base64格式验证
                        decoded = base64.b64decode(hashed_password)
                        if len(decoded) == 64:  # 32字节salt + 32字节hash
                            salt = decoded[:32]
                            stored_hash = decoded[32:]
                            
                            # 计算提供密码的哈希值
                            hashed = hashlib.pbkdf2_hmac(
                                'sha256',
                                password.encode('utf-8'),
                                salt,
                                100000
                            )
                            
                            if hashed == stored_hash:
                                password_valid = True
                        # 如果base64验证失败，尝试hex格式
                        else:
                            # 尝试hex格式验证
                            if len(hashed_password) == 96:  # 16字节salt + 32字节hash（hex格式）
                                salt_hex = hashed_password[:32]
                                hash_hex = hashed_password[32:96]
                                salt = bytes.fromhex(salt_hex)
                                stored_hash = bytes.fromhex(hash_hex)
                                
                                # 计算提供密码的哈希值
                                hashed = hashlib.pbkdf2_hmac(
                                    'sha256',
                                    password.encode('utf-8'),
                                    salt,
                                    100000
                                )
                                
                                if hashed == stored_hash:
                                    password_valid = True
                except Exception as e:
                    print(f"密码验证错误: {e}")
                
                if password_valid:
                    # 从数据库获取最新信息，确保登录后显示的信息与数据库完全匹配
                    try:
                        # 再次查询数据库，获取最新的用户状态
                        conn = sqlite3.connect('app.db')
                        cursor = conn.cursor()
                        cursor.execute(
                            'SELECT id, username, email, password, role, is_active FROM users WHERE id = ?',
                            (user_id,)
                        )
                        latest_user = cursor.fetchone()
                        conn.close()
                        
                        if latest_user:
                            user_id, db_username, email, hashed_password, role, is_active = latest_user
                            
                            # 设置会话，使用数据库中的最新信息
                            session['user_id'] = user_id
                            session['username'] = db_username
                            session['email'] = email
                            session['role'] = role
                            session['logged_in'] = is_active == 1
                            session['session_id'] = str(uuid.uuid4())
                            
                            # 如果用户已被禁用，返回错误信息
                            if is_active != 1:
                                session.clear()
                                return render_template(
                                    'index.html', 
                                    logged_in=False, 
                                    error="该账户已被禁用，请联系管理员"
                                )
                        else:
                            # 用户不存在于数据库中
                            return render_template(
                                'index.html', 
                                logged_in=False, 
                                error="用户不存在"
                            )
                    except Exception as e:
                        print(f"[ERROR] 登录时获取最新用户信息失败: {e}")
                        # 使用之前获取的信息作为备选
                        session['user_id'] = user_id
                        session['username'] = db_username
                        session['email'] = email
                        session['role'] = role
                        session['logged_in'] = True
                        session['session_id'] = str(uuid.uuid4())
                    
                    # 登录成功后直接根据角色重定向
                    if role == 'student':
                        # 学生直接跳转到语言测试系统
                        return redirect(url_for('language_test'))
                    else:
                        # 其他角色跳转到仪表盘
                        return redirect(url_for('index'))
                else:
                    return render_template('index.html', logged_in=False, error="密码不正确")
            else:
                # 如果没有用户，创建一个默认用户
                print("没有找到用户，创建默认用户...")
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                
                # 创建默认用户，密码为明文"password"
                cursor.execute('''
                    INSERT INTO users (username, password, email, role, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'password', 'admin@example.com', 'admin', 1))
                conn.commit()
                conn.close()
                
                # 再次尝试登录
                if password == 'password':
                    session['user_id'] = 1
                    session['username'] = 'admin'
                    session['email'] = 'admin@example.com'
                    session['role'] = 'admin'
                    session['logged_in'] = True
                    session['session_id'] = str(uuid.uuid4())
                    return render_template('index.html', logged_in=True, username='admin')
                else:
                    return render_template('index.html', logged_in=False, error="密码不正确")
        except Exception as e:
            print(f"登录错误: {e}")
            return render_template('index.html', logged_in=False, error=f"登录时发生错误: {str(e)}")
    # GET请求，渲染登录页面
    return render_template('index.html', logged_in=session.get('logged_in', False), username=session.get('username', ''))

# 生成选项内容的辅助函数
def generate_option_content(question_content, correct_answer, is_correct, language):
    """根据题目内容生成智能选项"""
    # 英语选项生成
    if language == 'english':
        # 语法题目
        if 'grammar' in question_content.lower() or 'verb' in question_content.lower() or 'sentence' in question_content.lower():
            if is_correct:
                # 正确的语法选项
                grammar_correct = [
                    "She goes to school every day.",
                    "They are playing football.",
                    "I have eaten breakfast.",
                    "He will come tomorrow.",
                    "We should study hard.",
                    "The book is on the table.",
                    "She sings beautifully.",
                    "I like coffee but my brother prefers tea.",
                    "What is your name?",
                    "This is the best book I've ever read."
                ]
                return random.choice(grammar_correct)
            else:
                # 错误的语法选项（相似但错误）
                grammar_incorrect = [
                    "She go to school every day.",
                    "They is playing football.",
                    "I have ate breakfast.",
                    "He will comes tomorrow.",
                    "We should to study hard.",
                    "The book is in the table.",
                    "She sings beautiful.",
                    "I like coffee but my brother prefer tea.",
                    "What your name is?",
                    "This is the better book I've ever read."
                ]
                return random.choice(grammar_incorrect)
        # 词汇题目
        elif 'vocabulary' in question_content.lower() or 'meaning' in question_content.lower() or 'synonym' in question_content.lower():
            if is_correct:
                # 正确的词汇选项
                vocab_correct = [
                    "happy",
                    "big",
                    "beautiful",
                    "quick",
                    "smart",
                    "strong",
                    "kind",
                    "brave",
                    "honest",
                    "friendly"
                ]
                return random.choice(vocab_correct)
            else:
                # 错误的词汇选项（相似但错误）
                vocab_incorrect = [
                    "happpy",
                    "bigg",
                    "beutiful",
                    "quik",
                    "smar",
                    "stronk",
                    "kinde",
                    "braive",
                    "honst",
                    "freindly"
                ]
                return random.choice(vocab_incorrect)
        # 其他题目
        else:
            if is_correct:
                return f"{correct_answer}: Correct answer"
            else:
                return f"{generate_similar_word(correct_answer)}: Incorrect answer"
    # 日语选项生成
    else:  # japanese
        # 语法题目
        if '文法' in question_content or '動詞' in question_content or '文' in question_content:
            if is_correct:
                # 正确的语法选项
                grammar_correct = [
                    "彼女は毎日学校へ行きます。",
                    "彼らはサッカーをしています。",
                    "私は朝ごはんを食べました。",
                    "彼は明日来ます。",
                    "私たちは一生懸命勉強すべきです。",
                    "本は机の上にあります。",
                    "彼女は美しく歌います。",
                    "私はコーヒーが好きですが、弟は紅茶が好きです。",
                    "お名前は何ですか？",
                    "これは私が今まで読んだ中で一番いい本です。"
                ]
                return random.choice(grammar_correct)
            else:
                # 错误的语法选项（相似但错误）
                grammar_incorrect = [
                    "彼女は毎日学校へ行くます。",
                    "彼らはサッカーをしますている。",
                    "私は朝ごはんを食べたました。",
                    "彼は明日来るます。",
                    "私たちは一生懸命勉強するべき。",
                    "本は机の上であります。",
                    "彼女は美しい歌います。",
                    "私はコーヒーが好きですが、弟は紅茶が好きですが。",
                    "お名前は何ですか？は？",
                    "これは私が今まで読んだ中で一番いい本ですが。"
                ]
                return random.choice(grammar_incorrect)
        # 词汇题目
        elif '語彙' in question_content or '意味' in question_content or '類義語' in question_content:
            if is_correct:
                # 正确的词汇选项
                vocab_correct = [
                    "嬉しい",
                    "大きい",
                    "美しい",
                    "速い",
                    "賢い",
                    "強い",
                    "親切な",
                    "勇敢な",
                    "正直な",
                    "友好的な"
                ]
                return random.choice(vocab_correct)
            else:
                # 错误的词汇选项（相似但错误）
                vocab_incorrect = [
                    "嬉しいい",
                    "大きいい",
                    "美しいい",
                    "速いい",
                    "賢いい",
                    "強いい",
                    "親切なな",
                    "勇敢なな",
                    "正直なな",
                    "友好的なな"
                ]
                return random.choice(vocab_incorrect)
        # 其他题目
        else:
            if is_correct:
                return f"{correct_answer}: 正しい答え"
            else:
                return f"{generate_similar_word(correct_answer, is_japanese=True)}: 誤った答え"

# 生成相似词的辅助函数
def generate_similar_word(correct_word, is_japanese=False):
    """生成与正确答案相似的混淆词"""
    if is_japanese:
        # 日语混淆词，根据正确答案的长度和结构生成相似的错误词
        if len(correct_word) <= 2:
            # 短词处理
            return correct_word + random.choice(['a', 'i', 'u', 'e', 'o', 'っ', 'ん'])
        else:
            # 长词处理：替换一个字符，添加一个字符，或删除一个字符
            operations = ['replace', 'add', 'remove']
            operation = random.choice(operations)
            
            if operation == 'replace':
                # 替换一个字符
                index = random.randint(0, len(correct_word) - 1)
                replacement_chars = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
                return correct_word[:index] + random.choice(replacement_chars) + correct_word[index+1:]
            elif operation == 'add':
                # 添加一个字符
                index = random.randint(0, len(correct_word))
                addition_chars = ['あ', 'い', 'う', 'え', 'お', 'っ', 'ん']
                return correct_word[:index] + random.choice(addition_chars) + correct_word[index:]
            else:  # remove
                # 删除一个字符
                if len(correct_word) > 1:
                    index = random.randint(0, len(correct_word) - 1)
                    return correct_word[:index] + correct_word[index+1:]
                else:
                    return correct_word
    else:
        # 英语混淆词，根据正确答案的长度和结构生成相似的错误词
        if len(correct_word) <= 3:
            # 短词处理
            return correct_word + random.choice(['a', 'e', 'i', 'o', 'u', 's', 't', 'r'])
        else:
            # 长词处理：替换一个字符，添加一个字符，或删除一个字符
            operations = ['replace', 'add', 'remove']
            operation = random.choice(operations)
            
            if operation == 'replace':
                # 替换一个字符
                index = random.randint(0, len(correct_word) - 1)
                replacement_chars = ['a', 'e', 'i', 'o', 'u', 's', 't', 'r', 'n', 'l']
                return correct_word[:index] + random.choice(replacement_chars) + correct_word[index+1:]
            elif operation == 'add':
                # 添加一个字符
                index = random.randint(0, len(correct_word))
                addition_chars = ['a', 'e', 'i', 'o', 'u', 's', 't', 'r', 'n', 'l']
                return correct_word[:index] + random.choice(addition_chars) + correct_word[index:]
            else:  # remove
                # 删除一个字符
                if len(correct_word) > 2:
                    index = random.randint(0, len(correct_word) - 1)
                    return correct_word[:index] + correct_word[index+1:]
                else:
                    return correct_word

# 自动扩充题库功能
def auto_expand_question_bank(min_questions=1000):
    """自动扩充题库，确保题库至少有min_questions道题目"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查当前题库数量
        cursor.execute('SELECT COUNT(*) FROM questions')
        current_count = cursor.fetchone()[0]
        
        print(f"[考试AI] 当前题库数量: {current_count}，目标数量: {min_questions}")
        
        # 如果数量不足，自动生成新题目
        if current_count < min_questions:
            # 需要生成的题目数量
            need_to_generate = min_questions - current_count
            print(f"[考试AI] 开始自动生成 {need_to_generate} 道新题目...")
            
            # 获取现有题目类型和难度
            cursor.execute('SELECT DISTINCT question_type FROM questions')
            question_types = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT id FROM question_banks')
            question_bank_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT id FROM question_levels')
            level_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT id FROM question_sections')
            section_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT id FROM question_difficulties')
            difficulty_ids = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT id, language_code FROM question_languages')
            languages = cursor.fetchall()
            language_ids = [lang[0] for lang in languages]
            language_codes = {lang[0]: lang[1] for lang in languages}
            
            # 如果没有获取到任何数据，使用默认值
            if not question_bank_ids:
                question_bank_ids = [1]
            if not level_ids:
                level_ids = [1]
            if not section_ids:
                section_ids = [1]
            if not difficulty_ids:
                difficulty_ids = [1]
            if not language_ids:
                language_ids = [1]
                language_codes = {1: 'english'}
            if not question_types:
                question_types = ['single_choice']
            
            # 语言特定的题目模板
            question_templates = {
                'english': {
                    'grammar': [
                        "Which of the following sentences is grammatically correct?",
                        "Choose the correct form of the verb to complete the sentence: She _______ to school every day.",
                        "Select the proper preposition: The book is _______ the table.",
                        "Identify the correct article: I saw _______ interesting movie last night.",
                        "Choose the right adjective: This is the _______ book I've ever read.",
                        "Which pronoun correctly completes the sentence: John and _______ went to the park.",
                        "Select the correct adverb: She sings _______.",
                        "Choose the right conjunction: I like coffee _______ my brother prefers tea.",
                        "Identify the correct sentence structure.",
                        "Which of the following is a correctly formed question?"
                    ],
                    'vocabulary': [
                        "What is the synonym of 'happy'?",
                        "Choose the correct antonym for 'big'.",
                        "Select the word that best completes the sentence: The weather is very _______ today.",
                        "What does the word 'beautiful' mean?",
                        "Identify the correct spelling of the following word.",
                        "Choose the right word to fill in the blank: I need to _______ my homework.",
                        "Which of the following is a noun?",
                        "Select the verb from the options below.",
                        "What is the past tense of 'go'?",
                        "Choose the correct plural form of 'child'."
                    ]
                },
                'japanese': {
                    'grammar': [
                        "次の文の文法的に正しいものはどれですか？",
                        "正しい動詞の形を選んで文を完成してください：彼女は毎日学校へ_______。",
                        "正しい助詞を選んでください：本は机_______あります。",
                        "正しい指示代名詞を選んでください：_______は私の本です。",
                        "正しい形容詞を選んでください：これは私が今まで読んだ中で_______本です。",
                        "正しい接続詞を選んでください：私はコーヒーが好きです_______弟は紅茶が好きです。",
                        "正しい敬語の形を選んでください。",
                        "正しい文の構造を選んでください。",
                        "正しい疑問文の作り方を選んでください。",
                        "正しい助動詞を選んでください：彼は明日来る_______と言いました。"
                    ],
                    'vocabulary': [
                        "'嬉しい'の同義語はどれですか？",
                        "'大きい'の反義語を選んでください。",
                        "文を完成するのに最適な単語を選んでください：今日の天気はとても_______です。",
                        "'美しい'とはどういう意味ですか？",
                        "正しいスペルを選んでください。",
                        "空欄を埋めるのに正しい単語を選んでください：宿題を_______必要があります。",
                        "次の中で名詞はどれですか？",
                        "次の中で動詞はどれですか？",
                        "'行く'の過去形は何ですか？",
                        "'子供'の複数形は何ですか？"
                    ]
                }
            }
            
            # 开始事务
            cursor.execute('BEGIN TRANSACTION')
            
            for i in range(need_to_generate):
                # 随机选择语言
                selected_language_id = random.choice(language_ids)
                selected_language = language_codes.get(selected_language_id, 'english')
                
                # 随机选择题目类型
                question_type = random.choice(question_types)
                
                # 随机选择题目类别（语法或词汇）
                category = random.choice(['grammar', 'vocabulary'])
                
                # 从模板中选择题目
                templates = question_templates.get(selected_language, question_templates['english'])
                category_templates = templates.get(category, templates['grammar'])
                base_question = random.choice(category_templates)
                
                # 生成题目内容
                question_number = current_count + i + 1
                question_content = f"{base_question} ({category.capitalize()})"
                
                # 生成正确答案
                correct_answer = random.choice(['A', 'B', 'C', 'D'])
                
                # 生成智能选项，确保语言一致性
                options = []
                option_labels = ['A', 'B', 'C', 'D']
                
                # 生成正确选项
                correct_option = {
                    'label': correct_answer,
                    'content': generate_option_content(question_content, correct_answer, True, selected_language)
                }
                options.append(correct_option)
                
                # 生成混淆选项
                wrong_options = []
                remaining_labels = [label for label in option_labels if label != correct_answer]
                
                for label in remaining_labels:
                    wrong_option = {
                        'label': label,
                        'content': generate_option_content(question_content, correct_answer, False, selected_language)
                    }
                    wrong_options.append(wrong_option)
                
                # 随机打乱选项顺序
                all_options = options + wrong_options
                random.shuffle(all_options)
                
                # 插入题目，确保语言ID正确
                cursor.execute(
                    'INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, language_id, question_content, correct_answer, is_active, question_type, topic_tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (random.choice(question_bank_ids), random.choice(level_ids), random.choice(section_ids), random.choice(difficulty_ids), selected_language_id, question_content, correct_answer, 1, question_type, category)
                )
                question_id = cursor.lastrowid
                
                # 插入选项
                for option_order, option in enumerate(all_options):
                    cursor.execute(
                        'INSERT INTO question_options (question_id, option_label, option_content, option_order) VALUES (?, ?, ?, ?)',
                        (question_id, option['label'], option['content'], option_order)
                    )
            
            cursor.execute('COMMIT')
            print(f"[考试AI] 成功生成 {need_to_generate} 道新题目，当前题库数量: {min_questions}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] 自动扩充题库失败: {e}")
        return False

# 添加语言测试开始路由，包含考试AI功能
@app.route('/language-test/start', methods=['POST'])
def start_language_test():
    """开始语言测试 - 考试AI自动从题库随机提取题目生成试卷"""
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    try:
        # 获取选择的语言
        selected_language = request.form.get('language', 'english')
        
        # 连接数据库获取最新用户信息
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, role, is_active FROM users WHERE id = ?',
            (session['user_id'],)
        )
        user = cursor.fetchone()
        
        if user:
            user_id, username, email, role, is_active = user
            
            # 检查用户是否为学生角色
            if role != 'student':
                conn.close()
                return render_template(
                    'index.html',
                    logged_in=True,
                    username=username,
                    user_id=user_id,
                    email=email,
                    role=role,
                    error="您的角色不允许参加语言测试"
                )
            
            # 1. 考试AI: 自动扩充题库
            auto_expand_question_bank()
            
            # 2. 考试AI: 从题库智能提取特定语言的题目生成试卷
            # 获取所选语言的ID
            cursor.execute('SELECT id FROM question_languages WHERE language_code = ?', (selected_language,))
            language_result = cursor.fetchone()
            language_id = language_result[0] if language_result else 2  # 默认英语
            
            # 智能生成试卷：确保题目类别和难度平衡
            print(f"[考试AI] 为语言 {selected_language} (ID: {language_id}) 生成智能试卷")
            
            # 1. 首先获取该语言所有可用题目，包含题目类型和难度信息
            cursor.execute('''
                SELECT q.id, q.topic_tags, q.difficulty_id 
                FROM questions q 
                WHERE q.is_active = 1 AND q.language_id = ?
            ''', (language_id,))
            all_questions = cursor.fetchall()
            
            # 确保只使用指定语言的题目，不混合其他语言
            if len(all_questions) < 50:
                print(f"[考试AI] 警告：{selected_language} 语言题目不足50题，仅能生成 {len(all_questions)} 题的试卷")
                selected_questions = all_questions
            else:
                # 2. 智能分组：支持简单标签和复杂标签
                import random
                
                # 智能分类函数
                def categorize_question(topic_tags):
                    """智能分类题目"""
                    if not topic_tags:
                        return 'other'
                    # 支持复杂标签，如 "grammar,advanced,exam_prep"
                    tags = topic_tags.lower().split(',')
                    if 'grammar' in tags:
                        return 'grammar'
                    elif 'vocabulary' in tags:
                        return 'vocabulary'
                    elif 'reading' in tags:
                        return 'reading'
                    elif 'listening' in tags:
                        return 'listening'
                    else:
                        return 'other'
                
                # 按类别分组
                grammar_questions = []
                vocabulary_questions = []
                other_questions = []
                
                for q in all_questions:
                    category = categorize_question(q[1])
                    if category == 'grammar':
                        grammar_questions.append(q)
                    elif category == 'vocabulary':
                        vocabulary_questions.append(q)
                    else:
                        other_questions.append(q)
                
                print(f"[考试AI] 题目类别分布：语法 {len(grammar_questions)} 题，词汇 {len(vocabulary_questions)} 题，其他 {len(other_questions)} 题")
                
                # 3. 智能选择题目：确保各类别平衡，灵活调整
                selected_questions = []
                total_needed = 50
                
                # 计算各类别应选数量
                categories = [
                    ('grammar', grammar_questions, 25),  # 目标25题
                    ('vocabulary', vocabulary_questions, 25),  # 目标25题
                    ('other', other_questions, 0)  # 补充用
                ]
                
                for cat_name, cat_questions, target in categories:
                    if target > 0:
                        if len(cat_questions) >= target:
                            # 随机选择目标数量
                            selected = random.sample(cat_questions, target)
                            selected_questions.extend(selected)
                            # 从原始列表中移除已选题目
                            remaining_questions = [q for q in cat_questions if q not in selected]
                            # 更新其他类别列表
                            if cat_name == 'grammar':
                                grammar_questions = remaining_questions
                            elif cat_name == 'vocabulary':
                                vocabulary_questions = remaining_questions
                        else:
                            # 类别题目不足，全部选用
                            selected_questions.extend(cat_questions)
                            if cat_name == 'grammar':
                                grammar_questions = []
                            elif cat_name == 'vocabulary':
                                vocabulary_questions = []
                
                # 计算还需要多少题目
                remaining_needed = total_needed - len(selected_questions)
                print(f"[考试AI] 已选题目 {len(selected_questions)} 题，还需要 {remaining_needed} 题")
                
                # 从所有可用题目中补充剩余需要的题目
                if remaining_needed > 0:
                    all_available = [q for q in all_questions if q not in selected_questions]
                    if len(all_available) >= remaining_needed:
                        selected_questions.extend(random.sample(all_available, remaining_needed))
                    else:
                        # 如果还是不足，使用所有剩余题目
                        selected_questions.extend(all_available)
                
                # 确保不超过50题
                selected_questions = selected_questions[:50]
            
            # 4. 打乱题目顺序
            import random
            random.shuffle(selected_questions)
            
            # 5. 提取题目ID列表
            selected_question_ids = [q[0] for q in selected_questions[:50]]
            
            # 6. 考试AI：为每个题目生成智能选项
            print(f"[考试AI] 为 {len(selected_question_ids)} 道题目生成智能选项")
            
            # 智能选项生成函数
            def generate_smart_options(question_id, question_content, correct_answer):
                """为题目生成智能选项"""
                # 获取题目信息
                cursor.execute('''
                    SELECT q.question_content, q.correct_answer, q.language_id
                    FROM questions q
                    WHERE q.id = ?
                ''', (question_id,))
                question = cursor.fetchone()
                
                if not question:
                    return []
                
                q_content, q_correct, q_language_id = question
                
                # 获取语言
                cursor.execute('SELECT language_code FROM question_languages WHERE id = ?', (q_language_id,))
                lang_code = cursor.fetchone()[0] if cursor.fetchone() else 'english'
                
                # 生成选项
                options = []
                
                # 确保正确答案存在
                correct_option = {
                    'label': correct_answer,
                    'content': f"{correct_answer}. {generate_option_content(q_content, q_correct, True, lang_code)}"
                }
                options.append(correct_option)
                
                # 生成混淆选项
                wrong_options = []
                option_labels = ['A', 'B', 'C', 'D']
                option_labels.remove(correct_answer)
                
                for label in option_labels:
                    wrong_option = {
                        'label': label,
                        'content': f"{label}. {generate_option_content(q_content, q_correct, False, lang_code)}"
                    }
                    wrong_options.append(wrong_option)
                
                # 随机打乱选项顺序
                all_options = options + wrong_options
                random.shuffle(all_options)
                
                return all_options
            
            # 为每个题目生成智能选项
            for question_id in selected_question_ids:
                # 检查是否已有选项
                cursor.execute('SELECT COUNT(*) FROM question_options WHERE question_id = ?', (question_id,))
                existing_options = cursor.fetchone()[0]
                
                # 如果没有选项或选项不足，生成新选项
                if existing_options < 4:
                    # 获取题目信息
                    cursor.execute('SELECT question_content, correct_answer FROM questions WHERE id = ?', (question_id,))
                    question_info = cursor.fetchone()
                    if question_info:
                        q_content, q_correct = question_info
                        # 删除现有选项
                        cursor.execute('DELETE FROM question_options WHERE question_id = ?', (question_id,))
                        # 生成新选项
                        generated_options = generate_smart_options(question_id, q_content, q_correct)
                        # 保存选项
                        for order, option in enumerate(generated_options):
                            cursor.execute('''
                                INSERT INTO question_options (question_id, option_label, option_content, option_order)
                                VALUES (?, ?, ?, ?)
                            ''', (question_id, option['label'], option['content'], order))
                        print(f"[考试AI] 为题目 {question_id} 生成了 {len(generated_options)} 个智能选项")
            
            print(f"[考试AI] 成功生成包含 {len(selected_question_ids)} 道题目的试卷")
            
            # 3. 生成唯一的试卷ID
            test_paper_id = f"paper_{uuid.uuid4().hex[:12]}"
            
            # 4. 创建测试记录
            cursor.execute('BEGIN TRANSACTION')
            
            # 语言显示名称映射
            language_display = {
                'english': 'English',
                'japanese': 'Japanese'
            }
            
            # 插入测试信息到tests表
            cursor.execute('''
                INSERT INTO tests (test_id, test_name, test_type, language, level, question_count, test_duration, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_paper_id, 
                f"{language_display.get(selected_language, 'English')}_Test_{username}", 
                "language", 
                language_display.get(selected_language, 'English'), 
                "A1-A2", 
                len(selected_question_ids), 
                60,  # 60分钟
                username
            ))
            
            # 5. 为每个题目创建试卷题目关联，并添加唯一标记
            for question_order, question_id in enumerate(selected_question_ids):
                # 插入到test_questions表，保存题目顺序和关联关系
                cursor.execute('''
                    INSERT INTO test_questions (test_id, question_id, question_order)
                    VALUES (?, ?, ?)
                ''', (test_paper_id, question_id, question_order))
            
            cursor.execute('COMMIT')
            
            conn.close()
            
            # 检查是否有可用题目
            if not selected_question_ids:
                return render_template(
                    'language_test.html',
                    logged_in=True,
                    username=username,
                    user_id=user_id,
                    email=email,
                    role=role,
                    error="当前没有可用的测试题目"
                )
            
            # 初始化测试会话，包含所选语言
            session['test_start_time'] = time.time()
            session['test_questions'] = selected_question_ids  # 存储随机选择的题目ID
            session['current_question_index'] = 0
            session['user_answers'] = {}
            session['test_paper_id'] = test_paper_id  # 保存唯一试卷ID
            session['test_language'] = selected_language  # 保存所选语言
            
            # 重定向到第一题
            return redirect(url_for('take_language_test'))
        else:
            conn.close()
            # 用户不存在，清除会话
            session.clear()
            return redirect(url_for('index'))
    except Exception as e:
        print(f"[ERROR] 开始语言测试失败: {e}")
        return render_template(
            'language_test.html',
            logged_in=session.get('logged_in', False),
            username=session.get('username', ''),
            error="开始语言测试失败，请稍后重试"
        )

@app.route('/language-test/take')
def take_language_test():
    """进行语言测试"""
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    # 检查测试会话是否已初始化
    if 'test_questions' not in session or 'current_question_index' not in session:
        return redirect(url_for('language_test'))
    
    try:
        # 获取当前题目信息
        current_index = session['current_question_index']
        question_id = session['test_questions'][current_index]
        total_questions = len(session['test_questions'])
        
        # 连接数据库获取题目详情
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 获取题目内容
        cursor.execute('SELECT question_content, question_type, correct_answer FROM questions WHERE id = ?', (question_id,))
        question = cursor.fetchone()
        
        # 获取选项
        cursor.execute('SELECT option_label, option_content FROM question_options WHERE question_id = ? ORDER BY option_order ASC', (question_id,))
        options = cursor.fetchall()
        conn.close()
        
        # 获取用户信息
        user_id = session['user_id']
        username = session['username']
        email = session['email']
        
        return render_template(
            'language_test_take.html',
            logged_in=True,
            username=username,
            user_id=user_id,
            email=email,
            question_id=question_id,
            question_content=question[0],
            question_type=question[1],
            options=options,
            current_index=current_index + 1,
            total_questions=total_questions,
            test_duration=60  # 测试时长为60分钟
        )
    except Exception as e:
        print(f"[ERROR] 进行语言测试失败: {e}")
        return render_template(
            'language_test.html',
            logged_in=session.get('logged_in', False),
            username=session.get('username', ''),
            error="进行语言测试失败，请稍后重试"
        )

@app.route('/language-test/submit-answer', methods=['POST'])
def submit_answer():
    """提交答案"""
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    # 检查测试会话是否已初始化
    if 'test_questions' not in session or 'current_question_index' not in session:
        return redirect(url_for('language_test'))
    
    try:
        # 获取当前题目信息
        current_index = session['current_question_index']
        question_id = session['test_questions'][current_index]
        
        # 获取用户答案
        user_answer = request.form.get('answer')
        
        # 保存用户答案
        session['user_answers'][question_id] = user_answer
        
        # 检查是否是最后一题
        if current_index == len(session['test_questions']) - 1:
            # 最后一题，跳转到提交页面
            return redirect(url_for('submit_language_test'))
        else:
            # 不是最后一题，跳转到下一题
            session['current_question_index'] = current_index + 1
            return redirect(url_for('take_language_test'))
    except Exception as e:
        print(f"[ERROR] 提交答案失败: {e}")
        return redirect(url_for('take_language_test'))

@app.route('/language-test/submit')
def submit_language_test():
    """提交测试"""
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    # 检查测试会话是否已初始化
    if 'test_questions' not in session or 'user_answers' not in session or 'test_start_time' not in session:
        return redirect(url_for('language_test'))
    
    try:
        # 计算测试结果
        user_id = session['user_id']
        username = session['username']
        email = session['email']
        
        # 获取测试信息
        questions = session['test_questions']
        user_answers = session['user_answers']
        start_time = session['test_start_time']
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        # 连接数据库获取正确答案
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 计算得分
        correct_count = 0
        total_count = len(questions)
        
        for question_id in questions:
            cursor.execute('SELECT correct_answer FROM questions WHERE id = ?', (question_id,))
            correct_answer = cursor.fetchone()[0]
            
            if question_id in user_answers and user_answers[question_id] == correct_answer:
                correct_count += 1
        
        # 计算得分百分比
        if total_count > 0:
            score = round((correct_count / total_count) * 100, 2)
        else:
            score = 0
        
        # 保存测试结果到数据库
        cursor.execute(
            'INSERT INTO test_scores (user_id, username, email, score, total_questions, correct_questions, duration, test_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, email, score, total_count, correct_count, duration, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()
        
        # 清除测试会话
        session.pop('test_questions', None)
        session.pop('current_question_index', None)
        session.pop('user_answers', None)
        session.pop('test_start_time', None)
        
        return render_template(
            'language_test_result.html',
            logged_in=True,
            username=username,
            user_id=user_id,
            email=email,
            score=score,
            total_questions=total_count,
            correct_questions=correct_count,
            duration=duration
        )
    except Exception as e:
        print(f"[ERROR] 提交测试失败: {e}")
        return render_template(
            'language_test.html',
            logged_in=session.get('logged_in', False),
            username=session.get('username', ''),
            error="提交测试失败，请稍后重试"
        )

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 输入验证
        if not username or not email or not password or not confirm_password:
            return render_template(
                'index.html',
                logged_in=session.get('logged_in', False),
                username=session.get('username', ''),
                error="所有字段都是必填的"
            )
        
        if password != confirm_password:
            return render_template(
                'index.html',
                logged_in=session.get('logged_in', False),
                username=session.get('username', ''),
                error="密码和确认密码不匹配"
            )
        
        try:
            # 连接数据库
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            # 插入用户信息
            cursor.execute('''
                INSERT INTO users (username, password, email, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, email, 'user', 1))
            conn.commit()
            conn.close()
            
            # 注册成功后，从数据库获取最新的用户信息，确保显示的信息与数据库完全匹配
            try:
                # 查询数据库，获取刚注册的用户的完整信息
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id, username, email, password, role, is_active FROM users WHERE id = ?',
                    (cursor.lastrowid,)
                )
                new_user = cursor.fetchone()
                conn.close()
                
                if new_user:
                    user_id, db_username, db_email, hashed_password, role, is_active = new_user
                    
                    # 设置会话，使用数据库中的最新信息
                    session['user_id'] = user_id
                    session['username'] = db_username
                    session['email'] = db_email
                    session['role'] = role
                    session['logged_in'] = is_active == 1
                    session['session_id'] = str(uuid.uuid4())
                    
                    return render_template(
                        'index.html',
                        logged_in=True,
                        username=db_username,
                        user_id=user_id,
                        email=db_email,
                        role=role,
                        session_id=session['session_id'],
                        success="注册成功，已自动登录"
                    )
                else:
                    # 注册失败，用户不存在于数据库中
                    return render_template(
                        'index.html',
                        logged_in=False,
                        error="注册失败，请重试"
                    )
            except Exception as e:
                print(f"[ERROR] 注册后获取最新用户信息失败: {e}")
                # 使用之前的信息作为备选
                session['user_id'] = cursor.lastrowid
                session['username'] = username
                session['email'] = email
                session['role'] = 'user'
                session['logged_in'] = True
                session['session_id'] = str(uuid.uuid4())
                
                return render_template(
                    'index.html',
                    logged_in=True,
                    username=username,
                    user_id=cursor.lastrowid,
                    email=email,
                    role='user',
                    session_id=session['session_id'],
                    success="注册成功，已自动登录"
                )
        except Exception as e:
            print(f"注册错误: {e}")
            return render_template(
                'index.html',
                logged_in=session.get('logged_in', False),
                username=session.get('username', ''),
                error=f"注册时发生错误: {str(e)}"
            )
    return render_template(
        'index.html',
        logged_in=session.get('logged_in', False),
        username=session.get('username', '')
    )

@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    return jsonify({'message': 'API测试成功'}), 200

@app.route('/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    # 清空会话
    session.clear()
    return redirect(url_for('index'))

@app.route('/language-test')
def language_test():
    """语言测试系统路由，仅允许学生访问
    学生可以参加语言测试，管理员不能参加考试
    """
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    try:
        # 连接数据库获取最新用户信息
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, role, is_active FROM users WHERE id = ?',
            (session['user_id'],)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_id, username, email, role, is_active = user
            
            # 检查用户是否为学生角色
            if role != 'student':
                # 管理员、超级管理员、硬件管理员不能参加考试
                return render_template(
                    'index.html',
                    logged_in=True,
                    username=username,
                    user_id=user_id,
                    email=email,
                    role=role,
                    error="您的角色不允许参加语言测试"
                )
            
            # 检查用户是否被禁用
            if is_active != 1:
                session.clear()
                return render_template(
                    'index.html',
                    logged_in=False,
                    error="该账户已被禁用，请联系管理员"
                )
            
            # 获取可用的测试题目数量
            try:
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM questions WHERE is_active = 1')
                total_questions = cursor.fetchone()[0]
                conn.close()
            except Exception as e:
                print(f"[ERROR] 获取题目数量失败: {e}")
                total_questions = 0
            
            # 学生可以访问语言测试系统
            return render_template(
                'language_test.html',
                logged_in=True,
                username=username,
                user_id=user_id,
                email=email,
                role=role,
                total_questions=total_questions
            )
        else:
            # 用户不存在，清除会话
            session.clear()
            return redirect(url_for('index'))
    except Exception as e:
        print(f"[ERROR] 访问语言测试系统失败: {e}")
        return render_template(
            'index.html',
            logged_in=session.get('logged_in', False),
            username=session.get('username', ''),
            error="访问语言测试系统失败，请稍后重试"
        )


@app.route('/settings')
def settings():
    """系统设置路由，仅允许管理员、超级管理员、硬件管理员访问
    管理员、超级管理员、硬件管理员可以进入设置页面，可以审批、修改系统参数、修改和查看数据库
    不同角色有不同的权限
    """
    # 检查用户是否已登录
    if not session.get('logged_in', False) or not session.get('user_id'):
        return redirect(url_for('index'))
    
    try:
        # 连接数据库获取最新用户信息
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, role, is_active FROM users WHERE id = ?',
            (session['user_id'],)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_id, username, email, role, is_active = user
            
            # 检查用户是否为管理员角色
            if role not in ['admin', 'super_admin', 'hardware_admin']:
                # 学生和其他角色不能访问设置页面
                return render_template(
                    'index.html',
                    logged_in=True,
                    username=username,
                    user_id=user_id,
                    email=email,
                    role=role,
                    error="您的角色不允许访问系统设置"
                )
            
            # 检查用户是否被禁用
            if is_active != 1:
                session.clear()
                return render_template(
                    'index.html',
                    logged_in=False,
                    error="该账户已被禁用，请联系管理员"
                )
            
            # 根据不同角色设置权限
            permissions = {
                'can_approve': role in ['admin', 'super_admin', 'hardware_admin'],  # 所有管理员都可以审批
                'can_modify_system': role in ['super_admin', 'admin'],  # 超级管理员和管理员可以修改系统参数
                'can_modify_database': role in ['super_admin'],  # 只有超级管理员可以修改数据库
                'can_view_database': role in ['super_admin', 'admin'],  # 超级管理员和管理员可以查看数据库
                'can_manage_hardware': role in ['hardware_admin', 'super_admin']  # 硬件管理员和超级管理员可以管理硬件
            }
            
            # 管理员、超级管理员、硬件管理员可以访问设置页面
            return render_template(
                'settings.html',
                logged_in=True,
                username=username,
                user_id=user_id,
                email=email,
                role=role,
                permissions=permissions
            )
        else:
            # 用户不存在，清除会话
            session.clear()
            return redirect(url_for('index'))
    except Exception as e:
        print(f"[ERROR] 访问系统设置失败: {e}")
        return render_template(
            'index.html',
            logged_in=session.get('logged_in', False),
            username=session.get('username', ''),
            error="访问系统设置失败，请稍后重试"
        )

# 导入JSON数据库同步服务
from json_db_sync import JSONDBSync

if __name__ == '__main__':
    print("=== 极简Flask启动脚本 (带完整路由) ===")
    print("启动Flask服务器...")
    print("访问地址: http://localhost:8888")
    
    # 启动JSON与数据库同步服务
    print("启动JSON与数据库同步服务...")
    json_sync_service = JSONDBSync()
    json_sync_service.start()
    # 将同步服务实例保存到app对象中，以便健康检查使用
    app.json_sync_service = json_sync_service
    print("JSON与数据库同步服务启动成功")
    
    # 启动系统优化器的定时任务
    print("启动系统定时优化任务...")
    from system_optimization import SystemOptimizer
    optimizer = SystemOptimizer()
    optimizer.start_scheduled_optimization(interval_hours=24)
    print("系统定时优化任务启动成功")
    
    # 启动服务器
    try:
        app.run(host='0.0.0.0', port=8888, debug=True)
    except Exception as e:
        print(f"[ERROR] 服务器启动失败: {str(e)}")
        # 停止同步服务
        json_sync_service.stop()
        raise
    finally:
        # 确保同步服务停止
        json_sync_service.stop()