# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版AI职业介绍所模块
包含数据库持久化,技能学习路径,性能评估,搜索过滤等增强功能
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger('ai_career_center_optimized')

class AICareerCenterOptimized:
    """优化版AI职业介绍所类"""

    def __init__(self, data_dir: str = None):
        """初始化优化版AI职业介绍所"""
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '../../data')
        os.makedirs(self.data_dir, exist_ok=True)

        self.skills_file = os.path.join(self.data_dir, 'skills_database.json')
        self.careers_file = os.path.join(self.data_dir, 'career_paths.json')
        self.profiles_file = os.path.join(self.data_dir, 'ai_profiles.json')
        self.learning_paths_file = os.path.join(self.data_dir, 'learning_paths.json')
        self.performance_records_file = os.path.join(self.data_dir, 'performance_records.json')

        self.skills_database = {}
        self.career_paths = {}
        self.ai_profiles = {}
        self.learning_paths = {}
        self.performance_records = {}
        self.learning_resources = {}
        self.maintenance_records = {}

        self._load_data()

        self._initialize_default_skills()
        self._initialize_default_career_paths()
        self._initialize_default_learning_paths()

        self._save_data()

        logger.info("优化版AI职业介绍所初始化完成")

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
            return True
        except Exception as e:
            logger.error(f"添加技能失败: {str(e)}")
            return False

    def _initialize_default_skills(self):
        """初始化默认技能"""
        default_skills = [
            {
                'skill_id': 'git_basic',
                'skill_name': 'Git基础操作',
                'description': '掌握Git基本命令,如clone, add, commit, push, pull等',
                'category': 'Git',
                'level': '初级',
                'prerequisites': []
            },
            {
                'skill_id': 'git_branching',
                'skill_name': 'Git分支管理',
                'description': '熟练使用Git分支,包括创建,切换,合并分支等',
                'category': 'Git',
                'level': '中级',
                'prerequisites': ['git_basic']
            },
            {
                'skill_id': 'git_workflow',
                'skill_name': 'Git工作流',
                'description': '掌握Git Flow,GitHub Flow等工作流,能够制定分支策略',
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
                'description': '能够分析Git提交历史,进行版本追踪和代码审计',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic']
            },
            {
                'skill_id': 'git_automation',
                'skill_name': 'Git自动化',
                'description': '能够自动化Git操作,如自动提交,版本标签生成等',
                'category': 'Git',
                'level': '高级',
                'prerequisites': ['git_basic', 'git_branching']
            },
            {
                'skill_id': 'python_basic',
                'skill_name': 'Python基础',
                'description': '掌握Python基础语法,数据类型,控制结构等',
                'category': 'Python',
                'level': '初级',
                'prerequisites': []
            },
            {
                'skill_id': 'python_oop',
                'skill_name': 'Python面向对象',
                'description': '掌握Python类,对象,继承,多态等面向对象概念',
                'category': 'Python',
                'level': '中级',
                'prerequisites': ['python_basic']
            },
            {
                'skill_id': 'python_web',
                'skill_name': 'Python Web开发',
                'description': '使用Flask,Django等框架进行Web开发',
                'category': 'Python',
                'level': '高级',
                'prerequisites': ['python_basic', 'python_oop']
            },
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
                'description': '能够分析学生错题,找出知识薄弱点',
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
            {
                'skill_id': 'code_analysis',
                'skill_name': '代码分析',
                'description': '能够分析代码质量,检测潜在问题',
                'category': '工程',
                'level': '中级',
                'prerequisites': []
            },
            {
                'skill_id': 'bug_fixing',
                'skill_name': 'Bug修复',
                'description': '能够定位和修复代码中的错误',
                'category': '工程',
                'level': '高级',
                'prerequisites': ['code_analysis']
            },
            {
                'skill_id': 'performance_optimization',
                'skill_name': '性能优化',
                'description': '能够优化系统性能',
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
                'recommended_skills': [],
                'description': '能够管理Git分支'
            },
            {
                'path_id': 'git_workflow_designer',
                'path_name': 'Git工作流设计师',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow'],
                'recommended_skills': ['git_history', 'git_automation'],
                'description': '能够设计和实施Git工作流,提升团队开发效率'
            },
            {
                'path_id': 'git_expert',
                'path_name': 'Git专家',
                'required_skills': ['git_basic', 'git_branching', 'git_workflow', 'git_conflict', 'git_history', 'git_automation'],
                'recommended_skills': [],
                'description': '全面掌握Git,能够解决复杂的版本控制问题'
            },
            {
                'path_id': 'python_developer',
                'path_name': 'Python开发者',
                'required_skills': ['python_basic', 'python_oop'],
                'recommended_skills': [],
                'description': '能够使用Python进行软件开发'
            },
            {
                'path_id': 'python_web_developer',
                'path_name': 'Python Web开发者',
                'required_skills': ['python_basic', 'python_oop', 'python_web'],
                'recommended_skills': ['git_basic', 'git_branching'],
                'description': '能够使用Python进行Web开发'
            },
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
            {
                'path_id': 'code_reviewer',
                'path_name': '代码审查员',
                'required_skills': ['code_analysis'],
                'recommended_skills': [],
                'description': '能够审查代码质量'
            },
            {
                'path_id': 'senior_engineer',
                'path_name': '高级工程师',
                'required_skills': ['code_analysis', 'bug_fixing', 'performance_optimization'],
                'recommended_skills': ['git_basic', 'git_branching'],
                'description': '能够解决复杂的工程问题'
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
                'created_at': datetime.now().isoformat()
            }
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"添加职业路径失败: {str(e)}")
            return False

    def _initialize_default_learning_paths(self):
        """初始化默认学习路径"""
        default_paths = [
            {
                'path_id': 'learn_git_expert',
                'path_name': 'Git专家成长路径',
                'target_career': 'git_expert',
                'skill_sequence': ['git_basic', 'git_branching', 'git_workflow', 'git_conflict', 'git_history', 'git_automation']
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

    def add_learning_path(self, path_id: str, path_name: str, target_career: str,
                          skill_sequence: List[str]) -> bool:
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
            return True
        except Exception as e:
            logger.error(f"添加学习路径失败: {str(e)}")
            return False


ai_career_center_optimized = AICareerCenterOptimized()

if __name__ == '__main__':
    print("优化版AI职业介绍所初始化成功")
    print(f"技能数量: {len(ai_career_center_optimized.skills_database)}")
    print(f"职业路径数量: {len(ai_career_center_optimized.career_paths)}")
    print(f"学习路径数量: {len(ai_career_center_optimized.learning_paths)}")
