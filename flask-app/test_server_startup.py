#!/usr/bin/env python3
"""
测试服务器启动 - 验证配置加载和基本功能

import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_loading():
    测试配置加载功能
    logger.info("测试配置加载...")

    try:
        from app.config import load_config

        # 加载配置
        config = load_config()

        # 验证关键配置项
        required_keys = [
            'SERVER_HOST', 'SERVER_PORT', 'PROTOCOL',
            'DATABASE_TYPE', 'DATABASE_PATH',
            'VERSION', 'ENV', 'DEBUG'
        ]

        for key in required_keys:
            if key not in config:
                logger.error(f"配置项缺失: {key}")
                return False
            logger.info(f"配置项 {key}: {config[key]}")

        logger.info("配置加载测试通过")
        return True
    except Exception as e:
        logger.error(f"配置加载测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_db_config_saved():
    logger.info("测试数据库配置保存...")

    try:
        import sqlite3

        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        # 检查system_config表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
        if not cursor.fetchone():
            logger.error("system_config表不存在")
            return False

        # 检查配置项数量
        cursor.execute("SELECT COUNT(*) FROM system_config")
        count = cursor.fetchone()[0]
        logger.info(f"数据库中配置项数量: {count}")
        if count == 0:
            logger.error("数据库中没有配置项")
            return False

        # 检查关键配置项
        key_to_check = 'SERVER_PORT'
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = ?", (key_to_check,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"关键配置项 {key_to_check} 不存在于数据库中")
            return False

        logger.info(f"关键配置项 {key_to_check} 已保存到数据库，值为: {result[0]}")

        conn.close()
        logger.info("数据库配置保存测试通过")
    except Exception as e:
        logger.error(f"数据库配置保存测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_app_import():
    测试应用导入
    logger.info("测试应用导入...")
        from app import app
        logger.info(f"应用路由数量: {len(list(app.url_map.iter_rules()))}")
        return True
        logger.error(f"应用导入失败: {str(e)}")
        return False

def main():
    主函数
    logger.info("开始测试服务器启动配置...")

    # 运行所有测试
    tests = [
        test_config_loading,
    ]

    for test in tests:
        results.append(test())

    passed = sum(results)
    total = len(results)
    logger.info(f"测试完成: {passed}/{total} 测试通过")
    if passed == total:
        logger.info("所有测试通过！服务器配置正确，应该可以正常启动")
        return 0
    else:
        logger.error("部分测试失败，请检查配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())

"""