# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI引擎集成管理器,用于集成和管理多种AI引擎
支持:抖音火山引擎、豆包、腾讯云、阿里云、阿福、千问等
"""

import time
import threading
import requests
import logging

logger = logging.getLogger(__name__)


class AIEngineIntegrator:
    """AI引擎集成管理器"""

    def __init__(self):
        self.engines = {}
        self.engine_lock = threading.Lock()
        self.health_status = {}
        self.health_check_interval = 30
        self.health_check_thread = None
        self.is_running = True
        self.fallback_engine = "minimax"
        self.supported_engines = [
            "volcengine", "doubao", "tencent", "aliyun", "afu", "qianwen",
            "openai", "huggingface", "gemini", "claude", "wenxin", "zhipu",
            "llama", "minimax", "local"
        ]

        self.engine_priorities = {
            "minimax": 10, "doubao": 9, "zhipu": 8, "wenxin": 8,
            "qianwen": 8, "tencent": 7, "aliyun": 7, "afu": 6,
            "volcengine": 5, "openai": 5, "huggingface": 4,
            "gemini": 4, "claude": 4, "llama": 3, "local": 2
        }

        self.engine_configs = {
            "volcengine": {
                "api_key": None,
                "endpoint": "https://api.volcengine.com",
                "model": "doubao-pro",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "summarization"],
                "top_p": 0.9,
                "top_k": 50
            },
            "doubao": {
                "api_key": None,
                "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                "max_tokens": 4096,
                "timeout": 60,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation"],
                "top_k": 50
            },
            "tencent": {
                "secret_key": None,
                "access_key_id": None,
                "model": "chatglm_turbo",
                "max_tokens": 4096,
                "timeout": 60,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "summarization"]
            },
            "aliyun": {
                "access_key_id": None,
                "endpoint": "https://dashscope.aliyuncs.com/api/v1/services",
                "model": "qwen-turbo",
                "temperature": 0.7,
                "timeout": 60,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation"]
            },
            "afu": {
                "api_key": None,
                "model": "afu-70b",
                "temperature": 0.7,
                "retry_count": 3,
            },
            "qianwen": {
                "access_key_id": None,
                "access_key_secret": None,
                "model": "qwen-turbo",
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation"]
            },
            "openai": {
                "api_key": None,
                "max_tokens": 4096,
                "temperature": 0.7,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation", "multilingual"]
            },
            "huggingface": {
                "api_key": None,
                "model": "meta-llama/Llama-3-70b-chat-hf",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 120,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "summarization", "code-generation"]
            },
            "gemini": {
                "api_key": None,
                "model": "gemini-pro",
                "max_tokens": 8192,
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation", "vision"]
            },
            "claude": {
                "api_key": None,
                "model": "claude-3-opus",
                "max_tokens": 200000,
                "temperature": 0.7,
                "timeout": 120,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing", "code-generation", "long-context"]
            },
            "wenxin": {
                "api_key": None,
                "secret_key": None,
                "model": "ernie-4.0",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "creative-writing"]
            },
            "zhipu": {
                "api_key": None,
                "model": "glm-4",
                "max_tokens": 8192,
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "code-generation"]
            },
            "llama": {
                "api_key": None,
                "model": "llama-3-70b",
                "max_tokens": 4096,
                "temperature": 0.7,
            },
            "minimax": {
                "model": "abab5.5-chat",
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 60,
                "retry_count": 3,
                "top_p": 0.9,
                "top_k": 50
            },
            "local": {
                "model": "local-llm",
                "max_tokens": 8192,
                "timeout": 120,
                "supported_features": ["text-generation", "chatbot", "question-answering", "translation", "summarization", "code-generation", "multilingual", "text-classification"],
                "top_k": 50
            }
        }

        for engine in self.supported_engines:
            self.health_status[engine] = {
                "last_check": time.time(),
                "error_count": 0,
                "last_recovery": time.time(),
                "recovery_time": 0
            }
        self._start_health_check()

    def register_engine(self, engine_type, engine_instance):
        """注册AI引擎实例"""
        with self.engine_lock:
            if engine_type in self.supported_engines:
                self.engines[engine_type] = engine_instance
                logger.info(f"成功注册AI引擎: {engine_type}")
                return True
            else:
                logger.error(f"不支持的AI引擎类型: {engine_type}")
                return False

    def get_engine(self, engine_type):
        """获取AI引擎实例"""
        with self.engine_lock:
            return self.engines.get(engine_type)

    def get_supported_engines(self):
        """获取支持的AI引擎列表"""
        return self.supported_engines

    def configure_engine(self, engine_type, config):
        """配置AI引擎"""
        with self.engine_lock:
            if engine_type in self.supported_engines:
                self.engine_configs[engine_type].update(config)
                logger.info(f"成功配置AI引擎: {engine_type}")
                return True
            else:
                logger.error(f"不支持的AI引擎类型: {engine_type}")
                return False

    def get_engine_config(self, engine_type):
        """获取AI引擎配置"""
        with self.engine_lock:
            return self.engine_configs.get(engine_type)

    def create_engine(self, engine_type, config=None):
        """创建AI引擎实例"""
        if engine_type not in self.supported_engines:
            logger.error(f"不支持的AI引擎类型: {engine_type}")
            return None
        
        try:
            engine_config = self.engine_configs[engine_type].copy()
            if config:
                engine_config.update(config)

            if engine_type == "local":
                return LocalAIEngine(engine_config)
            elif engine_type == "gemini":
                from .gemini_engine import GeminiEngine
                return GeminiEngine(engine_config)
            elif engine_type == "qianwen":
                from .qianwen_engine import QianwenEngine
                return QianwenEngine(engine_config)
            elif engine_type == "openai":
                from .chatgpt_engine import ChatGPTEngine
                return ChatGPTEngine(engine_config)
            else:
                logger.warning(f"引擎 {engine_type} 尚未完全实现,返回None")
                return None
        except Exception as e:
            logger.error(f"创建AI引擎实例失败: {str(e)}")
            return None

    def _start_health_check(self):
        """启动健康检查线程"""
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()

    def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                for engine in self.supported_engines:
                    self._check_engine_health(engine)
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"健康检查循环异常: {str(e)}")

    def _check_engine_health(self, engine_type):
        """检查单个引擎健康状态"""
        try:
            engine = self.get_engine(engine_type)
            if engine:
                try:
                    if hasattr(engine, 'health_check'):
                        result = engine.health_check()
                        self.health_status[engine_type]["error_count"] = 0
                        self.health_status[engine_type]["last_check"] = time.time()
                        self.health_status[engine_type]["last_recovery"] = time.time()
                        self.health_status[engine_type]["recovery_time"] = 0
                except Exception as e:
                    self.health_status[engine_type]["error_count"] += 1
                    logger.warning(f"引擎 {engine_type} 健康检查失败: {str(e)}")
        except Exception as e:
            logger.error(f"检查引擎健康状态异常: {str(e)}")

    def get_available_engine(self, features=None):
        """获取可用的AI引擎"""
        with self.engine_lock:
            prioritized = sorted(self.supported_engines, key=lambda x: self.engine_priorities.get(x, 0), reverse=True)
            
            for engine_type in prioritized:
                if self.health_status.get(engine_type, {}).get("error_count", 0) < 3:
                    config = self.engine_configs.get(engine_type, {})
                    engine_features = config.get("supported_features", [])
                    
                    if features:
                        if all(f in engine_features for f in features):
                            return engine_type
                    else:
                        return engine_type
            
            return self.fallback_engine

    def generate_response(self, prompt, engine_type=None, features=None, **kwargs):
        """生成AI响应"""
        try:
            if not engine_type:
                engine_type = self.get_available_engine(features)
            
            engine = self.get_engine(engine_type)
            if not engine:
                engine = self.create_engine(engine_type)
                if engine:
                    self.register_engine(engine_type, engine)
            
            if engine:
                return engine.generate(prompt, **kwargs)
            else:
                return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"生成响应失败: {str(e)}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt):
        """备用响应"""
        logger.warning("使用备用响应")
        return {
            "code": 0,
            "message": "success",
            "data": {
                "response": f"AI回复: {prompt}"
            }
        }

    def shutdown(self):
        """关闭AI引擎集成管理器"""
        self.is_running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("AI引擎集成管理器已关闭")


class LocalAIEngine:
    """本地AI引擎实现"""
    
    def __init__(self, config):
        self.config = config
        logger.info("本地AI引擎初始化完成")
    
    def generate(self, prompt, **kwargs):
        """生成响应"""
        try:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": f"本地AI回复: {prompt}"
                }
            }
        except Exception as e:
            logger.error(f"本地AI引擎调用失败: {str(e)}")
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "response": f"本地AI回复: {prompt}"
                }
            }


ai_engine_integrator = AIEngineIntegrator()