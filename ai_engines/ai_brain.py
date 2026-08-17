# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI脑库数据模型 - 升级版
支持5层认知维度、知识关联图谱、深度评分、跨域推理
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
import logging
import math
import uuid

logger = logging.getLogger(__name__)


# ========== 认知维度定义 ==========
COGNITIVE_LEVELS = {
    "L1": {"name": "基础事实", "description": "事实性知识，知道是什么", "weight": 0.1},
    "L2": {"name": "原理理解", "description": "理解原理，知道为什么", "weight": 0.2},
    "L3": {"name": "应用实践", "description": "实践应用，知道怎么做", "weight": 0.3},
    "L4": {"name": "分析评估", "description": "分析评估，知道好坏优劣", "weight": 0.2},
    "L5": {"name": "创新创造", "description": "创新创造，突破现有边界", "weight": 0.2},
}

# ========== 知识域关联图谱 ==========
DOMAIN_RELATIONS = {
    "架构设计": {"related": ["AI架构", "安全防护", "云计算", "中间件技术"], "strength": 0.9},
    "安全防护": {"related": ["架构设计", "AI架构", "区块链", "量子计算"], "strength": 0.8},
    "Python": {"related": ["机器学习", "数据分析", "AI架构", "前端"], "strength": 0.85},
    "前端": {"related": ["UI/UX设计规范", "Python", "AI架构", "云计算"], "strength": 0.7},
    "教育系统": {"related": ["AI架构", "机器学习", "自然语言处理", "数据分析"], "strength": 0.6},
    "AI运维": {"related": ["AI架构", "云计算", "中间件技术", "数据库技术"], "strength": 0.8},
    "项目经验": {"related": ["架构设计", "AI架构", "云计算", "数据库技术"], "strength": 0.75},
    "AI架构": {"related": ["机器学习", "自然语言处理", "计算机视觉", "边缘计算"], "strength": 0.95},
    "机器学习": {"related": ["自然语言处理", "计算机视觉", "AI架构", "数据分析"], "strength": 0.9},
    "云计算": {"related": ["架构设计", "AI运维", "中间件技术", "物联网"], "strength": 0.85},
    "数据分析": {"related": ["机器学习", "数据库技术", "AI架构", "教育系统"], "strength": 0.8},
    "自然语言处理": {"related": ["机器学习", "AI架构", "计算机视觉", "区块链"], "strength": 0.9},
    "计算机视觉": {"related": ["机器学习", "AI架构", "自然语言处理", "物联网"], "strength": 0.85},
    "物联网": {"related": ["云计算", "计算机视觉", "中间件技术", "量子计算"], "strength": 0.7},
    "区块链": {"related": ["安全防护", "金融科技", "供应链管理", "量子计算"], "strength": 0.75},
    "企业微信": {"related": ["AI架构", "中间件技术", "教育系统", "项目经验"], "strength": 0.8},
    "数据库技术": {"related": ["中间件技术", "云计算", "数据分析", "AI架构"], "strength": 0.85},
    "中间件技术": {"related": ["架构设计", "云计算", "数据库技术", "AI架构"], "strength": 0.9},
    "量子计算": {"related": ["AI架构", "安全防护", "区块链", "计算机视觉"], "strength": 0.7},
    "UI/UX设计规范": {"related": ["前端", "AI架构", "教育系统"], "strength": 0.65},
    "金融科技": {"related": ["区块链", "安全防护", "数据分析", "云计算"], "strength": 0.7},
    "边缘计算": {"related": ["AI架构", "物联网", "云计算", "机器学习"], "strength": 0.75},
}


