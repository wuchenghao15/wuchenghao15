#!/usr/bin/env python3
"""
题库更新脚本
用于更新和扩充题库内容

import os
import sys
import sqlite3
# JSON import removed - using database
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class QuestionBankUpdater:
    """题库更新器"""

    def __init__(self, db_path):
        """初始化题库更新器"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"成功连接到数据库: {self.db_path}")
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")

    def execute(self, sql, params=None):
        """执行SQL语句"""
        try:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()

    def fetch_all(self, sql, params=None):
        """执行查询并返回所有结果"""
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            return []
        """添加题库"""
        sql = """
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        return self.execute(sql, (name, description, language_id))

    def add_question(self, content, answer, explanation, category_id, language_id, level_id, question_type, options):
        """添加问题"""
        sql = """
        INSERT OR IGNORE INTO questions
        (content, answer, explanation, category_id, language_id, level_id, question_type, options, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        params = (
            content,
            answer,
            explanation,
            category_id,
            language_id,
            level_id,
            str(options)
        )
        return self.execute(sql, params)

    def get_language_id(self, code):
        """根据语言代码获取语言ID"""
        sql = "SELECT id FROM question_languages WHERE code = ?"
        result = self.fetch_all(sql, (code,))
        return result[0][0] if result else None

    def get_category_id(self, name):
        """根据分类名称获取分类ID"""
        sql = "SELECT id FROM question_categories WHERE name = ?"
        result = self.fetch_all(sql, (name,))
        return result[0][0] if result else None

    def get_level_id(self, name):
        """根据难度级别名称获取级别ID"""
        sql = "SELECT id FROM question_levels WHERE name = ?"
        result = self.fetch_all(sql, (name,))
        return result[0][0] if result else None

    def update_question_banks(self):
        """更新题库"""
        print("更新题库...")

        # 获取语言ID
        en_id = self.get_language_id("en")
        ja_id = self.get_language_id("ja")

        if not all([zh_id, en_id, ja_id]):
            print("获取语言ID失败")
        # 添加中文题库
        self.add_question_bank("中文数学题库", "包含各种难度的中文数学题目", zh_id)
        self.add_question_bank("中文英语题库", "包含各种难度的中文英语题目", zh_id)
        self.add_question_bank("中文日语题库", "包含各种难度的中文日语题目", zh_id)

        # 添加英语题库
        self.add_question_bank("English Vocabulary Bank", "English vocabulary questions of various difficulty levels", en_id)

        # 添加日语题库
        self.add_question_bank("日本語数学問題集", "様々な難易度の日本語数学問題", ja_id)
        self.add_question_bank("日本語単語問題集", "様々な難易度の日本語単語問題", ja_id)

        print("题库更新完成")
        return True

    def update_questions(self):
        """更新问题"""
        print("更新问题...")
        # 获取语言ID
        zh_id = self.get_language_id("zh")
        en_id = self.get_language_id("en")
        ja_id = self.get_language_id("ja")

        # 获取分类ID
        math_id = self.get_category_id("数学")
        english_id = self.get_category_id("英语")
        japanese_id = self.get_category_id("日语")

        # 获取难度级别ID
        beginner_id = self.get_level_id("入门级")
        elementary_id = self.get_level_id("初级")
        intermediate_id = self.get_level_id("中级")
        advanced_id = self.get_level_id("高级")
        expert_id = self.get_level_id("专家级")

        if not all([zh_id, en_id, ja_id, math_id, english_id, japanese_id, beginner_id, elementary_id, intermediate_id, advanced_id, expert_id]):
            return False
        # 添加中文数学问题
            {
                "answer": "2",
                "explanation": "1加1等于2",
                "category_id": math_id,
                "level_id": beginner_id,
                "question_type": "single_choice",
                "options": ["1", "2", "3", "4"]
            },
            {
                "content": "2 + 3 × 4 = ?",
                "answer": "14",
                "explanation": "根据运算顺序，先乘除后加减，所以3×4=12，然后2+12=14",
                "category_id": math_id,
                "language_id": zh_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
                "options": ["14", "20", "11", "16"]
            },
            {
                "content": "解方程：2x + 5 = 15",
                "answer": "5",
                "explanation": "2x = 15 - 5 = 10，所以x = 10 ÷ 2 = 5",
                "category_id": math_id,
                "language_id": zh_id,
                "level_id": intermediate_id,
                "question_type": "single_choice",
                "options": ["5", "10", "15", "20"]
            }
        ]

        # 添加中文英语问题
            {
                "content": "What is the capital of China?",
                "answer": "Beijing",
                "explanation": "北京是中国的首都",
                "language_id": zh_id,
                "question_type": "single_choice",
                "options": ["Shanghai", "Beijing", "Guangzhou", "Shenzhen"]
            {
                "content": "Which of the following is a verb?",
                "explanation": "Run是动词，意思是跑",
                "category_id": english_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
            }
        ]

        # 添加中文日语问题
            {
                "content": "日本の首都は何ですか？",
                "answer": "東京",
                "explanation": "东京是日本的首都",
                "category_id": japanese_id,
                "language_id": zh_id,
                "level_id": beginner_id,
                "question_type": "single_choice",
                "options": ["大阪", "東京", "京都", "福岡"]
                "content": "'こんにちは'は何の意味ですか？",
                "answer": "你好",
                "explanation": "'こんにちは'是日语中'你好'的意思",
                "language_id": zh_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
            }

        # 添加英语数学问题
            {
                "content": "What is 5 + 7?",
                "answer": "12",
                "category_id": math_id,
                "language_id": en_id,
                "level_id": beginner_id,
                "question_type": "single_choice",
                "options": ["10", "11", "12", "13"]
            {
                "content": "What is the square root of 64?",
                "explanation": "The square root of 64 is 8",
                "category_id": math_id,
                "language_id": en_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
            }
        ]

            {
                "answer": "Cold",
                "explanation": "'Cold' is the opposite of 'hot'",
                "category_id": english_id,
                "language_id": en_id,
                "level_id": beginner_id,
                "question_type": "single_choice",
                "options": ["Warm", "Cold", "Cool", "Freezing"]
            {
                "answer": "Buy",
                "explanation": "'Buy' means to give money in exchange for goods or services",
                "category_id": english_id,
                "language_id": en_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
                "options": ["Sell", "Buy", "Trade", "Exchange"]
            }
        ]
        # 添加日语数学问题
                "content": "3 + 4 = ?",
                "answer": "7",
                "explanation": "3足す4は7です",
                "category_id": math_id,
                "language_id": ja_id,
                "question_type": "single_choice",
                "options": ["5", "6", "7", "8"]
            {
                "content": "10 - 3 = ?",
                "answer": "7",
                "explanation": "10引く3は7です",
                "category_id": math_id,
                "language_id": ja_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
            }
        ]

        # 添加日语词汇问题
            {
                "content": "'犬'は何の意味ですか？",
                "explanation": "'犬'は英語で'Dog'といいます",
                "category_id": japanese_id,
                "language_id": ja_id,
                "level_id": beginner_id,
                "question_type": "single_choice",
                "content": "'水'は何の意味ですか？",
                "answer": "Water",
                "category_id": japanese_id,
                "level_id": elementary_id,
                "question_type": "single_choice",
                "options": ["Water", "Fire", "Earth", "Wind"]
            }
        ]
        # 合并所有问题
                        english_math_questions + english_vocabulary_questions + \
                        japanese_math_questions + japanese_vocabulary_questions
        for question in all_questions:
            self.add_question(
                question["answer"],
                question["explanation"],
                question["language_id"],
                question["level_id"],
                question["question_type"],
                question["options"]
            )
        print(f"问题更新完成，添加了 {len(all_questions)} 个问题")
        return True

    def update_all(self):
        """更新所有内容"""
        print("开始更新题库...")
        # 更新题库
        self.update_question_banks()

        # 更新问题
        self.update_questions()

        print("题库更新完成！")


    # 创建题库更新器
    updater = QuestionBankUpdater(db_path)

    # 连接数据库
        # 更新题库
        updater.update_all()
        updater.close()
    else:
        print("无法连接到数据库，更新失败")
