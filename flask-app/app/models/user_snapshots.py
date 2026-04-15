#!/usr/bin/env python3
"""
用户快照模型
用于处理用户状态快照的记录和查询
"""

import json
import time
import gzip
import base64
import zlib
import lzma
from app.utils.db import db_manager
from app.utils.logging import logger

class UserSnapshot:
    """用户状态快照数据模型"""
    
    def __init__(self, snapshot_id=None, user_id=None, session_id=None, timestamp=None, snapshot_type=None, version='1.0', size=0, compressed=0, compression_algorithm=None, checksum=None, status='active', metadata=None, data=None):
        self.snapshot_id = snapshot_id
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.snapshot_type = snapshot_type
        self.version = version
        self.size = size
        self.compressed = compressed
        self.compression_algorithm = compression_algorithm
        self.checksum = checksum
        self.status = status
        self.metadata = metadata or {}
        self.data = data or {}
    
    # 删除了 _connect_db 方法，改用 db_manager
    
    @staticmethod
    def create_table():
        """创建用户快照表"""
        # 创建表
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS user_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                snapshot_type TEXT NOT NULL,
                version TEXT DEFAULT '1.0',
                size INTEGER DEFAULT 0,
                compressed INTEGER DEFAULT 0,
                compression_algorithm TEXT DEFAULT NULL,
                checksum TEXT DEFAULT NULL,
                status TEXT DEFAULT 'active',
                metadata TEXT NOT NULL DEFAULT '{}',
                data TEXT NOT NULL DEFAULT '{}'
            )
        '''
        db_manager.execute(create_table_sql)
        
        # 检查并添加缺失的列
        try:
            # 检查 compression_algorithm 列是否存在
            db_manager.execute('SELECT compression_algorithm FROM user_snapshots LIMIT 1')
        except Exception as e:
            # 如果不存在，添加该列
            db_manager.execute('ALTER TABLE user_snapshots ADD COLUMN compression_algorithm TEXT DEFAULT NULL')
        
        try:
            # 检查 checksum 列是否存在
            db_manager.execute('SELECT checksum FROM user_snapshots LIMIT 1')
        except Exception as e:
            # 如果不存在，添加该列
            db_manager.execute('ALTER TABLE user_snapshots ADD COLUMN checksum TEXT DEFAULT NULL')
        
        # 添加索引以提高查询性能
        index_queries = [
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_user_id ON user_snapshots(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_session_id ON user_snapshots(session_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_timestamp ON user_snapshots(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_type ON user_snapshots(snapshot_type)',
            'CREATE INDEX IF NOT EXISTS idx_user_snapshots_status ON user_snapshots(status)'  # 新增状态索引
        ]
        
        for query in index_queries:
            db_manager.execute(query)
        
        logger.info("用户快照表创建成功")
    
    @staticmethod
    def _compress_data(data_str, algorithm='gzip'):
        """使用指定算法压缩数据"""
        data_bytes = data_str.encode('utf-8')
        
        if algorithm == 'gzip':
            compressed = gzip.compress(data_bytes, compresslevel=9)
        elif algorithm == 'zlib':
            compressed = zlib.compress(data_bytes, level=9)
        elif algorithm == 'lzma':
            compressed = lzma.compress(data_bytes, preset=9)
        else:
            raise ValueError(f"不支持的压缩算法: {algorithm}")
        
        return base64.b64encode(compressed).decode('utf-8')
    
    @staticmethod
    def _decompress_data(compressed_str, algorithm='gzip'):
        """使用指定算法解压缩数据"""
        decoded = base64.b64decode(compressed_str.encode('utf-8'))
        
        if algorithm == 'gzip':
            decompressed = gzip.decompress(decoded)
        elif algorithm == 'zlib':
            decompressed = zlib.decompress(decoded)
        elif algorithm == 'lzma':
            decompressed = lzma.decompress(decoded)
        else:
            raise ValueError(f"不支持的压缩算法: {algorithm}")
        
        return decompressed.decode('utf-8')
    
    @staticmethod
    def _select_best_compression_algorithm(data_str):
        """智能选择最优压缩算法"""
        data_bytes = data_str.encode('utf-8')
        original_size = len(data_bytes)
        
        # 对于小数据，直接返回None，不压缩
        if original_size < 512:
            return None
        
        # 测试不同压缩算法
        algorithms = ['gzip', 'zlib', 'lzma']
        results = []
        
        for algo in algorithms:
            try:
                compressed = UserSnapshot._compress_data(data_str, algo)
                compressed_size = len(compressed.encode('utf-8'))
                compression_ratio = compressed_size / original_size
                
                results.append({
                    'algorithm': algo,
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio
                })
            except Exception as e:
                logger.warning(f"测试压缩算法 {algo} 失败: {str(e)}")
                continue
        
        # 选择压缩率最高的算法
        if results:
            best_result = min(results, key=lambda x: x['compression_ratio'])
            # 只有当压缩率小于0.9时才使用压缩
            if best_result['compression_ratio'] < 0.9:
                return best_result['algorithm']
        
        return None
    
    @staticmethod
    def _calculate_checksum(data_str):
        """计算数据的MD5校验和"""
        import hashlib
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create(user_id, session_id, timestamp=None, snapshot_type="pre_vikey_switch", version='1.0', metadata=None, data=None, should_compress=True):
        """创建用户快照"""
        # 生成唯一的快照ID
        snapshot_id = f"snapshot_{int(time.time() * 1000)}_{user_id}_{session_id[:8]}"
        
        # 确保data和metadata是JSON字符串
        data = data or {}
        metadata = metadata or {}
        data_json = json.dumps(data)
        metadata_json = json.dumps(metadata)
        
        # 计算原始大小
        original_size = len(data_json.encode('utf-8'))
        
        # 初始化压缩相关变量
        compressed = 0
        final_data = data_json
        final_size = original_size
        compression_algorithm = None
        
        # 如果需要压缩且数据大小超过阈值，则进行智能压缩
        if should_compress and original_size > 512:
            best_algorithm = UserSnapshot._select_best_compression_algorithm(data_json)
            if best_algorithm:
                compressed_data = UserSnapshot._compress_data(data_json, best_algorithm)
                compressed_size = len(compressed_data.encode('utf-8'))
                
                # 只有当压缩后大小更小时才使用压缩数据
                if compressed_size < original_size:
                    final_data = compressed_data
                    final_size = compressed_size
                    compressed = 1
                    compression_algorithm = best_algorithm
        
        # 计算数据校验和
        checksum = UserSnapshot._calculate_checksum(data_json)
        
        # 插入数据
        insert_sql = '''
            INSERT INTO user_snapshots 
            (snapshot_id, user_id, session_id, timestamp, snapshot_type, version, size, compressed, compression_algorithm, checksum, status, metadata, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (snapshot_id, user_id, session_id, timestamp or time.time(), snapshot_type, version, final_size, compressed, compression_algorithm, checksum, 'active', metadata_json, final_data)
        cursor, success = db_manager.execute(insert_sql, params)
        
        logger.debug(f"创建用户快照成功: {snapshot_id}, 用户ID: {user_id}, 会话ID: {session_id}, 原始大小: {original_size}字节, 存储大小: {final_size}字节, 压缩: {'是' if compressed else '否'}, 算法: {compression_algorithm}, 校验和: {checksum}")
        return UserSnapshot(snapshot_id, user_id, session_id, timestamp or time.time(), snapshot_type, version, final_size, compressed, compression_algorithm, checksum, 'active', metadata, data)
    
    @staticmethod
    def get_by_id(snapshot_id):
        """通过ID获取用户快照"""
        # 查询数据
        query = 'SELECT * FROM user_snapshots WHERE snapshot_id=?'
        row = db_manager.fetch_one(query, (snapshot_id,))
        
        if row:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {snapshot_id}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            return UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            )
        return None
    
    @staticmethod
    def get_by_session(session_id):
        """通过会话ID获取用户快照"""
        # 查询数据
        query = 'SELECT * FROM user_snapshots WHERE session_id=? ORDER BY timestamp DESC'
        rows = db_manager.fetch_all(query, (session_id,))
        
        snapshots = []
        for row in rows:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {row[0]}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            snapshots.append(UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            ))
        return snapshots
    
    @staticmethod
    def get_by_user(user_id):
        """通过用户ID获取用户快照"""
        # 查询数据
        query = 'SELECT * FROM user_snapshots WHERE user_id=? AND status=? ORDER BY timestamp DESC LIMIT 100'
        rows = db_manager.fetch_all(query, (user_id, 'active'))
        
        snapshots = []
        for row in rows:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {row[0]}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            snapshots.append(UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            ))
        return snapshots
    
    @staticmethod
    def get_latest(limit=50, status='active'):
        """获取最新的用户快照"""
        # 查询数据
        query = 'SELECT * FROM user_snapshots WHERE status=? ORDER BY timestamp DESC LIMIT ?'
        rows = db_manager.fetch_all(query, (status, limit))
        
        snapshots = []
        for row in rows:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {row[0]}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            snapshots.append(UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            ))
        return snapshots
    
    @staticmethod
    def get_by_type_and_time_range(snapshot_type, start_time, end_time, user_id=None, status='active', limit=100):
        """按类型和时间范围查询快照"""
        query = '''
            SELECT * FROM user_snapshots 
            WHERE snapshot_type=? AND timestamp BETWEEN ? AND ? AND status=?
        '''
        params = [snapshot_type, start_time, end_time, status]
        
        if user_id:
            query += ' AND user_id=?'
            params.append(user_id)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        rows = db_manager.fetch_all(query, params)
        
        snapshots = []
        for row in rows:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {row[0]}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            snapshots.append(UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            ))
        return snapshots
    
    @staticmethod
    def delete_old_snapshots(retention_days=7):
        """删除旧的用户快照"""
        # 计算保留时间阈值
        retention_threshold = time.time() - (retention_days * 24 * 3600)
        
        # 删除超过保留时间的快照
        delete_sql = 'DELETE FROM user_snapshots WHERE timestamp < ?'
        cursor, success = db_manager.execute(delete_sql, (retention_threshold,))
        
        # 获取删除的记录数
        deleted_count = cursor.rowcount if cursor else 0
        
        if deleted_count > 0:
            logger.info(f"删除了 {deleted_count} 个旧的用户快照")
        
        return deleted_count
    
    def save(self, should_compress=True):
        """保存用户快照"""
        # 确保data和metadata是JSON字符串
        data = self.data or {}
        metadata = self.metadata or {}
        data_json = json.dumps(data)
        metadata_json = json.dumps(metadata)
        
        # 计算原始大小
        original_size = len(data_json.encode('utf-8'))
        
        # 初始化压缩相关变量
        final_compressed = self.compressed
        final_data = data_json
        final_size = original_size
        final_compression_algorithm = self.compression_algorithm
        
        # 如果需要压缩且数据大小超过阈值，则进行智能压缩
        if should_compress and original_size > 512:
            best_algorithm = UserSnapshot._select_best_compression_algorithm(data_json)
            if best_algorithm:
                compressed_data = UserSnapshot._compress_data(data_json, best_algorithm)
                compressed_size = len(compressed_data.encode('utf-8'))
                
                # 只有当压缩后大小更小时才使用压缩数据
                if compressed_size < original_size:
                    final_data = compressed_data
                    final_size = compressed_size
                    final_compressed = 1
                    final_compression_algorithm = best_algorithm
                else:
                    final_compressed = 0
                    final_compression_algorithm = None
            else:
                final_compressed = 0
                final_compression_algorithm = None
        else:
            final_compressed = 0
            final_compression_algorithm = None
        
        # 计算数据校验和
        final_checksum = UserSnapshot._calculate_checksum(data_json)
        
        # 更新对象属性
        self.size = final_size
        self.compressed = final_compressed
        self.compression_algorithm = final_compression_algorithm
        self.checksum = final_checksum
        
        if self.snapshot_id:
            # 更新现有记录
            update_sql = '''
                UPDATE user_snapshots SET user_id=?, session_id=?, timestamp=?, snapshot_type=?, version=?, 
                size=?, compressed=?, compression_algorithm=?, checksum=?, status=?, metadata=?, data=?
                WHERE snapshot_id=?
            '''
            params = (self.user_id, self.session_id, self.timestamp, self.snapshot_type, self.version, 
                     final_size, final_compressed, final_compression_algorithm, final_checksum, self.status, 
                     metadata_json, final_data, self.snapshot_id)
            db_manager.execute(update_sql, params)
        else:
            # 创建新记录
            # 生成唯一的快照ID
            self.snapshot_id = f"snapshot_{int(time.time() * 1000)}_{self.user_id}_{self.session_id[:8]}"
            
            insert_sql = '''
                INSERT INTO user_snapshots (snapshot_id, user_id, session_id, timestamp, snapshot_type, version, 
                size, compressed, compression_algorithm, checksum, status, metadata, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.snapshot_id, self.user_id, self.session_id, self.timestamp or time.time(), 
                     self.snapshot_type, self.version, final_size, final_compressed, final_compression_algorithm, 
                     final_checksum, self.status, metadata_json, final_data)
            db_manager.execute(insert_sql, params)
        
        logger.debug(f"保存用户快照成功: {self.snapshot_id}, 原始大小: {original_size}字节, 存储大小: {final_size}字节, 压缩: {'是' if final_compressed else '否'}, 算法: {final_compression_algorithm}, 校验和: {final_checksum}")
        return self
    
    def restore(self):
        """恢复用户快照"""
        if not self.snapshot_id:
            return False
        
        # 更新快照状态为恢复
        update_sql = 'UPDATE user_snapshots SET status=? WHERE snapshot_id=?'
        cursor, success = db_manager.execute(update_sql, ('restored', self.snapshot_id))
        updated_count = cursor.rowcount if cursor else 0
        
        if updated_count > 0:
            self.status = 'restored'
            logger.debug(f"恢复用户快照成功: {self.snapshot_id}")
            return True
        return False
    
    def archive(self):
        """归档用户快照"""
        if not self.snapshot_id:
            return False
        
        # 更新快照状态为归档
        update_sql = 'UPDATE user_snapshots SET status=? WHERE snapshot_id=?'
        cursor, success = db_manager.execute(update_sql, ('archived', self.snapshot_id))
        updated_count = cursor.rowcount if cursor else 0
        
        if updated_count > 0:
            self.status = 'archived'
            logger.debug(f"归档用户快照成功: {self.snapshot_id}")
            return True
        return False
    
    @staticmethod
    def get_restored_snapshots(limit=50):
        """获取已恢复的快照"""
        # 查询数据
        query = 'SELECT * FROM user_snapshots WHERE status=? ORDER BY timestamp DESC LIMIT ?'
        rows = db_manager.fetch_all(query, ('restored', limit))
        
        snapshots = []
        for row in rows:
            # 处理数据解压缩
            data_str = row[12]  # 数据在第13列（索引12）
            if row[7]:  # compressed flag is 1
                compression_algorithm = row[8] or 'gzip'  # 压缩算法在第9列（索引8）
                data_str = UserSnapshot._decompress_data(data_str, compression_algorithm)
            
            # 验证快照完整性
            original_data = json.loads(data_str) if data_str else {}
            original_json = json.dumps(original_data)
            stored_checksum = row[9]  # 校验和在第10列（索引9）
            
            if stored_checksum and stored_checksum != UserSnapshot._calculate_checksum(original_json):
                logger.warning(f"快照完整性验证失败: {row[0]}, 存储校验和: {stored_checksum}, 计算校验和: {UserSnapshot._calculate_checksum(original_json)}")
            
            snapshots.append(UserSnapshot(
                snapshot_id=row[0],
                user_id=row[1],
                session_id=row[2],
                timestamp=row[3],
                snapshot_type=row[4],
                version=row[5],
                size=row[6],
                compressed=row[7],
                compression_algorithm=row[8],
                checksum=row[9],
                status=row[10],  # 状态在第11列（索引10）
                metadata=json.loads(row[11]) if row[11] != '{}' else {},  # 元数据在第12列（索引11）
                data=original_data
            ))
        return snapshots
    
    def delete(self):
        """删除用户快照"""
        if not self.snapshot_id:
            return False
        
        # 删除快照
        delete_sql = 'DELETE FROM user_snapshots WHERE snapshot_id=?'
        cursor, success = db_manager.execute(delete_sql, (self.snapshot_id,))
        deleted_count = cursor.rowcount if cursor else 0
        
        if deleted_count > 0:
            logger.debug(f"删除用户快照成功: {self.snapshot_id}")
            return True
        return False
