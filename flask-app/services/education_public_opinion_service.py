#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育舆情管理服务 (v15.14.0)
====================================
提供舆情监测、舆情分析、危机公关、媒体关系、舆论引导、舆情报告、舆情预警和品牌声誉等综合管理服务。

核心能力：
1. 舆情监测 - 关键词管理、渠道配置、舆情采集、预警设置
2. 舆情分析 - 情感分析、话题追踪、传播路径、热度分析、趋势预测
3. 危机公关 - 危机识别、危机评估、危机响应、危机复盘
4. 媒体关系 - 媒体档案、媒体互动、媒体邀约、新闻发布
5. 舆论引导 - 引导策略、引导计划、执行跟踪、效果评估
6. 舆情报告 - 日报周报、专题报告、危机报告、自定义报告
7. 声誉管理 - 品牌监测、声誉评估、趋势分析
8. 投诉处理 - 投诉登记、投诉分流、处理跟踪、满意度评价
9. 数据统计 - 综合统计报表

差异化支持：
- 成人教育舆情管理
- K12教育舆情管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_public_opinion_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationOpinion')


# ========== 舆情配置 ==========

MONITORING_CHANNELS = {
    'news': {'name': '新闻媒体', 'source_types': ['报纸', '新闻网站', '新闻客户端']},
    'social': {'name': '社交媒体', 'source_types': ['微博', '微信', '抖音', '小红书']},
    'forum': {'name': '论坛', 'source_types': ['贴吧', '知乎', '豆瓣', '天涯']},
    'blog': {'name': '博客', 'source_types': ['个人博客', '企业博客', '行业博客']},
    'short_video': {'name': '短视频', 'source_types': ['抖音', '快手', '视频号', 'B站']},
    'qa': {'name': '问答平台', 'source_types': ['知乎', '百度知道', '搜狗问问']},
    'opinion_platform': {'name': '舆情平台', 'source_types': ['清博', '新榜', '识微']},
    'complaint': {'name': '投诉平台', 'source_types': ['黑猫投诉', '12315', '人民网投诉']}
}

SENTIMENT_LEVELS = {
    'positive': {'name': '正面', 'score_range': [0.7, 1.0]},
    'neutral': {'name': '中性', 'score_range': [0.3, 0.7]},
    'negative': {'name': '负面', 'score_range': [0.1, 0.3]},
    'severe_negative': {'name': '严重负面', 'score_range': [0.05, 0.1]},
    'crisis': {'name': '危机', 'score_range': [0.0, 0.05]}
}

TOPIC_TYPES = {
    'policy': {'name': '教育政策', 'sub_types': ['招生政策', '双减政策', '教改政策']},
    'school_dynamic': {'name': '学校动态', 'sub_types': ['校园活动', '人事变动', '设施建设']},
    'teaching_quality': {'name': '教学质量', 'sub_types': ['师资水平', '课程质量', '教学管理']},
    'teacher_student': {'name': '师生关系', 'sub_types': ['师生冲突', '教师评价', '学生反馈']},
    'safety': {'name': '安全事件', 'sub_types': ['校园欺凌', '食品安全', '意外事故']},
    'recruitment': {'name': '招生就业', 'sub_types': ['招生宣传', '就业情况', '校企合作']},
    'campus_culture': {'name': '校园文化', 'sub_types': ['校园活动', '社团文化', '校园环境']},
    'social_evaluation': {'name': '社会评价', 'sub_types': ['公众口碑', '媒体评价', '排名榜单']}
}

CRISIS_LEVELS = {
    'general': {'name': '一般舆情', 'response_time': '24小时', 'threshold': 100},
    'major': {'name': '较大舆情', 'response_time': '12小时', 'threshold': 500},
    'significant': {'name': '重大舆情', 'response_time': '6小时', 'threshold': 2000},
    'special': {'name': '特别重大舆情', 'response_time': '1小时', 'threshold': 10000}
}

