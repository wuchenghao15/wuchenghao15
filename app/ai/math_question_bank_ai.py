# -*- coding: utf-8 -*-
import os
import logging
import json
import random
import time

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

        os.makedirs(self.math_question_bank_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)

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
            },
            'high': {
                'name': '高中',
                'grades': ['grade_10', 'grade_11', 'grade_12'],
                'topics': ['algebra', 'geometry', 'trigonometry', 'calculus', 'statistics', 'probability']
            },
            'college': {
                'name': '大学',
                'majors': ['math', 'engineering', 'computer_science', 'economics'],
                'topics': ['calculus', 'linear_algebra', 'abstract_algebra', 'real_analysis',
                          'complex_analysis', 'differential_equations', 'probability_theory', 'statistics', 'discrete_mathematics']
            }
        }

        self.question_types = ['calculation', 'proof', 'application', 'multiple_choice', 'fill_in_the_blank']
        self.source_types = ['past_exam', 'difficult', 'required', 'practice', 'skill_based']

        logger.info("数学题库AI初始化完成")

    def generate_primary_questions(self, grade, topic, source_type, count=10):
        """生成小学题目"""
        questions = []
        for i in range(count):
            question = {
                'id': f"primary_{grade}_{topic}_{source_type}_{int(time.time())}_{i}",
                'subject': 'math',
                'education_level': 'primary',
                'grade': grade,
                'topic': topic,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'arithmetic':
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
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            return {
                'question': f"计算: {a} + {b} = ?",
                'answer': str(a + b),
                'difficulty': 'easy'
            }
        elif grade in ['grade_2', 'grade_3']:
            a = random.randint(1, 100)
            b = random.randint(1, 50)
            return {
                'question': f"计算: {a} - {b} = ?",
                'answer': str(a - b),
                'difficulty': 'medium'
            }
        elif grade in ['grade_4', 'grade_5']:
            a = random.randint(1, 100)
            b = random.randint(1, 10)
            return {
                'question': f"计算: {a} ÷ {b} = ?",
                'answer': str(a // b),
                'difficulty': 'medium'
            }
        else:
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            c = random.randint(1, 10)
            return {
                'question': f"计算: ({a} + {b}) × {c} = ?",
                'answer': str((a + b) * c),
                'difficulty': 'hard'
            }

    def _generate_primary_geometry(self, grade, source_type):
        """生成小学数学几何题"""
        if grade in ['grade_3', 'grade_4']:
            return {
                'question': '一个长方形的长是8厘米,宽是5厘米,它的面积是多少?',
                'answer': '40平方厘米',
                'difficulty': 'medium'
            }
        elif grade in ['grade_5', 'grade_6']:
            return {
                'question': '一个正方形的面积是36平方厘米,它的边长是多少?',
                'answer': '6厘米',
                'difficulty': 'hard'
            }
        return {
            'question': '一个正方形的周长是20厘米,它的边长是多少?',
            'answer': '5厘米',
            'difficulty': 'easy'
        }

    def _generate_primary_word_problems(self, grade, source_type):
        """生成小学数学应用题"""
        if grade == 'grade_1':
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            return {
                'question': f"小明有{a}个苹果,妈妈又给了他{b}个,现在他有多少个?",
                'answer': str(a + b),
                'difficulty': 'easy'
            }
        elif grade in ['grade_2', 'grade_3']:
            a = random.randint(1, 20)
            b = random.randint(1, 10)
            return {
                'question': f"妈妈买了{a}个鸡蛋,用了{b}个,还剩多少个?",
                'answer': str(a - b),
                'difficulty': 'medium'
            }
        elif grade in ['grade_4', 'grade_5']:
            a = random.randint(50, 100)
            b = random.randint(1, 5)
            return {
                'question': f"一辆汽车每小时行驶{a}公里,行驶{b}小时,一共行驶多少公里?",
                'answer': str(a * b),
                'difficulty': 'medium'
            }
        else:
            a = random.randint(10, 50)
            b = random.randint(1, 10)
            c = random.randint(100, 200)
            return {
                'question': f"一个工程队每天修{a}米路,修了{b}天后,还剩{c}米,这条路全长多少米?",
                'answer': str(a * b + c),
                'difficulty': 'hard'
            }

    def generate_middle_questions(self, grade, topic, question_type, source_type, count=10):
        """生成初中题目"""
        questions = []
        for i in range(count):
            question = {
                'id': f"middle_{grade}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'math',
                'education_level': 'middle',
                'grade': grade,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'algebra':
                question['content'] = self._generate_middle_algebra(grade, source_type)
            elif topic == 'geometry':
                question['content'] = self._generate_middle_geometry(grade, source_type)
            elif topic == 'trigonometry':
                question['content'] = self._generate_middle_trigonometry(grade, source_type)
            elif topic == 'statistics':
                question['content'] = self._generate_middle_statistics(grade, source_type)
            questions.append(question)
        return questions

    def _generate_middle_algebra(self, grade, source_type):
        """生成初中代数题"""
        if grade == 'grade_7':
            a = random.randint(1, 10)
            b = random.randint(1, 20)
            c = random.randint(1, 50)
            return {
                'question': f"解方程: {a}x + {b} = {c}",
                'answer': f"x = {(c - b) / a}",
                'difficulty': 'medium'
            }
        elif grade in ['grade_8', 'grade_9']:
            return {
                'question': '解二元一次方程: 2x + y = 7, x + y = 4',
                'answer': 'x = 3, y = 1',
                'difficulty': 'hard'
            }
        return {
            'question': '解一元一次方程: 3x + 5 = 14',
            'answer': 'x = 3',
            'difficulty': 'medium'
        }

    def _generate_middle_geometry(self, grade, source_type):
        """生成初中几何题"""
        return {
            'question': '一个三角形的三个内角分别是30°、60°,第三个角是多少度?',
            'answer': '90°',
            'difficulty': 'easy'
        }

    def _generate_middle_trigonometry(self, grade, source_type):
        """生成初中三角题"""
        return {
            'question': '在直角三角形中,一个锐角是30°,对边是5厘米,斜边是多少?',
            'answer': '10厘米',
            'difficulty': 'medium'
        }

    def _generate_middle_statistics(self, grade, source_type):
        """生成初中统计题"""
        numbers = [random.randint(1, 10) for _ in range(5)]
        return {
            'question': f"一组数据: {numbers},求平均数",
            'answer': str(sum(numbers) / len(numbers)),
            'difficulty': 'medium'
        }

    def generate_high_questions(self, grade, topic, question_type, source_type, count=10):
        """生成高中题目"""
        questions = []
        for i in range(count):
            question = {
                'id': f"high_{grade}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'math',
                'education_level': 'high',
                'grade': grade,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'algebra':
                question['content'] = self._generate_high_algebra(grade, source_type)
            elif topic == 'geometry':
                question['content'] = self._generate_high_geometry(grade, source_type)
            elif topic == 'trigonometry':
                question['content'] = self._generate_high_trigonometry(grade, source_type)
            elif topic == 'calculus':
                question['content'] = self._generate_high_calculus(grade, source_type)
            elif topic == 'statistics':
                question['content'] = self._generate_high_statistics(grade, source_type)
            elif topic == 'probability':
                question['content'] = self._generate_high_probability(grade, source_type)
            questions.append(question)
        return questions

    def _generate_high_algebra(self, grade, source_type):
        """生成高中代数题"""
        if grade in ['grade_10', 'grade_11']:
            return {
                'question': '解不等式: x² - 5x + 6 > 0',
                'answer': 'x < 2 或 x > 3',
                'difficulty': 'medium'
            }
        else:
            return {
                'question': '求函数 f(x) = x³ - 3x² + 2x的根',
                'answer': 'x = 0, x = 1, x = 2',
                'difficulty': 'hard'
            }

    def _generate_high_geometry(self, grade, source_type):
        """生成高中几何题"""
        return {
            'question': '已知圆的方程是x² + y² = 25,求点(3,4)到圆心的距离',
            'answer': '5',
            'difficulty': 'medium'
        }

    def _generate_high_trigonometry(self, grade, source_type):
        """生成高中三角题"""
        return {
            'question': '证明: sin²x + cos²x = 1',
            'answer': '略',
            'difficulty': 'hard'
        }

    def _generate_high_calculus(self, grade, source_type):
        """生成高中微积分题"""
        if grade in ['grade_11', 'grade_12']:
            return {
                'question': '求函数f(x) = x²的导数',
                'answer': "f'(x) = 2x",
                'difficulty': 'medium'
            }
        return {
            'question': '求函数f(x) = x³在区间[0,1]上的定积分',
            'answer': '1/4',
            'difficulty': 'hard'
        }

    def _generate_high_statistics(self, grade, source_type):
        """生成高中统计题"""
        return {
            'question': '一组数据的方差是16,标准差是多少?',
            'answer': '4',
            'difficulty': 'medium'
        }

    def _generate_high_probability(self, grade, source_type):
        """生成高中概率题"""
        return {
            'question': '掷一枚骰子,出现偶数的概率是多少?',
            'answer': '1/2',
            'difficulty': 'easy'
        }

    def generate_college_questions(self, major, topic, source_type, count=10):
        """生成大学题目"""
        questions = []
        for i in range(count):
            question = {
                'id': f"college_{major}_{topic}_{source_type}_{int(time.time())}_{i}",
                'subject': 'math',
                'education_level': 'college',
                'major': major,
                'topic': topic,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'calculus':
                question['content'] = self._generate_college_calculus(major, source_type)
            elif topic == 'linear_algebra':
                question['content'] = self._generate_college_linear_algebra(major, source_type)
            elif topic == 'abstract_algebra':
                question['content'] = self._generate_college_abstract_algebra(major, source_type)
            elif topic == 'real_analysis':
                question['content'] = self._generate_college_real_analysis(major, source_type)
            elif topic == 'complex_analysis':
                question['content'] = self._generate_college_complex_analysis(major, source_type)
            elif topic == 'differential_equations':
                question['content'] = self._generate_college_differential_equations(major, source_type)
            elif topic == 'probability_theory':
                question['content'] = self._generate_college_probability_theory(major, source_type)
            elif topic == 'statistics':
                question['content'] = self._generate_college_statistics(major, source_type)
            elif topic == 'discrete_mathematics':
                question['content'] = self._generate_college_discrete_mathematics(major, source_type)
            questions.append(question)
        return questions

    def _generate_college_calculus(self, major, source_type):
        """生成大学微积分题"""
        return {
            'question': '求二重积分∫∫(x² + y²)dA,其中D是单位圆',
            'answer': 'π/2',
            'difficulty': 'hard'
        }

    def _generate_college_linear_algebra(self, major, source_type):
        """生成大学线性代数题"""
        return {
            'question': '求矩阵[[1, 2],[3, 4]]的行列式',
            'answer': '-2',
            'difficulty': 'medium'
        }

    def _generate_college_abstract_algebra(self, major, source_type):
        """生成大学抽象代数题"""
        return {
            'question': '证明: 群的单位元是唯一的',
            'answer': '略',
            'difficulty': 'hard'
        }

    def _generate_college_real_analysis(self, major, source_type):
        """生成大学实分析题"""
        return {
            'question': '证明: 闭区间上的连续函数是一致连续的',
            'answer': '略',
            'difficulty': 'hard'
        }

    def _generate_college_complex_analysis(self, major, source_type):
        """生成大学复分析题"""
        return {
            'question': '计算积分∮(1/z)dz,其中C是单位圆',
            'answer': '2πi',
            'difficulty': 'hard'
        }

    def _generate_college_differential_equations(self, major, source_type):
        """生成大学微分方程题"""
        return {
            'question': '解方程: y\' + y = e^x',
            'answer': 'y = (1/2)e^x + Ce^(-x)',
            'difficulty': 'medium'
        }

    def _generate_college_probability_theory(self, major, source_type):
        """生成大学概率论题"""
        return {
            'question': '设X ~ N(0,1),求P(|X| < 1)',
            'answer': '0.6826',
            'difficulty': 'medium'
        }

    def _generate_college_statistics(self, major, source_type):
        """生成大学统计题"""
        return {
            'question': '解释什么是置信区间',
            'answer': '略',
            'difficulty': 'medium'
        }

    def _generate_college_discrete_mathematics(self, major, source_type):
        """生成大学离散数学题"""
        return {
            'question': '证明: 在任何6个人中,至少有3个人互相认识或至少有3个人互不认识',
            'answer': '略',
            'difficulty': 'hard'
        }

    def save_questions(self, questions, education_level):
        """保存题目到题库"""
        try:
            for question in questions:
                if education_level in ['primary', 'middle', 'high']:
                    grade = question.get('grade', 'unknown')
                    topic = question.get('topic', 'unknown')
                    source_type = question.get('source_type', 'unknown')
                    save_dir = os.path.join(self.math_question_bank_dir, education_level, grade, topic, source_type)
                else:
                    major = question.get('major', 'unknown')
                    topic = question.get('topic', 'unknown')
                    source_type = question.get('source_type', 'unknown')
                    save_dir = os.path.join(self.math_question_bank_dir, education_level, major, topic, source_type)

                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, f"{question['id']}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(question, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(questions)}道数学题目到题库")
            return True
        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False

    def report_to_ai_brain(self, questions):
        """将生成的题目报告到AI脑库"""
        try:
            knowledge_entry = {
                'type': 'math_question_generation',
                'generated_count': len(questions),
                'education_levels': list(set(q['education_level'] for q in questions)),
                'source_types': list(set(q['source_type'] for q in questions)),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'questions': questions[:5]
            }
            brain_path = os.path.join(self.ai_brain_dir, f"math_questions_{int(time.time())}.json")
            with open(brain_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)
            logger.info("数学题目生成结果已报告到AI脑库")
            return True
        except Exception as e:
            logger.error(f"报告到AI脑库时出错: {str(e)}")
            return False

    def run(self, count_per_category=10):
        """运行数学题库扩充"""
        try:
            logger.info("开始扩充数学题库")
            all_questions = []

            for level_key, level_config in self.education_levels.items():
                if 'grades' in level_config:
                    for grade in level_config['grades']:
                        for topic in level_config['topics']:
                            for source_type in self.source_types:
                                if level_key == 'primary':
                                    questions = self.generate_primary_questions(grade, topic, source_type, count_per_category)
                                elif level_key == 'middle':
                                    questions = self.generate_middle_questions(grade, topic, 'calculation', source_type, count_per_category)
                                elif level_key == 'high':
                                    questions = self.generate_high_questions(grade, topic, 'calculation', source_type, count_per_category)
                                else:
                                    questions = []
                                all_questions.extend(questions)
                                self.save_questions(questions, level_key)

                elif 'majors' in level_config:
                    for major in level_config['majors']:
                        for topic in level_config['topics']:
                            for source_type in self.source_types:
                                questions = self.generate_college_questions(major, topic, source_type, count_per_category)
                                all_questions.extend(questions)
                                self.save_questions(questions, 'college')

            if all_questions:
                self.report_to_ai_brain(all_questions)
            logger.info(f"数学题库扩充完成,共生成 {len(all_questions)}道题目")
            return True
        except Exception as e:
            logger.error(f"运行数学题库扩充时出错: {str(e)}")
            return False


if __name__ == "__main__":
    math_bank_ai = MathQuestionBankAI()
    math_bank_ai.run()
