# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云千问AI引擎实现
支持Qwen-7B、Qwen-14B、Qwen-72B等模型
"""

import json
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning("dashscope 未安装，千问引擎功能受限")


class QianwenEngine:
    """阿里云千问AI引擎实现"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key') or self.config.get('access_key_id')
        self.secret_key = self.config.get('secret_key') or self.config.get('access_key_secret')
        self.model_name = self.config.get('model', 'qwen-turbo')
        self.max_tokens = self.config.get('max_tokens', 4096)
        self.temperature = self.config.get('temperature', 0.7)
        self.timeout = self.config.get('timeout', 60)
        self.retry_count = self.config.get('retry_count', 3)
        
        self._initialized = False
        self._last_error = None
        
        self.supported_features = [
            "text-generation",
            "chatbot",
            "question-answering",
            "translation",
            "creative-writing",
            "code-generation",
            "summarization",
            "reasoning",
            "multilingual"
        ]
        
        self.supported_models = [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-0428",
            "qwen-7b-chat",
            "qwen-14b-chat",
            "qwen-72b-chat"
        ]
        
        if self.api_key and DASHSCOPE_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """初始化千问客户端"""
        try:
            dashscope.api_key = self.api_key
            self._initialized = True
            logger.info(f"千问引擎初始化成功，模型: {self.model_name}")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"千问引擎初始化失败: {str(e)}")
            self._initialized = False
    
    def is_initialized(self) -> bool:
        """检查引擎是否已初始化"""
        return self._initialized
    
    def _generate_with_retry(self, prompt: str, **kwargs) -> Dict:
        """带重试的生成方法"""
        last_exception = None
        
        for attempt in range(self.retry_count):
            try:
                return self._generate(prompt, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"千问引擎调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
        
        self._last_error = str(last_exception)
        logger.error(f"千问引擎调用最终失败: {str(last_exception)}")
        return self._create_error_response(str(last_exception))
    
    def _generate(self, prompt: str, **kwargs) -> Dict:
        """生成响应"""
        if not self._initialized:
            if self.api_key and DASHSCOPE_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("千问引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            response = dashscope.Generation.call(
                model=self.model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "response": response.output.text,
                        "model": self.model_name,
                        "usage": self._extract_usage(response)
                    }
                }
            else:
                return self._create_error_response(f"API错误: {response.message}")
        
        except Exception as e:
            raise e
    
    def _extract_usage(self, response) -> Dict:
        """提取使用信息"""
        usage = {}
        if hasattr(response, 'usage'):
            usage_data = response.usage
            if hasattr(usage_data, 'input_tokens'):
                usage['prompt_tokens'] = usage_data.input_tokens
            if hasattr(usage_data, 'output_tokens'):
                usage['completion_tokens'] = usage_data.output_tokens
            if hasattr(usage_data, 'total_tokens'):
                usage['total_tokens'] = usage_data.total_tokens
        return usage
    
    def _create_error_response(self, error_message: str) -> Dict:
        """创建错误响应"""
        return {
            "code": -1,
            "message": error_message,
            "data": {
                "response": "",
                "model": self.model_name,
                "usage": {}
            }
        }
    
    def generate(self, prompt: str, **kwargs) -> Dict:
        """生成AI响应"""
        return self._generate_with_retry(prompt, **kwargs)
    
    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天模式"""
        if not self._initialized:
            if self.api_key and DASHSCOPE_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("千问引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            response = dashscope.Generation.call(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "response": response.output.text,
                        "model": self.model_name,
                        "usage": self._extract_usage(response)
                    }
                }
            else:
                return self._create_error_response(f"API错误: {response.message}")
        
        except Exception as e:
            logger.error(f"千问聊天模式失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def generate_stream(self, prompt: str, **kwargs):
        """流式生成响应"""
        if not self._initialized:
            if self.api_key and DASHSCOPE_AVAILABLE:
                self._initialize()
            else:
                yield self._create_error_response("千问引擎未初始化")
                return
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            responses = dashscope.Generation.call(
                model=self.model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                timeout=self.timeout
            )
            
            for response in responses:
                if response.status_code == 200:
                    yield {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "response": response.output.text,
                            "model": self.model_name,
                            "is_finished": response.output.finish_reason is not None
                        }
                    }
                else:
                    yield self._create_error_response(f"API错误: {response.message}")
        
        except Exception as e:
            logger.error(f"千问流式生成失败: {str(e)}")
            yield self._create_error_response(str(e))
    
    def embed(self, text: str, **kwargs) -> Dict:
        """生成文本嵌入"""
        try:
            response = dashscope.TextEmbedding.call(
                model=dashscope.TextEmbedding.Models.text_embedding_v1,
                input=text
            )
            
            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "embedding": response.output.embeddings[0]['embedding'],
                        "model": "text-embedding-v1"
                    }
                }
            else:
                return self._create_error_response(f"嵌入API错误: {response.message}")
        
        except Exception as e:
            logger.error(f"千问嵌入生成失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._initialized:
                return False
            
            response = dashscope.Generation.call(
                model=self.model_name,
                prompt="Hello",
                max_tokens=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"千问健康检查失败: {str(e)}")
            return False
    
    def get_supported_features(self) -> List[str]:
        """获取支持的功能列表"""
        return self.supported_features
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.supported_models
    
    def get_config(self) -> Dict:
        """获取配置"""
        return {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "initialized": self._initialized
        }
    
    def update_config(self, config: Dict):
        """更新配置"""
        self.config.update(config)
        self.api_key = self.config.get('api_key', self.api_key) or self.config.get('access_key_id', self.api_key)
        self.secret_key = self.config.get('secret_key', self.secret_key) or self.config.get('access_key_secret', self.secret_key)
        self.model_name = self.config.get('model', self.model_name)
        self.max_tokens = self.config.get('max_tokens', self.max_tokens)
        self.temperature = self.config.get('temperature', self.temperature)
        self.timeout = self.config.get('timeout', self.timeout)
        self.retry_count = self.config.get('retry_count', self.retry_count)
        
        if self.api_key and DASHSCOPE_AVAILABLE:
            self._initialize()


def create_qianwen_engine(config: Dict = None) -> QianwenEngine:
    """创建千问引擎实例"""
    return QianwenEngine(config)


def init_qianwen_engine(api_key: str, model: str = "qwen-turbo") -> QianwenEngine:
    """初始化千问引擎"""
    config = {
        "api_key": api_key,
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60,
        "retry_count": 3
    }
    return QianwenEngine(config)