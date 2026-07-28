#!/usr/bin/env python3
# type: ignore
"""
激活数据库保存的所有AI员工
从数据库读取所有员工，启动它们，并更新状态
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

class ActiveEmployee:
    """激活状态的员工对象"""
    def __init__(self, row):
        self.employee_id = row['employee_id']
        self.name = row['name']
        self.employee_type = row['employee_type'] if 'employee_type' in row else 'general'
        self.level = row['level'] if 'level' in row else 1
        self.status = row['status'] if 'status' in row else 'inactive'
        self.is_enabled = row['is_enabled'] if 'is_enabled' in row else 0
        self.capabilities = json.loads(row['capabilities']) if 'capabilities' in row and row['capabilities'] else []
        self.knowledge_domain = row['knowledge_domain'] if 'knowledge_domain' in row else ''
        self.personality_type = row['personality_type'] if 'personality_type' in row else ''
        self.performance_score = row['performance_score'] if 'performance_score' in row else 0.0
        self.total_tasks = row['total_tasks'] if 'total_tasks' in row else 0
        self.successful_tasks = row['successful_tasks'] if 'successful_tasks' in row else 0
        self.failed_tasks = row['failed_tasks'] if 'failed_tasks' in row else 0
        
        self._is_active = False
        self._start_time = None
        self._active_tasks = 0
    
    def activate(self):
        """激活员工"""
        self._is_active = True
        self._start_time = datetime.now().isoformat()
        self.status = 'active'
        self.is_enabled = 1
        return {'success': True, 'message': f'{self.name} 已激活', 'employee_id': self.employee_id}
    
    def get_active_status(self):
        """获取激活状态"""
        return {
            'employee_id': self.employee_id,
            'name': self.name,
            'type': self.employee_type,
            'level': self.level,
            'status': 'running' if self._is_active else 'stopped',
            'is_active': self._is_active,
            'start_time': self._start_time,
            'active_tasks': self._active_tasks,
            'performance_score': self.performance_score,
            'success_rate': self.successful_tasks / max(self.total_tasks, 1) * 100
        }

def main():
    print_section('激活数据库保存的所有AI员工')
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'目标数据库: {AI_DB_PATH}')
    
    print_section('1. 从数据库读取所有员工')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ai_employees')
    rows = cursor.fetchall()
    total_count = len(rows)
    
    print(f'   ✓ 数据库中共有 {total_count} 个AI员工')
    
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status != 'active'")
    inactive_count = cursor.fetchone()[0]
    
    print(f'   ✓ 当前活跃状态: {active_count}')
    print(f'   ✓ 当前非活跃状态: {inactive_count}')
    
    print_section('2. 创建员工对象并激活')
    active_employees = []
    activated_count = 0
    already_active_count = 0
    
    for row in rows:
        emp = ActiveEmployee(row)
        if emp.status == 'active' and emp.is_enabled == 1:
            already_active_count += 1
            emp._is_active = True
        else:
            result = emp.activate()
            if result['success']:
                activated_count += 1
        
        active_employees.append(emp)
        if activated_count % 500 == 0 and activated_count > 0:
            print(f'   ✓ 已激活 {activated_count} 个员工...')
    
    print(f'   ✓ 激活完成: 新增激活 {activated_count} 个, 已活跃 {already_active_count} 个')
    
    print_section('3. 更新数据库状态')
    updated_count = 0
    for emp in active_employees:
        if emp.status != 'active' or emp.is_enabled != 1:
            cursor.execute('''
                UPDATE ai_employees 
                SET status = ?, is_enabled = ?, updated_at = ?
                WHERE employee_id = ?
            ''', ('active', 1, datetime.now().isoformat(), emp.employee_id))
            updated_count += 1
    
    conn.commit()
    print(f'   ✓ 数据库更新完成: 更新 {updated_count} 条记录')
    
    print_section('4. 验证激活结果')
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
    new_active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE is_enabled = 1")
    enabled_count = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT employee_type, COUNT(*) as cnt 
        FROM ai_employees 
        WHERE status = 'active'
        GROUP BY employee_type 
        ORDER BY cnt DESC
    ''')
    type_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT level, COUNT(*) as cnt 
        FROM ai_employees 
        WHERE status = 'active'
        GROUP BY level 
        ORDER BY level DESC
    ''')
    level_stats = cursor.fetchall()
    
    conn.close()
    
    print(f'   验证结果:')
    print(f'     活跃员工总数: {new_active_count}')
    print(f'     启用员工总数: {enabled_count}')
    print(f'     按类型分布:')
    for row in type_stats:
        print(f'       {row["employee_type"]}: {row["cnt"]}')
    print(f'     按级别分布:')
    for row in level_stats:
        print(f'       Level {row["level"]}: {row["cnt"]}')
    
    print_section('5. 生成激活报告')
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_employees': total_count,
        'activated_count': activated_count,
        'already_active_count': already_active_count,
        'database_updated_count': updated_count,
        'final_active_count': new_active_count,
        'final_enabled_count': enabled_count,
        'by_type': {row['employee_type']: row['cnt'] for row in type_stats},
        'by_level': {row['level']: row['cnt'] for row in level_stats},
        'active_employees': [emp.get_active_status() for emp in active_employees[:10]]
    }
    
    report_file = os.path.join('/tmp', f'ai_employees_activation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'   激活报告已生成: {report_file}')
    
    print_section('激活完成')
    print(f'总结:')
    print(f'  - 数据库员工总数: {total_count}')
    print(f'  - 本次激活数量: {activated_count}')
    print(f'  - 已活跃数量: {already_active_count}')
    print(f'  - 最终活跃数量: {new_active_count}')
    print(f'  - 数据库更新记录: {updated_count}')
    print(f'  - 激活报告文件: {report_file}')
    
    if new_active_count == total_count:
        print(f'\n✓ 所有AI员工已成功激活！')

if __name__ == '__main__':
    main()
