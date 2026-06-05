"""
增强知识图谱系统 v4.0.0
支持多模态知识表示、语义搜索、推理和知识演化
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """知识类型"""
    TEXT = "text"                    # 文本知识
    IMAGE = "image"                  # 图像知识
    AUDIO = "audio"                  # 音频知识
    VIDEO = "video"                  # 视频知识
    STRUCTURED = "structured"        # 结构化数据
    CODE = "code"                    # 代码知识
    CONCEPT = "concept"              # 概念知识
    RELATION = "relation"            # 关系知识


class EntityType(Enum):
    """实体类型"""
    CONCEPT = "concept"              # 概念
    PERSON = "person"                # 人物
    ORGANIZATION = "organization"    # 组织
    LOCATION = "location"            # 地点
    EVENT = "event"                  # 事件
    OBJECT = "object"                # 物体
    TOPIC = "topic"                  # 主题
    SKILL = "skill"                  # 技能
    QUESTION = "question"            # 问题
    ANSWER = "answer"                # 答案
    LEARNING_PATH = "learning_path"  # 学习路径


class RelationType(Enum):
    """关系类型"""
    IS_A = "is_a"                    # 是一种
    PART_OF = "part_of"              # 属于
    RELATED_TO = "related_to"        # 相关
    REQUIRES = "requires"            # 需要
    TEACHES = "teaches"              # 教授
    LEADS_TO = "leads_to"            # 导致
    SIMILAR_TO = "similar_to"        # 相似
    CONTRASTS_WITH = "contrasts_with"  # 对比
    EXAMPLE_OF = "example_of"        # 是...的例子
    DEFINED_BY = "defined_by"        # 由...定义


@dataclass
class KnowledgeNode:
    """知识节点"""
    id: str
    entity_type: EntityType
    name: str
    description: str
    knowledge_type: KnowledgeType
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    confidence: float = 1.0
    popularity: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'description': self.description,
            'knowledge_type': self.knowledge_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'confidence': self.confidence,
            'popularity': self.popularity,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': list(self.tags)
        }


@dataclass
class KnowledgeEdge:
    """知识边（关系）"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'weight': self.weight,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class SearchResult:
    """搜索结果"""
    node: KnowledgeNode
    score: float
    matched_relations: List[KnowledgeEdge] = field(default_factory=list)
    explanation: str = ""


