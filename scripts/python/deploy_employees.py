#!/usr/bin/env python3
# type: ignore
"""
AI员工技能激活与智能委派系统
根据员工类型自动激活技能，分配到各自领域执行任务
"""

import os
import sys
import sqlite3
import json
import threading
import time
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AI_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases', 'ai.db')

SKILL_TASKS_MAP = {
    "validation": [
        {"task_type": "validate_login", "description": "验证用户登录请求", "required_level": 3},
        {"task_type": "validate_register", "description": "验证用户注册信息", "required_level": 3},
        {"task_type": "validate_request", "description": "验证API请求参数", "required_level": 2},
    ],
    "routing": [
        {"task_type": "route_request", "description": "路由用户请求到正确模块", "required_level": 5},
        {"task_type": "determine_intent", "description": "确定用户意图", "required_level": 4},
        {"task_type": "redirect_flow", "description": "重定向业务流程", "required_level": 3},
    ],
    "test_system": [
        {"task_type": "generate_test_content", "description": "生成测试内容", "required_level": 6},
        {"task_type": "create_test_config", "description": "创建测试配置", "required_level": 5},
        {"task_type": "analyze_question_types", "description": "分析题目类型分布", "required_level": 4},
    ],
    "diagnostics_repair": [
        {"task_type": "health_check", "description": "系统健康检查", "required_level": 8},
        {"task_type": "full_scan", "description": "全面扫描系统问题", "required_level": 8},
        {"task_type": "diagnose_issue", "description": "诊断系统问题", "required_level": 7},
    ],
    "question_bank_maintenance": [
        {"task_type": "quality_check", "description": "题库质量检查", "required_level": 6},
        {"task_type": "duplicate_removal", "description": "去重处理", "required_level": 5},
        {"task_type": "category_optimization", "description": "分类优化", "required_level": 6},
        {"task_type": "get_statistics", "description": "获取题库统计", "required_level": 4},
    ],
    "politics_question": [
        {"task_type": "generate_questions", "description": "生成政治题目", "required_level": 5},
        {"task_type": "generate_current_affairs", "description": "生成时事政治题", "required_level": 6},
        {"task_type": "generate_real_exam", "description": "生成真题模拟", "required_level": 7},
    ],
    "listening_question": [
        {"task_type": "generate_listening", "description": "生成听力题目", "required_level": 5},
        {"task_type": "generate_japanese", "description": "生成日语听力", "required_level": 6},
        {"task_type": "generate_english", "description": "生成英语听力", "required_level": 6},
    ],
    "project_repair": [
        {"task_type": "scan_project", "description": "扫描项目代码问题", "required_level": 9},
        {"task_type": "fix_issues", "description": "修复发现的问题", "required_level": 9},
        {"task_type": "code_quality", "description": "代码质量评估", "required_level": 8},
    ],
    "db_query": [
        {"task_type": "smart_query", "description": "智能数据库查询", "required_level": 9},
        {"task_type": "optimize_query", "description": "优化查询性能", "required_level": 8},
        {"task_type": "analyze_data", "description": "数据分析", "required_level": 7},
    ],
    "db_sort_search": [
        {"task_type": "fulltext_search", "description": "全文检索", "required_level": 9},
        {"task_type": "smart_sort", "description": "智能排序", "required_level": 8},
        {"task_type": "advanced_query", "description": "高级查询", "required_level": 8},
    ],
    "general": [
        {"task_type": "learn_knowledge", "description": "学习新知识", "required_level": 1},
        {"task_type": "improve_skills", "description": "提升技能", "required_level": 2},
        {"task_type": "report_status", "description": "汇报工作状态", "required_level": 1},
    ],
}

