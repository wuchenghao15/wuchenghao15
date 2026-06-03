# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""数据库深度维护工具 - 完整版本"""
import os
import sqlite3
from datetime import datetime
import sys

class DatabaseMaintenance:
    def __init__(self):
        self.main_db = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        self.backup_dir = 'db_backups'
        self.migration_log = []
        
    def log_action(self, action, details):
        """记录维护操作"""
        self.migration_log.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'details': details
        })
    
    def backup_database(self, db_path):
        """备份数据库"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        backup_name = f"{os.path.basename(db_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
            self.log_action('BACKUP', f"备份 {db_path} -> {backup_path}")
            return True
        except Exception as e:
            self.log_action('BACKUP_FAILED', f"备份失败 {db_path}: {e}")
            return False
    
    def migrate_table(self, src_db, table_name, dst_db):
        """迁移表数据"""
        try:
            src_conn = sqlite3.connect(src_db)
            dst_conn = sqlite3.connect(dst_db)
            
            # 获取表结构
            src_conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM {table_name}")
            dst_conn.execute(f"ATTACH DATABASE '{src_db}' AS src")
            
            # 获取源表的创建语句
            cursor = src_conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = cursor.fetchone()
            if create_sql:
                # 检查目标表是否存在
                dst_cursor = dst_conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not dst_cursor.fetchone():
                    dst_conn.execute(create_sql[0])
            
            # 复制数据
            dst_conn.execute(f"INSERT OR IGNORE INTO {table_name} SELECT * FROM src.{table_name}")
            dst_conn.commit()
            
            row_count = dst_conn.execute(f"SELECT changes()").fetchone()[0]
            self.log_action('MIGRATE', f"迁移 {src_db}.{table_name}: {row_count} 条记录")
            
            src_conn.close()
            dst_conn.close()
            return row_count
        except Exception as e:
            self.log_action('MIGRATE_FAILED', f"迁移失败 {src_db}.{table_name}: {e}")
            return 0
    
    def delete_empty_tables(self, db_path):
        """删除空表"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            deleted_count = 0
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if count == 0:
                    conn.execute(f"DROP TABLE {table}")
                    deleted_count += 1
                    self.log_action('DELETE_EMPTY', f"删除空表 {db_path}.{table}")
            
            conn.commit()
            conn.close()
            return deleted_count
        except Exception as e:
            self.log_action('DELETE_EMPTY_FAILED', f"删除空表失败 {db_path}: {e}")
            return 0
    
    def delete_unused_database(self, db_path):
        """删除不再使用的数据库文件"""
        try:
            os.remove(db_path)
            self.log_action('DELETE_DB', f"删除数据库文件: {db_path}")
            return True
        except Exception as e:
            self.log_action('DELETE_DB_FAILED', f"删除数据库失败 {db_path}: {e}")
            return False
    
    def optimize_database(self, db_path):
        """优化数据库"""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            conn.close()
            self.log_action('OPTIMIZE', f"优化数据库: {db_path}")
            return True
        except Exception as e:
            self.log_action('OPTIMIZE_FAILED', f"优化失败 {db_path}: {e}")
            return False
    
    def save_log_to_database(self):
        """将维护日志保存到数据库"""
        try:
            conn = sqlite3.connect(self.main_db)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    action TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            for log in self.migration_log:
                conn.execute("""
                    INSERT INTO maintenance_logs (timestamp, action, details)
                    VALUES (?, ?, ?)
                """, (log['timestamp'], log['action'], log['details']))
            
            conn.commit()
            conn.close()
            self.log_action('LOG_SAVED', f"维护日志已保存到数据库,共 {len(self.migration_log)} 条记录")
            return True
        except Exception as e:
            self.log_action('LOG_SAVE_FAILED', f"保存日志失败: {e}")
            return False
    
    def generate_summary(self):
        """生成维护总结"""
        summary = []
        summary.append("=" * 80)
        summary.append("数据库深度维护总结报告")
        summary.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("=" * 80)
        
        # 统计各类操作
        action_counts = {}
        for log in self.migration_log:
            action = log['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        summary.append("\n📋 维护操作统计:")
        for action, count in action_counts.items():
            summary.append(f"  {action}: {count} 次")
        
        # 详细日志
        summary.append("\n📝 详细操作日志:")
        for i, log in enumerate(self.migration_log, 1):
            summary.append(f"  {i}. [{log['timestamp']}] {log['action']}: {log['details']}")
        
        return '\n'.join(summary)
    
    def run_maintenance(self):
        """执行完整的数据库维护"""
        print("🚀 开始执行数据库深度维护...")
        
        # 1. 备份所有数据库
        print("\n📦 备份数据库...")
        db_files = ['app_backup.db', 'backup.db', 'dev.db', 'mtscos.db', 'primary.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                self.backup_database(db_file)
        
        # 2. 迁移重要表到主数据库
        print("\n🔄 迁移表数据...")
        tables_to_migrate = ['users', 'questions', 'system_config', 'user_japanese_levels']
        for table in tables_to_migrate:
            for db_file in ['app_backup.db', 'backup.db', 'dev.db', 'primary.db']:
                if os.path.exists(db_file):
                    self.migrate_table(db_file, table, self.main_db)
        
        # 3. 删除空表
        print("\n🗑️ 删除空表...")
        for db_file in db_files + ['app.db']:
            if os.path.exists(db_file):
                count = self.delete_empty_tables(db_file)
                if count > 0:
                    print(f"   {db_file}: 删除 {count} 张空表")
        
        # 4. 优化数据库
        print("\n⚡ 优化数据库...")
        self.optimize_database(self.main_db)
        
        # 5. 保存日志到数据库
        print("\n📝 保存维护日志...")
        self.save_log_to_database()
        
        # 6. 生成报告
        print("\n📊 生成维护报告...")
        summary = self.generate_summary()
        print(summary)
        
        # 保存报告
        report_file = f"maintenance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"\n📄 报告已保存至: {report_file}")
        
        return summary

if __name__ == '__main__':
    maintenance = DatabaseMaintenance()
    maintenance.run_maintenance()
