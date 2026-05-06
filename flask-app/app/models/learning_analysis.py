#!/usr/bin/env python3
"""
学习分析模型，用于分析学生的学习方向和兴趣

# JSON import removed - using database
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption
from app.ai.teacher_ai import teacher_ai_map

class LearningAnalysisManager:
    """学习分析管理器"""

    def __init__(self):
        """初始化学习分析管理器"""
        self._create_tables()

    def _create_tables(self):
        """创建必要的表"""
        try:
            # 获取加密后的表名
            learning_analyses_table = table_encryption.encrypt_table_name('learning_analyses')
            learning_interests_table = table_encryption.encrypt_table_name('learning_interests')
            learning_directions_table = table_encryption.encrypt_table_name('learning_directions')
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')
            user_table = table_encryption.encrypt_table_name('user')

            # 创建学习分析表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {learning_analyses_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            # 创建学习兴趣表
            db_manager.execute(f'''
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    interest_level INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            db_manager.execute(f'''
                    user_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')

            # 创建学习活动表
            db_manager.execute(f'''
                    user_id INTEGER NOT NULL,
                    activity_data TEXT NOT NULL,
                )


        except Exception as e:
            logger.error(f"创建学习分析表结构失败: {str(e)}")

    def analyze_learning_interest(self, user_id: int) -> Dict[str, Any]:
        分析学习兴趣
        Args:
            user_id: 用户ID

            兴趣分析结果
        try:

            activities = db_manager.fetch_all(
            )

            # 分析活动数据
            interest_scores = self._analyze_activities(activities)

            # 获取历史兴趣数据
            history_interests = db_manager.fetch_all(
                f'SELECT subject, interest_level FROM {learning_interests_table} WHERE user_id = ?',
                (user_id,)
            )

            # 合并历史数据和新分析数据
            for interest in history_interests:
                subject = interest['subject'] if isinstance(interest, dict) else interest[0]
                level = interest['interest_level'] if isinstance(interest, dict) else interest[1]
                if subject not in interest_scores:
                    interest_scores[subject] = level

            # 计算综合兴趣
            comprehensive_interest = self._calculate_comprehensive_interest(interest_scores)
            # 生成兴趣分析报告
            analysis = {
                "user_id": user_id,
                "analysis_type": "interest",
                "interest_scores": interest_scores,
                "comprehensive_interest": comprehensive_interest,
                "recommended_subjects": self._get_recommended_subjects(interest_scores),
                "generated_at": datetime.now().isoformat()

            # 保存分析结果
            self._save_analysis(user_id, "interest", analysis)

            # 更新学习兴趣表
            for subject, level in interest_scores.items():
                self._update_learning_interest(user_id, subject, level)

            return analysis
        except Exception as e:
            logger.error(f"分析学习兴趣失败: {str(e)}")
            return {}

    def analyze_learning_direction(self, user_id: int) -> Dict[str, Any]:
        分析学习方向

        Args:
            user_id: 用户ID

        Returns:
            方向分析结果
        try:
            # 获取用户的错题统计
            from app.models.error_question import error_question_manager
            error_stats = error_question_manager.get_error_question_statistics(user_id)

            from app.models.enhanced_exam import enhanced_exam_system
            exam_records = enhanced_exam_system.get_user_exam_records(user_id)

            # 分析学习方向
            directions = self._identify_learning_directions(error_stats, exam_records)

            # 生成方向分析报告
            analysis = {
                "user_id": user_id,
                "analysis_type": "direction",
                "directions": directions,
                "priority_areas": self._identify_priority_areas(directions),
                "action_plan": self._generate_action_plan(directions),
            }

            # 保存分析结果
            self._save_analysis(user_id, "direction", analysis)

            # 更新学习方向表
            for direction in directions:
                self._update_learning_direction(user_id, direction["direction"], direction["priority"])

            logger.info(f"分析学习方向成功: {user_id}")
            return analysis
        except Exception as e:
            logger.error(f"分析学习方向失败: {str(e)}")
            return {}

    def analyze_learning_progress(self, user_id: int) -> Dict[str, Any]:
        分析学习进度

        Args:
            user_id: 用户ID

        Returns:
            进度分析结果
        try:
            # 获取用户的考试记录
            from app.models.enhanced_exam import enhanced_exam_system
            exam_records = enhanced_exam_system.get_user_exam_records(user_id)

            progress = self._analyze_progress(exam_records)
            analysis = {
                "user_id": user_id,
                "analysis_type": "progress",
                "progress": progress,
                "trends": self._analyze_trends(exam_records),
                "generated_at": datetime.now().isoformat()
            }

            self._save_analysis(user_id, "progress", analysis)

            logger.info(f"分析学习进度成功: {user_id}")
        except Exception as e:
            logger.error(f"分析学习进度失败: {str(e)}")
            return {}

    def analyze_strengths_weaknesses(self, user_id: int) -> Dict[str, Any]:

        Args:
            user_id: 用户ID
        Returns:
            优势劣势分析结果
        try:
            # 获取用户的错题统计
            from app.models.error_question import error_question_manager
            error_stats = error_question_manager.get_error_question_statistics(user_id)

            # 获取用户的考试记录
            from app.models.enhanced_exam import enhanced_exam_system
            exam_records = enhanced_exam_system.get_user_exam_records(user_id)

            strengths, weaknesses = self._identify_strengths_weaknesses(error_stats, exam_records)

            analysis = {
                "strengths": strengths,
                "generated_at": datetime.now().isoformat()
            }

            # 保存分析结果
            self._save_analysis(user_id, "strength_weakness", analysis)
            return analysis
        except Exception as e:
            logger.error(f"分析学习优势和劣势失败: {str(e)}")
            return {}
    def add_learning_activity(self, user_id: int, activity_type: str, activity_data: Dict[str, Any], duration: int = None) -> int:
        添加学习活动

        Args:
            user_id: 用户ID
            activity_data: 活动数据
            duration: 持续时间（秒）

        Returns:
        try:
            # 获取加密后的表名
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')

            activity_data_json = str(activity_data)

            db_manager.execute(
                f'''
                INSERT INTO {learning_activities_table} (user_id, activity_type, activity_data, duration)
                VALUES (?, ?, ?, ?)
                ''',
            )

            result = db_manager.fetch_one('SELECT last_insert_rowid()')
                return activity_id
            return -1
    def get_user_learning_analyses(self, user_id: int) -> List[Dict[str, Any]]:
        获取用户的学习分析记录
            user_id: 用户ID

        try:
            # 获取加密后的表名

                f'SELECT * FROM {learning_analyses_table} WHERE user_id = ? ORDER BY generated_at DESC',
                (user_id,)
            )

            result = []
            for analysis in analyses:
                    'id': analysis['id'] if isinstance(analysis, dict) else analysis[0],
                    'analysis_type': analysis['analysis_type'] if isinstance(analysis, dict) else analysis[2],
                    'generated_at': analysis['generated_at'] if isinstance(analysis, dict) else analysis[4],
                    'updated_at': analysis['updated_at'] if isinstance(analysis, dict) else analysis[5]
                }
            return result
        except Exception as e:
            logger.error(f"获取用户学习分析记录失败: {str(e)}")

    def generate_comprehensive_report(self, user_id: int) -> Dict[str, Any]:
        生成综合学习报告

        Args:
            user_id: 用户ID

        Returns:
            综合报告
        try:
            # 分析学习兴趣

            # 分析学习方向
            direction_analysis = self.analyze_learning_direction(user_id)

            # 分析学习进度
            progress_analysis = self.analyze_learning_progress(user_id)

            # 分析优势和劣势
            strength_weakness_analysis = self.analyze_strengths_weaknesses(user_id)
            # 生成学习风格分析
            learning_style_analysis = self._analyze_learning_style(user_id)
            # 生成学习目标建议
            learning_goals = self._generate_learning_goals(
                interest_analysis, direction_analysis, progress_analysis, strength_weakness_analysis
            )

            # 生成学习计划
            learning_plan = self._generate_personalized_learning_plan(
                user_id, interest_analysis, direction_analysis, progress_analysis
            )

            # 生成综合报告
            report = {
                "user_id": user_id,
                "interest_analysis": interest_analysis,
                "direction_analysis": direction_analysis,
                "progress_analysis": progress_analysis,
                "strength_weakness_analysis": strength_weakness_analysis,
                "learning_style_analysis": learning_style_analysis,
                "learning_goals": learning_goals,
                "learning_plan": learning_plan,
                "recommendations": self._generate_comprehensive_recommendations(
                    interest_analysis, direction_analysis, progress_analysis, strength_weakness_analysis
                ),
                ),
                "generated_at": datetime.now().isoformat(),
                "report_id": f"report_{user_id}_{int(datetime.now().timestamp())}"
            }

            logger.info(f"生成综合学习报告成功: {user_id}")
            return report
        except Exception as e:
            logger.error(f"生成综合学习报告失败: {str(e)}")
            return {}

    def _analyze_activities(self, activities: List[Any]) -> Dict[str, int]:
        分析学习活动

        Args:
            activities: 活动列表

        Returns:
            兴趣分数
        activity_weights = {
            'exam': 0.4,        # 考试权重最高
            'practice': 0.3,     # 练习次之
            'resource_view': 0.2, # 资源查看
        }

        for activity in activities:
            activity_type = activity['activity_type'] if isinstance(activity, dict) else activity[2]
            activity_data = eval(activity['activity_data']) if (isinstance(activity, dict) and activity['activity_data']) else (eval(activity[3]) if activity[3] else {})
            duration = activity['duration'] if isinstance(activity, dict) else activity[4]

            # 根据活动类型和数据分析兴趣
            if activity_type == 'exam':
                subject = activity_data.get('subject', 'general')
                score = activity_data.get('score', 0)
                # 分数越高，兴趣越高
                interest_level = min(5, max(1, int(score / 20) + 1))
                weight = activity_weights.get(activity_type, 0.1)
                current_score = interest_scores.get(subject, 0)
                interest_scores[subject] = max(current_score, interest_level * weight)
            elif activity_type == 'practice':
                subject = activity_data.get('subject', 'general')
                completion_rate = activity_data.get('completion_rate', 0)
                accuracy = activity_data.get('accuracy', 0)
                # 完成率和准确率综合计算
                interest_level = min(5, max(1, int((completion_rate * 0.6 + accuracy * 0.4) * 5) + 1))
                weight = activity_weights.get(activity_type, 0.1)
                current_score = interest_scores.get(subject, 0)
                interest_scores[subject] = max(current_score, interest_level * weight)
            elif activity_type == 'resource_view':
                subject = activity_data.get('subject', 'general')
                duration = activity_data.get('duration', duration or 0)
                interest_level = min(5, max(1, int((min(duration / 300, 1) * 0.7 + min(interaction_count / 10, 1) * 0.3) * 5) + 1))
                weight = activity_weights.get(activity_type, 0.1)
                current_score = interest_scores.get(subject, 0)
            elif activity_type == 'review':
                subject = activity_data.get('subject', 'general')
                review_efficiency = activity_data.get('review_efficiency', 0)
                weight = activity_weights.get(activity_type, 0.1)
                current_score = interest_scores.get(subject, 0)
                interest_scores[subject] = max(current_score, interest_level * weight)

        # 归一化兴趣分数到1-5分
        for subject in interest_scores:
            interest_scores[subject] = min(5, max(1, round(interest_scores[subject] / sum(activity_weights.values()) * 5)))

        return interest_scores

    def _calculate_comprehensive_interest(self, interest_scores: Dict[str, int]) -> Dict[str, Any]:
        计算综合兴趣

        Args:
            interest_scores: 兴趣分数

        Returns:
            综合兴趣
        if not interest_scores:
            return {
                "overall_level": 2,
                "top_subjects": [],
                "suggested_exploration": ["数学", "英语", "物理"]
            }

        # 计算平均兴趣水平

        # 找出最感兴趣的科目
        top_subjects = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:3]

        # 建议探索的科目
        suggested_exploration = []
        all_subjects = ["数学", "英语", "物理", "化学", "生物"]
            if subject not in interest_scores or interest_scores[subject] < 3:
                suggested_exploration.append(subject)

        return {
            "overall_level": min(5, max(1, int(avg_level))),
            "top_subjects": top_subjects,
            "suggested_exploration": suggested_exploration[:3]
        }

    def _get_recommended_subjects(self, interest_scores: Dict[str, int]) -> List[str]:
        获取推荐科目

        Args:
            interest_scores: 兴趣分数

        Returns:
            推荐科目列表
        # 推荐兴趣分数高的科目
        recommended = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return [subject for subject, _ in recommended]

    def _identify_learning_directions(self, error_stats: Dict[str, Any], exam_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        识别学习方向

        Args:
            error_stats: 错题统计
            exam_records: 考试记录

        Returns:
            学习方向列表
        directions = []

        # 根据错题类型分析方向
        error_types = error_stats.get('error_types', {})
        total_errors = error_stats.get('total_count', 1)
        # 确保total_errors是数值类型
        if isinstance(total_errors, (int, float)):
            for error_type, count in error_types.items():
                if count > 0:
                    # 计算错误率
                    error_rate = count / total_errors

                    # 根据错误率确定优先级
                    if error_rate > 0.4:
                    elif error_rate > 0.2:
                        priority = 2  # 中等优先级
                    else:
                        priority = 3  # 低优先级

                        "direction": f"减少{error_type}类型的错误",
                        "error_rate": error_rate

        # 根据知识点分析方向
        knowledge_points = error_stats.get('knowledge_points', {})
        if isinstance(total_errors, (int, float)):
                if count > 3:  # 知识点错误次数较多

                        priority = 1
                    elif error_rate > 0.15:
                    else:

                    directions.append({
                        "direction": f"加强{point}知识点的学习",
                        "reason": f"该知识点错误出现了{count}次，错误率为{error_rate:.2f}",
                        "error_rate": error_rate
                    })
        # 根据考试成绩分析方向
        if exam_records:
            recent_scores = [record['score'] for record in exam_records[:5]]
            avg_score = sum(recent_scores) / len(recent_scores)

            # 分析成绩趋势
            if len(recent_scores) >= 3:
                trend = "stable"
                if recent_scores[-1] > recent_scores[0] + 5:
                    trend = "improving"
                elif recent_scores[-1] < recent_scores[0] - 5:
                    trend = "declining"
            else:
                trend = "insufficient_data"

            if avg_score < 60:
                directions.append({
                    "direction": "加强基础知识学习",
                    "priority": 1,
                    "reason": f"最近考试平均成绩为{avg_score:.1f}，需要加强基础知识",
                    "trend": trend
                })
            elif avg_score < 80:
                directions.append({
                    "direction": "提高解题能力和技巧",
                    "priority": 2,
                    "reason": f"最近考试平均成绩为{avg_score:.1f}，需要提高解题能力",
                    "trend": trend
                })
            else:
                directions.append({
                    "direction": "挑战更高难度的题目",
                    "priority": 3,
                    "reason": f"最近考试平均成绩为{avg_score:.1f}，可以挑战更高难度",
                    "trend": trend
                })

        # 按优先级排序
        directions.sort(key=lambda x: x['priority'])

        return directions

    def _identify_priority_areas(self, directions: List[Dict[str, Any]]) -> List[str]:
        识别优先领域

        Args:
            directions: 学习方向列表

        Returns:
            优先领域列表
        # 按优先级排序，取前3个
        priority_directions = sorted(directions, key=lambda x: x["priority"], reverse=True)[:3]

    def _generate_action_plan(self, directions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        生成行动计划

        Args:
            directions: 学习方向列表

        Returns:
            行动计划列表
        action_plan = []

        for direction in directions:
            action = {
                "direction": direction["direction"],
                "priority": direction["priority"],
                "actions": self._generate_specific_actions(direction["direction"]),
                "timeline": "1-2 weeks"
            }
            action_plan.append(action)

        return action_plan

    def _generate_specific_actions(self, direction: str) -> List[str]:
        生成具体行动

        Args:
            direction: 学习方向

        Returns:
            具体行动列表
        actions_map = {
            "减少概念理解错误类型的错误": [
                "复习相关概念的定义和原理",
                "做针对性的概念理解练习题",
                "向老师或同学请教不懂的概念"
            ],
            "减少计算错误类型的错误": [
                "加强计算练习，提高计算准确性",
                "养成检查计算过程的习惯",
                "学习计算技巧和方法"
            ],
            "加强基础知识学习": [
                "制定基础知识学习计划",
                "每天复习一个基础知识点",
                "做基础练习题巩固知识"
            ],
            "提高解题能力和技巧": [
                "学习解题方法和技巧",
                "做更多的练习题",
            ],
            "挑战更高难度的题目": [
                "尝试解决高难度题目",
                "学习更深入的知识点"
            ]
        }

        return actions_map.get(direction, ["制定具体的学习计划", "按计划执行", "定期检查进度"])

    def _analyze_progress(self, exam_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        分析学习进度

            exam_records: 考试记录

            进度分析
        if not exam_records:
                "total_exams": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "improvement_rate": 0,
                "consistency": 0,
                "subject_breakdown": {},
                "skill_improvement": {}
            }

        scores = [record['score'] for record in exam_records]
        total_exams = len(scores)
        average_score = sum(scores) / total_exams
        highest_score = max(scores)
        lowest_score = min(scores)

        if total_exams >= 2:
            first_score = scores[-1]
            last_score = scores[0]
            improvement_rate = (last_score - first_score) / first_score * 100 if first_score > 0 else 0
        else:
            improvement_rate = 0
        # 计算成绩一致性（标准差的倒数）
        if total_exams >= 2:
            import statistics
            try:
                std_dev = statistics.stdev(scores)
                consistency = 100 / (std_dev + 1)  # 标准化到0-100
                consistency = 0
        else:

        # 按科目分析成绩
        subject_breakdown = {}
        for record in exam_records:
            subject = record.get('subject', 'general')
            score = record.get('score', 0)
                subject_breakdown[subject] = []
            subject_breakdown[subject].append(score)

        # 计算各科目统计
        for subject, sub_scores in subject_breakdown.items():
            subject_breakdown[subject] = {
                "average": sum(sub_scores) / len(sub_scores),
                "lowest": min(sub_scores),
                "count": len(sub_scores)
            }

        # 技能改进分析
        skill_improvement = {}
        # 这里可以根据具体的技能类型进行分析
        # 简化实现，实际应基于题目类型或知识点分析
        skill_improvement["problem_solving"] = {
            "level": "intermediate"
        }
        skill_improvement["time_management"] = {
            "improvement_rate": improvement_rate * 0.6,
            "level": "beginner"
        }

        return {
            "total_exams": total_exams,
            "average_score": average_score,
            "highest_score": highest_score,
            "lowest_score": lowest_score,
            "consistency": consistency,
            "subject_breakdown": subject_breakdown,
            "skill_improvement": skill_improvement
        }

    def _analyze_trends(self, exam_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        分析学习趋势

        Args:
            exam_records: 考试记录

        Returns:
            趋势分析
        if not exam_records:
            return []

        trends = []

        # 按时间顺序分析分数趋势
        scores = [record['score'] for record in reversed(exam_records)]

        if len(scores) >= 3:
            # 最近三次考试的趋势
            recent_scores = scores[-3:]
            if recent_scores[-1] > recent_scores[0]:
                trend = "improving"
                message = "成绩呈上升趋势"
            elif recent_scores[-1] < recent_scores[0]:
                trend = "declining"
                message = "成绩呈下降趋势"
            else:
                message = "成绩保持稳定"

            trends.append({
                "period": "recent",
                "trend": trend,
                "message": message,
                "scores": recent_scores
            })

        return trends

    def _identify_milestones(self, exam_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        识别学习里程碑

        Args:
            exam_records: 考试记录

        Returns:
            里程碑列表
        if not exam_records:
            return []
        milestones = []

        # 找出最高分的考试
        highest_record = max(exam_records, key=lambda x: x['score'])
        milestones.append({
            "type": "highest_score",
            "exam_name": highest_record['exam_name'],
            "score": highest_record['score'],
            "date": highest_record['created_at'],
            "description": "最高分数记录"
        })

        # 找出进步最大的考试
        if len(exam_records) >= 2:
            max_improvement = 0
            improvement_record = None

            for i in range(1, len(exam_records)):
                improvement = exam_records[i-1]['score'] - exam_records[i]['score']
                if improvement > max_improvement:
                    max_improvement = improvement
                    improvement_record = exam_records[i-1]

            if improvement_record:
                milestones.append({
                    "type": "max_improvement",
                    "exam_name": improvement_record['exam_name'],
                    "score": improvement_record['score'],
                    "improvement": max_improvement,
                    "date": improvement_record['created_at'],
                    "description": "最大进步记录"
                })

        return milestones

    def _identify_strengths_weaknesses(self, error_stats: Dict[str, Any], exam_records: List[Dict[str, Any]]) -> (List[str], List[str]):
        识别优势和劣势

        Args:
            error_stats: 错题统计
            exam_records: 考试记录

        Returns:
        strengths = []
        weaknesses = []

        # 根据错题类型分析劣势
        error_types = error_stats.get('error_types', {})
        for error_type, count in error_types.items():
            if count > 5:
                weaknesses.append(f"{error_type}错误较多")
        # 根据考试成绩分析优势
        if exam_records:
            recent_scores = [record['score'] for record in exam_records[:5]]
            avg_score = sum(recent_scores) / len(recent_scores)

            if avg_score >= 80:
                strengths.append("整体成绩优秀")
            elif avg_score >= 60:
                strengths.append("基础掌握良好")

            # 分析各科目表现
            # 这里简化处理，实际应该根据具体科目成绩分析
            strengths.append("学习态度认真")

        # 默认优势和劣势
        if not strengths:
            strengths.append("有学习潜力")
        if not weaknesses:
            weaknesses.append("需要进一步提高")

        return strengths, weaknesses

    def _generate_improvement_suggestions(self, strengths: List[str], weaknesses: List[str]) -> List[str]:
        生成改进建议

        Args:
            weaknesses: 劣势列表

        Returns:
            改进建议列表
        suggestions = []

        # 根据优势生成建议
        for strength in strengths:
            if "优秀" in strength:
            elif "良好" in strength:
                suggestions.append("巩固基础，争取更上一层楼")
            elif "潜力" in strength:
                suggestions.append("制定合理的学习计划，充分发挥学习潜力")

        # 根据劣势生成建议
        for weakness in weaknesses:
            if "错误较多" in weakness:
                suggestions.append("分析错误原因，针对性地进行练习")
            elif "提高" in weakness:
                suggestions.append("制定具体的学习计划，有步骤地提高")

        # 通用建议
        suggestions.append("定期复习，巩固所学知识")
        suggestions.append("多做练习题，提高解题能力")
        suggestions.append("保持良好的学习习惯和态度")


    def _generate_comprehensive_recommendations(self, interest_analysis: Dict[str, Any],
                                             direction_analysis: Dict[str, Any],
                                             progress_analysis: Dict[str, Any],
                                             strength_weakness_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        生成综合建议

        Args:
            direction_analysis: 方向分析
            progress_analysis: 进度分析

            综合建议列表

        # 根据兴趣分析生成建议
        if interest_analysis:
            top_subjects = interest_analysis.get('comprehensive_interest', {}).get('top_subjects', [])
            if top_subjects:
                recommendations.append({
                    "title": "基于兴趣的学习建议",
                    "content": f"你对{', '.join(top_subjects)}等科目很感兴趣，可以深入学习这些科目，参加相关的竞赛或活动"
                })

        # 根据方向分析生成建议
        if direction_analysis:
            priority_areas = direction_analysis.get('priority_areas', [])
            if priority_areas:
                recommendations.append({
                    "type": "direction_based",
                    "title": "基于学习方向的建议",
                    "content": f"优先关注{', '.join(priority_areas)}等方面，制定具体的学习计划"
                })

        # 根据进度分析生成建议
        if progress_analysis:
            improvement_rate = progress_analysis.get('progress', {}).get('improvement_rate', 0)
            if improvement_rate > 10:
                recommendations.append({
                    "type": "progress_based",
                    "title": "基于学习进度的建议",
                })
            elif improvement_rate < -10:
                recommendations.append({
                    "type": "progress_based",
                    "title": "基于学习进度的建议",
                    "content": "你的学习成绩有所下降，需要调整学习方法，找出问题所在"
                })

        # 根据优势劣势分析生成建议
        if strength_weakness_analysis:
            strengths = strength_weakness_analysis.get('strengths', [])
            weaknesses = strength_weakness_analysis.get('weaknesses', [])
            if strengths and weaknesses:
                recommendations.append({
                    "type": "strength_weakness_based",
                    "title": "基于优势劣势的建议",
                    "content": f"发挥{', '.join(strengths)}等优势，改进{', '.join(weaknesses)}等劣势"
                })

        # 通用建议
        recommendations.append({
            "type": "general",
            "title": "通用学习建议",
            "content": "保持良好的学习习惯，定期复习，多做练习，积极参加课外活动，培养学习兴趣"
        })
        return recommendations
    def _save_analysis(self, user_id: int, analysis_type: str, analysis_data: Dict[str, Any]):
        保存分析结果

        Args:
            analysis_type: 分析类型
            analysis_data: 分析数据
        try:
            # 获取加密后的表名
            learning_analyses_table = table_encryption.encrypt_table_name('learning_analyses')

            analysis_data_json = str(analysis_data)
            db_manager.execute(
                f'''
                VALUES (?, ?, ?)
                ''',
                (user_id, analysis_type, analysis_data_json)
            )
        except Exception as e:
            logger.error(f"保存分析结果失败: {str(e)}")

    def _update_learning_interest(self, user_id: int, subject: str, interest_level: int):
        更新学习兴趣

        Args:
            user_id: 用户ID
            interest_level: 兴趣水平
            # 获取加密后的表名

            # 检查是否已存在
            existing = db_manager.fetch_one(
                f'SELECT id FROM {learning_interests_table} WHERE user_id = ? AND subject = ?',
                (user_id, subject)
            )

            if existing:
                # 更新
                db_manager.execute(
                    f'''
                    UPDATE {learning_interests_table}
                    SET interest_level = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND subject = ?
                    ''',
                    (interest_level, user_id, subject)
                )
                # 插入
                db_manager.execute(
                    f'''
                    INSERT INTO {learning_interests_table} (user_id, subject, interest_level)
                    VALUES (?, ?, ?)
                    ''',
                    (user_id, subject, interest_level)
                )
        except Exception as e:

    def _update_learning_direction(self, user_id: int, direction: str, priority: int):
        更新学习方向

            user_id: 用户ID
            direction: 方向
            priority: 优先级
        try:
            # 获取加密后的表名
            learning_directions_table = table_encryption.encrypt_table_name('learning_directions')

            # 检查是否已存在
            existing = db_manager.fetch_one(
                (user_id, direction)
            )

            if existing:
                # 更新
                db_manager.execute(
                    f'''
                    UPDATE {learning_directions_table}
                    SET priority = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND direction = ?
                    (priority, user_id, direction)
                )
            else:
                # 插入
                db_manager.execute(
                    f'''
                    INSERT INTO {learning_directions_table} (user_id, direction, priority)
                    ''',
                )
        except Exception as e:
            logger.error(f"更新学习方向失败: {str(e)}")

    def _analyze_learning_style(self, user_id: int) -> Dict[str, Any]:
        分析学习风格

        Args:
            user_id: 用户ID

        Returns:
            学习风格分析
        try:
            # 获取加密后的表名
            learning_activities_table = table_encryption.encrypt_table_name('learning_activities')
            # 获取用户学习活动
            activities = db_manager.fetch_all(
                f'SELECT activity_type, duration FROM {learning_activities_table} WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
            )
            # 分析学习风格
            style_scores = {
                "visual": 0,
                "auditory": 0,
                "kinesthetic": 0,
                "reading/writing": 0
            }

            for activity in activities:
                duration = activity['duration'] if isinstance(activity, dict) else activity[1]
                # 根据活动类型分析学习风格
                if activity_type == 'resource_view':
                    style_scores["visual"] += duration or 1
                elif activity_type == 'review':
                    style_scores["reading/writing"] += duration or 1
                elif activity_type == 'practice':
                    style_scores["kinesthetic"] += duration or 1
                elif activity_type == 'exam':
            # 确定主导学习风格
            dominant_style = max(style_scores, key=style_scores.get)

            # 学习风格描述
                "visual": "你倾向于通过视觉方式学习，如图表、图片和视频",
                "auditory": "你倾向于通过听觉方式学习，如听讲、讨论和音频材料",
                "kinesthetic": "你倾向于通过动手实践学习，如实验、操作和角色扮演",
                "reading/writing": "你倾向于通过阅读和写作学习，如笔记、文章和书籍"
            }

            return {
                "dominant_style": dominant_style,
                "style_scores": style_scores,
            logger.error(f"分析学习风格失败: {str(e)}")
                "dominant_style": "mixed",
                "description": "无法确定学习风格",
            }

        根据学习风格获取学习建议

        Args:
        Returns:
            "visual": [
                "使用图表和思维导图来组织信息",
                "观看相关视频教程",
                "使用彩色笔记和标记",
            ],
            "auditory": [
                "大声朗读学习材料",
                "与同学讨论学习内容"
            ],
                "通过实验和实践学习",
                "在学习时保持活跃",
                "使用实物模型和道具"
            "reading/writing": [
                "多做笔记和摘要",
                "写学习日记",
                "通过写作来巩固知识"
            ],
            "mixed": [
                "结合多种学习方式",
                "保持学习的多样性"
            ]
        return tips_map.get(style, tips_map["mixed"])
    def _generate_learning_goals(self, interest_analysis: Dict[str, Any],
                                direction_analysis: Dict[str, Any],
                                progress_analysis: Dict[str, Any],
                                strength_weakness_analysis: Dict[str, Any]) -> Dict[str, Any]:
        生成学习目标
        Args:
            interest_analysis: 兴趣分析
            direction_analysis: 方向分析
            progress_analysis: 进度分析
            strength_weakness_analysis: 优势劣势分析

        Returns:
            学习目标
        goals = {
            "short_term": [],  # 短期目标（1-4周）
            "medium_term": [],  # 中期目标（1-3个月）
            "long_term": []     # 长期目标（3-6个月）
        }

        # 基于兴趣分析生成目标
        if interest_analysis:
            top_subjects = interest_analysis.get('comprehensive_interest', {}).get('top_subjects', [])
            for subject in top_subjects:
                goals["short_term"].append(f"深入学习{subject}的核心知识点")

            priority_areas = direction_analysis.get('priority_areas', [])
            for area in priority_areas[:2]:
                goals["short_term"].append(f"解决{area}的问题")
                goals["medium_term"].append(f"在{area}方面取得明显改善")
        # 基于进度分析生成目标
        if progress_analysis:
            improvement_rate = progress_analysis.get('progress', {}).get('improvement_rate', 0)
            if improvement_rate < 0:
            elif improvement_rate < 10:
                goals["medium_term"].append("提高学习进步率")
            else:

        if strength_weakness_analysis:
            strengths = strength_weakness_analysis.get('strengths', [])
            weaknesses = strength_weakness_analysis.get('weaknesses', [])

            for strength in strengths[:2]:
                goals["medium_term"].append(f"进一步发挥{strength}的优势")

                goals["short_term"].append(f"改善{weakness}的不足")

        return goals

    def _generate_personalized_learning_plan(self, user_id: int,
                                           interest_analysis: Dict[str, Any],
                                           progress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        生成个性化学习计划

        Args:
            user_id: 用户ID
            interest_analysis: 兴趣分析
            direction_analysis: 方向分析
            progress_analysis: 进度分析

        Returns:
            学习计划
        weekly_plan = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": []
        }

        # 基于兴趣和方向安排学习内容
        if interest_analysis:
            top_subjects = interest_analysis.get('comprehensive_interest', {}).get('top_subjects', [])
            for i, subject in enumerate(top_subjects):
                day = list(weekly_plan.keys())[i % 7]
                weekly_plan[day].append(f"学习{subject}知识点")

        if direction_analysis:
            priority_areas = direction_analysis.get('priority_areas', [])
            for i, area in enumerate(priority_areas):
                weekly_plan[day].append(f"专注于{area}")
        # 每天安排复习时间
        for day in weekly_plan:

        # 生成学习资源推荐
        resources = {
            "books": [],
        }

        # 生成学习策略
        strategies = [
            "制定每日学习计划",
            "定期复习错题",
            "使用适合自己的学习方法",
            "保持良好的学习习惯",
            "定期评估学习效果"

            "weekly_plan": weekly_plan,
            "strategies": strategies,
                "daily_study_time": "2-3小时",
                "focus_time": "25分钟",
                "break_time": "5分钟"
            }
        }

    def _generate_next_steps(self, direction_analysis: Dict[str, Any],
                           learning_goals: Dict[str, Any],
                           learning_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        生成下一步行动建议

        Args:
            direction_analysis: 方向分析
            learning_goals: 学习目标
            learning_plan: 学习计划

        Returns:
            下一步行动建议
        next_steps = []

        # 基于优先级领域的下一步行动
        if direction_analysis:
            priority_areas = direction_analysis.get('priority_areas', [])
            for i, area in enumerate(priority_areas[:3]):
                next_steps.append({
                    "step": i + 1,
                    "action": f"开始着手解决{area}的问题",
                    "timeframe": "1周内",
                    "priority": "high"
                })

        # 基于短期目标的下一步行动
        if learning_goals:
            short_term_goals = learning_goals.get('short_term', [])
            for i, goal in enumerate(short_term_goals[:2]):
                next_steps.append({
                    "step": len(next_steps) + 1,
                    "action": f"开始实施{goal}",
                    "timeframe": "2周内",
                    "priority": "medium"
                })

        # 基于学习计划的下一步行动
        next_steps.append({
            "step": len(next_steps) + 1,
            "action": "开始执行个性化学习计划",
            "timeframe": "立即",
            "priority": "high"
        })
        # 定期评估的下一步行动
        next_steps.append({
            "step": len(next_steps) + 1,
            "action": "每周评估学习进度和效果",
            "timeframe": "每周日",
            "priority": "medium"
        })

        return next_steps

# 创建全局学习分析管理器实例
learning_analysis_manager = LearningAnalysisManager()
