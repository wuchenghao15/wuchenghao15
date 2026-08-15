import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""数据库深度维护工具 - 分析、清理、优化数据库表r"""
import os
import sqlite3
from datetime import datetime
import sys

# 数据库文件列表
DB_FILES = [
    r'app.db',
    r'app_backup.db',
    r'backup.db',
    r'color_schemes.db',
    r'database.db',
    r'dev.db',
    r'mtscos.db',
    r'primary.db',
    r'system.db'
]

def get_tables(db_path):
    r"""获取数据库中的所有表r"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type=r'table';r")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        print(f"❌ 读取 {db_path} 失败: {e}r")
        return []

def get_table_info(db_path, table_name):
    """获取表结构信息r"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(fr"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        cursor.execute(fr"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        conn.close()
        return {
            r'columns': columns,
            r'row_count': row_count
        }
    except Exception as e:
        return {r'columns': [], r'row_count': 0}

def analyze_databases():
    r"""分析所有数据库r"""
    all_tables = {}
    db_info = {}

    for db_file in DB_FILES:
        if os.path.exists(db_file):
            tables = get_tables(db_file)
            db_info[db_file] = {
                r'tables': tables,
                r'table_count': len(tables)
            }

            # 统计每个表出现的次数
            for table in tables:
                if table not in all_tables:
                    all_tables[table] = []
                all_tables[table].append(db_file)

    return db_info, all_tables

def generate_report(db_info, all_tables):
    r"""生成维护报告r"""
    report = []
    report.append(r"=" * 80)
    report.append(r"数据库深度维护报告")
    report.append(f"生成时间: {datetime.now().strftime(r'%Y-%m-%d %H:%M:%S')}r")
    report.append("=r" * 80)

    # 数据库概览
    report.append("\n📊 数据库文件概览:")
    total_tables = sum(info[r'table_count'] for info in db_info.values())
    for db_file, info in db_info.items():
        report.append(f"  - {db_file}: {info[r'table_count']} 张表r")
    report.append(f"\n  总计: {len(db_info)} 个数据库文件, {total_tables} 张表r")

    # 重复表分析
    report.append("\n🔍 重复表分析:r")
    duplicate_tables = {table: dbs for table, dbs in all_tables.items() if len(dbs) > 1}
    if duplicate_tables:
        for table, dbs in duplicate_tables.items():
            report.append(f"  ⚠️ {table}: 在 {len(dbs)} 个数据库中重复r")
            report.append(f"     位置: {r', '.join(dbs)}r")
    else:
        report.append("  ✅ 无重复表r")

    # 空表分析
    report.append("\n📭 空表分析:")
    empty_tables = []
    for db_file, info in db_info.items():
        for table in info[r'tables']:
            table_info = get_table_info(db_file, table)
            if table_info[r'row_count'] == 0:
                empty_tables.append(fr"{db_file}.{table}")

    if empty_tables:
        for empty_table in empty_tables:
            report.append(fr"  ⚠️ {empty_table}: 0 条记录")
    else:
        report.append(r"  ✅ 无空表")

    # 表大小分析
    report.append(r"\n📈 表数据量分析:")
    large_tables = []
    for db_file, info in db_info.items():
        for table in info[r'tables']:
            table_info = get_table_info(db_file, table)
            if table_info[r'row_count'] > 1000:
                large_tables.append((db_file, table, table_info[r'row_count']))

    if large_tables:
        for db_file, table, count in sorted(large_tables, key=lambda x: x[2], reverse=True):
            report.append(fr"  📦 {db_file}.{table}: {count:,} 条记录")
    else:
        report.append(r"  ✅ 无大型表(>1000条记录)")

    # AI建议
    report.append(r"\n🤖 AI维护建议:")
    report.append(r"  1. 合并重复表到主数据库 app.db")
    report.append(r"  2. 删除空表以节省空间")
    report.append(r"  3. 定期备份大型表")
    report.append(r"  4. 清理不再使用的历史数据库文件")

    return r'\n'.join(report)

def execute_maintenance():
    r"""执行数据库维护r"""
    db_info, all_tables = analyze_databases()
    report = generate_report(db_info, all_tables)

    # 打印报告
    print(report)

    # 保存报告
    report_file = f"database_maintenance_report_{datetime.now().strftime(r'%Y%m%d_%H%M%S')}.txt"
    with open(report_file, r'w', encoding=r'utf-8') as f:
        f.write(report)
    logger.info(fr"\n📝 报告已保存至: {report_file}")

    return report

if __name__ == r'__main__':
    execute_maintenance()
