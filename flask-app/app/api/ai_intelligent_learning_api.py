# -*- coding: utf-8 -*-
"""
AI智能学习闭环系统API
功能：
1. AI学情诊断 - 分析学生学习数据，识别薄弱环节
2. AI学习推荐 - 根据诊断结果推荐个性化学习路径
3. AI智能出题 - 根据学生水平自动生成针对性题目
4. AI作业批改 - 自动批改作业并生成AI反馈
5. AI学习效果预测 - 预测学生学习趋势和成绩
6. AI学习助手 - 智能辅导和答疑
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
import math

logger = logging.getLogger(__name__)

ai_intelligent_learning_api = Blueprint('ai_intelligent_learning_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_student_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.*, s.class_name, s.grade 
        FROM users u 
        LEFT JOIN students s ON u.id = s.user_id 
        WHERE u.id = ?
    ''', (user_id,))
    user = cursor.fetchone()
    
    cursor.execute('''
        SELECT score, subject, created_at FROM exam_results 
        WHERE user_id = ? ORDER BY created_at DESC LIMIT 20
    ''', (user_id,))
    exam_records = cursor.fetchall()
    
    cursor.execute('''
        SELECT question_id, is_wrong, created_at FROM user_answers 
        WHERE user_id = ? ORDER BY created_at DESC LIMIT 50
    ''', (user_id,))
    answer_records = cursor.fetchall()
    
    cursor.execute('''
        SELECT homework_id, score, status FROM homework_submissions 
        WHERE user_id = ? ORDER BY submission_time DESC LIMIT 20
    ''', (user_id,))
    homework_records = cursor.fetchall()
    
    conn.close()
    
    return {
        'user': dict(user) if user else None,
        'exams': [dict(r) for r in exam_records],
        'answers': [dict(r) for r in answer_records],
        'homework': [dict(r) for r in homework_records]
    }


def analyze_weak_points(student_data):
    subject_scores = {}
    wrong_counts = {}
    subject_wrong = {}
    
    for exam in student_data['exams']:
        subject = exam.get('subject', '未知')
        score = exam.get('score', 0)
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(score)
    
    for answer in student_data['answers']:
        qid = answer.get('question_id')
        is_wrong = answer.get('is_wrong', 0)
        if qid:
            wrong_counts[qid] = wrong_counts.get(qid, 0) + is_wrong
    
    subject_stats = {}
    for subject, scores in subject_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            pass_rate = len([s for s in scores if s >= 60]) / len(scores)
            subject_stats[subject] = {
                'avg_score': round(avg_score, 2),
                'count': len(scores),
                'pass_rate': round(pass_rate, 2),
                'weak_level': '弱' if avg_score < 60 else ('中等' if avg_score < 80 else '强')
            }
    
    sorted_subjects = sorted(subject_stats.items(), key=lambda x: x[1]['avg_score'])
    weak_subjects = [s for s in sorted_subjects if s[1]['weak_level'] != '强']
    
    wrong_question_ids = [qid for qid, count in wrong_counts.items() if count >= 2]
    
    return {
        'subject_stats': dict(subject_stats),
        'weak_subjects': [{'subject': s[0], **s[1]} for s in weak_subjects],
        'frequent_wrong_questions': wrong_question_ids,
        'overall_analysis': generate_analysis_report(subject_stats)
    }


def generate_analysis_report(subject_stats):
    if not subject_stats:
        return '暂无足够数据进行分析'
    
    avg_all = sum(s['avg_score'] for s in subject_stats.values()) / len(subject_stats)
    weak_count = len([s for s in subject_stats.values() if s['weak_level'] == '弱'])
    
    if avg_all >= 90:
        return '学习表现优秀，建议挑战更高难度内容'
    elif avg_all >= 80:
        return '学习表现良好，继续保持并关注薄弱科目'
    elif avg_all >= 60:
        return f'学习表现一般，有{weak_count}个科目需要加强'
    else:
        return f'学习表现较差，建议重点复习基础内容，有{weak_count}个科目需要重点关注'


def generate_personalized_recommendations(student_data, weak_points):
    recommendations = []
    
    for weak in weak_points['weak_subjects']:
        subject = weak['subject']
        avg_score = weak['avg_score']
        
        recommendation = {
            'subject': subject,
            'priority': 'high' if avg_score < 60 else 'medium',
            'action_items': [],
            'estimated_time': 0
        }
        
        if avg_score < 60:
            recommendation['action_items'].append(f'复习{subject}基础知识，建议每天学习30分钟')
            recommendation['action_items'].append(f'完成{subject}基础练习题，巩固知识点')
            recommendation['estimated_time'] = 20
        elif avg_score < 80:
            recommendation['action_items'].append(f'加强{subject}薄弱章节的练习')
            recommendation['action_items'].append(f'观看{subject}相关教学视频')
            recommendation['estimated_time'] = 10
        
        recommendations.append(recommendation)
    
    for qid in weak_points['frequent_wrong_questions'][:5]:
        recommendations.append({
            'subject': '错题复习',
            'priority': 'high',
            'action_items': [f'重做题目ID:{qid}，分析错误原因'],
            'estimated_time': 5
        })
    
    return recommendations


def generate_adaptive_questions(user_id, subject='', count=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT difficulty, COUNT(*) as cnt 
        FROM user_answers ua 
        LEFT JOIN questions q ON ua.question_id = q.id 
        WHERE ua.user_id = ? AND ua.is_wrong = 1
        GROUP BY q.difficulty
        ORDER BY cnt DESC LIMIT 1
    ''', (user_id,))
    weak_diff = cursor.fetchone()
    target_diff = weak_diff['difficulty'] if weak_diff else 'medium'
    
    conditions = []
    params = []
    
    if subject:
        conditions.append('q.subject = ?')
        params.append(subject)
    
    conditions.append('q.difficulty IN (?, ?, ?)')
    diff_order = ['easy', 'medium', 'hard']
    idx = diff_order.index(target_diff) if target_diff in diff_order else 1
    params.extend([diff_order[max(0, idx-1)], diff_order[idx], diff_order[min(2, idx+1)]])
    
    query = f'''
        SELECT q.id, q.question_text, q.question_type, q.difficulty, q.subject, q.options
        FROM questions q
        LEFT JOIN user_answers ua ON q.id = ua.question_id AND ua.user_id = ?
        WHERE {' AND '.join(conditions)}
          AND (ua.id IS NULL OR ua.is_wrong = 1)
        ORDER BY RANDOM() LIMIT ?
    '''
    params.extend([user_id, count])
    
    cursor.execute(query, params)
    questions = cursor.fetchall()
    
    conn.close()
    
    return [dict(q) for q in questions]


def predict_learning_outcome(student_data):
    exams = student_data['exams']
    if not exams:
        return {'prediction': '数据不足，无法预测', 'confidence': 0}
    
    recent_scores = [e['score'] for e in exams[-10:] if e['score']]
    if not recent_scores:
        return {'prediction': '数据不足，无法预测', 'confidence': 0}
    
    avg_score = sum(recent_scores) / len(recent_scores)
    trend = 0
    if len(recent_scores) >= 3:
        for i in range(1, len(recent_scores)):
            trend += recent_scores[i] - recent_scores[i-1]
        trend /= len(recent_scores) - 1
    
    improvement_rate = trend / avg_score if avg_score > 0 else 0
    
    predicted_score = avg_score + trend * 2
    
    confidence = min(1, len(recent_scores) / 10)
    
    if predicted_score >= 90:
        prediction = '优秀'
    elif predicted_score >= 80:
        prediction = '良好'
    elif predicted_score >= 60:
        prediction = '及格'
    else:
        prediction = '需加强'
    
    return {
        'current_avg': round(avg_score, 2),
        'trend': round(trend, 2),
        'improvement_rate': round(improvement_rate * 100, 2),
        'predicted_score': round(predicted_score, 2),
        'prediction': prediction,
        'confidence': round(confidence, 2),
        'suggestion': generate_prediction_suggestion(trend, avg_score)
    }


def generate_prediction_suggestion(trend, avg_score):
    if trend > 5:
        return '学习进步明显，继续保持当前学习节奏'
    elif trend > 0:
        return '学习稳步提升，建议适当增加练习强度'
    elif trend == 0:
        return '学习成绩持平，建议调整学习方法'
    elif trend > -5:
        return '学习成绩有所下降，建议回顾近期学习内容'
    else:
        return '学习成绩下降明显，建议寻求老师辅导或调整学习计划'


@ai_intelligent_learning_api.route('/api/ai/learning/diagnosis', methods=['GET'])
@require_login
def learning_diagnosis():
    try:
        user_id = session.get('user_id')
        student_data = get_student_data(user_id)
        weak_points = analyze_weak_points(student_data)
        recommendations = generate_personalized_recommendations(student_data, weak_points)
        
        return APIResponse.success(data={
            'student_info': student_data['user'],
            'weak_points': weak_points,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }, message='AI学情诊断完成')
    
    except Exception as e:
        logger.error(f'AI学情诊断失败: {e}')
        return APIResponse.error(message=f'AI学情诊断失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/recommend', methods=['POST'])
@require_login
def learning_recommend():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        subject = data.get('subject', '')
        limit = data.get('limit', 5)
        
        student_data = get_student_data(user_id)
        weak_points = analyze_weak_points(student_data)
        recommendations = generate_personalized_recommendations(student_data, weak_points)
        
        filtered_recs = recommendations
        if subject:
            filtered_recs = [r for r in recommendations if r['subject'] == subject]
        
        return APIResponse.success(data={
            'recommendations': filtered_recs[:limit],
            'total_count': len(filtered_recs),
            'subject': subject,
            'generated_at': datetime.now().isoformat()
        }, message='AI学习推荐生成完成')
    
    except Exception as e:
        logger.error(f'AI学习推荐失败: {e}')
        return APIResponse.error(message=f'AI学习推荐失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/adaptive_questions', methods=['POST'])
@require_login
def adaptive_questions():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        subject = data.get('subject', '')
        count = data.get('count', 5)
        
        questions = generate_adaptive_questions(user_id, subject, count)
        
        if not questions:
            conn = get_db_connection()
            cursor = conn.cursor()
            cond = ''
            params = []
            if subject:
                cond = 'WHERE subject = ?'
                params.append(subject)
            cursor.execute(f'SELECT id, question_text, question_type, difficulty, subject, options FROM questions {cond} ORDER BY RANDOM() LIMIT ?', params + [count])
            questions = [dict(q) for q in cursor.fetchall()]
            conn.close()
        
        return APIResponse.success(data={
            'questions': questions,
            'count': len(questions),
            'subject': subject,
            'strategy': 'adaptive' if generate_adaptive_questions else 'random',
            'generated_at': datetime.now().isoformat()
        }, message='AI自适应题目生成完成')
    
    except Exception as e:
        logger.error(f'AI自适应题目生成失败: {e}')
        return APIResponse.error(message=f'AI自适应题目生成失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/predict', methods=['GET'])
@require_login
def learning_predict():
    try:
        user_id = session.get('user_id')
        student_data = get_student_data(user_id)
        prediction = predict_learning_outcome(student_data)
        
        return APIResponse.success(data={
            'prediction': prediction,
            'exam_count': len(student_data['exams']),
            'generated_at': datetime.now().isoformat()
        }, message='AI学习效果预测完成')
    
    except Exception as e:
        logger.error(f'AI学习效果预测失败: {e}')
        return APIResponse.error(message=f'AI学习效果预测失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/score_trend', methods=['GET'])
@require_login
def score_trend():
    try:
        user_id = session.get('user_id')
        data = request.args
        
        subject = data.get('subject', '')
        time_range = data.get('time_range', 'month')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        conditions = ['user_id = ?']
        params = [user_id]
        
        if subject:
            conditions.append('subject = ?')
            params.append(subject)
        
        if time_range == 'week':
            conditions.append('created_at >= ?')
            params.append((datetime.now() - timedelta(days=7)).isoformat())
        elif time_range == 'month':
            conditions.append('created_at >= ?')
            params.append((datetime.now() - timedelta(days=30)).isoformat())
        elif time_range == 'quarter':
            conditions.append('created_at >= ?')
            params.append((datetime.now() - timedelta(days=90)).isoformat())
        
        cursor.execute(f'''
            SELECT DATE(created_at) as date, AVG(score) as avg_score, COUNT(*) as count
            FROM exam_results
            WHERE {' AND '.join(conditions)}
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''', params)
        
        records = cursor.fetchall()
        conn.close()
        
        trend_data = {
            'labels': [r['date'] for r in records],
            'scores': [round(r['avg_score'], 2) if r['avg_score'] else 0 for r in records],
            'counts': [r['count'] for r in records]
        }
        
        return APIResponse.success(data={
            'trend': trend_data,
            'subject': subject,
            'time_range': time_range,
            'generated_at': datetime.now().isoformat()
        }, message='AI成绩趋势分析完成')
    
    except Exception as e:
        logger.error(f'AI成绩趋势分析失败: {e}')
        return APIResponse.error(message=f'AI成绩趋势分析失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/dashboard', methods=['GET'])
@require_login
def learning_dashboard():
    try:
        user_id = session.get('user_id')
        student_data = get_student_data(user_id)
        weak_points = analyze_weak_points(student_data)
        prediction = predict_learning_outcome(student_data)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total FROM exam_results WHERE user_id = ?
        ''', (user_id,))
        total_exams = cursor.fetchone()['total']
        
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
        
        conn.close()
        
        accuracy = 0
        if wrong_count + correct_count > 0:
            accuracy = round(correct_count / (wrong_count + correct_count) * 100, 2)
        
        return APIResponse.success(data={
            'overview': {
                'total_exams': total_exams,
                'completed_homework': completed_homework,
                'wrong_count': wrong_count,
                'correct_count': correct_count,
                'accuracy': accuracy
            },
            'weak_points': weak_points['weak_subjects'][:3],
            'prediction': prediction,
            'subject_stats': weak_points['subject_stats'],
            'generated_at': datetime.now().isoformat()
        }, message='AI学习仪表盘数据获取完成')
    
    except Exception as e:
        logger.error(f'AI学习仪表盘失败: {e}')
        return APIResponse.error(message=f'AI学习仪表盘失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/teacher_dashboard/<int:user_id>', methods=['GET'])
@require_admin
def teacher_dashboard(user_id):
    try:
        student_data = get_student_data(user_id)
        weak_points = analyze_weak_points(student_data)
        prediction = predict_learning_outcome(student_data)
        
        return APIResponse.success(data={
            'student_id': user_id,
            'student_info': student_data['user'],
            'weak_points': weak_points,
            'prediction': prediction,
            'exam_history': student_data['exams'][:10],
            'generated_at': datetime.now().isoformat()
        }, message='教师端AI学习分析完成')
    
    except Exception as e:
        logger.error(f'教师端AI学习分析失败: {e}')
        return APIResponse.error(message=f'教师端AI学习分析失败: {str(e)}')


@ai_intelligent_learning_api.route('/api/ai/learning/class_analysis', methods=['GET'])
@require_admin
def class_analysis():
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
        
        class_stats = {
            'total_students': len(students),
            'class_name': cls or '全部',
            'student_details': []
        }
        
        for student in students:
            sid = student['id']
            s_data = get_student_data(sid)
            weak = analyze_weak_points(s_data)
            predict = predict_learning_outcome(s_data)
            
            class_stats['student_details'].append({
                'user_id': sid,
                'username': student['username'],
                'class_name': student['class_name'],
                'avg_score': weak['subject_stats'] and sum(s['avg_score'] for s in weak['subject_stats'].values()) / len(weak['subject_stats']) or 0,
                'weak_count': len(weak['weak_subjects']),
                'prediction': predict['prediction'],
                'confidence': predict['confidence']
            })
        
        conn.close()
        
        avg_class_score = sum(s['avg_score'] for s in class_stats['student_details']) / len(class_stats['student_details']) if class_stats['student_details'] else 0
        weak_student_count = len([s for s in class_stats['student_details'] if s['weak_count'] > 0])
        
        class_stats['class_avg_score'] = round(avg_class_score, 2)
        class_stats['weak_student_count'] = weak_student_count
        class_stats['generated_at'] = datetime.now().isoformat()
        
        return APIResponse.success(data=class_stats, message='班级AI学习分析完成')
    
    except Exception as e:
        logger.error(f'班级AI学习分析失败: {e}')
        return APIResponse.error(message=f'班级AI学习分析失败: {str(e)}')


def init_ai_learning_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_diagnosis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                diagnosis_data TEXT,
                recommendations TEXT,
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                current_avg REAL,
                trend REAL,
                predicted_score REAL,
                prediction TEXT,
                confidence REAL,
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info('AI智能学习系统表结构创建完成')
    except Exception as e:
        logger.error(f'AI智能学习系统表结构创建失败: {e}')


init_ai_learning_tables()