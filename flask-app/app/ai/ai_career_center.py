#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI职业介绍所模块
负责给AI专业赋能，转岗，提取，知识库学习，AI本生维护等
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logger = logging.getLogger('ai_career_center')

class AICareerCenter:
    """AI职业介绍所类"""
    
    def __init__(self):
        """初始化AI职业介绍所"""
        self.skills_database = {}
        self.career_paths = {}
        self.ai_profiles = {}
        self.learning_resources = {}
        self.maintenance_records = {}
        
        # 初始化Git相关技能和职业路径
        self._initialize_git_skills()
        self._initialize_git_career_paths()
        
        logger.info("AI职业介绍所初始化完成")
    
    def add_skill(self, skill_id: str, skill_name: str, description: str, category: str, level: str):
        """添加技能到技能数据库"""
        try:
            self.skills_database[skill_id] = {
                'skill_id': skill_id,
                'skill_name': skill_name,
                'description': description,
                'category': category,
                'level': level,
                'created_at': datetime.now().isoformat()
            }
            logger.info(f"技能添加成功: {skill_name}")
        except Exception as e:
            logger.error(f"添加技能失败: {str(e)}")
    
    def add_career_path(self, path_id: str, path_name: str, required_skills: List[str], description: str):
        """添加职业路径"""
        try:
            self.career_paths[path_id] = {
                'path_id': path_id,
                'path_name': path_name,
                'required_skills': required_skills,
                'description': description,
                'created_at': datetime.now().isoformat()
            }
            logger.info(f"职业路径添加成功: {path_name}")
        except Exception as e:
            logger.error(f"添加职业路径失败: {str(e)}")
    
    def register_ai(self, ai_instance_id: str, ai_type: str, current_skills: List[str], current_career: str = None):
        """注册AI到职业介绍所"""
        try:
            self.ai_profiles[ai_instance_id] = {
                'ai_instance_id': ai_instance_id,
                'ai_type': ai_type,
                'current_skills': current_skills,
                'current_career': current_career,
                'registered_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            logger.info(f"AI注册成功: {ai_instance_id}")
        except Exception as e:
            logger.error(f"注册AI失败: {str(e)}")
    
    def empower_ai(self, ai_instance_id: str, skills: List[str]):
        """给AI赋能，添加新技能"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return False
            
            # 添加新技能
            for skill_id in skills:
                if skill_id in self.skills_database:
                    if skill_id not in self.ai_profiles[ai_instance_id]['current_skills']:
                        self.ai_profiles[ai_instance_id]['current_skills'].append(skill_id)
                        logger.info(f"AI {ai_instance_id} 获得新技能: {self.skills_database[skill_id]['skill_name']}")
                else:
                    logger.warning(f"技能不存在: {skill_id}")
            
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"AI赋能成功: {ai_instance_id}")
            return True
        except Exception as e:
            logger.error(f"赋能AI失败: {str(e)}")
            return False
    
    def transfer_ai_career(self, ai_instance_id: str, new_career_path_id: str):
        """帮助AI转岗到新的职业路径"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return False
            
            if new_career_path_id not in self.career_paths:
                logger.error(f"职业路径不存在: {new_career_path_id}")
                return False
            
            # 检查是否具备所需技能
            required_skills = self.career_paths[new_career_path_id]['required_skills']
            current_skills = self.ai_profiles[ai_instance_id]['current_skills']
            missing_skills = [skill for skill in required_skills if skill not in current_skills]
            
            if missing_skills:
                logger.warning(f"AI {ai_instance_id} 缺少转岗所需技能: {missing_skills}")
                return False
            
            # 执行转岗
            self.ai_profiles[ai_instance_id]['current_career'] = new_career_path_id
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"AI转岗成功: {ai_instance_id} -> {self.career_paths[new_career_path_id]['path_name']}")
            return True
        except Exception as e:
            logger.error(f"转岗AI失败: {str(e)}")
            return False
    
    def extract_ai_knowledge(self, ai_instance_id: str) -> Dict[str, Any]:
        """从AI中提取知识"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return {}
            
            # 提取AI的知识和技能
            ai_profile = self.ai_profiles[ai_instance_id]
            extracted_knowledge = {
                'ai_instance_id': ai_instance_id,
                'ai_type': ai_profile['ai_type'],
                'current_skills': [],
                'current_career': None,
                'extracted_at': datetime.now().isoformat()
            }
            
            # 转换技能ID为技能名称
            for skill_id in ai_profile['current_skills']:
                if skill_id in self.skills_database:
                    extracted_knowledge['current_skills'].append({
                        'skill_id': skill_id,
                        'skill_name': self.skills_database[skill_id]['skill_name'],
                        'category': self.skills_database[skill_id]['category'],
                        'level': self.skills_database[skill_id]['level']
                    })
            
            # 添加当前职业
            if ai_profile['current_career'] and ai_profile['current_career'] in self.career_paths:
                extracted_knowledge['current_career'] = {
                    'path_id': ai_profile['current_career'],
                    'path_name': self.career_paths[ai_profile['current_career']]['path_name'],
                    'description': self.career_paths[ai_profile['current_career']]['description']
                }
            
            logger.info(f"AI知识提取成功: {ai_instance_id}")
            return extracted_knowledge
        except Exception as e:
            logger.error(f"提取AI知识失败: {str(e)}")
            return {}
    
    def learn_knowledge_base(self, ai_instance_id: str, knowledge_base_id: str, resources: List[str]):
        """让AI学习新的知识库"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return False
            
            # 记录学习资源
            if knowledge_base_id not in self.learning_resources:
                self.learning_resources[knowledge_base_id] = {
                    'knowledge_base_id': knowledge_base_id,
                    'resources': resources,
                    'created_at': datetime.now().isoformat()
                }
            
            # 模拟学习过程
            logger.info(f"AI {ai_instance_id} 开始学习知识库: {knowledge_base_id}")
            # 这里可以添加实际的学习逻辑
            
            # 更新AI的技能
            # 假设学习完成后获得新技能
            # 这里简化处理，实际应该根据学习内容更新技能
            
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"AI学习知识库成功: {ai_instance_id} -> {knowledge_base_id}")
            return True
        except Exception as e:
            logger.error(f"AI学习知识库失败: {str(e)}")
            return False
    
    def maintain_ai(self, ai_instance_id: str, maintenance_type: str, details: Dict[str, Any]):
        """维护AI，包括性能优化、错误修复等"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return False
            
            # 记录维护记录
            maintenance_id = f"maintenance_{ai_instance_id}_{datetime.now().timestamp()}"
            self.maintenance_records[maintenance_id] = {
                'maintenance_id': maintenance_id,
                'ai_instance_id': ai_instance_id,
                'maintenance_type': maintenance_type,
                'details': details,
                'maintenance_at': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            # 执行维护操作
            logger.info(f"开始维护AI: {ai_instance_id} - {maintenance_type}")
            # 这里可以添加实际的维护逻辑
            
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"AI维护成功: {ai_instance_id} - {maintenance_type}")
            return True
        except Exception as e:
            logger.error(f"维护AI失败: {str(e)}")
            return False
    
    def get_ai_career_recommendations(self, ai_instance_id: str) -> List[Dict[str, Any]]:
        """获取AI的职业建议"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return []
            
            # 分析AI的当前技能
            ai_profile = self.ai_profiles[ai_instance_id]
            current_skills = ai_profile['current_skills']
            
            # 推荐适合的职业路径
            recommendations = []
            for path_id, path in self.career_paths.items():
                required_skills = path['required_skills']
                missing_skills = [skill for skill in required_skills if skill not in current_skills]
                match_score = (len(required_skills) - len(missing_skills)) / len(required_skills) if required_skills else 0
                
                if match_score > 0:
                    recommendations.append({
                        'path_id': path_id,
                        'path_name': path['path_name'],
                        'match_score': match_score,
                        'missing_skills': missing_skills,
                        'description': path['description']
                    })
            
            # 按匹配度排序
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            logger.info(f"获取AI职业建议成功: {ai_instance_id}")
            return recommendations
        except Exception as e:
            logger.error(f"获取AI职业建议失败: {str(e)}")
            return []
    
    def get_ai_skill_gap(self, ai_instance_id: str, target_career_path_id: str) -> Dict[str, Any]:
        """获取AI与目标职业路径之间的技能差距"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return {}
            
            if target_career_path_id not in self.career_paths:
                logger.error(f"职业路径不存在: {target_career_path_id}")
                return {}
            
            # 分析技能差距
            ai_profile = self.ai_profiles[ai_instance_id]
            current_skills = ai_profile['current_skills']
            required_skills = self.career_paths[target_career_path_id]['required_skills']
            
            missing_skills = []
            for skill_id in required_skills:
                if skill_id not in current_skills:
                    if skill_id in self.skills_database:
                        missing_skills.append({
                            'skill_id': skill_id,
                            'skill_name': self.skills_database[skill_id]['skill_name'],
                            'category': self.skills_database[skill_id]['category'],
                            'level': self.skills_database[skill_id]['level']
                        })
            
            skill_gap = {
                'ai_instance_id': ai_instance_id,
                'target_career_path': {
                    'path_id': target_career_path_id,
                    'path_name': self.career_paths[target_career_path_id]['path_name']
                },
                'current_skills_count': len(current_skills),
                'required_skills_count': len(required_skills),
                'missing_skills': missing_skills,
                'skill_gap_score': len(missing_skills) / len(required_skills) if required_skills else 0
            }
            
            logger.info(f"获取AI技能差距成功: {ai_instance_id} -> {target_career_path_id}")
            return skill_gap
        except Exception as e:
            logger.error(f"获取AI技能差距失败: {str(e)}")
            return {}
    
    def _initialize_git_skills(self):
        """初始化Git相关技能"""
        git_skills = [
            {
                'skill_id': 'git_basic',
                'skill_name': 'Git基础操作',
                'description': '掌握Git基本命令，如clone, add, commit, push, pull等',
                'category': 'Git',
                'level': '初级'
            },
            {
                'skill_id': 'git_branching',
                'skill_name': 'Git分支管理',
                'description': '熟练使用Git分支，包括创建、切换、合并分支等',
                'category': 'Git',
                'level': '中级'
            },
            {
                'skill_id': 'git_workflow',
                'skill_name': 'Git工作流',
                'description': '掌握Git Flow、GitHub Flow等工作流，能够制定分支策略',
                'category': 'Git',
                'level': '高级'
            },
            {
                'skill_id': 'git_conflict',
                'skill_name': 'Git冲突解决',
                'description': '能够有效检测和解决Git合并冲突',
                'category': 'Git',
                'level': '高级'
            },
            {
                'skill_id': 'git_history',
                'skill_name': 'Git历史分析',
                'description': '能够分析Git提交历史，进行版本追踪和代码审计',
                'category': 'Git',
                'level': '高级'
            },
            {
                'skill_id': 'git_automation',
                'skill_name': 'Git自动化',
                'description': '能够自动化Git操作，如自动提交、版本标签生成等',
                'category': 'Git',
                'level': '高级'
            }
        ]
        
        for skill in git_skills:
            self.add_skill(
                skill['skill_id'],
                skill['skill_name'],
                skill['description'],
                skill['category'],
                skill['level']
            )
        logger.info("Git技能初始化完成")
    
    def _initialize_git_career_paths(self):
        """初始化Git相关职业路径"""
        git_career_paths = [
            {
                'path_id': 'git_basic_user',
                'path_name': 'Git基础用户',
                'required_skills': ['git_basic'],
                'description': '能够使用Git进行基本的版本控制操作'
            },
            {
                'path_id': 'git_branch_manager',
                'path_name': 'Git分支管理员',
                'required_skills': ['git_basic', 'git_branching'],
                'description': '能够管理Git分支，支持团队协作开发'
            },
            {
                'path_id': 'git_workflow_designer',
                'path_name': 'Git工作流设计师',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow'],
                'description': '能够设计和实施Git工作流，提升团队开发效率'
            },
            {
                'path_id': 'git_expert',
                'path_name': 'Git专家',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow', 'git_conflict', 'git_history', 'git_automation'],
                'description': '全面掌握Git，能够解决复杂的版本控制问题'
            }
        ]
        
        for path in git_career_paths:
            self.add_career_path(
                path['path_id'],
                path['path_name'],
                path['required_skills'],
                path['description']
            )
        logger.info("Git职业路径初始化完成")

# 创建全局AI职业介绍所实例
ai_career_center = AICareerCenter()

if __name__ == '__main__':
    # 测试AI职业介绍所
    print("初始化AI职业介绍所...")
    
    # 添加技能
    print("\n添加技能...")
    ai_career_center.add_skill('skill_1', 'Python编程', 'Python语言编程技能', '编程', '高级')
    ai_career_center.add_skill('skill_2', 'Flask框架', 'Flask Web框架开发', '编程', '中级')
    ai_career_center.add_skill('skill_3', '数据库设计', '数据库设计与优化', '数据库', '中级')
    ai_career_center.add_skill('skill_4', '网络安全', '网络安全防护', '安全', '高级')
    ai_career_center.add_skill('skill_5', 'AI算法', '人工智能算法设计', 'AI', '高级')
    
    # 添加职业路径
    print("\n添加职业路径...")
    ai_career_center.add_career_path('path_1', 'Web开发者', ['skill_1', 'skill_2', 'skill_3'], 'Web应用开发')
    ai_career_center.add_career_path('path_2', 'AI工程师', ['skill_1', 'skill_5', 'skill_3'], '人工智能开发')
    ai_career_center.add_career_path('path_3', '安全专家', ['skill_1', 'skill_4'], '网络安全防护')
    
    # 注册AI
    print("\n注册AI...")
    ai_career_center.register_ai('ai_1', 'general', ['skill_1', 'skill_2'])
    ai_career_center.register_ai('ai_2', 'ai_specialist', ['skill_1', 'skill_5'])
    
    # 赋能AI
    print("\n赋能AI...")
    ai_career_center.empower_ai('ai_1', ['skill_3'])
    
    # 转岗AI
    print("\n转岗AI...")
    ai_career_center.transfer_ai_career('ai_1', 'path_1')
    
    # 提取AI知识
    print("\n提取AI知识...")
    knowledge = ai_career_center.extract_ai_knowledge('ai_1')
    print(f"提取的知识: {knowledge}")
    
    # 学习知识库
    print("\n学习知识库...")
    ai_career_center.learn_knowledge_base('ai_2', 'kb_1', ['resource_1', 'resource_2'])
    
    # 维护AI
    print("\n维护AI...")
    ai_career_center.maintain_ai('ai_1', 'performance_optimization', {'cpu': '优化', 'memory': '清理'})
    
    # 获取职业建议
    print("\n获取职业建议...")
    recommendations = ai_career_center.get_ai_career_recommendations('ai_2')
    for rec in recommendations:
        print(f"推荐职业: {rec['path_name']} (匹配度: {rec['match_score']})")
    
    # 获取技能差距
    print("\n获取技能差距...")
    skill_gap = ai_career_center.get_ai_skill_gap('ai_2', 'path_2')
    print(f"技能差距: {skill_gap}")
    
    print("\nAI职业介绍所测试完成！")