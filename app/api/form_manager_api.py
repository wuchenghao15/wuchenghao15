#!/usr/bin/env python3
"""
表单管理 API
===============
表单模板管理、表单字段管理、表单数据管理的RESTful API。
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

form_manager_api = Bluelogger.info('form_manager_api', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        if session.get('role') not in ['admin', 'super_admin']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated


# ==================== 表单模板管理 ====================

@form_manager_api.route('/api/form/templates', methods=['GET'])
@login_required
def list_form_templates():
    from form_manager_service import form_manager_service
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    result = form_manager_service.list_form_templates(status, page, page_size)
    return jsonify(result)


@form_manager_api.route('/api/form/templates', methods=['POST'])
@admin_required
def create_form_template():
    from form_manager_service import form_manager_service
    data = request.json
    result = form_manager_service.create_form_template(
        name=data.get('name', ''),
        description=data.get('description', ''),
        created_by=session.get('username', ''),
        settings=data.get('settings', {})
    )
    return jsonify(result)


@form_manager_api.route('/api/form/templates/<form_id>', methods=['GET'])
@login_required
def get_form_template(form_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.get_form_template(form_id)
    return jsonify(result)


@form_manager_api.route('/api/form/templates/<form_id>', methods=['PUT'])
@admin_required
def update_form_template(form_id):
    from form_manager_service import form_manager_service
    data = request.json
    result = form_manager_service.update_form_template(form_id, **data)
    return jsonify(result)


@form_manager_api.route('/api/form/templates/<form_id>', methods=['DELETE'])
@admin_required
def delete_form_template(form_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.delete_form_template(form_id)
    return jsonify(result)


# ==================== 表单字段管理 ====================

@form_manager_api.route('/api/form/fields/<form_id>', methods=['GET'])
@login_required
def get_form_fields(form_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.get_form_fields(form_id)
    return jsonify(result)


@form_manager_api.route('/api/form/fields', methods=['POST'])
@admin_required
def add_form_field():
    from form_manager_service import form_manager_service
    data = request.json
    result = form_manager_service.add_form_field(
        form_id=data.get('form_id', ''),
        field_type=data.get('field_type', 'text'),
        label=data.get('label', ''),
        name=data.get('name', ''),
        placeholder=data.get('placeholder', ''),
        required=data.get('required', False),
        options=data.get('options', []),
        default_value=data.get('default_value', ''),
        validation=data.get('validation', {}),
        order=data.get('order', 0)
    )
    return jsonify(result)


@form_manager_api.route('/api/form/fields/<field_id>', methods=['PUT'])
@admin_required
def update_form_field(field_id):
    from form_manager_service import form_manager_service
    data = request.json
    result = form_manager_service.update_form_field(field_id, **data)
    return jsonify(result)


@form_manager_api.route('/api/form/fields/<field_id>', methods=['DELETE'])
@admin_required
def delete_form_field(field_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.delete_form_field(field_id)
    return jsonify(result)


# ==================== 表单提交管理 ====================

@form_manager_api.route('/api/form/submissions', methods=['GET'])
@login_required
def list_form_submissions():
    from form_manager_service import form_manager_service
    form_id = request.args.get('form_id')
    user_id = request.args.get('user_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    result = form_manager_service.list_form_submissions(form_id, user_id, page, page_size)
    return jsonify(result)


@form_manager_api.route('/api/form/submissions', methods=['POST'])
@login_required
def submit_form():
    from form_manager_service import form_manager_service
    data = request.json
    result = form_manager_service.submit_form(
        form_id=data.get('form_id', ''),
        data=data.get('data', {}),
        user_id=session.get('user_id', ''),
        username=session.get('username', '')
    )
    return jsonify(result)


@form_manager_api.route('/api/form/submissions/<submission_id>', methods=['GET'])
@login_required
def get_form_submission(submission_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.get_form_submission(submission_id)
    return jsonify(result)


@form_manager_api.route('/api/form/submissions/<submission_id>', methods=['DELETE'])
@admin_required
def delete_form_submission(submission_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.delete_form_submission(submission_id)
    return jsonify(result)


# ==================== 表单统计 ====================

@form_manager_api.route('/api/form/stats/<form_id>', methods=['GET'])
@login_required
def get_form_stats(form_id):
    from form_manager_service import form_manager_service
    result = form_manager_service.get_form_stats(form_id)
    return jsonify(result)


# ==================== 字典查询 ====================

@form_manager_api.route('/api/form/field-types', methods=['GET'])
@login_required
def get_field_types():
    from form_manager_service import form_manager_service
    result = form_manager_service.get_field_types()
    return jsonify(result)


@form_manager_api.route('/api/form/statuses', methods=['GET'])
@login_required
def get_form_statuses():
    from form_manager_service import form_manager_service
    result = form_manager_service.get_form_statuses()
    return jsonify(result)