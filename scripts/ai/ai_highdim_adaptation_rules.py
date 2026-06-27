#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI高维适配法则系统 - AI High-Dimensional Adaptation Rules System
MTSCOS AI Project v3.1
深度高维度AI功能适配，支持系统各层级各方面的弹性匹配
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
import secrets
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_highdim_adaptation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_highdim_adaptation')

class AdaptationDimension(Enum):
    """适配维度"""
    SYNTAX = "syntax"                    # 语法维度
    SEMANTIC = "semantic"                # 语义维度
    CONTEXTUAL = "contextual"           # 上下文维度
    FUNCTIONAL = "functional"            # 功能维度
    BEHAVIORAL = "behavioral"            # 行为维度
    COGNITIVE = "cognitive"              # 认知维度
    TEMPORAL = "temporal"                # 时间维度
    SPATIAL = "spatial"                  # 空间维度
    RELATIONAL = "relational"            # 关系维度
    EVOLUTIONARY = "evolutionary"        # 进化维度

class AdaptationLevel(Enum):
    """适配级别"""
    SURFACE = "surface"                  # 表层适配
    STRUCTURAL = "structural"            # 结构适配
    SEMANTIC = "semantic"                # 语义适配
    PRAGMATIC = "pragmatic"             # 语用适配
    COGNITIVE = "cognitive"              # 认知适配
    META = "meta"                        # 元层级适配

class SystemLayer(Enum):
    """系统层级"""
    PRESENTATION = "presentation"         # 表现层
    BUSINESS = "business"               # 业务层
    SERVICE = "service"                 # 服务层
    DATA = "data"                       # 数据层
    INFRASTRUCTURE = "infrastructure"   # 基础设施层
    SECURITY = "security"               # 安全层
    INTEGRATION = "integration"          # 集成层

class FunctionCategory(Enum):
    """功能类别"""
    COMPUTATION = "computation"          # 计算功能
    COGNITION = "cognition"             # 认知功能
    COMMUNICATION = "communication"      # 通信功能
    OPTIMIZATION = "optimization"        # 优化功能
    PREDICTION = "prediction"            # 预测功能
    REASONING = "reasoning"              # 推理功能
    LEARNING = "learning"                # 学习功能
    MEMORY = "memory"                    # 记忆功能
    PERCEPTION = "perception"           # 感知功能
    ACTION = "action"                   # 行动功能

class MatchingStrategy(Enum):
    """匹配策略"""
    EXACT = "exact"                     # 精确匹配
    FUZZY = "fuzzy"                     # 模糊匹配
    SEMANTIC = "semantic"               # 语义匹配
    STRUCTURAL = "structural"           # 结构匹配
    BEHAVIORAL = "behavioral"           # 行为匹配
    MULTI_DIMENSIONAL = "multi_dimensional"  # 多维度匹配

@dataclass
class DimensionVector:
    """维度向量"""
    dimension: AdaptationDimension
    value: float
    weight: float = 1.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptationPattern:
    """适配模式"""
    pattern_id: str
    name: str
    dimensions: List[DimensionVector]
    system_layer: SystemLayer
    function_category: FunctionCategory
    match_score: float
    adaptation_rules: Dict[str, Any]
    success_rate: float
    usage_count: int = 0
    created_at: str = None

@dataclass
class LayerMapping:
    """层级映射"""
    mapping_id: str
    source_layer: SystemLayer
    target_layer: SystemLayer
    dimension_vectors: List[DimensionVector]
    transformation_rules: Dict[str, Any]
    compatibility_score: float
    created_at: str = None

@dataclass
class FunctionalBridge:
    """功能桥接"""
    bridge_id: str
    source_function: FunctionCategory
    target_function: FunctionCategory
    dimension_vectors: List[DimensionVector]
    adaptation_layer: AdaptationLevel
    performance_metrics: Dict[str, float]
    active: bool = True
    created_at: str = None

@dataclass
class AdaptationContext:
    """适配上下文"""
    context_id: str
    system_state: Dict[str, Any]
    available_dimensions: List[AdaptationDimension]
    required_dimensions: List[AdaptationDimension]
    current_layer: SystemLayer
    target_layer: SystemLayer
    constraints: Dict[str, Any]
    timestamp: str

