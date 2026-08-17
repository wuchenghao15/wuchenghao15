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

class AIHomeworkGrading:
    QUESTION_TYPES = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer', 'essay']
    GRADING_STATUS = ['pending', 'grading', 'completed', 'reviewed']
    SCORE_LEVELS = ['excellent', 'good', 'fair', 'poor']
    
    def __init__(self):
        self.grading_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
        self._init_grading_rules()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_homework_grading.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assignment_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    subject TEXT,
                    grade_level TEXT,
                    total_score INTEGER DEFAULT 100,
                    deadline TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT NOT NULL UNIQUE,
                    assignment_id TEXT NOT NULL,
                    question_type TEXT DEFAULT 'single_choice',
                    content TEXT NOT NULL,
                    options TEXT,
                    correct_answer TEXT,
                    score INTEGER DEFAULT 10,
                    grading_rule TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT NOT NULL UNIQUE,
                    assignment_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    answers TEXT,
                    status TEXT DEFAULT 'submitted',
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    graded_at TEXT,
                    total_score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 100,
                    metadata TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grading_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id TEXT NOT NULL UNIQUE,
                    submission_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_type TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 10,
                    grading_detail TEXT,
                    feedback TEXT,
                    grading_time REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grading_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    question_type TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    rule_description TEXT,
                    rule_logic TEXT,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grading_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assignment_id TEXT NOT NULL,
                    submission_count INTEGER DEFAULT 0,
                    avg_score REAL DEFAULT 0.0,
                    score_distribution TEXT,
                    common_errors TEXT,
                    difficult_questions TEXT,
                    grading_time_avg REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"创建表失败: {e}")

    def _init_grading_rules(self):
        try:
            conn = sqlite3.connect('ai_homework_grading.db')
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM grading_rules')
            if cursor.fetchone()[0] == 0:
                rules = [
                    {
                        'rule_id': 'sc_exact_match',
                        'question_type': 'single_choice',
                        'rule_name': '单选题精确匹配',
                        'rule_description': '用户答案与正确答案完全一致得满分',
                        'rule_logic': json.dumps({'type': 'exact_match', 'case_insensitive': True}),
                        'weight': 1.0
                    },
                    {
                        'rule_id': 'mc_exact_match',
                        'question_type': 'multiple_choice',
                        'rule_name': '多选题精确匹配',
                        'rule_description': '用户答案与正确答案完全一致得满分，部分正确按比例得分',
                        'rule_logic': json.dumps({'type': 'partial_match', 'score_method': 'proportion'}),
                        'weight': 1.0
                    },
                    {
                        'rule_id': 'tf_exact_match',
                        'question_type': 'true_false',
                        'rule_name': '判断题精确匹配',
                        'rule_description': '用户答案与正确答案完全一致得满分',
                        'rule_logic': json.dumps({'type': 'exact_match', 'case_insensitive': True}),
                        'weight': 1.0
                    },
                    {
                        'rule_id': 'fb_keyword',
                        'question_type': 'fill_blank',
                        'rule_name': '填空题关键词匹配',
                        'rule_description': '根据关键词匹配程度评分，支持同义词和近义词',
                        'rule_logic': json.dumps({'type': 'keyword_match', 'exact_weight': 1.0, 'synonym_weight': 0.7}),
                        'weight': 1.0
                    },
                    {
                        'rule_id': 'sa_semantic',
                        'question_type': 'short_answer',
                        'rule_name': '简答题语义分析',
                        'rule_description': '基于关键词匹配和语义相似度进行评分',
                        'rule_logic': json.dumps({'type': 'semantic_analysis', 'keyword_weight': 0.5,
                        'structure_weight': 0.3, 'language_weight': 0.2}),
                        'weight': 1.0
                    },
                    {
                        'rule_id': 'essay_multidimensional',
                        'question_type': 'essay',
                        'rule_name': '作文多维度评分',
                        'rule_description': '从内容、结构、语言表达、创新性四个维度评分',
                        'rule_logic': json.dumps({'dimensions': ['content', 'structure', 'language', 'creativity'],
                        'weights': [0.35, 0.25, 0.25, 0.15]}),
                        'weight': 1.0
                    }
                ]

                for rule in rules:
                    cursor.execute('''
                        INSERT INTO grading_rules 
                        (rule_id, question_type, rule_name, rule_description, rule_logic, weight)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (rule['rule_id'], rule['question_type'], rule['rule_name'], 
                          rule['rule_description'], rule['rule_logic'], rule['weight']))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"初始化评分规则失败: {e}")

    def create_assignment(self, title, subject, grade_level, total_score=100, deadline=None, questions=None):
        """创建作业"""
        assignment_id = hashlib.md5(f"{title}{subject}{datetime.now()}{random.random()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO homework_assignments 
            (assignment_id, title, subject, grade_level, total_score, deadline, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (assignment_id, title, subject, grade_level, total_score, deadline, 'active'))
        
        if questions:
            for idx, q in enumerate(questions):
                question_id = f"{assignment_id}_q{idx+1}"
                cursor.execute('''
                    INSERT INTO homework_questions 
                    (question_id, assignment_id, question_type, content, options, correct_answer, score, grading_rule)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (question_id, assignment_id, q.get('type', 'single_choice'), 
                      q.get('content', ''), json.dumps(q.get('options', [])), 
                      q.get('correct_answer', ''), q.get('score', 10), q.get('grading_rule', '')))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'assignment_id': assignment_id,
            'title': title,
            'subject': subject,
            'grade_level': grade_level,
            'total_score': total_score,
            'question_count': len(questions) if questions else 0,
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }

    def submit_homework(self, assignment_id, user_id, answers):
        """提交作业"""
        submission_id = hashlib.md5(f"{assignment_id}{user_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT total_score FROM homework_assignments WHERE assignment_id = ?', (assignment_id,))
        row = cursor.fetchone()
        max_score = row[0] if row else 100
        
        cursor.execute('''
            INSERT INTO homework_submissions 
            (submission_id, assignment_id, user_id, answers, status, max_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (submission_id, assignment_id, user_id, json.dumps(answers), 'submitted', max_score))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'submission_id': submission_id,
            'assignment_id': assignment_id,
            'user_id': user_id,
            'status': 'submitted',
            'submitted_at': datetime.now().isoformat()
        }

    def grade_submission(self, submission_id):
        """批改作业"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM homework_submissions WHERE submission_id = ?', (submission_id,))
        submission = cursor.fetchone()
        if not submission:
            conn.close()
            return {'success': False, 'error': '提交记录不存在'}
        
        assignment_id = submission[2]
        user_id = submission[3]
        answers = json.loads(submission[4])
        
        cursor.execute('SELECT * FROM homework_questions WHERE assignment_id = ?', (assignment_id,))
        questions = cursor.fetchall()
        
        total_score = 0
        max_score_total = 0
        grading_results = []
        
        for question in questions:
            question_id = question[1]
            question_type = question[3]
            correct_answer = question[6]
            score = question[7]
            grading_rule = question[8]
            
            user_answer = answers.get(question_id, '')
            score_result, feedback, detail = self._grade_question(question_type, user_answer, correct_answer, score,
            grading_rule)
            
            total_score += score_result
            max_score_total += score
            
            result_id = hashlib.md5(f"{submission_id}{question_id}".encode()).hexdigest()[:16]
            cursor.execute('''
                INSERT INTO grading_results 
                (result_id, submission_id, question_id, question_type, user_answer, 
                 correct_answer, score, max_score, grading_detail, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (result_id, submission_id, question_id, question_type, str(user_answer), 
                  correct_answer, score_result, score, json.dumps(detail), feedback))
            
            grading_results.append({
                'question_id': question_id,
                'question_type': question_type,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'score': score_result,
                'max_score': score,
                'feedback': feedback,
                'detail': detail
            })
        
        cursor.execute('''
            UPDATE homework_submissions 
            SET status = ?, graded_at = ?, total_score = ?
            WHERE submission_id = ?
        ''', ('graded', datetime.now().isoformat(), total_score, submission_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'submission_id': submission_id,
            'total_score': total_score,
            'max_score': max_score_total,
            'grade': self._calculate_grade(total_score, max_score_total),
            'grading_results': grading_results,
            'graded_at': datetime.now().isoformat()
        }

    def _grade_question(self, question_type, user_answer, correct_answer, max_score, grading_rule):
        """批改单个题目"""
        user_answer = str(user_answer).strip()
        correct_answer = str(correct_answer).strip()
        
        if question_type == 'single_choice':
            return self._grade_single_choice(user_answer, correct_answer, max_score)
        elif question_type == 'multiple_choice':
            return self._grade_multiple_choice(user_answer, correct_answer, max_score)
        elif question_type == 'true_false':
            return self._grade_true_false(user_answer, correct_answer, max_score)
        elif question_type == 'fill_blank':
            return self._grade_fill_blank(user_answer, correct_answer, max_score)
        elif question_type == 'short_answer':
            return self._grade_short_answer(user_answer, correct_answer, max_score)
        elif question_type == 'essay':
            return self._grade_essay(user_answer, correct_answer, max_score)
        
        return 0, '未知题型', {'reason': '未知题型'}

    def _grade_single_choice(self, user_answer, correct_answer, max_score):
        if user_answer.lower() == correct_answer.lower():
            return max_score, '回答正确', {'matched': True, 'reason': '答案完全一致'}
        return 0, f'回答错误，正确答案是: {correct_answer}', {'matched': False, 'correct_answer': correct_answer}

    def _grade_multiple_choice(self, user_answer, correct_answer, max_score):
        user_set = set([a.strip() for a in user_answer.split(',') if a.strip()])
        correct_set = set([a.strip() for a in correct_answer.split(',') if a.strip()])
        
        if user_set == correct_set:
            return max_score, '回答正确', {'matched': True, 'reason': '答案完全一致'}
        
        intersection = user_set & correct_set
        union = user_set | correct_set
        
        if not intersection:
            return 0, f'回答错误，正确答案是: {correct_answer}', {'matched': False, 'correct_answer': correct_answer}
        
        score = int(max_score * len(intersection) / len(correct_set))
        return score, f'部分正确，正确答案是: {correct_answer}', {
            'matched': True, 'partial': True,
            'correct_count': len(intersection),
            'total_correct': len(correct_set),
            'user_answer': list(user_set),
            'correct_answer': list(correct_set)
        }

    def _grade_true_false(self, user_answer, correct_answer, max_score):
        user_norm = user_answer.lower()
        correct_norm = correct_answer.lower()
        
        true_variants = ['true', 't', '正确', '对', '是', '√']
        false_variants = ['false', 'f', '错误', '错', '否', '×']
        
        user_is_true = any(v in user_norm for v in true_variants)
        correct_is_true = any(v in correct_norm for v in true_variants)
        
        if user_is_true == correct_is_true:
            return max_score, '回答正确', {'matched': True, 'reason': '答案完全一致'}
        return 0, f'回答错误，正确答案是: {correct_answer}', {'matched': False, 'correct_answer': correct_answer}

    def _grade_fill_blank(self, user_answer, correct_answer, max_score):
        keywords = [k.strip() for k in correct_answer.split('|') if k.strip()]
        
        if not keywords:
            keywords = [correct_answer]
        
        matched_count = 0
        for keyword in keywords:
            if keyword in user_answer:
                matched_count += 1
        
        if matched_count == len(keywords):
            return max_score, '回答正确', {'matched': True, 'matched_keywords': keywords}
        
        if matched_count > 0:
            score = int(max_score * matched_count / len(keywords))
            return score, f'部分正确，需要包含: {", ".join(keywords)}', {
                'matched': True, 'partial': True,
                'matched_count': matched_count,
                'total_keywords': len(keywords),
                'keywords': keywords
            }
        
        return 0, f'回答错误，正确答案应包含: {", ".join(keywords)}', {
            'matched': False, 'keywords': keywords
        }

    def _grade_short_answer(self, user_answer, correct_answer, max_score):
        keywords = [k.strip() for k in correct_answer.split('|') if k.strip()]
        
        if not keywords:
            keywords = [correct_answer]
        
        matched_count = 0
        for keyword in keywords:
            if keyword in user_answer:
                matched_count += 1
        
        score_ratio = matched_count / len(keywords)
        
        if score_ratio >= 0.8:
            score = max_score
            feedback = '回答完整准确'
        elif score_ratio >= 0.5:
            score = int(max_score * 0.7)
            feedback = f'回答基本正确，但不够完整，需要包含: {", ".join(keywords[matched_count:])}'
        elif score_ratio > 0:
            score = int(max_score * 0.4)
            feedback = f'回答部分正确，需要包含更多要点: {", ".join(keywords[matched_count:])}'
        else:
            score = 0
            feedback = f'回答错误，正确答案应包含: {", ".join(keywords)}'
        
        return score, feedback, {
            'matched_count': matched_count,
            'total_keywords': len(keywords),
            'score_ratio': score_ratio,
            'keywords': keywords
        }

    def _grade_essay(self, user_answer, correct_answer, max_score):
        content_score = self._evaluate_essay_content(user_answer, correct_answer)
        structure_score = self._evaluate_essay_structure(user_answer)
        language_score = self._evaluate_essay_language(user_answer)
        creativity_score = self._evaluate_essay_creativity(user_answer)
        
        total_percent = content_score * 0.35 + structure_score * 0.25 + language_score * 0.25 + creativity_score * 0.15
        total_score = int(total_percent / 100 * max_score)
        
        feedback_parts = []
        if content_score >= 80:
            feedback_parts.append('内容丰富')
        elif content_score >= 60:
            feedback_parts.append('内容基本完整')
        else:
            feedback_parts.append('内容需要充实')
        
        if structure_score >= 80:
            feedback_parts.append('结构清晰')
        elif structure_score >= 60:
            feedback_parts.append('结构较清晰')
        else:
            feedback_parts.append('结构需要调整')
        
        if language_score >= 80:
            feedback_parts.append('语言流畅')
        elif language_score >= 60:
            feedback_parts.append('语言较流畅')
        else:
            feedback_parts.append('语言需要改进')
        
        feedback = '、'.join(feedback_parts)
        
        return total_score, feedback, {
            'content_score': content_score,
            'structure_score': structure_score,
            'language_score': language_score,
            'creativity_score': creativity_score,
            'word_count': len(user_answer),
            'paragraph_count': len([p for p in user_answer.split('\n') if p.strip()])
        }

    def _evaluate_essay_content(self, user_answer, correct_answer):
        keywords = [k.strip() for k in correct_answer.split('|') if k.strip()]
        if not keywords:
            return 70
        
        matched_count = sum(1 for k in keywords if k in user_answer)
        score = int(100 * matched_count / len(keywords))
        
        if len(user_answer) < 100:
            score = max(0, score - 20)
        elif len(user_answer) > 500:
            score = min(100, score + 10)
        
        return score

    def _evaluate_essay_structure(self, user_answer):
        paragraphs = [p for p in user_answer.split('\n') if p.strip()]
        
        if len(paragraphs) >= 4:
            return 85
        elif len(paragraphs) >= 3:
            return 70
        elif len(paragraphs) >= 2:
            return 55
        else:
            return 40

    def _evaluate_essay_language(self, user_answer):
        errors = []
        
        if len(user_answer) < 50:
            return 40
        
        sentence_lengths = [len(s) for s in re.split(r'[。！？；]', user_answer) if s.strip()]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if avg_length > 60:
                errors.append('句子过长')
        
        if user_answer.count('的') > len(user_answer) * 0.15:
            errors.append('助词过多')
        
        if not user_answer.strip().endswith(('。', '！', '？')):
            errors.append('缺少结尾标点')
        
        if not errors:
            return 85
        elif len(errors) == 1:
            return 70
        else:
            return 55

    def _evaluate_essay_creativity(self, user_answer):
        unique_chars = len(set(user_answer))
        total_chars = len(user_answer)
        
        if total_chars == 0:
            return 0
        
        diversity = unique_chars / total_chars
        
        if diversity > 0.8:
            return 80
        elif diversity > 0.6:
            return 60
        elif diversity > 0.4:
            return 40
        else:
            return 20

    def _calculate_grade(self, score, max_score):
        if max_score == 0:
            return 'N/A'
        ratio = score / max_score
        
        if ratio >= 0.9:
            return '优秀'
        elif ratio >= 0.8:
            return '良好'
        elif ratio >= 0.7:
            return '中等'
        elif ratio >= 0.6:
            return '及格'
        else:
            return '不及格'

    def get_submission(self, submission_id):
        """获取提交记录"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM homework_submissions WHERE submission_id = ?', (submission_id,))
        submission = cursor.fetchone()
        
        if submission:
            cursor.execute('SELECT * FROM grading_results WHERE submission_id = ?', (submission_id,))
            results = cursor.fetchall()
            
            grading_results = []
            for r in results:
                grading_results.append({
                    'question_id': r[3],
                    'question_type': r[4],
                    'user_answer': r[5],
                    'correct_answer': r[6],
                    'score': r[7],
                    'max_score': r[8],
                    'feedback': r[10]
                })
            
            conn.close()
            return {
                'success': True,
                'submission': {
                    'submission_id': submission[1],
                    'assignment_id': submission[2],
                    'user_id': submission[3],
                    'answers': json.loads(submission[4]),
                    'status': submission[5],
                    'submitted_at': submission[6],
                    'graded_at': submission[7],
                    'total_score': submission[8],
                    'max_score': submission[9]
                },
                'grading_results': grading_results
            }
        
        conn.close()
        return {'success': False, 'error': '提交记录不存在'}

    def list_submissions(self, assignment_id=None, user_id=None, limit=20):
        """列出提交记录"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM homework_submissions WHERE 1=1'
        params = []
        
        if assignment_id:
            query += ' AND assignment_id = ?'
            params.append(assignment_id)
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        query += ' ORDER BY submitted_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        conn.close()
        
        result = []
        for s in submissions:
            result.append({
                'submission_id': s[1],
                'assignment_id': s[2],
                'user_id': s[3],
                'status': s[5],
                'submitted_at': s[6],
                'graded_at': s[7],
                'total_score': s[8],
                'max_score': s[9]
            })
        
        return {'success': True, 'submissions': result}

    def get_assignment(self, assignment_id):
        """获取作业详情"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM homework_assignments WHERE assignment_id = ?', (assignment_id,))
        assignment = cursor.fetchone()
        
        if assignment:
            cursor.execute('SELECT * FROM homework_questions WHERE assignment_id = ?', (assignment_id,))
            questions = cursor.fetchall()
            
            question_list = []
            for q in questions:
                question_list.append({
                    'question_id': q[1],
                    'question_type': q[3],
                    'content': q[4],
                    'options': json.loads(q[5]) if q[5] else [],
                    'correct_answer': q[6],
                    'score': q[7]
                })
            
            conn.close()
            return {
                'success': True,
                'assignment': {
                    'assignment_id': assignment[1],
                    'title': assignment[2],
                    'subject': assignment[3],
                    'grade_level': assignment[4],
                    'total_score': assignment[5],
                    'deadline': assignment[6],
                    'status': assignment[7],
                    'created_at': assignment[8]
                },
                'questions': question_list
            }
        
        conn.close()
        return {'success': False, 'error': '作业不存在'}

    def list_assignments(self, subject=None, status=None, limit=20):
        """列出作业"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM homework_assignments WHERE 1=1'
        params = []
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        assignments = cursor.fetchall()
        conn.close()
        
        result = []
        for a in assignments:
            result.append({
                'assignment_id': a[1],
                'title': a[2],
                'subject': a[3],
                'grade_level': a[4],
                'total_score': a[5],
                'deadline': a[6],
                'status': a[7],
                'created_at': a[8]
            })
        
        return {'success': True, 'assignments': result}

    def get_grading_analytics(self, assignment_id):
        """获取批改分析"""
        conn = sqlite3.connect('ai_homework_grading.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE assignment_id = ?', (assignment_id,))
        submission_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT total_score FROM homework_submissions WHERE assignment_id = ? AND status = ?', 
                      (assignment_id, 'graded'))
        scores = cursor.fetchall()
        
        avg_score = sum(s[0] for s in scores) / len(scores) if scores else 0
        
        score_dist = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        for s in scores:
            ratio = s[0] / 100
            if ratio >= 0.9:
                score_dist['excellent'] += 1
            elif ratio >= 0.75:
                score_dist['good'] += 1
            elif ratio >= 0.6:
                score_dist['fair'] += 1
            else:
                score_dist['poor'] += 1
        
        conn.close()
        
        return {
            'success': True,
            'analytics': {
                'submission_count': submission_count,
                'graded_count': len(scores),
                'avg_score': round(avg_score, 2),
                'score_distribution': score_dist,
                'pass_rate': round(len([s for s in scores if s[0] >= 60]) / len(scores) * 100, 2) if scores else 0
            }
        }

ai_homework_grading = AIHomeworkGrading()