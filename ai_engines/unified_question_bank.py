#!/usr/bin/env python3
"""
MTSCOS Unified Question Bank - 统一题库管理系统
支持所有科目（语文、数学、英语、政治、日语、物理、化学、生物、历史、地理）
支持所有题型（单选、多选、判断、填空、简答、计算、听力、写作、阅读理解等）
支持AI自动延展题库内容
"""

import os
import sqlite3
import json
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_DB_DIR = os.path.join(BASE_DIR, 'split_databases')


def get_db_path() -> str:
    """获取题库数据库路径"""
    return os.path.join(SPLIT_DB_DIR, 'question.db')


def execute_sql(sql: str, params=None) -> bool:
    """执行SQL语句"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"SQL执行失败: {e}")
        return False


def fetch_all(sql: str, params=None) -> List[Dict]:
    """执行查询并返回所有结果"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        print(f"SQL查询失败: {e}")
        return []


def fetch_one(sql: str, params=None) -> Optional[Dict]:
    """执行查询并返回单条结果"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        conn.close()
        return dict(zip(columns, result)) if result else None
    except Exception as e:
        print(f"SQL查询失败: {e}")
        return None


SUBJECTS = {
    'chinese': {'name': '语文', 'icon': '📚', 'color': '#e74c3c'},
    'math': {'name': '数学', 'icon': '📐', 'color': '#3498db'},
    'english': {'name': '英语', 'icon': '🔤', 'color': '#27ae60'},
    'physics': {'name': '物理', 'icon': '⚡', 'color': '#9b59b6'},
    'chemistry': {'name': '化学', 'icon': '🧪', 'color': '#f39c12'},
    'biology': {'name': '生物', 'icon': '🧬', 'color': '#1abc9c'},
    'history': {'name': '历史', 'icon': '📜', 'color': '#8e44ad'},
    'geography': {'name': '地理', 'icon': '🌍', 'color': '#16a085'},
    'politics': {'name': '政治', 'icon': '⚖️', 'color': '#c0392b'},
    'japanese': {'name': '日语', 'icon': '🇯🇵', 'color': '#e67e22'},
}

QUESTION_TYPES = {
    'single_choice': {'name': '单选题', 'description': '从多个选项中选择一个正确答案'},
    'multiple_choice': {'name': '多选题', 'description': '从多个选项中选择多个正确答案'},
    'judge': {'name': '判断题', 'description': '判断题目陈述是否正确'},
    'fill_blank': {'name': '填空题', 'description': '填写题目中空缺的内容'},
    'short_answer': {'name': '简答题', 'description': '简要回答题目问题'},
    'essay': {'name': '论述题', 'description': '详细论述题目问题'},
    'calculation': {'name': '计算题', 'description': '进行数学或物理计算'},
    'listening': {'name': '听力题', 'description': '听录音后回答问题'},
    'reading': {'name': '阅读理解', 'description': '阅读文章后回答问题'},
    'writing': {'name': '写作题', 'description': '根据题目要求写作'},
    'dictation': {'name': '听写题', 'description': '听录音后写出内容'},
    'translation': {'name': '翻译题', 'description': '进行语言翻译'},
    'programming': {'name': '编程题', 'description': '编写程序代码'},
}

DIFFICULTY_LEVELS = {
    'easy': {'name': '基础题', 'description': '适合入门学习', 'score_weight': 1.0},
    'medium': {'name': '提高题', 'description': '适合巩固提升', 'score_weight': 1.5},
    'hard': {'name': '压轴题', 'description': '适合挑战突破', 'score_weight': 2.0},
}

QUESTION_TAGS = [
    '真题', '模拟题', '练习题', '专项训练', '单元测试', '期中', '期末', '中考', '高考',
    '时政', '热点', '易错', '高频', '重点', '难点', '解题模型', '举一反三', '拓展延伸'
]


class UnifiedQuestionBank:
    """统一题库管理系统"""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化数据库表结构"""
        # 通用题目表
        execute_sql('''
            CREATE TABLE IF NOT EXISTS unified_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_uuid TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                question_type TEXT NOT NULL,
                difficulty TEXT DEFAULT 'easy',
                content TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                analysis TEXT,
                explanation TEXT,
                tags TEXT,
                knowledge_points TEXT,
                chapter TEXT,
                section TEXT,
                grade TEXT,
                semester TEXT,
                source TEXT DEFAULT 'ai_generated',
                source_type TEXT DEFAULT 'auto',
                score REAL DEFAULT 5.0,
                usage_count INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                ai_extended INTEGER DEFAULT 0,
                extended_from TEXT,
                sync_status TEXT DEFAULT 'local',
                last_sync TEXT
            )
        ''')
        
        # 科目章节表
        execute_sql('''
            CREATE TABLE IF NOT EXISTS subject_chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                chapter_order INTEGER DEFAULT 0,
                grade TEXT,
                semester TEXT,
                total_questions INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject, chapter_name, grade, semester)
            )
        ''')
        
        # 题库统计表
        execute_sql('''
            CREATE TABLE IF NOT EXISTS question_bank_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date TEXT UNIQUE,
                total_questions INTEGER DEFAULT 0,
                by_subject TEXT,
                by_type TEXT,
                by_difficulty TEXT,
                ai_extended_count INTEGER DEFAULT 0,
                synced_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 题库同步日志表
        execute_sql('''
            CREATE TABLE IF NOT EXISTS question_sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_id TEXT UNIQUE NOT NULL,
                sync_type TEXT,
                source TEXT,
                subject TEXT,
                question_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AI延展记录表
        execute_sql('''
            CREATE TABLE IF NOT EXISTS ai_extension_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                source_question_uuid TEXT,
                subject TEXT,
                extension_type TEXT,
                generated_count INTEGER DEFAULT 0,
                keywords TEXT,
                difficulty TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def add_question(self, question_data: Dict) -> Dict:
        """添加题目"""
        question_uuid = question_data.get('question_uuid', f'q_{uuid.uuid4().hex[:12]}')
        
        execute_sql('''
            INSERT INTO unified_questions (
                question_uuid, subject, question_type, difficulty, content, options,
                correct_answer, analysis, explanation, tags, knowledge_points,
                chapter, section, grade, semester, source, source_type, score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_uuid,
            question_data.get('subject', ''),
            question_data.get('question_type', ''),
            question_data.get('difficulty', 'easy'),
            question_data.get('content', ''),
            json.dumps(question_data.get('options', [])),
            question_data.get('correct_answer', ''),
            question_data.get('analysis', ''),
            question_data.get('explanation', ''),
            json.dumps(question_data.get('tags', [])),
            json.dumps(question_data.get('knowledge_points', [])),
            question_data.get('chapter', ''),
            question_data.get('section', ''),
            question_data.get('grade', ''),
            question_data.get('semester', ''),
            question_data.get('source', 'ai_generated'),
            question_data.get('source_type', 'auto'),
            question_data.get('score', 5.0)
        ))
        
        return {'success': True, 'message': '题目添加成功', 'question_uuid': question_uuid}

    def get_questions(self, filters: Dict = None) -> Dict:
        """获取题目列表"""
        filters = filters or {}
        sql = "SELECT * FROM unified_questions WHERE is_active = 1"
        params = []
        
        if filters.get('subject'):
            sql += " AND subject = ?"
            params.append(filters['subject'])
        if filters.get('question_type'):
            sql += " AND question_type = ?"
            params.append(filters['question_type'])
        if filters.get('difficulty'):
            sql += " AND difficulty = ?"
            params.append(filters['difficulty'])
        if filters.get('grade'):
            sql += " AND grade = ?"
            params.append(filters['grade'])
        if filters.get('keyword'):
            sql += " AND (content LIKE ? OR tags LIKE ?)"
            params.extend([f'%{filters["keyword"]}%', f'%{filters["keyword"]}%'])
        
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        offset = (page - 1) * page_size
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        questions = fetch_all(sql, params)
        
        count_sql = "SELECT COUNT(*) as total FROM unified_questions WHERE is_active = 1"
        if filters.get('subject'):
            count_sql += " AND subject = ?"
        if filters.get('question_type'):
            count_sql += " AND question_type = ?"
        if filters.get('difficulty'):
            count_sql += " AND difficulty = ?"
        if filters.get('grade'):
            count_sql += " AND grade = ?"
        total = fetch_one(count_sql, params[:-2])['total'] if params else fetch_one(count_sql)['total']
        
        return {'success': True, 'data': questions, 'total': total, 'page': page, 'page_size': page_size}

    def get_question_by_uuid(self, question_uuid: str) -> Dict:
        """根据UUID获取题目"""
        question = fetch_one("SELECT * FROM unified_questions WHERE question_uuid = ?", (question_uuid,))
        if not question:
            return {'success': False, 'error': '题目不存在'}
        
        if question.get('options'):
            question['options'] = json.loads(question['options'])
        if question.get('tags'):
            question['tags'] = json.loads(question['tags'])
        if question.get('knowledge_points'):
            question['knowledge_points'] = json.loads(question['knowledge_points'])
        
        return {'success': True, 'data': question}

    def update_question(self, question_uuid: str, updates: Dict) -> Dict:
        """更新题目"""
        update_fields = []
        params = []
        
        if 'content' in updates:
            update_fields.append('content = ?')
            params.append(updates['content'])
        if 'options' in updates:
            update_fields.append('options = ?')
            params.append(json.dumps(updates['options']))
        if 'correct_answer' in updates:
            update_fields.append('correct_answer = ?')
            params.append(updates['correct_answer'])
        if 'analysis' in updates:
            update_fields.append('analysis = ?')
            params.append(updates['analysis'])
        if 'explanation' in updates:
            update_fields.append('explanation = ?')
            params.append(updates['explanation'])
        if 'tags' in updates:
            update_fields.append('tags = ?')
            params.append(json.dumps(updates['tags']))
        if 'knowledge_points' in updates:
            update_fields.append('knowledge_points = ?')
            params.append(json.dumps(updates['knowledge_points']))
        if 'difficulty' in updates:
            update_fields.append('difficulty = ?')
            params.append(updates['difficulty'])
        if 'score' in updates:
            update_fields.append('score = ?')
            params.append(updates['score'])
        
        params.append(question_uuid)
        sql = f"UPDATE unified_questions SET {', '.join(update_fields)} WHERE question_uuid = ?"
        execute_sql(sql, params)
        
        return {'success': True, 'message': '题目更新成功'}

    def delete_question(self, question_uuid: str) -> Dict:
        """删除题目（软删除）"""
        execute_sql("UPDATE unified_questions SET is_active = 0 WHERE question_uuid = ?", (question_uuid,))
        return {'success': True, 'message': '题目已禁用'}

    def ai_extend_question(self, source_uuid: str, extension_type: str = 'similar', count: int = 5) -> Dict:
        """AI自动延展题目"""
        source_question = self.get_question_by_uuid(source_uuid)
        if not source_question['success']:
            return source_question
        
        source_data = source_question['data']
        subject = source_data['subject']
        question_type = source_data['question_type']
        difficulty = source_data['difficulty']
        knowledge_points = source_data.get('knowledge_points', [])
        
        generated = []
        for i in range(count):
            new_question = self._generate_extended_question(source_data, extension_type, i)
            if new_question:
                result = self.add_question(new_question)
                if result['success']:
                    generated.append(result['question_uuid'])
                    execute_sql('''
                        INSERT INTO ai_extension_records (record_id, source_question_uuid, subject, extension_type, keywords)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (f'ext_{uuid.uuid4().hex[:8]}', source_uuid, subject, extension_type, json.dumps(knowledge_points)))
        
        return {
            'success': True,
            'message': f'AI延展成功，生成{len(generated)}道新题目',
            'generated_count': len(generated),
            'generated_uuids': generated,
            'source_uuid': source_uuid,
            'extension_type': extension_type
        }

    def _generate_extended_question(self, source: Dict, extension_type: str, index: int) -> Optional[Dict]:
        """生成延展题目"""
        try:
            subject = source['subject']
            question_type = source['question_type']
            difficulty = source['difficulty']
            
            if subject == 'math':
                return self._generate_math_extension(source, index)
            elif subject == 'chinese':
                return self._generate_chinese_extension(source, index)
            elif subject == 'english':
                return self._generate_english_extension(source, index)
            elif subject == 'physics':
                return self._generate_physics_extension(source, index)
            elif subject == 'chemistry':
                return self._generate_chemistry_extension(source, index)
            elif subject == 'politics':
                return self._generate_politics_extension(source, index)
            elif subject == 'japanese':
                return self._generate_japanese_extension(source, index)
            elif subject == 'history':
                return self._generate_history_extension(source, index)
            elif subject == 'geography':
                return self._generate_geography_extension(source, index)
            elif subject == 'biology':
                return self._generate_biology_extension(source, index)
            
            return None
        except Exception as e:
            print(f"生成延展题目失败: {e}")
            return None

    def _generate_math_extension(self, source: Dict, index: int) -> Dict:
        """生成数学延展题目"""
        knowledge = source.get('knowledge_points', [])
        num1 = random.randint(10, 100)
        num2 = random.randint(10, 100)
        operator = random.choice(['+', '-', '×', '÷'])
        
        if '方程' in str(knowledge):
            x = random.randint(1, 20)
            content = f"解方程：{num1}x + {num2} = {num1*x + num2}"
            answer = str(x)
        elif '几何' in str(knowledge):
            content = f"一个长方形的长为{num1}cm，宽为{num2}cm，求其面积和周长。"
            answer = f"面积：{num1*num2}cm²，周长：{2*(num1+num2)}cm"
        else:
            if operator == '+':
                answer = num1 + num2
            elif operator == '-':
                answer = num1 - num2 if num1 > num2 else num2 - num1
            elif operator == '×':
                answer = num1 * num2
            else:
                answer = num1 // num2 if num2 != 0 else 0
            content = f"计算：{num1} {operator} {num2} = ?"
            answer = str(answer)
        
        return {
            'subject': 'math',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answer,
            'analysis': f'考察{knowledge[0] if knowledge else "基本运算"}能力',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': knowledge,
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_chinese_extension(self, source: Dict, index: int) -> Dict:
        """生成语文延展题目"""
        words = ['美丽', '勇敢', '智慧', '勤奋', '团结', '善良', '诚实', '快乐']
        target_word = words[index % len(words)]
        
        content = f"请写出词语'{target_word}'的拼音并解释其含义。"
        pinyin_map = {
            '美丽': 'měi lì', '勇敢': 'yǒng gǎn', '智慧': 'zhì huì',
            '勤奋': 'qín fèn', '团结': 'tuán jié', '善良': 'shàn liáng',
            '诚实': 'chéng shí', '快乐': 'kuài lè'
        }
        
        return {
            'subject': 'chinese',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': f"{pinyin_map[target_word]} - 形容{target_word}的含义",
            'analysis': '考察词语听写和理解能力',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': ['词语听写', '词语理解'],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_english_extension(self, source: Dict, index: int) -> Dict:
        """生成英语延展题目"""
        words = ['beautiful', 'brave', 'intelligent', 'hardworking', 'united', 'kind', 'honest', 'happy']
        target_word = words[index % len(words)]
        
        content = f"请翻译英语单词 '{target_word}' 为中文，并写出其词性。"
        translations = {
            'beautiful': '美丽的 (形容词)', 'brave': '勇敢的 (形容词)',
            'intelligent': '聪明的 (形容词)', 'hardworking': '勤奋的 (形容词)',
            'united': '团结的 (形容词)', 'kind': '善良的 (形容词)',
            'honest': '诚实的 (形容词)', 'happy': '快乐的 (形容词)'
        }
        
        return {
            'subject': 'english',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': translations[target_word],
            'analysis': '考察英语词汇翻译能力',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': ['词汇翻译', '词性'],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_physics_extension(self, source: Dict, index: int) -> Dict:
        """生成物理延展题目"""
        topics = ['速度计算', '力的平衡', '功的计算', '能量守恒']
        topic = topics[index % len(topics)]
        
        if topic == '速度计算':
            distance = random.randint(100, 1000)
            time = random.randint(10, 100)
            content = f"一辆汽车行驶了{distance}米，用时{time}秒，求其平均速度。"
            answer = f"{distance/time:.2f} m/s"
        else:
            content = f"请简述{topic}的基本原理。"
            answer = f"{topic}的核心原理说明"
        
        return {
            'subject': 'physics',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answer,
            'analysis': f'考察{topic}知识点',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': [topic],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_chemistry_extension(self, source: Dict, index: int) -> Dict:
        """生成化学延展题目"""
        elements = ['H', 'O', 'C', 'N', 'Na', 'Cl', 'Fe', 'Cu']
        element = elements[index % len(elements)]
        
        content = f"请写出元素 '{element}' 的中文名称、原子序数和常见化合价。"
        element_info = {
            'H': '氢，原子序数1，化合价+1', 'O': '氧，原子序数8，化合价-2',
            'C': '碳，原子序数6，化合价+2、+4', 'N': '氮，原子序数7，化合价-3、+5',
            'Na': '钠，原子序数11，化合价+1', 'Cl': '氯，原子序数17，化合价-1',
            'Fe': '铁，原子序数26，化合价+2、+3', 'Cu': '铜，原子序数29，化合价+1、+2'
        }
        
        return {
            'subject': 'chemistry',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': element_info[element],
            'analysis': '考察化学元素基础知识',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': ['元素周期表', '化合价'],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_politics_extension(self, source: Dict, index: int) -> Dict:
        """生成政治延展题目"""
        topics = ['社会主义核心价值观', '中国梦', '依法治国', '生态文明']
        topic = topics[index % len(topics)]
        
        content = f"请简述{topic}的基本内涵。"
        answers = {
            '社会主义核心价值观': '富强、民主、文明、和谐，自由、平等、公正、法治，爱国、敬业、诚信、友善',
            '中国梦': '实现中华民族伟大复兴，就是中华民族近代以来最伟大梦想',
            '依法治国': '依照宪法和法律治理国家，是党领导人民治理国家的基本方略',
            '生态文明': '人类遵循人、自然、社会和谐发展这一客观规律而取得的物质与精神成果的总和'
        }
        
        return {
            'subject': 'politics',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answers[topic],
            'analysis': f'考察{topic}相关知识',
            'tags': ['AI延展', '时政', '专项训练'],
            'knowledge_points': [topic],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_japanese_extension(self, source: Dict, index: int) -> Dict:
        """生成日语延展题目"""
        words = ['こんにちは', 'ありがとう', 'すみません', 'はじめまして']
        target_word = words[index % len(words)]
        
        content = f"请翻译日语 '{target_word}' 为中文，并写出其使用场景。"
        translations = {
            'こんにちは': '你好，用于白天问候', 'ありがとう': '谢谢，表示感谢',
            'すみません': '对不起/打扰了，表示歉意或请求', 'はじめまして': '初次见面，用于自我介绍'
        }
        
        return {
            'subject': 'japanese',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': translations[target_word],
            'analysis': '考察日语日常用语翻译',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': ['日常用语', '翻译'],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_history_extension(self, source: Dict, index: int) -> Dict:
        """生成历史延展题目"""
        events = ['鸦片战争', '辛亥革命', '五四运动', '新中国成立']
        event = events[index % len(events)]
        
        content = f"请简述{event}的时间、背景和历史意义。"
        answers = {
            '鸦片战争': '1840-1842年，英国发动侵华战争，中国开始沦为半殖民地半封建社会',
            '辛亥革命': '1911年，孙中山领导的资产阶级民主革命，推翻了清王朝统治',
            '五四运动': '1919年，反帝反封建的爱国运动，标志着新民主主义革命的开始',
            '新中国成立': '1949年10月1日，中华人民共和国成立，中国人民站起来了'
        }
        
        return {
            'subject': 'history',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answers[event],
            'analysis': f'考察{event}相关历史知识',
            'tags': ['AI延展', '真题', '专项训练'],
            'knowledge_points': [event],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_geography_extension(self, source: Dict, index: int) -> Dict:
        """生成地理延展题目"""
        topics = ['地球自转', '气候类型', '板块运动', '河流特征']
        topic = topics[index % len(topics)]
        
        content = f"请简述{topic}的基本特征。"
        answers = {
            '地球自转': '地球绕地轴自西向东旋转，周期约24小时，产生昼夜交替',
            '气候类型': '包括热带、亚热带、温带、寒带等，受纬度、海陆、地形等因素影响',
            '板块运动': '地球岩石圈分为六大板块，板块运动导致火山、地震等地质现象',
            '河流特征': '包括流向、流量、流速、含沙量等，受地形、气候等因素影响'
        }
        
        return {
            'subject': 'geography',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answers[topic],
            'analysis': f'考察{topic}相关地理知识',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': [topic],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def _generate_biology_extension(self, source: Dict, index: int) -> Dict:
        """生成生物延展题目"""
        topics = ['细胞结构', '光合作用', '遗传规律', '生态系统']
        topic = topics[index % len(topics)]
        
        content = f"请简述{topic}的基本原理。"
        answers = {
            '细胞结构': '包括细胞膜、细胞质、细胞核等，植物细胞还有细胞壁和叶绿体',
            '光合作用': '绿色植物利用光能将二氧化碳和水转化为有机物并释放氧气',
            '遗传规律': '孟德尔遗传定律，包括分离定律和自由组合定律',
            '生态系统': '生物群落及其生存环境共同组成的统一整体，包括生产者、消费者、分解者'
        }
        
        return {
            'subject': 'biology',
            'question_type': source['question_type'],
            'difficulty': source['difficulty'],
            'content': content,
            'correct_answer': answers[topic],
            'analysis': f'考察{topic}相关生物知识',
            'tags': ['AI延展', '专项训练'],
            'knowledge_points': [topic],
            'grade': source.get('grade', ''),
            'source_type': 'ai_extended',
            'score': source.get('score', 5.0)
        }

    def batch_import_questions(self, questions: List[Dict]) -> Dict:
        """批量导入题目"""
        success_count = 0
        failed_count = 0
        
        for question in questions:
            result = self.add_question(question)
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success': True,
            'total': len(questions),
            'success_count': success_count,
            'failed_count': failed_count
        }

    def get_statistics(self) -> Dict:
        """获取题库统计"""
        total = fetch_one("SELECT COUNT(*) as count FROM unified_questions WHERE is_active = 1")['count']
        
        by_subject = fetch_all('''
            SELECT subject, COUNT(*) as count 
            FROM unified_questions 
            WHERE is_active = 1 
            GROUP BY subject
        ''')
        
        by_type = fetch_all('''
            SELECT question_type, COUNT(*) as count 
            FROM unified_questions 
            WHERE is_active = 1 
            GROUP BY question_type
        ''')
        
        by_difficulty = fetch_all('''
            SELECT difficulty, COUNT(*) as count 
            FROM unified_questions 
            WHERE is_active = 1 
            GROUP BY difficulty
        ''')
        
        ai_extended = fetch_one("SELECT COUNT(*) as count FROM unified_questions WHERE ai_extended = 1")['count']
        
        return {
            'success': True,
            'data': {
                'total_questions': total,
                'by_subject': by_subject,
                'by_type': by_type,
                'by_difficulty': by_difficulty,
                'ai_extended_count': ai_extended
            }
        }

    def sync_with_external(self, source: str, subject: str = None) -> Dict:
        """同步外部题库"""
        sync_id = f'sync_{uuid.uuid4().hex[:8]}'
        
        execute_sql('''
            INSERT INTO question_sync_logs (sync_id, sync_type, source, subject, started_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (sync_id, 'full', source, subject or 'all', datetime.now().isoformat()))
        
        try:
            success_count = 0
            
            if source == 'mock':
                mock_questions = self._generate_mock_sync_data(subject)
                for q in mock_questions:
                    result = self.add_question(q)
                    if result['success']:
                        success_count += 1
            
            execute_sql('''
                UPDATE question_sync_logs 
                SET status = ?, success_count = ?, completed_at = ? 
                WHERE sync_id = ?
            ''', ('completed', success_count, datetime.now().isoformat(), sync_id))
            
            return {
                'success': True,
                'message': f'同步完成，新增{success_count}道题目',
                'sync_id': sync_id,
                'success_count': success_count
            }
        except Exception as e:
            execute_sql('''
                UPDATE question_sync_logs 
                SET status = ?, error_message = ?, completed_at = ? 
                WHERE sync_id = ?
            ''', ('failed', str(e), datetime.now().isoformat(), sync_id))
            return {'success': False, 'error': str(e), 'sync_id': sync_id}

    def _generate_mock_sync_data(self, subject: str) -> List[Dict]:
        """生成模拟同步数据"""
        questions = []
        
        if subject == 'politics' or subject is None:
            politics_questions = [
                {
                    'subject': 'politics', 'question_type': 'single_choice', 'difficulty': 'easy',
                    'content': '社会主义核心价值观在国家层面的价值目标是：',
                    'options': ['富强、民主、文明、和谐', '自由、平等、公正、法治', '爱国、敬业、诚信、友善'],
                    'correct_answer': '富强、民主、文明、和谐',
                    'analysis': '社会主义核心价值观分为三个层面：国家层面、社会层面、个人层面',
                    'tags': ['真题', '时政'], 'knowledge_points': ['社会主义核心价值观'],
                    'grade': '初中', 'source': '同步数据', 'source_type': 'external'
                },
                {
                    'subject': 'politics', 'question_type': 'short_answer', 'difficulty': 'medium',
                    'content': '请简述中国梦的基本内涵。',
                    'correct_answer': '实现中华民族伟大复兴，就是中华民族近代以来最伟大梦想。具体表现是国家富强、民族振兴、人民幸福。',
                    'analysis': '考察中国梦的核心概念',
                    'tags': ['真题', '时政'], 'knowledge_points': ['中国梦'],
                    'grade': '高中', 'source': '同步数据', 'source_type': 'external'
                }
            ]
            questions.extend(politics_questions)
        
        if subject == 'english' or subject is None:
            english_questions = [
                {
                    'subject': 'english', 'question_type': 'single_choice', 'difficulty': 'easy',
                    'content': 'The book _____ on the desk belongs to my sister.',
                    'options': ['lying', 'lies', 'lay', 'lied'],
                    'correct_answer': 'lying',
                    'analysis': '考察现在分词作定语的用法',
                    'tags': ['真题', '语法'], 'knowledge_points': ['分词', '定语'],
                    'grade': '初中', 'source': '同步数据', 'source_type': 'external'
                },
                {
                    'subject': 'english', 'question_type': 'translation', 'difficulty': 'medium',
                    'content': 'Translate: 科技改变生活',
                    'correct_answer': 'Technology changes life.',
                    'analysis': '考察汉译英能力',
                    'tags': ['真题', '翻译'], 'knowledge_points': ['翻译', '科技词汇'],
                    'grade': '高中', 'source': '同步数据', 'source_type': 'external'
                }
            ]
            questions.extend(english_questions)
        
        if subject == 'math' or subject is None:
            math_questions = [
                {
                    'subject': 'math', 'question_type': 'calculation', 'difficulty': 'medium',
                    'content': '解方程：2x² - 5x + 2 = 0',
                    'correct_answer': 'x = 2 或 x = 0.5',
                    'analysis': '考察一元二次方程的解法',
                    'tags': ['真题', '压轴题'], 'knowledge_points': ['一元二次方程', '求根公式'],
                    'grade': '初中', 'source': '同步数据', 'source_type': 'external'
                },
                {
                    'subject': 'math', 'question_type': 'single_choice', 'difficulty': 'hard',
                    'content': '已知函数 f(x) = x³ - 3x，则 f(x) 的单调递增区间是：',
                    'options': ['(-∞, -1)和(1, +∞)', '(-1, 1)', '(-∞, +∞)', '(0, +∞)'],
                    'correct_answer': '(-∞, -1)和(1, +∞)',
                    'analysis': '考察导数与函数单调性',
                    'tags': ['真题', '压轴题'], 'knowledge_points': ['导数', '单调性'],
                    'grade': '高中', 'source': '同步数据', 'source_type': 'external'
                }
            ]
            questions.extend(math_questions)
        
        if subject == 'japanese' or subject is None:
            japanese_questions = [
                {
                    'subject': 'japanese', 'question_type': 'single_choice', 'difficulty': 'easy',
                    'content': '「日本」の読み方はどれですか？',
                    'options': ['にほん', 'にぽん', 'じほん', 'じぽん'],
                    'correct_answer': 'にほん',
                    'analysis': '考察日语单词发音',
                    'tags': ['真题', '发音'], 'knowledge_points': ['发音', '基础词汇'],
                    'grade': '初中', 'source': '同步数据', 'source_type': 'external'
                },
                {
                    'subject': 'japanese', 'question_type': 'translation', 'difficulty': 'medium',
                    'content': 'Translate: 我喜欢学习日语',
                    'correct_answer': '私は日本語を勉強するのが好きです',
                    'analysis': '考察日语句子翻译',
                    'tags': ['真题', '翻译'], 'knowledge_points': ['句子结构', '动词'],
                    'grade': '高中', 'source': '同步数据', 'source_type': 'external'
                }
            ]
            questions.extend(japanese_questions)
        
        return questions


unified_question_bank = UnifiedQuestionBank()


def initialize_bank_data():
    """初始化题库基础数据 - 所有科目完整题目内容"""
    bank = UnifiedQuestionBank()
    
    initial_questions = []
    
    # 政治题目
    politics_questions = [
        {'subject': 'politics', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '社会主义核心价值观在国家层面的价值目标是：',
         'options': ['富强、民主、文明、和谐', '自由、平等、公正、法治', '爱国、敬业、诚信、友善'],
         'correct_answer': '富强、民主、文明、和谐',
         'analysis': '社会主义核心价值观分为三个层面：国家层面、社会层面、个人层面',
         'tags': ['真题', '时政'], 'knowledge_points': ['社会主义核心价值观'], 'grade': '初中'},
        {'subject': 'politics', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '中国共产党的根本宗旨是：',
         'options': ['全心全意为人民服务', '实现共产主义', '建设社会主义'],
         'correct_answer': '全心全意为人民服务',
         'analysis': '党的根本宗旨是全心全意为人民服务',
         'tags': ['真题'], 'knowledge_points': ['党的宗旨'], 'grade': '初中'},
        {'subject': 'politics', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '请简述中国梦的基本内涵。',
         'correct_answer': '实现中华民族伟大复兴，就是中华民族近代以来最伟大梦想。具体表现是国家富强、民族振兴、人民幸福。',
         'analysis': '考察中国梦的核心概念',
         'tags': ['真题', '时政'], 'knowledge_points': ['中国梦'], 'grade': '高中'},
        {'subject': 'politics', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '什么是依法治国？',
         'correct_answer': '依法治国就是依照宪法和法律治理国家，是党领导人民治理国家的基本方略。',
         'analysis': '考察依法治国的基本概念',
         'tags': ['真题'], 'knowledge_points': ['依法治国'], 'grade': '高中'},
        {'subject': 'politics', 'question_type': 'essay', 'difficulty': 'hard',
         'content': '论述生态文明建设的重要性及其实现路径。',
         'correct_answer': '生态文明建设是关系中华民族永续发展的根本大计...',
         'analysis': '考察生态文明建设的综合知识',
         'tags': ['压轴题', '时政'], 'knowledge_points': ['生态文明'], 'grade': '高中'},
        {'subject': 'politics', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '我国的根本政治制度是：',
         'options': ['人民代表大会制度', '社会主义制度', '民主集中制'],
         'correct_answer': '人民代表大会制度',
         'analysis': '人民代表大会制度是我国的根本政治制度',
         'tags': ['真题'], 'knowledge_points': ['政治制度'], 'grade': '初中'},
        {'subject': 'politics', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '我国的国家性质是______。',
         'correct_answer': '人民民主专政的社会主义国家',
         'analysis': '考察我国国家性质',
         'tags': ['基础题'], 'knowledge_points': ['国家性质'], 'grade': '初中'},
        {'subject': 'politics', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '简述社会主义民主的特点。',
         'correct_answer': '社会主义民主是最广泛、最真实、最管用的民主。',
         'analysis': '考察社会主义民主的特征',
         'tags': ['提高题'], 'knowledge_points': ['社会主义民主'], 'grade': '高中'},
    ]
    initial_questions.extend(politics_questions)
    
    # 日语题目
    japanese_questions = [
        {'subject': 'japanese', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '「日本」の読み方はどれですか？',
         'options': ['にほん', 'にぽん', 'じほん', 'じぽん'],
         'correct_answer': 'にほん',
         'analysis': '考察日语单词发音',
         'tags': ['真题', '发音'], 'knowledge_points': ['发音', '基础词汇'], 'grade': '初中'},
        {'subject': 'japanese', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '「こんにちは」の意味はどれですか？',
         'options': ['你好', '谢谢', '对不起', '再见'],
         'correct_answer': '你好',
         'analysis': '考察日语日常用语',
         'tags': ['基础题'], 'knowledge_points': ['日常用语'], 'grade': '初中'},
        {'subject': 'japanese', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '「ありがとう」は______の意味です。',
         'correct_answer': '谢谢',
         'analysis': '考察日语词汇',
         'tags': ['基础题'], 'knowledge_points': ['基础词汇'], 'grade': '初中'},
        {'subject': 'japanese', 'question_type': 'translation', 'difficulty': 'medium',
         'content': 'Translate: 我喜欢学习日语',
         'correct_answer': '私は日本語を勉強するのが好きです',
         'analysis': '考察日语句子翻译',
         'tags': ['真题', '翻译'], 'knowledge_points': ['句子结构', '动词'], 'grade': '高中'},
        {'subject': 'japanese', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '「は」と「が」の違いを説明してください。',
         'correct_answer': '「は」は主題を示し、「が」は新情報を提示します。',
         'analysis': '考察助词用法',
         'tags': ['提高题'], 'knowledge_points': ['助词'], 'grade': '高中'},
        {'subject': 'japanese', 'question_type': 'writing', 'difficulty': 'hard',
         'content': '「私の趣味」について作文を書いてください。（300字程度）',
         'correct_answer': '私の趣味は読書です...',
         'analysis': '考察日语写作能力',
         'tags': ['压轴题'], 'knowledge_points': ['写作'], 'grade': '高中'},
        {'subject': 'japanese', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '「学校」の平仮名はどれですか？',
         'options': ['がっこう', 'がくこう', 'しょうがっこう', 'ちゅうがっこう'],
         'correct_answer': 'がっこう',
         'analysis': '考察日语单词拼写',
         'tags': ['基础题'], 'knowledge_points': ['平假名'], 'grade': '初中'},
        {'subject': 'japanese', 'question_type': 'fill_blank', 'difficulty': 'medium',
         'content': '明日は______があります。（試験）',
         'correct_answer': '試験',
         'analysis': '考察日语语法填空',
         'tags': ['提高题'], 'knowledge_points': ['语法'], 'grade': '高中'},
    ]
    initial_questions.extend(japanese_questions)
    
    # 英语题目
    english_questions = [
        {'subject': 'english', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': 'She _____ to school every day.',
         'options': ['go', 'goes', 'going', 'went'],
         'correct_answer': 'goes',
         'analysis': '考察一般现在时第三人称单数',
         'tags': ['基础题', '语法'], 'knowledge_points': ['时态'], 'grade': '初中'},
        {'subject': 'english', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': 'The book _____ on the desk belongs to my sister.',
         'options': ['lying', 'lies', 'lay', 'lied'],
         'correct_answer': 'lying',
         'analysis': '考察现在分词作定语的用法',
         'tags': ['真题', '语法'], 'knowledge_points': ['分词', '定语'], 'grade': '初中'},
        {'subject': 'english', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': 'He is good _____ math.',
         'correct_answer': 'at',
         'analysis': '考察固定搭配be good at',
         'tags': ['基础题'], 'knowledge_points': ['固定搭配'], 'grade': '初中'},
        {'subject': 'english', 'question_type': 'translation', 'difficulty': 'medium',
         'content': 'Translate: 科技改变生活',
         'correct_answer': 'Technology changes life.',
         'analysis': '考察汉译英能力',
         'tags': ['真题', '翻译'], 'knowledge_points': ['翻译', '科技词汇'], 'grade': '高中'},
        {'subject': 'english', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': 'What is the difference between "affect" and "effect"?',
         'correct_answer': '"Affect" is usually a verb meaning to influence, while "effect" is usually a noun meaning result.',
         'analysis': '考察近义词辨析',
         'tags': ['提高题'], 'knowledge_points': ['词汇辨析'], 'grade': '高中'},
        {'subject': 'english', 'question_type': 'reading', 'difficulty': 'hard',
         'content': 'Read the passage and answer: What is the main idea of the article?',
         'correct_answer': 'The main idea is about environmental protection.',
         'analysis': '考察阅读理解能力',
         'tags': ['压轴题', '真题'], 'knowledge_points': ['阅读理解'], 'grade': '高中'},
        {'subject': 'english', 'question_type': 'writing', 'difficulty': 'hard',
         'content': 'Write an essay about "My Dream" (200 words).',
         'correct_answer': 'Everyone has a dream...',
         'analysis': '考察英语写作能力',
         'tags': ['压轴题'], 'knowledge_points': ['写作'], 'grade': '高中'},
        {'subject': 'english', 'question_type': 'single_choice', 'difficulty': 'medium',
         'content': 'If I _____ rich, I would travel the world.',
         'options': ['am', 'was', 'were', 'be'],
         'correct_answer': 'were',
         'analysis': '考察虚拟语气',
         'tags': ['提高题', '语法'], 'knowledge_points': ['虚拟语气'], 'grade': '高中'},
    ]
    initial_questions.extend(english_questions)
    
    # 数学题目
    math_questions = [
        {'subject': 'math', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '2 + 3 = ?',
         'options': ['4', '5', '6', '7'],
         'correct_answer': '5',
         'analysis': '考察基本加法',
         'tags': ['基础题'], 'knowledge_points': ['基本运算'], 'grade': '小学'},
        {'subject': 'math', 'question_type': 'calculation', 'difficulty': 'easy',
         'content': '计算：25 × 4 = ?',
         'correct_answer': '100',
         'analysis': '考察基本乘法',
         'tags': ['基础题'], 'knowledge_points': ['乘法'], 'grade': '小学'},
        {'subject': 'math', 'question_type': 'calculation', 'difficulty': 'medium',
         'content': '解方程：2x² - 5x + 2 = 0',
         'correct_answer': 'x = 2 或 x = 0.5',
         'analysis': '考察一元二次方程的解法',
         'tags': ['真题', '压轴题'], 'knowledge_points': ['一元二次方程', '求根公式'], 'grade': '初中'},
        {'subject': 'math', 'question_type': 'single_choice', 'difficulty': 'hard',
         'content': '已知函数 f(x) = x³ - 3x，则 f(x) 的单调递增区间是：',
         'options': ['(-∞, -1)和(1, +∞)', '(-1, 1)', '(-∞, +∞)', '(0, +∞)'],
         'correct_answer': '(-∞, -1)和(1, +∞)',
         'analysis': '考察导数与函数单调性',
         'tags': ['真题', '压轴题'], 'knowledge_points': ['导数', '单调性'], 'grade': '高中'},
        {'subject': 'math', 'question_type': 'fill_blank', 'difficulty': 'medium',
         'content': '若 log₂(x) = 3，则 x = ______',
         'correct_answer': '8',
         'analysis': '考察对数运算',
         'tags': ['提高题'], 'knowledge_points': ['对数'], 'grade': '高中'},
        {'subject': 'math', 'question_type': 'calculation', 'difficulty': 'hard',
         'content': '求函数 f(x) = x⁴ - 4x³ + 6x² - 4x + 1 的极值。',
         'correct_answer': '极小值为0，无极大值',
         'analysis': '考察导数求极值',
         'tags': ['压轴题'], 'knowledge_points': ['导数', '极值'], 'grade': '高中'},
        {'subject': 'math', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '简述等差数列的通项公式。',
         'correct_answer': 'aₙ = a₁ + (n-1)d，其中a₁为首项，d为公差',
         'analysis': '考察等差数列知识',
         'tags': ['提高题'], 'knowledge_points': ['等差数列'], 'grade': '高中'},
        {'subject': 'math', 'question_type': 'single_choice', 'difficulty': 'medium',
         'content': '在三角形ABC中，若a=3, b=4, C=90°，则c等于：',
         'options': ['5', '6', '7', '12'],
         'correct_answer': '5',
         'analysis': '考察勾股定理',
         'tags': ['真题'], 'knowledge_points': ['勾股定理'], 'grade': '初中'},
    ]
    initial_questions.extend(math_questions)
    
    # 语文题目
    chinese_questions = [
        {'subject': 'chinese', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '下列词语中，书写正确的是：',
         'options': ['安祥', '安详', '安祥', '安享'],
         'correct_answer': '安详',
         'analysis': '考察词语书写',
         'tags': ['基础题'], 'knowledge_points': ['词语书写'], 'grade': '初中'},
        {'subject': 'chinese', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '床前明月光，______。',
         'correct_answer': '疑是地上霜',
         'analysis': '考察古诗词背诵',
         'tags': ['基础题', '古诗词'], 'knowledge_points': ['古诗词'], 'grade': '小学'},
        {'subject': 'chinese', 'question_type': 'dictation', 'difficulty': 'easy',
         'content': '听写词语：美丽',
         'correct_answer': '美丽',
         'analysis': '考察词语听写',
         'tags': ['基础题', '听写'], 'knowledge_points': ['词语听写'], 'grade': '小学'},
        {'subject': 'chinese', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '解释成语"锲而不舍"的含义。',
         'correct_answer': '比喻有恒心，有毅力，坚持不懈。',
         'analysis': '考察成语理解',
         'tags': ['提高题', '成语'], 'knowledge_points': ['成语'], 'grade': '初中'},
        {'subject': 'chinese', 'question_type': 'reading', 'difficulty': 'hard',
         'content': '阅读《岳阳楼记》选段，分析"先天下之忧而忧，后天下之乐而乐"的思想内涵。',
         'correct_answer': '表达了作者忧国忧民的情怀和以天下为己任的责任感。',
         'analysis': '考察文言文阅读理解',
         'tags': ['压轴题', '真题'], 'knowledge_points': ['文言文', '阅读理解'], 'grade': '高中'},
        {'subject': 'chinese', 'question_type': 'writing', 'difficulty': 'hard',
         'content': '以"成长"为题写一篇作文（600字）。',
         'correct_answer': '成长是一段漫长的旅程...',
         'analysis': '考察写作能力',
         'tags': ['压轴题'], 'knowledge_points': ['写作'], 'grade': '高中'},
        {'subject': 'chinese', 'question_type': 'single_choice', 'difficulty': 'medium',
         'content': '"春风又绿江南岸"中"绿"字的词性是：',
         'options': ['名词', '动词', '形容词', '副词'],
         'correct_answer': '动词',
         'analysis': '考察词性辨析',
         'tags': ['提高题'], 'knowledge_points': ['词性'], 'grade': '初中'},
        {'subject': 'chinese', 'question_type': 'fill_blank', 'difficulty': 'medium',
         'content': '______，一览众山小。',
         'correct_answer': '会当凌绝顶',
         'analysis': '考察古诗词背诵',
         'tags': ['真题', '古诗词'], 'knowledge_points': ['古诗词'], 'grade': '初中'},
    ]
    initial_questions.extend(chinese_questions)
    
    # 物理题目
    physics_questions = [
        {'subject': 'physics', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '光在真空中的传播速度约为：',
         'options': ['3×10⁶ m/s', '3×10⁷ m/s', '3×10⁸ m/s', '3×10⁹ m/s'],
         'correct_answer': '3×10⁸ m/s',
         'analysis': '考察光速',
         'tags': ['基础题'], 'knowledge_points': ['光速'], 'grade': '初中'},
        {'subject': 'physics', 'question_type': 'calculation', 'difficulty': 'easy',
         'content': '一辆汽车以20m/s的速度行驶，5秒内行驶的距离是多少？',
         'correct_answer': '100米',
         'analysis': '考察匀速直线运动',
         'tags': ['基础题'], 'knowledge_points': ['速度'], 'grade': '初中'},
        {'subject': 'physics', 'question_type': 'calculation', 'difficulty': 'medium',
         'content': '一个质量为2kg的物体受到10N的力，求其加速度。',
         'correct_answer': '5 m/s²',
         'analysis': '考察牛顿第二定律',
         'tags': ['提高题'], 'knowledge_points': ['牛顿定律'], 'grade': '高中'},
        {'subject': 'physics', 'question_type': 'short_answer', 'difficulty': 'hard',
         'content': '简述能量守恒定律的内容。',
         'correct_answer': '能量既不会凭空产生，也不会凭空消失，它只会从一种形式转化为另一种形式，或者从一个物体转移到另一个物体，而能量的总量保持不变。',
         'analysis': '考察能量守恒定律',
         'tags': ['压轴题'], 'knowledge_points': ['能量守恒'], 'grade': '高中'},
        {'subject': 'physics', 'question_type': 'single_choice', 'difficulty': 'medium',
         'content': '下列现象中，属于光的折射的是：',
         'options': ['镜子成像', '水中筷子弯曲', '影子形成', '小孔成像'],
         'correct_answer': '水中筷子弯曲',
         'analysis': '考察光的折射',
         'tags': ['提高题'], 'knowledge_points': ['光的折射'], 'grade': '初中'},
        {'subject': 'physics', 'question_type': 'fill_blank', 'difficulty': 'medium',
         'content': '欧姆定律的表达式是______。',
         'correct_answer': 'U = IR',
         'analysis': '考察欧姆定律',
         'tags': ['真题'], 'knowledge_points': ['欧姆定律'], 'grade': '初中'},
    ]
    initial_questions.extend(physics_questions)
    
    # 化学题目
    chemistry_questions = [
        {'subject': 'chemistry', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '水的化学式是：',
         'options': ['H₂O', 'CO₂', 'NaCl', 'HCl'],
         'correct_answer': 'H₂O',
         'analysis': '考察水的化学式',
         'tags': ['基础题'], 'knowledge_points': ['化学式'], 'grade': '初中'},
        {'subject': 'chemistry', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '元素周期表中，原子序数等于______。',
         'correct_answer': '质子数',
         'analysis': '考察原子序数',
         'tags': ['基础题'], 'knowledge_points': ['元素周期表'], 'grade': '初中'},
        {'subject': 'chemistry', 'question_type': 'calculation', 'difficulty': 'medium',
         'content': '计算1mol水的质量（H=1, O=16）。',
         'correct_answer': '18g',
         'analysis': '考察摩尔质量',
         'tags': ['提高题'], 'knowledge_points': ['摩尔质量'], 'grade': '高中'},
        {'subject': 'chemistry', 'question_type': 'short_answer', 'difficulty': 'hard',
         'content': '简述化学反应速率的影响因素。',
         'correct_answer': '温度、浓度、压强、催化剂等',
         'analysis': '考察化学反应速率',
         'tags': ['压轴题'], 'knowledge_points': ['反应速率'], 'grade': '高中'},
        {'subject': 'chemistry', 'question_type': 'single_choice', 'difficulty': 'medium',
         'content': '下列物质中，属于电解质的是：',
         'options': ['蔗糖', '氯化钠', '酒精', '铜'],
         'correct_answer': '氯化钠',
         'analysis': '考察电解质概念',
         'tags': ['提高题'], 'knowledge_points': ['电解质'], 'grade': '高中'},
    ]
    initial_questions.extend(chemistry_questions)
    
    # 生物题目
    biology_questions = [
        {'subject': 'biology', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '细胞的基本结构不包括：',
         'options': ['细胞膜', '细胞质', '细胞核', '细胞液'],
         'correct_answer': '细胞液',
         'analysis': '考察细胞结构',
         'tags': ['基础题'], 'knowledge_points': ['细胞结构'], 'grade': '初中'},
        {'subject': 'biology', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '光合作用的场所是______。',
         'correct_answer': '叶绿体',
         'analysis': '考察光合作用',
         'tags': ['基础题'], 'knowledge_points': ['光合作用'], 'grade': '初中'},
        {'subject': 'biology', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '简述DNA的双螺旋结构。',
         'correct_answer': 'DNA由两条反向平行的脱氧核苷酸链组成，呈双螺旋结构。',
         'analysis': '考察DNA结构',
         'tags': ['提高题'], 'knowledge_points': ['DNA'], 'grade': '高中'},
        {'subject': 'biology', 'question_type': 'essay', 'difficulty': 'hard',
         'content': '论述生态系统的组成和功能。',
         'correct_answer': '生态系统由生物群落和非生物环境组成...',
         'analysis': '考察生态系统',
         'tags': ['压轴题'], 'knowledge_points': ['生态系统'], 'grade': '高中'},
    ]
    initial_questions.extend(biology_questions)
    
    # 历史题目
    history_questions = [
        {'subject': 'history', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '中国近代史的开端是：',
         'options': ['鸦片战争', '辛亥革命', '五四运动', '新中国成立'],
         'correct_answer': '鸦片战争',
         'analysis': '考察中国近代史开端',
         'tags': ['真题'], 'knowledge_points': ['近代史'], 'grade': '初中'},
        {'subject': 'history', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '秦始皇统一六国的时间是______年。',
         'correct_answer': '公元前221',
         'analysis': '考察秦朝历史',
         'tags': ['基础题'], 'knowledge_points': ['秦朝'], 'grade': '初中'},
        {'subject': 'history', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '简述辛亥革命的历史意义。',
         'correct_answer': '推翻了清王朝统治，结束了两千多年的封建帝制，使民主共和观念深入人心。',
         'analysis': '考察辛亥革命',
         'tags': ['真题'], 'knowledge_points': ['辛亥革命'], 'grade': '高中'},
        {'subject': 'history', 'question_type': 'essay', 'difficulty': 'hard',
         'content': '论述改革开放的背景和意义。',
         'correct_answer': '改革开放是中国特色社会主义发展的重要阶段...',
         'analysis': '考察改革开放',
         'tags': ['压轴题', '时政'], 'knowledge_points': ['改革开放'], 'grade': '高中'},
    ]
    initial_questions.extend(history_questions)
    
    # 地理题目
    geography_questions = [
        {'subject': 'geography', 'question_type': 'single_choice', 'difficulty': 'easy',
         'content': '地球自转的方向是：',
         'options': ['自西向东', '自东向西', '自南向北', '自北向南'],
         'correct_answer': '自西向东',
         'analysis': '考察地球自转',
         'tags': ['基础题'], 'knowledge_points': ['地球自转'], 'grade': '初中'},
        {'subject': 'geography', 'question_type': 'fill_blank', 'difficulty': 'easy',
         'content': '世界上最大的洋是______。',
         'correct_answer': '太平洋',
         'analysis': '考察世界地理',
         'tags': ['基础题'], 'knowledge_points': ['大洋'], 'grade': '初中'},
        {'subject': 'geography', 'question_type': 'short_answer', 'difficulty': 'medium',
         'content': '简述季风气候的特点。',
         'correct_answer': '夏季高温多雨，冬季寒冷干燥，雨热同期。',
         'analysis': '考察气候类型',
         'tags': ['提高题'], 'knowledge_points': ['季风气候'], 'grade': '高中'},
        {'subject': 'geography', 'question_type': 'essay', 'difficulty': 'hard',
         'content': '分析我国地形地势对气候和河流的影响。',
         'correct_answer': '我国地势西高东低，呈三级阶梯分布...',
         'analysis': '考察中国地理',
         'tags': ['压轴题'], 'knowledge_points': ['地形地势'], 'grade': '高中'},
    ]
    initial_questions.extend(geography_questions)
    
    result = bank.batch_import_questions(initial_questions)
    print(f"初始化题库完成: {result['success_count']}道题目")


if __name__ == '__main__':
    initialize_bank_data()
    print("统一题库管理系统初始化完成！")