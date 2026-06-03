# -*- coding: utf-8 -*-
"""
MTSCOS AI引擎 v4.0 - 核心能力增强版
集成智能学习推荐、自适应学习、知识图谱、智能评估等核心能力
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ai_engine_v4')

class LearningProfile:
    """学习档案 - 记录用户学习行为和能力状态"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.skill_levels = {}
        self.learning_history = []
        self.preferences = {}
        self.weak_points = []
        self.strong_points = []
        self.last_update = datetime.now()
    
    def update_skill(self, subject: str, level: float, confidence: float = 0.9):
        """更新技能水平"""
        self.skill_levels[subject] = {
            'level': level,
            'confidence': confidence,
            'last_practiced': datetime.now().isoformat()
        }
    
    def add_learning_record(self, record: Dict[str, Any]):
        """添加学习记录"""
        self.learning_history.append({
            **record,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-1000:]
    
    def identify_weak_points(self, threshold: float = 0.6) -> List[str]:
        """识别薄弱环节"""
        self.weak_points = [
            subject for subject, data in self.skill_levels.items()
            if data['level'] < threshold
        ]
        return self.weak_points
    
    def identify_strong_points(self, threshold: float = 0.85) -> List[str]:
        """识别强项"""
        self.strong_points = [
            subject for subject, data in self.skill_levels.items()
            if data['level'] >= threshold
        ]
        return self.strong_points

class KnowledgeGraph:
    """知识图谱 - 管理知识点关联关系"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.prerequisites = {}
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """加载知识库"""
        subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '道德与法治']
        
        for subject in subjects:
            self.nodes[subject] = {
                'subject': subject,
                'topics': [],
                'difficulty': 0.5,
                'importance': 1.0
            }
        
        math_topics = [
            {'id': 'math_algebra', 'name': '代数', 'difficulty': 0.4},
            {'id': 'math_geometry', 'name': '几何', 'difficulty': 0.5},
            {'id': 'math_function', 'name': '函数', 'difficulty': 0.6},
            {'id': 'math_probability', 'name': '概率统计', 'difficulty': 0.55},
            {'id': 'math_sequence', 'name': '数列', 'difficulty': 0.5},
            {'id': 'math_trigonometry', 'name': '三角函数', 'difficulty': 0.65},
            {'id': 'math_calculus', 'name': '微积分基础', 'difficulty': 0.75}
        ]
        self.nodes['数学']['topics'] = math_topics
        
        chinese_topics = [
            {'id': 'chinese_reading', 'name': '阅读理解', 'difficulty': 0.5},
            {'id': 'chinese_writing', 'name': '写作', 'difficulty': 0.6},
            {'id': 'chinese_poetry', 'name': '古诗词', 'difficulty': 0.45},
            {'id': 'chinese_grammar', 'name': '语法', 'difficulty': 0.4},
            {'id': 'chinese_essay', 'name': '文言文', 'difficulty': 0.7}
        ]
        self.nodes['语文']['topics'] = chinese_topics
        
        english_topics = [
            {'id': 'english_vocabulary', 'name': '词汇', 'difficulty': 0.35},
            {'id': 'english_grammar', 'name': '语法', 'difficulty': 0.5},
            {'id': 'english_reading', 'name': '阅读理解', 'difficulty': 0.55},
            {'id': 'english_writing', 'name': '写作', 'difficulty': 0.65},
            {'id': 'english_listening', 'name': '听力', 'difficulty': 0.5},
            {'id': 'english_speaking', 'name': '口语', 'difficulty': 0.6}
        ]
        self.nodes['英语']['topics'] = english_topics
        
        self.prerequisites = {
            'math_function': ['math_algebra'],
            'math_trigonometry': ['math_algebra', 'math_function'],
            'math_calculus': ['math_function', 'math_trigonometry'],
            'math_probability': ['math_algebra'],
            'chinese_essay': ['chinese_grammar', 'chinese_poetry'],
            'chinese_writing': ['chinese_reading', 'chinese_grammar'],
            'english_writing': ['english_vocabulary', 'english_grammar'],
            'english_reading': ['english_vocabulary', 'english_grammar']
        }
    
    def get_prerequisites(self, topic_id: str) -> List[str]:
        """获取知识点的前置依赖"""
        return self.prerequisites.get(topic_id, [])
    
    def calculate_topic_difficulty(self, topic_id: str) -> float:
        """计算知识点难度(考虑前置依赖)"""
        prereqs = self.get_prerequisites(topic_id)
        base_difficulty = 0.5
        
        for subject, data in self.nodes.items():
            for topic in data['topics']:
                if topic['id'] == topic_id:
                    base_difficulty = topic['difficulty']
                    break
        
        if prereqs:
            base_difficulty += len(prereqs) * 0.05
        
        return min(base_difficulty, 0.95)

class AILearningRecommender:
    """AI学习推荐系统 v4.0"""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.user_profiles = {}
        self.recommendation_history = []
        logger.info("AI学习推荐系统 v4.0 初始化完成")
    
    def get_or_create_profile(self, user_id: str) -> LearningProfile:
        """获取或创建用户学习档案"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = LearningProfile(user_id)
        return self.user_profiles[user_id]
    
    def analyze_learning_pattern(self, user_id: str) -> Dict[str, Any]:
        """分析用户学习模式"""
        profile = self.get_or_create_profile(user_id)
        
        pattern = {
            'total_learning_time': 0,
            'preferred_time_of_day': 'unknown',
            'preferred_subjects': [],
            'learning_intensity': 'normal',
            'consistency_score': 0.0,
            'skill_levels': profile.skill_levels,
            'weak_points': profile.identify_weak_points(),
            'strong_points': profile.identify_strong_points()
        }
        
        if profile.learning_history:
            total_time = sum(record.get('duration', 0) for record in profile.learning_history)
            pattern['total_learning_time'] = total_time
            
            subject_counts = {}
            for record in profile.learning_history:
                subject = record.get('subject', 'unknown')
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
            
            if subject_counts:
                pattern['preferred_subjects'] = sorted(
                    subject_counts.keys(), 
                    key=lambda x: subject_counts[x], 
                    reverse=True
                )[:3]
            
            if total_time > 3600:
                pattern['learning_intensity'] = 'high'
            elif total_time < 300:
                pattern['learning_intensity'] = 'low'
        
        return pattern
    
    def generate_personalized_recommendations(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """生成个性化学习推荐"""
        profile = self.get_or_create_profile(user_id)
        pattern = self.analyze_learning_pattern(user_id)
        
        recommendations = []
        weak_points = pattern['weak_points']
        
        if weak_points:
            for subject in weak_points[:3]:
                if subject in self.knowledge_graph.nodes:
                    for topic in self.knowledge_graph.nodes[subject]['topics'][:2]:
                        recommendations.append({
                            'type': 'weak_point',
                            'subject': subject,
                            'topic': topic['name'],
                            'topic_id': topic['id'],
                            'difficulty': topic['difficulty'],
                            'reason': f'检测到{subject}科目存在薄弱环节',
                            'priority': 'high',
                            'estimated_time': int(topic['difficulty'] * 60)
                        })
        
        for subject in pattern['strong_points'][:2]:
            if subject in self.knowledge_graph.nodes:
                advanced_topics = [
                    t for t in self.knowledge_graph.nodes[subject]['topics']
                    if t['difficulty'] > 0.6
                ]
                for topic in advanced_topics[:2]:
                    recommendations.append({
                        'type': 'enhancement',
                        'subject': subject,
                        'topic': topic['name'],
                        'topic_id': topic['id'],
                        'difficulty': topic['difficulty'],
                        'reason': f'{subject}表现优秀，建议进阶学习',
                        'priority': 'medium',
                        'estimated_time': int(topic['difficulty'] * 80)
                    })
        
        return recommendations[:count]
    
    def get_learning_path(self, user_id: str, target_subject: str = None) -> List[Dict[str, Any]]:
        """生成学习路径"""
        profile = self.get_or_create_profile(user_id)
        path = []
        
        if target_subject and target_subject in self.knowledge_graph.nodes:
            topics = self.knowledge_graph.nodes[target_subject]['topics']
            topics_sorted = sorted(topics, key=lambda x: x['difficulty'])
            
            for topic in topics_sorted:
                prereqs = self.knowledge_graph.get_prerequisites(topic['id'])
                current_level = profile.skill_levels.get(target_subject, {}).get('level', 0)
                
                status = 'completed' if current_level >= 0.8 else \
                         'in_progress' if current_level >= 0.4 else 'pending'
                
                path.append({
                    'topic_id': topic['id'],
                    'topic_name': topic['name'],
                    'difficulty': topic['difficulty'],
                    'prerequisites': prereqs,
                    'status': status,
                    'estimated_time': int(topic['difficulty'] * 60)
                })
        
        return path
    
    def update_with_exam_result(self, user_id: str, subject: str, score: float, max_score: float):
        """根据考试结果更新学习档案"""
        profile = self.get_or_create_profile(user_id)
        normalized_score = score / max_score
        
        profile.update_skill(subject, normalized_score)
        
        profile.add_learning_record({
            'type': 'exam',
            'subject': subject,
            'score': score,
            'max_score': max_score,
            'normalized_score': normalized_score
        })
        
        logger.info(f"用户 {user_id} {subject} 考试得分: {score}/{max_score}")

class AIAdaptiveLearningEngine:
    """自适应学习引擎 v4.0"""
    
    def __init__(self):
        self.recommender = AILearningRecommender()
        self.knowledge_graph = KnowledgeGraph()
        self.question_bank = {}
        self.difficulty_adjustment_history = []
        logger.info("自适应学习引擎 v4.0 初始化完成")
    
    def load_question_bank(self):
        """加载题库"""
        self.question_bank = {
            'math': [
                {'id': 'q1', 'topic': 'math_algebra', 'difficulty': 0.3, 'content': '解方程: 2x + 5 = 15'},
                {'id': 'q2', 'topic': 'math_algebra', 'difficulty': 0.4, 'content': '解方程: 3x - 7 = 2x + 4'},
                {'id': 'q3', 'topic': 'math_geometry', 'difficulty': 0.45, 'content': '计算三角形面积，底为8cm，高为5cm'},
                {'id': 'q4', 'topic': 'math_function', 'difficulty': 0.55, 'content': '求函数 f(x) = x^2 - 4x + 3 的顶点坐标'},
                {'id': 'q5', 'topic': 'math_trigonometry', 'difficulty': 0.6, 'content': '已知sin(x) = 0.5，求x的值'},
                {'id': 'q6', 'topic': 'math_probability', 'difficulty': 0.5, 'content': '从1-10中随机取一个数，取到偶数的概率是多少'}
            ],
            'chinese': [
                {'id': 'cq1', 'topic': 'chinese_grammar', 'difficulty': 0.35, 'content': '选出正确的词语填空: 他____地完成了任务'},
                {'id': 'cq2', 'topic': 'chinese_poetry', 'difficulty': 0.4, 'content': '"床前明月光"的下一句是?'},
                {'id': 'cq3', 'topic': 'chinese_reading', 'difficulty': 0.5, 'content': '阅读短文并回答: 文章的主旨是什么?'},
                {'id': 'cq4', 'topic': 'chinese_essay', 'difficulty': 0.7, 'content': '翻译文言文: "学而时习之，不亦说乎"'},
                {'id': 'cq5', 'topic': 'chinese_writing', 'difficulty': 0.6, 'content': '写一篇200字的记叙文'}
            ],
            'english': [
                {'id': 'eq1', 'topic': 'english_vocabulary', 'difficulty': 0.3, 'content': '选择正确的单词: The cat ____ on the mat.'},
                {'id': 'eq2', 'topic': 'english_grammar', 'difficulty': 0.45, 'content': '填空: She ____ (go) to school every day.'},
                {'id': 'eq3', 'topic': 'english_reading', 'difficulty': 0.5, 'content': '阅读理解: What is the main idea of the passage?'},
                {'id': 'eq4', 'topic': 'english_writing', 'difficulty': 0.6, 'content': '写一篇100词的英语作文'}
            ]
        }
    
    def generate_adaptive_question(self, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """生成自适应题目"""
        profile = self.recommender.get_or_create_profile(user_id)
        current_level = profile.skill_levels.get(subject, {}).get('level', 0.5)
        
        questions = self.question_bank.get(subject.lower(), [])
        
        if not questions:
            return None
        
        target_difficulty = current_level + 0.05
        if target_difficulty > 0.95:
            target_difficulty = 0.95
        
        best_match = None
        min_diff = float('inf')
        
        for q in questions:
            diff = abs(q['difficulty'] - target_difficulty)
            if diff < min_diff:
                min_diff = diff
                best_match = q
        
        if best_match:
            return {
                'question': best_match,
                'target_difficulty': target_difficulty,
                'estimated_user_level': current_level,
                'adaptive_reason': f'基于当前水平 {current_level:.2f}，推荐难度 {target_difficulty:.2f}'
            }
        
        return None
    
    def adjust_difficulty(self, user_id: str, subject: str, answered_correctly: bool, question_difficulty: float):
        """根据答题结果调整难度"""
        profile = self.recommender.get_or_create_profile(user_id)
        current_level = profile.skill_levels.get(subject, {}).get('level', 0.5)
        
        adjustment = 0.08 if answered_correctly else -0.1
        new_level = max(0.1, min(0.95, current_level + adjustment))
        
        profile.update_skill(subject, new_level)
        
        self.difficulty_adjustment_history.append({
            'user_id': user_id,
            'subject': subject,
            'answered_correctly': answered_correctly,
            'question_difficulty': question_difficulty,
            'previous_level': current_level,
            'new_level': new_level,
            'adjustment': adjustment,
            'timestamp': datetime.now().isoformat()
        })
        
        return new_level
    
    def generate_practice_session(self, user_id: str, subject: str, question_count: int = 10) -> List[Dict[str, Any]]:
        """生成练习会话"""
        session = []
        
        for _ in range(question_count):
            question = self.generate_adaptive_question(user_id, subject)
            if question:
                session.append(question)
        
        return session

class AIEngineV4:
    """MTSCOS AI引擎 v4.0 主入口"""
    
    def __init__(self):
        self.recommender = AILearningRecommender()
        self.adaptive_engine = AIAdaptiveLearningEngine()
        self.adaptive_engine.load_question_bank()
        self.version = '4.0.0'
        logger.info(f"MTSCOS AI引擎 v{self.version} 初始化完成")
    
    def get_version(self) -> Dict[str, Any]:
        """获取版本信息"""
        return {
            'version': self.version,
            'modules': {
                'learning_recommender': '4.0',
                'adaptive_engine': '4.0',
                'knowledge_graph': '2.0',
                'question_bank': '2.0'
            },
            'features': [
                '个性化学习推荐',
                '自适应难度调整',
                '知识图谱关联',
                '学习路径规划',
                '智能题目生成',
                '学习模式分析'
            ]
        }
    
    def analyze_user(self, user_id: str) -> Dict[str, Any]:
        """分析用户学习情况"""
        pattern = self.recommender.analyze_learning_pattern(user_id)
        return {
            'user_id': user_id,
            'learning_pattern': pattern,
            'recommendations': self.recommender.generate_personalized_recommendations(user_id),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_recommendations(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """获取学习推荐"""
        return self.recommender.generate_personalized_recommendations(user_id, count)
    
    def get_learning_path(self, user_id: str, subject: str) -> List[Dict[str, Any]]:
        """获取学习路径"""
        return self.recommender.get_learning_path(user_id, subject)
    
    def generate_question(self, user_id: str, subject: str) -> Optional[Dict[str, Any]]:
        """生成自适应题目"""
        return self.adaptive_engine.generate_adaptive_question(user_id, subject)
    
    def record_answer(self, user_id: str, subject: str, question_difficulty: float, correct: bool):
        """记录答题结果"""
        new_level = self.adaptive_engine.adjust_difficulty(user_id, subject, correct, question_difficulty)
        self.recommender.update_with_exam_result(user_id, subject, new_level * 100, 100)
        return new_level
    
    def generate_practice(self, user_id: str, subject: str, count: int = 10) -> List[Dict[str, Any]]:
        """生成练习题目"""
        return self.adaptive_engine.generate_practice_session(user_id, subject, count)

ai_engine_v4 = AIEngineV4()

if __name__ == '__main__':
    engine = AIEngineV4()
    
    print("=== MTSCOS AI引擎 v4.0 测试 ===")
    print(json.dumps(engine.get_version(), indent=2, ensure_ascii=False))
    
    print("\n=== 分析用户学习情况 ===")
    analysis = engine.analyze_user('test_user_001')
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    print("\n=== 获取学习推荐 ===")
    recs = engine.get_recommendations('test_user_001', 3)
    print(json.dumps(recs, indent=2, ensure_ascii=False))
    
    print("\n=== 获取数学学习路径 ===")
    path = engine.get_learning_path('test_user_001', '数学')
    print(json.dumps(path, indent=2, ensure_ascii=False))
    
    print("\n=== 生成自适应题目 ===")
    question = engine.generate_question('test_user_001', '数学')
    print(json.dumps(question, indent=2, ensure_ascii=False))
    
    print("\n=== 生成练习会话 ===")
    practice = engine.generate_practice('test_user_001', '数学', 3)
    print(json.dumps(practice, indent=2, ensure_ascii=False))
    
    print("\n=== 记录答题结果 ===")
    new_level = engine.record_answer('test_user_001', '数学', 0.5, True)
    print(f"新技能水平: {new_level:.2f}")
    
    print("\n=== 测试完成 ===")