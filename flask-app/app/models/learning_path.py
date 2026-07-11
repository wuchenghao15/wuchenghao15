"""学习路径模型 - MTSCOS AI项目"""

from datetime import datetime
from enum import Enum
from app.utils.db import DatabaseManager
from app.utils.logger import get_logger

logger = get_logger(__name__)
db_manager = DatabaseManager()


class LearningPathStatus(Enum):
    """学习路径状态"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    PAUSED = 'paused'


class LearningPath:
    """学习路径模型"""
    
    TABLE_NAME = 'learning_paths'
    
    @classmethod
    def _create_table(cls):
        """创建表（如果不存在）"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        except Exception as e:
            logger.error(f"创建学习路径表失败: {str(e)}")
    
    def __init__(self, id=None, user_id=None, name=None, description=None, 
                 status=LearningPathStatus.DRAFT, created_at=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, Enum) else self.status,
            'created_at': self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at if isinstance(self.updated_at, str) else self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create(cls, user_id: int, name: str, description: str = None):
        """创建学习路径"""
        cls._create_table()
        try:
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} (user_id, name, description)
                VALUES (?, ?, ?)
            """, (user_id, name, description))
            
            result = db_manager.fetch_one(f"SELECT last_insert_rowid()")
            path_id = result[0] if result else None
            
            logger.info(f"创建学习路径成功: id={path_id}, user_id={user_id}")
            return cls.get_by_id(path_id)
        except Exception as e:
            logger.error(f"创建学习路径失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, path_id: int):
        """根据ID获取学习路径"""
        cls._create_table()
        try:
            result = db_manager.fetch_one(f"""
                SELECT id, user_id, name, description, status, created_at, updated_at
                FROM {cls.TABLE_NAME} WHERE id = ?
            """, (path_id,))
            
            if result:
                return cls(
                    id=result[0],
                    user_id=result[1],
                    name=result[2],
                    description=result[3],
                    status=LearningPathStatus(result[4]),
                    created_at=result[5],
                    updated_at=result[6]
                )
        except Exception as e:
            logger.error(f"获取学习路径失败: {str(e)}")
        return None
    
    @classmethod
    def get_by_user(cls, user_id: int, status: str = None, limit: int = 20):
        """获取用户学习路径"""
        cls._create_table()
        try:
            query = f"""
                SELECT id, user_id, name, description, status, created_at, updated_at
                FROM {cls.TABLE_NAME} WHERE user_id = ?
            """
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            results = db_manager.fetch_all(query, tuple(params))
            paths = []
            for result in results:
                paths.append(cls(
                    id=result[0],
                    user_id=result[1],
                    name=result[2],
                    description=result[3],
                    status=LearningPathStatus(result[4]),
                    created_at=result[5],
                    updated_at=result[6]
                ))
            return paths
        except Exception as e:
            logger.error(f"获取用户学习路径失败: {str(e)}")
            return []
    
    @classmethod
    def update(cls, path_id: int, **kwargs):
        """更新学习路径"""
        cls._create_table()
        try:
            update_fields = []
            params = []
            
            if 'name' in kwargs:
                update_fields.append('name = ?')
                params.append(kwargs['name'])
            if 'description' in kwargs:
                update_fields.append('description = ?')
                params.append(kwargs['description'])
            if 'status' in kwargs:
                status_value = kwargs['status'].value if isinstance(kwargs['status'], Enum) else kwargs['status']
                update_fields.append('status = ?')
                params.append(status_value)
            
            params.append(path_id)
            
            if update_fields:
                db_manager.execute(f"""
                    UPDATE {cls.TABLE_NAME} SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?
                """, tuple(params + [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]))
            
            logger.info(f"更新学习路径成功: id={path_id}")
            return cls.get_by_id(path_id)
        except Exception as e:
            logger.error(f"更新学习路径失败: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, path_id: int):
        """删除学习路径"""
        cls._create_table()
        try:
            db_manager.execute(f"DELETE FROM {cls.TABLE_NAME} WHERE id = ?", (path_id,))
            logger.info(f"删除学习路径成功: id={path_id}")
            return True
        except Exception as e:
            logger.error(f"删除学习路径失败: {str(e)}")
            return False


class PathNode:
    """路径节点模型"""
    
    TABLE_NAME = 'learning_path_nodes'
    
    @classmethod
    def _create_table(cls):
        """创建表（如果不存在）"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_id INTEGER NOT NULL,
                    node_order INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    node_type TEXT DEFAULT 'lesson',
                    content_url TEXT,
                    estimated_time INTEGER,
                    completed INTEGER DEFAULT 0,
                    completed_at TIMESTAMP
                )
            """)
        except Exception as e:
            logger.error(f"创建路径节点表失败: {str(e)}")
    
    def __init__(self, id=None, path_id=None, node_order=None, title=None, description=None,
                 node_type='lesson', content_url=None, estimated_time=None, 
                 completed=False, completed_at=None):
        self.id = id
        self.path_id = path_id
        self.node_order = node_order
        self.title = title
        self.description = description
        self.node_type = node_type
        self.content_url = content_url
        self.estimated_time = estimated_time
        self.completed = completed
        self.completed_at = completed_at
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'path_id': self.path_id,
            'order': self.node_order,
            'title': self.title,
            'description': self.description,
            'type': self.node_type,
            'content_url': self.content_url,
            'estimated_time': self.estimated_time,
            'completed': bool(self.completed),
            'completed_at': self.completed_at if isinstance(self.completed_at, str) else self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def create(cls, path_id: int, node_order: int, title: str, description: str = None,
               node_type: str = 'lesson', content_url: str = None, estimated_time: int = None):
        """创建路径节点"""
        cls._create_table()
        try:
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} (path_id, node_order, title, description, node_type, content_url, estimated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (path_id, node_order, title, description, node_type, content_url, estimated_time))
            
            result = db_manager.fetch_one(f"SELECT last_insert_rowid()")
            node_id = result[0] if result else None
            
            logger.info(f"创建路径节点成功: id={node_id}, path_id={path_id}")
            return cls.get_by_id(node_id)
        except Exception as e:
            logger.error(f"创建路径节点失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, node_id: int):
        """根据ID获取路径节点"""
        cls._create_table()
        try:
            result = db_manager.fetch_one(f"""
                SELECT id, path_id, node_order, title, description, node_type, content_url, estimated_time, completed, completed_at
                FROM {cls.TABLE_NAME} WHERE id = ?
            """, (node_id,))
            
            if result:
                return cls(
                    id=result[0],
                    path_id=result[1],
                    node_order=result[2],
                    title=result[3],
                    description=result[4],
                    node_type=result[5],
                    content_url=result[6],
                    estimated_time=result[7],
                    completed=bool(result[8]),
                    completed_at=result[9]
                )
        except Exception as e:
            logger.error(f"获取路径节点失败: {str(e)}")
        return None
    
    @classmethod
    def get_by_path(cls, path_id: int):
        """获取路径的所有节点"""
        cls._create_table()
        try:
            results = db_manager.fetch_all(f"""
                SELECT id, path_id, node_order, title, description, node_type, content_url, estimated_time, completed, completed_at
                FROM {cls.TABLE_NAME} WHERE path_id = ? ORDER BY node_order
            """, (path_id,))
            
            nodes = []
            for result in results:
                nodes.append(cls(
                    id=result[0],
                    path_id=result[1],
                    node_order=result[2],
                    title=result[3],
                    description=result[4],
                    node_type=result[5],
                    content_url=result[6],
                    estimated_time=result[7],
                    completed=bool(result[8]),
                    completed_at=result[9]
                ))
            return nodes
        except Exception as e:
            logger.error(f"获取路径节点失败: {str(e)}")
            return []
    
    @classmethod
    def mark_completed(cls, node_id: int):
        """标记节点完成"""
        cls._create_table()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db_manager.execute(f"""
                UPDATE {cls.TABLE_NAME} SET completed = 1, completed_at = ? WHERE id = ?
            """, (now, node_id))
            
            logger.info(f"标记节点完成: node_id={node_id}")
            return cls.get_by_id(node_id)
        except Exception as e:
            logger.error(f"标记节点完成失败: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, node_id: int):
        """删除路径节点"""
        cls._create_table()
        try:
            db_manager.execute(f"DELETE FROM {cls.TABLE_NAME} WHERE id = ?", (node_id,))
            logger.info(f"删除路径节点成功: id={node_id}")
            return True
        except Exception as e:
            logger.error(f"删除路径节点失败: {str(e)}")
            return False