#!/usr/bin/env python3
"""
测试深度自我学习功能

import time
import logging
from app.ai.instances import ai_instance_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_deep_learning_basic():
    """测试深度自我学习基本功能"""
    logger.info("开始测试深度自我学习基本功能...")

    # 创建测试AI实例
    test_instance_id = "test-deep-learning-ai-001"
    test_instance = ai_instance_manager.create_ai_instance(
        instance_id=test_instance_id,
        ai_type="general",
        name="深度学习测试AI",
        description="用于测试深度自我学习功能的AI实例",
        enable_self_learning=True
    )

    if not test_instance:
        logger.error("创建测试AI实例失败")
        return False

    logger.info(f"创建测试AI实例成功: {test_instance_id}")

    # 开始深度自我学习
    start_result = ai_instance_manager.start_deep_learning(test_instance_id)
    if not start_result:
        logger.error("开始深度自我学习失败")
        return False
    logger.info("开始深度自我学习成功")

    # 等待一段时间，让学习过程运行
    logger.info("等待深度自我学习运行...")
    time.sleep(5)

    # 获取学习状态
    learning_status = ai_instance_manager.get_learning_status(test_instance_id)
    logger.info(f"学习状态: {learning_status}")

    if not learning_status.get('is_learning', False):
        logger.error("AI实例未处于学习状态")
        return False
    # 停止深度自我学习
    stop_result = ai_instance_manager.stop_deep_learning(test_instance_id)
    if not stop_result:
        logger.error("停止深度自我学习失败")
        return False
    logger.info("停止深度自我学习成功")

    # 再次获取学习状态，确认已停止
    learning_status_after_stop = ai_instance_manager.get_learning_status(test_instance_id)
    logger.info(f"停止后学习状态: {learning_status_after_stop}")

    if learning_status_after_stop.get('is_learning', True):
        logger.error("AI实例仍处于学习状态，停止失败")
        return False
    logger.info("深度自我学习基本功能测试通过")
    return True


def test_deep_learning_all_instances():
    """测试所有实例的深度自我学习"""
    logger.info("开始测试所有实例的深度自我学习...")

    # 创建多个测试AI实例
    test_instances = []
    for i in range(3):
        instance_id = f"test-deep-learning-ai-{i+101}"
        instance = ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="general",
            description=f"用于测试深度自我学习功能的AI实例 {i+1}",
            enable_self_learning=True
        )
            test_instances.append(instance_id)

    if not test_instances:
        logger.error("创建测试AI实例失败")
        return False

    # 开始所有实例的深度自我学习
    logger.info(f"开始了 {started_count} 个AI实例的深度自我学习")
    if started_count == 0:
        logger.error("没有实例开始深度自我学习")
        return False

    # 等待一段时间
    logger.info("等待所有实例的深度自我学习运行...")
    time.sleep(3)
    # 检查每个实例的学习状态
    for instance_id in test_instances:
        status = ai_instance_manager.get_learning_status(instance_id)
        if status.get('is_learning', False):
            logger.info(f"实例 {instance_id} 正在学习")
        else:
            logger.warning(f"实例 {instance_id} 未处于学习状态")

    # 停止所有实例的深度自我学习
    stopped_count = ai_instance_manager.stop_all_instances_learning()
    logger.info(f"停止了 {stopped_count} 个AI实例的深度自我学习")

    if stopped_count == 0:
        logger.error("没有实例停止深度自我学习")
        return False

    logger.info("所有实例的深度自我学习测试通过")
    return True

def test_deep_learning_integration():
    """测试深度自我学习与其他系统的集成"""
    logger.info("开始测试深度自我学习与其他系统的集成...")

    # 创建一个技术型AI实例
    tech_instance_id = "test-tech-deep-learning-ai-001"
    tech_instance = ai_instance_manager.create_ai_instance(
        instance_id=tech_instance_id,
        ai_type="technical",
        description="用于测试技术型AI的深度自我学习",
        enable_self_learning=True
    )
    if not tech_instance:
        logger.error("创建技术型AI实例失败")

    logger.info(f"创建技术型AI实例成功: {tech_instance_id}")

    # 开始深度自我学习
    start_result = ai_instance_manager.start_deep_learning(tech_instance_id)
    if not start_result:
        return False

    logger.info("开始技术型AI的深度自我学习成功")

    # 模拟一些通信和协作数据，以便AI学习
    for i in range(5):
        # 发送一些测试消息
            from_instance_id=tech_instance_id,
            to_instance_id=tech_instance_id,  # 自己给自己发消息
            message_type="test_message",
            content=f"测试消息 {i+1}: 技术型AI的深度学习测试"

    # 等待学习过程

    learning_status = ai_instance_manager.get_learning_status(tech_instance_id)
    logger.info(f"技术型AI学习状态: {learning_status}")

    # 停止深度自我学习
    stop_result = ai_instance_manager.stop_deep_learning(tech_instance_id)
    if not stop_result:
        logger.error("停止深度自我学习失败")
        return False

    logger.info("停止技术型AI的深度自我学习成功")

    # 检查实例的知识库
    instance = ai_instance_manager.get_ai_instance(tech_instance_id)
    knowledge_count = len(instance.get('knowledge_base', []))
    logger.info(f"技术型AI的知识库大小: {knowledge_count}")
    if knowledge_count > 0:
        logger.info("技术型AI成功生成了新知识")
        logger.warning("技术型AI未生成新知识")

    return True


def main():
    logger.info("开始测试深度自我学习功能...")

    basic_test_passed = test_deep_learning_basic()
    # 测试所有实例
    all_instances_test_passed = test_deep_learning_all_instances()

    # 测试集成
    integration_test_passed = test_deep_learning_integration()

    # 总结测试结果
    total_tests = 3
    passed_tests = sum([basic_test_passed, all_instances_test_passed, integration_test_passed])

    logger.info(f"\n深度自我学习功能测试完成！")
    logger.info(f"测试总数: {total_tests}")
    logger.info(f"通过测试: {passed_tests}")
    logger.info(f"失败测试: {total_tests - passed_tests}")

    if passed_tests == total_tests:
    else:
        logger.warning("部分测试失败，需要进一步检查和修复。")


if __name__ == "__main__":
    main()
