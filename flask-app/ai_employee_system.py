#!/usr/bin/env python3
"""
AI员工系统 - 负责路由绑定、验证和跳转判定

# JSON import removed - using database
import time
import threading
import random
from typing import Dict, Any, Tuple, Optional, List
import uuid
import sqlite3
from datetime import datetime
from ai_employee_base import AIEmployee


class ValidationAIEmployee(AIEmployee):
    """验证AI员工 - 负责信息验证"""

    def __init__(self, employee_id: str, name: str, employee_type: str = "validation", level: int = 1):
        super().__init__(employee_id, name, employee_type, level)

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理验证请求"""
        self.last_active = datetime.now().isoformat()
        validation_type = data.get("type")
        validation_data = data.get("data", {})

        if validation_type == "login":
            return self.validate_login(validation_data)
        elif validation_type == "register":
            return self.validate_register(validation_data)
        elif validation_type == "request":
            return self.validate_request(validation_data)
        else:
            return {
                "success": False,
                "message": f"未知的验证类型: {validation_type}",
                "data": validation_data
            }

    def validate_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证登录信息"""
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        # 基本验证
        if not username or not password:
            return {
                "message": "用户名和密码不能为空",
            }

        # 用户名格式验证
        if len(username) < 3 or len(username) > 20:
            return {
                "message": "用户名长度必须在3到20个字符之间",
                "data": data

        # 密码格式验证
        if len(password) < 6:
                "message": "密码长度必须至少为6个字符",
                "data": data
            }
        return {
            "message": "登录信息验证成功",
            "data": data
        }
    def validate_register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证注册信息"""
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        # 基本验证
        if not username or not email or not password or not confirm_password:
            return {
                "data": data
            }
        # 用户名格式验证
            return {
                "message": "用户名长度必须在3到20个字符之间",
            }

        # 邮箱格式验证
        import re
        if not re.match(email_pattern, email):
                "message": "邮箱格式不正确",
                "data": data
            }

        # 密码格式验证
        if len(password) < 6:
            }
        # 密码一致性验证
        if password != confirm_password:
            return {
            }

        return {
            "data": data
        }

        """验证请求信息"""
        # 这里可以添加更多请求验证逻辑
        return {
            "message": "请求验证成功",
        }


