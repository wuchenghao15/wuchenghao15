# -*- coding: utf-8 -*-
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'flask-app')))

from app.ai.exam_ai import exam_ai
from app.utils.exam_rule_manager import exam_rule_manager
from app.utils.exam_permission_manager import exam_permission_manager
from app.utils.route_manager import route_manager
from app.services.exam_service import get_exam_service

class TestExamSystem(unittest.TestCase):
    """测试考试系统的各项功能"""

    def setUp(self):
        """设置测试环境"""
        self.exam_service = get_exam_service()

    def test_exam_ai(self):
        """测试考试系统AI"""
        print("测试考试系统AI...")

        # 测试生成题目
        question = exam_ai.generate_question(
            topic="数学",
            question_type="multiple_choice",
            difficulty="medium",
            education_version="middle"
        )

        self.assertIsInstance(question, dict)
        self.assertIn("id", question)
        self.assertIn("content", question)
        self.assertIn("options", question)
        self.assertIn("correct_answer", question)

        # 测试创建考试
        exam = exam_ai.create_exam(
            name="数学测试",
            questions=[question["id"]],
            education_version="middle",
            time_limit=60

        self.assertIsInstance(exam, dict)
        self.assertIn("id", exam)
        self.assertIn("name", exam)
        self.assertIn("questions", exam)

        # 测试评分考试
        answers = {question["id"]: "选项A"}
        correct_answers = {question["id"]: "选项A"}
        evaluation = exam_ai.score_exam(exam["id"], answers, correct_answers)

        self.assertIsInstance(evaluation, dict)
        self.assertIn("score", evaluation)
        self.assertIn("accuracy", evaluation)

        # 测试分析学习模式
        learning_patterns = exam_ai.analyze_learning_patterns("student1", [evaluation])

        self.assertIsInstance(learning_patterns, dict)
        self.assertIn("user_id", learning_patterns)
        self.assertIn("average_score", learning_patterns)

        # 测试检测作弊行为
        exam_behavior = [
            {"action_type": "answer", "time_spent": 5, "question_id": question["id"]}
        ]
        cheating_detection = exam_ai.detect_cheating("student1", exam["id"], exam_behavior)

        self.assertIsInstance(cheating_detection, dict)
        self.assertIn("suspicious_activities", cheating_detection)
        self.assertIn("risk_score", cheating_detection)

        # 测试生成自适应测试
        adaptive_test = exam_ai.generate_adaptive_test(
            user_id="student1",
            initial_difficulty="medium",
            target_score=80.0
        )
        self.assertIsInstance(adaptive_test, dict)
        self.assertIn("id", adaptive_test)
        self.assertIn("name", adaptive_test)
        self.assertIn("questions", adaptive_test)

        # 测试提供反馈
        feedback = exam_ai.provide_feedback("student1", exam["id"], evaluation)

        self.assertIsInstance(feedback, dict)
        self.assertIn("user_id", feedback)
        self.assertIn("score", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("weaknesses", feedback)

        print("考试系统AI测试通过!")

    def test_exam_rule_manager(self):
        """测试考试规则管理器"""
        print("\n测试考试规则管理器...")

        # 测试获取规则
        question_generation_rules = exam_rule_manager.get_rules("question_generation")
        self.assertIsInstance(question_generation_rules, dict)
        self.assertIn("min_length", question_generation_rules)

        # 测试设置规则
        exam_rule_manager.set_rule("question_generation", "min_length", 20)
        updated_min_length = exam_rule_manager.get_rule("question_generation", "min_length")
        self.assertEqual(updated_min_length, 20)

        # 测试检查题目生成规则
        question = {
            "content": "关于数学的选择题，内容长度足够长，确保符合规则要求",
            "type": "multiple_choice",
            "difficulty": "medium",
            "education_version": "middle",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "选项A"
        }
        question_check = exam_rule_manager.check_question_generation(question)
        self.assertIsInstance(question_check, dict)
        self.assertEqual(question_check["success"], True)

        # 测试检查考试创建规则
        exam = {
            "name": "数学测试",
            "questions": ["q1", "q2", "q3", "q4", "q5"],
            "education_version": "middle",
            "time_limit": 60
        }
        self.assertIsInstance(exam_check, dict)
        self.assertEqual(exam_check["success"], True)
        # 测试检查评分规则
        score_check = exam_rule_manager.check_scoring(85)
        self.assertIsInstance(score_check, dict)
        self.assertEqual(score_check["success"], True)
        self.assertEqual(score_check["grade"], "良好")

        print("考试规则管理器测试通过!")

    def test_exam_permission_manager(self):
        """测试考试权限管理器"""
        print("\n测试考试权限管理器...")

        # 测试获取权限
        admin_permissions = exam_permission_manager.get_permissions("admin")
        self.assertIsInstance(admin_permissions, list)
        self.assertIn("manage_system", admin_permissions)

        # 测试检查权限
        has_admin_permission = exam_permission_manager.has_permission("admin", "manage_system")
        self.assertTrue(has_admin_permission)

        has_student_permission = exam_permission_manager.has_permission("student", "manage_system")
        self.assertFalse(has_student_permission)

        # 测试检查考试访问权限
        admin_exam_access = exam_permission_manager.check_exam_access("admin", "exam1", "edit")
        self.assertTrue(admin_exam_access)

        student_exam_access = exam_permission_manager.check_exam_access("student", "exam1", "take")
        self.assertTrue(student_exam_access)

        # 测试检查题目访问权限
        admin_question_access = exam_permission_manager.check_question_access("admin", "q1", "edit")
        self.assertTrue(admin_question_access)

        student_question_access = exam_permission_manager.check_question_access("student", "q1", "edit")
        self.assertFalse(student_question_access)

        print("考试权限管理器测试通过!")

    def test_route_manager(self):
        """测试路由管理器"""
        print("\n测试路由管理器...")

        # 测试获取路由
        login_route = route_manager.get_route("auth", "login")
        self.assertEqual(login_route, "/login")

        register_route = route_manager.get_route("auth", "register")
        self.assertEqual(register_route, "/register")

        # 测试获取路由权限
        login_permissions = route_manager.get_route_permissions("auth.login")
        self.assertIsInstance(login_permissions, list)

        admin_center_permissions = route_manager.get_route_permissions("main.admin_center")
        self.assertIsInstance(admin_center_permissions, list)
        self.assertIn("admin", admin_center_permissions)

        # 测试检查路由权限
        admin_has_access = route_manager.check_route_permission("main.admin_center", "admin", ["admin"])
        self.assertTrue(admin_has_access)

        user_has_access = route_manager.check_route_permission("main.admin_center", "user", ["user"])
        self.assertFalse(user_has_access)

        print("路由管理器测试通过!")

    def test_exam_service(self):
        """测试考试服务"""
        print("\n测试考试服务...")

        # 测试使用AI生成题目
        question = self.exam_service.generate_question_with_ai(
            question_type="multiple_choice",
            difficulty="medium",
        )
        self.assertIsInstance(question, dict)

        question["content"] = "关于数学的选择题，内容长度足够长，确保符合规则要求"

        # 测试使用AI创建考试
        # 生成5道题目，确保符合题目数量要求
        for i in range(5):
                question_type="multiple_choice",
                difficulty="medium",
                education_version="middle"
            q["content"] = "关于数学的选择题，内容长度足够长，确保符合规则要求"
            questions.append(q["id"])
        exam = self.exam_service.create_exam_with_ai(
            name="数学测试",
            education_version="middle",
            time_limit=60

        self.assertIsInstance(exam, dict)
        self.assertIn("id", exam)

        # 测试检查题目生成规则
        print(f"修改后的题目: {question}")
        question_check = self.exam_service.check_question_generation_rules(question)
        print(f"题目检查结果: {question_check}")
        self.assertEqual(question_check["success"], True)

        print(f"修改后的考试: {exam}")
        exam_check = self.exam_service.check_exam_creation_rules(exam)
        self.assertIsInstance(exam_check, dict)

        # 测试检查评分规则
        score_check = self.exam_service.check_scoring_rules(85)
        self.assertEqual(score_check["success"], True)
        # 测试检查考试访问权限
        admin_exam_access = self.exam_service.check_exam_access("admin", "exam1", "edit")

        # 测试检查题目访问权限
        admin_question_access = self.exam_service.check_question_access("admin", "q1", "edit")
        self.assertTrue(admin_question_access)

        # 测试获取用户权限
        self.assertIsInstance(admin_permissions, list)
        # 测试检查权限
        has_admin_permission = self.exam_service.has_permission("admin", "manage_system")

        print("考试服务测试通过!")

if __name__ == "__main__":
    unittest.main()
