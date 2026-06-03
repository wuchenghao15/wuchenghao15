# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
带详细日志的启动脚本

import os
import sys
import logging
import traceback

# 配置基础日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('startup.log')
    ]
)

logger = logging.getLogger('MTSCOS_Start')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info("开始启动MTSCOS AI项目...")
logger.info(f"Python版本: {sys.version}")
logger.info(f"当前目录: {os.getcwd()}")

# 尝试导入和启动应用
try:
    # 导入应用
    logger.info("正在导入Flask应用...")
    from app import app

    # 获取应用配置
    logger.info(f"应用配置: DEBUG={app.config.get('DEBUG')}")

    # 启动服务器
    logger.info("正在启动Flask服务器...")
    app.run(host='0.0.0.0', port=8888, debug=True, load_dotenv=False)

except Exception as e:
    logger.error(f"启动失败: {str(e)}")
    logger.error("完整堆栈跟踪:")
    traceback.print_exc()
    logger.error("应用启动失败,详细日志已写入startup.log")
    sys.exit(1)

"""