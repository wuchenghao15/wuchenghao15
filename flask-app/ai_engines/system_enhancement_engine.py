# -*- coding: utf-8 -*-
"""
MTSCOS 系统增强引擎
增强 AI 员工能力评估、自动任务分配、集群负载均衡
提供真实的能力增强功能，而非仅定义
"""

import os
import sys
import json
import time
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SystemEnhancementEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class SystemEnhancementEngine:
    """系统增强引擎 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._initialized = True
        self._init_database()
        logger.info("SystemEnhancementEngine 初始化完成")

    def _init_database(self):
        """初始化增强引擎数据库表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_task_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT UNIQUE,
                        task_type TEXT,
                        task_data TEXT,
                        required_capability TEXT,
                        assigned_employee TEXT,
                        assigned_cluster TEXT,
                        priority INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        assigned_at TEXT,
                        completed_at TEXT,
                        result TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cluster_load_balance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        cluster_id TEXT,
                        load_score REAL,
                        active_employees INTEGER,
                        busy_employees INTEGER,
                        task_queue_length INTEGER,
                        recommendation TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS employee_capability_matrix (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT,
                        capability TEXT,
                        proficiency INTEGER DEFAULT 50,
                        tasks_done INTEGER DEFAULT 0,
                        last_updated TEXT,
                        UNIQUE(employee_id, capability)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化增强引擎数据库失败: {e}")

    # ==================== 智能任务分配 ====================

    def assign_task_intelligently(self, task_id: str, task_type: str,
                                  required_capability: str, task_data: Dict,
                                  priority: int = 0) -> Dict[str, Any]:
        """智能分配任务给最合适的员工"""
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager

            best_employee = None
            best_score = -1
            best_cluster = None

            for emp_id, emp in ai_cluster_manager.employees.items():
                # 只考虑活跃或空闲的员工
                if emp.status not in ('active',):
                    continue
                # 检查能力匹配
                if required_capability and required_capability not in emp.capabilities:
                    continue
                # 计算匹配分数
                score = self._calculate_employee_score(emp, required_capability)
                if score > best_score:
                    best_score = score
                    best_employee = emp_id
                    best_cluster = emp.assigned_cluster

            if best_employee:
                # 分配任务
                emp = ai_cluster_manager.employees[best_employee]
                task = {
                    'task_id': task_id,
                    'task_type': task_type,
                    'required_capability': required_capability,
                    'data': task_data
                }
                if emp.assign_task(task):
                    self._record_task_assignment(task_id, task_type, task_data,
                                                 required_capability, best_employee,
                                                 best_cluster, priority)
                    self._update_capability_proficiency(best_employee, required_capability)
                    return {
                        'success': True,
                        'task_id': task_id,
                        'assigned_to': best_employee,
                        'cluster': best_cluster,
                        'match_score': round(best_score, 2)
                    }

            # 没有可用员工，加入队列
            self._record_task_assignment(task_id, task_type, task_data,
                                         required_capability, None, None, priority, 'queued')
            return {
                'success': False,
                'message': '无可用员工，任务已加入队列',
                'task_id': task_id
            }
        except Exception as e:
            logger.error(f"智能任务分配失败: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_employee_score(self, employee, required_capability: str) -> float:
        """计算员工匹配分数"""
        score = 50.0  # 基础分
        # 成功率加分
        success_rate = employee.performance_metrics.get('success_rate', 1.0)
        score += success_rate * 30
        # 完成任务数加分（ logarithmic ）
        tasks = employee.performance_metrics.get('tasks_completed', 0)
        score += min(20, tasks * 0.5)
        # 能力熟练度加分
        proficiency = self._get_capability_proficiency(employee.employee_id, required_capability)
        score += proficiency * 0.1
        return score

    def _get_capability_proficiency(self, employee_id: str, capability: str) -> int:
        """获取能力熟练度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT proficiency FROM employee_capability_matrix
                    WHERE employee_id = ? AND capability = ?
                ''', (employee_id, capability))
                row = cursor.fetchone()
                return row[0] if row else 50
        except Exception:
            return 50

    def _update_capability_proficiency(self, employee_id: str, capability: str):
        """更新能力熟练度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO employee_capability_matrix
                    (employee_id, capability, proficiency, tasks_done, last_updated)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(employee_id, capability)
                    DO UPDATE SET
                        proficiency = MIN(100, proficiency + 2),
                        tasks_done = tasks_done + 1,
                        last_updated = ?
                ''', (employee_id, capability, 52, datetime.now().isoformat(),
                      datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"更新能力熟练度失败: {e}")

    def _record_task_assignment(self, task_id, task_type, task_data, capability,
                                employee_id, cluster_id, priority, status='assigned'):
        """记录任务分配"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_task_assignments
                    (task_id, task_type, task_data, required_capability,
                     assigned_employee, assigned_cluster, priority, status, assigned_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id, task_type, json.dumps(task_data, ensure_ascii=False),
                    capability, employee_id, cluster_id, priority, status,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录任务分配失败: {e}")

    # ==================== 集群负载均衡 ====================

    def analyze_cluster_load(self) -> Dict[str, Any]:
        """分析集群负载并给出均衡建议"""
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager

            cluster_loads = []
            for cluster_id, cluster in ai_cluster_manager.clusters.items():
                active = sum(1 for e in cluster.employees.values() if e.status == 'active')
                busy = sum(1 for e in cluster.employees.values() if e.status == 'busy')
                total = len(cluster.employees)
                queue_len = len(cluster.task_queue)

                # 负载分数: 0-100, 越高表示越忙
                load_score = 0
                if total > 0:
                    load_score = (busy / total) * 100
                if queue_len > 0:
                    load_score += min(20, queue_len * 2)
                load_score = min(100, load_score)

                recommendation = 'balanced'
                if load_score > 80:
                    recommendation = 'overloaded'
                elif load_score < 20 and total > 0:
                    recommendation = 'underutilized'

                cluster_loads.append({
                    'cluster_id': cluster_id,
                    'cluster_type': cluster.cluster_type,
                    'total_employees': total,
                    'active_employees': active,
                    'busy_employees': busy,
                    'task_queue_length': queue_len,
                    'load_score': round(load_score, 1),
                    'recommendation': recommendation
                })

                # 记录到数据库
                self._record_cluster_load(cluster_id, load_score, active, busy, queue_len, recommendation)

            # 生成均衡建议
            overloaded = [c for c in cluster_loads if c['recommendation'] == 'overloaded']
            underutilized = [c for c in cluster_loads if c['recommendation'] == 'underutilized']

            suggestions = []
            for o in overloaded:
                for u in underutilized:
                    if u['cluster_type'] == o['cluster_type']:
                        suggestions.append(
                            f"建议从 {o['cluster_id']} 迁移部分员工到 {u['cluster_id']}")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'clusters': cluster_loads,
                'overloaded_clusters': len(overloaded),
                'underutilized_clusters': len(underutilized),
                'suggestions': suggestions
            }
        except Exception as e:
            logger.error(f"分析集群负载失败: {e}")
            return {'success': False, 'error': str(e)}

    def _record_cluster_load(self, cluster_id, load_score, active, busy, queue_len, recommendation):
        """记录集群负载"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cluster_load_balance
                    (timestamp, cluster_id, load_score, active_employees,
                     busy_employees, task_queue_length, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(), cluster_id, load_score,
                    active, busy, queue_len, recommendation
                ))
                cursor.execute('''DELETE FROM cluster_load_balance
                    WHERE timestamp < datetime("now", "-7 days")''')
                conn.commit()
        except Exception as e:
            logger.error(f"记录集群负载失败: {e}")

    # ==================== 员工能力评估 ====================

    def evaluate_all_employees(self) -> Dict[str, Any]:
        """评估所有员工的能力"""
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager

            evaluations = []
            for emp_id, emp in ai_cluster_manager.employees.items():
                metrics = emp.performance_metrics
                tasks = metrics.get('tasks_completed', 0)
                success_rate = metrics.get('success_rate', 1.0)
                avg_time = metrics.get('average_response_time', 0)

                # 综合评分
                task_score = min(40, tasks * 2)
                success_score = success_rate * 40
                speed_score = max(0, 20 - avg_time * 10) if avg_time > 0 else 10
                total_score = task_score + success_score + speed_score

                level = 'beginner'
                if total_score >= 80:
                    level = 'expert'
                elif total_score >= 60:
                    level = 'advanced'
                elif total_score >= 40:
                    level = 'intermediate'

                evaluations.append({
                    'employee_id': emp_id,
                    'employee_type': emp.employee_type,
                    'capabilities': emp.capabilities,
                    'status': emp.status,
                    'tasks_completed': tasks,
                    'success_rate': round(success_rate * 100, 1),
                    'avg_response_time': avg_time,
                    'total_score': round(total_score, 1),
                    'level': level,
                    'cluster': emp.assigned_cluster
                })

            evaluations.sort(key=lambda x: -x['total_score'])

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'total_employees': len(evaluations),
                'evaluations': evaluations,
                'summary': {
                    'expert': sum(1 for e in evaluations if e['level'] == 'expert'),
                    'advanced': sum(1 for e in evaluations if e['level'] == 'advanced'),
                    'intermediate': sum(1 for e in evaluations if e['level'] == 'intermediate'),
                    'beginner': sum(1 for e in evaluations if e['level'] == 'beginner')
                }
            }
        except Exception as e:
            logger.error(f"评估员工能力失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 系统增强概览 ====================

    def get_enhancement_overview(self) -> Dict[str, Any]:
        """获取系统增强概览"""
        load_analysis = self.analyze_cluster_load()
        employee_eval = self.evaluate_all_employees()

        # 统计任务分配
        task_stats = {'total': 0, 'assigned': 0, 'queued': 0, 'completed': 0}
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT status, COUNT(*) FROM ai_task_assignments GROUP BY status')
                for status, count in cursor.fetchall():
                    task_stats['total'] += count
                    if status == 'assigned':
                        task_stats['assigned'] = count
                    elif status == 'queued':
                        task_stats['queued'] = count
                    elif status in ('completed', 'done'):
                        task_stats['completed'] = count
        except Exception:
            pass

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'load_analysis': {
                'clusters': load_analysis.get('clusters', []),
                'overloaded': load_analysis.get('overloaded_clusters', 0),
                'underutilized': load_analysis.get('underutilized_clusters', 0),
                'suggestions': load_analysis.get('suggestions', [])
            },
            'employee_evaluation': {
                'summary': employee_eval.get('summary', {}),
                'total_employees': employee_eval.get('total_employees', 0)
            },
            'task_assignment_stats': task_stats
        }


system_enhancement_engine = SystemEnhancementEngine()
