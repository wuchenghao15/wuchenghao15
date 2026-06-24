#!/usr/bin/env python3
"""
HTTP辅助服务 - 提供HTTP 8888端口访问
"""

import os
import sys
import threading
import time
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("[INFO] HTTP辅助服务启动成功")
except Exception as e:
    print(f"[ERROR] 加载应用失败: {e}")
    sys.exit(1)


class HTTPServerThread(threading.Thread):
    def __init__(self, app, host='0.0.0.0', port=8888):
        threading.Thread.__init__(self)
        self.server = make_server(host, port, app, threaded=True)
        self.daemon = True

    def run(self):
        print(f"[INFO] HTTP服务器运行在 http://0.0.0.0:8888")
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


if __name__ == '__main__':
    server = HTTPServerThread(app)
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 关闭HTTP服务")
        server.stop()
