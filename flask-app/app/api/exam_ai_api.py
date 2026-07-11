# -*- coding: utf-8 -*-
"""
智能考试助手AI API路由
提供AI对话、学习建议、性能分析等接口
"""

from flask import Blueprint, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

exam_ai_api = Blueprint('exam_ai_api', __name__)


def get_exam_ai_assistant():
    """获取智能考试助手实例"""
    try:
        from app.services.exam_ai_assistant import ExamAIAssistant
        return ExamAIAssistant()
    except Exception as e:
        logger.error(f"获取智能考试助手失败: {str(e)}")
        return None


@exam_ai_api.route('/api/exam-ai/chat', methods=['POST'])
def ai_chat():
    """AI对话接口"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        data = request.get_json() or {}
        message = data.get('message', '')
        session_id = data.get('session_id')
        session_type = data.get('type', 'general')

        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        if not session_id:
            session_id = ai_assistant.create_session(user_id, session_type)

        ai_assistant.add_message(session_id, user_id, 'user', message)

        reply = f"我理解您的问题：{message}。这是一个很好的问题，让我为您分析一下..."

        ai_assistant.add_message(session_id, user_id, 'assistant', reply, len(reply))

        return jsonify({
            'success': True,
            'session_id': session_id,
            'reply': reply,
            'message': 'AI回复成功'
        })

    except Exception as e:
        logger.error(f"AI对话失败: {str(e)}")
        return jsonify({'success': False, 'error': f'AI对话失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/suggestions', methods=['GET'])
def get_suggestions():
    """获取学习建议"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        exam_id = request.args.get('exam_id', type=int)

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        suggestions = ai_assistant.generate_study_suggestions(user_id, exam_id)

        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })

    except Exception as e:
        logger.error(f"获取学习建议失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取学习建议失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/analysis', methods=['GET'])
def get_analysis():
    """获取学习表现分析"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        exam_id = request.args.get('exam_id', type=int)

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        analysis = ai_assistant.analyze_performance(user_id, exam_id)

        return jsonify({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"获取学习分析失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取学习分析失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/recommend', methods=['GET'])
def get_recommendations():
    """获取智能题目推荐"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        count = request.args.get('count', 5, type=int)
        count = min(max(count, 1), 20)

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        recommendations = ai_assistant.smart_question_recommendation(user_id, count)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        logger.error(f"获取题目推荐失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取题目推荐失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/history', methods=['GET'])
def get_history():
    """获取对话历史"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        session_id = request.args.get('session_id', type=int)
        limit = request.args.get('limit', 50, type=int)

        if not session_id:
            return jsonify({'success': False, 'error': '会话ID不能为空'}), 400

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        history = ai_assistant.get_conversation_history(session_id, limit)

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })

    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取对话历史失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/stats', methods=['GET'])
def get_stats():
    """获取AI使用统计"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        stats = ai_assistant.get_user_stats(user_id)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"获取AI统计失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取AI统计失败: {str(e)}'}), 500


@exam_ai_api.route('/api/exam-ai/session/create', methods=['POST'])
def create_session():
    """创建AI会话"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        data = request.get_json() or {}
        session_type = data.get('type', 'general')
        context = data.get('context')

        ai_assistant = get_exam_ai_assistant()
        if not ai_assistant:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        session_id = ai_assistant.create_session(user_id, session_type, context)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '会话创建成功'
        })

    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        return jsonify({'success': False, 'error': f'创建会话失败: {str(e)}'}), 500
