#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级AI员工系统
实现分布式任务分配、员工匹配、实时监控和功能升级
"""

import time
import uuid
import logging
import threading
from collections import defaultdict
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_ai_employee.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AdvancedAIEmployeeSystem')

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AIEmployeeSystem:
    """高级AI员工系统"""
    
    def __init__(self):
        self.ai_employees = {}
        self.tasks = {}
        self.task_queue = []
        self.task_history = []
        self.employee_skills = defaultdict(set)
        self.employee_workload = defaultdict(int)
        self.system_monitor = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        # 启动系统
        self.start()
    
    def start(self):
        """启动AI员工系统"""
        if self.is_running:
            logger.warning("AI员工系统已在运行")
            return
        
        self.is_running = True
        logger.info("启动高级AI员工系统...")
        
        # 启动任务分配线程
        self.task_thread = threading.Thread(target=self._task_scheduler)
        self.task_thread.daemon = True
        self.task_thread.start()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._system_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # 启动优化线程
        self.optimize_thread = threading.Thread(target=self._auto_optimize)
        self.optimize_thread.daemon = True
        self.optimize_thread.start()
        
        logger.info("高级AI员工系统已启动")
    
    def stop(self):
        """停止AI员工系统"""
        if not self.is_running:
            logger.warning("AI员工系统未在运行")
            return
        
        self.is_running = False
        logger.info("停止高级AI员工系统...")
        
        # 等待线程结束
        self.task_thread.join(timeout=5)
        self.monitor_thread.join(timeout=5)
        self.optimize_thread.join(timeout=5)
        
        logger.info("高级AI员工系统已停止")
    
    def register_ai_employee(self, employee_id, name, employee_type, skills, responsibilities):
        """注册AI员工"""
        with self.lock:
            if employee_id in self.ai_employees:
                logger.warning(f"AI员工已存在: {employee_id}")
                return False
            
            employee = {
                "employee_id": employee_id,
                "name": name,
                "type": employee_type,
                "skills": skills,
                "responsibilities": responsibilities,
                "status": "active",
                "workload": 0,
                "completed_tasks": 0,
                "success_rate": 1.0,
                "last_active": time.time(),
                "created_at": time.time()
            }
            
            self.ai_employees[employee_id] = employee
            
            # 记录员工技能
            for skill in skills:
                self.employee_skills[skill].add(employee_id)
            
            self.employee_workload[employee_id] = 0
            
            logger.info(f"已注册AI员工: {employee_id} - {name} ({employee_type})")
            return True
    
    def create_task(self, task_id, name, description, required_skills, priority=TaskPriority.MEDIUM):
        """创建任务"""
        with self.lock:
            if task_id in self.tasks:
                logger.warning(f"任务已存在: {task_id}")
                return False
            
            task = {
                "task_id": task_id,
                "name": name,
                "description": description,
                "required_skills": required_skills,
                "priority": priority.value,
                "status": TaskStatus.PENDING.value,
                "assigned_to": None,
                "created_at": time.time(),
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error": None
            }
            
            self.tasks[task_id] = task
            self.task_queue.append(task_id)
            
            # 按优先级排序任务队列
            self._sort_task_queue()
            
            logger.info(f"已创建任务: {task_id} - {name} (优先级: {priority.value})")
            return True
    
    def _sort_task_queue(self):
        """按优先级排序任务队列"""
        priority_order = {
            TaskPriority.URGENT.value: 0,
            TaskPriority.HIGH.value: 1,
            TaskPriority.MEDIUM.value: 2,
            TaskPriority.LOW.value: 3
        }
        
        self.task_queue.sort(key=lambda task_id: priority_order[self.tasks[task_id]["priority"]])
    
    def _match_employee_to_task(self, task_id):
        """匹配适合的AI员工到任务"""
        task = self.tasks[task_id]
        required_skills = set(task["required_skills"])
        
        # 找到具备所有必需技能的员工
        qualified_employees = []
        for skill in required_skills:
            if skill in self.employee_skills:
                if not qualified_employees:
                    qualified_employees = set(self.employee_skills[skill])
                else:
                    qualified_employees.intersection_update(self.employee_skills[skill])
            else:
                # 没有员工具备该技能
                return None
        
        if not qualified_employees:
            return None
        
        # 按工作量和成功率排序员工
        employee_scores = []
        for employee_id in qualified_employees:
            employee = self.ai_employees[employee_id]
            if employee["status"] != "active":
                continue
            
            # 计算员工得分 (工作量越低、成功率越高，得分越高)
            score = (1.0 / (employee["workload"] + 1)) * employee["success_rate"]
            employee_scores.append((score, employee_id))
        
        if not employee_scores:
            return None
        
        # 选择得分最高的员工
        employee_scores.sort(reverse=True)
        best_employee_id = employee_scores[0][1]
        
        return best_employee_id
    
    def _task_scheduler(self):
        """任务调度器"""
        while self.is_running:
            with self.lock:
                # 处理待分配任务
                for task_id in list(self.task_queue):
                    if self.tasks[task_id]["status"] != TaskStatus.PENDING.value:
                        self.task_queue.remove(task_id)
                        continue
                    
                    # 匹配员工
                    employee_id = self._match_employee_to_task(task_id)
                    if employee_id:
                        # 分配任务
                        self._assign_task(task_id, employee_id)
                        self.task_queue.remove(task_id)
            
            time.sleep(1)
    
    def _assign_task(self, task_id, employee_id):
        """分配任务给AI员工"""
        with self.lock:
            task = self.tasks[task_id]
            employee = self.ai_employees[employee_id]
            
            # 更新任务状态
            task["status"] = TaskStatus.ASSIGNED.value
            task["assigned_to"] = employee_id
            
            # 更新员工工作量
            employee["workload"] += 1
            self.employee_workload[employee_id] += 1
            
            logger.info(f"任务已分配: {task_id} -> {employee_id} ({employee['name']})")
            
            # 启动任务执行
            threading.Thread(target=self._execute_task, args=(task_id, employee_id)).start()
    
    def _execute_task(self, task_id, employee_id):
        """执行任务"""
        with self.lock:
            task = self.tasks[task_id]
            task["status"] = TaskStatus.RUNNING.value
            task["started_at"] = time.time()
        
        try:
            logger.info(f"开始执行任务: {task_id} - {task['name']} (员工: {employee_id})")
            
            # 模拟任务执行
            time.sleep(3)  # 模拟任务耗时
            
            # 任务执行成功
            with self.lock:
                task["status"] = TaskStatus.COMPLETED.value
                task["completed_at"] = time.time()
                task["result"] = f"任务执行成功: {task_id}"
                
                # 更新员工信息
                employee = self.ai_employees[employee_id]
                employee["workload"] -= 1
                employee["completed_tasks"] += 1
                employee["success_rate"] = (
                    (employee["success_rate"] * (employee["completed_tasks"] - 1) + 1.0) / 
                    employee["completed_tasks"]
                )
                employee["last_active"] = time.time()
                
                self.employee_workload[employee_id] -= 1
                
                # 添加到任务历史
                self.task_history.append(task.copy())
                
            logger.info(f"任务执行完成: {task_id} - {task['name']}")
            
        except Exception as e:
            with self.lock:
                task["status"] = TaskStatus.FAILED.value
                task["completed_at"] = time.time()
                task["error"] = str(e)
                
                # 更新员工信息
                employee = self.ai_employees[employee_id]
                employee["workload"] -= 1
                employee["completed_tasks"] += 1
                employee["success_rate"] = (
                    (employee["success_rate"] * (employee["completed_tasks"] - 1) + 0.0) / 
                    employee["completed_tasks"]
                )
                employee["last_active"] = time.time()
                
                self.employee_workload[employee_id] -= 1
                
                # 添加到任务历史
                self.task_history.append(task.copy())
                
            logger.error(f"任务执行失败: {task_id} - {task['name']}, 错误: {str(e)}")
    
    def _system_monitor(self):
        """系统监控"""
        while self.is_running:
            with self.lock:
                # 监控员工状态
                current_time = time.time()
                for employee_id, employee in self.ai_employees.items():
                    if current_time - employee["last_active"] > 300:  # 5分钟未活跃
                        employee["status"] = "idle"
                        logger.warning(f"AI员工已闲置: {employee_id} - {employee['name']}")
                
                # 更新系统监控信息
                self.system_monitor = {
                    "timestamp": current_time,
                    "total_employees": len(self.ai_employees),
                    "active_employees": len([e for e in self.ai_employees.values() if e["status"] == "active"]),
                    "total_tasks": len(self.tasks),
                    "pending_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.PENDING.value]),
                    "running_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.RUNNING.value]),
                    "completed_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.COMPLETED.value]),
                    "failed_tasks": len([t for t in self.tasks.values() if t["status"] == TaskStatus.FAILED.value])
                }
            
            time.sleep(30)  # 每30秒监控一次
    
    def _auto_optimize(self):
        """自动优化系统"""
        while self.is_running:
            with self.lock:
                logger.info("执行系统自动优化...")
                
                # 优化任务队列
                self._sort_task_queue()
                
                # 检查系统负载
                if self.system_monitor.get("running_tasks", 0) > len(self.ai_employees) * 2:
                    logger.warning("系统负载过高，建议增加AI员工数量")
                
                # 分析任务成功率
                if self.system_monitor.get("failed_tasks", 0) > self.system_monitor.get("completed_tasks", 1) * 0.1:
                    logger.warning("任务失败率过高，建议检查AI员工技能和任务分配")
            
            time.sleep(60)  # 每分钟优化一次
    
    def get_system_status(self):
        """获取系统状态"""
        with self.lock:
            return self.system_monitor.copy()
    
    def list_ai_employees(self, status=None):
        """列出AI员工"""
        with self.lock:
            if status:
                return [e for e in self.ai_employees.values() if e["status"] == status]
            return list(self.ai_employees.values())
    
    def list_tasks(self, status=None):
        """列出任务"""
        with self.lock:
            if status:
                return [t for t in self.tasks.values() if t["status"] == status]
            return list(self.tasks.values())
    
    def get_task_history(self, limit=10):
        """获取任务历史"""
        with self.lock:
            return self.task_history[-limit:]
    
    def auto_instantiate_ai_employees(self):
        """自动实例化AI员工"""
        logger.info("开始自动实例化AI员工...")
        
        # AI员工配置
        employee_configs = [
            {
                "type": "developer",
                "name": "AI开发者",
                "skills": ["code_development", "feature_implementation", "bug_fixing", "code_review"],
                "responsibilities": ["系统开发", "功能实现", "bug修复", "代码审查"]
            },
            {
                "type": "tester",
                "name": "AI测试员",
                "skills": ["test_case_design", "test_execution", "bug_reporting", "performance_testing"],
                "responsibilities": ["测试用例设计", "测试执行", "bug报告", "性能测试"]
            },
            {
                "type": "monitor",
                "name": "AI监控员",
                "skills": ["system_monitoring", "performance_optimization", "alert_handling", "log_analysis"],
                "responsibilities": ["系统监控", "性能优化", "告警处理", "日志分析"]
            },
            {
                "type": "manager",
                "name": "AI管理员",
                "skills": ["system_management", "resource_scheduling", "task_allocation", "team_coordination"],
                "responsibilities": ["系统管理", "资源调度", "任务分配", "团队协调"]
            },
            {
                "type": "optimizer",
                "name": "AI优化师",
                "skills": ["system_optimization", "algorithm_improvement", "performance_tuning", "resource_optimization"],
                "responsibilities": ["系统优化", "算法改进", "性能调优", "资源优化"]
            }
        ]
        
        # 自动创建AI员工
        for config in employee_configs:
            employee_id = f"ai_employee_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            self.register_ai_employee(
                employee_id=employee_id,
                name=f"{config['name']}_{uuid.uuid4().hex[:2]}",
                employee_type=config['type'],
                skills=config['skills'],
                responsibilities=config['responsibilities']
            )
        
        logger.info(f"自动实例化完成，共创建 {len(employee_configs)} 个AI员工")
        return True

# 测试系统
def main():
    """测试高级AI员工系统"""
    print("=" * 60)
    print("高级AI员工系统测试")
    print("=" * 60)
    
    # 创建AI员工系统实例
    ai_system = AIEmployeeSystem()
    
    # 自动实例化AI员工
    ai_system.auto_instantiate_ai_employees()
    
    # 列出AI员工
    print("\nAI员工列表:")
    employees = ai_system.list_ai_employees()
    for employee in employees:
        print(f"  ID: {employee['employee_id']}")
        print(f"  名称: {employee['name']}")
        print(f"  类型: {employee['type']}")
        print(f"  技能: {', '.join(employee['skills'])}")
        print(f"  状态: {employee['status']}")
        print()
    
    # 创建测试任务
    print("创建测试任务...")
    
    # 开发任务
    ai_system.create_task(
        task_id=f"task_dev_{int(time.time())}",
        name="开发新功能",
        description="开发AI员工系统的新功能",
        required_skills=["code_development", "feature_implementation"],
        priority=TaskPriority.HIGH
    )
    
    # 测试任务
    ai_system.create_task(
        task_id=f"task_test_{int(time.time())}",
        name="测试新功能",
        description="测试新开发的功能",
        required_skills=["test_case_design", "test_execution"],
        priority=TaskPriority.MEDIUM
    )
    
    # 监控任务
    ai_system.create_task(
        task_id=f"task_monitor_{int(time.time())}",
        name="监控系统性能",
        description="监控系统运行性能",
        required_skills=["system_monitoring", "performance_optimization"],
        priority=TaskPriority.LOW
    )
    
    # 优化任务
    ai_system.create_task(
        task_id=f"task_optimize_{int(time.time())}",
        name="优化系统",
        description="优化AI员工系统",
        required_skills=["system_optimization", "algorithm_improvement"],
        priority=TaskPriority.MEDIUM
    )
    
    # 等待任务执行
    print("\n等待任务执行...")
    time.sleep(5)
    
    # 查看任务状态
    print("\n任务状态:")
    tasks = ai_system.list_tasks()
    for task in tasks:
        print(f"  ID: {task['task_id']}")
        print(f"  名称: {task['name']}")
        print(f"  状态: {task['status']}")
        print(f"  优先级: {task['priority']}")
        print(f"  分配给: {task['assigned_to']}")
        print()
    
    # 查看系统状态
    print("系统状态:")
    status = ai_system.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # 等待更多任务完成
    print("\n等待更多任务完成...")
    time.sleep(5)
    
    # 查看任务历史
    print("\n任务历史:")
    history = ai_system.get_task_history(10)
    for task in history:
        print(f"  {task['task_id']} - {task['name']}: {task['status']}")
    
    print("\n" + "=" * 60)
    print("高级AI员工系统测试完成")
    print("=" * 60)
    
    # 停止系统
    ai_system.stop()

if __name__ == "__main__":
    main()
