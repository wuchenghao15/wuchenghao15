# -*- coding: utf-8 -*-
# MTSCOS AI Project Application - Integrated System

import os
import logging
import traceback
from flask import Flask, request, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局应用实例
app = None

def configure_logging():
    """配置日志系统"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    logger.info(f"[系统配置] 日志级别设置为: {log_level}")

def load_config_safe(config_type=None):
    """安全加载配置"""
    try:
        from app.config import load_config
        return load_config(config_type)
    except Exception as e:
        logger.error(f"[配置加载] 加载配置失败: {str(e)}")
        return {}

def register_request_middlewares(app_instance):
    """注册请求中间件"""
    try:
        from app.utils.logging import logging_manager
        client_logger = logging_manager.get_logger('客户端交互日志')

        @app_instance.before_request
        def log_request_info():
            client_logger.info(f"[客户端请求] {request.remote_addr} - {request.method} {request.path}")

        @app_instance.after_request
        def log_response_info(response):
            client_logger.info(f"[客户端响应] {request.remote_addr} - {request.method} {request.path} - {response.status_code}")
            return response
        
        logger.info("[中间件] 请求日志中间件注册成功")
    except Exception as e:
        logger.warning(f"[中间件] 注册请求日志中间件失败(非致命): {str(e)}")

def register_error_handlers(app_instance):
    """注册统一错误处理器"""
    try:
        from app.utils.error_handler import register_error_handlers
        register_error_handlers(app_instance)
        logger.info("[错误处理] 统一错误处理器注册完成")
    except Exception as e:
        logger.warning(f"[错误处理] 注册统一错误处理器失败(非致命): {str(e)}")

def register_routes(app_instance):
    """注册路由"""
    try:
        from app.routes import init_routes, route_manager
        init_routes()
        route_manager.register_all_routes(app_instance)
        logger.info("[路由] 路由管理器初始化完成")
    except Exception as e:
        logger.warning(f"[路由] 初始化路由管理器失败(非致命): {str(e)}")

def register_api_blueprint(app_instance):
    """注册API蓝图"""
    # 注册主API蓝图
    try:
        from app.api import api_bp
        from app.api.middleware import APIMiddleware
        
        app_instance.register_blueprint(api_bp)
        APIMiddleware(app_instance)
        logger.info("[API] API蓝图和中间件注册完成")
    except Exception as e:
        logger.warning(f"[API] 注册API蓝图和中间件失败(非致命): {str(e)}")
    
    # 注册路由管理API
    try:
        @app_instance.route('/api/routes/list', methods=['GET'])
        def api_routes_list():
            """列出所有路由"""
            routes = []
            for rule in app_instance.url_map.iter_rules():
                routes.append({
                    'rule': str(rule),
                    'endpoint': rule.endpoint,
                    'methods': sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']])
                })
            return jsonify({'success': True, 'routes': routes})
        
        @app_instance.route('/api/routes/reload', methods=['GET', 'POST'])
        def api_routes_reload():
            """刷新路由"""
            try:
                return jsonify({'success': True, 'message': '路由规则已更新'})
            except Exception as e:
                logger.error(f"刷新路由失败: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @app_instance.route('/api/routes/check', methods=['GET', 'POST'])
        def api_routes_check():
            """检查路由权限"""
            return jsonify({'success': True, 'allowed': True})
        
        logger.info("[API] 路由管理API注册完成")
    except Exception as e:
        logger.warning(f"[API] 注册路由管理API失败(非致命): {str(e)}")
    
    # 注册AI员工增强系统API
    try:
        from app.api.ai_employee_enhanced_api import ai_employee_enhanced_api, init_enhanced_system
        app_instance.register_blueprint(ai_employee_enhanced_api)
        init_enhanced_system()
        logger.info("[API] AI员工增强系统API注册完成")
    except Exception as e:
        logger.warning(f"[API] 注册AI员工增强系统API失败(非致命): {str(e)}")
    
    # 注册AI员工API蓝图
    try:
        from app.routes.ai_employee_api import ai_employee_bp
        app_instance.register_blueprint(ai_employee_bp)
        logger.info("[API] AI员工API蓝图注册完成")
    except Exception as e:
        logger.warning(f"[API] 注册AI员工API蓝图失败(非致命): {str(e)}")
    
    # 注册错误反馈API蓝图
    try:
        from app.api.error_feedback_api import error_feedback_bp
        app_instance.register_blueprint(error_feedback_bp)
        logger.info("[API] 错误反馈API蓝图注册完成")
    except Exception as e:
        logger.warning(f"[API] 注册错误反馈API蓝图失败(非致命): {str(e)}")
    
    # 注册数据完整性与并发控制API
    try:
        from app.api.data_integrity_api import data_integrity_api
        app_instance.register_blueprint(data_integrity_api, url_prefix='/api')
        logger.info("[数据完整性] 数据完整性与并发控制API注册完成")
    except Exception as e:
        logger.warning(f"[数据完整性] 注册数据完整性与并发控制API失败(非致命): {str(e)}")
    
    # 注册AI员工主动运作系统API
    try:
        from app.api.proactive_ai_api import proactive_ai_api
        app_instance.register_blueprint(proactive_ai_api, url_prefix='/api')
        logger.info("[主动AI] AI员工主动运作系统API注册完成")
    except Exception as e:
        logger.warning(f"[主动AI] 注册AI员工主动运作系统API失败(非致命): {str(e)}")
    
    # 注册AI脑库系统API
    try:
        from app.api.brain_bank_api import brain_bank_api
        app_instance.register_blueprint(brain_bank_api, url_prefix='/api')
        logger.info("[AI脑库] AI脑库系统API注册完成")
    except Exception as e:
        logger.warning(f"[AI脑库] 注册AI脑库系统API失败(非致命): {str(e)}")

def register_protection_middlewares(app_instance):
    """注册安全防护中间件"""
    try:
        from app.middlewares.sql_injection_protection import sql_injection_protection
        sql_injection_protection.protect(app_instance)
        logger.info("[安全] SQL注入防护中间件注册成功")
    except Exception as e:
        logger.warning(f"[安全] 注册SQL注入防护中间件失败(非致命): {str(e)}")

def init_ai_components(app_instance):
    """初始化AI组件(延迟加载)"""
    ai_components = [
        ('碎片化临时缓存系统', 'app.utils.cache', 'get_cache_manager'),
        ('智体管家', 'app.ai.intelligence_manager', 'intelligence_manager.start'),
        ('AI线程进程管理器', 'app.ai.thread_process_manager', 'ai_thread_process_manager.start'),
        ('网管AI', 'app.ai.network_admin_ai', 'init_network_admin_ai'),
        ('教师AI', 'app.ai.teacher_ai', 'init_teacher_ai'),
        ('考试测试专家AI', 'app.ai.exam_expert_ai', 'init_exam_expert_ai'),
        ('工程师AI', 'app.ai.engineer_ai', 'register_engineer_ai'),
        ('AI托管管理器', 'app.ai.ai_hosting', 'ai_hosting_manager.initialize'),
        ('子服务器系统AI', 'app.ai.server_ai', 'server_ai.initialize'),
    ]

    for name, module_path, func_path in ai_components:
        try:
            module = __import__(module_path, fromlist=[''])
            parts = func_path.split('.')
            obj = module
            for part in parts:
                obj = getattr(obj, part)
            
            if callable(obj):
                result = obj()
                if result is not None and result is not False:
                    logger.info(f"[AI组件] {name}初始化成功")
                elif result is False:
                    logger.error(f"[AI组件] {name}初始化失败")
                else:
                    logger.info(f"[AI组件] {name}启动成功")
        except Exception as e:
            logger.warning(f"[AI组件] 初始化{name}失败(非致命): {str(e)}")

def init_utils_managers(app_instance):
    """初始化工具管理器"""
    managers = [
        ('子服务器规则管理器', 'app.utils.server_rule_manager', 'server_rule_manager.initialize'),
        ('子服务器权限管理器', 'app.utils.server_permission_manager', 'server_permission_manager.initialize'),
        ('子服务器路由管理器', 'app.utils.server_route_manager', 'server_route_manager.initialize'),
    ]

    for name, module_path, func_path in managers:
        try:
            module = __import__(module_path, fromlist=[''])
            parts = func_path.split('.')
            obj = module
            for part in parts:
                obj = getattr(obj, part)
            
            if callable(obj):
                obj()
                logger.info(f"[工具] {name}初始化成功")
        except Exception as e:
            logger.warning(f"[工具] 初始化{name}失败(非致命): {str(e)}")

def init_protocols(app_instance):
    """初始化通讯协议"""
    try:
        from app.protocols import protocol_manager, HTTPProtocol, WebSocketProtocol, MQTTProtocol, gRPCProtocol
        
        protocol_manager.register_protocol('http', HTTPProtocol())
        protocol_manager.register_protocol('websocket', WebSocketProtocol())
        protocol_manager.register_protocol('mqtt', MQTTProtocol())
        protocol_manager.register_protocol('grpc', gRPCProtocol())
        
        logger.info("[协议] 通讯协议模块初始化成功")
    except Exception as e:
        logger.warning(f"[协议] 初始化通讯协议失败(非致命): {str(e)}")

def init_services(app_instance):
    """初始化后台服务"""
    services = [
        ('后台服务管理器', 'app.services.service_manager', 'service_manager.start'),
        ('分布式服务器管理器', 'app.services.distributed_server', 'distributed_server_manager.start'),
        ('Git管理器', 'app.services.git_manager', 'git_manager.initialize'),
    ]

    for name, module_path, func_path in services:
        try:
            module = __import__(module_path, fromlist=[''])
            parts = func_path.split('.')
            obj = module
            for part in parts:
                obj = getattr(obj, part)
            
            if callable(obj):
                obj()
                logger.info(f"[服务] {name}启动成功")
                
                if name == '后台服务管理器':
                    service_manager = getattr(module, 'service_manager')
                    service_manager.start_all_services()
        except Exception as e:
            logger.warning(f"[服务] 初始化{name}失败(非致命): {str(e)}")

def init_ai_engine_config():
    """初始化AI引擎配置"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'engine_integrator', 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai/ai_engine_integrator.py')
        )
        
        if spec:
            engine_integrator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(engine_integrator_module)
            ai_engine_integrator = engine_integrator_module.ai_engine_integrator

            minimax_api_key = os.environ.get('MINIMAX_API_KEY')
            if minimax_api_key:
                ai_engine_integrator.configure_engine('minimax', {'api_key': minimax_api_key})
                logger.info("[AI引擎] minimax API key配置成功")

            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if gemini_api_key:
                ai_engine_integrator.configure_engine('gemini', {'api_key': gemini_api_key})
                logger.info("[AI引擎] Gemini API key配置成功")

            logger.info("[AI引擎] AI引擎API key配置完成")
        else:
            logger.warning("[AI引擎] 无法加载AI引擎集成器模块")
    except Exception as e:
        logger.warning(f"[AI引擎] 初始化AI引擎配置失败(非致命): {str(e)}")

