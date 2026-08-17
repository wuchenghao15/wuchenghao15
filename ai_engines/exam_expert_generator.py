#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版考试专家题目生成器
确保单选题必须有一个正确选项,其余选项必须有混淆性易错性
"""
import random
import sqlite3
from contextlib import contextmanager
import os
from typing import List, Dict
from app.utils.logging import logger

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')

class EnhancedExamExpertGenerator:
    """增强版考试专家题目生成器"""
    
    def __init__(self):
        self.init_knowledge_base()
        logger.info("增强版考试专家题目生成器初始化成功")
    
    def init_knowledge_base(self):
        """初始化知识库"""
        self.japanese_vocab_db = {
            '初级': [
                {
                    'word': '猫',
                    'kana': 'ねこ',
                    'meaning': '猫',
                    'confusions': [
                        {'word': '犬', 'kana': 'いぬ', 'meaning': '狗', 'reason': '都是动物'},
                        {'word': '鳥', 'kana': 'とり', 'meaning': '鸟', 'reason': '都是动物'},
                        {'word': '魚', 'kana': 'さかな', 'meaning': '鱼', 'reason': '都是动物'}
                    ]
                },
                {
                    'word': '食べる',
                    'kana': 'たべる',
                    'meaning': '吃',
                    'confusions': [
                        {'word': '飲む', 'kana': 'のむ', 'meaning': '喝', 'reason': '都是动作'},
                        {'word': '見る', 'kana': 'みる', 'meaning': '看', 'reason': '都是动作'},
                        {'word': '話す', 'kana': 'はなす', 'meaning': '说', 'reason': '都是动作'}
                    ]
                },
                {
                    'word': '本',
                    'kana': 'ほん',
                    'meaning': '书',
                    'confusions': [
                        {'word': '雑誌', 'kana': 'ざっし', 'meaning': '杂志', 'reason': '都是读物'},
                        {'word': '新聞', 'kana': 'しんぶん', 'meaning': '报纸', 'reason': '都是读物'},
                        {'word': '辞書', 'kana': 'じしょ', 'meaning': '字典', 'reason': '都是读物'}
                    ]
                },
                {
                    'word': '水',
                    'kana': 'みず',
                    'meaning': '水',
                    'confusions': [
                        {'word': 'お茶', 'kana': 'おちゃ', 'meaning': '茶', 'reason': '都是饮品'},
                        {'word': 'コーヒー', 'kana': 'こーひー', 'meaning': '咖啡', 'reason': '都是饮品'},
                        {'word': 'ジュース', 'kana': 'じゅーす', 'meaning': '果汁', 'reason': '都是饮品'}
                    ]
                }
            ],
            '中级': [
                {
                    'word': '勉強',
                    'kana': 'べんきょう',
                    'meaning': '学习',
                    'confusions': [
                        {'word': '仕事', 'kana': 'しごと', 'meaning': '工作', 'reason': '都是活动'},
                        {'word': '研究', 'kana': 'けんきゅう', 'meaning': '研究', 'reason': '都是学习相关'},
                        {'word': '練習', 'kana': 'れんしゅう', 'meaning': '练习', 'reason': '都是学习相关'}
                    ]
                },
                {
                    'word': '重要',
                    'kana': 'じゅうよう',
                    'meaning': '重要',
                    'confusions': [
                        {'word': '重大', 'kana': 'じゅうだい', 'meaning': '重大', 'reason': '都是重要性'},
                        {'word': '必要', 'kana': 'ひつよう', 'meaning': '必要', 'reason': '都是重要性'},
                        {'word': '大切', 'kana': 'たいせつ', 'meaning': '重要', 'reason': '都是重要性'}
                    ]
                }
            ],
            '高级': [
                {
                    'word': '複雑',
                    'kana': 'ふくざつ',
                    'meaning': '复杂',
                    'confusions': [
                        {'word': '簡単', 'kana': 'かんたん', 'meaning': '简单', 'reason': '反义词'},
                        {'word': '難しい', 'kana': 'むずかしい', 'meaning': '困难', 'reason': '都是难度'},
                        {'word': '困難', 'kana': 'こんなん', 'meaning': '困难', 'reason': '都是难度'}
                    ]
                }
            ]
        }
        
        self.japanese_grammar_db = {
            '初级': [
                {
                    'sentence': '私は毎日学校に___',
                    'correct_answer': '行きます',
                    'meaning': '我每天去学校',
                    'confusions': [
                        {'answer': '行きました', 'explanation': '时态混淆'},
                        {'answer': '行きません', 'explanation': '否定混淆'},
                        {'answer': '行きましょう', 'explanation': '祈使混淆'}
                    ]
                },
                {
                    'sentence': 'この本は___です',
                    'correct_answer': 'おもしろい',
                    'meaning': '这本书很有趣',
                    'confusions': [
                        {'answer': 'おもしろくない', 'explanation': '否定混淆'},
                        {'answer': 'おもしろかった', 'explanation': '过去式混淆'},
                        {'answer': 'おもしろいですか', 'explanation': '疑问混淆'}
                    ]
                }
            ],
            '中级': [
                {
                    'sentence': '日本に___と思います',
                    'correct_answer': '行きたい',
                    'meaning': '我想去日本',
                    'confusions': [
                        {'answer': '行きました', 'explanation': '过去式混淆'},
                        {'answer': '行きます', 'explanation': '现在式混淆'},
                        {'answer': '行きたくない', 'explanation': '否定混淆'}
                    ]
                }
            ]
        }
        
        self.english_vocab_db = {
            '初级': [
                {
                    'word': 'apple',
                    'meaning': '苹果',
                    'confusions': [
                        {'word': 'orange', 'meaning': '橘子', 'reason': '都是水果'},
                        {'word': 'banana', 'meaning': '香蕉', 'reason': '都是水果'},
                        {'word': 'grape', 'meaning': '葡萄', 'reason': '都是水果'}
                    ]
                },
                {
                    'word': 'beautiful',
                    'meaning': '美丽的',
                    'confusions': [
                        {'word': 'ugly', 'meaning': '丑的', 'reason': '反义词'},
                        {'word': 'pretty', 'meaning': '漂亮的', 'reason': '近义词'},
                        {'word': 'big', 'meaning': '大的', 'reason': '形容词混淆'}
                    ]
                }
            ],
            '中级': [
                {
                    'word': 'environment',
                    'meaning': '环境',
                    'confusions': [
                        {'word': 'ecology', 'meaning': '生态学', 'reason': '相关词'},
                        {'word': 'nature', 'meaning': '自然', 'reason': '相关词'},
                        {'word': 'environmentalist', 'meaning': '环保主义者', 'reason': '相关词'}
                    ]
                }
            ]
        }
        
        self.math_problem_db = {
            '初级': [
                {
                    'question': '12 + 18 = ?',
                    'correct_answer': '30',
                    'confusions': [
                        {'answer': '28', 'explanation': '加法错误'},
                        {'answer': '32', 'explanation': '加法错误'},
                        {'answer': '29', 'explanation': '加法错误'}
                    ]
                },
                {
                    'question': '36 ÷ 4 = ?',
                    'correct_answer': '9',
                    'confusions': [
                        {'answer': '8', 'explanation': '除法错误'},
                        {'answer': '10', 'explanation': '除法错误'},
                        {'answer': '7', 'explanation': '除法错误'}
                    ]
                },
                {
                    'question': '5的3次方 = ?',
                    'correct_answer': '125',
                    'confusions': [
                        {'answer': '15', 'explanation': '次方与乘法混淆'},
                        {'answer': '55', 'explanation': '次方计算错误'},
                        {'answer': '25', 'explanation': '次方错误'}
                    ]
                }
            ],
            '中级': [
                {
                    'question': '如果一个长方形长8,宽5,周长是多少?',
                    'correct_answer': '26',
                    'confusions': [
                        {'answer': '40', 'explanation': '周长与面积混淆'},
                        {'answer': '13', 'explanation': '忘记乘2'},
                        {'answer': '25', 'explanation': '计算错误'}
                    ]
                }
            ]
        }
        
        self.japanese_dialect_db = {
            '关西腔': [
                {
                    'question': '「おおきに」はどういう意味ですか?',
                    'correct_answer': 'ありがとう',
                    'confusions': [
                        {'answer': 'さようなら', 'explanation': '混淆'},
                        {'answer': 'すみません', 'explanation': '混淆'},
                        {'answer': 'こんにちは', 'explanation': '混淆'}
                    ]
                },
                {
                    'question': '「あかん」はどういう意味ですか?',
                    'correct_answer': 'だめ',
                    'confusions': [
                        {'answer': 'いいです', 'explanation': '反义词混淆'},
                        {'answer': 'ありがとう', 'explanation': '混淆'},
                        {'answer': 'わかりました', 'explanation': '混淆'}
                    ]
                }
            ],
            '关东腔': [
                {
                    'question': '「承知いたしました」はどういう意味ですか?',
                    'correct_answer': 'わかりました',
                    'confusions': [
                        {'answer': 'すみません', 'explanation': '混淆'},
                        {'answer': 'ありがとう', 'explanation': '混淆'},
                        {'answer': 'さようなら', 'explanation': '混淆'}
                    ]
                }
            ]
        }
        
        self.english_dialect_db = {
            'british': [
                {
                    'question': 'What is the British English word for "color"?',
                    'correct_answer': 'colour',
                    'confusions': [
                        {'answer': 'colur', 'explanation': '拼写错误'},
                        {'answer': 'coler', 'explanation': '拼写错误'},
                        {'answer': 'colo(u)r', 'explanation': '拼写错误'}
                    ]
                },
                {
                    'question': 'What do British people call "lift"?',
                    'correct_answer': 'elevator',
                    'confusions': [
                        {'answer': 'escalator', 'explanation': '混淆'},
                        {'answer': 'stairs', 'explanation': '混淆'},
                        {'answer': 'ladder', 'explanation': '混淆'}
                    ]
                }
            ],
            'american': [
                {
                    'question': 'What is the American English spelling of "travelled"?',
                    'correct_answer': 'traveled',
                    'confusions': [
                        {'answer': 'travaled', 'explanation': '拼写错误'},
                        {'answer': 'travelleed', 'explanation': '拼写错误'},
                        {'answer': 'travelled', 'explanation': '英式拼写混淆'}
                    ]
                }
            ]
        }
    
    def generate_questions(self, language: str, difficulty: str, 
                          exam_type: str = 'standard', 
                          question_count: int = 10) -> List[Dict]:
        """生成高质量题目(确保不重复)"""
        questions = []
        used_contents = set()
        
        normalized_difficulty = self._normalize_difficulty(difficulty)
        
        max_attempts = question_count * 5
        
        for attempt in range(max_attempts):
            if len(questions) >= question_count:
                break
            
            if exam_type == 'listening':
                q = self._generate_listening_question(language, normalized_difficulty)
            elif language == '日语':
                if random.random() > 0.5:
                    q = self._generate_japanese_vocab_question(normalized_difficulty)
                else:
                    q = self._generate_japanese_grammar_question(normalized_difficulty)
            elif language == '英语':
                if random.random() > 0.5:
                    q = self._generate_english_vocab_question(normalized_difficulty)
                else:
                    q = self._generate_english_grammar_question(normalized_difficulty)
            elif language == '中文':
                q = self._generate_math_question(normalized_difficulty)
            else:
                q = self._generate_japanese_vocab_question(normalized_difficulty)
            
            if q and q['content'] not in used_contents:
                used_contents.add(q['content'])
                q['id'] = len(questions) + 1
                questions.append(q)
        
        return questions
    
    def generate_questions_with_audio(self, language: str, difficulty: str, 
                                     exam_type: str = 'standard', 
                                     question_count: int = 10,
                                     voice_type: str = 'standard') -> List[Dict]:
        """生成带音频的题目"""
        questions = self.generate_questions(language, difficulty, exam_type, question_count)
        
        try:
            from app.ai.audio_manager import audio_manager
            
            for q in questions:
                if q.get('audio_available', False):
                    audio_url = audio_manager.generate_audio_url(q['content'], language, voice_type)
                    q['audio_url'] = audio_url
        except Exception as e:
            logger.error(f"生成音频URL失败: {str(e)}")
        
        return questions
    
    def _normalize_difficulty(self, difficulty: str) -> str:
        """标准化难度级别"""
        difficulty_map = {
            '初级': '初级',
            '中级': '中级', 
            '高级': '高级',
            '专家级': '高级',
            '入门': '初级',
            '基础': '初级',
            '自适应': random.choice(['初级', '中级', '高级']),
            '自动': random.choice(['初级', '中级', '高级']),
        }
        return difficulty_map.get(difficulty, '初级')
    
    def _generate_japanese_vocab_question(self, difficulty: str) -> Dict:
        """生成日语词汇题目"""
        vocab_list = self.japanese_vocab_db.get(difficulty, self.japanese_vocab_db['初级'])
        vocab_item = random.choice(vocab_list)
        
        options = [{'key': 'A', 'text': vocab_item['meaning']}]
        confusion = random.sample(vocab_item['confusions'], min(3, len(vocab_item['confusions'])))
        for conf in confusion:
            options.append({'key': chr(66 + len(options) - 1), 'text': conf['meaning']})
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == vocab_item['meaning'])
        
        return {
            'type': '单选题',
            'content': f"「{vocab_item['word']}」({vocab_item['kana']}」の正しい意味はどれですか?",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"「{vocab_item['word']}」({vocab_item['kana']}」は「{vocab_item['meaning']}」を意味します.",
            'audio_available': True,
            'language': '日语'
        }
    
    def _generate_japanese_grammar_question(self, difficulty: str) -> Dict:
        """生成日语文法题目"""
        grammar_list = self.japanese_grammar_db.get(difficulty, self.japanese_grammar_db['初级'])
        grammar_item = random.choice(grammar_list)
        
        options = [{'key': 'A', 'text': grammar_item['correct_answer']}]
        for conf in grammar_item['confusions']:
            options.append({'key': chr(66 + len(options) - 1), 'text': conf['answer']})
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == grammar_item['correct_answer'])
        
        return {
            'type': '单选题',
            'content': f"_____の文章を完成させてください.{grammar_item['sentence']}",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"正解は「{grammar_item['correct_answer']}」で、文は「{grammar_item['meaning']}」を意味します.",
            'audio_available': True,
            'language': '日语'
        }
    
    def _generate_english_vocab_question(self, difficulty: str) -> Dict:
        """生成英语词汇题目"""
        vocab_list = self.english_vocab_db.get(difficulty, self.english_vocab_db['初级'])
        vocab_item = random.choice(vocab_list)
        
        options = [{'key': 'A', 'text': vocab_item['meaning']}]
        for conf in vocab_item['confusions']:
            options.append({'key': chr(66 + len(options) - 1), 'text': conf['meaning']})
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == vocab_item['meaning'])
        
        return {
            'type': '单选题',
            'content': f"What is the correct meaning of \"{vocab_item['word']}\"?",
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"The word \"{vocab_item['word']}\" means \"{vocab_item['meaning']}\".",
            'audio_available': True,
            'language': '英语'
        }
    
    def _generate_english_grammar_question(self, difficulty: str) -> Dict:
        """生成英语语法题目(简化版使用词汇替代"""
        return self._generate_english_vocab_question(difficulty)
    
    def _generate_math_question(self, difficulty: str) -> Dict:
        """生成数学题目"""
        problem_list = self.math_problem_db.get(difficulty, self.math_problem_db['初级'])
        problem_item = random.choice(problem_list)
        
        options = [{'key': 'A', 'text': problem_item['correct_answer']}]
        for conf in problem_item['confusions']:
            options.append({'key': chr(66 + len(options) - 1), 'text': conf['answer']})
        
        random.shuffle(options)
        correct_key = next(opt['key'] for opt in options if opt['text'] == problem_item['correct_answer'])
        
        return {
            'type': '单选题',
            'content': problem_item['question'],
            'options': options,
            'correct_answer': correct_key,
            'explanation': f"正解は {problem_item['correct_answer']} です.",
            'audio_available': False,
            'language': '中文'
        }
    
    def _generate_listening_question(self, language: str, difficulty: str) -> Dict:
        """生成听力题目"""
        if language == '日语':
            vocab_list = self.japanese_vocab_db.get(difficulty, self.japanese_vocab_db['初级'])
            vocab_item = random.choice(vocab_list)
            
            options = [{'key': 'A', 'text': vocab_item['meaning']}]
            for conf in vocab_item['confusions']:
                options.append({'key': chr(66 + len(options) - 1), 'text': conf['meaning']})
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == vocab_item['meaning'])
            
            return {
                'type': '听力题',
                'content': f"「{vocab_item['word']}」を聞いて、正しい意味を選んでください.",
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"「{vocab_item['word']}」は「{vocab_item['meaning']}」です.",
                'audio_available': True,
                'language': '日语'
            }
        else:
            vocab_list = self.english_vocab_db.get(difficulty, self.english_vocab_db['初级'])
            vocab_item = random.choice(vocab_list)
            
            options = [{'key': 'A', 'text': vocab_item['meaning']}]
            for conf in vocab_item['confusions']:
                options.append({'key': chr(66 + len(options) - 1), 'text': conf['meaning']})
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == vocab_item['meaning'])
            
            return {
                'type': '听力题',
                'content': f"Listen to the word and choose the correct meaning of \"{vocab_item['word']}\".",
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"The meaning is \"{vocab_item['meaning']}\".",
                'audio_available': True,
                'language': '英语'
            }
    
    def generate_dialect_questions(self, dialect_type: str, question_count: int = 5) -> List[Dict]:
        """生成方言题目"""
        if dialect_type == '关西腔' or dialect_type == 'kansai':
            return self._generate_japanese_dialect_questions('关西腔', question_count)
        elif dialect_type == '关东腔' or dialect_type == 'kanto':
            return self._generate_japanese_dialect_questions('关东腔', question_count)
        elif dialect_type == 'british':
            return self._generate_english_dialect_questions('british', question_count)
        elif dialect_type == 'american':
            return self._generate_english_dialect_questions('american', question_count)
        else:
            return []
    
    def _generate_japanese_dialect_questions(self, dialect: str, count: int) -> List[Dict]:
        """生成日语方言题目"""
        questions = []
        q_list = self.japanese_dialect_db.get(dialect, [])
        q_list = q_list * (count // len(q_list) + 1)
        
        for i, item in enumerate(random.sample(q_list, min(count, len(q_list)))):
            options = [{'key': 'A', 'text': item['correct_answer']}]
            for conf in item['confusions']:
                options.append({'key': chr(66 + len(options) - 1), 'text': conf['answer']})
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == item['correct_answer'])
            
            questions.append({
                'id': i + 1,
                'type': '单选题',
                'content': item['question'],
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"正解は「{item['correct_answer']}」です.",
                'audio_available': True,
                'language': '日语'
            })
        
        return questions
    
    def _generate_english_dialect_questions(self, dialect: str, count: int) -> List[Dict]:
        """生成英语方言题目"""
        questions = []
        q_list = self.english_dialect_db.get(dialect, [])
        q_list = q_list * (count // len(q_list) + 1)
        
        for i, item in enumerate(random.sample(q_list, min(count, len(q_list)))):
            options = [{'key': 'A', 'text': item['correct_answer']}]
            for conf in item['confusions']:
                options.append({'key': chr(66 + len(options) - 1), 'text': conf['answer']})
            
            random.shuffle(options)
            correct_key = next(opt['key'] for opt in options if opt['text'] == item['correct_answer'])
            
            questions.append({
                'id': i + 1,
                'type': '单选题',
                'content': item['question'],
                'options': options,
                'correct_answer': correct_key,
                'explanation': f"The correct answer is \"{item['correct_answer']}\".",
                'audio_available': True,
                'language': '英语'
            })
        
        return questions

enhanced_exam_generator = EnhancedExamExpertGenerator()
