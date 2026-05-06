#!/usr/bin/env python3
"""
调试应用初始化过程的脚本

import sys
import os
import logging

# 配置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DEBUG_INIT")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info("开始调试应用初始化过程...")

try:
    # 测试1: 导入基本模块
    logger.info("测试1: 导入基本模块")
    from flask import Flask
    logger.info("✓ 成功导入Flask")

    # 测试2: 逐步初始化应用
    logger.info("\n测试2: 逐步初始化应用")

    # 加载配置
    logger.info("  - 加载配置")
    from app.config import load_config
    config = load_config()
    logger.info(f"  ✓ 配置加载完成，环境: {config.get('ENV', 'development')}")

    # 初始化路由管理器
    logger.info("\n测试3: 初始化路由管理器")
    from app.routes import init_routes, route_manager
    init_routes()
    logger.info(f"  ✓ 路由初始化完成，视图路由数量: {len(route_manager.view_routes)}")

    # 创建Flask应用实例
    logger.info("\n测试4: 创建Flask应用实例")
    app = Flask(__name__)
    app.config.update(config)
    logger.info("  ✓ Flask应用实例创建完成")

    # 注册路由
    logger.info("\n测试5: 注册路由到应用")
    route_manager.register_all_routes(app)
    route_manager.print_routes()
    logger.info("  ✓ 路由注册完成")

    # 测试6: 检查健康检查路由
    logger.info("\n测试6: 检查健康检查路由")
    health_route = next((r for r in list(app.url_map.iter_rules()) if r.rule == '/health'), None)
    if health_route:
        logger.info("  ✓ 健康检查路由已注册")
    else:
        logger.warning("  ✗ 健康检查路由未注册")

    # 测试7: 检查测试系统路由
    logger.info("\n测试7: 检查测试系统路由")
    test_system_route = next((r for r in list(app.url_map.iter_rules()) if '/test-system' in r.rule), None)
    if test_system_route:
        logger.info("  ✓ 测试系统路由已注册")
    else:

    logger.info("\n✓ 应用初始化调试完成，未发现致命错误")
    logger.info("\n应用已准备好启动，您可以运行 'python3 start_server.py' 来启动服务器")

except Exception as e:
    logger.error(f"✗ 应用初始化调试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

"""