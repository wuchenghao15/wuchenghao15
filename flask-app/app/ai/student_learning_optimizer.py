#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI学生考试学习能力优化系统
提供个性化的学习路径优化和考试策略指导
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from collections import defaultdict
from app.utils.logging import logger


class StudentPerformanceAnalyzer:
    """学生学习表现分析器"""
    
    def __init__(self):
        # 知识点权重配置
        self.difficulty_weights = {
            1: 1.0,   # 简单
            2: 1.5,   # 较易
            3: 2.0,   # 中等
            4: 2.5,   # 较难
            5: 3.0    # 困难
        }
    
    def analyze_performance(self, exam_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析学习表现"""
        if not exam_records:
            return {
                'total_exams': 0,
                'average_score': 0,
                'trend': 'insufficient_data',
                'strengths': [],
                'weaknesses': []
            }
        
        # 计算基本统计
        total_exams = len(exam_records)
        scores = [r.get('score', 0) for r in exam_records]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # 分析趋势
        if total_exams >= 3:
            recent_scores = scores[-3:]
            early_scores = scores[:3]
            recent_avg = sum(recent_scores) / len(recent_scores)
            early_avg = sum(early_scores) / len(early_scores)
            
            if recent_avg > early_avg + 5:
                trend = 'improving'
            elif recent_avg < early_avg - 5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # 分析正确率分布
        accuracy_by_type = self._analyze_by_question_type(exam_records)
        
        # 识别优势和劣势
        strengths = []
        weaknesses = []
        
        for qtype, stats in accuracy_by_type.items():
            if stats['avg_accuracy'] >= 80:
                strengths.append({
                    'type': qtype,
                    'accuracy': stats['avg_accuracy'],
                    'count': stats['count']
                })
            elif stats['avg_accuracy'] < 60:
                weaknesses.append({
                    'type': qtype,
                    'accuracy': stats['avg_accuracy'],
                    'count': stats['count']
                })
        
        # 分析时间效率
        time_analysis = self._analyze_time_efficiency(exam_records)
        
        return {
            'total_exams': total_exams,
            'average_score': round(average_score, 2),
            'highest_score': max(scores) if scores else 0,
            'lowest_score': min(scores) if scores else 0,
            'trend': trend,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'accuracy_by_type': accuracy_by_type,
            'time_analysis': time_analysis
        }
    
    def _analyze_by_question_type(self, exam_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按题目类型分析"""
        type_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for record in exam_records:
            # 假设exam_records包含题目分析详情
            if 'question_analysis' in record:
                for qa in record['question_analysis']:
                    qtype = qa.get('type', 'unknown')
                    is_correct = qa.get('is_correct', False)
                    type_stats[qtype]['total'] += 1
                    if is_correct:
                        type_stats[qtype]['correct'] += 1
        
        # 计算准确率
        result = {}
        for qtype, stats in type_stats.items():
            accuracy = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            result[qtype] = {
                'avg_accuracy': round(accuracy, 2),
                'count': stats['total']
            }
        
        return result
    
    def _analyze_time_efficiency(self, exam_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析时间效率"""
        if not exam_records:
            return {'average_time': 0, 'efficient': True}
        
        total_time = sum(r.get('time_taken', 0) for r in exam_records)
        total_questions = sum(r.get('question_count', 0) for r in exam_records)
        
        avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
        
        return {
            'average_time_per_question': round(avg_time_per_question, 1),
            'efficient': avg_time_per_question < 120  # 假设每题2分钟内为高效
        }


class KnowledgeGapIdentifier:
    """知识漏洞识别器"""
    
    def __init__(self):
        # 知识点分类配置
        self.knowledge_categories = {
            'vocabulary': '词汇',
            'grammar': '语法',
            'listening': '听力',
            'reading': '阅读',
            'writing': '写作',
            'culture': '文化'
        }
    
    def identify_gaps(self, question_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别知识漏洞"""
        gap_scores = defaultdict(lambda: {'correct': 0, 'total': 0, 'weighted_score': 0.0})
        
        for qa in question_analysis:
            tags = qa.get('tags', [])
            difficulty = qa.get('difficulty', 1)
            is_correct = qa.get('is_correct', False)
            
            for tag in tags:
                gap_scores[tag]['total'] += 1
                if is_correct:
                    gap_scores[tag]['correct'] += 1
                    gap_scores[tag]['weighted_score'] += 10 / difficulty
                else:
                    gap_scores[tag]['weighted_score'] -= 5 * difficulty
        
        # 计算漏洞程度
        gaps = []
        for tag, stats in gap_scores.items():
            if stats['total'] >= 3:  # 至少回答3次
                accuracy = stats['correct'] / stats['total']
                gap_severity = self._calculate_gap_severity(accuracy, stats['total'])
                
                if gap_severity > 0.3:  # 超过30%的漏洞程度
                    gaps.append({
                        'knowledge_point': tag,
                        'accuracy': round(accuracy * 100, 2),
                        'gap_severity': round(gap_severity, 2),
                        'attempts': stats['total'],
                        'priority': self._calculate_priority(gap_severity, stats['total'])
                    })
        
        # 按严重程度排序
        gaps.sort(key=lambda x: x['gap_severity'], reverse=True)
        
        return {
            'identified_gaps': gaps[:10],  # 返回最严重的10个漏洞
            'total_gaps': len(gaps),
            'category_analysis': self._analyze_by_category(gaps)
        }
    
    def _calculate_gap_severity(self, accuracy: float, attempts: int) -> float:
        """计算漏洞严重程度"""
        # 基础严重程度
        base_severity = 1 - accuracy
        
        # 考虑尝试次数的调整
        attempts_factor = min(attempts / 10, 1.0)  # 最多10次，线性增长
        
        return base_severity * (0.5 + 0.5 * attempts_factor)
    
    def _calculate_priority(self, gap_severity: float, attempts: int) -> str:
        """计算优先级"""
        if gap_severity > 0.7 and attempts >= 5:
            return 'urgent'
        elif gap_severity > 0.5:
            return 'high'
        elif gap_severity > 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_by_category(self, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按类别分析漏洞"""
        category_gaps = defaultdict(list)
        
        for gap in gaps:
            # 简单分类
            tag = gap['knowledge_point']
            if any(kw in tag for kw in ['词汇', '单词', 'vocab']):
                category = 'vocabulary'
            elif any(kw in tag for kw in ['语法', 'grammar']):
                category = 'grammar'
            elif any(kw in tag for kw in ['听力', 'listen']):
                category = 'listening'
            elif any(kw in tag for kw in ['阅读', 'read']):
                category = 'reading'
            elif any(kw in tag for kw in ['写作', 'write']):
                category = 'writing'
            else:
                category = 'other'
            
            category_gaps[category].append(gap)
        
        return {
            category: {
                'count': len(gaps),
                'avg_severity': round(sum(g['gap_severity'] for g in gaps) / len(gaps), 2) if gaps else 0
            }
            for category, gaps in category_gaps.items()
        }


class LearningPathOptimizer:
    """学习路径优化器"""
    
    def __init__(self):
        self.daily_study_hours = 2.0
        self.weakness_weight = 2.0
    
    def generate_learning_path(self, gaps: Dict[str, Any], 
                              performance: Dict[str, Any]) -> Dict[str, Any]:
        """生成个性化学习路径"""
        if not gaps.get('identified_gaps'):
            return {
                'path_type': 'maintenance',
                'daily_plan': self._generate_maintenance_plan(),
                'weekly_goals': []
            }
        
        # 排序学习任务
        prioritized_tasks = self._prioritize_learning_tasks(gaps, performance)
        
        # 生成每日计划
        daily_plan = self._generate_daily_plan(prioritized_tasks)
        
        # 生成每周目标
        weekly_goals = self._generate_weekly_goals(prioritized_tasks)
        
        return {
            'path_type': 'improvement',
            'prioritized_tasks': prioritized_tasks[:10],
            'daily_plan': daily_plan,
            'weekly_goals': weekly_goals,
            'estimated_improvement': self._estimate_improvement(prioritized_tasks)
        }
    
    def _prioritize_learning_tasks(self, gaps: Dict[str, Any], 
                                  performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """优先级排序学习任务"""
        tasks = []
        
        # 从漏洞生成任务
        for gap in gaps.get('identified_gaps', []):
            tasks.append({
                'topic': gap['knowledge_point'],
                'priority': gap['priority'],
                'gap_severity': gap['gap_severity'],
                'type': 'weakness_improvement',
                'study_time': self._calculate_study_time(gap['gap_severity']),
                'resources': self._suggest_resources(gap['knowledge_point'])
            })
        
        # 从优势生成任务（保持领先）
        for strength in performance.get('strengths', []):
            tasks.append({
                'topic': strength['type'],
                'priority': 'low',
                'gap_severity': 0,
                'type': 'strength_maintenance',
                'study_time': 30,  # 30分钟保持练习
                'resources': self._suggest_resources(strength['type'])
            })
        
        # 按优先级排序
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        tasks.sort(key=lambda x: (priority_order.get(x['priority'], 4), -x['gap_severity']))
        
        return tasks
    
    def _generate_daily_plan(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成每日学习计划"""
        plan = []
        remaining_hours = self.daily_study_hours
        
        for task in tasks:
            if remaining_hours <= 0:
                break
            
            study_time = min(task['study_time'] / 60, remaining_hours)  # 转换为小时
            plan.append({
                'topic': task['topic'],
                'duration_minutes': int(study_time * 60),
                'type': task['type'],
                'priority': task['priority']
            })
            
            remaining_hours -= study_time
        
        return plan
    
    def _generate_weekly_goals(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成每周目标"""
        weekly_goals = []
        
        # 假设每周重点攻克2-3个知识点
        priority_tasks = [t for t in tasks if t['priority'] in ['urgent', 'high']][:3]
        
        for i, task in enumerate(priority_tasks):
            weekly_goals.append({
                'week': i + 1,
                'focus_topic': task['topic'],
                'target_accuracy': min(80, 60 + task['gap_severity'] * 20),
                'study_hours': task['study_time'] * 7 / 60,
                'success_criteria': f"在练习中达到{self._format_target(task)}的正确率"
            })
        
        return weekly_goals
    
    def _generate_maintenance_plan(self) -> Dict[str, Any]:
        """生成保持型计划（无漏洞时）"""
        return {
            'daily_review': 30,  # 每日复习30分钟
            'practice_exercises': 20,  # 练习20题
            'weakness_check': '每周评估一次'
        }
    
    def _calculate_study_time(self, gap_severity: float) -> int:
        """计算学习时间（分钟）"""
        base_time = 60  # 基础60分钟
        severity_factor = gap_severity * 60  # 根据严重程度增加时间
        return int(base_time + severity_factor)
    
    def _suggest_resources(self, topic: str) -> List[str]:
        """推荐学习资源"""
        resources = {
            'vocabulary': ['词汇卡片', '记忆APP', '例句练习'],
            'grammar': ['语法书', '练习题', '语法视频'],
            'listening': ['听力材料', '音频练习', '真题听力'],
            'reading': ['阅读材料', '速读练习', '真题阅读'],
            'writing': ['写作模板', '范文分析', '写作练习']
        }
        
        # 简单匹配
        topic_lower = topic.lower()
        for key, res in resources.items():
            if key in topic_lower:
                return res
        
        return ['综合学习资料', '练习题库', '在线课程']
    
    def _estimate_improvement(self, tasks: List[Dict[str, Any]]) -> str:
        """预估改善情况"""
        if not tasks:
            return "当前表现良好，建议保持练习"
        
        urgent_tasks = len([t for t in tasks if t['priority'] == 'urgent'])
        high_tasks = len([t for t in tasks if t['priority'] == 'high'])
        
        if urgent_tasks >= 2:
            return "预计2-3周可显著改善主要漏洞"
        elif high_tasks >= 2:
            return "预计4-6周可提升整体水平"
        else:
            return "预计1-2周可优化薄弱环节"
    
    def _format_target(self, task: Dict[str, Any]) -> str:
        """格式化目标"""
        return f"{task['target_accuracy']:.0f}%" if task.get('target_accuracy') else "80%"


class ExamStrategyAdvisor:
    """考试策略顾问"""
    
    def __init__(self):
        # 时间分配权重
        self.difficulty_weights = {
            'easy': 1.0,
            'medium': 1.5,
            'hard': 2.0
        }
    
    def generate_exam_strategy(self, performance: Dict[str, Any], 
                              exam_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成考试策略"""
        # 分析应该先做还是后做某种题型
        question_order = self._optimize_question_order(performance)
        
        # 计算时间分配
        time_allocation = self._calculate_time_allocation(exam_config, performance)
        
        # 生成答题技巧
        tips = self._generate_exam_tips(performance)
        
        return {
            'question_order': question_order,
            'time_allocation': time_allocation,
            'tips': tips,
            'stress_management': self._generate_stress_management()
        }
    
    def _optimize_question_order(self, performance: Dict[str, Any]) -> List[str]:
        """优化题目顺序"""
        # 先做擅长的题目建立信心
        strengths = performance.get('strengths', [])
        weaknesses = performance.get('weaknesses', [])
        
        order = []
        
        # 添加擅长的题型（优先）
        for s in strengths:
            order.append({
                'type': s['type'],
                'reason': f"正确率{s['accuracy']}%，建议优先完成"
            })
        
        # 添加中等问题
        order.append({
            'type': 'medium_difficulty',
            'reason': "中等难度题目，性价比高"
        })
        
        # 添加劣势题型（根据情况决定顺序）
        if weaknesses:
            order.append({
                'type': 'weakness_first',
                'reason': "趁头脑清醒先解决难题" if performance.get('trend') == 'improving' else "留到最后处理"
            })
        
        return order
    
    def _calculate_time_allocation(self, exam_config: Dict[str, Any], 
                                  performance: Dict[str, Any]) -> Dict[str, Any]:
        """计算时间分配"""
        total_time = exam_config.get('duration', 60) * 60  # 转换为秒
        total_questions = exam_config.get('question_count', 50)
        
        avg_time_per_question = total_time / total_questions
        
        # 根据表现调整时间
        strengths = performance.get('strengths', [])
        weaknesses = performance.get('weaknesses', [])
        
        time_allocation = {
            'strength_questions': {
                'time_per_question': int(avg_time_per_question * 0.8),
                'total_questions': len(strengths) * 5 if strengths else total_questions * 0.4
            },
            'medium_questions': {
                'time_per_question': int(avg_time_per_question),
                'total_questions': total_questions * 0.4
            },
            'weakness_questions': {
                'time_per_question': int(avg_time_per_question * 1.5),
                'total_questions': len(weaknesses) * 3 if weaknesses else total_questions * 0.2
            }
        }
        
        return time_allocation
    
    def _generate_exam_tips(self, performance: Dict[str, Any]) -> List[str]:
        """生成考试技巧"""
        tips = []
        trend = performance.get('trend', 'stable')
        
        if trend == 'improving':
            tips.append("近期表现提升，保持当前节奏")
            tips.append("相信自己，已经看到进步")
        elif trend == 'declining':
            tips.append("注意调整心态，不要压力过大")
            tips.append("回顾错题，找出规律")
        else:
            tips.append("稳扎稳打，不要急于求成")
        
        # 根据弱点给出建议
        weaknesses = performance.get('weaknesses', [])
        if weaknesses:
            tips.append(f"注意{weaknesses[0]['type']}类题目，仔细审题")
        
        return tips
    
    def _generate_stress_management(self) -> Dict[str, Any]:
        """压力管理建议"""
        return {
            'before_exam': [
                '提前熟悉考场环境',
                '保证充足睡眠',
                '准备必备文具'
            ],
            'during_exam': [
                '深呼吸放松',
                '遇到难题先跳过',
                '保持平稳节奏'
            ],
            'time_trouble': '如果时间紧张，先完成有把握的题目'
        }


class StudentLearningOptimizer:
    """学生学习优化器主类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.db_path = db_path
        
        # 初始化组件
        self.performance_analyzer = StudentPerformanceAnalyzer()
        self.gap_identifier = KnowledgeGapIdentifier()
        self.path_optimizer = LearningPathOptimizer()
        self.exam_advisor = ExamStrategyAdvisor()
        
        self.initialized_at = datetime.now().isoformat()
        
        logger.info("学生学习优化器初始化完成")
    
    def analyze_student(self, user_id: int, exam_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """全面分析学生"""
        # 1. 分析学习表现
        performance = self.performance_analyzer.analyze_performance(exam_history)
        
        # 2. 收集题目分析数据
        question_analysis = self._get_question_analysis(user_id)
        
        # 3. 识别知识漏洞
        gaps = self.gap_identifier.identify_gaps(question_analysis)
        
        # 4. 生成学习路径
        learning_path = self.path_optimizer.generate_learning_path(gaps, performance)
        
        return {
            'user_id': user_id,
            'performance': performance,
            'knowledge_gaps': gaps,
            'learning_path': learning_path,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def generate_exam_strategy(self, user_id: int, exam_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成考试策略"""
        # 获取历史表现
        exam_history = self._get_exam_history(user_id)
        performance = self.performance_analyzer.analyze_performance(exam_history)
        
        # 生成策略
        return self.exam_advisor.generate_exam_strategy(performance, exam_config)
    
    def get_progress_tracking(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取进步追踪"""
        exam_history = self._get_exam_history(user_id, days=days)
        performance = self.performance_analyzer.analyze_performance(exam_history)
        
        # 计算改进指标
        improvements = []
        
        if len(exam_history) >= 2:
            first_half = exam_history[:len(exam_history)//2]
            second_half = exam_history[len(exam_history)//2:]
            
            first_avg = sum(e.get('score', 0) for e in first_half) / len(first_half)
            second_avg = sum(e.get('score', 0) for e in second_half) / len(second_half)
            
            improvement = second_avg - first_avg
            improvements.append({
                'metric': 'overall_score',
                'before': round(first_avg, 2),
                'after': round(second_avg, 2),
                'change': round(improvement, 2),
                'positive': improvement > 0
            })
        
        return {
            'user_id': user_id,
            'period_days': days,
            'exam_count': len(exam_history),
            'performance': performance,
            'improvements': improvements,
            'tracked_at': datetime.now().isoformat()
        }
    
    def _get_exam_history(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """获取考试历史"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                cursor.execute("""
                    SELECT * FROM exam_results 
                    WHERE user_id = ? AND created_at >= ?
                    ORDER BY created_at DESC
                """, (user_id, cutoff_date))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取考试历史失败: {e}")
            return []
    
    def _get_question_analysis(self, user_id: int) -> List[Dict[str, Any]]:
        """获取题目分析数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM question_analysis 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT 100
                """, (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取题目分析失败: {e}")
            return []
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()


# 创建全局实例
student_learning_optimizer = StudentLearningOptimizer()
