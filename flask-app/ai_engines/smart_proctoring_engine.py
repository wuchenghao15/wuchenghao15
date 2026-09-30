# -*- coding: utf-8 -*-
"""
智能监考引擎
提供考试诚信监控、异常行为检测、诚信评分、实时告警等功能
检测维度：切屏/失焦、复制粘贴、答题时间异常、多设备登录、IP切换、面部异常（预留）
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_proctoring_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SmartProctoringEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 异常行为类型权重
VIOLATION_WEIGHTS = {
    'tab_switch': 5,        # 切屏/失焦
    'window_blur': 3,       # 窗口失焦
    'copy_paste': 15,      # 复制粘贴（严重）
    'context_menu': 8,     # 右键菜单
    'devtools': 20,        # 开发者工具（严重）
    'fullscreen_exit': 10, # 退出全屏
    'rapid_answer': 4,     # 答题过快
    'slow_answer': 2,      # 答题过慢（疑似查阅资料）
    'idle_timeout': 6,     # 长时间空闲
    'multi_device': 25,    # 多设备登录（严重）
    'ip_change': 12,       # IP地址变化
    'resolution_change': 7,# 分辨率变化（疑似分屏）
}


class SmartProctoringEngine:
    """智能监考引擎 - 考试诚信监控与异常行为检测"""

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
        # 在线考试会话缓存：session_id -> 监控状态
        self._active_sessions = {}
        self._init_database()
        self._initialized = True
        logger.info("SmartProctoringEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 考试监控会话
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctor_sessions (
                        session_id TEXT PRIMARY KEY,
                        exam_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        status TEXT DEFAULT 'active',
                        integrity_score REAL DEFAULT 100.0,
                        violation_count INTEGER DEFAULT 0,
                        total_weight INTEGER DEFAULT 0,
                        warning_level TEXT DEFAULT 'clean',
                        report_path TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 异常行为记录
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctor_violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        exam_id TEXT NOT NULL,
                        violation_type TEXT NOT NULL,
                        severity TEXT DEFAULT 'minor',
                        weight INTEGER DEFAULT 0,
                        description TEXT,
                        event_data TEXT,
                        occurred_at TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES proctor_sessions(session_id)
                    )
                ''')

                # 诚信历史
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctor_integrity_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        exam_id TEXT,
                        session_id TEXT,
                        score REAL NOT NULL,
                        level TEXT NOT NULL,
                        violation_count INTEGER DEFAULT 0,
                        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, session_id)
                    )
                ''')

                # 监考配置
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctor_config (
                        config_key TEXT PRIMARY KEY,
                        config_value TEXT,
                        description TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 告警记录
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS proctor_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        user_id TEXT NOT NULL,
                        exam_id TEXT,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        acknowledged INTEGER DEFAULT 0,
                        acknowledged_by TEXT,
                        acknowledged_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pv_session ON proctor_violations(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pv_user ON proctor_violations(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pih_user ON proctor_integrity_history(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pa_user ON proctor_alerts(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pa_severity ON proctor_alerts(severity)')

                # 初始化默认配置
                cursor.execute('SELECT COUNT(*) FROM proctor_config')
                if cursor.fetchone()[0] == 0:
                    defaults = [
                        ('enable_tab_switch_detect', 'true', '启用切屏检测'),
                        ('enable_copy_paste_block', 'true', '启用复制粘贴阻止'),
                        ('enable_devtools_detect', 'true', '启用开发者工具检测'),
                        ('enable_multi_device_check', 'true', '启用多设备登录检测'),
                        ('enable_idle_timeout', 'true', '启用空闲超时检测'),
                        ('idle_timeout_seconds', '300', '空闲超时秒数'),
                        ('max_tab_switches', '5', '最大切屏次数（超过告警）'),
                        ('min_answer_seconds', '5', '最小答题秒数（过快告警）'),
                        ('violation_threshold_warning', '15', '违规权重告警阈值'),
                        ('violation_threshold_serious', '40', '违规权重严重阈值'),
                        ('violation_threshold_critical', '70', '违规权重危急阈值'),
                        ('auto_submit_on_critical', 'false', '危急时自动交卷'),
                    ]
                    for k, v, desc in defaults:
                        cursor.execute(
                            'INSERT OR IGNORE INTO proctor_config (config_key, config_value, description) VALUES (?, ?, ?)',
                            (k, v, desc)
                        )

                conn.commit()
        except Exception as e:
            logger.error(f"初始化监考引擎数据库失败: {e}")

    def _get_config(self, key: str, default: str = ''):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT config_value FROM proctor_config WHERE config_key = ?', (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception:
            return default

    # ==================== 监控会话管理 ====================

    def start_monitoring(self, session_id: str, exam_id: str, user_id: str,
                         ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """开始考试监控"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO proctor_sessions
                        (session_id, exam_id, user_id, start_time, ip_address,
                         user_agent, status, integrity_score, violation_count, total_weight,
                         warning_level)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', 100.0, 0, 0, 'clean')
                    ''', (session_id, exam_id, user_id, datetime.now().isoformat(),
                          ip_address, user_agent))
                    conn.commit()

                # 检查多设备登录
                self._check_multi_device(exam_id, user_id, session_id, ip_address)

                # 更新内存缓存
                self._active_sessions[session_id] = {
                    'exam_id': exam_id,
                    'user_id': user_id,
                    'start_time': time.time(),
                    'violations': 0,
                    'weight': 0,
                    'last_activity': time.time(),
                }

                logger.info(f"开始监控: session={session_id}, user={user_id}, exam={exam_id}")
                return {
                    'success': True,
                    'session_id': session_id,
                    'integrity_score': 100.0,
                    'message': '考试监控已启动'
                }
            except Exception as e:
                logger.error(f"启动监控失败: {e}")
                return {'success': False, 'error': str(e)}

    def end_monitoring(self, session_id: str, auto_submit: bool = False) -> Dict[str, Any]:
        """结束考试监控，生成诚信报告"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    # 获取会话信息
                    cursor.execute('''
                        SELECT exam_id, user_id, integrity_score, violation_count, total_weight, warning_level
                        FROM proctor_sessions WHERE session_id = ?
                    ''', (session_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '监控会话不存在'}

                    exam_id, user_id, score, v_count, weight, level = row

                    # 更新会话状态
                    cursor.execute('''
                        UPDATE proctor_sessions
                        SET status = ?, end_time = ?
                        WHERE session_id = ?
                    ''', ('auto_submitted' if auto_submit else 'completed',
                          datetime.now().isoformat(), session_id))

                    # 记录诚信历史
                    cursor.execute('''
                        INSERT OR REPLACE INTO proctor_integrity_history
                        (user_id, exam_id, session_id, score, level, violation_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, exam_id, session_id, score, level, v_count))

                    conn.commit()

                # 清理内存缓存
                self._active_sessions.pop(session_id, None)

                report = self._generate_report(session_id)
                logger.info(f"结束监控: session={session_id}, 诚信分={score}, 违规={v_count}")
                return {
                    'success': True,
                    'session_id': session_id,
                    'integrity_score': score,
                    'violation_count': v_count,
                    'warning_level': level,
                    'report': report,
                    'auto_submitted': auto_submit
                }
            except Exception as e:
                logger.error(f"结束监控失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 异常行为记录 ====================

    def record_violation(self, session_id: str, user_id: str, exam_id: str,
                         violation_type: str, description: str = '',
                         event_data: Dict = None) -> Dict[str, Any]:
        """记录一次违规行为"""
        with self._lock:
            try:
                weight = VIOLATION_WEIGHTS.get(violation_type, 1)
                severity = self._get_severity(weight)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO proctor_violations
                        (session_id, user_id, exam_id, violation_type, severity,
                         weight, description, event_data, occurred_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, user_id, exam_id, violation_type, severity,
                          weight, description, json.dumps(event_data or {}, ensure_ascii=False),
                          datetime.now().isoformat()))

                    # 更新会话统计
                    cursor.execute('''
                        UPDATE proctor_sessions
                        SET violation_count = violation_count + 1,
                            total_weight = total_weight + ?
                        WHERE session_id = ?
                    ''', (weight, session_id))

                    # 重新计算诚信分
                    cursor.execute('''
                        SELECT total_weight, violation_count FROM proctor_sessions
                        WHERE session_id = ?
                    ''', (session_id,))
                    row = cursor.fetchone()
                    total_weight = row[0] if row else 0
                    v_count = row[1] if row else 0
                    new_score = max(0.0, 100.0 - total_weight * 0.8)
                    new_level = self._score_to_level(new_score, total_weight)

                    cursor.execute('''
                        UPDATE proctor_sessions
                        SET integrity_score = ?, warning_level = ?
                        WHERE session_id = ?
                    ''', (new_score, new_level, session_id))

                    conn.commit()

                # 检查是否需要告警
                self._check_alert_threshold(session_id, user_id, exam_id, violation_type,
                                            weight, total_weight, new_level)

                # 更新内存缓存
                if session_id in self._active_sessions:
                    self._active_sessions[session_id]['violations'] = v_count
                    self._active_sessions[session_id]['weight'] = total_weight
                    self._active_sessions[session_id]['last_activity'] = time.time()

                return {
                    'success': True,
                    'session_id': session_id,
                    'violation_type': violation_type,
                    'severity': severity,
                    'weight': weight,
                    'new_score': new_score,
                    'new_level': new_level,
                    'total_violations': v_count
                }
            except Exception as e:
                logger.error(f"记录违规失败: {e}")
                return {'success': False, 'error': str(e)}

    def record_heartbeat(self, session_id: str, question_index: int = None,
                         answer_seconds: int = None) -> Dict[str, Any]:
        """记录心跳/活动（用于空闲检测和答题时间分析）"""
        with self._lock:
            try:
                if session_id not in self._active_sessions:
                    return {'success': False, 'message': '会话不在活跃监控中'}
                sess = self._active_sessions[session_id]
                now = time.time()
                idle_seconds = now - sess['last_activity']
                sess['last_activity'] = now

                # 检查答题时间异常
                alerts = []
                if answer_seconds is not None:
                    min_seconds = int(self._get_config('min_answer_seconds', '5'))
                    if answer_seconds < min_seconds:
                        # 答题过快
                        self.record_violation(
                            session_id, sess['user_id'], sess['exam_id'],
                            'rapid_answer',
                            f'第{question_index or 0}题仅用{answer_seconds}秒作答',
                            {'question_index': question_index, 'seconds': answer_seconds}
                        )
                        alerts.append('rapid_answer')

                # 检查空闲超时
                idle_timeout = int(self._get_config('idle_timeout_seconds', '300'))
                if idle_seconds > idle_timeout:
                    self.record_violation(
                        session_id, sess['user_id'], sess['exam_id'],
                        'idle_timeout',
                        f'空闲 {int(idle_seconds)} 秒未操作',
                        {'idle_seconds': idle_seconds}
                    )
                    alerts.append('idle_timeout')

                return {
                    'success': True,
                    'session_id': session_id,
                    'idle_seconds': int(idle_seconds),
                    'alerts': alerts
                }
            except Exception as e:
                logger.error(f"记录心跳失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 查询与分析 ====================

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取监控会话状态"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, exam_id, user_id, start_time, end_time,
                           ip_address, status, integrity_score, violation_count,
                           total_weight, warning_level
                    FROM proctor_sessions WHERE session_id = ?
                ''', (session_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '会话不存在'}

                # 获取违规详情
                cursor.execute('''
                    SELECT violation_type, severity, weight, description, occurred_at
                    FROM proctor_violations WHERE session_id = ?
                    ORDER BY occurred_at DESC LIMIT 20
                ''', (session_id,))
                violations = [{
                    'type': r[0], 'severity': r[1], 'weight': r[2],
                    'description': r[3], 'occurred_at': r[4]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'session': {
                    'session_id': row[0], 'exam_id': row[1], 'user_id': row[2],
                    'start_time': row[3], 'end_time': row[4], 'ip_address': row[5],
                    'status': row[6], 'integrity_score': row[7],
                    'violation_count': row[8], 'total_weight': row[9],
                    'warning_level': row[10]
                },
                'recent_violations': violations
            }
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_integrity_history(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """获取用户诚信历史"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT exam_id, session_id, score, level, violation_count, recorded_at
                    FROM proctor_integrity_history
                    WHERE user_id = ? ORDER BY recorded_at DESC LIMIT ?
                ''', (user_id, limit))
                records = [{
                    'exam_id': r[0], 'session_id': r[1], 'score': r[2],
                    'level': r[3], 'violation_count': r[4], 'recorded_at': r[5]
                } for r in cursor.fetchall()]

                # 计算平均分
                avg_score = 100.0
                if records:
                    avg_score = sum(r['score'] for r in records) / len(records)

            return {
                'success': True,
                'user_id': user_id,
                'records': records,
                'total': len(records),
                'average_score': round(avg_score, 2)
            }
        except Exception as e:
            logger.error(f"获取诚信历史失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_active_alerts(self, severity: str = None, acknowledged: int = 0) -> Dict[str, Any]:
        """获取活跃告警列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = 'SELECT id, session_id, user_id, exam_id, alert_type, severity, message, created_at FROM proctor_alerts WHERE acknowledged = ?'
                params = [acknowledged]
                if severity:
                    sql += ' AND severity = ?'
                    params.append(severity)
                sql += ' ORDER BY created_at DESC LIMIT 100'
                cursor.execute(sql, params)
                alerts = [{
                    'id': r[0], 'session_id': r[1], 'user_id': r[2], 'exam_id': r[3],
                    'alert_type': r[4], 'severity': r[5], 'message': r[6], 'created_at': r[7]
                } for r in cursor.fetchall()]
            return {
                'success': True,
                'alerts': alerts,
                'total': len(alerts)
            }
        except Exception as e:
            logger.error(f"获取告警失败: {e}")
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: int, admin_id: str) -> Dict[str, Any]:
        """确认告警"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE proctor_alerts
                    SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
                    WHERE id = ?
                ''', (admin_id, datetime.now().isoformat(), alert_id))
                conn.commit()
            return {'success': True, 'alert_id': alert_id, 'message': '告警已确认'}
        except Exception as e:
            logger.error(f"确认告警失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_exam_proctor_summary(self, exam_id: str) -> Dict[str, Any]:
        """获取单场考试的监考汇总"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*), AVG(integrity_score), SUM(violation_count),
                           SUM(CASE WHEN warning_level='warning' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN warning_level='serious' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN warning_level='critical' THEN 1 ELSE 0 END)
                    FROM proctor_sessions WHERE exam_id = ? AND status != 'active'
                ''', (exam_id,))
                row = cursor.fetchone()
                total, avg_score, total_violations, warn, serious, critical = row

                # 违规类型分布
                cursor.execute('''
                    SELECT violation_type, COUNT(*) as cnt, SUM(weight) as total_w
                    FROM proctor_violations WHERE exam_id = ?
                    GROUP BY violation_type ORDER BY cnt DESC
                ''', (exam_id,))
                type_dist = [{
                    'violation_type': r[0], 'count': r[1], 'total_weight': r[2]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'exam_id': exam_id,
                'total_sessions': total or 0,
                'average_score': round(avg_score or 100, 2),
                'total_violations': total_violations or 0,
                'warning_sessions': warn or 0,
                'serious_sessions': serious or 0,
                'critical_sessions': critical or 0,
                'violation_distribution': type_dist
            }
        except Exception as e:
            logger.error(f"获取考试监考汇总失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取监考引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM proctor_sessions')
                total_sessions = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM proctor_sessions WHERE status='active'")
                active = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM proctor_violations')
                total_violations = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(integrity_score) FROM proctor_sessions')
                avg_score = cursor.fetchone()[0] or 100.0
                cursor.execute('SELECT COUNT(*) FROM proctor_alerts WHERE acknowledged=0')
                pending_alerts = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM proctor_alerts WHERE severity='critical' AND acknowledged=0")
                critical_alerts = cursor.fetchone()[0]

                # 违规类型 Top 5
                cursor.execute('''
                    SELECT violation_type, COUNT(*) as cnt
                    FROM proctor_violations GROUP BY violation_type
                    ORDER BY cnt DESC LIMIT 5
                ''')
                top_violations = [{'type': r[0], 'count': r[1]} for r in cursor.fetchall()]

            return {
                'success': True,
                'total_sessions': total_sessions,
                'active_sessions': active,
                'total_violations': total_violations,
                'average_score': round(avg_score, 2),
                'pending_alerts': pending_alerts,
                'critical_alerts': critical_alerts,
                'top_violations': top_violations
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 内部辅助方法 ====================

    def _get_severity(self, weight: int) -> str:
        if weight >= 20:
            return 'critical'
        elif weight >= 10:
            return 'serious'
        elif weight >= 5:
            return 'warning'
        return 'minor'

    def _score_to_level(self, score: float, total_weight: int) -> str:
        if total_weight >= 70 or score < 30:
            return 'critical'
        elif total_weight >= 40 or score < 60:
            return 'serious'
        elif total_weight >= 15 or score < 85:
            return 'warning'
        return 'clean'

    def _check_multi_device(self, exam_id: str, user_id: str, session_id: str, ip: str):
        """检查多设备登录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, ip_address FROM proctor_sessions
                    WHERE exam_id = ? AND user_id = ? AND status = 'active'
                    AND session_id != ?
                ''', (exam_id, user_id, session_id))
                others = cursor.fetchall()
                if others:
                    for other_sid, other_ip in others:
                        self.record_violation(
                            session_id, user_id, exam_id, 'multi_device',
                            f'检测到多设备登录: 另一会话 {other_sid} (IP: {other_ip})',
                            {'other_session': other_sid, 'other_ip': other_ip}
                        )
        except Exception as e:
            logger.error(f"多设备检查失败: {e}")

    def _check_alert_threshold(self, session_id: str, user_id: str, exam_id: str,
                                violation_type: str, weight: int, total_weight: int, level: str):
        """检查告警阈值并生成告警"""
        try:
            warn_threshold = int(self._get_config('violation_threshold_warning', '15'))
            serious_threshold = int(self._get_config('violation_threshold_serious', '40'))
            critical_threshold = int(self._get_config('violation_threshold_critical', '70'))

            alert_type = None
            severity = None
            message = None

            if total_weight >= critical_threshold and level == 'critical':
                alert_type = 'critical_integrity'
                severity = 'critical'
                message = f'用户 {user_id} 诚信分危急（权重 {total_weight}），触发 {violation_type}'
            elif total_weight >= serious_threshold and level == 'serious':
                alert_type = 'serious_integrity'
                severity = 'serious'
                message = f'用户 {user_id} 诚信分严重（权重 {total_weight}）'
            elif total_weight >= warn_threshold and level == 'warning':
                alert_type = 'integrity_warning'
                severity = 'warning'
                message = f'用户 {user_id} 出现诚信告警（权重 {total_weight}）'

            if alert_type:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO proctor_alerts
                        (session_id, user_id, exam_id, alert_type, severity, message)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (session_id, user_id, exam_id, alert_type, severity, message))
                    conn.commit()

                # 危急时检查是否自动交卷
                if severity == 'critical' and self._get_config('auto_submit_on_critical', 'false') == 'true':
                    logger.warning(f"危急诚信分，自动交卷: session={session_id}")
        except Exception as e:
            logger.error(f"告警检查失败: {e}")

    def _generate_report(self, session_id: str) -> Dict[str, Any]:
        """生成诚信报告"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT violation_type, severity, weight, description, occurred_at
                    FROM proctor_violations WHERE session_id = ?
                    ORDER BY occurred_at
                ''', (session_id,))
                violations = [{
                    'type': r[0], 'severity': r[1], 'weight': r[2],
                    'description': r[3], 'occurred_at': r[4]
                } for r in cursor.fetchall()]

                # 按类型汇总
                type_summary = {}
                for v in violations:
                    t = v['type']
                    if t not in type_summary:
                        type_summary[t] = {'count': 0, 'weight': 0}
                    type_summary[t]['count'] += 1
                    type_summary[t]['weight'] += v['weight']

            return {
                'session_id': session_id,
                'total_violations': len(violations),
                'violations': violations,
                'type_summary': type_summary,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {}


smart_proctoring_engine = SmartProctoringEngine()
