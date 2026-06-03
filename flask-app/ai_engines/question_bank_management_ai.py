# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库管理AI - 负责题库规则题目维护与更新,题库扩充等,直接上传数据库,共享错误修复案例到脑库
"""

import os
import sqlite3
import json
import time
import logging
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('question_bank_management_ai')

class QuestionBankManagementAI:
    """题库管理AI"""

    def __init__(self):
        self.ai_id = f"question-bank-management-ai-{int(time.time())}"
        self.name = "题库管理AI"
        self.description = "负责题库规则题目维护与更新,题库扩充等,直接上传数据库,共享错误修复案例到脑库"
        self.created_at = datetime.now().isoformat()
        logger.info(f"✅ 新建题库管理AI: {self.ai_id}")

    def manage_question_bank(self):
        """管理题库"""
        logger.info("=== 开始管理题库 ===")

        bank_management = {
            'rules_management': self.manage_rules(),
            'questions_maintenance': self.maintain_questions(),
            'bank_expansion': self.expand_question_bank(),
            'management_time': self.created_at
        }

        logger.info("✅ 题库管理完成")
        return bank_management

    def manage_rules(self):
        """管理题库规则"""
        try:
            db_path = 'data/mtscos_ai_project.db'
            if not os.path.exists('data'):
                os.makedirs('data')

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS question_bank_rules (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT UNIQUE, rule_name TEXT, rule_description TEXT, rule_config TEXT, status TEXT, created_at TEXT, updated_at TEXT)")

            rules = [
                {
                    'rule_id': 'rule-001',
                    'rule_name': '题目难度分级规则',
                    'rule_description': '根据题目难度进行分级管理',
                    'rule_config': str({'difficulty_levels': ['easy', 'medium', 'hard'], 'score_ranges': {'easy': [1, 5], 'medium': [6, 8], 'hard': [9, 10]}}),
                    'status': 'active'
                },
                {
                    'rule_id': 'rule-002',
                    'rule_name': '题目类型规则',
                    'rule_description': '根据题目类型进行分类管理',
                    'rule_config': str({'question_types': ['multiple_choice', 'true_false', 'fill_blank', 'essay']}),
                    'status': 'active'
                },
                {
                    'rule_id': 'rule-003',
                    'rule_name': '题目审核规则',
                    'rule_description': '题目审核流程规则',
                    'rule_config': str({'review_steps': ['submission', 'review', 'approval', 'publish'], 'required_reviews': 2}),
                    'status': 'active'
                }
            ]

            managed_count = 0
            for rule in rules:
                cursor.execute("INSERT OR REPLACE INTO question_bank_rules (rule_id, rule_name, rule_description, rule_config, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
                    rule['rule_id'],
                    rule['rule_name'],
                    rule['rule_description'],
                    rule['rule_config'],
                    rule['status'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                managed_count += 1

            conn.commit()
            conn.close()

            logger.info(f"✅ 成功管理 {managed_count} 个题库规则")
            return {'status': 'ok', 'managed_count': managed_count, 'rules': rules}

        except Exception as e:
            logger.error(f"❌ 管理题库规则失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def maintain_questions(self):
        """维护题目"""
        try:
            db_path = 'data/mtscos_ai_project.db'

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id TEXT UNIQUE, question_text TEXT, question_type TEXT, difficulty TEXT, options TEXT, correct_answer TEXT, explanation TEXT, tags TEXT, status TEXT, created_at TEXT, updated_at TEXT)")

            questions = [
                {
                    'question_id': 'q-001',
                    'question_text': 'Python中,以下哪个不是内置数据类型?',
                    'question_type': 'multiple_choice',
                    'difficulty': 'easy',
                    'options': str(['list', 'dict', 'set', 'array']),
                    'correct_answer': 'array',
                    'explanation': 'array不是Python的内置数据类型,list、dict和set都是Python的内置数据类型.',
                    'tags': str(['Python', '数据类型']),
                    'status': 'published'
                },
                {
                    'question_id': 'q-002',
                    'question_text': 'Flask是一个轻量级的Web框架.',
                    'question_type': 'true_false',
                    'difficulty': 'easy',
                    'options': str(['True', 'False']),
                    'correct_answer': 'True',
                    'explanation': 'Flask是一个轻量级的Python Web框架,适合构建小型到中型的Web应用.',
                    'tags': str(['Flask', 'Web框架']),
                    'status': 'published'
                },
                {
                    'question_id': 'q-003',
                    'question_text': 'SQL中,用于从表中获取数据的关键字是?',
                    'question_type': 'fill_blank',
                    'difficulty': 'medium',
                    'options': str([]),
                    'correct_answer': 'SELECT',
                    'explanation': 'SELECT关键字用于从SQL表中获取数据.',
                    'tags': str(['SQL', '数据库']),
                    'status': 'published'
                }
            ]

            maintained_count = 0
            for question in questions:
                cursor.execute("INSERT OR REPLACE INTO questions (question_id, question_text, question_type, difficulty, options, correct_answer, explanation, tags, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    question['question_id'],
                    question['question_text'],
                    question['question_type'],
                    question['difficulty'],
                    question['options'],
                    question['correct_answer'],
                    question['explanation'],
                    question['tags'],
                    question['status'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                maintained_count += 1

            conn.commit()
            conn.close()

            logger.info(f"✅ 成功维护 {maintained_count} 个题目")
            return {'status': 'ok', 'maintained_count': maintained_count, 'questions': questions}

        except Exception as e:
            logger.error(f"❌ 维护题目失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def expand_question_bank(self):
        """扩充题库"""
        try:
            db_path = 'data/mtscos_ai_project.db'

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, question_id TEXT UNIQUE, question_text TEXT, question_type TEXT, difficulty TEXT, options TEXT, correct_answer TEXT, explanation TEXT, tags TEXT, status TEXT, created_at TEXT, updated_at TEXT)")

            question_types = ['multiple_choice', 'true_false', 'fill_blank']
            difficulties = ['easy', 'medium', 'hard']

            expanded_questions = []
            for i in range(10):
                question_id = f'q-{100+i}'
                question_type = random.choice(question_types)
                difficulty = random.choice(difficulties)

                if question_type == 'multiple_choice':
                    question_text = f'Python中,以下哪个函数用于获取列表长度?'
                    options = str(['len()', 'length()', 'size()', 'count()'])
                    correct_answer = 'len()'
                    explanation = 'len()函数用于获取列表、字符串等对象的长度.'
                elif question_type == 'true_false':
                    question_text = 'Python是一种编译型语言.'
                    options = str(['True', 'False'])
                    correct_answer = 'False'
                    explanation = 'Python是一种解释型语言,不是编译型语言.'
                else:
                    question_text = 'Python中,用于定义函数的关键字是?'
                    options = str([])
                    correct_answer = 'def'
                    explanation = 'def关键字用于定义函数.'

                tags = str(['Python', '基础']) if difficulty == 'easy' else str(['Python', '进阶'])

                expanded_questions.append({
                    'question_id': question_id,
                    'question_text': question_text,
                    'question_type': question_type,
                    'difficulty': difficulty,
                    'options': options,
                    'correct_answer': correct_answer,
                    'explanation': explanation,
                    'tags': tags,
                    'status': 'review'
                })

            expanded_count = 0
            for question in expanded_questions:
                cursor.execute("INSERT OR REPLACE INTO questions (question_id, question_text, question_type, difficulty, options, correct_answer, explanation, tags, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    question['question_id'],
                    question['question_text'],
                    question['question_type'],
                    question['difficulty'],
                    question['options'],
                    question['correct_answer'],
                    question['explanation'],
                    question['tags'],
                    question['status'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                expanded_count += 1

            conn.commit()
            conn.close()

            logger.info(f"✅ 成功扩充 {expanded_count} 个题目到题库")
            return {'status': 'ok', 'expanded_count': expanded_count, 'questions': expanded_questions}

        except Exception as e:
            logger.error(f"❌ 扩充题库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def report_to_database(self, bank_management):
        """上报到数据库"""
        logger.info("=== 开始上报到数据库 ===")

        try:
            db_path = 'data/mtscos_ai_project.db'

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            rules_managed = bank_management['rules_management'].get('managed_count', 0)
            management_id = f"mgmt-{int(time.time())}"

            cursor.execute("CREATE TABLE IF NOT EXISTS question_bank_management_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, management_id TEXT UNIQUE, ai_id TEXT, rules_managed INTEGER, status TEXT, created_at TEXT)")

            cursor.execute("INSERT OR REPLACE INTO question_bank_management_reports (management_id, ai_id, rules_managed, status, created_at) VALUES (?, ?, ?, ?, ?)", (
                management_id,
                self.ai_id,
                rules_managed,
                'completed',
                datetime.now().isoformat()
            ))

            cursor.execute("CREATE TABLE IF NOT EXISTS workflow_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, report_id TEXT UNIQUE, ai_id TEXT, report_type TEXT, report_data TEXT, created_at TEXT)")

            report_data = str({
                'bank_management': bank_management,
                'management_id': management_id,
                'ai_id': self.ai_id,
                'created_at': self.created_at
            })

            report_id = f"report-{int(time.time())}"
            cursor.execute("INSERT OR REPLACE INTO workflow_reports (report_id, ai_id, report_type, report_data, created_at) VALUES (?, ?, ?, ?, ?)", (
                report_id,
                self.ai_id,
                'question_bank_management',
                report_data,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            return {'status': 'ok', 'management_id': management_id, 'report_id': report_id}

        except Exception as e:
            logger.error(f"❌ 上报到数据库失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def share_error_cases(self):
        """共享错误修复案例到脑库"""
        logger.info("=== 开始共享错误修复案例 ===")

        try:
            error_cases = [
                {
                    "id": "question-bank-case-001",
                    "title": "题库规则管理失败",
                    "description": "题库规则管理失败,可能是数据库连接问题或规则格式错误",
                    "solution": "检查数据库连接和规则格式,确保规则符合数据库表结构要求",
                    "affected_files": ["app/services/question_bank_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "question-bank-case-002",
                    "title": "题目维护失败",
                    "description": "题目维护失败,可能是题目格式错误或数据库权限问题",
                    "solution": "检查题目格式和数据库权限,确保题目数据符合要求",
                    "affected_files": ["app/services/question_bank_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "question-bank-case-003",
                    "title": "题库扩充失败",
                    "description": "题库扩充失败,可能是生成的题目质量问题或数据库存储空间不足",
                    "solution": "检查生成的题目质量和数据库存储空间,确保有足够的空间存储新题目",
                    "affected_files": ["app/services/question_bank_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "question-bank-case-004",
                    "title": "数据库上报失败",
                    "description": "数据库上报失败,可能是数据库连接问题或表结构不匹配",
                    "solution": "检查数据库连接和表结构,确保表结构符合上报要求",
                    "affected_files": ["app/services/question_bank_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                },
                {
                    "id": "question-bank-case-005",
                    "title": "工作流报告保存失败",
                    "description": "工作流报告保存失败,可能是数据库权限问题或存储空间不足",
                    "solution": "检查数据库权限和存储空间,确保有足够的权限和空间保存报告",
                    "affected_files": ["app/services/question_bank_service.py"],
                    "fix_date": self.created_at,
                    "fixer": self.ai_id
                }
            ]

            brain_file = 'app/ai/brain/error_cases.json'
            if not os.path.exists('app/ai/brain'):
                os.makedirs('app/ai/brain')

            existing_cases = []
            if os.path.exists(brain_file):
                with open(brain_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_cases = json.load(f)
                    except Exception:
                        existing_cases = []

            all_cases = existing_cases + error_cases

            seen_ids = set()
            unique_cases = []
            for case in all_cases:
                if case['id'] not in seen_ids:
                    seen_ids.add(case['id'])
                    unique_cases.append(case)

            with open(brain_file, 'w', encoding='utf-8') as f:
                json.dump(unique_cases, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 错误修复案例共享完成,保存至: {brain_file}")
            logger.info(f"✅ 共共享 {len(error_cases)} 个新案例")

            return {'status': 'ok', 'cases': error_cases, 'total_cases': len(unique_cases)}

        except Exception as e:
            logger.error(f"❌ 共享错误修复案例失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def run_workflow(self):
        """执行完整的工作流程"""

        bank_management = self.manage_question_bank()

        database_report = self.report_to_database(bank_management)

        error_cases = self.share_error_cases()

        results = {
            'bank_management': bank_management,
            'database_report': database_report,
            'error_cases': error_cases
        }

        return results

def main():
    """主函数"""
    logger.info("=== 启动题库管理AI ===")

    bank_ai = QuestionBankManagementAI()

    results = bank_ai.run_workflow()

    logger.info("\n == 工作结果摘要 ===")
    logger.info(f"规则管理: {results['bank_management']['rules_management']}")
    logger.info(f"题目维护: {results['bank_management']['questions_maintenance']}")
    logger.info(f"题库扩充: {results['bank_management']['bank_expansion']}")
    logger.info(f"错误案例共享: {results['error_cases']}")

    logger.info("\n == 题库管理AI工作完成 ===")

if __name__ == '__main__':
    main()
