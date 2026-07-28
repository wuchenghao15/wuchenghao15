# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MTSCOS AI Project Main Application

import logging
logger = logging.getLogger(__name__)
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入Flask应用实例,跳过配置验证
from app import app
from app.utils.logging import logger

# 简化启动:只注册必要的中间件
from app.middlewares.security_headers import security_headers_middleware
security_headers_middleware(app)

logger.info("简化启动模式:跳过AI初始化和数据库表创建")

if __name__ == '__main__':
    # 直接使用硬编码端口,避免配置验证问题
    port = 8888
    print(f"[DEBUG] MTSCOS AI Project 启动中... 端口: {port}")
    logger.info(f"MTSCOS AI Project 启动中... 端口: {port}")
    try:
        print(f"[DEBUG] 即将启动Flask应用,监听地址: 0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except KeyboardInterrupt:
        print("[DEBUG] MTSCOS AI Project 已停止")
        logger.info("MTSCOS AI Project 已停止")
    except Exception as e:
        print(f"[DEBUG] 应用运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"应用运行出错: {str(e)}")
        logger.error("应用运行错误")

"""