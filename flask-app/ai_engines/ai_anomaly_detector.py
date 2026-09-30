# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强版AI异常检测器 - 引入机器学习能力和自动学习机制
"""

import logging
logger = logging.getLogger(__name__)
import os
import time
import sqlite3
from datetime import datetime
from collections import defaultdict, deque

class EnhancedAIAnomalyDetector:
    """增强版AI异常检测器,支持机器学习和自动学习"""

    def __init__(self, db_path='ai_anomaly.db', learning_rate=0.1):
        """初始化增强版AI异常检测器

        Args:
            db_path: 数据库路径
            learning_rate: 学习率
        """
        self.db_path = db_path
        self.learning_rate = learning_rate
        self._init_db()

        # 正常行为模式参数
        self.normal_patterns = {
            'failed_login_attempts': 3,
            'rapid_attempts_window': 60,
            'rapid_attempts_threshold': 5,
            'unusual_user_agent_score': 0.7,
            'anomaly_score_threshold': 0.8,
            'consecutive_failures_threshold': 3,
            'time_between_attempts': 5
        }

        # 最近尝试记录,用于实时检测
        self.recent_attempts = defaultdict(lambda: {
            'login_attempts': deque(maxlen=100),
            'total_failed': 0,
            'last_attempt': 0,
            'consecutive_failures': 0
        })

        # 学习模式开关
        self.learning_enabled = True

        # 初始化学习数据
        self._load_learning_data()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_ip TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_anomalous INTEGER NOT NULL,
            anomaly_score REAL NOT NULL,
            anomaly_details TEXT,
            user_agent TEXT,
            path TEXT,
            metadata TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_data (
            feature_name TEXT UNIQUE NOT NULL,
            value REAL NOT NULL,
            confidence REAL DEFAULT 0.5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_ip ON anomaly_logs(client_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_anomalous ON anomaly_logs(is_anomalous)')

            conn.commit()

    def _load_learning_data(self):
        """从数据库加载学习数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT feature_name, value, confidence FROM learning_data')
                for row in cursor.fetchall():
                    feature_name, value, confidence = row
                    if feature_name in self.normal_patterns:
                        self.normal_patterns[feature_name] = (
                            value * confidence + self.normal_patterns[feature_name] * (1 - confidence)
                        )
            except Exception as e:
                logger.error(f"Error loading learning data: {str(e)}")

    def _save_learning_data(self):
        """保存学习数据到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                for feature_name, value in self.normal_patterns.items():
                    cursor.execute('SELECT id FROM learning_data WHERE feature_name = ?', (feature_name,))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute('''
                            UPDATE learning_data
                            SET value = ?, confidence = MIN(confidence + 0.1, 0.95),
                            last_updated = CURRENT_TIMESTAMP
                            WHERE feature_name = ?
                            ''', (value, feature_name))
                    else:
                        cursor.execute('''
                            INSERT INTO learning_data (feature_name, value, confidence)
                            VALUES (?, ?, 0.5)
                            ''', (feature_name, value))
                conn.commit()
            except Exception as e:
                logger.error(f"Error saving learning data: {str(e)}")

    def _log_anomaly(self, client_ip, action, is_anomalous, anomaly_score, anomaly_details,
                    user_agent='', path='', metadata=None):
        """记录异常检测日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO anomaly_logs 
                (client_ip, action, is_anomalous, anomaly_score, anomaly_details, user_agent, path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (client_ip, action, 1 if is_anomalous else 0, anomaly_score,
                      anomaly_details, user_agent, path, str(metadata)))
                conn.commit()
            except Exception as e:
                logger.error(f"Error logging anomaly: {str(e)}")

    def _calculate_anomaly_score(self, client_ip, attempt_record):
        """计算异常分数

        Args:
            client_ip: 客户端IP
            attempt_record: 尝试记录

        Returns:
            tuple: (异常分数, 影响因子列表)
        """
        score = 0.0
        factors = []

        client_history = self.recent_attempts[client_ip]
        current_time = time.time()

        recent_attempts_count = len([a for a in client_history['login_attempts'] 
                                      if current_time - a['timestamp'] < self.normal_patterns['rapid_attempts_window']])

        if recent_attempts_count > self.normal_patterns['rapid_attempts_threshold']:
            rapid_factor = min(
                (recent_attempts_count / self.normal_patterns['rapid_attempts_threshold']) * 0.3,
                0.3
            )
            score += rapid_factor
            factors.append(f"快速连续尝试 ({recent_attempts_count}/{self.normal_patterns['rapid_attempts_threshold']})")

        if 'failed' in attempt_record.get('details', '').lower():
            failed_factor = min(
                (client_history['total_failed'] / self.normal_patterns['failed_login_attempts']) * 0.25,
                0.25
            )
            score += failed_factor
            factors.append(f"失败尝试 ({client_history['total_failed']}/{self.normal_patterns['failed_login_attempts']})")

        if client_history['consecutive_failures'] > self.normal_patterns['consecutive_failures_threshold']:
            consecutive_factor = min(
                (client_history['consecutive_failures'] / self.normal_patterns['consecutive_failures_threshold']) * 0.25,
                0.25
            )
            score += consecutive_factor
            factors.append(f"连续失败 ({client_history['consecutive_failures']}/{self.normal_patterns['consecutive_failures_threshold']})")

        if client_history['last_attempt'] > 0:
            time_between = current_time - client_history['last_attempt']
            if time_between < self.normal_patterns['time_between_attempts']:
                interval_factor = min(
                    (self.normal_patterns['time_between_attempts'] / max(time_between, 0.1)) * 0.1,
                    0.1
                )
                score += interval_factor
                factors.append(f"尝试间隔过短 ({time_between:.2f}秒)")

        user_agent = attempt_record.get('user_agent', '')
        if self._is_anomalous_user_agent(user_agent):
            score += 0.1
            factors.append("异常User-Agent")

        path = attempt_record.get('path', '')
        if self._is_anomalous_path(path):
            score += 0.1
            factors.append("异常访问路径")

        return min(score, 1.0), factors

    def _is_anomalous_user_agent(self, user_agent):
        """检测异常User-Agent"""
        if not user_agent or len(user_agent) < 10:
            return True

        anomalous_patterns = [
            'curl', 'wget', 'python-requests', 'httplib2', 'urllib',
            'scrapy', 'bot', 'spider', 'crawler', 'headless',
            'phantomjs', 'selenium', 'webdriver', 'libwww-perl',
            'java/', 'node-fetch', 'axios', 'postman', 'insomnia',
            'httpie', 'newman', 'go-http-client', 'okhttp',
            'apache-httpclient'
        ]

        user_agent_lower = user_agent.lower()
        for pattern in anomalous_patterns:
            if pattern in user_agent_lower:
                return True

        return False

    def _is_anomalous_path(self, path):
        """检测异常访问路径"""
        malicious_patterns = [
            '/etc/passwd', '/var/www/html', '/proc/self/environ',
            '..', '../', '.git', '.env', 'config.php',
            'wp-admin', 'admin.php', 'login.php', 'phpmyadmin',
            '/admin/', '/wp-', '/phpmyadmin/', '/webadmin/',
            '/cpanel/', '/whm/', '/ftp/', '/mail/',
            '/api/v1/auth', '/api/v2/login', '/auth/', '/login/',
            '/signin/', '/sign-up/', '/register/', '/oauth/',
            '/token/', '/jwt/', '/api/keys/', '/api/tokens/',
            '/debug/', '/test/', '/dev/', '/staging/', '/uat/',
            '/backup/', '/backups/', '/dump/', '/export/', '/import/',
            '/upload/', '/download/', '/file/', '/files/',
            '.sql', '.bak', '.tar', '.gz', '.zip', '.rar',
            '.log', '.txt', '.cfg', '.conf', '.ini', '.yml', '.yaml'
        ]

        path_lower = path.lower()
        for pattern in malicious_patterns:
            if pattern in path_lower:
                return True

        return False

    def detect_anomalous_behavior(self, client_ip, action, details=None, user_agent='', path=''):
        """检测多种类型的异常行为,支持机器学习和自动调整

        Args:
            client_ip: 客户端IP
            action: 行为类型
            details: 详细信息
            user_agent: User-Agent
            path: 访问路径

        Returns:
            tuple: (是否异常, 异常详情, 异常分数)
        """
        current_time = time.time()

        attempt_record = {
            'timestamp': current_time,
            'action': action,
            'details': details,
            'user_agent': user_agent,
            'path': path
        }

        client_history = self.recent_attempts[client_ip]
        client_history['login_attempts'].append(attempt_record)
        cutoff_time = current_time - self.normal_patterns['rapid_attempts_window']
        while client_history['login_attempts'] and client_history['login_attempts'][0]['timestamp'] < cutoff_time:
            client_history['login_attempts'].popleft()

        if details and 'failed' in details.lower():
            client_history['total_failed'] += 1
            client_history['consecutive_failures'] += 1
        else:
            client_history['consecutive_failures'] = 0

        client_history['last_attempt'] = current_time

        anomaly_score, factors = self._calculate_anomaly_score(client_ip, attempt_record)
        is_anomalous = anomaly_score >= self.normal_patterns['anomaly_score_threshold']

        if is_anomalous:
            anomaly_details = f"检测到异常行为 (分数: {anomaly_score:.2f}): {'; '.join(factors)}"
        else:
            anomaly_details = None

        self._log_anomaly(
            client_ip=client_ip,
            action=action,
            is_anomalous=is_anomalous,
            anomaly_score=anomaly_score,
            anomaly_details=anomaly_details,
            user_agent=user_agent,
            path=path,
            metadata={
                'client_history': {
                    'total_failed': client_history['total_failed'],
                    'consecutive_failures': client_history['consecutive_failures'],
                },
                'detection_factors': factors
            }
        )

        if self.learning_enabled:
            self._automatic_learning(client_ip, is_anomalous, anomaly_score, factors)

        return is_anomalous, anomaly_details, anomaly_score

    def _automatic_learning(self, client_ip, is_anomalous, anomaly_score, factors):
        """自动学习和调整检测参数

        Args:
            client_ip: 客户端IP
            is_anomalous: 是否异常
            anomaly_score: 异常分数
            factors: 影响因子列表
        """
        client_history = self.recent_attempts[client_ip]
        if len(client_history['login_attempts']) < 10:
            return

        for factor in factors:
            if '快速连续尝试' in factor:
                current_threshold = self.normal_patterns['rapid_attempts_threshold']
                if is_anomalous:
                    new_threshold = current_threshold * (1 - self.learning_rate * 0.5)
                else:
                    new_threshold = current_threshold * (1 + self.learning_rate * 0.2)
                self.normal_patterns['rapid_attempts_threshold'] = max(3, min(20, new_threshold))

            elif '失败尝试' in factor:
                current_threshold = self.normal_patterns['failed_login_attempts']
                if is_anomalous:
                    new_threshold = current_threshold * (1 - self.learning_rate * 0.5)
                else:
                    new_threshold = current_threshold * (1 + self.learning_rate * 0.2)
                self.normal_patterns['failed_login_attempts'] = max(2, min(10, new_threshold))

            elif '连续失败' in factor:
                current_threshold = self.normal_patterns['consecutive_failures_threshold']
                if is_anomalous:
                    new_threshold = current_threshold * (1 - self.learning_rate * 0.5)
                else:
                    new_threshold = current_threshold * (1 + self.learning_rate * 0.2)
                self.normal_patterns['consecutive_failures_threshold'] = max(2, min(8, new_threshold))

        if int(time.time()) % 300 == 0:
            self._save_learning_data()

    def get_anomaly_stats(self, time_window=3600):
        """获取异常检测统计信息

        Args:
            time_window: 时间窗口(秒)

        Returns:
            dict: 统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cutoff_time = datetime.utcfromtimestamp(time.time() - time_window)

                cursor.execute('SELECT COUNT(*) FROM anomaly_logs WHERE timestamp >= ?', (cutoff_time,))
                total_events = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM anomaly_logs WHERE is_anomalous = 1 AND timestamp >= ?', (cutoff_time,))
                anomalous_events = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT client_ip, COUNT(*) as count
                    FROM anomaly_logs
                    WHERE is_anomalous = 1 AND timestamp >= ?
                    GROUP BY client_ip
                    ORDER BY count DESC
                    LIMIT 10
                ''', (cutoff_time,))
                top_anomalous_ips = [{'ip': row[0], 'count': row[1]} for row in cursor.fetchall()]

                cursor.execute('''
                    SELECT action, COUNT(*) as count
                    FROM anomaly_logs
                    WHERE is_anomalous = 1 AND timestamp >= ?
                    GROUP BY action
                    ORDER BY count DESC
                ''', (cutoff_time,))
                anomaly_by_action = [{'action': row[0], 'count': row[1]} for row in cursor.fetchall()]

                return {
                    'total_events': total_events,
                    'anomalous_events': anomalous_events,
                    'anomaly_rate': round(anomalous_events / total_events * 100, 2) if total_events > 0 else 0,
                    'top_anomalous_ips': top_anomalous_ips,
                    'anomaly_by_action': anomaly_by_action,
                    'time_window': time_window,
                    'current_time': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting anomaly stats: {str(e)}")
                return {
                    'total_events': 0,
                    'anomalous_events': 0,
                    'anomaly_rate': 0,
                    'top_anomalous_ips': [],
                    'anomaly_by_action': [],
                    'time_window': time_window,
                    'current_time': datetime.now().isoformat()
                }

    def export_learning_data(self):
        """导出学习数据

        Returns:
            dict: 学习数据
        """
        return {
            'learning_rate': self.learning_rate,
            'learning_enabled': self.learning_enabled,
            'normal_patterns': self.normal_patterns,
            'export_time': datetime.now().isoformat()
        }

global_ai_detector = None

def get_ai_detector():
    """获取全局AI异常检测器实例"""
    global global_ai_detector
    if global_ai_detector is None:
        global_ai_detector = EnhancedAIAnomalyDetector()
    return global_ai_detector

if __name__ == '__main__':
    ai_detector = EnhancedAIAnomalyDetector()

    test_ips = ['192.168.1.1', '10.0.0.1']
    for i in range(10):
        for ip in test_ips:
            details = 'failed' if i >= 7 else 'success'
            is_anomalous, anomaly_details, score = ai_detector.detect_anomalous_behavior(
                client_ip=ip,
                action='login_attempt',
                details=details,
                path='/auth/login'
            )

            if is_anomalous:
                print(f"[异常检测] IP: {ip}, 异常: {is_anomalous}, 分数: {score:.2f}, 详情: {anomaly_details}")

    stats = ai_detector.get_anomaly_stats()
    print(f"\n异常检测统计:")
    print(f"总事件数: {stats['total_events']}")
    print(f"异常事件数: {stats['anomalous_events']}")
    print(f"异常率: {stats['anomaly_rate']}%")
    print(f"异常IP排行: {stats['top_anomalous_ips']}")
    print(f"按行为分类: {stats['anomaly_by_action']}")

    learning_data = ai_detector.export_learning_data()
    print(f"\n学习数据:")
    print(str(learning_data))
