#!/usr/bin/env python3
"""
MTSCOS AI 向量数据库服务 (v14.6.0)
====================================
纯 Python 实现的向量存储与检索服务，支持多种索引结构和相似度算法。

核心能力：
1. 向量存储 - 文档+向量+元数据持久化
2. 索引结构 - 暴力搜索 / LSH / IVF 倒排
3. 相似度算法 - 余弦/欧氏/点积/曼哈顿
4. CRUD 操作 - 增删改查批量操作
5. 元数据过滤 - 标签/分类/范围过滤
6. 集合管理 - 多 collection 独立管理
7. 嵌入服务 - 简单文本嵌入（字符级/词频）
8. 统计监控 - 集合大小/查询延迟/召回率
"""
import os
import json
import math
import sqlite3
import random
import logging
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_vector_store.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIVectorStore')


# ========== 相似度算法 ==========

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """余弦相似度"""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def euclidean_distance(v1: List[float], v2: List[float]) -> float:
    """欧氏距离（转换为相似度：1/(1+d)）"""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    return 1.0 / (1.0 + dist)


def dot_product(v1: List[float], v2: List[float]) -> float:
    """点积相似度"""
    if len(v1) != len(v2) or not v1:
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


def manhattan_distance(v1: List[float], v2: List[float]) -> float:
    """曼哈顿距离（转换为相似度）"""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dist = sum(abs(a - b) for a, b in zip(v1, v2))
    return 1.0 / (1.0 + dist)


SIMILARITY_FUNCTIONS = {
    'cosine': cosine_similarity,
    'euclidean': euclidean_distance,
    'dot': dot_product,
    'manhattan': manhattan_distance,
}


# ========== 文本嵌入 ==========

def text_to_char_vector(text: str, dim: int = 256) -> List[float]:
    """字符级嵌入（基于字符hash映射到向量维度）"""
    vec = [0.0] * dim
    if not text:
        return vec
    for ch in text:
        h = ord(ch) % dim
        vec[h] += 1.0
    # 归一化
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def text_to_word_vector(text: str, vocab: Optional[Dict[str, int]] = None,
                       dim: int = 256) -> List[float]:
    """词频向量嵌入"""
    # 简单分词：中文按字，英文按空格
    tokens = []
    # 英文单词
    en_words = re.findall(r'[a-zA-Z]+', text.lower())
    tokens.extend(en_words)
    # 中文字符
    cn_chars = re.findall(r'[\u4e00-\u9fff]', text)
    tokens.extend(cn_chars)

    vec = [0.0] * dim
    for token in tokens:
        h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % dim
        vec[h] += 1.0
    # 归一化
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def text_to_hash_vector(text: str, dim: int = 256) -> List[float]:
    """哈希嵌入（签名向量）"""
    vec = [0.0] * dim
    if not text:
        return vec
    # 用 n-gram 哈希
    ngrams = []
    for n in [1, 2, 3]:
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i + n])
    for ng in ngrams:
        h = int(hashlib.md5(ng.encode('utf-8')).hexdigest(), 16) % dim
        vec[h] += 1.0 if random.random() > 0.5 else -1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


EMBEDDING_FUNCTIONS = {
    'char': text_to_char_vector,
    'word': text_to_word_vector,
    'hash': text_to_hash_vector,
}


# ========== LSH 索引 ==========

