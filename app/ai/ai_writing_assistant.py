#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
import re
from datetime import datetime
from collections import defaultdict

class AIWritingAssistant:
    WRITING_TYPES = ['essay', 'report', 'summary', 'letter', 'email', 'story', 'poem', 'article', 'review',
    'description']
    TARGET_AUDIENCES = ['students', 'teachers', 'parents', 'general', 'experts', 'children']
    TONE_STYLES = ['formal', 'informal', 'academic', 'creative', 'professional', 'friendly', 'humorous', 'serious']
    GRAMMAR_RULES = [
        {'name': '主谓一致', 'pattern': r'\b(is|are|was|were|has|have)\b', 'level': 'basic'},
        {'name': '时态一致', 'pattern': r'\b(will|would|can|could|may|might|must)\b', 'level': 'basic'},
        {'name': '冠词使用', 'pattern': r'\b(a|an|the)\b', 'level': 'basic'},
        {'name': '介词搭配', 'pattern': r'\b(in|on|at|with|by|for|from|to)\b', 'level': 'intermediate'},
        {'name': '从句结构', 'pattern': r'\b(that|which|who|whom|whose)\b', 'level': 'advanced'},
        {'name': '平行结构', 'pattern': r'\b(and|or|but|not only)\b', 'level': 'advanced'}
    ]

    def __init__(self):
        self.writing_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
        self._init_writing_templates()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_writing.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS writing_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    user_id TEXT,
                    writing_type TEXT DEFAULT 'essay',
                    title TEXT,
                    content TEXT,
                    target_audience TEXT DEFAULT 'general',
                    tone TEXT DEFAULT 'formal',
                    word_count INTEGER DEFAULT 500,
                    status TEXT DEFAULT 'draft',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS writing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    content TEXT,
                    changes TEXT,
                    saved_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grammar_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    position_start INTEGER,
                    position_end INTEGER,
                    suggestion TEXT,
                    severity TEXT DEFAULT 'medium',
                    fixed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS writing_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL UNIQUE,
                    writing_type TEXT,
                    target_audience TEXT,
                    tone TEXT,
                    structure TEXT,
                    examples TEXT,
                    tips TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS writing_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    readability_score REAL DEFAULT 0.0,
                    word_count INTEGER DEFAULT 0,
                    sentence_count INTEGER DEFAULT 0,
                    avg_sentence_length REAL DEFAULT 0.0,
                    vocabulary_diversity REAL DEFAULT 0.0,
                    grammar_score REAL DEFAULT 0.0,
                    coherence_score REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"创建表失败: {e}")

    def _init_writing_templates(self):
        try:
            conn = sqlite3.connect('ai_writing.db')
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM writing_templates')
            if cursor.fetchone()[0] == 0:
                templates = [
                    {
                        'template_name': '议论文模板',
                        'writing_type': 'essay',
                        'target_audience': 'students',
                        'tone': 'academic',
                        'structure': json.dumps({
                            'introduction': '引出话题，提出论点',
                            'body': ['分论点1', '分论点2', '分论点3'],
                            'conclusion': '总结论点，升华主题'
                        }),
                        'examples': '科技进步对教育的影响',
                        'tips': '使用论据支撑论点，注意逻辑连贯'
                    },
                    {
                        'template_name': '报告模板',
                        'writing_type': 'report',
                        'target_audience': 'teachers',
                        'tone': 'professional',
                        'structure': json.dumps({
                            'title': '报告主题',
                            'summary': '内容摘要',
                            'methodology': '研究方法',
                            'results': '研究结果',
                            'conclusion': '结论与建议'
                        }),
                        'examples': '学生学习成绩分析报告',
                        'tips': '数据准确，分析深入，建议可行'
                    },
                    {
                        'template_name': '故事模板',
                        'writing_type': 'story',
                        'target_audience': 'children',
                        'tone': 'creative',
                        'structure': json.dumps({
                            'exposition': '人物和背景介绍',
                            'rising_action': '矛盾冲突出现',
                            'climax': '故事高潮',
                            'falling_action': '问题解决',
                            'resolution': '结局'
                        }),
                        'examples': '勇敢的小兔子',
                        'tips': '生动的人物描写，引人入胜的情节'
                    },
                    {
                        'template_name': '邮件模板',
                        'writing_type': 'email',
                        'target_audience': 'general',
                        'tone': 'friendly',
                        'structure': json.dumps({
                            'subject': '邮件主题',
                            'greeting': '问候语',
                            'body': '正文内容',
                            'closing': '结束语',
                            'signature': '签名'
                        }),
                        'examples': '家长会邀请邮件',
                        'tips': '简洁明了，礼貌得体'
                    }
                ]

                for template in templates:
                    cursor.execute('''
                        INSERT INTO writing_templates 
                        (template_name, writing_type, target_audience, tone, structure, examples, tips)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (template['template_name'], template['writing_type'], template['target_audience'],
                          template['tone'], template['structure'], template['examples'], template['tips']))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"初始化模板失败: {e}")

    def generate_content(self, title, writing_type='essay', target_audience='general', 
                        tone='formal', word_count=500, keywords=None):
        """生成写作内容"""
        task_id = hashlib.md5(f"{title}{writing_type}{datetime.now()}{random.random()}".encode()).hexdigest()[:16]
        
        structures = {
            'essay': ['引言', '正文第一段', '正文第二段', '正文第三段', '结论'],
            'report': ['摘要', '背景介绍', '研究方法', '结果分析', '结论与建议'],
            'summary': ['主要内容概述', '关键要点提取', '核心观点总结'],
            'letter': ['称呼', '开头问候', '正文内容', '结尾祝福', '落款'],
            'email': ['主题', '问候语', '正文', '结束语', '签名'],
            'story': ['开头', '发展', '高潮', '结局'],
            'poem': ['第一诗节', '第二诗节', '第三诗节', '第四诗节'],
            'article': ['标题', '导语', '正文', '结尾'],
            'review': ['引言', '正文评价', '优缺点分析', '总结建议'],
            'description': ['整体描述', '细节描写', '感受表达']
        }

        structure = structures.get(writing_type, structures['essay'])
        
        content_parts = []
        for part in structure:
            content_parts.append(f"## {part}\n\n")

        content = ''.join(content_parts)
        
        conn = sqlite3.connect('ai_writing.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO writing_tasks 
            (task_id, title, writing_type, target_audience, tone, word_count, content, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, title, writing_type, target_audience, tone, word_count, content, 'draft'))
        conn.commit()
        conn.close()

        analytics = self._analyze_content(content)
        
        return {
            'success': True,
            'task_id': task_id,
            'title': title,
            'writing_type': writing_type,
            'target_audience': target_audience,
            'tone': tone,
            'word_count': word_count,
            'content': content,
            'status': 'draft',
            'analytics': analytics,
            'created_at': datetime.now().isoformat()
        }

    def rewrite_content(self, content, target_tone='formal', improvements=None):
        """重写内容"""
        if improvements is None:
            improvements = ['grammar', 'vocabulary', 'style', 'clarity']
        
        rewritten = content
        
        if 'grammar' in improvements:
            errors = self._check_grammar(content)
            offset = 0
            for error in errors:
                if error.get('suggestion'):
                    start = error['position_start'] + offset
                    end = error['position_end'] + offset
                    if error['error_type'] == '连续重复':
                        rewritten = rewritten[:start] + rewritten[start:end][:1] + rewritten[end:]
                        offset -= 1
                    elif error['error_type'] == '缺少标点':
                        rewritten = rewritten[:end] + error['suggestion'] + rewritten[end:]
                        offset += 1
                    elif error['error_type'] == '标点滥用':
                        rewritten = rewritten[:start] + error['suggestion'] + rewritten[end:]
                        offset -= (end - start - 1)
                    else:
                        rewritten = rewritten[:start] + error['suggestion'] + rewritten[end:]
        
        if 'vocabulary' in improvements:
            vocabulary_map = {
                '很好': '非常出色',
                '很多': '大量',
                '重要': '至关重要',
                '说': '阐述',
                '想': '思考',
                '做': '执行',
                '看': '观察',
                '好': '优秀',
                '坏': '不佳',
                '大': '庞大'
            }
            for old, new in vocabulary_map.items():
                rewritten = rewritten.replace(old, new)
        
        if 'style' in improvements:
            if target_tone == 'formal':
                rewritten = rewritten.replace('你', '您').replace('我', '本人').replace('很', '非常')
            elif target_tone == 'informal':
                rewritten = rewritten.replace('您', '你').replace('非常', '很')
        
        if 'clarity' in improvements:
            rewritten = re.sub(r'的话', '', rewritten)
            rewritten = re.sub(r'其实', '', rewritten)
        
        analytics = self._analyze_content(rewritten)
        
        return {
            'success': True,
            'original_content': content,
            'rewritten_content': rewritten,
            'target_tone': target_tone,
            'improvements_applied': improvements,
            'analytics': analytics
        }

    def summarize_content(self, content, max_length=200):
        """总结内容"""
        sentences = re.split(r'[。！？；]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            summary = content[:max_length]
        else:
            key_sentences = sentences[:2] + sentences[-1:]
            summary = '。'.join(key_sentences)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
        
        return {
            'success': True,
            'original_length': len(content),
            'summary_length': len(summary),
            'summary': summary
        }

    def check_grammar(self, content):
        """检查语法"""
        errors = self._check_grammar(content)
        return {
            'success': True,
            'error_count': len(errors),
            'errors': errors
        }

    def _check_grammar(self, content):
        errors = []

        if len(content) < 5:
            return errors

        common_doubles = ['说说', '看看', '听听', '想想', '问问', '谢谢', '明明', '仅仅', '渐渐', '慢慢',
                          '刚刚', '常常', '偏偏', '悄悄', '暗暗', '轻轻', '重重', '冷冷', '热热',
                          '深深', '浅浅', '长长', '短短', '高高', '低低', '远远', '近近', '早早', '晚晚',
                          '好好', '坏坏', '多多', '少少', '大大', '小小', '快快', '紧紧', '松松']

        for i in range(len(content) - 1):
            if content[i] == content[i + 1] and '\u4e00' <= content[i] <= '\u9fa5':
                double_char = content[i:i+2]
                if double_char not in common_doubles:
                    if i == 0 or content[i-1] in '，。！？；、\s':
                        errors.append({
                            'error_type': '连续重复',
                            'error_message': f'发现连续重复的汉字 "{content[i]}"',
                            'position_start': i,
                            'position_end': i + 2,
                            'suggestion': f'{content[i]}',
                            'severity': 'medium'
                        })
                        break

        pattern = re.compile(r'([，。！？；、\s])([\u4e00-\u9fa5]{2,})([，。！？；、\s]*)\2')
        matches = pattern.findall(content)
        if matches:
            _, matched, _ = matches[0]
            pos = content.find(matched)
            errors.append({
                'error_type': '词语重复',
                'error_message': f'发现重复词语: "{matched}"',
                'position_start': pos,
                'position_end': pos + len(matched),
                'suggestion': '',
                'severity': 'low'
            })

        sentence_lengths = [len(s) for s in re.split(r'[。！？；]', content) if s.strip()]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if avg_length > 50:
                errors.append({
                    'error_type': '句子过长',
                    'error_message': f'平均句子长度{avg_length:.1f}字，建议拆分长句',
                    'position_start': 0,
                    'position_end': min(50, len(content)),
                    'suggestion': '',
                    'severity': 'medium'
                })

        if not content.strip().endswith(('。', '！', '？', '；', '"', "'")):
            errors.append({
                'error_type': '缺少标点',
                'error_message': '段落末尾缺少句号或其他结束标点',
                'position_start': len(content) - 1,
                'position_end': len(content),
                'suggestion': '。',
                'severity': 'low'
            })

        punctuation_patterns = re.findall(r'([，。！？；、]){3,}', content)
        if punctuation_patterns:
            errors.append({
                'error_type': '标点滥用',
                'error_message': '发现连续使用多个相同标点',
                'position_start': content.find(punctuation_patterns[0] * 3),
                'position_end': content.find(punctuation_patterns[0] * 3) + 3,
                'suggestion': punctuation_patterns[0],
                'severity': 'low'
            })

        if content.count('的') > len(content) * 0.1:
            errors.append({
                'error_type': '助词过多',
                'error_message': f'"的"字使用频率过高({content.count("的")}次)，建议简化表达',
                'position_start': content.find('的'),
                'position_end': content.find('的') + 1,
                'suggestion': '',
                'severity': 'low'
            })

        return errors

    def _analyze_content(self, content):
        sentences = [s.strip() for s in re.split(r'[。！？；]', content) if s.strip()]
        words = re.findall(r'[\u4e00-\u9fa5]+', content)
        
        word_count = len(''.join(content.split()))
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        
        grammar_score = 100 - (len(self._check_grammar(content)) * 10)
        grammar_score = max(0, min(100, grammar_score))
        
        readability_score = 100 - (avg_sentence_length * 1.5)
        readability_score = max(0, min(100, readability_score))
        
        return {
            'readability_score': round(readability_score, 2),
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'vocabulary_diversity': round(vocabulary_diversity, 2),
            'grammar_score': round(grammar_score, 2),
            'coherence_score': round(85.0, 2)
        }

    def get_templates(self, writing_type=None):
        """获取写作模板"""
        conn = sqlite3.connect('ai_writing.db')
        cursor = conn.cursor()
        
        if writing_type:
            cursor.execute('SELECT * FROM writing_templates WHERE writing_type = ?', (writing_type,))
        else:
            cursor.execute('SELECT * FROM writing_templates')
        
        rows = cursor.fetchall()
        conn.close()
        
        templates = []
        for row in rows:
            templates.append({
                'id': row[0],
                'template_name': row[1],
                'writing_type': row[2],
                'target_audience': row[3],
                'tone': row[4],
                'structure': json.loads(row[5]) if row[5] else {},
                'examples': row[6],
                'tips': row[7]
            })
        
        return {
            'success': True,
            'templates': templates
        }

    def save_task(self, task_id, content, status='draft'):
        """保存写作任务"""
        conn = sqlite3.connect('ai_writing.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT content FROM writing_tasks WHERE task_id = ?', (task_id,))
        old_content = cursor.fetchone()
        
        if old_content:
            cursor.execute('SELECT MAX(version) FROM writing_history WHERE task_id = ?', (task_id,))
            max_version = cursor.fetchone()[0] or 0
            
            changes = f"版本 {max_version + 1}"
            cursor.execute('''
                INSERT INTO writing_history (task_id, version, content, changes)
                VALUES (?, ?, ?, ?)
            ''', (task_id, max_version + 1, old_content[0], changes))
        
        cursor.execute('''
            UPDATE writing_tasks 
            SET content = ?, status = ?, updated_at = ?
            WHERE task_id = ?
        ''', (content, status, datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'task_id': task_id}

    def get_task(self, task_id):
        """获取写作任务"""
        conn = sqlite3.connect('ai_writing.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM writing_tasks WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'success': True,
                'task': {
                    'task_id': row[1],
                    'user_id': row[2],
                    'writing_type': row[3],
                    'title': row[4],
                    'content': row[5],
                    'target_audience': row[6],
                    'tone': row[7],
                    'word_count': row[8],
                    'status': row[9],
                    'created_at': row[10],
                    'updated_at': row[11]
                }
            }
        return {'success': False, 'error': '任务不存在'}

    def list_tasks(self, user_id=None, limit=10):
        """列出写作任务"""
        conn = sqlite3.connect('ai_writing.db')
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('SELECT * FROM writing_tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?', (user_id,
            limit))
        else:
            cursor.execute('SELECT * FROM writing_tasks ORDER BY created_at DESC LIMIT ?', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                'task_id': row[1],
                'user_id': row[2],
                'writing_type': row[3],
                'title': row[4],
                'status': row[9],
                'created_at': row[10],
                'updated_at': row[11]
            })
        
        return {'success': True, 'tasks': tasks}

ai_writing_assistant = AIWritingAssistant()