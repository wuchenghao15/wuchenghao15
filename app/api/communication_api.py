#!/usr/bin/env python3
"""
通讯中心 API
=============
提供站内通知、邮件、短信、交流系统的RESTful API接口。
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps

communication_api = Bluelogger.info('communication_api', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        if session.get('role') not in ['admin', 'super_admin']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated


# ==================== 站内通知 ====================

@communication_api.route('/api/communication/notifications', methods=['GET'])
@login_required
def get_notifications():
    from communication_center_service import communication_service
    user_id = session.get('user_id')
    status = request.args.get('status')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    notifs = communication_service.get_notifications(user_id, status, category, limit, offset)
    unread = communication_service.get_unread_count(user_id)
    return jsonify({'success': True, 'data': notifs, 'unread': unread, 'total': len(notifs)})


@communication_api.route('/api/communication/notifications', methods=['POST'])
@admin_required
def send_notification():
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_notification(
        user_id=data.get('user_id'),
        title=data.get('title'),
        content=data.get('content', ''),
        notif_type=data.get('type', 'info'),
        category=data.get('category', 'system'),
        priority=data.get('priority', 'normal'),
        sender_id=session.get('user_id'),
        sender_name=session.get('username', '管理员'),
        action_url=data.get('action_url'),
        action_text=data.get('action_text')
    )
    return jsonify(result)


@communication_api.route('/api/communication/notifications/batch', methods=['POST'])
@admin_required
def send_batch_notifications():
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_batch_notifications(
        user_ids=data.get('user_ids', []),
        title=data.get('title'),
        content=data.get('content', ''),
        notif_type=data.get('type', 'info'),
        category=data.get('category', 'system'),
        priority=data.get('priority', 'normal'),
        sender_id=session.get('user_id'),
        sender_name=session.get('username', '管理员')
    )
    return jsonify(result)


@communication_api.route('/api/communication/notifications/<notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    from communication_center_service import communication_service
    result = communication_service.mark_notification_read(notification_id)
    return jsonify(result)


@communication_api.route('/api/communication/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_read():
    from communication_center_service import communication_service
    user_id = session.get('user_id')
    result = communication_service.mark_all_read(user_id)
    return jsonify(result)


@communication_api.route('/api/communication/notifications/<notification_id>/archive', methods=['PUT'])
@login_required
def archive_notification(notification_id):
    from communication_center_service import communication_service
    result = communication_service.archive_notification(notification_id)
    return jsonify(result)


@communication_api.route('/api/communication/notifications/<notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    from communication_center_service import communication_service
    result = communication_service.delete_notification(notification_id)
    return jsonify(result)


# ==================== 邮件系统 ====================

@communication_api.route('/api/communication/emails', methods=['POST'])
@admin_required
def send_email():
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_email(
        to_address=data.get('to_address'),
        subject=data.get('subject', ''),
        body_text=data.get('body_text', ''),
        body_html=data.get('body_html'),
        template_id=data.get('template_id'),
        variables=data.get('variables'),
        cc_address=data.get('cc_address'),
        priority=data.get('priority', 'normal'),
        created_by=session.get('user_id')
    )
    return jsonify(result)


@communication_api.route('/api/communication/emails/templates', methods=['GET'])
@login_required
def get_email_templates():
    from communication_center_service import communication_service
    category = request.args.get('category')
    templates = communication_service.get_email_templates(category)
    return jsonify({'success': True, 'data': templates})


@communication_api.route('/api/communication/emails/history', methods=['GET'])
@admin_required
def get_email_history():
    from communication_center_service import communication_service
    to_address = request.args.get('to_address')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    history = communication_service.get_email_history(to_address, status, limit)
    return jsonify({'success': True, 'data': history, 'total': len(history)})


# ==================== 短信系统 ====================

@communication_api.route('/api/communication/sms', methods=['POST'])
@admin_required
def send_sms():
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_sms(
        phone_number=data.get('phone_number'),
        content=data.get('content', ''),
        template_id=data.get('template_id'),
        variables=data.get('variables'),
        sms_type=data.get('sms_type', 'notification'),
        priority=data.get('priority', 'normal'),
        created_by=session.get('user_id')
    )
    return jsonify(result)


@communication_api.route('/api/communication/sms/verification-code', methods=['POST'])
def send_verification_code():
    """发送验证码（无需登录）"""
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_verification_code(
        phone_number=data.get('phone_number'),
        purpose=data.get('purpose', 'login')
    )
    return jsonify(result)


@communication_api.route('/api/communication/sms/verify-code', methods=['POST'])
def verify_code():
    """验证验证码（无需登录）"""
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.verify_code(
        phone_number=data.get('phone_number'),
        code=data.get('code'),
        purpose=data.get('purpose', 'login')
    )
    return jsonify(result)


@communication_api.route('/api/communication/sms/history', methods=['GET'])
@admin_required
def get_sms_history():
    from communication_center_service import communication_service
    phone_number = request.args.get('phone_number')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    history = communication_service.get_sms_history(phone_number, status, limit)
    return jsonify({'success': True, 'data': history, 'total': len(history)})


# ==================== 交流系统 ====================

@communication_api.route('/api/communication/chat/conversations', methods=['GET'])
@login_required
def get_conversations():
    from communication_center_service import communication_service
    user_id = session.get('user_id')
    convs = communication_service.get_conversations(user_id)
    return jsonify({'success': True, 'data': convs, 'total': len(convs)})


@communication_api.route('/api/communication/chat/conversations', methods=['POST'])
@login_required
def create_conversation():
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.create_conversation(
        creator_id=session.get('user_id'),
        participant_ids=data.get('participant_ids', []),
        conversation_type=data.get('conversation_type', 'direct'),
        name=data.get('name')
    )
    return jsonify(result)


@communication_api.route('/api/communication/chat/conversations/<conversation_id>/messages', methods=['GET'])
@login_required
def get_messages(conversation_id):
    from communication_center_service import communication_service
    user_id = session.get('user_id')
    limit = int(request.args.get('limit', 50))
    before_id = request.args.get('before_id')
    messages = communication_service.get_messages(conversation_id, user_id, limit, before_id)
    return jsonify({'success': True, 'data': messages, 'total': len(messages)})


@communication_api.route('/api/communication/chat/conversations/<conversation_id>/messages', methods=['POST'])
@login_required
def send_message(conversation_id):
    from communication_center_service import communication_service
    data = request.json
    result = communication_service.send_message(
        conversation_id=conversation_id,
        sender_id=session.get('user_id'),
        content=data.get('content', ''),
        message_type=data.get('message_type', 'text'),
        sender_name=session.get('username'),
        sender_avatar=session.get('avatar'),
        attachment_url=data.get('attachment_url'),
        attachment_name=data.get('attachment_name'),
        reply_to_id=data.get('reply_to_id')
    )
    return jsonify(result)


@communication_api.route('/api/communication/chat/messages/<message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    from communication_center_service import communication_service
    result = communication_service.delete_message(message_id, session.get('user_id'))
    return jsonify(result)


# ==================== 通讯统计 ====================

@communication_api.route('/api/communication/stats', methods=['GET'])
@admin_required
def get_stats():
    from communication_center_service import communication_service
    stats = communication_service.get_stats()
    return jsonify({'success': True, 'data': stats})
