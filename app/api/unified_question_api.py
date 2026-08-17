#!/usr/bin/env python3
"""
MTSCOS Unified Question Bank API - 统一题库管理API
支持所有科目（语文、数学、英语、政治、日语、物理、化学、生物、历史、地理）
支持所有题型（单选、多选、判断、填空、简答、计算、听力、写作、阅读理解等）
支持AI自动延展题库内容
"""

import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin, allow_guest_access
from ai_engines.unified_question_bank import unified_question_bank, SUBJECTS, QUESTION_TYPES, DIFFICULTY_LEVELS, QUESTION_TAGS

unified_question_api = Blueprint('unified_question_api', __name__)


@unified_question_api.route('/api/questions', methods=['GET'])
@allow_guest_access
def get_questions():
    """获取题目列表"""
    filters = {}
    
    if 'subject' in request.args:
        filters['subject'] = request.args['subject']
    if 'type' in request.args:
        filters['question_type'] = request.args['type']
    if 'difficulty' in request.args:
        filters['difficulty'] = request.args['difficulty']
    if 'grade' in request.args:
        filters['grade'] = request.args['grade']
    if 'keyword' in request.args:
        filters['keyword'] = request.args['keyword']
    if 'page' in request.args:
        filters['page'] = int(request.args['page'])
    if 'page_size' in request.args:
        filters['page_size'] = int(request.args['page_size'])
    
    result = unified_question_bank.get_questions(filters)
    return jsonify(result)


@unified_question_api.route('/api/questions/<question_uuid>', methods=['GET'])
@allow_guest_access
def get_question(question_uuid):
    """获取单个题目"""
    result = unified_question_bank.get_question_by_uuid(question_uuid)
    return jsonify(result)


@unified_question_api.route('/api/questions', methods=['POST'])
@require_login
def add_question():
    """添加题目"""
    data = request.get_json() or {}
    
    if not data.get('content') or not data.get('correct_answer'):
        return jsonify({'success': False, 'error': '题目内容和正确答案不能为空'})
    
    result = unified_question_bank.add_question(data)
    return jsonify(result)


@unified_question_api.route('/api/questions/<question_uuid>', methods=['PUT'])
@require_login
def update_question(question_uuid):
    """更新题目"""
    updates = request.get_json() or {}
    result = unified_question_bank.update_question(question_uuid, updates)
    return jsonify(result)


@unified_question_api.route('/api/questions/<question_uuid>', methods=['DELETE'])
@require_admin
def delete_question(question_uuid):
    """删除题目"""
    result = unified_question_bank.delete_question(question_uuid)
    return jsonify(result)


@unified_question_api.route('/api/questions/batch', methods=['POST'])
@require_admin
def batch_import_questions():
    """批量导入题目"""
    data = request.get_json() or {}
    questions = data.get('questions', [])
    
    if not questions:
        return jsonify({'success': False, 'error': '题目列表不能为空'})
    
    result = unified_question_bank.batch_import_questions(questions)
    return jsonify(result)


@unified_question_api.route('/api/questions/ai_extend', methods=['POST'])
@require_login
def ai_extend_question():
    """AI自动延展题目"""
    data = request.get_json() or {}
    source_uuid = data.get('source_uuid')
    count = int(data.get('count', 5))
    
    if not source_uuid:
        return jsonify({'success': False, 'error': '源题目UUID不能为空'})
    
    result = unified_question_bank.ai_extend_question(source_uuid, count=count)
    return jsonify(result)


@unified_question_api.route('/api/questions/stats', methods=['GET'])
@allow_guest_access
def get_statistics():
    """获取题库统计"""
    result = unified_question_bank.get_statistics()
    return jsonify(result)


@unified_question_api.route('/api/questions/sync', methods=['POST'])
@require_admin
def sync_with_external():
    """同步外部题库"""
    data = request.get_json() or {}
    source = data.get('source', 'mock')
    subject = data.get('subject')
    
    result = unified_question_bank.sync_with_external(source, subject)
    return jsonify(result)


@unified_question_api.route('/api/subjects', methods=['GET'])
@allow_guest_access
def get_subjects():
    """获取科目列表"""
    subjects_list = []
    for code, info in SUBJECTS.items():
        subjects_list.append({
            'code': code,
            'name': info['name'],
            'icon': info['icon'],
            'color': info['color']
        })
    return jsonify({'success': True, 'data': subjects_list})


@unified_question_api.route('/api/question_types', methods=['GET'])
@allow_guest_access
def get_question_types():
    """获取题型列表"""
    types_list = []
    for code, info in QUESTION_TYPES.items():
        types_list.append({
            'code': code,
            'name': info['name'],
            'description': info['description']
        })
    return jsonify({'success': True, 'data': types_list})


@unified_question_api.route('/api/difficulty_levels', methods=['GET'])
@allow_guest_access
def get_difficulty_levels():
    """获取难度级别列表"""
    levels_list = []
    for code, info in DIFFICULTY_LEVELS.items():
        levels_list.append({
            'code': code,
            'name': info['name'],
            'description': info['description'],
            'score_weight': info['score_weight']
        })
    return jsonify({'success': True, 'data': levels_list})


@unified_question_api.route('/api/question_tags', methods=['GET'])
@allow_guest_access
def get_question_tags():
    """获取题目标签列表"""
    return jsonify({'success': True, 'data': QUESTION_TAGS})


@unified_question_api.route('/api/questions/generate', methods=['POST'])
@require_login
def generate_questions():
    """批量生成题目"""
    data = request.get_json() or {}
    subject = data.get('subject', 'math')
    count = int(data.get('count', 10))
    difficulty = data.get('difficulty', 'easy')
    question_type = data.get('question_type', 'single_choice')
    
    generated = []
    for i in range(count):
        question_data = unified_question_bank._generate_extended_question(
            {'subject': subject, 'question_type': question_type, 'difficulty': difficulty, 'grade': data.get('grade', '初中')},
            'auto', i
        )
        if question_data:
            result = unified_question_bank.add_question(question_data)
            if result['success']:
                generated.append(result['question_uuid'])
    
    return jsonify({
        'success': True,
        'message': f'成功生成{len(generated)}道题目',
        'generated_count': len(generated),
        'generated_uuids': generated,
        'subject': subject,
        'difficulty': difficulty,
        'question_type': question_type
    })


@unified_question_api.route('/api/questions/filter_options', methods=['GET'])
@allow_guest_access
def get_filter_options():
    """获取筛选选项"""
    return jsonify({
        'success': True,
        'data': {
            'subjects': SUBJECTS,
            'question_types': QUESTION_TYPES,
            'difficulty_levels': DIFFICULTY_LEVELS,
            'tags': QUESTION_TAGS,
            'grades': ['小学', '初中', '高中'],
            'semesters': ['上学期', '下学期']
        }
    })