# -*- coding: utf-8 -*-
"""
学习系统增强API - 学习路径规划、学习进度追踪、学习成就系统、学习社区
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

learning_enhancement_api = Blueprint('learning_enhancement_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_response(code=200, message='success', data=None):
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                target_score REAL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                progress REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_path_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                item_title TEXT NOT NULL,
                order_num INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                FOREIGN KEY (path_id) REFERENCES learning_paths(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_id INTEGER,
                activity_title TEXT,
                duration INTEGER DEFAULT 0,
                progress REAL DEFAULT 0,
                score REAL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '🏆',
                points INTEGER DEFAULT 0,
                type TEXT DEFAULT 'bronze',
                unlocked INTEGER DEFAULT 0,
                condition TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TEXT,
                progress REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(user_id, achievement_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_communities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '📚',
                member_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                community_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (community_id) REFERENCES learning_communities(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(community_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                community_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (community_id) REFERENCES learning_communities(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                reply_to INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES community_posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (reply_to) REFERENCES post_comments(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '🎖️',
                category TEXT DEFAULT 'learning',
                condition TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                badge_id INTEGER NOT NULL,
                earned_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (badge_id) REFERENCES learning_badges(id),
                UNIQUE(user_id, badge_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_learning_date TEXT,
                total_days INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 学习系统增强表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建学习系统增强表失败: {e}")


create_tables()


@learning_enhancement_api.route('/api/learning/paths', methods=['GET'])
@require_login
def get_learning_paths():
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role in ['admin', 'super_admin', 'teacher']:
            cursor.execute('''
                SELECT lp.id, lp.user_id, u.username, lp.name, lp.description, lp.subject, 
                       lp.target_score, lp.start_date, lp.end_date, lp.progress, lp.status, lp.created_at
                FROM learning_paths lp
                JOIN users u ON lp.user_id = u.id
                ORDER BY lp.created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT id, name, description, subject, target_score, start_date, end_date, 
                       progress, status, created_at
                FROM learning_paths
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))

        paths = []
        for row in cursor.fetchall():
            cursor.execute('SELECT COUNT(*) FROM learning_path_items WHERE path_id = ?', (row['id'],))
            total_items = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM learning_path_items WHERE path_id = ? AND completed = 1', (row['id'],))
            completed_items = cursor.fetchone()[0] or 0

            paths.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row.get('username', ''),
                'name': row['name'],
                'description': row['description'] or '',
                'subject': row['subject'] or '',
                'target_score': row['target_score'] or 0,
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'progress': round(row['progress'] or 0, 2),
                'status': row['status'],
                'total_items': total_items,
                'completed_items': completed_items,
                'created_at': row['created_at']
            })
        conn.close()
        return create_response(200, 'success', {'paths': paths})

    except Exception as e:
        logger.error(f"获取学习路径失败: {e}")
        return create_response(500, '获取学习路径失败')


@learning_enhancement_api.route('/api/learning/paths', methods=['POST'])
@require_login
def create_learning_path():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        name = data.get('name', '')
        description = data.get('description', '')
        subject = data.get('subject', '')
        target_score = data.get('target_score', 0)
        end_date = data.get('end_date', '')

        if not name:
            return create_response(400, '路径名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO learning_paths (user_id, name, description, subject, target_score, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (user_id, name, description, subject, target_score, datetime.now().isoformat(), end_date))
        path_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '学习路径创建成功', {'path_id': path_id, 'name': name})

    except Exception as e:
        logger.error(f"创建学习路径失败: {e}")
        return create_response(500, '创建学习路径失败')


@learning_enhancement_api.route('/api/learning/paths/<int:path_id>', methods=['GET', 'PUT', 'DELETE'])
@require_login
def learning_path_detail(path_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            if role in ['admin', 'super_admin', 'teacher']:
                cursor.execute('''
                    SELECT lp.id, lp.user_id, u.username, lp.name, lp.description, lp.subject, 
                           lp.target_score, lp.start_date, lp.end_date, lp.progress, lp.status, lp.created_at
                    FROM learning_paths lp
                    JOIN users u ON lp.user_id = u.id
                    WHERE lp.id = ?
                ''', (path_id,))
            else:
                cursor.execute('''
                    SELECT id, name, description, subject, target_score, start_date, end_date, 
                           progress, status, created_at
                    FROM learning_paths
                    WHERE id = ? AND user_id = ?
                ''', (path_id, user_id))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return create_response(404, '学习路径不存在')

            cursor.execute('''
                SELECT id, item_type, item_id, item_title, order_num, completed, completed_at
                FROM learning_path_items
                WHERE path_id = ?
                ORDER BY order_num
            ''', (path_id,))
            items = []
            for item_row in cursor.fetchall():
                items.append({
                    'id': item_row['id'],
                    'item_type': item_row['item_type'],
                    'item_id': item_row['item_id'],
                    'item_title': item_row['item_title'],
                    'order_num': item_row['order_num'],
                    'completed': item_row['completed'] == 1,
                    'completed_at': item_row['completed_at']
                })

            conn.close()
            return create_response(200, 'success', {
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row.get('username', ''),
                'name': row['name'],
                'description': row['description'] or '',
                'subject': row['subject'] or '',
                'target_score': row['target_score'] or 0,
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'progress': round(row['progress'] or 0, 2),
                'status': row['status'],
                'created_at': row['created_at'],
                'items': items
            })

        elif request.method == 'PUT':
            if role not in ['admin', 'super_admin', 'teacher']:
                cursor.execute('SELECT id FROM learning_paths WHERE id = ? AND user_id = ?', (path_id, user_id))
                if not cursor.fetchone():
                    conn.close()
                    return create_response(403, '无权操作')

            data = request.get_json() or {}
            updates = []
            params = []

            if 'name' in data:
                updates.append('name = ?')
                params.append(data['name'])
            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])
            if 'subject' in data:
                updates.append('subject = ?')
                params.append(data['subject'])
            if 'target_score' in data:
                updates.append('target_score = ?')
                params.append(data['target_score'])
            if 'end_date' in data:
                updates.append('end_date = ?')
                params.append(data['end_date'])
            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(path_id)

            cursor.execute(f'UPDATE learning_paths SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '学习路径更新成功')

        elif request.method == 'DELETE':
            if role not in ['admin', 'super_admin', 'teacher']:
                cursor.execute('SELECT id FROM learning_paths WHERE id = ? AND user_id = ?', (path_id, user_id))
                if not cursor.fetchone():
                    conn.close()
                    return create_response(403, '无权操作')

            cursor.execute('DELETE FROM learning_path_items WHERE path_id = ?', (path_id,))
            cursor.execute('DELETE FROM learning_paths WHERE id = ?', (path_id,))
            conn.commit()
            conn.close()
            return create_response(200, '学习路径已删除')

    except Exception as e:
        logger.error(f"学习路径操作失败: {e}")
        return create_response(500, '学习路径操作失败')


@learning_enhancement_api.route('/api/learning/paths/<int:path_id>/items', methods=['GET', 'POST'])
@require_login
def path_items(path_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role not in ['admin', 'super_admin', 'teacher']:
            cursor.execute('SELECT id FROM learning_paths WHERE id = ? AND user_id = ?', (path_id, user_id))
            if not cursor.fetchone():
                conn.close()
                return create_response(403, '无权操作')

        if request.method == 'GET':
            cursor.execute('''
                SELECT id, item_type, item_id, item_title, order_num, completed, completed_at
                FROM learning_path_items
                WHERE path_id = ?
                ORDER BY order_num
            ''', (path_id,))

            items = []
            for row in cursor.fetchall():
                items.append({
                    'id': row['id'],
                    'item_type': row['item_type'],
                    'item_id': row['item_id'],
                    'item_title': row['item_title'],
                    'order_num': row['order_num'],
                    'completed': row['completed'] == 1,
                    'completed_at': row['completed_at']
                })
            conn.close()
            return create_response(200, 'success', {'items': items})

        elif request.method == 'POST':
            data = request.get_json() or {}
            item_type = data.get('item_type', '')
            item_id = data.get('item_id')
            item_title = data.get('item_title', '')
            order_num = data.get('order_num', 0)

            if not item_type or not item_title:
                conn.close()
                return create_response(400, '缺少必要参数')

            cursor.execute('INSERT INTO learning_path_items (path_id, item_type, item_id, item_title, order_num) VALUES (?, ?, ?, ?, ?)',
                         (path_id, item_type, item_id, item_title, order_num))
            conn.commit()
            conn.close()
            return create_response(201, '学习项添加成功')

    except Exception as e:
        logger.error(f"学习项操作失败: {e}")
        return create_response(500, '学习项操作失败')


@learning_enhancement_api.route('/api/learning/paths/<int:path_id>/items/<int:item_id>', methods=['PUT', 'DELETE'])
@require_login
def path_item_detail(path_id, item_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role not in ['admin', 'super_admin', 'teacher']:
            cursor.execute('SELECT lp.id FROM learning_paths lp JOIN learning_path_items lpi ON lp.id = lpi.path_id WHERE lpi.id = ? AND lp.user_id = ?', (item_id, user_id))
            if not cursor.fetchone():
                conn.close()
                return create_response(403, '无权操作')

        if request.method == 'PUT':
            data = request.get_json() or {}
            completed = data.get('completed', False)

            cursor.execute('''
                UPDATE learning_path_items 
                SET completed = ?, completed_at = ? 
                WHERE id = ? AND path_id = ?
            ''', (1 if completed else 0, datetime.now().isoformat() if completed else None, item_id, path_id))

            cursor.execute('SELECT COUNT(*) FROM learning_path_items WHERE path_id = ?', (path_id,))
            total = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM learning_path_items WHERE path_id = ? AND completed = 1', (path_id,))
            completed_count = cursor.fetchone()[0] or 0

            progress = (completed_count / total) * 100 if total > 0 else 0
            cursor.execute('UPDATE learning_paths SET progress = ? WHERE id = ?', (progress, path_id))

            conn.commit()
            conn.close()
            return create_response(200, '学习项状态更新成功', {'progress': round(progress, 2)})

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM learning_path_items WHERE id = ? AND path_id = ?', (item_id, path_id))
            conn.commit()
            conn.close()
            return create_response(200, '学习项已删除')

    except Exception as e:
        logger.error(f"学习项操作失败: {e}")
        return create_response(500, '学习项操作失败')


@learning_enhancement_api.route('/api/learning/records', methods=['GET'])
@require_login
def get_learning_records():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        activity_type = request.args.get('activity_type', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if role not in ['admin', 'super_admin', 'teacher']:
            where_clauses.append('user_id = ?')
            params.append(user_id)
        else:
            target_user_id = request.args.get('user_id')
            if target_user_id:
                where_clauses.append('user_id = ?')
                params.append(target_user_id)

        if activity_type:
            where_clauses.append('activity_type = ?')
            params.append(activity_type)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM learning_records {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, user_id, activity_type, activity_id, activity_title, duration, 
                   progress, score, details, created_at
            FROM learning_records
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'activity_type': row['activity_type'],
                'activity_id': row['activity_id'],
                'activity_title': row['activity_title'] or '',
                'duration': row['duration'] or 0,
                'progress': row['progress'] or 0,
                'score': row['score'] or 0,
                'details': row['details'] or '',
                'created_at': row['created_at']
            })
        conn.close()

        return create_response(200, 'success', {
            'records': records,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取学习记录失败: {e}")
        return create_response(500, '获取学习记录失败')


@learning_enhancement_api.route('/api/learning/records', methods=['POST'])
@require_login
def create_learning_record():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        activity_type = data.get('activity_type', '')
        activity_id = data.get('activity_id')
        activity_title = data.get('activity_title', '')
        duration = data.get('duration', 0)
        progress = data.get('progress', 0)
        score = data.get('score', 0)
        details = data.get('details', '')

        if not activity_type:
            return create_response(400, '活动类型不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO learning_records (user_id, activity_type, activity_id, activity_title, duration, progress, score, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (user_id, activity_type, activity_id, activity_title, duration, progress, score, details))
        record_id = cursor.lastrowid

        cursor.execute('SELECT * FROM learning_streaks WHERE user_id = ?', (user_id,))
        streak_row = cursor.fetchone()
        today = datetime.now().date().isoformat()

        if streak_row:
            last_date = streak_row['last_learning_date']
            if last_date == today:
                pass
            elif last_date == (datetime.now() - timedelta(days=1)).date().isoformat():
                cursor.execute('UPDATE learning_streaks SET current_streak = current_streak + 1, longest_streak = MAX(longest_streak, current_streak + 1), last_learning_date = ?, total_days = total_days + 1 WHERE user_id = ?',
                             (today, user_id))
            else:
                cursor.execute('UPDATE learning_streaks SET current_streak = 1, longest_streak = MAX(longest_streak, 1), last_learning_date = ?, total_days = total_days + 1 WHERE user_id = ?',
                             (today, user_id))
        else:
            cursor.execute('INSERT INTO learning_streaks (user_id, current_streak, longest_streak, last_learning_date, total_days) VALUES (?, 1, 1, ?, 1)',
                         (user_id, today))

        conn.commit()
        conn.close()

        return create_response(201, '学习记录创建成功', {'record_id': record_id})

    except Exception as e:
        logger.error(f"创建学习记录失败: {e}")
        return create_response(500, '创建学习记录失败')


@learning_enhancement_api.route('/api/learning/achievements', methods=['GET'])
@require_login
def get_achievements():
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, achievement_code, name, description, icon, points, type FROM achievements')
        all_achievements = []
        for row in cursor.fetchall():
            cursor.execute('SELECT unlocked_at, progress FROM user_achievements WHERE user_id = ? AND achievement_id = ?', (user_id, row['id']))
            user_achievement = cursor.fetchone()

            all_achievements.append({
                'id': row['id'],
                'achievement_code': row['achievement_code'],
                'name': row['name'],
                'description': row['description'] or '',
                'icon': row['icon'],
                'points': row['points'] or 0,
                'type': row['type'],
                'unlocked': user_achievement is not None,
                'unlocked_at': user_achievement['unlocked_at'] if user_achievement else None,
                'progress': user_achievement['progress'] if user_achievement else 0
            })
        conn.close()
        return create_response(200, 'success', {'achievements': all_achievements})

    except Exception as e:
        logger.error(f"获取成就失败: {e}")
        return create_response(500, '获取成就失败')


@learning_enhancement_api.route('/api/learning/achievements', methods=['POST'])
@require_admin
def create_achievement():
    try:
        data = request.get_json() or {}
        achievement_code = data.get('achievement_code', '')
        name = data.get('name', '')
        description = data.get('description', '')
        icon = data.get('icon', '🏆')
        points = data.get('points', 0)
        achievement_type = data.get('type', 'bronze')
        condition = data.get('condition', '')

        if not achievement_code or not name:
            return create_response(400, '成就代码和名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM achievements WHERE achievement_code = ?', (achievement_code,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '成就代码已存在')

        cursor.execute('INSERT INTO achievements (achievement_code, name, description, icon, points, type, condition) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (achievement_code, name, description, icon, points, achievement_type, condition))
        achievement_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '成就创建成功', {'achievement_id': achievement_id})

    except Exception as e:
        logger.error(f"创建成就失败: {e}")
        return create_response(500, '创建成就失败')


@learning_enhancement_api.route('/api/learning/achievements/unlock', methods=['POST'])
@require_login
def unlock_achievement():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        achievement_id = data.get('achievement_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM achievements WHERE id = ?', (achievement_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '成就不存在')

        cursor.execute('SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?', (user_id, achievement_id))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '成就已解锁')

        cursor.execute('INSERT INTO user_achievements (user_id, achievement_id, unlocked_at, progress) VALUES (?, ?, ?, 100)',
                     (user_id, achievement_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return create_response(200, '成就解锁成功')

    except Exception as e:
        logger.error(f"解锁成就失败: {e}")
        return create_response(500, '解锁成就失败')


@learning_enhancement_api.route('/api/learning/streak/<int:user_id>', methods=['GET'])
@require_login
def get_streak(user_id):
    try:
        current_user_id = session.get('user_id')
        role = session.get('role')

        if role not in ['admin', 'super_admin', 'teacher'] and current_user_id != user_id:
            return create_response(403, '无权查看')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT current_streak, longest_streak, last_learning_date, total_days FROM learning_streaks WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row:
            streak = {
                'current_streak': row['current_streak'] or 0,
                'longest_streak': row['longest_streak'] or 0,
                'last_learning_date': row['last_learning_date'],
                'total_days': row['total_days'] or 0
            }
        else:
            streak = {
                'current_streak': 0,
                'longest_streak': 0,
                'last_learning_date': None,
                'total_days': 0
            }

        conn.close()
        return create_response(200, 'success', {'streak': streak})

    except Exception as e:
        logger.error(f"获取学习连续天数失败: {e}")
        return create_response(500, '获取学习连续天数失败')


@learning_enhancement_api.route('/api/learning/communities', methods=['GET'])
@require_login
def get_communities():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT lc.id, lc.name, lc.description, lc.icon, lc.member_count, lc.created_at,
                   COUNT(DISTINCT cp.id) as post_count
            FROM learning_communities lc
            LEFT JOIN community_posts cp ON lc.id = cp.community_id
            GROUP BY lc.id
            ORDER BY lc.member_count DESC
        ''')

        communities = []
        user_id = session.get('user_id')
        for row in cursor.fetchall():
            cursor.execute('SELECT role FROM community_members WHERE community_id = ? AND user_id = ?', (row['id'], user_id))
            member_row = cursor.fetchone()

            communities.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'icon': row['icon'],
                'member_count': row['member_count'] or 0,
                'post_count': row['post_count'] or 0,
                'created_at': row['created_at'],
                'is_member': member_row is not None,
                'role': member_row['role'] if member_row else None
            })
        conn.close()
        return create_response(200, 'success', {'communities': communities})

    except Exception as e:
        logger.error(f"获取学习社区失败: {e}")
        return create_response(500, '获取学习社区失败')


@learning_enhancement_api.route('/api/learning/communities', methods=['POST'])
@require_admin
def create_community():
    try:
        data = request.get_json() or {}
        name = data.get('name', '')
        description = data.get('description', '')
        icon = data.get('icon', '📚')

        if not name:
            return create_response(400, '社区名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM learning_communities WHERE name = ?', (name,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '社区名称已存在')

        cursor.execute('INSERT INTO learning_communities (name, description, icon) VALUES (?, ?, ?)',
                     (name, description, icon))
        community_id = cursor.lastrowid

        cursor.execute('INSERT INTO community_members (community_id, user_id, role) VALUES (?, ?, ?)',
                     (community_id, session.get('user_id'), 'admin'))
        cursor.execute('UPDATE learning_communities SET member_count = 1 WHERE id = ?', (community_id,))

        conn.commit()
        conn.close()

        return create_response(201, '学习社区创建成功', {'community_id': community_id})

    except Exception as e:
        logger.error(f"创建学习社区失败: {e}")
        return create_response(500, '创建学习社区失败')


@learning_enhancement_api.route('/api/learning/communities/<int:community_id>/join', methods=['POST'])
@require_login
def join_community(community_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM learning_communities WHERE id = ?', (community_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '社区不存在')

        cursor.execute('SELECT id FROM community_members WHERE community_id = ? AND user_id = ?', (community_id, user_id))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '已加入该社区')

        cursor.execute('INSERT INTO community_members (community_id, user_id, role) VALUES (?, ?, ?)',
                     (community_id, user_id, 'member'))
        cursor.execute('UPDATE learning_communities SET member_count = member_count + 1 WHERE id = ?', (community_id,))

        conn.commit()
        conn.close()

        return create_response(200, '加入社区成功')

    except Exception as e:
        logger.error(f"加入社区失败: {e}")
        return create_response(500, '加入社区失败')


@learning_enhancement_api.route('/api/learning/communities/<int:community_id>/posts', methods=['GET', 'POST'])
@require_login
def community_posts(community_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM community_members WHERE community_id = ? AND user_id = ?', (community_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return create_response(403, '请先加入社区')

        if request.method == 'GET':
            cursor.execute('''
                SELECT cp.id, cp.user_id, u.username, cp.title, cp.content, cp.views, 
                       cp.likes, cp.comments, cp.created_at
                FROM community_posts cp
                JOIN users u ON cp.user_id = u.id
                WHERE cp.community_id = ?
                ORDER BY cp.created_at DESC
            ''', (community_id,))

            posts = []
            for row in cursor.fetchall():
                posts.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'title': row['title'],
                    'content': row['content'] or '',
                    'views': row['views'] or 0,
                    'likes': row['likes'] or 0,
                    'comments': row['comments'] or 0,
                    'created_at': row['created_at']
                })
            conn.close()
            return create_response(200, 'success', {'posts': posts})

        elif request.method == 'POST':
            data = request.get_json() or {}
            title = data.get('title', '')
            content = data.get('content', '')

            if not title:
                conn.close()
                return create_response(400, '帖子标题不能为空')

            cursor.execute('INSERT INTO community_posts (community_id, user_id, title, content) VALUES (?, ?, ?, ?)',
                         (community_id, user_id, title, content))
            post_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return create_response(201, '帖子发布成功', {'post_id': post_id})

    except Exception as e:
        logger.error(f"社区帖子操作失败: {e}")
        return create_response(500, '社区帖子操作失败')


@learning_enhancement_api.route('/api/learning/posts/<int:post_id>/comments', methods=['GET', 'POST'])
@require_login
def post_comments(post_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('''
                SELECT pc.id, pc.user_id, u.username, pc.content, pc.reply_to, pc.created_at
                FROM post_comments pc
                JOIN users u ON pc.user_id = u.id
                WHERE pc.post_id = ?
                ORDER BY pc.created_at ASC
            ''', (post_id,))

            comments = []
            for row in cursor.fetchall():
                comments.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'content': row['content'],
                    'reply_to': row['reply_to'],
                    'created_at': row['created_at']
                })
            conn.close()
            return create_response(200, 'success', {'comments': comments})

        elif request.method == 'POST':
            data = request.get_json() or {}
            content = data.get('content', '')
            reply_to = data.get('reply_to')

            if not content:
                conn.close()
                return create_response(400, '评论内容不能为空')

            cursor.execute('INSERT INTO post_comments (post_id, user_id, content, reply_to) VALUES (?, ?, ?, ?)',
                         (post_id, user_id, content, reply_to))

            cursor.execute('UPDATE community_posts SET comments = comments + 1 WHERE id = ?', (post_id,))

            conn.commit()
            conn.close()

            return create_response(201, '评论发布成功')

    except Exception as e:
        logger.error(f"帖子评论操作失败: {e}")
        return create_response(500, '帖子评论操作失败')