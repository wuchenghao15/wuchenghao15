from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育智能辅导服务 (v15.24.0) ==================================== 提供智能辅导计划、个性化学习路径、智能答疑、学习分析、作业辅导、 考试辅导、学习反馈和智能推荐等综合智能辅导服务。  核心能力： 1. 智能辅导计划 - 一对一/小班/小组/在线/线下/混合/专题/综合辅导 2. 个性化学习路径 - 根据学习风格和知识水平定制学习路线 3. 智能答疑 - 概念理解/知识应用/分析推理/综合评价等多种问题类型 4. 学习分析 - 学习行为/知识掌握/学习进度/学习效果等多维度分析 5. 作业辅导 - 作业布置/批改/反馈/统计分析 6. 考试辅导 - 单元测验/期中/期末/模拟/资格/认证/竞赛/综合测评 7. 学习反馈 - 即时/延迟/个性化/群体/正面/建设性/详细/简洁反馈 8. 智能推荐 - 内容/资源/课程/学习路径/辅导老师/学习伙伴/活动/任务推荐 9. 预警管理 - 学习预警/风险提示/干预措施/预警历史 10. 统计分析 - 全局数据分析与报表生成  支持教育类型：成人教育 / K12教育 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_tutoring_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationTutoring')


# ========== 辅导配置 ==========

TUTORING_TYPES = {
    'one_on_one': {'name': '一对一辅导', 'description': '专属教师一对一指导', 'duration': 60},
    'small_group': {'name': '小班辅导', 'description': '3-6人精品小班教学', 'duration': 90},
    'team_tutoring': {'name': '小组辅导', 'description': '7-15人小组协作学习', 'duration': 120},
    'online': {'name': '在线辅导', 'description': '网络远程实时互动教学', 'duration': 60},
    'offline': {'name': '线下辅导', 'description': '面对面实体教学', 'duration': 90},
    'hybrid': {'name': '混合辅导', 'description': '线上线下相结合教学', 'duration': 90},
    'special_topic': {'name': '专题辅导', 'description': '特定主题深度讲解', 'duration': 120},
    'comprehensive': {'name': '综合辅导', 'description': '全科综合提升辅导', 'duration': 180}
}

LEARNING_STYLES = {
    'visual': {'name': '视觉型', 'description': '通过图像、图表学习效果最佳'},
    'auditory': {'name': '听觉型', 'description': '通过听讲、讨论学习效果最佳'},
    'kinesthetic': {'name': '动觉型', 'description': '通过实践、操作学习效果最佳'},
    'reading_writing': {'name': '读写型', 'description': '通过阅读、写作学习效果最佳'},
    'social': {'name': '社交型', 'description': '通过合作、互动学习效果最佳'},
    'independent': {'name': '独立型', 'description': '通过自主学习效果最佳'},
    'reflective': {'name': '反思型', 'description': '通过思考、总结学习效果最佳'},
    'active': {'name': '主动型', 'description': '通过主动探索学习效果最佳'}
}

KNOWLEDGE_LEVELS = {
    'introductory': {'name': '入门级', 'description': '基础知识入门', 'progress': 0.1},
    'beginner': {'name': '初级', 'description': '基础概念掌握', 'progress': 0.2},
    'intermediate': {'name': '中级', 'description': '核心知识应用', 'progress': 0.4},
    'advanced': {'name': '高级', 'description': '深入理解与拓展', 'progress': 0.6},
    'expert': {'name': '专家级', 'description': '专业领域精通', 'progress': 0.8},
    'master': {'name': '精通级', 'description': '全方位熟练运用', 'progress': 0.9},
    'legendary': {'name': '大师级', 'description': '领域权威', 'progress': 0.95},
    'mythic': {'name': '传奇级', 'description': '开创与引领', 'progress': 1.0}
}

QUESTION_TYPES = {
    'concept': {'name': '概念理解', 'description': '基础概念与定义理解'},
    'application': {'name': '知识应用', 'description': '运用知识解决问题'},
    'analysis': {'name': '分析推理', 'description': '分析问题并推理结论'},
    'evaluation': {'name': '综合评价', 'description': '综合评估与判断'},
    'innovation': {'name': '创新创造', 'description': '创造性思维与实践'},
    'practice': {'name': '实践操作', 'description': '动手实践与技能操作'},
    'open': {'name': '开放问题', 'description': '无固定答案的开放性问题'},
    'complex': {'name': '复杂问题', 'description': '多维度复杂问题解决'}
}

