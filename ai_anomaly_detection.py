#!/usr/bin/env python3
"""
MTSCOS AI 异常检测服务 (v14.5.0)
==================================
基于统计学和规则方法的异常检测引擎，支持时序数据、点异常、模式异常检测。

核心能力：
1. 点异常 - Z-Score / IQR / 3-Sigma
2. 时序异常 - 移动平均 / EWMA / 差分
3. 模式异常 - 频率变化 / 周期性异常
4. 多维异常 - 基线偏离 + 加权评分
5. 行为异常 - 用户行为基线对比
6. 检测器管理 - 多检测器配置和动态加载
7. 告警阈值 - 动态阈值和静态阈值
"""
import os
import json
import math
import sqlite3
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_anomaly.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIAnomaly')


# ========== 统计工具 ==========

def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _percentile(values: List[float], p: float) -> float:
    """计算百分位数"""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < len(s):
        return s[f] + (s[f + 1] - s[f]) * c
    return s[f]


def _ewma(values: List[float], alpha: float = 0.3) -> List[float]:
    """指数加权移动平均"""
    if not values:
        return []
    result = [values[0]]
    for i in range(1, len(values)):
        result.append(alpha * values[i] + (1 - alpha) * result[i - 1])
    return result


# ========== 检测算法 ==========

def detect_zscore(values: List[float], threshold: float = 3.0) -> List[Dict]:
    """Z-Score 检测：偏离均值 threshold 个标准差视为异常"""
    if len(values) < 3:
        return []
    m = _mean(values)
    s = _std(values)
    if s == 0:
        return []
    anomalies = []
    for i, v in enumerate(values):
        z = abs(v - m) / s
        if z > threshold:
            anomalies.append({
                'index': i,
                'value': v,
                'z_score': round(z, 4),
                'expected': round(m, 4),
                'deviation': round(abs(v - m), 4),
                'method': 'zscore'
            })
    return anomalies


def detect_iqr(values: List[float], multiplier: float = 1.5) -> List[Dict]:
    """IQR (四分位距) 检测"""
    if len(values) < 4:
        return []
    q1 = _percentile(values, 25)
    q3 = _percentile(values, 75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    anomalies = []
    for i, v in enumerate(values):
        if v < lower or v > upper:
            anomalies.append({
                'index': i,
                'value': v,
                'expected_range': [round(lower, 4), round(upper, 4)],
                'is_lower': v < lower,
                'method': 'iqr'
            })
    return anomalies


def detect_3sigma(values: List[float]) -> List[Dict]:
    """3-Sigma 检测"""
    return detect_zscore(values, threshold=3.0)


def detect_moving_average(values: List[float], window: int = 5,
                          threshold: float = 2.0) -> List[Dict]:
    """移动平均异常检测"""
    if len(values) < window + 1:
        return []
    anomalies = []
    for i in range(window, len(values)):
        window_vals = values[i - window:i]
        m = _mean(window_vals)
        s = _std(window_vals)
        if s == 0:
            continue
        z = abs(values[i] - m) / s
        if z > threshold:
            anomalies.append({
                'index': i,
                'value': values[i],
                'expected': round(m, 4),
                'z_score': round(z, 4),
                'window': window,
                'method': 'moving_average'
            })
    return anomalies


def detect_ewma_anomaly(values: List[float], alpha: float = 0.3,
                       threshold: float = 3.0) -> List[Dict]:
    """EWMA 异常检测"""
    if len(values) < 3:
        return []
    ewma_vals = _ewma(values, alpha)
    residuals = [values[i] - ewma_vals[i] for i in range(len(values))]
    m = _mean(residuals)
    s = _std(residuals)
    if s == 0:
        return []
    anomalies = []
    for i, r in enumerate(residuals):
        z = abs(r - m) / s
        if z > threshold:
            anomalies.append({
                'index': i,
                'value': values[i],
                'ewma': round(ewma_vals[i], 4),
                'residual': round(r, 4),
                'z_score': round(z, 4),
                'method': 'ewma'
            })
    return anomalies


def detect_diff_anomaly(values: List[float], threshold: float = 3.0) -> List[Dict]:
    """差分异常检测（检测突变）"""
    if len(values) < 3:
        return []
    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]
    m = _mean(diffs)
    s = _std(diffs)
    if s == 0:
        return []
    anomalies = []
    for i, d in enumerate(diffs):
        z = abs(d - m) / s
        if z > threshold:
            anomalies.append({
                'index': i + 1,
                'value': values[i + 1],
                'diff': round(d, 4),
                'expected_diff': round(m, 4),
                'z_score': round(z, 4),
                'method': 'diff'
            })
    return anomalies


