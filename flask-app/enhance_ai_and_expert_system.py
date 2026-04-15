#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增加AI并优化专家系统脚本
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
logger = logging.getLogger('enhance_ai_and_expert_system')

class AIAndExpertSystemEnhancer:
    """AI和专家系统增强器类"""
    
    def __init__(self):
        """初始化AI和专家系统增强器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.db_path = os.path.join(self.data_dir, 'mtscos_ai_project.db')
        self.expert_dir = os.path.join(self.data_dir, 'expert_system')
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.expert_dir, exist_ok=True)
        
        # 新AI类型定义
        self.new_ai_types = [
            {
                'ai_type': 'expert_management_ai',
                'name': '专家管理AI',
                'description': '专门负责专家信息和资源管理',
                'functions': [
                    '专家档案管理',
                    '专家领域分类',
                    '专家匹配推荐',
                    '专家资源协调'
                ],
                'required_skills': ['expert_management', 'resource_coordination', 'matching_algorithm']
            },
            {
                'ai_type': 'expert_consultation_ai',
                'name': '专家咨询AI',
                'description': '专门提供专家咨询和解答',
                'functions': [
                    '问题分类与路由',
                    '专家匹配',
                    '咨询过程管理',
                    '咨询结果评估'
                ],
                'required_skills': ['consultation_management', 'problem_classification', 'expert_matching']
            },
            {
                'ai_type': 'knowledge_expert_ai',
                'name': '知识专家AI',
                'description': '专门负责知识管理和专家知识提取',
                'functions': [
                    '知识提取与整理',
                    '知识图谱构建',
                    '知识更新与维护',
                    '知识检索与推荐'
                ],
                'required_skills': ['knowledge_management', 'information_extraction', 'knowledge_graph']
            },
            {
                'ai_type': 'expert_evaluation_ai',
                'name': '专家评估AI',
                'description': '专门负责专家能力和表现评估',
                'functions': [
                    '专家能力评估',
                    '专家表现分析',
                    '专家发展建议',
                    '专家排名与认证'
                ],
                'required_skills': ['expert_evaluation', 'performance_analysis', 'development_planning']
            },
            {
                'ai_type': 'expert_collaboration_ai',
                'name': '专家协作AI',
                'description': '专门促进专家之间的协作',
                'functions': [
                    '协作机会识别',
                    '专家团队组建',
                    '协作过程管理',
                    '协作成果评估'
                ],
                'required_skills': ['collaboration_management', 'team_building', 'process_coordination']
            }
        ]
        
        # 专家系统优化配置
        self.expert_system_configs = {
            'general': {
                'enabled': True,
                'expert_features': ['management', 'consultation', 'knowledge', 'evaluation', 'collaboration'],
                'data_retention_days': 3650,
                'privacy_protection': True,
                'auto_backup': True,
                'backup_frequency': 'daily'
            },
            'expert_management': {
                'enabled': True,
                'profile_fields': ['basic', 'professional', 'expertise', 'availability'],
                'auto_validation': True,
                'data_encryption': True,
                'access_control': True,
                'audit_log': True
            },
            'expert_consultation': {
                'enabled': True,
                'consultation_features': ['problem_routing', 'expert_matching', 'process_management', 'result_evaluation'],
                'auto_classification': True,
                'intelligent_matching': True,
                'real_time_support': True,
                'follow_up_management': True
            },
            'knowledge_expert': {
                'enabled': True,
                'knowledge_features': ['extraction', 'organization', 'maintenance', 'retrieval'],
                'auto_extraction': True,
                'knowledge_graph': True,
                'semantic_search': True,
                'recommendation_engine': True
            },
            'expert_evaluation': {
                'enabled': True,
                'evaluation_methods': ['peer_review', 'performance_metrics', 'client_feedback', 'self_assessment'],
                'multi_source_evaluation': True,
                'performance_tracking': True,
                'development_recommendations': True,
                'certification_support': True
            },
            'expert_collaboration': {
                'enabled': True,
                'collaboration_features': ['opportunity_identification', 'team_building', 'process_management', 'outcome_evaluation'],
                'intelligent_matching': True,
                'collaboration_tools': True,
                'progress_tracking': True,
                'outcome_assessment': True
            },
            'reporting': {
                'enabled': True,
                'report_types': ['individual', 'department', 'organization', 'comparative'],
                'include_statistics': True,
                'include_visualization': True,
                'include_recommendations': True,
                'export_formats': ['pdf', 'excel', 'json', 'html']
            }
        }
        
        logger.info("AI和专家系统增强器初始化完成")
    
    def check_database(self) -> bool:
        """检查数据库是否存在并创建必要的表"""
        try:
            logger.info("开始检查数据库")
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查专家系统配置表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE,
                    config_value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            """)
            
            # 检查专家系统状态表是否存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_system_status (
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
    
    def optimize_expert_system_configs(self) -> bool:
        """优化专家系统配置"""
        try:
            logger.info("开始优化专家系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for config_category, config_values in self.expert_system_configs.items():
                for config_name, config_value in config_values.items():
                    full_config_name = f"expert_{config_category}_{config_name}"
                    
                    # 检查是否已存在
                    cursor.execute(
                        "SELECT config_name FROM expert_system_configs WHERE config_name = ?",
                        (full_config_name,)
                    )
                    if cursor.fetchone():
                        # 更新配置
                        cursor.execute(
                            "UPDATE expert_system_configs SET config_value = ?, updated_at = ? WHERE config_name = ?",
                            (json.dumps(config_value), datetime.now().isoformat(), full_config_name)
                        )
                    else:
                        # 添加新配置
                        cursor.execute(
                            "INSERT INTO expert_system_configs (config_name, config_value, description, updated_at) VALUES (?, ?, ?, ?)",
                            (
                                full_config_name,
                                json.dumps(config_value),
                                f"专家系统 {config_category} 配置: {config_name}",
                                datetime.now().isoformat()
                            )
                        )
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"专家系统配置优化完成，更新 {updated_count} 个配置项")
            return True
        except Exception as e:
            logger.error(f"优化专家系统配置失败: {str(e)}")
            return False
    
    def update_expert_system_status(self) -> bool:
        """更新专家系统状态"""
        try:
            logger.info("开始更新专家系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新专家系统状态
            statuses = {
                'expert_system_enabled': 'True',
                'last_analysis_run': datetime.now().isoformat(),
                'total_experts': '0',
                'active_consultations': '0',
                'total_knowledge_items': '0',
                'total_evaluations_completed': '0',
                'total_collaborations': '0',
                'system_status': 'healthy'
            }
            
            updated_count = 0
            for status_name, status_value in statuses.items():
                # 检查是否已存在
                cursor.execute(
                    "SELECT status_name FROM expert_system_status WHERE status_name = ?",
                    (status_name,)
                )
                if cursor.fetchone():
                    # 更新状态
                    cursor.execute(
                        "UPDATE expert_system_status SET status_value = ?, updated_at = ? WHERE status_name = ?",
                        (status_value, datetime.now().isoformat(), status_name)
                    )
                else:
                    # 添加新状态
                    cursor.execute(
                        "INSERT INTO expert_system_status (status_name, status_value, description, updated_at) VALUES (?, ?, ?, ?)",
                        (
                            status_name,
                            status_value,
                            f"专家系统状态: {status_name}",
                            datetime.now().isoformat()
                        )
                    )
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"专家系统状态更新完成，更新 {updated_count} 个状态项")
            return True
        except Exception as e:
            logger.error(f"更新专家系统状态失败: {str(e)}")
            return False
    
    def get_expert_system_configs(self) -> Dict[str, Any]:
        """获取专家系统配置"""
        try:
            logger.info("获取专家系统配置")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT config_name, config_value FROM expert_system_configs")
            configs = {}
            for row in cursor.fetchall():
                config_name = row[0]
                config_value = json.loads(row[1])
                configs[config_name] = config_value
            
            conn.close()
            
            return configs
        except Exception as e:
            logger.error(f"获取专家系统配置失败: {str(e)}")
            return {}
    
    def get_expert_system_status(self) -> Dict[str, Any]:
        """获取专家系统状态"""
        try:
            logger.info("获取专家系统状态")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT status_name, status_value FROM expert_system_status")
            statuses = {}
            for row in cursor.fetchall():
                status_name = row[0]
                status_value = row[1]
                statuses[status_name] = status_value
            
            conn.close()
            
            return statuses
        except Exception as e:
            logger.error(f"获取专家系统状态失败: {str(e)}")
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
    
    def restart_expert_system(self) -> bool:
        """重启专家系统"""
        try:
            logger.info("开始重启专家系统")
            
            # 这里可以添加实际的专家系统重启逻辑
            # 例如重启相关服务等
            
            logger.info("专家系统重启指令已准备就绪")
            logger.info("请根据需要重启专家系统相关服务")
            
            return True
        except Exception as e:
            logger.error(f"重启专家系统失败: {str(e)}")
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
            
            # 步骤3: 优化专家系统配置
            if self.optimize_expert_system_configs():
                enhance_result['steps'].append('专家系统配置优化完成')
            else:
                enhance_result['errors'].append('专家系统配置优化失败')
                enhance_result['success'] = False
            
            # 步骤4: 更新专家系统状态
            if self.update_expert_system_status():
                enhance_result['steps'].append('专家系统状态更新完成')
            else:
                enhance_result['errors'].append('专家系统状态更新失败')
                enhance_result['success'] = False
            
            # 步骤5: 重启专家系统
            if self.restart_expert_system():
                enhance_result['steps'].append('专家系统重启指令已准备')
            else:
                enhance_result['errors'].append('专家系统重启失败')
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
    logger.info("增加AI并优化专家系统脚本")
    logger.info("=" * 60)
    
    enhancer = AIAndExpertSystemEnhancer()
    
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
    # 过滤出专家系统相关的AI类型
    expert_ai_types = [ai for ai in ai_types if 'expert' in ai['ai_type'] or 'consultation' in ai['ai_type'] or 'knowledge' in ai['ai_type'] or 'evaluation' in ai['ai_type'] or 'collaboration' in ai['ai_type']]
    logger.info(f"已添加 {len(expert_ai_types)} 个专家系统相关AI类型")
    for ai_type in expert_ai_types:
        logger.info(f"  - {ai_type['name']} ({ai_type['ai_type']})")
        logger.info(f"    描述: {ai_type['description']}")
        logger.info(f"    功能: {', '.join(ai_type['functions'])}")
        logger.info(f"    必需技能: {', '.join(ai_type['required_skills'])}")
    
    # 获取专家系统配置
    logger.info("\n3. 获取专家系统配置")
    expert_configs = enhancer.get_expert_system_configs()
    logger.info(f"专家系统配置项数量: {len(expert_configs)}")
    
    # 按类别显示配置
    config_categories = {}
    for config_name, config_value in expert_configs.items():
        category = config_name.split('_')[1]  # 提取类别
        if category not in config_categories:
            config_categories[category] = {}
        config_categories[category][config_name] = config_value
    
    for category, configs in config_categories.items():
        logger.info(f"\n  {category} 配置:")
        for config_name, config_value in configs.items():
            logger.info(f"    {config_name.split('_')[-1]}: {config_value}")
    
    # 获取专家系统状态
    logger.info("\n4. 获取专家系统状态")
    expert_status = enhancer.get_expert_system_status()
    logger.info(f"专家系统状态项数量: {len(expert_status)}")
    for status_name, status_value in expert_status.items():
        logger.info(f"  {status_name}: {status_value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("系统增强完成")
    logger.info("=" * 60)
    
    return 0 if enhance_result['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
