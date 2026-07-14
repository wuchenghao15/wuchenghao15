# -*- coding: utf-8 -*-
"""
AI自动化学习推荐系统API
功能：
1. AI自动学习计划生成 - 根据学情自动生成个性化学习计划
2. AI智能学习路径推荐 - 基于知识图谱的学习路径规划
3. AI自动作业批改 - 自动批改作业并生成反馈
4. AI学习效果追踪 - 实时追踪学习效果
5. AI智能提醒 - 智能推送学习提醒
6. AI学习闭环 - 完整的学习-练习-反馈-改进闭环
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

ai_auto_learning_api = Blueprint('ai_auto_learning_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def analyze_student_level(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT AVG(score) as avg_score, COUNT(*) as exam_count 
        FROM exam_results WHERE user_id = ?
    ''', (user_id,))
    exam_stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT COUNT(*) as wrong_count FROM user_answers WHERE user_id = ? AND is_wrong = 1
    ''', (user_id,))
    wrong_count = cursor.fetchone()['wrong_count']
    
    cursor.execute('''
        SELECT COUNT(*) as total_count FROM user_answers WHERE user_id = ?
    ''', (user_id,))
    total_count = cursor.fetchone()['total_count']
    
    cursor.execute('''
        SELECT COUNT(*) as completed FROM homework_submissions WHERE student_id = ? AND status = 'graded'
    ''', (str(user_id),))
    completed_homework = cursor.fetchone()['completed']
    
    conn.close()
    
    avg_score = exam_stats['avg_score'] or 0
    exam_count = exam_stats['exam_count'] or 0
    
    accuracy = 0
    if total_count > 0:
        accuracy = (total_count - wrong_count) / total_count * 100
    
    if avg_score >= 90:
        level = 'advanced'
        level_desc = '高级'
    elif avg_score >= 80:
        level = 'intermediate'
        level_desc = '中级'
    elif avg_score >= 60:
        level = 'basic'
        level_desc = '初级'
    else:
        level = 'beginner'
        level_desc = '入门'
    
    return {
        'user_id': user_id,
        'avg_score': round(avg_score, 2),
        'exam_count': exam_count,
        'wrong_count': wrong_count,
        'total_answers': total_count,
        'accuracy': round(accuracy, 2),
        'completed_homework': completed_homework,
        'level': level,
        'level_desc': level_desc,
        'generated_at': datetime.now().isoformat()
    }


def generate_learning_plan(user_id, duration_days=7):
    student_level = analyze_student_level(user_id)
    level = student_level['level']
    
    subjects = ['数学', '英语', '物理', '化学']
    plan = {
        'user_id': user_id,
        'duration_days': duration_days,
        'student_level': student_level,
        'daily_plans': [],
        'goals': [],
        'estimated_hours': 0
    }
    
    daily_hours = {
        'beginner': 2,
        'basic': 1.5,
        'intermediate': 1,
        'advanced': 0.5
    }
    
    for day in range(1, duration_days + 1):
        daily_plan = {
            'day': day,
            'date': (datetime.now() + timedelta(days=day - 1)).strftime('%Y-%m-%d'),
            'subjects': [],
            'total_hours': daily_hours.get(level, 1)
        }
        
        subject_order = subjects.copy()
        random.shuffle(subject_order)
        
        hours_per_subject = daily_hours.get(level, 1) / len(subjects)
        
        for subject in subject_order:
            daily_plan['subjects'].append({
                'subject': subject,
                'hours': round(hours_per_subject, 1),
                'activities': generate_subject_activities(subject, level),
                'target_score': generate_target_score(level)
            })
        
        plan['daily_plans'].append(daily_plan)
        plan['estimated_hours'] += daily_hours.get(level, 1)
    
    plan['goals'] = [
        f'在{duration_days}天内提高{student_level["accuracy"]:.1f}%的答题准确率',
        f'完成{student_level["completed_homework"] + duration_days}份作业',
        f'复习{student_level["wrong_count"]}道错题',
        f'将平均分提升至{min(100, student_level["avg_score"] + 5):.0f}分'
    ]
    
    return plan


def generate_subject_activities(subject, level):
    activities_map = {
        '数学': {
            'beginner': ['复习基础概念', '完成10道基础题', '观看教学视频'],
            'basic': ['复习课本章节', '完成15道练习题', '整理错题'],
            'intermediate': ['专题练习', '完成5道难题', '模拟测试'],
            'advanced': ['竞赛题练习', '错题回顾', '知识拓展']
        },
        '英语': {
            'beginner': ['背诵20个单词', '学习基础语法', '跟读练习'],
            'basic': ['背诵30个单词', '语法专项练习', '阅读理解'],
            'intermediate': ['背诵50个单词', '完形填空', '写作练习'],
            'advanced': ['词汇拓展', '阅读理解', '口语对话']
        },
        '物理': {
            'beginner': ['理解基本概念', '公式背诵', '基础实验'],
            'basic': ['公式应用', '基础题练习', '实验分析'],
            'intermediate': ['综合题练习', '实验设计', '知识拓展'],
            'advanced': ['竞赛题练习', '实验探究', '理论拓展']
        },
        '化学': {
            'beginner': ['元素周期表', '基础化学反应', '简单实验'],
            'basic': ['化学反应方程式', '计算题练习', '实验观察'],
            'intermediate': ['化学平衡', '有机化学', '实验设计'],
            'advanced': ['竞赛题练习', '实验探究', '理论研究']
        }
    }
    
    return activities_map.get(subject, activities_map['数学']).get(level, ['学习', '练习'])


def generate_target_score(level):
    targets = {
        'beginner': 60,
        'basic': 75,
        'intermediate': 85,
        'advanced': 95
    }
    return targets.get(level, 70)


def auto_grade_homework(submission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM homework_submissions WHERE id = ?
    ''', (submission_id,))
    submission = cursor.fetchone()
    
    if not submission:
        conn.close()
        return None
    
    cursor.execute('''
        SELECT * FROM homework_answers WHERE submission_id = ?
    ''', (submission_id,))
    answers = cursor.fetchall()
    
    cursor.execute('''
        SELECT * FROM homework_questions WHERE homework_id = ?
    ''', (submission['homework_id'],))
    questions = cursor.fetchall()
    
    question_map = {q['id']: q for q in questions}
    
    total_score = 0
    max_score = 0
    feedback_items = []
    
    for answer in answers:
        question = question_map.get(answer['question_id'])
        if question:
            max_score += question['score'] or 0
            
            user_answer = answer['answer_text'] or ''
            correct_answer = question['correct_answer'] or ''
            
            if user_answer.strip().lower() == correct_answer.strip().lower():
                score = question['score'] or 0
                feedback_items.append({
                    'question_id': question['id'],
                    'question_text': question['question_text'],
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'score': score,
                    'is_correct': True,
                    'feedback': '回答正确！'
                })
            else:
                score = 0
                feedback_items.append({
                    'question_id': question['id'],
                    'question_text': question['question_text'],
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'score': score,
                    'is_correct': False,
                    'feedback': f'回答错误。正确答案是：{correct_answer}。建议复习相关知识点。'
                })
            
            total_score += score
    
    percentage = round(total_score / max_score * 100, 2) if max_score > 0 else 0
    
    cursor.execute('''
        UPDATE homework_submissions 
        SET status = 'graded', score = ?, graded_at = ?
        WHERE id = ?
    ''', (percentage, datetime.now().isoformat(), submission_id))
    
    for answer in answers:
        q_id = answer['question_id']
        item = next((f for f in feedback_items if f['question_id'] == q_id), None)
        if item:
            cursor.execute('''
                UPDATE homework_answers 
                SET score = ?, ai_feedback = ?
                WHERE id = ?
            ''', (item['score'], item['feedback'], answer['id']))
    
    conn.commit()
    conn.close()
    
    return {
        'submission_id': submission_id,
        'total_score': round(percentage, 2),
        'max_score': max_score,
        'correct_count': len([f for f in feedback_items if f['is_correct']]),
        'wrong_count': len([f for f in feedback_items if not f['is_correct']]),
        'feedback_items': feedback_items,
        'overall_comment': generate_overall_comment(percentage),
        'graded_at': datetime.now().isoformat()
    }


def generate_overall_comment(score):
    if score >= 90:
        return '作业完成优秀！继续保持！'
    elif score >= 80:
        return '作业完成良好，还有提升空间。'
    elif score >= 70:
        return '作业完成一般，需要加强练习。'
    elif score >= 60:
        return '刚刚及格，需要更加努力。'
    else:
        return '作业完成较差，建议寻求老师帮助。'


def track_learning_progress(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, AVG(score) as avg_score, COUNT(*) as count
        FROM exam_results WHERE user_id = ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC LIMIT 14
    ''', (user_id,))
    exam_trend = cursor.fetchall()
    
    cursor.execute('''
        SELECT DATE(submission_time) as date, AVG(score) as avg_score, COUNT(*) as count
        FROM homework_submissions WHERE student_id = ? AND status = 'graded'
        GROUP BY DATE(submission_time)
        ORDER BY date DESC LIMIT 14
    ''', (str(user_id),))
    homework_trend = cursor.fetchall()
    
    cursor.execute('''
        SELECT DATE(created_at) as date, 
               SUM(CASE WHEN is_wrong = 0 THEN 1 ELSE 0 END) as correct,
               SUM(CASE WHEN is_wrong = 1 THEN 1 ELSE 0 END) as wrong
        FROM user_answers WHERE user_id = ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC LIMIT 14
    ''', (user_id,))
    answer_trend = cursor.fetchall()
    
    conn.close()
    
    return {
        'user_id': user_id,
        'exam_trend': {
            'labels': [r['date'] for r in reversed(exam_trend)],
            'scores': [round(r['avg_score'], 2) if r['avg_score'] else 0 for r in reversed(exam_trend)],
            'counts': [r['count'] for r in reversed(exam_trend)]
        },
        'homework_trend': {
            'labels': [r['date'] for r in reversed(homework_trend)],
            'scores': [round(r['avg_score'], 2) if r['avg_score'] else 0 for r in reversed(homework_trend)],
            'counts': [r['count'] for r in reversed(homework_trend)]
        },
        'answer_trend': {
            'labels': [r['date'] for r in reversed(answer_trend)],
            'correct': [r['correct'] for r in reversed(answer_trend)],
            'wrong': [r['wrong'] for r in reversed(answer_trend)]
        },
        'generated_at': datetime.now().isoformat()
    }


def generate_personalized_recommendations(user_id):
    student_level = analyze_student_level(user_id)
    weak_subjects = []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT subject, AVG(score) as avg_score 
        FROM exam_results WHERE user_id = ?
        GROUP BY subject
        ORDER BY avg_score ASC
    ''', (user_id,))
    subject_scores = cursor.fetchall()
    
    for row in subject_scores:
        if row['avg_score'] < 80:
            weak_subjects.append({
                'subject': row['subject'],
                'avg_score': round(row['avg_score'], 2),
                'priority': 'high' if row['avg_score'] < 60 else 'medium'
            })
    
    cursor.execute('''
        SELECT q.id, q.subject, q.question_text, q.difficulty
        FROM user_answers ua
        LEFT JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_wrong = 1
        GROUP BY q.id
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ''', (user_id,))
    frequent_wrong = cursor.fetchall()
    
    conn.close()
    
    recommendations = []
    
    for ws in weak_subjects:
        recommendations.append({
            'type': 'subject',
            'subject': ws['subject'],
            'avg_score': ws['avg_score'],
            'priority': ws['priority'],
            'action': f'加强{ws["subject"]}学习，建议每天学习{1 if ws["priority"] == "high" else 0.5}小时',
            'resources': generate_resource_suggestions(ws['subject'])
        })
    
    for q in frequent_wrong[:5]:
        recommendations.append({
            'type': 'question',
            'question_id': q['id'],
            'subject': q['subject'],
            'difficulty': q['difficulty'],
            'priority': 'high',
            'action': f'重做错题ID:{q["id"]}，分析错误原因',
            'resources': []
        })
    
    return {
        'user_id': user_id,
        'student_level': student_level,
        'weak_subjects': weak_subjects,
        'recommendations': recommendations,
        'total_recommendations': len(recommendations),
        'generated_at': datetime.now().isoformat()
    }


def generate_resource_suggestions(subject):
    resources_map = {
        '数学': ['基础教材', '习题集', '在线课程', '数学思维训练'],
        '英语': ['单词书', '语法书', '阅读材料', '听力练习'],
        '物理': ['实验手册', '公式手册', '例题集', '科普读物'],
        '化学': ['实验视频', '方程式手册', '习题集', '科普读物']
    }
    return resources_map.get(subject, ['相关教材', '习题集', '在线课程'])


@ai_auto_learning_api.route('/api/ai/auto/learning_plan', methods=['GET'])
@require_login
def learning_plan():
    try:
        user_id = session.get('user_id')
        data = request.args
        duration = int(data.get('duration', 7))
        
        plan = generate_learning_plan(user_id, duration)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_plans (user_id, plan_data, duration_days, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(plan), duration, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=plan, message='AI自动学习计划生成完成')
    
    except Exception as e:
        logger.error(f'AI自动学习计划生成失败: {e}')
        return APIResponse.error(message=f'AI自动学习计划生成失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/analyze_level', methods=['GET'])
@require_login
def analyze_level():
    try:
        user_id = session.get('user_id')
        level = analyze_student_level(user_id)
        
        return APIResponse.success(data=level, message='AI学情分析完成')
    
    except Exception as e:
        logger.error(f'AI学情分析失败: {e}')
        return APIResponse.error(message=f'AI学情分析失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/grade_homework/<int:submission_id>', methods=['POST'])
@require_login
def grade_homework(submission_id):
    try:
        result = auto_grade_homework(submission_id)
        
        if not result:
            return APIResponse.not_found(message='作业提交不存在')
        
        return APIResponse.success(data=result, message='AI自动批改完成')
    
    except Exception as e:
        logger.error(f'AI自动批改失败: {e}')
        return APIResponse.error(message=f'AI自动批改失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/track_progress', methods=['GET'])
@require_login
def track_progress():
    try:
        user_id = session.get('user_id')
        progress = track_learning_progress(user_id)
        
        return APIResponse.success(data=progress, message='AI学习进度追踪完成')
    
    except Exception as e:
        logger.error(f'AI学习进度追踪失败: {e}')
        return APIResponse.error(message=f'AI学习进度追踪失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/recommendations', methods=['GET'])
@require_login
def recommendations():
    try:
        user_id = session.get('user_id')
        recs = generate_personalized_recommendations(user_id)
        
        return APIResponse.success(data=recs, message='AI个性化推荐生成完成')
    
    except Exception as e:
        logger.error(f'AI个性化推荐生成失败: {e}')
        return APIResponse.error(message=f'AI个性化推荐生成失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/learning_cycle', methods=['POST'])
@require_login
def learning_cycle():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        action = data.get('action', '')
        
        cycle_result = {
            'user_id': user_id,
            'action': action,
            'steps': [],
            'result': {},
            'generated_at': datetime.now().isoformat()
        }
        
        if action == 'complete':
            level = analyze_student_level(user_id)
            cycle_result['steps'].append({'step': 'analyze', 'status': 'completed', 'data': level})
            
            recommendations = generate_personalized_recommendations(user_id)
            cycle_result['steps'].append({'step': 'recommend', 'status': 'completed', 'data': recommendations})
            
            plan = generate_learning_plan(user_id, 7)
            cycle_result['steps'].append({'step': 'plan', 'status': 'completed', 'data': plan})
            
            cycle_result['result'] = {
                'message': '学习闭环完成',
                'next_action': '按照学习计划进行学习',
                'estimated_time': plan['estimated_hours']
            }
        
        elif action == 'diagnose':
            level = analyze_student_level(user_id)
            recommendations = generate_personalized_recommendations(user_id)
            
            cycle_result['steps'].append({'step': 'diagnose', 'status': 'completed'})
            cycle_result['steps'].append({'step': 'analyze', 'status': 'completed', 'data': level})
            cycle_result['steps'].append({'step': 'recommend', 'status': 'completed', 'data': recommendations})
            
            cycle_result['result'] = {
                'message': '学情诊断完成',
                'weak_points': recommendations['weak_subjects'],
                'recommendation_count': recommendations['total_recommendations']
            }
        
        else:
            cycle_result['steps'].append({'step': 'unknown', 'status': 'failed'})
            cycle_result['result'] = {'message': '未知操作'}
        
        return APIResponse.success(data=cycle_result, message='AI学习闭环执行完成')
    
    except Exception as e:
        logger.error(f'AI学习闭环执行失败: {e}')
        return APIResponse.error(message=f'AI学习闭环执行失败: {str(e)}')


@ai_auto_learning_api.route('/api/ai/auto/class_analysis', methods=['GET'])
@require_admin
def class_analysis():
    try:
        data = request.args
        cls = data.get('class', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if cls:
            cursor.execute('''
                SELECT u.id FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                WHERE s.class_name = ? AND u.role = 'student'
            ''', (cls,))
        else:
            cursor.execute('''
                SELECT u.id FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                WHERE u.role = 'student'
            ''')
        
        students = cursor.fetchall()
        
        class_analysis = {
            'class_name': cls or '全部',
            'total_students': len(students),
            'level_distribution': {'beginner': 0, 'basic': 0, 'intermediate': 0, 'advanced': 0},
            'avg_score': 0,
            'avg_accuracy': 0,
            'weak_subjects': [],
            'students': [],
            'generated_at': datetime.now().isoformat()
        }
        
        total_score = 0
        total_accuracy = 0
        subject_scores = {}
        
        for student in students:
            level = analyze_student_level(student['id'])
            class_analysis['level_distribution'][level['level']] += 1
            
            if level['avg_score'] > 0:
                total_score += level['avg_score']
            if level['accuracy'] > 0:
                total_accuracy += level['accuracy']
            
            class_analysis['students'].append({
                'user_id': student['id'],
                'level': level['level'],
                'level_desc': level['level_desc'],
                'avg_score': level['avg_score'],
                'accuracy': level['accuracy']
            })
        
        if students:
            class_analysis['avg_score'] = round(total_score / len(students), 2)
            class_analysis['avg_accuracy'] = round(total_accuracy / len(students), 2)
        
        conn.close()
        
        return APIResponse.success(data=class_analysis, message='AI班级学情分析完成')
    
    except Exception as e:
        logger.error(f'AI班级学情分析失败: {e}')
        return APIResponse.error(message=f'AI班级学情分析失败: {str(e)}')


def init_auto_learning_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_data TEXT,
                duration_days INTEGER DEFAULT 7,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                progress_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recommendation_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info('AI自动化学习系统表结构创建完成')
    except Exception as e:
        logger.error(f'AI自动化学习系统表结构创建失败: {e}')


init_auto_learning_tables()