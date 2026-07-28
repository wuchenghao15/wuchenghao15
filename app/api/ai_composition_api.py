#!/usr/bin/env python3
"""
AI作文批改API
提供作文批改、批改记录查询等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_composition_grader import ai_composition_grader

ai_composition_api = Bluelogger.info('ai_composition_api', __name__)

@ai_composition_api.route('/api/ai/composition/grade', methods=['POST'])
@require_login
def grade_composition():
    """批改作文"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    content = data.get('content')
    title = data.get('title', '')
    subject = data.get('subject', '语文')
    
    if not user_id or not content:
        return jsonify({'success': False, 'error': '用户ID和作文内容不能为空'}), 400
    
    if len(content) < 50:
        return jsonify({'success': False, 'error': '作文内容至少需要50个字符'}), 400
    
    result = ai_composition_grader.grade_composition(user_id, content, title, subject)
    return jsonify({'success': True, 'data': result})

@ai_composition_api.route('/api/ai/composition/grading/<grading_id>', methods=['GET'])
@require_login
def get_grading(grading_id):
    """获取批改记录"""
    result = ai_composition_grader.get_grading_record(grading_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '批改记录不存在'}), 404

@ai_composition_api.route('/api/ai/composition/history', methods=['GET'])
@require_login
def get_grading_history():
    """获取批改历史"""
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_composition_grader.get_user_grading_history(user_id, limit)
    return jsonify({'success': True, 'data': result})

@ai_composition_api.route('/api/ai/composition/criteria', methods=['GET'])
@require_login
def get_criteria():
    """获取评分标准"""
    return jsonify({'success': True, 'data': ai_composition_grader.CRITERIA})