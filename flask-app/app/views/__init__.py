# -*- coding: utf-8 -*-
# Views package
import logging
logger = logging.getLogger(__name__)
import os
import importlib
from flask import Blueprint

# 蓝图注册配置
BLUEPRINT_CONFIG = {
    'main_bp': {'url_prefix': None},  # 主蓝图,无前缀
    'auth_bp': {'url_prefix': '/auth'},
    'ai_bp': {'url_prefix': '/ai'},
    'monitoring_bp': {'url_prefix': '/monitoring'},
    'system_bp': {'url_prefix': '/system'},  # 系统管理蓝图
    'language_tests_bp': {'url_prefix': '/language-tests'},  # 语言测试蓝图
    'smart_dashboard_bp': {'url_prefix': '/smart-dashboard'},  # 智能仪表盘蓝图
    'smart_user_management_bp': {'url_prefix': '/smart-user-management'},  # 智能用户管理蓝图
    'smart_permission_management_bp': {'url_prefix': '/smart-permission-management'},  # 智能权限管理蓝图
    'enhanced_monitoring_bp': {'url_prefix': '/enhanced-monitoring'},  # 增强型系统监控蓝图
    'smart_system_config_bp': {'url_prefix': '/smart-system-config'},  # 智能系统配置蓝图
    'smart_ai_rule_management_bp': {'url_prefix': '/smart-ai-rule-management'},  # 智能AI规则管理蓝图
    'session_management_bp': {'url_prefix': '/session-management'}  # 会话管理蓝图
}


# Register blueprints function
def register_blueprints(app):
    """
    注册所有蓝图,支持自动发现和手动配置

    Args:
        app: Flask应用实例
    print("开始注册蓝图...")

    # 注册主蓝图和认证蓝图,这两个是系统运行的核心蓝图
    try:
        from app.views.main import main_bp
        app.register_blueprint(main_bp, url_prefix=None)
        print(f"✓ 成功注册蓝图: main_bp 到 /")
    except Exception as e:
        print(f"✗ 注册蓝图 main_bp 失败: {str(e)}")

    try:
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print(f"✓ 成功注册蓝图: auth_bp 到 /auth")
    except Exception as e:
        print(f"✗ 注册蓝图 auth_bp 失败: {str(e)}")

    # 注册系统管理蓝图
    try:
        app.register_blueprint(system_bp, url_prefix='/system')
        print(f"✓ 成功注册蓝图: system_bp 到 /system")
    except Exception as e:
        print(f"✗ 注册蓝图 system_bp 失败: {str(e)}")

    # 注册AI管理蓝图
    try:
        app.register_blueprint(ai_bp, url_prefix='/ai')
        print(f"✓ 成功注册蓝图: ai_bp 到 /ai")
    except Exception as e:
        print(f"✗ 注册蓝图 ai_bp 失败: {str(e)}")
        print(f"  警告: AI相关模块可能不存在,将跳过该蓝图注册")

    # 注册监控管理蓝图
    try:
        app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
        print(f"✓ 成功注册蓝图: monitoring_bp 到 /monitoring")
    except Exception as e:
        print(f"✗ 注册蓝图 monitoring_bp 失败: {str(e)}")

    # 注册语言测试蓝图
    try:
        app.register_blueprint(language_tests_bp, url_prefix='/language-tests')
        print(f"✓ 成功注册蓝图: language_tests_bp 到 /language-tests")
    except Exception as e:
        print(f"✗ 注册蓝图 language_tests_bp 失败: {str(e)}")

    # 注册整合设计页面蓝图
    try:
        app.register_blueprint(integrated_design_bp)
        print(f"✓ 成功注册蓝图: integrated_design_bp 到 /integrated-design")
        # 打印路由信息
        print("  路由:")
        for rule in app.url_map.iter_rules():
            if 'integrated-design' in str(rule):
                print(f"    - {rule}")
    except Exception as e:
        print(f"✗ 注册蓝图 integrated_design_bp 失败: {str(e)}")
        import traceback
import sys
        traceback.print_exc()

    # 注册智能仪表盘蓝图
    try:
        app.register_blueprint(smart_dashboard_bp, url_prefix='/smart-dashboard')
        print(f"✓ 成功注册蓝图: smart_dashboard_bp 到 /smart-dashboard")
    except Exception as e:
        print(f"✗ 注册蓝图 smart_dashboard_bp 失败: {str(e)}")
        print(f"  警告: 智能仪表盘依赖的AI模块可能不存在,将跳过该蓝图注册")

    # 注册智能用户管理蓝图
    try:
        app.register_blueprint(smart_user_management_bp, url_prefix='/smart-user-management')
        print(f"✓ 成功注册蓝图: smart_user_management_bp 到 /smart-user-management")
    except Exception as e:
        print(f"✗ 注册蓝图 smart_user_management_bp 失败: {str(e)}")

    # 注册智能权限管理蓝图
    try:
        app.register_blueprint(smart_permission_management_bp, url_prefix='/smart-permission-management')
        print(f"✓ 成功注册蓝图: smart_permission_management_bp 到 /smart-permission-management")
    except Exception as e:
        print(f"✗ 注册蓝图 smart_permission_management_bp 失败: {str(e)}")

    # 注册增强型系统监控蓝图
    try:
        app.register_blueprint(enhanced_monitoring_bp, url_prefix='/enhanced-monitoring')
        print(f"✓ 成功注册蓝图: enhanced_monitoring_bp 到 /enhanced-monitoring")
    except Exception as e:
        print(f"✗ 注册蓝图 enhanced_monitoring_bp 失败: {str(e)}")

    # 注册智能系统配置蓝图
    try:
        app.register_blueprint(smart_system_config_bp, url_prefix='/smart-system-config')
        print(f"✓ 成功注册蓝图: smart_system_config_bp 到 /smart-system-config")
    except Exception as e:
        print(f"✗ 注册蓝图 smart_system_config_bp 失败: {str(e)}")

    # 注册智能AI规则管理蓝图
    try:
        app.register_blueprint(smart_ai_rule_management_bp, url_prefix='/smart-ai-rule-management')
        print(f"✓ 成功注册蓝图: smart_ai_rule_management_bp 到 /smart-ai-rule-management")
    except Exception as e:
        print(f"✗ 注册蓝图 smart_ai_rule_management_bp 失败: {str(e)}")

    # 注册会话管理蓝图
    try:
        app.register_blueprint(session_management_bp, url_prefix='/session-management')
        print(f"✓ 成功注册蓝图: session_management_bp 到 /session-management")
    except Exception as e:
        print(f"✗ 注册蓝图 session_management_bp 失败: {str(e)}")

    print("蓝图注册完成")


def auto_discover_blueprints(app):
    自动发现并注册蓝图

    Args:
        app: Flask应用实例

    for file_name in os.listdir(views_dir):
        if file_name.endswith('.py') and file_name != '__init__.py':
            module_name = file_name[:-3]  # 去掉.py后缀
            full_module_name = f"app.views.{module_name}"

            try:
                # 导入模块
                module = importlib.import_module(full_module_name)

                # 遍历模块中的所有属性,查找Blueprint实例
                    attr = getattr(module, attr_name)
                    if isinstance(attr, Blueprint):
                        # 检查是否已经在手动配置中注册过
                        if attr_name not in BLUEPRINT_CONFIG:
                            # 自动生成url_prefix
                            url_prefix = f"/{module_name}" if module_name != 'main' else None
                            app.register_blueprint(attr, url_prefix=url_prefix)
                            print(f"✓ 自动发现并注册蓝图: {attr_name} 到 {url_prefix or '/'} (自动)")
            except Exception as e:
                print(f"✗ 自动发现蓝图 {module_name} 失败: {str(e)}")


def do_work(**kwargs):
    """