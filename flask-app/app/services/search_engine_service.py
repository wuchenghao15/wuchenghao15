# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎服务 - 实现全文搜索和倒排索引
"""

import os
import re
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import math

from app.utils.logging import logger
import logging


class SearchEngineType(Enum):
    """搜索引擎类型"""
    LOCAL = "local"
    ELASTICSEARCH = "elasticsearch"
    MEILISEARCH = "meilisearch"
    TYPESENSE = "typesense"


class QueryType(Enum):
    """查询类型"""
    FULLTEXT = "fulltext"
    PHRASE = "phrase"
    BOOLEAN = "boolean"
    FUZZY = "fuzzy"


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    title: str
    content: str
    score: float
    highlight: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content,
            'score': self.score,
            'highlight': self.highlight,
            'metadata': self.metadata
        }


@dataclass
class Document:
    """文档"""
    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())


class InvertedIndex:
    """倒排索引"""
    
    def __init__(self):
        self._index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        self._documents: Dict[str, Document] = {}
        self._doc_lengths: Dict[str, int] = {}
        self._total_docs = 0
        self._avg_doc_length = 0.0
        self._lock = threading.RLock()

    def add_document(self, doc: Document):
        """添加文档到索引"""
        with self._lock:
            # 分词
            tokens = self._tokenize(doc.content + " " + doc.title)
            
            # 更新文档
            self._documents[doc.doc_id] = doc
            self._doc_lengths[doc.doc_id] = len(tokens)
            self._total_docs += 1
            
            # 更新倒排索引
            token_positions = defaultdict(list)
            for idx, token in enumerate(tokens):
                token_positions[token].append(idx)
            
            for token, positions in token_positions.items():
                self._index[token].append((doc.doc_id, len(positions)))
            
            # 更新平均文档长度
            self._avg_doc_length = sum(self._doc_lengths.values()) / self._total_docs

    def remove_document(self, doc_id: str):
        """从索引中移除文档"""
        with self._lock:
            if doc_id not in self._documents:
                return
            
            doc = self._documents[doc_id]
            tokens = self._tokenize(doc.content + " " + doc.title)
            
            # 从倒排索引中移除
            for token in set(tokens):
                self._index[token] = [(did, cnt) for did, cnt in self._index[token] if did != doc_id]
            
            # 更新文档统计
            del self._documents[doc_id]
            del self._doc_lengths[doc_id]
            self._total_docs -= 1
            
            if self._total_docs > 0:
                self._avg_doc_length = sum(self._doc_lengths.values()) / self._total_docs
            else:
                self._avg_doc_length = 0.0

    def _tokenize(self, text: str) -> List[str]:
        """分词处理"""
        text = text.lower()
        tokens = re.findall(r'[a-zA-Z\u4e00-\u9fff]+', text)
        return [t for t in tokens if len(t) > 1]

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """搜索文档"""
        tokens = self._tokenize(query)
        if not tokens:
            return []
        
        with self._lock:
            # 计算每个文档的分数
            scores: Dict[str, float] = defaultdict(float)
            
            for token in tokens:
                if token not in self._index:
                    continue
                
                # IDF计算
                doc_freq = len(self._index[token])
                idf = math.log(self._total_docs / (doc_freq + 1))
                
                for doc_id, term_freq in self._index[token]:
                    # TF计算
                    tf = term_freq / self._doc_lengths[doc_id]
                    
                    # BM25评分
                    k1 = 1.5
                    b = 0.75
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * self._doc_lengths[doc_id] / self._avg_doc_length)
                    
                    scores[doc_id] += idf * (numerator / denominator)
            
            # 排序并返回
            results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
            return results

    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        with self._lock:
            return self._documents.get(doc_id)

    def get_documents(self) -> List[Document]:
        """获取所有文档"""
        with self._lock:
            return list(self._documents.values())


class SearchEngineService:
    """搜索引擎服务"""

    def __init__(self):
        self._engine_type = SearchEngineType.LOCAL
        self._inverted_index = InvertedIndex()
        self._lock = threading.RLock()
        self._index_path = os.path.join(os.path.dirname(__file__), '..', '..', 'search_index')
        os.makedirs(self._index_path, exist_ok=True)
        logger.info("搜索引擎服务初始化完成")

    def set_engine_type(self, engine_type: SearchEngineType):
        """设置搜索引擎类型"""
        self._engine_type = engine_type
        logger.info(f"搜索引擎类型已设置为: {engine_type.value}")

    def get_engine_type(self) -> SearchEngineType:
        """获取搜索引擎类型"""
        return self._engine_type

    def index_document(self, doc_id: str, title: str, content: str, metadata: Optional[Dict] = None):
        """索引文档"""
        doc = Document(
            doc_id=doc_id,
            title=title,
            content=content,
            metadata=metadata or {}
        )
        self._inverted_index.add_document(doc)
        logger.info(f"文档已索引: {doc_id}")

    def delete_document(self, doc_id: str):
        """删除索引文档"""
        self._inverted_index.remove_document(doc_id)
        logger.info(f"文档已删除: {doc_id}")

    def search(self, query: str, limit: int = 10, query_type: QueryType = QueryType.FULLTEXT) -> List[SearchResult]:
        """搜索文档"""
        results = []
        
        if self._engine_type == SearchEngineType.LOCAL:
            # 使用本地倒排索引
            doc_scores = self._inverted_index.search(query, limit)
            
            for doc_id, score in doc_scores:
                doc = self._inverted_index.get_document(doc_id)
                if doc:
                    highlight = self._highlight(doc.content, query)
                    results.append(SearchResult(
                        doc_id=doc.doc_id,
                        title=doc.title,
                        content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        score=round(score, 4),
                        highlight=highlight,
                        metadata=doc.metadata
                    ))
        else:
            # 外部搜索引擎(简化实现)
            logger.warning(f"未实现 {self._engine_type.value} 搜索引擎")
        
        return results

    def _highlight(self, content: str, query: str) -> Optional[str]:
        """生成高亮摘要"""
        tokens = self._inverted_index._tokenize(query)
        if not tokens:
            return None
        
        # 找到包含任意查询词的片段
        window_size = 50
        content_lower = content.lower()
        
        for token in tokens:
            idx = content_lower.find(token)
            if idx != -1:
                start = max(0, idx - window_size)
                end = min(len(content), idx + len(token) + window_size)
                snippet = content[start:end]
                # 高亮匹配的词
                for t in tokens:
                    snippet = re.sub(f'({t})', r'<em>\1</em>', snippet, flags=re.IGNORECASE)
                return "..." + snippet + "..."
        
        return None

    def search_with_filters(self, query: str, filters: Dict, limit: int = 10) -> List[SearchResult]:
        """带过滤条件的搜索"""
        results = self.search(query, limit * 2)
        
        # 应用过滤条件
        filtered = []
        for result in results:
            match = True
            for key, value in filters.items():
                if result.metadata.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(result)
        
        return filtered[:limit]

    def get_document(self, doc_id: str) -> Optional[SearchResult]:
        """获取单个文档"""
        doc = self._inverted_index.get_document(doc_id)
        if doc:
            return SearchResult(
                doc_id=doc.doc_id,
                title=doc.title,
                content=doc.content,
                score=1.0,
                metadata=doc.metadata
            )
        return None

    def update_document(self, doc_id: str, title: Optional[str] = None, 
                       content: Optional[str] = None, metadata: Optional[Dict] = None):
        """更新文档"""
        doc = self._inverted_index.get_document(doc_id)
        if not doc:
            logger.warning(f"文档不存在: {doc_id}")
            return
        
        # 删除旧文档
        self._inverted_index.remove_document(doc_id)
        
        # 创建新文档
        new_doc = Document(
            doc_id=doc_id,
            title=title or doc.title,
            content=content or doc.content,
            metadata=metadata or doc.metadata
        )
        self._inverted_index.add_document(new_doc)
        logger.info(f"文档已更新: {doc_id}")

    def get_stats(self) -> Dict:
        """获取搜索引擎统计"""
        docs = self._inverted_index.get_documents()
        return {
            'engine_type': self._engine_type.value,
            'total_documents': len(docs),
            'total_tokens': sum(len(self._inverted_index._tokenize(d.content + " " + d.title)) for d in docs)
        }

    def save_index(self, path: Optional[str] = None):
        """保存索引到文件"""
        save_path = path or os.path.join(self._index_path, 'index.json')
        
        index_data = {
            'documents': {doc_id: {
                'title': doc.title,
                'content': doc.content,
                'metadata': doc.metadata,
                'created_at': doc.created_at
            } for doc_id, doc in self._inverted_index._documents.items()},
            'index': {token: [(did, cnt) for did, cnt in postings] 
                     for token, postings in self._inverted_index._index.items()}
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False)
        
        logger.info(f"索引已保存到: {save_path}")

    def load_index(self, path: Optional[str] = None):
        """从文件加载索引"""
        load_path = path or os.path.join(self._index_path, 'index.json')
        
        if not os.path.exists(load_path):
            logger.warning(f"索引文件不存在: {load_path}")
            return
        
        with open(load_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # 加载文档
        for doc_id, data in index_data.get('documents', {}).items():
            doc = Document(
                doc_id=doc_id,
                title=data['title'],
                content=data['content'],
                metadata=data.get('metadata', {}),
                created_at=data.get('created_at', time.time())
            )
            self._inverted_index.add_document(doc)
        
        logger.info(f"索引已从 {load_path} 加载")


# 创建全局实例
search_engine_service = SearchEngineService()
