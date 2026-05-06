#!/usr/bin/env python3
"""
增强版AI异常检测器 - 引入机器学习能力和自动学习机制

# JSON import removed - using database
import os
import time
import sqlite3
from datetime import datetime
from collections import defaultdict, deque

class EnhancedAIAnomalyDetector:
    """增强版AI异常检测器，支持机器学习和自动学习"""

    def __init__(self, db_path='ai_anomaly.db', learning_rate=0.1):
        """初始化增强版AI异常检测器

        Args:
            db_path: 数据库路径
            learning_rate: 学习率
        self.db_path = db_path
        self.learning_rate = learning_rate
        self._init_db()

        # 正常行为模式参数
        self.normal_patterns = {
            'failed_login_attempts': 3,          # 失败登录尝试次数阈值
            'rapid_attempts_window': 60,         # 快速尝试时间窗口（秒）
            'rapid_attempts_threshold': 5,       # 快速尝试次数阈值
            'unusual_user_agent_score': 0.7,     # 异常User-Agent分数阈值
            'anomaly_score_threshold': 0.8,      # 整体异常分数阈值
            'consecutive_failures_threshold': 3, # 连续失败阈值
            'time_between_attempts': 5           # 尝试间隔阈值（秒）
        }

        # 最近尝试记录，用于实时检测
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建异常检测日志表
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

        # 创建学习数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_data (
                feature_name TEXT UNIQUE NOT NULL,
                value REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_ip ON anomaly_logs(client_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_anomalous ON anomaly_logs(is_anomalous)')

        conn.commit()
        conn.close()

    def _load_learning_data(self):
        """从数据库加载学习数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for row in cursor.fetchall():
                feature_name, value, confidence = row
                if feature_name in self.normal_patterns:
                    # 结合学习值和初始值，根据置信度加权
                    self.normal_patterns[feature_name] = (
                        value * confidence + self.normal_patterns[feature_name] * (1 - confidence)
                    )
        except Exception as e:
            print(f"Error loading learning data: {str(e)}")
        finally:
            conn.close()

    def _save_learning_data(self):
        """保存学习数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
                cursor.execute('SELECT id FROM learning_data WHERE feature_name = ?', (feature_name,))
                existing = cursor.fetchone()

                if existing:
                    # 更新现有记录，提高置信度
                    cursor.execute('''
                        UPDATE learning_data
                            last_updated = CURRENT_TIMESTAMP
                        WHERE feature_name = ?
                    ''', (value, feature_name))
                    # 插入新记录，初始置信度0.5
                    cursor.execute('''
                        INSERT INTO learning_data (feature_name, value, confidence)
                        VALUES (?, ?, 0.5)
                    ''', (feature_name, value))
            conn.commit()
        except Exception as e:
        finally:
            conn.close()

    def _log_anomaly(self, client_ip, action, is_anomalous, anomaly_score, anomaly_details,
                    user_agent='', path='', metadata=None):
        """记录异常检测日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO anomaly_logs
                user_agent, path, metadata)
                client_ip, action, 1 if is_anomalous else 0, anomaly_score,
                anomaly_details, user_agent, path, str(metadata)
        except Exception as e:
            print(f"Error logging anomaly: {str(e)}")
        finally:
            conn.close()

    def _calculate_anomaly_score(self, client_ip, attempt_record):

        Args:
            client_ip: 客户端IP

        Returns:
            float: 异常分数（0-1）
        factors = []

        # 获取客户端尝试历史
        client_history = self.recent_attempts[client_ip]
        current_time = time.time()
        # 1. 快速连续尝试因子
        if recent_attempts_count > self.normal_patterns['rapid_attempts_threshold']:
            rapid_factor = min(
                (recent_attempts_count / self.normal_patterns['rapid_attempts_threshold']) * 0.3,
            )
            score += rapid_factor
            factors.append(f"快速连续尝试 ({recent_attempts_count}/{self.normal_patterns['rapid_attempts_threshold']})")

        # 2. 失败尝试因子
        if 'failed' in attempt_record.get('details', '').lower():
            failed_factor = min(
                (client_history['total_failed'] / self.normal_patterns['failed_login_attempts']) * 0.25,
                0.25
            )
            score += failed_factor
            factors.append(f"失败尝试 ({client_history['total_failed']}/{self.normal_patterns['failed_login_attempts']})")

        # 3. 连续失败因子
        if client_history['consecutive_failures'] > self.normal_patterns['consecutive_failures_threshold']:
            consecutive_factor = min(
                (client_history['consecutive_failures'] / self.normal_patterns['consecutive_failures_threshold']) * 0.25,
                0.25
            )
            score += consecutive_factor
            factors.append(f"连续失败 ({client_history['consecutive_failures']}/{self.normal_patterns['consecutive_failures_threshold']})")

        # 4. 尝试间隔因子
        if client_history['last_attempt'] > 0:
            time_between = current_time - client_history['last_attempt']
            if time_between < self.normal_patterns['time_between_attempts']:
                interval_factor = min(
                    (self.normal_patterns['time_between_attempts'] / max(time_between, 0.1)) * 0.1,
                    0.1
                )
                score += interval_factor
                factors.append(f"尝试间隔过短 ({time_between:.2f}秒)")

        # 5. 异常User-Agent因子
        user_agent = attempt_record.get('user_agent', '')
        if self._is_anomalous_user_agent(user_agent):
            score += 0.1
            factors.append("异常User-Agent")

        # 6. 异常路径因子
        path = attempt_record.get('path', '')
        if self._is_anomalous_path(path):
            score += 0.1
            factors.append("异常访问路径")
        return min(score, 1.0), factors

    def _is_anomalous_user_agent(self, user_agent):
        """检测异常User-Agent"""
        # 增强版User-Agent检测
        if not user_agent or len(user_agent) < 10:
            return True

        # 可疑User-Agent模式
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

        """检测异常访问路径"""
        # 增强版路径检测
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
        """检测多种类型的异常行为，支持机器学习和自动调整

        Args:
            client_ip: 客户端IP
            action: 行为类型
            user_agent: User-Agent
            path: 访问路径

        Returns:
            tuple: (是否异常, 异常详情, 异常分数)
        current_time = time.time()

        # 1. 记录当前尝试
        attempt_record = {
            'timestamp': current_time,
            'action': action,
            'details': details,
            'user_agent': user_agent,
            'path': path
        }
        # 2. 更新客户端历史
        client_history = self.recent_attempts[client_ip]
        client_history['login_attempts'].append(attempt_record)
        cutoff_time = current_time - self.normal_patterns['rapid_attempts_window']
        while client_history['login_attempts'] and client_history['login_attempts'][0]['timestamp'] < cutoff_time:
            client_history['login_attempts'].popleft()

            client_history['total_failed'] += 1
            client_history['consecutive_failures'] += 1
        else:
            client_history['consecutive_failures'] = 0

        client_history['last_attempt'] = current_time

        # 4. 计算异常分数
        anomaly_score, factors = self._calculate_anomaly_score(client_ip, attempt_record)
        # 5. 判断是否异常
        is_anomalous = anomaly_score >= self.normal_patterns['anomaly_score_threshold']

        # 6. 生成异常详情
        if is_anomalous:
            anomaly_details = f"检测到异常行为 (分数: {anomaly_score:.2f}): {'; '.join(factors)}"
        else:
            anomaly_details = None

        # 7. 记录异常日志
        self._log_anomaly(
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

        # 8. 自动学习和调整参数
        if self.learning_enabled:
            self._automatic_learning(client_ip, is_anomalous, anomaly_score, factors)
        return is_anomalous, anomaly_details, anomaly_score

    def _automatic_learning(self, client_ip, is_anomalous, anomaly_score, factors):
        """自动学习和调整检测参数

            client_ip: 客户端IP
            is_anomalous: 是否异常
            anomaly_score: 异常分数
        # 只在有足够数据时进行学习
        client_history = self.recent_attempts[client_ip]
        if len(client_history['login_attempts']) < 10:
            return

        # 分析检测因子，调整相应的阈值
        for factor in factors:
            if '快速连续尝试' in factor:
                # 调整快速尝试阈值
                current_threshold = self.normal_patterns['rapid_attempts_threshold']
                if is_anomalous:
                    # 异常情况，降低阈值以提高检测灵敏度
                    new_threshold = current_threshold * (1 - self.learning_rate * 0.5)
                else:
                    # 正常情况，提高阈值以减少误报
                    new_threshold = current_threshold * (1 + self.learning_rate * 0.2)

                self.normal_patterns['rapid_attempts_threshold'] = max(3, min(20, new_threshold))

            elif '失败尝试' in factor:
                # 调整失败尝试阈值
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
        # 定期保存学习数据
        if int(time.time()) % 300 == 0:  # 每5分钟保存一次
            self._save_learning_data()

    def get_anomaly_stats(self, time_window=3600):
        """获取异常检测统计信息

            time_window: 时间窗口（秒）

        Returns:
            dict: 统计信息
        cursor = conn.cursor()

        try:
            cutoff_time = datetime.fromtimestamp(time.time() - time_window).strftime('%Y-%m-%d %H:%M:%S')

            # 总事件数
            total_events = cursor.fetchone()[0]

            # 异常事件数
            cursor.execute('SELECT COUNT(*) FROM anomaly_logs WHERE is_anomalous = 1 AND timestamp >= ?', (cutoff_time,))

            # 按IP分组的异常事件
            cursor.execute('''
                SELECT client_ip, COUNT(*) as count
                WHERE is_anomalous = 1 AND timestamp >= ?
                ORDER BY count DESC
                LIMIT 10
            ''', (cutoff_time,))
            top_anomalous_ips = [{'ip': row[0], 'count': row[1]} for row in cursor.fetchall()]
            # 按行为类型分组的异常事件
            cursor.execute('''
                FROM anomaly_logs
                WHERE is_anomalous = 1 AND timestamp >= ?
                GROUP BY action
                ORDER BY count DESC
            ''', (cutoff_time,))
            anomaly_by_action = [{'action': row[0], 'count': row[1]} for row in cursor.fetchall()]
                'anomalous_events': anomalous_events,
                'anomaly_rate': round(anomalous_events / total_events * 100, 2) if total_events > 0 else 0,
                'top_anomalous_ips': top_anomalous_ips,
                'time_window': time_window,
                'current_time': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting anomaly stats: {str(e)}")
                'total_events': 0,
                'anomalous_events': 0,
                'anomaly_rate': 0,
                'top_anomalous_ips': [],
                'anomaly_by_action': [],
                'time_window': time_window,
            }
        finally:
            conn.close()

    def export_learning_data(self):
        """导出学习数据

        Returns:
            dict: 学习数据
        return {
            'learning_rate': self.learning_rate,
            'learning_enabled': self.learning_enabled,
            'export_time': datetime.now().isoformat()
        }

# 单例模式 - 全局AI异常检测器实例
global_ai_detector = None

def get_ai_detector():
    """获取全局AI异常检测器实例

    Returns:
        EnhancedAIAnomalyDetector: AI异常检测器实例
    global global_ai_detector
        global_ai_detector = EnhancedAIAnomalyDetector()
    return global_ai_detector

if __name__ == '__main__':
    # 创建AI异常检测器实例
    ai_detector = EnhancedAIAnomalyDetector()

    # 测试检测功能

    for i in range(10):
        for ip in test_ips:
            details = 'failed' if i >= 7 else 'success'
                client_ip=ip,
                action='login_attempt',
                path='/auth/login'

            if is_anomalous:
                print(f"[异常检测] IP: {ip}, 异常: {is_anomalous}, 分数: {score:.2f}, 详情: {anomaly_details}")

    # 获取统计信息
    stats = ai_detector.get_anomaly_stats()
    print(f"\n异常检测统计:")
    print(f"总事件数: {stats['total_events']}")
    print(f"异常事件数: {stats['anomalous_events']}")
    print(f"异常率: {stats['anomaly_rate']}%")
    print(f"异常IP排行: {stats['top_anomalous_ips']}")
    print(f"按行为分类: {stats['anomaly_by_action']}")

    # 导出学习数据
    learning_data = ai_detector.export_learning_data()
    print(f"\n学习数据:")
    print(str(learning_data, indent=2))
