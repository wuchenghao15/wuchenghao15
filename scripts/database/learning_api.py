#!/usr/bin/env python3
"""
学习系统API服务
提供学习系统相关的RESTful API接口
"""

from flask import Flask, request, jsonify, CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = 'mtcos_system.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/learning/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': '学习系统API运行正常',
        'timestamp': datetime.now().isoformat()
    })

# ==================== 课程相关API ====================

@app.route('/api/learning/courses', methods=['GET'])
def get_courses():
    """获取所有课程"""
    try:
        course_type = request.args.get('type', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if course_type:
            cursor.execute('SELECT * FROM course_catalog WHERE course_type = ? AND is_active = 1', (course_type,))
        else:
            cursor.execute('SELECT * FROM course_catalog WHERE is_active = 1')
        
        courses = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(course) for course in courses],
            'total': len(courses)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/courses/<course_code>', methods=['GET'])
def get_course_details(course_code):
    """获取课程详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM course_catalog WHERE course_code = ?', (course_code,))
        course = cursor.fetchone()
        conn.close()
        
        if course:
            return jsonify({
                'success': True,
                'data': dict(course)
            })
        else:
            return jsonify({'success': False, 'error': '课程不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 学习进度相关API ====================

@app.route('/api/learning/progress/<user_id>', methods=['GET'])
def get_learning_progress(user_id):
    """获取用户学习进度"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_progress WHERE user_id = ?', (user_id,))
        progress = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(p) for p in progress],
            'total': len(progress)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/progress', methods=['POST'])
def update_learning_progress():
    """更新学习进度"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        course_type = data.get('course_type')
        course_name = data.get('course_name')
        progress = data.get('progress', 0)
        hours = data.get('hours', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO learning_progress 
            (user_id, course_type, course_name, progress, total_hours, last_learned, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course_type, course_name, progress, hours, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '学习进度已更新'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 学习笔记相关API ====================

@app.route('/api/learning/notes/<user_id>', methods=['GET'])
def get_learning_notes(user_id):
    """获取用户学习笔记"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM learning_notes WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        notes = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(note) for note in notes],
            'total': len(notes)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/notes', methods=['POST'])
def create_learning_note():
    """创建学习笔记"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        note_title = data.get('note_title')
        note_content = data.get('note_content', '')
        tags = json.dumps(data.get('tags', []))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_notes 
            (user_id, note_title, note_content, tags)
            VALUES (?, ?, ?, ?)
        ''', (user_id, note_title, note_content, tags))
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '笔记创建成功',
            'note_id': note_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 学习计划相关API ====================

@app.route('/api/learning/schedule/<user_id>', methods=['GET'])
def get_learning_schedule(user_id):
    """获取用户学习计划"""
    try:
        date = request.args.get('date', '')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if date:
            cursor.execute('SELECT * FROM learning_schedule WHERE user_id = ? AND schedule_date = ? ORDER BY created_at', 
                         (user_id, date))
        else:
            cursor.execute('SELECT * FROM learning_schedule WHERE user_id = ? ORDER BY schedule_date', (user_id,))
        
        schedule = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(s) for s in schedule],
            'total': len(schedule)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/schedule', methods=['POST'])
def create_schedule_task():
    """创建学习计划任务"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        schedule_date = data.get('schedule_date')
        task_title = data.get('task_title')
        task_description = data.get('task_description', '')
        expected_duration = data.get('expected_duration', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_schedule 
            (user_id, schedule_date, task_title, task_description, expected_duration)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, schedule_date, task_title, task_description, expected_duration))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '任务创建成功',
            'task_id': task_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 学习统计相关API ====================

