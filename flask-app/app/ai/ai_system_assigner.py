#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统AI分配器模块
负责重新给系统指配专业AI，到系统各个层级和功能并完成适配和托管
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('ai_system_assigner')

class AISystemAssigner:
    """系统AI分配器类"""
    
    def __init__(self):
        """初始化系统AI分配器"""
        # 系统层级和功能定义
        self.system_structure = {
            'frontend': {
                'name': '前端层',
                'description': '用户界面和交互层',
                'functions': [
                    {
                        'name': '用户界面设计',
                        'description': '负责前端界面的设计和实现',
                        'required_skills': ['python_web', 'git_basic'],
                        'preferred_ai_types': ['general', 'web_specialist']
                    },
                    {
                        'name': '用户交互优化',
                        'description': '优化用户交互体验',
                        'required_skills': ['python_web', 'code_analysis'],
                        'preferred_ai_types': ['general', 'web_specialist']
                    },
                    {
                        'name': '响应式设计',
                        'description': '确保在不同设备上的良好显示',
                        'required_skills': ['python_web'],
                        'preferred_ai_types': ['web_specialist']
                    }
                ]
            },
            'backend': {
                'name': '后端层',
                'description': '业务逻辑和数据处理层',
                'functions': [
                    {
                        'name': 'API开发',
                        'description': '开发和维护API接口',
                        'required_skills': ['python_basic', 'python_oop', 'python_web'],
                        'preferred_ai_types': ['general', 'backend_specialist']
                    },
                    {
                        'name': '数据处理',
                        'description': '处理和分析数据',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['general', 'data_specialist']
                    },
                    {
                        'name': '业务逻辑实现',
                        'description': '实现核心业务逻辑',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['general', 'backend_specialist']
                    }
                ]
            },
            'database': {
                'name': '数据层',
                'description': '数据存储和管理层',
                'functions': [
                    {
                        'name': '数据库设计',
                        'description': '设计数据库结构',
                        'required_skills': ['python_basic', 'code_analysis'],
                        'preferred_ai_types': ['general', 'database_specialist']
                    },
                    {
                        'name': '数据查询优化',
                        'description': '优化数据库查询性能',
                        'required_skills': ['code_analysis', 'performance_optimization'],
                        'preferred_ai_types': ['database_specialist', 'engineer_ai']
                    },
                    {
                        'name': '数据安全',
                        'description': '确保数据安全',
                        'required_skills': ['code_analysis'],
                        'preferred_ai_types': ['engineer_ai', 'security_specialist']
                    }
                ]
            },
            'ai_system': {
                'name': 'AI系统层',
                'description': 'AI功能和智能处理层',
                'functions': [
                    {
                        'name': 'AI模型管理',
                        'description': '管理和维护AI模型',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['general', 'ai_specialist']
                    },
                    {
                        'name': '智能分析',
                        'description': '提供智能分析功能',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['ai_specialist', 'teacher_ai']
                    },
                    {
                        'name': 'AI训练',
                        'description': '训练和优化AI模型',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['ai_specialist']
                    }
                ]
            },
            'devops': {
                'name': '运维层',
                'description': '系统运维和部署层',
                'functions': [
                    {
                        'name': '版本控制',
                        'description': '管理代码版本',
                        'required_skills': ['git_basic', 'git_branching', 'git_workflow'],
                        'preferred_ai_types': ['git_ai', 'devops_specialist']
                    },
                    {
                        'name': '性能监控',
                        'description': '监控系统性能',
                        'required_skills': ['code_analysis', 'performance_optimization'],
                        'preferred_ai_types': ['engineer_ai', 'devops_specialist']
                    },
                    {
                        'name': '系统部署',
                        'description': '部署和维护系统',
                        'required_skills': ['code_analysis', 'git_basic'],
                        'preferred_ai_types': ['devops_specialist', 'engineer_ai']
                    }
                ]
            },
            'education': {
                'name': '教育功能层',
                'description': '教育相关功能层',
                'functions': [
                    {
                        'name': '错题分析',
                        'description': '分析学生错题',
                        'required_skills': ['teaching_basic', 'error_analysis'],
                        'preferred_ai_types': ['teacher_ai']
                    },
                    {
                        'name': '个性化教学',
                        'description': '提供个性化学习建议',
                        'required_skills': ['teaching_basic', 'personalized_feedback'],
                        'preferred_ai_types': ['teacher_ai']
                    },
                    {
                        'name': '学习计划制定',
                        'description': '制定学习计划',
                        'required_skills': ['teaching_basic', 'error_analysis'],
                        'preferred_ai_types': ['teacher_ai']
                    }
                ]
            }
        }
        
        # AI分配记录
        self.ai_assignments = {}
        # AI托管状态
        self.ai_hosting_status = {}
        # 系统适配记录
        self.adaptation_records = {}
        
        logger.info("系统AI分配器初始化完成")
    
    def get_system_structure(self) -> Dict[str, Any]:
        """获取系统结构"""
        return self.system_structure
    
    def assign_ai_to_system(self, ai_profile: Dict[str, Any]) -> Dict[str, Any]:
        """将AI分配到系统的各个层级和功能"""
        try:
            ai_id = ai_profile.get('ai_instance_id', 'unknown')
            ai_name = ai_profile.get('ai_name', 'unknown')
            ai_type = ai_profile.get('ai_type', 'general')
            ai_skills = set(ai_profile.get('current_skills', []))
            
            # 为每个层级分配AI
            assignments = {}
            for level_id, level_info in self.system_structure.items():
                level_assignments = []
                
                for func in level_info['functions']:
                    # 计算技能匹配度
                    required_skills = set(func['required_skills'])
                    matched_skills = ai_skills & required_skills
                    match_score = len(matched_skills) / len(required_skills) if required_skills else 0
                    
                    # 检查AI类型是否匹配
                    type_match = ai_type in func['preferred_ai_types'] or 'general' in func['preferred_ai_types']
                    
                    # 综合评分
                    overall_score = (match_score * 0.7) + (1.0 if type_match else 0.0) * 0.3
                    
                    if overall_score >= 0.5:  # 匹配阈值
                        level_assignments.append({
                            'function_name': func['name'],
                            'match_score': match_score,
                            'type_match': type_match,
                            'overall_score': overall_score,
                            'matched_skills': list(matched_skills),
                            'missing_skills': list(required_skills - ai_skills)
                        })
                
                if level_assignments:
                    # 按综合评分排序
                    level_assignments.sort(key=lambda x: x['overall_score'], reverse=True)
                    assignments[level_id] = level_assignments
            
            # 记录分配结果
            self.ai_assignments[ai_id] = {
                'ai_instance_id': ai_id,
                'ai_name': ai_name,
                'ai_type': ai_type,
                'assignments': assignments,
                'assigned_at': datetime.now().isoformat()
            }
            
            # 启动托管
            self.host_ai(ai_id)
            
            result = {
                'success': True,
                'ai_instance_id': ai_id,
                'ai_name': ai_name,
                'assignments': assignments,
                'hosting_status': self.ai_hosting_status.get(ai_id, 'not_hosted'),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"AI {ai_name} 分配到系统完成")
            return result
        except Exception as e:
            logger.error(f"分配AI到系统失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def host_ai(self, ai_instance_id: str) -> bool:
        """托管AI"""
        try:
            if ai_instance_id not in self.ai_assignments:
                logger.error(f"AI {ai_instance_id} 未分配，无法托管")
                return False
            
            # 模拟托管过程
            logger.info(f"开始托管AI: {ai_instance_id}")
            
            # 记录托管状态
            self.ai_hosting_status[ai_instance_id] = {
                'status': 'hosted',
                'hosted_at': datetime.now().isoformat(),
                'assigned_functions': self.ai_assignments[ai_instance_id]['assignments']
            }
            
            logger.info(f"AI {ai_instance_id} 托管成功")
            return True
        except Exception as e:
            logger.error(f"托管AI失败: {str(e)}")
            return False
    
    def adapt_ai_to_function(self, ai_instance_id: str, level_id: str, function_name: str) -> Dict[str, Any]:
        """适配AI到特定功能"""
        try:
            if ai_instance_id not in self.ai_assignments:
                return {
                    'success': False,
                    'error': f'AI {ai_instance_id} 未分配'
                }
            
            if level_id not in self.system_structure:
                return {
                    'success': False,
                    'error': f'系统层级不存在: {level_id}'
                }
            
            # 找到目标功能
            target_function = None
            for func in self.system_structure[level_id]['functions']:
                if func['name'] == function_name:
                    target_function = func
                    break
            
            if not target_function:
                return {
                    'success': False,
                    'error': f'功能不存在: {function_name}'
                }
            
            # 模拟适配过程
            logger.info(f"开始适配AI {ai_instance_id} 到 {level_id} 层级的 {function_name} 功能")
            
            # 记录适配过程
            adaptation_id = f"adapt_{ai_instance_id}_{level_id}_{function_name}_{datetime.now().timestamp()}"
            self.adaptation_records[adaptation_id] = {
                'adaptation_id': adaptation_id,
                'ai_instance_id': ai_instance_id,
                'level_id': level_id,
                'function_name': function_name,
                'status': 'completed',
                'adapted_at': datetime.now().isoformat()
            }
            
            result = {
                'success': True,
                'adaptation_id': adaptation_id,
                'ai_instance_id': ai_instance_id,
                'level_id': level_id,
                'function_name': function_name,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"AI {ai_instance_id} 适配到 {function_name} 功能成功")
            return result
        except Exception as e:
            logger.error(f"适配AI失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ai_assignments(self) -> Dict[str, Any]:
        """获取所有AI分配记录"""
        return self.ai_assignments
    
    def get_ai_hosting_status(self) -> Dict[str, Any]:
        """获取AI托管状态"""
        return self.ai_hosting_status
    
    def get_adaptation_records(self) -> Dict[str, Any]:
        """获取适配记录"""
        return self.adaptation_records
    
    def optimize_ai_assignments(self) -> Dict[str, Any]:
        """优化AI分配"""
        try:
            # 这里可以实现更复杂的优化逻辑
            # 例如：负载均衡、技能互补等
            
            optimization_result = {
                'optimization_time': datetime.now().isoformat(),
                'total_ais': len(self.ai_assignments),
                'total_assignments': sum(len(assignments['assignments']) for assignments in self.ai_assignments.values()),
                'status': 'completed'
            }
            
            logger.info("AI分配优化完成")
            return optimization_result
        except Exception as e:
            logger.error(f"优化AI分配失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# 创建全局系统AI分配器实例
ai_system_assigner = AISystemAssigner()

if __name__ == '__main__':
    print("系统AI分配器初始化成功")
    print(f"系统层级数量: {len(ai_system_assigner.system_structure)}")
    for level_id, level_info in ai_system_assigner.system_structure.items():
        print(f"\n层级: {level_info['name']} (ID: {level_id})")
        print(f"  功能数量: {len(level_info['functions'])}")
        for func in level_info['functions']:
            print(f"    - {func['name']}")
