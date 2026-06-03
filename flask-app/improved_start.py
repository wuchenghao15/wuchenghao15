# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
改进的启动脚本,先启动Flask服务器,再后台初始化AI组件
"""

import os
import sys
import time
import logging
import threading

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('improved_startup.log'),
                              logging.StreamHandler()])
logger = logging.getLogger('Improved_Startup')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_ai_components():
    """在后台初始化AI组件"""
    try:
        logger.info("=== 开始后台初始化AI组件 ===")

        time.sleep(2)

        logger.info("1. 初始化AI Cluster Manager...")
        try:
            from ai_cluster_manager import AIClusterManager
            ai_cluster_manager = AIClusterManager()
            logger.info("AI Cluster Manager 初始化完成")
        except Exception as e:
            logger.warning(f"AI Cluster Manager 初始化失败: {str(e)}")

        logger.info("2. 初始化AI Service Manager...")
        try:
            from ai_service import ai_service_manager
            logger.info("AI Service Manager 初始化完成")
        except Exception as e:
            logger.warning(f"AI Service Manager 初始化失败: {str(e)}")

        logger.info("3. 初始化AI Learning System...")
        try:
            from ai_learning_system import AILearningSystem
            ai_learning_system = AILearningSystem(ai_service_manager)
            logger.info("AI Learning System 初始化完成")
        except Exception as e:
            logger.warning(f"AI Learning System 初始化失败: {str(e)}")

        logger.info("=== AI组件后台初始化完成 ===")
        print("\n[INFO] AI组件后台初始化完成")
    except Exception as e:
        logger.error(f"AI组件初始化失败: {str(e)}")
        print(f"\n[ERROR] AI组件初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()

def startup():
    """Startup the AI Cluster System"""
    logger.info("=== 启动MTSCOS AI Cluster System ===")

    logger.info("0. 初始化数据库...")
    try:
        from app import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {str(e)}")

    logger.info("1. 创建Flask应用...")
    from app import app

    logger.info("2. 启动AI组件后台初始化线程...")
    ai_init_thread = threading.Thread(target=initialize_ai_components, daemon=True)
    ai_init_thread.start()

    logger.info("3. 启动Flask服务器...")
    print("\n == MTSCOS AI Cluster System ===")
    print(f"访问API端点: http://localhost:8888/api")
    print(f"- 健康检查: http://localhost:8888/api/health")
    print(f"- 集群信息: http://localhost:8888/api/clusters")
    print(f"- 员工信息: http://localhost:8888/api/employees")
    print(f"- 全局升级: http://localhost:8888/api/ai/global-upgrade")
    print("\n按 Ctrl+C 停止服务器\n")

    try:
        app.run(host='0.0.0.0', port=8888, debug=False)
    except KeyboardInterrupt:
        logger.info("收到关闭信号 - 停止服务器...")
        print("\n == 关闭MTSCOS AI Cluster System ===")
        return
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        raise

if __name__ == '__main__':
    startup()
