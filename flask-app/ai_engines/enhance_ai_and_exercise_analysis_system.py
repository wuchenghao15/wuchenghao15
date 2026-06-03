# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化评习题考点错题分析知识重点联系讲解系统脚本
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
logger = logging.getLogger('enhance_ai_and_exercise_analysis_system')

class AIAndExerciseAnalysisSystemEnhancer:
    """AI和习题分析系统增强器类"""

    def __init__(self):
        """初始化AI和习题分析系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.exercise_dir = os.path.join(self.data_dir, 'exercise_analysis_system')

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.exercise_dir, exist_ok=True)

        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'exercise_grading_ai',
                'name': '习题评分AI',
                'description': '专门负责习题的批改和评分',
                'functions': [
                    '客观题自动批改',
                    '主观题智能评分',
                    '评分标准执行',
                    '评分效率优化'
                ],
                'required_skills': ['grading', 'exercise_analysis', 'consistency_check']
            },
            {
                'name': '考点分析AI',
                'description': '专门负责考点的识别和分析',
                'functions': [
                    '考点自动识别',
                    '考点重要性评估',
                    '考点分布优化'
                ],
                'required_skills': ['data_analysis', 'pattern_recognition', 'importance_assessment']
            },
            {
                'ai_type': 'error_analysis_ai',
                'name': '错题分析AI',
                'description': '专门负责错题的深度分析',
                'functions': [
                    '错题自动归类',
                    '错误模式识别',
                    '错题统计报告'
                ],
                'required_skills': ['error_analysis', 'pattern_recognition', 'statistical_analysis']
            },
            {
                'ai_type': 'knowledge_focus_ai',
                'name': '知识重点AI',
                'description': '专门负责知识重点的提炼和强调',
                'functions': [
                    '知识重点自动提炼',
                    '重点内容强调',
                    '重点结构优化'
                ],
                'required_skills': ['content_analysis', 'knowledge_extraction', 'structure_optimization']
            },
            {
                'ai_type': 'knowledge_connection_ai',
                'name': '知识联系讲解AI',
                'description': '专门负责知识之间的联系和讲解',
                'functions': [
                    '关联知识讲解',
                    '知识网络构建',
                    '综合知识解析'
                ],
                'required_skills': ['knowledge_connection', 'explanation_generation', 'network_construction']
            }
        ]

        # 习题分析系统优化配置
        self.exercise_analysis_system_configs = {
            'general': {
                'enabled': True,
                'auto_analysis': True,
                'analysis_depth': 'comprehensive',
                'result_retention_days': 730
            },
            'exercise_grading': {
                'enabled': True,
                'auto_grading': True,
                'grading_methods': ['auto', 'semi_auto', 'manual'],
                'partial_credit': True,
                'grading_threshold': 0.8,
                'feedback_automation': True
            },
            'exam_point_analysis': {
                'enabled': True,
                'auto_detection': True,
                'analysis_methods': ['frequency', 'importance', 'difficulty'],
                'point_highlighting': True,
                'update_frequency': 'weekly'
            },
            'error_question_analysis': {
                'enabled': True,
                'error_categories': ['concept', 'calculation', 'application', 'careless'],
                'statistical_report': True,
                'suggestion_generation': True
            },
            'knowledge_focus': {
                'enabled': True,
                'auto_extraction': True,
                'structure_visualization': True,
                'priority_levels': 5
            },
            'knowledge_connection': {
                'enabled': True,
                'auto_detection': True,
                'connection_types': ['prerequisite', 'related', 'advanced', 'application'],
                'comprehensive_analysis': True
            },
            'reporting': {
                'report_types': ['individual', 'class', 'comparative', 'comprehensive'],
                'include_statistics': True,
                'include_visualization': True,
            }
        }

        logger.info("AI和习题分析系统增强器初始化完成")

    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            # 连接数据库
            with sqlite3.connect(self.db_path) as conn:
                conn_cursor = conn.cursor()
                cursor = conn.cursor()
                
                # 检查习题分析系统配置表是否存在
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS exercise_analysis_system_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT UNIQUE,
                config_value TEXT,
                description TEXT,
                updated_at TEXT
                )
                """)

                # 检查习题分析系统状态表是否存在
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS exercise_analysis_system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_name TEXT UNIQUE,
                status_value TEXT,
                description TEXT,
                updated_at TEXT
                )
                """)
                
                conn.commit()
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

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 确保ai_types表存在
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
                # 检查是否已存在
                cursor.execute(
                    "SELECT ai_type FROM ai_types WHERE ai_type = ?",
                    (ai_type_info['ai_type'],)
                )
                result = cursor.fetchone()
                if result is None:
                    # 添加新AI类型
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

            logger.info(f"添加AI类型完成,新增 {added_count} 个AI类型")
            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False

    def optimize_exercise_analysis_system_configs(self) -> bool:
        """优化习题分析系统配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updated_count = 0
                for config_category, config_values in self.exercise_analysis_system_configs.items():
                    for config_name, config_value in config_values.items():
                        full_config_name = f"{config_category}_{config_name}"
                        
                        # 检查是否已存在
                        cursor.execute(
                            "SELECT config_name FROM exercise_analysis_system_configs WHERE config_name = ?",
                            (full_config_name,)
                        )
                        result = cursor.fetchone()
                        if result:
                            # 更新配置
                            cursor.execute(
                                "UPDATE exercise_analysis_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                                (str(config_value), datetime.now().isoformat(), full_config_name)
                            )
                        else:
                            # 添加新配置
                            cursor.execute(
                                "INSERT INTO exercise_analysis_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                                (
                                    full_config_name,
                                    str(config_value),
                                    f"习题分析系统 {config_category} 配置: {config_name}",
                                    datetime.now().isoformat()
                                )
                            )
                        updated_count += 1
                
                conn.commit()

            logger.info(f"习题分析系统配置优化完成,更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化习题分析系统配置失败: {str(e)}")
            return False
    def update_exercise_analysis_system_status(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 更新习题分析系统状态
                statuses = {
                    'exercise_analysis_system_enabled': 'True',
                    'active_analyses': '0',
                    'total_exercises_graded': '0',
                    'total_exam_points_analyzed': '0',
                    'total_error_questions_analyzed': '0',
                    'total_knowledge_connections_identified': '0',
                    'system_status': 'healthy'
                }
                
                updated_count = 0
                for status_name, status_value in statuses.items():
                    # 检查是否已存在
                    cursor.execute(
                        "SELECT status_name FROM exercise_analysis_system_status WHERE status_name = ?",
                        (status_name,)
                    )
                    result = cursor.fetchone()
                    if result:
                        cursor.execute(
                            "UPDATE exercise_analysis_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                            (status_value, datetime.now().isoformat(), status_name)
                        )
                    else:
                        # 添加新状态
                        cursor.execute(
                            "INSERT INTO exercise_analysis_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                status_name,
                                status_value,
                                f"习题分析系统状态: {status_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1
                conn.commit()
            logger.info(f"习题分析系统状态更新完成,更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新习题分析系统状态失败: {str(e)}")
            return False

    def get_exercise_analysis_system_configs(self) -> Dict[str, Any]:
        """获取习题分析系统配置"""
        try:
            logger.info("获取习题分析系统配置")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_name, config_value FROM exercise_analysis_system_configs")
                configs = {}
                for row in cursor.fetchall():
                    config_name = row[0]
                    config_value = eval(row[1])
                    configs[config_name] = config_value

            return configs
        except Exception as e:
            logger.error(f"获取习题分析系统配置失败: {str(e)}")
            return {}

    def get_exercise_analysis_system_status(self) -> Dict[str, Any]:
        """获取习题分析系统状态"""
        try:
            logger.info("获取习题分析系统状态")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT status_name, status_value FROM exercise_analysis_system_status")
                statuses = {}
                for row in cursor.fetchall():
                    status_name = row[0]
                    status_value = row[1]
                    statuses[status_name] = status_value
                

        except Exception as e:
            logger.error(f"获取习题分析系统状态失败: {str(e)}")
            return {}

    def get_ai_types(self) -> List[Dict[str, Any]]:
        """获取AI类型"""
        try:
            logger.info("获取AI类型")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM ai_types")
            ai_types = []
            for row in cursor.fetchall():
                ai_type_info = {
                    'ai_type': row[0],
                    'name': row[1],
                    'description': row[2],
                    'functions': eval(row[3]),
                    'required_skills': eval(row[4]),
                    'created_at': row[5]
                }
                ai_types.append(ai_type_info)

            conn.close()

            return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []

    def restart_exercise_analysis_system(self) -> bool:
        """重启习题分析系统"""
        try:
            logger.info("习题分析系统重启指令已准备就绪")
            logger.info("请根据需要重启习题分析系统相关服务")
            return True
        except Exception as e:
            logger.error(f"重启习题分析系统失败: {str(e)}")
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
            # 步骤1: 检查数据库
            if self.check_database():
                enhance_result['steps'].append('数据库检查完成')
            else:
                enhance_result['success'] = False
                enhance_result['errors'].append('数据库检查失败')

            # 步骤2: 添加新AI类型
            if self.add_new_ai_types():
                enhance_result['steps'].append('添加新AI类型完成')
            else:
                enhance_result['success'] = False
                enhance_result['errors'].append('添加新AI类型失败')

            # 步骤3: 优化习题分析系统配置
            if self.optimize_exercise_analysis_system_configs():
                enhance_result['steps'].append('习题分析系统配置优化完成')
            else:
                enhance_result['errors'].append('习题分析系统配置优化失败')
                enhance_result['success'] = False

            # 步骤4: 更新习题分析系统状态
            if self.update_exercise_analysis_system_status():
                enhance_result['steps'].append('习题分析系统状态更新完成')
            else:
                enhance_result['errors'].append('习题分析系统状态更新失败')
                enhance_result['success'] = False

            # 步骤5: 重启习题分析系统
            if self.restart_exercise_analysis_system():
                enhance_result['steps'].append('习题分析系统重启指令已准备')
            else:
                enhance_result['errors'].append('习题分析系统重启失败')
                enhance_result['success'] = False
            logger.info(f"系统增强完成: {enhance_result}")
            return enhance_result
        except Exception as e:
            logger.error(f"增强系统失败: {str(e)}")
            return {
                'success': False,
                'errors': [str(e)],
                'steps': []
            }

def main():
    logger.info("=" * 60)
    logger.info("增加AI并优化评习题考点错题分析知识重点联系讲解系统脚本")
    logger.info("=" * 60)

    enhancer = AIAndExerciseAnalysisSystemEnhancer()
    # 增强系统
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
    logger.info("\n2. 获取AI类型")
    ai_types = enhancer.get_ai_types()
    # 过滤出习题分析系统相关的AI类型
    exercise_ai_types = [t for t in ai_types if 'exercise' in t['ai_type'].lower()]
    logger.info(f"已添加 {len(exercise_ai_types)} 个习题分析系统相关AI类型")
    for ai_type in exercise_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")
    # 获取习题分析系统配置
    exercise_analysis_configs = enhancer.get_exercise_analysis_system_configs()
    logger.info(f"习题分析系统配置项数量: {len(exercise_analysis_configs)}")

    # 按类别显示配置
    config_categories = {}
    for config_name, config_value in exercise_analysis_configs.items():
        category = config_name.split('_')[2]  # 提取类别
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value

    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")

    # 获取习题分析系统状态
    logger.info("\n4. 获取习题分析系统状态")
    exercise_analysis_status = enhancer.get_exercise_analysis_system_status()
    logger.info(f"习题分析系统状态项数量: {len(exercise_analysis_status)}")
    for status_name, status_value in exercise_analysis_status.items():
        logger.info(f"  {status_name}: {status_value}")

    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)

    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
