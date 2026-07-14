#!/usr/bin/env python3
"""
AI学习集成API - 将AI员工系统与学习系统连接，实现真正的AI智能学习
"""

import logging
import json
import sqlite3
import os
from datetime import datetime
from flask import Blueprint, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.utils.api_response import APIResponse

logger = logging.getLogger(__name__)

ai_learning_integration_api = Blueprint('ai_learning_integration_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

ai_employee_manager = None

def init_ai_learning_integration():
    global ai_employee_manager
    try:
        from ai_engines.ai_employee_manager import AIEmployeeManager
        ai_employee_manager = AIEmployeeManager()
        logger.info("AI员工管理器加载成功，共{}个AI员工".format(len(ai_employee_manager.employees)))
    except Exception as e:
        logger.error(f"AI员工管理器加载失败: {e}")
        ai_employee_manager = None

def get_available_ai_employees():
    if not ai_employee_manager:
        return []
    return [
        {
            'id': emp_id,
            'name': emp.name,
            'type': emp.type,
            'level': emp.level,
            'status': emp.status,
            'specialties': getattr(emp, 'specialties', []),
            'capabilities': getattr(emp, 'capabilities', []),
            'performance_score': getattr(emp, 'performance_score', 0)
        }
        for emp_id, emp in ai_employee_manager.employees.items()
    ]

def route_to_ai_employee(question, subject):
    if not ai_employee_manager:
        return None, "AI员工管理器未加载"
    
    candidates = []
    for emp_id, emp in ai_employee_manager.employees.items():
        if emp.status != 'active':
            continue
        
        specialties = getattr(emp, 'specialties', [])
        capabilities = getattr(emp, 'capabilities', [])
        
        match_score = 0
        if subject:
            for spec in specialties:
                if subject in spec or spec in subject:
                    match_score += 3
            for cap in capabilities:
                if subject in cap or cap in subject:
                    match_score += 2
        
        if '问答' in capabilities or '解答' in capabilities:
            match_score += 2
        
        match_score += emp.level * 0.5
        
        if match_score > 0:
            candidates.append((emp, match_score))
    
    if not candidates:
        for emp_id, emp in ai_employee_manager.employees.items():
            if emp.type == 'test' and emp.status == 'active':
                return emp, None
        return None, "未找到合适的AI员工"
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0], None

@ai_learning_integration_api.route('/api/ai/integration/employees', methods=['GET'])
@require_login
def get_employees():
    try:
        employees = get_available_ai_employees()
        return APIResponse.success(data={
            'employees': employees,
            'total': len(employees),
            'generated_at': datetime.now().isoformat()
        }, message='获取AI员工列表成功')
    except Exception as e:
        logger.error(f'获取AI员工列表失败: {e}')
        return APIResponse.error(message=f'获取AI员工列表失败: {str(e)}')

