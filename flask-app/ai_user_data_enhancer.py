# -*- coding: utf-8 -*-
import sqlite3
import logging
import random
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_user_data_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIUserDataEnhancer:
    def __init__(self):
        self.db_path = 'app.db'
        self.japanese_levels = ['N5', 'N4', 'N3', 'N2', 'N1']
        self.english_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    def connect_db(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)

    def get_all_users(self):
        """获取所有用户"""
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users;")
        users = cursor.fetchall()
        conn.close()
        return users

    def get_user_language_levels(self, username, language):
        """获取用户的语言水平"""
        cursor = conn.cursor()
        if language == 'japanese':
            cursor.execute("SELECT * FROM user_japanese_levels WHERE username = ?;", (username,))
        elif language == 'english':
            cursor.execute("SELECT * FROM user_english_levels WHERE username = ?;", (username,))

        result = cursor.fetchone()
        conn.close()
        return result
    def generate_initial_language_level(self, language):
        """生成初始语言水平"""
        if language == 'japanese':
            # 新用户默认N5水平，进度0
            return {
                'highest_level': 'N5',
                'progress': 0.0
            }
        elif language == 'english':
            # 新用户默认A1水平，进度0
            return {
                'level': 'A1',
                'progress': 0.0
            }
    def create_user_language_level(self, username, language, level_data):
        """创建用户语言水平记录"""
        cursor = conn.cursor()
        if language == 'japanese':
                INSERT INTO user_japanese_levels
                (username, level, highest_level, progress, last_assessment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                username,
                level_data['level'],
                level_data['highest_level'],
                level_data['progress'],
                current_time,
                current_time,
                current_time
            ))
        elif language == 'english':
            cursor.execute("""
                INSERT INTO user_english_levels
                (username, level, highest_level, progress, last_assessment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                level_data['highest_level'],
                current_time,
                current_time,
                current_time

        conn.commit()
        logger.info(f"为用户 {username} 创建了 {language} 语言水平记录")
    def update_user_language_level(self, username, language, level_data):
        current_time = datetime.now().isoformat()
            cursor.execute("""
                SET level = ?, highest_level = ?, progress = ?, last_assessment = ?, updated_at = ?
            """, (
                level_data['highest_level'],
                username
            ))
        elif language == 'english':
                SET level = ?, highest_level = ?, progress = ?, last_assessment = ?, updated_at = ?
                level_data['level'],
                level_data['highest_level'],
                level_data['progress'],
                current_time,
                current_time,
            ))

        conn.close()
        logger.info(f"更新了用户 {username} 的 {language} 语言水平")

        levels = self.japanese_levels if language == 'japanese' else self.english_levels
        current_index = levels.index(current_level)
        new_progress = progress

        if progress >= 100:
            if current_index < len(levels) - 1:
                # 已经是最高级，保持进度100%
                new_progress = 100.0
        return {
            'level': new_level,
            'progress': new_progress

    def get_user_test_results(self, username, language):

        # 根据语言筛选测试类型
        test_type = 'japanese' if language == 'japanese' else 'english'
            FROM test_results
            WHERE username = ? AND test_type = ?

        conn.close()
        return results
    def update_user_level_based_on_tests(self, username, language):
        """根据测试结果更新用户水平"""
        current_level_record = self.get_user_language_levels(username, language)
        if not current_level_record:

        current_progress = current_level_record[4]  # progress字段

        # 获取最近测试结果
        test_results = self.get_user_test_results(username, language)
            return

        # 计算测试平均得分
        total_score = 0
        for result in test_results:
            total_score += result[0]  # score字段

        avg_score = total_score / len(test_results)
        logger.info(f"用户 {username} 的 {language} 测试平均得分: {avg_score}")

        # 根据得分调整进度
        # 90分以上 +10% 进度，80-89 +5%，70-79 +3%，60-69 +1%，60以下 -2%
        progress_change = 0
        if avg_score >= 90:
            progress_change = 10.0
        elif avg_score >= 80:
            progress_change = 5.0
        elif avg_score >= 70:
            progress_change = 3.0
        elif avg_score >= 60:
            progress_change = 1.0
        else:
            progress_change = -2.0

        new_progress = max(0.0, min(100.0, current_progress + progress_change))
        logger.info(f"用户 {username} 的 {language} 进度变化: {progress_change}%，新进度: {new_progress}%")

        # 计算新水平
        level_update = self.calculate_new_level(current_level, new_progress, language)
        new_level = level_update['level']
        final_progress = level_update['progress']

        # 更新最高水平
        levels = self.japanese_levels if language == 'japanese' else self.english_levels
        if levels.index(new_level) > levels.index(highest_level):
            highest_level = new_level

        # 更新用户水平
        self.update_user_language_level(username, language, {
            'level': new_level,
            'highest_level': highest_level,
            'progress': final_progress
        })

    def auto_complete_user_data(self):
        """自动完善用户数据"""
        logger.info("开始自动完善用户数据...")

        users = self.get_all_users()
        logger.info(f"共找到 {len(users)} 个用户")

        for user in users:
            user_id, username = user
            logger.info(f"处理用户: {username}")

            # 处理日语水平
            logger.info(f"  检查日语水平...")
            japanese_level = self.get_user_language_levels(username, 'japanese')
                initial_level = self.generate_initial_language_level('japanese')
                self.create_user_language_level(username, 'japanese', initial_level)
            else:
                # 根据测试结果更新水平
                self.update_user_level_based_on_tests(username, 'japanese')

            # 处理英语水平
            logger.info(f"  检查英语水平...")
            english_level = self.get_user_language_levels(username, 'english')
            if not english_level:
                initial_level = self.generate_initial_language_level('english')
                self.create_user_language_level(username, 'english', initial_level)
            else:
                # 根据测试结果更新水平
                self.update_user_level_based_on_tests(username, 'english')

        logger.info("用户数据自动完善完成！")

    def run(self):
        """执行自动完善流程"""
        self.auto_complete_user_data()

if __name__ == "__main__":
    enhancer = AIUserDataEnhancer()
    enhancer.run()
