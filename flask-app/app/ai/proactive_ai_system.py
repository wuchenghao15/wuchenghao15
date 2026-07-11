# -*- coding: utf-8 -*-
"""
AI员工主动运作系统
实现从被动触发到主动发现和执行的转变
- 自主需求发现
- 主动任务调度
- 自我学习优化
- 协作式工作流
"""

import os
import sys
import time
import json
import uuid
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举定义
# ============================================================================

class InitiativeLevel(Enum):
    """主动性等级"""
    PASSIVE = "passive"           # 被动 - 只在触发时工作
    REACTIVE = "reactive"         # 反应 - 对问题快速响应
    PROACTIVE = "proactive"       # 主动 - 主动发现问题
    SELF_DRIVEN = "self_driven"   # 自驱 - 自主规划和执行
    AUTONOMOUS = "autonomous"     # 自主 - 完全自主决策


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 50
    LOW = 20
    TRIVIAL = 5


class TaskStatus(Enum):
    """任务状态"""
    DISCOVERED = "discovered"     # 已发现
    ANALYZING = "analyzing"       # 分析中
    PLANNED = "planned"           # 已规划
    ASSIGNED = "assigned"         # 已分配
    IN_PROGRESS = "in_progress"   # 执行中
    REVIEWING = "reviewing"       # 复核中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class DiscoverySource(Enum):
    """需求发现来源"""
    ERROR_LOG = "error_log"               # 错误日志
    PERFORMANCE_METRIC = "performance"    # 性能指标
    USER_BEHAVIOR = "user_behavior"       # 用户行为
    SYSTEM_HEALTH = "system_health"       # 系统健康
    DATA_ANOMALY = "data_anomaly"         # 数据异常
    SECURITY_ALERT = "security_alert"     # 安全告警
    PATTERN_ANALYSIS = "pattern_analysis" # 模式分析
    PREDICTIVE = "predictive"             # 预测性发现
    KNOWLEDGE_GAP = "knowledge_gap"       # 知识缺口
    OPTIMIZATION = "optimization"         # 优化机会


class LearningType(Enum):
    """学习类型"""
    FROM_SUCCESS = "from_success"         # 从成功中学习
    FROM_FAILURE = "from_failure"         # 从失败中学习
    FROM_FEEDBACK = "from_feedback"       # 从反馈中学习
    FROM_OBSERVATION = "from_observation" # 从观察中学习
    FROM_COLLABORATION = "from_collab"    # 从协作中学习
    FROM_PATTERN = "from_pattern"         # 从模式中学习


# ============================================================================
# 主动任务
# ============================================================================

class ProactiveTask:
    """主动任务"""

    def __init__(self, title: str, description: str, 
                 source: DiscoverySource, priority: TaskPriority,
                 category: str, required_skills: List[str] = None):
        self.task_id = f"task_{uuid.uuid4().hex[:12]}"
        self.title = title
        self.description = description
        self.source = source
        self.priority = priority
        self.category = category
        self.required_skills = required_skills or []
        self.status = TaskStatus.DISCOVERED
        self.created_at = datetime.now()
        self.assigned_to = None
        self.assigned_at = None
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.progress = 0.0
        self.subtasks: List['ProactiveTask'] = []
        self.dependencies: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.attempts = 0
        self.max_attempts = 3
        self.feedback_score = None
        self.learned_insights: List[str] = []

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'source': self.source.value,
            'priority': self.priority.value,
            'category': self.category,
            'required_skills': self.required_skills,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'assigned_to': self.assigned_to,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'progress': self.progress,
            'subtasks_count': len(self.subtasks),
            'attempts': self.attempts,
            'feedback_score': self.feedback_score,
            'metadata': self.metadata
        }


# ============================================================================
# 自主需求发现器
# ============================================================================

