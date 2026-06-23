"""
MongoSQL - SQLite到MongoDB同步模块
实现SQLite数据库与MongoDB的双向同步备份
"""

import sqlite3
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import logging
import shutil

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, BulkWriteError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoSQLSync:
    """SQLite到MongoDB同步器"""
    
    def __init__(self, sqlite_path: str, mongo_uri: str = "mongodb://localhost:27017", 
                 mongo_db: str = "mtscos", sync_interval: int = 60):
        """
        初始化MongoSQL同步器
        
        Args:
            sqlite_path: SQLite数据库路径
            mongo_uri: MongoDB连接URI
            mongo_db: MongoDB数据库名
            sync_interval: 同步间隔（秒）
        """
        self.sqlite_path = sqlite_path
        self.mongo_uri = mongo_uri
        self.mongo_db_name = mongo_db
        self.sync_interval = sync_interval
        self.mongo_client = None
        self.mongo_db = None
        self.sync_thread = None
        self.running = False
        
        # 同步状态
        self.last_sync_time = None
        self.last_sync_stats = {}
        
        # 连接MongoDB
        if PYMONGO_AVAILABLE:
            self._connect_mongo()
    
    def _connect_mongo(self):
        """连接MongoDB"""
        try:
            self.mongo_client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # 测试连接
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[self.mongo_db_name]
            logger.info(f"✅ MongoDB连接成功: {self.mongo_db_name}")
            
            # 创建索引集合
            self._ensure_indexes()
        except ConnectionFailure as e:
            logger.warning(f"⚠️ MongoDB连接失败: {e}")
            logger.info("💡 请确保MongoDB服务已启动，或设置 MONGODB_URI 环境变量")
            self.mongo_client = None
            self.mongo_db = None
    
    def _ensure_indexes(self):
        """确保MongoDB索引存在"""
        if not self.mongo_db:
            return
        
        # 为重要集合创建索引
        indexes = {
            "users": ["user_id", "email", "username"],
            "questions": ["question_id", "bank_id", "type", "difficulty"],
            "question_banks": ["bank_id", "subject", "grade_level"],
            "science_formulas": ["formula_id", "subject", "category"],
            "ai_employees": ["employee_id", "name", "category"],
            "logs": ["log_id", "type", "created_at"],
        }
        
        for collection, index_fields in indexes.items():
            try:
                for field in index_fields:
                    self.mongo_db[collection].create_index(field)
            except Exception as e:
                logger.debug(f"索引创建跳过: {collection}.{field}")
    
    def get_sqlite_tables(self) -> List[str]:
        """获取SQLite所有表名"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def get_table_data(self, table_name: str, since: int = None) -> List[Dict]:
        """获取表数据"""
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if since:
            # 获取自指定时间戳后更新的数据
            cursor.execute(f"SELECT * FROM {table_name} WHERE updated_at > ? OR created_at > ?", (since, since))
        else:
            cursor.execute(f"SELECT * FROM {table_name}")
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return data
    
    def sync_table(self, table_name: str) -> Dict[str, int]:
        """同步单个表到MongoDB"""
        if not self.mongo_db:
            return {"status": "mongodb_not_connected", "inserted": 0, "updated": 0}
        
        try:
            data = self.get_table_data(table_name)
            if not data:
                return {"status": "no_data", "inserted": 0, "updated": 0}
            
            collection = self.mongo_db[table_name]
            
            # 转换数据类型
            for doc in data:
                for key, value in doc.items():
                    if isinstance(value, (bytes, bytearray)):
                        doc[key] = str(value)
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        pass
                
                # 添加SQLite同步元数据
                doc["_sqlite_synced_at"] = int(time.time())
            
            # 批量插入/更新
            result = collection.replace_one(
                {"_id" if "_id" in data[0] else list(data[0].keys())[0]: data[0].get("_id") or data[0].get(list(data[0].keys())[0])},
                data[0],
                upsert=True
            )
            
            # 使用bulk_write进行高效同步
            from pymongo import UpdateOne, InsertOne
            
            operations = []
            primary_key = self._get_primary_key(table_name)
            
            for doc in data:
                if primary_key and primary_key in doc:
                    operations.append(
                        UpdateOne(
                            {primary_key: doc[primary_key]},
                            {"$set": doc},
                            upsert=True
                        )
                    )
            
            if operations:
                result = collection.bulk_write(operations, ordered=False)
                return {
                    "status": "success",
                    "inserted": result.upserted_count,
                    "updated": result.modified_count
                }
            
            return {"status": "success", "inserted": 0, "updated": 0}
            
        except Exception as e:
            logger.error(f"同步表 {table_name} 失败: {e}")
            return {"status": "error", "error": str(e), "inserted": 0, "updated": 0}
    
    def _get_primary_key(self, table_name: str) -> Optional[str]:
        """获取表的主键名"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        for col in columns:
            if col[5] == 1:  # pk == 1 表示是主键
                return col[1]
        return None
    
    def sync_all(self) -> Dict[str, Any]:
        """同步所有表到MongoDB"""
        tables = self.get_sqlite_tables()
        results = {}
        stats = {"tables": 0, "total_inserted": 0, "total_updated": 0}
        
        logger.info(f"开始同步 {len(tables)} 个表到MongoDB...")
        
        for table in tables:
            # 跳过系统表
            if table.startswith("sqlite_"):
                continue
            
            result = self.sync_table(table)
            results[table] = result
            
            if result.get("status") == "success":
                stats["tables"] += 1
                stats["total_inserted"] += result.get("inserted", 0)
                stats["total_updated"] += result.get("updated", 0)
        
        self.last_sync_time = int(time.time())
        self.last_sync_stats = stats
        
        logger.info(f"✅ 同步完成: {stats}")
        return stats
    
    def start_auto_sync(self):
        """启动自动同步线程"""
        if not PYMONGO_AVAILABLE or not self.mongo_client:
            logger.warning("⚠️ MongoDB未连接，自动同步已禁用")
            return
        
        if self.running:
            logger.info("自动同步已在运行中")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info(f"✅ 自动同步已启动，间隔: {self.sync_interval}秒")
    
    def _auto_sync_loop(self):
        """自动同步循环"""
        while self.running:
            try:
                self.sync_all()
            except Exception as e:
                logger.error(f"自动同步出错: {e}")
            
            time.sleep(self.sync_interval)
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("自动同步已停止")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return {
            "mongodb_connected": self.mongo_client is not None,
            "mongodb_uri": self.mongo_uri,
            "sqlite_path": self.sqlite_path,
            "last_sync_time": self.last_sync_time,
            "last_sync_stats": self.last_sync_stats,
            "auto_sync_running": self.running,
            "sync_interval": self.sync_interval,
        }
    
    def close(self):
        """关闭连接"""
        self.stop_auto_sync()
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB连接已关闭")


