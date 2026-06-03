# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI员工审评制度模块
负责AI员工的绩效评估、表现审查和职业发展管理
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logger = logging.getLogger('ai_performance_review')


class AIPerformanceReviewSystem:
    """AI员工审评系统类"""

    def __init__(self):
        """初始化AI员工审评系统"""
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
                'weight': 0.4,
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

        self.performance_levels = {
            'excellent': {
                'range': [4.5, 5.0],
                'description': '表现优异,超出预期'
            },
            'good': {
                'range': [3.5, 4.4],
                'description': '表现良好,达到预期'
            },
            'needs_improvement': {
                'range': [1.5, 3.4],
                'description': '需要改进,未达到预期'
            },
            'poor': {
                'range': [0.0, 1.4],
                'description': '表现较差,严重未达到预期'
            }
        }

        self.review_records = {}
        self.performance_goals = {}
        self.improvement_plans = {}
        self.career_development_plans = {}

        logger.info("AI员工审评系统初始化完成")

    def get_review_criteria(self) -> Dict[str, Any]:
        """获取审评标准"""
        return self.review_criteria

    def conduct_review(self, ai_employee_id: str, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """进行审评"""
        try:
            review_id = f"review_{ai_employee_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            review_record = {
                'review_id': review_id,
                'ai_employee_id': ai_employee_id,
                'review_date': datetime.now().isoformat(),
                'scores': review_data.get('scores', {}),
                'comments': review_data.get('comments', ''),
                'reviewer': review_data.get('reviewer', 'system'),
                'overall_score': self._calculate_overall_score(review_data.get('scores', {}))
            }

            self.review_records[review_id] = review_record
            logger.info(f"审评完成: {review_id}")
            
            return review_record
        except Exception as e:
            logger.error(f"进行审评失败: {str(e)}")
            return {}

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """计算总体得分"""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for criterion, data in self.review_criteria.items():
                if criterion in scores:
                    weight = data.get('weight', 0)
                    total_score += scores[criterion] * weight
                    total_weight += weight
            
            if total_weight > 0:
                return round(total_score / total_weight, 2)
            return 0.0
        except Exception as e:
            logger.error(f"计算总体得分失败: {str(e)}")
            return 0.0

    def get_performance_level(self, score: float) -> str:
        """获取绩效等级"""
        for level, data in self.performance_levels.items():
            if data['range'][0] <= score <= data['range'][1]:
                return level
        return 'unknown'

    def set_performance_goal(self, ai_employee_id: str, goal: Dict[str, Any]) -> bool:
        """设置绩效目标"""
        try:
            if ai_employee_id not in self.performance_goals:
                self.performance_goals[ai_employee_id] = []
            self.performance_goals[ai_employee_id].append(goal)
            logger.info(f"设置绩效目标: {ai_employee_id}")
            return True
        except Exception as e:
            logger.error(f"设置绩效目标失败: {str(e)}")
            return False

    def create_improvement_plan(self, ai_employee_id: str, plan: Dict[str, Any]) -> bool:
        """创建改进计划"""
        try:
            self.improvement_plans[ai_employee_id] = plan
            logger.info(f"创建改进计划: {ai_employee_id}")
            return True
        except Exception as e:
            logger.error(f"创建改进计划失败: {str(e)}")
            return False
