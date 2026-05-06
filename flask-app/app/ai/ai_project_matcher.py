#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI项目匹配器模块
负责动态匹配专业AI到项目的各个领域和功能

import os
# JSON import removed - using database
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('ai_project_matcher')

class AIProjectMatcher:
    """AI项目匹配器类"""

    def __init__(self):
        """初始化AI项目匹配器"""
        # 项目领域和功能映射
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
                        'required_skills': ['python_basic', 'python_oop', 'python_web'],
                        'ai_types': ['general', 'backend_specialist']
                    },
                    {
                        'ai_types': ['backend_specialist']
                    }
                ]
            },
            'education': {
                'name': '教育领域',
                'recommended_skills': ['personalized_feedback'],
                'functions': [
                        'name': '错题分析',
                        'ai_types': ['teacher_ai']
                    },
                    {
                        'name': '个性化教学',
                        'ai_types': ['teacher_ai']
                    },
                        'name': '学习计划制定',
                        'ai_types': ['teacher_ai']
                    }
                ]
            'software_engineering': {
                'name': '软件工程',
                'recommended_skills': ['performance_optimization', 'git_basic'],
                'functions': [
                        'name': '代码审查',
                    {
                    },
                    {
                        'name': '性能优化',
                        'required_skills': ['performance_optimization'],
                    }
            },
            'version_control': {
                'name': '版本控制',
                'required_skills': ['git_basic'],
                'functions': [
                        'name': '代码管理',
                        'required_skills': ['git_basic'],
                        'ai_types': ['git_ai']
                    {
                        'name': '分支管理',
                        'ai_types': ['git_ai']
                    {
                        'name': '工作流设计',
                        'ai_types': ['git_ai']
                ]
        }


        logger.info("AI项目匹配器初始化完成")

        """获取所有项目领域"""
        return [{
            'domain_id': domain_id,
            'name': domain_info['name'],
            'required_skills': domain_info['required_skills'],
            'recommended_skills': domain_info['recommended_skills'],
            'functions': domain_info['functions']
        } for domain_id, domain_info in self.project_domains.items()]

                          project_domain: str,
                          project_function: str = None) -> Dict[str, Any]:
        """匹配AI到项目领域和功能"""
        try:
            if project_domain not in self.project_domains:
                    'success': False,
                }

            domain_info = self.project_domains[project_domain]
            ai_skills = set(ai_profile.get('current_skills', []))
            # 计算技能匹配度
            required_skills = set(domain_info['required_skills'])
            recommended_skills = set(domain_info['recommended_skills'])

            # 计算匹配分数
            required_match = len(ai_skills & required_skills)
            recommended_match = len(ai_skills & recommended_skills)

            total_required = len(required_skills)
            total_recommended = len(recommended_skills)

            # 计算综合匹配度
            if total_required > 0:
                required_score = required_match / total_required
            else:
                required_score = 0

            if total_recommended > 0:
                recommended_score = recommended_match / total_recommended
            else:
                recommended_score = 0

            # 加权计算
            overall_score = (required_score * 0.7) + (recommended_score * 0.3)

            # 匹配到具体功能
            function_matches = []
            for func in domain_info['functions']:
                if project_function and func['name'] != project_function:
                    continue

                func_required = set(func['required_skills'])
                func_match = len(ai_skills & func_required)
                func_total = len(func_required)

                if func_total > 0:
                    func_score = func_match / func_total
                else:
                    func_score = 0

                # 检查AI类型是否匹配
                ai_type = ai_profile.get('ai_type', 'general')
                type_match = ai_type in func['ai_types'] or 'general' in func['ai_types']

                function_matches.append({
                    'function_name': func['name'],
                    'match_score': func_score,
                    'type_match': type_match,
                    'required_skills': list(func_required),
                    'matched_skills': list(ai_skills & func_required),
                    'missing_skills': list(func_required - ai_skills)
                })

            # 按匹配度排序
            function_matches.sort(key=lambda x: x['match_score'], reverse=True)
            # 生成匹配结果
            result = {
                'success': True,
                'ai_instance_id': ai_profile.get('ai_instance_id', 'unknown'),
                'ai_name': ai_profile.get('ai_name', 'unknown'),
                'ai_type': ai_profile.get('ai_type', 'general'),
                'project_domain': project_domain,
                'domain_name': domain_info['name'],
                'overall_match_score': overall_score,
                'skill_match': {
                    'required': {
                        'total': total_required,
                        'matched': required_match,
                        'missing': list(required_skills - ai_skills)
                    },
                    'recommended': {
                        'total': total_recommended,
                        'missing': list(recommended_skills - ai_skills)
                    }
                },
                'function_matches': function_matches,
                'timestamp': datetime.now().isoformat()
            }

            # 记录匹配历史
            self.matching_history.append(result)

            logger.info(f"AI {ai_profile.get('ai_instance_id', 'unknown')} 匹配到 {project_domain} 领域，匹配度: {overall_score:.2f}")
        except Exception as e:
            logger.error(f"匹配AI到项目失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)

    def find_best_ai_for_project(self, project_domain: str,
                                project_function: str = None,
                                ai_profiles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """为项目找到最佳的AI"""
        try:
            if project_domain not in self.project_domains:
                return {
                    'success': False,
                    'error': f'项目领域不存在: {project_domain}'
                }

            if not ai_profiles:
                return {
                    'success': False,
                    'error': '没有提供AI档案'
                }

            # 为每个AI计算匹配度
            matches = []
            for ai_profile in ai_profiles:
                match_result = self.match_ai_to_project(
                    ai_profile,
                    project_domain,
                    project_function
                )
                if match_result['success']:
                    matches.append(match_result)

            if not matches:
                return {
                    'success': False,
                    'error': '没有找到匹配的AI'
                }

            # 按匹配度排序
            matches.sort(key=lambda x: x['overall_match_score'], reverse=True)

            # 返回最佳匹配
            best_match = matches[0]
            result = {
                'success': True,
                'best_match': best_match,
                'timestamp': datetime.now().isoformat()

            logger.info(f"为 {project_domain} 领域找到最佳AI: {best_match['ai_instance_id']} (匹配度: {best_match['overall_match_score']:.2f})")
            return result
            logger.error(f"寻找最佳AI失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_skill_gaps(self, ai_profile: Dict[str, Any],
                      project_domain: str) -> Dict[str, Any]:
        """获取AI在特定项目领域的技能差距"""
        try:
            if project_domain not in self.project_domains:
                return {
                    'success': False,
                    'error': f'项目领域不存在: {project_domain}'
                }

            domain_info = self.project_domains[project_domain]
            ai_skills = set(ai_profile.get('current_skills', []))

            # 计算技能差距
            required_skills = set(domain_info['required_skills'])
            recommended_skills = set(domain_info['recommended_skills'])

            missing_required = list(required_skills - ai_skills)
            missing_recommended = list(recommended_skills - ai_skills)

            # 为每个功能计算技能差距
            function_gaps = []
                func_required = set(func['required_skills'])
                func_missing = list(func_required - ai_skills)

                function_gaps.append({
                    'function_name': func['name'],
                    'missing_skills': func_missing,
                    'total_required': len(func_required),
                    'missing_count': len(func_missing)
                })

            result = {
                'success': True,
                'ai_instance_id': ai_profile.get('ai_instance_id', 'unknown'),
                'project_domain': project_domain,
                'domain_name': domain_info['name'],
                'skill_gaps': {
                    'required': {
                        'missing': missing_required,
                    },
                    'recommended': {
                        'count': len(missing_recommended)
                    }
                },
                'function_gaps': function_gaps,
            }

            logger.info(f"获取AI {ai_profile.get('ai_instance_id', 'unknown')} 在 {project_domain} 领域的技能差距")
            return result
            logger.error(f"获取技能差距失败: {str(e)}")
                'error': str(e)
            }

        """为AI生成技能发展计划"""
            # 获取技能差距
            skill_gaps = self.get_skill_gaps(ai_profile, project_domain)
            if not skill_gaps['success']:
                return skill_gaps

            # 生成发展计划
            missing_required = skill_gaps['skill_gaps']['required']['missing']
            missing_recommended = skill_gaps['skill_gaps']['recommended']['missing']

            development_plan = []
            # 优先学习必需技能
            for skill_id in missing_required:
                development_plan.append({
                    'skill_id': skill_id,
                    'type': 'required'
                })

            # 然后学习推荐技能
            for skill_id in missing_recommended:
                development_plan.append({
                    'skill_id': skill_id,
                    'priority': 'medium',
                    'type': 'recommended'
                })

                'success': True,
                'ai_instance_id': ai_profile.get('ai_instance_id', 'unknown'),
                'development_plan': development_plan,
                'total_skills_to_learn': len(development_plan),
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"为AI {ai_profile.get('ai_instance_id', 'unknown')} 生成技能发展计划")
            return result
            logger.error(f"生成技能发展计划失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_matching_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取匹配历史记录"""
        return self.matching_history[-limit:]

# 创建全局AI项目匹配器实例
ai_project_matcher = AIProjectMatcher()

if __name__ == '__main__':
    print("AI项目匹配器初始化成功")
    print(f"支持的项目领域: {list(ai_project_matcher.project_domains.keys())}")
