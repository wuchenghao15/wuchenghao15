#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化评分系统脚本
"""

import os
import sys
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_ai_and_grading_system')

class AIAndGradingSystemEnhancer:
    """AI和评分系统增强器类"""
    
    def __init__(self):
        """初始化AI和评分系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.grading_dir = os.path.join(self.data_dir, 'grading_system')
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.grading_dir, exist_ok=True)
        
        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'auto_grading_ai',
                'name': '自动评分AI',
                'description': '专门负责自动评分和评估',
                'functions': [
                    '客观题自动评分',
                    '主观题智能评分',
                    '评分一致性检查',
                    '评分效率优化'
                ],
                'required_skills': ['grading', 'nlp', 'consistency_check']
            },
            {
                'ai_type': 'essay_grading_ai',
                'name': '作文评分AI',
                'description': '专门负责作文和主观题评分',
                'functions': [
                    '内容分析',
                    '结构评估',
                    '语言表达评分',
                    '创意和深度评估'
                ],
                'required_skills': ['nlp', 'content_analysis', 'language_assessment']
            },
            {
                'ai_type': 'feedback_generation_ai',
                'name': '反馈生成AI',
                'description': '专门负责生成个性化评分反馈',
                'functions': [
                    '个性化反馈生成',
                    '改进建议提供',
                    '学习资源推荐',
                    '进步追踪分析'
                ],
                'required_skills': ['personalization', 'feedback_generation', 'learning_analysis']
            },
            {
                'ai_type': 'grading_quality_control_ai',
                'name': '评分质量控制AI',
                'description': '专门负责评分质量控制和监督',
                'functions': [
                    '评分异常检测',
                    '评分标准执行检查',
                    '评分偏差修正',
                    '评分质量报告生成'
                ],
                'required_skills': ['quality_control', 'anomaly_detection', 'deviation_correction']
            }
        ]
        
        # 评分系统优化配置
        self.grading_system_configs = {
            'general': {
                'enabled': True,
                'grading_methods': ['auto', 'semi_auto', 'manual'],
                'auto_grading_threshold': 0.8,
                're_grading_enabled': True,
                're_grading_limit': 3,
                'score_precision': 2
            },
            'objective_grading': {
                'enabled': True,
                'strict_mode': True,
                'partial_credit': True,
                'answer_tolerance': 0,
                'case_sensitive': False
            },
            'subjective_grading': {
                'enabled': True,
                'ai_assisted': True,
                'grading_criteria': ['content', 'structure', 'language', 'creativity'],
                'criteria_weights': [0.4, 0.25, 0.25, 0.1],
                'minimum_word_count': 50,
                'plagiarism_check': True
            },
            'feedback': {
                'enabled': True,
                'auto_feedback': True,
                'feedback_types': ['strengths', 'weaknesses', 'suggestions'],
                'include_resources': True,
                'personalized': True,
                'constructive_criticism': True
            },
            'quality_control': {
                'enabled': True,
                'anomaly_detection': True,
                'consistency_check': True,
                'bias_detection': True,
                'random_audit': True,
                'audit_rate': 0.1
            },
            'reporting': {
                'enabled': True,
                'report_types': ['individual', 'class', 'comparative'],
                'include_statistics': True,
                'include_trends': True,
                'include_comparisons': True,
                'export_formats': ['pdf', 'excel', 'json']
            }
        }
        
        logger.info("AI和评分系统增强器初始化完成")
    
    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查评分系统配置表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grading_system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE,
                    config_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)
            
            # 检查评分系统状态表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grading_system_status (
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
                if not cursor.fetchone():
                    # 添加新AI类型
                    cursor.execute(
                        "INSERT INTO ai_types (ai_type, name, description, functions, required_skills, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            ai_type_info['ai_type'],
                            ai_type_info['name'],
                            ai_type_info['description'],
                            json.dumps(ai_type_info['functions']),
                            json.dumps(ai_type_info['required_skills']),
                            datetime.now().isoformat()
                        )
                    )
                    added_count += 1
                    logger.info(f"添加新AI类型: {ai_type_info['name']} ({ai_type_info['ai_type']})")
                else:
                    logger.info(f"AI类型已存在: {ai_type_info['name']} ({ai_type_info['ai_type']})")
            
            conn.commit()
            conn.close()
            
            logger.info(f"添加AI类型完成，新增 {added_count} 个AI类型")
            return True
        except Exception as e:
            logger.error(f"添加新AI类型失败: {str(e)}")
            return False
    
    def optimize_grading_system_configs(self) -> bool:
        """优化评分系统配置"""
        try:
            logger.info("开始优化评分系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for config_category, config_values in self.grading_system_configs.items():
                for config_name, config_value in config_values.items():
                    full_config_name = f"grading_{config_category}_{config_name}"
                    
                    # 检查是否已存在
                    cursor.execute(
                        "SELECT config_name FROM grading_system_configs WHERE config_name = ?",
                        (full_config_name,)
                    )
                    if cursor.fetchone():
                        # 更新配置
                        cursor.execute(
                            "UPDATE grading_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                            (json.dumps(config_value), datetime.now().isoformat(), full_config_name)
                        )
                    else:
                        # 添加新配置
                        cursor.execute(
                            "INSERT INTO grading_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                full_config_name,
                                json.dumps(config_value),
                                f"评分系统 {config_category} 配置: {config_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"评分系统配置优化完成，更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化评分系统配置失败: {str(e)}")
            return False
    
    def update_grading_system_status(self) -> bool:
        """更新评分系统状态"""
        try:
            logger.info("开始更新评分系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新评分系统状态
            statuses = {
                'grading_system_enabled': 'True',
                'last_grading_run': datetime.now().isoformat(),
                'active_gradings': '0',
                'total_gradings_completed': '0',
                'total_feedback_generated': '0',
                'quality_checks_passed': '0',
                'system_status': 'healthy'
            }
            
            updated_count = 0
            for status_name, status_value in statuses.items():
                # 检查是否已存在
                cursor.execute(
                    "SELECT status_name FROM grading_system_status WHERE status_name = ?",
                    (status_name,)
                )
                if cursor.fetchone():
                    # 更新状态
                    cursor.execute(
                        "UPDATE grading_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                        (status_value, datetime.now().isoformat(), status_name)
                    )
                else:
                    # 添加新状态
                    cursor.execute(
                        "INSERT INTO grading_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                        (
                            status_name,
                            status_value,
                            f"评分系统状态: {status_name}",
                            datetime.now().isoformat()
                        )
                    )
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"评分系统状态更新完成，更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新评分系统状态失败: {str(e)}")
            return False
    
    def get_grading_system_configs(self) -> Dict[str, Any]:
        """获取评分系统配置"""
        try:
            logger.info("获取评分系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT config_name, config_value FROM grading_system_configs")
            configs = {}
            for row in cursor.fetchall():
                config_name = row[0]
                config_value = json.loads(row[1])
                configs[config_name] = config_value
            
            conn.close()
            
            return configs
        except Exception as e:
            logger.error(f"获取评分系统配置失败: {str(e)}")
            return {}
    
    def get_grading_system_status(self) -> Dict[str, Any]:
        """获取评分系统状态"""
        try:
            logger.info("获取评分系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT status_name, status_value FROM grading_system_status")
            statuses = {}
            for row in cursor.fetchall():
                status_name = row[0]
                status_value = row[1]
                statuses[status_name] = status_value
            
            conn.close()
            
            return statuses
        except Exception as e:
            logger.error(f"获取评分系统状态失败: {str(e)}")
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
                    'functions': json.loads(row[3]),
                    'required_skills': json.loads(row[4]),
                    'created_at': row[5]
                }
                ai_types.append(ai_type_info)
            
            conn.close()
            
            return ai_types
        except Exception as e:
            logger.error(f"获取AI类型失败: {str(e)}")
            return []
    
    def restart_grading_system(self) -> bool:
        """重启评分系统"""
        try:
            logger.info("开始重启评分系统")
            
            # 这里可以添加实际的评分系统重启逻辑
            # 例如重启相关服务等
            
            logger.info("评分系统重启指令已准备就绪")
            logger.info("请根据需要重启评分系统相关服务")
            
            return True
        except Exception as e:
            logger.error(f"重启评分系统失败: {str(e)}")
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
                enhance_result['errors'].append('数据库检查失败')
                enhance_result['success'] = False
            
            # 步骤2: 添加新AI类型
            if self.add_new_ai_types():
                enhance_result['steps'].append('添加新AI类型完成')
            else:
                enhance_result['errors'].append('添加新AI类型失败')
                enhance_result['success'] = False
            
            # 步骤3: 优化评分系统配置
            if self.optimize_grading_system_configs():
                enhance_result['steps'].append('评分系统配置优化完成')
            else:
                enhance_result['errors'].append('评分系统配置优化失败')
                enhance_result['success'] = False
            
            # 步骤4: 更新评分系统状态
            if self.update_grading_system_status():
                enhance_result['steps'].append('评分系统状态更新完成')
            else:
                enhance_result['errors'].append('评分系统状态更新失败')
                enhance_result['success'] = False
            
            # 步骤5: 重启评分系统
            if self.restart_grading_system():
                enhance_result['steps'].append('评分系统重启指令已准备')
            else:
                enhance_result['errors'].append('评分系统重启失败')
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
    """主函数"""
    logger.info("=" * 60)
    logger.info("增加AI并优化评分系统脚本")
    logger.info("=" * 60)
    
    enhancer = AIAndGradingSystemEnhancer()
    
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
    # 过滤出评分系统相关的AI类型
    grading_ai_types = [ai for ai in ai_types if 'grading' in ai['ai_type'] or 'essay' in ai['ai_type'] or 'feedback' in ai['ai_type'] or 'quality' in ai['ai_type']]
    logger.info(f"已添加 {len(grading_ai_types)} 个评分系统相关AI类型")
    for ai_type in grading_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")
    
    # 获取评分系统配置
    logger.info("\n3. 获取评分系统配置")
    grading_configs = enhancer.get_grading_system_configs()
    logger.info(f"评分系统配置项数量: {len(grading_configs)}")
    
    # 按类别显示配置
    config_categories = {}
    for config_name, config_value in grading_configs.items():
        category = config_name.split('_')[1]  # 提取类别
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value
    
    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")
    
    # 获取评分系统状态
    logger.info("\n4. 获取评分系统状态")
    grading_status = enhancer.get_grading_system_status()
    logger.info(f"评分系统状态项数量: {len(grading_status)}")
    for status_name, status_value in grading_status.items():
        logger.info(f"  {status_name}: {status_value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)
    
    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
