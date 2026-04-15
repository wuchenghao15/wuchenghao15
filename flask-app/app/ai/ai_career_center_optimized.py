#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版AI职业介绍所模块
包含数据库持久化、技能学习路径、性能评估、搜索过滤等增强功能
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# 配置日志
logger = logging.getLogger('ai_career_center_optimized')

class AICareerCenterOptimized:
    """优化版AI职业介绍所类"""
    
    def __init__(self, data_dir: str = None):
        """初始化优化版AI职业介绍所"""
        # 数据目录
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '../../data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据文件路径
        self.skills_file = os.path.join(self.data_dir, 'skills_database.json')
        self.careers_file = os.path.join(self.data_dir, 'career_paths.json')
        self.profiles_file = os.path.join(self.data_dir, 'ai_profiles.json')
        self.learning_paths_file = os.path.join(self.data_dir, 'learning_paths.json')
        self.performance_records_file = os.path.join(self.data_dir, 'performance_records.json')
        
        # 数据结构
        self.skills_database = {}
        self.career_paths = {}
        self.ai_profiles = {}
        self.learning_paths = {}
        self.performance_records = {}
        self.learning_resources = {}
        self.maintenance_records = {}
        
        # 加载数据
        self._load_data()
        
        # 初始化默认数据
        self._initialize_default_skills()
        self._initialize_default_career_paths()
        self._initialize_default_learning_paths()
        
        # 保存数据
        self._save_data()
        
        logger.info("优化版AI职业介绍所初始化完成")
    
    # 数据持久化方法
    
    def _load_data(self):
        """从文件加载数据"""
        try:
            if os.path.exists(self.skills_file):
                with open(self.skills_file, 'r', encoding='utf-8') as f:
                    self.skills_database = json.load(f)
                logger.info(f"技能数据加载成功: {len(self.skills_database)} 条")
            
            if os.path.exists(self.careers_file):
                with open(self.careers_file, 'r', encoding='utf-8') as f:
                    self.career_paths = json.load(f)
                logger.info(f"职业路径数据加载成功: {len(self.career_paths)} 条")
            
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    self.ai_profiles = json.load(f)
                logger.info(f"AI档案数据加载成功: {len(self.ai_profiles)} 条")
            
            if os.path.exists(self.learning_paths_file):
                with open(self.learning_paths_file, 'r', encoding='utf-8') as f:
                    self.learning_paths = json.load(f)
                logger.info(f"学习路径数据加载成功: {len(self.learning_paths)} 条")
            
            if os.path.exists(self.performance_records_file):
                with open(self.performance_records_file, 'r', encoding='utf-8') as f:
                    self.performance_records = json.load(f)
                logger.info(f"性能记录数据加载成功: {len(self.performance_records)} 条")
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.skills_file, 'w', encoding='utf-8') as f:
                json.dump(self.skills_database, f, ensure_ascii=False, indent=2)
            
            with open(self.careers_file, 'w', encoding='utf-8') as f:
                json.dump(self.career_paths, f, ensure_ascii=False, indent=2)
            
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_profiles, f, ensure_ascii=False, indent=2)
            
            with open(self.learning_paths_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_paths, f, ensure_ascii=False, indent=2)
            
            with open(self.performance_records_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_records, f, ensure_ascii=False, indent=2)
            
            logger.info("数据保存成功")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
    
    # 技能管理方法
    
    def add_skill(self, skill_id: str, skill_name: str, description: str, 
                  category: str, level: str, prerequisites: List[str] = None) -> bool:
        """添加技能到技能数据库"""
        try:
            self.skills_database[skill_id] = {
                'skill_id': skill_id,
                'skill_name': skill_name,
                'description': description,
                'category': category,
                'level': level,
                'prerequisites': prerequisites or [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self._save_data()
            logger.info(f"技能添加成功: {skill_name}")
            return True
        except Exception as e:
            logger.error(f"添加技能失败: {str(e)}")
            return False
    
    def search_skills(self, keyword: str = None, category: str = None, 
                      level: str = None) -> List[Dict[str, Any]]:
        """搜索技能"""
        results = []
        for skill_id, skill in self.skills_database.items():
            match = True
            if keyword:
                keyword = keyword.lower()
                if keyword not in skill['skill_name'].lower() and \
                   keyword not in skill['description'].lower():
                    match = False
            if category and skill['category'] != category:
                match = False
            if level and skill['level'] != level:
                match = False
            if match:
                results.append(skill)
        return results
    
    # 职业路径管理方法
    
    def add_career_path(self, path_id: str, path_name: str, required_skills: List[str], 
                        description: str, recommended_skills: List[str] = None) -> bool:
        """添加职业路径"""
        try:
            self.career_paths[path_id] = {
                'path_id': path_id,
                'path_name': path_name,
                'required_skills': required_skills,
                'recommended_skills': recommended_skills or [],
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self._save_data()
            logger.info(f"职业路径添加成功: {path_name}")
            return True
        except Exception as e:
            logger.error(f"添加职业路径失败: {str(e)}")
            return False
    
    def search_career_paths(self, keyword: str = None, 
                            has_skill: str = None) -> List[Dict[str, Any]]:
        """搜索职业路径"""
        results = []
        for path_id, path in self.career_paths.items():
            match = True
            if keyword:
                keyword = keyword.lower()
                if keyword not in path['path_name'].lower() and \
                   keyword not in path['description'].lower():
                    match = False
            if has_skill and has_skill not in path['required_skills']:
                match = False
            if match:
                results.append(path)
        return results
    
    # AI档案管理方法
    
    def register_ai(self, ai_instance_id: str, ai_type: str, ai_name: str,
                   current_skills: List[str] = None, current_career: str = None) -> bool:
        """注册AI到职业介绍所"""
        try:
            self.ai_profiles[ai_instance_id] = {
                'ai_instance_id': ai_instance_id,
                'ai_type': ai_type,
                'ai_name': ai_name,
                'current_skills': current_skills or [],
                'current_career': current_career,
                'skill_mastery': {},
                'learning_progress': {},
                'registered_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self._save_data()
            logger.info(f"AI注册成功: {ai_instance_id} ({ai_name})")
            return True
        except Exception as e:
            logger.error(f"注册AI失败: {str(e)}")
            return False
    
    def get_all_ai_profiles(self) -> List[Dict[str, Any]]:
        """获取所有AI档案"""
        return list(self.ai_profiles.values())
    
    # AI赋能方法
    
    def empower_ai(self, ai_instance_id: str, skills: List[str]) -> Dict[str, Any]:
        """给AI赋能，添加新技能"""
        result = {
            'success': False,
            'added_skills': [],
            'failed_skills': [],
            'prerequisite_issues': []
        }
        
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                result['error'] = 'AI不存在'
                return result
            
            for skill_id in skills:
                if skill_id not in self.skills_database:
                    logger.warning(f"技能不存在: {skill_id}")
                    result['failed_skills'].append(skill_id)
                    continue
                
                # 检查前置技能
                skill = self.skills_database[skill_id]
                prerequisites = skill.get('prerequisites', [])
                missing_prereqs = [pr for pr in prerequisites 
                                  if pr not in self.ai_profiles[ai_instance_id]['current_skills']]
                
                if missing_prereqs:
                    result['prerequisite_issues'].append({
                        'skill_id': skill_id,
                        'missing_prerequisites': missing_prereqs
                    })
                    result['failed_skills'].append(skill_id)
                    continue
                
                # 添加技能
                if skill_id not in self.ai_profiles[ai_instance_id]['current_skills']:
                    self.ai_profiles[ai_instance_id]['current_skills'].append(skill_id)
                    self.ai_profiles[ai_instance_id]['skill_mastery'][skill_id] = {
                        'level': 'beginner',
                        'acquired_at': datetime.now().isoformat(),
                        'practice_count': 0
                    }
                    result['added_skills'].append(skill_id)
                    logger.info(f"AI {ai_instance_id} 获得新技能: {skill['skill_name']}")
            
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            self._save_data()
            result['success'] = len(result['added_skills']) > 0 or len(result['failed_skills']) == 0
            logger.info(f"AI赋能完成: {result}")
            return result
        except Exception as e:
            logger.error(f"赋能AI失败: {str(e)}")
            result['error'] = str(e)
            return result
    
    # 学习路径管理
    
    def add_learning_path(self, path_id: str, path_name: str, 
                          target_career: str, skill_sequence: List[str]) -> bool:
        """添加学习路径"""
        try:
            self.learning_paths[path_id] = {
                'path_id': path_id,
                'path_name': path_name,
                'target_career': target_career,
                'skill_sequence': skill_sequence,
                'created_at': datetime.now().isoformat()
            }
            self._save_data()
            logger.info(f"学习路径添加成功: {path_name}")
            return True
        except Exception as e:
            logger.error(f"添加学习路径失败: {str(e)}")
            return False
    
    def track_learning_progress(self, ai_instance_id: str, 
                               learning_path_id: str) -> Dict[str, Any]:
        """跟踪学习进度"""
        try:
            if ai_instance_id not in self.ai_profiles:
                return {'error': 'AI不存在'}
            
            if learning_path_id not in self.learning_paths:
                return {'error': '学习路径不存在'}
            
            learning_path = self.learning_paths[learning_path_id]
            ai_profile = self.ai_profiles[ai_instance_id]
            current_skills = set(ai_profile['current_skills'])
            
            # 计算进度
            completed_skills = []
            pending_skills = []
            
            for skill_id in learning_path['skill_sequence']:
                if skill_id in current_skills:
                    completed_skills.append(skill_id)
                else:
                    pending_skills.append(skill_id)
            
            progress = {
                'ai_instance_id': ai_instance_id,
                'learning_path_id': learning_path_id,
                'learning_path_name': learning_path['path_name'],
                'total_skills': len(learning_path['skill_sequence']),
                'completed_skills': len(completed_skills),
                'pending_skills': pending_skills,
                'progress_percentage': (len(completed_skills) / len(learning_path['skill_sequence']) * 100 
                                       if learning_path['skill_sequence'] else 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # 保存进度
            ai_profile['learning_progress'][learning_path_id] = progress
            self._save_data()
            
            return progress
        except Exception as e:
            logger.error(f"跟踪学习进度失败: {str(e)}")
            return {'error': str(e)}
    
    # 性能评估方法
    
    def record_performance(self, ai_instance_id: str, skill_id: str, 
                          performance_score: float, task_type: str,
                          details: Dict[str, Any] = None) -> bool:
        """记录AI性能表现"""
        try:
            if ai_instance_id not in self.ai_profiles:
                logger.error(f"AI不存在: {ai_instance_id}")
                return False
            
            record_id = f"perf_{ai_instance_id}_{datetime.now().timestamp()}"
            self.performance_records[record_id] = {
                'record_id': record_id,
                'ai_instance_id': ai_instance_id,
                'skill_id': skill_id,
                'performance_score': performance_score,
                'task_type': task_type,
                'details': details or {},
                'recorded_at': datetime.now().isoformat()
            }
            
            # 更新技能熟练度
            if skill_id in self.ai_profiles[ai_instance_id]['skill_mastery']:
                mastery = self.ai_profiles[ai_instance_id]['skill_mastery'][skill_id]
                mastery['practice_count'] = mastery.get('practice_count', 0) + 1
                
                # 根据表现更新等级
                if performance_score >= 0.9:
                    mastery['level'] = 'expert'
                elif performance_score >= 0.7:
                    mastery['level'] = 'intermediate'
                else:
                    mastery['level'] = 'beginner'
            
            self.ai_profiles[ai_instance_id]['last_updated'] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"性能记录成功: {ai_instance_id} - {skill_id}")
            return True
        except Exception as e:
            logger.error(f"记录性能失败: {str(e)}")
            return False
    
    def get_ai_performance_summary(self, ai_instance_id: str) -> Dict[str, Any]:
        """获取AI性能总结"""
        try:
            if ai_instance_id not in self.ai_profiles:
                return {'error': 'AI不存在'}
            
            # 获取该AI的所有性能记录
            ai_records = [
                record for record in self.performance_records.values()
                if record['ai_instance_id'] == ai_instance_id
            ]
            
            # 按技能分组统计
            skill_stats = {}
            for record in ai_records:
                skill_id = record['skill_id']
                if skill_id not in skill_stats:
                    skill_stats[skill_id] = {'scores': [], 'count': 0}
                skill_stats[skill_id]['scores'].append(record['performance_score'])
                skill_stats[skill_id]['count'] += 1
            
            # 计算平均分数
            summary = {
                'ai_instance_id': ai_instance_id,
                'total_records': len(ai_records),
                'skill_summary': {},
                'overall_average': 0.0
            }
            
            total_score = 0.0
            for skill_id, stats in skill_stats.items():
                avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                summary['skill_summary'][skill_id] = {
                    'average_score': avg_score,
                    'practice_count': stats['count']
                }
                total_score += avg_score
            
            if skill_stats:
                summary['overall_average'] = total_score / len(skill_stats)
            
            return summary
        except Exception as e:
            logger.error(f"获取性能总结失败: {str(e)}")
            return {'error': str(e)}
    
    # 统计和报告方法
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            stats = {
                'total_skills': len(self.skills_database),
                'total_career_paths': len(self.career_paths),
                'total_ai_profiles': len(self.ai_profiles),
                'total_learning_paths': len(self.learning_paths),
                'total_performance_records': len(self.performance_records),
                'skills_by_category': {},
                'ais_by_type': {},
                'generated_at': datetime.now().isoformat()
            }
            
            # 按类别统计技能
            for skill in self.skills_database.values():
                category = skill['category']
                if category not in stats['skills_by_category']:
                    stats['skills_by_category'][category] = 0
                stats['skills_by_category'][category] += 1
            
            # 按类型统计AI
            for profile in self.ai_profiles.values():
                ai_type = profile['ai_type']
                if ai_type not in stats['ais_by_type']:
                    stats['ais_by_type'][ai_type] = 0
                stats['ais_by_type'][ai_type] += 1
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {'error': str(e)}
    
    # 默认数据初始化
    
    def _initialize_default_skills(self):
        """初始化默认技能"""
        default_skills = [
            # Git相关技能
            {
                'skill_id': 'git_basic',
                'skill_name': 'Git基础操作',
                'description': '掌握Git基本命令，如clone, add, commit, push, pull等',
                'category': 'Git',
                'level': '初级',
                'prerequisites': []
            },
            {
                'skill_id': 'git_branching',
                'skill_name': 'Git分支管理',
                'description': '熟练使用Git分支，包括创建、切换、合并分支等',
                'category': 'Git',
                'level': '中级',
                'prerequisites': ['git_basic']
            },
            {
                'skill_id': 'git_workflow',
                'skill_name': 'Git工作流',
                'description': '掌握Git Flow、GitHub Flow等工作流，能够制定分支策略',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic', 'git_branching']
            },
            {
                'skill_id': 'git_conflict',
                'skill_name': 'Git冲突解决',
                'description': '能够有效检测和解决Git合并冲突',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic', 'git_branching']
            },
            {
                'skill_id': 'git_history',
                'skill_name': 'Git历史分析',
                'description': '能够分析Git提交历史，进行版本追踪和代码审计',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic']
            },
            {
                'skill_id': 'git_automation',
                'skill_name': 'Git自动化',
                'description': '能够自动化Git操作，如自动提交、版本标签生成等',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic', 'git_branching']
            },
            
            # Python相关技能
            {
                'skill_id': 'python_basic',
                'skill_name': 'Python基础',
                'description': '掌握Python基础语法、数据类型、控制结构等',
                'category': 'Python',
                'level': '初级',
                'prerequisites': []
            },
            {
                'skill_id': 'python_oop',
                'skill_name': 'Python面向对象编程',
                'description': '掌握Python类、对象、继承、多态等面向对象概念',
                'category': 'Python',
                'level': '中级',
                'prerequisites': ['python_basic']
            },
            {
                'skill_id': 'python_web',
                'skill_name': 'Python Web开发',
                'description': '使用Flask、Django等框架进行Web开发',
                'category': 'Python',
                'level': '高级',
                'prerequisites': ['python_basic', 'python_oop']
            },
            
            # 教学相关技能
            {
                'skill_id': 'teaching_basic',
                'skill_name': '基础教学能力',
                'description': '掌握基本的教学方法和知识传授技巧',
                'category': '教学',
                'level': '初级',
                'prerequisites': []
            },
            {
                'skill_id': 'error_analysis',
                'skill_name': '错题分析',
                'description': '能够分析学生错题，找出知识薄弱点',
                'category': '教学',
                'level': '中级',
                'prerequisites': ['teaching_basic']
            },
            {
                'skill_id': 'personalized_feedback',
                'skill_name': '个性化反馈',
                'description': '能够根据学生情况提供个性化学习建议',
                'category': '教学',
                'level': '高级',
                'prerequisites': ['teaching_basic', 'error_analysis']
            },
            
            # 工程相关技能
            {
                'skill_id': 'code_analysis',
                'skill_name': '代码分析',
                'description': '能够分析代码质量，检测潜在问题',
                'category': '工程',
                'level': '中级',
                'prerequisites': []
            },
            {
                'skill_id': 'bug_fixing',
                'skill_name': '错误修复',
                'description': '能够定位和修复代码中的错误',
                'category': '工程',
                'level': '高级',
                'prerequisites': ['code_analysis']
            },
            {
                'skill_id': 'performance_optimization',
                'skill_name': '性能优化',
                'description': '能够分析和优化系统性能',
                'category': '工程',
                'level': '高级',
                'prerequisites': ['code_analysis']
            }
        ]
        
        for skill in default_skills:
            if skill['skill_id'] not in self.skills_database:
                self.add_skill(
                    skill['skill_id'],
                    skill['skill_name'],
                    skill['description'],
                    skill['category'],
                    skill['level'],
                    skill['prerequisites']
                )
        logger.info("默认技能初始化完成")
    
    def _initialize_default_career_paths(self):
        """初始化默认职业路径"""
        default_careers = [
            # Git相关职业
            {
                'path_id': 'git_basic_user',
                'path_name': 'Git基础用户',
                'required_skills': ['git_basic'],
                'recommended_skills': [],
                'description': '能够使用Git进行基本的版本控制操作'
            },
            {
                'path_id': 'git_branch_manager',
                'path_name': 'Git分支管理员',
                'required_skills': ['git_basic', 'git_branching'],
                'recommended_skills': ['git_conflict'],
                'description': '能够管理Git分支，支持团队协作开发'
            },
            {
                'path_id': 'git_workflow_designer',
                'path_name': 'Git工作流设计师',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow'],
                'recommended_skills': ['git_history', 'git_automation'],
                'description': '能够设计和实施Git工作流，提升团队开发效率'
            },
            {
                'path_id': 'git_expert',
                'path_name': 'Git专家',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow', 
                                    'git_conflict', 'git_history', 'git_automation'],
                'recommended_skills': [],
                'description': '全面掌握Git，能够解决复杂的版本控制问题'
            },
            
            # Python开发者职业
            {
                'path_id': 'python_developer',
                'path_name': 'Python开发者',
                'required_skills': ['python_basic', 'python_oop'],
                'recommended_skills': ['python_web', 'git_basic'],
                'description': '能够使用Python进行软件开发'
            },
            {
                'path_id': 'python_web_developer',
                'path_name': 'Python Web开发者',
                'required_skills': ['python_basic', 'python_oop', 'python_web'],
                'recommended_skills': ['git_basic', 'git_branching'],
                'description': '能够使用Python进行Web应用开发'
            },
            
            # 老师AI职业
            {
                'path_id': 'teacher_assistant',
                'path_name': '教学助理',
                'required_skills': ['teaching_basic'],
                'recommended_skills': ['error_analysis'],
                'description': '能够协助进行教学工作'
            },
            {
                'path_id': 'expert_teacher',
                'path_name': '专家教师',
                'required_skills': ['teaching_basic', 'error_analysis', 'personalized_feedback'],
                'recommended_skills': [],
                'description': '能够提供专业的教学服务和个性化指导'
            },
            
            # 工程师AI职业
            {
                'path_id': 'code_reviewer',
                'path_name': '代码审查员',
                'required_skills': ['code_analysis'],
                'recommended_skills': ['git_basic'],
                'description': '能够审查代码质量'
            },
            {
                'path_id': 'senior_engineer',
                'path_name': '高级工程师',
                'required_skills': ['code_analysis', 'bug_fixing', 'performance_optimization'],
                'recommended_skills': ['git_basic', 'git_branching'],
                'description': '能够解决复杂的技术问题和优化系统性能'
            }
        ]
        
        for career in default_careers:
            if career['path_id'] not in self.career_paths:
                self.add_career_path(
                    career['path_id'],
                    career['path_name'],
                    career['required_skills'],
                    career['description'],
                    career['recommended_skills']
                )
        logger.info("默认职业路径初始化完成")
    
    def _initialize_default_learning_paths(self):
        """初始化默认学习路径"""
        default_paths = [
            {
                'path_id': 'learn_git_expert',
                'path_name': 'Git专家成长路径',
                'target_career': 'git_expert',
                'skill_sequence': ['git_basic', 'git_branching', 'git_workflow', 
                                   'git_conflict', 'git_history', 'git_automation']
            },
            {
                'path_id': 'learn_python_web',
                'path_name': 'Python Web开发者路径',
                'target_career': 'python_web_developer',
                'skill_sequence': ['python_basic', 'python_oop', 'python_web', 'git_basic']
            },
            {
                'path_id': 'learn_expert_teacher',
                'path_name': '专家教师成长路径',
                'target_career': 'expert_teacher',
                'skill_sequence': ['teaching_basic', 'error_analysis', 'personalized_feedback']
            },
            {
                'path_id': 'learn_senior_engineer',
                'path_name': '高级工程师成长路径',
                'target_career': 'senior_engineer',
                'skill_sequence': ['code_analysis', 'bug_fixing', 'performance_optimization', 'git_basic']
            }
        ]
        
        for path in default_paths:
            if path['path_id'] not in self.learning_paths:
                self.add_learning_path(
                    path['path_id'],
                    path['path_name'],
                    path['target_career'],
                    path['skill_sequence']
                )
        logger.info("默认学习路径初始化完成")

# 创建全局优化版AI职业介绍所实例
ai_career_center_optimized = AICareerCenterOptimized()

if __name__ == '__main__':
    print("优化版AI职业介绍所初始化成功")
    print(f"技能数量: {len(ai_career_center_optimized.skills_database)}")
    print(f"职业路径数量: {len(ai_career_center_optimized.career_paths)}")
    print(f"学习路径数量: {len(ai_career_center_optimized.learning_paths)}")
