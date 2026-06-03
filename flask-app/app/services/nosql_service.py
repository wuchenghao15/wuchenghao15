#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoSQL服务 - 实现多种NoSQL数据库支持
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class NoSQLType(Enum):
    """NoSQL类型"""
    REDIS = "redis"
    MONGO = "mongo"
    MEMCACHED = "memcached"
    LEVELDB = "leveldb"
    ROCKSDB = "rocksdb"


class DatabaseType(Enum):
    """数据库类型"""
    KEY_VALUE = "key_value"
    DOCUMENT = "document"
    COLUMN_FAMILY = "column_family"
    GRAPH = "graph"


@dataclass
class NoSQLRecord:
    """NoSQL记录"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'value': self.value,
            'ttl': self.ttl,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class InMemoryKVStore:
    """内存键值存储"""
    
    def __init__(self):
        self._store: Dict[str, NoSQLRecord] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        with self._lock:
            record = self._store.get(key)
            if record:
                # 检查TTL
                if record.ttl and (time.time() - record.created_at) > record.ttl:
                    del self._store[key]
                    return None
                return record.value
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置值"""
        with self._lock:
            self._store[key] = NoSQLRecord(
                key=key,
                value=value,
                ttl=ttl,
                updated_at=time.time()
            )

    def delete(self, key: str) -> bool:
        """删除值"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
        return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            # 先清理过期的
            now = time.time()
            expired = [k for k, v in self._store.items() 
                      if v.ttl and (now - v.created_at) > v.ttl]
            for k in expired:
                del self._store[k]
            
            return list(self._store.keys())

    def size(self) -> int:
        """获取存储大小"""
        with self._lock:
            return len(self._store)

    def clear(self):
        """清空存储"""
        with self._lock:
            self._store.clear()


class NoSQLService:
    """NoSQL服务"""

    def __init__(self):
        self._db_type = NoSQLType.REDIS
        self._kv_store = InMemoryKVStore()
        self._document_store: Dict[str, Dict[str, Any]] = {}
        self._collection_store: Dict[str, List[Dict]] = {}
        self._lock = threading.RLock()
        logger.info("NoSQL服务初始化完成")

    def set_db_type(self, db_type: NoSQLType):
        """设置数据库类型"""
        self._db_type = db_type
        logger.info(f"NoSQL类型已设置为: {db_type.value}")

    def get_db_type(self) -> NoSQLType:
        """获取数据库类型"""
        return self._db_type

    # 键值操作
    def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        return self._kv_store.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置键值"""
        self._kv_store.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """删除键值"""
        return self._kv_store.delete(key)

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self._kv_store.exists(key)

    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取键列表"""
        all_keys = self._kv_store.keys()
        if pattern:
            import fnmatch
            return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        return all_keys

    def incr(self, key: str, amount: int = 1) -> int:
        """递增数值"""
        with self._lock:
            value = self._kv_store.get(key)
            if value is None:
                new_value = amount
            else:
                new_value = int(value) + amount
            self._kv_store.set(key, new_value)
            return new_value

    def decr(self, key: str, amount: int = 1) -> int:
        """递减数值"""
        return self.incr(key, -amount)

    # 文档操作
    def insert_document(self, collection: str, document: Dict) -> str:
        """插入文档"""
        with self._lock:
            if collection not in self._collection_store:
                self._collection_store[collection] = []
            
            doc_id = document.get('_id', str(len(self._collection_store[collection]) + 1))
            document['_id'] = doc_id
            document['created_at'] = time.time()
            document['updated_at'] = time.time()
            
            self._collection_store[collection].append(document)
            return doc_id

    def find_document(self, collection: str, query: Dict) -> List[Dict]:
        """查询文档"""
        with self._lock:
            if collection not in self._collection_store:
                return []
            
            results = []
            for doc in self._collection_store[collection]:
                match = True
                for key, value in query.items():
                    if doc.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(doc)
            
            return results

    def find_one_document(self, collection: str, query: Dict) -> Optional[Dict]:
        """查询单个文档"""
        results = self.find_document(collection, query)
        return results[0] if results else None

    def update_document(self, collection: str, query: Dict, update: Dict) -> bool:
        """更新文档"""
        with self._lock:
            if collection not in self._collection_store:
                return False
            
            updated = False
            for doc in self._collection_store[collection]:
                match = True
                for key, value in query.items():
                    if doc.get(key) != value:
                        match = False
                        break
                if match:
                    doc.update(update)
                    doc['updated_at'] = time.time()
                    updated = True
            
            return updated

    def delete_document(self, collection: str, query: Dict) -> bool:
        """删除文档"""
        with self._lock:
            if collection not in self._collection_store:
                return False
            
            original_count = len(self._collection_store[collection])
            self._collection_store[collection] = [
                doc for doc in self._collection_store[collection]
                if not all(doc.get(k) == v for k, v in query.items())
            ]
            
            return len(self._collection_store[collection]) < original_count

    def get_collection_size(self, collection: str) -> int:
        """获取集合大小"""
        with self._lock:
            return len(self._collection_store.get(collection, []))

    # 哈希操作(Redis Hash)
    def hset(self, key: str, field: str, value: Any):
        """设置哈希字段"""
        with self._lock:
            hash_data = self._kv_store.get(key) or {}
            hash_data[field] = value
            self._kv_store.set(key, hash_data)

    def hget(self, key: str, field: str) -> Optional[Any]:
        """获取哈希字段"""
        hash_data = self._kv_store.get(key)
        if isinstance(hash_data, dict):
            return hash_data.get(field)
        return None

    def hgetall(self, key: str) -> Dict:
        """获取所有哈希字段"""
        hash_data = self._kv_store.get(key)
        return hash_data if isinstance(hash_data, dict) else {}

    def hdel(self, key: str, field: str) -> bool:
        """删除哈希字段"""
        with self._lock:
            hash_data = self._kv_store.get(key)
            if isinstance(hash_data, dict) and field in hash_data:
                del hash_data[field]
                self._kv_store.set(key, hash_data)
                return True
        return False

    # 列表操作(Redis List)
    def lpush(self, key: str, *values):
        """从左侧推入列表"""
        with self._lock:
            list_data = self._kv_store.get(key) or []
            for value in values:
                list_data.insert(0, value)
            self._kv_store.set(key, list_data)

    def rpush(self, key: str, *values):
        """从右侧推入列表"""
        with self._lock:
            list_data = self._kv_store.get(key) or []
            list_data.extend(values)
            self._kv_store.set(key, list_data)

    def lpop(self, key: str) -> Optional[Any]:
        """从左侧弹出"""
        with self._lock:
            list_data = self._kv_store.get(key)
            if isinstance(list_data, list) and list_data:
                value = list_data.pop(0)
                self._kv_store.set(key, list_data)
                return value
        return None

    def rpop(self, key: str) -> Optional[Any]:
        """从右侧弹出"""
        with self._lock:
            list_data = self._kv_store.get(key)
            if isinstance(list_data, list) and list_data:
                value = list_data.pop()
                self._kv_store.set(key, list_data)
                return value
        return None

    def lrange(self, key: str, start: int, end: int) -> List:
        """获取列表范围"""
        list_data = self._kv_store.get(key)
        if isinstance(list_data, list):
            return list_data[start:end+1]
        return []

    # 集合操作(Redis Set)
    def sadd(self, key: str, *values):
        """添加集合成员"""
        with self._lock:
            set_data = self._kv_store.get(key) or set()
            for value in values:
                set_data.add(value)
            self._kv_store.set(key, list(set_data))

    def smembers(self, key: str) -> List:
        """获取集合成员"""
        set_data = self._kv_store.get(key)
        return list(set_data) if isinstance(set_data, list) else []

    def sismember(self, key: str, value: Any) -> bool:
        """检查成员是否在集合中"""
        set_data = self._kv_store.get(key)
        return isinstance(set_data, list) and value in set_data

    def srem(self, key: str, *values) -> int:
        """移除集合成员"""
        with self._lock:
            set_data = self._kv_store.get(key)
            if not isinstance(set_data, list):
                return 0
            
            original_len = len(set_data)
            for value in values:
                if value in set_data:
                    set_data.remove(value)
            self._kv_store.set(key, set_data)
            return original_len - len(set_data)

    # 有序集合操作(Redis ZSet)
    def zadd(self, key: str, *args):
        """添加有序集合成员"""
        with self._lock:
            zset_data = self._kv_store.get(key) or {}
            
            # 参数格式: zadd(key, score1, member1, score2, member2, ...)
            for i in range(0, len(args), 2):
                if i + 1 < len(args):
                    score = float(args[i])
                    member = args[i + 1]
                    zset_data[member] = score
            
            # 按分数排序
            sorted_items = sorted(zset_data.items(), key=lambda x: x[1])
            zset_data = {k: v for k, v in sorted_items}
            
            self._kv_store.set(key, zset_data)

    def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> List:
        """获取有序集合范围"""
        zset_data = self._kv_store.get(key)
        if not isinstance(zset_data, dict):
            return []
        
        items = list(zset_data.items())[start:end+1]
        if withscores:
            return items
        return [item[0] for item in items]

    def zrank(self, key: str, member: Any) -> Optional[int]:
        """获取成员排名"""
        zset_data = self._kv_store.get(key)
        if not isinstance(zset_data, dict):
            return None
        
        members = list(zset_data.keys())
        try:
            return members.index(member)
        except ValueError:
            return None

    def zscore(self, key: str, member: Any) -> Optional[float]:
        """获取成员分数"""
        zset_data = self._kv_store.get(key)
        if isinstance(zset_data, dict):
            return zset_data.get(member)
        return None

    # 事务操作
    def transaction(self, operations: List[Dict]) -> bool:
        """执行事务"""
        try:
            with self._lock:
                for op in operations:
                    op_type = op.get('type')
                    key = op.get('key')
                    value = op.get('value')
                    
                    if op_type == 'set':
                        self._kv_store.set(key, value, op.get('ttl'))
                    elif op_type == 'delete':
                        self._kv_store.delete(key)
                    elif op_type == 'incr':
                        self.incr(key, op.get('amount', 1))
                    elif op_type == 'hset':
                        self.hset(key, op.get('field'), value)
            
            return True
        except Exception as e:
            logger.error(f"事务执行失败: {str(e)}")
            return False

    # 批量操作
    def mget(self, keys: List[str]) -> List[Any]:
        """批量获取"""
        return [self._kv_store.get(key) for key in keys]

    def mset(self, key_value_pairs: List[Tuple[str, Any]]):
        """批量设置"""
        for key, value in key_value_pairs:
            self._kv_store.set(key, value)

    # 持久化
    def save(self, path: str):
        """保存数据到文件"""
        data = {
            'kv_store': {k: v.to_dict() for k, v in self._kv_store._store.items()},
            'collections': self._collection_store
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"NoSQL数据已保存到: {path}")

    def load(self, path: str):
        """从文件加载数据"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载键值存储
            for key, record_data in data.get('kv_store', {}).items():
                self._kv_store.set(key, record_data['value'], record_data.get('ttl'))
            
            # 加载集合
            self._collection_store = data.get('collections', {})
            
            logger.info(f"NoSQL数据已从 {path} 加载")
        except Exception as e:
            logger.error(f"加载NoSQL数据失败: {str(e)}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'db_type': self._db_type.value,
            'kv_keys_count': self._kv_store.size(),
            'collections': list(self._collection_store.keys()),
            'documents_count': {
                coll: len(docs) for coll, docs in self._collection_store.items()
            }
        }


# 创建全局实例
nosql_service = NoSQLService()
