#!/usr/bin/env python3
"""
AI驱动的题库自动扩充系统
利用AI技术和Python技术自动扩充题库和丰富考试系统的题型展示

import os
import sys
import sqlite3
# JSON import removed - using database
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.question_generator_service import QuestionGeneratorService


class AutoQuestionBankExpander:
    """题库自动扩充器"""

    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.question_service = QuestionGeneratorService()
        self.conn = None
        self.cursor = None

        # 扩充配置
        self.expand_config = {
            "target_questions_per_category": 100,  # 每个分类目标题目数
            "batch_size": 50,  # 每批生成数量
            "min_difficulty": 1,
            "max_difficulty": 10,
            "question_types": ["multiple_choice", "fill_blank", "short_answer", "essay"]
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def get_current_question_count(self, category_id=None, exam_type=None, exam_level=None):
        """获取当前题目数量"""
        if not self.connect():
            return 0

        try:
            params = []

            if category_id:
                conditions.append("category_id = ?")
                params.append(category_id)

            if exam_type:
                conditions.append("exam_type = ?")
                params.append(exam_type)

            if exam_level:
                conditions.append("exam_level = ?")
                params.append(exam_level)

            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
            else:
                where_clause = ""

            sql = f"SELECT COUNT(*) FROM questions{where_clause}"
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"获取题目数量失败: {str(e)}")
        finally:
            self.close()
    def get_all_categories(self):
        """获取所有分类"""
        if not self.connect():
            return []

            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取分类失败: {str(e)}")
            return []
            self.close()

    def get_all_exam_levels(self):
        """获取所有考试等级"""
        return [
            ("日语", "N3", "JLPT", 3, 5),
            ("日语", "N2", "JLPT", 5, 7),
            ("日语", "N1", "JLPT", 7, 10),
            ("英语", "九年制基础", "九年义务教育", 1, 2),
            ("英语", "九年制进阶", "九年义务教育", 2, 4),
            ("英语", "四级", "CET", 3, 5),
            ("英语", "六级", "CET", 4, 6),
            ("英语", "专四", "TEM", 5, 7),
            ("英语", "专八", "TEM", 7, 10),
            ("数学", "九年制基础", "九年义务教育", 1, 3),
            ("数学", "九年制进阶", "九年义务教育", 3, 5),
            ("数学", "高中数学", "高考", 4, 7),
            ("数学", "高等数学", "大学", 6, 10),
            ("物理", "九年制基础", "九年义务教育", 2, 4),
            ("物理", "九年制进阶", "九年义务教育", 3, 5),
            ("物理", "高中物理", "高考", 4, 7),
            ("物理", "大学物理", "大学", 6, 10),
            ("化学", "九年制基础", "九年义务教育", 2, 4),
            ("化学", "九年制进阶", "九年义务教育", 3, 5),
            ("化学", "高中化学", "高考", 4, 7),
            ("化学", "大学化学", "大学", 6, 10),
            ("生物", "九年制基础", "九年义务教育", 2, 4),
            ("生物", "九年制进阶", "九年义务教育", 3, 5),
            ("生物", "高中生物", "高考", 4, 7),
            ("生物", "大学生物", "大学", 6, 10),
            ("历史", "九年制基础", "九年义务教育", 2, 4),
            ("历史", "九年制进阶", "九年义务教育", 3, 5),
            ("历史", "高中历史", "高考", 4, 7),
            ("历史", "大学历史", "大学", 6, 10),
            ("地理", "九年制基础", "九年义务教育", 2, 4),
            ("地理", "九年制进阶", "九年义务教育", 3, 5),
            ("地理", "高中地理", "高考", 4, 7),
            ("地理", "大学地理", "大学", 6, 10),
            ("计算机", "九年制基础", "九年义务教育", 2, 4),
            ("计算机", "九年制进阶", "九年义务教育", 3, 5),
            ("计算机", "高中信息技术", "高考", 4, 7),
            ("计算机", "大学计算机", "大学", 6, 10),
        ]

    def generate_and_save_questions(self, subject, topic, exam_type, exam_level,
                                   difficulty_min, difficulty_max, count=10):
        """生成并保存题目"""
        generated_count = 0

        for i in range(count):
            # 随机选择难度
            difficulty = random.randint(difficulty_min, difficulty_max)

            # 随机选择题型
            question_type = random.choice(self.expand_config["question_types"])

            # 生成题目
            question_data = self.question_service.generate_question(
                question_type, difficulty, subject, topic
            )

            if question_data:
                # 保存到数据库
                if self.save_question(question_data, exam_type, exam_level):
                    generated_count += 1
                    print(f"  生成题目 {generated_count}/{count}: {question_data['question'][:50]}...")

        return generated_count

    def save_question(self, question_data, exam_type, exam_level):
        """保存题目到数据库"""
        if not self.connect():
            return False

        try:
            topic = question_data.get('topic', '基础知识')
            if category_row:
                category_id = category_row[0]
            else:
                self.cursor.execute("INSERT INTO question_categories (name, description) VALUES (?, ?)",
                                  (topic, f"{question_data.get('subject', '通用')}-{topic}"))
                category_id = self.cursor.lastrowid

            # 获取或创建语言ID
            subject = question_data.get('subject', '通用')
            self.cursor.execute("SELECT id FROM question_languages WHERE name = ?", (subject,))
            lang_row = self.cursor.fetchone()
            if lang_row:
            else:
                self.cursor.execute("INSERT INTO question_languages (name, code) VALUES (?, ?)",
                                  (subject, subject.lower()))
                language_id = self.cursor.lastrowid

            # 获取或创建难度级别ID
            difficulty = question_data.get('difficulty_level', 5)
            self.cursor.execute("SELECT id FROM question_difficulties WHERE difficulty_level = ?",
                              (f"Level {difficulty}",))
            diff_row = self.cursor.fetchone()
                difficulty_id = diff_row[0]
            else:
                self.cursor.execute("INSERT INTO question_difficulties (difficulty_level, description) VALUES (?, ?)",
                                  (f"Level {difficulty}", f"难度等级 {difficulty}"))
                difficulty_id = self.cursor.lastrowid

            # 准备选项
            options = question_data.get('options', [])
            if options:
                options_json = str(options)
            else:

            # 插入题目
            self.cursor.execute("""
                INSERT INTO questions
                (content, answer, explanation, category_id, language_id, level_id,
                 question_type, options, exam_type, exam_level, difficulty_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question_data.get('answer', ''),
                question_data.get('explanation', ''),
                category_id,
                language_id,
                difficulty_id,
                question_data.get('question_type', 'multiple_choice'),
                options_json,
                exam_type,
                exam_level,
                question_data.get('difficulty_description', f"难度{difficulty}")
            ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"保存题目失败: {str(e)}")
        finally:
            self.close()
    def expand_question_bank(self, target_total=1000):
        """扩充题库"""
        print("=" * 80)
        print("开始自动扩充题库")

        # 获取当前题目总数
        current_count = self.get_current_question_count()
        print(f"\n当前题库题目数量: {current_count}")
        print(f"目标题目数量: {target_total}")

        if current_count >= target_total:
            print("题库已达到目标数量，无需扩充")
            return
        # 需要生成的题目数量
        need_to_generate = target_total - current_count
        print(f"需要生成题目数量: {need_to_generate}")

        # 获取所有考试等级
        exam_levels = self.get_all_exam_levels()

        # 计算每个等级需要生成的题目数
        questions_per_level = need_to_generate // len(exam_levels)
        total_generated = 0

        # 为每个考试等级生成题目
        for subject, level, exam_type, diff_min, diff_max in exam_levels:
            print(f"\n生成 {subject} - {level} 的题目...")

            # 获取该等级当前题目数
            current_level_count = self.get_current_question_count(
                exam_type=exam_type, exam_level=level
            )

            # 计算需要生成的数量
            need_for_this_level = max(0, questions_per_level - current_level_count)

            if need_for_this_level > 0:
                # 为该等级的各个知识点生成题目
                topics = self.get_topics_for_subject(subject, level)

                for topic in topics:
                    count_per_topic = need_for_this_level // len(topics) if topics else need_for_this_level

                    generated = self.generate_and_save_questions(
                        subject, topic, exam_type, level,
                        diff_min, diff_max, count_per_topic
                    )

                    total_generated += generated
                    print(f"  {topic}: 生成 {generated} 题")
            else:

        print("\n" + "=" * 80)
        print(f"扩充完成！共生成 {total_generated} 道新题目")
        print("=" * 80)

        # 显示扩充后的统计
        self.show_statistics()

    def get_topics_for_subject(self, subject, level):
        """获取学科的知识点"""
        knowledge_base = self.question_service.knowledge_base
        if subject in knowledge_base:
            subject_data = knowledge_base[subject]
            topics = []
            for topic_key, topic_data in subject_data.items():
                # 检查难度范围是否匹配
                if isinstance(topic_data, dict) and 'difficulty_range' in topic_data:
                    min_diff, max_diff = topic_data['difficulty_range']
                    level_diff = {'N5': 1, 'N4': 2, 'N3': 4, 'N2': 6, 'N1': 8,
                                 '九年制基础': 2, '九年制进阶': 4,
                                 '四级': 4, '六级': 5, '专四': 6, '专八': 8,
                                 '高中': 5, '大学': 8, '高等数学': 8}.get(level, 5)

                    if min_diff <= level_diff <= max_diff:
                else:
                    topics.append(topic_key)

            return topics

        return ["基础知识"]

    def show_statistics(self):
        """显示题库统计信息"""
        if not self.connect():
            return

        try:

            # 总题目数
            self.cursor.execute("SELECT COUNT(*) FROM questions")
            total = self.cursor.fetchone()[0]
            print(f"总题目数: {total}")
            # 按考试类型统计
            print("\n按考试类型统计：")
            self.cursor.execute("""
                SELECT exam_type, COUNT(*) as count
                FROM questions
                WHERE exam_type IS NOT NULL
                GROUP BY exam_type
                ORDER BY count DESC
            for row in self.cursor.fetchall():
                print(f"  {row[0]}: {row[1]} 题")

            # 按学科统计
            print("\n按学科统计：")
            self.cursor.execute("""
                SELECT ql.name, COUNT(*) as count
                FROM questions q
                GROUP BY ql.name
                ORDER BY count DESC
            """)
            for row in self.cursor.fetchall():
                print(f"  {row[0]}: {row[1]} 题")

            # 按题型统计
            print("\n按题型统计：")
            self.cursor.execute("""
                SELECT question_type, COUNT(*) as count
                GROUP BY question_type
                ORDER BY count DESC
            """)
            for row in self.cursor.fetchall():
                print(f"  {row[0]}: {row[1]} 题")

            # 按难度统计
            print("\n按难度统计：")
            self.cursor.execute("""
                SELECT qd.difficulty_level, COUNT(*) as count
                FROM questions q
                GROUP BY qd.difficulty_level
                ORDER BY qd.difficulty_level
            """)
            for row in self.cursor.fetchall():
                print(f"  {row[0]}: {row[1]} 题")

        except Exception as e:
            print(f"显示统计信息失败: {str(e)}")
        finally:
            self.close()
    """主函数"""
    expander = AutoQuestionBankExpander()

    # 显示当前统计
    print("当前题库状态：")
    expander.show_statistics()

    # 询问用户目标题目数量
        target_total = int(target) if target else 1000
        target_total = 1000
    # 开始扩充
    expander.expand_question_bank(target_total)


    main()
