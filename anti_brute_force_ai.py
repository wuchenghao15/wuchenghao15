#!/usr/bin/env python3
"""
MTSCOS 数据撞库防御AI
检测和防御数据撞库攻击

import os
import sys
# JSON import removed - using database
import time
import sqlite3
import logging
import hashlib
import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/anti_brute_force.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AntiBruteForceAI')

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path='mtscos.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_database()

    def initialize_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.create_tables()
            logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def create_tables(self):
        """创建数据表"""
        # 登录尝试表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            success INTEGER NOT NULL,
            attempt_count INTEGER DEFAULT 1
        )

        # 封锁记录表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS block_list (
            ip_address TEXT NOT NULL,
            blocked_at TEXT NOT NULL,
            block_duration INTEGER DEFAULT 3600,
        )

        # 异常检测表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomaly_detection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            anomaly_score REAL NOT NULL,
            action_taken TEXT NOT NULL
        )
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            updated_at TEXT NOT NULL
        )

        self.initialize_policies()
    def initialize_policies(self):
        """初始化安全策略"""
        policies = [
            ('max_attempts', '5', '最大登录尝试次数'),
            ('block_duration', '3600', '封锁持续时间(秒)'),
            ('window_size', '300', '时间窗口大小(秒)'),
            ('anomaly_threshold', '0.7', '异常检测阈值'),
            ('auto_block_enabled', 'true', '自动封锁功能')
        ]
        for policy_name, policy_value, description in policies:
            INSERT OR REPLACE INTO security_policies (policy_name, policy_value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ''', (policy_name, policy_value, description, datetime.datetime.now().isoformat()))

        self.conn.commit()
    def get_policy(self, policy_name: str) -> str:
        """获取安全策略"""
        self.cursor.execute('''
        SELECT policy_value FROM security_policies WHERE policy_name = ?
        ''', (policy_name,))
        row = self.cursor.fetchone()
        return row[0] if row else None

        """记录登录尝试"""
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute('''
        INSERT INTO login_attempts (username, ip_address, timestamp, success)
        VALUES (?, ?, ?, ?)
        ''', (username, ip_address, timestamp, 1 if success else 0))
        self.conn.commit()

        """获取指定时间窗口内的登录尝试"""
        window_start = (datetime.datetime.now() - datetime.timedelta(seconds=window_seconds)).isoformat()
        SELECT * FROM login_attempts
        WHERE ip_address = ? AND timestamp >= ?
        ORDER BY timestamp DESC
        ''', (ip_address, window_start))

        for row in self.cursor.fetchall():
            attempts.append({
                'id': row[0],
                'username': row[1],
                'ip_address': row[2],
                'timestamp': row[3],
                'success': bool(row[4]),
                'attempt_count': row[5]
            })
        return attempts
        """封锁IP"""
        blocked_at = datetime.datetime.now().isoformat()
        self.cursor.execute('''
        INSERT INTO block_list (ip_address, blocked_at, reason, block_duration)
        VALUES (?, ?, ?, ?)
        ''', (ip_address, blocked_at, reason, duration))
        self.conn.commit()

        """检查IP是否被封锁"""
        now = datetime.datetime.now().isoformat()
        self.cursor.execute('''
        SELECT * FROM block_list
        WHERE ip_address = ? AND status = 'active' AND
        datetime(blocked_at, '+' || block_duration || ' seconds') > ?
        ''', (ip_address, now))
        return self.cursor.fetchone() is not None
    def unblock_ip(self, ip_address: str):
        """解除IP封锁"""
        self.cursor.execute('''
        UPDATE block_list SET status = 'inactive' WHERE ip_address = ? AND status = 'active'
        ''', (ip_address,))
        self.conn.commit()

    def log_anomaly(self, ip_address: str, username: str, anomaly_score: float, risk_level: str, action_taken: str):
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute('''
        INSERT INTO anomaly_detection (ip_address, username, timestamp, anomaly_score, risk_level, action_taken)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (ip_address, username, timestamp, anomaly_score, risk_level, action_taken))
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

class AntiBruteForceAI:
    """数据撞库防御AI"""

    def __init__(self):
        self.db = DatabaseManager()
        self.ip_attempts = defaultdict(lambda: deque(maxlen=100))
        self.username_attempts = defaultdict(lambda: deque(maxlen=100))
        self.session_tracker = {}
        self.initialize_parameters()
        logger.info("数据撞库防御AI初始化完成")

        """初始化参数"""
        self.max_attempts = int(self.db.get_policy('max_attempts'))
        self.block_duration = int(self.db.get_policy('block_duration'))
        self.window_size = int(self.db.get_policy('window_size'))
        self.anomaly_threshold = float(self.db.get_policy('anomaly_threshold'))
        self.auto_block_enabled = self.db.get_policy('auto_block_enabled') == 'true'

    def check_login_attempt(self, username: str, password: str, ip_address: str) -> Dict[str, Any]:
        # 检查IP是否被封锁
            return {
                'allowed': False,
                'reason': 'IP地址已被封锁',
                'risk_level': 'high',
                'action': 'blocked'
            }

        # 分析登录尝试模式
        analysis = self.analyze_login_pattern(username, ip_address)

        # 检查是否超过尝试次数限制
        if analysis['attempt_count'] >= self.max_attempts:
            if self.auto_block_enabled:
                self.db.block_ip(ip_address, f'超过{self.max_attempts}次登录尝试', self.block_duration)
            return {
                'allowed': False,
                'reason': f'登录尝试次数超过限制 ({self.max_attempts}次)',
                'risk_level': 'high',
                'action': 'blocked'
            }

        # 检查异常行为
        if analysis['anomaly_score'] > self.anomaly_threshold:
            risk_level = self.get_risk_level(analysis['anomaly_score'])
            if risk_level == 'high' and self.auto_block_enabled:
                self.db.block_ip(ip_address, f'异常登录行为，异常分数: {analysis["anomaly_score"]:.2f}', self.block_duration)

            return {
                'allowed': False,
                'reason': f'检测到异常登录行为，异常分数: {analysis["anomaly_score"]:.2f}',
                'risk_level': risk_level,
                'action': 'blocked' if risk_level == 'high' else 'monitored'
            }

        # 允许登录尝试
        return {
            'allowed': True,
            'reason': '登录尝试正常',
            'risk_level': 'low',
            'action': 'allowed'
        }

    def analyze_login_pattern(self, username: str, ip_address: str) -> Dict[str, Any]:
        """分析登录模式"""
        # 记录当前尝试
        current_time = time.time()
        self.ip_attempts[ip_address].append(current_time)
        self.username_attempts[username].append(current_time)

        window_attempts = self.db.get_login_attempts(ip_address, self.window_size)
        # 计算尝试次数
        attempt_count = len(window_attempts)
        # 计算异常分数

        success_count = sum(1 for attempt in window_attempts if attempt['success'])
        success_rate = success_count / attempt_count if attempt_count > 0 else 0

            'attempt_count': attempt_count,
            'anomaly_score': anomaly_score,
            'window_size': self.window_size
        }

    def calculate_anomaly_score(self, username: str, ip_address: str, attempts: List[Dict[str, Any]]) -> float:
        score = 0.0

        # 1. 尝试频率
            time_diffs = []
            for i in range(1, len(attempts)):
                t1 = datetime.datetime.fromisoformat(attempts[i-1]['timestamp']).timestamp()
                t2 = datetime.datetime.fromisoformat(attempts[i]['timestamp']).timestamp()
                time_diffs.append(abs(t1 - t2))

            if time_diffs:
                if avg_time_diff < 2:  # 频繁尝试
                    score += 0.3

        # 2. 成功率
        success_count = sum(1 for attempt in attempts if attempt['success'])
        success_rate = success_count / len(attempts) if attempts else 0
        if success_rate < 0.1 and len(attempts) > 3:
            score += 0.4

        # 3. 用户名多样性
        usernames = set(attempt['username'] for attempt in attempts)
        if len(usernames) > 3 and len(attempts) > 5:
            score += 0.3


    def get_risk_level(self, anomaly_score: float) -> str:
        """获取风险等级"""
        if anomaly_score >= 0.8:
            return 'high'
        elif anomaly_score >= 0.5:
            return 'medium'
        else:
            return 'low'

    def process_login_result(self, username: str, ip_address: str, success: bool):
        """处理登录结果"""
        self.db.log_login_attempt(username, ip_address, success)

        # 分析登录模式
        analysis = self.analyze_login_pattern(username, ip_address)

        # 记录异常
        if analysis['anomaly_score'] > self.anomaly_threshold:
            risk_level = self.get_risk_level(analysis['anomaly_score'])
            action = 'blocked' if risk_level == 'high' else 'monitored'
            self.db.log_anomaly(ip_address, username, analysis['anomaly_score'], risk_level, action)

    def get_ip_status(self, ip_address: str) -> Dict[str, Any]:
        """获取IP状态"""
        is_blocked = self.db.is_ip_blocked(ip_address)
        attempts = self.db.get_login_attempts(ip_address, self.window_size)

        return {
            'ip_address': ip_address,
            'is_blocked': is_blocked,
            'attempts_in_window': len(attempts),
            'window_size': self.window_size,
            'max_attempts': self.max_attempts
        }

    def unblock_ip(self, ip_address: str):
        """解除IP封锁"""
        self.db.unblock_ip(ip_address)
        logger.info(f"已解除IP封锁: {ip_address}")

    def update_policy(self, policy_name: str, policy_value: str):
        """更新安全策略"""
        logger.info(f"更新安全策略: {policy_name} = {policy_value}")

    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        # 这里需要实现报告生成逻辑
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'ok',
            'message': '报告生成成功'
        }

class BruteForceDetector:
    """撞库攻击检测器"""

    def __init__(self, anti_brute_force_ai: AntiBruteForceAI):
        self.ai = anti_brute_force_ai
        self.detection_history = []
        logger.info("撞库攻击检测器初始化完成")
        """检测撞库攻击"""
        # 分析登录模式
        analysis = self.ai.analyze_login_pattern(username, ip_address)
        # 检测撞库攻击

            'username': username,
            'is_brute_force': is_brute_force,
            'analysis': analysis,
            'timestamp': datetime.datetime.now().isoformat()
        }

        self.detection_history.append(detection_result)

    def is_brute_force_attack(self, analysis: Dict[str, Any]) -> bool:
        """判断是否为撞库攻击"""
        # 基于尝试次数和异常分数判断
        if analysis['attempt_count'] >= self.ai.max_attempts:

        if analysis['anomaly_score'] >= 0.8:
            return True

        if analysis['success_rate'] < 0.1 and analysis['attempt_count'] >= 5:
            return True

        return False

class SecurityManager:
    """安全管理器"""

    def __init__(self):
        self.brute_force_detector = BruteForceDetector(self.anti_brute_force_ai)
        logger.info("安全管理器初始化完成")

    def process_login(self, username: str, password: str, ip_address: str) -> Dict[str, Any]:
        """处理登录请求"""
        # 检查登录尝试
        check_result = self.anti_brute_force_ai.check_login_attempt(username, password, ip_address)

        # 模拟登录验证（实际应用中应该调用真实的验证逻辑）
        success = self.validate_credentials(username, password)

        # 处理登录结果
        self.anti_brute_force_ai.process_login_result(username, ip_address, success)

        # 检测撞库攻击
        detection = self.brute_force_detector.detect_brute_force(username, ip_address)

        return {
            'login_allowed': check_result['allowed'],
            'login_success': success if check_result['allowed'] else False,
            'reason': check_result['reason'],
            'action': check_result['action'],
            'analysis': detection['analysis']
        }

    def validate_credentials(self, username: str, password: str) -> bool:
        """验证凭证（模拟）"""
        # 这里应该实现真实的凭证验证逻辑
        # 这里只是模拟
            'admin': 'admin123',
            'user': 'user123',
            'test': 'test123'

        return username in valid_users and valid_users[username] == password

    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            'anti_brute_force_enabled': True,
            'auto_block_enabled': self.anti_brute_force_ai.auto_block_enabled,
            'max_attempts': self.anti_brute_force_ai.max_attempts,
            'block_duration': self.anti_brute_force_ai.block_duration,
            'window_size': self.anti_brute_force_ai.window_size
        }

        """获取IP状态"""
        return self.anti_brute_force_ai.get_ip_status(ip_address)
    def unblock_ip(self, ip_address: str):
        """解除IP封锁"""

    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全报告"""
        return self.anti_brute_force_ai.generate_report()