def detect_frequency_anomaly(timestamps: List[str], expected_interval_sec: float = 60,
                            tolerance: float = 0.5) -> List[Dict]:
    """频率异常检测"""
    if len(timestamps) < 3:
        return []
    # 解析时间戳
    parsed = []
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            parsed.append(dt)
        except (ValueError, TypeError):
            continue

    parsed.sort()
    intervals = [(parsed[i] - parsed[i - 1]).total_seconds() for i in range(1, len(parsed))]
    if not intervals:
        return []

    m = _mean(intervals)
    s = _std(intervals)

    anomalies = []
    lower_bound = expected_interval_sec * (1 - tolerance)
    upper_bound = expected_interval_sec * (1 + tolerance)

    for i, interval in enumerate(intervals):
        if interval < lower_bound or interval > upper_bound:
            anomalies.append({
                'index': i + 1,
                'interval': round(interval, 2),
                'expected_interval': expected_interval_sec,
                'is_too_frequent': interval < lower_bound,
                'method': 'frequency'
            })
    return anomalies


# ========== 检测器注册 ==========

DETECTORS: Dict[str, Callable] = {
    'zscore': detect_zscore,
    'iqr': detect_iqr,
    '3sigma': detect_3sigma,
    'moving_average': detect_moving_average,
    'ewma': detect_ewma_anomaly,
    'diff': detect_diff_anomaly,
    'frequency': detect_frequency_anomaly,
}


# ========== 默认检测器配置 ==========

DEFAULT_DETECTOR_CONFIGS = [
    {
        'detector_id': 'DET-CPU-001',
        'name': 'CPU使用率异常检测',
        'metric': 'cpu_usage',
        'method': 'zscore',
        'params': {'threshold': 3.0},
        'enabled': True,
        'description': '基于Z-Score检测CPU使用率突变'
    },
    {
        'detector_id': 'DET-MEM-001',
        'name': '内存使用率异常检测',
        'metric': 'memory_usage',
        'method': 'iqr',
        'params': {'multiplier': 1.5},
        'enabled': True,
        'description': '基于IQR检测内存使用率异常'
    },
    {
        'detector_id': 'DET-RT-001',
        'name': '响应时间异常检测',
        'metric': 'response_time',
        'method': 'ewma',
        'params': {'alpha': 0.3, 'threshold': 2.5},
        'enabled': True,
        'description': '基于EWMA检测响应时间异常'
    },
    {
        'detector_id': 'DET-ERR-001',
        'name': '错误率异常检测',
        'metric': 'error_rate',
        'method': 'moving_average',
        'params': {'window': 5, 'threshold': 2.0},
        'enabled': True,
        'description': '基于移动平均检测错误率异常'
    },
    {
        'detector_id': 'DET-QPS-001',
        'name': '请求量异常检测',
        'metric': 'qps',
        'method': 'diff',
        'params': {'threshold': 3.0},
        'enabled': True,
        'description': '基于差分检测请求量突变'
    },
]


# ========== 异常检测服务 ==========

