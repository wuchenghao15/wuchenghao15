#!/usr/bin/env python3
# MTSCOS AI Project - 自定义HTTP服务器（带404页面处理）

import http.server
import socketserver
import os
import sys

# 设置项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_DIR = os.path.join(BASE_DIR, 'HTML')

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    # 自定义404错误处理
    def do_GET(self):
        try:
            # 尝试正常处理请求
            super().do_GET()
        except Exception as e:
            # 如果出错，返回404页面
            self.send_error(404, "Page not found")
    
    def send_error(self, code, message=None):
        if code == 404:
            # 发送自定义404页面
            self.send_response(code)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            # 读取并发送404.html文件
            try:
                with open(os.path.join(HTML_DIR, '404.html'), 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                # 如果404.html不存在，发送简单的404响应
                simple_404 = f"""<html>
                <head><title>404 - 页面未找到</title></head>
                <body>
                    <h1>404 - 页面未找到</h1>
                    <p>您请求的页面不存在。</p>
                    <p><a href="/">返回首页</a></p>
                </body>
                </html>""".encode()
                self.wfile.write(simple_404)
        else:
            # 对于其他错误，使用默认处理
            super().send_error(code, message)
    
    def translate_path(self, path):
        # 确保路径是相对于HTML目录的
        path = super().translate_path(path)
        
        # 如果请求的是根目录，提供index.html
        if path.endswith(os.sep):
            path = os.path.join(path, 'index.html')
        
        return path

def run_server(port=8000):
    # 更改工作目录到HTML目录
    os.chdir(HTML_DIR)
    
    # 创建服务器
    handler = CustomHTTPRequestHandler
    with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
        print(f"服务器启动在 http://localhost:{port}")
        print(f"404页面已绑定: {os.path.join(HTML_DIR, '404.html')}")
        
        try:
            # 启动服务器
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器正在关闭...")
            httpd.server_close()

if __name__ == "__main__":
    # 从命令行参数获取端口号，如果没有提供则使用8000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
