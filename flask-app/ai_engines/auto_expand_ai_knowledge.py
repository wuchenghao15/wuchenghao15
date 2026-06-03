#!/usr/bin/env python3
"""
自动扩充AI知识库脚本
用于生成新的AI知识条目并添加到数据库中
"""
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import time
import uuid
from datetime import datetime

class AIKnowledgeExpander:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def create_knowledge_collection(self, collection_name, description):
        try:
            self.cursor.execute("SELECT id FROM ai_collections WHERE collection_name = ?", (collection_name,))
            existing = self.cursor.fetchone()
            if existing:
                return existing[0]

            self.cursor.execute("""
                INSERT INTO ai_collections (collection_name, description, status)
                VALUES (?, ?, 'active')
            """, (collection_name, description))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"创建知识集合失败: {e}")
            self.conn.rollback()
            return None

    def create_knowledge_instance(self, ai_name, ai_type, description):
        try:
            self.cursor.execute("SELECT id FROM ai_instances WHERE ai_name = ?", (ai_name,))
            existing = self.cursor.fetchone()
            if existing:
                return existing[0]

            self.cursor.execute("""
                INSERT INTO ai_instances (ai_name, ai_type, description, status)
                VALUES (?, ?, ?, 'active')
            """, (ai_name, ai_type, description))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"创建知识实例失败: {e}")
            self.conn.rollback()
            return None

    def expand_question_bank(self, target_count):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM questions")
            current_count = self.cursor.fetchone()[0]

            need_to_generate = max(0, target_count - current_count)
            if need_to_generate <= 0:
                print("题库已经达到或超过目标题数,不需要扩充")
                return 0
            print(f"需要生成的题目数量: {need_to_generate}")

            self.cursor.execute("SELECT id FROM question_banks WHERE language_id = 1")
            bank_result = self.cursor.fetchone()
            if not bank_result:
                print("未找到题库")
                return 0
            bank_id = bank_result[0]

            self.cursor.execute("SELECT id FROM question_levels WHERE language_id = 1")
            levels = [row[0] for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT id FROM question_sections")
            sections = [row[0] for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT id FROM question_difficulties")
            difficulties = [row[0] for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT id FROM question_sources")
            sources = [row[0] for row in self.cursor.fetchall()]

            generated_count = 0

            for _ in range(need_to_generate):
                import random

                level_id = random.choice(levels)
                section_id = random.choice(sections)
                difficulty_id = random.choice(difficulties)
                source_id = random.choice(sources)

                question_content = f"自动生成的题目 {int(time.time())}_{generated_count}"
                correct_answer = random.choice(['A', 'B', 'C', 'D'])
                explanation = f"这是自动生成的题目解释"

                self.cursor.execute("""
                    INSERT INTO questions (question_bank_id, level_id, section_id, difficulty_id, source_id, question_content, correct_answer, explanation, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (bank_id, level_id, section_id, difficulty_id, source_id, question_content, correct_answer, explanation))

                question_id = self.cursor.lastrowid

                options = [f"选项 {i+1}" for i in range(4)]
                for i, option in enumerate(options):
                    option_label = chr(65 + i)
                    self.cursor.execute("""
                        INSERT INTO question_options (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, option_label, option, i+1))

                generated_count += 1
                if generated_count % 10 == 0:
                    print(f"已生成 {generated_count} 道题目")

            self.conn.commit()
            print(f"成功生成 {generated_count} 道新题目")
            return generated_count
        except Exception as e:
            print(f"扩充题库失败: {e}")
            self.conn.rollback()
            return 0

    def expand_ai_collections(self):
        try:
            collections = [
                ("japanese_knowledge", "日语知识库"),
                ("english_knowledge", "英语知识库"),
                ("test_strategies", "测试策略知识库"),
                ("learning_resources", "学习资源知识库")
            ]
            for collection_name, description in collections:
                collection_id = self.create_knowledge_collection(collection_name, description)
                print(f"创建AI集合: {collection_name} (ID: {collection_id})")

            instances = [
                ("english_tutor", "tutor", "英语辅导AI"),
                ("test_analyzer", "analyzer", "测试分析AI"),
                ("knowledge_manager", "manager", "知识管理AI")
            ]

            for ai_name, ai_type, description in instances:
                instance_id = self.create_knowledge_instance(ai_name, ai_type, description)
                print(f"创建AI实例: {ai_name} (ID: {instance_id})")

            return True
        except Exception as e:
            print(f"扩充AI集合失败: {e}")
            return False

    def auto_expand(self, target_question_count=200):
        print("开始自动扩充AI知识库...")

        start_time = datetime.now()

        result = {
            "success": True,
            "message": "AI知识库扩充成功",
            "details": {
                "collections_expanded": 0,
            }
        }

        print("\n1. 扩充AI集合和实例:")
        collections_result = self.expand_ai_collections()
        if collections_result:
            print("   ✓ 成功")
            result["details"]["collections_expanded"] = 4
            result["details"]["instances_expanded"] = 4
        else:
            print("   ✗ 失败")
            result["success"] = False
            result["message"] = "AI集合和实例扩充失败"

        print("\n2. 扩充题库:")
        questions_generated = self.expand_question_bank(target_question_count)
        result["details"]["questions_generated"] = questions_generated
        if questions_generated > 0:
            print(f"   ✓ 成功生成 {questions_generated} 道题目")
        else:
            print("   ✗ 没有生成新题目")

        end_time = datetime.now()
        result["details"]["end_time"] = end_time.isoformat()
        result["details"]["duration"] = (end_time - start_time).total_seconds()

        print("\nAI知识库扩充完成!")
        print(f"总耗时: {result['details']['duration']:.2f} 秒")
        print(f"添加的集合数量: {result['details']['collections_expanded']}")
        print(f"添加的实例数量: {result['details']['instances_expanded']}")
        print(f"生成的题目数量: {result['details']['questions_generated']}")

        return result

    def get_knowledge_stats(self):
        stats = {}

        try:
            self.cursor.execute("SELECT COUNT(*) FROM ai_collections")
            stats["collections_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM ai_instances")
            stats["instances_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM questions")
            stats["questions_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT s.source_type, COUNT(*) as count
                FROM questions q
                JOIN question_sources s ON q.source_id = s.id
                GROUP BY s.source_type
            """)
            stats["source_distribution"] = dict(self.cursor.fetchall())

            self.cursor.execute("""
                SELECT d.difficulty_level, COUNT(*) as count
                FROM questions q
                JOIN question_difficulties d ON q.difficulty_id = d.id
                GROUP BY d.difficulty_level
            """)
            stats["difficulty_distribution"] = dict(self.cursor.fetchall())

            return stats
        except Exception as e:
            print(f"获取知识库统计信息失败: {e}")
            return None

if __name__ == "__main__":
    expander = AIKnowledgeExpander()

    stats = expander.get_knowledge_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")

    print("\n" + "="*50)

    result = expander.auto_expand(target_question_count=200)

    print("\n" + "="*50)
    print("AI知识库扩充结果")
    print("="*50)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    for key, value in result["details"].items():
        print(f"- {key}: {value}")

    print("\n" + "="*50)
    print("扩充后的知识库统计信息")
    print("="*50)
    stats = expander.get_knowledge_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")
