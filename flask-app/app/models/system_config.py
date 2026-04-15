#!/usr/bin/env python3
"""
系统参数配置模型
"""

from app.models.base_model import BaseModel
from app.utils.db import DatabaseManager

db_manager = DatabaseManager()

class SystemConfig(BaseModel):
    """系统参数配置模型"""
    
    # 表名
    table_name = "system_config"
    
    # 字段定义
    fields = {
        "id": {"type": "INTEGER", "primary_key": True, "auto_increment": True},
        "key": {"type": "VARCHAR(100)", "unique": True, "not_null": True},
        "value": {"type": "TEXT"},  # 使用TEXT类型存储JSON格式的参数值
        "description": {"type": "VARCHAR(255)"},
        "category": {"type": "VARCHAR(50)"},  # 参数类别，如"ai_config", "app_config"等
        "data_type": {"type": "VARCHAR(20)"},  # 参数数据类型，如"string", "number", "boolean", "object", "array"
        "is_active": {"type": "BOOLEAN", "default": True},  # 参数是否启用
        "created_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"},
        "updated_at": {"type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP", "on_update": "CURRENT_TIMESTAMP"}
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @classmethod
    def get_by_key(cls, key):
        """根据键获取参数"""
        configs = cls.filter(where_clause="key = ? AND is_active = ?", where_params=(key, True))
        return configs[0] if configs else None
    
    @classmethod
    def get_by_category(cls, category):
        """根据类别获取参数"""
        return cls.filter(where_clause="category = ? AND is_active = ?", where_params=(category, True))
    
    @classmethod
    def update_value(cls, key, value):
        """更新参数值"""
        config = cls.get_by_key(key)
        if config:
            config.value = value
            config.save()
            return config
        return None
    
    @classmethod
    def delete_by_key(cls, key):
        """根据键删除参数"""
        config = cls.get_by_key(key)
        if config:
            config.is_active = False
            config.save()
            return True
        return False