class AIBrainKnowledge:
    """AI脑库知识模型（升级版，含认知维度）"""

    def __init__(self, knowledge_id=None, title=None, content=None,
                 knowledge_type=None, domain=None, source=None, tags=None, priority=0,
                 is_active=True, review_status="pending", confidence_score=0.0,
                 cognitive_level="L1", cognitive_score=0.5, parent_id=None,
                 knowledge_relations=None):
        self.knowledge_id = knowledge_id or f"kno_{uuid.uuid4().hex[:12]}"
        self.title = title
        self.content = content
        self.knowledge_type = knowledge_type
        self.domain = domain
        self.source = source
        self.tags = tags or []
        self.priority = priority
        self.is_active = is_active
        self.review_status = review_status
        self.confidence_score = confidence_score
        self.cognitive_level = cognitive_level  # L1-L5
        self.cognitive_score = cognitive_score  # 0.0-1.0
        self.parent_id = parent_id
        self.knowledge_relations = knowledge_relations or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.reviewed_at = None
        self.reviewed_by = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'knowledge_id': self.knowledge_id,
            'title': self.title,
            'content': self.content,
            'knowledge_type': self.knowledge_type,
            'domain': self.domain,
            'source': self.source,
            'tags': self.tags,
            'priority': self.priority,
            'is_active': self.is_active,
            'review_status': self.review_status,
            'confidence_score': self.confidence_score,
            'cognitive_level': self.cognitive_level,
            'cognitive_score': self.cognitive_score,
            'parent_id': self.parent_id,
            'knowledge_relations': self.knowledge_relations,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def create_table(cls):
        """创建表"""
        logger.info("创建 AIBrainKnowledge 表")

    @classmethod
    def get_by_status(cls, status):
        """按状态获取"""
        return []


class AIBrainActivity:
    """AI脑库活动模型"""

    @classmethod
    def create_table(cls):
        """创建表"""
        logger.info("创建 AIBrainActivity 表")


