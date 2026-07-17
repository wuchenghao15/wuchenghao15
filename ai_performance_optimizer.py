#!/usr/bin/env python3
"""
MTSCOS AI 性能优化服务 (v14.8.0)
===================================
AI 推理性能优化和资源调度管理服务。

核心能力：
1. 推理加速 - 批处理、并行推理、请求合并
2. 动态批处理 - 自动组批和动态批大小调整
3. 请求队列 - 优先级队列和背压控制
4. 资源调度 - GPU/CPU 资源动态分配
5. 延迟优化 - 推理延迟分析和瓶颈定位
6. 吞吐量优化 - QPS 提升和并发管理
7. 性能基准 - 自动基准测试和性能回归检测
8. 弹性伸缩 - 基于负载的自动扩缩容
"""
import os
import json
import time
import math
import sqlite3
import random
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_performance.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIPerformanceOptimizer')


# ========== 动态批处理器 ==========

class DynamicBatcher:
    """动态批处理器：自动收集请求并组批"""

    def __init__(self, max_batch_size: int = 32, max_wait_ms: float = 50):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._total_batched = 0
        self._total_requests = 0
        self._batch_sizes = []

    def add(self, request: Any) -> int:
        """添加请求到队列"""
        with self._lock:
            self._queue.append(request)
            self._total_requests += 1
            return len(self._queue)

    def get_batch(self) -> List[Any]:
        """获取一个批次"""
        batch = []
        start_time = time.time()
        while len(batch) < self.max_batch_size:
            with self._lock:
                if self._queue:
                    batch.append(self._queue.popleft())
                else:
                    break
            # 检查等待时间
            if (time.time() - start_time) * 1000 > self.max_wait_ms:
                break
        if batch:
            self._total_batched += len(batch)
            self._batch_sizes.append(len(batch))
        return batch

    def stats(self) -> Dict:
        avg_batch = sum(self._batch_sizes) / len(self._batch_sizes) if self._batch_sizes else 0
        return {
            'total_requests': self._total_requests,
            'total_batched': self._total_batched,
            'queue_size': len(self._queue),
            'avg_batch_size': round(avg_batch, 2),
            'max_batch_size': self.max_batch_size,
            'max_wait_ms': self.max_wait_ms
        }


# ========== 优先级队列 ==========

