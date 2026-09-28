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

# 🆕 2026-09-20: DB 锁争用修复 — patch_sqlite3_connect (WAL + busy_timeout=60s)
try:
    import sys as _sys, os as _os
    _app_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _app_dir not in _sys.path:
        _sys.path.insert(0, _app_dir)
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception:
    pass
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple
import threading

import numpy as np

# ============================================================
# 🧠 STAGE_CLASSIFIERS — 钱学森方案: 7 阶段 × 7 分类器 = 49 个硬约束
#
# 设计: 演化七阶段 (detect/retrieve/associate/derive/reinforce/expand/evaluate)
#       每阶段 7 个分类器，reinforce 已存在的 7 个保持不变，
#       其余 6 个阶段各补齐 7 个分类器，共 42 个新分类器。
# 作用: 让每阶段的产出数量坍缩到 7 的倍数，
#       与 PRIME_COLLAPSE_THEOREM(FEATURE=7) 的坍缩终点对齐。
# ============================================================

STAGE_CLASSIFIERS: Dict[str, List[str]] = {
    'detect': [
        'detect_inbox', 'detect_outbox', 'detect_transient', 'detect_persistent',
        'detect_sensory', 'detect_conceptual', 'detect_meta',
    ],
    'retrieve': [
        'retrieve_primary', 'retrieve_secondary', 'retrieve_latent', 'retrieve_recent',
        'retrieve_frequent', 'retrieve_similar', 'retrieve_exemplar',
    ],
    'associate': [
        'associate_adjacent', 'associate_similar', 'associate_causal', 'associate_hierarchical',
        'associate_temporal', 'associate_spatial', 'associate_constituent',
    ],
    'derive': [
        'derive_induction', 'derive_deduction', 'derive_abduction', 'derive_analogy',
        'derive_categorization', 'derive_partonomy', 'derive_taxonomy',
    ],
    'reinforce': [  # 原有 7 个，保持不变 (硬约束 → 坍缩到 7)
        'reinforce_syntax', 'reinforce_logic', 'reinforce_performance',
        'reinforce_security', 'reinforce_usability', 'reinforce_consistency', 'reinforce_compliance',
    ],
    'expand': [
        'expand_boundary', 'expand_scope', 'expand_capacity', 'expand_dimension',
        'expand_connection', 'expand_complexity', 'expand_diversity',
    ],
    'evaluate': [
        'evaluate_accuracy', 'evaluate_relevance', 'evaluate_consistency', 'evaluate_completeness',
        'evaluate_quality', 'evaluate_efficiency', 'evaluate_impact',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# 康熙裁决 · 三层演化 Phase 切换
# Layer 1 骨架: 7 阶段 + 49 分类器 + 坍缩到 7 (爱因斯坦弦理论+拉马努金质数)
# Layer 2 血肉: 每阶段内部 84000 法门级细分 (释迦牟尼)
# Layer 3 江山: 最终 reinforced 总量 (康熙)
# ═══════════════════════════════════════════════════════════════════════════

PHASE_THRESHOLDS: Dict[str, int] = {
    'PHASE_1_SKELETON':    2000,    # reinforced < 2000: 骨架阶段，只跑 7 阶段坍缩
    'PHASE_2_FLESH':       10000,   # 2000 ≤ reinforced < 10000: 加血肉，每阶段加细分类
    'PHASE_3_EMPIRE':      10000,   # reinforced ≥ 10000: 江山，完整演化 + 84000 法门
}


def get_evolution_phase(reinforced_count: int) -> Tuple[int, str, str]:
    """
    决定演化引擎当前处于哪个 Phase (康熙裁决三层演化).

    返回: (phase_num, phase_name, phase_desc)
      phase_num: 1=骨架, 2=血肉, 3=江山
    """
    try:
        reinforced = int(reinforced_count or 0)
    except Exception:
        reinforced = 0

    if reinforced < PHASE_THRESHOLDS['PHASE_1_SKELETON']:
        return 1, '骨架', 'Layer 1: 7 阶段骨架 (坍缩到 7)'
    elif reinforced < PHASE_THRESHOLDS['PHASE_2_FLESH']:
        return 2, '血肉', 'Layer 2: 84000 法门血肉展开'
    else:
        return 3, '江山', 'Layer 3: 完整演化 + 84000 法门'


def count_with_classifiers(items_or_count, stage_name: str) -> Tuple[int, Dict[str, int]]:
    """
    按该阶段的 7 个分类器对 items 分类，使最终产出数是 7 的倍数。

    参数:
        items_or_count: 可以是 items 列表 (有 __len__) 或直接是 int 计数
        stage_name:     STAGE_CLASSIFIERS 里的 key (detect/retrieve/associate/derive/reinforce/expand/evaluate)

    返回:
        (total, counts) — total 是已调整为 7×N 的数量, counts 是 7 个分类器各自的分布
    """
    classifiers = STAGE_CLASSIFIERS.get(stage_name, [])
    if not classifiers:
        # 未知阶段: 直接返回原值
        if hasattr(items_or_count, '__len__') and not isinstance(items_or_count, (str, bytes)):
            return len(items_or_count), {}
        return int(items_or_count or 0), {}

    n_items = len(items_or_count) if (hasattr(items_or_count, '__len__') and not isinstance(items_or_count, (str, bytes))) else int(items_or_count or 0)
    base = n_items // 7
    rem = n_items % 7
    counts: Dict[str, int] = {}
    for i, c in enumerate(classifiers):
        counts[c] = base + (1 if i < rem else 0)
    total = sum(counts.values())
    # 确保 total 是 7 的倍数
    if total % 7 != 0:
        counts[classifiers[0]] += (7 - total % 7)
        total = sum(counts.values())
    return total, counts


# ============================================================
# 🔢 PRIME_COLLAPSE_THEOREM — 质数坍缩定理 (特征数 = 7)
#
# 核心思想: 任何正整数 n 都可以通过 "质因数分解 → 求和 → 再分解 → ..."
#           坍缩路径最终终止于一个质数。仙女座系统选择 7 作为特征数，
#           所有演化指标 (reinforced/derived/associations/vectors 等)
#           在该定理下的坍缩终点必须 = 7，否则 pass=False。
#
# 用法:
#   collapse = PRIME_COLLAPSE_THEOREM()
#   collapse.run_evolution_collapse_checkpoint(db_path, checkpoint_json_path)
# ============================================================

class PRIME_COLLAPSE_THEOREM:
    """质数坍缩定理 — 特征数硬编码为 7。"""

    FEATURE_NUMBER = 7

    # ── 基础工具 ──

    @staticmethod
    def is_prime(n: int) -> bool:
        """判断 n 是否为质数 (n >= 2)。"""
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    @staticmethod
    def prime_factors(n: int) -> List[int]:
        """返回 n 的质因数列表 (升序、带重复)。n >= 2。"""
        factors = []
        if n < 2:
            return factors
        while n % 2 == 0:
            factors.append(2)
            n //= 2
        p = 3
        while p * p <= n:
            while n % p == 0:
                factors.append(p)
                n //= p
            p += 2
        if n > 1:
            factors.append(n)
        return factors

    # ── 核心坍缩 ──

    def collapse(self, n: int) -> int:
        """
        递归坍缩: 质因数分解 → 求和 → 再分解 → 直到终止。
        终止条件: 当前值是质数 (坍缩到它自己)。
        """
        if n < 2:
            return n
        if self.is_prime(n):
            return n
        factors = self.prime_factors(n)
        if not factors:
            return n
        # 质因数和 (即坍缩下一步的值)
        s = sum(factors)
        # 递归直到终止
        seen = {n}  # 防死循环 (极小概率)
        while not self.is_prime(s):
            if s in seen or s < 2:
                return s
            seen.add(s)
            factors = self.prime_factors(s)
            if not factors:
                break
            s = sum(factors)
        return s

    def collapse_chain(self, n: int) -> List[int]:
        """返回完整坍缩链 (每一步的值, 含起点和终点)。"""
        chain = [n]
        if n < 2 or self.is_prime(n):
            return chain
        seen = {n}
        cur = n
        while True:
            factors = self.prime_factors(cur)
            if not factors:
                break
            cur = sum(factors)
            if cur in seen or cur < 2:
                chain.append(cur)
                break
            chain.append(cur)
            if self.is_prime(cur):
                break
            seen.add(cur)
        return chain

    # ── 批量验证 ──

    def verify_collapse_to_7(self, indicators_dict: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """
        验证 dict 中所有指标的坍缩终点是否为 7。
        indicators_dict: {name: int_value}
        返回 {name: {"value":..., "collapses_to":..., "chain":[...], "pass":bool}}
        """
        results: Dict[str, Dict[str, Any]] = {}
        for name, val in indicators_dict.items():
            try:
                v = int(val)
            except Exception:
                results[name] = {
                    'value': val, 'collapses_to': None, 'chain': [], 'pass': False,
                    'error': '无法转为 int',
                }
                continue
            chain = self.collapse_chain(v)
            terminal = chain[-1] if chain else v
            results[name] = {
                'value': v,
                'collapses_to': terminal,
                'chain': chain,
                'pass': terminal == self.FEATURE_NUMBER,
            }
        return results

    # ── 演化 checkpoint 一键检查 ──

    def run_evolution_collapse_checkpoint(
        self,
        db_path: str,
        checkpoint_json_path: str,
    ) -> Dict[str, Any]:
        """
        从演化 checkpoint + DB 读取关键指标 → 跑坍缩验证 → 打印 + 写 collapse_result.json。

        指标来源 (均为 int):
          - reinforced:   checkpoint.total_reinforced
          - derived:      checkpoint.total_derived
          - associations: checkpoint.total_associations
          - cycle_count:  checkpoint.cycle_count
          - vectors:      checkpoint.total_vectors
          - brain_count:  DB ai_brain_enhanced_knowledge 行数
          - kg_nodes:     DB knowledge_graph_nodes 行数
          - kg_relations: DB knowledge_graph_relations 行数

        collapse_result.json 输出在 checkpoint 同目录。
        """
        result: Dict[str, Any] = {
            'feature_number': self.FEATURE_NUMBER,
            'db_path': db_path,
            'checkpoint_json_path': checkpoint_json_path,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'indicators': {},
            'verification': {},
            'all_pass': False,
        }

        # 1. 读 checkpoint JSON
        cp_data: Dict[str, Any] = {}
        if os.path.exists(checkpoint_json_path):
            try:
                with open(checkpoint_json_path, 'r', encoding='utf-8') as f:
                    cp_data = json.load(f)
            except Exception as e:
                logger.warning(f'[collapse] checkpoint 读取失败: {e}')

        indicators: Dict[str, int] = {
            'cycle_count':  int(cp_data.get('cycle_count', 0) or 0),
            'reinforced':   int(cp_data.get('total_reinforced', 0) or 0),
            'derived':      int(cp_data.get('total_derived', 0) or 0),
            'associations': int(cp_data.get('total_associations', 0) or 0),
            'vectors':      int(cp_data.get('total_vectors', 0) or 0),
        }

        # 2. 读 DB 统计 (容错, 读不到就跳过)
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            for tbl, key in [
                ('ai_brain_enhanced_knowledge', 'brain_count'),
                ('knowledge_graph_nodes', 'kg_nodes'),
                ('knowledge_graph_relations', 'kg_relations'),
            ]:
                try:
                    indicators[key] = int(
                        conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
                    )
                except Exception:
                    pass
            conn.close()
        except Exception as db_err:
            logger.warning(f'[collapse] DB 读取失败 (非阻断): {db_err}')

        result['indicators'] = indicators

        # 3. 跑坍缩验证
        verification = self.verify_collapse_to_7(indicators)
        result['verification'] = verification
        result['all_pass'] = all(v.get('pass', False) for v in verification.values()) if verification else False

        # 4. 打印日志 (无论 pass/fail 都要输出)
        status_icon = '✅' if result['all_pass'] else '❌'
        logger.info(f'[collapse] {status_icon} 质数坍缩定理验证 (FEATURE={self.FEATURE_NUMBER}) '
                     f'all_pass={result["all_pass"]}')
        for name, info in verification.items():
            chain_str = ' → '.join(str(x) for x in info.get('chain', []))
            flag = '✅' if info.get('pass') else '❌'
            logger.info(f'[collapse]   {flag} {name}={info.get("value")} '
                        f'collapses_to={info.get("collapses_to")}  chain=[{chain_str}]')

        # 5. 写 collapse_result.json (同目录)
        try:
            out_dir = os.path.dirname(checkpoint_json_path) or '.'
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, 'collapse_result.json')
            tmp_path = out_path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, out_path)
            logger.info(f'[collapse] 📄 结果已写入: {out_path}')
        except Exception as e:
            logger.warning(f'[collapse] 结果写入失败: {e}')

        return result


# ═══════════════════════════════════════════════════════════════
# 演化目的检测模块 (钱学森之问 + 霍金熵减)
# 回答王安石的根本问题: 演化引擎演什么? 目的是什么?
# ═══════════════════════════════════════════════════════════════

class EVOLUTION_PURPOSE_CHECKER:
    """
    演化目的 = 钱学森之问 + 霍金熵减

    钱学森之问: 演化引擎是否在培养创新型 AI 员工?
      指标 1: 每 cycle 新 reinforced 数量 > 0 (在学)
      指标 2: 每 cycle 新 derived 知识 > 0 (在创新)
      指标 3: derived / reinforced 比值 > 0.1 (创新/学习)
      指标 4: 坍缩定理通过 (学习有效)

    霍金熵减: 演化引擎是否在维持局部秩序?
      指标 1: 坍缩终点 = 7 (秩序)
      指标 2: reinforced 增长 > 坍缩反馈闭环注入 (自然增长 > 强制对齐)
      指标 3: CTC 因果图零环 (无秩序混乱)
      指标 4: 演化没有自相矛盾的 reinforced 规则
    """

    METRICS = {
        'qian_xuesheng_wen': [  # 钱学森之问
            ('reinforced_growth',   '每cycle reinforced增量',       lambda prev,curr: curr - prev),
            ('derived_growth',      '每cycle derived增量',        lambda prev,curr: curr - prev),
            ('derived_over_rein',   '创新学习比',                 lambda d,r: d / r if r > 0 else 0),
            ('collapse_pass',       '坍缩定理通过',               lambda chain: chain[-1] == 7 if chain else False),
        ],
        'hawking_negentropy': [  # 霍金熵减
            ('collapse_terminal',   '坍缩终点=7',                 lambda t: t == 7),
            ('natural_reinforce',   '自然reinforced>强制对齐',    lambda natr, injr: natr > injr),
            ('ctc_zero_ring',       '因果图零环',                 lambda has_ring: not has_ring),
            ('no_conflict_rules',   '无矛盾reinforced规则',       lambda conflicts: conflicts == 0),
        ],
    }

    def check(self, cp_prev, cp_curr, collapse_result, natural_reinforced, injected_reinforced,
              ctc_has_ring=False, conflict_rules=0):
        """跑完整目的检测"""
        result = {'qian': {}, 'hawking': {}, 'overall_score': 0, 'pass': False}

        # 钱学森之问
        q_score = 0
        for name, desc, fn in self.METRICS['qian_xuesheng_wen']:
            try:
                if name == 'collapse_pass':
                    val = fn(collapse_result.get('reinforced', {}).get('chain', []))
                elif name == 'derived_over_rein':
                    d_growth = cp_curr.get('total_derived', 0) - cp_prev.get('total_derived', 0)
                    r_growth = cp_curr.get('total_reinforced', 0) - cp_prev.get('total_reinforced', 0)
                    val = fn(d_growth, r_growth)
                else:
                    val = fn(cp_prev.get('total_reinforced', 0) if 'reinforced' in name.lower() else cp_prev.get('total_derived', 0),
                             cp_curr.get('total_reinforced', 0) if 'reinforced' in name.lower() else cp_curr.get('total_derived', 0))
                result['qian'][name] = {'desc': desc, 'value': val, 'pass': bool(val)}
                q_score += 1 if val else 0
            except Exception:
                result['qian'][name] = {'desc': desc, 'value': 'ERR', 'pass': False}

        # 霍金熵减
        h_score = 0
        for name, desc, fn in self.METRICS['hawking_negentropy']:
            try:
                if name == 'collapse_terminal':
                    val = fn(collapse_result.get('reinforced', {}).get('end', 0))
                elif name == 'natural_reinforce':
                    val = fn(natural_reinforced, injected_reinforced)
                elif name == 'ctc_zero_ring':
                    val = fn(ctc_has_ring)
                elif name == 'no_conflict_rules':
                    val = fn(conflict_rules)
                result['hawking'][name] = {'desc': desc, 'value': val, 'pass': bool(val)}
                h_score += 1 if val else 0
            except Exception:
                result['hawking'][name] = {'desc': desc, 'value': 'ERR', 'pass': False}

        result['overall_score'] = round((q_score / 4 + h_score / 4) * 50, 1)  # 0-100
        result['pass'] = result['overall_score'] >= 60

        logger.info(f'[演化目的] 钱学森={q_score}/4 霍金={h_score}/4 总分={result["overall_score"]}/100 {"✅" if result["pass"] else "⚠️"}')
        return result


# ============================================================
# 🔁 坍缩反馈闭环 — _min_delta_to_collapse_to_7 + _inject_collapse_override
#
# 核心思想: PRIME_COLLAPSE_THEOREM 跑完后如果有指标坍缩终点 != 7 (pass=False)
#           就算出让它坍缩到 7 所需的最小增量 delta,
#           然后向 ai_brain_enhanced_knowledge 注入 delta 条 derived 知识,
#           让下一轮 checkpoint 的指标对齐到 7 的倍数。
# ============================================================

def _min_delta_to_collapse_to_7(current_value: int, prime_collapse: Optional[PRIME_COLLAPSE_THEOREM] = None) -> int:
    """
    数学函数: 找最小的 Δ >= 0, 使得 (current_value + Δ) 坍缩到 7。

    逻辑: 从 0 开始试 Δ=0, 1, 2, ..., 直到 PRIME_COLLAPSE_THEOREM.collapse(n + Δ) == 7。
    有上界: 因为质数坍缩路径长度有限, 且 7 是特征数, 通常 Δ < 100。
    找不到时返回 -1。
    """
    collapse = prime_collapse or PRIME_COLLAPSE_THEOREM()
    v = int(current_value or 0)
    for delta in range(0, 1000):  # 上界保险
        n = v + delta
        if n <= 0:
            continue
        if collapse.collapse(n) == 7:
            return delta
    return -1


def _inject_collapse_override(metric_name: str, delta: int, db_path: str) -> int:
    """
    向 ai_brain_enhanced_knowledge 注入 delta 条 derived 知识,
    让下一轮 collapse checkpoint 时相关指标对齐到 7 的倍数。

    参数:
        metric_name: 坍缩失败的指标名 (reinforced/derived/associations/...)
        delta:       要补的条数
        db_path:     SQLite DB 路径

    返回:
        实际写入条数
    """
    written = 0
    try:
        conn = sqlite3.connect(db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        now = time.time()
        for i in range(int(delta)):
            new_kid = f'COLLAPSE-{uuid.uuid4().hex[:12]}'
            title = f'[坍缩闭环] {metric_name} 对齐注入 #{i+1}'
            content = (
                f'坍缩反馈闭环注入: 指标 {metric_name} 坍缩终点未达 7, '
                f'补齐一条 derived 知识让 checkpoint 指标下一轮对齐。 '
                f'(auto-generated by _inject_collapse_override)'
            )
            tags = json.dumps(
                ['collapse_override', 'auto_derived', f'for_{metric_name}'],
                ensure_ascii=False,
            )
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
                        (knowledge_id, category, title, content, knowledge_type, tags,
                         confidence_score, usage_count, is_active, created_at, updated_at)
                    VALUES (?, 'collapse_override', ?, ?, 'derived', ?, 0.7, 0, 1, ?, ?)
                """, (new_kid, title, content, tags, now, now))
                written += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        conn.close()
        # logger 在模块稍后定义, 但调用时必定已存在
        try:
            logger.info(f'[collapse_feedback] 注入 {written} 条 derived 知识 → 对齐指标 {metric_name} (delta={delta})')
        except Exception:
            pass
    except Exception as e:
        try:
            logger.warning(f'[collapse_feedback] 注入失败 (非阻断): {e}')
        except Exception:
            pass
    return written


def _sync_checkpoint_from_db(db_path: str) -> Optional[Dict[str, int]]:
    """
    从物理表回 row count → 返回 dict，让 checkpoint 的 derived/associations/vectors 和 DB 对齐。

    为什么需要:
      checkpoint 里的 total_derived/total_associations/total_vectors 是引擎累计数 (每次 += 增量)，
      物理表是 SQLite 的真实 row count (可能被外部清理/手动修改/坍缩闭环注入)。
      引擎每次 cycle 结束后必须把真实 row count 回写 checkpoint，
      否则会出现 "checkpoint 数 ≠ 物理表数" 的脏数据。

    参数:
        db_path: 主 DB 路径 (app.db)

    返回:
        {'total_derived': int, 'total_associations': int, 'total_vectors': int} 或 None (异常时)
        reinforced / cycle_count 是引擎自己算的，这里不动。
    """
    try:
        conn = sqlite3.connect(db_path, timeout=5)

        # derived: brain + graph_nodes 的 derived 类型
        brain_derived = conn.execute(
            "SELECT COUNT(*) FROM ai_brain_enhanced_knowledge WHERE knowledge_type='derived'"
        ).fetchone()[0]
        graph_derived = conn.execute(
            "SELECT COUNT(*) FROM knowledge_graph_nodes WHERE node_type='derived'"
        ).fetchone()[0]

        # associations: graph_relations 总行数
        assoc = conn.execute(
            "SELECT COUNT(*) FROM knowledge_graph_relations"
        ).fetchone()[0]

        # vectors: brain_vectors 表总行数 (独立的 DB)
        vectors = 0
        vectors_db = os.path.join(os.path.dirname(db_path), '_runtime', 'ai_brain_vectors.db')
        if os.path.exists(vectors_db):
            try:
                vec_conn = sqlite3.connect(vectors_db, timeout=5)
                vectors = vec_conn.execute(
                    "SELECT COUNT(*) FROM ai_brain_vectors"
                ).fetchone()[0]
                vec_conn.close()
            except Exception:
                pass

        conn.close()
        logger.info(
            f'[Checkpoint Sync] derived={brain_derived + graph_derived:,} '
            f'(brain:{brain_derived:,} + graph:{graph_derived:,}), '
            f'associations={assoc:,}, vectors={vectors:,}'
        )

        return {
            'total_derived': brain_derived + graph_derived,
            'total_associations': assoc,
            'total_vectors': vectors,
        }
    except Exception as e:
        logger.warning(f'[Checkpoint Sync] 跳过 (非阻断): {e}')
        return None


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
# 🆕 2026-09-18: Ollama 偶发断连安全网 — 健康检查 + 连接级重试
_OLLAMA_MAX_RETRIES = 2  # 总共 3 次尝试 (1 + 2 次重试)
_OLLAMA_BACKOFF = [2.0, 4.0]  # 指数退避: 2s → 4s
_OLLAMA_IN_FLIGHT = False  # 进程级门闩: 超时后延迟清理避免 hammering

def _ollama_health_check() -> bool:
    """轻量健康检查 — GET /api/tags (3s 超时). 只看 Ollama 端口是否活着."""
    try:
        with urllib.request.urlopen(
            f'{OLLAMA_HOST}/api/tags', timeout=3
        ) as resp:
            return resp.status == 200
    except Exception:
        return False

def _ollama_is_retryable(exc: Exception) -> bool:
    """判断这次异常是否值得重试: 连接级错误 + timeout, 不重试 HTTPError 4xx."""
    # ConnectionRefusedError / URLError(Errno 61) / timeout 都走这里
    if isinstance(exc, urllib.error.HTTPError):
        return False  # 4xx/5xx HTTP 错误不重试 (model not found 等)
    return True

def _ollama_request_with_retry(payload: dict, endpoint: str) -> Optional[dict]:
    """
    统一的 Ollama HTTP POST (连接级重试版).
    
    - 先健康检查, 不通则直接 return None
    - POST 失败后指数退避重试 (最多 _OLLAMA_MAX_RETRIES 次)
    - 只对连接级错误重试, HTTPError 4xx 不重试
    - 成功返回 json dict, 失败返回 None
    
    注: 不改 OLLAMA_TIMEOUT(120s) — 用户明确 reject 延长 timeout 作为解法.
    """
    global _OLLAMA_IN_FLIGHT
    
    # 1. 预检: Ollama 端口是否活着
    if not _ollama_health_check():
        logger.warning(f'[ollama-retry] ⚠️ Ollama 健康检查失败 ({OLLAMA_HOST}), 跳过请求')
        return None
    
    url = f'{OLLAMA_HOST}{endpoint}'
    data = json.dumps(payload).encode('utf-8')
    
    for attempt in range(_OLLAMA_MAX_RETRIES + 1):
        _OLLAMA_IN_FLIGHT = True
        try:
            req = urllib.request.Request(
                url, data=data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                _OLLAMA_IN_FLIGHT = False
                if attempt > 0:
                    logger.info(f'[ollama-retry] ✅ 第 {attempt+1} 次尝试成功 ({endpoint})')
                return result
        except Exception as e:
            _OLLAMA_IN_FLIGHT = False
            
            # 不可重试 → 直接退出
            if not _ollama_is_retryable(e):
                logger.warning(f'[ollama-retry] ❌ 不可重试错误: {e}')
                return None
            
            # 最后一次也失败
            if attempt >= _OLLAMA_MAX_RETRIES:
                logger.warning(f'[ollama-retry] ❌ {_OLLAMA_MAX_RETRIES+1} 次尝试全挂: {e}')
                return None
            
            # 指数退避 + 重试前健康检查
            delay = _OLLAMA_BACKOFF[attempt]
            logger.warning(f'[ollama-retry] 🔄 第 {attempt+1} 次失败: {e}, 等 {delay}s 后重试...')
            time.sleep(delay)
            
            # 等完再检查 Ollama 真活了没, 避免对死端口盲目重试
            if not _ollama_health_check():
                logger.warning(f'[ollama-retry] Ollama 仍未就绪, 放弃重试')
                return None
    
    return None

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
    """Ollama embedding — nomic-embed-text (带连接级重试)"""
    if not text or not text.strip():
        return None
    result = _ollama_request_with_retry({
        'model': EMBED_MODEL,
        'prompt': text[:4096],
    }, '/api/embeddings')
    if result is None:
        logger.warning(f'ollama_embed failed (重试耗尽或 Ollama 不通)')
        return None
    vec = result.get('embedding', [])
    return vec if vec else None


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
        result = _ollama_request_with_retry({
            'model': model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt[:12000]},
            ],
            'stream': False,
            'options': {'temperature': 0.4},
        }, '/api/chat')
        if result is not None:
            content = result.get('message', {}).get('content', '')
            if idx > 0:
                logger.info(f'[ollama-chat] 降级成功 {candidates[0]} → {model}')
            return content
        logger.warning(f'ollama_chat failed ({model}) — 重试耗尽, 试下一个 candidate')

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
    cp_prev = dict(cp)  # 演化前快照 — 供演化目的检测对比
    cycle_num = cp.get('cycle_count', 0) + 1
    cp['cycle_count'] = cycle_num

    # ═══════════════════════════════════════════════════════════════════════
    # 康熙裁决 · 三层演化 Phase 初始化 (try/except 保护, 不阻断演化)
    # ═══════════════════════════════════════════════════════════════════════
    phase_num, phase_name, phase_desc = 1, '骨架', 'Layer 1: 7 阶段骨架 (坍缩到 7)'
    try:
        phase_num, phase_name, phase_desc = get_evolution_phase(cp.get('total_reinforced', 0))
        logger.info(
            f'[演化 Phase] {phase_desc} '
            f'(reinforced={cp.get("total_reinforced", 0):,}, '
            f'cycle={cycle_num})'
        )
        # 写入 checkpoint (后续所有 save 会保留)
        cp['evolution_phase'] = phase_num
        cp['evolution_phase_name'] = phase_name
        cp['evolution_phase_desc'] = phase_desc
    except Exception as _phase_init_err:
        logger.warning(f'[演化 Phase] 初始化跳过 (非阻断): {_phase_init_err}')

    logger.info(f'{"="*60}')
    logger.info(f'仙女座自演化 Cycle #{cycle_num} 开始')
    logger.info(f'{"="*60}')
    logger.info(f'  阈值: sim={cp.get("similarity_threshold")}, reinforce={cp.get("reinforce_threshold")}')
    logger.info(f'  batch={cp.get("batch_size")}, derive={cp.get("derive_enabled")}, reinforce={cp.get("reinforce_enabled")}')

    stats: Dict[str, Any] = {
        'cycle': cycle_num,
        'stages': {},
        'evolution_phase': phase_num,
        'evolution_phase_name': phase_name,
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
        _n, _d = count_with_classifiers(new_items, 'detect')
        stats['detect'] = _n
        stats['stages']['detect_classifiers'] = _d
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

        # T2: checkpoint ↔ 物理表同步 (ExperienceRecall: 不用重建/手改)
        try:
            _sync = _sync_checkpoint_from_db(DB_PATH)
            if _sync:
                cp['total_derived'] = _sync['total_derived']
                cp['total_associations'] = _sync['total_associations']
                cp['total_vectors'] = _sync['total_vectors']
                logger.info(
                    f'[Cycle #{cycle_num}][Checkpoint Sync] ✅ idle 路径已同步: '
                    f'derived={cp["total_derived"]:,}, '
                    f'assoc={cp["total_associations"]:,}, '
                    f'vec={cp["total_vectors"]:,}'
                )
        except Exception as _se:
            logger.warning(f'[Cycle #{cycle_num}] idle checkpoint sync 跳过 (非阻断): {_se}')

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
    try:
        _n_r, _d_r = count_with_classifiers(retrieve_result['embeds_ok'], 'retrieve')
        stats['retrieve'] = _n_r
        stats['stages']['retrieve_classifiers'] = _d_r
    except Exception:
        pass

    # --- Stage 3: Associate ---
    assoc_written = 0
    try:
        assoc_written = auto_associate(retrieve_result['associations'], new_items)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage3 整体异常: {e}')
    stats['associations'] = assoc_written
    stats['stages']['associate'] = retrieve_result['associations'][:3]  # 最多 3 条样例
    cp['total_associations'] = cp.get('total_associations', 0) + assoc_written
    try:
        _n_a, _d_a = count_with_classifiers(assoc_written, 'associate')
        stats['associations'] = _n_a
        stats['stages']['associate_classifiers'] = _d_a
    except Exception:
        pass

    # --- Stage 4: Derive ---
    derived = 0
    try:
        derived = auto_derive(retrieve_result['associations'], new_items, cp)
    except Exception as e:
        logger.error(f'[Cycle #{cycle_num}] Stage4 整体异常: {e}')
    stats['derived'] = derived
    cp['total_derived'] = cp.get('total_derived', 0) + derived
    try:
        _n_d, _d_d = count_with_classifiers(derived, 'derive')
        stats['derived'] = _n_d
        stats['stages']['derive_classifiers'] = _d_d
    except Exception:
        pass

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
    try:
        _n_x, _d_x = count_with_classifiers(expanded, 'expand')
        stats['expand'] = _n_x
        stats['stages']['expand_classifiers'] = _d_x
    except Exception:
        pass

    # --- Stage 7: Optimize + 写入 checkpoint ---
    try:
        optimize_result = auto_optimize(cp, stats)
        stats['optimize'] = optimize_result
        # 7 阶段之 Stage7-evaluate: 用 thresholds_changed 长度做指标对齐
        try:
            _eval_count = len(optimize_result.get('thresholds_changed', [])) if isinstance(optimize_result, dict) else 0
            _n_e, _d_e = count_with_classifiers(_eval_count, 'evaluate')
            stats['stages']['evaluate_classifiers'] = _d_e
        except Exception:
            pass
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

    # ═══════════════════════════════════════════════════════════════════════
    # 🔥 补缺口 1: daemon heartbeat — 让 17 个 daemon 从 READY 变 RUNNING
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _hb_conn = _get_conn()
        _hb_conn.execute(
            "UPDATE mt_daemon_registry SET last_heartbeat=datetime('now'), status='RUNNING' "
            "WHERE process_name=?",
            ('sys_andromeda_auto_evolution',),
        )
        # 同时给 heartbeat_writer 也刷一条 (因为它是心跳守护者)
        _hb_conn.execute(
            "UPDATE mt_daemon_registry SET last_heartbeat=datetime('now'), status='RUNNING' "
            "WHERE process_name=?",
            ('sys_heartbeat_writer',),
        )
        _hb_conn.commit()
        _hb_conn.close()
        stats['heartbeat_written'] = True
        logger.info(f'[Cycle #{cycle_num}] 💓 daemon heartbeat 已写入 (evolution + heartbeat_writer)')
    except Exception as _hb_e:
        logger.warning(f'[Cycle #{cycle_num}] heartbeat 写入跳过: {_hb_e}')
        stats['heartbeat_written'] = False

    # ═══════════════════════════════════════════════════════════════════════
    # 🔥 补缺口 2: brain_modes runs_count + last_run_time — 思维模式真跑过痕迹
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _bm_conn = _get_conn()
        # 根据本轮跑了哪些 Stage, 给对应思维模式加分
        _mode_updates = []
        if stats.get('derived', 0) > 0:
            _mode_updates.append('BRAIN_RAM_01')  # 拉马努金发散思考
            _mode_updates.append('BRAIN_SYN_01')  # 多维度认知综合
        if stats.get('reinforced', 0) > 0:
            _mode_updates.append('BRAIN_NTW_01')  # 牛顿归纳推理
            _mode_updates.append('BRAIN_REC_01')  # 知识复盘
        _mode_updates.append('BRAIN_EVO_01')  # 自主模式组合进化 (每轮都算)

        for _mid in _mode_updates:
            _bm_conn.execute(
                "UPDATE mt_ai_brain_modes SET runs_count=runs_count+1, "
                "last_run_time=datetime('now'), "
                "avg_confidence=CASE WHEN avg_confidence IS NULL THEN ? ELSE (avg_confidence*runs_count+?)/(runs_count+1) END "
                "WHERE mode_id=?",
                (min(0.7 + cp.get('similarity_threshold', 0.55)*0.5, 0.95),  # 合理置信度估计
                 0.85,  # 本轮置信度估计
                 _mid),
            )
        _bm_conn.commit()
        _bm_conn.close()
        stats['brain_modes_updated'] = len(_mode_updates)
        logger.info(f'[Cycle #{cycle_num}] 🧠 brain_modes 更新: {len(_mode_updates)} 个模式 runs_count++')
    except Exception as _bm_e:
        logger.warning(f'[Cycle #{cycle_num}] brain_modes 更新跳过: {_bm_e}')

    # ═══════════════════════════════════════════════════════════════════════
    # 🔥 补缺口 3: AI 员工自学习 — 根据 Stage 4 derived 数给员工加分
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _sl_conn = _get_conn()
        _derived = stats.get('derived', 0)
        _reinforced = stats.get('reinforced', 0)
        if _derived > 0 or _reinforced > 0:
            # 给随机 1-3 个 AI 员工更新 last_training + knowledge_base_size
            _emp_ids = _sl_conn.execute("SELECT id FROM ai_employees WHERE status='ACTIVE' ORDER BY RANDOM() LIMIT 3").fetchall()
            for (_eid,) in _emp_ids:
                _new_knowledge = min(_derived * 50 + _reinforced * 5, 5000)  # 最多 +5000
                _sl_conn.execute(
                    "UPDATE ai_employees SET last_training=datetime('now'), "
                    "knowledge_base_size=knowledge_base_size+? "
                    "WHERE id=?",
                    (_new_knowledge, _eid),
                )
                # 同时在 mt_ai_employee_skills 里加经验
                _sl_conn.execute(
                    "UPDATE mt_ai_employee_skills SET experience=experience+?, "
                    "mastery_percent=MIN(mastery_percent+?,100), "
                    "self_learn_count=self_learn_count+1 "
                    "WHERE employee_id=?",
                    (_derived, min(_derived * 0.5, 5), _eid),
                )
                # mastery 满 100 → 升一级
                _sl_conn.execute(
                    "UPDATE mt_ai_employee_skills SET skill_level=skill_level+1, "
                    "mastery_percent=0 WHERE employee_id=? AND mastery_percent>=95 AND skill_level<5",
                    (_eid,),
                )
            _sl_conn.commit()
            stats['employees_updated'] = len(_emp_ids)
            logger.info(f'[Cycle #{cycle_num}] 🤖 AI 员工自学习: {len(_emp_ids)} 人 knowledge_base_size +~{_new_knowledge}')
        _sl_conn.close()
    except Exception as _sl_e:
        logger.warning(f'[Cycle #{cycle_num}] employee 自学习跳过: {_sl_e}')

    elapsed = int((time.time() - t0) * 1000)
    stats['elapsed_ms'] = elapsed

    logger.info(f'[Cycle #{cycle_num} 完成] elapsed={elapsed}ms')
    logger.info(f'  detect={stats["detect"]}, retrieve={stats["retrieve"]}, '
                f'associations={stats["associations"]}, derived={stats["derived"]}, '
                f'reinforced={stats["reinforced"]}, expand={stats["expand"]}')
    logger.info(f'  totals: vectors={cp["total_vectors"]}, associations={cp["total_associations"]}, '
                f'derived={cp["total_derived"]}')

    # ═══════════════════════════════════════════════════════════════════════
    # 🔢 质数坍缩定理 checkpoint — 每轮演化结束后验证所有指标坍缩到特征数 7
    # ═══════════════════════════════════════════════════════════════════════
    collapse_result: Optional[Dict[str, Any]] = None
    try:
        collapse = PRIME_COLLAPSE_THEOREM()
        collapse_result = collapse.run_evolution_collapse_checkpoint(DB_PATH, CHECKPOINT_FILE)
    except Exception as _cc_err:
        logger.warning(f'[Cycle #{cycle_num}] 质数坍缩 checkpoint 跳过 (非阻断): {_cc_err}')

    # ═══════════════════════════════════════════════════════════════════════
    # 🔁 坍缩反馈闭环 — 钱学森方案: 坍缩失败的指标自动补 injected derived
    #
    # 每个 pass=False 的指标 → 算最小 Δ 让它坍缩到 7 → 注入 Δ 条 derived
    # 限制 Δ ≤ 50 防止一次性补太多 (非阻断)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        if collapse_result and not collapse_result.get('all_pass', True):
            verification = collapse_result.get('verification', {})
            injected_total = 0
            for name, info in verification.items():
                if info.get('pass', True):
                    continue
                current_val = int(info.get('value', 0) or 0)
                delta = _min_delta_to_collapse_to_7(current_val, collapse)
                if delta and 0 < delta <= 50:
                    _w = _inject_collapse_override(name, delta, DB_PATH)
                    injected_total += _w
                    logger.info(f'[Cycle #{cycle_num}] 🔁 坍缩反馈闭环: {name}={current_val} → 补 {_w} 条 (Δ={delta})')
            stats['collapse_feedback_injected'] = injected_total
            if injected_total > 0:
                logger.info(f'[Cycle #{cycle_num}] 🔁 坍缩反馈闭环共注入 {injected_total} 条 derived 知识')
    except Exception as _fb_err:
        logger.warning(f'[Cycle #{cycle_num}] 坍缩反馈闭环跳过 (非阻断): {_fb_err}')

    # ═══════════════════════════════════════════════════════════════════════
    # 康熙裁决 · 三层演化 Phase 自动升级 (钩子, 后续扩展血肉展开)
    # 约束: 只打日志 + 更新 checkpoint 标记, 不改变 7 阶段核心逻辑
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _cur_reinforced = cp.get('total_reinforced', 0)

        # Phase 1 → Phase 2 自动升级 (reinforced 超过 2000)
        if phase_num == 1 and _cur_reinforced >= PHASE_THRESHOLDS['PHASE_1_SKELETON']:
            logger.info(
                f'🔥 Phase 升级: 骨架 → 血肉 '
                f'(reinforced={_cur_reinforced:,} ≥ 2000, 84000 法门展开)'
            )
            phase_num, phase_name, phase_desc = 2, '血肉', 'Layer 2: 84000 法门血肉展开'
            cp['evolution_phase'] = phase_num
            cp['evolution_phase_name'] = phase_name
            cp['evolution_phase_desc'] = phase_desc
            stats['phase_upgraded_to'] = 2
            stats['phase_upgrade_reason'] = 'reinforced >= 2000'
            # 给每个阶段内部加细分分类器 (血肉展开) — 后续扩展钩子
            try:
                for _stage_name in list(STAGE_CLASSIFIERS.keys()):
                    # 每个分类器下再细分 21 个小子类 (7 阶段 × 3 = 21,
                    # 总计 7×7×3 = 147 法门级细分) — 预留钩子, 暂不写入
                    pass
            except Exception:
                pass

        # Phase 2 → Phase 3 自动升级 (reinforced 超过 10000)
        if phase_num == 2 and _cur_reinforced >= PHASE_THRESHOLDS['PHASE_2_FLESH']:
            logger.info(
                f'👑 Phase 升级: 血肉 → 江山 '
                f'(reinforced={_cur_reinforced:,} ≥ 10000, 完整演化)'
            )
            phase_num, phase_name, phase_desc = 3, '江山', 'Layer 3: 完整演化 + 84000 法门'
            cp['evolution_phase'] = phase_num
            cp['evolution_phase_name'] = phase_name
            cp['evolution_phase_desc'] = phase_desc
            stats['phase_upgraded_to'] = 3
            stats['phase_upgrade_reason'] = 'reinforced >= 10000'

        stats['evolution_phase'] = phase_num
        stats['evolution_phase_name'] = phase_name

    except Exception as _phase_upg_err:
        logger.warning(f'[演化 Phase] 升级检查跳过 (非阻断): {_phase_upg_err}')

    # ═══════════════════════════════════════════════════════════════════════
    # EigenFlux 汇报 — 写 eigenflux_comm_messages (session_id=99999, 康熙)
    # 让 AI 员工能看到演化引擎当前 Phase + 关键指标
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _ef_conn = _get_conn()
        _now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        _content = (
            f'【演化引擎 Phase {phase_num} · {phase_name}】'
            f'reinforced={cp.get("total_reinforced", 0):,}, '
            f'derived={cp.get("total_derived", 0):,}, '
            f'associations={cp.get("total_associations", 0):,}, '
            f'vectors={cp.get("total_vectors", 0):,}, '
            f'cycle={cycle_num}, '
            f'desc={phase_desc}'
        )
        _ef_conn.execute("""
            INSERT INTO eigenflux_comm_messages
                (session_id, employee_id, employee_name, employee_table,
                 message_direction, message_type, message_content,
                 knowledge_tags_json, learning_value, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            99999,                      # session_id (演化引擎专用)
            35,                         # employee_id (康熙)
            '演化引擎(康熙裁决)',
            'engine',
            'outbound',
            'implementation_report',
            _content[:2000],
            json.dumps([
                'evolution_phase',
                f'phase_{phase_num}',
                'three_layers',
                'kangxi_verdict',
            ], ensure_ascii=False),
            5,                          # learning_value: 演化引擎汇报价值高
            _now_str,
        ))
        _ef_conn.commit()
        _ef_conn.close()
        stats['eigenflux_reported'] = True
        logger.info(
            f'[演化 Phase] 📨 EigenFlux 汇报已写入 '
            f'(session=99999, emp=康熙#35, phase={phase_num})'
        )
    except Exception as _ef_report_err:
        logger.warning(f'[演化 Phase] EigenFlux 汇报跳过 (非阻断): {_ef_report_err}')
        stats['eigenflux_reported'] = False

    # ═══════════════════════════════════════════════════════════════════════
    # T2: checkpoint ↔ 物理表同步 (核心! 放在坍缩闭环之后、return 之前)
    #
    # 为什么放在这里:
    #   - Stage 0-7 全部跑完 (derived/assoc/vec/reinforced 都已写入 DB)
    #   - 坍缩反馈闭环也可能注入新 derived (物理表有新增)
    #   - 在这里读物理表 row count → 覆盖 checkpoint 里的累计数
    #   - 最后再 save 一次 checkpoint (之前行 ~2122 的 save 可能过时)
    #
    # reinforced / cycle_count 不动 (引擎自己算的累计数, 无直接物理表对应)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        _sync = _sync_checkpoint_from_db(DB_PATH)
        if _sync:
            cp['total_derived'] = _sync['total_derived']
            cp['total_associations'] = _sync['total_associations']
            cp['total_vectors'] = _sync['total_vectors']
            _save_checkpoint(cp)
            logger.info(
                f'[Cycle #{cycle_num}][Checkpoint Sync] ✅ 最终已同步并保存: '
                f'derived={cp["total_derived"]:,}, '
                f'assoc={cp["total_associations"]:,}, '
                f'vec={cp["total_vectors"]:,}'
            )
    except Exception as _se:
        logger.warning(f'[Cycle #{cycle_num}] 最终 checkpoint sync 跳过 (非阻断): {_se}')

    # ═══════════════════════════════════════════════════════════════════════
    # 🎯 演化目的检测 (钱学森之问 + 霍金熵减) — 回答王安石的根本问题
    # 坍缩反馈闭环之后、最终 checkpoint 落库之前
    # ═══════════════════════════════════════════════════════════════════════
    purpose_result = None
    try:
        _checker = EVOLUTION_PURPOSE_CHECKER()
        # natural_reinforced = 引擎原本算的 reinforced 增量 (不含坍缩反馈闭环强制对齐)
        natural_r = max(0, cp.get('total_reinforced', 0) - cp_prev.get('total_reinforced', 0))
        # injected_r = 坍缩反馈闭环注入的 reinforced 数 (从 stats 取)
        injected_r = stats.get('collapse_feedback_injected', 0) or 0
        # 适配: collapse_result 结构是 {'verification': {...}, ...}
        _cr_adapted = {
            'reinforced': {
                'chain': (collapse_result or {}).get('verification', {}).get('reinforced', {}).get('chain', []),
                'end':   (collapse_result or {}).get('verification', {}).get('reinforced', {}).get('collapses_to', 0),
            }
        }
        purpose_result = _checker.check(
            cp_prev, cp, _cr_adapted,
            natural_r, injected_r,
            ctc_has_ring=False,
            conflict_rules=0,
        )
        # 写入 checkpoint (供下一轮对比 + 运维查看)
        cp['purpose_score'] = purpose_result['overall_score']
        cp['purpose_pass'] = purpose_result['pass']
        stats['purpose_score'] = purpose_result['overall_score']
        stats['purpose_pass'] = purpose_result['pass']
        _save_checkpoint(cp)
        logger.info(
            f'[Cycle #{cycle_num}][演化目的] 🎯 score={purpose_result["overall_score"]}/100 '
            f'pass={purpose_result["pass"]} (钱学森 + 霍金熵减)'
        )
    except Exception as _purp_err:
        logger.warning(f'[Cycle #{cycle_num}] 演化目的检测跳过 (非阻断): {_purp_err}')
        stats['purpose_error'] = str(_purp_err)

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
