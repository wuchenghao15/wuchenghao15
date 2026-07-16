#!/usr/bin/env python3
"""
MTSCOS AI 知识图谱服务 (v14.7.0)
===================================
AI 知识图谱构建、管理和查询服务。

核心能力：
1. 实体管理 - 实体CRUD和属性管理
2. 关系管理 - 关系类型和关系实例
3. 图谱构建 - 从文本/结构化数据自动抽取实体关系
4. 图查询 - 路径查询、邻居查询、子图查询
5. 实体融合 - 实体对齐和消歧
6. 知识推理 - 基于规则的知识推理
7. 社区发现 - 实体聚类和社区检测
8. 统计分析 - 图谱指标计算和可视化数据
"""
import os
import json
import re
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_knowledge_graph.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIKnowledgeGraph')


# ========== 默认知识图谱数据 ==========

DEFAULT_ENTITIES = [
    {'entity_id': 'E-SYS-001', 'name': 'MTSCOS系统', 'type': 'system',
     'description': 'MTSCOS AI智能教育系统', 'properties': {'version': '14.6.0', 'platform': 'Flask'}},
    {'entity_id': 'E-MOD-001', 'name': 'AI模型管理', 'type': 'module',
     'description': 'AI模型管理服务模块', 'properties': {'layer': 'core'}},
    {'entity_id': 'E-MOD-002', 'name': 'AI对话服务', 'type': 'module',
     'description': 'AI对话和意图识别服务', 'properties': {'layer': 'core'}},
    {'entity_id': 'E-MOD-003', 'name': 'AI知识库', 'type': 'module',
     'description': 'AI知识库和语义搜索', 'properties': {'layer': 'core'}},
    {'entity_id': 'E-MOD-004', 'name': 'AI工作流编排', 'type': 'module',
     'description': 'AI工作流DAG编排引擎', 'properties': {'layer': 'advanced'}},
    {'entity_id': 'E-MOD-005', 'name': 'AI决策引擎', 'type': 'module',
     'description': '基于规则的决策引擎', 'properties': {'layer': 'advanced'}},
    {'entity_id': 'E-PER-001', 'name': 'wuchenghao', 'type': 'person',
     'description': '系统超级管理员', 'properties': {'role': 'super_admin', 'level': '最高'}},
    {'entity_id': 'E-TECH-001', 'name': 'Python', 'type': 'technology',
     'description': 'Python编程语言', 'properties': {'version': '3.x'}},
    {'entity_id': 'E-TECH-002', 'name': 'Flask', 'type': 'technology',
     'description': 'Flask Web框架', 'properties': {'category': 'web_framework'}},
    {'entity_id': 'E-TECH-003', 'name': 'SQLite', 'type': 'technology',
     'description': 'SQLite数据库', 'properties': {'category': 'database'}},
]

DEFAULT_RELATIONS = [
    {'from': 'E-MOD-001', 'to': 'E-SYS-001', 'type': 'belongs_to'},
    {'from': 'E-MOD-002', 'to': 'E-SYS-001', 'type': 'belongs_to'},
    {'from': 'E-MOD-003', 'to': 'E-SYS-001', 'type': 'belongs_to'},
    {'from': 'E-MOD-004', 'to': 'E-SYS-001', 'type': 'belongs_to'},
    {'from': 'E-MOD-005', 'to': 'E-SYS-001', 'type': 'belongs_to'},
    {'from': 'E-MOD-001', 'to': 'E-MOD-002', 'type': 'supports'},
    {'from': 'E-MOD-003', 'to': 'E-MOD-002', 'type': 'supports'},
    {'from': 'E-MOD-004', 'to': 'E-MOD-005', 'type': 'integrates_with'},
    {'from': 'E-PER-001', 'to': 'E-SYS-001', 'type': 'manages'},
    {'from': 'E-TECH-001', 'to': 'E-SYS-001', 'type': 'developed_with'},
    {'from': 'E-TECH-002', 'to': 'E-SYS-001', 'type': 'developed_with'},
    {'from': 'E-TECH-003', 'to': 'E-SYS-001', 'type': 'used_by'},
]


# ========== 知识图谱服务 ==========

