#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影子系统 V2.0 (Shadow System)
增强版影子系统，用于在不影响主系统的情况下进行测试、监控和验证
"""

import time
import uuid
import logging
import threading
import json
import sqlite3
import hashlib
import queue
import os
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shadow_system_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ShadowSystemV2')

class ShadowSystemStatus(Enum):
    """影子系统状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    DEGRADED = "degraded"

class ShadowMode(Enum):
    """影子系统模式枚举"""
    MONITOR = "monitor"
    PARALLEL = "parallel"
    RECORD = "record"
    REPLAY = "replay"
    STRESS_TEST = "stress_test"
    FAULT_INJECTION = "fault_injection"
    PERFORMANCE_TEST = "performance_test"

class FaultType(Enum):
    """故障类型枚举"""
    DELAY = "delay"
    ERROR = "error"
    DATA_CORRUPTION = "data_corruption"
    NETWORK_LATENCY = "network_latency"
    RANDOM_FAILURE = "random_failure"

@dataclass
class FaultConfig:
    """故障配置"""
    fault_type: FaultType
    probability: float = 0.1
    delay_ms: int = 1000
    error_message: str = "Simulated fault"

@dataclass
class InputRecord:
    """输入记录"""
    input_id: str
    input_data: Dict
    timestamp: float
    trace_id: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ComparisonResult:
    """比较结果"""
    input_id: str
    timestamp: float
    match: bool
    differences: List[Dict]
    main_result: Optional[Dict]
    shadow_result: Optional[Dict]
    processing_time: float
    trace_id: str = ""

