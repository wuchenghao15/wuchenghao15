#!/usr/bin/env python3
"""
强力修复AI员工
支持多策略修复、监控后台错误计划、深度诊断等功能
"""

import logging
import json
import uuid
import os
import sys
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class FixStrategyType(Enum):
    """修复策略类型"""
    QUICK_FIX = "quick_fix"           # 快速修复
    DEEP_FIX = "deep_fix"             # 深度修复
    MULTI_FIX = "multi_fix"           # 多策略修复
    COLLABORATIVE_FIX = "collaborative_fix"  # 协同修复
    AUTOMATIC_FIX = "automatic_fix"   # 自动修复
    MANUAL_FIX = "manual_fix"         # 手动修复（需要审批）


class MonitorPlanStatus(Enum):
    """监控计划状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MonitorErrorPlan:
    """监控错误计划"""
    plan_id: str
    error_type: str
    error_pattern: str
    severity: str
    detection_interval: int  # 检测间隔（秒）
    auto_fix_enabled: bool
    notify_enabled: bool
    max_attempts: int
    status: str = 'active'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_detected: Optional[str] = None
    last_fixed: Optional[str] = None
    total_detected: int = 0
    total_fixed: int = 0
    assigned_employees: List[str] = field(default_factory=list)


@dataclass
class FixStrategy:
    """修复策略"""
    name: str
    strategy_type: FixStrategyType
    priority: int
    handlers: List[str]
    required_employees: List[str]
    description: str
    success_rate: float = 0.85
    avg_time: float = 5.0


class PowerfulFixEmployee:
    """强力修复AI员工"""
    
    # 修复策略库
    FIX_STRATEGIES = {
        'configuration': [
            FixStrategy(
                name='快速配置修复',
                strategy_type=FixStrategyType.QUICK_FIX,
                priority=1,
                handlers=['_fix_config_env_vars', '_fix_config_reload'],
                required_employees=['system_maintenance', 'devops_engineer'],
                description='自动设置缺失的环境变量并重新加载配置',
                success_rate=0.95,
                avg_time=3.0
            ),
            FixStrategy(
                name='深度配置修复',
                strategy_type=FixStrategyType.DEEP_FIX,
                priority=2,
                handlers=['_fix_config_deep_analysis', '_fix_config_validate', '_fix_config_backup'],
                required_employees=['system_maintenance', 'backend_engineer', 'devops_engineer'],
                description='深度分析配置问题，验证并备份配置',
                success_rate=0.90,
                avg_time=8.0
            )
        ],
        'database': [
            FixStrategy(
                name='快速数据库修复',
                strategy_type=FixStrategyType.QUICK_FIX,
                priority=1,
                handlers=['_fix_db_create_table', '_fix_db_clean_duplicates'],
                required_employees=['system_maintenance', 'backend_engineer'],
                description='快速创建缺失表、清理重复数据',
                success_rate=0.85,
                avg_time=5.0
            ),
            FixStrategy(
                name='深度数据库修复',
                strategy_type=FixStrategyType.DEEP_FIX,
                priority=2,
                handlers=['_fix_db_schema_analysis', '_fix_db_migrate', '_fix_db_verify'],
                required_employees=['data_analyzer', 'backend_engineer', 'devops_engineer'],
                description='深度分析数据库schema，执行迁移并验证',
                success_rate=0.92,
                avg_time=15.0
            ),
            FixStrategy(
                name='协同数据库修复',
                strategy_type=FixStrategyType.COLLABORATIVE_FIX,
                priority=3,
                handlers=['_fix_db_collaborative_analysis', '_fix_db_multi_fix', '_fix_db_report'],
                required_employees=['data_analyzer', 'backend_engineer', 'devops_engineer', 'qa_validator'],
                description='多员工协同分析和修复数据库问题',
                success_rate=0.98,
                avg_time=25.0
            )
        ],
        'performance': [
            FixStrategy(
                name='性能优化修复',
                strategy_type=FixStrategyType.AUTOMATIC_FIX,
                priority=1,
                handlers=['_fix_perf_monitor', '_fix_perf_optimize', '_fix_perf_verify'],
                required_employees=['performance_optimizer', 'monitoring_analyst'],
                description='监控性能指标，自动优化并验证',
                success_rate=0.88,
                avg_time=10.0
            )
        ],
        'security': [
            FixStrategy(
                name='安全加固修复',
                strategy_type=FixStrategyType.MANUAL_FIX,
                priority=1,
                handlers=['_fix_sec_scan', '_fix_sec_patch', '_fix_sec_verify'],
                required_employees=['security_guard', 'devops_engineer'],
                description='扫描安全漏洞，应用补丁并验证',
                success_rate=0.95,
                avg_time=12.0
            )
        ],
        'monitoring': [
            FixStrategy(
                name='监控错误修复',
                strategy_type=FixStrategyType.AUTOMATIC_FIX,
                priority=1,
                handlers=['_fix_monitor_detect', '_fix_monitor_analyze', '_fix_monitor_fix', '_fix_monitor_report'],
                required_employees=['monitoring_analyst', 'system_maintenance', 'devops_engineer'],
                description='自动检测、分析并修复监控错误',
                success_rate=0.92,
                avg_time=8.0
            )
        ]
    }
    
    def __init__(self, employee_id: str, name: str, level: int = 10):
        self.employee_id = employee_id
        self.name = name
        self.level = level
        self.type = "powerful_fix"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.performance_score = 95 + level * 0.5
        
        # 监控计划
        self.monitor_plans: Dict[str, MonitorErrorPlan] = {}
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_running = False
        
        # 修复历史
        self.fix_history: List[Dict[str, Any]] = []
        self.strategy_usage_stats: Dict[str, int] = defaultdict(int)
        
        # 技能列表
        self.skills = [
            {"name": "deep_diagnostics", "level": 10, "experience": 0.0},
            {"name": "multi_strategy_fix", "level": 10, "experience": 0.0},
            {"name": "monitor_planning", "level": 9, "experience": 0.0},
            {"name": "error_pattern_analysis", "level": 9, "experience": 0.0},
            {"name": "collaborative_fix", "level": 9, "experience": 0.0},
            {"name": "root_cause_analysis", "level": 10, "experience": 0.0},
            {"name": "auto_healing", "level": 10, "experience": 0.0},
            {"name": "report_generation", "level": 9, "experience": 0.0}
        ]
        
        # 数据库路径
        self._db_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),
            'app.db'
        )
        
        self._init_monitor_plans_db()
        self._load_monitor_plans()
        
        logger.info(f"[强力修复员工] 创建: {self.name} ({self.employee_id}) 级别: {self.level}")
    
    def start(self):
        """启动员工"""
        self.status = "active"
        self.start_monitor_thread()
        logger.info(f"[强力修复员工] {self.name} 已启动，监控线程已启动")
    
    def _init_monitor_plans_db(self):
        """初始化监控计划数据库表"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitor_error_plans (
                    plan_id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    error_pattern TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    detection_interval INTEGER DEFAULT 60,
                    auto_fix_enabled BOOLEAN DEFAULT TRUE,
                    notify_enabled BOOLEAN DEFAULT TRUE,
                    max_attempts INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    last_detected TEXT,
                    last_fixed TEXT,
                    total_detected INTEGER DEFAULT 0,
                    total_fixed INTEGER DEFAULT 0,
                    assigned_employees TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("[强力修复员工] 监控计划数据库表初始化完成")
        except Exception as e:
            logger.error(f"[强力修复员工] 初始化监控计划数据库失败: {e}")
    
    def _load_monitor_plans(self):
        """从数据库加载监控计划"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM monitor_error_plans WHERE status = "active"')
            plans = cursor.fetchall()
            
            for plan in plans:
                self.monitor_plans[plan[0]] = MonitorErrorPlan(
                    plan_id=plan[0],
                    error_type=plan[1],
                    error_pattern=plan[2],
                    severity=plan[3],
                    detection_interval=plan[4],
                    auto_fix_enabled=bool(plan[5]),
                    notify_enabled=bool(plan[6]),
                    max_attempts=plan[7],
                    status=plan[8],
                    created_at=plan[9],
                    last_detected=plan[10],
                    last_fixed=plan[11],
                    total_detected=plan[12],
                    total_fixed=plan[13],
                    assigned_employees=json.loads(plan[14]) if plan[14] else []
                )
            
            conn.close()
            logger.info(f"[强力修复员工] 加载了 {len(self.monitor_plans)} 个监控计划")
        except Exception as e:
            logger.error(f"[强力修复员工] 加载监控计划失败: {e}")
    
    def create_monitor_plan(self, error_type: str, error_pattern: str, 
                            severity: str = 'high', detection_interval: int = 60,
                            auto_fix_enabled: bool = True) -> Dict[str, Any]:
        """创建监控计划"""
        plan_id = f"monitor_{error_type}_{uuid.uuid4().hex[:8]}"
        
        plan = MonitorErrorPlan(
            plan_id=plan_id,
            error_type=error_type,
            error_pattern=error_pattern,
            severity=severity,
            detection_interval=detection_interval,
            auto_fix_enabled=auto_fix_enabled,
            notify_enabled=True,
            max_attempts=5,
            assigned_employees=[self.employee_id]
        )
        
        self.monitor_plans[plan_id] = plan
        self._save_monitor_plan(plan)
        
        logger.info(f"[强力修复员工] 创建监控计划: {plan_id} 监控错误类型: {error_type}")
        
        return {
            'success': True,
            'plan_id': plan_id,
            'message': f"成功创建监控计划: {plan_id}"
        }
    
    def _save_monitor_plan(self, plan: MonitorErrorPlan):
        """保存监控计划到数据库"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO monitor_error_plans VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                plan.plan_id, plan.error_type, plan.error_pattern, plan.severity,
                plan.detection_interval, plan.auto_fix_enabled, plan.notify_enabled,
                plan.max_attempts, plan.status, plan.created_at, plan.last_detected,
                plan.last_fixed, plan.total_detected, plan.total_fixed,
                json.dumps(plan.assigned_employees)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[强力修复员工] 保存监控计划失败: {e}")
    
    def start_monitor_thread(self):
        """启动监控线程"""
        if self.monitor_running:
            return
        
        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"[强力修复员工] {self.name} 监控线程已启动")
    
    def stop_monitor_thread(self):
        """停止监控线程"""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info(f"[强力修复员工] {self.name} 监控线程已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitor_running:
            try:
                self._check_monitor_plans()
            except Exception as e:
                logger.error(f"[强力修复员工] 监控循环错误: {e}")
            
            time.sleep(30)
    
    def _check_monitor_plans(self):
        """检查监控计划"""
        for plan_id, plan in self.monitor_plans.items():
            if plan.status != 'active':
                continue
            
            # 检测错误
            errors = self._detect_errors_by_pattern(plan.error_pattern)
            
            if errors:
                plan.total_detected += len(errors)
                plan.last_detected = datetime.now().isoformat()
                
                logger.info(f"[强力修复员工] 检测到 {len(errors)} 个错误，计划: {plan_id}")
                
                # 自动修复
                if plan.auto_fix_enabled:
                    fix_result = self._auto_fix_errors(errors, plan)
                    if fix_result['success']:
                        plan.total_fixed += fix_result['fixed_count']
                        plan.last_fixed = datetime.now().isoformat()
                
                self._save_monitor_plan(plan)
    
    def _detect_errors_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """根据模式检测错误"""
        errors = []
        
        try:
            # 从日志文件检测错误
            log_path = os.path.join(os.path.dirname(self._db_path), 'logs', 'mtscos.log')
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-1000:]  # 最近1000行
                    
                    for line in lines:
                        if pattern.lower() in line.lower() and 'ERROR' in line:
                            errors.append({
                                'type': 'log_error',
                                'pattern': pattern,
                                'message': line.strip(),
                                'timestamp': datetime.now().isoformat()
                            })
            
            # 从监控服务器获取错误
            try:
                from ai_engines.ai_monitor_server import AIMonitorServer
                monitor = AIMonitorServer()
                stats = monitor.get_error_stats()
                
                for error_type, count in stats.get('error_details', {}).items():
                    if pattern.lower() in error_type.lower():
                        errors.append({
                            'type': 'monitor_error',
                            'pattern': pattern,
                            'message': f"{error_type}: {count}次",
                            'count': count,
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                logger.warning(f"[强力修复员工] 获取监控服务器错误失败: {e}")
            
        except Exception as e:
            logger.error(f"[强力修复员工] 检测错误失败: {e}")
        
        return errors
    
    def _auto_fix_errors(self, errors: List[Dict[str, Any]], plan: MonitorErrorPlan) -> Dict[str, Any]:
        """自动修复错误"""
        fixed_count = 0
        
        for error in errors:
            try:
                fix_result = self.execute_fix({
                    'task_type': 'error_fix',
                    'error_data': error,
                    'plan_id': plan.plan_id
                })
                
                if fix_result.get('success', False):
                    fixed_count += 1
                    self.fix_history.append({
                        'error': error,
                        'plan_id': plan.plan_id,
                        'fix_result': fix_result,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"[强力修复员工] 自动修复错误失败: {e}")
        
        return {
            'success': fixed_count > 0,
            'fixed_count': fixed_count,
            'total_errors': len(errors)
        }
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        self.task_count += 1
        start_time = time.time()
        
        try:
            task_type = task_data.get("task_type", "powerful_fix")
            
            if task_type == "powerful_fix":
                result = self._execute_powerful_fix(task_data)
            elif task_type == "multi_strategy_fix":
                result = self._execute_multi_strategy_fix(task_data)
            elif task_type == "deep_diagnostics":
                result = self._execute_deep_diagnostics(task_data)
            elif task_type == "monitor_plan_create":
                result = self.create_monitor_plan(
                    task_data.get('error_type', 'general'),
                    task_data.get('error_pattern', 'ERROR'),
                    task_data.get('severity', 'high'),
                    task_data.get('detection_interval', 60),
                    task_data.get('auto_fix_enabled', True)
                )
            elif task_type == "error_fix":
                result = self._execute_error_fix(task_data)
            elif task_type == "full_scan":
                result = self._execute_full_scan(task_data)
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
            logger.error(f"[强力修复员工] 任务执行失败: {self.name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "employee_id": self.employee_id,
                "employee_name": self.name
            }
    
    def _execute_powerful_fix(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行强力修复"""
        logger.info(f"[强力修复员工] {self.name} 开始强力修复...")
        
        problems = task_data.get('problems', [])
        if not problems:
            # 从问题诊断服务获取问题
            from app.services.problems_and_diagnostics import run_powerful_diagnostic_fix
            result = run_powerful_diagnostic_fix()
            return result
        
        # 多策略修复
        return self._execute_multi_strategy_fix({'problems': problems})
    
    def _execute_multi_strategy_fix(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行多策略修复"""
        problems = task_data.get('problems', [])
        strategy_results = []
        
        for problem in problems:
            category = problem.get('category', 'general')
            severity = problem.get('severity', 'medium')
            
            # 选择最佳策略
            strategies = self.FIX_STRATEGIES.get(category, [])
            if not strategies:
                strategies = [FixStrategy(
                    name='默认修复',
                    strategy_type=FixStrategyType.QUICK_FIX,
                    priority=1,
                    handlers=['_fix_default'],
                    required_employees=['system_maintenance'],
                    description='默认快速修复策略',
                    success_rate=0.80
                )]
            
            # 根据严重程度选择策略
            if severity == 'critical':
                selected_strategy = max(strategies, key=lambda s: s.success_rate)
            elif severity == 'high':
                selected_strategy = strategies[0]
            else:
                selected_strategy = min(strategies, key=lambda s: s.avg_time)
            
            # 执行修复
            fix_result = self._apply_strategy(selected_strategy, problem)
            strategy_results.append(fix_result)
            
            self.strategy_usage_stats[selected_strategy.name] += 1
        
        successful_fixes = [r for r in strategy_results if r.get('success', False)]
        
        return {
            'success': len(successful_fixes) > 0,
            'message': f"多策略修复完成，成功修复 {len(successful_fixes)}/{len(problems)} 个问题",
            'strategy_results': strategy_results,
            'success_count': len(successful_fixes),
            'total_count': len(problems)
        }
    
    def _apply_strategy(self, strategy: FixStrategy, problem: Dict[str, Any]) -> Dict[str, Any]:
        """应用修复策略"""
        logger.info(f"[强力修复员工] 应用策略: {strategy.name} 处理问题: {problem.get('title')}")
        
        # 调用AI任务调度器
        from app.ai.ai_task_scheduler import get_ai_task_scheduler
        
        scheduler = get_ai_task_scheduler()
        fix_result = scheduler.submit_problems_for_fix([problem])
        
        scheduler.start_scheduler()
        time.sleep(5)
        
        tasks = scheduler.get_all_tasks()
        task_id = fix_result.get("task_ids", [None])[0]
        
        if task_id:
            matching_tasks = [t for t in tasks if t["task_id"] == task_id]
            if matching_tasks:
                task = matching_tasks[0]
                return {
                    'success': task.get('success', False),
                    'strategy': strategy.name,
                    'problem_id': problem.get('problem_id'),
                    'fix_result': task.get('fix_result'),
                    'task_id': task_id
                }
        
        return {'success': False, 'strategy': strategy.name, 'error': '任务未执行'}
    
    def _execute_deep_diagnostics(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行深度诊断"""
        logger.info(f"[强力修复员工] {self.name} 开始深度诊断...")
        
        from app.services.problems_and_diagnostics import get_problems_and_diagnostics_service
        
        diagnostics = get_problems_and_diagnostics_service()
        
        # 运行健康检查
        health = diagnostics.run_health_check()
        
        # 检测问题
        problems = diagnostics.detect_problems()
        
        # 分析问题根因
        root_cause_analysis = self._analyze_root_causes(problems)
        
        return {
            'success': True,
            'message': f"深度诊断完成，检测到 {len(problems)} 个问题",
            'health_check': health,
            'problems': [p.__dict__ for p in problems],
            'root_cause_analysis': root_cause_analysis
        }
    
    def _analyze_root_causes(self, problems: List[Any]) -> Dict[str, Any]:
        """分析问题根因"""
        analysis = {
            'total_problems': len(problems),
            'by_category': defaultdict(int),
            'by_severity': defaultdict(int),
            'root_causes': [],
            'recommendations': []
        }
        
        for problem in problems:
            analysis['by_category'][problem.category] += 1
            analysis['by_severity'][problem.severity] += 1
            
            # 根因分析
            if problem.category == 'configuration':
                analysis['root_causes'].append({
                    'problem_id': problem.problem_id,
                    'root_cause': '环境变量或配置文件缺失',
                    'impact': '系统功能异常',
                    'recommendation': '完善环境变量配置和配置文件管理'
                })
            elif problem.category == 'database':
                analysis['root_causes'].append({
                    'problem_id': problem.problem_id,
                    'root_cause': '数据库表结构缺失或不一致',
                    'impact': '数据操作失败',
                    'recommendation': '执行数据库迁移和表结构修复'
                })
        
        return analysis
    
    def _execute_error_fix(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行错误修复"""
        error_data = task_data.get('error_data', {})
        
        logger.info(f"[强力修复员工] {self.name} 开始修复错误: {error_data.get('pattern')}")
        
        # 根据错误类型选择修复策略
        error_type = error_data.get('type', 'log_error')
        pattern = error_data.get('pattern', '')
        
        if 'database' in pattern.lower() or 'table' in pattern.lower():
            category = 'database'
        elif 'config' in pattern.lower() or 'env' in pattern.lower():
            category = 'configuration'
        elif 'performance' in pattern.lower() or 'cpu' in pattern.lower():
            category = 'performance'
        elif 'security' in pattern.lower():
            category = 'security'
        else:
            category = 'monitoring'
        
        # 创建问题数据
        problem = {
            'problem_id': f"error_{error_type}_{uuid.uuid4().hex[:8]}",
            'category': category,
            'severity': 'high',
            'title': f"监控错误: {pattern}",
            'description': error_data.get('message', '监控检测到的错误'),
            'recommendation': '根据监控计划自动修复'
        }
        
        return self._execute_multi_strategy_fix({'problems': [problem]})
    
    def _execute_full_scan(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行全面扫描和修复"""
        logger.info(f"[强力修复员工] {self.name} 开始全面扫描和修复...")
        
        start_time = time.time()
        
        from app.services.problems_and_diagnostics import run_powerful_diagnostic_fix
        
        result = run_powerful_diagnostic_fix()
        
        execution_time = time.time() - start_time
        
        return {
            'success': True,
            'message': result.get("message", "全面扫描完成"),
            'diagnostics_result': result,
            'execution_time': execution_time,
            'monitor_plans_active': len([p for p in self.monitor_plans.values() if p.status == 'active'])
        }
    
    def _update_performance(self, success: bool, execution_time: float):
        """更新性能评分"""
        score_change = 3 if success else -5
        
        if execution_time < 5:
            score_change += 2
        elif execution_time > 20:
            score_change -= 2
        
        self.performance_score = max(0, min(100, self.performance_score + score_change))
        
        if success:
            for skill in self.skills:
                skill["experience"] += 1.0
    
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
            "monitor_plans_count": len(self.monitor_plans),
            "monitor_running": self.monitor_running,
            "strategy_usage": dict(self.strategy_usage_stats)
        }
    
    def generate_report(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成修复报告"""
        report = {
            "report_id": f"powerful_report_{uuid.uuid4().hex[:8]}",
            "generated_by": self.employee_id,
            "employee_name": self.name,
            "generated_at": datetime.now().isoformat(),
            "task_result": task_result,
            "summary": "",
            "recommendations": []
        }
        
        if task_result.get('success', False):
            report['summary'] = f"修复成功，耗时 {task_result.get('execution_time', 0):.2f}s"
        else:
            report['summary'] = f"修复失败: {task_result.get('error', '未知错误')}"
        
        if task_result.get('strategy_results'):
            for sr in task_result['strategy_results']:
                if sr.get('success'):
                    report['recommendations'].append(f"策略 {sr.get('strategy')} 成功修复问题")
                else:
                    report['recommendations'].append(f"策略 {sr.get('strategy')} 需要优化")
        
        return report