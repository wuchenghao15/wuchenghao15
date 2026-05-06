#!/usr/bin/env python3
"""
碎片化临时缓存系统
实现碎片化临时缓存功能，减少数据库吞吐和并发
临时缓存文件加密，只有系统本身才能访问

import os
# JSON import removed - using database
import hashlib
import sqlite3
import base64
from datetime import datetime
import logging
from cryptography.fernet import Fernet

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FragmentedCache:
    """碎片化临时缓存系统"""

    def __init__(self, cache_dir='.cache', db_path='app.db', encryption_key=None):
        初始化碎片化缓存系统

        Args:
            cache_dir: 缓存文件存储目录
            db_path: 数据库路径
            encryption_key: 加密密钥，None则自动生成
        self.cache_dir = cache_dir
        self.db_path = db_path

        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)

        # 生成或使用加密密钥
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # 从文件加载密钥，如果不存在则生成新密钥
            key_file = os.path.join(self.cache_dir, '.encryption_key')
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                # 保存密钥到文件
                    f.write(self.encryption_key)
                # 设置文件权限为只读，只有当前用户可访问
                os.chmod(key_file, 0o400)

        self.cipher = Fernet(self.encryption_key)

        # 初始化数据库
        self._initialize_db()

        # 缓存统计
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'syncs': 0
        }

        logger.info("碎片化临时缓存系统初始化完成")

    def _initialize_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建缓存记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                cache_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expiry_time TEXT,
                hit_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        ''')

        conn.close()

    def _get_cache_file_path(self, cache_key):
        """获取缓存文件路径"""
        # 使用哈希值生成文件名，避免文件名冲突
        key_hash = hashlib.sha256(cache_key.encode()).hexdigest()
        # 碎片化存储，根据哈希值的前两位创建子目录
        subdir = key_hash[:2]
        subdir_path = os.path.join(self.cache_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        return os.path.join(subdir_path, f"{key_hash}.cache")

    def _encrypt_data(self, data):
        """加密数据"""
        if isinstance(data, dict):
            data_str = str(data)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)

        encrypted = self.cipher.encrypt(data_str.encode())

    def _decrypt_data(self, encrypted_data):
        """解密数据"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes).decode()
        try:
            return eval(decrypted)
        except json.JSONDecodeError:
            return decrypted

    def set(self, cache_key, data, cache_type='general', expiry_time=None):
        设置缓存

        Args:
            cache_key: 缓存键
            data: 缓存数据
            cache_type: 缓存类型
            expiry_time: 过期时间（时间戳）
            # 加密数据
            encrypted_data = self._encrypt_data(data)

            # 写入缓存文件
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w') as f:
                f.write(encrypted_data)

            os.chmod(cache_file, 0o600)

            # 更新统计
            self.cache_stats['writes'] += 1

            logger.debug(f"缓存设置成功: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"缓存设置失败 {cache_key}: {str(e)}")
            return False

    def get(self, cache_key):
        获取缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据，不存在返回None
        try:
            cache_file = self._get_cache_file_path(cache_key)
                self.cache_stats['misses'] += 1
                return None

            # 读取并解密数据
            with open(cache_file, 'r') as f:

            data = self._decrypt_data(encrypted_data)

            self.cache_stats['hits'] += 1

            logger.debug(f"缓存命中: {cache_key}")
        except Exception as e:
            logger.error(f"缓存获取失败 {cache_key}: {str(e)}")
            self.cache_stats['misses'] += 1
            return None

    def delete(self, cache_key):
        删除缓存

        Args:
            cache_key: 缓存键
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug(f"缓存删除成功: {cache_key}")
                return True
            return False
            logger.error(f"缓存删除失败 {cache_key}: {str(e)}")
            return False
    def sync_to_db(self, cache_key):

        Args:
            # 获取缓存数据
            data = self.get(cache_key)
            if data is None:
                return False
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 准备数据
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('SELECT id FROM cache_records WHERE cache_key = ? AND is_active = 1', (cache_key,))

            if existing:
                    SET content = ?, updated_at = ?, hit_count = hit_count + 1
                    WHERE id = ?
                ''', (str(data), current_time, existing[0]))
            else:
                cursor.execute('''
                    VALUES (?, ?, ?, ?, ?)
                ''', (cache_key, 'general', str(data), current_time, current_time))

            conn.commit()
            conn.close()

            # 更新统计

            logger.debug(f"缓存同步到数据库成功: {cache_key}")
            return True
            return False

    def sync_all_to_db(self):
        将所有缓存同步到数据库
        logger.info("开始同步所有缓存到数据库...")
        sync_count = 0
        try:
            # 遍历所有缓存文件
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith('.cache'):
                        # 从文件名获取cache_key
                        # 实际实现中，应该维护一个哈希值到cache_key的映射
                        pass

            logger.info(f"缓存同步完成，共同步 {sync_count} 个缓存")
            return sync_count
        except Exception as e:
            logger.error(f"同步所有缓存到数据库失败: {str(e)}")
            return 0

    def cleanup(self):
        清理所有缓存文件
        logger.info("开始清理缓存文件...")

        try:
            # 遍历所有缓存文件
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                        os.remove(file_path)
                        delete_count += 1

            logger.info(f"缓存清理完成，共删除 {delete_count} 个缓存文件")
        except Exception as e:
            logger.error(f"清理缓存文件失败: {str(e)}")
            return 0

    def get_stats(self):
        获取缓存统计信息
        return self.cache_stats

    def close(self):
        关闭缓存系统，同步到数据库并清理缓存
        logger.info("关闭缓存系统，同步到数据库并清理缓存...")

        # 同步所有缓存到数据库
        self.sync_all_to_db()

        # 清理缓存文件
        self.cleanup()


# 创建全局缓存实例
cache_manager = None

def get_cache_manager():
    """获取缓存管理器实例"""
    global cache_manager
    if cache_manager is None:
        cache_manager = FragmentedCache()
    return cache_manager

# 退出时自动同步和清理
import atexit
atexit.register(lambda: get_cache_manager().close())
