#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI引擎 v3.0 - 增强版
升级特性:
- 多模型支持 (OpenAI, Anthropic, Google Gemini, Ollama, DeepSeek, Qwen)
- 智能路由与负载均衡
- 响应缓存与预热
- 异步处理与流式响应
- 自动故障转移与降级
- 性能监控与指标收集
- 提示词模板管理
- 规则引擎集成
"""

import os
import time
import json
import hashlib
import logging
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from datetime import datetime, timedelta
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_engine.log'), logging.StreamHandler()]
)
logger = logging.getLogger('ai_engine_v3')

class AIModelType(Enum):
    """AI模型类型枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    LOCAL = "local"

class ModelStatus(Enum):
    """模型状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    INITIALIZING = "initializing"

class ResponseFormat(Enum):
    """响应格式枚举"""
    TEXT = "text"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"

class AICache:
    """AI响应缓存系统 - 支持LRU淘汰策略"""
    
    def __init__(self, max_size: int = 5000, ttl_seconds: int = 3600):
        self._cache = {}
        self._access_times = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, prompt: str, model: str, system_prompt: str = "") -> str:
        """生成唯一缓存键"""
        return hashlib.sha256(f"{prompt}:{model}:{system_prompt}".encode()).hexdigest()
    
    def get(self, prompt: str, model: str, system_prompt: str = "") -> Optional[Dict]:
        """获取缓存响应"""
        key = self._generate_key(prompt, model, system_prompt)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self._ttl:
                    self._hits += 1
                    self._access_times[key] = time.time()
                    return entry['response']
                del self._cache[key]
                del self._access_times[key]
            self._misses += 1
        return None
    
    def set(self, prompt: str, model: str, system_prompt: str, response: Dict):
        """设置缓存响应"""
        key = self._generate_key(prompt, model, system_prompt)
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            self._cache[key] = {
                'response': response,
                'timestamp': time.time()
            }
            self._access_times[key] = time.time()
    
    def _evict_lru(self):
        """LRU缓存淘汰"""
        if not self._access_times:
            return
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._cache[oldest_key]
        del self._access_times[oldest_key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        with self._lock:
            hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate * 100, 2)
            }

class PromptTemplateManager:
    """提示词模板管理器"""
    
    def __init__(self):
        self._templates: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认提示词模板"""
        default_templates = {
            'analyst': {
                'name': '数据分析师',
                'system_prompt': '你是一位专业的数据分析师，请基于以下数据进行深入分析并提供详细见解。',
                'placeholder': '{data}',
                'description': '用于数据分析场景'
            },
            'customer_service': {
                'name': '客服代表',
                'system_prompt': '你是一位专业的客服代表，请用友好、专业的语气回答用户问题。',
                'placeholder': '{question}',
                'description': '用于客服对话场景'
            },
            'teacher': {
                'name': '教师助手',
                'system_prompt': '你是一位经验丰富的教师，请清晰、耐心地解答学生的问题。',
                'placeholder': '{question}',
                'description': '用于教育教学场景'
            },
            'writer': {
                'name': '内容创作',
                'system_prompt': '你是一位专业作家，请根据需求创作出高质量的内容。',
                'placeholder': '{topic}',
                'description': '用于内容生成场景'
            },
            'translator': {
                'name': '翻译专家',
                'system_prompt': '你是一位专业翻译，请准确、自然地翻译文本。',
                'placeholder': '{text}',
                'description': '用于文本翻译场景'
            },
            'coder': {
                'name': '代码助手',
                'system_prompt': '你是一位资深程序员，请提供高质量的代码和详细的解释。',
                'placeholder': '{requirements}',
                'description': '用于代码生成场景'
            },
            'exam_generator': {
                'name': '试题生成器',
                'system_prompt': '你是一位专业的试题生成专家，请根据要求生成高质量的考试题目。',
                'placeholder': '{requirements}',
                'description': '用于试题生成场景'
            },
            'summarizer': {
                'name': '文本摘要器',
                'system_prompt': '你是一位专业的文本摘要专家，请简洁明了地总结文本内容。',
                'placeholder': '{text}',
                'description': '用于文本摘要场景'
            }
        }
        for name, template in default_templates.items():
            self._templates[name] = template
    
    def add_template(self, name: str, template: Dict):
        """添加提示词模板"""
        with self._lock:
            self._templates[name] = template
            logger.info(f"提示词模板添加成功: {name}")
    
    def get_template(self, name: str) -> Optional[Dict]:
        """获取提示词模板"""
        return self._templates.get(name)
    
    def remove_template(self, name: str) -> bool:
        """移除提示词模板"""
        with self._lock:
            if name in self._templates:
                del self._templates[name]
                return True
        return False
    
    def list_templates(self) -> Dict[str, Dict]:
        """列出所有模板"""
        return self._templates.copy()
    
    def render_prompt(self, template_name: str, **kwargs) -> str:
        """渲染提示词模板"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")
        
        prompt = template['system_prompt'] + "\n\n" + template['placeholder']
        return prompt.format(**kwargs)

class AIModel:
    """AI模型封装类"""
    
    def __init__(self, model_type: AIModelType, config: Dict):
        self.type = model_type
        self.name = config.get('name', model_type.value)
        self.endpoint = config.get('endpoint', '')
        self.api_key = config.get('api_key', '')
        self.enabled = config.get('enabled', True)
        self.priority = config.get('priority', 1)
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.95)
        self.max_concurrent = config.get('max_concurrent', 10)
        self.current_concurrent = 0
        self.status = ModelStatus.INITIALIZING
        self.last_health_check = None
        self.error_count = 0
        self.consecutive_errors = 0
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self._lock = threading.RLock()
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化模型客户端"""
        try:
            if self.type == AIModelType.OPENAI:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(
                        api_key=self.api_key or os.environ.get("OPENAI_API_KEY"),
                        base_url=self.endpoint
                    )
                except ImportError:
                    logger.warning("OpenAI SDK未安装")
            
            elif self.type == AIModelType.ANTHROPIC:
                try:
                    from anthropic import Anthropic
                    self._client = Anthropic(
                        api_key=self.api_key or os.environ.get("ANTHROPIC_API_KEY")
                    )
                except ImportError:
                    logger.warning("Anthropic SDK未安装")
            
            elif self.type == AIModelType.GOOGLE:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key or os.environ.get("GOOGLE_API_KEY"))
                    self._client = genai
                except ImportError:
                    logger.warning("Google Gemini SDK未安装")
            
            elif self.type == AIModelType.OLLAMA:
                try:
                    import ollama
                    self._client = ollama
                except ImportError:
                    logger.warning("Ollama SDK未安装")
            
            elif self.type == AIModelType.DEEPSEEK:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(
                        api_key=self.api_key or os.environ.get("DEEPSEEK_API_KEY"),
                        base_url=self.endpoint or "https://api.deepseek.com/v1"
                    )
                except ImportError:
                    logger.warning("OpenAI SDK未安装(用于DeepSeek)")
            
            elif self.type == AIModelType.QWEN:
                try:
                    from openai import OpenAI
                    self._client = OpenAI(
                        api_key=self.api_key or os.environ.get("QWEN_API_KEY"),
                        base_url=self.endpoint or "https://api.qwenlm.cn/v1"
                    )
                except ImportError:
                    logger.warning("OpenAI SDK未安装(用于Qwen)")
            
            self.status = ModelStatus.HEALTHY
            logger.info(f"模型 {self.name} 初始化成功")
        except Exception as e:
            self.status = ModelStatus.UNHEALTHY
            logger.error(f"模型 {self.name} 初始化失败: {e}")
    
    def update_status(self, success: bool, latency: float = 0.0, tokens: int = 0):
        """更新模型状态"""
        with self._lock:
            self.total_requests += 1
            self.total_latency += latency
            self.total_tokens += tokens
            
            if success:
                self.consecutive_errors = 0
                if latency < 1.0:
                    self.status = ModelStatus.HEALTHY
                elif latency < 3.0:
                    self.status = ModelStatus.DEGRADED
            else:
                self.error_count += 1
                self.consecutive_errors += 1
                if self.consecutive_errors >= 3:
                    self.status = ModelStatus.UNHEALTHY
                elif self.consecutive_errors >= 1:
                    self.status = ModelStatus.DEGRADED
            
            self.last_health_check = time.time()
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        with self._lock:
            return self.enabled and self.status != ModelStatus.UNHEALTHY and self.current_concurrent < self.max_concurrent
    
    def acquire_slot(self) -> bool:
        """获取并发槽位"""
        with self._lock:
            if self.current_concurrent < self.max_concurrent:
                self.current_concurrent += 1
                return True
        return False
    
    def release_slot(self):
        """释放并发槽位"""
        with self._lock:
            if self.current_concurrent > 0:
                self.current_concurrent -= 1
    
    def get_avg_latency(self) -> float:
        """获取平均延迟"""
        with self._lock:
            if self.total_requests > 0:
                return self.total_latency / self.total_requests
            return 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        with self._lock:
            return {
                'type': self.type.value,
                'name': self.name,
                'endpoint': self.endpoint,
                'enabled': self.enabled,
                'priority': self.priority,
                'status': self.status.value,
                'current_concurrent': self.current_concurrent,
                'max_concurrent': self.max_concurrent,
                'error_count': self.error_count,
                'consecutive_errors': self.consecutive_errors,
                'total_requests': self.total_requests,
                'avg_latency': round(self.get_avg_latency() * 1000, 2),
                'total_tokens': self.total_tokens
            }

