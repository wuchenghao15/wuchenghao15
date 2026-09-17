# -*- coding: utf-8 -*-
"""
仙女座七阶段自演化编排引擎 (sys_andromeda_auto_evolution)
========================================================

用户需求: 自动检测 → 自动检索 → 自动联想 → 自动衍生 → 自动强化 → 自动拓展 → 自动优化

设计原则:
  - 统一一个 daemon (600s 周期), 内部按阶段串联, 避免 7 个 daemon 竞争资源
  - 每阶段独立 try/except, 单点异常不影响整体循环
  - 增量策略: 用 checkpoint 记录已处理进度, 绝不全量扫描
  - 零额外 pip 依赖: Ollama (nomic-embed-text + qwen2.5) + SQLite + numpy

七阶段流水线:
  Stage 1  auto_detect        — 扫描脑库新增知识 (checkpoint 增量)
  Stage 2  auto_retrieve      — 新行 Ollama 向量化 + 语义检索关联知识
  Stage 3  auto_associate     — 相似度 > 阈值 → 写 knowledge_graph_relations
  Stage 4  auto_derive        — 关联知识 → Ollama 推理衍生新知识 → 写脑库
  Stage 5  auto_reinforce     — 强化已有知识 confidence_score + usage_count
  Stage 6  auto_expand        — 知识图谱新节点 + AI 员工增强建议
  Stage 7  auto_optimize      — 记录演化日志 + 动态调整阈值

调用方式:
  daemon 工作体自动调用 run_cycle()
  API 可手动触发: POST /api/ai/github-fusion/deep/evolution-cycle
  单阶段调试: python -c "from engines.andromeda_auto_evolution import run_cycle; run_cycle()"
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple
import threading

import numpy as np

logger = logging.getLogger('andromeda_auto_evolution')

# ============ 🆕 演化唤醒 Event (autosync 同步完 → 立刻触发演化) ============
# 跨模块联动: autosync 同步完 eigenflux_comm_messages 增量后 set(),
# 演化 daemon 内部 wait(timeout=600) —— 要么被唤醒, 要么 10min 周期.
# 这是拉马努金式自举循环的关键: AI 员工跨机讨论 → 同步 → 立刻摄入脑库 → 立刻关联图谱 → 立刻衍生
EVOLUTION_WAKEUP_EVENT = threading.Event()
_last_trigger_ts = 0.0
_trigger_count = 0

def trigger_evolution(reason: str = "manual") -> bool:
    """
    触发演化 daemon 提前跑一轮.
    带冷却 (min_interval=30s), 避免 autosync 高频同步时打爆演化.
    返回 True = 唤醒信号已发送, False = 冷却中被跳过.
    """
    global _last_trigger_ts, _trigger_count
    now = time.time()
    min_interval = 30.0  # 两次触发至少隔 30s
    if now - _last_trigger_ts < min_interval:
        logger.info(f"[EVOL-WAKE] 冷却中 ({now - _last_trigger_ts:.1f}s < {min_interval}s), 跳过触发 (reason={reason})")
        return False
    _last_trigger_ts = now
    _trigger_count += 1
    EVOLUTION_WAKEUP_EVENT.set()
    logger.info(f"[EVOL-WAKE] 🔔 演化唤醒信号已发送! reason={reason}, 累计触发={_trigger_count}")
    return True

def reset_evolution_event():
    """演化 daemon 跑完一轮后调这个清掉唤醒信号."""
    EVOLUTION_WAKEUP_EVENT.clear()

# --- 路径配置 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get(
    'ANDROMEDA_DB',
    os.path.join(PROJECT_ROOT, 'database', 'app.db'),
)
# 注意: engines/andromeda_auto_evolution.py → PROJECT_ROOT = flask-app/
# RUNTIME_DIR 应该是 flask-app/ai_engines/_runtime/ (和 fusion_adapter 一致)
RUNTIME_DIR = os.environ.get(
    'ANDROMEDA_RUNTIME',
    os.path.join(PROJECT_ROOT, 'ai_engines', '_runtime'),
)
CHECKPOINT_FILE = os.path.join(RUNTIME_DIR, 'evolution_checkpoint.json')

# --- Ollama 配置 ---
# 🆕 2026-09-17: 统一 11435 (launch agent 原生 Ollama, Metal iGPU + q8_0 KV cache)
# 之前默认 11434 走 CLI 实例, embedding 慢 35 倍 (0.4s vs 14.2s)
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11435')
EMBED_MODEL = os.environ.get('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
OLLAMA_TIMEOUT = 120  # 大模型推理慢

# 🆕 2026-09-17: Volcengine 方舟 ARK 兜底 (Ollama 挂了自动切云端)
# 见 ai_engines/ai_volcengine_engine.py — 已实现 smart fallback
_VOLCENGINE_FALLBACK = True  # 开启云端兜底 (消耗 token)

# 🔀 智能择优选择本地大模型
# 优先级: OLLAMA_DERIVE_MODEL 显式覆盖 > 硬件自动检测+Ollama已装模型择优 > 默认 7b
def _detect_machine_tier() -> str:
    """
    检测当前机器档位: 'dev' (开发机 MacBook Pro) | 'light' (Mac mini/其他)
    依据: hostname + sysctl hw.model
    """
    hostname = os.environ.get('HOSTNAME', '')
    hw_model = ''
    try:
        import subprocess as _sp
        hw_model = _sp.run(['sysctl', '-n', 'hw.model'], capture_output=True,
                           text=True, timeout=2).stdout.strip()
    except Exception:
        pass
    if ('MacBookPro' in hostname
            or any(tag in hw_model for tag in ['Mac16', 'Mac17', 'Mac18', 'Mac19', 'Mac20'])):
        return 'dev'
    return 'light'


def _ollama_list_models() -> set:
    """
    调用 Ollama API 获取已装模型名集合。
    失败返回空集合（安全降级）。
    """
    models = set()
    try:
        req = urllib.request.Request(f'{OLLAMA_HOST}/api/tags')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for m in data.get('models', []):
                name = m.get('name', '').split(':')[0]  # qwen2.5:14b → qwen2.5
                models.add(name)
                models.add(m.get('name', ''))          # qwen2.5:14b (完整带 tag)
    except Exception:
        pass
    return models


def _pick_best_derive_model() -> str:
    """
    智能择优:
      dev 档  → 优先 14b → 13b → 12b → 7b → 默认 7b
      light 档 → 优先 7b → 9b → 默认 7b
      显式环境变量 OLLAMA_DERIVE_MODEL 最优先
    """
    if 'OLLAMA_DERIVE_MODEL' in os.environ:
        return os.environ['OLLAMA_DERIVE_MODEL']

    tier = _detect_machine_tier()
    available = _ollama_list_models()

    # 候选列表 (按优先级排序)
    if tier == 'dev':
        candidates = [
            'qwen2.5:14b', 'qwen2.5:13b', 'qwen2.5:12b', 'qwen2.5:7b',
            'qwen2:14b', 'qwen2:7b', 'llama3.1:8b',
        ]
    else:
        candidates = [
            'qwen2.5:7b', 'qwen2.5:9b', 'qwen2:7b', 'llama3.1:8b',
        ]

    for cand in candidates:
        if cand in available:
            return cand

    # 兜底: 开发机兜底 14b, 轻量机兜底 7b (假设已装)
    return 'qwen2.5:14b' if tier == 'dev' else 'qwen2.5:7b'


DERIVE_MODEL = _pick_best_derive_model()
_MACHINE_TIER = _detect_machine_tier()

# --- 阈值配置 (可通过 checkpoint 动态调整) ---
DEFAULTS = {
    # 七阶段核心配置
    'similarity_threshold': 0.60,    # 低于此值不关联 (自适应)
    'reinforce_threshold': 0.80,     # 高于此值强化已有知识
    'batch_size': 50,                # 每轮处理的新增行数
    'max_associations_per_item': 5,   # 每条新知识最多关联几条
    'top_k_search': 10,              # 语义检索 top_k
    'derive_enabled': True,          # 是否开启衍生 (耗 LLM tokens)
    'reinforce_enabled': True,       # 是否开启强化

    # Checkpoint (脑库知识增量)
    'last_knowledge_id': None,
    'created_at_checkpoint': 0.0,

    # 🆕 EigenFlux 摄入 (AI 员工交流 → 脑库)
    'eigenflux_ingest_enabled': True,
    'eigenflux_last_msg_id': 0,       # mt_ai_eigenflux_messages.msg_id 增量
    'eigenflux_total_ingested': 0,    # 累计摄入的 EigenFlux 消息数

    # Cycle 累计
    'cycle_count': 0,
    'total_vectors': 0,
    'total_derived': 0,
    'total_associations': 0,
    'total_reinforced': 0,
}


# ============================================================
# 基础设施 (checkpoint / Ollama / DB)
# ============================================================

def _load_checkpoint() -> Dict:
    """加载 checkpoint (不存在则返回 DEFAULTS)"""
    cp = dict(DEFAULTS)
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            cp.update(saved)
    except Exception as e:
        logger.warning(f'checkpoint load failed: {e}, using defaults')
    return cp


def _save_checkpoint(cp: Dict) -> None:
    """保存 checkpoint (原子写)"""
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        tmp = CHECKPOINT_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(cp, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CHECKPOINT_FILE)
    except Exception as e:
        logger.error(f'checkpoint save failed: {e}')


def _ollama_embed(text: str) -> Optional[List[float]]:
    """Ollama embedding — nomic-embed-text"""
    if not text or not text.strip():
        return None
    try:
        payload = json.dumps({
            'model': EMBED_MODEL,
            'prompt': text[:4096],
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
        logger.warning(f'ollama_embed failed: {e}')
        return None


def _ollama_chat(prompt: str, system: str = '你是仙女座 AI 系统的知识衍生专家。') -> Optional[str]:
    """
    Ollama chat — 开发机优先 14b, 失败自动降级 7b, 再失败走火山引擎.
    
    兜底链路 (开发机):
      1. qwen2.5:14b (主力, 更深推理)
      2. qwen2.5:7b  (兜底, 更快)
      3. Volcengine ARK (云端兜底, 消耗 token)
    
    轻量机直接 7b → Volcengine.
    """
    # 🆕 2026-09-17: 开发机双重兜底链路
    candidates = [DERIVE_MODEL]  # 主力
    if _MACHINE_TIER == 'dev':
        # 开发机 dev 档: 主力 14b → 兜底 7b → 云端
        fallback = 'qwen2.5:7b'
        if fallback not in candidates and fallback in _ollama_list_models():
            candidates.append(fallback)
    
    for idx, model in enumerate(candidates):
        try:
            payload = json.dumps({
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': prompt[:12000]},
                ],
                'stream': False,
                'options': {'temperature': 0.4},
            }).encode('utf-8')
            req = urllib.request.Request(
                f'{OLLAMA_HOST}/api/chat',
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                result = data.get('message', {}).get('content', '')
                if idx > 0:
                    logger.info(f'[ollama-chat] 降级成功 {candidates[0]} → {model}')
                return result
        except Exception as e:
            logger.warning(f'ollama_chat failed ({model}): {e}')
            continue  # 试下一个 candidate

    # 🆕 2026-09-17: Volcengine 方舟 ARK 兜底 (本地全挂)
    if _VOLCENGINE_FALLBACK:
        try:
            from ai_engines.ai_volcengine_engine import chat as ark_chat
            result = ark_chat(prompt[:12000], system=system,
                             flow_id=f"andromeda_derive_{int(time.time())}")
            if result.get('success'):
                logger.info(f'[ollama-chat] → 火山引擎兜底成功: model={result.get("model")}')
                return result.get('response', '')
            else:
                logger.warning(f'[ollama-chat] → 火山引擎也失败: {result.get("error")}')
        except Exception as ark_err:
            logger.warning(f'[ollama-chat] → volcengine import/调用失败: {ark_err}')
    return None


def _get_conn() -> sqlite3.Connection:
    """DB 连接 (WAL + timeout)"""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.row_factory = sqlite3.Row
    # SQLite 不内置 REGEXP, 用 Python re 注册一个
    import re as _re
    conn.create_function('REGEXP', 2, lambda pattern, text:
                         1 if text and _re.search(pattern, text) else 0)
    return conn


def _load_rule_constraints(max_rules: int = 6, per_rule: int = 3) -> str:
    """
    从 mt_andromeda_rule_knowledge 提取强制约束词段落,
    用于注入 auto_derive / auto_reinforce 的 system prompt,
    让仙女座演化方向始终受规则约束驱动.

    取强制关键词 (必须/禁止/严禁/不得/强制) 命中的分块,
    每篇规则取 top per_rule 条, 共 max_rules 篇.
    返回一段可以直接拼接进 prompt 的文本.
    """
    try:
        conn = _get_conn()
        rows = conn.execute(f"""
            SELECT rule_id, content_chunk FROM mt_andromeda_rule_knowledge
            WHERE content_chunk REGEXP '必须|禁止|严禁|不得|强制|严禁|不可|务必|严格'
            ORDER BY LENGTH(content_chunk) DESC
            LIMIT {max_rules * per_rule}
        """).fetchall()
        if not rows:
            conn.close()
            return ''
        # 按 rule_id 聚合, 每篇规则取前 per_rule 条
        grouped: Dict[str, list] = {}
        for r in rows:
            rid = r[0]
            if rid not in grouped:
                grouped[rid] = []
            if len(grouped[rid]) < per_rule:
                grouped[rid].append(r[1])
        conn.close()
        parts = []
        for rid, chunks in grouped.items():
            body = ' | '.join(c[:120] for c in chunks)
            parts.append(f'[{rid}] {body}')
        return '\n'.join(parts)
    except Exception as e:
        # 非阻断: 规则约束注入失败, 仙女座照常跑
        logger.debug(f'[rule_constraints] 提取失败 (非阻断): {e}')
        return ''


def _cosine(a: List[float], b: List[float]) -> float:
    """numpy 加速余弦相似度"""
    try:
        q = np.array(a, dtype=np.float32)
        c = np.array(b, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-10)
        c = c / (np.linalg.norm(c) + 1e-10)
        return float(q @ c)
    except Exception:
        return 0.0


# ============================================================
# 🆕 Stage 0: eigenflux_ingest — EigenFlux AI 员工交流 → 脑库知识
#
# 设计: AI 员工在 EigenFlux network 上互相交流产生的消息,
#       是极其宝贵的"活知识"——比静态脑库更有即时性和关联性。
#       每条消息自动包装成脑库条目写入 ai_brain_enhanced_knowledge,
#       然后参与 Stage 1-7 的完整自演化循环。
#
# 增量策略: msg_id > checkpoint.eigenflux_last_msg_id
# 消息来源 (双表兼容, 哪个有数据用哪个):
#   1. mt_ai_eigenflux_messages (ai_eigenflux_network_engine 自动建)
#   2. eigenflux_messages (Flask eigenflux_routes 用的旧表)
# ============================================================

def eigenflux_ingest(cp: Dict) -> Dict[str, Any]:
    """
    从 EigenFlux 消息表抓新消息 → 写 ai_brain_enhanced_knowledge。
    返回: {'ingested': int, 'skipped': int, 'sources': [...]}
    """
    if not cp.get('eigenflux_ingest_enabled', True):
        logger.info('[Stage0-eigenflux] disabled by config')
        return {'ingested': 0, 'skipped': 0, 'sources': []}

    result = {'ingested': 0, 'skipped': 0, 'sources': []}

    try:
        conn = _get_conn()

        # 探测可用的消息表 (多表兼容, 哪个有数据用哪个)
        # 智能过滤策略:
        #   ① mt_ai_eigenflux_messages: learning_value > 0 OR knowledge_tags_json != '[]' OR LENGTH(content) > 50
        #   ② eigenflux_comm_messages:   learning_value > 0 OR message_type != 'CHAT' OR LENGTH(message_content) > 50
        #   ③ eigenflux_messages:        简单 LENGTH(content) > 50
        # 同时排除 source='auto_derived' 防止 Stage 4 衍生知识被循环摄入
        candidate_tables = [
            # (表名, id列, content列, sender列, receiver列, topic列, learning_value列, tags列, 智能过滤SQL片段)
            ('mt_ai_eigenflux_messages', 'msg_id', 'content', 'sender_name', 'receiver_name', 'topic_key',
             'learning_value', 'knowledge_tags_json',
             '(learning_value > 0 OR knowledge_tags_json != \'[]\' OR LENGTH(content) > 50)'),
            ('eigenflux_messages', 'message_id', 'content', 'sender_id', 'receiver_id', 'topic',
             None, None,
             'LENGTH(content) > 50'),
            # eigenflux_comm_messages 结构不同: id / message_content / employee_name
            ('eigenflux_comm_messages', 'id', 'message_content', 'employee_name', 'employee_name', 'message_type',
             'learning_value', None,
             '(learning_value > 0 OR message_type != \'CHAT\' OR LENGTH(message_content) > 50)'),
        ]

        for entry in candidate_tables:
            table_name, id_col, content_col, sender_col, receiver_col, topic_col, lv_col, tags_col, smart_filter = entry
            # 检查表是否存在
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            ).fetchone()
            if not exists:
                continue

            # 取增量消息 + 智能过滤 (先不过滤 auto_derived——后面处理)
            last_id = cp.get('eigenflux_last_msg_id', 0)

            # 构建动态 SQL
            select_cols = [id_col, content_col, sender_col, receiver_col, topic_col]
            if lv_col:
                select_cols.append(lv_col)
            if tags_col:
                select_cols.append(tags_col)
            select_cols.append('created_at')

            # 可选 source 列 (防反向循环)
            try:
                has_source = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
                source_col_exists = any(c[1] == 'source' for c in has_source) or any(c[1] == 'origin' for c in has_source)
            except Exception:
                source_col_exists = False

            where_parts = [f'{id_col} > ?']
            # 智能过滤
            if smart_filter:
                where_parts.append(smart_filter)
            # 防反向循环
            # 🆕 2026-09-16: 放宽防循环策略, 允许 DERIVED_KNOWLEDGE / DISCUSSION 反向驱动演化
            # 之前排除所有 DERIVED_KNOWLEDGE 导致: 演化产出永远不入脑库 → 无法形成自举循环
            # 现在只排除明确标记为 source='auto_derived' 的 (AI 自己写回的衍生知识)
            # DISCUSSION (AI 员工围绕新知识展开讨论) 要摄入 → 反过来驱动下一轮演化
            anti_loop_parts = []
            if source_col_exists:
                anti_loop_parts.append("(source IS NULL OR source != 'auto_derived')")
            # 🆕 去掉了 message_type != 'DERIVED_KNOWLEDGE' — 演化产出的 DISCUSSION 反向驱动
            # 🆕 去掉了 knowledge_tags_json NOT LIKE '%auto_derived%' — 同理
            if anti_loop_parts:
                where_parts.append(' AND '.join(anti_loop_parts))

            where_sql = ' AND '.join(where_parts)
            sql = f"""
                SELECT {', '.join(select_cols)}
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY {id_col} ASC
                LIMIT 200
            """

            try:
                rows = conn.execute(sql, (last_id,)).fetchall()
            except sqlite3.Error as e:
                logger.warning(f'[Stage0-eigenflux] query {table_name} failed: {e}')
                continue

            if not rows:
                logger.info(f'[Stage0-eigenflux] {table_name}: 无新消息 (last_id={last_id})')
                continue

            logger.info(f'[Stage0-eigenflux] {table_name}: 发现 {len(rows)} 条新消息 (last_id={last_id})')
            result['sources'].append({'table': table_name, 'count': len(rows)})

            new_max_id = last_id

            for row in rows:
                # 动态解析列
                col_values = list(row)
                msg_id = col_values[0]
                content = (col_values[1] or '').strip()
                sender = col_values[2] or 'unknown'
                receiver = col_values[3] or 'unknown'
                topic = col_values[4] or 'general'
                # learning_value 和 tags 跳过, 直接用
                created_at_str = col_values[-1] if col_values else ''

                if not content or len(content) < 5:
                    result['skipped'] += 1
                    continue

                # 构造 knowledge_id (防重入)
                knowledge_id = f'EIGENFLUX-{table_name}-{msg_id}'

                # 检查是否已存在
                existing = conn.execute(
                    "SELECT 1 FROM ai_brain_enhanced_knowledge WHERE knowledge_id=?",
                    (knowledge_id,)
                ).fetchone()
                if existing:
                    result['skipped'] += 1
                    continue

                # 解析 created_at
                try:
                    # 可能是 'YYYY-MM-DD HH:MM:SS' 或 epoch float
                    if isinstance(created_at_str, str) and created_at_str:
                        from datetime import datetime
                        ts = datetime.strptime(created_at_str[:19], '%Y-%m-%d %H:%M:%S').timestamp()
                    elif isinstance(created_at_str, (int, float)):
                        ts = float(created_at_str)
                    else:
                        ts = time.time()
                except Exception:
                    ts = time.time()

                now_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
                            (knowledge_id, category, title, content, knowledge_type, tags,
                             confidence_score, usage_count, is_active, created_at, updated_at)
                        VALUES (?, 'eigenflux', ?, ?, 'eigenflux_message', ?, 0.65, 0, 1, ?, ?)
                    """, (
                        knowledge_id,
                        f'[EigenFlux] {sender} → {receiver}: {str(topic)[:60]}',
                        content[:2000],
                        json.dumps(['eigenflux', f'from_{sender}', f'to_{receiver}',
                                   f'topic_{topic}'], ensure_ascii=False),
                        ts, ts,
                    ))
                    result['ingested'] += 1
                except sqlite3.IntegrityError:
                    result['skipped'] += 1

                new_max_id = max(new_max_id, int(msg_id))

            # 更新 checkpoint
            if new_max_id > cp.get('eigenflux_last_msg_id', 0):
                cp['eigenflux_last_msg_id'] = new_max_id

        conn.commit()
        conn.close()

        cp['eigenflux_total_ingested'] = cp.get('eigenflux_total_ingested', 0) + result['ingested']

        logger.info(
            f'[Stage0-eigenflux] ingested={result["ingested"]}, '
            f'skipped={result["skipped"]}, total={cp["eigenflux_total_ingested"]}'
        )
        return result

    except Exception as e:
        logger.error(f'[Stage0-eigenflux] failed: {e}')
        return {'ingested': 0, 'skipped': 0, 'sources': [], 'error': str(e)}


