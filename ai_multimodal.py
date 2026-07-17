#!/usr/bin/env python3
"""
MTSCOS AI 多模态处理服务 (v15.0.0)
===================================
AI 多模态数据处理和融合服务。

核心能力：
1. 模态编码 - 文本/图像/音频特征编码
2. 跨模态融合 - 拼接/加权/注意力融合
3. 跨模态检索 - 文图互检
4. 模态对齐 - 跨模态嵌入空间对齐
5. 多模态分类 - 融合特征分类
6. 模态补全 - 缺失模态生成
7. 模态转换 - 简化版文转图描述
8. 多模态报告 - 融合分析报告
"""
import os
import json
import math
import hashlib
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_multimodal.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIMultimodal')


# ========== 模态编码器 ==========

def encode_text(text: str, dim: int = 128) -> List[float]:
    """文本编码：基于字符级和词级的哈希嵌入"""
    if not text:
        return [0.0] * dim

    vector = [0.0] * dim
    # 字符级编码
    for i, char in enumerate(text):
        idx = hash(char) % dim
        vector[idx] += 1.0 / (1 + i * 0.01)

    # 词级编码
    words = text.lower().split()
    for i, word in enumerate(words):
        word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = word_hash % dim
        vector[idx] += 2.0 / (1 + i * 0.1)

    # 位置编码
    for i in range(min(len(text), dim)):
        vector[i] += math.sin(i / 10000) * 0.1

    # L2归一化
    norm = math.sqrt(sum(v ** 2 for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def encode_image_features(width: int, height: int, channels: int = 3,
                         dim: int = 128) -> List[float]:
    """图像特征编码（模拟）：从图像属性生成嵌入"""
    # 模拟从图像提取特征
    vector = [0.0] * dim

    # 基于尺寸的特征
    aspect_ratio = width / max(height, 1)
    size_feature = math.log(1 + width * height)

    vector[0] = aspect_ratio
    vector[1] = size_feature / 20
    vector[2] = channels / 3.0

    # 模拟纹理特征（随机但确定性）
    seed = width * 1000 + height
    rng = random.Random(seed)
    for i in range(3, dim):
        vector[i] = rng.gauss(0, 0.3)

    # L2归一化
    norm = math.sqrt(sum(v ** 2 for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def encode_image_from_pixels(pixels: List[List[List[float]]], dim: int = 128) -> List[float]:
    """从像素数据编码图像（简化版）"""
    if not pixels or not pixels[0]:
        return [0.0] * dim

    vector = [0.0] * dim
    height = len(pixels)
    width = len(pixels[0])
    channels = len(pixels[0][0]) if pixels[0] else 3

    # 颜色直方图特征
    total_pixels = height * width
    color_sum = [0.0] * channels
    for row in pixels:
        for pixel in row:
            for c in range(min(channels, len(pixel))):
                color_sum[c] += pixel[c]

    # 平均颜色
    avg_colors = [s / total_pixels for s in color_sum]
    for i in range(min(channels, dim)):
        vector[i] = avg_colors[i]

    # 模拟纹理和形状特征
    rng = random.Random(int(sum(color_sum)) % (2**31))
    for i in range(channels, dim):
        vector[i] = rng.gauss(0, 0.2)

    # L2归一化
    norm = math.sqrt(sum(v ** 2 for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def encode_audio_features(duration_sec: float, sample_rate: int = 44100,
                         dim: int = 128) -> List[float]:
    """音频特征编码（模拟）"""
    vector = [0.0] * dim

    # 基本特征
    vector[0] = min(duration_sec / 60, 1.0)  # 时长归一化
    vector[1] = math.log(1 + sample_rate) / math.log(44100)  # 采样率

    # 模拟频谱特征
    rng = random.Random(int(duration_sec * 1000) + sample_rate)
    for i in range(2, dim):
        # 模拟频谱衰减
        freq_weight = 1.0 / (1 + i * 0.05)
        vector[i] = rng.gauss(0, freq_weight * 0.3)

    # L2归一化
    norm = math.sqrt(sum(v ** 2 for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


MODAL_ENCODERS = {
    'text': lambda data, dim=128: encode_text(data, dim) if isinstance(data, str) else encode_text(str(data), dim),
    'image': lambda data, dim=128: encode_image_from_pixels(data, dim) if isinstance(data, list) else encode_image_features(data.get('width', 224), data.get('height', 224), data.get('channels', 3), dim),
    'audio': lambda data, dim=128: encode_audio_features(data.get('duration', 1.0), data.get('sample_rate', 44100), dim) if isinstance(data, dict) else encode_audio_features(float(data), dim=dim),
}


# ========== 融合策略 ==========

def concatenate_fusion(modal_vectors: Dict[str, List[float]]) -> List[float]:
    """拼接融合"""
    result = []
    for modality in sorted(modal_vectors.keys()):
        result.extend(modal_vectors[modality])
    return result


def weighted_fusion(modal_vectors: Dict[str, List[float]],
                   weights: Dict[str, float] = None) -> List[float]:
    """加权融合（需要各模态维度相同）"""
    if not modal_vectors:
        return []

    weights = weights or {}
    # 归一化权重
    total_weight = sum(weights.get(m, 1.0) for m in modal_vectors)
    if total_weight == 0:
        total_weight = 1

    # 获取维度
    dim = len(next(iter(modal_vectors.values())))
    result = [0.0] * dim
    for modality, vec in modal_vectors.items():
        w = weights.get(modality, 1.0) / total_weight
        for i in range(min(len(vec), dim)):
            result[i] += w * vec[i]

    # L2归一化
    norm = math.sqrt(sum(v ** 2 for v in result))
    if norm > 0:
        result = [v / norm for v in result]
    return result


def attention_fusion(modal_vectors: Dict[str, List[float]],
                    query: List[float] = None) -> List[float]:
    """注意力融合"""
    if not modal_vectors:
        return []

    modalities = list(modal_vectors.keys())
    vectors = [modal_vectors[m] for m in modalities]

    # 如果没有query，使用均值作为query
    if query is None:
        dim = len(vectors[0])
        query = [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]

    # 计算注意力权重
    weights = []
    for vec in vectors:
        # 点积注意力
        score = sum(q * v for q, v in zip(query, vec))
        weights.append(score)

    # Softmax
    max_w = max(weights)
    exp_w = [math.exp(w - max_w) for w in weights]
    total = sum(exp_w)
    weights = [w / total for w in exp_w]

    # 加权求和
    dim = len(vectors[0])
    result = [0.0] * dim
    for w, vec in zip(weights, vectors):
        for i in range(dim):
            result[i] += w * vec[i]

    return result


FUSION_METHODS = {
    'concatenate': concatenate_fusion,
    'weighted': weighted_fusion,
    'attention': attention_fusion,
}


# ========== 跨模态检索 ==========

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(y ** 2 for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ========== 多模态服务 ==========

class AIMultimodal:
    """AI 多模态处理服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._embedding_store: Dict[str, List[Dict]] = defaultdict(list)  # modality -> [{id, vector, metadata}]

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS multimodal_items (
                        item_id TEXT PRIMARY KEY,
                        modality TEXT NOT NULL,
                        content_hash TEXT,
                        embedding TEXT,
                        metadata TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS multimodal_fusions (
                        fusion_id TEXT PRIMARY KEY,
                        method TEXT,
                        modalities TEXT,
                        input_ids TEXT,
                        result_embedding TEXT,
                        result_dim INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS multimodal_alignments (
                        alignment_id TEXT PRIMARY KEY,
                        source_modality TEXT,
                        target_modality TEXT,
                        source_id TEXT,
                        target_id TEXT,
                        similarity REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_mm_modality ON multimodal_items(modality)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化多模态数据库失败: {e}")

    # ========== 编码和存储 ==========

    def encode_and_store(self, item_id: str, modality: str, data: Any,
                        metadata: Dict = None, dim: int = 128) -> Dict:
        """编码并存储多模态数据"""
        if modality not in MODAL_ENCODERS:
            return {'success': False, 'error': f'不支持的模态: {modality}'}

        embedding = MODAL_ENCODERS[modality](data, dim)
        content_hash = hashlib.md5(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO multimodal_items
                    (item_id, modality, content_hash, embedding, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, modality, content_hash,
                    json.dumps(embedding),
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        # 内存缓存
        self._embedding_store[modality].append({
            'id': item_id,
            'vector': embedding,
            'metadata': metadata or {}
        })

        return {
            'success': True,
            'item_id': item_id,
            'modality': modality,
            'embedding_dim': len(embedding),
            'content_hash': content_hash
        }

    def get_embedding(self, item_id: str) -> Optional[Dict]:
        """获取存储的嵌入"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM multimodal_items WHERE item_id = ?', (item_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'item_id': row[0], 'modality': row[1],
                    'content_hash': row[2],
                    'embedding': json.loads(row[3]),
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                }
        except Exception:
            return None

    # ========== 融合 ==========

    def fuse_modalities(self, item_ids: List[str], method: str = 'attention',
                       weights: Dict[str, float] = None,
                       query: List[float] = None) -> Dict:
        """融合多个模态的嵌入"""
        modal_vectors = {}
        items_info = {}

        for item_id in item_ids:
            item = self.get_embedding(item_id)
            if item:
                modal_vectors[item['modality']] = item['embedding']
                items_info[item_id] = item['modality']

        if not modal_vectors:
            return {'success': False, 'error': '未找到有效嵌入'}

        fusion_fn = FUSION_METHODS.get(method)
        if not fusion_fn:
            return {'success': False, 'error': f'不支持的融合方法: {method}'}

        if method == 'weighted':
            result = fusion_fn(modal_vectors, weights)
        elif method == 'attention':
            result = fusion_fn(modal_vectors, query)
        else:
            result = fusion_fn(modal_vectors)

        fusion_id = f"FUSE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO multimodal_fusions
                    (fusion_id, method, modalities, input_ids, result_embedding,
                     result_dim, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fusion_id, method,
                    json.dumps(list(modal_vectors.keys())),
                    json.dumps(item_ids),
                    json.dumps(result),
                    len(result), datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

        return {
            'success': True,
            'fusion_id': fusion_id,
            'method': method,
            'modalities': list(modal_vectors.keys()),
            'input_items': items_info,
            'result_dim': len(result),
            'result_embedding': result[:10]  # 只返回前10维预览
        }

    # ========== 跨模态检索 ==========

    def cross_modal_search(self, query_item_id: str, target_modality: str,
                          top_k: int = 5) -> Dict:
        """跨模态检索：用一个模态的查询检索另一个模态"""
        query_item = self.get_embedding(query_item_id)
        if not query_item:
            return {'success': False, 'error': '查询项不存在'}

        query_vec = query_item['embedding']
        source_modality = query_item['modality']

        # 在目标模态中搜索
        target_items = self._embedding_store.get(target_modality, [])
        if not target_items:
            # 从数据库加载
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT item_id, embedding, metadata FROM multimodal_items WHERE modality = ?',
                                 (target_modality,))
                    for row in cursor.fetchall():
                        target_items.append({
                            'id': row[0],
                            'vector': json.loads(row[1]),
                            'metadata': json.loads(row[2]) if row[2] else {}
                        })
            except Exception:
                pass

        if not target_items:
            return {'success': False, 'error': f'模态 {target_modality} 无数据'}

        # 计算相似度
        results = []
        for item in target_items:
            sim = cosine_similarity(query_vec, item['vector'])
            results.append({
                'item_id': item['id'],
                'similarity': round(sim, 6),
                'metadata': item.get('metadata', {})
            })

        results.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            'success': True,
            'query_item': query_item_id,
            'source_modality': source_modality,
            'target_modality': target_modality,
            'total_results': len(results),
            'top_results': results[:top_k]
        }

    # ========== 模态对齐 ==========

    def align_modalities(self, source_modality: str, target_modality: str,
                        pairs: List[Tuple[str, str]]) -> Dict:
        """模态对齐：计算跨模态对齐质量"""
        alignments = []
        total_sim = 0

        for source_id, target_id in pairs:
            source_item = self.get_embedding(source_id)
            target_item = self.get_embedding(target_id)
            if not source_item or not target_item:
                continue

            sim = cosine_similarity(source_item['embedding'], target_item['embedding'])
            total_sim += sim
            alignments.append({
                'source_id': source_id,
                'target_id': target_id,
                'similarity': round(sim, 6)
            })

            # 保存对齐记录
            alignment_id = f"ALIGN-{random.randint(100000, 999999)}"
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO multimodal_alignments
                        (alignment_id, source_modality, target_modality,
                         source_id, target_id, similarity, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alignment_id, source_modality, target_modality,
                        source_id, target_id, sim, datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception:
                pass

        avg_sim = total_sim / max(len(alignments), 1)

        return {
            'success': True,
            'source_modality': source_modality,
            'target_modality': target_modality,
            'total_pairs': len(alignments),
            'avg_similarity': round(avg_sim, 6),
            'alignment_quality': 'good' if avg_sim > 0.7 else ('fair' if avg_sim > 0.4 else 'poor'),
            'alignments': alignments
        }

    # ========== 缺失模态补全 ==========

    def complete_missing_modality(self, available_items: List[str],
                                 target_modality: str) -> Dict:
        """缺失模态补全：基于已有模态推断缺失模态"""
        # 获取已有模态的融合表示
        available_embeddings = []
        available_modalities = []
        for item_id in available_items:
            item = self.get_embedding(item_id)
            if item:
                available_embeddings.append(item['embedding'])
                available_modalities.append(item['modality'])

        if not available_embeddings:
            return {'success': False, 'error': '无可用模态数据'}

        # 用融合表示作为缺失模态的近似嵌入
        dim = len(available_embeddings[0])
        completed = [0.0] * dim
        for emb in available_embeddings:
            for i in range(min(len(emb), dim)):
                completed[i] += emb[i] / len(available_embeddings)

        # 找最近邻
        target_items = self._embedding_store.get(target_modality, [])
        if target_items:
            nearest = max(target_items, key=lambda x: cosine_similarity(completed, x['vector']))
            return {
                'success': True,
                'target_modality': target_modality,
                'available_modalities': available_modalities,
                'completed_embedding_dim': dim,
                'nearest_neighbor': nearest['id'],
                'nearest_similarity': round(cosine_similarity(completed, nearest['vector']), 6)
            }

        return {
            'success': True,
            'target_modality': target_modality,
            'available_modalities': available_modalities,
            'completed_embedding_dim': dim,
            'note': '无目标模态数据可对比'
        }

    # ========== 多模态分类 ==========

    def multimodal_classify(self, item_ids: List[str],
                           class_prototypes: Dict[str, List[float]] = None) -> Dict:
        """多模态分类（基于融合嵌入）"""
        # 融合
        fusion_result = self.fuse_modalities(item_ids, method='attention')
        if not fusion_result.get('success'):
            return fusion_result

        # 获取完整嵌入
        fusion_id = fusion_result['fusion_id']
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT result_embedding FROM multimodal_fusions WHERE fusion_id = ?', (fusion_id,))
                row = cursor.fetchone()
                fused_embedding = json.loads(row[0]) if row else []
        except Exception:
            return {'success': False, 'error': '获取融合嵌入失败'}

        if not class_prototypes:
            return {'success': False, 'error': '无类别原型'}

        # 计算与各类别的相似度
        scores = {}
        for class_name, prototype in class_prototypes.items():
            scores[class_name] = cosine_similarity(fused_embedding, prototype)

        prediction = max(scores, key=scores.get)

        return {
            'success': True,
            'prediction': prediction,
            'confidence': round(scores[prediction], 6),
            'all_scores': {k: round(v, 6) for k, v in scores.items()},
            'fused_modalities': fusion_result['modalities']
        }

    # ========== 查询和统计 ==========

    def list_items(self, modality: str = None, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if modality:
                    cursor.execute('''
                        SELECT item_id, modality, content_hash, created_at
                        FROM multimodal_items WHERE modality = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (modality, limit))
                else:
                    cursor.execute('''
                        SELECT item_id, modality, content_hash, created_at
                        FROM multimodal_items
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {
                        'item_id': r[0], 'modality': r[1],
                        'content_hash': r[2], 'created_at': r[3]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM multimodal_items')
                total_items = cursor.fetchone()[0]
                cursor.execute("SELECT modality, COUNT(*) FROM multimodal_items GROUP BY modality")
                modality_dist = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM multimodal_fusions')
                total_fusions = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM multimodal_alignments')
                total_alignments = cursor.fetchone()[0]
                return {
                    'total_items': total_items,
                    'modality_distribution': modality_dist,
                    'total_fusions': total_fusions,
                    'total_alignments': total_alignments
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    mm = AIMultimodal()

    print("=== 编码和存储 ===")
    # 文本
    mm.encode_and_store('text-1', 'text', '一只猫坐在窗台上', metadata={'lang': 'zh'})
    mm.encode_and_store('text-2', 'text', '一只狗在公园里奔跑', metadata={'lang': 'zh'})
    mm.encode_and_store('text-3', 'text', '猫在窗台上睡觉', metadata={'lang': 'zh'})

    # 图像（模拟）
    mm.encode_and_store('img-1', 'image', {'width': 224, 'height': 224, 'channels': 3},
                       metadata={'description': '猫的图片'})
    mm.encode_and_store('img-2', 'image', {'width': 256, 'height': 256, 'channels': 3},
                       metadata={'description': '狗的图片'})

    # 音频（模拟）
    mm.encode_and_store('audio-1', 'audio', {'duration': 5.0, 'sample_rate': 44100},
                       metadata={'description': '猫叫声'})

    print(f"  统计: {mm.get_statistics()}")

    print("\n=== 跨模态检索 ===")
    # 用文本检索图像
    result = mm.cross_modal_search('text-1', 'image', top_k=3)
    print(f"  文本→图像: {result.get('top_results')}")

    # 用文本检索音频
    result = mm.cross_modal_search('text-1', 'audio', top_k=3)
    print(f"  文本→音频: {result.get('top_results')}")

    print("\n=== 模态融合 ===")
    # 融合文本和图像
    fusion = mm.fuse_modalities(['text-1', 'img-1'], method='attention')
    print(f"  融合方法: {fusion.get('method')}")
    print(f"  模态: {fusion.get('modalities')}")
    print(f"  维度: {fusion.get('result_dim')}")

    # 加权融合
    fusion = mm.fuse_modalities(['text-1', 'img-1', 'audio-1'], method='weighted',
                               weights={'text': 0.5, 'image': 0.3, 'audio': 0.2})
    print(f"  加权融合: {fusion.get('modalities')}")

    print("\n=== 模态对齐 ===")
    alignment = mm.align_modalities('text', 'image', [('text-1', 'img-1'), ('text-2', 'img-2')])
    print(f"  对齐质量: {alignment.get('alignment_quality')}")
    print(f"  平均相似度: {alignment.get('avg_similarity')}")
    for a in alignment.get('alignments', []):
        print(f"    {a['source_id']} ↔ {a['target_id']}: {a['similarity']}")

    print("\n=== 缺失模态补全 ===")
    completion = mm.complete_missing_modality(['text-1', 'img-1'], 'audio')
    print(f"  目标模态: {completion.get('target_modality')}")
    print(f"  可用模态: {completion.get('available_modalities')}")
    if completion.get('nearest_neighbor'):
        print(f"  最近邻: {completion['nearest_neighbor']} (sim={completion['nearest_similarity']})")

    print(f"\n最终统计: {mm.get_statistics()}")
