#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育个性化服务 (v15.24.0)
====================================
提供用户画像构建、个性化推荐、自适应学习等综合个性化服务。

核心能力：
1. 用户画像构建 - 多维用户画像、画像更新、画像分析、画像导出
2. 个性化推荐 - 课程推荐、内容推荐、学习路径推荐、活动推荐
3. 自适应学习 - 难度自适应、进度自适应、内容自适应、方法自适应
4. 个性化内容 - 内容定制、内容推送、内容偏好、内容过滤、内容排序
5. 个性化评估 - 评估定制、评估执行、结果分析、评估反馈
6. 个性化反馈 - 即时反馈、详细反馈、鼓励反馈、反思反馈
7. 个性化路径 - 路径规划、路径调整、路径追踪、路径评估
8. 个性化体验 - 界面定制、交互优化、激励机制、专属服务
9. 预警管理 - 学习预警、风险评估、干预建议、预警历史
10. 统计分析 - 个性化效果统计
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_personalization_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationPersonalization')


# ========== 个性化配置 ==========

USER_PROFILE_DIMENSIONS = {
    'learning_interests': {'name': '学习兴趣', 'sub': ['学科偏好', '学习领域', '兴趣强度', '兴趣变化']},
    'learning_ability': {'name': '学习能力', 'sub': ['认知水平', '知识储备', '技能掌握', '问题解决']},
    'learning_style': {'name': '学习风格', 'sub': ['视觉型', '听觉型', '动觉型', '阅读型', '社交型', '独立型']},
    'learning_goals': {'name': '学习目标', 'sub': ['短期目标', '中期目标', '长期目标', '职业目标', '学业目标']},
    'learning_preferences': {'name': '学习偏好', 'sub': ['时间偏好', '环境偏好', '内容形式', '学习节奏']},
    'learning_history': {'name': '学习历史', 'sub': ['课程记录', '成绩记录', '学习时长', '完成率']},
    'learning_behavior': {'name': '学习行为', 'sub': ['登录频率', '学习时长', '互动行为', '作业提交']},
    'learning_motivation': {'name': '学习动机', 'sub': ['内在动机', '外在动机', '自我效能', '学习坚持']}
}

RECOMMENDATION_ALGORITHMS = {
    'collaborative_filtering': {'name': '协同过滤', 'type': 'user-based', '适用场景': '相似用户推荐'},
    'content_based': {'name': '内容推荐', 'type': 'item-based', '适用场景': '基于内容特征'},
    'knowledge_graph': {'name': '基于知识图谱', 'type': 'semantic', '适用场景': '知识关联推荐'},
    'deep_learning': {'name': '深度学习', 'type': 'neural', '适用场景': '复杂模式挖掘'},
    'reinforcement_learning': {'name': '强化学习', 'type': 'adaptive', '适用场景': '动态优化推荐'},
    'hybrid': {'name': '混合推荐', 'type': 'ensemble', '适用场景': '多算法融合'},
    'context_aware': {'name': '上下文推荐', 'type': 'context', '适用场景': '场景感知推荐'},
    'temporal': {'name': '时序推荐', 'type': 'time-based', '适用场景': '时间动态推荐'}
}

ADAPTIVE_STRATEGIES = {
    'difficulty_adaptive': {'name': '难度自适应', 'description': '根据能力动态调整难度'},
    'content_adaptive': {'name': '内容自适应', 'description': '根据需求定制学习内容'},
    'progress_adaptive': {'name': '进度自适应', 'description': '根据进度调整学习计划'},
    'method_adaptive': {'name': '方法自适应', 'description': '根据风格调整教学方法'},
    'assessment_adaptive': {'name': '评估自适应', 'description': '根据表现调整评估方式'},
    'feedback_adaptive': {'name': '反馈自适应', 'description': '根据需求调整反馈策略'},
    'path_adaptive': {'name': '路径自适应', 'description': '根据状态调整学习路径'},
    'experience_adaptive': {'name': '体验自适应', 'description': '根据偏好调整学习体验'}
}

CONTENT_TYPES = {
    'video_course': {'name': '视频课程', 'duration_unit': '分钟', 'suitable_for': ['成人教育', 'K12']},
    'audio_course': {'name': '音频课程', 'duration_unit': '分钟', 'suitable_for': ['成人教育']},
    'text_material': {'name': '图文资料', 'duration_unit': '页', 'suitable_for': ['成人教育', 'K12']},
    'interactive_practice': {'name': '互动练习', 'duration_unit': '题', 'suitable_for': ['成人教育', 'K12']},
    'simulation_experiment': {'name': '模拟实验', 'duration_unit': '分钟', 'suitable_for': ['成人教育', 'K12']},
    'case_study': {'name': '案例分析', 'duration_unit': '个', 'suitable_for': ['成人教育']},
    'practice_project': {'name': '实践项目', 'duration_unit': '小时', 'suitable_for': ['成人教育']},
    'comprehensive_assessment': {'name': '综合测评', 'duration_unit': '分钟', 'suitable_for': ['成人教育', 'K12']}
}