@app.route('/api/learning/statistics/<user_id>', methods=['GET'])
def get_learning_statistics(user_id):
    """获取用户学习统计"""
    try:
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('SELECT * FROM learning_statistics WHERE user_id = ? AND stat_date BETWEEN ? AND ? ORDER BY stat_date DESC', 
                         (user_id, start_date, end_date))
        else:
            cursor.execute('SELECT * FROM learning_statistics WHERE user_id = ? ORDER BY stat_date DESC LIMIT 30', (user_id,))
        
        stats = cursor.fetchall()
        conn.close()
        
        # 计算总统计
        total_minutes = sum(s['study_minutes'] for s in stats)
        total_courses = sum(s['courses_completed'] for s in stats)
        total_notes = sum(s['notes_created'] for s in stats)
        max_streak = max(s['streak_days'] for s in stats) if stats else 0
        
        return jsonify({
            'success': True,
            'data': [dict(s) for s in stats],
            'summary': {
                'total_study_minutes': total_minutes,
                'total_courses_completed': total_courses,
                'total_notes_created': total_notes,
                'max_streak_days': max_streak,
                'active_days': len(stats)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 学习资源相关API ====================

@app.route('/api/learning/resources', methods=['GET'])
def get_learning_resources():
    """获取学习资源"""
    try:
        resource_type = request.args.get('type', '')
        subject = request.args.get('subject', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM learning_resources WHERE is_active = 1'
        params = []
        
        if resource_type:
            query += ' AND resource_type = ?'
            params.append(resource_type)
        if subject:
            query += ' AND subject_area = ?'
            params.append(subject)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        resources = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(r) for r in resources],
            'total': len(resources)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AI辅导相关API ====================

@app.route('/api/learning/ai-tutoring', methods=['POST'])
def record_ai_tutoring():
    """记录AI辅导会话"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        ai_employee_id = data.get('ai_employee_id')
        subject = data.get('subject')
        session_type = data.get('session_type', 'question')
        question_text = data.get('question_text', '')
        ai_response = data.get('ai_response', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_tutoring_sessions 
            (user_id, ai_employee_id, subject, session_type, question_text, ai_response)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, ai_employee_id, subject, session_type, question_text, ai_response))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '辅导会话已记录',
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/learning/ai-tutoring/<user_id>', methods=['GET'])
def get_ai_tutoring_history(user_id):
    """获取AI辅导历史"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ai_tutoring_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50', (user_id,))
        sessions = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(s) for s in sessions],
            'total': len(sessions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 仪表板API ====================

@app.route('/api/learning/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    """获取仪表板数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取学习进度
        cursor.execute('SELECT * FROM learning_progress WHERE user_id = ?', (user_id,))
        progress = cursor.fetchall()
        
        # 获取统计数据
        cursor.execute('SELECT * FROM learning_statistics WHERE user_id = ? ORDER BY stat_date DESC LIMIT 7', (user_id,))
        recent_stats = cursor.fetchall()
        
        # 获取最近笔记
        cursor.execute('SELECT * FROM learning_notes WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,))
        recent_notes = cursor.fetchall()
        
        # 获取AI辅导记录
        cursor.execute('SELECT * FROM ai_tutoring_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,))
        ai_sessions = cursor.fetchall()
        
        conn.close()
        
        # 计算统计
        total_courses = len(progress)
        avg_progress = sum(p['progress'] for p in progress) / total_courses if total_courses > 0 else 0
        total_study_minutes = sum(s['study_minutes'] for s in recent_stats)
        current_streak = recent_stats[0]['streak_days'] if recent_stats else 0
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_courses': total_courses,
                    'average_progress': round(avg_progress, 2),
                    'total_study_hours': round(total_study_minutes / 60, 2),
                    'current_streak': current_streak
                },
                'recent_progress': [dict(p) for p in progress[:5]],
                'recent_notes': [dict(n) for n in recent_notes],
                'ai_sessions': [dict(s) for s in ai_sessions]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("MTSCOS 学习系统 API 服务")
    print("=" * 80)
    print(f"📚 服务地址: http://localhost:5001")
    print("🔧 可用API接口:")
    print("   - /api/learning/health - 健康检查")
    print("   - /api/learning/courses - 课程管理")
    print("   - /api/learning/progress - 学习进度")
    print("   - /api/learning/notes - 学习笔记")
    print("   - /api/learning/schedule - 学习计划")
    print("   - /api/learning/statistics - 学习统计")
    print("   - /api/learning/resources - 学习资源")
    print("   - /api/learning/ai-tutoring - AI辅导")
    print("   - /api/learning/dashboard - 仪表板")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
