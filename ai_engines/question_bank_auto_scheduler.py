#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库自动维护调度器 - QuestionBankAutoScheduler
负责定期执行题库维护任务，包括：
- 自动扩充题库（历年真题、高频练习题、竞赛题、自主招生题、政治题、K12题、听力题）
- 题库整理分类
- 质量检查和去重
- 利用AI能力自动生成和维护题库
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('question_bank_auto_scheduler')


class ScheduleType:
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class QuestionBankAutoScheduler:
    """题库自动维护调度器"""
    
    def __init__(self):
        self.scheduler_id = "qbank_scheduler_001"
        self.name = "题库自动维护调度器"
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self._db_path = self._find_db_path()
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        self._ensure_scheduler_tables()
        self._load_active_plans()
        self._create_default_plans_if_empty()
        
        logger.info(f"题库自动维护调度器已初始化: {self.name}, {len(self.active_plans)} 个活跃计划")
    
    def _find_db_path(self) -> str:
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mtscos.db'),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p
        return search_paths[0]
    
    def _get_db_connection(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_scheduler_tables(self):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS question_bank_schedule_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT UNIQUE NOT NULL,
                        plan_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        subject TEXT,
                        source_type TEXT,
                        target_count INTEGER DEFAULT 50,
                        schedule_type TEXT DEFAULT 'daily',
                        schedule_hour INTEGER DEFAULT 2,
                        schedule_minute INTEGER DEFAULT 0,
                        schedule_weekday INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        last_run_time TEXT,
                        last_run_status TEXT,
                        last_run_result TEXT,
                        next_run_time TEXT,
                        total_runs INTEGER DEFAULT 0,
                        success_runs INTEGER DEFAULT 0,
                        failed_runs INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS question_bank_schedule_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        plan_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT,
                        result TEXT,
                        execution_time REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
        except Exception as e:
            logger.error(f"创建题库调度器表失败: {e}")
    
    def _load_active_plans(self):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT plan_id, plan_name, task_type, subject, source_type,
                           target_count, schedule_type, schedule_hour, schedule_minute,
                           schedule_weekday, is_active, last_run_time, next_run_time,
                           total_runs, success_runs, failed_runs
                    FROM question_bank_schedule_plans WHERE is_active = 1
                """)
                
                rows = cursor.fetchall()
                self.active_plans = {}
                for row in rows:
                    plan = {
                        'plan_id': row[0],
                        'plan_name': row[1],
                        'task_type': row[2],
                        'subject': row[3],
                        'source_type': row[4],
                        'target_count': row[5],
                        'schedule_type': row[6],
                        'schedule_hour': row[7],
                        'schedule_minute': row[8],
                        'schedule_weekday': row[9],
                        'is_active': bool(row[10]),
                        'last_run_time': row[11],
                        'next_run_time': row[12],
                        'total_runs': row[13],
                        'success_runs': row[14],
                        'failed_runs': row[15]
                    }
                    self.active_plans[row[0]] = plan
                
                logger.info(f"加载了 {len(self.active_plans)} 个题库维护计划")
        except Exception as e:
            logger.error(f"加载题库维护计划失败: {e}")
    
    def _create_default_plans_if_empty(self):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM question_bank_schedule_plans")
                if cursor.fetchone()[0] > 0:
                    return
                
                now = datetime.now().isoformat()
                
                default_plans = [
                    {
                        'plan_name': '每日题库扩充',
                        'task_type': 'expand_questions',
                        'subject': 'all',
                        'source_type': 'ai_generated',
                        'target_count': 100,
                        'schedule_type': 'daily',
                        'schedule_hour': 2,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每日政治题更新',
                        'task_type': 'expand_questions',
                        'subject': 'politics',
                        'source_type': 'politics_new',
                        'target_count': 50,
                        'schedule_type': 'daily',
                        'schedule_hour': 3,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每日K12题库扩充',
                        'task_type': 'expand_questions',
                        'subject': 'k12',
                        'source_type': 'k12',
                        'target_count': 80,
                        'schedule_type': 'daily',
                        'schedule_hour': 4,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每周听力题扩充',
                        'task_type': 'expand_questions',
                        'subject': 'listening',
                        'source_type': 'ai_generated',
                        'target_count': 60,
                        'schedule_type': 'weekly',
                        'schedule_hour': 5,
                        'schedule_minute': 0,
                        'schedule_weekday': 6
                    },
                    {
                        'plan_name': '每周真题补充',
                        'task_type': 'expand_questions',
                        'subject': 'all',
                        'source_type': 'past_exam',
                        'target_count': 150,
                        'schedule_type': 'weekly',
                        'schedule_hour': 6,
                        'schedule_minute': 0,
                        'schedule_weekday': 0
                    },
                    {
                        'plan_name': '每周题库整理',
                        'task_type': 'organize_questions',
                        'subject': 'all',
                        'source_type': 'ai_generated',
                        'target_count': 500,
                        'schedule_type': 'weekly',
                        'schedule_hour': 7,
                        'schedule_minute': 0,
                        'schedule_weekday': 6
                    },
                    {
                        'plan_name': '每日质量检查',
                        'task_type': 'quality_check',
                        'subject': 'all',
                        'source_type': 'ai_generated',
                        'target_count': 200,
                        'schedule_type': 'daily',
                        'schedule_hour': 1,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每月竞赛题更新',
                        'task_type': 'expand_questions',
                        'subject': 'all',
                        'source_type': 'competition',
                        'target_count': 200,
                        'schedule_type': 'monthly',
                        'schedule_hour': 8,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每月自主招生题更新',
                        'task_type': 'expand_questions',
                        'subject': 'k12',
                        'source_type': 'independent_recruitment',
                        'target_count': 100,
                        'schedule_type': 'monthly',
                        'schedule_hour': 9,
                        'schedule_minute': 0
                    },
                    {
                        'plan_name': '每小时快速检查',
                        'task_type': 'quality_check',
                        'subject': 'all',
                        'source_type': 'ai_generated',
                        'target_count': 50,
                        'schedule_type': 'hourly',
                        'schedule_hour': 0,
                        'schedule_minute': 0
                    }
                ]
                
                for plan_data in default_plans:
                    plan_id = f"qbank_plan_{uuid.uuid4().hex[:12]}"
                    
                    next_run = self._calculate_next_run(
                        plan_data['schedule_type'],
                        plan_data.get('schedule_hour', 2),
                        plan_data.get('schedule_minute', 0),
                        plan_data.get('schedule_weekday', 0)
                    )
                    
                    cursor.execute("""
                        INSERT INTO question_bank_schedule_plans (
                            plan_id, plan_name, task_type, subject, source_type,
                            target_count, schedule_type, schedule_hour, schedule_minute,
                            schedule_weekday, is_active, next_run_time,
                            total_runs, success_runs, failed_runs,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0, 0, 0, ?, ?)
                    """, (
                        plan_id,
                        plan_data['plan_name'],
                        plan_data['task_type'],
                        plan_data['subject'],
                        plan_data['source_type'],
                        plan_data['target_count'],
                        plan_data['schedule_type'],
                        plan_data.get('schedule_hour', 2),
                        plan_data.get('schedule_minute', 0),
                        plan_data.get('schedule_weekday', 0),
                        next_run.isoformat(),
                        now, now
                    ))
                
                conn.commit()
            self._load_active_plans()
            logger.info("题库维护默认计划创建完成")
        except Exception as e:
            logger.error(f"创建题库默认计划失败: {e}")
    
    def _calculate_next_run(self, schedule_type: str, hour: int = 2, 
                           minute: int = 0, weekday: int = 0) -> datetime:
        now = datetime.now()
        
        if schedule_type == 'hourly':
            next_run = now.replace(minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
        
        elif schedule_type == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule_type == 'weekly':
            days_ahead = weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        
        elif schedule_type == 'monthly':
            if now.day >= 1:
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                next_run = datetime(next_year, next_month, 1, hour, minute, 0)
            else:
                next_run = now.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    def start(self):
        if self.is_running:
            logger.warning("题库调度器已经在运行中")
            return False
        
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        logger.info("题库自动维护调度器已启动")
        return True
    
    def stop(self):
        if not self.is_running:
            return
        
        self._stop_event.set()
        self.is_running = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("题库自动维护调度器已停止")
    
    def _run_scheduler(self):
        logger.info("题库调度器主循环开始")
        
        while not self._stop_event.is_set():
            try:
                self._check_and_execute_plans()
                
                for _ in range(60):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"题库调度器循环异常: {e}")
                time.sleep(10)
        
        logger.info("题库调度器主循环结束")
    
    def _check_and_execute_plans(self):
        now = datetime.now()
        
        for plan_id, plan in list(self.active_plans.items()):
            if not plan.get('is_active', True):
                continue
            
            next_run_str = plan.get('next_run_time')
            if not next_run_str:
                continue
            
            try:
                next_run = datetime.fromisoformat(next_run_str)
            except:
                continue
            
            if now >= next_run:
                logger.info(f"执行题库维护计划: {plan['plan_name']} ({plan_id})")
                self._execute_plan(plan_id, plan)
    
    def _execute_plan(self, plan_id: str, plan: Dict[str, Any]):
        start_time = time.time()
        start_time_str = datetime.now().isoformat()
        
        try:
            result = self._dispatch_task(plan)
            
            execution_time = time.time() - start_time
            status = 'success' if result.get('success', False) else 'failed'
            
            self._record_history(plan_id, plan, start_time_str, execution_time, status, result)
            self._update_plan_after_run(plan_id, plan, status, result, execution_time)
            
            logger.info(f"题库维护计划执行{'成功' if status == 'success' else '失败'}: {plan['plan_name']}, "
                        f"耗时: {execution_time:.2f}s, 结果: {result.get('message', '')}")
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            result = {"success": False, "error": str(e), "message": f"执行异常: {e}"}
            
            self._record_history(plan_id, plan, start_time_str, execution_time, 'failed', result)
            self._update_plan_after_run(plan_id, plan, 'failed', result, execution_time)
            
            logger.error(f"题库维护计划执行异常: {plan['plan_name']}, 错误: {e}")
            return result
    
    def _dispatch_task(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        task_data = {
            "task_type": plan['task_type'],
            "subject": plan['subject'],
            "source_type": plan['source_type'],
            "target_count": plan['target_count'],
            "schedule_plan_id": plan['plan_id'],
            "schedule_plan_name": plan['plan_name']
        }
        
        try:
            from ai_engines.ai_employee_manager import AIEmployeeManager
            manager = AIEmployeeManager.get_instance()
            
            if manager:
                result = manager.auto_assign_task(task_data)
                return result
            
            logger.warning("AI员工管理器未初始化，使用直接执行模式")
            
            return self._execute_task_directly(task_data)
        
        except Exception as e:
            logger.error(f"任务分派失败: {e}")
            return self._execute_task_directly(task_data)
    
    def _execute_task_directly(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get("task_type", "expand_questions")
        subject = task_data.get("subject", "all")
        source_type = task_data.get("source_type", "ai_generated")
        target_count = int(task_data.get("target_count", 50))
        
        try:
            if subject == 'politics' or (subject == 'all' and source_type == 'politics_new'):
                from ai_engines.politics_question_employee import PoliticsQuestionEmployee
                employee = PoliticsQuestionEmployee('temp_pol', '临时政治员工', 5)
                result = employee.execute_task({
                    "task_type": "generate_questions",
                    "count": target_count,
                    "question_type": "all",
                    "difficulty": "medium",
                    "category": "current_affairs" if source_type == 'politics_new' else "theory"
                })
            
            elif subject == 'k12' or (subject == 'all' and source_type in ['k12', 'independent_recruitment']):
                from ai_engines.k12_question_employee import K12QuestionEmployee
                employee = K12QuestionEmployee('temp_k12', '临时K12员工', 5)
                result = employee.execute_task({
                    "task_type": "generate_questions",
                    "subject": "math",
                    "grade": "senior_high",
                    "question_type": "all",
                    "difficulty": "medium",
                    "source_type": source_type if source_type in ['competition', 'independent_recruitment'] else 'past_exam'
                })
            
            elif subject == 'listening':
                from ai_engines.listening_question_employee import ListeningQuestionEmployee
                employee = ListeningQuestionEmployee('temp_list', '临时听力员工', 5)
                result = employee.execute_task({
                    "task_type": "generate_questions",
                    "count": target_count,
                    "language": "all"
                })
            
            else:
                from ai_engines.question_bank_maintenance_employee import QuestionBankMaintenanceEmployee
                employee = QuestionBankMaintenanceEmployee('temp_qbm', '临时题库维护员工', 5)
                result = employee.execute_task(task_data)
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"直接执行任务失败: {e}"}
    
    def _record_history(self, plan_id: str, plan: Dict, start_time: str, 
                       execution_time: float, status: str, result: Dict):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO question_bank_schedule_history (
                        plan_id, plan_name, task_type, start_time, end_time,
                        status, result, execution_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_id,
                    plan['plan_name'],
                    plan['task_type'],
                    start_time,
                    datetime.now().isoformat(),
                    status,
                    json.dumps(result, ensure_ascii=False),
                    execution_time
                ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"记录执行历史失败: {e}")
    
    def _update_plan_after_run(self, plan_id: str, plan: Dict, status: str, 
                               result: Dict, execution_time: float):
        try:
            now = datetime.now()
            
            next_run = self._calculate_next_run(
                plan['schedule_type'],
                plan.get('schedule_hour', 2),
                plan.get('schedule_minute', 0),
                plan.get('schedule_weekday', 0)
            )
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE question_bank_schedule_plans SET
                        last_run_time = ?,
                        last_run_status = ?,
                        last_run_result = ?,
                        next_run_time = ?,
                        total_runs = total_runs + 1,
                        success_runs = success_runs + ?,
                        failed_runs = failed_runs + ?,
                        updated_at = ?
                    WHERE plan_id = ?
                """, (
                    now.isoformat(),
                    status,
                    json.dumps(result, ensure_ascii=False),
                    next_run.isoformat(),
                    1 if status == 'success' else 0,
                    1 if status == 'failed' else 0,
                    now.isoformat(),
                    plan_id
                ))
                
                conn.commit()
            
            self._load_active_plans()
            
        except Exception as e:
            logger.error(f"更新计划状态失败: {e}")
    
    def run_plan_now(self, plan_id: str) -> Dict[str, Any]:
        if plan_id not in self.active_plans:
            return {"success": False, "message": f"未找到计划: {plan_id}"}
        
        plan = self.active_plans[plan_id]
        logger.info(f"手动执行题库维护计划: {plan['plan_name']}")
        return self._execute_plan(plan_id, plan)
    
    def get_all_plans(self) -> Dict[str, Any]:
        return {
            "success": True,
            "total": len(self.active_plans),
            "plans": list(self.active_plans.values())
        }
    
    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        if plan_id not in self.active_plans:
            return {"success": False, "message": f"未找到计划: {plan_id}"}
        
        return {"success": True, "plan": self.active_plans[plan_id]}
    
    def update_plan(self, plan_id: str, updates: Dict) -> Dict[str, Any]:
        if plan_id not in self.active_plans:
            return {"success": False, "message": f"未找到计划: {plan_id}"}
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = []
                update_values = []
                
                if 'plan_name' in updates:
                    update_fields.append('plan_name = ?')
                    update_values.append(updates['plan_name'])
                if 'task_type' in updates:
                    update_fields.append('task_type = ?')
                    update_values.append(updates['task_type'])
                if 'subject' in updates:
                    update_fields.append('subject = ?')
                    update_values.append(updates['subject'])
                if 'source_type' in updates:
                    update_fields.append('source_type = ?')
                    update_values.append(updates['source_type'])
                if 'target_count' in updates:
                    update_fields.append('target_count = ?')
                    update_values.append(updates['target_count'])
                if 'schedule_type' in updates:
                    update_fields.append('schedule_type = ?')
                    update_values.append(updates['schedule_type'])
                if 'schedule_hour' in updates:
                    update_fields.append('schedule_hour = ?')
                    update_values.append(updates['schedule_hour'])
                if 'schedule_minute' in updates:
                    update_fields.append('schedule_minute = ?')
                    update_values.append(updates['schedule_minute'])
                if 'schedule_weekday' in updates:
                    update_fields.append('schedule_weekday = ?')
                    update_values.append(updates['schedule_weekday'])
                if 'is_active' in updates:
                    update_fields.append('is_active = ?')
                    update_values.append(1 if updates['is_active'] else 0)
                
                update_fields.append('updated_at = ?')
                update_values.append(datetime.now().isoformat())
                update_values.append(plan_id)
                
                if update_fields:
                    cursor.execute(f"""
                        UPDATE question_bank_schedule_plans SET
                            {', '.join(update_fields)}
                        WHERE plan_id = ?
                    """, tuple(update_values))
                    
                    conn.commit()
            
            self._load_active_plans()
            return {"success": True, "message": "计划更新成功", "plan": self.active_plans[plan_id]}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_plan(self, plan_id: str) -> Dict[str, Any]:
        if plan_id not in self.active_plans:
            return {"success": False, "message": f"未找到计划: {plan_id}"}
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM question_bank_schedule_plans WHERE plan_id = ?", (plan_id,))
                conn.commit()
            
            del self.active_plans[plan_id]
            return {"success": True, "message": "计划删除成功"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_plan(self, plan_data: Dict) -> Dict[str, Any]:
        try:
            plan_id = f"qbank_plan_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            
            next_run = self._calculate_next_run(
                plan_data.get('schedule_type', 'daily'),
                plan_data.get('schedule_hour', 2),
                plan_data.get('schedule_minute', 0),
                plan_data.get('schedule_weekday', 0)
            )
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO question_bank_schedule_plans (
                        plan_id, plan_name, task_type, subject, source_type,
                        target_count, schedule_type, schedule_hour, schedule_minute,
                        schedule_weekday, is_active, next_run_time,
                        total_runs, success_runs, failed_runs,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0, 0, 0, ?, ?)
                """, (
                    plan_id,
                    plan_data['plan_name'],
                    plan_data['task_type'],
                    plan_data.get('subject', 'all'),
                    plan_data.get('source_type', 'ai_generated'),
                    plan_data.get('target_count', 50),
                    plan_data.get('schedule_type', 'daily'),
                    plan_data.get('schedule_hour', 2),
                    plan_data.get('schedule_minute', 0),
                    plan_data.get('schedule_weekday', 0),
                    next_run.isoformat(),
                    now, now
                ))
                
                conn.commit()
            
            self._load_active_plans()
            return {"success": True, "message": "计划创建成功", "plan": self.active_plans[plan_id]}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_history(self, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, plan_id, plan_name, task_type, start_time, end_time,
                           status, result, execution_time
                    FROM question_bank_schedule_history
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                history = []
                for row in rows:
                    history.append({
                        'id': row[0],
                        'plan_id': row[1],
                        'plan_name': row[2],
                        'task_type': row[3],
                        'start_time': row[4],
                        'end_time': row[5],
                        'status': row[6],
                        'result': json.loads(row[7]) if row[7] else None,
                        'execution_time': row[8]
                    })
                
                return {"success": True, "total": len(history), "history": history}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "success": True,
            "scheduler_id": self.scheduler_id,
            "name": self.name,
            "is_running": self.is_running,
            "active_plans": len(self.active_plans),
            "total_plans": len(self.active_plans),
            "execution_history_count": len(self.execution_history)
        }


_scheduler_instance = None

def get_question_bank_auto_scheduler() -> QuestionBankAutoScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = QuestionBankAutoScheduler()
    return _scheduler_instance

def init_question_bank_auto_scheduler():
    scheduler = get_question_bank_auto_scheduler()
    scheduler.start()
    logger.info("题库自动维护调度器初始化完成")