# ============================================================
# Stage 1: auto_detect — 扫描新增脑库数据
# ============================================================

def auto_detect(cp: Dict) -> List[sqlite3.Row]:
    """
    增量扫描 ai_brain_enhanced_knowledge 中 created_at > checkpoint 的新行。
    每轮最多取 batch_size 条。
    """
    try:
        conn = _get_conn()
        checkpoint_ts = cp.get('created_at_checkpoint', 0.0)
        batch_size = cp.get('batch_size', 20)

        rows = conn.execute("""
            SELECT * FROM ai_brain_enhanced_knowledge
            WHERE is_active = 1
              AND COALESCE(created_at, 0) > ?
            ORDER BY COALESCE(created_at, 0) ASC
            LIMIT ?
        """, (checkpoint_ts, batch_size)).fetchall()
        conn.close()

        if rows:
            logger.info(f'[Stage1-detect] 发现 {len(rows)} 条新增脑库知识')
        else:
            logger.info(f'[Stage1-detect] 无新增脑库知识 (checkpoint={checkpoint_ts})')

        return rows
    except Exception as e:
        logger.error(f'[Stage1-detect] failed: {e}')
        return []


# ============================================================
# Stage 2: auto_retrieve — 向量化 + 语义检索关联
# ============================================================

def auto_retrieve(new_items: List[sqlite3.Row], cp: Dict) -> Dict[str, Any]:
    """
    对新行做 Ollama 向量化 → 写本地向量存储 → 语义检索已存在向量找关联。
    返回 {vectors: [...], associations: [(new_id, existing_id, sim)], embeds_ok: int, embeds_fail: int}
    """
    if not new_items:
        return {'vectors': [], 'associations': [], 'embeds_ok': 0, 'embeds_fail': 0}

    try:
        import sys as _sys
        # PROJECT_ROOT 已经是 flask-app/, 直接加进去即可
        if PROJECT_ROOT not in _sys.path:
            _sys.path.insert(0, PROJECT_ROOT)
        from ai_engines.fusion_adapter import (
            _ensure_vector_db, vector_store_upsert, vector_store_search,
        )

        _ensure_vector_db()
        threshold = cp.get('similarity_threshold', 0.65)
        top_k = cp.get('top_k_search', 10)
        max_assoc = cp.get('max_associations_per_item', 5)

        vectors = []       # (knowledge_id, vec)
        associations = []  # [(new_kid, existing_kid, similarity), ...]
        ok = 0
        fail = 0

        for row in new_items:
            kid = row['knowledge_id']
            content = (row['content'] or row['title'] or '')[:4096]
            if not content.strip():
                fail += 1
                continue

            vec = _ollama_embed(content)
            if not vec:
                fail += 1
                continue
            ok += 1
            vectors.append((kid, vec))

            # 写本地向量存储
            vector_store_upsert([
                ('ai_brain_enhanced_knowledge', kid, content, vec)
            ])

            # 语义检索已存在向量 (排除自己)
            results = vector_store_search(vec, top_k=top_k + 10)
            count = 0
            for r in results:
                if count >= max_assoc:
                    break
                if r['source_id'] == kid:
                    continue
                if r['similarity'] >= threshold:
                    associations.append((kid, r['source_id'], r['similarity']))
                    count += 1

        logger.info(f'[Stage2-retrieve] embeds_ok={ok}, embeds_fail={fail}, associations={len(associations)}')
        return {
            'vectors': vectors,
            'associations': associations,
            'embeds_ok': ok,
            'embeds_fail': fail,
        }
    except Exception as e:
        logger.error(f'[Stage2-retrieve] failed: {e}')
        return {'vectors': [], 'associations': [], 'embeds_ok': 0, 'embeds_fail': 0}


