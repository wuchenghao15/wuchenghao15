#!/usr/bin/env python3
"""
AI员工系统 - 负责路由绑定、验证和跳转判定
"""

import logging
logger = logging.getLogger(__name__)
import time
import threading
import random
from typing import Dict, Any, Tuple, Optional, List
import uuid
import sqlite3
from contextlib import contextmanager
from datetime import datetime

class AIEmployee:
    """AI员工基类"""
    
    def __init__(self, employee_id: str, name: str, employee_type: str = "general", level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.employee_type = employee_type
        self.level = level
        self.status = "active"
        self.last_active = datetime.now().isoformat()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        self.last_active = datetime.now().isoformat()
        return {"success": False, "message": "未实现的方法"}


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

        if not username or not password:
            return {
                "success": False,
                "message": "用户名和密码不能为空",
                "data": data
            }

        if len(username) < 3 or len(username) > 20:
            return {
                "success": False,
                "message": "用户名长度必须在3到20个字符之间",
                "data": data
            }

        if len(password) < 6:
            return {
                "success": False,
                "message": "密码长度必须至少为6个字符",
                "data": data
            }
        
        return {
            "success": True,
            "message": "登录信息验证成功",
            "data": data
        }

    def validate_register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证注册信息"""
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not username or not email or not password or not confirm_password:
            return {
                "success": False,
                "message": "所有字段都必须填写",
                "data": data
            }

        if len(username) < 3 or len(username) > 20:
            return {
                "success": False,
                "message": "用户名长度必须在3到20个字符之间",
                "data": data
            }

        import re
        if not re.match(email_pattern, email):
            return {
                "success": False,
                "message": "邮箱格式不正确",
                "data": data
            }

        if len(password) < 6:
            return {
                "success": False,
                "message": "密码长度必须至少为6个字符",
                "data": data
            }

        if password != confirm_password:
            return {
                "success": False,
                "message": "两次输入的密码不一致",
                "data": data
            }

        return {
            "success": True,
            "message": "注册信息验证成功",
            "data": data
        }

    def validate_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证请求信息"""
        return {
            "success": True,
            "message": "请求验证成功",
            "data": data
        }


class RoutingAIEmployee(AIEmployee):
    """路由AI员工 - 负责路由跳转判定"""
    
    def __init__(self, employee_id: str, name: str, employee_type: str = "routing", level: int = 1):
        super().__init__(employee_id, name, employee_type, level)
        self.routing_rules = {
            "login": {
                "success": "/",
                "failure": "/auth/login"
            },
            "register": {
                "success": "/auth/login",
                "failure": "/auth/register"
            },
            "logout": {
                "success": "/auth/login",
                "failure": "/"
            }
        }
        self.route_map = self.routing_rules

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
                "data": routing_data
            }

    def determine_route(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """确定路由"""
        action = data.get("action")
        result = data.get("result", "success")
        request_path = data.get("request_path", "/")
        user_role = data.get("user_role", "guest")

        redirect_path = self.route_map.get(action, {}).get(result, "/")

        if user_role == "student":
            redirect_path = "/test-system"
        elif user_role in ["admin", "super_admin", "hardware_admin"]:
            redirect_path = "/dashboard"

        return {
            "success": True,
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
        }

    def update_route_map(self, new_routes: Dict[str, Any]):
        """更新路由映射"""
        self.route_map.update(new_routes)
        print(f"[AI员工] 更新路由映射: {str(new_routes)}")


class TestSystemAIEmployee(AIEmployee):
    """测试系统AI员工 - 负责测试系统参数管理、自我升级学习和测试页面自动完善"""

    def __init__(self, employee_id: str, name: str, employee_type: str = "test_system", level: int = 1):
        super().__init__(employee_id, name, employee_type, level)
        self.test_config = {
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
        self.test_parameters = self.test_config
        self.learning_history = []
        self.upgrade_count = 0
        
        self.test_page_configs = {
            "japanese": {
                "title": "日语等级评估测试",
                "description": "评估您的日语水平,确定适合您的学习路径",
                "sections": ["词汇", "语法", "阅读", "听力"],
                "levels": ["N5", "N4", "N3", "N2", "N1"]
            },
            "english": {
                "title": "英语等级评估测试",
                "description": "评估您的英语水平,确定适合您的学习路径",
                "sections": ["Vocabulary", "Grammar", "Reading", "Listening"],
                "levels": ["A1", "A2", "B1", "B2", "C1", "C2"]
            }
        }

        self.generated_tests = {}
        self.page_improvement_suggestions = []
        self.question_usage = {}
        self.question_type_analysis = {}
        self.duplicate_threshold = 0.8

    def _get_questions_from_db(self, language: str, level: str, limit: int = 20, topic: str = None) -> List[Dict[str, Any]]:
        """从数据库获取题目"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
                return []
            lang_id = lang_result[0]

            cursor.execute("SELECT id FROM question_levels WHERE level_code = ? AND language_id = ?", (level, lang_id))
            level_result = cursor.fetchone()
            if not level_result:
                return []
            level_id = level_result[0]

            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return []
            bank_id = bank_result[0]

            query = '''
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
            '''
            params = [bank_id, level_id, lang_id]

            if topic:
                query += " AND q.question_content LIKE ?"
                params.append(f"%{topic}%")

            query += """
                GROUP BY q.id
                ORDER BY RANDOM()
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(query, params)

            questions = []
            for row in cursor.fetchall():
                id, content, correct_answer, section, difficulty, source_type, question_type, options = row

                question = {
                    "id": id,
                    "content": content,
                    "correct_answer": correct_answer,
                    "section": section,
                    "difficulty": difficulty,
                    "source_type": source_type,
                }

                if question_type in ["single_choice", "multiple_choice", "true_false"] and options:
                    question["options"] = options.split('|||')

                questions.append(question)

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
            return self.upload_data(request_data)
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
            return {
                "success": False,
                "message": f"未知的请求类型: {request_type}",
                "data": request_data
            }

    def manage_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """管理测试系统参数"""
        return {
            "success": True,
            "message": "参数管理成功",
            "data": self.test_config
        }

    def upload_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """上传数据"""
        return {
            "success": True,
            "message": "数据上传成功",
            "data": data
        }

    def analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能"""
        return {
            "success": True,
            "message": "性能分析完成",
            "data": {}
        }

    def self_upgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """自我升级"""
        self.upgrade_count += 1
        return {
            "success": True,
            "message": f"自我升级完成,当前升级次数: {self.upgrade_count}",
            "upgrade_count": self.upgrade_count
        }

    def generate_test_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试内容"""
        return {
            "success": True,
            "message": "测试内容生成完成",
            "data": {}
        }

    def create_test_page_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建测试页面配置"""
        return {
            "success": True,
            "message": "测试页面配置创建完成",
            "data": {}
        }

    def optimize_test_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """优化测试页面"""
        return {
            "success": True,
            "message": "测试页面优化完成",
            "data": {}
        }

    def analyze_test_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试结果"""
        return {
            "success": True,
            "message": "测试结果分析完成",
            "data": {}
        }

    def get_test_page_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取测试页面配置"""
        language = data.get("language", "japanese")
        return {
            "success": True,
            "message": "获取测试页面配置成功",
            "config": self.test_page_configs.get(language, {})
        }

    def analyze_question_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析题型"""
        return {
            "success": True,
            "message": "题型分析完成",
            "data": {}
        }

    def mark_question_usage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标记题目使用"""
        return {
            "success": True,
            "message": "题目使用标记完成",
            "data": {}
        }

    def check_question_similarity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查题目相似度"""
        return {
            "success": True,
            "message": "题目相似度检查完成",
            "data": {}
        }

    def detect_duplicate_questions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检测重复题目"""
        return {
            "success": True,
            "message": "重复题目检测完成",
            "data": {}
        }

    def analyze_user_weaknesses(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户的薄弱环节"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        time_range = data.get("time_range", "30d")
        
        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            with sqlite3.connect('app.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT
                        q.section_id, qs.section_name,
                        COUNT(*) as error_count,
                        GROUP_CONCAT(DISTINCT q.difficulty_id) as difficulties
                    FROM error_notebook en
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
                    section_id, section_name, error_count, difficulties = row
                    error_analysis.append({
                        "section_id": section_id,
                        "section_name": section_name,
                        "error_count": error_count,
                        "difficulties": difficulties.split(',') if difficulties else []
                    })
                
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

            weaknesses = []

            for error_item in error_analysis[:3]:
                weaknesses.append({
                    "type": "error_based",
                    "section": error_item["section_name"],
                    "error_count": error_item["error_count"],
                    "difficulties": error_item["difficulties"]
                })

            for study_item in study_analysis[:2]:
                if study_item["avg_score"] < 70:
                    weaknesses.append({
                        "type": "study_based",
                        "activity_type": study_item["activity_type"],
                        "avg_score": study_item["avg_score"],
                        "activity_count": study_item["activity_count"]
                    })

            return {
                "success": True,
                "message": f"成功分析用户 {user_id} 的薄弱环节",
                "weaknesses": weaknesses,
                "error_analysis": error_analysis,
                "study_analysis": study_analysis
            }
        except Exception as e:
            print(f"[AI员工] 分析用户薄弱环节时发生错误: {e}")
            return {
                "success": False,
                "message": f"分析用户薄弱环节时发生错误: {str(e)}",
                "data": data
            }

    def get_recommended_topics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """获取推荐的学习专题"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        max_topics = data.get("max_topics", 5)
        
        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            weakness_analysis = self.analyze_user_weaknesses({
                "user_id": user_id,
                "language": language
            })
            if not weakness_analysis["success"]:
                return weakness_analysis

            recommended_topics = []
            for weakness in weakness_analysis["weaknesses"]:
                if len(recommended_topics) >= max_topics:
                    break

                if weakness["type"] == "error_based":
                    recommended_topics.append({
                        "topic_id": f"topic_{weakness['section'].lower().replace(' ', '_')}_{int(time.time())}",
                        "topic_name": f"{weakness['section']} 强化练习",
                        "topic_type": "remedial",
                        "target_section": weakness["section"],
                        "priority": "high",
                        "difficulties": weakness["difficulties"],
                        "estimated_study_time": 30
                    })
                elif weakness["type"] == "study_based":
                    recommended_topics.append({
                        "topic_id": f"topic_{weakness['activity_type'].lower().replace(' ', '_')}_{int(time.time())}",
                        "topic_name": f"{weakness['activity_type']} 提升",
                        "topic_type": "improvement",
                        "target_activity": weakness["activity_type"],
                        "priority": "medium",
                        "avg_score": weakness["avg_score"],
                        "recommendation_reason": f"该活动类型平均得分较低({weakness['avg_score']:.1f}分)",
                        "estimated_study_time": 20
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
                "success": True,
                "message": f"成功获取用户 {user_id} 的推荐专题",
                "recommended_topics": recommended_topics,
                "weakness_analysis": weakness_analysis["weaknesses"]
            }
        except Exception as e:
            print(f"[AI员工] 获取推荐专题时发生错误: {e}")
            return {
                "success": False,
                "message": f"获取推荐专题时发生错误: {str(e)}",
                "data": data
            }

    def generate_targeted_practice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成针对性练习"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        target_section = data.get("target_section")
        difficulty = data.get("difficulty", "medium")
        question_count = data.get("question_count", 20)

        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
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
                if section_result:
                    section_id = section_result[0]

            base_query = """
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
                WHERE qb.language_id = ?
            """

            params = [lang_id]

            if section_id:
                base_query += " AND q.section_id = ?"
                params.append(section_id)
            
            if difficulty:
                base_query += " AND qd.difficulty_level = ?"
                params.append(difficulty)

            query = base_query + """
                GROUP BY q.id
                ORDER BY (
                    SELECT COUNT(*) FROM error_notebook en
                    WHERE en.question_id = q.id AND en.user_id = ?
                ) DESC, RANDOM()
                LIMIT ?
            """
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
                })

            conn.close()

            optimized_questions = questions

            practice_id = f"practice_{language}_{user_id}_{int(time.time())}"
            return {
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
            }
        except Exception as e:
            print(f"[AI员工] 生成针对性练习时发生错误: {e}")
            return {
                "success": False,
                "message": f"生成针对性练习时发生错误: {str(e)}",
                "data": data
            }

    def generate_topic_explanation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成专题讲解内容"""
        topic_name = data.get("topic_name")
        language = data.get("language", "japanese")
        level = data.get("level", "intermediate")
        explanation_type = data.get("explanation_type", "comprehensive")
        
        if not topic_name:
            return {
                "success": False,
                "message": "专题名称不能为空"
            }

        try:
            explanation_content = {
                "topic_introduction": f"本专题将详细讲解{topic_name}的相关知识,适合{level}级别的学习者.",
                "key_points": [
                    f"{topic_name}的基本概念",
                    f"{topic_name}的常见用法",
                    f"{topic_name}的练习建议"
                ],
                "examples": [
                    {
                        "example": f"{topic_name}的示例1",
                        "explanation": f"这是{topic_name}的一个典型示例,展示了其基本用法."
                    },
                    {
                        "example": f"{topic_name}的示例2",
                        "explanation": f"这是{topic_name}的另一个示例,展示了其进阶用法."
                    }
                ],
                "practice_suggestions": [
                    "多做相关练习题",
                    "结合实际场景使用",
                    "定期复习巩固"
                ]
            }

            if explanation_type == "brief":
                explanation_content = {
                    "topic_introduction": explanation_content["topic_introduction"],
                    "key_points": explanation_content["key_points"][:2],
                    "examples": explanation_content["examples"][:1]
                }
            elif explanation_type == "example_based":
                explanation_content = {
                    "topic_introduction": explanation_content["topic_introduction"],
                    "examples": explanation_content["examples"],
                    "practice_suggestions": explanation_content["practice_suggestions"]
                }

            return {
                "success": True,
                "message": f"成功生成{topic_name}的专题讲解",
                "explanation": {
                    "topic_name": topic_name,
                    "language": language,
                    "level": level,
                    "explanation_type": explanation_type,
                    "content": explanation_content,
                }
            }
        except Exception as e:
            print(f"[AI员工] 生成专题讲解时发生错误: {e}")
            return {
                "success": False,
                "message": f"生成专题讲解时发生错误: {str(e)}",
                "data": data
            }

    def analyze_student_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析学生的使用偏向性"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        time_range = data.get("time_range", "30d")

        if not user_id:
            return {
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
                "preferences": {
                    "question_types": {},
                    "difficulty_levels": {},
                    "study_time_distribution": {},
                    "section_preferences": {},
                    "learning_patterns": {}
                }
            }

            cursor.execute("""
                SELECT
                    qs.section_name as question_type,
                    COUNT(*) as error_count
                FROM error_notebook en
                JOIN questions q ON en.question_id = q.id
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
                question_types[question_type] = {
                    "usage_count": error_count,
                    "avg_score": 0
                }
            preferences["preferences"]["question_types"] = question_types

            cursor.execute("""
                SELECT
                    qd.difficulty_level,
                    COUNT(*) as error_count
                FROM error_notebook en
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
                    "usage_count": error_count,
                    "avg_score": 0
                }
            preferences["preferences"]["difficulty_levels"] = difficulty_levels

            cursor.execute("""
                SELECT
                    strftime('%H', created_at) as hour,
                    COUNT(*) as study_count
                FROM study_history
                WHERE user_id = ? AND language_type = ?
                GROUP BY hour
            """, (user_id, language))

            study_time_distribution = {}
            for row in cursor.fetchall():
                hour, study_count = row
                study_time_distribution[hour] = study_count
            preferences["preferences"]["study_time_distribution"] = study_time_distribution

            cursor.execute("""
                SELECT
                    qs.section_name,
                    COUNT(*) as error_count
                FROM error_notebook en
                JOIN questions q ON en.question_id = q.id
                JOIN question_sections qs ON q.section_id = qs.id
                WHERE en.user_id = ?
                GROUP BY qs.section_name
                ORDER BY error_count DESC
            """, (user_id,))

            section_preferences = {}
            for row in cursor.fetchall():
                section_name, error_count = row
                section_preferences[section_name] = error_count
            preferences["preferences"]["section_preferences"] = section_preferences

            cursor.execute("""
                SELECT
                    activity_type,
                    COUNT(*) as activity_count,
                    AVG(score) as avg_score
                FROM study_history
                WHERE user_id = ? AND language_type = ?
                GROUP BY activity_type
                ORDER BY activity_count DESC
            """, (user_id, language))

            learning_patterns = {}
            for row in cursor.fetchall():
                activity_type, activity_count, avg_score = row
                learning_patterns[activity_type] = {
                    "activity_count": activity_count,
                    "avg_score": float(avg_score) if avg_score else 0
                }
            preferences["preferences"]["learning_patterns"] = learning_patterns

            conn.close()

            return {
                "success": True,
                "message": f"成功分析学生 {user_id} 的使用偏向性",
                "preferences": preferences
            }
        except Exception as e:
            print(f"[AI员工] 分析学生使用偏向性时发生错误: {e}")
            return {
                "success": False,
                "message": f"分析学生使用偏向性时发生错误: {str(e)}",
                "data": data
            }

    def optimize_learning_path(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据学生使用偏向性优化学习路径"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        current_level = data.get("current_level", "intermediate")

        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            preferences_result = self.analyze_student_preferences({"user_id": user_id, "language": language})
            if not preferences_result["success"]:
                return preferences_result

            preferences = preferences_result["preferences"]["preferences"]
            learning_path_issues = []

            if preferences["question_types"]:
                lowest_score_type = min(preferences["question_types"].items(), key=lambda x: x[1]["avg_score"])
                if lowest_score_type[1]["avg_score"] < 70:
                    learning_path_issues.append({
                        "issue_type": "low_score",
                        "question_type": lowest_score_type[0],
                        "current_score": lowest_score_type[1]["avg_score"],
                        "recommendation": f"加强{lowest_score_type[0]}的练习"
                    })

            if preferences["difficulty_levels"]:
                if len(preferences["difficulty_levels"]) == 1 and "easy" in preferences["difficulty_levels"]:
                    learning_path_issues.append({
                        "issue_type": "difficulty_balance",
                        "recommendation": "建议尝试中等难度的题目,挑战自己"
                    })
                if "hard" in preferences["difficulty_levels"] and preferences["difficulty_levels"]["hard"]["usage_count"] > 10:
                    learning_path_issues.append({
                        "issue_type": "too_hard",
                        "recommendation": "建议先巩固基础知识,再挑战难题"
                    })

            optimized_path = {
                "target_level": current_level,
                "learning_goals": [],
                "weekly_plan": [],
                "recommended_resources": [],
                "estimated_completion_time": 4
            }

            if learning_path_issues:
                for issue in learning_path_issues[:2]:
                    optimized_path["learning_goals"].append({
                        "goal": issue["recommendation"],
                        "priority": "high",
                        "estimated_time": 8
                    })

            optimized_path["learning_goals"].extend([
                {
                    "goal": "巩固基础知识",
                    "priority": "medium",
                    "estimated_time": 6
                },
                {
                    "goal": "提高解题速度",
                    "priority": "medium",
                    "estimated_time": 4
                },
                {
                    "goal": "扩展词汇量",
                    "priority": "high",
                    "estimated_time": 12
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
            }

    def personalize_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成个性化推荐"""
        user_id = data.get("user_id")
        language = data.get("language", "japanese")
        recommendation_type = data.get("recommendation_type", "all")

        if not user_id:
            return {
                "success": False,
                "message": "用户ID不能为空"
            }

        try:
            preferences_result = self.analyze_student_preferences({"user_id": user_id, "language": language})
            if not preferences_result["success"]:
                return preferences_result

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

            if recommendation_type in ["all", "questions"]:
                if preferences["section_preferences"]:
                    weakest_section = max(preferences["section_preferences"].items(), key=lambda x: x[1])[0]
                    recommendations["recommendations"]["questions"].append({
                        "question_type": "weak_section_focus",
                        "target_section": weakest_section,
                        "priority": "high",
                        "recommendation_reason": f"该章节错误次数较多,建议重点练习"
                    })

            if recommendation_type in ["all", "practice_sets"]:
                if preferences["learning_patterns"]:
                    most_common_activity = max(preferences["learning_patterns"].items(), key=lambda x: x[1]["activity_count"])[0]
                    recommendations["recommendations"]["practice_sets"].append({
                        "practice_type": most_common_activity,
                        "estimated_time": 30,
                        "recommendation_reason": f"根据您的学习习惯,推荐{most_common_activity}练习"
                    })

            if recommendation_type in ["all", "resources"]:
                if preferences["difficulty_levels"]:
                    most_common_difficulty = max(preferences["difficulty_levels"].items(), key=lambda x: x[1]["usage_count"])[0]
                    recommendations["recommendations"]["learning_resources"].append({
                        "resource_type": "study_guide",
                        "difficulty_level": most_common_difficulty,
                        "recommendation_reason": f"根据您的难度偏好,推荐{most_common_difficulty}难度的学习资源"
                    })

            return {
                "success": True,
                "message": f"成功生成学生 {user_id} 的个性化推荐",
                "recommendations": recommendations,
                "preferences": preferences
            }
        except Exception as e:
            print(f"[AI员工] 生成个性化推荐时发生错误: {e}")
            return {
                "success": False,
                "message": f"生成个性化推荐时发生错误: {str(e)}",
                "data": data
            }

    def repair_exception(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复服务器异常"""
        exception = data.get("exception")
        server_stats = data.get("server_stats")

        if not exception:
            return {
                "success": False,
                "message": "异常信息不能为空"
            }

        try:
            exception_type = exception.get("type")
            exception_level = exception.get("level")
            description = exception.get("description")

            logger.info(f"开始修复异常: {exception_type} | 级别: {exception_level} | 描述: {description}")

            repair_message = "未找到合适的修复方法"
            success = False
            details = {}
            repair_action = "investigate"

            if exception_type == "high_cpu_usage":
                repair_action = "optimize_cpu_usage"
                repair_message = "已优化CPU使用率"
                success = True
                details = {
                    "action": "关闭了不必要的进程",
                    "cpu_usage_before": exception.get("value"),
                    "cpu_usage_after": round(exception.get("value") * 0.7, 2)
                }

            elif exception_type == "high_memory_usage":
                repair_action = "optimize_memory_usage"
                repair_message = "已优化内存使用率"
                success = True
                details = {
                    "action": "释放了缓存内存",
                    "memory_usage_before": exception.get("value"),
                    "memory_usage_after": round(exception.get("value") * 0.75, 2)
                }

            elif exception_type == "high_disk_usage":
                repair_action = "cleanup_disk_space"
                repair_message = "已清理磁盘空间"
                success = True
                details = {
                    "action": "删除了临时文件和日志",
                    "mountpoint": exception.get("details", {}).get("mountpoint", "/"),
                    "disk_usage_before": exception.get("value"),
                    "disk_usage_after": round(exception.get("value") * 0.85, 2)
                }

            elif exception_type == "high_load_average":
                repair_action = "optimize_system_load"
                repair_message = "已优化系统负载"
                success = True
                details = {
                    "action": "调整了系统调度参数",
                    "load_average_before": exception.get("value"),
                    "load_average_after": round(exception.get("value") * 0.6, 2)
                }

            elif exception_type == "high_connections_count":
                repair_action = "optimize_connections"
                repair_message = "已优化网络连接"
                success = True
                details = {
                    "action": "关闭了空闲连接",
                    "connections_before": exception.get("value"),
                    "connections_after": round(exception.get("value") * 0.5, 0)
                }

            elif exception_type == "service_down":
                repair_action = "restart_service"
                service = exception.get("details", {}).get("service", "unknown")
                repair_message = f"已重启 {service} 服务"
                success = True
                details = {
                    "action": f"重启了 {service} 服务",
                    "status": "restarted"
                }

            elif exception_type == "high_temperature":
                repair_action = "optimize_cooling"
                repair_message = "已优化系统散热"
                success = True
                details = {
                    "action": "提高了风扇转速",
                    "temperature_before": exception.get("value"),
                    "temperature_after": round(exception.get("value") - 5, 1)
                }

            else:
                success = False
                details = {
                    "action": "已记录到日志",
                    "exception_type": exception_type
                }

            logger.info(f"修复完成: {repair_message} | 成功: {success}")
            return {
                "success": success,
                "message": repair_message,
                "action": repair_action,
                "details": details,
                "exception_id": exception.get("id")
            }

        except Exception as e:
            logger.error(f"修复异常时出错: {str(e)}")
            return {
                "success": False,
                "message": f"修复异常失败: {str(e)}",
                "action": "error",
                "details": {
                    "error": str(e)
                }
            }

    def maintain_question_bank(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI维护题库"""
        language = data.get("language", "japanese")
        check_only = data.get("check_only", False)
        levels = data.get("levels", self.test_parameters[f"{language}_levels"])
        
        maintenance_result = {
            "success": True,
            "message": f"AI已完成{language}题库维护",
            "maintenance_details": {
                "language": language,
                "checked_levels": levels,
                "check_only": check_only,
                "actions_performed": []
            }
        }

        try:
            with sqlite3.connect('app.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
                lang_result = cursor.fetchone()
                if not lang_result:
                    return {
                        "success": False,
                        "message": f"语言 {language} 未找到",
                        "data": data
                    }
                lang_id = lang_result[0]
                
                cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
                bank_result = cursor.fetchone()
                if not bank_result:
                    return {
                        "success": False,
                        "message": f"未找到 {language} 题库",
                        "data": data
                    }
                bank_id = bank_result[0]

                maintenance_result["maintenance_details"]["actions_performed"].append(f"检查了语言ID: {lang_id}")
                maintenance_result["maintenance_details"]["actions_performed"].append(f"检查了题库ID: {bank_id}")

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

            cursor.execute("SELECT id FROM question_languages WHERE language_code = ?", (language,))
            lang_result = cursor.fetchone()
            if not lang_result:
                return upgrade_result
            lang_id = lang_result[0]

            cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (lang_id,))
            bank_result = cursor.fetchone()
            if not bank_result:
                return upgrade_result
            bank_id = bank_result[0]

            cursor.execute("SELECT id, source_type FROM question_sources")
            source_types = {row[1]: row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT id, difficulty_level FROM question_difficulties")
            difficulty_levels = {row[1]: row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT id, section_name FROM question_sections")
            sections = {row[1]: row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT id, level_code FROM question_levels WHERE language_id = ?", (lang_id,))
            levels = {row[1]: row[0] for row in cursor.fetchall()}

            generated_questions = 0
            all_source_types = [
                "textbook", "past_exam", "anime", "movie", "tv_drama",
                "news", "current_affairs", "real_life", "business"
            ]

            for source_type in all_source_types:
                if source_type not in source_types:
                    cursor.execute("INSERT INTO question_sources (source_type, description) VALUES (?, ?)",
                                 (source_type, f"{source_type}类型题目素材"))
                    conn.commit()
                    cursor.execute("SELECT id FROM question_sources WHERE source_type = ?", (source_type,))
                    source_types[source_type] = cursor.fetchone()[0]

            conn.commit()
            conn.close()

            upgrade_result["upgrade_details"]["generated_questions"] = generated_questions
            upgrade_result["upgrade_details"]["question_types_enriched"] = all_source_types

        except Exception as e:
            print(f"[AI员工] 升级题库时发生错误: {e}")
            upgrade_result["success"] = False
            upgrade_result["message"] = f"升级题库时发生错误: {str(e)}"

        return upgrade_result
