# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI智能学习推荐系统 v3.0.0
功能：基于用户行为分析的智能学习内容推荐
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ai_learning_recommender')

class AILearningRecommender:
    """AI智能学习推荐系统"""

    def __init__(self):
        """初始化推荐系统"""
        self.user_profiles = {}
        self.course_features = {}
        self.recommendation_history = {}
        self.learning_patterns = {}
        logger.info("AI智能学习推荐系统 v3.0.0 初始化完成")

    def analyze_user_learning_pattern(self, user_id: str, learning_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析用户学习模式
        
        Args:
            user_id: 用户ID
            learning_data: 学习数据列表
            
        Returns:
            用户学习模式分析结果
        """
        logger.info(f"分析用户 {user_id} 的学习模式")

        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._create_new_profile(user_id)

        profile = self.user_profiles[user_id]
        
        # 更新学习数据
        profile['total_learning_time'] += self._calculate_learning_time(learning_data)
        profile['learning_count'] += len(learning_data)
        
        # 分析学习偏好
        subject_stats = defaultdict(int)
        time_of_day_stats = defaultdict(int)
        difficulty_stats = defaultdict(int)
        
        for data in learning_data:
            subject = data.get('subject', 'unknown')
            subject_stats[subject] += 1
            
            hour = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())).hour
            time_of_day_stats[hour] += 1
            
            difficulty = data.get('difficulty', 'medium')
            difficulty_stats[difficulty] += 1

        # 更新偏好
        profile['preferred_subjects'] = dict(sorted(subject_stats.items(), key=lambda x: -x[1]))
        profile['preferred_time_of_day'] = max(time_of_day_stats, key=time_of_day_stats.get, default=14)
        profile['difficulty_distribution'] = dict(difficulty_stats)

        # 计算学习节奏
        profile['learning_rhythm'] = self._calculate_learning_rhythm(learning_data)
        
        # 识别薄弱环节
        profile['weak_points'] = self._identify_weak_points(learning_data)
        
        # 评估学习效果
        profile['learning_effectiveness'] = self._evaluate_effectiveness(learning_data)

        logger.info(f"用户 {user_id} 学习模式分析完成")
        return profile

    def _create_new_profile(self, user_id: str) -> Dict[str, Any]:
        """创建新用户档案"""
        return {
            'user_id': user_id,
            'total_learning_time': 0,
            'learning_count': 0,
            'preferred_subjects': {},
            'preferred_time_of_day': 14,
            'difficulty_distribution': {},
            'learning_rhythm': 'steady',
            'weak_points': [],
            'learning_effectiveness': 0.5,
            'last_updated': datetime.now().isoformat(),
            'learning_goals': []
        }

    def _calculate_learning_time(self, learning_data: List[Dict[str, Any]]) -> int:
        """计算学习时长（秒）"""
        total_time = 0
        for data in learning_data:
            total_time += data.get('duration', 0)
        return total_time

    def _calculate_learning_rhythm(self, learning_data: List[Dict[str, Any]]) -> str:
        """计算学习节奏"""
        if len(learning_data) < 5:
            return 'exploring'
        
        timestamps = sorted([datetime.fromisoformat(d.get('timestamp', datetime.now().isoformat())) for d in learning_data])
        
        intervals = []
        for i in range(1, len(timestamps)):
            intervals.append((timestamps[i] - timestamps[i-1]).total_seconds() / 3600)
        
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 24:
            return 'daily'
        elif avg_interval < 168:
            return 'weekly'
        else:
            return 'sporadic'

    def _identify_weak_points(self, learning_data: List[Dict[str, Any]]) -> List[str]:
        """识别学习薄弱环节"""
        weak_points = []
        subject_errors = defaultdict(int)
        subject_attempts = defaultdict(int)
        
        for data in learning_data:
            subject = data.get('subject', 'unknown')
            subject_attempts[subject] += 1
            if data.get('correct', True) is False:
                subject_errors[subject] += 1
        
        for subject, attempts in subject_attempts.items():
            error_rate = subject_errors[subject] / attempts
            if error_rate > 0.3:
                weak_points.append(subject)
        
        return weak_points

    def _evaluate_effectiveness(self, learning_data: List[Dict[str, Any]]) -> float:
        """评估学习效果"""
        if not learning_data:
            return 0.5
        
        total_correct = sum(1 for d in learning_data if d.get('correct', True))
        avg_duration = sum(d.get('duration', 0) for d in learning_data) / len(learning_data)
        
        accuracy = total_correct / len(learning_data)
        engagement = min(avg_duration / 600, 1)  # 以10分钟为基准
        
        return (accuracy * 0.6 + engagement * 0.4)

    def generate_recommendations(self, user_id: str, grade: str, count: int = 5) -> List[Dict[str, Any]]:
        """生成个性化学习推荐
        
        Args:
            user_id: 用户ID
            grade: 用户年级
            count: 推荐数量
            
        Returns:
            推荐列表
        """
        logger.info(f"为用户 {user_id} 生成学习推荐")

        if user_id not in self.user_profiles:
            return self._generate_default_recommendations(grade, count)

        profile = self.user_profiles[user_id]
        recommendations = []
        
        # 1. 薄弱环节强化推荐
        for subject in profile['weak_points'][:2]:
            recommendations.extend(self._generate_subject_recommendations(subject, grade, 2))
        
        # 2. 兴趣扩展推荐
        preferred_subjects = list(profile['preferred_subjects'].keys())[:3]
        for subject in preferred_subjects:
            if subject not in profile['weak_points']:
                recommendations.extend(self._generate_subject_recommendations(subject, grade, 1))
        
        # 3. 能力均衡推荐
        all_subjects = self._get_all_subjects_for_grade(grade)
        for subject in all_subjects:
            if subject not in profile['preferred_subjects'] and subject not in profile['weak_points']:
                recommendations.extend(self._generate_subject_recommendations(subject, grade, 1))
                break
        
        # 4. 智能排序
        recommendations = self._intelligent_sort(recommendations, profile)
        
        # 记录推荐历史
        self.recommendation_history[user_id] = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': [r['id'] for r in recommendations[:count]]
        }

        return recommendations[:count]

    def _generate_default_recommendations(self, grade: str, count: int) -> List[Dict[str, Any]]:
        """生成默认推荐（新用户）"""
        recommendations = []
        subjects = self._get_all_subjects_for_grade(grade)
        
        for subject in subjects[:count]:
            recommendations.extend(self._generate_subject_recommendations(subject, grade, 1))
        
        return recommendations[:count]

    def _get_all_subjects_for_grade(self, grade: str) -> List[str]:
        """获取对应年级的所有科目"""
        grade_subjects = {
            'grade1': ['语文', '数学', '英语', '美术', '音乐'],
            'grade2': ['语文', '数学', '英语', '美术', '音乐'],
            'grade3': ['语文', '数学', '英语', '科学', '美术'],
            'grade4': ['语文', '数学', '英语', '科学', '美术'],
            'grade5': ['语文', '数学', '英语', '科学', '美术'],
            'grade6': ['语文', '数学', '英语', '科学', '历史'],
            'grade7': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理'],
            'grade8': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理'],
            'grade9': ['语文', '数学', '英语', '物理', '化学', '历史', '道德与法治'],
            'grade10': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理'],
            'grade11': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理'],
            'grade12': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理']
        }
        return grade_subjects.get(grade, ['语文', '数学', '英语'])

    def _generate_subject_recommendations(self, subject: str, grade: str, count: int) -> List[Dict[str, Any]]:
        """生成特定科目的推荐"""
        recommendations = []
        
        subject_topics = {
            '语文': ['阅读理解', '作文写作', '文言文', '诗词鉴赏', '语法知识'],
            '数学': ['代数运算', '几何图形', '函数', '概率统计', '应用题'],
            '英语': ['词汇记忆', '语法学习', '阅读理解', '口语练习', '写作技巧'],
            '物理': ['力学', '电学', '光学', '热学', '声学'],
            '化学': ['元素周期', '化学反应', '有机化学', '无机化学', '实验操作'],
            '生物': ['细胞结构', '遗传变异', '生态系统', '新陈代谢', '生命进化'],
            '历史': ['中国古代史', '中国近代史', '世界史', '历史人物', '历史事件'],
            '地理': ['自然地理', '人文地理', '区域地理', '地理信息', '环境保护'],
            '科学': ['自然科学', '科学实验', '科学思维', '科技创新', '科学探索'],
            '美术': ['绘画基础', '色彩理论', '艺术鉴赏', '创意设计', '手工制作'],
            '音乐': ['音乐理论', '乐器学习', '音乐鉴赏', '唱歌技巧', '音乐创作'],
            '道德与法治': ['道德规范', '法律知识', '公民素养', '社会公德', '心理健康']
        }

        topics = subject_topics.get(subject, [subject])
        
        for topic in topics[:count]:
            recommendations.append({
                'id': f"{subject}-{topic}-{grade}",
                'subject': subject,
                'topic': topic,
                'grade': grade,
                'type': self._determine_content_type(subject, topic),
                'difficulty': self._determine_difficulty(grade, subject),
                'estimated_time': self._estimate_time(subject, topic),
                'priority': self._calculate_priority(subject, topic, grade)
            })
        
        return recommendations

    def _determine_content_type(self, subject: str, topic: str) -> str:
        """确定内容类型"""
        if topic in ['阅读理解', '作文写作', '文言文', '诗词鉴赏']:
            return '练习'
        elif topic in ['实验操作', '科学实验']:
            return '实验'
        elif topic in ['词汇记忆', '语法知识']:
            return '基础'
        else:
            return '综合'

    def _determine_difficulty(self, grade: str, subject: str) -> str:
        """确定难度"""
        grade_level = int(grade.replace('grade', ''))
        
        if grade_level <= 6:
            return 'easy'
        elif grade_level <= 9:
            return 'medium'
        else:
            return 'hard'

    def _estimate_time(self, subject: str, topic: str) -> int:
        """估计学习时间（分钟）"""
        base_times = {
            '语文': {'阅读理解': 30, '作文写作': 45, '文言文': 25, '诗词鉴赏': 20, '语法知识': 15},
            '数学': {'代数运算': 20, '几何图形': 25, '函数': 30, '概率统计': 25, '应用题': 35},
            '英语': {'词汇记忆': 15, '语法学习': 25, '阅读理解': 30, '口语练习': 20, '写作技巧': 35},
            '物理': {'力学': 30, '电学': 35, '光学': 25, '热学': 20, '声学': 15},
            '化学': {'元素周期': 20, '化学反应': 30, '有机化学': 40, '无机化学': 25, '实验操作': 45},
            '生物': {'细胞结构': 25, '遗传变异': 30, '生态系统': 25, '新陈代谢': 20, '生命进化': 25},
            '历史': {'中国古代史': 25, '中国近代史': 30, '世界史': 35, '历史人物': 20, '历史事件': 25},
            '地理': {'自然地理': 30, '人文地理': 25, '区域地理': 30, '地理信息': 20, '环境保护': 25}
        }
        
        return base_times.get(subject, {}).get(topic, 30)

    def _calculate_priority(self, subject: str, topic: str, grade: str) -> float:
        """计算推荐优先级"""
        grade_level = int(grade.replace('grade', ''))
        
        # 基础科目权重更高
        base_weight = {'语文': 1.5, '数学': 1.5, '英语': 1.3}.get(subject, 1.0)
        
        # 难度调整
        difficulty_factor = {'easy': 0.8, 'medium': 1.0, 'hard': 1.2}.get(
            self._determine_difficulty(grade, subject), 1.0
        )
        
        # 年级调整
        grade_factor = min(grade_level / 6, 1.5)
        
        return base_weight * difficulty_factor * grade_factor

    def _intelligent_sort(self, recommendations: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """智能排序推荐列表"""
        # 基于用户偏好调整优先级
        subject_preferences = profile.get('preferred_subjects', {})
        weak_points = profile.get('weak_points', [])
        
        for rec in recommendations:
            # 薄弱环节优先
            if rec['subject'] in weak_points:
                rec['priority'] *= 1.5
            
            # 偏好科目加分
            preference_score = subject_preferences.get(rec['subject'], 0)
            if preference_score > 0:
                rec['priority'] *= (1 + preference_score * 0.1)
        
        # 按优先级排序
        return sorted(recommendations, key=lambda x: -x['priority'])

    def get_learning_plan(self, user_id: str, grade: str, days: int = 7) -> Dict[str, Any]:
        """生成学习计划
        
        Args:
            user_id: 用户ID
            grade: 用户年级
            days: 计划天数
            
        Returns:
            学习计划
        """
        logger.info(f"为用户 {user_id} 生成 {days} 天学习计划")
        
        recommendations = self.generate_recommendations(user_id, grade, days * 3)
        plan = {
            'user_id': user_id,
            'grade': grade,
            'days': days,
            'total_estimated_time': 0,
            'daily_plans': []
        }
        
        # 平均分配推荐到每天
        rec_per_day = len(recommendations) // days
        remaining = len(recommendations) % days
        
        start_idx = 0
        for day in range(1, days + 1):
            end_idx = start_idx + rec_per_day + (1 if remaining > 0 else 0)
            remaining -= 1 if remaining > 0 else 0
            
            day_recommendations = recommendations[start_idx:end_idx]
            day_time = sum(r['estimated_time'] for r in day_recommendations)
            
            plan['daily_plans'].append({
                'day': day,
                'recommendations': day_recommendations,
                'estimated_time': day_time,
                'suggested_time': self._suggest_time_of_day(user_id)
            })
            
            plan['total_estimated_time'] += day_time
            start_idx = end_idx
        
        return plan

    def _suggest_time_of_day(self, user_id: str) -> str:
        """建议学习时间"""
        if user_id not in self.user_profiles:
            return "14:00-16:00"
        
        preferred_hour = self.user_profiles[user_id].get('preferred_time_of_day', 14)
        
        if preferred_hour < 6:
            return "06:00-08:00"
        elif preferred_hour < 12:
            return "09:00-11:00"
        elif preferred_hour < 18:
            return "14:00-16:00"
        else:
            return "19:00-21:00"

    def update_recommendation_feedback(self, user_id: str, recommendation_id: str, feedback: str) -> bool:
        """更新推荐反馈
        
        Args:
            user_id: 用户ID
            recommendation_id: 推荐ID
            feedback: 反馈类型 ('like', 'dislike', 'completed')
            
        Returns:
            是否成功
        """
        logger.info(f"记录用户 {user_id} 对推荐 {recommendation_id} 的反馈: {feedback}")
        
        if user_id not in self.recommendation_history:
            self.recommendation_history[user_id] = {
                'timestamp': datetime.now().isoformat(),
                'recommendations': []
            }
        
        # 更新用户偏好
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            subject = recommendation_id.split('-')[0]
            
            if feedback in ['like', 'completed']:
                profile['preferred_subjects'][subject] = profile['preferred_subjects'].get(subject, 0) + 1
            elif feedback == 'dislike':
                profile['preferred_subjects'][subject] = max(0, profile['preferred_subjects'].get(subject, 0) - 1)
            
            profile['last_updated'] = datetime.now().isoformat()
        
        return True

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'version': '3.0.0',
            'total_users': len(self.user_profiles),
            'total_recommendations': sum(
                len(recs.get('recommendations', [])) for recs in self.recommendation_history.values()
            ),
            'average_effectiveness': sum(
                p['learning_effectiveness'] for p in self.user_profiles.values()
            ) / max(len(self.user_profiles), 1),
            'active_users_today': sum(
                1 for p in self.user_profiles.values()
                if datetime.fromisoformat(p['last_updated']).date() == datetime.now().date()
            )
        }

# 创建全局实例
ai_learning_recommender = AILearningRecommender()

if __name__ == '__main__':
    # 测试推荐系统
    recommender = AILearningRecommender()
    
    # 模拟用户学习数据
    test_learning_data = [
        {'subject': '数学', 'duration': 300, 'correct': True, 'timestamp': '2026-06-01T14:00:00', 'difficulty': 'medium'},
        {'subject': '数学', 'duration': 240, 'correct': False, 'timestamp': '2026-06-01T14:05:00', 'difficulty': 'medium'},
        {'subject': '语文', 'duration': 360, 'correct': True, 'timestamp': '2026-06-02T10:00:00', 'difficulty': 'easy'},
        {'subject': '英语', 'duration': 180, 'correct': True, 'timestamp': '2026-06-02T15:00:00', 'difficulty': 'medium'},
        {'subject': '数学', 'duration': 420, 'correct': False, 'timestamp': '2026-06-03T14:00:00', 'difficulty': 'hard'},
        {'subject': '物理', 'duration': 300, 'correct': True, 'timestamp': '2026-06-03T16:00:00', 'difficulty': 'medium'}
    ]
    
    # 分析用户学习模式
    pattern = recommender.analyze_user_learning_pattern('test_user', test_learning_data)
    print("用户学习模式分析结果:")
    print(json.dumps(pattern, indent=2, ensure_ascii=False))
    
    # 生成推荐
    recommendations = recommender.generate_recommendations('test_user', 'grade8', 5)
    print("\n个性化学习推荐:")
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
    
    # 生成学习计划
    plan = recommender.get_learning_plan('test_user', 'grade8', 7)
    print("\n7天学习计划:")
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    
    # 获取系统统计
    stats = recommender.get_system_stats()
    print("\n系统统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
