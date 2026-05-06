# -*- coding: utf-8 -*-
import os
import logging
# JSON import removed - using database
import random
import time

# 配置日志
logs_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'math_question_bank_ai.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MathQuestionBankAI:
    """数学题库自动扩充AI"""

    def __init__(self):
        """初始化数学题库AI"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, '../data')
        self.math_question_bank_dir = os.path.join(self.data_dir, 'math_question_bank')
        self.ai_brain_dir = os.path.join(self.data_dir, 'ai_brain')

        # 确保目录存在
        os.makedirs(self.math_question_bank_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)

        # 教育阶段配置
        self.education_levels = {
            'primary': {
                'name': '小学',
                'grades': ['grade_1', 'grade_2', 'grade_3', 'grade_4', 'grade_5', 'grade_6'],
                'topics': ['arithmetic', 'geometry', 'word_problems']
            },
            'middle': {
                'name': '初中',
                'grades': ['grade_7', 'grade_8', 'grade_9'],
                'topics': ['algebra', 'geometry', 'trigonometry', 'statistics']
            'high': {
                'name': '高中',
                'grades': ['grade_10', 'grade_11', 'grade_12'],
                'topics': ['algebra', 'geometry', 'trigonometry', 'calculus', 'statistics', 'probability']
            'college': {
                'name': '大学',
                'majors': ['math', 'engineering', 'computer_science', 'economics'],
                'topics': ['calculus', 'linear_algebra', 'abstract_algebra', 'real_analysis', 'complex_analysis', 'differential_equations', 'probability_theory', 'statistics', 'discrete_mathematics']
            }
        }

        self.question_types = ['calculation', 'proof', 'application', 'multiple_choice', 'fill_in_the_blank']

        # 题目来源类型
        self.source_types = ['past_exam', 'difficult', 'required', 'practice', 'skill_based']

        logger.info("数学题库AI初始化完成")

    def generate_primary_questions(self, grade, topic, source_type, count=10):
        """生成小学题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"primary_{grade}_{topic}_{source_type}_{int(time.time())}_{i}",
                'education_level': 'primary',
                'grade': grade,
                'topic': topic,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

                question['content'] = self._generate_primary_arithmetic(grade, source_type)
            elif topic == 'geometry':
                question['content'] = self._generate_primary_geometry(grade, source_type)
            elif topic == 'word_problems':
                question['content'] = self._generate_primary_word_problems(grade, source_type)

            questions.append(question)

        return questions

    def _generate_primary_arithmetic(self, grade, source_type):
        """生成小学数学算术题"""
        if grade == 'grade_1':
            if source_type == 'past_exam':
                return {
                    'question': f"计算：{random.randint(1, 20)} + {random.randint(1, 20)} = ?",
                    'answer': f"{random.randint(1, 20) + random.randint(1, 20)}",
                    'difficulty': 'easy'
                }
            elif source_type == 'difficult':
                    'question': f"计算：{random.randint(1, 10)} + {random.randint(1, 10)} + {random.randint(1, 10)} = ?",
                    'answer': f"{random.randint(1, 10) + random.randint(1, 10) + random.randint(1, 10)}",
                    'difficulty': 'medium'
                }
                    'question': f"计算：{random.randint(1, 10)} + {random.randint(1, 10)} = ?",
                    'answer': f"{random.randint(1, 10) + random.randint(1, 10)}",
                    'difficulty': 'easy'
                }
        elif grade == 'grade_2':
                'answer': f"{random.randint(1, 100) - random.randint(1, 50)}",
                'difficulty': 'medium'
            }
        elif grade == 'grade_3':
                'difficulty': 'medium'
            }
        elif grade == 'grade_4':
                'question': f"计算：{random.randint(1, 100)} ÷ {random.randint(1, 10)} = ?",
                'answer': f"{random.randint(1, 100) // random.randint(1, 10)}",
            }
                'question': f"计算：({random.randint(1, 20)} + {random.randint(1, 20)}) × {random.randint(1, 10)} = ?",
                'answer': f"{ (random.randint(1, 20) + random.randint(1, 20)) * random.randint(1, 10) }",
                'difficulty': 'hard'
        else:  # grade_6
                'question': f"计算：{random.randint(1, 100)} × {random.randint(1, 100)} = ?",
                'difficulty': 'hard'
            }
        """生成小学数学几何题"""
        if grade == 'grade_3':
            return {
                'answer': "20厘米",
            }
        elif grade == 'grade_4':
                'question': "一个长方形的长是8厘米，宽是5厘米，它的面积是多少？",
                'answer': "40平方厘米",
                'difficulty': 'medium'
            }
        elif grade == 'grade_5':
                'question': "一个长方形的周长是24厘米，长是8厘米，宽是多少？",
                'difficulty': 'hard'
            }
        else:  # grade_6
                'question': "一个正方形的面积是36平方厘米，它的边长是多少？",
                'answer': "6厘米",
            }

        """生成小学数学应用题"""
        if grade == 'grade_1':
            return {
                'answer': f"{random.randint(1, 10) + random.randint(1, 10)}",
            }
        elif grade == 'grade_2':
                'question': f"妈妈买了{random.randint(1, 20)}个鸡蛋，用了{random.randint(1, 10)}个，还剩多少个？",
                'difficulty': 'medium'
            }
                'answer': f"{random.randint(1, 10) * random.randint(1, 5)}",
                'difficulty': 'medium'
            }
                'question': f"把{random.randint(1, 100)}个糖果平均分给{random.randint(1, 10)}个小朋友，每个小朋友分到多少个？",
                'difficulty': 'hard'
            }
                'question': f"一辆汽车每小时行驶{random.randint(50, 100)}公里，行驶{random.randint(1, 5)}小时，一共行驶多少公里？",
                'answer': f"{random.randint(50, 100) * random.randint(1, 5)}",
            }
        else:  # grade_6
                'question': f"一个工程队每天修{random.randint(10, 50)}米路，修了{random.randint(1, 10)}天后，还剩{random.randint(100, 200)}米，这条路全长多少米？",
                'answer': f"{random.randint(10, 50) * random.randint(1, 10) + random.randint(100, 200)}",

        """生成初中题目"""
        questions = []

                'id': f"middle_{grade}_{topic}_{source_type}_{int(time.time())}_{i}",
                'education_level': 'middle',
                'grade': grade,
                'topic': topic,
                'source_type': source_type,

            elif topic == 'geometry':
                question['content'] = self._generate_middle_geometry(grade, source_type)
            elif topic == 'statistics':
                question['content'] = self._generate_middle_statistics(grade, source_type)
            questions.append(question)


    def _generate_middle_algebra(self, grade, source_type):
                'question': f"解方程：{random.randint(1, 10)}x + {random.randint(1, 20)} = {random.randint(1, 50)}",
                'answer': f"x = { (random.randint(1, 50) - random.randint(1, 20)) / random.randint(1, 10) }",
                'difficulty': 'medium'
        elif grade == 'grade_8':
                'answer': "x = ..., y = ...",
            }
                'answer': "x = ...",
                'difficulty': 'hard'
            }

            return {
                'question': "一个三角形的三个内角分别是30°、60°，第三个角是多少度？",
                'answer': "90°",
            }
        elif grade == 'grade_8':
                'answer': "78.5平方厘米",
                'difficulty': 'medium'
        else:  # grade_9
                'question': "一个直角三角形的两条直角边分别是3厘米和4厘米，斜边是多少厘米？",
                'answer': "5厘米",
            }

        if grade == 'grade_8':
            return {
                'question': "在直角三角形中，一个锐角是30°，对边是5厘米，斜边是多少？",
                'answer': "10厘米",
                'difficulty': 'medium'
        else:  # grade_9
                'question': "计算sin60°的值",
                'answer': "√3/2",
                'difficulty': 'hard'
            }
        """生成初中统计题"""
        return {
            'question': f"一组数据：{random.randint(1, 10)}, {random.randint(1, 10)}, {random.randint(1, 10)}, {random.randint(1, 10)}, {random.randint(1, 10)}，求平均数",
            'answer': f"{(random.randint(1, 10) + random.randint(1, 10) + random.randint(1, 10) + random.randint(1, 10) + random.randint(1, 10)) / 5}",
            'difficulty': 'medium'
        }

        """生成高中题目"""

        for i in range(count):
            question = {
                'id': f"high_{grade}_{topic}_{source_type}_{int(time.time())}_{i}",
                'topic': topic,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            elif topic == 'geometry':
                question['content'] = self._generate_high_geometry(grade, source_type)
            elif topic == 'trigonometry':
                question['content'] = self._generate_high_trigonometry(grade, source_type)
            elif topic == 'calculus':
                question['content'] = self._generate_high_calculus(grade, source_type)
            elif topic == 'statistics':
                question['content'] = self._generate_high_statistics(grade, source_type)
                question['content'] = self._generate_high_probability(grade, source_type)

            questions.append(question)

        return questions
    def _generate_high_algebra(self, grade, source_type):
        """生成高中代数题"""
            return {
                'answer': "29",
                'difficulty': 'medium'
            }
                'answer': "31",
        else:  # grade_12
                'question': "解不等式：x² - 5x + 6 > 0",
                'answer': "x < 2 或 x > 3",
            }

        return {
            'question': "已知圆的方程是x² + y² = 25，求点(3,4)到圆心的距离",
            'difficulty': 'medium'
        }
        return {
            'question': "证明：sin²x + cos²x = 1",
            'answer': "略",
            'difficulty': 'hard'
        """生成高中微积分题"""
        if grade == 'grade_11':
                'question': "求函数f(x) = x²的导数",
                'answer': "f'(x) = 2x",
                'difficulty': 'medium'
            }
        else:  # grade_12
                'question': "求函数f(x) = x³在区间[0,1]上的定积分",
                'difficulty': 'hard'
            }
        """生成高中统计题"""
            'question': "一组数据的方差是16，标准差是多少？",
            'difficulty': 'medium'
        }

        """生成高中概率题"""
        return {
            'question': "掷一枚骰子，出现偶数的概率是多少？",
            'answer': "1/2",
        }

        """生成大学题目"""

            question = {
                'id': f"college_{major}_{topic}_{source_type}_{int(time.time())}_{i}",
                'education_level': 'college',
                'major': major,
                'topic': topic,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

                question['content'] = self._generate_college_calculus(major, source_type)
            elif topic == 'linear_algebra':
                question['content'] = self._generate_college_linear_algebra(major, source_type)
            elif topic == 'abstract_algebra':
            elif topic == 'real_analysis':
                question['content'] = self._generate_college_real_analysis(major, source_type)
            elif topic == 'complex_analysis':
                question['content'] = self._generate_college_complex_analysis(major, source_type)
            elif topic == 'differential_equations':
                question['content'] = self._generate_college_differential_equations(major, source_type)
            elif topic == 'probability_theory':
            elif topic == 'statistics':
                question['content'] = self._generate_college_statistics(major, source_type)
            elif topic == 'discrete_mathematics':
                question['content'] = self._generate_college_discrete_mathematics(major, source_type)

            questions.append(question)
    def _generate_college_calculus(self, major, source_type):
        """生成大学微积分题"""
        if source_type == 'past_exam':
            return {
                'difficulty': 'medium'
            }
                'question': "求二重积分∫∫(x² + y²)dA，其中D是单位圆",
                'answer': "π/2",
            }
                'question': "求函数f(x) = e^x的n阶导数",
                'difficulty': 'medium'

        """生成大学线性代数题"""
        return {
            'question': "求矩阵[[1, 2], [3, 4]]的行列式",
            'answer': "-2",
            'difficulty': 'medium'
        return {
            'question': "证明：群的单位元是唯一的",
            'answer': "略",
        }

        """生成大学实分析题"""
            'question': "证明：闭区间上的连续函数是一致连续的",
            'answer': "略",
            'difficulty': 'hard'
        }

        """生成大学复分析题"""
        return {
            'question': "计算积分∮(1/z)dz，其中C是单位圆",
            'answer': "2πi",
            'difficulty': 'hard'

        """生成大学微分方程题"""
        return {
            'question': "解方程：y' + y = e^x",
            'answer': "y = (1/2)e^x + Ce^(-x)",
            'difficulty': 'medium'
        }

        """生成大学概率论题"""
        return {
            'question': "设X ~ N(0,1)，求P(|X| < 1)",
            'answer': "0.6826",
            'difficulty': 'medium'

        return {
            'question': "解释什么是置信区间",
            'answer': "略",
            'difficulty': 'medium'

        """生成大学离散数学题"""
            'question': "证明：在任何6个人中，至少有3个人互相认识或至少有3个人互不认识",
            'answer': "略",
            'difficulty': 'hard'
        }
        """保存题目到题库"""
            # 按教育阶段和类型分类保存
            for question in questions:
                if education_level == 'primary' or education_level == 'middle' or education_level == 'high':
                    grade = question.get('grade', 'unknown')
                    topic = question.get('topic', 'unknown')

                    # 创建目录结构
                    save_dir = os.path.join(self.math_question_bank_dir, education_level, grade, topic, source_type)
                    major = question.get('major', 'unknown')
                    source_type = question.get('source_type', 'unknown')

                    # 创建目录结构
                    save_dir = os.path.join(self.math_question_bank_dir, education_level, major, topic, source_type)

                os.makedirs(save_dir, exist_ok=True)

                file_path = os.path.join(save_dir, f"{question['id']}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(question, f, ensure_ascii=False, indent=2)

            logger.info(f"保存了 {len(questions)} 道数学题目到题库")
            return True
        except Exception as e:
            return False

    def report_to_ai_brain(self, questions):
        """将生成的题目报告到AI脑库"""
        try:
            # 生成知识条目
            knowledge_entry = {
                'generated_count': len(questions),
                'education_levels': list(set(q['education_level'] for q in questions)),
                'source_types': list(set(q['source_type'] for q in questions)),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'questions': questions[:5]  # 只保存前5个作为示例
            }

            with open(brain_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)
            logger.info("数学题目生成结果已报告到AI脑库")
        except Exception as e:
            logger.error(f"报告到AI脑库时出错: {str(e)}")

    def run(self, count_per_category=10):
        """运行数学题库扩充"""
        try:
            logger.info("开始扩充数学题库")

            all_questions = []
            # 生成小学题目
                for topic in self.education_levels['primary']['topics']:
                    for source_type in self.source_types:
                        # 生成题目
                            grade, topic, source_type, count_per_category

                        # 保存题目

            # 生成初中题目
            for grade in self.education_levels['middle']['grades']:
                for topic in self.education_levels['middle']['topics']:
                        # 生成题目
                        questions = self.generate_middle_questions(
                            grade, topic, source_type, count_per_category

                        # 保存题目
                        self.save_questions(questions, 'middle')

            # 生成高中题目
            for grade in self.education_levels['high']['grades']:
                for topic in self.education_levels['high']['topics']:
                    for source_type in self.source_types:
                        # 生成题目
                        questions = self.generate_high_questions(
                            grade, topic, source_type, count_per_category
                        all_questions.extend(questions)

                        # 保存题目
                        self.save_questions(questions, 'high')

            # 生成大学题目
            for major in self.education_levels['college']['majors']:
                for topic in self.education_levels['college']['topics']:
                    for source_type in self.source_types:
                        # 生成题目
                        questions = self.generate_college_questions(
                            major, topic, source_type, count_per_category

                        # 保存题目
                        self.save_questions(questions, 'college')

            # 报告到AI脑库
            self.report_to_ai_brain(all_questions)

            return True
        except Exception as e:
            logger.error(f"运行数学题库扩充时出错: {str(e)}")
            return False

if __name__ == "__main__":
    math_bank_ai = MathQuestionBankAI()
