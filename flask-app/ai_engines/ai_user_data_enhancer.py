# -*- coding: utf-8 -*-
import sqlite3
from contextlib import contextmanager
import logging
import random
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'ai_user_data_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIUserDataEnhancer:
    def __init__(self):
        self.db_path = r'app.db'
        self.japanese_levels = [r'N5', r'N4', r'N3', r'N2', r'N1']
        self.english_levels = [r'A1', r'A2', r'B1', r'B2', r'C1', r'C2']

    def connect_db(self):
        return sqlite3.connect(self.db_path)

    def get_all_users(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute(r"SELECT id, username FROM users;")
        users = cursor.fetchall()
        conn.close()
        return users

    def get_user_language_levels(self, username, language):
        conn = self.connect_db()
        cursor = conn.cursor()
        if language == r'japanese':
            cursor.execute(r"SELECT * FROM user_japanese_levels WHERE username = ?;", (username,))
        elif language == r'english':
            cursor.execute(r"SELECT * FROM user_english_levels WHERE username = ?;", (username,))

        result = cursor.fetchone()
        conn.close()
        return result

    def generate_initial_language_level(self, language):
        if language == r'japanese':
            return {
                r'level': r'N5',
                r'highest_level': r'N5',
                r'progress': 0.0
            }
        elif language == r'english':
            return {
                r'level': r'A1',
                r'highest_level': r'A1',
                r'progress': 0.0
            }

    def create_user_language_level(self, username, language, level_data):
        conn = self.connect_db()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        if language == r'japanese':
            cursor.execute(r"""
                INSERT INTO user_japanese_levels
                (username, level, highest_level, progress, last_assessment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            r""", (
                username,
                level_data[r'level'],
                level_data[r'highest_level'],
                level_data[r'progress'],
                current_time,
                current_time,
                current_time
            ))
        elif language == r'english':
            cursor.execute(r"""
                INSERT INTO user_english_levels
                (username, level, highest_level, progress, last_assessment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            r""", (
                username,
                level_data[r'level'],
                level_data[r'highest_level'],
                level_data[r'progress'],
                current_time,
                current_time,
                current_time
            ))

        conn.commit()
        conn.close()
        logger.info(fr"为用户 {username} 创建了 {language} 语言水平记录")

    def update_user_language_level(self, username, language, level_data):
        conn = self.connect_db()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        if language == r'japanese':
            cursor.execute(r"""
                UPDATE user_japanese_levels
                SET level = ?, highest_level = ?, progress = ?, last_assessment = ?, updated_at = ?
                WHERE username = ?
            r""", (
                level_data[r'level'],
                level_data[r'highest_level'],
                level_data[r'progress'],
                current_time,
                current_time,
                username
            ))
        elif language == r'english':
            cursor.execute(r"""
                UPDATE user_english_levels
                SET level = ?, highest_level = ?, progress = ?, last_assessment = ?, updated_at = ?
                WHERE username = ?
            r""", (
                level_data[r'level'],
                level_data[r'highest_level'],
                level_data[r'progress'],
                current_time,
                current_time,
                username
            ))

        conn.commit()
        conn.close()
        logger.info(fr"更新了用户 {username} 的 {language} 语言水平")

    def calculate_new_level(self, current_level, progress, language):
        levels = self.japanese_levels if language == r'japanese' else self.english_levels
        current_index = levels.index(current_level)
        new_progress = progress
        new_level = current_level

        if progress >= 100:
            if current_index < len(levels) - 1:
                new_level = levels[current_index + 1]
                new_progress = 0.0
            else:
                new_progress = 100.0
        return {
            r'level': new_level,
            r'progress': new_progress
        }

    def get_user_test_results(self, username, language):
        conn = self.connect_db()
        cursor = conn.cursor()

        test_type = r'japanese' if language == r'japanese' else r'english'
        cursor.execute(r"""
            SELECT score, test_type FROM test_results
            WHERE username = ? AND test_type = ?
            ORDER BY created_at DESC LIMIT 10
        r""", (username, test_type))

        results = cursor.fetchall()
        conn.close()
        return results

    def update_user_level_based_on_tests(self, username, language):
        current_level_record = self.get_user_language_levels(username, language)
        if not current_level_record:
            initial_level = self.generate_initial_language_level(language)
            self.create_user_language_level(username, language, initial_level)
            return

        current_level = current_level_record[2]
        current_progress = current_level_record[4]

        test_results = self.get_user_test_results(username, language)
        if not test_results:
            return

        total_score = 0
        for result in test_results:
            total_score += result[0]

        avg_score = total_score / len(test_results)
        logger.info(fr"用户 {username} 的 {language} 测试平均得分: {avg_score}")

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
        logger.info(fr"用户 {username} 的 {language} 进度变化: {progress_change}%,新进度: {new_progress}%")

        level_update = self.calculate_new_level(current_level, new_progress, language)
        new_level = level_update[r'level']
        final_progress = level_update[r'progress']

        highest_level = current_level_record[3]
        levels = self.japanese_levels if language == r'japanese' else self.english_levels
        if levels.index(new_level) > levels.index(highest_level):
            highest_level = new_level

        self.update_user_language_level(username, language, {
            r'level': new_level,
            r'highest_level': highest_level,
            r'progress': final_progress
        })

    def auto_complete_user_data(self):
        logger.info(r"开始自动完善用户数据...")

        users = self.get_all_users()
        logger.info(fr"共找到 {len(users)} 个用户")

        for user in users:
            user_id, username = user
            logger.info(fr"处理用户: {username}")

            logger.info(r"  检查日语水平...")
            japanese_level = self.get_user_language_levels(username, r'japanese')
            if not japanese_level:
                initial_level = self.generate_initial_language_level(r'japanese')
                self.create_user_language_level(username, r'japanese', initial_level)
            else:
                self.update_user_level_based_on_tests(username, r'japanese')

            logger.info(r"  检查英语水平...")
            english_level = self.get_user_language_levels(username, r'english')
            if not english_level:
                initial_level = self.generate_initial_language_level(r'english')
                self.create_user_language_level(username, r'english', initial_level)
            else:
                self.update_user_level_based_on_tests(username, r'english')

        logger.info(r"用户数据自动完善完成!")

    def run(self):
        self.auto_complete_user_data()

if __name__ == r"__main__":
    enhancer = AIUserDataEnhancer()
    enhancer.run()