@dataclass
class MultiDimensionalMatcher:
    """多维度匹配器"""
    matcher_id: str
    dimensions: List[DimensionVector]
    similarity_scores: Dict[AdaptationDimension, float]
    aggregated_score: float
    matched_patterns: List[str]
    confidence: float
    timestamp: str

class VectorSpaceModel:
    """向量空间模型"""
    
    def __init__(self, dimensions: int = 10):
        self.dimensions = dimensions
        self.dimension_weights = {}
        self.dimension_vectors = {}
    
    def create_vector(self, dimension: AdaptationDimension, value: float, 
                     weight: float = 1.0) -> np.ndarray:
        """创建维度向量"""
        vector = np.zeros(self.dimensions)
        dim_idx = self._get_dimension_index(dimension)
        if 0 <= dim_idx < self.dimensions:
            vector[dim_idx] = value * weight
        return vector
    
    def _get_dimension_index(self, dimension: AdaptationDimension) -> int:
        """获取维度索引"""
        dim_list = list(AdaptationDimension)
        try:
            return dim_list.index(dimension)
        except ValueError:
            return 0
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def euclidean_distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算欧氏距离"""
        return float(np.linalg.norm(vec1 - vec2))
    
    def manhattan_distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算曼哈顿距离"""
        return float(np.sum(np.abs(vec1 - vec2)))
    
    def weighted_distance(self, vec1: np.ndarray, vec2: np.ndarray, 
                        weights: np.ndarray) -> float:
        """计算加权距离"""
        return float(np.sum(weights * np.abs(vec1 - vec2)))

