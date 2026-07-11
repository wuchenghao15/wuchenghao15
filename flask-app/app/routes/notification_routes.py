"""通知API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.notification_service import NotificationService
from app.utils.api_response import APIResponse
from app.utils.permission import require_login, require_admin

notification_api = Blueprint('notification_api', __name__)


@notification_api.route('/api/notifications', methods=['GET'])
@require_login
def get_notifications():
    """获取用户通知列表"""
    user_id = session.get('user_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    
    notifications = NotificationService.get_user_notifications(user_id, status, limit)
    return APIResponse.success(notifications)


@notification_api.route('/api/notifications/unread', methods=['GET'])
@require_login
def get_unread_count():
    """获取未读通知数量"""
    user_id = session.get('user_id')
    count = NotificationService.get_unread_count(user_id)
    return APIResponse.success({'unread_count': count})


@notification_api.route('/api/notifications/<int:notification_id>', methods=['PUT'])
@require_login
def mark_as_read(notification_id):
    """标记通知为已读"""
    result = NotificationService.mark_as_read(notification_id)
    if result:
        return APIResponse.success(result)
    return APIResponse.not_found("通知不存在")


@notification_api.route('/api/notifications/read_all', methods=['PUT'])
@require_login
def mark_all_read():
    """标记全部通知为已读"""
    user_id = session.get('user_id')
    NotificationService.mark_all_read(user_id)
    return APIResponse.success(message="全部标记为已读")


@notification_api.route('/api/notifications', methods=['POST'])
@require_admin
def send_notification():
    """发送通知（管理员权限）"""
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    content = data.get('content')
    notification_type = data.get('type', 'system')
    priority = data.get('priority', 0)
    action_url = data.get('action_url')
    
    if not user_id or not title or not content:
        return APIResponse.validation_error("参数不全")
    
    notification = NotificationService.send_notification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url
    )
    
    return APIResponse.success(notification.to_dict(), message="通知发送成功")