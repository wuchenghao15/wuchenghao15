# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
IP管理模块 - 实现黑白名单和沙箱IP的持久化存储
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
import os
from datetime import datetime
import sys


class IPManager:
    """IP管理类,处理黑白名单和沙箱IP的持久化存储"""

    def __init__(self, db_path='ip_manager.db'):
        """初始化IP管理器"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_management (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('whitelist', 'blacklist', 'sandbox')),
            reason TEXT NOT NULL,
            added_by TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_address ON ip_management(ip_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON ip_management(type)')

            conn.commit()

    def add_ip(self, ip_address, ip_type, reason, added_by, expires_at=None, metadata=None):
        """
        添加IP到指定列表

        Args:
            ip_address: IP地址
            ip_type: 类型 ('whitelist', 'blacklist', 'sandbox')
            reason: 添加原因
            added_by: 添加者
            expires_at: 过期时间
            metadata: 元数据

        Returns:
            bool: 是否添加成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT id FROM ip_management WHERE ip_address = ?', (ip_address,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute('''
                    UPDATE ip_management
                    SET type = ?, reason = ?, added_by = ?, expires_at = ?,
                    last_updated = CURRENT_TIMESTAMP, metadata = ?
                    WHERE ip_address = ?
                    ''', (ip_type, reason, added_by, expires_at, str(metadata), ip_address))
                else:
                    cursor.execute('''
                    INSERT INTO ip_management
                    (ip_address, type, reason, added_by, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ip_address, ip_type, reason, added_by, expires_at, str(metadata)))

                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error adding IP {ip_address}: {str(e)}")
                conn.rollback()
                return False

    def remove_ip(self, ip_address):
        """
        从所有列表中移除IP

        Args:
            ip_address: IP地址

        Returns:
            bool: 是否移除成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM ip_management WHERE ip_address = ?', (ip_address,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error removing IP {ip_address}: {str(e)}")
                conn.rollback()
                return False

    def get_ip_status(self, ip_address):
        """
        获取IP的状态

        Args:
            ip_address: IP地址

        Returns:
            str: IP状态 ('whitelist', 'blacklist', 'sandbox', 'normal')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT type, expires_at FROM ip_management
                WHERE ip_address = ?
                ''', (ip_address,))

                result = cursor.fetchone()
                if not result:
                    return 'normal'

                ip_type, expires_at = result

                if expires_at:
                    if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
                        self.remove_ip(ip_address)
                        return 'normal'

                return ip_type
        except Exception as e:
            logger.error(f"Error getting IP status: {str(e)}")
            return 'normal'

    def is_ip_whitelisted(self, ip_address):
        """
        检查IP是否在白名单中

        Args:
            ip_address: IP地址

        Returns:
            bool: 是否在白名单中
        """
        return self.get_ip_status(ip_address) == 'whitelist'

    def is_ip_blacklisted(self, ip_address):
        """
        检查IP是否在黑名单中

        Args:
            ip_address: IP地址

        Returns:
            bool: 是否在黑名单中
        """
        return self.get_ip_status(ip_address) == 'blacklist'

    def is_ip_in_sandbox(self, ip_address):
        """
        检查IP是否在沙箱中

        Args:
            ip_address: IP地址

        Returns:
            bool: 是否在沙箱中
        """
        return self.get_ip_status(ip_address) == 'sandbox'

    def get_list(self, list_type, limit=100):
        """
        获取指定类型的IP列表

        Args:
            list_type: 列表类型 ('whitelist', 'blacklist', 'sandbox')
            limit: 返回数量限制

        Returns:
            list: IP列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                SELECT ip_address, reason, added_by, added_at, expires_at, metadata
                FROM ip_management
                WHERE type = ?
                LIMIT ?
                ''', (list_type, limit))

                results = []
                for row in cursor.fetchall():
                    ip_address, reason, added_by, added_at, expires_at, metadata = row
                    results.append({
                        'ip_address': ip_address,
                        'reason': reason,
                        'added_by': added_by,
                        'added_at': added_at,
                        'expires_at': expires_at,
                        'metadata': eval(metadata) if metadata else None
                    })

                return results
            except Exception as e:
                logger.error(f"Error getting {list_type} list: {str(e)}")
                return []

    def get_stats(self):
        """
        获取IP管理统计信息

        Returns:
            dict: 统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                stats = {}

                for ip_type in ['whitelist', 'blacklist', 'sandbox']:
                    cursor.execute('SELECT COUNT(*) FROM ip_management WHERE type = ?', (ip_type,))
                    stats[ip_type] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM ip_management')
                stats['total'] = cursor.fetchone()[0]

                return stats
            except Exception as e:
                logger.error(f"Error getting stats: {str(e)}")
                return {'whitelist': 0, 'blacklist': 0, 'sandbox': 0, 'total': 0}

    def clear_expired_ips(self):
        """
        清理过期的IP记录

        Returns:
            int: 清理的记录数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM ip_management WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP')
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
            except Exception as e:
                logger.error(f"Error clearing expired IPs: {str(e)}")
                conn.rollback()
                return 0


global_ip_manager = None


def get_ip_manager():
    """
    获取全局IP管理器实例

    Returns:
        IPManager: IP管理器实例
    """
    global global_ip_manager
    if global_ip_manager is None:
        global_ip_manager = IPManager()
    return global_ip_manager


if __name__ == '__main__':
    ip_manager = IPManager()

    ip_manager.add_ip('192.168.1.1', 'whitelist', '测试白名单', 'system')
    ip_manager.add_ip('10.0.0.1', 'blacklist', '测试黑名单', 'system')
    ip_manager.add_ip('172.16.0.1', 'sandbox', '测试沙箱', 'system')

    print(f"192.168.1.1 白名单状态: {ip_manager.is_ip_whitelisted('192.168.1.1')}")
    print(f"172.16.0.1 沙箱状态: {ip_manager.is_ip_in_sandbox('172.16.0.1')}")
    print(f"8.8.8.8 状态: {ip_manager.get_ip_status('8.8.8.8')}")

    print("\n白名单列表:")
    for ip in ip_manager.get_list('whitelist'):
        print(f"  - {ip['ip_address']}: {ip['reason']}")

    print("\n黑名单列表:")
    for ip in ip_manager.get_list('blacklist'):
        print(f"  - {ip['ip_address']}: {ip['reason']}")

    print("\n沙箱列表:")
    for ip in ip_manager.get_list('sandbox'):
        print(f"  - {ip['ip_address']}: {ip['reason']}")

    print(f"\n统计信息: {ip_manager.get_stats()}")

    ip_manager.remove_ip('10.0.0.1')
    print(f"10.0.0.1 黑名单状态: {ip_manager.is_ip_blacklisted('10.0.0.1')}")
    print(f"移除后的统计信息: {ip_manager.get_stats()}")
