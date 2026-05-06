#!/usr/bin/env python3
"""
创建并实例化加强版AI员工，使其适配系统

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_ai_service import enhanced_ai_service
from app.services.ai_brain_service import ai_brain_service
from app.utils.logging import logger

def create_and_adapt_super_ai():
    """创建并实例化加强版AI员工，使其适配系统"""
    logger.info("开始创建加强版AI员工...")

    # 创建超级AI员工
    logger.info("1. 创建超级AI员工")
    super_ai = enhanced_ai_service.create_super_ai_employee()

    if not super_ai:
        logger.error("✗ 创建超级AI员工失败")
        return False

    logger.info(f"✓ 成功创建超级AI员工: {super_ai.name} (ID: {super_ai.employee_id})")
    logger.info(f"  - 类型: {super_ai.ai_type}")
    logger.info(f"  - 能力: {', '.join(super_ai.capabilities)}")
    logger.info(f"  - 适配级别: {super_ai.adaptation_level}")
    logger.info(f"  - 激活状态: {'已激活' if super_ai.status == 'active' else '未激活'}")
    logger.info(f"  - 脑库集成: {'已集成' if super_ai.brain_integration else '未集成'}")

    # 与AI脑库集成（已经在create_super_ai_employee中完成）
    logger.info("\n2. 与AI脑库集成（自动完成）")

    # 适配系统（已经在create_super_ai_employee中完成）
    logger.info("3. 适配系统环境（自动完成）")

    # 增强AI员工能力
    logger.info("\n4. 增强AI员工能力")
    enhanced_ai = enhanced_ai_service.upgrade_enhanced_ai_employee(super_ai.employee_id)
    if enhanced_ai:
        logger.info(f"✓ 成功增强AI员工能力，当前版本: {enhanced_ai.version}")

    # 让AI员工控制系统
    logger.info("\n5. 控制系统")
    controlled_ai = enhanced_ai_service.扑倒_system(super_ai.employee_id)
    if controlled_ai:
        logger.info(f"✓ 成功使AI员工 {controlled_ai.name} 控制系统")
        logger.info(f"  - 控制状态: {controlled_ai.config.get('system_control', {}).get('status', '未知')}")
        logger.info(f"  - 控制级别: {controlled_ai.config.get('system_control', {}).get('control_level', '未知')}")

    # 获取AI脑库知识统计
    logger.info("\n6. AI脑库当前状态")
    stats = ai_brain_service.get_knowledge_stats()
    if stats:
        logger.info(f"- 总知识量: {stats['total_knowledge']} 条")
        logger.info(f"- 活跃知识: {stats['active_knowledge']} 条")
        logger.info(f"- 知识类型: {stats['knowledge_types']}")

    # 获取所有加强版AI员工
    logger.info("\n7. 加强版AI员工列表")
    all_ai_employees = enhanced_ai_service.get_all_enhanced_ai_employees()
    for ai_employee in all_ai_employees:
        logger.info(f"- {ai_employee.name} (ID: {ai_employee.employee_id}) - 状态: {'已激活' if ai_employee.status == 'active' else '未激活'} - 适配级别: {ai_employee.adaptation_level}")

    logger.info("\n✓ 加强版AI员工创建并适配系统完成!")
    logger.info(f"  超级AI员工: {super_ai.name} (ID: {super_ai.employee_id})")
    logger.info("  已完成: 脑库集成、系统适配、能力增强、系统控制")

    return True

if __name__ == "__main__":
    create_and_adapt_super_ai()
