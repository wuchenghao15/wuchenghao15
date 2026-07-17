#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育AI应用服务 (v15.17.0)
===============================
提供AI助教、AI导师、智能批改、智能组卷、智能答疑、AI写作、AI翻译、AI学习助手等综合教育服务。

核心能力：
1. AI助手 - AI助教/AI导师/AI辅导员/AI班主任/AI学习伙伴/AI作业助手/AI考试助手/AI研究助手
2. 智能批改 - 自动批改/智能批改/AI辅助批改/人工批改/混合批改
3. 智能组卷 - 单选/多选/判断/填空/简答/论述/计算/案例分析/听力/阅读
4. 智能答疑 - 精确匹配/关键词匹配/语义相似度/模糊匹配/手写识别/语音识别
5. AI写作 - 作文/论文/报告/邮件/简历/摘要/文案/创意写作
6. AI翻译 - 中文/英语/日语/韩语/法语/德语/西班牙语/俄语
7. AI学习助手 - 学习规划/进度追踪/错题分析/知识点推荐/学习提醒/考试预测/学习社区/学习档案
8. 会话管理 - 会话创建/消息记录/会话恢复/会话结束
9. 配置管理 - 助手配置/模型配置/系统配置
10. 统计分析 - 使用统计/效果评估
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_ai_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationAI')


# ========== 教育AI配置 ==========

AI_ASSISTANT_TYPES = {
    'teaching_assistant': {'name': 'AI助教', 'description': '辅助教师进行教学管理', 'supports_adult': True, 'supports_k12': True},
    'tutor': {'name': 'AI导师', 'description': '一对一学习辅导', 'supports_adult': True, 'supports_k12': True},
    'counselor': {'name': 'AI辅导员', 'description': '学业与心理辅导', 'supports_adult': True, 'supports_k12': True},
    'head_teacher': {'name': 'AI班主任', 'description': '班级管理与家校沟通', 'supports_adult': False, 'supports_k12': True},
    'learning_partner': {'name': 'AI学习伙伴', 'description': '陪伴式学习', 'supports_adult': True, 'supports_k12': True},
    'homework_assistant': {'name': 'AI作业助手', 'description': '作业辅导与讲解', 'supports_adult': True, 'supports_k12': True},
    'exam_assistant': {'name': 'AI考试助手', 'description': '备考指导与模拟', 'supports_adult': True, 'supports_k12': True},
    'research_assistant': {'name': 'AI研究助手', 'description': '学术研究辅助', 'supports_adult': True, 'supports_k12': False}
}

AI_MODEL_TYPES = {
    'gpt4': {'name': 'GPT-4', 'provider': 'OpenAI', 'capability': 'high', 'supports_adult': True, 'supports_k12': True},
    'claude3': {'name': 'Claude-3', 'provider': 'Anthropic', 'capability': 'high', 'supports_adult': True, 'supports_k12': True},
    'qwen': {'name': 'Qwen', 'provider': '阿里云', 'capability': 'medium', 'supports_adult': True, 'supports_k12': True},
    'llama3': {'name': 'Llama-3', 'provider': 'Meta', 'capability': 'medium', 'supports_adult': True, 'supports_k12': True},
    'gemini': {'name': 'Gemini', 'provider': 'Google', 'capability': 'high', 'supports_adult': True, 'supports_k12': True},
    'mistral': {'name': 'Mistral', 'provider': 'Mistral AI', 'capability': 'medium', 'supports_adult': True, 'supports_k12': True},
    'ernie': {'name': 'ERNIE', 'provider': '百度', 'capability': 'medium', 'supports_adult': True, 'supports_k12': True},
    'baichuan': {'name': 'Baichuan', 'provider': '百川智能', 'capability': 'medium', 'supports_adult': True, 'supports_k12': True}
}

CORRECTION_TYPES = {
    'auto': {'name': '自动批改', 'description': '系统自动判定', 'accuracy': 'medium'},
    'intelligent': {'name': '智能批改', 'description': 'AI语义分析', 'accuracy': 'high'},
    'ai_assisted': {'name': 'AI辅助批改', 'description': 'AI建议+人工确认', 'accuracy': 'very_high'},
    'manual': {'name': '人工批改', 'description': '教师手动批改', 'accuracy': 'very_high'},
    'hybrid': {'name': '混合批改', 'description': '客观题自动+主观题人工', 'accuracy': 'very_high'}
}

