# -*- coding: utf-8 -*-
"""
智能预警引擎
多维度学生学习风险预警系统：
- 成绩下降、缺勤、活跃度低、作业未交、错题率高等多维风险评分
- 分级预警（蓝/黄/橙/红）+ 自动通知班主任/家长
- 个性化干预措施推荐
- 风险变化趋势追踪
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_warning_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IntelligentWarningEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 预警等级
WARNING_LEVELS = {
    'blue': {
        'name': '关注',
        'color': '#3b82f6',
        'score_range': (30, 50),
        'description': '存在轻微风险，需持续观察',
        'priority': 1
    },
    'yellow': {
        'name': '提醒',
        'color': '#eab308',
        'score_range': (50, 70),
        'description': '存在明显风险，建议干预',
        'priority': 2
    },
    'orange': {
        'name': '警告',
        'color': '#f97316',
        'score_range': (70, 85),
        'description': '风险较高，需立即干预',
        'priority': 3
    },
    'red': {
        'name': '高危',
        'color': '#ef4444',
        'score_range': (85, 100),
        'description': '风险极高，需紧急干预',
        'priority': 4
    }
}

# 风险维度权重
RISK_DIMENSIONS = {
    'score_decline': {
        'name': '成绩下降',
        'weight': 0.25,
        'description': '近期考试成绩下降幅度'
    },
    'attendance': {
        'name': '出勤情况',
        'weight': 0.20,
        'description': '缺勤次数与频率'
    },
    'activity': {
        'name': '学习活跃度',
        'weight': 0.15,
        'description': '系统登录与学习时长'
    },
    'homework': {
        'name': '作业完成',
        'weight': 0.20,
        'description': '作业提交率与质量'
    },
    'wrong_rate': {
        'name': '错题率',
        'weight': 0.20,
        'description': '近期错题占比'
    }
}


class IntelligentWarningEngine:
    """智能预警引擎 - 多维度学生学习风险预警"""

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
        self._init_default_rules()
        self._initialized = True
        logger.info("IntelligentWarningEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 预警记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warning_records (
                        warning_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        class_id TEXT,
                        grade TEXT,
                        level TEXT DEFAULT 'blue',
                        total_score REAL DEFAULT 0,
                        dimensions TEXT DEFAULT '{}',
                        risk_factors TEXT DEFAULT '[]',
                        status TEXT DEFAULT 'active',
                        detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TEXT,
                        resolved_by TEXT,
                        resolution_note TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 预警规则配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warning_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_name TEXT NOT NULL,
                        dimension TEXT NOT NULL,
                        condition_type TEXT,
                        threshold_value REAL,
                        score_weight REAL DEFAULT 1.0,
                        enabled BOOLEAN DEFAULT 1,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 3. 预警通知表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warning_notifications (
                        notification_id TEXT PRIMARY KEY,
                        warning_id TEXT NOT NULL,
                        recipient_id TEXT NOT NULL,
                        recipient_role TEXT,
                        recipient_name TEXT,
                        channel TEXT DEFAULT 'system',
                        title TEXT,
                        content TEXT,
                        status TEXT DEFAULT 'pending',
                        sent_at TEXT,
                        read_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (warning_id) REFERENCES warning_records(warning_id)
                    )
                ''')

                # 4. 干预计划表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intervention_plans (
                        plan_id TEXT PRIMARY KEY,
                        warning_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        plan_type TEXT,
                        actions TEXT DEFAULT '[]',
                        responsible_person TEXT,
                        target_date TEXT,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        effect_evaluation TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (warning_id) REFERENCES warning_records(warning_id)
                    )
                ''')

                # 5. 风险历史轨迹表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warning_history (
                        history_id TEXT PRIMARY KEY,
                        student_id TEXT NOT NULL,
                        snapshot_date TEXT,
                        total_score REAL,
                        level TEXT,
                        dimensions TEXT DEFAULT '{}',
                        trend TEXT DEFAULT 'stable',
                        note TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wr_student ON warning_records(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wr_level ON warning_records(level)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wr_status ON warning_records(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wn_recipient ON warning_notifications(recipient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_student ON intervention_plans(student_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wh_student ON warning_history(student_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化预警引擎数据库失败: {e}")

    def _init_default_rules(self):
        """初始化默认预警规则"""
        default_rules = [
            ('rule_score_decline_severe', '成绩严重下降', 'score_decline', 'relative_drop', 20, 1.0, '考试成绩下降20分以上'),
            ('rule_score_decline_mild', '成绩轻度下降', 'score_decline', 'relative_drop', 10, 0.6, '考试成绩下降10-20分'),
            ('rule_absence_high', '频繁缺勤', 'attendance', 'count_threshold', 5, 1.0, '近30天缺勤5次以上'),
            ('rule_absence_medium', '中等缺勤', 'attendance', 'count_threshold', 3, 0.6, '近30天缺勤3-5次'),
            ('rule_activity_low', '活跃度低', 'activity', 'login_count', 3, 0.8, '近7天登录不足3次'),
            ('rule_homework_missed', '作业未交', 'homework', 'missing_rate', 0.3, 1.0, '作业未交率达30%以上'),
            ('rule_wrong_rate_high', '错题率高', 'wrong_rate', 'ratio_threshold', 0.5, 0.8, '错题率达50%以上'),
        ]
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                for rid, name, dim, cond, thresh, weight, desc in default_rules:
                    cursor.execute('''
                        INSERT OR IGNORE INTO warning_rules
                        (rule_id, rule_name, dimension, condition_type, threshold_value, score_weight, enabled, description)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (rid, name, dim, cond, thresh, weight, desc))
                conn.commit()
        except Exception as e:
            logger.error(f"初始化默认预警规则失败: {e}")

    # ==================== 风险评估核心 ====================

    def assess_student_risk(self, student_id: str, student_name: str = None,
                           class_id: str = None, grade: str = None) -> Dict[str, Any]:
        """评估学生学习风险"""
        with self._lock:
            try:
                # 收集各维度风险数据
                dimensions_data = self._collect_risk_data(student_id)
                # 计算各维度得分（0-100，越高风险越大）
                dimension_scores = {}
                risk_factors = []

                for dim_key, dim_info in RISK_DIMENSIONS.items():
                    dim_data = dimensions_data.get(dim_key, {})
                    score = self._compute_dimension_score(dim_key, dim_data)
                    dimension_scores[dim_key] = {
                        'name': dim_info['name'],
                        'score': round(score, 2),
                        'weight': dim_info['weight'],
                        'weighted_score': round(score * dim_info['weight'], 2),
                        'details': dim_data
                    }
                    if score >= 50:
                        risk_factors.append({
                            'dimension': dim_key,
                            'name': dim_info['name'],
                            'score': round(score, 2),
                            'severity': self._score_to_severity(score)
                        })

                # 计算总分
                total_score = sum(d['weighted_score'] for d in dimension_scores.values())
                # 确定预警等级
                level = self._score_to_level(total_score)

                # 创建/更新预警记录
                warning_id = f"warn_{int(time.time() * 1000)}_{student_id}"
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 检查是否已有活跃预警
                    cursor.execute(
                        'SELECT warning_id, level, total_score FROM warning_records WHERE student_id = ? AND status = ?',
                        (student_id, 'active'))
                    existing = cursor.fetchone()

                    if existing:
                        warning_id = existing[0]
                        prev_score = existing[2]
                        cursor.execute('''
                            UPDATE warning_records
                            SET level = ?, total_score = ?, dimensions = ?, risk_factors = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE warning_id = ?
                        ''', (level, total_score, json.dumps(dimension_scores, ensure_ascii=False),
                              json.dumps(risk_factors, ensure_ascii=False), warning_id))
                        # 记录趋势
                        trend = 'rising' if total_score > prev_score else (
                            'falling' if total_score < prev_score else 'stable')
                    else:
                        cursor.execute('''
                            INSERT INTO warning_records
                            (warning_id, student_id, student_name, class_id, grade,
                             level, total_score, dimensions, risk_factors, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                        ''', (warning_id, student_id, student_name, class_id, grade,
                              level, total_score, json.dumps(dimension_scores, ensure_ascii=False),
                              json.dumps(risk_factors, ensure_ascii=False)))
                        trend = 'new'

                    # 写入历史轨迹
                    cursor.execute('''
                        INSERT INTO warning_history
                        (history_id, student_id, snapshot_date, total_score, level, dimensions, trend)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (f"hist_{int(time.time() * 1000)}_{student_id}", student_id,
                          datetime.now().isoformat(), total_score, level,
                          json.dumps(dimension_scores, ensure_ascii=False), trend))

                    conn.commit()

                result = {
                    'success': True,
                    'warning_id': warning_id,
                    'student_id': student_id,
                    'total_score': round(total_score, 2),
                    'level': level,
                    'level_name': WARNING_LEVELS.get(level, {}).get('name', '未知'),
                    'dimensions': dimension_scores,
                    'risk_factors': risk_factors,
                    'trend': trend,
                    'recommendations': self._recommend_interventions(level, risk_factors)
                }
                logger.info(f"学生 {student_id} 风险评估完成：{level}({total_score:.1f})")
                return result
            except Exception as e:
                logger.error(f"评估学生 {student_id} 风险失败: {e}")
                return {'success': False, 'error': str(e)}

    def _collect_risk_data(self, student_id: str) -> Dict[str, Any]:
        """从各数据源收集风险数据"""
        data = {
            'score_decline': {},
            'attendance': {},
            'activity': {},
            'homework': {},
            'wrong_rate': {}
        }
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 成绩下降维度
                try:
                    cursor.execute('''
                        SELECT total_score, created_at FROM exam_results
                        WHERE student_id = ? ORDER BY created_at DESC LIMIT 5
                    ''', (student_id,))
                    rows = cursor.fetchall()
                    if len(rows) >= 2:
                        scores = [r[0] or 0 for r in rows]
                        latest = scores[0]
                        prev_avg = sum(scores[1:]) / max(len(scores[1:]), 1)
                        data['score_decline'] = {
                            'latest_score': latest,
                            'previous_avg': round(prev_avg, 2),
                            'decline': round(prev_avg - latest, 2),
                            'decline_percent': round((prev_avg - latest) / max(prev_avg, 1) * 100, 2)
                        }
                except Exception:
                    pass

                # 出勤维度
                try:
                    cursor.execute('''
                        SELECT COUNT(*) FROM learning_events
                        WHERE student_id = ? AND event_type = 'absence'
                        AND created_at >= datetime('now', '-30 days')
                    ''', (student_id,))
                    absence_count = cursor.fetchone()[0] or 0
                    data['attendance'] = {'absence_count_30d': absence_count}
                except Exception:
                    pass

                # 活跃度维度
                try:
                    cursor.execute('''
                        SELECT COUNT(DISTINCT DATE(created_at)) FROM learning_events
                        WHERE student_id = ? AND created_at >= datetime('now', '-7 days')
                    ''', (student_id,))
                    active_days = cursor.fetchone()[0] or 0
                    data['activity'] = {'active_days_7d': active_days}
                except Exception:
                    pass

                # 作业维度
                try:
                    cursor.execute('''
                        SELECT COUNT(*) as total,
                        SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as submitted
                        FROM homework_submissions WHERE student_id = ?
                    ''', (student_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        missing_rate = 1 - (row[1] or 0) / row[0]
                        data['homework'] = {
                            'total': row[0],
                            'submitted': row[1] or 0,
                            'missing_rate': round(missing_rate, 2)
                        }
                except Exception:
                    pass

                # 错题率维度
                try:
                    cursor.execute('''
                        SELECT COUNT(*) as total,
                        SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as wrong
                        FROM wrong_questions WHERE student_id = ?
                        AND created_at >= datetime('now', '-30 days')
                    ''', (student_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        wrong_rate = (row[1] or 0) / row[0]
                        data['wrong_rate'] = {
                            'total_30d': row[0],
                            'wrong_30d': row[1] or 0,
                            'wrong_rate': round(wrong_rate, 2)
                        }
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"收集风险数据失败: {e}")
        return data

    def _compute_dimension_score(self, dimension: str, data: Dict) -> float:
        """计算单个维度风险得分（0-100）"""
        if not data:
            return 20.0  # 数据缺失，给基线分

        if dimension == 'score_decline':
            decline = data.get('decline', 0)
            decline_pct = data.get('decline_percent', 0)
            if decline <= 0:
                return 10.0
            score = min(100, decline * 4 + decline_pct)
            return max(10, score)

        elif dimension == 'attendance':
            absence = data.get('absence_count_30d', 0)
            return min(100, absence * 18)

        elif dimension == 'activity':
            active_days = data.get('active_days_7d', 0)
            # 7天活跃0天=100分，3天=50分，7天=10分
            return max(10, min(100, (7 - active_days) * 14))

        elif dimension == 'homework':
            missing_rate = data.get('missing_rate', 0)
            return min(100, missing_rate * 150)

        elif dimension == 'wrong_rate':
            wrong_rate = data.get('wrong_rate', 0)
            return min(100, wrong_rate * 150)

        return 20.0

    def _score_to_level(self, score: float) -> str:
        """根据总分映射预警等级"""
        for level, info in WARNING_LEVELS.items():
            low, high = info['score_range']
            if low <= score < high:
                return level
        return 'red' if score >= 85 else 'blue'

    def _score_to_severity(self, score: float) -> str:
        if score >= 85:
            return 'critical'
        elif score >= 70:
            return 'high'
        elif score >= 50:
            return 'medium'
        return 'low'

    # ==================== 干预推荐 ====================

    def _recommend_interventions(self, level: str, risk_factors: List) -> List[Dict]:
        """根据风险等级和因素推荐干预措施"""
        recommendations = []
        # 等级基础干预
        if level == 'red':
            recommendations.append({
                'priority': 'urgent',
                'type': 'urgent_meeting',
                'title': '紧急约谈',
                'description': '班主任立即与学生进行一对一约谈，了解根本原因'
            })
            recommendations.append({
                'priority': 'urgent',
                'type': 'parent_contact',
                'title': '联系家长',
                'description': '及时通知家长，共同制定帮扶方案'
            })
        elif level == 'orange':
            recommendations.append({
                'priority': 'high',
                'type': 'counseling',
                'title': '心理辅导',
                'description': '安排心理老师介入，了解学习压力情况'
            })

        # 针对性干预
        for factor in risk_factors:
            dim = factor['dimension']
            if dim == 'score_decline':
                recommendations.append({
                    'priority': 'high',
                    'type': 'academic_support',
                    'title': '学业辅导',
                    'description': '安排学科教师进行针对性补习，分析错题原因'
                })
            elif dim == 'attendance':
                recommendations.append({
                    'priority': 'high',
                    'type': 'attendance_monitoring',
                    'title': '考勤监控',
                    'description': '加强日常考勤管理，了解缺勤原因'
                })
            elif dim == 'activity':
                recommendations.append({
                    'priority': 'medium',
                    'type': 'engagement_boost',
                    'title': '激励参与',
                    'description': '通过学习任务和奖励机制提升学习积极性'
                })
            elif dim == 'homework':
                recommendations.append({
                    'priority': 'high',
                    'type': 'homework_supervision',
                    'title': '作业督导',
                    'description': '检查作业完成情况，提供必要辅导'
                })
            elif dim == 'wrong_rate':
                recommendations.append({
                    'priority': 'medium',
                    'type': 'wrong_book_review',
                    'title': '错题复习',
                    'description': '利用错题本智能引擎安排针对性复习'
                })

        # 去重
        seen = set()
        unique_recs = []
        for r in recommendations:
            if r['type'] not in seen:
                seen.add(r['type'])
                unique_recs.append(r)
        return unique_recs

    # ==================== 通知系统 ====================

    def notify_stakeholders(self, warning_id: str, recipients: List[Dict] = None) -> Dict[str, Any]:
        """通知相关方（班主任/家长/学生）"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM warning_records WHERE warning_id = ?', (warning_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '预警记录不存在'}

                    student_id = row[1]
                    student_name = row[2] or student_id
                    level = row[4]
                    try:
                        total_score = float(row[5] or 0)
                    except (TypeError, ValueError):
                        total_score = 0.0
                    level_info = WARNING_LEVELS.get(level, {})

                    if not recipients:
                        recipients = [
                            {'id': f'teacher_{student_id}', 'role': 'teacher', 'name': '班主任'},
                            {'id': f'parent_{student_id}', 'role': 'parent', 'name': '家长'},
                            {'id': student_id, 'role': 'student', 'name': student_name}
                        ]

                    notifications = []
                    for r in recipients:
                        notif_id = f"notif_{int(time.time() * 1000)}_{r['id']}"
                        title = f"【{level_info.get('name', '预警')}】学生{student_name}学习风险预警"
                        content = (f"学生：{student_name}\n"
                                   f"风险等级：{level_info.get('name', level)}\n"
                                   f"风险评分：{total_score:.1f}/100\n"
                                   f"建议：{level_info.get('description', '')}")
                        cursor.execute('''
                            INSERT INTO warning_notifications
                            (notification_id, warning_id, recipient_id, recipient_role,
                             recipient_name, channel, title, content, status)
                            VALUES (?, ?, ?, ?, ?, 'system', ?, ?, 'pending')
                        ''', (notif_id, warning_id, r['id'], r['role'], r.get('name', r['id']),
                              title, content))
                        notifications.append(notif_id)
                    conn.commit()

                return {
                    'success': True,
                    'warning_id': warning_id,
                    'notifications_sent': len(notifications),
                    'notification_ids': notifications
                }
            except Exception as e:
                logger.error(f"发送预警通知失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 查询接口 ====================

    def get_warning(self, warning_id: str) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM warning_records WHERE warning_id = ?', (warning_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '预警记录不存在'}
                    result = dict(row)
                    result['dimensions'] = json.loads(result.get('dimensions') or '{}')
                    result['risk_factors'] = json.loads(result.get('risk_factors') or '[]')
                    return {'success': True, 'warning': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def list_warnings(self, level: str = None, status: str = 'active',
                      class_id: str = None, limit: int = 50) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    sql = 'SELECT * FROM warning_records WHERE 1=1'
                    params = []
                    if level:
                        sql += ' AND level = ?'
                        params.append(level)
                    if status:
                        sql += ' AND status = ?'
                        params.append(status)
                    if class_id:
                        sql += ' AND class_id = ?'
                        params.append(class_id)
                    sql += ' ORDER BY total_score DESC, updated_at DESC LIMIT ?'
                    params.append(limit)
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    warnings = []
                    for r in rows:
                        w = dict(r)
                        w['dimensions'] = json.loads(w.get('dimensions') or '{}')
                        w['risk_factors'] = json.loads(w.get('risk_factors') or '[]')
                        warnings.append(w)
                    return {'success': True, 'warnings': warnings, 'count': len(warnings)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_student_history(self, student_id: str, limit: int = 30) -> Dict[str, Any]:
        """获取学生风险变化历史"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM warning_history
                        WHERE student_id = ? ORDER BY snapshot_date DESC LIMIT ?
                    ''', (student_id, limit))
                    rows = [dict(r) for r in cursor.fetchall()]
                    return {'success': True, 'history': rows, 'count': len(rows)}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 各等级预警数量
                    level_stats = {}
                    for level in WARNING_LEVELS:
                        cursor.execute(
                            'SELECT COUNT(*) FROM warning_records WHERE level = ? AND status = ?',
                            (level, 'active'))
                        level_stats[level] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM warning_records WHERE status = ?', ('active',))
                    total_active = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM warning_records')
                    total_all = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM warning_notifications')
                    total_notifs = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM intervention_plans')
                    total_plans = cursor.fetchone()[0]
                    return {
                        'success': True,
                        'total_active_warnings': total_active,
                        'total_all_warnings': total_all,
                        'level_stats': level_stats,
                        'total_notifications': total_notifs,
                        'total_intervention_plans': total_plans
                    }
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def resolve_warning(self, warning_id: str, resolved_by: str, note: str = None) -> Dict[str, Any]:
        """解除预警"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE warning_records
                        SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP,
                            resolved_by = ?, resolution_note = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE warning_id = ?
                    ''', (resolved_by, note, warning_id))
                    conn.commit()
                    return {'success': True, 'warning_id': warning_id, 'message': '预警已解除'}
            except Exception as e:
                return {'success': False, 'error': str(e)}


# 单例
intelligent_warning_engine = IntelligentWarningEngine()
