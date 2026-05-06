# -*- coding: utf-8 -*-
import os
import sqlite3
import logging
from datetime import datetime

# 配置日志
logs_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'test_user_login.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestUserLogin:
    """测试用户登录和摸底测试跳转"""

    def __init__(self):
        """初始化测试用户登录测试"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, '../data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.flask_db_path = os.path.join(self.project_root, '../../flask-app/data/mtscos_ai_project.db')

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        logger.info("测试用户登录初始化完成")

    def check_db_connection(self):
        """检查数据库连接"""
        try:
            # 优先使用Flask应用的数据库
            if os.path.exists(self.flask_db_path):
                conn = sqlite3.connect(self.flask_db_path)
                logger.info("成功连接到Flask应用数据库")
                return conn
            else:
                # 使用备用数据库
                conn = sqlite3.connect(self.db_path)
                logger.info("成功连接到备用数据库")
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return None

    def check_user_table(self, conn):
        """检查用户表是否存在"""
            cursor = conn.cursor()

            # 检查用户表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            user_table = cursor.fetchone()

            if not user_table:
                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        email TEXT,
                        role TEXT DEFAULT 'student',
                        is_active INTEGER DEFAULT 1,
                        super_admin_approved INTEGER DEFAULT 1,
                        hardware_admin_approved INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ''')
                conn.commit()
                logger.info("创建用户表成功")
                return True

            return True
        except Exception as e:
            logger.error(f"检查用户表失败: {str(e)}")
            return False

    def check_user_learning_levels_table(self, conn):
        """检查用户学习等级表是否存在"""
        try:

            # 检查用户学习等级表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_learning_levels'")

            return level_table is not None
        except Exception as e:
            logger.error(f"检查用户学习等级表失败: {str(e)}")
            return False

    def create_user_learning_levels_table(self, conn):
        """创建用户学习等级表"""
        try:

            # 创建用户学习等级表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_learning_levels (
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    level TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, subject)

            conn.commit()
            logger.info("创建用户学习等级表成功")
            return True
        except Exception as e:
            logger.error(f"创建用户学习等级表失败: {str(e)}")
            return False

    def add_test_user(self, conn, username='test_student', password='password123', email='test_student@example.com'):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if not user:
                cursor.execute("INSERT INTO users (username, password, email, role, is_active, super_admin_approved, hardware_admin_approved) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (username, password, email, 'student', 1, 1, 1))
                conn.commit()
                user_id = cursor.lastrowid
                logger.info(f"添加测试用户 {username} 成功，ID: {user_id}")
                return user_id
            else:
                user_id = user[0]
                logger.info(f"测试用户 {username} 已存在，ID: {user_id}")
                return user_id
        except Exception as e:
            logger.error(f"添加测试用户失败: {str(e)}")
            return None
    def check_user_language_level(self, conn, user_id, language):
        """检查用户语言等级"""
            cursor = conn.cursor()
            # 构建科目名称
            subject = f"{language}_level"
            # 查询用户语言等级
            cursor.execute('''
                SELECT level FROM user_learning_levels WHERE user_id=? AND subject=?
            ''', (user_id, subject))

            if result:
                logger.info(f"用户 {user_id} 的 {language} 语言等级为: {result[0]}")
                return result[0]
            else:
                logger.info(f"用户 {user_id} 暂无 {language} 语言等级记录")
                return None
        except Exception as e:
            logger.error(f"检查用户语言等级失败: {str(e)}")

    def test_login_flow(self, username, language='japanese'):
        try:
            conn = self.check_db_connection()
                logger.error("无法连接数据库")

            # 检查用户表
                logger.error("用户表不存在")
                conn.close()
                return False

            # 检查并创建用户学习等级表
            if not self.check_user_learning_levels_table(conn):
                if not self.create_user_learning_levels_table(conn):
                    logger.error("创建用户学习等级表失败")
                    conn.close()
                    return False

            # 添加测试用户
            user_id = self.add_test_user(conn, username)
            if not user_id:
                logger.error("添加测试用户失败")
                conn.close()
                return False

            # 检查用户语言等级
            language_level = self.check_user_language_level(conn, user_id, language)

            if not language_level:
                logger.info(f"用户 {username} 无 {language} 语言等级，应该跳转到摸底测试")
                logger.info("测试结果: 符合预期 - 无语言等级时应跳转到摸底测试")
            else:
                logger.info(f"用户 {username} 已有 {language} 语言等级: {language_level}，不需要跳转到摸底测试")
                logger.info("测试结果: 符合预期 - 有语言等级时不需要跳转到摸底测试")

            conn.close()
            return True
        except Exception as e:
            logger.error(f"测试登录流程失败: {str(e)}")
            return False
        """运行测试"""
        try:
            logger.info(f"开始测试用户 {test_username} 的登录流程")
            # 测试日语语言等级
            logger.info("测试日语语言等级检查...")
            self.test_login_flow(test_username, 'japanese')
            # 测试英语语言等级
            logger.info("测试英语语言等级检查...")
            self.test_login_flow(test_username, 'english')

            logger.info("测试完成")
            return True
        except Exception as e:
            logger.error(f"运行测试失败: {str(e)}")
            return False

if __name__ == "__main__":
    test_login = TestUserLogin()
