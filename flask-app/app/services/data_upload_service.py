#!/usr/bin/env python3
"""
数据上传服务，用于将本地数据统一上传到数据库并由AI员工处理

import os
# JSON import removed - using database
import time
from app.models import LocalData
from app.utils.logging import logger
from app.ai.user_ai_manager import user_ai_manager

class DataUploadService:
    """数据上传服务，用于将本地数据统一上传到数据库"""

    def __init__(self):
        self.ai_ensemble = None

    def init_ai_ensemble(self):
        """初始化AI集"""
        from app.ai.ai_ensemble import AIEnsemble
        self.ai_ensemble = AIEnsemble()

    def scan_local_data(self, data_dir, data_type):
        """扫描本地数据文件"""
        logger.info(f"开始扫描本地数据目录: {data_dir}，数据类型: {data_type}")

        data_files = []

        if not os.path.exists(data_dir):
            logger.error(f"本地数据目录不存在: {data_dir}")
            return data_files

        try:
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith('.json') or file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        data_files.append({
                            'file_path': file_path,
                            'data_type': data_type,
                            'file_name': file
                        })

            logger.info(f"扫描完成，找到 {len(data_files)} 个数据文件")
            return data_files
            logger.error(f"扫描本地数据失败: {str(e)}")
            return data_files
    def upload_data(self, data_type, content, file_path=None):
        """上传单条数据到数据库"""
        logger.info(f"开始上传数据到数据库，数据类型: {data_type}")

        try:
            # 创建本地数据记录
            local_data = LocalData(
                content=str(content),
                file_path=file_path,
                status="pending"
            )

            # 保存到数据库
            result = local_data.save()
            if result:
                logger.info(f"数据上传成功，数据ID: {local_data._data['id']}")
                return local_data
            else:
                logger.error("数据上传失败")
                return None
        except Exception as e:
            logger.error(f"上传数据到数据库失败: {str(e)}")
            return None

        """上传本地文件到数据库"""
        logger.info(f"开始上传本地文件: {file_path}，数据类型: {data_type}")
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:

            # 上传数据
            return self.upload_data(data_type, content, file_path)
        except Exception as e:
            logger.error(f"上传本地文件 {file_path} 失败: {str(e)}")
            return None

    def upload_local_directory(self, data_dir, data_type):
        logger.info(f"开始上传本地目录: {data_dir}，数据类型: {data_type}")

        # 扫描本地数据文件
        uploaded_count = 0
        failed_count = 0

        for data_file in data_files:
            result = self.upload_local_file(data_file['file_path'], data_type)
            if result:
                uploaded_count += 1
            else:
                failed_count += 1

        logger.info(f"本地目录上传完成，成功: {uploaded_count}，失败: {failed_count}")
        return {
            'uploaded': uploaded_count,
            'failed': failed_count

    def process_uploaded_data(self):
        """处理已上传但未处理的数据"""
        logger.info("开始处理已上传但未处理的数据")

        try:
            # 获取所有待处理的数据
            pending_data = LocalData.find_many("status = ?", ["pending"])

            if not pending_data:
                return {"processed": 0, "pending": 0}

            # 获取可用的AI员工
            if not self.ai_ensemble:
                self.init_ai_ensemble()

            sub_ais = self.ai_ensemble.get_all_sub_ais()
            ai_employees = [ai for ai in sub_ais if ai['status'] == 'active']

            if not ai_employees:
                logger.error("没有可用的AI员工")
                return {"processed": 0, "pending": len(pending_data)}

            # 分配数据给AI员工处理
            processed_count = 0
            for data_item in pending_data:
                # 轮询分配给AI员工
                ai_employee = ai_employees[processed_count % len(ai_employees)]
                ai_employee_id = ai_employee['instance_id']

                # 处理数据
                result = data_item.process_data(ai_employee_id)
                if result:
                    processed_count += 1

                # 避免请求过快
                time.sleep(0.1)

            logger.info(f"数据处理完成，成功处理 {processed_count} 条数据")
            return {
                "pending": len(pending_data) - processed_count
            }
        except Exception as e:
            logger.error(f"处理已上传数据失败: {str(e)}")
            return {"processed": 0, "pending": 0}

    def upload_feature_library(self, feature_library_path):
        """上传特征库到数据库"""

        try:
            # 读取特征库文件
            with open(feature_library_path, 'r', encoding='utf-8') as f:

            # 上传每个特征
            uploaded_count = 0
            for feature in feature_library['features']:
                result = self.upload_data('feature', feature)
                    uploaded_count += 1

            logger.info(f"特征库上传完成，成功上传 {uploaded_count} 个特征")
            return {
                'total': len(feature_library['features']),
                'uploaded': uploaded_count
            }
        except Exception as e:
            logger.error(f"上传特征库失败: {str(e)}")
                'total': 0,
                'uploaded': 0

data_upload_service = DataUploadService()
