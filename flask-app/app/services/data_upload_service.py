#!/usr/bin/env python3
"""
数据上传服务 - 用于将本地数据统一上传到数据库并由AI员工处理
"""
import os
import time
from app.models import LocalData
from app.utils.logging import logger
from app.ai.user_ai_manager import user_ai_manager

class DataUploadService:
    """数据上传服务: 用于将本地数据统一上传到数据库"""

    def __init__(self):
        self.ai_ensemble = None

    def init_ai_ensemble(self):
        """初始化AI集"""
        from app.ai.ai_ensemble import AIEnsemble
        self.ai_ensemble = AIEnsemble()

    def scan_local_data(self, data_dir, data_type):
        """扫描本地数据文件"""
        logger.info(f"开始扫描本地数据目录: {data_dir},数据类型: {data_type}")

        data_files = []

        if not os.path.exists(data_dir):
            logger.error(f"本地数据目录不存在: {data_dir}")
            return data_files

        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                
                data_files.append({
                    'file_path': file_path,
                    'file_name': file,
                    'file_size': file_size,
                    'file_mtime': file_mtime,
                    'data_type': data_type
                })

        logger.info(f"扫描完成,找到 {len(data_files)} 个文件")
        return data_files

    def upload_data(self, data_type, content, file_path=None):
        """上传单条数据到数据库"""
        logger.info(f"开始上传数据到数据库,数据类型: {data_type}")

        try:
            local_data = LocalData(
                content=str(content),
                file_path=file_path,
                status="pending"
            )

            result = local_data.save()
            if result:
                logger.info(f"数据上传成功,数据ID: {local_data._data['id']}")
                return local_data
            else:
                logger.error("数据上传失败")
                return None
        except Exception as e:
            logger.error(f"数据上传失败: {str(e)}")
            return None

    def upload_local_file(self, file_path, data_type):
        """上传单个本地文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.upload_data(data_type, content, file_path)
        except Exception as e:
            logger.error(f"上传本地文件失败 {file_path}: {str(e)}")
            return None

    def upload_local_directory(self, data_dir, data_type):
        """上传本地目录"""
        logger.info(f"开始上传本地目录: {data_dir},数据类型: {data_type}")

        data_files = self.scan_local_data(data_dir, data_type)
        
        uploaded_count = 0
        failed_count = 0

        for data_file in data_files:
            result = self.upload_local_file(data_file['file_path'], data_type)
            if result:
                uploaded_count += 1
            else:
                failed_count += 1

        logger.info(f"本地目录上传完成,成功: {uploaded_count},失败: {failed_count}")
        return {
            'total': len(data_files),
            'uploaded': uploaded_count,
            'failed': failed_count
        }

    def process_uploaded_data(self):
        """处理已上传但未处理的数据"""
        logger.info("开始处理已上传但未处理的数据")

        try:
            pending_data = LocalData.find_many("status = ?", ["pending"])

            if not pending_data:
                logger.info("没有待处理的数据")
                return {"processed": 0, "pending": 0}

            processed_count = 0
            for data in pending_data:
                try:
                    if self.ai_ensemble:
                        self.ai_ensemble.process_data(data)
                    
                    data.status = "processed"
                    data.save()
                    processed_count += 1
                except Exception as e:
                    logger.error(f"处理数据失败 {data.id}: {str(e)}")
                    data.status = "failed"
                    data.save()

            logger.info(f"数据处理完成,已处理: {processed_count}")
            return {"processed": processed_count, "pending": len(pending_data) - processed_count}
        except Exception as e:
            logger.error(f"处理数据失败: {str(e)}")
            return {"processed": 0, "pending": 0}

    def upload_feature_library(self, feature_library_path):
        """上传特征库到数据库"""
        logger.info(f"开始上传特征库: {feature_library_path}")

        try:
            import json
            with open(feature_library_path, 'r', encoding='utf-8') as f:
                feature_library = json.load(f)

            uploaded_count = 0
            for feature in feature_library.get('features', []):
                result = self.upload_data('feature', feature)
                if result:
                    uploaded_count += 1

            logger.info(f"特征库上传完成,成功上传 {uploaded_count} 个特征")
            return {"uploaded": uploaded_count}
        except Exception as e:
            logger.error(f"上传特征库失败: {str(e)}")
            return {"uploaded": 0}

    def get_upload_status(self):
        """获取上传状态"""
        try:
            pending_count = LocalData.count("status = ?", ["pending"])
            processed_count = LocalData.count("status = ?", ["processed"])
            failed_count = LocalData.count("status = ?", ["failed"])
            
            return {
                "pending": pending_count,
                "processed": processed_count,
                "failed": failed_count
            }
        except Exception as e:
            logger.error(f"获取上传状态失败: {str(e)}")
            return {"pending": 0, "processed": 0, "failed": 0}

data_upload_service = DataUploadService()