class AutonomousDiscoveryEngine:
    """自主需求发现引擎"""

    def __init__(self):
        self._discovery_modules: Dict[str, Callable] = {}
        self._discovery_history: deque = deque(maxlen=1000)
        self._pattern_memory: Dict[str, List[Dict]] = defaultdict(list)
        self._anomaly_thresholds: Dict[str, float] = {}
        self._baseline_metrics: Dict[str, float] = {}
        self._running = False
        self._lock = threading.Lock()
        self._discovery_interval = 60
        self._callbacks: List[Callable] = []

        self._register_default_modules()

    def _register_default_modules(self):
        """注册默认发现模块"""
        self.register_module('error_pattern_analysis', self._discover_error_patterns)
        self.register_module('performance_anomaly', self._discover_performance_anomalies)
        self.register_module('user_behavior_pattern', self._discover_behavior_patterns)
        self.register_module('system_health_monitor', self._discover_health_issues)
        self.register_module('data_integrity_check', self._discover_data_anomalies)
        self.register_module('optimization_opportunity', self._discover_optimization_opportunities)
        self.register_module('knowledge_gap_detector', self._discover_knowledge_gaps)
        self.register_module('predictive_maintenance', self._predictive_discovery)

    def register_module(self, name: str, module_func: Callable):
        """注册发现模块"""
        self._discovery_modules[name] = module_func
        logger.info(f"注册发现模块: {name}")

    def register_callback(self, callback: Callable):
        """注册发现回调"""
        self._callbacks.append(callback)

    def start(self):
        """启动发现引擎"""
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._discovery_loop, daemon=True, name="discovery-engine").start()
        logger.info("自主需求发现引擎已启动")

    def stop(self):
        """停止发现引擎"""
        self._running = False
        logger.info("自主需求发现引擎已停止")

    def _discovery_loop(self):
        """发现循环"""
        while self._running:
            try:
                self.run_discovery_cycle()
            except Exception as e:
                logger.error(f"发现周期异常: {e}")
            time.sleep(self._discovery_interval)

    def run_discovery_cycle(self) -> List[ProactiveTask]:
        """运行一个发现周期"""
        discovered_tasks = []
        
        for module_name, module_func in self._discovery_modules.items():
            try:
                tasks = module_func()
                if tasks:
                    if isinstance(tasks, list):
                        discovered_tasks.extend(tasks)
                    else:
                        discovered_tasks.append(tasks)
                    
                    self._record_discovery(module_name, tasks)
                    
                    for callback in self._callbacks:
                        try:
                            callback(module_name, tasks)
                        except Exception as e:
                            logger.error(f"发现回调异常: {e}")
                            
            except Exception as e:
                logger.error(f"发现模块 {module_name} 执行失败: {e}")
        
        return discovered_tasks

    def _record_discovery(self, module_name: str, tasks: List[ProactiveTask]):
        """记录发现历史"""
        with self._lock:
            self._discovery_history.append({
                'timestamp': datetime.now(),
                'module': module_name,
                'tasks_count': len(tasks) if isinstance(tasks, list) else 1,
                'tasks': [t.task_id for t in tasks] if isinstance(tasks, list) else [tasks.task_id]
            })

    def _discover_error_patterns(self) -> List[ProactiveTask]:
        """发现错误模式"""
        tasks = []
        try:
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查最近的错误模式
            try:
                cursor.execute('''
                    SELECT error_type, COUNT(*) as cnt 
                    FROM error_reports 
                    WHERE created_at > datetime('now', '-1 hour')
                    GROUP BY error_type 
                    HAVING cnt > 3
                    ORDER BY cnt DESC
                    LIMIT 10
                ''')
                patterns = cursor.fetchall()
                
                for error_type, count in patterns:
                    task = ProactiveTask(
                        title=f"高频错误分析: {error_type}",
                        description=f"最近1小时内 {error_type} 类型错误发生 {count} 次，超过阈值，需要分析根因并修复",
                        source=DiscoverySource.ERROR_LOG,
                        priority=TaskPriority.HIGH if count > 10 else TaskPriority.MEDIUM,
                        category='error_analysis',
                        required_skills=['error_analysis', 'debugging']
                    )
                    task.metadata['error_type'] = error_type
                    task.metadata['error_count'] = count
                    tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"错误模式发现: {e}")
        
        return tasks

    def _discover_performance_anomalies(self) -> List[ProactiveTask]:
        """发现性能异常"""
        tasks = []
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            
            if cpu_percent > 90:
                task = ProactiveTask(
                    title="CPU使用率过高",
                    description=f"CPU使用率达到 {cpu_percent:.1f}%，可能存在性能瓶颈，需要分析进程并优化",
                    source=DiscoverySource.PERFORMANCE_METRIC,
                    priority=TaskPriority.HIGH,
                    category='performance',
                    required_skills=['performance_optimization', 'system_analysis']
                )
                task.metadata['cpu_percent'] = cpu_percent
                tasks.append(task)
            
            if memory.percent > 90:
                task = ProactiveTask(
                    title="内存使用率过高",
                    description=f"内存使用率达到 {memory.percent:.1f}%，可能存在内存泄漏，需要分析并优化",
                    source=DiscoverySource.PERFORMANCE_METRIC,
                    priority=TaskPriority.HIGH,
                    category='performance',
                    required_skills=['memory_optimization', 'system_analysis']
                )
                task.metadata['memory_percent'] = memory.percent
                tasks.append(task)
                
        except Exception as e:
            logger.debug(f"性能异常发现: {e}")
        
        return tasks

    def _discover_behavior_patterns(self) -> List[ProactiveTask]:
        """发现用户行为模式"""
        tasks = []
        try:
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # 分析用户访问热点
                cursor.execute('''
                    SELECT page, COUNT(*) as visits
                    FROM page_views
                    WHERE timestamp > datetime('now', '-24 hour')
                    GROUP BY page
                    ORDER BY visits DESC
                    LIMIT 5
                ''')
                top_pages = cursor.fetchall()
                
                if len(top_pages) >= 5:
                    top_page = top_pages[0]
                    if top_page[1] > 1000:
                        task = ProactiveTask(
                            title=f"热门页面优化分析: {top_page[0]}",
                            description=f"页面 {top_page[0]} 24小时内访问 {top_page[1]} 次，建议分析并优化性能",
                            source=DiscoverySource.USER_BEHAVIOR,
                            priority=TaskPriority.MEDIUM,
                            category='optimization',
                            required_skills=['frontend_optimization', 'ux_design']
                        )
                        task.metadata['page'] = top_page[0]
                        task.metadata['visits'] = top_page[1]
                        tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"行为模式发现: {e}")
        
        return tasks

    def _discover_health_issues(self) -> List[ProactiveTask]:
        """发现系统健康问题"""
        tasks = []
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            if disk.percent > 85:
                task = ProactiveTask(
                    title="磁盘空间不足预警",
                    description=f"磁盘使用率达到 {disk.percent:.1f}%，建议清理临时文件和执行数据归档",
                    source=DiscoverySource.SYSTEM_HEALTH,
                    priority=TaskPriority.HIGH if disk.percent > 95 else TaskPriority.MEDIUM,
                    category='maintenance',
                    required_skills=['system_maintenance', 'storage_management']
                )
                task.metadata['disk_percent'] = disk.percent
                tasks.append(task)
            
            # 检查活跃连接数
            try:
                connections = psutil.net_connections()
                if len(connections) > 500:
                    task = ProactiveTask(
                        title="网络连接数过高",
                        description=f"当前网络连接数 {len(connections)}，可能存在连接泄漏",
                        source=DiscoverySource.SYSTEM_HEALTH,
                        priority=TaskPriority.MEDIUM,
                        category='network',
                        required_skills=['network_analysis', 'connection_management']
                    )
                    task.metadata['connections'] = len(connections)
                    tasks.append(task)
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"健康问题发现: {e}")
        
        return tasks

    def _discover_data_anomalies(self) -> List[ProactiveTask]:
        """发现数据异常"""
        tasks = []
        try:
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查重复数据
            try:
                cursor.execute('''
                    SELECT COUNT(*) FROM (
                        SELECT username, email, COUNT(*) as cnt
                        FROM users
                        GROUP BY username, email
                        HAVING cnt > 1
                    )
                ''')
                dup_count = cursor.fetchone()[0]
                if dup_count > 0:
                    task = ProactiveTask(
                        title="用户数据重复检测",
                        description=f"检测到 {dup_count} 组重复用户数据，需要去重并添加唯一约束",
                        source=DiscoverySource.DATA_ANOMALY,
                        priority=TaskPriority.MEDIUM,
                        category='data_quality',
                        required_skills=['data_cleaning', 'database_design']
                    )
                    task.metadata['duplicate_count'] = dup_count
                    tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"数据异常发现: {e}")
        
        return tasks

    def _discover_optimization_opportunities(self) -> List[ProactiveTask]:
        """发现优化机会"""
        tasks = []
        try:
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查慢速查询（假设有查询日志表）
            try:
                cursor.execute('''
                    SELECT query, avg_time, call_count
                    FROM query_performance
                    WHERE avg_time > 1000
                    ORDER BY avg_time DESC
                    LIMIT 5
                ''')
                slow_queries = cursor.fetchall()
                
                for query, avg_time, call_count in slow_queries:
                    task = ProactiveTask(
                        title="慢查询优化",
                        description=f"查询平均耗时 {avg_time:.0f}ms，调用 {call_count} 次，建议优化索引或查询语句",
                        source=DiscoverySource.OPTIMIZATION,
                        priority=TaskPriority.MEDIUM,
                        category='database_optimization',
                        required_skills=['sql_optimization', 'index_design']
                    )
                    task.metadata['query'] = query[:100]
                    task.metadata['avg_time'] = avg_time
                    task.metadata['call_count'] = call_count
                    tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"优化机会发现: {e}")
        
        return tasks

    def _discover_knowledge_gaps(self) -> List[ProactiveTask]:
        """发现知识缺口"""
        tasks = []
        try:
            # 分析错误类型分布，识别AI员工不擅长的领域
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    SELECT error_category, 
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                           SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
                    FROM ai_employee_tasks
                    WHERE created_at > datetime('now', '-7 day')
                    GROUP BY error_category
                    HAVING failed > success * 2
                    ORDER BY failed DESC
                    LIMIT 5
                ''')
                weak_areas = cursor.fetchall()
                
                for category, failed, success in weak_areas:
                    if failed > 5:
                        task = ProactiveTask(
                            title=f"能力提升: {category}",
                            description=f"AI员工在 {category} 领域失败 {failed} 次，成功率偏低，需要专项训练",
                            source=DiscoverySource.KNOWLEDGE_GAP,
                            priority=TaskPriority.MEDIUM,
                            category='training',
                            required_skills=['training', 'knowledge_transfer']
                        )
                        task.metadata['category'] = category
                        task.metadata['failed_count'] = failed
                        task.metadata['success_count'] = success
                        tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"知识缺口发现: {e}")
        
        return tasks

    def _predictive_discovery(self) -> List[ProactiveTask]:
        """预测性发现"""
        tasks = []
        try:
            db_path = self._get_db_path()
            if not db_path or not os.path.exists(db_path):
                return tasks
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 预测磁盘空间耗尽时间
            try:
                import psutil
                disk = psutil.disk_usage('/')
                
                if disk.percent > 70:
                    # 估算增长速率
                    cursor.execute('''
                        SELECT COUNT(*) FROM backup_records
                        WHERE created_at > datetime('now', '-7 day')
                    ''')
                    weekly_backups = cursor.fetchone()[0]
                    
                    if weekly_backups > 0:
                        task = ProactiveTask(
                            title="预测性存储管理",
                            description=f"基于当前增长趋势，建议提前规划存储扩容或实施数据归档策略",
                            source=DiscoverySource.PREDICTIVE,
                            priority=TaskPriority.LOW,
                            category='capacity_planning',
                            required_skills=['capacity_planning', 'storage_management']
                        )
                        task.metadata['current_usage'] = disk.percent
                        tasks.append(task)
            except Exception:
                pass
            
            conn.close()
        except Exception as e:
            logger.debug(f"预测性发现: {e}")
        
        return tasks

    def _get_db_path(self) -> Optional[str]:
        """获取数据库路径"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'app.db')
            return db_path if os.path.exists(db_path) else None
        except Exception:
            return None

    def get_discovery_stats(self) -> Dict:
        """获取发现统计"""
        with self._lock:
            stats = {
                'modules_count': len(self._discovery_modules),
                'history_count': len(self._discovery_history),
                'modules': list(self._discovery_modules.keys()),
                'running': self._running
            }
        return stats

    def set_discovery_interval(self, interval: int):
        """设置发现间隔"""
        self._discovery_interval = max(10, interval)
        logger.info(f"发现间隔设置为 {self._discovery_interval} 秒")


# ============================================================================
# 主动任务调度器
# ============================================================================

class ProactiveTaskScheduler:
    """主动任务调度器"""

    def __init__(self):
        self._task_queue: List[ProactiveTask] = []
        self._active_tasks: Dict[str, ProactiveTask] = {}
        self._completed_tasks: deque = deque(maxlen=500)
        self._failed_tasks: deque = deque(maxlen=200)
        self._queue_lock = threading.Lock()
        self._running = False
        self._max_concurrent = 5
        self._workers: List[threading.Thread] = []
        self._task_executors: Dict[str, Callable] = {}
        self._scheduling_strategy = 'priority_fifo'
        self._idle_callbacks: List[Callable] = []

    def register_executor(self, category: str, executor: Callable):
        """注册任务执行器"""
        self._task_executors[category] = executor
        logger.info(f"注册任务执行器: {category}")

    def register_idle_callback(self, callback: Callable):
        """注册空闲回调"""
        self._idle_callbacks.append(callback)

    def start(self, num_workers: int = 3):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._max_concurrent = num_workers
        
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"task-worker-{i}"
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"主动任务调度器已启动，工作线程数: {num_workers}")

    def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("主动任务调度器已停止")

    def add_task(self, task: ProactiveTask) -> bool:
        """添加任务到队列"""
        with self._queue_lock:
            # 检查是否重复
            for existing in self._task_queue:
                if existing.title == task.title and existing.status in [TaskStatus.DISCOVERED, TaskStatus.PLANNED]:
                    logger.debug(f"跳过重复任务: {task.title}")
                    return False
            
            self._task_queue.append(task)
            self._sort_queue()
            logger.info(f"任务入队: {task.title} (优先级: {task.priority.value})")
            return True

    def _sort_queue(self):
        """排序队列"""
        self._task_queue.sort(key=lambda t: t.priority.value, reverse=True)

    def _worker_loop(self):
        """工作线程循环"""
        while self._running:
            try:
                task = self._get_next_task()
                if task:
                    self._execute_task(task)
                else:
                    # 空闲时调用回调
                    for callback in self._idle_callbacks:
                        try:
                            callback()
                        except Exception as e:
                            logger.error(f"空闲回调异常: {e}")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"工作线程异常: {e}")
                time.sleep(1)

    def _get_next_task(self) -> Optional[ProactiveTask]:
        """获取下一个任务"""
        with self._queue_lock:
            if len(self._active_tasks) >= self._max_concurrent:
                return None
            
            if not self._task_queue:
                return None
            
            task = self._task_queue.pop(0)
            task.status = TaskStatus.ASSIGNED
            self._active_tasks[task.task_id] = task
            return task

    def _execute_task(self, task: ProactiveTask):
        """执行任务"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.attempts += 1
        
        logger.info(f"开始执行任务: {task.title}")
        
        try:
            executor = self._task_executors.get(task.category)
            if executor:
                result = executor(task)
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                logger.info(f"任务完成: {task.title}")
            else:
                # 通用处理
                task.result = self._generic_execute(task)
                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                logger.info(f"任务完成(通用): {task.title}")
                
        except Exception as e:
            task.error = e
            task.status = TaskStatus.FAILED
            logger.error(f"任务失败: {task.title}, 错误: {e}")
            
            # 重试逻辑
            if task.attempts < task.max_attempts:
                task.status = TaskStatus.PLANNED
                with self._queue_lock:
                    self._task_queue.append(task)
                    self._sort_queue()
                logger.info(f"任务重试: {task.title} (第 {task.attempts + 1} 次)")
        
        task.completed_at = datetime.now()
        
        with self._queue_lock:
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]
            
            if task.status == TaskStatus.COMPLETED:
                self._completed_tasks.append(task)
            elif task.status == TaskStatus.FAILED:
                self._failed_tasks.append(task)

    def _generic_execute(self, task: ProactiveTask) -> Dict:
        """通用任务执行"""
        result = {
            'analyzed': True,
            'recommendations': [],
            'actions_taken': []
        }
        
        # 根据任务类别进行分析
        if task.category == 'error_analysis':
            result['recommendations'].append('建议查看详细错误日志')
            result['recommendations'].append('检查相关代码模块')
        elif task.category == 'performance':
            result['recommendations'].append('建议进行性能分析')
            result['recommendations'].append('检查资源使用情况')
        elif task.category == 'maintenance':
            result['recommendations'].append('建议执行系统维护任务')
            result['recommendations'].append('清理临时文件')
        
        return result

    def get_queue_stats(self) -> Dict:
        """获取队列统计"""
        with self._queue_lock:
            return {
                'queued': len(self._task_queue),
                'active': len(self._active_tasks),
                'completed_today': len([t for t in self._completed_tasks 
                                       if t.completed_at and t.completed_at.date() == datetime.now().date()]),
                'failed_today': len([t for t in self._failed_tasks
                                    if t.completed_at and t.completed_at.date() == datetime.now().date()]),
                'total_completed': len(self._completed_tasks),
                'total_failed': len(self._failed_tasks),
                'executors': list(self._task_executors.keys()),
                'running': self._running
            }

    def get_task_list(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取任务列表"""
        tasks = []
        
        with self._queue_lock:
            # 队列中的任务
            for task in self._task_queue:
                if not status or task.status.value == status:
                    tasks.append(task.to_dict())
            
            # 活跃任务
            for task in self._active_tasks.values():
                if not status or task.status.value == status:
                    tasks.append(task.to_dict())
            
            # 已完成任务
            for task in list(self._completed_tasks)[-limit:]:
                if not status or task.status.value == status:
                    tasks.append(task.to_dict())
            
            # 失败任务
            for task in list(self._failed_tasks)[-limit:]:
                if not status or task.status.value == status:
                    tasks.append(task.to_dict())
        
        return sorted(tasks, key=lambda t: t.get('created_at', ''), reverse=True)[:limit]


# ============================================================================
# 自我学习引擎
# ============================================================================

class SelfLearningEngine:
    """自我学习引擎"""

    def __init__(self):
        self._knowledge_base: Dict[str, List[Dict]] = defaultdict(list)
        self._learning_records: deque = deque(maxlen=1000)
        self._skill_levels: Dict[str, float] = defaultdict(lambda: 0.5)
        self._improvement_tracking: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._learning_rate = 0.1
        self._auto_optimize = True

    def record_learning(self, learning_type: LearningType, source: str,
                       insight: str, impact: float = 0.0, metadata: Dict = None):
        """记录学习"""
        record = {
            'timestamp': datetime.now(),
            'type': learning_type.value,
            'source': source,
            'insight': insight,
            'impact': impact,
            'metadata': metadata or {}
        }
        
        with self._lock:
            self._learning_records.append(record)
            self._knowledge_base[learning_type.value].append(record)
            
            # 更新技能水平
            if impact > 0:
                category = metadata.get('category', 'general') if metadata else 'general'
                current_level = self._skill_levels.get(category, 0.5)
                improvement = impact * self._learning_rate
                new_level = min(1.0, current_level + improvement)
                self._skill_levels[category] = new_level
                self._improvement_tracking[category].append(new_level)
                
                # 只保留最近50个记录
                if len(self._improvement_tracking[category]) > 50:
                    self._improvement_tracking[category] = self._improvement_tracking[category][-50:]
        
        logger.debug(f"记录学习: {learning_type.value} - {insight[:50]}...")

    def learn_from_task(self, task: ProactiveTask):
        """从任务结果中学习"""
        if task.status == TaskStatus.COMPLETED:
            self.record_learning(
                learning_type=LearningType.FROM_SUCCESS,
                source=task.category,
                insight=f"成功完成任务: {task.title}",
                impact=0.05,
                metadata={'category': task.category, 'task_id': task.task_id}
            )
            if task.learned_insights:
                for insight in task.learned_insights:
                    self.record_learning(
                        learning_type=LearningType.FROM_OBSERVATION,
                        source=task.category,
                        insight=insight,
                        impact=0.02,
                        metadata={'category': task.category}
                    )
        elif task.status == TaskStatus.FAILED:
            self.record_learning(
                learning_type=LearningType.FROM_FAILURE,
                source=task.category,
                insight=f"任务失败: {task.title}, 错误: {task.error}",
                impact=0.1,
                metadata={'category': task.category, 'error': str(task.error)}
            )

    def get_skill_level(self, category: str) -> float:
        """获取技能水平"""
        with self._lock:
            return self._skill_levels.get(category, 0.5)

    def get_all_skills(self) -> Dict[str, float]:
        """获取所有技能水平"""
        with self._lock:
            return dict(self._skill_levels)

    def get_knowledge_stats(self) -> Dict:
        """获取知识统计"""
        with self._lock:
            return {
                'knowledge_entries': sum(len(v) for v in self._knowledge_base.values()),
                'learning_records': len(self._learning_records),
                'skill_categories': len(self._skill_levels),
                'skills': dict(self._skill_levels),
                'learning_rate': self._learning_rate,
                'auto_optimize': self._auto_optimize
            }

    def generate_improvement_suggestions(self) -> List[Dict]:
        """生成改进建议"""
        suggestions = []
        
        with self._lock:
            # 找出技能水平最低的领域
            sorted_skills = sorted(self._skill_levels.items(), key=lambda x: x[1])
            
            for category, level in sorted_skills[:5]:
                if level < 0.7:
                    suggestions.append({
                        'category': category,
                        'current_level': level,
                        'suggestion': f"建议加强 {category} 领域的训练",
                        'priority': 'high' if level < 0.4 else 'medium'
                    })
        
        return suggestions

    def set_learning_rate(self, rate: float):
        """设置学习率"""
        self._learning_rate = max(0.001, min(1.0, rate))


# ============================================================================
# AI员工主动运作中心
# ============================================================================

class ProactiveAICenter:
    """AI员工主动运作中心"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化"""
        self.discovery_engine = AutonomousDiscoveryEngine()
        self.task_scheduler = ProactiveTaskScheduler()
        self.learning_engine = SelfLearningEngine()
        
        self._initiative_level = InitiativeLevel.PROACTIVE
        self._running = False
        self._start_time = None
        
        # 连接发现引擎和调度器
        self.discovery_engine.register_callback(self._on_discovered_tasks)
        
        # 连接调度器和学习引擎
        self._setup_executors()
        
        # 空闲时进行自我提升
        self.task_scheduler.register_idle_callback(self._idle_self_improvement)
        
        logger.info("AI员工主动运作中心初始化完成")

    def _setup_executors(self):
        """设置任务执行器"""
        # 错误分析执行器
        def error_analysis_executor(task: ProactiveTask) -> Dict:
            result = {
                'analysis': '完成错误模式分析',
                'root_causes': [],
                'recommendations': []
            }
            task.learned_insights.append(f"分析了 {task.metadata.get('error_type', '未知')} 类型的错误模式")
            return result
        
        # 性能优化执行器
        def performance_executor(task: ProactiveTask) -> Dict:
            result = {
                'analysis': '完成性能分析',
                'bottlenecks': [],
                'optimizations': []
            }
            task.learned_insights.append(f"识别了系统性能瓶颈: CPU/内存")
            return result
        
        self.task_scheduler.register_executor('error_analysis', error_analysis_executor)
        self.task_scheduler.register_executor('performance', performance_executor)

    def _on_discovered_tasks(self, module_name: str, tasks: List[ProactiveTask]):
        """发现任务回调"""
        for task in tasks:
            added = self.task_scheduler.add_task(task)
            if added:
                logger.debug(f"发现新任务: {task.title} (来自 {module_name})")

    def _idle_self_improvement(self):
        """空闲时自我提升"""
        if self._initiative_level.value in [InitiativeLevel.SELF_DRIVEN.value, 
                                           InitiativeLevel.AUTONOMOUS.value]:
            # 自驱模式下，空闲时主动学习
            suggestions = self.learning_engine.generate_improvement_suggestions()
            for suggestion in suggestions:
                if suggestion['priority'] == 'high':
                    task = ProactiveTask(
                        title=f"自我提升: {suggestion['category']}",
                        description=suggestion['suggestion'],
                        source=DiscoverySource.KNOWLEDGE_GAP,
                        priority=TaskPriority.LOW,
                        category='training',
                        required_skills=['self_learning']
                    )
                    task.metadata['improvement_target'] = suggestion['category']
                    self.task_scheduler.add_task(task)
                    break

    def start(self, num_workers: int = 3):
        """启动主动运作系统"""
        if self._running:
            return
        
        self._running = True
        self._start_time = datetime.now()
        
        self.discovery_engine.start()
        self.task_scheduler.start(num_workers)
        
        logger.info(f"AI员工主动运作系统已启动 (主动性等级: {self._initiative_level.value})")

    def stop(self):
        """停止主动运作系统"""
        self._running = False
        self.discovery_engine.stop()
        self.task_scheduler.stop()
        logger.info("AI员工主动运作系统已停止")

    def set_initiative_level(self, level: InitiativeLevel):
        """设置主动性等级"""
        self._initiative_level = level
        
        # 根据等级调整发现频率
        if level == InitiativeLevel.PASSIVE:
            self.discovery_engine.set_discovery_interval(300)
            self.discovery_engine.stop()
        elif level == InitiativeLevel.REACTIVE:
            self.discovery_engine.set_discovery_interval(120)
        elif level == InitiativeLevel.PROACTIVE:
            self.discovery_engine.set_discovery_interval(60)
            if not self.discovery_engine._running:
                self.discovery_engine.start()
        elif level == InitiativeLevel.SELF_DRIVEN:
            self.discovery_engine.set_discovery_interval(30)
            if not self.discovery_engine._running:
                self.discovery_engine.start()
        elif level == InitiativeLevel.AUTONOMOUS:
            self.discovery_engine.set_discovery_interval(15)
            if not self.discovery_engine._running:
                self.discovery_engine.start()
        
        logger.info(f"主动性等级设置为: {level.value}")

    def trigger_manual_discovery(self) -> List[Dict]:
        """触发手动发现"""
        tasks = self.discovery_engine.run_discovery_cycle()
        return [t.to_dict() for t in tasks]

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        uptime = None
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
        
        return {
            'running': self._running,
            'initiative_level': self._initiative_level.value,
            'uptime_seconds': uptime,
            'discovery': self.discovery_engine.get_discovery_stats(),
            'scheduler': self.task_scheduler.get_queue_stats(),
            'learning': self.learning_engine.get_knowledge_stats(),
            'improvement_suggestions': self.learning_engine.generate_improvement_suggestions()
        }

    def get_task_list(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取任务列表"""
        return self.task_scheduler.get_task_list(status, limit)

    def create_custom_task(self, title: str, description: str,
                          priority: str = 'medium', category: str = 'custom',
                          required_skills: List[str] = None) -> Dict:
        """创建自定义任务"""
        priority_map = {
            'critical': TaskPriority.CRITICAL,
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW,
            'trivial': TaskPriority.TRIVIAL
        }
        
        task = ProactiveTask(
            title=title,
            description=description,
            source=DiscoverySource.PATTERN_ANALYSIS,
            priority=priority_map.get(priority, TaskPriority.MEDIUM),
            category=category,
            required_skills=required_skills or []
        )
        
        self.task_scheduler.add_task(task)
        return task.to_dict()


# 全局单例
proactive_ai_center = ProactiveAICenter()
