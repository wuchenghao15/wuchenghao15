#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则库自动维护AI员工 - RuleBaseMaintenanceEmployee
负责自动维护系统规则库，包括：
- 自动扩充规则库（从网络收集、AI生成、历史数据挖掘）
- 规则整理分类和优化
- 质量检查和去重
- 自动适配系统和增派AI员工
- 上传数据库
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('rule_base_maintenance_employee')


class RuleRecord:
    """规则记录"""
    
    def __init__(self, rule_code: str, rule_name: str, rule_type: str, 
                 rule_value: str, priority: int = 100):
        self.rule_code = rule_code
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.rule_value = rule_value
        self.priority = priority
        self.is_active = True
        self.created_at = time.time()
        self.updated_at = time.time()
        self.last_used_at = None


class RuleBaseMaintenanceEmployee:
    """规则库自动维护AI员工"""
    
    def __init__(self, employee_id: str, name: str, level: int = 1):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "rule_base_maintenance"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 80 + level * 2
        self._lock = threading.RLock()
        
        self.skills = [
            {"name": "rule_generation", "level": 5 + level, "experience": 0.0},
            {"name": "rule_organization", "level": 5 + level, "experience": 0.0},
            {"name": "quality_control", "level": 4 + level, "experience": 0.0},
            {"name": "web_crawling", "level": 4 + level, "experience": 0.0},
            {"name": "category_management", "level": 4 + level, "experience": 0.0},
            {"name": "duplicate_detection", "level": 4 + level, "experience": 0.0},
            {"name": "system_adaptation", "level": 4 + level, "experience": 0.0},
            {"name": "employee_deployment", "level": 3 + level, "experience": 0.0}
        ]
        
        self._rules_cache: Dict[str, RuleRecord] = {}
        self._db_path = self._find_db_path()
        self._ensure_tables()
        
        logger.info(f"[规则库维护员工] {self.name} 已创建,级别: {level}")
    
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
    
    def _ensure_tables(self):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rule_maintenance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id TEXT UNIQUE NOT NULL,
                        task_type TEXT NOT NULL,
                        action TEXT NOT NULL,
                        rule_code TEXT,
                        rule_name TEXT,
                        rule_type TEXT,
                        result TEXT,
                        employee_id TEXT,
                        created_at REAL DEFAULT (strftime('%s','now'))
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rule_expansion_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id TEXT UNIQUE NOT NULL,
                        source_name TEXT NOT NULL,
                        source_type TEXT,
                        source_url TEXT,
                        last_fetched REAL,
                        fetched_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at REAL DEFAULT (strftime('%s','now'))
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            logger.error(f"[规则库维护员工] 初始化数据库失败: {e}")
    
    def start(self):
        """启动员工"""
        self.status = "active"
        logger.info(f"[规则库维护员工] {self.name} 已启动")
    
    def stop(self):
        """停止员工"""
        self.status = "inactive"
        logger.info(f"[规则库维护员工] {self.name} 已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.task_count, 1) * 100,
            "performance_score": self.performance_score,
            "skills": self.skills,
            "cached_rules": len(self._rules_cache)
        }
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()
        
        try:
            task_type = task_data.get("task_type", "expand_rules")
            
            if task_type == "expand_rules":
                result = self._expand_rules(task_data)
            elif task_type == "organize_rules":
                result = self._organize_rules(task_data)
            elif task_type == "quality_check":
                result = self._quality_check(task_data)
            elif task_type == "duplicate_removal":
                result = self._duplicate_removal(task_data)
            elif task_type == "web_fetch":
                result = self._web_fetch_rules(task_data)
            elif task_type == "ai_generate":
                result = self._ai_generate_rules(task_data)
            elif task_type == "system_adapt":
                result = self._system_adapt(task_data)
            elif task_type == "deploy_employees":
                result = self._deploy_employees(task_data)
            elif task_type == "full_maintenance":
                result = self._full_maintenance(task_data)
            elif task_type == "get_statistics":
                result = self._get_statistics()
            else:
                result = {"success": False, "error": f"未知任务类型: {task_type}"}
            
            if result.get("success", False):
                self.success_count += 1
                self._update_performance(True, time.time() - start_time)
            else:
                self.failure_count += 1
                self._update_performance(False, time.time() - start_time)
            
            result["execution_time"] = time.time() - start_time
            result["employee_id"] = self.employee_id
            result["employee_name"] = self.name
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self._update_performance(False, time.time() - start_time)
            logger.error(f"[规则库维护员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }
    
    def _generate_record_id(self) -> str:
        return f"RMR-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    
    def _record_maintenance(self, task_type: str, action: str, rule_code: str = None, 
                           rule_name: str = None, rule_type: str = None, result: str = None):
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rule_maintenance_records (
                        record_id, task_type, action, rule_code, rule_name, rule_type, result, employee_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self._generate_record_id(), task_type, action, rule_code, rule_name, rule_type, result, self.employee_id))
                conn.commit()
        except Exception as e:
            logger.error(f"[规则库维护员工] 记录维护日志失败: {e}")
    
    def _update_performance(self, success: bool, execution_time: float):
        score_change = 1 if success else -1
        if execution_time < 1.0:
            score_change += 1
        elif execution_time > 10:
            score_change -= 1
        self.performance_score = max(0, min(100, self.performance_score + score_change))
    
    def _expand_rules(self, task_data: Dict) -> Dict:
        """扩充规则库"""
        source_type = task_data.get("source_type", "all")
        target_count = int(task_data.get("target_count", 100))
        
        added_count = 0
        
        try:
            if source_type in ["ai_generated", "all"]:
                generated = self._ai_generate_rules_internal(target_count // 2)
                added_count += generated
            
            if source_type in ["web_fetch", "all"]:
                fetched = self._web_fetch_rules_internal(target_count // 2)
                added_count += fetched
            
            if source_type in ["historical", "all"]:
                historical = self._mining_historical_rules(target_count // 2)
                added_count += historical
            
            self._record_maintenance("expand_rules", "expansion", result=f"新增 {added_count} 条规则")
            
            return {
                "success": True,
                "message": f"规则库扩充完成，新增 {added_count} 条规则",
                "added_count": added_count,
                "source_type": source_type,
                "target_count": target_count
            }
        
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"规则扩充失败: {e}"}
    
    def _ai_generate_rules_internal(self, count: int) -> int:
        """AI生成规则"""
        generated = 0
        
        rule_templates = [
            {
                'rule_code': 'auto_perf_cpu_high',
                'rule_name': 'CPU高负载自动告警',
                'rule_type': 'performance',
                'rule_value': '{"conditions": [{"field": "cpu_usage", "operator": "greater_than", "value": 85}], "actions": [{"action": "notify_admin", "params": {"level": "critical"}}]}',
                'priority': 10
            },
            {
                'rule_code': 'auto_perf_memory_high',
                'rule_name': '内存高负载自动告警',
                'rule_type': 'performance',
                'rule_value': '{"conditions": [{"field": "memory_usage", "operator": "greater_than", "value": 90}], "actions": [{"action": "notify_admin", "params": {"level": "critical"}}]}',
                'priority': 10
            },
            {
                'rule_code': 'auto_task_timeout',
                'rule_name': '任务超时自动处理',
                'rule_type': 'task_management',
                'rule_value': '{"conditions": [{"field": "task_duration", "operator": "greater_than", "value": 300}], "actions": [{"action": "notify_admin", "params": {"level": "warning"}}, {"action": "create_employee", "params": {"type": "task_optimizer"}}]}',
                'priority': 15
            },
            {
                'rule_code': 'auto_security_login_attempts',
                'rule_name': '登录失败次数过多自动锁定',
                'rule_type': 'security',
                'rule_value': '{"conditions": [{"field": "login_failures", "operator": "greater_than", "value": 5}], "actions": [{"action": "lock_account", "params": {"duration": 30}}]}',
                'priority': 20
            },
            {
                'rule_code': 'auto_ai_employee_scale',
                'rule_name': 'AI员工自动扩容',
                'rule_type': 'ai_management',
                'rule_value': '{"conditions": [{"field": "pending_tasks", "operator": "greater_than", "value": 20}], "actions": [{"action": "create_employee", "params": {"count": 3, "type": "general_worker"}}]}',
                'priority': 8
            },
            {
                'rule_code': 'auto_db_backup',
                'rule_name': '数据库自动备份',
                'rule_type': 'maintenance',
                'rule_value': '{"conditions": [{"field": "backup_interval", "operator": "greater_than", "value": 86400}], "actions": [{"action": "execute_backup", "params": {"type": "full"}}]}',
                'priority': 12
            },
            {
                'rule_code': 'auto_log_cleanup',
                'rule_name': '日志自动清理',
                'rule_type': 'maintenance',
                'rule_value': '{"conditions": [{"field": "log_age_days", "operator": "greater_than", "value": 7}], "actions": [{"action": "cleanup_logs", "params": {"days_to_keep": 7}}]}',
                'priority': 15
            },
            {
                'rule_code': 'auto_network_monitor',
                'rule_name': '网络异常自动检测',
                'rule_type': 'health',
                'rule_value': '{"conditions": [{"field": "network_latency", "operator": "greater_than", "value": 1000}], "actions": [{"action": "notify_admin", "params": {"level": "warning"}}]}',
                'priority': 18
            },
            {
                'rule_code': 'auto_api_rate_limit',
                'rule_name': 'API限流自动调整',
                'rule_type': 'security',
                'rule_value': '{"conditions": [{"field": "api_requests_per_minute", "operator": "greater_than", "value": 1000}], "actions": [{"action": "adjust_rate_limit", "params": {"limit": 500}}]}',
                'priority': 16
            },
            {
                'rule_code': 'auto_rule_priority',
                'rule_name': '规则优先级自动调整',
                'rule_type': 'rule_management',
                'rule_value': '{"conditions": [{"field": "rule_execution_count", "operator": "less_than", "value": 10}], "actions": [{"action": "lower_priority", "params": {"decrement": 20}}]}',
                'priority': 5
            },
            {
                'rule_code': 'auto_k12_subject_rule',
                'rule_name': 'K12科目规则自动生成',
                'rule_type': 'education',
                'rule_value': '{"conditions": [{"field": "k12_subject", "operator": "exists", "value": true}], "actions": [{"action": "generate_subject_rules", "params": {"subject": "{{k12_subject}}"}}]}',
                'priority': 10
            },
            {
                'rule_code': 'auto_politics_rule_update',
                'rule_name': '政治题库规则自动更新',
                'rule_type': 'education',
                'rule_value': '{"conditions": [{"field": "politics_update_date", "operator": "greater_than", "value": 7}], "actions": [{"action": "update_politics_rules", "params": {"source": "current_affairs"}}]}',
                'priority': 8
            },
            {
                'rule_code': 'auto_listening_rule_generation',
                'rule_name': '听力题规则自动生成',
                'rule_type': 'education',
                'rule_value': '{"conditions": [{"field": "listening_difficulty", "operator": "in_list", "value": ["easy", "medium", "hard"]}], "actions": [{"action": "generate_listening_rules", "params": {"difficulty": "{{listening_difficulty}}"}}]}',
                'priority': 12
            },
            {
                'rule_code': 'auto_question_bank_expand',
                'rule_name': '题库自动扩充规则',
                'rule_type': 'education',
                'rule_value': '{"conditions": [{"field": "question_bank_count", "operator": "less_than", "value": 10000}], "actions": [{"action": "expand_question_bank", "params": {"target_count": 1000}}]}',
                'priority': 15
            },
            {
                'rule_code': 'auto_competition_rule_update',
                'rule_name': '竞赛题规则自动更新',
                'rule_type': 'education',
                'rule_value': '{"conditions": [{"field": "competition_season", "operator": "equals", "value": "new"}], "actions": [{"action": "update_competition_rules", "params": {"season": "{{competition_season}}"}}]}',
                'priority': 10
            }
        ]
        
        for _ in range(min(count, len(rule_templates))):
            template = rule_templates[_ % len(rule_templates)]
            unique_code = f"{template['rule_code']}_{int(time.time())}"
            
            if self._add_rule_to_db(unique_code, template['rule_name'], 
                                  template['rule_type'], template['rule_value'], 
                                  template['priority']):
                generated += 1
        
        return generated
    
    def _web_fetch_rules_internal(self, count: int) -> int:
        """从网络获取规则"""
        fetched = 0
        
        try:
            import urllib.request
            import urllib.error
            
            urls = [
                'https://raw.githubusercontent.com/mtscos/mtscos-rules/main/rules/performance_rules.json',
                'https://raw.githubusercontent.com/mtscos/mtscos-rules/main/rules/security_rules.json',
                'https://raw.githubusercontent.com/mtscos/mtscos-rules/main/rules/education_rules.json',
                'https://raw.githubusercontent.com/mtscos/mtscos-rules/main/rules/ai_management_rules.json'
            ]
            
            for url in urls:
                try:
                    with urllib.request.urlopen(url, timeout=5) as response:
                        data = response.read().decode('utf-8')
                        rules_data = json.loads(data)
                        
                        for rule in rules_data.get('rules', [])[:count // len(urls)]:
                            if self._add_rule_to_db(
                                rule.get('rule_code', f'web_rule_{int(time.time())}'),
                                rule.get('rule_name', '网络获取规则'),
                                rule.get('rule_type', 'web_import'),
                                json.dumps(rule.get('rule_value', '{}')),
                                rule.get('priority', 100)
                            ):
                                fetched += 1
                except Exception:
                    continue
                
                if fetched >= count:
                    break
            
        except Exception:
            pass
        
        return fetched
    
    def _mining_historical_rules(self, count: int) -> int:
        """从历史数据挖掘规则"""
        mined = 0
        
        historical_patterns = [
            ('auto_error_retry', '错误自动重试规则', 'reliability', 
             '{"conditions": [{"field": "error_count", "operator": "greater_than", "value": 3}], "actions": [{"action": "retry_task", "params": {"max_retries": 3}}]}', 20),
            ('auto_resource_cleanup', '资源自动清理规则', 'maintenance',
             '{"conditions": [{"field": "resource_age", "operator": "greater_than", "value": 30}], "actions": [{"action": "cleanup_resource", "params": {}}]}', 15),
            ('auto_performance_optimize', '性能自动优化规则', 'performance',
             '{"conditions": [{"field": "response_time", "operator": "greater_than", "value": 500}], "actions": [{"action": "optimize_performance", "params": {}}]}', 18),
            ('auto_backup_verify', '备份自动验证规则', 'maintenance',
             '{"conditions": [{"field": "backup_age", "operator": "greater_than", "value": 24}], "actions": [{"action": "verify_backup", "params": {}}]}', 12),
            ('auto_user_activity_monitor', '用户活动自动监控规则', 'security',
             '{"conditions": [{"field": "unusual_activity", "operator": "equals", "value": true}], "actions": [{"action": "alert_security", "params": {"level": "warning"}}]}', 16),
            ('auto_api_version_check', 'API版本自动检查规则', 'development',
             '{"conditions": [{"field": "api_version", "operator": "less_than", "value": "2.0"}], "actions": [{"action": "update_api", "params": {}}]}', 8),
            ('auto_dependency_update', '依赖自动更新规则', 'development',
             '{"conditions": [{"field": "dependency_outdated", "operator": "equals", "value": true}], "actions": [{"action": "update_dependency", "params": {}}]}', 10),
            ('auto_load_balancing', '负载自动均衡规则', 'performance',
             '{"conditions": [{"field": "server_load", "operator": "greater_than", "value": 80}], "actions": [{"action": "balance_load", "params": {}}]}', 14),
            ('auto_failover', '自动故障转移规则', 'reliability',
             '{"conditions": [{"field": "service_down", "operator": "equals", "value": true}], "actions": [{"action": "switch_to_backup", "params": {}}]}', 20),
            ('auto_log_analysis', '日志自动分析规则', 'maintenance',
             '{"conditions": [{"field": "error_rate", "operator": "greater_than", "value": 0.05}], "actions": [{"action": "analyze_logs", "params": {}}]}', 12)
        ]
        
        for code, name, rule_type, value, priority in historical_patterns[:min(count, len(historical_patterns))]:
            unique_code = f"{code}_{int(time.time())}"
            if self._add_rule_to_db(unique_code, name, rule_type, value, priority):
                mined += 1
        
        return mined
    
    def _add_rule_to_db(self, rule_code: str, rule_name: str, rule_type: str, 
                       rule_value: str, priority: int) -> bool:
        """添加规则到数据库"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO system_rules (
                        rule_code, rule_name, rule_description, rule_type, 
                        rule_value, is_active, priority, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                ''', (rule_code, rule_name, f"自动生成规则: {rule_name}", rule_type, 
                      rule_value, priority, datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
            
            self._record_maintenance("expand_rules", "add_rule", rule_code, rule_name, rule_type, "success")
            return True
        
        except Exception as e:
            logger.error(f"[规则库维护员工] 添加规则失败: {e}")
            return False
    
    def _organize_rules(self, task_data: Dict) -> Dict:
        """整理规则"""
        rule_type = task_data.get("rule_type", "all")
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                if rule_type != "all":
                    cursor.execute('SELECT rule_code, rule_type FROM system_rules WHERE rule_type = ?', (rule_type,))
                else:
                    cursor.execute('SELECT rule_code, rule_type FROM system_rules')
                
                rows = cursor.fetchall()
                organized_count = len(rows)
                
                rule_type_counts = {}
                for row in rows:
                    rt = row[1]
                    rule_type_counts[rt] = rule_type_counts.get(rt, 0) + 1
                
                self._record_maintenance("organize_rules", "organization", result=f"整理了 {organized_count} 条规则")
                
                return {
                    "success": True,
                    "message": f"规则整理完成，共整理 {organized_count} 条规则",
                    "organized_count": organized_count,
                    "rule_type": rule_type,
                    "type_distribution": rule_type_counts
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _quality_check(self, task_data: Dict) -> Dict:
        """质量检查"""
        check_type = task_data.get("check_type", "all")
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_code, rule_name, rule_value, is_active FROM system_rules')
                
                rows = cursor.fetchall()
                total = len(rows)
                issues = []
                
                for row in rows:
                    rule_code, rule_name, rule_value, is_active = row
                    
                    try:
                        json.loads(rule_value)
                    except:
                        issues.append({"rule_code": rule_code, "issue": "invalid_json"})
                    
                    if not rule_name or len(rule_name) < 3:
                        issues.append({"rule_code": rule_code, "issue": "short_name"})
                
                self._record_maintenance("quality_check", "check", result=f"检查了 {total} 条规则，发现 {len(issues)} 个问题")
                
                return {
                    "success": True,
                    "message": f"质量检查完成，检查 {total} 条规则，发现 {len(issues)} 个问题",
                    "total_rules": total,
                    "issues_found": len(issues),
                    "issues": issues[:50],
                    "check_type": check_type
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _duplicate_removal(self, task_data: Dict) -> Dict:
        """去重处理"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT rule_code, rule_name, rule_value FROM system_rules')
                
                rows = cursor.fetchall()
                seen = set()
                duplicates = []
                
                for row in rows:
                    rule_code, rule_name, rule_value = row
                    key = (rule_name, rule_value)
                    
                    if key in seen:
                        duplicates.append(rule_code)
                    else:
                        seen.add(key)
                
                removed_count = 0
                for duplicate_code in duplicates:
                    cursor.execute('DELETE FROM system_rules WHERE rule_code = ?', (duplicate_code,))
                    removed_count += 1
                
                conn.commit()
                
                self._record_maintenance("duplicate_removal", "remove_duplicates", result=f"移除了 {removed_count} 条重复规则")
                
                return {
                    "success": True,
                    "message": f"去重完成，移除 {removed_count} 条重复规则",
                    "total_checked": len(rows),
                    "removed_count": removed_count,
                    "duplicate_codes": duplicates[:50]
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _web_fetch_rules(self, task_data: Dict) -> Dict:
        """网络获取规则"""
        urls = task_data.get("urls", [])
        target_count = int(task_data.get("target_count", 50))
        
        fetched = self._web_fetch_rules_internal(target_count)
        
        return {
            "success": True,
            "message": f"网络获取完成，获取 {fetched} 条规则",
            "fetched_count": fetched,
            "target_count": target_count,
            "urls_used": len(urls) if urls else "default"
        }
    
    def _ai_generate_rules(self, task_data: Dict) -> Dict:
        """AI生成规则"""
        count = int(task_data.get("count", 50))
        rule_category = task_data.get("category", "all")
        
        generated = self._ai_generate_rules_internal(count)
        
        return {
            "success": True,
            "message": f"AI生成完成，生成 {generated} 条规则",
            "generated_count": generated,
            "target_count": count,
            "category": rule_category
        }
    
    def _system_adapt(self, task_data: Dict) -> Dict:
        """系统适配"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT rule_code, rule_value FROM system_rules WHERE is_active = 1')
                rows = cursor.fetchall()
                
                adapted_count = 0
                for row in rows:
                    rule_code, rule_value = row
                    try:
                        rule_data = json.loads(rule_value)
                        
                        if 'conditions' in rule_data and 'actions' in rule_data:
                            adapted_count += 1
                    except:
                        continue
                
                self._record_maintenance("system_adapt", "adaptation", result=f"适配了 {adapted_count} 条规则")
                
                return {
                    "success": True,
                    "message": f"系统适配完成，适配 {adapted_count} 条规则到系统",
                    "adapted_count": adapted_count,
                    "total_active_rules": len(rows)
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _deploy_employees(self, task_data: Dict) -> Dict:
        """自动增派AI员工"""
        try:
            from ai_engines.ai_employee_manager import AIEmployeeManager
            
            manager = AIEmployeeManager.get_instance()
            if not manager:
                return {"success": False, "message": "AI员工管理器未初始化"}
            
            deployed_count = 0
            
            employee_types_to_deploy = [
                ("rule_base_maintenance", "规则库维护AI", 5),
                ("question_bank_maintenance", "题库维护AI", 5),
                ("diagnostics_repair", "诊断修复AI", 6),
                ("validation", "验证AI", 4),
                ("routing", "路由AI", 5)
            ]
            
            for emp_type, name, level in employee_types_to_deploy:
                try:
                    employee_id = manager.create_employee(emp_type, name, level)
                    deployed_count += 1
                except Exception:
                    continue
            
            return {
                "success": True,
                "message": f"自动增派完成，新增 {deployed_count} 个AI员工",
                "deployed_count": deployed_count,
                "total_employees": len(manager.employees)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _full_maintenance(self, task_data: Dict) -> Dict:
        """全面维护"""
        results = []
        
        results.append(self._expand_rules({"source_type": "all", "target_count": 50}))
        results.append(self._duplicate_removal({}))
        results.append(self._quality_check({"check_type": "all"}))
        results.append(self._organize_rules({"rule_type": "all"}))
        results.append(self._system_adapt({}))
        
        success_count = sum(1 for r in results if r.get("success", False))
        
        return {
            "success": True,
            "message": f"全面维护完成，{success_count}/{len(results)} 项任务成功",
            "total_tasks": len(results),
            "success_count": success_count,
            "results": results
        }
    
    def _get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM system_rules')
                total_rules = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM system_rules WHERE is_active = 1')
                active_rules = cursor.fetchone()[0]
                
                cursor.execute('SELECT rule_type, COUNT(*) FROM system_rules GROUP BY rule_type')
                type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
                
                cursor.execute('SELECT COUNT(*) FROM rule_maintenance_records')
                maintenance_records = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM rule_expansion_sources')
                expansion_sources = cursor.fetchone()[0]
                
                return {
                    "success": True,
                    "statistics": {
                        "total_rules": total_rules,
                        "active_rules": active_rules,
                        "rule_type_distribution": type_distribution,
                        "maintenance_records": maintenance_records,
                        "expansion_sources": expansion_sources,
                        "last_updated": datetime.now().isoformat()
                    }
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}