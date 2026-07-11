import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""数据库深度维护工具 - 分析、清理、优化数据库表"""
import os
import sqlite3
from datetime import datetime
import sys

# 数据库文件列表
DB_FILES = [
    'app.db',
    'app_backup.db', 
    'backup.db',
    'color_schemes.db',
    'database.db',
    'dev.db',
    'mtscos.db',
    'primary.db',
    'system.db'
]

def get_tables(db_path):
    """获取数据库中的所有表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        print(f"❌ 读取 {db_path} 失败: {e}")
        return []

def get_table_info(db_path, table_name):
    """获取表结构信息"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        conn.close()
        return {
            'columns': columns,
            'row_count': row_count
        }
    except Exception as e:
        return {'columns': [], 'row_count': 0}

def analyze_databases():
    """分析所有数据库"""
    all_tables = {}
    db_info = {}
    
    for db_file in DB_FILES:
        if os.path.exists(db_file):
            tables = get_tables(db_file)
            db_info[db_file] = {
                'tables': tables,
                'table_count': len(tables)
            }
            
            # 统计每个表出现的次数
            for table in tables:
                if table not in all_tables:
                    all_tables[table] = []
                all_tables[table].append(db_file)
    
    return db_info, all_tables

def generate_report(db_info, all_tables):
    """生成维护报告"""
    report = []
    report.append("=" * 80)
    report.append("数据库深度维护报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # 数据库概览
    report.append("\n📊 数据库文件概览:")
    total_tables = sum(info['table_count'] for info in db_info.values())
    for db_file, info in db_info.items():
        report.append(f"  - {db_file}: {info['table_count']} 张表")
    report.append(f"\n  总计: {len(db_info)} 个数据库文件, {total_tables} 张表")
    
    # 重复表分析
    report.append("\n🔍 重复表分析:")
    duplicate_tables = {table: dbs for table, dbs in all_tables.items() if len(dbs) > 1}
    if duplicate_tables:
        for table, dbs in duplicate_tables.items():
            report.append(f"  ⚠️ {table}: 在 {len(dbs)} 个数据库中重复")
            report.append(f"     位置: {', '.join(dbs)}")
    else:
        report.append("  ✅ 无重复表")
    
    # 空表分析
    report.append("\n📭 空表分析:")
    empty_tables = []
    for db_file, info in db_info.items():
        for table in info['tables']:
            table_info = get_table_info(db_file, table)
            if table_info['row_count'] == 0:
                empty_tables.append(f"{db_file}.{table}")
    
    if empty_tables:
        for empty_table in empty_tables:
            report.append(f"  ⚠️ {empty_table}: 0 条记录")
    else:
        report.append("  ✅ 无空表")
    
    # 表大小分析
    report.append("\n📈 表数据量分析:")
    large_tables = []
    for db_file, info in db_info.items():
        for table in info['tables']:
            table_info = get_table_info(db_file, table)
            if table_info['row_count'] > 1000:
                large_tables.append((db_file, table, table_info['row_count']))
    
    if large_tables:
        for db_file, table, count in sorted(large_tables, key=lambda x: x[2], reverse=True):
            report.append(f"  📦 {db_file}.{table}: {count:,} 条记录")
    else:
        report.append("  ✅ 无大型表(>1000条记录)")
    
    # AI建议
    report.append("\n🤖 AI维护建议:")
    report.append("  1. 合并重复表到主数据库 app.db")
    report.append("  2. 删除空表以节省空间")
    report.append("  3. 定期备份大型表")
    report.append("  4. 清理不再使用的历史数据库文件")
    
    return '\n'.join(report)

def execute_maintenance():
    """执行数据库维护"""
    db_info, all_tables = analyze_databases()
    report = generate_report(db_info, all_tables)
    
    # 打印报告
    print(report)
    
    # 保存报告
    report_file = f"database_maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"\n📝 报告已保存至: {report_file}")
    
    return report

if __name__ == '__main__':
    execute_maintenance()