ANALYSIS_METHODS = {
    'behavior': {'name': '学习行为分析', 'description': '分析学习时间、频率、习惯'},
    'knowledge': {'name': '知识掌握分析', 'description': '分析知识点掌握程度'},
    'progress': {'name': '学习进度分析', 'description': '分析学习计划完成情况'},
    'effectiveness': {'name': '学习效果分析', 'description': '分析学习成果与提升'},
    'motivation': {'name': '学习动机分析', 'description': '分析学习积极性与动力'},
    'style': {'name': '学习风格分析', 'description': '分析学习偏好与方式'},
    'path': {'name': '学习路径分析', 'description': '分析最优学习路线'},
    'pattern': {'name': '学习模式分析', 'description': '分析学习规律与模式'}
}

FEEDBACK_TYPES = {
    'immediate': {'name': '即时反馈', 'description': '实时给出学习反馈'},
    'delayed': {'name': '延迟反馈', 'description': '适当时间后给出反馈'},
    'personalized': {'name': '个性化反馈', 'description': '针对个人特点定制反馈'},
    'group': {'name': '群体反馈', 'description': '面向群体的共性反馈'},
    'positive': {'name': '正面反馈', 'description': '鼓励性、肯定性反馈'},
    'constructive': {'name': '建设性反馈', 'description': '有建设性的改进建议'},
    'detailed': {'name': '详细反馈', 'description': '全面细致的反馈内容'},
    'concise': {'name': '简洁反馈', 'description': '简洁明了的反馈要点'}
}

RECOMMENDATION_TYPES = {
    'content': {'name': '内容推荐', 'description': '推荐学习内容与资料'},
    'resource': {'name': '资源推荐', 'description': '推荐学习资源与工具'},
    'course': {'name': '课程推荐', 'description': '推荐相关课程'},
    'path': {'name': '学习路径推荐', 'description': '推荐最优学习路线'},
    'teacher': {'name': '辅导老师推荐', 'description': '推荐合适的辅导教师'},
    'partner': {'name': '学习伙伴推荐', 'description': '推荐学习搭档'},
    'activity': {'name': '活动推荐', 'description': '推荐学习活动与竞赛'},
    'task': {'name': '任务推荐', 'description': '推荐学习任务与挑战'}
}

EXAM_TYPES = {
    'unit_test': {'name': '单元测验', 'description': '课程单元知识检测', 'duration': 45},
    'midterm': {'name': '期中考试', 'description': '学期中期综合检测', 'duration': 120},
    'final': {'name': '期末考试', 'description': '学期末综合检测', 'duration': 180},
    'simulation': {'name': '模拟考试', 'description': '考前模拟训练', 'duration': 180},
    'qualification': {'name': '资格考试', 'description': '专业资格认证考试', 'duration': 150},
    'certification': {'name': '认证考试', 'description': '技能认证考试', 'duration': 120},
    'competition': {'name': '竞赛考试', 'description': '学科竞赛', 'duration': 90},
    'comprehensive': {'name': '综合测评', 'description': '多维度综合评估', 'duration': 120}
}


