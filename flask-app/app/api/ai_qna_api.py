#!/usr/bin/env python3
import json
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin
from app.ai.ai_intelligent_qna import ai_intelligent_qna

ai_qna_api = Blueprint('ai_qna_api', __name__)

@ai_qna_api.route('/api/ai/qna/answer', methods=['POST'])
@require_login
def answer_question():
    data = request.get_json() or {}
    question = data.get('question')
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    
    if not question:
        return jsonify({'success': False, 'error': '问题不能为空'}), 400
    
    result = ai_intelligent_qna.answer_question(question, session_id, user_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/session', methods=['POST'])
@require_login
def create_session():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    subject = data.get('subject')
    
    result = ai_intelligent_qna.create_session(user_id, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/session/<session_id>', methods=['PUT'])
@require_login
def end_session(session_id):
    result = ai_intelligent_qna.end_session(session_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/session/<session_id>/history', methods=['GET'])
@require_login
def get_session_history(session_id):
    history = ai_intelligent_qna.get_session_history(session_id)
    return jsonify({'success': True, 'data': history})

@ai_qna_api.route('/api/ai/qna/qa', methods=['POST'])
@require_admin
def add_qa_pair():
    data = request.get_json() or {}
    question = data.get('question')
    answer = data.get('answer')
    question_type = data.get('question_type', 'factual')
    answer_source = data.get('answer_source', 'generated')
    confidence = data.get('confidence', 0.8)
    tags = data.get('tags', [])
    subject = data.get('subject')
    category = data.get('category')
    
    if not question or not answer:
        return jsonify({'success': False, 'error': '问题和答案不能为空'}), 400
    
    result = ai_intelligent_qna.add_qa_pair(question, answer, question_type, answer_source, confidence, tags, subject, category)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/qa/search', methods=['GET'])
@require_login
def search_qa_pairs():
    query = request.args.get('query', '')
    subject = request.args.get('subject')
    question_type = request.args.get('question_type')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
    
    results = ai_intelligent_qna.search_qa_pairs(query, subject, question_type, limit)
    return jsonify({'success': True, 'data': results})

@ai_qna_api.route('/api/ai/qna/qa/<qa_id>', methods=['GET'])
@require_login
def get_qa_pair(qa_id):
    qa = ai_intelligent_qna.get_qa_pair(qa_id)
    if qa:
        return jsonify({'success': True, 'data': qa})
    return jsonify({'success': False, 'error': '问答对不存在'}), 404

@ai_qna_api.route('/api/ai/qna/feedback', methods=['POST'])
@require_login
def submit_feedback():
    data = request.get_json() or {}
    conversation_id = data.get('conversation_id')
    user_id = data.get('user_id')
    rating = data.get('rating', 0)
    comment = data.get('comment', '')
    useful = data.get('useful', True)
    
    if not conversation_id or not user_id:
        return jsonify({'success': False, 'error': '对话ID和用户ID不能为空'}), 400
    
    result = ai_intelligent_qna.submit_feedback(conversation_id, user_id, rating, comment, useful)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/topic', methods=['POST'])
@require_admin
def add_topic():
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description', '')
    subject = data.get('subject')
    
    if not name:
        return jsonify({'success': False, 'error': '主题名称不能为空'}), 400
    
    result = ai_intelligent_qna.add_topic(name, description, subject)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@ai_qna_api.route('/api/ai/qna/topics', methods=['GET'])
@require_login
def get_topics():
    subject = request.args.get('subject')
    topics = ai_intelligent_qna.get_topics(subject)
    return jsonify({'success': True, 'data': topics})

@ai_qna_api.route('/api/ai/qna/statistics', methods=['GET'])
@require_admin
def get_qna_statistics():
    stats = ai_intelligent_qna.get_qna_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_qna_api.route('/api/ai/qna/summary', methods=['GET'])
@require_login
def get_qna_summary():
    stats = ai_intelligent_qna.get_qna_statistics()
    return jsonify({'success': True, 'data': stats})

@ai_qna_api.route('/api/ai/qna/sessions', methods=['GET'])
@require_login
def list_sessions():
    user_id = request.args.get('user_id')
    sessions = ai_intelligent_qna.list_sessions(user_id)
    return jsonify({'success': True, 'data': sessions})

@ai_qna_api.route('/api/ai/qna/hot', methods=['GET'])
@require_login
def get_hot_qa():
    limit = int(request.args.get('limit', 10))
    hot_qa = ai_intelligent_qna.get_hot_qa_pairs(limit)
    return jsonify({'success': True, 'data': hot_qa})

@ai_qna_api.route('/api/ai/qna/database', methods=['GET'])
@require_login
def get_qa_database():
    limit = int(request.args.get('limit', 20))
    qa_list = ai_intelligent_qna.list_qa_pairs(limit)
    return jsonify({'success': True, 'data': qa_list})

@ai_qna_api.route('/api/ai/qna/feedback/summary', methods=['GET'])
@require_admin
def get_feedback_summary():
    stats = ai_intelligent_qna.get_feedback_statistics()
    return jsonify({'success': True, 'data': stats})