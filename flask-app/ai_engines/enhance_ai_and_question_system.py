# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化出题系统脚本
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_ai_and_question_system')


class AIAndQuestionSystemEnhancer:
    """AI和出题系统增强器类"""

    def __init__(self):
        """初始化AI和出题系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.question_dir = os.path.join(self.data_dir, 'question_system')

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.question_dir, exist_ok=True)

        self.new_ai_types = [
            {
                'ai_type': 'question_generation_ai',
                'name': '题目生成AI',
                'description': '专门负责自动生成各种类型的题目',
                'functions': [
                    '题目内容生成',
                    '题目难度控制',
                    '题目类型多样化',
                    '题目质量评估'
                ],
                'required_skills': ['content_generation', 'difficulty_control', 'quality_assessment']
            },
            {
                'ai_type': 'question_management_ai',
                'name': '题目管理AI',
                'description': '专门负责题目的管理和维护',
                'functions': [
                    '题目分类管理',
                    '题目版本控制',
                    '题目使用统计'
                ],
                'required_skills': ['question_management', 'category_management', 'statistics']
            },
            {
                'ai_type': 'question_analysis_ai',
                'name': '题目分析AI',
                'description': '专门负责题目的分析和评估',
                'functions': [
                    '题目难度分析',
                    '题目区分度评估',
                    '题目使用效果评估'
                ],
                'required_skills': ['question_analysis', 'difficulty_assessment', 'effectiveness_evaluation']
            },
            {
                'ai_type': 'question_adaptation_ai',
                'name': '题目适配AI',
                'description': '专门负责题目的个性化适配',
                'functions': [
                    '个性化题目推荐',
                    '学习水平适配',
                    '自适应学习支持'
                ],
                'required_skills': ['personalization', 'adaptation', 'recommendation']
            },
            {
                'ai_type': 'question_bank_ai',
                'name': '题库管理AI',
                'description': '专门负责题库的管理和优化',
                'functions': [
                    '题库内容扩充',
                    '题库质量控制',
                    '题库检索优化'
                ],
                'required_skills': ['bank_management', 'content_optimization', 'retrieval_optimization']
            }
        ]

        self.question_system_configs = {
            'general': {
                'enabled': True,
                'auto_backup': True,
                'backup_frequency': 'daily',
                'retention_period': 365,
                'compression': True
            },
            'question_generation': {
                'enabled': True,
                'question_types': ['single_choice', 'multiple_choice', 'true_false', 'short_answer', 'essay'],
                'difficulty_levels': ['easy', 'medium', 'hard', 'expert'],
                'auto_generation': True,
                'quality_check': True,
                'diversity_control': True,
                'generation_timeout': 30
            },
            'question_management': {
                'enabled': True,
                'categories': ['math', 'science', 'language', 'history', 'general'],
                'version_control': True,
                'usage_tracking': True,
                'access_control': True,
                'audit_log': True
            },
            'question_analysis': {
                'enabled': True,
                'analysis_methods': ['difficulty', 'discrimination', 'quality', 'effectiveness'],
                'analysis_frequency': 'weekly',
                'report_generation': True,
                'recommendation_system': True
            },
            'question_adaptation': {
                'enabled': True,
                'user_profiling': True,
                'learning_path_integration': True,
                'feedback_integration': True
            },
            'question_bank': {
                'enabled': True,
                'bank_structure': ['category', 'difficulty', 'topic', 'skill'],
                'content_expansion': True,
                'suggestion_system': True
            },
            'reporting': {
                'enabled': True,
                'report_types': ['question_analysis', 'bank_analysis', 'usage_statistics', 'performance_trends'],
                'include_statistics': True,
                'include_recommendations': True
            }
        }

        logger.info("AI和出题系统增强器初始化完成")

    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS question_system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT UNIQUE,
                config_value TEXT,
                description TEXT,
                updated_at TEXT
                )""")

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS question_system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_name TEXT UNIQUE,
                status_value TEXT,
                description TEXT,
                updated_at TEXT
                )""")

                conn.commit()

            logger.info("数据库检查完成")
            return True
        except Exception as e:
            logger.error(f"检查数据库失败: {str(e)}")
            return False

    def add_new_ai_types(self) -> bool:
        """添加新的AI类型"""
        try:
            logger.info("开始添加新的AI类型")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_types (
                ai_type TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                functions TEXT,
                required_skills TEXT,
                created_at TEXT
                )""")

                added_count = 0
                for ai_type_info in self.new_ai_types:
                    cursor.execute(
                        "SELECT ai_type FROM ai_types WHERE ai_type = ?",
                        (ai_type_info['ai_type'],)
                    )
                    if cursor.fetchone():
                        logger.info(f"AI类型已存在: {ai_type_info['name']} ({ai_type_info['ai_type']})")
                        continue

                    cursor.execute(
                        "INSERT INTO ai_types (ai_type, name, description, functions, required_skills, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            ai_type_info['ai_type'],
                            ai_type_info['name'],
                            ai_type_info['description'],
                            str(ai_type_info['functions']),
                            str(ai_type_info['required_skills']),
                            datetime.now().isoformat()
                        )
                    )
                    logger.info(f"添加新AI类型: {ai_type_info['name']} ({ai_type_info['ai_type']})")
                    added_count += 1

                conn.commit()

            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False

    def optimize_question_system_configs(self) -> bool:
        """优化出题系统配置"""
        try:
            logger.info("开始优化出题系统配置")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                updated_count = 0
                for config_category, config_values in self.question_system_configs.items():
                    for config_name, config_value in config_values.items():
                        full_config_name = f"question_{config_category}_{config_name}"

                        cursor.execute(
                            "SELECT config_name FROM question_system_configs WHERE config_name = ?",
                            (full_config_name,)
                        )
                        if cursor.fetchone():
                            cursor.execute(
                                "UPDATE question_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                                (str(config_value), datetime.now().isoformat(), full_config_name)
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO question_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                                (
                                    full_config_name,
                                    str(config_value),
                                    f"出题系统 {config_category} 配置: {config_name}",
                                    datetime.now().isoformat()
                                )
                            )
                        updated_count += 1

                conn.commit()

            logger.info(f"出题系统配置优化完成,更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化出题系统配置失败: {str(e)}")
            return False

    def update_question_system_status(self) -> bool:
        """更新出题系统状态"""
        try:
            logger.info("开始更新出题系统状态")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                statuses = {
                    'question_system_enabled': 'True',
                    'last_analysis_run': datetime.now().isoformat(),
                    'total_questions': '0',
                    'questions_generated': '0',
                    'questions_analyzed': '0',
                    'active_generations': '0',
                    'system_status': 'healthy'
                }

                updated_count = 0
                for status_name, status_value in statuses.items():
                    cursor.execute(
                        "SELECT status_name FROM question_system_status WHERE status_name = ?",
                        (status_name,)
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE question_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                            (status_value, datetime.now().isoformat(), status_name)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO question_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                status_name,
                                status_value,
                                f"出题系统状态: {status_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1

                conn.commit()

            logger.info(f"出题系统状态更新完成,更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新出题系统状态失败: {str(e)}")
            return False

    def get_question_system_configs(self) -> Dict[str, Any]:
        """获取出题系统配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_name, config_value FROM question_system_configs")
                configs = {}
                for row in cursor.fetchall():
                    config_name = row[0]
                    config_value = row[1]
                    configs[config_name] = config_value
                return configs
        except Exception as e:
            logger.error(f"获取出题系统配置失败: {str(e)}")
            return {}

    def get_question_system_status(self) -> Dict[str, Any]:
        """获取出题系统状态"""
        try:
            logger.info("获取出题系统状态")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT status_name, status_value FROM question_system_status")
                statuses = {}
                for row in cursor.fetchall():
                    status_name = row[0]
                    status_value = row[1]
                    statuses[status_name] = status_value

                return statuses
        except Exception as e:
            logger.error(f"获取出题系统状态失败: {str(e)}")
            return {}

    def get_ai_types(self) -> List[Dict[str, Any]]:
        """获取AI类型"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ai_types")
                ai_types = []
                for row in cursor.fetchall():
                    ai_type_info = {
                        'ai_type': row[0],
                        'name': row[1],
                        'description': row[2],
                        'functions': row[3],
                        'required_skills': row[4],
                        'created_at': row[5]
                    }
                    ai_types.append(ai_type_info)
                return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []

    def restart_question_system(self) -> bool:
        """重启出题系统"""
        try:
            logger.info("出题系统重启指令已准备就绪")
            logger.info("请根据需要重启出题系统相关服务")
            return True
        except Exception as e:
            logger.error(f"重启出题系统失败: {str(e)}")
            return False

    def enhance_system(self) -> Dict[str, Any]:
        """增强系统"""
        try:
            enhance_result = {
                'success': True,
                'steps': [],
                'errors': []
            }

            if self.check_database():
                enhance_result['steps'].append('数据库检查完成')
            else:
                enhance_result['errors'].append('数据库检查失败')
                enhance_result['success'] = False

            if self.add_new_ai_types():
                enhance_result['steps'].append('新AI类型添加完成')
            else:
                enhance_result['errors'].append('添加新AI类型失败')
                enhance_result['success'] = False

            if self.optimize_question_system_configs():
                enhance_result['steps'].append('出题系统配置优化完成')
            else:
                enhance_result['errors'].append('出题系统配置优化失败')
                enhance_result['success'] = False

            if self.update_question_system_status():
                enhance_result['steps'].append('出题系统状态更新完成')
            else:
                enhance_result['errors'].append('出题系统状态更新失败')
                enhance_result['success'] = False

            if self.restart_question_system():
                enhance_result['steps'].append('出题系统重启指令已准备')
            else:
                enhance_result['errors'].append('出题系统重启失败')
                enhance_result['success'] = False

            logger.info(f"系统增强完成: {enhance_result}")
            return enhance_result
        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)],
                'steps': []
            }


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("增加AI并优化出题系统脚本")
    logger.info("=" * 60)
    enhancer = AIAndQuestionSystemEnhancer()

    logger.info("\n1. 增强系统")
    enhance_result = enhancer.enhance_system()

    if enhance_result['success']:
        logger.info("系统增强成功")
        for step in enhance_result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("系统增强失败")
        for error in enhance_result['errors']:
            logger.error(f"  - {error}")

    logger.info("\n2. 获取AI类型")
    ai_types = enhancer.get_ai_types()
    question_ai_types = [ai for ai in ai_types if 'question' in ai['ai_type'] or 'bank' in ai['ai_type'] or 'generation' in ai['ai_type'] or 'management' in ai['ai_type'] or 'analysis' in ai['ai_type'] or 'adaptation' in ai['ai_type']]
    logger.info(f"已添加 {len(question_ai_types)} 个出题系统相关AI类型")
    for ai_type in question_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")

    logger.info("\n3. 获取出题系统配置")
    question_configs = enhancer.get_question_system_configs()
    logger.info(f"出题系统配置项数量: {len(question_configs)}")

    logger.info("\n4. 获取出题系统状态")
    question_status = enhancer.get_question_system_status()
    logger.info(f"出题系统状态项数量: {len(question_status)}")
    for status_name, status_value in question_status.items():
        logger.info(f"  {status_name}: {status_value}")

    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)

    return 0 if enhance_result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