class ShadowSystem:
    """增强版影子系统"""

    def __init__(self, system_id: str = None, main_system=None):
        """初始化影子系统"""
        self.system_id = system_id or f"shadow_{uuid.uuid4().hex[:8]}"
        self.main_system = main_system
        self.status = ShadowSystemStatus.INITIALIZING
        self.mode = ShadowMode.PARALLEL
        self.is_running = False
        self.input_queue = queue.Queue(maxsize=10000)
        self.processing_threads = []
        self.max_threads = 16
        self.min_threads = 2
        self.current_thread_count = 4
        self.comparison_results = deque(maxlen=10000)
        self.input_records = deque(maxlen=100000)
        self.replay_index = 0
        self.last_scaling_time = 0
        self.last_mode_switch_time = time.time()
        self.trace_id_counter = 0
        
        self.lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.config = {
            "comparison_enabled": True,
            "recording_enabled": True,
            "max_queue_size": 10000,
            "max_results_size": 10000,
            "max_records_size": 100000,
            "auto_scaling_enabled": True,
            "scaling_threshold_high": 200,
            "scaling_threshold_low": 20,
            "performance_monitoring_enabled": True,
            "smart_mode_switching": True,
            "mode_switch_threshold": 0.1,
            "fault_injection_enabled": False,
            "stress_test_concurrent": 100,
            "performance_test_duration": 60,
            "database_logging_enabled": True,
            "detailed_tracing_enabled": True,
            "anomaly_detection_enabled": True,
            "alert_threshold_mismatch_rate": 0.2,
            "alert_threshold_latency_ms": 1000,
            "health_check_interval": 30,
            "metrics_retention_hours": 24
        }
        
        self.performance_metrics = {
            "total_processed": 0,
            "total_matched": 0,
            "total_mismatched": 0,
            "average_processing_time": 0,
            "average_latency": 0,
            "queue_size_history": deque(maxlen=1000),
            "processing_time_history": deque(maxlen=1000),
            "latency_history": deque(maxlen=1000),
            "throughput_history": deque(maxlen=60),
            "errors": 0,
            "warnings": 0,
            "alert_triggers": 0,
            "last_health_check": 0
        }
        
        self.fault_configs = []
        
        self._init_database()
        
        logger.info(f"初始化影子系统 V2.0: {self.system_id}")

    def _init_database(self):
        """初始化数据库"""
        if not self.config["database_logging_enabled"]:
            return
        
        try:
            self.db_conn = sqlite3.connect('shadow_system.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    input_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    match BOOLEAN NOT NULL,
                    differences TEXT,
                    main_result TEXT,
                    shadow_result TEXT,
                    processing_time REAL,
                    trace_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS input_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    input_id TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    trace_id TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    total_processed INTEGER,
                    total_matched INTEGER,
                    total_mismatched INTEGER,
                    average_latency REAL,
                    throughput REAL,
                    queue_size INTEGER,
                    thread_count INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    severity TEXT,
                    timestamp REAL NOT NULL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparison_timestamp ON comparison_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_input_records_timestamp ON input_records(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp)')
            
            self.db_conn.commit()
            logger.info("影子系统数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            self.config["database_logging_enabled"] = False

    def _log_to_database(self, table: str, **kwargs):
        """记录数据到数据库"""
        if not self.config["database_logging_enabled"]:
            return
        
        try:
            conn = sqlite3.connect('shadow_system.db', check_same_thread=False, timeout=5)
            cursor = conn.cursor()
            placeholders = ", ".join([f":{k}" for k in kwargs.keys()])
            columns = ", ".join(kwargs.keys())
            cursor.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', kwargs)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"数据库日志记录失败: {str(e)}")

    def start(self):
        """启动影子系统"""
        if self.is_running:
            logger.warning(f"影子系统 {self.system_id} 已在运行")
            return

        self.status = ShadowSystemStatus.RUNNING
        self.is_running = True

        self._start_processing_threads()

        if self.config["performance_monitoring_enabled"]:
            self.performance_thread = threading.Thread(target=self._performance_monitoring_loop)
            self.performance_thread.daemon = True
            self.performance_thread.start()

        if self.config["anomaly_detection_enabled"]:
            self.anomaly_thread = threading.Thread(target=self._anomaly_detection_loop)
            self.anomaly_thread.daemon = True
            self.anomaly_thread.start()

        if self.config["health_check_interval"] > 0:
            self.health_thread = threading.Thread(target=self._health_check_loop)
            self.health_thread.daemon = True
            self.health_thread.start()

        logger.info(f"影子系统 V2.0 已启动: {self.system_id}")
        self._log_event("system_start", "影子系统启动", severity="INFO")

    def _start_processing_threads(self):
        """启动处理线程"""
        with self.lock:
            self.processing_threads = []
            for i in range(self.current_thread_count):
                thread = threading.Thread(
                    target=self._processing_loop, 
                    name=f"shadow_processing_{i}"
                )
                thread.daemon = True
                thread.start()
                self.processing_threads.append(thread)

    def stop(self):
        """停止影子系统"""
        if not self.is_running:
            logger.warning(f"影子系统 {self.system_id} 未在运行")
            return

        self.status = ShadowSystemStatus.SHUTTING_DOWN
        self.is_running = False

        for thread in self.processing_threads:
            thread.join(timeout=10)

        if self.config["database_logging_enabled"]:
            self.db_conn.close()

        self.status = ShadowSystemStatus.SHUTDOWN
        logger.info(f"影子系统 V2.0 已停止: {self.system_id}")
        self._log_event("system_stop", "影子系统停止", severity="INFO")

    def pause(self):
        """暂停影子系统"""
        if self.status == ShadowSystemStatus.RUNNING:
            self.status = ShadowSystemStatus.PAUSED
            logger.info(f"影子系统已暂停: {self.system_id}")
            self._log_event("system_pause", "影子系统暂停", severity="INFO")

    def resume(self):
        """恢复影子系统"""
        if self.status == ShadowSystemStatus.PAUSED:
            self.status = ShadowSystemStatus.RUNNING
            logger.info(f"影子系统已恢复: {self.system_id}")
            self._log_event("system_resume", "影子系统恢复", severity="INFO")

    def set_mode(self, mode):
        """设置影子系统模式"""
        try:
            if isinstance(mode, str):
                mode = ShadowMode(mode)
        except ValueError:
            logger.error(f"无效的模式: {mode}")
            return

        old_mode = self.mode
        self.mode = mode
        logger.info(f"影子系统模式已切换: {old_mode.value} -> {mode.value}")
        self._log_event("mode_switch", f"模式切换: {old_mode.value} -> {mode.value}", severity="INFO")

    def configure(self, **kwargs):
        """配置影子系统"""
        with self.lock:
            old_config = self.config.copy()
            self.config.update(kwargs)
            changed = {k: v for k, v in kwargs.items() if old_config.get(k) != v}
            if changed:
                logger.info(f"影子系统已配置: {changed}")
                self._log_event("config_update", f"配置更新: {changed}", severity="INFO")

    def add_fault_config(self, fault_config: FaultConfig):
        """添加故障配置"""
        self.fault_configs.append(fault_config)
        logger.info(f"添加故障配置: {fault_config.fault_type.value}")
        self._log_event("fault_config_add", f"添加故障配置: {fault_config.fault_type.value}", severity="INFO")

    def remove_fault_configs(self):
        """清除所有故障配置"""
        self.fault_configs.clear()
        logger.info("已清除所有故障配置")
        self._log_event("fault_config_clear", "清除所有故障配置", severity="INFO")

    def _inject_fault(self):
        """根据配置注入故障"""
        if not self.config["fault_injection_enabled"] or not self.fault_configs:
            return None

        import random
        for config in self.fault_configs:
            if random.random() < config.probability:
                if config.fault_type == FaultType.DELAY:
                    time.sleep(config.delay_ms / 1000)
                    return {"type": "delay", "ms": config.delay_ms}
                elif config.fault_type == FaultType.ERROR:
                    raise Exception(config.error_message)
                elif config.fault_type == FaultType.RANDOM_FAILURE:
                    if random.random() < 0.5:
                        raise Exception("Random failure injected")
        return None

    def inject_input(self, input_data: Dict, input_id: str = None, trace_id: str = None, tags: List[str] = None):
        """注入输入到影子系统"""
        if not self.is_running:
            return

        input_id = input_id or f"input_{uuid.uuid4().hex[:8]}"
        trace_id = trace_id or self._generate_trace_id()

        if self.config["recording_enabled"]:
            record = InputRecord(
                input_id=input_id,
                input_data=input_data,
                timestamp=time.time(),
                trace_id=trace_id,
                tags=tags or []
            )
            with self.lock:
                self.input_records.append(record)
                self._log_to_database(
                    "input_records",
                    system_id=self.system_id,
                    input_id=input_id,
                    input_data=json.dumps(input_data, ensure_ascii=False),
                    timestamp=record.timestamp,
                    trace_id=trace_id,
                    tags=json.dumps(tags or [])
                )

        try:
            self.input_queue.put((input_id, input_data, trace_id), block=False)
        except queue.Full:
            logger.warning("输入队列已满，丢弃输入")
            self._log_event("queue_full", "输入队列已满", severity="WARNING")

        logger.debug(f"输入已注入影子系统: {input_id}, trace_id: {trace_id}")

    def _generate_trace_id(self) -> str:
        """生成唯一追踪ID"""
        with self.lock:
            self.trace_id_counter += 1
            return f"trace_{self.system_id}_{self.trace_id_counter}_{int(time.time() * 1000)}"

    def _processing_loop(self):
        """处理循环"""
        thread_name = threading.current_thread().name
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(0.05)
                continue

            try:
                input_id, input_data, trace_id = None, None, None
                try:
                    input_id, input_data, trace_id = self.input_queue.get(timeout=0.1)
                except queue.Empty:
                    time.sleep(0.05)
                    continue

                start_time = time.time()
                
                fault_result = self._inject_fault()
                
                self._process_input(input_id, input_data, trace_id)
                
                processing_time = time.time() - start_time
                
                with self.stats_lock:
                    self.performance_metrics["processing_time_history"].append(processing_time)
                    
                self.input_queue.task_done()
                
            except Exception as e:
                logger.error(f"处理输入时发生错误 [{thread_name}]: {str(e)}")
                with self.stats_lock:
                    self.performance_metrics["errors"] += 1

    def _performance_monitoring_loop(self):
        """性能监控循环"""
        last_processed = 0
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(1)
                continue

            try:
                with self.stats_lock:
                    queue_size = self.input_queue.qsize()
                    self.performance_metrics["queue_size_history"].append(queue_size)

                    if self.performance_metrics["processing_time_history"]:
                        avg_time = sum(self.performance_metrics["processing_time_history"]) / len(self.performance_metrics["processing_time_history"])
                        self.performance_metrics["average_processing_time"] = avg_time

                    current_processed = self.performance_metrics["total_processed"]
                    throughput = current_processed - last_processed
                    self.performance_metrics["throughput_history"].append(throughput)
                    last_processed = current_processed

                if self.config["auto_scaling_enabled"]:
                    self._auto_scale()

                if self.config["smart_mode_switching"]:
                    self._smart_mode_switch()

                self._log_performance_metrics()

                time.sleep(5)
            except Exception as e:
                logger.error(f"性能监控时发生错误: {str(e)}")
                time.sleep(5)

    def _auto_scale(self):
        """自动扩缩容处理线程"""
        if time.time() - self.last_scaling_time < 30:
            return

        with self.stats_lock:
            queue_size = self.input_queue.qsize()
            current_threads = self.current_thread_count

        if queue_size > self.config["scaling_threshold_high"] and current_threads < self.max_threads:
            new_thread_count = min(current_threads + 2, self.max_threads)
            self._adjust_thread_count(new_thread_count)
            logger.info(f"影子系统自动扩容: {current_threads} -> {new_thread_count}, 队列大小: {queue_size}")
            self._log_event("auto_scale_up", f"线程扩容: {current_threads} -> {new_thread_count}", severity="INFO")

        if queue_size < self.config["scaling_threshold_low"] and current_threads > self.min_threads:
            new_thread_count = max(current_threads - 1, self.min_threads)
            self._adjust_thread_count(new_thread_count)
            logger.info(f"影子系统自动缩容: {current_threads} -> {new_thread_count}, 队列大小: {queue_size}")
            self._log_event("auto_scale_down", f"线程缩容: {current_threads} -> {new_thread_count}", severity="INFO")

    def _adjust_thread_count(self, new_thread_count: int):
        """调整处理线程数量"""
        with self.lock:
            self.current_thread_count = new_thread_count
            
            for thread in self.processing_threads:
                thread.join(timeout=1)
            
            self.processing_threads = []
            for i in range(self.current_thread_count):
                thread = threading.Thread(
                    target=self._processing_loop,
                    name=f"shadow_processing_{i}"
                )
                thread.daemon = True
                thread.start()
                self.processing_threads.append(thread)

        self.last_scaling_time = time.time()

    def _smart_mode_switch(self):
        """智能模式切换"""
        if time.time() - self.last_mode_switch_time < 60:
            return

        with self.stats_lock:
            mismatched = self.performance_metrics["total_mismatched"]
            total = self.performance_metrics["total_processed"]

        if total == 0:
            return

        mismatch_rate = mismatched / total

        if mismatch_rate > self.config["mode_switch_threshold"] and self.mode != ShadowMode.MONITOR:
            self.set_mode(ShadowMode.MONITOR)
            self._log_event("smart_mode_switch", f"切换到监控模式, 不匹配率: {mismatch_rate:.2%}", severity="WARNING")
            self.last_mode_switch_time = time.time()

        elif mismatch_rate <= self.config["mode_switch_threshold"] and self.mode == ShadowMode.MONITOR:
            self.set_mode(ShadowMode.PARALLEL)
            self._log_event("smart_mode_switch", f"切换到并行模式, 不匹配率: {mismatch_rate:.2%}", severity="INFO")
            self.last_mode_switch_time = time.time()

    def _anomaly_detection_loop(self):
        """异常检测循环"""
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(5)
                continue

            try:
                metrics = self.get_performance_metrics()
                
                if metrics["mismatch_rate"] > self.config["alert_threshold_mismatch_rate"]:
                    self._trigger_alert("high_mismatch_rate", 
                        f"不匹配率超过阈值: {metrics['mismatch_rate']:.2%}", "WARNING")

                avg_latency_ms = metrics["average_processing_time"] * 1000
                if avg_latency_ms > self.config["alert_threshold_latency_ms"]:
                    self._trigger_alert("high_latency",
                        f"平均延迟超过阈值: {avg_latency_ms:.2f}ms", "WARNING")

                time.sleep(10)
            except Exception as e:
                logger.error(f"异常检测时发生错误: {str(e)}")
                time.sleep(10)

    def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(self.config["health_check_interval"])
                continue

            try:
                health_status = self._perform_health_check()
                self.performance_metrics["last_health_check"] = time.time()
                
                if health_status["status"] != "healthy":
                    self._log_event("health_degraded", 
                        f"健康状态降级: {health_status}", severity="WARNING")
                    self.status = ShadowSystemStatus.DEGRADED
                else:
                    if self.status == ShadowSystemStatus.DEGRADED:
                        self.status = ShadowSystemStatus.RUNNING
                        self._log_event("health_recovered", "健康状态恢复", severity="INFO")

                time.sleep(self.config["health_check_interval"])
            except Exception as e:
                logger.error(f"健康检查时发生错误: {str(e)}")
                time.sleep(self.config["health_check_interval"])

    def _perform_health_check(self) -> Dict:
        """执行健康检查"""
        with self.stats_lock:
            queue_size = self.input_queue.qsize()
            thread_alive = sum(1 for t in self.processing_threads if t.is_alive())
            total_processed = self.performance_metrics["total_processed"]

        status = "healthy"
        issues = []

        if queue_size > self.config["max_queue_size"] * 0.8:
            issues.append(f"队列接近上限: {queue_size}/{self.config['max_queue_size']}")
            
        if thread_alive < self.current_thread_count:
            issues.append(f"部分线程未运行: {thread_alive}/{self.current_thread_count}")
            
        if issues:
            status = "degraded"

        return {
            "status": status,
            "timestamp": time.time(),
            "queue_size": queue_size,
            "threads_alive": thread_alive,
            "total_threads": self.current_thread_count,
            "total_processed": total_processed,
            "issues": issues
        }

    def _trigger_alert(self, alert_type: str, message: str, severity: str = "WARNING"):
        """触发告警"""
        with self.stats_lock:
            self.performance_metrics["alert_triggers"] += 1
        
        logger.warning(f"【告警】{alert_type}: {message}")
        self._log_event("alert", f"{alert_type}: {message}", severity=severity)

    def _log_event(self, event_type: str, message: str, severity: str = "INFO"):
        """记录系统事件"""
        try:
            self._log_to_database(
                "system_events",
                system_id=self.system_id,
                event_type=event_type,
                message=message,
                details="{}",
                severity=severity,
                timestamp=time.time()
            )
        except:
            pass

    def _log_performance_metrics(self):
        """记录性能指标到数据库"""
        if not self.config["database_logging_enabled"]:
            return
        
        with self.stats_lock:
            metrics = {
                "system_id": self.system_id,
                "timestamp": time.time(),
                "total_processed": self.performance_metrics["total_processed"],
                "total_matched": self.performance_metrics["total_matched"],
                "total_mismatched": self.performance_metrics["total_mismatched"],
                "average_latency": self.performance_metrics["average_processing_time"],
                "throughput": sum(self.performance_metrics["throughput_history"]) / len(self.performance_metrics["throughput_history"]) if self.performance_metrics["throughput_history"] else 0,
                "queue_size": self.input_queue.qsize(),
                "thread_count": self.current_thread_count
            }
        
        self._log_to_database("performance_metrics", **metrics)

    def _process_input(self, input_id: str, input_data: Dict, trace_id: str):
        """处理单个输入"""
        logger.debug(f"处理输入: {input_id}, trace_id: {trace_id}")

        if self.mode == ShadowMode.MONITOR:
            logger.debug(f"监控模式: 跳过输入处理: {input_id}")
            return

        elif self.mode == ShadowMode.PARALLEL:
            self._process_parallel(input_id, input_data, trace_id)

        elif self.mode == ShadowMode.RECORD:
            logger.debug(f"记录模式: 已记录输入: {input_id}")

        elif self.mode == ShadowMode.REPLAY:
            logger.debug(f"回放模式: 跳过新输入: {input_id}")

        elif self.mode == ShadowMode.STRESS_TEST:
            self._process_stress_test(input_id, input_data)

        elif self.mode == ShadowMode.PERFORMANCE_TEST:
            self._process_performance_test(input_id, input_data)

    def _process_parallel(self, input_id: str, input_data: Dict, trace_id: str):
        """并行处理输入并比较结果"""
        try:
            main_result = None
            if self.main_system:
                main_start = time.time()
                main_result = self._call_main_system(input_data)
                main_latency = time.time() - main_start
            else:
                main_latency = 0

            shadow_start = time.time()
            shadow_result = self._call_shadow_system(input_data)
            shadow_latency = time.time() - shadow_start

            processing_time = abs(main_latency - shadow_latency)

            if self.config["comparison_enabled"]:
                comparison = self._compare_results(input_id, input_data, main_result, shadow_result, trace_id)
                comparison.processing_time = processing_time

                with self.stats_lock:
                    self.comparison_results.append(comparison)
                    self.performance_metrics["total_processed"] += 1
                    if comparison.match:
                        self.performance_metrics["total_matched"] += 1
                    else:
                        self.performance_metrics["total_mismatched"] += 1

                self._log_to_database(
                    "comparison_results",
                    system_id=self.system_id,
                    input_id=input_id,
                    timestamp=time.time(),
                    match=comparison.match,
                    differences=json.dumps(comparison.differences),
                    main_result=json.dumps(main_result) if main_result else "null",
                    shadow_result=json.dumps(shadow_result),
                    processing_time=processing_time,
                    trace_id=trace_id
                )

        except Exception as e:
            logger.error(f"并行处理时发生错误: {str(e)}")
            with self.stats_lock:
                self.performance_metrics["errors"] += 1

    def _process_stress_test(self, input_id: str, input_data: Dict):
        """压力测试处理"""
        import concurrent.futures
        
        def stress_worker(i):
            try:
                start = time.time()
                self._call_shadow_system(input_data)
                return {"worker": i, "latency": time.time() - start, "success": True}
            except:
                return {"worker": i, "latency": 0, "success": False}

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["stress_test_concurrent"]) as executor:
            futures = [executor.submit(stress_worker, i) for i in range(self.config["stress_test_concurrent"])]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        success_count = sum(1 for r in results if r["success"])
        avg_latency = sum(r["latency"] for r in results) / len(results) if results else 0

        logger.info(f"压力测试完成: {success_count}/{len(results)} 成功, 平均延迟: {avg_latency*1000:.2f}ms")

    def _process_performance_test(self, input_id: str, input_data: Dict):
        """性能测试处理"""
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < self.config["performance_test_duration"]:
            self._call_shadow_system(input_data)
            count += 1
        
        duration = time.time() - start_time
        throughput = count / duration
        
        logger.info(f"性能测试完成: {count} 请求, 耗时 {duration:.2f}s, 吞吐量 {throughput:.2f} req/s")

    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        with self.stats_lock:
            total = self.performance_metrics["total_processed"]
            mismatch_rate = self.performance_metrics["total_mismatched"] / total if total > 0 else 0
            
            return {
                "total_processed": total,
                "total_matched": self.performance_metrics["total_matched"],
                "total_mismatched": self.performance_metrics["total_mismatched"],
                "mismatch_rate": mismatch_rate,
                "average_processing_time": self.performance_metrics["average_processing_time"],
                "average_latency": self.performance_metrics["average_latency"],
                "current_queue_size": self.input_queue.qsize(),
                "thread_count": self.current_thread_count,
                "max_threads": self.max_threads,
                "min_threads": self.min_threads,
                "errors": self.performance_metrics["errors"],
                "warnings": self.performance_metrics["warnings"],
                "alert_triggers": self.performance_metrics["alert_triggers"],
                "last_health_check": self.performance_metrics["last_health_check"],
                "throughput": sum(self.performance_metrics["throughput_history"]) / len(self.performance_metrics["throughput_history"]) if self.performance_metrics["throughput_history"] else 0
            }

    def _call_main_system(self, input_data: Dict) -> Dict:
        """调用主系统处理输入"""
        logger.debug("调用主系统处理输入")

        if hasattr(self.main_system, "process"):
            return self.main_system.process(input_data)
        elif hasattr(self.main_system, "handle"):
            return self.main_system.handle(input_data)

        time.sleep(0.01)
        return {
            "status": "success",
            "result": f"main_result_{time.time()}",
            "timestamp": time.time()
        }

    def _call_shadow_system(self, input_data: Dict) -> Dict:
        """调用影子系统处理输入"""
        logger.debug("调用影子系统处理输入")

        time.sleep(0.005)
        result_type = input_data.get('type', 'default')
        if result_type == 'error':
            return {
                "status": "error",
                "result": f"result_{result_type}",
                "timestamp": time.time()
            }
        return {
            "status": "success",
            "result": f"result_{result_type}",
            "timestamp": time.time()
        }

    def _compare_results(self, input_id: str, input_data: Dict, 
                        main_result: Dict, shadow_result: Dict, trace_id: str) -> ComparisonResult:
        """比较结果"""
        logger.debug(f"比较结果: {input_id}")

        match = False
        differences = []

        if main_result and shadow_result:
            match = True
            
            if main_result.get("status") != shadow_result.get("status"):
                differences.append({
                    "field": "status",
                    "main_value": main_result.get("status"),
                    "shadow_value": shadow_result.get("status")
                })
                match = False

            if main_result.get("result") != shadow_result.get("result"):
                differences.append({
                    "field": "result",
                    "main_value": main_result.get("result"),
                    "shadow_value": shadow_result.get("result")
                })
                match = False

        comparison = ComparisonResult(
            input_id=input_id,
            timestamp=time.time(),
            match=match,
            differences=differences,
            main_result=main_result,
            shadow_result=shadow_result,
            processing_time=0,
            trace_id=trace_id
        )

        if not match:
            logger.warning(f"结果不匹配: {input_id}, trace_id: {trace_id}")
            with self.stats_lock:
                self.performance_metrics["warnings"] += 1
        else:
            logger.debug(f"结果匹配: {input_id}")

        return comparison

    def start_replay(self, speed: float = 1.0):
        """开始回放记录的输入"""
        if not self.input_records:
            logger.warning("没有可回放的输入记录")
            return

        self.set_mode(ShadowMode.REPLAY)
        self.replay_index = 0

        logger.info("开始回放输入记录")
        self._log_event("replay_start", "开始回放", severity="INFO")

        self.replay_thread = threading.Thread(target=self._replay_loop, args=(speed,))
        self.replay_thread.daemon = True
        self.replay_thread.start()

    def _replay_loop(self, speed: float):
        """回放循环"""
        while self.is_running and self.replay_index < len(self.input_records):
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(0.1)
                continue

            try:
                record = self.input_records[self.replay_index]
                self.replay_index += 1

                shadow_result = self._call_shadow_system(record.input_data)

                logger.debug(f"回放输入: {record.input_id}, 索引: {self.replay_index}/{len(self.input_records)}")
                time.sleep(0.1 / speed)
            except Exception as e:
                logger.error(f"回放时发生错误: {str(e)}")
                time.sleep(0.1)

        self.set_mode(ShadowMode.PARALLEL)
        logger.info("回放完成")
        self._log_event("replay_complete", "回放完成", severity="INFO")

    def get_status(self) -> Dict:
        """获取影子系统状态"""
        metrics = self.get_performance_metrics()
        
        return {
            "system_id": self.system_id,
            "status": self.status.value,
            "mode": self.mode.value,
            "queue_size": self.input_queue.qsize(),
            "comparison_results_count": len(self.comparison_results),
            "input_records_count": len(self.input_records),
            "replay_index": self.replay_index,
            "thread_count": self.current_thread_count,
            "max_threads": self.max_threads,
            "min_threads": self.min_threads,
            "fault_injection_enabled": self.config["fault_injection_enabled"],
            "fault_config_count": len(self.fault_configs),
            "performance_metrics": metrics,
            "config_summary": {
                "comparison_enabled": self.config["comparison_enabled"],
                "recording_enabled": self.config["recording_enabled"],
                "auto_scaling_enabled": self.config["auto_scaling_enabled"],
                "anomaly_detection_enabled": self.config["anomaly_detection_enabled"],
                "database_logging_enabled": self.config["database_logging_enabled"]
            }
        }

    def get_comparison_results(self, limit: int = 100) -> List[Dict]:
        """获取比较结果"""
        results = list(self.comparison_results)[-limit:]
        return [self._result_to_dict(r) for r in results]

    def _result_to_dict(self, result: ComparisonResult) -> Dict:
        """将比较结果转换为字典"""
        return {
            "input_id": result.input_id,
            "timestamp": result.timestamp,
            "match": result.match,
            "differences": result.differences,
            "main_result": result.main_result,
            "shadow_result": result.shadow_result,
            "processing_time": result.processing_time,
            "trace_id": result.trace_id
        }

    def get_input_records(self, limit: int = 100) -> List[Dict]:
        """获取输入记录"""
        records = list(self.input_records)[-limit:]
        return [{
            "input_id": r.input_id,
            "input_data": r.input_data,
            "timestamp": r.timestamp,
            "trace_id": r.trace_id,
            "tags": r.tags
        } for r in records]

    def generate_report(self, detailed: bool = False) -> Dict:
        """生成报告"""
        comparison_list = list(self.comparison_results)
        
        if not comparison_list:
            return {"message": "没有比较结果"}

        total = len(comparison_list)
        matches = sum(1 for r in comparison_list if r.match)
        mismatches = total - matches

        difference_types = defaultdict(int)
        for result in comparison_list:
            for diff in result.differences:
                difference_types[diff["field"]] += 1

        avg_processing_time = sum(r.processing_time for r in comparison_list) / len(comparison_list) if comparison_list else 0

        report = {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "system_id": self.system_id,
            "generated_at": time.time(),
            "statistics": {
                "total_comparisons": total,
                "matches": matches,
                "mismatches": mismatches,
                "match_rate": matches / total if total > 0 else 0,
                "average_processing_time": avg_processing_time,
                "total_processed": self.performance_metrics["total_processed"],
                "errors": self.performance_metrics["errors"],
                "warnings": self.performance_metrics["warnings"],
                "alert_triggers": self.performance_metrics["alert_triggers"]
            },
            "difference_types": dict(difference_types),
            "config_summary": {
                "mode": self.mode.value,
                "thread_count": self.current_thread_count,
                "auto_scaling": self.config["auto_scaling_enabled"],
                "anomaly_detection": self.config["anomaly_detection_enabled"]
            }
        }

        if detailed:
            report["recent_results"] = self.get_comparison_results(100)
            report["performance_trends"] = {
                "throughput_history": list(self.performance_metrics["throughput_history"]),
                "latency_history": [t * 1000 for t in list(self.performance_metrics["processing_time_history"])]
            }

        report_file = f"shadow_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"比较报告已生成: {report_file}")
        return report

    def export_data(self, output_dir: str = "shadow_export") -> Dict:
        """导出数据"""
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            "system_id": self.system_id,
            "export_time": time.time(),
            "comparison_results": self.get_comparison_results(),
            "input_records": self.get_input_records(),
            "performance_metrics": self.get_performance_metrics(),
            "status": self.get_status()
        }
        
        export_file = os.path.join(output_dir, f"shadow_export_{time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据导出完成: {export_file}")
        return {"export_file": export_file, "record_count": len(data["comparison_results"])}

    def clear_data(self):
        """清除所有数据"""
        with self.lock:
            self.comparison_results.clear()
            self.input_records.clear()
            
        with self.stats_lock:
            self.performance_metrics = {
                "total_processed": 0,
                "total_matched": 0,
                "total_mismatched": 0,
                "average_processing_time": 0,
                "average_latency": 0,
                "queue_size_history": deque(maxlen=1000),
                "processing_time_history": deque(maxlen=1000),
                "latency_history": deque(maxlen=1000),
                "throughput_history": deque(maxlen=60),
                "errors": 0,
                "warnings": 0,
                "alert_triggers": 0,
                "last_health_check": 0
            }
        
        logger.info("影子系统数据已清除")
        self._log_event("data_clear", "清除所有数据", severity="INFO")


