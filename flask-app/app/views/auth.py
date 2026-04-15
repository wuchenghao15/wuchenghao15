import re
import requests
from datetime import datetime, timedelta, UTC
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.utils.logging import logger
from app.models.user import User
from app.utils.security import security_utils
from app.ai.auth import auth_ai
from app.utils.rule_manager import rule_manager
from app.utils.permission_manager import permission_manager
from app.utils.route_manager import route_manager
from app.utils.db import db_manager

# 延迟导入，避免循环依赖和导入时的数据库访问
user_ai_manager = None
user_login_ai = None
ai_login_analyzer = None

def record_user_operation(user_id, operation_type, operation_description, ip_address, user_agent):
    """记录用户操作"""
    try:
        # 检测设备类型
        user_agent_lower = user_agent.lower()
        device_type = 'desktop'
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            device_type = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'tablet'
        
        # 插入操作记录
        db_manager.execute(
            '''
            INSERT INTO user_operations (user_id, operation_type, operation_description, ip_address, user_agent, device_type)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, operation_type, operation_description, ip_address, user_agent, device_type)
        )
        logger.info(f"记录用户操作成功: {user_id}, {operation_type}")
    except Exception as e:
        logger.error(f"记录用户操作失败: {str(e)}")


def get_user_ai_manager():
    global user_ai_manager
    if user_ai_manager is None:
        from app.ai.user_ai_manager import user_ai_manager
    return user_ai_manager


def get_user_login_ai():
    global user_login_ai
    if user_login_ai is None:
        from app.ai.user_login_ai import user_login_ai
    return user_login_ai

def get_ai_login_analyzer():
    global ai_login_analyzer
    if ai_login_analyzer is None:
        from app.ai.login_analyzer import ai_login_analyzer
    return ai_login_analyzer

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 注册蓝图到路由管理器
route_manager.register_blueprint(auth_bp)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录视图"""
    # 处理GET请求，返回登录页面
    if request.method == 'GET':
        return render_template('index.html')
    
    # 处理POST请求，执行登录逻辑
    try:
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # 验证表单数据
        if not username or not password:
            flash('请填写用户名/手机号和密码', 'danger')
            return redirect(url_for('auth.login'))
        
        # 验证用户
        username = username.strip()
        password = password.strip()
        
        # 获取IP地址和用户代理
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        # 使用规则管理器检查登录规则
        # 1. 检查IP地址限制
        ip_check = rule_manager.check_rule("login", "ip_restriction", ip_address=ip_address)
        if not ip_check['success']:
            flash(ip_check['message'], 'danger')
            return redirect(url_for('auth.login'))
        
        # 2. 检查速率限制
        rate_limit_check = rule_manager.check_rule("login", "rate_limiting", ip_address=ip_address)
        if not rate_limit_check['success']:
            flash(rate_limit_check['message'], 'danger')
            return redirect(url_for('auth.login'))
        
        # 3. 检查登录尝试次数
        login_attempts_check = rule_manager.check_rule("login", "max_attempts", username=username)
        if not login_attempts_check['success']:
            flash(login_attempts_check['message'], 'danger')
            return redirect(url_for('auth.login'))
        
        # 使用登录行为分析AI分析登录尝试
        login_analysis = get_ai_login_analyzer().analyze_login_attempt(username, ip_address, user_agent)
        
        # 检查是否为异常登录
        if login_analysis['is_anomaly']:
            logger.warning(f"检测到异常登录尝试: {username}, IP: {ip_address}, 风险等级: {login_analysis['risk_level']}")
            # 对于高风险登录，要求额外验证
            if login_analysis['risk_level'] == 'high':
                flash('检测到异常登录行为，请使用双因素认证', 'danger')
                # 这里可以重定向到双因素认证页面
                return redirect(url_for('auth.login'))
        
        # 使用用户登录AI处理登录请求
        login_result = get_user_login_ai().process_login(username, password, ip_address, user_agent)
        
        # 更新登录结果到登录行为分析AI
        get_ai_login_analyzer().update_login_result(username, login_result['success'])
        
        if not login_result['success']:
            flash(login_result['message'], 'danger')
            return redirect(url_for('auth.login'))
        
        # 登录成功，重置登录尝试次数
        rule_manager.reset_login_attempts(username)
        
        # 获取用户信息
        user = User.get_by_username(username)
        
        # 检查用户是否已激活
        if not user.is_active:
            flash('您的账号尚未激活，请等待管理员批准后使用', 'warning')
            return redirect(url_for('auth.login'))
        
        # 检查用户是否已被批准
        if not user.super_admin_approved or not user.hardware_admin_approved:
            flash('您的账号尚未完全批准，请等待管理员批准后使用', 'warning')
            return redirect(url_for('auth.login'))
        
        # 使用SessionManager创建会话
        from app.utils.session_manager import session_manager
        login_type = 'password'
        device_info = f"Browser: {user_agent}"
        
        success, session_result = session_manager.create_session(
            user_id=user.user_id,
            username=user.username,
            login_type=login_type,
            device_info=device_info,
            remember=remember
        )
        
        if not success:
            flash(session_result, 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取用户的权限
        user_permissions = permission_manager.get_role_permissions(user.role)
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = user.username
        session['user_level'] = user.role
        session['user_role'] = user.role
        session['is_guest'] = False
        session['user_id'] = user.user_id
        session['email'] = user.email
        session['session_id'] = session_result  # 保存会话ID
        session['permissions'] = user_permissions  # 保存用户权限
        
        # 保存用户组别
        user_group = login_result.get('group', 'default')
        session['user_group'] = user_group
        logger.info(f"设置用户组别: {user_group}, 权限数: {len(user_permissions)}")
        
        # 为用户创建并绑定AI实例
        try:
            user_ai_id = get_user_ai_manager().bind_user_to_ai(user.user_id)
            session['user_ai_id'] = user_ai_id
        except Exception as ai_error:
            logger.error(f"创建AI实例失败: {str(ai_error)}")
        
        # 获取登录统计信息
        login_statistics = get_ai_login_analyzer().get_login_statistics(username)
        
        # 生成安全建议
        security_suggestions = []
        if login_statistics['failed_logins'] > 3:
            security_suggestions.append('您最近有多次登录失败，建议修改密码')
        if len(login_statistics['login_locations']) > 3:
            security_suggestions.append('您的账户从多个位置登录，建议启用双因素认证')
        
        # 合并安全建议
        all_suggestions = login_analysis.get('suggestions', []) + security_suggestions
        
        # 保存安全建议到会话
        if all_suggestions:
            session['security_suggestions'] = all_suggestions
            # 显示第一条安全建议
            if all_suggestions:
                flash(all_suggestions[0], 'warning')
        
        logger.info(f"用户登录成功: {user.username}, 角色: {user.role}, 登录统计: {login_statistics}")
        
        # 记录用户登录操作
        record_user_operation(
            user_id=user.user_id,
            operation_type='login',
            operation_description=f'用户登录成功，角色: {user.role}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        flash('登录成功', 'success')
        
        # 生成用户容器标签
        import uuid
        user_container = f"user_{user.user_id}_{uuid.uuid4().hex[:8]}"
        
        # 根据用户角色和组别进行不同的跳转
        user_role = user.role
        user_group = login_result.get('group', 'default')
        logger.info(f"从login_result获取用户组别: {user_group}")
        
        # 同时更新session中的用户组别
        session['user_group'] = user_group
        
        logger.info(f"最终跳转判断 - user_role: {user_role}, user_group: {user_group}")
        
        # 学生组别进入考试系统主页
        if user_role == 'student' or user_group == 'student':
            logger.info(f"学生用户/组别，跳转到语言测试系统首页")
            from flask import make_response
            response = make_response(redirect(url_for('language_tests.test_system')))
            response.set_cookie('user_container', user_container, max_age=7*24*60*60, httponly=True)
            return response
        # 设计师进入Arduino设计主页
        elif user_group == 'designer':
            logger.info(f"设计师组别，跳转到Arduino设计主页")
            from flask import make_response
            response = make_response(redirect(url_for('integrated_design.integrated_design')))
            response.set_cookie('user_container', user_container, max_age=7*24*60*60, httponly=True)
            return response
        # 管理员根据权限配置自动挂载后台程序
        elif user_role in ['admin', 'super_admin', 'hardware_vikey_admin']:
            logger.info(f"管理员用户，跳转到管理员中心")
            from flask import make_response
            response = make_response(redirect(url_for('main.admin_center')))
            response.set_cookie('user_container', user_container, max_age=7*24*60*60, httponly=True)
            return response
        else:
            logger.info(f"其他用户，跳转到主首页")
            from flask import make_response
            response = make_response(redirect(url_for('main.index')))
            response.set_cookie('user_container', user_container, max_age=7*24*60*60, httponly=True)
            return response
        
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        flash(f'登录失败: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册视图"""
    # 处理GET请求，返回注册页面
    if request.method == 'GET':
        return render_template('register.html')
    
    # 处理POST请求，执行注册逻辑
    try:
        # 获取表单数据
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        agree_user_agreement = request.form.get('agree_user_agreement')
        agree_user_manual = request.form.get('agree_user_manual')
        
        # 验证表单数据
        if not username or not email or not password or not confirm_password:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('auth.register'))
        
        # 验证协议同意
        if not agree_user_agreement or not agree_user_manual:
            flash('请阅读并同意用户协议和用户手册', 'danger')
            return redirect(url_for('auth.register'))
        
        # 获取IP地址
        ip_address = request.remote_addr
        
        # 使用规则管理器检查注册规则
        # 1. 检查注册限制
        registration_check = rule_manager.check_rule("registration", "max_registrations_per_ip", ip_address=ip_address)
        if not registration_check['success']:
            flash(registration_check['message'], 'danger')
            return redirect(url_for('auth.register'))
        
        # 2. 检查验证码
        captcha_response = request.form.get('captcha')
        captcha_check = rule_manager.check_rule("registration", "captcha", captcha_response=captcha_response)
        if not captcha_check['success']:
            flash(captcha_check['message'], 'danger')
            return redirect(url_for('auth.register'))
        
        # 验证密码匹配
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.register'))
        
        # 用户名验证（国际标准）
        username = username.strip()
        if len(username) < 3 or len(username) > 20:
            flash('用户名长度必须在3-20个字符之间', 'danger')
            return redirect(url_for('auth.register'))
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
            flash('用户名必须以字母开头，只能包含字母、数字、下划线和连字符', 'danger')
            return redirect(url_for('auth.register'))
        if re.search(r'[-_]{2,}', username):
            flash('用户名中不能包含连续的下划线或连字符', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查用户名是否已存在
        if User.get_by_username(username):
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        # 邮箱验证（国际标准，符合RFC 5322）
        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('请输入有效的邮箱地址', 'danger')
            return redirect(url_for('auth.register'))
        # 检查邮箱长度
        if len(email) > 254:
            flash('邮箱地址长度不能超过254个字符', 'danger')
            return redirect(url_for('auth.register'))
        
        # 密码验证（国际标准，强密码要求）
        password = password.strip()
        if len(password) < 8:
            flash('密码长度不能少于8个字符', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[A-Z]', password):
            flash('密码必须包含至少一个大写字母', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[a-z]', password):
            flash('密码必须包含至少一个小写字母', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'\d', password):
            flash('密码必须包含至少一个数字', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('密码必须包含至少一个特殊字符', 'danger')
            return redirect(url_for('auth.register'))
        if re.search(r'(.)\1{2,}', password):
            flash('密码不能包含连续3个或以上相同的字符', 'danger')
            return redirect(url_for('auth.register'))
        # 检查常见密码
        if User.is_common_password(password):
            flash('密码不能使用常见密码，请选择更安全的密码', 'danger')
            return redirect(url_for('auth.register'))
        
        # 哈希密码
        hashed_password = security_utils.hash_password(password)
        
        # 创建新用户 - 初始状态为未激活，需要审核
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role='user',
            is_active=0,  # 初始为未激活状态
            super_admin_approved=0,  # 初始为未批准状态
            hardware_admin_approved=0  # 初始为未批准状态
        )
        
        # 保存用户到数据库
        user_id = user.save()
        
        if user_id:
            # 检查是否为游客用户注册
            is_guest = session.get('is_guest', False)
            guest_user_id = session.get('user_id')
            
            # 添加密码历史记录
            user.user_id = user_id
            user.add_password_history(hashed_password)
            # 设置密码修改时间和修改人
            user.password_modified_at = datetime.now(UTC).isoformat()
            user.password_modified_by = 'user'
            user.update()
            
            logger.info(f"用户注册成功: {username}，用户ID: {user_id}，等待审核")
            
            # 将用户添加到默认组别
            try:
                from app.ai.user_login_ai_db import add_user_to_group
                add_user_to_group(user_id, "default")
            except Exception as group_error:
                logger.error(f"添加用户到组别失败: {str(group_error)}")
            
            # 如果是游客用户注册，同步游客数据
            if is_guest and guest_user_id:
                try:
                    from app.services.guest_user_manager import guest_user_manager
                    guest_user_manager.sync_guest_data_to_registered_user(guest_user_id, user_id)
                    logger.info(f"游客数据同步到注册用户成功: 游客ID={guest_user_id}, 注册用户ID={user_id}")
                except Exception as sync_error:
                    logger.error(f"同步游客数据失败: {str(sync_error)}")
            
            # 通知AI员工进行审核
            try:
                from app.ai.monitoring import ai_monitor
                ai_monitor.notify_approval(
                    user_id=user_id,
                    username=username,
                    action="register",
                    priority="medium"
                )
            except Exception as ai_error:
                logger.error(f"通知AI审核失败: {str(ai_error)}")
            
            # 直接登录用户，不需要审核
            user.is_active = 1
            user.super_admin_approved = 1
            user.hardware_admin_approved = 1
            user.update()
            
            # 使用SessionManager创建会话
            from app.utils.session_manager import session_manager
            login_type = 'register'
            device_info = 'Web Browser'
            
            success, session_result = session_manager.create_session(
                user_id=user_id,
                username=user.username,
                login_type=login_type,
                device_info=device_info
            )
            
            if not success:
                flash(session_result, 'danger')
                return redirect(url_for('auth.login'))
            
            # 设置会话
            session['logged_in'] = True
            session['username'] = user.username
            session['user_level'] = user.role
            session['user_role'] = user.role
            session['is_guest'] = False
            session['user_id'] = user_id
            session['email'] = user.email
            session['session_id'] = session_result
            session['user_group'] = 'user'
            
            # 为用户创建并绑定AI实例
            try:
                user_ai_id = get_user_ai_manager().bind_user_to_ai(user_id)
                session['user_ai_id'] = user_ai_id
            except Exception as ai_error:
                logger.error(f"创建AI实例失败: {str(ai_error)}")
            
            # 获取用户的权限
            user_permissions = permission_manager.get_role_permissions(user.role)
            session['permissions'] = user_permissions  # 保存用户权限
            
            logger.info(f"用户注册并自动登录成功: {user.username}, 角色: {user.role}, 权限数: {len(user_permissions)}")
            
            flash('注册成功，已自动登录', 'success')
            
            # 自动跳转考试系统
            return redirect(url_for('language_tests.test_system'))
        else:
            flash('注册失败，请稍后重试', 'danger')
            return redirect(url_for('auth.register'))
            
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        flash(f'注册失败: {str(e)}', 'danger')
        return redirect(url_for('auth.register'))



@auth_bp.route('/auto_guest_login')
def auto_guest_login():
    """自动游客登录视图"""
    try:
        # 使用游客用户管理器生成游客用户
        from app.services.guest_user_manager import guest_user_manager
        guest_user, guest_user_id, password = guest_user_manager.generate_guest_user()
        
        if not guest_user or not guest_user_id:
            flash('游客登录失败，请稍后重试', 'danger')
            return redirect(url_for('main.index'))
        
        # 将游客添加到默认组别
        try:
            from app.ai.user_login_ai_db import add_user_to_group
            add_user_to_group(guest_user_id, "guest")
        except Exception as group_error:
            logger.error(f"添加游客到组别失败: {group_error}")
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = guest_user.username
        session['user_level'] = 'guest'  # 游客角色
        session['user_role'] = 'guest'  # 同时设置user_role，用于权限系统
        session['is_guest'] = True
        session['user_id'] = guest_user_id
        session['user_group'] = 'guest'  # 保存游客组别
        
        # 尝试为游客创建并绑定AI实例
        try:
            guest_ai_id = get_user_ai_manager().bind_user_to_ai(guest_user_id)
            session['user_ai_id'] = guest_ai_id
            logger.info(f"游客登录成功: {guest_user.username}, 用户ID: {guest_user_id}, 密码: {password}, 绑定AI实例: {guest_ai_id}, 组别: guest")
        except Exception as ai_error:
            # 如果AI引擎不可用，仍然允许游客登录，只是不绑定AI实例
            logger.warning(f"绑定AI实例失败: {str(ai_error)}, 游客登录继续")
            session['user_ai_id'] = None
            logger.info(f"游客登录成功: {guest_user.username}, 用户ID: {guest_user_id}, 密码: {password}, 组别: guest")
        
        # 直接重定向到测试系统主页
        return redirect(url_for('language_tests.test_system'))
    except Exception as e:
        logger.error(f"游客登录失败: {str(e)}")
        flash('游客登录失败，请稍后重试', 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    """登出视图，支持会话管理"""
    username = session.get('username')
    is_guest = session.get('is_guest', False)
    session_id = session.get('session_id')
    
    # 如果是游客用户，跳转到登出提示页面
    if is_guest:
        logger.info(f"游客用户登出流程: {username}")
        return render_template('guest_logout.html')
    
    # 普通用户登出，先清除数据库会话
    if session_id:
        try:
            from app.utils.session_manager import session_manager
            session_manager.invalidate_session(session_id)
        except Exception as e:
            logger.error(f"清除数据库会话失败: {str(e)}")
    
    # 清除会话
    session.clear()
    logger.info(f"用户登出成功: {username}")
    flash('登出成功', 'success')
    
    # 登出后返回首页
    return redirect(url_for('main.index'))

@auth_bp.route('/confirm_guest_logout', methods=['POST'])
def confirm_guest_logout():
    """确认游客登出并删除数据"""
    username = session.get('username')
    user_id = session.get('user_id')
    session_id = session.get('session_id')
    
    try:
        # 如果有会话ID，清除数据库会话
        if session_id:
            try:
                from app.utils.session_manager import session_manager
                session_manager.invalidate_session(session_id)
            except Exception as e:
                logger.error(f"清除数据库会话失败: {str(e)}")
        
        # 使用游客用户管理器删除游客用户数据
        if user_id:
            from app.services.guest_user_manager import guest_user_manager
            guest_user_manager.cleanup_guest_user(user_id)
        
        # 清除会话
        session.clear()
        logger.info(f"游客用户登出成功: {username}")
        flash('登出成功，您的游客数据已被删除', 'success')
    except Exception as e:
        logger.error(f"删除游客数据失败: {str(e)}")
        flash('登出成功，但删除数据时发生错误', 'warning')
    
    # 登出后返回首页
    return redirect(url_for('main.index'))

@auth_bp.route('/api/auth/login-vikey', methods=['POST'])
def login_vikey():
    """Vikey登录API端点，支持会话管理"""
    try:
        # 获取请求数据
        data = request.get_json()
        hardware_id = data.get('hardwareId')
        challenge = data.get('challenge')
        signature = data.get('signature')
        timestamp = data.get('timestamp')
        is_admin = data.get('isAdmin', False)
        
        # 验证请求参数
        if not hardware_id or not challenge or not signature:
            return jsonify({
                'success': False,
                'message': '缺少必要的请求参数'
            }), 400
        
        # 记录Vikey登录尝试
        logger.info(f"Vikey登录尝试: 硬件ID={hardware_id}, 是否管理员={is_admin}")
        
        # 验证Vikey签名（这里可以根据实际情况实现更复杂的验证逻辑）
        # 示例：简单验证签名格式
        if len(signature) < 10:
            return jsonify({
                'success': False,
                'message': '无效的Vikey签名'
            }), 401
        
        # 检查硬件ID是否在允许的列表中（这里可以根据实际情况实现更复杂的验证逻辑）
        # 示例：简单验证硬件ID格式
        if len(hardware_id) < 10:
            return jsonify({
                'success': False,
                'message': '无效的Vikey硬件ID'
            }), 401
        
        # 根据硬件ID查找或创建用户
        user = User.get_by_username(f"vikey_{hardware_id[:8]}")
        if not user:
            # 创建新用户
            user = User(
                username=f"vikey_{hardware_id[:8]}",
                email=f"vikey_{hardware_id[:8]}@example.com",
                password=security_utils.hash_password(hardware_id),  # 使用硬件ID作为临时密码
                role='hardware_vikey_admin' if is_admin else 'user',
                is_active=1,  # Vikey用户自动激活
                super_admin_approved=1,  # Vikey用户自动批准
                hardware_admin_approved=1  # Vikey用户自动批准
            )
            user_id = user.save()
            logger.info(f"已创建Vikey用户: {user.username}, 用户ID: {user_id}")
            
            # 将Vikey用户添加到相应组别
            try:
                from app.ai.user_login_ai_db import add_user_to_group
                group_name = "admin" if is_admin else "user"
                add_user_to_group(user_id, group_name)
            except Exception as group_error:
                logger.error(f"添加Vikey用户到组别失败: {str(group_error)}")
        
        # 使用SessionManager创建会话
        from app.utils.session_manager import session_manager
        login_type = 'vikey'
        device_info = f"Vikey: {hardware_id}"
        
        success, session_result = session_manager.create_session(
            user_id=user.user_id,
            username=user.username,
            login_type=login_type,
            device_info=device_info
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': session_result
            }), 401
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = user.username
        session['user_level'] = user.role
        session['is_guest'] = False
        session['vikey_hardware_id'] = hardware_id
        session['vikey_is_admin'] = is_admin
        session['session_id'] = session_result  # 保存会话ID
        session['user_group'] = "admin" if is_admin else "user"  # 保存用户组别
        
        # 为用户创建并绑定AI实例
        user_ai_id = get_user_ai_manager().bind_user_to_ai(user.user_id)
        session['user_ai_id'] = user_ai_id
        
        logger.info(f"Vikey登录成功: {user.username}, 硬件ID: {hardware_id}, 会话ID: {session_result[:10]}..., 组别: {session['user_group']}")
        
        # 返回登录结果
        return jsonify({
            'success': True,
            'message': 'Vikey登录成功',
            'token': f"vikey_{hardware_id}_{timestamp}",  # 生成简单的token
            'sessionId': session_result,  # 返回会话ID
            'userInfo': {
                'username': user.username,
                'role': user.role,
                'vikeyHardwareId': hardware_id,
                'vikeyIsAdmin': is_admin
            }
        })
        
    except Exception as e:
        logger.error(f"Vikey登录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Vikey登录失败: {str(e)}'
        }), 500


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码视图"""
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    try:
        # 获取表单数据
        email = request.form.get('email')
        
        # 验证邮箱
        if not email:
            flash('请输入邮箱地址', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        # 检查用户是否存在
        user = User.get_by_email(email)
        if not user:
            flash('邮箱地址不存在', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        # 生成重置密码令牌
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # 保存令牌到用户
        user.reset_token = reset_token
        user.reset_token_expiry = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        user.update()
        
        # 模拟发送重置链接（实际项目中应该发送邮件）
        reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
        logger.info(f"重置密码链接: {reset_link}")
        
        # 提示用户
        flash('重置密码链接已发送到您的邮箱，请在1小时内点击链接重置密码', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        logger.error(f"忘记密码处理失败: {str(e)}")
        flash(f'处理失败: {str(e)}', 'danger')
        return redirect(url_for('auth.forgot_password'))


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """重置密码视图"""
    # 检查令牌是否有效
    user = User.get_by_reset_token(token)
    if not user:
        flash('无效的重置密码链接', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    # 检查令牌是否过期
    if datetime.fromisoformat(user.reset_token_expiry) < datetime.now(UTC):
        flash('重置密码链接已过期', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'GET':
        return render_template('reset_password.html', token=token)
    
    try:
        # 获取表单数据
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证密码
        if not password or not confirm_password:
            flash('请填写密码和确认密码', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 验证密码强度
        if len(password) < 8:
            flash('密码长度不能少于8个字符', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[A-Z]', password):
            flash('密码必须包含至少一个大写字母', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[a-z]', password):
            flash('密码必须包含至少一个小写字母', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'\d', password):
            flash('密码必须包含至少一个数字', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('密码必须包含至少一个特殊字符', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 检查是否为常用密码
        if User.is_common_password(password):
            flash('密码不能使用常见密码，请选择更安全的密码', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 哈希新密码
        hashed_password = security_utils.hash_password(password)
        
        # 检查密码是否在历史记录中使用过
        if user.is_password_used_before(hashed_password):
            flash('密码不能与历史密码一致，请选择新密码', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 添加密码历史记录
        user.add_password_history(hashed_password)
        
        # 更新密码并清除重置令牌
        user.password = hashed_password
        user.reset_token = None
        user.reset_token_expiry = None
        user.password_modified_at = datetime.now(UTC).isoformat()
        user.password_modified_by = 'user'
        user.update()
        
        flash('密码重置成功，请使用新密码登录', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        logger.error(f"重置密码处理失败: {str(e)}")
        flash(f'处理失败: {str(e)}', 'danger')
        return redirect(url_for('auth.reset_password', token=token))

@auth_bp.route('/github/login')
def github_login():
    """GitHub登录视图"""
    try:
        logger.info("用户尝试使用GitHub登录")
        
        # 从配置中获取GitHub OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        github_config = oauth_config.get('GITHUB', {})
        
        # 检查配置是否完整
        client_id = github_config.get('CLIENT_ID')
        if not client_id:
            flash('GitHub登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 生成随机state参数防止CSRF攻击
        import secrets
        state = secrets.token_urlsafe(32)
        session['github_oauth_state'] = state
        
        # 构建授权URL
        authorize_url = github_config['AUTHORIZE_URL']
        redirect_uri = github_config['REDIRECT_URI']
        scope = github_config['SCOPE']
        
        auth_url = f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
        logger.info(f"重定向到GitHub授权页面: {auth_url}")
        
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"GitHub登录失败: {str(e)}")
        flash('GitHub登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/github/callback')
def github_callback():
    """GitHub登录回调处理"""
    try:
        logger.info("处理GitHub登录回调")
        
        # 从配置中获取GitHub OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        github_config = oauth_config.get('GITHUB', {})
        
        # 检查配置是否完整
        client_id = github_config.get('CLIENT_ID')
        client_secret = github_config.get('CLIENT_SECRET')
        if not client_id or not client_secret:
            flash('GitHub登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取回调参数
        code = request.args.get('code')
        state = request.args.get('state')
        
        # 验证state参数防止CSRF攻击
        if not state or state != session.get('github_oauth_state'):
            flash('GitHub登录验证失败，请重试', 'danger')
            return redirect(url_for('auth.login'))
        
        # 清除state参数
        session.pop('github_oauth_state', None)
        
        # 构建获取访问令牌的请求
        token_url = github_config['TOKEN_URL']
        redirect_uri = github_config['REDIRECT_URI']
        
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'MTSCOS AI Project'
        }
        
        # 发送请求获取访问令牌
        response = requests.post(token_url, data=payload, headers=headers)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            flash('GitHub登录失败，无法获取访问令牌', 'danger')
            return redirect(url_for('auth.login'))
        
        access_token = token_data['access_token']
        
        # 使用访问令牌获取用户信息
        user_info_url = github_config['USER_INFO_URL']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'MTSCOS AI Project'
        }
        
        user_response = requests.get(user_info_url, headers=headers)
        user_data = user_response.json()
        
        # 提取用户信息
        github_id = user_data.get('id')
        username = user_data.get('login')
        email = user_data.get('email')
        name = user_data.get('name')
        
        if not github_id or not username:
            flash('GitHub登录失败，无法获取用户信息', 'danger')
            return redirect(url_for('auth.login'))
        
        # 检查用户是否已存在
        user = User.get_by_username(f'github_{username}')
        
        if not user:
            # 创建新用户
            user = User(
                username=f'github_{username}',
                email=email or f'{username}@github.com',
                password=security_utils.hash_password(str(github_id)),
                role='user',
                is_active=1,
                super_admin_approved=1,
                hardware_admin_approved=1
            )
            user_id = user.save()
            logger.info(f"创建GitHub用户: {user.username}, 用户ID: {user_id}")
        else:
            # 更新用户信息
            if email and user.email != email:
                user.email = email
                user.update()
            user_id = user.user_id
            logger.info(f"GitHub用户登录: {user.username}, 用户ID: {user_id}")
        
        # 使用SessionManager创建会话
        from app.utils.session_manager import session_manager
        login_type = 'github'
        device_info = f"GitHub: {username}"
        
        success, session_result = session_manager.create_session(
            user_id=user_id,
            username=user.username,
            login_type=login_type,
            device_info=device_info
        )
        
        if not success:
            flash(session_result, 'danger')
            return redirect(url_for('auth.login'))
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = user.username
        session['user_level'] = user.role
        session['user_role'] = user.role
        session['is_guest'] = False
        session['user_id'] = user_id
        session['email'] = user.email
        session['session_id'] = session_result
        session['user_group'] = 'user'
        
        # 为用户创建并绑定AI实例
        try:
            user_ai_id = get_user_ai_manager().bind_user_to_ai(user_id)
            session['user_ai_id'] = user_ai_id
        except Exception as ai_error:
            logger.error(f"创建AI实例失败: {str(ai_error)}")
        
        logger.info(f"GitHub登录成功: {user.username}, 角色: {user.role}")
        
        flash('GitHub登录成功', 'success')
        
        # 根据用户角色进行不同的跳转
        if user.role == 'student':
            return redirect(url_for('language_tests.test_system'))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"GitHub登录回调失败: {str(e)}")
        flash('GitHub登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/google/callback')
def google_callback():
    """Google登录回调处理"""
    try:
        logger.info("处理Google登录回调")
        
        # 从配置中获取Google OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        google_config = oauth_config.get('GOOGLE', {})
        
        # 检查配置是否完整
        client_id = google_config.get('CLIENT_ID')
        client_secret = google_config.get('CLIENT_SECRET')
        if not client_id or not client_secret:
            flash('Google登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取回调参数
        code = request.args.get('code')
        state = request.args.get('state')
        
        # 验证state参数防止CSRF攻击
        if not state or state != session.get('google_oauth_state'):
            flash('Google登录验证失败，请重试', 'danger')
            return redirect(url_for('auth.login'))
        
        # 清除state参数
        session.pop('google_oauth_state', None)
        
        # 构建获取访问令牌的请求
        token_url = google_config['TOKEN_URL']
        redirect_uri = google_config['REDIRECT_URI']
        
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'MTSCOS AI Project'
        }
        
        # 发送请求获取访问令牌
        response = requests.post(token_url, data=payload, headers=headers)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            flash('Google登录失败，无法获取访问令牌', 'danger')
            return redirect(url_for('auth.login'))
        
        access_token = token_data['access_token']
        
        # 使用访问令牌获取用户信息
        user_info_url = google_config['USER_INFO_URL']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'MTSCOS AI Project'
        }
        
        user_response = requests.get(user_info_url, headers=headers)
        user_data = user_response.json()
        
        # 提取用户信息
        google_id = user_data.get('id')
        email = user_data.get('email')
        name = user_data.get('name')
        given_name = user_data.get('given_name')
        family_name = user_data.get('family_name')
        
        if not google_id or not email:
            flash('Google登录失败，无法获取用户信息', 'danger')
            return redirect(url_for('auth.login'))
        
        # 生成用户名
        username = f'google_{google_id[:8]}'
        
        # 检查用户是否已存在
        user = User.get_by_username(username)
        
        if not user:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password=security_utils.hash_password(str(google_id)),
                role='user',
                is_active=1,
                super_admin_approved=1,
                hardware_admin_approved=1
            )
            user_id = user.save()
            logger.info(f"创建Google用户: {user.username}, 用户ID: {user_id}")
        else:
            # 更新用户信息
            if email and user.email != email:
                user.email = email
                user.update()
            user_id = user.user_id
            logger.info(f"Google用户登录: {user.username}, 用户ID: {user_id}")
        
        # 使用SessionManager创建会话
        from app.utils.session_manager import session_manager
        login_type = 'google'
        device_info = f"Google: {email}"
        
        success, session_result = session_manager.create_session(
            user_id=user_id,
            username=user.username,
            login_type=login_type,
            device_info=device_info
        )
        
        if not success:
            flash(session_result, 'danger')
            return redirect(url_for('auth.login'))
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = user.username
        session['user_level'] = user.role
        session['user_role'] = user.role
        session['is_guest'] = False
        session['user_id'] = user_id
        session['email'] = user.email
        session['session_id'] = session_result
        session['user_group'] = 'user'
        
        # 为用户创建并绑定AI实例
        try:
            user_ai_id = get_user_ai_manager().bind_user_to_ai(user_id)
            session['user_ai_id'] = user_ai_id
        except Exception as ai_error:
            logger.error(f"创建AI实例失败: {str(ai_error)}")
        
        logger.info(f"Google登录成功: {user.username}, 角色: {user.role}")
        
        flash('Google登录成功', 'success')
        
        # 根据用户角色进行不同的跳转
        if user.role == 'student':
            return redirect(url_for('language_tests.test_system'))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"Google登录回调失败: {str(e)}")
        flash('Google登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/auth/weixin/callback')
def weixin_callback():
    """微信登录回调处理"""
    try:
        logger.info("处理微信登录回调")
        
        # 从配置中获取微信OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        weixin_config = oauth_config.get('WEIXIN', {})
        
        # 检查配置是否完整
        app_id = weixin_config.get('APP_ID')
        app_secret = weixin_config.get('APP_SECRET')
        if not app_id or not app_secret:
            flash('微信登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 获取回调参数
        code = request.args.get('code')
        state = request.args.get('state')
        
        # 验证state参数防止CSRF攻击
        if not state or state != session.get('weixin_oauth_state'):
            flash('微信登录验证失败，请重试', 'danger')
            return redirect(url_for('auth.login'))
        
        # 清除state参数
        session.pop('weixin_oauth_state', None)
        
        # 构建获取访问令牌的请求
        token_url = weixin_config['TOKEN_URL']
        
        params = {
            'appid': app_id,
            'secret': app_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'MTSCOS AI Project'
        }
        
        # 发送请求获取访问令牌
        response = requests.get(token_url, params=params, headers=headers)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            flash('微信登录失败，无法获取访问令牌', 'danger')
            return redirect(url_for('auth.login'))
        
        access_token = token_data['access_token']
        openid = token_data['openid']
        
        # 使用访问令牌和openid获取用户信息
        user_info_url = weixin_config['USER_INFO_URL']
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN'
        }
        
        user_response = requests.get(user_info_url, params=params, headers=headers)
        user_data = user_response.json()
        
        # 提取用户信息
        weixin_id = user_data.get('openid')
        nickname = user_data.get('nickname')
        email = user_data.get('email', f'{weixin_id}@weixin.com')
        
        if not weixin_id:
            flash('微信登录失败，无法获取用户信息', 'danger')
            return redirect(url_for('auth.login'))
        
        # 生成用户名
        username = f'weixin_{weixin_id[:8]}'
        
        # 检查用户是否已存在
        user = User.get_by_username(username)
        
        if not user:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                password=security_utils.hash_password(str(weixin_id)),
                role='user',
                is_active=1,
                super_admin_approved=1,
                hardware_admin_approved=1
            )
            user_id = user.save()
            logger.info(f"创建微信用户: {user.username}, 用户ID: {user_id}")
        else:
            # 更新用户信息
            if email and user.email != email:
                user.email = email
                user.update()
            user_id = user.user_id
            logger.info(f"微信用户登录: {user.username}, 用户ID: {user_id}")
        
        # 使用SessionManager创建会话
        from app.utils.session_manager import session_manager
        login_type = 'weixin'
        device_info = f"Weixin: {nickname or weixin_id}"
        
        success, session_result = session_manager.create_session(
            user_id=user_id,
            username=user.username,
            login_type=login_type,
            device_info=device_info
        )
        
        if not success:
            flash(session_result, 'danger')
            return redirect(url_for('auth.login'))
        
        # 设置会话
        session['logged_in'] = True
        session['username'] = user.username
        session['user_level'] = user.role
        session['user_role'] = user.role
        session['is_guest'] = False
        session['user_id'] = user_id
        session['email'] = user.email
        session['session_id'] = session_result
        session['user_group'] = 'user'
        
        # 为用户创建并绑定AI实例
        try:
            user_ai_id = get_user_ai_manager().bind_user_to_ai(user_id)
            session['user_ai_id'] = user_ai_id
        except Exception as ai_error:
            logger.error(f"创建AI实例失败: {str(ai_error)}")
        
        logger.info(f"微信登录成功: {user.username}, 角色: {user.role}")
        
        flash('微信登录成功', 'success')
        
        # 根据用户角色进行不同的跳转
        if user.role == 'student':
            return redirect(url_for('language_tests.test_system'))
        else:
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"微信登录回调失败: {str(e)}")
        flash('微信登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/google/login')
def google_login():
    """Google登录视图"""
    try:
        logger.info("用户尝试使用Google登录")
        
        # 从配置中获取Google OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        google_config = oauth_config.get('GOOGLE', {})
        
        # 检查配置是否完整
        client_id = google_config.get('CLIENT_ID')
        if not client_id:
            flash('Google登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 生成随机state参数防止CSRF攻击
        import secrets
        state = secrets.token_urlsafe(32)
        session['google_oauth_state'] = state
        
        # 构建授权URL
        authorize_url = google_config['AUTHORIZE_URL']
        redirect_uri = google_config['REDIRECT_URI']
        scope = google_config['SCOPE']
        
        auth_url = f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&response_type=code"
        logger.info(f"重定向到Google授权页面: {auth_url}")
        
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Google登录失败: {str(e)}")
        flash('Google登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/weixin/login')
def weixin_login():
    """微信登录视图"""
    try:
        logger.info("用户尝试使用微信登录")
        
        # 从配置中获取微信OAuth配置
        from app import app
        oauth_config = app.config.get('OAUTH_CONFIG', {})
        weixin_config = oauth_config.get('WEIXIN', {})
        
        # 检查配置是否完整
        app_id = weixin_config.get('APP_ID')
        if not app_id:
            flash('微信登录配置未完成，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        # 生成随机state参数防止CSRF攻击
        import secrets
        state = secrets.token_urlsafe(32)
        session['weixin_oauth_state'] = state
        
        # 构建授权URL
        authorize_url = weixin_config['AUTHORIZE_URL']
        redirect_uri = weixin_config['REDIRECT_URI']
        scope = weixin_config['SCOPE']
        
        # 微信授权URL格式：https://open.weixin.qq.com/connect/qrconnect?appid=APPID&redirect_uri=REDIRECT_URI&response_type=code&scope=SCOPE&state=STATE#wechat_redirect
        auth_url = f"{authorize_url}?appid={app_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state={state}#wechat_redirect"
        logger.info(f"重定向到微信授权页面: {auth_url}")
        
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"微信登录失败: {str(e)}")
        flash('微信登录失败，请稍后重试', 'danger')
        return redirect(url_for('auth.login'))