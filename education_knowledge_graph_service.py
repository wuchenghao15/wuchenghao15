#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育知识图谱服务 (v15.28.0)
====================================
提供知识图谱构建、节点管理、关系管理、查询、推理、推荐、融合和更新等综合服务。

核心能力：
1. 知识图谱 - 图谱构建、图谱配置、图谱导出、图谱导入
2. 知识节点 - 节点创建、节点查询、节点更新、节点删除
3. 知识关系 - 关系创建、关系查询、关系更新、关系删除
4. 知识查询 - 精确查询、模糊查询、语义查询、关系查询、路径查询
5. 知识推理 - 演绎推理、归纳推理、类比推理、因果推理
6. 知识推荐 - 相关知识推荐、学习路径推荐、知识点推荐、资源推荐
7. 知识融合 - 实体对齐、关系融合、属性合并、冲突解决
8. 知识更新 - 增量更新、全量更新、实时更新、定期更新
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_knowledge_graph_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationKnowledgeGraph')


# ========== 知识图谱配置 ==========

KNOWLEDGE_TYPES = {
    'subject': {'name': '学科知识', 'description': '学科层面的知识体系', 'education_type': ['adult', 'k12']},
    'course': {'name': '课程知识', 'description': '具体课程的知识内容', 'education_type': ['adult', 'k12']},
    'knowledge_point': {'name': '知识点', 'description': '最小知识单元', 'education_type': ['adult', 'k12']},
    'concept': {'name': '概念', 'description': '抽象的知识概念', 'education_type': ['adult', 'k12']},
    'principle': {'name': '原理', 'description': '基本规律和法则', 'education_type': ['adult', 'k12']},
    'formula': {'name': '公式', 'description': '数学或科学公式', 'education_type': ['adult', 'k12']},
    'case': {'name': '案例', 'description': '实际应用案例', 'education_type': ['adult']},
    'practice': {'name': '实践', 'description': '实践操作知识', 'education_type': ['adult', 'k12']}
}

NODE_TYPES = {
    'entity': {'name': '实体节点', 'description': '具体的实体对象', 'education_type': ['adult', 'k12']},
    'concept': {'name': '概念节点', 'description': '抽象概念', 'education_type': ['adult', 'k12']},
    'relation': {'name': '关系节点', 'description': '表示关系的节点', 'education_type': ['adult', 'k12']},
    'attribute': {'name': '属性节点', 'description': '属性信息节点', 'education_type': ['adult', 'k12']},
    'event': {'name': '事件节点', 'description': '事件信息节点', 'education_type': ['adult']},
    'document': {'name': '文档节点', 'description': '文档资源节点', 'education_type': ['adult', 'k12']},
    'resource': {'name': '资源节点', 'description': '学习资源节点', 'education_type': ['adult', 'k12']},
    'user': {'name': '用户节点', 'description': '用户信息节点', 'education_type': ['adult', 'k12']}
}

RELATION_TYPES = {
    'contains': {'name': '包含关系', 'description': '一个节点包含另一个节点', 'education_type': ['adult', 'k12']},
    'belongs_to': {'name': '从属关系', 'description': '从属或归属关系', 'education_type': ['adult', 'k12']},
    'causal': {'name': '因果关系', 'description': '因果逻辑关系', 'education_type': ['adult', 'k12']},
    'temporal': {'name': '时序关系', 'description': '时间顺序关系', 'education_type': ['adult']},
    'similar': {'name': '相似关系', 'description': '相似或类比关系', 'education_type': ['adult', 'k12']},
    'contrast': {'name': '对比关系', 'description': '对比或对立关系', 'education_type': ['adult', 'k12']},
    'related': {'name': '关联关系', 'description': '一般关联关系', 'education_type': ['adult', 'k12']},
    'derived': {'name': '推导关系', 'description': '逻辑推导关系', 'education_type': ['adult', 'k12']}
}

QUERY_TYPES = {
    'exact': {'name': '精确查询', 'description': '精确匹配查询', 'education_type': ['adult', 'k12']},
    'fuzzy': {'name': '模糊查询', 'description': '模糊匹配查询', 'education_type': ['adult', 'k12']},
    'semantic': {'name': '语义查询', 'description': '语义相似度查询', 'education_type': ['adult', 'k12']},
    'relation': {'name': '关系查询', 'description': '基于关系的查询', 'education_type': ['adult', 'k12']},
    'path': {'name': '路径查询', 'description': '节点间路径查询', 'education_type': ['adult']},
    'multi_hop': {'name': '多跳查询', 'description': '多跳关系查询', 'education_type': ['adult']},
    'aggregate': {'name': '聚合查询', 'description': '数据聚合查询', 'education_type': ['adult', 'k12']},
    'full_text': {'name': '全文查询', 'description': '全文检索查询', 'education_type': ['adult', 'k12']}
}

REASONING_TYPES = {
    'deductive': {'name': '演绎推理', 'description': '从一般到特殊的推理', 'education_type': ['adult', 'k12']},
    'inductive': {'name': '归纳推理', 'description': '从特殊到一般的推理', 'education_type': ['adult']},
    'analogical': {'name': '类比推理', 'description': '基于相似性的推理', 'education_type': ['adult', 'k12']},
    'causal': {'name': '因果推理', 'description': '因果关系推理', 'education_type': ['adult']},
    'fuzzy': {'name': '模糊推理', 'description': '模糊逻辑推理', 'education_type': ['adult']},
    'common_sense': {'name': '常识推理', 'description': '基于常识的推理', 'education_type': ['adult', 'k12']},
    'logical': {'name': '逻辑推理', 'description': '形式逻辑推理', 'education_type': ['adult', 'k12']},
    'deep_learning': {'name': '深度学习推理', 'description': '基于深度学习的推理', 'education_type': ['adult']}
}

RECOMMENDATION_TYPES = {
    'related_knowledge': {'name': '相关知识推荐', 'description': '推荐相关知识内容', 'education_type': ['adult', 'k12']},
    'learning_path': {'name': '学习路径推荐', 'description': '推荐学习路径', 'education_type': ['adult', 'k12']},
    'knowledge_point': {'name': '知识点推荐', 'description': '推荐相关知识点', 'education_type': ['adult', 'k12']},
    'resource': {'name': '资源推荐', 'description': '推荐学习资源', 'education_type': ['adult', 'k12']},
    'expert': {'name': '专家推荐', 'description': '推荐领域专家', 'education_type': ['adult']},
    'course': {'name': '课程推荐', 'description': '推荐相关课程', 'education_type': ['adult', 'k12']},
    'practice': {'name': '实践推荐', 'description': '推荐实践项目', 'education_type': ['adult']},
    'association': {'name': '关联推荐', 'description': '基于关联规则的推荐', 'education_type': ['adult', 'k12']}
}