class EnhancedKnowledgeGraph:
    """增强知识图谱"""
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.outgoing_edges: Dict[str, List[KnowledgeEdge]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[KnowledgeEdge]] = defaultdict(list)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self.name_index: Dict[str, Set[str]] = defaultdict(set)
        self.lock = threading.RLock()
        
        logger.info("增强知识图谱初始化完成")
    
    def generate_node_id(self, name: str, entity_type: EntityType) -> str:
        """生成节点ID"""
        key = f"{entity_type.value}:{name}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def generate_edge_id(self, source_id: str, target_id: str, relation_type: RelationType) -> str:
        """生成边ID"""
        key = f"{source_id}:{target_id}:{relation_type.value}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def add_node(self, 
                 name: str, 
                 entity_type: EntityType,
                 description: str = "",
                 knowledge_type: KnowledgeType = KnowledgeType.CONCEPT,
                 content: Any = None,
                 metadata: Dict[str, Any] = None,
                 tags: List[str] = None,
                 confidence: float = 1.0) -> KnowledgeNode:
        """
        添加知识节点
        
        Args:
            name: 节点名称
            entity_type: 实体类型
            description: 描述
            knowledge_type: 知识类型
            content: 内容（多模态）
            metadata: 元数据
            tags: 标签
            confidence: 置信度
            
        Returns:
            KnowledgeNode
        """
        with self.lock:
            node_id = self.generate_node_id(name, entity_type)
            
            if node_id in self.nodes:
                # 更新现有节点
                node = self.nodes[node_id]
                node.description = description or node.description
                node.content = content if content is not None else node.content
                node.metadata.update(metadata or {})
                node.tags.update(tags or [])
                node.updated_at = datetime.now()
                node.confidence = max(node.confidence, confidence)
                logger.info(f"更新知识节点: {name}")
            else:
                # 创建新节点
                node = KnowledgeNode(
                    id=node_id,
                    entity_type=entity_type,
                    name=name,
                    description=description,
                    knowledge_type=knowledge_type,
                    content=content,
                    metadata=metadata or {},
                    tags=set(tags or []),
                    confidence=confidence
                )
                self.nodes[node_id] = node
                logger.info(f"添加知识节点: {name}")
            
            # 更新索引
            self.type_index[entity_type].add(node_id)
            self.name_index[name.lower()].add(node_id)
            for tag in node.tags:
                self.tag_index[tag.lower()].add(node_id)
            
            return node
    
    def add_edge(self,
                 source_name: str,
                 source_type: EntityType,
                 target_name: str,
                 target_type: EntityType,
                 relation_type: RelationType,
                 weight: float = 1.0,
                 metadata: Dict[str, Any] = None) -> Optional[KnowledgeEdge]:
        """
        添加知识边（关系）
        
        Args:
            source_name: 源节点名称
            source_type: 源节点类型
            target_name: 目标节点名称
            target_type: 目标节点类型
            relation_type: 关系类型
            weight: 权重
            metadata: 元数据
            
        Returns:
            KnowledgeEdge 或 None
        """
        with self.lock:
            source_id = self.generate_node_id(source_name, source_type)
            target_id = self.generate_node_id(target_name, target_type)
            
            if source_id not in self.nodes:
                logger.warning(f"源节点不存在: {source_name}")
                return None
            if target_id not in self.nodes:
                logger.warning(f"目标节点不存在: {target_name}")
                return None
            
            edge_id = self.generate_edge_id(source_id, target_id, relation_type)
            
            if edge_id in self.edges:
                # 更新现有边
                edge = self.edges[edge_id]
                edge.weight = max(edge.weight, weight)
                edge.metadata.update(metadata or {})
            else:
                # 创建新边
                edge = KnowledgeEdge(
                    id=edge_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    weight=weight,
                    metadata=metadata or {}
                )
                self.edges[edge_id] = edge
                self.outgoing_edges[source_id].append(edge)
                self.incoming_edges[target_id].append(edge)
            
            logger.info(f"添加关系: {source_name} {relation_type.value} {target_name}")
            return edge
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_node_by_name(self, name: str, entity_type: EntityType = None) -> Optional[KnowledgeNode]:
        """通过名称获取节点"""
        with self.lock:
            name_lower = name.lower()
            if name_lower in self.name_index:
                node_ids = self.name_index[name_lower]
                for node_id in node_ids:
                    node = self.nodes[node_id]
                    if entity_type is None or node.entity_type == entity_type:
                        return node
        return None
    
    def get_related_nodes(self, 
                          node_id: str, 
                          relation_types: List[RelationType] = None,
                          max_depth: int = 1,
                          limit: int = 50) -> List[Tuple[KnowledgeNode, KnowledgeEdge, int]]:
        """
        获取相关节点
        
        Args:
            node_id: 起始节点ID
            relation_types: 关系类型过滤
            max_depth: 最大深度
            limit: 结果限制
            
        Returns:
            列表的 (节点, 边, 深度)
        """
        with self.lock:
            if node_id not in self.nodes:
                return []
            
            results = []
            visited = set()
            queue = [(node_id, 0)]
            
            while queue and len(results) < limit:
                current_id, depth = queue.pop(0)
                
                if current_id in visited or depth > max_depth:
                    continue
                visited.add(current_id)
                
                if depth > 0:
                    # 找到连接到current_id的边
                    for edge in self.incoming_edges[current_id]:
                        if edge.source_id in visited:
                            if relation_types is None or edge.relation_type in relation_types:
                                node = self.nodes[current_id]
                                results.append((node, edge, depth))
                
                # 添加下一层
                if depth < max_depth:
                    for edge in self.outgoing_edges[current_id]:
                        if relation_types is None or edge.relation_type in relation_types:
                            queue.append((edge.target_id, depth + 1))
            
            return results[:limit]
    
    def search(self, 
               query: str, 
               entity_types: List[EntityType] = None,
               tags: List[str] = None,
               limit: int = 20) -> List[SearchResult]:
        """
        搜索知识图谱
        
        Args:
            query: 搜索查询
            entity_types: 实体类型过滤
            tags: 标签过滤
            limit: 结果限制
            
        Returns:
            SearchResult列表
        """
        with self.lock:
            results = []
            query_lower = query.lower()
            query_terms = set(query_lower.split())
            
            # 候选节点集合
            candidate_ids = set()
            
            # 1. 名称匹配
            for name, node_ids in self.name_index.items():
                if query_lower in name or any(term in name for term in query_terms):
                    candidate_ids.update(node_ids)
            
            # 2. 标签匹配
            if tags:
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in self.tag_index:
                        candidate_ids.update(self.tag_index[tag_lower])
            
            # 3. 如果没有候选，使用类型索引或全部节点
            if not candidate_ids:
                if entity_types:
                    for et in entity_types:
                        candidate_ids.update(self.type_index.get(et, set()))
                else:
                    candidate_ids.update(self.nodes.keys())
            
            # 评分和排序
            for node_id in candidate_ids:
                node = self.nodes[node_id]
                
                # 类型过滤
                if entity_types and node.entity_type not in entity_types:
                    continue
                
                # 标签过滤
                if tags and not any(tag.lower() in node.tags for tag in tags):
                    continue
                
                # 计算分数
                score = self._calculate_search_score(node, query_lower, query_terms)
                
                if score > 0:
                    # 获取相关关系
                    matched_relations = []
                    for edge in self.outgoing_edges[node_id][:5]:
                        matched_relations.append(edge)
                    for edge in self.incoming_edges[node_id][:5]:
                        matched_relations.append(edge)
                    
                    results.append(SearchResult(
                        node=node,
                        score=score,
                        matched_relations=matched_relations,
                        explanation=self._generate_explanation(node, query)
                    ))
            
            # 排序
            results.sort(key=lambda r: (-r.score, -r.node.popularity))
            return results[:limit]
    
    def _calculate_search_score(self, node: KnowledgeNode, query_lower: str, query_terms: Set[str]) -> float:
        """计算搜索分数"""
        score = 0.0
        name_lower = node.name.lower()
        desc_lower = node.description.lower()
        
        # 完全匹配
        if query_lower == name_lower:
            score += 10.0
        elif query_lower in name_lower:
            score += 5.0
        
        # 部分匹配
        matched_terms = sum(1 for term in query_terms if term in name_lower)
        score += matched_terms * 2.0
        
        matched_terms = sum(1 for term in query_terms if term in desc_lower)
        score += matched_terms * 0.5
        
        # 标签匹配
        tag_matches = sum(1 for term in query_terms if term in (t.lower() for t in node.tags))
        score += tag_matches * 1.5
        
        # 流行度和置信度
        score += node.popularity * 0.1
        score += node.confidence * 0.5
        
        return score
    
    def _generate_explanation(self, node: KnowledgeNode, query: str) -> str:
        """生成搜索解释"""
        parts = []
        if query.lower() in node.name.lower():
            parts.append("名称匹配")
        if any(tag.lower() in query.lower() for tag in node.tags):
            parts.append("标签匹配")
        if query.lower() in node.description.lower():
            parts.append("描述匹配")
        
        if not parts:
            parts.append("相关知识")
        
        return ", ".join(parts)
    
    def infer(self, start_node_id: str, rule_chain: List[RelationType]) -> List[KnowledgeNode]:
        """
        基于规则链推理
        
        Args:
            start_node_id: 起始节点
            rule_chain: 关系链
            
        Returns:
            推理得到的节点列表
        """
        with self.lock:
            if start_node_id not in self.nodes:
                return []
            
            current_nodes = {start_node_id}
            
            for relation_type in rule_chain:
                next_nodes = set()
                for node_id in current_nodes:
                    for edge in self.outgoing_edges[node_id]:
                        if edge.relation_type == relation_type:
                            next_nodes.add(edge.target_id)
                current_nodes = next_nodes
                if not current_nodes:
                    break
            
            return [self.nodes[nid] for nid in current_nodes]
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[KnowledgeEdge]]:
        """
        寻找节点间的路径
        
        Args:
            source_id: 源节点
            target_id: 目标节点
            max_depth: 最大深度
            
        Returns:
            路径列表（每条路径是边的列表）
        """
        with self.lock:
            if source_id not in self.nodes or target_id not in self.nodes:
                return []
            
            # BFS寻找最短路径
            queue = [(source_id, [])]
            visited = set()
            paths = []
            
            while queue:
                current_id, path = queue.pop(0)
                
                if current_id == target_id:
                    paths.append(path)
                    continue
                
                if len(path) >= max_depth or current_id in visited:
                    continue
                visited.add(current_id)
                
                for edge in self.outgoing_edges[current_id]:
                    queue.append((edge.target_id, path + [edge]))
            
            return paths
    
    def update_popularity(self, node_id: str, increment: float = 1.0):
        """更新节点流行度"""
        with self.lock:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.popularity += increment
                node.updated_at = datetime.now()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        with self.lock:
            type_counts = {et.value: len(ids) for et, ids in self.type_index.items()}
            relation_counts = defaultdict(int)
            for edge in self.edges.values():
                relation_counts[edge.relation_type.value] += 1
            
            return {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'node_types': type_counts,
                'relation_types': dict(relation_counts),
                'total_tags': len(self.tag_index),
                'top_nodes': sorted(
                    self.nodes.values(), 
                    key=lambda n: -n.popularity
                )[:10]
            }
    
    def export_to_json(self, filepath: str):
        """导出到JSON"""
        with self.lock:
            data = {
                'nodes': [node.to_dict() for node in self.nodes.values()],
                'edges': [edge.to_dict() for edge in self.edges.values()],
                'exported_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识图谱已导出: {filepath}")
    
    def import_from_json(self, filepath: str):
        """从JSON导入"""
        with self.lock:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 导入节点
            for node_data in data.get('nodes', []):
                node = KnowledgeNode(
                    id=node_data['id'],
                    entity_type=EntityType(node_data['entity_type']),
                    name=node_data['name'],
                    description=node_data['description'],
                    knowledge_type=KnowledgeType(node_data['knowledge_type']),
                    content=node_data.get('content'),
                    metadata=node_data.get('metadata', {}),
                    confidence=node_data.get('confidence', 1.0),
                    popularity=node_data.get('popularity', 0.0),
                    created_at=datetime.fromisoformat(node_data['created_at']),
                    updated_at=datetime.fromisoformat(node_data['updated_at']),
                    tags=set(node_data.get('tags', []))
                )
                self.nodes[node.id] = node
                self.type_index[node.entity_type].add(node.id)
                self.name_index[node.name.lower()].add(node.id)
                for tag in node.tags:
                    self.tag_index[tag.lower()].add(node.id)
            
            # 导入边
            for edge_data in data.get('edges', []):
                edge = KnowledgeEdge(
                    id=edge_data['id'],
                    source_id=edge_data['source_id'],
                    target_id=edge_data['target_id'],
                    relation_type=RelationType(edge_data['relation_type']),
                    weight=edge_data.get('weight', 1.0),
                    metadata=edge_data.get('metadata', {}),
                    created_at=datetime.fromisoformat(edge_data['created_at'])
                )
                self.edges[edge.id] = edge
                self.outgoing_edges[edge.source_id].append(edge)
                self.incoming_edges[edge.target_id].append(edge)
            
            logger.info(f"知识图谱已导入: {filepath}")


# 全局单例
_knowledge_graph: Optional[EnhancedKnowledgeGraph] = None


def get_knowledge_graph() -> EnhancedKnowledgeGraph:
    """获取知识图谱单例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = EnhancedKnowledgeGraph()
    return _knowledge_graph


def initialize_learning_knowledge():
    """初始化学习相关知识"""
    kg = get_knowledge_graph()
    
    # 添加数学相关知识
    math_concepts = [
        ("代数", EntityType.CONCEPT, "数学的一个分支，研究符号和运算规则", ["数学", "基础"]),
        ("几何", EntityType.CONCEPT, "研究形状、大小、位置和空间性质", ["数学", "基础"]),
        ("微积分", EntityType.CONCEPT, "研究变化率和累积量", ["数学", "高等"]),
        ("方程", EntityType.CONCEPT, "表示两个表达式相等的数学陈述", ["数学", "代数", "基础"]),
        ("函数", EntityType.CONCEPT, "输入与输出的映射关系", ["数学", "代数", "核心"]),
    ]
    
    for name, et, desc, tags in math_concepts:
        kg.add_node(name, et, desc, KnowledgeType.CONCEPT, tags=tags)
    
    # 添加关系
    relations = [
        ("代数", EntityType.CONCEPT, "方程", EntityType.CONCEPT, RelationType.PART_OF, 1.0),
        ("代数", EntityType.CONCEPT, "函数", EntityType.CONCEPT, RelationType.PART_OF, 1.0),
        ("微积分", EntityType.CONCEPT, "函数", EntityType.CONCEPT, RelationType.REQUIRES, 0.9),
    ]
    
    for s_name, s_type, t_name, t_type, rel, weight in relations:
        kg.add_edge(s_name, s_type, t_name, t_type, rel, weight)
    
    logger.info("学习知识库初始化完成")
