#!/usr/bin/env python3
"""
考试管理服务模块
负责考试系统的管理和优化，集成本地AI自动填充功能

import os
import sys
import sqlite3
# JSON import removed - using database
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入考试系统AI
from app.ai.exam_ai import exam_ai
# 导入考试规则管理器
from app.utils.exam_rule_manager import exam_rule_manager
# 导入考试权限管理器
from app.utils.exam_permission_manager import exam_permission_manager

class ExamService:
    """考试管理服务类"""

    def __init__(self, db_path="app.db"):
        """初始化考试管理服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        # 自动填充配置
        self.auto_fill_config = {
            "enabled": True,
            "fields": ["answer", "essay", "short_answer"],
            "context_aware": True,
            "learning_rate": 0.1
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def save_exam_auto_fill(self, user_id, exam_id, question_id, field_name, field_value, context=None):
        """保存考试自动填充数据"""
        if not self.connect():
            return False

        try:
            sql = """
            SELECT id, usage_count FROM exam_auto_fill
            WHERE user_id = ? AND exam_id = ? AND question_id = ? AND field_name = ? AND field_value = ?
            self.cursor.execute(sql, (user_id, exam_id, question_id, field_name, field_value))
            existing = self.cursor.fetchone()

            if existing:
                # 更新使用次数
                sql = """
                UPDATE exam_auto_fill
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                self.cursor.execute(sql, (existing[0],))
            else:
                # 插入新数据
                sql = """
                INSERT INTO exam_auto_fill (user_id, exam_id, question_id, field_name, field_value, context, usage_count, last_used)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                self.cursor.execute(sql, (user_id, exam_id, question_id, field_name, field_value, str(context) if context else None))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存考试自动填充数据失败: {str(e)}")
            return False
        finally:

    def get_exam_auto_fill(self, user_id, exam_id=None, question_id=None, field_name=None):
        """获取考试自动填充数据"""
        if not self.connect():
            return []

        try:
            # 构建查询
            conditions = ["user_id = ?"]
            if exam_id:
                conditions.append("exam_id = ?")
                params.append(exam_id)

            if question_id:
                conditions.append("question_id = ?")
                params.append(question_id)

            if field_name:
                conditions.append("field_name = ?")
                params.append(field_name)

            where_clause = " AND ".join(conditions)
            sql = f"""
            SELECT field_name, field_value, context, usage_count, last_used
            FROM exam_auto_fill
            WHERE {where_clause}
            ORDER BY usage_count DESC, last_used DESC

            self.cursor.execute(sql, params)

            results = []
            for row in self.cursor.fetchall():
                result = {
                    "field_name": row[0],
                    "field_value": row[1],
                    "context": eval(row[2]) if row[2] else None,
                    "usage_count": row[3],
                    "last_used": row[4]
                }
                results.append(result)

            return results
        except Exception as e:
            return []
        finally:
            self.close()

    def get_auto_fill_suggestions(self, user_id, exam_id, question_id, field_name, context=None):
        """获取自动填充建议"""
        if not self.connect():
            return []

        try:
            # 获取相关的自动填充数据
            sql = """
            SELECT field_value, usage_count, context
            WHERE user_id = ? AND field_name = ?

            suggestions = []
            for row in self.cursor.fetchall():
                # 计算匹配度
                score = row[1]  # 基础分数基于使用次数
                # 如果提供了上下文，计算上下文匹配度
                if context and row[2]:
                    try:
                        stored_context = eval(row[2])
                        if isinstance(stored_context, dict) and isinstance(context, dict):
                            # 简单的上下文匹配计算
                            if common_keys:
                                match_count = sum(1 for key in common_keys if stored_context.get(key) == context.get(key))
                        pass

                suggestions.append({
                    "value": row[0],
                    "score": score,
                    "context": eval(row[2]) if row[2] else None

            # 按分数排序
            suggestions.sort(key=lambda x: x["score"], reverse=True)

            return suggestions
        except Exception as e:
            print(f"获取自动填充建议失败: {str(e)}")
            return []
        finally:
            self.close()

    def save_exam_performance(self, user_id, exam_id, score, time_spent=None, correct_answers=None, total_questions=None, difficulty_level=None, strengths=None, weaknesses=None):
        """保存考试性能数据"""
        if not self.connect():
            return False

        try:
            sql = """
            INSERT INTO exam_performance
            (user_id, exam_id, score, time_spent, correct_answers, total_questions,
             difficulty_level, strengths, weaknesses)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            params = (
                exam_id,
                score,
                total_questions,
                difficulty_level,
                str(weaknesses) if weaknesses else None
            )
            self.cursor.execute(sql, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存考试性能数据失败: {str(e)}")
            return False
        finally:
            self.close()

    def get_exam_performance(self, user_id, exam_id=None, limit=50, offset=0):
        """获取考试性能数据"""
        if not self.connect():
            return []

        try:
            conditions = ["user_id = ?"]
            params = [user_id]

            if exam_id:
                conditions.append("exam_id = ?")
                params.append(exam_id)
            where_clause = " AND ".join(conditions)
            SELECT id, exam_id, score, time_spent, correct_answers, total_questions,
                   difficulty_level, strengths, weaknesses, created_at
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            self.cursor.execute(sql, params)

            for row in self.cursor.fetchall():
                performance = {
                    "id": row[0],
                    "exam_id": row[1],
                    "score": row[2],
                    "time_spent": row[3],
                    "correct_answers": row[4],
                    "total_questions": row[5],
                    "difficulty_level": row[6],
                    "strengths": eval(row[7]) if row[7] else None,
                    "created_at": row[9]
                performances.append(performance)
            return performances
        except Exception as e:
            return []

        """设置考试设置"""
        if not self.connect():

            sql = """
            INSERT OR REPLACE INTO exam_settings
            (user_id, setting_key, setting_value, category, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            self.cursor.execute(sql, (user_id, setting_key, setting_value, category))
            return True
        except Exception as e:
            print(f"设置考试设置失败: {str(e)}")
        finally:
            self.close()

    def get_exam_settings(self, user_id, category=None):
            return {}

        try:
            # 构建查询

            if category:

            sql = f"""
            FROM exam_settings
            WHERE {where_clause}

            self.cursor.execute(sql, params)

            settings = {}
            for row in self.cursor.fetchall():
                    settings[cat] = {}
                settings[cat][key] = value

            return settings
        except Exception as e:
            print(f"获取考试设置失败: {str(e)}")
        finally:
            self.close()

    def record_exam_behavior(self, user_id, exam_id, question_id, action_type, action_data=None, time_spent=None, attempt_count=1, difficulty_perceived=None, confidence_level=None):
        """记录考试行为"""
            return False

        try:
            sql = """
            INSERT INTO exam_behavior (user_id, exam_id, question_id, action_type, action_data, time_spent, attempt_count, difficulty_perceived, confidence_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            self.cursor.execute(sql, (
                user_id,
                exam_id,
                question_id,
                action_type,
                str(action_data) if action_data else None,
                attempt_count,
                confidence_level
            self.conn.commit()
            return True
            print(f"记录考试行为失败: {str(e)}")
            return False
        finally:

    def get_exam_behavior(self, user_id, exam_id, question_id=None, limit=100, offset=0):
        """获取考试行为记录"""
        if not self.connect():
            return []

        try:
            params = [user_id, exam_id]
            if question_id:
                params.append(question_id)

            where_clause = " AND ".join(conditions)
            FROM exam_behavior
            ORDER BY timestamp

            params.extend([limit, offset])
            self.cursor.execute(sql, params)

            behaviors = []
                behavior = {
                    "id": row[0],
                    "action_type": row[2],
                    "action_data": eval(row[3]) if row[3] else None,
                    "timestamp": row[4],
                    "difficulty_perceived": row[7],
                    "confidence_level": row[8]
                }
                behaviors.append(behavior)

            return behaviors
            print(f"获取考试行为记录失败: {str(e)}")
            return []
        finally:
            self.close()

        """分析考试性能"""

        try:
            # 获取考试性能数据
            sql = """
            SELECT score, time_spent, correct_answers, total_questions, difficulty_level, strengths, weaknesses
            FROM exam_performance
            WHERE user_id = ? AND exam_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            self.cursor.execute(sql, (user_id, exam_id))

            if not row:
                return None

                "score": score,
                "time_spent": time_spent,
                "accuracy": correct_answers / total_questions if total_questions > 0 else 0,
                "difficulty_level": difficulty_level,
                "weaknesses": eval(weaknesses) if weaknesses else [],
                "recommendations": []
            }

            if analysis["accuracy"] < 0.6:

                analysis["recommendations"].append("建议在答题时更加仔细，不要过于匆忙")
            if difficulty_level and difficulty_level < 3:
                analysis["recommendations"].append("建议尝试更高级别的题目，挑战自己")
            return analysis
            print(f"分析考试性能失败: {str(e)}")
            return None
    def detect_cheating(self, user_id, exam_id):
        """检测作弊行为"""
        if not self.connect():
            return None

        try:

            if not behaviors:
                return None

            # 分析行为
            suspicious_activities = []
            time_spent_list = []
            action_counts = {}

                # 记录时间花费
                if behavior["time_spent"]:
                    time_spent_list.append(behavior["time_spent"])

                action_type = behavior["action_type"]
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
                if behavior["time_spent"] and behavior["time_spent"] < 2:
                    suspicious_activities.append({
                        "type": "quick_answer",
                        "question_id": behavior["question_id"],
                        "time_spent": behavior["time_spent"]
                    })

            if time_spent_list:
                avg_time = sum(time_spent_list) / len(time_spent_list)

                if std_dev > avg_time * 0.5:
                    suspicious_activities.append({
                        "type": "time_anomaly",
                        "message": "答题时间波动异常",
                        "average_time": avg_time,
                        "std_deviation": std_dev
                    })

            # 检测过多的修改
            if action_counts.get("modify_answer", 0) > len(behaviors) * 0.5:
                    "type": "frequent_modifications",
                    "message": "频繁修改答案",
                    "count": action_counts.get("modify_answer", 0)
                })

            return {
                "suspicious_activities": suspicious_activities,
                "risk_score": min(100, len(suspicious_activities) * 25),
                "action_summary": action_counts
        except Exception as e:
            print(f"检测作弊行为失败: {str(e)}")
            return None
        finally:
            self.close()
    def analyze_answer_behavior(self, user_id, exam_id):
        """分析用户答题行为模式"""
            return None

        try:
            behaviors = self.get_exam_behavior(user_id, exam_id)

            if not behaviors:
                return None
            # 分析行为
            behavior_analysis = {
                "total_actions": len(behaviors),
                "action_distribution": {},
                "time_distribution": {},
                "modification_count": 0,
                "confidence_levels": [],
                "difficulty_perceptions": [],
                "question_analysis": {}
            }
            # 按题目分组分析
            questions = {}
            for behavior in behaviors:
                question_id = behavior["question_id"]
                if question_id not in questions:
                    questions[question_id] = []
                questions[question_id].append(behavior)

            # 统计动作分布
            for behavior in behaviors:
                action_type = behavior["action_type"]

                # 统计修改次数
                    behavior_analysis["modification_count"] += 1

                # 收集信心水平
                if behavior["confidence_level"]:
                    behavior_analysis["confidence_levels"].append(behavior["confidence_level"])

                # 收集难度感知
                if behavior["difficulty_perceived"]:

            # 分析每个题目的行为
            total_time = 0
            for question_id, question_behaviors in questions.items():
                question_analysis = {
                    "actions": len(question_behaviors),
                    "attempts": 0,
                    "confidence": None,
                    "difficulty": None
                }

                for behavior in question_behaviors:
                        question_analysis["time_spent"] += behavior["time_spent"]
                        total_time += behavior["time_spent"]
                    if behavior["action_type"] == "modify_answer":
                        question_analysis["modifications"] += 1

                    if behavior["attempt_count"]:
                        question_analysis["attempts"] = max(question_analysis["attempts"], behavior["attempt_count"])

                        question_analysis["confidence"] = behavior["confidence_level"]

                    if behavior["difficulty_perceived"]:
                        question_analysis["difficulty"] = behavior["difficulty_perceived"]
                behavior_analysis["question_analysis"][question_id] = question_analysis

            # 计算平均答题时间
            if questions:
                behavior_analysis["average_time_per_question"] = total_time / len(questions)

            # 分析时间分布
            if behaviors:
                time_spent_list = [b["time_spent"] for b in behaviors if b["time_spent"]]
                if time_spent_list:
                    avg_time = sum(time_spent_list) / len(time_spent_list)
                    behavior_analysis["time_distribution"] = {
                        "min": min(time_spent_list),
                        "max": max(time_spent_list),
                        "total": sum(time_spent_list)
                    }

            return behavior_analysis
        except Exception as e:
            return None
        finally:
            self.close()
    def generate_question_with_ai(self, topic, question_type, difficulty, education_version):
        """使用AI生成题目

        Args:
            question_type: 题目类型
            difficulty: 难度级别
            education_version: 教育版本

            生成的题目
        try:
            question = exam_ai.generate_question(topic, question_type, difficulty, education_version)
            return question
        except Exception as e:
            print(f"使用AI生成题目失败: {str(e)}")
            return None

        """使用AI创建考试

        Args:
            name: 考试名称
            questions: 题目ID列表
            education_version: 教育版本

        Returns:
            创建的考试
        try:
            exam = exam_ai.create_exam(name, questions, education_version, time_limit)
            return exam
            return None

        """使用AI评分考试
        Args:
            exam_id: 考试ID
            correct_answers: 正确答案

        Returns:
        try:
            evaluation = exam_ai.score_exam(exam_id, answers, correct_answers)
            return evaluation
        except Exception as e:
            print(f"使用AI评分考试失败: {str(e)}")
            return None
    def analyze_learning_patterns_with_ai(self, user_id, exam_results):
        """使用AI分析学习模式

        Args:
            user_id: 用户ID

        Returns:
            学习模式分析
            learning_patterns = exam_ai.analyze_learning_patterns(user_id, exam_results)
            return learning_patterns
        except Exception as e:
            print(f"使用AI分析学习模式失败: {str(e)}")
            return None

        Args:
            user_id: 用户ID
            exam_behavior: 考试行为记录

        Returns:
            作弊检测结果
        try:
            cheating_detection = exam_ai.detect_cheating(user_id, exam_id, exam_behavior)
            return cheating_detection
        except Exception as e:
            print(f"使用AI检测作弊行为失败: {str(e)}")
            return None

    def generate_adaptive_test_with_ai(self, user_id, topic, initial_difficulty, target_score):

        Args:
            user_id: 用户ID
            topic: 测试主题
            initial_difficulty: 初始难度
            target_score: 目标分数

        Returns:
            自适应测试
        try:
            adaptive_test = exam_ai.generate_adaptive_test(user_id, topic, initial_difficulty, target_score)
            return adaptive_test
        except Exception as e:
            print(f"使用AI生成自适应测试失败: {str(e)}")
            return None
    def provide_feedback_with_ai(self, user_id, exam_id, evaluation):

        Args:
            user_id: 用户ID
            exam_id: 考试ID
            evaluation: 考试评价

        Returns:
            反馈结果
        try:
            feedback = exam_ai.provide_feedback(user_id, exam_id, evaluation)
            return feedback
        except Exception as e:
            return None

    def check_question_generation_rules(self, question):

            question: 题目

        Returns:
            检查结果
            result = exam_rule_manager.check_question_generation(question)
            return result
        except Exception as e:
            print(f"检查题目生成规则失败: {str(e)}")
            return None
    def check_exam_creation_rules(self, exam):

        Args:
            exam: 考试

            检查结果
        try:
            result = exam_rule_manager.check_exam_creation(exam)
            return result
        except Exception as e:
            print(f"检查考试创建规则失败: {str(e)}")
            return None

        """检查评分规则

        Args:
            score: 分数

        Returns:
        try:
            result = exam_rule_manager.check_scoring(score)
            return result
        except Exception as e:
            print(f"检查评分规则失败: {str(e)}")
            return None

    def check_user_access_rules(self, user_id, exam_count, last_exam_time=None):
        """检查用户访问规则

        Args:
            user_id: 用户ID
            last_exam_time: 上次考试时间

            检查结果
        try:
            result = exam_rule_manager.check_user_access(user_id, exam_count, last_exam_time)
            return result
        except Exception as e:
            print(f"检查用户访问规则失败: {str(e)}")
            return None

    def get_exam_rules(self, rule_type=None):
        """获取考试规则
        Args:
            rule_type: 规则类型

        Returns:
            if rule_type:
                return exam_rule_manager.get_rules(rule_type)
            else:
                return exam_rule_manager.get_all_rules()
        except Exception as e:
            print(f"获取考试规则失败: {str(e)}")
            return {}

    def update_exam_rules(self, rule_type, rules):
        """更新考试规则

        Args:
            rule_type: 规则类型
            rules: 规则字典

        Returns:
            exam_rule_manager.update_rules(rule_type, rules)
            return True
        except Exception as e:
            print(f"更新考试规则失败: {str(e)}")
            return False

    def check_exam_access(self, role, exam_id, action):
        """检查用户对考试的访问权限

        Args:
            role: 角色名称
            exam_id: 考试ID
            action: 操作类型 (view, edit, delete, take)

            是否有权限
        try:
            result = exam_permission_manager.check_exam_access(role, exam_id, action)
        except Exception as e:
            print(f"检查考试访问权限失败: {str(e)}")
            return False

    def check_question_access(self, role, question_id, action):
        """检查用户对题目的访问权限

        Args:
            role: 角色名称
            question_id: 题目ID
            action: 操作类型 (view, edit, delete, generate)

        Returns:
            是否有权限
            result = exam_permission_manager.check_question_access(role, question_id, action)
        except Exception as e:
            print(f"检查题目访问权限失败: {str(e)}")

    def get_user_permissions(self, role):
        """获取用户权限

        Args:
            role: 角色名称

        Returns:
            权限列表
        try:
            permissions = exam_permission_manager.get_permissions(role)
            return permissions
            print(f"获取用户权限失败: {str(e)}")
            return []

        """检查角色是否有指定权限
        Args:
            role: 角色名称
            permission: 权限名称

            是否有权限
        try:
            result = exam_permission_manager.has_permission(role, permission)
            return result
            print(f"检查权限失败: {str(e)}")

    def update_user_permissions(self, role, permissions):
        """更新用户权限

        Args:
            role: 角色名称

        Returns:
        try:
            exam_permission_manager.update_permissions(role, permissions)
            return True
        except Exception as e:
            print(f"更新用户权限失败: {str(e)}")

    def get_all_roles(self):
        """获取所有角色

        Returns:
            角色列表
        try:
            return roles
        except Exception as e:
            print(f"获取角色列表失败: {str(e)}")
            return []

# 全局考试服务实例
exam_service = None

    """获取考试服务实例"""
    global exam_service
    if exam_service is None:
        exam_service = ExamService()
    return exam_service

if __name__ == "__main__":
    service = ExamService()

    # 测试保存自动填充数据
    user_id = 1
    exam_id = 1
    question_id = 1

    print("保存自动填充数据...")
        user_id, exam_id, question_id, "answer", "A",
        context={"question_type": "multiple_choice", "difficulty": "easy"}
    )
    print(f"保存结果: {result}")

    # 测试获取自动填充建议
    print("\n获取自动填充建议...")
    suggestions = service.get_auto_fill_suggestions(
        user_id, exam_id, question_id, "answer",
    )
    print(f"建议: {str(suggestions, indent=2)}")
    # 测试保存考试性能
    print("\n保存考试性能...")
    result = service.save_exam_performance(
        user_id, exam_id, 85.5, 1200, 17, 20, 3.5,
        strengths=["语法", "词汇"],
        weaknesses=["听力", "写作"]
    )
    print(f"保存结果: {result}")

    # 测试分析考试性能
    print("\n分析考试性能...")
    analysis = service.analyze_exam_performance(user_id, exam_id)
    print(f"分析结果: {str(analysis, indent=2)}")

    print("\n记录考试行为...")
    result = service.record_exam_behavior(
        user_id, exam_id, question_id, "answer",
        action_data={"selected_option": "A"}, time_spent=5
    )
    # 测试检测作弊
    print("\n检测作弊行为...")
    cheating_detection = service.detect_cheating(user_id, exam_id)
    print(f"检测结果: {str(cheating_detection, indent=2)}")
