#!/usr/bin/env python3
"""
IP管理模块 - 实现黑白名单和沙箱IP的持久化存储

import sqlite3
import os
from datetime import datetime
# JSON import removed - using database
class IPManager:
    """IP管理类，处理黑白名单和沙箱IP的持久化存储"""

    def __init__(self, db_path='ip_manager.db'):
        """初始化IP管理器"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建IP管理表
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

        # 创建索引，提高查询效率
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_address ON ip_management(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON ip_management(type)')

        conn.commit()
        conn.close()

    def add_ip(self, ip_address, ip_type, reason, added_by, expires_at=None, metadata=None):
        """添加IP到指定列表

        Args:
            ip_address: IP地址
            ip_type: 类型 ('whitelist', 'blacklist', 'sandbox')
            reason: 添加原因
            added_by: 添加者
            expires_at: 过期时间
            metadata: 元数据

        Returns:
            bool: 是否添加成功
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM ip_management WHERE ip_address = ?', (ip_address,))
            existing = cursor.fetchone()

            if existing:
                # 更新现有记录
                cursor.execute('''
                    UPDATE ip_management
                    SET type = ?, reason = ?, added_by = ?, expires_at = ?,
                        last_updated = CURRENT_TIMESTAMP, metadata = ?
                ''', (ip_type, reason, added_by, expires_at, str(metadata), ip_address))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO ip_management
                    (ip_address, type, reason, added_by, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)

            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding IP {ip_address}: {str(e)}")
            conn.rollback()
            return False
            conn.close()

    def remove_ip(self, ip_address):
        """从所有列表中移除IP

        Args:
            ip_address: IP地址
        Returns:
            bool: 是否移除成功
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

            conn.commit()
            print(f"Error removing IP {ip_address}: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

        """获取IP的状态

            ip_address: IP地址

        Returns:
            str: IP状态 ('whitelist', 'blacklist', 'sandbox', 'normal')

        try:
                SELECT type, expires_at FROM ip_management
            ''', (ip_address,))

                return 'normal'  # 不在任何列表中

            # 检查是否过期
            if expires_at:
                if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
                    # IP已过期，从列表中移除
                    self.remove_ip(ip_address)
                    return 'normal'

            return ip_type
        except Exception as e:
            return 'normal'
        finally:
            conn.close()

        """检查IP是否在白名单中

        Args:
            ip_address: IP地址

        Returns:
            bool: 是否在白名单中
        return self.get_ip_status(ip_address) == 'whitelist'

    def is_ip_blacklisted(self, ip_address):
        """检查IP是否在黑名单中

            ip_address: IP地址

        Returns:
            bool: 是否在黑名单中
        return self.get_ip_status(ip_address) == 'blacklist'
    def is_ip_in_sandbox(self, ip_address):

        Args:
            ip_address: IP地址
            bool: 是否在沙箱中
        return self.get_ip_status(ip_address) == 'sandbox'

    def get_list(self, list_type, limit=100):
        """获取指定类型的IP列表
        Args:
            list_type: 列表类型 ('whitelist', 'blacklist', 'sandbox')
            limit: 返回数量限制

            list: IP列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
                SELECT ip_address, reason, added_by, added_at, expires_at, metadata
                FROM ip_management
                WHERE type = ?
                LIMIT ?
            ''', (list_type, limit))
            results = []
                ip_address, reason, added_by, added_at, expires_at, metadata = row
                results.append({
                    'ip_address': ip_address,
                    'added_by': added_by,
                    'added_at': added_at,
                    'metadata': eval(metadata) if metadata else None
                })

            return results
        except Exception as e:
            print(f"Error getting {list_type} list: {str(e)}")
            return []
        finally:
            conn.close()

    def get_stats(self):
        """获取IP管理统计信息

        Returns:
            dict: 统计信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

            stats = {}

            # 获取各类型数量
            for ip_type in ['whitelist', 'blacklist', 'sandbox']:
                cursor.execute('SELECT COUNT(*) FROM ip_management WHERE type = ?', (ip_type,))

            # 获取总数
            cursor.execute('SELECT COUNT(*) FROM ip_management')
            stats['total'] = cursor.fetchone()[0]

        except Exception as e:
            return {'whitelist': 0, 'blacklist': 0, 'sandbox': 0, 'total': 0}
        finally:
            conn.close()

    def clear_expired_ips(self):
        """清理过期的IP记录

        Returns:
            int: 清理的记录数量
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM ip_management WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP')
            return cursor.rowcount
        except Exception as e:
            print(f"Error clearing expired IPs: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

# 单例模式 - 全局IP管理器实例
global_ip_manager = None


        IPManager: IP管理器实例
    global global_ip_manager
    if global_ip_manager is None:
        global_ip_manager = IPManager()
    return global_ip_manager

# 测试代码
if __name__ == '__main__':
    ip_manager = IPManager()

    ip_manager.add_ip('192.168.1.1', 'whitelist', '测试白名单', 'system')
    ip_manager.add_ip('10.0.0.1', 'blacklist', '测试黑名单', 'system')
    ip_manager.add_ip('172.16.0.1', 'sandbox', '测试沙箱', 'system')

    # 测试查询
    print(f"192.168.1.1 白名单状态: {ip_manager.is_ip_whitelisted('192.168.1.1')}")
    print(f"172.16.0.1 沙箱状态: {ip_manager.is_ip_in_sandbox('172.16.0.1')}")
    print(f"8.8.8.8 状态: {ip_manager.get_ip_status('8.8.8.8')}")
    # 测试获取列表
    print("\n白名单列表:")
    for ip in ip_manager.get_list('whitelist'):
        print(f"  - {ip['ip_address']}: {ip['reason']}")

    print("\n黑名单列表:")
    for ip in ip_manager.get_list('blacklist'):

    print("\n沙箱列表:")
    for ip in ip_manager.get_list('sandbox'):
        print(f"  - {ip['ip_address']}: {ip['reason']}")

    # 测试统计信息
    print(f"\n统计信息: {ip_manager.get_stats()}")

    # 测试移除IP
    print(f"10.0.0.1 黑名单状态: {ip_manager.is_ip_blacklisted('10.0.0.1')}")
    print(f"移除后的统计信息: {ip_manager.get_stats()}")
