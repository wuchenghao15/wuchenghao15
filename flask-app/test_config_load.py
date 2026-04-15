#!/usr/bin/env python3
"""
测试配置加载功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import load_config, ConfigManager

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST_CONFIG_LOAD")

def test_config_loading():
    """测试配置加载"""
    logger.info("开始测试配置加载功能...")
    
    # 测试1: 加载默认配置
    logger.info("\n1. 测试加载默认配置...")
    config = load_config()
    logger.info(f"✓ 默认配置加载成功，环境: {config.get('ENV')}")
    logger.info(f"  版本: {config.get('VERSION')}")
    logger.info(f"  服务器: {config.get('SERVER_HOST')}:{config.get('SERVER_PORT')}")
    logger.info(f"  协议: {config.get('PROTOCOL')}")
    logger.info(f"  数据库类型: {config.get('DATABASE_TYPE')}")
    
    # 测试2: 加载生产环境配置
    logger.info("\n2. 测试加载生产环境配置...")
    prod_config = load_config('production')
    logger.info(f"✓ 生产环境配置加载成功，环境: {prod_config.get('ENV')}")
    logger.info(f"  DEBUG模式: {prod_config.get('DEBUG')}")
    logger.info(f"  日志级别: {prod_config.get('LOG_LEVEL')}")
    
    # 测试3: 检查配置完整性
    logger.info("\n3. 测试配置完整性...")
    required_configs = [
        'VERSION', 'SERVER_HOST', 'SERVER_PORT', 'PROTOCOL', 
        'DATABASE_TYPE', 'DATABASE_PATH', 'LOG_LEVEL'
    ]
    
    missing_configs = []
    for config_item in required_configs:
        if config_item not in config:
            missing_configs.append(config_item)
    
    if missing_configs:
        logger.error(f"✗ 缺少必要配置: {missing_configs}")
    else:
        logger.info(f"✓ 所有必要配置都已加载")
    
    # 测试4: 检查嵌套配置
    logger.info("\n4. 测试嵌套配置...")
    nested_configs = [
        'NETWORK_CONFIG', 'CHANNEL_CONFIG', 'RULES_CONFIG', 
        'SCRIPT_CONFIG', 'MECHANISM_CONFIG'
    ]
    
    for nested_config in nested_configs:
        if nested_config in config:
            logger.info(f"✓ {nested_config} 嵌套配置加载成功")
        else:
            logger.error(f"✗ {nested_config} 嵌套配置未加载")
    
    # 测试5: 测试从文件加载配置
    logger.info("\n5. 测试从文件加载配置...")
    if os.path.exists('system_config.json'):
        logger.info("✓ 检测到system_config.json文件")
        file_config = ConfigManager._load_config_from_file()
        if file_config:
            logger.info(f"✓ 从文件加载了 {len(file_config)} 个配置项")
        else:
            logger.warning("⚠ 从文件加载配置项为空")
    else:
        logger.error("✗ 未检测到system_config.json文件")
    
    # 测试6: 测试从环境变量加载配置
    logger.info("\n6. 测试从环境变量加载配置...")
    os.environ['TEST_ENV_VAR'] = 'test_value'
    env_config = ConfigManager._load_env_vars()
    if 'TEST_ENV_VAR' in env_config:
        logger.info("✓ 成功从环境变量加载配置")
    else:
        logger.warning("⚠ 从环境变量加载配置失败")
    
    logger.info("\n配置加载测试完成！")

if __name__ == "__main__":
    test_config_loading()
