# -*- coding: utf-8 -*-
# MTSCOS AI Project Application - Integrated System
import os
import logging
import traceback
from flask import Flask

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建全局日志记录器
logger = logging.getLogger(__name__)

# 导入基本组件
from app.config import load_config

# 应用工厂函数
def create_app(config_type=None):
    """
    创建并配置Flask应用实例
    只保留最基本的配置和初始化逻辑，确保应用能够成功启动

    Args:
        config_type: 配置类型，可选值：'production', 'development', 'test'

    Returns:
        Flask应用实例
    """
    global logger
    logger.info("[系统集成] 开始创建Flask应用实例...")

    # 创建Flask应用实例
    app = Flask(__name__)

    # 配置模板目录，确保能够正确找到模板文件
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates')
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static')

    # 明确设置编码配置，确保中文显示正常
    app.config['JSON_AS_ASCII'] = False  # 确保JSON响应使用UTF-8编码
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # 确保模板自动重载
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存

    # 1. 加载配置
    logger.info("[系统集成] 加载系统配置...")
    config = load_config(config_type)
    app.config.update(config)
    logger.info(f"[系统集成] 配置加载完成，环境: {config.get('ENV', 'development')}")

    # 2. 配置HTTPS
    if config.get('HTTPS_ENABLED', False):
        ssl_cert_path = config.get('SSL_CERT_PATH', 'ssl/cert.pem')
        ssl_key_path = config.get('SSL_KEY_PATH', 'ssl/key.pem')
        # 检查证书文件是否存在
        if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
            app.config['SSL_CERT_PATH'] = ssl_cert_path
            app.config['SSL_KEY_PATH'] = ssl_key_path
            logger.info("[系统集成] HTTPS 配置完成")
        else:
            logger.warning("[系统集成] HTTPS 证书文件不存在，将使用 HTTP")
            app.config['HTTPS_ENABLED'] = False

    # 导入请求处理相关模块，确保在蓝图注册之前
    from flask import request
    # 导入日志管理器
    from app.utils.logging import logging_manager

    # 获取中文日志记录器
    client_logger = logging_manager.get_logger('客户端交互日志')

    # 添加客户端请求日志中间件
    @app.before_request
    def log_request_info():
        """记录请求信息"""
        client_logger.info(f"[客户端请求] {request.remote_addr} - {request.method} {request.path}")
        client_logger.info(f"[请求头] {dict(request.headers)}")
        if request.method in ['POST', 'PUT', 'PATCH']:
            client_logger.info(f"[请求体] {request.get_data(as_text=True)}")

    # 添加响应日志中间件
    @app.after_request
    def log_response_info(response):
        """记录响应信息"""
        client_logger.info(f"[客户端响应] {request.remote_addr} - {request.method} {request.path} - 状态码: {response.status_code}")
        client_logger.info(f"[响应头] {dict(response.headers)}")
        return response

    # 注册统一错误处理器
    try:
        from app.utils.error_handler import register_error_handlers
        register_error_handlers(app)
        logger.info("[系统集成] 统一错误处理器注册完成")
    except Exception as e:
        logger.error(f"[系统集成] 注册统一错误处理器失败: {str(e)}")

    # 初始化并注册所有路由
    try:
        from app.routes import init_routes, route_manager
        init_routes()
        route_manager.register_all_routes(app)
        logger.info("[系统集成] 路由管理器初始化完成")
    except Exception as e:
        logger.error(f"[系统集成] 初始化路由管理器失败: {str(e)}")

    # 注册API蓝图和中间件
    try:
        from app.api import api_bp
        from app.api.middleware import APIMiddleware

        # 注册API蓝图
        app.register_blueprint(api_bp)
        logger.info("[系统集成] API蓝图注册完成")

        # 初始化API中间件
        APIMiddleware(app)
        logger.info("[系统集成] API中间件初始化完成")
    except Exception as e:
        logger.error(f"[系统集成] 注册API蓝图和中间件失败: {str(e)}")

    logger.info("[系统集成] Flask应用实例创建完成！")
    return app

# 创建默认应用实例
app = create_app()

# 初始化碎片化临时缓存系统
try:
    from app.utils.cache import get_cache_manager
    app.cache_manager = get_cache_manager()
    logger.info("碎片化临时缓存系统启动成功")
except Exception as e:
    logger.error(f"初始化碎片化临时缓存系统失败: {str(e)}")
    traceback.print_exc()

# 初始化智体管家
try:
    from app.ai.intelligence_manager import intelligence_manager
    intelligence_manager.start()
    logger.info("智体管家启动成功")
except Exception as e:
    logger.error(f"初始化智体管家失败: {str(e)}")
    traceback.print_exc()

# 初始化AI线程进程管理器
try:
    from app.ai.thread_process_manager import ai_thread_process_manager
    ai_thread_process_manager.start()
    logger.info("AI线程进程管理器启动成功")