# ============================================================
# Stage 3: auto_associate — 写知识图谱关系
# ============================================================

def auto_associate(associations: List[Tuple[str, str, float]],
                   new_items: List[sqlite3.Row]) -> int:
    """
    把关联提案写入 knowledge_graph_relations + knowledge_graph_nodes (如节点不存在)。
    去重: 同 (source, target, type) 不重复写。
    返回写入的新关系数。
    """
    if not associations:
        return 0

    try:
        conn = _get_conn()
        written = 0
        now = time.time()

        # 收集所有涉及的 knowledge_id
        all_kids = set()
        new_kids_info = {}  # kid -> row
        for row in new_items:
            all_kids.add(row['knowledge_id'])
            new_kids_info[row['knowledge_id']] = row
        for a in associations:
            all_kids.add(a[0])
            all_kids.add(a[1])

        # 确保 knowledge_graph_nodes 里有这些条目
        existing_nodes = {
            r['node_name']: r for r in conn.execute(
                "SELECT node_name FROM knowledge_graph_nodes WHERE node_type='knowledge'"
            ).fetchall()
        }

        for kid in all_kids:
            if kid in existing_nodes:
                continue
            info = new_kids_info.get(kid)
            content = ''
            node_type = 'knowledge'
            if info:
                content = (info['content'] or info['title'] or '')[:500]
                node_type = info['knowledge_type'] or 'knowledge'
            else:
                # 查脑库
                r = conn.execute(
                    "SELECT content, title, knowledge_type FROM ai_brain_enhanced_knowledge WHERE knowledge_id=?",
                    (kid,)
                ).fetchone()
                if r:
                    content = (r['content'] or r['title'] or '')[:500]
                    node_type = r['knowledge_type'] or 'knowledge'

            node_id = f'NODE-{uuid.uuid4().hex[:12]}'
            now_real = now
            try:
                conn.execute("""
                    INSERT INTO knowledge_graph_nodes
                        (node_id, node_name, node_type, content, metadata, importance_score, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    node_id, kid, node_type, content,
                    json.dumps({'source': 'auto_associate'}, ensure_ascii=False),
                    0.5, now_real, now_real,
                ))
                existing_nodes[kid] = {'node_name': kid, 'node_id': node_id}
            except sqlite3.IntegrityError:
                pass

        # 写 relations
        node_name_to_id = {}
        for r in conn.execute("SELECT node_id, node_name FROM knowledge_graph_nodes").fetchall():
            node_name_to_id[r['node_name']] = r['node_id']

        for src_kid, tgt_kid, sim in associations:
            src_nid = node_name_to_id.get(src_kid)
            tgt_nid = node_name_to_id.get(tgt_kid)
            if not src_nid or not tgt_nid:
                continue

            # 去重检查
            dup = conn.execute("""
                SELECT 1 FROM knowledge_graph_relations
                WHERE source_node_id=? AND target_node_id=? AND relation_type='semantic_association'
            """, (src_nid, tgt_nid)).fetchone()
            if dup:
                continue

            rel_id = f'REL-{uuid.uuid4().hex[:12]}'
            try:
                conn.execute("""
                    INSERT INTO knowledge_graph_relations
                        (relation_id, source_node_id, target_node_id, relation_type, weight, description, is_active, created_at)
                    VALUES (?, ?, ?, 'semantic_association', ?, ?, 1, ?)
                """, (
                    rel_id, src_nid, tgt_nid,
                    round(float(sim), 4),
                    f'自动联想: 相似度 {round(float(sim), 3)}',
                    now,
                ))
                written += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()
        logger.info(f'[Stage3-associate] 写入 {written} 条新关联关系')
        return written
    except Exception as e:
        logger.error(f'[Stage3-associate] failed: {e}')
        return 0


# ============================================================
# Stage 4: auto_derive — 衍生新知识
# ============================================================

def auto_derive(associations: List[Tuple[str, str, float]],
                new_items: List[sqlite3.Row], cp: Dict) -> int:
    """
    对高相似度关联 (>= reinforce_threshold) 调 Ollama 做知识衍生:
      prompt: "知识A + 知识B → 衍生: ..."
    衍生结果写入 ai_brain_enhanced_knowledge (knowledge_type='derived')。
    返回衍生条目数。
    """
    if not cp.get('derive_enabled', True):
        logger.info('[Stage4-derive] disabled by config')
        return 0
    if not associations:
        return 0

    # ── 注入规则约束: mt_andromeda_rule_knowledge 里的强制约束词 ──
    _rule_constraints = _load_rule_constraints()
    if _rule_constraints:
        logger.info(f'[Stage4-derive] 📜 加载规则约束词 ({len(_rule_constraints)} chars)')
    derive_system = (
        '你是仙女座 AI 知识衍生专家。只输出 JSON，不要其他文字。'
        + ('\n\n【必须遵守的系统规则约束】\n' + _rule_constraints
           if _rule_constraints else '')
    )

    # 只取高相似度的关联 + top 限制 (避免 14b 推理 250 次太慢)
    threshold = cp.get('reinforce_threshold', 0.80)
    high_sim = [(s, t, sim) for s, t, sim in associations if sim >= threshold]
    # 按相似度降序, 取 top N (14b=80, 7b=120)
    is_large = _MACHINE_TIER == 'dev' and '14b' in DERIVE_MODEL
    top_n = cp.get('derive_top_n', 80 if is_large else 120)
    high_sim.sort(key=lambda x: x[2], reverse=True)
    high_sim = high_sim[:top_n]

    if not high_sim:
        logger.info(f'[Stage4-derive] no high-sim associations (threshold={threshold})')
        return 0
    logger.info(f'[Stage4-derive] high-sim={len(high_sim)} (top_n={top_n}, model={DERIVE_MODEL})')

    try:
        conn = _get_conn()
        written = 0

        # 建 kid → content 映射
        kid_content = {}
        for row in new_items:
            kid_content[row['knowledge_id']] = (row['title'] or '') + ': ' + (row['content'] or '')[:300]
        # 从 DB 补已有的
        missing = [kid for a in high_sim for kid in [a[0], a[1]] if kid not in kid_content]
        if missing:
            placeholders = ','.join(['?'] * len(missing))
            for r in conn.execute(f"""
                SELECT knowledge_id, title, content FROM ai_brain_enhanced_knowledge
                WHERE knowledge_id IN ({placeholders})
            """, missing).fetchall():
                kid_content[r['knowledge_id']] = (r['title'] or '') + ': ' + (r['content'] or '')[:300]

        for src_kid, tgt_kid, sim in high_sim:
            src_text = kid_content.get(src_kid, '')
            tgt_text = kid_content.get(tgt_kid, '')
            if not src_text or not tgt_text:
                continue

            prompt = f"""基于以下两条知识，推导/衍生出一条新的洞见或关联知识:

知识 A ({src_kid}): {src_text}

知识 B ({tgt_kid}): {tgt_text}

(相似度 {round(sim, 3)})

请输出一条衍生知识，JSON 格式:
{{"title": "...", "content": "..."}}

要求:
1. content 必须是独立完整的句子，不能使用代词
2. 必须整合 A 和 B 的信息，不能只是重复
3. 控制在 200 字以内"""

            response = _ollama_chat(prompt, system=derive_system)
            if not response:
                continue

            # 解析 JSON (容错)
            try:
                # 找第一个 { 和最后一个 }
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(response[start:end])
                else:
                    continue
                title = (data.get('title') or '')[:100]
                content = (data.get('content') or '')[:500]
                if not title or not content:
                    continue
            except Exception:
                # 降级: 把整个 response 当 content
                title = f'自动衍生: {src_kid[:12]} ↔ {tgt_kid[:12]}'
                content = response[:500]
                if not content:
                    continue

            # 写脑库
            new_kid = f'AE-{uuid.uuid4().hex[:12]}'
            now = time.time()
            tags_list = ['auto_derived', src_kid, tgt_kid, f'sim_{round(sim,2)}']
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
                        (knowledge_id, category, title, content, knowledge_type, tags,
                         confidence_score, usage_count, is_active, created_at, updated_at)
                    VALUES (?, 'auto_derive', ?, ?, 'derived', ?, 0.7, 0, 1, ?, ?)
                """, (
                    new_kid, title, content,
                    json.dumps(tags_list, ensure_ascii=False),
                    now, now,
                ))
                written += 1

                # 🆕 反向驱动: 衍生知识 → EigenFlux 消息表 (给 AI 员工讨论!)
                # 写入 eigenflux_comm_messages, knowledge_tags_json 包含 'auto_derived'
                # eigenflux_ingest 的防循环: knowledge_tags_json LIKE '%auto_derived%' 时跳过
                # 表结构: id, session_id, employee_id, employee_name, employee_table,
                #         message_direction, message_type, message_content,
                #         knowledge_tags_json, learning_value, created_at
                try:
                    # 找一个活跃的 AI 员工作为 "发送者"
                    # mt_andromeda_employee_registry: employee_id, name, level, enabled
                    emp = conn.execute("""
                        SELECT name, 'mt_andromeda_employee_registry', employee_id
                        FROM mt_andromeda_employee_registry
                        WHERE enabled=1 ORDER BY level DESC LIMIT 1
                    """).fetchone()
                    if not emp:
                        emp = conn.execute("""
                            SELECT name, 'ai_employees', id FROM ai_employees WHERE status='active' LIMIT 1
                        """).fetchone()

                    sender_name = emp[0] if emp else '仙女座-自演化'
                    sender_table = emp[1] if emp else 'system'
                    emp_id = emp[2] if emp else 0

                    # 找一个已有 session (或 NULL)
                    # 注意: eigenflux_comm_sessions 主键是 id, 不是 session_id
                    session = conn.execute(
                        "SELECT id FROM eigenflux_comm_sessions ORDER BY rowid DESC LIMIT 1"
                    ).fetchone()
                    session_id = session[0] if session else 0

                    # 反向驱动消息内容: 带 "source=auto_derived" 标记
                    rev_content = f'[AUTO_DERIVED] {title}\n\n{content}\n\n(源自 {src_kid} ↔ {tgt_kid}, 相似度 {round(sim, 3)})'
                    conn.execute("""
                        INSERT INTO eigenflux_comm_messages
                            (session_id, employee_id, employee_name, employee_table,
                             message_direction, message_type, message_content,
                             knowledge_tags_json, learning_value, created_at)
                        VALUES (?, ?, ?, ?, 'inbound', 'DERIVED_KNOWLEDGE', ?, ?, 5, ?)
                    """, (
                        session_id, emp_id, sender_name, sender_table,
                        rev_content,
                        json.dumps(tags_list, ensure_ascii=False),
                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)),
                    ))
                except sqlite3.Error as rev_err:
                    logger.debug(f'[Stage4-derive] 反向驱动跳过 (非致命): {rev_err}')
                    pass

            except sqlite3.IntegrityError:
                pass

        conn.commit()
        conn.close()
        logger.info(f'[Stage4-derive] 衍生 {written} 条新知识')
        return written
    except Exception as e:
        logger.error(f'[Stage4-derive] failed: {e}')
        return 0


