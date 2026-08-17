#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_writing_assistant import ai_writing_assistant

ai_writing_api = Bluelogger.info('ai_writing_api', __name__)

@ai_writing_api.route('/api/ai/writing/generate', methods=['POST'])
@require_login
def generate_content():
    data = request.get_json() or {}
    title = data.get('title')
    writing_type = data.get('writing_type', 'essay')
    target_audience = data.get('target_audience', 'general')
    tone = data.get('tone', 'formal')
    word_count = data.get('word_count', 500)
    keywords = data.get('keywords')
    
    if not title:
        return jsonify({'success': False, 'error': '标题不能为空'}), 400
    
    result = ai_writing_assistant.generate_content(title, writing_type, target_audience, tone, word_count, keywords)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/rewrite', methods=['POST'])
@require_login
def rewrite_content():
    data = request.get_json() or {}
    content = data.get('content')
    target_tone = data.get('target_tone', 'formal')
    improvements = data.get('improvements', ['grammar', 'vocabulary', 'style', 'clarity'])
    
    if not content:
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    
    result = ai_writing_assistant.rewrite_content(content, target_tone, improvements)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/summarize', methods=['POST'])
@require_login
def summarize_content():
    data = request.get_json() or {}
    content = data.get('content')
    max_length = data.get('max_length', 200)
    
    if not content:
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    
    result = ai_writing_assistant.summarize_content(content, max_length)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/grammar', methods=['POST'])
@require_login
def check_grammar():
    data = request.get_json() or {}
    content = data.get('content')
    
    if not content:
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    
    result = ai_writing_assistant.check_grammar(content)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/templates', methods=['GET'])
@require_login
def get_templates():
    writing_type = request.args.get('writing_type')
    result = ai_writing_assistant.get_templates(writing_type)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/task/<task_id>', methods=['GET'])
@require_login
def get_task(task_id):
    result = ai_writing_assistant.get_task(task_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/task/<task_id>', methods=['PUT'])
@require_login
def save_task(task_id):
    data = request.get_json() or {}
    content = data.get('content')
    status = data.get('status', 'draft')
    
    if not content:
        return jsonify({'success': False, 'error': '内容不能为空'}), 400
    
    result = ai_writing_assistant.save_task(task_id, content, status)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/tasks', methods=['GET'])
@require_login
def list_tasks():
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))
    
    result = ai_writing_assistant.list_tasks(user_id, limit)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_writing_api.route('/api/ai/writing/types', methods=['GET'])
@require_login
def get_writing_types():
    return jsonify({
        'success': True,
        'data': {
            'writing_types': ai_writing_assistant.WRITING_TYPES,
            'target_audiences': ai_writing_assistant.TARGET_AUDIENCES,
            'tone_styles': ai_writing_assistant.TONE_STYLES
        }
    })