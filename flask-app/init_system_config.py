#!/usr/bin/env python3
"""
初始化系统配置表并添加默认配置

from app.models.system_config import SystemConfig, SystemConfigManager
from app.utils.logging import logger

def main():
    """主函数"""
    logger.info("开始初始化系统配置表...")

    try:
        # 创建系统配置表
        logger.info("创建系统配置表...")
        success = SystemConfig.create_table()
        if success:
            logger.info("系统配置表创建成功")
        else:
            logger.error("系统配置表创建失败")
            return 1

        # 初始化默认配置
        logger.info("初始化默认配置...")
        SystemConfigManager.init_default_configs()
        logger.info("默认配置初始化成功")

        # 测试配置加载
        logger.info("测试配置加载...")
        app_name = SystemConfigManager.get_config('app_name')
        app_version = SystemConfigManager.get_config('app_version')
        app_port = SystemConfigManager.get_config('app_port')
        debug_mode = SystemConfigManager.get_config('debug_mode')

        logger.info(f"应用名称: {app_name}")
        logger.info(f"应用版本: {app_version}")
        logger.info(f"应用端口: {app_port}")
        logger.info(f"调试模式: {debug_mode}")

        logger.info("系统配置表初始化完成")
        return 0
    except Exception as e:
        logger.error(f"初始化系统配置表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
if __name__ == "__main__":
    import sys
    sys.exit(main())
