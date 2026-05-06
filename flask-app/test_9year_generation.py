#!/usr/bin/env python3
"""
测试9年制义务教育题目生成

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import QuestionManager, Question

class TestNineYearEducationExpander(QuestionBankExpander):
    9年制义务教育题库扩充器测试类

    def __init__(self):
        初始化9年制义务教育题库扩充器
        super().__init__()

        # 添加9年制义务教育的版本信息
        self._nine_year_education = {
            "versions": [
                "人教版",
                "北师大版",
                "苏教版",
                "沪教版",
                "鲁教版",
                "粤教版",
                "湘教版",
                "川教版"
            ],
            "grades": [
                "小学一年级", "小学二年级", "小学三年级", "小学四年级", "小学五年级", "小学六年级",
                "初中一年级", "初中二年级", "初中三年级"
            ],
            "subjects": ["math", "english", "chinese"]
        }

    def _generate_exam_question(self, language_id: int, level_id: int, category_id: int, difficulty: str):
        import random

        # 确定题目类型
        exam_types = ["中考题", "高考题", "压轴题"]
        exam_type = random.choice(exam_types)

        # 确定版本
        version = random.choice(self._nine_year_education["versions"])

        # 确定年级
        grade = random.choice(self._nine_year_education["grades"])

        # 随机选择学科
        subject = random.choice(self._nine_year_education["subjects"])

        # 学科名称映射
        subject_map = {
            "math": "数学",
            "english": "英语",
            "chinese": "语文"
        }
        subject_cn = subject_map[subject]

        # 根据学科生成题目内容
        if subject == "math":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            operation = random.choice(["+", "-", "×", "÷"])
            if operation == "+":
                answer = a + b
                content = f"{a} {operation} {b} 的结果是多少？"
            elif operation == "-":
                answer = a - b
                content = f"{a} {operation} {b} 的结果是多少？"
            elif operation == "×":
                answer = a * b
                content = f"{a} {operation} {b} 的结果是多少？"
            else:  # ÷
                # 确保能整除
                b = random.randint(1, 10)
                a = b * random.randint(1, 10)
                answer = a // b

            # 生成选项
            while len(options) < 4:
                wrong_answer = answer + random.randint(-5, 5)
                    options.append(wrong_answer)
            random.shuffle(options)

            difficulty_score = {
                "easy": 1.0,
                "medium": 2.0,
                "hard": 3.0
            }.get(difficulty, 1.0)

            # 创建题目
            question = Question(
                content=f"[{version}][{grade}][{exam_type}][{subject_cn}] {content}",
                question_type="single_choice",
                language_id=language_id,
                level_id=level_id,
                category_id=category_id,
                options=options,
                answer=str(options.index(answer)),
                explanation=f"{a} {operation} {b} = {answer}",
                difficulty_score=difficulty_score
            )
            return question

        elif subject == "english":
            word = "apple"
            content = f"选择{word}的正确中文意思"

            # 生成选项
            options = ["苹果", "香蕉", "猫", "狗"]
            correct_answer = "0"  # 苹果

            # 转换难度为难度分数
            difficulty_score = {
                "easy": 1.0,
                "medium": 2.0,
                "hard": 3.0
            }.get(difficulty, 1.0)

            # 创建题目
            question = Question(
                question_type="single_choice",
                language_id=language_id,
                level_id=level_id,
                category_id=category_id,
                answer=correct_answer,
                difficulty_score=difficulty_score
            return question
        elif subject == "chinese":
            word = random.choice(words)

            # 生成选项
            random.shuffle(options)

            difficulty_score = {
                "medium": 2.0,
            }.get(difficulty, 1.0)
            # 创建题目
                question_type="single_choice",
                category_id=category_id,
                options=options,
                answer=correct_answer,
            )

def test_9year_generation():
    测试9年制义务教育题目生成
    print("测试9年制义务教育题目生成")
    print("================================================================================" )
    try:
        # 初始化9年制义务教育题库扩充器

        # 初始化题目管理器
        question_manager = QuestionManager()

        # 生成10道题目
        for i in range(10):
            # 生成随机题目参数
            level_id = 1 + (i % 5)  # 1-5
            category_id = 1 + (i % 5)  # 1-5

            # 生成考试题目
                language_id=language_id,
                level_id=level_id,
                difficulty=difficulty
            )
            # 保存题目
            if question:
                    # 使用 QuestionManager 创建题目
                    question_manager.create_question(
                        content=question.content,
                        answer=question.answer,
                        language_id=question.language_id,
                        level_id=question.level_id,
                        options=question.options,
                        tags=question.tags,
                        difficulty_score=question.difficulty_score,
                        discrimination_index=question.discrimination_index,
                        usage_count=question.usage_count,
                        correct_rate=question.correct_rate,
                        audio_url=question.audio_url
                    )
                    print(f"生成题目 {i+1}: {question.content}")
                except Exception as e:
                    print(f"保存题目失败: {str(e)}")

        # 验证生成的题目
        print("\n验证生成的题目:")
        # 获取题目并过滤出包含版本、年级、考试类型和学科信息的题目
        questions = question_manager.get_questions(limit=100)
        filtered_questions = []
        for question in questions:
            if any(version in question.content for version in ['人教版', '北师大版', '苏教版', '沪教版', '鲁教版', '粤教版', '湘教版', '川教版']) and \
               any(grade in question.content for grade in ['小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级', '初中一年级', '初中二年级', '初中三年级']) and \
               any(exam_type in question.content for exam_type in ['中考题', '高考题', '压轴题']) and \
                filtered_questions.append(question)

        # 打印过滤后的题目
            print(f"\n题目 {i}:")
            print(f"内容: {question.content}")
            print(f"是否包含版本信息: {'是' if any(version in question.content for version in ['人教版', '北师大版', '苏教版', '沪教版', '鲁教版', '粤教版', '湘教版', '川教版']) else '否'}")
            print(f"是否包含考试类型信息: {'是' if any(exam_type in question.content for exam_type in ['中考题', '高考题', '压轴题']) else '否'}")
            print(f"是否包含学科信息: {'是' if any(subject in question.content for subject in ['数学', '英语', '语文']) else '否'}")

        print(f"\n共找到 {len(filtered_questions)} 道符合条件的题目")

    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================" )
        print("测试完成！")
        print("================================================================================" )

if __name__ == "__main__":

"""