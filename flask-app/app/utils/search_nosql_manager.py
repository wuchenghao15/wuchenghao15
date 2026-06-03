# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎 + NoSQL数据库管理器 - 支持全文搜索、索引管理、文档存储
"""

import os
import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('search_nosql')

class SearchEngineType(Enum):
    """搜索引擎类型"""
    WHOOSH = "whoosh"      # Whoosh全文搜索
    ELASTICSEARCH = "elasticsearch"  # Elasticsearch
    LUNR = "lunr"          # Lunr.js/Python
    
class NoSQLType(Enum):
    """NoSQL数据库类型"""
    MONGODB = "mongodb"    # MongoDB
    REDIS = "redis"        # Redis
    COUCHDB = "couchdb"    # CouchDB
    IN_MEMORY = "in_memory" # 内存存储

class SearchIndex:
    """搜索索引"""
    
    def __init__(self, name: str, fields: List[str]):
        self.name = name
        self.fields = fields
        self.documents = {}
        self.inverted_index = {}
        
        # 初始化倒排索引
        for field in fields:
            self.inverted_index[field] = {}
    
    def add_document(self, doc_id: str, document: Dict):
        """添加文档"""
        self.documents[doc_id] = document
        
        # 更新倒排索引
        for field in self.fields:
            if field in document:
                text = str(document[field]).lower()
                words = self._tokenize(text)
                
                for word in words:
                    if word not in self.inverted_index[field]:
                        self.inverted_index[field][word] = set()
                    self.inverted_index[field][word].add(doc_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        import re
        words = re.findall(r'\w+', text)
        return [word for word in words if len(word) > 1]
    
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """搜索文档"""
        query_words = self._tokenize(query.lower())
        
        if not query_words:
            return []
        
        search_fields = fields or self.fields
        results = {}
        
        for field in search_fields:
            if field not in self.inverted_index:
                continue
            
            for word in query_words:
                if word in self.inverted_index[field]:
                    for doc_id in self.inverted_index[field][word]:
                        if doc_id not in results:
                            results[doc_id] = 0
                        results[doc_id] += 1
        
        # 按得分排序
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    def delete_document(self, doc_id: str):
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            
            # 更新倒排索引
            for field in self.inverted_index:
                for word in list(self.inverted_index[field].keys()):
                    if doc_id in self.inverted_index[field][word]:
                        self.inverted_index[field][word].remove(doc_id)
                        if not self.inverted_index[field][word]:
                            del self.inverted_index[field][word]
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取文档"""
        return self.documents.get(doc_id)

