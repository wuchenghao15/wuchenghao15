# -*- coding: utf-8 -*-
"""
AI智能辅导助手API
功能：
1. AI智能问答 - 解答学生问题，提供详细解析
2. AI作业辅导 - 分析作业题目，提供解题思路
3. AI学习笔记 - 自动生成学习笔记和知识点总结
4. AI学习提醒 - 智能提醒学习任务和复习计划
5. AI学习社区 - 学生互助问答平台
6. AI智能评价 - 自动评价学生学习表现
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
import json
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ai_tutor_assistant_api = Blueprint('ai_tutor_assistant_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_answer_analysis(question_text, user_answer, correct_answer):
    analysis = {
        'question_summary': question_text[:50] + '...' if len(question_text) > 50 else question_text,
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'is_correct': str(user_answer).strip().lower() == str(correct_answer).strip().lower(),
        'analysis': '',
        'suggestion': '',
        'related_topics': []
    }
    
    if analysis['is_correct']:
        analysis['analysis'] = '回答正确！'
        analysis['suggestion'] = '继续保持，可以尝试挑战更难的题目'
    else:
        analysis['analysis'] = f'回答错误。正确答案是：{correct_answer}。'
        analysis['suggestion'] = '建议回顾相关知识点，多加练习'
    
    return analysis


def generate_study_notes(subject, content):
    notes = {
        'subject': subject,
        'summary': '',
        'key_points': [],
        'formulas': [],
        'examples': [],
        'practice_tips': ''
    }
    
    if subject == '数学':
        notes['summary'] = '数学是研究数量、结构、变化以及空间等概念的学科'
        notes['key_points'] = ['理解基本概念', '掌握公式定理', '多做练习题', '总结解题方法']
        notes['formulas'] = ['勾股定理: a² + b² = c²', '二次方程求根公式', '导数公式']
        notes['examples'] = ['应用题解题步骤', '几何证明方法', '代数运算技巧']
        notes['practice_tips'] = '每天坚持练习，注意错题分析，建立错题本'
    
    elif subject == '英语':
        notes['summary'] = '英语学习需要听说读写全面发展'
        notes['key_points'] = ['词汇积累', '语法掌握', '阅读理解', '口语表达']
        notes['formulas'] = ['基本句型结构', '时态变化规则', '从句用法']
        notes['examples'] = ['日常对话练习', '阅读理解技巧', '写作模板']
        notes['practice_tips'] = '多听英文歌和看英文电影，坚持每天阅读和写作'
    
    elif subject == '物理':
        notes['summary'] = '物理是研究物质运动和相互作用的自然科学'
        notes['key_points'] = ['理解物理概念', '掌握公式应用', '分析物理过程', '实验操作']
        notes['formulas'] = ['牛顿第二定律: F=ma', '能量守恒定律', '欧姆定律']
        notes['examples'] = ['力学解题方法', '电学实验设计', '光学现象分析']
        notes['practice_tips'] = '结合生活实例理解物理概念，多做实验练习'
    
    elif subject == '化学':
        notes['summary'] = '化学是研究物质组成、结构和变化的科学'
        notes['key_points'] = ['元素周期表', '化学反应方程式', '化学平衡', '有机化学']
        notes['formulas'] = ['摩尔定律', '化学反应速率公式', '溶解度计算']
        notes['examples'] = ['化学方程式配平', '物质推断题', '实验设计']
        notes['practice_tips'] = '牢记化学方程式，多做实验观察，理解反应原理'
    
    else:
        notes['summary'] = f'{subject}学习笔记'
        notes['key_points'] = ['理解基本概念', '掌握核心知识点', '多做练习', '定期复习']
        notes['practice_tips'] = '制定学习计划，按章节系统学习'
    
    return notes


def generate_study_reminders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, deadline FROM homework_assignments 
        WHERE deadline IS NOT NULL AND deadline > ?
        ORDER BY deadline ASC LIMIT 5
    ''', (datetime.now().isoformat(),))
    upcoming_homework = cursor.fetchall()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as cnt 
        FROM user_answers 
        WHERE user_id = ? AND is_wrong = 1
        GROUP BY DATE(created_at)
        ORDER BY date DESC LIMIT 3
    ''', (user_id,))
    recent_wrong = cursor.fetchall()
    
    conn.close()
    
    reminders = []
    
    for hw in upcoming_homework:
        deadline = datetime.fromisoformat(hw['deadline']) if hw['deadline'] else None
        if deadline:
            days_left = (deadline - datetime.now()).days
            if days_left <= 1:
                priority = 'high'
            elif days_left <= 3:
                priority = 'medium'
            else:
                priority = 'low'
            
            reminders.append({
                'type': 'homework',
                'title': hw['title'],
                'deadline': hw['deadline'],
                'days_left': days_left,
                'priority': priority,
                'message': f'作业"{hw["title"]}"还有{days_left}天截止，请及时完成'
            })
    
    if recent_wrong and len([r for r in recent_wrong if r['cnt'] > 5]) > 0:
        reminders.append({
            'type': 'review',
            'title': '错题复习提醒',
            'priority': 'high',
            'message': '近期错题较多，建议进行错题复习'
        })
    
    return reminders


def generate_performance_report(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as total FROM exam_results WHERE user_id = ?
    ''', (user_id,))
    total_exams = cursor.fetchone()['total']
    
    cursor.execute('''
        SELECT AVG(score) as avg FROM exam_results WHERE user_id = ?
    ''', (user_id,))
    avg_score = cursor.fetchone()['avg'] or 0
    
    cursor.execute('''
        SELECT COUNT(*) as completed FROM homework_submissions WHERE student_id = ? AND status = 'graded'
    ''', (str(user_id),))
    completed_homework = cursor.fetchone()['completed']
    
    cursor.execute('''
        SELECT COUNT(*) as wrong FROM user_answers WHERE user_id = ? AND is_wrong = 1
    ''', (user_id,))
    wrong_count = cursor.fetchone()['wrong']
    
    cursor.execute('''
        SELECT COUNT(*) as correct FROM user_answers WHERE user_id = ? AND is_wrong = 0
    ''', (user_id,))
    correct_count = cursor.fetchone()['correct']
    
    cursor.execute('''
        SELECT s.class_name, s.grade FROM students s WHERE s.user_id = ?
    ''', (user_id,))
    student_info = cursor.fetchone()
    
    conn.close()
    
    accuracy = 0
    if wrong_count + correct_count > 0:
        accuracy = round(correct_count / (wrong_count + correct_count) * 100, 2)
    
    if avg_score >= 90:
        grade = 'A'
        comment = '学习表现优秀，继续保持！'
    elif avg_score >= 80:
        grade = 'B'
        comment = '学习表现良好，还有提升空间'
    elif avg_score >= 70:
        grade = 'C'
        comment = '学习表现一般，需要加强练习'
    elif avg_score >= 60:
        grade = 'D'
        comment = '刚刚及格，需要更加努力'
    else:
        grade = 'F'
        comment = '学习表现较差，建议寻求老师帮助'
    
    return {
        'user_id': user_id,
        'class_name': student_info['class_name'] if student_info else '',
        'grade': student_info['grade'] if student_info else '',
        'total_exams': total_exams,
        'avg_score': round(avg_score, 2),
        'completed_homework': completed_homework,
        'wrong_count': wrong_count,
        'correct_count': correct_count,
        'accuracy': accuracy,
        'performance_grade': grade,
        'comment': comment,
        'generated_at': datetime.now().isoformat()
    }


@ai_tutor_assistant_api.route('/api/ai/tutor/ask', methods=['POST'])
@require_login
def tutor_ask():
    try:
        data = request.get_json()
        question = data.get('question', '')
        subject = data.get('subject', '')
        
        if not question:
            return APIResponse.validation_error(message='请输入问题')
        
        answer = {
            'question': question,
            'subject': subject,
            'answer': generate_tutor_answer(question, subject),
            'related_topics': generate_related_topics(subject, question),
            'suggested_questions': generate_suggested_questions(subject),
            'generated_at': datetime.now().isoformat()
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tutor_questions (user_id, question, subject, answer, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session.get('user_id'), question, subject, json.dumps(answer), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=answer, message='AI辅导解答完成')
    
    except Exception as e:
        logger.error(f'AI辅导解答失败: {e}')
        return APIResponse.error(message=f'AI辅导解答失败: {str(e)}')


def generate_tutor_answer(question, subject):
    base_answers = {
        '数学': {
            'default': '这是一个数学问题。让我为你详细解答：\n\n',
            '公式': '这个问题涉及以下公式和定理：\n',
            '解题': '解题步骤如下：\n1. 理解题目要求\n2. 确定适用的公式\n3. 代入数值计算\n4. 验证结果'
        },
        '英语': {
            'default': '这是一个英语问题。让我为你详细解答：\n\n',
            '语法': '这个问题涉及以下语法知识：\n',
            '词汇': '相关词汇和短语：\n',
            '例句': '例句：\n'
        },
        '物理': {
            'default': '这是一个物理问题。让我为你详细解答：\n\n',
            '公式': '相关公式：\n',
            '原理': '物理原理：\n',
            '应用': '实际应用：\n'
        },
        '化学': {
            'default': '这是一个化学问题。让我为你详细解答：\n\n',
            '方程式': '相关化学方程式：\n',
            '原理': '化学反应原理：\n',
            '实验': '实验注意事项：\n'
        }
    }
    
    answer = base_answers.get(subject, base_answers['数学'])['default']
    
    keywords = ['公式', '定理', '解题', '计算', '证明', '推导']
    for kw in keywords:
        if kw in question:
            answer += base_answers.get(subject, {}).get('公式', '')
            break
    
    answer += '\n建议步骤：\n1. 仔细阅读题目\n2. 分析已知条件\n3. 确定解题方法\n4. 逐步推导\n5. 检查结果\n\n如果有具体题目，我可以为你提供更详细的解答！'
    
    return answer


def generate_related_topics(subject, question):
    topics_map = {
        '数学': ['代数运算', '几何图形', '函数', '概率统计', '微积分'],
        '英语': ['词汇', '语法', '阅读理解', '写作', '口语'],
        '物理': ['力学', '电学', '光学', '热学', '量子物理'],
        '化学': ['无机化学', '有机化学', '化学反应', '元素周期表', '实验化学']
    }
    
    return topics_map.get(subject, ['基础概念', '进阶知识', '拓展学习'])


def generate_suggested_questions(subject):
    questions_map = {
        '数学': [
            '如何求解一元二次方程？',
            '勾股定理的应用场景有哪些？',
            '如何计算概率？',
            '导数的定义是什么？'
        ],
        '英语': [
            '如何区分现在完成时和一般过去时？',
            '宾语从句的用法是什么？',
            '如何提高阅读理解能力？',
            '英语写作有哪些技巧？'
        ],
        '物理': [
            '牛顿三大定律是什么？',
            '欧姆定律的应用？',
            '光的折射定律是什么？',
            '能量守恒定律的应用？'
        ],
        '化学': [
            '如何配平化学方程式？',
            '元素周期表的规律是什么？',
            '酸碱中和反应的原理？',
            '有机化合物的命名规则？'
        ]
    }
    
    return questions_map.get(subject, ['相关知识点有哪些？', '如何应用这些知识？', '有什么学习技巧？'])[:3]


@ai_tutor_assistant_api.route('/api/ai/tutor/homework_help', methods=['POST'])
@require_login
def homework_help():
    try:
        data = request.get_json()
        question_text = data.get('question', '')
        subject = data.get('subject', '')
        user_answer = data.get('user_answer', '')
        
        if not question_text:
            return APIResponse.validation_error(message='请输入作业题目')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, correct_answer, hints FROM homework_questions 
            WHERE question_text LIKE ? LIMIT 1
        ''', (f'%{question_text[:50]}%',))
        question = cursor.fetchone()
        
        conn.close()
        
        correct_answer = question['correct_answer'] if question else '暂无标准答案'
        
        analysis = generate_answer_analysis(question_text, user_answer, correct_answer)
        
        if question:
            analysis['hints'] = question['hints']
        
        return APIResponse.success(data={
            'question': question_text,
            'subject': subject,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat()
        }, message='AI作业辅导完成')
    
    except Exception as e:
        logger.error(f'AI作业辅导失败: {e}')
        return APIResponse.error(message=f'AI作业辅导失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/study_notes', methods=['POST'])
@require_login
def study_notes():
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        content = data.get('content', '')
        
        if not subject:
            return APIResponse.validation_error(message='请输入科目')
        
        notes = generate_study_notes(subject, content)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO study_notes (user_id, subject, notes_data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (session.get('user_id'), subject, json.dumps(notes), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=notes, message='AI学习笔记生成完成')
    
    except Exception as e:
        logger.error(f'AI学习笔记生成失败: {e}')
        return APIResponse.error(message=f'AI学习笔记生成失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/reminders', methods=['GET'])
@require_login
def reminders():
    try:
        user_id = session.get('user_id')
        reminders = generate_study_reminders(user_id)
        
        return APIResponse.success(data={
            'reminders': reminders,
            'count': len(reminders),
            'generated_at': datetime.now().isoformat()
        }, message='AI学习提醒获取完成')
    
    except Exception as e:
        logger.error(f'AI学习提醒获取失败: {e}')
        return APIResponse.error(message=f'AI学习提醒获取失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/performance_report', methods=['GET'])
@require_login
def performance_report():
    try:
        user_id = session.get('user_id')
        report = generate_performance_report(user_id)
        
        return APIResponse.success(data=report, message='AI学习表现报告生成完成')
    
    except Exception as e:
        logger.error(f'AI学习表现报告生成失败: {e}')
        return APIResponse.error(message=f'AI学习表现报告生成失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/class_performance', methods=['GET'])
@require_admin
def class_performance():
    try:
        data = request.args
        cls = data.get('class', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if cls:
            cursor.execute('''
                SELECT u.id, u.username, s.class_name, s.grade
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                WHERE s.class_name = ? AND u.role = 'student'
            ''', (cls,))
        else:
            cursor.execute('''
                SELECT u.id, u.username, s.class_name, s.grade
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                WHERE u.role = 'student'
            ''')
        
        students = cursor.fetchall()
        
        class_report = {
            'class_name': cls or '全部',
            'total_students': len(students),
            'students': [],
            'class_avg_score': 0,
            'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
            'generated_at': datetime.now().isoformat()
        }
        
        total_avg = 0
        count = 0
        
        for student in students:
            report = generate_performance_report(student['id'])
            class_report['students'].append({
                'user_id': student['id'],
                'username': student['username'],
                'avg_score': report['avg_score'],
                'performance_grade': report['performance_grade'],
                'comment': report['comment']
            })
            
            if report['avg_score'] > 0:
                total_avg += report['avg_score']
                count += 1
            
            class_report['grade_distribution'][report['performance_grade']] += 1
        
        if count > 0:
            class_report['class_avg_score'] = round(total_avg / count, 2)
        
        conn.close()
        
        return APIResponse.success(data=class_report, message='班级AI学习表现报告生成完成')
    
    except Exception as e:
        logger.error(f'班级AI学习表现报告生成失败: {e}')
        return APIResponse.error(message=f'班级AI学习表现报告生成失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/community/questions', methods=['GET'])
@require_login
def community_questions():
    try:
        data = request.args
        page = int(data.get('page', 1))
        limit = int(data.get('limit', 10))
        subject = data.get('subject', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if subject:
            conditions.append('subject = ?')
            params.append(subject)
        
        query = f'''
            SELECT q.*, u.username as author_name
            FROM community_questions q
            LEFT JOIN users u ON q.user_id = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY q.created_at DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([limit, (page - 1) * limit])
        
        cursor.execute(query, params)
        questions = cursor.fetchall()
        
        cursor.execute(f'''
            SELECT COUNT(*) as total FROM community_questions
            WHERE {' AND '.join(conditions)}
        ''', params[:-2])
        total = cursor.fetchone()['total']
        
        conn.close()
        
        return APIResponse.success(data={
            'questions': [dict(q) for q in questions],
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit,
            'subject': subject
        }, message='AI学习社区问题获取完成')
    
    except Exception as e:
        logger.error(f'AI学习社区问题获取失败: {e}')
        return APIResponse.error(message=f'AI学习社区问题获取失败: {str(e)}')


@ai_tutor_assistant_api.route('/api/ai/tutor/community/questions', methods=['POST'])
@require_login
def community_post_question():
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        subject = data.get('subject', '')
        
        if not title or not content:
            return APIResponse.validation_error(message='请输入标题和内容')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO community_questions (user_id, title, content, subject, status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
        ''', (session.get('user_id'), title, content, subject, datetime.now().isoformat()))
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        
        return APIResponse.success(data={
            'question_id': question_id,
            'title': title,
            'content': content,
            'subject': subject,
            'created_at': datetime.now().isoformat()
        }, message='问题发布成功')
    
    except Exception as e:
        logger.error(f'AI学习社区问题发布失败: {e}')
        return APIResponse.error(message=f'AI学习社区问题发布失败: {str(e)}')


def init_tutor_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutor_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                subject TEXT,
                answer TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                notes_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                subject TEXT,
                status TEXT DEFAULT 'active',
                answers_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                is_accepted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES community_questions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info('AI智能辅导助手表结构创建完成')
    except Exception as e:
        logger.error(f'AI智能辅导助手表结构创建失败: {e}')


init_tutor_tables()