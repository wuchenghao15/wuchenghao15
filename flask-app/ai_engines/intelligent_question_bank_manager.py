#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 智能化题库管理系统 (IntelligentQuestionBankManager)
=========================================================
在现有 AIQuestionAuthoringEngine (IRT3PL/查重/质量评估) 之上构建智能化管理层：

  1. KnowledgeGraphManager      — 知识点图谱（树+依赖关系+覆盖率分析）
  2. IntelligentPaperComposer   — 遗传算法智能组卷（蓝图约束+多目标优化）
  3. QuestionLifecycleManager   — 题目生命周期状态机
  4. AdaptiveLearningPath       — 自适应学习路径（薄弱知识点+个性化推荐）
  5. BankHealthAnalyzer         — 题库健康度（覆盖率/新鲜度/质量/难度分布+缺口分析）
  6. SmartTagRecommender        — 智能标签推荐（关键词提取+相似题目标签）

遵循:
  - SSOT 数据库权威源 + 实时写入
  - 超级管理员 wuchenghao15 IRON_RULE级配置
  - 所有公开方法含输入校验（防注入）
  - 线程安全单例

版本: v1.0.0
"""

import os
import sys
import json
import time
import math
import random
import re
import sqlite3
import logging
import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('intelligent_question_bank_manager')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'app.db')

_SUPER_ADMIN_UN = "wuchenghao15"

# 合法枚举值（防注入）
_VALID_SUBJECTS = {'语文', '数学', '英语', '政治', '日语', '物理', '化学', '生物',
                    '历史', '地理', '通用'}
_VALID_QTYPES = {'single_choice', 'multiple_choice', 'true_false', 'fill_blank',
                 'short_answer', 'essay', 'listening', 'calculation', 'reading'}
_VALID_DIFFICULTY = {'easy', 'medium_easy', 'medium', 'medium_hard', 'hard'}
_VALID_LIFECYCLE = {'draft', 'review', 'published', 'active', 'deprecated', 'archived'}
_VALID_NODE_TYPE = {'root', 'chapter', 'section', 'knowledge_point', 'sub_point'}


def _safe_str(val, max_len=500):
    """安全字符串校验（防XSS/注入）"""
    if not isinstance(val, str):
        return ''
    if len(val) > max_len:
        return val[:max_len]
    if re.search(r'[<>{}]|script:|expression\(|javascript:', val, re.I):
        return re.sub(r'[<>{}]|script:|expression\(|javascript:', '', val, flags=re.I)
    return val.strip()


def _safe_id(val):
    """安全ID校验（仅允许字母数字下划线连字符）"""
    if isinstance(val, str) and re.match(r'^[a-zA-Z0-9_\-]+$', val) and len(val) <= 100:
        return val
    return None


def _safe_enum(val, allowed):
    """枚举校验"""
    try:
        return val if val in allowed else None
    except TypeError:
        return None


def _safe_int(val, default=0, lo=None, hi=None):
    """整数校验"""
    try:
        v = int(val)
        if lo is not None and v < lo:
            return lo
        if hi is not None and v > hi:
            return hi
        return v
    except (TypeError, ValueError):
        return default


def _safe_float(val, default=0.0, lo=0.0, hi=1.0):
    """浮点数校验"""
    try:
        v = float(val)
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v
    except (TypeError, ValueError):
        return default


def _get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ============================================================================
# 1. 知识点图谱管理器
# ============================================================================

class KnowledgeGraphManager:
    """知识点图谱管理 — 树形结构 + 依赖关系 + 覆盖率分析"""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        with _get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_knowledge_graph (
                node_id TEXT PRIMARY KEY,
                parent_id TEXT,
                subject TEXT NOT NULL,
                node_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                depth INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                question_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_knowledge_deps (
                dep_id TEXT PRIMARY KEY,
                from_node TEXT NOT NULL,
                to_node TEXT NOT NULL,
                dep_type TEXT DEFAULT 'prerequisite',
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_node) REFERENCES iqbm_knowledge_graph(node_id),
                FOREIGN KEY (to_node) REFERENCES iqbm_knowledge_graph(node_id)
            )''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_kg_parent ON iqbm_knowledge_graph(parent_id)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_kg_subject ON iqbm_knowledge_graph(subject)''')
            conn.commit()

    def add_node(self, node_id: str, subject: str, node_type: str, name: str,
                 parent_id: str = None, description: str = None) -> Dict[str, Any]:
        """添加知识点节点"""
        node_id = _safe_id(node_id)
        if not node_id:
            return {'success': False, 'error': 'node_id无效（仅允许字母数字下划线连字符）'}
        subject = _safe_enum(subject, _VALID_SUBJECTS) or '通用'
        node_type = _safe_enum(node_type, _VALID_NODE_TYPE) or 'knowledge_point'
        name = _safe_str(name, 200)
        if not name:
            return {'success': False, 'error': 'name不能为空'}
        parent_id = _safe_id(parent_id) if parent_id else None
        description = _safe_str(description, 1000) if description else None

        depth = 0
        if parent_id:
            with _get_db() as conn:
                row = conn.execute('SELECT depth FROM iqbm_knowledge_graph WHERE node_id=?',
                                   (parent_id,)).fetchone()
                if row:
                    depth = row['depth'] + 1
                else:
                    return {'success': False, 'error': f'父节点 {parent_id} 不存在'}

        try:
            with _get_db() as conn:
                conn.execute('''INSERT OR REPLACE INTO iqbm_knowledge_graph
                    (node_id, parent_id, subject, node_type, name, description, depth)
                    VALUES (?,?,?,?,?,?,?)''',
                    (node_id, parent_id, subject, node_type, name, description, depth))
                conn.commit()
            logger.info(f"知识点节点已添加: {node_id} ({name})")
            return {'success': True, 'node_id': node_id, 'depth': depth}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_dependency(self, from_node: str, to_node: str,
                       dep_type: str = 'prerequisite', weight: float = 1.0) -> Dict[str, Any]:
        """添加知识点依赖关系（from_node 依赖 to_node，即 to_node 是 from_node 的前置）"""
        from_node = _safe_id(from_node)
        to_node = _safe_id(to_node)
        if not from_node or not to_node:
            return {'success': False, 'error': '节点ID无效'}
        if from_node == to_node:
            return {'success': False, 'error': '不能自依赖'}
        dep_type = _safe_str(dep_type, 50) or 'prerequisite'
        weight = _safe_float(weight, 1.0, 0.0, 1.0)
        dep_id = f"dep_{from_node}_{to_node}"

        # 检查循环依赖
        if self._has_cycle(from_node, to_node):
            return {'success': False, 'error': '检测到循环依赖，拒绝添加'}

        try:
            with _get_db() as conn:
                conn.execute('''INSERT OR REPLACE INTO iqbm_knowledge_deps
                    (dep_id, from_node, to_node, dep_type, weight) VALUES (?,?,?,?,?)''',
                    (dep_id, from_node, to_node, dep_type, weight))
                conn.commit()
            return {'success': True, 'dep_id': dep_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _has_cycle(self, from_node: str, to_node: str, visited: set = None) -> bool:
        """DFS检测循环依赖"""
        if visited is None:
            visited = set()
        if to_node == from_node:
            return True
        if to_node in visited:
            return False
        visited.add(to_node)
        with _get_db() as conn:
            rows = conn.execute('SELECT to_node FROM iqbm_knowledge_deps WHERE from_node=?',
                                (to_node,)).fetchall()
        for r in rows:
            if self._has_cycle(from_node, r['to_node'], visited):
                return True
        return False

    def get_tree(self, subject: str = None, parent_id: str = None) -> List[Dict]:
        """获取知识点树"""
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        parent_id = _safe_id(parent_id) if parent_id else None
        with _get_db() as conn:
            if parent_id:
                rows = conn.execute('SELECT * FROM iqbm_knowledge_graph WHERE parent_id=? ORDER BY sort_order',
                                    (parent_id,)).fetchall()
            elif subject:
                rows = conn.execute('SELECT * FROM iqbm_knowledge_graph WHERE subject=? AND parent_id IS NULL ORDER BY sort_order',
                                    (subject,)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM iqbm_knowledge_graph WHERE parent_id IS NULL ORDER BY sort_order').fetchall()
        result = []
        for r in rows:
            node = dict(r)
            node['children'] = self.get_tree(subject, r['node_id'])
            result.append(node)
        return result

    def get_coverage(self, subject: str = None) -> Dict[str, Any]:
        """知识点覆盖率分析"""
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        with _get_db() as conn:
            if subject:
                total = conn.execute('SELECT COUNT(*) as c FROM iqbm_knowledge_graph WHERE subject=?',
                                     (subject,)).fetchone()['c']
                covered = conn.execute('SELECT COUNT(*) as c FROM iqbm_knowledge_graph WHERE subject=? AND question_count>0',
                                       (subject,)).fetchone()['c']
            else:
                total = conn.execute('SELECT COUNT(*) as c FROM iqbm_knowledge_graph').fetchone()['c']
                covered = conn.execute('SELECT COUNT(*) as c FROM iqbm_knowledge_graph WHERE question_count>0').fetchone()['c']
        rate = round(covered / total * 100, 1) if total > 0 else 0
        return {'total_nodes': total, 'covered_nodes': covered,
                'uncovered_nodes': total - covered, 'coverage_rate': f'{rate}%'}

    def get_prerequisite_chain(self, node_id: str) -> List[str]:
        """获取前置知识点链"""
        node_id = _safe_id(node_id)
        if not node_id:
            return []
        chain = []
        visited = set()
        self._collect_prereqs(node_id, chain, visited)
        return chain

    def _collect_prereqs(self, node_id: str, chain: List[str], visited: set):
        if node_id in visited:
            return
        visited.add(node_id)
        with _get_db() as conn:
            rows = conn.execute('SELECT to_node FROM iqbm_knowledge_deps WHERE from_node=?',
                                (node_id,)).fetchall()
        for r in rows:
            if r['to_node'] not in visited:
                chain.append(r['to_node'])
                self._collect_prereqs(r['to_node'], chain, visited)

    def delete_node(self, node_id: str) -> Dict[str, Any]:
        """删除知识点节点（级联删除子节点和依赖）"""
        node_id = _safe_id(node_id)
        if not node_id:
            return {'success': False, 'error': 'node_id无效'}
        try:
            with _get_db() as conn:
                # 删除依赖
                conn.execute('DELETE FROM iqbm_knowledge_deps WHERE from_node=? OR to_node=?',
                             (node_id, node_id))
                # 递归删除子节点
                children = conn.execute('SELECT node_id FROM iqbm_knowledge_graph WHERE parent_id=?',
                                        (node_id,)).fetchall()
                for child in children:
                    self.delete_node(child['node_id'])
                conn.execute('DELETE FROM iqbm_knowledge_graph WHERE node_id=?', (node_id,))
                conn.commit()
            return {'success': True, 'deleted': node_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================================================
# 2. 智能组卷引擎（遗传算法）
# ============================================================================

class IntelligentPaperComposer:
    """遗传算法智能组卷 — 蓝图约束 + 多目标优化"""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        with _get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_paper_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                total_score REAL DEFAULT 100,
                duration_min INTEGER DEFAULT 120,
                config TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_composed_papers (
                paper_id TEXT PRIMARY KEY,
                blueprint_id TEXT,
                subject TEXT NOT NULL,
                name TEXT NOT NULL,
                question_ids TEXT NOT NULL,
                total_score REAL,
                stats TEXT,
                composed_by TEXT,
                composed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blueprint_id) REFERENCES iqbm_paper_blueprints(blueprint_id)
            )''')
            conn.commit()

    def save_blueprint(self, blueprint_id: str, name: str, subject: str,
                       config: Dict, total_score: float = 100,
                       duration_min: int = 120, created_by: str = 'system') -> Dict[str, Any]:
        """保存组卷蓝图"""
        blueprint_id = _safe_id(blueprint_id)
        if not blueprint_id:
            return {'success': False, 'error': 'blueprint_id无效'}
        name = _safe_str(name, 200)
        subject = _safe_enum(subject, _VALID_SUBJECTS) or '通用'
        total_score = _safe_float(total_score, 100, 1, 1000)
        duration_min = _safe_int(duration_min, 120, 1, 600)
        created_by = _safe_str(created_by, 50)

        # 校验config结构
        if not isinstance(config, dict):
            return {'success': False, 'error': 'config必须是字典'}
        # 防注入：序列化前校验
        config_str = json.dumps(config, ensure_ascii=False)
        if len(config_str) > 10000:
            return {'success': False, 'error': 'config过大'}

        try:
            with _get_db() as conn:
                conn.execute('''INSERT OR REPLACE INTO iqbm_paper_blueprints
                    (blueprint_id, name, subject, total_score, duration_min, config, created_by)
                    VALUES (?,?,?,?,?,?,?)''',
                    (blueprint_id, name, subject, total_score, duration_min, config_str, created_by))
                conn.commit()
            return {'success': True, 'blueprint_id': blueprint_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def compose_paper(self, subject: str, blueprint_config: Dict,
                      paper_name: str = None, composed_by: str = 'system',
                      population_size: int = 50, generations: int = 100) -> Dict[str, Any]:
        """
        遗传算法智能组卷
        blueprint_config: {
            "sections": [
                {"qtype": "single_choice", "count": 20, "score_per_q": 2,
                 "difficulty": {"easy": 0.2, "medium_easy": 0.2, "medium": 0.3, "medium_hard": 0.2, "hard": 0.1},
                 "knowledge_points": ["kp_001", "kp_002"]}
            ]
        }
        """
        subject = _safe_enum(subject, _VALID_SUBJECTS) or '通用'
        if not isinstance(blueprint_config, dict) or 'sections' not in blueprint_config:
            return {'success': False, 'error': 'blueprint_config必须包含sections'}
        sections = blueprint_config['sections']
        if not isinstance(sections, list) or len(sections) == 0:
            return {'success': False, 'error': 'sections不能为空'}
        if len(sections) > 50:
            return {'success': False, 'error': 'sections数量超出限制(50)'}
        population_size = _safe_int(population_size, 50, 10, 200)
        generations = _safe_int(generations, 100, 10, 500)
        paper_name = _safe_str(paper_name, 200) or f"智能组卷_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        composed_by = _safe_str(composed_by, 50)

        # 校验每个section
        for sec in sections:
            qtype = _safe_enum(sec.get('qtype'), _VALID_QTYPES)
            if not qtype:
                return {'success': False, 'error': f'题型无效: {sec.get("qtype")}'}
            count = _safe_int(sec.get('count'), 0, 1, 200)
            if count < 1:
                return {'success': False, 'error': '题目数量必须≥1'}

        # 加载题库候选题目
        candidates = self._load_candidates(subject, sections)
        if not candidates:
            return {'success': False, 'error': f'科目 {subject} 无可用题目'}

        # 遗传算法优化
        best_paper = self._genetic_optimize(candidates, sections, population_size, generations)

        if not best_paper:
            return {'success': False, 'error': '组卷失败：候选题目不足或约束过严'}

        # 计算统计
        total_score = sum(sec.get('score_per_q', 0) * sec.get('count', 0) for sec in sections)
        question_ids = [q['question_id'] for q in best_paper]
        stats = {
            'question_count': len(question_ids),
            'total_score': total_score,
            'difficulty_dist': self._calc_difficulty_dist(best_paper),
            'qtype_dist': self._calc_qtype_dist(best_paper),
        }

        paper_id = f"paper_{int(time.time()*1000)}_{random.randint(1000,9999)}"
        try:
            with _get_db() as conn:
                conn.execute('''INSERT INTO iqbm_composed_papers
                    (paper_id, blueprint_id, subject, name, question_ids, total_score, stats, composed_by)
                    VALUES (?,?,?,?,?,?,?,?)''',
                    (paper_id, None, subject, paper_name, json.dumps(question_ids),
                     total_score, json.dumps(stats, ensure_ascii=False), composed_by))
                conn.commit()
        except Exception as e:
            logger.warning(f"组卷结果保存失败: {e}")

        return {'success': True, 'paper_id': paper_id, 'paper_name': paper_name,
                'question_ids': question_ids, 'stats': stats, 'total_score': total_score}

    def _load_candidates(self, subject: str, sections: List[Dict]) -> Dict[str, List[Dict]]:
        """按题型加载候选题目"""
        candidates = {}
        for sec in sections:
            qtype = sec.get('qtype')
            if qtype not in candidates:
                try:
                    with _get_db() as conn:
                        rows = conn.execute(
                            '''SELECT question_id, subject, question_type, difficulty,
                                      difficulty_value, content, knowledge_point, quality_score
                               FROM ai_authored_questions
                               WHERE subject=? AND question_type=? AND status IN ('published','active')
                               ORDER BY quality_score DESC LIMIT 500''',
                            (subject, qtype)).fetchall()
                    candidates[qtype] = [dict(r) for r in rows]
                except Exception:
                    candidates[qtype] = []
        return candidates

    def _genetic_optimize(self, candidates: Dict[str, List], sections: List[Dict],
                          pop_size: int, generations: int) -> Optional[List[Dict]]:
        """遗传算法优化组卷"""
        # 初始化种群
        population = []
        for _ in range(pop_size):
            individual = []
            for sec in sections:
                qtype = sec.get('qtype')
                count = sec.get('count', 0)
                pool = candidates.get(qtype, [])
                if len(pool) < count:
                    return None
                selected = random.sample(pool, count)
                individual.extend(selected)
            population.append(individual)

        # 进化
        for gen in range(generations):
            # 评估适应度
            scored = [(ind, self._fitness(ind, sections)) for ind in population]
            scored.sort(key=lambda x: x[1], reverse=True)

            # 精英保留 + 锦标赛选择
            elite_count = max(2, pop_size // 5)
            new_pop = [ind for ind, _ in scored[:elite_count]]

            while len(new_pop) < pop_size:
                parent1 = self._tournament(scored)
                parent2 = self._tournament(scored)
                child = self._crossover(parent1, parent2, sections, candidates)
                if random.random() < 0.1:
                    child = self._mutate(child, sections, candidates)
                new_pop.append(child)

            population = new_pop

        # 返回最优解
        scored = [(ind, self._fitness(ind, sections)) for ind in population]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None

    def _fitness(self, individual: List[Dict], sections: Dict) -> float:
        """适应度函数（越高越好）"""
        score = 0.0
        idx = 0
        for sec in sections:
            count = sec.get('count', 0)
            section_qs = individual[idx:idx + count]
            idx += count

            # 难度分布匹配
            target_dist = sec.get('difficulty', {})
            if target_dist:
                actual = {}
                for q in section_qs:
                    d = q.get('difficulty', 'medium')
                    actual[d] = actual.get(d, 0) + 1
                for diff, target_ratio in target_dist.items():
                    target_count = target_ratio * count
                    actual_count = actual.get(diff, 0)
                    score -= abs(target_count - actual_count) * 2

            # 知识点覆盖
            kps = sec.get('knowledge_points', [])
            if kps:
                covered = set()
                for q in section_qs:
                    kp = q.get('knowledge_point', '')
                    if kp:
                        covered.add(kp)
                score += len(covered & set(kps)) * 3

            # 质量分
            score += sum(q.get('quality_score', 0) for q in section_qs)

        # 重复惩罚
        qids = [q.get('question_id') for q in individual]
        if len(qids) != len(set(qids)):
            score -= 50

        return score

    def _tournament(self, scored: List, k: int = 3) -> List[Dict]:
        """锦标赛选择"""
        contestants = random.sample(scored, min(k, len(scored)))
        return max(contestants, key=lambda x: x[1])[0]

    def _crossover(self, p1: List[Dict], p2: List[Dict],
                   sections: List[Dict], candidates: Dict) -> List[Dict]:
        """交叉操作（按section分段交叉）"""
        child = []
        idx = 0
        for sec in sections:
            count = sec.get('count', 0)
            source = p1 if random.random() < 0.5 else p2
            child.extend(source[idx:idx + count])
            idx += count
        return child

    def _mutate(self, individual: List[Dict], sections: List[Dict],
                candidates: Dict) -> List[Dict]:
        """变异操作（随机替换一个section的题目）"""
        if not sections:
            return individual
        sec_idx = random.randint(0, len(sections) - 1)
        sec = sections[sec_idx]
        qtype = sec.get('qtype')
        count = sec.get('count', 0)
        pool = candidates.get(qtype, [])
        if len(pool) >= count:
            idx = sum(s.get('count', 0) for s in sections[:sec_idx])
            new_qs = random.sample(pool, count)
            individual[idx:idx + count] = new_qs
        return individual

    def _calc_difficulty_dist(self, questions: List[Dict]) -> Dict[str, int]:
        dist = {}
        for q in questions:
            d = q.get('difficulty', 'medium')
            dist[d] = dist.get(d, 0) + 1
        return dist

    def _calc_qtype_dist(self, questions: List[Dict]) -> Dict[str, int]:
        dist = {}
        for q in questions:
            t = q.get('question_type', 'unknown')
            dist[t] = dist.get(t, 0) + 1
        return dist

    def list_blueprints(self, subject: str = None) -> List[Dict]:
        """列出组卷蓝图"""
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        with _get_db() as conn:
            if subject:
                rows = conn.execute('SELECT * FROM iqbm_paper_blueprints WHERE subject=? ORDER BY created_at DESC',
                                    (subject,)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM iqbm_paper_blueprints ORDER BY created_at DESC').fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d['config'] = json.loads(d['config']) if d['config'] else {}
            result.append(d)
        return result

    def list_papers(self, subject: str = None, limit: int = 50) -> List[Dict]:
        """列出已组卷的试卷"""
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        limit = _safe_int(limit, 50, 1, 500)
        with _get_db() as conn:
            if subject:
                rows = conn.execute('SELECT * FROM iqbm_composed_papers WHERE subject=? ORDER BY composed_at DESC LIMIT ?',
                                    (subject, limit)).fetchall()
            else:
                rows = conn.execute('SELECT * FROM iqbm_composed_papers ORDER BY composed_at DESC LIMIT ?',
                                    (limit,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d['question_ids'] = json.loads(d['question_ids']) if d['question_ids'] else []
            d['stats'] = json.loads(d['stats']) if d['stats'] else {}
            result.append(d)
        return result


# ============================================================================
# 3. 题目生命周期管理器
# ============================================================================

class QuestionLifecycleManager:
    """题目生命周期状态机 — draft→review→published→active→deprecated→archived"""

    LIFECYCLE_TRANSITIONS = {
        'draft': ['review', 'archived'],
        'review': ['published', 'draft', 'archived'],
        'published': ['active', 'deprecated', 'archived'],
        'active': ['deprecated', 'archived'],
        'deprecated': ['archived', 'active'],
        'archived': [],
    }

    AUTO_TRANSITION_RULES = {
        # 正确率过低 → deprecated
        'low_correct_rate': {'threshold': 0.2, 'from': 'active', 'to': 'deprecated'},
        # 使用率过低（老化）→ deprecated
        'low_usage': {'threshold': 0, 'from': 'active', 'to': 'deprecated', 'days_unused': 180},
        # 质量分过低 → deprecated
        'low_quality': {'threshold': 0.3, 'from': 'active', 'to': 'deprecated'},
    }

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        with _get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_lifecycle_events (
                event_id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                trigger_type TEXT DEFAULT 'manual',
                trigger_reason TEXT,
                operator TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_le_qid ON iqbm_lifecycle_events(question_id)''')
            conn.commit()

    def transition(self, question_id: str, to_state: str,
                   operator: str = 'system', reason: str = None) -> Dict[str, Any]:
        """手动状态转换"""
        question_id = _safe_str(question_id, 100)
        if not question_id:
            return {'success': False, 'error': 'question_id无效'}
        to_state = _safe_enum(to_state, _VALID_LIFECYCLE)
        if not to_state:
            return {'success': False, 'error': f'目标状态无效，合法值: {_VALID_LIFECYCLE}'}
        operator = _safe_str(operator, 50)
        reason = _safe_str(reason, 500) if reason else None

        # 获取当前状态
        current_state = self._get_current_state(question_id)
        if current_state is None:
            # 题目不在ai_authored_questions表，仅记录事件
            current_state = 'draft'

        # 校验转换合法性
        allowed = self.LIFECYCLE_TRANSITIONS.get(current_state, [])
        if to_state not in allowed:
            return {'success': False, 'error': f'非法状态转换: {current_state}→{to_state}，允许: {allowed}'}

        # 记录事件
        event_id = f"evt_{int(time.time()*1000)}_{random.randint(1000,9999)}"
        try:
            with _get_db() as conn:
                conn.execute('''INSERT INTO iqbm_lifecycle_events
                    (event_id, question_id, from_state, to_state, trigger_type, trigger_reason, operator)
                    VALUES (?,?,?,?,?,?,?)''',
                    (event_id, question_id, current_state, to_state, 'manual', reason, operator))
                # 更新题目状态
                conn.execute('UPDATE ai_authored_questions SET status=?, reviewed_at=CURRENT_TIMESTAMP WHERE question_id=?',
                             (to_state, question_id))
                conn.commit()
        except Exception as e:
            return {'success': False, 'error': str(e)}

        logger.info(f"题目 {question_id} 状态转换: {current_state}→{to_state} (操作人: {operator})")
        return {'success': True, 'event_id': event_id,
                'question_id': question_id, 'from': current_state, 'to': to_state}

    def _get_current_state(self, question_id: str) -> Optional[str]:
        """获取题目当前状态"""
        try:
            with _get_db() as conn:
                row = conn.execute('SELECT status FROM ai_authored_questions WHERE question_id=?',
                                   (question_id,)).fetchone()
                return row['status'] if row else None
        except Exception:
            return None

    def get_lifecycle_history(self, question_id: str, limit: int = 50) -> List[Dict]:
        """获取题目生命周期历史"""
        question_id = _safe_str(question_id, 100)
        limit = _safe_int(limit, 50, 1, 500)
        with _get_db() as conn:
            rows = conn.execute('''SELECT * FROM iqbm_lifecycle_events
                                   WHERE question_id=? ORDER BY created_at DESC LIMIT ?''',
                                (question_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def auto_transition_scan(self) -> Dict[str, Any]:
        """自动状态转换扫描（基于使用率/正确率/质量分）"""
        transitions = []
        try:
            with _get_db() as conn:
                # 查找active状态的题目
                rows = conn.execute('''SELECT question_id, correct_rate, usage_count, quality_score,
                                              generated_at
                                       FROM ai_authored_questions WHERE status='active' ''').fetchall()
        except sqlite3.OperationalError:
            return {'success': True, 'scanned': 0, 'auto_transitioned': 0, 'transitions': []}
        try:
                now = datetime.now()
                for row in rows:
                    should_deprecate = False
                    reason = ''

                    # 正确率过低
                    if row['correct_rate'] < self.AUTO_TRANSITION_RULES['low_correct_rate']['threshold']:
                        should_deprecate = True
                        reason = f"正确率过低({row['correct_rate']:.1%})"

                    # 质量分过低
                    if row['quality_score'] < self.AUTO_TRANSITION_RULES['low_quality']['threshold']:
                        should_deprecate = True
                        reason = f"质量分过低({row['quality_score']:.2f})"

                    # 使用率过低（180天未使用）
                    if row['usage_count'] == 0 and row['generated_at']:
                        try:
                            gen_time = datetime.fromisoformat(row['generated_at'].replace('Z', ''))
                            days_unused = (now - gen_time).days
                            if days_unused > 180:
                                should_deprecate = True
                                reason = f"已{days_unused}天未使用"
                        except Exception:
                            pass

                    if should_deprecate:
                        result = self.transition(row['question_id'], 'deprecated',
                                                 operator='auto_system', reason=reason)
                        if result.get('success'):
                            transitions.append(result)
        except Exception as e:
            return {'success': False, 'error': str(e), 'transitions': transitions}

        return {'success': True, 'scanned': len(rows), 'auto_transitioned': len(transitions),
                'transitions': transitions}

    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """生命周期统计"""
        stats = {s: 0 for s in _VALID_LIFECYCLE}
        try:
            with _get_db() as conn:
                for state in _VALID_LIFECYCLE:
                    count = conn.execute('SELECT COUNT(*) as c FROM ai_authored_questions WHERE status=?',
                                         (state,)).fetchone()['c']
                    stats[state] = count
        except sqlite3.OperationalError:
            pass  # ai_authored_questions 表尚未创建
        total = sum(stats.values())
        return {'distribution': stats, 'total': total}


# ============================================================================
# 4. 自适应学习路径
# ============================================================================

class AdaptiveLearningPath:
    """自适应学习路径 — 薄弱知识点识别 + 个性化推荐"""

    def __init__(self, knowledge_graph: KnowledgeGraphManager):
        self.kg = knowledge_graph
        self._init_tables()

    def _init_tables(self):
        with _get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS iqbm_learning_paths (
                path_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                weak_points TEXT NOT NULL,
                recommended_path TEXT NOT NULL,
                mastery_level REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_lp_student ON iqbm_learning_paths(student_id)''')
            conn.commit()

    def analyze_weakness(self, student_id: str, subject: str,
                         answer_records: List[Dict]) -> Dict[str, Any]:
        """分析薄弱知识点"""
        student_id = _safe_str(student_id, 100)
        subject = _safe_enum(subject, _VALID_SUBJECTS) or '通用'
        if not isinstance(answer_records, list) or not answer_records:
            return {'success': False, 'error': '答题记录不能为空'}
        if len(answer_records) > 10000:
            return {'success': False, 'error': '答题记录数量超出限制(10000)'}

        # 按知识点统计正确率
        kp_stats = {}
        for rec in answer_records:
            if not isinstance(rec, dict):
                continue
            kp = _safe_str(rec.get('knowledge_point', ''), 100)
            is_correct = bool(rec.get('is_correct', False))
            if kp:
                if kp not in kp_stats:
                    kp_stats[kp] = {'total': 0, 'correct': 0}
                kp_stats[kp]['total'] += 1
                if is_correct:
                    kp_stats[kp]['correct'] += 1

        # 识别薄弱知识点（正确率<60%）
        weak_points = []
        for kp, stats in kp_stats.items():
            rate = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            if rate < 0.6:
                weak_points.append({
                    'knowledge_point': kp,
                    'correct_rate': round(rate, 3),
                    'total_questions': stats['total'],
                    'severity': 'high' if rate < 0.3 else 'medium' if rate < 0.5 else 'low',
                })

        weak_points.sort(key=lambda x: x['correct_rate'])

        # 生成推荐路径（基于前置知识点链）
        recommended_path = []
        for wp in weak_points[:10]:  # 取最弱的10个
            kp = wp['knowledge_point']
            prereqs = self.kg.get_prerequisite_chain(kp)
            # 先补前置知识点，再学当前知识点
            for pre in prereqs:
                if pre not in [r['knowledge_point'] for r in recommended_path]:
                    recommended_path.append({
                        'knowledge_point': pre,
                        'action': 'review_prerequisite',
                        'reason': f'{kp}的前置知识点',
                    })
            recommended_path.append({
                'knowledge_point': kp,
                'action': 'practice_weak',
                'reason': f"正确率{wp['correct_rate']:.0%}，需加强",
            })

        # 计算掌握度
        total_correct = sum(s['correct'] for s in kp_stats.values())
        total_q = sum(s['total'] for s in kp_stats.values())
        mastery = round(total_correct / total_q, 3) if total_q > 0 else 0

        # 保存
        path_id = f"path_{student_id}_{subject}_{int(time.time())}"
        try:
            with _get_db() as conn:
                conn.execute('''INSERT OR REPLACE INTO iqbm_learning_paths
                    (path_id, student_id, subject, weak_points, recommended_path, mastery_level)
                    VALUES (?,?,?,?,?,?)''',
                    (path_id, student_id, subject,
                     json.dumps(weak_points, ensure_ascii=False),
                     json.dumps(recommended_path, ensure_ascii=False),
                     mastery))
                conn.commit()
        except Exception as e:
            logger.warning(f"学习路径保存失败: {e}")

        return {'success': True, 'path_id': path_id, 'student_id': student_id,
                'subject': subject, 'weak_points': weak_points,
                'recommended_path': recommended_path, 'mastery_level': mastery,
                'total_knowledge_points': len(kp_stats)}

    def get_path(self, student_id: str, subject: str = None) -> List[Dict]:
        """获取学生最新的学习路径"""
        student_id = _safe_str(student_id, 100)
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        with _get_db() as conn:
            if subject:
                rows = conn.execute('''SELECT * FROM iqbm_learning_paths
                                       WHERE student_id=? AND subject=? ORDER BY updated_at DESC LIMIT 10''',
                                    (student_id, subject)).fetchall()
            else:
                rows = conn.execute('''SELECT * FROM iqbm_learning_paths
                                       WHERE student_id=? ORDER BY updated_at DESC LIMIT 10''',
                                    (student_id,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d['weak_points'] = json.loads(d['weak_points']) if d['weak_points'] else []
            d['recommended_path'] = json.loads(d['recommended_path']) if d['recommended_path'] else []
            result.append(d)
        return result


# ============================================================================
# 5. 题库健康度分析器
# ============================================================================

class BankHealthAnalyzer:
    """题库健康度分析 — 覆盖率/新鲜度/质量/难度分布 + 缺口分析"""

    def __init__(self, knowledge_graph: KnowledgeGraphManager):
        self.kg = knowledge_graph

    def analyze(self, subject: str = None) -> Dict[str, Any]:
        """全面健康度分析"""
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None

        coverage = self.kg.get_coverage(subject)
        quality = self._analyze_quality(subject)
        difficulty = self._analyze_difficulty(subject)
        freshness = self._analyze_freshness(subject)
        gaps = self._analyze_gaps(subject)

        # 综合健康分（0-100）
        health_score = self._calc_health_score(coverage, quality, difficulty, freshness)
        grade = self._grade(health_score)

        return {
            'subject': subject or '全部',
            'health_score': health_score,
            'grade': grade,
            'coverage': coverage,
            'quality': quality,
            'difficulty_distribution': difficulty,
            'freshness': freshness,
            'gaps': gaps,
            'analyzed_at': datetime.now().isoformat(),
        }

    def _analyze_quality(self, subject: str = None) -> Dict[str, Any]:
        """质量分析"""
        try:
            with _get_db() as conn:
                if subject:
                    rows = conn.execute('SELECT quality_score, correct_rate, usage_count FROM ai_authored_questions WHERE subject=?',
                                        (subject,)).fetchall()
                else:
                    rows = conn.execute('SELECT quality_score, correct_rate, usage_count FROM ai_authored_questions').fetchall()
        except sqlite3.OperationalError:
            return {'total': 0, 'avg_quality': 0, 'low_quality_count': 0, 'unused_count': 0}
        total = len(rows)
        if total == 0:
            return {'total': 0, 'avg_quality': 0, 'low_quality_count': 0, 'unused_count': 0}

        avg_quality = sum(r['quality_score'] or 0 for r in rows) / total
        low_quality = sum(1 for r in rows if (r['quality_score'] or 0) < 0.3)
        unused = sum(1 for r in rows if (r['usage_count'] or 0) == 0)

        return {'total': total, 'avg_quality': round(avg_quality, 3),
                'low_quality_count': low_quality,
                'unused_count': unused,
                'low_quality_rate': round(low_quality / total * 100, 1),
                'unused_rate': round(unused / total * 100, 1)}

    def _analyze_difficulty(self, subject: str = None) -> Dict[str, Any]:
        """难度分布分析"""
        try:
            with _get_db() as conn:
                if subject:
                    rows = conn.execute('SELECT difficulty FROM ai_authored_questions WHERE subject=?',
                                        (subject,)).fetchall()
                else:
                    rows = conn.execute('SELECT difficulty FROM ai_authored_questions').fetchall()
        except sqlite3.OperationalError:
            return {'distribution': {}, 'percentage': {}, 'total': 0}
        dist = {}
        for r in rows:
            d = r['difficulty'] or 'medium'
            dist[d] = dist.get(d, 0) + 1
        total = len(rows)
        pct = {k: round(v / total * 100, 1) for k, v in dist.items()} if total > 0 else {}
        return {'distribution': dist, 'percentage': pct, 'total': total}

    def _analyze_freshness(self, subject: str = None) -> Dict[str, Any]:
        """新鲜度分析"""
        now = datetime.now()
        try:
            with _get_db() as conn:
                if subject:
                    rows = conn.execute('SELECT generated_at FROM ai_authored_questions WHERE subject=?',
                                        (subject,)).fetchall()
                else:
                    rows = conn.execute('SELECT generated_at FROM ai_authored_questions').fetchall()
        except sqlite3.OperationalError:
            return {'total': 0, 'fresh_rate': '0%', 'stale_count': 0}
        total = len(rows)
        if total == 0:
            return {'total': 0, 'fresh_rate': '0%', 'stale_count': 0}

        fresh = 0  # 30天内
        stale = 0  # 180天以上
        for r in rows:
            try:
                gen = datetime.fromisoformat((r['generated_at'] or '').replace('Z', ''))
                days = (now - gen).days
                if days <= 30:
                    fresh += 1
                elif days > 180:
                    stale += 1
            except Exception:
                stale += 1

        return {'total': total, 'fresh_count': fresh,
                'fresh_rate': f'{round(fresh / total * 100, 1)}%',
                'stale_count': stale,
                'stale_rate': f'{round(stale / total * 100, 1)}%'}

    def _analyze_gaps(self, subject: str = None) -> Dict[str, Any]:
        """缺口分析"""
        coverage = self.kg.get_coverage(subject)
        try:
            with _get_db() as conn:
                if subject:
                    rows = conn.execute('''SELECT knowledge_point, COUNT(*) as c FROM ai_authored_questions
                                           WHERE subject=? GROUP BY knowledge_point''',
                                        (subject,)).fetchall()
                else:
                    rows = conn.execute('''SELECT knowledge_point, COUNT(*) as c FROM ai_authored_questions
                                           GROUP BY knowledge_point''').fetchall()
        except sqlite3.OperationalError:
            rows = []
        kp_counts = {r['knowledge_point']: r['c'] for r in rows if r['knowledge_point']}
        # 找题目数<5的知识点（缺口）
        gaps = [{'knowledge_point': kp, 'count': c}
                for kp, c in kp_counts.items() if c < 5]
        gaps.sort(key=lambda x: x['count'])
        return {'uncovered_nodes': coverage['uncovered_nodes'],
                'low_coverage_points': gaps[:20],
                'gap_count': len(gaps)}

    def _calc_health_score(self, coverage, quality, difficulty, freshness) -> float:
        """综合健康分（0-100）"""
        # 覆盖率分（30%）
        cov_rate = float(coverage['coverage_rate'].rstrip('%')) if coverage['total_nodes'] > 0 else 0
        cov_score = cov_rate * 0.3

        # 质量分（30%）
        q_score = quality['avg_quality'] * 100 * 0.3

        # 新鲜度分（20%）
        fresh_rate = float(freshness['fresh_rate'].rstrip('%')) if freshness['total'] > 0 else 0
        f_score = fresh_rate * 0.2

        # 难度均衡分（20%）— 越接近标准分布(20/20/30/20/10)越好
        dist = difficulty['percentage']
        if dist:
            target = {'easy': 20, 'medium_easy': 20, 'medium': 30, 'medium_hard': 20, 'hard': 10}
            diff_penalty = sum(abs(dist.get(k, 0) - v) for k, v in target.items())
            d_score = max(0, 20 - diff_penalty * 0.1)
        else:
            d_score = 0

        return round(cov_score + q_score + f_score + d_score, 1)

    def _grade(self, score: float) -> str:
        if score >= 90:
            return 'A+'
        if score >= 80:
            return 'A'
        if score >= 70:
            return 'B'
        if score >= 60:
            return 'C'
        return 'D'


# ============================================================================
# 6. 智能标签推荐器
# ============================================================================

class SmartTagRecommender:
    """智能标签推荐 — 关键词提取 + 相似题目标签"""

    # 常见学科关键词权重
    SUBJECT_KEYWORDS = {
        '数学': ['函数', '导数', '积分', '向量', '概率', '统计', '几何', '代数', '方程', '不等式',
                 '三角', '数列', '极限', '矩阵', '复数'],
        '物理': ['力学', '电学', '光学', '热学', '波动', '电磁', '动量', '能量', '运动', '场',
                 '量子', '相对论', '原子', '分子'],
        '化学': ['反应', '方程式', '元素', '化合物', '有机', '无机', '酸碱', '氧化', '还原',
                 '化学键', '晶体', '溶液'],
        '英语': ['语法', '词汇', '阅读', '写作', '听力', '翻译', '完形', '时态', '语态', '从句'],
        '语文': ['文言文', '现代文', '诗歌', '散文', '小说', '修辞', '字词', '句子', '段落', '作文'],
    }

    def recommend_tags(self, content: str, subject: str = None,
                       existing_tags: List[str] = None) -> Dict[str, Any]:
        """为题目推荐标签"""
        content = _safe_str(content, 5000)
        if not content:
            return {'success': False, 'error': '内容不能为空'}
        subject = _safe_enum(subject, _VALID_SUBJECTS) if subject else None
        if not isinstance(existing_tags, list):
            existing_tags = []

        recommended = set()

        # 1. 学科关键词匹配
        if subject and subject in self.SUBJECT_KEYWORDS:
            for kw in self.SUBJECT_KEYWORDS[subject]:
                if kw in content:
                    recommended.add(kw)

        # 2. 通用关键词提取（高频词）
        keywords = self._extract_keywords(content)
        recommended.update(keywords[:5])

        # 3. 题型推断
        qtype = self._infer_qtype(content)
        if qtype:
            recommended.add(qtype)

        # 4. 难度推断
        difficulty = self._infer_difficulty(content)
        if difficulty:
            recommended.add(difficulty)

        # 5. 基于相似题目的标签
        similar_tags = self._find_similar_tags(content, subject)
        recommended.update(similar_tags[:5])

        # 排除已有标签
        new_tags = [t for t in recommended if t not in existing_tags]

        return {'success': True, 'recommended_tags': list(new_tags)[:15],
                'content_length': len(content)}

    def _extract_keywords(self, text: str) -> List[str]:
        """简单关键词提取（基于词频）"""
        # 移除标点和特殊字符
        cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        words = cleaned.split()
        # 过滤短词
        words = [w for w in words if len(w) >= 2]
        # 统计词频
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        # 按频率排序
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:8]]

    def _infer_qtype(self, content: str) -> Optional[str]:
        """推断题型"""
        if re.search(r'[A-D][.．、]\s*\S', content) or re.search(r'下列.*正确|以下.*不正确', content):
            return 'single_choice'
        if '判断' in content or '对错' in content:
            return 'true_false'
        if '填空' in content or '___' in content or '＿＿＿' in content:
            return 'fill_blank'
        if '计算' in content or '求解' in content or '求证' in content:
            return 'calculation'
        if '简答' in content or '简述' in content:
            return 'short_answer'
        if '论述' in content or '分析' in content and '字' in content:
            return 'essay'
        return None

    def _infer_difficulty(self, content: str) -> Optional[str]:
        """推断难度"""
        if any(w in content for w in ['基础', '简单', '容易', '入门']):
            return 'easy'
        if any(w in content for w in ['综合', '中等', '一般']):
            return 'medium'
        if any(w in content for w in ['困难', '挑战', '提高', '竞赛', '压轴']):
            return 'hard'
        return None

    def _find_similar_tags(self, content: str, subject: str = None) -> List[str]:
        """基于相似题目的标签推荐"""
        # 用内容指纹查找相似题目
        fingerprint = hashlib.md5(content[:200].encode()).hexdigest()[:8]
        try:
            with _get_db() as conn:
                if subject:
                    rows = conn.execute('''SELECT tags FROM ai_authored_questions
                                           WHERE subject=? AND tags IS NOT NULL AND tags != '[]'
                                           ORDER BY usage_count DESC LIMIT 100''',
                                        (subject,)).fetchall()
                else:
                    rows = conn.execute('''SELECT tags FROM ai_authored_questions
                                           WHERE tags IS NOT NULL AND tags != '[]'
                                           ORDER BY usage_count DESC LIMIT 100''').fetchall()
            tag_freq = {}
            for r in rows:
                try:
                    tags = json.loads(r['tags']) if r['tags'] else []
                    if isinstance(tags, list):
                        for t in tags:
                            if isinstance(t, str):
                                tag_freq[t] = tag_freq.get(t, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue
            # 按频率排序
            sorted_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
            return [t for t, _ in sorted_tags[:10]]
        except Exception:
            return []


# ============================================================================
# 主管理器（门面模式）
# ============================================================================

class IntelligentQuestionBankManager:
    """智能化题库管理系统主管理器"""

    VERSION = "v1.0.0"
    _instance = None
    _initialized = False
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self.knowledge_graph = KnowledgeGraphManager()
            self.paper_composer = IntelligentPaperComposer()
            self.lifecycle = QuestionLifecycleManager()
            self.learning_path = AdaptiveLearningPath(self.knowledge_graph)
            self.health_analyzer = BankHealthAnalyzer(self.knowledge_graph)
            self.tag_recommender = SmartTagRecommender()
            self._initialized = True
            logger.info(f"IntelligentQuestionBankManager {self.VERSION} 已初始化")

    def get_status(self) -> Dict[str, Any]:
        """系统状态"""
        return {
            'version': self.VERSION,
            'modules': {
                'knowledge_graph': 'KnowledgeGraphManager',
                'paper_composer': 'IntelligentPaperComposer',
                'lifecycle': 'QuestionLifecycleManager',
                'learning_path': 'AdaptiveLearningPath',
                'health_analyzer': 'BankHealthAnalyzer',
                'tag_recommender': 'SmartTagRecommender',
            },
            'lifecycle_stats': self.lifecycle.get_lifecycle_stats(),
            'initialized_at': datetime.now().isoformat(),
        }


# 单例获取
_manager_instance = None

def get_iqbm_manager() -> IntelligentQuestionBankManager:
    """获取智能化题库管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = IntelligentQuestionBankManager()
    return _manager_instance