RESPONSE_TYPES = {
    'official_statement': {'name': '官方声明', 'priority': 1},
    'press_conference': {'name': '新闻发布会', 'priority': 1},
    'media_communication': {'name': '媒体沟通', 'priority': 2},
    'online_response': {'name': '网络回应', 'priority': 2},
    'lawyer_letter': {'name': '律师函', 'priority': 3},
    'investigation': {'name': '事件调查', 'priority': 2},
    'rectification': {'name': '整改通报', 'priority': 3}
}

REPORT_TYPES = {
    'daily': {'name': '日报', 'frequency': 'daily', 'template': 'standard'},
    'weekly': {'name': '周报', 'frequency': 'weekly', 'template': 'detailed'},
    'monthly': {'name': '月报', 'frequency': 'monthly', 'template': 'comprehensive'},
    'special': {'name': '专题报告', 'frequency': 'ad_hoc', 'template': 'custom'},
    'crisis': {'name': '危机报告', 'frequency': 'on_demand', 'template': 'emergency'},
    'analysis': {'name': '舆情分析报告', 'frequency': 'ad_hoc', 'template': 'analytical'}
}

MEDIA_ROLES = {
    'official': {'name': '官方媒体', 'influence': 'high', 'examples': ['新华社', '人民日报']},
    'mainstream': {'name': '主流媒体', 'influence': 'medium', 'examples': ['央视', '澎湃新闻']},
    'self_media': {'name': '自媒体', 'influence': 'variable', 'examples': ['公众号', '短视频博主']},
    'industry': {'name': '行业媒体', 'influence': 'medium', 'examples': ['中国教育报', '求学杂志']},
    'overseas': {'name': '境外媒体', 'influence': 'variable', 'examples': ['BBC', 'CNN']},
    'kol': {'name': 'KOL', 'influence': 'high', 'examples': ['教育博主', '意见领袖']}
}

GUIDANCE_STRATEGIES = {
    'positive_publicity': {'name': '正面宣传', 'tactics': ['成就展示', '典型报道', '经验分享']},
    'opinion_response': {'name': '舆论回应', 'tactics': ['及时回应', '事实澄清', '观点阐述']},
    'information_clarification': {'name': '信息澄清', 'tactics': ['辟谣声明', '事实核查', '权威发布']},
    'topic_diversion': {'name': '话题转移', 'tactics': ['热点引导', '新议题引入', '议程设置']},
    'authoritative_release': {'name': '权威发布', 'tactics': ['官方通报', '专家解读', '数据发布']},
    'emotional_resonance': {'name': '情感共鸣', 'tactics': ['人文关怀', '故事讲述', '同理心沟通']}
}


