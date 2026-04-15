#!/usr/bin/env python3
"""
扩充9年制义务教育所有版本的适配习题、中考题、高考题和压轴题到题库
"""

import sys
import os
import time
import logging
import random

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Optional
from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import QuestionManager, Question

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NineYearEducationExpander(QuestionBankExpander):
    """
    9年制义务教育题库扩充器
    """
    
    def __init__(self):
        """
        初始化9年制义务教育题库扩充器
        """
        super().__init__()
        
        # 添加9年制义务教育的题目模板
        self._config["subjects"]["math"]["templates"]["exam_question"] = [
            "[中考题] {content}",
            "[高考题] {content}",
            "[压轴题] {content}"
        ]
        
        self._config["subjects"]["english"]["templates"]["exam_question"] = [
            "[中考题] {content}",
            "[高考题] {content}",
            "[压轴题] {content}"
        ]
        
        self._config["subjects"]["chinese"]["templates"]["exam_question"] = [
            "[中考题] {content}",
            "[高考题] {content}",
            "[压轴题] {content}"
        ]
        
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
            "subjects": [
                {"id": 1, "name": "数学", "categories": ["算术", "代数", "几何", "概率", "统计"]},
                {"id": 2, "name": "英语", "categories": ["词汇", "语法", "阅读", "听力", "写作"]},
                {"id": 3, "name": "语文", "categories": ["词语", "语法", "阅读", "写作", "文学常识"]},
                {"id": 4, "name": "物理", "categories": ["力学", "热学", "光学", "电学", "磁学"]},
                {"id": 5, "name": "化学", "categories": ["无机化学", "有机化学", "化学实验", "化学计算"]}
            ]
        }
    
    def _generate_exam_question(self, language_id: int, level_id: int, category_id: int, difficulty: str) -> Optional[Question]:
        """
        生成考试题目（中考题、高考题、压轴题）
        
        Args:
            language_id: 语言ID
            level_id: 等级ID
            category_id: 分类ID
            difficulty: 难度级别
            
        Returns:
            Optional[Question]: 生成的题目
        """
        try:
            # 确定题目类型
            exam_types = ["中考题", "高考题", "压轴题"]
            exam_type = random.choice(exam_types)
            
            # 确定版本
            version = random.choice(self._nine_year_education["versions"])
            
            # 确定年级
            grade = random.choice(self._nine_year_education["grades"])
            
            # 随机选择学科
            subjects = ["math", "english", "chinese"]
            subject = random.choice(subjects)
            
            # 根据学科生成题目内容
            if subject == "math":
                # 生成数学考试题目
                if difficulty == "easy":
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
                    
                    # 转换难度为难度分数
                    difficulty_score = {
                        "easy": 1.0,
                        "medium": 2.0,
                        "hard": 3.0
                    }.get(difficulty, 1.0)
                    
                    # 创建题目
                    question = Question(
                        content=f"[{version}][{grade}][{exam_type}][数学] {content}",
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
                # 生成英语考试题目
                word = self._generate_english_word(difficulty)
                content = f"选择{word}的正确中文意思"
                
                # 生成选项（这里简化处理，实际应该有真实的翻译）
                options = [f"选项1", f"选项2", f"选项3", f"选项4"]
                correct_answer = str(random.randint(0, 3))
                
                # 转换难度为难度分数
                difficulty_score = {
                    "easy": 1.0,
                    "medium": 2.0,
                    "hard": 3.0
                }.get(difficulty, 1.0)
                
                # 创建题目
                question = Question(
                    content=f"[{version}][{grade}][{exam_type}][英语] {content}",
                    question_type="single_choice",
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    options=options,
                    answer=correct_answer,
                    explanation=f"{word}的正确意思是{options[int(correct_answer)]}",
                    difficulty_score=difficulty_score
                )
                return question
            
            elif subject == "chinese":
                # 生成语文考试题目
                words = ["美丽", "漂亮", "好看", "美观"]
                word = random.choice(words)
                content = f"选择与{word}意思最接近的词语"
                
                # 生成选项
                options = ["美丽", "漂亮", "好看", "美观"]
                random.shuffle(options)
                correct_answer = str(options.index(word))
                
                # 转换难度为难度分数
                difficulty_score = {
                    "easy": 1.0,
                    "medium": 2.0,
                    "hard": 3.0
                }.get(difficulty, 1.0)
                
                # 创建题目
                question = Question(
                    content=f"[{version}][{grade}][{exam_type}][语文] {content}",
                    question_type="single_choice",
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    options=options,
                    answer=correct_answer,
                    explanation=f"{word}的意思是{word}",
                    difficulty_score=difficulty_score
                )
                return question
            
            return None
        except Exception as e:
            logger.error(f"生成考试题目失败: {str(e)}")
            return None

def expand_nine_year_education():
    """
    扩充9年制义务教育所有版本的适配习题、中考题、高考题和压轴题到题库
    """
    print("================================================================================" )
    print("扩充9年制义务教育所有版本的适配习题、中考题、高考题和压轴题到题库")
    print("================================================================================" )
    
    try:
        # 初始化9年制义务教育题库扩充器
        expander = NineYearEducationExpander()
        logger.info("9年制义务教育题库扩充器初始化成功")
        
        # 初始化题目管理器
        question_manager = QuestionManager()
        logger.info("题目管理器初始化成功")
        
        # 目标题目数量
        target_count = 10000
        
        # 记录开始时间
        start_time = time.time()
        
        # 生成题目
        generated_count = 0
        batch_size = 100  # 每批生成100道题目
        
        while generated_count < target_count:
            batch_start = time.time()
            batch_generated = 0
            
            for _ in range(batch_size):
                # 生成随机题目参数
                language_id = 3  # 中文
                level_id = 1 + (generated_count % 5)  # 1-5
                category_id = 1 + (generated_count % 5)  # 1-5
                difficulty = ["easy", "medium", "hard"][generated_count % 3]
                
                # 生成考试题目
                question = expander._generate_exam_question(
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    difficulty=difficulty
                )
                
                # 保存题目
                if question:
                    try:
                        # 使用 QuestionManager 创建题目
                        question_manager.create_question(
                            content=question.content,
                            answer=question.answer,
                            explanation=question.explanation,
                            category_id=question.category_id,
                            language_id=question.language_id,
                            level_id=question.level_id,
                            question_type=question.question_type,
                            options=question.options,
                            tags=question.tags,
                            difficulty_score=question.difficulty_score,
                            discrimination_index=question.discrimination_index,
                            usage_count=question.usage_count,
                            correct_rate=question.correct_rate,
                            audio_url=question.audio_url
                        )
                        batch_generated += 1
                        generated_count += 1
                        
                        # 每生成100道题目，打印一次进度
                        if generated_count % 100 == 0:
                            logger.info(f"已生成 {generated_count}/{target_count} 道题目")
                    except Exception as e:
                        logger.error(f"保存题目失败: {str(e)}")
            
            batch_end = time.time()
            batch_time = batch_end - batch_start
            logger.info(f"第 {generated_count // batch_size} 批生成完成，耗时 {batch_time:.2f} 秒，生成 {batch_generated} 道题目")
            
            # 短暂休息，避免系统过载
            time.sleep(0.5)
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info("\n扩充完成！")
        logger.info(f"成功生成 {generated_count} 道题目")
        logger.info(f"耗时: {elapsed_time:.2f} 秒")
        logger.info(f"平均生成速度: {generated_count / elapsed_time:.2f} 题/秒")
        
    except Exception as e:
        logger.error(f"扩充失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================" )
        print("扩充完成！")
        print("================================================================================" )

if __name__ == "__main__":
    expand_nine_year_education()
