#!/usr/bin/env python3
"""
启动用户行为子服务器和相关AI模块

import time
from app.utils.logging import logger
from app.services.distributed_server import distributed_server_manager
from app.services.user_behavior_server import start_user_behavior_server, get_user_behavior_server
from app.ai.user_behavior_ai import get_user_behavior_ai

def main():
    """主函数"""
    logger.info("启动用户行为子服务器和相关AI模块...")

    try:
        # 启动分布式服务器管理器
        logger.info("启动分布式服务器管理器...")
        distributed_server_manager.start()
        time.sleep(2)

        # 初始化用户行为AI
        logger.info("初始化用户行为AI...")
        user_behavior_ai = get_user_behavior_ai()
        if user_behavior_ai:
            logger.info("用户行为AI初始化成功")
        else:
            logger.error("用户行为AI初始化失败")

        # 启动用户行为子服务器
        logger.info("启动用户行为子服务器...")
        success = start_user_behavior_server()
        if success:
            logger.info("用户行为子服务器启动成功")
        else:

        # 等待一段时间，让服务器完全启动
        time.sleep(3)

        # 检查服务器状态
        server = get_user_behavior_server()
        if server:
            status = server.get_status()
            logger.info(f"用户行为子服务器状态: {status}")

        # 检查分布式服务器管理器状态
        stats = distributed_server_manager.get_distributed_stats()
        logger.info(f"分布式服务器管理器状态: {stats}")

        logger.info("用户行为子服务器和相关AI模块启动完成")

        # 保持脚本运行，以便观察服务器状态
        logger.info("按 Ctrl+C 停止服务器...")
        while True:
            time.sleep(60)
            # 定期检查服务器状态
            if server:
                status = server.get_status()
            stats = distributed_server_manager.get_distributed_stats()

    except KeyboardInterrupt:
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()
