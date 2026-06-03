# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI项目匹配器模块
负责动态匹配专业AI到项目的各个领域和功能
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger('ai_project_matcher')


class AIProjectMatcher:
    """AI项目匹配器类"""

    def __init__(self):
        """初始化AI项目匹配器"""
        self.project_domains = {
            'web_development': {
                'name': 'Web开发',
                'required_skills': ['python_basic', 'python_oop', 'python_web', 'git_basic'],
                'recommended_skills': ['git_branching', 'code_analysis'],
                'functions': [
                    {
                        'name': '前端开发',
                        'required_skills': ['python_web'],
                        'ai_types': ['general', 'web_specialist']
                    },
                    {
                        'name': '后端开发',
                        'required_skills': ['python_basic', 'python_oop', 'python_web'],
                        'ai_types': ['general', 'backend_specialist']
                    },
                    {
                        'name': 'API开发',
                        'required_skills': ['python_web'],
                        'ai_types': ['backend_specialist']
                    }
                ]
            },
            'education': {
                'name': '教育领域',
                'required_skills': ['teaching_basic'],
                'recommended_skills': ['personalized_feedback'],
                'functions': [
                    {
                        'name': '错题分析',
                        'required_skills': ['teaching_basic'],
                        'ai_types': ['teacher_ai']
                    },
                    {
                        'name': '个性化教学',
                        'required_skills': ['personalized_feedback'],
                        'ai_types': ['teacher_ai']
                    },
                    {
                        'name': '学习计划制定',
                        'required_skills': ['teaching_basic'],
                        'ai_types': ['teacher_ai']
                    }
                ]
            },
            'software_engineering': {
                'name': '软件工程',
                'required_skills': ['python_basic', 'python_oop'],
                'recommended_skills': ['performance_optimization', 'git_basic'],
                'functions': [
                    {
                        'name': '代码审查',
                        'required_skills': ['code_analysis'],
                        'ai_types': ['code_reviewer_ai']
                    },
                    {
                        'name': '性能优化',
                        'required_skills': ['performance_optimization'],
                        'ai_types': ['performance_ai']
                    }
                ]
            },
            'version_control': {
                'name': '版本控制',
                'required_skills': ['git_basic'],
                'recommended_skills': ['git_branching'],
                'functions': [
                    {
                        'name': '代码管理',
                        'required_skills': ['git_basic'],
                        'ai_types': ['git_ai']
                    },
                    {
                        'name': '分支管理',
                        'required_skills': ['git_branching'],
                        'ai_types': ['git_ai']
                    },
                    {
                        'name': '工作流设计',
                        'required_skills': ['git_basic', 'git_branching'],
                        'ai_types': ['git_ai']
                    }
                ]
            }
        }

        logger.info("AI项目匹配器初始化完成")

    def get_all_domains(self) -> List[Dict[str, Any]]:
        """获取所有项目领域"""
        return [
            {
                'domain_id': domain_id,
                'name': domain_data['name'],
                'required_skills': domain_data.get('required_skills', []),
                'recommended_skills': domain_data.get('recommended_skills', []),
                'functions_count': len(domain_data.get('functions', []))
            }
            for domain_id, domain_data in self.project_domains.items()
        ]

    def match_ai_to_project(self, ai_skills: List[str], project_domain: str) -> Dict[str, Any]:
        """匹配AI到项目

        Args:
            ai_skills: AI技能列表
            project_domain: 项目领域

        Returns:
            匹配结果
        """
        if project_domain not in self.project_domains:
            return {
                'success': False,
                'message': f'项目领域 {project_domain} 不存在'
            }

        domain = self.project_domains[project_domain]
        required_skills = set(domain.get('required_skills', []))
        ai_skills_set = set(ai_skills)

        matched_required = required_skills & ai_skills_set
        missing_required = required_skills - ai_skills_set

        recommended_skills = set(domain.get('recommended_skills', []))
        matched_recommended = recommended_skills & ai_skills_set

        match_score = len(matched_required) / len(required_skills) if required_skills else 1.0

        suitable_functions = []
        for func in domain.get('functions', []):
            func_required = set(func.get('required_skills', []))
            if func_required <= ai_skills_set:
                suitable_functions.append(func['name'])

        return {
            'success': True,
            'domain': domain['name'],
            'match_score': match_score,
            'matched_required_skills': list(matched_required),
            'missing_required_skills': list(missing_required),
            'matched_recommended_skills': list(matched_recommended),
            'suitable_functions': suitable_functions,
            'ai_types': self._get_recommended_ai_types(domain, ai_skills_set)
        }

    def _get_recommended_ai_types(self, domain: Dict[str, Any], ai_skills: set) -> List[str]:
        """获取推荐的AI类型"""
        ai_types = set()
        for func in domain.get('functions', []):
            func_required = set(func.get('required_skills', []))
            if func_required <= ai_skills:
                ai_types.update(func.get('ai_types', []))
        return list(ai_types)

    def get_domain_functions(self, domain_id: str) -> List[Dict[str, Any]]:
        """获取领域功能列表"""
        if domain_id not in self.project_domains:
            return []

        return self.project_domains[domain_id].get('functions', [])

    def suggest_skills_for_domain(self, domain_id: str) -> Dict[str, Any]:
        """为领域建议技能"""
        if domain_id not in self.project_domains:
            return {
                'success': False,
                'message': f'项目领域 {domain_id} 不存在'
            }

        domain = self.project_domains[domain_id]
        return {
            'success': True,
            'domain': domain['name'],
            'required_skills': domain.get('required_skills', []),
            'recommended_skills': domain.get('recommended_skills', []),
            'learning_path': self._generate_learning_path(domain)
        }

    def _generate_learning_path(self, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成学习路径"""
        path = []
        for skill in domain.get('required_skills', []):
            path.append({
                'skill': skill,
                'priority': 'required',
                'description': f'学习 {skill} 技能'
            })
        for skill in domain.get('recommended_skills', []):
            path.append({
                'skill': skill,
                'priority': 'recommended',
                'description': f'学习 {skill} 技能'
            })
        return path

    def find_best_domain_for_ai(self, ai_skills: List[str]) -> Dict[str, Any]:
        """为AI找到最佳匹配领域"""
        best_match = None
        best_score = 0

        for domain_id, domain in self.project_domains.items():
            required_skills = set(domain.get('required_skills', []))
            ai_skills_set = set(ai_skills)

            matched = required_skills & ai_skills_set
            score = len(matched) / len(required_skills) if required_skills else 0

            if score > best_score:
                best_score = score
                best_match = {
                    'domain_id': domain_id,
                    'domain_name': domain['name'],
                    'match_score': score,
                    'matched_skills': list(matched)
                }

        return best_match or {
            'domain_id': None,
            'domain_name': None,
            'match_score': 0,
            'matched_skills': []
        }
