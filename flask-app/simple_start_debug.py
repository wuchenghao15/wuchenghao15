#!/usr/bin/env python3
"""
简化的调试启动脚本，用于诊断服务器启动问题
"""

import sys
import os
import logging

# 设置详细日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并启动Flask应用
try:
    logger.info("正在导入Flask应用...")
    from app import app
    logger.info("成功导入Flask应用")
    
    # 打印应用的URL规则
    logger.info("应用URL规则:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule}")
    
    # 启动应用
    logger.info("正在启动Flask应用...")
    logger.info("访问地址: http://localhost:8888")
    app.run(host='0.0.0.0', port=8888, debug=True)
    
except Exception as e:
    logger.error(f"应用启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
