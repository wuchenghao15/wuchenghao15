from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育AI助手服务 (v15.28.0) ==================================== 提供AI学习助手、AI辅导助手、AI写作助手、AI编程助手、AI翻译助手、 AI创作助手、AI分析助手、AI对话助手等综合智能教育服务。  核心能力： 1. AI学习助手 - 智能学习辅助、知识问答、学习进度跟踪 2. AI辅导助手 - 作业辅导、知识点讲解、错题分析 3. AI写作助手 - 论文写作、报告撰写、文案创作 4. AI编程助手 - 代码生成、代码调试、编程指导 5. AI翻译助手 - 多语言翻译、术语翻译、翻译记忆 6. AI创作助手 - 创意写作、诗歌创作、剧本创作 7. AI分析助手 - 数据分析、文本分析、趋势分析 8. AI对话助手 - 智能对话、情感交流、知识问答  差异化支持： - 成人教育：专业技能提升、职业培训、终身学习 - K12教育：学科辅导、作业指导、综合素质培养 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_ai_assistant_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationAI')


# ========== 教育AI助手配置 ==========

ASSISTANT_TYPES = {
    'learning': {'name': '学习助手', 'description': '智能学习辅助、知识问答、学习进度跟踪'},
    'tutoring': {'name': '辅导助手', 'description': '作业辅导、知识点讲解、错题分析'},
    'writing': {'name': '写作助手', 'description': '论文写作、报告撰写、文案创作'},
    'coding': {'name': '编程助手', 'description': '代码生成、代码调试、编程指导'},
    'translation': {'name': '翻译助手', 'description': '多语言翻译、术语翻译、翻译记忆'},
    'creation': {'name': '创作助手', 'description': '创意写作、诗歌创作、剧本创作'},
    'analysis': {'name': '分析助手', 'description': '数据分析、文本分析、趋势分析'},
    'conversation': {'name': '对话助手', 'description': '智能对话、情感交流、知识问答'}
}

AI_MODELS = {
    'gpt4': {'name': 'GPT-4', 'provider': 'OpenAI', 'max_tokens': 8192, 'capabilities': ['all']},
    'gpt35': {'name': 'GPT-3.5', 'provider': 'OpenAI', 'max_tokens': 4096, 'capabilities': ['all']},
    'claude': {'name': 'Claude', 'provider': 'Anthropic', 'max_tokens': 100000, 'capabilities': ['writing', 'analysis',
    'creation']},
    'llama': {'name': 'LLaMA', 'provider': 'Meta', 'max_tokens': 4096, 'capabilities': ['learning', 'tutoring',
    'coding']},
    'mistral': {'name': 'Mistral', 'provider': 'Mistral AI', 'max_tokens': 8192, 'capabilities': ['all']},
    'qwen': {'name': 'Qwen', 'provider': 'Alibaba', 'max_tokens': 8192, 'capabilities': ['all']},
    'baichuan': {'name': 'Baichuan', 'provider': 'Baichuan', 'max_tokens': 8192, 'capabilities': ['learning',
    'tutoring', 'translation']},
    'ernie': {'name': 'ERNIE', 'provider': 'Baidu', 'max_tokens': 8192, 'capabilities': ['learning', 'writing',
    'analysis']}
}

SERVICE_MODES = {
    'conversation': {'name': '对话模式', 'description': '自由对话交流'},
    'qa': {'name': '问答模式', 'description': '提问回答模式'},
    'task': {'name': '任务模式', 'description': '完成特定任务'},
    'learning': {'name': '学习模式', 'description': '系统化学习'},
    'creation': {'name': '创作模式', 'description': '创意内容生成'},
    'analysis': {'name': '分析模式', 'description': '数据文本分析'},
    'translation': {'name': '翻译模式', 'description': '多语言翻译'},
    'coding': {'name': '编程模式', 'description': '代码开发调试'}
}

LEARNING_SCENARIOS = {
    'pre_study': {'name': '课前预习', 'description': '课程内容预先学习'},
    'in_class': {'name': '课堂学习', 'description': '课堂知识掌握'},
    'review': {'name': '课后复习', 'description': '课后知识巩固'},
    'homework': {'name': '作业辅导', 'description': '作业完成指导'},
    'exam_prep': {'name': '考试准备', 'description': '考试复习备考'},
    'paper': {'name': '论文写作', 'description': '学术论文撰写'},
    'project': {'name': '项目研究', 'description': '研究项目开展'},
    'knowledge_expand': {'name': '知识拓展', 'description': '跨学科知识拓展'}
}

