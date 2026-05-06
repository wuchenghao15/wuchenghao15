#!/usr/bin/env python3
"""
初始化数据库表结构

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入模块
from app.utils.db import db_manager
from app.utils.table_encryption import table_encryption

def create_tables():
    """创建所有必要的数据库表"""
    print("开始创建数据库表结构...")
    print("=" * 80)

    try:
        # 创建用户表
        print("创建用户表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        print("用户表创建成功")

        # 创建考试表
        print("创建考试表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                name TEXT NOT NULL,
                description TEXT,
                total_questions INTEGER,
                passing_score REAL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        print("考试表创建成功")
        # 创建题目表
        # 获取加密后的表名
        questions_table = table_encryption.encrypt_table_name('questions')
        db_manager.execute(f'DROP TABLE IF EXISTS {questions_table}')
        db_manager.execute(f'''
            CREATE TABLE IF NOT EXISTS {questions_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                points REAL DEFAULT 1.0,
                audio_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        print("题目表创建成功")

        print("创建题目选项表...")
        question_options_table = table_encryption.encrypt_table_name('question_options')
        db_manager.execute(f'''
            CREATE TABLE IF NOT EXISTS {question_options_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_index INTEGER NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES {questions_table}(id)
            )
        print("题目选项表创建成功")

        # 创建题目标签表
        question_tags_table = table_encryption.encrypt_table_name('question_tags')
            CREATE TABLE IF NOT EXISTS {question_tags_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        print("题目标签表创建成功")
        print("创建题目-标签关联表...")
        question_tag_relations_table = table_encryption.encrypt_table_name('question_tag_relations')
        db_manager.execute(f'''
            CREATE TABLE IF NOT EXISTS {question_tag_relations_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tag_id) REFERENCES {question_tags_table}(id),
                UNIQUE(question_id, tag_id)

        # 创建考试记录表
        print("创建考试记录表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                score REAL,
                total_questions INTEGER,
                end_time TIMESTAMP,
                duration INTEGER,
                answers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
        print("考试记录表创建成功")

        # 创建答题记录表
        print("创建答题记录表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS answer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_record_id INTEGER,
                question_id INTEGER,
                user_answer TEXT,
                is_correct INTEGER,
                FOREIGN KEY (exam_record_id) REFERENCES exam_records(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        # 创建错题表
        db_manager.execute('''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                exam_record_id INTEGER NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                error_reason TEXT,
                mastery_level INTEGER DEFAULT 0,
                last_review_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_record_id) REFERENCES exam_records(id)
            )
        print("错题表创建成功")

        # 创建错题标签表
        print("创建错题标签表...")
            CREATE TABLE IF NOT EXISTS error_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        print("错题标签表创建成功")

        # 创建错题-标签关联表
        db_manager.execute('''
                error_question_id INTEGER,
                tag_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (error_question_id, tag_id),
                FOREIGN KEY (tag_id) REFERENCES error_tags(id)
            )
        print("错题-标签关联表创建成功")

        print("创建错题复习计划表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS review_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_time TIMESTAMP,
                review_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
                FOREIGN KEY (error_question_id) REFERENCES error_questions(id)
        print("错题复习计划表创建成功")

        print("创建老师AI交接表...")
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                teacher_ai_id TEXT NOT NULL,
                teacher_feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
            )
        print("老师AI交接表创建成功")

        print("创建学习分析表...")
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS learning_analyses (
                user_id INTEGER NOT NULL,
                analysis_data TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        print("学习分析表创建成功")

        # 创建学习兴趣表
        print("创建学习兴趣表...")
            CREATE TABLE IF NOT EXISTS learning_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        # 创建学习方向表
        print("创建学习方向表...")
        db_manager.execute('''
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
        print("学习方向表创建成功")
        print("创建学习活动表...")
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        print("学习活动表创建成功")

        print("=" * 80)
        print("所有数据库表创建完成！")
    except Exception as e:
        logger.error(f"创建数据库表结构失败: {str(e)}")
    """插入示例数据"""
    print("开始插入示例数据...")

        # 插入示例用户
        print("插入示例用户...")
            '''
            INSERT OR IGNORE INTO user (username, password, email, role)
            ('admin', 'admin123', 'admin@example.com', 'admin')
        )
        db_manager.execute(
            ''',
            ('student1', 'student123', 'student1@example.com', 'student')
        )
        print("插入示例考试...")
            '''
            INSERT OR IGNORE INTO exams (name, description, duration, total_questions, passing_score)
            VALUES (?, ?, ?, ?, ?)
            ''',
            ('数学测试', '基础数学知识测试', 60, 5, 60)

        exam_id_result = db_manager.fetch_scalar('SELECT id FROM exams WHERE name = ?', ('数学测试',))

        if exam_id:
            # 插入示例题目
            print("插入示例题目...")
            questions = [
                {
                    'exam_id': exam_id,
                    'type': 'multiple_choice',
                    'content': '1 + 1 = ?',
                    'correct_answer': '2',
                    'difficulty': 1,
                    'points': 20,
                    'tags': ['基础数学', '加法']
                {
                    'exam_id': exam_id,
                    'type': 'multiple_choice',
                    'content': '2 + 2 = ?',
                    'correct_answer': '4',
                    'difficulty': 1,
                    'options': ['3', '4', '5', '6'],
                    'tags': ['基础数学', '加法']
                },
                {
                    'type': 'multiple_choice',
                    'correct_answer': '6',
                    'points': 20,
                    'options': ['5', '6', '7', '8'],
                    'tags': ['基础数学', '加法']
                },
                {
                    'exam_id': exam_id,
                    'type': 'multiple_choice',
                    'content': '4 + 4 = ?',
                    'correct_answer': '8',
                    'difficulty': 1,
                    'points': 20,
                    'options': ['7', '8', '9', '10'],
                    'tags': ['基础数学', '加法']
                {
                    'type': 'multiple_choice',
                    'content': '5 + 5 = ?',
                    'correct_answer': '10',
                    'difficulty': 1,
                    'points': 20,
                    'options': ['9', '10', '11', '12'],
                    'tags': ['基础数学', '加法']
                }
            ]

            # 获取加密后的表名
            questions_table = table_encryption.encrypt_table_name('questions')
            question_options_table = table_encryption.encrypt_table_name('question_options')
            question_tag_relations_table = table_encryption.encrypt_table_name('question_tag_relations')

            for question in questions:
                # 插入题目
                db_manager.execute(
                    f'''
                    INSERT OR IGNORE INTO {questions_table} (exam_id, type, content, correct_answer, difficulty, points)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (question['exam_id'], question['type'], question['content'],
                     question['correct_answer'], question['difficulty'], question['points'])
                )
                # 获取题目ID
                question_id_result = db_manager.fetch_one('SELECT last_insert_rowid()')
                if question_id_result:
                    question_id = question_id_result[0] if isinstance(question_id_result, tuple) else question_id_result['last_insert_rowid()']

                    # 插入选项
                    if question.get('options'):
                        for index, option_text in enumerate(question['options']):
                            db_manager.execute(
                                f'INSERT INTO {question_options_table} (question_id, option_text, option_index) VALUES (?, ?, ?)',
                                (question_id, option_text, index)
                            )
                    # 插入标签
                    if question.get('tags'):
                        for tag_name in question['tags']:
                            # 查找或创建标签
                            tag = db_manager.fetch_one(f'SELECT id FROM {question_tags_table} WHERE tag_name = ?', (tag_name,))
                            if not tag:
                                db_manager.execute(f'INSERT INTO {question_tags_table} (tag_name) VALUES (?)', (tag_name,))
                                tag_id = tag[0] if isinstance(tag, tuple) else tag['last_insert_rowid()']
                                tag_id = tag[0] if isinstance(tag, tuple) else tag['id']
                            # 关联标签
                            db_manager.execute(
                                f'INSERT OR IGNORE INTO {question_tag_relations_table} (question_id, tag_id) VALUES (?, ?)',
                                (question_id, tag_id)
                            )

        print("示例数据插入完成！")

    except Exception as e:
        logger.error(f"插入示例数据失败: {str(e)}")
        print(f"插入示例数据失败: {str(e)}")

def main():
    """主函数"""
    print("初始化数据库...")
    print("=" * 80)

    # 创建表结构
    create_tables()

    # 插入示例数据
    insert_sample_data()

    print("=" * 80)
    print("数据库初始化完成！")

if __name__ == "__main__":
    main()