class EducationIntelligentTutoringService:
    """教育智能辅导服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS tutoring_plans ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, tutoring_type TEXT NOT NULL, education_type TEXT NOT NULL, subject TEXT, grade_level INTEGER, target_level TEXT, estimated_hours REAL, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'draft', description TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS plan_details ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT NOT NULL, week_number INTEGER, topic TEXT, learning_objectives TEXT, teaching_method TEXT, materials TEXT, assessment_method TEXT, hours REAL DEFAULT 2, FOREIGN KEY (plan_id) REFERENCES tutoring_plans(plan_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_paths ( path_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, education_type TEXT NOT NULL, learning_style TEXT, current_level TEXT, target_level TEXT, subject TEXT, estimated_duration INTEGER, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS path_nodes ( id INTEGER PRIMARY KEY AUTOINCREMENT, path_id TEXT NOT NULL, node_order INTEGER, node_type TEXT, content TEXT, duration_hours REAL, prerequisites TEXT, completed INTEGER DEFAULT 0, completed_at TEXT, FOREIGN KEY (path_id) REFERENCES learning_paths(path_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS intelligent_qna ( qna_id TEXT PRIMARY KEY, question TEXT NOT NULL, question_type TEXT, subject TEXT, knowledge_point TEXT, education_type TEXT, answer TEXT, solution_steps TEXT, difficulty_level INTEGER DEFAULT 1, views INTEGER DEFAULT 0, likes INTEGER DEFAULT 0, status TEXT DEFAULT 'approved', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS qna_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, qna_id TEXT NOT NULL, question_text TEXT, answer_text TEXT, feedback_rating INTEGER, feedback_comment TEXT, created_at TEXT, FOREIGN KEY (qna_id) REFERENCES intelligent_qna(qna_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_analysis ( analysis_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, education_type TEXT, analysis_method TEXT, period_start TEXT, period_end TEXT, status TEXT DEFAULT 'processing', report_url TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS analysis_results ( id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_id TEXT NOT NULL, metric_name TEXT, metric_value TEXT, metric_unit TEXT, trend TEXT, recommendation TEXT, FOREIGN KEY (analysis_id) REFERENCES learning_analysis(analysis_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS homework_tutoring ( homework_id TEXT PRIMARY KEY, subject TEXT NOT NULL, education_type TEXT NOT NULL, grade_level INTEGER, assignment_title TEXT, assignment_content TEXT, deadline TEXT, total_score REAL DEFAULT 100, status TEXT DEFAULT 'assigned', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS homework_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, homework_id TEXT NOT NULL, student_id INTEGER NOT NULL, submission_content TEXT, submission_time TEXT, score REAL, feedback TEXT, status TEXT DEFAULT 'submitted', FOREIGN KEY (homework_id) REFERENCES homework_tutoring(homework_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS exam_tutoring ( exam_id TEXT PRIMARY KEY, exam_name TEXT NOT NULL, exam_type TEXT NOT NULL, education_type TEXT NOT NULL, subject TEXT, grade_level INTEGER, duration_minutes INTEGER, total_score REAL DEFAULT 100, exam_date TEXT, exam_time TEXT, location TEXT, status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS exam_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, score REAL, grade TEXT, rank INTEGER, total_participants INTEGER, status TEXT DEFAULT 'registered', FOREIGN KEY (exam_id) REFERENCES exam_tutoring(exam_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_feedback ( feedback_id TEXT PRIMARY KEY, feedback_type TEXT NOT NULL, education_type TEXT NOT NULL, subject TEXT, grade_level INTEGER, template_content TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS feedback_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id TEXT NOT NULL, student_id INTEGER NOT NULL, student_name TEXT, feedback_content TEXT, sent_time TEXT, read_time TEXT, FOREIGN KEY (feedback_id) REFERENCES learning_feedback(feedback_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS smart_recommendation ( rec_id TEXT PRIMARY KEY, rec_type TEXT NOT NULL, education_type TEXT NOT NULL, subject TEXT, grade_level INTEGER, content_title TEXT, content_description TEXT, content_url TEXT, recommended_for TEXT, priority INTEGER DEFAULT 1, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS recommendation_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, rec_id TEXT NOT NULL, student_id INTEGER NOT NULL, recommended_at TEXT, viewed INTEGER DEFAULT 0, viewed_at TEXT, clicked INTEGER DEFAULT 0, FOREIGN KEY (rec_id) REFERENCES smart_recommendation(rec_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS tutoring_alerts ( alert_id TEXT PRIMARY KEY, student_id INTEGER NOT NULL, education_type TEXT, alert_type TEXT, alert_level TEXT DEFAULT 'warning', title TEXT, description TEXT, recommended_action TEXT, status TEXT DEFAULT 'active', created_at TEXT, resolved_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alert_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id TEXT NOT NULL, student_id INTEGER NOT NULL, alert_type TEXT, alert_level TEXT, title TEXT, description TEXT, action_taken TEXT, resolved_by TEXT, resolved_at TEXT, FOREIGN KEY (alert_id) REFERENCES tutoring_alerts(alert_id) ) ''')
                conn.commit()
                logger.info('教育智能辅导服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 智能辅导 ==========

    def create_tutoring_plan(self, plan_name: str, tutoring_type: str,
                              education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"tut_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TUTORING_TYPES.get(tutoring_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO tutoring_plans ( plan_id, plan_name, tutoring_type, education_type, subject, grade_level, target_level, estimated_hours, start_date, end_date, status, description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?) ''', (plan_id, plan_name, tutoring_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('target_level'),
                          kwargs.get('estimated_hours', config.get('duration', 60)),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建辅导计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建辅导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_plan_detail(self, plan_id: str, week_number: int, topic: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO plan_details (plan_id, week_number, topic, learning_objectives, teaching_method, materials, assessment_method, hours) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                 (plan_id, week_number, topic,
                                  kwargs.get('learning_objectives'),
                                  kwargs.get('teaching_method'),
                                  kwargs.get('materials'),
                                  kwargs.get('assessment_method'),
                                  kwargs.get('hours', 2)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加计划详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def activate_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tutoring_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 ('active', now, plan_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'active'}
                    return {'success': False, 'error': '计划状态不允许激活'}
        except Exception as e:
            logger.error(f'激活辅导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tutoring_plans WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '计划不存在'}
                cursor.execute('SELECT * FROM plan_details WHERE plan_id = ? ORDER BY week_number', (plan_id,))
                details = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'plan': dict(plan), 'details': details}
        except Exception as e:
            logger.error(f'获取计划详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习路径 ==========

    def create_learning_path(self, student_id: int, education_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            path_id = f"lpa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO learning_paths ( path_id, student_id, education_type, learning_style, current_level, target_level, subject, estimated_duration, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (path_id, student_id, education_type,
                          kwargs.get('learning_style'),
                          kwargs.get('current_level'),
                          kwargs.get('target_level'),
                          kwargs.get('subject'),
                          kwargs.get('estimated_duration', 90), now, now))
                    conn.commit()
                    logger.info(f'创建学习路径: student={student_id} ({path_id})')
                    return {'success': True, 'path_id': path_id}
        except Exception as e:
            logger.error(f'创建学习路径失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_path_node(self, path_id: str, node_order: int, node_type: str,
                       content: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO path_nodes (path_id, node_order, node_type, content, duration_hours, prerequisites) VALUES (?, ?, ?, ?, ?, ?)',
                                 (path_id, node_order, node_type, content,
                                  kwargs.get('duration_hours', 2),
                                  kwargs.get('prerequisites')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加路径节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_node_completed(self, path_id: str, node_order: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE path_nodes SET completed = 1, completed_at = ? WHERE path_id = ? AND node_order = ? AND completed = 0',
                                 (now, path_id, node_order))
                    if cursor.rowcount > 0:
                        conn.commit()
                        cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as done FROM path_nodes WHERE path_id = ?',
                        (path_id,))
                        stats = cursor.fetchone()
                        progress = (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
                        return {'success': True, 'progress': round(progress, 1)}
                    return {'success': False, 'error': '节点不存在或已完成'}
        except Exception as e:
            logger.error(f'标记节点完成失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learning_progress(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_paths WHERE student_id = ?'
                params = [student_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                paths = [dict(p) for p in cursor.fetchall()]
                for path in paths:
                    cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as done FROM path_nodes WHERE path_id = ?',
                    (path['path_id'],))
                    stats = cursor.fetchone()
                    path['progress'] = round(stats['done'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
                return {'success': True, 'paths': paths}
        except Exception as e:
            logger.error(f'获取学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能答疑 ==========

    def add_qna(self, question: str, question_type: str, **kwargs) -> Dict[str, Any]:
        try:
            qna_id = f"qna_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO intelligent_qna ( qna_id, question, question_type, subject, knowledge_point, education_type, answer, solution_steps, difficulty_level, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?) ''', (qna_id, question, question_type,
                          kwargs.get('subject'), kwargs.get('knowledge_point'),
                          kwargs.get('education_type'), kwargs.get('answer'),
                          kwargs.get('solution_steps'),
                          kwargs.get('difficulty_level', 1), now))
                    conn.commit()
                    logger.info(f'添加答疑内容: {qna_id}')
                    return {'success': True, 'qna_id': qna_id}
        except Exception as e:
            logger.error(f'添加答疑内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_qna(self, question: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intelligent_qna WHERE question LIKE ? AND status = ?'
                params = [f'%{question}%', 'approved']
                if kwargs.get('subject'):
                    query += ' AND subject = ?'
                    params.append(kwargs.get('subject'))
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs.get('education_type'))
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'查询答疑内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_qna_interaction(self, student_id: int, qna_id: str,
                                question_text: str, answer_text: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO qna_records (student_id, qna_id, question_text, answer_text, feedback_rating, feedback_comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (student_id, qna_id, question_text, answer_text,
                          kwargs.get('feedback_rating'),
                          kwargs.get('feedback_comment'), now))
                    cursor.execute('UPDATE intelligent_qna SET views = views + 1 WHERE qna_id = ?', (qna_id,))
                    if kwargs.get('feedback_rating') and kwargs.get('feedback_rating') >= 4:
                        cursor.execute('UPDATE intelligent_qna SET likes = likes + 1 WHERE qna_id = ?', (qna_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录答疑交互失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_qna_history(self, student_id: int, page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM qna_records WHERE student_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', (student_id,))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (student_id, page_size, (page - 1) * page_size))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取答疑历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习分析 ==========

    def create_analysis(self, student_id: int, analysis_method: str,
                         period_start: str, period_end: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ana_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO learning_analysis ( analysis_id, student_id, education_type, analysis_method, period_start, period_end, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'processing', ?, ?) ''', (analysis_id, student_id, kwargs.get('education_type'),
                          analysis_method, period_start, period_end, now, now))
                    conn.commit()
                    logger.info(f'创建学习分析: {analysis_id}')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建学习分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_analysis_result(self, analysis_id: str, metric_name: str,
                             metric_value: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO analysis_results (analysis_id, metric_name, metric_value, metric_unit, trend, recommendation) VALUES (?, ?, ?, ?, ?, ?)',
                                 (analysis_id, metric_name, metric_value,
                                  kwargs.get('metric_unit'),
                                  kwargs.get('trend'),
                                  kwargs.get('recommendation')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_analysis(self, analysis_id: str, report_url: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_analysis SET status = ?, report_url = ?, updated_at = ? WHERE analysis_id = ? AND status = ?',
                                 ('completed', report_url, now, analysis_id, 'processing'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '分析状态不允许完成'}
        except Exception as e:
            logger.error(f'完成学习分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_report(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '分析报告不存在'}
                cursor.execute('SELECT * FROM analysis_results WHERE analysis_id = ?', (analysis_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'analysis': dict(analysis), 'results': results}
        except Exception as e:
            logger.error(f'获取分析报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_analysis_history(self, student_id: int, page: int = 1,
                                      page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_analysis WHERE student_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', (student_id,))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (student_id, page_size, (page - 1) * page_size))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学生分析历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 作业辅导 ==========

    def assign_homework(self, subject: str, education_type: str,
                         assignment_title: str, assignment_content: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            homework_id = f"hwm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO homework_tutoring ( homework_id, subject, education_type, grade_level, assignment_title, assignment_content, deadline, total_score, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'assigned', ?, ?) ''', (homework_id, subject, education_type,
                          kwargs.get('grade_level'), assignment_title,
                          assignment_content, kwargs.get('deadline'),
                          kwargs.get('total_score', 100), now, now))
                    conn.commit()
                    logger.info(f'布置作业: {assignment_title} ({homework_id})')
                    return {'success': True, 'homework_id': homework_id}
        except Exception as e:
            logger.error(f'布置作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_homework(self, homework_id: str, student_id: int,
                         submission_content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT deadline FROM homework_tutoring WHERE homework_id = ?', (homework_id,))
                    homework = cursor.fetchone()
                    if not homework:
                        return {'success': False, 'error': '作业不存在'}
                    if homework[0] and now[:10] > homework[0]:
                        return {'success': False, 'error': '已过截止日期'}
                    cursor.execute('INSERT INTO homework_records (homework_id, student_id, submission_content, submission_time, status) VALUES (?, ?, ?, ?, ?)',
                                 (homework_id, student_id, submission_content, now, 'submitted'))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'提交作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_homework(self, homework_id: str, student_id: int,
                        score: float, feedback: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE homework_records SET score = ?, feedback = ?, status = ? WHERE homework_id = ? AND student_id = ? AND status = ?',
                                 (score, feedback, 'graded', homework_id, student_id, 'submitted'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '作业记录不存在或已批改'}
        except Exception as e:
            logger.error(f'批改作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_homework_stats(self, homework_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status = \'graded\' THEN 1 ELSE 0 END) as graded, AVG(score) as avg_score FROM homework_records WHERE homework_id = ?', (homework_id,))
                stats = cursor.fetchone()
                return {'success': True, 'total_submissions': stats[0], 'graded_count': stats[1],
                'average_score': round(stats[2], 2) if stats[2] else 0}
        except Exception as e:
            logger.error(f'获取作业统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 考试辅导 ==========

    def create_exam(self, exam_name: str, exam_type: str, education_type: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            exam_id = f"exm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXAM_TYPES.get(exam_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO exam_tutoring ( exam_id, exam_name, exam_type, education_type, subject, grade_level, duration_minutes, total_score, exam_date, exam_time, location, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?) ''', (exam_id, exam_name, exam_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('duration_minutes', config.get('duration', 90)),
                          kwargs.get('total_score', 100),
                          kwargs.get('exam_date'), kwargs.get('exam_time'),
                          kwargs.get('location'), now, now))
                    conn.commit()
                    logger.info(f'创建考试: {exam_name} ({exam_id})')
                    return {'success': True, 'exam_id': exam_id}
        except Exception as e:
            logger.error(f'创建考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_exam(self, exam_id: str, student_id: int,
                       student_name: str = None) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM exam_tutoring WHERE exam_id = ?', (exam_id,))
                    exam = cursor.fetchone()
                    if not exam:
                        return {'success': False, 'error': '考试不存在'}
                    if exam[0] != 'scheduled':
                        return {'success': False, 'error': '考试状态不允许报名'}
                    cursor.execute('SELECT id FROM exam_records WHERE exam_id = ? AND student_id = ?', (exam_id,
                    student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该考试'}
                    cursor.execute('INSERT INTO exam_records (exam_id, student_id, student_name, status) VALUES (?, ?, ?, ?)',
                                 (exam_id, student_id, student_name, 'registered'))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'考试报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_exam_score(self, exam_id: str, student_id: int,
                           score: float) -> Dict[str, Any]:
        try:
            grade = 'A' if score >= 90 else ('B' if score >= 80 else ('C' if score >= 70 else (
            'D' if score >= 60 else 'F')))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exam_records SET score = ?, grade = ?, status = ? WHERE exam_id = ? AND student_id = ?',
                                 (score, grade, 'completed', exam_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '考试记录不存在'}
        except Exception as e:
            logger.error(f'记录考试成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_exam_ranking(self, exam_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as total FROM exam_records WHERE exam_id = ? AND status = ?', (exam_id,
                'completed'))
                total = cursor.fetchone()['total']
                cursor.execute(''' SELECT student_id, student_name, score, grade, RANK() OVER (ORDER BY score DESC) as rank FROM exam_records WHERE exam_id = ? AND status = ? ORDER BY score DESC ''', (exam_id, 'completed'))
                rankings = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rankings': rankings, 'total_participants': total}
        except Exception as e:
            logger.error(f'获取考试排名失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习反馈 ==========

    def create_feedback_template(self, feedback_type: str, education_type: str,
                                  template_content: str, **kwargs) -> Dict[str, Any]:
        try:
            feedback_id = f"fdb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO learning_feedback ( feedback_id, feedback_type, education_type, subject, grade_level, template_content, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (feedback_id, feedback_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          template_content, now, now))
                    conn.commit()
                    logger.info(f'创建反馈模板: {feedback_id}')
                    return {'success': True, 'feedback_id': feedback_id}
        except Exception as e:
            logger.error(f'创建反馈模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def send_feedback(self, feedback_id: str, student_id: int,
                       student_name: str, feedback_content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO feedback_records (feedback_id, student_id, student_name, feedback_content, sent_time) VALUES (?, ?, ?, ?, ?)',
                                 (feedback_id, student_id, student_name, feedback_content, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'发送反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_feedback_read(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE feedback_records SET read_time = ? WHERE id = ? AND read_time IS NULL',
                                 (now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在或已读'}
        except Exception as e:
            logger.error(f'标记反馈已读失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_feedback_history(self, student_id: int, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT fr.*, lf.feedback_type FROM feedback_records fr JOIN learning_feedback lf ON fr.feedback_id = lf.feedback_id WHERE fr.student_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM feedback_records WHERE student_id = ?', (student_id,))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY fr.sent_time DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (student_id, page_size, (page - 1) * page_size))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取反馈历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能推荐 ==========

    def create_recommendation(self, rec_type: str, education_type: str,
                               content_title: str, content_description: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            rec_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO smart_recommendation ( rec_id, rec_type, education_type, subject, grade_level, content_title, content_description, content_url, recommended_for, priority, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (rec_id, rec_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          content_title, content_description,
                          kwargs.get('content_url'), kwargs.get('recommended_for'),
                          kwargs.get('priority', 1), now, now))
                    conn.commit()
                    logger.info(f'创建推荐: {content_title} ({rec_id})')
                    return {'success': True, 'rec_id': rec_id}
        except Exception as e:
            logger.error(f'创建推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_to_student(self, rec_id: str, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO recommendation_records (rec_id, student_id, recommended_at) VALUES (?, ?, ?)',
                                 (rec_id, student_id, now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '该推荐已发送给此学生'}
        except Exception as e:
            logger.error(f'推荐给学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def track_recommendation_click(self, rec_id: str, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recommendation_records SET viewed = 1, viewed_at = ?, clicked = 1 WHERE rec_id = ? AND student_id = ?',
                                 (now, rec_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推荐记录不存在'}
        except Exception as e:
            logger.error(f'跟踪推荐点击失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_recommendations(self, student_id: int, education_type: str = None,
                                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = ''' SELECT sr.*, rr.viewed, rr.clicked, rr.recommended_at FROM smart_recommendation sr LEFT JOIN recommendation_records rr ON sr.rec_id = rr.rec_id AND rr.student_id = ? WHERE sr.status = ? '''
                params = [student_id, 'active']
                if education_type:
                    query += ' AND sr.education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM smart_recommendation WHERE status = ?', ('active',))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY sr.priority DESC, sr.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                recommendations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'recommendations': recommendations, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学生推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, student_id: int, alert_type: str, title: str,
                      description: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO tutoring_alerts ( alert_id, student_id, education_type, alert_type, alert_level, title, description, recommended_action, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?) ''', (alert_id, student_id, kwargs.get('education_type'),
                          alert_type, kwargs.get('alert_level', 'warning'),
                          title, description, kwargs.get('recommended_action'),
                          now))
                    conn.commit()
                    logger.info(f'创建预警: {title} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, action_taken: str, resolved_by: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, alert_type, alert_level, title, description FROM tutoring_alerts WHERE alert_id = ?', (alert_id,))
                    alert = cursor.fetchone()
                    if not alert:
                        return {'success': False, 'error': '预警不存在'}
                    cursor.execute('UPDATE tutoring_alerts SET status = ?, resolved_at = ? WHERE alert_id = ? AND status = ?',
                                 ('resolved', now, alert_id, 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO alert_history (alert_id, student_id, alert_type, alert_level, title, description, action_taken, resolved_by, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                     (alert_id, alert[0], alert[1], alert[2], alert[3], alert[4], action_taken,
                                     resolved_by, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警已解决或状态不允许'}
        except Exception as e:
            logger.error(f'解决预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_active_alerts(self, student_id: int = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM tutoring_alerts WHERE status = ?'
                params = ['active']
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取活动预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_history(self, student_id: int = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM alert_history'
                params = []
                if student_id:
                    query += ' WHERE student_id = ?'
                    params.append(student_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY resolved_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_overall_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                query_suffix = f" WHERE education_type = '{education_type}'" if education_type else ""

                cursor.execute(f'SELECT COUNT(*) FROM tutoring_plans WHERE status = \'active\'{query_suffix}')
                stats['active_tutoring_plans'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM learning_paths WHERE status = \'active\'{query_suffix}')
                stats['active_learning_paths'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM intelligent_qna WHERE status = \'approved\'')
                stats['approved_qna_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM homework_tutoring{query_suffix}')
                stats['total_homework'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM exam_tutoring{query_suffix}')
                stats['total_exams'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM tutoring_alerts WHERE status = \'active\'{query_suffix}')
                stats['active_alerts'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM learning_analysis WHERE status = \'completed\'{query_suffix}')
                stats['completed_analyses'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM smart_recommendation WHERE status = \'active\'{query_suffix}')
                stats['active_recommendations'] = cursor.fetchone()[0]

                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}






























































