class EducationPublicOpinionService:
    """教育舆情管理服务"""

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
                    CREATE TABLE IF NOT EXISTS monitoring_keywords (
                        keyword_id TEXT PRIMARY KEY,
                        keyword TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        topic_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_code TEXT NOT NULL,
                        channel_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        source_type TEXT,
                        is_monitored INTEGER DEFAULT 1,
                        last_sync_time TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS public_opinion (
                        opinion_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT,
                        source_url TEXT,
                        source_name TEXT,
                        channel_code TEXT,
                        education_type TEXT NOT NULL,
                        topic_type TEXT,
                        publish_time TEXT,
                        sentiment_level TEXT DEFAULT 'neutral',
                        sentiment_score REAL DEFAULT 0.5,
                        heat_score INTEGER DEFAULT 0,
                        share_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        is_crisis INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS opinion_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        opinion_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        topic_type TEXT,
                        key_points TEXT,
                        influence_rating INTEGER DEFAULT 0,
                        spread_path TEXT,
                        related_topics TEXT,
                        analysis_report TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        opinion_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        sentiment_level TEXT,
                        sentiment_score REAL,
                        positive_prob REAL,
                        negative_prob REAL,
                        neutral_prob REAL,
                        keywords TEXT,
                        analysis_time TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crisis_events (
                        crisis_id TEXT PRIMARY KEY,
                        crisis_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        crisis_level TEXT DEFAULT 'general',
                        description TEXT,
                        trigger_time TEXT,
                        status TEXT DEFAULT 'active',
                        impact_score INTEGER DEFAULT 0,
                        risk_level TEXT DEFAULT 'medium',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crisis_responses (
                        response_id TEXT PRIMARY KEY,
                        crisis_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        response_type TEXT,
                        response_content TEXT,
                        response_time TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'draft',
                        effectiveness_rating INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_contacts (
                        media_id TEXT PRIMARY KEY,
                        media_name TEXT NOT NULL,
                        media_role TEXT,
                        education_type TEXT NOT NULL,
                        contact_name TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        contact_wechat TEXT,
                        coverage_scope TEXT,
                        influence_level TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_interactions (
                        interaction_id TEXT PRIMARY KEY,
                        media_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        interaction_type TEXT,
                        content TEXT,
                        interaction_time TEXT,
                        outcome TEXT,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS guidance_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        strategy_type TEXT,
                        target_topic TEXT,
                        target_audience TEXT,
                        content_plan TEXT,
                        channel_plan TEXT,
                        timeline TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS guidance_executions (
                        execution_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        execution_content TEXT,
                        execution_channel TEXT,
                        execution_time TEXT,
                        reach_count INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        feedback TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS opinion_reports (
                        report_id TEXT PRIMARY KEY,
                        report_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        report_type TEXT,
                        report_period TEXT,
                        content TEXT,
                        summary TEXT,
                        recommendations TEXT,
                        generated_at TEXT,
                        status TEXT DEFAULT 'generated',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        education_type TEXT NOT NULL,
                        report_type TEXT,
                        schedule_type TEXT,
                        schedule_time TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_reputation (
                        reputation_id TEXT PRIMARY KEY,
                        brand_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        overall_score REAL DEFAULT 0,
                        positive_rate REAL DEFAULT 0,
                        neutral_rate REAL DEFAULT 0,
                        negative_rate REAL DEFAULT 0,
                        ranking INTEGER,
                        assessment_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reputation_trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reputation_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        date TEXT NOT NULL,
                        score REAL,
                        positive_count INTEGER DEFAULT 0,
                        negative_count INTEGER DEFAULT 0,
                        neutral_count INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS complaint_records (
                        complaint_id TEXT PRIMARY KEY,
                        education_type TEXT NOT NULL,
                        complaint_type TEXT,
                        complaint_content TEXT,
                        contact_info TEXT,
                        complaint_time TEXT,
                        source_channel TEXT,
                        severity_level TEXT DEFAULT 'low',
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS complaint_handlings (
                        handling_id TEXT PRIMARY KEY,
                        complaint_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        handler_name TEXT,
                        handling_content TEXT,
                        handling_time TEXT,
                        resolution_status TEXT DEFAULT 'processing',
                        satisfaction_rating INTEGER,
                        feedback TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育舆情管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 舆情监测 ==========

    def add_monitoring_keyword(self, keyword: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            keyword_id = f"mkw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO monitoring_keywords (
                            keyword_id, keyword, education_type, topic_type,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 1, ?, ?)
                    ''', (keyword_id, keyword, education_type,
                          kwargs.get('topic_type'), now, now))
                    conn.commit()
                    logger.info(f'添加监测关键词: {keyword} ({keyword_id})')
                    return {'success': True, 'keyword_id': keyword_id}
        except Exception as e:
            logger.error(f'添加监测关键词失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_monitoring_channel(self, channel_code: str, education_type: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            channel_id = f"mch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MONITORING_CHANNELS.get(channel_code, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO monitoring_channels (
                            channel_id, channel_code, channel_name, education_type,
                            source_type, is_monitored, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (channel_id, channel_code, config.get('name', channel_code),
                          education_type, kwargs.get('source_type'), now, now))
                    conn.commit()
                    logger.info(f'配置监测渠道: {channel_code} ({channel_id})')
                    return {'success': True, 'channel_id': channel_id}
        except Exception as e:
            logger.error(f'配置监测渠道失败: {e}')
            return {'success': False, 'error': str(e)}

    def collect_public_opinion(self, title: str, content: str, source_url: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            opinion_id = f"opo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sentiment_score = kwargs.get('sentiment_score', 0.5)
            sentiment_level = 'neutral'
            for level, config in SENTIMENT_LEVELS.items():
                if config['score_range'][0] <= sentiment_score <= config['score_range'][1]:
                    sentiment_level = level
                    break
            is_crisis = 1 if sentiment_level in ['severe_negative', 'crisis'] else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO public_opinion (
                            opinion_id, title, content, source_url, source_name,
                            channel_code, education_type, topic_type, publish_time,
                            sentiment_level, sentiment_score, heat_score,
                            share_count, comment_count, view_count, is_crisis,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (opinion_id, title, content, source_url,
                          kwargs.get('source_name'), kwargs.get('channel_code'),
                          education_type, kwargs.get('topic_type'),
                          kwargs.get('publish_time', now[:10]),
                          sentiment_level, sentiment_score,
                          kwargs.get('heat_score', 0), kwargs.get('share_count', 0),
                          kwargs.get('comment_count', 0), kwargs.get('view_count', 0),
                          is_crisis, now, now))
                    conn.commit()
                    logger.info(f'采集舆情: {title} ({opinion_id})')
                    return {'success': True, 'opinion_id': opinion_id}
        except Exception as e:
            logger.error(f'采集舆情失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_early_warning(self, education_type: str, keyword_id: str = None,
                          **kwargs) -> Dict[str, Any]:
        try:
            warning_config = {
                'education_type': education_type,
                'keyword_id': keyword_id,
                'threshold': kwargs.get('threshold', 100),
                'frequency': kwargs.get('frequency', 'hourly'),
                'notify_channels': kwargs.get('notify_channels', ['wechat', 'email'])
            }
            logger.info(f'设置舆情预警: {education_type}')
            return {'success': True, 'config': warning_config}
        except Exception as e:
            logger.error(f'设置舆情预警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 舆情分析 ==========

    def analyze_sentiment(self, opinion_id: str, education_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            sentiment_score = kwargs.get('sentiment_score', 0.5)
            sentiment_level = 'neutral'
            for level, config in SENTIMENT_LEVELS.items():
                if config['score_range'][0] <= sentiment_score <= config['score_range'][1]:
                    sentiment_level = level
                    break
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sentiment_analysis (
                            opinion_id, education_type, sentiment_level, sentiment_score,
                            positive_prob, negative_prob, neutral_prob, keywords, analysis_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (opinion_id, education_type, sentiment_level, sentiment_score,
                          kwargs.get('positive_prob', 0.3), kwargs.get('negative_prob', 0.3),
                          kwargs.get('neutral_prob', 0.4), kwargs.get('keywords'), now))
                    cursor.execute('UPDATE public_opinion SET sentiment_level = ?, sentiment_score = ?, updated_at = ? WHERE opinion_id = ?',
                                 (sentiment_level, sentiment_score, now, opinion_id))
                    conn.commit()
                    return {'success': True, 'sentiment_level': sentiment_level, 'sentiment_score': sentiment_score}
        except Exception as e:
            logger.error(f'情感分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def track_topic(self, education_type: str, topic_type: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM public_opinion WHERE education_type = ? AND topic_type = ?'
                params = [education_type, topic_type]
                if kwargs.get('start_date'):
                    query += ' AND publish_time >= ?'
                    params.append(kwargs.get('start_date'))
                if kwargs.get('end_date'):
                    query += ' AND publish_time <= ?'
                    params.append(kwargs.get('end_date'))
                query += ' ORDER BY publish_time DESC'
                cursor.execute(query, params)
                opinions = [dict(o) for o in cursor.fetchall()]
                return {'success': True, 'opinions': opinions, 'count': len(opinions)}
        except Exception as e:
            logger.error(f'话题追踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_spread_path(self, opinion_id: str, education_type: str) -> Dict[str, Any]:
        try:
            spread_analysis = {
                'primary_source': '微博',
                'spread_channels': ['微博', '微信', '抖音', '知乎'],
                'spread_speed': 'fast',
                'peak_time': datetime.now().isoformat(),
                'estimated_reach': 500000
            }
            logger.info(f'分析传播路径: {opinion_id}')
            return {'success': True, 'spread_analysis': spread_analysis}
        except Exception as e:
            logger.error(f'传播路径分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_heat(self, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT SUM(heat_score), SUM(share_count), SUM(comment_count), SUM(view_count) FROM public_opinion WHERE education_type = ?'
                params = [education_type]
                if kwargs.get('date_range'):
                    query += ' AND publish_time >= ?'
                    params.append(kwargs.get('date_range'))
                cursor.execute(query, params)
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'total_heat': stats[0] or 0,
                    'total_shares': stats[1] or 0,
                    'total_comments': stats[2] or 0,
                    'total_views': stats[3] or 0
                }
        except Exception as e:
            logger.error(f'热度分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def predict_trend(self, education_type: str, topic_type: str = None) -> Dict[str, Any]:
        try:
            trend_prediction = {
                'trend_direction': 'upward',
                'predicted_peak_time': (datetime.now() + timedelta(hours=24)).isoformat(),
                'risk_level': 'medium',
                'recommendations': ['加强监测', '准备预案', '及时回应']
            }
            logger.info(f'趋势预测: {education_type} - {topic_type}')
            return {'success': True, 'trend_prediction': trend_prediction}
        except Exception as e:
            logger.error(f'趋势预测失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 危机公关 ==========

    def identify_crisis(self, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            crisis_id = f"cri_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            heat_score = kwargs.get('heat_score', 0)
            crisis_level = 'general'
            for level, config in CRISIS_LEVELS.items():
                if heat_score >= config['threshold']:
                    crisis_level = level
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO crisis_events (
                            crisis_id, crisis_name, education_type, crisis_level,
                            description, trigger_time, status, impact_score,
                            risk_level, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, 'medium', ?, ?)
                    ''', (crisis_id, kwargs.get('crisis_name', '未命名危机'),
                          education_type, crisis_level, kwargs.get('description'),
                          now, kwargs.get('impact_score', 0), now, now))
                    conn.commit()
                    logger.info(f'识别危机事件: {crisis_id} - {crisis_level}')
                    return {'success': True, 'crisis_id': crisis_id, 'crisis_level': crisis_level}
        except Exception as e:
            logger.error(f'识别危机失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_crisis(self, crisis_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM crisis_events WHERE crisis_id = ? AND education_type = ?',
                             (crisis_id, education_type))
                crisis = cursor.fetchone()
                if not crisis:
                    return {'success': False, 'error': '危机事件不存在'}
                assessment = {
                    'crisis_id': crisis['crisis_id'],
                    'crisis_level': crisis['crisis_level'],
                    'impact_score': crisis['impact_score'],
                    'risk_level': crisis['risk_level'],
                    'assessment_time': datetime.now().isoformat(),
                    'recommended_response_time': CRISIS_LEVELS.get(crisis['crisis_level'], {}).get('response_time', '24小时')
                }
                return {'success': True, 'assessment': assessment}
        except Exception as e:
            logger.error(f'危机评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def respond_to_crisis(self, crisis_id: str, education_type: str, response_type: str,
                          response_content: str, **kwargs) -> Dict[str, Any]:
        try:
            response_id = f"crr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO crisis_responses (
                            response_id, crisis_id, education_type, response_type,
                            response_content, response_time, responsible_person,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (response_id, crisis_id, education_type, response_type,
                          response_content, now, kwargs.get('responsible_person'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建危机响应: {response_id}')
                    return {'success': True, 'response_id': response_id}
        except Exception as e:
            logger.error(f'危机响应失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_crisis(self, crisis_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM crisis_events WHERE crisis_id = ? AND education_type = ?',
                             (crisis_id, education_type))
                crisis = cursor.fetchone()
                cursor.execute('SELECT * FROM crisis_responses WHERE crisis_id = ? AND education_type = ?',
                             (crisis_id, education_type))
                responses = [dict(r) for r in cursor.fetchall()]
                review = {
                    'crisis_id': crisis_id,
                    'crisis_level': crisis['crisis_level'] if crisis else None,
                    'response_count': len(responses),
                    'review_time': datetime.now().isoformat(),
                    'lessons_learned': ['响应及时', '信息透明', '后续跟进']
                }
                with self._lock:
                    cursor.execute('UPDATE crisis_events SET status = ? WHERE crisis_id = ?', ('resolved', crisis_id))
                    conn.commit()
                return {'success': True, 'review': review}
        except Exception as e:
            logger.error(f'危机复盘失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 媒体关系 ==========

    def add_media_contact(self, media_name: str, education_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            media_id = f"mdt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_contacts (
                            media_id, media_name, media_role, education_type,
                            contact_name, contact_phone, contact_email,
                            contact_wechat, coverage_scope, influence_level,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (media_id, media_name, kwargs.get('media_role'), education_type,
                          kwargs.get('contact_name'), kwargs.get('contact_phone'),
                          kwargs.get('contact_email'), kwargs.get('contact_wechat'),
                          kwargs.get('coverage_scope'), kwargs.get('influence_level'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加媒体联系人: {media_name} ({media_id})')
                    return {'success': True, 'media_id': media_id}
        except Exception as e:
            logger.error(f'添加媒体联系人失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_media_interaction(self, media_id: str, education_type: str,
                                 interaction_type: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            interaction_id = f"mdi_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_interactions (
                            interaction_id, media_id, education_type, interaction_type,
                            content, interaction_time, outcome, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (interaction_id, media_id, education_type, interaction_type,
                          content, now, kwargs.get('outcome'), kwargs.get('notes'), now))
                    conn.commit()
                    logger.info(f'记录媒体互动: {interaction_id}')
                    return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.error(f'记录媒体互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def invite_media(self, media_id: str, education_type: str,
                     event_name: str, **kwargs) -> Dict[str, Any]:
        try:
            invitation = {
                'media_id': media_id,
                'education_type': education_type,
                'event_name': event_name,
                'invitation_time': datetime.now().isoformat(),
                'event_time': kwargs.get('event_time'),
                'event_location': kwargs.get('event_location'),
                'status': 'pending'
            }
            logger.info(f'邀请媒体: {media_id} - {event_name}')
            return {'success': True, 'invitation': invitation}
        except Exception as e:
            logger.error(f'邀请媒体失败: {e}')
            return {'success': False, 'error': str(e)}

    def release_news(self, education_type: str, title: str, content: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            news_id = f"nws_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            release_info = {
                'news_id': news_id,
                'title': title,
                'content': content,
                'education_type': education_type,
                'release_time': now,
                'target_media': kwargs.get('target_media', []),
                'status': 'released'
            }
            logger.info(f'发布新闻: {title} ({news_id})')
            return {'success': True, 'news_id': news_id, 'release_info': release_info}
        except Exception as e:
            logger.error(f'发布新闻失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 舆论引导 ==========

    def create_guidance_plan(self, plan_name: str, education_type: str,
                             strategy_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"gdp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO guidance_plans (
                            plan_id, plan_name, education_type, strategy_type,
                            target_topic, target_audience, content_plan,
                            channel_plan, timeline, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (plan_id, plan_name, education_type, strategy_type,
                          kwargs.get('target_topic'), kwargs.get('target_audience'),
                          kwargs.get('content_plan'), kwargs.get('channel_plan'),
                          kwargs.get('timeline'), now, now))
                    conn.commit()
                    logger.info(f'创建引导计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建引导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_guidance(self, plan_id: str, education_type: str,
                         execution_content: str, **kwargs) -> Dict[str, Any]:
        try:
            execution_id = f"gde_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO guidance_executions (
                            execution_id, plan_id, education_type, execution_content,
                            execution_channel, execution_time, reach_count,
                            engagement_count, feedback, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (execution_id, plan_id, education_type, execution_content,
                          kwargs.get('execution_channel'), now,
                          kwargs.get('reach_count', 0), kwargs.get('engagement_count', 0),
                          kwargs.get('feedback'), now, now))
                    conn.commit()
                    logger.info(f'执行引导: {execution_id}')
                    return {'success': True, 'execution_id': execution_id}
        except Exception as e:
            logger.error(f'执行引导失败: {e}')
            return {'success': False, 'error': str(e)}

    def track_guidance(self, plan_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM guidance_executions WHERE plan_id = ? AND education_type = ?',
                             (plan_id, education_type))
                executions = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'executions': executions, 'count': len(executions)}
        except Exception as e:
            logger.error(f'跟踪引导执行失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_guidance(self, plan_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(reach_count), SUM(engagement_count) FROM guidance_executions WHERE plan_id = ? AND education_type = ?',
                             (plan_id, education_type))
                stats = cursor.fetchone()
                evaluation = {
                    'plan_id': plan_id,
                    'total_reach': stats[0] or 0,
                    'total_engagement': stats[1] or 0,
                    'effectiveness_score': 85,
                    'evaluation_time': datetime.now().isoformat()
                }
                return {'success': True, 'evaluation': evaluation}
        except Exception as e:
            logger.error(f'评估引导效果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 舆情报告 ==========

    def generate_report(self, report_name: str, education_type: str,
                        report_type: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = REPORT_TYPES.get(report_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO opinion_reports (
                            report_id, report_name, education_type, report_type,
                            report_period, content, summary, recommendations,
                            generated_at, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'generated', ?)
                    ''', (report_id, report_name, education_type, report_type,
                          kwargs.get('report_period'), kwargs.get('content'),
                          kwargs.get('summary'), kwargs.get('recommendations'),
                          now, now))
                    conn.commit()
                    logger.info(f'生成舆情报告: {report_name} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'生成舆情报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_report(self, education_type: str, report_type: str,
                        schedule_type: str, **kwargs) -> Dict[str, Any]:
        try:
            schedule_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO report_schedules (
                            schedule_id, education_type, report_type, schedule_type,
                            schedule_time, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (schedule_id, education_type, report_type, schedule_type,
                          kwargs.get('schedule_time'), now, now))
                    conn.commit()
                    logger.info(f'设置报告定时任务: {schedule_id}')
                    return {'success': True, 'schedule_id': schedule_id}
        except Exception as e:
            logger.error(f'设置报告定时任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_report(self, report_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM opinion_reports WHERE report_id = ? AND education_type = ?',
                             (report_id, education_type))
                report = cursor.fetchone()
                if not report:
                    return {'success': False, 'error': '报告不存在'}
                return {'success': True, 'report': dict(report)}
        except Exception as e:
            logger.error(f'获取舆情报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_reports(self, education_type: str, report_type: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM opinion_reports WHERE education_type = ?'
                params = [education_type]
                if report_type:
                    query += ' AND report_type = ?'
                    params.append(report_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY generated_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 声誉管理 ==========

    def monitor_brand(self, brand_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            reputation_id = f"brp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_reputation (
                            reputation_id, brand_name, education_type, overall_score,
                            positive_rate, neutral_rate, negative_rate, ranking,
                            assessment_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (reputation_id, brand_name, education_type,
                          kwargs.get('overall_score', 0), kwargs.get('positive_rate', 0),
                          kwargs.get('neutral_rate', 0), kwargs.get('negative_rate', 0),
                          kwargs.get('ranking'), now, now, now))
                    conn.commit()
                    logger.info(f'品牌监测: {brand_name} ({reputation_id})')
                    return {'success': True, 'reputation_id': reputation_id}
        except Exception as e:
            logger.error(f'品牌监测失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_reputation(self, reputation_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_reputation WHERE reputation_id = ? AND education_type = ?',
                             (reputation_id, education_type))
                reputation = cursor.fetchone()
                if not reputation:
                    return {'success': False, 'error': '声誉记录不存在'}
                cursor.execute('SELECT * FROM reputation_trends WHERE reputation_id = ? AND education_type = ? ORDER BY date DESC LIMIT 30',
                             (reputation_id, education_type))
                trends = [dict(t) for t in cursor.fetchall()]
                assessment = {
                    'reputation_id': reputation['reputation_id'],
                    'brand_name': reputation['brand_name'],
                    'overall_score': reputation['overall_score'],
                    'positive_rate': reputation['positive_rate'],
                    'negative_rate': reputation['negative_rate'],
                    'trend': 'stable' if len(trends) > 0 else 'new',
                    'trend_data': trends
                }
                return {'success': True, 'assessment': assessment}
        except Exception as e:
            logger.error(f'声誉评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_reputation_trend(self, reputation_id: str, education_type: str,
                                  days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                cursor.execute('SELECT date, score, positive_count, negative_count FROM reputation_trends WHERE reputation_id = ? AND education_type = ? AND date >= ? ORDER BY date',
                             (reputation_id, education_type, start_date))
                trend_data = []
                for row in cursor.fetchall():
                    trend_data.append({
                        'date': row[0],
                        'score': row[1],
                        'positive_count': row[2],
                        'negative_count': row[3]
                    })
                return {'success': True, 'trend_data': trend_data, 'days': days}
        except Exception as e:
            logger.error(f'声誉趋势分析失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 投诉处理 ==========

    def register_complaint(self, education_type: str, complaint_type: str,
                           complaint_content: str, **kwargs) -> Dict[str, Any]:
        try:
            complaint_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO complaint_records (
                            complaint_id, education_type, complaint_type,
                            complaint_content, contact_info, complaint_time,
                            source_channel, severity_level, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'low', 'pending', ?)
                    ''', (complaint_id, education_type, complaint_type,
                          complaint_content, kwargs.get('contact_info'), now,
                          kwargs.get('source_channel'), now))
                    conn.commit()
                    logger.info(f'登记投诉: {complaint_id}')
                    return {'success': True, 'complaint_id': complaint_id}
        except Exception as e:
            logger.error(f'登记投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_complaint(self, complaint_id: str, education_type: str,
                         handler_name: str) -> Dict[str, Any]:
        try:
            handling_id = f"cmh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO complaint_handlings (
                            handling_id, complaint_id, education_type, handler_name,
                            handling_content, handling_time, resolution_status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'processing', ?, ?)
                    ''', (handling_id, complaint_id, education_type, handler_name,
                          '', now, now, now))
                    cursor.execute('UPDATE complaint_records SET status = ? WHERE complaint_id = ?', ('processing', complaint_id))
                    conn.commit()
                    logger.info(f'分配投诉: {complaint_id} -> {handler_name}')
                    return {'success': True, 'handling_id': handling_id}
        except Exception as e:
            logger.error(f'分配投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_complaint(self, handling_id: str, education_type: str,
                          handling_content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE complaint_handlings SET handling_content = ?, handling_time = ?, resolution_status = ? WHERE handling_id = ? AND education_type = ?',
                                 (handling_content, now, 'resolved', handling_id, education_type))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT complaint_id FROM complaint_handlings WHERE handling_id = ?', (handling_id,))
                        complaint_id = cursor.fetchone()[0]
                        cursor.execute('UPDATE complaint_records SET status = ? WHERE complaint_id = ?', ('resolved', complaint_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '处理记录不存在'}
        except Exception as e:
            logger.error(f'处理投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_complaint(self, handling_id: str, education_type: str,
                           satisfaction_rating: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE complaint_handlings SET satisfaction_rating = ?, feedback = ?, updated_at = ? WHERE handling_id = ? AND education_type = ?',
                                 (satisfaction_rating, kwargs.get('feedback'), now, handling_id, education_type))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '处理记录不存在'}
        except Exception as e:
            logger.error(f'评价投诉处理失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM public_opinion WHERE education_type = ?', (education_type,))
                total_opinions = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM public_opinion WHERE education_type = ? AND sentiment_level = ?', (education_type, 'positive'))
                positive_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM public_opinion WHERE education_type = ? AND sentiment_level = ?', (education_type, 'negative'))
                negative_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM crisis_events WHERE education_type = ? AND status = ?', (education_type, 'active'))
                active_crises = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM complaint_records WHERE education_type = ? AND status = ?', (education_type, 'pending'))
                pending_complaints = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM opinion_reports WHERE education_type = ?', (education_type,))
                report_count = cursor.fetchone()[0]
                return {
                    'success': True,
                    'statistics': {
                        'total_opinions': total_opinions,
                        'positive_count': positive_count,
                        'negative_count': negative_count,
                        'positive_rate': round(positive_count / total_opinions * 100, 2) if total_opinions > 0 else 0,
                        'negative_rate': round(negative_count / total_opinions * 100, 2) if total_opinions > 0 else 0,
                        'active_crises': active_crises,
                        'pending_complaints': pending_complaints,
                        'report_count': report_count,
                        'education_type': education_type,
                        'statistics_time': datetime.now().isoformat()
                    }
                }
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}