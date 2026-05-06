#!/usr/bin/env python3
"""
测试应用启动脚本

import sys
import os
import logging
import traceback

# 配置日志
try:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('test_startup')
    logger.info("开始测试应用启动")
except Exception as e:
    print(f"配置日志失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# 添加项目根目录到Python路径
try:
    logger.info(f"添加到Python路径: {os.path.dirname(os.path.abspath(__file__))}")
except Exception as e:
    logger.error(f"添加Python路径失败: {str(e)}")
    sys.exit(1)

# 尝试导入app模块
try:
    from app import app
    logger.info("成功导入app模块")
except Exception as e:
    logger.error(f"导入app模块失败: {str(e)}")
    traceback.print_exc()

# 尝试运行应用
try:
    app.run(host='0.0.0.0', port=8080, debug=True, load_dotenv=False, use_reloader=False)
    logger.info("应用运行成功")
except KeyboardInterrupt:
    logger.info("收到键盘中断，停止应用")
except Exception as e:
    logger.error(f"应用运行失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
    logger.info("应用退出")

"""