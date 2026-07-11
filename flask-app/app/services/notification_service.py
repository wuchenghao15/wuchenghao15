"""消息通知服务 - MTSCOS AI项目"""

from typing import Optional
from app.models.notification import Notification, NotificationType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """通知服务"""
    
    @staticmethod
    def send_notification(
        user_id: int,
        title: str,
        content: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: int = 0,
        action_url: str = None
    ):
        """发送通知"""
        logger.info(f"发送通知: user_id={user_id}, title={title}")
        return Notification.create(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url
        )
    
    @staticmethod
    def send_system_notification(user_id: int, title: str, content: str):
        """发送系统通知"""
        return NotificationService.send_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.SYSTEM,
            priority=10
        )
    
    @staticmethod
    def send_exam_notification(user_id: int, title: str, content: str, action_url: str = None):
        """发送考试通知"""
        return NotificationService.send_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.EXAM,
            priority=20,
            action_url=action_url
        )
    
    @staticmethod
    def send_learning_notification(user_id: int, title: str, content: str, action_url: str = None):
        """发送学习通知"""
        return NotificationService.send_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.LEARNING,
            priority=15,
            action_url=action_url
        )
    
    @staticmethod
    def send_alert(user_id: int, title: str, content: str):
        """发送告警通知"""
        return NotificationService.send_notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=NotificationType.ALERT,
            priority=30
        )
    
    @staticmethod
    def get_user_notifications(user_id: int, status: str = None, limit: int = 20):
        """获取用户通知"""
        logger.info(f"获取用户通知: user_id={user_id}")
        notifications = Notification.get_by_user(user_id, status, limit)
        return [n.to_dict() for n in notifications]
    
    @staticmethod
    def mark_as_read(notification_id: int):
        """标记为已读"""
        logger.info(f"标记通知已读: notification_id={notification_id}")
        notification = Notification.mark_as_read(notification_id)
        return notification.to_dict() if notification else None
    
    @staticmethod
    def mark_all_read(user_id: int):
        """标记全部已读"""
        logger.info(f"标记全部通知已读: user_id={user_id}")
        Notification.mark_all_read(user_id)
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """获取未读数量"""
        return Notification.get_unread_count(user_id)