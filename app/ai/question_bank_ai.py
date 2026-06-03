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
        logging.FileHandler(os.path.join(logs_dir, 'question_bank_ai.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class QuestionBankAI:
    """自动扩充题库AI"""

    def __init__(self):
        """初始化题库AI"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_root, '../data')
        self.question_bank_dir = os.path.join(self.data_dir, 'question_bank')
        self.ai_brain_dir = os.path.join(self.data_dir, 'ai_brain')

        os.makedirs(self.question_bank_dir, exist_ok=True)
        os.makedirs(self.ai_brain_dir, exist_ok=True)

        self.languages = {
            'chinese': {
                'name': '中文',
                'dialects': ['standard'],
                'levels': ['beginner', 'intermediate', 'advanced']
            },
            'english': {
                'name': '英语',
                'dialects': ['american', 'british'],
                'levels': ['beginner', 'intermediate', 'advanced']
            },
            'japanese': {
                'name': '日语',
                'dialects': ['kanto', 'kansai'],
                'levels': ['beginner', 'intermediate', 'advanced']
            }
        }

        self.question_types = ['listening', 'reading', 'grammar', 'vocabulary', 'writing']

        logger.info("题库AI初始化完成")

    def generate_listening_questions(self, language, dialect, level, count=10):
        """生成听力题"""
        questions = []
        for i in range(count):
            question = {
                'id': f"{language}_{dialect}_{level}_listening_{int(time.time())}_{i}",
                'language': language,
                'dialect': dialect,
                'level': level,
                'type': 'listening',
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if language == 'chinese':
                question['content'] = self._generate_chinese_listening(dialect, level)
            elif language == 'english':
                question['content'] = self._generate_english_listening(dialect, level)
            elif language == 'japanese':
                question['content'] = self._generate_japanese_listening(dialect, level)
            questions.append(question)
        return questions

    def _generate_chinese_listening(self, dialect, level):
        """生成中文听力题"""
        if level == 'beginner':
            dialogues = [
                '你好,请问你叫什么名字?我叫小明。很高兴认识你。',
                '今天天气怎么样?今天天气很好,阳光明媚。',
                '你喜欢吃什么?我喜欢吃米饭和蔬菜。',
                '你来自哪里?我来自北京。',
                '现在几点了?现在是下午三点。'
            ]
        elif level == 'intermediate':
            dialogues = [
                '你周末打算做什么?我打算去公园散步,然后去书店买书。',
                '你觉得这部电影怎么样?我觉得非常好看,演员的表演很精彩。',
                '你学习中文多久了?我学习中文已经两年了。',
                '你喜欢什么运动?我喜欢打篮球和游泳。',
                '你对中国的印象如何?中国是一个历史悠久的国家,文化丰富多彩。'
            ]
        else:  # advanced:
            dialogues = [
                '中国的传统文化博大精深,包括书法、绘画、武术等多种形式。',
                '随着科技的发展,人工智能在各个领域都发挥着越来越重要的作用。',
                '环境保护是当今世界面临的重要挑战,需要每个人的共同努力。',
                '中国的经济发展速度很快,已经成为世界第二大经济体。',
                '学习语言不仅要掌握语法和词汇,还要了解相关的文化背景。'
            ]
        return {
            'dialogue': random.choice(dialogues),
            'audio_url': f"https://example.com/audio/chinese/{dialect}/{level}/{random.randint(1, 100)}.mp3",
            'questions': [
                {
                    'type': 'multiple_choice',
                    'content': '根据对话,下列哪项是正确的?',
                    'options': ['选项1', '选项2', '选项3', '选项4'],
                    'correct_answer': random.randint(0, 3)
                }
            ]
        }

    def _generate_english_listening(self, dialect, level):
        """生成英语听力题"""
        if level == 'beginner':
            dialogues = [
                "Hello, what's your name? My name is John. Nice to meet you.",
                "What time is it now? It's three o'clock in the afternoon.",
                "Where are you from? I'm from the United States.",
                "Do you like coffee? Yes, I do. I drink it every morning."
            ]
        elif level == 'intermediate':
            dialogues = [
                "What are you going to do this weekend? I'm going to visit my friends and watch a movie.",
                "How long have you been learning English? I've been learning English for three years.",
                "What's your favorite hobby? My favorite hobby is playing the guitar."
            ]
        else:  # advanced:
            dialogues = [
                "The development of technology has significantly changed our daily lives in many ways.",
                "Climate change is a global issue that requires immediate action from all countries.",
                "The importance of education cannot be overstated in today's competitive world."
            ]
        dialogue = random.choice(dialogues)
        return {
            'dialogue': dialogue,
            'audio_url': f"https://example.com/audio/english/{dialect}/{level}/{random.randint(1, 100)}.mp3",
            'questions': [
                {
                    'type': 'multiple_choice',
                    'content': 'According to the dialogue, which is correct?',
                    'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                    'correct_answer': random.randint(0, 3)
                }
            ]
        }

    def _generate_japanese_listening(self, dialect, level):
        """生成日语听力题"""
        if level == 'beginner':
            dialogues = [
                'こんにちは、お名前は何ですか?私はたろうです。はじめまして。',
                '今日はいい天気ですね。ええ、そうですね。暖かいです。',
                '何が好きですか?私はりんごが好きです。'
            ]
        elif level == 'intermediate':
            dialogues = [
                'この映画はどうでしたか?とても面白かったです。',
                'どんなスポーツが好きですか?サッカーと野球が好きです。'
            ]
        else:  # advanced:
            dialogues = [
                '環境保護は世界中の重要な課題であり、みんなの協力が必要です。'
            ]
        dialogue = random.choice(dialogues)
        return {
            'dialogue': dialogue,
            'audio_url': f"https://example.com/audio/japanese/{dialect}/{level}/{random.randint(1, 100)}.mp3",
            'questions': [
                {
                    'content': '会話によると、正しいのはどれですか?',
                    'options': ['オプション1', 'オプション2', 'オプション3', 'オプション4'],
                    'correct_answer': random.randint(0, 3)
                }
            ]
        }

    def generate_other_questions(self, language, level, question_type, count=10):
        """生成其他类型题目"""
        questions = []
        for i in range(count):
            question = {
                'id': f"{language}_{level}_{question_type}_{int(time.time())}_{i}",
                'language': language,
                'level': level,
                'type': question_type,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            if question_type == 'reading':
                question['content'] = self._generate_reading_question(language, level)
            elif question_type == 'grammar':
                question['content'] = self._generate_grammar_question(language, level)
            elif question_type == 'vocabulary':
                question['content'] = self._generate_vocabulary_question(language, level)
            elif question_type == 'writing':
                question['content'] = self._generate_writing_question(language, level)
            questions.append(question)
        return questions

    def _generate_reading_question(self, language, level):
        """生成阅读题"""
        texts = {
            'chinese': {
                'beginner': '今天天气很好。小明去公园玩。',
                'intermediate': '随着社会的发展,人们的生活水平不断提高。越来越多的人关注健康和环境问题。',
                'advanced': '人工智能技术的快速发展正在改变我们的生活和工作方式。未来,AI将在更多领域发挥重要作用。'
            },
            'english': {
                'beginner': 'Today is a sunny day. John goes to the park.',
                'intermediate': 'With the development of society, people\'s living standards are improving. More and more people are paying attention to health and environmental issues.',
                'advanced': 'The rapid development of artificial intelligence technology is changing the way we live and work. In the future, AI will play an important role in more fields.'
            },
            'japanese': {
                'beginner': '今日はいい天気です。たろうは公園へ行きます。',
                'intermediate': '社会の発展につれて、人々の生活水準は向上しています。ますます多くの人々が健康と環境問題に注目しています。',
                'advanced': '人工知能技術の急速な発展は、私たちの生活と仕事の方法を変えています。未来、AIはより多くの分野で重要な役割を果たすでしょう。'
            }
        }
        return {
            'text': texts[language][level],
            'questions': [
                {
                    'type': 'multiple_choice',
                    'content': '根据文章,下列哪项是正确的?' if language == 'chinese' else 'According to the text, which is correct?',
                    'options': ['选项1', '选项2', '选项3', '选项4'] if language == 'chinese' else ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                    'correct_answer': random.randint(0, 3)
                }
            ]
        }

    def _generate_grammar_question(self, language, level):
        """生成语法题"""
        if language == 'chinese':
            questions = {
                'beginner': '选择正确的词语: 他____去学校。 A. 正在 B. 已经 C. 将要 D. 刚刚',
                'intermediate': '选择正确的句子: A. 我昨天去了北京。 B. 我昨天去北京了。 C. 我去了昨天北京。 D. 昨天我去了北京。',
                'advanced': '选择正确的关联词: ____天气不好,____我们还是决定去爬山。 A. 因为...所以 B. 虽然...但是 C. 不仅...而且 D. 无论...都'
            }
        elif language == 'english':
            questions = {
                'beginner': 'Choose the correct word: He ___ to school every day. A. go B. goes C. went D. going',
                'intermediate': 'Choose the correct sentence: A. I have been to Paris last year. B. I went to Paris last year. C. I go to Paris last year. D. I was going to Paris last year.',
                'advanced': 'Choose the correct tense: By next year, I ___ my degree. A. will complete B. will have completed C. have completed D. completed'
            }
        else:  # japanese:
            questions = {
                'beginner': '正しい言葉を選びなさい: 彼は毎日学校に____。 A. 行く B. 行きます C. 行って D. 行った',
                'intermediate': '正しい文を選びなさい: A. 私は昨日東京に行きました。 B. 私は昨日東京に行くました。 C. 私は東京に昨日行きました。 D. 昨日私は東京に行きました。',
                'advanced': '正しい接続詞を選びなさい: ____雨が降っていた、____私たちは山に登ることにしました。 A. なぜなら...だから B. たとえ...でも C. 不但...而且 D. 无论...都'
            }
        return {
            'question': questions[level],
            'correct_answer': random.randint(0, 3)
        }

    def _generate_vocabulary_question(self, language, level):
        """生成词汇题"""
        if language == 'chinese':
            questions = {
                'beginner': '选择与"高兴"意思相近的词语: A. 难过 B. 快乐 C. 生气 D. 害怕',
                'intermediate': '选择"犹豫"的正确解释: A. 坚决 B. 犹豫 C. 果断 D. 迅速',
                'advanced': '选择"邂逅"的正确解释: A. 偶然相遇 B. 故意等待 C. 计划见面 D. 避免相见'
            }
        elif language == 'english':
            questions = {
                'beginner': 'Choose the word that means "happy": A. sad B. happy C. angry D. scared',
                'intermediate': 'Choose the correct meaning of "hesitate": A. decide firmly B. pause before acting C. act quickly D. refuse completely',
                'advanced': 'Choose the correct meaning of "encounter": A. meet by chance B. wait intentionally C. plan to meet D. avoid meeting'
            }
        else:  # japanese:
            questions = {
                'beginner': '「嬉しい」と同じ意味の言葉を選びなさい: A. 悲しい B. 楽しい C. 怒っている D. 怖い',
                'intermediate': '「ためらう」の正しい意味を選びなさい: A. 断固として B. ためらう C. 果断に D. 速く',
                'advanced': '「出会う」の正しい意味を選びなさい: A. 偶然に出会う B. 故意に待つ C. 会う予定を立てる D. 会うのを避ける'
            }
        return {
            'question': questions[level],
            'correct_answer': random.randint(0, 3)
        }

    def _generate_writing_question(self, language, level):
        """生成写作题"""
        if language == 'chinese':
            topics = {
                'beginner': '我的家庭',
                'intermediate': '我的梦想',
                'advanced': '科技对生活的影响'
            }
            requirements = {
                'beginner': '请写一段话介绍你的家庭,不少于50字。',
                'intermediate': '请写一篇作文介绍你的梦想,不少于200字。',
                'advanced': '请写一篇议论文讨论科技对生活的影响,不少于500字。'
            }
        elif language == 'english':
            topics = {
                'beginner': 'My Family',
                'intermediate': 'My Dream',
                'advanced': 'The Impact of Technology on Life'
            }
            requirements = {
                'beginner': 'Write a short paragraph about your family, at least 50 words.',
                'intermediate': 'Write an essay about your dream, at least 200 words.',
                'advanced': 'Write an argumentative essay discussing the impact of technology on life, at least 500 words.'
            }
        else:  # japanese:
            topics = {
                'beginner': '私の家族',
                'intermediate': '私の夢',
                'advanced': 'テクノロジーが生活に与える影響'
            }
            requirements = {
                'beginner': 'あなたの家族について短い文章を書きなさい。少なくとも50文字。',
                'intermediate': 'あなたの夢について作文を書きなさい。少なくとも200文字。',
                'advanced': 'テクノロジーが生活に与える影響について論文を書きなさい。少なくとも500文字。'
            }
        return {
            'topic': topics[level],
            'requirements': requirements[level]
        }

    def save_questions(self, questions, language):
        """保存题目到题库"""
        try:
            for question in questions:
                question_type = question['type']
                level = question['level']
                save_dir = os.path.join(self.question_bank_dir, language, level, question_type)
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, f"{question['id']}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(question, f, ensure_ascii=False, indent=2)
            logger.info(f"保存了 {len(questions)}道题目到题库")
            return True
        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False

    def report_to_ai_brain(self, questions):
        """将生成的题目报告到AI脑库"""
        try:
            knowledge_entry = {
                'type': 'question_generation',
                'languages': list(set(q['language'] for q in questions)),
                'question_types': list(set(q['type'] for q in questions)),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'questions': questions[:5]
            }
            brain_path = os.path.join(self.ai_brain_dir, f"questions_{int(time.time())}.json")
            with open(brain_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)
            logger.info("题目生成结果已报告到AI脑库")
            return True
        except Exception as e:
            logger.error(f"报告到AI脑库时出错: {str(e)}")
            return False

    def run(self, count_per_language=20):
        """运行题库扩充"""
        try:
            logger.info("开始扩充题库")
            all_questions = []

            for language, config in self.languages.items():
                for dialect in config['dialects']:
                    for level in config['levels']:
                        listening_questions = self.generate_listening_questions(language, dialect, level, count_per_language // 4)
                        all_questions.extend(listening_questions)
                        self.save_questions(listening_questions, language)

                        for question_type in self.question_types:
                            if question_type != 'listening':
                                other_questions = self.generate_other_questions(language, level, question_type, count_per_language // 4)
                                all_questions.extend(other_questions)
                                self.save_questions(other_questions, language)

            if all_questions:
                self.report_to_ai_brain(all_questions)
            logger.info(f"题库扩充完成,共生成 {len(all_questions)}道题目")
            return True
        except Exception as e:
            logger.error(f"运行题库扩充时出错: {str(e)}")
            return False


if __name__ == "__main__":
    question_bank_ai = QuestionBankAI()
    question_bank_ai.run()
