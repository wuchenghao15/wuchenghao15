#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显式启动Flask应用，显示详细日志

import os
import sys
import logging

# 设置基本日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入应用
from app import app

# 从配置中获取端口和HTTPS设置
PORT = app.config.get('SERVER_PORT', 8443)
HTTPS_ENABLED = app.config.get('HTTPS_ENABLED', False)
SSL_CERT_PATH = app.config.get('SSL_CERT_PATH', 'ssl/cert.pem')
SSL_KEY_PATH = app.config.get('SSL_KEY_PATH', 'ssl/key.pem')

# 显式设置Flask的DEBUG模式
app.debug = True

# 显式设置日志级别
logging.getLogger('werkzeug').setLevel(logging.INFO)
logging.getLogger('flask').setLevel(logging.INFO)

if __name__ == '__main__':
    protocol = 'https' if HTTPS_ENABLED else 'http'
    print(f"Starting Flask app on {protocol}://0.0.0.0:{PORT}...")
    print(f"About to call app.run()...")
    try:
        if HTTPS_ENABLED and os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
            app.run(
                host='0.0.0.0',
                port=PORT,
                debug=True,
                ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH)
            )
            app.run(host='0.0.0.0', port=PORT, debug=True)
        print(f"app.run() completed successfully")
    except KeyboardInterrupt:
        print("Flask app stopped by KeyboardInterrupt.")
    except Exception as e:
        print(f"Error starting Flask app: {str(e)}")
        import traceback
        traceback.print_exc()
    print("Start script completed.")



"""