ASSESSMENT_TYPES = {
    'formative': {'name': '形成性评估', 'purpose': '过程性评价', 'frequency': '高频'},
    'summative': {'name': '总结性评估', 'purpose': '结果性评价', 'frequency': '低频'},
    'diagnostic': {'name': '诊断性评估', 'purpose': '能力诊断', 'frequency': '一次性'},
    'performance': {'name': '表现性评估', 'purpose': '能力展示', 'frequency': '中频'},
    'standardized': {'name': '标准化评估', 'purpose': '统一衡量', 'frequency': '定期'},
    'adaptive': {'name': '自适应评估', 'purpose': '精准测量', 'frequency': '按需'},
    'personalized': {'name': '个性化评估', 'purpose': '定制评价', 'frequency': '按需'},
    'dynamic': {'name': '动态评估', 'purpose': '成长追踪', 'frequency': '持续'}
}

FEEDBACK_STRATEGIES = {
    'immediate': {'name': '即时反馈', 'timing': '实时', 'depth': '浅层'},
    'progressive': {'name': '渐进反馈', 'timing': '阶段性', 'depth': '中深层'},
    'detailed': {'name': '详细反馈', 'timing': '任务后', 'depth': '深层'},
    'encouraging': {'name': '鼓励反馈', 'timing': '适时', 'depth': '情感层'},
    'guidance': {'name': '指导反馈', 'timing': '需要时', 'depth': '策略层'},
    'reflective': {'name': '反思反馈', 'timing': '学习后', 'depth': '元认知层'},
    'comparative': {'name': '对比反馈', 'timing': '阶段性', 'depth': '参照层'},
    'metacognitive': {'name': '元认知反馈', 'timing': '学习后', 'depth': '认知层'}
}

PATH_STRATEGIES = {
    'linear': {'name': '线性路径', 'structure': '顺序', 'flexibility': '低'},
    'branching': {'name': '分支路径', 'structure': '选择', 'flexibility': '中'},
    'network': {'name': '网状路径', 'structure': '网状', 'flexibility': '高'},
    'adaptive': {'name': '自适应路径', 'structure': '动态', 'flexibility': '极高'},
    'personalized': {'name': '个性化路径', 'structure': '定制', 'flexibility': '极高'},
    'exploratory': {'name': '探索路径', 'structure': '开放', 'flexibility': '极高'},
    'spiral': {'name': '螺旋路径', 'structure': '循环', 'flexibility': '中'},
    'cyclical': {'name': '循环路径', 'structure': '往复', 'flexibility': '低'}
}

EXPERIENCE_ELEMENTS = {
    'interface_style': {'name': '界面风格', 'options': ['简约', '活泼', '专业', '个性化']},
    'interaction_mode': {'name': '交互方式', 'options': ['点击', '拖拽', '语音', '手势']},
    'content_presentation': {'name': '内容呈现', 'options': ['列表', '卡片', '瀑布流', '思维导图']},
    'learning_rhythm': {'name': '学习节奏', 'options': ['快节奏', '标准', '慢节奏', '自由']},
    'incentive_mechanism': {'name': '激励机制', 'options': ['积分', '徽章', '等级', '成就']},
    'social_interaction': {'name': '社交互动', 'options': ['讨论区', '小组', '导师', '同伴']},
    'personalized_messages': {'name': '个性化消息', 'options': ['推送', '邮件', '短信', '站内信']},
    'exclusive_service': {'name': '专属服务', 'options': ['一对一', 'VIP', '优先', '定制']}
}


