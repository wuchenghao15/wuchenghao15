from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
"""
表单管理服务
===============
提供表单定义、表单字段、表单数据的完整管理功能。

核心模块：
1. 表单模板管理 - 创建、编辑、删除表单模板
2. 表单字段管理 - 添加不同类型的字段（文本、数字、选择、日期等）
3. 表单数据管理 - 用户提交的表单数据存储和查询
4. 表单统计分析 - 表单提交统计、字段数据分析
"""
import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('FormManagerService')


class FormManagerService:
    """表单管理服务"""

    FIELD_TYPES = {
        'text': {'name': '文本输入', 'description': '单行文本输入'},
        'textarea': {'name': '多行文本', 'description': '多行文本输入'},
        'number': {'name': '数字', 'description': '数字输入'},
        'email': {'name': '邮箱', 'description': '邮箱地址'},
        'phone': {'name': '电话', 'description': '手机号码'},
        'date': {'name': '日期', 'description': '日期选择'},
        'datetime': {'name': '日期时间', 'description': '日期时间选择'},
        'select': {'name': '单选', 'description': '单选下拉框'},
        'checkbox': {'name': '多选', 'description': '多选框'},
        'radio': {'name': '单选按钮', 'description': '单选按钮组'},
        'boolean': {'name': '布尔值', 'description': '是/否选择'},
        'file': {'name': '文件上传', 'description': '文件上传'},
        'password': {'name': '密码', 'description': '密码输入'}
    }

    FORM_STATUS = {
        'draft': {'name': '草稿', 'description': '表单草稿，未发布'},
        'published': {'name': '已发布', 'description': '表单已发布，可填写'},
        'closed': {'name': '已关闭', 'description': '表单已关闭，不可填写'},
        'archived': {'name': '已归档', 'description': '表单已归档'}
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'draft',
                    fields TEXT DEFAULT '[]',
                    settings TEXT DEFAULT '{}',
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    submit_count INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_fields (
                    id TEXT PRIMARY KEY,
                    form_id TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    name TEXT NOT NULL,
                    placeholder TEXT,
                    required INTEGER DEFAULT 0,
                    options TEXT DEFAULT '[]',
                    default_value TEXT,
                    validation TEXT DEFAULT '{}',
                    "order" INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (form_id) REFERENCES form_templates(id) ON DELETE CASCADE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS form_submissions (
                    id TEXT PRIMARY KEY,
                    form_id TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    data TEXT NOT NULL,
                    status TEXT DEFAULT 'submitted',
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (form_id) REFERENCES form_templates(id) ON DELETE CASCADE
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_form_fields_form_id ON form_fields(form_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_form_submissions_form_id ON form_submissions(form_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_form_submissions_user_id ON form_submissions(user_id)
            ''')

            conn.commit()
            logger.info("表单管理数据库表初始化完成")

    def create_form_template(self, name: str, description: str = '', created_by: str = '', 
                            settings: Dict = None) -> Dict[str, Any]:
        """创建表单模板"""
        form_id = str(uuid.uuid4())
        settings = settings or {}

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO form_templates (id, name, description, status, settings, created_by, created_at, updated_at)
                VALUES (?, ?, ?, 'draft', ?, ?, ?, ?)
            ''', (form_id, name, description, json.dumps(settings), created_by, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()

        logger.info(f"创建表单模板: {name} (ID: {form_id})")
        return {'success': True, 'form_id': form_id, 'message': '表单模板创建成功'}

    def update_form_template(self, form_id: str, **kwargs) -> Dict[str, Any]:
        """更新表单模板"""
        update_fields = []
        update_values = []

        if 'name' in kwargs:
            update_fields.append('name = ?')
            update_values.append(kwargs['name'])
        if 'description' in kwargs:
            update_fields.append('description = ?')
            update_values.append(kwargs['description'])
        if 'status' in kwargs:
            update_fields.append('status = ?')
            update_values.append(kwargs['status'])
        if 'settings' in kwargs:
            update_fields.append('settings = ?')
            update_values.append(json.dumps(kwargs['settings']))

        update_values.append(form_id)

        if not update_fields:
            return {'success': False, 'error': '没有需要更新的字段'}

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE form_templates SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?
            ''', [*update_values, datetime.now().isoformat()])
            conn.commit()

        logger.info(f"更新表单模板: {form_id}")
        return {'success': True, 'message': '表单模板更新成功'}

    def delete_form_template(self, form_id: str) -> Dict[str, Any]:
        """删除表单模板"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM form_templates WHERE id = ?', (form_id,))
            conn.commit()

        logger.info(f"删除表单模板: {form_id}")
        return {'success': True, 'message': '表单模板删除成功'}

    def get_form_template(self, form_id: str) -> Dict[str, Any]:
        """获取表单模板详情"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM form_templates WHERE id = ?', (form_id,))
            row = cursor.fetchone()

            if not row:
                return {'success': False, 'error': '表单模板不存在'}

            form = dict(row)
            form['fields'] = self.get_form_fields(form_id)['data']
            form['settings'] = json.loads(form.get('settings', '{}'))

            return {'success': True, 'data': form}

    def list_form_templates(self, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取表单模板列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = 'SELECT * FROM form_templates'
            params = []

            if status:
                query += ' WHERE status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([page_size, (page - 1) * page_size])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            cursor.execute('SELECT COUNT(*) FROM form_templates' + (' WHERE status = ?' if status else ''), 
                          params[:-2] if status else [])
            total = cursor.fetchone()[0]

            forms = []
            for row in rows:
                form = dict(row)
                form['settings'] = json.loads(form.get('settings', '{}'))
                forms.append(form)

            return {'success': True, 'data': forms, 'total': total, 'page': page, 'page_size': page_size}

    def add_form_field(self, form_id: str, field_type: str, label: str, name: str, 
                       placeholder: str = '', required: bool = False, options: List[str] = None,
                       default_value: str = '', validation: Dict = None, order: int = 0) -> Dict[str, Any]:
        """添加表单字段"""
        if field_type not in self.FIELD_TYPES:
            return {'success': False, 'error': f'不支持的字段类型: {field_type}'}

        field_id = str(uuid.uuid4())
        options = options or []
        validation = validation or {}

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO form_fields (id, form_id, field_type, label, name, placeholder, 
                                         required, options, default_value, validation, order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (field_id, form_id, field_type, label, name, placeholder,
                  1 if required else 0, json.dumps(options), default_value, 
                  json.dumps(validation), order, datetime.now().isoformat()))
            conn.commit()

        logger.info(f"添加表单字段: {name} (ID: {field_id})")
        return {'success': True, 'field_id': field_id, 'message': '表单字段添加成功'}

    def update_form_field(self, field_id: str, **kwargs) -> Dict[str, Any]:
        """更新表单字段"""
        update_fields = []
        update_values = []

        if 'field_type' in kwargs:
            update_fields.append('field_type = ?')
            update_values.append(kwargs['field_type'])
        if 'label' in kwargs:
            update_fields.append('label = ?')
            update_values.append(kwargs['label'])
        if 'name' in kwargs:
            update_fields.append('name = ?')
            update_values.append(kwargs['name'])
        if 'placeholder' in kwargs:
            update_fields.append('placeholder = ?')
            update_values.append(kwargs['placeholder'])
        if 'required' in kwargs:
            update_fields.append('required = ?')
            update_values.append(1 if kwargs['required'] else 0)
        if 'options' in kwargs:
            update_fields.append('options = ?')
            update_values.append(json.dumps(kwargs['options']))
        if 'default_value' in kwargs:
            update_fields.append('default_value = ?')
            update_values.append(kwargs['default_value'])
        if 'validation' in kwargs:
            update_fields.append('validation = ?')
            update_values.append(json.dumps(kwargs['validation']))
        if 'order' in kwargs:
            update_fields.append('order = ?')
            update_values.append(kwargs['order'])

        update_values.append(field_id)

        if not update_fields:
            return {'success': False, 'error': '没有需要更新的字段'}

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE form_fields SET {", ".join(update_fields)} WHERE id = ?', update_values)
            conn.commit()

        return {'success': True, 'message': '表单字段更新成功'}

    def delete_form_field(self, field_id: str) -> Dict[str, Any]:
        """删除表单字段"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM form_fields WHERE id = ?', (field_id,))
            conn.commit()

        return {'success': True, 'message': '表单字段删除成功'}

    def get_form_fields(self, form_id: str) -> Dict[str, Any]:
        """获取表单字段列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM form_fields WHERE form_id = ? ORDER BY order ASC', (form_id,))
            rows = cursor.fetchall()

            fields = []
            for row in rows:
                field = dict(row)
                field['options'] = json.loads(field.get('options', '[]'))
                field['validation'] = json.loads(field.get('validation', '{}'))
                field['required'] = bool(field['required'])
                fields.append(field)

            return {'success': True, 'data': fields}

    def submit_form(self, form_id: str, data: Dict, user_id: str = '', username: str = '') -> Dict[str, Any]:
        """提交表单"""
        submission_id = str(uuid.uuid4())

        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM form_templates WHERE id = ?', (form_id,))
            row = cursor.fetchone()

            if not row:
                return {'success': False, 'error': '表单不存在'}

            if row[0] != 'published':
                return {'success': False, 'error': '表单未发布或已关闭'}

            cursor.execute('''
                INSERT INTO form_submissions (id, form_id, user_id, username, data, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (submission_id, form_id, user_id, username, json.dumps(data), datetime.now().isoformat()))

            cursor.execute('UPDATE form_templates SET submit_count = submit_count + 1 WHERE id = ?', (form_id,))
            conn.commit()

        logger.info(f"表单提交: {form_id} (用户: {username})")
        return {'success': True, 'submission_id': submission_id, 'message': '表单提交成功'}

    def get_form_submission(self, submission_id: str) -> Dict[str, Any]:
        """获取表单提交详情"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM form_submissions WHERE id = ?', (submission_id,))
            row = cursor.fetchone()

            if not row:
                return {'success': False, 'error': '表单提交不存在'}

            submission = dict(row)
            submission['data'] = json.loads(submission.get('data', '{}'))

            return {'success': True, 'data': submission}

    def list_form_submissions(self, form_id: str = None, user_id: str = None, 
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取表单提交列表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = 'SELECT * FROM form_submissions'
            params = []

            conditions = []
            if form_id:
                conditions.append('form_id = ?')
                params.append(form_id)
            if user_id:
                conditions.append('user_id = ?')
                params.append(user_id)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY submitted_at DESC LIMIT ? OFFSET ?'
            params.extend([page_size, (page - 1) * page_size])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            count_query = 'SELECT COUNT(*) FROM form_submissions'
            if conditions:
                count_query += ' WHERE ' + ' AND '.join(conditions)
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]

            submissions = []
            for row in rows:
                submission = dict(row)
                submission['data'] = json.loads(submission.get('data', '{}'))
                submissions.append(submission)

            return {'success': True, 'data': submissions, 'total': total, 'page': page, 'page_size': page_size}

    def delete_form_submission(self, submission_id: str) -> Dict[str, Any]:
        """删除表单提交"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM form_submissions WHERE id = ?', (submission_id,))
            conn.commit()

        return {'success': True, 'message': '表单提交删除成功'}

    def get_form_stats(self, form_id: str) -> Dict[str, Any]:
        """获取表单统计信息"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT submit_count FROM form_templates WHERE id = ?', (form_id,))
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': '表单不存在'}

            submit_count = row[0]

            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM form_submissions WHERE form_id = ?
            ''', (form_id,))
            user_count = cursor.fetchone()[0]

            cursor.execute('''
                SELECT strftime('%Y-%m-%d', submitted_at) as date, COUNT(*) as count
                FROM form_submissions WHERE form_id = ?
                GROUP BY date ORDER BY date DESC LIMIT 7
            ''', (form_id,))
            daily_stats = []
            for r in cursor.fetchall():
                daily_stats.append({'date': r[0], 'count': r[1]})

        return {
            'success': True,
            'data': {
                'submit_count': submit_count,
                'user_count': user_count,
                'daily_stats': daily_stats
            }
        }

    def get_field_types(self) -> Dict[str, Any]:
        """获取支持的字段类型"""
        return {'success': True, 'data': self.FIELD_TYPES}

    def get_form_statuses(self) -> Dict[str, Any]:
        """获取表单状态列表"""
        return {'success': True, 'data': self.FORM_STATUS}


form_manager_service = FormManagerService()