class HighDimensionalAdapter:
    """高维适配器核心"""
    
    def __init__(self, db_path: str = "ai_highdim_adaptation.db"):
        self.db_path = db_path
        self.vector_space = VectorSpaceModel(dimensions=len(AdaptationDimension))
        self.dimension_weights = self._initialize_dimension_weights()
        self.layer_mappings = {}
        self.functional_bridges = {}
        self.adaptation_cache = {}
        self.lock = threading.Lock()
        self._init_database()
        self._init_default_patterns()
    
    def _initialize_dimension_weights(self) -> Dict[AdaptationDimension, float]:
        """初始化维度权重"""
        return {
            AdaptationDimension.SYNTAX: 0.8,
            AdaptationDimension.SEMANTIC: 0.9,
            AdaptationDimension.CONTEXTUAL: 0.85,
            AdaptationDimension.FUNCTIONAL: 0.95,
            AdaptationDimension.BEHAVIORAL: 0.8,
            AdaptationDimension.COGNITIVE: 0.9,
            AdaptationDimension.TEMPORAL: 0.75,
            AdaptationDimension.SPATIAL: 0.7,
            AdaptationDimension.RELATIONAL: 0.85,
            AdaptationDimension.EVOLUTIONARY: 0.9
        }
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptation_patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dimensions TEXT,
                system_layer TEXT,
                function_category TEXT,
                match_score REAL DEFAULT 0.0,
                adaptation_rules TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS layer_mappings (
                mapping_id TEXT PRIMARY KEY,
                source_layer TEXT NOT NULL,
                target_layer TEXT NOT NULL,
                dimension_vectors TEXT,
                transformation_rules TEXT,
                compatibility_score REAL DEFAULT 0.0,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functional_bridges (
                bridge_id TEXT PRIMARY KEY,
                source_function TEXT NOT NULL,
                target_function TEXT NOT NULL,
                dimension_vectors TEXT,
                adaptation_layer TEXT,
                performance_metrics TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptation_contexts (
                context_id TEXT PRIMARY KEY,
                system_state TEXT,
                available_dimensions TEXT,
                required_dimensions TEXT,
                current_layer TEXT,
                target_layer TEXT,
                constraints TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS multi_dimensional_matches (
                matcher_id TEXT PRIMARY KEY,
                dimensions TEXT,
                similarity_scores TEXT,
                aggregated_score REAL DEFAULT 0.0,
                matched_patterns TEXT,
                confidence REAL DEFAULT 0.0,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptation_metrics (
                metric_id TEXT PRIMARY KEY,
                dimension TEXT,
                value REAL,
                weight REAL,
                confidence REAL,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"高维适配数据库初始化完成: {self.db_path}")
    
    def _init_default_patterns(self):
        """初始化默认适配模式"""
        default_patterns = [
            {
                'pattern_id': 'PAT-001',
                'name': '跨层语义映射',
                'dimensions': [
                    DimensionVector(AdaptationDimension.SYNTAX, 0.8, 0.8),
                    DimensionVector(AdaptationDimension.SEMANTIC, 0.9, 0.9)
                ],
                'system_layer': SystemLayer.BUSINESS,
                'function_category': FunctionCategory.REASONING,
                'match_score': 0.85,
                'adaptation_rules': {'strategy': 'semantic_mapping', 'depth': 'deep'}
            },
            {
                'pattern_id': 'PAT-002',
                'name': '功能协同适配',
                'dimensions': [
                    DimensionVector(AdaptationDimension.FUNCTIONAL, 0.95, 0.95),
                    DimensionVector(AdaptationDimension.RELATIONAL, 0.85, 0.85)
                ],
                'system_layer': SystemLayer.SERVICE,
                'function_category': FunctionCategory.OPTIMIZATION,
                'match_score': 0.90,
                'adaptation_rules': {'strategy': 'functional_coordination', 'sync': 'real_time'}
            },
            {
                'pattern_id': 'PAT-003',
                'name': '认知进化适配',
                'dimensions': [
                    DimensionVector(AdaptationDimension.COGNITIVE, 0.9, 0.9),
                    DimensionVector(AdaptationDimension.EVOLUTIONARY, 0.9, 0.9)
                ],
                'system_layer': SystemLayer.DATA,
                'function_category': FunctionCategory.LEARNING,
                'match_score': 0.92,
                'adaptation_rules': {'strategy': 'cognitive_evolution', 'learning_rate': 0.15}
            }
        ]
        
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            for pattern in default_patterns:
                cursor.execute("SELECT pattern_id FROM adaptation_patterns WHERE pattern_id = ?",
                              (pattern['pattern_id'],))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO adaptation_patterns
                        (pattern_id, name, dimensions, system_layer, function_category,
                         match_score, adaptation_rules, success_rate, usage_count, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pattern['pattern_id'],
                        pattern['name'],
                        json.dumps([{'dimension': d.dimension.value, 'value': d.value, 
                                    'weight': d.weight} for d in pattern['dimensions']]),
                        pattern['system_layer'].value,
                        pattern['function_category'].value,
                        pattern['match_score'],
                        json.dumps(pattern['adaptation_rules']),
                        0.85,
                        0,
                        datetime.now().isoformat()
                    ))
            
            conn.commit()
            conn.close()
    
    def register_adaptation_pattern(self, name: str, dimensions: List[DimensionVector],
                                   system_layer: SystemLayer, 
                                   function_category: FunctionCategory,
                                   adaptation_rules: Dict[str, Any]) -> str:
        """注册适配模式"""
        pattern_id = f"PAT-{int(time.time())}-{secrets.token_hex(4)}"
        
        pattern = AdaptationPattern(
            pattern_id=pattern_id,
            name=name,
            dimensions=dimensions,
            system_layer=system_layer,
            function_category=function_category,
            match_score=0.0,
            adaptation_rules=adaptation_rules,
            success_rate=0.0,
            created_at=datetime.now().isoformat()
        )
        
        self._save_pattern(pattern)
        logger.info(f"适配模式已注册: {pattern_id} - {name}")
        return pattern_id
    
    def _save_pattern(self, pattern: AdaptationPattern):
        """保存适配模式"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adaptation_patterns
                (pattern_id, name, dimensions, system_layer, function_category,
                 match_score, adaptation_rules, success_rate, usage_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_id,
                pattern.name,
                json.dumps([{'dimension': d.dimension.value, 'value': d.value, 
                           'weight': d.weight} for d in pattern.dimensions]),
                pattern.system_layer.value,
                pattern.function_category.value,
                pattern.match_score,
                json.dumps(pattern.adaptation_rules),
                pattern.success_rate,
                pattern.usage_count,
                pattern.created_at
            ))
            conn.commit()
            conn.close()
    
    def create_layer_mapping(self, source_layer: SystemLayer, target_layer: SystemLayer,
                           dimension_vectors: List[DimensionVector],
                           transformation_rules: Dict[str, Any]) -> str:
        """创建层级映射"""
        mapping_id = f"MAP-{int(time.time())}-{secrets.token_hex(4)}"
        
        mapping = LayerMapping(
            mapping_id=mapping_id,
            source_layer=source_layer,
            target_layer=target_layer,
            dimension_vectors=dimension_vectors,
            transformation_rules=transformation_rules,
            compatibility_score=0.0,
            created_at=datetime.now().isoformat()
        )
        
        self._save_layer_mapping(mapping)
        logger.info(f"层级映射已创建: {mapping_id} - {source_layer.value} -> {target_layer.value}")
        return mapping_id
    
    def _save_layer_mapping(self, mapping: LayerMapping):
        """保存层级映射"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            compatibility = self._calculate_compatibility(
                mapping.dimension_vectors,
                [self.dimension_weights.get(d.dimension, 1.0) for d in mapping.dimension_vectors]
            )
            
            cursor.execute("""
                INSERT INTO layer_mappings
                (mapping_id, source_layer, target_layer, dimension_vectors,
                 transformation_rules, compatibility_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                mapping.mapping_id,
                mapping.source_layer.value,
                mapping.target_layer.value,
                json.dumps([{'dimension': d.dimension.value, 'value': d.value, 
                           'weight': d.weight} for d in mapping.dimension_vectors]),
                json.dumps(mapping.transformation_rules),
                compatibility,
                mapping.created_at
            ))
            conn.commit()
            conn.close()
    
    def create_functional_bridge(self, source_function: FunctionCategory,
                               target_function: FunctionCategory,
                               dimension_vectors: List[DimensionVector],
                               adaptation_layer: AdaptationLevel) -> str:
        """创建功能桥接"""
        bridge_id = f"BRG-{int(time.time())}-{secrets.token_hex(4)}"
        
        bridge = FunctionalBridge(
            bridge_id=bridge_id,
            source_function=source_function,
            target_function=target_function,
            dimension_vectors=dimension_vectors,
            adaptation_layer=adaptation_layer,
            performance_metrics={},
            active=True,
            created_at=datetime.now().isoformat()
        )
        
        self._save_functional_bridge(bridge)
        logger.info(f"功能桥接已创建: {bridge_id} - {source_function.value} -> {target_function.value}")
        return bridge_id
    
    def _save_functional_bridge(self, bridge: FunctionalBridge):
        """保存功能桥接"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO functional_bridges
                (bridge_id, source_function, target_function, dimension_vectors,
                 adaptation_layer, performance_metrics, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bridge.bridge_id,
                bridge.source_function.value,
                bridge.target_function.value,
                json.dumps([{'dimension': d.dimension.value, 'value': d.value, 
                           'weight': d.weight} for d in bridge.dimension_vectors]),
                bridge.adaptation_layer.value,
                json.dumps(bridge.performance_metrics),
                int(bridge.active),
                bridge.created_at
            ))
            conn.commit()
            conn.close()
    
    def _calculate_compatibility(self, vectors: List[DimensionVector],
                                weights: List[float]) -> float:
        """计算兼容性分数"""
        if not vectors:
            return 0.0
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(v.value * w for v, w in zip(vectors, weights))
        return weighted_sum / total_weight
    
    def multi_dimensional_match(self, context: AdaptationContext,
                              strategy: MatchingStrategy = MatchingStrategy.MULTI_DIMENSIONAL) -> MultiDimensionalMatcher:
        """多维度匹配"""
        matcher_id = f"MATCH-{int(time.time())}-{secrets.token_hex(4)}"
        
        available_vectors = []
        for dim in context.available_dimensions:
            weight = self.dimension_weights.get(dim, 1.0)
            vector = self.vector_space.create_vector(dim, 0.5, weight)
            available_vectors.append(DimensionVector(dim, 0.5, weight))
        
        patterns = self._get_all_patterns()
        
        similarity_scores = {}
        for dim in context.available_dimensions:
            dim_similarities = []
            for pattern in patterns:
                for pvec in pattern['dimensions']:
                    if pvec['dimension'] == dim.value:
                        sim = self.vector_space.cosine_similarity(
                            self.vector_space.create_vector(dim, 0.5),
                            self.vector_space.create_vector(
                                AdaptationDimension(dim.value), 
                                pvec['value']
                            )
                        )
                        dim_similarities.append(sim)
            
            similarity_scores[dim.value] = max(dim_similarities) if dim_similarities else 0.0
        
        aggregated_score = sum(similarity_scores.values()) / len(similarity_scores) if similarity_scores else 0.0
        
        matched_patterns = [
            p['pattern_id'] for p in patterns 
            if p['match_score'] >= aggregated_score
        ]
        
        confidence = min(1.0, aggregated_score + 0.1)
        
        matcher = MultiDimensionalMatcher(
            matcher_id=matcher_id,
            dimensions=available_vectors,
            similarity_scores=similarity_scores,
            aggregated_score=aggregated_score,
            matched_patterns=matched_patterns,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
        
        self._save_matcher(matcher)
        logger.info(f"多维度匹配完成: {matcher_id} - 聚合分数: {aggregated_score:.3f}")
        return matcher
    
    def _get_all_patterns(self) -> List[Dict]:
        """获取所有模式"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM adaptation_patterns")
            rows = cursor.fetchall()
            conn.close()
            
            columns = ['pattern_id', 'name', 'dimensions', 'system_layer', 'function_category',
                      'match_score', 'adaptation_rules', 'success_rate', 'usage_count', 'created_at']
            
            patterns = []
            for row in rows:
                data = dict(zip(columns, row))
                data['dimensions'] = json.loads(data['dimensions'])
                patterns.append(data)
            
            return patterns
    
    def _save_matcher(self, matcher: MultiDimensionalMatcher):
        """保存匹配器"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO multi_dimensional_matches
                (matcher_id, dimensions, similarity_scores, aggregated_score,
                 matched_patterns, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                matcher.matcher_id,
                json.dumps([{'dimension': d.dimension.value, 'value': d.value, 
                           'weight': d.weight} for d in matcher.dimensions]),
                json.dumps(matcher.similarity_scores),
                matcher.aggregated_score,
                json.dumps(matcher.matched_patterns),
                matcher.confidence,
                matcher.timestamp
            ))
            conn.commit()
            conn.close()
    
    def adapt_across_layers(self, source_layer: SystemLayer, target_layer: SystemLayer,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """跨层级适配"""
        mappings = self._get_layer_mappings(source_layer, target_layer)
        
        if not mappings:
            mapping_id = self.create_layer_mapping(
                source_layer, target_layer,
                [DimensionVector(AdaptationDimension.SYNTAX, 0.7, 0.8),
                 DimensionVector(AdaptationDimension.SEMANTIC, 0.8, 0.9)],
                {'transformation': 'auto_generated', 'context': context}
            )
            mappings = self._get_layer_mappings(source_layer, target_layer)
        
        best_mapping = max(mappings, key=lambda m: m['compatibility_score'])
        
        adapted_content = self._transform_content(
            context.get('content', ''),
            json.loads(best_mapping['transformation_rules'])
        )
        
        return {
            'source_layer': source_layer.value,
            'target_layer': target_layer.value,
            'mapping_id': best_mapping['mapping_id'],
            'compatibility_score': best_mapping['compatibility_score'],
            'adapted_content': adapted_content,
            'dimensions': json.loads(best_mapping['dimension_vectors'])
        }
    
    def _get_layer_mappings(self, source_layer: SystemLayer, 
                           target_layer: SystemLayer) -> List[Dict]:
        """获取层级映射"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM layer_mappings 
                WHERE source_layer = ? AND target_layer = ?
            """, (source_layer.value, target_layer.value))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return []
            
            columns = ['mapping_id', 'source_layer', 'target_layer', 'dimension_vectors',
                       'transformation_rules', 'compatibility_score', 'created_at']
            
            mappings = []
            for row in rows:
                data = dict(zip(columns, row))
                mappings.append(data)
            
            return mappings
    
    def _transform_content(self, content: str, rules: Dict[str, Any]) -> str:
        """转换内容"""
        transformation = rules.get('transformation', 'passthrough')
        
        if transformation == 'semantic_expansion':
            return f"[SEMANTIC_EXPANSION]{content}[/SEMANTIC_EXPANSION]"
        elif transformation == 'structural_conversion':
            return f"[STRUCTURAL_CONVERSION]{content}[/STRUCTURAL_CONVERSION]"
        else:
            return content
    
    def bridge_functions(self, source_function: FunctionCategory,
                        target_function: FunctionCategory,
                        adaptation_level: AdaptationLevel) -> Optional[FunctionalBridge]:
        """桥接功能"""
        bridges = self._get_functional_bridges(source_function, target_function)
        
        if bridges:
            best_bridge = max(bridges, key=lambda b: b['performance_metrics'].get('efficiency', 0))
            return self._deserialize_bridge(best_bridge)
        
        bridge_id = self.create_functional_bridge(
            source_function, target_function,
            [DimensionVector(AdaptationDimension.FUNCTIONAL, 0.85, 0.95),
             DimensionVector(AdaptationDimension.RELATIONAL, 0.8, 0.85)],
            adaptation_level
        )
        
        bridges = self._get_functional_bridges(source_function, target_function)
        if bridges:
            return self._deserialize_bridge(bridges[0])
        
        return None
    
    def _get_functional_bridges(self, source: FunctionCategory,
                               target: FunctionCategory) -> List[Dict]:
        """获取功能桥接"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM functional_bridges 
                WHERE source_function = ? AND target_function = ? AND active = 1
            """, (source.value, target.value))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return []
            
            columns = ['bridge_id', 'source_function', 'target_function', 'dimension_vectors',
                       'adaptation_layer', 'performance_metrics', 'active', 'created_at']
            
            bridges = []
            for row in rows:
                data = dict(zip(columns, row))
                data['dimension_vectors'] = json.loads(data['dimension_vectors'])
                data['performance_metrics'] = json.loads(data['performance_metrics'])
                bridges.append(data)
            
            return bridges
    
    def _deserialize_bridge(self, data: Dict) -> FunctionalBridge:
        """反序列化桥接"""
        return FunctionalBridge(
            bridge_id=data['bridge_id'],
            source_function=FunctionCategory(data['source_function']),
            target_function=FunctionCategory(data['target_function']),
            dimension_vectors=[DimensionVector(
                AdaptationDimension(d['dimension']),
                d['value'],
                d['weight']
            ) for d in data['dimension_vectors']],
            adaptation_layer=AdaptationLevel(data['adaptation_layer']),
            performance_metrics=data['performance_metrics'],
            active=bool(data['active']),
            created_at=data['created_at']
        )
    
    def create_adaptation_context(self, system_state: Dict[str, Any],
                                 required_dimensions: List[AdaptationDimension],
                                 current_layer: SystemLayer,
                                 target_layer: SystemLayer,
                                 constraints: Dict[str, Any] = None) -> AdaptationContext:
        """创建适配上下文"""
        context_id = f"CTX-{int(time.time())}-{secrets.token_hex(4)}"
        
        available = [d for d in AdaptationDimension 
                     if d in required_dimensions or d in [
                         AdaptationDimension.SYNTAX,
                         AdaptationDimension.SEMANTIC,
                         AdaptationDimension.FUNCTIONAL
                     ]]
        
        context = AdaptationContext(
            context_id=context_id,
            system_state=system_state,
            available_dimensions=available,
            required_dimensions=required_dimensions,
            current_layer=current_layer,
            target_layer=target_layer,
            constraints=constraints or {},
            timestamp=datetime.now().isoformat()
        )
        
        self._save_context(context)
        logger.info(f"适配上下文已创建: {context_id}")
        return context
    
    def _save_context(self, context: AdaptationContext):
        """保存上下文"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adaptation_contexts
                (context_id, system_state, available_dimensions, required_dimensions,
                 current_layer, target_layer, constraints, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context.context_id,
                json.dumps(context.system_state),
                json.dumps([d.value for d in context.available_dimensions]),
                json.dumps([d.value for d in context.required_dimensions]),
                context.current_layer.value,
                context.target_layer.value,
                json.dumps(context.constraints),
                context.timestamp
            ))
            conn.commit()
            conn.close()
    
    def adaptive_optimize(self, ai_id: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """自适应优化"""
        available_dims = [
            AdaptationDimension.SYNTAX,
            AdaptationDimension.SEMANTIC,
            AdaptationDimension.FUNCTIONAL,
            AdaptationDimension.BEHAVIORAL,
            AdaptationDimension.COGNITIVE
        ]
        
        context = self.create_adaptation_context(
            system_state=current_state,
            required_dimensions=available_dims,
            current_layer=SystemLayer.BUSINESS,
            target_layer=SystemLayer.SERVICE
        )
        
        matcher = self.multi_dimensional_match(context, MatchingStrategy.MULTI_DIMENSIONAL)
        
        optimizations = []
        
        for dim in available_dims:
            if dim.value in matcher.similarity_scores:
                score = matcher.similarity_scores[dim.value]
                if score < 0.7:
                    optimizations.append({
                        'dimension': dim.value,
                        'current_score': score,
                        'target_score': 0.85,
                        'suggestion': f'优化{dim.value}维度的适配能力'
                    })
        
        return {
            'ai_id': ai_id,
            'aggregated_score': matcher.aggregated_score,
            'confidence': matcher.confidence,
            'matched_patterns': len(matcher.matched_patterns),
            'optimizations': optimizations,
            'recommendations': self._generate_recommendations(matcher)
        }
    
    def _generate_recommendations(self, matcher: MultiDimensionalMatcher) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if matcher.aggregated_score < 0.6:
            recommendations.append("建议增强多维度学习能力")
        
        if matcher.confidence < 0.7:
            recommendations.append("建议提高模式匹配的置信度")
        
        weak_dims = [d for d, s in matcher.similarity_scores.items() if s < 0.5]
        if weak_dims:
            recommendations.append(f"需要加强的维度: {', '.join(weak_dims)}")
        
        return recommendations
    
    def get_system_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取系统兼容性矩阵"""
        layers = list(SystemLayer)
        matrix = {}
        
        for source in layers:
            matrix[source.value] = {}
            for target in layers:
                if source == target:
                    matrix[source.value][target.value] = 1.0
                else:
                    mappings = self._get_layer_mappings(source, target)
                    if mappings:
                        matrix[source.value][target.value] = max(
                            m['compatibility_score'] for m in mappings
                        )
                    else:
                        matrix[source.value][target.value] = 0.0
        
        return matrix
    
    def get_function_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取功能兼容性矩阵"""
        functions = list(FunctionCategory)
        matrix = {}
        
        for source in functions:
            matrix[source.value] = {}
            for target in functions:
                if source == target:
                    matrix[source.value][target.value] = 1.0
                else:
                    bridges = self._get_functional_bridges(source, target)
                    if bridges:
                        matrix[source.value][target.value] = bridges[0][
                            'performance_metrics'
                        ].get('efficiency', 0.5)
                    else:
                        matrix[source.value][target.value] = 0.3
        
        return matrix
    
    def get_adapter_statistics(self) -> Dict[str, Any]:
        """获取适配器统计"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM adaptation_patterns")
            total_patterns = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM layer_mappings")
            total_mappings = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM functional_bridges WHERE active = 1")
            active_bridges = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM multi_dimensional_matches")
            total_matches = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT AVG(aggregated_score) FROM multi_dimensional_matches
            """)
            avg_match_score = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                'total_patterns': total_patterns,
                'total_mappings': total_mappings,
                'active_bridges': active_bridges,
                'total_matches': total_matches,
                'average_match_score': round(avg_match_score, 3),
                'dimension_count': len(AdaptationDimension),
                'layer_count': len(SystemLayer),
                'function_count': len(FunctionCategory)
            }

def main():
    """测试主函数"""
    print("\n🤖 AI高维适配法则系统测试")
    print("=" * 70)
    
    adapter = HighDimensionalAdapter()
    
    print("\n📊 适配器统计:")
    stats = adapter.get_adapter_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 测试注册适配模式:")
    pattern_id = adapter.register_adaptation_pattern(
        name="跨域语义适配",
        dimensions=[
            DimensionVector(AdaptationDimension.SEMANTIC, 0.9, 0.95),
            DimensionVector(AdaptationDimension.CONTEXTUAL, 0.85, 0.9),
            DimensionVector(AdaptationDimension.RELATIONAL, 0.8, 0.85)
        ],
        system_layer=SystemLayer.BUSINESS,
        function_category=FunctionCategory.COGNITION,
        adaptation_rules={'strategy': 'cross_domain_semantic'}
    )
    print(f"  模式ID: {pattern_id}")
    
    print("\n🧪 测试创建层级映射:")
    mapping_id = adapter.create_layer_mapping(
        source_layer=SystemLayer.PRESENTATION,
        target_layer=SystemLayer.BUSINESS,
        dimension_vectors=[
            DimensionVector(AdaptationDimension.SYNTAX, 0.8, 0.85),
            DimensionVector(AdaptationDimension.SEMANTIC, 0.9, 0.9)
        ],
        transformation_rules={'type': 'presentation_to_business'}
    )
    print(f"  映射ID: {mapping_id}")
    
    print("\n🧪 测试创建功能桥接:")
    bridge_id = adapter.create_functional_bridge(
        source_function=FunctionCategory.COMPUTATION,
        target_function=FunctionCategory.REASONING,
        dimension_vectors=[
            DimensionVector(AdaptationDimension.FUNCTIONAL, 0.9, 0.95),
            DimensionVector(AdaptationDimension.COGNITIVE, 0.85, 0.9)
        ],
        adaptation_layer=AdaptationLevel.COGNITIVE
    )
    print(f"  桥接ID: {bridge_id}")
    
    print("\n🧪 测试跨层级适配:")
    cross_layer_result = adapter.adapt_across_layers(
        source_layer=SystemLayer.PRESENTATION,
        target_layer=SystemLayer.SERVICE,
        context={'content': '用户请求数据展示'}
    )
    print(f"  兼容性分数: {cross_layer_result['compatibility_score']:.3f}")
    print(f"  转换内容: {cross_layer_result['adapted_content']}")
    
    print("\n🧪 测试多维度匹配:")
    context = adapter.create_adaptation_context(
        system_state={'status': 'active', 'load': 0.7},
        required_dimensions=[
            AdaptationDimension.SYNTAX,
            AdaptationDimension.SEMANTIC,
            AdaptationDimension.FUNCTIONAL
        ],
        current_layer=SystemLayer.BUSINESS,
        target_layer=SystemLayer.DATA
    )
    matcher = adapter.multi_dimensional_match(context)
    print(f"  聚合分数: {matcher.aggregated_score:.3f}")
    print(f"  置信度: {matcher.confidence:.3f}")
    print(f"  匹配模式数: {len(matcher.matched_patterns)}")
    
    print("\n🧪 测试功能桥接:")
    bridge = adapter.bridge_functions(
        source_function=FunctionCategory.LEARNING,
        target_function=FunctionCategory.MEMORY,
        adaptation_level=AdaptationLevel.META
    )
    if bridge:
        print(f"  桥接ID: {bridge.bridge_id}")
        print(f"  适配层级: {bridge.adaptation_layer.value}")
    
    print("\n🧪 测试自适应优化:")
    optimization = adapter.adaptive_optimize(
        ai_id='AI-SYS-001',
        current_state={'accuracy': 0.8, 'speed': 0.75, 'efficiency': 0.85}
    )
    print(f"  聚合分数: {optimization['aggregated_score']:.3f}")
    print(f"  置信度: {optimization['confidence']:.3f}")
    print(f"  优化项数: {len(optimization['optimizations'])}")
    for rec in optimization['recommendations']:
        print(f"    - {rec}")
    
    print("\n🧪 系统兼容性矩阵:")
    compat_matrix = adapter.get_system_compatibility_matrix()
    print("  层级兼容矩阵已生成")
    
    print("\n🧪 功能兼容性矩阵:")
    func_matrix = adapter.get_function_compatibility_matrix()
    print("  功能兼容矩阵已生成")
    
    print("\n📊 最终统计:")
    final_stats = adapter.get_adapter_statistics()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ AI高维适配法则系统测试完成")

if __name__ == '__main__':
    main()