except Exception as e:
    logger.error(f"初始化AI线程进程管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化AI引擎配置，加载API key
try:
    from app.ai.engine_integrator import ai_engine_integrator

    # 配置minimax API key
    minimax_api_key = os.environ.get('MINIMAX_API_KEY')
    if minimax_api_key:
        ai_engine_integrator.configure_engine('minimax', {'api_key': minimax_api_key})
        logger.info("minimax API key配置成功")

    # 配置gemini API key（如果存在）
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if gemini_api_key:
        ai_engine_integrator.configure_engine('gemini', {'api_key': gemini_api_key})
        logger.info("Gemini API key配置成功")

    logger.info("AI引擎API key配置完成")
except Exception as e:
    logger.error(f"初始化AI引擎配置失败: {str(e)}")
    traceback.print_exc()

# 初始化网管AI
try:
    from app.ai.network_admin_ai import init_network_admin_ai, network_admin_instance
    network_admin_instance = init_network_admin_ai()
    if network_admin_instance:
        logger.info("网管AI初始化成功")
    else:
        logger.error("网管AI初始化失败")
except Exception as e:
    logger.error(f"初始化网管AI失败: {str(e)}")
    traceback.print_exc()

# 初始化教师AI
try:
    from app.ai.teacher_ai import init_teacher_ai
    teacher_instance = init_teacher_ai()
    if teacher_instance:
        logger.info("教师AI初始化成功")
    else:
        logger.error("教师AI初始化失败")
except Exception as e:
    logger.error(f"初始化教师AI失败: {str(e)}")
    traceback.print_exc()

# 初始化考试测试专家AI
try:
    from app.ai.exam_expert_ai import init_exam_expert_ai
    exam_expert_instance = init_exam_expert_ai()
    if exam_expert_instance:
        logger.info("考试测试专家AI初始化成功")
    else:
        logger.error("考试测试专家AI初始化失败")
except Exception as e:
    logger.error(f"初始化考试测试专家AI失败: {str(e)}")
    traceback.print_exc()

# 初始化工程师AI
try:
    from app.ai.engineer_ai import register_engineer_ai
    register_engineer_ai()
    logger.info("工程师AI初始化成功")
except Exception as e:
    logger.error(f"初始化工程师AI失败: {str(e)}")
    traceback.print_exc()

# 初始化后台服务管理器
try:
    from app.services.service_manager import service_manager
    service_manager.start()
    logger.info("后台服务管理器启动成功")

    service_manager.start_all_services()
except Exception as e:
    logger.error(f"初始化后台服务管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化分布式服务器管理器
try:
    from app.services.distributed_server import distributed_server_manager
    distributed_server_manager.start()
    logger.info("分布式服务器管理器启动成功")
except Exception as e:
    logger.error(f"初始化分布式服务器管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化子服务器系统AI
try:
    from app.ai.server_ai import server_ai
    server_ai.initialize()
    logger.info("子服务器系统AI初始化成功")
except Exception as e:
    logger.error(f"初始化子服务器系统AI失败: {str(e)}")
    traceback.print_exc()

# 初始化子服务器规则管理器
try:
    from app.utils.server_rule_manager import server_rule_manager
    server_rule_manager.initialize()
    logger.info("子服务器规则管理器初始化成功")
except Exception as e:
    logger.error(f"初始化子服务器规则管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化子服务器权限管理器
try:
    from app.utils.server_permission_manager import server_permission_manager
    server_permission_manager.initialize()
    logger.info("子服务器权限管理器初始化成功")
except Exception as e:
    logger.error(f"初始化子服务器权限管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化子服务器路由管理器
try:
    from app.utils.server_route_manager import server_route_manager
    server_route_manager.initialize()
    logger.info("子服务器路由管理器初始化成功")
except Exception as e:
    logger.error(f"初始化子服务器路由管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化Git管理器
try:
    from app.services.git_manager import git_manager
    git_manager.initialize()
    logger.info("Git管理器初始化成功")
except Exception as e:
    logger.error(f"初始化Git管理器失败: {str(e)}")
    traceback.print_exc()

# 注册SQL注入防护中间件
try:
    from app.middlewares.sql_injection_protection import sql_injection_protection
    sql_injection_protection.protect(app)
    logger.info("SQL注入防护中间件注册成功")
except Exception as e:
    logger.error(f"注册SQL注入防护中间件失败: {str(e)}")
    traceback.print_exc()

# 初始化AI托管管理器
try:
    from app.ai.ai_hosting import ai_hosting_manager
    ai_hosting_manager.initialize()
    logger.info("AI托管管理器初始化成功")
except Exception as e:
    logger.error(f"初始化AI托管管理器失败: {str(e)}")
    traceback.print_exc()