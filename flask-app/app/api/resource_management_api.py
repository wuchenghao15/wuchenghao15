# -*- coding: utf-8 -*-
"""
资源管理系统API - 文件上传、资源分类、资源分享、权限控制
"""

from flask import Blueprint, jsonify, request, session, send_from_directory
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

resource_management_api = Blueprint('resource_management_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


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
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_uuid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                original_name TEXT,
                file_path TEXT,
                file_type TEXT,
                file_size INTEGER DEFAULT 0,
                mime_type TEXT,
                description TEXT,
                category_id INTEGER,
                tags TEXT DEFAULT '[]',
                uploaded_by INTEGER NOT NULL,
                access_type TEXT DEFAULT 'private',
                thumbnail TEXT,
                downloads INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES resource_categories(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                parent_id INTEGER,
                icon TEXT DEFAULT '📁',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES resource_categories(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                user_id INTEGER,
                group_id INTEGER,
                permission TEXT DEFAULT 'view',
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES user_groups(id),
                UNIQUE(resource_id, user_id, group_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                share_token TEXT UNIQUE NOT NULL,
                expires_at TEXT,
                downloads_limit INTEGER DEFAULT 0,
                downloads_count INTEGER DEFAULT 0,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                user_id INTEGER,
                download_time TEXT DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(resource_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                version_number INTEGER DEFAULT 1,
                file_path TEXT,
                file_size INTEGER DEFAULT 0,
                changelog TEXT,
                uploaded_by INTEGER NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 资源管理系统表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建资源管理系统表失败: {e}")


create_tables()


@resource_management_api.route('/api/resources', methods=['GET'])
def get_resources():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        category_id = request.args.get('category_id', '')
        file_type = request.args.get('file_type', '')
        access_type = request.args.get('access_type', '')
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if user_id and role not in ['admin', 'super_admin']:
            where_clauses.append('(r.access_type = "public" OR r.uploaded_by = ?)')
            params.append(user_id)
        elif not user_id:
            where_clauses.append('r.access_type = "public"')

        if category_id:
            where_clauses.append('r.category_id = ?')
            params.append(category_id)

        if file_type:
            where_clauses.append('r.file_type = ?')
            params.append(file_type)

        if access_type:
            where_clauses.append('r.access_type = ?')
            params.append(access_type)

        if keyword:
            where_clauses.append('(r.name LIKE ? OR r.description LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'SELECT COUNT(*) FROM resources r {where_sql}', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT r.id, r.resource_uuid, r.name, r.original_name, r.file_type, 
                   r.file_size, r.mime_type, r.description, r.category_id, r.tags,
                   r.uploaded_by, u.username as uploaded_name, r.access_type, 
                   r.downloads, r.views, r.created_at, r.updated_at,
                   rc.name as category_name, rc.icon as category_icon
            FROM resources r
            JOIN users u ON r.uploaded_by = u.id
            LEFT JOIN resource_categories rc ON r.category_id = rc.id
            {where_sql}
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        resources = []
        for row in cursor.fetchall():
            is_favorite = False
            if user_id:
                cursor.execute('SELECT id FROM resource_favorites WHERE resource_id = ? AND user_id = ?',
                             (row['id'], user_id))
                is_favorite = cursor.fetchone() is not None

            resources.append({
                'id': row['id'],
                'resource_uuid': row['resource_uuid'],
                'name': row['name'],
                'original_name': row['original_name'] or '',
                'file_type': row['file_type'] or '',
                'file_size': row['file_size'] or 0,
                'mime_type': row['mime_type'] or '',
                'description': row['description'] or '',
                'category_id': row['category_id'],
                'category_name': row['category_name'] or '',
                'category_icon': row['category_icon'] or '',
                'tags': json.loads(row['tags'] or '[]'),
                'uploaded_by': row['uploaded_by'],
                'uploaded_name': row['uploaded_name'],
                'access_type': row['access_type'],
                'downloads': row['downloads'] or 0,
                'views': row['views'] or 0,
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'is_favorite': is_favorite
            })
        conn.close()

        return create_response(200, 'success', {
            'resources': resources,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取资源列表失败: {e}")
        return create_response(500, '获取资源列表失败')


@resource_management_api.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource_detail(resource_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT r.id, r.resource_uuid, r.name, r.original_name, r.file_path, 
                   r.file_type, r.file_size, r.mime_type, r.description, r.category_id, 
                   r.tags, r.uploaded_by, u.username as uploaded_name, r.access_type, 
                   r.thumbnail, r.downloads, r.views, r.created_at, r.updated_at,
                   rc.name as category_name
            FROM resources r
            JOIN users u ON r.uploaded_by = u.id
            LEFT JOIN resource_categories rc ON r.category_id = rc.id
            WHERE r.id = ?
        ''', (resource_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '资源不存在')

        if row['access_type'] == 'private' and user_id not in [row['uploaded_by']] and role not in ['admin', 'super_admin']:
            cursor.execute('SELECT id FROM resource_permissions WHERE resource_id = ? AND user_id = ?',
                         (resource_id, user_id))
            if not cursor.fetchone():
                conn.close()
                return create_response(403, '无权访问')

        cursor.execute('UPDATE resources SET views = views + 1 WHERE id = ?', (resource_id,))

        is_favorite = False
        if user_id:
            cursor.execute('SELECT id FROM resource_favorites WHERE resource_id = ? AND user_id = ?',
                         (resource_id, user_id))
            is_favorite = cursor.fetchone() is not None

        conn.commit()
        conn.close()

        return create_response(200, 'success', {
            'id': row['id'],
            'resource_uuid': row['resource_uuid'],
            'name': row['name'],
            'original_name': row['original_name'] or '',
            'file_path': row['file_path'] or '',
            'file_type': row['file_type'] or '',
            'file_size': row['file_size'] or 0,
            'mime_type': row['mime_type'] or '',
            'description': row['description'] or '',
            'category_id': row['category_id'],
            'category_name': row['category_name'] or '',
            'tags': json.loads(row['tags'] or '[]'),
            'uploaded_by': row['uploaded_by'],
            'uploaded_name': row['uploaded_name'],
            'access_type': row['access_type'],
            'thumbnail': row['thumbnail'] or '',
            'downloads': row['downloads'] or 0,
            'views': row['views'] + 1,
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'is_favorite': is_favorite
        })

    except Exception as e:
        logger.error(f"获取资源详情失败: {e}")
        return create_response(500, '获取资源详情失败')


@resource_management_api.route('/api/resources/upload', methods=['POST'])
@require_login
def upload_resource():
    try:
        user_id = session.get('user_id')

        if 'file' not in request.files:
            return create_response(400, '请选择文件')

        file = request.files['file']
        if file.filename == '':
            return create_response(400, '请选择文件')

        name = request.form.get('name', file.filename)
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        access_type = request.form.get('access_type', 'private')
        tags = request.form.get('tags', '[]')

        resource_uuid = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        saved_filename = f"{resource_uuid}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, saved_filename)

        file.save(file_path)
        file_size = os.path.getsize(file_path)
        file_type = file_ext[1:].lower() if file_ext else 'other'

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO resources 
            (resource_uuid, name, original_name, file_path, file_type, file_size, 
             mime_type, description, category_id, tags, uploaded_by, access_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            resource_uuid, name, file.filename, saved_filename, file_type, file_size,
            file.content_type, description, category_id, tags, user_id, access_type
        ))

        resource_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '文件上传成功', {'resource_id': resource_id, 'name': name})

    except Exception as e:
        logger.error(f"上传资源失败: {e}")
        return create_response(500, '上传资源失败')


@resource_management_api.route('/api/resources/<int:resource_id>', methods=['PUT', 'DELETE'])
@require_login
def manage_resource(resource_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT uploaded_by, file_path FROM resources WHERE id = ?', (resource_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '资源不存在')

        if role not in ['admin', 'super_admin'] and row['uploaded_by'] != user_id:
            conn.close()
            return create_response(403, '无权操作')

        if request.method == 'PUT':
            data = request.get_json() or {}
            updates = []
            params = []

            if 'name' in data:
                updates.append('name = ?')
                params.append(data['name'])
            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])
            if 'category_id' in data:
                updates.append('category_id = ?')
                params.append(data['category_id'])
            if 'tags' in data:
                updates.append('tags = ?')
                params.append(json.dumps(data['tags']))
            if 'access_type' in data:
                updates.append('access_type = ?')
                params.append(data['access_type'])

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(resource_id)

            cursor.execute(f'UPDATE resources SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '资源更新成功')

        elif request.method == 'DELETE':
            if row['file_path']:
                full_path = os.path.join(UPLOAD_FOLDER, row['file_path'])
                if os.path.exists(full_path):
                    os.remove(full_path)

            cursor.execute('DELETE FROM resource_permissions WHERE resource_id = ?', (resource_id,))
            cursor.execute('DELETE FROM resource_shares WHERE resource_id = ?', (resource_id,))
            cursor.execute('DELETE FROM resource_favorites WHERE resource_id = ?', (resource_id,))
            cursor.execute('DELETE FROM resource_downloads WHERE resource_id = ?', (resource_id,))
            cursor.execute('DELETE FROM resource_versions WHERE resource_id = ?', (resource_id,))
            cursor.execute('DELETE FROM resources WHERE id = ?', (resource_id,))

            conn.commit()
            conn.close()
            return create_response(200, '资源已删除')

    except Exception as e:
        logger.error(f"资源管理操作失败: {e}")
        return create_response(500, '资源管理操作失败')


@resource_management_api.route('/api/resources/<int:resource_id>/download', methods=['GET'])
@require_login
def download_resource(resource_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name, file_path, access_type, uploaded_by FROM resources WHERE id = ?', (resource_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '资源不存在')

        if row['access_type'] == 'private' and user_id not in [row['uploaded_by']] and role not in ['admin', 'super_admin']:
            cursor.execute('SELECT id FROM resource_permissions WHERE resource_id = ? AND user_id = ?',
                         (resource_id, user_id))
            if not cursor.fetchone():
                conn.close()
                return create_response(403, '无权下载')

        cursor.execute('UPDATE resources SET downloads = downloads + 1 WHERE id = ?', (resource_id,))
        cursor.execute('INSERT INTO resource_downloads (resource_id, user_id, ip_address) VALUES (?, ?, ?)',
                     (resource_id, user_id, request.remote_addr))

        conn.commit()
        conn.close()

        return send_from_directory(UPLOAD_FOLDER, row['file_path'], as_attachment=True, download_name=row['name'])

    except Exception as e:
        logger.error(f"下载资源失败: {e}")
        return create_response(500, '下载资源失败')


@resource_management_api.route('/api/resources/<int:resource_id>/share', methods=['POST'])
@require_login
def create_share_link(resource_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        data = request.get_json() or {}
        expires_days = data.get('expires_days', 7)
        downloads_limit = data.get('downloads_limit', 0)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT uploaded_by FROM resources WHERE id = ?', (resource_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '资源不存在')

        if role not in ['admin', 'super_admin'] and row['uploaded_by'] != user_id:
            conn.close()
            return create_response(403, '无权操作')

        share_token = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days > 0 else None

        cursor.execute('INSERT INTO resource_shares (resource_id, share_token, expires_at, downloads_limit, created_by) VALUES (?, ?, ?, ?, ?)',
                     (resource_id, share_token, expires_at, downloads_limit, user_id))

        conn.commit()
        conn.close()

        return create_response(200, '分享链接创建成功', {
            'share_token': share_token,
            'share_url': f'/api/resources/share/{share_token}',
            'expires_at': expires_at,
            'downloads_limit': downloads_limit
        })

    except Exception as e:
        logger.error(f"创建分享链接失败: {e}")
        return create_response(500, '创建分享链接失败')


@resource_management_api.route('/api/resources/share/<share_token>', methods=['GET'])
def access_shared_resource(share_token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rs.resource_id, rs.expires_at, rs.downloads_limit, rs.downloads_count,
                   r.name, r.file_path, r.access_type
            FROM resource_shares rs
            JOIN resources r ON rs.resource_id = r.id
            WHERE rs.share_token = ?
        ''', (share_token,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '分享链接不存在')

        if row['expires_at'] and datetime.now().isoformat() > row['expires_at']:
            conn.close()
            return create_response(400, '分享链接已过期')

        if row['downloads_limit'] > 0 and row['downloads_count'] >= row['downloads_limit']:
            conn.close()
            return create_response(400, '分享链接下载次数已用完')

        cursor.execute('UPDATE resource_shares SET downloads_count = downloads_count + 1 WHERE share_token = ?',
                     (share_token,))
        cursor.execute('UPDATE resources SET downloads = downloads + 1 WHERE id = ?', (row['resource_id'],))
        cursor.execute('INSERT INTO resource_downloads (resource_id, ip_address) VALUES (?, ?)',
                     (row['resource_id'], request.remote_addr))

        conn.commit()
        conn.close()

        return send_from_directory(UPLOAD_FOLDER, row['file_path'], as_attachment=True, download_name=row['name'])

    except Exception as e:
        logger.error(f"访问分享资源失败: {e}")
        return create_response(500, '访问分享资源失败')


@resource_management_api.route('/api/resources/<int:resource_id>/favorite', methods=['POST'])
@require_login
def toggle_favorite(resource_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        action = data.get('action', 'add')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM resources WHERE id = ?', (resource_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '资源不存在')

        if action == 'add':
            cursor.execute('INSERT OR IGNORE INTO resource_favorites (resource_id, user_id) VALUES (?, ?)',
                         (resource_id, user_id))
            conn.commit()
            conn.close()
            return create_response(200, '资源已收藏')
        else:
            cursor.execute('DELETE FROM resource_favorites WHERE resource_id = ? AND user_id = ?',
                         (resource_id, user_id))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected == 0:
                return create_response(404, '未收藏该资源')
            return create_response(200, '资源已取消收藏')

    except Exception as e:
        logger.error(f"收藏资源失败: {e}")
        return create_response(500, '收藏资源失败')


@resource_management_api.route('/api/resource_categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, description, parent_id, icon, sort_order FROM resource_categories ORDER BY sort_order')
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'parent_id': row['parent_id'],
                'icon': row['icon'],
                'sort_order': row['sort_order']
            })
        conn.close()
        return create_response(200, 'success', {'categories': categories})

    except Exception as e:
        logger.error(f"获取资源分类失败: {e}")
        return create_response(500, '获取资源分类失败')


@resource_management_api.route('/api/resource_categories', methods=['POST'])
@require_admin
def create_category():
    try:
        data = request.get_json() or {}
        name = data.get('name', '')
        description = data.get('description', '')
        parent_id = data.get('parent_id')
        icon = data.get('icon', '📁')
        sort_order = data.get('sort_order', 0)

        if not name:
            return create_response(400, '分类名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM resource_categories WHERE name = ?', (name,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '分类名称已存在')

        cursor.execute('INSERT INTO resource_categories (name, description, parent_id, icon, sort_order) VALUES (?, ?, ?, ?, ?)',
                     (name, description, parent_id, icon, sort_order))

        conn.commit()
        conn.close()
        return create_response(201, '资源分类创建成功')

    except Exception as e:
        logger.error(f"创建资源分类失败: {e}")
        return create_response(500, '创建资源分类失败')