class SystemConfigManager:
    """系统参数配置管理器"""
    
    @staticmethod
    def init_default_configs():
        """初始化默认系统参数"""
        # AI配置参数
        ai_configs = [
            {
                "key": "ai_model_type",
                "value": "gpt-4o-mini",
                "description": "默认使用的AI模型类型",
                "category": "ai_config",
                "data_type": "string"
            },
            {
                "key": "ai_api_key",
                "value": "",
                "description": "AI API密钥",
                "category": "ai_config",
                "data_type": "string"
            },
            {
                "key": "ai_temperature",
                "value": "0.7",
                "description": "AI生成文本的温度参数",
                "category": "ai_config",
                "data_type": "number"
            },
            {
                "key": "ai_max_tokens",
                "value": "2000",
                "description": "AI生成文本的最大令牌数",
                "category": "ai_config",
                "data_type": "number"
            }
        ]
        
        # 应用配置参数
        app_configs = [
            {
                "key": "app_name",
                "value": "MTSCOS AI Project",
                "description": "应用名称",
                "category": "app_config",
                "data_type": "string"
            },
            {
                "key": "app_version",
                "value": "1.0.0",
                "description": "应用版本",
                "category": "app_config",
                "data_type": "string"
            },
            {
                "key": "app_port",
                "value": "8888",
                "description": "应用默认端口",
                "category": "app_config",
                "data_type": "number"
            },
            {
                "key": "debug_mode",
                "value": "true",
                "description": "调试模式开关",
                "category": "app_config",
                "data_type": "boolean"
            }
        ]
        
        # 题目生成配置参数
        question_configs = [
            {
                "key": "supported_languages",
                "value": '["japanese", "english", "chinese"]',
                "description": "支持的语言列表",
                "category": "question_config",
                "data_type": "array"
            },
            {
                "key": "supported_categories",
                "value": '["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]',
                "description": "支持的题目类别列表",
                "category": "question_config",
                "data_type": "array"
            },
            {
                "key": "supported_question_types",
                "value": '["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]',
                "description": "支持的题目类型列表",
                "category": "question_config",
                "data_type": "array"
            },
            {
                "key": "default_question_count",
                "value": "20",
                "description": "默认题目数量",
                "category": "question_config",
                "data_type": "number"
            },
            {
                "key": "default_user_level",
                "value": "3",
                "description": "默认用户等级",
                "category": "question_config",
                "data_type": "number"
            }
        ]
        
        # 试卷生成配置参数
        paper_configs = [
            {
                "key": "paper_category_ratios",
                "value": '{"placement": {"词汇": 20, "语法": 20, "阅读": 20, "听力": 20, "写作": 10, "翻译": 10}, "diagnostic": {"词汇": 25, "语法": 25, "阅读": 20, "听力": 20, "写作": 5, "翻译": 5}, "comprehensive": {"词汇": 15, "语法": 15, "阅读": 20, "听力": 20, "写作": 15, "口语": 10, "翻译": 5}, "level": {"1": {"词汇": 50, "语法": 30, "阅读": 20}, "2": {"词汇": 50, "语法": 30, "阅读": 20}, "3": {"词汇": 40, "语法": 35, "阅读": 25}, "4": {"词汇": 30, "语法": 30, "阅读": 40}, "5": {"词汇": 30, "语法": 30, "阅读": 40}}}',
                "description": "不同测试类型的题目类别比例配置",
                "category": "paper_config",
                "data_type": "object"
            },
            {
                "key": "paper_difficulty_adjustment",
                "value": '{"max_difficulty_increase": 1, "max_difficulty_decrease": 1}',
                "description": "试卷难度调整配置",
                "category": "paper_config",
                "data_type": "object"
            }
        ]
        
        # 评分配置参数
        scoring_configs = [
            {
                "key": "scoring_criteria",
                "value": '{"short_answer": {"accuracy": 40, "completeness": 30, "clarity": 20, "vocabulary": 10}, "essay": {"content": 30, "structure": 25, "language": 20, "creativity": 15, "format": 10}, "speaking": {"pronunciation": 25, "grammar": 25, "vocabulary": 20, "fluency": 20, "relevance": 10}, "translation": {"accuracy": 40, "fluency": 30, "naturalness": 20, "format": 10}}',
                "description": "AI评分标准配置",
                "category": "scoring_config",
                "data_type": "object"
            }
        ]
        
        # 合并所有配置
        all_configs = ai_configs + app_configs + question_configs + paper_configs + scoring_configs
        
        # 插入或更新配置
        for config in all_configs:
            existing_config = SystemConfig.get_by_key(config["key"])
            if existing_config:
                # 更新现有配置
                existing_config.value = config["value"]
                existing_config.description = config["description"]
                existing_config.category = config["category"]
                existing_config.data_type = config["data_type"]
                existing_config.is_active = True
                existing_config.save()
            else:
                # 插入新配置
                SystemConfig(**config).save()
    
    @staticmethod
    def get_config(key, default=None):
        """获取配置值"""
        import json
        
        config = SystemConfig.get_by_key(key)
        if config:
            value = config.value
            data_type = config.data_type
            
            try:
                if data_type == "number":
                    return float(value)
                elif data_type == "boolean":
                    return value.lower() in ["true", "1", "yes"]
                elif data_type in ["object", "array"]:
                    return json.loads(value)
                else:
                    return value
            except Exception:
                return default
        return default
    
    @staticmethod
    def set_config(key, value, description="", category="general", data_type="string"):
        """设置配置值"""
        import json
        
        # 转换值为字符串
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            data_type = "object" if isinstance(value, dict) else "array"
        elif isinstance(value, bool):
            value = str(value).lower()
            data_type = "boolean"
        elif isinstance(value, (int, float)):
            value = str(value)
            data_type = "number"
        else:
            value = str(value)
            data_type = "string"
        
        # 插入或更新配置
        config = SystemConfig.get_by_key(key)
        if config:
            config.value = value
            config.description = description
            config.category = category
            config.data_type = data_type
            config.is_active = True
            config.save()
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description,
                category=category,
                data_type=data_type
            ).save()
        
        # 清空配置缓存，确保下次加载时获取最新配置
        try:
            from app.config import ConfigManager
            ConfigManager.clear_cache()
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"配置缓存已清空，键: {key}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"清空配置缓存失败: {str(e)}")
        
        return config

# 初始化数据表
if __name__ == "__main__":
    SystemConfig.create_table()
    SystemConfigManager.init_default_configs()
    print("系统参数配置表创建成功，并初始化了默认配置")

# 自动创建表和初始化默认配置
try:
    # 确保表结构正确创建
    SystemConfig.create_table()
    # 初始化默认配置
    SystemConfigManager.init_default_configs()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"系统参数配置表初始化失败: {str(e)}")
    # 尝试重新创建表
    try:
        SystemConfig.create_table()
        SystemConfigManager.init_default_configs()
        logger.info("系统参数配置表重新初始化成功")
    except Exception as e2:
        logger.error(f"系统参数配置表重新初始化失败: {str(e2)}")
