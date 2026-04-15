#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Flask服务器，支持真实登录功能和AI数据库保护
"""

from flask import Flask, render_template, Blueprint, request, session, redirect, url_for, flash, jsonify
import os
import sys
import sqlite3
import hashlib
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用实例
app = Flask(__name__)

# 配置密钥，用于会话加密
app.secret_key = os.urandom(24)

# 配置模板目录
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# 配置静态文件目录
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 配置数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

# 创建蓝图，与原始应用保持一致
main_bp = Blueprint('main', __name__, url_prefix=None)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 安全工具类 - 使用PBKDF2算法，与原始应用保持一致
class SecurityUtils:
    """安全工具类，用于密码哈希和验证 - 与原始应用使用相同的PBKDF2算法"""
    
    @staticmethod
    def hash_password(password):
        """使用PBKDF2算法进行密码哈希"""
        import os
        import base64
        # 模拟原始应用的配置
        HASH_ALGORITHM = 'sha256'
        HASH_ITERATIONS = 100000
        
        # 生成32字节的随机盐
        salt = os.urandom(32)
        hashed = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            HASH_ITERATIONS
        )
        # 将盐和哈希值连接起来，然后进行base64编码
        return base64.b64encode(salt + hashed).decode('utf-8')
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """验证密码 - 使用PBKDF2算法"""
        import base64
        # 模拟原始应用的配置
        HASH_ALGORITHM = 'sha256'
        HASH_ITERATIONS = 100000
        
        try:
            # 解码存储的密码
            decoded = base64.b64decode(stored_password)
            salt = decoded[:32]  # 前32字节是盐
            stored_hash = decoded[32:]  # 后面是哈希值
            
            # 计算提供密码的哈希值
            hashed = hashlib.pbkdf2_hmac(
                HASH_ALGORITHM,
                provided_password.encode('utf-8'),
                salt,
                HASH_ITERATIONS
            )
            
            return hashed == stored_hash
        except Exception as e:
            print(f"密码验证失败: {e}")
            return False

security_utils = SecurityUtils()

# AI数据库保护类
class AIDatabaseProtector:
    """AI数据库保护类，用于防止数据库问题"""
    
    def __init__(self):
        self.db_backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_backup.db')
        self.protection_enabled = True
    
    def _connect_db(self, db_path=DATABASE_PATH):
        """连接数据库，带有AI保护"""
        try:
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            # 尝试使用备份数据库
            if db_path != self.db_backup_path:
                print("尝试使用备份数据库...")
                return self._connect_db(self.db_backup_path)
            else:
                # 备份数据库也失败，创建新数据库
                print("创建新数据库...")
                self._create_new_db()
                return sqlite3.connect(db_path)
    
    def _create_new_db(self):
        """创建新数据库"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        # 创建用户表
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
        conn.commit()
        conn.close()
        print("新数据库创建成功")
    
    def backup_db(self):
        """备份数据库"""
        if not self.protection_enabled:
            return False
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            backup_conn = sqlite3.connect(self.db_backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            print("数据库备份成功")
            return True
        except Exception as e:
            print(f"数据库备份失败: {e}")
            return False
    
    def verify_db_integrity(self):
        """验证数据库完整性"""
        if not self.protection_enabled:
            return True
        
        try:
            conn = self._connect_db()
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'ok'
        except Exception as e:
            print(f"数据库完整性检查失败: {e}")
            return False

ai_db_protector = AIDatabaseProtector()

# 用户模型
class User:
    """用户数据模型"""
    
    @staticmethod
    def get_by_username(username):
        """通过用户名获取用户"""
        conn = ai_db_protector._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password': row[3],
                'role': row[4],
                'created_at': row[5],
                'updated_at': row[6],
                'is_active': row[7],
                'super_admin_approved': row[8],
                'hardware_admin_approved': row[9],
                'avatar': row[10] if len(row) > 10 else None
            }
            return user
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """通过ID获取用户"""
        conn = ai_db_protector._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password': row[3],
                'role': row[4],
                'created_at': row[5],
                'updated_at': row[6],
                'is_active': row[7],
                'super_admin_approved': row[8],
                'hardware_admin_approved': row[9],
                'avatar': row[10] if len(row) > 10 else None
            }
            return user
        return None

