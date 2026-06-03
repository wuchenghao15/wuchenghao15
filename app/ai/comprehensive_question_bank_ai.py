# -*- coding: utf-8 -*-
import os
import logging
import json
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
                'education_levels': ['primary', 'middle', 'high'],
                'topics': ['vocabulary', 'grammar', 'reading', 'writing', 'listening', 'speaking'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'translation']
            },
            'math': {
                'name': '数学',
                'education_levels': ['primary', 'middle', 'high', 'college'],
                'topics': ['arithmetic', 'algebra', 'geometry', 'calculus', 'statistics', 'probability'],
                'question_types': ['calculation', 'proof', 'application', 'multiple_choice']
            },
            'physics': {
                'name': '物理',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['mechanics', 'thermodynamics', 'electromagnetism', 'optics', 'modern_physics'],
                'question_types': ['calculation', 'proof', 'application', 'multiple_choice']
            },
            'chemistry': {
                'name': '化学',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['inorganic', 'organic', 'physical', 'analytical'],
                'question_types': ['calculation', 'reaction', 'multiple_choice', 'experiment']
            },
            'biology': {
                'name': '生物',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['cell', 'genetics', 'evolution', 'ecology', 'physiology'],
                'question_types': ['multiple_choice', 'fill_in', 'experiment', 'analysis']
            },
            'history': {
                'name': '历史',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['ancient', 'medieval', 'modern', 'contemporary'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'analysis']
            },
            'geography': {
                'name': '地理',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['physical', 'human', 'regional', 'cartography'],
                'question_types': ['multiple_choice', 'fill_in', 'map', 'analysis']
            },
            'politics': {
                'name': '政治',
                'education_levels': ['middle', 'high', 'college'],
                'topics': ['ideology', 'economics', 'law', 'ethics'],
                'question_types': ['multiple_choice', 'fill_in', 'essay', 'analysis']
            }
        }
        # 题目来源类型
        self.source_types = ['past_exam', 'difficult', 'required', 'practice', 'skill_based']

        logger.info("综合题库AI初始化完成")

    def generate_chinese_questions(self, education_level, topic, question_type, source_type, count=10):
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
                "春天来了,万物复苏.公园里的花儿开了,草儿绿了,小鸟在枝头唱歌.",
                "小明是一个勤奋的学生,他每天都认真学习,成绩一直很好.",
                "妈妈做的饭菜很香,我们全家人都喜欢吃."
            ]
        elif education_level == 'middle':
            passages = [
                "中国是一个历史悠久的国家,有着灿烂的文化和伟大的文明.",
                "科技的发展改变了我们的生活,让我们的生活更加便捷.",
                "环境保护是我们每个人的责任,我们应该从身边的小事做起."
            ]
        else:  # high:
            passages = [
                "传统文化是一个国家的精神财富,我们应该继承和发扬.",
                "人工智能的发展给人类带来了机遇和挑战,我们需要理性看待.",
                "青春是人生中最美好的时光,我们应该珍惜并努力奋斗."
            ]

        return {
            'passage': random.choice(passages),
            'questions': [
                {
                    'type': 'multiple_choice',
                    'content': '根据文章,下列哪项是正确的?',
                    'options': ['选项1', '选项2', '选项3', '选项4'],
                    'correct_answer': random.randint(0, 3)
                }
            ],
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_chinese_writing(self, education_level, source_type):
        """生成语文写作题"""
        if education_level == 'primary':
            topics = ["我的妈妈", "我的学校", "一次难忘的经历"]
        elif education_level == 'middle':
            topics = ["成长的烦恼", "友谊的力量", "科技改变生活"]
        else:  # high:
            topics = ["责任与担当", "传统文化的传承", "青春的意义"]

        return {
            'topic': random.choice(topics),
            'requirements': "请根据题目写一篇不少于800字的作文",
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_chinese_grammar(self, education_level, source_type):
        """生成语文语法题"""
        if education_level == 'primary':
            questions = ["选择正确的字:他___了一本书.A. 买 B. 卖 C. 买 D. 卖"]
        elif education_level == 'middle':
            questions = ["选择正确的成语:___山流水 A. 高 B. 青 C. 大 D. 长"]
        else:  # high:
            questions = ["选择正确的标点:他说___我明天不来了___ A. ,. B. :. C. ,! D. :!"]

        return {
            'question': random.choice(questions),
            'correct_answer': random.randint(0, 3),
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_chinese_poetry(self, education_level, source_type):
        """生成语文诗词题"""
        if education_level == 'primary':
            poems = ["床前明月光,疑是地上霜.举头望明月,低头思故乡."]
        elif education_level == 'middle':
            poems = ["春眠不觉晓,处处闻啼鸟.夜来风雨声,花落知多少."]
        else:  # high:
            poems = ["离离原上草,一岁一枯荣.野火烧不尽,春风吹又生."]
        return {
            'poem': random.choice(poems),
            'questions': [
                {
                    'content': '请补全诗句:床前明月光,___.',
                    'correct_answer': '疑是地上霜'
                }
            ]
        }

    def _generate_chinese_comprehension(self, education_level, source_type):
        """生成语文阅读理解题"""
        return {
            'passage': "阅读理解文章内容...",
            'questions': [
                {
                    'content': '根据文章内容回答问题',
                    'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
                }
            ]
        }

    def generate_english_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成英语题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"english_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'english',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            if topic == 'vocabulary':
                question['content'] = self._generate_english_vocabulary(education_level, source_type)
            elif topic == 'grammar':
                question['content'] = self._generate_english_grammar(education_level, source_type)
            elif topic == 'reading':
                question['content'] = self._generate_english_reading(education_level, source_type)
            elif topic == 'writing':
                question['content'] = self._generate_english_writing(education_level, source_type)
            elif topic == 'listening':
                question['content'] = self._generate_english_listening(education_level, source_type)

            questions.append(question)

        return questions

    def _generate_english_vocabulary(self, education_level, source_type):
        """生成英语词汇题"""
        if education_level == 'primary':
            words = ["interesting", "difficult", "important", "beautiful"]
        else:
            words = ["sophisticated", "comprehensive", "fundamental", "significant"]
        return {
            'question': f"What does '{random.choice(words)}' mean?",
            'correct_answer': random.randint(0, 3),
            'difficulty': 'easy' if education_level == 'primary' else 'medium'
        }

    def _generate_english_grammar(self, education_level, source_type):
        """生成英语语法题"""
        if education_level == 'primary':
            questions = ["Choose the correct word: I ___ to school every day. A. go B. goes C. went D. going"]
        elif education_level == 'middle':
            questions = ["Choose the correct tense: He ___ to school yesterday. A. go B. goes C. went D. going"]
        else:  # high:
            questions = ["Choose the correct sentence: A. I have been to Paris last year. B. I went to Paris last year."]

        return {
            'question': random.choice(questions),
            'correct_answer': random.randint(0, 3),
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_english_reading(self, education_level, source_type):
        """生成英语阅读题"""
        if education_level == 'primary':
            passages = ["English is fun. I like learning English."]
        elif education_level == 'middle':
            passages = ["English is an important language. It is spoken by people all over the world. We should learn it well."]
        else:
            passages = ["The development of technology has changed our lives in many ways. It has made our lives more convenient."]

        return {
            'passage': random.choice(passages),
            'questions': [
                {
                    'content': 'According to the passage, which is correct?',
                    'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                    'correct_answer': random.randint(0, 3)
                }
            ],
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_english_writing(self, education_level, source_type):
        """生成英语写作题"""
        if education_level == 'primary':
            topics = ["My Family", "My School", "My Favorite Animal"]
        elif education_level == 'middle':
            topics = ["My Best Friend", "My Hobby", "My Dream"]
        else:
            topics = ["The Importance of Education", "Environmental Protection", "Technology and Life"]

        return {
            'topic': random.choice(topics),
            'requirements': "Write a composition of at least 100 words",
            'difficulty': 'easy' if education_level == 'primary' else 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_english_listening(self, education_level, source_type):
        """生成英语听力题"""
        dialogues = [
            "What's your name? My name is John. Nice to meet you. Nice to meet you too."
        ]
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
        }

    def generate_physics_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成物理题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"physics_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'physics',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            if topic == 'mechanics':
                question['content'] = self._generate_physics_mechanics(education_level, source_type)
            elif topic == 'electromagnetism':
                question['content'] = self._generate_physics_electromagnetism(education_level, source_type)

            questions.append(question)

        return questions

    def _generate_physics_mechanics(self, education_level, source_type):
        """生成物理力学题"""
        return {
            'question': f"一个物体从高度{random.randint(1, 10)}米自由下落,求落地时的速度",
            'answer': f"{(2 * 9.8 * random.randint(1, 10))**0.5:.2f} m/s",
            'difficulty': 'medium' if education_level == 'middle' else 'hard'
        }

    def _generate_physics_electromagnetism(self, education_level, source_type):
        """生成物理电磁学题"""
        return {
            'question': "欧姆定律是什么?",
            'answer': "I = U/R",
            'difficulty': 'medium' if education_level == 'middle' else 'hard'
        }

    def generate_chemistry_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成化学题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"chemistry_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'chemistry',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': {
                    'question': f"{topic}相关的化学题目",
                    'answer': "答案"
                }
            }

            questions.append(question)

        return questions

    def generate_biology_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成生物题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"biology_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'biology',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': {
                    'question': f"{topic}相关的生物题目",
                    'answer': "答案",
                    'difficulty': 'medium' if education_level == 'middle' else 'hard'
                }
            }

            questions.append(question)

        return questions

    def generate_history_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成历史题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"history_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'history',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': {
                    'question': f"{topic}相关的历史题目",
                    'answer': "答案"
                }
            }

            questions.append(question)

        return questions

    def generate_geography_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成地理题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"geography_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'geography',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': {
                    'question': f"{topic}相关的地理题目",
                    'answer': "答案",
                    'difficulty': 'medium' if education_level == 'middle' else 'hard'
                }
            }

            questions.append(question)

        return questions

    def generate_politics_questions(self, education_level, topic, question_type, source_type, count=10):
        """生成政治题目"""
        questions = []

        for i in range(count):
            question = {
                'id': f"politics_{education_level}_{topic}_{question_type}_{source_type}_{int(time.time())}_{i}",
                'subject': 'politics',
                'education_level': education_level,
                'topic': topic,
                'question_type': question_type,
                'source_type': source_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content': {
                    'question': f"{topic}相关的政治题目",
                    'answer': "答案",
                    'difficulty': 'medium' if education_level == 'middle' else 'hard'
                }
            }

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
                    self.comprehensive_bank_dir,
                    subject,
                    education_level,
                    question_type,
                    source_type
                )
                os.makedirs(save_dir, exist_ok=True)
                
                # 保存题目
                file_path = os.path.join(save_dir, f"{question['id']}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(question, f, ensure_ascii=False, indent=2)

            logger.info(f"保存了 {len(questions)} 道{self.subjects[subject]['name']}题目到题库")
            return True
        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False

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
            brain_path = os.path.join(self.ai_brain_dir, f"comprehensive_questions_{int(time.time())}.json")
            with open(brain_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)

            logger.info("综合题目生成结果已报告到AI脑库")
            return True
        except Exception as e:
            logger.error(f"报告到AI脑库时出错: {str(e)}")
            return False

    def run(self, count_per_category=20):
        """运行综合题库扩充"""
        try:
            logger.info("开始扩充综合题库")

            all_questions = []
            # 生成各学科题目
            for subject, config in self.subjects.items():
                for education_level in config['education_levels']:
                    for topic in config['topics']:
                        for question_type in config['question_types']:
                            for source_type in self.source_types:
                                # 根据学科生成题目
                                if subject == 'chinese':
                                    questions = self.generate_chinese_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'english':
                                    questions = self.generate_english_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'physics':
                                    questions = self.generate_physics_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'chemistry':
                                    questions = self.generate_chemistry_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'biology':
                                    questions = self.generate_biology_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'history':
                                    questions = self.generate_history_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'geography':
                                    questions = self.generate_geography_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                elif subject == 'politics':
                                    questions = self.generate_politics_questions(
                                        education_level, topic, question_type, source_type, count_per_category
                                    )
                                else:
                                    questions = []
                                
                                all_questions.extend(questions)

                                # 保存题目
                                self.save_questions(questions, subject)

            # 报告到AI脑库
            if all_questions:
                self.report_to_ai_brain(all_questions)

            logger.info(f"综合题库扩充完成,共生成 {len(all_questions)} 道题目")
            return True
        except Exception as e:
            logger.error(f"运行综合题库扩充时出错: {str(e)}")
            return False


if __name__ == "__main__":
    import math
    comprehensive_bank_ai = ComprehensiveQuestionBankAI()
    comprehensive_bank_ai.run()