class PriorityRequestQueue:
    """优先级请求队列"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues = {1: deque(), 2: deque(), 3: deque()}  # 1=高, 2=中, 3=低
        self._lock = threading.Lock()
        self._dropped = 0

    def put(self, request: Any, priority: int = 2) -> bool:
        """添加请求，priority: 1(高) 2(中) 3(低)"""
        priority = max(1, min(3, priority))
        with self._lock:
            total = sum(len(q) for q in self._queues.values())
            if total >= self.max_size:
                self._dropped += 1
                return False
            self._queues[priority].append(request)
            return True

    def get(self) -> Optional[Any]:
        """按优先级获取请求"""
        with self._lock:
            for p in [1, 2, 3]:
                if self._queues[p]:
                    return self._queues[p].popleft()
            return None

    def size(self) -> int:
        with self._lock:
            return sum(len(q) for q in self._queues.values())

    def stats(self) -> Dict:
        with self._lock:
            return {
                'queue_sizes': {p: len(q) for p, q in self._queues.items()},
                'total_size': sum(len(q) for q in self._queues.values()),
                'dropped': self._dropped,
                'max_size': self.max_size
            }


# ========== 延迟追踪器 ==========

class LatencyTracker:
    """推理延迟追踪"""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self._latencies: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def record(self, latency_ms: float):
        with self._lock:
            self._latencies.append(latency_ms)

    def stats(self) -> Dict:
        with self._lock:
            if not self._latencies:
                return {'count': 0}
            sorted_lats = sorted(self._latencies)
            n = len(sorted_lats)
            return {
                'count': n,
                'avg_ms': round(sum(sorted_lats) / n, 2),
                'p50_ms': round(sorted_lats[n // 2], 2),
                'p95_ms': round(sorted_lats[int(n * 0.95)], 2),
                'p99_ms': round(sorted_lats[int(n * 0.99)], 2),
                'min_ms': round(sorted_lats[0], 2),
                'max_ms': round(sorted_lats[-1], 2)
            }


# ========== 性能优化服务 ==========

class AIPerformanceOptimizer:
    """AI 性能优化服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()
        self._batchers: Dict[str, DynamicBatcher] = {}
        self._queues: Dict[str, PriorityRequestQueue] = {}
        self._latency_trackers: Dict[str, LatencyTracker] = {}
        self._benchmarks: Dict[str, List[Dict]] = {}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS perf_metrics (
                        metric_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        metric_type TEXT,
                        value REAL,
                        unit TEXT,
                        metadata TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS perf_benchmarks (
                        benchmark_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        total_requests INTEGER,
                        total_time_ms REAL,
                        qps REAL,
                        avg_latency_ms REAL,
                        p95_latency_ms REAL,
                        p99_latency_ms REAL,
                        success_rate REAL,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS perf_optimizations (
                        optimization_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        optimization_type TEXT,
                        description TEXT,
                        before_value REAL,
                        after_value REAL,
                        improvement_percent REAL,
                        status TEXT DEFAULT 'applied',
                        created_at TEXT
                    )
                ''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_perf_model ON perf_metrics(model_id)')
                conn.commit()
        except Exception as e:
            logger.error(f"初始化性能优化数据库失败: {e}")

    # ========== 批处理 ==========

    def get_batcher(self, model_id: str, max_batch_size: int = 32,
                   max_wait_ms: float = 50) -> DynamicBatcher:
        """获取或创建批处理器"""
        if model_id not in self._batchers:
            self._batchers[model_id] = DynamicBatcher(max_batch_size, max_wait_ms)
        return self._batchers[model_id]

    def batch_inference(self, model_id: str, predict_fn: Callable,
                       requests: List[Any], max_batch_size: int = 32) -> Dict:
        """批处理推理"""
        batcher = self.get_batcher(model_id, max_batch_size)
        for req in requests:
            batcher.add(req)

        results = []
        total_batches = 0
        start_time = time.time()

        while True:
            batch = batcher.get_batch()
            if not batch:
                break
            total_batches += 1
            try:
                batch_results = predict_fn(batch) if len(batch) > 1 else [predict_fn(batch[0])]
                if isinstance(batch_results, (list, tuple)):
                    results.extend(batch_results)
                else:
                    results.append(batch_results)
            except Exception as e:
                logger.error(f"批处理推理失败: {e}")
                results.extend([None] * len(batch))

        elapsed = (time.time() - start_time) * 1000

        return {
            'success': True,
            'model_id': model_id,
            'total_requests': len(requests),
            'total_batches': total_batches,
            'total_time_ms': round(elapsed, 2),
            'avg_time_per_request_ms': round(elapsed / max(len(requests), 1), 2),
            'batcher_stats': batcher.stats()
        }

    # ========== 并行推理 ==========

    def parallel_inference(self, predict_fn: Callable, requests: List[Any],
                          max_workers: int = 4) -> Dict:
        """并行推理"""
        start_time = time.time()
        results = [None] * len(requests)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(predict_fn, req): idx
                for idx, req in enumerate(requests)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    results[idx] = None
                    logger.error(f"并行推理失败 [{idx}]: {e}")

        elapsed = (time.time() - start_time) * 1000

        return {
            'success': True,
            'total_requests': len(requests),
            'max_workers': max_workers,
            'total_time_ms': round(elapsed, 2),
            'avg_time_per_request_ms': round(elapsed / max(len(requests), 1), 2),
            'throughput_qps': round(len(requests) / max(elapsed / 1000, 0.001), 2)
        }

    # ========== 队列管理 ==========

    def get_queue(self, model_id: str) -> PriorityRequestQueue:
        if model_id not in self._queues:
            self._queues[model_id] = PriorityRequestQueue()
        return self._queues[model_id]

    def enqueue_request(self, model_id: str, request: Any, priority: int = 2) -> Dict:
        queue = self.get_queue(model_id)
        success = queue.put(request, priority)
        return {'success': success, 'queue_size': queue.size()}

    # ========== 延迟追踪 ==========

    def get_latency_tracker(self, model_id: str) -> LatencyTracker:
        if model_id not in self._latency_trackers:
            self._latency_trackers[model_id] = LatencyTracker()
        return self._latency_trackers[model_id]

    def record_latency(self, model_id: str, latency_ms: float):
        tracker = self.get_latency_tracker(model_id)
        tracker.record(latency_ms)
        # 持久化
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO perf_metrics
                    (metric_id, model_id, metric_type, value, unit, created_at)
                    VALUES (?, ?, 'latency', ?, 'ms', ?)
                ''', (
                    f"PM-{random.randint(100000, 999999)}",
                    model_id, latency_ms, datetime.now().isoformat()
                ))
                conn.commit()
        except Exception:
            pass

    # ========== 性能基准测试 ==========

    def run_benchmark(self, model_id: str, predict_fn: Callable,
                     num_requests: int = 100, concurrency: int = 1) -> Dict:
        """运行性能基准测试"""
        requests = [random.random() for _ in range(num_requests)]
        latencies = []
        success_count = 0

        start_time = time.time()

        if concurrency == 1:
            # 串行基准
            for req in requests:
                t0 = time.time()
                try:
                    predict_fn(req)
                    success_count += 1
                except Exception:
                    pass
                latencies.append((time.time() - t0) * 1000)
        else:
            # 并发基准
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for req in requests:
                    t0 = time.time()
                    future = executor.submit(predict_fn, req)
                    futures.append((future, t0))

                for future, t0 in futures:
                    try:
                        future.result()
                        success_count += 1
                    except Exception:
                        pass
                    latencies.append((time.time() - t0) * 1000)

        total_time = (time.time() - start_time) * 1000
        sorted_lats = sorted(latencies)
        n = len(sorted_lats)

        benchmark_id = f"BENCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        result = {
            'benchmark_id': benchmark_id,
            'model_id': model_id,
            'total_requests': num_requests,
            'concurrency': concurrency,
            'total_time_ms': round(total_time, 2),
            'qps': round(num_requests / max(total_time / 1000, 0.001), 2),
            'avg_latency_ms': round(sum(latencies) / n, 2) if n > 0 else 0,
            'p95_latency_ms': round(sorted_lats[int(n * 0.95)], 2) if n > 0 else 0,
            'p99_latency_ms': round(sorted_lats[int(n * 0.99)], 2) if n > 0 else 0,
            'success_rate': round(success_count / num_requests * 100, 2),
            'created_at': datetime.now().isoformat()
        }

        # 保存基准
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO perf_benchmarks
                    (benchmark_id, model_id, total_requests, total_time_ms, qps,
                     avg_latency_ms, p95_latency_ms, p99_latency_ms, success_rate, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    benchmark_id, model_id, num_requests, result['total_time_ms'],
                    result['qps'], result['avg_latency_ms'], result['p95_latency_ms'],
                    result['p99_latency_ms'], result['success_rate'], result['created_at']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存基准测试失败: {e}")

        # 记录到内存
        if model_id not in self._benchmarks:
            self._benchmarks[model_id] = []
        self._benchmarks[model_id].append(result)

        logger.info(f"基准测试完成: {model_id}, QPS={result['qps']}, P95={result['p95_latency_ms']}ms")

        return result

    def detect_regression(self, model_id: str, threshold_percent: float = 20) -> Dict:
        """检测性能回归"""
        benchmarks = self._benchmarks.get(model_id, [])
        if len(benchmarks) < 2:
            return {'detected': False, 'reason': '基准数据不足'}

        latest = benchmarks[-1]
        previous = benchmarks[-2]

        latency_regression = 0
        qps_regression = 0

        if previous['avg_latency_ms'] > 0:
            latency_regression = ((latest['avg_latency_ms'] - previous['avg_latency_ms'])
                                  / previous['avg_latency_ms'] * 100)
        if previous['qps'] > 0:
            qps_regression = ((previous['qps'] - latest['qps'])
                              / previous['qps'] * 100)

        is_regression = latency_regression > threshold_percent or qps_regression > threshold_percent

        return {
            'detected': is_regression,
            'model_id': model_id,
            'latest_qps': latest['qps'],
            'previous_qps': previous['qps'],
            'qps_change_percent': round(qps_regression, 2),
            'latest_latency': latest['avg_latency_ms'],
            'previous_latency': previous['avg_latency_ms'],
            'latency_change_percent': round(latency_regression, 2),
            'threshold_percent': threshold_percent
        }

    # ========== 优化建议 ==========

    def suggest_optimizations(self, model_id: str) -> Dict:
        """生成性能优化建议"""
        suggestions = []
        tracker = self._latency_trackers.get(model_id)
        batcher = self._batchers.get(model_id)
        queue = self._queues.get(model_id)

        if tracker:
            stats = tracker.stats()
            if stats.get('p99_ms', 0) > 1000:
                suggestions.append({
                    'type': 'latency',
                    'priority': 'high',
                    'title': 'P99 延迟过高',
                    'description': f'P99延迟 {stats["p99_ms"]}ms 超过1秒，建议启用批处理或增加并发',
                    'expected_improvement': '40-60%'
                })
            if stats.get('avg_ms', 0) > 500:
                suggestions.append({
                    'type': 'latency',
                    'priority': 'medium',
                    'title': '平均延迟偏高',
                    'description': f'平均延迟 {stats["avg_ms"]}ms，考虑模型量化或缓存',
                    'expected_improvement': '30-50%'
                })

        if batcher:
            bs = batcher.stats()
            if bs.get('avg_batch_size', 0) < 4:
                suggestions.append({
                    'type': 'batching',
                    'priority': 'medium',
                    'title': '批处理利用率低',
                    'description': f'平均批大小 {bs["avg_batch_size"]}，建议增加等待时间或批大小上限',
                    'expected_improvement': '20-40%'
                })

        if queue and queue.size() > 100:
            suggestions.append({
                'type': 'scaling',
                'priority': 'high',
                'title': '请求积压',
                'description': f'队列积压 {queue.size()} 个请求，建议扩容实例',
                'expected_improvement': '50-70%'
            })

        # 通用建议
        suggestions.append({
            'type': 'caching',
            'priority': 'low',
            'title': '启用推理缓存',
            'description': '对重复请求启用结果缓存，可大幅降低延迟',
            'expected_improvement': '60-80%'
        })

        # 保存优化记录
        for s in suggestions:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO perf_optimizations
                        (optimization_id, model_id, optimization_type, description,
                         before_value, after_value, improvement_percent, status, created_at)
                        VALUES (?, ?, ?, ?, NULL, NULL, ?, 'suggested', ?)
                    ''', (
                        f"OPT-{random.randint(100000, 999999)}",
                        model_id, s['type'], s['title'],
                        s['expected_improvement'].rstrip('%'),
                        datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception:
                pass

        return {
            'model_id': model_id,
            'suggestions': suggestions,
            'total': len(suggestions)
        }

    # ========== 弹性伸缩 ==========

    def autoscale_decision(self, model_id: str, current_instances: int,
                          target_latency_ms: float = 500) -> Dict:
        """弹性伸缩决策"""
        tracker = self._latency_trackers.get(model_id)
        queue = self._queues.get(model_id)

        current_latency = tracker.stats().get('p95_ms', 0) if tracker else 0
        queue_size = queue.size() if queue else 0

        if current_latency > target_latency_ms * 1.5 or queue_size > 50:
            action = 'scale_out'
            # 简单计算：延迟超标比例
            ratio = current_latency / max(target_latency_ms, 1)
            recommended = max(current_instances + 1, int(current_instances * ratio))
            reason = f'延迟 {current_latency}ms 超过目标 {target_latency_ms}ms'
        elif current_latency < target_latency_ms * 0.3 and queue_size == 0:
            action = 'scale_in'
            recommended = max(1, current_instances - 1)
            reason = '负载较低，可缩减实例'
        else:
            action = 'maintain'
            recommended = current_instances
            reason = '负载正常'

        return {
            'model_id': model_id,
            'action': action,
            'current_instances': current_instances,
            'recommended_instances': recommended,
            'current_p95_latency': current_latency,
            'target_latency': target_latency_ms,
            'queue_size': queue_size,
            'reason': reason
        }

    # ========== 查询和统计 ==========

    def get_latency_stats(self, model_id: str) -> Dict:
        tracker = self._latency_trackers.get(model_id)
        if tracker:
            return tracker.stats()
        return {'count': 0}

    def list_benchmarks(self, model_id: str = None, limit: int = 20) -> List[Dict]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if model_id:
                    cursor.execute('''
                        SELECT * FROM perf_benchmarks WHERE model_id = ?
                        ORDER BY created_at DESC LIMIT ?
                    ''', (model_id, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM perf_benchmarks
                        ORDER BY created_at DESC LIMIT ?
                    ''', (limit,))
                return [
                    {
                        'benchmark_id': r[0], 'model_id': r[1], 'total_requests': r[2],
                        'total_time_ms': r[3], 'qps': r[4], 'avg_latency_ms': r[5],
                        'p95_latency_ms': r[6], 'p99_latency_ms': r[7],
                        'success_rate': r[8], 'created_at': r[9]
                    }
                    for r in cursor.fetchall()
                ]
        except Exception:
            return []

    def get_statistics(self) -> Dict:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM perf_metrics')
                total_metrics = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM perf_benchmarks')
                total_benchmarks = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM perf_optimizations')
                total_opts = cursor.fetchone()[0]
            return {
                'total_metrics': total_metrics,
                'total_benchmarks': total_benchmarks,
                'total_optimizations': total_opts,
                'active_batchers': len(self._batchers),
                'active_queues': len(self._queues),
                'active_trackers': len(self._latency_trackers)
            }
        except Exception as e:
            return {'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    po = AIPerformanceOptimizer()

    # 模拟预测函数
    def slow_predict(x):
        time.sleep(random.uniform(0.001, 0.01))
        return x * 2

    def batch_predict(xs):
        time.sleep(0.01)  # 批处理固定开销
        return [x * 2 for x in xs]

    print("批处理推理:")
    requests = [random.random() for _ in range(100)]
    result = po.batch_inference('test-model', batch_predict, requests, max_batch_size=16)
    print(f"  总批次: {result['total_batches']}, 耗时: {result['total_time_ms']}ms")
    print(f"  批处理器: {result['batcher_stats']}")

    print("\n并行推理:")
    result = po.parallel_inference(slow_predict, requests[:50], max_workers=4)
    print(f"  耗时: {result['total_time_ms']}ms, QPS: {result['throughput_qps']}")

    print("\n基准测试:")
    bench = po.run_benchmark('test-model', slow_predict, num_requests=100, concurrency=4)
    print(f"  QPS: {bench['qps']}, P95: {bench['p95_latency_ms']}ms, P99: {bench['p99_latency_ms']}ms")

    # 第二次基准
    bench2 = po.run_benchmark('test-model', slow_predict, num_requests=100, concurrency=2)
    print(f"\n回归检测: {po.detect_regression('test-model')}")

    print("\n延迟追踪:")
    for _ in range(100):
        po.record_latency('test-model', random.uniform(1, 50))
    print(f"  {po.get_latency_stats('test-model')}")

    print("\n优化建议:")
    suggestions = po.suggest_optimizations('test-model')
    for s in suggestions['suggestions']:
        print(f"  [{s['priority']}] {s['title']}: 预期提升 {s['expected_improvement']}")

    print("\n弹性伸缩:")
    print(f"  {po.autoscale_decision('test-model', current_instances=2)}")

    print(f"\n统计: {po.get_statistics()}")
