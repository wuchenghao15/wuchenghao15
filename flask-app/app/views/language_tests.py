# Language Tests Blueprint
from flask import Blueprint, render_template, session, redirect, url_for

# 导入用户状态检查装饰器
from app.views.main import check_user_status
# 导入游客权限中间件
from app.middlewares.guest_permission import guest_permission_middleware
# 导入学习系统模型
from app.models.learning_system import LearningSystem
# 导入路由管理器
from app.utils.route_manager import route_manager

# 创建语言测试蓝图
language_tests_bp = Blueprint('language_tests', __name__)

# 注册蓝图到路由管理器
route_manager.register_blueprint(language_tests_bp)

# 语言测试系统路由
@language_tests_bp.route('/english-test')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def english_test():
    """英语测试系统"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    return render_template('english_test.html', user=user)

@language_tests_bp.route('/japanese-test')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def japanese_test():
    """日语测试系统"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    return render_template('japanese_test.html', user=user)

@language_tests_bp.route('/japanese-level-test')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def japanese_level_test():
    """日语等级测试系统"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    return render_template('japanese_level_test.html', user=user)

@language_tests_bp.route('/unified-level-test')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def unified_level_test():
    """统一等级测试系统"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    return render_template('unified_level_test.html', user=user)

@language_tests_bp.route('/test-system')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def test_system():
    """测试系统入口 - 语言测试系统主页"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    # 普通用户和游客进入语言测试系统主页
    return render_template('test_system.html', user=user)

@language_tests_bp.route('/test-system/japanese')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def test_system_japanese():
    """测试系统日语测试入口"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    
    # 检查用户是否登录
    if session.get('user_id'):
        # 获取用户日语等级
        user_level = LearningSystem.get_user_language_level(session.get('user_id'), 'japanese')
        
        # 如果用户没有日语等级，重定向到等级评测测试
        if not user_level:
            return redirect(url_for('language_tests.level_assessment'))
    
    return render_template('japanese_test.html', user=user)

@language_tests_bp.route('/test-system/english')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def test_system_english():
    """测试系统英语测试入口"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    
    # 检查用户是否登录
    if session.get('user_id'):
        # 获取用户英语等级
        user_level = LearningSystem.get_user_language_level(session.get('user_id'), 'english')
        
        # 如果用户没有英语等级，重定向到等级评测测试
        if not user_level:
            return redirect(url_for('language_tests.level_assessment'))
    
    return render_template('english_test.html', user=user)

@language_tests_bp.route('/level-assessment')
@check_user_status
@guest_permission_middleware.require_guest_permission()
def level_assessment():
    """等级评估测试页面"""
    # 构建user对象，包含username属性
    user = {
        'username': session.get('username')
    }
    return render_template('level_assessment.html', user=user)
