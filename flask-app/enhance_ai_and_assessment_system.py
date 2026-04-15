#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化摸底测试系统脚本
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
logger = logging.getLogger('enhance_ai_and_assessment_system')

class AIAndAssessmentSystemEnhancer:
    """AI和摸底测试系统增强器类"""
    
    def __init__(self):
        """初始化AI和摸底测试系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.assessment_dir = os.path.join(self.data_dir, 'assessment_system')
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.assessment_dir, exist_ok=True)
        
        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'assessment_ai',
                'name': '摸底测试AI',
                'description': '专门负责摸底测试的管理和优化',
                'functions': [
                    '测试内容生成',
                    '测试难度评估',
                    '测试结果分析',
                    '个性化学习建议'
                ],
                'required_skills': ['education', 'data_analysis', 'personalization']
            },
            {
                'ai_type': 'skill_assessment_ai',
                'name': '技能评估AI',
                'description': '专门负责技能评估和分析',
                'functions': [
                    '技能水平评估',
                    '能力差距分析',
                    '技能发展建议',
                    '学习路径规划'
                ],
                'required_skills': ['education', 'skill_analysis', 'personalization']
            },
            {
                'ai_type': 'adaptive_test_ai',
                'name': '自适应测试AI',
                'description': '专门负责自适应测试的管理',
                'functions': [
                    '动态难度调整',
                    '实时能力评估',
                    '个性化测试内容',
                    '测试效率优化'
                ],
                'required_skills': ['education', 'adaptive_learning', 'data_analysis']
            }
        ]
        
        # 摸底测试系统优化配置
        self.assessment_system_configs = {
            'general': {
                'enabled': True,
                'test_types': ['skill_assessment', 'knowledge_test', 'aptitude_test'],
                'max_test_duration': 120,  # 分钟
                'auto_save_interval': 60,  # 秒
                'result_retention_days': 365
            },
            'adaptive_test': {
                'enabled': True,
                'initial_difficulty': 'medium',  # easy, medium, hard
                'difficulty_adjustment_rate': 0.1,
                'minimum_questions': 10,
                'maximum_questions': 50,
                'confidence_threshold': 0.85
            },
            'scoring': {
                'enabled': True,
                'scoring_method': 'weighted',  # weighted, raw, percentile
                'passing_score': 60,
                'skill_levels': {
                    'beginner': 0,
                    'intermediate': 60,
                    'advanced': 80,
                    'expert': 95
                }
            },
            'reporting': {
                'enabled': True,
                'report_types': ['detailed', 'summary', 'comparative'],
                'include_recommendations': True,
                'include_skill_analysis': True,
                'include_progress_tracking': True
            }
        }
        
        logger.info("AI和摸底测试系统增强器初始化完成")
    
    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查摸底测试配置表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE,
                    config_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)
            
            # 检查摸底测试状态表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_system_status (
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
    
    def optimize_assessment_system_configs(self) -> bool:
        """优化摸底测试系统配置"""
        try:
            logger.info("开始优化摸底测试系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for config_category, config_values in self.assessment_system_configs.items():
                for config_name, config_value in config_values.items():
                    full_config_name = f"assessment_{config_category}_{config_name}"
                    
                    # 检查是否已存在
                    cursor.execute(
                        "SELECT config_name FROM assessment_system_configs WHERE config_name = ?",
                        (full_config_name,)
                    )
                    if cursor.fetchone():
                        # 更新配置
                        cursor.execute(
                            "UPDATE assessment_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                            (json.dumps(config_value), datetime.now().isoformat(), full_config_name)
                        )
                    else:
                        # 添加新配置
                        cursor.execute(
                            "INSERT INTO assessment_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                full_config_name,
                                json.dumps(config_value),
                                f"摸底测试系统 {config_category} 配置: {config_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"摸底测试系统配置优化完成，更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化摸底测试系统配置失败: {str(e)}")
            return False
    
    def update_assessment_system_status(self) -> bool:
        """更新摸底测试系统状态"""
        try:
            logger.info("开始更新摸底测试系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新摸底测试系统状态
            statuses = {
                'assessment_system_enabled': 'True',
                'last_test_run': datetime.now().isoformat(),
                'active_tests': '0',
                'total_tests_completed': '0',
                'system_status': 'healthy'
            }
            
            updated_count = 0
            for status_name, status_value in statuses.items():
                # 检查是否已存在
                cursor.execute(
                    "SELECT status_name FROM assessment_system_status WHERE status_name = ?",
                    (status_name,)
                )
                if cursor.fetchone():
                    # 更新状态
                    cursor.execute(
                        "UPDATE assessment_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                        (status_value, datetime.now().isoformat(), status_name)
                    )
                else:
                    # 添加新状态
                    cursor.execute(
                        "INSERT INTO assessment_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                        (
                            status_name,
                            status_value,
                            f"摸底测试系统状态: {status_name}",
                            datetime.now().isoformat()
                        )
                    )
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"摸底测试系统状态更新完成，更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新摸底测试系统状态失败: {str(e)}")
            return False
    
    def get_assessment_system_configs(self) -> Dict[str, Any]:
        """获取摸底测试系统配置"""
        try:
            logger.info("获取摸底测试系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT config_name, config_value FROM assessment_system_configs")
            configs = {}
            for row in cursor.fetchall():
                config_name = row[0]
                config_value = json.loads(row[1])
                configs[config_name] = config_value
            
            conn.close()
            
            return configs
        except Exception as e:
            logger.error(f"获取摸底测试系统配置失败: {str(e)}")
            return {}
    
    def get_assessment_system_status(self) -> Dict[str, Any]:
        """获取摸底测试系统状态"""
        try:
            logger.info("获取摸底测试系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT status_name, status_value FROM assessment_system_status")
            statuses = {}
            for row in cursor.fetchall():
                status_name = row[0]
                status_value = row[1]
                statuses[status_name] = status_value
            
            conn.close()
            
            return statuses
        except Exception as e:
            logger.error(f"获取摸底测试系统状态失败: {str(e)}")
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
    
    def restart_assessment_system(self) -> bool:
        """重启摸底测试系统"""
        try:
            logger.info("开始重启摸底测试系统")
            
            # 这里可以添加实际的摸底测试系统重启逻辑
            # 例如重启相关服务等
            
            logger.info("摸底测试系统重启指令已准备就绪")
            logger.info("请根据需要重启摸底测试系统相关服务")
            
            return True
        except Exception as e:
            logger.error(f"重启摸底测试系统失败: {str(e)}")
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
            
            # 步骤3: 优化摸底测试系统配置
            if self.optimize_assessment_system_configs():
                enhance_result['steps'].append('摸底测试系统配置优化完成')
            else:
                enhance_result['errors'].append('摸底测试系统配置优化失败')
                enhance_result['success'] = False
            
            # 步骤4: 更新摸底测试系统状态
            if self.update_assessment_system_status():
                enhance_result['steps'].append('摸底测试系统状态更新完成')
            else:
                enhance_result['errors'].append('摸底测试系统状态更新失败')
                enhance_result['success'] = False
            
            # 步骤5: 重启摸底测试系统
            if self.restart_assessment_system():
                enhance_result['steps'].append('摸底测试系统重启指令已准备')
            else:
                enhance_result['errors'].append('摸底测试系统重启失败')
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
    logger.info("增加AI并优化摸底测试系统脚本")
    logger.info("=" * 60)
    
    enhancer = AIAndAssessmentSystemEnhancer()
    
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
    # 过滤出摸底测试相关的AI类型
    assessment_ai_types = [ai for ai in ai_types if 'assessment' in ai['ai_type'] or 'test' in ai['ai_type']]
    logger.info(f"已添加 {len(assessment_ai_types)} 个摸底测试相关AI类型")
    for ai_type in assessment_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")
    
    # 获取摸底测试系统配置
    logger.info("\n3. 获取摸底测试系统配置")
    assessment_configs = enhancer.get_assessment_system_configs()
    logger.info(f"摸底测试系统配置项数量: {len(assessment_configs)}")
    
    # 按类别显示配置
    config_categories = {}
    for config_name, config_value in assessment_configs.items():
        category = config_name.split('_')[1]  # 提取类别
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value
    
    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")
    
    # 获取摸底测试系统状态
    logger.info("\n4. 获取摸底测试系统状态")
    assessment_status = enhancer.get_assessment_system_status()
    logger.info(f"摸底测试系统状态项数量: {len(assessment_status)}")
    for status_name, status_value in assessment_status.items():
        logger.info(f"  {status_name}: {status_value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)
    
    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