class SearchEngineManager:
    """搜索引擎管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.engine_type = SearchEngineType(self.config.get('engine_type', 'whoosh'))
        self.indexes = {}
        
        # 初始化默认索引
        self._init_default_indexes()
        
        logger.info(f"搜索引擎管理器初始化完成,类型: {self.engine_type.value}")
    
    def _default_config(self) -> Dict:
        return {
            'engine_type': 'whoosh',
            'index_dir': '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/search/indexes',
            'max_results': 100,
            'min_word_length': 2,
            'enable_stemming': True,
            'enable_synonyms': True
        }
    
    def _init_default_indexes(self):
        """初始化默认索引"""
        # 文档索引
        self.create_index('documents', ['title', 'content', 'tags', 'author'])
        
        # 用户索引
        self.create_index('users', ['username', 'email', 'name'])
        
        # 题库索引
        self.create_index('questions', ['question', 'answer', 'category', 'tags'])
        
        # 日志索引
        self.create_index('logs', ['message', 'level'])
    
    def create_index(self, name: str, fields: List[str]):
        """创建索引"""
        if name not in self.indexes:
            self.indexes[name] = SearchIndex(name, fields)
            logger.info(f"创建索引: {name}, 字段: {fields}")
    
    def add_document(self, index_name: str, doc_id: str, document: Dict):
        """添加文档到索引"""
        if index_name in self.indexes:
            self.indexes[index_name].add_document(doc_id, document)
        else:
            logger.error(f"索引不存在: {index_name}")
    
    def search(self, index_name: str, query: str, 
               fields: Optional[List[str]] = None) -> List[Dict]:
        """搜索"""
        if index_name not in self.indexes:
            return []
        
        results = self.indexes[index_name].search(query, fields)
        
        # 获取完整文档
        index = self.indexes[index_name]
        return [index.get_document(doc_id) for doc_id, _ in results]
    
    def delete_document(self, index_name: str, doc_id: str):
        """删除文档"""
        if index_name in self.indexes:
            self.indexes[index_name].delete_document(doc_id)
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict]:
        """获取文档"""
        if index_name in self.indexes:
            return self.indexes[index_name].get_document(doc_id)
        return None
    
    def get_index_stats(self, index_name: str) -> Dict:
        """获取索引统计"""
        if index_name not in self.indexes:
            return {}
        
        index = self.indexes[index_name]
        return {
            'name': index.name,
            'fields': index.fields,
            'document_count': len(index.documents),
            'unique_words': sum(len(field_index) for field_index in index.inverted_index.values())
        }
    
    def get_all_indexes(self) -> List[str]:
        """获取所有索引名称"""
        return list(self.indexes.keys())

class NoSQLManager:
    """NoSQL数据库管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.db_type = NoSQLType(self.config.get('db_type', 'in_memory'))
        
        # 内存存储
        self.collections = {}
        
        # MongoDB连接(如果可用)
        self.mongo_client = None
        
        logger.info(f"NoSQL管理器初始化完成,类型: {self.db_type.value}")
    
    def _default_config(self) -> Dict:
        return {
            'db_type': 'in_memory',
            'mongodb_uri': 'mongodb://localhost:27017/',
            'mongodb_db': 'mtscos',
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'couchdb_url': 'http://localhost:5984/',
            'couchdb_db': 'mtscos'
        }
    
    def _ensure_collection(self, collection_name: str):
        """确保集合存在"""
        if collection_name not in self.collections:
            self.collections[collection_name] = {}
    
    def insert(self, collection_name: str, document: Dict) -> str:
        """插入文档"""
        self._ensure_collection(collection_name)
        
        doc_id = document.get('_id') or self._generate_id()
        document['_id'] = doc_id
        document['created_at'] = time.time()
        document['updated_at'] = time.time()
        
        self.collections[collection_name][doc_id] = document
        return doc_id
    
    def _generate_id(self) -> str:
        """生成文档ID"""
        return hashlib.md5(f"{time.time()}-{os.urandom(8).hex()}".encode()).hexdigest()
    
    def find(self, collection_name: str, query: Dict = None) -> List[Dict]:
        """查询文档"""
        if collection_name not in self.collections:
            return []
        
        query = query or {}
        results = []
        
        for doc_id, document in self.collections[collection_name].items():
            match = True
            for key, value in query.items():
                if document.get(key) != value:
                    match = False
                    break
            if match:
                results.append(document)
        
        return results
    
    def find_one(self, collection_name: str, query: Dict) -> Optional[Dict]:
        """查询单个文档"""
        results = self.find(collection_name, query)
        return results[0] if results else None
    
    def update(self, collection_name: str, query: Dict, update: Dict) -> int:
        """更新文档"""
        if collection_name not in self.collections:
            return 0
        
        updated_count = 0
        
        for doc_id, document in self.collections[collection_name].items():
            match = True
            for key, value in query.items():
                if document.get(key) != value:
                    match = False
                    break
            
            if match:
                document.update(update)
                document['updated_at'] = time.time()
                updated_count += 1
        
        return updated_count
    
    def delete(self, collection_name: str, query: Dict) -> int:
        """删除文档"""
        if collection_name not in self.collections:
            return 0
        
        to_delete = []
        for doc_id, document in self.collections[collection_name].items():
            match = True
            for key, value in query.items():
                if document.get(key) != value:
                    match = False
                    break
            if match:
                to_delete.append(doc_id)
        
        for doc_id in to_delete:
            del self.collections[collection_name][doc_id]
        
        return len(to_delete)
    
    def count(self, collection_name: str, query: Dict = None) -> int:
        """统计文档数量"""
        results = self.find(collection_name, query)
        return len(results)
    
    def get_collection_names(self) -> List[str]:
        """获取所有集合名称"""
        return list(self.collections.keys())
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """获取集合统计"""
        if collection_name not in self.collections:
            return {}
        
        return {
            'name': collection_name,
            'document_count': len(self.collections[collection_name]),
            'first_created': min(
                [doc['created_at'] for doc in self.collections[collection_name].values()],
                default=None
            ),
            'last_updated': max(
                [doc['updated_at'] for doc in self.collections[collection_name].values()],
                default=None
            )
        }