class MongoSQLBackupManager:
    """MongoSQL备份管理器"""
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "backup"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.sync = None
    
    def create_backup(self, db_name: str = "mtscos_new.db") -> str:
        """创建SQLite数据库备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{db_name}.backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        source = os.path.join(self.data_dir, db_name)
        shutil.copy2(source, backup_path)
        
        # 同时创建一份latest备份
        latest_path = os.path.join(self.backup_dir, f"{db_name}.latest")
        shutil.copy2(source, latest_path)
        
        logger.info(f"✅ 备份已创建: {backup_path}")
        return backup_path
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        if os.path.exists(self.backup_dir):
            for f in os.listdir(self.backup_dir):
                if f.endswith(".db") or f.endswith(".backup_"):
                    path = os.path.join(self.backup_dir, f)
                    stat = os.stat(path)
                    backups.append({
                        "name": f,
                        "path": path,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        if not os.path.exists(backup_path):
            logger.error(f"备份文件不存在: {backup_name}")
            return False
        
        db_path = os.path.join(self.data_dir, "mtscos_new.db")
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"✅ 备份已恢复: {backup_name}")
        return True
    
    def init_sync(self, mongo_uri: str = None) -> MongoSQLSync:
        """初始化MongoSQL同步"""
        from database_schema import SCHEMA
        
        db_path = os.path.join(self.data_dir, "mtscos_new.db")
        
        self.sync = MongoSQLSync(
            sqlite_path=db_path,
            mongo_uri=mongo_uri or "mongodb://localhost:27017",
            mongo_db="mtscos",
            sync_interval=60
        )
        
        return self.sync


# 全局实例
_mongo_sql = None

def get_mongo_sql() -> Optional[MongoSQLSync]:
    """获取全局MongoSQL实例"""
    global _mongo_sql
    return _mongo_sql

def init_mongo_sql(mongo_uri: str = None) -> MongoSQLSync:
    """初始化全局MongoSQL实例"""
    global _mongo_sql
    
    backup_manager = MongoSQLBackupManager()
    _mongo_sql = backup_manager.init_sync(mongo_uri)
    
    return _mongo_sql

def start_mongo_sql_sync(mongo_uri: str = None):
    """启动MongoSQL同步"""
    global _mongo_sql
    
    if _mongo_sql is None:
        _mongo_sql = init_mongo_sql(mongo_uri)
    
    if _mongo_sql.mongo_client:
        _mongo_sql.start_auto_sync()
        return True
    else:
        logger.warning("MongoDB未连接，无法启动同步")
        return False


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║           MongoSQL - SQLite/MongoDB 同步工具             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 初始化MongoSQL
    mongo_sql = init_mongo_sql()
    
    # 显示状态
    status = mongo_sql.get_sync_status()
    print(f"""
📊 MongoSQL状态:
  - MongoDB连接: {'✅ 已连接' if status['mongodb_connected'] else '❌ 未连接'}
  - SQLite路径: {status['sqlite_path']}
  - 自动同步: {'✅ 运行中' if status['auto_sync_running'] else '❌ 已停止'}
    """)
    
    if status['mongodb_connected']:
        # 执行一次同步
        print("📝 执行首次同步...")
        stats = mongo_sql.sync_all()
        print(f"✅ 同步完成: {stats}")
        
        # 启动自动同步
        print("🔄 启动自动同步...")
        mongo_sql.start_auto_sync()
    else:
        print("""
💡 提示:
   如果需要启用MongoDB同步，请:
   1. 安装并启动MongoDB服务
   2. 设置 MONGODB_URI 环境变量（可选）
   3. 重新运行此脚本
        """)
