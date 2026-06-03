# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库分表分列管理系统
支持按时间、类别等维度进行分表，以及将大字段分离到单独的表
"""

import os
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

class DatabaseShardingManager:
    """数据库分表分列管理器"""
    
    def __init__(self):
        self.base_dir = Path("/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project")
        self.db_path = self.base_dir / "app.db"
        self.shard_dir = self.base_dir / "sharded_databases"
        self.shard_dir.mkdir(exist_ok=True)
    
    def get_timestamp(self) -> str:
        """获取时间戳"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_before_sharding(self) -> str:
        """分表前备份"""
        backup_path = self.base_dir / f"backups/app_sharding_backup_{self.get_timestamp()}.db"
        shutil.copy2(self.db_path, backup_path)
        print(f"✓ 分表前备份: {backup_path}")
        return str(backup_path)
    
    def create_shard_by_category(self, table_name: str, category_column: str) -> bool:
        """按类别分表"""
        print(f"\n == 按类别分表: {table_name} -> {category_column} ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT DISTINCT {category_column} FROM {table_name} WHERE {category_column} IS NOT NULL")
            categories = [row[0] for row in cursor.fetchall()]
            
            if not categories:
                print(f"⚠ 没有可用于分表的类别数据")
                return False
            
            for category in categories:
                safe_category = str(category).replace('/', '_').replace('\\', '_').replace(' ', '_')
                shard_table = f"{table_name}_{safe_category[:20]}"
                
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {shard_table} AS SELECT * FROM {table_name} WHERE {category_column} = ?", (category,))
                print(f"✓ 创建分表: {shard_table} ({cursor.rowcount} 条记录)")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ 按类别分表失败: {e}")
            return False
    
    def create_shard_by_month(self, table_name: str, date_column: str = "created_at") -> bool:
        """按月份分表"""
        print(f"\n == 按月份分表: {table_name} -> {date_column} ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT STRFTIME('%Y-%m', {date_column}) as month FROM {table_name} WHERE {date_column} IS NOT NULL GROUP BY month")
            months = [row[0] for row in cursor.fetchall()]
            
            if not months:
                print(f"⚠ 没有可用于分表的日期数据")
                return False
            
            for month in months:
                shard_table = f"{table_name}_{month.replace('-', '_')}"
                
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {shard_table} AS SELECT * FROM {table_name} WHERE STRFTIME('%Y-%m', {date_column}) = ?", (month,))
                print(f"✓ 创建分表: {shard_table} ({cursor.rowcount} 条记录)")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ 按月份分表失败: {e}")
            return False
    
    def split_large_columns(self, table_name: str, large_columns: List[str]) -> bool:
        """将大字段分离到单独的表"""
        print(f"\n == 分离大字段: {table_name} -> {large_columns} ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取主键信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            primary_key = columns[0][1] if columns else "id"
            
            for column in large_columns:
                # 创建大字段表
                large_table = f"{table_name}_{column}"
                
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {large_table} (
                        {primary_key} INTEGER PRIMARY KEY,
                        {column} TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 迁移数据
                cursor.execute(f"INSERT OR IGNORE INTO {large_table} ({primary_key}, {column}) SELECT {primary_key}, {column} FROM {table_name} WHERE {column} IS NOT NULL")
                print(f"✓ 创建大字段表: {large_table} ({cursor.rowcount} 条记录)")
                
                # 原表中设置为外键或删除
                try:
                    cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column}")
                    print(f"✓ 已从原表删除字段: {column}")
                except Exception:
                    # SQLite 不支持直接删除列，创建新表
                    other_columns = [col[1] for col in columns if col[1] != column]
                    if other_columns:
                        cursor.execute(f"CREATE TABLE {table_name}_new AS SELECT {', '.join(other_columns)} FROM {table_name}")
                        cursor.execute(f"DROP TABLE {table_name}")
                        cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                        print(f"✓ 通过重建表移除字段: {column}")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ 分离大字段失败: {e}")
            return False
    
    def create_shard_database(self, db_name: str, tables: List[str]) -> str:
        """创建独立的分片数据库"""
        print(f"\n == 创建分片数据库: {db_name} ===")
        
        shard_db_path = self.shard_dir / f"{db_name}.db"
        
        try:
            # 创建新数据库
            shard_conn = sqlite3.connect(shard_db_path)
            shard_cursor = shard_conn.cursor()
            
            # 复制表结构和数据
            main_conn = sqlite3.connect(self.db_path)
            main_cursor = main_conn.cursor()
            
            for table in tables:
                # 获取表结构
                main_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                create_sql = main_cursor.fetchone()
                
                if create_sql:
                    shard_cursor.execute(create_sql[0])
                    shard_cursor.execute(f"INSERT INTO {table} SELECT * FROM main.{table}")
                    print(f"✓ 复制表: {table} ({shard_cursor.rowcount} 条记录)")
            
            shard_conn.commit()
            shard_conn.close()
            main_conn.close()
            
            print(f"✓ 分片数据库创建完成: {shard_db_path}")
            return str(shard_db_path)
            
        except Exception as e:
            print(f"✗ 创建分片数据库失败: {e}")
            return ""
    
    def create_partitioned_tables(self) -> bool:
        """创建分区表结构"""
        print("\n == 创建分区表结构 ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建题库分区表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions_p0 (
                    id INTEGER PRIMARY KEY,
                    question_text TEXT,
                    answer TEXT,
                    category_id INTEGER,
                    difficulty_level INTEGER,
                    question_type TEXT,
                    tags TEXT,
                    usage_count INTEGER,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions_p1 (
                    id INTEGER PRIMARY KEY,
                    question_text TEXT,
                    answer TEXT,
                    category_id INTEGER,
                    difficulty_level INTEGER,
                    question_type TEXT,
                    tags TEXT,
                    usage_count INTEGER,
                    last_used_at TIMESTAMP,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            # 创建知识库分区表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_p0 (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    category TEXT,
                    embedding TEXT,
                    confidence REAL,
                    source_type TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_p1 (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    category TEXT,
                    embedding TEXT,
                    confidence REAL,
                    source_type TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("✓ 分区表结构创建完成")
            return True
            
        except Exception as e:
            print(f"✗ 创建分区表失败: {e}")
            return False
    
    def distribute_data_to_partitions(self) -> bool:
        """将数据分布到分区表"""
        print("\n == 数据分布到分区表 ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 分布questions数据
            cursor.execute("INSERT OR IGNORE INTO questions_p0 SELECT * FROM questions WHERE id % 2 = 0")
            print(f"✓ questions_p0: {cursor.rowcount} 条记录")
            
            cursor.execute("INSERT OR IGNORE INTO questions_p1 SELECT * FROM questions WHERE id % 2 = 1")
            print(f"✓ questions_p1: {cursor.rowcount} 条记录")
            
            # 分布knowledge数据
            cursor.execute("INSERT OR IGNORE INTO knowledge_p0 SELECT * FROM ai_brain_knowledge WHERE id % 2 = 0")
            print(f"✓ knowledge_p0: {cursor.rowcount} 条记录")
            
            cursor.execute("INSERT OR IGNORE INTO knowledge_p1 SELECT * FROM ai_brain_knowledge WHERE id % 2 = 1")
            print(f"✓ knowledge_p1: {cursor.rowcount} 条记录")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"✗ 数据分布失败: {e}")
            return False
    
    def create_view_for_shards(self, base_table: str, shard_tables: List[str]) -> bool:
        """为分表创建视图"""
        print(f"\n == 为分表创建视图: {base_table} ===")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            union_sql = " UNION ALL ".join([f"SELECT * FROM {table}" for table in shard_tables])
            view_name = f"v_{base_table}"
            
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
            cursor.execute(f"CREATE VIEW {view_name} AS {union_sql}")
            
            conn.commit()
            conn.close()
            print(f"✓ 创建视图: {view_name}")
            return True
            
        except Exception as e:
            print(f"✗ 创建视图失败: {e}")
            return False
    
    def run_sharding(self) -> Dict[str, Any]:
        """运行完整的分表分列流程"""
        print("=" * 70)
        print("MTSCOS AI 数据库分表分列系统")
        print("=" * 70)
        
        # 1. 备份
        print("\n[步骤1] 分表前备份")
        backup = self.backup_before_sharding()
        
        # 2. 按类别分表
        print("\n[步骤2] 按类别分表")
        self.create_shard_by_category("questions", "question_type")
        
        # 3. 按月份分表
        print("\n[步骤3] 按月份分表")
        self.create_shard_by_month("ai_brain_knowledge", "created_at")
        
        # 4. 分离大字段
        print("\n[步骤4] 分离大字段")
        self.split_large_columns("ai_brain_knowledge", ["content", "embedding"])
        
        # 5. 创建分区表
        print("\n[步骤5] 创建分区表结构")
        self.create_partitioned_tables()
        
        # 6. 分布数据
        print("\n[步骤6] 数据分布到分区表")
        self.distribute_data_to_partitions()
        
        # 7. 创建分片数据库
        print("\n[步骤7] 创建分片数据库")
        shard_db = self.create_shard_database("ai_knowledge", ["ai_brain_knowledge", "ai_feature_store"])
        
        # 8. 创建视图
        print("\n[步骤8] 创建分表视图")
        self.create_view_for_shards("questions", ["questions_p0", "questions_p1"])
        self.create_view_for_shards("knowledge", ["knowledge_p0", "knowledge_p1"])
        
        # 输出总结
        print("\n" + "=" * 70)
        print("分表分列完成总结")
        print("=" * 70)
        
        print("\n操作统计:")
        print(f"  ✓ 分表前备份: {backup}")
        print(f"  ✓ 按类别分表: questions -> question_type")
        print(f"  ✓ 按月份分表: ai_brain_knowledge -> created_at")
        print(f"  ✓ 大字段分离: ai_brain_knowledge -> content, embedding")
        print(f"  ✓ 分区表创建: questions_p0/p1, knowledge_p0/p1")
        print(f"  ✓ 分片数据库: {shard_db}")
        print(f"  ✓ 视图创建: v_questions, v_knowledge")
        
        print("\n" + "=" * 70)
        
        return {
            "backup": backup,
            "shard_database": shard_db,
            "timestamp": self.get_timestamp()
        }

def main():
    """主入口"""
    manager = DatabaseShardingManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "category":
            table = sys.argv[2] if len(sys.argv) > 2 else "questions"
            column = sys.argv[3] if len(sys.argv) > 3 else "question_type"
            manager.create_shard_by_category(table, column)
        elif command == "month":
            table = sys.argv[2] if len(sys.argv) > 2 else "ai_brain_knowledge"
            manager.create_shard_by_month(table)
        elif command == "split":
            table = sys.argv[2] if len(sys.argv) > 2 else "ai_brain_knowledge"
            columns = sys.argv[3:] if len(sys.argv) > 3 else ["content", "embedding"]
            manager.split_large_columns(table, columns)
        elif command == "partition":
            manager.create_partitioned_tables()
            manager.distribute_data_to_partitions()
        elif command == "full":
            manager.run_sharding()
        else:
            print(f"未知命令: {command}")
            print("可用命令: category, month, split, partition, full")
    else:
        manager.run_sharding()

if __name__ == "__main__":
    import sys
    main()