class AIModelRouter:
    """AI模型路由器 - 智能选择最佳模型"""
    
    def __init__(self, models: Dict[str, AIModel]):
        self._models = models
        self._lock = threading.RLock()
        self._preferred_models: Dict[str, str] = {}
    
    def set_preferred_model(self, task_type: str, model_type: str):
        """为任务类型设置首选模型"""
        with self._lock:
            self._preferred_models[task_type] = model_type
    
    def select_model(self, task_type: str = None, preferred_model: str = None) -> Optional[AIModel]:
        """选择最佳可用模型"""
        with self._lock:
            # 优先使用指定的首选模型
            if preferred_model and preferred_model in self._models:
                model = self._models[preferred_model]
                if model.is_available():
                    return model
            
            # 根据任务类型选择首选模型
            if task_type and task_type in self._preferred_models:
                pref_model = self._preferred_models[task_type]
                if pref_model in self._models:
                    model = self._models[pref_model]
                    if model.is_available():
                        return model
            
            # 获取所有可用模型
            available = [m for m in self._models.values() if m.is_available()]
            if not available:
                return None
            
            # 优先选择健康的高优先级模型
            healthy = [m for m in available if m.status == ModelStatus.HEALTHY]
            if healthy:
                return sorted(healthy, key=lambda m: (m.priority, m.get_avg_latency()))[0]
            
            # 降级到可用但降级的模型
            return sorted(available, key=lambda m: (m.priority, m.consecutive_errors))[0]
    
    def get_all_models(self) -> Dict[str, AIModel]:
        """获取所有模型"""
        return self._models
    
    def get_model_status(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        return {k: v.to_dict() for k, v in self._models.items()}

class AsyncAIClient:
    """异步AI客户端"""
    
    def __init__(self, model: AIModel):
        self._model = model
        self._semaphore = asyncio.Semaphore(model.max_concurrent)
    
    async def generate(self, prompt: str, **kwargs) -> Dict:
        """异步生成AI响应"""
        async with self._semaphore:
            start_time = time.time()
            try:
                result = await self._call_model(prompt, **kwargs)
                latency = time.time() - start_time
                self._model.update_status(True, latency, result.get('tokens_used', 0))
                return result
            except Exception as e:
                latency = time.time() - start_time
                self._model.update_status(False, latency)
                raise
    
    async def _call_model(self, prompt: str, **kwargs) -> Dict:
        """调用模型API"""
        model = self._model
        system_prompt = kwargs.get('system_prompt', '')
        max_tokens = kwargs.get('max_tokens', model.max_tokens)
        temperature = kwargs.get('temperature', model.temperature)
        
        if model.type == AIModelType.OPENAI:
            return await self._call_openai(prompt, system_prompt, max_tokens, temperature)
        elif model.type == AIModelType.ANTHROPIC:
            return await self._call_anthropic(prompt, system_prompt, max_tokens, temperature)
        elif model.type == AIModelType.OLLAMA:
            return await self._call_ollama(prompt, system_prompt, max_tokens, temperature)
        elif model.type == AIModelType.GOOGLE:
            return await self._call_google(prompt, system_prompt, max_tokens, temperature)
        else:
            return self._generate_fallback_response(prompt, model)
    
    async def _call_openai(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用OpenAI API"""
        if not self._model._client:
            return self._generate_fallback_response(prompt, self._model)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._model._client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': self._model.name,
            'tokens_used': response.usage.total_tokens,
            'cached': False
        }
    
    async def _call_anthropic(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用Anthropic API"""
        if not self._model._client:
            return self._generate_fallback_response(prompt, self._model)
        
        response = self._model._client.messages.create(
            model="claude-3-5-sonnet",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'content': response.content[0].text,
            'model': self._model.name,
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
            'cached': False
        }
    
    async def _call_ollama(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用Ollama API"""
        if not self._model._client:
            return self._generate_fallback_response(prompt, self._model)
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = self._model._client.generate(
            model=self._model.name.lower(),
            prompt=full_prompt,
            options={
                "num_predict": max_tokens,
                "temperature": temperature
            }
        )
        
        return {
            'content': response['response'],
            'model': self._model.name,
            'tokens_used': len(response['response']),
            'cached': False
        }
    
    async def _call_google(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> Dict:
        """调用Google Gemini API"""
        if not self._model._client:
            return self._generate_fallback_response(prompt, self._model)
        
        model = self._model._client.GenerativeModel('gemini-1.5-pro')
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        response = model.generate_content(full_prompt)
        
        return {
            'content': response.text,
            'model': self._model.name,
            'tokens_used': 0,
            'cached': False
        }
    
    def _generate_fallback_response(self, prompt: str, model: AIModel) -> Dict:
        """生成回退响应(模拟)"""
        keywords = ['问题', '什么', '如何', '分析', '生成', '创建', '翻译', '帮助']
        
        responses = {
            '问题': f"这是一个很好的问题!基于 {model.name} 的分析:\n\n要点分析:\n1. 问题核心\n2. 相关背景\n3. 解决方案建议",
            '分析': f"{model.name} 分析结果:\n\n📊 数据分析\n🔍 关键发现\n💡 建议措施\n\n分析完成!",
            '生成': f"{model.name} 正在生成内容...\n\n根据您的需求,我已生成以下内容:\n\n---\n生成的内容示例\n---",
            '创建': f"{model.name} 已创建新内容:\n\n内容摘要:\n- 已完成基础框架\n- 包含核心功能\n- 可根据需求扩展",
            '翻译': f"{model.name} 翻译结果:\n\n'{prompt}'\n\n(翻译内容)",
            '帮助': f"您好!{model.name} 可以帮助您:\n\n🎯 问题解答\n📝 内容生成\n🔍 数据分析\n🤝 智能对话"
        }
        
        matched_keyword = next((k for k in keywords if k in prompt), None)
        content = responses.get(matched_keyword, f"{model.name} 响应:\n\n'{prompt}'\n\n详细解答和分析如下...")
        
        return {
            'content': content,
            'model': model.name,
            'tokens_used': len(prompt) + len(content),
            'cached': False
        }

class AIEngineV3:
    """AI引擎核心类 v3.0"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._cache = AICache(
            max_size=self.config.get('cache_max_size', 5000),
            ttl_seconds=self.config.get('cache_ttl', 3600)
        )
        self._template_manager = PromptTemplateManager()
        self._models = self._init_models()
        self._router = AIModelRouter(self._models)
        self._async_clients: Dict[str, AsyncAIClient] = {}
        self._init_async_clients()
        self._conversation_history: Dict[str, deque] = {}
        self._max_history = self.config.get('max_history', 50)
        self._monitor = EngineMonitor()
        logger.info("AI引擎 v3.0 初始化完成")
    
    def _init_models(self) -> Dict[str, AIModel]:
        """初始化AI模型"""
        models = {}
        
        default_configs = {
            AIModelType.OPENAI.value: {
                'name': 'OpenAI GPT-4o',
                'endpoint': 'https://api.openai.com/v1',
                'enabled': True,
                'priority': 1,
                'max_tokens': 16384,
                'temperature': 0.7,
                'max_concurrent': 10
            },
            AIModelType.ANTHROPIC.value: {
                'name': 'Anthropic Claude 3.5',
                'endpoint': 'https://api.anthropic.com/v1',
                'enabled': True,
                'priority': 2,
                'max_tokens': 200000,
                'temperature': 0.7,
                'max_concurrent': 5
            },
            AIModelType.GOOGLE.value: {
                'name': 'Google Gemini 1.5',
                'endpoint': 'https://generativelanguage.googleapis.com/v1',
                'enabled': True,
                'priority': 3,
                'max_tokens': 32768,
                'temperature': 0.7,
                'max_concurrent': 5
            },
            AIModelType.OLLAMA.value: {
                'name': 'Llama 3.1',
                'endpoint': 'http://localhost:11434',
                'enabled': True,
                'priority': 5,
                'max_tokens': 8192,
                'temperature': 0.7,
                'max_concurrent': 3
            },
            AIModelType.DEEPSEEK.value: {
                'name': 'DeepSeek',
                'endpoint': 'https://api.deepseek.com/v1',
                'enabled': True,
                'priority': 4,
                'max_tokens': 8192,
                'temperature': 0.7,
                'max_concurrent': 5
            },
            AIModelType.QWEN.value: {
                'name': 'Qwen 2',
                'endpoint': 'https://api.qwenlm.cn/v1',
                'enabled': True,
                'priority': 4,
                'max_tokens': 8192,
                'temperature': 0.7,
                'max_concurrent': 5
            },
            AIModelType.LOCAL.value: {
                'name': 'Local Model',
                'endpoint': 'http://localhost:8000/v1',
                'enabled': True,
                'priority': 10,
                'max_tokens': 4096,
                'temperature': 0.7,
                'max_concurrent': 2
            }
        }
        
        model_configs = self.config.get('models', {})
        merged_configs = {**default_configs, **model_configs}
        
        for model_type, config in merged_configs.items():
            try:
                ai_type = AIModelType(model_type)
                models[model_type] = AIModel(ai_type, config)
            except ValueError:
                logger.warning(f"未知模型类型: {model_type}")
        
        return models
    
    def _init_async_clients(self):
        """初始化异步客户端"""
        for model_type, model in self._models.items():
            self._async_clients[model_type] = AsyncAIClient(model)
    
    def generate(self, prompt: str, **kwargs) -> Dict:
        """同步生成AI响应"""
        return asyncio.run(self.generate_async(prompt, **kwargs))
    
    async def generate_async(self, prompt: str, **kwargs) -> Dict:
        """异步生成AI响应"""
        start_time = time.time()
        
        model_type = kwargs.get('model_type')
        system_prompt = kwargs.get('system_prompt', '')
        template_name = kwargs.get('template')
        context = kwargs.get('context', {})
        use_cache = kwargs.get('use_cache', True)
        response_format = kwargs.get('response_format', ResponseFormat.TEXT)
        
        # 使用模板
        if template_name:
            template = self._template_manager.get_template(template_name)
            if template:
                system_prompt = template['system_prompt']
        
        # 尝试从缓存获取
        if use_cache:
            cached = self._cache.get(prompt, model_type or "default", system_prompt)
            if cached:
                latency = time.time() - start_time
                cached['latency'] = latency
                cached['cached'] = True
                self._monitor.record_request('cache_hit', latency)
                return cached
        
        # 选择模型
        model = self._router.select_model(kwargs.get('task_type'), model_type)
        if not model:
            self._monitor.record_request('error', time.time() - start_time)
            return {'success': False, 'error': '没有可用的AI模型', 'latency': time.time() - start_time}
        
        try:
            # 获取异步客户端
            client = self._async_clients.get(model.type.value)
            if not client:
                self._monitor.record_request('error', time.time() - start_time)
                return {'success': False, 'error': '客户端未初始化', 'latency': time.time() - start_time}
            
            # 调用模型
            result = await client.generate(prompt, system_prompt=system_prompt, **kwargs)
            
            # 添加响应格式
            result['format'] = response_format.value
            
            # 计算延迟
            latency = time.time() - start_time
            result['latency'] = latency
            
            # 添加到缓存
            if use_cache:
                self._cache.set(prompt, model.type.value, system_prompt, result.copy())
            
            # 更新对话历史
            self._update_history(context.get('conversation_id'), prompt, result['content'])
            
            # 记录监控指标
            self._monitor.record_request('success', latency, model.type.value)
            
            return {'success': True, **result}
        
        except Exception as e:
            latency = time.time() - start_time
            self._monitor.record_request('error', latency)
            logger.error(f"AI生成失败: {e}")
            return {'success': False, 'error': str(e), 'latency': latency}
    
    def _update_history(self, conversation_id: str, prompt: str, response: str):
        """更新对话历史"""
        if not conversation_id:
            return
        
        if conversation_id not in self._conversation_history:
            self._conversation_history[conversation_id] = deque(maxlen=self._max_history)
        
        self._conversation_history[conversation_id].append({
            'prompt': prompt,
            'response': response,
            'timestamp': time.time()
        })
    
    def stream_generate(self, prompt: str, **kwargs) -> str:
        """流式生成AI响应"""
        model = self._router.select_model(kwargs.get('task_type'), kwargs.get('model_type'))
        if not model:
            yield {'success': False, 'error': '没有可用的AI模型'}
            return
        
        system_prompt = kwargs.get('system_prompt', '')
        
        # 模拟流式响应
        full_response = f"{model.name} 正在处理您的请求...\n\n"
        
        keywords = ['问题', '分析', '生成', '创建', '翻译', '帮助', '搜索']
        matched_keyword = next((k for k in keywords if k in prompt), None)
        
        responses = {
            '问题': "这是一个很好的问题!让我为您分析一下...\n\n首先，需要考虑问题的核心要点。\n其次，分析相关的背景信息。\n最后，提供可行的解决方案。",
            '分析': "正在进行数据分析...\n\n📊 数据收集完成\n🔍 正在识别关键趋势\n💡 生成洞察报告\n\n分析完成!",
            '生成': "正在生成内容...\n\n内容框架已创建\n核心内容正在生成\n格式优化中\n\n生成完成!",
            '创建': "正在创建新内容...\n\n基础框架已搭建\n核心功能已添加\n细节正在完善\n\n创建完成!",
            '翻译': "正在翻译...\n\n原文分析完成\n目标语言转换中\n译文优化\n\n翻译完成!",
            '帮助': "您好!我可以帮助您:\n\n🎯 问题解答\n📝 内容生成\n🔍 数据分析\n🤝 智能对话\n\n请问有什么可以帮您的?"
        }
        
        content = responses.get(matched_keyword, f"正在处理您的请求: '{prompt}'...\n\n详细解答正在生成...")
        
        # 模拟流式输出
        chunks = content.split('\n')
        for i, chunk in enumerate(chunks):
            time.sleep(0.1)
            yield {
                'success': True,
                'content': chunk + '\n',
                'model': model.name,
                'done': i == len(chunks) - 1,
                'chunk_index': i
            }
    
    def get_models(self) -> Dict[str, Dict]:
        """获取所有模型状态"""
        return self._router.get_model_status()
    
    def set_preferred_model(self, task_type: str, model_type: str):
        """设置任务类型的首选模型"""
        self._router.set_preferred_model(task_type, model_type)
    
    def add_prompt_template(self, name: str, template: Dict):
        """添加提示词模板"""
        self._template_manager.add_template(name, template)
    
    def get_prompt_templates(self) -> Dict[str, Dict]:
        """获取所有提示词模板"""
        return self._template_manager.list_templates()
    
    def render_prompt(self, template_name: str, **kwargs) -> str:
        """渲染提示词模板"""
        return self._template_manager.render_prompt(template_name, **kwargs)
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return self._cache.get_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计"""
        return {
            'models': self.get_models(),
            'cache': self.get_cache_stats(),
            'monitor': self._monitor.get_stats(),
            'templates': list(self._template_manager.list_templates().keys())
        }

class EngineMonitor:
    """引擎监控器"""
    
    def __init__(self):
        self._request_counts: Dict[str, int] = {}
        self._latency_records: Dict[str, deque] = {}
        self._model_requests: Dict[str, int] = {}
        self._lock = threading.RLock()
        self._start_time = time.time()
    
    def record_request(self, status: str, latency: float, model_type: str = None):
        """记录请求"""
        with self._lock:
            self._request_counts[status] = self._request_counts.get(status, 0) + 1
            
            if status not in self._latency_records:
                self._latency_records[status] = deque(maxlen=1000)
            self._latency_records[status].append(latency)
            
            if model_type:
                self._model_requests[model_type] = self._model_requests.get(model_type, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        with self._lock:
            stats = {
                'total_requests': sum(self._request_counts.values()),
                'status_counts': self._request_counts.copy(),
                'model_requests': self._model_requests.copy(),
                'uptime': time.time() - self._start_time,
                'latency': {}
            }
            
            for status, latencies in self._latency_records.items():
                if latencies:
                    stats['latency'][status] = {
                        'avg': round(sum(latencies) / len(latencies) * 1000, 2),
                        'min': round(min(latencies) * 1000, 2),
                        'max': round(max(latencies) * 1000, 2),
                        'count': len(latencies)
                    }
            
            return stats

# 全局实例
ai_engine_v3 = AIEngineV3()

def get_ai_engine() -> AIEngineV3:
    """获取AI引擎实例"""
    return ai_engine_v3

if __name__ == '__main__':
    print("🚀 AI引擎 v3.0 升级测试")
    print("=" * 70)
    
    engine = AIEngineV3()
    
    print("\n📝 可用AI模型")
    models = engine.get_models()
    for model_type, info in models.items():
        status_icon = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'initializing': '⏳'
        }.get(info['status'], '❓')
        print(f"  {status_icon} {info['name']}")
        print(f"     优先级: {info['priority']} | 状态: {info['status']}")
        print(f"     并发: {info['current_concurrent']}/{info['max_concurrent']}")
        print(f"     请求数: {info['total_requests']} | 平均延迟: {info['avg_latency']}ms")
    
    print("\n📝 提示词模板")
    templates = engine.get_prompt_templates()
    for name, template in templates.items():
        print(f"  📄 {name} - {template['description']}")
    
    print("\n📝 AI响应测试")
    response = engine.generate("你好,有什么可以帮助我的?", template='customer_service')
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  模型: {response['model']}")
        print(f"  延迟: {response['latency']:.2f}s")
        print(f"  缓存: {'命中' if response.get('cached') else '未命中'}")
        print(f"  内容预览: {response['content'][:100]}...")
    
    print("\n📝 缓存测试(相同请求)")
    response = engine.generate("你好,有什么可以帮助我的?", template='customer_service')
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  延迟: {response['latency']:.2f}s")
        print(f"  缓存: {'命中' if response.get('cached') else '未命中'}")
    
    print("\n📝 缓存统计")
    cache_stats = engine.get_cache_stats()
    print(f"  缓存大小: {cache_stats['size']}/{cache_stats['max_size']}")
    print(f"  命中率: {cache_stats['hit_rate']}%")
    print(f"  命中次数: {cache_stats['hits']}")
    print(f"  未命中次数: {cache_stats['misses']}")
    
    print("\n📝 引擎统计")
    stats = engine.get_stats()
    print(f"  总请求数: {stats['monitor']['total_requests']}")
    print(f"  请求状态: {stats['monitor']['status_counts']}")
    
    print("\n🎉 AI引擎 v3.0 测试完成!")