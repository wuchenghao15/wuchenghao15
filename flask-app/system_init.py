# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统初始化脚本
确保系统在启动时从数据库加载配置并初始化AI员工管理
"""
import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'system_init_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemInitializer:
    """系统初始化器"""

    def __init__(self):
        """初始化系统初始化器"""
        self.success = True

    def init_database(self):
        """初始化数据库"""
        logger.info("🗄️  开始数据库初始化")

        try:
            os.makedirs('instance', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
            os.makedirs('data', exist_ok=True)

            from app.models.user import User
            from app.models.system_config import SystemConfig
            from app.models.backup import Backup
            from app.models.logs import LogEntry
            from app.models.user_snapshots import UserSnapshot
            from app.models.ai import AIInstance
            from app.models.local_data import LocalData

            tables = [
                User,
                SystemConfig,
                Backup,
                LogEntry,
                UserSnapshot,
                AIInstance,
                LocalData
            ]
            for model in tables:
                model.create_table()

            logger.info("✅ 数据库初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def init_config(self):
        """初始化配置"""
        logger.info("📁 开始配置初始化")

        try:
            from app.services.config_service import init_config_service
            init_config_service()

            logger.info("✅ 配置初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 配置初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def init_ai_employees(self):
        """初始化AI员工系统"""
        logger.info("🤖 开始AI员工系统初始化")

        try:
            from app.ai.engineer_ai import register_engineer_ai
            register_engineer_ai()

            logger.info("✅ AI员工系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ AI员工系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        """执行完整的系统初始化"""
        logger.info("🚀 开始系统初始化流程")

        try:
            if not self.init_database():
                self.success = False

            if not self.init_config():
                self.success = False

            if not self.init_ai_employees():
                self.success = False

            if self.success:
                logger.info("🎉 系统初始化成功完成!")
                return True
            else:
                logger.error("❌ 系统初始化部分步骤失败")
                return False

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    initializer = SystemInitializer()
    success = initializer.run()
    sys.exit(0 if success else 1)
