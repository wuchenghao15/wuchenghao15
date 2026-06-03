# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
自动扩充系统功能AI知识库脚本
用于生成系统功能相关的AI知识条目并添加到数据库中
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
import time
import uuid
from datetime import datetime
import sys
import os


class SystemKnowledgeExpander:
    """系统功能知识扩充器"""

    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def expand_system_config(self):
        """
        扩充系统配置项,添加新的系统功能配置

        返回:
        - 添加的配置项数量
        """
        try:
            new_configs = [
                {
                    "config_key": "AI_EMPLOYEE_AUTO_START",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否自动启动AI员工系统"
                },
                {
                    "config_key": "AI_EMPLOYEE_AUTO_UPGRADE",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否自动升级AI员工系统"
                },
                {
                    "config_key": "AI_EMPLOYEE_UPGRADE_INTERVAL",
                    "config_value": "604800",
                    "config_type": "int",
                    "description": "AI员工系统自动升级间隔(秒)"
                },
                {
                    "config_key": "KNOWLEDGE_BASE_AUTO_EXPAND",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否自动扩充知识库"
                },
                {
                    "config_key": "KNOWLEDGE_BASE_EXPAND_INTERVAL",
                    "config_value": "604800",
                    "config_type": "int",
                    "description": "知识库自动扩充间隔(秒)"
                },
                {
                    "config_key": "KNOWLEDGE_BASE_TARGET_COUNT",
                    "config_value": "500",
                    "config_type": "int",
                    "description": "知识库目标题目数量"
                },
                {
                    "config_key": "TEST_SYSTEM_AUTO_TEST",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否自动运行测试"
                },
                {
                    "config_key": "TEST_SYSTEM_AUTO_TEST_INTERVAL",
                    "config_value": "3600",
                    "config_type": "int",
                    "description": "自动测试间隔(秒)"
                },
                {
                    "config_key": "SYSTEM_MONITOR_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用系统监控"
                },
                {
                    "config_key": "SYSTEM_MONITOR_INTERVAL",
                    "config_value": "60",
                    "config_type": "int",
                    "description": "系统监控间隔(秒)"
                },
                {
                    "config_key": "LOG_LEVEL",
                    "config_value": "INFO",
                    "config_type": "string",
                    "description": "日志级别"
                },
                {
                    "config_key": "LOG_FILE_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用日志文件"
                },
                {
                    "config_key": "SECURITY_PROTECTION_ENABLED",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否启用安全防护"
                },
                {
                    "config_key": "SECURITY_SCAN_INTERVAL",
                    "config_value": "300",
                    "config_type": "int",
                    "description": "安全扫描间隔(秒)"
                }
            ]

            added_count = 0

            for config in new_configs:
                self.cursor.execute(
                    "SELECT id FROM system_config WHERE config_key = ?",
                    (config["config_key"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue

                self.cursor.execute("""
                    INSERT INTO system_config
                    (config_key, config_value, config_type, description, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (
                    config["config_key"],
                    config["config_value"],
                    config["config_type"],
                    config["description"]
                ))

                added_count += 1

            self.conn.commit()
            print(f"成功添加 {added_count} 个系统配置项")
            return added_count
        except Exception as e:
            print(f"扩充系统配置失败: {e}")
            self.conn.rollback()
            return 0

    def create_system_function_collections(self):
        """
        创建系统功能相关的AI集合

        返回:
        - 添加的集合数量
        """
        try:
            system_collections = [
                {
                    "collection_name": "system_functions",
                    "description": "系统功能知识库"
                },
                {
                    "collection_name": "ai_employee_system",
                    "description": "AI员工系统知识库"
                },
                {
                    "collection_name": "knowledge_management",
                    "description": "知识管理系统知识库"
                },
                {
                    "collection_name": "system_monitoring",
                    "description": "系统监控知识库"
                },
                {
                    "collection_name": "system_security",
                    "description": "系统安全知识库"
                },
                {
                    "collection_name": "log_management",
                    "description": "日志管理知识库"
                }
            ]

            added_count = 0

            for collection in system_collections:
                self.cursor.execute(
                    "SELECT id FROM ai_collections WHERE collection_name = ?",
                    (collection["collection_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue

                self.cursor.execute("""
                    INSERT INTO ai_collections
                    (collection_name, description, status)
                    VALUES (?, ?, 'active')
                """, (
                    collection["collection_name"],
                    collection["description"]
                ))

                added_count += 1

            self.conn.commit()
            print(f"成功创建 {added_count} 个系统功能AI集合")
            return added_count
        except Exception as e:
            print(f"创建系统功能集合失败: {e}")
            self.conn.rollback()
            return 0

    def create_system_function_instances(self):
        """
        创建系统功能相关的AI实例

        返回:
        - 添加的实例数量
        """
        try:
            system_instances = [
                {
                    "ai_name": "系统管理AI",
                    "ai_type": "manager",
                    "description": "系统管理AI"
                },
                {
                    "ai_name": "系统监控AI",
                    "ai_type": "monitor",
                    "description": "系统监控AI"
                },
                {
                    "ai_name": "安全管理AI",
                    "ai_type": "security",
                    "description": "安全管理AI"
                },
                {
                    "ai_name": "日志分析AI",
                    "ai_type": "analyzer",
                    "description": "日志分析AI"
                },
                {
                    "ai_name": "知识管理AI",
                    "ai_type": "manager",
                    "description": "知识管理AI"
                },
                {
                    "ai_name": "知识扩充AI",
                    "ai_type": "expander",
                    "description": "知识扩充AI"
                }
            ]

            added_count = 0

            for instance in system_instances:
                self.cursor.execute(
                    "SELECT id FROM ai_instances WHERE ai_name = ?",
                    (instance["ai_name"],)
                )
                if self.cursor.fetchone():
                    continue

                self.cursor.execute("""
                    INSERT INTO ai_instances
                    (ai_name, ai_type, description, status)
                    VALUES (?, ?, ?, 'active')
                """, (
                    instance["ai_name"],
                    instance["ai_type"],
                    instance["description"]
                ))

                added_count += 1

            self.conn.commit()
            return added_count
        except Exception as e:
            print(f"创建系统功能实例失败: {e}")
            self.conn.rollback()
            return 0

    def expand_question_bank_with_system_knowledge(self, target_count=10):
        """
        扩充题库,添加系统功能相关的题目

        返回:
        - 添加的题目数量
        """
        try:
            self.cursor.execute("SELECT id FROM languages WHERE language_code = 'ja'")
            lang_result = self.cursor.fetchone()
            if not lang_result:
                print("未找到日语知识库ID")
                return 0
            lang_id = lang_result[0]

            self.cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = self.cursor.fetchone()
            if not bank_result:
                print("未找到题库ID")
                return 0
            bank_id = bank_result[0]

            self.cursor.execute("SELECT id FROM question_sections WHERE section_name = '系统功能'")
            section_result = self.cursor.fetchone()
            if not section_result:
                self.cursor.execute("INSERT INTO question_sections (section_name, description) VALUES ('系统功能', '系统功能相关题目')")
                section_id = self.cursor.lastrowid
            else:
                section_id = section_result[0]

            self.cursor.execute("SELECT id FROM question_difficulties WHERE difficulty_level = 'medium'")
            difficulty_result = self.cursor.fetchone()
            if not difficulty_result:
                print("未找到medium难度ID")
                return 0
            difficulty_id = difficulty_result[0]

            self.cursor.execute("SELECT id FROM question_sources WHERE source_type = 'standard'")
            source_result = self.cursor.fetchone()
            if not source_result:
                return 0
            source_id = source_result[0]

            self.cursor.execute("SELECT id FROM question_levels WHERE language_id = ? AND level_code = 'N3'", (lang_id,))
            level_result = self.cursor.fetchone()
            if not level_result:
                print("未找到N3等级ID")
                return 0
            level_id = level_result[0]

            system_questions = [
                {
                    "content": "AI员工系统的主要功能是什么?",
                    "options": [
                        "A. 管理系统配置",
                        "B. 处理用户请求",
                        "C. 自动生成测试题目",
                        "D. 以上都是"
                    ],
                    "correct_answer": "D",
                    "explanation": "AI员工系统具有管理系统配置、处理用户请求和自动生成测试题目等多种功能."
                },
                {
                    "content": "系统监控AI的主要职责是什么?",
                    "options": [
                        "A. 监控系统运行状态",
                        "B. 生成系统报告",
                        "C. 处理用户请求",
                        "D. 以上都是"
                    ],
                    "correct_answer": "A",
                    "explanation": "系统监控AI的主要职责是监控系统运行状态,及时发现并报告系统异常."
                },
                {
                    "content": "知识库自动扩充的默认间隔是多少?",
                    "options": [
                        "A. 1天",
                        "B. 7天",
                        "C. 14天",
                        "D. 30天"
                    ],
                    "correct_answer": "B",
                    "explanation": "知识库自动扩充的默认间隔是7天(604800秒)."
                },
                {
                    "content": "安全管理AI的主要功能是什么?",
                    "options": [
                        "A. 监控系统安全",
                        "B. 防止恶意攻击",
                        "C. 生成安全报告",
                        "D. 以上都是"
                    ],
                    "correct_answer": "D",
                    "explanation": "安全管理AI具有监控系统安全、防止恶意攻击和生成安全报告等多种功能."
                },
                {
                    "content": "系统日志分析AI的主要功能是什么?",
                    "options": [
                        "A. 收集系统日志",
                        "B. 分析系统日志",
                        "C. 生成日志报告",
                        "D. 以上都是"
                    ],
                    "correct_answer": "D",
                    "explanation": "系统日志分析AI具有收集系统日志、分析系统日志和生成日志报告等功能."
                }
            ]

            added_count = 0

            for question in system_questions:
                self.cursor.execute("""
                    INSERT INTO questions
                    (question_bank_id, level_id, section_id, difficulty_id, source_id, question_content, correct_answer, explanation, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    bank_id,
                    level_id,
                    section_id,
                    difficulty_id,
                    source_id,
                    question["content"],
                    question["correct_answer"],
                    question["explanation"]
                ))

                question_id = self.cursor.lastrowid

                for i, option in enumerate(question["options"]):
                    option_label = option.split(".")[0]
                    option_content = option[3:]

                    self.cursor.execute("""
                        INSERT INTO question_options
                        (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                    """, (
                        question_id,
                        option_label,
                        option_content,
                        i + 1
                    ))
                added_count += 1
                if added_count >= target_count:
                    break

            self.conn.commit()
            print(f"成功添加 {added_count} 道系统功能相关题目")
            return added_count
        except Exception as e:
            print(f"扩充题库失败: {e}")
            self.conn.rollback()
            return 0

    def auto_expand(self):
        """
        自动扩充系统功能AI知识库

        返回:
        - 扩充结果
        """
        print("开始自动扩充系统功能AI知识库...")

        start_time = datetime.now()

        result = {
            "success": True,
            "message": "系统功能AI知识库扩充成功",
            "details": {
                "start_time": start_time.isoformat(),
                "system_configs_added": 0,
                "ai_collections_added": 0,
                "ai_instances_added": 0,
                "system_questions_added": 0
            }
        }

        print("\n1. 扩充系统配置:")
        configs_added = self.expand_system_config()
        result["details"]["system_configs_added"] = configs_added
        print(f"   成功添加 {configs_added} 个系统配置项")

        print("\n2. 创建系统功能相关的AI集合:")
        collections_added = self.create_system_function_collections()
        result["details"]["ai_collections_added"] = collections_added
        print(f"   成功创建 {collections_added} 个系统功能AI集合")

        print("\n3. 创建系统功能相关的AI实例:")
        instances_added = self.create_system_function_instances()
        result["details"]["ai_instances_added"] = instances_added
        print(f"   成功创建 {instances_added} 个系统功能AI实例")

        print("\n4. 扩充题库,添加系统功能相关题目:")
        questions_added = self.expand_question_bank_with_system_knowledge(target_count=10)
        result["details"]["system_questions_added"] = questions_added
        print(f"   成功添加 {questions_added} 道系统功能相关题目")

        end_time = datetime.now()
        result["details"]["end_time"] = end_time.isoformat()
        result["details"]["duration"] = (end_time - start_time).total_seconds()

        print(f"\n总耗时: {result['details']['duration']:.2f} 秒")
        print(f"添加的系统配置项: {result['details']['system_configs_added']}")
        print(f"创建的AI集合: {result['details']['ai_collections_added']}")
        print(f"创建的AI实例: {result['details']['ai_instances_added']}")
        print(f"添加的系统功能题目: {result['details']['system_questions_added']}")

        return result

    def get_system_knowledge_stats(self):
        """
        获取系统功能知识统计信息

        返回:
        - 统计信息字典
        """
        try:
            stats = {}

            self.cursor.execute("SELECT COUNT(*) FROM system_config")
            stats["config_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM ai_collections")
            stats["collection_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(*) FROM ai_instances")
            stats["ai_instance_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT COUNT(*) FROM questions q
                JOIN question_sections s ON q.section_id = s.id
                WHERE s.section_name = '系统功能'
            """)
            stats["question_count"] = self.cursor.fetchone()[0]

            return stats
        except Exception as e:
            print(f"获取系统功能知识统计信息失败: {e}")
            return None


if __name__ == "__main__":
    expander = SystemKnowledgeExpander()

    print("当前系统功能知识统计信息:")
    stats = expander.get_system_knowledge_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")

    print("\n" + "=" * 50)
    print("开始自动扩充系统功能AI知识库")
    print("=" * 50)
    result = expander.auto_expand()

    print("\n" + "=" * 50)
    print("扩充结果:")
    print(f"成功: {result['success']}")
    for key, value in result["details"].items():
        print(f"- {key}: {value}")

    print("\n" + "=" * 50)
    print("扩充后的系统功能知识统计信息:")
    stats = expander.get_system_knowledge_stats()
    if stats:
        for key, value in stats.items():
            print(f"- {key}: {value}")

    print("\n系统功能AI知识库自动扩充完成!")
