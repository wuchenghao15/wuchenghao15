#!/usr/bin/env python3
"""
AI错题本智能分析API
提供错题分析、模式识别、改进建议等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_wrong_book_analysis import ai_wrong_book_analyzer

ai_wrong_book_api = Bluelogger.info('ai_wrong_book_api', __name__)

@ai_wrong_book_api.route('/api/ai/wrong-book/analyze', methods=['POST'])
@require_login
def analyze_wrong_book():
    """分析错题本"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_wrong_book_analyzer.analyze_wrong_book(user_id, subject)
    return jsonify({'success': True, 'data': result})

@ai_wrong_book_api.route('/api/ai/wrong-book/analysis/<analysis_id>', methods=['GET'])
@require_login
def get_analysis(analysis_id):
    """获取分析记录"""
    result = ai_wrong_book_analyzer.get_analysis_record(analysis_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 404

@ai_wrong_book_api.route('/api/ai/wrong-book/history', methods=['GET'])
@require_login
def get_analysis_history():
    """获取分析历史"""
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_wrong_book_analyzer.get_user_analysis_history(user_id, limit)
    return jsonify({'success': True, 'data': result})

@ai_wrong_book_api.route('/api/ai/wrong-book/patterns', methods=['GET'])
@require_login
def get_patterns():
    """获取错题模式"""
    user_id = request.args.get('user_id')
    subject = request.args.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_wrong_book_analyzer.get_wrong_patterns(user_id, subject)
    return jsonify({'success': True, 'data': result})