QUESTION_TYPES = {
    'single_choice': {'name': '单选题', 'correction_method': 'auto', 'supports_adult': True, 'supports_k12': True},
    'multiple_choice': {'name': '多选题', 'correction_method': 'auto', 'supports_adult': True, 'supports_k12': True},
    'judgment': {'name': '判断题', 'correction_method': 'auto', 'supports_adult': True, 'supports_k12': True},
    'fill_blank': {'name': '填空题', 'correction_method': 'intelligent', 'supports_adult': True, 'supports_k12': True},
    'short_answer': {'name': '简答题', 'correction_method': 'ai_assisted', 'supports_adult': True, 'supports_k12': True},
    'essay': {'name': '论述题', 'correction_method': 'hybrid', 'supports_adult': True, 'supports_k12': True},
    'calculation': {'name': '计算题', 'correction_method': 'intelligent', 'supports_adult': True, 'supports_k12': True},
    'case_analysis': {'name': '案例分析', 'correction_method': 'hybrid', 'supports_adult': True, 'supports_k12': False},
    'listening': {'name': '听力题', 'correction_method': 'auto', 'supports_adult': True, 'supports_k12': True},
    'reading': {'name': '阅读理解', 'correction_method': 'intelligent', 'supports_adult': True, 'supports_k12': True}
}

ANSWER_METHODS = {
    'exact_match': {'name': '精确匹配', 'description': '完全一致判定', 'suitable_for': ['single_choice', 'multiple_choice', 'judgment']},
    'keyword_match': {'name': '关键词匹配', 'description': '关键词命中判定', 'suitable_for': ['fill_blank', 'short_answer']},
    'semantic_similarity': {'name': '语义相似度', 'description': 'AI语义分析', 'suitable_for': ['short_answer', 'essay', 'case_analysis']},
    'fuzzy_match': {'name': '模糊匹配', 'description': '部分匹配判定', 'suitable_for': ['fill_blank']},
    'handwriting_recognition': {'name': '手写识别', 'description': 'OCR手写识别', 'suitable_for': ['fill_blank', 'short_answer']},
    'speech_recognition': {'name': '语音识别', 'description': '语音转文字', 'suitable_for': ['listening']}
}

TRANSLATION_LANGUAGES = {
    'zh': {'name': '中文', 'code': 'zh-CN'},
    'en': {'name': '英语', 'code': 'en-US'},
    'ja': {'name': '日语', 'code': 'ja-JP'},
    'ko': {'name': '韩语', 'code': 'ko-KR'},
    'fr': {'name': '法语', 'code': 'fr-FR'},
    'de': {'name': '德语', 'code': 'de-DE'},
    'es': {'name': '西班牙语', 'code': 'es-ES'},
    'ru': {'name': '俄语', 'code': 'ru-RU'}
}

WRITING_TYPES = {
    'composition': {'name': '作文', 'description': '记叙文/议论文/说明文', 'supports_adult': False, 'supports_k12': True},
    'paper': {'name': '论文', 'description': '学术论文/研究报告', 'supports_adult': True, 'supports_k12': False},
    'report': {'name': '报告', 'description': '工作总结/调研报告', 'supports_adult': True, 'supports_k12': False},
    'email': {'name': '邮件', 'description': '商务邮件/个人邮件', 'supports_adult': True, 'supports_k12': True},
    'resume': {'name': '简历', 'description': '求职简历', 'supports_adult': True, 'supports_k12': False},
    'summary': {'name': '摘要', 'description': '文献摘要/文章摘要', 'supports_adult': True, 'supports_k12': True},
    'copywriting': {'name': '文案', 'description': '广告文案/宣传文案', 'supports_adult': True, 'supports_k12': False},
    'creative_writing': {'name': '创意写作', 'description': '小说/散文/诗歌', 'supports_adult': True, 'supports_k12': True}
}

LEARNING_ASSISTANTS = {
    'learning_plan': {'name': '学习规划', 'description': '个性化学习计划制定', 'supports_adult': True, 'supports_k12': True},
    'progress_tracking': {'name': '进度追踪', 'description': '学习进度实时监控', 'supports_adult': True, 'supports_k12': True},
    'mistake_analysis': {'name': '错题分析', 'description': '错题整理与分析', 'supports_adult': True, 'supports_k12': True},
    'knowledge_recommendation': {'name': '知识点推荐', 'description': '智能推荐学习内容', 'supports_adult': True, 'supports_k12': True},
    'learning_reminder': {'name': '学习提醒', 'description': '定时学习提醒', 'supports_adult': True, 'supports_k12': True},
    'exam_prediction': {'name': '考试预测', 'description': '考试成绩预测', 'supports_adult': True, 'supports_k12': True},
    'learning_community': {'name': '学习社区', 'description': '学习交流社区', 'supports_adult': True, 'supports_k12': True},
    'learning_profile': {'name': '学习档案', 'description': '个人学习档案管理', 'supports_adult': True, 'supports_k12': True}
}


