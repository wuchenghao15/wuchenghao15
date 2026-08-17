#!/usr/bin/env python3
"""
AI作业辅导API接口
提供作业辅导相关的REST API服务
"""

from flask import Blueprint, request, jsonify, session
from app.ai.ai_homework_tutoring import ai_homework_tutoring
import json

ai_tutoring_api = Bluelogger.info('ai_tutoring_api', __name__, url_prefix='/api/ai/tutoring')

@ai_tutoring_api.route('/start', methods=['POST'])
def start_session():
    """开始辅导会话"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question_id = data.get('question_id', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_homework_tutoring.start_tutoring_session(user_id, question_id, subject, topic)
    return jsonify(result)

@ai_tutoring_api.route('/hint', methods=['POST'])
def get_hint():
    """获取解题提示"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question = data.get('question', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    level = data.get('level', 1)
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和题目不能为空'}), 400
    
    result = ai_homework_tutoring.get_hint(user_id, question, subject, topic, level)
    return jsonify(result)

@ai_tutoring_api.route('/guide', methods=['POST'])
def get_guide():
    """获取解题引导"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question = data.get('question', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和题目不能为空'}), 400
    
    result = ai_homework_tutoring.get_guide(user_id, question, subject, topic)
    return jsonify(result)

@ai_tutoring_api.route('/explanation', methods=['POST'])
def get_explanation():
    """获取详细解答"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question = data.get('question', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    user_answer = data.get('user_answer', '')
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和题目不能为空'}), 400
    
    result = ai_homework_tutoring.get_explanation(user_id, question, subject, topic, user_answer)
    return jsonify(result)

@ai_tutoring_api.route('/practice', methods=['POST'])
def get_practice():
    """获取练习题目"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question = data.get('question', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    count = data.get('count', 3)
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和题目不能为空'}), 400
    
    result = ai_homework_tutoring.get_practice(user_id, question, subject, topic, count)
    return jsonify(result)

@ai_tutoring_api.route('/ask', methods=['POST'])
def ask_question():
    """提出问题"""
    data = request.get_json()
    user_id = data.get('user_id', '')
    question = data.get('question', '')
    subject = data.get('subject', '数学')
    topic = data.get('topic', '')
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和问题不能为空'}), 400
    
    result = ai_homework_tutoring.ask_question(user_id, question, subject, topic)
    return jsonify(result)

@ai_tutoring_api.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话信息"""
    result = ai_homework_tutoring.get_session(session_id)
    
    if result:
        return jsonify({'success': True, 'data': result})
    else:
        return jsonify({'success': False, 'error': '会话不存在'}), 404

@ai_tutoring_api.route('/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """结束会话"""
    success = ai_homework_tutoring.end_session(session_id)
    
    if success:
        return jsonify({'success': True, 'message': '会话已结束'})
    else:
        return jsonify({'success': False, 'error': '会话不存在或已结束'}), 404

@ai_tutoring_api.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    """获取用户辅导历史"""
    limit = request.args.get('limit', 10, type=int)
    sessions = ai_homework_tutoring.get_user_sessions(user_id, limit)
    
    return jsonify({'success': True, 'data': sessions})