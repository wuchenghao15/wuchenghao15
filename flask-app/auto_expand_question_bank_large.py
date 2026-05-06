#!/usr/bin/env python3
"""
利用AI和Python技术自动完善并拓展题库
目标：生成10000道不重复且包含所有题型的题目

import sqlite3
# JSON import removed - using database
import random
import time
import sys
import os
from typing import List, Dict, Any, Set

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 简化题目生成器，避免依赖复杂的Flask应用
class SimpleQuestionGenerator:
    """简化的题目生成器，用于自动扩充题库"""

    def __init__(self):
        # 支持的语言
        self.supported_languages = ['japanese', 'english', 'chinese']
        # 支持的类别
        self.supported_categories = ['词汇', '语法', '阅读', '听力', '写作', '口语', '翻译']
        # 支持的难度
        self.supported_difficulties = [1, 2, 3, 4, 5]
        # 支持的题目类型
        self.supported_question_types = ['single', 'multiple', 'fill', 'short_answer', 'essay', 'speaking', 'translation']

        # 增强的题目模板，增加更多变化
        self.question_templates = {
            'japanese': {
                '词汇': [
                    "{word}の正しい意味はどれですか？",
                    "{word}の同義語はどれですか？",
                    "{word}の反義語はどれですか？",
                    "{word}を使った正しい文はどれですか？",
                    "{word}の品詞は何ですか？",
                    "{word}の敬語形は何ですか？",
                    "{word}の過去形は何ですか？",
                    "{word}の否定形は何ですか？"
                ],
                '语法': [
                    "{sentence}の空欄に入る最も適切な単語はどれですか？",
                    "{sentence}の文法形式は何ですか？",
                    "{sentence}の正しい形はどれですか？",
                    "次の文の中で文法的に正しいものはどれですか？",
                    "{sentence}の{part}の使い方は正しいですか？",
                    "{sentence}の時制は何ですか？",
                    "{sentence}の関係代名詞は何ですか？",
                    "{sentence}の助詞の使い方は正しいですか？"
                ],
                    "次の文章を読んで、質問に答えてください。\n{paragraph}\n質問：{question}",
                    "この文章の主旨は何ですか？\n{paragraph}",
                    "文中の{word}の意味は何ですか？\n{paragraph}",
                    "この文章から分かることはどれですか？\n{paragraph}",
                    "作者の意見はどれですか？\n{paragraph}"
                ],
                    "会話を聞いて、質問に答えてください。\n質問：{question}",
                    "次の音声内容について正しいのはどれですか？",
                    "スピーカーの主張は何ですか？",
                    "会話の目的は何ですか？",
                    "会話の中で言及された内容はどれですか？"
                ],
                    "{topic}について、{word_count}字程度で作文を書いてください。",
                    "次の図表を見て、内容をまとめてください。\n{chart}\n要求：{requirements}",
                    "{situation}について、手紙を書いてください。\n要求：{requirements}",
                    "{topic}について、意見を述べてください。\n要求：{requirements}"
                ],
                    "{topic}について、{duration}程度で話してください。",
                    "自己紹介をしてください。（{duration}）",
                    "{situation}について、対話を行ってください。",
                    "{topic}の利点と欠点について話してください。",
                    "{experience}について、経験談をしてください。"
                ],
                    "次の文を日本語に翻訳してください：{sentence}",
                    "次の文を{target_lang}に翻訳してください：{sentence}",
                    "文中の{phrase}の正しい翻訳はどれですか？\n{sentence}",
                    "次の文章を{target_lang}に翻訳してください：\n{paragraph}"
                ]
            },
            'english': {
                '词汇': [
                    "What is the synonym of '{word}'?",
                    "What is the antonym of '{word}'?",
                    "Which sentence uses '{word}' correctly?",
                    "What part of speech is '{word}'?",
                    "What is the past tense of '{word}'?",
                    "What is the plural form of '{word}'?",
                    "What is the comparative form of '{word}'?"
                ],
                '语法': [
                    "What is the grammatical form of {word}?",
                    "Which sentence is grammatically correct?",
                    "What tense is used in the sentence: {sentence}",
                    "Which preposition should be used in: {sentence}",
                    "What is the correct subject-verb agreement in: {sentence}",
                    "Which relative pronoun should be used in: {sentence}",
                ],
                '阅读': [
                    "What is the main idea of this passage?\n{paragraph}",
                    "What does '{word}' mean in the context?\n{paragraph}",
                    "Which of the following can be inferred from the passage?\n{paragraph}",
                    "What is the author's opinion on {topic}?\n{paragraph}"
                ],
                '听力': [
                    "Which of the following is true according to the audio?",
                    "What is the speaker's main point?",
                    "What information is mentioned in the conversation?"
                ],
                '写作': [
                    "Summarize the information in the chart below.\n{chart}\nRequirements: {requirements}",
                    "Write a letter about {situation}.\nRequirements: {requirements}",
                    "Express your opinion on {topic}.\nRequirements: {requirements}"
                ],
                    "Introduce yourself. ({duration})",
                    "Have a conversation about {situation}.",
                    "Discuss the advantages and disadvantages of {topic}.",
                    "Share an experience about {experience}."
                ],
                '翻译': [
                    "Translate the following sentence into {target_lang}: {sentence}",
                    "Translate the following passage into {target_lang}:\n{paragraph}"
                ]
            },
            'chinese': {
                '词汇': [
                    '"{word}"的同义词是？',
                    '下列句子中"{word}"使用正确的是？',
                    '"{word}"的词性是什么？',
                    '"{word}"的近义词是？',
                    '"{word}"的反义词是？',
                    '"{word}"的成语是？'
                ],
                '语法': [
                    '以下哪个句子语法正确？',
                    '"{sentence}"的{part}使用正确吗？',
                    '"{sentence}"的句式是什么？',
                    '"{sentence}"的时态是什么？',
                    '"{sentence}"的标点符号使用正确吗？',
                ],
                    '阅读下列文章，回答问题。\n{paragraph}\n问题：{question}',
                    '文中"{word}"的意思是什么？\n{paragraph}',
                    '从文章中可以推断出什么？\n{paragraph}',
                    '作者的观点是什么？\n{paragraph}'
                '听力': [
                    '听对话，回答问题。\n问题：{question}',
                    '说话者的主要观点是什么？',
                    '对话的目的是什么？',
                    '对话中提到的内容是哪项？'
                '写作': [
                    '请以"{topic}"为题，写一篇{word_count}字左右的作文。',
                    '请就{situation}写一封信。\n要求：{requirements}',
                    '请就{topic}发表你的看法。\n要求：{requirements}'
                ],
                    '请就"{topic}"话题，说{duration}左右。',
                    '请就{situation}进行对话。',
                    '请谈谈"{topic}"的优缺点。',
                    '请分享一次关于{experience}的经历。'
                ],
                '翻译': [
                    '请将"{sentence}"翻译成中文。',
                    '文中"{phrase}"的正确翻译是哪项？\n{sentence}',
                ]
            }
        }

        # 简单的选项生成器
        self.option_templates = {
            'single': ['A', 'B', 'C', 'D'],
            'multiple': ['A', 'B', 'C', 'D', 'E']

        # 增强的单词库
        self.word_libraries = {
            'japanese': {
                '语法': ['です', 'ます', 'て', 'た', 'ない', 'いる', 'ある', 'する', 'くる', 'あげる', 'くれる', 'もらう', 'れる', 'られる', 'させる', 'される', 'の', 'を', 'に', 'へ', 'と', 'が', 'は', 'で', 'から', 'まで', 'より', 'ので', 'から', 'ために', 'のに', 'けど', 'が', 'でも', 'それで', 'そこで', 'だから', 'し', 'て', 'ながら', 'つつ', 'たり', 'と', 'や', 'など', 'か', 'も', 'ばかり', 'だけ', 'しか', 'ほど', 'くらい', 'よう', 'みたい', 'らしい', 'そう', 'ようだ', 'みたいだ', 'らしいだ', 'そうだ', 'の', 'こと', 'もの', 'ところ', 'ほう', 'ため', 'うち', '間', 'まで', 'までに', 'から', 'より', 'まで', 'きり', 'ば', 'たら', 'なら', 'と', 'うち', '間', 'まで', 'までに', 'から', 'より', 'まで', 'きり']
            },
            'english': {
                '语法': ['is', 'am', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'ought to', 'used to', 'be able to', 'be going to', 'be about to', 'be supposed to', 'be willing to', 'be eager to', 'be afraid to', 'be interested in', 'be good at', 'be bad at', 'be used to', 'get used to', 'used to', 'would rather', 'had better', 'it is time', 'it is necessary', 'it is important', 'it is possible', 'it is easy', 'it is difficult', 'there is', 'there are', 'there was', 'there were', 'there will be', 'there would be', 'who', 'whom', 'whose', 'which', 'that', 'what', 'when', 'where', 'why', 'how', 'if', 'whether', 'because', 'since', 'as', 'for', 'so', 'but', 'or', 'and', 'yet', 'nor', 'not only...but also...', 'either...or...', 'neither...nor...', 'both...and...', 'so...that...', 'such...that...', 'too...to...', 'enough...to...', 'as...as...', 'not as...as...', 'not so...as...', 'the...the...']
            },
            'chinese': {
                '词汇': ['你好', '谢谢', '再见', '是', '不', '朋友', '学校', '吃', '喝', '去', '来', '看', '听', '说', '写', '读', '学习', '工作', '家', '车', '火车', '飞机', '旅行', '音乐', '电影', '书', '狗', '猫', '花', '树', '山', '河', '海', '天气', '季节', '时间', '日期', '星期', '年', '月', '日', '时', '分', '秒', '争吵', '感激', '邂逅', '拒绝', '放弃', '努力', '成功', '失败', '幸福', '悲伤', '喜悦', '愤怒', '惊讶', '恐惧', '希望', '失望', '梦想', '目标', '计划', '行动', '结果', '原因', '理由', '方法', '手段', '目的', '意义', '价值', '重要', '必要', '可能', '不可能', '容易', '困难', '简单', '复杂', '美丽', '丑陋', '大', '小', '高', '低', '长', '短', '宽', '窄', '深', '浅', '重', '轻', '快', '慢', '早', '晚', '多', '少', '强', '弱', '热', '冷', '暖', '凉', '甜', '辣', '酸', '苦', '咸'],
                '语法': ['的', '了', '着', '过', '吧', '呢', '吗', '啊', '呀', '啦', '和', '与', '及', '跟', '同', '或', '或者', '还是', '但', '但是', '然而', '可是', '不过', '却', '而', '因为', '所以', '因此', '因而', '由于', '既然', '如果', '假如', '假设', '要是', '倘若', '若', '即使', '即便', '哪怕', '虽然', '尽管', '固然', '虽然...但是...', '因为...所以...', '如果...就...', '只要...就...', '只有...才...', '无论...都...', '不管...总...', '即使...也...', '既然...就...', '与其...不如...', '宁可...也不...', '一边...一边...', '一面...一面...', '又...又...', '既...又...', '不是...而是...', '是...还是...', '不是...就是...', '要么...要么...', '与其...毋宁...', '之所以...是因为...']
            }
        }

        self.sentence_libraries = {
            'japanese': {
                '阅读': ['日本の春は3月から5月までです。桜が咲いて、とてもきれいです。多くの人が花見に行きます。', '昨日、私は友達と映画を見に行きました。映画はとても面白かったです。帰りに、レストランで食事をしました。', '毎日、私は学校に行きます。学校では、日本語、英語、数学などを勉強します。友達と一緒に食事をしたり、遊んだりします。', '近年、日本の高齢化が進んでいます。65歳以上の人口が増えて、社会保障費が増加しています。政府は様々な対策を講じています。', '日本の経済は高度成長期を経て、世界第3位の経済大国になりました。近年は少子化や高齢化の影響で、成長率が低くなっています。'],
                '听力': ['A: こんにちは。B: こんにちは。', 'A: 昨日何をしましたか？B: 映画を見ました。', 'A: 毎日何時に起きますか？B: 7時に起きます。', 'A: 明日は何をしますか？B: 友達と遊びます。', 'A: この本はいくらですか？B: 1000円です。']
            },
            'english': {
                '阅读': ['Spring in Japan is from March to May. Cherry blossoms bloom and it is very beautiful. Many people go to see the cherry blossoms.', 'Yesterday, I went to the movies with my friends. The movie was very interesting. On the way back, we ate dinner at a restaurant.', 'Every day, I go to school. At school, I study Japanese, English, math, etc. I eat and play with my friends.', 'In recent years, Japan has been aging. The population over 65 has increased, and social security costs have increased. The government is taking various measures.', 'Japans economy has become the third largest in the world through a period of high growth. In recent years, growth rates have slowed due to the effects of declining birthrates and aging.'],
                '听力': ['A: Hello. B: Hello.', 'A: What did you do yesterday? B: I watched a movie.', 'A: What time do you get up every day? B: I get up at 7 oclock.', 'A: What will you do tomorrow? B: I will play with my friends.', 'A: How much is this book? B: It is 1000 yen.']
            },
            'chinese': {
                '语法': ['我____学生。', '昨天，我____电影。', '每天，我____学校。', '他说他____来。', '如果下雨，我____去。', '我每天早上7点____。', '她英语____。', '这本书很____。', '他去年____日本。', '我和朋友____。'],
                '阅读': ['日本的春天是3月到5月。樱花盛开，非常美丽。很多人去赏花。', '昨天，我和朋友去看电影了。电影非常有趣。回来的时候，我们在餐厅吃了饭。', '每天，我都去上学。在学校里，我学习日语、英语、数学等。我和朋友一起吃饭、玩耍。', '近年来，日本的老龄化在加剧。65岁以上的人口在增加，社会保障费用也在增加。政府正在采取各种对策。', '日本经济经过高度成长期，成为世界第三大经济大国。近年来，由于少子化和老龄化的影响，增长率变低了。'],
                '听力': ['A: 你好。B: 你好。', 'A: 昨天你做了什么？B: 我看了电影。', 'A: 你每天几点起床？B: 我7点起床。', 'A: 明天你要做什么？B: 我要和朋友玩。', 'A: 这本书多少钱？B: 1000日元。']
            }
        }

        # 增强的段落库
        self.paragraph_libraries = {
            'japanese': {
                '翻译': ['日本はアジアの東に位置する島国です。四季がはっきりしていて、それぞれの季節に美しい景色があります。春には桜が咲き、夏は海で泳いだり山で登山したりでき、秋は紅葉が美しく、冬は雪が降ってスキーができます。日本の文化は非常に豊かで、茶道、華道、歌舞伎、能などの伝統文化があります。また、日本の食文化も世界的に有名で、寿司、天ぷら、焼肉などが人気です。日本は技術が進んでいて、自動車、電子機器、精密機械などの産業が盛んです。東京は日本の首都であり、世界最大の都市の一つです。']
            },
            'english': {
                '翻译': ['Japan is an island country located in East Asia. It has four distinct seasons, each with beautiful scenery. In spring, cherry blossoms bloom; in summer, you can swim in the sea or climb mountains; in autumn, the autumn leaves are beautiful; and in winter, it snows and you can ski. Japanese culture is very rich, with traditional cultures such as tea ceremony, flower arrangement, kabuki, and noh. Japanese food culture is also world-famous, with sushi, tempura, and yakiniku being popular. Japan is advanced in technology, with thriving industries such as automobiles, electronic devices, and precision machinery. Tokyo is the capital of Japan and one of the largest cities in the world.']
            },
                '翻译': ['日本是位于东亚的岛国。四季分明，每个季节都有美丽的景色。春天樱花盛开，夏天可以在海里游泳或在山上登山，秋天红叶美丽，冬天下雪可以滑雪。日本的文化非常丰富，有茶道、花道、歌舞伎、能剧等传统文化。另外，日本的饮食文化也世界闻名，寿司、天妇罗、烤肉等很受欢迎。日本技术先进，汽车、电子设备、精密机械等产业发达。东京是日本的首都，是世界上最大的城市之一。']
            }
        }

        self.topic_libraries = {
            'japanese': {
                '口语': ['自己紹介', '私の趣味', '私の家族', '私の友達', '私の学校', '私の夢', '私の好きな食べ物', '私の好きなスポーツ', '私の好きな本', '私の好きな映画', '私の旅行', '私の夏休み', '私の冬休み', '私の春休み', '私の秋休み', '私の故郷', '私の将来の計画', '私の勉強方法', '私の得意な科目', '私の苦手な科目']
            },
            'english': {
                '写作': ['My Day', 'My Hobby', 'My Family', 'My Friend', 'My School', 'My Dream', 'My Favorite Food', 'My Favorite Sport', 'My Favorite Book', 'My Favorite Movie', 'My Trip', 'My Summer Vacation', 'My Winter Vacation', 'My Spring Vacation', 'My Fall Vacation', 'My Hometown', 'My Future Plan', 'My Study Method', 'My Favorite Subject', 'My Least Favorite Subject'],
                '口语': ['Self Introduction', 'My Hobby', 'My Family', 'My Friend', 'My School', 'My Dream', 'My Favorite Food', 'My Favorite Sport', 'My Favorite Book', 'My Favorite Movie', 'My Trip', 'My Summer Vacation', 'My Winter Vacation', 'My Spring Vacation', 'My Fall Vacation', 'My Hometown', 'My Future Plan', 'My Study Method', 'My Favorite Subject', 'My Least Favorite Subject']
            'chinese': {
                '写作': ['我的一天', '我的爱好', '我的家庭', '我的朋友', '我的学校', '我的梦想', '我喜欢的食物', '我喜欢的运动', '我喜欢的书', '我喜欢的电影', '我的旅行', '我的暑假', '我的寒假', '我的春假', '我的秋假', '我的故乡', '我的未来计划', '我的学习方法', '我擅长的科目', '我不擅长的科目'],
                '口语': ['自我介绍', '我的爱好', '我的家庭', '我的朋友', '我的学校', '我的梦想', '我喜欢的食物', '我喜欢的运动', '我喜欢的书', '我喜欢的电影', '我的旅行', '我的暑假', '我的寒假', '我的春假', '我的秋假', '我的故乡', '我的未来计划', '我的学习方法', '我擅长的科目', '我不擅长的科目']
            }
        # 增强的问题库
        self.question_libraries = {
            'japanese': {
                '听力': ['会話の内容は何ですか？', '話している人は誰ですか？', '話している場所はどこですか？', '話している時間はいつですか？', '話している理由は何ですか？', '会話の結果は何ですか？', '会話の中で言及された事柄はどれですか？', '会話の中で最も重要な情報は何ですか？', '会話のトピックは何ですか？', '会話の流れはどのようなものですか？']
            },
            'english': {
                '听力': ['What is the content of the conversation?', 'Who are the speakers?', 'Where are they speaking?', 'When are they speaking?', 'Why are they speaking?', 'What is the result of the conversation?', 'Which of the following is mentioned in the conversation?', 'What is the most important information in the conversation?', 'What is the topic of the conversation?', 'What is the flow of the conversation?']
            },
            'chinese': {
                '阅读': ['这篇文章的主旨是什么？', '文中「{word}」的意思是什么？', '从这篇文章中可以推断出什么？', '作者的观点是什么？', '这篇文章的结论是什么？', '这篇文章的结构是什么？', '文中「{sentence}」的意思是什么？', '这篇文章的背景是什么？', '这篇文章的目的是什么？', '这篇文章的目标读者是谁？'],
            }
        }

        """生成单个题目"""
        # 生成唯一ID
        unique_id = f"simple_{int(time.time() * 1000)}_{random.randint(1, 1000)}"
        # 随机选择题目类型
        if not question_type:
            question_type = random.choice(self.supported_question_types)

        # 生成题目内容
        if language in self.question_templates and category in self.question_templates[language]:
            # 生成所有可能需要的变量
            variables = {
                'word': self._generate_random_word(language, category, difficulty),
                'paragraph': self._generate_random_paragraph(language, category, difficulty),
                'topic': self._generate_random_topic(language, category, difficulty),
                'question': self._generate_random_question(language, category, difficulty),
                'part': self._generate_random_part(language, category, difficulty),
                'target_lang': self._generate_random_target_lang(language, category, difficulty),
                'duration': self._generate_random_duration(language, category, difficulty),
                'phrase': self._generate_random_word(language, category, difficulty),
                'situation': f"{category}场景{difficulty}",
                'experience': f"{category}经历{difficulty}",
                'chart': f"图表{difficulty}",
            }

        else:
            content = f"{language} {category} {question_type} 题目示例 (难度{difficulty})"

        # 生成选项
        options = self._generate_options(question_type)

        # 生成正确答案
            correct_answers = [random.choice(options)]
            required_answers = 1
        elif question_type == 'multiple':
            # 多选题生成2-3个正确答案
            num_correct = random.randint(2, 3)
            correct_answers = random.sample(options, num_correct)
            required_answers = num_correct
        else:
            correct_answers = []
            required_answers = 1

        # 生成解析
        explanation = f"这是一道{language}的{category}类{question_type}，难度为{difficulty}级。"

        # 生成知识点
        knowledge_points = self._generate_knowledge_points(category, difficulty)

        return {
            'id': unique_id,
            'language': language,
            'category': category,
            'difficulty': difficulty,
            'content': content,
            'options': options,
            'question_type': question_type,
            'required_answers': required_answers,
            'correct_answers': correct_answers,
            'explanation': explanation,
            'knowledge_points': knowledge_points,
            'used_count': 0,
            'created_at': time.time(),
            'freshness_score': random.uniform(0.8, 1.0),
            'generated_by_ai': False
        }

    def _generate_random_word(self, language: str, category: str, difficulty: int) -> str:
        """生成随机单词"""
        return random.choice(self.word_libraries.get(language, {}).get(category, ['示例单词']))

    def _generate_random_sentence(self, language: str, category: str, difficulty: int) -> str:
        """生成随机句子"""
        return random.choice(self.sentence_libraries.get(language, {}).get(category, ['示例句子']))

    def _generate_random_paragraph(self, language: str, category: str, difficulty: int) -> str:
        """生成随机段落"""
        return random.choice(self.paragraph_libraries.get(language, {}).get(category, ['示例段落']))

    def _generate_random_topic(self, language: str, category: str, difficulty: int) -> str:
        """生成随机话题"""
        return random.choice(self.topic_libraries.get(language, {}).get(category, ['示例话题']))

    def _generate_random_question(self, language: str, category: str, difficulty: int) -> str:
        """生成随机问题"""
        return random.choice(self.question_libraries.get(language, {}).get(category, ['示例问题']))

    def _generate_random_part(self, language: str, category: str, difficulty: int) -> str:
        """生成随机语法部分"""
        parts = {
            'japanese': {
            },
            'english': {
                '语法': ['preposition', 'verb', 'noun', 'adjective', 'adverb', 'conjunction', 'interjection', 'auxiliary verb', 'prefix', 'suffix']
            },
            'chinese': {
                '语法': ['助词', '动词', '名词', '形容词', '副词', '连词', '感叹词', '介词', '前缀', '后缀']
            }
        }

    def _generate_random_target_lang(self, language: str, category: str, difficulty: int) -> str:
        """生成随机目标语言"""
        return random.choice(available_langs) if available_langs else 'english'

    def _generate_random_word_count(self, language: str, category: str, difficulty: int) -> str:
        """生成随机字数要求"""
        word_counts = {
            1: ['50', '100'],
            2: ['100', '150'],
            3: ['150', '200'],
            4: ['200', '300'],
            5: ['300', '500']
        }
        return random.choice(word_counts.get(difficulty, ['100']))

    def _generate_random_duration(self, language: str, category: str, difficulty: int) -> str:
        """生成随机时长要求"""
        durations = {
            1: ['30秒', '1分'],
            2: ['1分', '1分30秒'],
            3: ['1分30秒', '2分'],
            4: ['2分', '3分'],
            5: ['3分', '5分']
        }
        return random.choice(durations.get(difficulty, ['1分']))

    def _generate_options(self, question_type: str) -> List[str]:
        """生成选项"""
        if question_type in ['single', 'multiple']:
            options = []
            for i, letter in enumerate(self.option_templates[question_type]):
            return options
        else:
            # 其他题型不需要选项
            return []

    def _generate_knowledge_points(self, category: str, difficulty: int) -> List[str]:
        """生成知识点"""
        return [f"{category}知识点{difficulty}", f"{category}难度{difficulty}"]

def get_existing_question_contents() -> Set[str]:
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT content FROM question_bank")
        contents = cursor.fetchall()
        return {content[0] for content in contents}
    except Exception as e:
        return set()
    finally:
        conn.close()

def get_all_categories() -> List[str]:
    获取所有可用的题目类别
    # 智能题目生成器支持的类别
    supported_categories = ['词汇', '语法', '阅读', '听力', '写作', '口语', '翻译']
    return supported_categories

def expand_question_bank_large():
    自动拓展题库，生成10000道不重复且包含所有题型的题目
    print("开始自动拓展题库，目标10000道题目...")

    # 创建简化的题目生成器实例，避免依赖复杂的Flask应用
    generator = SimpleQuestionGenerator()

    # 连接到数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 获取现有题目内容，用于去重
    existing_contents = get_existing_question_contents()
    print(f"现有题目数量: {len(existing_contents)}")

    # 定义要生成的题目数量
    target_question_count = 10000
    generated_count = 0

    # 定义要生成的语言、类别和难度
    languages = generator.supported_languages
    difficulties = generator.supported_difficulties
    all_categories = generator.supported_categories

    # 支持的题目类型
    question_types = generator.supported_question_types

    # 已生成的题目类型集合，用于确保覆盖所有题型
    generated_types = set()

    print(f"可用语言: {languages}")
    print(f"可用难度: {difficulties}")
    print(f"支持的题目类型: {question_types}")
    # 生成新题目
    retry_count = 0
    max_retries = 10000  # 最大重试次数，避免无限循环
    while generated_count < target_question_count and retry_count < max_retries:
        # 随机选择语言、类别、难度和题目类型
        language = random.choice(languages)
        category = random.choice(all_categories)
        difficulty = random.choice(difficulties)
        question_type = random.choice(question_types)

        # 确保覆盖所有题型
        if len(generated_types) < len(question_types):
            # 还有题型没生成，优先生成未生成的题型
            remaining_types = [qt for qt in question_types if qt not in generated_types]
            question_type = random.choice(remaining_types)

        try:
            # 生成题目
            question = generator.generate_question(
                language=language,
                category=category,
                difficulty=difficulty,
                question_type=question_type
            )

            # 检查题目是否生成成功
            if question and 'content' in question and 'correct_answers' in question:
                # 检查题目内容是否重复
                if question['content'] in existing_contents:
                    # 题目重复，跳过，重新生成
                    retry_count += 1
                    if retry_count % 100 == 0:
                        print(f"✗ 已重试 {retry_count} 次，当前成功率: {generated_count/(retry_count+generated_count)*100:.1f}%")
                    continue

                # 确保选项字段存在（对于需要选项的题目类型）
                if question_type in ['single', 'multiple']:
                    if 'options' not in question or len(question['options']) < 2:
                        retry_count += 1
                        continue

                # 将选项转换为JSON字符串
                options_json = str(question.get('options', []))

                # 将正确答案转换为JSON字符串
                correct_answer_json = str(question['correct_answers'])

                # 插入题目到数据库
                cursor.execute('''
                    INSERT INTO question_bank (
                        language, category, difficulty, content,
                        options, correct_answer, explanation, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    language, category, difficulty, question['content'],
                    options_json, correct_answer_json, question.get('explanation', ''),
                ))

                # 更新已生成的题目类型集合
                generated_types.add(question_type)

                # 更新现有题目内容集合
                existing_contents.add(question['content'])

                generated_count += 1
                retry_count = 0  # 重置重试计数

                # 显示生成成功信息
                if generated_count % 50 == 0:
                    print(f"✓ 生成题目成功 [{generated_count}/{target_question_count}]: {language} - {category} - {question_type} - 难度{difficulty} - {question['content'][:30]}...")

                # 每生成50道题目提交一次事务，提高效率
                if generated_count % 50 == 0:
                    conn.commit()
                    print(f"\n已生成 {generated_count} 道题目，休息2秒...")
                    time.sleep(2)

                # 每生成200道题目显示一次进度，减少输出
                if generated_count % 200 == 0:
                    print(f"\n=== 进度报告 ===")
                    print(f"已生成: {generated_count} 道题目")
                    print(f"剩余: {target_question_count - generated_count} 道题目")
                    print(f"已覆盖题型: {', '.join(generated_types)}")
                    print(f"=== 进度报告结束 ===\n")
            else:
                retry_count += 1
                if retry_count % 100 == 0:
                    print(f"✗ 生成题目失败，已重试 {retry_count} 次")
        except Exception as e:
            retry_count += 1
            if retry_count % 100 == 0:
                print(f"✗ 生成题目出错: {str(e)}，已重试 {retry_count} 次")
            # 出错后休息1秒，避免连续出错

    if retry_count >= max_retries:
        print(f"\n⚠️  已达到最大重试次数 {max_retries}，生成题目数量: {generated_count}")

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

    print(f"\n题库拓展完成！共生成 {generated_count} 道题目。")
    print(f"已覆盖题型: {', '.join(generated_types)}")

def analyze_question_bank():
    分析现有题库
    print("开始分析现有题库...")

    # 连接到数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM question_bank")
    total_count = cursor.fetchone()[0]
    print(f"总题目数量: {total_count}")

    cursor.execute("SELECT language, COUNT(*) FROM question_bank GROUP BY language")
    language_stats = cursor.fetchall()
    print("\n按语言分布:")
    for language, count in language_stats:
        print(f"  {language}: {count} 道 ({count/total_count*100:.1f}%)")

    # 按类别统计
    cursor.execute("SELECT category, COUNT(*) FROM question_bank GROUP BY category")
    category_stats = cursor.fetchall()
    print("\n按类别分布:")
    for category, count in category_stats:
        print(f"  {category}: {count} 道 ({count/total_count*100:.1f}%)")

    # 按难度统计
    cursor.execute("SELECT difficulty, COUNT(*) FROM question_bank GROUP BY difficulty")
    difficulty_stats = cursor.fetchall()
    print("\n按难度分布:")
    for difficulty, count in difficulty_stats:
        print(f"  难度{difficulty}: {count} 道 ({count/total_count*100:.1f}%)")

    # 关闭连接
    conn.close()

    return {
        'total_count': total_count,
        'language_stats': language_stats,
        'category_stats': category_stats,
        'difficulty_stats': difficulty_stats
    }

def main():
    主函数
    print("=== 利用AI和Python技术自动完善并拓展题库 ===")
    print("策略：题目重复则跳过，重新生成")

    # 分析现有题库
    analyze_question_bank()
    # 自动拓展题库
    expand_question_bank_large()

    # 再次分析题库，查看拓展效果
    print("\n=== 拓展后的题库分析 ===")
    analyze_question_bank()

    print("\n=== 题库自动完善和拓展完成！===")

if __name__ == "__main__":
