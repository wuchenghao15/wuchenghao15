# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
启动用户行为子服务器和相关AI模块
"""

import time
from app.utils.logging import logger
from app.services.distributed_server import distributed_server_manager
from app.services.user_behavior_server import start_user_behavior_server, get_user_behavior_server
from app.ai.user_behavior_ai import get_user_behavior_ai
import logging

def main():
    """主函数"""
    logger.info("启动用户行为子服务器和相关AI模块...")

    try:
        logger.info("启动分布式服务器管理器...")
        distributed_server_manager.start()
        time.sleep(2)

        logger.info("初始化用户行为AI...")
        user_behavior_ai = get_user_behavior_ai()
        if user_behavior_ai:
            logger.info("用户行为AI初始化成功")
        else:
            logger.error("用户行为AI初始化失败")

        logger.info("启动用户行为子服务器...")
        success = start_user_behavior_server()
        if success:
            logger.info("用户行为子服务器启动成功")
        else:
            logger.error("用户行为子服务器启动失败")
            return

        time.sleep(3)

        server = get_user_behavior_server()
        if server:
            status = server.get_status()
            logger.info(f"用户行为子服务器状态: {status}")

        stats = distributed_server_manager.get_distributed_stats()
        logger.info(f"分布式服务器管理器状态: {stats}")

        logger.info("用户行为子服务器和相关AI模块启动完成")

        logger.info("按 Ctrl+C 停止服务器...")
        while True:
            time.sleep(60)
            if server:
                status = server.get_status()
            stats = distributed_server_manager.get_distributed_stats()

    except KeyboardInterrupt:
        logger.info("收到停止信号,正在停止服务器...")
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()
