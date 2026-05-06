# -*- coding: utf-8 -*-
# User Management Client - 用于主系统调用用户管理服务器
import requests
# JSON import removed - using database
import time
import hashlib
from app.utils.logging import logger

class UserManagementClient:
    """用户管理服务客户端"""

    def __init__(self, base_url='http://localhost:5001', api_key=None):
        """
        初始化用户管理客户端

        Args:
            base_url: 用户管理服务器基础URL
            api_key: 访问API密钥
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['X-API-Key'] = api_key

        # 配置会话，启用连接池
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 缓存机制
        self.cache = {
            'users': {},  # 用户缓存
            'last_refresh': 0  # 上次刷新时间
        }

        # 重试配置
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 0.3,
            'status_forcelist': [500, 502, 503, 504]
        }
        # 状态统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    def _make_request(self, endpoint, method='GET', data=None, timeout=2):
        发送HTTP请求到用户管理服务器，带重试机制

        Args:
            endpoint: API端点路径
            method: 请求方法 (GET, POST, PUT, DELETE)
            data: 请求数据
            timeout: 请求超时时间

        Returns:
            dict: 响应数据
        url = f"{self.base_url}{endpoint}"
        retry_count = 0
        backoff_factor = self.retry_config['backoff_factor']
        max_retries = self.retry_config['max_retries']
        status_forcelist = self.retry_config['status_forcelist']

        # 更新请求统计
        self.stats['total_requests'] += 1

        while retry_count <= max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=timeout
                )

                # 记录请求日志
                logger.info(f"User Management API Request: {method} {url} -> Status: {response.status_code}")

                # 解析响应
                if response.status_code in [200, 201, 204]:
                    self.stats['successful_requests'] += 1
                    if response.text:
                        return response.json()
                    return {'success': True}
                elif response.status_code in status_forcelist and retry_count < max_retries:
                    # 需要重试的状态码
                    retry_count += 1
                    wait_time = backoff_factor * (2 ** (retry_count - 1))
                    logger.warning(f"Request failed with status {response.status_code}, retrying in {wait_time:.2f}s... ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # 不需要重试的错误响应
                    self.stats['failed_requests'] += 1
                    error_msg = f"User Management API Error: {response.status_code} - {response.text}"
                    logger.warning(error_msg)  # 使用warning级别，避免错误日志过于频繁
                    return {
                        'success': False,
                        'error': error_msg,
                        'status_code': response.status_code
                    }
            except requests.exceptions.RequestException as e:
                retry_count += 1
                    # 网络异常，重试
                    wait_time = backoff_factor * (2 ** (retry_count - 1))
                    logger.warning(f"Request exception: {str(e)}, retrying in {wait_time:.2f}s... ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                    # 重试次数耗尽
                    self.stats['failed_requests'] += 1
                    error_msg = f"User Management API Request Failed: {str(e)}"
                    return {
                        'success': False,
                    }
    def _refresh_cache(self):
        if current_time - self.cache['last_refresh'] > self.cache_ttl:
            logger.info("Refreshing user cache...")
            if users_result.get('success'):
                self.cache['users'] = {user['id']: user for user in users_result.get('users', [])}
                logger.info(f"Cache refreshed, {len(self.cache['users'])} users cached")
    def _get_cache_key(self, endpoint, method, data=None):
        cache_key_data = f"{method}:{endpoint}:{str(data) if data else ''}"
        return hashlib.md5(cache_key_data.encode()).hexdigest()

    def _clear_cache(self):
        """清除缓存"""
        logger.info("Clearing user cache...")
        self.cache = {
            'users': {},
            'last_refresh': 0
        }

    def get_stats(self):
        return self.stats

    def create_user(self, username, email, password, role='user'):
        创建用户，创建后清除缓存

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 角色

        Returns:
            dict: 响应数据
        data = {
            'username': username,
            'email': email,
            'password': password,
            'role': role
        }
        result = self._make_request('/api/users', method='POST', data=data)
        if result.get('success'):
            # 创建成功，清除缓存
            self._clear_cache()
    def get_user(self, user_id):
        获取用户信息，使用缓存

        Args:
            user_id: 用户ID

        Returns:
            dict: 响应数据
        # 先检查缓存
        self._refresh_cache()
        if user_id in self.cache['users']:
            self.stats['cache_hits'] += 1
            return {
                'success': True,
                'user': self.cache['users'][user_id]
            }

        # 缓存未命中，从服务器获取
        self.stats['cache_misses'] += 1
        result = self._make_request(f'/api/users/{user_id}', method='GET')
        if result.get('success'):
        return result

    def get_all_users(self):
        获取所有用户，使用缓存

        Returns:
            dict: 响应数据
        # 先检查缓存
        self._refresh_cache()
        if self.cache['users']:
            self.stats['cache_hits'] += 1
            return {
                'success': True,
                'users': list(self.cache['users'].values())

        # 缓存未命中，从服务器获取
        self.stats['cache_misses'] += 1
        return self._make_request('/api/users', method='GET')

    def update_user(self, user_id, **kwargs):
        更新用户信息，更新后清除缓存

            **kwargs: 用户属性（username, email, password, role, is_active, avatar）

            dict: 响应数据
        result = self._make_request(f'/api/users/{user_id}', method='PUT', data=kwargs)
        if result.get('success'):
            self._clear_cache()
        return result

    def delete_user(self, user_id):
        删除用户，删除后清除缓存

        Args:
            user_id: 用户ID
        Returns:
        result = self._make_request(f'/api/users/{user_id}', method='DELETE')
            # 删除成功，清除缓存
            self._clear_cache()
    # 认证方法
    def login(self, username, password):

        Args:
            username: 用户名
            password: 密码
        Returns:
        data = {
            'username': username,
        }
        return self._make_request('/api/auth/login', method='POST', data=data)
    def verify_token(self, token):
        验证JWT令牌
        Args:
            token: JWT令牌

            dict: 响应数据，包含用户信息
        return self._make_request('/api/auth/verify', method='POST', data=data)

    # API密钥管理方法
        创建API密钥

        Args:
            description: API密钥描述
            expires_at: 过期时间（ISO格式字符串）
            dict: 响应数据，包含生成的API密钥
        data = {
            'description': description
        }
            data['expires_at'] = expires_at
        return self._make_request('/api/keys', method='POST', data=data)
    def get_api_keys(self):
        获取所有API密钥
        Returns:
        return self._make_request('/api/keys', method='GET')

    # 健康检查
    def health_check(self):
        检查用户管理服务健康状态
        Returns:
        return self._make_request('/health', method='GET')
# 全局用户管理客户端实例
# 在应用初始化时配置和使用
user_management_client = None


def init_user_management_client(base_url='http://localhost:5001', api_key=None):
    初始化全局用户管理客户端

    Args:
        base_url: 用户管理服务器基础URL
        api_key: 访问API密钥

    Returns:
        UserManagementClient: 用户管理客户端实例
    global user_management_client
    user_management_client = UserManagementClient(base_url=base_url, api_key=api_key)
    logger.info(f"User Management Client initialized with base URL: {base_url}")
    return user_management_client


def get_user_management_client():
    获取全局用户管理客户端实例

    Returns:
        UserManagementClient: 用户管理客户端实例
    if not user_management_client:
        logger.error("User Management Client not initialized. Call init_user_management_client() first.")
    return user_management_client
