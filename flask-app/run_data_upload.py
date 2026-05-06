#!/usr/bin/env python3
"""
本地数据统一上传和处理脚本
用于将所有本地数据上传到数据库并由AI员工收集整理和处理

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'data_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LocalDataUploader:
    """本地数据上传器"""

    def __init__(self):
        # 导入应用组件（延迟导入，避免过早加载）
        from app.config import Config
        self.config = Config

        # 确保数据目录存在
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        os.makedirs(self.config.LOGS_DIR, exist_ok=True)
        os.makedirs(self.config.INSTANCE_DIR, exist_ok=True)

        # 初始化数据上传服务
        from app.services.data_upload_service import data_upload_service
        self.upload_service = data_upload_service

    def upload_all_local_data(self):
        """上传所有本地数据"""
        logger.info("🚀 开始执行本地数据统一上传任务")

        # 定义需要上传的本地数据目录
        data_dirs = [
            # 特征库目录
            os.path.join(self.config.DATA_DIR, 'features'),
            # 日志目录
            self.config.LOGS_DIR,
            # 配置目录
            self.config.INSTANCE_DIR
        ]
        total_uploaded = 0
        total_files = 0

        # 上传每个目录的数据
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                data_type = os.path.basename(data_dir)
                logger.info(f"📁 开始上传目录: {data_dir}，数据类型: {data_type}")

                # 上传目录下的所有数据文件
                result = self.upload_service.upload_local_directory(data_dir, data_type)
                logger.info(f"📊 目录上传结果: {result['uploaded']}/{result['total']} 成功")

                total_uploaded += result['uploaded']
                total_files += result['total']
            else:
                logger.warning(f"⚠️  目录不存在，跳过: {data_dir}")

        logger.info(f"📊 总上传结果: {total_uploaded}/{total_files} 成功")
        return total_uploaded, total_files

    def process_uploaded_data(self):
        """处理已上传的数据"""
        logger.info("🤖 开始处理已上传的数据")

        process_result = self.upload_service.process_uploaded_data()
        logger.info(f"📊 数据处理结果: 成功处理 {process_result['processed']} 条数据，剩余 {process_result['pending']} 条待处理")

        return process_result

    def run(self):
        """执行完整的上传和处理流程"""
        try:
            # 1. 上传所有本地数据
            uploaded, total = self.upload_all_local_data()

            # 2. 处理已上传的数据
            process_result = self.process_uploaded_data()

            # 3. 上传特征库（如果有）
            feature_lib_path = os.path.join(self.config.DATA_DIR, 'feature_library.json')
            if os.path.exists(feature_lib_path):
                logger.info(f"📚 开始上传特征库: {feature_lib_path}")
                feature_result = self.upload_service.upload_feature_library(feature_lib_path)
                logger.info(f"📊 特征库上传结果: {feature_result['uploaded']}/{feature_result['total']} 成功")

            logger.info("\n🎉 本地数据统一上传和处理任务已完成")
            logger.info(f"📋 总结:")
            logger.info(f"   - 共扫描到 {total} 个数据文件")
            logger.info(f"   - 成功上传 {uploaded} 个文件")
            logger.info(f"   - 成功处理 {process_result['processed']} 条数据")
            logger.info(f"   - 剩余 {process_result['pending']} 条数据待处理")

            return True

        except Exception as e:
            logger.error(f"❌ 任务执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    uploader = LocalDataUploader()
    success = uploader.run()
    sys.exit(0 if success else 1)
