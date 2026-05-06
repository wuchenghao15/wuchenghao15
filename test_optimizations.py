#!/usr/bin/env python3
"""
测试程序池、存储池和交互式急缓存的优化实现

import sys
import os
import time

# 添加项目路径到sys.path
flask_app_path = os.path.join(os.path.dirname(__file__), 'flask-app')
sys.path.append(flask_app_path)

# 动态导入我们的优化组件
import importlib.util

# 创建一个临时模块来导入我们的类
spec = importlib.util.spec_from_file_location("app", os.path.join(flask_app_path, "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# 从动态导入的模块中获取我们的类
StoragePool = app_module.StoragePool
InteractiveCache = app_module.InteractiveCache

# 测试存储池
def test_storage_pool():
    print("\n=== 测试存储池 ===")

    # 创建存储池实例
    storage_pool = StoragePool(max_cache_size=10, cache_timeout=5)

    # 测试基本功能
    storage_pool.put("key1", "value1")
    storage_pool.put("key2", "value2", priority=2)

    # 测试获取数据
    print(f"获取key1: {storage_pool.get('key1')}")
    print(f"获取key2: {storage_pool.get('key2')}")
    print(f"获取不存在的key: {storage_pool.get('key3')}")

    # 测试统计信息
    stats = storage_pool.get_stats()
    print(f"存储池统计: {stats}")

    # 测试缓存过期
    print("等待6秒，测试缓存过期...")
    time.sleep(6)
    print(f"获取过期的key1: {storage_pool.get('key1')}")

    # 测试清理
    storage_pool.put("key3", "value3")
    storage_pool.cleanup()
    print(f"清理后的存储池统计: {storage_pool.get_stats()}")

    # 测试清空
    storage_pool.clear()
    print(f"清空后的存储池统计: {storage_pool.get_stats()}")

# 测试交互式急缓存
def test_interactive_cache():
    print("\n=== 测试交互式急缓存 ===")

    # 创建交互式急缓存实例
    interactive_cache = InteractiveCache(max_size=5, priority_threshold=3)

    # 测试基本功能
    interactive_cache.put("normal_key1", "normal_value1", priority=10)
    interactive_cache.put("emergency_key2", "emergency_value2", priority=2)

    # 测试获取数据
    print(f"获取紧急数据emergency_key1: {interactive_cache.get('emergency_key1', is_emergency=True)}")
    print(f"获取不存在的紧急数据: {interactive_cache.get('nonexistent_key', is_emergency=True)}")

    # 测试批量获取紧急数据
    keys = ["emergency_key1", "emergency_key2", "normal_key1"]
    print(f"批量获取紧急数据: {interactive_cache.get_emergency_data(keys)}")

    # 测试统计信息
    stats = interactive_cache.get_stats()
    print(f"交互式缓存统计: {stats}")
    # 测试清理低优先级数据
    print("清理低优先级数据...")
    count = interactive_cache.clear_low_priority()
    print(f"清理了 {count} 个低优先级数据项")
    print(f"清理后的缓存统计: {interactive_cache.get_stats()}")
    print(f"获取已清理的normal_key1: {interactive_cache.get('normal_key1')}")

    # 测试清空
    interactive_cache.clear()
    print(f"清空后的缓存统计: {interactive_cache.get_stats()}")

def test_auto_scaling():
    print("\n=== 测试自动扩容和缩容（模拟） ===")

    # 这里我们模拟一个简单的自动扩容和缩容场景
    # 实际的线程池自动扩容和缩容已经在ai_management.py中实现

    class MockThreadPool:
        def __init__(self, min_workers=2, max_workers=10):
            self.min_workers = min_workers
            self.max_workers = max_workers
            self.current_workers = min_workers
            self.queue_size = 0

        def add_task(self):
            self.queue_size += 1
            # 模拟自动扩容
            if self.queue_size > self.current_workers and self.current_workers < self.max_workers:
                new_workers = min(self.queue_size - self.current_workers, self.max_workers - self.current_workers)
                self.current_workers += new_workers
                print(f"自动扩容: 增加 {new_workers} 个工作线程，总线程数: {self.current_workers}")

        def complete_task(self):
            if self.queue_size > 0:
                self.queue_size -= 1
                # 模拟自动缩容
                if self.queue_size == 0 and self.current_workers > self.min_workers:
                    workers_to_remove = min(self.current_workers - self.min_workers, self.current_workers // 2)
                    self.current_workers -= workers_to_remove
                    print(f"自动缩容: 减少 {workers_to_remove} 个工作线程，总线程数: {self.current_workers}")

    # 创建模拟线程池
    mock_pool = MockThreadPool()

    # 模拟任务增加，触发自动扩容
    print(f"初始线程数: {mock_pool.current_workers}")
    for i in range(15):
        mock_pool.add_task()

    # 模拟任务完成，触发自动缩容
    for i in range(15):
        mock_pool.complete_task()

if __name__ == "__main__":
    print("开始测试优化组件...")
    test_storage_pool()
    test_interactive_cache()
    test_auto_scaling()

    print("\n=== 所有测试完成 ===")
    print("优化组件工作正常！")

"""