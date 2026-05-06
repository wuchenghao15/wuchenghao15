#!/usr/bin/env python3
"""
拓展AI脑库，添加系统控制和AI集管理相关知识

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_brain_service import ai_brain_service
from app.utils.logging import logger

def enhance_ai_brain():
    """拓展AI脑库，添加系统控制和AI集管理相关知识"""
    logger.info("开始拓展AI脑库...")

    # 添加系统控制相关知识
    system_control_knowledge = [
        {
            "title": "系统控制基础",
            "content": "系统控制是指对整个系统进行监控、管理和调整的能力。包括服务器管理、端口配置、进程监控等。",
            "knowledge_type": "experience",
            "source": "system",
            "tags": ["系统控制", "服务器", "管理"],
            "priority": 5
        },
        {
            "content": "AI集统管需要考虑负载均衡、资源分配、故障转移等因素。建议使用线程池管理AI实例，避免资源浪费。",
            "knowledge_type": "experience",
            "source": "system",
            "priority": 5
        {
            "content": "线程管理需要注意避免死锁、资源竞争等问题。建议使用线程池和锁机制，确保线程安全。",
            "source": "system",
            "priority": 4
        },
            "content": "系统适配是指AI员工根据系统环境自动调整自身配置的能力。包括硬件适配、软件适配、网络适配等。",
            "knowledge_type": "experience",
            "source": "system",
            "tags": ["系统适配", "配置", "调整"],
            "priority": 4
            "content": "AI员工与AI脑库集成需要考虑数据同步、知识共享、权限管理等因素。建议使用定时同步机制，确保数据一致性。",
            "source": "system",
            "tags": ["AI脑库", "集成", "同步"],
            "priority": 5
        },
        {
            "content": "系统安全控制包括访问权限管理、数据加密、漏洞扫描等。建议使用最小权限原则，确保系统安全。",
            "tags": ["系统安全", "权限管理", "加密"],
        },
        {
            "content": "AI员工性能优化包括算法优化、资源分配优化、缓存策略优化等。建议定期进行性能测试，根据测试结果调整配置。",
            "source": "system",
            "priority": 3
        {
            "content": "故障诊断与修复包括日志分析、异常检测、自动修复等。建议使用监控系统实时监控AI员工状态，发现问题及时处理。",
            "source": "system",
            "tags": ["故障诊断", "日志分析", "自动修复"],
    ]

    # 添加AI集管理相关知识
            "knowledge_type": "experience",
            "source": "system",
            "priority": 5
        },
        {
            "content": "AI集调度策略包括负载均衡、任务分配、优先级调度等。建议根据任务类型和AI员工能力动态调整调度策略。",
            "source": "system",
            "priority": 4
        },
        {
            "content": "AI集通信机制包括同步通信和异步通信。建议使用消息队列实现异步通信，提高系统吞吐量。",
            "knowledge_type": "experience",
            "tags": ["AI集通信", "消息队列", "异步通信"],
        }
    ]

    # 添加所有知识到AI脑库
    all_knowledge = system_control_knowledge + ai_ensemble_knowledge
    added_count = 0
            # 检查是否已存在
                keyword=knowledge_item["title"],
                knowledge_type=knowledge_item["knowledge_type"]
            )

                result = ai_brain_service.add_knowledge(
                    title=knowledge_item["title"],
                    content=knowledge_item["content"],
                    knowledge_type=knowledge_item["knowledge_type"],
                    source=knowledge_item["source"],
                    tags=knowledge_item["tags"],
                    priority=knowledge_item["priority"]

                if result:
                    added_count += 1
                    logger.info(f"✓ 添加知识: {knowledge_item['title']}")
                else:
                    logger.error(f"✗ 添加知识失败: {knowledge_item['title']}")
            else:
        except Exception as e:
            logger.error(f"✗ 添加知识失败 {knowledge_item['title']}: {str(e)}")

    # 批量增强知识
    enhanced_count = ai_brain_service.batch_enhance_knowledge()

    logger.info(f"\nAI脑库拓展完成!")
    logger.info(f"- 增强现有知识: {enhanced_count} 条")

    # 获取知识统计
    stats = ai_brain_service.get_knowledge_stats()
        logger.info(f"\nAI脑库当前状态:")
        logger.info(f"- 活跃知识: {stats['active_knowledge']} 条")
        logger.info(f"- 知识类型: {stats['knowledge_types']}")
        logger.info(f"- 标签统计: {stats['top_tags']}")

if __name__ == "__main__":
    enhance_ai_brain()
