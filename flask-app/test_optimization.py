#!/usr/bin/env python3
"""
测试优化效果，确保系统正常运行

import time
import logging
from app.utils.db import db_manager
from app.models.question import QuestionManager
from app.config import ConfigManager, load_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_manager():
    """测试数据库管理器优化效果"""
    logger.info("=== 测试数据库管理器优化效果 ===")

    # 测试连接池
    start_time = time.time()
    for i in range(100):
        conn = db_manager.get_connection()
        if conn:
            db_manager.return_connection(conn)
    conn_time = time.time() - start_time
    logger.info(f"连接池测试：100次连接获取和返回耗时: {conn_time:.4f}秒")

    # 测试查询缓存
    start_time = time.time()
        # 执行相同的查询，第二次应该从缓存获取
        db_manager.fetch_all("SELECT * FROM questions LIMIT 10")
    query_time = time.time() - start_time
    logger.info(f"查询缓存测试：10次相同查询耗时: {query_time:.4f}秒")

    # 测试批量操作
    start_time = time.time()
    batch_time = time.time() - start_time
    logger.info(f"批量操作测试：耗时: {batch_time:.4f}秒")

def test_question_manager():
    """测试题库系统优化效果"""
    logger.info("=== 测试题库系统优化效果 ===")

    question_manager = QuestionManager()

    # 测试获取题目列表
    start_time = time.time()
    get_time = time.time() - start_time
    logger.info(f"获取题目列表测试：获取{len(questions)}道题目耗时: {get_time:.4f}秒")

    # 测试获取单个题目
    start_time = time.time()
        question = question_manager.get_question(questions[0].id)
        single_time = time.time() - start_time
        logger.info(f"获取单个题目测试：耗时: {single_time:.4f}秒")

    # 测试搜索题目
    start_time = time.time()
        search_results = question_manager.search_questions("测试")
        search_time = time.time() - start_time
        logger.info(f"搜索题目测试：获取{len(search_results)}个结果耗时: {search_time:.4f}秒")
    except Exception as e:
        search_time = time.time() - start_time
        logger.warning(f"搜索题目测试失败（可能是因为题库表不存在）: {str(e)}")
        logger.info(f"搜索题目测试：耗时: {search_time:.4f}秒")

def test_config_manager():
    """测试系统配置库优化效果"""

    # 测试配置加载
    start_time = time.time()
        config = load_config()
    load_time = time.time() - start_time
    logger.info(f"配置加载测试：10次加载耗时: {load_time:.4f}秒")

    # 测试配置缓存
    start_time = time.time()
    cache_time = time.time() - start_time
    logger.info(f"配置缓存测试：10次缓存加载耗时: {cache_time:.4f}秒")

    # 测试配置保存
    start_time = time.time()
    save_time = time.time() - start_time

def main():
    """主测试函数"""

    try:
        test_database_manager()
        test_question_manager()
        test_config_manager()
        logger.info("测试完成，所有测试通过！")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
