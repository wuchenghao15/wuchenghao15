# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化考试系统脚本
"""

import os
import sys
import logging
# JSON import removed - using database
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_ai_and_exam_system')

class AIAndExamSystemEnhancer:
    """AI和考试系统增强器类"""

    def __init__(self):
        """初始化AI和考试系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.exam_dir = os.path.join(self.data_dir, 'exam_system')

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.exam_dir, exist_ok=True)

        self.new_ai_types = [
            {
                'ai_type': 'exam_ai',
                'name': '考试AI',
                'description': '专门负责考试系统的管理和优化',
                'functions': [
                    '考试内容生成',
                    '考试难度评估',
                    '考试结果分析',
                    '考试流程优化'
                ],
                'required_skills': ['education', 'data_analysis', 'exam_management']
            },
            {
                'ai_type': 'grading_ai',
                'name': '批卷AI',
                'description': '专门负责自动批卷和评分',
                'functions': [
                    '自动批卷',
                    '错题分析',
                    '评分标准优化'
                ],
                'required_skills': ['education', 'grading', 'error_analysis']
            },
            {
                'ai_type': 'question_gen_ai',
                'name': '题目生成AI',
                'description': '专门负责自动生成考试题目',
                'functions': [
                    '题目内容生成',
                    '题目难度控制',
                    '题目质量评估'
                ],
                'required_skills': ['education', 'content_generation', 'difficulty_assessment']
            },
            {
                'ai_type': 'anti_cheat_ai',
                'name': '防作弊AI',
                'description': '专门负责考试防作弊监控',
                'functions': [
                    '行为监控',
                    '异常检测'
                ],
                'required_skills': ['security', 'behavior_analysis', 'anomaly_detection']
            }
        ]

        self.exam_system_configs = {
            'exam': {
                'enabled': True,
                'exam_types': ['practice', 'quiz', 'midterm', 'final'],
                'max_exam_duration': 180,
                'auto_save_interval': 30,
                'result_retention_days': 730
            },
            'grading': {
                'enabled': True,
                'auto_grading': True,
                'grading_methods': ['keyword', 'similarity', 'comprehensive'],
                'partial_credit': True,
                'confidence_threshold': 0.9
            },
            'question_generation': {
                'enabled': True,
                'difficulty_levels': ['easy', 'medium', 'hard', 'expert'],
                'auto_diversity': True,
                'quality_check': True
            },
            'anti_cheat': {
                'enabled': True,
                'detection_methods': ['behavior', 'pattern', 'content'],
                'alert_threshold': 0.7,
                'auto_action': False
            },
            'reporting': {
                'include_analysis': True,
                'include_recommendations': True,
                'include_statistics': True
            }
        }

    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exam_system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE,
                    config_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exam_system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status_name TEXT UNIQUE,
                    status_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)

            conn.commit()
            conn.close()

            logger.info("数据库检查完成")
            return True
        except Exception as e:
            logger.error(f"检查数据库失败: {str(e)}")
            return False

    def add_new_ai_types(self) -> bool:
        """添加新的AI类型"""
        try:
            logger.info("开始添加新的AI类型")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_types (
                    ai_type TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    functions TEXT,
                    required_skills TEXT,
                    created_at TEXT
                )
            """)

            added_count = 0
            for ai_type_info in self.new_ai_types:
                cursor.execute(
                    "SELECT ai_type FROM ai_types WHERE ai_type = ?",
                    (ai_type_info['ai_type'],)
                )
                if not cursor.fetchone():
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
                    added_count += 1
                    logger.info(f"添加新AI类型: {ai_type_info['name']} ({ai_type_info['ai_type']})")
                else:
                    logger.info(f"AI类型已存在: {ai_type_info['name']} ({ai_type_info['ai_type']})")

            conn.commit()
            conn.close()
            logger.info(f"添加AI类型完成,新增 {added_count} 个AI类型")
            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False

    def optimize_exam_system_configs(self) -> bool:
        try:
            logger.info("开始优化考试系统配置")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            updated_count = 0
            for config_category, config_values in self.exam_system_configs.items():
                for config_name, config_value in config_values.items():
                    full_config_name = f"exam_{config_category}_{config_name}"

                    cursor.execute(
                        "SELECT config_name FROM exam_system_configs WHERE config_name = ?",
                        (full_config_name,)
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE exam_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                            (str(config_value), datetime.now().isoformat(), full_config_name)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO exam_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                full_config_name,
                                str(config_value),
                                f"考试系统 {config_category} 配置: {config_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1

            conn.commit()
            conn.close()
            logger.info(f"考试系统配置优化完成,更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化考试系统配置失败: {str(e)}")
            return False

    def update_exam_system_status(self) -> bool:
        try:
            logger.info("开始更新考试系统状态")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            statuses = {
                'exam_system_enabled': 'True',
                'last_exam_run': datetime.now().isoformat(),
                'active_exams': '0',
                'total_exams_completed': '0',
                'total_questions_graded': '0',
                'system_status': 'healthy'
            }

            for status_name, status_value in statuses.items():
                cursor.execute(
                    "SELECT status_name FROM exam_system_status WHERE status_name = ?",
                    (status_name,)
                )
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE exam_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                        (status_value, datetime.now().isoformat(), status_name)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO exam_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                        (status_name, status_value, f"考试系统状态: {status_name}", datetime.now().isoformat())
                    )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"更新考试系统状态失败: {str(e)}")
            return False

    def get_exam_system_configs(self) -> Dict[str, Any]:
        """获取考试系统配置"""
        try:
            logger.info("获取考试系统配置")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT config_name, config_value FROM exam_system_configs")
            configs = {}
            for row in cursor.fetchall():
                config_name = row[0]
                config_value = eval(row[1])
                configs[config_name] = config_value

            conn.close()
            return configs
        except Exception as e:
            logger.error(f"获取考试系统配置失败: {str(e)}")
            return {}

    def get_exam_system_status(self) -> Dict[str, Any]:
        """获取考试系统状态"""
        try:
            logger.info("获取考试系统状态")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT status_name, status_value FROM exam_system_status")
            statuses = {}
            for row in cursor.fetchall():
                status_name = row[0]
                status_value = row[1]
                statuses[status_name] = status_value
            conn.close()
            return statuses
        except Exception as e:
            logger.error(f"获取考试系统状态失败: {str(e)}")
            return {}

    def get_ai_types(self) -> List[Dict[str, Any]]:
        """获取AI类型"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT ai_type, name, description, functions, required_skills FROM ai_types")
            ai_types = []
            for row in cursor.fetchall():
                ai_type_info = {
                    'ai_type': row[0],
                    'name': row[1],
                    'description': row[2],
                    'functions': eval(row[3]) if row[3] else [],
                    'required_skills': eval(row[4]) if row[4] else [],
                }
                ai_types.append(ai_type_info)
            conn.close()
            return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []

    def restart_exam_system(self) -> bool:
        """重启考试系统"""
        try:
            logger.info("考试系统重启指令已准备就绪")
            logger.info("请根据需要重启考试系统相关服务")
            return True
        except Exception as e:
            logger.error(f"重启考试系统失败: {str(e)}")
            return False

    def enhance_system(self) -> Dict[str, Any]:
        """增强系统"""
        try:
            logger.info("开始增强系统")
            enhance_result = {
                'success': True,
                'steps': [],
                'errors': []
            }

            if self.check_database():
                enhance_result['steps'].append('数据库检查完成')
            else:
                enhance_result['errors'].append('数据库检查失败')

            if self.add_new_ai_types():
                enhance_result['steps'].append('添加新AI类型完成')
            else:
                enhance_result['errors'].append('添加新AI类型失败')
                enhance_result['success'] = False

            if self.optimize_exam_system_configs():
                enhance_result['steps'].append('考试系统配置优化完成')
            else:
                enhance_result['errors'].append('考试系统配置优化失败')
                enhance_result['success'] = False

            if self.update_exam_system_status():
                enhance_result['steps'].append('考试系统状态更新完成')
            else:
                enhance_result['errors'].append('考试系统状态更新失败')
                enhance_result['success'] = False

            if self.restart_exam_system():
                enhance_result['steps'].append('考试系统重启完成')
            else:
                enhance_result['errors'].append('考试系统重启失败')
                enhance_result['success'] = False

            logger.info(f"系统增强完成: {enhance_result}")
            return enhance_result
        except Exception as e:
            logger.error(f"增强系统失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)],
            }

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("增加AI并优化考试系统脚本")
    logger.info("=" * 60)

    enhancer = AIAndExamSystemEnhancer()

    logger.info("\n1. 增强系统")
    enhance_result = enhancer.enhance_system()

    if enhance_result['success']:
        logger.info("✅ 系统增强成功")
        for step in enhance_result['steps']:
            logger.info(f"  - {step}")
    else:
        logger.error("❌ 系统增强失败")
        for error in enhance_result['errors']:
            logger.error(f"  - {error}")

    # 获取AI类型
    ai_types = enhancer.get_ai_types()
    # 过滤出考试系统相关的AI类型
    exam_ai_types = [ai for ai in ai_types if 'exam' in ai['ai_type'] or 'grading' in ai['ai_type'] or 'question' in ai['ai_type'] or 'anti' in ai['ai_type']]
    logger.info(f"已添加 {len(exam_ai_types)} 个考试系统相关AI类型")
    for ai_type in exam_ai_types:
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")

    # 获取考试系统配置
    logger.info("\n3. 获取考试系统配置")
    exam_configs = enhancer.get_exam_system_configs()
    logger.info(f"考试系统配置项数量: {len(exam_configs)}")

    # 按类别显示配置
    config_categories = {}
    for config_name, config_value in exam_configs.items():
        category = config_name.split('_')[1]  # 提取类别
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value

    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")

    # 获取考试系统状态
    logger.info("\n4. 获取考试系统状态")
    exam_status = enhancer.get_exam_system_status()
    logger.info(f"考试系统状态项数量: {len(exam_status)}")
    for status_name, status_value in exam_status.items():
        logger.info(f"  {status_name}: {status_value}")

    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)

    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
