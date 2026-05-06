#!/usr/bin/env python3
"""
MTSCOS 源服务器
使用完整的应用配置，包括所有路由和集群功能

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置默认的MODEL_PATH环境变量
if 'MODEL_PATH' not in os.environ:
    os.environ['MODEL_PATH'] = './models'

# 禁用dotenv加载
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载完整的应用实例
logger.info("[源服务器] 加载完整的应用实例...")
try:
    from app import app
    logger.info("[源服务器] 应用实例加载成功！")
except Exception as e:
    logger.error(f"[源服务器] 加载应用实例失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    # 源服务器配置
    app.run(host='0.0.0.0', port=8889, debug=False, use_reloader=False)

"""