# ============================================================
# Stage 4.5: ai_employees_discuss_derived — AI 员工讨论衍生知识
# ============================================================

# employee_type → 角色 system prompt
_EMPLOYEE_ROLE_PROMPTS = {
    # 核心工程
    'code_reviewer':              '你是资深代码审查专家。擅长从代码质量、安全漏洞、设计模式、边界条件角度深入讨论。',
    'security_analyst':           '你是安全分析师。擅长从威胁模型、漏洞链、权限绕过、输入注入角度深入讨论。',
    'perf_engineer':              '你是性能工程师。擅长从性能瓶颈、资源优化、并发模型、内存管理角度深入讨论。',
    'planner':                    '你是架构规划师。擅长从整体架构、可行性评估、演进路径、技术债务角度深入讨论。',
    'system_analyzer':            '你是系统分析师。擅长从系统一致性、边界条件、异常处理、数据流角度深入讨论。',
    'system_upgrader':            '你是系统升级专家。擅长从版本兼容、数据迁移、灰度发布、回滚预案角度深入讨论。',
    'scheduler':                  '你是调度专家。擅长从任务编排、资源分配、优先级、deadlock 避免角度深入讨论。',
    'dependency_analyst':         '你是依赖分析专家。擅长从依赖冲突、版本安全、替代方案、升级建议角度深入讨论。',
    'api_tester':                 '你是 API 测试专家。擅长从接口契约、边界用例、异常响应、幂等性角度深入讨论。',
    'network_engineer':           '你是网络工程师。擅长从协议设计、超时重试、连接管理、安全传输角度深入讨论。',
    'knowledge_curator':          '你是知识策展人。擅长从知识体系构建、分类关联、冗余消解、质量分级角度深入讨论。',
    'system_learner':             '你是系统学习专家。擅长从自动标注、主动学习、课程学习、持续学习角度深入讨论。',

    # Arduino / IoT 硬件方向（对跨学科观点补充硬件落地视角）
    'arduino_hal_developer':      '你是 Arduino HAL 开发专家。擅长从硬件抽象层、寄存器操作、驱动适配角度讨论硬件实现路径。',
    'arduino_peripheral_driver':  '你是 Arduino 外设驱动专家。擅长从传感器/执行器驱动、总线协议、时序要求角度讨论硬件接口。',
    'arduino_smart_advisor':      '你是 Arduino 智能顾问。擅长从教学引导、实验设计、学生常见错误角度讨论。',

    # 教育内容方向
    'education_researcher':      '你是教育研究专家。擅长从认知科学、学习效果评估、教学设计角度深入讨论。',
    'edu_analyst':                '你是教育数据分析专家。擅长从学情分析、知识图谱在教育中的应用、学习路径优化角度讨论。',
    'curriculum_designer':        '你是课程设计专家。擅长从课程体系构建、知识点前后衔接、模块化教学角度讨论。',
    'content_curator':            '你是内容策展专家。擅长从教学内容编排、案例选择、实操性与理论平衡角度讨论。',

    # UI/UX 方向
    'ui_designer':                '你是 UI 设计师。擅长从视觉层次、交互流程、可用性、信息架构角度讨论用户体验。',
    'ux_researcher':              '你是 UX 研究员。擅长从用户画像、可用性测试、交互模式发现角度讨论。',
}


