#!/usr/bin/env python3
"""
MTSCOS AI 智能监控服务 (v14.6.0)
==================================
AI 系统自身的智能监控和健康度评估服务。

核心能力：
1. 健康度评分 - 综合评估 AI 系统健康度（0-100）
2. 服务监控 - 监控 AI 服务运行状态和性能
3. 资源监控 - CPU/内存/磁盘/数据库
4. 指标采集 - 时序指标采集和存储
5. 告警生成 - 智能告警规则和通知
6. 趋势分析 - 历史趋势和预测
7. 自检报告 - 定期生成自检报告
8. 仪表盘 - 监控数据可视化聚合
"""
import os
import json
import time
import psutil
import sqlite3
import random
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_monitor.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AISmartMonitor')


# ========== 监控的服务清单 ==========

MONITORED_SERVICES = [
    {'service_id': 'ai-model-manager', 'name': 'AI 模型管理服务', 'category': 'ai_core', 'critical': True},
    {'service_id': 'ai-conversation', 'name': 'AI 对话服务', 'category': 'ai_core', 'critical': True},
    {'service_id': 'ai-knowledge-base', 'name': 'AI 知识库服务', 'category': 'ai_core', 'critical': True},
    {'service_id': 'ai-inference-pipeline', 'name': 'AI 推理流水线', 'category': 'ai_core', 'critical': True},
    {'service_id': 'ai-agent-service', 'name': 'AI Agent 服务', 'category': 'ai_enhance', 'critical': True},
    {'service_id': 'ai-workflow-orchestrator', 'name': 'AI 工作流编排', 'category': 'ai_advanced', 'critical': True},
    {'service_id': 'ai-decision-engine', 'name': 'AI 决策引擎', 'category': 'ai_advanced', 'critical': True},
    {'service_id': 'ai-anomaly-detection', 'name': 'AI 异常检测', 'category': 'ai_advanced', 'critical': False},
    {'service_id': 'ai-vector-store', 'name': 'AI 向量数据库', 'category': 'ai_advanced', 'critical': True},
    {'service_id': 'auto-repair-engine', 'name': '自动修复引擎', 'category': 'system', 'critical': True},
    {'service_id': 'brain-feeding-engine', 'name': '脑库投喂引擎', 'category': 'system', 'critical': True},
    {'service_id': 'flask-app', 'name': 'Flask 主应用', 'category': 'system', 'critical': True},
]


# ========== 告警规则 ==========

ALERT_RULES = [
    {
        'rule_id': 'MON-001',
        'name': 'CPU 使用率过高',
        'metric': 'cpu_usage',
        'condition': '>',
        'threshold': 80,
        'severity': 'high',
        'message': 'CPU 使用率 {value}% 超过阈值 {threshold}%'
    },
    {
        'rule_id': 'MON-002',
        'name': '内存使用率过高',
        'metric': 'memory_usage',
        'condition': '>',
        'threshold': 85,
        'severity': 'high',
        'message': '内存使用率 {value}% 超过阈值 {threshold}%'
    },
    {
        'rule_id': 'MON-003',
        'name': '磁盘空间不足',
        'metric': 'disk_usage',
        'condition': '>',
        'threshold': 85,
        'severity': 'critical',
        'message': '磁盘使用率 {value}% 超过阈值 {threshold}%'
    },
    {
        'rule_id': 'MON-004',
        'name': '服务响应时间过长',
        'metric': 'response_time',
        'condition': '>',
        'threshold': 2000,
        'severity': 'medium',
        'message': '响应时间 {value}ms 超过阈值 {threshold}ms'
    },
    {
        'rule_id': 'MON-005',
        'name': '错误率过高',
        'metric': 'error_rate',
        'condition': '>',
        'threshold': 5,
        'severity': 'high',
        'message': '错误率 {value}% 超过阈值 {threshold}%'
    },
    {
        'rule_id': 'MON-006',
        'name': '服务离线',
        'metric': 'service_status',
        'condition': '==',
        'threshold': 'offline',
        'severity': 'critical',
        'message': '服务 {service_name} 离线'
    },
    {
        'rule_id': 'MON-007',
        'name': '数据库连接异常',
        'metric': 'db_connections',
        'condition': '>',
        'threshold': 50,
        'severity': 'medium',
        'message': '数据库连接数 {value} 超过阈值 {threshold}'
    },
]


