#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智能客服服务 (v15.15.0)
====================================
提供AI智能客服、智能问答、知识库管理、多轮对话、情感分析、工单管理、智能路由、客服质检等综合服务。

核心能力：
1. AI智能客服 - 智能问答、多轮对话、上下文理解
2. 知识库管理 - FAQ管理、文档知识、案例知识、流程知识
3. 多轮对话 - 对话流程、上下文对话、知识引导
4. 情感分析 - 情感识别、情绪监测、客户满意度
5. 工单管理 - 工单创建、分配、处理、关闭
6. 智能路由 - 技能路由、优先级路由、业务路由
7. 客服质检 - 响应速度、服务态度、问题解决
8. 客服绩效 - 绩效评估、服务指标、工作统计

差异化支持：
- 成人教育 - 职业培训、学历提升、继续教育
- K12教育 - 中小学教育、学科辅导、素质教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_customer_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationCustomerService')


# ========== 服务配置 ==========

# 服务渠道
SERVICE_CHANNELS = {
    'online': {'name': '在线客服', 'icon': '💬', 'response_time': '30秒'},
    'phone': {'name': '电话客服', 'icon': '📞', 'response_time': '1分钟'},
    'email': {'name': '邮件客服', 'icon': '📧', 'response_time': '24小时'},
    'wechat': {'name': '微信客服', 'icon': '💚', 'response_time': '5分钟'},
    'app': {'name': 'APP客服', 'icon': '📱', 'response_time': '30秒'},
    'robot': {'name': '机器人客服', 'icon': '🤖', 'response_time': '5秒'},
    'self_service': {'name': '自助服务', 'icon': '🔧', 'response_time': '即时'}
}

# 问题类型
QUESTION_TYPES = {
    'faq': {'name': '常见问题', 'priority': 'low', 'auto_reply': True},
    'business': {'name': '业务咨询', 'priority': 'medium', 'auto_reply': False},
    'tech': {'name': '技术支持', 'priority': 'high', 'auto_reply': False},
    'complaint': {'name': '投诉建议', 'priority': 'high', 'auto_reply': False},
    'booking': {'name': '预约服务', 'priority': 'medium', 'auto_reply': True},
    'query': {'name': '信息查询', 'priority': 'low', 'auto_reply': True},
    'guide': {'name': '操作指导', 'priority': 'medium', 'auto_reply': True},
    'emergency': {'name': '紧急求助', 'priority': 'urgent', 'auto_reply': False}
}

# 知识类型
KNOWLEDGE_TYPES = {
    'faq': {'name': 'FAQ', 'searchable': True, 'category': 'basic'},
    'document': {'name': '文档知识', 'searchable': True, 'category': 'advanced'},
    'case': {'name': '案例知识', 'searchable': True, 'category': 'advanced'},
    'process': {'name': '流程知识', 'searchable': True, 'category': 'basic'},
    'policy': {'name': '政策知识', 'searchable': True, 'category': 'basic'},
    'product': {'name': '产品知识', 'searchable': True, 'category': 'advanced'},
    'tech': {'name': '技术知识', 'searchable': True, 'category': 'advanced'},
    'common': {'name': '常见问题', 'searchable': True, 'category': 'basic'}
}

# 对话类型
DIALOG_TYPES = {
    'qa': {'name': '问答对话', 'turn_limit': 1},
    'task': {'name': '任务对话', 'turn_limit': 10},
    'chat': {'name': '闲聊对话', 'turn_limit': 20},
    'multi_turn': {'name': '多轮对话', 'turn_limit': 15},
    'context': {'name': '上下文对话', 'turn_limit': 25},
    'guide': {'name': '知识引导', 'turn_limit': 8}
}

# 情感级别
SENTIMENT_LEVELS = {
    'positive': {'name': '积极', 'score_range': (0.7, 1.0), 'action': '表扬'},
    'neutral': {'name': '中性', 'score_range': (0.3, 0.7), 'action': '正常处理'},
    'negative': {'name': '消极', 'score_range': (0.1, 0.3), 'action': '安抚'},
    'angry': {'name': '愤怒', 'score_range': (0.05, 0.1), 'action': '紧急处理'},
    'anxious': {'name': '焦虑', 'score_range': (0.15, 0.25), 'action': '快速响应'},
    'confused': {'name': '困惑', 'score_range': (0.2, 0.35), 'action': '详细解释'}
}

# 工单类型
TICKET_TYPES = {
    'consult': {'name': '咨询工单', 'sla_hours': 24, 'priority': 'low'},
    'complaint': {'name': '投诉工单', 'sla_hours': 4, 'priority': 'high'},
    'suggestion': {'name': '建议工单', 'sla_hours': 72, 'priority': 'low'},
    'fault': {'name': '故障工单', 'sla_hours': 1, 'priority': 'urgent'},
    'service': {'name': '服务工单', 'sla_hours': 12, 'priority': 'medium'},
    'emergency': {'name': '紧急工单', 'sla_hours': 0.5, 'priority': 'urgent'}
}

