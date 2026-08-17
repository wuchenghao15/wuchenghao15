#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎AI引擎实现
支持豆包系列模型（doubao-pro、doubao-lite等）
"""

import json
import time
import logging
import os
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlencode

import requests

logger = logging.getLogger(__name__)


class VolcengineEngine:
    """火山引擎AI引擎实现"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key') or os.environ.get('VOLCENGINE_ACCESS_KEY_ID')
        self.secret_key = self.config.get('secret_key') or os.environ.get('VOLCENGINE_SECRET_ACCESS_KEY')
        self.endpoint = self.config.get('endpoint', 'https://api.volcengine.com')
        self.model_name = self.config.get('model', 'doubao-pro')
        self.max_tokens = self.config.get('max_tokens', 4096)
        self.temperature = self.config.get('temperature', 0.7)
        self.top_p = self.config.get('top_p', 0.9)
        self.top_k = self.config.get('top_k', 50)
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
            "doubao-pro",
            "doubao-lite",
            "doubao-lite-128k",
            "doubao-pro-256k"
        ]

        if self.api_key and self.secret_key:
            self._initialize()

    def _initialize(self):
        """初始化火山引擎客户端"""
        try:
            if not self.api_key or not self.secret_key:
                raise ValueError("AK/SK不能为空")

            self._initialized = True
            logger.info(f"火山引擎初始化成功，模型: {self.model_name}")
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"火山引擎初始化失败: {str(e)}")
            self._initialized = False

    def is_initialized(self) -> bool:
        """检查引擎是否已初始化"""
        return self._initialized

    def _sign_request(self, method: str, path: str, params: Dict = None, body: Dict = None) -> Dict:
        """生成火山引擎API签名"""
        timestamp = str(int(time.time()))
        date = time.strftime("%Y%m%d", time.localtime())

        headers = {
            "Content-Type": "application/json",
            "Host": urlparse(self.endpoint).hostname,
            "X-Date": date,
            "Authorization": ""
        }

        canonical_headers = "content-type:application/json\nhost:" + headers["Host"] + "\n"
        signed_headers = "content-type;host"

        if params:
            query_string = urlencode(sorted(params.items()))
        else:
            query_string = ""

        body_str = json.dumps(body) if body else ""
        body_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

        canonical_request = (
            f"{method}\n"
            f"{path}\n"
            f"{query_string}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{body_hash}"
        )

        credential_scope = f"{date}/volcengineapi/aws4_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n"
            f"{timestamp}\n"
            f"{credential_scope}\n"
            f"{hashed_canonical_request}"
        )

        def hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = hmac_sha256(("AWS4" + self.secret_key).encode("utf-8"), date)
        k_region = hmac_sha256(k_date, "cn-north-1")
        k_service = hmac_sha256(k_region, "volcengineapi")
        k_signing = hmac_sha256(k_service, "aws4_request")

        signature = hmac_sha256(k_signing, string_to_sign).hex()

        authorization = (
            f"AWS4-HMAC-SHA256 Credential={self.api_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers["Authorization"] = authorization
        headers["X-Date"] = timestamp

        return headers

    def _generate_with_retry(self, prompt: str, **kwargs) -> Dict:
        """带重试的生成方法"""
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                return self._generate(prompt, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"火山引擎调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)

        self._last_error = str(last_exception)
        logger.error(f"火山引擎调用最终失败: {str(last_exception)}")
        return self._create_error_response(str(last_exception))

    def _generate(self, prompt: str, **kwargs) -> Dict:
        """生成响应"""
        if not self._initialized:
            if self.api_key and self.secret_key:
                self._initialize()
            else:
                return self._create_error_response("火山引擎未初始化，缺少AK/SK")

        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)

            body = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": self.top_p,
                "top_k": self.top_k
            }

            headers = self._sign_request("POST", "/api/v3/chat/completions", body=body)
            url = f"{self.endpoint}/api/v3/chat/completions"

            response = requests.post(url, headers=headers, json=body, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "response": result["choices"][0]["message"]["content"],
                            "model": self.model_name,
                            "usage": self._extract_usage(result)
                        }
                    }
                else:
                    return self._create_error_response(f"API响应异常: {json.dumps(result)}")
            else:
                return self._create_error_response(f"API错误 [{response.status_code}]: {response.text}")

        except Exception as e:
            raise e

    def _extract_usage(self, response: Dict) -> Dict:
        """提取使用信息"""
        usage = {}
        if "usage" in response:
            usage_data = response["usage"]
            if "prompt_tokens" in usage_data:
                usage["prompt_tokens"] = usage_data["prompt_tokens"]
            if "completion_tokens" in usage_data:
                usage["completion_tokens"] = usage_data["completion_tokens"]
            if "total_tokens" in usage_data:
                usage["total_tokens"] = usage_data["total_tokens"]
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
            if self.api_key and self.secret_key:
                self._initialize()
            else:
                return self._create_error_response("火山引擎未初始化，缺少AK/SK")

        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)

            body = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": self.top_p,
                "top_k": self.top_k
            }

            headers = self._sign_request("POST", "/api/v3/chat/completions", body=body)
            url = f"{self.endpoint}/api/v3/chat/completions"

            response = requests.post(url, headers=headers, json=body, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "response": result["choices"][0]["message"]["content"],
                            "model": self.model_name,
                            "usage": self._extract_usage(result)
                        }
                    }
                else:
                    return self._create_error_response(f"API响应异常: {json.dumps(result)}")
            else:
                return self._create_error_response(f"API错误 [{response.status_code}]: {response.text}")

        except Exception as e:
            logger.error(f"火山引擎聊天模式失败: {str(e)}")
            return self._create_error_response(str(e))

    def generate_stream(self, prompt: str, **kwargs):
        """流式生成响应"""
        if not self._initialized:
            if self.api_key and self.secret_key:
                self._initialize()
            else:
                yield self._create_error_response("火山引擎未初始化，缺少AK/SK")
                return

        try:
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)

            body = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "stream": True
            }

            headers = self._sign_request("POST", "/api/v3/chat/completions", body=body)
            url = f"{self.endpoint}/api/v3/chat/completions"

            with requests.post(url, headers=headers, json=body, timeout=self.timeout, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                line = line[6:]
                                if line.strip() == "[DONE]":
                                    break
                                try:
                                    result = json.loads(line)
                                    if "choices" in result and len(result["choices"]) > 0:
                                        content = result["choices"][0]["delta"].get("content", "")
                                        is_finished = result["choices"][0].get("finish_reason") is not None
                                        yield {
                                            "code": 0,
                                            "message": "success",
                                            "data": {
                                                "response": content,
                                                "model": self.model_name,
                                                "is_finished": is_finished
                                            }
                                        }
                                except json.JSONDecodeError:
                                    continue
                else:
                    yield self._create_error_response(f"API错误 [{response.status_code}]: {response.text}")

        except Exception as e:
            logger.error(f"火山引擎流式生成失败: {str(e)}")
            yield self._create_error_response(str(e))

    def embed(self, text: str, **kwargs) -> Dict:
        """生成文本嵌入"""
        try:
            body = {
                "model": "text-embedding",
                "input": text
            }

            headers = self._sign_request("POST", "/api/v3/embeddings", body=body)
            url = f"{self.endpoint}/api/v3/embeddings"

            response = requests.post(url, headers=headers, json=body, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "embedding": result["data"][0]["embedding"],
                            "model": "text-embedding"
                        }
                    }
                else:
                    return self._create_error_response(f"嵌入API响应异常: {json.dumps(result)}")
            else:
                return self._create_error_response(f"嵌入API错误 [{response.status_code}]: {response.text}")

        except Exception as e:
            logger.error(f"火山引擎嵌入生成失败: {str(e)}")
            return self._create_error_response(str(e))

    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._initialized:
                return False

            response = self.generate("Hello", max_tokens=10)
            return response["code"] == 0
        except Exception as e:
            logger.error(f"火山引擎健康检查失败: {str(e)}")
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
            "endpoint": self.endpoint,
            "timeout": self.timeout,
            "initialized": self._initialized
        }

    def update_config(self, config: Dict):
        """更新配置"""
        self.config.update(config)
        self.api_key = self.config.get('api_key', self.api_key) or os.environ.get('VOLCENGINE_ACCESS_KEY_ID')
        self.secret_key = self.config.get('secret_key', self.secret_key) or os.environ.get('VOLCENGINE_SECRET_ACCESS_KEY')
        self.endpoint = self.config.get('endpoint', self.endpoint)
        self.model_name = self.config.get('model', self.model_name)
        self.max_tokens = self.config.get('max_tokens', self.max_tokens)
        self.temperature = self.config.get('temperature', self.temperature)
        self.top_p = self.config.get('top_p', self.top_p)
        self.top_k = self.config.get('top_k', self.top_k)
        self.timeout = self.config.get('timeout', self.timeout)
        self.retry_count = self.config.get('retry_count', self.retry_count)

        if self.api_key and self.secret_key:
            self._initialize()


def create_volcengine_engine(config: Dict = None) -> VolcengineEngine:
    """创建火山引擎实例"""
    return VolcengineEngine(config)


def init_volcengine_engine(api_key: str, secret_key: str, model: str = "doubao-pro") -> VolcengineEngine:
    """初始化火山引擎"""
    config = {
        "api_key": api_key,
        "secret_key": secret_key,
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60,
        "retry_count": 3
    }
    return VolcengineEngine(config)