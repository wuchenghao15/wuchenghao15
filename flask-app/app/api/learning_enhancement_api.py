# -*- coding: utf-8 -*-
"""
学习增强API模块
提供学习路径规划、错题智能推荐、知识图谱可视化等功能
"""

from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# 创建蓝图
learning_enhancement_api = Blueprint('learning_enhancement_api', __name__, url_prefix='/api/learning/enhancement')

# 数据库路径配置
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class LearningPathPlanner:
    """学习路径规划器"""
    
    def __init__(self):
        # 学习目标配置
        self.goal_templates = {
            '基础巩固': {'difficulty_range': [1, 2], 'focus': '基础知识', 'duration_weeks': 2},
            '能力提升': {'difficulty_range': [2, 3], 'focus': '核心技能', 'duration_weeks': 3},
            '进阶突破': {'difficulty_range': [3, 4], 'focus': '高阶应用', 'duration_weeks': 4},
            '冲刺备考': {'difficulty_range': [4, 5], 'focus': '考试冲刺', 'duration_weeks': 2}
        }
        
        # 知识点依赖关系
        self.knowledge_dependencies = {
            '词汇基础': ['基础语法'],
            '基础语法': ['句型结构', '阅读理解'],
            '句型结构': ['写作表达', '听力理解'],
            '阅读理解': ['阅读技巧', '文学鉴赏'],
            '听力理解': ['听力技巧', '口语表达'],
            '写作表达': ['写作技巧', '文章结构']
        }
    
    def generate_personalized_path(self, user_id: int, current_level: str, 
                                   learning_goal: str, available_time: int) -> Dict[str, Any]:
        """
        生成个性化学习路径
        
        Args:
            user_id: 用户ID
            current_level: 当前水平（初级/中级/高级）
            learning_goal: 学习目标
            available_time: 每周可用学习时间（小时）
        
        Returns:
            学习路径规划结果
        """
        try:
            # 获取用户学习数据
            user_data = self._get_user_learning_data(user_id)
            
            # 分析当前状态
            current_status = self._analyze_current_status(user_data)
            
            # 确定目标配置
            goal_config = self.goal_templates.get(learning_goal, self.goal_templates['能力提升'])
            
            # 生成学习阶段
            learning_stages = self._generate_learning_stages(
                current_status, goal_config, available_time
            )
            
            # 生成每日学习计划
            daily_plan = self._generate_daily_plan(learning_stages, available_time)
            
            # 生成里程碑节点
            milestones = self._generate_milestones(learning_stages)
            
            return {
                'user_id': user_id,
                'current_level': current_level,
                'learning_goal': learning_goal,
                'total_duration_weeks': goal_config['duration_weeks'],
                'learning_stages': learning_stages,
                'daily_plan': daily_plan,
                'milestones': milestones,
                'estimated_improvement': self._estimate_improvement(current_status, goal_config),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"生成学习路径失败: {str(e)}")
            return {'error': str(e)}
    
    def _get_user_learning_data(self, user_id: int) -> Dict[str, Any]:
        """获取用户学习数据"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取学习记录
                cursor.execute('''
                    SELECT subject, duration, created_at FROM learning_records
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
                ''', (user_id,))
                learning_records = [dict(row) for row in cursor.fetchall()]
                
                # 获取错题数据
                cursor.execute('''
                    SELECT knowledge_point, error_type, difficulty_level FROM wrong_questions
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 30
                ''', (user_id,))
                wrong_questions = [dict(row) for row in cursor.fetchall()]
                
                # 获取考试成绩
                cursor.execute('''
                    SELECT score, total_score, created_at FROM exam_results
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 20
                ''', (user_id,))
                exam_results = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'learning_records': learning_records,
                    'wrong_questions': wrong_questions,
                    'exam_results': exam_results
                }
        except Exception as e:
            logger.error(f"获取用户学习数据失败: {str(e)}")
            return {}
    
    def _analyze_current_status(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前学习状态"""
        # 分析学习频率
        learning_records = user_data.get('learning_records', [])
        total_duration = sum(r.get('duration', 0) for r in learning_records)
        avg_duration = total_duration / len(learning_records) if learning_records else 0
        
        # 分析错题分布
        wrong_questions = user_data.get('wrong_questions', [])
        error_distribution = defaultdict(int)
        for q in wrong_questions:
            kp = q.get('knowledge_point', '未知')
            error_distribution[kp] += 1
        
        # 分析考试成绩趋势
        exam_results = user_data.get('exam_results', [])
        if exam_results:
            scores = [r.get('score', 0) / r.get('total_score', 100) * 100 for r in exam_results]
            avg_score = sum(scores) / len(scores)
            recent_scores = scores[:5] if len(scores) >= 5 else scores
            early_scores = scores[-5:] if len(scores) >= 5 else scores
            trend = 'improving' if sum(recent_scores) > sum(early_scores) else 'stable'
        else:
            avg_score = 0
            trend = 'no_data'
        
        return {
            'avg_study_duration': round(avg_duration, 1),
            'total_study_count': len(learning_records),
            'error_distribution': dict(error_distribution),
            'avg_exam_score': round(avg_score, 1),
            'score_trend': trend,
            'main_weaknesses': list(error_distribution.keys())[:3]
        }
    
    def _generate_learning_stages(self, current_status: Dict[str, Any],
                                  goal_config: Dict[str, Any],
                                  available_time: int) -> List[Dict[str, Any]]:
        """生成学习阶段"""
        stages = []
        difficulty_range = goal_config['difficulty_range']
        duration_weeks = goal_config['duration_weeks']
        
        # 阶段1：基础复习（1周）
        if current_status.get('main_weaknesses'):
            stages.append({
                'stage_id': 1,
                'name': '基础巩固阶段',
                'duration_weeks': 1,
                'focus_topics': current_status['main_weaknesses'],
                'difficulty_level': difficulty_range[0],
                'daily_hours': min(available_time * 0.4, 2),
                'objectives': [
                    '巩固薄弱知识点',
                    '建立学习习惯',
                    '基础概念复习'
                ],
                'activities': [
                    {'type': '复习', 'content': '错题重做', 'duration': 30},
                    {'type': '练习', 'content': '基础练习题', 'duration': 45},
                    {'type': '总结', 'content': '知识点归纳', 'duration': 15}
                ]
            })
        
        # 阶段2：能力提升（主要阶段）
        main_stage_weeks = duration_weeks - 2
        stages.append({
            'stage_id': 2,
            'name': '能力提升阶段',
            'duration_weeks': main_stage_weeks,
            'focus_topics': [goal_config['focus']],
            'difficulty_level': difficulty_range[1],
            'daily_hours': min(available_time * 0.5, 2.5),
            'objectives': [
                '系统学习核心内容',
                '提升解题能力',
                '扩展知识应用'
            ],
            'activities': [
                {'type': '学习', 'content': '新知识点学习', 'duration': 40},
                {'type': '练习', 'content': '针对性练习', 'duration': 50},
                {'type': '测试', 'content': '阶段性测验', 'duration': 30}
            ]
        })
        
        # 阶段3：综合强化（最后阶段）
        stages.append({
            'stage_id': 3,
            'name': '综合强化阶段',
            'duration_weeks': 1,
            'focus_topics': ['综合复习', '模拟测试'],
            'difficulty_level': difficulty_range[1],
            'daily_hours': min(available_time * 0.6, 3),
            'objectives': [
                '综合能力检验',
                '考前冲刺准备',
                '知识点串联'
            ],
            'activities': [
                {'type': '模拟', 'content': '模拟考试', 'duration': 60},
                {'type': '分析', 'content': '错题分析', 'duration': 30},
                {'type': '强化', 'content': '重点强化', 'duration': 30}
            ]
        })
        
        return stages
    
    def _generate_daily_plan(self, learning_stages: List[Dict[str, Any]],
                            available_time: int) -> Dict[str, Any]:
        """生成每日学习计划"""
        # 获取当前阶段
        current_stage = learning_stages[0] if learning_stages else None
        
        if not current_stage:
            return {'error': '无学习阶段'}
        
        daily_hours = current_stage['daily_hours']
        total_minutes = int(daily_hours * 60)
        
        # 分配学习时间
        plan = {
            'morning': {
                'time_range': '08:00-12:00',
                'activities': [],
                'total_minutes': int(total_minutes * 0.4)
            },
            'afternoon': {
                'time_range': '14:00-17:00',
                'activities': [],
                'total_minutes': int(total_minutes * 0.35)
            },
            'evening': {
                'time_range': '19:00-21:00',
                'activities': [],
                'total_minutes': int(total_minutes * 0.25)
            }
        }
        
        # 分配活动
        activities = current_stage.get('activities', [])
        time_slots = ['morning', 'afternoon', 'evening']
        
        for i, activity in enumerate(activities):
            slot = time_slots[i % len(time_slots)]
            plan[slot]['activities'].append({
                'type': activity['type'],
                'content': activity['content'],
                'duration': activity['duration'],
                'priority': 'high' if i == 0 else 'medium'
            })
        
        return plan
    
    def _generate_milestones(self, learning_stages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成里程碑节点"""
        milestones = []
        base_date = datetime.now()
        
        for stage in learning_stages:
            milestone_date = base_date + timedelta(weeks=stage['duration_weeks'])
            milestones.append({
                'stage_id': stage['stage_id'],
                'name': stage['name'] + '完成',
                'target_date': milestone_date.strftime('%Y-%m-%d'),
                'criteria': [
                    f"完成{stage['focus_topics']}相关学习",
                    f"正确率达到{70 + stage['stage_id'] * 5}%以上",
                    f"错题减少{30 + stage['stage_id'] * 10}%"
                ],
                'reward': f"解锁下一阶段：{learning_stages[stage['stage_id']]['name'] if stage['stage_id'] < len(learning_stages) else '学习完成'}"
            })
            base_date = milestone_date
        
        return milestones
    
    def _estimate_improvement(self, current_status: Dict[str, Any],
                             goal_config: Dict[str, Any]) -> str:
        """预估学习改善情况"""
        avg_score = current_status.get('avg_exam_score', 0)
        trend = current_status.get('score_trend', 'stable')
        
        if avg_score < 60:
            return f"预计经过{goal_config['duration_weeks']}周学习，成绩可提升至70-80分区间"
        elif avg_score < 80:
            return f"预计经过{goal_config['duration_weeks']}周学习，成绩可提升至85-95分区间"
        else:
            return f"预计经过{goal_config['duration_weeks']}周学习，可保持并稳定在高分水平"
    
    def update_learning_progress(self, user_id: int, stage_id: int,
                                 completed_activities: List[str]) -> Dict[str, Any]:
        """更新学习进度"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # 创建学习进度表（如果不存在）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_path_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        stage_id INTEGER NOT NULL,
                        completed_activities TEXT,
                        completion_rate REAL DEFAULT 0,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 更新进度
                completion_rate = len(completed_activities) / 3  # 假设每阶段3个活动
                
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_path_progress 
                    (user_id, stage_id, completed_activities, completion_rate, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, stage_id, json.dumps(completed_activities), completion_rate))
                
                return {
                    'success': True,
                    'stage_id': stage_id,
                    'completion_rate': completion_rate,
                    'message': '进度已更新'
                }
        except Exception as e:
            logger.error(f"更新学习进度失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_recommended_sequence(self, user_id: int) -> List[Dict[str, Any]]:
        """获取推荐学习顺序"""
        try:
            user_data = self._get_user_learning_data(user_id)
            current_status = self._analyze_current_status(user_data)
            
            # 根据知识依赖关系确定学习顺序
            weaknesses = current_status.get('main_weaknesses', [])
            sequence = []
            
            for weakness in weaknesses:
                # 找到前置知识点
                prerequisites = []
                for kp, deps in self.knowledge_dependencies.items():
                    if weakness in deps:
                        prerequisites.append(kp)
                
                sequence.append({
                    'knowledge_point': weakness,
                    'priority': 'high',
                    'prerequisites': prerequisites,
                    'recommended_order': len(sequence) + 1
                })
            
            return sequence
        except Exception as e:
            logger.error(f"获取推荐学习顺序失败: {str(e)}")
            return []


class WrongQuestionRecommender:
    """错题智能推荐器"""
    
    def __init__(self):
        # 错题类型分类
        self.error_type_categories = {
            '概念理解': ['概念混淆', '定义不清', '理解偏差'],
            '计算错误': ['运算失误', '公式错误', '数值偏差'],
            '逻辑推理': ['推理错误', '逻辑跳跃', '因果关系'],
            '应用能力': ['情境应用', '综合分析', '迁移能力'],
            '记忆失误': ['遗忘', '记忆模糊', '提取失败']
        }
        
        # 知识点关联图谱
        self.knowledge_relations = {
            '词汇': ['语法', '阅读', '写作'],
            '语法': ['句型', '写作', '翻译'],
            '阅读': ['词汇', '语法', '理解'],
            '听力': ['词汇', '语音', '理解'],
            '写作': ['词汇', '语法', '阅读']
        }
    
    def recommend_targeted_practice(self, user_id: int) -> Dict[str, Any]:
        """
        推荐针对性练习
        
        Args:
            user_id: 用户ID
        
        Returns:
            推荐练习结果
        """
        try:
            # 获取错题数据
            wrong_questions = self._get_wrong_questions(user_id)
            
            # 分析错题类型
            error_analysis = self._analyze_error_types(wrong_questions)
            
            # 生成推荐练习
            recommendations = self._generate_recommendations(error_analysis)
            
            # 关联知识点推荐
            related_knowledge = self._get_related_knowledge_points(error_analysis)
            
            return {
                'user_id': user_id,
                'error_analysis': error_analysis,
                'recommendations': recommendations,
                'related_knowledge_points': related_knowledge,
                'study_priority': self._calculate_study_priority(error_analysis),
                'estimated_practice_count': self._estimate_practice_count(error_analysis),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"推荐针对性练习失败: {str(e)}")
            return {'error': str(e)}
    
    def _get_wrong_questions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取错题数据"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, question_id, knowledge_point, error_type, 
                           difficulty_level, wrong_count, last_wrong_at
                    FROM wrong_questions
                    WHERE user_id = ?
                    ORDER BY wrong_count DESC, last_wrong_at DESC
                    LIMIT 50
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取错题数据失败: {str(e)}")
            return []
    
    def _analyze_error_types(self, wrong_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析错题类型"""
        type_distribution = defaultdict(lambda: {'count': 0, 'difficulty_avg': 0, 'points': []})
        knowledge_distribution = defaultdict(lambda: {'count': 0, 'error_types': []})
        
        for q in wrong_questions:
            error_type = q.get('error_type', '未知')
            difficulty = q.get('difficulty_level', 1)
            knowledge_point = q.get('knowledge_point', '未知')
            
            # 错题类型统计
            type_distribution[error_type]['count'] += 1
            type_distribution[error_type]['difficulty_avg'] += difficulty
            if knowledge_point not in type_distribution[error_type]['points']:
                type_distribution[error_type]['points'].append(knowledge_point)
            
            # 知识点统计
            knowledge_distribution[knowledge_point]['count'] += 1
            if error_type not in knowledge_distribution[knowledge_point]['error_types']:
                knowledge_distribution[knowledge_point]['error_types'].append(error_type)
        
        # 计算平均难度
        for error_type, data in type_distribution.items():
            if data['count'] > 0:
                data['difficulty_avg'] = round(data['difficulty_avg'] / data['count'], 1)
        
        return {
            'type_distribution': dict(type_distribution),
            'knowledge_distribution': dict(knowledge_distribution),
            'total_errors': len(wrong_questions),
            'most_frequent_type': max(type_distribution.items(), 
                                     key=lambda x: x[1]['count'])[0] if type_distribution else '无',
            'most_difficult_knowledge': max(knowledge_distribution.items(),
                                           key=lambda x: sum([self._get_type_weight(et) 
                                                             for et in x[1]['error_types']]))[0]
                                           if knowledge_distribution else '无'
        }
    
    def _get_type_weight(self, error_type: str) -> int:
        """获取错题类型权重"""
        weights = {
            '概念理解': 3,
            '计算错误': 2,
            '逻辑推理': 4,
            '应用能力': 5,
            '记忆失误': 1
        }
        return weights.get(error_type, 2)
    
    def _generate_recommendations(self, error_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成推荐练习"""
        recommendations = []
        type_dist = error_analysis.get('type_distribution', {})
        
        for error_type, data in type_dist.items():
            if data['count'] >= 2:  # 至少出现2次才推荐
                category = self._get_error_category(error_type)
                
                recommendations.append({
                    'error_type': error_type,
                    'category': category,
                    'frequency': data['count'],
                    'difficulty_level': int(data['difficulty_avg']),
                    'knowledge_points': data['points'],
                    'recommended_practice': {
                        'type': self._get_practice_type(error_type),
                        'count': data['count'] * 3,  # 推荐3倍练习量
                        'method': self._get_practice_method(error_type),
                        'time_allocation': f"{data['count'] * 10}分钟/天"
                    },
                    'priority': self._calculate_priority(data['count'], data['difficulty_avg'])
                })
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations[:10]  # 返回前10个推荐
    
    def _get_error_category(self, error_type: str) -> str:
        """获取错题所属类别"""
        for category, types in self.error_type_categories.items():
            if error_type in types:
                return category
        return '其他'
    
    def _get_practice_type(self, error_type: str) -> str:
        """获取推荐练习类型"""
        practice_mapping = {
            '概念理解': '概念辨析练习',
            '计算错误': '计算专项训练',
            '逻辑推理': '逻辑推理题组',
            '应用能力': '情境应用练习',
            '记忆失误': '记忆强化训练'
        }
        return practice_mapping.get(error_type, '综合练习')
    
    def _get_practice_method(self, error_type: str) -> str:
        """获取推荐学习方法"""
        method_mapping = {
            '概念理解': '对比学习法 - 对比相似概念，找出差异',
            '计算错误': '分步验证法 - 每步计算后验证结果',
            '逻辑推理': '思维导图法 - 画出推理过程，检查逻辑链条',
            '应用能力': '情境模拟法 - 在不同情境中应用知识点',
            '记忆失误': '间隔复习法 - 按遗忘曲线规律复习'
        }
        return method_mapping.get(error_type, '重复练习法')
    
    def _calculate_priority(self, count: int, difficulty_avg: float) -> int:
        """计算推荐优先级"""
        # 基于频率和难度的综合优先级
        frequency_score = min(count * 2, 10)
        difficulty_score = min(difficulty_avg * 2, 10)
        return int(frequency_score + difficulty_score)
    
    def _get_related_knowledge_points(self, error_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取关联知识点推荐"""
        knowledge_dist = error_analysis.get('knowledge_distribution', {})
        related_points = []
        
        for kp, data in knowledge_dist.items():
            # 找到关联知识点
            relations = self.knowledge_relations.get(kp, [])
            
            related_points.append({
                'knowledge_point': kp,
                'error_count': data['count'],
                'error_types': data['error_types'],
                'related_points': relations,
                'recommended_review': f"复习{kp}的同时，建议复习{', '.join(relations[:2])}"
            })
        
        return related_points
    
    def _calculate_study_priority(self, error_analysis: Dict[str, Any]) -> List[str]:
        """计算学习优先级顺序"""
        type_dist = error_analysis.get('type_distribution', {})
        
        # 按权重和频率排序
        priorities = []
        for error_type, data in type_dist.items():
            weight = self._get_type_weight(error_type)
            score = weight * data['count']
            priorities.append({
                'type': error_type,
                'score': score,
                'reason': f"权重{weight}×频率{data['count']}={score}"
            })
        
        priorities.sort(key=lambda x: x['score'], reverse=True)
        
        return [p['type'] + f" (优先级: {p['reason']})" for p in priorities[:5]]
    
    def _estimate_practice_count(self, error_analysis: Dict[str, Any]) -> Dict[str, int]:
        """估算练习数量"""
        type_dist = error_analysis.get('type_distribution', {})
        
        estimates = {}
        for error_type, data in type_dist.items():
            # 根据错题频率和难度估算练习量
            base_count = data['count'] * 3
            difficulty_factor = data['difficulty_avg']
            total_estimate = int(base_count * (1 + difficulty_factor * 0.5))
            
            estimates[error_type] = total_estimate
        
        return {
            'total_estimated': sum(estimates.values()),
            'by_type': estimates,
            'recommended_daily': min(sum(estimates.values()) // 7, 20),  # 每日推荐上限20题
            'estimated_completion_days': max(7, sum(estimates.values()) // 10)
        }
    
    def generate_review_schedule(self, user_id: int, 
                                review_mode: str = 'intensive') -> Dict[str, Any]:
        """生成错题复习计划"""
        try:
            wrong_questions = self._get_wrong_questions(user_id)
            
            if not wrong_questions:
                return {'message': '暂无错题需要复习'}
            
            # 根据复习模式生成计划
            if review_mode == 'intensive':
                schedule = self._generate_intensive_schedule(wrong_questions)
            elif review_mode == 'gradual':
                schedule = self._generate_gradual_schedule(wrong_questions)
            else:
                schedule = self._generate_balanced_schedule(wrong_questions)
            
            return {
                'user_id': user_id,
                'review_mode': review_mode,
                'total_questions': len(wrong_questions),
                'schedule': schedule,
                'estimated_duration': f"{len(schedule)}天",
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"生成复习计划失败: {str(e)}")
            return {'error': str(e)}
    
    def _generate_intensive_schedule(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成强化复习计划（快速攻克）"""
        # 按错误次数分组，高频错题优先
        grouped = defaultdict(list)
        for q in questions:
            count = q.get('wrong_count', 1)
            grouped[count].append(q)
        
        schedule = []
        day = 1
        
        # 按错误次数从高到低安排
        for count in sorted(grouped.keys(), reverse=True):
            batch_size = min(len(grouped[count]), 10)  # 每天最多10题
            
            for i in range(0, len(grouped[count]), batch_size):
                batch = grouped[count][i:i+batch_size]
                schedule.append({
                    'day': day,
                    'questions': [q['question_id'] for q in batch],
                    'focus': f"错误{count}次的错题",
                    'count': len(batch),
                    'review_method': '重复练习+深度分析'
                })
                day += 1
        
        return schedule
    
    def _generate_gradual_schedule(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成渐进复习计划（稳步推进）"""
        # 按知识点分组
        grouped = defaultdict(list)
        for q in questions:
            kp = q.get('knowledge_point', '综合')
            grouped[kp].append(q)
        
        schedule = []
        day = 1
        
        for kp, qs in grouped.items():
            schedule.append({
                'day': day,
                'questions': [q['question_id'] for q in qs],
                'focus': f"{kp}知识点",
                'count': len(qs),
                'review_method': '知识点系统复习'
            })
            day += 1
        
        return schedule
    
    def _generate_balanced_schedule(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成均衡复习计划（兼顾频率和知识点）"""
        # 每天混合安排高频错题和不同知识点
        schedule = []
        
        # 按错误次数排序
        sorted_questions = sorted(questions, key=lambda x: x.get('wrong_count', 0), reverse=True)
        
        batch_size = 5  # 每天5题
        for i in range(0, len(sorted_questions), batch_size):
            batch = sorted_questions[i:i+batch_size]
            knowledge_points = set(q.get('knowledge_point', '') for q in batch)
            
            schedule.append({
                'day': i // batch_size + 1,
                'questions': [q['question_id'] for q in batch],
                'focus': f"混合复习：{', '.join(knowledge_points)}",
                'count': len(batch),
                'review_method': '综合复习+重点突破'
            })
        
        return schedule


class KnowledgeGraphVisualizer:
    """知识图谱可视化器"""
    
    def __init__(self):
        # 知识点分类体系
        self.knowledge_categories = {
            '语言基础': ['词汇', '语法', '语音', '句型'],
            '语言技能': ['阅读', '听力', '写作', '口语'],
            '语言应用': ['翻译', '交际', '文化', '策略'],
            '综合能力': ['理解', '表达', '分析', '创新']
        }
        
        # 知识点层级关系
        self.knowledge_hierarchy = {
            '词汇': {
                'level': 1,
                'parent': '语言基础',
                'children': ['基础词汇', '高级词汇', '专业词汇'],
                'related': ['语法', '阅读']
            },
            '语法': {
                'level': 1,
                'parent': '语言基础',
                'children': ['基础语法', '高级语法', '句法'],
                'related': ['词汇', '写作']
            },
            '阅读': {
                'level': 2,
                'parent': '语言技能',
                'children': ['阅读理解', '阅读技巧', '文学阅读'],
                'related': ['词汇', '语法']
            },
            '听力': {
                'level': 2,
                'parent': '语言技能',
                'children': ['听力理解', '听力技巧', '语音辨识'],
                'related': ['词汇', '语音']
            },
            '写作': {
                'level': 2,
                'parent': '语言技能',
                'children': ['基础写作', '应用写作', '创意写作'],
                'related': ['语法', '词汇']
            }
        }
        
        # 知识点依赖关系
        self.dependencies = {
            '基础词汇': ['词汇'],
            '高级词汇': ['基础词汇'],
            '基础语法': ['语法'],
            '高级语法': ['基础语法'],
            '阅读理解': ['词汇', '语法'],
            '听力理解': ['词汇', '语音'],
            '写作表达': ['语法', '词汇']
        }
    
    def generate_knowledge_graph(self, user_id: int) -> Dict[str, Any]:
        """
        生成知识图谱
        
        Args:
            user_id: 用户ID
        
        Returns:
            知识图谱数据
        """
        try:
            # 获取用户掌握状态
            mastery_status = self._get_user_mastery_status(user_id)
            
            # 构建图谱节点
            nodes = self._build_graph_nodes(mastery_status)
            
            # 构建图谱边（关系）
            edges = self._build_graph_edges()
            
            # 计算用户学习路径
            user_path = self._calculate_user_path(mastery_status)
            
            # 生成可视化数据
            visualization_data = self._generate_visualization_data(nodes, edges, mastery_status)
            
            return {
                'user_id': user_id,
                'nodes': nodes,
                'edges': edges,
                'visualization': visualization_data,
                'user_learning_path': user_path,
                'mastery_summary': self._generate_mastery_summary(mastery_status),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"生成知识图谱失败: {str(e)}")
            return {'error': str(e)}
    
    def _get_user_mastery_status(self, user_id: int) -> Dict[str, Any]:
        """获取用户知识点掌握状态"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取学习记录中的知识点分布
                cursor.execute('''
                    SELECT subject, COUNT(*) as count FROM learning_records
                    WHERE user_id = ?
                    GROUP BY subject
                ''', (user_id,))
                learning_distribution = {row['subject']: row['count'] for row in cursor.fetchall()}
                
                # 获取错题知识点分布
                cursor.execute('''
                    SELECT knowledge_point, COUNT(*) as error_count, AVG(difficulty_level) as avg_difficulty
                    FROM wrong_questions
                    WHERE user_id = ?
                    GROUP BY knowledge_point
                ''', (user_id,))
                error_distribution = {}
                for row in cursor.fetchall():
                    kp = row['knowledge_point']
                    error_distribution[kp] = {
                        'error_count': row['error_count'],
                        'avg_difficulty': row['avg_difficulty']
                    }
                
                # 计算掌握程度
                mastery_levels = {}
                for category, points in self.knowledge_categories.items():
                    for point in points:
                        learning_count = learning_distribution.get(point, 0)
                        error_data = error_distribution.get(point, {})
                        error_count = error_data.get('error_count', 0)
                        
                        # 掌握程度计算公式
                        base_mastery = 50
                        learning_bonus = min(learning_count * 2, 30)
                        error_penalty = min(error_count * 5, 40)
                        mastery = max(0, min(100, base_mastery + learning_bonus - error_penalty))
                        
                        mastery_levels[point] = {
                            'mastery_level': mastery,
                            'learning_count': learning_count,
                            'error_count': error_count,
                            'status': self._get_mastery_status_label(mastery)
                        }
                
                return mastery_levels
        except Exception as e:
            logger.error(f"获取用户掌握状态失败: {str(e)}")
            # 返回默认状态
            return {point: {'mastery_level': 50, 'status': '学习中'} 
                    for category, points in self.knowledge_categories.items() 
                    for point in points}
    
    def _get_mastery_status_label(self, mastery: int) -> str:
        """获取掌握状态标签"""
        if mastery >= 80:
            return '已掌握'
        elif mastery >= 60:
            return '基本掌握'
        elif mastery >= 40:
            return '学习中'
        else:
            return '需强化'
    
    def _build_graph_nodes(self, mastery_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建图谱节点"""
        nodes = []
        
        # 添加分类节点
        for category, points in self.knowledge_categories.items():
            nodes.append({
                'id': category,
                'type': 'category',
                'label': category,
                'level': 0,
                'color': self._get_category_color(category),
                'size': 40,
                'mastery_level': None
            })
            
            # 添加知识点节点
            for point in points:
                mastery_data = mastery_status.get(point, {})
                mastery_level = mastery_data.get('mastery_level', 50)
                
                nodes.append({
                    'id': point,
                    'type': 'knowledge_point',
                    'label': point,
                    'level': 1,
                    'category': category,
                    'color': self._get_mastery_color(mastery_level),
                    'size': self._get_node_size(mastery_level),
                    'mastery_level': mastery_level,
                    'status': mastery_data.get('status', '学习中')
                })
                
                # 添加子知识点节点
                hierarchy = self.knowledge_hierarchy.get(point, {})
                children = hierarchy.get('children', [])
                for child in children:
                    nodes.append({
                        'id': child,
                        'type': 'sub_knowledge_point',
                        'label': child,
                        'level': 2,
                        'parent': point,
                        'color': '#e0e0e0',
                        'size': 20,
                        'mastery_level': mastery_level * 0.8  # 子知识点继承父知识点掌握程度
                    })
        
        return nodes
    
    def _get_category_color(self, category: str) -> str:
        """获取分类颜色"""
        colors = {
            '语言基础': '#4CAF50',
            '语言技能': '#2196F3',
            '语言应用': '#FF9800',
            '综合能力': '#9C27B0'
        }
        return colors.get(category, '#757575')
    
    def _get_mastery_color(self, mastery: int) -> str:
        """根据掌握程度获取颜色"""
        if mastery >= 80:
            return '#4CAF50'  # 绿色 - 已掌握
        elif mastery >= 60:
            return '#8BC34A'  # 浅绿 - 基本掌握
        elif mastery >= 40:
            return '#FFC107'  # 黄色 - 学习中
        else:
            return '#F44336'  # 红色 - 需强化
    
    def _get_node_size(self, mastery: int) -> int:
        """根据掌握程度获取节点大小"""
        base_size = 20
        mastery_bonus = mastery // 10
        return base_size + mastery_bonus
    
    def _build_graph_edges(self) -> List[Dict[str, Any]]:
        """构建图谱边（关系）"""
        edges = []
        
        # 分类到知识点的边
        for category, points in self.knowledge_categories.items():
            for point in points:
                edges.append({
                    'source': category,
                    'target': point,
                    'type': 'category_relation',
                    'label': '包含',
                    'weight': 1
                })
        
        # 知识点到子知识点的边
        for point, hierarchy in self.knowledge_hierarchy.items():
            children = hierarchy.get('children', [])
            for child in children:
                edges.append({
                    'source': point,
                    'target': child,
                    'type': 'parent_child',
                    'label': '子节点',
                    'weight': 2
                })
        
        # 知识点关联边
        for point, hierarchy in self.knowledge_hierarchy.items():
            related = hierarchy.get('related', [])
            for rel_point in related:
                edges.append({
                    'source': point,
                    'target': rel_point,
                    'type': 'knowledge_relation',
                    'label': '关联',
                    'weight': 1.5,
                    'dashed': True
                })
        
        # 依赖关系边
        for child, parents in self.dependencies.items():
            for parent in parents:
                edges.append({
                    'source': parent,
                    'target': child,
                    'type': 'dependency',
                    'label': '前置',
                    'weight': 3,
                    'arrow': True
                })
        
        return edges
    
    def _calculate_user_path(self, mastery_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算用户学习路径"""
        # 找出需要强化的知识点
        weak_points = [
            (point, data['mastery_level'])
            for point, data in mastery_status.items()
            if data['mastery_level'] < 60
        ]
        
        # 按掌握程度排序（最低优先）
        weak_points.sort(key=lambda x: x[1])
        
        # 构建学习路径
        path = []
        for point, mastery in weak_points:
            # 检查前置知识点
            prerequisites = self.dependencies.get(point, [])
            prereq_status = [
                (p, mastery_status.get(p, {}).get('mastery_level', 50))
                for p in prerequisites
            ]
            
            path.append({
                'knowledge_point': point,
                'current_mastery': mastery,
                'prerequisites': prereq_status,
                'can_start': all(s >= 40 for _, s in prereq_status),  # 前置知识点至少40%
                'priority': self._calculate_path_priority(mastery, prereq_status)
            })
        
        # 按优先级排序
        path.sort(key=lambda x: x['priority'], reverse=True)
        
        return path
    
    def _calculate_path_priority(self, mastery: int, prerequisites: List) -> int:
        """计算学习路径优先级"""
        # 掌握程度越低优先级越高
        mastery_score = 100 - mastery
        
        # 前置知识点满足程度
        prereq_score = sum(1 for _, s in prerequisites if s >= 60) * 20
        
        return mastery_score + prereq_score
    
    def _generate_visualization_data(self, nodes: List[Dict[str, Any]], 
                                     edges: List[Dict[str, Any]],
                                     mastery_status: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化数据"""
        return {
            'format': 'd3.js',
            'layout': 'force-directed',
            'nodes_data': nodes,
            'edges_data': edges,
            'color_scale': {
                'range': ['#F44336', '#FFC107', '#8BC34A', '#4CAF50'],
                'domain': [0, 40, 60, 80, 100],
                'label': '掌握程度'
            },
            'size_scale': {
                'range': [15, 30],
                'domain': [0, 100],
                'label': '学习进度'
            },
            'legend': [
                {'color': '#4CAF50', 'label': '已掌握 (≥80%)'},
                {'color': '#8BC34A', 'label': '基本掌握 (60-80%)'},
                {'color': '#FFC107', 'label': '学习中 (40-60%)'},
                {'color': '#F44336', 'label': '需强化 (<40%)'}
            ],
            'interactive_features': [
                '点击节点查看详情',
                '拖拽节点调整布局',
                '悬停显示掌握程度',
                '筛选特定分类'
            ]
        }
    
    def _generate_mastery_summary(self, mastery_status: Dict[str, Any]) -> Dict[str, Any]:
        """生成掌握程度摘要"""
        mastery_levels = [data['mastery_level'] for data in mastery_status.values()]
        
        # 统计各状态数量
        status_counts = defaultdict(int)
        for data in mastery_status.values():
            status_counts[data['status']] += 1
        
        return {
            'average_mastery': round(sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0, 1),
            'highest_mastery': max(mastery_levels) if mastery_levels else 0,
            'lowest_mastery': min(mastery_levels) if mastery_levels else 0,
            'status_distribution': dict(status_counts),
            'recommendation': self._generate_summary_recommendation(mastery_levels, status_counts)
        }
    
    def _generate_summary_recommendation(self, mastery_levels: List[int], 
                                         status_counts: Dict[str, int]) -> str:
        """生成摘要建议"""
        avg = sum(mastery_levels) / len(mastery_levels) if mastery_levels else 0
        
        if avg >= 70:
            return "整体掌握情况良好，建议继续保持并挑战更高难度"
        elif avg >= 50:
            return "基础掌握基本到位，建议重点强化薄弱知识点"
        else:
            return "需要加强基础学习，建议从基础知识点开始系统学习"
    
    def get_knowledge_point_details(self, knowledge_point: str) -> Dict[str, Any]:
        """获取知识点详情"""
        hierarchy = self.knowledge_hierarchy.get(knowledge_point, {})
        
        return {
            'knowledge_point': knowledge_point,
            'level': hierarchy.get('level', 1),
            'category': hierarchy.get('parent', '未知'),
            'children': hierarchy.get('children', []),
            'related_points': hierarchy.get('related', []),
            'prerequisites': self.dependencies.get(knowledge_point, []),
            'learning_resources': self._get_learning_resources(knowledge_point),
            'practice_suggestions': self._get_practice_suggestions(knowledge_point)
        }
    
    def _get_learning_resources(self, knowledge_point: str) -> List[str]:
        """获取学习资源推荐"""
        resources_mapping = {
            '词汇': ['词汇卡片', '记忆APP', '词汇书籍', '例句练习'],
            '语法': ['语法书', '语法视频', '练习题', '语法总结'],
            '阅读': ['阅读材料', '阅读技巧书', '真题阅读', '文学作品'],
            '听力': ['听力材料', '音频练习', '听力APP', '真题听力'],
            '写作': ['写作模板', '范文分析', '写作练习', '写作指导书']
        }
        return resources_mapping.get(knowledge_point, ['综合学习资料', '练习题库', '在线课程'])
    
    def _get_practice_suggestions(self, knowledge_point: str) -> List[str]:
        """获取练习建议"""
        suggestions_mapping = {
            '词汇': ['每日背诵20个新词', '复习昨日词汇', '做词汇练习题'],
            '语法': ['分析句子结构', '语法填空练习', '改错练习'],
            '阅读': ['每日阅读一篇', '总结阅读技巧', '做阅读理解题'],
            '听力': ['每日听力训练30分钟', '跟读练习', '听力理解题'],
            '写作': ['模仿范文写作', '写作练习', '教师批改反馈']
        }
        return suggestions_mapping.get(knowledge_point, ['每日练习', '总结反思', '错题重做'])


# 创建全局实例
learning_path_planner = LearningPathPlanner()
wrong_question_recommender = WrongQuestionRecommender()
knowledge_graph_visualizer = KnowledgeGraphVisualizer()


# ==================== API路由定义 ====================

@learning_enhancement_api.route('/path/generate', methods=['POST'])
def generate_learning_path():
    """生成个性化学习路径"""
    try:
        data = request.get_json()
        user_id = session.get('user_id') or data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        current_level = data.get('current_level', '中级')
        learning_goal = data.get('learning_goal', '能力提升')
        available_time = data.get('available_time', 10)  # 每周10小时
        
        result = learning_path_planner.generate_personalized_path(
            user_id, current_level, learning_goal, available_time
        )
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"生成学习路径API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/path/progress', methods=['POST'])
def update_learning_progress():
    """更新学习进度"""
    try:
        data = request.get_json()
        user_id = session.get('user_id') or data.get('user_id')
        stage_id = data.get('stage_id')
        completed_activities = data.get('completed_activities', [])
        
        if not user_id or not stage_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        result = learning_path_planner.update_learning_progress(
            user_id, stage_id, completed_activities
        )
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"更新学习进度API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/path/sequence', methods=['GET'])
def get_recommended_sequence():
    """获取推荐学习顺序"""
    try:
        user_id = session.get('user_id') or request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        sequence = learning_path_planner.get_recommended_sequence(user_id)
        
        return jsonify({'success': True, 'data': sequence})
    except Exception as e:
        logger.error(f"获取推荐学习顺序API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/wrong-questions/recommend', methods=['GET'])
def recommend_wrong_question_practice():
    """错题智能推荐"""
    try:
        user_id = session.get('user_id') or request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        result = wrong_question_recommender.recommend_targeted_practice(user_id)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"错题推荐API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/wrong-questions/schedule', methods=['POST'])
def generate_review_schedule():
    """生成错题复习计划"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id') or data.get('user_id')
        review_mode = data.get('review_mode', 'balanced')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        result = wrong_question_recommender.generate_review_schedule(user_id, review_mode)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"生成复习计划API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/knowledge-graph/generate', methods=['GET'])
def generate_knowledge_graph():
    """生成知识图谱"""
    try:
        user_id = session.get('user_id') or request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        result = knowledge_graph_visualizer.generate_knowledge_graph(user_id)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"生成知识图谱API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/knowledge-graph/details/<knowledge_point>', methods=['GET'])
def get_knowledge_point_details(knowledge_point):
    """获取知识点详情"""
    try:
        result = knowledge_graph_visualizer.get_knowledge_point_details(knowledge_point)
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取知识点详情API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_enhancement_api.route('/comprehensive-analysis', methods=['GET'])
def get_comprehensive_analysis():
    """获取综合学习分析"""
    try:
        user_id = session.get('user_id') or request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        # 整合三个模块的分析结果
        path_result = learning_path_planner.get_recommended_sequence(user_id)
        wrong_result = wrong_question_recommender.recommend_targeted_practice(user_id)
        graph_result = knowledge_graph_visualizer.generate_knowledge_graph(user_id)
        
        comprehensive = {
            'user_id': user_id,
            'learning_path': path_result,
            'wrong_question_analysis': wrong_result,
            'knowledge_graph': graph_result,
            'overall_recommendation': _generate_overall_recommendation(path_result, wrong_result, graph_result),
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'data': comprehensive})
    except Exception as e:
        logger.error(f"综合分析API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _generate_overall_recommendation(path_result, wrong_result, graph_result) -> Dict[str, Any]:
    """生成整体学习建议"""
    recommendations = []
    
    # 从学习路径添加建议
    if isinstance(path_result, list) and path_result:
        recommendations.append({
            'source': '学习路径',
            'priority': 'high',
            'content': f"建议优先学习：{path_result[0].get('knowledge_point', '基础知识')}",
            'reason': '根据知识依赖关系，先掌握前置知识点'
        })
    
    # 从错题分析添加建议
    if isinstance(wrong_result, dict) and wrong_result.get('recommendations'):
        first_rec = wrong_result['recommendations'][0]
        recommendations.append({
            'source': '错题分析',
            'priority': 'high',
            'content': f"建议重点练习：{first_rec.get('error_type', '综合')}类型题目",
            'reason': f"该类型错误频率最高({first_rec.get('frequency', 0)}次)"
        })
    
    # 从知识图谱添加建议
    if isinstance(graph_result, dict) and graph_result.get('user_learning_path'):
        first_path = graph_result['user_learning_path'][0]
        recommendations.append({
            'source': '知识图谱',
            'priority': 'medium',
            'content': f"建议强化知识点：{first_path.get('knowledge_point', '基础')}",
            'reason': f"当前掌握程度：{first_path.get('current_mastery', 0)}%"
        })
    
    return {
        'recommendations': recommendations,
        'total_study_time_estimate': '建议每日学习2-3小时',
        'weekly_focus': '本周重点攻克高频错题和薄弱知识点',
        'progress_check': '建议每周进行一次知识点测试评估进度'
    }


@learning_enhancement_api.route('/capabilities', methods=['GET'])
def get_capabilities():
    """获取学习增强系统能力说明"""
    capabilities = {
        'name': '学习增强系统',
        'version': '1.0.0',
        'modules': [
            {
                'name': '学习路径规划器',
                'description': '根据用户情况生成个性化学习路径',
                'features': [
                    '个性化路径生成',
                    '学习阶段划分',
                    '每日计划制定',
                    '里程碑设置',
                    '进度追踪'
                ],
                'api_endpoints': [
                    '/path/generate',
                    '/path/progress',
                    '/path/sequence'
                ]
            },
            {
                'name': '错题智能推荐器',
                'description': '智能分析错题并推荐针对性练习',
                'features': [
                    '错题类型分析',
                    '知识点关联推荐',
                    '练习量估算',
                    '复习计划生成',
                    '学习方法建议'
                ],
                'api_endpoints': [
                    '/wrong-questions/recommend',
                    '/wrong-questions/schedule'
                ]
            },
            {
                'name': '知识图谱可视化器',
                'description': '构建和展示知识点关联图谱',
                'features': [
                    '知识点层级结构',
                    '掌握程度可视化',
                    '依赖关系展示',
                    '学习路径计算',
                    '知识点详情查询'
                ],
                'api_endpoints': [
                    '/knowledge-graph/generate',
                    '/knowledge-graph/details/<knowledge_point>'
                ]
            }
        ],
        'integration_features': [
            '综合学习分析',
            '整体学习建议',
            '跨模块数据整合',
            '进度同步追踪'
        ]
    }
    
    return jsonify({'success': True, 'data': capabilities})