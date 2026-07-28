#!/usr/bin/env python3
"""
AI员工数量上传同步数据库 - 简化版
直接测试同步功能，不依赖有语法错误的文件
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_engines.ai_employee_sync import AIEmployeeSync, ensure_employee_table

AI_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases', 'ai.db')

def get_db_connection():
    conn = sqlite3.connect(AI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def print_section(title):
    print('')
    print('=' * 70)
    print(f' {title}')
    print('=' * 70)

class SimpleEmployee:
    """简化的员工对象"""
    def __init__(self, employee_id, name, emp_type='general', level=1, status='active'):
        self.employee_id = employee_id
        self.name = name
        self.type = emp_type
        self.level = level
        self.status = status
        self.title = ''
        self.description = ''
        self.category = ''
        self.capabilities = []
        self.efficiency = 0
        self.workload = 0
        self.knowledge_domain = ''
        self.personality_type = ''
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.performance_score = 80.0 + level * 2

def get_all_employees_from_db():
    """从数据库获取所有员工"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT employee_id, name, employee_type, level FROM ai_employees')
    rows = cursor.fetchall()
    conn.close()
    employees = {}
    for row in rows:
        employees[row['employee_id']] = SimpleEmployee(
            row['employee_id'], row['name'], row['employee_type'], row['level']
        )
    return employees

def main():
    print_section('AI员工数量上传同步数据库')
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'目标数据库: {AI_DB_PATH}')
    
    print_section('1. 初始化数据库表')
    ensure_employee_table()
    print('   ✓ 数据库表检查完成')
    
    print_section('2. 从数据库读取现有员工')
    employees = get_all_employees_from_db()
    print(f'   ✓ 数据库中共有 {len(employees)} 个AI员工')
    
    print_section('3. 同步员工到数据库')
    sync_manager = AIEmployeeSync()
    sync_result = sync_manager.sync_all_employees(employees)
    
    print(f'   同步结果:')
    print(f'     总数: {sync_result["total"]}')
    print(f'     新增: {sync_result["created"]}')
    print(f'     更新: {sync_result["updated"]}')
    print(f'     失败: {sync_result["failed"]}')
    
    if sync_result['errors']:
        print(f'   失败详情(前5个):')
        for error in sync_result['errors'][:5]:
            print(f'     - {error["employee_id"]}: {error["error"]}')
    
    print_section('4. 同步统计信息')
    stats = sync_manager.get_employee_stats(employees)
    
    print(f'   数据库统计:')
    print(f'     总数: {stats.get("db_total", 0)}')
    print(f'     活跃状态: {stats.get("db_active", 0)}')
    print(f'     非活跃状态: {stats.get("db_inactive", 0)}')
    
    print(f'   内存统计:')
    print(f'     总数: {stats.get("memory_total", 0)}')
    
    print(f'   数据库按类型统计:')
    for emp_type, count in sorted(stats.get("db_by_type", {}).items()):
        print(f'     {emp_type}: {count}')
    
    print(f'   内存按类型统计:')
    for emp_type, count in sorted(stats.get("memory_by_type", {}).items()):
        print(f'     {emp_type}: {count}')
    
    print(f'   数据库按级别统计:')
    for level, count in sorted(stats.get("db_by_level", {}).items()):
        print(f'     {level}: {count}')
    
    print_section('5. 导出同步数据')
    export_file = os.path.join('/tmp', f'ai_employees_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    export_result = sync_manager.export_employees(employees, export_file)
    print(f'   导出员工数: {export_result["total_employees"]}')
    print(f'   输出文件: {export_file}')
    
    print_section('6. 数据库验证')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE is_enabled = 1')
    active = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE is_enabled = 0')
    inactive = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT employee_type, COUNT(*) as cnt 
        FROM ai_employees 
        GROUP BY employee_type 
        ORDER BY cnt DESC
    ''')
    type_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT level, COUNT(*) as cnt 
        FROM ai_employees 
        GROUP BY level 
        ORDER BY level DESC
    ''')
    level_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT COUNT(*) FROM ai_employees WHERE employee_type != 'general'
    ''')
    special_types = cursor.fetchone()[0]
    
    conn.close()
    
    print(f'   数据库验证结果:')
    print(f'     总员工数: {total}')
    print(f'     活跃员工: {active}')
    print(f'     非活跃员工: {inactive}')
    print(f'     特殊类型员工: {special_types}')
    print(f'     普通类型员工: {total - special_types}')
    print(f'     按类型分布:')
    for row in type_stats:
        print(f'       {row["employee_type"]}: {row["cnt"]}')
    print(f'     按级别分布:')
    for row in level_stats:
        print(f'       Level {row["level"]}: {row["cnt"]}')
    
    print_section('同步完成')
    print(f'总结:')
    print(f'  - 数据库员工总数: {total}')
    print(f'  - 活跃员工数: {active}')
    print(f'  - 非活跃员工数: {inactive}')
    print(f'  - 员工类型数量: {len(type_stats)}')
    print(f'  - 员工级别数量: {len(level_stats)}')
    print(f'  - 本次新增: {sync_result["created"]}')
    print(f'  - 本次更新: {sync_result["updated"]}')
    print(f'  - 同步失败: {sync_result["failed"]}')

if __name__ == '__main__':
    main()
