# -*- coding: utf-8 -*-
"""
知识图谱引擎
提供知识点关联、智能检索、知识推理、学习路径推荐等功能
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_graph_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KnowledgeGraphEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class KnowledgeGraphEngine:
    """知识图谱引擎 - 管理知识点之间的关联关系"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._knowledge_cache = {}
        self._relation_cache = {}
        self._init_database()
        self._load_subject_hierarchy()
        self._initialized = True
        logger.info("KnowledgeGraphEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_nodes (
                        node_id TEXT PRIMARY KEY,
                        subject TEXT NOT NULL,
                        grade TEXT,
                        knowledge_point TEXT NOT NULL,
                        category TEXT,
                        difficulty INTEGER DEFAULT 3,
                        importance REAL DEFAULT 0.5,
                        description TEXT,
                        prerequisites TEXT DEFAULT '[]',
                        dependents TEXT DEFAULT '[]',
                        tags TEXT DEFAULT '[]',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_node TEXT NOT NULL,
                        target_node TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        strength REAL DEFAULT 0.5,
                        direction TEXT DEFAULT 'undirected',
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source_node, target_node, relation_type)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_search_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        query TEXT,
                        result_count INTEGER,
                        search_time TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_user_paths (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        start_node TEXT,
                        target_node TEXT,
                        path_data TEXT,
                        total_steps INTEGER,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_node_subject ON knowledge_nodes(subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_node_grade ON knowledge_nodes(grade)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_relation_source ON knowledge_relations(source_node)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_kg_relation_target ON knowledge_relations(target_node)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化知识图谱数据库失败: {e}")

    def _load_subject_hierarchy(self):
        """加载各学科知识点层级结构"""
        self.subject_hierarchy = {
            '数学': {
                '小学': {
                    '一年级': ['数的认识', '加减法', '简单图形', '认识时间'],
                    '二年级': ['乘法口诀', '除法入门', '长度单位', '角的认识'],
                    '三年级': ['分数初步认识', '小数初步认识', '长方形周长', '面积'],
                    '四年级': ['四则运算', '运算定律', '三角形', '平行四边形'],
                    '五年级': ['小数乘除法', '简易方程', '长方体正方体', '分数加减法'],
                    '六年级': ['分数乘除法', '比和比例', '圆', '百分数', '圆柱圆锥']
                },
                '初中': {
                    '初一': ['有理数', '整式加减', '一元一次方程', '几何图形初步', '相交线与平行线'],
                    '初二': ['三角形', '全等三角形', '轴对称', '整式乘除', '分式', '二次根式', '勾股定理', '平行四边形'],
                    '初三': ['一元二次方程', '二次函数', '旋转', '圆', '概率初步', '相似三角形', '锐角三角函数']
                },
                '高中': {
                    '高一': ['集合', '函数概念', '指数函数', '对数函数', '幂函数', '三角函数', '平面向量', '三角恒等变换'],
                    '高二': ['解三角形', '数列', '不等式', '常用逻辑用语', '圆锥曲线', '空间向量', '导数及其应用'],
                    '高三': ['推理与证明', '复数', '计数原理', '概率统计', '随机变量', '统计案例']
                }
            },
            '语文': {
                '小学': {
                    '一年级': ['拼音', '识字', '简单阅读', '看图写话'],
                    '二年级': ['词语积累', '阅读理解', '日记写作', '古诗背诵'],
                    '三年级': ['记叙文', '作文入门', '文言文初步', '修辞手法'],
                    '四年级': ['写景作文', '状物作文', '现代诗', '古文启蒙'],
                    '五年级': ['散文阅读', '议论文入门', '小说初步', '古诗词鉴赏'],
                    '六年级': ['记叙文写作', '文言文阅读', '文学常识', '名著导读']
                },
                '初中': {
                    '初一': ['记叙文阅读', '散文阅读', '作文基础', '文言文', '古诗词'],
                    '初二': ['说明文阅读', '议论文阅读', '记叙文写作', '文言虚词', '名著阅读'],
                    '初三': ['小说阅读', '散文赏析', '议论文写作', '文言文综合', '中考作文']
                }
            },
            '英语': {
                '小学': {
                    '一年级': ['字母认识', '简单单词', '日常对话'],
                    '三年级': ['基础词汇', '一般现在时', '简单句型', '音标入门'],
                    '五年级': ['现在进行时', '一般过去时', '比较级', '阅读理解']
                },
                '初中': {
                    '初一': ['名词代词', '一般现在时', '现在进行时', '简单句', '基础词汇'],
                    '初二': ['一般过去时', '一般将来时', '现在完成时', '宾语从句', '比较级最高级'],
                    '初三': ['定语从句', '状语从句', '被动语态', '非谓语动词', '中考词汇']
                }
            },
            '物理': {
                '初中': {
                    '初二': ['机械运动', '声现象', '物态变化', '光现象', '透镜成像', '质量密度', '力', '运动和力', '压强', '浮力'],
                    '初三': ['功和机械能', '简单机械', '内能', '内能的利用', '电流电路', '电压电阻', '欧姆定律', '电功率', '生活用电', '电与磁']
                }
            },
            '化学': {
                '初中': {
                    '初三': ['走进化学世界', '我们周围的空气', '物质构成的奥秘', '自然界的水', '化学方程式', '碳和碳的氧化物', '燃料及其利用', '金属和金属材料', '溶液', '酸和碱', '盐 化肥', '化学与生活']
                }
            }
        }

    def add_knowledge_node(self, subject: str, knowledge_point: str, grade: str = None,
                           category: str = None, difficulty: int = 3, importance: float = 0.5,
                           description: str = None, tags: List[str] = None,
                           prerequisites: List[str] = None, dependents: List[str] = None) -> Dict[str, Any]:
        """添加知识点节点"""
        with self._lock:
            try:
                node_id = f"kg_{subject}_{grade}_{knowledge_point}_{int(time.time())}"
                tags_json = json.dumps(tags or [], ensure_ascii=False)
                prereq_json = json.dumps(prerequisites or [], ensure_ascii=False)
                depend_json = json.dumps(dependents or [], ensure_ascii=False)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_nodes
                        (node_id, subject, grade, knowledge_point, category, difficulty,
                         importance, description, prerequisites, dependents, tags, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (node_id, subject, grade, knowledge_point, category, difficulty,
                          importance, description or '', prereq_json, depend_json, tags_json,
                          datetime.now().isoformat()))
                    conn.commit()

                self._knowledge_cache.pop(node_id, None)
                return {'success': True, 'node_id': node_id, 'message': '知识点添加成功'}
            except Exception as e:
                logger.error(f"添加知识点失败: {e}")
                return {'success': False, 'error': str(e)}

    def add_relation(self, source_node: str, target_node: str, relation_type: str,
                     strength: float = 0.5, direction: str = 'undirected',
                     description: str = None) -> Dict[str, Any]:
        """添加知识点关联关系"""
        with self._lock:
            try:
                valid_types = ['prerequisite', 'related', 'part_of', 'similar', 'extends', 'opposite']
                if relation_type not in valid_types:
                    return {'success': False, 'message': f'无效的关联类型: {relation_type}'}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_relations
                        (source_node, target_node, relation_type, strength, direction, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (source_node, target_node, relation_type, strength, direction, description))
                    conn.commit()

                self._relation_cache.clear()
                return {'success': True, 'message': '关联关系添加成功'}
            except Exception as e:
                logger.error(f"添加关联关系失败: {e}")
                return {'success': False, 'error': str(e)}

    def search_knowledge(self, query: str, subject: str = None, grade: str = None,
                         limit: int = 20, user_id: str = None) -> Dict[str, Any]:
        """智能检索知识点"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    sql = '''
                        SELECT node_id, subject, grade, knowledge_point, category,
                               difficulty, importance, description, tags
                        FROM knowledge_nodes
                        WHERE (knowledge_point LIKE ? OR description LIKE ?)
                    '''
                    params = [f'%{query}%', f'%{query}%']

                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)
                    if grade:
                        sql += ' AND grade = ?'
                        params.append(grade)

                    sql += ' ORDER BY importance DESC, difficulty ASC LIMIT ?'
                    params.append(limit)

                    cursor.execute(sql, params)
                    rows = cursor.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            'node_id': row[0],
                            'subject': row[1],
                            'grade': row[2],
                            'knowledge_point': row[3],
                            'category': row[4],
                            'difficulty': row[5],
                            'importance': row[6],
                            'description': row[7],
                            'tags': json.loads(row[8]) if row[8] else [],
                            'relevance_score': self._calculate_relevance(query, row[3], row[7])
                        })

                    results.sort(key=lambda x: -x['relevance_score'])

                    # 记录搜索日志
                    if user_id:
                        cursor.execute('''
                            INSERT INTO knowledge_search_log (user_id, query, result_count)
                            VALUES (?, ?, ?)
                        ''', (user_id, query, len(results)))
                        conn.commit()

                return {
                    'success': True,
                    'query': query,
                    'total': len(results),
                    'results': results
                }
            except Exception as e:
                logger.error(f"搜索知识点失败: {e}")
                return {'success': False, 'error': str(e)}

    def _calculate_relevance(self, query: str, title: str, desc: str) -> float:
        """计算相关性分数"""
        score = 0.0
        query_lower = query.lower()
        title_lower = title.lower()
        desc_lower = desc.lower()

        if query_lower == title_lower:
            score += 10.0
        elif query_lower in title_lower:
            score += 5.0
        if query_lower in desc_lower:
            score += 2.0

        # 部分匹配
        query_words = query_lower.split()
        for word in query_words:
            if word in title_lower:
                score += 1.0
            if word in desc_lower:
                score += 0.5

        return min(score, 10.0)

    def get_related_knowledge(self, node_id: str, relation_type: str = None,
                              depth: int = 1) -> Dict[str, Any]:
        """获取关联知识点"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    # 获取节点基本信息
                    cursor.execute('''
                        SELECT node_id, subject, grade, knowledge_point, difficulty, importance
                        FROM knowledge_nodes WHERE node_id = ?
                    ''', (node_id,))
                    node = cursor.fetchone()
                    if not node:
                        return {'success': False, 'message': '知识点不存在'}

                    # 获取直接关联
                    sql = '''
                        SELECT kr.target_node, kn.knowledge_point, kn.subject, kn.grade,
                               kn.difficulty, kn.importance, kr.relation_type, kr.strength
                        FROM knowledge_relations kr
                        JOIN knowledge_nodes kn ON kr.target_node = kn.node_id
                        WHERE kr.source_node = ?
                    '''
                    params = [node_id]
                    if relation_type:
                        sql += ' AND kr.relation_type = ?'
                        params.append(relation_type)

                    cursor.execute(sql, params)
                    relations = cursor.fetchall()

                    related = []
                    for r in relations:
                        related.append({
                            'node_id': r[0],
                            'knowledge_point': r[1],
                            'subject': r[2],
                            'grade': r[3],
                            'difficulty': r[4],
                            'importance': r[5],
                            'relation_type': r[6],
                            'strength': r[7]
                        })

                    # 按关联强度排序
                    related.sort(key=lambda x: -x['strength'])

                return {
                    'success': True,
                    'node': {
                        'node_id': node[0],
                        'knowledge_point': node[3],
                        'subject': node[1],
                        'grade': node[2],
                        'difficulty': node[4],
                        'importance': node[5]
                    },
                    'related_count': len(related),
                    'related': related
                }
            except Exception as e:
                logger.error(f"获取关联知识点失败: {e}")
                return {'success': False, 'error': str(e)}

    def find_learning_path(self, start_node: str, target_node: str,
                           user_id: str = None) -> Dict[str, Any]:
        """知识推理 - 寻找从起点到目标的学习路径"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    # 验证节点存在
                    cursor.execute('SELECT node_id, knowledge_point FROM knowledge_nodes WHERE node_id IN (?, ?)',
                                   (start_node, target_node))
                    nodes = {row[0]: row[1] for row in cursor.fetchall()}
                    if start_node not in nodes:
                        return {'success': False, 'message': '起点知识点不存在'}
                    if target_node not in nodes:
                        return {'success': False, 'message': '目标知识点不存在'}

                    # BFS寻找最短路径
                    from collections import deque
                    visited = {start_node}
                    queue = deque([(start_node, [start_node])])
                    found_path = None
                    max_depth = 10
                    depth = 0

                    while queue and depth < max_depth:
                        current, path = queue.popleft()
                        if current == target_node:
                            found_path = path
                            break

                        cursor.execute('''
                            SELECT target_node FROM knowledge_relations
                            WHERE source_node = ? AND relation_type IN ('prerequisite', 'related', 'extends')
                            ORDER BY strength DESC LIMIT 10
                        ''', (current,))
                        neighbors = [r[0] for r in cursor.fetchall()]

                        for neighbor in neighbors:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append((neighbor, path + [neighbor]))

                        depth += 1

                    if not found_path:
                        return {
                            'success': True,
                            'path_found': False,
                            'message': '未找到明确学习路径，建议直接学习目标知识点',
                            'recommendation': f'建议先复习基础知识，再直接学习{nodes[target_node]}'
                        }

                    # 获取路径中每个节点的详情
                    path_details = []
                    total_difficulty = 0
                    for node_id in found_path:
                        cursor.execute('''
                            SELECT node_id, knowledge_point, subject, grade, difficulty, importance, description
                            FROM knowledge_nodes WHERE node_id = ?
                        ''', (node_id,))
                        detail = cursor.fetchone()
                        if detail:
                            path_details.append({
                                'node_id': detail[0],
                                'knowledge_point': detail[1],
                                'subject': detail[2],
                                'grade': detail[3],
                                'difficulty': detail[4],
                                'importance': detail[5],
                                'description': detail[6]
                            })
                            total_difficulty += detail[4]

                    path_data = {
                        'steps': path_details,
                        'total_steps': len(path_details),
                        'total_difficulty': total_difficulty,
                        'avg_difficulty': round(total_difficulty / max(len(path_details), 1), 1),
                        'estimated_time': f'{len(path_details) * 30}分钟'
                    }

                    # 保存用户学习路径
                    if user_id:
                        path_id = f"path_{user_id}_{int(time.time())}"
                        subject = path_details[0]['subject'] if path_details else None
                        cursor.execute('''
                            INSERT INTO knowledge_user_paths
                            (user_id, subject, start_node, target_node, path_data, total_steps)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_id, subject, start_node, target_node,
                              json.dumps(path_data, ensure_ascii=False), len(path_details)))
                        conn.commit()

                return {
                    'success': True,
                    'path_found': True,
                    'start_node': nodes[start_node],
                    'target_node': nodes[target_node],
                    'path': path_data
                }
            except Exception as e:
                logger.error(f"寻找学习路径失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_knowledge_tree(self, subject: str, grade: str = None) -> Dict[str, Any]:
        """获取学科知识树结构"""
        with self._lock:
            try:
                subject_data = self.subject_hierarchy.get(subject, {})
                if not subject_data:
                    return {'success': False, 'message': f'不支持的学科: {subject}'}

                # 如果指定了年级段
                if grade and grade in subject_data:
                    tree = {
                        'subject': subject,
                        'stage': grade,
                        'grades': subject_data[grade]
                    }
                else:
                    # 返回完整学科树
                    tree = {
                        'subject': subject,
                        'stages': list(subject_data.keys()),
                        'hierarchy': subject_data
                    }

                # 统计数据库中的知识点数量
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM knowledge_nodes WHERE subject = ?', (subject,))
                    db_count = cursor.fetchone()[0]
                    tree['database_nodes_count'] = db_count

                return {
                    'success': True,
                    'tree': tree
                }
            except Exception as e:
                logger.error(f"获取知识树失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM knowledge_nodes')
                total_nodes = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM knowledge_relations')
                total_relations = cursor.fetchone()[0]
                cursor.execute('SELECT subject, COUNT(*) FROM knowledge_nodes GROUP BY subject')
                by_subject = dict(cursor.fetchall())
                cursor.execute('SELECT relation_type, COUNT(*) FROM knowledge_relations GROUP BY relation_type')
                by_relation = dict(cursor.fetchall())
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM knowledge_search_log')
                search_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM knowledge_search_log')
                total_searches = cursor.fetchone()[0]

            return {
                'success': True,
                'total_nodes': total_nodes,
                'total_relations': total_relations,
                'by_subject': by_subject,
                'by_relation_type': by_relation,
                'search_users': search_users,
                'total_searches': total_searches,
                'supported_subjects': list(self.subject_hierarchy.keys())
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def init_default_knowledge(self, subject: str = None) -> Dict[str, Any]:
        """从层级结构初始化默认知识点"""
        with self._lock:
            try:
                added = 0
                relations_added = 0
                subjects = [subject] if subject else list(self.subject_hierarchy.keys())

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    for subj in subjects:
                        hierarchy = self.subject_hierarchy.get(subj, {})
                        prev_stage_kps = []

                        for stage, grades in hierarchy.items():
                            stage_kps = []
                            prev_grade_kps = []

                            for grade, kps in grades.items():
                                grade_kp_ids = []

                                for i, kp in enumerate(kps):
                                    node_id = f"kg_{subj}_{grade}_{kp.replace(' ', '_')}"
                                    # 检查是否已存在
                                    cursor.execute('SELECT node_id FROM knowledge_nodes WHERE node_id = ?', (node_id,))
                                    if cursor.fetchone():
                                        grade_kp_ids.append(node_id)
                                        continue

                                    difficulty = 2 + i % 4
                                    importance = 0.4 + (len(kps) - i) * 0.05
                                    importance = min(importance, 0.95)

                                    cursor.execute('''
                                        INSERT OR IGNORE INTO knowledge_nodes
                                        (node_id, subject, grade, knowledge_point, category, difficulty,
                                         importance, description, tags)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (node_id, subj, grade, kp, stage, difficulty,
                                          importance, f'{grade}{kp}知识点学习',
                                          json.dumps([subj, stage, grade], ensure_ascii=False)))
                                    added += 1
                                    grade_kp_ids.append(node_id)

                                # 同年级知识点之间建立关联
                                for j in range(len(grade_kp_ids)):
                                    for k in range(j + 1, len(grade_kp_ids)):
                                        cursor.execute('''
                                            INSERT OR IGNORE INTO knowledge_relations
                                            (source_node, target_node, relation_type, strength, direction)
                                            VALUES (?, ?, 'related', 0.6, 'undirected')
                                        ''', (grade_kp_ids[j], grade_kp_ids[k]))
                                        relations_added += 1

                                # 与上一年级建立先后关系
                                if prev_grade_kps:
                                    for prev_id in prev_grade_kps[:3]:
                                        for curr_id in grade_kp_ids[:3]:
                                            cursor.execute('''
                                                INSERT OR IGNORE INTO knowledge_relations
                                                (source_node, target_node, relation_type, strength, direction)
                                                VALUES (?, ?, 'prerequisite', 0.7, 'directed')
                                            ''', (prev_id, curr_id))
                                            relations_added += 1

                                prev_grade_kps = grade_kp_ids
                                stage_kps.extend(grade_kp_ids)

                            prev_stage_kps = stage_kps

                    conn.commit()

                return {
                    'success': True,
                    'nodes_added': added,
                    'relations_added': relations_added,
                    'message': f'成功添加 {added} 个知识点节点，{relations_added} 条关联关系'
                }
            except Exception as e:
                logger.error(f"初始化默认知识点失败: {e}")
                return {'success': False, 'error': str(e)}


knowledge_graph_engine = KnowledgeGraphEngine()
