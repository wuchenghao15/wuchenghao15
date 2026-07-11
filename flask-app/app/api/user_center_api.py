# -*- coding: utf-8 -*-
"""
用户中心API
提供个人资料、通知消息、设置等用户相关API
"""

from flask import Blueprint, request, jsonify, session, render_template
import logging
import os

logger = logging.getLogger(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

user_center_bp = Blueprint('user_center', __name__,
                            template_folder=os.path.join(APP_ROOT, '../templates'))


def get_current_user():
    """获取当前用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None, None
    username = session.get('username', '')
    role = session.get('role', '')
    return user_id, {'username': username, 'role': role}


def get_profile_service():
    """获取用户资料服务"""
    try:
        from app.services.user_profile_service import UserProfileService
        return UserProfileService()
    except Exception as e:
        logger.error(f"获取用户资料服务失败: {str(e)}")
        return None


def get_notification_service():
    """获取通知服务"""
    try:
        from app.services.notification_service import NotificationService
        return NotificationService()
    except Exception as e:
        logger.error(f"获取通知服务失败: {str(e)}")
        return None


# ==================== 页面路由 ====================

@user_center_bp.route('/profile')
def profile_page():
    """个人资料页面"""
    user_id, user_info = get_current_user()
    if not user_id:
        return render_template('error.html',
                               error_code=403,
                               error_title='请先登录',
                               error_message='访问个人中心需要先登录',
                               error_suggestion='请登录后再访问此页面'), 403

    try:
        service = get_profile_service()
        profile = service.get_profile(user_id) if service else None
        return render_template('profile.html', user=profile or {'username': user_info.get('username', '')})
    except Exception:
        return render_template('profile.html', user={'username': user_info.get('username', '')})


@user_center_bp.route('/notifications')
def notifications_page():
    """通知中心页面"""
    user_id, user_info = get_current_user()
    if not user_id:
        return render_template('error.html',
                               error_code=403,
                               error_title='请先登录',
                               error_message='访问通知中心需要先登录',
                               error_suggestion='请登录后再访问此页面'), 403
    return render_template('notifications.html')


# ==================== 用户资料API ====================

@user_center_bp.route('/api/user/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        profile = service.get_profile(user_id)
        if not profile:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/profile', methods=['POST'])
def update_profile():
    """更新用户资料"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}

        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        profile = service.update_profile(user_id, data)
        return jsonify({
            'success': True,
            'profile': profile,
            'message': '资料更新成功'
        })
    except Exception as e:
        logger.error(f"更新用户资料失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/password', methods=['POST'])
def change_password():
    """修改密码"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password or not new_password:
            return jsonify({'success': False, 'error': '旧密码和新密码不能为空'}), 400

        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        result = service.change_password(user_id, old_password, new_password)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/settings', methods=['GET'])
def get_user_settings():
    """获取用户设置"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        profile = service.get_profile(user_id)
        settings = {
            'language': profile.get('language', 'zh'),
            'theme': profile.get('theme', 'light'),
            'notification_enabled': profile.get('notification_enabled', 1),
            'email_notification': profile.get('email_notification', 1)
        }
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        logger.error(f"获取用户设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/settings', methods=['POST'])
def update_user_settings():
    """更新用户设置"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}

        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        result = service.update_settings(user_id, data)
        return jsonify({
            'success': True,
            'settings': result.get('settings', {}),
            'message': '设置更新成功'
        })
    except Exception as e:
        logger.error(f"更新用户设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/login-history', methods=['GET'])
def get_login_history():
    """获取登录历史"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        limit = request.args.get('limit', 20, type=int)

        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        history = service.get_login_history(user_id, limit)
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取登录历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/activity', methods=['GET'])
def get_activity_logs():
    """获取活动日志"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        limit = request.args.get('limit', 50, type=int)
        activity_type = request.args.get('type')

        service = get_profile_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        logs = service.get_activity_logs(user_id, limit, activity_type)
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        logger.error(f"获取活动日志失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """获取用户统计"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        profile_service = get_profile_service()
        notification_service = get_notification_service()

        stats = {}
        if profile_service:
            stats.update(profile_service.get_stats(user_id))
        if notification_service:
            stats['notifications'] = notification_service.get_stats(user_id)

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 通知API ====================

@user_center_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    """获取通知列表"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        limit = request.args.get('limit', 50, type=int)
        is_read = request.args.get('read')
        notification_type = request.args.get('type')
        category = request.args.get('category')

        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        read_flag = None
        if is_read is not None:
            read_flag = is_read.lower() == 'true'

        notifications = service.get_notifications(
            user_id, limit, read_flag, notification_type, category
        )
        unread_count = service.get_unread_count(user_id)

        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count,
            'count': len(notifications)
        })
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """获取未读通知数量"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        count = service.get_unread_count(user_id)
        msg_count = service.get_unread_message_count(user_id)

        return jsonify({
            'success': True,
            'notification_count': count,
            'message_count': msg_count,
            'total': count + msg_count
        })
    except Exception as e:
        logger.error(f"获取未读数量失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """标记通知为已读"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        success = service.mark_as_read(notification_id, user_id)
        if not success:
            return jsonify({'success': False, 'error': '通知不存在'}), 404

        return jsonify({
            'success': True,
            'message': '已标记为已读'
        })
    except Exception as e:
        logger.error(f"标记通知已读失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notifications/read-all', methods=['POST'])
def mark_all_read():
    """标记所有通知为已读"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        count = service.mark_all_as_read(user_id)
        return jsonify({
            'success': True,
            'marked_count': count,
            'message': f'已标记 {count} 条通知为已读'
        })
    except Exception as e:
        logger.error(f"标记全部已读失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """删除通知"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        success = service.delete_notification(notification_id, user_id)
        if not success:
            return jsonify({'success': False, 'error': '通知不存在'}), 404

        return jsonify({
            'success': True,
            'message': '通知已删除'
        })
    except Exception as e:
        logger.error(f"删除通知失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    """清空所有通知"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        count = service.clear_all(user_id)
        return jsonify({
            'success': True,
            'cleared_count': count,
            'message': f'已清空 {count} 条通知'
        })
    except Exception as e:
        logger.error(f"清空通知失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notification-settings', methods=['GET'])
def get_notification_settings():
    """获取通知设置"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        settings = service.get_settings(user_id)
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        logger.error(f"获取通知设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/notification-settings', methods=['POST'])
def update_notification_settings():
    """更新通知设置"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}

        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        settings = service.update_settings(user_id, data)
        return jsonify({
            'success': True,
            'settings': settings,
            'message': '通知设置已更新'
        })
    except Exception as e:
        logger.error(f"更新通知设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 私信API ====================

@user_center_bp.route('/api/messages', methods=['GET'])
def get_messages():
    """获取消息列表"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        folder = request.args.get('folder', 'inbox')
        limit = request.args.get('limit', 50, type=int)

        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        messages = service.get_messages(user_id, folder, limit)
        return jsonify({
            'success': True,
            'messages': messages,
            'folder': folder,
            'count': len(messages)
        })
    except Exception as e:
        logger.error(f"获取消息列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/messages/<int:message_id>', methods=['GET'])
def get_message_detail(message_id):
    """获取消息详情"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        message = service.get_message_detail(message_id, user_id)
        if not message:
            return jsonify({'success': False, 'error': '消息不存在'}), 404

        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        logger.error(f"获取消息详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_center_bp.route('/api/messages/send', methods=['POST'])
def send_message():
    """发送私信"""
    user_id, user_info = get_current_user()
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401

    try:
        data = request.get_json() or {}
        receiver_id = data.get('receiver_id')
        title = data.get('title', '')
        content = data.get('content', '')
        parent_id = data.get('parent_id')

        if not receiver_id:
            return jsonify({'success': False, 'error': '接收者ID不能为空'}), 400
        if not content:
            return jsonify({'success': False, 'error': '消息内容不能为空'}), 400

        service = get_notification_service()
        if not service:
            return jsonify({'success': False, 'error': '服务不可用'}), 500

        msg_id = service.send_message(user_id, receiver_id, title, content, parent_id)
        return jsonify({
            'success': True,
            'message_id': msg_id,
            'message': '消息发送成功'
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
