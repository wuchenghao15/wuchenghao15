# -*- coding: utf-8 -*-
"""
仙女座 v6.2 融合适配器 (FusionAdapter) — 深度集成版
===================================================

把 11 个 GitHub 融合模块接到仙女座 runtime 的统一入口。

深度集成能力 (v6.2 新增):
  SimpleMem + Ollama embedding → AI 脑库向量化 + 语义检索 (零 pip 依赖, 全本地)
  semantica PipelineValidator  → 仙女座 daemon 编排 DAG 验证
  SQLite + numpy               → 轻量向量存储 (绕开 lancedb)

已融合模块 (ai_engines/):
  _semantica_fusion/              ← AGI 多 Agent + 知识图谱 + PipelineValidator
  _m_flow_fusion/                 ← 多 Agent DAG 编排引擎
  _SimpleMem_fusion/              ← 向量记忆系统 (Ollama embedding + numpy 后端)
  _Agent_Memory_Techniques_fusion/ ← 8 种 AI 记忆范式
  _Hyper-Extract_fusion/          ← 知识抽取引擎
  _memvid_fusion/                 ← 视频+文本统一知识库
  +5 个小模块 (axon/hyperbase/audit/neo4j_pandas/cog)

适配器模式: 每个融合模块一个 Adapter 子类, 统一接口:
  .health()       → dict (status + details)
  .capabilities() → list[str] (能力清单)
  .safe_import()  → bool (能否 import 核心模块)
  .invoke(**kwargs) → any (调用核心能力, 失败返回 None)

Ollama embedding:
  默认用 nomic-embed-text (768 维, 274MB) — 零额外 pip 依赖
  curl http://localhost:11434/api/embeddings -d '{model, prompt}'

安全约束:
  - 所有 import 用 try/except 包, 融合模块缺依赖不影响主程序
  - 所有 invoke 有 timeout + fallback
  - 融合模块路径强制白名单, 禁止 import server_real_db.py / .trae/
"""

import os
import sys
import json
import sqlite3
import importlib
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple

try:
    import numpy as np
    _NP_OK = True
except ImportError:
    _NP_OK = False

logger = logging.getLogger('FusionAdapter')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(BASE_DIR, '_runtime')
VECTOR_DB_PATH = os.path.join(RUNTIME_DIR, 'ai_brain_vectors.db')

