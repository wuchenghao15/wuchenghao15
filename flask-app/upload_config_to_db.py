#!/usr/bin/env python3
"""
将当前配置上传到数据库
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.models.system_config import SystemConfig
from app.utils.logging import logger


def upload_config_to_db():
    """将当前配置上传到数据库"""
    logger.info("🚀 开始将配置上传到数据库")
    
    try:
        # 确保系统配置表存在
        SystemConfig.create_table()
        
        # 获取当前配置的所有属性
        config_attrs = dir(Config)
        
        # 过滤掉私有属性和方法
        config_attrs = [attr for attr in config_attrs if not attr.startswith('_') and not callable(getattr(Config, attr))]
        
        # 上传每个配置
        uploaded_count = 0
        updated_count = 0
        skipped_count = 0
        
        for attr in config_attrs:
            try:
                value = getattr(Config, attr)
                
                # 确定配置类型
                config_type = get_config_type(value)
                
                # 转换值为字符串
                str_value = convert_to_string(value, config_type)
                
                # 检查配置是否已存在
                existing_config = SystemConfig.get_by_key(attr)
                
                if existing_config:
                    # 更新现有配置
                    existing_config.config_value = str_value
                    existing_config.config_type = config_type
                    existing_config.save()
                    updated_count += 1
                    logger.debug(f"✏️  更新配置: {attr} -> {value}")
                else:
                    # 创建新配置
                    new_config = SystemConfig(
                        config_key=attr,
                        config_value=str_value,
                        config_type=config_type,
                        description=f"自动上传的配置: {attr}"
                    )
                    new_config.save()
                    uploaded_count += 1
                    logger.debug(f"📤 上传配置: {attr} -> {value}")
                    
            except Exception as e:
                logger.warning(f"⚠️  处理配置 {attr} 失败: {str(e)}")
                skipped_count += 1
        
        logger.info(f"🎉 配置上传完成！")
        logger.info(f"📊 结果: 新增 {uploaded_count} 个，更新 {updated_count} 个，跳过 {skipped_count} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置上传失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_config_type(value):
    """确定配置类型"""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, (dict, list)):
        return "json"
    else:
        return "string"


def convert_to_string(value, config_type):
    """将值转换为字符串"""
    if config_type == "json":
        return json.dumps(value, ensure_ascii=False, indent=None)
    else:
        return str(value)


if __name__ == "__main__":
    upload_config_to_db()
