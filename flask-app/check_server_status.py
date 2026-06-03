# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
检查服务器状态并保存配置到数据库
"""

import os
import sys
import time
import logging
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CHECK_SERVER_STATUS")

from app.config import load_config

def check_server_running():
    """检查服务器是否正在运行"""
    logger.info("开始检查服务器状态...")

    # 加载配置获取服务器参数
    config = load_config()
    host = config.get('SERVER_HOST', '0.0.0.0')
    port = config.get('SERVER_PORT', 8888)
    protocol = config.get('PROTOCOL', 'http')

    # 构建健康检查URL
    if host == '0.0.0.0':
        host = 'localhost'  # 使用localhost进行本地检查
    health_url = f"{protocol}://{host}:{port}/health"

    logger.info(f"检查服务器健康状态: {health_url}")

    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200 and response.text == "OK":
            logger.info("✓ 服务器正在运行并响应正常")
            return True
        else:
            logger.warning(f"✗ 服务器响应异常: 状态码 {response.status_code}, 响应文本: {response.text}")
            return False
    except requests.ConnectionError:
        logger.error(f"✗ 无法连接到服务器: {health_url}")
        return False
    except requests.Timeout:
        logger.error(f"✗ 服务器连接超时: {health_url}")
        return False
    except Exception as e:
        logger.error(f"✗ 检查服务器状态时发生错误: {str(e)}")
        return False

def save_config_and_verify():
    """保存配置到数据库并验证"""
    logger.info("\n开始保存配置到数据库...")

    try:
        os.system("python3 save_config_to_db.py > save_config.log 2>&1")
        logger.info("✓ 配置保存脚本已执行")

        # 查看保存配置的日志
        with open("save_config.log", "r", encoding="utf-8") as f:
            log_content = f.read()
        logger.info(f"配置保存日志:\n{log_content}")

        # 验证服务器配置是否已生效
        logger.info("\n验证服务器配置...")
        config = load_config()

        return True
    except Exception as e:
        logger.error(f"✗ 保存配置和验证过程中发生错误: {str(e)}")
        traceback.print_exc()
        return False

def main():

    # 检查服务器状态
    server_running = check_server_running()

    if not server_running:
        logger.warning("服务器未运行,尝试启动服务器...")
        # 尝试启动服务器
        os.system("python3 start_server.py > server_start.log 2>&1 &")

        # 等待服务器启动
        logger.info("等待5秒后再次检查服务器状态...")
        time.sleep(5)

        # 再次检查服务器状态
        server_running = check_server_running()
        if server_running:
            logger.info("✓ 服务器已成功启动")
        else:
            logger.error("✗ 服务器启动失败,请查看 server_start.log 了解详情")
            with open("server_start.log", "r", encoding="utf-8") as f:
                log_content = f.read()
            sys.exit(1)

    save_config_and_verify()

    logger.info("\n == 操作完成 ===")


if __name__ == "__main__":
    main()
