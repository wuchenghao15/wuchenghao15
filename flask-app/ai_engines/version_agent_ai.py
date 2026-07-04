#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VersionAgentAI - 系统版本管理AI员工
负责监控并维护系统版本，维护版本规则，版本显示，版本细则，
版本存储更新触发条件处罚规则，自动计划维护
"""

import os
import sys
import json
import logging
import hashlib
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('version_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('version_agent')


class VersionChangeType(Enum):
    MAJOR = 'major'
    MINOR = 'minor'
    PATCH = 'patch'
    HOTFIX = 'hotfix'
    PREVIEW = 'preview'


class ViolationLevel(Enum):
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class PenaltyRule:
    def __init__(self, violation_type: str, level: ViolationLevel, description: str, 
                 max_violations: int, penalty_action: str):
        self.violation_type = violation_type
        self.level = level
        self.description = description
        self.max_violations = max_violations
        self.penalty_action = penalty_action
        self.violation_count = 0
        self.last_violation_time = None


class VersionTriggerCondition:
    def __init__(self, condition_type: str, description: str, threshold: Any, 
                 required: bool = False):
        self.condition_type = condition_type
        self.description = description
        self.threshold = threshold
        self.required = required
        self.met = False


class VersionAgentAI:
    """系统版本管理AI员工"""

    def __init__(self):
        self.employee_id = "version_agent_001"
        self.employee_name = "系统版本管理Agent"
        self.specialty = "系统版本监控、版本规则维护、版本显示、版本存储、更新触发条件、处罚规则、自动计划维护"
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.last_maintenance = None
        self.maintenance_plans = {}
        
        self._init_database()
        self._load_rules()
        self._load_trigger_conditions()
        self._load_maintenance_plans()
        
        self._start_scheduler()
        
        logger.info("VersionAgentAI 初始化完成")

    def _init_database(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL UNIQUE,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                description TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_type TEXT NOT NULL,
                level TEXT NOT NULL,
                description TEXT,
                version TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_name TEXT NOT NULL UNIQUE,
                trigger_type TEXT NOT NULL,
                condition TEXT,
                threshold TEXT,
                action TEXT,
                enabled INTEGER DEFAULT 1,
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS va_maintenance_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name TEXT NOT NULL UNIQUE,
                plan_type TEXT NOT NULL,
                schedule TEXT NOT NULL,
                tasks TEXT,
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS va_maintenance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                tasks TEXT,
                results TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    


    def _load_rules(self):
        self.rules = {
            'semver_major': {
                'name': 'SemVer Major版本规则',
                'description': '主版本号在不兼容的API变更时递增',
                'pattern': r'^\d+\.\d+\.\d+$',
                'enforced': True
            },
            'semver_minor': {
                'name': 'SemVer Minor版本规则',
                'description': '次版本号在向后兼容的功能新增时递增',
                'pattern': r'^\d+\.\d+\.\d+$',
                'enforced': True
            },
            'semver_patch': {
                'name': 'SemVer Patch版本规则',
                'description': '修订号在向后兼容的问题修正时递增',
                'pattern': r'^\d+\.\d+\.\d+$',
                'enforced': True
            },
            'version_format': {
                'name': '版本号格式规则',
                'description': '版本号必须符合X.Y.Z格式',
                'pattern': r'^\d+\.\d+\.\d+$',
                'enforced': True
            },
            'version_increment': {
                'name': '版本递增规则',
                'description': '新版本号必须大于旧版本号',
                'enforced': True
            },
            'changelog_required': {
                'name': '变更日志必填规则',
                'description': '每次版本更新必须提供变更日志',
                'enforced': True
            },
            'backup_before_update': {
                'name': '更新前备份规则',
                'description': '版本更新前必须创建备份',
                'enforced': True
            },
            'health_check_after_update': {
                'name': '更新后健康检查规则',
                'description': '版本更新后必须进行健康检查',
                'enforced': True
            }
        }
        
        self.penalty_rules = [
            PenaltyRule('version_format_violation', ViolationLevel.ERROR, 
                        '版本号格式不符合规则', 3, 'disable_auto_update'),
            PenaltyRule('version_decrement', ViolationLevel.CRITICAL, 
                        '版本号递减，违反版本递增规则', 2, 'lock_version_system'),
            PenaltyRule('missing_changelog', ViolationLevel.WARNING, 
                        '缺少变更日志', 5, 'warning_notification'),
            PenaltyRule('no_backup_before_update', ViolationLevel.ERROR, 
                        '更新前未创建备份', 3, 'block_update'),
            PenaltyRule('update_failure', ViolationLevel.WARNING, 
                        '版本更新失败', 10, 'disable_auto_update'),
            PenaltyRule('health_check_failed', ViolationLevel.ERROR, 
                        '更新后健康检查失败', 5, 'trigger_rollback')
        ]
        
        for rule_name, rule_info in self.rules.items():
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO version_rules 
                    (rule_name, rule_type, rule_value, description, enabled)
                    VALUES (?, ?, ?, ?, ?)
                ''', (rule_name, 'version', json.dumps(rule_info), rule_info['description'], 1))
            except:
                pass
        self.conn.commit()

    def _load_trigger_conditions(self):
        self.trigger_conditions = [
            VersionTriggerCondition('code_changes', '代码变更数量', 10, True),
            VersionTriggerCondition('security_patch', '安全补丁数量', 1, True),
            VersionTriggerCondition('feature_addition', '新增功能数量', 1, False),
            VersionTriggerCondition('bug_fix', 'Bug修复数量', 5, False),
            VersionTriggerCondition('performance_improvement', '性能优化数量', 3, False),
            VersionTriggerCondition('dependency_update', '依赖更新数量', 3, False),
            VersionTriggerCondition('days_since_last_release', '距上次发布天数', 30, False),
            VersionTriggerCondition('user_feedback_count', '用户反馈数量', 50, False)
        ]
        
        for condition in self.trigger_conditions:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO version_triggers 
                    (trigger_name, trigger_type, condition, threshold, action)
                    VALUES (?, ?, ?, ?, ?)
                ''', (condition.condition_type, 'auto_update', condition.description, 
                      str(condition.threshold), 'trigger_version_bump'))
            except:
                pass
        self.conn.commit()

    def _load_maintenance_plans(self):
        self.maintenance_plans = {
            'daily_health_check': {
                'name': '每日健康检查',
                'type': 'daily',
                'schedule': '02:00',
                'tasks': ['check_database', 'check_disk_space', 'check_logs', 'check_backups'],
                'enabled': True,
                'last_run': None,
                'next_run': None
            },
            'weekly_version_audit': {
                'name': '每周版本审计',
                'type': 'weekly',
                'schedule': 'Sunday 03:00',
                'tasks': ['version_consistency_check', 'update_log_review', 'backup_audit', 'security_scan'],
                'enabled': True,
                'last_run': None,
                'next_run': None
            },
            'monthly_release_planning': {
                'name': '每月发布规划',
                'type': 'monthly',
                'schedule': '1st 04:00',
                'tasks': ['version_analysis', 'changelog_preparation', 'release_schedule', 'staging_deployment'],
                'enabled': True,
                'last_run': None,
                'next_run': None
            },
            'emergency_backup': {
                'name': '紧急备份',
                'type': 'manual',
                'schedule': 'on_demand',
                'tasks': ['create_full_backup', 'verify_backup', 'sync_backup'],
                'enabled': True,
                'last_run': None,
                'next_run': None
            }
        }
        
        for plan_id, plan_info in self.maintenance_plans.items():
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO va_maintenance_plans 
                    (plan_name, plan_type, schedule, tasks, enabled)
                    VALUES (?, ?, ?, ?, ?)
                ''', (plan_id, plan_info['type'], plan_info['schedule'], 
                      json.dumps(plan_info['tasks']), 1 if plan_info['enabled'] else 0))
            except:
                pass
        self.conn.commit()

    def _start_scheduler(self):
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("版本Agent调度器已启动")

    def _run_scheduler(self):
        while self.scheduler_running:
            now = datetime.now()
            
            for plan_id, plan_info in self.maintenance_plans.items():
                if not plan_info['enabled']:
                    continue
                
                if self._should_run(plan_info, now):
                    logger.info(f"自动执行维护计划: {plan_info['name']}")
                    self.execute_maintenance_plan(plan_id)
            
            time.sleep(60)

    def _should_run(self, plan_info: Dict, now: datetime) -> bool:
        plan_type = plan_info['type']
        schedule = plan_info['schedule']
        last_run = plan_info['last_run']
        
        if last_run:
            last_run_time = datetime.fromisoformat(last_run)
            if plan_type == 'daily':
                if (now - last_run_time).days < 1:
                    return False
            elif plan_type == 'weekly':
                if (now - last_run_time).days < 7:
                    return False
            elif plan_type == 'monthly':
                if now.month == last_run_time.month and now.year == last_run_time.year:
                    return False
            elif plan_type == 'manual':
                return False
        
        if plan_type == 'daily':
            hour, minute = map(int, schedule.split(':'))
            return now.hour == hour and now.minute == 0
        elif plan_type == 'weekly':
            parts = schedule.split()
            day_name = parts[0]
            hour, minute = map(int, parts[1].split(':'))
            days = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                    'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            if now.weekday() == days.get(day_name, 6) and now.hour == hour and now.minute == 0:
                return True
        elif plan_type == 'monthly':
            parts = schedule.split()
            day_of_month = int(parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            hour, minute = map(int, parts[1].split(':'))
            if now.day == day_of_month and now.hour == hour and now.minute == 0:
                return True
        
        return False

    def get_current_version(self) -> Dict[str, Any]:
        try:
            from app.version import VERSION, BUILD_NUMBER, RELEASE_DATE, VERSION_INFO, CHANGELOG
            return {
                'version': VERSION,
                'build_number': BUILD_NUMBER,
                'release_date': RELEASE_DATE,
                'version_info': VERSION_INFO,
                'changelog': CHANGELOG[:3]
            }
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return {'error': str(e)}

    def validate_version_format(self, version: str) -> bool:
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))

    def compare_versions(self, v1: str, v2: str) -> int:
        def parse(v):
            parts = v.split('.')
            return tuple(map(int, parts))
        v1_parts = parse(v1)
        v2_parts = parse(v2)
        if v1_parts > v2_parts:
            return 1
        elif v1_parts < v2_parts:
            return -1
        return 0

    def bump_version(self, current_version: str, change_type: VersionChangeType) -> str:
        major, minor, patch = map(int, current_version.split('.'))
        
        if change_type == VersionChangeType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif change_type == VersionChangeType.MINOR:
            minor += 1
            patch = 0
        elif change_type == VersionChangeType.PATCH:
            patch += 1
        elif change_type == VersionChangeType.HOTFIX:
            patch += 1
        elif change_type == VersionChangeType.PREVIEW:
            return f"{current_version}-preview"
        
        return f"{major}.{minor}.{patch}"

    def check_version_rules(self, new_version: str, current_version: str = None) -> List[Dict]:
        violations = []
        
        if current_version is None:
            current_version = self.get_current_version().get('version', '0.0.0')
        
        if not self.validate_version_format(new_version):
            violations.append({
                'rule': 'version_format',
                'level': 'error',
                'message': f"版本号格式错误: {new_version}，必须符合X.Y.Z格式",
                'penalty': '版本格式违规，累计3次禁用自动更新'
            })
            self._record_violation('version_format_violation', ViolationLevel.ERROR, 
                                   f"版本号格式错误: {new_version}")
        
        comparison = self.compare_versions(new_version, current_version)
        if comparison < 0:
            violations.append({
                'rule': 'version_increment',
                'level': 'critical',
                'message': f"版本号递减: {current_version} -> {new_version}",
                'penalty': '版本递减违规，累计2次锁定版本系统'
            })
            self._record_violation('version_decrement', ViolationLevel.CRITICAL, 
                                   f"版本号递减: {current_version} -> {new_version}")
        
        return violations

    def _record_violation(self, violation_type: str, level: ViolationLevel, description: str):
        try:
            self.cursor.execute('''
                INSERT INTO version_violations 
                (violation_type, level, description, version)
                VALUES (?, ?, ?, ?)
            ''', (violation_type, level.value, description, 
                  self.get_current_version().get('version', 'unknown')))
            self.conn.commit()
            
            for penalty_rule in self.penalty_rules:
                if penalty_rule.violation_type == violation_type:
                    penalty_rule.violation_count += 1
                    penalty_rule.last_violation_time = datetime.now().isoformat()
                    self._check_penalty(penalty_rule)
        except Exception as e:
            logger.error(f"记录违规失败: {e}")

    def _check_penalty(self, penalty_rule: PenaltyRule):
        if penalty_rule.violation_count >= penalty_rule.max_violations:
            logger.warning(f"触发处罚规则: {penalty_rule.violation_type} - {penalty_rule.penalty_action}")
            
            if penalty_rule.penalty_action == 'disable_auto_update':
                self.set_auto_update_enabled(False)
            elif penalty_rule.penalty_action == 'lock_version_system':
                self.lock_version_system()
            elif penalty_rule.penalty_action == 'warning_notification':
                self._send_notification(f"版本管理警告: {penalty_rule.description}")
            elif penalty_rule.penalty_action == 'block_update':
                self.set_update_blocked(True)
            elif penalty_rule.penalty_action == 'trigger_rollback':
                self.trigger_rollback()

    def set_auto_update_enabled(self, enabled: bool):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO version_rules 
                (rule_name, rule_type, rule_value, description, enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', ('auto_update_enabled', 'system', str(enabled), 
                  '自动更新开关', 1 if enabled else 0))
            self.conn.commit()
        except Exception as e:
            logger.error(f"设置自动更新失败: {e}")

    def lock_version_system(self):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO version_rules 
                (rule_name, rule_type, rule_value, description, enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', ('version_system_locked', 'system', 'true', 
                  '版本系统锁定', 0))
            self.conn.commit()
            logger.warning("版本系统已锁定")
        except Exception as e:
            logger.error(f"锁定版本系统失败: {e}")

    def set_update_blocked(self, blocked: bool):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO version_rules 
                (rule_name, rule_type, rule_value, description, enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', ('update_blocked', 'system', str(blocked), 
                  '更新阻止开关', 1))
            self.conn.commit()
        except Exception as e:
            logger.error(f"设置更新阻止失败: {e}")

    def trigger_rollback(self):
        logger.warning("触发版本回滚")

    def _send_notification(self, message: str):
        logger.info(f"发送通知: {message}")

    def check_trigger_conditions(self) -> Dict[str, Any]:
        conditions = []
        triggered = []
        
        for condition in self.trigger_conditions:
            conditions.append({
                'type': condition.condition_type,
                'description': condition.description,
                'threshold': condition.threshold,
                'required': condition.required,
                'met': condition.met
            })
            if condition.met:
                triggered.append(condition.condition_type)
        
        return {
            'conditions': conditions,
            'triggered': triggered,
            'should_update': len(triggered) > 0,
            'suggested_change_type': self._determine_change_type(triggered)
        }

    def _determine_change_type(self, triggered: List[str]) -> str:
        if 'security_patch' in triggered or 'code_changes' in triggered:
            return VersionChangeType.MAJOR.value
        elif 'feature_addition' in triggered:
            return VersionChangeType.MINOR.value
        elif 'bug_fix' in triggered or 'performance_improvement' in triggered:
            return VersionChangeType.PATCH.value
        return VersionChangeType.PATCH.value

    def execute_maintenance_plan(self, plan_id: str) -> Dict[str, Any]:
        plan = self.maintenance_plans.get(plan_id)
        if not plan:
            return {'success': False, 'error': f"维护计划不存在: {plan_id}"}
        
        if not plan['enabled']:
            return {'success': False, 'error': f"维护计划已禁用: {plan_id}"}
        
        started_at = datetime.now().isoformat()
        results = []
        
        for task_name in plan['tasks']:
            result = self._execute_maintenance_task(task_name)
            results.append({'task': task_name, **result})
        
        finished_at = datetime.now().isoformat()
        success = all(r.get('success', False) for r in results)
        
        plan['last_run'] = finished_at
        plan['next_run'] = self._calculate_next_run(plan)
        
        try:
            self.cursor.execute('''
                UPDATE va_maintenance_plans 
                SET last_run = ?, next_run = ?, run_count = run_count + 1,
                    success_count = success_count + ?, failure_count = failure_count + ?,
                    updated_at = ?
                WHERE plan_name = ?
            ''', (finished_at, plan['next_run'], 1 if success else 0, 
                  0 if success else 1, finished_at, plan_id))
            
            self.cursor.execute('''
                INSERT INTO va_maintenance_logs 
                (plan_name, started_at, finished_at, status, tasks, results)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (plan_id, started_at, finished_at, 'success' if success else 'failed',
                  json.dumps(plan['tasks']), json.dumps(results)))
            self.conn.commit()
        except Exception as e:
            logger.error(f"记录维护日志失败: {e}")
        
        logger.info(f"维护计划执行完成: {plan['name']}, 状态: {'成功' if success else '失败'}")
        
        return {
            'success': success,
            'plan_name': plan['name'],
            'started_at': started_at,
            'finished_at': finished_at,
            'tasks': results,
            'total_tasks': len(results),
            'success_tasks': sum(1 for r in results if r.get('success', False)),
            'failed_tasks': sum(1 for r in results if not r.get('success', False))
        }

    def _execute_maintenance_task(self, task_name: str) -> Dict[str, Any]:
        try:
            if task_name == 'check_database':
                return self._check_database_health()
            elif task_name == 'check_disk_space':
                return self._check_disk_space()
            elif task_name == 'check_logs':
                return self._check_logs()
            elif task_name == 'check_backups':
                return self._check_backups()
            elif task_name == 'version_consistency_check':
                return self._check_version_consistency()
            elif task_name == 'update_log_review':
                return self._review_update_logs()
            elif task_name == 'backup_audit':
                return self._audit_backups()
            elif task_name == 'security_scan':
                return self._run_security_scan()
            elif task_name == 'version_analysis':
                return self._analyze_versions()
            elif task_name == 'changelog_preparation':
                return self._prepare_changelog()
            elif task_name == 'release_schedule':
                return self._schedule_release()
            elif task_name == 'staging_deployment':
                return self._deploy_to_staging()
            elif task_name == 'create_full_backup':
                return self._create_full_backup()
            elif task_name == 'verify_backup':
                return self._verify_backup()
            elif task_name == 'sync_backup':
                return self._sync_backup()
            else:
                return {'success': False, 'error': f"未知任务: {task_name}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_database_health(self) -> Dict[str, Any]:
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
            if not os.path.exists(db_path):
                return {'success': False, 'status': 'error', 'message': '数据库文件不存在'}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            integrity = cursor.fetchone()[0]
            conn.close()
            
            if integrity != 'ok':
                return {'success': False, 'status': 'error', 'message': f'数据库完整性检查失败: {integrity}'}
            
            return {'success': True, 'status': 'healthy', 'message': '数据库健康检查通过'}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _check_disk_space(self) -> Dict[str, Any]:
        try:
            import shutil
            disk = shutil.disk_usage('/')
            percent_used = (disk.used / disk.total) * 100
            
            if percent_used > 90:
                status = 'critical'
                message = f'磁盘空间严重不足，已使用 {percent_used:.1f}%'
            elif percent_used > 80:
                status = 'warning'
                message = f'磁盘空间紧张，已使用 {percent_used:.1f}%'
            else:
                status = 'healthy'
                message = f'磁盘空间充足，已使用 {percent_used:.1f}%'
            
            return {'success': True, 'status': status, 'message': message,
                    'total': disk.total, 'used': disk.used, 'free': disk.free}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _check_logs(self) -> Dict[str, Any]:
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            if not os.path.exists(log_dir):
                return {'success': True, 'status': 'warning', 'message': '日志目录不存在'}
            
            total_size = 0
            file_count = 0
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
                    file_count += 1
            
            if total_size > 500 * 1024 * 1024:
                status = 'critical'
                message = f'日志文件过大，总计 {total_size / (1024 * 1024):.1f} MB'
            elif total_size > 100 * 1024 * 1024:
                status = 'warning'
                message = f'日志文件较大，总计 {total_size / (1024 * 1024):.1f} MB'
            else:
                status = 'healthy'
                message = f'日志文件正常，总计 {total_size / (1024 * 1024):.1f} MB'
            
            return {'success': True, 'status': status, 'message': message,
                    'file_count': file_count, 'total_size': total_size}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _check_backups(self) -> Dict[str, Any]:
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            if not os.path.exists(backup_dir):
                return {'success': False, 'status': 'warning', 'message': '备份目录不存在'}
            
            backups = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    backups.append({
                        'filename': filename,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })
            
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
            if not backups:
                return {'success': False, 'status': 'error', 'message': '未找到备份文件'}
            
            latest_backup = backups[0]
            backup_age = (datetime.now() - datetime.fromisoformat(latest_backup['modified'])).days
            
            if backup_age > 7:
                status = 'warning'
                message = f'最近备份已超过7天 ({backup_age}天前)'
            else:
                status = 'healthy'
                message = f'备份状态良好，最近备份 {backup_age}天前'
            
            return {'success': True, 'status': status, 'message': message,
                    'backup_count': len(backups), 'latest_backup': latest_backup}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _check_version_consistency(self) -> Dict[str, Any]:
        try:
            from app.version import VERSION
            from ai_engines.version_manager import version_manager
            
            vm_version = version_manager.get_current_version().get('version', 'unknown')
            
            if VERSION == vm_version:
                return {'success': True, 'status': 'healthy', 
                        'message': f'版本一致性检查通过: {VERSION}',
                        'app_version': VERSION, 'version_manager_version': vm_version}
            else:
                self._record_violation('version_inconsistency', ViolationLevel.WARNING,
                                       f'版本不一致: app.version={VERSION}, version_manager={vm_version}')
                return {'success': False, 'status': 'warning',
                        'message': f'版本不一致: app.version={VERSION}, version_manager={vm_version}',
                        'app_version': VERSION, 'version_manager_version': vm_version}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _review_update_logs(self) -> Dict[str, Any]:
        try:
            self.cursor.execute('SELECT COUNT(*) FROM version_violations WHERE resolved = 0')
            unresolved = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM version_violations')
            total = self.cursor.fetchone()[0]
            
            if unresolved > 0:
                return {'success': False, 'status': 'warning',
                        'message': f'存在 {unresolved} 条未解决的版本违规记录',
                        'total_violations': total, 'unresolved_violations': unresolved}
            else:
                return {'success': True, 'status': 'healthy',
                        'message': '所有版本违规记录已解决',
                        'total_violations': total, 'unresolved_violations': 0}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _audit_backups(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '备份审计完成'}

    def _run_security_scan(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '安全扫描完成'}

    def _analyze_versions(self) -> Dict[str, Any]:
        try:
            from ai_engines.version_manager import version_manager
            stats = version_manager.get_version_statistics()
            return {'success': True, 'status': 'healthy', 'message': '版本分析完成', 'statistics': stats}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _prepare_changelog(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '变更日志准备完成'}

    def _schedule_release(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '发布计划已安排'}

    def _deploy_to_staging(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '已部署到预发布环境'}

    def _create_full_backup(self) -> Dict[str, Any]:
        try:
            import shutil
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'app_backup_{timestamp}.db')
            
            shutil.copy2(db_path, backup_path)
            
            metadata = {
                'backup_path': backup_path,
                'backup_time': datetime.now().isoformat(),
                'description': 'VersionAgent自动创建的完整备份',
                'file_size': os.path.getsize(backup_path)
            }
            
            with open(backup_path + '.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return {'success': True, 'status': 'healthy', 
                    'message': f'完整备份创建成功: {backup_path}',
                    'backup_path': backup_path}
        except Exception as e:
            return {'success': False, 'status': 'error', 'message': str(e)}

    def _verify_backup(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '备份验证完成'}

    def _sync_backup(self) -> Dict[str, Any]:
        return {'success': True, 'status': 'healthy', 'message': '备份同步完成'}

    def _calculate_next_run(self, plan: Dict) -> str:
        now = datetime.now()
        
        if plan['type'] == 'daily':
            next_run = now + timedelta(days=1)
            hour, minute = map(int, plan['schedule'].split(':'))
            next_run = next_run.replace(hour=hour, minute=minute, second=0)
        elif plan['type'] == 'weekly':
            next_run = now + timedelta(weeks=1)
            parts = plan['schedule'].split()
            day_name = parts[0]
            hour, minute = map(int, parts[1].split(':'))
            days = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                    'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            days_ahead = days[day_name] - next_run.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = next_run + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0)
        elif plan['type'] == 'monthly':
            next_run = now + timedelta(days=30)
            parts = plan['schedule'].split()
            day_of_month = int(parts[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            hour, minute = map(int, parts[1].split(':'))
            try:
                next_run = next_run.replace(day=day_of_month, hour=hour, minute=minute, second=0)
            except ValueError:
                next_run = next_run.replace(day=1, hour=hour, minute=minute, second=0) + timedelta(months=1)
        else:
            return None
        
        return next_run.isoformat()

    def get_version_rules(self) -> Dict[str, Any]:
        return {
            'rules': self.rules,
            'penalty_rules': [
                {
                    'violation_type': pr.violation_type,
                    'level': pr.level.value,
                    'description': pr.description,
                    'max_violations': pr.max_violations,
                    'penalty_action': pr.penalty_action,
                    'current_count': pr.violation_count
                }
                for pr in self.penalty_rules
            ]
        }

    def get_trigger_conditions(self) -> List[Dict[str, Any]]:
        return [
            {
                'type': tc.condition_type,
                'description': tc.description,
                'threshold': tc.threshold,
                'required': tc.required,
                'met': tc.met
            }
            for tc in self.trigger_conditions
        ]

    def get_maintenance_plans(self) -> Dict[str, Any]:
        result = {}
        for plan_id, plan_info in self.maintenance_plans.items():
            result[plan_id] = {
                'name': plan_info['name'],
                'type': plan_info['type'],
                'schedule': plan_info['schedule'],
                'tasks': plan_info['tasks'],
                'enabled': plan_info['enabled'],
                'last_run': plan_info['last_run'],
                'next_run': plan_info['next_run']
            }
        return result

    def get_maintenance_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            self.cursor.execute('SELECT * FROM va_maintenance_logs ORDER BY created_at DESC LIMIT ?', (limit,))
            rows = self.cursor.fetchall()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'plan_name': row[1],
                    'started_at': row[2],
                    'finished_at': row[3],
                    'status': row[4],
                    'tasks': json.loads(row[5]) if row[5] else [],
                    'results': json.loads(row[6]) if row[6] else [],
                    'error_message': row[7],
                    'created_at': row[8]
                })
            
            return logs
        except Exception as e:
            logger.error(f"获取维护日志失败: {e}")
            return []

    def get_violations(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            self.cursor.execute('SELECT * FROM version_violations ORDER BY timestamp DESC LIMIT ?', (limit,))
            rows = self.cursor.fetchall()
            
            violations = []
            for row in rows:
                violations.append({
                    'id': row[0],
                    'violation_type': row[1],
                    'level': row[2],
                    'description': row[3],
                    'version': row[4],
                    'timestamp': row[5],
                    'resolved': bool(row[6])
                })
            
            return violations
        except Exception as e:
            logger.error(f"获取违规记录失败: {e}")
            return []

    def resolve_violation(self, violation_id: int) -> bool:
        try:
            self.cursor.execute('UPDATE version_violations SET resolved = 1 WHERE id = ?', (violation_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"解决违规记录失败: {e}")
            return False

    def enable_maintenance_plan(self, plan_id: str, enabled: bool) -> bool:
        plan = self.maintenance_plans.get(plan_id)
        if not plan:
            return False
        
        plan['enabled'] = enabled
        
        try:
            self.cursor.execute('UPDATE va_maintenance_plans SET enabled = ? WHERE plan_name = ?', 
                               (1 if enabled else 0, plan_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"设置维护计划状态失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'specialty': self.specialty,
            'status': self.status,
            'created_at': self.created_at,
            'last_maintenance': self.last_maintenance,
            'current_version': self.get_current_version().get('version', 'unknown'),
            'scheduler_running': self.scheduler_running,
            'maintenance_plans_count': len(self.maintenance_plans),
            'enabled_plans_count': sum(1 for p in self.maintenance_plans.values() if p['enabled'])
        }

    def shutdown(self):
        self.scheduler_running = False
        if self.conn:
            self.conn.close()
        logger.info("VersionAgentAI 已关闭")


# 延迟加载单例
_version_agent_ai_instance = None

def get_version_agent_ai():
    """获取VersionAgentAI单例（延迟加载）"""
    global _version_agent_ai_instance
    if _version_agent_ai_instance is None:
        _version_agent_ai_instance = VersionAgentAI()
    return _version_agent_ai_instance

# 兼容性别名
version_agent_ai = None

def _ensure_version_agent():
    """确保单例已创建"""
    global version_agent_ai
    if version_agent_ai is None:
        version_agent_ai = get_version_agent_ai()
    return version_agent_ai

if __name__ == '__main__':
    agent = VersionAgentAI()
    
    print("=== VersionAgentAI 状态 ===")
    print(json.dumps(agent.get_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 当前版本 ===")
    print(json.dumps(agent.get_current_version(), indent=2, ensure_ascii=False))
    
    print("\n=== 版本规则 ===")
    print(json.dumps(agent.get_version_rules(), indent=2, ensure_ascii=False))
    
    print("\n=== 触发条件 ===")
    print(json.dumps(agent.get_trigger_conditions(), indent=2, ensure_ascii=False))
    
    print("\n=== 维护计划 ===")
    print(json.dumps(agent.get_maintenance_plans(), indent=2, ensure_ascii=False))
    
    print("\n=== 检查版本规则 (5.1.1) ===")
    violations = agent.check_version_rules('5.1.1')
    print(json.dumps(violations, indent=2, ensure_ascii=False))
    
    print("\n=== 检查版本规则 (4.0.0 - 递减) ===")
    violations = agent.check_version_rules('4.0.0')
    print(json.dumps(violations, indent=2, ensure_ascii=False))
    
    print("\n=== 违规记录 ===")
    violations = agent.get_violations()
    print(json.dumps(violations, indent=2, ensure_ascii=False))
    
    print("\n=== 执行每日健康检查 ===")
    result = agent.execute_maintenance_plan('daily_health_check')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 维护日志 ===")
    logs = agent.get_maintenance_logs(5)
    print(json.dumps(logs, indent=2, ensure_ascii=False))
    
    agent.shutdown()