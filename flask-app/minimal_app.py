# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Minimal MTSCOS AI Project Application for testing port 8888 accessibility

import logging
logger = logging.getLogger(__name__)
import os
from flask import Flask

# Disable dotenv loading to avoid timeout issues
os.environ['FLASK_SKIP_DOTENV'] = '1'
os.environ['FLASK_APP'] = __file__
os.environ['FLASK_ENV'] = 'development'

# Create a minimal Flask app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'temp-secret-key-for-development'

# Define simple routes
@app.route('/')
def index():
    return "MTSCOS AI Project - Running on port 8888", 200

@app.route('/health')
def health():
    return "OK", 200

@app.route('/version')
def version():
    return {"version": "3.0.0"}, 200

if __name__ == '__main__':
    try:
        print("[INFO] 启动极简MTSCOS AI应用...")

        # 直接启动Flask服务器,不初始化任何其他组件
        port = 8888
        print(f"[INFO] 监听地址: 0.0.0.0:{port}")
        print(f"[INFO] 访问地址: http://localhost:{port}")

        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("[INFO] 收到中断信号,正在关闭应用...")
    except Exception as e:
        print(f"[ERROR] 应用启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("[INFO] 应用关闭,清理资源...")
        print("[INFO] 极简MTSCOS AI应用已关闭")

"""