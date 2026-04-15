#!/usr/bin/env python3
"""
自动扩充题库脚本
用于根据不同的语言、等级、章节、难度和素材来源生成新题目
"""

import sqlite3
import json
import time
import uuid
import random
from datetime import datetime

class QuestionGenerator:
    """题目生成器"""
    
    def __init__(self):
        self.db_path = 'app.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        self.conn.close()
    
    def get_all_languages(self):
        """获取所有语言"""
        self.cursor.execute("SELECT id, language_code, language_name FROM question_languages")
        return self.cursor.fetchall()
    
    def get_all_levels(self, language_id):
        """获取指定语言的所有等级"""
        self.cursor.execute("SELECT id, level_code, level_name FROM question_levels WHERE language_id = ?", (language_id,))
        return self.cursor.fetchall()
    
    def get_all_sections(self):
        """获取所有章节"""
        self.cursor.execute("SELECT id, section_name FROM question_sections")
        return self.cursor.fetchall()
    
    def get_all_difficulties(self):
        """获取所有难度"""
        self.cursor.execute("SELECT id, difficulty_level FROM question_difficulties")
        return self.cursor.fetchall()
    
    def get_all_sources(self):
        """获取所有素材来源"""
        self.cursor.execute("SELECT id, source_type FROM question_sources")
        return self.cursor.fetchall()
    
    def get_question_bank(self, language_id):
        """获取指定语言的题库"""
        self.cursor.execute("SELECT id FROM question_banks WHERE language_id = ?", (language_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def generate_japanese_question(self, level, section, difficulty, source_type):
        """生成日语题目"""
        # 基于等级、章节、难度和素材来源生成不同的题目
        question_templates = {
            'standard': {
                'vocabulary': {
                    'easy': [
                        ("この単語の正しい意味は何ですか？「{word}」", "{options}", "{answer}", "{explanation}"),
                        ("「{word1}」の反対語は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("「{word}」の正しい読み方は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("「{word}」の類義語はどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("次の単語の中で、正しく書かれたものはどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("「{phrase}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("「{idiom}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("「{kanji}」の正しい読み方と意味を選んでください。", "{options}", "{answer}", "{explanation}"),
                        ("次の外来語の正しい意味は何ですか？「{word}」", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("「{verb}」のて形は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("次の文で正しい助詞を選んでください。「私は昨日＿＿映画を見ました。」", "{options}", "{answer}", "{explanation}"),
                        ("「{adjective}」の否定形は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("次の文の正しい形を選んでください。「彼は毎日英語を＿＿。」", "{options}", "{answer}", "{explanation}"),
                        ("「～てください」の正しい使い方はどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("「{verb}」の受身形は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("次の文の正しい形を選んでください。「もし雨が降ったら、ピクニックは＿＿。」", "{options}", "{answer}", "{explanation}"),
                        ("「～によって」と「～に応じて」の違いは何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("「{complex_sentence}」の文法構造を説明してください。", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'reading': {
                    'easy': [
                        ("以下の文章を読んで、質問に答えてください。「私は毎朝7時に起きて、朝ご飯を食べます。それから、学校に行きます。」質問：私は毎朝何時に起きますか？", "{options}", "{answer}", "{explanation}"),
                        ("次の文章の意味は何ですか？「今日は天気が良いです。公園に行きましょう。」", "{options}", "{answer}", "{explanation}"),
                        ("この文章の主語は何ですか？「犬は公園で走っています。」", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("以下のメールを読んで、正しい答えを選んでください。\n\n件名：約束の件\n\nこんにちは、\n来週の水曜日の会議は14時からに変更になりました。\nお手数ですが、スケジュールを調整してください。\nよろしくお願いします。\n\n質問：会議は何時からですか？", "{options}", "{answer}", "{explanation}"),
                        ("次の文章の中で、誤っている部分はどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("この文章の要約はどれですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("以下の新聞記事を読んで、質問に答えてください。\n\n「最近、電子書籍の普及率が急速に上昇しています。特に若者の間では、紙の本よりも電子書籍を好む人が増えています。しかし、電子書籍の普及に伴って、本屋の経営が困難になっているケースも多く見られます。」\n\n質問：この記事の主な内容は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("この文章の筆者の意見はどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("次の文章の中で、筆者が最も強調している点はどれですか？", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'past_exam': {
                'vocabulary': {
                    'easy': [
                        ("JLPT N5過去問：「{word}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N5過去問：「{word}」の正しい読み方は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("JLPT N3過去問：「{word}」の類義語はどれですか？", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N3過去問：「{phrase}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("JLPT N1過去問：「{idiom}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N1過去問：「{kanji}」の正しい読み方は何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("JLPT N5過去問：「{verb}」のて形は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N5過去問：次の文で正しい助詞を選んでください。「私は昨日＿＿映画を見ました。」", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("JLPT N3過去問：次の文の正しい形を選んでください。「彼は毎日英語を＿＿。」", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N3過去問：「{verb}」の受身形は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("JLPT N1過去問：次の文の正しい形を選んでください。「もし雨が降ったら、ピクニックは＿＿。」", "{options}", "{answer}", "{explanation}"),
                        ("JLPT N1過去問：「～によって」と「～に応じて」の違いは何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'anime_movie': {
                'vocabulary': {
                    'easy': [
                        ("アニメ「ドラえもん」から：「どらえもん」の道具の一つ「ひみつ道具」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("映画「君の名は。」から：「{word}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("アニメ「進撃の巨人」から：「立体機動装置」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("アニメ「鬼滅の刃」から：「水の呼吸」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("アニメ「攻殻機動隊」から：「サイバネティックス」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("映画「千と千尋の神隠し」から：「神隠し」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("アニメ台詞：「私は{verb}」の正しい形は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("映画台詞：「{phrase}」の文法構造は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("アニメ台詞：「もし{condition}なら、{result}」の正しい形は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("映画台詞：「{phrase}」の使い方は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("アニメ台詞：「{complex_sentence}」の文法解釈は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("映画台詞：「{phrase}」の微妙なニュアンスは何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'news': {
                'vocabulary': {
                    'easy': [
                        ("ニュース用語：「{word}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("経済ニュース：「{word}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("国際ニュース：「{phrase}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("科学ニュース：「{term}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("政治ニュース：「{idiom}」の意味は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("社会ニュース：「{complex_phrase}」の意味は何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'reading': {
                    'easy': [
                        ("以下のニュース見出しの意味は何ですか？「{headline}」", "{options}", "{answer}", "{explanation}"),
                        ("短いニュース記事から：「{fact}」は何ですか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("ニュース記事から：「{event}」の原因は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("ニュース記事から：「{person}」は何をしましたか？", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("長いニュース記事から：「{topic}」についての筆者の意見は何ですか？", "{options}", "{answer}", "{explanation}"),
                        ("ニュース分析記事から：「{trend}」の影響は何ですか？", "{options}", "{answer}", "{explanation}")
                    ]
                }
            }
        }
        
        # 基于等级、章节、难度和素材来源选择合适的模板
        # 这里简化处理，实际项目中可以根据需要扩展
        templates = question_templates.get(source_type, question_templates['standard'])
        section_templates = templates.get(section.lower(), templates['vocabulary'])
        difficulty_templates = section_templates.get(difficulty.lower(), section_templates['easy'])
        
        # 随机选择一个模板
        import random
        template = random.choice(difficulty_templates)
        
        # 生成具体的题目内容
        # 这里简化处理，实际项目中可以根据需要生成更真实的题目
        content = template[0].format(
            word="日本", 
            word1="大きい", 
            word2="小さい", 
            phrase="おはようございます", 
            idiom="青二才", 
            kanji="漢", 
            verb="食べる", 
            adjective="美しい", 
            phrase2="明日は雨が降るかもしれません",
            complex_phrase="複雑なフレーズ",
            complex_sentence="私は昨日友達と映画を見て、晩御飯を食べました",
            headline="東京で桜が満開に",
            fact="今日の気温は20度です",
            event="地震",
            person="首相",
            topic="環境問題",
            trend="人口減少",
            term="科学用語",
            condition="明日雨が降ったら",
            result="ピクニックを中止します"
        )
        
        # 生成选项
        options = ["A. 選択肢1", "B. 選択肢2", "C. 選択肢3", "D. 選択肢4"]
        
        # 随机选择一个正确答案
        correct_answer = random.choice(["A", "B", "C", "D"])
        
        # 生成解释
        explanation = f"この問題の正しい答えは{correct_answer}です。"
        
        return content, options, correct_answer, explanation
    
    def generate_question(self, language_code, level, section, difficulty, source_type, question_type=None):
        """生成题目"""
        import random
        
        # 如果没有指定题型，随机选择题目类型
        if not question_type:
            question_types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer']
            question_type = random.choice(question_types)
        
        if language_code == "japanese":
            return self.generate_japanese_question(level, section, difficulty, source_type) + (question_type,)
        elif language_code == "english":
            return self.generate_english_question(level, section, difficulty, source_type) + (question_type,)
        else:
            # 默认生成简单题目
            content = f"{language_code} question: What is the meaning of '{language_code}'?"
            options = ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"]
            correct_answer = "A"
            explanation = "This is a default explanation."
            return content, options, correct_answer, explanation, question_type
    
    def generate_english_question(self, level, section, difficulty, source_type):
        """生成英语题目"""
        # 基于等级、章节、难度和素材来源生成不同的题目
        question_templates = {
            'standard': {
                'vocabulary': {
                    'easy': [
                        ("What is the meaning of '{word}'?", "{options}", "{answer}", "{explanation}"),
                        ("What is the antonym of '{word}'?", "{options}", "{answer}", "{explanation}"),
                        ("What is the synonym of '{word}'?", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("Choose the correct spelling of '{word}'", "{options}", "{answer}", "{explanation}"),
                        ("Which word has the same meaning as '{phrase}'", "{options}", "{answer}", "{explanation}"),
                        ("What is the correct form of '{verb}' in past tense?", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("What is the idiom that means '{meaning}'", "{options}", "{answer}", "{explanation}"),
                        ("Choose the correct preposition: '{sentence}'", "{options}", "{answer}", "{explanation}"),
                        ("What does '{slang}' mean in informal English?", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("Choose the correct verb form: She {verb} to school every day", "{options}", "{answer}", "{explanation}"),
                        ("Choose the correct article: I have {article} cat", "{options}", "{answer}", "{explanation}"),
                        ("What is the plural form of '{noun}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("Choose the correct tense: They {verb} in Paris since 2010", "{options}", "{answer}", "{explanation}"),
                        ("Choose the correct pronoun: {noun} is my best friend", "{options}", "{answer}", "{explanation}"),
                        ("What is the correct passive form of '{sentence}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("Choose the correct conditional: If I {verb}, I would {result}", "{options}", "{answer}", "{explanation}"),
                        ("What is the correct reported speech for: '{direct_speech}'", "{options}", "{answer}", "{explanation}"),
                        ("Choose the correct inversion: Never {verb} that", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'reading': {
                    'easy': [
                        ("Read the text and answer: What is the main topic?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("What is the meaning of '{word}' in the context?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("Choose the correct answer: How many {noun} are there?\n\n{text}", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("What is the author's attitude towards {topic}?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("Which statement is true according to the text?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("What is the main idea of paragraph {number}?\n\n{text}", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("What can be inferred from the text?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("What is the purpose of the text?\n\n{text}", "{options}", "{answer}", "{explanation}"),
                        ("Choose the best title for the text\n\n{text}", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'listening': {
                    'easy': [
                        ("Listen to the audio and answer: What is {noun}?", "{options}", "{answer}", "{explanation}"),
                        ("What time does {event} start?", "{options}", "{answer}", "{explanation}"),
                        ("Where is {place}?", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("What is the main purpose of the call?", "{options}", "{answer}", "{explanation}"),
                        ("What does the speaker suggest?", "{options}", "{answer}", "{explanation}"),
                        ("What information does the speaker provide?", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("What is the speaker's opinion about {topic}?", "{options}", "{answer}", "{explanation}"),
                        ("What can be concluded from the conversation?", "{options}", "{answer}", "{explanation}"),
                        ("What details are mentioned about {item}?", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'past_exam': {
                'vocabulary': {
                    'easy': [
                        ("TOEFL practice: What is the meaning of '{word}'?", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct synonym for '{word}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("TOEFL practice: What is the antonym of '{word}'?", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct form of '{word}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("TOEFL practice: What does '{idiom}' mean in this context?", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct collocation for '{word}'", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("TOEFL practice: Choose the correct verb form", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct article", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("TOEFL practice: Choose the correct tense", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct pronoun", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("TOEFL practice: Choose the correct conditional", "{options}", "{answer}", "{explanation}"),
                        ("IELTS practice: Choose the correct inversion", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'anime_movie': {
                'vocabulary': {
                    'easy': [
                        ("From 'Harry Potter': What does '{word}' mean?", "{options}", "{answer}", "{explanation}"),
                        ("From 'Frozen': What is the meaning of '{phrase}'?", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("From 'The Lion King': What does '{phrase}' mean in this context?", "{options}", "{answer}", "{explanation}"),
                        ("From 'Toy Story': Choose the correct meaning of '{word}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("From 'Inception': What is the meaning of '{complex_phrase}'?", "{options}", "{answer}", "{explanation}"),
                        ("From 'The Matrix': Choose the correct interpretation of '{phrase}'", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'grammar': {
                    'easy': [
                        ("Movie quote: Choose the correct verb form", "{options}", "{answer}", "{explanation}"),
                        ("Anime quote: Choose the correct preposition", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("Movie quote: Choose the correct tense", "{options}", "{answer}", "{explanation}"),
                        ("Anime quote: Choose the correct conditional", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("Movie quote: What is the grammatical structure?", "{options}", "{answer}", "{explanation}"),
                        ("Anime quote: Choose the correct inversion", "{options}", "{answer}", "{explanation}")
                    ]
                }
            },
            'news': {
                'vocabulary': {
                    'easy': [
                        ("News term: What does '{word}' mean?", "{options}", "{answer}", "{explanation}"),
                        ("Economic news: Choose the correct meaning of '{word}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("International news: What is the meaning of '{phrase}'", "{options}", "{answer}", "{explanation}"),
                        ("Science news: Choose the correct term for '{definition}'", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("Political news: What does '{idiom}' mean in this context?", "{options}", "{answer}", "{explanation}"),
                        ("Social news: Choose the correct interpretation of '{complex_phrase}'", "{options}", "{answer}", "{explanation}")
                    ]
                },
                'reading': {
                    'easy': [
                        ("News headline: What is the main topic?\n\n{headline}", "{options}", "{answer}", "{explanation}"),
                        ("Short news: What happened?\n\n{news}", "{options}", "{answer}", "{explanation}")
                    ],
                    'medium': [
                        ("News article: What is the cause of {event}?\n\n{news}", "{options}", "{answer}", "{explanation}"),
                        ("News analysis: What is the impact of {policy}?\n\n{analysis}", "{options}", "{answer}", "{explanation}")
                    ],
                    'hard': [
                        ("Editorial: What is the author's opinion?\n\n{editorial}", "{options}", "{answer}", "{explanation}"),
                        ("Investigative report: What can be concluded?\n\n{report}", "{options}", "{answer}", "{explanation}")
                    ]
                }
            }
        }
        
        # 基于等级、章节、难度和素材来源选择合适的模板
        templates = question_templates.get(source_type, question_templates['standard'])
        section_templates = templates.get(section.lower(), templates['vocabulary'])
        difficulty_templates = section_templates.get(difficulty.lower(), section_templates['easy'])
        
        # 随机选择一个模板
        template = random.choice(difficulty_templates)
        
        # 生成具体的题目内容
        content = template[0].format(
            word="apple", 
            word1="big", 
            word2="small", 
            phrase="good morning", 
            idiom="break a leg", 
            noun="cat", 
            verb="go", 
            article="a", 
            meaning="definition", 
            complex_phrase="in the long run",
            complex_sentence="I went to the store and bought some milk, then I came home and made dinner",
            headline="New Study Shows Benefits of Exercise",
            fact="Today's temperature is 20 degrees",
            event="earthquake",
            person="president",
            topic="climate change",
            trend="population growth",
            term="photosynthesis",
            condition="it rains tomorrow",
            result="we'll stay home",
            direct_speech="I'm going to the park",
            text="This is a simple text about the importance of learning English. English is the most widely spoken language in the world, and it's used in business, science, and technology. Learning English can open up many opportunities for you.",
            number="2",
            slang="cool",
            sentence="I'm going to the store",
            place="school",
            audio="[Audio: People talking about their plans for the weekend]",
            definition="the process by which plants make food",
            news="Scientists have discovered a new species of bird in the Amazon rainforest. The bird has bright blue feathers and a unique song. This discovery could help us understand more about biodiversity in the region.",
            analysis="The new policy is expected to have a positive impact on the economy, but some experts are concerned about its long-term effects.",
            editorial="We need to take action to address climate change before it's too late. The science is clear: we're running out of time.",
            report="An investigative report has revealed that many companies are not following safety regulations, putting workers at risk. This is a serious issue that needs to be addressed immediately."
        )
        
        # 生成选项
        options = ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"]
        
        # 随机选择一个正确答案
        correct_answer = random.choice(["A", "B", "C", "D"])
        
        # 生成解释
        explanation = f"This is an explanation for the {difficulty} level {section} question about {source_type}"
        
        return content, options, correct_answer, explanation
    
    def add_question(self, question_bank_id, level_id, section_id, difficulty_id, source_id, question_content, correct_answer, explanation, options, question_type='single_choice'):
        """添加题目到数据库"""
        try:
            # 开始事务
            self.conn.execute('BEGIN TRANSACTION;')
            
            # 生成主题标签
            import random
            topic_tags_list = []
            
            # 根据章节生成相关标签
            if section_id == 1:  # 词汇
                topic_tags_list.append("vocabulary")
            elif section_id == 2:  # 语法
                topic_tags_list.append("grammar")
            elif section_id == 3:  # 阅读
                topic_tags_list.append("reading")
            elif section_id == 4:  # 听力
                topic_tags_list.append("listening")
            
            # 根据难度生成相关标签
            if difficulty_id == 1:  # easy
                topic_tags_list.append("beginner")
            elif difficulty_id == 2:  # medium
                topic_tags_list.append("intermediate")
            elif difficulty_id == 3:  # hard
                topic_tags_list.append("advanced")
            
            # 添加一些通用标签
            general_tags = ["exam_prep", "practice", "learning"]
            topic_tags_list.extend(random.sample(general_tags, 2))
            
            # 转换为逗号分隔的字符串
            topic_tags = ",".join(topic_tags_list)
            
            # 生成题目解析文本
            analysis_text = f"本题为{question_type}类型，考察了{section_id}相关知识，难度为{difficulty_id}级别。" if explanation else ""
            
            # 生成作者信息
            author = f"AI_Generator_{random.randint(1000, 9999)}"
            
            # 插入题目，包含新添加的字段
            self.cursor.execute("""
                INSERT INTO questions (
                    question_bank_id, level_id, section_id, difficulty_id, source_id, 
                    question_content, correct_answer, explanation, is_active, question_type,
                    analysis_text, analysis_video_url, is_duplicate, duplicate_of, 
                    topic_tags, is_targeted, author, source_reference
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, 0, NULL, ?, 0, ?, NULL)
            """, (
                question_bank_id, level_id, section_id, difficulty_id, source_id, 
                question_content, correct_answer, explanation, question_type,
                analysis_text, topic_tags, author
            ))
            
            question_id = self.cursor.lastrowid
            
            # 只有选择题（单选、多选）才需要插入选项
            if question_type in ['single_choice', 'multiple_choice'] and options:
                # 插入选项
                for i, option in enumerate(options):
                    option_label = chr(65 + i)  # A, B, C, D
                    self.cursor.execute("""
                        INSERT INTO question_options (question_id, option_label, option_content, option_order)
                        VALUES (?, ?, ?, ?)
                    """, (question_id, option_label, option, i+1))
            
            # 提交事务
            self.conn.commit()
            
            return True, question_id
        except Exception as e:
            # 回滚事务
            self.conn.rollback()
            print(f"添加题目失败: {e}")
            return False, None
    
    def expand_question_bank(self, target_count=1000, min_per_type=100):
        """扩充题库"""
        print(f"开始扩充题库，目标总题数：{target_count}，每种题型至少：{min_per_type}")
        
        # 获取当前题目数量
        self.cursor.execute("SELECT COUNT(*) FROM questions")
        current_count = self.cursor.fetchone()[0]
        print(f"当前题库题数：{current_count}")
        
        # 获取当前题型分布
        self.cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
        current_type_dist = dict(self.cursor.fetchall())
        print(f"当前题型分布：{current_type_dist}")
        
        # 获取所有必要的信息
        languages = self.get_all_languages()
        all_sections = self.get_all_sections()
        all_difficulties = self.get_all_difficulties()
        all_sources = self.get_all_sources()
        
        # 定义所有题型
        all_question_types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer']
        
        generated_count = 0
        
        # 循环生成题目，直到达到目标数量和每种题型的最小数量
        while True:
            # 检查是否达到目标
            if current_count + generated_count >= target_count:
                # 检查每种题型是否达到最小数量
                self.cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
                type_dist = dict(self.cursor.fetchall())
                if all(type_dist.get(qt, 0) >= min_per_type for qt in all_question_types):
                    break
            
            # 随机选择语言、等级、章节、难度和素材来源
            import random
            
            # 随机选择语言
            language_id, language_code, language_name = random.choice(languages)
            
            # 获取该语言的所有等级
            levels = self.get_all_levels(language_id)
            if not levels:
                continue
            
            # 随机选择等级
            level_id, level_code, level_name = random.choice(levels)
            
            # 随机选择章节
            section_id, section_name = random.choice(all_sections)
            
            # 随机选择难度
            difficulty_id, difficulty_level = random.choice(all_difficulties)
            
            # 随机选择素材来源
            source_id, source_type = random.choice(all_sources)
            
            # 获取题库ID
            question_bank_id = self.get_question_bank(language_id)
            if not question_bank_id:
                continue
            
            # 检查当前题型分布，优先生成数量较少的题型
            self.cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
            type_dist = dict(self.cursor.fetchall())
            
            # 找出数量最少的题型
            min_type = min(all_question_types, key=lambda x: type_dist.get(x, 0))
            
            # 生成题目，指定题型为数量最少的题型
            question_content, options, correct_answer, explanation, question_type = self.generate_question(
                language_code, level_code, section_name, difficulty_level, source_type, min_type
            )
            
            # 根据题目类型调整选项和答案
            if question_type == 'true_false':
                # 判断题只有两个选项
                options = ['A. True', 'B. False']
                correct_answer = random.choice(['A', 'B'])
                explanation = f"这是一道判断题。正确答案是：{correct_answer}。" if language_code == "japanese" else f"This is a true/false question. The correct answer is: {correct_answer}."
            elif question_type == 'fill_blank':
                # 填空题不需要选项
                options = []
                # 根据语言和主题生成更贴合的填空题答案
                if language_code == "japanese":
                    fill_answers = {
                        "词汇": ["日本", "東京", "桜", "寿司", "言葉", "文化", "歴史", "地理"],
                        "语法": ["て", "た", "を", "に", "は", "が", "で", "と"],
                        "阅读": ["文章", "段落", "主旨", "細部", "推論", "語彙", "文法", "構造"],
                        "听力": ["会話", "講義", "ニュース", "天気予報", "案内", "インタビュー", "広告", "アナウンス"]
                    }
                    topic_answers = fill_answers.get(section_name, fill_answers["词汇"])
                    correct_answer = random.choice(topic_answers)
                    explanation = f"これは穴埋め問題です。正しい答えは：'{correct_answer}'です。"
                else:
                    fill_answers = {
                        "vocabulary": ["apple", "banana", "cat", "dog", "house", "school", "teacher", "student"],
                        "grammar": ["is", "are", "was", "were", "have", "has", "had", "will"],
                        "reading": ["text", "paragraph", "main idea", "detail", "inference", "vocabulary", "grammar", "structure"],
                        "listening": ["conversation", "lecture", "news", "weather", "directions", "interview", "advertisement", "announcement"]
                    }
                    topic_answers = fill_answers.get(section_name.lower(), fill_answers["vocabulary"])
                    correct_answer = random.choice(topic_answers)
                    explanation = f"This is a fill-in-the-blank question. The correct answer is: '{correct_answer}'."
            elif question_type == 'short_answer':
                # 简答题不需要选项
                options = []
                # 根据语言和主题生成更贴合的简答题答案
                if language_code == "japanese":
                    short_answers = {
                        "词汇": ["日本語の単語は漢字、ひらがな、カタカナで構成されています。", "敬語は日本語の重要な特徴です。", "類義語は意味が似ている単語です。"],
                        "语法": ["動詞の活用形は目的語の関係によって変わります。", "助詞は文の構造を示す重要な要素です。", "日本語の文は主語が省略されることが多いです。"],
                        "阅读": ["文章の主旨を理解するには、最初と最後の段落が重要です。", "細部問題には文章の特定の部分を参照する必要があります。", "推論問題には文章の情報から論理的に導き出す必要があります。"],
                        "听力": ["会話のテーマを把握するには、最初の数文が重要です。", "時間や場所などの具体的な情報に注意する必要があります。", "発言者の意見や感情を理解するには、トーンやイントネーションに注意する必要があります。"]
                    }
                    topic_answers = short_answers.get(section_name, short_answers["词汇"])
                    correct_answer = random.choice(topic_answers)
                    explanation = f"これは短答問題です。正しい答えは：{correct_answer}"
                else:
                    short_answers = {
                        "vocabulary": ["English words consist of roots, prefixes, and suffixes.", "Synonyms are words with similar meanings.", "Antonyms are words with opposite meanings."],
                        "grammar": ["Verbs change form according to tense, person, and number.", "Articles are used to indicate definiteness or indefiniteness.", "Prepositions show relationships between words in a sentence."],
                        "reading": ["To understand the main idea, look at the first and last paragraphs.", "For detail questions, refer to specific parts of the text.", "Inference questions require logical deduction from the text."],
                        "listening": ["To grasp the topic, pay attention to the first few sentences.", "Note specific information like time, place, and numbers.", "To understand the speaker's opinion, listen to tone and intonation."]
                    }
                    topic_answers = short_answers.get(section_name.lower(), short_answers["vocabulary"])
                    correct_answer = random.choice(topic_answers)
                    explanation = f"This is a short answer question. The correct answer is: {correct_answer}"
            elif question_type == 'multiple_choice':
                # 多选题可以有多个正确答案
                # 随机选择1-3个正确答案
                num_correct = random.randint(1, 3)
                all_options = ['A', 'B', 'C', 'D']
                correct_answers = random.sample(all_options, num_correct)
                correct_answer = ','.join(correct_answers)
                explanation = f"これは複数回答問題です。正しい答えは：{', '.join(correct_answers)}です。" if language_code == "japanese" else f"This is a multiple choice question. The correct answers are: {', '.join(correct_answers)}."
            
            # 添加题目到数据库
            success, question_id = self.add_question(
                question_bank_id, level_id, section_id, difficulty_id, source_id,
                question_content, correct_answer, explanation, options, question_type
            )
            
            if success:
                generated_count += 1
                print(f"成功生成第{generated_count}道题目（{question_type}）：{question_content[:50]}...")
            
            # 随机延迟，避免生成的题目过于相似
            time.sleep(0.1)
        
        # 验证最终题目数量
        self.cursor.execute("SELECT COUNT(*) FROM questions")
        final_count = self.cursor.fetchone()[0]
        
        # 验证最终题型分布
        self.cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
        final_type_dist = dict(self.cursor.fetchall())
        
        print(f"\n题库扩充完成！")
        print(f"当前题库题数：{final_count}")
        print(f"实际生成的题目数量：{final_count - current_count}")
        print(f"最终题型分布：{final_type_dist}")
        
        return final_count

if __name__ == "__main__":
    # 创建题目生成器
    generator = QuestionGenerator()
    
    # 扩充题库到1500道题目，每种题型至少200道
    final_count = generator.expand_question_bank(target_count=1500, min_per_type=200)
    
    print(f"\n题库扩充完成，最终题数：{final_count}")
