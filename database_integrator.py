#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库整合脚本 - 分析、整合、去重并备份"""

import sqlite3
import os
# JSON import removed - using database
import hashlib
from datetime import datetime

class DatabaseIntegrator:
    def __init__(self, db_path='app.db'):
        self.db_path = db_path
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def get_all_tables(self):
        """获取所有表名"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def get_table_schema(self, table_name):
        """获取表结构"""
        cursor = conn.cursor()
        schema = cursor.fetchall()
        conn.close()
        return schema
    def get_table_row_count(self, table_name):
        """获取表行数"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        conn.close()
        return count

    def analyze_tables(self):
        tables = self.get_all_tables()
        table_info = []

        for table in tables:
            schema = self.get_table_schema(table)
            row_count = self.get_table_row_count(table)
            columns = [col[1] for col in schema]

            table_info.append({
                'name': table,
                'row_count': row_count,
                'columns': columns,
                'column_count': len(columns),
                'is_temp': table.startswith('t_'),
                'is_backup': table.endswith('_backup') or table.endswith('_bak')
            })

        return table_info

    def find_duplicate_tables(self, table_info):
        """查找可能重复的表"""
        duplicates = []

        # 根据列名相似性查找重复表
        for i, table1 in enumerate(table_info):
            for j, table2 in enumerate(table_info):
                if i >= j:
                    continue

                cols1 = set(table1['columns'])
                cols2 = set(table2['columns'])
                similarity = len(cols1 & cols2) / max(len(cols1), len(cols2))

                if similarity > 0.7:  # 超过70%的列相同
                    duplicates.append({
                        'table1': table1['name'],
                        'table2': table2['name'],
                        'similarity': round(similarity * 100, 2),
                        'common_columns': list(cols1 & cols2)
                    })

        return duplicates

    def backup_table(self, table_name):
        """备份单个表"""
        backup_file = os.path.join(self.backup_dir, f'{table_name}_{timestamp}.sql')

        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Table: {table_name}\n")
            f.write(f"-- Backup time: {datetime.now()}\n")
            f.write(f"-- Row count: {len(rows)}\n")
            f.write("\n")

            for i, row in enumerate(rows):
                values = []
                for val in row:
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        values.append(f"'{escaped_val}'")
                    else:
                        values.append(str(val))

                line = f"  ({', '.join(values)})"
                if i < len(rows) - 1:
                    line += ","
                f.write(line + "\n")

        conn.close()
        return backup_file

    def backup_database(self):
        """备份整个数据库"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_conn = sqlite3.connect(backup_file)
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()

        return backup_file

    def remove_duplicate_rows(self, table_name, unique_columns):
        cursor = conn.cursor()
        # 创建临时表存储唯一记录
        cursor.execute(f"CREATE TEMP TABLE temp_unique AS SELECT DISTINCT * FROM {table_name}")

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        original_count = cursor.fetchone()[0]

        # 清空原表
        cursor.execute(f"DELETE FROM {table_name}")
        # 插入唯一记录
        cursor.execute(f"INSERT INTO {table_name} SELECT * FROM temp_unique")

        # 获取去重后的行数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        new_count = cursor.fetchone()[0]

        conn.commit()

        removed_count = original_count - new_count
        return {'original': original_count, 'remaining': new_count, 'removed': removed_count}

    def merge_tables(self, source_table, target_table, key_columns):
        """合并两个表"""
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {source_table}")

        cursor.execute(f"PRAGMA table_info({target_table})")
        columns = [col[1] for col in cursor.fetchall()]
        column_names = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])

        merged_count = 0
        skipped_count = 0

        for row in rows:
            try:
                cursor.execute(f"INSERT OR IGNORE INTO {target_table} ({column_names}) VALUES ({placeholders})", row)
                if cursor.rowcount > 0:
                    merged_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                skipped_count += 1

        conn.close()

        return {'merged': merged_count, 'skipped': skipped_count}

        """删除空的临时表"""
        cursor = conn.cursor()
        dropped = []

        for table in table_info:
            if table['is_temp'] and table['row_count'] == 0:
                dropped.append(table['name'])
        conn.commit()
        conn.close()
        return dropped

    def run_integration(self):
        print("="*70)
        print("              数据库整合与去重脚本")
        print("="*70)

        print("\n[1/5] 分析数据库表结构...")

        for table in table_info[:5]:
            print(f"    - {table['name']}: {table['row_count']} 行, {table['column_count']} 列")
        if len(table_info) > 5:
            print(f"    ... 还有 {len(table_info) - 5} 个表")

        # 2. 查找重复表
        print("\n[2/5] 查找重复表...")
        duplicates = self.find_duplicate_tables(table_info)

        if duplicates:
            print(f"  发现 {len(duplicates)} 对可能重复的表:")
            for dup in duplicates:
                print(f"    - {dup['table1']} ↔ {dup['table2']} (相似度: {dup['similarity']}%)")
        else:

        # 3. 备份数据库
        print("\n[3/5] 备份数据库...")
        pass
        backup_file = self.backup_database()
        print(f"  数据库已备份到: {backup_file}")

        # 4. 处理重复数据
        print("\n[4/5] 处理重复数据...")

        # 合并 questions 和 question_bank 到 questions 主表
        questions_count = self.get_table_row_count('questions')
        qb_count = self.get_table_row_count('question_bank')
        result = self.merge_tables('question_bank', 'questions', ['content', 'answer'])
        print(f"    合并结果: {result['merged']} 条新增, {result['skipped']} 条跳过")

        # 清理 user_backup 到 user 表
        print("  合并 user_backup -> user...")
        result = self.merge_tables('user_backup', 'user', ['username', 'email'])
        print(f"    合并结果: {result['merged']} 条新增, {result['skipped']} 条跳过")

        # 删除 questions 表中的重复行
        print("  删除 questions 表重复行...")
        result = self.remove_duplicate_rows('questions', ['content', 'answer'])
        print(f"    去重结果: 删除 {result['removed']} 条重复行")
        # 删除 user 表中的重复行
        print("  删除 user 表重复行...")
        result = self.remove_duplicate_rows('user', ['username', 'email'])
        print(f"    去重结果: 删除 {result['removed']} 条重复行")

        # 删除空的临时表
        print("\n[5/5] 清理空临时表...")
        dropped = self.drop_empty_temp_tables(table_info)
        if dropped:
            print(f"  删除了 {len(dropped)} 个空临时表")
        else:
            print("  没有空临时表需要删除")

        print("\n" + "="*70)
        print("              数据库整合完成")
        print("="*70)

        # 生成整合报告
        report = self.generate_report(table_info, duplicates)
        print(f"\n整合报告已保存到: {report}")

        return True

    def generate_report(self, table_info, duplicates):
        """生成整合报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(table_info),
            'duplicate_pairs': len(duplicates),
            'tables': table_info,
            'duplicates': duplicates,
            'summary': {
                'total_rows': sum(t['row_count'] for t in table_info),
                'temp_tables': sum(1 for t in table_info if t['is_temp']),
                'backup_tables': sum(1 for t in table_info if t['is_backup'])
            }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report_file

def main():
    integrator = DatabaseIntegrator()
    integrator.run_integration()

    main()
