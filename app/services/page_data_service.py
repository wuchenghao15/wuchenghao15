import sqlite3
import json
from datetime import datetime

DATABASE_PATH = 'app.db'

def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

def get_dashboard_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            stats['active_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            stats['exams_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            stats['questions_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exam_papers')
            stats['papers_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE status = 'completed'")
            stats['completed_exams'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login >= date('now')")
            stats['today_logins'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now')")
            stats['today_registers'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            stats['ai_employees_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE status = "active"')
            stats['active_ai_employees'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM growth_cycles')
            stats['growth_cycles_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE status = "pending"')
            stats['pending_errors'] = cursor.fetchone()[0]
            
    except Exception as e:
        stats = {
            'total_users': 0,
            'active_users': 0,
            'exams_count': 0,
            'questions_count': 0,
            'papers_count': 0,
            'completed_exams': 0,
            'today_logins': 0,
            'today_registers': 0,
            'ai_employees_count': 0,
            'active_ai_employees': 0,
            'growth_cycles_count': 0,
            'pending_errors': 0
        }
    return stats

def get_activity_list():
    activities = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT 'exam_result' as type, er.user_id, er.score, er.completed_at, u.username FROM exam_results er LEFT JOIN users u ON er.user_id = u.id ORDER BY er.completed_at DESC LIMIT 5 ''')
            for row in cursor.fetchall():
                activities.append({
                    'type': 'exam_result',
                    'user': row[4] or f'用户{row[1]}',
                    'action': f'完成考试，得分 {row[2]}分',
                    'time': row[3]
                })
            
            cursor.execute(''' SELECT u.id, u.username, u.created_at FROM users u ORDER BY u.created_at DESC LIMIT 3 ''')
            for row in cursor.fetchall():
                activities.append({
                    'type': 'user_register',
                    'user': row[1],
                    'action': '新用户注册',
                    'time': row[2]
                })
            
            activities.sort(key=lambda x: x['time'] if x['time'] else '', reverse=True)
            activities = activities[:8]
    except Exception:
        activities = []
    return activities

def get_system_alerts():
    alerts = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT id, error_type, error_message, created_at, status FROM error_logs WHERE status = 'pending' ORDER BY created_at DESC LIMIT 5 ''')
            for row in cursor.fetchall():
                alerts.append({
                    'type': row[1] or 'error',
                    'message': row[2],
                    'time': row[3],
                    'level': '紧急' if 'critical' in str(row[1]).lower() else '警告'
                })
            
            cursor.execute('SELECT COUNT(*) FROM error_logs WHERE status = "resolved"')
            resolved_count = cursor.fetchone()[0]
    except Exception:
        alerts = []
        resolved_count = 0
    return alerts, resolved_count

def get_ai_employee_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            stats['total_employees'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE status = "active"')
            stats['active_employees'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM growth_cycles')
            stats['growth_cycles'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(knowledge_base_size) FROM ai_employees')
            kb_size = cursor.fetchone()[0]
            stats['knowledge_base_size'] = kb_size or 0
            
            cursor.execute('SELECT SUM(total_thinking_sessions) FROM ai_employees')
            thinking = cursor.fetchone()[0]
            stats['thinking_sessions'] = thinking or 0
            
            cursor.execute('SELECT SUM(total_learning_hours) FROM ai_employees')
            learning = cursor.fetchone()[0]
            stats['learning_hours'] = learning or 0
            
            cursor.execute(''' SELECT role_name, COUNT(*) as count FROM ai_employees GROUP BY role_name ''')
            stats['roles'] = {}
            role_rows = cursor.fetchall()
            total_roles = sum(row[1] for row in role_rows) if role_rows else 1
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
            stats['role_distribution'] = []
            for i, row in enumerate(role_rows):
                percentage = round(row[1] / total_roles * 100) if total_roles > 0 else 0
                stats['role_distribution'].append({
                    'name': row[0],
                    'count': row[1],
                    'percentage': percentage,
                    'color': colors[i % len(colors)]
                })
                stats['roles'][row[0]] = row[1]
            
            cursor.execute(''' SELECT id, employee_id, name, role_name, status, skill_score, total_thinking_sessions, knowledge_base_size, created_at FROM ai_employees ORDER BY created_at DESC ''')
            stats['employees'] = []
            for row in cursor.fetchall():
                stats['employees'].append({
                    'id': row[0],
                    'employee_id': row[1],
                    'name': row[2],
                    'role_name': row[3],
                    'status': row[4],
                    'skill_score': row[5] or 0,
                    'thinking_sessions': row[6] or 0,
                    'knowledge_base_size': row[7] or 0,
                    'created_at': row[8]
                })
            
            cursor.execute(''' SELECT employee_id, employee_name, cycle_number, steps, created_at, CASE WHEN completed_at IS NOT NULL THEN 'completed' ELSE 'running' END as status FROM growth_cycles ORDER BY created_at DESC LIMIT 10 ''')
            stats['growth_history'] = []
            for row in cursor.fetchall():
                steps_info = row[3] or '[]'
                try:
                    steps_data = json.loads(steps_info)
                except:
                    steps_data = []
                stats['growth_history'].append({
                    'employee_id': row[0],
                    'employee_name': row[1],
                    'cycle_number': row[2],
                    'steps': steps_data,
                    'created_at': row[4],
                    'status': row[5]
                })
    except Exception:
        roles_data = {}
        total_roles = 0
        colors = []
        role_distribution = []
        stats = {
            'total_employees': 0,
            'active_employees': 0,
            'growth_cycles': 0,
            'knowledge_base_size': 0,
            'thinking_sessions': 0,
            'learning_hours': 0,
            'roles': {},
            'role_distribution': [],
            'employees': [],
            'growth_history': []
        }
    return stats

def get_cognitive_reasoning_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM reasoning_tasks')
            stats['total_tasks'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_base')
            stats['knowledge_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM reasoning_tasks WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM reasoning_tasks')
            total = cursor.fetchone()[0]
            stats['success_rate'] = f"{round(completed/total*100)}%" if total > 0 else '0%'
            
            cursor.execute('SELECT AVG(execution_time_ms) FROM reasoning_tasks WHERE execution_time_ms IS NOT NULL')
            avg_time = cursor.fetchone()[0]
            stats['avg_time'] = round(avg_time) if avg_time else 0
            
            cursor.execute(''' SELECT id, task_type, input_data, status, created_at FROM reasoning_tasks ORDER BY created_at DESC LIMIT 10 ''')
            stats['tasks'] = []
            for row in cursor.fetchall():
                stats['tasks'].append({
                    'id': row[0],
                    'task_type': row[1],
                    'input_data': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
                    'status': row[3],
                    'created_at': row[4]
                })
            
            cursor.execute(''' SELECT id, knowledge_type, content_summary, source_url, created_at FROM knowledge_base ORDER BY created_at DESC LIMIT 10 ''')
            stats['knowledge_items'] = []
            for row in cursor.fetchall():
                stats['knowledge_items'].append({
                    'id': row[0],
                    'knowledge_type': row[1],
                    'content_summary': row[2][:50] + '...' if len(row[2]) > 50 else row[2],
                    'source_url': row[3],
                    'created_at': row[4]
                })
    except Exception:
        stats = {
            'total_tasks': 0,
            'knowledge_count': 0,
            'success_rate': '0%',
            'avg_time': 0,
            'tasks': [],
            'knowledge_items': []
        }
    return stats

def get_adaptive_learning_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM learning_profiles')
            stats['total_profiles'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM learning_paths')
            stats['active_paths'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(progress) FROM learning_paths')
            avg_progress = cursor.fetchone()[0]
            stats['avg_progress'] = f"{round(avg_progress)}%" if avg_progress else '0%'
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_gaps')
            stats['gap_detections'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, user_id, learning_style, preferences_json, created_at FROM learning_profiles ORDER BY created_at DESC LIMIT 10 ''')
            stats['profiles'] = []
            for row in cursor.fetchall():
                prefs = row[3] or '{}'
                try:
                    prefs_data = json.loads(prefs)
                except:
                    prefs_data = {}
                stats['profiles'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'learning_style': row[2],
                    'preferences': prefs_data,
                    'created_at': row[4]
                })
            
            cursor.execute(''' SELECT id, user_id, path_name, progress, status, created_at FROM learning_paths ORDER BY created_at DESC LIMIT 10 ''')
            stats['paths'] = []
            for row in cursor.fetchall():
                stats['paths'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'path_name': row[2],
                    'progress': row[3] or 0,
                    'status': row[4],
                    'created_at': row[5]
                })
    except Exception:
        stats = {
            'total_profiles': 0,
            'active_paths': 0,
            'avg_progress': '0%',
            'gap_detections': 0,
            'profiles': [],
            'paths': []
        }
    return stats

def get_intelligent_qna_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM qa_pairs')
            stats['total_answers'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qa_conversations')
            stats['active_sessions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(response_time_ms) FROM qa_pairs')
            avg_response = cursor.fetchone()[0]
            stats['avg_response'] = round(avg_response) if avg_response else 0
            
            cursor.execute('SELECT COUNT(*) FROM qa_feedback')
            stats['feedback_count'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, question, answer, rating, created_at FROM qa_pairs ORDER BY created_at DESC LIMIT 10 ''')
            stats['qa_pairs'] = []
            for row in cursor.fetchall():
                stats['qa_pairs'].append({
                    'id': row[0],
                    'question': row[1][:50] + '...' if len(row[1]) > 50 else row[1],
                    'answer': row[2][:80] + '...' if len(row[2]) > 80 else row[2],
                    'rating': row[3] or 0,
                    'created_at': row[4]
                })
            
            cursor.execute(''' SELECT id, user_id, session_json, created_at FROM qa_conversations ORDER BY created_at DESC LIMIT 5 ''')
            stats['conversations'] = []
            for row in cursor.fetchall():
                session_data = row[2] or '{}'
                try:
                    session = json.loads(session_data)
                except:
                    session = {}
                stats['conversations'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'session': session,
                    'created_at': row[3]
                })
    except Exception:
        stats = {
            'total_answers': 0,
            'active_sessions': 0,
            'avg_response': 0,
            'feedback_count': 0,
            'qa_pairs': [],
            'conversations': []
        }
    return stats

def get_memory_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM memory_entries')
            stats['total_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memory_entries WHERE is_active = 1")
            stats['active_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM memory_relations')
            stats['relation_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT tag) FROM memory_tags')
            stats['tag_count'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, memory_type, content, importance_level, is_active, created_at FROM memory_entries ORDER BY created_at DESC LIMIT 20 ''')
            stats['memories'] = []
            for row in cursor.fetchall():
                stats['memories'].append({
                    'id': row[0],
                    'memory_type': row[1],
                    'content': row[2][:100] + '...' if len(row[2]) > 100 else row[2],
                    'importance_level': row[3],
                    'is_active': row[4],
                    'created_at': row[5]
                })
    except Exception:
        stats = {
            'total_count': 0,
            'active_count': 0,
            'relation_count': 0,
            'tag_count': 0,
            'memories': []
        }
    return stats

def get_emotion_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM emotion_records')
            stats['total_records'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM emotion_records')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emotion_alerts WHERE status = 'active'")
            stats['active_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emotion_interventions WHERE status = 'executed'")
            stats['executed_interventions'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, user_id, emotion_type, emotion_score, alert_level, created_at FROM emotion_alerts WHERE status = 'active' ORDER BY created_at DESC LIMIT 20 ''')
            stats['alerts'] = []
            for row in cursor.fetchall():
                stats['alerts'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'emotion_type': row[2],
                    'emotion_score': row[3],
                    'alert_level': row[4],
                    'created_at': row[5]
                })
            
            cursor.execute(''' SELECT id, user_id, emotion_type, emotion_score, analysis_json, created_at FROM emotion_records ORDER BY created_at DESC LIMIT 20 ''')
            stats['history'] = []
            for row in cursor.fetchall():
                analysis = row[4] or '{}'
                try:
                    analysis_data = json.loads(analysis)
                except:
                    analysis_data = {}
                stats['history'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'emotion_type': row[2],
                    'emotion_score': row[3],
                    'analysis': analysis_data,
                    'created_at': row[5]
                })
    except Exception:
        stats = {
            'total_records': 0,
            'total_users': 0,
            'active_alerts': 0,
            'executed_interventions': 0,
            'alerts': [],
            'history': []
        }
    return stats

def get_evaluation_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM evaluation_records')
            stats['total_evaluations'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM evaluation_records')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(final_score) FROM evaluation_records')
            avg_score = cursor.fetchone()[0]
            stats['average_score'] = round(avg_score) if avg_score else 0
            
            cursor.execute('SELECT COUNT(DISTINCT evaluation_type) FROM evaluation_records')
            stats['type_count'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, user_id, evaluation_type, final_score, grade, created_at FROM evaluation_records ORDER BY created_at DESC LIMIT 20 ''')
            stats['evaluations'] = []
            for row in cursor.fetchall():
                stats['evaluations'].append({
                    'id': row[0],
                    'user_id': row[1],
                    'evaluation_type': row[2],
                    'final_score': row[3],
                    'grade': row[4],
                    'created_at': row[5]
                })
    except Exception:
        stats = {
            'total_evaluations': 0,
            'total_users': 0,
            'average_score': 0,
            'type_count': 0,
            'evaluations': []
        }
    return stats

def get_ai_learning_dashboard_stats():
    cognitive = get_cognitive_reasoning_stats()
    adaptive = get_adaptive_learning_stats()
    qna = get_intelligent_qna_stats()
    memory = get_memory_stats()
    emotion = get_emotion_stats()
    evaluation = get_evaluation_stats()
    
    return {
        'total_memories': memory['total_count'],
        'active_alerts': emotion['active_alerts'],
        'total_evaluations': evaluation['total_evaluations'],
        'total_reasoning_tasks': cognitive['total_tasks'],
        'total_knowledge': cognitive['knowledge_count'],
        'total_profiles': adaptive['total_profiles'],
        'total_answers': qna['total_answers'],
        'cognitive': cognitive,
        'adaptive': adaptive,
        'qna': qna,
        'memory': memory,
        'emotion': emotion,
        'evaluation': evaluation
    }

def get_tutor_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM tutor_sessions')
            stats['total_sessions'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tutor_sessions WHERE status = 'active'")
            stats['active_students'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(session_duration_minutes) FROM tutor_sessions')
            avg_duration = cursor.fetchone()[0]
            stats['avg_session_duration'] = round(avg_duration) if avg_duration else 0
            
            cursor.execute("SELECT COUNT(*) FROM tutor_sessions WHERE status = 'completed'")
            stats['completed_sessions'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, student_name, tutor_type, status, session_duration_minutes, created_at FROM tutor_sessions ORDER BY created_at DESC LIMIT 10 ''')
            stats['recent_sessions'] = []
            for row in cursor.fetchall():
                stats['recent_sessions'].append({
                    'id': row[0],
                    'student_name': row[1],
                    'type': row[2],
                    'status': row[3],
                    'duration': row[4] or 0,
                    'timestamp': row[5]
                })
    except Exception:
        stats = {
            'total_sessions': 0,
            'active_students': 0,
            'avg_session_duration': 0,
            'completed_sessions': 0,
            'recent_sessions': []
        }
    return stats

def get_warning_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM warning_alerts')
            stats['total_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM warning_alerts WHERE status = 'active'")
            stats['active_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM warning_alerts WHERE status = 'resolved'")
            stats['resolved_alerts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM intervention_records')
            stats['interventions'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, alert_level, alert_message, created_at FROM warning_alerts WHERE status = 'active' ORDER BY created_at DESC LIMIT 10 ''')
            stats['active_alerts_list'] = []
            for row in cursor.fetchall():
                stats['active_alerts_list'].append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3]
                })
            
            cursor.execute(''' SELECT id, alert_id, intervention_type, intervention_content, status, created_at FROM intervention_records ORDER BY created_at DESC LIMIT 10 ''')
            stats['intervention_history'] = []
            for row in cursor.fetchall():
                stats['intervention_history'].append({
                    'id': row[0],
                    'alert_id': row[1],
                    'type': row[2],
                    'content': row[3],
                    'status': row[4],
                    'timestamp': row[5]
                })
    except Exception:
        stats = {
            'total_alerts': 0,
            'active_alerts': 0,
            'resolved_alerts': 0,
            'interventions': 0,
            'active_alerts_list': [],
            'intervention_history': []
        }
    return stats

def get_auto_learning_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM learning_jobs')
            stats['total_jobs'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_jobs WHERE status = 'running'")
            stats['running_jobs'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_jobs WHERE status = 'completed'")
            stats['completed_jobs'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(duration_hours) FROM learning_jobs')
            total_hours = cursor.fetchone()[0]
            stats['total_hours'] = round(total_hours) if total_hours else 0
            
            cursor.execute(''' SELECT id, job_name, learning_type, status, progress, created_at FROM learning_jobs ORDER BY created_at DESC LIMIT 10 ''')
            stats['recent_jobs'] = []
            for row in cursor.fetchall():
                stats['recent_jobs'].append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'status': row[3],
                    'progress': row[4] or 0,
                    'timestamp': row[5]
                })
    except Exception:
        stats = {
            'total_jobs': 0,
            'running_jobs': 0,
            'completed_jobs': 0,
            'total_hours': 0,
            'recent_jobs': []
        }
    return stats

def get_graph_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_nodes')
            stats['total_nodes'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_relations')
            stats['total_relations'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT category) FROM knowledge_nodes')
            stats['total_categories'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_nodes WHERE created_at >= date('now')")
            stats['updated_today'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, node_name, category, description, created_at FROM knowledge_nodes ORDER BY created_at DESC LIMIT 10 ''')
            stats['recent_nodes'] = []
            for row in cursor.fetchall():
                stats['recent_nodes'].append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'description': row[3],
                    'timestamp': row[4]
                })
    except Exception:
        stats = {
            'total_nodes': 0,
            'total_relations': 0,
            'total_categories': 0,
            'updated_today': 0,
            'recent_nodes': []
        }
    return stats

def get_question_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM generated_questions')
            stats['total_generated'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT question_type) FROM generated_questions')
            stats['total_types'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT difficulty) FROM generated_questions')
            stats['total_difficulties'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM generated_questions WHERE used_in_exam = 1")
            stats['used_in_exams'] = cursor.fetchone()[0]
            
            cursor.execute(''' SELECT id, content, question_type, difficulty, status, created_at FROM generated_questions ORDER BY created_at DESC LIMIT 10 ''')
            stats['recent_questions'] = []
            for row in cursor.fetchall():
                stats['recent_questions'].append({
                    'id': row[0],
                    'content': row[1],
                    'type': row[2],
                    'difficulty': row[3],
                    'status': row[4],
                    'timestamp': row[5]
                })
    except Exception:
        stats = {
            'total_generated': 0,
            'total_types': 5,
            'total_difficulties': 3,
            'used_in_exams': 0,
            'recent_questions': []
        }
    return stats

def get_planner_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM learning_plans')
            stats['total_plans'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_plans WHERE status = 'active'")
            stats['active_plans'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_plans WHERE status = 'completed'")
            stats['completed_plans'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(total_goals) FROM learning_plans')
            total_goals = cursor.fetchone()[0]
            stats['total_goals'] = total_goals or 0
            
            cursor.execute(''' SELECT id, plan_name, duration, priority, progress, status, created_at FROM learning_plans ORDER BY created_at DESC LIMIT 10 ''')
            stats['recent_plans'] = []
            for row in cursor.fetchall():
                stats['recent_plans'].append({
                    'id': row[0],
                    'name': row[1],
                    'duration': row[2],
                    'priority': row[3],
                    'progress': row[4] or 0,
                    'status': row[5],
                    'timestamp': row[6]
                })
    except Exception:
        stats = {
            'total_plans': 0,
            'active_plans': 0,
            'completed_plans': 0,
            'total_goals': 0,
            'recent_plans': []
        }
    return stats

def get_user_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE username != 'wuchenghao15' AND role != 'super_admin'")
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT( *) FROM users WHERE is_active = 1 AND username != 'wuchenghao15' AND role != 'super_admin'")
            stats['active_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            stats['student_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            stats['admin_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login >= date( 'now') AND username != 'wuchenghao15' AND role != 'super_admin'")
            stats['online_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date( 'now') AND username != 'wuchenghao15' AND role != 'super_admin'")
            stats['new_users_today'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days') AND username != 'wuchenghao15' AND role != 'super_admin'")
            stats['new_users_week'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT( *) FROM users WHERE is_active = 0 AND username != 'wuchenghao15' AND role != 'super_admin'")
            stats['inactive_users'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_users': 0,
            'active_users': 0,
            'student_count': 0,
            'admin_count': 1,
            'online_users': 0,
            'new_users_today': 0,
            'new_users_week': 0,
            'inactive_users': 0
        }
    return stats

def get_exam_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            stats['total_exams'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exams WHERE status = 'active'")
            stats['active_exams'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exams WHERE status = 'completed'")
            stats['completed_exams'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results")
            stats['total_results'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM exam_results")
            stats['participant_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM exam_results')
            avg_score = cursor.fetchone()[0]
            stats['avg_score'] = round(avg_score) if avg_score else 0
            
            cursor.execute('SELECT COUNT(*) FROM questions')
            stats['total_questions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exam_papers')
            stats['total_papers'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_exams': 0,
            'active_exams': 0,
            'completed_exams': 0,
            'total_results': 0,
            'participant_count': 0,
            'avg_score': 0,
            'total_questions': 0,
            'total_papers': 0
        }
    return stats

def get_course_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM courses')
            stats['total_courses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses WHERE status = 'active'")
            stats['active_courses'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT instructor) FROM courses')
            stats['total_instructors'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM course_enrollments')
            stats['total_enrollments'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses WHERE created_at >= date('now', '-30 days')")
            stats['new_courses_month'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses WHERE difficulty = '初级'")
            stats['beginner_courses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses WHERE difficulty = '中级'")
            stats['intermediate_courses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM courses WHERE difficulty = '高级'")
            stats['advanced_courses'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_courses': 0,
            'active_courses': 0,
            'total_instructors': 0,
            'total_enrollments': 0,
            'new_courses_month': 0,
            'beginner_courses': 0,
            'intermediate_courses': 0,
            'advanced_courses': 0
        }
    return stats

def get_assignment_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM assignments')
            stats['total_assignments'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'active'")
            stats['active_assignments'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'completed'")
            stats['completed_assignments'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM assignment_submissions')
            stats['total_submissions'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM assignment_submissions WHERE status = 'graded'")
            stats['graded_submissions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM assignment_submissions')
            avg_score = cursor.fetchone()[0]
            stats['avg_score'] = round(avg_score) if avg_score else 0
            
            cursor.execute("SELECT COUNT(*) FROM assignments WHERE due_date >= date('now')")
            stats['upcoming_deadlines'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM assignments WHERE due_date < date('now')")
            stats['overdue_assignments'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_assignments': 0,
            'active_assignments': 0,
            'completed_assignments': 0,
            'total_submissions': 0,
            'graded_submissions': 0,
            'avg_score': 0,
            'upcoming_deadlines': 0,
            'overdue_assignments': 0
        }
    return stats

def get_notification_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM notifications')
            stats['total_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
            stats['unread_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE priority = 'high'")
            stats['high_priority'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE created_at >= date('now')")
            stats['today_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE type = 'system'")
            stats['system_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE type = 'exam'")
            stats['exam_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE type = 'course'")
            stats['course_notifications'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notifications WHERE type = 'assignment'")
            stats['assignment_notifications'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_notifications': 0,
            'unread_count': 0,
            'high_priority': 0,
            'today_notifications': 0,
            'system_notifications': 0,
            'exam_notifications': 0,
            'course_notifications': 0,
            'assignment_notifications': 0
        }
    return stats

def get_system_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM error_logs')
            stats['total_errors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE status = 'pending'")
            stats['pending_errors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE status = 'resolved'")
            stats['resolved_errors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE error_type = 'critical'")
            stats['critical_errors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE created_at >= date('now')")
            stats['errors_today'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE created_at >= date('now', '-7 days')")
            stats['errors_week'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM system_logs')
            stats['total_logs'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_logs WHERE level = 'error'")
            stats['error_logs'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_errors': 0,
            'pending_errors': 0,
            'resolved_errors': 0,
            'critical_errors': 0,
            'errors_today': 0,
            'errors_week': 0,
            'total_logs': 0,
            'error_logs': 0
        }
    return stats

def get_resource_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM resources')
            stats['total_files'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(file_size) FROM resources')
            total_size = cursor.fetchone()[0]
            stats['total_size'] = round(total_size / 1024 / 1024) if total_size else 0
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE file_type LIKE 'image%'")
            stats['image_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE file_type LIKE 'video%'")
            stats['video_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE file_type LIKE 'audio%'")
            stats['audio_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE file_type = 'document'")
            stats['document_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE created_at >= date('now')")
            stats['uploaded_today'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM resources WHERE created_at >= date('now', '-7 days')")
            stats['uploaded_week'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_files': 0,
            'total_size': 0,
            'image_count': 0,
            'video_count': 0,
            'audio_count': 0,
            'document_count': 0,
            'uploaded_today': 0,
            'uploaded_week': 0
        }
    return stats

def get_analysis_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM exams')
            stats['total_exams'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE status = 'completed'")
            stats['completed_exams'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(score) FROM exam_results')
            avg_score = cursor.fetchone()[0]
            stats['avg_score'] = round(avg_score) if avg_score else 0
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-30 days')")
            stats['new_users_month'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE created_at >= date('now', '-30 days')")
            stats['exams_month'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            stats['student_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_papers")
            stats['paper_count'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_users': 1,
            'total_exams': 0,
            'completed_exams': 0,
            'avg_score': 0,
            'new_users_month': 0,
            'exams_month': 0,
            'student_count': 0,
            'paper_count': 0
        }
    return stats

def get_auth_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM auth_tokens')
            stats['total_tokens'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM auth_tokens WHERE expires_at > datetime('now')")
            stats['active_tokens'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_locked = 1")
            stats['locked_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM login_records WHERE login_time >= date('now')")
            stats['today_logins'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM login_records WHERE status = 'failed' AND login_time >= date('now')")
            stats['failed_logins'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM login_records")
            stats['total_login_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM auth_tokens WHERE created_at >= date('now', '-30 days')")
            stats['tokens_month'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE password_changed_at >= date('now', '-90 days')")
            stats['recent_password_changes'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_tokens': 0,
            'active_tokens': 0,
            'locked_users': 0,
            'today_logins': 0,
            'failed_logins': 0,
            'total_login_records': 0,
            'tokens_month': 0,
            'recent_password_changes': 0
        }
    return stats

def get_path_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM learning_paths')
            stats['total_paths'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_paths WHERE status = 'active'")
            stats['active_paths'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM learning_paths')
            stats['student_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_paths WHERE status = 'completed'")
            stats['completed_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(progress) FROM learning_paths')
            avg_progress = cursor.fetchone()[0]
            stats['avg_progress'] = round(avg_progress) if avg_progress else 0
            
            cursor.execute("SELECT COUNT(*) FROM learning_paths WHERE created_at >= date('now', '-30 days')")
            stats['new_paths_month'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM learning_path_enrollments')
            stats['total_enrollments'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_path_enrollments WHERE completed_at IS NOT NULL")
            stats['completed_enrollments'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_paths': 0,
            'active_paths': 0,
            'student_count': 0,
            'completed_count': 0,
            'avg_progress': 0,
            'new_paths_month': 0,
            'total_enrollments': 0,
            'completed_enrollments': 0
        }
    return stats

def get_student_stats():
    stats = {}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
            stats['total_students'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(score) FROM exam_results")
            avg_score = cursor.fetchone()[0]
            stats['avg_score'] = round(avg_score) if avg_score else 0
            
            cursor.execute("SELECT AVG(session_duration_minutes) FROM tutor_sessions")
            avg_duration = cursor.fetchone()[0]
            stats['avg_study_time'] = round(avg_duration) if avg_duration else 0
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE score >= 80")
            stats['excellent_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM exam_results WHERE score < 60")
            stats['failed_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student' AND is_active = 1")
            stats['active_students'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_profiles")
            stats['profiles_count'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student' AND created_at >= date('now', '-30 days')")
            stats['new_students_month'] = cursor.fetchone()[0]
    except Exception:
        stats = {
            'total_students': 0,
            'avg_score': 0,
            'avg_study_time': 0,
            'excellent_count': 0,
            'failed_count': 0,
            'active_students': 0,
            'profiles_count': 0,
            'new_students_month': 0
        }
    return stats