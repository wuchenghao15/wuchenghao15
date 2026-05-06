# -*- coding: utf-8 -*-

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
            with open(os.path.join(script_dir, '../MyData', 'db_connection_string.txt'), 'r', encoding='utf-8') as f:
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

            return pyodbc.connect(self.conn_str)
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            # 切换到文件存储模式
            self.using_file_storage = True
            logger.info(f"已切换到文件存储模式，目录: {captcha_dir}")
            return None

class CaptchaManager:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.captcha_timeout = 300  # 5分钟
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

            import pyodbc
            conn = self.db_config.get_connection()
            if conn:

                # 创建验证码表
                cursor.execute('''
                    IF NOT EXISTS (
                        SELECT * FROM sysobjects WHERE name='CaptchaCodes' AND xtype='U'
                    )
                    CREATE TABLE CaptchaCodes (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        captcha_id VARCHAR(50) NOT NULL,
                        created_time DATETIME NOT NULL,
                        expires_time DATETIME NOT NULL,
                        is_used BIT DEFAULT 0
                    )
                ''')

                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f'创建验证码表失败: {str(e)}')
            # 切换到文件存储模式
            self.db_config.using_file_storage = True
            logger.info(f"已切换到文件存储模式，目录: {captcha_dir}")

    def generate_captcha(self):
        """生成4位纯大写字母和数字混合的验证码"""
        # 定义验证码字符集（大写字母和数字）
        chars = string.ascii_uppercase + string.digits
        captcha_code = ''.join(random.choice(chars) for _ in range(4))
        # 生成验证码ID
        # 计算过期时间
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
    def _create_captcha_image(self, code):
        # 创建验证码图片
        width, height = 120, 40
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 尝试加载字体，如果失败则使用默认字体
            font = ImageFont.load_default()
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
            draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)), width=1)

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
            import pyodbc
            conn = self.db_config.get_connection()
            if conn:
                cursor = conn.cursor()

                self._clean_expired_captchas_from_db(cursor)

                # 插入新验证码
                cursor.execute(
                    "INSERT INTO CaptchaCodes (captcha_id, captcha_code, created_time, expires_time) VALUES (?, ?, ?, ?)",
                    (captcha_id, captcha_code, created_time, expires_time)
                )

                conn.commit()
                cursor.close()
                logger.info(f"验证码保存到数据库成功，ID: {captcha_id}")
                self.db_config.using_file_storage = True
        except Exception as e:
            logger.error(f'保存验证码到数据库失败: {str(e)}')
            # 回退到文件存储
            self.db_config.using_file_storage = True
            self._save_to_file(captcha_id, captcha_code, created_time, expires_time)

    def _save_to_file(self, captcha_id, captcha_code, created_time, expires_time):
            captcha_data = {
                'captcha_code': captcha_code,
                'created_time': created_time.isoformat(),
                'expires_time': expires_time.isoformat(),
            }
            file_path = os.path.join(captcha_dir, f"{captcha_id}.json")
                json.dump(captcha_data, f)

            logger.info(f"验证码保存到文件成功，ID: {captcha_id}")
        except Exception as e:

        """清理过期的验证码"""
        if self.db_config.using_file_storage:
        else:
            self._clean_expired_captchas_from_db()
        """从数据库清理过期的验证码"""
            import pyodbc
            conn = None
            if not cursor:
                conn = self.db_config.get_connection()
                if conn:
                    cursor = conn.cursor()
                else:
            cursor.execute(
                "DELETE FROM CaptchaCodes WHERE expires_time < GETDATE()"
            )
            if conn:
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            logger.error(f'清理过期验证码(数据库)失败: {str(e)}')

            deleted_count = 0
            current_time = datetime.datetime.now()

            for filename in os.listdir(captcha_dir):
                if filename.endswith('.json'):
                        with open(file_path, 'r') as f:
                            captcha_data = json.load(f)
                        if current_time > expires_time:
                            os.remove(file_path)
                    except Exception as e:
                        logger.error(f"处理过期验证码文件失败 {filename}: {str(e)}")

            if deleted_count > 0:
                logger.info(f"清理了{deleted_count}个过期的验证码文件")
            logger.error(f"清理过期验证码(文件)失败: {str(e)}")

    def verify_captcha(self, captcha_id, captcha_code):
        """验证验证码是否正确且未过期"""
        if self.db_config.using_file_storage:
        else:
            result, message = self._verify_captcha_from_db(captcha_id, captcha_code)
            if not result:
            return result, message

    def _verify_captcha_from_db(self, captcha_id, captcha_code):
        """从数据库验证验证码"""
            import pyodbc
            conn = self.db_config.get_connection()
            if conn:
                cursor = conn.cursor()

                # 清理过期的验证码
                self._clean_expired_captchas_from_db(cursor)
                # 查询验证码
                cursor.execute(
                    (captcha_id,)
                )
                row = cursor.fetchone()
                if not row:
                    cursor.close()
                    conn.close()
                    return False, "验证码不存在"

                stored_code, expires_time, is_used = row

                # 检查是否已使用
                if is_used:
                    cursor.close()
                    conn.close()

                # 检查是否过期
                if datetime.datetime.now() > expires_time:
                    # 标记为已过期
                    cursor.execute(
                        "UPDATE CaptchaCodes SET is_used = 1 WHERE captcha_id = ?",
                    conn.commit()
                    cursor.close()
                    conn.close()

                # 检查是否匹配
                if captcha_code.upper() != stored_code:
                    cursor.close()
                    return False, "验证码错误"

                # 标记为已使用
                cursor.execute(
                    (captcha_id,)
                )

                cursor.close()
                conn.close()
                return True, "验证成功"
            else:
                # 切换到文件存储模式
                self.db_config.using_file_storage = True
                return False, "数据库连接失败，已切换到文件存储模式"
        except Exception as e:
            self.db_config.using_file_storage = True

    def _verify_captcha_from_file(self, captcha_id, captcha_code):

            if not os.path.exists(file_path):

            with open(file_path, 'r') as f:
                captcha_data = json.load(f)

            if captcha_data.get('is_used', False):

            # 检查是否过期
            if datetime.datetime.now() > expires_time:
                # 标记为已使用
                captcha_data['is_used'] = True
                return False, "验证码已过期"

            # 检查是否匹配
            stored_code = captcha_data['captcha_code']
                return False, "验证码错误"
            captcha_data['is_used'] = True
            with open(file_path, 'w') as f:
                json.dump(captcha_data, f)

            logger.error(f"验证验证码(文件)失败: {str(e)}")
            return False, f"验证失败: {str(e)}"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.captcha_manager = CaptchaManager()

    # 处理GET请求
    def do_GET(self):
            self.handle_get_captcha()
        else:
            super().do_GET()

    # 处理POST请求
        if self.path.startswith('/api/verify-captcha'):
            self.handle_verify_captcha()
        else:
            super().do_POST()
    # 处理获取验证码请求
    def handle_get_captcha(self):
            # 生成验证码
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域请求
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

                'success': True,
                'captcha_id': captcha_id,
                'captcha_image': image_data,  # 返回Base64编码的图片
                'timeout': self.captcha_manager.captcha_timeout
            }

        except Exception as e:
            logger.error(f'生成验证码失败: {str(e)}')
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str({
                'success': False,
                'message': f'生成验证码失败: {str(e)}'
            }).encode())
    # 处理验证验证码请求
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            verify_data = eval(post_data)

            captcha_id = verify_data.get('captcha_id', '')
            captcha_code = verify_data.get('captcha_code', '').strip().upper()
            if not captcha_id or not captcha_code:
                self.end_headers()
                self.wfile.write(str({
                    'message': '验证码ID和验证码不能为空'
                }).encode())

            # 验证验证码
            # 创建响应
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')

            response = {
                'message': message
            }
            self.wfile.write(str(response).encode())
            logger.error(f'验证验证码时发生错误: {str(e)}')
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
                'success': False,
                'message': f'验证验证码失败: {str(e)}'
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # 自定义日志格式
    def log_message(self, format, *args):
        if not args[0].startswith('GET /api/captcha') and not args[0].startswith('POST /api/verify-captcha') and not args[0].startswith('OPTIONS '):
            # 只记录非API请求
            logger.info("%s - - [%s] %s" % (
                self.client_address[0],
                format % args))

# 启动服务器
def run_server():
        # 创建TCP服务器
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
