from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育心理健康服务 (v15.25.0) ==================================== 提供心理健康评估、心理咨询服务、心理危机干预、心理健康教育、 心理档案管理、心理数据监测、心理健康预警、心理康复支持等综合管理服务。  核心能力： 1. 心理健康评估 - 测评管理、评估记录、结果分析、报告生成 2. 心理咨询服务 - 咨询预约、咨询记录、咨询师管理、咨询统计 3. 心理危机干预 - 危机识别、干预处理、危机跟踪、危机报告 4. 心理健康教育 - 课程管理、讲座组织、资料发布、教育评估、活动记录 5. 心理档案管理 - 档案创建、档案查询、档案更新、档案归档 6. 心理数据监测 - 数据采集、数据分析、趋势跟踪、异常预警 7. 心理健康预警 - 预警规则、预警触发、预警处理、预警统计 8. 心理康复支持 - 康复计划、康复记录、康复评估、康复跟踪 """
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_mental_health_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MentalHealth')


# ========== 心理健康配置 ==========

ASSESSMENT_TYPES = {
    'mental_health': {'name': '心理健康测评', 'duration': 30, 'questions': 50},
    'emotion': {'name': '情绪评估', 'duration': 15, 'questions': 20},
    'stress': {'name': '压力评估', 'duration': 20, 'questions': 25},
    'anxiety': {'name': '焦虑评估', 'duration': 25, 'questions': 30},
    'depression': {'name': '抑郁评估', 'duration': 25, 'questions': 25},
    'personality': {'name': '人格评估', 'duration': 45, 'questions': 100},
    'adaptation': {'name': '适应评估', 'duration': 20, 'questions': 30},
    'development': {'name': '发展评估', 'duration': 30, 'questions': 40}
}

COUNSELING_MODES = {
    'face_to_face': {'name': '面对面咨询', 'requires_room': True, 'duration': 50},
    'phone': {'name': '电话咨询', 'requires_room': False, 'duration': 40},
    'online': {'name': '在线咨询', 'requires_room': False, 'duration': 50},
    'group': {'name': '团体咨询', 'requires_room': True, 'duration': 90, 'min_participants': 4, 'max_participants': 10},
    'family': {'name': '家庭咨询', 'requires_room': True, 'duration': 60, 'min_participants': 2},
    'crisis': {'name': '危机咨询', 'requires_room': True, 'duration': 30, 'priority': True},
    'short_term': {'name': '短期咨询', 'requires_room': True, 'duration': 50, 'sessions': 4},
    'long_term': {'name': '长期咨询', 'requires_room': True, 'duration': 50, 'sessions': 12}
}

CRISIS_LEVELS = {
    'general': {'name': '一般危机', 'response_time': 24, 'required_actions': ['评估', '建议']},
    'moderate': {'name': '中度危机', 'response_time': 8, 'required_actions': ['干预', '跟踪']},
    'severe': {'name': '重度危机', 'response_time': 4, 'required_actions': ['紧急干预', '监护']},
    'urgent': {'name': '紧急危机', 'response_time': 1, 'required_actions': ['立即干预', '就医']},
    'suicide_risk': {'name': '自杀风险', 'response_time': 0.5, 'required_actions': ['24小时监护', '专业医疗']},
    'harm_risk': {'name': '伤害风险', 'response_time': 0.5, 'required_actions': ['隔离', '专业医疗']},
    'emotional_collapse': {'name': '情绪崩溃', 'response_time': 2, 'required_actions': ['安抚', '心理支持']},
    'psychological_imbalance': {'name': '心理失衡', 'response_time': 12, 'required_actions': ['疏导', '调整']}
}

EDUCATION_TOPICS = {
    'mental_health_knowledge': {'name': '心理健康知识', 'target_audience': ['all']},
    'emotion_management': {'name': '情绪管理', 'target_audience': ['adult', 'k12']},
    'stress_management': {'name': '压力管理', 'target_audience': ['adult', 'k12']},
    'interpersonal': {'name': '人际交往', 'target_audience': ['k12', 'adult']},
    'self_cognition': {'name': '自我认知', 'target_audience': ['k12']},
    'psychological_adjustment': {'name': '心理调适', 'target_audience': ['adult', 'k12']},
    'psychological_care': {'name': '心理保健', 'target_audience': ['adult']},
    'psychological_prevention': {'name': '心理预防', 'target_audience': ['all']}
}

RECORD_TYPES = {
    'basic_info': {'name': '基本信息', 'required': True},
    'assessment_record': {'name': '评估记录', 'required': False},
    'counseling_record': {'name': '咨询记录', 'required': False},
    'crisis_record': {'name': '危机记录', 'required': False},
    'education_record': {'name': '教育记录', 'required': False},
    'intervention_record': {'name': '干预记录', 'required': False},
    'rehabilitation_record': {'name': '康复记录', 'required': False},
    'follow_up_record': {'name': '随访记录', 'required': False}
}

MONITORING_METRICS = {
    'emotion_state': {'name': '情绪状态', 'normal_range': [60, 80], 'unit': 'score'},
    'stress_index': {'name': '压力指数', 'normal_range': [0, 50], 'unit': 'score'},
    'sleep_quality': {'name': '睡眠质量', 'normal_range': [7, 10], 'unit': 'score'},
    'study_state': {'name': '学习状态', 'normal_range': [60, 90], 'unit': 'score'},
    'social_behavior': {'name': '社交行为', 'normal_range': [50, 80], 'unit': 'score'},
    'psychological_resilience': {'name': '心理韧性', 'normal_range': [50, 85], 'unit': 'score'},
    'psychological_energy': {'name': '心理能量', 'normal_range': [50, 80], 'unit': 'score'},
    'psychological_balance': {'name': '心理平衡', 'normal_range': [60, 85], 'unit': 'score'}
}

WARNING_LEVELS = {
    'green': {'name': '绿色安全', 'action': '正常监测', 'color': '#22c55e'},
    'yellow': {'name': '黄色关注', 'action': '加强关注', 'color': '#eab308'},
    'orange': {'name': '橙色预警', 'action': '主动干预', 'color': '#f97316'},
    'red': {'name': '红色危机', 'action': '紧急处理', 'color': '#ef4444'},
    'emergency': {'name': '紧急干预', 'action': '立即行动', 'color': '#dc2626'},
    'focus': {'name': '重点监控', 'action': '持续跟踪', 'color': '#a855f7'},
    'continuous': {'name': '持续关注', 'action': '定期评估', 'color': '#3b82f6'},
    'recovery': {'name': '恢复跟踪', 'action': '康复指导', 'color': '#14b8a6'}
}

REHABILITATION_TYPES = {
    'psychological_rehabilitation': {'name': '心理康复', 'duration': 90, 'frequency': 'weekly'},
    'emotion_regulation': {'name': '情绪调节', 'duration': 60, 'frequency': 'biweekly'},
    'cognitive_reconstruction': {'name': '认知重建', 'duration': 120, 'frequency': 'weekly'},
    'behavior_modification': {'name': '行为矫正', 'duration': 90, 'frequency': 'weekly'},
    'social_skills_training': {'name': '社交技能训练', 'duration': 60, 'frequency': 'biweekly'},
    'stress_management_training': {'name': '压力管理训练', 'duration': 45, 'frequency': 'weekly'},
    'mindfulness_training': {'name': '正念训练', 'duration': 30, 'frequency': 'daily'},
    'resilience_cultivation': {'name': '心理韧性培养', 'duration': 90, 'frequency': 'weekly'}
}


class MentalHealthService:
    """教育心理健康服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mental_health_assessment ( assessment_id TEXT PRIMARY KEY, assessment_name TEXT NOT NULL, assessment_type TEXT NOT NULL, education_type TEXT, description TEXT, duration INTEGER, question_count INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS assessment_records ( record_id TEXT PRIMARY KEY, assessment_id TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, score REAL, result TEXT, details TEXT, assessment_date TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS counseling_service ( service_id TEXT PRIMARY KEY, service_name TEXT NOT NULL, counseling_mode TEXT NOT NULL, counselor_id INTEGER, counselor_name TEXT, education_type TEXT, room_id TEXT, available_slots TEXT, status TEXT DEFAULT 'available', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS counseling_records ( record_id TEXT PRIMARY KEY, service_id TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, counselor_id INTEGER, counselor_name TEXT, counseling_date TEXT, counseling_time TEXT, duration INTEGER, content TEXT, advice TEXT, next_session_date TEXT, status TEXT DEFAULT 'completed', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS crisis_intervention ( intervention_id TEXT PRIMARY KEY, crisis_level TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, crisis_description TEXT, response_time TEXT, actions_taken TEXT, responsible_person TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS intervention_records ( record_id TEXT PRIMARY KEY, intervention_id TEXT NOT NULL, action_type TEXT, action_description TEXT, action_time TEXT, operator TEXT, result TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mental_health_education ( education_id TEXT PRIMARY KEY, education_name TEXT NOT NULL, education_topic TEXT NOT NULL, education_type TEXT, target_audience TEXT, description TEXT, content TEXT, duration INTEGER, organizer TEXT, location TEXT, max_participants INTEGER DEFAULT 50, enrolled_count INTEGER DEFAULT 0, status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS education_records ( record_id TEXT PRIMARY KEY, education_id TEXT NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, attendance INTEGER DEFAULT 0, score REAL, feedback TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS psychological_records ( record_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, record_type TEXT NOT NULL, record_data TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS record_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, record_id TEXT NOT NULL, field_name TEXT, field_value TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mental_health_monitoring ( monitoring_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, metrics TEXT, monitoring_start_date TEXT, monitoring_end_date TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS monitoring_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, monitoring_id TEXT NOT NULL, metric_name TEXT NOT NULL, metric_value REAL, record_date TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mental_health_warning ( warning_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, warning_level TEXT NOT NULL, warning_reason TEXT, warning_time TEXT, actions_taken TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS warning_records ( record_id TEXT PRIMARY KEY, warning_id TEXT NOT NULL, action_type TEXT, action_description TEXT, action_time TEXT, operator TEXT, result TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS psychological_rehabilitation ( rehabilitation_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, user_name TEXT, education_type TEXT, rehabilitation_type TEXT NOT NULL, plan_description TEXT, start_date TEXT, end_date TEXT, target_goals TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS rehabilitation_records ( record_id TEXT PRIMARY KEY, rehabilitation_id TEXT NOT NULL, session_date TEXT, session_content TEXT, progress REAL, notes TEXT, counselor_name TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('教育心理健康服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 心理健康评估 ==========

    def create_assessment(self, assessment_name: str, assessment_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"mas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ASSESSMENT_TYPES.get(assessment_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO mental_health_assessment ( assessment_id, assessment_name, assessment_type, education_type, description, duration, question_count, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ''', (assessment_id, assessment_name, assessment_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('duration', config.get('duration', 30)),
                          kwargs.get('question_count', config.get('questions', 50)),
                          now, now))
                    conn.commit()
                    logger.info(f'创建评估: {assessment_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_assessment(self, assessment_id: str, user_id: int,
                           user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"mar_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            score = kwargs.get('score', 0)
            if score >= 80:
                result = '良好'
            elif score >= 60:
                result = '一般'
            else:
                result = '需关注'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM mental_health_assessment WHERE assessment_id = ?',
                    (assessment_id,))
                    assessment = cursor.fetchone()
                    education_type = assessment[0] if assessment else kwargs.get('education_type', 'adult')
                    cursor.execute(''' INSERT INTO assessment_records ( record_id, assessment_id, user_id, user_name, education_type, score, result, details, assessment_date, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, assessment_id, user_id, user_name,
                          education_type, score, result,
                          json.dumps(kwargs.get('details', {})),
                          now[:10], now))
                    conn.commit()
                    logger.info(f'完成评估记录: {user_name} ({record_id})')
                    return {'success': True, 'record_id': record_id, 'result': result}
        except Exception as e:
            logger.error(f'完成评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_result(self, record_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assessment_records WHERE record_id = ?', (record_id,))
                record = cursor.fetchone()
                if record:
                    result = dict(record)
                    result['details'] = json.loads(result.get('details', '{}'))
                    return {'success': True, 'result': result}
                return {'success': False, 'error': '评估记录不存在'}
        except Exception as e:
            logger.error(f'获取评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_assessment_report(self, user_id: int, education_type: str = None,
                                   start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM assessment_records WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if start_date:
                    query += ' AND assessment_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND assessment_date <= ?'
                    params.append(end_date)
                query += ' ORDER BY assessment_date DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                for r in records:
                    r['details'] = json.loads(r.get('details', '{}'))
                total = len(records)
                avg_score = sum(r['score'] for r in records) / total if total > 0 else 0
                result_dist = {'良好': 0, '一般': 0, '需关注': 0}
                for r in records:
                    if r['result'] in result_dist:
                        result_dist[r['result']] += 1
                report = {
                    'user_id': user_id,
                    'total_assessments': total,
                    'average_score': round(avg_score, 2),
                    'result_distribution': result_dist,
                    'records': records[:10]
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理咨询服务 ==========

    def create_counseling_service(self, service_name: str, counseling_mode: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"cos_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COUNSELING_MODES.get(counseling_mode, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO counseling_service ( service_id, service_name, counseling_mode, counselor_id, counselor_name, education_type, room_id, available_slots, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?) ''', (service_id, service_name, counseling_mode,
                          kwargs.get('counselor_id'), kwargs.get('counselor_name'),
                          kwargs.get('education_type'), kwargs.get('room_id'),
                          json.dumps(kwargs.get('available_slots', [])),
                          now, now))
                    conn.commit()
                    logger.info(f'创建咨询服务: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建咨询服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_counseling(self, service_id: str, user_id: int, user_name: str,
                        counseling_date: str, counseling_time: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cor_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT counseling_mode, counselor_id, counselor_name, education_type, available_slots FROM counseling_service WHERE service_id = ?', (service_id,))
                    service = cursor.fetchone()
                    if not service:
                        return {'success': False, 'error': '咨询服务不存在'}
                    config = COUNSELING_MODES.get(service[0], {})
                    duration = config.get('duration', 50)
                    cursor.execute(''' INSERT INTO counseling_records ( record_id, service_id, user_id, user_name, education_type, counselor_id, counselor_name, counseling_date, counseling_time, duration, content, advice, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', 'scheduled', ?) ''', (record_id, service_id, user_id, user_name,
                          service[4] or kwargs.get('education_type', 'adult'),
                          service[2], service[3], counseling_date, counseling_time, duration, now))
                    conn.commit()
                    logger.info(f'预约咨询: {user_name} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'预约咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_counseling(self, record_id: str, content: str, advice: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE counseling_records SET content = ?, advice = ?, next_session_date = ?, status = 'completed', updated_at = ? WHERE record_id = ? AND status = 'scheduled' ''', (content, advice, kwargs.get('next_session_date'), now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '咨询记录状态不允许完成'}
        except Exception as e:
            logger.error(f'完成咨询失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_counseling_records(self, user_id: int, education_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM counseling_records WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY counseling_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取咨询记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理危机干预 ==========

    def report_crisis(self, user_id: int, user_name: str, crisis_level: str,
                      crisis_description: str, **kwargs) -> Dict[str, Any]:
        try:
            intervention_id = f"cri_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CRISIS_LEVELS.get(crisis_level, {})
            response_time = config.get('response_time', 24)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO crisis_intervention ( intervention_id, crisis_level, user_id, user_name, education_type, crisis_description, response_time, actions_taken, responsible_person, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (intervention_id, crisis_level, user_id, user_name,
                          kwargs.get('education_type', 'adult'), crisis_description,
                          f'{response_time}小时',
                          json.dumps(config.get('required_actions', [])),
                          kwargs.get('responsible_person'), now, now))
                    conn.commit()
                    logger.info(f'报告危机: {user_name} ({intervention_id})')
                    return {'success': True, 'intervention_id': intervention_id, 'response_time': f'{response_time}小时'}
        except Exception as e:
            logger.error(f'报告危机失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_crisis(self, intervention_id: str, action_type: str,
                       action_description: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cir_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO intervention_records ( record_id, intervention_id, action_type, action_description, action_time, operator, result ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (record_id, intervention_id, action_type, action_description,
                          now, kwargs.get('operator'), kwargs.get('result')))
                    if kwargs.get('status'):
                        cursor.execute('UPDATE crisis_intervention SET status = ?, updated_at = ? WHERE intervention_id = ?',
                                     (kwargs['status'], now, intervention_id))
                    conn.commit()
                    logger.info(f'处理危机: {intervention_id} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'处理危机失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_crisis_status(self, intervention_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM crisis_intervention WHERE intervention_id = ?', (intervention_id,))
                crisis = cursor.fetchone()
                if crisis:
                    result = dict(crisis)
                    result['actions_taken'] = json.loads(result.get('actions_taken', '[]'))
                    cursor.execute(
                    'SELECT * FROM intervention_records WHERE intervention_id = ? ORDER BY action_time DESC',
                    (intervention_id,))
                    records = [dict(r) for r in cursor.fetchall()]
                    result['intervention_records'] = records
                    return {'success': True, 'crisis': result}
                return {'success': False, 'error': '危机记录不存在'}
        except Exception as e:
            logger.error(f'获取危机状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_crisis(self, intervention_id: str, close_reason: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE crisis_intervention SET status = ?, updated_at = ? WHERE intervention_id = ?',
                                 ('closed', now, intervention_id))
                    if cursor.rowcount > 0:
                        cursor.execute(''' INSERT INTO intervention_records ( record_id, intervention_id, action_type, action_description, action_time, operator, result ) VALUES (?, ?, 'close', ?, ?, ?, '已关闭') ''', (f"cir_{uuid.uuid4().hex[:12]}", intervention_id, close_reason, now,
                        kwargs.get('operator')))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '危机记录不存在'}
        except Exception as e:
            logger.error(f'关闭危机失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理健康教育 ==========

    def create_education_program(self, education_name: str, education_topic: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            education_id = f"edu_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EDUCATION_TOPICS.get(education_topic, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO mental_health_education ( education_id, education_name, education_topic, education_type, target_audience, description, content, duration, organizer, location, max_participants, enrolled_count, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'scheduled', ?, ?) ''', (education_id, education_name, education_topic,
                          kwargs.get('education_type'),
                          json.dumps(config.get('target_audience', ['all'])),
                          kwargs.get('description'), kwargs.get('content'),
                          kwargs.get('duration', 60), kwargs.get('organizer'),
                          kwargs.get('location'), kwargs.get('max_participants', 50),
                          now, now))
                    conn.commit()
                    logger.info(f'创建教育项目: {education_name} ({education_id})')
                    return {'success': True, 'education_id': education_id}
        except Exception as e:
            logger.error(f'创建教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_education(self, education_id: str, user_id: int, user_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"edr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, education_type FROM mental_health_education WHERE education_id = ?', (education_id,))
                    education = cursor.fetchone()
                    if not education:
                        return {'success': False, 'error': '教育项目不存在'}
                    if education[0] and education[1] >= education[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO education_records (record_id, education_id, user_id, user_name, education_type) VALUES (?, ?, ?, ?, ?)',
                                 (record_id, education_id, user_id, user_name,
                                 education[2] or kwargs.get('education_type', 'adult')))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE mental_health_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE education_id = ?', (now, education_id))
                        conn.commit()
                        return {'success': True, 'record_id': record_id}
                    return {'success': False, 'error': '已报名该教育项目'}
        except Exception as e:
            logger.error(f'报名教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_education_attendance(self, record_id: str, attended: bool = True,
                                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE education_records SET attendance = ?, score = ?, feedback = ? WHERE record_id = ? ''', (1 if attended else 0, kwargs.get('score'), kwargs.get('feedback'), record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '教育记录不存在'}
        except Exception as e:
            logger.error(f'记录教育出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_programs(self, education_topic: str = None,
                                education_type: str = None, status: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mental_health_education WHERE 1=1'
                params = []
                if education_topic:
                    query += ' AND education_topic = ?'
                    params.append(education_topic)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                for p in programs:
                    p['target_audience'] = json.loads(p.get('target_audience', '[]'))
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教育项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_education_records(self, user_id: int, education_type: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_records WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教育记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理档案管理 ==========

    def create_psychological_record(self, user_id: int, user_name: str,
                                    record_type: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"psr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO psychological_records ( record_id, user_id, user_name, education_type, record_type, record_data, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (record_id, user_id, user_name, kwargs.get('education_type', 'adult'),
                          record_type, json.dumps(kwargs.get('record_data', {})), now, now))
                    if kwargs.get('record_data'):
                        for key, value in kwargs['record_data'].items():
                            cursor.execute('INSERT INTO record_data (record_id, field_name, field_value, created_at) VALUES (?, ?, ?, ?)',
                                         (record_id, key, str(value), now))
                    conn.commit()
                    logger.info(f'创建心理档案: {user_name} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'创建心理档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_psychological_record(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_params = []
                    if 'record_data' in kwargs:
                        update_fields.append('record_data = ?')
                        update_params.append(json.dumps(kwargs['record_data']))
                        cursor.execute('DELETE FROM record_data WHERE record_id = ?', (record_id,))
                        for key, value in kwargs['record_data'].items():
                            cursor.execute('INSERT INTO record_data (record_id, field_name, field_value, created_at) VALUES (?, ?, ?, ?)',
                                         (record_id, key, str(value), now))
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_params.append(kwargs['status'])
                    update_params.append(record_id)
                    if update_fields:
                        cursor.execute(f'UPDATE psychological_records SET {", ".join(update_fields)}, updated_at = ? WHERE record_id = ?',
                                     [now] + update_params)
                        if cursor.rowcount > 0:
                            conn.commit()
                            return {'success': True}
                    return {'success': False, 'error': '档案记录不存在或无更新内容'}
        except Exception as e:
            logger.error(f'更新心理档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_psychological_record(self, record_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM psychological_records WHERE record_id = ?', (record_id,))
                record = cursor.fetchone()
                if record:
                    result = dict(record)
                    result['record_data'] = json.loads(result.get('record_data', '{}'))
                    cursor.execute('SELECT * FROM record_data WHERE record_id = ?', (record_id,))
                    data_records = [dict(d) for d in cursor.fetchall()]
                    result['field_data'] = data_records
                    return {'success': True, 'record': result}
                return {'success': False, 'error': '档案记录不存在'}
        except Exception as e:
            logger.error(f'获取心理档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_psychological_records(self, user_id: int = None,
                                     record_type: str = None, education_type: str = None,
                                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM psychological_records WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if record_type:
                    query += ' AND record_type = ?'
                    params.append(record_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                for r in records:
                    r['record_data'] = json.loads(r.get('record_data', '{}'))
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索心理档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理数据监测 ==========

    def create_monitoring(self, user_id: int, user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            monitoring_id = f"mon_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO mental_health_monitoring ( monitoring_id, user_id, user_name, education_type, metrics, monitoring_start_date, monitoring_end_date, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (monitoring_id, user_id, user_name, kwargs.get('education_type', 'adult'),
                          json.dumps(kwargs.get('metrics', list(MONITORING_METRICS.keys()))),
                          now[:10], kwargs.get('monitoring_end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建监测: {user_name} ({monitoring_id})')
                    return {'success': True, 'monitoring_id': monitoring_id}
        except Exception as e:
            logger.error(f'创建监测失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_monitoring_data(self, monitoring_id: str, metric_name: str,
                               metric_value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO monitoring_data ( monitoring_id, metric_name, metric_value, record_date, created_at ) VALUES (?, ?, ?, ?, ?) ''', (monitoring_id, metric_name, metric_value,
                          kwargs.get('record_date', now[:10]), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录监测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_monitoring_data(self, monitoring_id: str, metric_name: str = None,
                                start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM monitoring_data WHERE monitoring_id = ?'
                params = [monitoring_id]
                if metric_name:
                    query += ' AND metric_name = ?'
                    params.append(metric_name)
                if start_date:
                    query += ' AND record_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND record_date <= ?'
                    params.append(end_date)
                query += ' ORDER BY record_date ASC'
                cursor.execute(query, params)
                data = [dict(d) for d in cursor.fetchall()]
                if not data:
                    return {'success': False, 'error': '无监测数据'}
                values = [d['metric_value'] for d in data]
                avg = sum(values) / len(values)
                max_val = max(values)
                min_val = min(values)
                trend = '上升' if values[-1] > values[0] else ('下降' if values[-1] < values[0] else '稳定')
                config = MONITORING_METRICS.get(metric_name, {})
                normal_range = config.get('normal_range', [0, 100])
                is_normal = normal_range[0] <= avg <= normal_range[1]
                analysis = {
                    'metric_name': metric_name,
                    'data_count': len(data),
                    'average': round(avg, 2),
                    'max': round(max_val, 2),
                    'min': round(min_val, 2),
                    'trend': trend,
                    'normal_range': normal_range,
                    'is_normal': is_normal
                }
                return {'success': True, 'analysis': analysis, 'raw_data': data}
        except Exception as e:
            logger.error(f'分析监测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitoring_summary(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mental_health_monitoring WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                monitorings = [dict(m) for m in cursor.fetchall()]
                summaries = []
                for m in monitorings:
                    m['metrics'] = json.loads(m.get('metrics', '[]'))
                    cursor.execute('SELECT metric_name, AVG(metric_value) as avg_val FROM monitoring_data WHERE monitoring_id = ? GROUP BY metric_name',
                    (m['monitoring_id'],))
                    metric_avgs = {row['metric_name']: round(row['avg_val'], 2) for row in cursor.fetchall()}
                    summaries.append({
                        'monitoring_id': m['monitoring_id'],
                        'start_date': m['monitoring_start_date'],
                        'end_date': m['monitoring_end_date'],
                        'status': m['status'],
                        'metric_averages': metric_avgs
                    })
                return {'success': True, 'summaries': summaries}
        except Exception as e:
            logger.error(f'获取监测汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理健康预警 ==========

    def trigger_warning(self, user_id: int, user_name: str, warning_level: str,
                        warning_reason: str, **kwargs) -> Dict[str, Any]:
        try:
            warning_id = f"war_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = WARNING_LEVELS.get(warning_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO mental_health_warning ( warning_id, user_id, user_name, education_type, warning_level, warning_reason, warning_time, actions_taken, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (warning_id, user_id, user_name, kwargs.get('education_type', 'adult'),
                          warning_level, warning_reason, now,
                          config.get('action', ''), now, now))
                    conn.commit()
                    logger.info(f'触发预警: {user_name} ({warning_id})')
                    return {'success': True, 'warning_id': warning_id, 'action': config.get('action', '')}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_warning(self, warning_id: str, action_type: str,
                        action_description: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"wrr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO warning_records ( record_id, warning_id, action_type, action_description, action_time, operator, result ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (record_id, warning_id, action_type, action_description,
                          now, kwargs.get('operator'), kwargs.get('result')))
                    if kwargs.get('status'):
                        cursor.execute('UPDATE mental_health_warning SET status = ?, updated_at = ? WHERE warning_id = ?',
                                     (kwargs['status'], now, warning_id))
                    conn.commit()
                    logger.info(f'处理预警: {warning_id} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'处理预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_warning_status(self, warning_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM mental_health_warning WHERE warning_id = ?', (warning_id,))
                warning = cursor.fetchone()
                if warning:
                    result = dict(warning)
                    cursor.execute('SELECT * FROM warning_records WHERE warning_id = ? ORDER BY action_time DESC',
                    (warning_id,))
                    records = [dict(r) for r in cursor.fetchall()]
                    result['warning_records'] = records
                    return {'success': True, 'warning': result}
                return {'success': False, 'error': '预警记录不存在'}
        except Exception as e:
            logger.error(f'获取预警状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_warning_summary(self, education_type: str = None, status: str = 'active',
                            start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mental_health_warning WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if start_date:
                    query += ' AND warning_time >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND warning_time <= ?'
                    params.append(end_date)
                cursor.execute(query, params)
                warnings = [dict(w) for w in cursor.fetchall()]
                level_dist = {}
                for w in warnings:
                    level = w['warning_level']
                    level_dist[level] = level_dist.get(level, 0) + 1
                summary = {
                    'total_warnings': len(warnings),
                    'level_distribution': level_dist,
                    'warnings': warnings[:20]
                }
                return {'success': True, 'summary': summary}
        except Exception as e:
            logger.error(f'获取预警汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 心理康复支持 ==========

    def create_rehabilitation_plan(self, user_id: int, user_name: str,
                                   rehabilitation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            rehabilitation_id = f"reh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = REHABILITATION_TYPES.get(rehabilitation_type, {})
            duration_days = config.get('duration', 90)
            end_date = (datetime.now() + timedelta(days=duration_days)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO psychological_rehabilitation ( rehabilitation_id, user_id, user_name, education_type, rehabilitation_type, plan_description, start_date, end_date, target_goals, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (rehabilitation_id, user_id, user_name, kwargs.get('education_type', 'adult'),
                          rehabilitation_type, kwargs.get('plan_description'),
                          now[:10], end_date, json.dumps(kwargs.get('target_goals', [])),
                          now, now))
                    conn.commit()
                    logger.info(f'创建康复计划: {user_name} ({rehabilitation_id})')
                    return {'success': True, 'rehabilitation_id': rehabilitation_id, 'end_date': end_date}
        except Exception as e:
            logger.error(f'创建康复计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_rehabilitation_session(self, rehabilitation_id: str, session_date: str,
                                      session_content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rer_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO rehabilitation_records ( record_id, rehabilitation_id, session_date, session_content, progress, notes, counselor_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, rehabilitation_id, session_date, session_content,
                          kwargs.get('progress', 0), kwargs.get('notes'),
                          kwargs.get('counselor_name'), now))
                    conn.commit()
                    logger.info(f'记录康复会话: {rehabilitation_id} ({record_id})')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录康复会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_rehabilitation(self, rehabilitation_id: str, evaluation_score: float,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if evaluation_score >= 70 else 'active'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE psychological_rehabilitation SET status = ?, updated_at = ? WHERE rehabilitation_id = ?',
                                 (status, now, rehabilitation_id))
                    if cursor.rowcount > 0:
                        cursor.execute(''' INSERT INTO rehabilitation_records ( record_id, rehabilitation_id, session_date, session_content, progress, notes, counselor_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (f"rer_{uuid.uuid4().hex[:12]}", rehabilitation_id, now[:10],
                              '康复评估', evaluation_score, kwargs.get('notes', f'评估得分: {evaluation_score}'),
                              kwargs.get('counselor_name'), now))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '康复计划不存在'}
        except Exception as e:
            logger.error(f'评估康复失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_rehabilitation_progress(self, rehabilitation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM psychological_rehabilitation WHERE rehabilitation_id = ?',
                (rehabilitation_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '康复计划不存在'}
                plan_dict = dict(plan)
                plan_dict['target_goals'] = json.loads(plan_dict.get('target_goals', '[]'))
                cursor.execute(
                'SELECT * FROM rehabilitation_records WHERE rehabilitation_id = ? ORDER BY session_date ASC',
                (rehabilitation_id,))
                sessions = [dict(s) for s in cursor.fetchall()]
                if sessions:
                    avg_progress = sum(s.get('progress', 0) for s in sessions) / len(sessions)
                    latest_progress = sessions[-1].get('progress', 0)
                else:
                    avg_progress = 0
                    latest_progress = 0
                progress = {
                    'total_sessions': len(sessions),
                    'average_progress': round(avg_progress, 2),
                    'latest_progress': round(latest_progress, 2),
                    'sessions': sessions
                }
                plan_dict['progress'] = progress
                return {'success': True, 'plan': plan_dict}
        except Exception as e:
            logger.error(f'获取康复进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_mental_health_statistics(self, education_type: str = None,
                                     start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                query_params = []
                date_filter = ''
                if start_date:
                    date_filter += ' AND assessment_date >= ?'
                    query_params.append(start_date)
                if end_date:
                    date_filter += ' AND assessment_date <= ?'
                    query_params.append(end_date)

                if education_type:
                    query_params.append(education_type)
                    education_filter = ' AND education_type = ?'
                else:
                    education_filter = ''

                cursor.execute(f'SELECT COUNT(*) FROM assessment_records WHERE 1=1{date_filter}{education_filter}',
                query_params)
                stats['total_assessments'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM counseling_records WHERE 1=1{date_filter}{education_filter}',
                query_params)
                stats['total_counselings'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM crisis_intervention WHERE 1=1{education_filter}', query_params)
                stats['total_crises'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM mental_health_warning WHERE 1=1{education_filter}', query_params)
                stats['total_warnings'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM psychological_rehabilitation WHERE 1=1{education_filter}',
                query_params)
                stats['total_rehabilitations'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT AVG(score) FROM assessment_records WHERE 1=1{date_filter}{education_filter}',
                query_params)
                avg_score = cursor.fetchone()[0]
                stats['average_assessment_score'] = round(avg_score, 2) if avg_score else 0

                cursor.execute(f'SELECT result, COUNT(*) FROM assessment_records WHERE 1=1{date_filter}{education_filter} GROUP BY result',
                query_params)
                result_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['assessment_result_distribution'] = result_dist

                cursor.execute(f'SELECT warning_level, COUNT(*) FROM mental_health_warning WHERE 1=1{education_filter} GROUP BY warning_level', query_params)
                warning_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['warning_level_distribution'] = warning_dist

                stats['education_type'] = education_type or 'all'
                stats['period'] = {'start_date': start_date, 'end_date': end_date}

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}

















































