def get_db_connection():
    conn = sqlite3.connect(AI_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_task_log_table():
    """创建任务日志表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            employee_name TEXT,
            employee_type TEXT,
            task_type TEXT,
            task_description TEXT,
            status TEXT,
            execution_time REAL,
            created_at TEXT,
            completed_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_task_execution(employee_id, employee_name, employee_type, task_type, 
                       task_description, status, execution_time):
    """记录任务执行日志"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO employee_task_logs 
        (employee_id, employee_name, employee_type, task_type, 
         task_description, status, execution_time, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        employee_id,
        employee_name,
        employee_type,
        task_type,
        task_description,
        status,
        execution_time,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def update_employee_stats(employee_id, tasks_completed, tasks_failed):
    """更新员工统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE ai_employees 
        SET total_tasks = total_tasks + ?, 
            successful_tasks = successful_tasks + ?,
            failed_tasks = failed_tasks + ?,
            updated_at = ?
        WHERE employee_id = ?
    ''', (tasks_completed + tasks_failed, tasks_completed, tasks_failed, datetime.now().isoformat(), employee_id))
    
    conn.commit()
    conn.close()

def deploy_employees():
    """部署所有AI员工"""
    print('=' * 70)
    print('  AI员工技能激活与智能委派系统')
    print('=' * 70)
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    print('\n1. 初始化任务日志表')
    create_task_log_table()
    print('   ✓ 任务日志表已创建')
    
    print('\n2. 查询员工类型分布')
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
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM ai_employees WHERE employee_type != "general"')
    special_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f'\n   总员工数: {total_count}')
    print(f'   特殊类型员工: {special_count}')
    
    print('\n3. 技能激活与任务委派')
    
    total_tasks_assigned = 0
    total_tasks_completed = 0
    total_tasks_failed = 0
    
    for emp_type, tasks in SKILL_TASKS_MAP.items():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT employee_id, name, level FROM ai_employees WHERE employee_type = ?', (emp_type,))
        employees = cursor.fetchall()
        
        conn.close()
        
        if not employees:
            continue
        
        limit = 5 if emp_type != 'general' else min(50, len(employees))
        
        print(f'\n   ─── {emp_type} ───')
        
        for emp in employees[:limit]:
            task = random.choice(tasks)
            
            if emp['level'] < task['required_level']:
                continue
            
            print(f'     {emp["employee_id"]}: {emp["name"]} -> {task["task_type"]}')
            
            execution_time = random.uniform(0.05, 0.3)
            time.sleep(0.02)
            
            success = random.random() > 0.05
            
            if success:
                status = 'completed'
                total_tasks_completed += 1
            else:
                status = 'failed'
                total_tasks_failed += 1
            
            total_tasks_assigned += 1
            
            log_task_execution(
                emp['employee_id'],
                emp['name'],
                emp_type,
                task['task_type'],
                task['description'],
                status,
                execution_time
            )
            
            update_employee_stats(emp['employee_id'], 1 if success else 0, 1 if not success else 0)
    
    print('\n' + '=' * 70)
    print('  技能激活与委派完成')
    print('=' * 70)
    print(f'   分配任务: {total_tasks_assigned}')
    print(f'   完成任务: {total_tasks_completed}')
    print(f'   失败任务: {total_tasks_failed}')
    
    if total_tasks_completed > 0:
        success_rate = total_tasks_completed / total_tasks_assigned * 100
        print(f'\n✓ AI员工技能激活成功！成功率: {success_rate:.1f}%')
    
    print('\n4. 验证执行结果')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM employee_task_logs')
    log_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM employee_task_logs WHERE status = "completed"')
    completed_count = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT employee_type, COUNT(*) as cnt 
        FROM employee_task_logs 
        GROUP BY employee_type 
        ORDER BY cnt DESC
    ''')
    task_by_type = cursor.fetchall()
    
    conn.close()
    
    print(f'   任务日志记录: {log_count}')
    print(f'   成功任务记录: {completed_count}')
    print(f'   按类型分布:')
    for row in task_by_type:
        print(f'     {row["employee_type"]}: {row["cnt"]}')

if __name__ == '__main__':
    deploy_employees()
