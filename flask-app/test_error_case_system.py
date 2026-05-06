#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理案例系统集成测试脚本
测试整个系统的功能和性能

import os
# JSON import removed - using database
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_error_case_system')

def test_error_case_collector():
    """测试异常处理案例收集器"""
    logger.info("开始测试异常处理案例收集器...")

    try:
        from app.ai.error_case_collector import error_case_collector, capture_errors

        # 测试异常捕获
        @capture_errors
        def test_function():
            raise ValueError("测试异常: 文件不存在")

        # 记录初始案例数量
        initial_count = len(error_case_collector.error_cases)
        logger.info(f"初始错误案例数量: {initial_count}")

        # 触发异常
        try:
        except Exception as e:
            logger.info(f"捕获到异常: {str(e)}")

        # 检查案例数量是否增加
        final_count = len(error_case_collector.error_cases)
        logger.info(f"测试后错误案例数量: {final_count}")

        if final_count > initial_count:
            logger.info("异常处理案例收集器测试通过")
            return True
        else:
            logger.error("异常处理案例收集器测试失败")
            return False
    except Exception as e:
        logger.error(f"测试异常处理案例收集器失败: {str(e)}")

def test_error_case_learner():
    logger.info("开始测试异常处理案例学习器...")

    try:

        # 测试预测功能
        test_errors = [
            "文件不存在: app/config/config.py",
            "数据库连接失败: 无法连接到SQLite数据库",
            "权限错误: 无法访问文件",
            "导入错误: 无法导入模块"
        ]

        for test_error in test_errors:
            error_type = error_case_learner.predict_error_type(test_error)
            solution = error_case_learner.predict_solution(test_error)
            recommendations = error_case_learner.get_recommendations(test_error)

            logger.info(f"测试错误: {test_error}")
            logger.info(f"预测错误类型: {error_type}")
            logger.info(f"预测解决方案: {solution}")
            logger.info(f"推荐解决方案数量: {len(recommendations)}")

            if recommendations:
                logger.info("最相似的解决方案:")
                for i, rec in enumerate(recommendations[:2]):
                    logger.info(f"  {i+1}. {rec['title']} (相似度: {rec['similarity']:.2f})")
                    logger.info(f"     解决方案: {rec['solution']}")

            logger.info("---")

        # 测试聚类分析
        cluster_report = error_case_learner.cluster_analysis()
        logger.info(f"聚类分析结果: {cluster_report.get('total_clusters', 0)} 个簇")

        # 测试统计信息
        stats = error_case_learner.get_statistics()
        logger.info(f"错误案例统计: {stats.get('total_cases', 0)} 条案例")
        logger.info(f"错误类型数量: {len(stats.get('error_types', {}))}")

        logger.info("异常处理案例学习器测试通过")
        return True
    except Exception as e:
        logger.error(f"测试异常处理案例学习器失败: {str(e)}")
        return False
    """测试集成功能"""
    logger.info("开始测试集成功能...")

        from app.ai.error_case_learner import error_case_learner

        # 测试异常捕获和学习的完整流程
        def integration_test_function():
            raise FileNotFoundError("集成测试: 文件不存在")

        # 记录初始状态
        logger.info(f"集成测试前错误案例数量: {initial_cases}")

        try:
        except Exception as e:
            logger.info(f"集成测试捕获到异常: {str(e)}")

        # 等待案例保存

        # 更新模型
        error_case_learner.update_model()

        # 测试预测
        test_error = "文件不存在: test_file.txt"
        error_type = error_case_learner.predict_error_type(test_error)
        solution = error_case_learner.predict_solution(test_error)

        logger.info(f"集成测试 - 测试错误: {test_error}")
        logger.info(f"集成测试 - 预测错误类型: {error_type}")
        logger.info(f"集成测试 - 预测解决方案: {solution}")

        logger.info("集成功能测试通过")
        return True
    except Exception as e:
        logger.error(f"测试集成功能失败: {str(e)}")
        return False

def test_performance():
    """测试系统性能"""


        start_time = time.time()
        error_case_collector._load_error_cases()
        load_time = time.time() - start_time
        logger.info(f"案例加载时间: {load_time:.2f} 秒")
        # 测试模型训练性能
        start_time = time.time()
        error_case_learner._train_model()
        train_time = time.time() - start_time
        logger.info(f"模型训练时间: {train_time:.2f} 秒")

        # 测试预测性能
        test_error = "文件不存在: test_file.txt"
        start_time = time.time()
        for _ in range(10):
        predict_time = (time.time() - start_time) / 10
        logger.info(f"平均预测时间: {predict_time:.4f} 秒")

        logger.info("系统性能测试通过")
        return True
    except Exception as e:
        logger.error(f"测试系统性能失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始异常处理案例系统集成测试...")
    # 测试各个组件
        ("异常处理案例收集器", test_error_case_collector),
        ("异常处理案例学习器", test_error_case_learner),
        ("集成功能", test_integration),
    ]
    results = []
        logger.info(f"测试: {test_name}")
        results.append((test_name, result))
        logger.info(f"测试结果: {'通过' if result else '失败'}")
        logger.info("-" * 50)

    # 总结测试结果
    passed = sum(1 for _, result in results if result)
    total = len(results)

    logger.info("测试结果总结:")
    logger.info(f"通过: {passed}/{total}")

    for test_name, result in results:
        logger.info(f"{test_name}: {'通过' if result else '失败'}")

    if passed == total:
        logger.info("所有测试通过！异常处理案例系统功能正常")
        return 0
        logger.error("部分测试失败，系统需要进一步优化")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