FUSION_METHODS = {
    'entity_alignment': {'name': '实体对齐', 'description': '不同来源实体对齐', 'education_type': ['adult', 'k12']},
    'relation_fusion': {'name': '关系融合', 'description': '关系信息融合', 'education_type': ['adult', 'k12']},
    'attribute_merge': {'name': '属性合并', 'description': '属性信息合并', 'education_type': ['adult', 'k12']},
    'conflict_resolution': {'name': '冲突解决', 'description': '解决数据冲突', 'education_type': ['adult', 'k12']},
    'knowledge_completion': {'name': '知识补全', 'description': '补全缺失知识', 'education_type': ['adult', 'k12']},
    'semantic_fusion': {'name': '语义融合', 'description': '语义层面融合', 'education_type': ['adult']},
    'structure_fusion': {'name': '结构融合', 'description': '结构层面融合', 'education_type': ['adult']},
    'incremental_fusion': {'name': '增量融合', 'description': '增量式融合更新', 'education_type': ['adult']}
}

UPDATE_METHODS = {
    'incremental': {'name': '增量更新', 'description': '只更新变化部分', 'education_type': ['adult', 'k12']},
    'full': {'name': '全量更新', 'description': '全面更新数据', 'education_type': ['adult', 'k12']},
    'real_time': {'name': '实时更新', 'description': '实时同步更新', 'education_type': ['adult']},
    'periodic': {'name': '定期更新', 'description': '按周期更新', 'education_type': ['adult', 'k12']},
    'event_driven': {'name': '事件驱动', 'description': '事件触发更新', 'education_type': ['adult']},
    'user_contribution': {'name': '用户贡献', 'description': '基于用户贡献更新', 'education_type': ['adult', 'k12']},
    'ml_update': {'name': '机器学习更新', 'description': '机器学习辅助更新', 'education_type': ['adult']},
    'manual_review': {'name': '人工审核', 'description': '人工审核更新', 'education_type': ['adult', 'k12']}
}


