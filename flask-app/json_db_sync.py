#!/usr/bin/env python3
"""
JSON与数据库同步服务
实时监控JSON文件变化，同步到数据库，并确保数据库数据有效性

import os
# JSON import removed - using database
import hashlib
import time
import sqlite3
import threading
from datetime import datetime
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('json_db_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库连接配置
DB_PATH = 'app.db'

# 监控的JSON文件路径
JSON_DIR = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'
JSON_EXTENSIONS = ['.json']

# 监控间隔（秒）
MONITOR_INTERVAL = 5

class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""
    FILE_WINS = "file_wins"  # 文件优先
    DB_WINS = "db_wins"      # 数据库优先
    NEWEST_WINS = "newest_wins"  # 最新修改优先
    MERGE = "merge"         # 合并内容（仅适用于JSON对象）

class JSONDBSync:
    """JSON与数据库同步服务"""

    def __init__(self):
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.json_file_hashs = {}  # 存储JSON文件的哈希值，用于检测变化
        self.last_sync_time = time.time()
        self.conflict_strategy = ConflictResolutionStrategy.NEWEST_WINS
        self.chunk_size = 8192  # 8KB 块大小，用于大文件处理
        self.initialize_db()

    def initialize_db(self):
        """初始化数据库，确保json_files表存在"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 确保json_files表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS json_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                file_hash TEXT,
                last_modified TEXT,
                sync_status TEXT DEFAULT 'pending',
                sync_error TEXT DEFAULT NULL
            )

        # 添加索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_json_files_file_path ON json_files(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_json_files_sync_status ON json_files(sync_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_json_files_last_modified ON json_files(last_modified)')

        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

    def get_file_hash(self, file_path):
        """计算文件的SHA256哈希值，优化大文件处理"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # 以配置的块大小读取文件内容并更新哈希
                for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {str(e)}")
            return None

    def _resolve_conflict(self, file_path, file_content, db_content, file_mtime, db_mtime):
        """解决文件与数据库之间的冲突"""
        logger.warning(f"检测到冲突: {file_path}")

        if self.conflict_strategy == ConflictResolutionStrategy.FILE_WINS:
            logger.info(f"冲突解决策略: 文件优先，使用文件内容")
            return file_content, True

        elif self.conflict_strategy == ConflictResolutionStrategy.DB_WINS:
            logger.info(f"冲突解决策略: 数据库优先，使用数据库内容")
            return db_content, False

        elif self.conflict_strategy == ConflictResolutionStrategy.NEWEST_WINS:
            file_time = datetime.datetime.fromisoformat(file_mtime).timestamp()
            db_time = datetime.datetime.fromisoformat(db_mtime).timestamp()

            if file_time > db_time:
                logger.info(f"冲突解决策略: 最新修改优先，文件更新 (文件: {file_mtime}, 数据库: {db_mtime})")
                return file_content, True
            else:
                return db_content, False

        elif self.conflict_strategy == ConflictResolutionStrategy.MERGE:
                # 尝试合并JSON内容
                file_json = eval(file_content)
                db_json = eval(db_content)

                if isinstance(file_json, dict) and isinstance(db_json, dict):
                    # 合并两个JSON对象，文件内容优先
                    merged_json = {**db_json, **file_json}
                    merged_content = str(merged_json, ensure_ascii=False, indent=2)
                    logger.info(f"冲突解决策略: 合并内容")
                    return merged_content, True
                else:
                    logger.warning(f"无法合并非JSON对象内容，使用文件优先策略")
                    return file_content, True
            except json.JSONDecodeError as e:
                return file_content, True

        return file_content, True

        """将JSON文件同步到数据库，可选择上传后删除本地文件，支持增量同步和冲突解决"""
        try:
            # 获取文件基本信息
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_hash = self.get_file_hash(file_path)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

            if not file_hash:
                return False

            # 连接数据库
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # 检查文件是否已存在
            existing = cursor.fetchone()

            uploaded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 读取文件内容（延迟读取，仅在需要时读取）
            content = None

            if existing:
                # 文件已存在，检查哈希值是否变化
                existing_id, existing_hash, existing_content, existing_mtime = existing

                if existing_hash != file_hash:
                    # 哈希值变化，需要同步
                    logger.info(f"检测到文件变化: {file_path}")

                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 验证JSON格式
                    eval(content)

                    # 检测冲突
                    if existing_mtime > file_mtime:
                        # 数据库中的记录比文件更新，发生冲突
                        final_content, use_file = self._resolve_conflict(file_path, content, existing_content, file_mtime, existing_mtime)

                        if use_file:
                            # 使用文件内容更新数据库
                            cursor.execute('''
                                UPDATE json_files
                                SET content = ?, uploaded_at = ?, file_size = ?, file_hash = ?, last_modified = ?, sync_status = ?
                                WHERE id = ?
                            logger.info(f"更新JSON文件记录（冲突解决）: {file_path}")
                        else:
                            # 使用数据库内容更新文件
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(final_content)
                            logger.info(f"更新本地文件（冲突解决）: {file_path}")
                    else:
                        # 正常更新，文件比数据库更新
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 验证JSON格式
                        eval(content)

                        cursor.execute('''
                            UPDATE json_files
                            SET content = ?, uploaded_at = ?, file_size = ?, file_hash = ?, last_modified = ?, sync_status = ?
                        logger.info(f"更新JSON文件记录: {file_path}")
                # 文件不存在，插入新记录
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 验证JSON格式

                cursor.execute('''
                    INSERT INTO json_files (file_path, file_name, content, uploaded_at, file_size, file_hash, last_modified, sync_status)
                ''', (file_path, file_name, content, uploaded_at, file_size, file_hash, file_mtime, 'synced'))
            conn.close()
            self.json_file_hashs[file_path] = file_hash
            # 如果需要，上传后删除本地文件
                try:
                    logger.info(f"已删除本地JSON文件: {file_path}")
                    if file_path in self.json_file_hashs:
                        del self.json_file_hashs[file_path]
                    logger.error(f"删除本地JSON文件失败 {file_path}: {str(e)}")
                    return False

            return True

        except json.JSONDecodeError as e:
            logger.error(f"JSON格式错误 {file_path}: {str(e)}")
            # 更新数据库中的同步状态为错误
            cursor = conn.cursor()
                UPDATE json_files
                SET sync_status = ?, sync_error = ?
            ''', ('error', str(e), file_path))
            conn.commit()
            return False
        except Exception as e:
            # 更新数据库中的同步状态为错误
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
                SET sync_status = ?, sync_error = ?
            conn.commit()
            conn.close()
    def sync_db_to_json(self, file_path):
        """将数据库中的JSON数据同步回文件，支持增量同步和冲突解决"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # 从数据库获取最新内容
            cursor.execute('SELECT content, file_hash, uploaded_at, last_modified FROM json_files WHERE file_path = ?', (file_path,))
            db_data = cursor.fetchone()
                conn.close()
                return False
            db_content, db_hash, db_uploaded_at, db_last_modified = db_data
            conn.close()

            # 检查文件是否存在
            current_hash = self.get_file_hash(file_path) if file_exists else None

            if file_exists:
                # 文件存在，检查哈希值是否一致
                if current_hash == db_hash:
                    # 文件内容与数据库一致，无需同步
                    return True

                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

                # 检测冲突
                if file_mtime > db_last_modified:

                    final_content, use_file = self._resolve_conflict(file_path, file_content, db_content, file_mtime, db_last_modified)

                    if use_file:
                        # 使用文件内容更新数据库
                            UPDATE json_files
                            WHERE file_path = ?
                        conn.commit()
                        logger.info(f"使用文件内容更新数据库（冲突解决）: {file_path}")
                        # 更新哈希值缓存
                        self.json_file_hashs[file_path] = self.get_file_hash(file_path)
                        return True
                    else:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(final_content)
                        logger.info(f"已将数据库数据同步回文件（冲突解决）: {file_path}")
                        # 更新哈希值缓存
                        self.json_file_hashs[file_path] = db_hash
                        return True
                    # 数据库比文件更新，正常同步
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(db_content)
                    # 更新哈希值缓存
                    self.json_file_hashs[file_path] = db_hash
                    return True
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(db_content)
                logger.info(f"从数据库创建文件: {file_path}")
                self.json_file_hashs[file_path] = db_hash
                return True

            logger.error(f"同步数据库数据到文件失败 {file_path}: {str(e)}")
            # 更新数据库中的同步状态为错误
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
                WHERE file_path = ?
            ''', ('error', str(e), file_path))
            conn.commit()
            conn.close()

    def validate_db_json_data(self):
        """验证数据库中JSON数据的有效性"""
        try:
            cursor = conn.cursor()
            records = cursor.fetchall()

            invalid_records = []
            for record_id, file_path, content in records:
                    eval(content)
                except json.JSONDecodeError:
                    invalid_records.append(record_id)
                    logger.warning(f"数据库中JSON数据无效，记录ID: {record_id}, 文件: {file_path}")

                placeholders = ','.join(['?'] * len(invalid_records))
                cursor.execute(f'DELETE FROM json_files WHERE id IN ({placeholders})', invalid_records)
                logger.info(f"已删除 {len(invalid_records)} 条无效JSON记录")

            conn.close()

            logger.error(f"验证数据库JSON数据失败: {str(e)}")
            return False
        """扫描所有JSON文件并同步，可选择上传后删除本地文件"""

        for root, dirs, files in os.walk(JSON_DIR):
            for file in files:
                    file_path = os.path.join(root, file)
                    # 同步到数据库
        logger.info("JSON文件扫描完成")
    def monitor_json_files(self):
        logger.info("启动JSON文件监控服务")

            try:
                current_json_files = set()
                # 记录同步统计信息
                sync_stats = {
                    'changed_files': 0,
                    'failed_files': 0

                start_time = time.time()

                for root, dirs, files in os.walk(JSON_DIR):
                    # 过滤出JSON文件

                    for file in json_files:
                        file_path = os.path.join(root, file)
                        current_json_files.add(file_path)
                        # 计算当前文件哈希

                                logger.debug(f"检测到JSON文件变化: {file_path}")
                                # 直接将文件同步到数据库（文件变化以文件为准）
                                if self.sync_json_to_db(file_path):
                                    sync_stats['synced_files'] += 1
                                else:

                # 检查是否有文件被删除
                deleted_files = previous_files - current_json_files

                if deleted_files:
                    self.delete_missing_files(deleted_files)

                # 验证数据库中JSON数据的有效性（每10次检查执行一次，优化性能）
                if int(time.time() - self.last_sync_time) % (MONITOR_INTERVAL * 10) < MONITOR_INTERVAL:
                    self.validate_db_json_data()

                # 记录同步耗时和统计信息
                elapsed_time = time.time() - start_time
                logger.info(f"JSON文件监控周期完成 - 耗时: {elapsed_time:.2f}秒, 总文件: {sync_stats['total_files']}, 变化文件: {sync_stats['changed_files']}, 同步成功: {sync_stats['synced_files']}, 同步失败: {sync_stats['failed_files']}")

                # 更新最后同步时间
                self.last_sync_time = time.time()

                time.sleep(MONITOR_INTERVAL)

            except Exception as e:
                logger.error(f"监控JSON文件失败: {str(e)}")
                time.sleep(MONITOR_INTERVAL)

    def delete_missing_files(self, deleted_files):
        """删除数据库中不存在的文件记录"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            for file_path in deleted_files:
                # 删除数据库中的记录
                cursor.execute('DELETE FROM json_files WHERE file_path = ?', (file_path,))
                logger.info(f"已从数据库删除文件记录: {file_path}")
                # 从哈希缓存中移除
                if file_path in self.json_file_hashs:
                    del self.json_file_hashs[file_path]

            conn.close()
        except Exception as e:
            logger.error(f"删除数据库中缺失文件记录失败: {str(e)}")

    def start(self):
        """启动同步服务"""
        # 初始化哈希值缓存
        self.scan_json_files()

        # 启动监控线程
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self.monitor_json_files)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("JSON与数据库同步服务已启动")

    def stop(self):
        """停止同步服务"""
        self.stop_event.set()
            self.monitor_thread.join()
        logger.info("JSON与数据库同步服务已停止")

# 命令行使用示例
    import argparse

    parser = argparse.ArgumentParser(description='JSON与数据库同步服务')
    parser.add_argument('--start', action='store_true', help='启动同步服务')
    parser.add_argument('--stop', action='store_true', help='停止同步服务')
    parser.add_argument('--scan', action='store_true', help='扫描并同步所有JSON文件')
    parser.add_argument('--validate', action='store_true', help='验证数据库JSON数据有效性')

    args = parser.parse_args()

    sync_service = JSONDBSync()

    if args.start:
        sync_service.start()
        try:
            # 保持主进程运行
                time.sleep(1)
        except KeyboardInterrupt:
            sync_service.stop()
        sync_service.scan_json_files(args.delete_after_upload)
    elif args.validate:
        sync_service.validate_db_json_data()
    elif args.stop:
        sync_service.stop()
    else:
