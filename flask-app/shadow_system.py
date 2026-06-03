# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影子系统(Shadow System)
用于在不影响主系统的情况下进行测试和监控
"""

import time
import uuid
import logging
import threading
import json
from enum import Enum
from collections import defaultdict, deque
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shadow_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ShadowSystem')

class ShadowSystemStatus(Enum):
    """影子系统状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

class ShadowMode(Enum):
    """影子系统模式枚举"""
    MONITOR = "monitor"
    PARALLEL = "parallel"
    RECORD = "record"
    REPLAY = "replay"

class ShadowSystem:
    """影子系统"""

    def __init__(self, system_id, main_system=None):
        """初始化影子系统"""
        self.system_id = system_id or f"shadow_{uuid.uuid4().hex[:8]}"
        self.main_system = main_system
        self.status = ShadowSystemStatus.INITIALIZING
        self.mode = ShadowMode.PARALLEL
        self.is_running = False
        self.input_queue = deque()
        self.processing_threads = []
        self.max_threads = 4
        self.min_threads = 1
        self.current_thread_count = 1
        self.comparison_results = []
        self.input_records = []
        self.replay_index = 0
        self.last_scaling_time = 0
        self.config = {
            "comparison_enabled": True,
            "recording_enabled": True,
            "max_queue_size": 1000,
            "max_results_size": 1000,
            "max_records_size": 10000,
            "auto_scaling_enabled": True,
            "scaling_threshold_high": 50,
            "scaling_threshold_low": 10,
            "performance_monitoring_enabled": True,
            "smart_mode_switching": True,
            "mode_switch_threshold": 0.1
        }
        self.lock = threading.Lock()
        self.performance_metrics = {
            "total_processed": 0,
            "total_matched": 0,
            "total_mismatched": 0,
            "average_processing_time": 0,
            "queue_size_history": deque(maxlen=100),
            "processing_time_history": deque(maxlen=100)
        }
        self.last_mode_switch_time = time.time()

        logger.info(f"初始化影子系统: {self.system_id}")

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

        logger.info(f"影子系统已启动: {self.system_id}")

    def _start_processing_threads(self):
        """启动处理线程"""
        with self.lock:
            self.processing_threads = []
            for i in range(self.current_thread_count):
                thread = threading.Thread(target=self._processing_loop, name=f"processing_thread_{i}")
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
            thread.join(timeout=5)

        self.status = ShadowSystemStatus.SHUTDOWN
        logger.info(f"影子系统已停止: {self.system_id}")

    def pause(self):
        """暂停影子系统"""
        if self.status == ShadowSystemStatus.RUNNING:
            self.status = ShadowSystemStatus.PAUSED
            logger.info(f"影子系统已暂停: {self.system_id}")

    def resume(self):
        """恢复影子系统"""
        if self.status == ShadowSystemStatus.PAUSED:
            self.status = ShadowSystemStatus.RUNNING
            logger.info(f"影子系统已恢复: {self.system_id}")

    def set_mode(self, mode):
        """设置影子系统模式"""
        try:
            if isinstance(mode, str):
                mode = ShadowMode(mode)
        except ValueError:
            logger.error(f"无效的模式: {mode}")
            return

        self.mode = mode
        logger.info(f"影子系统模式已设置为: {mode.value}")

    def configure(self, **kwargs):
        """配置影子系统"""
        with self.lock:
            self.config.update(kwargs)
            logger.info(f"影子系统已配置: {kwargs}")

    def inject_input(self, input_data, input_id=None):
        """注入输入到影子系统"""
        if not self.is_running:
            return

        input_id = input_id or f"input_{uuid.uuid4().hex[:8]}"

        with self.lock:
            if self.config["recording_enabled"]:
                record = {
                    "input_id": input_id,
                    "input_data": input_data,
                    "timestamp": time.time()
                }
                self.input_records.append(record)

                if len(self.input_records) > self.config["max_records_size"]:
                    self.input_records.pop(0)

            self.input_queue.append((input_id, input_data))

            if len(self.input_queue) > self.config["max_queue_size"]:
                self.input_queue.popleft()

        logger.debug(f"输入已注入影子系统: {input_id}")

    def _processing_loop(self):
        """处理循环"""
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(0.1)
                continue

            try:
                input_id, input_data = None, None
                with self.lock:
                    if self.input_queue:
                        input_id, input_data = self.input_queue.popleft()

                if input_id and input_data:
                    start_time = time.time()
                    self._process_input(input_id, input_data)
                    processing_time = time.time() - start_time
                    with self.lock:
                        self.performance_metrics["processing_time_history"].append(processing_time)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"处理输入时发生错误: {str(e)}")
                time.sleep(0.1)

    def _performance_monitoring_loop(self):
        """性能监控循环"""
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(1)
                continue

            try:
                with self.lock:
                    queue_size = len(self.input_queue)
                    self.performance_metrics["queue_size_history"].append(queue_size)

                    if self.performance_metrics["processing_time_history"]:
                        avg_time = sum(self.performance_metrics["processing_time_history"]) / len(self.performance_metrics["processing_time_history"])
                        self.performance_metrics["average_processing_time"] = avg_time

                if self.config["auto_scaling_enabled"]:
                    self._auto_scale()

                if self.config["smart_mode_switching"]:
                    self._smart_mode_switch()

                time.sleep(5)
            except Exception as e:
                logger.error(f"性能监控时发生错误: {str(e)}")
                time.sleep(5)

    def _auto_scale(self):
        """自动扩缩容处理线程"""
        if time.time() - self.last_scaling_time < 30:
            return

        with self.lock:
            queue_size = len(self.input_queue)
            current_threads = self.current_thread_count

        if queue_size > self.config["scaling_threshold_high"] and current_threads < self.max_threads:
            new_thread_count = min(current_threads + 1, self.max_threads)
            self._adjust_thread_count(new_thread_count)
            logger.info(f"影子系统自动扩容: {current_threads} -> {new_thread_count}, 队列大小: {queue_size}")

        if queue_size < self.config["scaling_threshold_low"] and current_threads > self.min_threads:
            new_thread_count = max(current_threads - 1, self.min_threads)
            self._adjust_thread_count(new_thread_count)
            logger.info(f"影子系统自动缩容: {current_threads} -> {new_thread_count}, 队列大小: {queue_size}")

    def _adjust_thread_count(self, new_thread_count):
        """调整处理线程数量"""
        with self.lock:
            self.current_thread_count = new_thread_count

        self.last_scaling_time = time.time()

    def _smart_mode_switch(self):
        """智能模式切换"""
        if time.time() - self.last_mode_switch_time < 60:
            return

        with self.lock:
            mismatched = self.performance_metrics["total_mismatched"]
            total = self.performance_metrics["total_processed"]

        if total == 0:
            return

        mismatch_rate = mismatched / total

        if mismatch_rate > self.config["mode_switch_threshold"] and self.mode != ShadowMode.MONITOR:
            self.set_mode(ShadowMode.MONITOR)
            logger.info(f"智能模式切换: {self.mode.value} -> MONITOR, 不匹配率: {mismatch_rate:.2%}")
            self.last_mode_switch_time = time.time()

        elif mismatch_rate <= self.config["mode_switch_threshold"] and self.mode != ShadowMode.PARALLEL:
            self.set_mode(ShadowMode.PARALLEL)
            logger.info(f"智能模式切换: {self.mode.value} -> PARALLEL, 不匹配率: {mismatch_rate:.2%}")
            self.last_mode_switch_time = time.time()

    def _process_input(self, input_id, input_data):
        """处理单个输入"""
        logger.debug(f"处理输入: {input_id}")

        if self.mode == ShadowMode.MONITOR:
            logger.debug(f"监控模式: 跳过输入处理: {input_id}")
            return

        elif self.mode == ShadowMode.PARALLEL:
            self._process_parallel(input_id, input_data)

        elif self.mode == ShadowMode.RECORD:
            logger.debug(f"记录模式: 跳过处理: {input_id}")

        elif self.mode == ShadowMode.REPLAY:
            logger.debug(f"回放模式: 跳过新输入: {input_id}")

    def _process_parallel(self, input_id, input_data):
        """并行处理输入并比较结果"""
        try:
            main_result = None
            if self.main_system:
                main_result = self._call_main_system(input_data)

            shadow_result = self._call_shadow_system(input_data)

            if self.config["comparison_enabled"]:
                comparison = self._compare_results(input_id, input_data, main_result, shadow_result)

                with self.lock:
                    self.comparison_results.append(comparison)

                    if len(self.comparison_results) > self.config["max_results_size"]:
                        self.comparison_results.pop(0)

                    self.performance_metrics["total_processed"] += 1
                    if comparison["match"]:
                        self.performance_metrics["total_matched"] += 1
                    else:
                        self.performance_metrics["total_mismatched"] += 1
        except Exception as e:
            logger.error(f"并行处理时发生错误: {str(e)}")

    def get_performance_metrics(self):
        """获取性能指标"""
        with self.lock:
            return {
                "total_processed": self.performance_metrics["total_processed"],
                "total_matched": self.performance_metrics["total_matched"],
                "total_mismatched": self.performance_metrics["total_mismatched"],
                "mismatch_rate": self.performance_metrics["total_mismatched"] / self.performance_metrics["total_processed"] if self.performance_metrics["total_processed"] > 0 else 0,
                "average_processing_time": self.performance_metrics["average_processing_time"],
                "current_queue_size": len(self.input_queue),
                "thread_count": self.current_thread_count,
                "max_threads": self.max_threads,
                "min_threads": self.min_threads
            }

    def _call_main_system(self, input_data):
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

    def _call_shadow_system(self, input_data):
        """调用影子系统处理输入"""
        logger.debug("调用影子系统处理输入")

        time.sleep(0.01)
        return {
            "status": "success",
            "result": f"shadow_result_{time.time()}",
            "timestamp": time.time()
        }

    def _compare_results(self, input_id, input_data, main_result, shadow_result):
        """比较结果"""
        logger.debug(f"比较结果: {input_id}")

        match = False
        differences = []

        if main_result and shadow_result:
            if main_result.get("status") == shadow_result.get("status"):
                match = True
            else:
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

        comparison = {
            "input_id": input_id,
            "timestamp": time.time(),
            "match": match,
            "differences": differences,
            "main_result": main_result,
            "shadow_result": shadow_result,
            "processing_time": abs(
                main_result.get("timestamp", 0) - shadow_result.get("timestamp", 0)
            )
        }

        if not match:
            logger.warning(f"结果不匹配: {input_id}")
        else:
            logger.debug(f"结果匹配: {input_id}")

        return comparison

    def start_replay(self):
        """开始回放记录的输入"""
        if not self.input_records:
            logger.warning("没有可回放的输入记录")
            return

        self.set_mode(ShadowMode.REPLAY)
        self.replay_index = 0

        logger.info("开始回放输入记录")

        self.replay_thread = threading.Thread(target=self._replay_loop)
        self.replay_thread.daemon = True
        self.replay_thread.start()

    def _replay_loop(self):
        """回放循环"""
        while self.is_running and self.replay_index < len(self.input_records):
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(0.1)
                continue

            try:
                record = self.input_records[self.replay_index]
                self.replay_index += 1

                shadow_result = self._call_shadow_system(record["input_data"])

                logger.debug(f"回放输入: {record['input_id']}, 索引: {self.replay_index}/{len(self.input_records)}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"回放时发生错误: {str(e)}")
                time.sleep(0.1)

        self.set_mode(ShadowMode.PARALLEL)

    def get_status(self):
        """获取影子系统状态"""
        with self.lock:
            return {
                "system_id": self.system_id,
                "status": self.status.value,
                "mode": self.mode.value,
                "queue_size": len(self.input_queue),
                "comparison_results_count": len(self.comparison_results),
                "input_records_count": len(self.input_records),
                "replay_index": self.replay_index,
                "thread_count": self.current_thread_count,
                "max_threads": self.max_threads,
                "min_threads": self.min_threads,
                "performance_metrics": {
                    "total_processed": self.performance_metrics["total_processed"],
                    "total_matched": self.performance_metrics["total_matched"],
                    "mismatch_rate": self.performance_metrics["total_mismatched"] / self.performance_metrics["total_processed"] if self.performance_metrics["total_processed"] > 0 else 0,
                    "average_processing_time": self.performance_metrics["average_processing_time"]
                },
            }

    def get_comparison_results(self, limit=100):
        """获取比较结果"""
        with self.lock:
            return self.comparison_results[-limit:]

    def get_input_records(self, limit=100):
        """获取输入记录"""
        with self.lock:
            return self.input_records[-limit:]

    def generate_report(self):
        """生成报告"""
        with self.lock:
            if not self.comparison_results:
                return {"message": "没有比较结果"}

            total = len(self.comparison_results)
            matches = sum(1 for r in self.comparison_results if r["match"])
            mismatches = total - matches

            difference_types = defaultdict(int)
            for result in self.comparison_results:
                for diff in result.get("differences", []):
                    difference_types[diff["field"]] += 1

            avg_processing_time = sum(r.get("processing_time", 0) for r in self.comparison_results) / len(self.comparison_results)

            report = {
                "report_id": f"report_{uuid.uuid4().hex[:8]}",
                "system_id": self.system_id,
                "generated_at": time.time(),
                "statistics": {
                    "total_comparisons": total,
                    "matches": matches,
                    "mismatches": mismatches,
                    "match_rate": matches / total if total > 0 else 0,
                    "average_processing_time": avg_processing_time
                },
                "difference_types": dict(difference_types),
                "recent_results": self.comparison_results[-10:]
            }

            report_file = f"shadow_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"比较报告已生成: {report_file}")
            return report

class TestMainSystem:
    """测试用的主系统"""

    def __init__(self):
        self.name = "TestMainSystem"

    def process(self, input_data):
        """处理输入"""
        time.sleep(0.005)
        return {
            "status": "success",
            "result": f"main_{input_data.get('type', 'default')}_{time.time()}",
            "timestamp": time.time()
        }

class TestShadowSystem:
    """测试用的影子系统处理器"""

    def __init__(self):
        self.name = "TestShadowSystem"

    def process(self, input_data):
        """处理输入"""
        time.sleep(0.005)
        if input_data.get('type') == 'error':
            return {
                "status": "error",
                "result": f"shadow_error_{time.time()}",
                "timestamp": time.time()
            }
        return {
            "status": "success",
            "result": f"shadow_{input_data.get('type', 'default')}_{time.time()}",
            "timestamp": time.time()
        }

def test_shadow_system():
    """测试影子系统"""
    print("影子系统测试")
    print("=" * 60)

    main_system = TestMainSystem()

    shadow_system = ShadowSystem("test_shadow_system", main_system)

    shadow_system.configure(
        comparison_enabled=True,
        recording_enabled=True,
        max_queue_size=100
    )

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

    print("\n等待处理完成 (2秒)...")
    time.sleep(2)

    status = shadow_system.get_status()
    print("\n影子系统状态:")
    for key, value in status.items():
        if key != "config":
            print(f"  {key}: {value}")

    print("\n生成比较报告...")
    report = shadow_system.generate_report()

    print("\n比较报告摘要:")
    print(f"  生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report['generated_at']))}")
    print(f"  总比较次数: {report['statistics']['total_comparisons']}")
    print(f"  匹配次数: {report['statistics']['matches']}")
    print(f"  匹配率: {report['statistics']['match_rate']:.2%}")
    print(f"  平均处理时间差: {report['statistics']['average_processing_time']:.6f}秒")

    if report['difference_types']:
        print("\n差异类型统计:")
        for field, count in report['difference_types'].items():
            print(f"  {field}: {count}次")

    print("\n最近5条比较结果:")
    results = shadow_system.get_comparison_results(5)
    for result in results:
        status = "✅" if result['match'] else "❌"
        print(f"  {status} {result['input_id']}: 匹配={result['match']}, 差异数={len(result['differences'])}")

    print("\n测试回放功能...")
    shadow_system.start_replay()

    print("等待回放完成 (3秒)...")
    time.sleep(3)

    print("\n影子系统测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_shadow_system()
