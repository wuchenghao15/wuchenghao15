#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI员工审评制度模块
负责AI员工的绩效评估、表现审查和职业发展管理
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logger = logging.getLogger('ai_performance_review')

class AIPerformanceReviewSystem:
    """AI员工审评系统类"""
    
    def __init__(self):
        """初始化AI员工审评系统"""
        # 审评指标和标准
        self.review_criteria = {
            'performance': {
                'name': '工作表现',
                'weight': 0.4,
                'sub_criteria': {
                    'task_completion': {
                        'name': '任务完成率',
                        'weight': 0.4
                    },
                    'quality': {
                        'name': '工作质量',
                        'weight': 0.3
                    },
                    'efficiency': {
                        'name': '工作效率',
                        'weight': 0.3
                    }
                }
            },
            'skills': {
                'name': '技能水平',
                'weight': 0.3,
                'sub_criteria': {
                    'technical_skills': {
                        'name': '技术技能',
                        'weight': 0.5
                    },
                    'soft_skills': {
                        'name': '软技能',
                        'weight': 0.3
                    },
                    'learning_ability': {
                        'name': '学习能力',
                        'weight': 0.2
                    }
                }
            },
            'teamwork': {
                'name': '团队协作',
                'weight': 0.2,
                'sub_criteria': {
                    'collaboration': {
                        'name': '协作能力',
                        'weight': 0.5
                    },
                    'communication': {
                        'name': '沟通能力',
                        'weight': 0.5
                    }
                }
            },
            'innovation': {
                'name': '创新能力',
                'weight': 0.1,
                'sub_criteria': {
                    'problem_solving': {
                        'name': '问题解决',
                        'weight': 0.6
                    },
                    'creativity': {
                        'name': '创造力',
                        'weight': 0.4
                    }
                }
            }
        }
        
        # 绩效等级
        self.performance_levels = {
            'excellent': {
                'range': [4.5, 5.0],
                'description': '表现优异，超出预期'
            },
            'good': {
                'range': [3.5, 4.4],
                'description': '表现良好，达到预期'
            },
            'average': {
                'range': [2.5, 3.4],
                'description': '表现一般，基本达到预期'
            },
            'needs_improvement': {
                'range': [1.5, 2.4],
                'description': '需要改进，未达到预期'
            },
            'poor': {
                'range': [0.0, 1.4],
                'description': '表现较差，严重未达到预期'
            }
        }
        
        # 审评记录
        self.review_records = {}
        # 绩效目标
        self.performance_goals = {}
        # 改进计划
        self.improvement_plans = {}
        # 职业发展计划
        self.career_development_plans = {}
        
        logger.info("AI员工审评系统初始化完成")
    
    def get_review_criteria(self) -> Dict[str, Any]:
        """获取审评标准"""
        return self.review_criteria
    
    def create_performance_review(self, ai_instance_id: str, reviewer_id: str, 
                                review_period: str, ratings: Dict[str, Any],
                                comments: str = None, goals: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建绩效审评"""
        try:
            review_id = f"review_{ai_instance_id}_{review_period}_{datetime.now().timestamp()}"
            
            # 计算总分
            total_score = self._calculate_total_score(ratings)
            performance_level = self._determine_performance_level(total_score)
            
            # 创建审评记录
            self.review_records[review_id] = {
                'review_id': review_id,
                'ai_instance_id': ai_instance_id,
                'reviewer_id': reviewer_id,
                'review_period': review_period,
                'ratings': ratings,
                'total_score': total_score,
                'performance_level': performance_level,
                'comments': comments,
                'goals': goals,
                'created_at': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            # 生成改进计划
            if goals:
                improvement_plan = self._generate_improvement_plan(ai_instance_id, goals)
                self.improvement_plans[review_id] = improvement_plan
            
            result = {
                'success': True,
                'review_id': review_id,
                'ai_instance_id': ai_instance_id,
                'total_score': total_score,
                'performance_level': performance_level,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"为AI {ai_instance_id} 创建绩效审评: {review_id}")
            return result
        except Exception as e:
            logger.error(f"创建绩效审评失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_total_score(self, ratings: Dict[str, Any]) -> float:
        """计算总评分"""
        total_score = 0.0
        
        for category, category_data in self.review_criteria.items():
            category_score = 0.0
            category_weight = category_data['weight']
            
            for sub_criterion, sub_data in category_data['sub_criteria'].items():
                if category in ratings and sub_criterion in ratings[category]:
                    sub_score = ratings[category][sub_criterion]
                    sub_weight = sub_data['weight']
                    category_score += sub_score * sub_weight
            
            total_score += category_score * category_weight
        
        return round(total_score, 2)
    
    def _determine_performance_level(self, score: float) -> str:
        """确定绩效等级"""
        for level, level_data in self.performance_levels.items():
            min_score, max_score = level_data['range']
            if min_score <= score <= max_score:
                return level
        return 'average'  # 默认等级
    
    def _generate_improvement_plan(self, ai_instance_id: str, goals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成改进计划"""
        improvement_plan = {
            'ai_instance_id': ai_instance_id,
            'goals': goals,
            'action_items': [],
            'timeline': {},
            'created_at': datetime.now().isoformat()
        }
        
        # 为每个目标生成行动项
        for goal in goals:
            action_item = {
                'goal': goal['description'],
                'actions': goal.get('actions', []),
                'deadline': goal.get('deadline', None),
                'status': 'pending'
            }
            improvement_plan['action_items'].append(action_item)
        
        return improvement_plan
    
    def update_improvement_plan(self, review_id: str, progress: Dict[str, Any]) -> Dict[str, Any]:
        """更新改进计划"""
        try:
            if review_id not in self.improvement_plans:
                return {
                    'success': False,
                    'error': f'改进计划不存在: {review_id}'
                }
            
            # 更新改进计划
            self.improvement_plans[review_id]['progress'] = progress
            self.improvement_plans[review_id]['updated_at'] = datetime.now().isoformat()
            
            result = {
                'success': True,
                'review_id': review_id,
                'message': '改进计划更新成功',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"更新改进计划: {review_id}")
            return result
        except Exception as e:
            logger.error(f"更新改进计划失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_career_development_plan(self, ai_instance_id: str, 
                                    career_goals: List[Dict[str, Any]],
                                    skills_to_develop: List[str]) -> Dict[str, Any]:
        """创建职业发展计划"""
        try:
            plan_id = f"career_plan_{ai_instance_id}_{datetime.now().timestamp()}"
            
            career_plan = {
                'plan_id': plan_id,
                'ai_instance_id': ai_instance_id,
                'career_goals': career_goals,
                'skills_to_develop': skills_to_develop,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.career_development_plans[plan_id] = career_plan
            
            result = {
                'success': True,
                'plan_id': plan_id,
                'ai_instance_id': ai_instance_id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"为AI {ai_instance_id} 创建职业发展计划: {plan_id}")
            return result
        except Exception as e:
            logger.error(f"创建职业发展计划失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_review_history(self, ai_instance_id: str) -> List[Dict[str, Any]]:
        """获取AI的审评历史"""
        history = []
        for review_id, review in self.review_records.items():
            if review['ai_instance_id'] == ai_instance_id:
                history.append(review)
        
        # 按时间排序
        history.sort(key=lambda x: x['created_at'], reverse=True)
        return history
    
    def get_performance_trend(self, ai_instance_id: str) -> Dict[str, Any]:
        """获取AI的绩效趋势"""
        history = self.get_review_history(ai_instance_id)
        
        if not history:
            return {
                'success': False,
                'error': '没有审评记录'
            }
        
        # 提取分数和时间
        scores = []
        dates = []
        levels = []
        
        for review in history:
            scores.append(review['total_score'])
            dates.append(review['created_at'])
            levels.append(review['performance_level'])
        
        # 计算趋势
        trend = 'improving' if scores[0] > scores[-1] else 'declining' if scores[0] < scores[-1] else 'stable'
        
        result = {
            'success': True,
            'ai_instance_id': ai_instance_id,
            'scores': scores,
            'dates': dates,
            'levels': levels,
            'trend': trend,
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores)
        }
        
        return result
    
    def generate_performance_report(self, ai_instance_id: str) -> Dict[str, Any]:
        """生成绩效报告"""
        try:
            history = self.get_review_history(ai_instance_id)
            trend = self.get_performance_trend(ai_instance_id)
            
            if not history:
                return {
                    'success': False,
                    'error': '没有审评记录'
                }
            
            # 最新审评
            latest_review = history[0]
            
            report = {
                'ai_instance_id': ai_instance_id,
                'report_date': datetime.now().isoformat(),
                'latest_review': latest_review,
                'performance_trend': trend,
                'total_reviews': len(history),
                'recommendations': self._generate_recommendations(ai_instance_id, latest_review)
            }
            
            logger.info(f"为AI {ai_instance_id} 生成绩效报告")
            return report
        except Exception as e:
            logger.error(f"生成绩效报告失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_recommendations(self, ai_instance_id: str, latest_review: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 根据绩效等级生成建议
        if latest_review['performance_level'] == 'excellent':
            recommendations.append('考虑承担更具挑战性的任务')
            recommendations.append('作为团队的技术顾问')
            recommendations.append('参与知识分享和培训')
        elif latest_review['performance_level'] == 'good':
            recommendations.append('继续保持良好表现')
            recommendations.append('关注技能提升')
            recommendations.append('设定更高的目标')
        elif latest_review['performance_level'] == 'average':
            recommendations.append('加强技能培训')
            recommendations.append('提高工作效率')
            recommendations.append('寻求导师指导')
        else:
            recommendations.append('制定详细的改进计划')
            recommendations.append('参加相关培训')
            recommendations.append('定期接受绩效辅导')
        
        return recommendations
    
    def get_all_reviews(self) -> Dict[str, Any]:
        """获取所有审评记录"""
        return self.review_records
    
    def get_all_improvement_plans(self) -> Dict[str, Any]:
        """获取所有改进计划"""
        return self.improvement_plans
    
    def get_all_career_plans(self) -> Dict[str, Any]:
        """获取所有职业发展计划"""
        return self.career_development_plans

# 创建全局AI员工审评系统实例
ai_performance_review_system = AIPerformanceReviewSystem()

if __name__ == '__main__':
    print("AI员工审评系统初始化成功")
    print(f"审评标准数量: {len(ai_performance_review_system.review_criteria)}")
    print(f"绩效等级数量: {len(ai_performance_review_system.performance_levels)}")
