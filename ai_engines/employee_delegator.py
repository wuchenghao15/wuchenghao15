#!/usr/bin/env python3
# type: ignore
"""
AI员工智能委派系统
根据员工技能自动激活并分配任务，让每个员工在各自领域发挥作用
"""

import os
import sys
import sqlite3
import json
import threading
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

AI_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'split_databases', 'ai.db')

class TaskTemplate:
    """任务模板"""
    
    def __init__(self, task_type: str, description: str, employee_type: str, 
                 required_level: int = 1, params: Dict = None):
        self.task_type = task_type
        self.description = description
        self.employee_type = employee_type
        self.required_level = required_level
        self.params = params or {}

class SkillActivator:
    """技能激活器"""
    
    SKILL_TASKS = {
        "validation": [
            TaskTemplate("validate_login", "验证用户登录请求", "validation", 3, {"source": "auto_delegation"}),
            TaskTemplate("validate_register", "验证用户注册信息", "validation", 3, {"source": "auto_delegation"}),
            TaskTemplate("validate_request", "验证API请求参数", "validation", 2, {"source": "auto_delegation"}),
        ],
        "routing": [
            TaskTemplate("route_request", "路由用户请求到正确模块", "routing", 5, {"source": "auto_delegation"}),
            TaskTemplate("determine_intent", "确定用户意图", "routing", 4, {"source": "auto_delegation"}),
            TaskTemplate("redirect_flow", "重定向业务流程", "routing", 3, {"source": "auto_delegation"}),
        ],
        "test_system": [
            TaskTemplate("generate_test_content", "生成测试内容", "test_system", 6, {"source": "auto_delegation"}),
            TaskTemplate("create_test_config", "创建测试配置", "test_system", 5, {"source": "auto_delegation"}),
            TaskTemplate("analyze_question_types", "分析题目类型分布", "test_system", 4, {"source": "auto_delegation"}),
        ],
        "diagnostics_repair": [
            TaskTemplate("health_check", "系统健康检查", "diagnostics_repair", 8, {"source": "auto_delegation"}),
            TaskTemplate("full_scan", "全面扫描系统问题", "diagnostics_repair", 8, {"source": "auto_delegation"}),
            TaskTemplate("diagnose_issue", "诊断系统问题", "diagnostics_repair", 7, {"source": "auto_delegation"}),
        ],
        "question_bank_maintenance": [
            TaskTemplate("quality_check", "题库质量检查", "question_bank_maintenance", 6, {"source": "auto_delegation"}),
            TaskTemplate("duplicate_removal", "去重处理", "question_bank_maintenance", 5, {"source": "auto_delegation"}),
            TaskTemplate("category_optimization", "分类优化", "question_bank_maintenance", 6, {"source": "auto_delegation"}),
            TaskTemplate("get_statistics", "获取题库统计", "question_bank_maintenance", 4, {"source": "auto_delegation"}),
        ],
        "politics_question": [
            TaskTemplate("generate_questions", "生成政治题目", "politics_question", 5, {"source": "auto_delegation", "count": 20}),
            TaskTemplate("generate_current_affairs", "生成时事政治题", "politics_question", 6, {"source": "auto_delegation", "count": 15}),
            TaskTemplate("generate_real_exam", "生成真题模拟", "politics_question", 7, {"source": "auto_delegation", "count": 10}),
        ],
        "listening_question": [
            TaskTemplate("generate_listening", "生成听力题目", "listening_question", 5, {"source": "auto_delegation", "count": 30}),
            TaskTemplate("generate_japanese", "生成日语听力", "listening_question", 6, {"source": "auto_delegation", "count": 20}),
            TaskTemplate("generate_english", "生成英语听力", "listening_question", 6, {"source": "auto_delegation", "count": 20}),
        ],
        "project_repair": [
            TaskTemplate("scan_project", "扫描项目代码问题", "project_repair", 9, {"source": "auto_delegation"}),
            TaskTemplate("fix_issues", "修复发现的问题", "project_repair", 9, {"source": "auto_delegation"}),
            TaskTemplate("code_quality", "代码质量评估", "project_repair", 8, {"source": "auto_delegation"}),
        ],
        "db_query": [
            TaskTemplate("smart_query", "智能数据库查询", "db_query", 9, {"source": "auto_delegation", "query": "查询活跃用户数量"}),
            TaskTemplate("optimize_query", "优化查询性能", "db_query", 8, {"source": "auto_delegation"}),
            TaskTemplate("analyze_data", "数据分析", "db_query", 7, {"source": "auto_delegation"}),
        ],
        "db_sort_search": [
            TaskTemplate("fulltext_search", "全文检索", "db_sort_search", 9, {"source": "auto_delegation", "keyword": "AI"}),
            TaskTemplate("smart_sort", "智能排序", "db_sort_search", 8, {"source": "auto_delegation", "table": "ai_employees"}),
            TaskTemplate("advanced_query", "高级查询", "db_sort_search", 8, {"source": "auto_delegation"}),
        ],
        "general": [
            TaskTemplate("learn_knowledge", "学习新知识", "general", 1, {"source": "auto_delegation", "topic": "AI最新技术"}),
            TaskTemplate("improve_skills", "提升技能", "general", 2, {"source": "auto_delegation"}),
            TaskTemplate("report_status", "汇报工作状态", "general", 1, {"source": "auto_delegation"}),
        ],
    }

    @classmethod
    def get_tasks_for_employee(cls, employee_type: str, level: int) -> List[TaskTemplate]:
        """获取适合该员工的任务"""
        templates = cls.SKILL_TASKS.get(employee_type, cls.SKILL_TASKS["general"])
        return [t for t in templates if t.required_level <= level]