class TestMainSystem:
    """测试用的主系统"""

    def __init__(self):
        self.name = "TestMainSystem"

    def process(self, input_data: Dict) -> Dict:
        """处理输入"""
        time.sleep(0.005)
        result_type = input_data.get('type', 'default')
        if result_type == 'error':
            return {
                "status": "error",
                "result": f"result_{result_type}",
                "timestamp": time.time()
            }
        return {
            "status": "success",
            "result": f"result_{result_type}",
            "timestamp": time.time()
        }


def test_shadow_system():
    """测试影子系统 V2.0"""
    print("影子系统 V2.0 测试")
    print("=" * 60)

    main_system = TestMainSystem()

    shadow_system = ShadowSystem("test_shadow_system_v2", main_system)

    shadow_system.configure(
        comparison_enabled=True,
        recording_enabled=True,
        auto_scaling_enabled=True,
        anomaly_detection_enabled=True
    )

    print("启动影子系统...")
    shadow_system.start()

    print("\n注入测试输入...")
    test_inputs = [
        {"type": "normal", "data": "test_data_1"},
        {"type": "normal", "data": "test_data_2"},
        {"type": "error", "data": "test_data_3"},
        {"type": "normal", "data": "test_data_4"},
        {"type": "normal", "data": "test_data_5"}
    ]

    for i, input_data in enumerate(test_inputs):
        shadow_system.inject_input(input_data, f"test_input_{i+1}")

    print("\n等待处理完成 (3秒)...")
    time.sleep(3)

    status = shadow_system.get_status()
    print("\n影子系统状态:")
    print(f"  系统ID: {status['system_id']}")
    print(f"  状态: {status['status']}")
    print(f"  模式: {status['mode']}")
    print(f"  队列大小: {status['queue_size']}")
    print(f"  线程数: {status['thread_count']}/{status['max_threads']}")
    print(f"  比较结果数: {status['comparison_results_count']}")
    print(f"  输入记录数: {status['input_records_count']}")

    metrics = status['performance_metrics']
    print("\n性能指标:")
    print(f"  总处理数: {metrics['total_processed']}")
    print(f"  匹配数: {metrics['total_matched']}")
    print(f"  不匹配数: {metrics['total_mismatched']}")
    print(f"  不匹配率: {metrics['mismatch_rate']:.2%}")
    print(f"  平均处理时间: {metrics['average_processing_time']:.6f}s")
    print(f"  吞吐量: {metrics['throughput']:.2f} req/s")

    print("\n测试故障注入功能...")
    shadow_system.configure(fault_injection_enabled=True)
    fault_config = FaultConfig(
        fault_type=FaultType.DELAY,
        probability=0.5,
        delay_ms=100
    )
    shadow_system.add_fault_config(fault_config)
    
    for i in range(3):
        shadow_system.inject_input({"type": "fault_test", "data": f"fault_data_{i}"})
    
    time.sleep(1)
    shadow_system.configure(fault_injection_enabled=False)

    print("\n测试回放功能...")
    shadow_system.start_replay(speed=2.0)
    time.sleep(2)

    print("\n生成详细报告...")
    report = shadow_system.generate_report(detailed=True)
    print(f"\n报告摘要:")
    print(f"  报告ID: {report['report_id']}")
    print(f"  总比较次数: {report['statistics']['total_comparisons']}")
    print(f"  匹配率: {report['statistics']['match_rate']:.2%}")
    print(f"  错误数: {report['statistics']['errors']}")

    print("\n测试数据导出...")
    export_result = shadow_system.export_data()
    print(f"  导出文件: {export_result['export_file']}")
    print(f"  记录数: {export_result['record_count']}")

    print("\n停止影子系统...")
    shadow_system.stop()

    print("\n影子系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_shadow_system()