# -*- coding: utf-8 -*-
"""
AI智能预警与干预系统API
功能：
1. 学习困难预警 - 基于成绩趋势、作业完成率、登录频率识别学习困难学生
2. 挂科风险预测 - AI预测学生挂科概率和风险等级
3. 个性化干预建议 - 根据预警原因生成针对性干预方案
4. 干预措施跟踪 - 跟踪干预措施执行情况和效果
5. 班级预警总览 - 班级层面预警统计和分析
6. 预警趋势分析 - 预警数量和等级变化趋势
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ai_warning_intervention_api = Blueprint('ai_warning_intervention_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_warning_tables():
    """初始化预警系统数据库表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                warning_type TEXT NOT NULL,
                warning_level TEXT NOT NULL,
                risk_score REAL NOT NULL,
                warning_reason TEXT,
                intervention_suggestion TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intervention_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warning_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                intervention_type TEXT NOT NULL,
                intervention_content TEXT,
                executor TEXT,
                status TEXT DEFAULT 'pending',
                effect_score REAL,
                feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (warning_id) REFERENCES learning_warnings(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_data TEXT,
                risk_factors TEXT,
                predicted_score REAL,
                risk_level TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info('AI预警与干预系统表结构创建完成')
    except Exception as e:
        logger.error(f'AI预警与干预系统表结构创建失败: {e}')


def calculate_risk_score(user_id):
    """计算学生风险分数（0-100，越高风险越大）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    risk_score = 0
    risk_factors = []

    # 1. 成绩因素（40分）
    cursor.execute('SELECT AVG(score) as avg_score, COUNT(*) as count FROM scores WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    avg_score = result['avg_score'] if result and result['avg_score'] else 0
    score_count = result['count'] if result and result['count'] else 0

    if score_count > 0:
        if avg_score < 60:
            risk_score += 40
            risk_factors.append(f'平均成绩{avg_score:.1f}分，低于及格线')
        elif avg_score < 70:
            risk_score += 25
            risk_factors.append(f'平均成绩{avg_score:.1f}分，处于及格边缘')
        elif avg_score < 80:
            risk_score += 10
            risk_factors.append(f'平均成绩{avg_score:.1f}分，有待提高')

    # 2. 作业完成率（25分）- homework_submissions表使用student_id字段
    cursor.execute('SELECT COUNT(*) as total FROM homework_submissions WHERE student_id = ?', (str(user_id),))
    homework_count = cursor.fetchone()['total']

    if homework_count < 3:
        risk_score += 25
        risk_factors.append(f'作业提交次数仅{homework_count}次，完成率低')
    elif homework_count < 5:
        risk_score += 15
        risk_factors.append(f'作业提交次数{homework_count}次，完成率偏低')

    # 3. 错题数量（20分）- wrong_questions表user_id为TEXT类型
    cursor.execute('SELECT COUNT(*) as total FROM wrong_questions WHERE user_id = ?', (str(user_id),))
    wrong_count = cursor.fetchone()['total']

    if wrong_count > 20:
        risk_score += 20
        risk_factors.append(f'错题数量{wrong_count}道，知识掌握不牢')
    elif wrong_count > 10:
        risk_score += 10
        risk_factors.append(f'错题数量{wrong_count}道，需加强复习')

    # 4. 成绩下降趋势（15分）
    cursor.execute('''
        SELECT score, created_at FROM scores 
        WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
    ''', (user_id,))
    recent_scores = cursor.fetchall()

    if len(recent_scores) >= 3:
        latest = [s['score'] for s in recent_scores]
        trend = latest[0] - latest[-1]
        if trend < -10:
            risk_score += 15
            risk_factors.append(f'成绩下降{abs(trend):.1f}分，呈明显下滑趋势')
        elif trend < -5:
            risk_score += 8
            risk_factors.append(f'成绩下降{abs(trend):.1f}分，需关注')

    conn.close()

    risk_score = min(100, risk_score)
    return round(risk_score, 1), risk_factors


def get_warning_level(risk_score):
    """根据风险分数获取预警等级"""
    if risk_score >= 70:
        return 'critical', '红色预警'
    elif risk_score >= 50:
        return 'high', '橙色预警'
    elif risk_score >= 30:
        return 'medium', '黄色预警'
    else:
        return 'low', '蓝色预警'


def generate_intervention_suggestion(risk_factors, warning_level):
    """生成个性化干预建议"""
    suggestions = []

    for factor in risk_factors:
        if '平均成绩' in factor and '低于及格线' in factor:
            suggestions.append({
                'type': 'academic',
                'priority': 'high',
                'action': '安排一对一辅导，重点补基础知识',
                'expected_effect': '预计1个月内成绩提升至及格线以上',
                'responsible': '班主任+学科老师'
            })
        elif '平均成绩' in factor and '及格边缘' in factor:
            suggestions.append({
                'type': 'academic',
                'priority': 'medium',
                'action': '加强课后练习，每周额外辅导2次',
                'expected_effect': '预计2周内成绩稳定在70分以上',
                'responsible': '学科老师'
            })
        elif '作业提交' in factor:
            suggestions.append({
                'type': 'behavior',
                'priority': 'high',
                'action': '与家长沟通，督促按时完成作业',
                'expected_effect': '预计1周内作业提交率提升至80%',
                'responsible': '班主任+家长'
            })
        elif '错题数量' in factor:
            suggestions.append({
                'type': 'study_method',
                'priority': 'medium',
                'action': '建立错题本制度，定期复习错题',
                'expected_effect': '预计2周内错题数量减少50%',
                'responsible': '学科老师+学生'
            })
        elif '成绩下降' in factor and '明显下滑' in factor:
            suggestions.append({
                'type': 'psychological',
                'priority': 'high',
                'action': '了解成绩下降原因，必要时安排心理辅导',
                'expected_effect': '稳定学习状态，止住下滑趋势',
                'responsible': '班主任+心理老师'
            })

    if not suggestions:
        suggestions.append({
            'type': 'general',
            'priority': 'low',
            'action': '保持关注，定期了解学习情况',
            'expected_effect': '维持当前学习状态',
            'responsible': '班主任'
        })

    return suggestions


@ai_warning_intervention_api.route('/api/ai/warning/scan', methods=['POST'])
@require_admin
def scan_all_warnings():
    """扫描所有学生，生成预警"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, username FROM users WHERE role IN ('student', 'student_vip')")
        students = cursor.fetchall()

        warnings_generated = 0
        warnings_updated = 0

        for student in students:
            user_id = student['id']
            risk_score, risk_factors = calculate_risk_score(user_id)

            if risk_score >= 30:
                warning_level, level_desc = get_warning_level(risk_score)
                suggestion = generate_intervention_suggestion(risk_factors, warning_level)

                cursor.execute('''
                    SELECT id, status FROM learning_warnings 
                    WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1
                ''', (user_id,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute('''
                        UPDATE learning_warnings 
                        SET risk_score = ?, warning_reason = ?, intervention_suggestion = ?,
                            warning_level = ?, created_at = ?
                        WHERE id = ?
                    ''', (risk_score, json.dumps(risk_factors, ensure_ascii=False),
                          json.dumps(suggestion, ensure_ascii=False), warning_level,
                          datetime.now().isoformat(), existing['id']))
                    warnings_updated += 1
                else:
                    cursor.execute('''
                        INSERT INTO learning_warnings 
                        (user_id, warning_type, warning_level, risk_score, warning_reason, 
                         intervention_suggestion, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (user_id, 'learning_difficulty', warning_level, risk_score,
                          json.dumps(risk_factors, ensure_ascii=False),
                          json.dumps(suggestion, ensure_ascii=False),
                          datetime.now().isoformat()))
                    warnings_generated += 1

        conn.commit()
        conn.close()

        return APIResponse.success(data={
            'total_students': len(students),
            'warnings_generated': warnings_generated,
            'warnings_updated': warnings_updated,
            'scanned_at': datetime.now().isoformat()
        }, message=f'预警扫描完成，新增{warnings_generated}条，更新{warnings_updated}条')

    except Exception as e:
        logger.error(f'预警扫描失败: {e}')
        return APIResponse.error(message=f'预警扫描失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/list', methods=['GET'])
@require_admin
def get_warning_list():
    """获取预警列表"""
    try:
        level = request.args.get('level', '')
        status = request.args.get('status', 'active')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
            SELECT w.*, u.username, u.class_name, u.grade
            FROM learning_warnings w
            LEFT JOIN users u ON w.user_id = u.id
            WHERE 1=1
        '''
        params = []

        if status:
            query += ' AND w.status = ?'
            params.append(status)
        if level:
            query += ' AND w.warning_level = ?'
            params.append(level)

        query += ' ORDER BY w.risk_score DESC, w.created_at DESC'

        cursor.execute(query, params)
        warnings = []

        for row in cursor.fetchall():
            warning = dict(row)
            warning['warning_reason'] = json.loads(warning['warning_reason']) if warning['warning_reason'] else []
            warning['intervention_suggestion'] = json.loads(warning['intervention_suggestion']) if warning['intervention_suggestion'] else []
            warnings.append(warning)

        conn.close()

        level_count = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for w in warnings:
            level_count[w['warning_level']] = level_count.get(w['warning_level'], 0) + 1

        return APIResponse.success(data={
            'warnings': warnings,
            'total': len(warnings),
            'level_distribution': level_count,
            'generated_at': datetime.now().isoformat()
        }, message='获取预警列表成功')

    except Exception as e:
        logger.error(f'获取预警列表失败: {e}')
        return APIResponse.error(message=f'获取预警列表失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/student/<int:user_id>', methods=['GET'])
@require_login
def get_student_warning_detail(user_id):
    """获取学生预警详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, username, class_name, grade FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return APIResponse.error(message='用户不存在')

        cursor.execute('''
            SELECT * FROM learning_warnings WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        warnings = [dict(w) for w in cursor.fetchall()]

        for w in warnings:
            w['warning_reason'] = json.loads(w['warning_reason']) if w['warning_reason'] else []
            w['intervention_suggestion'] = json.loads(w['intervention_suggestion']) if w['intervention_suggestion'] else []

        cursor.execute('''
            SELECT * FROM intervention_records WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        interventions = [dict(i) for i in cursor.fetchall()]

        risk_score, risk_factors = calculate_risk_score(user_id)
        warning_level, level_desc = get_warning_level(risk_score)

        cursor.execute('SELECT subject, AVG(score) as avg_score, COUNT(*) as count FROM scores WHERE user_id = ? GROUP BY subject', (user_id,))
        scores = [dict(s) for s in cursor.fetchall()]

        conn.close()

        return APIResponse.success(data={
            'student_info': dict(user),
            'current_risk_score': risk_score,
            'current_risk_level': warning_level,
            'current_risk_factors': risk_factors,
            'warning_history': warnings,
            'intervention_history': interventions,
            'score_analysis': scores,
            'generated_at': datetime.now().isoformat()
        }, message='获取学生预警详情成功')

    except Exception as e:
        logger.error(f'获取学生预警详情失败: {e}')
        return APIResponse.error(message=f'获取学生预警详情失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/intervention', methods=['POST'])
@require_admin
def create_intervention():
    """创建干预措施"""
    try:
        data = request.get_json()
        warning_id = data.get('warning_id')
        user_id = data.get('user_id')
        intervention_type = data.get('intervention_type', 'academic')
        intervention_content = data.get('intervention_content', '')
        executor = data.get('executor', session.get('username', '系统'))

        if not warning_id or not user_id:
            return APIResponse.validation_error(message='请提供预警ID和学生ID')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO intervention_records 
            (warning_id, user_id, intervention_type, intervention_content, executor, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        ''', (warning_id, user_id, intervention_type, intervention_content, executor,
              datetime.now().isoformat()))

        record_id = cursor.lastrowid

        cursor.execute('''
            UPDATE learning_warnings SET status = 'intervening' WHERE id = ?
        ''', (warning_id,))

        conn.commit()
        conn.close()

        return APIResponse.success(data={
            'record_id': record_id,
            'created_at': datetime.now().isoformat()
        }, message='干预措施创建成功')

    except Exception as e:
        logger.error(f'创建干预措施失败: {e}')
        return APIResponse.error(message=f'创建干预措施失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/intervention/<int:record_id>/complete', methods=['POST'])
@require_admin
def complete_intervention(record_id):
    """完成干预措施"""
    try:
        data = request.get_json()
        effect_score = data.get('effect_score', 0)
        feedback = data.get('feedback', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT warning_id, user_id FROM intervention_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()

        if not record:
            conn.close()
            return APIResponse.error(message='干预记录不存在')

        cursor.execute('''
            UPDATE intervention_records 
            SET status = 'completed', effect_score = ?, feedback = ?, completed_at = ?
            WHERE id = ?
        ''', (effect_score, feedback, datetime.now().isoformat(), record_id))

        new_risk_score, _ = calculate_risk_score(record['user_id'])

        if new_risk_score < 30:
            cursor.execute('''
                UPDATE learning_warnings SET status = 'resolved', resolved_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), record['warning_id']))
        else:
            cursor.execute('''
                UPDATE learning_warnings SET risk_score = ? WHERE id = ?
            ''', (new_risk_score, record['warning_id']))

        conn.commit()
        conn.close()

        return APIResponse.success(data={
            'record_id': record_id,
            'new_risk_score': new_risk_score,
            'completed_at': datetime.now().isoformat()
        }, message='干预措施已完成')

    except Exception as e:
        logger.error(f'完成干预措施失败: {e}')
        return APIResponse.error(message=f'完成干预措施失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/dashboard', methods=['GET'])
@require_admin
def warning_dashboard():
    """预警仪表盘"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT warning_level, COUNT(*) as count 
            FROM learning_warnings WHERE status = 'active' 
            GROUP BY warning_level
        ''', )
        level_stats = {row['warning_level']: row['count'] for row in cursor.fetchall()}

        cursor.execute('SELECT COUNT(*) as total FROM learning_warnings WHERE status = ?', ('active',))
        total_active = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM learning_warnings WHERE status = ?', ('resolved',))
        total_resolved = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM intervention_records WHERE status = ?', ('pending',))
        pending_interventions = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM intervention_records WHERE status = ?', ('completed',))
        completed_interventions = cursor.fetchone()['total']

        cursor.execute('''
            SELECT AVG(effect_score) as avg_effect 
            FROM intervention_records WHERE status = 'completed' AND effect_score IS NOT NULL
        ''')
        avg_effect = cursor.fetchone()['avg_effect'] or 0

        cursor.execute('''
            SELECT w.warning_level, COUNT(*) as count, strftime('%Y-%m-%d', w.created_at) as date
            FROM learning_warnings w
            WHERE w.created_at >= datetime('now', '-30 days')
            GROUP BY date, w.warning_level
            ORDER BY date
        ''')
        trend_data = {}
        for row in cursor.fetchall():
            date = row['date']
            if date not in trend_data:
                trend_data[date] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            trend_data[date][row['warning_level']] = row['count']

        cursor.execute('''
            SELECT w.risk_score, w.warning_level, w.warning_reason, w.intervention_suggestion,
                   w.user_id, u.username, u.class_name, w.created_at, w.id
            FROM learning_warnings w
            LEFT JOIN users u ON w.user_id = u.id
            WHERE w.status = 'active'
            ORDER BY w.risk_score DESC LIMIT 10
        ''')
        top_risk_students = []
        for row in cursor.fetchall():
            student = dict(row)
            student['warning_reason'] = json.loads(student['warning_reason']) if student['warning_reason'] else []
            top_risk_students.append(student)

        conn.close()

        return APIResponse.success(data={
            'level_distribution': level_stats,
            'total_active': total_active,
            'total_resolved': total_resolved,
            'pending_interventions': pending_interventions,
            'completed_interventions': completed_interventions,
            'avg_intervention_effect': round(avg_effect, 1),
            'trend_data': trend_data,
            'top_risk_students': top_risk_students,
            'generated_at': datetime.now().isoformat()
        }, message='预警仪表盘数据获取成功')

    except Exception as e:
        logger.error(f'获取预警仪表盘失败: {e}')
        return APIResponse.error(message=f'获取预警仪表盘失败: {str(e)}')


@ai_warning_intervention_api.route('/api/ai/warning/predict/<int:user_id>', methods=['GET'])
@require_login
def predict_student_risk(user_id):
    """预测学生风险"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return APIResponse.error(message='用户不存在')

        risk_score, risk_factors = calculate_risk_score(user_id)
        warning_level, level_desc = get_warning_level(risk_score)

        cursor.execute('SELECT AVG(score) as avg_score FROM scores WHERE user_id = ?', (user_id,))
        current_avg = cursor.fetchone()['avg_score'] or 60

        predicted_score = max(0, current_avg - risk_score * 0.2)

        confidence = 0.7 + (len(risk_factors) * 0.05)
        confidence = min(0.95, confidence)

        suggestion = generate_intervention_suggestion(risk_factors, warning_level)

        cursor.execute('''
            INSERT INTO risk_assessments 
            (user_id, assessment_data, risk_factors, predicted_score, risk_level, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, json.dumps({'current_avg': current_avg, 'risk_score': risk_score}, ensure_ascii=False),
              json.dumps(risk_factors, ensure_ascii=False), predicted_score, warning_level,
              confidence, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return APIResponse.success(data={
            'student_info': dict(user),
            'current_avg_score': round(current_avg, 1),
            'predicted_score': round(predicted_score, 1),
            'risk_score': risk_score,
            'risk_level': warning_level,
            'risk_level_desc': level_desc,
            'risk_factors': risk_factors,
            'confidence': round(confidence, 2),
            'intervention_suggestion': suggestion,
            'generated_at': datetime.now().isoformat()
        }, message='风险预测完成')

    except Exception as e:
        logger.error(f'风险预测失败: {e}')
        return APIResponse.error(message=f'风险预测失败: {str(e)}')


init_warning_tables()