class AIKnowledgeGraph:
    """AI 知识图谱服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()
        # 内存缓存（用于图遍历）
        self._adj_list: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)  # node -> [(target, rel_type, direction)]
        self._rebuild_cache()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kg_entities (
                        entity_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT,
                        description TEXT,
                        properties TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kg_relations (
                        relation_id TEXT PRIMARY KEY,
                        from_entity TEXT NOT NULL,
                        to_entity TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        weight REAL DEFAULT 1.0,
                        properties TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kg_relation_types (
                        type_id TEXT PRIMARY KEY,
                        type_name TEXT NOT NULL,
                        description TEXT,
                        inverse_type TEXT,
                        symmetric INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kg_inference_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_name TEXT,
                        condition TEXT,
                        conclusion TEXT,
                        enabled INTEGER DEFAULT 1
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_rel_from ON kg_relations(from_entity)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_rel_to ON kg_relations(to_entity)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_ent_type ON kg_entities(type)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化知识图谱数据库失败: {e}")

    def _register_defaults(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 注册关系类型
                rel_types = [
                    ('RT-001', 'belongs_to', '属于', 'has_member', 0),
                    ('RT-002', 'supports', '支持', 'supported_by', 0),
                    ('RT-003', 'integrates_with', '集成于', 'integrates_with', 1),
                    ('RT-004', 'manages', '管理', 'managed_by', 0),
                    ('RT-005', 'developed_with', '使用开发', 'used_to_develop', 0),
                    ('RT-006', 'used_by', '被使用', 'uses', 0),
                    ('RT-007', 'related_to', '相关于', 'related_to', 1),
                ]
                for rt in rel_types:
                    cursor.execute('SELECT type_id FROM kg_relation_types WHERE type_id = ?', (rt[0],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO kg_relation_types
                            (type_id, type_name, description, inverse_type, symmetric)
                            VALUES (?, ?, ?, ?, ?)
                        ''', rt)

                # 注册实体
                for ent in DEFAULT_ENTITIES:
                    cursor.execute('SELECT entity_id FROM kg_entities WHERE entity_id = ?', (ent['entity_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO kg_entities
                            (entity_id, name, type, description, properties, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            ent['entity_id'], ent['name'], ent['type'], ent['description'],
                            json.dumps(ent['properties'], ensure_ascii=False),
                            datetime.now().isoformat(), datetime.now().isoformat()
                        ))

                # 注册关系
                for i, rel in enumerate(DEFAULT_RELATIONS):
                    rel_id = f"R-DEF-{i+1:03d}"
                    cursor.execute('SELECT relation_id FROM kg_relations WHERE relation_id = ?', (rel_id,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO kg_relations
                            (relation_id, from_entity, to_entity, relation_type, weight, created_at)
                            VALUES (?, ?, ?, ?, 1.0, ?)
                        ''', (rel_id, rel['from'], rel['to'], rel['type'], datetime.now().isoformat()))

                # 注册推理规则
                rules = [
                    ('IR-001', '传递性推理', 'A belongs_to B AND B belongs_to C', 'A belongs_to C', 0),
                    ('IR-002', '支持传递', 'A supports B AND B supports C', 'A supports C', 0),
                ]
                for rule in rules:
                    cursor.execute('SELECT rule_id FROM kg_inference_rules WHERE rule_id = ?', (rule[0],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO kg_inference_rules
                            (rule_id, rule_name, condition, conclusion, enabled)
                            VALUES (?, ?, ?, ?, ?)
                        ''', rule)

                conn.commit()
        except Exception as e:
            logger.error(f"注册默认知识图谱数据失败: {e}")

    def _rebuild_cache(self):
        """重建内存邻接表缓存"""
        self._adj_list.clear()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT from_entity, to_entity, relation_type, weight FROM kg_relations')
                for row in cursor.fetchall():
                    src, tgt, rtype, weight = row
                    self._adj_list[src].append((tgt, rtype, 'out'))
                    self._adj_list[tgt].append((src, rtype, 'in'))
        except Exception as e:
            logger.error(f"重建图谱缓存失败: {e}")

    # ========== 实体管理 ==========

    def add_entity(self, entity_id: str, name: str, entity_type: str = 'general',
                  description: str = '', properties: Optional[Dict] = None) -> Dict:
        """添加实体"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO kg_entities
                    (entity_id, name, type, description, properties, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entity_id, name, entity_type, description,
                    json.dumps(properties or {}, ensure_ascii=False),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            self._rebuild_cache()
            return {'success': True, 'entity_id': entity_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM kg_entities WHERE entity_id = ?', (entity_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'entity_id': row[0], 'name': row[1], 'type': row[2],
                    'description': row[3],
                    'properties': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5], 'updated_at': row[6]
                }
        except Exception:
            return None

    def find_entities(self, keyword: str = '', entity_type: str = None,
                     limit: int = 20) -> List[Dict]:
        """搜索实体"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                conditions = []
                params = []
                if keyword:
                    conditions.append('(name LIKE ? OR description LIKE ?)')
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                if entity_type:
                    conditions.append('type = ?')
                    params.append(entity_type)

                sql = 'SELECT entity_id, name, type, description FROM kg_entities'
                if conditions:
                    sql += ' WHERE ' + ' AND '.join(conditions)
                sql += ' ORDER BY name LIMIT ?'
                params.append(limit)
                cursor.execute(sql, params)
                return [
                    {
                        'entity_id': r[0], 'name': r[1], 'type': r[2],
                        'description': r[3]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def update_entity(self, entity_id: str, **kwargs) -> Dict:
        allowed = {'name', 'type', 'description', 'properties'}
        updates = []
        values = []
        for k, v in kwargs.items():
            if k in allowed:
                if k == 'properties':
                    v = json.dumps(v, ensure_ascii=False)
                updates.append(f'{k} = ?')
                values.append(v)
        if not updates:
            return {'success': False, 'error': '无可更新字段'}
        updates.append('updated_at = ?')
        values.append(datetime.now().isoformat())
        values.append(entity_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE kg_entities SET {", ".join(updates)} WHERE entity_id = ?', values)
                conn.commit()
                return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_entity(self, entity_id: str) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM kg_relations WHERE from_entity = ? OR to_entity = ?',
                              (entity_id, entity_id))
                cursor.execute('DELETE FROM kg_entities WHERE entity_id = ?', (entity_id,))
                conn.commit()
            self._rebuild_cache()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 关系管理 ==========

    def add_relation(self, from_entity: str, to_entity: str, relation_type: str,
                    weight: float = 1.0, properties: Optional[Dict] = None,
                    relation_id: Optional[str] = None) -> Dict:
        """添加关系"""
        # 校验实体存在
        if not self.get_entity(from_entity) or not self.get_entity(to_entity):
            return {'success': False, 'error': '实体不存在'}

        relation_id = relation_id or f"R-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO kg_relations
                    (relation_id, from_entity, to_entity, relation_type, weight, properties, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    relation_id, from_entity, to_entity, relation_type, weight,
                    json.dumps(properties or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
            self._rebuild_cache()
            return {'success': True, 'relation_id': relation_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_neighbors(self, entity_id: str, relation_type: str = None,
                     direction: str = 'both') -> List[Dict]:
        """查询实体邻居"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                results = []

                if direction in ('out', 'both'):
                    if relation_type:
                        cursor.execute('''
                            SELECT r.relation_id, r.to_entity, e.name, e.type, r.relation_type, r.weight, 'out'
                            FROM kg_relations r
                            JOIN kg_entities e ON r.to_entity = e.entity_id
                            WHERE r.from_entity = ? AND r.relation_type = ?
                        ''', (entity_id, relation_type))
                    else:
                        cursor.execute('''
                            SELECT r.relation_id, r.to_entity, e.name, e.type, r.relation_type, r.weight, 'out'
                            FROM kg_relations r
                            JOIN kg_entities e ON r.to_entity = e.entity_id
                            WHERE r.from_entity = ?
                        ''', (entity_id,))
                    for row in cursor.fetchall():
                        results.append({
                            'relation_id': row[0], 'entity_id': row[1],
                            'name': row[2], 'entity_type': row[3],
                            'relation_type': row[4], 'weight': row[5],
                            'direction': row[6]
                        })

                if direction in ('in', 'both'):
                    if relation_type:
                        cursor.execute('''
                            SELECT r.relation_id, r.from_entity, e.name, e.type, r.relation_type, r.weight, 'in'
                            FROM kg_relations r
                            JOIN kg_entities e ON r.from_entity = e.entity_id
                            WHERE r.to_entity = ? AND r.relation_type = ?
                        ''', (entity_id, relation_type))
                    else:
                        cursor.execute('''
                            SELECT r.relation_id, r.from_entity, e.name, e.type, r.relation_type, r.weight, 'in'
                            FROM kg_relations r
                            JOIN kg_entities e ON r.from_entity = e.entity_id
                            WHERE r.to_entity = ?
                        ''', (entity_id,))
                    for row in cursor.fetchall():
                        results.append({
                            'relation_id': row[0], 'entity_id': row[1],
                            'name': row[2], 'entity_type': row[3],
                            'relation_type': row[4], 'weight': row[5],
                            'direction': row[6]
                        })

                return results
        except Exception:
            return []

    def find_path(self, start: str, end: str, max_depth: int = 5,
                 relation_type: str = None) -> List[Dict]:
        """BFS 查找最短路径"""
        if start == end:
            return [{'path': [start], 'length': 0}]

        visited = {start}
        queue = deque([(start, [start])])
        paths = []

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue

            for neighbor, rtype, direction in self._adj_list.get(current, []):
                if relation_type and rtype != relation_type:
                    continue
                if neighbor in visited:
                    continue

                new_path = path + [neighbor]
                if neighbor == end:
                    paths.append({'path': new_path, 'length': len(new_path) - 1})
                    if len(paths) >= 3:  # 最多返回3条路径
                        return paths
                else:
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))

        return paths

    def get_subgraph(self, center_entity: str, depth: int = 2) -> Dict:
        """获取以某实体为中心的子图"""
        visited = set()
        entities = set()
        relations = []
        queue = deque([(center_entity, 0)])

        while queue:
            entity, level = queue.popleft()
            if entity in visited or level > depth:
                continue
            visited.add(entity)

            for neighbor, rtype, direction in self._adj_list.get(entity, []):
                if direction == 'out':
                    relations.append({'from': entity, 'to': neighbor, 'type': rtype})
                else:
                    relations.append({'from': neighbor, 'to': entity, 'type': rtype})
                entities.add(neighbor)
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))

        # 获取实体详情
        entity_details = []
        for eid in entities:
            ent = self.get_entity(eid)
            if ent:
                entity_details.append(ent)

        return {
            'center': center_entity,
            'depth': depth,
            'entities': entity_details,
            'relations': relations,
            'entity_count': len(entity_details),
            'relation_count': len(relations)
        }

    # ========== 知识抽取 ==========

    def extract_from_text(self, text: str) -> Dict:
        """从文本中抽取实体和关系（基于规则的简易版）"""
        extracted_entities = []
        extracted_relations = []

        # 抽取系统名（大写开头的系统名）
        sys_pattern = re.findall(r'\b([A-Z][A-Za-z0-9_-]{2,}(?:系统|平台|服务))', text)
        for match in sys_pattern:
            extracted_entities.append({
                'name': match,
                'type': 'system',
                'confidence': 0.7
            })

        # 抽取技术名词
        tech_kw = ['Python', 'Flask', 'SQLite', 'MySQL', 'Redis', 'Vue', 'React', 'Docker']
        for kw in tech_kw:
            if kw in text:
                extracted_entities.append({
                    'name': kw,
                    'type': 'technology',
                    'confidence': 0.9
                })

        # 抽取关系模式 "A使用B" "A属于B" "A支持B"
        rel_patterns = [
            (r'(\S+)(?:使用|基于)(\S+)', 'used_by'),
            (r'(\S+)(?:属于|隶属于)(\S+)', 'belongs_to'),
            (r'(\S+)(?:支持|支撑)(\S+)', 'supports'),
            (r'(\S+)(?:管理|维护)(\S+)', 'manages'),
        ]
        for pattern, rtype in rel_patterns:
            matches = re.findall(pattern, text)
            for a, b in matches:
                extracted_relations.append({
                    'from': a,
                    'to': b,
                    'type': rtype,
                    'confidence': 0.6
                })

        return {
            'entities': extracted_entities,
            'relations': extracted_relations,
            'entity_count': len(extracted_entities),
            'relation_count': len(extracted_relations)
        }

    # ========== 社区发现 ==========

    def detect_communities(self, method: str = 'label_propagation',
                          max_iter: int = 10) -> Dict:
        """社区发现（标签传播算法简化版）"""
        # 初始化：每个节点一个社区
        labels = {}
        nodes = list(self._adj_list.keys())
        for i, node in enumerate(nodes):
            labels[node] = i

        for _ in range(max_iter):
            changed = False
            random.shuffle(nodes)
            for node in nodes:
                if not self._adj_list[node]:
                    continue
                # 统计邻居标签
                label_count = defaultdict(int)
                for neighbor, _, _ in self._adj_list[node]:
                    if neighbor in labels:
                        label_count[labels[neighbor]] += 1
                if label_count:
                    # 选最频繁的标签
                    new_label = max(label_count, key=label_count.get)
                    if new_label != labels[node]:
                        labels[node] = new_label
                        changed = True
            if not changed:
                break

        # 按社区分组
        communities = defaultdict(list)
        for node, label in labels.items():
            communities[label].append(node)

        # 排序
        sorted_communities = sorted(communities.values(), key=len, reverse=True)
        result = []
        for i, members in enumerate(sorted_communities):
            # 获取成员名
            member_names = []
            for m in members[:10]:
                ent = self.get_entity(m)
                if ent:
                    member_names.append(ent['name'])
            result.append({
                'community_id': f'C-{i+1}',
                'size': len(members),
                'members': members,
                'member_names': member_names
            })

        return {
            'method': method,
            'community_count': len(result),
            'communities': result
        }

    # ========== 统计分析 ==========

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM kg_entities')
                entity_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM kg_relations')
                relation_count = cursor.fetchone()[0]
                cursor.execute('SELECT type, COUNT(*) FROM kg_entities GROUP BY type')
                type_dist = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT relation_type, COUNT(*) FROM kg_relations GROUP BY relation_type')
                rel_dist = {r[0]: r[1] for r in cursor.fetchall()}

                # 计算度数
                cursor.execute('SELECT from_entity, COUNT(*) FROM kg_relations GROUP BY from_entity')
                out_degrees = dict(cursor.fetchall())
                cursor.execute('SELECT to_entity, COUNT(*) FROM kg_relations GROUP BY to_entity')
                in_degrees = dict(cursor.fetchall())

                all_nodes = set(list(out_degrees.keys()) + list(in_degrees.keys()))
                if all_nodes:
                    degrees = [out_degrees.get(n, 0) + in_degrees.get(n, 0) for n in all_nodes]
                    avg_degree = sum(degrees) / len(degrees)
                    max_degree = max(degrees)
                else:
                    avg_degree = 0
                    max_degree = 0

                # 密度
                max_edges = entity_count * (entity_count - 1) if entity_count > 1 else 1
                density = relation_count / max_edges

                return {
                    'entity_count': entity_count,
                    'relation_count': relation_count,
                    'entity_type_distribution': type_dist,
                    'relation_type_distribution': rel_dist,
                    'avg_degree': round(avg_degree, 2),
                    'max_degree': max_degree,
                    'density': round(density, 6)
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    kg = AIKnowledgeGraph()
    stats = kg.get_statistics()
    print(f"知识图谱统计: {stats}")

    print("\n搜索实体 'AI':")
    results = kg.find_entities('AI')
    for r in results:
        print(f"  [{r['type']}] {r['name']} ({r['entity_id']})")

    print("\nMTSCOS系统的邻居:")
    neighbors = kg.get_neighbors('E-SYS-001', direction='both')
    for n in neighbors:
        print(f"  [{n['direction']}] {n['relation_type']} -> {n['name']}")

    print("\n最短路径 (AI模型管理 -> wuchenghao):")
    paths = kg.find_path('E-MOD-001', 'E-PER-001', max_depth=4)
    for p in paths:
        names = [kg.get_entity(eid)['name'] if kg.get_entity(eid) else eid for eid in p['path']]
        print(f"  路径长度 {p['length']}: {' → '.join(names)}")

    print("\n子图 (MTSCOS系统, depth=1):")
    subgraph = kg.get_subgraph('E-SYS-001', depth=1)
    print(f"  实体数: {subgraph['entity_count']}, 关系数: {subgraph['relation_count']}")

    print("\n社区发现:")
    communities = kg.detect_communities()
    print(f"  社区数: {communities['community_count']}")
    for c in communities['communities'][:3]:
        print(f"    社区 {c['community_id']} (大小 {c['size']}): {', '.join(c['member_names'][:5])}")

    print("\n文本抽取测试:")
    text = "MTSCOS系统使用Python和Flask开发，AI模型管理服务属于MTSCOS系统，wuchenghao管理MTSCOS系统"
    extracted = kg.extract_from_text(text)
    print(f"  抽取实体数: {extracted['entity_count']}")
    for e in extracted['entities']:
        print(f"    [{e['type']}] {e['name']} (置信度: {e['confidence']})")
    print(f"  抽取关系数: {extracted['relation_count']}")
    for r in extracted['relations']:
        print(f"    {r['from']} --[{r['type']}]--> {r['to']}")
