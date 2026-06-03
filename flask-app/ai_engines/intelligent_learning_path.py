# -*- coding: utf-8 -*-
"""
MTSCOS 智能学习路径规划系统
基于知识图谱和用户学习情况，生成个性化学习路径
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('learning_path')

class LearningObjective:
    """学习目标"""
    
    def __init__(self, topic_id: str, topic_name: str, subject: str, difficulty: float):
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.subject = subject
        self.difficulty = difficulty
        self.prerequisites = []
        self.dependencies = []
        self.estimated_hours = difficulty * 8
        self.status = 'pending'
        self.progress = 0.0
    
    def to_dict(self):
        return {
            'topic_id': self.topic_id,
            'topic_name': self.topic_name,
            'subject': self.subject,
            'difficulty': self.difficulty,
            'prerequisites': self.prerequisites,
            'dependencies': self.dependencies,
            'estimated_hours': self.estimated_hours,
            'status': self.status,
            'progress': self.progress
        }

class LearningPathNode:
    """学习路径节点"""
    
    def __init__(self, objective: LearningObjective, order: int):
        self.objective = objective
        self.order = order
        self.duration_hours = objective.estimated_hours
        self.recommended_date = None
        self.completion_date = None
        self.resources = []
        self.assessments = []
    
    def to_dict(self):
        return {
            'order': self.order,
            'objective': self.objective.to_dict(),
            'duration_hours': self.duration_hours,
            'recommended_date': self.recommended_date.isoformat() if self.recommended_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'resources': self.resources,
            'assessments': self.assessments
        }

class IntelligentLearningPath:
    """智能学习路径规划器"""
    
    def __init__(self):
        self.knowledge_graph = self._build_knowledge_graph()
        self.user_profiles = {}
        logger.info("智能学习路径规划系统初始化完成")
    
    def _build_knowledge_graph(self) -> Dict[str, Any]:
        """构建知识图谱"""
        subjects = {
            '数学': {
                'topics': [
                    {'id': 'math_numbers', 'name': '数与代数基础', 'difficulty': 0.2, 'prereqs': []},
                    {'id': 'math_algebra', 'name': '代数运算', 'difficulty': 0.35, 'prereqs': ['math_numbers']},
                    {'id': 'math_geometry_basic', 'name': '几何基础', 'difficulty': 0.3, 'prereqs': ['math_numbers']},
                    {'id': 'math_equation', 'name': '方程与不等式', 'difficulty': 0.45, 'prereqs': ['math_algebra']},
                    {'id': 'math_function', 'name': '函数', 'difficulty': 0.55, 'prereqs': ['math_equation']},
                    {'id': 'math_geometry', 'name': '几何图形', 'difficulty': 0.5, 'prereqs': ['math_geometry_basic', 'math_algebra']},
                    {'id': 'math_sequence', 'name': '数列', 'difficulty': 0.5, 'prereqs': ['math_algebra']},
                    {'id': 'math_probability', 'name': '概率统计', 'difficulty': 0.55, 'prereqs': ['math_algebra']},
                    {'id': 'math_trigonometry', 'name': '三角函数', 'difficulty': 0.65, 'prereqs': ['math_function', 'math_geometry']},
                    {'id': 'math_calculus', 'name': '微积分基础', 'difficulty': 0.75, 'prereqs': ['math_function', 'math_trigonometry']}
                ]
            },
            '语文': {
                'topics': [
                    {'id': 'chinese_pinyin', 'name': '拼音与识字', 'difficulty': 0.15, 'prereqs': []},
                    {'id': 'chinese_grammar', 'name': '语法基础', 'difficulty': 0.3, 'prereqs': ['chinese_pinyin']},
                    {'id': 'chinese_reading', 'name': '阅读理解', 'difficulty': 0.45, 'prereqs': ['chinese_grammar']},
                    {'id': 'chinese_poetry', 'name': '古诗词', 'difficulty': 0.4, 'prereqs': ['chinese_grammar']},
                    {'id': 'chinese_writing', 'name': '写作基础', 'difficulty': 0.55, 'prereqs': ['chinese_reading']},
                    {'id': 'chinese_essay', 'name': '文言文', 'difficulty': 0.7, 'prereqs': ['chinese_poetry', 'chinese_grammar']},
                    {'id': 'chinese_composition', 'name': '作文写作', 'difficulty': 0.65, 'prereqs': ['chinese_writing']}
                ]
            },
            '英语': {
                'topics': [
                    {'id': 'english_alphabet', 'name': '字母与发音', 'difficulty': 0.15, 'prereqs': []},
                    {'id': 'english_vocabulary', 'name': '词汇基础', 'difficulty': 0.25, 'prereqs': ['english_alphabet']},
                    {'id': 'english_grammar', 'name': '语法基础', 'difficulty': 0.4, 'prereqs': ['english_vocabulary']},
                    {'id': 'english_reading', 'name': '阅读理解', 'difficulty': 0.5, 'prereqs': ['english_vocabulary', 'english_grammar']},
                    {'id': 'english_listening', 'name': '听力', 'difficulty': 0.45, 'prereqs': ['english_vocabulary']},
                    {'id': 'english_writing', 'name': '写作', 'difficulty': 0.6, 'prereqs': ['english_grammar', 'english_reading']},
                    {'id': 'english_speaking', 'name': '口语', 'difficulty': 0.55, 'prereqs': ['english_listening', 'english_vocabulary']}
                ]
            },
            '物理': {
                'topics': [
                    {'id': 'physics_basic', 'name': '物理入门', 'difficulty': 0.25, 'prereqs': []},
                    {'id': 'physics_motion', 'name': '运动学', 'difficulty': 0.45, 'prereqs': ['physics_basic']},
                    {'id': 'physics_forces', 'name': '力学', 'difficulty': 0.5, 'prereqs': ['physics_motion']},
                    {'id': 'physics_energy', 'name': '能量', 'difficulty': 0.55, 'prereqs': ['physics_forces']},
                    {'id': 'physics_electricity', 'name': '电学', 'difficulty': 0.6, 'prereqs': ['physics_energy']},
                    {'id': 'physics_optics', 'name': '光学', 'difficulty': 0.55, 'prereqs': ['physics_basic']}
                ]
            },
            '化学': {
                'topics': [
                    {'id': 'chemistry_basic', 'name': '化学入门', 'difficulty': 0.25, 'prereqs': []},
                    {'id': 'chemistry_elements', 'name': '元素与化合物', 'difficulty': 0.4, 'prereqs': ['chemistry_basic']},
                    {'id': 'chemistry_reactions', 'name': '化学反应', 'difficulty': 0.5, 'prereqs': ['chemistry_elements']},
                    {'id': 'chemistry_periodic', 'name': '元素周期律', 'difficulty': 0.55, 'prereqs': ['chemistry_elements']},
                    {'id': 'chemistry_solution', 'name': '溶液化学', 'difficulty': 0.5, 'prereqs': ['chemistry_reactions']}
                ]
            },
            '生物': {
                'topics': [
                    {'id': 'biology_basic', 'name': '生物入门', 'difficulty': 0.2, 'prereqs': []},
                    {'id': 'biology_cell', 'name': '细胞', 'difficulty': 0.4, 'prereqs': ['biology_basic']},
                    {'id': 'biology_genetics', 'name': '遗传学', 'difficulty': 0.55, 'prereqs': ['biology_cell']},
                    {'id': 'biology_ecology', 'name': '生态学', 'difficulty': 0.45, 'prereqs': ['biology_basic']}
                ]
            },
            '历史': {
                'topics': [
                    {'id': 'history_ancient', 'name': '古代史', 'difficulty': 0.3, 'prereqs': []},
                    {'id': 'history_medieval', 'name': '近代史', 'difficulty': 0.4, 'prereqs': ['history_ancient']},
                    {'id': 'history_modern', 'name': '现代史', 'difficulty': 0.45, 'prereqs': ['history_medieval']}
                ]
            },
            '地理': {
                'topics': [
                    {'id': 'geography_earth', 'name': '地球概论', 'difficulty': 0.25, 'prereqs': []},
                    {'id': 'geography_climate', 'name': '气候与环境', 'difficulty': 0.4, 'prereqs': ['geography_earth']},
                    {'id': 'geography_regions', 'name': '区域地理', 'difficulty': 0.45, 'prereqs': ['geography_climate']}
                ]
            }
        }
        return subjects
    
    def create_user_profile(self, user_id: str, grade: int = 1, education_type: str = 'k12'):
        """创建用户档案"""
        self.user_profiles[user_id] = {
            'user_id': user_id,
            'grade': grade,
            'education_type': education_type,
            'skill_levels': {},
            'completed_topics': [],
            'in_progress_topics': [],
            'learning_goals': [],
            'weekly_hours': 10,
            'learning_style': 'balanced'
        }
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户档案"""
        return self.user_profiles.get(user_id)
    
    def update_user_skill(self, user_id: str, subject: str, level: float):
        """更新用户技能水平"""
        if user_id not in self.user_profiles:
            self.create_user_profile(user_id)
        
        self.user_profiles[user_id]['skill_levels'][subject] = level
    
    def _calculate_topic_order(self, subject: str, user_skills: Dict[str, float]) -> List[str]:
        """计算主题学习顺序"""
        topics = self.knowledge_graph.get(subject, {}).get('topics', [])
        topic_map = {t['id']: t for t in topics}
        
        in_degree = {t['id']: len(t['prereqs']) for t in topics}
        available = [t['id'] for t in topics if len(t['prereqs']) == 0]
        
        order = []
        while available:
            available.sort(key=lambda tid: topic_map[tid]['difficulty'])
            
            best_topic = None
            best_score = float('-inf')
            
            for tid in available:
                topic = topic_map[tid]
                current_skill = user_skills.get(subject, 0.5)
                diff_score = 1 - abs(topic['difficulty'] - current_skill)
                score = diff_score * (1 - topic['difficulty'])
                
                if score > best_score:
                    best_score = score
                    best_topic = tid
            
            if best_topic:
                order.append(best_topic)
                available.remove(best_topic)
                
                for tid in topics:
                    if best_topic in tid.get('prereqs', []):
                        in_degree[tid['id']] -= 1
                        if in_degree[tid['id']] == 0:
                            available.append(tid['id'])
        
        return order
    
    def generate_learning_path(self, user_id: str, subjects: List[str] = None) -> Dict[str, Any]:
        """生成学习路径"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return {'error': '用户档案不存在'}
        
        if not subjects:
            subjects = list(self.knowledge_graph.keys())
        
        path = []
        total_duration = 0
        current_date = datetime.now()
        
        for subject in subjects:
            topic_order = self._calculate_topic_order(subject, profile['skill_levels'])
            
            topics = self.knowledge_graph.get(subject, {}).get('topics', [])
            topic_map = {t['id']: t for t in topics}
            
            for idx, topic_id in enumerate(topic_order):
                topic = topic_map.get(topic_id)
                if not topic:
                    continue
                
                objective = LearningObjective(
                    topic_id=topic_id,
                    topic_name=topic['name'],
                    subject=subject,
                    difficulty=topic['difficulty']
                )
                objective.prerequisites = topic['prereqs']
                
                status = 'completed' if topic_id in profile['completed_topics'] else \
                         'in_progress' if topic_id in profile['in_progress_topics'] else 'pending'
                
                objective.status = status
                objective.progress = 1.0 if status == 'completed' else \
                                   0.5 if status == 'in_progress' else 0.0
                
                node = LearningPathNode(objective, idx + 1)
                node.duration_hours = objective.estimated_hours
                node.recommended_date = current_date
                
                weekly_hours = profile.get('weekly_hours', 10)
                days_needed = (objective.estimated_hours / weekly_hours) * 7
                current_date = current_date.replace(hour=0, minute=0, second=0) + \
                              timedelta(days=days_needed)
                
                node.resources = self._get_resources(subject, topic_id)
                node.assessments = self._get_assessments(subject, topic_id)
                
                path.append(node.to_dict())
                total_duration += objective.estimated_hours
        
        return {
            'user_id': user_id,
            'grade': profile['grade'],
            'subjects': subjects,
            'path': path,
            'total_duration_hours': total_duration,
            'estimated_weeks': round(total_duration / profile.get('weekly_hours', 10)),
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_resources(self, subject: str, topic_id: str) -> List[Dict[str, Any]]:
        """获取学习资源"""
        return [
            {'type': 'video', 'title': f'{subject} - {topic_id} 教学视频', 'duration': '30分钟'},
            {'type': 'exercise', 'title': f'{subject} - {topic_id} 练习题', 'count': 15},
            {'type': 'article', 'title': f'{subject} - {topic_id} 知识点讲解'}
        ]
    
    def _get_assessments(self, subject: str, topic_id: str) -> List[Dict[str, Any]]:
        """获取评估项目"""
        return [
            {'type': 'quiz', 'title': f'{subject} - {topic_id} 小测验', 'questions': 10},
            {'type': 'homework', 'title': f'{subject} - {topic_id} 作业', 'questions': 5},
            {'type': 'project', 'title': f'{subject} - {topic_id} 实践项目', 'description': '完成相关实践任务'}
        ]
    
    def get_path_progress(self, user_id: str) -> Dict[str, Any]:
        """获取学习路径进度"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return {'error': '用户档案不存在'}
        
        completed = len(profile['completed_topics'])
        in_progress = len(profile['in_progress_topics'])
        
        all_topics = []
        for subject in self.knowledge_graph.values():
            all_topics.extend(subject.get('topics', []))
        
        total = len(all_topics)
        
        return {
            'user_id': user_id,
            'completed_topics': profile['completed_topics'],
            'in_progress_topics': profile['in_progress_topics'],
            'completed_count': completed,
            'in_progress_count': in_progress,
            'total_topics': total,
            'progress_percentage': round((completed / total) * 100, 2) if total > 0 else 0,
            'skill_levels': profile['skill_levels']
        }
    
    def mark_topic_completed(self, user_id: str, topic_id: str, score: float = None):
        """标记主题完成"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False
        
        if topic_id in profile['in_progress_topics']:
            profile['in_progress_topics'].remove(topic_id)
        
        if topic_id not in profile['completed_topics']:
            profile['completed_topics'].append(topic_id)
        
        if score is not None:
            for subject, topics in self.knowledge_graph.items():
                for topic in topics.get('topics', []):
                    if topic['id'] == topic_id:
                        current_level = profile['skill_levels'].get(subject, 0.5)
                        new_level = min(0.95, current_level + (score / 100) * 0.1)
                        profile['skill_levels'][subject] = new_level
                        break
        
        logger.info(f"用户 {user_id} 完成主题: {topic_id}")
        return True
    
    def suggest_next_topic(self, user_id: str) -> Optional[Dict[str, Any]]:
        """推荐下一个学习主题"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
        
        path = self.generate_learning_path(user_id)
        
        for node in path.get('path', []):
            if node['objective']['status'] == 'pending':
                return node['objective']
        
        return None

intelligent_learning_path = IntelligentLearningPath()

if __name__ == '__main__':
    planner = IntelligentLearningPath()
    
    planner.create_user_profile('student_001', grade=7, education_type='k12')
    planner.update_user_skill('student_001', '数学', 0.6)
    planner.update_user_skill('student_001', '语文', 0.7)
    
    print("=== 生成学习路径 ===")
    path = planner.generate_learning_path('student_001', ['数学', '语文'])
    print(json.dumps(path, indent=2, ensure_ascii=False))
    
    print("\n=== 获取学习进度 ===")
    progress = planner.get_path_progress('student_001')
    print(json.dumps(progress, indent=2, ensure_ascii=False))
    
    print("\n=== 推荐下一个学习主题 ===")
    next_topic = planner.suggest_next_topic('student_001')
    print(json.dumps(next_topic, indent=2, ensure_ascii=False))
    
    print("\n=== 标记主题完成 ===")
    planner.mark_topic_completed('student_001', 'math_numbers', 95)
    
    print("\n=== 更新后的进度 ===")
    progress = planner.get_path_progress('student_001')
    print(json.dumps(progress, indent=2, ensure_ascii=False))