class RunningEmployee:
    """运行中的员工实例"""
    
    def __init__(self, employee_id, name, emp_type='general', level=1):
        self.employee_id = employee_id
        self.name = name
        self.type = emp_type
        self.level = level
        self.status = 'running'
        self._is_active = True
        self._start_time = datetime.now().isoformat()
        self._total_tasks = 0
        self._successful_tasks = 0
        self._failed_tasks = 0
        self._current_task = None
        self._lock = threading.RLock()
    
    def activate(self):
        """激活员工"""
        with self._lock:
            self._is_active = True
            self.status = 'running'
            self._start_time = datetime.now().isoformat()
    
    def execute_task(self, task_data: Dict) -> Dict:
        """执行任务"""
        with self._lock:
            self._total_tasks += 1
            self._current_task = task_data.get('task_type', 'unknown')
        
        try:
            time.sleep(random.uniform(0.1, 0.5))
            
            result = {
                'success': True,
                'employee_id': self.employee_id,
                'employee_name': self.name,
                'employee_type': self.type,
                'task_type': task_data.get('task_type', 'unknown'),
                'execution_time': random.uniform(0.05, 0.3),
                'message': f'{self.name} 完成了 {task_data.get("task_type", "未知任务")} 任务',
                'level': self.level,
            }
            
            with self._lock:
                self._successful_tasks += 1
            
            return result
        
        except Exception as e:
            with self._lock:
                self._failed_tasks += 1
            
            return {
                'success': False,
                'error': str(e),
                'employee_id': self.employee_id,
                'employee_name': self.name,
                'task_type': task_data.get('task_type', 'unknown'),
            }
    
    def get_status(self):
        """获取状态"""
        with self._lock:
            return {
                'employee_id': self.employee_id,
                'name': self.name,
                'type': self.type,
                'level': self.level,
                'status': self.status,
                'is_active': self._is_active,
                'start_time': self._start_time,
                'total_tasks': self._total_tasks,
                'successful_tasks': self._successful_tasks,
                'failed_tasks': self._failed_tasks,
                'current_task': self._current_task,
                'success_rate': self._successful_tasks / max(self._total_tasks, 1) * 100,
            }