def _employee_role_system(employee_type: str) -> str:
    """根据 employee_type 生成角色 system prompt"""
    base = _EMPLOYEE_ROLE_PROMPTS.get(employee_type)
    if base:
        return base + ' 用中文简洁回复，3-5 句话，聚焦你的专业角度。'
    return f'你是一名 {employee_type} 方向的 AI 员工。请用中文简洁讨论，3-5 句话，聚焦你的专业视角。'


def ai_employees_discuss_derived(
    limit_per_derived: int = 4,
    max_derived_to_discuss: int = 3,
    cp: Optional[Dict] = None,
) -> int:
    """
    🆕 Stage 4.5 — AI 员工讨论最新 DERIVED_KNOWLEDGE

    流程:
      1. 取最新 max_derived_to_discuss 条 DERIVED_KNOWLEDGE（反向驱动写回的）
      2. 每条知识找 limit_per_derived 个不同专业方向的活跃 AI 员工
      3. 每个员工基于自己的 employee_type + 衍生知识 → ollama chat 生成讨论
      4. 讨论回复写回 eigenflux_comm_messages (type='DISCUSSION', learning_value=3)
      5. 智能过滤下次摄入自动放行（learning_value>0）→ 形成知识闭环

    防循环: message_type='DISCUSSION' != 'CHAT'，智能过滤自动放行；
           讨论内容不含 auto_derived 标签，Stage 0 不会跳过。
    """
    if cp and not cp.get('derive_enabled', True):
        return 0

    try:
        conn = _get_conn()

        # 1. 取最新的 DERIVED_KNOWLEDGE 消息
        derived_msgs = conn.execute("""
            SELECT id, employee_name, message_content, knowledge_tags_json
            FROM eigenflux_comm_messages
            WHERE message_type='DERIVED_KNOWLEDGE'
            ORDER BY id DESC
            LIMIT ?
        """, (max_derived_to_discuss,)).fetchall()

        if not derived_msgs:
            logger.debug('[Stage4.5-discuss] 暂无 DERIVED_KNOWLEDGE 可供讨论')
            conn.close()
            return 0

        # 2. 取活跃 AI 员工（按 employee_type 去重，不同专业）
        all_emps = conn.execute("""
            SELECT employee_id, name, employee_type, level
            FROM mt_andromeda_employee_registry
            WHERE enabled=1
            ORDER BY level DESC
        """).fetchall()

        # 按 employee_type 去重 —— 每个专业方向只取第一个（最高 level）
        seen_types = set()
        unique_emps = []
        for emp in all_emps:
            if emp['employee_type'] not in seen_types:
                seen_types.add(emp['employee_type'])
                unique_emps.append(emp)
            if len(unique_emps) >= 15:  # 上限 15 个不同专业方向（覆盖工程/硬件/教育/UI）
                break

        written = 0
        now = int(time.time())

        for dm in derived_msgs:
            derived_content = dm['message_content'] or ''
            # 提取 [AUTO_DERIVED] 里的知识摘要
            summary = derived_content.replace('[AUTO_DERIVED]', '').strip()[:500]

            # 选 limit_per_derived 个员工
            selected = unique_emps[:limit_per_derived]
            if not selected:
                continue

            # 3. 每个员工生成讨论
            for emp in selected:
                e_name = emp['name']
                e_type = emp['employee_type']
                e_id = emp['employee_id']
                role_system = _employee_role_system(e_type)

                discuss_prompt = f"""请从你的专业角度，讨论以下 AI 自动衍生的知识观点：

【衍生知识】
{summary}

请用中文回复：
1. 你对这个观点的评价（合理/存疑/需要补充什么证据）
2. 你的专业视角下，这个观点可以怎样落地或延伸
3. 如果有相关的反向例或边界条件，请指出

3-5 句话，简洁有力。"""

                reply = _ollama_chat(discuss_prompt, system=role_system)
                if not reply or len(reply.strip()) < 15:
                    continue

                # 4. 写回 eigenflux_comm_messages
                try:
                    session_row = conn.execute(
                        "SELECT id FROM eigenflux_comm_sessions ORDER BY rowid DESC LIMIT 1"
                    ).fetchone()
                    session_id = session_row['id'] if session_row else 0

                    conn.execute("""
                        INSERT INTO eigenflux_comm_messages
                            (session_id, employee_id, employee_name, employee_table,
                             message_direction, message_type, message_content,
                             knowledge_tags_json, learning_value, created_at)
                        VALUES (?, ?, ?, ?, 'inbound', 'DISCUSSION', ?, ?, 3, ?)
                    """, (
                        session_id, e_id, e_name, 'mt_andromeda_employee_registry',
                        reply.strip(),
                        json.dumps(['derived_discussion', e_type,
                                    f'derived_ref_{dm["id"]}'], ensure_ascii=False),
                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)),
                    ))
                    written += 1
                    logger.info(f'[Stage4.5-discuss] {e_name}({e_type}) → DISCUSSION (len={len(reply)})')
                except sqlite3.Error as ins_err:
                    logger.debug(f'[Stage4.5-discuss] 写入跳过: {ins_err}')

        conn.commit()
        conn.close()
        logger.info(f'[Stage4.5-discuss] AI 员工讨论完成: {written} 条 DISCUSSION')
        return written

    except Exception as e:
        logger.error(f'[Stage4.5-discuss] failed: {e}')
        return 0