def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("MTSCOS 数据撞库防御AI启动")
    logger.info("=" * 80)

    # 创建安全管理器
    security_manager = SecurityManager()

    # 测试登录
    test_cases = [
        # 正常登录
        ('admin', 'admin123', '192.168.1.100'),
        ('admin', 'wrongpass', '192.168.1.101'),
        # 多次错误尝试
        ('admin', 'wrong2', '192.168.1.102'),
        ('admin', 'wrong4', '192.168.1.102'),
        ('admin', 'wrong5', '192.168.1.102'),
        # 撞库攻击模拟
        ('user1', 'pass1', '192.168.1.103'),
        ('user2', 'pass2', '192.168.1.103'),
        ('user4', 'pass4', '192.168.1.103'),
        ('user5', 'pass5', '192.168.1.103')
    for username, password, ip in test_cases:
        result = security_manager.process_login(username, password, ip)

    # 测试IP状态
    ip_status = security_manager.get_ip_status('192.168.1.102')
    logger.info(f"IP状态: {ip_status}")

    # 测试安全状态
    security_status = security_manager.get_security_status()

    # 生成安全报告
    report = security_manager.generate_security_report()
    logger.info(f"安全报告: {report}")

    logger.info("=" * 80)
    logger.info("MTSCOS 数据撞库防御AI运行完成")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
