#!/usr/bin/env python3
"""
MTSCOS AI Project Main Application
"""

import os
import sys
import logging
import traceback
from flask import jsonify

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置默认的MODEL_PATH环境变量，避免AI模块导入时出现KeyError
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用app/__init__.py中创建的Flask应用实例
from app import app as flask_app

# 直接测试 AI 自动更新管理器状态的路由
@flask_app.route('/test/auto-update/status')
def test_auto_update_status():
    """直接测试 AI 自动更新管理器状态的路由"""
    from app.ai.auto_update_manager import ai_auto_update_manager
    status = ai_auto_update_manager.get_status()
    return jsonify(status), 200

# 调试路由：查看所有注册的路由
@flask_app.route('/debug/routes')
def debug_routes():
    """调试路由，查看所有注册的路由"""
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        route = {
            'rule': str(rule),
            'endpoint': rule.endpoint,
            'methods': list(rule.methods)
        }
        routes.append(route)
    return jsonify(routes)

# 预加载动画测试页面路由
@flask_app.route('/test/preloader')
def test_preloader():
    """预加载动画测试页面"""
    from flask import render_template
    return render_template('preloader_test.html')

# 蓝图路由现在通过路由管理器统一注册，不再直接注册
logger.info("蓝图路由将通过路由管理器统一注册")

# 打印当前文件执行情况
logger.info("app.py 文件被导入，开始执行路由注册代码...")

# 健康检查路由已在上方定义，无需重复注册

# 测试路由已在上方定义，无需重复注册

# AI自动更新管理器API蓝图已通过路由管理器注册，无需重复注册
logger.info("AI自动更新管理器API蓝图已通过路由管理器注册")

# 打印所有注册的路由，用于调试
logger.info("已注册的路由:")
for rule in flask_app.url_map.iter_rules():
    logger.info(f"  - {rule}")

# 初始化AI线程进程管理器
try:
    from app.ai.thread_process_manager import ai_thread_process_manager
    ai_thread_process_manager.start()
    logger.info("AI线程进程管理器启动成功")
except Exception as e:
    logger.error(f"初始化AI线程进程管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化AI自动更新管理器
try:
    from app.ai.auto_update_manager import ai_auto_update_manager
    ai_auto_update_manager.start()
    logger.info("AI自动更新管理器启动成功")
except Exception as e:
    logger.error(f"初始化AI自动更新管理器失败: {str(e)}")
    traceback.print_exc()

# 初始化系统监控
try:
    from app.utils.system_monitor import system_monitor
    system_monitor.start()
    logger.info("系统监控已启动")
except Exception as e:
    logger.error(f"初始化系统监控失败: {str(e)}")
    traceback.print_exc()

# 初始化防火墙系统
try:
    from app.services.firewall_system import firewall_system
    firewall_system.initialize()
    logger.info("防火墙系统初始化成功")
except Exception as e:
    logger.error(f"初始化防火墙系统失败: {str(e)}")
    traceback.print_exc()

# 初始化防火墙AI
try:
    logger.info("开始初始化防火墙AI...")
    from app.ai.firewall_ai import firewall_ai
    logger.info("成功导入防火墙AI模块")
    firewall_ai.initialize()
    logger.info("防火墙AI初始化成功")
except ImportError as e:
    logger.error(f"导入防火墙AI模块失败: {str(e)}")
    traceback.print_exc()
except Exception as e:
    logger.error(f"初始化防火墙AI失败: {str(e)}")
    traceback.print_exc()

# 初始化题库拓展系统
try:
    logger.info("开始初始化题库拓展系统...")
    from app.ai.question_bank_expander import question_bank_expander
    logger.info("成功导入题库拓展系统模块")
    question_bank_expander.initialize()
    logger.info("题库拓展系统初始化成功")
except ImportError as e:
    logger.error(f"导入题库拓展系统模块失败: {str(e)}")
    traceback.print_exc()
except Exception as e:
    logger.error(f"初始化题库拓展系统失败: {str(e)}")
    traceback.print_exc()

# 注册全局错误处理器
try:
    from app.utils.error_handler import register_error_handlers
    register_error_handlers(flask_app)
    logger.info("全局错误处理器已注册")
except Exception as e:
    logger.error(f"注册全局错误处理器失败: {str(e)}")
    traceback.print_exc()

import argparse

# 启动服务器
if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='MTSCOS AI Application')
    parser.add_argument('--port', type=int, default=8888, help='端口号')
    args = parser.parse_args()
    
    print(f"[INFO] 启动MTSCOS AI应用...")
    print(f"[INFO] 服务器运行在 http://0.0.0.0:{args.port}")
    flask_app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)



