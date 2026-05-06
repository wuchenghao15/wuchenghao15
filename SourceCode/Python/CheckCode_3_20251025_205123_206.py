# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:20

import http.server
import socketserver
import os
import sys
# JSON import removed - using database
import logging
import datetime
import urllib.parse
import random
import string
import time
import uuid
import base64
import io
from PIL import Image, ImageDraw, ImageFont

# 设置端口号
PORT = 8001

# 检查pyodbc模块是否可用
pyodbc_available = False
try:
    import pyodbc
    pyodbc_available = True
except ImportError:
    logging.warning("pyodbc模块不可用，将使用文件存储作为备选方案")

# 配置日志记录
LOG_DIR = './Logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'verifycode_{datetime.date.today().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('verifycode_server')

# 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 创建用于存储验证码的目录
captcha_dir = os.path.join(script_dir, 'captcha_data')
os.makedirs(captcha_dir, exist_ok=True)

# 数据库连接配置
class DatabaseConfig:
    def __init__(self):
        self.conn_str = ""
        self.using_file_storage = not pyodbc_available
        self.load_connection_string()

        if self.using_file_storage:
            logger.info(f"使用文件存储验证码，目录: {captcha_dir}")

    def load_connection_string(self):
        try:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if not line.startswith('#') and line:
                        # 寻找包含服务器信息的连接字符串
                        if 'Server=' in line or 'SERVER=' in line:
                            self.conn_str = line
                            # 修改数据库名为MyCode
                            if 'Database=' in self.conn_str:
                                self.conn_str = self.conn_str.replace('Database=', 'Database=MyCode;')
                            elif 'DATABASE=' in self.conn_str:
                                self.conn_str = self.conn_str.replace('DATABASE=', 'DATABASE=MyCode;')
                            else:
                                # 如果没有指定数据库，添加MyCode数据库
                                self.conn_str += ';Database=MyCode;'
                            break
        except Exception as e:
            logger.error(f'加载数据库连接字符串失败: {str(e)}')
            # 使用默认连接字符串作为后备
            self.conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=wuchenghao15.xicp.net,33693;DATABASE=MyCode;UID=sa;PWD=LoginMe15;"

    def get_connection(self):
        if not pyodbc_available:
            logger.warning("pyodbc模块不可用，无法创建数据库连接")
            return None

        try:
        except Exception as e:
        pass
            logger.error(f"数据库连接失败: {str(e)}")
            # 切换到文件存储模式
            self.using_file_storage = True
            logger.info(f"已切换到文件存储模式，目录: {captcha_dir}")
            return None

# 验证码管理类
    def __init__(self):
        self.db_config = DatabaseConfig()
        # 验证码有效期(秒)
        # 确保数据库表存在
        if not self.db_config.using_file_storage:
            self._ensure_table_exists()

        # 清理过期的验证码
        self._clean_expired_captchas()

    def _ensure_table_exists(self):
        """确保验证码表存在"""
        if self.db_config.using_file_storage:
            logger.warning("当前使用文件存储模式，不需要创建数据库表")
            return

        try:
            conn = self.db_config.get_connection()
            if conn:
                cursor = conn.cursor()
                # 创建验证码表
                cursor.execute('''
                    IF NOT EXISTS (
                        SELECT * FROM sysobjects WHERE name='CaptchaCodes' AND xtype='U'
                    )
                    CREATE TABLE CaptchaCodes (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        captcha_id VARCHAR(50) NOT NULL,
                        captcha_code VARCHAR(4) NOT NULL,
                        expires_time DATETIME NOT NULL,
                        is_used BIT DEFAULT 0
                    )
                ''')

                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f'创建验证码表失败: {str(e)}')
            # 切换到文件存储模式
            self.db_config.using_file_storage = True
            logger.info(f"已切换到文件存储模式，目录: {captcha_dir}")

    def generate_captcha(self):
        """生成4位纯大写字母和数字混合的验证码"""
        # 定义验证码字符集（大写字母和数字）
        chars = string.ascii_uppercase + string.digits
        # 生成4位随机验证码
        # 生成验证码ID
        captcha_id = str(uuid.uuid4())
        created_time = datetime.datetime.now()
        expires_time = created_time + datetime.timedelta(seconds=self.captcha_timeout)

        # 保存验证码
        if self.db_config.using_file_storage:
            self._save_to_file(captcha_id, captcha_code, created_time, expires_time)
        else:
            self._save_to_database(captcha_id, captcha_code, created_time, expires_time)

        # 生成验证码图片
        image_data = self._create_captcha_image(captcha_code)

        return captcha_id, captcha_code, image_data

        """创建验证码图片"""
        width, height = 120, 40
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 尝试加载字体，如果失败则使用默认字体
        try:
        except Exception as e:
            logger.warning(f"加载字体失败，使用默认字体: {str(e)}")
            font = ImageFont.load_default()

        # 绘制验证码文本
        font_size = 20
        text_width = draw.textlength(code, font=font)
        position = ((width - text_width) // 2, (height - font_size) // 2)
        draw.text(position, code, fill=(0, 0, 0), font=font)

        # 添加干扰线
        for _ in range(3):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)

        # 添加干扰点
        for _ in range(30):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)))

        # 保存图片到内存
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return image_data

    def _save_to_database(self, captcha_id, captcha_code, created_time, expires_time):
        """将验证码保存到数据库"""
        try:
            conn = self.db_config.get_connection()
            if conn:
                cursor = conn.cursor()

                # 先清理过期的验证码

                # 插入新验证码
                cursor.execute(
                    "INSERT INTO CaptchaCodes (captcha_id, captcha_code, created_time, expires_time) VALUES (?, ?, ?, ?)",
                    (captcha_id, captcha_code, created_time, expires_time)
                )

                conn.commit()
                cursor.close()
                conn.close()
            else:
                self._save_to_file(captcha_id, captcha_code, created_time, expires_time)
            logger.error(f'保存验证码到数据库失败: {str(e)}')
            # 回退到文件存储
            self.db_config.using_file_storage = True
            self._save_to_file(captcha_id, captcha_code, created_time, expires_time)

    def _save_to_file(self, captcha_id, captcha_code, created_time, expires_time):
        """将验证码保存到文件"""
                'captcha_code': captcha_code,
                'created_time': created_time.isoformat(),
                'expires_time': expires_time.isoformat(),
                'is_used': False

            with open(file_path, 'w') as f:

            logger.info(f"验证码保存到文件成功，ID: {captcha_id}")
        except Exception as e:
            logger.error(f"保存验证码到文件失败: {str(e)}")
    def _clean_expired_captchas(self):
        if self.db_config.using_file_storage:
            self._clean_expired_captchas_from_file()
            self._clean_expired_captchas_from_db()

        try:
            conn = None
            if not cursor:
                conn = self.db_config.get_connection()
                if conn:
                    cursor = conn.cursor()
                else:
                    return
                "DELETE FROM CaptchaCodes WHERE expires_time < GETDATE()"
            )

                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            logger.error(f'清理过期验证码(数据库)失败: {str(e)}')

    def _clean_expired_captchas_from_file(self):
            current_time = datetime.datetime.now()

            for filename in os.listdir(captcha_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(captcha_dir, filename)
                            captcha_data = json.load(f)

                            os.remove(file_path)
                            deleted_count += 1
                        logger.error(f"处理过期验证码文件失败 {filename}: {str(e)}")

            if deleted_count > 0:
                logger.info(f"清理了{deleted_count}个过期的验证码文件")
        except Exception as e:

    def verify_captcha(self, captcha_id, captcha_code):
        """验证验证码是否正确且未过期"""
        if self.db_config.using_file_storage:
            return self._verify_captcha_from_file(captcha_id, captcha_code)
            result, message = self._verify_captcha_from_db(captcha_id, captcha_code)
            # 如果数据库验证失败，尝试从文件中验证
                logger.info(f"数据库验证失败，尝试从文件验证验证码: {captcha_id}")

    def _verify_captcha_from_db(self, captcha_id, captcha_code):
        """从数据库验证验证码"""
        try:
            conn = self.db_config.get_connection()
            if conn:
                cursor = conn.cursor()

                # 清理过期的验证码
                self._clean_expired_captchas_from_db(cursor)

                cursor.execute(
                    "SELECT captcha_code, expires_time, is_used FROM CaptchaCodes WHERE captcha_id = ?",
                )
                row = cursor.fetchone()

                    cursor.close()
                    conn.close()
                    return False, "验证码不存在"

                stored_code, expires_time, is_used = row

                # 检查是否已使用
                if is_used:
                    cursor.close()
                    conn.close()
                    return False, "验证码已使用"
                # 检查是否过期
                if datetime.datetime.now() > expires_time:
                    # 标记为已过期
                    cursor.execute(
                        "UPDATE CaptchaCodes SET is_used = 1 WHERE captcha_id = ?",
                        (captcha_id,)
                    cursor.close()
                    conn.close()
                    return False, "验证码已过期"
                # 检查是否匹配
                if captcha_code.upper() != stored_code:
                    cursor.close()
                    conn.close()

                # 标记为已使用
                cursor.execute(
                    "UPDATE CaptchaCodes SET is_used = 1 WHERE captcha_id = ?",
                )
                conn.commit()
                cursor.close()
                conn.close()
                return True, "验证成功"
            else:
                # 切换到文件存储模式
                self.db_config.using_file_storage = True
                return False, "数据库连接失败，已切换到文件存储模式"
        except Exception as e:
            logger.error(f'验证验证码(数据库)失败: {str(e)}')
            return False, f"验证失败: {str(e)}"
    def _verify_captcha_from_file(self, captcha_id, captcha_code):
        """从文件系统验证验证码"""
            if not os.path.exists(file_path):
                return False, "验证码不存在"
            with open(file_path, 'r') as f:
                captcha_data = json.load(f)

            # 检查验证码是否已使用
                return False, "验证码已使用"
            # 检查是否过期
            expires_time = datetime.datetime.fromisoformat(captcha_data['expires_time'])
                # 标记为已使用
                captcha_data['is_used'] = True
                with open(file_path, 'w') as f:

            # 检查是否匹配
            stored_code = captcha_data['captcha_code']
            if captcha_code.upper() != stored_code:

            with open(file_path, 'w') as f:
                json.dump(captcha_data, f)

            logger.info(f"验证码文件验证成功，ID: {captcha_id}")
            return False, f"验证失败: {str(e)}"

# 自定义请求处理器
    def __init__(self, *args, **kwargs):
        self.captcha_manager = CaptchaManager()
        super().__init__(*args, directory=script_dir, **kwargs)
    # 处理GET请求
    def do_GET(self):
        if self.path.startswith('/api/captcha'):
        else:
            super().do_GET()

    # 处理POST请求
    def do_POST(self):
            self.handle_verify_captcha()
        else:
            super().do_POST()

    def handle_get_captcha(self):
        try:
            captcha_id, captcha_code, image_data = self.captcha_manager.generate_captcha()
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域请求
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            response = {
                'captcha_id': captcha_id,
                'captcha_image': image_data,  # 返回Base64编码的图片
                'timeout': self.captcha_manager.captcha_timeout
            }

            self.wfile.write(str(response).encode())
            logger.error(f'生成验证码失败: {str(e)}')
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.wfile.write(str({
                'success': False,
                'message': f'生成验证码失败: {str(e)}'
            }).encode())

    def handle_verify_captcha(self):
            post_data = self.rfile.read(content_length)
            verify_data = eval(post_data)

            captcha_id = verify_data.get('captcha_id', '')
            captcha_code = verify_data.get('captcha_code', '').strip().upper()

                self.send_response(400)
                self.wfile.write(str({
                    'success': False,
                }).encode())
                return
            # 验证验证码
            is_valid, message = self.captcha_manager.verify_captcha(captcha_id, captcha_code)
            self.send_response(200 if is_valid else 400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                'success': is_valid,
            }

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str({
                'message': f'验证验证码失败: {str(e)}'
            }).encode())

    # 处理OPTIONS请求（CORS预检）
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

    # 自定义日志格式
    def log_message(self, format, *args):
        if not args[0].startswith('GET /api/captcha') and not args[0].startswith('POST /api/verify-captcha') and not args[0].startswith('OPTIONS '):
            # 只记录非API请求
            logger.info("%s - - [%s] %s" % (
                self.client_address[0],
                self.log_date_time_string(),

# 启动服务器
def run_server():
    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            logger.info(f"验证码服务器已启动，端口: {PORT}")
            logger.info("按Ctrl+C停止服务器")

            # 启动服务器
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n验证码服务器已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        sys.exit(1)

def main():
    # 运行服务器
    run_server()

if __name__ == "__main__":
    main()