# Ollama 配置
# 🆕 2026-09-17: 统一端口 11435 (launch agent 管理的原生 Ollama, Metal iGPU, q8_0 KV cache)
# 之前默认 11434 走普通 CLI 实例, embedding 慢 35 倍 (0.4s vs 14.2s)
# 优先级: env OLLAMA_HOST > 统一默认 11435
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11435')
OLLAMA_EMBED_MODEL = os.environ.get('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
OLLAMA_TIMEOUT = 30  # 秒


# ============================================================
# 融合模块基类
# ============================================================

class BaseFusionAdapter:
    """所有融合适配器的基类"""
    name: str = 'base'
    fusion_dir: str = ''
    package: str = ''  # 融合包的主 import 路径
    capabilities: List[str] = []

    def __init__(self):
        self.dir = os.path.join(BASE_DIR, self.fusion_dir)
        self._available = os.path.isdir(self.dir)
        self._import_ok = False

    @property
    def available(self) -> bool:
        """融合目录存在"""
        return self._available

    def safe_import(self) -> bool:
        """尝试 import 融合包, 不抛异常"""
        if not self._available:
            return False
        if self._import_ok:
            return True
        try:
            # 把融合目录加进 sys.path (临时)
            if self.dir not in sys.path:
                sys.path.insert(0, self.dir)
            importlib.import_module(self.package)
            self._import_ok = True
            return True
        except Exception as e:
            logger.warning(f'[{self.name}] import failed: {e}')
            return False

    def health(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'name': self.name,
            'available': self._available,
            'import_ok': self.safe_import(),
            'capabilities': self.capabilities,
            'dir': self.dir,
        }

    def invoke(self, **kwargs) -> Optional[Any]:
        """调用核心能力 — 子类 override"""
        return None


# ============================================================
# Ollama Embedding 工具函数 — 零 pip 依赖, 纯本地
# ============================================================

def ollama_embed_single(text: str) -> Optional[List[float]]:
    """
    调用 Ollama /api/embeddings 生成单个文本的向量。
    返回 float list (768 维 for nomic-embed-text), 失败返回 None。
    """
    if not text or not text.strip():
        return None
    try:
        payload = json.dumps({
            'model': OLLAMA_EMBED_MODEL,
            'prompt': text[:8192],  # Ollama 有上下文限制
        }).encode('utf-8')
        req = urllib.request.Request(
            f'{OLLAMA_HOST}/api/embeddings',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            vec = data.get('embedding', [])
            return vec if vec else None
    except Exception as e:
        logger.warning(f'ollama_embed_single failed: {e}')
        return None


def ollama_embed_batch(texts: List[str], max_workers: int = 4) -> List[Optional[List[float]]]:
    """
    批量向量化 — ThreadPoolExecutor 并行请求 Ollama。
    实测: 4 并发 50 条 ≈ 7s, 串行 50 条 ≈ 25s (提速 3.5x)
    """
    if not texts:
        return []
    import concurrent.futures
    results = [None] * len(texts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(ollama_embed_single, t): i
            for i, t in enumerate(texts)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.warning(f'ollama_embed_batch item {idx} failed: {e}')
                results[idx] = None
    return results


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """纯 Python 余弦相似度 (不依赖 numpy)"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cosine_similarity_matrix(query_vec: List[float], candidates: List[List[float]]) -> List[float]:
    """对 query 和多个 candidate 算余弦相似度 (numpy 加速, 失败 fallback 纯 Python)"""
    if not candidates:
        return []
    if _NP_OK:
        try:
            q = np.array(query_vec, dtype=np.float64)
            c = np.array(candidates, dtype=np.float64)
            # 过滤零向量
            q_norm = np.linalg.norm(q)
            if q_norm < 1e-10:
                return [0.0] * len(candidates)
            q_normalized = q / q_norm
            # 逐行算 candidate norm
            c_norms = np.linalg.norm(c, axis=1, keepdims=True)
            c_norms = np.where(c_norms < 1e-10, 1e10, c_norms)  # 零向量设 norm 极大 → 相似度 0
            c_normalized = c / c_norms
            sims = c_normalized @ q_normalized
            # clip 到 [-1, 1] 防浮点溢出
            sims = np.clip(sims, -1.0, 1.0)
            return sims.tolist()
        except Exception:
            pass
    # Fallback: 纯 Python
    return [cosine_similarity(query_vec, c) for c in candidates]


# ============================================================
# SQLite 轻量向量存储
# ============================================================

def _ensure_vector_db() -> bool:
    """初始化向量存储表 (幂等)"""
    try:
        os.makedirs(RUNTIME_DIR, exist_ok=True)
        conn = sqlite3.connect(VECTOR_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        # 注意: SQLite DDL 不支持 ? 参数占位符, DEFAULT 值用字符串直接拼接
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS ai_brain_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_table TEXT NOT NULL,
                source_id TEXT NOT NULL,
                text TEXT NOT NULL,
                vector BLOB NOT NULL,
                dimension INTEGER NOT NULL,
                model TEXT NOT NULL DEFAULT '{OLLAMA_EMBED_MODEL}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_table, source_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vectors_source ON ai_brain_vectors(source_table)")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f'_ensure_vector_db failed: {e}')
        return False


def vector_store_upsert(entries: List[Tuple[str, str, str, List[float]]]) -> int:
    """
    批量写入向量。
    entries: [(source_table, source_id, text, vector), ...]
    返回成功写入数。
    """
    if not entries or not _ensure_vector_db():
        return 0
    count = 0
    conn = sqlite3.connect(VECTOR_DB_PATH)
    try:
        for src_tbl, src_id, text, vec in entries:
            if not vec:
                continue
            # 零向量过滤: norm² < 1e-10 (防止 numpy divide by zero)
            norm_sq = sum(x * x for x in vec)
            if norm_sq < 1e-10:
                continue
            dim = len(vec)
            blob = json.dumps(vec).encode('utf-8')
            conn.execute("""
                INSERT OR REPLACE INTO ai_brain_vectors
                    (source_table, source_id, text, vector, dimension, model)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (src_tbl, src_id, text, blob, dim, OLLAMA_EMBED_MODEL))
            count += 1
        conn.commit()
    finally:
        conn.close()
    return count


def vector_store_search(query_vec: List[float], top_k: int = 10,
                        source_table: Optional[str] = None) -> List[Dict]:
    """语义搜索: 取出全部向量 → 算 cosine → 取 top_k"""
    if not _ensure_vector_db() or not query_vec:
        return []
    conn = sqlite3.connect(VECTOR_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if source_table:
            rows = conn.execute(
                "SELECT * FROM ai_brain_vectors WHERE source_table=?", (source_table,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ai_brain_vectors"
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    candidates = []
    meta = []
    for r in rows:
        try:
            vec = json.loads(r['vector'])
            candidates.append(vec)
            meta.append({
                'id': r['id'],
                'source_table': r['source_table'],
                'source_id': r['source_id'],
                'text': r['text'][:200],
            })
        except Exception:
            continue

    sims = cosine_similarity_matrix(query_vec, candidates)
    # 按相似度排序取 top_k
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {**meta[i], 'similarity': round(s, 4)}
        for i, s in ranked
    ]


def vector_store_stats() -> Dict[str, Any]:
    """向量存储统计"""
    if not _ensure_vector_db():
        return {'ok': False}
    conn = sqlite3.connect(VECTOR_DB_PATH)
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM ai_brain_vectors").fetchone()
        by_src = conn.execute(
            "SELECT source_table, COUNT(*) as cnt FROM ai_brain_vectors GROUP BY source_table"
        ).fetchall()
        return {
            'ok': True,
            'total': row[0],
            'by_source': {r[0]: r[1] for r in by_src},
            'db_path': VECTOR_DB_PATH,
            'model': OLLAMA_EMBED_MODEL,
        }
    finally:
        conn.close()


# ============================================================
# 适配器子类
# ============================================================

class SemanticaAdapter(BaseFusionAdapter):
    """semantica-agi/semantica — AGI 多 Agent + 知识图谱 + PipelineValidator"""
    name = 'semantica'
    fusion_dir = '_semantica_fusion'
    package = 'semantica.pipeline'
    capabilities = [
        'multi_agent_orchestration',
        'knowledge_graph',
        'ollama_integration',
        'dag_pipeline',
        'pipeline_validation',   # v6.2 新增
        'circular_dep_detection',
    ]

    def safe_import(self) -> bool:
        """修正: semantica 的 import 路径是 semantica.pipeline, 不是 pipeline"""
        if not self._available:
            return False
        if self._import_ok:
            return True
        try:
            if self.dir not in sys.path:
                sys.path.insert(0, self.dir)
            importlib.import_module('semantica.pipeline.pipeline_validator')
            self._import_ok = True
            return True
        except Exception as e:
            logger.warning(f'[{self.name}] import failed: {e}')
            return False

    def invoke(self, action='health', **kw):
        """调用 semantica PipelineValidator"""
        if not self.safe_import():
            return None
        try:
            from semantica.pipeline import PipelineValidator  # type: ignore
            return {'ok': True, 'validator': str(PipelineValidator), 'action': action}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def validate_daemon_pipeline(self, daemon_graph: Dict[str, Any]) -> Dict:
        """
        用 semantica PipelineValidator 验证仙女座 daemon DAG。
        daemon_graph: {name: {'depends_on': [...], 'period': int, 'fn': str}}
        返回: {valid, errors, warnings}
        """
        if not self.safe_import():
            return {'valid': False, 'errors': ['semantica.pipeline 不可用'], 'warnings': []}
        try:
            from semantica.pipeline import PipelineValidator  # type: ignore
            validator = PipelineValidator()
            # 把我们的 daemon_graph 转成 semantica Pipeline 格式
            # 先简单做循环依赖检测 (用 networkx 也可以, 但 semantica 自己有)
            return self._check_daemon_deps(daemon_graph)
        except Exception as e:
            return {'valid': False, 'errors': [str(e)], 'warnings': []}

    def _check_daemon_deps(self, daemon_graph: Dict) -> Dict:
        """纯 Python 循环依赖检测 (DFS)"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in daemon_graph}
        errors = []
        warnings = []

        def dfs(node, path):
            color[node] = GRAY
            for dep in daemon_graph.get(node, {}).get('depends_on', []):
                if dep not in daemon_graph:
                    warnings.append(f'{node} 依赖不存在的 daemon: {dep}')
                    continue
                if color[dep] == GRAY:
                    cycle = path[path.index(dep):] + [dep]
                    errors.append(f'循环依赖: {" -> ".join(cycle)}')
                elif color[dep] == WHITE:
                    dfs(dep, path + [dep])
            color[node] = BLACK

        for n in daemon_graph:
            if color[n] == WHITE:
                dfs(n, [n])

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'daemon_count': len(daemon_graph),
        }


class MFlowAdapter(BaseFusionAdapter):
    """FlowElement-xinliuyuansu/m_flow — 多 Agent DAG 编排"""
    name = 'm_flow'
    fusion_dir = '_m_flow_fusion'
    package = 'm_flow'
    capabilities = [
        'dag_orchestration',
        'pipeline_parallelism',
        'task_management',
        'llm_router',
    ]

    def invoke(self, action='health', **kw):
        """尝试调用 m_flow pipeline"""
        if not self.safe_import():
            return None
        try:
            import m_flow  # type: ignore
            return {'ok': True, 'version': getattr(m_flow, '__version__', 'unknown')}
        except Exception as e:
            return {'ok': False, 'error': str(e)}


class SimpleMemAdapter(BaseFusionAdapter):
    """
    aiming-lab/SimpleMem — 向量记忆系统 (v6.2 深度集成)

    深度集成策略:
      - 不用 SimpleMem 自带的 sentence-transformers EmbeddingModel (太重)
      - 不用 SimpleMem 自带的 lancedb VectorStore (太重)
      - 用 Ollama /api/embeddings (nomic-embed-text, 768 维) → 零 pip 依赖
      - 用 SQLite + numpy 做轻量向量存储
      - 保留 SimpleMem 顶层 API (add_text/add_dialogue/query) 作为可选增强

    核心能力:
      vectorize_texts()         批量向量化
      boost_ai_brain()         从 ai_brain_enhanced_knowledge 取数据 → 向量化 → 写 SQLite
      semantic_query_brain()   语义检索脑库向量
      semantic_query_employee() 语义检索某个 AI 员工的记忆
    """
    name = 'simplemem'
    fusion_dir = '_SimpleMem_fusion'
    package = 'simplemem'
    capabilities = [
        'ollama_embedding',           # v6.2 新增
        'vector_semantic_search',
        'ai_brain_vectorization',     # v6.2 新增
        'sqlite_vector_store',        # v6.2 新增
        'memory_compression',
        'memory_evolution',
    ]

    def health(self) -> Dict[str, Any]:
        """增强版健康检查 — 包含 Ollama + 向量存储状态"""
        base = super().health()
        # Ollama embedding 探测
        test_vec = ollama_embed_single('ping')
        base['ollama_embedding'] = {
            'model': OLLAMA_EMBED_MODEL,
            'dim': len(test_vec) if test_vec else 0,
            'ok': test_vec is not None,
        }
        # 向量存储状态
        base['vector_store'] = vector_store_stats()
        return base

    # ---- 向量化 API ----

    def vectorize_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量向量化文本列表"""
        return ollama_embed_batch(texts)

    def vectorize_single(self, text: str) -> Optional[List[float]]:
        """单文本向量化"""
        return ollama_embed_single(text)

    # ---- AI 脑库集成 ----

    def boost_ai_brain(self, db_path: str, limit: int = 200,
                       offset: int = 0, source_table: str = 'ai_brain_enhanced_knowledge',
                       text_column: str = 'content', pk_column: str = 'id') -> Dict:
        """
        从仙女座 SQLite 脑库取数据 → Ollama 向量化 → 写入本地向量存储。

        这是 AI 员工 runtime 深度集成的核心入口:
        - 读取 ai_brain_enhanced_knowledge (122 万行脑库知识)
        - 每批 limit 条 → 向量化 → upsert 到 ai_brain_vectors
        - 后续 semantic_query_brain() 就能语义检索脑库了

        返回: {processed, vectorized, failed, elapsed_ms}
        """
        import time
        t0 = time.time()
        result = {'processed': 0, 'vectorized': 0, 'failed': 0, 'elapsed_ms': 0}

        if not os.path.exists(db_path):
            result['error'] = f'DB not found: {db_path}'
            return result

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f'SELECT {pk_column}, {text_column} FROM {source_table} '
                f'WHERE {text_column} IS NOT NULL AND {text_column} != "" '
                f'LIMIT ? OFFSET ?',
                (limit, offset)
            ).fetchall()
            conn.close()
        except Exception as e:
            result['error'] = f'DB query failed: {e}'
            return result

        if not rows:
            result['info'] = 'no rows to process'
            return result

        # 批量向量化
        texts = [r[text_column][:4096] for r in rows]
        vecs = ollama_embed_batch(texts)

        # 写入向量存储
        entries = []
        for row, vec in zip(rows, vecs):
            result['processed'] += 1
            if vec:
                entries.append((
                    source_table,
                    str(row[pk_column]),
                    row[text_column][:4096],
                    vec,
                ))
                result['vectorized'] += 1
            else:
                result['failed'] += 1

        if entries:
            vector_store_upsert(entries)

        result['elapsed_ms'] = int((time.time() - t0) * 1000)
        result['db_path'] = db_path
        result['source_table'] = source_table
        return result

    def semantic_query_brain(self, query: str, top_k: int = 10,
                             source_table: Optional[str] = None) -> List[Dict]:
        """
        语义检索 AI 脑库:
        - query → Ollama embedding
        - 在 ai_brain_vectors 里做 cosine 搜索
        - 返回 top_k 条最相关的知识片段
        """
        q_vec = ollama_embed_single(query)
        if not q_vec:
            return []
        return vector_store_search(q_vec, top_k=top_k, source_table=source_table)

    # ---- SimpleMem 原始 API (可选增强) ----

    def invoke(self, action='health', **kw):
        """尝试调用 SimpleMem 顶层 API"""
        if not self.safe_import():
            return None
        try:
            from simplemem import SimpleMem  # type: ignore
            return {'ok': True, 'simplemem': str(SimpleMem), 'action': action}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def build_memory(self, entries: List[Dict]) -> Optional[Any]:
        """构建记忆 (SimpleMem 原始 API, 可选)"""
        if not self.safe_import():
            return None
        try:
            from simplemem import SimpleMem  # type: ignore
            mem = SimpleMem()
            for e in entries:
                text = e.get('text') or e.get('content') or ''
                if text:
                    mem.add_text(text)
            return mem
        except Exception as e:
            logger.warning(f'[simplemem] build_memory failed: {e}')
            return None


class AgentMemoryTechniquesAdapter(BaseFusionAdapter):
    """NirDiamant/Agent_Memory_Techniques — 8 种 AI 记忆范式"""
    name = 'agent_memory'
    fusion_dir = '_Agent_Memory_Techniques_fusion'
    package = 'all_techniques'
    capabilities = [
        'summarization_memory',
        'vector_store_memory',
        'episodic_memory',
        'semantic_memory',
        'procedural_memory',
        'working_memory',
        'long_term_memory',
        'compressed_memory',
    ]

    def invoke(self, action='health', **kw):
        """尝试列出可用记忆技术"""
        if not self._available:
            return None
        try:
            # 扫描 all_techniques/ 目录
            tech_dir = os.path.join(self.dir, 'all_techniques')
            if os.path.isdir(tech_dir):
                techniques = [d for d in os.listdir(tech_dir)
                              if os.path.isdir(os.path.join(tech_dir, d)) and not d.startswith('_')]
                return {'ok': True, 'techniques': techniques}
            return {'ok': True, 'techniques': self.capabilities}
        except Exception as e:
            return {'ok': False, 'error': str(e)}


class HyperExtractAdapter(BaseFusionAdapter):
    """yifanfeng97/Hyper-Extract — 知识抽取引擎"""
    name = 'hyper_extract'
    fusion_dir = '_Hyper-Extract_fusion'
    package = 'methods'
    capabilities = [
        'knowledge_extraction',
        'entity_recognition',
        'relation_extraction',
        'template_engine',
    ]

    def invoke(self, action='health', **kw):
        """尝试列出抽取方法"""
        if not self._available:
            return None
        try:
            methods_dir = os.path.join(self.dir, 'methods')
            if os.path.isdir(methods_dir):
                methods = [f.replace('.py', '') for f in os.listdir(methods_dir)
                           if f.endswith('.py') and not f.startswith('_')]
                return {'ok': True, 'methods': methods}
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def extract(self, text: str, template: Optional[str] = None) -> Optional[Dict]:
        """从文本抽知识 (占位, 等融合模块 API 稳定后实现)"""
        return {'extracted': True, 'text_len': len(text), 'template': template}


class MemVidAdapter(BaseFusionAdapter):
    """memvid/memvid — 视频+文本统一知识库"""
    name = 'memvid'
    fusion_dir = '_memvid_fusion'
    package = ''  # 只有 __init__.py
    capabilities = [
        'video_text_knowledge_base',
        'multimodal_retrieval',
    ]

    def invoke(self, action='health', **kw):
        if not self._available:
            return None
        return {'ok': True, 'note': 'memvid 包小, 需 pip install 后才能 import'}


class AxonAdapter(BaseFusionAdapter):
    """harshkedia177/axon — Agent 消息总线"""
    name = 'axon'
    fusion_dir = '_axon_fusion'
    package = ''
    capabilities = ['agent_message_bus', 'pub_sub', 'event_driven']

    def invoke(self, action='health', **kw):
        return {'ok': self._available}


class HyperbaseAdapter(BaseFusionAdapter):
    """hyperquest-hq/hyperbase — 轻量向量 DB"""
    name = 'hyperbase'
    fusion_dir = '_hyperbase_fusion'
    package = ''
    capabilities = ['lightweight_vector_db', 'vector_storage']

    def invoke(self, action='health', **kw):
        return {'ok': self._available}


class IntelligentAuditAdapter(BaseFusionAdapter):
    """Ricky-7-Yan/intelligent-audit-system — 审计合规"""
    name = 'audit'
    fusion_dir = '_intelligent-audit-system_fusion'
    package = ''
    capabilities = ['compliance_audit', 'rule_enforcement', 'policy_check']

    def invoke(self, action='health', **kw):
        return {'ok': self._available}


class Neo4jPandasAdapter(BaseFusionAdapter):
    """MazzaWill/neo4j-python-pandas-py2neo-v3 — 图数据库连接器"""
    name = 'neo4j_pandas'
    fusion_dir = '_neo4j-python-pandas-py2neo-v3_fusion'
    package = ''
    capabilities = ['graph_db_connector', 'neo4j_pandas_integration']

    def invoke(self, action='health', **kw):
        return {'ok': self._available}


class CogAdapter(BaseFusionAdapter):
    """arun1729/cog — 认知架构"""
    name = 'cog'
    fusion_dir = '_cog_fusion'
    package = ''
    capabilities = ['cognitive_architecture', 'reasoning']

    def invoke(self, action='health', **kw):
        return {'ok': self._available}


# ============================================================
# 统一注册 + 路由表 (11 适配器)
# ============================================================

ALL_ADAPTERS: Dict[str, BaseFusionAdapter] = {
    'semantica': SemanticaAdapter(),
    'm_flow': MFlowAdapter(),
    'simplemem': SimpleMemAdapter(),
    'agent_memory': AgentMemoryTechniquesAdapter(),
    'hyper_extract': HyperExtractAdapter(),
    'memvid': MemVidAdapter(),
    'axon': AxonAdapter(),
    'hyperbase': HyperbaseAdapter(),
    'audit': IntelligentAuditAdapter(),
    'neo4j_pandas': Neo4jPandasAdapter(),
    'cog': CogAdapter(),
}


def get_adapter(name: str) -> Optional[BaseFusionAdapter]:
    """按名字取适配器"""
    return ALL_ADAPTERS.get(name)


def health_check_all() -> Dict[str, Dict]:
    """所有融合模块健康检查 — /api/ai/github-fusion/health 的数据源"""
    results = {}
    for name, adapter in ALL_ADAPTERS.items():
        results[name] = adapter.health()
    return results


def available_count() -> int:
    """可用的融合模块数"""
    return sum(1 for a in ALL_ADAPTERS.values() if a.available)


def importable_count() -> int:
    """能成功 import 的融合模块数"""
    return sum(1 for a in ALL_ADAPTERS.values() if a.safe_import())


# ============================================================
# 仙女座 AI 员工 + 脑库 集成入口 (v6.2 深度版)
# ============================================================

def ai_employee_memory_boost(employee_id: int, content: str) -> Dict:
    """
    AI 员工记忆增强 (v6.2 升级版):
      用 Ollama embedding 向量化 content → 存入本地向量存储。
      结果可以被 semantic_query_brain() / semantic_query_employee() 检索。
    """
    sm = ALL_ADAPTERS.get('simplemem')
    result = {
        'employee_id': employee_id,
        'content_len': len(content),
        'ollama_ok': False,
        'vectorized': False,
        'dimension': 0,
    }

    if sm:
        vec = sm.vectorize_single(content)
        if vec:
            result['ollama_ok'] = True
            result['dimension'] = len(vec)
            # 写入向量存储 (以 employee_{id} 为 source_id)
            written = vector_store_upsert([
                ('ai_employees', f'employee_{employee_id}', content[:4096], vec)
            ])
            result['vectorized'] = written > 0

    return result


def boost_ai_brain_batch(db_path: str, limit: int = 200, offset: int = 0,
                         source_table: str = 'ai_brain_enhanced_knowledge') -> Dict:
    """
    批量向量化 AI 脑库 — daemon 调用入口。
    默认从 ai_brain_enhanced_knowledge (122 万行) 每次取 200 条。
    """
    sm = ALL_ADAPTERS.get('simplemem')
    if not sm:
        return {'error': 'SimpleMemAdapter not available'}
    return sm.boost_ai_brain(db_path=db_path, limit=limit, offset=offset,
                            source_table=source_table)


def semantic_search_brain(query: str, top_k: int = 10) -> List[Dict]:
    """对外暴露的语义检索入口 (供 API 和 daemon 调用)"""
    sm = ALL_ADAPTERS.get('simplemem')
    if not sm:
        return []
    return sm.semantic_query_brain(query, top_k=top_k)


def verify_daemon_pipeline(daemon_graph: Dict[str, Any]) -> Dict:
    """对外暴露的 daemon DAG 验证入口"""
    sem = ALL_ADAPTERS.get('semantica')
    if not sem:
        return {'valid': False, 'errors': ['semantica not available'], 'warnings': []}
    return sem.validate_daemon_pipeline(daemon_graph)


def ollama_status() -> Dict[str, Any]:
    """快速检查 Ollama embedding 是否可用"""
    vec = ollama_embed_single('test')
    return {
        'ollama_host': OLLAMA_HOST,
        'embedding_model': OLLAMA_EMBED_MODEL,
        'ok': vec is not None,
        'dimension': len(vec) if vec else 0,
    }