class EducationKnowledgeGraphService:
    """教育知识图谱服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_graph (
                        graph_id TEXT PRIMARY KEY,
                        graph_name TEXT NOT NULL,
                        description TEXT,
                        education_type TEXT NOT NULL,
                        subject TEXT,
                        version TEXT DEFAULT '1.0',
                        node_count INTEGER DEFAULT 0,
                        relation_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS graph_config (
                        config_id TEXT PRIMARY KEY,
                        graph_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        description TEXT,
                        created_at TEXT,
                        FOREIGN KEY (graph_id) REFERENCES knowledge_graph(graph_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_nodes (
                        node_id TEXT PRIMARY KEY,
                        graph_id TEXT NOT NULL,
                        node_type TEXT NOT NULL,
                        knowledge_type TEXT,
                        node_name TEXT NOT NULL,
                        node_label TEXT,
                        description TEXT,
                        content TEXT,
                        metadata TEXT,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        subject TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (graph_id) REFERENCES knowledge_graph(graph_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS node_properties (
                        property_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id TEXT NOT NULL,
                        property_key TEXT NOT NULL,
                        property_value TEXT,
                        property_type TEXT DEFAULT 'string',
                        created_at TEXT,
                        FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_relations (
                        relation_id TEXT PRIMARY KEY,
                        graph_id TEXT NOT NULL,
                        source_node_id TEXT NOT NULL,
                        target_node_id TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        relation_name TEXT,
                        weight REAL DEFAULT 1.0,
                        description TEXT,
                        education_type TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (graph_id) REFERENCES knowledge_graph(graph_id),
                        FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(node_id),
                        FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(node_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS relation_properties (
                        property_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        relation_id TEXT NOT NULL,
                        property_key TEXT NOT NULL,
                        property_value TEXT,
                        property_type TEXT DEFAULT 'string',
                        created_at TEXT,
                        FOREIGN KEY (relation_id) REFERENCES knowledge_relations(relation_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_query (
                        query_id TEXT PRIMARY KEY,
                        query_name TEXT NOT NULL,
                        query_type TEXT NOT NULL,
                        query_template TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS query_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_id TEXT,
                        query_text TEXT NOT NULL,
                        query_type TEXT,
                        education_type TEXT,
                        result_count INTEGER DEFAULT 0,
                        execution_time REAL DEFAULT 0,
                        status TEXT DEFAULT 'success',
                        created_at TEXT,
                        FOREIGN KEY (query_id) REFERENCES knowledge_query(query_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_reasoning (
                        reasoning_id TEXT PRIMARY KEY,
                        reasoning_name TEXT NOT NULL,
                        reasoning_type TEXT NOT NULL,
                        reasoning_rules TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reasoning_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reasoning_id TEXT,
                        reasoning_type TEXT NOT NULL,
                        input_data TEXT,
                        output_data TEXT,
                        confidence REAL DEFAULT 0,
                        education_type TEXT,
                        status TEXT DEFAULT 'success',
                        created_at TEXT,
                        FOREIGN KEY (reasoning_id) REFERENCES knowledge_reasoning(reasoning_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_recommendation (
                        rec_id TEXT PRIMARY KEY,
                        rec_name TEXT NOT NULL,
                        rec_type TEXT NOT NULL,
                        rec_algorithm TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recommendation_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rec_id TEXT,
                        rec_type TEXT NOT NULL,
                        user_id INTEGER,
                        target_node_id TEXT,
                        recommendations TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'success',
                        created_at TEXT,
                        FOREIGN KEY (rec_id) REFERENCES knowledge_recommendation(rec_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_fusion (
                        fusion_id TEXT PRIMARY KEY,
                        fusion_name TEXT NOT NULL,
                        fusion_method TEXT NOT NULL,
                        source_graph_id TEXT,
                        target_graph_id TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fusion_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fusion_id TEXT,
                        fusion_method TEXT NOT NULL,
                        source_data TEXT,
                        target_data TEXT,
                        fused_count INTEGER DEFAULT 0,
                        conflict_count INTEGER DEFAULT 0,
                        education_type TEXT,
                        status TEXT DEFAULT 'success',
                        created_at TEXT,
                        FOREIGN KEY (fusion_id) REFERENCES knowledge_fusion(fusion_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_update (
                        update_id TEXT PRIMARY KEY,
                        update_name TEXT NOT NULL,
                        update_method TEXT NOT NULL,
                        description TEXT,
                        education_type TEXT,
                        schedule TEXT,
                        is_active INTEGER DEFAULT 1,
                        last_run_at TEXT,
                        next_run_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS update_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        update_id TEXT,
                        update_method TEXT NOT NULL,
                        updated_count INTEGER DEFAULT 0,
                        affected_nodes INTEGER DEFAULT 0,
                        affected_relations INTEGER DEFAULT 0,
                        education_type TEXT,
                        status TEXT DEFAULT 'success',
                        message TEXT,
                        created_at TEXT,
                        FOREIGN KEY (update_id) REFERENCES knowledge_update(update_id)
                    )
                ''')
                conn.commit()
                logger.info('教育知识图谱服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 知识图谱 ==========

    def create_graph(self, graph_name: str, education_type: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            graph_id = f"kg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_graph (
                            graph_id, graph_name, description,
                            education_type, subject, version,
                            node_count, relation_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, '1.0', 0, 0, 'active', ?, ?)
                    ''', (graph_id, graph_name, kwargs.get('description'),
                          education_type, kwargs.get('subject'), now, now))
                    conn.commit()
                    logger.info(f'创建知识图谱: {graph_name} ({graph_id})')
                    return {'success': True, 'graph_id': graph_id}
        except Exception as e:
            logger.error(f'创建知识图谱失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_graph_info(self, graph_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                graph = cursor.fetchone()
                if not graph:
                    return {'success': False, 'error': '知识图谱不存在'}
                return {'success': True, 'graph': dict(graph)}
        except Exception as e:
            logger.error(f'获取知识图谱信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def export_graph(self, graph_id: str, export_format: str = 'json') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                graph = cursor.fetchone()
                if not graph:
                    return {'success': False, 'error': '知识图谱不存在'}
                cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ?', (graph_id,))
                nodes = [dict(n) for n in cursor.fetchall()]
                cursor.execute('SELECT * FROM knowledge_relations WHERE graph_id = ?', (graph_id,))
                relations = [dict(r) for r in cursor.fetchall()]
                export_data = {
                    'graph': dict(graph),
                    'nodes': nodes,
                    'relations': relations
                }
                return {'success': True, 'format': export_format, 'data': export_data}
        except Exception as e:
            logger.error(f'导出知识图谱失败: {e}')
            return {'success': False, 'error': str(e)}

    def import_graph(self, graph_data: Dict[str, Any], education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    graph_info = graph_data.get('graph', {})
                    graph_id = f"kg_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO knowledge_graph (
                            graph_id, graph_name, description,
                            education_type, subject, version,
                            node_count, relation_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (graph_id, graph_info.get('graph_name', 'Imported Graph'),
                          graph_info.get('description'),
                          education_type or graph_info.get('education_type', 'adult'),
                          graph_info.get('subject'), graph_info.get('version', '1.0'),
                          0, 0, now, now))
                    node_map = {}
                    for node in graph_data.get('nodes', []):
                        new_node_id = f"nd_{uuid.uuid4().hex[:12]}"
                        node_map[node.get('node_id')] = new_node_id
                        cursor.execute('''
                            INSERT INTO knowledge_nodes (
                                node_id, graph_id, node_type,
                                knowledge_type, node_name, node_label,
                                description, content, metadata,
                                education_type, grade_level, subject,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (new_node_id, graph_id, node.get('node_type'),
                              node.get('knowledge_type'), node.get('node_name'),
                              node.get('node_label'), node.get('description'),
                              node.get('content'), node.get('metadata'),
                              education_type or node.get('education_type', 'adult'),
                              node.get('grade_level'), node.get('subject'),
                              node.get('is_active', 1), now, now))
                    for relation in graph_data.get('relations', []):
                        new_relation_id = f"rl_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO knowledge_relations (
                                relation_id, graph_id, source_node_id,
                                target_node_id, relation_type, relation_name,
                                weight, description, education_type,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (new_relation_id, graph_id,
                              node_map.get(relation.get('source_node_id')),
                              node_map.get(relation.get('target_node_id')),
                              relation.get('relation_type'),
                              relation.get('relation_name'),
                              relation.get('weight', 1.0),
                              relation.get('description'),
                              education_type or relation.get('education_type', 'adult'),
                              relation.get('is_active', 1), now, now))
                    node_count = len(graph_data.get('nodes', []))
                    relation_count = len(graph_data.get('relations', []))
                    cursor.execute('''
                        UPDATE knowledge_graph SET
                            node_count = ?, relation_count = ?, updated_at = ?
                        WHERE graph_id = ?
                    ''', (node_count, relation_count, now, graph_id))
                    conn.commit()
                    logger.info(f'导入知识图谱: {graph_id}, nodes: {node_count}, relations: {relation_count}')
                    return {'success': True, 'graph_id': graph_id, 'node_count': node_count, 'relation_count': relation_count}
        except Exception as e:
            logger.error(f'导入知识图谱失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识节点 ==========

    def create_node(self, graph_id: str, node_type: str, node_name: str,
                    education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            node_id = f"nd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                    graph = cursor.fetchone()
                    if not graph:
                        return {'success': False, 'error': '知识图谱不存在'}
                    cursor.execute('''
                        INSERT INTO knowledge_nodes (
                            node_id, graph_id, node_type, knowledge_type,
                            node_name, node_label, description, content,
                            metadata, education_type, grade_level, subject,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (node_id, graph_id, node_type, kwargs.get('knowledge_type'),
                          node_name, kwargs.get('node_label'), kwargs.get('description'),
                          kwargs.get('content'), kwargs.get('metadata'),
                          education_type, kwargs.get('grade_level'),
                          kwargs.get('subject'), now, now))
                    cursor.execute('UPDATE knowledge_graph SET node_count = node_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    logger.info(f'创建知识节点: {node_name} ({node_id})')
                    return {'success': True, 'node_id': node_id}
        except Exception as e:
            logger.error(f'创建知识节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_nodes(self, graph_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_nodes WHERE graph_id = ?'
                params = [graph_id]
                if 'node_type' in kwargs:
                    query += ' AND node_type = ?'
                    params.append(kwargs['node_type'])
                if 'knowledge_type' in kwargs:
                    query += ' AND knowledge_type = ?'
                    params.append(kwargs['knowledge_type'])
                if 'education_type' in kwargs:
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                if 'subject' in kwargs:
                    query += ' AND subject = ?'
                    params.append(kwargs['subject'])
                if 'node_name' in kwargs:
                    query += ' AND node_name LIKE ?'
                    params.append(f"%{kwargs['node_name']}%")
                if 'is_active' in kwargs:
                    query += ' AND is_active = ?'
                    params.append(1 if kwargs['is_active'] else 0)
                page = kwargs.get('page', 1)
                page_size = kwargs.get('page_size', 20)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                nodes = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'nodes': nodes, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询知识节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_node(self, node_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_params = []
                    if 'node_name' in kwargs:
                        update_fields.append('node_name = ?')
                        update_params.append(kwargs['node_name'])
                    if 'node_label' in kwargs:
                        update_fields.append('node_label = ?')
                        update_params.append(kwargs['node_label'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        update_params.append(kwargs['description'])
                    if 'content' in kwargs:
                        update_fields.append('content = ?')
                        update_params.append(kwargs['content'])
                    if 'metadata' in kwargs:
                        update_fields.append('metadata = ?')
                        update_params.append(kwargs['metadata'])
                    if 'grade_level' in kwargs:
                        update_fields.append('grade_level = ?')
                        update_params.append(kwargs['grade_level'])
                    if 'subject' in kwargs:
                        update_fields.append('subject = ?')
                        update_params.append(kwargs['subject'])
                    if 'is_active' in kwargs:
                        update_fields.append('is_active = ?')
                        update_params.append(1 if kwargs['is_active'] else 0)
                    if not update_fields:
                        return {'success': False, 'error': '未提供更新字段'}
                    update_fields.append('updated_at = ?')
                    update_params.append(now)
                    update_params.append(node_id)
                    query = f'UPDATE knowledge_nodes SET {", ".join(update_fields)} WHERE node_id = ?'
                    cursor.execute(query, update_params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '节点不存在'}
        except Exception as e:
            logger.error(f'更新知识节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_node(self, node_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT graph_id FROM knowledge_nodes WHERE node_id = ?', (node_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '节点不存在'}
                    graph_id = result[0]
                    cursor.execute('UPDATE knowledge_nodes SET is_active = 0, updated_at = ? WHERE node_id = ?', (now, node_id))
                    cursor.execute('UPDATE knowledge_relations SET is_active = 0, updated_at = ? WHERE source_node_id = ? OR target_node_id = ?', (now, node_id, node_id))
                    cursor.execute('UPDATE knowledge_graph SET node_count = node_count - 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    logger.info(f'删除知识节点: {node_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'删除知识节点失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识关系 ==========

    def create_relation(self, graph_id: str, source_node_id: str,
                        target_node_id: str, relation_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            relation_id = f"rl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                    graph = cursor.fetchone()
                    if not graph:
                        return {'success': False, 'error': '知识图谱不存在'}
                    cursor.execute('SELECT is_active FROM knowledge_nodes WHERE node_id = ?', (source_node_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '源节点不存在'}
                    cursor.execute('SELECT is_active FROM knowledge_nodes WHERE node_id = ?', (target_node_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '目标节点不存在'}
                    cursor.execute('''
                        INSERT INTO knowledge_relations (
                            relation_id, graph_id, source_node_id,
                            target_node_id, relation_type, relation_name,
                            weight, description, education_type,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (relation_id, graph_id, source_node_id, target_node_id,
                          relation_type, kwargs.get('relation_name'),
                          kwargs.get('weight', 1.0), kwargs.get('description'),
                          education_type, now, now))
                    cursor.execute('UPDATE knowledge_graph SET relation_count = relation_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    logger.info(f'创建知识关系: {relation_id}')
                    return {'success': True, 'relation_id': relation_id}
        except Exception as e:
            logger.error(f'创建知识关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_relations(self, graph_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_relations WHERE graph_id = ?'
                params = [graph_id]
                if 'relation_type' in kwargs:
                    query += ' AND relation_type = ?'
                    params.append(kwargs['relation_type'])
                if 'education_type' in kwargs:
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                if 'source_node_id' in kwargs:
                    query += ' AND source_node_id = ?'
                    params.append(kwargs['source_node_id'])
                if 'target_node_id' in kwargs:
                    query += ' AND target_node_id = ?'
                    params.append(kwargs['target_node_id'])
                if 'is_active' in kwargs:
                    query += ' AND is_active = ?'
                    params.append(1 if kwargs['is_active'] else 0)
                page = kwargs.get('page', 1)
                page_size = kwargs.get('page_size', 20)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                relations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'relations': relations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询知识关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_relation(self, relation_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_params = []
                    if 'relation_name' in kwargs:
                        update_fields.append('relation_name = ?')
                        update_params.append(kwargs['relation_name'])
                    if 'weight' in kwargs:
                        update_fields.append('weight = ?')
                        update_params.append(kwargs['weight'])
                    if 'description' in kwargs:
                        update_fields.append('description = ?')
                        update_params.append(kwargs['description'])
                    if 'is_active' in kwargs:
                        update_fields.append('is_active = ?')
                        update_params.append(1 if kwargs['is_active'] else 0)
                    if not update_fields:
                        return {'success': False, 'error': '未提供更新字段'}
                    update_fields.append('updated_at = ?')
                    update_params.append(now)
                    update_params.append(relation_id)
                    query = f'UPDATE knowledge_relations SET {", ".join(update_fields)} WHERE relation_id = ?'
                    cursor.execute(query, update_params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '关系不存在'}
        except Exception as e:
            logger.error(f'更新知识关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_relation(self, relation_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT graph_id FROM knowledge_relations WHERE relation_id = ?', (relation_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '关系不存在'}
                    graph_id = result[0]
                    cursor.execute('UPDATE knowledge_relations SET is_active = 0, updated_at = ? WHERE relation_id = ?', (now, relation_id))
                    cursor.execute('UPDATE knowledge_graph SET relation_count = relation_count - 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    conn.commit()
                    logger.info(f'删除知识关系: {relation_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'删除知识关系失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识查询 ==========

    def exact_query(self, graph_id: str, node_name: str,
                    education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_nodes WHERE graph_id = ? AND node_name = ? AND is_active = 1'
                params = [graph_id, node_name]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                nodes = [dict(n) for n in cursor.fetchall()]
                cursor.execute('INSERT INTO query_records (query_text, query_type, education_type, result_count, created_at) VALUES (?, ?, ?, ?, ?)',
                             (node_name, 'exact', education_type, len(nodes), now))
                conn.commit()
                return {'success': True, 'nodes': nodes, 'count': len(nodes)}
        except Exception as e:
            logger.error(f'精确查询失败: {e}')
            return {'success': False, 'error': str(e)}

    def fuzzy_query(self, graph_id: str, keyword: str,
                    education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1 AND (node_name LIKE ? OR description LIKE ? OR content LIKE ?)'
                params = [graph_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                nodes = [dict(n) for n in cursor.fetchall()]
                cursor.execute('INSERT INTO query_records (query_text, query_type, education_type, result_count, created_at) VALUES (?, ?, ?, ?, ?)',
                             (keyword, 'fuzzy', education_type, len(nodes), now))
                conn.commit()
                return {'success': True, 'nodes': nodes, 'count': len(nodes)}
        except Exception as e:
            logger.error(f'模糊查询失败: {e}')
            return {'success': False, 'error': str(e)}

    def semantic_query(self, graph_id: str, query_text: str,
                       education_type: str = None, top_k: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1'
                params = [graph_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                nodes = [dict(n) for n in cursor.fetchall()]
                scored_nodes = []
                for node in nodes:
                    content = f"{node.get('node_name', '')} {node.get('description', '')} {node.get('content', '')}"
                    if query_text.lower() in content.lower():
                        scored_nodes.append(node)
                scored_nodes = scored_nodes[:top_k]
                cursor.execute('INSERT INTO query_records (query_text, query_type, education_type, result_count, created_at) VALUES (?, ?, ?, ?, ?)',
                             (query_text, 'semantic', education_type, len(scored_nodes), now))
                conn.commit()
                return {'success': True, 'nodes': scored_nodes, 'count': len(scored_nodes)}
        except Exception as e:
            logger.error(f'语义查询失败: {e}')
            return {'success': False, 'error': str(e)}

    def relation_query(self, graph_id: str, source_node_id: str = None,
                       target_node_id: str = None, relation_type: str = None,
                       education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_relations WHERE graph_id = ? AND is_active = 1'
                params = [graph_id]
                if source_node_id:
                    query += ' AND source_node_id = ?'
                    params.append(source_node_id)
                if target_node_id:
                    query += ' AND target_node_id = ?'
                    params.append(target_node_id)
                if relation_type:
                    query += ' AND relation_type = ?'
                    params.append(relation_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                relations = [dict(r) for r in cursor.fetchall()]
                cursor.execute('INSERT INTO query_records (query_text, query_type, education_type, result_count, created_at) VALUES (?, ?, ?, ?, ?)',
                             (f"relation_query_{source_node_id}_{target_node_id}", 'relation', education_type, len(relations), now))
                conn.commit()
                return {'success': True, 'relations': relations, 'count': len(relations)}
        except Exception as e:
            logger.error(f'关系查询失败: {e}')
            return {'success': False, 'error': str(e)}

    def path_query(self, graph_id: str, start_node_id: str,
                   end_node_id: str, max_hops: int = 3,
                   education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                paths = []
                visited = {start_node_id}
                queue = [(start_node_id, [])]
                while queue:
                    current, path = queue.pop(0)
                    if current == end_node_id:
                        paths.append(path)
                        continue
                    if len(path) >= max_hops:
                        continue
                    query = 'SELECT relation_id, target_node_id FROM knowledge_relations WHERE graph_id = ? AND source_node_id = ? AND is_active = 1'
                    params = [graph_id, current]
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    for rel in cursor.fetchall():
                        if rel['target_node_id'] not in visited:
                            visited.add(rel['target_node_id'])
                            queue.append((rel['target_node_id'], path + [rel['relation_id']]))
                cursor.execute('INSERT INTO query_records (query_text, query_type, education_type, result_count, created_at) VALUES (?, ?, ?, ?, ?)',
                             (f"path_{start_node_id}_to_{end_node_id}", 'path', education_type, len(paths), now))
                conn.commit()
                return {'success': True, 'paths': paths, 'count': len(paths)}
        except Exception as e:
            logger.error(f'路径查询失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识推理 ==========

    def deductive_reasoning(self, graph_id: str, premise: str,
                            education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1', (graph_id,))
                nodes = [dict(n) for n in cursor.fetchall()]
                conclusions = []
                for node in nodes:
                    if education_type and node.get('education_type') != education_type:
                        continue
                    content = f"{node.get('node_name', '')} {node.get('description', '')} {node.get('content', '')}"
                    if premise.lower() in content.lower():
                        conclusions.append(node)
                cursor.execute('INSERT INTO reasoning_records (reasoning_type, input_data, output_data, confidence, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('deductive', premise, json.dumps([n['node_id'] for n in conclusions]), 0.85, education_type, now))
                conn.commit()
                return {'success': True, 'conclusions': conclusions, 'confidence': 0.85}
        except Exception as e:
            logger.error(f'演绎推理失败: {e}')
            return {'success': False, 'error': str(e)}

    def inductive_reasoning(self, graph_id: str, examples: List[str],
                            education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                patterns = []
                for example in examples:
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1 AND (node_name LIKE ? OR description LIKE ?)',
                                 (graph_id, f"%{example}%", f"%{example}%"))
                    matches = [dict(n) for n in cursor.fetchall()]
                    if education_type:
                        matches = [m for m in matches if m.get('education_type') == education_type]
                    patterns.extend(matches)
                cursor.execute('INSERT INTO reasoning_records (reasoning_type, input_data, output_data, confidence, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('inductive', json.dumps(examples), json.dumps([p['node_id'] for p in patterns]), 0.75, education_type, now))
                conn.commit()
                return {'success': True, 'patterns': patterns, 'confidence': 0.75}
        except Exception as e:
            logger.error(f'归纳推理失败: {e}')
            return {'success': False, 'error': str(e)}

    def analogical_reasoning(self, graph_id: str, source_node_id: str,
                             education_type: str = None, top_k: int = 5) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (source_node_id,))
                source_node = cursor.fetchone()
                if not source_node:
                    return {'success': False, 'error': '源节点不存在'}
                source = dict(source_node)
                query = 'SELECT * FROM knowledge_nodes WHERE graph_id = ? AND node_id != ? AND is_active = 1'
                params = [graph_id, source_node_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                candidates = [dict(n) for n in cursor.fetchall()]
                similar_nodes = []
                for node in candidates:
                    if node.get('node_type') == source.get('node_type'):
                        similar_nodes.append(node)
                similar_nodes = similar_nodes[:top_k]
                cursor.execute('INSERT INTO reasoning_records (reasoning_type, input_data, output_data, confidence, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('analogical', source_node_id, json.dumps([n['node_id'] for n in similar_nodes]), 0.70, education_type, now))
                conn.commit()
                return {'success': True, 'similar_nodes': similar_nodes, 'confidence': 0.70}
        except Exception as e:
            logger.error(f'类比推理失败: {e}')
            return {'success': False, 'error': str(e)}

    def causal_reasoning(self, graph_id: str, event_node_id: str,
                         education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                causes = []
                effects = []
                cursor.execute('SELECT * FROM knowledge_relations WHERE graph_id = ? AND target_node_id = ? AND relation_type = ? AND is_active = 1',
                             (graph_id, event_node_id, 'causal'))
                for rel in cursor.fetchall():
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (rel['source_node_id'],))
                    node = cursor.fetchone()
                    if node:
                        causes.append(dict(node))
                cursor.execute('SELECT * FROM knowledge_relations WHERE graph_id = ? AND source_node_id = ? AND relation_type = ? AND is_active = 1',
                             (graph_id, event_node_id, 'causal'))
                for rel in cursor.fetchall():
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (rel['target_node_id'],))
                    node = cursor.fetchone()
                    if node:
                        effects.append(dict(node))
                if education_type:
                    causes = [c for c in causes if c.get('education_type') == education_type]
                    effects = [e for e in effects if e.get('education_type') == education_type]
                cursor.execute('INSERT INTO reasoning_records (reasoning_type, input_data, output_data, confidence, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('causal', event_node_id, json.dumps({'causes': [c['node_id'] for c in causes], 'effects': [e['node_id'] for e in effects]}), 0.80, education_type, now))
                conn.commit()
                return {'success': True, 'causes': causes, 'effects': effects, 'confidence': 0.80}
        except Exception as e:
            logger.error(f'因果推理失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识推荐 ==========

    def recommend_related_knowledge(self, node_id: str,
                                    education_type: str = None, top_k: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT graph_id FROM knowledge_nodes WHERE node_id = ?', (node_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '节点不存在'}
                graph_id = result['graph_id']
                related = []
                cursor.execute('SELECT target_node_id FROM knowledge_relations WHERE graph_id = ? AND source_node_id = ? AND is_active = 1',
                             (graph_id, node_id))
                for rel in cursor.fetchall():
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ? AND is_active = 1', (rel['target_node_id'],))
                    node = cursor.fetchone()
                    if node:
                        if not education_type or node.get('education_type') == education_type:
                            related.append(dict(node))
                cursor.execute('SELECT source_node_id FROM knowledge_relations WHERE graph_id = ? AND target_node_id = ? AND is_active = 1',
                             (graph_id, node_id))
                for rel in cursor.fetchall():
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ? AND is_active = 1', (rel['source_node_id'],))
                    node = cursor.fetchone()
                    if node:
                        if not education_type or node.get('education_type') == education_type:
                            related.append(dict(node))
                related = related[:top_k]
                cursor.execute('INSERT INTO recommendation_records (rec_type, user_id, target_node_id, recommendations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('related_knowledge', None, node_id, json.dumps([r['node_id'] for r in related]), education_type, now))
                conn.commit()
                return {'success': True, 'recommendations': related, 'count': len(related)}
        except Exception as e:
            logger.error(f'相关知识推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_learning_path(self, start_node_id: str,
                                education_type: str = None, steps: int = 5) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT graph_id FROM knowledge_nodes WHERE node_id = ?', (start_node_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '起始节点不存在'}
                graph_id = result['graph_id']
                path = [start_node_id]
                current = start_node_id
                for _ in range(steps - 1):
                    cursor.execute('SELECT target_node_id FROM knowledge_relations WHERE graph_id = ? AND source_node_id = ? AND relation_type = ? AND is_active = 1',
                                 (graph_id, current, 'derived'))
                    next_nodes = cursor.fetchall()
                    if not next_nodes:
                        cursor.execute('SELECT target_node_id FROM knowledge_relations WHERE graph_id = ? AND source_node_id = ? AND is_active = 1',
                                     (graph_id, current))
                        next_nodes = cursor.fetchall()
                    if next_nodes:
                        current = next_nodes[0]['target_node_id']
                        if current not in path:
                            path.append(current)
                    else:
                        break
                path_nodes = []
                for nid in path:
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (nid,))
                    node = cursor.fetchone()
                    if node:
                        if not education_type or node.get('education_type') == education_type:
                            path_nodes.append(dict(node))
                cursor.execute('INSERT INTO recommendation_records (rec_type, user_id, target_node_id, recommendations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('learning_path', None, start_node_id, json.dumps(path), education_type, now))
                conn.commit()
                return {'success': True, 'path': path_nodes, 'path_ids': path}
        except Exception as e:
            logger.error(f'学习路径推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_knowledge_points(self, subject: str,
                                   education_type: str = None, top_k: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_nodes WHERE knowledge_type = ? AND is_active = 1'
                params = ['knowledge_point']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                cursor.execute(query, params)
                points = [dict(p) for p in cursor.fetchall()]
                points = points[:top_k]
                cursor.execute('INSERT INTO recommendation_records (rec_type, user_id, target_node_id, recommendations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('knowledge_point', None, subject, json.dumps([p['node_id'] for p in points]), education_type, now))
                conn.commit()
                return {'success': True, 'knowledge_points': points, 'count': len(points)}
        except Exception as e:
            logger.error(f'知识点推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_resources(self, node_id: str,
                            education_type: str = None, top_k: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT graph_id FROM knowledge_nodes WHERE node_id = ?', (node_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '节点不存在'}
                graph_id = result['graph_id']
                resources = []
                cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ? AND node_type = ? AND is_active = 1',
                             (graph_id, 'resource'))
                for node in cursor.fetchall():
                    if not education_type or node.get('education_type') == education_type:
                        resources.append(dict(node))
                resources = resources[:top_k]
                cursor.execute('INSERT INTO recommendation_records (rec_type, user_id, target_node_id, recommendations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                             ('resource', None, node_id, json.dumps([r['node_id'] for r in resources]), education_type, now))
                conn.commit()
                return {'success': True, 'resources': resources, 'count': len(resources)}
        except Exception as e:
            logger.error(f'资源推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识融合 ==========

    def entity_alignment(self, source_graph_id: str, target_graph_id: str,
                         education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1', (source_graph_id,))
                    source_nodes = [dict(n) for n in cursor.fetchall()]
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE graph_id = ? AND is_active = 1', (target_graph_id,))
                    target_nodes = [dict(n) for n in cursor.fetchall()]
                    aligned = []
                    conflicts = 0
                    for source in source_nodes:
                        if education_type and source.get('education_type') != education_type:
                            continue
                        for target in target_nodes:
                            if education_type and target.get('education_type') != education_type:
                                continue
                            if source.get('node_name') == target.get('node_name'):
                                aligned.append({'source_id': source['node_id'], 'target_id': target['node_id']})
                    cursor.execute('INSERT INTO fusion_records (fusion_method, source_data, target_data, fused_count, conflict_count, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 ('entity_alignment', source_graph_id, target_graph_id, len(aligned), conflicts, education_type, now))
                    conn.commit()
                    return {'success': True, 'aligned_count': len(aligned), 'conflicts': conflicts, 'alignments': aligned}
        except Exception as e:
            logger.error(f'实体对齐失败: {e}')
            return {'success': False, 'error': str(e)}

    def relation_fusion(self, source_graph_id: str, target_graph_id: str,
                        education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM knowledge_relations WHERE graph_id = ? AND is_active = 1', (source_graph_id,))
                    source_rels = [dict(r) for r in cursor.fetchall()]
                    cursor.execute('SELECT * FROM knowledge_relations WHERE graph_id = ? AND is_active = 1', (target_graph_id,))
                    target_rels = [dict(r) for r in cursor.fetchall()]
                    fused = []
                    conflicts = 0
                    for source in source_rels:
                        if education_type and source.get('education_type') != education_type:
                            continue
                        exists = False
                        for target in target_rels:
                            if education_type and target.get('education_type') != education_type:
                                continue
                            if source.get('source_node_id') == target.get('source_node_id') and \
                               source.get('target_node_id') == target.get('target_node_id') and \
                               source.get('relation_type') == target.get('relation_type'):
                                exists = True
                                break
                        if not exists:
                            fused.append(source)
                        else:
                            conflicts += 1
                    cursor.execute('INSERT INTO fusion_records (fusion_method, source_data, target_data, fused_count, conflict_count, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 ('relation_fusion', source_graph_id, target_graph_id, len(fused), conflicts, education_type, now))
                    conn.commit()
                    return {'success': True, 'fused_count': len(fused), 'conflicts': conflicts}
        except Exception as e:
            logger.error(f'关系融合失败: {e}')
            return {'success': False, 'error': str(e)}

    def attribute_merge(self, target_node_id: str, source_node_ids: List[str],
                        education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM knowledge_nodes WHERE node_id = ?', (target_node_id,))
                    target = cursor.fetchone()
                    if not target:
                        return {'success': False, 'error': '目标节点不存在'}
                    merged_props = {}
                    for source_id in source_node_ids:
                        cursor.execute('SELECT * FROM node_properties WHERE node_id = ?', (source_id,))
                        props = cursor.fetchall()
                        for prop in props:
                            merged_props[prop['property_key']] = prop['property_value']
                    for key, value in merged_props.items():
                        cursor.execute('INSERT OR REPLACE INTO node_properties (node_id, property_key, property_value, created_at) VALUES (?, ?, ?, ?)',
                                     (target_node_id, key, value, now))
                    conn.commit()
                    return {'success': True, 'merged_properties': len(merged_props)}
        except Exception as e:
            logger.error(f'属性合并失败: {e}')
            return {'success': False, 'error': str(e)}

    def conflict_resolution(self, graph_id: str, conflict_data: Dict[str, Any],
                            education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    resolved = 0
                    for conflict in conflict_data.get('conflicts', []):
                        node_id = conflict.get('node_id')
                        property_key = conflict.get('property_key')
                        resolved_value = conflict.get('resolved_value')
                        cursor.execute('UPDATE node_properties SET property_value = ? WHERE node_id = ? AND property_key = ?',
                                     (resolved_value, node_id, property_key))
                        if cursor.rowcount > 0:
                            resolved += 1
                    cursor.execute('INSERT INTO fusion_records (fusion_method, source_data, target_data, fused_count, conflict_count, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 ('conflict_resolution', graph_id, json.dumps(conflict_data), resolved, len(conflict_data.get('conflicts', [])) - resolved, education_type, now))
                    conn.commit()
                    return {'success': True, 'resolved_count': resolved}
        except Exception as e:
            logger.error(f'冲突解决失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识更新 ==========

    def incremental_update(self, graph_id: str, updates: Dict[str, Any],
                           education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updated_nodes = 0
                    updated_relations = 0
                    for node in updates.get('nodes', []):
                        node_id = node.get('node_id')
                        if node_id:
                            update_fields = []
                            params = []
                            if 'node_name' in node:
                                update_fields.append('node_name = ?')
                                params.append(node['node_name'])
                            if 'description' in node:
                                update_fields.append('description = ?')
                                params.append(node['description'])
                            if 'content' in node:
                                update_fields.append('content = ?')
                                params.append(node['content'])
                            if update_fields:
                                update_fields.append('updated_at = ?')
                                params.append(now)
                                params.append(node_id)
                                query = f'UPDATE knowledge_nodes SET {", ".join(update_fields)} WHERE node_id = ?'
                                cursor.execute(query, params)
                                updated_nodes += cursor.rowcount
                    for relation in updates.get('relations', []):
                        relation_id = relation.get('relation_id')
                        if relation_id:
                            update_fields = []
                            params = []
                            if 'weight' in relation:
                                update_fields.append('weight = ?')
                                params.append(relation['weight'])
                            if 'description' in relation:
                                update_fields.append('description = ?')
                                params.append(relation['description'])
                            if update_fields:
                                update_fields.append('updated_at = ?')
                                params.append(now)
                                params.append(relation_id)
                                query = f'UPDATE knowledge_relations SET {", ".join(update_fields)} WHERE relation_id = ?'
                                cursor.execute(query, params)
                                updated_relations += cursor.rowcount
                    cursor.execute('INSERT INTO update_records (update_method, updated_count, affected_nodes, affected_relations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 ('incremental', updated_nodes + updated_relations, updated_nodes, updated_relations, education_type, now))
                    conn.commit()
                    return {'success': True, 'updated_nodes': updated_nodes, 'updated_relations': updated_relations}
        except Exception as e:
            logger.error(f'增量更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def full_update(self, graph_id: str, graph_data: Dict[str, Any],
                     education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE knowledge_nodes SET is_active = 0, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    cursor.execute('UPDATE knowledge_relations SET is_active = 0, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                    node_count = 0
                    relation_count = 0
                    for node in graph_data.get('nodes', []):
                        node_id = f"nd_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO knowledge_nodes (
                                node_id, graph_id, node_type, knowledge_type,
                                node_name, node_label, description, content,
                                metadata, education_type, grade_level, subject,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        ''', (node_id, graph_id, node.get('node_type'),
                              node.get('knowledge_type'), node.get('node_name'),
                              node.get('node_label'), node.get('description'),
                              node.get('content'), node.get('metadata'),
                              education_type or node.get('education_type', 'adult'),
                              node.get('grade_level'), node.get('subject'),
                              now, now))
                        node_count += 1
                    for relation in graph_data.get('relations', []):
                        relation_id = f"rl_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO knowledge_relations (
                                relation_id, graph_id, source_node_id,
                                target_node_id, relation_type, relation_name,
                                weight, description, education_type,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        ''', (relation_id, graph_id, relation.get('source_node_id'),
                              relation.get('target_node_id'), relation.get('relation_type'),
                              relation.get('relation_name'), relation.get('weight', 1.0),
                              relation.get('description'),
                              education_type or relation.get('education_type', 'adult'),
                              now, now))
                        relation_count += 1
                    cursor.execute('UPDATE knowledge_graph SET node_count = ?, relation_count = ?, updated_at = ? WHERE graph_id = ?',
                                 (node_count, relation_count, now, graph_id))
                    cursor.execute('INSERT INTO update_records (update_method, updated_count, affected_nodes, affected_relations, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 ('full', node_count + relation_count, node_count, relation_count, education_type, now))
                    conn.commit()
                    return {'success': True, 'updated_nodes': node_count, 'updated_relations': relation_count}
        except Exception as e:
            logger.error(f'全量更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def real_time_update(self, graph_id: str, update_data: Dict[str, Any],
                         education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updated_count = 0
                    if update_data.get('action') == 'add_node':
                        node_id = f"nd_{uuid.uuid4().hex[:12]}"
                        node = update_data.get('data', {})
                        cursor.execute('''
                            INSERT INTO knowledge_nodes (
                                node_id, graph_id, node_type, knowledge_type,
                                node_name, node_label, description, content,
                                metadata, education_type, grade_level, subject,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        ''', (node_id, graph_id, node.get('node_type'),
                              node.get('knowledge_type'), node.get('node_name'),
                              node.get('node_label'), node.get('description'),
                              node.get('content'), node.get('metadata'),
                              education_type or node.get('education_type', 'adult'),
                              node.get('grade_level'), node.get('subject'),
                              now, now))
                        cursor.execute('UPDATE knowledge_graph SET node_count = node_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                        updated_count = 1
                    elif update_data.get('action') == 'add_relation':
                        relation_id = f"rl_{uuid.uuid4().hex[:12]}"
                        relation = update_data.get('data', {})
                        cursor.execute('''
                            INSERT INTO knowledge_relations (
                                relation_id, graph_id, source_node_id,
                                target_node_id, relation_type, relation_name,
                                weight, description, education_type,
                                is_active, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        ''', (relation_id, graph_id, relation.get('source_node_id'),
                              relation.get('target_node_id'), relation.get('relation_type'),
                              relation.get('relation_name'), relation.get('weight', 1.0),
                              relation.get('description'),
                              education_type or relation.get('education_type', 'adult'),
                              now, now))
                        cursor.execute('UPDATE knowledge_graph SET relation_count = relation_count + 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                        updated_count = 1
                    elif update_data.get('action') == 'delete_node':
                        node_id = update_data.get('node_id')
                        cursor.execute('UPDATE knowledge_nodes SET is_active = 0, updated_at = ? WHERE node_id = ?', (now, node_id))
                        cursor.execute('UPDATE knowledge_relations SET is_active = 0, updated_at = ? WHERE source_node_id = ? OR target_node_id = ?', (now, node_id, node_id))
                        cursor.execute('UPDATE knowledge_graph SET node_count = node_count - 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                        updated_count = 1
                    elif update_data.get('action') == 'delete_relation':
                        relation_id = update_data.get('relation_id')
                        cursor.execute('UPDATE knowledge_relations SET is_active = 0, updated_at = ? WHERE relation_id = ?', (now, relation_id))
                        cursor.execute('UPDATE knowledge_graph SET relation_count = relation_count - 1, updated_at = ? WHERE graph_id = ?', (now, graph_id))
                        updated_count = 1
                    cursor.execute('INSERT INTO update_records (update_method, updated_count, education_type, created_at) VALUES (?, ?, ?, ?)',
                                 ('real_time', updated_count, education_type, now))
                    conn.commit()
                    return {'success': True, 'updated_count': updated_count}
        except Exception as e:
            logger.error(f'实时更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def periodic_update(self, graph_id: str, schedule_type: str = 'daily',
                        education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            next_run = (datetime.now() + timedelta(days=1)).isoformat() if schedule_type == 'daily' else \
                       (datetime.now() + timedelta(weeks=1)).isoformat() if schedule_type == 'weekly' else \
                       (datetime.now() + timedelta(days=30)).isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_update (
                            update_id, update_name, update_method, description,
                            education_type, schedule, is_active, last_run_at,
                            next_run_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (f"upd_{uuid.uuid4().hex[:12]}", f"{schedule_type}_update",
                          'periodic', f"{schedule_type} periodic update",
                          education_type, schedule_type, now, next_run, now))
                    cursor.execute('INSERT INTO update_records (update_method, updated_count, education_type, message, created_at) VALUES (?, ?, ?, ?, ?)',
                                 ('periodic', 0, education_type, f"Triggered {schedule_type} update", now))
                    conn.commit()
                    return {'success': True, 'next_run_at': next_run}
        except Exception as e:
            logger.error(f'定期更新失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, graph_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}
                if graph_id:
                    cursor.execute('SELECT node_count, relation_count FROM knowledge_graph WHERE graph_id = ?', (graph_id,))
                    graph = cursor.fetchone()
                    if graph:
                        stats['node_count'] = graph['node_count']
                        stats['relation_count'] = graph['relation_count']
                    query = 'WHERE graph_id = ?'
                    params = [graph_id]
                else:
                    cursor.execute('SELECT SUM(node_count) as total_nodes, SUM(relation_count) as total_relations FROM knowledge_graph')
                    totals = cursor.fetchone()
                    stats['total_graphs'] = cursor.execute('SELECT COUNT(*) FROM knowledge_graph').fetchone()[0]
                    stats['total_nodes'] = totals['total_nodes'] or 0
                    stats['total_relations'] = totals['total_relations'] or 0
                    query = 'WHERE 1=1'
                    params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) FROM knowledge_nodes {query}', params)
                stats['active_nodes'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM knowledge_relations {query}', params)
                stats['active_relations'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM query_records {"WHERE education_type = ?" if education_type else ""}',
                             ([education_type] if education_type else []))
                stats['query_count'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM reasoning_records {"WHERE education_type = ?" if education_type else ""}',
                             ([education_type] if education_type else []))
                stats['reasoning_count'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM recommendation_records {"WHERE education_type = ?" if education_type else ""}',
                             ([education_type] if education_type else []))
                stats['recommendation_count'] = cursor.fetchone()[0]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}