# 路由规则
ROUTING_RULES = {
    'skill': {'name': '按技能路由', 'description': '根据客服技能匹配'},
    'priority': {'name': '按优先级路由', 'description': '根据工单优先级分配'},
    'time': {'name': '按时间路由', 'description': '根据工作时间分配'},
    'region': {'name': '按区域路由', 'description': '根据客户区域分配'},
    'business': {'name': '按业务路由', 'description': '根据业务类型分配'}
}

# 质检维度
QUALITY_DIMENSIONS = {
    'response_speed': {'name': '响应速度', 'weight': 0.15, 'scale': (0, 10)},
    'service_attitude': {'name': '服务态度', 'weight': 0.2, 'scale': (0, 10)},
    'problem_solving': {'name': '问题解决', 'weight': 0.25, 'scale': (0, 10)},
    'knowledge_accuracy': {'name': '知识准确性', 'weight': 0.2, 'scale': (0, 10)},
    'communication_skill': {'name': '沟通技巧', 'weight': 0.1, 'scale': (0, 10)},
    'compliance': {'name': '合规性', 'weight': 0.1, 'scale': (0, 10)}
}


class EducationSmartCustomerService:
    """教育智能客服服务"""

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
                    CREATE TABLE IF NOT EXISTS service_channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT NOT NULL,
                        icon TEXT,
                        response_time TEXT,
                        status TEXT DEFAULT 'active',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        session_id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        customer_id INTEGER,
                        customer_name TEXT,
                        agent_id INTEGER,
                        agent_name TEXT,
                        dialog_type TEXT,
                        education_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT DEFAULT 'active',
                        sentiment_score REAL DEFAULT 0,
                        sentiment_level TEXT,
                        satisfaction_score INTEGER,
                        total_messages INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        message_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        sender_type TEXT NOT NULL,
                        sender_id INTEGER,
                        sender_name TEXT,
                        content TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        sentiment_score REAL,
                        sentiment_level TEXT,
                        timestamp TEXT,
                        is_auto_reply INTEGER DEFAULT 0,
                        knowledge_ref TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        knowledge_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        knowledge_type TEXT,
                        category_id TEXT,
                        tags TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        view_count INTEGER DEFAULT 0,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_categories (
                        category_id TEXT PRIMARY KEY,
                        category_name TEXT NOT NULL,
                        parent_id TEXT,
                        education_type TEXT,
                        sort_order INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dialog_flows (
                        flow_id TEXT PRIMARY KEY,
                        flow_name TEXT NOT NULL,
                        dialog_type TEXT,
                        education_type TEXT,
                        start_node TEXT,
                        nodes TEXT,
                        edges TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        message_id TEXT,
                        content TEXT,
                        sentiment_score REAL,
                        sentiment_level TEXT,
                        confidence REAL,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id TEXT PRIMARY KEY,
                        ticket_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        channel_id TEXT,
                        customer_id INTEGER,
                        customer_name TEXT,
                        education_type TEXT,
                        priority TEXT DEFAULT 'low',
                        status TEXT DEFAULT 'open',
                        sla_hours INTEGER DEFAULT 24,
                        created_at TEXT,
                        updated_at TEXT,
                        resolved_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ticket_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id TEXT NOT NULL,
                        agent_id INTEGER,
                        agent_name TEXT,
                        assign_time TEXT,
                        status TEXT DEFAULT 'assigned',
                        UNIQUE(ticket_id, agent_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ticket_interactions (
                        interaction_id TEXT PRIMARY KEY,
                        ticket_id TEXT NOT NULL,
                        actor_id INTEGER,
                        actor_name TEXT,
                        actor_type TEXT,
                        action TEXT NOT NULL,
                        content TEXT,
                        timestamp TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS routing_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_name TEXT NOT NULL,
                        rule_type TEXT,
                        education_type TEXT,
                        conditions TEXT,
                        actions TEXT,
                        priority INTEGER DEFAULT 100,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS routing_logs (
                        log_id TEXT PRIMARY KEY,
                        rule_id TEXT,
                        ticket_id TEXT,
                        session_id TEXT,
                        source TEXT,
                        target_agent_id INTEGER,
                        target_agent_name TEXT,
                        reason TEXT,
                        timestamp TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_inspections (
                        inspection_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        ticket_id TEXT,
                        agent_id INTEGER,
                        agent_name TEXT,
                        inspector_id INTEGER,
                        inspector_name TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inspection_results (
                        result_id TEXT PRIMARY KEY,
                        inspection_id TEXT NOT NULL,
                        dimension TEXT NOT NULL,
                        score REAL NOT NULL,
                        comment TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS customer_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        ticket_id TEXT,
                        customer_id INTEGER,
                        customer_name TEXT,
                        education_type TEXT,
                        satisfaction_score INTEGER,
                        rating INTEGER,
                        comment TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_metrics (
                        metric_id TEXT PRIMARY KEY,
                        date TEXT NOT NULL,
                        education_type TEXT,
                        channel_id TEXT,
                        total_sessions INTEGER DEFAULT 0,
                        resolved_sessions INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0,
                        avg_handle_time REAL DEFAULT 0,
                        satisfaction_rate REAL DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agent_performance (
                        perf_id TEXT PRIMARY KEY,
                        agent_id INTEGER NOT NULL,
                        agent_name TEXT,
                        education_type TEXT,
                        date TEXT NOT NULL,
                        total_tickets INTEGER DEFAULT 0,
                        resolved_tickets INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0,
                        avg_handle_time REAL DEFAULT 0,
                        satisfaction_score REAL DEFAULT 0,
                        quality_score REAL DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(agent_id, date)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auto_replies (
                        reply_id TEXT PRIMARY KEY,
                        keyword TEXT NOT NULL,
                        content TEXT NOT NULL,
                        education_type TEXT,
                        question_type TEXT,
                        priority INTEGER DEFAULT 100,
                        is_active INTEGER DEFAULT 1,
                        usage_count INTEGER DEFAULT 0,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        agent_id INTEGER NOT NULL,
                        agent_name TEXT,
                        education_type TEXT,
                        day_of_week TEXT NOT NULL,
                        start_time TEXT,
                        end_time TEXT,
                        is_on_duty INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育智能客服服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 智能问答 ==========

    def ask_question(self, customer_id: int, question: str,
                      channel_id: str = 'online', **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            question_type = self._classify_question(question, education_type)
            auto_reply = self._find_auto_reply(question, education_type)
            
            if auto_reply:
                return {'success': True, 'reply': auto_reply, 'is_auto': True,
                        'question_type': question_type, 'education_type': education_type}
            
            knowledge = self._search_knowledge(question, education_type)
            if knowledge:
                return {'success': True, 'reply': knowledge['content'], 'is_auto': False,
                        'knowledge_id': knowledge['knowledge_id'], 'question_type': question_type,
                        'education_type': education_type}
            
            session_id = self._create_session(customer_id, kwargs.get('customer_name'),
                                              channel_id, 'qa', education_type)
            return {'success': True, 'reply': '请稍候，正在为您转接人工客服...',
                    'is_auto': False, 'session_id': session_id, 'question_type': question_type,
                    'education_type': education_type}
        except Exception as e:
            logger.error(f'智能问答失败: {e}')
            return {'success': False, 'error': str(e)}

    def _classify_question(self, question: str, education_type: str) -> str:
        keywords = {
            'faq': ['什么是', '怎么', '如何', '请问', '是否'],
            'business': ['报名', '课程', '学费', '优惠', '活动'],
            'tech': ['登录', '密码', '系统', '报错', '打不开'],
            'complaint': ['投诉', '不满意', '问题', '错误', '差'],
            'booking': ['预约', '安排', '时间', '试听', '体验'],
            'query': ['查询', '查看', '进度', '状态', '结果'],
            'guide': ['操作', '步骤', '教程', '指引', '帮助'],
            'emergency': ['紧急', '立刻', '马上', '故障', '崩溃']
        }
        for q_type, kws in keywords.items():
            if any(kw in question for kw in kws):
                return q_type
        return 'faq'

    def _find_auto_reply(self, question: str, education_type: str) -> Optional[str]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT content FROM auto_replies 
                    WHERE is_active = 1 AND education_type = ? AND keyword LIKE ?
                    ORDER BY priority DESC LIMIT 1
                ''', (education_type, f'%{question[:10]}%'))
                result = cursor.fetchone()
                if result:
                    cursor.execute('UPDATE auto_replies SET usage_count = usage_count + 1 WHERE reply_id = ?',
                                 (result['reply_id'],))
                    conn.commit()
                    return result['content']
            return None
        except Exception:
            return None

    def _search_knowledge(self, query: str, education_type: str) -> Optional[Dict]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM knowledge_base 
                    WHERE is_active = 1 AND education_type = ? 
                    AND (title LIKE ? OR content LIKE ?)
                    ORDER BY view_count DESC LIMIT 1
                ''', (education_type, f'%{query}%', f'%{query}%'))
                result = cursor.fetchone()
                if result:
                    cursor.execute('UPDATE knowledge_base SET view_count = view_count + 1 WHERE knowledge_id = ?',
                                 (result['knowledge_id'],))
                    conn.commit()
                    return dict(result)
            return None
        except Exception:
            return None

    def _create_session(self, customer_id: int, customer_name: str,
                        channel_id: str, dialog_type: str, education_type: str) -> str:
        session_id = f"ses_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_sessions (
                        session_id, channel_id, customer_id, customer_name,
                        dialog_type, education_type, start_time, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                ''', (session_id, channel_id, customer_id, customer_name,
                      dialog_type, education_type, now, now))
                conn.commit()
        return session_id

    def get_qa_history(self, customer_id: int, education_type: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM chat_sessions WHERE customer_id = ?'
                params = [customer_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                sessions = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'sessions': sessions, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取问答历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识库管理 ==========

    def add_knowledge(self, title: str, content: str, knowledge_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            knowledge_id = f"kno_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_base (
                            knowledge_id, title, content, knowledge_type,
                            category_id, tags, education_type, is_active,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (knowledge_id, title, content, knowledge_type,
                          kwargs.get('category_id'), kwargs.get('tags'),
                          education_type, kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'添加知识: {title} ({knowledge_id})')
                    return {'success': True, 'knowledge_id': knowledge_id}
        except Exception as e:
            logger.error(f'添加知识失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_knowledge(self, knowledge_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'title' in kwargs:
                        updates.append('title = ?')
                        params.append(kwargs['title'])
                    if 'content' in kwargs:
                        updates.append('content = ?')
                        params.append(kwargs['content'])
                    if 'knowledge_type' in kwargs:
                        updates.append('knowledge_type = ?')
                        params.append(kwargs['knowledge_type'])
                    if 'category_id' in kwargs:
                        updates.append('category_id = ?')
                        params.append(kwargs['category_id'])
                    if 'tags' in kwargs:
                        updates.append('tags = ?')
                        params.append(kwargs['tags'])
                    if 'is_active' in kwargs:
                        updates.append('is_active = ?')
                        params.append(kwargs['is_active'])
                    params.append(knowledge_id)
                    if updates:
                        cursor.execute(f'UPDATE knowledge_base SET {", ".join(updates)}, updated_at = ? WHERE knowledge_id = ?',
                                     params + [now])
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未更新任何字段'}
        except Exception as e:
            logger.error(f'更新知识失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM knowledge_base WHERE knowledge_id = ?', (knowledge_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'删除知识: {knowledge_id}')
                        return {'success': True}
                    return {'success': False, 'error': '知识不存在'}
        except Exception as e:
            logger.error(f'删除知识失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_knowledge(self, education_type: str = None, knowledge_type: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_base WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if knowledge_type:
                    query += ' AND knowledge_type = ?'
                    params.append(knowledge_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                knowledge = [dict(k) for k in cursor.fetchall()]
                return {'success': True, 'knowledge': knowledge, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取知识列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 对话管理 ==========

    def send_message(self, session_id: str, content: str, sender_type: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sentiment = self._analyze_sentiment(content)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO chat_messages (
                            message_id, session_id, sender_type, sender_id,
                            sender_name, content, sentiment_score, sentiment_level,
                            timestamp, is_auto_reply, knowledge_ref, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (message_id, session_id, sender_type, kwargs.get('sender_id'),
                          kwargs.get('sender_name'), content, sentiment['score'],
                          sentiment['level'], now, kwargs.get('is_auto_reply', 0),
                          kwargs.get('knowledge_ref'), now))
                    cursor.execute('UPDATE chat_sessions SET total_messages = total_messages + 1 WHERE session_id = ?',
                                 (session_id,))
                    conn.commit()
                    return {'success': True, 'message_id': message_id, 'sentiment': sentiment}
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_session_messages(self, session_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC',
                             (session_id,))
                messages = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'messages': messages}
        except Exception as e:
            logger.error(f'获取会话消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE chat_sessions SET status = 'closed', end_time = ?,
                        sentiment_score = ?, sentiment_level = ?, satisfaction_score = ?
                        WHERE session_id = ? AND status = 'active'
                    ''', (now, kwargs.get('sentiment_score'), kwargs.get('sentiment_level'),
                          kwargs.get('satisfaction_score'), session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '会话状态不允许关闭'}
        except Exception as e:
            logger.error(f'关闭会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_session(self, session_id: str, target_agent_id: int,
                         target_agent_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE chat_sessions SET agent_id = ?, agent_name = ?
                        WHERE session_id = ?
                    ''', (target_agent_id, target_agent_name, session_id))
                    cursor.execute('''
                        INSERT INTO routing_logs (
                            log_id, session_id, target_agent_id, target_agent_name,
                            reason, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, '会话转接', ?, ?)
                    ''', (f"log_{uuid.uuid4().hex[:12]}", session_id, target_agent_id,
                          target_agent_name, now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'转接会话失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 情感分析 ==========

    def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        positive_words = ['好', '棒', '赞', '满意', '感谢', '不错', '优秀', '完美', '开心', '喜欢']
        negative_words = ['差', '烂', '糟糕', '不满意', '投诉', '问题', '错误', '崩溃', '急', '烦']
        angry_words = ['愤怒', '气死', '太过分', '无法忍受', '投诉', '强烈']
        anxious_words = ['着急', '焦虑', '担心', '怕', '快点', '急']
        confused_words = ['不懂', '困惑', '不清楚', '不知道', '怎么', '为什么']
        
        score = 0.5
        level = 'neutral'
        
        if any(w in content for w in angry_words):
            score = 0.07
            level = 'angry'
        elif any(w in content for w in anxious_words):
            score = 0.2
            level = 'anxious'
        elif any(w in content for w in confused_words):
            score = 0.28
            level = 'confused'
        elif any(w in content for w in negative_words):
            score = 0.2
            level = 'negative'
        elif any(w in content for w in positive_words):
            score = 0.85
            level = 'positive'
        
        return {'score': score, 'level': level, 'confidence': 0.75}

    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        try:
            result = self._analyze_sentiment(content)
            analysis_id = f"sen_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sentiment_analysis (
                        analysis_id, content, sentiment_score, sentiment_level,
                        confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (analysis_id, content[:500], result['score'], result['level'],
                      result['confidence'], now))
                conn.commit()
            return {'success': True, **result}
        except Exception as e:
            logger.error(f'情感分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_session_sentiment(self, session_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT AVG(sentiment_score) as avg_score, sentiment_level, COUNT(*) as count
                    FROM chat_messages WHERE session_id = ?
                ''', (session_id,))
                result = cursor.fetchone()
                if result:
                    avg_score = round(result['avg_score'], 2) if result['avg_score'] else 0
                    level = self._get_sentiment_level(avg_score)
                    return {'success': True, 'avg_score': avg_score, 'level': level, 'count': result['count']}
                return {'success': False, 'error': '会话无消息'}
        except Exception as e:
            logger.error(f'获取会话情感失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_sentiment_level(self, score: float) -> str:
        if score >= 0.7:
            return 'positive'
        elif score >= 0.3:
            return 'neutral'
        elif score >= 0.15:
            return 'negative'
        elif score >= 0.07:
            return 'anxious'
        else:
            return 'angry'

    def get_sentiment_trend(self, customer_id: int, days: int = 7) -> Dict[str, Any]:
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DATE(timestamp) as date, AVG(sentiment_score) as avg_score, COUNT(*) as count
                    FROM chat_messages 
                    WHERE sender_id = ? AND DATE(timestamp) >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (customer_id, start_date))
                trend = [{'date': r['date'], 'avg_score': round(r['avg_score'], 2) if r['avg_score'] else 0,
                          'count': r['count']} for r in cursor.fetchall()]
                return {'success': True, 'trend': trend, 'days': days}
        except Exception as e:
            logger.error(f'获取情感趋势失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 工单管理 ==========

    def create_ticket(self, ticket_type: str, title: str, customer_id: int,
                       **kwargs) -> Dict[str, Any]:
        try:
            ticket_id = f"tkt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TICKET_TYPES.get(ticket_type, {})
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tickets (
                            ticket_id, ticket_type, title, description,
                            channel_id, customer_id, customer_name, education_type,
                            priority, sla_hours, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ticket_id, ticket_type, title, kwargs.get('description'),
                          kwargs.get('channel_id'), customer_id, kwargs.get('customer_name'),
                          education_type, config.get('priority', 'low'),
                          config.get('sla_hours', 24), now, now))
                    cursor.execute('''
                        INSERT INTO ticket_interactions (
                            interaction_id, ticket_id, actor_id, actor_name,
                            actor_type, action, content, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, 'system', 'created', '工单已创建', ?, ?)
                    ''', (f"int_{uuid.uuid4().hex[:12]}", ticket_id, customer_id,
                          kwargs.get('customer_name'), now, now))
                    conn.commit()
                    logger.info(f'创建工单: {title} ({ticket_id})')
                    return {'success': True, 'ticket_id': ticket_id}
        except Exception as e:
            logger.error(f'创建工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_ticket(self, ticket_id: str, agent_id: int, agent_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM tickets WHERE ticket_id = ?', (ticket_id,))
                    ticket = cursor.fetchone()
                    if not ticket:
                        return {'success': False, 'error': '工单不存在'}
                    if ticket[0] != 'open':
                        return {'success': False, 'error': '工单状态不允许分配'}
                    cursor.execute('INSERT INTO ticket_assignments (ticket_id, agent_id, agent_name, assign_time) VALUES (?, ?, ?, ?)',
                                 (ticket_id, agent_id, agent_name, now))
                    cursor.execute('UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?',
                                 ('assigned', now, ticket_id))
                    cursor.execute('''
                        INSERT INTO ticket_interactions (
                            interaction_id, ticket_id, actor_id, actor_name,
                            actor_type, action, content, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, 'agent', 'assigned', ?, ?, ?)
                    ''', (f"int_{uuid.uuid4().hex[:12]}", ticket_id, agent_id, agent_name,
                          f'已分配给客服 {agent_name}', now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_ticket(self, ticket_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'title' in kwargs:
                        updates.append('title = ?')
                        params.append(kwargs['title'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if 'status' in kwargs:
                        updates.append('status = ?')
                        params.append(kwargs['status'])
                        if kwargs['status'] == 'resolved':
                            updates.append('resolved_at = ?')
                            params.append(now)
                    if 'priority' in kwargs:
                        updates.append('priority = ?')
                        params.append(kwargs['priority'])
                    params.append(ticket_id)
                    if updates:
                        cursor.execute(f'UPDATE tickets SET {", ".join(updates)}, updated_at = ? WHERE ticket_id = ?',
                                     params + [now])
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未更新任何字段'}
        except Exception as e:
            logger.error(f'更新工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_ticket_interaction(self, ticket_id: str, actor_id: int, actor_name: str,
                               actor_type: str, action: str, content: str = '') -> Dict[str, Any]:
        try:
            interaction_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ticket_interactions (
                            interaction_id, ticket_id, actor_id, actor_name,
                            actor_type, action, content, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (interaction_id, ticket_id, actor_id, actor_name,
                          actor_type, action, content, now, now))
                    conn.commit()
                    return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.error(f'添加工单交互失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_tickets(self, status: str = None, education_type: str = None,
                     agent_id: int = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT t.* FROM tickets t LEFT JOIN ticket_assignments ta ON t.ticket_id = ta.ticket_id WHERE 1=1'
                params = []
                if status:
                    query += ' AND t.status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND t.education_type = ?'
                    params.append(education_type)
                if agent_id:
                    query += ' AND ta.agent_id = ?'
                    params.append(agent_id)
                cursor.execute(f'SELECT COUNT(DISTINCT t.ticket_id) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY t.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tickets = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tickets': tickets, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取工单列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能路由 ==========

    def add_routing_rule(self, rule_name: str, rule_type: str, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"rul_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO routing_rules (
                            rule_id, rule_name, rule_type, education_type,
                            conditions, actions, priority, is_active,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (rule_id, rule_name, rule_type, education_type,
                          kwargs.get('conditions'), kwargs.get('actions'),
                          kwargs.get('priority', 100), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'添加路由规则: {rule_name} ({rule_id})')
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'添加路由规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def route_ticket(self, ticket_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT ticket_type, education_type, priority FROM tickets WHERE ticket_id = ?',
                             (ticket_id,))
                ticket = cursor.fetchone()
                if not ticket:
                    return {'success': False, 'error': '工单不存在'}
                
                cursor.execute('''
                    SELECT * FROM routing_rules 
                    WHERE is_active = 1 AND education_type = ?
                    ORDER BY priority DESC LIMIT 1
                ''', (ticket['education_type'],))
                rule = cursor.fetchone()
                
                cursor.execute('''
                    SELECT agent_id, agent_name FROM agent_performance 
                    WHERE date = ? AND education_type = ?
                    ORDER BY resolved_tickets DESC LIMIT 1
                ''', (now[:10], ticket['education_type']))
                agent = cursor.fetchone()
                
                if agent:
                    self.assign_ticket(ticket_id, agent['agent_id'], agent['agent_name'])
                    cursor.execute('''
                        INSERT INTO routing_logs (
                            log_id, rule_id, ticket_id, target_agent_id,
                            target_agent_name, reason, timestamp, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (f"log_{uuid.uuid4().hex[:12]}", rule['rule_id'] if rule else None,
                          ticket_id, agent['agent_id'], agent['agent_name'],
                          f'按规则路由: {rule["rule_name"]}' if rule else '默认路由', now, now))
                    conn.commit()
                    return {'success': True, 'agent_id': agent['agent_id'], 'agent_name': agent['agent_name']}
                return {'success': False, 'error': '暂无可用客服'}
        except Exception as e:
            logger.error(f'路由工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_routing_rules(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM routing_rules WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY priority DESC'
                cursor.execute(query, params)
                rules = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rules': rules}
        except Exception as e:
            logger.error(f'获取路由规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_routing_logs(self, ticket_id: str = None, days: int = 7) -> Dict[str, Any]:
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM routing_logs WHERE DATE(timestamp) >= ?'
                params = [start_date]
                if ticket_id:
                    query += ' AND ticket_id = ?'
                    params.append(ticket_id)
                query += ' ORDER BY timestamp DESC'
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs}
        except Exception as e:
            logger.error(f'获取路由日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 客服质检 ==========

    def create_inspection(self, session_id: str = None, ticket_id: str = None,
                           agent_id: int = None, **kwargs) -> Dict[str, Any]:
        try:
            inspection_id = f"ins_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_inspections (
                            inspection_id, session_id, ticket_id, agent_id,
                            agent_name, inspector_id, inspector_name,
                            education_type, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (inspection_id, session_id, ticket_id, agent_id,
                          kwargs.get('agent_name'), kwargs.get('inspector_id'),
                          kwargs.get('inspector_name'), education_type, now))
                    conn.commit()
                    return {'success': True, 'inspection_id': inspection_id}
        except Exception as e:
            logger.error(f'创建质检失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_inspection_result(self, inspection_id: str, results: List[Dict]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            total_score = 0
            total_weight = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for result in results:
                        dimension = result.get('dimension')
                        score = result.get('score', 0)
                        comment = result.get('comment', '')
                        weight = QUALITY_DIMENSIONS.get(dimension, {}).get('weight', 0.1)
                        total_score += score * weight
                        total_weight += weight
                        cursor.execute('''
                            INSERT INTO inspection_results (
                                result_id, inspection_id, dimension, score, comment, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (f"irs_{uuid.uuid4().hex[:12]}", inspection_id, dimension, score, comment, now))
                    avg_score = round(total_score / total_weight, 2) if total_weight > 0 else 0
                    cursor.execute('UPDATE quality_inspections SET status = ?, completed_at = ? WHERE inspection_id = ?',
                                 ('completed', now, inspection_id))
                    conn.commit()
                    return {'success': True, 'total_score': avg_score, 'dimension_count': len(results)}
        except Exception as e:
            logger.error(f'提交质检结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_inspection_details(self, inspection_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quality_inspections WHERE inspection_id = ?', (inspection_id,))
                inspection = cursor.fetchone()
                if not inspection:
                    return {'success': False, 'error': '质检不存在'}
                cursor.execute('SELECT * FROM inspection_results WHERE inspection_id = ?', (inspection_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'inspection': dict(inspection), 'results': results}
        except Exception as e:
            logger.error(f'获取质检详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_inspections(self, agent_id: int = None, status: str = None,
                         education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_inspections WHERE 1=1'
                params = []
                if agent_id:
                    query += ' AND agent_id = ?'
                    params.append(agent_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                inspections = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'inspections': inspections}
        except Exception as e:
            logger.error(f'获取质检列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 客服绩效 ==========

    def record_agent_performance(self, agent_id: int, agent_name: str, **kwargs) -> Dict[str, Any]:
        try:
            perf_id = f"prf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            date = now[:10]
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT perf_id FROM agent_performance WHERE agent_id = ? AND date = ?',
                                 (agent_id, date))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute('''
                            UPDATE agent_performance SET
                                total_tickets = total_tickets + ?,
                                resolved_tickets = resolved_tickets + ?,
                                avg_response_time = ?,
                                avg_handle_time = ?,
                                satisfaction_score = ?,
                                quality_score = ?
                            WHERE agent_id = ? AND date = ?
                        ''', (kwargs.get('total_tickets', 0), kwargs.get('resolved_tickets', 0),
                              kwargs.get('avg_response_time', 0), kwargs.get('avg_handle_time', 0),
                              kwargs.get('satisfaction_score', 0), kwargs.get('quality_score', 0),
                              agent_id, date))
                    else:
                        cursor.execute('''
                            INSERT INTO agent_performance (
                                perf_id, agent_id, agent_name, education_type,
                                date, total_tickets, resolved_tickets,
                                avg_response_time, avg_handle_time,
                                satisfaction_score, quality_score, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (perf_id, agent_id, agent_name, education_type, date,
                              kwargs.get('total_tickets', 0), kwargs.get('resolved_tickets', 0),
                              kwargs.get('avg_response_time', 0), kwargs.get('avg_handle_time', 0),
                              kwargs.get('satisfaction_score', 0), kwargs.get('quality_score', 0), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录客服绩效失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_agent_performance(self, agent_id: int, date: str = None) -> Dict[str, Any]:
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM agent_performance WHERE agent_id = ? AND date = ?',
                             (agent_id, date))
                perf = cursor.fetchone()
                if perf:
                    return {'success': True, 'performance': dict(perf)}
                return {'success': False, 'error': '无绩效记录'}
        except Exception as e:
            logger.error(f'获取客服绩效失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_agent_rankings(self, education_type: str = None, days: int = 7) -> Dict[str, Any]:
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT agent_id, agent_name, education_type,
                           SUM(total_tickets) as total_tickets,
                           SUM(resolved_tickets) as resolved_tickets,
                           AVG(avg_response_time) as avg_response_time,
                           AVG(satisfaction_score) as satisfaction_score,
                           AVG(quality_score) as quality_score
                    FROM agent_performance
                    WHERE date >= ?
                '''
                params = [start_date]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY agent_id ORDER BY resolved_tickets DESC'
                cursor.execute(query, params)
                rankings = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rankings': rankings, 'days': days}
        except Exception as e:
            logger.error(f'获取客服排名失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_agent_workload(self, agent_id: int) -> Dict[str, Any]:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM ticket_assignments WHERE agent_id = ? AND status = 'assigned') as assigned_tickets,
                        (SELECT COUNT(*) FROM ticket_assignments ta JOIN tickets t ON ta.ticket_id = t.ticket_id 
                          WHERE ta.agent_id = ? AND t.status = 'open') as open_tickets,
                        (SELECT COUNT(*) FROM chat_sessions WHERE agent_id = ? AND status = 'active') as active_sessions,
                        (SELECT COUNT(*) FROM chat_sessions WHERE agent_id = ? AND DATE(start_time) = ?) as today_sessions
                    ''', (agent_id, agent_id, agent_id, agent_id, today))
                workload = cursor.fetchone()
                if workload:
                    return {'success': True, 'workload': dict(workload)}
                return {'success': False, 'error': '无工作负载数据'}
        except Exception as e:
            logger.error(f'获取客服工作负载失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 自动回复 ==========

    def add_auto_reply(self, keyword: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            reply_id = f"rpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO auto_replies (
                            reply_id, keyword, content, education_type,
                            question_type, priority, is_active, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (reply_id, keyword, content, education_type,
                          kwargs.get('question_type'), kwargs.get('priority', 100),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'添加自动回复: {keyword} ({reply_id})')
                    return {'success': True, 'reply_id': reply_id}
        except Exception as e:
            logger.error(f'添加自动回复失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_auto_reply(self, reply_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'keyword' in kwargs:
                        updates.append('keyword = ?')
                        params.append(kwargs['keyword'])
                    if 'content' in kwargs:
                        updates.append('content = ?')
                        params.append(kwargs['content'])
                    if 'question_type' in kwargs:
                        updates.append('question_type = ?')
                        params.append(kwargs['question_type'])
                    if 'priority' in kwargs:
                        updates.append('priority = ?')
                        params.append(kwargs['priority'])
                    if 'is_active' in kwargs:
                        updates.append('is_active = ?')
                        params.append(kwargs['is_active'])
                    params.append(reply_id)
                    if updates:
                        cursor.execute(f'UPDATE auto_replies SET {", ".join(updates)}, updated_at = ? WHERE reply_id = ?',
                                     params + [now])
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '未更新任何字段'}
        except Exception as e:
            logger.error(f'更新自动回复失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_auto_replies(self, education_type: str = None, question_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM auto_replies WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if question_type:
                    query += ' AND question_type = ?'
                    params.append(question_type)
                query += ' ORDER BY priority DESC'
                cursor.execute(query, params)
                replies = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'replies': replies}
        except Exception as e:
            logger.error(f'获取自动回复列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_service_summary(self, date: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_params = [date]
                if education_type:
                    query_params.append(education_type)
                
                cursor.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM chat_sessions WHERE DATE(start_time) = ? {}) as total_sessions,
                        (SELECT COUNT(*) FROM chat_sessions WHERE DATE(start_time) = ? {} AND status = 'closed') as closed_sessions,
                        (SELECT COUNT(*) FROM tickets WHERE DATE(created_at) = ? {}) as total_tickets,
                        (SELECT COUNT(*) FROM tickets WHERE DATE(created_at) = ? {} AND status = 'resolved') as resolved_tickets,
                        (SELECT AVG(sentiment_score) FROM chat_sessions WHERE DATE(start_time) = ? {}) as avg_sentiment,
                        (SELECT AVG(satisfaction_score) FROM customer_feedback WHERE DATE(created_at) = ? {}) as avg_satisfaction
                    '''.format('AND education_type = ?' if education_type else '',) * 6,
                    query_params * 6)
                summary = cursor.fetchone()
                
                if summary:
                    return {
                        'success': True,
                        'date': date,
                        'education_type': education_type,
                        'total_sessions': summary['total_sessions'] or 0,
                        'closed_sessions': summary['closed_sessions'] or 0,
                        'total_tickets': summary['total_tickets'] or 0,
                        'resolved_tickets': summary['resolved_tickets'] or 0,
                        'avg_sentiment': round(summary['avg_sentiment'], 2) if summary['avg_sentiment'] else 0,
                        'avg_satisfaction': round(summary['avg_satisfaction'], 2) if summary['avg_satisfaction'] else 0,
                        'session_resolution_rate': round((summary['closed_sessions'] / summary['total_sessions']) * 100, 1) if summary['total_sessions'] else 0,
                        'ticket_resolution_rate': round((summary['resolved_tickets'] / summary['total_tickets']) * 100, 1) if summary['total_tickets'] else 0
                    }
                return {'success': False, 'error': '无统计数据'}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}