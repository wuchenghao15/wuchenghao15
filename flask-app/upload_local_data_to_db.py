#!/usr/bin/env python3
"""
本地数据统一上传脚本
用于将本地数据上传到数据库并由AI员工收集整理和处理

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/data_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from app.services.data_upload_service import data_upload_service
from app.config import Config


def main():
    """主函数，执行本地数据统一上传和处理"""
    logger.info("🚀 开始执行本地数据统一上传任务")

    try:
        # 1. 定义需要上传的本地数据目录
        data_dirs = [
            # 特征库目录
            os.path.join(Config.DATA_DIR, 'features'),
            # 日志目录
            os.path.join(Config.LOGS_DIR),
            # 配置目录
            os.path.join(Config.INSTANCE_DIR)
        ]
        # 2. 上传每个目录的数据
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                data_type = os.path.basename(data_dir)
                logger.info(f"📁 开始上传目录: {data_dir}，数据类型: {data_type}")

                # 上传目录下的所有数据文件
                result = data_upload_service.upload_local_directory(data_dir, data_type)
                logger.info(f"📊 目录上传结果: {result['uploaded']}/{result['total']} 成功")
            else:
                logger.warning(f"⚠️  目录不存在，跳过: {data_dir}")

        # 3. 处理已上传的数据
        logger.info("🤖 开始处理已上传的数据")
        process_result = data_upload_service.process_uploaded_data()
        logger.info(f"📊 数据处理结果: 成功处理 {process_result['processed']} 条数据，剩余 {process_result['pending']} 条待处理")

        # 4. 上传特征库（如果有）
        feature_lib_path = os.path.join(Config.DATA_DIR, 'feature_library.json')
        if os.path.exists(feature_lib_path):
            logger.info(f"📚 开始上传特征库: {feature_lib_path}")
            feature_result = data_upload_service.upload_feature_library(feature_lib_path)
            logger.info(f"📊 特征库上传结果: {feature_result['uploaded']}/{feature_result['total']} 成功")

        logger.info("✅ 本地数据统一上传任务完成")
        return 0

    except Exception as e:
        logger.error(f"❌ 本地数据统一上传任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
