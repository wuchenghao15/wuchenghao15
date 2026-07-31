#!/usr/bin/env python3
"""
系统上报服务 (System Report Service)
统一管理全系统数据上报：页面使用、API调用、错误日志、性能指标、AI员工状态等
提供查询、统计、告警功能
"""
import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(_PROJECT_ROOT, 'app.db')


class SystemReportService:
    """系统上报服务"""

    def __init__(self):
        self._init_db()
        logger.info("[SystemReportService] 系统上报服务初始化完成")

    def _init_db(self):
        """初始化上报数据库表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                # 主上报记录表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT UNIQUE,
                        report_type TEXT NOT NULL,
                        module TEXT NOT NULL,
                        severity TEXT DEFAULT 'info',
                        title TEXT,
                        content TEXT,
                        metadata TEXT,
                        reported_by TEXT,
                        status TEXT DEFAULT 'new',
                        created_at TEXT,
                        acknowledged_at TEXT,
                        acknowledged_by TEXT
                    )
                ''')

                # 页面使用统计表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS page_usage_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        page_name TEXT NOT NULL,
                        page_category TEXT,
                        user_id TEXT,
                        session_id TEXT,
                        visit_duration INTEGER DEFAULT 0,
                        actions_count INTEGER DEFAULT 0,
                        features_used TEXT,
                        errors_count INTEGER DEFAULT 0,
                        visited_at TEXT,
                        created_at TEXT
                    )
                ''')

                # API调用统计表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS api_call_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint TEXT NOT NULL,
                        method TEXT,
                        status_code INTEGER,
                        response_time_ms REAL,
                        user_id TEXT,
                        request_data TEXT,
                        error_message TEXT,
                        called_at TEXT,
                        created_at TEXT
                    )
                ''')

                # 系统性能指标表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_performance_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        metric_unit TEXT,
                        category TEXT,
                        threshold_warning REAL,
                        threshold_critical REAL,
                        status TEXT DEFAULT 'normal',
                        recorded_at TEXT,
                        created_at TEXT
                    )
                ''')

                # AI员工状态上报表
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ai_employee_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT,
                        task_type TEXT,
                        task_status TEXT,
                        execution_time_ms REAL,
                        accuracy REAL,
                        error_message TEXT,
                        reported_at TEXT,
                        created_at TEXT
                    )
                ''')

                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sr_type ON system_reports(report_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sr_module ON system_reports(module)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sr_severity ON system_reports(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_pur_page ON page_usage_reports(page_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_acr_endpoint ON api_call_reports(endpoint)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_spr_metric ON system_performance_reports(metric_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_aer_emp ON ai_employee_reports(employee_id)")

                conn.commit()
        except Exception as e:
            logger.error(f"[SystemReportService] 初始化数据库失败: {e}")

    def submit_report(self, report_type: str, module: str, severity: str = 'info',
                      title: str = '', content: str = '', metadata: Dict = None,
                      reported_by: str = 'system') -> Dict[str, Any]:
        """提交上报记录"""
        import uuid as _uuid
        report_id = f"rpt_{_uuid.uuid4().hex[:16]}"
        now = datetime.now().isoformat()

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO system_reports
                    (report_id, report_type, module, severity, title, content,
                     metadata, reported_by, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                ''', (
                    report_id, report_type, module, severity, title, content,
                    json.dumps(metadata or {}, ensure_ascii=False), reported_by, now
                ))
                conn.commit()
            return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f"[SystemReportService] 提交上报失败: {e}")
            return {'success': False, 'error': str(e)}

    def report_page_usage(self, page_name: str, page_category: str = '',
                          user_id: str = '', session_id: str = '',
                          duration: int = 0, actions: int = 0,
                          features: List[str] = None, errors: int = 0) -> bool:
        """上报页面使用数据"""
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO page_usage_reports
                    (page_name, page_category, user_id, session_id,
                     visit_duration, actions_count, features_used, errors_count,
                     visited_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    page_name, page_category, user_id, session_id,
                    duration, actions,
                    json.dumps(features or [], ensure_ascii=False), errors,
                    now, now
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SystemReportService] 上报页面使用失败: {e}")
            return False

    def report_api_call(self, endpoint: str, method: str = 'GET',
                        status_code: int = 200, response_time: float = 0,
                        user_id: str = '', request_data: str = '',
                        error_message: str = '') -> bool:
        """上报API调用数据"""
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO api_call_reports
                    (endpoint, method, status_code, response_time_ms,
                     user_id, request_data, error_message, called_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    endpoint, method, status_code, response_time,
                    user_id, request_data, error_message, now, now
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SystemReportService] 上报API调用失败: {e}")
            return False

    def report_performance(self, metric_name: str, value: float,
                           unit: str = '', category: str = 'system',
                           warn_threshold: float = None,
                           critical_threshold: float = None) -> bool:
        """上报性能指标"""
        now = datetime.now().isoformat()
        status = 'normal'
        if critical_threshold and value >= critical_threshold:
            status = 'critical'
        elif warn_threshold and value >= warn_threshold:
            status = 'warning'

        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO system_performance_reports
                    (metric_name, metric_value, metric_unit, category,
                     threshold_warning, threshold_critical, status, recorded_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric_name, value, unit, category,
                    warn_threshold, critical_threshold, status, now, now
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SystemReportService] 上报性能指标失败: {e}")
            return False

    def report_ai_employee_status(self, employee_id: str, employee_name: str = '',
                                  task_type: str = '', task_status: str = '',
                                  execution_time: float = 0, accuracy: float = 0,
                                  error_message: str = '') -> bool:
        """上报AI员工状态"""
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT INTO ai_employee_reports
                    (employee_id, employee_name, task_type, task_status,
                     execution_time_ms, accuracy, error_message, reported_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id, employee_name, task_type, task_status,
                    execution_time, accuracy, error_message, now, now
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SystemReportService] 上报AI员工状态失败: {e}")
            return False

    def get_reports(self, report_type: str = '', module: str = '',
                    severity: str = '', limit: int = 50) -> List[Dict]:
        """查询上报记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM system_reports WHERE 1=1'
                params = []
                if report_type:
                    query += ' AND report_type = ?'
                    params.append(report_type)
                if module:
                    query += ' AND module = ?'
                    params.append(module)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item['metadata'] = json.loads(item.get('metadata') or '{}')
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"[SystemReportService] 查询上报失败: {e}")
            return []

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取上报仪表板统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 总上报数
                cursor.execute('SELECT COUNT(*) as cnt FROM system_reports')
                total_reports = cursor.fetchone()['cnt']

                # 按严重级别统计
                cursor.execute('''
                    SELECT severity, COUNT(*) as cnt
                    FROM system_reports GROUP BY severity
                ''')
                by_severity = {row['severity']: row['cnt'] for row in cursor.fetchall()}

                # 按模块统计
                cursor.execute('''
                    SELECT module, COUNT(*) as cnt
                    FROM system_reports GROUP BY module ORDER BY cnt DESC LIMIT 10
                ''')
                by_module = {row['module']: row['cnt'] for row in cursor.fetchall()}

                # 页面使用统计
                cursor.execute('SELECT COUNT(*) as cnt FROM page_usage_reports')
                total_page_visits = cursor.fetchone()['cnt']
                cursor.execute('''
                    SELECT page_name, COUNT(*) as cnt, AVG(visit_duration) as avg_dur
                    FROM page_usage_reports GROUP BY page_name ORDER BY cnt DESC LIMIT 10
                ''')
                top_pages = [dict(row) for row in cursor.fetchall()]

                # API调用统计
                cursor.execute('SELECT COUNT(*) as cnt FROM api_call_reports')
                total_api_calls = cursor.fetchone()['cnt']
                cursor.execute('''
                    SELECT endpoint, COUNT(*) as cnt, AVG(response_time_ms) as avg_time
                    FROM api_call_reports GROUP BY endpoint ORDER BY cnt DESC LIMIT 10
                ''')
                top_apis = [dict(row) for row in cursor.fetchall()]

                # 性能指标
                cursor.execute('SELECT COUNT(*) as cnt FROM system_performance_reports')
                total_metrics = cursor.fetchone()['cnt']
                cursor.execute("SELECT COUNT(*) as cnt FROM system_performance_reports WHERE status = 'critical'")
                critical_metrics = cursor.fetchone()['cnt']
                cursor.execute("SELECT COUNT(*) as cnt FROM system_performance_reports WHERE status = 'warning'")
                warning_metrics = cursor.fetchone()['cnt']

                # AI员工上报
                cursor.execute('SELECT COUNT(*) as cnt FROM ai_employee_reports')
                total_ai_reports = cursor.fetchone()['cnt']

                # 未确认告警
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM system_reports
                    WHERE status = 'new' AND severity IN ('critical', 'error', 'warning')
                """)
                unacknowledged = cursor.fetchone()['cnt']

            return {
                'total_reports': total_reports,
                'by_severity': by_severity,
                'by_module': by_module,
                'page_usage': {
                    'total_visits': total_page_visits,
                    'top_pages': top_pages
                },
                'api_calls': {
                    'total_calls': total_api_calls,
                    'top_apis': top_apis
                },
                'performance': {
                    'total_metrics': total_metrics,
                    'critical': critical_metrics,
                    'warning': warning_metrics,
                    'normal': total_metrics - critical_metrics - warning_metrics
                },
                'ai_employee_reports': total_ai_reports,
                'unacknowledged_alerts': unacknowledged,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[SystemReportService] 获取仪表板失败: {e}")
            return {'error': str(e)}

    def acknowledge_report(self, report_id: str, acknowledged_by: str = 'admin') -> bool:
        """确认上报记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    UPDATE system_reports
                    SET status = 'acknowledged', acknowledged_at = ?, acknowledged_by = ?
                    WHERE report_id = ?
                ''', (datetime.now().isoformat(), acknowledged_by, report_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SystemReportService] 确认上报失败: {e}")
            return False

    def get_page_feature_coverage(self) -> Dict[str, Any]:
        """获取页面功能覆盖率分析"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 统计每个页面的使用情况
                cursor.execute('''
                    SELECT page_name, page_category,
                           COUNT(*) as visits,
                           AVG(visit_duration) as avg_duration,
                           AVG(actions_count) as avg_actions,
                           SUM(errors_count) as total_errors
                    FROM page_usage_reports
                    GROUP BY page_name
                    ORDER BY visits DESC
                ''')
                page_stats = [dict(row) for row in cursor.fetchall()]

                # 扫描 templates 目录获取全部页面
                templates_dir = os.path.join(_PROJECT_ROOT, 'templates')
                all_pages = []
                if os.path.isdir(templates_dir):
                    for root, dirs, files in os.walk(templates_dir):
                        for f in files:
                            if f.endswith('.html'):
                                rel_path = os.path.relpath(os.path.join(root, f), templates_dir)
                                all_pages.append(rel_path)

                # 计算覆盖率
                used_pages = set(p['page_name'] for p in page_stats)
                all_page_set = set(all_pages)
                covered = used_pages & all_page_set
                uncovered = all_page_set - used_pages

                return {
                    'total_pages': len(all_page_set),
                    'used_pages': len(covered),
                    'unused_pages': len(uncovered),
                    'coverage_rate': round(len(covered) / max(len(all_page_set), 1) * 100, 2),
                    'page_stats': page_stats,
                    'uncovered_pages': sorted(list(uncovered))[:20]
                }
        except Exception as e:
            logger.error(f"[SystemReportService] 获取页面覆盖率失败: {e}")
            return {'error': str(e)}


system_report_service = SystemReportService()
