#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影子系统（Shadow System）
用于在不影响主系统的情况下进行测试和监控

import time
import uuid
import logging
import threading
# JSON import removed - using database
from enum import Enum
from collections import defaultdict, deque

# 配置日志
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
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"          # 运行中
    PAUSED = "paused"            # 已暂停
    SHUTTING_DOWN = "shutting_down"  # 正在关闭
    SHUTDOWN = "shutdown"        # 已关闭

class ShadowMode(Enum):
    """影子系统模式枚举"""
    MONITOR = "monitor"          # 仅监控，不处理
    PARALLEL = "parallel"        # 并行处理，比较结果
    RECORD = "record"           # 记录输入，用于回放
    REPLAY = "replay"           # 回放记录的输入

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
            "mode_switch_threshold": 0.1  # 10% 不匹配率触发模式切换
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

        # 启动处理线程
        self._start_processing_threads()

        # 启动性能监控线程
        if self.config["performance_monitoring_enabled"]:
            self.performance_thread = threading.Thread(target=self._performance_monitoring_loop)
            self.performance_thread.daemon = True
            self.performance_thread.start()

        logger.info(f"影子系统已启动: {self.system_id}")

    def _start_processing_threads(self):
        """启动处理线程"""
        with self.lock:
            # 清除现有线程
            self.processing_threads = []
            # 启动指定数量的线程
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
        # 等待所有处理线程结束
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
            mode = ShadowMode(mode)

        self.mode = mode
        logger.info(f"影子系统模式已设置为: {mode.value}")

    def configure(self, **kwargs):
        """配置影子系统"""
        with self.lock:
            self.config.update(kwargs)
            logger.info(f"影子系统已配置: {kwargs}")

    def inject_input(self, input_data, input_id=None):
        """注入输入到影子系统"""
            return

        input_id = input_id or f"input_{uuid.uuid4().hex[:8]}"

            # 记录输入（如果启用）
            if self.config["recording_enabled"]:
                record = {
                    "input_id": input_id,
                    "input_data": input_data,
                    "timestamp": time.time()
                self.input_records.append(record)

                if len(self.input_records) > self.config["max_records_size"]:
                    self.input_records.pop(0)

            # 添加到处理队列
            self.input_queue.append((input_id, input_data))

            # 限制队列大小
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
                # 从队列获取输入
                input_id, input_data = None, None
                with self.lock:
                    if self.input_queue:
                        input_id, input_data = self.input_queue.popleft()

                if input_id and input_data:
                    start_time = time.time()
                    self._process_input(input_id, input_data)
                    processing_time = time.time() - start_time
                    # 更新性能指标
                    with self.lock:
                        self.performance_metrics["processing_time_history"].append(processing_time)
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"处理输入时发生错误: {str(e)}")
                time.sleep(0.1)

        """性能监控循环"""
        while self.is_running:
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(1)
                continue

                with self.lock:
                    # 更新队列大小历史
                    self.performance_metrics["queue_size_history"].append(queue_size)

                    # 计算平均处理时间
                        avg_time = sum(self.performance_metrics["processing_time_history"]) / len(self.performance_metrics["processing_time_history"])
                # 检查是否需要自动扩缩容
                if self.config["auto_scaling_enabled"]:
                    self._auto_scale()

                if self.config["smart_mode_switching"]:
                    self._smart_mode_switch()
                time.sleep(5)  # 每5秒检查一次
            except Exception as e:
                logger.error(f"性能监控时发生错误: {str(e)}")
                time.sleep(5)

    def _auto_scale(self):
        """自动扩缩容处理线程"""
        # 避免过于频繁地扩缩容
        if time.time() - self.last_scaling_time < 30:
            return

        with self.lock:
            queue_size = len(self.input_queue)
            current_threads = self.current_thread_count
        # 检查是否需要扩容
        if queue_size > self.config["scaling_threshold_high"] and current_threads < self.max_threads:
            # 扩容
            new_thread_count = min(current_threads + 1, self.max_threads)
            self._adjust_thread_count(new_thread_count)
        # 检查是否需要缩容
            # 缩容
            new_thread_count = max(current_threads - 1, self.min_threads)
            self._adjust_thread_count(new_thread_count)
            logger.info(f"影子系统自动缩容: {current_threads} -> {new_thread_count}, 队列大小: {queue_size}")

    def _adjust_thread_count(self, new_thread_count):
        """调整处理线程数量"""
        with self.lock:
            self.current_thread_count = new_thread_count

        # 重启处理线程
        self.last_scaling_time = time.time()

    def _smart_mode_switch(self):
        """智能模式切换"""
            return

        with self.lock:
            mismatched = self.performance_metrics["total_mismatched"]

            return

        # 计算不匹配率
        mismatch_rate = mismatched / total
        # 如果不匹配率过高，切换到监控模式
            self.set_mode(ShadowMode.MONITOR)
            self.last_mode_switch_time = time.time()
        # 如果不匹配率正常，切换回并行模式
        elif mismatch_rate <= self.config["mode_switch_threshold"] and self.mode != ShadowMode.PARALLEL:
            self.set_mode(ShadowMode.PARALLEL)
            logger.info(f"智能模式切换: {self.mode.value} -> PARALLEL, 不匹配率: {mismatch_rate:.2%}")
            self.last_mode_switch_time = time.time()
    def _process_input(self, input_id, input_data):
        """处理单个输入"""
        logger.debug(f"处理输入: {input_id}")

        if self.mode == ShadowMode.MONITOR:
            # 仅监控，不处理
            logger.debug(f"监控模式: 跳过输入处理: {input_id}")
            return

        elif self.mode == ShadowMode.PARALLEL:
            # 并行处理，比较结果
            self._process_parallel(input_id, input_data)

        elif self.mode == ShadowMode.RECORD:
            # 仅记录，不处理

        elif self.mode == ShadowMode.REPLAY:
            # 回放模式，不处理新输入
            logger.debug(f"回放模式: 跳过新输入: {input_id}")

    def _process_parallel(self, input_id, input_data):
        """并行处理输入并比较结果"""
        try:
            # 调用主系统处理（如果可用）
            main_result = None
            if self.main_system:
                main_result = self._call_main_system(input_data)

            # 调用影子系统处理
            shadow_result = self._call_shadow_system(input_data)

            # 比较结果（如果启用）
            if self.config["comparison_enabled"]:
                comparison = self._compare_results(input_id, input_data, main_result, shadow_result)

                with self.lock:
                    self.comparison_results.append(comparison)

                    # 限制结果大小
                    if len(self.comparison_results) > self.config["max_results_size"]:
                        self.comparison_results.pop(0)

                    # 更新性能指标
                    self.performance_metrics["total_processed"] += 1
                    if comparison["match"]:
                        self.performance_metrics["total_matched"] += 1
                    else:
                        self.performance_metrics["total_mismatched"] += 1
        except Exception as e:
            logger.error(f"并行处理时发生错误: {str(e)}")

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
        logger.debug("调用主系统处理输入")

        if hasattr(self.main_system, "process"):
            return self.main_system.process(input_data)
        elif hasattr(self.main_system, "handle"):
            return self.main_system.handle(input_data)

        time.sleep(0.01)
        return {
            "status": "success",
            "result": f"main_result_{time.time()}",
        }

        logger.debug("调用影子系统处理输入")

        # 模拟影子系统处理
        time.sleep(0.01)
        return {
            "status": "success",
            "result": f"shadow_result_{time.time()}",
            "timestamp": time.time()
        }

    def _compare_results(self, input_id, input_data, main_result, shadow_result):
        logger.debug(f"比较结果: {input_id}")

        # 比较结果
        match = False
        differences = []

        if main_result and shadow_result:
            # 比较状态
            if main_result.get("status") == shadow_result.get("status"):
                match = True
            else:
                differences.append({
                    "main_value": main_result.get("status"),
                    "shadow_value": shadow_result.get("status")
                })
                match = False

            # 比较结果内容
            if main_result.get("result") != shadow_result.get("result"):
                differences.append({
                    "field": "result",
                    "main_value": main_result.get("result"),
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

        if not match:
            logger.debug(f"结果匹配: {input_id}")

        return comparison

    def start_replay(self):
        """开始回放记录的输入"""
        if not self.input_records:
            logger.warning("没有可回放的输入记录")

        self.set_mode(ShadowMode.REPLAY)
        self.replay_index = 0

        logger.info("开始回放输入记录")
        # 启动回放线程
        self.replay_thread = threading.Thread(target=self._replay_loop)
        self.replay_thread.start()

    def _replay_loop(self):
        while self.is_running and self.replay_index < len(self.input_records):
            if self.status != ShadowSystemStatus.RUNNING:
                time.sleep(0.1)
                continue

                # 获取下一条记录
                record = self.input_records[self.replay_index]
                self.replay_index += 1

                shadow_result = self._call_shadow_system(record["input_data"])

                logger.debug(f"回放输入: {record['input_id']}, 索引: {self.replay_index}/{len(self.input_records)}")
                time.sleep(0.1)  # 控制回放速度
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
                    "total_processed": self.performance_metrics["total_processed"],
                    "total_matched": self.performance_metrics["total_matched"],
                    "mismatch_rate": self.performance_metrics["total_mismatched"] / self.performance_metrics["total_processed"] if self.performance_metrics["total_processed"] > 0 else 0,
                    "average_processing_time": self.performance_metrics["average_processing_time"]
                },
            }

        """获取比较结果"""

    def get_input_records(self, limit=100):
        """获取输入记录"""
        with self.lock:
            return self.input_records[-limit:]

    def generate_report(self):
        with self.lock:
            if not self.comparison_results:
                return {"message": "没有比较结果"}

            # 计算统计信息
            total = len(self.comparison_results)
            matches = sum(1 for r in self.comparison_results if r["match"])
            mismatches = total - matches

            difference_types = defaultdict(int)
            for result in self.comparison_results:
                    difference_types[diff["field"]] += 1

            report = {
                "report_id": f"report_{uuid.uuid4().hex[:8]}",
                "system_id": self.system_id,
                "statistics": {
                    "total_comparisons": total,
                    "match_rate": matches / total if total > 0 else 0,
                    "average_processing_time": avg_processing_time
                },
                "difference_types": dict(difference_types),
                "recent_results": self.comparison_results[-10:]
            }
            # 保存报告
            report_file = f"shadow_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"比较报告已生成: {report_file}")
            return report