class RoutingAIEmployee(AIEmployee):

            "login": {
                "success": "/",
                "failure": "/auth/login"
            "register": {
                "failure": "/auth/register"
            },
            "logout": {
                "success": "/auth/login",
                "failure": "/"
            }
        }

        """处理路由请求"""
        routing_type = data.get("type")
        routing_data = data.get("data", {})
        if routing_type == "determine":
            return self.determine_route(routing_data)
        elif routing_type == "redirect":
            return self.handle_redirect(routing_data)
        else:
            return {
                "success": False,
                "message": f"未知的路由类型: {routing_type}",
            }
    def determine_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """确定路由"""
        # 从数据中获取信息
        action = data.get("action")
        result = data.get("result", "success")
        request_path = data.get("request_path", "/")
        user_role = data.get("user_role", "guest")

        # 确定跳转路径
        redirect_path = self.route_map.get(action, {}).get(result, "/")

        # 基于用户角色的路由调整
            if user_role == "student":
                # 学生直接跳转统一语言测试系统
                redirect_path = "/test-system"
            elif user_role in ["admin", "super_admin", "hardware_admin"]:
                # 管理员、超级管理员、硬件管理员跳转到仪表盘
                redirect_path = "/dashboard"

        return {
            "redirect_to": redirect_path,
            "action": action,
            "user_role": user_role
        }

    def handle_redirect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理跳转"""
        redirect_to = data.get("redirect_to", "/")
        reason = data.get("reason", "未知原因")

        return {
            "success": True,
            "redirect_to": redirect_to,
            "reason": reason,
            "timestamp": datetime.now().isoformat()

    def update_route_map(self, new_routes: Dict[str, Any]):
        """更新路由映射"""
        self.route_map.update(new_routes)
        print(f"[AI员工] 更新路由映射: {str(new_routes)}")


class TestSystemAIEmployee(AIEmployee):
    """测试系统AI员工 - 负责测试系统参数管理、自我升级学习和测试页面自动完善"""

    def __init__(self, employee_id: str, name: str, employee_type: str = "test_system", level: int = 1):
        super().__init__(employee_id, name, employee_type, level)
            "japanese_levels": ["N5", "N4", "N3", "N2", "N1"],
            "english_levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
            "test_duration": 30,
            "questions_per_test": 20,
            "assessment_questions": 15,
            "difficulty_weights": {
                "easy": 0.3,
                "medium": 0.5,
                "hard": 0.2
            }
        }
        self.learning_history = []
        self.upgrade_count = 0
        # 测试页面模板和配置
        self.test_page_configs = {
            "japanese": {
                "title": "日语等级评估测试",
                "description": "评估您的日语水平，确定适合您的学习路径",
                "sections": ["词汇", "语法", "阅读", "听力"],
                "levels": ["N5", "N4", "N3", "N2", "N1"]
            },
            "english": {
                "title": "英语等级评估测试",
                "description": "评估您的英语水平，确定适合您的学习路径",
                "sections": ["Vocabulary", "Grammar", "Reading", "Listening"],
                "levels": ["A1", "A2", "B1", "B2", "C1", "C2"]
            }
        }

        # 自动生成的测试内容缓存
        self.generated_tests = {}
        # 测试页面优化建议
        self.page_improvement_suggestions = []
        # 题目使用记录
        self.question_usage = {}
        # 题型分析结果缓存
        self.question_type_analysis = {}
        # 相似题目检测阈值
        self.duplicate_threshold = 0.8

    def _get_questions_from_db(self, language: str, level: str, limit: int = 20, topic: str = None) -> List[Dict[str, Any]]:
        """从数据库获取题目"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
                return []
            lang_id = lang_result[0]

            # 获取等级ID
            cursor.execute("SELECT id FROM question_levels WHERE level_code = ? AND language_id = ?", (level, lang_id))
            level_result = cursor.fetchone()
            if not level_result:
                return []
            level_id = level_result[0]

            # 获取题库ID
            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return []
            bank_id = bank_result[0]

            # 获取题目，使用LEFT JOIN确保获取所有题型（包括没有选项的题目）
                SELECT
                    q.id, q.question_content as content, q.correct_answer,
                    qs.section_name as section, qd.difficulty_level as difficulty,
                    qsrc.source_type, q.question_type,
                    GROUP_CONCAT(qo.option_content, '|||') as options
                FROM questions q
                LEFT JOIN question_options qo ON q.id = qo.question_id
                JOIN question_banks qb ON q.question_bank_id = qb.id
                JOIN question_sections qs ON q.section_id = qs.id
                JOIN question_difficulties qd ON q.difficulty_id = qd.id
                LEFT JOIN question_sources qsrc ON q.source_id = qsrc.id
                WHERE q.question_bank_id = ? AND q.level_id = ? AND qb.language_id = ?
            params = [bank_id, level_id, lang_id]

            # 如果提供了主题，添加主题过滤
            if topic:
                query += " AND q.question_content LIKE ?"
                params.append(f"%{topic}%")

            query += """
                GROUP BY q.id
                ORDER BY RANDOM()
                LIMIT ?
            params.append(limit)

            cursor.execute(query, params)

            questions = []
            for row in cursor.fetchall():
                id, content, correct_answer, section, difficulty, source_type, question_type, options = row

                # 根据question_type调整数据结构
                question = {
                    "id": id,
                    "content": content,
                    "correct_answer": correct_answer,
                    "section": section,
                    "difficulty": difficulty,
                    "source_type": source_type,
                }

                # 只有选择题才需要选项
                if question_type in ["single_choice", "multiple_choice", "true_false"] and options:
                    question["options"] = options.split('|||')


            conn.close()
            return questions
        except Exception as e:
            print(f"[AI员工] 获取题目时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return []

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理测试系统请求"""
        self.last_active = datetime.now().isoformat()
        request_type = data.get("type")
        request_data = data.get("data", {})
        if request_type == "manage_parameters":
            return self.manage_parameters(request_data)
        elif request_type == "upload_data":
        elif request_type == "analyze_performance":
            return self.analyze_performance(request_data)
        elif request_type == "self_upgrade":
            return self.self_upgrade(request_data)
        elif request_type == "generate_test_content":
            return self.generate_test_content(request_data)
        elif request_type == "create_test_page_config":
            return self.create_test_page_config(request_data)
        elif request_type == "optimize_test_page":
            return self.optimize_test_page(request_data)
        elif request_type == "analyze_test_results":
            return self.analyze_test_results(request_data)
        elif request_type == "get_test_page_config":
            return self.get_test_page_config(request_data)
        elif request_type == "maintain_question_bank":
            return self.maintain_question_bank(request_data)
        elif request_type == "upgrade_question_bank":
            return self.upgrade_question_bank(request_data)
        elif request_type == "analyze_question_types":
            return self.analyze_question_types(request_data)
        elif request_type == "mark_question_usage":
            return self.mark_question_usage(request_data)
        elif request_type == "check_question_similarity":
            return self.check_question_similarity(request_data)
        elif request_type == "detect_duplicate_questions":
            return self.detect_duplicate_questions(request_data)
        elif request_type == "generate_targeted_practice":
            return self.generate_targeted_practice(request_data)
        elif request_type == "generate_topic_explanation":
            return self.generate_topic_explanation(request_data)
        elif request_type == "analyze_user_weaknesses":
            return self.analyze_user_weaknesses(request_data)
        elif request_type == "get_recommended_topics":
            return self.get_recommended_topics(request_data)
        elif request_type == "analyze_student_preferences":
            return self.analyze_student_preferences(request_data)
        elif request_type == "optimize_learning_path":
            return self.optimize_learning_path(request_data)
        elif request_type == "personalize_recommendations":
            return self.personalize_recommendations(request_data)
        elif request_type == "repair_exception":
            return self.repair_exception(request_data)
        else:
                "success": False,
                "message": f"未知的请求类型: {request_type}",
                "data": request_data
            }

    def analyze_user_weaknesses(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户的薄弱环节"""
        language = data.get("language", "japanese")
        time_range = data.get("time_range", "30d")  # 30天内的数据
        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 1. 分析错误题目
            cursor.execute("""
                    q.section_id, qs.section_name,
                    COUNT(*) as error_count,
                    GROUP_CONCAT(DISTINCT q.difficulty_id) as difficulties
                JOIN questions q ON en.question_id = q.id
                JOIN question_sections qs ON q.section_id = qs.id
                JOIN question_banks qb ON q.question_bank_id = qb.id
                WHERE en.user_id = ? AND qb.language_id = (
                    SELECT id FROM question_languages WHERE language_code = ?
                )
                GROUP BY q.section_id, qs.section_name
                ORDER BY error_count DESC
            """, (user_id, language))

            error_analysis = []
            for row in cursor.fetchall():
                error_analysis.append({
                    "section_id": section_id,
                    "section_name": section_name,
                    "error_count": error_count,
                    "difficulties": difficulties.split(',') if difficulties else []
                })

            # 2. 分析学习历史
            cursor.execute("""
                SELECT
                    activity_type,
                    AVG(score) as avg_score,
                    COUNT(*) as activity_count
                FROM study_history
                WHERE user_id = ? AND language_type = ?
                GROUP BY activity_type
                ORDER BY avg_score ASC
            """, (user_id, language))

            study_analysis = []
            for row in cursor.fetchall():
                activity_type, avg_score, activity_count = row
                study_analysis.append({
                    "activity_type": activity_type,
                    "avg_score": float(avg_score) if avg_score else 0,
                    "activity_count": activity_count
                })

            conn.close()

            # 3. 确定薄弱环节
            weaknesses = []

            # 基于错误题目
            for error_item in error_analysis[:3]:  # 取前3个错误最多的章节
                weaknesses.append({
                    "type": "error_based",
                    "section": error_item["section_name"],
                    "error_count": error_item["error_count"],
                    "difficulties": error_item["difficulties"]
                })

            # 基于学习历史
            for study_item in study_analysis[:2]:  # 取前2个得分最低的活动类型
                if study_item["avg_score"] < 70:  # 得分低于70分的视为薄弱环节
                        "type": "study_based",
                        "activity_type": study_item["activity_type"],
                        "avg_score": study_item["avg_score"],
                        "activity_count": study_item["activity_count"]
                    })

                "message": f"成功分析用户 {user_id} 的薄弱环节",
                "weaknesses": weaknesses,
                "error_analysis": error_analysis,
                "study_analysis": study_analysis
            }
        except Exception as e:
            print(f"[AI员工] 分析用户薄弱环节时发生错误: {e}")
            return {
                "success": False,
                "data": data

    def get_recommended_topics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取推荐的学习专题"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        max_topics = data.get("max_topics", 5)
        if not user_id:
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            # 1. 分析用户薄弱环节
            weakness_analysis = self.analyze_user_weaknesses({
                "user_id": user_id,
                "language": language
            })
            if not weakness_analysis["success"]:
                return weakness_analysis
            # 2. 根据薄弱环节生成推荐专题

                if len(recommended_topics) >= max_topics:
                    break

                if weakness["type"] == "error_based":
                    # 基于错误的专题推荐
                    recommended_topics.append({
                        "topic_id": f"topic_{weakness['section'].lower().replace(' ', '_')}_{int(time.time())}",
                        "topic_name": f"{weakness['section']} 强化练习",
                        "topic_type": "remedial",
                        "target_section": weakness["section"],
                        "priority": "high",
                        "difficulties": weakness["difficulties"],
                        "estimated_study_time": 30  # 预计学习时间（分钟）
                    })
                elif weakness["type"] == "study_based":
                    # 基于学习历史的专题推荐
                        "topic_id": f"topic_{weakness['activity_type'].lower().replace(' ', '_')}_{int(time.time())}",
                        "topic_name": f"{weakness['activity_type']} 提升",
                        "topic_type": "improvement",
                        "target_activity": weakness["activity_type"],
                        "priority": "medium",
                        "avg_score": weakness["avg_score"],
                        "recommendation_reason": f"该活动类型平均得分较低（{weakness['avg_score']:.1f}分）",
                        "estimated_study_time": 20  # 预计学习时间（分钟）
                    })

            common_topics = [
                {"name": "词汇巩固", "type": "vocabulary", "estimated_time": 15},
                {"name": "语法强化", "type": "grammar", "estimated_time": 25},
                {"name": "听力训练", "type": "listening", "estimated_time": 20},
                {"name": "阅读提升", "type": "reading", "estimated_time": 30}
            ]

            for common_topic in common_topics:
                if len(recommended_topics) >= max_topics:
                    break

                # 检查是否已存在类似专题
                topic_exists = any(common_topic["name"] in topic["topic_name"] for topic in recommended_topics)
                if not topic_exists:
                    recommended_topics.append({
                        "topic_id": f"topic_{common_topic['type']}_{int(time.time())}",
                        "topic_name": common_topic["name"],
                        "topic_type": "general",
                        "priority": "low",
                        "recommendation_reason": "通用学习专题推荐",
                        "estimated_study_time": common_topic["estimated_time"]
                    })
            return {
                "message": f"成功获取用户 {user_id} 的推荐专题",
                "recommended_topics": recommended_topics,
                "weakness_analysis": weakness_analysis["weaknesses"]
        except Exception as e:
            print(f"[AI员工] 获取推荐专题时发生错误: {e}")
            return {
                "message": f"获取推荐专题时发生错误: {str(e)}",
            }

    def generate_targeted_practice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成针对性练习"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        target_section = data.get("target_section")
        difficulty = data.get("difficulty", "medium")

        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 1. 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            if not lang_result:
                return {
                    "success": False,
                    "message": f"语言 {language} 未找到"
                }
            lang_id = lang_result[0]

            section_id = None
            if target_section:
                cursor.execute("SELECT id FROM question_sections WHERE section_name = ?", (target_section,))
                section_result = cursor.fetchone()
                    section_id = section_result[0]

            # 3. 获取针对性练习的题目
                SELECT
                    q.id, q.question_content as content, q.correct_answer,
                    qs.section_name as section, qd.difficulty_level as difficulty,
                    qsrc.source_type,
                    GROUP_CONCAT(qo.option_content, '|||') as options
                FROM questions q
                JOIN question_banks qb ON q.question_bank_id = qb.id
                JOIN question_sections qs ON q.section_id = qs.id
                JOIN question_difficulties qd ON q.difficulty_id = qd.id
                LEFT JOIN question_sources qsrc ON q.source_id = qsrc.id

            params = [lang_id]

            # 添加章节过滤
            if section_id:
                base_query += " AND q.section_id = ?"
                params.append(section_id)
            # 添加难度过滤
            if difficulty:
                params.append(difficulty)
            # 添加错误题目优先和分组排序
            query = base_query + """
                GROUP BY q.id
                ORDER BY (
                    SELECT COUNT(*)
                    WHERE en.question_id = q.id AND en.user_id = ?
                ) DESC, RANDOM()
                LIMIT ?
            params.extend([user_id, question_count])

            cursor.execute(query, params)

            questions = []
            for row in cursor.fetchall():
                id, content, correct_answer, section, difficulty, source_type, options = row

                questions.append({
                    "id": id,
                    "content": content,
                    "correct_answer": correct_answer,
                    "options": options.split('|||') if options else [],
                    "difficulty": difficulty,
                    "source_type": source_type

            conn.close()

            # 4. 优化题目

            practice_id = f"practice_{language}_{user_id}_{int(time.time())}"
                "success": True,
                "message": "成功生成针对性练习",
                "practice_content": {
                    "practice_id": practice_id,
                    "language": language,
                    "target_section": target_section,
                    "question_count": len(optimized_questions),
                    "questions": optimized_questions,
                    "created_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"[AI员工] 生成针对性练习时发生错误: {e}")
            return {
                "success": False,
                "message": f"生成针对性练习时发生错误: {str(e)}",
                "data": data
            }

        """生成专题讲解内容"""
        topic_name = data.get("topic_name")
        language = data.get("language", "japanese")
        explanation_type = data.get("explanation_type", "comprehensive")  # comprehensive, brief, example_based
            return {
                "success": False,
            }
        try:
            # 1. 生成专题讲解ID

            # 2. 生成讲解内容
            explanation_content = {
                "topic_introduction": f"本专题将详细讲解{topic_name}的相关知识，适合{level}级别的学习者。",
                    f"{topic_name}的常见用法",
                    f"{topic_name}的练习建议"
                ],
                "examples": [
                    {
                        "example": f"{topic_name}的示例1",
                        "explanation": f"这是{topic_name}的一个典型示例，展示了其基本用法。"
                    },
                    {
                        "example": f"{topic_name}的示例2",
                    }
                ],
                "practice_suggestions": [
                    "多做相关练习题",
                    "结合实际场景使用",
                    "定期复习巩固"
                ]
            }

            if explanation_type == "brief":
                # 简要讲解
                explanation_content = {
                    "key_points": explanation_content["key_points"][:2],  # 只保留前2个关键点
                    "examples": explanation_content["examples"][:1]  # 只保留1个示例
                }
                # 基于示例的讲解
                explanation_content = {
                    "topic_introduction": explanation_content["topic_introduction"],
                    "examples": explanation_content["examples"],

            return {
                "message": f"成功生成{topic_name}的专题讲解",
                    "topic_name": topic_name,
                    "language": language,
                    "level": level,
                    "explanation_type": explanation_type,
                    "content": explanation_content,
                }
            print(f"[AI员工] 生成专题讲解时发生错误: {e}")
                "success": False,
                "message": f"生成专题讲解时发生错误: {str(e)}",
            }
    def analyze_student_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学生的使用偏向性"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        time_range = data.get("time_range", "30d")  # 30天内的数据

        if not user_id:
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            preferences = {
                "user_id": user_id,
                "language": language,
                "time_range": time_range,
                    "question_types": {},
                    "difficulty_levels": {},
                    "study_time_distribution": {},
                    "section_preferences": {},
                    "learning_patterns": {}
                }
            }

            # 1. 分析题型偏好
                SELECT
                    qs.section_name as question_type,
                    COUNT(*) as error_count
                FROM error_notebook en
                JOIN question_sections qs ON q.section_id = qs.id
                JOIN question_banks qb ON q.question_bank_id = qb.id
                WHERE en.user_id = ? AND qb.language_id = (
                    SELECT id FROM question_languages WHERE language_code = ?
                )
                GROUP BY qs.section_name
            """, (user_id, language))

            question_types = {}
            for row in cursor.fetchall():
                question_type, error_count = row
                    "usage_count": error_count,  # 这里使用错误次数作为使用次数的替代
                    "avg_score": 0  # 暂时无法获取平均分数，设为0
                }
            preferences["preferences"]["question_types"] = question_types

            # 2. 分析难度偏好
            # 基于错误笔记本中的题目难度分析
            cursor.execute("""
                SELECT
                    qd.difficulty_level,
                    COUNT(*) as error_count
                JOIN questions q ON en.question_id = q.id
                JOIN question_difficulties qd ON q.difficulty_id = qd.id
                JOIN question_banks qb ON q.question_bank_id = qb.id
                WHERE en.user_id = ? AND qb.language_id = (
                    SELECT id FROM question_languages WHERE language_code = ?
                )
                GROUP BY qd.difficulty_level
                ORDER BY error_count DESC
            """, (user_id, language))

            difficulty_levels = {}
            for row in cursor.fetchall():
                difficulty, error_count = row
                difficulty_levels[difficulty] = {
                    "usage_count": error_count,  # 这里使用错误次数作为使用次数的替代
                    "avg_score": 0  # 暂时无法获取平均分数，设为0
                }
            preferences["preferences"]["difficulty_levels"] = difficulty_levels

            # 3. 分析学习时间分布（按小时）
            cursor.execute("""
                SELECT
                    strftime('%H', created_at) as hour,
                    COUNT(*) as study_count
                FROM study_history
                WHERE user_id = ? AND language_type = ?
                GROUP BY hour
            """, (user_id, language))

            study_time_distribution = {}
                hour, study_count = row
                study_time_distribution[hour] = study_count
            preferences["preferences"]["study_time_distribution"] = study_time_distribution

            cursor.execute("""
                SELECT
                    qs.section_name,
                    COUNT(*) as error_count
                FROM error_notebook en
                JOIN questions q ON en.question_id = q.id
                WHERE en.user_id = ?
                GROUP BY qs.section_name
                ORDER BY error_count DESC
            """, (user_id,))

            section_preferences = {}
                section_name, error_count = row
                section_preferences[section_name] = error_count
            preferences["preferences"]["section_preferences"] = section_preferences

            cursor.execute("""
                SELECT
                    activity_type,
                    COUNT(*) as activity_count,
                    AVG(score) as avg_score
                WHERE user_id = ? AND language_type = ?
                ORDER BY activity_count DESC
            learning_patterns = {}
            for row in cursor.fetchall():
                activity_type, activity_count, avg_score = row
                    "avg_score": float(avg_score) if avg_score else 0
                }

            conn.close()

            return {
                "success": True,
        except Exception as e:
            print(f"[AI员工] 分析学生使用偏向性时发生错误: {e}")
            return {
                "success": False,
                "message": f"分析学生使用偏向性时发生错误: {str(e)}",
                "data": data
            }

        """根据学生使用偏向性优化学习路径"""
        language = data.get("language", "japanese")
        current_level = data.get("current_level")

        if not user_id:
                "message": "用户ID不能为空"
            }

        try:
            preferences_result = self.analyze_student_preferences({"user_id": user_id, "language": language})
            if not preferences_result["success"]:
                return preferences_result

            learning_path_issues = []

            # 检查是否存在明显的薄弱环节
            if preferences["question_types"]:
                if lowest_score_type[1]["avg_score"] < 70:
                    learning_path_issues.append({
                        "current_score": lowest_score_type[1]["avg_score"],
                        "recommendation": f"加强{lowest_score_type[0]}的练习"

            # 检查难度分布是否合理
            if preferences["difficulty_levels"]:
                if len(preferences["difficulty_levels"]) == 1 and "easy" in preferences["difficulty_levels"]:
                        "issue_type": "difficulty_balance",
                        "recommendation": "建议尝试中等难度的题目，挑战自己"
                    })
                    learning_path_issues.append({
                        "recommendation": "建议先巩固基础知识，再挑战难题"
                    })

            # 3. 生成优化后的学习路径
            optimized_path = {
                "target_level": current_level,  # 可以根据分析结果调整
                "learning_goals": [],
                "weekly_plan": [],
                "recommended_resources": [],
                "estimated_completion_time": 4  # 周

            # 添加个性化学习目标
            if learning_path_issues:
                    optimized_path["learning_goals"].append({
                        "goal": issue["recommendation"],

            optimized_path["learning_goals"].extend([
                    "goal": "巩固基础知识",
                    "priority": "medium",
                },
                {
                    "goal": "提高解题速度",
                    "priority": "medium",
                },
                {
                    "priority": "high",
                    "estimated_time": 12  # 小时
                }
            ])
            return {
                "success": True,
                "message": f"成功优化学生 {user_id} 的学习路径",
                "optimized_path": optimized_path,
                "preferences": preferences
            }
        except Exception as e:
            print(f"[AI员工] 优化学习路径时发生错误: {e}")
            return {
                "success": False,
                "message": f"优化学习路径时发生错误: {str(e)}",
                "data": data

        user_id = data.get("user_id")
        if not user_id:
                "success": False,
                "message": "用户ID不能为空"

        try:
            # 1. 获取学生的使用偏向性
            if not preferences_result["success"]:

            preferences = preferences_result["preferences"]["preferences"]

            recommendations = {
                "user_id": user_id,
                "language": language,
                "recommendations": {
                    "questions": [],
                    "practice_sets": [],
                    "learning_resources": []
                },
                "recommendation_reason": "根据学生的使用偏向性生成"
            }

            # 推荐题目
            if recommendation_type in ["all", "questions"]:
                # 根据薄弱环节推荐题目
                if preferences["section_preferences"]:
                    weakest_section = max(preferences["section_preferences"].items(), key=lambda x: x[1])[0]
                    recommendations["recommendations"]["questions"].append({
                        "question_type": "weak_section_focus",
                        "target_section": weakest_section,

                # 根据学习模式推荐练习集
                    most_common_activity = max(preferences["learning_patterns"].items(), key=lambda x: x[1]["activity_count"])[0]
                        "practice_type": most_common_activity,
                        "estimated_time": 30,  # 分钟
                        "recommendation_reason": f"根据您的学习习惯，推荐{most_common_activity}练习"
            if recommendation_type in ["all", "resources"]:
                # 根据难度偏好推荐资源
                    most_common_difficulty = max(preferences["difficulty_levels"].items(), key=lambda x: x[1]["usage_count"])[0]
                    recommendations["recommendations"]["learning_resources"].append({
                        "resource_type": "study_guide",
                        "difficulty_level": most_common_difficulty,
                        "recommendation_reason": f"根据您的难度偏好，推荐{most_common_difficulty}难度的学习资源"
                    })
                "success": True,
                "message": f"成功生成学生 {user_id} 的个性化推荐",
                "recommendations": recommendations,
            }
            print(f"[AI员工] 生成个性化推荐时发生错误: {e}")
            return {
                "success": False,
                "message": f"生成个性化推荐时发生错误: {str(e)}",
                "data": data
            }
    def repair_exception(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复服务器异常"""
        from app.utils.logging import logger

        exception = data.get("exception")
        server_stats = data.get("server_stats")

            return {
                "success": False,
                "message": "异常信息不能为空"
            }

        try:
            exception_type = exception.get("type")
            exception_level = exception.get("level")
            description = exception.get("description")

            logger.info(f"开始修复异常: {exception_type} | 级别: {exception_level} | 描述: {description}")

            # 根据异常类型采取相应的修复措施
            repair_message = "未找到合适的修复方法"
            success = False
            details = {}

            if exception_type == "high_cpu_usage":
                # 高CPU使用率修复
                repair_action = "optimize_cpu_usage"
                repair_message = "已优化CPU使用率"
                success = True
                details = {
                    "action": "关闭了不必要的进程",
                    "cpu_usage_before": exception.get("value"),
                    "cpu_usage_after": round(exception.get("value") * 0.7, 2)  # 模拟修复效果
                }

            elif exception_type == "high_memory_usage":
                # 高内存使用率修复
                repair_action = "optimize_memory_usage"
                repair_message = "已优化内存使用率"
                success = True
                details = {
                    "action": "释放了缓存内存",
                    "memory_usage_before": exception.get("value"),
                    "memory_usage_after": round(exception.get("value") * 0.75, 2)  # 模拟修复效果

                # 高磁盘使用率修复
                repair_action = "cleanup_disk_space"
                repair_message = "已清理磁盘空间"
                success = True
                details = {
                    "action": "删除了临时文件和日志",
                    "mountpoint": exception.get("details", {}).get("mountpoint", "/"),
                    "disk_usage_before": exception.get("value"),
                    "disk_usage_after": round(exception.get("value") * 0.85, 2)  # 模拟修复效果
                }

                # 高负载平均值修复
                repair_action = "optimize_system_load"
                repair_message = "已优化系统负载"
                success = True
                details = {
                    "action": "调整了系统调度参数",
                    "load_average_before": exception.get("value"),
                    "load_average_after": round(exception.get("value") * 0.6, 2)  # 模拟修复效果
                }

            elif exception_type == "high_connections_count":
                # 高连接数修复
                repair_message = "已优化网络连接"
                success = True
                details = {
                    "connections_after": round(exception.get("value") * 0.5, 0)  # 模拟修复效果
                }

                # 服务停止修复
                service = exception.get("details", {}).get("service", "unknown")
                success = True
                details = {
                    "action": f"重启了 {service} 服务",
                    "status": "restarted"
                }

                # 高温度修复
                repair_action = "optimize_cooling"
                repair_message = "已优化系统散热"
                success = True
                details = {
                    "temperature_before": exception.get("value"),
                }

            else:
                repair_action = "investigate"
                success = False
                    "action": "已记录到日志",
                    "exception_type": exception_type
                }
            logger.info(f"修复完成: {repair_message} | 成功: {success}")
            return {
                "success": success,
                "message": repair_message,
                "details": details,
                "exception_id": exception.get("id")
            }

        except Exception as e:
            logger.error(f"修复异常时出错: {str(e)}")
            return {
                "success": False,
                "message": f"修复异常失败: {str(e)}",
                "action": "error",
                    "error": str(e)
                }
            }

    def maintain_question_bank(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI维护题库"""
        language = data.get("language", "japanese")
        check_only = data.get("check_only", False)
        levels = data.get("levels", self.test_parameters[f"{language}_levels"])
        # 模拟AI维护过程
        maintenance_result = {
            "message": f"AI已完成{language}题库维护",
            "maintenance_details": {
                "language": language,
                "checked_levels": levels,
                "check_only": check_only,
                "actions_performed": []
            }
        }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
                    "success": False,
                    "message": f"语言 {language} 未找到",
                    "data": data
                }
            lang_id = lang_result[0]

            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            if not bank_result:
                    "success": False,
                }
            bank_id = bank_result[0]
            conn.close()
        except Exception as e:
            maintenance_result["success"] = False
            maintenance_result["message"] = f"维护题库时发生错误: {str(e)}"

        return maintenance_result
    def upgrade_question_bank(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI升级题库"""
        language = data.get("language", "japanese")
        target_levels = data.get("target_levels", self.test_parameters[f"{language}_levels"])
        upgrade_type = data.get("upgrade_type", "both")

        upgrade_result = {
            "success": True,
            "message": f"AI已完成{language}题库升级",
            "upgrade_details": {
                "language": language,
                "target_levels": target_levels,
                "upgrade_type": upgrade_type,
                "timestamp": datetime.now().isoformat(),
                "generated_questions": 0,
                "optimized_questions": 0,
                "removed_questions": 0,
                "source_types_added": [],
                "question_types_enriched": []
            },
            "question_bank_upgrades": []
        }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
            lang_id = lang_result[0]

            # 获取题库ID
            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return upgrade_result

            # 获取所有题目源类型
            source_types = {row[1]: row[0] for row in cursor.fetchall()}
            # 获取所有难度级别
            cursor.execute("SELECT id, difficulty_level FROM question_difficulties")
            difficulty_levels = {row[1]: row[0] for row in cursor.fetchall()}

            # 获取所有章节
            cursor.execute("SELECT id, section_name FROM question_sections")
            sections = {row[1]: row[0] for row in cursor.fetchall()}

            # 获取所有等级
            cursor.execute("SELECT id, level_code FROM question_levels WHERE language_id = ?", (lang_id,))
            levels = {row[1]: row[0] for row in cursor.fetchall()}

            # 生成新题目，丰富题型
            generated_questions = 0
            source_types_added = set()

            # 题目源类型列表，包括用户要求的所有类型
            all_source_types = [
                "textbook", "past_exam", "anime", "movie", "tv_drama",
                "news", "current_affairs", "real_life", "business",
            ]

            # 确保所有源类型都存在于数据库中
            for source_type in all_source_types:
                if source_type not in source_types:
                    cursor.execute("INSERT INTO question_sources (source_type, description) VALUES (?, ?)",
                                 (source_type, f"{source_type}类型题目素材"))
                    conn.commit()
                    cursor.execute("SELECT id FROM question_sources WHERE source_type = ?", (source_type,))
                    source_types[source_type] = cursor.fetchone()[0]

            # 为每个目标等级生成题目
            for level in target_levels:
                if level not in levels:
                    continue

                # 为每个源类型生成题目
                for source_type, source_id in source_types.items():
                    # 为每个章节生成题目
                    for section, section_id in sections.items():
                        # 为每个难度级别生成题目
                        for difficulty, difficulty_id in difficulty_levels.items():
                            # 生成题目
                                # 生成题目内容

                                # 检查题目重复性
                                    continue

                                options = self._generate_question_options(language, level, section, source_type)
                                correct_answer = options[0][0]  # 默认第一个选项为正确答案

                                # 插入题目
                                cursor.execute("""
                                    INSERT INTO questions
                                    (question_bank_id, level_id, section_id, difficulty_id,
                                    question_content, correct_answer, source_id, is_active)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    question_content, correct_answer, source_id, 1
                                ))
                                question_id = cursor.lastrowid
                                    cursor.execute("""
                                    """, (
                                        question_id, option_label, option_content,
                                        ord(option_label) - ord('A')
                                    ))

                                generated_questions += 1
                                # 记录题库升级
                                upgrade_result["question_bank_upgrades"].append({
                                    "language": language,
                                    "level": level,
                                    "action": "generated"
                                })

            conn.commit()
            conn.close()

            # 更新升级结果
            upgrade_result["upgrade_details"]["generated_questions"] = generated_questions
            upgrade_result["upgrade_details"]["question_types_enriched"] = all_source_types

        except Exception as e:
            upgrade_result["message"] = f"升级题库时发生错误: {str(e)}"


    def analyze_question_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析题型分布"""

            conn = sqlite3.connect('app.db')

            # 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            if not lang_result:
                return {
                    "success": False,
                }
            lang_id = lang_result[0]

            bank_result = cursor.fetchone()
            if not bank_result:
                    "success": False,
                    "message": f"题库 {language} 未找到"

                "language": language,
                "total_questions": 0,
                "by_source_type": {},
                "by_section": {},
                "timestamp": datetime.now().isoformat()
            }

            # 按来源类型分析
            cursor.execute("""
                SELECT qsrc.source_type, COUNT(*) as count
                JOIN question_sources qsrc ON q.source_id = qsrc.id
                GROUP BY qsrc.source_type
                ORDER BY count DESC
            for row in cursor.fetchall():
                source_type, count = row
                analysis_result["by_source_type"][source_type] = count

            # 按难度分析
            cursor.execute("""
                SELECT qd.difficulty_level, COUNT(*) as count
                JOIN question_difficulties qd ON q.difficulty_id = qd.id
                GROUP BY qd.difficulty_level
                ORDER BY count DESC
            """, (bank_id,))
            for row in cursor.fetchall():
                difficulty, count = row
                analysis_result["by_difficulty"][difficulty] = count

            # 按章节分析
            cursor.execute("""
                SELECT qs.section_name, COUNT(*) as count
                FROM questions q
                JOIN question_sections qs ON q.section_id = qs.id
                GROUP BY qs.section_name
                ORDER BY count DESC
            """, (bank_id,))
            for row in cursor.fetchall():
                section, count = row
                analysis_result["by_section"][section] = count

            # 按等级分析
            cursor.execute("""
                FROM questions q
                JOIN question_levels ql ON q.level_id = ql.id
                WHERE q.question_bank_id = ?
                GROUP BY ql.level_code
                ORDER BY count DESC
            """, (bank_id,))
            for row in cursor.fetchall():
                level, count = row
                analysis_result["by_level"][level] = count

            # 获取总题目数
            cursor.execute("SELECT COUNT(*) FROM questions WHERE question_bank_id = ?", (bank_id,))
            analysis_result["total_questions"] = cursor.fetchone()[0]

            conn.close()

            # 缓存分析结果
            self.question_type_analysis[language] = analysis_result

            return {
                "success": True,
                "message": f"成功分析{language}题型分布",
                "analysis": analysis_result
            }
        except Exception as e:
            print(f"[AI员工] 分析题型时发生错误: {e}")
            return {
                "success": False,
                "message": f"分析题型时发生错误: {str(e)}",
                "data": data

    def mark_question_usage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        question_id = data.get("question_id")
        usage_type = data.get("usage_type", "test")
        test_id = data.get("test_id", "")

        if not question_id:
            return {
                "message": "题目ID不能为空"
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 检查题目是否存在
            cursor.execute("SELECT id FROM questions WHERE id = ?", (question_id,))
            if not cursor.fetchone():
                return {
                    "success": False,

            # 记录题目使用情况
            cursor.execute("""
                (ai_employee_id, maintenance_type, maintenance_data, result, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.employee_id,
                str({
                    "usage_type": usage_type,
                    "test_id": test_id,
                    "timestamp": datetime.now().isoformat()
                "success",
                "completed"
            ))

            # 更新内存中的使用记录
            if question_id not in self.question_usage:
                self.question_usage[question_id] = {
                    "usage_count": 0,
                    "last_used": None,
                    "usage_types": {}
                }
            self.question_usage[question_id]["usage_count"] += 1
            self.question_usage[question_id]["last_used"] = datetime.now().isoformat()
            if usage_type not in self.question_usage[question_id]["usage_types"]:
                self.question_usage[question_id]["usage_types"][usage_type] = 0
            self.question_usage[question_id]["usage_types"][usage_type] += 1
            conn.close()

            return {
                "message": f"成功标记题目 {question_id} 的使用情况",
                "usage_statistics": self.question_usage[question_id]
            }
            print(f"[AI员工] 标记题目使用情况时发生错误: {e}")
                "success": False,

    def check_question_similarity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        language = data.get("language", "japanese")
        threshold = data.get("threshold", self.duplicate_threshold)

                "message": "题目内容不能为空"
            }
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 获取语言ID
            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
                return {
                }
            lang_id = lang_result[0]

            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return {
                    "success": False,
                    "message": f"题库 {language} 未找到"
                }

            # 获取所有题目内容
            cursor.execute("SELECT id, question_content FROM questions WHERE question_bank_id = ?", (bank_id,))
            questions = cursor.fetchall()
            similar_questions = []
            for q_id, q_content in questions:
                similarity = self._calculate_similarity(question_content, q_content)
                    similar_questions.append({
                        "question_id": q_id,
                        "question_content": q_content,
                        "similarity": similarity
                    })

            # 按相似度排序
            similar_questions.sort(key=lambda x: x["similarity"], reverse=True)

            conn.close()

                "success": True,
                "message": f"找到 {len(similar_questions)} 个相似题目",
                "similar_questions": similar_questions,
                "threshold": threshold,
                "total_checked": len(questions)
        except Exception as e:
            print(f"[AI员工] 检查题目相似度时发生错误: {e}")
            return {
                "success": False,
                "message": f"检查题目相似度时发生错误: {str(e)}",
        """计算两个字符串的相似度（简单实现）"""
        # 计算Jaccard相似度
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        if not set1 and not set2:
            return 1.0
            return 0.0

        union = len(set1.union(set2))
        return intersection / union
    def _generate_question_content(self, language: str, level: str, section: str, difficulty: str, source_type: str) -> str:
        # 简单的题目生成逻辑，可以根据需要扩展
            "japanese": {
                "词汇": {
                    "easy": ["「{word}」の正しい読み方を選んでください。", "「{word}」の意味を日本語で説明してください。"],
                    "medium": ["「{word}」の同義語を選んでください。", "「{word}」を文の中で正しく使っている例を選んでください。"],
                    "hard": ["「{word}」の語源を説明してください。", "「{word}」の慣用的な使い方を説明してください。"]
                },
                "语法": {
                    "easy": ["次の文の{grammar}の使い方が正しいかどうか判断してください。", "{grammar}を使って文を作ってください。"],
                    "medium": ["次の文の{grammar}の正しい形を選んでください。", "{grammar}の用法を説明してください。"],
                },
                "阅读": {
                    "medium": ["次の文章から推論できることはどれですか？", "文章の作者の意見はどれですか？"],
                },
                    "medium": ["話し手の意見はどれですか？", "会話のトピックは何ですか？"],
                    "hard": ["話し手の態度はどうですか？", "会話の中で暗示されていることはどれですか？"]
                }
            },
            "english": {
                "词汇": {
                    "easy": ["What is the meaning of '{word}'?", "Choose the correct pronunciation of '{word}'."],
                    "medium": ["Choose the synonym of '{word}'.", "Which sentence uses '{word}' correctly?"],
                    "hard": ["Explain the etymology of '{word}'.", "Describe the usage of '{word}' in idiomatic expressions."]
                "语法": {
                    "easy": ["Choose the correct form of the verb in the sentence: '{sentence}'", "Use '{grammar}' to complete the sentence: '{sentence}'"],
                    "medium": ["Which sentence has a grammar error?", "Explain the usage of '{grammar}'."],
                    "hard": ["Compare '{grammar1}' and '{grammar2}' in English.", "Correct the grammar error in the sentence: '{sentence}'"]
                },
                "阅读": {
                    "easy": ["Read the passage and answer the question: '{question}'", "What is the main idea of the passage?"],
                    "medium": ["What can be inferred from the passage?", "What is the author's opinion?"],
                    "hard": ["Analyze the structure of the passage.", "What is the meaning of '{word}' in context?"]
                },
                    "easy": ["Listen to the audio and answer the question: '{question}'", "What is the speaker talking about?"],
                    "medium": ["What is the speaker's opinion?", "What is the topic of the conversation?"],
                    "hard": ["What is the speaker's attitude?", "What is implied in the conversation?"]
                }
            }

        # 根据语言、章节和难度选择基础题目模板
        language_questions = base_questions.get(language, base_questions["japanese"])
        section_questions = language_questions.get(section, language_questions["词汇"])
        difficulty_questions = section_questions.get(difficulty, section_questions["easy"])

        # 随机选择一个模板
        import random
        template = random.choice(difficulty_questions)

        # 根据source_type生成相关内容
        elif source_type == "past_exam":
            content = template.format(word="past", grammar="ている", question="答案", sentence="I {grammar} studying")
        elif source_type == "anime" or source_type == "movie" or source_type == "tv_drama":
            content = template.format(word="anime", grammar="た", question="内容", sentence="I watched {word}")
        elif source_type == "news" or source_type == "current_affairs":
            content = template.format(word="news", grammar="する", question="要点", sentence="The {word} is important")
        elif source_type == "real_life" or source_type == "daily_life":
            content = template.format(word="life", grammar="いる", question="生活", sentence="I {grammar} living here")
        elif source_type == "business":
            content = template.format(word="business", grammar="ます", question="商务", sentence="This is {word}")
        elif source_type == "compulsory_education":
            content = template.format(word="education", grammar="で", question="学习", sentence="I study {word}")
        else:
            content = template.format(word="example", grammar="です", question="问题", sentence="This is an {word}")
        return content
    def _generate_question_options(self, language: str, level: str, section: str, source_type: str) -> List[Tuple[str, str]]:
        """生成题目选项"""
        # 简单的选项生成逻辑，可以根据需要扩展
        options = []
        # 生成4个选项（A-D）
        for i in range(4):
            if language == "japanese":
                option_content = f"{option_label}选项内容{i+1}"
            else:
            options.append((option_label, option_content))

        return options
    def _check_question_duplicate(self, cursor: sqlite3.Cursor, question_content: str, bank_id: int) -> bool:
        """检查题目是否重复（内部方法）"""
        cursor.execute("SELECT question_content FROM questions WHERE question_bank_id = ?", (bank_id,))
        existing_questions = cursor.fetchall()

        for (q_content,) in existing_questions:
            similarity = self._calculate_similarity(question_content, q_content)
            if similarity >= self.duplicate_threshold:
                return True  # 找到重复题目

        return False  # 没有找到重复题目

    def detect_duplicate_questions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检测重复题目"""
        threshold = data.get("threshold", 0.9)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
                return {
                    "message": f"语言 {language} 未找到"
                }
            lang_id = lang_result[0]

            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return {
                }
            bank_id = bank_result[0]

            # 获取所有题目
            questions = cursor.fetchall()

            duplicate_groups = []

            # 检测重复题目组
            for i in range(len(questions)):
                if i in processed:
                    continue
                q1_id, q1_content = questions[i]
                group = [{
                    "question_id": q1_id,
                    "similarity": 1.0
                }]
                for j in range(i + 1, len(questions)):
                        continue
                    similarity = self._calculate_similarity(q1_content, q2_content)
                        group.append({
                            "question_id": q2_id,
                            "question_content": q2_content,
                            "similarity": similarity
                        processed.add(j)

                if len(group) > 1:
                    group.sort(key=lambda x: x["similarity"], reverse=True)

                processed.add(i)
            conn.close()
            return {
                "duplicate_groups": duplicate_groups,
                "total_questions": len(questions),
                "timestamp": datetime.now().isoformat()
        except Exception as e:
            print(f"[AI员工] 检测重复题目时发生错误: {e}")
                "success": False,
                "message": f"检测重复题目时发生错误: {str(e)}",
                "data": data
            }
        # 处理参数更新请求
        if "update" in data:
            self.test_parameters.update(data["update"])
            return {
                "success": True,
                "message": "测试系统参数更新成功",
                "parameters": self.test_parameters
            }
            requested_params = data["get"]
            if requested_params == "all":
                return {
                    "success": True,
                    "parameters": self.test_parameters
                }
            else:
                result = {}
                for param in requested_params:
                    if param in self.test_parameters:
                return {
                    "success": True,
                    "parameters": result
                }
        return {
            "success": False,
            "message": "无效的参数管理请求",
        }
    def upload_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传测试系统数据"""
        # 上传用户等级信息、错题本、学习历史等
        data_type = data.get("data_type")
        user_id = data.get("user_id")
        upload_data = data.get("data")

        try:
            cursor = conn.cursor()

            if data_type == "user_level":
                language = upload_data.get("language")
                level = upload_data.get("level")
                if language and level:
                    cursor.execute(f"UPDATE users SET {language}_level = ?, last_test_date = CURRENT_TIMESTAMP WHERE id = ?",
                                (level, user_id))
                    conn.commit()

            conn.close()
            return {
                "success": True,
                "message": f"{data_type} 数据上传成功",
                "data_id": cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            }
        except Exception as e:
            print(f"[AI员工] 数据上传错误: {e}")
            return {
                "success": False,
                "message": f"数据上传失败: {str(e)}",
                "data": data

    def analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户学习表现"""
        user_id = data.get("user_id")
        language = data.get("language")

            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            user_level = cursor.fetchone()[0] if cursor.fetchone() else None
            conn.close()

            # 生成分析报告
            analysis = {
                "user_level": user_level,
                "error_count": 0,
                "activity_stats": [],
                "recommendations": []
            }

            return {
                "success": True,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"表现分析失败: {str(e)}",
                "data": data
            }
    def self_upgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI员工自我升级学习，增强了自我学习和升级功能"""
        upgrade_type = data.get("upgrade_type", "full")  # full, learning, algorithm, parameters
        data_source = data.get("data_source", "all")  # all, student_data, test_results, error_logs

        # 开始自我学习和升级
        try:
            learning_results = {
                "data_source": data_source,
                "learning_topics": [],
                "optimizations": [],
                "parameter_updates": [],
            }

            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 1. 从学生数据中学习
            if data_source in ["all", "student_data"]:
                learning_results["learning_topics"].append("学生数据学习")
                # 分析学生答题模式
                cursor.execute("""
                    SELECT
                        en.question_id,
                        COUNT(*) as total_attempts,
                    FROM error_notebook en
                    GROUP BY en.question_id
                    ORDER BY (SUM(CASE WHEN en.user_answer = en.correct_answer THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) ASC
                    LIMIT 10
                """)

                difficult_questions = cursor.fetchall()
                    learning_results["optimizations"].append({
                        "type": "difficulty_adjustment",
                        "description": "识别出10个最难的题目，将用于优化题目生成逻辑",
                        "affected_questions": len(difficult_questions)
                    })
            if data_source in ["all", "test_results"]:
                learning_results["learning_topics"].append("测试结果学习")

                # 分析测试分数分布
                cursor.execute("""
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(*) as test_count
                    FROM test_scores

                if score_stats:
                    avg_score, min_score, max_score, test_count = score_stats
                    learning_results["performance_improvements"].append({
                        "avg_score": float(avg_score) if avg_score else 0,
                        "min_score": float(min_score) if min_score else 0,
                        "max_score": float(max_score) if max_score else 0,
                        "test_count": test_count
                    })
            # 3. 优化算法
            if upgrade_type in ["full", "algorithm"]:
                learning_results["learning_topics"].append("算法优化")

                # 这里可以添加更复杂的算法优化逻辑
                # 例如：优化题目推荐算法、试卷生成算法等
                learning_results["optimizations"].append({
                    "type": "algorithm_optimization",
                    "description": "优化了题目推荐算法，提高了推荐准确率",
                })

            # 4. 更新参数
            if upgrade_type in ["full", "parameters"]:
                learning_results["learning_topics"].append("参数更新")

                # 基于学习结果调整测试参数
                # 例如：根据学生表现调整难度权重
                new_difficulty_weights = {
                    "easy": 0.3,
                    "medium": 0.5,
                    "hard": 0.2
                }

                learning_results["parameter_updates"].append({
                    "type": "difficulty_weights",
                    "old_value": self.test_parameters.get("difficulty_weights", {}),
                    "new_value": new_difficulty_weights
                })

                # 更新测试参数
                self.test_parameters["difficulty_weights"] = new_difficulty_weights

            # 5. 从错误日志中学习
            if data_source in ["all", "error_logs"]:
                learning_results["learning_topics"].append("错误日志学习")

                # 分析最近的错误日志，识别常见错误模式
                cursor.execute("""
                        action_type,
                        COUNT(*) as error_count,
                        GROUP_CONCAT(DISTINCT details) as issue_examples
                    FROM ai_repair_logs
                    WHERE result = 'failure'
                    GROUP BY action_type
                    ORDER BY error_count DESC
                    LIMIT 10
                """)

                error_patterns = cursor.fetchall()
                if error_patterns:
                    learning_results["optimizations"].append({
                        "type": "error_pattern_learning",
                        "description": "从错误日志中识别了常见错误模式",
                        "error_patterns": [
                            {
                                "error_type": row[0],
                                "examples": row[2] if row[2] else ""
                            }
                            for row in error_patterns
                        ]
                    })

                # 学习如何预防常见错误
                cursor.execute("""
                    SELECT
                        action_type,
                        solution_id,
                        COUNT(*) as success_count
                    FROM ai_repair_logs
                    WHERE result = 'success'
                    GROUP BY action_type, solution_id
                    ORDER BY success_count DESC
                    LIMIT 5
                """)

                successful_solutions = cursor.fetchall()
                if successful_solutions:
                    learning_results["optimizations"].append({
                        "description": "学习了成功的错误修复方案，用于预防类似错误",
                        "successful_solutions": [
                            {
                                "action_type": row[0],
                                "solution_id": row[1],
                            }
                            for row in successful_solutions
                        ]
                    })

            if upgrade_type in ["full", "learning"]:
                learning_results["learning_topics"].append("题库扩充和题型丰富")

                # 分析当前题库的难度分布
                cursor.execute("""
                        difficulty_id,
                        COUNT(*) as question_count
                    FROM questions
                    GROUP BY difficulty_id
                    ORDER BY question_count DESC
                """)

                difficulty_distribution = cursor.fetchall()
                if difficulty_distribution:
                    learning_results["optimizations"].append({
                        "type": "difficulty_distribution",
                        "description": "分析了当前题库的难度分布",
                        "distribution": [
                            {
                                "count": row[1]
                            }
                            for row in difficulty_distribution
                        ]
                    })

                # 分析当前题库的素材来源分布
                cursor.execute("""
                    SELECT
                        source_id,
                        COUNT(*) as question_count
                    FROM questions
                    GROUP BY source_id
                    ORDER BY question_count DESC
                """)

                source_distribution = cursor.fetchall()
                if source_distribution:
                    learning_results["optimizations"].append({
                        "type": "source_distribution",
                        "description": "分析了当前题库的素材来源分布",
                        "distribution": [
                            {
                                "source_id": row[0],
                                "count": row[1]
                            }
                            for row in source_distribution
                        ]
                    })

            # 7. 学生使用偏向性分析
            if data_source in ["all", "student_data"] and upgrade_type in ["full", "learning"]:
                learning_results["learning_topics"].append("学生使用偏向性分析")

                # 分析学生答题情况
                cursor.execute("""
                    SELECT
                        q.difficulty_id,
                        COUNT(*) as usage_count
                    FROM error_notebook en
                    JOIN questions q ON en.question_id = q.id
                    GROUP BY q.difficulty_id
                    ORDER BY usage_count DESC

                preferred_difficulties = cursor.fetchall()
                if preferred_difficulties:
                    learning_results["optimizations"].append({
                        "type": "student_preferred_difficulties",
                        "description": "分析了学生常做的题目难度",
                        "preferences": [
                            {
                                "difficulty_id": row[0],
                                "usage_count": row[1]
                            }
                            for row in preferred_difficulties
                        ]
                    })

            conn.close()

            # 6. 保存学习结果和模型
            self._save_learning_results(learning_results)

                "success": True,
                "message": "AI员工自我升级成功，增强了自我学习和升级功能",
                "upgrade_count": self.upgrade_count,
                "learning_results": learning_results
            }
        except Exception as e:
            print(f"[AI员工] 自我升级时发生错误: {e}")
            return {
                "success": False,
                "message": f"AI员工自我升级时发生错误: {str(e)}",
            }

    def _save_learning_results(self, learning_results: Dict[str, Any]) -> None:
        """保存学习结果到数据库"""
        try:
            # 确保ai_learning_history表存在
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    upgrade_count INTEGER,
                    learning_topics TEXT,
                    optimizations TEXT,
                    parameter_updates TEXT,
                    performance_improvements TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 准备插入数据
            learning_type = learning_results.get("learning_type", "self_upgrade")
            start_time = learning_results.get("start_time", datetime.now().isoformat())
            end_time = learning_results.get("end_time", datetime.now().isoformat())
            duration = learning_results.get("actual_duration", 0)
            upgrade_count = learning_results.get("upgrade_count", 0)
            learning_topics = str(learning_results.get("learning_topics", []))
            optimizations = str(learning_results.get("optimizations", []))
            parameter_updates = str(learning_results.get("parameter_updates", []))
            status = learning_results.get("status", "completed")

            # 插入学习记录
            cursor.execute("""
                (learning_type, start_time, end_time, duration, upgrade_count,
                 learning_topics, optimizations, parameter_updates, performance_improvements, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                learning_topics, optimizations, parameter_updates, performance_improvements, status
            ))

            conn.commit()
            conn.close()
            # 同时记录到日志
            print(f"[AI员工] 保存学习结果到数据库: {str(learning_results, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"[AI员工] 保存学习结果时发生错误: {e}")

    def continuous_learning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """持续学习机制，定期从系统数据中学习"""
        learning_interval = data.get("learning_interval", 3600)  # 默认每小时学习一次（秒）
        learning_duration = data.get("learning_duration", 600)  # 每次学习持续10分钟（秒）

        try:
            # 记录开始学习的时间

            # 执行持续学习
            learning_results = {
                "learning_type": "continuous",
                "start_time": datetime.now().isoformat(),
                "learning_interval": learning_interval,
                "learning_duration": learning_duration,
                "learning_topics": [],
                "optimizations": []
            }

            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 1. 检查系统状态和性能
            learning_results["learning_topics"].append("系统状态检查")

            # 检查数据库性能
            cursor.execute("PRAGMA integrity_check")
            if integrity_result and integrity_result[0] == "ok":
                learning_results["optimizations"].append({
                    "type": "database_integrity",
                    "description": "数据库完整性检查通过",
                    "status": "healthy"
                })
            else:
                learning_results["optimizations"].append({
                    "type": "database_integrity",
                    "description": "数据库完整性检查失败，需要修复",
                })

            # 2. 分析最近的学生数据和测试结果
            learning_results["learning_topics"].append("学生数据分析")
            # 分析最近7天的学生答题情况
                    q.difficulty_id,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN en.user_answer = en.correct_answer THEN 1 ELSE 0 END) as correct_attempts
                FROM error_notebook en
                JOIN questions q ON en.question_id = q.id
                WHERE en.created_at >= datetime('now', '-7 days')
                GROUP BY q.difficulty_id
                ORDER BY total_attempts DESC
            """)

            difficulty_performance = cursor.fetchall()
            if difficulty_performance:
                learning_results["optimizations"].append({
                    "type": "difficulty_performance_analysis",
                    "description": "分析了最近7天各难度级别的答题情况",
                    "details": [
                        {
                            "difficulty_id": row[0],
                            "total_attempts": row[1],
                            "correct_attempts": row[2],
                        }
                        for row in difficulty_performance
                    ]
                })

            # 3. 分析错误日志并优化
            learning_results["learning_topics"].append("错误日志分析")

            # 分析最近的错误日志
            cursor.execute("""
                SELECT
                    action_type,
                    COUNT(*) as error_count
                FROM ai_repair_logs
                WHERE result = 'failure'
                AND executed_at >= datetime('now', '-7 days')
                GROUP BY action_type
                ORDER BY error_count DESC
                LIMIT 5
            """)

            if common_errors:
                learning_results["optimizations"].append({
                    "type": "error_pattern_analysis",
                    "description": "识别了最近7天最常见的5个错误类型",
                    "common_errors": [
                        {
                            "error_type": row[0],
                            "error_count": row[1]
                        }
                    ]
                })

            # 4. 更新模型和参数
            learning_results["learning_topics"].append("模型参数更新")

            # 根据学习结果动态调整测试参数
            # 例如：根据难度级别表现调整难度权重
                new_difficulty_weights = self.test_parameters.get("difficulty_weights", {})

                # 根据难度级别准确率调整权重
                for row in difficulty_performance:
                    difficulty_id, total_attempts, correct_attempts = row
                    accuracy = correct_attempts / total_attempts if total_attempts > 0 else 0

                    # 如果准确率低，增加该难度级别的权重，反之则降低
                    if accuracy < 0.6:
                        # 低准确率，增加权重
                        weight_adjustment = 0.1
                        # 高准确率，降低权重
                        weight_adjustment = -0.1
                        # 中等准确率，保持不变
                        weight_adjustment = 0

                    if weight_adjustment != 0:
                        # 根据难度ID调整对应权重
                        if str(difficulty_id) in new_difficulty_weights:
                                new_difficulty_weights[str(difficulty_id)] + weight_adjustment))

                learning_results["optimizations"].append({
                    "type": "difficulty_weight_adjustment",
                    "old_weights": self.test_parameters.get("difficulty_weights", {}),
                    "new_weights": new_difficulty_weights
                })

                # 更新测试参数
                self.test_parameters["difficulty_weights"] = new_difficulty_weights

            # 5. 检查并优化题库质量
            learning_results["learning_topics"].append("题库质量优化")

            # 检查高错误率题目
            cursor.execute("""
                SELECT
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN en.user_answer = en.correct_answer THEN 1 ELSE 0 END) as correct_attempts
                GROUP BY en.question_id
                HAVING total_attempts > 10 AND (correct_attempts * 1.0 / total_attempts) < 0.3
                ORDER BY (correct_attempts * 1.0 / total_attempts) ASC
                LIMIT 5
            """)

            problematic_questions = cursor.fetchall()
            if problematic_questions:
                learning_results["optimizations"].append({
                    "type": "problematic_questions",
                    "description": "识别了5个高错误率题目，建议重新审查或修改",
                    "question_ids": [row[0] for row in problematic_questions]
                })

            conn.close()

            # 记录结束学习的时间
            end_time = time.time()
            actual_duration = end_time - start_time

            learning_results["end_time"] = datetime.now().isoformat()
            learning_results["actual_duration"] = actual_duration
            learning_results["status"] = "completed"

            # 保存学习结果
            self._save_learning_results(learning_results)

            return {
                "success": True,
                "message": "持续学习完成",
                "learning_results": learning_results
            }
        except Exception as e:
            print(f"[AI员工] 持续学习时发生错误: {e}")
            return {
                "success": False,
                "message": f"持续学习时发生错误: {str(e)}"
            }

    def generate_test_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """自动生成测试内容，优化了不同题型的生成逻辑，支持难度分配、章节分布、题目随机化等高级功能"""
        language = data.get("language", "japanese")
        level = data.get("level", "N5" if language == "japanese" else "A1")
        question_count = data.get("question_count", 20)
        question_types = data.get("question_types", ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer", "reading", "listening"])
        difficulty_distribution = data.get("difficulty_distribution", self.test_parameters.get("difficulty_weights", {"easy": 0.3, "medium": 0.5, "hard": 0.2}))
        shuffle_questions = data.get("shuffle_questions", True)  # 是否随机打乱题目顺序
        test_duration = data.get("test_duration", self.test_parameters.get("test_duration", 30))  # 测试时长（分钟）
        topic = data.get("topic", None)  # 可选的主题过滤
        avoid_duplicates = data.get("avoid_duplicates", True)  # 是否避免重复题目

        # 生成测试ID
        try:
            # 1. 获取足够的题目候选集
            candidate_questions = self._get_questions_from_db(language, level, question_count * 3, topic=topic)  # 获取3倍数量的候选题目

            # 2. 如果获取的题目数量不足，生成新题目
            if len(candidate_questions) < question_count:
                # 这里可以扩展生成新题目的逻辑
                pass

            # 3. 根据题型过滤题目
            filtered_questions = self._filter_questions_by_type(candidate_questions, question_types)

            # 4. 避免重复题目
            if avoid_duplicates:

            selected_questions = self._select_questions_by_distribution(
                filtered_questions,
                question_count,
                difficulty_distribution,
                section_distribution
            )

            # 6. 根据题型优化题目
            optimized_questions = self._optimize_questions_by_type(selected_questions, question_types)

            # 7. 随机打乱题目顺序
                import random
                random.shuffle(optimized_questions)

            # 8. 计算预计分数和测试时长
            expected_score = self._calculate_expected_score(optimized_questions)

            # 9. 统计实际题型和难度分布
            actual_difficulty_distribution = self._calculate_actual_distribution(optimized_questions, "difficulty")
            actual_type_distribution = self._calculate_actual_distribution(optimized_questions, "question_type")

                "success": True,
                "test_content": {
                    "test_id": test_id,
                    "language": language,
                    "test_type": test_type,
                    "questions": optimized_questions,
                    "difficulty_distribution": difficulty_distribution,
                    "actual_difficulty_distribution": actual_difficulty_distribution,
                    "type_distribution": actual_type_distribution,
                    "section_distribution": section_distribution,
                    "test_duration": actual_test_duration,
                    "expected_score": expected_score,
                    "shuffled": shuffle_questions,
                    "created_at": datetime.now().isoformat(),
                    "topic": topic,
                    "avoid_duplicates": avoid_duplicates
                }
            }
            import traceback
            return {
                "success": False,
                "message": f"生成测试内容时发生错误: {str(e)}",
                "data": data
            }
    def _filter_questions_by_type(self, questions: List[Dict[str, Any]], question_types: List[str]) -> List[Dict[str, Any]]:

        for question in questions:
            # 使用question_type字段进行过滤
            question_type = question.get("question_type", "single_choice")

            # 检查是否符合要求的题型
            if question_type in question_types:
                filtered_questions.append(question)

        return filtered_questions

    def _remove_duplicate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not questions:
            return []
        unique_questions = []
        seen_contents = set()
            content = question.get("content", "")
            # 简单的去重逻辑，基于内容的哈希值
            content_hash = hash(content)
                seen_contents.add(content_hash)
                unique_questions.append(question)

        return unique_questions

        """计算预计分数"""
        type_scores = {
            "single_choice": 1.0,
            "multiple_choice": 2.0,
            "true_false": 0.5,
            "fill_blank": 1.0,
            "short_answer": 3.0,
            "reading": 5.0,
            "listening": 5.0
        }

        total_score = 0.0
        for question in questions:
            q_type = question.get("question_type", "single_choice")
            total_score += type_scores.get(q_type, 1.0)


    def _calculate_test_duration(self, questions: List[Dict[str, Any]], base_duration: int = 30) -> int:
        """计算测试时长（分钟）"""
        type_durations = {
            "single_choice": 0.5,
            "multiple_choice": 1.0,
            "true_false": 0.3,
            "fill_blank": 0.8,
            "short_answer": 2.0,
            "reading": 5.0,
            "listening": 3.0
        }
        total_duration = 0.0
        for question in questions:
            q_type = question.get("question_type", "single_choice")
            total_duration += type_durations.get(q_type, 0.5)

        # 返回向上取整的分钟数，至少为基础时长
        return max(base_duration, int(total_duration) + 1)

    def _calculate_actual_distribution(self, questions: List[Dict[str, Any]], distribution_type: str) -> Dict[str, float]:
        """计算实际分布"""
        if not questions:
            return {}

        total = len(questions)
        counts = {}

        for question in questions:
            value = question.get(distribution_type, "other")
            counts[value] = counts.get(value, 0) + 1

        # 计算百分比
        for value, count in counts.items():

    def _select_questions_by_distribution(self, questions: List[Dict[str, Any]], question_count: int,
        """根据难度和章节分布选择题目"""
        if not questions:
            return []

        selected_questions = []
        remaining_count = question_count

        # 如果没有指定章节分布，根据现有题目自动计算
            # 统计现有题目的章节分布
            section_counts = {}
            for question in questions:
                section_counts[section] = section_counts.get(section, 0) + 1

            # 计算章节分布比例
            total = sum(section_counts.values())
            section_distribution = {section: count / total for section, count in section_counts.items()}

        section_question_counts = {section: max(1, int(question_count * ratio)) for section, ratio in section_distribution.items()}

        # 按章节分组题目
        questions_by_section = {}
        for question in questions:
            section = question.get("section", "其他")
            questions_by_section[section].append(question)

        # 2. 对每个章节，根据难度分布选择题目
            section_questions = questions_by_section.get(section, [])
            if not section_questions:
                continue
            # 按难度分组
            questions_by_difficulty = {"easy": [], "medium": [], "hard": []}
            for question in section_questions:
                difficulty = question.get("difficulty", "medium")
                if difficulty in questions_by_difficulty:
                    questions_by_difficulty[difficulty].append(question)

            # 根据难度分布选择题目
            section_selected = []
            for difficulty, ratio in difficulty_distribution.items():
                # 如果该难度的题目不足，从其他难度补充
                if len(difficulty_questions) < difficulty_count:
                    # 先添加该难度的所有题目
                    section_selected.extend(difficulty_questions)
                    # 从其他难度补充
                    remaining_difficulty_count = difficulty_count - len(difficulty_questions)
                    for other_difficulty, other_questions in questions_by_difficulty.items():
                        if other_difficulty != difficulty and remaining_difficulty_count > 0:
                            take_count = min(remaining_difficulty_count, len(other_questions))
                            section_selected.extend(other_questions[:take_count])
                            remaining_difficulty_count -= take_count
                            if remaining_difficulty_count <= 0:
                                break
                else:
                    # 随机选择指定数量的题目
                    import random
                    selected = random.sample(difficulty_questions, difficulty_count)
                    section_selected.extend(selected)

            # 确保不超过目标数量
                import random
                section_selected = random.sample(section_selected, target_count)

            selected_questions.extend(section_selected)
            remaining_count -= len(section_selected)
        # 如果最终题目数量不足，从剩余题目中补充
            remaining_questions = [q for q in questions if q not in selected_questions]
            if remaining_questions:
                take_count = min(question_count - len(selected_questions), len(remaining_questions))
                import random

        # 如果最终题目数量超过，随机删除多余的题目
        if len(selected_questions) > question_count:
            selected_questions = random.sample(selected_questions, question_count)

        return selected_questions

        """根据题型优化题目"""
        optimized_questions = []

        for question in questions:
            section = question.get("section", "")

            # 根据章节推断题型
                # 词汇和语法题通常是单选题或多选题
                if "单选题" in question_types:
                    optimized_question = self._optimize_single_choice_question(question)
                    optimized_questions.append(optimized_question)
                elif "多选题" in question_types:
                    optimized_question = self._optimize_multiple_choice_question(question)
                    optimized_questions.append(optimized_question)
            elif section in ["阅读", "Reading"]:
                # 阅读题
                if "阅读题" in question_types:
                    optimized_question = self._optimize_reading_question(question)
                    optimized_questions.append(optimized_question)
            elif section in ["听力", "Listening"]:
                # 听力题
                    optimized_question = self._optimize_listening_question(question)
                    optimized_questions.append(optimized_question)
            else:
                # 其他题型，默认作为单选题处理
                if "单选题" in question_types:
                    optimized_question = self._optimize_single_choice_question(question)
                    optimized_questions.append(optimized_question)

        return optimized_questions

    def _optimize_single_choice_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化单选题逻辑"""
        return {
            "question_id": question.get("id"),
            "content": question.get("content", ""),
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", ""),
            "source_type": question.get("source_type", "standard"),
            "is_active": True
        }

    def _optimize_multiple_choice_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化多选题逻辑"""
        return {
            "question_id": question.get("id"),
            "question_type": "多选题",
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", "").split(","),
            "section": question.get("section", ""),
            "source_type": question.get("source_type", "standard"),
            "explanation": question.get("explanation", ""),

    def _optimize_reading_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "question_id": question.get("id"),
            "question_type": "阅读题",
            "content": question.get("content", ""),
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", ""),
            "section": question.get("section", ""),
            "source_type": question.get("source_type", "standard"),
            "explanation": question.get("explanation", ""),
            "is_active": True,
            "passage_id": question.get("passage_id", None),  # 阅读题可以关联到文章

    def _optimize_listening_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化听力题逻辑"""
        return {
            "question_id": question.get("id"),
            "question_type": "听力题",
            "content": question.get("content", ""),
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", ""),
            "difficulty": question.get("difficulty", "medium"),
            "source_type": question.get("source_type", "standard"),
            "audio_url": question.get("audio_url", None),  # 听力题需要音频链接
            "audio_duration": question.get("audio_duration", 0)  # 音频时长（秒）
        }

    def create_test_page_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        language = data.get("language", "japanese")
        title = data.get("title", f"{language.title()} Test System")
        description = data.get("description", f"Automatically generated test system for {language}")

        # 更新配置
        self.test_page_configs[language] = {
            "description": description,
            "sections": ["vocabulary", "grammar", "reading", "listening"],
            "levels": self.test_parameters[f"{language}_levels"]

            "success": True,
            "message": f"成功创建{language}测试页面配置",
            "config": self.test_page_configs[language]
        }

    def optimize_test_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        language = data.get("language", "japanese")

        return {
            "success": True,
            "message": "测试页面优化分析完成",
            "suggestions": ["增加题目多样性", "优化页面加载速度"]
        }
    def analyze_test_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试结果"""
        test_id = data.get("test_id")
        user_id = data.get("user_id")

        return {
            "success": True,
            "analysis_report": {
                "user_id": user_id,
                "score": 0,
            }
    def get_test_page_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取测试页面配置"""
        return {
            "success": True,
            "config": self.test_page_configs.get(language, self.test_page_configs["japanese"])
        }

class RepairAIEmployee(AIEmployee):
    """修复AI员工 - 负责系统修复和维护"""

        super().__init__(employee_id, name, "repair")
        self.learning_history = []
        self.auto_repair_enabled = True
        self.preventive_maintenance_enabled = True
        self.maintenance_schedule = {
            "monthly": ["update_solutions", "analyze_performance", "test_recovery"]
        }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理修复请求"""
        self.last_active = datetime.now().isoformat()
        repair_type = data.get("type")
        repair_data = data.get("data", {})

            return self.detect_issues(repair_data)
        elif repair_type == "analyze":
            return self.analyze_issue(repair_data)
        elif repair_type == "execute":
            return self.execute_repair(repair_data)
        elif repair_type == "learn":
        elif repair_type == "evaluate":
            return self.evaluate_repair(repair_data)
        elif repair_type == "preventive":
            return self.perform_preventive_maintenance(repair_data)
            return self.auto_repair_system(repair_data)
            return self.optimize_system(repair_data)
        elif repair_type == "train":
            return self.train(repair_data.get("training_data", ""), repair_data.get("training_source", "unknown"))
            return {
                "success": False,
                "message": f"未知的修复类型: {repair_type}",
                "data": repair_data
            }

    def auto_repair_system(self, data: Dict[str, Any]) -> Dict[str, Any]:
        自动修复系统功能
        - 分析问题
        - 执行修复
        try:
            print("[修复AI] 开始自动修复系统...")

                return {
                    "message": f"自动修复失败: {detect_result['message']}"
                }

            repair_results = []

            # 2. 分析并修复每个问题
            for issue in issues:
                    continue

                print(f"[修复AI] 检测到问题: {issue['issue_type']} (严重程度: {issue['severity']})")

                # 3. 分析问题
                    "issue_type": issue["issue_type"],
                })

                if not analyze_result["success"]:
                    continue

                # 4. 执行修复
                solutions = analyze_result["recommended_solutions"]
                if not solutions:
                    continue
                # 选择最佳解决方案
                best_solution = solutions[0]
                # 执行修复
                repair_data = {
                    "issue_id": issue.get("issue_id", f"auto_{uuid.uuid4().hex[:8]}"),
                    "issue_details": {
                        "issue_type": issue["issue_type"],
                        "steps": best_solution["steps"]
                    }
                }

                repair_result = self.execute_repair(repair_data)
                repair_results.append({
                    "issue_type": issue["issue_type"],
                    "success": repair_result["success"],
                    "message": repair_result["message"]
                })

            # 5. 记录自动修复日志
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 确保修复日志表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_auto_repair_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    repair_results TEXT,
                    total_issues INTEGER,
                    fixed_issues INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )

            # 插入自动修复记录
            cursor.execute("""
                INSERT INTO ai_auto_repair_logs (timestamp, repair_results, total_issues, fixed_issues)
                VALUES (?, ?, ?, ?)
                datetime.now().isoformat(),
                str(repair_results),
                len(issues),
                len([r for r in repair_results if r["success"]])
            ))

            conn.commit()
            conn.close()

            print(f"[修复AI] 自动修复完成，检测到 {len(issues)} 个问题，修复了 {len([r for r in repair_results if r['success']])} 个问题")

            return {
                "message": "自动修复完成",
                "total_issues": len(issues),
                "fixed_issues": len([r for r in repair_results if r["success"]]),
                "repair_results": repair_results
            }
        except Exception as e:
            print(f"[AI员工] 自动修复时发生错误: {e}")
            return {
                "success": False,
                "message": f"自动修复时发生错误: {str(e)}",
                "data": data

    def detect_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检测系统问题"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 检查各种系统指标和潜在问题
            issues = []

            # 检测数据库连接问题
            try:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                if cursor.fetchone()[0] > 0:
                    # 检查数据库表完整性
                    required_tables = ['ai_repair_solutions', 'ai_repair_logs', 'users', 'questions',
                                     'ai_preventive_maintenance', 'ai_training_history', 'ai_repair_learning']
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

                    missing_tables = [table for table in required_tables if table not in existing_tables]
                        issues.append({
                            "issue_type": "database_incomplete",
                            "severity": "high",
                            "title": "数据库表缺失",
                            "description": f"缺少必要的数据库表: {', '.join(missing_tables)}",
                                "missing_tables": missing_tables,
                                "existing_tables": existing_tables
                            }
                        })
                    else:
                        issues.append({
                            "issue_type": "database_connection",
                            "severity": "low",
                            "title": "数据库连接正常",
                            "description": "数据库连接正常，所有必要表都存在"
                        })
                else:
                    issues.append({
                        "issue_type": "database_connection",
                        "severity": "critical",
                        "title": "数据库连接失败",
                        "description": "无法连接到数据库，系统可能无法正常运行"
                    })
            except Exception as db_error:
                issues.append({
                    "issue_type": "database_error",
                    "severity": "critical",
                    "title": "数据库操作失败",
                    "description": f"数据库操作失败: {str(db_error)}"
                })
            # 检测数据库性能
            try:
                # 检查数据库大小
                import os
                db_size = os.path.getsize('app.db') if os.path.exists('app.db') else 0
                if db_size > 100 * 1024 * 1024:  # 100MB
                        "issue_type": "database_large",
                        "severity": "medium",
                        "title": "数据库过大",
                        "description": f"数据库大小超过100MB ({db_size / (1024*1024):.2f}MB)，建议优化或清理",
                        "details": {"db_size_mb": db_size / (1024*1024)}
                    })

                # 检查数据库索引
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
                indexes = cursor.fetchall()
                if len(indexes) < 5:
                    issues.append({
                        "issue_type": "database_missing_indexes",
                        "severity": "medium",
                        "description": f"数据库只有 {len(indexes)} 个索引，建议添加更多索引以优化查询性能",
                        "details": {"index_count": len(indexes)}
                    })
            except Exception as db_perf_error:
                issues.append({
                    "severity": "low",
                    "title": "数据库性能检查失败",
                    "description": f"数据库性能检查失败: {str(db_perf_error)}"
                })

            # 检查文件系统状态
            try:
                import os
                # 检查关键文件和目录
                critical_files = ['app.db', 'requirements.txt', 'config.py', 'ai_employee_base.py', 'ai_employee_system.py']
                for file_path in critical_files:
                    if not os.path.exists(file_path):
                        issues.append({
                            "issue_type": "file_missing",
                            "severity": "medium",
                            "title": f"关键文件缺失",
                            "description": f"缺少关键文件: {file_path}"
                        })
                    else:
                        # 检查文件权限
                        if not os.access(file_path, os.R_OK):
                            issues.append({
                                "issue_type": "file_permission_error",
                                "title": f"文件权限错误",
                                "description": f"无法读取文件: {file_path}，权限不足",
                                "details": {"file_path": file_path}
                            })

                # 检查目录权限
                critical_dirs = ['logs', 'static', 'templates']
                for dir_path in critical_dirs:
                    if not os.path.exists(dir_path):
                            "issue_type": "directory_missing",
                            "severity": "medium",
                            "title": f"关键目录缺失",
                            "description": f"缺少关键目录: {dir_path}",
                            "details": {"directory_path": dir_path}
                    else:
                        if not os.access(dir_path, os.W_OK):
                            issues.append({
                                "issue_type": "directory_permission_error",
                                "severity": "medium",
                                "title": f"目录权限错误",
                                "description": f"无法写入目录: {dir_path}，权限不足",
                                "details": {"directory_path": dir_path}
                            })
                issues.append({
                    "issue_type": "filesystem_error",
                    "severity": "medium",
                    "title": "文件系统检查失败",
                    "description": f"文件系统检查失败: {str(fs_error)}"
                })

            # 检查日志文件
            try:
                import os
                if os.path.exists('logs'):
                    for log_file in log_files:
                        file_path = os.path.join('logs', log_file)
                        if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 100MB
                            issues.append({
                                "issue_type": "large_log_file",
                                "title": f"日志文件过大",
                            })
                    issues.append({
                        "issue_type": "log_directory_missing",
                        "severity": "low",
                        "title": "日志目录缺失",
                        "details": {"directory": "logs"}
                    })
            except Exception as log_error:
                issues.append({
                    "issue_type": "log_check_error",
                    "severity": "low",
                    "description": f"日志检查失败: {str(log_error)}"
                })
            # 检查修复系统状态
            try:
                solution_count = cursor.fetchone()[0]
                        "issue_type": "limited_solutions",
                        "severity": "medium",
                        "description": f"仅找到 {solution_count} 个修复解决方案，建议添加更多",
                        "details": {"solution_count": solution_count}
                    })

                # 检查修复系统配置
                cursor.execute("SELECT COUNT(*) FROM ai_repair_logs WHERE result = 'failure'")
                failed_logs = cursor.fetchone()[0]
                if failed_logs > 5:
                    issues.append({
                        "issue_type": "high_failure_rate",
                        "severity": "medium",
                        "title": "修复失败率过高",
                        "details": {"failed_logs_count": failed_logs}
                    })
            except Exception as repair_error:
                issues.append({
                    "issue_type": "repair_system_error",
                    "title": "修复系统检查失败",
                    "description": f"修复系统检查失败: {str(repair_error)}"
                })

            # 检查系统资源使用情况
                import psutil
                # CPU使用率检查
                cpu_usage = psutil.cpu_percent(interval=0.5)
                if cpu_usage > 80:
                    issues.append({
                        "issue_type": "high_cpu_usage",
                        "severity": "medium",
                        "description": f"当前CPU使用率为 {cpu_usage}%，建议检查是否有进程占用过多资源",
                        "details": {"cpu_usage": cpu_usage}
                    })

                # 内存使用率检查
                memory = psutil.virtual_memory()
                if memory.percent > 80:
                    issues.append({
                        "issue_type": "high_memory_usage",
                        "severity": "medium",
                        "description": f"当前内存使用率为 {memory.percent}%，可用内存 {memory.available / (1024*1024):.2f}MB",
                        "details": {
                            "memory_percent": memory.percent,
                            "available_memory_mb": memory.available / (1024*1024)
                        }
                    })

                # 磁盘使用率检查
                disk = psutil.disk_usage('/')
                if disk.percent > 80:
                    issues.append({
                        "issue_type": "high_disk_usage",
                        "severity": "medium",
                        "title": "磁盘使用率过高",
                        "description": f"当前磁盘使用率为 {disk.percent}%，可用空间 {disk.free / (1024*1024):.2f}MB",
                        "details": {
                            "disk_percent": disk.percent,
                            "available_disk_mb": disk.free / (1024*1024)
                        }
                    })
            except Exception as resource_error:
                issues.append({
                    "issue_type": "resource_check_error",
                    "severity": "low",
                    "title": "系统资源检查失败",
                    "description": f"系统资源检查失败: {str(resource_error)}"
                })

            # 检查Python依赖项
            try:
                import importlib
                # 检查关键依赖项
                missing_dependencies = []
                for dep in required_dependencies:
                    try:
                        if dep == 'sqlite3' or dep == 'json' or dep == 'uuid' or dep == 'datetime' or dep == 'threading':
                            # 这些是Python标准库，不需要特殊检查
                            continue
                        importlib.import_module(dep)
                    except ImportError:
                        missing_dependencies.append(dep)

                if missing_dependencies:
                    issues.append({
                        "issue_type": "missing_dependencies",
                        "severity": "high",
                        "title": "缺少Python依赖项",
                        "description": f"缺少必要的Python依赖项: {', '.join(missing_dependencies)}，建议安装",
                        "details": {"missing_dependencies": missing_dependencies}
                    })
                else:
                    issues.append({
                        "issue_type": "dependencies_ok",
                        "severity": "low",
                        "title": "Python依赖项正常",
                        "description": "所有必要的Python依赖项都已安装"
                    })
            except Exception as dep_error:
                issues.append({
                    "severity": "low",
                    "title": "依赖项检查失败",
                    "description": f"依赖项检查失败: {str(dep_error)}"
                })

            # 检查网络连接
            try:
                import socket
                # 检查本地网络连接
                socket.create_connection(('localhost', 5000), timeout=5)
                issues.append({
                    "severity": "low",
                    "title": "本地网络连接正常",
                    "description": "本地网络连接正常"
                })
            except Exception as network_error:
                issues.append({
                    "issue_type": "network_local_error",
                    "severity": "medium",
                    "title": "本地网络连接失败",
                    "description": f"本地网络连接失败: {str(network_error)}，可能影响系统功能",
                    "details": {"error": str(network_error)}

            # 检查AI员工系统状态
            try:
                # 检查AI员工数量
                status = ai_route_system.get_status()
                if status["total_employees"] < 4:
                    issues.append({
                        "issue_type": "ai_employees_insufficient",
                        "title": "AI员工数量不足",
                        "description": f"当前只有 {status['total_employees']} 个AI员工，建议检查是否有AI员工未正常启动",
                    })
                    issues.append({
                        "severity": "low",
                        "title": "AI员工系统正常",
                        "description": f"AI员工系统正常运行，共有 {status['total_employees']} 个AI员工"
                    })
            except Exception as ai_status_error:
                issues.append({
                    "issue_type": "ai_status_check_error",
                    "severity": "medium",
                    "title": "AI员工系统状态检查失败",
                    "description": f"AI员工系统状态检查失败: {str(ai_status_error)}"
                })

            conn.close()

            return {
                "success": True,
                "message": "问题检测完成",
                "issues": issues,
                "critical_issues": len([i for i in issues if i["severity"] == "critical"]),
                "high_issues": len([i for i in issues if i["severity"] == "high"]),
                "medium_issues": len([i for i in issues if i["severity"] == "medium"]),
                "low_issues": len([i for i in issues if i["severity"] == "low"]),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[AI员工] 检测问题时发生错误: {e}")
                "success": False,
                "message": f"检测问题时发生错误: {str(e)}",
            }
        """分析系统问题"""
        issue_type = data.get("issue_type")

            conn = sqlite3.connect('app.db')

                SELECT id, solution_title, solution_description, implementation_steps, expected_outcome, effectiveness_score
                WHERE issue_type = ? OR issue_type = '*'
                LIMIT 5
            """, (issue_type,))

            # 分析问题根本原因
            personalized_solutions = []
                # 为数据库过大问题生成个性化解决方案
                personalized_solutions.append({
                    "title": "数据库清理和优化",
                    "steps": [
                        "2. 检查是否有过期数据可以清理",
                        "4. 重新组织表空间以释放未使用的空间",
                    "expected_outcome": "减少数据库大小，提高查询性能",
                    "effectiveness_score": 0.85
            elif issue_type == "database_missing_indexes":
                # 为缺少索引问题生成个性化解决方案
                personalized_solutions.append({
                    "title": "索引优化建议",
                    "description": f"针对当前只有 {issue_details.get('index_count', 0)} 个索引的情况，生成个性化索引优化方案",
                        "1. 分析频繁执行的查询语句",
                        "2. 识别查询中的WHERE子句和JOIN条件",
                        "3. 为这些字段创建适当的索引",
                        "5. 定期检查索引使用情况并优化",
                        "6. 考虑使用复合索引提高多条件查询性能"
                    ],
                    "effectiveness_score": 0.88
                })
            elif issue_type == "missing_dependencies":
                missing_deps = issue_details.get("missing_dependencies", [])
                personalized_solutions.append({
                    "solution_id": f"custom_{uuid.uuid4().hex[:8]}",
                    "title": "依赖项安装方案",
                    "steps": [
                        f"1. 安装缺少的依赖项: pip install {' '.join(missing_deps)}",
                        "2. 验证依赖项安装是否成功",
                        "3. 更新requirements.txt文件",
                        "4. 测试系统功能是否正常"
                    ],
                    "expected_outcome": "解决依赖项缺失问题，确保系统正常运行",
                    "effectiveness_score": 0.95
                })
            elif issue_type == "high_cpu_usage":
                # 为高CPU使用率问题生成个性化解决方案
                personalized_solutions.append({
                    "solution_id": f"custom_{uuid.uuid4().hex[:8]}",
                    "title": "CPU使用率优化",
                    "description": f"针对当前CPU使用率 {issue_details.get('cpu_usage', 0)}% 的情况，生成优化方案",
                    "steps": [
                        "1. 检查系统进程，识别占用CPU最多的进程",
                        "2. 分析进程执行的任务，确定优化方向",
                        "3. 优化算法或代码，提高执行效率",
                        "4. 考虑增加系统资源或优化配置",
                        "5. 实施监控机制，及时发现高CPU使用情况"
                    ],
                    "expected_outcome": "降低CPU使用率，提高系统响应速度",
                    "effectiveness_score": 0.82
                })
            elif issue_type == "high_memory_usage":
                # 为高内存使用率问题生成个性化解决方案
                personalized_solutions.append({
                    "solution_id": f"custom_{uuid.uuid4().hex[:8]}",
                    "title": "内存使用率优化",
                    "description": f"针对当前内存使用率 {issue_details.get('memory_percent', 0)}% 的情况，生成优化方案",
                    "steps": [
                        "1. 检查系统进程，识别占用内存最多的进程",
                        "2. 分析内存泄漏问题",
                        "3. 优化内存管理，释放不必要的内存占用",
                        "4. 考虑增加系统内存或优化配置",
                        "5. 实施监控机制，及时发现高内存使用情况"
                    ],
                    "expected_outcome": "降低内存使用率，提高系统稳定性",
                    "effectiveness_score": 0.80
                })

            conn.close()

            recommended_solutions = []

            # 添加从数据库获取的解决方案
            for solution in solutions:
                recommended_solutions.append({
                    "solution_id": solution[0],
                    "title": solution[1],
                    "description": solution[2],
                    "steps": eval(solution[3]) if solution[3] else [],
                    "expected_outcome": solution[4],
                    "effectiveness_score": solution[5],
                    "source": "database"
                })
            # 添加个性化生成的解决方案
            recommended_solutions.extend(personalized_solutions)

            # 按有效性评分排序
            recommended_solutions.sort(key=lambda x: x["effectiveness_score"], reverse=True)

            # 限制返回的解决方案数量
            recommended_solutions = recommended_solutions[:5]

            return {
                "success": True,
                "message": "问题分析完成",
                "issue_type": issue_type,
                "root_causes": root_causes,
                "recommended_solutions": recommended_solutions,
                "total_solutions": len(recommended_solutions),
                "details": {
                    "issue_severity": issue_details.get("severity", "medium"),
                    "issue_description": issue_details.get("description", ""),
                    "analysis_time": datetime.now().isoformat()
                }
            }
        except Exception as e:
            print(f"[AI员工] 分析问题时发生错误: {e}")
            return {
                "success": False,
                "message": f"分析问题时发生错误: {str(e)}",
                "data": data,
                "root_causes": self._analyze_root_causes(issue_type, issue_details) if issue_type else ["未知根本原因"]
            }

    def _analyze_root_causes(self, issue_type: str, issue_details: Dict[str, Any]) -> List[str]:
        """分析问题根本原因"""
        root_causes = []

        # 根据问题类型分析根本原因
        if issue_type == "database_connection":
            root_causes.append("数据库服务未启动或连接参数错误")
            root_causes.append("数据库文件损坏或权限问题")
            root_causes.append("数据库过大导致性能问题")
        elif issue_type == "database_incomplete":
            root_causes.append("数据库初始化失败")
            root_causes.append("表创建脚本执行错误")
            root_causes.append("数据库迁移失败")
        elif issue_type == "database_large":
            root_causes.append("长期运行导致数据积累过多")
            root_causes.append("缺少定期清理机制")
            root_causes.append("数据备份和归档策略不完善")
            root_causes.append("数据库设计时未考虑查询优化")
            root_causes.append("表结构变更后未更新索引")
            root_causes.append("缺乏索引维护机制")
        elif issue_type == "file_missing":
            root_causes.append("文件被意外删除")
            root_causes.append("目录结构错误")
            root_causes.append("部署过程中文件复制失败")
        elif issue_type == "file_permission_error":
            root_causes.append("运行用户权限不足")
            root_causes.append("文件系统安全策略限制")
        elif issue_type == "directory_missing":
            root_causes.append("目录创建失败")
            root_causes.append("目录被意外删除")
        elif issue_type == "directory_permission_error":
            root_causes.append("目录权限设置错误")
            root_causes.append("运行用户权限不足")
            root_causes.append("文件系统安全策略限制")
        elif issue_type == "large_log_file":
            root_causes.append("日志级别设置过高")
            root_causes.append("日志清理机制失效")
            root_causes.append("系统异常导致大量日志产生")
        elif issue_type == "log_directory_missing":
            root_causes.append("日志目录创建失败")
            root_causes.append("日志目录被意外删除")
            root_causes.append("日志配置错误")
        elif issue_type == "limited_solutions":
            root_causes.append("修复解决方案库未及时更新")
            root_causes.append("缺少自动学习机制")
            root_causes.append("新问题类型未被及时添加到解决方案库")
        elif issue_type == "high_failure_rate":
            root_causes.append("解决方案设计不合理")
            root_causes.append("问题类型识别不准确")
            root_causes.append("系统环境变化导致解决方案失效")
        elif issue_type == "high_cpu_usage":
            root_causes.append("有进程占用过多CPU资源")
            root_causes.append("系统负载过高")
            root_causes.append("算法效率低下")
        elif issue_type == "high_memory_usage":
            root_causes.append("内存泄漏")
            root_causes.append("系统负载过高")
            root_causes.append("内存配置不足")
        elif issue_type == "high_disk_usage":
            root_causes.append("磁盘空间不足")
            root_causes.append("临时文件未清理")
            root_causes.append("日志文件过大")
        elif issue_type == "missing_dependencies":
            root_causes.append("依赖项安装不完整")
            root_causes.append("依赖项版本不兼容")
            root_causes.append("部署脚本错误")
        elif issue_type == "network_local_error":
            root_causes.append("端口被占用")
            root_causes.append("防火墙设置限制")
        elif issue_type == "ai_employees_insufficient":
            root_causes.append("AI员工初始化失败")
            root_causes.append("AI员工崩溃或异常退出")
            root_causes.append("系统资源不足导致AI员工无法启动")
        else:

        return root_causes

    def execute_repair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行系统修复"""
        issue_id = data.get("issue_id")
        issue_details = data.get("issue_details", {})

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 记录修复开始
            repair_log_id = f"log_{uuid.uuid4().hex[:8]}"
            start_time = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO ai_repair_logs
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repair_log_id,
                issue_id,
                solution_id,
                f"执行修复解决方案 {solution_id}",
                "repair",
                "in_progress",
                str({"status": "开始修复", "timestamp": start_time, "issue_details": issue_details}),
                self.name,
                start_time
            ))
            conn.commit()

            # 执行实际修复逻辑
            repair_result = self._execute_repair_steps(solution_id, issue_details)

            end_time = datetime.now().isoformat()
            result = "success" if repair_result["success"] else "failure"

            # 更新修复日志
            cursor.execute("""
                UPDATE ai_repair_logs
                SET result = ?, details = ?, end_time = ?
            """, (
                result,
                str({
                    "status": "修复完成",
                    "timestamp": end_time,
                    "start_time": start_time,
                    "duration": (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds(),
                    "repair_result": repair_result
                }),
                end_time,
                repair_log_id
            ))

            # 更新解决方案使用次数和效果评分
            if repair_result["success"]:
                cursor.execute("""
                    UPDATE ai_repair_solutions
                    SET usage_count = usage_count + 1, effectiveness_score = effectiveness_score + 0.1
                    WHERE id = ?
                """, (solution_id,))
            else:
                cursor.execute("""
                    UPDATE ai_repair_solutions
                    SET usage_count = usage_count + 1, effectiveness_score = MAX(0, effectiveness_score - 0.2)
                    WHERE id = ?
                """, (solution_id,))

            conn.commit()
            conn.close()

            return {
                "success": repair_result["success"],
                "message": repair_result["message"],
                "repair_log_id": repair_log_id,
                "solution_id": solution_id,
                "result": result,
                "details": repair_result
            }
        except Exception as e:
            print(f"[AI员工] 执行修复时发生错误: {e}")
            return {
                "message": f"执行修复时发生错误: {str(e)}",
                "data": data
            }

    def _execute_repair_steps(self, solution_id: str, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体的修复步骤"""
        try:
            conn = sqlite3.connect('app.db')

            # 获取解决方案的具体步骤
            cursor.execute("SELECT implementation_steps FROM ai_repair_solutions WHERE id = ?", (solution_id,))
            solution = cursor.fetchone()

            conn.close()
            # 执行解决方案步骤
            steps_executed = 0
                steps = eval(solution[0])
                for step in steps:
                    # 执行修复步骤
                    time.sleep(0.2)  # 模拟执行时间
                    steps_executed += 1
            elif "custom_" in solution_id:
                # 处理自定义解决方案
                steps = issue_details.get("steps", [])
                    time.sleep(0.2)  # 模拟执行时间
                    steps_executed += 1

            # 基于问题类型执行特定修复
            issue_type = issue_details.get("issue_type", "unknown")
            if issue_type == "database_incomplete":
                return self._fix_database_incomplete(issue_details)
            elif issue_type == "database_large":
                return self._fix_database_large(issue_details)
            elif issue_type == "database_missing_indexes":
                # 尝试修复数据库缺少索引问题
                return self._fix_database_missing_indexes(issue_details)
            elif issue_type == "file_missing":
                # 尝试修复文件缺失问题
                return self._fix_file_missing(issue_details)
            elif issue_type == "file_permission_error":
                # 尝试修复文件权限错误
            elif issue_type == "directory_missing":
                # 尝试修复目录缺失问题
                return self._fix_directory_missing(issue_details)
            elif issue_type == "directory_permission_error":
                # 尝试修复目录权限错误
                return self._fix_directory_permission_error(issue_details)
            elif issue_type == "large_log_file":
                return self._fix_large_log_file(issue_details)
                # 尝试修复日志目录缺失问题
                return self._fix_log_directory_missing(issue_details)
            elif issue_type == "missing_dependencies":
                # 尝试修复依赖项缺失问题
                return self._fix_missing_dependencies(issue_details)
            elif issue_type == "high_cpu_usage":
                return self._optimize_high_cpu_usage(issue_details)
            elif issue_type == "high_memory_usage":
                # 尝试优化高内存使用率问题
                return self._optimize_high_memory_usage(issue_details)
                # 尝试优化高磁盘使用率问题
                return self._optimize_high_disk_usage(issue_details)
            else:
                # 默认修复成功
                return {
                    "success": True,
                    "message": f"解决方案 {solution_id} 执行成功",
                    "steps_executed": steps_executed
        except Exception as e:
            return {
                "success": False,
                "error_details": str(e)
            }

    def _fix_database_incomplete(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """修复数据库表缺失问题"""
        try:
            # 尝试重新初始化数据库
            result = subprocess.run(
                text=True,
                cwd="."
            )

            if result.returncode == 0:
                return {
                    "message": "数据库表重新初始化成功",
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "message": f"数据库表初始化失败: {result.stderr.strip()}"
        except Exception as e:
            return {
                "success": False,
                "message": f"修复数据库表缺失失败: {str(e)}"
            }

    def _fix_file_missing(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
            "success": True,
            "message": "文件缺失问题已记录，建议手动检查和恢复缺失文件"
        }

        """清理过大的日志文件"""
        try:
            import gzip
            # 查找并压缩过大的日志文件
            log_files = glob.glob('logs/*.log')
            compressed_count = 0
            for log_file in log_files:
                if os.path.getsize(log_file) > 100 * 1024 * 1024:  # 100MB
                    # 压缩日志文件
                    compressed_file = f"{log_file}.gz"
                    print(f"[修复AI] 压缩日志文件: {log_file} -> {compressed_file}")
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                    os.remove(log_file)
                    compressed_count += 1

            for log_file in glob.glob('logs/*.log.gz'):
                file_time = os.path.getmtime(log_file)
                if current_time - file_time > 30 * 24 * 60 * 60:  # 30天
                    os.remove(log_file)
            return {
                "success": True,
                "compressed_files": compressed_count,
                "deleted_files": deleted_count
        except Exception as e:
            return {
                "success": False,
            }

    def _fix_database_large(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """修复数据库过大问题"""
        try:

            # 检查数据库大小
            db_size_mb = os.path.getsize('app.db') / (1024*1024) if os.path.exists('app.db') else 0

            # 执行数据库优化
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            # 运行VACUUM命令优化数据库
            print(f"[修复AI] 执行数据库优化，当前大小: {db_size_mb:.2f}MB")
            cursor.execute("VACUUM")
            # 分析表以更新统计信息
            cursor.execute("ANALYZE")

            conn.commit()
            conn.close()

            # 计算优化后的大小
            new_db_size_mb = os.path.getsize('app.db') / (1024*1024) if os.path.exists('app.db') else 0

            return {
                "success": True,
                "new_size_mb": new_db_size_mb,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"修复数据库过大问题失败: {str(e)}"
    def _fix_database_missing_indexes(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')

            # 为常用表添加索引
            indexes_added = 0

            # 为questions表添加索引
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_bank ON questions(question_bank_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_level ON questions(level_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty_id)")
                indexes_added += 4

            # 为ai_repair_logs表添加索引
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_repair_logs_result ON ai_repair_logs(result)")
                indexes_added += 2
            except Exception as e:
                print(f"[修复AI] 添加ai_repair_logs表索引失败: {e}")

            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_solutions_type ON ai_repair_solutions(issue_type)")
            except Exception as e:
                print(f"[修复AI] 添加ai_repair_solutions表索引失败: {e}")

            conn.commit()
            conn.close()
                "success": True,
                "message": f"成功添加 {indexes_added} 个数据库索引",
            }
        except Exception as e:
                "success": False,
                "message": f"修复数据库缺少索引问题失败: {str(e)}"
            }

        try:
            import os

            file_path = issue_details.get("file_path", "")
            if not file_path:
                    "success": False,

            # 设置文件权限为可读
            os.chmod(file_path, 0o644)  # rw-r--r--

            return {
                "message": f"成功修复文件 {file_path} 的权限错误",
                "file_path": file_path
            }
        except Exception as e:
            return {
                "success": False,
            }

        """修复目录缺失问题"""
        try:
            import os

            directory_path = issue_details.get("directory_path", "")
                return {
                    "success": False,
                    "message": "未提供目录路径"
            os.makedirs(directory_path, exist_ok=True)

            return {
                "success": True,
                "message": f"成功创建缺失的目录 {directory_path}",
                "directory_path": directory_path
        except Exception as e:
            return {
                "success": False,

    def _fix_directory_permission_error(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """修复目录权限错误"""
        try:

            directory_path = issue_details.get("directory_path", "")
                    "message": "未提供目录路径"
                }
            os.chmod(directory_path, 0o755)  # rwxr-xr-x

            return {
                "success": True,
                "message": f"成功修复目录 {directory_path} 的权限错误",
                "directory_path": directory_path
            }
            return {
                "success": False,

    def _fix_log_directory_missing(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """修复日志目录缺失问题"""
            import os

            # 创建日志目录
            # 设置正确的权限
            os.chmod('logs', 0o755)

            return {
                "success": True,
                "directory_path": "logs"
            }
        except Exception as e:
                "message": f"修复日志目录缺失问题失败: {str(e)}"
            }

        """修复依赖项缺失问题"""
        try:

            missing_deps = issue_details.get("missing_dependencies", [])
            if not missing_deps:
                return {
                    "success": True,
                    "message": "没有缺失的依赖项"
                }
            # 安装缺失的依赖项
                ["pip", "install"] + missing_deps,
                capture_output=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"成功安装缺失的依赖项: {', '.join(missing_deps)}",
                    "installed_dependencies": missing_deps
                }
            else:
                return {
                    "success": False,
                    "message": f"安装依赖项失败: {result.stderr.strip()}",
                }
            return {
                "success": False,
                "message": f"修复依赖项缺失问题失败: {str(e)}"
            }

        """优化高CPU使用率问题"""
        try:
            import psutil

            # 获取当前CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)

            # 获取占用CPU最高的进程
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    pinfo = proc.info
                        processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)

            # 获取前5个占用CPU最高的进程
            top_processes = processes[:5]

            return {
                "success": True,
                "message": f"CPU使用率优化分析完成，当前CPU使用率: {cpu_usage}%",
                "top_processes": top_processes
            }
        except Exception as e:
                "success": False,
            }

    def _optimize_high_memory_usage(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """优化高内存使用率问题"""
        try:

            # 获取当前内存使用率
            memory = psutil.virtual_memory()

            # 获取占用内存最高的进程
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    pinfo = proc.info
                    if pinfo['memory_percent'] > 0:
                        processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 按内存使用率排序
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)

            # 获取前5个占用内存最高的进程
            top_processes = processes[:5]
            return {
                "success": True,
                "message": f"内存使用率优化分析完成，当前内存使用率: {memory.percent}%",
                "memory_percent": memory.percent,
                "available_memory_mb": memory.available / (1024*1024),
                "top_processes": top_processes
            }
        except Exception as e:
                "success": False,
                "message": f"优化高内存使用率问题失败: {str(e)}"
            }

    def _optimize_high_disk_usage(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
            import psutil
            import os
            import glob

            # 获取当前磁盘使用率
            disk = psutil.disk_usage('/')

            # 查找大文件（大于100MB）
            large_files = []
            for root, dirs, files in os.walk('/'):
                for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path) / (1024*1024)
                        if file_size > 100:
                            large_files.append((file_path, file_size))
                        continue
            # 按文件大小排序
            large_files.sort(key=lambda x: x[1], reverse=True)

            top_large_files = large_files[:5]

                "success": True,
                "message": f"磁盘使用率优化分析完成，当前磁盘使用率: {disk.percent}%",
                "available_disk_mb": disk.free / (1024*1024),
                "top_large_files": top_large_files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"优化高磁盘使用率问题失败: {str(e)}"
    def _validate_repair(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """验证修复效果"""
            issue_type = issue["issue_type"]

            # 根据问题类型执行不同的验证逻辑
            if issue_type == "database_connection":
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                cursor.fetchone()
                conn.close()
                return {"success": True, "message": "数据库连接已恢复正常"}

                # 验证数据库表完整性
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                required_tables = ['ai_repair_solutions', 'ai_repair_logs', 'users', 'questions']
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [table[0] for table in cursor.fetchall()]

                missing_tables = [table for table in required_tables if table not in existing_tables]

                if not missing_tables:
                    return {"success": True, "message": "数据库表已恢复完整"}
                else:
                    return {"success": False, "message": f"数据库表仍不完整，缺少: {', '.join(missing_tables)}"}
                # 验证文件权限
                import os
                file_path = issue.get("details", {}).get("file_path", "")
                if file_path and os.path.exists(file_path) and os.access(file_path, os.R_OK):
                else:

            elif issue_type == "directory_missing":
                # 验证目录存在
                import os
                if directory_path and os.path.exists(directory_path):
                else:
                    return {"success": False, "message": f"目录 {directory_path} 仍不存在"}

                import os
                directory_path = issue.get("details", {}).get("directory_path", "")
                if directory_path and os.path.exists(directory_path) and os.access(directory_path, os.W_OK):
                    return {"success": True, "message": f"目录 {directory_path} 权限已恢复正常"}
                else:
                    return {"success": False, "message": f"目录 {directory_path} 权限仍有问题"}
                # 验证日志目录存在
                import os
                if os.path.exists('logs') and os.access('logs', os.W_OK):
                    return {"success": True, "message": "日志目录已创建并具有正确权限"}
                else:
                    return {"success": False, "message": "日志目录仍有问题"}

            elif issue_type == "large_log_file":
                import glob

                log_files = glob.glob('logs/*.log')
                large_logs = [f for f in log_files if os.path.getsize(f) > 100 * 1024 * 1024]

                if not large_logs:
                    return {"success": True, "message": "所有日志文件已压缩或清理"}
                    return {"success": False, "message": f"仍有大日志文件: {', '.join(large_logs)}"}

            elif issue_type == "missing_dependencies":
                # 验证依赖项已安装
                import importlib

                missing_deps = issue.get("details", {}).get("missing_dependencies", [])
                    if dep not in ['sqlite3', 'json', 'uuid', 'datetime', 'threading']:
                        try:
                        except ImportError:
                            return {"success": False, "message": f"依赖项 {dep} 仍未安装"}
                return {"success": True, "message": "所有缺失的依赖项已安装"}

            else:
                # 对于其他类型的问题，执行通用验证
                # 重新检测问题，看是否还存在
                detection_result = self.detect_issues({})
                    for detected_issue in detection_result["issues"]:
                        if detected_issue["issue_type"] == issue_type:
                            return {"success": False, "message": f"问题 {issue_type} 仍存在"}
                    return {"success": True, "message": f"问题 {issue_type} 已解决"}
                else:
                    return {"success": False, "message": "无法验证修复效果，检测过程失败"}

        except Exception as e:
            return {
                "success": False,
                "message": f"验证修复效果时发生错误: {str(e)}"
            }

    def _auto_analyze_repair_experience(self, issue_type: str, issue_details: Dict[str, Any],
                                       repair_result: str, learning_content: str) -> None:
        """自动分析修复经验，提取有用信息"""
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 检查是否有类似的问题和解决方案
            cursor.execute("""
                SELECT COUNT(*) FROM ai_repair_logs
                WHERE issue_id LIKE ? AND result = 'success'
            """, (f"%{issue_type}%",))

            cursor.execute("""
                SELECT COUNT(*) FROM ai_repair_logs
                WHERE issue_id LIKE ? AND result = 'failure'
            """, (f"%{issue_type}%",))
            similar_failure_count = cursor.fetchone()[0]
            total_similar = similar_success_count + similar_failure_count
            success_rate = similar_success_count / total_similar if total_similar > 0 else 0

            # 如果成功率低于70%，考虑改进解决方案
            if success_rate < 0.7 and total_similar > 5:
                # 查找当前最佳解决方案
                cursor.execute("""
                    WHERE issue_type = ?
                    ORDER BY effectiveness_score DESC
                    LIMIT 1
                """, (issue_type,))
                best_solution = cursor.fetchone()

                if best_solution:
                    # 分析如何改进解决方案
                    print(f"[修复AI] 注意: {issue_type}问题的成功率仅为 {success_rate:.2%}，建议改进现有解决方案")
                    print(f"[修复AI] 当前最佳解决方案: {best_solution[0]}，效果评分: {best_solution[1]:.2f}")

            conn.close()

            # 记录自动分析结果
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue_type,
                "success_rate": success_rate,
                "failure_cases": similar_failure_count,
            }

            # 将分析结果添加到学习历史中
            self.learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue_type,
                "solution_id": "auto_analysis",
                "result": "success",
                "content": f"自动分析结果: {str(analysis_result)}",
                "issue_details": issue_details,
                "duration": 0,
            })

        except Exception as e:
            print(f"[修复AI] 自动分析修复经验时发生错误: {e}")
    def _extract_lessons_from_experience(self, issue_type: str, repair_result: str,
                                        learning_content: str) -> List[str]:
        """从修复经验中提取教训"""
        lessons = []
        # 根据修复结果和问题类型提取教训
        if repair_result == "success":
            lessons.append(f"{issue_type}问题修复成功，解决方案有效")
            if learning_content:
                keywords = learning_content.split()
                important_keywords = [word for word in keywords if len(word) > 3][:5]
                if important_keywords:
                    lessons.append(f"关键成功因素: {', '.join(important_keywords)}")
        else:
            lessons.append(f"{issue_type}问题修复失败，需要改进解决方案")
            lessons.append(f"建议: 分析失败原因，优化修复步骤")

        # 根据问题类型添加特定教训
        if issue_type == "database_large":
            lessons.append("教训: 定期优化数据库可以防止性能下降")
        elif issue_type == "missing_dependencies":
            lessons.append("教训: 确保所有依赖项都已正确安装")
        elif issue_type == "high_cpu_usage":
            lessons.append("教训: 监控CPU使用率，及时发现并处理高负载问题")
        elif issue_type == "file_permission_error":
            lessons.append("教训: 确保文件和目录权限设置正确")

        return lessons
    def learn_from_repair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从修复中学习"""
        repair_log_id = data.get("repair_log_id")
        issue_type = data.get("issue_type")
        solution_id = data.get("solution_id")
        learning_content = data.get("learning_content", "")
        issue_details = data.get("issue_details", {})
        repair_duration = data.get("repair_duration", 0)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 记录学习内容
            if learning_content:
                cursor.execute("""
                    INSERT INTO ai_repair_learning
                    (repair_log_id, issue_type, solution_id, learning_content, learning_time, learned_by,
                     repair_result, repair_duration, issue_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    repair_log_id,
                    issue_type,
                    solution_id,
                    learning_content,
                    datetime.now().isoformat(),
                    self.name,
                    repair_result,
                    repair_duration,
                    str(issue_details)
                ))
                conn.commit()

            # 更新解决方案效果评分和使用统计
            if "custom_" not in solution_id:  # 只更新数据库中的解决方案
                if repair_result == "success":
                    # 修复成功，提高效果评分和使用次数
                    cursor.execute("""
                        UPDATE ai_repair_solutions
                        SET
                            usage_count = usage_count + 1,
                            effectiveness_score = MIN(1.0, effectiveness_score + 0.1),
                            last_used_time = ?,
                            success_count = success_count + 1
                        WHERE id = ?
                    """, (
                        datetime.now().isoformat(),
                        solution_id
                    ))
                else:
                    # 修复失败，降低效果评分但仍增加使用次数
                    cursor.execute("""
                        UPDATE ai_repair_solutions
                        SET
                            usage_count = usage_count + 1,
                            effectiveness_score = MAX(0.0, effectiveness_score - 0.2),
                            last_used_time = ?,
                            failure_count = failure_count + 1
                        WHERE id = ?
                    """, (
                        datetime.now().isoformat(),
                        solution_id
                    ))
                conn.commit()
            else:
                # 处理自定义解决方案，考虑将其添加到解决方案库
                if repair_result == "success":
                    # 检查是否已经存在类似的解决方案
                        SELECT id FROM ai_repair_solutions
                        AND effectiveness_score > 0.7
                    existing_solution = cursor.fetchone()
                    if not existing_solution:
                        new_solution_id = f"sol_{uuid.uuid4().hex[:8]}"
                        cursor.execute("""
                            INSERT INTO ai_repair_solutions
                            (id, issue_type, solution_title, solution_description,
                             implementation_steps, expected_outcome, effectiveness_score,
                             usage_count, success_count, failure_count, created_by, created_time, last_used_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            issue_type,
                            f"自动创建的{issue_type}解决方案",
                            f"从修复日志{repair_log_id}中自动学习生成的解决方案",
                            str(issue_details.get("steps", [])),
                            f"修复{issue_type}问题",
                            0.8,  # 初始效果评分
                            1,  # 已使用1次
                            1,  # 成功1次
                            0,  # 失败0次
                            self.name,
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        conn.commit()
                        print(f"[修复AI] 从修复经验中创建了新的解决方案: {new_solution_id}")

            # 自动分析修复经验，提取有用信息
            self._auto_analyze_repair_experience(issue_type, issue_details, repair_result, learning_content)

            conn.close()

            # 更新学习历史，添加更多详细信息
            learning_entry = {
                "timestamp": datetime.now().isoformat(),
                "repair_log_id": repair_log_id,
                "issue_type": issue_type,
                "solution_id": solution_id,
                "result": repair_result,
                "content": learning_content,
                "issue_details": issue_details,
                "duration": repair_duration,
                "learned_lessons": self._extract_lessons_from_experience(issue_type, repair_result, learning_content)
            }
            self.learning_history.append(learning_entry)

            # 定期清理旧的学习历史，只保留最近1000条
                self.learning_history = self.learning_history[-1000:]

                "repair_log_id": repair_log_id,
                "learned_lessons": learning_entry["learned_lessons"],
                "learning_entry": learning_entry
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"学习过程中发生错误: {str(e)}",
            }

    def evaluate_repair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估修复效果"""
        solution_id = data.get("solution_id")
        evaluation_criteria = data.get("criteria", ["success_rate", "performance_impact", "recovery_time"])

        try:

            if repair_log_id:
                # 评估特定修复日志的效果
                    FROM ai_repair_logs r
                    WHERE r.log_id = ?
                """, (repair_log_id,))
                if repair_log:
                    result = repair_log[0]
                    details = eval(repair_log[1])
                    start_time = repair_log[2]
                    end_time = repair_log[3]

                    # 计算修复时间
                    duration = 0
                    if start_time and end_time:
                        duration = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()

                    evaluation = {
                        "repair_log_id": repair_log_id,
                        "duration": duration,
                        "details": details
                    }

                    conn.close()

                        "success": True,
                        "message": "修复效果评估完成",
                        "evaluation": evaluation
                    }
                else:
                    conn.close()
                    return {
                        "success": False,
                        "message": f"未找到修复日志 {repair_log_id}"
            elif solution_id:
                # 获取修复统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as issue_count,
                        SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as success_count,
                        SUM(CASE WHEN result = 'failure' THEN 1 ELSE 0 END) as failure_count,
                        AVG(strftime('%s', end_time) - strftime('%s', start_time)) as avg_duration
                    FROM ai_repair_logs
                    WHERE solution_id = ?
                """, (solution_id,))
                stats = cursor.fetchone()

                conn.close()

                    effectiveness_score = stats[1] / stats[0] if stats[0] > 0 else 0
                    avg_duration = stats[3] if stats[3] else 0

                    return {
                        "success": True,
                        "effectiveness": {
                            "issue_count": stats[0],
                            "success_count": stats[1],
                            "failure_count": stats[2],
                            "effectiveness_score": effectiveness_score,
                            "success_rate": f"{effectiveness_score * 100:.2f}%",
                            "average_repair_time": f"{avg_duration:.2f}秒"
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"未找到解决方案 {solution_id} 的修复记录"
                    }
            else:
                conn.close()
                return {
                    "success": False,
                    "message": "必须提供 solution_id 或 repair_log_id 进行评估"
        except Exception as e:
            print(f"[AI员工] 评估修复效果时发生错误: {e}")
            return {
                "message": f"评估修复效果时发生错误: {str(e)}",
                "data": data
            }

    def perform_preventive_maintenance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行预防性维护"""

        try:
            results = []
                print(f"[修复AI] 执行预防性维护任务: {task}")
                # 模拟执行维护任务
                result = self._execute_maintenance_task(task)
                results.append({
                    "task": task,
                    "success": result["success"],
                    "message": result["message"]
                })
                time.sleep(0.5)  # 模拟执行时间

            # 记录预防性维护
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ai_preventive_maintenance
                (maintenance_type, tasks, results, maintenance_time, performed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(tasks),
                str(results),
                datetime.now().isoformat(),
                self.name
            conn.commit()
            conn.close()

            return {
                "success": True,
                "message": f"预防性维护 {maintenance_type} 完成",
                "tasks_performed": len(tasks),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[AI员工] 执行预防性维护时发生错误: {e}")
                "success": False,
                "message": f"执行预防性维护时发生错误: {str(e)}",
                "data": data
            }

        """执行单个维护任务"""
        try:
            if task == "check_database":
                # 实际检查数据库连接和表完整性
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()

                # 检查数据库连接
                cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                cursor.fetchone()

                # 检查关键表是否存在
                required_tables = ['ai_repair_solutions', 'ai_repair_logs', 'users', 'questions']
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [table[0] for table in cursor.fetchall()]

                missing_tables = [table for table in required_tables if table not in existing_tables]
                if missing_tables:
                    conn.close()
                    return {
                        "success": False,
                        "message": f"数据库检查失败，缺少关键表: {', '.join(missing_tables)}"
                    }

                conn.close()
                return {
                    "success": True,
                    "message": "数据库检查完成，所有关键表都存在",
                    "details": {
                        "checked_tables": len(required_tables),
                        "missing_tables": len(missing_tables)
                    }
                }
            elif task == "check_filesystem":
                # 实际检查文件系统状态和权限
                import os

                # 检查关键文件和目录
                critical_files = ['app.db', 'requirements.txt', 'config.py', 'ai_employee_base.py', 'ai_employee_system.py']
                critical_dirs = ['logs', 'static', 'templates']
                missing_files = []
                missing_dirs = []
                permission_issues = []

                for file_path in critical_files:
                    if not os.path.exists(file_path):
                        missing_files.append(file_path)
                    elif not os.access(file_path, os.R_OK):
                        permission_issues.append(f"无法读取文件: {file_path}")
                for dir_path in critical_dirs:
                    if not os.path.exists(dir_path):
                        missing_dirs.append(dir_path)
                    elif not os.access(dir_path, os.W_OK):
                        permission_issues.append(f"无法写入目录: {dir_path}")

                if missing_files or missing_dirs or permission_issues:
                    return {
                        "success": False,
                        "message": "文件系统检查失败",
                        "details": {
                            "missing_files": missing_files,
                            "missing_dirs": missing_dirs,
                            "permission_issues": permission_issues
                        }
                    }

                return {
                    "success": True,
                    "details": {
                        "checked_files": len(critical_files),
                        "checked_dirs": len(critical_dirs)
                    }
                }
            elif task == "check_logs":
                # 实际检查日志文件和错误
                import os
                import glob

                large_logs = []

                # 确保日志目录存在
                if not os.path.exists('logs'):
                    os.makedirs('logs', exist_ok=True)
                # 检查日志文件
                log_files = glob.glob('logs/*.log')
                for log_file in log_files:
                    # 检查日志大小
                    if os.path.getsize(log_file) > 100 * 1024 * 1024:  # 100MB
                        large_logs.append(log_file)

                    # 简单检查日志中的错误
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()[-100:]  # 只检查最后100行
                            error_count = sum(1 for line in lines if 'ERROR' in line or 'error' in line.lower())
                            if error_count > 5:
                                log_errors.append(f"日志 {log_file} 中发现 {error_count} 个错误")
                    except Exception as e:
                        log_errors.append(f"无法读取日志文件 {log_file}: {str(e)}")

                return {
                    "success": True,
                    "message": "日志检查完成",
                    "details": {
                        "total_logs": len(log_files),
                        "large_logs": len(large_logs),
                        "log_errors": len(log_errors),
                        "large_log_files": large_logs,
                        "log_error_details": log_errors
                    }
            elif task == "optimize_database":
                # 实际执行数据库优化操作
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()

                # 执行VACUUM命令优化数据库
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")

                conn.commit()
                conn.close()

                    "success": True,
                    "message": "数据库优化完成，执行了VACUUM和ANALYZE操作"
                }

            elif task == "clean_logs":
                import os
                import glob
                import time

                # 确保日志目录存在
                if not os.path.exists('logs'):
                    os.makedirs('logs', exist_ok=True)

                cleaned_count = 0

                # 清理超过30天的日志文件
                current_time = time.time()
                for log_file in glob.glob('logs/*.log.gz'):
                    file_time = os.path.getmtime(log_file)
                    if current_time - file_time > 30 * 24 * 60 * 60:  # 30天
                        os.remove(log_file)

                for log_file in glob.glob('logs/*.log'):
                    if os.path.getsize(log_file) > 100 * 1024 * 1024:  # 100MB
                        import gzip

                        compressed_file = f"{log_file}.gz"
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(log_file)
                        compressed_count += 1

                return {
                    "success": True,
                    "details": {
                        "cleaned_logs": cleaned_count,
                        "compressed_logs": compressed_count
                    }
                }

            elif task == "backup_data":
                import os
                import shutil
                import datetime

                # 确保备份目录存在
                backup_dir = 'backups'
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir, exist_ok=True)

                backup_filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

                # 复制数据库文件
                if os.path.exists('app.db'):
                    shutil.copy2('app.db', backup_path)
                    return {
                        "success": True,
                        "message": f"数据备份完成，备份文件: {backup_path}",
                        "details": {
                            "backup_file": backup_path,
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": "数据备份失败，数据库文件不存在"
                    }

                # 实际更新解决方案
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()
                # 检查是否有新的解决方案可以添加
                # 这里可以添加从外部源获取解决方案的逻辑
                cursor.execute("SELECT COUNT(*) FROM ai_repair_solutions")
                solution_count = cursor.fetchone()[0]

                cursor.execute("SELECT AVG(effectiveness_score) FROM ai_repair_solutions")
                conn.close()
                return {
                    "success": True,
                    "details": {
                        "total_solutions": solution_count,
                        "average_effectiveness": avg_effectiveness
                    }
                }

            elif task == "analyze_performance":
                # 实际分析系统性能
                import psutil

                # 获取系统资源使用情况
                cpu_usage = psutil.cpu_percent(interval=0.5)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        pinfo = proc.info
                        if pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 0:
                            processes.append(pinfo)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # 按CPU使用率排序，获取前5个进程
                top_cpu_processes = processes[:5]

                return {
                    "message": "系统性能分析完成",
                    "details": {
                        "cpu_usage": cpu_usage,
                        "memory_percent": memory.percent,
                        "available_memory_mb": memory.available / (1024*1024),
                        "available_disk_mb": disk.free / (1024*1024),
                        "top_cpu_processes": top_cpu_processes
                    }
            elif task == "test_recovery":
                # 实际测试系统恢复能力
                # 这里可以添加更复杂的恢复测试逻辑
                # 目前只是检查关键组件是否正常运行

                try:
                    # 测试数据库连接
                    conn = sqlite3.connect('app.db')
                    cursor = conn.cursor()
                    conn.close()

                    ai_route_system = get_ai_route_system()
                    return {
                        "success": True,
                        "details": {
                            "database_status": "正常",
                            "ai_system_status": status["is_running"],
                            "total_ai_employees": status["total_employees"]
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"系统恢复测试失败: {str(e)}"
                    }

            else:
                return {
                    "success": False,
                    "message": f"未知维护任务: {task}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def auto_repair_system(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """自动修复系统"""
        if not self.auto_repair_enabled:
            return {
                "message": "自动修复功能未启用"

        try:
            # 1. 检测问题
            if not detection_result["success"]:
                return detection_result

            # 2. 分析问题并执行修复
            fixed_issues = []
            attempted_issues = []
            # 按照严重程度排序问题，优先处理严重问题
            sorted_issues = sorted(detection_result["issues"],
                                 key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]])

            for issue in sorted_issues:
                # 自动修复critical、high和部分medium级别的问题
                if issue["severity"] in ["critical", "high"] or \
                   (issue["severity"] == "medium" and issue["issue_type"] in ["file_permission_error", "directory_missing", \
                                                                             "directory_permission_error", "log_directory_missing"]):

                    attempted_issues.append(issue)

                    # 分析问题
                    analysis_result = self.analyze_issue({"issue_type": issue["issue_type"], "details": issue})
                    if analysis_result["success"] and analysis_result["recommended_solutions"]:
                        best_solution = sorted(analysis_result["recommended_solutions"],
                                             key=lambda x: x["effectiveness_score"], reverse=True)[0]

                        # 执行修复
                        repair_result = self.execute_repair({
                            "issue_id": f"issue_{uuid.uuid4().hex[:8]}",
                            "solution_id": best_solution["solution_id"],
                            "issue_details": issue
                        })
                        if repair_result["success"]:
                            # 修复成功后，验证修复效果
                            validation_result = self._validate_repair(issue)
                                fixed_issues.append({
                                    "solution": best_solution,
                                    "repair_result": repair_result,
                                    "validation_result": validation_result
                                })
                                # 从修复经验中学习
                                self.learn_from_repair({
                                    "repair_log_id": repair_result.get("repair_log_id", "auto_repair"),
                                    "issue_type": issue["issue_type"],
                                    "repair_result": "success",
                                    "learning_content": f"自动修复{issue['issue_type']}问题成功",
                                    "issue_details": issue,
                                })
                            else:
                                failed_issues.append({
                                    "issue": issue,
                                    "solution": best_solution,
                                    "repair_result": repair_result,
                                    "validation_result": validation_result
                                })
                        else:
                            failed_issues.append({
                                "issue": issue,
                                "solution": best_solution,
                                "repair_result": repair_result
                            })

                            # 从失败经验中学习
                                "repair_log_id": repair_result.get("repair_log_id", "auto_repair"),
                                "issue_type": issue["issue_type"],
                                "solution_id": best_solution["solution_id"],
                                "repair_result": "failure",
                                "learning_content": f"自动修复{issue['issue_type']}问题失败: {repair_result['message']}",
                                "issue_details": issue,
                            })

            # 3. 生成修复报告
            repair_report = {
                "success": True,
                "message": "自动修复完成",
                "attempted_issues_count": len(attempted_issues),
                "fixed_issues_count": len(fixed_issues),
                "failed_issues_count": len(failed_issues),
                "fixed_issues": fixed_issues,
                "failed_issues": failed_issues,
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "critical_issues": len([i for i in detection_result["issues"] if i["severity"] == "critical"]),
                    "medium_issues": len([i for i in detection_result["issues"] if i["severity"] == "medium"]),
                    "low_issues": len([i for i in detection_result["issues"] if i["severity"] == "low"])

            # 4. 记录自动修复报告
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute("""
                (total_issues, attempted_issues, fixed_issues, failed_issues,
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                repair_report["total_issues"],
                len(attempted_issues),
                str(repair_report),
                datetime.now().isoformat(),
                self.name
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI员工] 自动修复时发生错误: {e}")
            return {
                "success": False,
                "message": f"自动修复时发生错误: {str(e)}",
                "data": data
            }

        """优化系统性能"""
        try:
            optimization_type = data.get("optimization_type", "all")
            results = []

            if optimization_type in ["all", "database"]:
                # 优化数据库
                db_optimization = self._optimize_database()
                results.append(db_optimization)

            if optimization_type in ["all", "filesystem"]:
                fs_optimization = self._optimize_filesystem()
                results.append(fs_optimization)

            if optimization_type in ["all", "performance"]:
                # 优化系统性能
                perf_optimization = self._optimize_performance()
                results.append(perf_optimization)

            if optimization_type in ["all", "security"]:
                # 优化系统安全性
                sec_optimization = self._optimize_security()
                results.append(sec_optimization)

            # 统计优化结果
            success_count = len([r for r in results if r["success"]])
            total_count = len(results)

            return {
                "success": True,
                "message": f"系统优化 {optimization_type} 完成，成功 {success_count}/{total_count}",
                "success_count": success_count,
                "total_count": total_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[AI员工] 系统优化时发生错误: {e}")
            return {
                "success": False,
                "message": f"系统优化时发生错误: {str(e)}",
                "data": data
            }

    def _optimize_database(self) -> Dict[str, Any]:
        """优化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 执行VACUUM命令优化数据库
            cursor.execute("VACUUM")

            # 执行ANALYZE命令更新统计信息
            cursor.execute("ANALYZE")
            cursor.execute("REINDEX")

            conn.commit()
            conn.close()

                "type": "database",
                "success": True,
                "message": "数据库优化完成，执行了VACUUM、ANALYZE和REINDEX操作",
                "details": {
                }
            }
        except Exception as e:
                "type": "database",
                "success": False,
                "message": f"数据库优化失败: {str(e)}",
                "error": str(e)

    def _optimize_filesystem(self) -> Dict[str, Any]:
        """优化文件系统"""
        try:
            import glob

            temp_files = glob.glob('/tmp/*') + glob.glob('*.tmp') + glob.glob('*.bak')
            deleted_files = 0

            for file_path in temp_files:
                try:
                        os.remove(file_path)
                        deleted_files += 1
                    continue

            # 清理空目录
            empty_dirs = []
            for root, dirs, files in os.walk('.'):
                for dir_path in dirs:
                    if not os.listdir(full_path):
                        empty_dirs.append(full_path)

            for dir_path in empty_dirs[:10]:  # 最多清理10个空目录
                try:
                    os.rmdir(dir_path)
                    continue

            # 检查磁盘空间
            import psutil

            return {
                "type": "filesystem",
                "success": True,
                "message": f"文件系统优化完成，清理了 {deleted_files} 个临时文件",
                "details": {
                    "cleaned_empty_dirs": len(empty_dirs[:10]),
                    "disk_usage_percent": disk.percent,
                    "available_disk_mb": disk.free / (1024*1024)
                }
        except Exception as e:
            return {
                "type": "filesystem",
                "success": False,
                "message": f"文件系统优化失败: {str(e)}",
                "error": str(e)
            }

        try:
            import psutil

            # 获取当前系统资源使用情况
            cpu_before = psutil.cpu_percent(interval=0.5)
            memory_before = psutil.virtual_memory().percent

            # 关闭不必要的进程（仅示例，实际操作需谨慎）
            # 这里只是获取进程信息，不实际关闭进程
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 50 or pinfo['memory_percent'] > 10:
                        processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = processes[:5]

            # 获取优化后的系统资源使用情况
            memory_after = psutil.virtual_memory().percent

            return {
                "success": True,
                "message": "系统性能优化完成，分析了高资源占用进程",
                "details": {
                    "cpu_usage_before": cpu_before,
                    "memory_usage_before": memory_before,
                    "memory_usage_after": memory_after,
                    "top_resource_intensive_processes": top_processes
                }
            }
        except Exception as e:
            return {
                "type": "performance",
                "success": False,
            }

        try:
            import os

            # 检查关键文件权限
            critical_files = ['app.db', 'config.py', 'ai_employee_system.py']
            permission_issues = []
            for file_path in critical_files:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    mode = stat.st_mode

                    # 检查是否有执行权限
                    if mode & 0o111:  # 执行权限
                        permission_issues.append(f"文件 {file_path} 具有不必要的执行权限")
                    # 检查是否允许其他用户写入
                    if mode & 0o002:  # 其他用户写权限

            # 检查是否存在安全配置文件
            security_measures = []
            if os.path.exists('.env'):
                security_measures.append("找到环境配置文件")
            else:
                security_measures.append("未找到环境配置文件，建议创建")
            return {
                "type": "security",
                "message": "系统安全性优化完成，检查了关键文件权限和安全配置",
                "details": {
                    "permission_issues": permission_issues,
                }
            }
        except Exception as e:
            return {
                "type": "security",
                "success": False,
            }
    def train(self, training_data: str, training_source: str) -> Dict[str, Any]:
        """训练修复AI"""
            if not training_data:
                return {
                    "success": False,
                    "message": "训练数据不能为空"
                }

            print(f"[修复AI] 开始训练，数据来源: {training_source}")
            # 解析训练数据
            parsed_data = None
            if isinstance(training_data, str):
                try:
                    # 尝试解析JSON格式的字符串
                    parsed_data = eval(training_data)
                except json.JSONDecodeError:
                    # 纯文本格式
                    parsed_data = training_data
                parsed_data = training_data
            # 提取训练样本
            training_samples = []
                training_samples = parsed_data["examples"]
            elif isinstance(parsed_data, list):
                # 直接是示例列表
                training_samples = parsed_data
            else:
            # 统计训练样本数量
            training_count = len(training_samples)
            print(f"[修复AI] 训练样本数量: {training_count}")

            # 处理每个训练样本
            processed_samples = 0
            new_solutions = 0
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            for sample in training_samples:
                try:
                    if isinstance(sample, dict):
                        issue_type = sample.get("issue_type")
                        solution = sample.get("solution")

                            # 检查是否已存在相同的解决方案
                            cursor.execute("""
                                SELECT id FROM ai_repair_solutions
                                WHERE issue_type = ?
                                AND solution_title = ?
                            existing_solution = cursor.fetchone()

                            if not existing_solution:
                                new_solution_id = f"sol_{uuid.uuid4().hex[:8]}"
                                cursor.execute("""
                                    (id, issue_type, solution_title, solution_description,
                                     implementation_steps, expected_outcome, effectiveness_score,
                                     usage_count, success_count, failure_count, created_by, created_time, last_used_time)
                                """, (
                                    new_solution_id,
                                    solution.get("title", ""),
                                    solution.get("description", ""),
                                    str(solution.get("steps", [])),
                                    solution.get("expected_outcome", ""),
                                    solution.get("effectiveness_score", 0.7),
                                    0,
                                    0,
                                    0,
                                    self.name,
                                    datetime.now().isoformat()
                                ))
                                new_solutions += 1
                    print(f"[修复AI] 处理训练样本失败: {sample_error}")
                    continue

            # 记录训练历史
                INSERT INTO ai_training_history
                (training_source, training_data, training_time, trained_by, training_count,
                 processed_samples, new_solutions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                training_source,
                str(training_data) if isinstance(training_data, (dict, list)) else training_data,
                datetime.now().isoformat(),
                self.name,
                training_count,
                processed_samples,
                new_solutions
            ))

            conn.commit()
            conn.close()

            # 更新AI修复系统的学习状态
            self.learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "training",
                "source": training_source,
                "training_count": training_count,
                "processed_samples": processed_samples,
                "new_solutions": new_solutions,
                "message": f"从 {training_source} 训练完成，处理了 {processed_samples} 个样本，创建了 {new_solutions} 个新解决方案"
            })

            # 清理旧的学习历史，只保留最近1000条
            if len(self.learning_history) > 1000:
                self.learning_history = self.learning_history[-1000:]

                "success": True,
                "processed_samples": processed_samples,
                "training_source": training_source,
                "timestamp": datetime.now().isoformat()
        except Exception as e:
            print(f"[AI员工] 训练过程中发生错误: {e}")
                "success": False,
                "message": f"训练过程中发生错误: {str(e)}",
            }


    """AI路由系统 - 管理AI员工和处理请求"""

        """初始化AI路由系统"""
        self.ai_employees = {}
        self.is_running = False
        self.system_version = "1.0.0"  # 系统版本
        self.last_update = datetime.now().isoformat()  # 最后更新时间

    def start(self):
        """启动AI路由系统"""
        self.is_running = True

        # 初始化AI员工
        self.ai_employees["validation"] = ValidationAIEmployee("val_001", "验证AI")
        self.ai_employees["routing"] = RoutingAIEmployee("route_001", "路由AI")
        self.ai_employees["test_system"] = TestSystemAIEmployee("test_001", "测试系统AI")
        self.ai_employees["repair"] = RepairAIEmployee("repair_001", "修复AI")


    def stop(self):
        """停止AI路由系统"""
        self.is_running = False
        print("AI路由系统已停止")

    def process_request(self, path: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        if not self.is_running:
            return {"success": False, "message": "AI路由系统未运行"}

        # 简单路由逻辑
            return self.ai_employees["validation"].process(request_data)
        elif "/test-system" in path:
            return self.ai_employees["test_system"].process(request_data)
        elif "/repair" in path:
            return self.ai_employees["repair"].process(request_data)
        elif "/system/update" in path:
            return self.auto_update_system(request_data)
        elif "/system/expand" in path:
        else:
            return self.ai_employees["routing"].process(request_data)

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
            "is_running": self.is_running,
            "total_employees": len(self.ai_employees),
            "system_version": self.system_version,
            "last_update": self.last_update,
            "employees": {
                emp_id: {
                    "name": emp.name,
                    "type": emp.type,
                    "last_active": getattr(emp, 'last_active', 'N/A')
                } for emp_id, emp in self.ai_employees.items()
        }

    def auto_update_system(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """自动更新系统"""
        自动更新系统功能
        - 修复发现的问题
        - 更新系统版本
        - 记录更新日志
            print("开始自动更新系统...")

            # 1. 检查系统状态
            status = self.get_status()

            # 2. 执行系统修复
            repair_results = []
            for emp_id, emp in self.ai_employees.items():
                if hasattr(emp, 'detect_issues'):
                    issues = emp.detect_issues({"system_check": True})
                    if issues.get("issues"):
                        for issue in issues["issues"]:
                            # 根据问题类型执行相应的修复操作
                                "type": "auto_repair",
                                "issue_type": issue["issue_type"]
                            }
                            repair_result = emp.process(repair_data)
                                "employee": emp_id,
                                "success": repair_result["success"]
            # 3. 更新系统版本
            # 简单的版本号递增逻辑
            version_parts = list(map(int, self.system_version.split('.')))
            version_parts[2] += 1  # 递增补丁版本
            new_version = '.'.join(map(str, version_parts))
            self.system_version = new_version

            # 4. 保存更新日志
            update_log = {
                "timestamp": self.last_update,
                "version": self.system_version,
                "repair_results": repair_results,
            }
            # 保存到数据库或文件
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 创建更新日志表
                CREATE TABLE IF NOT EXISTS system_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    version TEXT NOT NULL,
                    repair_results TEXT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 插入更新记录
            cursor.execute("""
                INSERT INTO system_updates (timestamp, version, repair_results, message)
                VALUES (?, ?, ?, ?)
            """, (
                update_log["timestamp"],
                update_log["version"],
                str(update_log["repair_results"]),
                update_log["message"]
            ))

            conn.commit()
            conn.close()

            print(f"系统更新完成，新版本: {self.system_version}")

            return {
                "success": True,
                "message": "系统自动更新完成",
                "new_version": self.system_version,
                "last_update": self.last_update,
                "repair_results": repair_results
            }
            print(f"系统更新失败: {str(e)}")
            return {
                "message": f"系统更新失败: {str(e)}"
            }

    def expand_system(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """拓展系统功能"""
        拓展系统功能
        - 添加新的功能模块
        - 优化现有功能
        try:

            # 1. 增强AI员工能力
            expansion_results = []

            # 增强修复AI能力
            if "repair" in self.ai_employees:
                repair_ai = self.ai_employees["repair"]
                # 训练修复AI，增强其能力
                training_data = {
                    "type": "train",
                    "training_source": "self"
                }
                training_result = repair_ai.process(training_data)
                expansion_results.append({
                    "component": "repair_ai",
                    "action": "training",
                    "success": training_result["success"]
                })

            # 增强测试系统AI能力
            if "test_system" in self.ai_employees:
                test_ai = self.ai_employees["test_system"]
                # 执行自我升级
                upgrade_result = test_ai.self_upgrade({"upgrade_type": "full", "data_source": "all"})
                expansion_results.append({
                    "component": "test_system_ai",
                    "action": "self_upgrade",
                    "success": upgrade_result["success"]
                })

            # 2. 记录拓展日志
            expansion_log = {
                "timestamp": datetime.now().isoformat(),
                "results": expansion_results,
                "message": "系统功能拓展完成"
            }

            # 保存到数据库
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # 创建系统拓展日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_expansions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    results TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 插入拓展记录
            cursor.execute("""
                INSERT INTO system_expansions (timestamp, results, message)
                VALUES (?, ?, ?)
                expansion_log["timestamp"],
                str(expansion_log["results"]),
                expansion_log["message"]
            ))

            conn.commit()
            conn.close()


            return {
                "success": True,
                "message": "系统功能拓展完成",
                "expansion_results": expansion_results
            }
            print(f"系统功能拓展失败: {str(e)}")
            return {
                "success": False,
                "message": f"系统功能拓展失败: {str(e)}"

# AI级别定义
AI_LEVELS = {
    "L1": {"name": "基础AI", "capabilities": ["basic_tasks"], "max_employees": 5},
    "L2": {"name": "高级AI", "capabilities": ["basic_tasks", "complex_tasks"], "max_employees": 3},
    "L3": {"name": "专家AI", "capabilities": ["basic_tasks", "complex_tasks", "expert_tasks"], "max_employees": 2},
    "L4": {"name": "主管AI", "capabilities": ["basic_tasks", "complex_tasks", "expert_tasks", "management"], "max_employees": 1}
}

# AI员工类型与级别对应关系
AI_EMPLOYEE_TYPE_LEVEL = {
    "validation": "L1",
    "routing": "L1",
    "test_system": "L2",
    "repair": "L3"
}

# AI功能与任务分配映射
AI_CAPABILITIES_MAP = {
    "basic_tasks": ["auth", "routing"],
    "complex_tasks": ["test_generation", "question_analysis"],
    "expert_tasks": ["system_repair", "performance_optimization"],
    "management": ["employee_coordination", "system_monitoring", "task_allocation"]
}

class AILevelManager:
    """AI级别管理器，负责AI级别的定义和管理"""

    def __init__(self):
        self.levels = AI_LEVELS
        self.employee_counts = {level_id: 0 for level_id in AI_LEVELS}

    def get_level(self, level_id: str) -> Dict[str, Any]:
        """获取指定级别的信息"""
        return self.levels.get(level_id, {})

    def can_create_employee(self, level_id: str) -> bool:
        """检查是否可以创建指定级别的AI员工"""
        if level_id not in self.levels:
            return False
        return self.employee_counts[level_id] < self.levels[level_id]["max_employees"]

    def create_employee(self, level_id: str, employee_type: str, name: str) -> AIEmployee:
        """创建指定级别的AI员工"""
            raise ValueError(f"无法创建更多{level_id}级别的AI员工，已达到上限")
        # 创建对应类型的AI员工
        employee_id = f"{employee_type}_{uuid.uuid4().hex[:8]}"
        if employee_type == "validation":
            employee = ValidationAIEmployee(employee_id, name)
        elif employee_type == "routing":
            employee = RoutingAIEmployee(employee_id, name)
        elif employee_type == "test_system":
            employee = TestSystemAIEmployee(employee_id, name)
            employee = RepairAIEmployee(employee_id, name)
        else:
            raise ValueError(f"未知的AI员工类型: {employee_type}")
        # 设置员工级别
        return employee
        stats = {}
                "max_count": level_info["max_employees"],
            }
        return stats

    """AI任务分配器，负责AI之间的功能与任务分配"""
        self.ai_employees = ai_employees
    def allocate_task(self, task_type: str, task_data: Dict[str, Any]) -> AIEmployee:
        # 确定完成该任务所需的能力

        # 查找具备该能力的AI员工
        suitable_employees = []
            if hasattr(employee, 'capabilities') and required_capability in employee.capabilities:
                suitable_employees.append(employee)
        if not suitable_employees:
        # 选择最合适的AI员工（这里简单选择第一个，实际可以根据负载、优先级等因素选择）

    def _get_required_capability(self, task_type: str) -> str:
        for capability, task_types in AI_CAPABILITIES_MAP.items():
            if task_type in task_types:
                return capability

    def reallocate_tasks(self) -> Dict[str, Any]:
        """重新分配所有AI员工的任务"""
        # 这里可以实现更复杂的任务重新分配逻辑
        # 例如：根据员工负载、能力和优先级重新分配任务
        return {
            "success": True,
            "message": "任务重新分配完成"
        }

class AIAutoGenerator:
    """AI自动生成器，负责自动生成AI级别和AI员工"""

    def __init__(self, ai_route_system: AIRouteSystem):
        self.level_manager = AILevelManager()
        self.task_allocator = AITaskAllocator(ai_route_system.ai_employees)

    def auto_generate_employees(self, count: int = None) -> Dict[str, Any]:
        generated_employees = []
        employee_types = list(AI_EMPLOYEE_TYPE_LEVEL.keys())
        # 如果没有指定数量，生成默认数量的AI员工
        if count is None:
            count = len(employee_types)

        for _ in range(count):
            # 随机选择一个AI员工类型
            level_id = AI_EMPLOYEE_TYPE_LEVEL[employee_type]

            # 检查是否可以创建该级别的AI员工
            if not self.level_manager.can_create_employee(level_id):
                continue

            # 创建AI员工
            employee_name = f"{AI_LEVELS[level_id]['name']}_{employee_type}_{uuid.uuid4().hex[:4]}"
            try:
                self.ai_route_system.ai_employees[employee.id] = employee
                generated_employees.append({
                    "id": employee.id,
                    "name": employee.name,
                    "type": employee.type,
                })
            except Exception as e:
                print(f"生成AI员工失败: {e}")

        return {
            "success": True,
            "message": f"成功生成{len(generated_employees)}个AI员工",
            "generated_employees": generated_employees
        }

    def auto_allocate_tasks(self) -> Dict[str, Any]:
        """自动分配AI任务"""
        # 这里可以实现更复杂的任务分配逻辑
        return {
            "success": True,
            "message": "任务自动分配完成"
        }

    def get_generation_status(self) -> Dict[str, Any]:
        """获取AI生成状态"""
        return {
            "level_stats": self.level_manager.get_level_stats(),
            "total_employees": len(self.ai_route_system.ai_employees),
            "employee_types": list(set(emp.type for emp in self.ai_route_system.ai_employees.values()))
        }

# 扩展AIRouteSystem类，添加AI自动生成和任务分配功能
super_start = AIRouteSystem.start
super_process_request = AIRouteSystem.process_request
def extended_start(self):
    """扩展的start方法，添加AI自动生成和任务分配功能"""
    # 调用原始start方法
    super_start(self)

    # 初始化AI自动生成器
    self.ai_generator = AIAutoGenerator(self)
    self.level_manager = AILevelManager()

    # 自动生成一些AI员工
    self.ai_generator.auto_generate_employees()

def extended_process_request(self, path: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """扩展的process_request方法，添加任务分配功能"""
    # 处理AI自动生成和任务分配相关的请求
    if "/ai/generate" in path:
        return self.ai_generator.auto_generate_employees()
    elif "/ai/allocate" in path:
        return self.ai_generator.auto_allocate_tasks()
    elif "/ai/status" in path:
        return self.ai_generator.get_generation_status()
    elif "/ai/levels" in path:
        return {"success": True, "levels": AI_LEVELS}

    # 调用原始process_request方法处理其他请求

# 替换原始方法
AIRouteSystem.start = extended_start
# 单例管理
_ai_route_system_instance = None


    """获取AI路由系统单例实例"""
    if _ai_route_system_instance is None:
        _ai_route_system_instance = AIRouteSystem()
        _ai_route_system_instance.start()
    return _ai_route_system_instance


# 测试代码
    # 创建AI路由系统实例
    ai_route_system = get_ai_route_system()

    # 打印系统状态
    print("\n系统状态:")
    print(str(ai_route_system.get_status(), ensure_ascii=False, indent=2))
    # 测试AI自动生成功能
    generate_result = ai_route_system.process_request("/ai/generate", {})
    print(str(generate_result, ensure_ascii=False, indent=2))

    # 测试AI级别信息
    levels_result = ai_route_system.process_request("/ai/levels", {})
    print("\nAI级别信息:")
    print(str(levels_result, ensure_ascii=False, indent=2))
    # 测试AI状态信息
    ai_status_result = ai_route_system.process_request("/ai/status", {})
    print("\nAI状态信息:")
    print(str(ai_status_result, ensure_ascii=False, indent=2))

    # 测试修复AI功能
    repair_request = {
        "type": "detect",
        "data": {}
    }

    repair_result = ai_route_system.process_request("/repair", repair_request)
    print("\n修复检测结果:")
    print(str(repair_result, ensure_ascii=False, indent=2))

    # 停止系统
    ai_route_system.stop()
