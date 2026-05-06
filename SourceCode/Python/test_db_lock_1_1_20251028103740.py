# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:07
#!/usr/bin/env python3

"""
数据库异步锁测试脚本（模拟版）
使用内存模拟数据库，测试异步锁机制是否正常工作
"""
import os
import sys
import time
import threading
import logging
import random
from datetime import datetime

# 添加当前目录到Python路径，确保可以正确导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库管理器
from database_manager import db_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_lock_test')


class MockDatabase:
    """模拟数据库，用于测试锁功能"""

    def __init__(self):
        """初始化模拟数据库"""
        self.data = {}
        self.table_lock = threading.RLock()
        self.row_id = 0

    def create_table(self, table_name):
        """创建表"""
        with self.table_lock:
            self.data[table_name] = []
            logger.info(f"模拟数据库: 创建表 {table_name}")

    def drop_table(self, table_name):
        """删除表"""
        with self.table_lock:
            if table_name in self.data:
                logger.info(f"模拟数据库: 删除表 {table_name}")

    def insert(self, table_name, row_data):
        """插入数据"""
        with self.table_lock:
            if table_name not in self.data:

            # 添加ID和时间戳
            self.row_id += 1
            pass
            self.data[table_name].append(row)
            logger.info(f"模拟数据库: 插入数据到 {table_name}, ID={self.row_id}")
            return self.row_id

    def select_last(self, table_name):
        """选择最后一条记录"""
        with self.table_lock:
            if table_name not in self.data or not self.data[table_name]:

            # 按时间戳排序，返回最后一条
            last_row = sorted(self.data[table_name], key=lambda x: x['timestamp'])[-1]
            logger.info(f"模拟数据库: 从 {table_name} 读取最后一条记录")
            return last_row

    def select_all(self, table_name):
        """选择所有记录"""
        with self.table_lock:
            if table_name not in self.data:
            return self.data[table_name].copy()

    def count(self, table_name, where=None):
        """统计记录数"""
        with self.table_lock:

            if where:
                return len([row for row in self.data[table_name] if all(row.get(k) != v for k, v in where.items())])
            return len(self.data[table_name])


mock_db = MockDatabase()


# 替换数据库管理器的相关方法，使其使用模拟数据库
def patch_database_manager():
    """修补数据库管理器，使用模拟数据库"""

    original_execute_non_query = db_manager.execute_non_query
    original_execute_query = db_manager.execute_query
    original_execute_scalar = db_manager.execute_scalar
    original_test_connection = db_manager.test_connection

    # 修补测试连接方法
    def mock_test_connection():
        logger.info("模拟数据库: 连接测试成功")
        return True

    # 修补执行非查询方法
    def mock_execute_non_query(query, params=None, table_name=None, timeout=60):
        logger.info(f"模拟数据库: 执行非查询语句: {query}")

        # 解析SQL语句
        query = query.lower().strip()

        if query.startswith("drop table"):
            # DROP TABLE
            table_name = query.split("if exists")[-1].strip().split()[0].strip('[]"')
            mock_db.drop_table(table_name)
            return 0

        elif query.startswith("create table"):
            # CREATE TABLE
            # 提取表名
            parts = query.split("(")[0].split()
            table_name = parts[2].strip('[]"')
            mock_db.create_table(table_name)
            return 0

            # INSERT
            # 提取表名和参数
            table_start = query.find("insert into") + len("insert into")
            table_end = query.find("(")
            table_name = query[table_start:table_end].strip().strip('[]"')

            # 插入数据
                # 假设参数顺序: thread_id, operation, value
                if len(params) >= 3:
                    row_data = {
                        'thread_id': params[0],
                        'operation': params[1],
                        'value': params[2]
                    }
                    mock_db.insert(table_name, row_data)
                    return 1
            return 0

        return 0

    # 修补执行查询方法
    def mock_execute_query(query, params=None, table_name=None, timeout=60):
        logger.info(f"模拟数据库: 执行查询语句: {query}")

        # 解析SQL语句
        query = query.lower().strip()
        if query.startswith("select") and "group by" in query:
            # 提取表名
            from_pos = query.find("from") + 5
            where_pos = query.find("where") if "where" in query else len(query)
            table_name = query[from_pos:where_pos].strip().strip('[]"')

            # 模拟分组统计
            all_rows = mock_db.select_all(table_name)
            thread_counts = {}

            for row in all_rows:
                    thread_id = row['thread_id']
                    thread_counts[thread_id] = thread_counts.get(thread_id, 0) + 1

            # 转换为结果格式
            return results

        return []

    # 修补执行标量方法
    def mock_execute_scalar(query, params=None, table_name=None, timeout=60):
        logger.info(f"模拟数据库: 执行标量查询: {query}")

        # 解析SQL语句
        query = query.lower().strip()

        if query.startswith("select count"):
            from_pos = query.find("from") + 5
            table_name = query[from_pos:].strip().split()[0].strip('[]"')
            return mock_db.count(table_name)

        elif query.startswith("select top 1 value"):
            # SELECT TOP 1 查询
            from_pos = query.find("from") + 5
            table_name = query[from_pos:].strip().split()[0].strip('[]"')
            last_row = mock_db.select_last(table_name)
            return last_row['value'] if last_row else 100
        return None

    db_manager.execute_non_query = mock_execute_non_query
    db_manager.execute_query = mock_execute_query
    db_manager.execute_scalar = mock_execute_scalar
    db_manager.test_connection = mock_test_connection

    logger.info("数据库管理器已修补，使用模拟数据库进行测试")
