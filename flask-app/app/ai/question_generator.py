#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI出题专家系统 - 根据考试类型和语言生成高质量题目
支持从数据库题库随机出题，确保选项具有混淆性和易错性
"""

import random
import sqlite3
import os
import json

class QuestionGenerator:
    """AI出题专家 - 根据语言和难度生成高质量题目"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        
        self.japanese_vocabulary = {
            '初级': [
                {'word': '猫', 'kana': 'ねこ', 'meaning': '猫', 'confusions': ['犬', '鳥', '魚']},
                {'word': '犬', 'kana': 'いぬ', 'meaning': '狗', 'confusions': ['猫', '馬', '牛']},
                {'word': '本', 'kana': 'ほん', 'meaning': '书', 'confusions': ['雑誌', '新聞', '辞書']},
                {'word': '水', 'kana': 'みず', 'meaning': '水', 'confusions': ['お茶', 'コーヒー', 'ジュース']},
                {'word': '食べる', 'kana': 'たべる', 'meaning': '吃', 'confusions': ['飲む', '話す', '見る']},
                {'word': '行く', 'kana': 'いく', 'meaning': '去', 'confusions': ['来る', '帰る', '出る']},
                {'word': '見る', 'kana': 'みる', 'meaning': '看', 'confusions': ['聞く', '話す', '食べる']},
                {'word': '聞く', 'kana': 'きく', 'meaning': '听', 'confusions': ['見る', '話す', '読む']},
                {'word': '話す', 'kana': 'はなす', 'meaning': '说', 'confusions': ['聞く', '読む', '書く']},
                {'word': '読む', 'kana': 'よむ', 'meaning': '读', 'confusions': ['書く', '話す', '見る']},
            ],
            '中级': [
                {'word': '勉強', 'kana': 'べんきょう', 'meaning': '学习', 'confusions': ['仕事', '働く', '研究']},
                {'word': '研究', 'kana': 'けんきゅう', 'meaning': '研究', 'confusions': ['勉強', '調査', '開発']},
                {'word': '開発', 'kana': 'かいはつ', 'meaning': '开发', 'confusions': ['研究', '設計', '製造']},
                {'word': '設計', 'kana': 'せっけい', 'meaning': '设计', 'confusions': ['開発', '製造', '企画']},
                {'word': '企画', 'kana': 'きかく', 'meaning': '企划', 'confusions': ['設計', '開発', '販売']},
                {'word': '販売', 'kana': 'はんばい', 'meaning': '销售', 'confusions': ['購入', '生産', '輸入']},
                {'word': '生産', 'kana': 'せいさん', 'meaning': '生产', 'confusions': ['製造', '販売', '輸出']},
                {'word': '輸入', 'kana': 'ゆにゅう', 'meaning': '进口', 'confusions': ['輸出', '販売', '購入']},
                {'word': '輸出', 'kana': 'ゆしゅつ', 'meaning': '出口', 'confusions': ['輸入', '生産', '輸入']},
                {'word': '技術', 'kana': 'ぎじゅつ', 'meaning': '技术', 'confusions': ['科学', '知識', '能力']},
            ],
            '高级': [
                {'word': '複雑', 'kana': 'ふくざつ', 'meaning': '复杂', 'confusions': ['単純', '簡単', '困難']},
                {'word': '困難', 'kana': 'こんなん', 'meaning': '困难', 'confusions': ['簡単', '複雑', '容易']},
                {'word': '重要', 'kana': 'じゅうよう', 'meaning': '重要', 'confusions': ['重大', '必要', '必須']},
                {'word': '必須', 'kana': 'ひっす', 'meaning': '必须', 'confusions': ['必要', '重要', '不可欠']},
                {'word': '不可欠', 'kana': 'ふかけつ', 'meaning': '不可或缺', 'confusions': ['必須', '重要', '必要']},
                {'word': '影響', 'kana': 'えいきょう', 'meaning': '影响', 'confusions': ['効果', '作用', '結果']},
                {'word': '効果', 'kana': 'こうか', 'meaning': '效果', 'confusions': ['影響', '結果', '効率']},
                {'word': '効率', 'kana': 'こうりつ', 'meaning': '效率', 'confusions': ['効果', '速度', '質量']},
                {'word': '質量', 'kana': 'しつりょう', 'meaning': '质量', 'confusions': ['品質', '数量', '効率']},
                {'word': '品質', 'kana': 'ひんしつ', 'meaning': '品质', 'confusions': ['質量', '性能', '効果']},
            ]
        }

        self.english_vocabulary = {
            '初级': [
                {'word': 'apple', 'meaning': '苹果', 'confusions': ['orange', 'banana', 'grape']},
                {'word': 'book', 'meaning': '书', 'confusions': ['notebook', 'magazine', 'dictionary']},
                {'word': 'happy', 'meaning': '快乐的', 'confusions': ['sad', 'angry', 'tired']},
                {'word': 'run', 'meaning': '跑', 'confusions': ['walk', 'jump', 'swim']},
                {'word': 'eat', 'meaning': '吃', 'confusions': ['drink', 'sleep', 'read']},
                {'word': 'big', 'meaning': '大的', 'confusions': ['small', 'long', 'short']},
                {'word': 'water', 'meaning': '水', 'confusions': ['juice', 'milk', 'tea']},
                {'word': 'house', 'meaning': '房子', 'confusions': ['apartment', 'building', 'room']},
                {'word': 'friend', 'meaning': '朋友', 'confusions': ['family', 'classmate', 'teacher']},
                {'word': 'school', 'meaning': '学校', 'confusions': ['college', 'university', 'office']},
            ],
            '中级': [
                {'word': 'environment', 'meaning': '环境', 'confusions': ['ecology', 'nature', 'climate']},
                {'word': 'technology', 'meaning': '技术', 'confusions': ['science', 'innovation', 'engineering']},
                {'word': 'education', 'meaning': '教育', 'confusions': ['training', 'learning', 'teaching']},
                {'word': 'communication', 'meaning': '交流', 'confusions': ['conversation', 'interaction', 'dialogue']},
                {'word': 'information', 'meaning': '信息', 'confusions': ['data', 'knowledge', 'intelligence']},
                {'word': 'development', 'meaning': '发展', 'confusions': ['growth', 'progress', 'improvement']},
                {'word': 'opportunity', 'meaning': '机会', 'confusions': ['chance', 'possibility', 'option']},
                {'word': 'challenge', 'meaning': '挑战', 'confusions': ['problem', 'difficulty', 'obstacle']},
                {'word': 'solution', 'meaning': '解决方案', 'confusions': ['answer', 'method', 'approach']},
                {'word': 'experience', 'meaning': '经验', 'confusions': ['knowledge', 'skill', 'practice']},
            ],
            '高级': [
                {'word': 'comprehensive', 'meaning': '全面的', 'confusions': ['comprehensible', 'complete', 'complex']},
                {'word': 'sophisticated', 'meaning': '复杂精密的', 'confusions': ['complicated', 'simple', 'elegant']},
                {'word': 'fundamental', 'meaning': '基本的', 'confusions': ['essential', 'basic', 'primary']},
                {'word': 'significant', 'meaning': '重要的', 'confusions': ['important', 'substantial', 'considerable']},
                {'word': 'controversial', 'meaning': '有争议的', 'confusions': ['controversy', 'debated', 'disputed']},
                {'word': 'contemporary', 'meaning': '当代的', 'confusions': ['modern', 'current', 'traditional']},
                {'word': 'predominant', 'meaning': '主要的', 'confusions': ['dominant', 'primary', 'principal']},
                {'word': 'substantial', 'meaning': '大量的', 'confusions': ['significant', 'considerable', 'extensive']},
                {'word': 'inevitable', 'meaning': '不可避免的', 'confusions': ['unavoidable', 'certain', 'necessary']},
                {'word': 'phenomenon', 'meaning': '现象', 'confusions': ['phenomena', 'occurrence', 'event']},
            ]
        }

        self.japanese_grammar = {
            '初级': [
                {'structure': 'ます形', 'example': '食べます', 'meaning': '吃', 'confusions': ['食べる', '食べた', '食べて']},
                {'structure': 'て形', 'example': '食べて', 'meaning': '吃（连接形）', 'confusions': ['食べます', '食べた', '食べる']},
                {'structure': 'た形', 'example': '食べた', 'meaning': '吃了', 'confusions': ['食べます', '食べて', '食べる']},
                {'structure': 'ない形', 'example': '食べない', 'meaning': '不吃', 'confusions': ['食べる', '食べます', '食べた']},
                {'structure': '～ますか', 'example': '食べますか', 'meaning': '吃吗？', 'confusions': ['食べます', '食べた', '食べない']},
            ],
            '中级': [
                {'structure': '～ている', 'example': '食べている', 'meaning': '正在吃', 'confusions': ['食べる', '食べた', '食べます']},
                {'structure': '～たことがある', 'example': '食べたことがある', 'meaning': '吃过', 'confusions': ['食べる', '食べている', '食べた']},
                {'structure': '～そうだ', 'example': 'おいしそう', 'meaning': '看起来好吃', 'confusions': ['おいしい', 'おいしくて', 'おいしかった']},
                {'structure': '～ようだ', 'example': '雨が降るようだ', 'meaning': '好像要下雨', 'confusions': ['降る', '降った', '降りそう']},
                {'structure': '～ながら', 'example': '音楽を聴きながら勉強', 'meaning': '边听音乐边学习', 'confusions': ['聴いて', '聴き', '聴いた']},
            ],
            '高级': [
                {'structure': '～ところだ', 'example': '食べるところだ', 'meaning': '正要吃', 'confusions': ['食べた', '食べている', '食べよう']},
                {'structure': '～たばかり', 'example': '食べたばかり', 'meaning': '刚吃完', 'confusions': ['食べた', '食べている', '食べる']},
                {'structure': '～てみる', 'example': '食べてみる', 'meaning': '试着吃', 'confusions': ['食べる', '食べた', '食べて']},
                {'structure': '～う（よう）とする', 'example': '食べようとする', 'meaning': '想要吃', 'confusions': ['食べる', '食べたい', '食べて']},
                {'structure': '～に決まっている', 'example': '彼は来るに決まっている', 'meaning': '他肯定会来', 'confusions': ['来る', '来た', '来ない']},
            ]
        }

        self.english_grammar = {
            '初级': [
                {'structure': 'Present Simple', 'example': 'I eat', 'meaning': '我吃', 'confusions': ['I ate', 'I am eating', 'I will eat']},
                {'structure': 'Present Continuous', 'example': 'I am eating', 'meaning': '我正在吃', 'confusions': ['I eat', 'I ate', 'I was eating']},
                {'structure': 'Past Simple', 'example': 'I ate', 'meaning': '我吃了', 'confusions': ['I eat', 'I am eating', 'I had eaten']},
                {'structure': 'Future Simple', 'example': 'I will eat', 'meaning': '我将要吃', 'confusions': ['I eat', 'I am eating', 'I ate']},
                {'structure': 'Comparative', 'example': 'bigger', 'meaning': '更大', 'confusions': ['big', 'biggest', 'more big']},
            ],
            '中级': [
                {'structure': 'Present Perfect', 'example': 'I have eaten', 'meaning': '我已经吃了', 'confusions': ['I ate', 'I have been eating', 'I had eaten']},
                {'structure': 'Past Continuous', 'example': 'I was eating', 'meaning': '我当时正在吃', 'confusions': ['I ate', 'I am eating', 'I had been eating']},
                {'structure': 'Past Perfect', 'example': 'I had eaten', 'meaning': '我之前已经吃了', 'confusions': ['I ate', 'I have eaten', 'I had been eating']},
                {'structure': 'Future Continuous', 'example': 'I will be eating', 'meaning': '我那时会正在吃', 'confusions': ['I will eat', 'I am eating', 'I was eating']},
                {'structure': 'Passive Voice', 'example': 'It is eaten', 'meaning': '它被吃', 'confusions': ['It eats', 'It ate', 'It was eaten']},
            ],
            '高级': [
                {'structure': 'Present Perfect Continuous', 'example': 'I have been eating', 'meaning': '我一直在吃', 'confusions': ['I have eaten', 'I am eating', 'I was eating']},
                {'structure': 'Past Perfect Continuous', 'example': 'I had been eating', 'meaning': '我之前一直在吃', 'confusions': ['I had eaten', 'I was eating', 'I have been eating']},
                {'structure': 'Future Perfect', 'example': 'I will have eaten', 'meaning': '我到那时会已经吃了', 'confusions': ['I will eat', 'I will be eating', 'I have eaten']},
                {'structure': 'Conditional', 'example': 'If I had eaten', 'meaning': '如果我当时吃了', 'confusions': ['If I eat', 'If I ate', 'If I would eat']},
                {'structure': 'Reported Speech', 'example': 'He said he had eaten', 'meaning': '他说他吃了', 'confusions': ['He said "I ate"', 'He says he eats', 'He said he ate']},
            ]
        }

        self.math_problems = {
            '初级': [
                {'operation': '加法', 'question': '2 + 3 = ?', 'answer': 5, 'confusions': [4, 6, 7]},
                {'operation': '减法', 'question': '10 - 4 = ?', 'answer': 6, 'confusions': [5, 7, 8]},
                {'operation': '乘法', 'question': '4 × 5 = ?', 'answer': 20, 'confusions': [19, 21, 25]},
                {'operation': '除法', 'question': '18 ÷ 3 = ?', 'answer': 6, 'confusions': [5, 7, 9]},
                {'operation': '简单方程', 'question': 'x + 5 = 12，x = ?', 'answer': 7, 'confusions': [6, 8, 17]},
            ],
            '中级': [
                {'operation': '四则运算', 'question': '3 × (4 + 2) - 5 = ?', 'answer': 13, 'confusions': [11, 14, 17]},
                {'operation': '分数运算', 'question': '1/2 + 1/3 = ?（用分数表示）', 'answer': '5/6', 'confusions': ['2/5', '1/6', '7/6']},
                {'operation': '小数运算', 'question': '2.5 × 4.8 = ?', 'answer': 12, 'confusions': [10, 11, 14]},
                {'operation': '百分数', 'question': '20% of 150 = ?', 'answer': 30, 'confusions': [20, 25, 35]},
                {'operation': '一元一次方程', 'question': '2x + 8 = 20，x = ?', 'answer': 6, 'confusions': [5, 7, 14]},
            ],
            '高级': [
                {'operation': '平方运算', 'question': '12² + 5² = ?', 'answer': 169, 'confusions': [144, 139, 174]},
                {'operation': '平方根', 'question': '√(64 + 36) = ?', 'answer': 10, 'confusions': [8, 9, 11]},
                {'operation': '一元二次方程', 'question': 'x² - 5x + 6 = 0，x的较小解是?', 'answer': 2, 'confusions': [1, 3, 6]},
                {'operation': '比例问题', 'question': '如果3:5 = x:20，x = ?', 'answer': 12, 'confusions': [10, 15, 18]},
                {'operation': '几何面积', 'question': '半径为5的圆面积是?（π取3.14）', 'answer': 78.5, 'confusions': [31.4, 157, 25]},
            ]
        }

    def get_questions_from_db(self, exam_id, count=10):
        """从数据库题库获取题目"""
        questions = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM t_fb06970853c347b6 
                WHERE exam_id = ? 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (exam_id, count))
            
            rows = cursor.fetchall()
            for row in rows:
                options = []
                if row['option_a']:
                    options.append({'key': 'A', 'text': row['option_a']})
                if row['option_b']:
                    options.append({'key': 'B', 'text': row['option_b']})
                if row['option_c']:
                    options.append({'key': 'C', 'text': row['option_c']})
                if row['option_d']:
                    options.append({'key': 'D', 'text': row['option_d']})
                
                questions.append({
                    'id': row['id'],
                    'type': row['question_type'],
                    'content': row['question_text'],
                    'options': options,
                    'correct_answer': row['correct_answer'],
                    'explanation': row['explanation'],
                    'audio_available': row['audio_available'] == 1,
                    'language': row['language']
                })
            
            conn.close()
        except Exception as e:
            print(f"从数据库获取题目失败: {e}")
        
        return questions

    def generate_japanese_vocab_question(self, difficulty):
        """生成日语词汇单选题"""
        vocab_list = self.japanese_vocabulary.get(difficulty, [])
        if not vocab_list:
            return None
        
        vocab = random.choice(vocab_list)
        correct_answer = vocab['meaning']
        
        all_confusions = set()
        for v in vocab_list:
            all_confusions.update(v['confusions'])
        all_confusions.discard(correct_answer)
        
        wrong_options = random.sample(list(all_confusions), min(3, len(all_confusions)))
        options = [
            {'key': 'A', 'text': correct_answer},
            {'key': 'B', 'text': wrong_options[0] if len(wrong_options) > 0 else '错误选项1'},
            {'key': 'C', 'text': wrong_options[1] if len(wrong_options) > 1 else '错误选项2'},
            {'key': 'D', 'text': wrong_options[2] if len(wrong_options) > 2 else '错误选项3'},
        ]
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == correct_answer)
        
        return {
            'type': '单选题',
            'content': f"「{vocab['word']}」（{vocab['kana']}）の意味は何ですか？",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"「{vocab['word']}」（{vocab['kana']}）は「{correct_answer}」を意味します。",
            'audio_available': False,
            'language': '日语'
        }

    def generate_english_vocab_question(self, difficulty):
        """生成英语词汇单选题"""
        vocab_list = self.english_vocabulary.get(difficulty, [])
        if not vocab_list:
            return None
        
        vocab = random.choice(vocab_list)
        correct_answer = vocab['meaning']
        
        all_confusions = set()
        for v in vocab_list:
            all_confusions.update(v['confusions'])
        all_confusions.discard(vocab['word'])
        
        wrong_options = random.sample(list(all_confusions), min(3, len(all_confusions)))
        options = [
            {'key': 'A', 'text': correct_answer},
            {'key': 'B', 'text': self._get_word_meaning(wrong_options[0]) if len(wrong_options) > 0 else '错误选项1'},
            {'key': 'C', 'text': self._get_word_meaning(wrong_options[1]) if len(wrong_options) > 1 else '错误选项2'},
            {'key': 'D', 'text': self._get_word_meaning(wrong_options[2]) if len(wrong_options) > 2 else '错误选项3'},
        ]
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == correct_answer)
        
        return {
            'type': '单选题',
            'content': f"What does '{vocab['word']}' mean?",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"'{vocab['word']}' means '{correct_answer}'.",
            'audio_available': True,
            'language': '英语'
        }

    def _get_word_meaning(self, word):
        """获取单词的中文意思"""
        for level, words in self.english_vocabulary.items():
            for w in words:
                if w['word'] == word:
                    return w['meaning']
        return word

    def generate_japanese_grammar_question(self, difficulty):
        """生成日语语法单选题"""
        grammar_list = self.japanese_grammar.get(difficulty, [])
        if not grammar_list:
            return None
        
        grammar = random.choice(grammar_list)
        
        options = [
            {'key': 'A', 'text': grammar['structure']},
            {'key': 'B', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
            {'key': 'C', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
            {'key': 'D', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
        ]
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == grammar['structure'])
        
        return {
            'type': '单选题',
            'content': f"「{grammar['example']}」はどの文法構造ですか？",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"「{grammar['example']}」は「{grammar['structure']}」の構造で、「{grammar['meaning']}」という意味です。",
            'audio_available': False,
            'language': '日语'
        }

    def generate_english_grammar_question(self, difficulty):
        """生成英语语法单选题"""
        grammar_list = self.english_grammar.get(difficulty, [])
        if not grammar_list:
            return None
        
        grammar = random.choice(grammar_list)
        
        options = [
            {'key': 'A', 'text': grammar['structure']},
            {'key': 'B', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
            {'key': 'C', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
            {'key': 'D', 'text': random.choice([g['structure'] for g in grammar_list if g['structure'] != grammar['structure']])},
        ]
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == grammar['structure'])
        
        return {
            'type': '单选题',
            'content': f"What grammatical structure is used in: '{grammar['example']}'?",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"'{grammar['example']}' uses {grammar['structure']}, meaning '{grammar['meaning']}'.",
            'audio_available': True,
            'language': '英语'
        }

    def generate_math_question(self, difficulty):
        """生成数学单选题"""
        problems = self.math_problems.get(difficulty, [])
        if not problems:
            return None
        
        problem = random.choice(problems)
        correct_answer = str(problem['answer'])
        
        options = [
            {'key': 'A', 'text': correct_answer},
            {'key': 'B', 'text': str(problem['confusions'][0])},
            {'key': 'C', 'text': str(problem['confusions'][1])},
            {'key': 'D', 'text': str(problem['confusions'][2])},
        ]
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == correct_answer)
        
        return {
            'type': '单选题',
            'content': problem['question'],
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"这是一道{problem['operation']}题，正确答案是 {correct_answer}。",
            'audio_available': False,
            'language': '中文'
        }

    def generate_listening_question(self, language, difficulty):
        """生成听力题"""
        if language == '日语':
            vocab_list = self.japanese_vocabulary.get(difficulty, [])
            vocab = random.choice(vocab_list)
            
            options = [
                {'key': 'A', 'text': vocab['meaning']},
                {'key': 'B', 'text': vocab['confusions'][0] if vocab['confusions'] else '错误选项1'},
                {'key': 'C', 'text': vocab['confusions'][1] if len(vocab['confusions']) > 1 else '错误选项2'},
                {'key': 'D', 'text': vocab['confusions'][2] if len(vocab['confusions']) > 2 else '错误选项3'},
            ]
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == vocab['meaning'])
            
            return {
                'type': '听力题',
                'content': f"聴いた単語「{vocab['word']}」の意味は何ですか？",
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"聴かれた単語は「{vocab['word']}」（{vocab['kana']}）で、意味は「{vocab['meaning']}」です。",
                'audio_available': True,
                'language': '日语'
            }
        
        else:
            vocab_list = self.english_vocabulary.get(difficulty, [])
            vocab = random.choice(vocab_list)
            
            options = [
                {'key': 'A', 'text': vocab['meaning']},
                {'key': 'B', 'text': self._get_word_meaning(vocab['confusions'][0]) if vocab['confusions'] else '错误选项1'},
                {'key': 'C', 'text': self._get_word_meaning(vocab['confusions'][1]) if len(vocab['confusions']) > 1 else '错误选项2'},
                {'key': 'D', 'text': self._get_word_meaning(vocab['confusions'][2]) if len(vocab['confusions']) > 2 else '错误选项3'},
            ]
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == vocab['meaning'])
            
            return {
                'type': '听力题',
                'content': f"What does the word '{vocab['word']}' mean?",
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"The word you heard is '{vocab['word']}', meaning '{vocab['meaning']}'.",
                'audio_available': True,
                'language': '英语'
            }

    def generate_questions(self, exam_id, count=10, language='中文', difficulty='中级', exam_type='standard'):
        """根据考试配置生成题目列表"""
        questions = []
        
        db_questions = self.get_questions_from_db(exam_id, count // 2)
        questions.extend(db_questions)
        
        remaining = count - len(questions)
        
        for _ in range(remaining):
            if exam_type == 'listening':
                q = self.generate_listening_question(language, difficulty)
            elif language == '日语':
                if random.random() > 0.5:
                    q = self.generate_japanese_vocab_question(difficulty)
                else:
                    q = self.generate_japanese_grammar_question(difficulty)
            elif language == '英语':
                if random.random() > 0.5:
                    q = self.generate_english_vocab_question(difficulty)
                else:
                    q = self.generate_english_grammar_question(difficulty)
            elif language == '中文':
                q = self.generate_math_question(difficulty)
            else:
                q = self.generate_japanese_vocab_question(difficulty)
            
            if q:
                questions.append(q)
        
        random.shuffle(questions)
        
        for i, q in enumerate(questions):
            q['id'] = i + 1
        
        return questions

question_generator = QuestionGenerator()