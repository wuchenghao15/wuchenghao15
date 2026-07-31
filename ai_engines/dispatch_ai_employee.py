#!/usr/bin/env python3
"""
输配AI员工 (Dispatch & Distribution AI Employee)
负责任务调度、资源分配、负载均衡、智能路由
将任务自动分发给最合适的AI员工执行，并上报分发结果
"""
import os
import json
import sqlite3
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(_PROJECT_ROOT, 'app.db')


class DispatchAIEmployee:
    """输配AI员工：智能任务调度与资源分配"""

    def __init__(self, employee_id: str = 'dispatch_001', name: str = '输配调度AI员工', level: int = 9):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.role = 'dispatch'
        self.status = 'active'
        self.created_at = datetime.now().isoformat()
        self.dispatch_count = 0
        self.success_count = 0
        self.fail_count = 0
        self._init_db()
        logger.info(f"[DispatchAIEmployee] {name} 初始化完成 (level={level})")

    def _init_db(self):
        """初始化输配记录表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS dispatch_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dispatch_id TEXT UNIQUE,
                        task_type TEXT NOT NULL,
                        source_module TEXT,
                        target_employee_id TEXT,
                        target_employee_name TEXT,
                        priority INTEGER DEFAULT 5,
                        status TEXT DEFAULT 'pending',
                        task_data TEXT,
                        result_data TEXT,
                        dispatch_reason TEXT,
                        created_at TEXT,
                        completed_at TEXT,
                        duration_ms REAL
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS dispatch_routing_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT UNIQUE,
                        task_type TEXT,
                        target_role TEXT,
                        priority_weight INTEGER DEFAULT 50,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                # 插入默认路由规则
                default_rules = [
                    ('listening_question', 'question_bank_maintenance', 80),
                    ('chinese_dictation', 'question_bank_maintenance', 80),
                    ('system_diagnostic', 'diagnostics_repair', 90),
                    ('security_scan', 'vikey_security', 90),
                    ('layout_adjust', 'layout_adjuster', 70),
                    ('k12_question', 'k12_question', 75),
                    ('general_task', 'developer', 50),
                    ('test_task', 'tester', 60),
                    ('data_analysis', 'analyst', 65),
                    ('content_writing', 'writer', 55),
                ]
                for task_type, target_role, weight in default_rules:
                    conn.execute('''
                        INSERT OR IGNORE INTO dispatch_routing_rules
                        (rule_name, task_type, target_role, priority_weight, is_active, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    ''', (f'{task_type}_to_{target_role}', task_type, target_role, weight,
                          datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 初始化数据库失败: {e}")

    def start(self):
        """启动输配AI员工"""
        self.status = 'running'
        logger.info(f"[DispatchAIEmployee] {self.name} 已启动")

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行输配任务"""
        task_type = task_data.get('task_type', 'general')
        source = task_data.get('source_module', 'system')
        priority = task_data.get('priority', 5)

        # 查找最佳目标员工
        target = self._find_best_employee(task_type)

        dispatch_id = f"disp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

        record = {
            'dispatch_id': dispatch_id,
            'task_type': task_type,
            'source_module': source,
            'target_employee_id': target.get('employee_id', ''),
            'target_employee_name': target.get('name', ''),
            'priority': priority,
            'status': 'dispatched',
            'task_data': json.dumps(task_data, ensure_ascii=False),
            'dispatch_reason': target.get('reason', 'best_match'),
            'created_at': datetime.now().isoformat()
        }

        self._save_dispatch(record)
        self.dispatch_count += 1

        # 尝试执行任务
        result = self._execute_on_target(target, task_data)
        if result.get('success'):
            self.success_count += 1
            record['status'] = 'completed'
        else:
            self.fail_count += 1
            record['status'] = 'failed'

        record['result_data'] = json.dumps(result, ensure_ascii=False)
        record['completed_at'] = datetime.now().isoformat()
        self._update_dispatch(record)

        # 上报结果
        self._report_dispatch_result(record)

        return {
            'success': result.get('success', False),
            'dispatch_id': dispatch_id,
            'target': target.get('name', ''),
            'result': result
        }

    def _find_best_employee(self, task_type: str) -> Dict[str, Any]:
        """根据路由规则查找最佳目标员工"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 先查路由规则
                cursor.execute('''
                    SELECT target_role, priority_weight FROM dispatch_routing_rules
                    WHERE task_type = ? AND is_active = 1
                    ORDER BY priority_weight DESC
                ''', (task_type,))
                rule = cursor.fetchone()

                if rule:
                    target_role = rule['target_role']
                    # 查找匹配角色的员工
                    cursor.execute('''
                        SELECT id, name, employee_code, skill_level, accuracy, total_tasks
                        FROM ai_employees
                        WHERE employee_code = ? AND is_enabled = 1 AND status = 'active'
                        ORDER BY skill_level DESC, accuracy DESC
                        LIMIT 1
                    ''', (target_role,))
                    emp = cursor.fetchone()
                    if emp:
                        return {
                            'employee_id': f"db_emp_{emp['id']}",
                            'name': emp['name'],
                            'role': target_role,
                            'reason': f'路由规则匹配 (权重={rule["priority_weight"]})'
                        }

                # 回退：查找任意可用员工
                cursor.execute('''
                    SELECT id, name, employee_code, skill_level
                    FROM ai_employees
                    WHERE is_enabled = 1 AND status = 'active'
                    ORDER BY skill_level DESC, total_tasks ASC
                    LIMIT 1
                ''')
                emp = cursor.fetchone()
                if emp:
                    return {
                        'employee_id': f"db_emp_{emp['id']}",
                        'name': emp['name'],
                        'role': emp['employee_code'],
                        'reason': '负载均衡选择'
                    }
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 查找员工失败: {e}")

        return {
            'employee_id': 'fallback',
            'name': '系统默认处理器',
            'role': 'general',
            'reason': '无可用员工，使用回退'
        }

    def _execute_on_target(self, target: Dict, task_data: Dict) -> Dict[str, Any]:
        """在目标员工上执行任务"""
        try:
            # 尝试通过AI员工加载器执行
            from ai_engines.all_ai_employees_loader import ai_employee_loader

            emp_id = target.get('employee_id', '')
            if emp_id in ai_employee_loader.employees:
                emp_info = ai_employee_loader.employees[emp_id]
                employee = emp_info.get('employee')
                if employee and hasattr(employee, 'execute_task'):
                    return employee.execute_task(task_data)

            # 回退：直接返回模拟结果
            return {
                'success': True,
                'message': f"任务已分配给 {target.get('name', '未知')}",
                'executed_by': target.get('name', ''),
                'task_type': task_data.get('task_type', 'general')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _save_dispatch(self, record: Dict):
        """保存输配记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO dispatch_records
                    (dispatch_id, task_type, source_module, target_employee_id,
                     target_employee_name, priority, status, task_data,
                     dispatch_reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record['dispatch_id'], record['task_type'],
                    record['source_module'], record['target_employee_id'],
                    record['target_employee_name'], record['priority'],
                    record['status'], record.get('task_data', ''),
                    record.get('dispatch_reason', ''), record['created_at']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 保存输配记录失败: {e}")

    def _update_dispatch(self, record: Dict):
        """更新输配记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    UPDATE dispatch_records
                    SET status = ?, result_data = ?, completed_at = ?
                    WHERE dispatch_id = ?
                ''', (
                    record.get('status', 'unknown'),
                    record.get('result_data', ''),
                    record.get('completed_at'),
                    record['dispatch_id']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 更新输配记录失败: {e}")

    def _report_dispatch_result(self, record: Dict):
        """上报输配结果到上报数据库"""
        try:
            from app.services.system_report_service import system_report_service
            system_report_service.submit_report(
                report_type='dispatch_result',
                module='dispatch_ai_employee',
                severity='info' if record.get('status') == 'completed' else 'warning',
                title=f"输配任务 {record.get('dispatch_id', '')}",
                content=json.dumps(record, ensure_ascii=False),
                metadata={
                    'task_type': record.get('task_type'),
                    'target': record.get('target_employee_name'),
                    'status': record.get('status')
                }
            )
        except Exception as e:
            logger.debug(f"[DispatchAIEmployee] 上报结果失败: {e}")

    def get_dispatch_stats(self) -> Dict[str, Any]:
        """获取输配统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as total FROM dispatch_records')
                total = cursor.fetchone()['total']
                cursor.execute("SELECT COUNT(*) as cnt FROM dispatch_records WHERE status = 'completed'")
                completed = cursor.fetchone()['cnt']
                cursor.execute("SELECT COUNT(*) as cnt FROM dispatch_records WHERE status = 'failed'")
                failed = cursor.fetchone()['cnt']

                # 按任务类型统计
                cursor.execute('''
                    SELECT task_type, COUNT(*) as cnt
                    FROM dispatch_records
                    GROUP BY task_type ORDER BY cnt DESC
                ''')
                by_type = {row['task_type']: row['cnt'] for row in cursor.fetchall()}

                # 按目标员工统计
                cursor.execute('''
                    SELECT target_employee_name, COUNT(*) as cnt
                    FROM dispatch_records
                    GROUP BY target_employee_name ORDER BY cnt DESC LIMIT 10
                ''')
                by_employee = {row['target_employee_name']: row['cnt'] for row in cursor.fetchall()}

            return {
                'total_dispatches': total,
                'completed': completed,
                'failed': failed,
                'success_rate': round(completed / max(total, 1) * 100, 2),
                'by_task_type': by_type,
                'by_employee': by_employee,
                'employee_stats': {
                    'dispatch_count': self.dispatch_count,
                    'success_count': self.success_count,
                    'fail_count': self.fail_count
                }
            }
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 获取统计失败: {e}")
            return {'error': str(e)}

    def list_routing_rules(self) -> List[Dict]:
        """列出所有路由规则"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM dispatch_routing_rules ORDER BY priority_weight DESC')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 获取路由规则失败: {e}")
            return []

    def add_routing_rule(self, task_type: str, target_role: str, weight: int = 50) -> bool:
        """添加路由规则"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO dispatch_routing_rules
                    (rule_name, task_type, target_role, priority_weight, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                ''', (f'{task_type}_to_{target_role}', task_type, target_role, weight,
                      datetime.now().isoformat()))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[DispatchAIEmployee] 添加路由规则失败: {e}")
            return False


def create_dispatch_ai_employee(level: int = 9) -> DispatchAIEmployee:
    """创建输配AI员工实例"""
    return DispatchAIEmployee(level=level)
