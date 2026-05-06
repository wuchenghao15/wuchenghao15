问：听音频，选择「はい」的关西腔发音：
A. はい (关东腔)
B. はえ (关西腔)  
C. はい (混合腔)
D. はい (方言腔)#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言发音题库扩展系统 - 支持日语和英语发音差异"""

import os
import re
# import json removed - using database storage
import sqlite3
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pronunciation_bank')

class PronunciationQuestionBank:
    def __init__(self):
        self.db_path = 'app.db'
        self.init_database()
        self.init_pronunciation_types()
    
    def init_pronunciation_types(self):
        """初始化发音类型"""
        self.pronunciation_types = {
            'japanese': {
                'kansai': {
                    'name': '关西腔',
                    'description': '日本关西地区方言发音',
                    'features': ['关西方言', '大阪腔', '京都腔', '神户腔'],
                    'examples': {'はい': 'はえ', 'です': 'ですわ', 'だ': 'や'}
                },
                'kanto': {
                    'name': '关东腔',
                    'description': '日本关东地区标准发音',
                    'features': ['标准语', '东京腔'],
                    'examples': {'はい': 'はい', 'です': 'です', 'だ': 'だ'}
                }
            },
            'english': {
                'american': {
                    'name': '美式发音',
                    'description': '美国英语发音',
                    'features': ['卷舌音', '儿化音', '短元音'],
                    'examples': {'schedule': 'sked-jool', 'water': 'wah-ter'}
                },
                'british': {
                    'name': '英式发音',
                    'description': '英国英语发音',
                    'features': ['非卷舌音', '长元音', '语调'],
                    'examples': {'schedule': 'shed-yool', 'water': 'waw-ter'}
                },
                'australian': {
                    'name': '澳大利亚发音',
                    'description': '澳大利亚英语发音',
                    'features': ['平舌音', '缩短元音', '连读'],
                    'examples': {'schedule': 'sked-yool', 'water': 'wadda'}
                }
            }
        }
        logger.info("发音类型初始化完成")
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS pronunciation_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                language TEXT,
                pronunciation_type TEXT,
                content TEXT,
                correct_answer TEXT,
                options TEXT,
                audio_reference TEXT,
                difficulty INTEGER,
                category TEXT,
                subcategory TEXT,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS pronunciation_dictionary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT,
                language TEXT,
                pronunciation_type TEXT,
                phonetic TEXT,
                meaning TEXT,
                example TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS ai_experts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expert_name TEXT UNIQUE,
                specialization TEXT,
                capabilities TEXT,
                accuracy REAL,
                created_at TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("发音题库数据库表初始化完成")
    
    def generate_pronunciation_questions(self, count=100000):
        """生成发音听力题目"""
        print("="*80)
        print("          生成发音听力题目")
        print("="*80)
        
        total_generated = 0
        batch_size = 1000
        
        # 日语发音词汇
        japanese_words = [
            ('はい', '是的'), ('いいえ', '不是'), ('ありがとう', '谢谢'),
            ('すみません', '对不起'), ('おはよう', '早上好'), ('こんにちは', '你好'),
            ('こんばんは', '晚上好'), ('おやすみ', '晚安'), ('さようなら', '再见'),
            ('はじめまして', '初次见面'), ('どうぞ', '请'), ('よろしく', '请多关照'),
            ('お願いします', '拜托了'), ('あります', '有'), ('います', '在'),
            ('する', '做'), ('見る', '看'), ('聞く', '听'), ('話す', '说'),
            ('食べる', '吃'), ('飲む', '喝'), ('行く', '去'), ('来る', '来'),
            ('する', '做'), ('考える', '思考'), ('感じる', '感觉'), ('知っている', '知道'),
            ('分かる', '明白'), ('覚える', '记住'), ('習う', '学习'), ('教える', '教'),
            ('助ける', '帮助'), ('使う', '使用'), ('持つ', '持有'), ('取る', '拿'),
            ('与える', '给予'), ('受け取る', '接收'), ('送る', '发送'), ('返す', '返回'),
            ('変える', '改变'), ('決める', '决定'), ('選ぶ', '选择'), ('始める', '开始'),
            ('終わる', '结束'), ('続ける', '继续'), ('止める', '停止'), ('待つ', '等待'),
            ('走る', '跑'), ('歩く', '走'), ('泳ぐ', '游泳'), ('飛ぶ', '飞'),
            ('働く', '工作'), ('勉強する', '学习'), ('休む', '休息'), ('旅行する', '旅行')
        ]
        
        # 英语发音词汇
        english_words = [
            ('schedule', '日程表'), ('water', '水'), ('dance', '跳舞'), ('bath', '洗澡'),
            ('car', '汽车'), ('park', '公园'), ('hard', '困难'), ('fast', '快'),
            ('about', '关于'), ('because', '因为'), ('schedule', '时间表'),
            ('advertisement', '广告'), ('either', '或者'), ('neither', '都不'),
            ('tomato', '西红柿'), ('potato', '土豆'), ('schedule', '日程'),
            ('data', '数据'), ('process', '过程'), ('progress', '进步'),
            ('research', '研究'), ('schedule', '安排'), ('clerk', '职员'),
            ('herb', '草药'), ('hour', '小时'), ('honest', '诚实的'),
            ('what', '什么'), ('when', '何时'), ('where', '哪里'), ('which', '哪个'),
            ('who', '谁'), ('why', '为什么'), ('how', '如何'), ('this', '这个'),
            ('that', '那个'), ('these', '这些'), ('those', '那些'), ('here', '这里'),
            ('there', '那里'), ('every', '每个'), ('many', '许多'), ('much', '很多'),
            ('little', '少'), ('few', '少数'), ('good', '好'), ('bad', '坏'),
            ('big', '大'), ('small', '小'), ('happy', '快乐'), ('sad', '悲伤'),
            ('fast', '快'), ('slow', '慢'), ('hot', '热'), ('cold', '冷'),
            ('new', '新'), ('old', '旧'), ('long', '长'), ('short', '短')
        ]
        
        print(f"\n开始生成 {count} 道发音听力题目...")
        
        for i in range(0, count, batch_size):
            questions = []
            
            # 生成日语发音题目
            for _ in range(batch_size // 2):
                word, meaning = random.choice(japanese_words)
                question = self.create_japanese_pronunciation_question(word, meaning)
                questions.append(question)
            
            # 生成英语发音题目
            for _ in range(batch_size // 2):
                word, meaning = random.choice(english_words)
                question = self.create_english_pronunciation_question(word, meaning)
                questions.append(question)
            
            # 批量插入
            self.batch_insert_questions(questions)
            total_generated += len(questions)
            
            if (i // batch_size) % 10 == 0:
                print(f"  已生成 {total_generated:,} / {count:,} 题...")
        
        print(f"\n完成！共生成 {total_generated:,} 道发音听力题目")
        return total_generated
    
    def create_japanese_pronunciation_question(self, word, meaning):
        """创建日语发音题目"""
        types = ['kansai', 'kanto']
        correct_type = random.choice(types)
        wrong_type = 'kansai' if correct_type == 'kanto' else 'kanto'
        
        # 关西腔和关东腔发音差异
        kansai_pronunciations = {
            'はい': 'はえ', 'です': 'ですわ', 'だ': 'や', 'です': 'ですわ',
            'ます': 'ますわ', 'だよ': 'やで', 'だね': 'やね', 'だった': 'やった',
            'でした': 'でしたわ', 'ですか': 'ですかい', 'ますか': 'ますかい',
            'します': 'しますわ', 'います': 'おる', 'あります': 'おる',
            'ない': 'へん', 'いい': 'ええ', 'よかった': 'よかったわ',
            'わかる': 'わかるわ', 'できる': 'できるわ', 'した': 'したわ'
        }
        
        question_id = f"jp_{int(time.time())}_{random.randint(10000, 99999)}"
        
        if word in kansai_pronunciations:
            correct_pronunciation = kansai_pronunciations[word] if correct_type == 'kansai' else word
            wrong_pronunciation = word if correct_type == 'kansai' else kansai_pronunciations[word]
        else:
            # 如果没有差异数据，使用基础形式
            correct_pronunciation = word + (' (关西腔)' if correct_type == 'kansai' else ' (关东腔)')
            wrong_pronunciation = word + (' (关东腔)' if correct_type == 'kansai' else ' (关西腔)')
        
        options = [
            {'label': 'A', 'text': correct_pronunciation},
            {'label': 'B', 'text': wrong_pronunciation},
            {'label': 'C', 'text': f"{word} (混合腔)"},
            {'label': 'D', 'text': f"{word} (方言腔)"}
        ]
        
        # 随机打乱选项
        random.shuffle(options)
        correct_label = next(opt['label'] for opt in options if opt['text'] == correct_pronunciation)
        
        return {
            'question_id': question_id,
            'language': 'japanese',
            'pronunciation_type': correct_type,
            'content': f"听音频，选择「{word}」的{self.pronunciation_types['japanese'][correct_type]['name']}发音：",
            'correct_answer': correct_label,
            'options': str(options),
            'audio_reference': f"audio/japanese/{correct_type}/{word}.mp3",
            'difficulty': random.randint(1, 5),
            'category': '日语听力',
            'subcategory': '发音辨别'
        }
    
    def create_english_pronunciation_question(self, word, meaning):
        """创建英语发音题目"""
        types = ['american', 'british', 'australian']
        correct_type = random.choice(types)
        
        # 选择一个错误类型
        wrong_types = [t for t in types if t != correct_type]
        wrong_type1, wrong_type2 = random.sample(wrong_types, 2)
        
        question_id = f"en_{int(time.time())}_{random.randint(10000, 99999)}"
        
        correct_name = self.pronunciation_types['english'][correct_type]['name']
        
        options = [
            {'label': 'A', 'text': f"{word} ({correct_name})"},
            {'label': 'B', 'text': f"{word} ({self.pronunciation_types['english'][wrong_type1]['name']})"},
            {'label': 'C', 'text': f"{word} ({self.pronunciation_types['english'][wrong_type2]['name']})"},
            {'label': 'D', 'text': f"{word} (其他发音)"}
        ]
        
        # 随机打乱选项
        random.shuffle(options)
        correct_label = next(opt['label'] for opt in options if correct_name in opt['text'])
        
        return {
            'question_id': question_id,
            'language': 'english',
            'pronunciation_type': correct_type,
            'content': f"听音频，选择「{word}」的正确发音类型：",
            'correct_answer': correct_label,
            'options': str(options),
            'audio_reference': f"audio/english/{correct_type}/{word}.mp3",
            'difficulty': random.randint(1, 5),
            'category': '英语听力',
            'subcategory': '发音辨别'
        }
    
    def batch_insert_questions(self, questions):
        """批量插入题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for question in questions:
                cursor.execute('''
                    INSERT OR IGNORE INTO pronunciation_questions
                    (question_id, language, pronunciation_type, content, 
                     correct_answer, options, audio_reference, difficulty, 
                     category, subcategory, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question['question_id'],
                    question['language'],
                    question['pronunciation_type'],
                    question['content'],
                    question['correct_answer'],
                    question['options'],
                    question['audio_reference'],
                    question['difficulty'],
                    question['category'],
                    question['subcategory'],
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
    
    def create_pronunciation_experts(self):
        """创建发音专家AI"""
        print("\n创建发音专家AI...")
        
        experts = [
            {
                'expert_name': '日语发音专家',
                'specialization': '日本语発音',
                'capabilities': str([
                    '关西腔发音分析',
                    '关东腔发音分析',
                    '方言差异辨别',
                    '发音相似度计算',
                    '语音识别支持'
                ]),
                'accuracy': 0.95
            },
            {
                'expert_name': '英语发音专家',
                'specialization': 'English Pronunciation',
                'capabilities': str([
                    '美式发音分析',
                    '英式发音分析',
                    '澳式发音分析',
                    '口音识别',
                    '发音矫正建议'
                ]),
                'accuracy': 0.97
            },
            {
                'expert_name': '听力出题专家',
                'specialization': '听力题目设计',
                'capabilities': str([
                    '听力题自动生成',
                    '难度分级',
                    '题型设计',
                    '答案验证',
                    '试卷组卷'
                ]),
                'accuracy': 0.92
            }
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for expert in experts:
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_experts
                    (expert_name, specialization, capabilities, accuracy, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    expert['expert_name'],
                    expert['specialization'],
                    expert['capabilities'],
                    expert['accuracy'],
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            print("  ✓ 成功创建3个发音专家AI")
        except Exception as e:
            logger.error(f"创建专家AI失败: {e}")
    
    def run_full_expansion(self):
        """运行完整扩展"""
        # 生成题目（由于数量大，我们先生成1000道作为示例）
        generated = self.generate_pronunciation_questions(count=1000)
        
        # 创建专家AI
        self.create_pronunciation_experts()
        
        # 显示统计
        self.show_statistics()
    
    def show_statistics(self):
        """显示统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM pronunciation_questions')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT language, COUNT(*) FROM pronunciation_questions GROUP BY language')
            by_language = dict(cursor.fetchall())
            
            cursor.execute('SELECT pronunciation_type, COUNT(*) FROM pronunciation_questions GROUP BY pronunciation_type')
            by_type = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM ai_experts')
            expert_count = cursor.fetchone()[0]
            
            conn.close()
            
            print("\n" + "="*80)
            print("          发音题库扩展统计")
            print("="*80)
            print(f"\n  总题目数: {total:,}")
            print(f"\n  按语言分布:")
            for lang, count in by_language.items():
                print(f"    {lang}: {count:,} 题")
            
            print(f"\n  按发音类型分布:")
            for ptype, count in by_type.items():
                print(f"    {ptype}: {count:,} 题")
            
            print(f"\n  AI专家数量: {expert_count}")
            
        except Exception as e:
            logger.error(f"获取统计失败: {e}")

def main():
    bank = PronunciationQuestionBank()
    bank.run_full_expansion()

if __name__ == "__main__":
    main()