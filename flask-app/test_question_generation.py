#!/usr/bin/env python3
"""
测试题目生成功能
"""

import sys
import os
import random

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import Question

class TestQuestionGenerator:
    """
    测试题目生成器
    """
    
    def __init__(self):
        """
        初始化测试题目生成器
        """
        # 9年制义务教育的版本信息
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
            "subjects": ["数学", "英语", "语文"]
        }
    
    def generate_test_question(self):
        """
        生成测试题目
        
        Returns:
            Question: 生成的题目
        """
        # 确定题目类型
        exam_types = ["中考题", "高考题", "压轴题"]
        exam_type = random.choice(exam_types)
        
        # 确定版本
        version = random.choice(self._nine_year_education["versions"])
        
        # 确定年级
        grade = random.choice(self._nine_year_education["grades"])
        
        # 随机选择学科
        subject = random.choice(self._nine_year_education["subjects"])
        
        # 生成题目内容
        if subject == "数学":
            # 生成数学题目
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
                content = f"{a} {operation} {b} 的结果是多少？"
            
            # 生成选项
            options = [answer]
            while len(options) < 4:
                wrong_answer = answer + random.randint(-5, 5)
                if wrong_answer != answer and wrong_answer >= 0:
                    options.append(wrong_answer)
            random.shuffle(options)
            
            # 创建题目
            question = Question(
                content=f"[{version}][{grade}][{exam_type}][{subject}] {content}",
                question_type="single_choice",
                language_id=3,  # 中文
                level_id=1,
                category_id=1,
                options=options,
                answer=str(options.index(answer)),
                explanation=f"{a} {operation} {b} = {answer}",
                difficulty_score=1.0
            )
        elif subject == "英语":
            # 生成英语题目
            words = ["cat", "dog", "book", "house", "school"]
            word = random.choice(words)
            content = f"选择{word}的正确中文意思"
            
            # 生成选项
            options = ["选项1", "选项2", "选项3", "选项4"]
            correct_answer = str(random.randint(0, 3))
            
            # 创建题目
            question = Question(
                content=f"[{version}][{grade}][{exam_type}][{subject}] {content}",
                question_type="single_choice",
                language_id=3,  # 中文
                level_id=1,
                category_id=1,
                options=options,
                answer=correct_answer,
                explanation=f"{word}的正确意思是{options[int(correct_answer)]}",
                difficulty_score=1.0
            )
        else:  # 语文
            # 生成语文题目
            words = ["美丽", "漂亮", "好看", "美观"]
            word = random.choice(words)
            content = f"选择与{word}意思最接近的词语"
            
            # 生成选项
            options = ["美丽", "漂亮", "好看", "美观"]
            random.shuffle(options)
            correct_answer = str(options.index(word))
            
            # 创建题目
            question = Question(
                content=f"[{version}][{grade}][{exam_type}][{subject}] {content}",
                question_type="single_choice",
                language_id=3,  # 中文
                level_id=1,
                category_id=1,
                options=options,
                answer=correct_answer,
                explanation=f"{word}的意思是{word}",
                difficulty_score=1.0
            )
        
        return question

def test_question_generation():
    """
    测试题目生成功能
    """
    print("测试题目生成功能")
    print("=" * 50)
    
    generator = TestQuestionGenerator()
    
    # 生成10道测试题目
    for i in range(10):
        question = generator.generate_test_question()
        print(f"题目 {i+1}: {question.content}")
        print(f"选项: {question.options}")
        print(f"答案: {question.answer}")
        print("-" * 50)

if __name__ == "__main__":
    test_question_generation()