class CognitiveGraph:
    """知识关联图谱"""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}  # knowledge_id -> node
        self._edges: List[Tuple[str, str, float]] = []  # (from_id, to_id, weight)
        self._domain_index: Dict[str, Set[str]] = defaultdict(set)  # domain -> set of knowledge_ids

    def add_node(self, knowledge: AIBrainKnowledge):
        """添加知识节点"""
        node_data = knowledge.to_dict()
        self._nodes[knowledge.knowledge_id] = node_data
        if knowledge.domain:
            self._domain_index[knowledge.domain].add(knowledge.knowledge_id)

    def add_edge(self, from_id: str, to_id: str, weight: float = 0.5):
        """添加知识关联"""
        if from_id in self._nodes and to_id in self._nodes:
            self._edges.append((from_id, to_id, weight))
            # 双向关联
            self._edges.append((to_id, from_id, weight))

    def get_related(self, knowledge_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """获取相关知识（按深度）"""
        visited = {knowledge_id}
        current_level = {knowledge_id}
        result = []

        for d in range(depth):
            next_level = set()
            for node_id in current_level:
                for edge in self._edges:
                    if edge[0] == node_id and edge[1] not in visited:
                        next_level.add(edge[1])
                        visited.add(edge[1])
            result.extend([self._nodes[nid] for nid in next_level if nid in self._nodes])
            current_level = next_level

        return result

    def get_domain_knowledge(self, domain: str) -> List[Dict[str, Any]]:
        """获取某领域所有知识"""
        return [self._nodes[kid] for kid in self._domain_index.get(domain, set()) if kid in self._nodes]

    def get_cross_domain_relations(self, domain_a: str, domain_b: str) -> List[Tuple[str, str, float]]:
        """获取跨域知识关联"""
        a_nodes = self._domain_index.get(domain_a, set())
        b_nodes = self._domain_index.get(domain_b, set())
        cross_edges = []
        for edge in self._edges:
            if (edge[0] in a_nodes and edge[1] in b_nodes) or \
               (edge[0] in b_nodes and edge[1] in a_nodes):
                cross_edges.append(edge)
        return cross_edges

    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计"""
        return {
            'total_nodes': len(self._nodes),
            'total_edges': len(self._edges),
            'total_domains': len(self._domain_index),
            'cross_domain_links': len(self._edges),  # 跨域关联数
            'domains': {d: len(kids) for d, kids in self._domain_index.items()},
            'avg_cognitive_score': self._calc_avg_cognitive(),
            'cognitive_distribution': self._calc_cognitive_distribution(),
        }

    def _calc_avg_cognitive(self) -> float:
        """计算平均认知分"""
        if not self._nodes:
            return 0.0
        scores = [n['cognitive_score'] for n in self._nodes.values() if n.get('cognitive_score')]
        return sum(scores) / len(scores) if scores else 0.0

    def _calc_cognitive_distribution(self) -> Dict[str, int]:
        """认知维度分布"""
        dist = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}
        for node in self._nodes.values():
            level = node.get('cognitive_level', 'L1')
            if level in dist:
                dist[level] += 1
        return dist

    def build_auto_relations(self):
        """基于领域关联图谱自动构建知识关联"""
        for domain, info in DOMAIN_RELATIONS.items():
            related_domains = info.get('related', [])
            domain_nodes = self._domain_index.get(domain, set())

            for related_domain in related_domains:
                related_nodes = self._domain_index.get(related_domain, set())
                strength = info.get('strength', 0.5)

                # 每个领域取2条代表节点建立关联
                domain_list = list(domain_nodes)[:2]
                related_list = list(related_nodes)[:2]

                for src in domain_list:
                    for dst in related_list:
                        self.add_edge(src, dst, strength)


class CognitiveEvaluator:
    """认知深度评估器"""

    @staticmethod
    def evaluate_level(knowledge: AIBrainKnowledge, interaction_count: int = 0,
                       feedback_score: float = 0.0, cross_domain_links: int = 0) -> Tuple[str, float]:
        """评估知识的认知维度和深度"""
        content = knowledge.content or ""
        tags = knowledge.tags or []

        # 基础分
        base_score = knowledge.confidence_score or 0.5

        # 根据内容特征判断初始认知级别
        level_scores = {
            "L1": 0.2,  # 基础事实
            "L2": 0.4,  # 原理理解
            "L3": 0.6,  # 应用实践
            "L4": 0.8,  # 分析评估
            "L5": 0.95,  # 创新创造
        }

        # 关键词分析
        l2_keywords = ["原理", "机制", "架构", "模式", "设计", "结构", "原理", "理论"]
        l3_keywords = ["实现", "应用", "实践", "部署", "使用", "开发", "构建", "配置"]
        l4_keywords = ["分析", "评估", "对比", "优化", "对比", "选择", "判断", "评价"]
        l5_keywords = ["创新", "创造", "突破", "融合", "集成", "设计", "新", "独特"]

        text = (knowledge.title or "") + " " + content
        l2_hits = sum(1 for kw in l2_keywords if kw in text)
        l3_hits = sum(1 for kw in l3_keywords if kw in text)
        l4_hits = sum(1 for kw in l4_keywords if kw in text)
        l5_hits = sum(1 for kw in l5_keywords if kw in text)

        # 基于关键词分布确定初始级别
        max_hits = max(l2_hits, l3_hits, l4_hits, l5_hits)
        if max_hits == 0:
            initial_level = "L1"
        elif max_hits == l5_hits and l5_hits > 0:
            initial_level = "L5"
        elif max_hits == l4_hits:
            initial_level = "L4"
        elif max_hits == l3_hits:
            initial_level = "L3"
        else:
            initial_level = "L2"

        # 计算认知分数（基于初始级别+反馈+交互+跨域链接）
        level_base = level_scores[initial_level]
        feedback_boost = feedback_score * 0.15
        interaction_boost = min(interaction_count * 0.02, 0.1)
        cross_domain_boost = min(cross_domain_links * 0.05, 0.2)

        cognitive_score = min(1.0, level_base + feedback_boost + interaction_boost + cross_domain_boost)

        # 根据分数调整级别
        if cognitive_score >= 0.9:
            final_level = "L5"
        elif cognitive_score >= 0.75:
            final_level = "L4"
        elif cognitive_score >= 0.55:
            final_level = "L3"
        elif cognitive_score >= 0.35:
            final_level = "L2"
        else:
            final_level = "L1"

        return final_level, cognitive_score

    @staticmethod
    def promote_knowledge(knowledge: AIBrainKnowledge, current_level: str,
                          interactions: int, feedback: float) -> Dict[str, Any]:
        """提升知识的认知维度"""
        current_weight = COGNITIVE_LEVELS[current_level]["weight"]
        next_level_key = f"L{int(current_level[1]) + 1}"

        if next_level_key not in COGNITIVE_LEVELS:
            return {
                'promoted': False,
                'reason': '已达到最高认知维度',
                'current_level': current_level,
            }

        # 提升条件：交互次数 >= 5 且 反馈 >= 0.7
        promote_threshold = 5 + (0.7 - feedback) * 10

        if interactions >= promote_threshold and feedback >= 0.7:
            return {
                'promoted': True,
                'from_level': current_level,
                'to_level': next_level_key,
                'reason': f'交互{interactions}次，反馈{feedback}，满足提升条件',
            }

        return {
            'promoted': False,
            'reason': f'交互{interactions}次/阈值{promote_threshold:.1f}，反馈{feedback}/阈值0.7',
            'current_level': current_level,
        }


class CrossDomainReasoner:
    """跨域知识推理引擎"""

    def __init__(self, graph: CognitiveGraph):
        self.graph = graph
        self._reasoning_history: List[Dict[str, Any]] = []

    def reason(self, source_domain: str, target_domain: str,
               query: str = "") -> Dict[str, Any]:
        """跨域推理"""
        # 获取两个域的知识
        source_knowledge = self.graph.get_domain_knowledge(source_domain)
        target_knowledge = self.graph.get_domain_knowledge(target_domain)

        if not source_knowledge or not target_knowledge:
            return {
                'success': False,
                'reason': f'知识不足：源域{len(source_knowledge)}条，目标域{len(target_knowledge)}条',
            }

        # 计算跨域关联
        cross_relations = self.graph.get_cross_domain_relations(source_domain, target_domain)

        # 基于领域关联图谱的关联强度
        domain_config = DOMAIN_RELATIONS.get(source_domain, {})
        related_to_target = target_domain in domain_config.get('related', [])
        base_strength = domain_config.get('strength', 0.3) if related_to_target else 0.1

        # 生成推理路径
        reasoning_paths = self._generate_reasoning_paths(
            source_knowledge, target_knowledge, cross_relations, base_strength
        )

        # 计算推理置信度
        confidence = self._calc_reasoning_confidence(
            source_knowledge, target_knowledge, reasoning_paths
        )

        result = {
            'success': True,
            'source_domain': source_domain,
            'target_domain': target_domain,
            'query': query,
            'cross_relations_count': len(cross_relations),
            'reasoning_paths': reasoning_paths[:5],  # 最多5条路径
            'confidence': confidence,
            'insights': self._generate_insights(reasoning_paths, confidence),
            'timestamp': datetime.now().isoformat(),
        }

        self._reasoning_history.append(result)
        return result

    def _generate_reasoning_paths(self, source_know: List[Dict], target_know: List[Dict],
                                   cross_relations: List, base_strength: float) -> List[Dict]:
        """生成推理路径"""
        paths = []

        # 策略1：直接知识关联
        for src in source_know[:3]:
            for tgt in target_know[:3]:
                # 检查标签重叠
                src_tags = set(src.get('tags', []))
                tgt_tags = set(tgt.get('tags', []))
                common_tags = src_tags & tgt_tags

                if common_tags or base_strength > 0.5:
                    path_strength = base_strength + len(common_tags) * 0.1
                    paths.append({
                        'from': src.get('title', 'Unknown'),
                        'to': tgt.get('title', 'Unknown'),
                        'path_type': 'direct_relation',
                        'common_tags': list(common_tags),
                        'strength': min(1.0, path_strength),
                        'description': f"从{src.get('title')}到{tgt.get('title')}的关联推理",
                    })

        # 策略2：基于认知维度的映射
        for src in source_know[:2]:
            for tgt in target_know[:2]:
                src_level = src.get('cognitive_level', 'L1')
                tgt_level = tgt.get('cognitive_level', 'L1')
                level_diff = abs(int(src_level[1]) - int(tgt_level[1]))

                if level_diff <= 2:
                    paths.append({
                        'from': src.get('title', 'Unknown'),
                        'to': tgt.get('title', 'Unknown'),
                        'path_type': 'cognitive_mapping',
                        'src_level': src_level,
                        'tgt_level': tgt_level,
                        'strength': 0.7 - level_diff * 0.1,
                        'description': f"认知维度相近（{src_level}→{tgt_level}）的知识映射",
                    })

        # 按强度排序
        paths.sort(key=lambda x: x['strength'], reverse=True)
        return paths

    def _calc_reasoning_confidence(self, source_know: List[Dict], target_know: List[Dict],
                                    paths: List[Dict]) -> float:
        """计算推理置信度"""
        if not paths:
            return 0.1

        # 基础置信度
        base_confidence = 0.3

        # 路径数量加成
        path_bonus = min(len(paths) * 0.1, 0.3)

        # 平均强度加成
        avg_strength = sum(p['strength'] for p in paths) / len(paths)
        strength_bonus = avg_strength * 0.3

        # 知识量加成
        knowledge_bonus = min((len(source_know) + len(target_know)) * 0.005, 0.2)

        return min(1.0, base_confidence + path_bonus + strength_bonus + knowledge_bonus)

    def _generate_insights(self, paths: List[Dict], confidence: float) -> List[str]:
        """生成推理洞察"""
        insights = []

        if confidence >= 0.7:
            insights.append("跨域推理置信度较高，建议优先参考")
        elif confidence >= 0.4:
            insights.append("跨域推理有一定参考价值，需结合实际情况判断")
        else:
            insights.append("跨域推理置信度较低，建议谨慎参考")

        if paths:
            best_path = paths[0]
            insights.append(f"最强关联路径: {best_path['description']}")

        return insights

    def get_reasoning_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return self._reasoning_history[-limit:]


class AIBrain:
    """AI脑库 — 认知维度 / 知识图谱 / 跨域推理 / 自我修复 / 问题追踪"""

    def __init__(self, db_path=None):
        import os
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), 'app.db')
        self.db_path = db_path

        # 知识存储
        self._knowledge_store: Dict[str, AIBrainKnowledge] = {}
        self._knowledge_by_domain: Dict[str, List[str]] = defaultdict(list)
        self._knowledge_by_level: Dict[str, List[str]] = defaultdict(list)

        # 图谱和推理
        self.cognitive_graph = CognitiveGraph()
        self.cognitive_evaluator = CognitiveEvaluator()
        self.cross_domain_reasoner = CrossDomainReasoner(self.cognitive_graph)

        # 问题追踪
        self._problems = {}
        self._solutions = {}
        self._repair_history = []

        # 学习统计
        self._learning_stats = {
            'total_injected': 0,
            'total_promoted': 0,
            'total_reasoning': 0,
            'cross_domain_links': 0,
            'avg_cognitive_score': 0.0,
            'learning_rounds': 0,
        }

    # ========== 知识管理 ==========
    def add_knowledge(self, knowledge: AIBrainKnowledge) -> str:
        """添加知识到脑库"""
        kid = knowledge.knowledge_id
        self._knowledge_store[kid] = knowledge

        # 确保 domain 和 cognitive_level 有默认值
        domain = knowledge.domain or '未分类'
        level = knowledge.cognitive_level or 'L1'

        self._knowledge_by_domain[domain].append(kid)
        self._knowledge_by_level[level].append(kid)

        # 添加到图谱
        self.cognitive_graph.add_node(knowledge)

        self._learning_stats['total_injected'] += 1
        return kid

    def batch_add_knowledge(self, knowledge_list: List[AIBrainKnowledge]) -> int:
        """批量添加知识"""
        added_count = 0
        for k in knowledge_list:
            self.add_knowledge(k)
            added_count += 1
        return added_count

    def get_knowledge(self, knowledge_id: str) -> Optional[AIBrainKnowledge]:
        """获取知识"""
        return self._knowledge_store.get(knowledge_id)

    def get_domain_knowledge(self, domain: str) -> List[AIBrainKnowledge]:
        """获取领域知识"""
        kids = self._knowledge_by_domain.get(domain, [])
        return [self._knowledge_store[kid] for kid in kids if kid in self._knowledge_store]

    def get_all_domains(self) -> List[str]:
        """获取所有知识域"""
        return list(self._knowledge_by_domain.keys())

    def get_knowledge_by_level(self, level: str) -> List[AIBrainKnowledge]:
        """按认知维度获取知识"""
        kids = self._knowledge_by_level.get(level, [])
        return [self._knowledge_store[kid] for kid in kids if kid in self._knowledge_store]

    def search_knowledge(self, query: str, top_k: int = 5) -> List[AIBrainKnowledge]:
        """搜索知识（基于关键词匹配）"""
        results = []
        query_lower = query.lower()

        for kid, k in self._knowledge_store.items():
            text = ((k.title or "") + " " + (k.content or "") + " " + " ".join(k.tags)).lower()
            score = 0.0
            for word in query_lower.split():
                if word in text:
                    score += 1.0
            if score > 0:
                results.append((k, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_k]]

    # ========== 认知评估与提升 ==========
    def evaluate_knowledge_cognition(self, knowledge_id: str,
                                      interactions: int = 0,
                                      feedback: float = 0.0,
                                      cross_links: int = 0) -> Dict[str, Any]:
        """评估知识认知维度"""
        k = self._knowledge_store.get(knowledge_id)
        if not k:
            return {'success': False, 'error': '知识不存在'}

        new_level, new_score = self.cognitive_evaluator.evaluate_level(
            k, interactions, feedback, cross_links
        )

        # 更新知识
        old_level = k.cognitive_level
        k.cognitive_level = new_level
        k.cognitive_score = new_score
        k.updated_at = datetime.now().isoformat()

        # 同步更新图谱节点
        if knowledge_id in self.cognitive_graph._nodes:
            self.cognitive_graph._nodes[knowledge_id]['cognitive_level'] = new_level
            self.cognitive_graph._nodes[knowledge_id]['cognitive_score'] = new_score
            self.cognitive_graph._nodes[knowledge_id]['updated_at'] = k.updated_at

        # 重新索引
        if old_level != new_level:
            if old_level in self._knowledge_by_level:
                self._knowledge_by_level[old_level].remove(knowledge_id)
            self._knowledge_by_level[new_level].append(knowledge_id)
            self._learning_stats['total_promoted'] += 1

        return {
            'success': True,
            'knowledge_id': knowledge_id,
            'old_level': old_level,
            'new_level': new_level,
            'cognitive_score': new_score,
            'promoted': old_level != new_level,
        }

    def promote_knowledge(self, knowledge_id: str, interactions: int,
                          feedback: float) -> Dict[str, Any]:
        """尝试提升知识认知维度"""
        k = self._knowledge_store.get(knowledge_id)
        if not k:
            return {'success': False, 'error': '知识不存在'}

        result = self.cognitive_evaluator.promote_knowledge(
            k, k.cognitive_level, interactions, feedback
        )

        if result['promoted']:
            new_level = result['to_level']
            old_level = result['from_level']
            k.cognitive_level = new_level
            k.cognitive_score = max(k.cognitive_score, COGNITIVE_LEVELS[new_level]['weight'] + 0.3)
            k.updated_at = datetime.now().isoformat()

            # 同步更新图谱节点
            if knowledge_id in self.cognitive_graph._nodes:
                self.cognitive_graph._nodes[knowledge_id]['cognitive_level'] = new_level
                self.cognitive_graph._nodes[knowledge_id]['cognitive_score'] = k.cognitive_score
                self.cognitive_graph._nodes[knowledge_id]['updated_at'] = k.updated_at

            if old_level in self._knowledge_by_level:
                self._knowledge_by_level[old_level].remove(knowledge_id)
            self._knowledge_by_level[new_level].append(knowledge_id)
            self._learning_stats['total_promoted'] += 1

        return result

    # ========== 跨域推理 ==========
    def cross_domain_reason(self, source_domain: str, target_domain: str,
                            query: str = "") -> Dict[str, Any]:
        """执行跨域推理"""
        result = self.cross_domain_reasoner.reason(source_domain, target_domain, query)
        self._learning_stats['total_reasoning'] += 1
        return result

    def auto_build_domain_relations(self):
        """自动构建领域知识关联"""
        self.cognitive_graph.build_auto_relations()
        edge_count = len(self.cognitive_graph._edges)
        self._learning_stats['cross_domain_links'] = edge_count
        return edge_count

    # ========== 知识拓展 ==========
    def expand_knowledge(self, topic: str, depth: int = 3) -> List[Dict[str, Any]]:
        """基于真实知识池拓展知识"""
        expanded = []

        # 从现有知识中找相关
        for kid, k in self._knowledge_store.items():
            if topic.lower() in (k.title or "").lower() or topic.lower() in (k.content or "").lower():
                # 获取关联知识
                related = self.cognitive_graph.get_related(kid, depth=min(depth, 2))
                for r in related:
                    expanded.append({
                        'topic': r.get('title', ''),
                        'sub_topic': f"{topic}_{r.get('domain', '')}_{r.get('knowledge_id', '')[:8]}",
                        'confidence': r.get('cognitive_score', 0.5),
                        'source': 'graph_expand',
                        'domain': r.get('domain', ''),
                        'cognitive_level': r.get('cognitive_level', 'L1'),
                    })

        # 基于领域关联图谱生成拓展建议
        for domain, info in DOMAIN_RELATIONS.items():
            if topic in domain or any(kw in topic for kw in domain.split('/')):
                for related_domain in info.get('related', []):
                    domain_knowledge = self.get_domain_knowledge(related_domain)
                    for k in domain_knowledge[:depth]:
                        expanded.append({
                            'topic': k.title,
                            'sub_topic': f"{topic}_{related_domain}_{k.knowledge_id[:8]}",
                            'confidence': k.cognitive_score * info.get('strength', 0.5),
                            'source': 'domain_relation',
                            'domain': related_domain,
                            'cognitive_level': k.cognitive_level,
                        })

        # 如果没有找到相关，返回基于认知提升的建议
        if not expanded:
            for level_name, level_info in COGNITIVE_LEVELS.items():
                expanded.append({
                    'topic': topic,
                    'sub_topic': f"{topic}_{level_info['name']}",
                    'confidence': level_info['weight'],
                    'source': 'cognitive_expand',
                    'cognitive_level': level_name,
                    'description': level_info['description'],
                })

        return expanded[:depth * 3]

    # ========== 问题追踪与自我修复 ==========
    def add_problem(self, problem_id=None, description='', category='general',
                    severity='medium', context=None):
        if problem_id is None:
            problem_id = f"prob_{uuid.uuid4().hex[:12]}"
        self._problems[problem_id] = {
            'problem_id': problem_id, 'description': description,
            'category': category, 'severity': severity,
            'context': context or {}, 'status': 'open',
            'created_at': datetime.now().isoformat(),
        }
        return self._problems[problem_id]

    def get_problem(self, problem_id):
        return self._problems.get(problem_id)

    def add_solution(self, solution_id=None, problem_id=None,
                     solution='', confidence=0.5, auto_generated=True):
        if solution_id is None:
            solution_id = f"sol_{uuid.uuid4().hex[:12]}"
        self._solutions[solution_id] = {
            'solution_id': solution_id, 'problem_id': problem_id,
            'solution': solution, 'confidence': confidence,
            'auto_generated': auto_generated,
            'created_at': datetime.now().isoformat(),
        }
        return self._solutions[solution_id]

    def get_solution(self, solution_id):
        return self._solutions.get(solution_id)

    def auto_repair(self, problem_id, solution_id=None):
        problem = self._problems.get(problem_id)
        if not problem:
            return {'success': False, 'message': f'问题 {problem_id} 不存在'}
        solution = self._solutions.get(solution_id) if solution_id else None
        self._repair_history.append({
            'problem_id': problem_id,
            'solution_id': solution_id,
            'result': 'repaired',
            'timestamp': datetime.now().isoformat(),
        })
        problem['status'] = 'resolved'
        return {'success': True, 'problem_id': problem_id, 'repaired': True}

    def get_repair_history(self, limit=100):
        return list(reversed(self._repair_history[-limit:]))

    # ========== 统计与报告 ==========
    def get_stats(self) -> Dict[str, Any]:
        """获取脑库统计"""
        graph_stats = self.cognitive_graph.get_graph_stats()

        # 计算总体认知分
        knowledge_scores = [k.cognitive_score for k in self._knowledge_store.values()]
        avg_score = sum(knowledge_scores) / len(knowledge_scores) if knowledge_scores else 0.0

        # 认知分布
        level_dist = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}
        for k in self._knowledge_store.values():
            if k.cognitive_level in level_dist:
                level_dist[k.cognitive_level] += 1

        return {
            # 基础统计
            'total_problems': len(self._problems),
            'open_problems': sum(1 for p in self._problems.values() if p.get('status') == 'open'),
            'total_solutions': len(self._solutions),
            'total_repairs': len(self._repair_history),
            # 知识统计
            'total_knowledge': len(self._knowledge_store),
            'total_domains': len(self._knowledge_by_domain),
            'domains': list(self._knowledge_by_domain.keys()),
            # 认知统计
            'avg_cognitive_score': avg_score,
            'cognitive_distribution': level_dist,
            # 图谱统计
            'graph_stats': graph_stats,
            # 学习统计
            'learning_stats': self._learning_stats,
        }

    def get_cognitive_report(self) -> Dict[str, Any]:
        """生成认知报告"""
        stats = self.get_stats()

        # 计算认知成熟度
        level_weights = {"L1": 0.1, "L2": 0.2, "L3": 0.3, "L4": 0.2, "L5": 0.2}
        weighted_score = 0.0
        total_knowledge = stats['total_knowledge']

        for level, count in stats['cognitive_distribution'].items():
            weight = level_weights.get(level, 0.1)
            ratio = count / total_knowledge if total_knowledge > 0 else 0
            weighted_score += weight * ratio

        # 认知等级评估
        if weighted_score >= 0.7:
            maturity_level = "高度成熟"
        elif weighted_score >= 0.5:
            maturity_level = "中等成熟"
        elif weighted_score >= 0.3:
            maturity_level = "基础成熟"
        else:
            maturity_level = "初始阶段"

        return {
            'report_time': datetime.now().isoformat(),
            'maturity_level': maturity_level,
            'cognitive_maturity_score': round(weighted_score, 3),
            'knowledge_stats': {
                'total': total_knowledge,
                'domains': stats['total_domains'],
                'avg_score': round(stats['avg_cognitive_score'], 3),
            },
            'cognitive_distribution': stats['cognitive_distribution'],
            'learning_efficiency': {
                'promotion_rate': round(
                    self._learning_stats['total_promoted'] / max(1, self._learning_stats['total_injected']),
                    3
                ),
                'reasoning_count': self._learning_stats['total_reasoning'],
                'cross_domain_links': self._learning_stats['cross_domain_links'],
            },
            'recommendations': self._generate_recommendations(stats),
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成提升建议"""
        recommendations = []

        # 检查认知维度分布
        dist = stats['cognitive_distribution']
        total = stats['total_knowledge']

        if total > 0:
            l1_ratio = dist['L1'] / total
            l4_l5_ratio = (dist['L4'] + dist['L5']) / total

            if l1_ratio > 0.5:
                recommendations.append("基础事实(L1)占比过高，建议加强知识的深度理解和实践应用")
            if l4_l5_ratio < 0.2:
                recommendations.append("高阶认知(L4/L5)占比偏低，建议通过推理和创新任务提升知识维度")

        # 检查跨域关联
        if stats['graph_stats']['cross_domain_links'] < 10:
            recommendations.append("跨域知识关联较少，建议执行跨域推理以增强知识图谱连接")

        # 检查领域覆盖
        if stats['total_domains'] < 10:
            recommendations.append("知识域覆盖不足，建议扩展更多技术领域和业务领域的知识")

        return recommendations


_brain_instance = None


def get_ai_brain():
    """获取全局 AI 脑库单例"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AIBrain()
    return _brain_instance
