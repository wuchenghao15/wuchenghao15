#!/usr/bin/env python3
"""
测试AI实例化和规则约束

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.instances import ai_instance_manager
from app.ai.rule_manager import rule_manager_ai
from app.services.rule_management import rule_management_service

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST_AI_INSTANTIATION")

def test_ai_management_rules():
    """测试AI管理规则"""
    logger.info("开始测试AI管理规则...")

    # 获取AI管理规则
    ai_management_rules = rule_management_service.get_rules("ai_management_rules")

    logger.info(f"AI管理规则: {ai_management_rules}")

    # 检查必要的规则是否存在
    required_rule_categories = [
        "ai_instance_management",
        "ai_security",
        "ai_performance",
        "ai_decision_rules",
        "ai_permission_rules",
        "ai_constraint_rules"
    ]

    missing_rules = []
    for rule_category in required_rule_categories:
        if rule_category not in ai_management_rules:
            missing_rules.append(rule_category)

    if missing_rules:
        logger.error(f"缺少必要的AI管理规则: {missing_rules}")
        return False
    else:
        logger.info("所有必要的AI管理规则都已存在")
        return True

def test_ai_instance_creation_with_permissions():
    """测试带有权限检查的AI实例创建"""
    logger.info("\n开始测试带有权限检查的AI实例创建...")

    # 测试1: 使用admin角色创建AI实例
    logger.info("\n测试1: 使用admin角色创建AI实例...")
    ai_instance = ai_instance_manager.create_ai_instance(
        instance_id="test-ai-instance-001",
        ai_type="general",
        name="测试AI实例",
        description="用于测试AI实例化和规则约束的AI实例",
        functions=["general_assistant", "content_generation"],
        responsibilities=["提供一般协助", "生成内容"],
        config={"version": "1.0.0"},
        user_role="admin"
    )

    if ai_instance:
        logger.info(f"✓ 成功创建AI实例: {ai_instance['instance_id']}")
        logger.info(f"  权限: {ai_instance.get('permissions', [])}")
        logger.info(f"  决策规则: {ai_instance.get('decision_rules', {})}")
    else:

    # 测试2: 使用guest角色创建AI实例（应该失败，因为guest没有创建实例的权限）
    logger.info("\n测试2: 使用guest角色创建AI实例...")
    ai_instance_guest = ai_instance_manager.create_ai_instance(
        instance_id="test-ai-instance-002",
        ai_type="general",
        name="测试AI实例-访客",
        functions=["general_assistant"],
        user_role="guest"
    )

    if not ai_instance_guest:
    else:

    # 测试3: 测试功能约束
    logger.info("\n测试3: 测试功能约束...")
    ai_instance_technical = ai_instance_manager.create_ai_instance(
        instance_id="test-ai-instance-003",
        ai_type="technical",
        name="测试技术AI实例",
        description="用于测试功能约束的技术AI实例",
        functions=["hardware_management", "system_monitoring"],
        user_role="admin"
    )

    if ai_instance_technical:
        logger.info(f"  功能: {ai_instance_technical['functions']}")

    # 测试4: 测试规则执行权限
    logger.info("\n测试4: 测试规则执行权限...")
    # 使用admin角色执行规则
    result_admin = rule_manager_ai.execute_rule(
        "test_rules",
        "test_generator",
        user_role="admin"
    )

    if result_admin:
        logger.info(f"✓ 管理员成功执行规则")

    # 使用guest角色执行规则（应该失败）
        "test_rules",
        "test_generator",
        user_role="guest"
    )

    if not result_guest:
        logger.info(f"✓ 访客执行规则被拒绝（权限不足）")
    else:

def test_ai_instance_audit_log():
    """测试AI实例审计日志"""
    # 获取AI实例
    if ai_instance:
        audit_log = ai_instance.get("audit_log", [])
        if audit_log:
            logger.info(f"✓ AI实例审计日志存在: {audit_log}")
        else:
    else:

def cleanup_test_instances():
    """清理测试实例"""
    logger.info("\n开始清理测试实例...")

    test_instance_ids = [
        "test-ai-instance-001",
        "test-ai-instance-003"
    ]
    for instance_id in test_instance_ids:
        try:
            # 从内存中删除实例
            if instance_id in ai_instance_manager.ai_instances:
                del ai_instance_manager.ai_instances[instance_id]
                ai_instance_manager.instance_count -= 1
                logger.info(f"✓ 成功从内存中删除测试实例: {instance_id}")

            # 从数据库中删除实例
            from app.models.ai import AIInstance
            db_instance = AIInstance.get_by_id(instance_id)
            if db_instance:
                db_instance.delete()
                logger.info(f"✓ 成功从数据库中删除测试实例: {instance_id}")
        except Exception as e:
            logger.error(f"✗ 删除测试实例 {instance_id} 失败: {str(e)}")

if __name__ == "__main__":
    # 测试AI管理规则
    test_ai_management_rules()

    # 测试AI实例创建和权限检查
    test_ai_instance_creation_with_permissions()

    # 测试AI实例审计日志
    test_ai_instance_audit_log()

    # 清理测试实例
    cleanup_test_instances()

    logger.info("\nAI实例化和规则约束测试完成！")
