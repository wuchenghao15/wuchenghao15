#!/usr/bin/env python3
"""
测试优化后的AI系统功能

import time
import logging
from app.ai.instances import ai_instance_manager
from app.services.ai_brain_service import ai_brain_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_ai_instance_creation():
    """测试AI实例创建功能"""
    logger.info("开始测试AI实例创建功能...")

    # 创建不同类型的AI实例
    instance_ids = []

    # 创建教育型AI实例
    edu_instance_id = "test-edu-ai-001"
    edu_instance = ai_instance_manager.create_ai_instance(
        instance_id=edu_instance_id,
        ai_type="education",
        name="教育辅助AI",
        description="用于辅助教学和学习分析的AI",
        auto_load_knowledge=True,
        enable_self_learning=True
    )
    instance_ids.append(edu_instance_id)
    logger.info(f"创建教育型AI实例成功: {edu_instance_id}")

    # 创建技术型AI实例
    tech_instance_id = "test-tech-ai-001"
    tech_instance = ai_instance_manager.create_ai_instance(
        instance_id=tech_instance_id,
        ai_type="technical",
        name="技术支持AI",
        description="用于技术支持和系统维护的AI",
        auto_load_knowledge=True,
    )
    logger.info(f"创建技术型AI实例成功: {tech_instance_id}")
    # 创建研究型AI实例
    research_instance_id = "test-research-ai-001"
    research_instance = ai_instance_manager.create_ai_instance(
        instance_id=research_instance_id,
        ai_type="research",
        name="研究分析AI",
        description="用于数据分析和研究的AI",
        auto_load_knowledge=True,
    )
    instance_ids.append(research_instance_id)

    return instance_ids

def test_ai_communication():
    """测试AI间通信功能"""
    logger.info("开始测试AI间通信功能...")

    # 创建两个测试实例
    sender_id = "test-sender-ai-001"
    receiver_id = "test-receiver-ai-001"

    # 创建发送方实例
    ai_instance_manager.create_ai_instance(
        instance_id=sender_id,
        ai_type="general",
        name="发送方AI",
        description="用于测试通信的发送方AI"
    )

    # 创建接收方实例
    ai_instance_manager.create_ai_instance(
        instance_id=receiver_id,
        name="接收方AI",
        description="用于测试通信的接收方AI"
    )

    # 发送消息
        from_instance_id=sender_id,
        message_type="test_message",
        metadata={"test_key": "test_value"}
    )

    if success:
        logger.info("AI间通信测试成功")
    else:

    return sender_id, receiver_id


def test_ai_collaboration():
    """测试AI间协作功能"""
    logger.info("开始测试AI间协作功能...")

    # 创建两个测试实例
    instance1_id = "test-collab-ai-001"
    instance2_id = "test-collab-ai-002"

    # 创建实例
    ai_instance_manager.create_ai_instance(
        instance_id=instance1_id,
        ai_type="general",
        name="协作AI 1",
        description="用于测试协作的AI 1"

    ai_instance_manager.create_ai_instance(
        instance_id=instance2_id,
        ai_type="general",
        description="用于测试协作的AI 2"

    # 开始协作
    collaboration_id = ai_instance_manager.start_collaboration(
        collaboration_type="knowledge_sharing",
        goal="共享专业知识"

    if collaboration_id:
        logger.info(f"AI间协作测试成功，协作ID: {collaboration_id}")
    else:
    # 共享任务
    task_shared = ai_instance_manager.share_task(
        from_instance_id=instance1_id,
        to_instance_id=instance2_id,
        task_id="test-task-001",
        task_description="完成知识共享任务",
        priority="high"
    )

    if task_shared:
        logger.info("AI间任务共享测试成功")
    else:

    return instance1_id, instance2_id, collaboration_id


def test_ai_brain_sync():
    logger.info("开始测试AI脑库同步功能...")

    # 创建测试实例
    test_instance_id = "test-brain-ai-001"
    test_instance = ai_instance_manager.create_ai_instance(
        instance_id=test_instance_id,
        ai_type="general",
        name="脑库测试AI",
        description="用于测试脑库同步的AI"
    )

    # 同步知识到脑库
    synced = ai_instance_manager.sync_instance_to_brain(test_instance_id)
        logger.info("AI脑库同步测试成功")
    else:
        logger.error("AI脑库同步测试失败")

    # 获取脑库统计信息
    stats = ai_brain_service.get_knowledge_stats()
    if stats:
        logger.info(f"AI脑库统计信息: {stats}")
    else:
        logger.error("获取AI脑库统计信息失败")
    return test_instance_id


def test_auto_knowledge_acquisition():
    """测试自动知识获取功能"""
    logger.info("开始测试自动知识获取功能...")

    # 自动获取知识
    topics = ["人工智能", "机器学习", "深度学习"]
    acquired_count = ai_brain_service.auto_acquire_knowledge(topics, limit=2)

    logger.info(f"自动获取知识测试完成，获取了 {acquired_count} 条知识")

    interactions = [
        {"content": "人工智能是未来的发展方向，机器学习是其重要分支"},
        {"content": "深度学习在计算机视觉领域取得了重大突破"}
    ]
    learned_count = ai_brain_service.self_learn_from_interactions(interactions)


    return acquired_count + learned_count


def test_ai_learning_session():
    """测试AI共同学习系统"""
    logger.info("开始测试AI共同学习系统...")

    # 创建三个测试实例
    instance1_id = "test-learning-ai-001"
    instance2_id = "test-learning-ai-002"
    instance3_id = "test-learning-ai-003"

    # 创建实例
    for instance_id in [instance1_id, instance2_id, instance3_id]:
        ai_instance_manager.create_ai_instance(
            instance_id=instance_id,
            ai_type="general",
            name=f"学习AI {instance_id[-3:]}",
            description=f"用于测试学习会话的AI {instance_id[-3:]}"
        )

    # 开始学习会话
    session_id = ai_instance_manager.start_learning_session(
        instance_ids=[instance1_id, instance2_id, instance3_id],
        learning_goals=["了解最新AI技术", "分享AI应用案例", "讨论未来发展方向"]
    )

    if session_id:
        logger.info(f"学习会话创建成功，会话ID: {session_id}")

            "title": "AI发展趋势",
            "content": "人工智能正在向更智能化、更普及的方向发展",
            "type": "general",
            "tags": ["AI", "趋势", "发展"]
        }
        shared = ai_instance_manager.share_knowledge_in_session(
            session_id=session_id,
            from_instance_id=instance1_id,
            knowledge_item=knowledge_item

        if shared:
            logger.info("知识共享测试成功")
        else:

        # 完成学习会话
        report = ai_instance_manager.complete_learning_session(session_id)
        if report:
            logger.info(f"学习会话完成，报告: {report}")
        else:
            logger.error("学习会话完成测试失败")
    else:
        logger.error("学习会话创建失败")

    return session_id


def test_intelligent_upgrade():
    """测试智能升级功能"""
    logger.info("开始测试智能升级功能...")

    # 创建测试实例
    test_instance_id = "test-upgrade-ai-001"
    ai_instance_manager.create_ai_instance(
        instance_id=test_instance_id,
        ai_type="general",
        name="升级测试AI",
        description="用于测试智能升级的AI"
    )
    ai_instance_manager.update_instance_performance(
        instance_id=test_instance_id,
            'tasks_completed': 150,
            'errors': 10,
            'response_time': 2.5
        }

    upgraded_count = ai_instance_manager.intelligent_upgrade_instances()
    logger.info(f"智能升级测试完成，升级了 {upgraded_count} 个AI实例")
    optimized_count = ai_instance_manager.optimize_instance_resources()
    logger.info(f"资源优化测试完成，优化了 {optimized_count} 个AI实例")

    return upgraded_count + optimized_count


    """主测试函数"""
    logger.info("开始测试优化后的AI系统...")

    # 测试AI实例创建
    instance_ids = test_ai_instance_creation()

    # 测试AI间通信
    sender_id, receiver_id = test_ai_communication()

    # 测试AI间协作

    # 测试AI脑库同步
    brain_test_id = test_ai_brain_sync()
    # 测试自动知识获取
    acquired_knowledge_count = test_auto_knowledge_acquisition()

    # 测试AI共同学习系统
    learning_session_id = test_ai_learning_session()

    # 测试智能升级

    # 获取系统统计信息
    stats = ai_instance_manager.get_instance_stats()
    logger.info(f"系统统计信息: {stats}")

    logger.info("AI系统优化测试完成！")
    logger.info(f"自动获取的知识数量: {acquired_knowledge_count}")
    logger.info(f"升级和优化的实例数量: {upgrade_count}")


if __name__ == "__main__":
    main()
