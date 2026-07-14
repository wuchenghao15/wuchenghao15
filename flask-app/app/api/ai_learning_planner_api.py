# -*- coding: utf-8 -*-
"""
AI智能学习规划系统API
根据目标考试时间、每天可用时间、学科知识点数量，自动分配学习任务
考虑艾宾浩斯遗忘曲线安排复习
"""

from flask import Blueprint, request, session
from app.middlewares.permission_decorators import require_login
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ai_learning_planner_api = Blueprint('ai_learning_planner_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

SUBJECT_KNOWLEDGE_POINTS = {
    '数学': ['函数与导数', '三角函数', '数列', '立体几何', '解析几何', '概率统计', '不等式', '集合与逻辑', '复数', '向量'],
    '语文': ['现代文阅读', '古诗文阅读', '语言文字运用', '写作', '文言文', '诗词鉴赏', '成语与词语', '病句辨析', '语句衔接', '标点符号'],
    '英语': ['词汇', '语法', '阅读理解', '完形填空', '写作', '听力', '翻译', '七选五', '短文改错', '语法填空'],
    '物理': ['力学', '电磁学', '热学', '光学', '原子物理', '实验', '运动学', '牛顿定律', '机械能', '动量'],
    '化学': ['物质结构', '化学反应原理', '有机化学', '无机化学', '化学实验', '化学计算', '元素周期律', '电化学', '化学平衡', '溶液'],
    '生物': ['细胞生物学', '遗传学', '生态学', '分子生物学', '生物进化', '植物学', '动物学', '微生物学', '人体生理', '生物实验'],
    '历史': ['中国古代史', '中国近代史', '中国现代史', '世界古代史', '世界近代史', '世界现代史', '历史人物', '历史事件', '历史概念', '史料分析'],
    '地理': ['自然地理', '人文地理', '区域地理', '地理信息技术', '地图与地球', '气候', '地形地貌', '水文', '土壤植被', '人口城市'],
    '政治': ['经济生活', '政治生活', '文化生活', '生活与哲学', '时事政治', '国家与国际组织', '经济学常识', '科学社会主义', '公民道德', '法律常识']
}

DIFFICULTY_TIME = {
    'easy': 30,
    'medium': 45,
    'hard': 60
}


def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                total_hours REAL DEFAULT 0,
                daily_hours REAL DEFAULT 2,
                plan_type TEXT DEFAULT 'exam',
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plan_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                subject TEXT,
                knowledge_point TEXT,
                estimated_time INTEGER DEFAULT 45,
                difficulty TEXT DEFAULT 'medium',
                order_num INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                completed_at TEXT,
                is_review INTEGER DEFAULT 0,
                review_stage INTEGER DEFAULT 0,
                scheduled_date TEXT,
                FOREIGN KEY (plan_id) REFERENCES learning_plans(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER,
                task_id INTEGER,
                study_duration INTEGER DEFAULT 0,
                content TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (plan_id) REFERENCES learning_plans(id),
                FOREIGN KEY (task_id) REFERENCES plan_tasks(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("AI智能学习规划系统表创建完成")
    except Exception as e:
        logger.error(f"创建AI智能学习规划系统表失败: {e}")


def generate_learning_tasks(plan_id, subject, start_date, end_date, daily_hours, knowledge_points=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if knowledge_points is None:
        knowledge_points = SUBJECT_KNOWLEDGE_POINTS.get(subject, ['知识点1', '知识点2', '知识点3'])

    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    total_days = (end_dt - start_dt).days + 1

    if total_days <= 0:
        total_days = 1

    daily_minutes = daily_hours * 60

    new_tasks = []
    order_num = 0

    for kp_idx, kp in enumerate(knowledge_points):
        base_difficulty = 'medium'
        if kp_idx < len(knowledge_points) // 3:
            base_difficulty = 'easy'
        elif kp_idx >= len(knowledge_points) * 2 // 3:
            base_difficulty = 'hard'

        estimated_time = DIFFICULTY_TIME.get(base_difficulty, 45)

        day_offset = (kp_idx * estimated_time) // daily_minutes
        if day_offset >= total_days:
            day_offset = total_days - 1

        scheduled_dt = start_dt + timedelta(days=int(day_offset))
        scheduled_date = scheduled_dt.strftime('%Y-%m-%d')

        cursor.execute('''
            INSERT INTO plan_tasks (plan_id, task_name, subject, knowledge_point, estimated_time,
                                   difficulty, order_num, status, is_review, review_stage, scheduled_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        ''', (plan_id, f"学习：{kp}", subject, kp, estimated_time, base_difficulty,
              order_num, 'pending', scheduled_date))

        task_id = cursor.lastrowid
        new_tasks.append({
            'id': task_id,
            'knowledge_point': kp,
            'scheduled_date': scheduled_date,
            'estimated_time': estimated_time,
            'difficulty': base_difficulty
        })
        order_num += 1

        for stage, interval in enumerate(EBBINGHAUS_INTERVALS[:3]):
            review_day_offset = day_offset + interval
            if review_day_offset < total_days:
                review_dt = start_dt + timedelta(days=int(review_day_offset))
                review_date = review_dt.strftime('%Y-%m-%d')
                review_time = max(estimated_time // 2, 15)

                cursor.execute('''
                    INSERT INTO plan_tasks (plan_id, task_name, subject, knowledge_point, estimated_time,
                                           difficulty, order_num, status, is_review, review_stage, scheduled_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                ''', (plan_id, f"复习：{kp}（第{stage + 1}次）", subject, kp, review_time,
                      base_difficulty, order_num, 'pending', stage + 1, review_date))

                order_num += 1

    cursor.execute('SELECT COUNT(*) as total, SUM(estimated_time) as total_time FROM plan_tasks WHERE plan_id = ?', (plan_id,))
    stats = cursor.fetchone()
    total_hours = round((stats['total_time'] or 0) / 60, 1)

    cursor.execute('UPDATE learning_plans SET total_hours = ? WHERE id = ?', (total_hours, plan_id))

    conn.commit()
    conn.close()

    return new_tasks


@ai_learning_planner_api.route('/api/ai/planner/create', methods=['POST'])
@require_login
def create_learning_plan():
    try:
        user_id = session.get('user_id')
        data = request.get_json()

        title = data.get('title', '')
        subject = data.get('subject', '')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        daily_hours = float(data.get('daily_hours', 2))
        plan_type = data.get('plan_type', 'exam')
        knowledge_points = data.get('knowledge_points')

        if not title or not subject or not start_date or not end_date:
            return APIResponse.validation_error('请填写完整的计划信息')

        if daily_hours <= 0 or daily_hours > 12:
            return APIResponse.validation_error('每日学习时间应在0-12小时之间')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO learning_plans (user_id, title, subject, start_date, end_date, daily_hours, plan_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'draft')
        ''', (user_id, title, subject, start_date, end_date, daily_hours, plan_type))

        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()

        tasks = generate_learning_tasks(plan_id, subject, start_date, end_date, daily_hours, knowledge_points)

        return APIResponse.success({
            'plan_id': plan_id,
            'title': title,
            'subject': subject,
            'tasks_count': len(tasks),
            'message': '学习计划创建成功'
        }, '学习计划创建成功')

    except Exception as e:
        logger.error(f"创建学习计划失败: {e}")
        return APIResponse.server_error(f'创建学习计划失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/plans', methods=['GET'])
@require_login
def get_learning_plans():
    try:
        user_id = session.get('user_id')
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM learning_plans WHERE user_id = ?'
        params = [user_id]

        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([page_size, (page - 1) * page_size])

        cursor.execute(query, params)
        plans = [dict(row) for row in cursor.fetchall()]

        count_query = 'SELECT COUNT(*) as total FROM learning_plans WHERE user_id = ?'
        count_params = [user_id]
        if status:
            count_query += ' AND status = ?'
            count_params.append(status)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        for plan in plans:
            cursor.execute('SELECT COUNT(*) as total FROM plan_tasks WHERE plan_id = ?', (plan['id'],))
            plan['total_tasks'] = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(*) as completed FROM plan_tasks WHERE plan_id = ? AND status = "completed"', (plan['id'],))
            plan['completed_tasks'] = cursor.fetchone()['completed']

            if plan['total_tasks'] > 0:
                plan['progress'] = round(plan['completed_tasks'] / plan['total_tasks'] * 100, 1)
            else:
                plan['progress'] = 0

        conn.close()

        return APIResponse.success({
            'plans': plans,
            'total': total,
            'page': page,
            'page_size': page_size
        })

    except Exception as e:
        logger.error(f"获取学习计划列表失败: {e}")
        return APIResponse.server_error(f'获取学习计划列表失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/plan/<plan_id>', methods=['GET'])
@require_login
def get_plan_detail(plan_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM learning_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        plan = cursor.fetchone()

        if not plan:
            conn.close()
            return APIResponse.not_found('学习计划不存在')

        plan = dict(plan)

        cursor.execute('SELECT * FROM plan_tasks WHERE plan_id = ? ORDER BY order_num ASC', (plan_id,))
        tasks = [dict(row) for row in cursor.fetchall()]

        plan['tasks'] = tasks
        plan['total_tasks'] = len(tasks)
        plan['completed_tasks'] = sum(1 for t in tasks if t['status'] == 'completed')

        if plan['total_tasks'] > 0:
            plan['progress'] = round(plan['completed_tasks'] / plan['total_tasks'] * 100, 1)
        else:
            plan['progress'] = 0

        conn.close()

        return APIResponse.success(plan)

    except Exception as e:
        logger.error(f"获取计划详情失败: {e}")
        return APIResponse.server_error(f'获取计划详情失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/plan/<plan_id>/start', methods=['POST'])
@require_login
def start_plan(plan_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM learning_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        plan = cursor.fetchone()

        if not plan:
            conn.close()
            return APIResponse.not_found('学习计划不存在')

        if plan['status'] not in ['draft', 'paused']:
            conn.close()
            return APIResponse.error('计划状态不允许开始', code=400)

        cursor.execute('UPDATE learning_plans SET status = "active" WHERE id = ?', (plan_id,))
        conn.commit()
        conn.close()

        return APIResponse.success({'plan_id': plan_id, 'status': 'active'}, '学习计划已开始')

    except Exception as e:
        logger.error(f"开始计划失败: {e}")
        return APIResponse.server_error(f'开始计划失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/plan/<plan_id>/pause', methods=['POST'])
@require_login
def pause_plan(plan_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM learning_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        plan = cursor.fetchone()

        if not plan:
            conn.close()
            return APIResponse.not_found('学习计划不存在')

        if plan['status'] != 'active':
            conn.close()
            return APIResponse.error('计划状态不允许暂停', code=400)

        cursor.execute('UPDATE learning_plans SET status = "paused" WHERE id = ?', (plan_id,))
        conn.commit()
        conn.close()

        return APIResponse.success({'plan_id': plan_id, 'status': 'paused'}, '学习计划已暂停')

    except Exception as e:
        logger.error(f"暂停计划失败: {e}")
        return APIResponse.server_error(f'暂停计划失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/task/<task_id>/complete', methods=['POST'])
@require_login
def complete_task(task_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        study_duration = data.get('study_duration', 0)
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT pt.*, lp.user_id FROM plan_tasks pt
            JOIN learning_plans lp ON pt.plan_id = lp.id
            WHERE pt.id = ? AND lp.user_id = ?
        ''', (task_id, user_id))
        task = cursor.fetchone()

        if not task:
            conn.close()
            return APIResponse.not_found('任务不存在')

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            UPDATE plan_tasks SET status = "completed", completed_at = ? WHERE id = ?
        ''', (now, task_id))

        if study_duration > 0:
            cursor.execute('''
                INSERT INTO study_records (user_id, plan_id, task_id, study_duration, content, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, task['plan_id'], task_id, study_duration, task['task_name'], notes))

        conn.commit()
        conn.close()

        return APIResponse.success({'task_id': task_id, 'status': 'completed'}, '任务已完成')

    except Exception as e:
        logger.error(f"完成任务失败: {e}")
        return APIResponse.server_error(f'完成任务失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/record', methods=['POST'])
@require_login
def record_study():
    try:
        user_id = session.get('user_id')
        data = request.get_json()

        plan_id = data.get('plan_id')
        task_id = data.get('task_id')
        study_duration = int(data.get('study_duration', 0))
        content = data.get('content', '')
        notes = data.get('notes', '')

        if study_duration <= 0:
            return APIResponse.validation_error('学习时长必须大于0')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO study_records (user_id, plan_id, task_id, study_duration, content, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, plan_id, task_id, study_duration, content, notes))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return APIResponse.success({
            'record_id': record_id,
            'study_duration': study_duration
        }, '学习记录已保存')

    except Exception as e:
        logger.error(f"记录学习失败: {e}")
        return APIResponse.server_error(f'记录学习失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/progress/<plan_id>', methods=['GET'])
@require_login
def get_learning_progress(plan_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM learning_plans WHERE id = ? AND user_id = ?', (plan_id, user_id))
        plan = cursor.fetchone()

        if not plan:
            conn.close()
            return APIResponse.not_found('学习计划不存在')

        plan = dict(plan)

        cursor.execute('SELECT * FROM plan_tasks WHERE plan_id = ? ORDER BY order_num ASC', (plan_id,))
        tasks = [dict(row) for row in cursor.fetchall()]

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t['status'] == 'completed')
        pending_tasks = sum(1 for t in tasks if t['status'] == 'pending')
        review_tasks = sum(1 for t in tasks if t['is_review'] == 1)
        completed_reviews = sum(1 for t in tasks if t['is_review'] == 1 and t['status'] == 'completed')

        total_estimated_time = sum(t['estimated_time'] for t in tasks)
        completed_estimated_time = sum(t['estimated_time'] for t in tasks if t['status'] == 'completed')

        cursor.execute('SELECT SUM(study_duration) as total_duration FROM study_records WHERE user_id = ? AND plan_id = ?', (user_id, plan_id))
        actual_study_time = cursor.fetchone()['total_duration'] or 0

        start_dt = datetime.strptime(plan['start_date'], '%Y-%m-%d')
        end_dt = datetime.strptime(plan['end_date'], '%Y-%m-%d')
        today = datetime.now()
        total_days = (end_dt - start_dt).days + 1
        elapsed_days = (today - start_dt).days + 1

        if elapsed_days < 0:
            elapsed_days = 0
        if elapsed_days > total_days:
            elapsed_days = total_days

        if total_tasks > 0:
            progress = round(completed_tasks / total_tasks * 100, 1)
        else:
            progress = 0

        if elapsed_days > 0 and total_days > 0:
            expected_progress = round(elapsed_days / total_days * 100, 1)
        else:
            expected_progress = 0

        daily_progress = []
        for i in range(min(elapsed_days, 30)):
            day_date = (start_dt + timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) as count FROM plan_tasks WHERE plan_id = ? AND scheduled_date = ? AND status = "completed"', (plan_id, day_date))
            day_completed = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM plan_tasks WHERE plan_id = ? AND scheduled_date = ?', (plan_id, day_date))
            day_total = cursor.fetchone()['count']

            cursor.execute('SELECT COALESCE(SUM(study_duration), 0) as duration FROM study_records WHERE user_id = ? AND plan_id = ? AND DATE(created_at) = ?', (user_id, plan_id, day_date))
            day_duration = cursor.fetchone()['duration'] or 0

            daily_progress.append({
                'date': day_date,
                'total_tasks': day_total,
                'completed_tasks': day_completed,
                'study_minutes': day_duration
            })

        conn.close()

        return APIResponse.success({
            'plan_id': plan_id,
            'title': plan['title'],
            'subject': plan['subject'],
            'status': plan['status'],
            'progress': progress,
            'expected_progress': expected_progress,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'review_tasks': review_tasks,
            'completed_reviews': completed_reviews,
            'total_estimated_hours': round(total_estimated_time / 60, 1),
            'completed_estimated_hours': round(completed_estimated_time / 60, 1),
            'actual_study_hours': round(actual_study_time / 60, 1),
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'daily_progress': daily_progress
        })

    except Exception as e:
        logger.error(f"获取学习进度失败: {e}")
        return APIResponse.server_error(f'获取学习进度失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/recommend', methods=['GET'])
@require_login
def recommend_plans():
    try:
        user_id = session.get('user_id')
        subject = request.args.get('subject', '')
        plan_type = request.args.get('plan_type', 'exam')
        days = int(request.args.get('days', 30))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT subject, COUNT(*) as count, AVG(total_hours) as avg_hours
            FROM learning_plans
            WHERE user_id = ?
            GROUP BY subject
            ORDER BY count DESC
            LIMIT 5
        ''', (user_id,))
        user_history = [dict(row) for row in cursor.fetchall()]

        recommendations = []
        subjects = [subject] if subject else list(SUBJECT_KNOWLEDGE_POINTS.keys())[:5]

        for subj in subjects:
            kps = SUBJECT_KNOWLEDGE_POINTS.get(subj, [])
            total_points = len(kps)
            study_time_per_point = 45
            total_minutes = total_points * study_time_per_point
            total_hours_needed = round(total_minutes / 60, 1)
            daily_hours_recommended = round(total_minutes / days / 60, 1)

            if daily_hours_recommended < 0.5:
                daily_hours_recommended = 0.5
            if daily_hours_recommended > 8:
                daily_hours_recommended = 8

            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days - 1)).strftime('%Y-%m-%d')

            recommendations.append({
                'subject': subj,
                'knowledge_points_count': total_points,
                'knowledge_points': kps[:5],
                'recommended_daily_hours': daily_hours_recommended,
                'total_hours_needed': total_hours_needed,
                'start_date': start_date,
                'end_date': end_date,
                'plan_type': plan_type,
                'difficulty_distribution': {
                    'easy': round(total_points * 0.3),
                    'medium': round(total_points * 0.5),
                    'hard': round(total_points * 0.2)
                },
                'review_strategy': '艾宾浩斯遗忘曲线（1天、2天、4天复习）',
                'sample_title': f'{subj}{days}天学习计划'
            })

        conn.close()

        return APIResponse.success({
            'recommendations': recommendations,
            'user_history': user_history
        })

    except Exception as e:
        logger.error(f"获取推荐学习计划失败: {e}")
        return APIResponse.server_error(f'获取推荐学习计划失败: {str(e)}')


@ai_learning_planner_api.route('/api/ai/planner/stats', methods=['GET'])
@require_login
def get_learning_stats():
    try:
        user_id = session.get('user_id')
        days = int(request.args.get('days', 30))

        conn = get_db_connection()
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days - 1)).strftime('%Y-%m-%d')

        cursor.execute('SELECT COUNT(*) as total FROM learning_plans WHERE user_id = ?', (user_id,))
        total_plans = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as active FROM learning_plans WHERE user_id = ? AND status = "active"', (user_id,))
        active_plans = cursor.fetchone()['active']

        cursor.execute('SELECT COUNT(*) as completed FROM learning_plans WHERE user_id = ? AND status = "completed"', (user_id,))
        completed_plans = cursor.fetchone()['completed']

        cursor.execute('''
            SELECT COALESCE(SUM(study_duration), 0) as total_duration
            FROM study_records
            WHERE user_id = ? AND DATE(created_at) >= ?
        ''', (user_id, start_date))
        total_study_minutes = cursor.fetchone()['total_duration'] or 0

        cursor.execute('''
            SELECT DATE(created_at) as date, COALESCE(SUM(study_duration), 0) as duration
            FROM study_records
            WHERE user_id = ? AND DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (user_id, start_date))
        daily_stats = [dict(row) for row in cursor.fetchall()]

        daily_data = []
        for i in range(days):
            day_date = (datetime.now() - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
            day_duration = 0
            for stat in daily_stats:
                if stat['date'] == day_date:
                    day_duration = stat['duration']
                    break
            daily_data.append({
                'date': day_date,
                'study_minutes': day_duration
            })

        cursor.execute('''
            SELECT lp.subject, COALESCE(SUM(sr.study_duration), 0) as duration
            FROM study_records sr
            LEFT JOIN learning_plans lp ON sr.plan_id = lp.id
            WHERE sr.user_id = ? AND DATE(sr.created_at) >= ?
            GROUP BY lp.subject
            ORDER BY duration DESC
        ''', (user_id, start_date))
        subject_stats = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT COUNT(*) as completed FROM plan_tasks pt
            JOIN learning_plans lp ON pt.plan_id = lp.id
            WHERE lp.user_id = ? AND pt.status = "completed"
        ''', (user_id,))
        total_completed_tasks = cursor.fetchone()['completed']

        cursor.execute('''
            SELECT COUNT(*) as total FROM plan_tasks pt
            JOIN learning_plans lp ON pt.plan_id = lp.id
            WHERE lp.user_id = ?
        ''', (user_id,))
        total_tasks = cursor.fetchone()['total']

        if days > 0:
            avg_daily_minutes = round(total_study_minutes / days, 1)
        else:
            avg_daily_minutes = 0

        total_study_hours = round(total_study_minutes / 60, 1)

        streak = 0
        for i in range(days):
            day_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            found = False
            for stat in daily_stats:
                if stat['date'] == day_date and stat['duration'] > 0:
                    found = True
                    break
            if found:
                streak += 1
            else:
                break

        conn.close()

        return APIResponse.success({
            'total_plans': total_plans,
            'active_plans': active_plans,
            'completed_plans': completed_plans,
            'total_tasks': total_tasks,
            'total_completed_tasks': total_completed_tasks,
            'total_study_hours': total_study_hours,
            'avg_daily_minutes': avg_daily_minutes,
            'streak_days': streak,
            'period_days': days,
            'daily_data': daily_data,
            'subject_stats': subject_stats
        })

    except Exception as e:
        logger.error(f"获取学习统计失败: {e}")
        return APIResponse.server_error(f'获取学习统计失败: {str(e)}')


create_tables()
