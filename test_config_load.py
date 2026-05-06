#!/usr/bin/env python3
"""
测试系统启动时从数据库加载配置的功能

import os
import sys
import logging

# 添加flask-app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-app'))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_load():
    测试系统启动时从数据库加载配置的功能
    logger.info("开始测试系统配置加载功能...")
    try:
        # 导入配置加载函数
        from app.config import load_config

        # 加载配置
        config = load_config()
        logger.info(f"配置加载成功，环境: {config.get('ENV', 'development')}")

        # 打印关键配置项
        logger.info(f"应用名称: {config.get('APP_NAME', '未设置')}")
        logger.info(f"应用版本: {config.get('VERSION', '未设置')}")
        logger.info(f"应用端口: {config.get('SERVER_PORT', '未设置')}")
        logger.info(f"调试模式: {config.get('DEBUG', '未设置')}")
        logger.info(f"AI模型类型: {config.get('AI_MODEL_TYPE', '未设置')}")

        # 验证配置是否从数据库加载
        if 'APP_NAME' in config:
            logger.info("配置已从数据库加载成功！")
        else:
            logger.warning("配置可能未从数据库加载，使用了默认值")

        # 测试配置缓存
        logger.info("测试配置缓存...")
        from app.config import ConfigManager
        ConfigManager.clear_cache()
        logger.info("配置缓存已清空")

        # 再次加载配置
        config2 = load_config()
        logger.info("再次加载配置成功")

        # 验证两次加载的配置是否一致
        if config.get('APP_NAME') == config2.get('APP_NAME'):
            logger.info("配置加载一致性验证成功")
        else:
            logger.warning("配置加载一致性验证失败")

        return True
    except Exception as e:
        logger.error(f"测试配置加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    测试数据库连接
    logger.info("测试数据库连接...")

    try:
        import sqlite3
        conn = sqlite3.connect('flask-app/app.db')
        cursor = conn.cursor()

        # 检查system_config表是否存在
        result = cursor.fetchone()

        if result:
            logger.info("system_config表存在")

            # 检查配置项数量
            cursor.execute("SELECT COUNT(*) FROM system_config")
            count = cursor.fetchone()[0]
            logger.info(f"system_config表中有 {count} 个配置项")

            # 检查表结构
            cursor.execute("PRAGMA table_info(system_config)")
            columns = cursor.fetchall()
            logger.info(f"表结构: {[col[1] for col in columns]}")

            # 检查部分配置项
            cursor.execute("SELECT config_key, config_value FROM system_config LIMIT 5")
            sample_configs = cursor.fetchall()
            logger.info(f"示例配置项: {sample_configs}")
        else:
            logger.warning("system_config表不存在")

        conn.close()
        return True
    except Exception as e:
        logger.error(f"测试数据库连接失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    主函数

    # 测试数据库连接

    config_test = test_config_load()
        logger.info("所有测试通过！系统配置加载功能正常")
        return 0
    else:
        logger.error("测试失败！系统配置加载功能存在问题")
        return 1

if __name__ == '__main__':
    sys.exit(main())

"""