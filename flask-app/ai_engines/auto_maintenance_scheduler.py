#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动维护调度引擎 - AutoMaintenanceScheduler
负责定期执行维护检查，管理维护计划调度
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('auto_maintenance_scheduler')


class ScheduleType(Enum):
    """调度类型"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


class MaintenanceScheduler:
    """自动维护调度器"""
    
    def __init__(self):
        self.scheduler_id = "maint_scheduler_001"
        self.name = "自动维护调度引擎"
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self._db_path = self._find_db_path()
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        self._ensure_scheduler_tables()
        self._load_active_plans()
        
        logger.info(f"自动维护调度引擎已初始化: {self.name}")
    
    def _find_db_path(self) -> str:
        """查找数据库路径"""
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mtscos.db'),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p
        return search_paths[0]
    
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_scheduler_tables(self):
        """确保调度器表存在"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS maintenance_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        schedule_type TEXT DEFAULT 'daily',
                        schedule_cron TEXT,
                        schedule_hour INTEGER DEFAULT 2,
                        schedule_minute INTEGER DEFAULT 0,
                        schedule_weekday INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        check_categories TEXT,
                        last_run_time TEXT,
                        last_run_status TEXT,
                        last_run_report_id TEXT,
                        next_run_time TEXT,
                        total_runs INTEGER DEFAULT 0,
                        success_runs INTEGER DEFAULT 0,
                        failed_runs INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS maintenance_scheduler_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheduler_id TEXT UNIQUE NOT NULL,
                        status TEXT DEFAULT 'stopped',
                        is_running INTEGER DEFAULT 0,
                        active_plans INTEGER DEFAULT 0,
                        total_executions INTEGER DEFAULT 0,
                        last_heartbeat TEXT,
                        start_time TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
                
                conn.commit()
        except Exception as e:
            logger.error(f"创建调度器表失败: {e}")
    
    def _load_active_plans(self):
        """加载活跃的维护计划"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT plan_id, name, description, schedule_type,
                           schedule_hour, schedule_minute, schedule_weekday,
                           is_active, last_run_time, next_run_time
                    FROM maintenance_plans WHERE is_active = 1
                """)
                
                rows = cursor.fetchall()
                self.active_plans = {}
                for row in rows:
                    plan = {
                        'plan_id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'schedule_type': row[3],
                        'schedule_hour': row[4],
                        'schedule_minute': row[5],
                        'schedule_weekday': row[6],
                        'is_active': bool(row[7]),
                        'last_run_time': row[8],
                        'next_run_time': row[9]
                    }
                    self.active_plans[row[0]] = plan
                
                logger.info(f"加载了 {len(self.active_plans)} 个活跃维护计划")
        except Exception as e:
            logger.error(f"加载维护计划失败: {e}")
    
    def create_default_plans(self):
        """创建默认维护计划"""
        try:
            now = datetime.now().isoformat()
            
            default_plans = [
                {
                    'name': '每小时快速检查',
                    'description': '每小时执行一次快速系统健康检查，监控核心服务状态',
                    'schedule_type': 'hourly',
                    'schedule_hour': 0,
                    'schedule_minute': 0,
                    'categories': ['api_testing', 'network_testing', 'middleware_status']
                },
                {
                    'name': '每日全面维护',
                    'description': '每天凌晨2点执行全面系统维护检查',
                    'schedule_type': 'daily',
                    'schedule_hour': 2,
                    'schedule_minute': 0,
                    'categories': []
                },
                {
                    'name': '每周深度检查',
                    'description': '每周日凌晨3点执行深度系统检查和优化',
                    'schedule_type': 'weekly',
                    'schedule_hour': 3,
                    'schedule_minute': 0,
                    'schedule_weekday': 6,
                    'categories': []
                },
                {
                    'name': '月度安全审计',
                    'description': '每月1号凌晨1点执行全面安全审计',
                    'schedule_type': 'monthly',
                    'schedule_hour': 1,
                    'schedule_minute': 0,
                    'categories': ['data_security', 'permission_management', 'policy_rules']
                }
            ]
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                import uuid
                import json
                for plan_data in default_plans:
                    plan_id = f"maint_plan_{uuid.uuid4().hex[:12]}"
                    
                    # 检查是否已存在同名计划
                    cursor.execute("SELECT COUNT(*) FROM maintenance_plans WHERE name = ?", 
                                   (plan_data['name'],))
                    if cursor.fetchone()[0] > 0:
                        continue
                    
                    next_run = self._calculate_next_run(
                        plan_data['schedule_type'],
                        plan_data.get('schedule_hour', 2),
                        plan_data.get('schedule_minute', 0),
                        plan_data.get('schedule_weekday', 0)
                    )
                    
                    cursor.execute("""
                        INSERT INTO maintenance_plans (
                            plan_id, name, description, schedule_type,
                            schedule_hour, schedule_minute, schedule_weekday,
                            is_active, check_categories, next_run_time,
                            total_runs, success_runs, failed_runs,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, 0, 0, ?, ?)
                    """, (
                        plan_id,
                        plan_data['name'],
                        plan_data['description'],
                        plan_data['schedule_type'],
                        plan_data.get('schedule_hour', 2),
                        plan_data.get('schedule_minute', 0),
                        plan_data.get('schedule_weekday', 0),
                        json.dumps(plan_data.get('categories', []), ensure_ascii=False),
                        next_run.isoformat(),
                        now, now
                    ))
                
                conn.commit()
            
            self._load_active_plans()
            logger.info("默认维护计划创建完成")
            return True
        except Exception as e:
            logger.error(f"创建默认计划失败: {e}")
            return False
    
    def _calculate_next_run(self, schedule_type: str, hour: int = 2, 
                           minute: int = 0, weekday: int = 0) -> datetime:
        """计算下次运行时间"""
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
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行中")
            return False
        
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        self._update_scheduler_status('running', True)
        logger.info("自动维护调度引擎已启动")
        return True
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        self._stop_event.set()
        self.is_running = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        self._update_scheduler_status('stopped', False)
        logger.info("自动维护调度引擎已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        logger.info("调度器主循环开始")
        
        while not self._stop_event.is_set():
            try:
                self._update_heartbeat()
                self._check_and_execute_plans()
                
                # 每30秒检查一次
                for _ in range(30):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                time.sleep(10)
        
        logger.info("调度器主循环结束")
    
    def _check_and_execute_plans(self):
        """检查并执行到期的计划"""
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
                logger.info(f"执行维护计划: {plan['name']} ({plan_id})")
                self._execute_plan(plan_id, plan)
    
    def _execute_plan(self, plan_id: str, plan: Dict[str, Any]):
        """执行维护计划"""
        try:
            from ai_engines.comprehensive_maintenance_ai import get_comprehensive_maintenance_ai
            maint_ai = get_comprehensive_maintenance_ai()
            
            results = maint_ai.run_full_check()
            
            # 更新计划状态
            self._update_plan_after_run(plan_id, results, 'success')
            
            logger.info(f"维护计划执行成功: {plan['name']}, 通过率: {results['pass_rate']}%")
            return results
        
        except Exception as e:
            logger.error(f"维护计划执行失败: {e}")
            self._update_plan_after_run(plan_id, None, 'failed')
            return None
    
    def _update_plan_after_run(self, plan_id: str, results: Optional[Dict], status: str):
        """更新计划运行后状态"""
        try:
            now = datetime.now().isoformat()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 获取当前计划信息
                cursor.execute("""
                    SELECT schedule_type, schedule_hour, schedule_minute, schedule_weekday,
                           total_runs, success_runs, failed_runs
                    FROM maintenance_plans WHERE plan_id = ?
                """, (plan_id,))
                
                row = cursor.fetchone()
                if not row:
                    return
                
                total_runs = row[4] + 1
                success_runs = row[5] + (1 if status == 'success' else 0)
                failed_runs = row[6] + (1 if status == 'failed' else 0)
                
                # 计算下次运行时间
                next_run = self._calculate_next_run(row[0], row[1], row[2], row[3])
                
                report_id = results['check_id'] if results else None
                
                cursor.execute("""
                    UPDATE maintenance_plans SET
                        last_run_time = ?,
                        last_run_status = ?,
                        last_run_report_id = ?,
                        next_run_time = ?,
                        total_runs = ?,
                        success_runs = ?,
                        failed_runs = ?,
                        updated_at = ?
                    WHERE plan_id = ?
                """, (
                    now, status, report_id,
                    next_run.isoformat(),
                    total_runs, success_runs, failed_runs,
                    now, plan_id
                ))
                
                conn.commit()
            
            # 更新内存中的计划
            if plan_id in self.active_plans:
                self.active_plans[plan_id]['last_run_time'] = now
                self.active_plans[plan_id]['last_run_status'] = status
                self.active_plans[plan_id]['next_run_time'] = next_run.isoformat()
        
        except Exception as e:
            logger.error(f"更新计划状态失败: {e}")
    
    def _update_scheduler_status(self, status: str, is_running: bool):
        """更新调度器状态"""
        try:
            now = datetime.now().isoformat()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM maintenance_scheduler_status WHERE scheduler_id = ?
                """, (self.scheduler_id,))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    cursor.execute("""
                        UPDATE maintenance_scheduler_status SET
                            status = ?,
                            is_running = ?,
                            active_plans = ?,
                            last_heartbeat = ?,
                            updated_at = ?
                        WHERE scheduler_id = ?
                    """, (
                        status, 1 if is_running else 0,
                        len(self.active_plans),
                        now, now, self.scheduler_id
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO maintenance_scheduler_status (
                            scheduler_id, status, is_running, active_plans,
                            last_heartbeat, start_time, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.scheduler_id, status, 1 if is_running else 0,
                        len(self.active_plans),
                        now, now, now, now
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"更新调度器状态失败: {e}")
    
    def _update_heartbeat(self):
        """更新心跳"""
        try:
            now = datetime.now().isoformat()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE maintenance_scheduler_status SET
                        last_heartbeat = ?,
                        active_plans = ?,
                        updated_at = ?
                    WHERE scheduler_id = ?
                """, (
                    now, len(self.active_plans), now,
                    self.scheduler_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"更新心跳失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM maintenance_scheduler_status WHERE scheduler_id = ?
                """, (self.scheduler_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'scheduler_id': row[1],
                        'status': row[2],
                        'is_running': bool(row[3]),
                        'active_plans': row[4],
                        'total_executions': row[5],
                        'last_heartbeat': row[6],
                        'start_time': row[7],
                        'created_at': row[8],
                        'updated_at': row[9]
                    }
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
        
        return {
            'scheduler_id': self.scheduler_id,
            'status': 'unknown',
            'is_running': self.is_running,
            'active_plans': len(self.active_plans)
        }
    
    def get_plans(self) -> List[Dict[str, Any]]:
        """获取所有计划"""
        return list(self.active_plans.values())
    
    def trigger_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """手动触发计划执行"""
        if plan_id not in self.active_plans:
            logger.error(f"计划不存在: {plan_id}")
            return None
        
        plan = self.active_plans[plan_id]
        logger.info(f"手动触发维护计划: {plan['name']}")
        
        return self._execute_plan(plan_id, plan)


# 单例实例
_maintenance_scheduler = None


def get_maintenance_scheduler() -> MaintenanceScheduler:
    """获取维护调度器单例"""
    global _maintenance_scheduler
    if _maintenance_scheduler is None:
        _maintenance_scheduler = MaintenanceScheduler()
    return _maintenance_scheduler


if __name__ == '__main__':
    scheduler = get_maintenance_scheduler()
    print(f"调度器: {scheduler.name}")
    
    # 创建默认计划
    scheduler.create_default_plans()
    
    print(f"活跃计划数: {len(scheduler.active_plans)}")
    print()
    print("计划列表:")
    for plan in scheduler.get_plans():
        print(f"  - {plan['name']} ({plan['schedule_type']})")
        print(f"    下次运行: {plan.get('next_run_time', 'N/A')}")
    
    print()
    print("启动调度器...")
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止调度器...")
        scheduler.stop()
        print("调度器已停止")