class AIAnomalyDetection:
    """AI 异常检测服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._register_defaults()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_anomaly_detectors (
                        detector_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        metric TEXT NOT NULL,
                        method TEXT NOT NULL,
                        params TEXT,
                        enabled INTEGER DEFAULT 1,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_anomaly_events (
                        event_id TEXT PRIMARY KEY,
                        detector_id TEXT,
                        metric TEXT,
                        method TEXT,
                        anomaly_data TEXT,
                        severity TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        resolved_at TEXT,
                        resolved_by TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_anomaly_baselines (
                        baseline_id TEXT PRIMARY KEY,
                        metric TEXT NOT NULL,
                        baseline_value REAL,
                        std_value REAL,
                        sample_count INTEGER,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_events_time ON ai_anomaly_events(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_events_status ON ai_anomaly_events(status)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化异常检测数据库失败: {e}")

    def _register_defaults(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for det in DEFAULT_DETECTOR_CONFIGS:
                    cursor.execute('SELECT detector_id FROM ai_anomaly_detectors WHERE detector_id = ?',
                                  (det['detector_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_anomaly_detectors
                            (detector_id, name, metric, method, params, enabled, description, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            det['detector_id'], det['name'], det['metric'], det['method'],
                            json.dumps(det['params'], ensure_ascii=False),
                            1 if det['enabled'] else 0, det['description'],
                            datetime.now().isoformat(), datetime.now().isoformat()
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"注册默认检测器失败: {e}")

    # ========== 检测器管理 ==========

    def add_detector(self, detector_id: str, name: str, metric: str, method: str,
                    params: Dict = None, description: str = '', enabled: bool = True) -> Dict:
        if method not in DETECTORS:
            return {'success': False, 'error': f'不支持的检测方法: {method}'}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_anomaly_detectors
                    (detector_id, name, metric, method, params, enabled, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    detector_id, name, metric, method,
                    json.dumps(params or {}, ensure_ascii=False),
                    1 if enabled else 0, description,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            return {'success': True, 'detector_id': detector_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_detectors(self, enabled_only: bool = False) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = 'SELECT detector_id, name, metric, method, params, enabled, description FROM ai_anomaly_detectors'
                if enabled_only:
                    sql += ' WHERE enabled = 1'
                sql += ' ORDER BY detector_id'
                cursor.execute(sql)
                return [
                    {
                        'detector_id': r[0], 'name': r[1], 'metric': r[2],
                        'method': r[3], 'params': json.loads(r[4]) if r[4] else {},
                        'enabled': bool(r[5]), 'description': r[6]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    # ========== 检测执行 ==========

    def detect(self, values: List[float], method: str = 'zscore',
              params: Dict = None) -> Dict:
        """执行单次异常检测"""
        detector_fn = DETECTORS.get(method)
        if not detector_fn:
            return {'success': False, 'error': f'不支持的检测方法: {method}'}

        try:
            anomalies = detector_fn(values, **(params or {}))
            return {
                'success': True,
                'method': method,
                'total_points': len(values),
                'anomaly_count': len(anomalies),
                'anomalies': anomalies,
                'anomaly_rate': round(len(anomalies) / len(values) * 100, 2) if values else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def detect_with_detector(self, detector_id: str, values: List[float]) -> Dict:
        """使用已注册的检测器执行检测"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, metric, method, params FROM ai_anomaly_detectors WHERE detector_id = ? AND enabled = 1',
                              (detector_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '检测器不存在或未启用'}

                name, metric, method, params_str = row
                params = json.loads(params_str) if params_str else {}

                result = self.detect(values, method, params)
                if not result.get('success'):
                    return result

                # 记录异常事件
                if result['anomaly_count'] > 0:
                    severity = self._compute_severity(result['anomaly_rate'])
                    event_id = f"ANOM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
                    cursor.execute('''
                        INSERT INTO ai_anomaly_events
                        (event_id, detector_id, metric, method, anomaly_data, severity, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event_id, detector_id, metric, method,
                        json.dumps(result['anomalies'], ensure_ascii=False),
                        severity, 'open', datetime.now().isoformat()
                    ))
                    conn.commit()
                    result['event_id'] = event_id
                    result['severity'] = severity

                result['detector_id'] = detector_id
                result['detector_name'] = name
                return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _compute_severity(self, anomaly_rate: float) -> str:
        """根据异常率计算严重程度"""
        if anomaly_rate >= 30:
            return 'critical'
        elif anomaly_rate >= 15:
            return 'high'
        elif anomaly_rate >= 5:
            return 'medium'
        else:
            return 'low'

    # ========== 多检测器批量执行 ==========

    def detect_all(self, metric_values: Dict[str, List[float]]) -> Dict:
        """对多个指标执行所有匹配的检测器"""
        detectors = self.list_detectors(enabled_only=True)
        results = []

        for det in detectors:
            values = metric_values.get(det['metric'])
            if not values:
                continue
            result = self.detect_with_detector(det['detector_id'], values)
            results.append({
                'detector_id': det['detector_id'],
                'detector_name': det['name'],
                'metric': det['metric'],
                'method': det['method'],
                'success': result.get('success', False),
                'anomaly_count': result.get('anomaly_count', 0),
                'severity': result.get('severity', 'none'),
                'event_id': result.get('event_id')
            })

        total_anomalies = sum(r['anomaly_count'] for r in results)
        return {
            'total_detectors': len(detectors),
            'executed': len(results),
            'total_anomalies': total_anomalies,
            'results': results
        }

    # ========== 基线管理 ==========

    def update_baseline(self, metric: str, values: List[float]) -> Dict:
        """更新指标基线"""
        if len(values) < 2:
            return {'success': False, 'error': '样本数不足'}
        baseline_id = f"BL-{metric}"
        m = _mean(values)
        s = _std(values)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_anomaly_baselines
                    (baseline_id, metric, baseline_value, std_value, sample_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (baseline_id, metric, round(m, 4), round(s, 4), len(values),
                      datetime.now().isoformat()))
                conn.commit()
            return {'success': True, 'metric': metric, 'baseline': round(m, 4), 'std': round(s, 4)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_against_baseline(self, metric: str, value: float, threshold: float = 3.0) -> Dict:
        """根据基线检测异常"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT baseline_value, std_value FROM ai_anomaly_baselines WHERE metric = ?',
                              (metric,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': f'无 {metric} 的基线数据'}
                baseline, std = row
                if std == 0:
                    return {'success': True, 'is_anomaly': False, 'metric': metric, 'value': value}
                z = abs(value - baseline) / std
                is_anomaly = z > threshold
                return {
                    'success': True,
                    'is_anomaly': is_anomaly,
                    'metric': metric,
                    'value': value,
                    'baseline': baseline,
                    'z_score': round(z, 4),
                    'threshold': threshold
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 事件管理 ==========

    def resolve_event(self, event_id: str, resolved_by: str = 'system') -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_anomaly_events
                    SET status = 'resolved', resolved_at = ?, resolved_by = ?
                    WHERE event_id = ? AND status = 'open'
                ''', (datetime.now().isoformat(), resolved_by, event_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return {'success': True, 'event_id': event_id}
                return {'success': False, 'error': '事件不存在或已解决'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_events(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('''
                        SELECT event_id, detector_id, metric, method, anomaly_data, severity, status, created_at
                        FROM ai_anomaly_events
                        WHERE status = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (status, limit))
                else:
                    cursor.execute('''
                        SELECT event_id, detector_id, metric, method, anomaly_data, severity, status, created_at
                        FROM ai_anomaly_events
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {
                        'event_id': r[0], 'detector_id': r[1], 'metric': r[2], 'method': r[3],
                        'anomaly_data': json.loads(r[4]) if r[4] else [],
                        'severity': r[5], 'status': r[6], 'created_at': r[7]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_anomaly_detectors')
                total_detectors = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_anomaly_detectors WHERE enabled = 1')
                enabled_detectors = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_anomaly_events')
                total_events = cursor.fetchone()[0]
                cursor.execute("SELECT status, COUNT(*) FROM ai_anomaly_events GROUP BY status")
                status_dist = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute("SELECT severity, COUNT(*) FROM ai_anomaly_events GROUP BY severity")
                severity_dist = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'total_detectors': total_detectors,
                    'enabled_detectors': enabled_detectors,
                    'total_events': total_events,
                    'status_distribution': status_dist,
                    'severity_distribution': severity_dist
                }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    detector = AIAnomalyDetection()
    print(f"检测器数量: {len(detector.list_detectors())}")
    print(f"统计: {detector.get_statistics()}")

    # 生成测试数据（含异常点）
    normal_data = [50 + random.uniform(-5, 5) for _ in range(50)]
    test_data = normal_data + [100, 5, 90] + normal_data[-5:]

    print("\nZ-Score 检测:")
    result = detector.detect(test_data, method='zscore', params={'threshold': 2.5})
    print(f"异常点数: {result.get('anomaly_count')}, 异常率: {result.get('anomaly_rate')}%")

    print("\nIQR 检测:")
    result = detector.detect(test_data, method='iqr', params={'multiplier': 1.5})
    print(f"异常点数: {result.get('anomaly_count')}")

    print("\n移动平均检测:")
    result = detector.detect(test_data, method='moving_average', params={'window': 5, 'threshold': 2.0})
    print(f"异常点数: {result.get('anomaly_count')}")

    # 使用注册的检测器
    print("\n使用注册检测器 (CPU):")
    result = detector.detect_with_detector('DET-CPU-001', test_data)
    print(f"成功: {result.get('success')}, 异常数: {result.get('anomaly_count')}, 严重度: {result.get('severity')}")

    # 多检测器批量执行
    print("\n批量执行所有检测器:")
    batch_result = detector.detect_all({
        'cpu_usage': test_data,
        'memory_usage': normal_data + [95, 2],
        'response_time': [100, 110, 105, 95, 5000, 100],
        'error_rate': [0.01, 0.02, 0.01, 0.5, 0.02],
        'qps': [100, 105, 95, 100, 800, 100]
    })
    print(f"总异常数: {batch_result['total_anomalies']}")
    for r in batch_result['results']:
        print(f"  - {r['detector_name']}: {r['anomaly_count']}个异常 (严重度: {r['severity']})")

    # 基线检测
    print("\n基线检测:")
    detector.update_baseline('cpu_usage', normal_data)
    baseline_result = detector.check_against_baseline('cpu_usage', 95)
    print(f"是否异常: {baseline_result.get('is_anomaly')}, Z-Score: {baseline_result.get('z_score')}")
