#!/usr/bin/env python3
"""
AI智能作文批改系统
根据学生作文内容进行智能评分和详细批改
"""

import sqlite3
import hashlib
import json
import random
import re
from datetime import datetime
from typing import Dict, List, Optional

class AICompositionGrader:
    """AI智能作文批改引擎"""
    
    CRITERIA = {
        'structure': {'name': '结构组织', 'weight': 0.25, 'max_score': 25},
        'content': {'name': '内容表达', 'weight': 0.30, 'max_score': 30},
        'language': {'name': '语言运用', 'weight': 0.25, 'max_score': 25},
        'creativity': {'name': '创新思维', 'weight': 0.10, 'max_score': 10},
        'grammar': {'name': '语法规范', 'weight': 0.10, 'max_score': 10}
    }
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS composition_gradings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grading_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                word_count INTEGER,
                subject TEXT DEFAULT '语文',
                total_score REAL DEFAULT 0.0,
                structure_score REAL DEFAULT 0.0,
                content_score REAL DEFAULT 0.0,
                language_score REAL DEFAULT 0.0,
                creativity_score REAL DEFAULT 0.0,
                grammar_score REAL DEFAULT 0.0,
                comments TEXT,
                suggestions TEXT,
                grade_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS composition_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grading_id TEXT,
                keyword TEXT,
                frequency INTEGER DEFAULT 1,
                importance TEXT DEFAULT 'medium'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def grade_composition(self, user_id: str, content: str, title: str = '', subject: str = '语文') -> Dict:
        """批改作文"""
        grading_id = hashlib.md5(f"{user_id}{content[:50]}{datetime.now()}".encode()).hexdigest()[:16]
        word_count = len(content.replace(' ', '').replace('\n', ''))
        
        scores = self._calculate_scores(content, title)
        total_score = sum(scores.values())
        
        comments = self._generate_comments(content, scores)
        suggestions = self._generate_suggestions(content, scores)
        keywords = self._extract_keywords(content)
        
        grade_level = self._determine_grade_level(total_score)
        
        self._save_grading(grading_id, user_id, title, content, word_count, subject, 
                          total_score, scores, comments, suggestions, grade_level)
        self._save_keywords(grading_id, keywords)
        
        return {
            'success': True,
            'grading_id': grading_id,
            'user_id': user_id,
            'title': title,
            'word_count': word_count,
            'subject': subject,
            'total_score': round(total_score, 2),
            'grade_level': grade_level,
            'scores': {k: round(v, 2) for k, v in scores.items()},
            'criteria': self.CRITERIA,
            'comments': comments,
            'suggestions': suggestions,
            'keywords': keywords,
            'created_at': datetime.now().isoformat()
        }
    
    def _calculate_scores(self, content: str, title: str) -> Dict:
        """计算各维度得分"""
        scores = {}
        
        scores['structure'] = self._evaluate_structure(content, title)
        scores['content'] = self._evaluate_content(content)
        scores['language'] = self._evaluate_language(content)
        scores['creativity'] = self._evaluate_creativity(content)
        scores['grammar'] = self._evaluate_grammar(content)
        
        return scores
    
    def _evaluate_structure(self, content: str, title: str) -> float:
        """评估结构组织"""
        score = 15.0
        
        if title:
            score += 3.0
        
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 4.0
        elif len(paragraphs) >= 2:
            score += 2.0
        
        if len(paragraphs) >= 3:
            first_p = paragraphs[0]
            last_p = paragraphs[-1]
            
            if len(first_p) > 50:
                score += 2.0
            if len(last_p) > 30:
                score += 1.0
        
        return min(score + random.uniform(-1, 2), 25.0)
    
    def _evaluate_content(self, content: str) -> float:
        """评估内容表达"""
        score = 18.0
        
        word_count = len(content.replace(' ', '').replace('\n', ''))
        if word_count >= 600:
            score += 6.0
        elif word_count >= 400:
            score += 4.0
        elif word_count >= 200:
            score += 2.0
        
        emotional_words = ['感动', '激动', '难忘', '珍惜', '热爱', '梦想', '希望', '努力']
        found_emotions = sum(1 for word in emotional_words if word in content)
        score += found_emotions * 0.8
        
        descriptive_words = ['美丽', '精彩', '温暖', '明亮', '深沉', '生动', '细腻', '真挚']
        found_desc = sum(1 for word in descriptive_words if word in content)
        score += found_desc * 0.5
        
        return min(score + random.uniform(-2, 3), 30.0)
    
    def _evaluate_language(self, content: str) -> float:
        """评估语言运用"""
        score = 15.0
        
        if '，' in content and '。' in content:
            score += 4.0
        
        if '！' in content or '？' in content:
            score += 2.0
        
        idioms = ['一心一意', '百折不挠', '坚持不懈', '勇往直前', '精益求精', '实事求是', '脚踏实地']
        found_idioms = sum(1 for idiom in idioms if idiom in content)
        score += found_idioms * 1.5
        
        rhetoricals = ['像', '仿佛', '犹如', '如同', '好似']
        found_rhetoricals = sum(1 for r in rhetoricals if r in content)
        score += found_rhetoricals * 1.0
        
        return min(score + random.uniform(-1, 2), 25.0)
    
    def _evaluate_creativity(self, content: str) -> float:
        """评估创新思维"""
        score = 5.0
        
        unique_patterns = [
            r'不仅.*而且.*',
            r'从.*中.*学会.*',
            r'让我.*懂得.*',
            r'如果.*就.*',
            r'虽然.*但是.*'
        ]
        
        for pattern in unique_patterns:
            if re.search(pattern, content):
                score += 0.8
        
        if len(content) > 500:
            score += 1.0
        
        return min(score + random.uniform(-1, 2), 10.0)
    
    def _evaluate_grammar(self, content: str) -> float:
        """评估语法规范"""
        score = 8.0
        
        errors = 0
        
        if content.count('，，') > 0:
            errors += 1
        if content.count('。。') > 0:
            errors += 1
        if content.count('！！') > 0:
            errors += 1
        
        score -= errors * 0.5
        
        if '的' in content and '地' in content and '得' in content:
            score += 1.5
        
        return max(min(score + random.uniform(-0.5, 1), 10.0), 0)
    
    def _generate_comments(self, content: str, scores: Dict) -> List:
        """生成批改评语"""
        comments = []
        
        if scores['structure'] >= 20:
            comments.append('文章结构清晰，层次分明，过渡自然。')
        elif scores['structure'] >= 15:
            comments.append('文章结构较清晰，可以进一步优化段落衔接。')
        else:
            comments.append('建议加强文章结构规划，注意段落之间的逻辑关系。')
        
        if scores['content'] >= 25:
            comments.append('内容充实，情感真挚，表达生动。')
        elif scores['content'] >= 20:
            comments.append('内容较充实，可以增加更多细节描写。')
        else:
            comments.append('建议丰富文章内容，增加具体事例和细节。')
        
        if scores['language'] >= 20:
            comments.append('语言流畅，用词恰当，表达准确。')
        elif scores['language'] >= 15:
            comments.append('语言较流畅，可以注意用词的多样性。')
        else:
            comments.append('建议加强语言表达训练，注意语句通顺。')
        
        if scores['creativity'] >= 8:
            comments.append('文章富有创意，观点新颖。')
        elif scores['creativity'] >= 5:
            comments.append('文章有一定的创意，可以进一步拓展思路。')
        else:
            comments.append('建议尝试从不同角度思考，增加文章的独特性。')
        
        if scores['grammar'] >= 8:
            comments.append('语法规范，标点正确。')
        else:
            comments.append('注意语法和标点的正确使用。')
        
        return comments
    
    def _generate_suggestions(self, content: str, scores: Dict) -> List:
        """生成改进建议"""
        suggestions = []
        
        weak_points = [k for k, v in scores.items() if v < self.CRITERIA[k]['max_score'] * 0.7]
        
        if 'structure' in weak_points:
            suggestions.append('可以先列出提纲，规划好文章结构再写作。')
            suggestions.append('注意开头点题、中间展开、结尾升华的写作思路。')
        
        if 'content' in weak_points:
            suggestions.append('多积累素材，用具体事例支撑观点。')
            suggestions.append('加入细节描写，让文章更生动。')
        
        if 'language' in weak_points:
            suggestions.append('多读优秀范文，学习优美表达。')
            suggestions.append('注意词汇的积累和运用。')
        
        if 'creativity' in weak_points:
            suggestions.append('尝试用不同的表达方式阐述观点。')
            suggestions.append('从生活中寻找独特的视角。')
        
        if 'grammar' in weak_points:
            suggestions.append('写完后通读检查，修正语法错误。')
            suggestions.append('注意标点符号的正确使用。')
        
        if not suggestions:
            suggestions.append('继续保持，期待你更精彩的作品！')
        
        return suggestions
    
    def _extract_keywords(self, content: str) -> List:
        """提取关键词"""
        keywords = []
        
        common_nouns = ['生活', '学习', '成长', '梦想', '努力', '坚持', '友谊', '亲情', '时间', '青春']
        for noun in common_nouns:
            if noun in content:
                keywords.append({'word': noun, 'frequency': content.count(noun), 'importance': 'high'})
        
        if len(keywords) < 3:
            additional_words = ['奋斗', '希望', '成功', '挑战', '收获', '感悟']
            for word in additional_words:
                if word in content and len(keywords) < 5:
                    keywords.append({'word': word, 'frequency': content.count(word), 'importance': 'medium'})
        
        return keywords[:5]
    
    def _determine_grade_level(self, total_score: float) -> str:
        """确定等级"""
        if total_score >= 90:
            return '优秀'
        elif total_score >= 80:
            return '良好'
        elif total_score >= 70:
            return '中等'
        elif total_score >= 60:
            return '及格'
        else:
            return '需改进'
    
    def _save_grading(self, grading_id, user_id, title, content, word_count, subject,
                      total_score, scores, comments, suggestions, grade_level):
        """保存批改记录"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO composition_gradings 
            (grading_id, user_id, title, content, word_count, subject, total_score,
             structure_score, content_score, language_score, creativity_score, grammar_score,
             comments, suggestions, grade_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            grading_id, user_id, title, content, word_count, subject, total_score,
            scores['structure'], scores['content'], scores['language'], 
            scores['creativity'], scores['grammar'],
            json.dumps(comments, ensure_ascii=False),
            json.dumps(suggestions, ensure_ascii=False),
            grade_level
        ))
        
        conn.commit()
        conn.close()
    
    def _save_keywords(self, grading_id, keywords):
        """保存关键词"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        for kw in keywords:
            cursor.execute('''
                INSERT INTO composition_keywords (grading_id, keyword, frequency, importance)
                VALUES (?, ?, ?, ?)
            ''', (grading_id, kw['word'], kw['frequency'], kw['importance']))
        
        conn.commit()
        conn.close()
    
    def get_grading_record(self, grading_id: str) -> Optional[Dict]:
        """获取批改记录"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM composition_gradings WHERE grading_id = ?
        ''', (grading_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'grading_id': row[1],
                'user_id': row[2],
                'title': row[3],
                'content': row[4],
                'word_count': row[5],
                'subject': row[6],
                'total_score': row[7],
                'scores': {
                    'structure': row[8],
                    'content': row[9],
                    'language': row[10],
                    'creativity': row[11],
                    'grammar': row[12]
                },
                'comments': json.loads(row[13]) if row[13] else [],
                'suggestions': json.loads(row[14]) if row[14] else [],
                'grade_level': row[15],
                'created_at': row[16]
            }
        
        return None
    
    def get_user_grading_history(self, user_id: str, limit: int = 10) -> List:
        """获取用户批改历史"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT grading_id, title, total_score, grade_level, created_at 
            FROM composition_gradings 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'grading_id': row[0],
            'title': row[1],
            'total_score': row[2],
            'grade_level': row[3],
            'created_at': row[4]
        } for row in rows]

ai_composition_grader = AICompositionGrader()