# ============================================================
# Stage 5: auto_reinforce — 强化已有知识
# ============================================================

def auto_reinforce(new_items: List[sqlite3.Row], cp: Dict) -> int:
    """
    对被高频关联到的已有知识:
      - confidence_score += 0.05 (上限 1.0)
      - usage_count += 1
    返回强化了多少条。
    """
    if not cp.get('reinforce_enabled', True):
        logger.info('[Stage5-reinforce] disabled by config')
        return 0

    try:
        conn = _get_conn()

        # 统计: knowledge_graph_relations 中被引用次数
        ref_counts = conn.execute("""
            SELECT target_node_id, COUNT(*) as cnt
            FROM knowledge_graph_relations
            GROUP BY target_node_id
            HAVING cnt >= 2
        """).fetchall()

        reinforced = 0
        for row in ref_counts:
            target_nid = row['target_node_id']
            cnt = row['cnt']

            # 拿到 node_name (knowledge_id)
            node = conn.execute(
                "SELECT node_name FROM knowledge_graph_nodes WHERE node_id=?",
                (target_nid,)
            ).fetchone()
            if not node:
                continue
            kid = node['node_name']

            # 更新 confidence_score 和 usage_count
            cur = conn.execute(
                "SELECT confidence_score, usage_count FROM ai_brain_enhanced_knowledge WHERE knowledge_id=?",
                (kid,)
            ).fetchone()
            if cur:
                new_conf = min(1.0, (cur['confidence_score'] or 0.5) + 0.03 * min(cnt, 5))
                conn.execute("""
                    UPDATE ai_brain_enhanced_knowledge
                    SET confidence_score=?, usage_count=COALESCE(usage_count, 0)+1,
                        updated_at=?
                    WHERE knowledge_id=?
                """, (new_conf, time.time(), kid))
                reinforced += 1

        conn.commit()
        conn.close()
        logger.info(f'[Stage5-reinforce] 强化 {reinforced} 条知识')
        return reinforced
    except Exception as e:
        logger.error(f'[Stage5-reinforce] failed: {e}')
        return 0


# ============================================================
# Stage 6: auto_expand — 拓展建议
# ============================================================

def auto_expand(new_items: List[sqlite3.Row], reinforced_count: int, cp: Dict) -> int:
    """
    根据本轮演化结果，自动生成增强建议 (写入 ai_enhancement_suggestions):
      - 新脑库条目多 → 建议注册新 AI 员工处理该领域
      - 关联密度高 → 建议启动自动图谱整理
      - 强化多 → 建议增加该领域的 AI 员工数量
    """
    try:
        conn = _get_conn()
        written = 0
        now = time.time()

        # 建议 1: 新脑库条目 → 建议增强
        for row in new_items[:3]:  # 最多 3 条建议
            existing = conn.execute("""
                SELECT 1 FROM ai_enhancement_suggestions
                WHERE target_component=? AND status='PENDING'
            """, (f'brain:{row["knowledge_id"]}',)).fetchone()
            if existing:
                continue
            conn.execute("""
                INSERT INTO ai_enhancement_suggestions
                    (suggestion_type, target_component, description,
                     impact_score, difficulty, status, proposed_by, created_at)
                VALUES ('brain_enhance', ?, ?, 0.6, 'medium', 'PENDING',
                        'sys_andromeda_auto_evolution', ?)
            """, (
                f'brain:{row["knowledge_id"]}',
                f'新脑库条目 "{(row["title"] or row["content"] or "")[:60]}" 建议关联 AI 员工处理',
                now,
            ))
            written += 1

        # 建议 2: 强化多 → AI 员工注册建议
        if reinforced_count >= 3:
            existing = conn.execute("""
                SELECT 1 FROM ai_enhancement_suggestions
                WHERE suggestion_type='ai_employee_register' AND status='PENDING'
                  AND created_at > ?
            """, (now - 86400,)).fetchone()  # 一天内不重复
            if not existing:
                desc = '本轮强化 %d 条知识 → 建议注册 1-2 名 AI 员工聚焦该领域' % reinforced_count
                conn.execute("""
                    INSERT INTO ai_enhancement_suggestions
                        (suggestion_type, target_component, description,
                         impact_score, difficulty, status, proposed_by, created_at)
                    VALUES ('ai_employee_register', 'mt_andromeda_employee_registry',
                            ?, 0.7, 'medium', 'PENDING', 'sys_andromeda_auto_evolution', ?)
                """, (desc, now))
                written += 1

        conn.commit()
        conn.close()
        logger.info(f'[Stage6-expand] 生成 {written} 条拓展建议')
        return written
    except Exception as e:
        logger.error(f'[Stage6-expand] failed: {e}')
        return 0


# ============================================================
# Stage 7: auto_optimize — 记录 + 动态调整
# ============================================================

def auto_optimize(cp: Dict, stats: Dict[str, Any]) -> Dict:
    """
    - 写入 mt_ai_self_evolution_log (演化历史, 复用现有表结构)
    - 根据本轮表现动态调整阈值:
      - 如果 associations 为 0 但新行多 → 降低 similarity_threshold
      - 如果 derived 太多低质量 → 提高 reinforce_threshold
    """
    try:
        conn = _get_conn()
        now = time.time()

        # mt_ai_self_evolution_log 现有字段:
        # evolve_id, trigger_type, target_task, old_prompt, new_prompt,
        # rationale, approved_by, applied, created_at
        # 我们复用: trigger_type='auto_evolution', target_task=stage,
        #          rationale=详情 JSON, created_at=时间戳字符串
        # 注意: created_at 是 TEXT 类型
        for stage, items in stats.items():
            if stage in ('cycle', 'stages', 'elapsed_ms', 'skipped', 'optimize',
                         'detect', 'retrieve', 'associations', 'derived',
                         'reinforced', 'expand'):
                continue
            if not items:
                continue
            detail = json.dumps(items if isinstance(items, (dict, list)) else {'value': items},
                                ensure_ascii=False)[:500]
            try:
                conn.execute("""
                    INSERT INTO mt_ai_self_evolution_log
                        (trigger_type, target_task, rationale, applied, created_at)
                    VALUES (?, ?, ?, 1, ?)
                """, ('auto_evolution', f'cycle_{cp.get("cycle_count", 0)}_{stage}',
                      detail, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))))
            except sqlite3.Error:
                pass  # 表结构可能变了, 静默忽略

        # 写一条 cycle 总览
        summary = json.dumps({
            'cycle': cp.get('cycle_count', 0),
            'elapsed_ms': stats.get('elapsed_ms', 0),
            'detect': stats.get('detect', 0),
            'retrieve': stats.get('retrieve', 0),
            'associations': stats.get('associations', 0),
            'derived': stats.get('derived', 0),
            'reinforced': stats.get('reinforced', 0),
            'expand': stats.get('expand', 0),
            'thresholds': {
                'sim': cp.get('similarity_threshold'),
                'reinforce': cp.get('reinforce_threshold'),
            },
        }, ensure_ascii=False)[:500]
        try:
            conn.execute("""
                INSERT INTO mt_ai_self_evolution_log
                    (trigger_type, target_task, rationale, applied, created_at)
                VALUES (?, ?, ?, 1, ?)
            """, ('auto_evolution', f'cycle_{cp.get("cycle_count", 0)}_summary',
                  summary, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))))
        except sqlite3.Error:
            pass

        conn.commit()
        conn.close()

        # --- 动态阈值调整 ---
        thresholds_changed = []
        new_sim = cp.get('similarity_threshold', 0.65)
        new_reinforce = cp.get('reinforce_threshold', 0.80)

        new_count = stats.get('detect', 0)
        assoc_count = stats.get('associations', 0)
        derived_count = stats.get('derived', 0)

        # 新行多但关联为 0 → 降低相似度阈值
        if new_count >= 10 and assoc_count == 0 and new_sim > 0.55:
            new_sim = round(new_sim - 0.05, 2)
            thresholds_changed.append(f'similarity_threshold: {cp["similarity_threshold"]} → {new_sim}')

        # 无衍生产出但有高相似度关联 → 降低 reinforce_threshold
        if assoc_count >= 5 and derived_count == 0 and new_reinforce > 0.70:
            new_reinforce = round(new_reinforce - 0.05, 2)
            thresholds_changed.append(f'reinforce_threshold: {cp["reinforce_threshold"]} → {new_reinforce}')

        cp['similarity_threshold'] = new_sim
        cp['reinforce_threshold'] = new_reinforce

        if thresholds_changed:
            logger.info(f'[Stage7-optimize] 阈值自动调整: {"; ".join(thresholds_changed)}')

        logger.info(f'[Stage7-optimize] 日志已记录, 阈值: sim={new_sim}, reinforce={new_reinforce}')
        return {'thresholds_changed': thresholds_changed, 'final_sim': new_sim, 'final_reinforce': new_reinforce}
    except Exception as e:
        logger.error(f'[Stage7-optimize] failed: {e}')
        return {'thresholds_changed': [], 'error': str(e)}