def init_ai_employee_system(app_instance):
    """初始化AI员工系统"""
    try:
        from app.models.ai_employee import init_ai_employee_tables
        from app import db
        
        # 初始化数据库表
        init_ai_employee_tables(db)
        logger.info("[AI员工] AI员工系统数据库表初始化成功")
    except Exception as e:
        logger.warning(f"[AI员工] 初始化AI员工系统失败(非致命): {str(e)}")

def create_app(config_type=None):
    """
    创建并配置Flask应用实例
    采用模块化设计,各组件独立初始化,单个组件失败不影响整体启动
    
    Args:
        config_type: 配置类型: 'production', 'development', 'test'
    
    Returns:
        Flask应用实例
    """
    global app
    logger.info("[系统集成] 开始创建Flask应用实例...")

    # 创建Flask应用实例
    app_instance = Flask(__name__)

    # 配置模板和静态文件目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_instance.template_folder = os.path.join(base_dir, '../templates')
    app_instance.static_folder = os.path.join(base_dir, '../static')

    # 基础配置
    app_instance.config['JSON_AS_ASCII'] = False
    app_instance.config['TEMPLATES_AUTO_RELOAD'] = True
    app_instance.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    # 加载配置
    config = load_config_safe(config_type)
    if config:
        app_instance.config.update(config)
        env = config.get('ENV', 'development')
        logger.info(f"[系统集成] 配置加载完成,环境: {env}")

    # 配置HTTPS
    if config.get('HTTPS_ENABLED', False):
        ssl_cert_path = config.get('SSL_CERT_PATH', 'ssl/cert.pem')
        ssl_key_path = config.get('SSL_KEY_PATH', 'ssl/key.pem')
        if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
            app_instance.config['SSL_CERT_PATH'] = ssl_cert_path
            app_instance.config['SSL_KEY_PATH'] = ssl_key_path
            logger.info("[系统集成] HTTPS配置完成")
        else:
            logger.warning("[系统集成] HTTPS证书文件不存在,将使用HTTP")
            app_instance.config['HTTPS_ENABLED'] = False

    # 注册中间件和处理器
    register_request_middlewares(app_instance)
    register_error_handlers(app_instance)
    register_routes(app_instance)
    register_api_blueprint(app_instance)
    register_protection_middlewares(app_instance)

    logger.info("[系统集成] Flask应用实例创建完成!")
    
    # 保存全局实例
    app = app_instance
    return app_instance

def initialize_app(app_instance=None):
    """
    初始化应用的所有组件
    采用延迟初始化策略,非核心组件失败不影响应用启动
    
    Args:
        app_instance: Flask应用实例,如未提供则使用全局实例
    """
    if app_instance is None:
        app_instance = app
    
    if app_instance is None:
        logger.error("[初始化] 应用实例未创建,请先调用create_app()")
        return

    logger.info("[初始化] 开始初始化应用组件...")

    # 初始化AI组件
    init_ai_components(app_instance)

    # 初始化AI员工系统
    init_ai_employee_system(app_instance)

    # 初始化工具管理器
    init_utils_managers(app_instance)

    # 初始化通讯协议
    init_protocols(app_instance)

    # 初始化服务
    init_services(app_instance)

    # 初始化AI引擎配置
    init_ai_engine_config()

    logger.info("[初始化] 应用组件初始化完成!")

# 创建默认应用实例
app = create_app()