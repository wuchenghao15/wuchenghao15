import sqlite3
from app.config import Config
from app.utils.logging import logger

class AIInstance:
    """AI实例数据模型"""
    
    def __init__(self, instance_id=None, collection_id=None, ai_type="general", name="", description="", functions=None, responsibilities=None, status="active", config=None, bound_user=None, created_at=None, updated_at=None):
        self.instance_id = instance_id
        self.collection_id = collection_id
        self.ai_type = ai_type
        self.name = name
        self.description = description
        self.functions = functions or []
        self.responsibilities = responsibilities or []
        self.status = status
        self.config = config or {}
        self.bound_user = bound_user
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)
    
    @staticmethod
    def create_table():
        """创建AI实例相关表"""
        from app.utils.db import db_manager
        
        # 创建AI集表
        ai_collections_columns = {
            'collection_id': 'TEXT PRIMARY KEY',
            'name': 'TEXT NOT NULL',
            'description': 'TEXT',
            'status': 'TEXT NOT NULL DEFAULT "active"',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        # 创建AI实例表（扩展版本）
        ai_instances_columns = {
            'instance_id': 'TEXT PRIMARY KEY',
            'collection_id': 'TEXT',
            'ai_type': 'TEXT NOT NULL DEFAULT "general"',
            'name': 'TEXT NOT NULL',
            'ai_name': 'TEXT NOT NULL',
            'description': 'TEXT',
            'functions': 'TEXT NOT NULL DEFAULT "[]"',
            'responsibilities': 'TEXT NOT NULL DEFAULT "[]"',
            'status': 'TEXT NOT NULL DEFAULT "active"',
            'config': 'TEXT NOT NULL DEFAULT "{}"',
            'bound_user': 'INTEGER',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        # 使用db_manager创建表，这样表名会被正确加密
        success1 = db_manager.create_table('ai_collections', ai_collections_columns)
        success2 = db_manager.create_table('ai_instances', ai_instances_columns)
        
        if success1 and success2:
            logger.info("AI实例表和AI集表创建成功")
            return True
        else:
            logger.error("创建AI实例表和AI集表失败")
            return False
    
    def save(self):
        """保存AI实例信息"""
        import json
        import time
        from app.utils.db import db_manager
        
        config_json = json.dumps(self.config)
        functions_json = json.dumps(self.functions)
        responsibilities_json = json.dumps(self.responsibilities)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 使用db_manager进行数据库操作
        try:
            # 先检查实例是否存在
            existing = db_manager.fetch_one('SELECT instance_id FROM ai_instances WHERE instance_id=?', (self.instance_id,))
            
            if existing:
                # 更新现有AI实例
                update_query = '''
                    UPDATE ai_instances SET 
                        collection_id=?, ai_type=?, name=?, ai_name=?, description=?, functions=?, responsibilities=?, 
                        status=?, config=?, bound_user=?, updated_at=? 
                    WHERE instance_id=?
                '''
                params = (
                    self.collection_id, self.ai_type, self.name, self.name, self.description, functions_json, 
                    responsibilities_json, self.status, config_json, self.bound_user, 
                    current_time, self.instance_id
                )
                db_manager.execute(update_query, params)
                logger.debug(f"更新AI实例: {self.instance_id}")
            else:
                # 创建新AI实例
                insert_query = '''
                    INSERT INTO ai_instances (
                        instance_id, collection_id, ai_type, name, ai_name, description, functions, 
                        responsibilities, status, config, bound_user, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    self.instance_id, self.collection_id, self.ai_type, self.name, self.name, self.description, 
                    functions_json, responsibilities_json, self.status, config_json, self.bound_user, 
                    current_time, current_time
                )
                db_manager.execute(insert_query, params)
                logger.debug(f"创建AI实例: {self.instance_id}")
            
            return self
        except Exception as e:
            logger.error(f"保存AI实例失败: {str(e)}")
            return None
    
    @staticmethod
    def get_by_id(instance_id):
        """通过ID获取AI实例"""
        import json
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_instances WHERE instance_id=?'
        row = db_manager.fetch_one(query, (instance_id,))
        
        if row:
            try:
                # 根据行长度判断表结构版本
                if len(row) >= 12:
                    # 完整的新表结构
                    return AIInstance(
                        instance_id=row[0],
                        collection_id=row[1],
                        ai_type=row[2],
                        name=row[3] or "",
                        description=row[4] or "",
                        functions=json.loads(row[5]) if row[5] else [],
                        responsibilities=json.loads(row[6]) if row[6] else [],
                        status=row[7],
                        config=json.loads(row[8]) if row[8] else {},
                        bound_user=row[9],
                        created_at=row[10],
                        updated_at=row[11]
                    )
                elif len(row) == 6:
                    # 旧表结构
                    return AIInstance(
                        instance_id=row[0],
                        ai_type=row[1],
                        status=row[2],
                        config=json.loads(row[3]) if row[3] else {},
                        bound_user=row[4],
                        created_at=row[5],
                        name=row[0],  # 使用instance_id作为默认名称
                        description="",
                        functions=[],
                        responsibilities=[]
                    )
            except Exception as e:
                logger.error(f"解析AI实例数据失败: {str(e)}")
        return None
    
    @staticmethod
    def get_by_user(user_id):
        """获取用户绑定的AI实例"""
        import json
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_instances WHERE bound_user=?'
        rows = db_manager.fetch_all(query, (user_id,))
        
        instances = []
        for row in rows:
            try:
                # 根据行长度判断表结构版本
                if len(row) >= 12:
                    # 完整的新表结构
                    instances.append(AIInstance(
                        instance_id=row[0],
                        collection_id=row[1],
                        ai_type=row[2],
                        name=row[3] or "",
                        description=row[4] or "",
                        functions=json.loads(row[5]) if row[5] else [],
                        responsibilities=json.loads(row[6]) if row[6] else [],
                        status=row[7],
                        config=json.loads(row[8]) if row[8] else {},
                        bound_user=row[9],
                        created_at=row[10],
                        updated_at=row[11]
                    ))
                elif len(row) == 6:
                    # 旧表结构
                    instances.append(AIInstance(
                        instance_id=row[0],
                        ai_type=row[1],
                        status=row[2],
                        config=json.loads(row[3]) if row[3] else {},
                        bound_user=row[4],
                        created_at=row[5],
                        name=row[0],  # 使用instance_id作为默认名称
                        description="",
                        functions=[],
                        responsibilities=[]
                    ))
            except Exception as e:
                logger.error(f"解析AI实例数据失败: {str(e)}")
                continue
        return instances
    
    @staticmethod
    def get_all_instances():
        """获取所有AI实例"""
        import json
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_instances ORDER BY created_at DESC'
        rows = db_manager.fetch_all(query)
        
        instances = []
        for row in rows:
            try:
                # 根据行长度判断表结构版本
                if len(row) >= 12:
                    # 完整的新表结构
                    instances.append(AIInstance(
                        instance_id=row[0],
                        collection_id=row[1],
                        ai_type=row[2],
                        name=row[3] or "",
                        description=row[4] or "",
                        functions=json.loads(row[5]) if row[5] else [],
                        responsibilities=json.loads(row[6]) if row[6] else [],
                        status=row[7],
                        config=json.loads(row[8]) if row[8] else {},
                        bound_user=row[9],
                        created_at=row[10],
                        updated_at=row[11]
                    ))
                elif len(row) == 6:
                    # 旧表结构
                    instances.append(AIInstance(
                        instance_id=row[0],
                        ai_type=row[1],
                        status=row[2],
                        config=json.loads(row[3]) if row[3] else {},
                        bound_user=row[4],
                        created_at=row[5],
                        name=row[0],  # 使用instance_id作为默认名称
                        description="",
                        functions=[],
                        responsibilities=[]
                    ))
            except Exception as e:
                logger.error(f"解析AI实例数据失败: {str(e)}")
                continue
        return instances
    
    def update_status(self, new_status):
        """更新AI实例状态"""
        self.status = new_status
        self.save()
        logger.info(f"更新AI实例状态: {self.instance_id} -> {new_status}")
    
    def bind_to_user(self, user_id):
        """绑定到用户"""
        self.bound_user = user_id
        self.save()
        logger.info(f"AI实例 {self.instance_id} 绑定到用户 {user_id}")
    
    def unbind_from_user(self):
        """解除用户绑定"""
        self.bound_user = None
        self.save()
        logger.info(f"AI实例 {self.instance_id} 解除用户绑定")
    
    def delete(self):
        """删除AI实例"""
        conn = AIInstance._connect_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ai_instances WHERE instance_id=?', (self.instance_id,))
        conn.commit()
        conn.close()
        logger.info(f"删除AI实例: {self.instance_id}")
    
    def to_dict(self):
        """将AI实例转换为字典格式"""
        return {
            'instance_id': self.instance_id,
            'collection_id': self.collection_id,
            'ai_type': self.ai_type,
            'name': self.name,
            'description': self.description,
            'functions': self.functions,
            'responsibilities': self.responsibilities,
            'status': self.status,
            'config': self.config,
            'bound_user': self.bound_user,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


# AI集管理类
class AICollection:
    """AI集数据模型"""
    
    def __init__(self, collection_id=None, name="", description="", status="active", created_at=None, updated_at=None):
        self.collection_id = collection_id
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)
    
    @staticmethod
    def create(collection_id, name, description="", status="active"):
        """创建AI集"""
        import time
        conn = AICollection._connect_db()
        cursor = conn.cursor()
        
        # 确保ai_collections表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_collections (
                collection_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 检查AI集是否已存在
        cursor.execute('SELECT collection_id FROM ai_collections WHERE collection_id=?', (collection_id,))
        existing = cursor.fetchone()
        
        if existing:
            logger.warning(f"AI集 {collection_id} 已存在")
            conn.commit()
            conn.close()
            return None
        
        # 创建新AI集
        cursor.execute('''
            INSERT INTO ai_collections (collection_id, name, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (collection_id, name, description, status, 
              time.strftime("%Y-%m-%d %H:%M:%S"), time.strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        logger.info(f"创建AI集成功: {collection_id}")
        return AICollection(collection_id, name, description, status)
    
    @staticmethod
    def get_by_id(collection_id):
        """通过ID获取AI集"""
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_collections WHERE collection_id=?'
        row = db_manager.fetch_one(query, (collection_id,))
        
        if row:
            return AICollection(
                collection_id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
        return None
    
    @staticmethod
    def get_all():
        """获取所有AI集"""
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_collections ORDER BY created_at DESC'
        rows = db_manager.fetch_all(query)
        
        collections = []
        for row in rows:
            collections.append(AICollection(
                collection_id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5]
            ))
        return collections
    
    def save(self):
        """保存AI集信息"""
        import time
        from app.utils.db import db_manager
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 检查AI集是否已存在
        existing = db_manager.fetch_one('SELECT collection_id FROM ai_collections WHERE collection_id=?', (self.collection_id,))
        
        if existing:
            # 更新现有AI集
            update_query = '''
                UPDATE ai_collections SET name=?, description=?, status=?, updated_at=?
                WHERE collection_id=?
            '''
            params = (self.name, self.description, self.status, current_time, self.collection_id)
            db_manager.execute(update_query, params)
            logger.info(f"更新AI集: {self.collection_id}")
        else:
            # 创建新AI集
            insert_query = '''
                INSERT INTO ai_collections (collection_id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            params = (self.collection_id, self.name, self.description, self.status, current_time, current_time)
            db_manager.execute(insert_query, params)
            logger.info(f"创建AI集: {self.collection_id}")
        
        return self
    
    def delete(self):
        """删除AI集"""
        from app.utils.db import db_manager
        
        # 先删除该AI集下的所有实例
        delete_instances_query = 'DELETE FROM ai_instances WHERE collection_id=?'
        db_manager.execute(delete_instances_query, (self.collection_id,))
        
        # 然后删除AI集本身
        delete_collection_query = 'DELETE FROM ai_collections WHERE collection_id=?'
        db_manager.execute(delete_collection_query, (self.collection_id,))
        
        logger.info(f"删除AI集: {self.collection_id}")
    
    def get_instances(self):
        """获取AI集中的所有实例"""
        import json
        from app.utils.db import db_manager
        
        query = 'SELECT * FROM ai_instances WHERE collection_id=?'
        rows = db_manager.fetch_all(query, (self.collection_id,))
        
        instances = []
        for row in rows:
            instances.append(AIInstance(
                instance_id=row[0],
                collection_id=row[1],
                ai_type=row[2],
                name=row[3],
                description=row[4],
                functions=json.loads(row[5]),
                responsibilities=json.loads(row[6]),
                status=row[7],
                config=json.loads(row[8]),
                bound_user=row[9],
                created_at=row[10],
                updated_at=row[11]
            ))
        return instances
    
    def update_status(self, new_status):
        """更新AI集状态"""
        self.status = new_status
        self.save()
        logger.info(f"更新AI集状态: {self.collection_id} -> {new_status}")
    
    def add_instance(self, instance):
        """向AI集中添加实例"""
        instance.collection_id = self.collection_id
        instance.save()
        logger.info(f"AI实例 {instance.instance_id} 已添加到AI集 {self.collection_id}")
        return True
    
    def remove_instance(self, instance_id):
        """从AI集中移除实例"""
        conn = AICollection._connect_db()
        cursor = conn.cursor()
        
        # 将实例的collection_id设为NULL
        cursor.execute('UPDATE ai_instances SET collection_id=NULL WHERE instance_id=? AND collection_id=?', 
                      (instance_id, self.collection_id))
        
        if cursor.rowcount > 0:
            logger.info(f"AI实例 {instance_id} 已从AI集 {self.collection_id} 中移除")
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        logger.warning(f"AI实例 {instance_id} 不在AI集 {self.collection_id} 中")
        return False
