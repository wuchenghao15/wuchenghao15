#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP协议实现模块
提供HTTP/HTTPS协议的客户端和服务端支持
"""

import requests
import json
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin
from app.utils.logging import logger


class HTTPProtocol:
    """HTTP协议实现类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session.headers.update(self.default_headers)
        
        # 重试配置
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 0.3,
            'status_forcelist': [500, 502, 503, 504]
        }
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }
    
    def set_headers(self, headers: Dict[str, str]):
        """设置默认请求头"""
        self.session.headers.update(headers)
    
    def set_timeout(self, timeout: int):
        """设置超时时间"""
        self.timeout = timeout
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """计算重试退避时间"""
        return self.retry_config['backoff_factor'] * (2 ** retry_count)
    
    def request(self, method: str, url: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE, PATCH)
            url: 请求URL
            **kwargs: 其他参数 (headers, data, json, params, timeout等)
        
        Returns:
            元组 (状态码, 响应数据)
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        retry_count = 0
        max_retries = self.retry_config['max_retries']
        status_forcelist = self.retry_config['status_forcelist']
        
        while retry_count <= max_retries:
            try:
                response = self.session.request(method=method, url=url, **kwargs)
                
                response_time = time.time() - start_time
                self.stats['total_response_time'] += response_time
                
                if response.status_code in [200, 201, 204]:
                    self.stats['successful_requests'] += 1
                    self.stats['avg_response_time'] = (
                        self.stats['total_response_time'] / self.stats['successful_requests']
                    )
                    
                    if response.text:
                        try:
                            return response.status_code, response.json()
                        except json.JSONDecodeError:
                            return response.status_code, {'content': response.text}
                    return response.status_code, {'success': True}
                
                elif response.status_code in status_forcelist:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = self._calculate_backoff(retry_count)
                        logger.warning(f"HTTP请求失败，状态码: {response.status_code}，重试第 {retry_count} 次，等待 {wait_time:.2f} 秒")
                        time.sleep(wait_time)
                        continue
                
                # 其他错误状态码
                self.stats['failed_requests'] += 1
                logger.error(f"HTTP请求失败，状态码: {response.status_code}，URL: {url}")
                return response.status_code, {'error': response.text}
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = self._calculate_backoff(retry_count)
                    logger.warning(f"HTTP请求异常: {str(e)}，重试第 {retry_count} 次，等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
                    continue
                
                self.stats['failed_requests'] += 1
                logger.error(f"HTTP请求最终失败: {str(e)}，URL: {url}")
                return 0, {'error': str(e)}
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送GET请求"""
        return self.request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送POST请求"""
        return self.request('POST', url, json=data, **kwargs)
    
    def put(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送PUT请求"""
        return self.request('PUT', url, json=data, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送PATCH请求"""
        return self.request('PATCH', url, json=data, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }
    
    def close(self):
        """关闭会话"""
        self.session.close()


class HTTPClient:
    """HTTP客户端封装类"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url
        self.protocol = HTTPProtocol()
        
        if api_key:
            self.protocol.set_headers({'X-API-Key': api_key})
    
    def request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Dict[str, Any]]:
        """发送请求"""
        url = urljoin(self.base_url, endpoint) if self.base_url else endpoint
        return self.protocol.request(method, url, **kwargs)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs):
        """发送GET请求"""
        return self.request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        """发送POST请求"""
        return self.request('POST', endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        """发送PUT请求"""
        return self.request('PUT', endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs):
        """发送DELETE请求"""
        return self.request('DELETE', endpoint, **kwargs)
    
    def get_stats(self):
        """获取统计信息"""
        return self.protocol.get_stats()
