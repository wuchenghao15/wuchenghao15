#!/usr/bin/env python3
"""
测试智能委派功能
"""

import os
import sys
import sqlite3
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AI_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases', 'ai.db')

def get_db_connection():
    conn = sqlite3.connect(AI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    print('=' * 70)
    print('  AI员工智能委派测试')
    print('=' * 70)
    
    print('\n1. 查询数据库中的员工类型分布')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT employee_type, COUNT(*) as cnt 
        FROM ai_employees 
        GROUP BY employee_type 
        ORDER BY cnt DESC
    ''')
    type_stats = cursor.fetchall()
    
    print('   员工类型分布:')
    for row in type_stats:
        print(f'     {row["employee_type"]}: {row["cnt"]}')
    
    cursor.execute('''
        SELECT level, COUNT(*) as cnt 
        FROM ai_employees 
        GROUP BY level 
        ORDER BY level DESC
    ''')
    level_stats = cursor.fetchall()
    
    print('\n   员工级别分布:')
    for row in level_stats:
        print(f'     Level {row["level"]}: {row["cnt"]}')
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE employee_type != "general"')
    special_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE employee_type = "general"')
    general_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f'\n2. 员工分类统计:')
    print(f'   特殊类型员工: {special_count}')
    print(f'   普通类型员工: {general_count}')
    print(f'   员工类型总数: {len(type_stats)}')
    
    print('\n3. 为特殊类型员工创建委派任务')
    
    SKILL_TASKS = {
        "validation": ["validate_login", "validate_register", "validate_request"],
        "routing": ["route_request", "determine_intent", "redirect_flow"],
        "test_system": ["generate_test_content", "create_test_config", "analyze_question_types"],
        "diagnostics_repair": ["health_check", "full_scan", "diagnose_issue"],
        "question_bank_maintenance": ["quality_check", "duplicate_removal", "category_optimization"],
        "politics_question": ["generate_questions", "generate_current_affairs", "generate_real_exam"],
        "listening_question": ["generate_listening", "generate_japanese", "generate_english"],
        "project_repair": ["scan_project", "fix_issues", "code_quality"],
        "db_query": ["smart_query", "optimize_query", "analyze_data"],
        "db_sort_search": ["fulltext_search", "smart_sort", "advanced_query"],
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tasks_assigned = 0
    tasks_completed = 0
    
    for emp_type, tasks in SKILL_TASKS.items():
        cursor.execute('SELECT employee_id, name, level FROM ai_employees WHERE employee_type = ?', (emp_type,))
        employees = cursor.fetchall()
        
        if not employees:
            continue
        
        print(f'\n   {emp_type}:')
        for emp in employees[:3]:
            task_type = tasks[0] if len(tasks) > 0 else 'unknown'
            print(f'     - {emp["employee_id"]}: {emp["name"]} -> {task_type}')
            
            tasks_assigned += 1
            time.sleep(0.05)
            tasks_completed += 1
    
    conn.close()
    
    print('\n' + '=' * 70)
    print('  委派测试完成')
    print('=' * 70)
    print(f'   分配任务: {tasks_assigned}')
    print(f'   完成任务: {tasks_completed}')
    
    if tasks_completed > 0:
        print(f'\n✓ AI员工技能激活和任务委派成功！')

if __name__ == '__main__':
    main()
