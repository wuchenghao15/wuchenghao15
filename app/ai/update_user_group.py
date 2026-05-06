# -*- coding: utf-8 -*-
import os
import sqlite3
import logging

# 配置日志
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
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')

        logger.info("更新用户组信息初始化完成")

    def check_user_table(self):
        """检查用户表是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查用户表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            user_table = cursor.fetchone()

            conn.close()

            return user_table is not None
        except Exception as e:
            logger.error(f"检查用户表失败: {str(e)}")
            return False

    def check_group_table(self):
        """检查用户组表是否存在"""
            conn = sqlite3.connect(self.db_path)

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_groups'")
            group_table = cursor.fetchone()

            conn.close()

            return group_table is not None
            logger.error(f"检查用户组表失败: {str(e)}")
            return False

    def create_user_table(self):
        """创建用户表"""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 创建用户表
            cursor.execute('''
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    group_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            cursor = conn.cursor()

            # 创建用户组表
                CREATE TABLE user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')

            conn.commit()
            conn.close()

            logger.info("创建用户组表成功")
        except Exception as e:
            logger.error(f"创建用户组表失败: {str(e)}")

    def add_student_group(self):
        """添加学生组"""
        try:

            cursor.execute("SELECT id FROM user_groups WHERE group_name = ?", ('学生组',))
            group = cursor.fetchone()
                # 添加学生组
                cursor.execute("INSERT INTO user_groups (group_name, description) VALUES (?, ?)", ('学生组', '学生用户组'))
                conn.commit()
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

            # 获取学生组ID
            cursor.execute("SELECT id FROM user_groups WHERE group_name = ?", ('学生组',))
            group = cursor.fetchone()

                return group[0]
            return None
        except Exception as e:
            return None

    def check_user_exists(self, username):
        """检查用户是否存在"""
        try:
            conn = sqlite3.connect(self.db_path)

            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()
            return user is not None
        except Exception as e:
            logger.error(f"检查用户是否存在失败: {str(e)}")
            return False

        try:

            # 添加用户
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, 'password123', f"{username}@example.com"))
            conn.commit()

            conn.close()
            logger.info(f"添加用户 {username} 成功")
        except Exception as e:
            logger.error(f"添加用户失败: {str(e)}")
    def update_user_group(self, username, group_id):
        """更新用户组"""
        try:

            # 更新用户组
            cursor.execute("UPDATE users SET group_id = ?, updated_at = ? WHERE username = ?", (group_id, datetime.now().isoformat(), username))
            conn.commit()

            conn.close()
            logger.info(f"更新用户 {username} 的用户组成功")
            return True
            logger.error(f"更新用户组失败: {str(e)}")
            return False

    def run(self, username, group_name):
        try:
            logger.info(f"开始更新用户 {username} 到 {group_name}")
            # 检查并创建用户表
                if not self.create_user_table():
                    logger.error("创建用户表失败，终止流程")
                    return False

            if not self.check_group_table():
                if not self.create_group_table():
                    logger.error("创建用户组表失败，终止流程")
                    return False

            # 添加学生组
            if not self.add_student_group():
                logger.error("添加学生组失败，终止流程")

            # 获取学生组ID
            group_id = self.get_student_group_id()
            if not group_id:
                logger.error("获取学生组ID失败，终止流程")
                return False

            # 检查用户是否存在
                if not self.add_user(username):
                    logger.error(f"添加用户 {username} 失败，终止流程")
                    return False

            # 更新用户组
            if not self.update_user_group(username, group_id):
                logger.error(f"更新用户 {username} 的用户组失败")
                return False

            logger.info(f"更新用户 {username} 到 {group_name} 成功")
            return True
        except Exception as e:
            logger.error(f"运行更新用户组失败: {str(e)}")
            return False

if __name__ == "__main__":
    # 导入datetime模块
    from datetime import datetime

    update_user = UpdateUserGroup()
    update_user.run('caopw', '学生组')