# 全局实例
search_engine = SearchEngineManager()
nosql_manager = NoSQLManager()

def get_search_engine() -> SearchEngineManager:
    """获取搜索引擎实例"""
    return search_engine

def get_nosql_manager() -> NoSQLManager:
    """获取NoSQL管理器实例"""
    return nosql_manager

# 便捷函数
def search_index(index_name: str, query: str, fields: Optional[List[str]] = None):
    """搜索索引"""
    return search_engine.search(index_name, query, fields)

def search_add_document(index_name: str, doc_id: str, document: Dict):
    """添加文档到索引"""
    search_engine.add_document(index_name, doc_id, document)

def nosql_insert(collection_name: str, document: Dict) -> str:
    """插入文档"""
    return nosql_manager.insert(collection_name, document)

def nosql_find(collection_name: str, query: Dict = None) -> List[Dict]:
    """查询文档"""
    return nosql_manager.find(collection_name, query)

def nosql_find_one(collection_name: str, query: Dict) -> Optional[Dict]:
    """查询单个文档"""
    return nosql_manager.find_one(collection_name, query)

def nosql_update(collection_name: str, query: Dict, update: Dict) -> int:
    """更新文档"""
    return nosql_manager.update(collection_name, query, update)

def nosql_delete(collection_name: str, query: Dict) -> int:
    """删除文档"""
    return nosql_manager.delete(collection_name, query)

if __name__ == '__main__':
    # 测试搜索引擎
    print("🚀 搜索引擎 + NoSQL测试")
    print("=" * 70)
    
    # 测试1: 搜索引擎
    print("\n📝 测试1: 搜索引擎")
    search_engine.add_document('documents', 'doc1', {
        'title': 'Python入门指南',
        'content': 'Python是一种高级编程语言,非常适合初学者学习.',
        'tags': 'python, programming, beginner',
        'author': 'John'
    })
    
    search_engine.add_document('documents', 'doc2', {
        'title': 'Java编程教程',
        'content': 'Java是一种跨平台的编程语言,广泛用于企业开发.',
        'tags': 'java, programming, enterprise',
        'author': 'Jane'
    })
    
    results = search_engine.search('documents', '编程')
    print(f"  搜索'编程'找到 {len(results)} 条结果")
    for r in results:
        print(f"    - {r['title']}")
    
    # 测试2: NoSQL数据库
    print("\n📝 测试2: NoSQL数据库")
    doc_id = nosql_manager.insert('articles', {
        'title': '机器学习入门',
        'content': '机器学习是人工智能的一个分支...',
        'category': 'AI',
        'views': 1000
    })
    print(f"  插入文档ID: {doc_id}")
    
    found = nosql_manager.find_one('articles', {'title': '机器学习入门'})
    print(f"  查询结果: {'找到' if found else '未找到'}")
    
    # 测试3: 综合测试
    print("\n📝 测试3: 综合测试")
    # 将NoSQL文档添加到搜索索引
    if found:
        search_engine.add_document('documents', found['_id'], {
            'title': found['title'],
            'content': found['content'],
            'tags': found['category'],
            'author': 'System'
        })
        
        results = search_engine.search('documents', '机器学习')
        print(f"  搜索'机器学习'找到 {len(results)} 条结果")
    
    print("\n🎉 测试完成!")