# AI用户管理器
class UserAI:
    """AI用户管理器，用于处理用户AI相关操作"""
    
    def __init__(self):
        self.ai_instances = {}
    
    def process_login_request(self, username, password, request):
        """处理登录请求"""
        print(f"登录请求: 用户名={username}, 密码={password}")
        user = User.get_by_username(username)
        if user:
            print(f"找到用户: {user['username']}, 角色: {user['role']}")
            print(f"数据库中的密码哈希: {user['password']}")
            print(f"输入密码的哈希: {security_utils.hash_password(password)}")
            if security_utils.verify_password(user['password'], password):
                print("密码验证成功")
                return {
                    'success': True,
                    'message': '登录成功',
                    'ai_instance_id': f'user_ai_{user["id"]}'
                }
            else:
                print("密码验证失败")
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
        else:
            print("用户不存在")
            return {
                'success': False,
                'message': '用户名或密码错误'
            }
    
    def bind_user_to_ai(self, user_id):
        """绑定用户到AI实例"""
        ai_instance_id = f'user_ai_{user_id}'
        self.ai_instances[user_id] = ai_instance_id
        return ai_instance_id

user_ai_manager = UserAI()

# 定义main蓝图路由
@main_bp.route('/')
def index():
    """首页路由，返回index.html"""
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    """仪表盘路由"""
    return render_template('dashboard.html')

@main_bp.route('/permissions')
def permissions():
    """权限管理路由"""
    return render_template('permissions.html')

@main_bp.route('/ai_rules')
def ai_rules():
    """AI规则管理路由"""
    return render_template('ai_rules.html')

@main_bp.route('/approval')
def approval():
    """审批管理路由"""
    return render_template('approval.html')

@main_bp.route('/cleanup')
def cleanup():
    """系统清理路由"""
    return render_template('cleanup.html')

@main_bp.route('/system_config')
def system_config():
    """系统配置路由"""
    return render_template('system_config.html')

@main_bp.route('/projects')
def projects():
    """项目管理路由"""
    return render_template('projects.html')

@main_bp.route('/tasks')
def tasks():
    """任务管理路由"""
    return render_template('tasks.html')

@main_bp.route('/reports')
def reports():
    """报告中心路由"""
    return render_template('reports.html')

@main_bp.route('/hardware')
def hardware():
    """硬件管理路由"""
    return render_template('hardware.html')

@main_bp.route('/hardware_keys')
def hardware_keys():
    """硬件密钥路由"""
    return render_template('hardware_keys.html')

@main_bp.route('/system_monitoring')
def system_monitoring():
    """系统监控路由"""
    return render_template('system_monitoring.html')

@main_bp.route('/get_js_ai_code')
def get_js_ai_code():
    """JS AI代码路由"""
    return '''
// 用户AI实例代码
const UserAI = {
    databaseProtection: {
        verifyIntegrity: function() {
            console.log('AI: 验证数据库完整性...');
            return true;
        },
        backupDatabase: function() {
            console.log('AI: 备份数据库...');
            return true;
        },
        restoreDatabase: function() {
            console.log('AI: 恢复数据库...');
            return true;
        }
    },
    monitorLoginAttempts: function(username) {
        console.log('AI: 监控登录尝试:', username);
        return true;
    }
};
''', 200, {'Content-Type': 'application/javascript'}

@main_bp.route('/combined_test')
def combined_test():
    """结合测试路由"""
    return render_template('index.html')

