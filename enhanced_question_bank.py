问：下列选项中，属于我国根本政治制度的是？
A. 人民代表大会制度
B. 社会主义制度
C. 民主集中制
D. 多党合作制度#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版题库管理系统 - 支持题型拓展、真题更新和实时内容"""

import os
import re
# import json removed - using database storage
import sqlite3
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('question_bank_system')

class EnhancedQuestionBankSystem:
    def __init__(self):
        self.db_path = 'app.db'
        self.question_types = {}
        self.init_question_types()
        self.init_database()
    
    def init_question_types(self):
        """初始化题型定义"""
        self.question_types = {
            'single_choice': {'name': '单选题', 'description': '从选项中选择一个正确答案'},
            'multiple_choice': {'name': '多选题', 'description': '从选项中选择多个正确答案'},
            'judge': {'name': '判断题', 'description': '判断正误'},
            'fill_blank': {'name': '填空题', 'description': '填写正确答案'},
            'short_answer': {'name': '简答题', 'description': '简要回答问题'},
            'essay': {'name': '论述题', 'description': '详细论述问题'},
            'code': {'name': '编程题', 'description': '编写代码解决问题'},
            'case': {'name': '案例分析', 'description': '分析案例并回答问题'}
        }
        logger.info("题型定义初始化完成")
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                type TEXT,
                category TEXT,
                subcategory TEXT,
                difficulty INTEGER,
                content TEXT,
                options TEXT,
                answer TEXT,
                analysis TEXT,
                source TEXT,
                year INTEGER,
                tags TEXT,
                language TEXT DEFAULT 'zh',
                created_at TEXT,
                updated_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE,
                description TEXT,
                question_count INTEGER DEFAULT 0,
                last_update TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS exam_real_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT,
                exam_name TEXT,
                exam_year INTEGER,
                exam_type TEXT,
                source_url TEXT,
                FOREIGN KEY(question_id) REFERENCES questions(question_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS current_affairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                date TEXT,
                tags TEXT,
                source TEXT,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS internet_memes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meme TEXT,
                meaning TEXT,
                origin TEXT,
                popularity INTEGER,
                tags TEXT,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS question_bank_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT,
                value INTEGER,
                timestamp TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("数据库表初始化完成")
    
    def add_question(self, question_data):
        """添加题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import random
            question_id = f"{question_data['type']}_{int(time.time())}_{random.randint(1000, 9999)}"
            
            cursor.execute('''
                INSERT INTO questions 
                (question_id, type, category, subcategory, difficulty, 
                 content, options, answer, analysis, source, year, tags, language, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question_id,
                question_data.get('type', 'single_choice'),
                question_data.get('category', 'other'),
                question_data.get('subcategory', ''),
                question_data.get('difficulty', 3),
                question_data['content'],
                str(question_data.get('options', [])),
                question_data['answer'],
                question_data.get('analysis', ''),
                question_data.get('source', 'system'),
                question_data.get('year', datetime.now().year),
                str(question_data.get('tags', [])),
                question_data.get('language', 'zh'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.update_category_count(question_data.get('category', 'other'))
            self.update_stats()
            
            return question_id
        except Exception as e:
            logger.error(f"添加题目失败: {e}")
            return None
    
    def batch_add_questions(self, questions_data):
        """批量添加题目"""
        success_count = 0
        failed_count = 0
        
        for question in questions_data:
            if self.add_question(question):
                success_count += 1
            else:
                failed_count += 1
        
        logger.info(f"批量添加完成: 成功 {success_count}, 失败 {failed_count}")
        return success_count, failed_count
    
    def update_category_count(self, category):
        """更新分类题目数量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT question_count FROM question_categories WHERE category = ?', (category,))
            result = cursor.fetchone()
            
            if result:
                cursor.execute('''
                    UPDATE question_categories 
                    SET question_count = question_count + 1, last_update = ? 
                    WHERE category = ?
                ''', (datetime.now().isoformat(), category))
            else:
                cursor.execute('''
                    INSERT INTO question_categories (category, description, question_count, last_update)
                    VALUES (?, ?, 1, ?)
                ''', (category, f"{category}分类", datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新分类统计失败: {e}")
    
    def update_stats(self):
        """更新题库统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO question_bank_stats (stat_type, value, timestamp)
                VALUES ('total_questions', ?, ?)
            ''', (total_count, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新统计失败: {e}")
    
    def import_real_exam_questions(self, exam_name, exam_year, questions):
        """导入历年真题"""
        success_count = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for question in questions:
                question_id = self.add_question(question)
                if question_id:
                    cursor.execute('''
                        INSERT INTO exam_real_questions
                        (question_id, exam_name, exam_year, exam_type)
                        VALUES (?, ?, ?, ?)
                    ''', (question_id, exam_name, exam_year, 'real'))
                    success_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功导入 {success_count} 道{exam_name}{exam_year}年真题")
        except Exception as e:
            logger.error(f"导入真题失败: {e}")
        
        return success_count
    
    def fetch_current_affairs(self):
        """获取时事政治内容"""
        logger.info("获取时事政治内容...")
        
        current_affairs = []
        
        try:
            response = requests.get('https://newsapi.org/v2/top-headlines', 
                                params={'country': 'cn', 'apiKey': 'demo-key'},
                                timeout=10)
            if response.status_code == 200:
                data = response.json()
                for article in data.get('articles', [])[:10]:
                    current_affairs.append({
                        'title': article.get('title', ''),
                        'content': article.get('description', '') or article.get('content', ''),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'tags': ['时事', '新闻'],
                        'source': article.get('source', {}).get('name', 'unknown')
                    })
        except Exception as e:
            logger.error(f"获取时事新闻失败: {e}")
        
        if current_affairs:
            self.save_current_affairs(current_affairs)
            self.generate_affairs_questions(current_affairs)
        
        return current_affairs
    
    def save_current_affairs(self, affairs):
        """保存时事政治内容"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for affair in affairs:
                cursor.execute('''
                    INSERT OR IGNORE INTO current_affairs
                    (title, content, date, tags, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (affair['title'], affair['content'], affair['date'], 
                      str(affair['tags']), affair['source'], datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存时事内容失败: {e}")
    
    def generate_affairs_questions(self, affairs):
        """根据时事生成题目"""
        questions = []
        
        for affair in affairs:
            questions.append({
                'type': 'single_choice',
                'category': '时事政治',
                'difficulty': 3,
                'content': f"以下哪项是关于\"{affair['title'][:30]}...\"的正确描述？",
                'options': [
                    affair['content'][:50] + "...",
                    "这是一条假新闻",
                    "该事件发生在去年",
                    "以上都不对"
                ],
                'answer': "A",
                'analysis': f"根据{affair['source']}报道，{affair['title']}",
                'tags': ['时事', '政治'],
                'source': 'current_affairs'
            })
        
        self.batch_add_questions(questions)
        logger.info(f"根据时事生成 {len(questions)} 道题目")
    
    def fetch_internet_memes(self):
        """获取网络新梗"""
        logger.info("获取网络新梗...")
        
        memes = [
            {'meme': '躺平', 'meaning': '指年轻人对生活压力的一种消极应对态度', 'origin': '2021年', 'tags': ['流行语', '生活']},
            {'meme': '内卷', 'meaning': '指过度竞争导致的内部消耗', 'origin': '2020年', 'tags': ['流行语', '社会']},
            {'meme': '破防', 'meaning': '心理防线被突破', 'origin': '游戏圈', 'tags': ['网络用语', '情绪']},
            {'meme': 'yyds', 'meaning': '永远的神，表达强烈赞美', 'origin': '电竞圈', 'tags': ['网络用语', '赞美']},
            {'meme': 'emo了', 'meaning': '情绪低落、伤感', 'origin': '网络流行', 'tags': ['网络用语', '情绪']},
            {'meme': '栓Q', 'meaning': 'thank you的谐音，表达感谢或讽刺', 'origin': '网络', 'tags': ['网络用语', '谐音']},
            {'meme': '芭比Q了', 'meaning': '完了、糟糕了', 'origin': '游戏圈', 'tags': ['网络用语', '感叹']},
            {'meme': '显眼包', 'meaning': '指爱出风头的人', 'origin': '北方方言', 'tags': ['网络用语', '人物']},
            {'meme': '搭子', 'meaning': '因共同需求而结伴的人', 'origin': '方言', 'tags': ['网络用语', '社交']},
            {'meme': '特种兵式旅游', 'meaning': '高强度、高效率的旅行方式', 'origin': '大学生群体', 'tags': ['流行语', '旅游']}
        ]
        
        self.save_memes(memes)
        self.generate_meme_questions(memes)
        
        return memes
    
    def save_memes(self, memes):
        """保存网络新梗"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for meme in memes:
                cursor.execute('''
                    INSERT OR IGNORE INTO internet_memes
                    (meme, meaning, origin, popularity, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (meme['meme'], meme['meaning'], meme['origin'], 
                      50, str(meme['tags']), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存网络新梗失败: {e}")
    
    def generate_meme_questions(self, memes):
        """根据网络新梗生成题目"""
        questions = []
        
        for meme in memes:
            questions.append({
                'type': 'single_choice',
                'category': '网络流行语',
                'difficulty': 2,
                'content': f"网络流行语\"{meme['meme']}\"的含义是什么？",
                'options': [
                    meme['meaning'],
                    f"指一种食物",
                    f"指一种动物",
                    f"指一个地名"
                ],
                'answer': "A",
                'analysis': f"\"{meme['meme']}\"源自{meme['origin']}，意思是{meme['meaning']}",
                'tags': ['网络', '流行语'],
                'source': 'internet_meme'
            })
        
        self.batch_add_questions(questions)
        logger.info(f"根据网络新梗生成 {len(questions)} 道题目")
    
    def expand_question_bank(self):
        """扩充题库"""
        print("="*80)
        print("          题库扩充系统")
        print("="*80)
        
        print("\n[1/4] 获取时事政治...")
        affairs = self.fetch_current_affairs()
        print(f"  获取到 {len(affairs)} 条时事新闻")
        
        print("\n[2/4] 获取网络新梗...")
        memes = self.fetch_internet_memes()
        print(f"  获取到 {len(memes)} 个网络新梗")
        
        print("\n[3/4] 导入历年真题...")
        self.import_sample_real_questions()
        
        print("\n[4/4] 生成拓展题目...")
        self.generate_expanded_questions()
        
        self.show_stats()
    
    def import_sample_real_questions(self):
        """导入示例真题"""
        sample_questions = [
            {
                'type': 'single_choice',
                'category': '公务员考试',
                'subcategory': '行测',
                'difficulty': 3,
                'content': '下列选项中，属于我国根本政治制度的是？',
                'options': ['人民代表大会制度', '社会主义制度', '民主集中制', '多党合作制度'],
                'answer': 'A',
                'analysis': '人民代表大会制度是我国的根本政治制度',
                'year': 2023
            },
            {
                'type': 'single_choice',
                'category': '公务员考试',
                'subcategory': '行测',
                'difficulty': 4,
                'content': '根据宪法规定，下列哪项不属于公民的基本权利？',
                'options': ['选举权', '被选举权', '罢工权', '受教育权'],
                'answer': 'C',
                'analysis': '我国宪法未规定罢工权为公民基本权利',
                'year': 2023
            },
            {
                'type': 'multiple_choice',
                'category': '公务员考试',
                'subcategory': '行测',
                'difficulty': 4,
                'content': '下列属于我国基本国策的有？',
                'options': ['计划生育', '对外开放', '保护环境', '节约资源'],
                'answer': 'ABCD',
                'analysis': '以上都是我国的基本国策',
                'year': 2022
            }
        ]
        
        self.import_real_exam_questions('国家公务员考试', 2023, sample_questions)
    
    def generate_expanded_questions(self):
        """生成拓展题目"""
        categories = ['语文', '数学', '英语', '历史', '地理', '物理', '化学', '生物']
        subjects = {
            '语文': ['诗词鉴赏', '阅读理解', '文言文', '现代文'],
            '数学': ['代数', '几何', '概率', '函数'],
            '英语': ['词汇', '语法', '阅读理解', '写作'],
            '历史': ['中国古代史', '中国近现代史', '世界史'],
            '地理': ['自然地理', '人文地理', '区域地理'],
            '物理': ['力学', '电学', '光学', '热学'],
            '化学': ['有机化学', '无机化学', '化学反应'],
            '生物': ['细胞生物学', '遗传学', '生态学']
        }
        
        expanded_questions = []
        
        for category, subcategories in subjects.items():
            for subcategory in subcategories:
                for i in range(5):
                    expanded_questions.append({
                        'type': 'single_choice',
                        'category': category,
                        'subcategory': subcategory,
                        'difficulty': (i % 3) + 2,
                        'content': f"关于{category}-{subcategory}的第{i+1}道测试题",
                        'options': ['选项A', '选项B', '选项C', '选项D'],
                        'answer': chr(65 + (i % 4)),
                        'analysis': f"{category}-{subcategory}题目解析",
                        'tags': [category, subcategory],
                        'source': 'expansion'
                    })
        
        success, failed = self.batch_add_questions(expanded_questions)
        print(f"  生成 {success} 道拓展题目")
    
    def show_stats(self):
        """显示题库统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT category, question_count FROM question_categories ORDER BY question_count DESC')
            categories = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) FROM exam_real_questions')
            real_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM current_affairs')
            affairs_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM internet_memes')
            memes_count = cursor.fetchone()[0]
            
            conn.close()
            
            print("\n" + "="*80)
            print("          题库统计报告")
            print("="*80)
            print(f"\n  总题目数: {total}")
            print(f"  真题数量: {real_count}")
            print(f"  时事内容: {affairs_count}")
            print(f"  网络新梗: {memes_count}")
            
            print("\n  分类分布:")
            for category, count in categories[:10]:
                print(f"    {category}: {count} 题")
        
        except Exception as e:
            logger.error(f"获取统计失败: {e}")

def main():
    qb_system = EnhancedQuestionBankSystem()
    qb_system.expand_question_bank()

if __name__ == "__main__":
    main()