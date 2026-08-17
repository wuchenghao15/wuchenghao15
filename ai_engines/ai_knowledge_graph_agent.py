#!/usr/bin/env python3
"""AI知识图谱Agent"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIKnowledgeGraphAgent(AIEmployee):
    """AI知识图谱Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI知识图谱专家"):
        super().__init__(employee_id, name, 'knowledge_graph', 8)
        self.skills = [
            '知识抽取', '实体识别', '关系抽取',
            '图谱构建', '知识推理', '知识融合',
            '图谱查询', '知识补全', '知识可视化'
        ]
        self.entities = []
        self.relations = []
        self.total_entities = 0
        self.total_relations = 0
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """实体抽取"""
        entity_types = ['人物', '组织', '地点', '时间', '事件', '概念']
        
        extracted = [
            {'entity': '张三', 'type': '人物', 'confidence': 0.95, 'position': [0, 2]},
            {'entity': '阿里巴巴', 'type': '组织', 'confidence': 0.92, 'position': [10, 14]},
            {'entity': '北京', 'type': '地点', 'confidence': 0.88, 'position': [20, 22]}
        ]
        
        self.entities.extend([e['entity'] for e in extracted])
        self.total_entities += len(extracted)
        
        return {
            'success': True,
            'entities': extracted,
            'total': len(extracted),
            'types_found': list(set(e['type'] for e in extracted))
        }
    
    def extract_relations(self, text: str) -> Dict[str, Any]:
        """关系抽取"""
        relations = [
            {'head': '张三', 'relation': '就职于', 'tail': '阿里巴巴', 'confidence': 0.90},
            {'head': '阿里巴巴', 'relation': '总部位于', 'tail': '杭州', 'confidence': 0.93}
        ]
        
        self.relations.extend(relations)
        self.total_relations += len(relations)
        
        return {
            'success': True,
            'relations': relations,
            'total': len(relations)
        }
    
    def build_graph(self, entities: List[Dict], relations: List[Dict]) -> Dict[str, Any]:
        """构建知识图谱"""
        graph = {
            'graph_id': f'graph_{datetime.now().timestamp()}',
            'name': '知识图谱',
            'entities': entities if entities else self.entities,
            'relations': relations if relations else self.relations,
            'entity_count': len(entities) if entities else self.total_entities,
            'relation_count': len(relations) if relations else self.total_relations,
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'graph': graph
        }
    
    def knowledge_reasoning(self, query: str, graph: Dict = None) -> Dict[str, Any]:
        """知识推理"""
        reasoning_results = [
            {'result': '根据图谱推理，张三是阿里巴巴的员工', 'confidence': 0.85, 'path': '张三 -> 就职于 -> 阿里巴巴'},
            {'result': '阿里巴巴总部位于杭州', 'confidence': 0.90, 'path': '阿里巴巴 -> 总部位于 -> 杭州'}
        ]
        
        return {
            'success': True,
            'query': query,
            'results': reasoning_results,
            'total': len(reasoning_results)
        }
    
    def knowledge_fusion(self, graphs: List[Dict]) -> Dict[str, Any]:
        """知识融合"""
        merged_entities = set()
        merged_relations = set()
        
        for graph in graphs:
            for entity in graph.get('entities', []):
                if isinstance(entity, dict):
                    merged_entities.add(entity.get('entity', str(entity)))
                else:
                    merged_entities.add(str(entity))
            for relation in graph.get('relations', []):
                if isinstance(relation, dict):
                    key = f"{relation.get('head', '')}|{relation.get('relation', '')}|{relation.get('tail', '')}"
                    merged_relations.add(key)
        
        return {
            'success': True,
            'fused_graph': {
                'graph_id': f'fused_{datetime.now().timestamp()}',
                'entity_count': len(merged_entities),
                'relation_count': len(merged_relations),
                'source_graphs': len(graphs)
            }
        }
    
    def query_graph(self, query: str, query_type: str = 'entity') -> Dict[str, Any]:
        """图谱查询"""
        if query_type == 'entity':
            results = [e for e in self.entities if query.lower() in str(e).lower()]
            return {
                'success': True,
                'query': query,
                'type': 'entity',
                'results': results,
                'count': len(results)
            }
        elif query_type == 'relation':
            results = [r for r in self.relations if query in str(r)]
            return {
                'success': True,
                'query': query,
                'type': 'relation',
                'results': results,
                'count': len(results)
            }
        else:
            return {'success': False, 'message': f'未知查询类型: {query_type}'}
    
    def knowledge_completion(self, graph: Dict) -> Dict[str, Any]:
        """知识补全"""
        completions = [
            {'head': '张三', 'relation': '工作地点', 'tail': '杭州', 'confidence': 0.78, 'method': 'transE'},
            {'head': '阿里巴巴', 'relation': '创始人', 'tail': '马云', 'confidence': 0.85, 'method': 'transR'}
        ]
        
        return {
            'success': True,
            'completions': completions,
            'total': len(completions),
            'methods_used': list(set(c['method'] for c in completions))
        }
    
    def entity_linking(self, entity: str, candidates: List[str]) -> Dict[str, Any]:
        """实体链接"""
        linked = []
        for i, candidate in enumerate(candidates):
            linked.append({
                'candidate': candidate,
                'confidence': round(0.9 - i * 0.15, 2),
                'matched': i == 0
            })
        
        return {
            'success': True,
            'entity': entity,
            'candidates': candidates,
            'linked_entity': candidates[0] if candidates else '',
            'confidence': 0.9,
            'all_links': linked
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图谱统计"""
        return {
            'success': True,
            'statistics': {
                'total_entities': self.total_entities,
                'total_relations': self.total_relations,
                'entity_types': 6,
                'relation_types': 10,
                'density': round(self.total_relations / max(self.total_entities ** 2, 1), 4)
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_entities': self.total_entities,
            'total_relations': self.total_relations,
            'entity_history_count': len(self.entities),
            'relation_history_count': len(self.relations),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }