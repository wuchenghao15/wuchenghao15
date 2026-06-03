# -*- coding: utf-8 -*-
# JSON import removed - using database
from app.models.system_config import SystemConfig
import json
import sys

class APIService:
    """API服务配置和管理"""

    @staticmethod
    def get_api_config():
        """获取API配置"""
        config = {
            'main_port': 8888,
            'api_prefix': '/api',
            'ai_brain_prefix': '/api/ai-brain',
            'api_timeout': 30,
            'api_rate_limit': 100,
            'enable_cors': True
        }

        # 从系统配置中加载API配置
        api_config = SystemConfig.get_by_key('api_config')
        if api_config:
            try:
                config.update(eval(api_config.config_value))
            except json.JSONDecodeError:
                pass

        return config

    def get_ai_brain_endpoints():
        """获取AI脑库API端点列表"""
        config = APIService.get_api_config()
        return [
            f"{config['ai_brain_prefix']}/",
            f"{config['ai_brain_prefix']}/questions",
            f"{config['ai_brain_prefix']}/generate-questions",
            f"{config['ai_brain_prefix']}/exam",
            f"{config['ai_brain_prefix']}/status"
        ]

    def validate_api_request(request):
        """验证API请求"""
        # 这里可以添加请求验证逻辑
        # 如API密钥验证,速率限制等
        return True
