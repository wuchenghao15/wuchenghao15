#!/usr/bin/env python3
# 简化的测试脚本，只生成10道题目

import sys
sys.path.append('.')

from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import Question
from app.models.question import QuestionManager
import random
from typing import Optional

class SimpleNineYearEducationExpander(QuestionBankExpander):
    def __init__(self):
        super().__init__()
        # 9年义务教育相关信息
        self._nine_year_education = {
            "versions": ["人教版", "北师大版", "苏教版", "沪教版", "鲁教版", "粤教版", "湘教版", "川教版"],
            "grades": ["小学一年级", "小学二年级", "小学三年级", "小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级", "初中三年级"],
            "exam_types": ["中考题", "高考题", "压轴题"],
            "subjects": ["math", "english", "chinese"]
        }
        # 9年义务教育题目模板
        self.question_templates = {
            "math": [
                "计算：{num1} + {num2} = ?",
                "解方程：{num1}x + {num2} = {num3}",
                "计算：{num1} × {num2} = ?",
                "计算：{num1} ÷ {num2} = ?"
            ],
            "english": [
                "选择{word}的正确中文意思",
                "选择正确的单词填空：{sentence}",
                "翻译：{english_phrase}",
                "选择正确的时态：{sentence}"
            ],
            "chinese": [
                "选择正确的汉字：{phrase}",
                "解释成语：{idiom}",
                "选择正确的标点符号：{sentence}",
                "填写诗句：{poem}"
            ]
        }
    
    def _generate_exam_question(self, language_id: int, level_id: int, category_id: int, difficulty: str) -> Optional[Question]:
        # 确定题目类型
        exam_type = random.choice(self._nine_year_education["exam_types"])
        
        # 确定版本
        version = random.choice(self._nine_year_education["versions"])
        
        # 确定年级
        grade = random.choice(self._nine_year_education["grades"])
        
        # 随机选择学科
        subject_en = random.choice(self._nine_year_education["subjects"])
        
        # 学科名称映射
        subject_map = {
            "math": "数学",
            "english": "英语",
            "chinese": "语文"
        }
        subject = subject_map[subject_en]
        
        # 根据学科生成题目内容
        if subject_en == "math":
            template = random.choice(self.question_templates["math"])
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 100)
            num3 = num1 + num2
            content = template.format(num1=num1, num2=num2, num3=num3)
        elif subject_en == "english":
            template = random.choice(self.question_templates["english"])
            words = ["apple", "banana", "cat", "dog", "house", "school", "teacher", "student"]
            word = random.choice(words)
            content = template.format(word=word, sentence="I {action} to school every day", english_phrase="How are you?")
        else:  # chinese
            template = random.choice(self.question_templates["chinese"])
            idioms = ["井底之蛙", "守株待兔", "亡羊补牢", "画蛇添足"]
            idiom = random.choice(idioms)
            content = template.format(phrase="_____色", idiom=idiom, sentence="今天天气真好_____", poem="床前明月光，疑是地上霜")
        
        # 构建完整的题目内容，包含版本、年级、考试类型和学科信息
        full_content = f"[{version}][{grade}][{exam_type}][{subject}] {content}"
        
        # 生成答案
        if subject_en == "math":
            if "=" in full_content:
                if "+" in full_content:
                    answer = str(num1 + num2)
                elif "×" in full_content:
                    answer = str(num1 * num2)
                elif "÷" in full_content:
                    answer = str(num1 / num2)
                else:
                    answer = str((num3 - num2) / num1)
            else:
                answer = "正确"
        elif subject_en == "english":
            word_meanings = {
                "apple": "苹果", "banana": "香蕉", "cat": "猫", "dog": "狗",
                "house": "房子", "school": "学校", "teacher": "老师", "student": "学生"
            }
            answer = word_meanings.get(word, "正确")
        else:  # chinese
            answer = "正确"
        
        # 生成解析
        explanation = f"本题考查{subject}相关知识，难度适中。"
        
        # 生成题目
        question = Question(
            content=full_content,
            answer=answer,
            explanation=explanation,
            language_id=language_id,
            level_id=level_id,
            category_id=category_id
        )
        
        return question

def test_simple_expansion():
    """测试简化的题目生成功能"""
    print("开始测试简化的题目生成...")
    
    # 初始化扩展器
    expander = SimpleNineYearEducationExpander()
    
    # 生成10道题目
    generated_count = 0
    total_attempts = 0
    max_attempts = 50  # 最大尝试次数
    
    while generated_count < 10 and total_attempts < max_attempts:
        total_attempts += 1
        
        try:
            # 随机选择参数
            language_id = 1  # 中文
            level_id = random.randint(1, 3)
            category_id = random.randint(1, 5)
            difficulty = random.choice(["easy", "medium", "hard"])
            
            # 生成题目
            question = expander._generate_exam_question(language_id, level_id, category_id, difficulty)
            
            if question:
                # 保存题目
                question_manager = QuestionManager()
                question_manager.create_question(
                    content=question.content,
                    answer=question.answer,
                    explanation=question.explanation,
                    category_id=question.category_id,
                    language_id=question.language_id,
                    level_id=question.level_id
                )
                generated_count += 1
                print(f"生成第 {generated_count} 道题目: {question.content[:50]}...")
        except Exception as e:
            print(f"生成题目时出错: {e}")
    
    print(f"测试完成，成功生成 {generated_count} 道题目")
    
    # 验证生成的题目
    if generated_count > 0:
        print("\n验证生成的题目...")
        question_manager = QuestionManager()
        questions = question_manager.get_questions(limit=20)
        
        for i, q in enumerate(questions[:10]):
            print(f"题目 {i+1}: {q.content}")
    
    return generated_count

if __name__ == "__main__":
    test_simple_expansion()