WRITING_TYPES = {
    'thesis': {'name': '论文写作', 'description': '学术论文撰写'},
    'report': {'name': '报告撰写', 'description': '各类报告编写'},
    'copywriting': {'name': '文案创作', 'description': '营销文案创作'},
    'email': {'name': '邮件写作', 'description': '商务邮件撰写'},
    'article': {'name': '文章创作', 'description': '文章内容创作'},
    'script': {'name': '剧本创作', 'description': '影视剧本创作'},
    'poetry': {'name': '诗歌创作', 'description': '诗歌文学创作'},
    'prose': {'name': '散文创作', 'description': '散文文学创作'}
}

CODING_LANGUAGES = {
    'python': {'name': 'Python', 'description': '通用编程语言', 'category': 'scripting'},
    'javascript': {'name': 'JavaScript', 'description': 'Web前端语言', 'category': 'web'},
    'java': {'name': 'Java', 'description': '企业级开发语言', 'category': 'enterprise'},
    'cpp': {'name': 'C++', 'description': '系统级开发语言', 'category': 'system'},
    'go': {'name': 'Go', 'description': '云原生开发语言', 'category': 'cloud'},
    'rust': {'name': 'Rust', 'description': '系统安全语言', 'category': 'system'},
    'typescript': {'name': 'TypeScript', 'description': 'JavaScript超集', 'category': 'web'},
    'sql': {'name': 'SQL', 'description': '数据库查询语言', 'category': 'database'}
}

TRANSLATION_LANGUAGES = {
    'zh': {'name': '中文', 'code': 'zh-CN', 'direction': ['en', 'ja', 'ko', 'fr', 'de', 'es', 'ru']},
    'en': {'name': '英语', 'code': 'en-US', 'direction': ['zh', 'ja', 'ko', 'fr', 'de', 'es', 'ru']},
    'ja': {'name': '日语', 'code': 'ja-JP', 'direction': ['zh', 'en', 'ko']},
    'ko': {'name': '韩语', 'code': 'ko-KR', 'direction': ['zh', 'en', 'ja']},
    'fr': {'name': '法语', 'code': 'fr-FR', 'direction': ['zh', 'en']},
    'de': {'name': '德语', 'code': 'de-DE', 'direction': ['zh', 'en']},
    'es': {'name': '西班牙语', 'code': 'es-ES', 'direction': ['zh', 'en']},
    'ru': {'name': '俄语', 'code': 'ru-RU', 'direction': ['zh', 'en']}
}

ANALYSIS_TYPES = {
    'data': {'name': '数据分析', 'description': '数据统计与可视化分析'},
    'text': {'name': '文本分析', 'description': '文本内容深度分析'},
    'sentiment': {'name': '情感分析', 'description': '情感倾向识别分析'},
    'trend': {'name': '趋势分析', 'description': '数据趋势预测分析'},
    'prediction': {'name': '预测分析', 'description': '未来趋势预测'},
    'comparison': {'name': '对比分析', 'description': '多维度对比分析'},
    'correlation': {'name': '关联分析', 'description': '数据关联性分析'},
    'clustering': {'name': '聚类分析', 'description': '数据分组聚类'}
}