# ============================================================
# 主入口: run_cycle — 七阶段串联
# ============================================================

def run_cycle() -> Dict[str, Any]:
    """
    执行完整七阶段自演化循环。
    daemon 每 600s 调用一次。
    """
    t0 = time.time()
    cp = _load_checkpoint()
    cycle_num = cp.get('cycle_count', 0) + 1
    cp['cycle_count'] = cycle_num

    logger.info(f'{"="*60}')
    logger.info(f'仙女座自演化 Cycle #{cycle_num} 开始')
    logger.info(f'{"="*60}')
    logger.info(f'  阈值: sim={cp.get("similarity_threshold")}, reinforce={cp.get("reinforce_threshold")}')
    logger.info(f'  batch={cp.get("batch_size")}, derive={cp.get("derive_enabled")}, reinforce={cp.get("reinforce_enabled")}')

    stats: Dict[str, Any] = {
        'cycle': cycle_num,
        'stages': {},
    }

    # ── MT_RULE_VERSION §3.3 + §4: 规则引擎 ↔ 仙女座桥接 (启动前置检查) ──
    try:
        from ai_engines.rules_engine.rule_andromeda_bridge import (
            andromeda_version_check,
            trigger_evolution_rule_refresh,
            rule_knowledge_health_check,
        )
        # ① 版本感知: 版本过旧 → 跳过演化
        _v = andromeda_version_check()
        stats['system_version'] = _v['version']
        stats['version_ok'] = _v['ok']
        if not _v['ok']:
            logger.warning(f'[Cycle #{cycle_num}] ⚠️ 系统版本 {_v["version"]} < minimum — 跳过本轮演化')
            return stats
        logger.info(f'[Cycle #{cycle_num}] ✅ 版本感知 {_v["version"]} (ok={_v["ok"]})')

        # ② 规则覆盖度检查: rule_knowledge 全了没?
        _hc = rule_knowledge_health_check()
        stats['rule_knowledge_covered'] = _hc['covered']
        stats['rule_knowledge_missing'] = _hc['missing']
        logger.info(f'[Cycle #{cycle_num}] 📚 rule_knowledge 覆盖 {_hc["covered"]}/12 篇'
                     f' (missing={_hc["missing"]}, auto_ingested={_hc.get("auto_ingested",0)})')

        # ③ 扫 evolution_log: 有没有 rule_ingest_trigger 事件?
        try:
            _conn = _get_conn()
            _pending = _conn.execute(
                "SELECT evolve_id, trigger_type, target_task, rationale, created_at "
                "FROM mt_ai_self_evolution_log "
                "WHERE trigger_type IN ('rule_ingest_trigger', 'version_bump') "
                "AND (cycle_consumed IS NULL OR cycle_consumed != ?) "
                "ORDER BY evolve_id DESC LIMIT 10",
                (cycle_num,)
            ).fetchall()
            stats['pending_rule_events'] = len(_pending)
            if _pending:
                logger.info(f'[Cycle #{cycle_num}] 🔔 {len(_pending)} 条规则触发事件待处理')
                for ev in _pending:
                    # ev = (evolve_id, trigger_type, target_task, rationale, created_at)
                    logger.info(f'    → [{ev[0]}] {ev[1]}: {ev[3][:60]} ({ev[4]})')
                # 标记已消费 — ⚠️ 之前 bug: 误用 ev[0] 当 evolve_id 但 SELECT 没选它!
                _ids = [int(r[0]) for r in _pending]  # 现在 r[0] 是 evolve_id ✅
                if _ids:
                    # 参数化 IN 子句 (安全)
                    _placeholders = ','.join('?' * len(_ids))
                    _conn.execute(
                        f"UPDATE mt_ai_self_evolution_log SET cycle_consumed=? "
                        f"WHERE evolve_id IN ({_placeholders})",
                        [cycle_num] + _ids
                    )
                    _conn.commit()
                    logger.info(f'[Cycle #{cycle_num}] ✅ 已标记 {len(_ids)} 条事件为 consumed (cycle={cycle_num})')
        except Exception as _e2:
            logger.error(f'[Cycle #{cycle_num}] evolution_log 消费异常: {_e2}')
            stats['pending_rule_events'] = 0
    except Exception as _be:
        logger.warning(f'[Cycle #{cycle_num}] 桥接检查跳过 (非阻断): {_be}')

    # --- 🆕 Stage 0: EigenFlux 摄入 ---
    eigenflux_result = {'ingested': 0, 'skipped': 0, 'sources': []}
    try:
        eigenflux_result = eigenflux_ingest(cp)
        stats['eigenflux_ingest'] = eigenflux_result['ingested']
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage0-eigenflux 整体异常: {e}')
        stats['eigenflux_ingest'] = 0

    # --- Stage 1: Detect ---
    new_items = []
    try:
        new_items = auto_detect(cp)
        stats['detect'] = len(new_items)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage1 整体异常: {e}')
        stats['detect'] = 0

    if not new_items:
        logger.info(f'[Cycle #{cycle_num}] 无新增数据, 跳过后续阶段')
        # 即使没新数据也跑一次 optimize (记录 idle 状态)
        try:
            auto_optimize(cp, stats)
        except Exception:
            pass
        _save_checkpoint(cp)
        elapsed = int((time.time() - t0) * 1000)
        stats['elapsed_ms'] = elapsed
        stats['skipped'] = True
        logger.info(f'[Cycle #{cycle_num} 完成] elapsed={elapsed}ms (idle)')
        return stats

    # --- Stage 2: Retrieve ---
    retrieve_result = {'vectors': [], 'associations': [], 'embeds_ok': 0, 'embeds_fail': 0}
    try:
        retrieve_result = auto_retrieve(new_items, cp)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage2 整体异常: {e}')
    stats['retrieve'] = retrieve_result['embeds_ok']
    cp['total_vectors'] = cp.get('total_vectors', 0) + retrieve_result['embeds_ok']

    # --- Stage 3: Associate ---
    assoc_written = 0
    try:
        assoc_written = auto_associate(retrieve_result['associations'], new_items)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage3 整体异常: {e}')
    stats['associations'] = assoc_written
    stats['stages']['associate'] = retrieve_result['associations'][:3]  # 最多 3 条样例
    cp['total_associations'] = cp.get('total_associations', 0) + assoc_written

    # --- Stage 4: Derive ---
    derived = 0
    try:
        derived = auto_derive(retrieve_result['associations'], new_items, cp)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage4 整体异常: {e}')
    stats['derived'] = derived
    cp['total_derived'] = cp.get('total_derived', 0) + derived

    # --- Stage 4.5: AI 员工讨论衍生知识 ---
    discussed = 0
    try:
        discussed = ai_employees_discuss_derived(
            limit_per_derived=4, max_derived_to_discuss=3, cp=cp
        )
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage4.5 整体异常: {e}')
    stats['discussed'] = discussed

    # --- Stage 5: Reinforce ---
    reinforced = 0
    try:
        reinforced = auto_reinforce(new_items, cp)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage5 整体异常: {e}')
    stats['reinforced'] = reinforced
    cp['total_reinforced'] = cp.get('total_reinforced', 0) + reinforced

    # --- Stage 6: Expand ---
    expanded = 0
    try:
        expanded = auto_expand(new_items, reinforced, cp)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage6 整体异常: {e}')
    stats['expand'] = expanded

    # --- Stage 7: Optimize + 写入 checkpoint ---
    try:
        optimize_result = auto_optimize(cp, stats)
        stats['optimize'] = optimize_result
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage7 整体异常: {e}')

    # 更新 checkpoint (用最后一条 new_item 的 created_at)
    if new_items:
        last_ts = max(
            float(r['created_at'] or 0.0) for r in new_items
        )
        cp['created_at_checkpoint'] = max(cp.get('created_at_checkpoint', 0.0), last_ts)
        cp['last_knowledge_id'] = new_items[-1]['knowledge_id']

    _save_checkpoint(cp)

    elapsed = int((time.time() - t0) * 1000)
    stats['elapsed_ms'] = elapsed

    logger.info(f'[Cycle #{cycle_num} 完成] elapsed={elapsed}ms')
    logger.info(f'  detect={stats["detect"]}, retrieve={stats["retrieve"]}, '
                f'associations={stats["associations"]}, derived={stats["derived"]}, '
                f'reinforced={stats["reinforced"]}, expand={stats["expand"]}')
    logger.info(f'  totals: vectors={cp["total_vectors"]}, associations={cp["total_associations"]}, '
                f'derived={cp["total_derived"]}')

    return stats


# ============================================================
# 🆕 bulk_ingest — 全量 EigenFlux 批量摄入 (不走 daemon cycle, 批量模式)
#
# 场景: mt_ai_eigenflux_messages 有 4.4M 行, 走 daemon cycle batch=200 要 150+ 天
#       bulk_ingest 用 batch=1000, 快速跑完 Stage 0→1→2→3
#       只做: 摄入 → 向量化 → 联想关联 → 知识图谱, 不跑 Stage 4 衍生 (太慢)
#
# 调用: python3 engines/andromeda_auto_evolution.py --bulk
# 或:  API POST /api/ai/github-fusion/deep/bulk-ingest
# ============================================================

