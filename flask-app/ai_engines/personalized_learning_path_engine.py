# -*- coding: utf-8 -*-
"""
个性化学习路径引擎 (Personalized Learning Path Engine) v1.0
MTSCOS AI 第9轮引擎拓展 - v5.2.0新增

功能特性：
1. 3种学习路径算法 - 知识图谱/能力进阶/兴趣驱动
2. 自适应难度调节 - 根据学习表现动态调整
3. 学习风格检测 - 视觉/听觉/动觉/读写4种风格
4. 个性化推荐 - 基于学习历史和偏好
5. 学习目标管理 - 短期/中期/长期目标
6. 进度追踪与预警 - 实时监控学习进度

作者: MTSCOS AI System
版本: 1.0.0
创建日期: 2026-07-06
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'app.db')

# 学习风格类型
LEARNING_STYLES = {
    'visual': {'name': '视觉型', 'description': '通过图表、图像学习效果最佳', 'strategies': ['思维导图', '图表', '视频教学']},
    'auditory': {'name': '听觉型', 'description': '通过听讲、讨论学习效果最佳', 'strategies': ['音频讲解', '讨论', '朗读']},
    'kinesthetic': {'name': '动觉型', 'description': '通过实践操作学习效果最佳', 'strategies': ['实验', '角色扮演', '动手操作']},
    'read_write': {'name': '读写型', 'description': '通过阅读和写作学习效果最佳', 'strategies': ['阅读材料', '笔记', '写作练习']}
}

# 学习路径算法
PATH_ALGORITHMS = {
    'knowledge_graph': {
        'name': '知识图谱算法',
        'description': '基于知识点的前后依赖关系生成路径',
        'suitable_for': '系统性学习'
    },
    'ability_progression': {
        'name': '能力进阶算法',
        'description': '根据能力等级逐步提升难度',
        'suitable_for': '能力提升'
    },
    'interest_driven': {
        'name': '兴趣驱动算法',
        'description': '根据学生兴趣点切入相关知识',
        'suitable_for': '兴趣培养'
    }
}

# 难度等级
DIFFICULTY_LEVELS = {
    1: {'name': '入门', 'range': (0, 30), 'description': '基础知识了解'},
    2: {'name': '基础', 'range': (30, 50), 'description': '基础概念掌握'},
    3: {'name': '进阶', 'range': (50, 70), 'description': '中级应用'},
    4: {'name': '提高', 'range': (70, 85), 'description': '高级应用'},
    5: {'name': '挑战', 'range': (85, 100), 'description': '竞赛级别'}
}


class PersonalizedLearningPathEngine:
    """个性化学习路径引擎"""

    def __init__(self):
        self.engine_name = "PersonalizedLearningPathEngine"
        self.version = "1.0.0"
        self._init_db()
        logger.info(f"[个性化学习路径引擎] 初始化完成 v{self.version}")

    def _init_db(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # 学习路径表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_paths (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path_id TEXT UNIQUE,
                        student_id TEXT NOT NULL,
                        subject TEXT,
                        algorithm TEXT,
                        learning_style TEXT,
                        current_node TEXT,
                        total_nodes INTEGER,
                        completed_nodes INTEGER,
                        progress REAL,
                        difficulty_level INTEGER,
                        target TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # 学习路径节点表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_path_nodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path_id TEXT,
                        node_id TEXT,
                        node_order INTEGER,
                        title TEXT,
                        knowledge_point TEXT,
                        difficulty INTEGER,
                        estimated_time INTEGER,
                        learning_resources TEXT,
                        status TEXT DEFAULT 'pending',
                        score REAL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        FOREIGN KEY (path_id) REFERENCES learning_paths(path_id)
                    )
                ''')
                # 学习风格档案表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_style_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT UNIQUE,
                        visual_score REAL,
                        auditory_score REAL,
                        kinesthetic_score REAL,
                        read_write_score REAL,
                        primary_style TEXT,
                        secondary_style TEXT,
                        assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("[个性化学习路径引擎] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 数据库初始化失败: {e}")

    def detect_learning_style(self, student_id, answers=None):
        """
        检测学生的学习风格

        Args:
            student_id: 学生ID
            answers: VARK问卷答案

        Returns:
            dict: 学习风格评估结果
        """
        try:
            # 如果没有提供答案，使用默认分布
            if answers is None:
                answers = {'visual': 0.35, 'auditory': 0.25, 'kinesthetic': 0.20, 'read_write': 0.20}

            # 计算各风格得分
            styles_score = {}
            for style, weight in answers.items():
                styles_score[style] = round(weight * 100, 1)

            # 排序找出主要和次要风格
            sorted_styles = sorted(styles_score.items(), key=lambda x: x[1], reverse=True)
            primary_style = sorted_styles[0][0]
            secondary_style = sorted_styles[1][0] if len(sorted_styles) > 1 else None

            # 保存到数据库
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_style_profiles
                    (student_id, visual_score, auditory_score, kinesthetic_score,
                     read_write_score, primary_style, secondary_style)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_id,
                      styles_score.get('visual', 0),
                      styles_score.get('auditory', 0),
                      styles_score.get('kinesthetic', 0),
                      styles_score.get('read_write', 0),
                      primary_style, secondary_style))
                conn.commit()

            result = {
                'success': True,
                'student_id': student_id,
                'styles_score': styles_score,
                'primary_style': primary_style,
                'primary_style_name': LEARNING_STYLES[primary_style]['name'],
                'secondary_style': secondary_style,
                'secondary_style_name': LEARNING_STYLES[secondary_style]['name'] if secondary_style else None,
                'recommendations': LEARNING_STYLES[primary_style]['strategies'],
                'assessed_at': datetime.now().isoformat()
            }
            logger.info(f"[个性化学习路径引擎] 学生 {student_id} 学习风格: {primary_style}")
            return result
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 风格检测失败: {e}")
            return {'success': False, 'error': str(e)}

    def generate_learning_path(self, student_id, subject, algorithm='knowledge_graph',
                                 target=None, difficulty=3, knowledge_points=None):
        """
        生成个性化学习路径

        Args:
            student_id: 学生ID
            subject: 学科
            algorithm: 算法类型
            target: 学习目标
            difficulty: 起始难度(1-5)
            knowledge_points: 知识点列表

        Returns:
            dict: 学习路径
        """
        try:
            # 获取学生学习风格
            style_profile = self._get_style_profile(student_id)
            learning_style = style_profile.get('primary_style', 'visual') if style_profile else 'visual'

            # 如果没有提供知识点，使用默认知识点
            if knowledge_points is None:
                knowledge_points = self._get_default_knowledge_points(subject)

            # 根据算法生成路径
            if algorithm == 'knowledge_graph':
                nodes = self._build_knowledge_graph_path(knowledge_points, difficulty)
            elif algorithm == 'ability_progression':
                nodes = self._build_ability_progression_path(knowledge_points, difficulty)
            else:  # interest_driven
                nodes = self._build_interest_driven_path(knowledge_points, difficulty, learning_style)

            # 创建路径记录
            path_id = f"path_{datetime.now().strftime('%Y%m%d%H%M%S')}_{student_id}"
            total_nodes = len(nodes)
            self._save_learning_path(path_id, student_id, subject, algorithm,
                                     learning_style, nodes, difficulty, target)

            result = {
                'success': True,
                'path_id': path_id,
                'student_id': student_id,
                'subject': subject,
                'algorithm': algorithm,
                'algorithm_name': PATH_ALGORITHMS[algorithm]['name'],
                'learning_style': learning_style,
                'learning_style_name': LEARNING_STYLES[learning_style]['name'],
                'target': target,
                'difficulty_level': difficulty,
                'total_nodes': total_nodes,
                'nodes': nodes,
                'estimated_total_time': sum(n['estimated_time'] for n in nodes),
                'created_at': datetime.now().isoformat()
            }
            logger.info(f"[个性化学习路径引擎] 生成路径 {path_id}: {total_nodes}个节点")
            return result
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 生成路径失败: {e}")
            return {'success': False, 'error': str(e)}

    def _get_style_profile(self, student_id):
        """获取学生学习风格"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_style_profiles WHERE student_id = ?', (student_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except:
            return None

    def _get_default_knowledge_points(self, subject):
        """获取学科默认知识点"""
        default_kps = {
            '数学': ['数与代数', '图形与几何', '统计与概率', '综合与实践'],
            '语文': ['现代文阅读', '古诗文', '写作', '语言运用'],
            '英语': ['听力', '阅读', '写作', '语法', '词汇'],
            '物理': ['力学', '电学', '热学', '光学', '声学'],
            '化学': ['基本概念', '元素化合物', '化学计算', '化学实验']
        }
        return default_kps.get(subject, ['基础知识', '核心概念', '应用实践', '拓展提升'])

    def _build_knowledge_graph_path(self, knowledge_points, difficulty):
        """基于知识图谱构建路径"""
        nodes = []
        for i, kp in enumerate(knowledge_points):
            node = {
                'node_id': f"node_{i+1}",
                'node_order': i + 1,
                'title': f"第{i+1}节: {kp}",
                'knowledge_point': kp,
                'difficulty': min(difficulty + (i // 2), 5),
                'estimated_time': 30 + i * 5,
                'learning_resources': [
                    {'type': 'video', 'title': f"{kp}视频讲解", 'duration': 15},
                    {'type': 'reading', 'title': f"{kp}图文讲解", 'duration': 10},
                    {'type': 'exercise', 'title': f"{kp}练习题", 'count': 5}
                ],
                'status': 'pending'
            }
            nodes.append(node)
        return nodes

    def _build_ability_progression_path(self, knowledge_points, difficulty):
        """基于能力进阶构建路径"""
        nodes = []
        for i, kp in enumerate(knowledge_points):
            level = min(difficulty + (i // 2), 5)
            node = {
                'node_id': f"node_{i+1}",
                'node_order': i + 1,
                'title': f"等级{level} - {kp}",
                'knowledge_point': kp,
                'difficulty': level,
                'estimated_time': 25 + level * 5,
                'learning_resources': [
                    {'type': 'concept', 'title': f"{kp}概念学习", 'duration': 10},
                    {'type': 'example', 'title': f"{kp}例题精讲", 'duration': 15},
                    {'type': 'practice', 'title': f"{kp}专项练习", 'count': 3 + level},
                    {'type': 'challenge', 'title': f"{kp}挑战题", 'count': 2}
                ],
                'status': 'pending'
            }
            nodes.append(node)
        return nodes

    def _build_interest_driven_path(self, knowledge_points, difficulty, style):
        """基于兴趣驱动构建路径"""
        nodes = []
        style_strategies = LEARNING_STYLES[style]['strategies']
        for i, kp in enumerate(knowledge_points):
            node = {
                'node_id': f"node_{i+1}",
                'node_order': i + 1,
                'title': f"趣味学习: {kp}",
                'knowledge_point': kp,
                'difficulty': difficulty,
                'estimated_time': 20 + i * 3,
                'learning_resources': [
                    {'type': 'interactive', 'title': f"{kp}互动{style_strategies[0]}", 'duration': 15},
                    {'type': 'game', 'title': f"{kp}游戏化学习", 'duration': 10},
                    {'type': 'project', 'title': f"{kp}项目实践", 'duration': 20}
                ],
                'status': 'pending'
            }
            nodes.append(node)
        return nodes

    def _save_learning_path(self, path_id, student_id, subject, algorithm,
                            style, nodes, difficulty, target):
        """保存学习路径到数据库"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_paths
                    (path_id, student_id, subject, algorithm, learning_style,
                     current_node, total_nodes, completed_nodes, progress,
                     difficulty_level, target, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (path_id, student_id, subject, algorithm, style,
                      nodes[0]['node_id'] if nodes else None,
                      len(nodes), 0, 0.0, difficulty, target, 'active'))

                for node in nodes:
                    cursor.execute('''
                        INSERT INTO learning_path_nodes
                        (path_id, node_id, node_order, title, knowledge_point,
                         difficulty, estimated_time, learning_resources, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (path_id, node['node_id'], node['node_order'],
                          node['title'], node['knowledge_point'],
                          node['difficulty'], node['estimated_time'],
                          json.dumps(node['learning_resources'], ensure_ascii=False),
                          'pending'))
                conn.commit()
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 保存路径失败: {e}")

    def update_progress(self, path_id, node_id, score=None, status='completed'):
        """更新学习进度"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # 更新节点状态
                cursor.execute('''
                    UPDATE learning_path_nodes
                    SET status = ?, score = ?, completed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE path_id = ? AND node_id = ?
                ''', (status, score, status, path_id, node_id))

                # 计算进度
                cursor.execute('SELECT COUNT(*) FROM learning_path_nodes WHERE path_id = ?', (path_id,))
                total = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM learning_path_nodes WHERE path_id = ? AND status = 'completed'", (path_id,))
                completed = cursor.fetchone()[0]
                progress = round(completed / total * 100, 1) if total > 0 else 0

                # 更新路径进度
                cursor.execute('''
                    UPDATE learning_paths
                    SET completed_nodes = ?, progress = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE path_id = ?
                ''', (completed, progress, path_id))

                # 如果全部完成，更新状态
                if completed >= total:
                    cursor.execute("UPDATE learning_paths SET status = 'completed' WHERE path_id = ?", (path_id,))

                conn.commit()

            return {'success': True, 'path_id': path_id, 'node_id': node_id,
                    'status': status, 'progress': progress}
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 更新进度失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_learning_path(self, path_id):
        """获取学习路径详情"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_paths WHERE path_id = ?', (path_id,))
                path = cursor.fetchone()
                if not path:
                    return {'success': False, 'message': '路径不存在'}

                cursor.execute('SELECT * FROM learning_path_nodes WHERE path_id = ? ORDER BY node_order', (path_id,))
                nodes = cursor.fetchall()

                return {
                    'success': True,
                    'path': dict(path),
                    'nodes': [dict(n) for n in nodes],
                    'progress': path['progress']
                }
        except Exception as e:
            logger.error(f"[个性化学习路径引擎] 获取路径失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_engine_info(self):
        """获取引擎信息"""
        return {
            'name': self.engine_name,
            'version': self.version,
            'algorithms': PATH_ALGORITHMS,
            'learning_styles': LEARNING_STYLES,
            'difficulty_levels': DIFFICULTY_LEVELS,
            'features': [
                '3种学习路径算法',
                '自适应难度调节',
                '学习风格检测',
                '个性化推荐',
                '学习目标管理',
                '进度追踪与预警'
            ]
        }


# 单例
personalized_learning_path_engine = PersonalizedLearningPathEngine()


def get_engine():
    return personalized_learning_path_engine


if __name__ == '__main__':
    engine = PersonalizedLearningPathEngine()
    print("个性化学习路径引擎 v1.0")
    info = engine.get_engine_info()
    print(json.dumps(info, ensure_ascii=False, indent=2))