class EducationAIAssistantService:
    """教育AI助手服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_assistant ( assistant_id TEXT PRIMARY KEY, assistant_type TEXT NOT NULL, name TEXT NOT NULL, description TEXT, ai_model TEXT DEFAULT 'gpt35', education_type TEXT DEFAULT 'k12', config_json TEXT, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS assistant_config ( config_id TEXT PRIMARY KEY, assistant_id TEXT NOT NULL, config_key TEXT NOT NULL, config_value TEXT, description TEXT, created_at TEXT, updated_at TEXT, UNIQUE(assistant_id, config_key) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_conversation ( conversation_id TEXT PRIMARY KEY, assistant_id TEXT NOT NULL, user_id INTEGER, user_name TEXT, education_type TEXT, service_mode TEXT, status TEXT DEFAULT 'active', message_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS conversation_messages ( message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, ai_model TEXT, tokens_used INTEGER DEFAULT 0, response_time REAL DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_tasks ( task_id TEXT PRIMARY KEY, assistant_id TEXT NOT NULL, user_id INTEGER, user_name TEXT, education_type TEXT, task_type TEXT, task_name TEXT NOT NULL, task_description TEXT, status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'medium', progress INTEGER DEFAULT 0, result_json TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS task_records ( record_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, performed_by TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_learning ( learning_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, learning_scenario TEXT, subject TEXT, topic TEXT, progress REAL DEFAULT 0, status TEXT DEFAULT 'in_progress', total_hours REAL DEFAULT 0, completed_hours REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_records ( record_id TEXT PRIMARY KEY, learning_id TEXT NOT NULL, activity_type TEXT NOT NULL, activity_content TEXT, duration REAL DEFAULT 0, score REAL, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_writing ( writing_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, writing_type TEXT, title TEXT, content TEXT, status TEXT DEFAULT 'draft', word_count INTEGER DEFAULT 0, revision_count INTEGER DEFAULT 0, feedback_json TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS writing_records ( record_id TEXT PRIMARY KEY, writing_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, ai_model TEXT, tokens_used INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_coding ( coding_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, language TEXT, project_name TEXT, code_content TEXT, file_path TEXT, status TEXT DEFAULT 'draft', error_count INTEGER DEFAULT 0, test_results TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS coding_records ( record_id TEXT PRIMARY KEY, coding_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, ai_model TEXT, tokens_used INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_translation ( translation_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, source_lang TEXT, target_lang TEXT, source_text TEXT, translated_text TEXT, status TEXT DEFAULT 'pending', confidence REAL DEFAULT 0, glossary_json TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS translation_records ( record_id TEXT PRIMARY KEY, translation_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, ai_model TEXT, tokens_used INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_creation ( creation_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, creation_type TEXT, title TEXT, content TEXT, status TEXT DEFAULT 'draft', inspiration TEXT, tags TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS creation_records ( record_id TEXT PRIMARY KEY, creation_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, ai_model TEXT, tokens_used INTEGER DEFAULT 0, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS ai_analysis ( analysis_id TEXT PRIMARY KEY, user_id INTEGER, user_name TEXT, education_type TEXT, analysis_type TEXT, input_data TEXT, analysis_result TEXT, status TEXT DEFAULT 'pending', confidence REAL DEFAULT 0, visualization_data TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS analysis_records ( record_id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL, action TEXT NOT NULL, action_detail TEXT, ai_model TEXT, tokens_used INTEGER DEFAULT 0, created_at TEXT ) ''')
                conn.commit()
                logger.info('教育AI助手服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== AI学习助手 ==========

    def start_learning_session(self, user_id: int, user_name: str,
                               learning_scenario: str, subject: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            learning_id = f"lrn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_learning ( learning_id, user_id, user_name, education_type, learning_scenario, subject, topic, progress, status, total_hours, completed_hours, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'in_progress', ?, 0, ?, ?) ''', (learning_id, user_id, user_name, education_type,
                          learning_scenario, subject, kwargs.get('topic'),
                          kwargs.get('total_hours', 1), now, now))
                    conn.commit()
                    logger.info(f'{education_type}学习会话开始: {subject} ({learning_id})')
                    return {'success': True, 'learning_id': learning_id}
        except Exception as e:
            logger.error(f'开始学习会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_learning_activity(self, learning_id: str, activity_type: str,
                                  activity_content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"lrr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO learning_records (record_id, learning_id, activity_type, activity_content, duration, score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, learning_id, activity_type, activity_content,
                                  kwargs.get('duration', 0), kwargs.get('score'), now))
                    if kwargs.get('duration'):
                        cursor.execute('UPDATE ai_learning SET completed_hours = completed_hours + ?, updated_at = ? WHERE learning_id = ?',
                                     (kwargs.get('duration'), now, learning_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录学习活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learning_progress(self, learning_id: str, progress: float,
                                  **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'pending')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_learning SET progress = ?, status = ?, updated_at = ? WHERE learning_id = ?',
                                 (progress, status, now, learning_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '学习记录不存在'}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learning_report(self, user_id: int, education_type: str = None,
                             **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_learning WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                learning_sessions = [dict(s) for s in cursor.fetchall()]
                total_hours = sum(s.get('completed_hours', 0) for s in learning_sessions)
                completed_count = sum(1 for s in learning_sessions if s.get('status') == 'completed')
                return {
                    'success': True,
                    'learning_sessions': learning_sessions,
                    'total_hours': round(total_hours, 2),
                    'total_sessions': len(learning_sessions),
                    'completed_count': completed_count
                }
        except Exception as e:
            logger.error(f'获取学习报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI辅导助手 ==========

    def create_tutoring_session(self, user_id: int, user_name: str,
                                 subject: str, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"tut_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_conversation ( conversation_id, assistant_id, user_id, user_name, education_type, service_mode, status, message_count, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 'qa', 'active', 0, ?, ?) ''', (session_id, f"ast_{education_type}_tutoring", user_id, user_name,
                          education_type, now, now))
                    conn.commit()
                    logger.info(f'{education_type}辅导会话创建: {subject} ({session_id})')
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建辅导会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_homework_help(self, session_id: str, question_text: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO conversation_messages (message_id, conversation_id, role, content, ai_model, tokens_used, response_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (message_id, session_id, 'user', question_text,
                                  kwargs.get('ai_model', 'gpt35'), kwargs.get('tokens_used', 0),
                                  kwargs.get('response_time', 0), now))
                    cursor.execute('UPDATE ai_conversation SET message_count = message_count + 1, updated_at = ? WHERE conversation_id = ?', (now, session_id))
                    conn.commit()
                    return {'success': True, 'message_id': message_id}
        except Exception as e:
            logger.error(f'提交作业辅导失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_wrong_answer(self, user_id: int, question_text: str,
                              user_answer: str, correct_answer: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ana_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            analysis_result = {
                'question': question_text,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'mistake_type': kwargs.get('mistake_type', 'concept'),
                'explanation': kwargs.get('explanation', ''),
                'suggestion': kwargs.get('suggestion', '')
            }
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_analysis ( analysis_id, user_id, user_name, education_type, analysis_type, input_data, analysis_result, status, confidence, created_at, updated_at ) VALUES (?, ?, ?, ?, 'text', ?, ?, 'completed', ?, ?, ?) ''', (analysis_id, user_id, kwargs.get('user_name', ''), education_type,
                          json.dumps({'question': question_text, 'user_answer': user_answer,
                          'correct_answer': correct_answer}),
                          json.dumps(analysis_result), kwargs.get('confidence', 0.9), now, now))
                    conn.commit()
                    return {'success': True, 'analysis_id': analysis_id, 'analysis': analysis_result}
        except Exception as e:
            logger.error(f'错题分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_tutoring_history(self, user_id: int, education_type: str = None,
                             **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_conversation WHERE user_id = ? AND service_mode = ?'
                params = [user_id, 'qa']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(kwargs.get('limit', 20))
                cursor.execute(query, params)
                conversations = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'tutoring_sessions': conversations}
        except Exception as e:
            logger.error(f'获取辅导历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI写作助手 ==========

    def create_writing_project(self, user_id: int, user_name: str,
                                writing_type: str, title: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            writing_id = f"wrt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            content = kwargs.get('content', '')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_writing ( writing_id, user_id, user_name, education_type, writing_type, title, content, status, word_count, revision_count, feedback_json, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, 0, ?, ?, ?) ''', (writing_id, user_id, user_name, education_type,
                          writing_type, title, content, len(content),
                          json.dumps([]), now, now))
                    conn.commit()
                    logger.info(f'{education_type}写作项目创建: {title} ({writing_id})')
                    return {'success': True, 'writing_id': writing_id}
        except Exception as e:
            logger.error(f'创建写作项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_writing_feedback(self, writing_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"wrr_{uuid.uuid4().hex[:12]}"
            feedback = {
                'score': kwargs.get('score', 85),
                'comments': kwargs.get('comments', []),
                'suggestions': kwargs.get('suggestions', []),
                'grammar_check': kwargs.get('grammar_check', []),
                'style_analysis': kwargs.get('style_analysis', {})
            }
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO writing_records (record_id, writing_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, writing_id, 'feedback', json.dumps(feedback),
                                  kwargs.get('ai_model', 'gpt35'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_writing SET feedback_json = ?, revision_count = revision_count + 1, updated_at = ? WHERE writing_id = ?',
                                 (json.dumps(feedback), now, writing_id))
                    conn.commit()
                    return {'success': True, 'feedback': feedback}
        except Exception as e:
            logger.error(f'获取写作反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def revise_writing(self, writing_id: str, revised_content: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"wrr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO writing_records (record_id, writing_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, writing_id, 'revision', revised_content,
                                  kwargs.get('ai_model', 'gpt35'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_writing SET content = ?, word_count = ?, revision_count = revision_count + 1, updated_at = ? WHERE writing_id = ?',
                                 (revised_content, len(revised_content), now, writing_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'修改写作内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_writing(self, writing_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_writing SET status = ?, updated_at = ? WHERE writing_id = ? AND status = ?',
                                 ('published', now, writing_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '写作状态不允许发布'}
        except Exception as e:
            logger.error(f'发布写作失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI编程助手 ==========

    def create_coding_project(self, user_id: int, user_name: str,
                              language: str, project_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            coding_id = f"cod_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_coding ( coding_id, user_id, user_name, education_type, language, project_name, code_content, file_path, status, error_count, test_results, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, ?, ?, ?) ''', (coding_id, user_id, user_name, education_type,
                          language, project_name, kwargs.get('code_content', ''),
                          kwargs.get('file_path'), json.dumps([]), now, now))
                    conn.commit()
                    logger.info(f'{education_type}编程项目创建: {project_name} ({coding_id})')
                    return {'success': True, 'coding_id': coding_id}
        except Exception as e:
            logger.error(f'创建编程项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_code(self, coding_id: str, requirements: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"cdr_{uuid.uuid4().hex[:12]}"
            generated_code = kwargs.get('generated_code', '')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO coding_records (record_id, coding_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, coding_id, 'generate', json.dumps({'requirements': requirements,
                                 'code': generated_code}),
                                  kwargs.get('ai_model', 'gpt4'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_coding SET code_content = ?, updated_at = ? WHERE coding_id = ?',
                                 (generated_code, now, coding_id))
                    conn.commit()
                    return {'success': True, 'generated_code': generated_code}
        except Exception as e:
            logger.error(f'生成代码失败: {e}')
            return {'success': False, 'error': str(e)}

    def debug_code(self, coding_id: str, error_message: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"cdr_{uuid.uuid4().hex[:12]}"
            fix_suggestion = kwargs.get('fix_suggestion', '')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO coding_records (record_id, coding_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, coding_id, 'debug', json.dumps({'error': error_message,
                                 'fix': fix_suggestion}),
                                  kwargs.get('ai_model', 'gpt4'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_coding SET error_count = error_count + 1, updated_at = ? WHERE coding_id = ?',
                                 (now, coding_id))
                    conn.commit()
                    return {'success': True, 'fix_suggestion': fix_suggestion}
        except Exception as e:
            logger.error(f'调试代码失败: {e}')
            return {'success': False, 'error': str(e)}

    def test_code(self, coding_id: str, test_cases: List[Dict], **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"cdr_{uuid.uuid4().hex[:12]}"
            test_results = kwargs.get('test_results', {'passed': 0, 'failed': 0, 'details': []})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO coding_records (record_id, coding_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, coding_id, 'test', json.dumps({'test_cases': test_cases,
                                 'results': test_results}),
                                  kwargs.get('ai_model', 'gpt4'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_coding SET test_results = ?, updated_at = ? WHERE coding_id = ?',
                                 (json.dumps(test_results), now, coding_id))
                    conn.commit()
                    return {'success': True, 'test_results': test_results}
        except Exception as e:
            logger.error(f'测试代码失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_coding_project(self, coding_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_coding SET status = ?, updated_at = ? WHERE coding_id = ? AND status = ?',
                                 ('completed', now, coding_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '编程项目状态不允许完成'}
        except Exception as e:
            logger.error(f'完成编程项目失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI翻译助手 ==========

    def create_translation_task(self, user_id: int, user_name: str,
                                 source_lang: str, target_lang: str,
                                 source_text: str, **kwargs) -> Dict[str, Any]:
        try:
            translation_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_translation ( translation_id, user_id, user_name, education_type, source_lang, target_lang, source_text, translated_text, status, confidence, glossary_json, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, '', 'pending', 0, ?, ?, ?) ''', (translation_id, user_id, user_name, education_type,
                          source_lang, target_lang, source_text,
                          json.dumps(kwargs.get('glossary', {})), now, now))
                    conn.commit()
                    logger.info(f'{education_type}翻译任务创建: {source_lang}->{target_lang} ({translation_id})')
                    return {'success': True, 'translation_id': translation_id}
        except Exception as e:
            logger.error(f'创建翻译任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_translation(self, translation_id: str, translated_text: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"trr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO translation_records (record_id, translation_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, translation_id, 'translate', translated_text,
                                  kwargs.get('ai_model', 'gpt35'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_translation SET translated_text = ?, status = ?, confidence = ?, updated_at = ? WHERE translation_id = ?',
                                 (translated_text, 'completed', kwargs.get('confidence', 0.95), now, translation_id))
                    conn.commit()
                    return {'success': True, 'translated_text': translated_text}
        except Exception as e:
            logger.error(f'执行翻译失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_translation_memory(self, translation_id: str, glossary_item: Dict,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"trr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT glossary_json FROM ai_translation WHERE translation_id = ?', (translation_id,
                    ))
                    row = cursor.fetchone()
                    if row:
                        glossary = json.loads(row[0] or '{}')
                        glossary.update(glossary_item)
                        cursor.execute('UPDATE ai_translation SET glossary_json = ?, updated_at = ? WHERE translation_id = ?',
                                     (json.dumps(glossary), now, translation_id))
                    cursor.execute('INSERT INTO translation_records (record_id, translation_id, action, action_detail, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (record_id, translation_id, 'add_memory', json.dumps(glossary_item), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加翻译记忆失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_translation_history(self, user_id: int, education_type: str = None,
                                **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_translation WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(kwargs.get('limit', 20))
                cursor.execute(query, params)
                translations = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'translations': translations}
        except Exception as e:
            logger.error(f'获取翻译历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI创作助手 ==========

    def create_creation_project(self, user_id: int, user_name: str,
                                 creation_type: str, title: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            creation_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_creation ( creation_id, user_id, user_name, education_type, creation_type, title, content, status, inspiration, tags, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?) ''', (creation_id, user_id, user_name, education_type,
                          creation_type, title, kwargs.get('content', ''),
                          kwargs.get('inspiration', ''),
                          ','.join(kwargs.get('tags', [])), now, now))
                    conn.commit()
                    logger.info(f'{education_type}创作项目创建: {title} ({creation_id})')
                    return {'success': True, 'creation_id': creation_id}
        except Exception as e:
            logger.error(f'创建创作项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_creation_content(self, creation_id: str, prompt: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"crr_{uuid.uuid4().hex[:12]}"
            generated_content = kwargs.get('generated_content', '')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO creation_records (record_id, creation_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, creation_id, 'generate', json.dumps({'prompt': prompt,
                                 'content': generated_content}),
                                  kwargs.get('ai_model', 'claude'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_creation SET content = ?, updated_at = ? WHERE creation_id = ?',
                                 (generated_content, now, creation_id))
                    conn.commit()
                    return {'success': True, 'generated_content': generated_content}
        except Exception as e:
            logger.error(f'生成创作内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def refine_creation(self, creation_id: str, refinement_request: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"crr_{uuid.uuid4().hex[:12]}"
            refined_content = kwargs.get('refined_content', '')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO creation_records (record_id, creation_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, creation_id, 'refine', json.dumps({'request': refinement_request,
                                 'content': refined_content}),
                                  kwargs.get('ai_model', 'claude'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_creation SET content = ?, updated_at = ? WHERE creation_id = ?',
                                 (refined_content, now, creation_id))
                    conn.commit()
                    return {'success': True, 'refined_content': refined_content}
        except Exception as e:
            logger.error(f'优化创作内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_creation(self, creation_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_creation SET status = ?, updated_at = ? WHERE creation_id = ? AND status = ?',
                                 ('published', now, creation_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '创作状态不允许发布'}
        except Exception as e:
            logger.error(f'发布创作失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI分析助手 ==========

    def create_analysis_task(self, user_id: int, user_name: str,
                              analysis_type: str, input_data: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ans_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'adult')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_analysis ( analysis_id, user_id, user_name, education_type, analysis_type, input_data, analysis_result, status, confidence, visualization_data, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, '', 'pending', 0, ?, ?, ?) ''', (analysis_id, user_id, user_name, education_type,
                          analysis_type, input_data,
                          json.dumps(kwargs.get('visualization', {})), now, now))
                    conn.commit()
                    logger.info(f'{education_type}分析任务创建: {analysis_type} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建分析任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_analysis(self, analysis_id: str, analysis_result: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"anr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO analysis_records (record_id, analysis_id, action, action_detail, ai_model, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, analysis_id, 'analyze', analysis_result,
                                  kwargs.get('ai_model', 'gpt4'), kwargs.get('tokens_used', 0), now))
                    cursor.execute('UPDATE ai_analysis SET analysis_result = ?, status = ?, confidence = ?, visualization_data = ?, updated_at = ? WHERE analysis_id = ?',
                                 (analysis_result, 'completed', kwargs.get('confidence', 0.9),
                                  json.dumps(kwargs.get('visualization', {})), now, analysis_id))
                    conn.commit()
                    return {'success': True, 'analysis_result': analysis_result}
        except Exception as e:
            logger.error(f'执行分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_summary(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if analysis:
                    return {'success': True, 'analysis': dict(analysis)}
                return {'success': False, 'error': '分析记录不存在'}
        except Exception as e:
            logger.error(f'获取分析摘要失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_history(self, user_id: int, education_type: str = None,
                             **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_analysis WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(kwargs.get('limit', 20))
                cursor.execute(query, params)
                analyses = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'analyses': analyses}
        except Exception as e:
            logger.error(f'获取分析历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== AI对话助手 ==========

    def create_conversation(self, user_id: int, user_name: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            conversation_id = f"cnv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'k12')
            service_mode = kwargs.get('service_mode', 'conversation')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO ai_conversation ( conversation_id, assistant_id, user_id, user_name, education_type, service_mode, status, message_count, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', 0, ?, ?) ''', (conversation_id, f"ast_{education_type}_conversation", user_id, user_name,
                          education_type, service_mode, now, now))
                    conn.commit()
                    logger.info(f'{education_type}对话创建: {conversation_id}')
                    return {'success': True, 'conversation_id': conversation_id}
        except Exception as e:
            logger.error(f'创建对话失败: {e}')
            return {'success': False, 'error': str(e)}

    def send_message(self, conversation_id: str, content: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO conversation_messages (message_id, conversation_id, role, content, ai_model, tokens_used, response_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (message_id, conversation_id, 'user', content,
                                  kwargs.get('ai_model', 'gpt35'), kwargs.get('tokens_used', 0),
                                  kwargs.get('response_time', 0), now))
                    cursor.execute('UPDATE ai_conversation SET message_count = message_count + 1, updated_at = ? WHERE conversation_id = ?', (now, conversation_id))
                    conn.commit()
                    return {'success': True, 'message_id': message_id}
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_conversation_history(self, conversation_id: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC',
                (conversation_id,))
                messages = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'messages': messages}
        except Exception as e:
            logger.error(f'获取对话历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_conversation(self, conversation_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ai_conversation SET status = ?, updated_at = ? WHERE conversation_id = ? AND status = ?',
                                 ('closed', now, conversation_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'closed'}
                    return {'success': False, 'error': '对话状态不允许关闭'}
        except Exception as e:
            logger.error(f'关闭对话失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计查询 ==========

    def get_service_statistics(self, education_type: str = None,
                               **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                query_base = ''
                params = []
                if education_type:
                    query_base = 'WHERE education_type = ?'
                    params = [education_type]

                cursor.execute(f'SELECT COUNT(*) FROM ai_assistant {query_base}', params)
                stats['total_assistants'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_conversation {query_base}', params)
                stats['total_conversations'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_learning {query_base}', params)
                stats['total_learning_sessions'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_writing {query_base}', params)
                stats['total_writing_projects'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_coding {query_base}', params)
                stats['total_coding_projects'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_translation {query_base}', params)
                stats['total_translations'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_creation {query_base}', params)
                stats['total_creations'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_analysis {query_base}', params)
                stats['total_analyses'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM ai_tasks {query_base}', params)
                stats['total_tasks'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM conversation_messages')
                stats['total_messages'] = cursor.fetchone()[0]

                stats['education_type'] = education_type if education_type else 'all'

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}