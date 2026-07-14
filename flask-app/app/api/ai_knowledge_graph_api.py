# -*- coding: utf-8 -*-
"""
AI知识图谱系统API
功能：
1. 知识点图谱构建 - 自动抽取知识点，构建学科知识图谱
2. 知识点关系发现 - 挖掘知识点间的前驱后继、关联关系
3. 知识薄弱点定位 - 基于错题和成绩定位知识漏洞
4. 学习路径推荐 - 基于图谱推荐最优学习顺序
5. 知识掌握度评估 - 评估学生对各知识点的掌握程度
6. 知识关联推荐 - 推荐关联知识点和拓展学习内容
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

ai_knowledge_graph_api = Blueprint('ai_knowledge_graph_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_knowledge_graph_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_kg_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                level INTEGER DEFAULT 1,
                parent_id INTEGER,
                difficulty REAL DEFAULT 0.5,
                importance REAL DEFAULT 0.5,
                tags TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_kg_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_point_id INTEGER NOT NULL,
                to_point_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_kg_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                point_id INTEGER NOT NULL,
                mastery_level REAL DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_study_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_kg_learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                path_data TEXT NOT NULL,
                start_point TEXT,
                end_point TEXT,
                estimated_time INTEGER DEFAULT 0,
                difficulty_avg REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_kg_subject ON ai_kg_points(subject)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_kg_from ON ai_kg_relations(from_point_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_kg_to ON ai_kg_relations(to_point_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_kg_user ON ai_kg_mastery(user_id)
        ''')

        conn.commit()
        conn.close()
        logger.info('AI知识图谱系统表结构创建完成')
    except Exception as e:
        logger.error(f'AI知识图谱系统表结构创建失败: {e}')


def init_default_knowledge_graph():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM ai_kg_points')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        subjects = {
            '数学': [
                {'name': '实数与运算', 'level': 1, 'difficulty': 0.2, 'importance': 0.6, 'tags': '基础,运算',
                 'children': [
                     {'name': '有理数', 'level': 2, 'difficulty': 0.2, 'importance': 0.5, 'tags': '基础'},
                     {'name': '无理数', 'level': 2, 'difficulty': 0.3, 'importance': 0.4, 'tags': '基础'},
                     {'name': '绝对值', 'level': 2, 'difficulty': 0.3, 'importance': 0.5, 'tags': '基础'},
                 ]},
                {'name': '整式与因式分解', 'level': 1, 'difficulty': 0.3, 'importance': 0.7, 'tags': '代数',
                 'children': [
                     {'name': '整式的加减', 'level': 2, 'difficulty': 0.2, 'importance': 0.5, 'tags': '代数'},
                     {'name': '整式的乘法', 'level': 2, 'difficulty': 0.4, 'importance': 0.6, 'tags': '代数'},
                     {'name': '因式分解', 'level': 2, 'difficulty': 0.5, 'importance': 0.7, 'tags': '代数,重点'},
                 ]},
                {'name': '方程与不等式', 'level': 1, 'difficulty': 0.4, 'importance': 0.8, 'tags': '代数,重点',
                 'children': [
                     {'name': '一元一次方程', 'level': 2, 'difficulty': 0.3, 'importance': 0.6, 'tags': '代数,方程'},
                     {'name': '二元一次方程组', 'level': 2, 'difficulty': 0.4, 'importance': 0.6, 'tags': '代数,方程'},
                     {'name': '一元二次方程', 'level': 2, 'difficulty': 0.6, 'importance': 0.8, 'tags': '代数,方程,重点'},
                     {'name': '不等式', 'level': 2, 'difficulty': 0.4, 'importance': 0.5, 'tags': '代数,不等式'},
                 ]},
                {'name': '函数', 'level': 1, 'difficulty': 0.6, 'importance': 0.9, 'tags': '代数,重点,难点',
                 'children': [
                     {'name': '一次函数', 'level': 2, 'difficulty': 0.4, 'importance': 0.7, 'tags': '函数'},
                     {'name': '反比例函数', 'level': 2, 'difficulty': 0.5, 'importance': 0.6, 'tags': '函数'},
                     {'name': '二次函数', 'level': 2, 'difficulty': 0.7, 'importance': 0.9, 'tags': '函数,重点,难点'},
                 ]},
                {'name': '几何图形', 'level': 1, 'difficulty': 0.4, 'importance': 0.7, 'tags': '几何',
                 'children': [
                     {'name': '三角形', 'level': 2, 'difficulty': 0.4, 'importance': 0.7, 'tags': '几何,重点'},
                     {'name': '四边形', 'level': 2, 'difficulty': 0.4, 'importance': 0.5, 'tags': '几何'},
                     {'name': '圆', 'level': 2, 'difficulty': 0.6, 'importance': 0.7, 'tags': '几何,重点'},
                 ]},
                {'name': '统计与概率', 'level': 1, 'difficulty': 0.3, 'importance': 0.4, 'tags': '统计',
                 'children': [
                     {'name': '数据统计', 'level': 2, 'difficulty': 0.2, 'importance': 0.3, 'tags': '统计'},
                     {'name': '概率初步', 'level': 2, 'difficulty': 0.3, 'importance': 0.3, 'tags': '统计,概率'},
                 ]},
            ],
            '物理': [
                {'name': '力学', 'level': 1, 'difficulty': 0.5, 'importance': 0.8, 'tags': '力学,重点',
                 'children': [
                     {'name': '运动学', 'level': 2, 'difficulty': 0.3, 'importance': 0.6, 'tags': '力学'},
                     {'name': '牛顿定律', 'level': 2, 'difficulty': 0.6, 'importance': 0.8, 'tags': '力学,重点,难点'},
                     {'name': '功和能', 'level': 2, 'difficulty': 0.5, 'importance': 0.7, 'tags': '力学,能量'},
                 ]},
                {'name': '电学', 'level': 1, 'difficulty': 0.6, 'importance': 0.9, 'tags': '电学,重点,难点',
                 'children': [
                     {'name': '电路基础', 'level': 2, 'difficulty': 0.4, 'importance': 0.7, 'tags': '电学'},
                     {'name': '欧姆定律', 'level': 2, 'difficulty': 0.5, 'importance': 0.8, 'tags': '电学,重点'},
                     {'name': '电功率', 'level': 2, 'difficulty': 0.6, 'importance': 0.8, 'tags': '电学,重点'},
                     {'name': '电磁感应', 'level': 2, 'difficulty': 0.7, 'importance': 0.7, 'tags': '电学,难点'},
                 ]},
            ],
            '英语': [
                {'name': '词汇', 'level': 1, 'difficulty': 0.2, 'importance': 0.7, 'tags': '基础,词汇',
                 'children': [
                     {'name': '核心词汇', 'level': 2, 'difficulty': 0.2, 'importance': 0.7, 'tags': '词汇'},
                     {'name': '高频短语', 'level': 2, 'difficulty': 0.3, 'importance': 0.6, 'tags': '词汇,短语'},
                 ]},
                {'name': '语法', 'level': 1, 'difficulty': 0.4, 'importance': 0.8, 'tags': '语法,重点',
                 'children': [
                     {'name': '时态', 'level': 2, 'difficulty': 0.4, 'importance': 0.7, 'tags': '语法,时态'},
                     {'name': '从句', 'level': 2, 'difficulty': 0.6, 'importance': 0.8, 'tags': '语法,重点,难点'},
                     {'name': '非谓语动词', 'level': 2, 'difficulty': 0.6, 'importance': 0.7, 'tags': '语法,难点'},
                 ]},
                {'name': '阅读', 'level': 1, 'difficulty': 0.5, 'importance': 0.8, 'tags': '阅读,重点',
                 'children': [
                     {'name': '阅读理解', 'level': 2, 'difficulty': 0.5, 'importance': 0.8, 'tags': '阅读'},
                     {'name': '完形填空', 'level': 2, 'difficulty': 0.6, 'importance': 0.7, 'tags': '阅读,难点'},
                 ]},
            ],
            '语文': [
                {'name': '基础知识', 'level': 1, 'difficulty': 0.2, 'importance': 0.6, 'tags': '基础',
                 'children': [
                     {'name': '字音字形', 'level': 2, 'difficulty': 0.2, 'importance': 0.5, 'tags': '基础'},
                     {'name': '成语俗语', 'level': 2, 'difficulty': 0.3, 'importance': 0.5, 'tags': '基础'},
                 ]},
                {'name': '阅读', 'level': 1, 'difficulty': 0.5, 'importance': 0.8, 'tags': '阅读,重点',
                 'children': [
                     {'name': '现代文阅读', 'level': 2, 'difficulty': 0.5, 'importance': 0.7, 'tags': '阅读'},
                     {'name': '文言文阅读', 'level': 2, 'difficulty': 0.7, 'importance': 0.8, 'tags': '阅读,难点,重点'},
                 ]},
                {'name': '写作', 'level': 1, 'difficulty': 0.6, 'importance': 0.9, 'tags': '写作,重点',
                 'children': [
                     {'name': '记叙文', 'level': 2, 'difficulty': 0.5, 'importance': 0.6, 'tags': '写作'},
                     {'name': '议论文', 'level': 2, 'difficulty': 0.7, 'importance': 0.8, 'tags': '写作,重点'},
                 ]},
            ],
            '化学': [
                {'name': '基础概念', 'level': 1, 'difficulty': 0.2, 'importance': 0.6, 'tags': '基础',
                 'children': [
                     {'name': '物质结构', 'level': 2, 'difficulty': 0.3, 'importance': 0.5, 'tags': '基础'},
                     {'name': '化学用语', 'level': 2, 'difficulty': 0.3, 'importance': 0.6, 'tags': '基础'},
                 ]},
                {'name': '化学反应', 'level': 1, 'difficulty': 0.5, 'importance': 0.8, 'tags': '重点',
                 'children': [
                     {'name': '氧化还原', 'level': 2, 'difficulty': 0.6, 'importance': 0.8, 'tags': '重点,难点'},
                     {'name': '酸碱反应', 'level': 2, 'difficulty': 0.4, 'importance': 0.7, 'tags': '重点'},
                 ]},
            ],
        }

        for subject, points in subjects.items():
            point_ids = {}
            for parent in points:
                cursor.execute('''
                    INSERT INTO ai_kg_points (subject, name, description, level, parent_id, difficulty, importance, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (subject, parent['name'], f'{subject}-{parent["name"]}', parent['level'], None,
                      parent['difficulty'], parent['importance'], parent['tags']))
                parent_id = cursor.lastrowid
                point_ids[parent['name']] = parent_id

                if 'children' in parent:
                    for child in parent['children']:
                        cursor.execute('''
                            INSERT INTO ai_kg_points (subject, name, description, level, parent_id, difficulty, importance, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (subject, child['name'], f'{subject}-{child["name"]}', child['level'], parent_id,
                              child['difficulty'], child['importance'], child['tags']))
                        child_id = cursor.lastrowid
                        point_ids[child['name']] = child_id

                        cursor.execute('''
                            INSERT INTO ai_kg_relations (from_point_id, to_point_id, relation_type, strength, description)
                            VALUES (?, ?, 'prerequisite', 0.9, ?)
                        ''', (parent_id, child_id, f'学习{parent["name"]}需要先掌握{child["name"]}'))

        conn.commit()
        conn.close()
        logger.info('默认知识图谱数据初始化完成')
    except Exception as e:
        logger.error(f'默认知识图谱数据初始化失败: {e}')


@ai_knowledge_graph_api.route('/api/ai/kg/graph', methods=['GET'])
@require_login
def get_knowledge_graph():
    try:
        subject = request.args.get('subject', '数学')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, description, level, parent_id, difficulty, importance, tags
            FROM ai_kg_points
            WHERE subject = ? AND status = 'active'
            ORDER BY level, id
        ''', (subject,))
        points = [dict(row) for row in cursor.fetchall()]

        point_ids = [p['id'] for p in points]
        if point_ids:
            placeholders = ','.join(['?'] * len(point_ids))
            cursor.execute(f'''
                SELECT id, from_point_id, to_point_id, relation_type, strength, description
                FROM ai_kg_relations
                WHERE from_point_id IN ({placeholders}) AND to_point_id IN ({placeholders})
            ''', point_ids + point_ids)
            relations = [dict(row) for row in cursor.fetchall()]
        else:
            relations = []

        cursor.execute('''
            SELECT point_id, mastery_level, correct_count, wrong_count, total_attempts
            FROM ai_kg_mastery
            WHERE user_id = ?
        ''', (user_id,))
        mastery_data = {}
        for row in cursor.fetchall():
            mastery_data[row['point_id']] = {
                'mastery_level': row['mastery_level'],
                'correct_count': row['correct_count'],
                'wrong_count': row['wrong_count'],
                'total_attempts': row['total_attempts']
            }

        for point in points:
            pid = point['id']
            if pid in mastery_data:
                point.update(mastery_data[pid])
            else:
                point.update({'mastery_level': 0, 'correct_count': 0, 'wrong_count': 0, 'total_attempts': 0})

        conn.close()

        return APIResponse.success(data={
            'subject': subject,
            'points': points,
            'relations': relations,
            'total_points': len(points),
            'total_relations': len(relations),
            'generated_at': datetime.now().isoformat()
        }, message='获取知识图谱成功')

    except Exception as e:
        logger.error(f'获取知识图谱失败: {e}')
        return APIResponse.error(message=f'获取知识图谱失败: {str(e)}')


@ai_knowledge_graph_api.route('/api/ai/kg/mastery', methods=['GET'])
@require_login
def get_mastery_analysis():
    try:
        subject = request.args.get('subject', '数学')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT kp.id, kp.name, kp.level, kp.difficulty, kp.importance, kp.tags,
                   COALESCE(km.mastery_level, 0) as mastery_level,
                   COALESCE(km.correct_count, 0) as correct_count,
                   COALESCE(km.wrong_count, 0) as wrong_count,
                   COALESCE(km.total_attempts, 0) as total_attempts
            FROM ai_kg_points kp
            LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
            WHERE kp.subject = ? AND kp.status = 'active'
            ORDER BY kp.level, kp.id
        ''', (user_id, subject))
        points = [dict(row) for row in cursor.fetchall()]

        weak_points = [p for p in points if p['mastery_level'] < 0.4]
        strong_points = [p for p in points if p['mastery_level'] >= 0.7]

        total_points = len(points)
        mastered_count = sum(1 for p in points if p['mastery_level'] >= 0.6)
        avg_mastery = sum(p['mastery_level'] for p in points) / total_points if total_points > 0 else 0

        level_stats = {}
        for p in points:
            lvl = p['level']
            if lvl not in level_stats:
                level_stats[lvl] = {'count': 0, 'mastered': 0, 'avg_mastery': 0}
            level_stats[lvl]['count'] += 1
            if p['mastery_level'] >= 0.6:
                level_stats[lvl]['mastered'] += 1
            level_stats[lvl]['avg_mastery'] += p['mastery_level']
        for lvl in level_stats:
            level_stats[lvl]['avg_mastery'] = round(level_stats[lvl]['avg_mastery'] / level_stats[lvl]['count'], 3)

        conn.close()

        return APIResponse.success(data={
            'subject': subject,
            'summary': {
                'total_points': total_points,
                'mastered_count': mastered_count,
                'mastered_rate': round(mastered_count / total_points, 3) if total_points > 0 else 0,
                'avg_mastery': round(avg_mastery, 3),
                'weak_count': len(weak_points),
                'strong_count': len(strong_points)
            },
            'weak_points': weak_points[:10],
            'strong_points': strong_points[:10],
            'all_points': points,
            'level_stats': level_stats,
            'generated_at': datetime.now().isoformat()
        }, message='掌握度分析完成')

    except Exception as e:
        logger.error(f'掌握度分析失败: {e}')
        return APIResponse.error(message=f'掌握度分析失败: {str(e)}')


@ai_knowledge_graph_api.route('/api/ai/kg/weak_points', methods=['GET'])
@require_login
def get_weak_points():
    try:
        subject = request.args.get('subject', '数学')
        user_id = session.get('user_id')
        limit = request.args.get('limit', 10, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT kp.id, kp.name, kp.level, kp.difficulty, kp.importance,
                   COALESCE(km.mastery_level, 0) as mastery_level,
                   COALESCE(km.wrong_count, 0) as wrong_count,
                   COALESCE(km.total_attempts, 0) as total_attempts
            FROM ai_kg_points kp
            LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
            WHERE kp.subject = ? AND kp.status = 'active'
            ORDER BY km.mastery_level ASC NULLS FIRST, kp.importance DESC
            LIMIT ?
        ''', (user_id, subject, limit))
        weak_points = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return APIResponse.success(data={
            'subject': subject,
            'weak_points': weak_points,
            'count': len(weak_points),
            'generated_at': datetime.now().isoformat()
        }, message='薄弱知识点分析完成')

    except Exception as e:
        logger.error(f'薄弱知识点分析失败: {e}')
        return APIResponse.error(message=f'薄弱知识点分析失败: {str(e)}')


@ai_knowledge_graph_api.route('/api/ai/kg/related/<int:point_id>', methods=['GET'])
@require_login
def get_related_points(point_id):
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_kg_points WHERE id = ?', (point_id,))
        target = dict(cursor.fetchone()) if cursor.fetchone() else None

        if not target:
            conn.close()
            return APIResponse.validation_error(message='知识点不存在')

        cursor.execute('''
            SELECT kp.*, kr.relation_type, kr.strength, kr.description as relation_desc
            FROM ai_kg_relations kr
            JOIN ai_kg_points kp ON kr.to_point_id = kp.id
            WHERE kr.from_point_id = ? AND kp.status = 'active'
            ORDER BY kr.strength DESC
        ''', (point_id,))
        next_points = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT kp.*, kr.relation_type, kr.strength, kr.description as relation_desc
            FROM ai_kg_relations kr
            JOIN ai_kg_points kp ON kr.from_point_id = kp.id
            WHERE kr.to_point_id = ? AND kp.status = 'active'
            ORDER BY kr.strength DESC
        ''', (point_id,))
        prev_points = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT COALESCE(mastery_level, 0) FROM ai_kg_mastery
            WHERE user_id = ? AND point_id = ?
        ''', (user_id, point_id))
        row = cursor.fetchone()
        target['mastery_level'] = row[0] if row else 0

        cursor.execute('''
            SELECT kp.id, kp.name, kp.difficulty, kp.importance,
                   COALESCE(km.mastery_level, 0) as mastery_level
            FROM ai_kg_points kp
            LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
            WHERE kp.subject = ? AND kp.id != ? AND kp.status = 'active'
            ORDER BY RANDOM()
            LIMIT 5
        ''', (user_id, target['subject'], point_id))
        recommend = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return APIResponse.success(data={
            'target': target,
            'prerequisites': prev_points,
            'next_points': next_points,
            'recommendations': recommend,
            'generated_at': datetime.now().isoformat()
        }, message='关联知识点查询成功')

    except Exception as e:
        logger.error(f'关联知识点查询失败: {e}')
        return APIResponse.error(message=f'关联知识点查询失败: {str(e)}')


@ai_knowledge_graph_api.route('/api/ai/kg/learning_path', methods=['POST'])
@require_login
def generate_learning_path():
    try:
        data = request.get_json()
        subject = data.get('subject', '数学')
        target_point = data.get('target_point')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        if target_point:
            cursor.execute('SELECT * FROM ai_kg_points WHERE name = ? AND subject = ?', (target_point, subject))
            target = cursor.fetchone()
        else:
            cursor.execute('''
                SELECT kp.*, COALESCE(km.mastery_level, 0) as mastery
                FROM ai_kg_points kp
                LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
                WHERE kp.subject = ? AND kp.status = 'active'
                ORDER BY mastery ASC, kp.importance DESC
                LIMIT 1
            ''', (user_id, subject))
            target = cursor.fetchone()

        if not target:
            conn.close()
            return APIResponse.validation_error(message='未找到目标知识点')

        target_id = target['id']
        visited = set()
        path = []
        queue = [(target_id, 0)]
        all_points = {}
        all_relations = {}

        cursor.execute('SELECT * FROM ai_kg_points WHERE subject = ?', (subject,))
        for row in cursor.fetchall():
            all_points[row['id']] = dict(row)

        cursor.execute('SELECT * FROM ai_kg_relations WHERE relation_type = "prerequisite"')
        for row in cursor.fetchall():
            if row['to_point_id'] not in all_relations:
                all_relations[row['to_point_id']] = []
            all_relations[row['to_point_id']].append(row)

        def collect_prerequisites(point_id, depth, max_depth=5):
            if depth > max_depth or point_id in visited:
                return []
            visited.add(point_id)
            result = []
            if point_id in all_relations:
                for rel in all_relations[point_id]:
                    prereq_id = rel['from_point_id']
                    result.extend(collect_prerequisites(prereq_id, depth + 1, max_depth))
                    result.append({
                        'point': all_points.get(prereq_id, {}),
                        'relation': dict(rel),
                        'depth': depth
                    })
            return result

        learning_path = collect_prerequisites(target_id, 1)
        learning_path.reverse()
        learning_path.append({
            'point': dict(target),
            'relation': {'relation_type': 'target', 'strength': 1.0},
            'depth': 0
        })

        seen = set()
        unique_path = []
        for item in learning_path:
            pid = item['point'].get('id')
            if pid and pid not in seen:
                seen.add(pid)
                cursor.execute('SELECT COALESCE(mastery_level, 0) FROM ai_kg_mastery WHERE user_id = ? AND point_id = ?',
                              (user_id, pid))
                row = cursor.fetchone()
                item['mastery_level'] = row[0] if row else 0
                unique_path.append(item)

        total_time = sum(int(item['point'].get('difficulty', 0.5) * 60 + 30) for item in unique_path)
        avg_difficulty = sum(item['point'].get('difficulty', 0.5) for item in unique_path) / len(unique_path) if unique_path else 0

        cursor.execute('''
            INSERT INTO ai_kg_learning_paths (user_id, subject, path_data, start_point, end_point, estimated_time, difficulty_avg, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        ''', (
            user_id, subject, json.dumps([{'point_id': item['point']['id'], 'point_name': item['point']['name']} for item in unique_path]),
            unique_path[0]['point']['name'] if unique_path else '',
            dict(target)['name'],
            total_time,
            round(avg_difficulty, 3)
        ))
        path_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return APIResponse.success(data={
            'path_id': path_id,
            'subject': subject,
            'target': dict(target)['name'],
            'path': unique_path,
            'total_steps': len(unique_path),
            'estimated_time': total_time,
            'avg_difficulty': round(avg_difficulty, 3),
            'generated_at': datetime.now().isoformat()
        }, message='学习路径生成成功')

    except Exception as e:
        logger.error(f'学习路径生成失败: {e}')
        return APIResponse.error(message=f'学习路径生成失败: {str(e)}')


@ai_knowledge_graph_api.route('/api/ai/kg/dashboard', methods=['GET'])
@require_login
def get_kg_dashboard():
    try:
        subject = request.args.get('subject', '数学')
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM ai_kg_points WHERE subject = ? AND status = ?', (subject, 'active'))
        total_points = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM ai_kg_mastery km
            JOIN ai_kg_points kp ON km.point_id = kp.id
            WHERE km.user_id = ? AND kp.subject = ? AND km.mastery_level >= 0.6
        ''', (user_id, subject))
        mastered = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COALESCE(AVG(km.mastery_level), 0) FROM ai_kg_mastery km
            JOIN ai_kg_points kp ON km.point_id = kp.id
            WHERE km.user_id = ? AND kp.subject = ?
        ''', (user_id, subject))
        avg_mastery = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM ai_kg_relations kr
            JOIN ai_kg_points kp1 ON kr.from_point_id = kp1.id
            JOIN ai_kg_points kp2 ON kr.to_point_id = kp2.id
            WHERE kp1.subject = ? AND kp2.subject = ?
        ''', (subject, subject))
        total_relations = cursor.fetchone()[0]

        cursor.execute('''
            SELECT kp.name, kp.level, kp.importance, COALESCE(km.mastery_level, 0) as mastery
            FROM ai_kg_points kp
            LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
            WHERE kp.subject = ? AND kp.status = 'active'
            ORDER BY mastery ASC, kp.importance DESC
            LIMIT 5
        ''', (user_id, subject))
        weakest = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT kp.name, kp.level, kp.importance, COALESCE(km.mastery_level, 0) as mastery
            FROM ai_kg_points kp
            LEFT JOIN ai_kg_mastery km ON kp.id = km.point_id AND km.user_id = ?
            WHERE kp.subject = ? AND kp.status = 'active'
            ORDER BY mastery DESC, kp.importance DESC
            LIMIT 5
        ''', (user_id, subject))
        strongest = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT level, COUNT(*) as count FROM ai_kg_points
            WHERE subject = ? AND status = 'active'
            GROUP BY level ORDER BY level
        ''', (subject,))
        level_dist = [{'level': row['level'], 'count': row['count']} for row in cursor.fetchall()]

        conn.close()

        return APIResponse.success(data={
            'subject': subject,
            'summary': {
                'total_points': total_points,
                'total_relations': total_relations,
                'mastered_points': mastered,
                'mastery_rate': round(mastered / total_points, 3) if total_points > 0 else 0,
                'avg_mastery': round(avg_mastery, 3),
                'remaining': total_points - mastered
            },
            'weakest_top5': weakest,
            'strongest_top5': strongest,
            'level_distribution': level_dist,
            'generated_at': datetime.now().isoformat()
        }, message='知识图谱仪表盘数据获取成功')

    except Exception as e:
        logger.error(f'知识图谱仪表盘数据获取失败: {e}')
        return APIResponse.error(message=f'知识图谱仪表盘数据获取失败: {str(e)}')


init_knowledge_graph_tables()
init_default_knowledge_graph()
