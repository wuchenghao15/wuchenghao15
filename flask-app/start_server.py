#!/usr/bin/env python3
"""
启动服务器 - 集成所有组件的统一入口
"""

import os
import sys
import logging

# 设置默认的MODEL_PATH环境变量，避免AI模块导入时出现KeyError
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 也设置到DEFAULT_CONFIG中，确保配置系统能获取到
os.environ['DEFAULT_CONFIG_MODEL_PATH'] = './models'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 禁用dotenv加载，避免超时问题
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 打印当前工作目录和Python路径
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python path: {sys.path}")

# 直接导入app.py中的应用实例，使用其中的AI智能路由系统
try:
    logger.info("[系统集成] 尝试导入app.py中的应用实例...")
    from app import app
    logger.info("[系统集成] 成功导入app.py中的应用实例！")
    
    # 直接在start_server.py中添加健康检查路由
    logger.info("[系统集成] 直接添加健康检查路由 /health")
    @app.route('/health')
    def health():
        """健康检查路由"""
        return "OK", 200
    
    # 直接添加测试路由
    logger.info("[系统集成] 直接添加测试路由 /test")
    @app.route('/test')
    def test():
        """测试路由"""
        return "Test OK", 200
    
    # 直接添加AI自动更新管理器状态路由
    logger.info("[系统集成] 直接添加AI自动更新管理器状态路由 /test/auto-update/status")
    @app.route('/test/auto-update/status')
    def test_auto_update_status():
        """直接测试AI自动更新管理器状态的路由"""
        from app.ai.auto_update_manager import ai_auto_update_manager
        status = ai_auto_update_manager.get_status()
        import json
        return json.dumps(status), 200, {'Content-Type': 'application/json'}
    
    # 直接添加测试系统日语测试路由，修复模板链接
    logger.info("[系统集成] 直接添加测试系统日语测试路由 /test-system/japanese")
    @app.route('/test-system/japanese')
    def test_system_japanese():
        """测试系统日语测试入口"""
        from flask import render_template, session, redirect, url_for
        # 检查用户名是否为None，如果是则清除会话并重定向到登录页面
        username = session.get('username')
        if username is None:
            # 清除会话
            session.clear()
            return redirect(url_for('auth.login'))
        
        # 构建user对象，包含username属性
        user = {
            'username': username
        }
        return render_template('japanese_test.html', user=user)
    
    # 直接添加/index.html路由，确保主入口可访问
    logger.info("[系统集成] 直接添加/index.html路由")
    @app.route('/index.html')
    def index_html():
        """主入口index.html路由"""
        from flask import render_template, session
        return render_template('index.html', 
                           user={'username': session.get('username'), 'role': session.get('user_level', 'guest')})
    
    # 直接添加/debug/routes路由，方便调试
    logger.info("[系统集成] 直接添加/debug/routes路由")
    @app.route('/debug/routes')
    def debug_routes():
        """调试路由，查看所有注册的路由"""
        from flask import jsonify
        routes = []
        for rule in app.url_map.iter_rules():
            route = {
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': list(rule.methods)
            }
            routes.append(route)
        return jsonify(routes)
    
    # 直接注册AI自动更新管理器API蓝图
    try:
        logger.info("[系统集成] 直接注册AI自动更新管理器API蓝图")
        from app.api.auto_update_api import auto_update_api_bp
        app.register_blueprint(auto_update_api_bp, url_prefix='/api/auto-update')
        logger.info("[系统集成] AI自动更新管理器API蓝图注册成功")
    except Exception as e:
        logger.error(f"[系统集成] 注册AI自动更新管理器API蓝图失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 直接注册考试测试系统API蓝图
    try:
        logger.info("[系统集成] 直接注册考试测试系统API蓝图")
        from app.api.exam_test_api import exam_test_api
        app.register_blueprint(exam_test_api, url_prefix='/api')
        logger.info("[系统集成] 考试测试系统API蓝图注册成功")
    except Exception as e:
        logger.error(f"[系统集成] 注册考试测试系统API蓝图失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 打印所有注册的路由
    logger.info("[系统集成] 已注册的路由:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  - {rule}")
    
    # 启动AI自动化服务
    logger.info("[系统集成] 启动AI自动化服务...")
    try:
        from app.services.ai_automation_service import ai_automation_service
        ai_automation_service.start()
        logger.info("[系统集成] AI自动化服务启动成功")
    except Exception as e:
        logger.error(f"[系统集成] AI自动化服务启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 启动分布式服务器管理器
    logger.info("[系统集成] 启动分布式服务器管理器...")
    try:
        from app.services.distributed_server import distributed_server_manager
        distributed_server_manager.start()
        logger.info("[系统集成] 分布式服务器管理器启动成功")
    except Exception as e:
        logger.error(f"[系统集成] 分布式服务器管理器启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
except Exception as e:
    logger.error(f"[系统集成] 导入app.py中的应用实例失败: {str(e)}")
    import traceback
    logger.error("完整错误堆栈:")
    traceback.print_exc()
    sys.exit(1)



# 启动服务器
if __name__ == '__main__':
    try:
        # 添加命令行参数支持
        import argparse
        import time
        parser = argparse.ArgumentParser(description='MTSCOS AI Server')
        parser.add_argument('--port', type=int, default=8443, help='Server port')
        parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
        parser.add_argument('--debug', action='store_true', help='Debug mode')
        parser.add_argument('--node-id', type=str, default='root-1', help='Cluster node ID')
        parser.add_argument('--node-role', type=str, default='master', help='Cluster node role')
        args = parser.parse_args()
        
        # 根服务器配置
        host = args.host
        port = args.port
        debug = args.debug
        node_id = args.node_id
        node_role = args.node_role
        
        # 根服务器特殊设置
        if node_role == 'master':
            logger.info("[根服务器配置] 检测到根服务器配置，应用特殊设置...")
            debug = False  # 根服务器建议关闭调试模式
            logger.info("[根服务器配置] 根服务器特殊设置已应用")
        
        # 获取HTTPS设置
        HTTPS_ENABLED = app.config.get('HTTPS_ENABLED', False)
        SSL_CERT_PATH = app.config.get('SSL_CERT_PATH', 'ssl/cert.pem')
        SSL_KEY_PATH = app.config.get('SSL_KEY_PATH', 'ssl/key.pem')
        protocol = 'https' if HTTPS_ENABLED else 'http'
        
        logger.info(f"Starting MTSCOS Root Server...")
        logger.info(f"Server will run on {protocol}://{host}:{port}")
        logger.info(f"Node ID: {node_id}")
        logger.info(f"Node role: {node_role}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"HTTPS enabled: {HTTPS_ENABLED}")
        
        # 直接运行Flask服务器，不依赖复杂配置
        logger.info("[服务器启动] 开始运行Flask服务器...")
        logger.info(f"[服务器启动] 服务器配置: host={host}, port={port}, debug={debug}")
        logger.info(f"[服务器启动] 当前工作目录: {os.getcwd()}")
        logger.info(f"[服务器启动] 服务器将运行在: {protocol}://{host}:{port}")
        
        # 检查端口是否可用
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            logger.info(f"[服务器启动] 端口 {port} 可用")
        except Exception as e:
            logger.error(f"[服务器启动] 端口 {port} 不可用: {e}")
            sys.exit(1)
        
        try:
            logger.info("[服务器启动] 正在启动Flask应用...")
            if HTTPS_ENABLED and os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
                app.run(
                    host=host, 
                    port=port, 
                    debug=debug, 
                    use_reloader=False,
                    ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH)
                )
            else:
                app.run(host=host, port=port, debug=debug, use_reloader=False)
            logger.info("[服务器启动] MTSCOS Root Server started successfully!")
        except Exception as e:
            logger.error(f"[服务器启动] 服务器运行失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

