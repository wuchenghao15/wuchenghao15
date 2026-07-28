#!/usr/bin/env python3
"""
AI智能答疑API
提供智能问答、对话管理、FAQ查询等功能的REST API接口
"""

from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_intelligent_qna import ai_intelligent_qna

ai_qna_api = Bluelogger.info('ai_intelligent_qna_api', __name__)

@ai_qna_api.route('/api/ai/qna/ask', methods=['POST'])
@require_login
def ask_question():
    """提问"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    question = data.get('question')
    subject = data.get('subject')
    
    if not user_id or not question:
        return jsonify({'success': False, 'error': '用户ID和问题不能为空'}), 400
    
    result = ai_intelligent_qna.ask_question(user_id, question, subject)
    return jsonify({'success': True, 'data': result})

@ai_qna_api.route('/api/ai/qna/conversation', methods=['POST'])
@require_login
def create_conversation():
    """创建对话"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    
    if not user_id:
        return jsonify({'success': False, 'error': '用户ID不能为空'}), 400
    
    result = ai_intelligent_qna.create_conversation(user_id, subject)
    return jsonify({'success': True, 'data': result})

@ai_qna_api.route('/api/ai/qna/conversation/<conversation_id>', methods=['POST'])
@require_login
def send_message(conversation_id):
    """发送消息"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    message = data.get('message')
    subject = data.get('subject')
    
    if not user_id or not message:
        return jsonify({'success': False, 'error': '用户ID和消息不能为空'}), 400
    
    result = ai_intelligent_qna.send_message(conversation_id, user_id, message, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 404

@ai_qna_api.route('/api/ai/qna/conversation/<conversation_id>', methods=['GET'])
@require_login
def get_conversation(conversation_id):
    """获取对话"""
    result = ai_intelligent_qna.get_conversation(conversation_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify(result), 404

@ai_qna_api.route('/api/ai/qna/faq', methods=['GET'])
@require_login
def get_faq():
    """获取FAQ"""
    subject = request.args.get('subject')
    
    result = ai_intelligent_qna.get_faq(subject)
    return jsonify({'success': True, 'data': result})