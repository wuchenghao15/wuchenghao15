# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:09
#!/usr/bin/env python3
"""
Arduino 在线开发服务模块
实现在线编辑、编译和上传 Arduino 代码的功能
"""
import http.server
import socketserver
# JSON import removed - using database
import logging
import os
import sys
import tempfile
import subprocess
import re
import uuid
import time
from datetime import datetime
from urllib.parse import parse_qs, unquote
import hashlib

# 设置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'arduino_{datetime.now().strftime("%Y-%m-%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ArduinoServer')

# 脚本目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# 临时文件目录
TEMP_DIR = os.path.join(project_root, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# 用户数据目录
USERS_DATA_DIR = os.path.join(project_root, 'users_data')
os.makedirs(USERS_DATA_DIR, exist_ok=True)

# Arduino 常用板型和端口配置
ARDUINO_BOARDS = {
    'uno': 'arduino:avr:uno',
    'nano': 'arduino:avr:nano',
    'mega': 'arduino:avr:mega',
    'leonardo': 'arduino:avr:leonardo',
    'esp8266': 'esp8266:esp8266:nodemcuv2',
    'esp32': 'esp32:esp32:esp32'
}

# 常用 Arduino 代码模板
ARDUINO_TEMPLATES = {
    'blink': '''void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

  digitalWrite(LED_BUILTIN, HIGH);  // 打开LED
  delay(1000);                      // 等待1秒
  digitalWrite(LED_BUILTIN, LOW);   // 关闭LED
  delay(1000);                      // 等待1秒
}''',
    'button': '''const int buttonPin = 2;

int buttonState = 0;

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT);
}

  buttonState = digitalRead(buttonPin);

  if (buttonState == HIGH) {
  } else {
    digitalWrite(ledPin, LOW);
  }
}''',
  Serial.begin(9600);
}

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    Serial.println(input);
  }
}

class ArduinoHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 设置服务器目录为项目根目录
        super().__init__(*args, directory=project_root, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        # 检查API请求是否需要认证
        if self.path.startswith('/api/arduino'):
            if '/ports' in self.path or '/compile' in self.path or '/upload' in self.path or '/verify' in self.path:
                if not self.is_user_authenticated():
                    self.send_unauthorized_response()
                    return

            if '/templates' in self.path:
                self.handle_get_templates()
            elif '/boards' in self.path:
                self.handle_get_boards()
            elif '/ports' in self.path:
                self.handle_get_ports()
            else:
                self.send_error(404, "Not Found")
        else:
            super().do_GET()

    def do_POST(self):
        """处理POST请求"""
        # 所有POST请求都需要认证
        if not self.is_user_authenticated():
            self.send_unauthorized_response()
            return

        try:
            if self.path == '/api/arduino/compile':
            elif self.path == '/api/arduino/upload':
                self.handle_upload()
            elif self.path == '/api/arduino/verify':
                self.handle_verify()
            else:
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = str({
                'success': False,
                'message': f'服务器内部错误: {str(e)}'
            })
            self.wfile.write(response.encode('utf-8'))

    def is_user_authenticated(self):
        try:
            # 从Cookie中获取用户信息
            for cookie in cookies.split(';'):
                cookie = cookie.strip()
                if cookie.startswith('mtscos_user_cookie='):
                    # 解码cookie值
                    encoded_user_data = cookie.split('=', 1)[1]
                    user_data_str = unquote(encoded_user_data)

                    # 尝试解析用户数据
                    try:
                        user_data = eval(user_data_str)
                        logger.info(f"已验证用户: {user_data.get('username', 'unknown')}")
                        return True
                    except json.JSONDecodeError:
                        logger.error("Cookie中用户数据格式错误")
                        return False

            # 如果没有找到有效的Cookie，检查是否有本地用户文件
            # 这是一个回退方案，用于测试环境
            if os.path.exists(os.path.join(USERS_DATA_DIR, 'test_user.json')):
                logger.info("测试环境: 允许访问")
                return True

            logger.warn("用户未认证")
            return False
        except Exception as e:
            logger.error(f"认证检查时出错: {str(e)}")
            return False

    def send_unauthorized_response(self):
        """发送未授权响应"""
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = str({
            'success': False,
            'message': '未授权访问，请先登录',
            'error': 'UNAUTHORIZED'
        self.wfile.write(response.encode('utf-8'))

    def handle_get_templates(self):
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = str({
                'templates': ARDUINO_TEMPLATES
            self.wfile.write(response.encode('utf-8'))
            logger.error(f'获取模板时发生错误: {str(e)}')

        """获取支持的Arduino板型"""
        try:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
                'success': True,
            })
            self.wfile.write(response.encode('utf-8'))
            logger.error(f'获取板型时发生错误: {str(e)}')
            self.send_error(500, f'Internal Server Error: {str(e)}')
    def handle_get_ports(self):
        """获取可用的串口"""
        try:
            ports = self.list_serial_ports()
            self.send_response(200)
            self.end_headers()
            response = str({
            })
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f'Internal Server Error: {str(e)}')

    def handle_compile(self):
        try:
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            data = eval(post_data)
            code = data.get('code', '')
            board = data.get('board', 'uno')
            # 验证输入
            if not code:
                return
            if board not in ARDUINO_BOARDS:
                self.send_error(400, f'不支持的板型: {board}')

            result = self.compile_arduino_code(code, ARDUINO_BOARDS[board])

            self.send_response(200 if result['success'] else 400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.wfile.write(str(result).encode('utf-8'))
            self.send_error(400, '无效的JSON数据')
        except Exception as e:

        """上传代码到Arduino板"""
        try:
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            data = eval(post_data)
            code = data.get('code', '')
            board = data.get('board', 'uno')

            logger.info(f'开始上传Arduino代码，板型: {board}，端口: {port}')

            # 验证输入
            if not code or not port:

            if board not in ARDUINO_BOARDS:
                self.send_error(400, f'不支持的板型: {board}')
                return
            # 上传代码
            result = self.upload_arduino_code(code, ARDUINO_BOARDS[board], port)

            self.send_response(200 if result['success'] else 400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(result).encode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, '无效的JSON数据')
        except Exception as e:
            self.send_error(500, f'上传失败: {str(e)}')

    def handle_verify(self):
        """验证代码语法"""
        try:
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            data = eval(post_data)

            code = data.get('code', '')
            logger.info('开始验证Arduino代码语法')

            result = self.verify_arduino_syntax(code)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

        except json.JSONDecodeError:
            self.send_error(400, '无效的JSON数据')
        except Exception as e:
            logger.error(f'验证时发生错误: {str(e)}')
            self.send_error(500, f'验证失败: {str(e)}')
    def list_serial_ports(self):
        """列出所有可用的串口"""
        ports = []
        try:
                import serial.tools.list_ports
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # Linux 系统
            elif sys.platform.startswith('darwin'):
                import glob
                ports = glob.glob('/dev/tty.*') + glob.glob('/dev/cu.*')
        except Exception as e:
            logger.error(f'列出串口时发生错误: {str(e)}')

        for port in ports:
            try:
                # 尝试打开端口以验证是否可用
                    filtered_ports.append(port)
            except (OSError, IOError):
        return filtered_ports
    def create_temp_sketch(self, code):
        """创建临时的Arduino sketch文件"""
        sketch_id = str(uuid.uuid4())[:8]
        sketch_dir = os.path.join(TEMP_DIR, f'sketch_{sketch_id}')
        os.makedirs(sketch_dir, exist_ok=True)

        ino_file = os.path.join(sketch_dir, f'sketch_{sketch_id}.ino')
        with open(ino_file, 'w', encoding='utf-8') as f:
            f.write(code)


        """编译Arduino代码"""
        try:

                subprocess.run(['arduino-cli', '--version'], check=True, capture_output=True)
                has_cli = True
            except (subprocess.SubprocessError, FileNotFoundError):

            if has_cli:
                # 使用arduino-cli编译
                cmd = [
                    'arduino-cli', 'compile',
                    '--fqbn', board,
                    sketch_dir
                ]


                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '编译成功',
                        'output': result.stdout
                    }
                else:
                        'message': '编译失败',
                        'error': result.stderr
                    }
            else:
                if 'setup()' not in code or 'loop()' not in code:
                    return {
                        'success': False,
                        'message': '编译失败：缺少setup()或loop()函数',
                        'error': 'Arduino代码必须包含setup()和loop()函数'
                    }

                # 简单的括号匹配检查
                close_brackets = code.count('}')
                if open_brackets != close_brackets:
                    return {
                        'success': False,
                        'message': '编译失败：括号不匹配',
                    }

                # 模拟编译成功
                    'success': True,
                    'message': '编译成功（模拟模式）',
                }

                'success': False,
                'message': f'编译过程中发生错误',
                'error': str(e)
            }

    def upload_arduino_code(self, code, board, port):
        try:
            # 首先编译代码
            compile_result = self.compile_arduino_code(code, board)
            if not compile_result['success']:
                return compile_result

            # 检查arduino-cli是否安装
                subprocess.run(['arduino-cli', '--version'], check=True, capture_output=True)
                has_cli = True
            except (subprocess.SubprocessError, FileNotFoundError):
                has_cli = False

            if has_cli:
                # 使用arduino-cli上传
                sketch_dir = os.path.dirname(self.create_temp_sketch(code))
                cmd = [
                    'arduino-cli', 'upload',
                    '--fqbn', board,
                    '--port', port,
                    sketch_dir
                ]


                    return {
                        'success': True,
                        'message': '上传成功',
                        'output': result.stdout
                else:
                    return {
                        'success': False,
                        'error': result.stderr
            else:
                # 模拟上传（开发环境下）
                return {
                    'message': '上传成功（模拟模式）',
                    'output': '注意：arduino-cli未安装，使用模拟上传模式'
                }

        except Exception as e:
            return {
                'message': f'上传过程中发生错误',
                'error': str(e)
            }

        """简单验证Arduino代码语法"""
        warnings = []

        # 检查必要的函数
        if 'setup()' not in code:
            errors.append('缺少必要的setup()函数')
        if 'loop()' not in code:
            errors.append('缺少必要的loop()函数')
        # 检查括号匹配
        open_brackets = code.count('{')
        close_brackets = code.count('}')
        if open_brackets != close_brackets:
            errors.append(f'括号不匹配：{open_brackets}个开括号，{close_brackets}个闭括号')
        # 检查分号
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 检查简单语句是否以分号结尾（排除函数定义、条件语句等）
            if (stripped and not stripped.startswith('#') and
                not stripped.startswith('//') and
                not stripped.endswith('{') and
                not stripped.endswith('}') and
                not stripped.endswith(':') and
                not '=' in stripped and not stripped.endswith(';') and
                not any(x in stripped for x in ['void ', 'if(', 'for(', 'while(', 'switch('])):
                warnings.append(f'第{i+1}行：语句可能缺少分号')

        # 检查未闭合的注释
        if '/*' in code and '*/' not in code.split('/*')[-1]:
            errors.append('存在未闭合的多行注释')

        return {
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def log_message(self, format, *args):
        """重写日志记录方法，使用自定义日志器"""
        log_entry = format % args
            return
        logger.info(f'HTTP {self.client_address[0]} - {log_entry}')

def run_server(port=8003):
    """启动Arduino在线开发服务器"""
    try:
        logger.info(f'正在启动Arduino在线开发服务器，端口: {port}')

        # 创建TCP服务器
        with socketserver.TCPServer(('', port), ArduinoHandler) as httpd:
            logger.info(f'Arduino在线开发服务器已启动，监听端口: {port}')

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                logger.info('服务器已停止')
    except Exception as e:
        logger.error(f'启动服务器时发生错误: {str(e)}')

def setup_test_user():
    test_user_path = os.path.join(USERS_DATA_DIR, 'test_user.json')
            'username': 'test_user',
            'displayName': '测试用户'
        with open(test_user_path, 'w', encoding='utf-8') as f:
            json.dump(test_user_data, f, ensure_ascii=False, indent=2)
def main():
    """主函数"""
    logger.info('Arduino在线开发服务启动')

    setup_test_user()

    port = 8003
    if len(sys.argv) > 1:
            port = int(sys.argv[1])
            logger.info(f'使用命令行参数中的端口: {port}')
        except ValueError:

    # 启动服务器

if __name__ == '__main__':
    main()