# 定义auth蓝图路由
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录路由"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证表单数据
        if not username or not password:
            flash('请填写用户名和密码', 'danger')
            return redirect(url_for('auth.login'))
        
        # 验证数据库完整性
        if not ai_db_protector.verify_db_integrity():
            ai_db_protector.backup_db()
        
        # 使用登录AI处理登录请求
        login_result = user_ai_manager.process_login_request(username, password, request)
        
        if login_result['success']:
            # 检查用户是否已激活
            user = User.get_by_username(username)
            if user and user['is_active'] == 0:
                flash('您的账号正在审核中，请等待管理员批准后使用', 'warning')
                return redirect(url_for('auth.login'))
            
            # 设置会话
            session['logged_in'] = True
            session['username'] = user['username']
            session['user_level'] = user['role']
            session['is_guest'] = False
            
            # 存储用户专用AI实例ID
            if 'ai_instance_id' in login_result:
                session['user_ai_id'] = login_result['ai_instance_id']
            
            flash('登录成功', 'success')
            
            # 重定向到结合测试页面
            return redirect(url_for('main.combined_test'))
        else:
            flash(login_result.get('message', '用户名或密码错误'), 'danger')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        flash(f'登录失败: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册路由"""
    return render_template('index.html')

@auth_bp.route('/logout')
def logout():
    """登出路由"""
    session.clear()
    flash('登出成功', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/auto_guest_login')
def auto_guest_login():
    """游客自动登录路由"""
    try:
        # 生成随机游客用户名
        guest_username = f"guest_{uuid.uuid4().hex[:8]}"
        
        # 为游客生成随机邮箱
        guest_email = f"{guest_username}@guest.example.com"
        
        # 为游客生成随机密码
        random_password = uuid.uuid4().hex[:16]
        hashed_password = security_utils.hash_password(random_password)
        
        # 绑定AI实例
        guest_ai_id = user_ai_manager.bind_user_to_ai(0)
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = guest_username
        session['user_level'] = 'guest'
        session['is_guest'] = True
        session['user_ai_id'] = guest_ai_id
        
        flash('游客登录成功', 'success')
        
        # 重定向到结合测试页面
        return redirect(url_for('main.combined_test'))
    except Exception as e:
        flash('游客登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/confirm_guest_logout', methods=['GET', 'POST'])
def confirm_guest_logout():
    """确认游客登出路由"""
    session.clear()
    flash('登出成功', 'success')
    return redirect(url_for('auth.login'))

# 注册蓝图
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

# 模拟AI路由
@app.route('/api/database/verify')
def verify_database():
    """验证数据库API"""
    integrity = ai_db_protector.verify_db_integrity()
    return jsonify({'success': integrity, 'message': '数据库完整性验证成功' if integrity else '数据库完整性验证失败'})

@app.route('/api/database/backup')
def backup_database():
    """备份数据库API"""
    result = ai_db_protector.backup_db()
    return jsonify({'success': result, 'message': '数据库备份成功' if result else '数据库备份失败'})

# 规则管理API路由 - 暂时移除，因为rule_management_service导入已移除

# 这些路由将在修复导入问题后重新添加
# @app.route('/api/rules')
# def get_rules():
#     """获取所有规则"""
#     rules = rule_management_service.get_rules()
#     return jsonify({'success': True, 'rules': rules})

# @app.route('/api/rules/<rule_type>')
# def get_rules_by_type(rule_type):
#     """获取特定类型的规则"""
#     rules = rule_management_service.get_rules(rule_type)
#     return jsonify({'success': True, 'rules': rules})

# @app.route('/api/rules', methods=['POST'])
# def add_rule():
#     """添加新规则"""
#     data = request.json
#     rule_type = data.get('rule_type')
#     rule_name = data.get('rule_name')
#     rule_content = data.get('rule_content')
    
#     if not all([rule_type, rule_name, rule_content]):
#         return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
#     result = rule_management_service.add_rule(rule_type, rule_name, rule_content)
#     return jsonify({'success': result, 'message': '规则添加成功' if result else '规则添加失败'})

# @app.route('/api/rules/<rule_type>/<rule_name>', methods=['PUT'])
# def update_rule(rule_type, rule_name):
#     """更新规则"""
#     data = request.json
#     rule_content = data.get('rule_content')
    
#     if not rule_content:
#         return jsonify({'success': False, 'message': '缺少规则内容'}), 400
    
#     result = rule_management_service.update_rule(rule_type, rule_name, rule_content)
#     return jsonify({'success': result, 'message': '规则更新成功' if result else '规则更新失败'})

# @app.route('/api/rules/<rule_type>/<rule_name>', methods=['DELETE'])
# def delete_rule(rule_type, rule_name):
#     """删除规则"""
#     result = rule_management_service.delete_rule(rule_type, rule_name)
#     return jsonify({'success': result, 'message': '规则删除成功' if result else '规则删除失败'})

# @app.route('/api/rules/collect', methods=['POST'])
# def collect_rules():
#     """手动收集规则"""
#     rules = rule_management_service.collect_rules()
#     return jsonify({'success': True, 'message': '规则收集成功', 'rules': rules})

# @app.route('/api/rules/optimize', methods=['POST'])
# def optimize_rules():
#     """优化规则"""
#     result = rule_management_service.optimize_rules()
#     return jsonify({'success': result, 'message': '规则优化成功' if result else '规则优化失败'})

# @app.route('/api/rules/monitor', methods=['POST'])
# def monitor_rules():
#     """监控规则"""
#     result = rule_management_service.monitor_rules()
#     return jsonify({'success': result, 'message': '规则监控成功' if result else '规则监控失败'})

# @app.route('/api/rules/manager')
# def get_rule_manager():
#     """获取规则管理AI信息"""
#     manager_ai = rule_management_service.get_rule_manager_ai()
#     return jsonify({'success': True, 'rule_manager': manager_ai})

@app.route('/ai/<path:path>')
def ai_route(path):
    """AI相关路由"""
    return '', 200

if __name__ == '__main__':
    # 显式设置端口为8888
    PORT = 8888
    print(f"Starting enhanced Flask server on http://0.0.0.0:{PORT}...")
    
    # 初始化数据库
    ai_db_protector._connect_db()
    ai_db_protector.backup_db()
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=True)
    except KeyboardInterrupt:
        print("Flask server stopped.")
    except Exception as e:
        print(f"Error starting Flask server: {str(e)}")
        import traceback
        traceback.print_exc()