class EducationPersonalizationService:
    """教育个性化服务"""

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
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        profile_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        age INTEGER,
                        gender TEXT,
                        learning_interests TEXT,
                        learning_ability TEXT,
                        learning_style TEXT,
                        learning_goals TEXT,
                        learning_preferences TEXT,
                        learning_history TEXT,
                        learning_behavior TEXT,
                        learning_motivation TEXT,
                        profile_score REAL DEFAULT 0,
                        last_updated TEXT,
                        created_at TEXT,
                        UNIQUE(user_id, education_type)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS profile_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_id TEXT NOT NULL,
                        dimension TEXT NOT NULL,
                        data_key TEXT NOT NULL,
                        data_value TEXT,
                        confidence REAL DEFAULT 1.0,
                        source TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (profile_id) REFERENCES user_profiles(profile_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalization_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_name TEXT NOT NULL,
                        rule_type TEXT,
                        education_type TEXT,
                        priority INTEGER DEFAULT 1,
                        condition TEXT,
                        action TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rule_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        FOREIGN KEY (rule_id) REFERENCES personalization_rules(rule_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS adaptive_learning (
                        adaptive_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        course_id TEXT,
                        strategy TEXT,
                        current_difficulty REAL DEFAULT 1.0,
                        progress REAL DEFAULT 0,
                        performance REAL DEFAULT 0,
                        adaptation_count INTEGER DEFAULT 0,
                        last_adapted TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        adaptive_id TEXT NOT NULL,
                        state_key TEXT NOT NULL,
                        state_value TEXT,
                        recorded_at TEXT,
                        FOREIGN KEY (adaptive_id) REFERENCES adaptive_learning(adaptive_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalized_content (
                        content_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        content_type TEXT,
                        source_content_id TEXT,
                        customization_level TEXT DEFAULT 'low',
                        delivery_status TEXT DEFAULT 'pending',
                        delivered_at TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        content_type TEXT NOT NULL,
                        preference_score REAL DEFAULT 0.5,
                        last_interaction TEXT,
                        interaction_count INTEGER DEFAULT 0,
                        UNIQUE(user_id, education_type, content_type)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalized_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        assessment_type TEXT,
                        target_dimension TEXT,
                        difficulty REAL DEFAULT 1.0,
                        question_count INTEGER DEFAULT 10,
                        duration_minutes INTEGER DEFAULT 30,
                        status TEXT DEFAULT 'created',
                        scheduled_at TEXT,
                        completed_at TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_results (
                        result_id TEXT PRIMARY KEY,
                        assessment_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        score REAL DEFAULT 0,
                        max_score REAL DEFAULT 100,
                        correct_count INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        performance_level TEXT,
                        feedback TEXT,
                        analyzed_at TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES personalized_assessment(assessment_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalized_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        feedback_type TEXT,
                        source_type TEXT,
                        source_id TEXT,
                        content TEXT,
                        tone TEXT DEFAULT 'neutral',
                        depth TEXT DEFAULT 'shallow',
                        action_required INTEGER DEFAULT 0,
                        read_status INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feedback_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        action TEXT,
                        action_time TEXT,
                        FOREIGN KEY (feedback_id) REFERENCES personalized_feedback(feedback_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_paths (
                        path_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        path_name TEXT NOT NULL,
                        strategy TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        total_nodes INTEGER DEFAULT 0,
                        completed_nodes INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS path_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path_id TEXT NOT NULL,
                        node_order INTEGER NOT NULL,
                        node_type TEXT,
                        node_content TEXT,
                        prerequisites TEXT,
                        estimated_duration INTEGER,
                        FOREIGN KEY (path_id) REFERENCES learning_paths(path_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalized_experience (
                        experience_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        interface_style TEXT,
                        interaction_mode TEXT,
                        content_presentation TEXT,
                        learning_rhythm TEXT,
                        incentive_mechanism TEXT,
                        social_interaction TEXT,
                        personalized_messages TEXT,
                        exclusive_service TEXT,
                        last_updated TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experience_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        experience_id TEXT NOT NULL,
                        setting_key TEXT NOT NULL,
                        setting_value TEXT,
                        FOREIGN KEY (experience_id) REFERENCES personalized_experience(experience_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personalization_alerts (
                        alert_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        education_type TEXT,
                        alert_type TEXT,
                        severity TEXT DEFAULT 'medium',
                        title TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        threshold_value TEXT,
                        current_value TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        action TEXT,
                        action_result TEXT,
                        action_time TEXT,
                        FOREIGN KEY (alert_id) REFERENCES personalization_alerts(alert_id)
                    )
                ''')

                conn.commit()
                logger.info('教育个性化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 用户画像构建 ==========

    def create_user_profile(self, user_id: int, user_name: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            profile_id = f"prf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO user_profiles (
                            profile_id, user_id, user_name, education_type,
                            grade_level, age, gender, learning_interests,
                            learning_ability, learning_style, learning_goals,
                            learning_preferences, learning_history,
                            learning_behavior, learning_motivation,
                            profile_score, last_updated, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (profile_id, user_id, user_name, education_type,
                          kwargs.get('grade_level'), kwargs.get('age'),
                          kwargs.get('gender'),
                          json.dumps(kwargs.get('learning_interests', {})),
                          json.dumps(kwargs.get('learning_ability', {})),
                          json.dumps(kwargs.get('learning_style', {})),
                          json.dumps(kwargs.get('learning_goals', {})),
                          json.dumps(kwargs.get('learning_preferences', {})),
                          json.dumps(kwargs.get('learning_history', {})),
                          json.dumps(kwargs.get('learning_behavior', {})),
                          json.dumps(kwargs.get('learning_motivation', {})),
                          now, now))
                    conn.commit()
                    logger.info(f'创建用户画像: {user_name} ({profile_id})')
                    return {'success': True, 'profile_id': profile_id}
        except Exception as e:
            logger.error(f'创建用户画像失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_profile_dimension(self, profile_id: str, dimension: str,
                                 data_key: str, data_value: Any, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT profile_id FROM user_profiles WHERE profile_id = ?', (profile_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '用户画像不存在'}
                    cursor.execute('''
                        INSERT OR REPLACE INTO profile_data (
                            profile_id, dimension, data_key, data_value,
                            confidence, source, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (profile_id, dimension, data_key, json.dumps(data_value),
                          kwargs.get('confidence', 1.0), kwargs.get('source', 'system'), now))
                    cursor.execute('UPDATE user_profiles SET last_updated = ? WHERE profile_id = ?', (now, profile_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新画像维度失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_user_profile(self, profile_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_profiles WHERE profile_id = ?', (profile_id,))
                profile = cursor.fetchone()
                if not profile:
                    return {'success': False, 'error': '用户画像不存在'}
                cursor.execute('SELECT * FROM profile_data WHERE profile_id = ?', (profile_id,))
                data = cursor.fetchall()
                analysis = {
                    'profile': dict(profile),
                    'dimension_data': [dict(d) for d in data],
                    'insights': self._generate_profile_insights(dict(profile), [dict(d) for d in data])
                }
                return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f'分析用户画像失败: {e}')
            return {'success': False, 'error': str(e)}

    def export_profile(self, profile_id: str, format_type: str = 'json') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_profiles WHERE profile_id = ?', (profile_id,))
                profile = cursor.fetchone()
                if not profile:
                    return {'success': False, 'error': '用户画像不存在'}
                cursor.execute('SELECT * FROM profile_data WHERE profile_id = ?', (profile_id,))
                data = cursor.fetchall()
                export_data = {
                    'profile': dict(profile),
                    'dimension_data': [dict(d) for d in data],
                    'export_time': datetime.now().isoformat(),
                    'format': format_type
                }
                if format_type == 'json':
                    return {'success': True, 'data': export_data, 'content': json.dumps(export_data, ensure_ascii=False, indent=2)}
                return {'success': True, 'data': export_data}
        except Exception as e:
            logger.error(f'导出用户画像失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_profile_insights(self, profile: Dict, data: List[Dict]) -> Dict[str, Any]:
        insights = {}
        interests = json.loads(profile.get('learning_interests', '{}'))
        ability = json.loads(profile.get('learning_ability', '{}'))
        style = json.loads(profile.get('learning_style', '{}'))
        if interests:
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:3]
            insights['top_interests'] = [{'subject': k, 'score': v} for k, v in top_interests]
        if ability:
            avg_ability = sum(ability.values()) / len(ability) if ability else 0
            insights['ability_level'] = 'high' if avg_ability >= 0.7 else ('medium' if avg_ability >= 0.4 else 'low')
        if style:
            dominant_style = max(style.items(), key=lambda x: x[1])[0] if style else None
            insights['dominant_style'] = dominant_style
        return insights

    # ========== 个性化推荐 ==========

    def recommend_courses(self, user_id: int, education_type: str,
                          count: int = 5, **kwargs) -> Dict[str, Any]:
        try:
            algorithm = kwargs.get('algorithm', 'hybrid')
            config = RECOMMENDATION_ALGORITHMS.get(algorithm, {})
            recommendations = []
            for i in range(count):
                recommendations.append({
                    'course_id': f"rec_course_{i+1}",
                    'course_name': f"推荐课程{i+1}",
                    'algorithm': algorithm,
                    'algorithm_name': config.get('name', algorithm),
                    'score': round(0.8 + i * 0.02, 2),
                    'reason': '基于用户画像匹配',
                    'education_type': education_type
                })
            return {'success': True, 'recommendations': recommendations, 'algorithm': algorithm}
        except Exception as e:
            logger.error(f'推荐课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_content(self, user_id: int, education_type: str,
                          content_type: str = None, count: int = 5) -> Dict[str, Any]:
        try:
            recommendations = []
            types = [content_type] if content_type else list(CONTENT_TYPES.keys())
            for i, ct in enumerate(types[:count]):
                config = CONTENT_TYPES.get(ct, {})
                recommendations.append({
                    'content_id': f"rec_content_{i+1}",
                    'content_type': ct,
                    'content_type_name': config.get('name', ct),
                    'score': round(0.75 + i * 0.03, 2),
                    'reason': '基于内容偏好推荐',
                    'education_type': education_type
                })
            return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'推荐内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_learning_path(self, user_id: int, education_type: str,
                                goal: str = None) -> Dict[str, Any]:
        try:
            path_id = f"rec_path_{uuid.uuid4().hex[:8]}"
            strategy = 'personalized' if goal else 'adaptive'
            path_config = PATH_STRATEGIES.get(strategy, {})
            nodes = []
            for i in range(5):
                nodes.append({
                    'node_order': i + 1,
                    'node_type': 'course',
                    'node_content': f"学习模块{i+1}",
                    'estimated_duration': (i + 1) * 4
                })
            return {
                'success': True,
                'path_id': path_id,
                'path_name': f"个性化学习路径_{goal or '通用'}",
                'strategy': strategy,
                'strategy_name': path_config.get('name', strategy),
                'nodes': nodes,
                'education_type': education_type
            }
        except Exception as e:
            logger.error(f'推荐学习路径失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_events(self, user_id: int, education_type: str,
                         count: int = 3) -> Dict[str, Any]:
        try:
            recommendations = []
            event_types = ['workshop', 'webinar', 'competition', 'study_group']
            for i in range(count):
                et = event_types[i % len(event_types)]
                recommendations.append({
                    'event_id': f"rec_event_{i+1}",
                    'event_name': f"{et}活动{i+1}",
                    'event_type': et,
                    'score': round(0.7 + i * 0.05, 2),
                    'reason': '基于学习行为推荐',
                    'education_type': education_type
                })
            return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'推荐活动失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 自适应学习 ==========

    def initialize_adaptive_learning(self, user_id: int, education_type: str,
                                     course_id: str, **kwargs) -> Dict[str, Any]:
        try:
            adaptive_id = f"adp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            strategy = kwargs.get('strategy', 'difficulty_adaptive')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO adaptive_learning (
                            adaptive_id, user_id, education_type, course_id,
                            strategy, current_difficulty, progress,
                            performance, adaptation_count, last_adapted, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
                    ''', (adaptive_id, user_id, education_type, course_id,
                          strategy, kwargs.get('initial_difficulty', 1.0), now, now))
                    conn.commit()
                    logger.info(f'初始化自适应学习: {user_id} ({adaptive_id})')
                    return {'success': True, 'adaptive_id': adaptive_id}
        except Exception as e:
            logger.error(f'初始化自适应学习失败: {e}')
            return {'success': False, 'error': str(e)}

    def adapt_learning_difficulty(self, adaptive_id: str, performance: float,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_difficulty, adaptation_count FROM adaptive_learning WHERE adaptive_id = ?', (adaptive_id,))
                    adaptive = cursor.fetchone()
                    if not adaptive:
                        return {'success': False, 'error': '自适应学习不存在'}
                    current_diff = adaptive[0]
                    adaptation_count = adaptive[1]
                    if performance >= 0.8:
                        new_diff = min(current_diff + 0.1, 3.0)
                    elif performance < 0.5:
                        new_diff = max(current_diff - 0.1, 0.5)
                    else:
                        new_diff = current_diff
                    cursor.execute('''
                        UPDATE adaptive_learning SET
                            current_difficulty = ?, performance = ?,
                            adaptation_count = ?, last_adapted = ?
                        WHERE adaptive_id = ?
                    ''', (new_diff, performance, adaptation_count + 1, now, adaptive_id))
                    cursor.execute('''
                        INSERT INTO learning_state (adaptive_id, state_key, state_value, recorded_at)
                        VALUES (?, 'difficulty_change', ?, ?)
                    ''', (adaptive_id, json.dumps({'old': current_diff, 'new': new_diff, 'reason': 'performance'}), now))
                    conn.commit()
                    return {'success': True, 'new_difficulty': new_diff, 'adaptation_count': adaptation_count + 1}
        except Exception as e:
            logger.error(f'自适应调整难度失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learning_progress(self, adaptive_id: str, progress: float,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM adaptive_learning WHERE adaptive_id = ?', (adaptive_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '自适应学习不存在'}
                    cursor.execute('UPDATE adaptive_learning SET progress = ?, updated_at = ? WHERE adaptive_id = ?', (progress, now, adaptive_id))
                    cursor.execute('''
                        INSERT INTO learning_state (adaptive_id, state_key, state_value, recorded_at)
                        VALUES (?, 'progress_update', ?, ?)
                    ''', (adaptive_id, json.dumps({'progress': progress, 'details': kwargs.get('details', {})}), now))
                    conn.commit()
                    status = 'completed' if progress >= 100 else 'active'
                    return {'success': True, 'progress': progress, 'status': status}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_adaptive_learning_state(self, adaptive_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM adaptive_learning WHERE adaptive_id = ?', (adaptive_id,))
                adaptive = cursor.fetchone()
                if not adaptive:
                    return {'success': False, 'error': '自适应学习不存在'}
                cursor.execute('SELECT * FROM learning_state WHERE adaptive_id = ? ORDER BY recorded_at DESC', (adaptive_id,))
                states = cursor.fetchall()
                return {'success': True, 'adaptive_info': dict(adaptive), 'history': [dict(s) for s in states]}
        except Exception as e:
            logger.error(f'获取自适应学习状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 个性化内容 ==========

    def create_personalized_content(self, user_id: int, education_type: str,
                                    content_type: str, source_content_id: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            content_id = f"pcn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalized_content (
                            content_id, user_id, education_type, content_type,
                            source_content_id, customization_level,
                            delivery_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (content_id, user_id, education_type, content_type,
                          source_content_id, kwargs.get('customization_level', 'low'), now))
                    conn.commit()
                    logger.info(f'创建个性化内容: {content_id}')
                    return {'success': True, 'content_id': content_id}
        except Exception as e:
            logger.error(f'创建个性化内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_content_preference(self, user_id: int, education_type: str,
                                   content_type: str, preference_score: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO content_preferences (
                            user_id, education_type, content_type,
                            preference_score, last_interaction, interaction_count
                        ) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT interaction_count FROM content_preferences WHERE user_id = ? AND education_type = ? AND content_type = ?), 0) + 1)
                    ''', (user_id, education_type, content_type, preference_score, now,
                          user_id, education_type, content_type))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新内容偏好失败: {e}')
            return {'success': False, 'error': str(e)}

    def deliver_content(self, content_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE personalized_content SET delivery_status = ?, delivered_at = ? WHERE content_id = ? AND delivery_status = ?',
                                 ('delivered', now, content_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'delivered_at': now}
                    return {'success': False, 'error': '内容状态不允许发送'}
        except Exception as e:
            logger.error(f'发送内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def filter_content(self, user_id: int, education_type: str,
                       **filters) -> Dict[str, Any]:
        try:
            filtered = []
            for ct, config in CONTENT_TYPES.items():
                if config.get('suitable_for') and education_type in config['suitable_for']:
                    filtered.append({
                        'content_type': ct,
                        'name': config.get('name'),
                        'suitable_for': config.get('suitable_for')
                    })
            return {'success': True, 'filtered_content': filtered, 'filters': filters}
        except Exception as e:
            logger.error(f'过滤内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_content_preferences(self, user_id: int, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM content_preferences WHERE user_id = ? AND education_type = ?', (user_id, education_type))
                preferences = cursor.fetchall()
                return {'success': True, 'preferences': [dict(p) for p in preferences]}
        except Exception as e:
            logger.error(f'获取内容偏好失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 个性化评估 ==========

    def create_personalized_assessment(self, user_id: int, education_type: str,
                                        assessment_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"pas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalized_assessment (
                            assessment_id, user_id, education_type,
                            assessment_type, target_dimension, difficulty,
                            question_count, duration_minutes, status,
                            scheduled_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'created', ?, ?)
                    ''', (assessment_id, user_id, education_type, assessment_type,
                          kwargs.get('target_dimension'),
                          kwargs.get('difficulty', 1.0),
                          kwargs.get('question_count', 10),
                          kwargs.get('duration_minutes', 30),
                          kwargs.get('scheduled_at', now), now))
                    conn.commit()
                    logger.info(f'创建个性化评估: {assessment_id}')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建个性化评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_assessment(self, assessment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM personalized_assessment WHERE assessment_id = ?', (assessment_id,))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评估不存在'}
                    cursor.execute('UPDATE personalized_assessment SET status = ? WHERE assessment_id = ?', ('in_progress', assessment_id))
                    result_id = f"ars_{uuid.uuid4().hex[:12]}"
                    score = kwargs.get('score', 0)
                    correct_count = kwargs.get('correct_count', 0)
                    total_count = assessment[7]
                    performance_level = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
                    cursor.execute('''
                        INSERT INTO assessment_results (
                            result_id, assessment_id, user_id, score, max_score,
                            correct_count, total_count, performance_level,
                            feedback, analyzed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, assessment_id, assessment[1], score, 100,
                          correct_count, total_count, performance_level,
                          kwargs.get('feedback', ''), now))
                    cursor.execute('UPDATE personalized_assessment SET status = ?, completed_at = ? WHERE assessment_id = ?', ('completed', now, assessment_id))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'score': score, 'performance_level': performance_level}
        except Exception as e:
            logger.error(f'执行评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_assessment_result(self, result_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assessment_results WHERE result_id = ?', (result_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '评估结果不存在'}
                analysis = {
                    'result': dict(result),
                    'analysis': self._generate_assessment_analysis(dict(result)),
                    'suggestions': self._generate_assessment_suggestions(dict(result))
                }
                return {'success': True, 'analysis': analysis}
        except Exception as e:
            logger.error(f'分析评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_history(self, user_id: int, education_type: str,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pa.*, ar.score, ar.performance_level
                    FROM personalized_assessment pa
                    LEFT JOIN assessment_results ar ON pa.assessment_id = ar.assessment_id
                    WHERE pa.user_id = ? AND pa.education_type = ?
                    ORDER BY pa.created_at DESC LIMIT ? OFFSET ?
                ''', (user_id, education_type, page_size, (page - 1) * page_size))
                assessments = cursor.fetchall()
                cursor.execute('SELECT COUNT(*) as cnt FROM personalized_assessment WHERE user_id = ? AND education_type = ?', (user_id, education_type))
                total = cursor.fetchone()['cnt']
                return {'success': True, 'assessments': [dict(a) for a in assessments], 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_assessment_analysis(self, result: Dict) -> Dict[str, Any]:
        score = result.get('score', 0)
        return {
            'score_level': 'high' if score >= 80 else ('medium' if score >= 60 else 'low'),
            'accuracy_rate': round(result.get('correct_count', 0) / result.get('total_count', 1) * 100, 2),
            'comparison': {'average': 75, 'your_score': score, 'deviation': score - 75}
        }

    def _generate_assessment_suggestions(self, result: Dict) -> List[Dict]:
        score = result.get('score', 0)
        if score < 60:
            return [{'type': 'remedial', 'content': '建议复习基础知识', 'priority': 'high'},
                    {'type': 'practice', 'content': '增加练习次数', 'priority': 'high'}]
        elif score < 80:
            return [{'type': 'enhancement', 'content': '深入学习薄弱环节', 'priority': 'medium'},
                    {'type': 'challenge', 'content': '尝试更高难度内容', 'priority': 'low'}]
        else:
            return [{'type': 'advanced', 'content': '探索进阶内容', 'priority': 'medium'},
                    {'type': 'mentor', 'content': '考虑担任学习助手', 'priority': 'low'}]

    # ========== 个性化反馈 ==========

    def create_personalized_feedback(self, user_id: int, education_type: str,
                                      feedback_type: str, **kwargs) -> Dict[str, Any]:
        try:
            feedback_id = f"fdb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalized_feedback (
                            feedback_id, user_id, education_type, feedback_type,
                            source_type, source_id, content, tone, depth,
                            action_required, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (feedback_id, user_id, education_type, feedback_type,
                          kwargs.get('source_type'), kwargs.get('source_id'),
                          kwargs.get('content', ''), kwargs.get('tone', 'neutral'),
                          kwargs.get('depth', 'shallow'), kwargs.get('action_required', 0), now))
                    conn.commit()
                    logger.info(f'创建个性化反馈: {feedback_id}')
                    return {'success': True, 'feedback_id': feedback_id}
        except Exception as e:
            logger.error(f'创建个性化反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def deliver_feedback(self, feedback_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE personalized_feedback SET read_status = 1 WHERE feedback_id = ?', (feedback_id,))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO feedback_history (feedback_id, user_id, action, action_time)
                            SELECT feedback_id, user_id, 'delivered', ? FROM personalized_feedback WHERE feedback_id = ?
                        ''', (now, feedback_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '反馈不存在'}
        except Exception as e:
            logger.error(f'发送反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_feedback_history(self, user_id: int, education_type: str,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pf.*, fh.action, fh.action_time
                    FROM personalized_feedback pf
                    LEFT JOIN feedback_history fh ON pf.feedback_id = fh.feedback_id
                    WHERE pf.user_id = ? AND pf.education_type = ?
                    ORDER BY pf.created_at DESC LIMIT ? OFFSET ?
                ''', (user_id, education_type, page_size, (page - 1) * page_size))
                feedbacks = cursor.fetchall()
                cursor.execute('SELECT COUNT(*) as cnt FROM personalized_feedback WHERE user_id = ? AND education_type = ?', (user_id, education_type))
                total = cursor.fetchone()['cnt']
                return {'success': True, 'feedbacks': [dict(f) for f in feedbacks], 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取反馈历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_feedback_action(self, feedback_id: str, action: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM personalized_feedback WHERE feedback_id = ?', (feedback_id,))
                    user = cursor.fetchone()
                    if not user:
                        return {'success': False, 'error': '反馈不存在'}
                    cursor.execute('''
                        INSERT INTO feedback_history (feedback_id, user_id, action, action_result, action_time)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (feedback_id, user[0], action, kwargs.get('action_result', ''), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'处理反馈操作失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 个性化路径 ==========

    def create_learning_path(self, user_id: int, education_type: str,
                              path_name: str, **kwargs) -> Dict[str, Any]:
        try:
            path_id = f"lpa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            strategy = kwargs.get('strategy', 'personalized')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_paths (
                            path_id, user_id, education_type, path_name,
                            strategy, start_date, end_date, progress,
                            status, total_nodes, completed_nodes,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, 0, ?, ?)
                    ''', (path_id, user_id, education_type, path_name, strategy,
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), kwargs.get('total_nodes', 0), now, now))
                    conn.commit()
                    logger.info(f'创建学习路径: {path_name} ({path_id})')
                    return {'success': True, 'path_id': path_id}
        except Exception as e:
            logger.error(f'创建学习路径失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_path_node(self, path_id: str, node_order: int, node_type: str,
                      node_content: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_nodes FROM learning_paths WHERE path_id = ?', (path_id,))
                    path = cursor.fetchone()
                    if not path:
                        return {'success': False, 'error': '学习路径不存在'}
                    cursor.execute('''
                        INSERT INTO path_config (path_id, node_order, node_type, node_content, prerequisites, estimated_duration)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (path_id, node_order, node_type, node_content,
                          json.dumps(kwargs.get('prerequisites', [])),
                          kwargs.get('estimated_duration', 4)))
                    cursor.execute('UPDATE learning_paths SET total_nodes = total_nodes + 1, updated_at = ? WHERE path_id = ?', (datetime.now().isoformat(), path_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加路径节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_path_progress(self, path_id: str, completed_node_order: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_nodes, completed_nodes FROM learning_paths WHERE path_id = ?', (path_id,))
                    path = cursor.fetchone()
                    if not path:
                        return {'success': False, 'error': '学习路径不存在'}
                    total = path[0]
                    completed = path[1] + 1
                    progress = round((completed / total) * 100, 2) if total > 0 else 0
                    status = 'completed' if completed >= total else 'active'
                    cursor.execute('''
                        UPDATE learning_paths SET
                            completed_nodes = ?, progress = ?,
                            status = ?, updated_at = ?
                        WHERE path_id = ?
                    ''', (completed, progress, status, now, path_id))
                    conn.commit()
                    return {'success': True, 'progress': progress, 'status': status}
        except Exception as e:
            logger.error(f'更新路径进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_path_details(self, path_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_paths WHERE path_id = ?', (path_id,))
                path = cursor.fetchone()
                if not path:
                    return {'success': False, 'error': '学习路径不存在'}
                cursor.execute('SELECT * FROM path_config WHERE path_id = ? ORDER BY node_order', (path_id,))
                nodes = cursor.fetchall()
                return {'success': True, 'path': dict(path), 'nodes': [dict(n) for n in nodes]}
        except Exception as e:
            logger.error(f'获取路径详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 个性化体验 ==========

    def create_personalized_experience(self, user_id: int, education_type: str,
                                        **kwargs) -> Dict[str, Any]:
        try:
            experience_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalized_experience (
                            experience_id, user_id, education_type,
                            interface_style, interaction_mode,
                            content_presentation, learning_rhythm,
                            incentive_mechanism, social_interaction,
                            personalized_messages, exclusive_service,
                            last_updated, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (experience_id, user_id, education_type,
                          kwargs.get('interface_style'),
                          kwargs.get('interaction_mode'),
                          kwargs.get('content_presentation'),
                          kwargs.get('learning_rhythm'),
                          kwargs.get('incentive_mechanism'),
                          kwargs.get('social_interaction'),
                          kwargs.get('personalized_messages'),
                          kwargs.get('exclusive_service'), now, now))
                    conn.commit()
                    logger.info(f'创建个性化体验: {experience_id}')
                    return {'success': True, 'experience_id': experience_id}
        except Exception as e:
            logger.error(f'创建个性化体验失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_experience_setting(self, experience_id: str, setting_key: str,
                                   setting_value: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT experience_id FROM personalized_experience WHERE experience_id = ?', (experience_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '个性化体验不存在'}
                    cursor.execute('INSERT OR REPLACE INTO experience_settings (experience_id, setting_key, setting_value) VALUES (?, ?, ?)',
                                 (experience_id, setting_key, setting_value))
                    cursor.execute('UPDATE personalized_experience SET last_updated = ? WHERE experience_id = ?', (now, experience_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新体验设置失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_personalized_experience(self, user_id: int, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM personalized_experience WHERE user_id = ? AND education_type = ?', (user_id, education_type))
                experience = cursor.fetchone()
                if not experience:
                    return {'success': False, 'error': '个性化体验不存在'}
                cursor.execute('SELECT * FROM experience_settings WHERE experience_id = ?', (experience['experience_id'],))
                settings = cursor.fetchall()
                return {'success': True, 'experience': dict(experience), 'settings': [dict(s) for s in settings]}
        except Exception as e:
            logger.error(f'获取个性化体验失败: {e}')
            return {'success': False, 'error': str(e)}

    def reset_experience_to_default(self, experience_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            defaults = {
                'interface_style': '简约',
                'interaction_mode': '点击',
                'content_presentation': '卡片',
                'learning_rhythm': '标准',
                'incentive_mechanism': '积分',
                'social_interaction': '讨论区',
                'personalized_messages': '推送',
                'exclusive_service': None
            }
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE personalized_experience SET
                            interface_style = ?, interaction_mode = ?,
                            content_presentation = ?, learning_rhythm = ?,
                            incentive_mechanism = ?, social_interaction = ?,
                            personalized_messages = ?, exclusive_service = ?,
                            last_updated = ?
                        WHERE experience_id = ?
                    ''', (defaults['interface_style'], defaults['interaction_mode'],
                          defaults['content_presentation'], defaults['learning_rhythm'],
                          defaults['incentive_mechanism'], defaults['social_interaction'],
                          defaults['personalized_messages'], defaults['exclusive_service'],
                          now, experience_id))
                    cursor.execute('DELETE FROM experience_settings WHERE experience_id = ?', (experience_id,))
                    conn.commit()
                    return {'success': True, 'defaults': defaults}
        except Exception as e:
            logger.error(f'重置体验设置失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, user_id: int, education_type: str, alert_type: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO personalization_alerts (
                            alert_id, user_id, education_type, alert_type,
                            severity, title, description, status,
                            threshold_value, current_value, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (alert_id, user_id, education_type, alert_type,
                          kwargs.get('severity', 'medium'),
                          kwargs.get('title', ''), kwargs.get('description', ''),
                          kwargs.get('threshold_value', ''),
                          kwargs.get('current_value', ''), now))
                    conn.commit()
                    logger.info(f'创建预警: {alert_type} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_active_alerts(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM personalization_alerts WHERE user_id = ? AND status = ?'
                params = [user_id, 'active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                alerts = cursor.fetchall()
                return {'success': True, 'alerts': [dict(a) for a in alerts]}
        except Exception as e:
            logger.error(f'获取活动预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, action: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM personalization_alerts WHERE alert_id = ?', (alert_id,))
                    user = cursor.fetchone()
                    if not user:
                        return {'success': False, 'error': '预警不存在'}
                    cursor.execute('UPDATE personalization_alerts SET status = ? WHERE alert_id = ?', ('resolved', alert_id))
                    cursor.execute('''
                        INSERT INTO alert_history (alert_id, user_id, action, action_result, action_time)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (alert_id, user[0], action, kwargs.get('action_result', ''), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'处理预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_history(self, user_id: int, education_type: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM personalization_alerts WHERE user_id = ? AND status = ?'
                params = [user_id, 'resolved']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = cursor.fetchall()
                return {'success': True, 'alerts': [dict(a) for a in alerts], 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_personalization_stats(self, user_id: int = None, education_type: str = None,
                                   time_range: str = 'all') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}

                if user_id:
                    cursor.execute('SELECT COUNT(*) as cnt FROM user_profiles WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['profile_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM adaptive_learning WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['adaptive_learning_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalized_assessment WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['assessment_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalized_feedback WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['feedback_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM learning_paths WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['path_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalization_alerts WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    stats['alert_count'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT AVG(progress) as avg FROM learning_paths WHERE user_id = ?' + (' AND education_type = ?' if education_type else ''),
                                  [user_id] + ([education_type] if education_type else []))
                    avg_progress = cursor.fetchone()['avg']
                    stats['average_path_progress'] = round(avg_progress, 2) if avg_progress else 0

                    cursor.execute('SELECT AVG(score) as avg FROM assessment_results WHERE user_id = ?', (user_id,))
                    avg_score = cursor.fetchone()['avg']
                    stats['average_assessment_score'] = round(avg_score, 2) if avg_score else 0
                else:
                    cursor.execute('SELECT COUNT(*) as cnt FROM user_profiles' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_profiles'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM adaptive_learning' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_adaptive_learning'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalized_assessment' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_assessments'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalized_feedback' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_feedbacks'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM learning_paths' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_paths'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT COUNT(*) as cnt FROM personalization_alerts' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    stats['total_alerts'] = cursor.fetchone()['cnt']

                    cursor.execute('SELECT AVG(progress) as avg FROM learning_paths' + (' WHERE education_type = ?' if education_type else ''),
                                  [education_type] if education_type else [])
                    avg_progress = cursor.fetchone()['avg']
                    stats['overall_average_progress'] = round(avg_progress, 2) if avg_progress else 0

                    cursor.execute('SELECT AVG(score) as avg FROM assessment_results', ())
                    avg_score = cursor.fetchone()['avg']
                    stats['overall_average_score'] = round(avg_score, 2) if avg_score else 0

                stats['time_range'] = time_range
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}
