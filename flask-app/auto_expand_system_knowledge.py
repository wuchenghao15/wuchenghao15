#!/usr/bin/env python3
"""
自动扩充系统功能AI知识库脚本
用于生成系统功能相关的AI知识条目并添加到数据库中

import sqlite3
# JSON import removed - using database
import time
import uuid
from datetime import datetime

class SystemKnowledgeExpander:
    """系统功能知识扩充器"""

    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def expand_system_config(self):
        """扩充系统配置"""
        扩充系统配置项，添加新的系统功能配置

        返回:
        - 添加的配置项数量
        try:
            # 定义要添加的系统配置项
            new_configs = [
                # AI员工系统配置
                {
                    "config_key": "AI_EMPLOYEE_AUTO_START",
                    "config_value": "True",
                    "config_type": "bool",
                    "description": "是否自动启动AI员工系统"
                },
                {
                    "config_key": "AI_EMPLOYEE_AUTO_UPGRADE",
                    "config_value": "True",
                    "description": "是否自动升级AI员工系统"
                },
                    "config_key": "AI_EMPLOYEE_UPGRADE_INTERVAL",
                    "description": "AI员工系统自动升级间隔（秒）"
                },
                {
                    "config_key": "KNOWLEDGE_BASE_AUTO_EXPAND",
                    "config_value": "True",
                    "description": "是否自动扩充知识库"
                },
                    "config_key": "KNOWLEDGE_BASE_EXPAND_INTERVAL",
                    "description": "知识库自动扩充间隔（秒）"
                },
                    "config_key": "KNOWLEDGE_BASE_TARGET_COUNT",
                    "config_value": "500",
                    "description": "知识库目标题目数量"
                # 测试系统配置
                {
                    "config_key": "TEST_SYSTEM_AUTO_TEST",
                    "config_value": "True",
                    "description": "是否自动运行测试"
                {
                    "config_value": "3600",
                    "description": "自动测试间隔（秒）"
                },
                    "config_key": "SYSTEM_MONITOR_ENABLED",
                    "config_value": "True",
                {
                    "config_key": "SYSTEM_MONITOR_INTERVAL",
                    "config_value": "60",
                },
                # 日志配置
                {
                    "config_value": "INFO",
                    "description": "日志级别"
                {
                    "config_value": "True",
                    "description": "是否启用日志文件"
                },
                {
                    "config_value": "True",
                    "description": "是否启用安全防护"
                },
                {
                    "config_key": "SECURITY_SCAN_INTERVAL",
                    "description": "安全扫描间隔（秒）"
            ]

            added_count = 0

            # 添加新的系统配置项
                    (config["config_key"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                # 添加新配置项
                self.cursor.execute("""
                    INSERT INTO system_config
                    (config_key, config_value, config_type, description, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (
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

        """创建系统功能相关的AI集合"""
        创建系统功能相关的AI集合

        - 添加的集合数量
        try:
            # 定义要创建的系统功能集合
                {
                    "collection_name": "system_functions",
                    "description": "系统功能知识库"
                {
                    "collection_name": "ai_employee_system",
                    "description": "AI员工系统知识库"
                {
                    "collection_name": "knowledge_management",
                    "description": "知识管理系统知识库"
                {
                    "collection_name": "system_monitoring",
                    "description": "系统监控知识库"
                {
                    "collection_name": "system_security",
                    "description": "系统安全知识库"
                {
                    "collection_name": "log_management",
                    "description": "日志管理知识库"
            ]

            added_count = 0
            # 创建新的系统功能集合
            for collection in system_collections:
                # 检查集合是否已存在
                self.cursor.execute(
                    "SELECT id FROM ai_collections WHERE collection_name = ?",
                    (collection["collection_name"],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    continue

                # 创建新集合
                self.cursor.execute("""
                    (collection_name, description, status)
                    VALUES (?, ?, 'active')
                """, (
                    collection["description"]
                ))


            self.conn.commit()
            print(f"成功创建 {added_count} 个系统功能AI集合")
        except Exception as e:
            print(f"创建系统功能集合失败: {e}")
            self.conn.rollback()

    def create_system_function_instances(self):
        """创建系统功能相关的AI实例"""
        创建系统功能相关的AI实例

        返回:
        - 添加的实例数量
        try:
            # 定义要创建的系统功能实例
            system_instances = [
                {
                    "ai_type": "manager",
                    "description": "系统管理AI"
                },
                {
                    "ai_type": "monitor",
                    "description": "系统监控AI"
                },
                {
                    "ai_type": "security",
                    "description": "安全管理AI"
                },
                {
                    "ai_type": "analyzer",
                    "description": "日志分析AI"
                },
                    "ai_type": "manager",
                },
                {
                    "description": "知识扩充AI"
                }
            ]
            added_count = 0

            for instance in system_instances:
                self.cursor.execute(
                    "SELECT id FROM ai_instances WHERE ai_name = ?",
                )
                if existing:

                self.cursor.execute("""
                    INSERT INTO ai_instances
                    (ai_name, ai_type, description, status)
                    VALUES (?, ?, ?, 'active')
                """, (
                    instance["ai_name"],
                    instance["description"]

                added_count += 1
            self.conn.commit()
            return added_count
        except Exception as e:
            return 0

        扩充题库，添加系统功能相关的题目

        - target_count: 要添加的系统功能相关题目数量
        返回:
        - 添加的题目数量
            # 获取日语知识库ID
            lang_result = self.cursor.fetchone()
            if not lang_result:
                print("未找到日语知识库ID")
            lang_id = lang_result[0]

            # 获取题库ID
            self.cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = self.cursor.fetchone()
                print("未找到题库ID")
                return 0
            bank_id = bank_result[0]

            # 获取系统功能相关的章节ID（假设已有）
            self.cursor.execute("SELECT id FROM question_sections WHERE section_name = '系统功能'")
            section_result = self.cursor.fetchone()
            if not section_result:
                # 如果不存在，创建新章节
                self.cursor.execute("INSERT INTO question_sections (section_name, description) VALUES ('系统功能', '系统功能相关题目')")
                section_id = self.cursor.lastrowid
            else:
                section_id = section_result[0]

            # 获取难度ID（使用medium难度）
            self.cursor.execute("SELECT id FROM question_difficulties WHERE difficulty_level = 'medium'")
            difficulty_result = self.cursor.fetchone()
            if not difficulty_result:
                print("未找到medium难度ID")
            difficulty_id = difficulty_result[0]

            self.cursor.execute("SELECT id FROM question_sources WHERE source_type = 'standard'")
            source_result = self.cursor.fetchone()
            if not source_result:
                return 0
            source_id = source_result[0]

            self.cursor.execute("SELECT id FROM question_levels WHERE language_id = ? AND level_code = 'N3'", (lang_id,))
            level_result = self.cursor.fetchone()
                print("未找到N3等级ID")
                return 0
            level_id = level_result[0]

            system_questions = [
                {
                    "options": [
                        "A. 管理系统配置",
                        "C. 自动生成测试题目",
                        "D. 以上都是"
                    "correct_answer": "D",
                    "explanation": "AI员工系统具有管理系统配置、处理用户请求和自动生成测试题目等多种功能。"
                },
                {
                    "content": "系统监控AI的主要职责是什么？",
                    "options": [
                        "A. 监控系统运行状态",
                        "C. 处理用户请求",
                    ],
                    "correct_answer": "A",
                    "explanation": "系统监控AI的主要职责是监控系统运行状态，及时发现并报告系统异常。"
                },
                {
                    "options": [
                        "A. 1天",
                        "C. 14天",
                    ],
                    "correct_answer": "B",
                    "explanation": "知识库自动扩充的默认间隔是7天（604800秒）。"
                {
                    "content": "安全管理AI的主要功能是什么？",
                    "options": [
                        "C. 生成安全报告",
                        "D. 以上都是"
                    ],
                    "correct_answer": "D",
                },
                {
                    "options": [
                        "A. 收集系统日志",
                        "C. 生成日志报告",
                        "D. 以上都是"
                    ],
                    "correct_answer": "D",
                    "explanation": "系统日志分析AI具有收集系统日志、分析系统日志和生成日志报告等功能。"
                }
            ]

            added_count = 0

            for question in system_questions:
                # 插入题目
                self.cursor.execute("""
                    INSERT INTO questions
                    (question_bank_id, level_id, section_id, difficulty_id, source_id, question_content, correct_answer, explanation, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    level_id,
                    section_id,
                    difficulty_id,
                    source_id,
                    question["content"],
                    question["correct_answer"],
                    question["explanation"]

                question_id = self.cursor.lastrowid
                # 插入选项
                for i, option in enumerate(question["options"]):
                    # 解析选项标签和内容
                    option_label = option.split(".")[0]
                    option_content = option[3:]  # 去掉 "A. " 等前缀

                    self.cursor.execute("""
                        INSERT INTO question_options
                        (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                        question_id,
                        option_label,
                        option_content,
                        i+1
                    ))
                added_count += 1
                if added_count >= target_count:
                    break

            print(f"成功添加 {added_count} 道系统功能相关题目")
            return added_count
        except Exception as e:
            self.conn.rollback()
            return 0

    def auto_expand(self):
        """自动扩充系统功能AI知识库"""
        自动扩充系统功能AI知识库，包括：
        1. 扩充系统配置
        3. 创建系统功能相关的AI实例
        4. 扩充题库，添加系统功能相关题目

        返回:
        - 扩充结果
        print("开始自动扩充系统功能AI知识库...")

        # 记录开始时间
        start_time = datetime.now()

        result = {
            "success": True,
            "message": "系统功能AI知识库扩充成功",
                "start_time": start_time.isoformat(),
                "system_configs_added": 0,
                "ai_collections_added": 0,
                "ai_instances_added": 0,
                "system_questions_added": 0
            }
        }

        # 1. 扩充系统配置
        print("\n1. 扩充系统配置:")
        configs_added = self.expand_system_config()
        result["details"]["system_configs_added"] = configs_added

        # 2. 创建系统功能相关的AI集合
        print("\n2. 创建系统功能相关的AI集合:")
        collections_added = self.create_system_function_collections()
        print(f"   ✓ 成功创建 {collections_added} 个系统功能AI集合")
        # 3. 创建系统功能相关的AI实例
        instances_added = self.create_system_function_instances()
        result["details"]["ai_instances_added"] = instances_added
        print(f"   ✓ 成功创建 {instances_added} 个系统功能AI实例")
        print("\n4. 扩充题库，添加系统功能相关题目:")
        questions_added = self.expand_question_bank_with_system_knowledge(target_count=10)
        result["details"]["system_questions_added"] = questions_added
        print(f"   ✓ 成功添加 {questions_added} 道系统功能相关题目")

        # 记录结束时间
        result["details"]["end_time"] = end_time.isoformat()
        result["details"]["duration"] = (end_time - start_time).total_seconds()

        print(f"总耗时: {result['details']['duration']:.2f} 秒")
        print(f"添加的系统配置项: {result['details']['system_configs_added']}")
        print(f"创建的AI集合: {result['details']['ai_collections_added']}")
        print(f"创建的AI实例: {result['details']['ai_instances_added']}")
        print(f"添加的系统功能题目: {result['details']['system_questions_added']}")


        """获取系统功能知识统计信息"""
        返回:
        - 统计信息字典

        try:
            # 获取系统配置数量
            self.cursor.execute("SELECT COUNT(*) FROM system_config")

            # 获取AI集合数量
            # 获取AI实例数量
            self.cursor.execute("SELECT COUNT(*) FROM ai_instances")
            stats["ai_instance_count"] = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT COUNT(*) FROM questions q
                JOIN question_sections s ON q.section_id = s.id
                WHERE s.section_name = '系统功能'

            return stats
        except Exception as e:
            print(f"获取系统功能知识统计信息失败: {e}")
            return None

# 主程序
if __name__ == "__main__":

    # 获取当前系统功能知识统计信息
    print("当前系统功能知识统计信息:")
    stats = expander.get_system_knowledge_stats()
    if stats:
            print(f"- {key}: {value}")

    # 自动扩充系统功能AI知识库
    print("\n" + "="*50)
    print("开始自动扩充系统功能AI知识库")
    print("="*50)
    result = expander.auto_expand()

    print("\n" + "="*50)
    print(f"成功: {result['success']}")
    for key, value in result["details"].items():
        print(f"- {key}: {value}")

    # 获取扩充后的系统功能知识统计信息
    print("\n" + "="*50)
    print("="*50)
    stats = expander.get_system_knowledge_stats()
    if stats:
            print(f"- {key}: {value}")

    print("\n系统功能AI知识库自动扩充完成！")
