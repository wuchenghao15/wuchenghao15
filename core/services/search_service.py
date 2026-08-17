#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS搜索服务
提供全文搜索和索引功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class SearchIndex:
    """搜索索引"""
    
    def __init__(self, index_name: str, fields: List[str], analyzer: str = 'simple'):
        self.index_name = index_name
        self.fields = fields
        self.analyzer = analyzer
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, List[str]] = {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'index_name': self.index_name,
            'fields': self.fields,
            'analyzer': self.analyzer,
            'document_count': len(self.documents),
            'created_at': self.created_at
        }

class SearchService:
    """搜索服务"""
    
    def __init__(self):
        self.indices: Dict[str, SearchIndex] = {}
        self.is_running = False
        self.index_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'search_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'index_interval': 60,
            'max_results': 100,
            'min_query_length': 2,
            'enable_stemming': True,
            'enable_fuzzy_search': True,
            'fuzzy_distance': 2
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'search_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_indices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL UNIQUE,
                    fields TEXT,
                    analyzer TEXT DEFAULT 'simple',
                    document_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    index_name TEXT,
                    results_count INTEGER DEFAULT 0,
                    duration REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_indices_name ON search_indices(index_name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_search_docs_index ON search_documents(index_name)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 初始化数据库失败: {e}")
    
    def create_index(self, index_name: str, fields: List[str], analyzer: str = 'simple') -> bool:
        """创建索引"""
        if index_name in self.indices:
            logger(f"[搜索] 索引已存在: {index_name}")
            return False
        
        index = SearchIndex(index_name, fields, analyzer)
        
        with self.lock:
            self.indices[index_name] = index
        
        self._save_index_to_db(index)
        logger(f"[搜索] 创建索引: {index_name}")
        
        return True
    
    def _save_index_to_db(self, index: SearchIndex):
        """保存索引到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_indices 
                (index_name, fields, analyzer, document_count, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                index.index_name,
                json.dumps(index.fields),
                index.analyzer,
                len(index.documents),
                index.created_at
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 保存索引失败: {e}")
    
    def delete_index(self, index_name: str) -> bool:
        """删除索引"""
        with self.lock:
            if index_name not in self.indices:
                logger(f"[搜索] 索引不存在: {index_name}")
                return False
            
            del self.indices[index_name]
        
        self._delete_index_from_db(index_name)
        logger(f"[搜索] 删除索引: {index_name}")
        
        return True
    
    def _delete_index_from_db(self, index_name: str):
        """从数据库删除索引"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM search_indices WHERE index_name = ?', (index_name,))
            cursor.execute('DELETE FROM search_documents WHERE index_name = ?', (index_name,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 删除索引失败: {e}")
    
    def add_document(self, index_name: str, document_id: str, content: Dict[str, Any],
                     metadata: Dict[str, Any] = None):
        """添加文档"""
        with self.lock:
            if index_name not in self.indices:
                logger(f"[搜索] 索引不存在: {index_name}")
                return False
            
            index = self.indices[index_name]
            
            document = {
                'document_id': document_id,
                'content': content,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat()
            }
            
            index.documents[document_id] = document
            self._update_inverted_index(index, document_id, content)
        
        self._save_document_to_db(index_name, document_id, content, metadata)
        logger(f"[搜索] 添加文档: {document_id}")
        
        return True
    
    def _update_inverted_index(self, index: SearchIndex, document_id: str, content: Dict[str, Any]):
        """更新倒排索引"""
        text = ' '.join(str(content.get(field, '')) for field in index.fields)
        tokens = self._tokenize(text)
        
        for token in tokens:
            if token not in index.inverted_index:
                index.inverted_index[token] = []
            
            if document_id not in index.inverted_index[token]:
                index.inverted_index[token].append(document_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', ' ', text)
        tokens = text.split()
        
        if self.config['enable_stemming']:
            tokens = [self._stem(token) for token in tokens]
        
        return tokens
    
    def _stem(self, word: str) -> str:
        """词干提取"""
        suffixes = ['ing', 'ed', 'ly', 'ness', 'tion', 's', 'es']
        
        for suffix in suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)]
        
        return word
    
    def _save_document_to_db(self, index_name: str, document_id: str, content: Dict[str, Any],
                             metadata: Dict[str, Any]):
        """保存文档到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO search_documents 
                (index_name, document_id, content, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                index_name, document_id,
                json.dumps(content),
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 保存文档失败: {e}")
    
    def delete_document(self, index_name: str, document_id: str) -> bool:
        """删除文档"""
        with self.lock:
            if index_name not in self.indices:
                return False
            
            index = self.indices[index_name]
            
            if document_id not in index.documents:
                return False
            
            del index.documents[document_id]
            
            for token, doc_ids in list(index.inverted_index.items()):
                if document_id in doc_ids:
                    doc_ids.remove(document_id)
                    if not doc_ids:
                        del index.inverted_index[token]
        
        self._delete_document_from_db(index_name, document_id)
        logger(f"[搜索] 删除文档: {document_id}")
        
        return True
    
    def _delete_document_from_db(self, index_name: str, document_id: str):
        """从数据库删除文档"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM search_documents WHERE index_name = ? AND document_id = ?',
                          (index_name, document_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 删除文档失败: {e}")
    
    def search(self, query: str, index_name: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索"""
        if len(query) < self.config['min_query_length']:
            return []
        
        start_time = time.time()
        results = []
        
        tokens = self._tokenize(query)
        
        if index_name:
            indices_to_search = [index_name]
        else:
            indices_to_search = list(self.indices.keys())
        
        with self.lock:
            for idx_name in indices_to_search:
                if idx_name not in self.indices:
                    continue
                
                index = self.indices[idx_name]
                matched_docs = set()
                
                for token in tokens:
                    if token in index.inverted_index:
                        matched_docs.update(index.inverted_index[token])
                    
                    if self.config['enable_fuzzy_search']:
                        for idx_token in index.inverted_index:
                            if self._levenshtein_distance(token, idx_token) <= self.config['fuzzy_distance']:
                                matched_docs.update(index.inverted_index[idx_token])
                
                for doc_id in matched_docs:
                    if doc_id in index.documents:
                        doc = index.documents[doc_id]
                        score = self._calculate_score(doc, tokens)
                        
                        results.append({
                            'document_id': doc_id,
                            'index_name': idx_name,
                            'content': doc['content'],
                            'metadata': doc['metadata'],
                            'score': score
                        })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        duration = time.time() - start_time
        self._log_query(query, index_name, len(results), duration)
        
        return results[:limit]
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_score(self, doc: Dict[str, Any], tokens: List[str]) -> float:
        """计算得分"""
        text = ' '.join(str(doc['content'].get(field, '')) for field in ['title', 'content', 'description'])
        score = 0
        
        for token in tokens:
            score += text.count(token) * 10
            if token in text[:100]:
                score += 5
        
        return score
    
    def _log_query(self, query: str, index_name: str, results_count: int, duration: float):
        """记录查询"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_queries (query, index_name, results_count, duration)
                VALUES (?, ?, ?, ?)
            ''', (query, index_name, results_count, duration))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[搜索] 记录查询失败: {e}")
    
    def get_index(self, index_name: str) -> Optional[SearchIndex]:
        """获取索引"""
        return self.indices.get(index_name)
    
    def get_indices(self) -> List[SearchIndex]:
        """获取所有索引"""
        with self.lock:
            return list(self.indices.values())
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """获取索引统计"""
        with self.lock:
            index = self.indices.get(index_name)
            
            if not index:
                return {'error': '索引不存在'}
            
            return {
                'index_name': index.index_name,
                'fields': index.fields,
                'analyzer': index.analyzer,
                'document_count': len(index.documents),
                'term_count': len(index.inverted_index),
                'created_at': index.created_at
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            total_docs = sum(len(idx.documents) for idx in self.indices.values())
            total_terms = sum(len(idx.inverted_index) for idx in self.indices.values())
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_indices': len(self.indices),
                'total_documents': total_docs,
                'total_terms': total_terms,
                'min_query_length': self.config['min_query_length'],
                'enable_fuzzy_search': self.config['enable_fuzzy_search'],
                'fuzzy_distance': self.config['fuzzy_distance']
            }
    
    def start(self):
        """启动搜索服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[搜索] 搜索服务已启动")
    
    def stop(self):
        """停止搜索服务"""
        self.is_running = False
        logger(f"[搜索] 搜索服务已停止")

search_service = SearchService()
