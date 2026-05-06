#!/usr/bin/env python3
"""
测试优化后的考试系统功能

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.error_question import error_question_manager
from app.ai.teacher_ai import teacher_ai_map
from app.models.learning_analysis import learning_analysis_manager

class TestOptimizedExamSystem(unittest.TestCase):
    """测试优化后的考试系统功能"""

    def setUp(self):
        """设置测试环境"""
        self.user_id = 1
        self.question_id = 1
        self.exam_record_id = 1
        self.error_question_id = None

    def test_error_question_management(self):
        """测试错题管理功能"""
        print("测试错题管理功能...")

        # 测试添加错题
        error_id = error_question_manager.add_error_question(
            user_id=self.user_id,
            question_id=self.question_id,
            exam_record_id=self.exam_record_id,
            user_answer="选项B",
            correct_answer="选项A",
            error_reason="对知识点理解不透彻",
            error_type="conceptual",
            tags=["概念理解", "基础知识点"],
            knowledge_point="代数",
            difficulty_level=3
        )

        self.assertGreater(error_id, 0, "添加错题失败")
        self.error_question_id = error_id
        print(f"✓ 添加错题成功，ID: {error_id}")

        # 测试获取用户错题列表
        error_questions = error_question_manager.get_user_error_questions(self.user_id, limit=10)
        self.assertIsInstance(error_questions, list, "获取错题列表失败")
        self.assertGreater(len(error_questions), 0, "错题列表为空")
        print(f"✓ 获取错题列表成功，数量: {len(error_questions)}")

        # 测试更新掌握程度
        success = error_question_manager.update_mastery_level(error_id, 3)
        self.assertTrue(success, "更新掌握程度失败")
        print("✓ 更新掌握程度成功")

        # 测试复习错题
        success = error_question_manager.review_error_question(error_id, "已理解，掌握了相关知识点")
        self.assertTrue(success, "复习错题失败")
        print("✓ 复习错题成功")

        # 测试获取错题统计信息
        statistics = error_question_manager.get_error_question_statistics(self.user_id)
        self.assertIsInstance(statistics, dict, "获取错题统计信息失败")
        self.assertIn('total_count', statistics, "统计信息缺少total_count字段")
        print("✓ 获取错题统计信息成功")

        print("错题管理功能测试通过!")

    def test_teacher_ai_functionality(self):
        """测试老师AI功能"""
        print("\n测试老师AI功能...")

        # 确保有错题用于测试
        if not self.error_question_id:
            error_id = error_question_manager.add_error_question(
                question_id=self.question_id,
                user_answer="选项B",
                error_reason="对知识点理解不透彻",
                tags=["概念理解", "基础知识点"],
                difficulty_level=3
            self.error_question_id = error_id
        # 测试数学老师AI分析错题
        self.assertIsNotNone(math_teacher, "数学老师AI不存在")
        analysis_result = math_teacher.analyze_error_question(self.error_question_id, self.user_id)
        self.assertIn('error_reason', analysis_result, "分析结果缺少error_reason字段")
        print("✓ 老师AI分析错题成功")

        feedback = math_teacher.provide_feedback(self.user_id, self.error_question_id, analysis_result)
        self.assertIsInstance(feedback, dict, "提供反馈失败")
        self.assertIn('content', feedback, "反馈缺少content字段")
        print("✓ 老师AI提供反馈成功")

        # 测试老师AI生成练习题目
        practice_questions = math_teacher.generate_practice_questions(
            user_id=self.user_id,
            knowledge_points=["代数", "几何"],
            count=3,
            question_types=["multiple_choice", "fill_blank"]
        )
        self.assertIsInstance(practice_questions, list, "生成练习题目失败")
        self.assertEqual(len(practice_questions), 3, "生成的题目数量不正确")
        print("✓ 老师AI生成练习题目成功")

        # 测试老师AI跟踪学生进度
        progress = math_teacher.track_student_progress(self.user_id)
        self.assertIsInstance(progress, dict, "跟踪学生进度失败")
        self.assertIn('statistics', progress, "进度报告缺少statistics字段")
        print("✓ 老师AI跟踪学生进度成功")

        print("老师AI功能测试通过!")

    def test_learning_analysis(self):
        """测试学习分析功能"""
        print("\n测试学习分析功能...")

        # 测试添加学习活动
        activity_id = learning_analysis_manager.add_learning_activity(
            user_id=self.user_id,
            activity_type="practice",
                "subject": "数学",
                "completion_rate": 0.8,
                "accuracy": 0.7
            },
            duration=300
        )
        self.assertGreater(activity_id, 0, "添加学习活动失败")
        print(f"✓ 添加学习活动成功，ID: {activity_id}")

        # 测试分析学习兴趣
        interest_analysis = learning_analysis_manager.analyze_learning_interest(self.user_id)
        self.assertIsInstance(interest_analysis, dict, "分析学习兴趣失败")
        self.assertIn('interest_scores', interest_analysis, "兴趣分析缺少interest_scores字段")
        print("✓ 分析学习兴趣成功")

        # 测试分析学习方向
        direction_analysis = learning_analysis_manager.analyze_learning_direction(self.user_id)
        self.assertIsInstance(direction_analysis, dict, "分析学习方向失败")
        self.assertIn('directions', direction_analysis, "方向分析缺少directions字段")
        print("✓ 分析学习方向成功")

        # 测试分析学习进度
        progress_analysis = learning_analysis_manager.analyze_learning_progress(self.user_id)
        self.assertIsInstance(progress_analysis, dict, "分析学习进度失败")
        self.assertIn('progress', progress_analysis, "进度分析缺少progress字段")
        print("✓ 分析学习进度成功")

        # 测试分析学习优势和劣势
        strength_weakness_analysis = learning_analysis_manager.analyze_strengths_weaknesses(self.user_id)
        self.assertIsInstance(strength_weakness_analysis, dict, "分析优势和劣势失败")
        self.assertIn('strengths', strength_weakness_analysis, "优势劣势分析缺少strengths字段")
        self.assertIn('weaknesses', strength_weakness_analysis, "优势劣势分析缺少weaknesses字段")
        print("✓ 分析学习优势和劣势成功")

        # 测试生成综合学习报告
        comprehensive_report = learning_analysis_manager.generate_comprehensive_report(self.user_id)
        self.assertIsInstance(comprehensive_report, dict, "生成综合学习报告失败")
        self.assertIn('interest_analysis', comprehensive_report, "综合报告缺少interest_analysis字段")
        self.assertIn('direction_analysis', comprehensive_report, "综合报告缺少direction_analysis字段")
        self.assertIn('progress_analysis', comprehensive_report, "综合报告缺少progress_analysis字段")
        self.assertIn('strength_weakness_analysis', comprehensive_report, "综合报告缺少strength_weakness_analysis字段")
        self.assertIn('learning_style_analysis', comprehensive_report, "综合报告缺少learning_style_analysis字段")
        self.assertIn('learning_goals', comprehensive_report, "综合报告缺少learning_goals字段")
        self.assertIn('learning_plan', comprehensive_report, "综合报告缺少learning_plan字段")
        self.assertIn('recommendations', comprehensive_report, "综合报告缺少recommendations字段")
        self.assertIn('next_steps', comprehensive_report, "综合报告缺少next_steps字段")
        print("✓ 生成综合学习报告成功")

        print("学习分析功能测试通过!")

    def test_exam_system_integration(self):
        """测试考试系统集成功能"""
        print("\n测试考试系统集成功能...")

        # 测试完整的错题处理流程
        # 1. 添加错题
        error_id = error_question_manager.add_error_question(
            question_id=self.question_id + 1,
            exam_record_id=self.exam_record_id,
            correct_answer="选项A",
            error_reason="计算错误",
            error_type="calculation",
            tags=["计算错误", "代数"],
            knowledge_point="代数",
            difficulty_level=4
        self.assertGreater(error_id, 0, "添加错题失败")

        # 2. 老师AI分析
        math_teacher = teacher_ai_map.get('math')
        self.assertIsInstance(analysis_result, dict, "分析错题失败")

        # 3. 老师AI提供反馈
        feedback = math_teacher.provide_feedback(self.user_id, error_id, analysis_result)
        self.assertIsInstance(feedback, dict, "提供反馈失败")

        # 4. 生成练习题目
        practice_questions = math_teacher.generate_practice_questions(
            knowledge_points=["代数"],
            difficulty="medium",
        )
        self.assertEqual(len(practice_questions), 2, "生成练习题目失败")

        comprehensive_report = learning_analysis_manager.generate_comprehensive_report(self.user_id)
        self.assertIsInstance(comprehensive_report, dict, "生成综合学习报告失败")

        print("✓ 考试系统集成功能测试成功")

if __name__ == "__main__":
    unittest.main()
