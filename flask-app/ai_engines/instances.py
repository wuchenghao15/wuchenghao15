# -*- coding: utf-8 -*-
import threading
import time
import json
from app.config import Config
from app.utils.logging import logger
from app.models.ai import AIInstance, AICollection
from app.models.enhanced_ai_employee import EnhancedAIEmployee
from app.ai.sandbox_manager import sandbox_manager
from app.ai.self_healing import SelfHealingSystem

ai_brain_service = None
deep_self_learning = None

def _get_ai_brain_service():
    """获取AI脑库服务实例"""
    global ai_brain_service
    if ai_brain_service is None:
        from app.services.ai_brain_service import ai_brain_service as service
        ai_brain_service = service
    return ai_brain_service

def _get_deep_self_learning():
    """获取深度自我学习模块实例"""
    global deep_self_learning
    if deep_self_learning is None:
        from app.ai.deep_learning import get_deep_self_learning
        deep_self_learning = get_deep_self_learning(ai_instance_manager)
    return deep_self_learning

class AIInstanceManager:
    """AI实例管理器"""

    def __init__(self):
        self.ai_instances = {}
        self.instance_lock = threading.Lock()
        self.instance_count = 0
        self._load_instances_from_db()
        self.ai_collections = {}
        self._load_collections_from_db()
        self.self_healing_system = SelfHealingSystem(self)
        import os
        if os.environ.get('AI_SELF_HEALING_ENABLED', 'false').lower() == 'true':
            self.self_healing_system.start()
        self.deep_self_learning = None
        if os.environ.get('AI_DEEP_LEARNING_ENABLED', 'true').lower() == 'true':
            self._init_deep_learning()

    def _init_deep_learning(self):
        """初始化深度自我学习系统"""
        try:
            if deep_self_learning is None:
                from app.ai.deep_learning import DeepSelfLearning
                deep_self_learning = DeepSelfLearning(self)
                self.deep_self_learning = deep_self_learning
                logger.info("深度自我学习系统初始化成功")
        except Exception as e:
            logger.error(f"深度自我学习系统初始化失败: {str(e)}")

    def _load_instances_from_db(self):
        """从数据库加载AI实例到内存"""
        try:
            instances = AIInstance.get_all_instances()
            for instance in instances:
                self.ai_instances[instance.instance_id] = {
                    'instance_id': instance.instance_id,
                    'collection_id': instance.collection_id,
                    'ai_type': instance.ai_type,
                    'name': instance.name,
                    'description': instance.description,
                    'functions': instance.functions,
                    'responsibilities': instance.responsibilities,
                    'status': instance.status,
                    'config': instance.config,
                    'bound_user': instance.bound_user,
                    'created_at': time.mktime(time.strptime(instance.created_at, "%Y-%m-%d %H:%M:%S")),
                    'last_used': time.time(),
                    'updated_at': time.mktime(time.strptime(instance.updated_at, "%Y-%m-%d %H:%M:%S")),
                    'tasks': []
                }
            self.instance_count = len(self.ai_instances)
            logger.info(f"从数据库加载了 {self.instance_count} 个AI实例到内存")
        except Exception as e:
            logger.error(f"从数据库加载AI实例失败: {str(e)}")
            self.ai_instances = {}
            self.instance_count = 0

    def _load_collections_from_db(self):
        """从数据库加载AI集到内存"""
        try:
            collections = AICollection.get_all()
            with self.instance_lock:
                for collection in collections:
                    self.ai_collections[collection.collection_id] = {
                        'collection_id': collection.collection_id,
                        'name': collection.name,
                        'description': collection.description,
                        'created_at': time.mktime(time.strptime(collection.created_at, "%Y-%m-%d %H:%M:%S")),
                        'updated_at': time.mktime(time.strptime(collection.updated_at, "%Y-%m-%d %H:%M:%S"))
                    }
                logger.info(f"从数据库加载了 {len(self.ai_collections)} 个AI集到内存")
        except Exception as e:
            logger.error(f"从数据库加载AI集失败: {str(e)}")
            self.ai_collections = {}

    def create_ai_instance(self, instance_id, ai_type="general", name="", description="",
                           auto_load_knowledge=True, enable_self_learning=True):
        """创建AI实例"""
        with self.instance_lock:
            if instance_id in self.ai_instances:
                logger.warning(f"AI实例 {instance_id} 已存在")
                return self.ai_instances[instance_id]
            
            instance_data = {
                'instance_id': instance_id,
                'ai_type': ai_type,
                'name': name,
                'description': description,
                'functions': [],
                'responsibilities': [],
                'status': 'active',
                'config': {},
                'bound_user': None,
                'created_at': time.time(),
                'last_used': time.time(),
                'updated_at': time.time(),
                'tasks': []
            }
            
            self.ai_instances[instance_id] = instance_data
            self.instance_count += 1
            
            db_instance = AIInstance(
                instance_id=instance_id,
                ai_type=ai_type,
                name=name,
                description=description,
                status='active'
            )
            db_instance.save()
            
            logger.info(f"创建AI实例成功: {instance_id}")
            return instance_data

    def get_ai_instance(self, instance_id):
        """获取AI实例"""
        with self.instance_lock:
            instance = self.ai_instances.get(instance_id)
            if instance:
                instance['last_used'] = time.time()
            return instance

    def bind_ai_instance(self, user_id, instance_id):
        """将AI实例绑定到用户"""
        with self.instance_lock:
            ai_instance = self.ai_instances.get(instance_id)
            if not ai_instance:
                logger.error(f"AI实例 {instance_id} 不存在")
                return False
            ai_instance['bound_user'] = user_id
            return True

    def unbind_ai_instance(self, instance_id):
        """解除AI实例与用户的绑定"""
        with self.instance_lock:
            ai_instance = self.ai_instances.get(instance_id)
            if not ai_instance:
                logger.error(f"AI实例 {instance_id} 不存在")
                return False
            ai_instance['bound_user'] = None
            return True

    def update_ai_instance(self, instance_id, updates):
        """更新AI实例"""
        with self.instance_lock:
            ai_instance = self.ai_instances.get(instance_id)
            if not ai_instance:
                return False
            ai_instance.update(updates)
            ai_instance['updated_at'] = time.time()
            return True

    def delete_ai_instance(self, instance_id):
        """删除AI实例"""
        with self.instance_lock:
            if instance_id in self.ai_instances:
                db_instance = AIInstance.get_by_id(instance_id)
                if db_instance:
                    db_instance.delete()
                del self.ai_instances[instance_id]
                self.instance_count -= 1
                logger.info(f"AI实例 {instance_id} 已删除")
                return True
            return False

    def create_collection(self, collection_id, name, description="", status="active"):
        """创建AI集"""
        with self.instance_lock:
            if collection_id in self.ai_collections:
                logger.warning(f"AI集 {collection_id} 已存在")
                return self.ai_collections[collection_id]
            
            collection_data = {
                'collection_id': collection_id,
                'name': name,
                'description': description,
                'status': status,
                'created_at': time.time(),
                'updated_at': time.time()
            }
            
            self.ai_collections[collection_id] = collection_data
            
            db_collection = AICollection(
                collection_id=collection_id,
                name=name,
                description=description,
                status=status
            )
            db_collection.save()
            
            logger.info(f"创建AI集成功: {collection_id}")
            return collection_data

    def get_collection(self, collection_id):
        """获取AI集"""
        with self.instance_lock:
            return self.ai_collections.get(collection_id)

    def get_all_collections(self):
        """获取所有AI集"""
        with self.instance_lock:
            return list(self.ai_collections.values())

    def delete_collection(self, collection_id):
        """删除AI集"""
        with self.instance_lock:
            if collection_id in self.ai_collections:
                db_collection = AICollection.get_by_id(collection_id)
                if db_collection:
                    db_collection.delete()
                del self.ai_collections[collection_id]
                logger.info(f"AI集 {collection_id} 已删除")
                return True
            return False

    def add_instance_to_collection(self, instance_id, collection_id):
        """将AI实例添加到AI集"""
        with self.instance_lock:
            ai_instance = self.ai_instances.get(instance_id)
            if not ai_instance:
                logger.error(f"AI实例 {instance_id} 不存在")
                return False
            ai_instance['collection_id'] = collection_id
            return True

    def remove_instance_from_collection(self, instance_id):
        """将AI实例从AI集中移除"""
        with self.instance_lock:
            ai_instance = self.ai_instances.get(instance_id)
            if not ai_instance:
                return False
            ai_instance['collection_id'] = None
            return True

    def get_instances_by_collection(self, collection_id):
        """获取AI集中的所有实例"""
        with self.instance_lock:
            instances = []
            for instance in self.ai_instances.values():
                if instance.get('collection_id') == collection_id:
                    instances.append(instance)
            return instances

    def refresh_from_db(self):
        """从数据库刷新数据"""
        with self.instance_lock:
            self._load_instances_from_db()
            self._load_collections_from_db()
            return True

    def get_all_instances(self):
        """获取所有AI实例"""
        with self.instance_lock:
            return list(self.ai_instances.values())

    def cleanup_inactive_instances(self, inactive_time=3600):
        """清理不活跃的AI实例"""
        with self.instance_lock:
            current_time = time.time()
            inactive_instances = []
            
            for instance_id, instance in list(self.ai_instances.items()):
                if current_time - instance['last_used'] > inactive_time:
                    inactive_instances.append(instance_id)
                    del self.ai_instances[instance_id]
                    self.instance_count -= 1
            
            if inactive_instances:
                logger.info(f"清理了 {len(inactive_instances)} 个不活跃AI实例")
            
            return inactive_instances

    def auto_upgrade(self):
        """自动升级所有AI实例和AI集"""
        with self.instance_lock:
            logger.info("开始自动升级所有AI实例和AI集")
            upgraded_count = 0
            
            for instance_id, instance in list(self.ai_instances.items()):
                try:
                    config = instance.get('config', {})
                    if 'version' not in config or config['version'] < 1.2:
                        config['version'] = 1.2
                        instance['config'] = config
                        instance['updated_at'] = time.time()
                        upgraded_count += 1
                except Exception as e:
                    logger.error(f"升级AI实例 {instance_id} 失败: {str(e)}")
            
            logger.info(f"自动升级完成,共升级 {upgraded_count} 个AI实例")
            return upgraded_count

ai_instance_manager = AIInstanceManager()