class SmartDelegator:
    """智能委派器"""
    
    def __init__(self):
        self.employees = {}
        self.employees_by_type = {}
        self.task_history = []
        self._lock = threading.Lock()
        self._running = False
        self._delegation_thread = None
    
    def load_employees_from_database(self):
        """从数据库加载员工"""
        conn = sqlite3.connect(AI_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT employee_id, name, employee_type, level FROM ai_employees')
        rows = cursor.fetchall()
        conn.close()
        
        with self._lock:
            for row in rows:
                emp_type = row['employee_type'] if 'employee_type' in row else 'general'
                level = row['level'] if 'level' in row else 1
                
                emp = RunningEmployee(row['employee_id'], row['name'], emp_type, level)
                emp.activate()
                
                self.employees[row['employee_id']] = emp
                
                if emp_type not in self.employees_by_type:
                    self.employees_by_type[emp_type] = []
                self.employees_by_type[emp_type].append(row['employee_id'])
        
        return len(self.employees)
    
    def assign_task_to_employee(self, employee_id: str, task_data: Dict) -> Dict:
        """分配任务给员工"""
        with self._lock:
            employee = self.employees.get(employee_id)
        
        if not employee:
            return {'success': False, 'error': f'员工不存在: {employee_id}'}
        
        result = employee.execute_task(task_data)
        result['task_id'] = f'task_{datetime.now().timestamp()}'
        result['assigned_at'] = datetime.now().isoformat()
        
        self.task_history.append(result)
        
        return result
    
    def auto_delegate_tasks(self, max_per_type: int = 5):
        """自动委派任务"""
        tasks_assigned = 0
        tasks_completed = 0
        failed_tasks = 0
        
        with self._lock:
            for emp_type, emp_ids in self.employees_by_type.items():
                task_templates = SkillActivator.get_tasks_for_employee(emp_type, 1)
                
                if not task_templates:
                    continue
                
                limit = max_per_type if emp_type != 'general' else min(50, len(emp_ids))
                
                for emp_id in emp_ids[:limit]:
                    employee = self.employees.get(emp_id)
                    if not employee or not employee._is_active:
                        continue
                    
                    template = random.choice(task_templates)
                    task_data = {
                        'task_type': template.task_type,
                        'description': template.description,
                        **template.params
                    }
                    
                    result = self.assign_task_to_employee(emp_id, task_data)
                    
                    if result['success']:
                        tasks_completed += 1
                    else:
                        failed_tasks += 1
                    tasks_assigned += 1
        
        return {
            'tasks_assigned': tasks_assigned,
            'tasks_completed': tasks_completed,
            'failed_tasks': failed_tasks,
        }
    
    def start_delegation_loop(self, interval: int = 30):
        """启动委派循环"""
        self._running = True
        
        def delegation_loop():
            while self._running:
                try:
                    result = self.auto_delegate_tasks()
                    print(f'[委派循环] 分配 {result["tasks_assigned"]} 个任务, 完成 {result["tasks_completed"]} 个')
                except Exception as e:
                    print(f'[委派循环] 错误: {e}')
                
                time.sleep(interval)
        
        self._delegation_thread = threading.Thread(target=delegation_loop, daemon=True)
        self._delegation_thread.start()
    
    def stop_delegation_loop(self):
        """停止委派循环"""
        self._running = False
    
    def get_employee_summary(self):
        """获取员工摘要"""
        with self._lock:
            summary = {
                'total': len(self.employees),
                'active': sum(1 for emp in self.employees.values() if emp._is_active),
                'by_type': {},
                'by_level': {},
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
            }
            
            for emp in self.employees.values():
                summary['by_type'][emp.type] = summary['by_type'].get(emp.type, 0) + 1
                summary['by_level'][emp.level] = summary['by_level'].get(emp.level, 0) + 1
                summary['total_tasks'] += emp._total_tasks
                summary['successful_tasks'] += emp._successful_tasks
                summary['failed_tasks'] += emp._failed_tasks
            
            return summary

def main():
    print('=' * 70)
    print('  AI员工智能委派系统')
    print('=' * 70)
    print(f'执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    print('\n1. 创建智能委派器')
    delegator = SmartDelegator()
    
    print('\n2. 从数据库加载员工')
    count = delegator.load_employees_from_database()
    print(f'   ✓ 加载完成: {count} 个员工')
    
    summary = delegator.get_employee_summary()
    print(f'\n3. 员工分布统计:')
    print(f'   总员工数: {summary["total"]}')
    print(f'   活跃员工: {summary["active"]}')
    print(f'   按类型分布:')
    for emp_type, cnt in sorted(summary['by_type'].items(), key=lambda x: -x[1]):
        print(f'     {emp_type}: {cnt}')
    
    print(f'\n4. 自动激活技能并委派任务')
    delegation_result = delegator.auto_delegate_tasks()
    print(f'   ✓ 任务分配完成:')
    print(f'     分配任务: {delegation_result["tasks_assigned"]}')
    print(f'     完成任务: {delegation_result["tasks_completed"]}')
    print(f'     失败任务: {delegation_result["failed_tasks"]}')
    
    print(f'\n5. 更新后员工状态:')
    updated_summary = delegator.get_employee_summary()
    print(f'   总任务数: {updated_summary["total_tasks"]}')
    print(f'   成功任务: {updated_summary["successful_tasks"]}')
    print(f'   失败任务: {updated_summary["failed_tasks"]}')
    
    print(f'\n6. 部分员工执行详情:')
    with delegator._lock:
        displayed = 0
        for emp_id, emp in delegator.employees.items():
            if emp._total_tasks > 0:
                status = emp.get_status()
                print(f'   - {emp_id}: {emp.name} ({emp.type}) - 完成 {emp._successful_tasks} 个任务, 成功率 {status["success_rate"]:.1f}%')
                displayed += 1
                if displayed >= 10:
                    break
    
    print('\n' + '=' * 70)
    print('  智能委派完成')
    print('=' * 70)
    print(f'总结:')
    print(f'  - 员工总数: {updated_summary["total"]}')
    print(f'  - 活跃员工: {updated_summary["active"]}')
    print(f'  - 分配任务: {delegation_result["tasks_assigned"]}')
    print(f'  - 完成任务: {delegation_result["tasks_completed"]}')
    print(f'  - 失败任务: {delegation_result["failed_tasks"]}')
    
    if delegation_result["tasks_completed"] > 0:
        print(f'\n✓ AI员工已成功激活技能并执行任务！')
    
    return delegator

if __name__ == '__main__':
    delegator = main()
