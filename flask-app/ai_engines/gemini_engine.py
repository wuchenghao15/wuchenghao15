# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Gemini AI引擎实现
支持Gemini Pro、Gemini Pro Vision等模型
"""

import json
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai 未安装，Gemini引擎功能受限")


class GeminiEngine:
    """Google Gemini AI引擎实现"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.model_name = self.config.get('model', 'gemini-pro')
        self.max_tokens = self.config.get('max_tokens', 8192)
        self.temperature = self.config.get('temperature', 0.7)
        self.timeout = self.config.get('timeout', 60)
        self.retry_count = self.config.get('retry_count', 3)
        
        self._client = None
        self._model = None
        self._initialized = False
        self._last_error = None
        
        self.supported_features = [
            "text-generation",
            "chatbot",
            "question-answering",
            "translation",
            "creative-writing",
            "code-generation",
            "vision",
            "summarization",
            "reasoning",
            "multilingual"
        ]
        
        if self.api_key and GEMINI_AVAILABLE:
            self._initialize()
    
    def _initialize(self):
        """初始化Gemini客户端"""
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
            self._initialized = True
            logger.info(f"Gemini引擎初始化成功，模型: {self.model_name}")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Gemini引擎初始化失败: {str(e)}")
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
                logger.warning(f"Gemini引擎调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        self._last_error = str(last_exception)
        logger.error(f"Gemini引擎调用最终失败: {str(last_exception)}")
        return self._create_error_response(str(last_exception))
    
    def _generate(self, prompt: str, **kwargs) -> Dict:
        """生成响应"""
        if not self._initialized:
            if self.api_key and GEMINI_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("Gemini引擎未初始化")
        
        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_output_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if hasattr(response, 'text'):
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "response": response.text,
                        "model": self.model_name,
                        "usage": self._extract_usage(response)
                    }
                }
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "response": "\n".join(text_parts),
                            "model": self.model_name,
                            "usage": self._extract_usage(response)
                        }
                    }
            
            return self._create_error_response("无法解析Gemini响应")
        
        except Exception as e:
            raise e
    
    def _extract_usage(self, response) -> Dict:
        """提取使用信息"""
        usage = {}
        if hasattr(response, 'usage_metadata'):
            meta = response.usage_metadata
            if hasattr(meta, 'prompt_token_count'):
                usage['prompt_tokens'] = meta.prompt_token_count
            if hasattr(meta, 'candidates_token_count'):
                usage['completion_tokens'] = meta.candidates_token_count
            if hasattr(meta, 'total_token_count'):
                usage['total_tokens'] = meta.total_token_count
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
            if self.api_key and GEMINI_AVAILABLE:
                self._initialize()
            else:
                return self._create_error_response("Gemini引擎未初始化")
        
        try:
            chat_session = self._model.start_chat(history=[])
            
            for message in messages:
                role = message.get('role', 'user')
                content = message.get('content', '')
                
                if role == 'user':
                    chat_session.send_message(content)
                elif role == 'assistant':
                    # Gemini会自动处理助手消息作为历史
                    pass
            
            response = chat_session.send_message(messages[-1]['content'])
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": response.text,
                    "model": self.model_name,
                    "usage": self._extract_usage(response)
                }
            }
        except Exception as e:
            logger.error(f"Gemini聊天模式失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def generate_image(self, prompt: str, **kwargs) -> Dict:
        """生成图片（需要Gemini Pro Vision或其他支持图像生成的模型）"""
        return {
            "code": -1,
            "message": "Gemini当前模型不支持图像生成",
            "data": {}
        }
    
    def analyze_image(self, image_data: Any, prompt: str = "", **kwargs) -> Dict:
        """分析图像（需要Gemini Pro Vision）"""
        if not self._initialized or 'vision' not in self.model_name.lower():
            return self._create_error_response("需要Gemini Pro Vision模型")
        
        try:
            response = self._model.generate_content([prompt, image_data])
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": response.text,
                    "model": self.model_name,
                    "usage": self._extract_usage(response)
                }
            }
        except Exception as e:
            logger.error(f"Gemini图像分析失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def embed(self, text: str, **kwargs) -> Dict:
        """生成文本嵌入"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type=kwargs.get('task_type', "retrieval_query")
            )
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "embedding": result.get('embedding', []),
                    "model": "models/embedding-001"
                }
            }
        except Exception as e:
            logger.error(f"Gemini嵌入生成失败: {str(e)}")
            return self._create_error_response(str(e))
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._initialized:
                return False
            
            response = self._model.generate_content("Hello")
            return hasattr(response, 'text')
        except Exception as e:
            logger.error(f"Gemini健康检查失败: {str(e)}")
            return False
    
    def get_supported_features(self) -> List[str]:
        """获取支持的功能列表"""
        return self.supported_features
    
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
        self.model_name = self.config.get('model', self.model_name)
        self.max_tokens = self.config.get('max_tokens', self.max_tokens)
        self.temperature = self.config.get('temperature', self.temperature)
        self.timeout = self.config.get('timeout', self.timeout)
        self.retry_count = self.config.get('retry_count', self.retry_count)
        
        if self.api_key and GEMINI_AVAILABLE:
            self._initialize()


def create_gemini_engine(config: Dict = None) -> GeminiEngine:
    """创建Gemini引擎实例"""
    return GeminiEngine(config)


def init_gemini_engine(api_key: str, model: str = "gemini-pro") -> GeminiEngine:
    """初始化Gemini引擎"""
    config = {
        "api_key": api_key,
        "model": model,
        "max_tokens": 8192,
        "temperature": 0.7,
        "timeout": 60,
        "retry_count": 3
    }
    return GeminiEngine(config)