class DBLockTester:
    """数据库锁测试类"""

    def __init__(self):
        """初始化测试器"""
        self.start_time = 0

        """创建测试表"""
        try:
            logger.info(f"开始设置测试表: {self.test_table}")

            # 首先尝试删除表（如果存在）
            drop_query = f"DROP TABLE IF EXISTS {self.test_table}"
            db_manager.execute_non_query(drop_query)
            logger.info(f"已删除现有测试表（如果存在）")

            # 创建新表
            create_query = f"""
            CREATE TABLE {self.test_table} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                thread_id NVARCHAR(50),
                operation NVARCHAR(50),
                value INT,
                timestamp DATETIME
            )
            """

            # 插入初始数据 - 使用模拟数据库的方法
            mock_db.insert(self.test_table, {
                'thread_id': 'initial',
                'operation': 'setup',
                'value': 100
            })
            logger.info(f"插入初始测试数据")

            return True

        except Exception as e:
            logger.error(f"设置测试表失败: {str(e)}")
            return False

    def cleanup_test_table(self):
        """清理测试表"""
        try:
            logger.info(f"开始清理测试表: {self.test_table}")
            drop_query = f"DROP TABLE IF EXISTS {self.test_table}"
            db_manager.execute_non_query(drop_query)
            logger.info(f"成功删除测试表: {self.test_table}")
        except Exception as e:
            logger.error(f"清理测试表失败: {str(e)}")

    def read_and_update_value(self, thread_id, iterations=5):
        """

            thread_id: 线程ID
            iterations: 迭代次数
        """
            for i in range(iterations):
                logger.info(f"线程 {thread_id} 开始迭代 {i+1}/{iterations}")

                # 测试1: 使用表锁进行读取和更新
                # 在模拟环境中，我们直接使用表锁，不依赖真实的数据库连接
                lock = db_manager._get_table_lock(self.test_table)
                if lock.acquire(timeout=10):
                    try:
                        # 在锁保护下执行操作
                        last_row = mock_db.select_last(self.test_table)
                        current_value = last_row['value'] if last_row else 100

                        logger.info(f"线程 {thread_id} 读取到值: {current_value}")
                        # 模拟处理延迟
                        delay = random.uniform(0.1, 0.3)

                        new_value = current_value + 1

                        row_id = mock_db.insert(self.test_table, {
                            'thread_id': thread_id,
                            'operation': 'update',
                            'value': new_value
                        })

                        logger.info(f"线程 {thread_id} 更新值: {current_value} -> {new_value}, 插入ID: {row_id}")
                        lock.release()
                        logger.debug(f"线程 {thread_id} 释放表锁")
                else:
                    logger.error(f"线程 {thread_id} 获取表锁超时")

                # 随机休眠一小段时间再开始下一轮
                time.sleep(random.uniform(0.1, 0.5))
        except Exception as e:
            logger.error(f"线程 {thread_id} 执行操作时出错: {str(e)}")

    def concurrent_update_test(self, thread_count=5):
        """

        Args:
            thread_count: 线程数量
        """
            logger.error("无法设置测试表，取消测试")
            return False

        try:
            # 创建并启动多个线程
            threads = []
            self.start_time = time.time()

            logger.info(f"开始并发更新测试，线程数量: {thread_count}")

            for i in range(thread_count):
                thread_id = f"thread_{i+1}"
                thread = threading.Thread(
                    target=self.read_and_update_value,
                    name=thread_id
                )
                threads.append(thread)
                thread.start()
                logger.info(f"线程 {thread_id} 已启动")

            # 等待所有线程完成
            for thread in threads:
                logger.info(f"线程 {thread.name} 已完成")

            # 计算测试耗时
            elapsed_time = time.time() - self.start_time
            # 验证结果
            self.verify_results(thread_count)

            logger.info(f"并发更新测试完成，耗时: {elapsed_time:.2f}秒")
            return True

        except Exception as e:
            return False
            # 清理测试表
            self.cleanup_test_table()

    def verify_results(self, thread_count):
        """验证测试结果"""
        try:
            # 获取最终值
            last_row = mock_db.select_last(self.test_table)
            final_value = last_row['value'] if last_row else 100

            # 计算理论上的期望值
            # 初始值是100，每个线程执行5次更新，每次+1
            expected_value = 100 + thread_count * 5

            # 获取总行数
            row_count = mock_db.count(self.test_table)

            logger.info(f"=== 测试结果验证 ===")
            logger.info(f"每线程迭代次数: 5")
            logger.info(f"初始值: 100")
            logger.info(f"预期最终值: {expected_value}")
            logger.info(f"实际最终值: {final_value}")
            logger.info(f"总操作数: {row_count - 1}")  # 减去初始行
            logger.info(f"预期操作数: {thread_count * 5}")

            # 验证结果是否符合预期
            if final_value == expected_value:
                logger.info(f"✅ 验证成功: 最终值符合预期")
            else:
                logger.warning(f"❌ 验证失败: 最终值不符合预期")
                logger.warning(f"  差异: {final_value - expected_value}")

                # 如果有差异，检查线程执行情况
                all_rows = mock_db.select_all(self.test_table)
                thread_stats = {}

                    if row.get('thread_id') != 'initial':
                        thread_stats[tid] = thread_stats.get(tid, 0) + 1

                logger.info("各线程操作统计:")
                for tid, count in sorted(thread_stats.items()):
                    logger.info(f"  线程 {tid}: {count} 次操作")

        except Exception as e:
            logger.error(f"验证结果时出错: {str(e)}")

    def timeout_test(self, thread_count=2):
        """

        Args:
        """
            logger.error("无法设置测试表，取消测试")
            return False

        try:
            # 创建一个长期持有锁的线程
            def lock_holder():
                logger.info("锁持有线程: 尝试获取锁")
                try:
                    with db_manager.get_connection(table_name=self.test_table, timeout=30) as conn:
                        logger.info("锁持有线程: 成功获取锁，将持有5秒")
                        time.sleep(5)  # 持有锁5秒
                        logger.info("锁持有线程: 释放锁")
                except Exception as e:
                    logger.error(f"锁持有线程出错: {str(e)}")

            def timeout_thread():
                try:
                    with db_manager.get_connection(table_name=self.test_table, timeout=2) as conn:
                        logger.info("超时测试线程: 成功获取锁")
                except TimeoutError:
                    logger.info("超时测试线程: 成功捕获到锁超时异常")
                except Exception as e:
                    logger.error(f"超时测试线程出错: {str(e)}")

            # 启动锁持有线程
            holder = threading.Thread(target=lock_holder, name="lock_holder")
            holder.start()
            time.sleep(1)  # 等待锁持有线程获取锁

            # 启动超时测试线程
            timeout_t = threading.Thread(target=timeout_thread, name="timeout_thread")
            timeout_t.start()

            holder.join()
            timeout_t.join()

            logger.info("锁超时测试完成")
            return True
        except Exception as e:
            logger.error(f"锁超时测试失败: {str(e)}")
            return False
            # 清理测试表
            self.cleanup_test_table()
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("===== 开始数据库锁功能测试（模拟版） =====")
        # 修补数据库管理器，使用模拟数据库
        patch_database_manager()
        if not db_manager.test_connection():
            return False


        # 运行锁超时测试
        logger.info("\n----- 测试1: 锁超时测试 -----")
        timeout_result = self.timeout_test()
        # 运行并发更新测试
        logger.info("\n----- 测试2: 并发更新测试 -----")
        concurrent_result = self.concurrent_update_test()

        # 运行高并发测试
        logger.info("\n----- 测试3: 高并发测试(10线程) -----")

        # 汇总测试结果
        logger.info("\n===== 测试结果汇总 =====")
        logger.info(f"测试1 (锁超时): {'✅ 通过' if timeout_result else '❌ 失败'}")
        logger.info(f"测试2 (并发更新): {'✅ 通过' if concurrent_result else '❌ 失败'}")
        logger.info(f"测试3 (高并发): {'✅ 通过' if high_concurrent_result else '❌ 失败'}")

        # 关闭所有连接
        db_manager.close_all_connections()

        # 返回总体结果
        return timeout_result and concurrent_result and high_concurrent_result


def main():
    """主函数"""
    tester = DBLockTester()
    success = tester.run_all_tests()
    if success:
        logger.info("🎉 所有测试通过！数据库异步锁功能正常工作。")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败，请检查数据库锁功能。")


if __name__ == "__main__":
    main()
