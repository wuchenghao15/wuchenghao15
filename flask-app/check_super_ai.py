#!/usr/bin/env python3
"""
检查AI脑库状态和超级AI员工创建情况
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_brain_service import ai_brain_service
from app.services.enhanced_ai_service import enhanced_ai_service
from app.utils.logging import logger

def check_system_status():
    """检查系统状态"""
    logger.info("开始检查系统状态...")
    
    # 检查AI脑库状态
    logger.info("\n1. AI脑库状态")
    stats = ai_brain_service.get_knowledge_stats()
    if stats:
        logger.info(f"- 总知识量: {stats['total_knowledge']} 条")
        logger.info(f"- 活跃知识: {stats['active_knowledge']} 条")
        logger.info(f"- 知识类型: {stats['knowledge_types']}")
        logger.info(f"- 来源统计: {stats['sources']}")
        logger.info(f"- 热门标签: {stats['top_tags']}")
    else:
        logger.error("✗ 获取AI脑库统计失败")
    
    # 检查最近活动
    logger.info("\n2. AI脑库最近活动")
    activities = ai_brain_service.get_recent_activities(limit=10)
    if activities:
        for activity in activities:
            logger.info(f"- {activity.timestamp} - {activity.activity_type}: {activity.description}")
    else:
        logger.info("- 暂无活动记录")
    
    # 检查加强版AI员工
    logger.info("\n3. 加强版AI员工")
    ai_employees = enhanced_ai_service.get_all_enhanced_ai_employees()
    if ai_employees:
        for ai_employee in ai_employees:
            logger.info(f"\n- 名称: {ai_employee.name}")
            logger.info(f"  ID: {ai_employee.employee_id}")
            logger.info(f"  类型: {ai_employee.ai_type}")
            logger.info(f"  状态: {ai_employee.status}")
            logger.info(f"  版本: {ai_employee.version}")
            logger.info(f"  适配级别: {ai_employee.adaptation_level}")
            logger.info(f"  脑库集成: {'是' if ai_employee.brain_integration else '否'}")
            logger.info(f"  能力: {', '.join(ai_employee.capabilities)}")
            logger.info(f"  系统控制: {'是' if ai_employee.config.get('system_control', {}).get('enabled', False) else '否'}")
    else:
        logger.info("- 暂无加强版AI员工")
    
    logger.info("\n✓ 系统状态检查完成!")

if __name__ == "__main__":
    check_system_status()
