# -*- coding: utf-8 -*-
import os
import sqlite3
import logging
from datetime import datetime

logs_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'update_user_group.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UpdateUserGroup:
    """更新用户组信息的类"""

    def __init__(self):
        """初始化"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, '../data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')

        os.makedirs(self.data_dir, exist_ok=True)

        logger.info("更新用户组信息初始化完成")

    def check_user_table(self):
        """检查用户表是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            user_table = cursor.fetchone()

            conn.close()

            return user_table is not None
        except Exception as e:
            logger.error(f"检查用户表失败: {str(e)}")
            return False

    def check_group_table(self):
        """检查用户组表是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_groups'")
            group_table = cursor.fetchone()

            conn.close()

            return group_table is not None
        except Exception as e:
            logger.error(f"检查用户组表失败: {str(e)}")
            return False

    def create_user_table(self):
        """创建用户表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    group_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

            logger.info("创建用户表成功")
            return True
        except Exception as e:
            logger.error(f"创建用户表失败: {str(e)}")
            return False

    def create_group_table(self):
        """创建用户组表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

            logger.info("创建用户组表成功")
            return True
        except Exception as e:
            logger.error(f"创建用户组表失败: {str(e)}")
            return False

    def add_student_group(self):
        """添加学生组"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM user_groups WHERE group_name = ?", ('学生组',))
            group = cursor.fetchone()

            if not group:
                cursor.execute("INSERT INTO user_groups (group_name, description) VALUES (?, ?)", ('学生组', '学生用户组'))
                conn.commit()
                logger.info("添加学生组成功")
            else:
                logger.info("学生组已存在")

            conn.close()
            return True
        except Exception as e:
            logger.error(f"添加学生组失败: {str(e)}")
            return False

    def get_student_group_id(self):
        """获取学生组ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM user_groups WHERE group_name = ?", ('学生组',))
            group = cursor.fetchone()

            conn.close()

            if group:
                return group[0]
            return None
        except Exception as e:
            logger.error(f"获取学生组ID失败: {str(e)}")
            return None

    def check_user_exists(self, username):
        """检查用户是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()
            return user is not None
        except Exception as e:
            logger.error(f"检查用户是否存在失败: {str(e)}")
            return False

    def add_user(self, username):
        """添加用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, 'password123', f"{username}@example.com"))
            conn.commit()

            conn.close()
            logger.info(f"添加用户 {username} 成功")
            return True
        except Exception as e:
            logger.error(f"添加用户失败: {str(e)}")
            return False

    def update_user_group(self, username, group_id):
        """更新用户组"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET group_id = ?, updated_at = ? WHERE username = ?", (group_id, datetime.now().isoformat(), username))
            conn.commit()

            conn.close()
            logger.info(f"更新用户 {username} 的用户组成功")
            return True
        except Exception as e:
            logger.error(f"更新用户组失败: {str(e)}")
            return False

    def run(self, username, group_name):
        try:
            logger.info(f"开始更新用户 {username} 到 {group_name}")

            if not self.check_user_table():
                if not self.create_user_table():
                    logger.error("创建用户表失败,终止流程")
                    return False

            if not self.check_group_table():
                if not self.create_group_table():
                    logger.error("创建用户组表失败,终止流程")
                    return False

            if not self.add_student_group():
                logger.error("添加学生组失败,终止流程")
                return False

            group_id = self.get_student_group_id()
            if not group_id:
                logger.error("获取学生组ID失败,终止流程")
                return False

            if not self.check_user_exists(username):
                if not self.add_user(username):
                    logger.error(f"添加用户 {username} 失败,终止流程")
                    return False

            if not self.update_user_group(username, group_id):
                logger.error(f"更新用户 {username} 的用户组失败")
                return False

            logger.info(f"更新用户 {username} 到 {group_name} 成功")
            return True
        except Exception as e:
            logger.error(f"运行更新用户组失败: {str(e)}")
            return False

if __name__ == "__main__":
    update_user = UpdateUserGroup()
    update_user.run('caopw', '学生组')
