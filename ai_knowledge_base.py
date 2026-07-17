#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI知识库服务
提供向量检索、语义搜索和文档索引功能
"""

import os
import sys
import json
import time
import hashlib
import math
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

logger = print


def simple_hash_embedding(text: str, dim: int = 128) -> List[float]:
    """简易哈希向量嵌入（无需外部依赖）"""
    vec = [0.0] * dim

    # 字符级哈希
    for i, char in enumerate(text):
        idx = hash(char + str(i)) % dim
        vec[idx] += 1.0

    # 词级哈希
    words = text.split()
    for word in words:
        idx = hash(word) % dim
        vec[idx] += 2.0

    # 归一化
    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude > 0:
        vec = [v / magnitude for v in vec]

    return vec


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """余弦相似度"""
    if len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot / (mag1 * mag2)


class KnowledgeDocument:
    """知识文档"""

    def __init__(self, doc_id: str, title: str, content: str,
                 source: str = '', category: str = 'general',
                 tags: List[str] = None, metadata: Dict[str, Any] = None):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.source = source
        self.category = category
        self.tags = tags or []
        self.metadata = metadata or {}
        self.embedding: List[float] = []
        self.chunks: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.access_count = 0
        self.relevance_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'source': self.source,
            'category': self.category,
            'tags': self.tags,
            'metadata': self.metadata,
            'chunk_count': len(self.chunks),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'access_count': self.access_count,
            'relevance_score': round(self.relevance_score, 4)
        }


class AIKnowledgeBase:
    """AI知识库服务"""

    def __init__(self, embedding_dim: int = 128, chunk_size: int = 500,
                 chunk_overlap: int = 50):
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.embedding_dim = embedding_dim
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_knowledge()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_knowledge_docs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    category TEXT DEFAULT 'general',
                    tags TEXT,
                    metadata TEXT,
                    embedding TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_knowledge_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT NOT NULL UNIQUE,
                    doc_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    chunk_index INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_knowledge_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    matched_docs TEXT,
                    top_score REAL DEFAULT 0,
                    result_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_knowledge_docs_category ON ai_knowledge_docs(category)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc ON ai_knowledge_chunks(doc_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI知识库] 初始化数据库失败: {e}")

    def _register_default_knowledge(self):
        """注册默认知识"""
        defaults = [
            KnowledgeDocument(
                'kb_system_intro', 'MTSCOS系统介绍',
                'MTSCOS是一个企业级AI智能管理系统，提供用户管理、考试系统、智能助手、系统监控等功能。'
                '系统采用Flask框架开发，支持多租户、微服务架构。',
                'system', 'system'
            ),
            KnowledgeDocument(
                'kb_api_guide', 'API使用指南',
                'MTSCOS提供RESTful API接口，所有API支持JSON格式。认证使用JWT Token。'
                '主要API包括：用户管理、考试系统、文件管理、系统监控、AI助手等。',
                'system', 'api'
            ),
            KnowledgeDocument(
                'kb_security', '安全策略',
                'MTSCOS安全策略包括：JWT认证、角色权限控制、API限流、IP黑名单、'
                '断路器保护、数据加密存储、审计日志等。',
                'system', 'security'
            ),
            KnowledgeDocument(
                'kb_deployment', '部署指南',
                'MTSCOS支持本地部署和Docker部署。数据库使用SQLite或MySQL。'
                '生产环境建议使用Nginx反向代理，配置HTTPS。',
                'system', 'deployment'
            ),
            KnowledgeDocument(
                'kb_ai_features', 'AI功能说明',
                'MTSCOS AI功能包括：脑库投喂引擎、自动修复引擎、架构工程师、'
                'AI模型管理、AI对话服务、AI知识库、AI推理流水线等。',
                'system', 'ai'
            ),
        ]

        for doc in defaults:
            if doc.doc_id not in self.documents:
                self._index_document(doc)
                self._save_document_to_db(doc)

    def _chunk_text(self, text: str) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks

    def _index_document(self, doc: KnowledgeDocument):
        """索引文档"""
        doc.embedding = simple_hash_embedding(doc.title + ' ' + doc.content, self.embedding_dim)

        chunks = self._chunk_text(doc.content)
        doc.chunks = []

        for i, chunk in enumerate(chunks):
            chunk_embedding = simple_hash_embedding(chunk, self.embedding_dim)
            chunk_data = {
                'chunk_id': f"{doc.doc_id}_chunk_{i}",
                'content': chunk,
                'embedding': chunk_embedding,
                'chunk_index': i
            }
            doc.chunks.append(chunk_data)

    def _save_document_to_db(self, doc: KnowledgeDocument):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_knowledge_docs
                (doc_id, title, content, source, category, tags, metadata,
                 embedding, chunk_count, access_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doc.doc_id, doc.title, doc.content, doc.source,
                doc.category, json.dumps(doc.tags), json.dumps(doc.metadata),
                json.dumps(doc.embedding), len(doc.chunks),
                doc.access_count, doc.updated_at
            ))

            # 保存分块
            for chunk in doc.chunks:
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_knowledge_chunks
                    (chunk_id, doc_id, content, embedding, chunk_index)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    chunk['chunk_id'], doc.doc_id, chunk['content'],
                    json.dumps(chunk['embedding']), chunk['chunk_index']
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI知识库] 保存文档失败: {e}")

    def add_document(self, title: str, content: str, source: str = '',
                     category: str = 'general', tags: List[str] = None,
                     metadata: Dict[str, Any] = None) -> str:
        """添加文档"""
        import uuid
        doc_id = f"kb_{uuid.uuid4().hex[:12]}"

        doc = KnowledgeDocument(
            doc_id=doc_id, title=title, content=content,
            source=source, category=category,
            tags=tags or [], metadata=metadata or {}
        )

        self._index_document(doc)

        with self.lock:
            self.documents[doc_id] = doc

        self._save_document_to_db(doc)
        logger(f"[AI知识库] 添加文档: {title} ({len(doc.chunks)} chunks)")

        return doc_id

    def search(self, query: str, top_k: int = 5,
               category: str = None,
               min_score: float = 0.1) -> List[Dict[str, Any]]:
        """语义搜索"""
        query_embedding = simple_hash_embedding(query, self.embedding_dim)

        results = []

        with self.lock:
            for doc in self.documents.values():
                if category and doc.category != category:
                    continue

                # 文档级相似度
                doc_score = cosine_similarity(query_embedding, doc.embedding)

                # 分块级相似度（取最高分）
                best_chunk_score = 0.0
                best_chunk = None

                for chunk in doc.chunks:
                    chunk_score = cosine_similarity(query_embedding, chunk['embedding'])
                    if chunk_score > best_chunk_score:
                        best_chunk_score = chunk_score
                        best_chunk = chunk

                # 综合分数
                final_score = max(doc_score, best_chunk_score * 0.8)

                if final_score >= min_score:
                    doc.relevance_score = final_score
                    doc.access_count += 1
                    results.append({
                        'doc_id': doc.doc_id,
                        'title': doc.title,
                        'content': best_chunk['content'] if best_chunk else doc.content[:200],
                        'category': doc.category,
                        'tags': doc.tags,
                        'score': round(final_score, 4),
                        'source': doc.source
                    })

        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:top_k]

        self._log_query(query, results)

        return results

    def _log_query(self, query: str, results: List[Dict[str, Any]]):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            top_score = results[0]['score'] if results else 0
            matched = [r['doc_id'] for r in results]

            cursor.execute('''
                INSERT INTO ai_knowledge_queries
                (query_text, matched_docs, top_score, result_count)
                VALUES (?, ?, ?, ?)
            ''', (query, json.dumps(matched), top_score, len(results)))

            conn.commit()
            conn.close()
        except:
            pass

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        return self.documents.get(doc_id)

    def update_document(self, doc_id: str, title: str = None,
                        content: str = None, category: str = None,
                        tags: List[str] = None) -> bool:
        """更新文档"""
        with self.lock:
            doc = self.documents.get(doc_id)
            if not doc:
                return False

            if title:
                doc.title = title
            if content:
                doc.content = content
                self._index_document(doc)
            if category:
                doc.category = category
            if tags is not None:
                doc.tags = tags

            doc.updated_at = datetime.now().isoformat()

        self._save_document_to_db(doc)
        return True

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        with self.lock:
            if doc_id not in self.documents:
                return False
            del self.documents[doc_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ai_knowledge_docs WHERE doc_id = ?', (doc_id,))
            cursor.execute('DELETE FROM ai_knowledge_chunks WHERE doc_id = ?', (doc_id,))
            conn.commit()
            conn.close()
        except:
            pass

        return True

    def get_documents(self, category: str = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        with self.lock:
            docs = list(self.documents.values())

            if category:
                docs = [d for d in docs if d.category == category]

            return [d.to_dict() for d in docs[:limit]]

    def get_categories(self) -> List[Dict[str, Any]]:
        with self.lock:
            cat_counts: Dict[str, int] = {}
            for doc in self.documents.values():
                cat_counts[doc.category] = cat_counts.get(doc.category, 0) + 1

            return [{'category': k, 'count': v} for k, v in sorted(cat_counts.items())]

    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM ai_knowledge_queries
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except:
            return []

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            total_chunks = sum(len(d.chunks) for d in self.documents.values())
            total_access = sum(d.access_count for d in self.documents.values())

            return {
                'total_documents': len(self.documents),
                'total_chunks': total_chunks,
                'total_accesses': total_access,
                'embedding_dim': self.embedding_dim,
                'chunk_size': self.chunk_size,
                'categories': len(self.get_categories())
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_documents': len(self.documents),
            'embedding_dim': self.embedding_dim
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[AI知识库] 知识库服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[AI知识库] 知识库服务已停止")


ai_knowledge_base = AIKnowledgeBase()
