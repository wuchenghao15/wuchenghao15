# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统AI分配器模块
负责重新给系统指配专业AI,到系统各个层级和功能并完成适配和托管
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logger = logging.getLogger('ai_system_assigner')

class AISystemAssigner:
    """系统AI分配器类"""

    def __init__(self):
        """初始化系统AI分配器"""
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
                        'required_skills': [],
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
                        'required_skills': [],
                        'preferred_ai_types': ['general', 'database_specialist']
                    },
                    {
                        'name': '查询优化',
                        'description': '优化数据库查询性能',
                        'required_skills': [],
                        'preferred_ai_types': ['general', 'database_specialist']
                    },
                    {
                        'name': '数据安全',
                        'description': '确保数据安全',
                        'required_skills': [],
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
                        'preferred_ai_types': ['general']
                    },
                    {
                        'name': '智能分析',
                        'description': '提供智能分析功能',
                        'required_skills': [],
                        'preferred_ai_types': ['general']
                    },
                    {
                        'name': 'AI训练',
                        'description': '训练和优化AI模型',
                        'required_skills': ['python_basic', 'python_oop'],
                        'preferred_ai_types': ['general']
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
                        'preferred_ai_types': ['devops_specialist', 'engineer_ai']
                    },
                    {
                        'name': '性能监控',
                        'description': '监控系统性能',
                        'required_skills': ['code_analysis', 'performance_optimization'],
                        'preferred_ai_types': ['devops_specialist', 'engineer_ai']
                    },
                    {
                        'name': '系统部署',
                        'description': '部署和发布系统',
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
                        'required_skills': [],
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

        self.ai_assignments = {}
        self.ai_hosting_status = {}
        self.adaptation_records = {}

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

            assignments = {}
            for level_id, level_info in self.system_structure.items():
                level_assignments = []

                for func in level_info['functions']:
                    required_skills = set(func.get('required_skills', []))
                    matched_skills = ai_skills & required_skills
                    match_score = len(matched_skills) / len(required_skills) if required_skills else 0

                    type_match = ai_type in func.get('preferred_ai_types', []) or 'general' in func.get('preferred_ai_types', [])

                    overall_score = match_score * 0.7 + (0.3 if type_match else 0)

                    if overall_score >= 0.5:
                        level_assignments.append({
                            'function_name': func['name'],
                            'match_score': match_score,
                            'type_match': type_match,
                            'overall_score': overall_score,
                            'missing_skills': list(required_skills - ai_skills)
                        })

                if level_assignments:
                    level_assignments.sort(key=lambda x: x['overall_score'], reverse=True)
                    assignments[level_id] = level_assignments

            self.ai_assignments[ai_id] = {
                'ai_instance_id': ai_id,
                'ai_name': ai_name,
                'ai_type': ai_type,
                'assignments': assignments,
                'assigned_at': datetime.now().isoformat()
            }

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
            return {'success': False, 'error': str(e)}

    def host_ai(self, ai_id: str) -> bool:
        """托管AI实例"""
        try:
            self.ai_hosting_status[ai_id] = 'hosted'
            logger.info(f"AI实例 {ai_id} 已托管")
            return True
        except Exception as e:
            logger.error(f"托管AI实例失败: {str(e)}")
            return False

    def unhost_ai(self, ai_id: str) -> bool:
        """取消托管AI实例"""
        try:
            if ai_id in self.ai_hosting_status:
                del self.ai_hosting_status[ai_id]
                logger.info(f"AI实例 {ai_id} 已取消托管")
                return True
            return False
        except Exception as e:
            logger.error(f"取消托管AI实例失败: {str(e)}")
            return False

    def get_ai_assignments(self, ai_id: str = None) -> Dict[str, Any]:
        """获取AI分配信息"""
        if ai_id:
            return self.ai_assignments.get(ai_id, {})
        return self.ai_assignments
