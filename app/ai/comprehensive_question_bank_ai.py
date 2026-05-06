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
        logging.FileHandler(os.path.join(logs_dir, 'comprehensive_question_bank_ai.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveQuestionBankAI:
    """综合题库自动扩充AI"""

    def __init__(self):
        """初始化综合题库AI"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, '../data')
        self.comprehensive_bank_dir = os.path.join(self.data_dir, 'comprehensive_question_bank')
        self.ai_brain_dir = os.path.join(self.data_dir, 'ai_brain')

        # 确保目录存在
        os.makedirs(self.comprehensive_bank_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)

        # 学科配置
        self.subjects = {
            'chinese': {
                'name': '语文',
                'education_levels': ['primary', 'middle', 'high'],
                'topics': ['reading', 'writing', 'grammar', 'poetry', 'comprehension'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'analysis']
            },
            'english': {
                'name': '英语',
                'topics': ['vocabulary', 'grammar', 'reading', 'writing', 'listening', 'speaking'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'translation']
            },
                'name': '数学',
                'education_levels': ['primary', 'middle', 'high', 'college'],
                'topics': ['arithmetic', 'algebra', 'geometry', 'calculus', 'statistics', 'probability'],
                'question_types': ['calculation', 'proof', 'application', 'multiple_choice']
            },
                'name': '物理',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['mechanics', 'thermodynamics', 'electromagnetism', 'optics', 'modern_physics'],
                'question_types': ['calculation', 'proof', 'application', 'multiple_choice']
            },
                'name': '化学',
                'topics': ['inorganic', 'organic', 'physical', 'analytical'],
                'question_types': ['calculation', 'reaction', 'multiple_choice', 'experiment']
            },
                'name': '生物',
                'topics': ['cell', 'genetics', 'evolution', 'ecology', 'physiology'],
                'question_types': ['multiple_choice', 'fill_in', 'experiment', 'analysis']
            },
                'name': '历史',
                'education_levels': ['middle', 'high', 'college'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'analysis']
            'geography': {
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['physical', 'human', 'regional', 'cartography'],
                'question_types': ['multiple_choice', 'fill_in', 'map', 'analysis']
            'politics': {
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['ideology', 'economics', 'law', 'ethics'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'analysis']
        }
        # 题目来源类型
        self.source_types = ['past_exam', 'difficult', 'required', 'practice', 'skill_based']

        logger.info("综合题库AI初始化完成")

        """生成语文题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"chinese_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'chinese',
                'education_level': education_level,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            if topic == 'reading':
                question['content'] = self._generate_chinese_reading(education_level, source_type)
            elif topic == 'writing':
                question['content'] = self._generate_chinese_writing(education_level, source_type)
            elif topic == 'grammar':
                question['content'] = self._generate_chinese_grammar(education_level, source_type)
            elif topic == 'poetry':
                question['content'] = self._generate_chinese_poetry(education_level, source_type)
            elif topic == 'comprehension':
                question['content'] = self._generate_chinese_comprehension(education_level, source_type)

            questions.append(question)

        return questions
    def _generate_chinese_reading(self, education_level, source_type):
        """生成语文阅读题"""
        if education_level == 'primary':
            passages = [
                "春天来了，万物复苏。公园里的花儿开了，草儿绿了，小鸟在枝头唱歌。",
                "小明是一个勤奋的学生，他每天都认真学习，成绩一直很好。",
                "妈妈做的饭菜很香，我们全家人都喜欢吃。"
        elif education_level == 'middle':
            passages = [
                "中国是一个历史悠久的国家，有着灿烂的文化和伟大的文明。",
                "科技的发展改变了我们的生活，让我们的生活更加便捷。",
                "环境保护是我们每个人的责任，我们应该从身边的小事做起。"
        else:  # high
            passages = [
                "传统文化是一个国家的精神财富，我们应该继承和发扬。",
                "人工智能的发展给人类带来了机遇和挑战，我们需要理性看待。",
                "青春是人生中最美好的时光，我们应该珍惜并努力奋斗。"

        return {
            'passage': random.choice(passages),
            'questions': [
                {
                    'type': 'multiple_choice',
                    'content': '根据文章，下列哪项是正确的？',
                    'options': ['选项1', '选项2', '选项3', '选项4'],
                    'correct_answer': random.randint(0, 3)
                }
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_chinese_writing(self, education_level, source_type):
        """生成语文写作题"""
            topics = ["我的妈妈", "我的学校", "一次难忘的经历"]
        elif education_level == 'middle':
            topics = ["成长的烦恼", "友谊的力量", "科技改变生活"]
        else:  # high
            topics = ["责任与担当", "传统文化的传承", "青春的意义"]

        return {
            'topic': random.choice(topics),
            'requirements': "请根据题目写一篇不少于800字的作文",
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }
    def _generate_chinese_grammar(self, education_level, source_type):
        """生成语文语法题"""
            questions = ["选择正确的字：他（ ）了一本书。A. 买 B. 卖 C. 买 D. 卖"]
        elif education_level == 'middle':
            questions = ["选择正确的成语：（ ）山流水 A. 高 B. 青 C. 大 D. 长"]
        else:  # high
            questions = ["选择正确的标点：他说（ ）我明天不来了（ ） A. ，。 B. ：。 C. ，！ D. ：！"]

        return {
            'correct_answer': random.randint(0, 3),
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

        """生成语文诗词题"""
            poems = ["床前明月光，疑是地上霜。举头望明月，低头思故乡。"]
            poems = ["春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。"]
        else:  # high
            poems = ["离离原上草，一岁一枯荣。野火烧不尽，春风吹又生。"]
        return {
            'poem': random.choice(poems),
                {
                    'content': '请补全诗句：床前明月光，（ ）。',
                    'correct_answer': '疑是地上霜'
                }
        }

    def _generate_chinese_comprehension(self, education_level, source_type):
        return {
            'passage': "阅读理解文章内容...",
            'questions': [
                {
                    'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
                }
        }


        for i in range(count):
                'id': f"english_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'english',
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'vocabulary':
            elif topic == 'grammar':
            elif topic == 'reading':
                question['content'] = self._generate_english_reading(education_level, source_type)
                question['content'] = self._generate_english_writing(education_level, source_type)
                question['content'] = self._generate_english_listening(education_level, source_type)

            questions.append(question)

        return questions
        """生成英语词汇题"""
            words = ["interesting", "difficult", "important", "beautiful"]
            words = ["sophisticated", "comprehensive", "fundamental", "significant"]
        return {
            'question': f"What does '{random.choice(words)}' mean?",
            'correct_answer': random.randint(0, 3),
    def _generate_english_grammar(self, education_level, source_type):
        if education_level == 'primary':
        elif education_level == 'middle':
            questions = ["Choose the correct tense: He ( ) to school yesterday. A. go B. goes C. went D. going"]
        else:  # high

            'question': random.choice(questions),
            'correct_answer': random.randint(0, 3),
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'

    def _generate_english_reading(self, education_level, source_type):
        """生成英语阅读题"""
        if education_level == 'primary':
        elif education_level == 'middle':
            passages = ["English is an important language. It is spoken by people all over the world. We should learn it well."]
            passages = ["The development of technology has changed our lives in many ways. It has made our lives more convenient."]

        return {
            'passage': random.choice(passages),
            'questions': [
                {
                    'content': 'According to the passage, which is correct?',
                    'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                    'correct_answer': random.randint(0, 3)
                }
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

        """生成英语写作题"""
        if education_level == 'primary':
            topics = ["My Family", "My School", "My Favorite Animal"]
        elif education_level == 'middle':
            topics = ["My Best Friend", "My Hobby", "My Dream"]
            topics = ["The Importance of Education", "Environmental Protection", "Technology and Life"]

            'topic': random.choice(topics),
            'requirements': "Write a composition of at least 100 words",
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }
        """生成英语听力题"""
        dialogues = [
            "What's your name? My name is John. Nice to meet you. Nice to meet you too."
        return {
            'dialogue': random.choice(dialogues),
            'audio_url': f"https://example.com/audio/english/{education_level}/{random.randint(1, 100)}.mp3",
            'questions': [
                {
                    'content': 'What did they talk about?',
                    'correct_answer': 0
                }
            ],
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'

        """生成物理题目"""
        for i in range(count):
            question = {
                'subject': 'physics',
                'education_level': education_level,
                'topic': topic,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if topic == 'mechanics':
            elif topic == 'electromagnetism':
                question['content'] = self._generate_physics_electromagnetism(education_level, source_type)
            questions.append(question)

    def _generate_physics_mechanics(self, education_level, source_type):
        """生成物理力学题"""
                'question': f"一个物体从高度{random.randint(1, 10)}米自由下落，求落地时的速度",
                'answer': f"{math.sqrt(2 * 9.8 * random.randint(1, 10)):.2f} m/s",
            }
                'question': "一个质量为m的物体在光滑水平面上受到水平力F的作用，求加速度",
                'formula': 'F = ma',
                'difficulty': 'hard'

    def _generate_physics_electromagnetism(self, education_level, source_type):
        return {
            'formula': 'I = U/R',
            'difficulty': 'medium' if education_level == 'middle' else 'hard'
        }
        questions = []
        for i in range(count):
                'subject': 'chemistry',
                'topic': topic,
            }

                'question': f"{topic}相关的化学题目",
                'answer': "答案",

        return questions

    def generate_biology_questions(self, education_level, topic, question_type, source_type, count=20):
        """生成生物题目"""
        questions = []

        for i in range(count):
            question = {
                'education_level': education_level,
                'question_type': question_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

                'difficulty': 'medium' if education_level == 'middle' else 'hard'
            }

            questions.append(question)

    def generate_history_questions(self, education_level, topic, question_type, source_type, count=20):
        """生成历史题目"""

        for i in range(count):
            question = {
                'subject': 'history',
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                'question': f"{topic}相关的历史题目",
                'answer': "答案",
            }

            questions.append(question)
    def generate_geography_questions(self, education_level, topic, question_type, source_type, count=20):
        """生成地理题目"""

        for i in range(count):
                'id': f"geography_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'education_level': education_level,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

                'question': f"{topic}相关的地理题目",
                'answer': "答案",
                'difficulty': 'medium' if education_level == 'middle' else 'hard'

            questions.append(question)
        return questions
    def generate_politics_questions(self, education_level, topic, question_type, source_type, count=20):

        for i in range(count):
                'id': f"politics_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'politics',
                'question_type': question_type,
                'source_type': source_type,
            }

                'answer': "答案",
                'difficulty': 'medium' if education_level == 'middle' else 'hard'

            questions.append(question)

        return questions
    def save_questions(self, questions, subject):
        """保存题目到题库"""
        try:
            for question in questions:
                education_level = question.get('education_level', 'unknown')
                question_type = question.get('question_type', 'unknown')
                source_type = question.get('source_type', 'unknown')
                # 创建目录结构
                save_dir = os.path.join(
                    subject,
                    source_type
                )
                os.makedirs(save_dir, exist_ok=True)
                # 保存题目
                    json.dump(question, f, ensure_ascii=False, indent=2)

            logger.info(f"保存了 {len(questions)} 道{self.subjects[subject]['name']}题目到题库")
            return True
        except Exception as e:
    def report_to_ai_brain(self, questions):
        """将生成的题目报告到AI脑库"""
        try:
            # 生成知识条目
            knowledge_entry = {
                'type': 'comprehensive_question_generation',
                'subjects': list(set(q['subject'] for q in questions)),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'questions': questions[:10]  # 只保存前10个作为示例
            }

            # 保存到AI脑库
            with open(brain_path, 'w', encoding='utf-8') as f:

            logger.info("综合题目生成结果已报告到AI脑库")
        except Exception as e:
            logger.error(f"报告到AI脑库时出错: {str(e)}")

    def run(self, count_per_category=20):
        """运行综合题库扩充"""
            logger.info("开始扩充综合题库")

            all_questions = []
            # 生成各学科题目
            for subject, config in self.subjects.items():
                    for topic in config['topics']:
                            for source_type in self.source_types:
                                # 根据学科生成题目
                                if subject == 'chinese':
                                    questions = self.generate_chinese_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'english':
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                    questions = self.generate_physics_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                    questions = self.generate_chemistry_questions(
                                    questions = self.generate_biology_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                    questions = self.generate_history_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                    questions = self.generate_geography_questions(
                                    )
                                    questions = self.generate_politics_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                all_questions.extend(questions)

                                # 保存题目

            # 报告到AI脑库
            self.report_to_ai_brain(all_questions)

            logger.info(f"综合题库扩充完成，共生成 {len(all_questions)} 道题目")
            return True
        except Exception as e:
            logger.error(f"运行综合题库扩充时出错: {str(e)}")
            return False

    # 导入math模块
    import math

    comprehensive_bank_ai = ComprehensiveQuestionBankAI()
    comprehensive_bank_ai.run()