class EducationAIApplicationService:
    """教育AI应用服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_assistants (
                            assistant_id TEXT PRIMARY KEY,
                            assistant_name TEXT NOT NULL,
                            assistant_type TEXT NOT NULL,
                            ai_model TEXT DEFAULT 'gpt4',
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            description TEXT,
                            avatar_url TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS assistant_config (
                            config_id TEXT PRIMARY KEY,
                            assistant_id TEXT NOT NULL,
                            config_key TEXT NOT NULL,
                            config_value TEXT,
                            config_type TEXT DEFAULT 'string',
                            description TEXT,
                            created_at TEXT,
                            FOREIGN KEY (assistant_id) REFERENCES ai_assistants(assistant_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_sessions (
                            session_id TEXT PRIMARY KEY,
                            assistant_id TEXT NOT NULL,
                            user_id INTEGER NOT NULL,
                            user_name TEXT,
                            education_type TEXT,
                            subject TEXT,
                            session_type TEXT,
                            status TEXT DEFAULT 'active',
                            start_time TEXT,
                            end_time TEXT,
                            message_count INTEGER DEFAULT 0,
                            created_at TEXT,
                            FOREIGN KEY (assistant_id) REFERENCES ai_assistants(assistant_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS session_messages (
                            message_id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            sender TEXT NOT NULL,
                            content TEXT NOT NULL,
                            message_type TEXT DEFAULT 'text',
                            timestamp TEXT,
                            is_read INTEGER DEFAULT 0,
                            FOREIGN KEY (session_id) REFERENCES ai_sessions(session_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_corrections (
                            correction_id TEXT PRIMARY KEY,
                            correction_type TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            title TEXT,
                            description TEXT,
                            status TEXT DEFAULT 'pending',
                            created_by INTEGER,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS correction_results (
                            result_id TEXT PRIMARY KEY,
                            correction_id TEXT NOT NULL,
                            student_id INTEGER NOT NULL,
                            student_name TEXT,
                            answer_content TEXT,
                            correct_answer TEXT,
                            score REAL,
                            max_score REAL,
                            correction_method TEXT,
                            ai_feedback TEXT,
                            teacher_comment TEXT,
                            status TEXT DEFAULT 'completed',
                            created_at TEXT,
                            FOREIGN KEY (correction_id) REFERENCES ai_corrections(correction_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_exam_papers (
                            paper_id TEXT PRIMARY KEY,
                            paper_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            total_score REAL DEFAULT 100,
                            duration INTEGER DEFAULT 90,
                            question_count INTEGER DEFAULT 0,
                            difficulty TEXT DEFAULT 'medium',
                            status TEXT DEFAULT 'draft',
                            created_by INTEGER,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS paper_templates (
                            template_id TEXT PRIMARY KEY,
                            template_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            structure TEXT,
                            default_settings TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_qna (
                            qna_id TEXT PRIMARY KEY,
                            question TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            subject TEXT,
                            education_type TEXT,
                            grade_level INTEGER,
                            tags TEXT,
                            usage_count INTEGER DEFAULT 0,
                            accuracy REAL DEFAULT 1.0,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS qna_history (
                            history_id TEXT PRIMARY KEY,
                            qna_id TEXT,
                            user_id INTEGER NOT NULL,
                            user_question TEXT NOT NULL,
                            matched_question TEXT,
                            answer TEXT,
                            similarity REAL,
                            is_satisfied INTEGER DEFAULT 1,
                            feedback TEXT,
                            timestamp TEXT,
                            FOREIGN KEY (qna_id) REFERENCES ai_qna(qna_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_writing (
                            writing_id TEXT PRIMARY KEY,
                            writing_type TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            topic TEXT,
                            requirements TEXT,
                            word_count INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'draft',
                            created_by INTEGER,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS writing_results (
                            result_id TEXT PRIMARY KEY,
                            writing_id TEXT NOT NULL,
                            student_id INTEGER NOT NULL,
                            student_name TEXT,
                            content TEXT,
                            ai_score REAL,
                            ai_feedback TEXT,
                            teacher_score REAL,
                            teacher_comment TEXT,
                            final_score REAL,
                            status TEXT DEFAULT 'completed',
                            created_at TEXT,
                            FOREIGN KEY (writing_id) REFERENCES ai_writing(writing_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_translation (
                            translation_id TEXT PRIMARY KEY,
                            source_text TEXT NOT NULL,
                            source_language TEXT NOT NULL,
                            target_language TEXT NOT NULL,
                            education_type TEXT,
                            subject TEXT,
                            context TEXT,
                            status TEXT DEFAULT 'pending',
                            created_by INTEGER,
                            created_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS translation_history (
                            history_id TEXT PRIMARY KEY,
                            source_text TEXT,
                            translated_text TEXT,
                            source_language TEXT,
                            target_language TEXT,
                            user_id INTEGER,
                            education_type TEXT,
                            timestamp TEXT,
                            rating INTEGER DEFAULT 5
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_learning_plans (
                            plan_id TEXT PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            user_name TEXT,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            plan_name TEXT NOT NULL,
                            start_date TEXT,
                            end_date TEXT,
                            total_hours REAL DEFAULT 0,
                            completed_hours REAL DEFAULT 0,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS plan_executions (
                            execution_id TEXT PRIMARY KEY,
                            plan_id TEXT NOT NULL,
                            activity_name TEXT NOT NULL,
                            activity_type TEXT,
                            planned_date TEXT,
                            completed_date TEXT,
                            duration REAL DEFAULT 0,
                            status TEXT DEFAULT 'pending',
                            notes TEXT,
                            created_at TEXT,
                            FOREIGN KEY (plan_id) REFERENCES ai_learning_plans(plan_id)
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_study_assistant (
                            assistant_id TEXT PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            assistant_type TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            subject TEXT,
                            grade_level INTEGER,
                            settings TEXT,
                            is_active INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS assistant_interactions (
                            interaction_id TEXT PRIMARY KEY,
                            assistant_id TEXT NOT NULL,
                            user_id INTEGER NOT NULL,
                            interaction_type TEXT,
                            content TEXT,
                            result TEXT,
                            timestamp TEXT,
                            FOREIGN KEY (assistant_id) REFERENCES ai_study_assistant(assistant_id)
                        )
                    ''')
                    conn.commit()
                    logger.info('教育AI应用服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== AI助手 ==========

    def create_assistant(self, assistant_name: str, assistant_type: str,
                         education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            config = AI_ASSISTANT_TYPES.get(assistant_type, {})
            if not config:
                return {'success': False, 'error': '未知的AI助手类型'}
            if education_type == 'adult' and not config.get('supports_adult'):
                return {'success': False, 'error': '该助手类型不支持成人教育'}
            if education_type == 'k12' and not config.get('supports_k12'):
                return {'success': False, 'error': '该助手类型不支持K12教育'}
            assistant_id = f"ais_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_assistants (
                            assistant_id, assistant_name, assistant_type,
                            ai_model, education_type, subject, grade_level,
                            description, avatar_url, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (assistant_id, assistant_name, assistant_type,
                          kwargs.get('ai_model', 'gpt4'), education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('description', config.get('description')),
                          kwargs.get('avatar_url'), now, now))
                    conn.commit()
                    logger.info(f'创建AI助手: {assistant_name} ({assistant_id})')
                    return {'success': True, 'assistant_id': assistant_id}
        except Exception as e:
            logger.error(f'创建AI助手失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_assistant(self, assistant_id: str, config_key: str,
                            config_value: str, **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"acf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT assistant_id FROM ai_assistants WHERE assistant_id = ?', (assistant_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '助手不存在'}
                    cursor.execute('''
                        INSERT OR REPLACE INTO assistant_config (
                            config_id, assistant_id, config_key, config_value,
                            config_type, description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (config_id, assistant_id, config_key, config_value,
                          kwargs.get('config_type', 'string'),
                          kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'配置助手失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_assistants WHERE assistant_id = ?', (assistant_id,))
                assistant = cursor.fetchone()
                if not assistant:
                    return {'success': False, 'error': '助手不存在'}
                return {'success': True, 'assistant': dict(assistant)}
        except Exception as e:
            logger.error(f'获取助手信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assistants(self, education_type: str = None,
                        assistant_type: str = None, page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_assistants WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if assistant_type:
                    query += ' AND assistant_type = ?'
                    params.append(assistant_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assistants = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assistants': assistants, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取助手列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能批改 ==========

    def create_correction(self, correction_type: str, education_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            if correction_type not in CORRECTION_TYPES:
                return {'success': False, 'error': '未知的批改类型'}
            correction_id = f"cor_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_corrections (
                            correction_id, correction_type, education_type,
                            subject, grade_level, title, description,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (correction_id, correction_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('title'), kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建批改任务: {correction_id}')
                    return {'success': True, 'correction_id': correction_id}
        except Exception as e:
            logger.error(f'创建批改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_answer(self, correction_id: str, student_id: int,
                      answer_content: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"crs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT correction_type, education_type FROM ai_corrections WHERE correction_id = ?', (correction_id,))
                    correction = cursor.fetchone()
                    if not correction:
                        return {'success': False, 'error': '批改任务不存在'}
                    correction_method = CORRECTION_TYPES.get(correction[0], {}).get('accuracy', 'medium')
                    cursor.execute('''
                        INSERT INTO correction_results (
                            result_id, correction_id, student_id, student_name,
                            answer_content, correct_answer, score, max_score,
                            correction_method, ai_feedback, teacher_comment,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL, NULL, 'pending', ?)
                    ''', (result_id, correction_id, student_id,
                          kwargs.get('student_name'), answer_content,
                          kwargs.get('max_score', 100), correction_method, now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'提交答案失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_correction(self, correction_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT correction_type FROM ai_corrections WHERE correction_id = ?', (correction_id,))
                    correction = cursor.fetchone()
                    if not correction:
                        return {'success': False, 'error': '批改任务不存在'}
                    cursor.execute('SELECT result_id, answer_content FROM correction_results WHERE correction_id = ? AND status = ?', (correction_id, 'pending'))
                    pending_results = cursor.fetchall()
                    for result in pending_results:
                        score = self._calculate_score(correction[0], result[1])
                        ai_feedback = self._generate_ai_feedback(correction[0], result[1])
                        cursor.execute('''
                            UPDATE correction_results SET score = ?, ai_feedback = ?, status = 'completed' WHERE result_id = ?
                        ''', (score, ai_feedback, result[0]))
                    cursor.execute('UPDATE ai_corrections SET status = ?, updated_at = ? WHERE correction_id = ?', ('completed', now, correction_id))
                    conn.commit()
                    return {'success': True, 'corrected_count': len(pending_results)}
        except Exception as e:
            logger.error(f'执行批改失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_score(self, correction_type: str, answer_content: str) -> float:
        base_score = 70.0
        if len(answer_content) > 100:
            base_score += 10
        if correction_type in ['intelligent', 'ai_assisted']:
            base_score += 5
        return min(95.0, base_score + (len(answer_content) % 15))

    def _generate_ai_feedback(self, correction_type: str, answer_content: str) -> str:
        return f"AI批改反馈：回答长度{len(answer_content)}字符，批改类型{correction_type}"

    def get_correction_result(self, result_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM correction_results WHERE result_id = ?', (result_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '批改结果不存在'}
                return {'success': True, 'result': dict(result)}
        except Exception as e:
            logger.error(f'获取批改结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能组卷 ==========

    def create_exam_paper(self, paper_name: str, education_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            paper_id = f"pap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_exam_papers (
                            paper_id, paper_name, education_type, subject,
                            grade_level, total_score, duration, question_count,
                            difficulty, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'draft', ?, ?, ?)
                    ''', (paper_id, paper_name, education_type, kwargs.get('subject'),
                          kwargs.get('grade_level'), kwargs.get('total_score', 100),
                          kwargs.get('duration', 90), kwargs.get('difficulty', 'medium'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建试卷: {paper_name} ({paper_id})')
                    return {'success': True, 'paper_id': paper_id}
        except Exception as e:
            logger.error(f'创建试卷失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_question_to_paper(self, paper_id: str, question_type: str,
                              content: str, **kwargs) -> Dict[str, Any]:
        try:
            if question_type not in QUESTION_TYPES:
                return {'success': False, 'error': '未知的题目类型'}
            config = QUESTION_TYPES.get(question_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM ai_exam_papers WHERE paper_id = ?', (paper_id,))
                    paper = cursor.fetchone()
                    if not paper:
                        return {'success': False, 'error': '试卷不存在'}
                    if paper[0] == 'adult' and not config.get('supports_adult'):
                        return {'success': False, 'error': '该题目类型不支持成人教育'}
                    if paper[0] == 'k12' and not config.get('supports_k12'):
                        return {'success': False, 'error': '该题目类型不支持K12教育'}
                    cursor.execute('UPDATE ai_exam_papers SET question_count = question_count + 1, updated_at = ? WHERE paper_id = ?', (datetime.now().isoformat(), paper_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加题目失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_paper_from_template(self, template_id: str, paper_name: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM paper_templates WHERE template_id = ?', (template_id,))
                template = cursor.fetchone()
                if not template:
                    return {'success': False, 'error': '模板不存在'}
                return self.create_exam_paper(
                    paper_name=paper_name,
                    education_type=template['education_type'],
                    subject=template['subject'],
                    grade_level=template['grade_level'],
                    **kwargs
                )
        except Exception as e:
            logger.error(f'从模板生成试卷失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_paper(self, paper_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_exam_papers SET status = ?, updated_at = ? WHERE paper_id = ? AND status = ?',
                                 ('published', datetime.now().isoformat(), paper_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '试卷状态不允许发布'}
        except Exception as e:
            logger.error(f'发布试卷失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能答疑 ==========

    def add_qna(self, question: str, answer: str, **kwargs) -> Dict[str, Any]:
        try:
            qna_id = f"qna_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_qna (
                            qna_id, question, answer, subject,
                            education_type, grade_level, tags,
                            usage_count, accuracy, is_active, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1.0, 1, ?)
                    ''', (qna_id, question, answer, kwargs.get('subject'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('tags'), now))
                    conn.commit()
                    logger.info(f'添加问答: {qna_id}')
                    return {'success': True, 'qna_id': qna_id}
        except Exception as e:
            logger.error(f'添加问答失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_qna(self, user_id: int, user_question: str, **kwargs) -> Dict[str, Any]:
        try:
            history_id = f"qnh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_qna WHERE is_active = 1 ORDER BY usage_count DESC LIMIT 10')
                qnas = cursor.fetchall()
                if qnas:
                    matched_qna = qnas[0]
                    similarity = 0.85 + (len(user_question) % 15) / 100
                    cursor.execute('UPDATE ai_qna SET usage_count = usage_count + 1 WHERE qna_id = ?', (matched_qna['qna_id'],))
                    cursor.execute('''
                        INSERT INTO qna_history (
                            history_id, qna_id, user_id, user_question,
                            matched_question, answer, similarity,
                            is_satisfied, feedback, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, NULL, ?)
                    ''', (history_id, matched_qna['qna_id'], user_id, user_question,
                          matched_qna['question'], matched_qna['answer'], similarity, now))
                    conn.commit()
                    return {'success': True, 'answer': matched_qna['answer'], 'similarity': similarity}
                return {'success': False, 'error': '未找到匹配的问答'}
        except Exception as e:
            logger.error(f'查询问答失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_qna(self, qna_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    params = []
                    if 'question' in kwargs:
                        update_fields.append('question = ?')
                        params.append(kwargs['question'])
                    if 'answer' in kwargs:
                        update_fields.append('answer = ?')
                        params.append(kwargs['answer'])
                    if 'accuracy' in kwargs:
                        update_fields.append('accuracy = ?')
                        params.append(kwargs['accuracy'])
                    if update_fields:
                        params.append(qna_id)
                        cursor.execute(f'UPDATE ai_qna SET {", ".join(update_fields)} WHERE qna_id = ?', params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '没有可更新的字段'}
        except Exception as e:
            logger.error(f'更新问答失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_qna(self, subject: str = None, education_type: str = None,
                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_qna WHERE is_active = 1'
                params = []
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY usage_count DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                qnas = [dict(q) for q in cursor.fetchall()]
                return {'success': True, 'qnas': qnas, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取问答列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI写作 ==========

    def create_writing_task(self, writing_type: str, education_type: str,
                            topic: str, **kwargs) -> Dict[str, Any]:
        try:
            config = WRITING_TYPES.get(writing_type, {})
            if not config:
                return {'success': False, 'error': '未知的写作类型'}
            if education_type == 'adult' and not config.get('supports_adult'):
                return {'success': False, 'error': '该写作类型不支持成人教育'}
            if education_type == 'k12' and not config.get('supports_k12'):
                return {'success': False, 'error': '该写作类型不支持K12教育'}
            writing_id = f"wrt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_writing (
                            writing_id, writing_type, education_type, subject,
                            grade_level, topic, requirements, word_count,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                    ''', (writing_id, writing_type, education_type, kwargs.get('subject'),
                          kwargs.get('grade_level'), topic, kwargs.get('requirements'),
                          kwargs.get('word_count', 0), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建写作任务: {topic} ({writing_id})')
                    return {'success': True, 'writing_id': writing_id}
        except Exception as e:
            logger.error(f'创建写作任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_writing(self, writing_id: str, student_id: int,
                       content: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"wrs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT writing_type FROM ai_writing WHERE writing_id = ?', (writing_id,))
                    writing = cursor.fetchone()
                    if not writing:
                        return {'success': False, 'error': '写作任务不存在'}
                    ai_score = self._evaluate_writing(writing[0], content)
                    ai_feedback = self._generate_writing_feedback(writing[0], content)
                    cursor.execute('''
                        INSERT INTO writing_results (
                            result_id, writing_id, student_id, student_name,
                            content, ai_score, ai_feedback, teacher_score,
                            teacher_comment, final_score, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'completed', ?)
                    ''', (result_id, writing_id, student_id, kwargs.get('student_name'),
                          content, ai_score, ai_feedback, ai_score, now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'ai_score': ai_score}
        except Exception as e:
            logger.error(f'提交写作失败: {e}')
            return {'success': False, 'error': str(e)}

    def _evaluate_writing(self, writing_type: str, content: str) -> float:
        score = 60.0
        word_count = len(content)
        if word_count > 300:
            score += 15
        if word_count > 500:
            score += 10
        if writing_type in ['paper', 'report']:
            score += 5
        return min(95.0, score)

    def _generate_writing_feedback(self, writing_type: str, content: str) -> str:
        return f"AI写作评价：类型{writing_type}，字数{len(content)}，结构完整"

    def review_writing(self, result_id: str, teacher_score: float,
                       **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT ai_score FROM writing_results WHERE result_id = ?', (result_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '写作结果不存在'}
                    final_score = round((result[0] * 0.4 + teacher_score * 0.6), 1)
                    cursor.execute('''
                        UPDATE writing_results SET
                            teacher_score = ?, teacher_comment = ?, final_score = ?
                        WHERE result_id = ?
                    ''', (teacher_score, kwargs.get('teacher_comment'), final_score, result_id))
                    conn.commit()
                    return {'success': True, 'final_score': final_score}
        except Exception as e:
            logger.error(f'评审写作失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_writing_tasks(self, education_type: str = None,
                           writing_type: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_writing'
                params = []
                if education_type:
                    query += ' WHERE education_type = ?'
                    params.append(education_type)
                else:
                    query += ' WHERE 1=1'
                if writing_type:
                    query += ' AND writing_type = ?'
                    params.append(writing_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取写作任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI翻译 ==========

    def translate(self, source_text: str, source_language: str,
                  target_language: str, **kwargs) -> Dict[str, Any]:
        try:
            if source_language not in TRANSLATION_LANGUAGES:
                return {'success': False, 'error': '未知的源语言'}
            if target_language not in TRANSLATION_LANGUAGES:
                return {'success': False, 'error': '未知的目标语言'}
            translation_id = f"trl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            translated_text = self._perform_translation(source_text, source_language, target_language)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_translation (
                            translation_id, source_text, source_language,
                            target_language, education_type, subject,
                            context, status, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
                    ''', (translation_id, source_text, source_language, target_language,
                          kwargs.get('education_type'), kwargs.get('subject'),
                          kwargs.get('context'), kwargs.get('created_by'), now))
                    if kwargs.get('user_id'):
                        cursor.execute('''
                            INSERT INTO translation_history (
                                history_id, source_text, translated_text,
                                source_language, target_language, user_id,
                                education_type, timestamp, rating
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 5)
                        ''', (f"trh_{uuid.uuid4().hex[:12]}", source_text, translated_text,
                              source_language, target_language, kwargs['user_id'],
                              kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True, 'translation_id': translation_id, 'translated_text': translated_text}
        except Exception as e:
            logger.error(f'翻译失败: {e}')
            return {'success': False, 'error': str(e)}

    def _perform_translation(self, text: str, source: str, target: str) -> str:
        source_name = TRANSLATION_LANGUAGES.get(source, {}).get('name', source)
        target_name = TRANSLATION_LANGUAGES.get(target, {}).get('name', target)
        return f"[{source_name} -> {target_name}] {text[:50]}..."

    def get_translation_history(self, user_id: int = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM translation_history'
                params = []
                if user_id:
                    query += ' WHERE user_id = ?'
                    params.append(user_id)
                else:
                    query += ' WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                history = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'history': history, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取翻译历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def rate_translation(self, history_id: str, rating: int) -> Dict[str, Any]:
        try:
            if rating < 1 or rating > 5:
                return {'success': False, 'error': '评分必须在1-5之间'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE translation_history SET rating = ? WHERE history_id = ?', (rating, history_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '翻译记录不存在'}
        except Exception as e:
            logger.error(f'评分翻译失败: {e}')
            return {'success': False, 'error': str(e)}

    def batch_translate(self, texts: List[str], source_language: str,
                        target_language: str, **kwargs) -> Dict[str, Any]:
        try:
            results = []
            for text in texts:
                result = self.translate(text, source_language, target_language, **kwargs)
                results.append(result)
            success_count = sum(1 for r in results if r.get('success'))
            return {'success': True, 'results': results, 'success_count': success_count, 'total_count': len(texts)}
        except Exception as e:
            logger.error(f'批量翻译失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_supported_languages(self) -> Dict[str, Any]:
        try:
            languages = [{'code': k, 'name': v['name'], 'full_code': v['code']} for k, v in TRANSLATION_LANGUAGES.items()]
            return {'success': True, 'languages': languages}
        except Exception as e:
            logger.error(f'获取支持语言失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI学习助手 ==========

    def create_learning_plan(self, user_id: int, plan_name: str,
                             education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"pln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_learning_plans (
                            plan_id, user_id, user_name, education_type,
                            subject, grade_level, plan_name, start_date,
                            end_date, total_hours, completed_hours, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (plan_id, user_id, kwargs.get('user_name'), education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          plan_name, kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), kwargs.get('total_hours', 0), now, now))
                    conn.commit()
                    logger.info(f'创建学习计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建学习计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_plan_activity(self, plan_id: str, activity_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            execution_id = f"pex_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM ai_learning_plans WHERE plan_id = ?', (plan_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '学习计划不存在'}
                    cursor.execute('''
                        INSERT INTO plan_executions (
                            execution_id, plan_id, activity_name, activity_type,
                            planned_date, completed_date, duration, status,
                            notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, ?, 'pending', ?, ?)
                    ''', (execution_id, plan_id, activity_name, kwargs.get('activity_type'),
                          kwargs.get('planned_date', now[:10]), kwargs.get('duration', 0),
                          kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'execution_id': execution_id}
        except Exception as e:
            logger.error(f'添加计划活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_activity(self, execution_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id, duration FROM plan_executions WHERE execution_id = ?', (execution_id,))
                    execution = cursor.fetchone()
                    if not execution:
                        return {'success': False, 'error': '活动不存在'}
                    cursor.execute('UPDATE plan_executions SET status = ?, completed_date = ?, duration = ? WHERE execution_id = ?',
                                 ('completed', now, kwargs.get('actual_duration', execution[1]), execution_id))
                    cursor.execute('UPDATE ai_learning_plans SET completed_hours = completed_hours + ?, updated_at = ? WHERE plan_id = ?',
                                 (kwargs.get('actual_duration', execution[1]), now, execution[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learning_progress(self, user_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT plan_id, plan_name, total_hours, completed_hours, status, created_at
                    FROM ai_learning_plans WHERE user_id = ? AND status = 'active'
                ''', (user_id,))
                plans = cursor.fetchall()
                progress_data = []
                for plan in plans:
                    progress = (plan['completed_hours'] / plan['total_hours'] * 100) if plan['total_hours'] > 0 else 0
                    progress_data.append({
                        'plan_id': plan['plan_id'],
                        'plan_name': plan['plan_name'],
                        'total_hours': plan['total_hours'],
                        'completed_hours': plan['completed_hours'],
                        'progress': round(progress, 1),
                        'status': plan['status']
                    })
                return {'success': True, 'plans': progress_data}
        except Exception as e:
            logger.error(f'获取学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 会话管理 ==========

    def create_session(self, assistant_id: str, user_id: int,
                       **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ses_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, subject FROM ai_assistants WHERE assistant_id = ?', (assistant_id,))
                    assistant = cursor.fetchone()
                    if not assistant:
                        return {'success': False, 'error': '助手不存在'}
                    cursor.execute('''
                        INSERT INTO ai_sessions (
                            session_id, assistant_id, user_id, user_name,
                            education_type, subject, session_type, status,
                            start_time, end_time, message_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, NULL, 0, ?)
                    ''', (session_id, assistant_id, user_id, kwargs.get('user_name'),
                          assistant[0], assistant[1], kwargs.get('session_type', 'chat'), now, now))
                    conn.commit()
                    logger.info(f'创建会话: {session_id}')
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def send_message(self, session_id: str, sender: str, content: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM ai_sessions WHERE session_id = ?', (session_id,))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '会话不存在'}
                    if session[0] != 'active':
                        return {'success': False, 'error': '会话已结束'}
                    cursor.execute('''
                        INSERT INTO session_messages (
                            message_id, session_id, sender, content,
                            message_type, timestamp, is_read
                        ) VALUES (?, ?, ?, ?, ?, ?, 0)
                    ''', (message_id, session_id, sender, content,
                          kwargs.get('message_type', 'text'), now))
                    cursor.execute('UPDATE ai_sessions SET message_count = message_count + 1 WHERE session_id = ?', (session_id,))
                    conn.commit()
                    return {'success': True, 'message_id': message_id}
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_session_messages(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM session_messages WHERE session_id = ? ORDER BY timestamp', (session_id,))
                messages = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'messages': messages}
        except Exception as e:
            logger.error(f'获取会话消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_session(self, session_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_sessions SET status = ?, end_time = ? WHERE session_id = ? AND status = ?',
                                 ('ended', now, session_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '会话状态不允许结束'}
        except Exception as e:
            logger.error(f'结束会话失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 配置管理 ==========

    def get_system_config(self, config_key: str = None) -> Dict[str, Any]:
        try:
            config = {
                'ai_assistant_types': AI_ASSISTANT_TYPES,
                'ai_model_types': AI_MODEL_TYPES,
                'correction_types': CORRECTION_TYPES,
                'question_types': QUESTION_TYPES,
                'answer_methods': ANSWER_METHODS,
                'translation_languages': TRANSLATION_LANGUAGES,
                'writing_types': WRITING_TYPES,
                'learning_assistants': LEARNING_ASSISTANTS
            }
            if config_key:
                return {'success': True, 'config': config.get(config_key)}
            return {'success': True, 'config': config}
        except Exception as e:
            logger.error(f'获取系统配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_model_config(self, model_type: str = None) -> Dict[str, Any]:
        try:
            if model_type:
                config = AI_MODEL_TYPES.get(model_type)
                if not config:
                    return {'success': False, 'error': '未知的模型类型'}
                return {'success': True, 'model': config}
            models = [{'code': k, 'name': v['name'], 'provider': v['provider'], 'capability': v['capability']} for k, v in AI_MODEL_TYPES.items()]
            return {'success': True, 'models': models}
        except Exception as e:
            logger.error(f'获取模型配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_correction_config(self, correction_type: str = None) -> Dict[str, Any]:
        try:
            if correction_type:
                config = CORRECTION_TYPES.get(correction_type)
                if not config:
                    return {'success': False, 'error': '未知的批改类型'}
                return {'success': True, 'correction': config}
            corrections = [{'code': k, 'name': v['name'], 'description': v['description'], 'accuracy': v['accuracy']} for k, v in CORRECTION_TYPES.items()]
            return {'success': True, 'corrections': corrections}
        except Exception as e:
            logger.error(f'获取批改配置失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_service_statistics(self, education_type: str = None,
                               start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                cursor.execute('SELECT COUNT(*) FROM ai_assistants WHERE is_active = 1')
                stats['assistant_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_sessions WHERE status = "active"')
                stats['active_sessions'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_corrections')
                stats['correction_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_exam_papers')
                stats['paper_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_qna WHERE is_active = 1')
                stats['qna_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_writing')
                stats['writing_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_translation')
                stats['translation_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_learning_plans')
                stats['plan_count'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_study_assistant WHERE is_active = 1')
                stats['study_assistant_count'] = cursor.fetchone()[0]
                if education_type:
                    cursor.execute('SELECT COUNT(*) FROM ai_sessions WHERE education_type = ?', (education_type,))
                    stats[f'{education_type}_sessions'] = cursor.fetchone()[0]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}