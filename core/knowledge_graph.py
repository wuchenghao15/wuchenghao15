# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge Graph - 专业知识图谱系统
支持实体关系管理和智能推理
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
from datetime import datetime
import json
import hashlib

class Entity:
    """实体"""
    
    def __init__(self, entity_id: str, entity_type: str, name: str, properties: Dict[str, Any] = None):
        self.id = entity_id
        self.type = entity_type
        self.name = name
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def update_property(self, key: str, value: Any):
        self.properties[key] = value
        self.updated_at = datetime.now()


class Relation:
    """关系"""
    
    def __init__(self, relation_id: str, source_id: str, target_id: str, 
                 relation_type: str, properties: Dict[str, Any] = None):
        self.id = relation_id
        self.source = source_id
        self.target = target_id
        self.type = relation_type
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.weight = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.entity_index: Dict[str, List[str]] = defaultdict(list)
        self.type_index: Dict[str, Set[str]] = defaultdict(set)
        self.adjacency_list: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    
    def add_entity(self, entity_type: str, name: str, properties: Dict[str, Any] = None) -> str:
        """添加实体"""
        entity_id = self._generate_entity_id(name, entity_type)
        
        if entity_id in self.entities:
            return entity_id
        
        entity = Entity(entity_id, entity_type, name, properties)
        self.entities[entity_id] = entity
        
        self.entity_index[name].append(entity_id)
        self.type_index[entity_type].add(entity_id)
        
        return entity_id
    
    def add_relation(self, source_id: str, target_id: str, 
                    relation_type: str, properties: Dict[str, Any] = None, weight: float = 1.0) -> Optional[str]:
        """添加关系"""
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        relation_id = self._generate_relation_id(source_id, target_id, relation_type)
        
        if relation_id in self.relations:
            return relation_id
        
        relation = Relation(relation_id, source_id, target_id, relation_type, properties)
        relation.weight = weight
        self.relations[relation_id] = relation
        
        self.adjacency_list[source_id].append((target_id, relation_type))
        
        return relation_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """按类型获取实体"""
        entity_ids = self.type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]
    
    def get_related_entities(self, entity_id: str, depth: int = 1) -> Dict[str, List[str]]:
        """获取关联实体"""
        result = {}
        visited = set()
        queue = deque([(entity_id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            if current_depth > 0:
                if current_depth not in result:
                    result[current_depth] = []
                result[current_depth].append(current_id)
            
            if current_depth < depth:
                for neighbor_id, _ in self.adjacency_list.get(current_id, []):
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, current_depth + 1))
        
        return result
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[List[str]]:
        """查找路径"""
        if source_id == target_id:
            return [[source_id]]
        
        paths = []
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            for neighbor_id, _ in self.adjacency_list.get(current_id, []):
                if neighbor_id == target_id:
                    paths.append(path + [neighbor_id])
                elif neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return paths
    
    def search(self, query: str, search_type: Optional[str] = None) -> List[Entity]:
        """搜索实体"""
        results = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            if search_type and entity.type != search_type:
                continue
            
            if query_lower in entity.name.lower():
                results.append(entity)
            elif any(query_lower in str(v).lower() for v in entity.properties.values()):
                results.append(entity)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": {etype: len(eids) for etype, eids in self.type_index.items()},
            "relation_types": self._count_relation_types(),
            "average_degree": self._calculate_average_degree()
        }
    
    def _count_relation_types(self) -> Dict[str, int]:
        """统计关系类型"""
        counts = defaultdict(int)
        for relation in self.relations.values():
            counts[relation.type] += 1
        return dict(counts)
    
    def _calculate_average_degree(self) -> float:
        """计算平均度数"""
        if not self.adjacency_list:
            return 0.0
        total_degree = sum(len(neighbors) for neighbors in self.adjacency_list.values())
        return total_degree / len(self.adjacency_list)
    
    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """生成实体ID"""
        content = f"{entity_type}:{name}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_relation_id(self, source_id: str, target_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{source_id}:{target_id}:{relation_type}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "name": self.name,
            "entities": {eid: entity.to_dict() for eid, entity in self.entities.items()},
            "relations": {rid: rel.to_dict() for rid, rel in self.relations.items()}
        }
    
    def import_from_dict(self, data: Dict[str, Any]):
        """从字典导入"""
        self.name = data.get("name", self.name)
        
        for entity_id, entity_data in data.get("entities", {}).items():
            entity = Entity(
                entity_data["id"],
                entity_data["type"],
                entity_data["name"],
                entity_data.get("properties", {})
            )
            self.entities[entity_id] = entity
        
        for relation_id, relation_data in data.get("relations", {}).items():
            relation = Relation(
                relation_data["id"],
                relation_data["source"],
                relation_data["target"],
                relation_data["type"],
                relation_data.get("properties", {})
            )
            relation.weight = relation_data.get("weight", 1.0)
            self.relations[relation_id] = relation


