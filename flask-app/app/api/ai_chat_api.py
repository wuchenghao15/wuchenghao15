# -*- coding: utf-8 -*-
"""
本地AI对话API路由
提供完整的AI对话接口
"""

from flask import Blueprint, request, jsonify, session, render_template
import logging
import os

logger = logging.getLogger(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ai_chat_bp = Blueprint('ai_chat', __name__, 
                       template_folder=os.path.join(APP_ROOT, '../templates/ai_chat'))


def get_ai_chat_service():
    """获取AI对话服务"""
    try:
        from app.services.local_ai_chat_service import LocalAIChatService
        return LocalAIChatService()
    except Exception as e:
        logger.error(f"获取AI对话服务失败: {str(e)}")
        return None


def get_current_user():
    """获取当前用户ID"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return user_id


@ai_chat_bp.route('/ai-chat')
def ai_chat_page():
    """AI对话页面"""
    if not get_current_user():
        return render_template('error.html',
                               error_code=403,
                               error_title='请先登录',
                               error_message='使用AI对话功能需要先登录',
                               error_suggestion='请登录后再访问此页面'), 403
    return render_template('chat.html')


@ai_chat_bp.route('/api/ai-chat/personalities', methods=['GET'])
def get_personalities():
    """获取AI人格列表"""
    if not get_current_user():
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        personalities = service.get_personalities()
        return jsonify({
            'success': True,
            'personalities': personalities,
            'count': len(personalities)
        })
    except Exception as e:
        logger.error(f"获取人格列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations', methods=['GET'])
def get_conversations():
    """获取对话列表"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        limit = request.args.get('limit', 50, type=int)
        conversations = service.get_conversations(user_id, limit)
        return jsonify({
            'success': True,
            'conversations': conversations,
            'count': len(conversations)
        })
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations', methods=['POST'])
def create_conversation():
    """创建新对话"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        title = data.get('title')
        personality_id = data.get('personality_id')

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        conversation_id = service.create_conversation(user_id, title, personality_id)
        conversation = service.get_conversation(conversation_id, user_id)

        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'conversation': conversation,
            'message': '对话创建成功'
        })
    except Exception as e:
        logger.error(f"创建对话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """获取对话详情"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        conversation = service.get_conversation(conversation_id, user_id)
        if not conversation:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        return jsonify({
            'success': True,
            'conversation': conversation
        })
    except Exception as e:
        logger.error(f"获取对话详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        success = service.delete_conversation(conversation_id, user_id)
        if not success:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        return jsonify({
            'success': True,
            'message': '对话已删除'
        })
    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations/<int:conversation_id>/rename', methods=['POST'])
def rename_conversation(conversation_id):
    """重命名对话"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        title = data.get('title', '新对话')

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        success = service.rename_conversation(conversation_id, user_id, title)
        if not success:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        return jsonify({
            'success': True,
            'message': '对话已重命名'
        })
    except Exception as e:
        logger.error(f"重命名对话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    """获取对话消息"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        limit = request.args.get('limit', 50, type=int)
        messages = service.get_messages(conversation_id, limit)

        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    except Exception as e:
        logger.error(f"获取消息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/conversations/<int:conversation_id>/send', methods=['POST'])
def send_message(conversation_id):
    """发送消息"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        content = data.get('message', '')
        provider = data.get('provider')
        model = data.get('model')

        if not content.strip():
            return jsonify({'success': False, 'error': '消息内容不能为空'}), 400

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        reply = service.send_message(
            conversation_id, user_id, content,
            provider=provider, model=model
        )

        return jsonify({
            'success': True,
            'reply': reply
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/send', methods=['POST'])
def send_message_new():
    """发送消息（自动创建新对话）"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        content = data.get('message', '')
        personality_id = data.get('personality_id')
        provider = data.get('provider')
        model = data.get('model')

        if not content.strip():
            return jsonify({'success': False, 'error': '消息内容不能为空'}), 400

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        conversation_id = service.create_conversation(user_id, None, personality_id)
        reply = service.send_message(
            conversation_id, user_id, content,
            provider=provider, model=model
        )

        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'reply': reply
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/settings', methods=['GET'])
def get_settings():
    """获取用户设置"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        settings = service.get_user_settings(user_id)
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        logger.error(f"获取设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/settings', methods=['POST'])
def update_settings():
    """更新用户设置"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        settings = service.update_user_settings(user_id, data)
        return jsonify({
            'success': True,
            'settings': settings,
            'message': '设置已更新'
        })
    except Exception as e:
        logger.error(f"更新设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/models', methods=['GET'])
def get_models():
    """获取可用模型"""
    if not get_current_user():
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        provider = request.args.get('provider')

        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        models = service.get_available_models(provider)
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_chat_bp.route('/api/ai-chat/stats', methods=['GET'])
def get_stats():
    """获取AI对话统计"""
    user_id = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_ai_chat_service()
        if not service:
            return jsonify({'success': False, 'error': 'AI服务不可用'}), 500

        stats = service.get_stats(user_id)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
