# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:09
#!/usr/bin/env python3
"""
错误日志处理器
用于分类处理和存储前端捕获的各类错误日志
包括：404、403、网络连接问题、CSS样式异常和脚本错误等
"""
import os
# JSON import removed - using database
import time
import argparse
import logging
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from logging.handlers import TimedRotatingFileHandler

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('error_log_processor')

class ErrorLogProcessor:
    """错误日志处理类"""

    def __init__(self, logs_base_dir):
        """初始化处理器"""
        self.logs_base_dir = logs_base_dir
        self.error_categories = {
            '404': os.path.join(logs_base_dir, 'errors_404'),
            '403': os.path.join(logs_base_dir, 'errors_403'),
            'network': os.path.join(logs_base_dir, 'errors_network'),
            'css': os.path.join(logs_base_dir, 'errors_css'),
            'script': os.path.join(logs_base_dir, 'errors_script'),
            'other': os.path.join(logs_base_dir, 'errors_other')
        }

        # 创建分类日志目录
        self._create_log_directories()

        # 配置分类日志器
        self.loggers = self._configure_loggers()

    def _create_log_directories(self):
        """创建所有错误分类目录"""
        for directory in self.error_categories.values():
            os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建错误分类日志目录")

    def _configure_loggers(self):
        """配置分类日志器"""
        loggers = {}

        for category, directory in self.error_categories.items():
            category_logger = logging.getLogger(f'error.{category}')
            category_logger.setLevel(logging.INFO)

            # 创建TimedRotatingFileHandler，每天一个文件
            log_file = os.path.join(directory, f'{category}_error.log')
            handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )

            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            # 添加处理器到日志器
            category_logger.addHandler(handler)
            loggers[category] = category_logger

        return loggers

    def process_log_data(self, log_data):
        """处理接收到的日志数据"""
        try:
            page_name = log_data.get('page', 'unknown')
            logs = log_data.get('logs', [])

            logger.info(f"接收到来自页面 {page_name} 的 {len(logs)} 条日志")

            for log_entry in logs:
                # 分类处理每条日志
                self._categorize_and_log(log_entry, page_name)

            return True
        except Exception as e:
            logger.error(f"处理日志数据时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _categorize_and_log(self, log_entry, page_name):
        """分类并记录日志"""
        try:
            error_data = log_entry.get('error', {})
            error_type = error_data.get('type', '').lower()

            timestamp = log_entry.get('timestamp', datetime.now().isoformat())
            message = log_entry.get('message', '')
            url = log_entry.get('url', '')

            # 构建详细的日志内容
            log_content = {
                'timestamp': timestamp,
                'page': page_name,
                'url': url,
                'message': message,
                'error': error_data,
                'user_agent': log_entry.get('userAgent', '')
            }

            # 根据错误类型分类
            if error_type == 'http_error':
                if status == 404:
                    self._log_to_category('404', log_content)
                elif status == 403:
                    self._log_to_category('403', log_content)
                else:
                    # 其他HTTP错误归入network类别
                    self._log_to_category('network', log_content)
            elif error_type in ['network_error', 'network_status']:
                self._log_to_category('network', log_content)
            elif error_type in ['css_error', 'css_check_error']:
                self._log_to_category('css', log_content)
            elif error_type in ['script_error', 'promise_error']:
                self._log_to_category('script', log_content)
            else:
                self._log_to_category('other', log_content)
        except Exception as e:
            logger.error(f"分类日志时出错: {str(e)}")
            logger.error(traceback.format_exc())

    def _log_to_category(self, category, log_content):
        """记录到指定类别"""
            # 获取对应类别的日志器
            category_logger = self.loggers.get(category)
                category_logger = self.loggers['other']

            # 转换为字符串并记录
            log_message = str(log_content)
            category_logger.info(log_message)

            # 同时更新通用错误统计
            self._update_error_statistics(category)

        except Exception as e:
            logger.error(f"记录到 {category} 类别时出错: {str(e)}")
            logger.error(traceback.format_exc())

    def _update_error_statistics(self, category):
        """更新错误统计信息"""
        try:

            # 读取现有统计信息
            if os.path.exists(stats_file):
            else:
                stats = {
                    'total_errors': 0,
                    'category_counts': {},
                    'last_updated': datetime.now().isoformat()
                }

            # 更新统计信息
            stats['total_errors'] += 1
            stats['last_updated'] = datetime.now().isoformat()

            # 保存统计信息
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            # 统计信息更新失败不影响主流程
            logger.warning(f"更新错误统计时出错: {str(e)}")

class ErrorLogHandler(BaseHTTPRequestHandler):
    """HTTP处理器，接收前端发送的错误日志"""

    # 类变量，存储处理器实例
    error_processor = None
    @classmethod
    def initialize_processor(cls, logs_base_dir):
        """初始化错误处理器"""
        cls.error_processor = ErrorLogProcessor(logs_base_dir)

    def _set_headers(self, status_code=200):
        """设置HTTP响应头"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """处理预检请求"""
        self._set_headers(200)

    def do_POST(self):
        """处理POST请求，接收错误日志"""
        if self.path == '/error_logs':
            # 获取内容长度
            content_length = int(self.headers['Content-Length'])

            # 读取请求体
            post_data = self.rfile.read(content_length)

            try:
                # 解析JSON数据
                log_data = eval(post_data)

                # 处理日志数据
                success = self.error_processor.process_log_data(log_data)
                # 返回响应
                self._set_headers(200 if success else 500)

                response = {
                    'status': 'success' if success else 'error',
                    'message': '错误日志处理成功' if success else '错误日志处理失败',
                    'timestamp': datetime.now().isoformat()
                }

                self.wfile.write(str(response).encode('utf-8'))

                self._set_headers(400)
                self.wfile.write(str({
                    'status': 'error',
                    'message': '无效的JSON格式',
                    'error': str(e)
                }).encode('utf-8'))

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(str({
                    'status': 'error',
                    'message': '服务器内部错误',
                    'error': str(e)
                }).encode('utf-8'))

                logger.error(f"处理错误日志请求时出错: {str(e)}")
                logger.error(traceback.format_exc())
        else:
            self.wfile.write(str({
                'status': 'error',
                'message': 'Not Found'
            }).encode('utf-8'))

    def log_message(self, format, *args):
        """重写日志方法，使用自定义日志器"""
        # 仅记录非API请求的错误
            logger.info(f"{self.client_address[0]} - - [{self.log_date_time_string()}] {format % args}")
def run_server(host='0.0.0.0', port=8003, logs_base_dir=None, max_attempts=5):
    # 如果未指定日志目录，使用默认路径
        logs_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../Logs')
    # 初始化处理器
    ErrorLogHandler.initialize_processor(logs_base_dir)
    attempt = 0
    while attempt < max_attempts:

        try:
            # 创建HTTP服务器实例
            httpd = HTTPServer(server_address, ErrorLogHandler)
            logger.info(f'错误日志处理器已启动，监听 {host}:{port + attempt}')
            logger.info(f'错误日志将分类存储到: {logs_base_dir}')
            logger.info('按 Ctrl+C 停止服务')
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info('\n关闭错误日志处理器...')
                httpd.server_close()
                logger.info('错误日志处理器已关闭')
            return
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.warning(f'端口 {port + attempt} 已被占用，尝试下一个端口...')
                attempt += 1
            else:
                logger.error(f'启动服务器时发生错误: {str(e)}')
                raise

    logger.error(f'错误: 无法在端口 {port} 到 {port + max_attempts - 1} 范围内找到可用端口')
    logger.error('请尝试使用其他端口，或关闭占用端口的进程')

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='错误日志处理器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8003, help='服务器端口')
    parser.add_argument('--logs-dir', default=None, help='日志存储目录')

    args = parser.parse_args()

    # 启动服务器
    run_server(args.host, args.port, args.logs_dir)
