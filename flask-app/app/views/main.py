# -*- coding: utf-8 -*-
import sqlite3
import time
# JSON import removed - using database
import os
import uuid
from functools import wraps
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, current_app
from app.utils.logging import logger
from app.config import Config
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
from app.ai.learning import ai_learning
from app.utils.network import network_optimizer
from app.models.question import Question, question_manager
from app.ai.question_generator import ai_question_generator
from app.ai.user_ai_manager import user_ai_manager
from app.ai.js_ai_manager import js_instance_manager
# 导入游客权限中间件
from app.middlewares.guest_permission import guest_permission_middleware

# 创建蓝图
main_bp = Blueprint('main', __name__)

# 装饰器：检查用户状态，确保用户状态正常，否则重定向到首页
def check_user_status(func):
    """检查用户状态的装饰器，确保用户状态正常，否则重定向到首页"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 检查用户是否已登录
            if not session.get('logged_in'):
                # 自动进行游客登录
                logger.info("用户未登录，自动进行游客登录")
                from app.models.user import User
                from app.utils.security import security_utils

                # 生成随机游客用户名
                guest_username = f"guest_{uuid.uuid4().hex[:8]}"
                guest_email = f"{guest_username}@guest.example.com"
                random_password = uuid.uuid4().hex[:16]
                hashed_password = security_utils.hash_password(random_password)

                # 创建游客用户记录到数据库
                guest_user = User(
                    username=guest_username,
                    email=guest_email,
                    password=hashed_password,
                    role='guest',
                    is_active=1,
                    super_admin_approved=1,
                    hardware_admin_approved=1
                )

                # 保存游客用户到数据库
                guest_user_id = guest_user.save()
                logger.info(f"创建游客用户成功: {guest_username}, ID: {guest_user_id}")

                # 设置会话
                session['logged_in'] = True
                session['username'] = guest_username
                session['user_level'] = 'guest'
                session['user_role'] = 'guest'
                session['is_guest'] = True
                session['user_id'] = guest_user_id
                session['session_id'] = str(uuid.uuid4())
                logger.info(f"设置会话成功: {session}")

            # 检查用户名是否存在
            username = session.get('username')
            if username is None:
                # 清除会话
                session.clear()
                # 重定向到首页
                return redirect(url_for('main.index'))

            # 检查用户ID是否存在
            user_id = session.get('user_id')
            if user_id is None:
                session.clear()
                return redirect(url_for('main.index'))
            # 检查用户角色是否存在
            if user_role is None:
                session.clear()
                # 重定向到首页

            # 检查会话ID是否存在（如果使用会话管理）
            if session_id is None:
                # 设置会话ID
            logger.info(f"用户状态检查通过: {username}, 角色: {user_role}, ID: {user_id}")
            pass
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"用户状态检查失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 清除会话
            # 重定向到首页
            return redirect(url_for('main.index'))
    return wrapper
# 兼容旧装饰器名称
def check_username(func):
    """兼容旧装饰器名称，使用新的用户状态检查装饰器"""

@main_bp.route('/')
def index():
        logger.info("访问主页，固定显示index.html")

        # 获取系统版本信息
        versions = {'system_version': '1.0.0'}
            from app.services.system_version_service import system_version_service
            versions = system_version_service.get_current_versions()
        except Exception as version_error:
            logger.error(f"获取系统版本信息失败: {str(version_error)}")

        # 检查用户是否已登录，未登录用户自动进行游客登录
        if not session.get('logged_in'):
            logger.info("用户未登录，自动进行游客登录")
            from app.utils.security import security_utils
            # 生成随机游客用户名
            guest_username = f"guest_{uuid.uuid4().hex[:8]}"
            random_password = uuid.uuid4().hex[:16]

            # 创建游客用户记录到数据库
                username=guest_username,
                password=hashed_password,
                is_active=1,
                hardware_admin_approved=1

            # 保存游客用户到数据库

            session['logged_in'] = True
            session['user_level'] = 'guest'
            session['is_guest'] = True

            user = {
                'role': 'guest'
        else:
            logger.info("用户已登录，验证用户信息")
            username = session.get('username')
            user_id = session.get('user_id')

            try:
                from app.utils.session_manager import session_manager
                # 验证会话是否有效
                    session_valid, session_message = session_manager.validate_session(session_id)
                        # 清除会话，重新登录
                        # 重定向到首页，触发自动游客登录

                if user_id:
                    if not user_from_db:
                        logger.warning(f"用户不存在: {user_id}")
                        # 清除会话，重新登录
                        session.clear()
                        # 重定向到首页，触发自动游客登录
                        return redirect(url_for('main.index'))

                    # 验证用户名是否匹配
                    if username != user_from_db.username:
                        logger.warning(f"用户名不匹配: {username} != {user_from_db.username}")
                        # 更新会话中的用户名
                        username = user_from_db.username

                # 更新用户信息
                user = {
                    'username': username,
                    'role': session.get('user_level', 'guest')
                }

                logger.info(f"用户信息验证成功: {username}")
            except Exception as validate_error:
                logger.error(f"验证用户信息失败: {str(validate_error)}")
                # 清除会话，重新登录
                session.clear()
                # 重定向到首页，触发自动游客登录

        # 将主页参数上传到数据库
        try:
            # 上传主页配置参数
            SystemConfigManager.set_config(
                key='homepage_url',
                value='/',
                description='系统主页URL',
                category='app_config',
                data_type='string'
            )
                key='homepage_template',
                value='index.html',
                description='系统主页模板',
                category='app_config',
                data_type='string'
            )

            SystemConfigManager.set_config(
                key='homepage_auto_login',
                description='是否自动登录游客用户',
                category='app_config',
            )

        except Exception as db_error:
            logger.error(f"上传主页参数到数据库失败: {str(db_error)}")

        # 固定显示index.html
        return render_template('index.html',
                           user=user,
                           versions=versions)
    except Exception as e:
        import traceback

        # 错误处理：直接返回首页模板，避免重定向
        return render_template('index.html',
                           error="系统错误，请稍后重试")

# 智能路由重定向，根据AI建议自动跳转到最佳页面
@main_bp.route('/smart-redirect')
def smart_redirect():
    try:
        best_route = ai_route_optimizer.calculate_best_route(session)
        logger.info(f"智能重定向到: {best_route}")
    except Exception as e:
        logger.error(f"智能重定向失败: {str(e)}")
        return redirect(url_for('main.index'))

# 核心功能路由 - AI推荐优先级排序

# 1. 仪表盘 - 管理员首选，已登录用户次选
@main_bp.route('/dashboard')
@check_username
def dashboard():
    """仪表盘视图 - AI推荐管理员和已登录用户的首选页面"""
    try:
        dashboard_data = {
            'system_status': '正常',
            'ai_instance_count': len(ai_instance_manager.ai_instances),
            'project_count': 0
        }
        # 准备监控面板数据
        monitoring_data = {
            'performance': network_optimizer.get_performance_metrics(),
            'error_stats': ai_monitor.get_error_stats(),
        }
        system_settings = {
            'ai_learning_enabled': Config.AI_CONFIG['LEARNING_ENABLED'],
            'ai_monitoring_enabled': Config.AI_CONFIG['MONITORING_ENABLED'],
            'self_optimization_enabled': Config.AI_CONFIG['SELF_OPTIMIZATION']
        }
        # 获取用户名
        username = session.get('username', 'Guest')

        return render_template('dashboard.html',
                           user={'username': username, 'role': session.get('user_level', 'guest')},
                           system_status=dashboard_data['system_status'],
                           project_count=dashboard_data['project_count'],
                           role_counts={},
                           monitoring_data=monitoring_data,
                           system_settings=system_settings)
    except Exception as e:
        logger.error(f"访问仪表盘时发生错误: {str(e)}")
        return f"访问仪表盘时发生错误: {str(e)}", 500

# 2. 测试系统相关路由 - 游客和已登录用户首选
@main_bp.route('/test-center')
@guest_permission_middleware.require_guest_permission()
def test_center():
    """测试中心 - AI推荐游客和已登录用户的首选页面"""
    try:
        user = {
            'role': session.get('user_level', 'guest')
        }

        # 检查用户角色，管理员不能参加测试
        if session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            flash('管理员不能参加测试', 'error')
            return redirect(url_for('main.dashboard'))

        return redirect(url_for('language_tests.test_system'))
    except Exception as e:
        logger.error(f"访问测试中心时发生错误: {str(e)}")
        return f"访问测试中心时发生错误: {str(e)}", 500

@main_bp.route('/japanese_test')
@check_username
@guest_permission_middleware.require_guest_permission()
def japanese_test():
    """日语测试页面 - AI推荐已登录用户的次选页面"""
    try:
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        # 检查用户角色，管理员、超级管理员和硬件管理员不能参加测试
        if session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            flash('管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试', 'error')
            return redirect(url_for('main.dashboard'))

        # 初始化test_paper为None
        test_paper = None

        # 检查用户日语等级
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_japanese_levels WHERE username = ?', (username,))
        user_level = cursor.fetchone()
        conn.close()

        if not user_level or user_level[2] is None:  # user_level[2] 是 level 字段
            # 用户没有日语等级记录或等级为空，重定向到等级测试
            flash('您还没有设置日语等级，请先进行等级测试', 'info')
            return redirect(url_for('main.japanese_level_test'))

        # 生成测试试卷
        from app.ai.test_generator import test_generator
        test_paper = test_generator.generate_test_paper(
            language='japanese',
            level='intermediate'
        )

        return render_template('japanese_test.html', user=user, test_paper=test_paper)
    except Exception as e:
        logger.error(f"访问日语测试页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问日语测试页面时发生错误: {str(e)}", 500
@main_bp.route('/japanese_level_test')
@check_username
def japanese_level_test():
    """日语等级测试页面 - AI推荐游客的次选页面"""
    try:
        username = session.get('username')
        user = {
        }
        # 检查用户角色，管理员、超级管理员和硬件管理员不能参加测试
        if session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            flash('管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试', 'error')
            return redirect(url_for('main.dashboard'))
        return render_template('japanese_level_test.html', user=user)
    except Exception as e:
        logger.error(f"访问日语等级测试页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问日语等级测试页面时发生错误: {str(e)}", 500

@main_bp.route('/english_test')
@check_username
def english_test():
    """英语测试页面"""
    try:
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        # 检查用户角色，管理员、超级管理员和硬件管理员不能参加测试
            flash('管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试', 'error')
            return redirect(url_for('main.dashboard'))
        # 生成测试试卷
        from app.ai.test_generator import test_generator
        test_paper = test_generator.generate_test_paper(
            language='english',
            level='intermediate'

        return render_template('english_test.html', user=user, test_paper=test_paper)
    except Exception as e:
        logger.error(f"访问英语测试页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问英语测试页面时发生错误: {str(e)}", 500

@check_username
@guest_permission_middleware.require_guest_permission()
    """结合测试页面，整合日语和英语测试"""
    try:
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        # 检查用户角色，管理员、超级管理员和硬件管理员不能参加测试
        if session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            flash('管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试', 'error')
            return redirect(url_for('main.dashboard'))
        return render_template('combined_test.html', user=user)
    except Exception as e:
        logger.error(f"访问结合测试页面时发生错误: {str(e)}")
        return f"访问结合测试页面时发生错误: {str(e)}", 500

# 3. 管理员功能路由 - AI推荐管理员的关键功能
@main_bp.route('/admin')
@check_username
def admin_center():
    """管理员中心 - AI推荐管理员的统一入口"""
    try:
        logger.info(f"User role from session: {user_role}")
        logger.info(f"Session contents: {session}")
            return redirect(url_for('main.smart_redirect'))

        # 获取用户权限
        from app.utils.permission_enhance import get_user_permissions, define_permissions
        logger.info(f"User permissions: {user_permissions}")
        logger.info(f"All permissions: {define_permissions()}")

        # 根据用户角色和权限生成可访问的管理页面
        admin_pages = []
        # 系统管理页面
        if 'system_config' in user_permissions:
                'url': url_for('main.system_config'),
                'icon': 'fas fa-cogs',
                'description': '管理系统配置参数'
            })

            admin_pages.append({
                'name': '用户管理',

        # 系统监控页面
            admin_pages.append({
                'name': '系统监控',
                'icon': 'fas fa-chart-line',
                'description': '监控系统运行状态'
            })

        if 'permission_management' in user_permissions:
            admin_pages.append({
                'name': '权限管理',
                'icon': 'fas fa-shield-alt',
                'description': '管理用户权限和角色'

        # 智能系统配置页面
        if 'system_config' in user_permissions:
                    'name': '智能系统配置',
                    'url': url_for('smart_system_config.smart_system_config'),
                    'icon': 'fas fa-robot',
                })
                logger.error(f"智能系统配置页面链接错误: {str(e)}")
        # 智能仪表板页面
            try:
                    'icon': 'fas fa-tachometer-alt',
                })
            except Exception as e:
                logger.error(f"智能仪表板页面链接错误: {str(e)}")

            try:
                    'url': url_for('enhanced_monitoring.enhanced_monitoring'),
                    'description': '增强系统监控'
                })
                logger.error(f"增强监控页面链接错误: {str(e)}")

        username = session.get('username', 'Admin')
        user = {
            'username': username,
            'role': user_role
        return render_template('admin_center.html', user=user, admin_pages=admin_pages)
        logger.error(f"访问管理员中心时发生错误: {str(e)}")
        return f"访问管理员中心时发生错误: {str(e)}", 500

# 权限管理 - AI推荐管理员的第二优先级功能
@check_username
def permissions():
    try:
        from app.utils.permission_enhance import get_user_permissions
        user_permissions = get_user_permissions()

            flash('没有权限访问权限管理页面', 'error')
            return redirect(url_for('main.smart_redirect'))

        # 准备用户信息
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        # 从数据库获取所有用户
        from app.models.user import User

        # 转换用户数据为模板需要的格式
        users_data = []
        for user_data in users:
            users_data.append({
                'id': user_data.user_id,
                'username': user_data.username,
                'email': user_data.email,
                'role': user_data.role,
                'is_active': user_data.is_active,
                'super_admin_approved': user_data.super_admin_approved,
                'hardware_admin_approved': user_data.hardware_admin_approved
            })

        return render_template('permissions.html', user=user, users=users_data)
    except Exception as e:
        logger.error(f"访问权限管理页面时发生错误: {str(e)}")

# 系统配置 - AI推荐管理员的第三优先级功能
@main_bp.route('/system_config')
@check_username
def system_config():
    """系统配置页面 - AI推荐管理员的第三优先级功能"""
    try:
        from app.utils.permission_enhance import get_user_permissions
        user_permissions = get_user_permissions()

        if 'system_config' not in user_permissions:
            flash('没有权限访问系统配置页面', 'error')
            return redirect(url_for('main.smart_redirect'))

        # 准备用户信息
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }
        # 从数据库获取所有系统配置
        from app.models.system_config import SystemConfig

        config_groups = {
            'database': [],
            'ai': [],
            'authentication': [],
            'security': [],
            'system': [],
            'ui': [],
            'monitoring': [],
            'backup': [],
            'user_data': []

        # 配置分组映射
        group_mapping = {
            'db_': 'database',
            'database_': 'database',
            'password_': 'authentication',
            'login_': 'authentication',
            'csrf_': 'security',
            'cors_': 'security',
            'auto_': 'system',
            'system_': 'system',
            'default_': 'ui',
            'smtp_': 'email',
            'monitoring_': 'monitoring',
            'backup_': 'backup',
            'user_data_': 'user_data'
        }

        # 分配配置到相应分组
        for config in configs:
            group = 'system'  # 默认分组
                if config.config_key.startswith(prefix):
                    break
            config_groups[group].append(config)
        return render_template('system_config.html', user=user, config_groups=config_groups)
        logger.error(f"访问系统配置页面时发生错误: {str(e)}")
        return f"访问系统配置页面时发生错误: {str(e)}", 500
@main_bp.route('/projects')
@check_username
def projects():
    """项目管理页面"""
    try:
        username = session.get('username')
        user = {
            'username': username,
        }

        return render_template('projects.html', user=user)
        logger.error(f"访问项目管理页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问项目管理页面时发生错误: {str(e)}", 500

@main_bp.route('/tasks')
@check_username
def tasks():
    try:
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        return render_template('tasks.html', user=user)
    except Exception as e:
        logger.error(f"访问任务管理页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问任务管理页面时发生错误: {str(e)}", 500

@check_username
def reports():
    try:
        user = {
            'username': username,

    except Exception as e:
        logger.error(f"访问报告中心页面时发生错误: {str(e)}")
        # 直接返回错误信息，避免循环重定向
        return f"访问报告中心页面时发生错误: {str(e)}", 500

@main_bp.route('/hardware')
@check_username
def hardware():
    try:
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        return render_template('hardware.html', user=user)
    except Exception as e:
        logger.error(f"访问硬件管理页面时发生错误: {str(e)}")
        return f"访问硬件管理页面时发生错误: {str(e)}", 500

@main_bp.route('/ai_rules')
@check_username
def ai_rules():
    """AI规则管理页面"""
    try:
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        return render_template('ai_rules.html', user=user)
    except Exception as e:
        logger.error(f"访问AI规则管理页面时发生错误: {str(e)}")
        return f"访问AI规则管理页面时发生错误: {str(e)}", 500

@main_bp.route('/approval')
@check_username
def approval():
    try:
        user = {

        return render_template('approval.html', user=user)
    except Exception as e:
        logger.error(f"访问审批管理页面时发生错误: {str(e)}")
        return f"访问审批管理页面时发生错误: {str(e)}", 500

@check_username
    """系统监控页面"""
    try:
        user_permissions = get_user_permissions()

            return redirect(url_for('main.smart_redirect'))

        # 准备用户信息
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')

        return render_template('system_monitoring.html', user=user)
    except Exception as e:
        logger.error(f"访问系统监控页面时发生错误: {str(e)}")
        return f"访问系统监控页面时发生错误: {str(e)}", 500
@main_bp.route('/cleanup')
    """系统清理页面"""
        username = session.get('username')
        user = {
            'username': username,
            'role': session.get('user_level', 'guest')
        }

        return render_template('cleanup.html', user=user)
    except Exception as e:
        logger.error(f"访问系统清理页面时发生错误: {str(e)}")

@main_bp.route('/hardware_keys')
@check_username
def hardware_keys():
    try:
        username = session.get('username')
        }

        # 模拟硬件密钥数据
        keys = []
        for i in range(1, 6):
            keys.append({
                'key_id': f'VIKEY-{1000 + i}',
                'key_type': 'USB',
                'device_id': f'DEV-{2000 + i}',
                'is_active': True,
                'expiration_date': '2026-10-01'
            })

        return render_template('hardware_keys.html', user=user, keys=keys)
        logger.error(f"访问硬件密钥管理页面时发生错误: {str(e)}")


@main_bp.route('/api/questions/settings', methods=['GET'])
def get_question_settings():
    """获取题库设置信息，支持离线访问"""
    try:
        status = ai_question_generator.get_generation_status()

        question_counts = {}
        for language in status['supported_languages']:
            for level in status['supported_levels']:
                for category in status['supported_categories'][language]:
                    count = Question.get_question_count(language, level, category)
        return jsonify({
            'settings': status,
            'question_counts': question_counts
        }), 200
        logger.error(f"获取题库设置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取题库设置失败: {str(e)}'
        }), 500

# 测试生成API
def generate_japanese_test():
            return jsonify({
                'success': False,
                'error': '管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试'
            }), 403
        # 允许游客生成测试试卷，使用默认用户名'guest'

        test_type = request.json.get('test_type', 'practice')
        level = request.json.get('level')
        categories = request.json.get('categories', [])
        question_count = request.json.get('question_count')
        # 使用第一个选中的类别作为主类别
        category = categories[0] if categories else None
        # 生成测试试卷
        from app.ai.test_generator import test_generator
        test_paper = test_generator.generate_test_paper(
            language='japanese',
            level=level,

        return jsonify({
            'success': True,
        }), 200
        return jsonify({
            'success': False,
            'error': f'生成测试试卷失败: {str(e)}'
        }), 500

@main_bp.route('/api/english-test/generate', methods=['POST'])
def generate_english_test():
    """生成英语测试试卷"""
        if 'logged_in' in session and session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'error': '管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试'
        # 允许游客生成测试试卷，使用默认用户名'guest'

        test_type = request.json.get('test_type', 'practice')
        level = request.json.get('level')
        categories = request.json.get('categories', [])
        question_count = request.json.get('question_count')
        # 使用第一个选中的类别作为主类别
        category = categories[0] if categories else None

        # 生成测试试卷
        from app.ai.test_generator import test_generator
        test_paper = test_generator.generate_test_paper(
            language='english',
            level=level,

        return jsonify({
            'success': True,
        }), 200
    except Exception as e:
        logger.error(f"生成英语测试试卷失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'生成测试试卷失败: {str(e)}'
        }), 500

@main_bp.route('/api/japanese-test/submit', methods=['POST'])
def submit_japanese_test():
    """提交日语测试"""
        if 'logged_in' in session and session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'error': '管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试'
            }), 403
        # 允许游客提交测试，使用默认用户名'guest'
        username = session.get('username', 'guest')
        answers = request.json.get('answers', {})

        # 检查是否有答案
        if not answers:
            return jsonify({
                'error': '请至少回答一道题目'
            }), 400

        # 计算得分
        correct_count = 0
        total_questions = len(answers)

        # 从数据库中获取正确答案并计算得分
        from app.models.question import Question

        # 题型名称映射
        question_type_names = {
            'multiple_choice': '选择题',
            'fill_in_blank': '填空题',
            'true_false': '判断题',
            'short_answer': '简答题'
        }
        # 构建结果
        # 生成question_results数据
        question_results = []
        for question_id, user_answer in answers.items():
            if question_id.startswith('sample_'):
                correct_answer = 'A' if 'multiple_choice' in question_id else '正确' if 'true_false' in question_id else '答案示例'
                question_type = 'multiple_choice' if 'multiple_choice' in question_id else 'true_false' if 'true_false' in question_id else 'fill_in_blank' if 'fill_in_blank' in question_id else 'short_answer'
                explanation = f'本题解析：{question_id}的正确答案是{correct_answer}'
                question_content = f'模拟题目：{question_id}'
                type_name = question_type_names.get(question_type, '选择题')

                # 不同题型的正确判断逻辑
                if question_type == 'true_false':
                    is_correct = user_answer == correct_answer
            else:
                question = question_manager.get_question(question_id)
                if question:
                    correct_answer = question.answer
                    explanation = question.explanation or '暂无解析'
                    question_content = question.content
                    question_type = question.question_type
                    type_name = question_type_names.get(question_type, '选择题')

                    # 不同题型的正确判断逻辑
                    if question_type == 'true_false':
                        # 判断题：处理多种可能的正确答案格式
                        is_correct = user_answer == correct_answer or \
                                    (correct_answer.lower() == 'true' and user_answer in ['true', 'True', '正确', '✓']) or \
                    elif question_type in ['fill_in_blank', 'short_answer']:
                        # 填空题和简答题：允许一定的灵活性，这里简单比较
                        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
                    else:
                        # 选择题：精确匹配
                        is_correct = user_answer == correct_answer

                    # 更新题目使用情况
                    accuracy = 1.0 if is_correct else 0.0
                    Question.update_question_usage(question_id, accuracy)
                else:
                    correct_answer = 'A'  # 默认正确答案
                    explanation = '题目不存在'
                    question_content = '题目不存在'
                    type_name = '选择题'
                    is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1

            question_results.append({
                'question_id': question_id,
                'is_correct': is_correct,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'question': question_content,
                'type_name': type_name,
                'max_score': 100 / total_questions
            })

        # 计算分数
        score = round((correct_count / total_questions) * 100)

        result = {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'username': username,
            'test_type': 'japanese_practice',
            'submitted_at': time.strftime("%Y-%m-%d %H:%M:%S"),
            'duration': 0,  # 实际应该从请求中获取
            'question_results': question_results
        }

        logger.info(f"用户 {username} 提交日语测试，得分: {score}/{100}")

        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        logger.error(f"提交日语测试失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'提交测试失败: {str(e)}'
        }), 500

@main_bp.route('/api/japanese-test/submit-level-test', methods=['POST'])
def submit_japanese_level_test():
    """提交日语等级测试"""
    try:
        if 'logged_in' in session and session.get('user_level') in ['admin', 'super_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'error': '管理员、超级管理员和硬件管理员不符合系统要求，不能参加测试'
            }), 403

        username = session.get('username', 'guest')
        answers = request.json.get('answers', {})
        # 检查是否有答案
        if not answers:
                'success': False,
                'error': '请至少回答一道题目'

        # 计算得分
        correct_count = 0
        total_questions = len(answers)

        # 从数据库中获取正确答案并计算得分
        from app.models.question import Question

        # 题型名称映射
        question_type_names = {
            'multiple_choice': '选择题',
            'fill_in_blank': '填空题',
            'true_false': '判断题',
            'short_answer': '简答题'
        }

        # 构建结果
        # 生成question_results数据
        question_results = []
        for question_id, user_answer in answers.items():
            # 检查是否是示例题目
            if question_id.startswith('sample_'):
                # 模拟示例题目
                question_type = 'multiple_choice' if 'multiple_choice' in question_id else 'true_false' if 'true_false' in question_id else 'fill_in_blank' if 'fill_in_blank' in question_id else 'short_answer'
                question_content = f'模拟题目：{question_id}'
                type_name = question_type_names.get(question_type, '选择题')

                # 不同题型的正确判断逻辑
                if question_type == 'true_false':
                    is_correct = user_answer == correct_answer or user_answer == 'true' if correct_answer == '正确' else user_answer == 'false'
                else:
            else:
                # 从数据库中获取题目
                question = question_manager.get_question(question_id)
                    correct_answer = question.answer
                    explanation = question.explanation or '暂无解析'
                    question_content = question.content
                    type_name = question_type_names.get(question_type, '选择题')

                    if question_type == 'true_false':
                        # 判断题：处理多种可能的正确答案格式
                        is_correct = user_answer == correct_answer or \
                                    (correct_answer.lower() == 'true' and user_answer in ['true', 'True', '正确', '✓']) or \
                                    (correct_answer.lower() == 'false' and user_answer in ['false', 'False', '错误', '✗'])
                    elif question_type in ['fill_in_blank', 'short_answer']:
                        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
                    else:
                        # 选择题：精确匹配

                    # 更新题目使用情况
                    accuracy = 1.0 if is_correct else 0.0
                    Question.update_question_usage(question_id, accuracy)
                else:
                    correct_answer = 'A'  # 默认正确答案
                    explanation = '题目不存在'
                    question_content = '题目不存在'
                    type_name = '选择题'

                correct_count += 1

            question_results.append({
                'is_correct': is_correct,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'type_name': type_name,
            })

        score = round((correct_count / total_questions) * 100)
        # 确定等级
            level = 5  # N1
        elif score >= 70:
        elif score >= 60:
        else:

        result = {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'level': level,
            'test_type': 'japanese_level',
            'duration': 0,  # 实际应该从请求中获取
            'question_results': question_results
        }

        logger.info(f"用户 {username} 提交日语等级测试，得分: {score}/{100}，等级: {level}")
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,

# 窄路临时题目生成API
@main_bp.route('/api/narrow-road/questions/generate', methods=['POST'])
def generate_narrow_road_questions():
    try:
        count = request.json.get('count', 10)
        language = request.json.get('language', 'japanese')
        level = request.json.get('level', 'beginner')
        category = request.json.get('category', '日常对话')

        # 导入窄路临时题库
        from app.ai.narrow_road_question_bank import narrow_road_question_bank

        # 生成题目
        questions = narrow_road_question_bank.generate_questions(
            count=count,
            language=language,
            level=level,
            category=category
        )

        logger.info(f"成功生成 {len(questions)} 道窄路临时题目")

        return jsonify({
            'success': True,
            'questions': questions
        }), 200
    except Exception as e:
        logger.error(f"生成窄路临时题目失败: {str(e)}")
        return jsonify({
            'success': False,
        }), 500
# 保存用户语言等级API
@main_bp.route('/api/save-language-level', methods=['POST'])
def save_language_level():
    """保存用户语言等级"""
    try:
        if not session.get('logged_in') or not session.get('user_id'):
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401

        # 获取请求数据
        language = request.json.get('language')
        level = request.json.get('level')
        score = request.json.get('score')

        if not language or not level:
            return jsonify({
                'error': '缺少必要参数'
            }), 400

        # 保存用户语言等级
        from app.models.learning_system import LearningSystem

        subject = f"{language}_level"

        # 保存用户等级
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()

        # 检查是否已存在记录
        cursor.execute('''
            SELECT * FROM user_learning_levels WHERE user_id=? AND subject=?
        ''', (session.get('user_id'), subject))

            # 更新现有记录
            cursor.execute('''
                WHERE user_id=? AND subject=?
        else:
            # 创建新记录
            cursor.execute('''
                INSERT INTO user_learning_levels (user_id, subject, level, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (session.get('user_id'), subject, level))

        conn.commit()
        conn.close()


        return jsonify({
            'success': True,
            'message': '语言等级保存成功',
            'level': level,
            'score': score
        }), 200
    except Exception as e:
        logger.error(f"保存用户语言等级失败: {str(e)}")
            'success': False,
            'error': f'保存语言等级失败: {str(e)}'
        }), 500

# 数据库同步API
@main_bp.route('/api/database/sync', methods=['POST'])
def sync_database():
    """同步数据库，上传本地数据到服务器"""
    try:
        local_data = request.json.get('local_data', {})

        logger.info(f"收到数据库同步请求，数据大小: {len(str(local_data))} 字节")

        # 这里可以添加数据整合AI的逻辑

        return jsonify({
            'success': True,
            'message': '数据同步成功',
            'synced_data': local_data
        }), 200
    except Exception as e:
        logger.error(f"数据库同步失败: {str(e)}")
        return jsonify({
            'success': False,
        }), 500

# 系统配置API
@main_bp.route('/api/system-config', methods=['GET'])
def get_system_configs():
    try:
        configs = SystemConfig.get_all_configs_with_inactive()

        configs_data = []
        for config in configs:
            configs_data.append({
                'config_key': config.config_key,
                'config_value': config.config_value,
                'config_type': config.config_type,
                'is_active': config.is_active
            })

        return jsonify({
            'success': True,
        }), 200
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取系统配置失败: {str(e)}'
        }), 500
@main_bp.route('/api/system-config', methods=['POST'])
def add_system_config():
    """添加系统配置"""
    try:


        # 验证必填字段
        if not data or not all(key in data for key in ['config_key', 'config_value', 'config_type']):
                'success': False,
                'error': '缺少必填字段'
            }), 400
        # 检查配置键是否已存在
        if existing_config:
                'success': False,
                'error': '配置项已存在'

        username = session.get('username', 'guest')
        user_role = session.get('user_level', 'guest')
        # 超级管理员和硬件管理员可以直接修改配置，其他用户需要审批
            # 直接创建新配置
                config_key=data['config_key'],
                config_type=data['config_type'],
                is_active=data.get('is_active', 1)
            config.save()

            logger.info(f"超级管理员/硬件管理员{username}直接添加配置: {data['config_key']}")
            return jsonify({
            }), 201
            # 创建审批请求
                config_key=data['config_key'],
                new_value=data['config_value'],
                category=data.get('category', 'general'),
                requested_by=username,
            )


                'success': True,
            }), 201
    except Exception as e:
        logger.error(f"添加系统配置失败: {str(e)}")
            'success': False,
            'error': f'添加系统配置失败: {str(e)}'

@main_bp.route('/api/system-config/<config_key>', methods=['PUT'])
    """更新系统配置"""
    try:


        # 获取配置
        config = SystemConfig.get_by_key(config_key)
            all_configs = SystemConfig.get_all_configs_with_inactive()
            if not config:
                    'error': '配置项不存在'

        username = session.get('username', 'guest')

        if user_role in ['super_admin', 'hardware_vikey_admin']:
            # 直接更新配置
            if 'config_value' in data:
                config.config_value = data['config_value']
                config.config_type = data['config_type']
                config.description = data['description']
                config.category = data['category']
                config.is_active = data['is_active']
            config.save()

                'success': True,
            }), 200
        else:
            old_value = config.config_value
            new_value = data.get('config_value', old_value)
            approval = ConfigApproval(
                new_value=new_value,
                category=data.get('category', config.category),
                requested_by=username,
                requested_role=user_role
            approval.save()
            logger.info(f"用户{username}提交配置更新请求: {config_key}，等待审批")
            return jsonify({
                'message': '配置更新请求已提交，等待审批'
            }), 200
    except Exception as e:
        return jsonify({
            'error': f'更新系统配置失败: {str(e)}'
# 审批相关API
def get_config_approvals():
    try:
        # 获取审批列表

        approval_list = []
            approval_list.append({
                'config_key': approval.config_key,
                'new_value': approval.new_value,
                'category': approval.category,
                'data_type': approval.data_type,
                'requested_by': approval.requested_by,
                'status': approval.status

            'success': True,
            'approvals': approval_list
        }), 200
    except Exception as e:
        logger.error(f"获取配置审批列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取配置审批列表失败: {str(e)}'
        }), 500

@main_bp.route('/api/config-approval/<int:approval_id>/approve', methods=['POST'])
def approve_config(approval_id):
    """批准配置变更"""

        username = session.get('username', 'guest')

        if user_role not in ['super_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'error': '没有权限审批配置变更'

        approval = ConfigApproval.get_by_id(approval_id)
            return jsonify({
                'success': False,
                'error': '审批请求不存在'
            }), 404

        # 批准变更
        approval.approve(username)
        logger.info(f"{username}批准了配置变更请求: {approval.config_key}")

        return jsonify({
            'success': True,
            'message': '配置变更已批准'
        }), 200
        logger.error(f"批准配置变更失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'批准配置变更失败: {str(e)}'
        }), 500

@main_bp.route('/api/config-approval/<int:approval_id>/reject', methods=['POST'])
def reject_config(approval_id):
    """拒绝配置变更"""
    try:

        # 获取当前用户信息
        username = session.get('username', 'guest')
        user_role = session.get('user_level', 'guest')

        # 只有超级管理员和硬件管理员可以审批
        if user_role not in ['super_admin', 'hardware_vikey_admin']:
            return jsonify({
                'success': False,
                'error': '没有权限审批配置变更'
            }), 403

        # 获取审批请求
        approval = ConfigApproval.get_by_id(approval_id)
        if not approval:
                'error': '审批请求不存在'

        # 获取拒绝原因
        data = request.json
        comments = data.get('comments', '')
        # 拒绝变更
        approval.reject(username, comments)

        logger.info(f"{username}拒绝了配置变更请求: {approval.config_key}")

        return jsonify({
            'success': True,
            'message': '配置变更已拒绝'
        }), 200
    except Exception as e:
        logger.error(f"拒绝配置变更失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'拒绝配置变更失败: {str(e)}'
        }), 500

@main_bp.route('/api/system-config/<config_key>', methods=['DELETE'])
def delete_system_config(config_key):
    """删除系统配置"""
    try:

        SystemConfig.delete_by_key(config_key)

        return jsonify({
            'success': True,
            'message': '配置删除成功'
        }), 200
    except Exception as e:
        logger.error(f"删除系统配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'删除系统配置失败: {str(e)}'
        }), 500

# 用户管理API
@main_bp.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    try:
        users = User.get_all_users()

        # 转换为字典列表
        users_data = []
        for user in users:
            users_data.append({
                'id': user.user_id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'super_admin_approved': user.super_admin_approved,
                'hardware_admin_approved': user.hardware_admin_approved,
                'avatar': user.avatar,
                'created_at': user.created_at,
            })
        return jsonify({
            'success': True,
            'users': users_data
        }), 200
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户列表失败: {str(e)}'
        }), 500

@main_bp.route('/api/users/<username>', methods=['GET'])
    """通过用户名获取用户"""
    try:
        user = User.get_by_username(username)

        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_active': user.is_active,
                    'hardware_admin_approved': user.hardware_admin_approved,
                    'avatar': user.avatar,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '用户不存在'
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户信息失败: {str(e)}'
        }), 500

@main_bp.route('/api/users', methods=['POST'])
def add_user():
    """添加新用户"""
    try:
        from app.utils.security import security_utils

        data = request.json

        # 验证必填字段
        if not data or not all(key in data for key in ['username', 'email', 'password', 'role']):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400

        existing_user = User.get_by_username(data['username'])
        if existing_user:
            return jsonify({
                'success': False,
                'error': '用户名已存在'
            }), 400

        # 创建新用户
        hashed_password = security_utils.hash_password(data['password'])
        user = User(
            username=data['username'],
            password=hashed_password,
            role=data['role'],
            is_active=1,
            super_admin_approved=1 if data['role'] != 'super_admin' else 0,
            hardware_admin_approved=1 if data['role'] != 'hardware_vikey_admin' else 0
        )
        user.save()

        return jsonify({
            'success': True,
            'message': '用户添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'添加用户失败: {str(e)}'
        }), 500

@main_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
        from app.utils.security import security_utils

        data = request.json
        user = User.get_by_id(user_id)

        if not user:
                'success': False,
                'error': '用户不存在'
            }), 404

        # 更新用户信息
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data and data['password']:
            user.password = security_utils.hash_password(data['password'])
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']

        user.save()

        return jsonify({
            'success': True,
            'message': '用户更新成功'
        }), 200
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'更新用户失败: {str(e)}'
        }), 500

@main_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""

        if not user:
            return jsonify({
                'error': '用户不存在'
        user.delete()

        return jsonify({
            'success': True,
            'message': '用户删除成功'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除用户失败: {str(e)}'
        }), 500

# 自适应初次等级评测API
@main_bp.route('/api/placement-test/start', methods=['POST'])
def start_placement_test():
    """开始自适应初次等级评测"""
    try:

        from app.services.adaptive_placement_test_service import get_adaptive_placement_test_service
        service = get_adaptive_placement_test_service()

        result = service.generate_initial_test(language)

        if result['success']:
            # 保存测试状态到session
            session['placement_test'] = {
                'test_id': result['test_id'],
                'language': language,
                'current_question': result['current_question'],
                'adaptive_state': result['adaptive_state']
            }

            logger.info(f"开始初次等级评测，语言: {language}，测试ID: {result['test_id']}")
        return jsonify(result), 200 if result['success'] else 500
    except Exception as e:
            'error': f'开始评测失败: {str(e)}'
        }), 500

@main_bp.route('/api/placement-test/next', methods=['POST'])
def next_placement_test_questions():
    """获取下一组初次等级评测题目"""
    try:
        # 从session中获取测试状态
        if not test_state:
            return jsonify({
                'success': False,
                'error': '测试状态不存在，请重新开始测试'
            }), 400

        from app.services.adaptive_placement_test_service import get_adaptive_placement_test_service
        service = get_adaptive_placement_test_service()

        result = service.get_next_questions(test_state, answers, test_state.get('language', 'japanese'))

        if result['success']:
            # 更新session中的测试状态
            session['placement_test'].update({
                'current_difficulty': result['current_difficulty'],
                'adaptive_state': result['adaptive_state']
            })

            # 如果测试完成，保存结果
            if result.get('is_complete') and 'final_level' in result:
                user_id = session.get('user_id')
                if user_id:
                    service.save_test_result(
                        user_id=user_id,
                        final_level=result['final_level'],
                    )
                    # 清除session中的测试状态


        return jsonify(result), 200 if result['success'] else 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取题目失败: {str(e)}'
        }), 500
@main_bp.route('/api/placement-test/complete', methods=['POST'])
    """完成初次等级评测并保存结果"""
    try:
            return jsonify({
                'success': False,
                'error': '测试状态不存在'
            }), 400

        final_level = request.json.get('final_level')
            return jsonify({
                'success': False,
                'error': '缺少最终等级'
            }), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401

        from app.services.adaptive_placement_test_service import get_adaptive_placement_test_service
        service = get_adaptive_placement_test_service()

        success = service.save_test_result(
            user_id=user_id,
            language=test_state.get('language', 'japanese'),
            final_level=final_level,
            test_data=test_state
        )
        # 清除session中的测试状态
        session.pop('placement_test', None)


        return jsonify({
            'message': '评测结果保存成功' if success else '评测结果保存失败'
        }), 200
    except Exception as e:
        logger.error(f"完成初次等级评测失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'保存结果失败: {str(e)}'
        }), 500