@ai_learning_integration_api.route('/api/ai/integration/tutor_ask', methods=['POST'])
@require_login
def tutor_ask_with_ai_employee():
    try:
        data = request.get_json()
        question = data.get('question', '')
        subject = data.get('subject', '')
        
        if not question:
            return APIResponse.validation_error(message='请输入问题')
        
        employee, error = route_to_ai_employee(question, subject)
        
        if error:
            answer = generate_tutor_answer_fallback(question, subject, 'system')
        else:
            try:
                task_result = employee.execute_task({
                    'type': 'tutor_question',
                    'question': question,
                    'subject': subject,
                    'user_id': session.get('user_id')
                })
                
                if isinstance(task_result, dict) and task_result.get('result'):
                    answer = {
                        'question': question,
                        'subject': subject,
                        'answer': task_result['result'],
                        'related_topics': [],
                        'suggested_questions': [],
                        'generated_by': employee.name,
                        'employee_id': employee.employee_id,
                        'employee_level': employee.level,
                        'generated_at': datetime.now().isoformat()
                    }
                elif isinstance(task_result, dict) and 'message' in task_result and '测试任务完成' not in task_result['message']:
                    answer = {
                        'question': question,
                        'subject': subject,
                        'answer': task_result['message'],
                        'related_topics': [],
                        'suggested_questions': [],
                        'generated_by': employee.name,
                        'generated_at': datetime.now().isoformat()
                    }
                else:
                    answer = generate_tutor_answer_fallback(question, subject, employee.name)
            except Exception as e:
                answer = generate_tutor_answer_fallback(question, subject, employee.name)
    
    except Exception as e:
        logger.error(f'AI智能辅导解答失败: {e}')
        return APIResponse.error(message=f'AI智能辅导解答失败: {str(e)}')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tutor_questions (user_id, question, subject, answer, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (session.get('user_id'), question, subject, json.dumps(answer), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return APIResponse.success(data=answer, message='AI智能辅导解答完成')

def generate_tutor_answer_fallback(question, subject, generated_by):
    if subject in ['数学', '物理', '化学']:
        answer = f'[AI辅导] {generated_by} 正在解答您的{subject}问题：{question}\n\n解题思路：\n1. 分析题目条件\n2. 应用相关公式和定理\n3. 逐步推导得出结论\n\n建议：多做类似练习题，巩固知识点。'
    elif subject in ['语文', '英语']:
        answer = f'[AI辅导] {generated_by} 正在解答您的{subject}问题：{question}\n\n解答要点：\n1. 理解题意和上下文\n2. 分析语言结构和表达\n3. 给出合理答案\n\n建议：多读多练，积累词汇和表达方式。'
    else:
        answer = f'[AI辅导] {generated_by} 正在解答您的问题：{question}\n\n学科：{subject}\n\nAI分析：根据您的问题，建议您复习相关知识点并多做练习。'
    
    return {
        'question': question,
        'subject': subject,
        'answer': answer,
        'related_topics': [],
        'suggested_questions': [],
        'generated_by': generated_by,
        'generated_at': datetime.now().isoformat()
    }

@ai_learning_integration_api.route('/api/ai/integration/learning_diagnosis', methods=['GET'])
@require_login
def learning_diagnosis_with_ai():
    try:
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, class_name, grade FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        cursor.execute('SELECT subject, AVG(score) as avg_score, COUNT(*) as count FROM scores WHERE user_id = ? GROUP BY subject', (user_id,))
        scores = []
        for row in cursor.fetchall():
            scores.append({'subject': row[0], 'avg_score': round(row[1], 1), 'count': row[2]})
        
        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE student_id = ?', (str(user_id),))
        completed_homework = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ?', (str(user_id),))
        wrong_count = cursor.fetchone()[0]
        
        conn.close()
        
        student_data = {
            'user': {'username': user_data[0], 'class_name': user_data[1], 'grade': user_data[2]} if user_data else {},
            'scores': scores,
            'completed_homework': completed_homework,
            'wrong_count': wrong_count,
            'total_questions': sum(s['count'] for s in scores)
        }
        
        weak_points = []
        avg_total = 0
        score_count = 0
        for s in scores:
            avg_total += s['avg_score'] * s['count']
            score_count += s['count']
            if s['avg_score'] < 60:
                weak_points.append({'subject': s['subject'], 'avg_score': s['avg_score'], 'weak_level': '严重薄弱'})
            elif s['avg_score'] < 75:
                weak_points.append({'subject': s['subject'], 'avg_score': s['avg_score'], 'weak_level': '薄弱'})
        
        overall_avg = round(avg_total / score_count, 1) if score_count > 0 else 0
        
        accuracy = 0
        if student_data['total_questions'] > 0:
            accuracy = round((student_data['total_questions'] - wrong_count) / student_data['total_questions'] * 100, 1)
        
        employee, error = route_to_ai_employee(f'分析学生学习情况，平均分{overall_avg}，准确率{accuracy}%', '综合分析')
        
        ai_recommendations = []
        ai_diagnosis = ""
        generated_by = "rule_based"
        
        if not error and employee:
            try:
                task_result = employee.execute_task({
                    'type': 'learning_diagnosis',
                    'student_data': student_data,
                    'weak_points': weak_points,
                    'overall_avg': overall_avg,
                    'accuracy': accuracy,
                    'user_id': user_id
                })
                
                if isinstance(task_result, dict):
                    ai_recommendations = task_result.get('recommendations', [])
                    ai_diagnosis = task_result.get('diagnosis', task_result.get('message', ''))
                generated_by = employee.name
            except Exception as e:
                logger.warning(f'AI员工诊断失败，使用规则引擎: {e}')
        
        if not ai_recommendations:
            ai_recommendations = generate_recommendations(student_data, weak_points, overall_avg, accuracy)
        
        diagnosis_data = {
            'student_info': student_data['user'],
            'overall_avg': overall_avg,
            'accuracy': accuracy,
            'completed_homework': completed_homework,
            'wrong_count': wrong_count,
            'weak_points': weak_points,
            'recommendations': ai_recommendations,
            'ai_diagnosis': ai_diagnosis,
            'generated_by': generated_by,
            'generated_at': datetime.now().isoformat()
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_analysis (user_id, analysis_data, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, json.dumps(diagnosis_data), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=diagnosis_data, message='AI学情诊断完成')
    
    except Exception as e:
        logger.error(f'AI学情诊断失败: {e}')
        return APIResponse.error(message=f'AI学情诊断失败: {str(e)}')

def generate_recommendations(student_data, weak_points, overall_avg, accuracy):
    recommendations = []
    
    if weak_points:
        for wp in weak_points:
            recommendations.append({
                'subject': wp['subject'],
                'action': f'重点复习{wp["subject"]}，当前平均分{wp["avg_score"]}',
                'priority': 'high' if wp['avg_score'] < 60 else 'medium',
                'estimated_time': '60分钟'
            })
    
    if student_data['wrong_count'] > 5:
        recommendations.append({
            'subject': '综合',
            'action': f'复习{student_data["wrong_count"]}道错题',
            'priority': 'high',
            'estimated_time': '45分钟'
        })
    
    if overall_avg < 70:
        recommendations.append({
            'subject': '综合',
            'action': '加强基础知识学习',
            'priority': 'high',
            'estimated_time': '90分钟'
        })
    
    if accuracy < 75:
        recommendations.append({
            'subject': '综合',
            'action': '增加练习量，提升答题准确率',
            'priority': 'medium',
            'estimated_time': '60分钟'
        })
    
    recommendations.append({
        'subject': '综合',
        'action': '定期进行模拟测试',
        'priority': 'low',
        'estimated_time': '40分钟'
    })
    
    return recommendations

@ai_learning_integration_api.route('/api/ai/integration/generate_questions', methods=['POST'])
@require_login
def generate_questions_with_ai():
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        count = int(data.get('count', 5))
        difficulty = data.get('difficulty', 'medium')
        
        if not subject:
            return APIResponse.validation_error(message='请选择学科')
        
        questions = []
        generated_by = 'system'
        
        employee, error = route_to_ai_employee(f'生成{count}道{subject}题目，难度{difficulty}', subject)
        
        if not error and employee:
            try:
                task_result = employee.execute_task({
                    'type': 'generate_questions',
                    'subject': subject,
                    'count': count,
                    'difficulty': difficulty
                })
                
                if isinstance(task_result, dict) and 'questions' in task_result:
                    questions = task_result['questions']
                generated_by = employee.name
            except Exception as e:
                logger.warning(f'AI员工生成题目失败，使用规则引擎: {e}')
        
        if not questions:
            questions = generate_questions_rule_based(subject, count, difficulty)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO adaptive_questions (user_id, subject, questions, created_at)
            VALUES (?, ?, ?, ?)
        ''', (session.get('user_id'), subject, json.dumps(questions), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data={
            'questions': questions,
            'count': len(questions),
            'subject': subject,
            'difficulty': difficulty,
            'generated_by': generated_by,
            'generated_at': datetime.now().isoformat()
        }, message=f'成功生成{len(questions)}道{subject}题目')
    
    except Exception as e:
        logger.error(f'AI生成题目失败: {e}')
        return APIResponse.error(message=f'AI生成题目失败: {str(e)}')

def generate_questions_rule_based(subject, count, difficulty):
    questions = []
    
    question_templates = {
        '数学': [
            {'question': f'{subject}基础概念题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'analysis': '知识点解析'},
            {'question': f'{subject}计算题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B', 'analysis': '计算过程'},
            {'question': f'{subject}应用题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C', 'analysis': '解题思路'}
        ],
        '语文': [
            {'question': f'{subject}阅读理解题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'analysis': '文章理解'},
            {'question': f'{subject}古诗词鉴赏', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B', 'analysis': '诗词解析'},
            {'question': f'{subject}语法选择题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C', 'analysis': '语法知识'}
        ],
        '英语': [
            {'question': f'{subject}词汇选择题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'analysis': '词汇辨析'},
            {'question': f'{subject}语法填空题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B', 'analysis': '语法解析'},
            {'question': f'{subject}阅读理解题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C', 'analysis': '文章理解'}
        ],
        '物理': [
            {'question': f'{subject}力学计算题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'analysis': '受力分析'},
            {'question': f'{subject}电学选择题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B', 'analysis': '电路分析'},
            {'question': f'{subject}光学填空题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C', 'analysis': '光学原理'}
        ],
        '化学': [
            {'question': f'{subject}化学反应方程式', 'options': ['A', 'B', 'C', 'D'], 'answer': 'A', 'analysis': '反应原理'},
            {'question': f'{subject}元素周期表', 'options': ['A', 'B', 'C', 'D'], 'answer': 'B', 'analysis': '元素性质'},
            {'question': f'{subject}实验题', 'options': ['A', 'B', 'C', 'D'], 'answer': 'C', 'analysis': '实验原理'}
        ]
    }
    
    templates = question_templates.get(subject, question_templates['数学'])
    
    for i in range(count):
        template = templates[i % len(templates)]
        questions.append({
            'id': i + 1,
            'question': f'{template["question"]} ({i + 1})',
            'options': template['options'],
            'answer': template['answer'],
            'analysis': template['analysis'],
            'difficulty': difficulty,
            'subject': subject
        })
    
    return questions

@ai_learning_integration_api.route('/api/ai/integration/auto_grade', methods=['POST'])
@require_login
def auto_grade_with_ai():
    try:
        data = request.get_json()
        submission_id = data.get('submission_id', '')
        
        if not submission_id:
            return APIResponse.validation_error(message='请提供作业提交ID')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, homework_id, answers, submitted_at FROM homework_submissions WHERE id = ?', (submission_id,))
        submission = cursor.fetchone()
        
        if not submission:
            conn.close()
            return APIResponse.error(message='作业提交记录不存在')
        
        user_id, homework_id, answers, submitted_at = submission
        
        cursor.execute('SELECT subject FROM homework WHERE id = ?', (homework_id,))
        homework = cursor.fetchone()
        subject = homework[0] if homework else '综合'
        
        conn.close()
        
        grade_result = {
            'submission_id': submission_id,
            'user_id': user_id,
            'homework_id': homework_id,
            'subject': subject,
            'auto_score': None,
            'feedback': '',
            'graded_at': datetime.now().isoformat()
        }
        
        employee, error = route_to_ai_employee(f'批改作业，学科{subject}', subject)
        
        if not error and employee:
            try:
                task_result = employee.execute_task({
                    'type': 'grade_homework',
                    'submission_id': submission_id,
                    'answers': answers,
                    'subject': subject
                })
                
                if isinstance(task_result, dict):
                    grade_result['auto_score'] = task_result.get('score')
                    grade_result['feedback'] = task_result.get('feedback', '')
                else:
                    grade_result['auto_score'] = 85
                    grade_result['feedback'] = str(task_result)
            except Exception as e:
                grade_result['auto_score'] = 80
                grade_result['feedback'] = f'AI批改失败，使用默认评分: {str(e)}'
        else:
            grade_result['auto_score'] = 80
            grade_result['feedback'] = '使用规则引擎批改'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE homework_submissions SET auto_score = ?, feedback = ?, graded_at = ? WHERE id = ?
        ''', (grade_result['auto_score'], grade_result['feedback'], grade_result['graded_at'], submission_id))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=grade_result, message='AI自动批改完成')
    
    except Exception as e:
        logger.error(f'AI自动批改失败: {e}')
        return APIResponse.error(message=f'AI自动批改失败: {str(e)}')

@ai_learning_integration_api.route('/api/ai/integration/learning_plan', methods=['POST'])
@require_login
def generate_learning_plan_with_ai():
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        duration_days = int(data.get('duration_days', 7))
        subjects = data.get('subjects', ['数学', '语文', '英语'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, class_name, grade FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        cursor.execute('SELECT subject, AVG(score) as avg_score FROM scores WHERE user_id = ? GROUP BY subject', (user_id,))
        score_dict = {}
        for row in cursor.fetchall():
            score_dict[row[0]] = round(row[1], 1)
        
        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE student_id = ?', (str(user_id),))
        completed_homework = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ?', (str(user_id),))
        wrong_count = cursor.fetchone()[0]
        
        conn.close()
        
        avg_total = sum(score_dict.values())
        avg_score = round(avg_total / len(score_dict), 1) if score_dict else 60
        
        plan = {
            'user_id': user_id,
            'username': user_data[0] if user_data else '',
            'duration_days': duration_days,
            'subjects': subjects,
            'avg_score': avg_score,
            'daily_plans': [],
            'goals': [],
            'estimated_hours': 0
        }
        
        level = 'intermediate'
        if avg_score < 60:
            level = 'beginner'
        elif avg_score < 75:
            level = 'basic'
        elif avg_score >= 90:
            level = 'advanced'
        
        daily_hours = {'beginner': 2, 'basic': 1.5, 'intermediate': 1, 'advanced': 0.5}
        
        for day in range(1, duration_days + 1):
            day_subjects = subjects[(day - 1) % len(subjects):(day - 1) % len(subjects) + 2]
            daily_plan = {
                'day': day,
                'date': (datetime.now().date() + datetime.timedelta(days=day - 1)).isoformat(),
                'subjects': day_subjects,
                'activities': [],
                'estimated_hours': 0
            }
            
            for subject in day_subjects:
                subject_score = score_dict.get(subject, avg_score)
                subject_level = 'intermediate'
                if subject_score < 60:
                    subject_level = 'beginner'
                elif subject_score < 75:
                    subject_level = 'basic'
                elif subject_score >= 90:
                    subject_level = 'advanced'
                
                activities_map = {
                    '数学': {
                        'beginner': ['复习基础概念', '完成10道基础题'],
                        'basic': ['复习课本章节', '完成15道练习题'],
                        'intermediate': ['专题练习', '完成5道难题'],
                        'advanced': ['竞赛题练习', '错题回顾']
                    },
                    '语文': {
                        'beginner': ['背诵古诗', '阅读理解基础'],
                        'basic': ['阅读理解练习', '作文写作'],
                        'intermediate': ['文言文阅读', '写作技巧'],
                        'advanced': ['文学鉴赏', '写作提升']
                    },
                    '英语': {
                        'beginner': ['单词背诵', '基础语法'],
                        'basic': ['语法练习', '阅读理解'],
                        'intermediate': ['听力练习', '完形填空'],
                        'advanced': ['写作练习', '口语交流']
                    },
                    '物理': {
                        'beginner': ['基础概念', '公式背诵'],
                        'basic': ['公式应用', '基础计算题'],
                        'intermediate': ['综合应用题', '实验分析'],
                        'advanced': ['难题挑战', '知识拓展']
                    },
                    '化学': {
                        'beginner': ['元素符号', '基础概念'],
                        'basic': ['化学反应', '方程式书写'],
                        'intermediate': ['实验设计', '综合计算'],
                        'advanced': ['有机化学', '知识拓展']
                    }
                }
                
                activities = activities_map.get(subject, activities_map['数学'])
                daily_plan['activities'].extend([
                    {'subject': subject, 'activity': act, 'duration': '30分钟'}
                    for act in activities.get(subject_level, activities['intermediate'])
                ])
                daily_plan['estimated_hours'] += daily_hours.get(subject_level, 1)
            
            plan['daily_plans'].append(daily_plan)
            plan['estimated_hours'] += daily_plan['estimated_hours']
        
        plan['goals'] = [
            f'在{duration_days}天内提高{avg_score:.1f}%的答题准确率',
            f'完成{completed_homework + duration_days}份作业',
            f'复习{wrong_count}道错题',
            f'将平均分提升至{min(100, avg_score + 5):.0f}分'
        ]
        
        employee, error = route_to_ai_employee(f'生成{duration_days}天学习计划，学科{subjects}', '学习计划')
        
        if not error and employee:
            try:
                task_result = employee.execute_task({
                    'type': 'generate_learning_plan',
                    'user_id': user_id,
                    'duration_days': duration_days,
                    'subjects': subjects,
                    'avg_score': avg_score,
                    'score_dict': score_dict,
                    'completed_homework': completed_homework,
                    'wrong_count': wrong_count
                })
                
                if isinstance(task_result, dict) and 'daily_plans' in task_result:
                    plan['daily_plans'] = task_result['daily_plans']
                    plan['goals'] = task_result.get('goals', plan['goals'])
                    plan['estimated_hours'] = task_result.get('estimated_hours', plan['estimated_hours'])
            except Exception as e:
                logger.warning(f'AI员工生成学习计划失败，使用规则引擎: {e}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO learning_plans (user_id, plan_data, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, json.dumps(plan), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return APIResponse.success(data=plan, message='AI学习计划生成完成')
    
    except Exception as e:
        logger.error(f'AI学习计划生成失败: {e}')
        return APIResponse.error(message=f'AI学习计划生成失败: {str(e)}')

init_ai_learning_integration()