class GraphQuery:
    """图查询引擎"""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
    
    def find_common_neighbors(self, entity1_id: str, entity2_id: str) -> List[str]:
        """查找共同邻居"""
        neighbors1 = set(neighbor for neighbor, _ in self.graph.adjacency_list.get(entity1_id, []))
        neighbors2 = set(neighbor for neighbor, _ in self.graph.adjacency_list.get(entity2_id, []))
        return list(neighbors1 & neighbors2)
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Dijkstra最短路径"""
        distances = {source_id: 0}
        previous = {}
        visited = set()
        queue = [(0, source_id)]
        
        while queue:
            current_dist, current_id = queue.pop(0)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == target_id:
                path = []
                node = target_id
                while node in previous:
                    path.append(node)
                    node = previous[node]
                path.append(source_id)
                return path[::-1]
            
            for neighbor_id, _ in self.graph.adjacency_list.get(current_id, []):
                if neighbor_id not in visited:
                    new_dist = current_dist + 1
                    if neighbor_id not in distances or new_dist < distances[neighbor_id]:
                        distances[neighbor_id] = new_dist
                        previous[neighbor_id] = current_id
                        queue.append((new_dist, neighbor_id))
        
        return None
    
    def calculate_pagerank(self, damping: float = 0.85, iterations: int = 100) -> Dict[str, float]:
        """PageRank算法"""
        n = len(self.graph.entities)
        if n == 0:
            return {}
        
        pr = {eid: 1.0 / n for eid in self.graph.entities}
        
        for _ in range(iterations):
            new_pr = {}
            
            for entity_id in self.graph.entities:
                rank_sum = 0.0
                
                for other_id, relations in self.graph.adjacency_list.items():
                    for neighbor_id, _ in relations:
                        if neighbor_id == entity_id:
                            out_degree = len(self.graph.adjacency_list[other_id])
                            if out_degree > 0:
                                rank_sum += pr[other_id] / out_degree
                
                new_pr[entity_id] = (1 - damping) / n + damping * rank_sum
            
            pr = new_pr
        
        return pr


class ReasoningEngine:
    """推理引擎"""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.rules = []
    
    def add_rule(self, rule_name: str, condition: callable, conclusion: callable):
        """添加推理规则"""
        self.rules.append({
            "name": rule_name,
            "condition": condition,
            "conclusion": conclusion
        })
    
    def forward_chain(self, entity_id: str) -> List[Dict[str, Any]]:
        """前向链推理"""
        inferred = []
        
        for rule in self.rules:
            if rule["condition"](entity_id, self.graph):
                result = rule["conclusion"](entity_id, self.graph)
                if result:
                    inferred.append({
                        "rule": rule["name"],
                        "result": result
                    })
        
        return inferred
    
    def suggest_relations(self, entity_id: str) -> List[Dict[str, Any]]:
        """建议可能的关系"""
        suggestions = []
        entity = self.graph.get_entity(entity_id)
        
        if not entity:
            return suggestions
        
        entity_type = entity.type
        
        related = self.graph.get_related_entities(entity_id, depth=2)
        
        for depth, related_ids in related.items():
            for related_id in related_ids:
                related_entity = self.graph.get_entity(related_id)
                if related_entity:
                    suggestions.append({
                        "target_id": related_id,
                        "target_name": related_entity.name,
                        "target_type": related_entity.type,
                        "reason": f"通过{depth}层关系连接"
                    })
        
        return suggestions


# 全局实例
knowledge_graph = KnowledgeGraph("MTSCOS")
query_engine = GraphQuery(knowledge_graph)
reasoning_engine = ReasoningEngine(knowledge_graph)
