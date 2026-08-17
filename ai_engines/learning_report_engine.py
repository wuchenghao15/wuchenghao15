# -*- coding: utf-8 -*-
"""
学情分析报告引擎
生成多维度学情分析报告（周报/月报/学期报），聚合所有 AI 引擎数据
报告类型：周报、月报、学期报、年报、专项报告
聚合数据：考试、错题、学习路径、奖励、预测、监考、分析、日程等所有引擎
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_report_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningReportEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 报告类型
REPORT_TYPES = {
    'weekly': {'name': '周报', 'days': 7, 'auto_generate': True},
    'monthly': {'name': '月报', 'days': 30, 'auto_generate': True},
    'semester': {'name': '学期报', 'days': 120, 'auto_generate': True},
    'annual': {'name': '年报', 'days': 365, 'auto_generate': False},
    'special': {'name': '专项报告', 'days': 0, 'auto_generate': False}  # 自定义周期
}

# 报告范围
REPORT_SCOPES = {
    'student': '学生个人',
    'class': '班级',
    'grade': '年级',
    'subject': '学科',
    'school': '全校'
}


class LearningReportEngine:
    """学情分析报告引擎 - 跨引擎数据聚合与智能报告生成"""

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
        self._init_database()
        self._initialized = True
        logger.info("LearningReportEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 报告主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_reports (
                        report_id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        target_name TEXT,
                        period_start TEXT NOT NULL,
                        period_end TEXT NOT NULL,
                        title TEXT NOT NULL,
                        summary TEXT,
                        sections TEXT DEFAULT '[]',
                        key_metrics TEXT DEFAULT '{}',
                        insights TEXT DEFAULT '[]',
                        recommendations TEXT DEFAULT '[]',
                        status TEXT DEFAULT 'draft',
                        generated_by TEXT DEFAULT 'auto',
                        reviewed_by TEXT,
                        reviewed_at TEXT,
                        version INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 报告章节表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_sections (
                        section_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        section_key TEXT NOT NULL,
                        section_title TEXT NOT NULL,
                        section_order INTEGER DEFAULT 0,
                        content TEXT DEFAULT '{}',
                        charts TEXT DEFAULT '[]',
                        tables TEXT DEFAULT '[]',
                        summary TEXT,
                        FOREIGN KEY (report_id) REFERENCES learning_reports(report_id)
                    )
                ''')

                # 3. 报告订阅表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_subscriptions (
                        subscription_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        scope TEXT DEFAULT 'student',
                        target_id TEXT,
                        frequency TEXT DEFAULT 'weekly',
                        channel TEXT DEFAULT 'email',
                        active BOOLEAN DEFAULT 1,
                        last_sent TEXT,
                        next_send TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 4. 报告模板表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_templates (
                        template_id TEXT PRIMARY KEY,
                        template_name TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        sections_config TEXT DEFAULT '[]',
                        default_metrics TEXT DEFAULT '[]',
                        description TEXT,
                        is_default BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 5. 报告导出记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_exports (
                        export_id TEXT PRIMARY KEY,
                        report_id TEXT NOT NULL,
                        export_format TEXT DEFAULT 'pdf',
                        file_path TEXT,
                        file_size INTEGER DEFAULT 0,
                        exported_by TEXT,
                        status TEXT DEFAULT 'pending',
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (report_id) REFERENCES learning_reports(report_id)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lr_type ON learning_reports(report_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lr_target ON learning_reports(target_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rs_report ON report_sections(report_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rsub_user ON report_subscriptions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_re_report ON report_exports(report_id)')

                # 初始化默认模板
                self._init_default_templates(cursor)
                conn.commit()
        except Exception as e:
            logger.error(f"初始化学情报告数据库失败: {e}")

    def _init_default_templates(self, cursor):
        """初始化默认报告模板（每次启动都更新默认模板，确保 sections_config 完整）"""
        try:
            templates = [
                {
                    'template_id': 'tpl_student_weekly',
                    'template_name': '学生周报模板',
                    'report_type': 'weekly',
                    'scope': 'student',
                    'sections_config': json.dumps([
                        {'key': 'overview', 'title': '本周学习概览'},
                        {'key': 'study_time', 'title': '学习时长统计'},
                        {'key': 'exam_performance', 'title': '考试表现'},
                        {'key': 'wrong_questions', 'title': '错题分析'},
                        {'key': 'goal_progress', 'title': '目标进度'},
                        {'key': 'recommendations', 'title': '下周建议'}
                    ]),
                    'default_metrics': json.dumps(['study_time', 'exam_count', 'avg_score', 'wrong_count', 'goal_completion']),
                    'description': '学生每周学习情况综合报告',
                    'is_default': 1
                },
                {
                    'template_id': 'tpl_student_monthly',
                    'template_name': '学生月报模板',
                    'report_type': 'monthly',
                    'scope': 'student',
                    'sections_config': json.dumps([
                        {'key': 'overview', 'title': '本月学习概览'},
                        {'key': 'study_trend', 'title': '学习趋势分析'},
                        {'key': 'subject_performance', 'title': '各科表现'},
                        {'key': 'knowledge_mastery', 'title': '知识点掌握'},
                        {'key': 'ability_radar', 'title': '能力雷达图'},
                        {'key': 'achievement', 'title': '奖励成就'},
                        {'key': 'prediction', 'title': '学习预测'},
                        {'key': 'recommendations', 'title': '下月建议'}
                    ]),
                    'default_metrics': json.dumps(['total_study_time', 'avg_score', 'mastery_rate', 'achievement_count', 'risk_level']),
                    'description': '学生每月学习深度分析报告',
                    'is_default': 1
                },
                {
                    'template_id': 'tpl_class_weekly',
                    'template_name': '班级周报模板',
                    'report_type': 'weekly',
                    'scope': 'class',
                    'sections_config': json.dumps([
                        {'key': 'overview', 'title': '班级本周概览'},
                        {'key': 'participation', 'title': '参与度统计'},
                        {'key': 'top_performers', 'title': '优秀学生'},
                        {'key': 'needs_attention', 'title': '需要关注'},
                        {'key': 'subject_distribution', 'title': '学科分布'},
                        {'key': 'recommendations', 'title': '教学建议'}
                    ]),
                    'default_metrics': json.dumps(['active_students', 'avg_score', 'participation_rate', 'top_count', 'risk_count']),
                    'description': '班级整体学习情况周报',
                    'is_default': 1
                }
            ]

            for tpl in templates:
                cursor.execute('''
                    INSERT OR REPLACE INTO report_templates
                    (template_id, template_name, report_type, scope, sections_config,
                     default_metrics, description, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tpl['template_id'], tpl['template_name'], tpl['report_type'],
                      tpl['scope'], tpl['sections_config'], tpl['default_metrics'],
                      tpl['description'], tpl['is_default']))
        except Exception as e:
            logger.error(f"初始化默认模板失败: {e}")

    # ==================== 报告生成 ====================

    def generate_report(self, report_type: str, scope: str, target_id: str,
                       target_name: str = None, period_start: str = None,
                       period_end: str = None, template_id: str = None,
                       generated_by: str = 'auto') -> Dict[str, Any]:
        """生成学情分析报告（核心方法 - 跨引擎聚合）"""
        with self._lock:
            try:
                # 1. 确定时间范围
                end_date = datetime.fromisoformat(period_end) if period_end else datetime.now()
                days = REPORT_TYPES.get(report_type, {}).get('days', 7)
                if not period_start:
                    start_date = end_date - timedelta(days=days)
                else:
                    start_date = datetime.fromisoformat(period_start)

                period_start_str = start_date.isoformat()
                period_end_str = end_date.isoformat()

                # 2. 选择模板
                template = self._get_template(template_id, report_type, scope)

                # 3. 生成报告 ID 和标题
                report_id = f"report_{report_type}_{scope}_{int(time.time())}_{target_id[:8]}"
                title = self._generate_title(report_type, scope, target_name, start_date, end_date)

                # 4. 跨引擎聚合数据
                aggregated_data = self._aggregate_data(scope, target_id, start_date, end_date)

                # 5. 生成各章节
                sections = self._generate_sections(template, aggregated_data, start_date, end_date)

                # 6. 计算关键指标
                key_metrics = self._compute_key_metrics(report_type, scope, aggregated_data)

                # 7. 生成洞察
                insights = self._generate_insights(aggregated_data, key_metrics, scope)

                # 8. 生成建议
                recommendations = self._generate_recommendations(aggregated_data, insights, scope)

                # 9. 生成摘要
                summary = self._generate_summary(report_type, scope, target_name,
                                                 start_date, end_date, key_metrics)

                # 10. 保存报告
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_reports
                        (report_id, report_type, scope, target_id, target_name,
                         period_start, period_end, title, summary, sections,
                         key_metrics, insights, recommendations, status, generated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                    ''', (report_id, report_type, scope, target_id, target_name,
                          period_start_str, period_end_str, title, summary,
                          json.dumps(sections, ensure_ascii=False),
                          json.dumps(key_metrics, ensure_ascii=False),
                          json.dumps(insights, ensure_ascii=False),
                          json.dumps(recommendations, ensure_ascii=False),
                          generated_by))

                    # 保存章节
                    for idx, section in enumerate(sections):
                        section_id = f"sec_{report_id}_{idx}"
                        cursor.execute('''
                            INSERT INTO report_sections
                            (section_id, report_id, section_key, section_title,
                             section_order, content, summary)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (section_id, report_id, section['key'], section['title'],
                              idx, json.dumps(section.get('content', {}), ensure_ascii=False),
                              section.get('summary', '')))
                    conn.commit()

                return {
                    'success': True,
                    'report_id': report_id,
                    'title': title,
                    'report_type': report_type,
                    'scope': scope,
                    'period_start': period_start_str,
                    'period_end': period_end_str,
                    'sections_count': len(sections),
                    'key_metrics': key_metrics,
                    'insights_count': len(insights),
                    'recommendations_count': len(recommendations),
                    'summary': summary
                }
            except Exception as e:
                logger.error(f"生成报告失败: {e}")
                return {'success': False, 'error': str(e)}

    def _aggregate_data(self, scope: str, target_id: str,
                        start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """跨引擎聚合数据"""
        data = {
            'study_records': [],
            'exam_results': [],
            'wrong_questions': [],
            'learning_events': [],
            'rewards': [],
            'predictions': {},
            'proctor_sessions': [],
            'schedules': [],
            'interactions': []
        }

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                period_start = start_date.isoformat()
                period_end = end_date.isoformat()

                # 1. 考试成绩
                try:
                    cursor.execute('''
                        SELECT id, user_id, total_score, created_at, subject
                        FROM exam_results
                        WHERE user_id = ? AND created_at BETWEEN ? AND ?
                        ORDER BY created_at DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['exam_results'] = [{
                        'id': r[0], 'user_id': r[1], 'score': r[2],
                        'date': r[3], 'subject': r[4]
                    } for r in rows]
                except Exception:
                    pass

                # 2. 错题数据
                try:
                    cursor.execute('''
                        SELECT id, user_id, subject, difficulty, status, created_at
                        FROM wrong_questions
                        WHERE user_id = ? AND created_at BETWEEN ? AND ?
                        ORDER BY created_at DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['wrong_questions'] = [{
                        'id': r[0], 'subject': r[2], 'difficulty': r[3],
                        'status': r[4], 'date': r[5]
                    } for r in rows]
                except Exception:
                    pass

                # 3. 学习事件（来自 learning_analytics_engine）
                try:
                    cursor.execute('''
                        SELECT id, user_id, event_type, subject, value, created_at
                        FROM learning_events
                        WHERE user_id = ? AND created_at BETWEEN ? AND ?
                        ORDER BY created_at DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['learning_events'] = [{
                        'event_type': r[2], 'subject': r[3], 'value': r[4], 'date': r[5]
                    } for r in rows]
                except Exception:
                    pass

                # 4. 奖励记录
                try:
                    cursor.execute('''
                        SELECT id, user_id, points, badge_id, achievement_id, created_at
                        FROM user_points
                        WHERE user_id = ? AND created_at BETWEEN ? AND ?
                        ORDER BY created_at DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['rewards'] = [{
                        'points': r[2], 'badge': r[3], 'achievement': r[4], 'date': r[5]
                    } for r in rows]
                except Exception:
                    pass

                # 5. 监考会话
                try:
                    cursor.execute('''
                        SELECT session_id, user_id, exam_id, integrity_score, violations_count, started_at
                        FROM proctor_sessions
                        WHERE user_id = ? AND started_at BETWEEN ? AND ?
                        ORDER BY started_at DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['proctor_sessions'] = [{
                        'session_id': r[0], 'exam_id': r[2], 'integrity_score': r[3],
                        'violations': r[4], 'date': r[5]
                    } for r in rows]
                except Exception:
                    pass

                # 6. 学习日程
                try:
                    cursor.execute('''
                        SELECT id, user_id, title, subject, duration_minutes, completed, scheduled_date
                        FROM study_schedules
                        WHERE user_id = ? AND scheduled_date BETWEEN ? AND ?
                        ORDER BY scheduled_date DESC
                    ''', (target_id, period_start, period_end))
                    rows = cursor.fetchall()
                    data['schedules'] = [{
                        'title': r[2], 'subject': r[3], 'duration': r[4],
                        'completed': bool(r[5]), 'date': r[6]
                    } for r in rows]
                except Exception:
                    pass

                # 7. 学习目标
                try:
                    cursor.execute('''
                        SELECT id, user_id, title, target_value, current_value, progress, status
                        FROM learning_goals
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                    ''', (target_id,))
                    rows = cursor.fetchall()
                    data['goals'] = [{
                        'title': r[2], 'target': r[3], 'current': r[4],
                        'progress': r[5], 'status': r[6]
                    } for r in rows]
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"聚合数据失败: {e}")

        return data

    def _get_template(self, template_id: str, report_type: str, scope: str) -> Dict:
        """获取报告模板"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                row = None
                if template_id:
                    cursor.execute('SELECT * FROM report_templates WHERE template_id = ?',
                                   (template_id,))
                    row = cursor.fetchone()
                else:
                    # 优先按 report_type + scope + is_default 查找
                    cursor.execute('''
                        SELECT * FROM report_templates
                        WHERE report_type = ? AND scope = ? AND is_default = 1
                        LIMIT 1
                    ''', (report_type, scope))
                    row = cursor.fetchone()
                    if not row:
                        # 降级：仅按 report_type 查找
                        cursor.execute('SELECT * FROM report_templates WHERE report_type = ? LIMIT 1',
                                       (report_type,))
                        row = cursor.fetchone()

                if not row:
                    return {'sections_config': [], 'default_metrics': []}

                cols = ['template_id', 'template_name', 'report_type', 'scope',
                        'sections_config', 'default_metrics', 'description', 'is_default',
                        'created_at', 'updated_at']
                template = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
                try:
                    template['sections_config'] = json.loads(template.get('sections_config') or '[]')
                except Exception:
                    template['sections_config'] = []
                try:
                    template['default_metrics'] = json.loads(template.get('default_metrics') or '[]')
                except Exception:
                    template['default_metrics'] = []
                return template
        except Exception:
            return {'sections_config': [], 'default_metrics': []}

    def _generate_title(self, report_type: str, scope: str, target_name: str,
                        start: datetime, end: datetime) -> str:
        """生成报告标题"""
        type_name = REPORT_TYPES.get(report_type, {}).get('name', report_type)
        scope_name = REPORT_SCOPES.get(scope, scope)
        target = target_name or '学习情况'
        return f"{target}{scope_name}{type_name}（{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}）"

    def _generate_sections(self, template: Dict, data: Dict,
                            start: datetime, end: datetime) -> List[Dict]:
        """根据模板生成各章节"""
        sections = []
        for sec_cfg in template.get('sections_config', []):
            key = sec_cfg.get('key', '')
            title = sec_cfg.get('title', key)
            content = self._build_section_content(key, data, start, end)
            summary = self._build_section_summary(key, content)
            sections.append({
                'key': key,
                'title': title,
                'content': content,
                'summary': summary
            })
        return sections

    def _build_section_content(self, key: str, data: Dict,
                                start: datetime, end: datetime) -> Dict[str, Any]:
        """根据章节 key 构建具体内容"""
        content = {}
        try:
            if key == 'overview':
                content = {
                    'period': f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}",
                    'exam_count': len(data.get('exam_results', [])),
                    'event_count': len(data.get('learning_events', [])),
                    'wrong_question_count': len(data.get('wrong_questions', [])),
                    'schedule_count': len(data.get('schedules', []))
                }
            elif key == 'study_time':
                events = data.get('learning_events', [])
                total_minutes = sum(e.get('value', 0) or 0 for e in events if e.get('event_type') == 'study_duration')
                content = {
                    'total_minutes': total_minutes,
                    'total_hours': round(total_minutes / 60, 1),
                    'daily_avg': round(total_minutes / max((end - start).days, 1), 1),
                    'event_count': len(events)
                }
            elif key == 'exam_performance':
                exams = data.get('exam_results', [])
                if exams:
                    scores = [e['score'] for e in exams if e.get('score') is not None]
                    content = {
                        'exam_count': len(exams),
                        'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
                        'highest': max(scores) if scores else 0,
                        'lowest': min(scores) if scores else 0,
                        'subjects': list(set(e.get('subject') for e in exams if e.get('subject')))
                    }
                else:
                    content = {'exam_count': 0, 'message': '本周期内无考试记录'}
            elif key == 'wrong_questions':
                wrongs = data.get('wrong_questions', [])
                subjects_count = {}
                for w in wrongs:
                    subj = w.get('subject', 'unknown')
                    subjects_count[subj] = subjects_count.get(subj, 0) + 1
                content = {
                    'total_count': len(wrongs),
                    'by_subject': subjects_count,
                    'mastered_count': sum(1 for w in wrongs if w.get('status') == 'mastered')
                }
            elif key == 'goal_progress':
                goals = data.get('goals', [])
                completed = sum(1 for g in goals if g.get('status') == 'completed')
                content = {
                    'total_goals': len(goals),
                    'completed': completed,
                    'in_progress': len(goals) - completed,
                    'completion_rate': round(completed / max(len(goals), 1) * 100, 1),
                    'goal_details': goals[:10]
                }
            elif key == 'recommendations':
                content = {'items': []}  # 将在 _generate_recommendations 中填充
            elif key == 'study_trend':
                events = data.get('learning_events', [])
                daily_count = {}
                for e in events:
                    date = (e.get('date') or '')[:10]
                    if date:
                        daily_count[date] = daily_count.get(date, 0) + 1
                content = {
                    'daily_activity': daily_count,
                    'most_active_day': max(daily_count.items(), key=lambda x: x[1]) if daily_count else None
                }
            elif key == 'subject_performance':
                exams = data.get('exam_results', [])
                subject_scores = {}
                for e in exams:
                    subj = e.get('subject', 'unknown')
                    if subj not in subject_scores:
                        subject_scores[subj] = []
                    if e.get('score') is not None:
                        subject_scores[subj].append(e['score'])
                content = {
                    'subjects': {
                        subj: {
                            'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
                            'count': len(scores),
                            'highest': max(scores) if scores else 0
                        }
                        for subj, scores in subject_scores.items()
                    }
                }
            elif key == 'ability_radar':
                content = {
                    'dimensions': ['knowledge_mastery', 'learning_activity',
                                   'answer_accuracy', 'progress_rate', 'collaboration'],
                    'message': '请通过 /api/analytics/radar 获取详细数据'
                }
            elif key == 'achievement':
                rewards = data.get('rewards', [])
                content = {
                    'total_points': sum(r.get('points', 0) for r in rewards),
                    'badge_count': sum(1 for r in rewards if r.get('badge')),
                    'achievement_count': sum(1 for r in rewards if r.get('achievement'))
                }
            elif key == 'prediction':
                content = {
                    'risk_level': 'low',
                    'message': '请通过 /api/prediction 获取详细预测数据'
                }
            elif key == 'top_performers':
                exams = data.get('exam_results', [])
                sorted_exams = sorted(exams, key=lambda x: x.get('score', 0), reverse=True)[:5]
                content = {'top_students': sorted_exams}
            elif key == 'needs_attention':
                wrongs = data.get('wrong_questions', [])
                high_difficulty = [w for w in wrongs if w.get('difficulty') == 'hard']
                content = {
                    'at_risk_count': len(high_difficulty),
                    'details': high_difficulty[:5]
                }
            else:
                content = {'message': f'章节 {key} 暂无数据'}
        except Exception as e:
            logger.error(f"构建章节内容失败 ({key}): {e}")
            content = {'error': str(e)}
        return content

    def _build_section_summary(self, key: str, content: Dict) -> str:
        """构建章节摘要"""
        try:
            if key == 'overview':
                return f"考试 {content.get('exam_count', 0)} 次，错题 {content.get('wrong_question_count', 0)} 道"
            elif key == 'exam_performance':
                return f"平均分 {content.get('avg_score', 0)}，最高 {content.get('highest', 0)}"
            elif key == 'wrong_questions':
                return f"共 {content.get('total_count', 0)} 道错题，已掌握 {content.get('mastered_count', 0)} 道"
            elif key == 'goal_progress':
                return f"目标完成率 {content.get('completion_rate', 0)}%"
            elif key == 'study_time':
                return f"总时长 {content.get('total_hours', 0)} 小时，日均 {content.get('daily_avg', 0)} 分钟"
            return ''
        except Exception:
            return ''

    def _compute_key_metrics(self, report_type: str, scope: str, data: Dict) -> Dict[str, Any]:
        """计算关键指标"""
        metrics = {}
        try:
            exams = data.get('exam_results', [])
            if exams:
                scores = [e.get('score', 0) for e in exams if e.get('score') is not None]
                if scores:
                    metrics['avg_score'] = round(sum(scores) / len(scores), 1)
                    metrics['exam_count'] = len(scores)
                    metrics['highest_score'] = max(scores)
                    metrics['lowest_score'] = min(scores)

            metrics['wrong_question_count'] = len(data.get('wrong_questions', []))
            metrics['learning_event_count'] = len(data.get('learning_events', []))
            metrics['schedule_count'] = len(data.get('schedules', []))

            goals = data.get('goals', [])
            if goals:
                completed = sum(1 for g in goals if g.get('status') == 'completed')
                metrics['goal_completion_rate'] = round(completed / len(goals) * 100, 1)

            rewards = data.get('rewards', [])
            metrics['total_reward_points'] = sum(r.get('points', 0) for r in rewards)

            # 风险等级
            risk_score = 0
            if metrics.get('avg_score', 100) < 60:
                risk_score += 30
            if metrics.get('wrong_question_count', 0) > 20:
                risk_score += 20
            if metrics.get('learning_event_count', 1) < 3:
                risk_score += 15
            metrics['risk_level'] = ('high' if risk_score >= 40
                                     else 'medium' if risk_score >= 20
                                     else 'low')
            metrics['risk_score'] = risk_score
        except Exception as e:
            logger.error(f"计算关键指标失败: {e}")
        return metrics

    def _generate_insights(self, data: Dict, metrics: Dict, scope: str) -> List[str]:
        """生成数据洞察"""
        insights = []
        try:
            avg_score = metrics.get('avg_score')
            if avg_score is not None:
                if avg_score >= 85:
                    insights.append(f"学习成绩优异（平均 {avg_score} 分），保持当前学习强度")
                elif avg_score >= 70:
                    insights.append(f"学习成绩良好（平均 {avg_score} 分），仍有提升空间")
                elif avg_score < 60:
                    insights.append(f"学习成绩不理想（平均 {avg_score} 分），需要重点辅导")

            wrong_count = metrics.get('wrong_question_count', 0)
            if wrong_count > 20:
                insights.append(f"错题数量较多（{wrong_count} 道），建议安排专项错题复习")
            elif wrong_count > 0:
                insights.append(f"错题数量适中（{wrong_count} 道），保持及时订正习惯")

            event_count = metrics.get('learning_event_count', 0)
            if event_count < 3:
                insights.append("学习活跃度偏低，建议增加每日学习投入")

            risk = metrics.get('risk_level')
            if risk == 'high':
                insights.append("综合风险等级为高，需要立即采取干预措施")
            elif risk == 'medium':
                insights.append("综合风险等级为中，建议加强关注")

            goal_rate = metrics.get('goal_completion_rate')
            if goal_rate is not None and goal_rate < 50:
                insights.append(f"目标完成率偏低（{goal_rate}%），建议重新评估目标合理性")
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
        return insights[:10]

    def _generate_recommendations(self, data: Dict, insights: List[str], scope: str) -> List[str]:
        """生成学习建议"""
        recs = []
        try:
            avg_score = next((i for i in insights if '平均' in i), None)
            wrong_count = next((i for i in insights if '错题' in i), None)

            if avg_score and '不理想' in avg_score:
                recs.append("安排 1 对 1 辅导，针对薄弱知识点进行强化训练")
                recs.append("降低后续学习难度，先巩固基础知识")
            elif avg_score and '良好' in avg_score:
                recs.append("保持当前学习节奏，可适当挑战高难度题目")

            if wrong_count and '较多' in wrong_count:
                recs.append("使用错题本智能引擎安排每日 30 分钟错题重练")
                recs.append("针对高频错题相关知识点，观看配套教学视频")

            risk = next((i for i in insights if '风险等级' in i), None)
            if risk and '高' in risk:
                recs.append("建议教师重点关注，每周进行 1 次学习情况沟通")
                recs.append("调整学习计划，优先解决薄弱学科")

            # 通用建议
            recs.append("保持每日规律学习，确保充足睡眠和适当运动")

            if not recs:
                recs.append("整体学习情况良好，建议继续保持")
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
        return recs[:8]

    def _generate_summary(self, report_type: str, scope: str, target_name: str,
                         start: datetime, end: datetime, metrics: Dict) -> str:
        """生成报告摘要"""
        try:
            type_name = REPORT_TYPES.get(report_type, {}).get('name', report_type)
            scope_name = REPORT_SCOPES.get(scope, scope)
            target = target_name or '学习对象'

            avg = metrics.get('avg_score', '暂无')
            exam_count = metrics.get('exam_count', 0)
            wrong_count = metrics.get('wrong_question_count', 0)
            risk = metrics.get('risk_level', '未知')

            risk_cn = {'low': '低', 'medium': '中', 'high': '高'}.get(risk, risk)

            summary = (f"本{type_name}（{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}）"
                       f"针对{scope_name}「{target}」的学情分析："
                       f"参与考试 {exam_count} 次，"
                       f"平均分 {avg}，"
                       f"错题 {wrong_count} 道，"
                       f"综合风险等级：{risk_cn}。")
            return summary
        except Exception:
            return f"{report_type} 报告摘要"

    # ==================== 报告查询 ====================

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """获取报告详情"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_reports WHERE report_id = ?',
                               (report_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '报告不存在'}

                cols = ['report_id', 'report_type', 'scope', 'target_id', 'target_name',
                        'period_start', 'period_end', 'title', 'summary', 'sections',
                        'key_metrics', 'insights', 'recommendations', 'status',
                        'generated_by', 'reviewed_by', 'reviewed_at', 'version',
                        'created_at', 'updated_at']
                result = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}

                # 解析 JSON
                for k in ['sections', 'key_metrics', 'insights', 'recommendations']:
                    if result.get(k):
                        try:
                            result[k] = json.loads(result[k])
                        except Exception:
                            pass

                # 获取章节
                cursor.execute('''
                    SELECT section_key, section_title, section_order, content, summary
                    FROM report_sections WHERE report_id = ?
                    ORDER BY section_order
                ''', (report_id,))
                sec_rows = cursor.fetchall()
                sections = []
                for r in sec_rows:
                    content = r[3]
                    try:
                        content = json.loads(content) if content else {}
                    except Exception:
                        content = {}
                    sections.append({
                        'key': r[0], 'title': r[1], 'order': r[2],
                        'content': content, 'summary': r[4]
                    })
                result['sections'] = sections

                return {'success': True, 'report': result}
        except Exception as e:
            logger.error(f"获取报告失败: {e}")
            return {'success': False, 'error': str(e)}

    def list_reports(self, scope: str = None, target_id: str = None,
                     report_type: str = None, limit: int = 20) -> Dict[str, Any]:
        """列出报告"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT report_id, report_type, scope, target_id, target_name,
                                period_start, period_end, title, status, created_at
                         FROM learning_reports WHERE 1=1'''
                params = []
                if scope:
                    sql += ' AND scope = ?'
                    params.append(scope)
                if target_id:
                    sql += ' AND target_id = ?'
                    params.append(target_id)
                if report_type:
                    sql += ' AND report_type = ?'
                    params.append(report_type)
                sql += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                reports = [{
                    'report_id': r[0], 'report_type': r[1], 'scope': r[2],
                    'target_id': r[3], 'target_name': r[4],
                    'period_start': r[5], 'period_end': r[6],
                    'title': r[7], 'status': r[8], 'created_at': r[9]
                } for r in rows]

                return {
                    'success': True,
                    'reports': reports,
                    'count': len(reports)
                }
        except Exception as e:
            logger.error(f"列出报告失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 订阅与导出 ====================

    def subscribe(self, user_id: str, report_type: str, frequency: str = 'weekly',
                  scope: str = 'student', target_id: str = None,
                  channel: str = 'email') -> Dict[str, Any]:
        """订阅报告"""
        with self._lock:
            try:
                subscription_id = f"sub_{int(time.time())}_{user_id}"
                # 计算下次发送时间
                next_send = self._compute_next_send(frequency)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO report_subscriptions
                        (subscription_id, user_id, report_type, scope, target_id,
                         frequency, channel, active, next_send)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (subscription_id, user_id, report_type, scope, target_id,
                          frequency, channel, next_send))
                    conn.commit()

                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'next_send': next_send,
                    'message': '订阅成功'
                }
            except Exception as e:
                logger.error(f"订阅报告失败: {e}")
                return {'success': False, 'error': str(e)}

    def _compute_next_send(self, frequency: str) -> str:
        """计算下次发送时间"""
        now = datetime.now()
        if frequency == 'daily':
            next_send = now + timedelta(days=1)
            next_send = next_send.replace(hour=8, minute=0, second=0, microsecond=0)
        elif frequency == 'weekly':
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_send = now + timedelta(days=days_until_monday)
            next_send = next_send.replace(hour=8, minute=0, second=0, microsecond=0)
        elif frequency == 'monthly':
            next_month = now.month + 1 if now.month < 12 else 1
            next_year = now.year if now.month < 12 else now.year + 1
            next_send = now.replace(year=next_year, month=next_month, day=1,
                                    hour=8, minute=0, second=0, microsecond=0)
        else:
            next_send = now + timedelta(days=7)
        return next_send.isoformat()

    def get_pending_subscriptions(self) -> Dict[str, Any]:
        """获取待发送的订阅"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    SELECT subscription_id, user_id, report_type, scope, target_id,
                           frequency, channel, next_send
                    FROM report_subscriptions
                    WHERE active = 1 AND next_send <= ?
                ''', (now,))
                rows = cursor.fetchall()

                subs = [{
                    'subscription_id': r[0], 'user_id': r[1],
                    'report_type': r[2], 'scope': r[3], 'target_id': r[4],
                    'frequency': r[5], 'channel': r[6], 'next_send': r[7]
                } for r in rows]

                return {
                    'success': True,
                    'pending': subs,
                    'count': len(subs)
                }
        except Exception as e:
            logger.error(f"获取待发送订阅失败: {e}")
            return {'success': False, 'error': str(e)}

    def create_export(self, report_id: str, export_format: str = 'pdf',
                      exported_by: str = 'auto') -> Dict[str, Any]:
        """创建报告导出任务"""
        with self._lock:
            try:
                export_id = f"exp_{int(time.time())}_{report_id[:8]}"

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO report_exports
                        (export_id, report_id, export_format, exported_by, status)
                        VALUES (?, ?, ?, ?, 'pending')
                    ''', (export_id, report_id, export_format, exported_by))
                    conn.commit()

                return {
                    'success': True,
                    'export_id': export_id,
                    'report_id': report_id,
                    'format': export_format,
                    'message': '导出任务已创建'
                }
            except Exception as e:
                logger.error(f"创建导出任务失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM learning_reports')
                report_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_sections')
                section_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_subscriptions')
                sub_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_subscriptions WHERE active = 1')
                active_sub_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_templates')
                tpl_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_exports')
                export_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM report_exports WHERE status = "completed"')
                completed_exports = cursor.fetchone()[0]

                # 按类型统计
                cursor.execute('SELECT report_type, COUNT(*) FROM learning_reports GROUP BY report_type')
                by_type = {r[0]: r[1] for r in cursor.fetchall()}

                return {
                    'success': True,
                    'reports': report_count,
                    'sections': section_count,
                    'subscriptions': sub_count,
                    'active_subscriptions': active_sub_count,
                    'templates': tpl_count,
                    'exports': export_count,
                    'completed_exports': completed_exports,
                    'by_type': by_type
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
learning_report_engine = LearningReportEngine()