def bulk_ingest(max_batches: int = 100, batch_size: int = 1000,
                sleep_between_batches: float = 5.0) -> Dict[str, Any]:
    """
    全量批量摄入 EigenFlux 消息 → 脑库 → 向量化 → 联想 → KG
    最多跑 max_batches × batch_size 条 (默认 100000 条)
    只跑前 3 阶段 (Stage 0→1→2→3), 不跑 Stage 4-7 (太慢)

    返回: 统计 dict
    """
    import time as _time
    t0 = _time.time()
    cp = _load_checkpoint()

    stats = {
        'bulk_started': _time.strftime('%Y-%m-%d %H:%M:%S'),
        'max_batches': max_batches,
        'batch_size': batch_size,
        'batches_completed': 0,
        'total_ingested': 0,
        'total_vectors': 0,
        'total_associations': 0,
        'total_new_relations': 0,
        'elapsed_ms': 0,
    }

    logger.info(
        f'[BULK-INGEST] 启动: max_batches={max_batches}, batch={batch_size}, '
        f'last_msg_id={cp.get("eigenflux_last_msg_id", 0)}'
    )

    for batch_idx in range(max_batches):
        batch_t0 = _time.time()

        # Step A: Stage 0 — EigenFlux 摄入 (增量)
        ingest_result = eigenflux_ingest(cp)
        ingested = ingest_result.get('ingested', 0)

        if ingested == 0:
            logger.info(f'[BULK-INGEST] batch #{batch_idx}: 无新消息摄入 → 提前结束')
            break

        stats['total_ingested'] += ingested

        # Step B: 把新摄入的脑库条目也抓出来做向量化+联想
        # eigenflux_ingest 已经写了 ai_brain_enhanced_knowledge,
        # 用一个小 trick: 把 created_at_checkpoint 退回去再 auto_detect
        # 或者直接从 knowledge_type='eigenflux_message' 抓
        try:
            conn = _get_conn()
            new_brain = conn.execute("""
                SELECT * FROM ai_brain_enhanced_knowledge
                WHERE knowledge_type='eigenflux_message' AND COALESCE(created_at,0) > ?
                ORDER BY COALESCE(created_at,0) ASC
                LIMIT ?
            """, (cp.get('created_at_checkpoint', 0), batch_size)).fetchall()
            conn.close()
        except Exception as e:
            logger.warning(f'[BULK-INGEST] 获取新脑库条目失败: {e}')
            new_brain = []

        if new_brain:
            # Step C: Stage 2 — 向量化 + 联想
            retrieve_result = auto_retrieve(new_brain, cp)
            stats['total_vectors'] += retrieve_result.get('embeds_ok', 0)
            stats['total_associations'] += len(retrieve_result.get('associations', []))

            # Step D: Stage 3 — 写知识图谱关系
            assoc_written = auto_associate(retrieve_result.get('associations', []), new_brain)
            stats['total_new_relations'] += assoc_written

        stats['batches_completed'] = batch_idx + 1

        batch_elapsed = int((_time.time() - batch_t0) * 1000)
        logger.info(
            f'[BULK-INGEST] batch #{batch_idx}: ingested={ingested}, '
            f'vectors={stats["total_vectors"]}, assoc={stats["total_associations"]}, '
            f'relations={stats["total_new_relations"]}, elapsed={batch_elapsed}ms'
        )

        # 保存 checkpoint
        _save_checkpoint(cp)

        # 批次间隔 (给 DB 锁和 Ollama 喘息)
        _time.sleep(sleep_between_batches)

    stats['elapsed_ms'] = int((_time.time() - t0) * 1000)
    _save_checkpoint(cp)
    logger.info(
        f'[BULK-INGEST] 完成: {stats["batches_completed"]} batches, '
        f'{stats["total_ingested"]} ingested, {stats["total_vectors"]} vectors, '
        f'{stats["total_associations"]} associations, {stats["total_new_relations"]} relations, '
        f'{stats["elapsed_ms"]}ms'
    )
    return stats


def bulk_status() -> Dict[str, Any]:
    """bulk 摄入进度 (从 checkpoint 推断)"""
    cp = _load_checkpoint()
    return {
        'bulk_running': False,  # 后台线程没启动, 暂时 False
        'last_msg_id': cp.get('eigenflux_last_msg_id', 0),
        'total_ingested': cp.get('eigenflux_total_ingested', 0),
        'cycle_count': cp.get('cycle_count', 0),
        'batch_size': cp.get('batch_size', 50),
        'ingest_enabled': cp.get('eigenflux_ingest_enabled', True),
    }


def get_status() -> Dict[str, Any]:
    """当前演化状态 (供 API 查询)"""
    cp = _load_checkpoint()
    try:
        conn = _get_conn()
        db_stats = {
            'brain_knowledge': conn.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge").fetchone()[0],
            'graph_nodes': conn.execute("SELECT COUNT(*) FROM knowledge_graph_nodes").fetchone()[0],
            'graph_relations': conn.execute("SELECT COUNT(*) FROM knowledge_graph_relations").fetchone()[0],
            'enhancement_suggestions': conn.execute("SELECT COUNT(*) FROM ai_enhancement_suggestions").fetchone()[0],
            'self_evolution_logs': conn.execute("SELECT COUNT(*) FROM mt_ai_self_evolution_log").fetchone()[0],
            # 🆕 EigenFlux 统计
            'eigenflux_brain_items': conn.execute(
                "SELECT COUNT(*) FROM ai_brain_enhanced_knowledge WHERE knowledge_type='eigenflux_message'"
            ).fetchone()[0],
        }
        # 检查 EigenFlux 消息表
        for tbl in ['mt_ai_eigenflux_messages', 'eigenflux_comm_messages', 'eigenflux_messages']:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
            ).fetchone()
            if exists:
                try:
                    cnt = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                    db_stats[f'eigenflux_{tbl}'] = cnt
                except Exception:
                    db_stats[f'eigenflux_{tbl}'] = 'err'
            else:
                db_stats[f'eigenflux_{tbl}'] = 0
        conn.close()
    except Exception:
        db_stats = {}

    # Ollama 状态
    ollama_ok = False
    try:
        vec = _ollama_embed('ping')
        ollama_ok = vec is not None
    except Exception:
        pass

    return {
        'checkpoint': cp,
        'db_stats': db_stats,
        'ollama_ok': ollama_ok,
        'embedding_model': EMBED_MODEL,
        'derive_model': DERIVE_MODEL,
    }


def run_single_stage(stage: str) -> Dict[str, Any]:
    """手动触发单个阶段 (调试用)"""
    cp = _load_checkpoint()
    new_items = auto_detect(cp)

    if stage == 'detect':
        return {'new_items': len(new_items), 'knowledge_ids': [r['knowledge_id'] for r in new_items[:5]]}
    elif stage == 'retrieve':
        return auto_retrieve(new_items, cp)
    elif stage == 'associate':
        res = auto_retrieve(new_items, cp)
        written = auto_associate(res['associations'], new_items)
        return {'associations_input': len(res['associations']), 'written': written}
    elif stage == 'derive':
        res = auto_retrieve(new_items, cp)
        written = auto_derive(res['associations'], new_items, cp)
        return {'derived': written}
    elif stage == 'reinforce':
        written = auto_reinforce(new_items, cp)
        return {'reinforced': written}
    elif stage == 'expand':
        written = auto_expand(new_items, 0, cp)
        return {'expanded': written}
    else:
        return {'error': f'unknown stage: {stage}'}


# ============================================================
# 命令行入口 (daemon 模式)
# ============================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ANDROMEDA-EVOL] %(levelname)s %(message)s',
    )
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true', help='只跑一次就退出')
    parser.add_argument('--stage', type=str, help='只跑某个阶段')
    parser.add_argument('--status', action='store_true', help='打印状态就退出')
    parser.add_argument('--bulk', type=int, nargs='?', const=50, help='全量 bulk 摄入 (默认 50 batches)')
    parser.add_argument('--bulk-size', type=int, default=500, help='bulk 每批大小')
    args = parser.parse_args()

    if args.status:
        print(json.dumps(get_status(), indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.bulk is not None:
        print(f'启动 bulk_ingest: max_batches={args.bulk}, batch_size={args.bulk_size}')
        result = bulk_ingest(max_batches=args.bulk, batch_size=args.bulk_size)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        sys.exit(0)

    if args.stage:
        result = run_single_stage(args.stage)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        sys.exit(0)

    if args.once:
        result = run_cycle()
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        sys.exit(0)

    # daemon 模式: 无限循环, 每 600s 跑一次
    CYCLE_INTERVAL = 600
    logger.info(f'仙女座自演化 daemon 启动 (interval={CYCLE_INTERVAL}s)')
    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f'cycle crashed: {e}')
        time.sleep(CYCLE_INTERVAL)
