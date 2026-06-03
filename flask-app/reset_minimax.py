# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置 Minimax AI 引擎
"""

import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'reset_minimax_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('reset_minimax')

def reset_minimax_config():
    """重置 Minimax 配置"""
    logger.info("开始重置 Minimax 配置...")

    config_dir = 'app/config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    ai_engine_config = {
        "engines": [
            {
                "name": "minimax",
                "api_key": "your-api-key-here",
                "api_url": "https://api.minimax.chat/v1/text/chatcompletion",
                "enabled": False,
                "timeout": 30
            },
            {
                "name": "local",
                "api_key": "local-dev",
                "api_url": "http://localhost:8000/v1/chat/completions",
                "enabled": False,
                "timeout": 30
            }
        ],
        "retry_attempts": 3,
        "cache_enabled": True
    }

    config_file = os.path.join(config_dir, 'ai_engine_config.json')
    with open(config_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(ai_engine_config, f, ensure_ascii=False, indent=2)

    logger.info(f"重置 Minimax 配置文件: {config_file}")
    logger.info("重置 AI 引擎集成器配置...")

    cache_dirs = ['cache', 'temp']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        logger.info(f"清理缓存文件: {item_path}")
            except Exception as e:
                logger.error(f"清理缓存失败: {str(e)}")

    logger.info("Minimax 配置重置完成")

def restart_ai_engine():
    """重启 AI 引擎服务"""
    logger.info("开始重启 AI 引擎服务...")

    try:
        from app.ai.ai_engine_integrator import ai_engine_integrator

        minimax_config = {
            "endpoint": "https://api.minimax.chat/v1/text/chatcompletion",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60,
            "retry_count": 3,
            "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "summarization", "text-classification"],
            "top_p": 0.9,
            "top_k": 50
        }

        ai_engine_integrator.configure_engine('minimax', minimax_config)
        logger.info("重置 Minimax 引擎配置成功")
        logger.info("AI 引擎服务重启完成")

    except Exception as e:
        logger.error(f"重启 AI 引擎服务失败: {str(e)}")
        import traceback
        traceback.print_exc()

def verify_minimax_status():
    """验证 Minimax 状态"""
    logger.info("验证 Minimax 状态...")

    try:
        from app.ai.ai_engine_integrator import ai_engine_integrator

        minimax_config = ai_engine_integrator.get_engine_config('minimax')
        if minimax_config:
            logger.info(f"Minimax 引擎配置: {minimax_config}")
        else:
            logger.warning("无法获取 Minimax 引擎配置")

        health_status = ai_engine_integrator.health_status.get('minimax')
        if health_status:
            logger.info(f"Minimax 健康状态: {health_status}")
        else:
            logger.warning("无法获取 Minimax 健康状态")

        performance_data = ai_engine_integrator.engine_performance.get('minimax')
        if performance_data:
            logger.info(f"Minimax 性能数据: {performance_data}")
        else:
            logger.warning("无法获取 Minimax 性能数据")

    except Exception as e:
        logger.error(f"验证 Minimax 状态失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    logger.info("=== 开始重置 Minimax ===")

    try:
        reset_minimax_config()
        restart_ai_engine()
        verify_minimax_status()

        logger.info("=== Minimax 重置完成 ===")
        logger.info("Minimax 已成功重置,现在可以重新配置和使用")

    except Exception as e:
        logger.error(f"重置 Minimax 失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
