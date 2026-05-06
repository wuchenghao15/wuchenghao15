#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI智能自动化系统 - 提升项目智能性和自动化程度"""

import os
import sqlite3
# import json removed - using database storage
import logging
import subprocess
import time
from datetime import datetime
from threading import Thread
from typing import Dict, List, Any, Callable
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_automation')

class AIAutomationSystem:
    def __init__(self):
        self.project_dir = os.getcwd()
        self.db_path = 'app.db'
        self.is_running = False
        self.automation_tasks = {}
        self.system_metrics = defaultdict(list)
        self.init_ai_components()
    
    def init_ai_components(self):
        """初始化AI组件"""
        self.components = {
            'intelligent_scheduler': AIIntelligentScheduler(self),
            'self_optimizer': AISelfOptimizer(self),
            'smart_monitor': AISmartMonitor(self),
            'decision_engine': AIDecisionEngine(self),
            'continuous_learner': AIContinuousLearner(self),
            'auto_fixer': AIAutoFixer(self),
            'resource_manager': AIResourceManager(self)
        }
        logger.info("AI自动化组件初始化完成")
    
    def start(self):
        """启动AI自动化系统"""
        print("="*80)
        print("          AI智能自动化系统 - 启动中...")
        print("="*80)
        
        self.is_running = True
        
        for name, component in self.components.items():
            component.start()
            print(f"  ✓ {name} 启动成功")
        
        print("\n" + "="*80)
        print("          AI智能自动化系统已启动！")
        print("="*80)
        
        self.main_loop()
    
    def main_loop(self):
        """主循环 - 持续监控和优化"""
        while self.is_running:
            try:
                self.collect_metrics()
                self.update_status()
                time.sleep(60)
            except KeyboardInterrupt:
                self.stop()
                break
    
    def stop(self):
        """停止AI自动化系统"""
        print("\n" + "="*80)
        print("          AI智能自动化系统 - 停止中...")
        print("="*80)
        
        self.is_running = False
        
        for name, component in self.components.items():
            component.stop()
            print(f"  ✓ {name} 已停止")
        
        print("\n" + "="*80)
        print("          AI智能自动化系统已停止")
        print("="*80)
    
    def collect_metrics(self):
        """收集系统指标"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': self.get_cpu_usage(),
            'memory_usage': self.get_memory_usage(),
            'disk_usage': self.get_disk_usage(),
            'active_tasks': len([c for c in self.components.values() if c.is_active])
        }
        
        for key, value in metrics.items():
            self.system_metrics[key].append(value)
            if len(self.system_metrics[key]) > 100:
                self.system_metrics[key] = self.system_metrics[key][-100:]
        
        self.save_metrics(metrics)
    
    def get_cpu_usage(self):
        """获取CPU使用率"""
        try:
            result = subprocess.run(['top', '-l', '1', '-n', '0'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'CPU usage' in line:
                    parts = line.split()
                    return float(parts[3].replace('%', ''))
        except:
            pass
        return 0.0
    
    def get_memory_usage(self):
        """获取内存使用率"""
        try:
            result = subprocess.run(['vm_stat'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            free = active = 0
            for line in lines:
                if 'Pages free' in line:
                    free = int(line.split(':')[1].strip().replace('.', ''))
                if 'Pages active' in line:
                    active = int(line.split(':')[1].strip().replace('.', ''))
            return active / (active + free) * 100 if (active + free) > 0 else 0
        except:
            pass
        return 0.0
    
    def get_disk_usage(self):
        """获取磁盘使用率"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if '/' in line and not line.startswith('Filesystem'):
                    parts = line.split()
                    return float(parts[4].replace('%', ''))
        except:
            pass
        return 0.0
    
    def save_metrics(self, metrics):
        """保存指标到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    active_tasks INTEGER
                )
            ''')
            
            cursor.execute('''
                INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, disk_usage, active_tasks)
                VALUES (?, ?, ?, ?, ?)
            ''', (metrics['timestamp'], metrics['cpu_usage'], metrics['memory_usage'], 
                  metrics['disk_usage'], metrics['active_tasks']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存指标失败: {e}")
    
    def update_status(self):
        """更新系统状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_status (status_id, status, last_update)
                VALUES ('main', ?, ?)
            ''', ('running' if self.is_running else 'stopped', datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新状态失败: {e}")

class AIIntelligentScheduler:
    """AI智能调度器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.tasks = []
    
    def start(self):
        self.is_active = True
        self.load_scheduled_tasks()
        self.scheduler_thread = Thread(target=self.run, daemon=True)
        self.scheduler_thread.start()
        logger.info("智能调度器启动")
    
    def stop(self):
        self.is_active = False
    
    def run(self):
        while self.is_active:
            now = datetime.now()
            for task in self.tasks:
                if self.should_run(task, now):
                    self.execute_task(task)
            time.sleep(60)
    
    def should_run(self, task, now):
        """判断任务是否应该运行"""
        schedule = task.get('schedule', '')
        if schedule == 'hourly':
            return now.minute == 0
        elif schedule == 'daily':
            return now.hour == 3 and now.minute == 0
        elif schedule == 'weekly':
            return now.weekday() == 0 and now.hour == 3 and now.minute == 0
        return False
    
    def execute_task(self, task):
        """执行任务"""
        logger.info(f"执行调度任务: {task['task_name']}")
        try:
            exec(task.get('command', ''))
            task['last_run'] = datetime.now().isoformat()
            task['success_count'] = task.get('success_count', 0) + 1
        except Exception as e:
            task['error_count'] = task.get('error_count', 0) + 1
            logger.error(f"任务执行失败 {task['task_name']}: {e}")
    
    def load_scheduled_tasks(self):
        """加载调度任务"""
        self.tasks = [
            {'task_name': 'daily_cleanup', 'schedule': 'daily', 'command': 'self.parent.components["auto_fixer"].run_daily_cleanup()'},
            {'task_name': 'weekly_optimization', 'schedule': 'weekly', 'command': 'self.parent.components["self_optimizer"].run_weekly_optimization()'},
            {'task_name': 'hourly_backup', 'schedule': 'hourly', 'command': 'self.parent.components["resource_manager"].create_backup()'},
            {'task_name': 'hourly_learning', 'schedule': 'hourly', 'command': 'self.parent.components["continuous_learner"].learn_from_data()'}
        ]

class AISelfOptimizer:
    """AI自我优化器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.optimization_history = []
    
    def start(self):
        self.is_active = True
        logger.info("自我优化器启动")
    
    def stop(self):
        self.is_active = False
    
    def run_weekly_optimization(self):
        """运行每周优化"""
        logger.info("执行每周优化...")
        
        optimizations = [
            self.optimize_code_complexity,
            self.optimize_database,
            self.cleanup_logs,
            self.update_knowledge_base
        ]
        
        for opt in optimizations:
            try:
                opt()
            except Exception as e:
                logger.error(f"优化失败 {opt.__name__}: {e}")
    
    def optimize_code_complexity(self):
        """优化代码复杂度"""
        logger.info("优化代码复杂度...")
        # 可以添加代码分析和重构建议
    
    def optimize_database(self):
        """优化数据库"""
        logger.info("优化数据库...")
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.close()
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
    
    def cleanup_logs(self):
        """清理日志"""
        logger.info("清理日志...")
        # 可以添加日志清理逻辑
    
    def update_knowledge_base(self):
        """更新知识库"""
        logger.info("更新知识库...")
        self.parent.components['continuous_learner'].update_knowledge()

class AISmartMonitor:
    """AI智能监控器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.alerts = []
    
    def start(self):
        self.is_active = True
        self.monitor_thread = Thread(target=self.run, daemon=True)
        self.monitor_thread.start()
        logger.info("智能监控器启动")
    
    def stop(self):
        self.is_active = False
    
    def run(self):
        while self.is_active:
            self.check_system_health()
            time.sleep(30)
    
    def check_system_health(self):
        """检查系统健康状态"""
        cpu = self.parent.get_cpu_usage()
        memory = self.parent.get_memory_usage()
        disk = self.parent.get_disk_usage()
        
        if cpu > 90:
            self.trigger_alert('high_cpu', f"CPU使用率过高: {cpu}%")
        if memory > 90:
            self.trigger_alert('high_memory', f"内存使用率过高: {memory}%")
        if disk > 95:
            self.trigger_alert('high_disk', f"磁盘使用率过高: {disk}%")
    
    def trigger_alert(self, alert_type, message):
        """触发警报"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        self.alerts.append(alert)
        
        logger.warning(f"警报触发 [{alert_type}]: {message}")
        self.save_alert(alert)
        
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
    
    def save_alert(self, alert):
        """保存警报到数据库"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT,
                    message TEXT,
                    timestamp TEXT,
                    status TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT INTO alerts (alert_type, message, timestamp, status)
                VALUES (?, ?, ?, ?)
            ''', (alert['type'], alert['message'], alert['timestamp'], alert['status']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存警报失败: {e}")

class AIDecisionEngine:
    """AI决策引擎"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.decision_rules = []
    
    def start(self):
        self.is_active = True
        self.load_decision_rules()
        logger.info("决策引擎启动")
    
    def stop(self):
        self.is_active = False
    
    def load_decision_rules(self):
        """加载决策规则"""
        self.decision_rules = [
            {
                'condition': lambda: self.parent.get_cpu_usage() > 80,
                'action': self.throttle_non_critical_tasks,
                'priority': 10
            },
            {
                'condition': lambda: self.parent.get_memory_usage() > 85,
                'action': self.free_memory,
                'priority': 10
            },
            {
                'condition': lambda: len(self.parent.components['smart_monitor'].alerts) > 5,
                'action': self.raise_alert_level,
                'priority': 15
            }
        ]
    
    def evaluate_decisions(self):
        """评估并执行决策"""
        for rule in sorted(self.decision_rules, key=lambda x: x['priority'], reverse=True):
            if rule['condition']():
                try:
                    rule['action']()
                except Exception as e:
                    logger.error(f"决策执行失败: {e}")
    
    def throttle_non_critical_tasks(self):
        """限制非关键任务"""
        logger.info("决策: 限制非关键任务以降低CPU负载")
    
    def free_memory(self):
        """释放内存"""
        logger.info("决策: 释放缓存内存")
    
    def raise_alert_level(self):
        """提高警报级别"""
        logger.info("决策: 提高警报级别")

class AIContinuousLearner:
    """AI持续学习器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.learning_cycles = 0
    
    def start(self):
        self.is_active = True
        self.learning_thread = Thread(target=self.run, daemon=True)
        self.learning_thread.start()
        logger.info("持续学习器启动")
    
    def stop(self):
        self.is_active = False
    
    def run(self):
        while self.is_active:
            self.learn_from_data()
            time.sleep(3600)  # 每小时学习一次
    
    def learn_from_data(self):
        """从数据中学习"""
        self.learning_cycles += 1
        logger.info(f"第 {self.learning_cycles} 次学习循环...")
        
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM enhanced_fix_logs')
            fix_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT issue_type, COUNT(*) FROM code_fix_logs GROUP BY issue_type')
            issue_patterns = cursor.fetchall()
            
            conn.close()
            
            self.update_knowledge(fix_count, issue_patterns)
            
        except Exception as e:
            logger.error(f"学习失败: {e}")
    
    def update_knowledge(self, fix_count, issue_patterns):
        """更新知识库"""
        try:
            conn = sqlite3.connect(self.parent.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_learning_logs 
                (learning_cycle, knowledge_points, patterns_learned, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (self.learning_cycles, fix_count, len(issue_patterns), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")

class AIAutoFixer:
    """AI自动修复器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
    
    def start(self):
        self.is_active = True
        logger.info("自动修复器启动")
    
    def stop(self):
        self.is_active = False
    
    def run_daily_cleanup(self):
        """运行每日清理"""
        logger.info("执行每日清理...")
        
        cleanups = [
            self.remove_temp_files,
            self.clean_backups,
            self.optimize_logs
        ]
        
        for cleanup in cleanups:
            try:
                cleanup()
            except Exception as e:
                logger.error(f"清理失败 {cleanup.__name__}: {e}")
    
    def remove_temp_files(self):
        """删除临时文件"""
        temp_extensions = ['.tmp', '.bak', '.swp']
        removed = 0
        
        for root, dirs, files in os.walk(self.parent.project_dir):
            if 'node_modules' in root or '.git' in root:
                continue
            for file in files:
                if any(file.endswith(ext) for ext in temp_extensions):
                    try:
                        os.remove(os.path.join(root, file))
                        removed += 1
                    except:
                        pass
        
        logger.info(f"删除了 {removed} 个临时文件")
    
    def clean_backups(self):
        """清理旧备份"""
        # 可以添加备份清理逻辑
        pass
    
    def optimize_logs(self):
        """优化日志"""
        # 可以添加日志优化逻辑
        pass

class AIResourceManager:
    """AI资源管理器"""
    def __init__(self, parent):
        self.parent = parent
        self.is_active = False
        self.backup_count = 0
    
    def start(self):
        self.is_active = True
        logger.info("资源管理器启动")
    
    def stop(self):
        self.is_active = False
    
    def create_backup(self):
        """创建备份"""
        self.backup_count += 1
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            conn = sqlite3.connect(self.parent.db_path)
            backup_path = f'backups/backup_{timestamp}.db'
            os.makedirs('backups', exist_ok=True)
            
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()
            
            logger.info(f"创建备份 #{self.backup_count}: {backup_path}")
            
            self.clean_old_backups()
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
    
    def clean_old_backups(self):
        """清理旧备份"""
        backups_dir = 'backups'
        if not os.path.exists(backups_dir):
            return
        
        backups = sorted(os.listdir(backups_dir))
        if len(backups) > 10:
            for backup in backups[:-10]:
                try:
                    os.remove(os.path.join(backups_dir, backup))
                except:
                    pass

def main():
    ai_system = AIAutomationSystem()
    ai_system.start()

if __name__ == "__main__":
    main()