# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI ChatGPT AI引擎实现
支持GPT-3.5、GPT-4等模型
"""

import json
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai 未安装，ChatGPT引擎功能受限")


class ChatGPTEngine:
    """OpenAI ChatGPT AI引擎实现"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url')
        self.model_name = self.config.get('model', 'gpt-3.5-turbo')
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
            "multilingual",
            "function-calling"
        ]
        
        self.supported_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-0613",
            "gpt-4-32k",
            "gpt-4o",
            "gpt-4o-mini"
        ]
        
        if self.api_key and OPENAI_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """初始化ChatGPT客户端"""
        try:
            openai.api_key = self.api_key
            if self.base_url:
                openai.base_url = self.base_url
            self._initialized = True
            logger.info(f"ChatGPT引擎初始化成功，模型: {self.model_name}")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"ChatGPT引擎初始化失败: {str(e)}")
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
                logger.warning(f"ChatGPT引擎调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)
        
        self._last_error = str(last_exception)
        logger.error(f"ChatGPT引擎调用最终失败: {str(last_exception)}")
        return self._create_error_response(str(last_exception))
    
    def _generate(self, prompt: str, **kwargs) -> Dict:
        """生成响应"""
        if not self._initialized:
            if self.api_key and OPENAI_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("ChatGPT引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": response.choices[0].message['content'],
                    "model": self.model_name,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
        
        except Exception as e:
            raise e
    
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
            if self.api_key and OPENAI_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("ChatGPT引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": response.choices[0].message['content'],
                    "model": self.model_name,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"ChatGPT聊天模式失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def generate_stream(self, prompt: str, **kwargs):
        """流式生成响应"""
        if not self._initialized:
            if self.api_key and OPENAI_AVAILABLE:
                self._initialize()
            else:
                yield self._create_error_response("ChatGPT引擎未初始化")
                return
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                timeout=self.timeout
            )
            
            for chunk in response:
                if 'choices' in chunk and chunk['choices']:
                    delta = chunk['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    finish_reason = chunk['choices'][0].get('finish_reason')
                    
                    yield {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "response": content,
                            "model": self.model_name,
                            "is_finished": finish_reason is not None
                        }
                    }
        
        except Exception as e:
            logger.error(f"ChatGPT流式生成失败: {str(e)}")
            yield self._create_error_response(str(e))
    
    def function_call(self, messages: List[Dict], functions: List[Dict], **kwargs) -> Dict:
        """函数调用模式"""
        if not self._initialized:
            if self.api_key and OPENAI_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("ChatGPT引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            message = response.choices[0].message
            
            if 'function_call' in message:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "response": "",
                        "function_call": {
                            "name": message['function_call']['name'],
                            "arguments": json.loads(message['function_call']['arguments'])
                        },
                        "model": self.model_name,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    }
                }
            else:
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "response": message['content'],
                        "model": self.model_name,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    }
                }
        
        except Exception as e:
            logger.error(f"ChatGPT函数调用失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def embed(self, text: str, **kwargs) -> Dict:
        """生成文本嵌入"""
        try:
            response = openai.Embedding.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "embedding": response.data[0]['embedding'],
                    "model": "text-embedding-3-small"
                }
            }
        
        except Exception as e:
            logger.error(f"ChatGPT嵌入生成失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def image_generation(self, prompt: str, **kwargs) -> Dict:
        """图像生成（DALL-E）"""
        try:
            size = kwargs.get('size', '1024x1024')
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=size
            )
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "image_url": response.data[0]['url'],
                    "model": "dall-e-2"
                }
            }
        
        except Exception as e:
            logger.error(f"ChatGPT图像生成失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._initialized:
                return False
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10
            )
            return 'choices' in response
        
        except Exception as e:
            logger.error(f"ChatGPT健康检查失败: {str(e)}")
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
        self.api_key = self.config.get('api_key', self.api_key)
        self.base_url = self.config.get('base_url', self.base_url)
        self.model_name = self.config.get('model', self.model_name)
        self.max_tokens = self.config.get('max_tokens', self.max_tokens)
        self.temperature = self.config.get('temperature', self.temperature)
        self.timeout = self.config.get('timeout', self.timeout)
        self.retry_count = self.config.get('retry_count', self.retry_count)
        
        if self.api_key and OPENAI_AVAILABLE:
            self._initialize()


def create_chatgpt_engine(config: Dict = None) -> ChatGPTEngine:
    """创建ChatGPT引擎实例"""
    return ChatGPTEngine(config)


def init_chatgpt_engine(api_key: str, model: str = "gpt-3.5-turbo", base_url: str = None) -> ChatGPTEngine:
    """初始化ChatGPT引擎"""
    config = {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60,
        "retry_count": 3
    }
    return ChatGPTEngine(config)