#!/usr/bin/env python3
"""
简单启动服务器，只运行基本的Flask应用，不依赖AI组件

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("=== 启动简单Flask服务器 ===")

# 创建一个简单的Flask应用
from flask import Flask, jsonify

app = Flask(__name__)

# 添加健康检查路由
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'port': 8888
    }), 200

# 添加根路由
@app.route('/')
def root():
    return jsonify({
        'message': 'Welcome to MTSCOS AI Server',
        'features': ['auto-login', 'ai-route-optimization', 'fragmented-cache']
    }), 200

# 启动服务器
    host = '0.0.0.0'
    port = 8888
    debug = False

    logger.info(f"Starting simple Flask server on http://{host}:{port}")
    logger.info(f"Debug mode: {debug}")

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
        logger.info("Server started successfully!")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""