# 测试影子系统
class TestMainSystem:
    """测试用的主系统"""
        self.name = "TestMainSystem"
    def process(self, input_data):
        time.sleep(0.005)
        return {
            "result": f"main_{input_data.get('type', 'default')}_{time.time()}",
        }

# 测试用的影子系统处理器
class TestShadowSystem:
    def __init__(self):
        self.name = "TestShadowSystem"

    def process(self, input_data):
        """处理输入"""
        time.sleep(0.005)
        # 模拟影子系统处理，故意制造一些差异
        if input_data.get('type') == 'error':
            return {
                "status": "error",
                "result": f"shadow_error_{time.time()}",
                "timestamp": time.time()
            }
        return {
            "status": "success",
            "result": f"shadow_{input_data.get('type', 'default')}_{time.time()}",
        }

def test_shadow_system():
    """测试影子系统"""
    print("影子系统测试")
    print("=" * 60)

    # 创建测试主系统和影子系统处理器
    main_system = TestMainSystem()

    # 创建影子系统
    shadow_system = ShadowSystem("test_shadow_system", main_system)

    # 配置影子系统
    shadow_system.configure(
        comparison_enabled=True,
        recording_enabled=True,
        max_queue_size=100
    # 启动影子系统
    shadow_system.start()

    # 注入测试输入
    print("\n注入测试输入...")

    test_inputs = [
        {"type": "normal", "data": "test_data_2"},
        {"type": "error", "data": "test_data_3"},  # 会产生差异
        {"type": "normal", "data": "test_data_4"},
        {"type": "normal", "data": "test_data_5"}
    ]
    for i, input_data in enumerate(test_inputs):
        shadow_system.inject_input(input_data, f"test_input_{i+1}")
    # 等待处理完成
    print("\n等待处理完成 (2秒)...")
    time.sleep(2)

    status = shadow_system.get_status()
    print("\n影子系统状态:")
        if key != "config":
            print(f"  {key}: {value}")

    # 生成比较报告
    print("\n生成比较报告...")
    report = shadow_system.generate_report()

    print("\n比较报告摘要:")
    print(f"  生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report['generated_at']))}")
    print(f"  总比较次数: {report['statistics']['total_comparisons']}")
    print(f"  匹配次数: {report['statistics']['matches']}")
    print(f"  匹配率: {report['statistics']['match_rate']:.2%}")
    print(f"  平均处理时间差: {report['statistics']['average_processing_time']:.6f}秒")

        print("\n差异类型统计:")
        for field, count in report['difference_types'].items():
            print(f"  {field}: {count}次")

    print("\n最近5条比较结果:")
    results = shadow_system.get_comparison_results(5)
    for result in results:
        status = "✅" if result['match'] else "❌"
        print(f"  {status} {result['input_id']}: 匹配={result['match']}, 差异数={len(result['differences'])}")

    # 测试回放功能
    print("\n测试回放功能...")

    # 等待回放完成
    print("等待回放完成 (3秒)...")


    print("影子系统测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_shadow_system()