# ========== 智能监控服务 ==========

class AISmartMonitor:
    """AI 智能监控服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()
        self._lock = threading.RLock()
        self._metrics_buffer: List[Dict] = []
        self._buffer_lock = threading.Lock()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_monitor_services (
                        service_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT,
                        critical INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'unknown',
                        last_check TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_monitor_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        metric_unit TEXT,
                        tags TEXT,
                        timestamp TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_monitor_alerts (
                        alert_id TEXT PRIMARY KEY,
                        rule_id TEXT,
                        service_id TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        severity TEXT,
                        message TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        resolved_at TEXT,
                        resolved_by TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_monitor_health_logs (
                        log_id TEXT PRIMARY KEY,
                        health_score REAL,
                        status TEXT,
                        details TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_service ON ai_monitor_metrics(service_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_time ON ai_monitor_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON ai_monitor_alerts(status)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化监控数据库失败: {e}")

    def _register_defaults(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for svc in MONITORED_SERVICES:
                    cursor.execute('SELECT service_id FROM ai_monitor_services WHERE service_id = ?',
                                 (svc['service_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_monitor_services
                            (service_id, name, category, critical, status, last_check, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            svc['service_id'], svc['name'], svc['category'],
                            1 if svc['critical'] else 0, 'unknown',
                            datetime.now().isoformat(), datetime.now().isoformat()
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"注册默认服务失败: {e}")

    # ========== 指标采集 ==========

    def collect_system_metrics(self) -> Dict:
        """采集系统资源指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metrics = {
                'cpu_usage': {'value': cpu_percent, 'unit': '%'},
                'memory_usage': {'value': memory.percent, 'unit': '%'},
                'memory_used': {'value': round(memory.used / 1024 / 1024, 2), 'unit': 'MB'},
                'memory_total': {'value': round(memory.total / 1024 / 1024, 2), 'unit': 'MB'},
                'disk_usage': {'value': round(disk.percent, 2), 'unit': '%'},
                'disk_used': {'value': round(disk.used / 1024 / 1024 / 1024, 2), 'unit': 'GB'},
                'disk_total': {'value': round(disk.total / 1024 / 1024 / 1024, 2), 'unit': 'GB'},
            }

            # 进程数
            try:
                metrics['process_count'] = {'value': len(psutil.pids()), 'unit': ''}
            except Exception:
                pass

            # 数据库文件大小
            try:
                if os.path.exists(self.db_path):
                    db_size = os.path.getsize(self.db_path) / 1024 / 1024
                    metrics['db_size_mb'] = {'value': round(db_size, 2), 'unit': 'MB'}
            except Exception:
                pass

            # 持久化
            for name, data in metrics.items():
                self._record_metric('system', name, data['value'], data['unit'])

            return metrics
        except Exception as e:
            logger.error(f"采集系统指标失败: {e}")
            return {}

    def record_service_metric(self, service_id: str, metric_name: str, value: float,
                             unit: str = '', tags: Optional[Dict] = None):
        """记录服务指标"""
        self._record_metric(service_id, metric_name, value, unit, tags)

    def _record_metric(self, service_id: str, metric_name: str, value: float,
                      unit: str = '', tags: Optional[Dict] = None):
        # 写入缓冲区
        with self._buffer_lock:
            self._metrics_buffer.append({
                'service_id': service_id,
                'metric_name': metric_name,
                'metric_value': value,
                'metric_unit': unit,
                'tags': json.dumps(tags or {}, ensure_ascii=False),
                'timestamp': datetime.now().isoformat()
            })
            # 缓冲区满时批量写入
            if len(self._metrics_buffer) >= 50:
                self._flush_metrics()

    def _flush_metrics(self):
        """批量写入指标"""
        if not self._metrics_buffer:
            return
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for m in self._metrics_buffer:
                    cursor.execute('''
                        INSERT INTO ai_monitor_metrics
                        (service_id, metric_name, metric_value, metric_unit, tags, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (m['service_id'], m['metric_name'], m['metric_value'],
                          m['metric_unit'], m['tags'], m['timestamp']))
                conn.commit()
            self._metrics_buffer.clear()
        except Exception as e:
            logger.error(f"批量写入指标失败: {e}")

    # ========== 服务状态检查 ==========

    def check_service(self, service_id: str) -> Dict:
        """检查单个服务状态"""
        try:
            # 简单实现：检查服务相关表的最近活动
            status = 'online'
            details = {}

            # 根据服务ID推断关联表
            table_map = {
                'ai-model-manager': 'ai_engine_config',
                'ai-conversation': 'ai_employees',
                'ai-knowledge-base': 'ai_brain_knowledge',
                'auto-repair-engine': 'auto_repair_executions',
                'brain-feeding-engine': 'brain_feeding_stats',
                'flask-app': 'users',
            }

            related_table = table_map.get(service_id)
            if related_table:
                try:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'SELECT COUNT(*) FROM {related_table}')
                        count = cursor.fetchone()[0]
                        details['record_count'] = count
                        if count == 0:
                            status = 'idle'
                except Exception:
                    status = 'unknown'

            # 更新服务状态
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_monitor_services
                    SET status = ?, last_check = ?
                    WHERE service_id = ?
                ''', (status, datetime.now().isoformat(), service_id))
                conn.commit()

            return {'service_id': service_id, 'status': status, 'details': details}
        except Exception as e:
            return {'service_id': service_id, 'status': 'error', 'error': str(e)}

    def check_all_services(self) -> Dict:
        """检查所有服务"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT service_id FROM ai_monitor_services')
                service_ids = [r[0] for r in cursor.fetchall()]

            results = []
            for sid in service_ids:
                results.append(self.check_service(sid))

            online = sum(1 for r in results if r['status'] == 'online')
            idle = sum(1 for r in results if r['status'] == 'idle')
            offline = sum(1 for r in results if r['status'] in ('offline', 'error', 'unknown'))

            return {
                'total': len(results),
                'online': online,
                'idle': idle,
                'offline': offline,
                'results': results
            }
        except Exception as e:
            return {'error': str(e)}

    # ========== 告警检测 ==========

    def evaluate_alerts(self) -> Dict:
        """评估告警规则"""
        # 先采集系统指标
        system_metrics = self.collect_system_metrics()
        # 刷新指标到数据库
        self._flush_metrics()

        triggered_alerts = []

        for rule in ALERT_RULES:
            metric_value = None
            service_id = 'system'

            if rule['metric'] in system_metrics:
                metric_value = system_metrics[rule['metric']]['value']
            elif rule['metric'] == 'service_status':
                # 检查服务状态
                continue
            else:
                # 从最近指标查询
                try:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT metric_value FROM ai_monitor_metrics
                            WHERE metric_name = ?
                            ORDER BY timestamp DESC LIMIT 1
                        ''', (rule['metric'],))
                        row = cursor.fetchone()
                        if row:
                            metric_value = row[0]
                except Exception:
                    pass

            if metric_value is None:
                continue

            # 评估条件
            triggered = False
            try:
                if rule['condition'] == '>':
                    triggered = float(metric_value) > float(rule['threshold'])
                elif rule['condition'] == '<':
                    triggered = float(metric_value) < float(rule['threshold'])
                elif rule['condition'] == '>=':
                    triggered = float(metric_value) >= float(rule['threshold'])
                elif rule['condition'] == '<=':
                    triggered = float(metric_value) <= float(rule['threshold'])
                elif rule['condition'] == '==':
                    triggered = str(metric_value) == str(rule['threshold'])
                elif rule['condition'] == '!=':
                    triggered = str(metric_value) != str(rule['threshold'])
            except (ValueError, TypeError):
                continue

            if triggered:
                alert_id = f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
                message = rule['message'].format(
                    value=metric_value,
                    threshold=rule['threshold'],
                    service_name=service_id
                )

                try:
                    with self._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO ai_monitor_alerts
                            (alert_id, rule_id, service_id, metric_name, metric_value,
                             severity, message, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            alert_id, rule['rule_id'], service_id, rule['metric'],
                            metric_value, rule['severity'], message, 'open',
                            datetime.now().isoformat()
                        ))
                        conn.commit()
                except Exception as e:
                    logger.error(f"保存告警失败: {e}")

                triggered_alerts.append({
                    'alert_id': alert_id,
                    'rule_id': rule['rule_id'],
                    'severity': rule['severity'],
                    'message': message,
                    'metric_value': metric_value
                })

                logger.warning(f"触发告警: {rule['name']} - {message}")

        return {
            'total_alerts': len(triggered_alerts),
            'alerts': triggered_alerts,
            'system_metrics': system_metrics
        }

    # ========== 健康度评估 ==========

    def compute_health_score(self) -> Dict:
        """计算 AI 系统综合健康度"""
        # 1. 采集系统资源
        system_metrics = self.collect_system_metrics()

        # 2. 检查服务状态
        service_check = self.check_all_services()

        # 3. 检查活跃告警
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT severity, COUNT(*) FROM ai_monitor_alerts WHERE status = 'open' GROUP BY severity")
                alert_dist = {r[0]: r[1] for r in cursor.fetchall()}
        except Exception:
            alert_dist = {}

        # 4. 计算各项得分
        # 资源得分（40%）
        cpu_score = max(0, 100 - max(0, system_metrics.get('cpu_usage', {}).get('value', 0) - 50) * 2)
        mem_score = max(0, 100 - max(0, system_metrics.get('memory_usage', {}).get('value', 0) - 50) * 2)
        disk_score = max(0, 100 - max(0, system_metrics.get('disk_usage', {}).get('value', 0) - 50) * 2)
        resource_score = (cpu_score + mem_score + disk_score) / 3

        # 服务得分（40%）
        total_services = service_check.get('total', 1) or 1
        online_services = service_check.get('online', 0)
        service_score = (online_services / total_services) * 100

        # 告警得分（20%）
        alert_penalty = (alert_dist.get('critical', 0) * 25 +
                        alert_dist.get('high', 0) * 15 +
                        alert_dist.get('medium', 0) * 5 +
                        alert_dist.get('low', 0) * 1)
        alert_score = max(0, 100 - alert_penalty)

        # 综合得分
        health_score = resource_score * 0.4 + service_score * 0.4 + alert_score * 0.2

        # 状态判定
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 60:
            status = 'fair'
        elif health_score >= 40:
            status = 'poor'
        else:
            status = 'critical'

        details = {
            'resource_score': round(resource_score, 2),
            'service_score': round(service_score, 2),
            'alert_score': round(alert_score, 2),
            'cpu_score': round(cpu_score, 2),
            'memory_score': round(mem_score, 2),
            'disk_score': round(disk_score, 2),
            'system_metrics': system_metrics,
            'service_check': {
                'total': service_check.get('total', 0),
                'online': service_check.get('online', 0),
                'idle': service_check.get('idle', 0),
                'offline': service_check.get('offline', 0)
            },
            'alert_distribution': alert_dist
        }

        # 保存健康日志
        log_id = f"HLT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_monitor_health_logs
                    (log_id, health_score, status, details, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (log_id, round(health_score, 2), status,
                      json.dumps(details, ensure_ascii=False),
                      datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"保存健康日志失败: {e}")

        return {
            'health_score': round(health_score, 2),
            'status': status,
            'details': details
        }

    # ========== 查询 ==========

    def get_dashboard(self) -> Dict:
        """获取监控仪表盘数据"""
        health = self.compute_health_score()
        alerts = self.evaluate_alerts()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT service_id, name, category, status, last_check FROM ai_monitor_services')
                services = [
                    {
                        'service_id': r[0], 'name': r[1], 'category': r[2],
                        'status': r[3], 'last_check': r[4]
                    }
                    for r in cursor.fetchall()
                ]
                cursor.execute("SELECT COUNT(*) FROM ai_monitor_alerts WHERE status = 'open'")
                open_alerts = cursor.fetchone()[0]
                cursor.execute('''
                    SELECT severity, COUNT(*) FROM ai_monitor_alerts
                    WHERE status = 'open' GROUP BY severity
                ''')
                alert_summary = {r[0]: r[1] for r in cursor.fetchall()}
        except Exception as e:
            return {'error': str(e)}

        return {
            'health_score': health['health_score'],
            'status': health['status'],
            'health_details': health['details'],
            'services': services,
            'open_alerts': open_alerts,
            'alert_summary': alert_summary,
            'recent_alerts': alerts.get('alerts', []),
            'system_metrics': alerts.get('system_metrics', {}),
            'generated_at': datetime.now().isoformat()
        }

    def list_alerts(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('''
                        SELECT alert_id, rule_id, service_id, metric_name, metric_value,
                               severity, message, status, created_at
                        FROM ai_monitor_alerts WHERE status = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (status, limit))
                else:
                    cursor.execute('''
                        SELECT alert_id, rule_id, service_id, metric_name, metric_value,
                               severity, message, status, created_at
                        FROM ai_monitor_alerts
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {
                        'alert_id': r[0], 'rule_id': r[1], 'service_id': r[2],
                        'metric_name': r[3], 'metric_value': r[4], 'severity': r[5],
                        'message': r[6], 'status': r[7], 'created_at': r[8]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def resolve_alert(self, alert_id: str, resolved_by: str = 'system') -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_monitor_alerts
                    SET status = 'resolved', resolved_at = ?, resolved_by = ?
                    WHERE alert_id = ? AND status = 'open'
                ''', (datetime.now().isoformat(), resolved_by, alert_id))
                conn.commit()
                return {'success': cursor.rowcount > 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_health_history(self, limit: int = 24) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT log_id, health_score, status, created_at
                    FROM ai_monitor_health_logs
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                return [
                    {'log_id': r[0], 'health_score': r[1], 'status': r[2], 'created_at': r[3]}
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_monitor_services')
                total_services = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_monitor_metrics')
                total_metrics = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_monitor_alerts')
                total_alerts = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM ai_monitor_alerts WHERE status = 'open'")
                open_alerts = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(health_score) FROM ai_monitor_health_logs')
                avg_health = cursor.fetchone()[0] or 0
                return {
                    'total_services': total_services,
                    'total_metrics': total_metrics,
                    'total_alerts': total_alerts,
                    'open_alerts': open_alerts,
                    'avg_health_score': round(avg_health, 2)
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    monitor = AISmartMonitor()
    print(f"已注册服务数: {len(monitor.get_statistics().get('total_services', 0))}")
    print(f"统计: {monitor.get_statistics()}")

    print("\n采集系统指标:")
    metrics = monitor.collect_system_metrics()
    for k, v in metrics.items():
        print(f"  {k}: {v['value']} {v['unit']}")

    print("\n检查所有服务:")
    result = monitor.check_all_services()
    print(f"  在线: {result['online']}/{result['total']}")

    print("\n评估告警:")
    alerts = monitor.evaluate_alerts()
    print(f"  触发告警数: {alerts['total_alerts']}")
    for a in alerts['alerts']:
        print(f"  [{a['severity']}] {a['message']}")

    print("\n计算健康度:")
    health = monitor.compute_health_score()
    print(f"  健康度: {health['health_score']} ({health['status']})")
    print(f"  资源得分: {health['details']['resource_score']}")
    print(f"  服务得分: {health['details']['service_score']}")
    print(f"  告警得分: {health['details']['alert_score']}")

    print(f"\n最终统计: {monitor.get_statistics()}")
