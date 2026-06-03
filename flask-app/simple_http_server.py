# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最简单的HTTP服务器,用于测试服务器启动

import socketserver
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = 8888

handler = http.server.SimpleHTTPRequestHandler

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
            logger.info(f"Starting simple HTTP server on port {PORT}...")
            logger.info(f"Server will run on http://0.0.0.0:{PORT}")
            httpd.serve_forever()
            logger.info("Simple HTTP server started successfully!")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()

"""