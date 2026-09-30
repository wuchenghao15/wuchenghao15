#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI service module - Enhanced Version 2.0
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Union, Generator, Callable
from datetime import datetime, timedelta
from .config import config
from .logging import logger
from .exceptions import AIError

class AICache:
    """Simple in-memory cache for AI responses"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple] = {}
        self.ttl_seconds = ttl_seconds
    
    def _get_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters"""
        key_data = f"{prompt}:{model}:{sorted(kwargs.items())}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, **kwargs) -> Optional[str]:
        """Get cached response if exists and not expired"""
        key = self._get_key(prompt, model, **kwargs)
        if key in self.cache:
            value, expire_time = self.cache[key]
            if datetime.now() < expire_time:
                logger.debug("Cache hit")
                return value
            del self.cache[key]
        return None
    
    def set(self, prompt: str, model: str, response: str, **kwargs) -> None:
        """Cache a response"""
        key = self._get_key(prompt, model, **kwargs)
        expire_time = datetime.now() + timedelta(seconds=self.ttl_seconds)
        self.cache[key] = (response, expire_time)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Cleanup expired cache entries, return number removed"""
        now = datetime.now()
        expired = [k for k, (_, exp) in self.cache.items() if now >= exp]
        for k in expired:
            del self.cache[k]
        return len(expired)

class AIService:
    """Enhanced AI service wrapper with multiple providers"""
    
    def __init__(self):
        self.max_tokens = config.get("ai.max_tokens", 8192)
        self.temperature = config.get("ai.temperature", 0.7)
        self.top_p = config.get("ai.top_p", 0.95)
        self.top_k = config.get("ai.top_k", 40)
        self.timeout = config.get("ai.api_timeout", 120)
        self.default_provider = config.get("ai.default_provider", "auto")
        self.streaming_enabled = config.get("ai.streaming_enabled", True)
        self.cache_enabled = config.get("ai.cache_enabled", True)
        cache_ttl = config.get("ai.cache_ttl_seconds", 3600)
        
        self.cache = AICache(cache_ttl) if self.cache_enabled else None
        self.available_providers: Dict[str, bool] = {}
        self._init_ai()
    
    def _init_ai(self):
        """Initialize AI service with all providers"""
        try:
            self._load_providers()
            logger.info(f"AI service v2.0 initialized. Providers: {list(self.available_providers.keys())}")
        except Exception as e:
            logger.warning(f"Failed to initialize AI service: {e}")
    
    def _load_providers(self):
        """Load all AI providers"""
        self.available = False
        
        try:
            import openai
            api_key = config.get("ai.providers.openai.api_key", "") or os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                self.openai = openai
                self.openai.api_key = api_key
                self.openai.base_url = config.get("ai.providers.openai.base_url", "https://api.openai.com/v1")
                self.available_providers["openai"] = True
                self.available = True
                logger.info("OpenAI provider configured")
        except ImportError:
            pass
        
        try:
            import ollama
            self.ollama = ollama
            self.ollama_base_url = config.get("ai.providers.ollama.base_url", "http://localhost:11434")
            self.available_providers["ollama"] = True
            self.available = True
            logger.info("Ollama provider configured")
        except ImportError:
            pass
        
        try:
            import anthropic
            api_key = config.get("ai.providers.anthropic.api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key:
                self.anthropic = anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                self.available_providers["anthropic"] = True
                self.available = True
                logger.info("Anthropic provider configured")
        except ImportError:
            pass
    
    def _select_provider(self, preferred: Optional[str] = None) -> str:
        """Select the best available provider"""
        if preferred and preferred in self.available_providers:
            return preferred
        
        if self.default_provider in self.available_providers:
            return self.default_provider
        
        if self.available_providers:
            return next(iter(self.available_providers.keys()))
        
        raise AIError("No AI provider available")
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """Generate text using AI with caching support"""
        if not self.available:
            raise AIError("AI service not available")
        
        selected_provider = self._select_provider(provider)
        
        if model is None:
            model = config.get(f"ai.providers.{selected_provider}.default_model", "")
        
        if self.cache and use_cache:
            cached = self.cache.get(prompt, model, provider=selected_provider, **kwargs)
            if cached:
                return cached
        
        try:
            start_time = time.time()
            if selected_provider == "openai":
                result = self._generate_openai(prompt, model, **kwargs)
            elif selected_provider == "anthropic":
                result = self._generate_anthropic(prompt, model, **kwargs)
            elif selected_provider == "ollama":
                result = self._generate_ollama(prompt, model, **kwargs)
            else:
                raise AIError(f"Unknown provider: {selected_provider}")
            
            elapsed = time.time() - start_time
            logger.info(f"AI generation complete in {elapsed:.2f}s (provider: {selected_provider}, model: {model})")
            
            if self.cache and use_cache:
                self.cache.set(prompt, model, result, provider=selected_provider, **kwargs)
            
            return result
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise AIError(f"AI generation failed: {str(e)}")
    
    def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream AI response token by token"""
        if not self.streaming_enabled:
            yield self.generate(prompt, model, provider, use_cache=False, **kwargs)
            return
        
        if not self.available:
            raise AIError("AI service not available")
        
        selected_provider = self._select_provider(provider)
        
        if model is None:
            model = config.get(f"ai.providers.{selected_provider}.default_model", "")
        
        try:
            if selected_provider == "openai":
                yield from self._generate_openai_stream(prompt, model, **kwargs)
            elif selected_provider == "ollama":
                yield from self._generate_ollama_stream(prompt, model, **kwargs)
            else:
                yield self.generate(prompt, model, provider, use_cache=False, **kwargs)
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise AIError(f"Streaming generation failed: {str(e)}")
    
    def _generate_openai(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using OpenAI API"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        response = self.openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
            timeout=kwargs.get("timeout", self.timeout)
        )
        return response.choices[0].message.content.strip()
    
    def _generate_openai_stream(self, prompt: str, model: str, **kwargs):
        """Stream using OpenAI API"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        response = self.openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
            stream=True
        )
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content'):
                yield chunk.choices[0].delta.content or ""
    
    def _generate_anthropic(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Anthropic API"""
        message = self.anthropic_client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    
    def _generate_ollama(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Ollama"""
        response = self.ollama.generate(
            model=model,
            prompt=prompt,
            options={
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "top_k": kwargs.get("top_k", self.top_k)
            }
        )
        return response['response'].strip()
    
    def _generate_ollama_stream(self, prompt: str, model: str, **kwargs):
        """Stream using Ollama"""
        stream = self.ollama.generate(
            model=model,
            prompt=prompt,
            options={
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "top_p": kwargs.get("top_p", self.top_p),
                "top_k": kwargs.get("top_k", self.top_k)
            },
            stream=True
        )
        for chunk in stream:
            if 'response' in chunk:
                yield chunk['response']
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """Chat with AI using conversation history"""
        if not self.available:
            raise AIError("AI service not available")
        
        selected_provider = self._select_provider(provider)
        
        if model is None:
            model = config.get(f"ai.providers.{selected_provider}.default_model", "")
        
        try:
            if selected_provider == "openai":
                response = self.openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature)
                )
                return response.choices[0].message.content.strip()
            elif selected_provider == "anthropic":
                response = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature),
                    messages=messages
                )
                return response.content[0].text.strip()
            elif selected_provider == "ollama":
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                return self._generate_ollama(prompt, model, **kwargs)
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise AIError(f"Chat failed: {str(e)}")
    
    def analyze_code(self, code: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze code for issues with enhanced prompts"""
        prompts = {
            "general": f"Analyze this Python code and identify any issues. Return JSON with 'issues' array and 'suggestions' array:\n{code}",
            "security": f"Perform a security analysis of this code. Return JSON with 'vulnerabilities' array and 'recommendations' array:\n{code}",
            "optimization": f"Optimize this Python code and suggest improvements. Return JSON with 'optimizations' array and 'performance_impact' string:\n{code}",
            "debug": f"Debug this code and find potential bugs. Return JSON with 'bugs' array and 'fixes' array:\n{code}",
            "review": f"Perform a comprehensive code review. Return JSON with 'rating' (1-5), 'strengths' array, 'weaknesses' array, and 'suggestions' array:\n{code}"
        }
        
        prompt = prompts.get(analysis_type, prompts["general"])
        result = self.generate(prompt)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"analysis": result, "raw_response": result}
    
    def generate_code(self, requirements: str, language: str = "python", include_explanations: bool = False) -> str:
        """Generate code based on requirements with options"""
        if include_explanations:
            prompt = f"Generate {language} code that:\n{requirements}\n\nInclude explanations for each part."
        else:
            prompt = f"Generate {language} code that:\n{requirements}\n\nProvide only the code without explanations."
        return self.generate(prompt)
    
    def summarize_text(self, text: str, max_length: int = 200, style: str = "concise") -> str:
        """Summarize text with style options"""
        styles = {
            "concise": "brief and to the point",
            "detailed": "comprehensive with key details",
            "bullet": "using bullet points",
            "academic": "formal academic style"
        }
        style_desc = styles.get(style, styles["concise"])
        prompt = f"Summarize the following text in under {max_length} words in a {style_desc} style:\n{text}"
        return self.generate(prompt)
    
    def translate_text(self, text: str, target_language: str = "English", source_language: Optional[str] = None) -> str:
        """Translate text with optional source language"""
        if source_language:
            prompt = f"Translate the following text from {source_language} to {target_language}:\n{text}"
        else:
            prompt = f"Translate the following text to {target_language}:\n{text}"
        return self.generate(prompt)
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        prompt = f"Extract up to {max_keywords} keywords from the following text, return as JSON array:\n{text}"
        result = self.generate(prompt)
        try:
            keywords = json.loads(result)
            return keywords if isinstance(keywords, list) else []
        except json.JSONDecodeError:
            return []
    
    def rewrite_text(self, text: str, tone: str = "professional") -> str:
        """Rewrite text with specified tone"""
        tones = ["professional", "casual", "friendly", "formal", "exciting", "simple"]
        if tone not in tones:
            tone = "professional"
        prompt = f"Rewrite the following text in a {tone} tone:\n{text}"
        return self.generate(prompt)
    
    def get_available_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """Get list of available models grouped by provider"""
        result: Dict[str, List[str]] = {}
        
        if provider is None or provider == "ollama":
            if "ollama" in self.available_providers:
                try:
                    response = self.ollama.list()
                    result["ollama"] = [m['name'] for m in response.get('models', [])]
                except Exception as e:
                    logger.warning(f"Failed to get Ollama models: {e}")
                    result["ollama"] = config.get("ai.providers.ollama.available_models", [])
        
        if provider is None or provider == "openai":
            if "openai" in self.available_providers:
                result["openai"] = config.get("ai.providers.openai.available_models", [])
        
        if provider is None or provider == "anthropic":
            if "anthropic" in self.available_providers:
                result["anthropic"] = config.get("ai.providers.anthropic.available_models", [])
        
        return result
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.available_providers.keys())
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        if self.cache:
            self.cache.clear()
            logger.info("AI cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return {
                "enabled": True,
                "size": len(self.cache.cache),
                "ttl_seconds": self.cache.ttl_seconds
            }
        return {"enabled": False}
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        return {
            "available": self.available,
            "providers": self.get_available_providers(),
            "models": self.get_available_models(),
            "cache": self.get_cache_stats(),
            "version": "3.1.0"
        }

# Global AI service instance
ai_service = AIService()
