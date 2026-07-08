# -*- coding: utf-8 -*-
"""
AI智能答疑API
提供学生在线提问、AI解答、会话管理等接口
"""

from flask import Blueprint, request, jsonify, session
from app.services.ai_tutor_service import ai_tutor_service
import logging

logger = logging.getLogger(__name__)

ai_tutor_api = Blueprint('ai_tutor_api', __name__)


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        user_id = session.get('admin_user_id')
    return user_id


@ai_tutor_api.route('/api/ai/tutor/ask', methods=['POST'])
def ask_question():
    """
    AI答疑 - 学生提问
    
    Request Body:
        question: 问题内容
        subject: 科目（可选）
        question_type: 问题类型（可选）
        session_id: 会话ID（可选）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        question = data.get('question', '').strip()
        subject = data.get('subject')
        question_type = data.get('question_type', 'general')
        session_id = data.get('session_id')
        
        if not question:
            return jsonify({'success': False, 'error': '问题内容不能为空'}), 400
        
        result = ai_tutor_service.ask_question(
            user_id=user_id,
            question=question,
            subject=subject,
            question_type=question_type,
            session_id=session_id
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"AI答疑失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_tutor_api.route('/api/ai/tutor/sessions', methods=['GET'])
def get_sessions():
    """
    获取用户的答疑会话列表
    
    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        result = ai_tutor_service.get_user_sessions(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_tutor_api.route('/api/ai/tutor/session/<session_id>', methods=['GET'])
def get_session_messages(session_id):
    """
    获取会话的消息历史
    
    Path Parameters:
        session_id: 会话ID
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        result = ai_tutor_service.get_session_messages(
            user_id=user_id,
            session_id=session_id,
            page=page,
            page_size=page_size
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_tutor_api.route('/api/ai/tutor/feedback', methods=['POST'])
def submit_feedback():
    """
    提交答疑反馈
    
    Request Body:
        question_id: 问题ID
        is_helpful: 是否有帮助
        feedback: 反馈内容（可选）
    """
    try:
        user_id = get_current_user()
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        question_id = data.get('question_id')
        is_helpful = data.get('is_helpful', False)
        feedback = data.get('feedback', '')
        
        if not question_id:
            return jsonify({'success': False, 'error': '问题ID不能为空'}), 400
        
        result = ai_tutor_service.submit_feedback(
            user_id=user_id,
            question_id=question_id,
            is_helpful=is_helpful,
            feedback=feedback
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_tutor_api.route('/api/ai/tutor/statistics', methods=['GET'])
def get_statistics():
    """
    获取答疑统计数据
    """
    try:
        user_id = get_current_user()
        
        result = ai_tutor_service.get_answer_statistics(user_id=user_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_tutor_api.route('/api/ai/tutor/knowledge/search', methods=['GET'])
def search_knowledge():
    """
    搜索知识库
    
    Query Parameters:
        keyword: 关键词
        subject: 科目（可选）
        limit: 返回数量限制（默认20）
    """
    try:
        keyword = request.args.get('keyword', '')
        subject = request.args.get('subject')
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
        
        result = ai_tutor_service.search_knowledge_base(
            keyword=keyword,
            subject=subject,
            limit=limit
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"搜索知识库失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500