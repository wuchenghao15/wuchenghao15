"""消息通知模型 - MTSCOS AI项目"""

from datetime import datetime
from enum import Enum
from app.utils.db import DatabaseManager
from app.utils.logger import get_logger

logger = get_logger(__name__)
db_manager = DatabaseManager()


class NotificationType(Enum):
    """通知类型"""
    SYSTEM = 'system'
    EXAM = 'exam'
    LEARNING = 'learning'
    MESSAGE = 'message'
    ALERT = 'alert'


class NotificationStatus(Enum):
    """通知状态"""
    PENDING = 'pending'
    READ = 'read'
    ARCHIVED = 'archived'


class Notification:
    """通知模型"""
    
    TABLE_NAME = 'notifications'
    
    @classmethod
    def _create_table(cls):
        """创建表（如果不存在）"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    notification_type TEXT DEFAULT 'system',
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 0,
                    action_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            """)
        except Exception as e:
            logger.error(f"创建通知表失败: {str(e)}")
    
    def __init__(self, id=None, user_id=None, title=None, content=None, 
                 notification_type=NotificationType.SYSTEM, status=NotificationStatus.PENDING,
                 priority=0, action_url=None, created_at=None, read_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.notification_type = notification_type
        self.status = status
        self.priority = priority
        self.action_url = action_url
        self.created_at = created_at
        self.read_at = read_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'type': self.notification_type.value if isinstance(self.notification_type, Enum) else self.notification_type,
            'status': self.status.value if isinstance(self.status, Enum) else self.status,
            'priority': self.priority,
            'action_url': self.action_url,
            'created_at': self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at if isinstance(self.read_at, str) else self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def create(cls, user_id: int, title: str, content: str, 
               notification_type: NotificationType = NotificationType.SYSTEM,
               priority: int = 0, action_url: str = None):
        """创建通知"""
        cls._create_table()
        notification_type_value = notification_type.value if isinstance(notification_type, Enum) else notification_type
        
        try:
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} (user_id, title, content, notification_type, priority, action_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, title, content, notification_type_value, priority, action_url))
            
            result = db_manager.fetch_one(f"SELECT last_insert_rowid()")
            notification_id = result[0] if result else None
            
            logger.info(f"创建通知成功: id={notification_id}, user_id={user_id}")
            return cls.get_by_id(notification_id)
        except Exception as e:
            logger.error(f"创建通知失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, notification_id: int):
        """根据ID获取通知"""
        cls._create_table()
        try:
            result = db_manager.fetch_one(f"""
                SELECT id, user_id, title, content, notification_type, status, priority, action_url, created_at, read_at
                FROM {cls.TABLE_NAME} WHERE id = ?
            """, (notification_id,))
            
            if result:
                return cls(
                    id=result[0],
                    user_id=result[1],
                    title=result[2],
                    content=result[3],
                    notification_type=NotificationType(result[4]),
                    status=NotificationStatus(result[5]),
                    priority=result[6],
                    action_url=result[7],
                    created_at=result[8],
                    read_at=result[9]
                )
        except Exception as e:
            logger.error(f"获取通知失败: {str(e)}")
        return None
    
    @classmethod
    def get_by_user(cls, user_id: int, status: str = None, limit: int = 20):
        """获取用户通知"""
        cls._create_table()
        try:
            query = f"""
                SELECT id, user_id, title, content, notification_type, status, priority, action_url, created_at, read_at
                FROM {cls.TABLE_NAME} WHERE user_id = ?
            """
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            results = db_manager.fetch_all(query, tuple(params))
            notifications = []
            for result in results:
                notifications.append(cls(
                    id=result[0],
                    user_id=result[1],
                    title=result[2],
                    content=result[3],
                    notification_type=NotificationType(result[4]),
                    status=NotificationStatus(result[5]),
                    priority=result[6],
                    action_url=result[7],
                    created_at=result[8],
                    read_at=result[9]
                ))
            return notifications
        except Exception as e:
            logger.error(f"获取用户通知失败: {str(e)}")
            return []
    
    @classmethod
    def mark_as_read(cls, notification_id: int):
        """标记为已读"""
        cls._create_table()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db_manager.execute(f"""
                UPDATE {cls.TABLE_NAME} SET status = 'read', read_at = ? WHERE id = ?
            """, (now, notification_id))
            
            logger.info(f"标记通知已读: notification_id={notification_id}")
            return cls.get_by_id(notification_id)
        except Exception as e:
            logger.error(f"标记通知已读失败: {str(e)}")
            return None
    
    @classmethod
    def mark_all_read(cls, user_id: int):
        """标记全部已读"""
        cls._create_table()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db_manager.execute(f"""
                UPDATE {cls.TABLE_NAME} SET status = 'read', read_at = ? WHERE user_id = ? AND status = 'pending'
            """, (now, user_id))
            
            logger.info(f"标记全部通知已读: user_id={user_id}")
        except Exception as e:
            logger.error(f"标记全部通知已读失败: {str(e)}")
    
    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """获取未读数量"""
        cls._create_table()
        try:
            result = db_manager.fetch_one(f"""
                SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE user_id = ? AND status = 'pending'
            """, (user_id,))
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"获取未读数量失败: {str(e)}")
            return 0