class LSHIndex:
    """局部敏感哈希索引（用于近似最近邻搜索）"""

    def __init__(self, dim: int = 256, num_tables: int = 4, num_bits: int = 8):
        self.dim = dim
        self.num_tables = num_tables
        self.num_bits = num_bits
        # 每个表一组随机投影向量
        self.projections = [
            [[random.uniform(-1, 1) for _ in range(dim)] for _ in range(num_bits)]
            for _ in range(num_tables)
        ]
        self.tables: List[Dict[str, List[str]]] = [{} for _ in range(num_tables)]

    def _hash(self, vec: List[float], table_idx: int) -> str:
        bits = []
        for proj in self.projections[table_idx]:
            dot = sum(a * b for a, b in zip(vec, proj))
            bits.append('1' if dot >= 0 else '0')
        return ''.join(bits)

    def add(self, item_id: str, vec: List[float]):
        for i in range(self.num_tables):
            h = self._hash(vec, i)
            if h not in self.tables[i]:
                self.tables[i][h] = []
            if item_id not in self.tables[i][h]:
                self.tables[i][h].append(item_id)

    def query(self, vec: List[float]) -> List[str]:
        """返回候选 item_id 列表"""
        candidates = set()
        for i in range(self.num_tables):
            h = self._hash(vec, i)
            if h in self.tables[i]:
                candidates.update(self.tables[i][h])
        return list(candidates)

    def remove(self, item_id: str):
        for i in range(self.num_tables):
            for bucket in list(self.tables[i].keys()):
                if item_id in self.tables[i][bucket]:
                    self.tables[i][bucket].remove(item_id)
                    if not self.tables[i][bucket]:
                        del self.tables[i][bucket]

    def to_dict(self) -> Dict:
        return {
            'dim': self.dim,
            'num_tables': self.num_tables,
            'num_bits': self.num_bits,
            'tables': self.tables
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LSHIndex':
        idx = cls(data['dim'], data['num_tables'], data['num_bits'])
        idx.tables = data['tables']
        return idx


# ========== 向量数据库 ==========

class AIVectorStore:
    """AI 向量数据库服务"""

    def __init__(self, default_dim: int = 256, default_metric: str = 'cosine'):
        self.db_path = DATABASE_PATH
        self.default_dim = default_dim
        self.default_metric = default_metric
        self._init_db()
        self._lsh_indexes: Dict[str, LSHIndex] = {}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_vector_collections (
                        collection_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        dim INTEGER NOT NULL,
                        metric TEXT DEFAULT 'cosine',
                        description TEXT,
                        index_type TEXT DEFAULT 'flat',
                        item_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_vector_items (
                        item_id TEXT PRIMARY KEY,
                        collection_id TEXT NOT NULL,
                        vector TEXT NOT NULL,
                        document TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_vector_query_log (
                        log_id TEXT PRIMARY KEY,
                        collection_id TEXT,
                        query_text TEXT,
                        top_k INTEGER,
                        metric TEXT,
                        duration_ms INTEGER,
                        result_count INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vec_items_coll ON ai_vector_items(collection_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vec_query_coll ON ai_vector_query_log(collection_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}")

    # ========== Collection 管理 ==========

    def create_collection(self, name: str, dim: int = None, metric: str = None,
                         description: str = '', index_type: str = 'flat') -> Dict:
        collection_id = f"COL-{name}-{random.randint(1000, 9999)}"
        dim = dim or self.default_dim
        metric = metric or self.default_metric

        if metric not in SIMILARITY_FUNCTIONS:
            return {'success': False, 'error': f'不支持的相似度: {metric}'}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT collection_id FROM ai_vector_collections WHERE name = ?', (name,))
                if cursor.fetchone():
                    return {'success': False, 'error': f'集合 {name} 已存在'}

                cursor.execute('''
                    INSERT INTO ai_vector_collections
                    (collection_id, name, dim, metric, description, index_type, item_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                ''', (collection_id, name, dim, metric, description, index_type,
                      datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()

                # 创建 LSH 索引
                if index_type == 'lsh':
                    self._lsh_indexes[collection_id] = LSHIndex(dim=dim)

                return {'success': True, 'collection_id': collection_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_collection(self, collection_id: str) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM ai_vector_items WHERE collection_id = ?', (collection_id,))
                cursor.execute('DELETE FROM ai_vector_collections WHERE collection_id = ?', (collection_id,))
                conn.commit()
                if collection_id in self._lsh_indexes:
                    del self._lsh_indexes[collection_id]
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_collections(self) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT collection_id, name, dim, metric, description, index_type, item_count, created_at
                    FROM ai_vector_collections
                    ORDER BY created_at DESC
                ''')
                return [
                    {
                        'collection_id': r[0], 'name': r[1], 'dim': r[2], 'metric': r[3],
                        'description': r[4], 'index_type': r[5], 'item_count': r[6], 'created_at': r[7]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_collection(self, collection_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_vector_collections WHERE collection_id = ?', (collection_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'collection_id': row[0], 'name': row[1], 'dim': row[2], 'metric': row[3],
                    'description': row[4], 'index_type': row[5], 'item_count': row[6],
                    'created_at': row[7], 'updated_at': row[8]
                }
        except Exception:
            return None

    def get_collection_by_name(self, name: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_vector_collections WHERE name = ?', (name,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'collection_id': row[0], 'name': row[1], 'dim': row[2], 'metric': row[3],
                    'description': row[4], 'index_type': row[5], 'item_count': row[6],
                    'created_at': row[7], 'updated_at': row[8]
                }
        except Exception:
            return None

    # ========== Item CRUD ==========

    def add(self, collection_id: str, vector: List[float], document: str = '',
            metadata: Optional[Dict] = None, item_id: Optional[str] = None) -> Dict:
        coll = self.get_collection(collection_id)
        if not coll:
            return {'success': False, 'error': '集合不存在'}
        if len(vector) != coll['dim']:
            return {'success': False, 'error': f'向量维度不匹配: 期望 {coll["dim"]}, 实际 {len(vector)}'}

        item_id = item_id or f"ITEM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_vector_items
                    (item_id, collection_id, vector, document, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, collection_id,
                    json.dumps(vector),
                    document,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                # 更新集合计数
                cursor.execute('UPDATE ai_vector_collections SET item_count = item_count + 1, updated_at = ? WHERE collection_id = ?',
                              (datetime.now().isoformat(), collection_id))
                conn.commit()

                # 更新 LSH 索引
                if coll['index_type'] == 'lsh' and collection_id in self._lsh_indexes:
                    self._lsh_indexes[collection_id].add(item_id, vector)

                return {'success': True, 'item_id': item_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_batch(self, collection_id: str, items: List[Dict]) -> Dict:
        """批量添加 items: [{vector, document, metadata, item_id}]"""
        coll = self.get_collection(collection_id)
        if not coll:
            return {'success': False, 'error': '集合不存在'}

        added = 0
        errors = []
        for item in items:
            result = self.add(
                collection_id,
                vector=item.get('vector', []),
                document=item.get('document', ''),
                metadata=item.get('metadata'),
                item_id=item.get('item_id')
            )
            if result.get('success'):
                added += 1
            else:
                errors.append(result.get('error'))

        return {'success': True, 'added': added, 'errors': errors}

    def add_text(self, collection_id: str, text: str, document: str = '',
                metadata: Optional[Dict] = None, embedding: str = 'word',
                item_id: Optional[str] = None) -> Dict:
        """添加文本（自动嵌入）"""
        coll = self.get_collection(collection_id)
        if not coll:
            return {'success': False, 'error': '集合不存在'}

        embed_fn = EMBEDDING_FUNCTIONS.get(embedding)
        if not embed_fn:
            return {'success': False, 'error': f'不支持的嵌入方法: {embedding}'}

        vector = embed_fn(text, dim=coll['dim'])
        return self.add(collection_id, vector, document or text, metadata, item_id)

    def get(self, item_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_vector_items WHERE item_id = ?', (item_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'item_id': row[0], 'collection_id': row[1],
                    'vector': json.loads(row[2]) if row[2] else [],
                    'document': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5], 'updated_at': row[6]
                }
        except Exception:
            return None

    def update(self, item_id: str, vector: Optional[List[float]] = None,
              document: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT collection_id, vector FROM ai_vector_items WHERE item_id = ?', (item_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'item 不存在'}

                coll_id = row[0]
                old_vector = json.loads(row[1]) if row[1] else []

                updates = []
                values = []
                if vector is not None:
                    updates.append('vector = ?')
                    values.append(json.dumps(vector))
                if document is not None:
                    updates.append('document = ?')
                    values.append(document)
                if metadata is not None:
                    updates.append('metadata = ?')
                    values.append(json.dumps(metadata, ensure_ascii=False))
                updates.append('updated_at = ?')
                values.append(datetime.now().isoformat())
                values.append(item_id)

                cursor.execute(f'UPDATE ai_vector_items SET {", ".join(updates)} WHERE item_id = ?', values)
                conn.commit()

                # 更新 LSH 索引
                coll = self.get_collection(coll_id)
                if coll and coll['index_type'] == 'lsh' and coll_id in self._lsh_indexes:
                    self._lsh_indexes[coll_id].remove(item_id)
                    new_vec = vector if vector is not None else old_vector
                    self._lsh_indexes[coll_id].add(item_id, new_vec)

                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete(self, item_id: str) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT collection_id FROM ai_vector_items WHERE item_id = ?', (item_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'item 不存在'}

                coll_id = row[0]
                cursor.execute('DELETE FROM ai_vector_items WHERE item_id = ?', (item_id,))
                cursor.execute('UPDATE ai_vector_collections SET item_count = MAX(item_count - 1, 0) WHERE collection_id = ?',
                              (coll_id,))
                conn.commit()

                coll = self.get_collection(coll_id)
                if coll and coll['index_type'] == 'lsh' and coll_id in self._lsh_indexes:
                    self._lsh_indexes[coll_id].remove(item_id)

                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 查询 ==========

    def search(self, collection_id: str, query_vector: List[float], top_k: int = 10,
              metric: Optional[str] = None, filter_metadata: Optional[Dict] = None) -> Dict:
        """向量相似度搜索"""
        coll = self.get_collection(collection_id)
        if not coll:
            return {'success': False, 'error': '集合不存在'}

        metric = metric or coll['metric']
        sim_fn = SIMILARITY_FUNCTIONS.get(metric)
        if not sim_fn:
            return {'success': False, 'error': f'不支持的相似度: {metric}'}

        start_time = datetime.now()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # LSH 索引加速
                if coll['index_type'] == 'lsh' and collection_id in self._lsh_indexes:
                    candidate_ids = self._lsh_indexes[collection_id].query(query_vector)
                    if candidate_ids:
                        placeholders = ','.join(['?'] * len(candidate_ids))
                        cursor.execute(f'''
                            SELECT item_id, vector, document, metadata
                            FROM ai_vector_items
                            WHERE collection_id = ? AND item_id IN ({placeholders})
                        ''', [collection_id] + candidate_ids)
                    else:
                        cursor.execute('SELECT item_id, vector, document, metadata FROM ai_vector_items WHERE collection_id = ?',
                                     (collection_id,))
                else:
                    cursor.execute('SELECT item_id, vector, document, metadata FROM ai_vector_items WHERE collection_id = ?',
                                 (collection_id,))

                results = []
                for row in cursor.fetchall():
                    item_id, vec_str, document, meta_str = row
                    vec = json.loads(vec_str) if vec_str else []
                    if len(vec) != len(query_vector):
                        continue

                    # 元数据过滤
                    if filter_metadata:
                        meta = json.loads(meta_str) if meta_str else {}
                        if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                            continue

                    score = sim_fn(query_vector, vec)
                    results.append({
                        'item_id': item_id,
                        'score': round(score, 6),
                        'document': document,
                        'metadata': json.loads(meta_str) if meta_str else {}
                    })

                # 排序取 top_k
                results.sort(key=lambda x: x['score'], reverse=True)
                results = results[:top_k]

                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                # 记录查询日志
                log_id = f"VQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
                cursor.execute('''
                    INSERT INTO ai_vector_query_log
                    (log_id, collection_id, query_text, top_k, metric, duration_ms, result_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (log_id, collection_id, '', top_k, metric, duration_ms, len(results),
                      datetime.now().isoformat()))
                conn.commit()

                return {
                    'success': True,
                    'collection_id': collection_id,
                    'metric': metric,
                    'top_k': top_k,
                    'results': results,
                    'total_searched': len(results),
                    'duration_ms': duration_ms
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def search_text(self, collection_id: str, query_text: str, top_k: int = 10,
                   embedding: str = 'word', filter_metadata: Optional[Dict] = None) -> Dict:
        """文本搜索（自动嵌入）"""
        coll = self.get_collection(collection_id)
        if not coll:
            return {'success': False, 'error': '集合不存在'}

        embed_fn = EMBEDDING_FUNCTIONS.get(embedding)
        if not embed_fn:
            return {'success': False, 'error': f'不支持的嵌入方法: {embedding}'}

        query_vector = embed_fn(query_text, dim=coll['dim'])
        result = self.search(collection_id, query_vector, top_k, filter_metadata=filter_metadata)
        if result.get('success'):
            result['query_text'] = query_text
            result['embedding'] = embedding
        return result

    # ========== 统计 ==========

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_vector_collections')
                total_collections = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_vector_items')
                total_items = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_vector_query_log')
                total_queries = cursor.fetchone()[0]
                cursor.execute('SELECT name, item_count, dim, metric FROM ai_vector_collections')
                coll_stats = [
                    {'name': r[0], 'item_count': r[1], 'dim': r[2], 'metric': r[3]}
                    for r in cursor.fetchall()
                ]
                cursor.execute('SELECT AVG(duration_ms) FROM ai_vector_query_log')
                avg_duration = cursor.fetchone()[0] or 0
                return {
                    'total_collections': total_collections,
                    'total_items': total_items,
                    'total_queries': total_queries,
                    'avg_query_duration_ms': round(avg_duration, 2),
                    'collections': coll_stats
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    store = AIVectorStore(default_dim=128)
    print(f"统计: {store.get_statistics()}")

    # 创建集合
    print("\n创建集合:")
    result = store.create_collection('documents', dim=128, metric='cosine',
                                     description='文档向量集合', index_type='lsh')
    print(f"  {result}")

    coll = store.get_collection_by_name('documents')
    if coll:
        coll_id = coll['collection_id']

        # 添加文本
        print("\n添加文档:")
        docs = [
            ('Python 是一门解释型编程语言', 'python'),
            ('Java 是面向对象的编程语言', 'java'),
            ('JavaScript 用于前端开发', 'js'),
            ('机器学习是人工智能的分支', 'ml'),
            ('深度学习使用神经网络', 'dl'),
        ]
        for text, tag in docs:
            r = store.add_text(coll_id, text, document=text, metadata={'tag': tag})
            print(f"  添加: {tag} -> {r.get('item_id')}")

        # 搜索
        print("\n搜索 'AI 编程':")
        result = store.search_text(coll_id, 'AI 编程', top_k=3)
        for r in result.get('results', []):
            print(f"  [{r['score']:.4f}] {r['document']}")

        print("\n搜索 '机器学习':")
        result = store.search_text(coll_id, '机器学习', top_k=3)
        for r in result.get('results', []):
            print(f"  [{r['score']:.4f}] {r['document']}")

        print(f"\n最终统计: {store.get_statistics()}")
