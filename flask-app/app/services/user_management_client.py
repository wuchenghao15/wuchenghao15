# User Management Client - 用于主系统调用用户管理服务器
import requests
import json
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
        """
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
        self.cache_ttl = 300  # 缓存有效期（秒）
        
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
        """
        发送HTTP请求到用户管理服务器，带重试机制
        
        Args:
            endpoint: API端点路径
            method: 请求方法 (GET, POST, PUT, DELETE)
            data: 请求数据
            timeout: 请求超时时间
        
        Returns:
            dict: 响应数据
        """
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
                if retry_count <= max_retries:
                    # 网络异常，重试
                    wait_time = backoff_factor * (2 ** (retry_count - 1))
                    logger.warning(f"Request exception: {str(e)}, retrying in {wait_time:.2f}s... ({retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # 重试次数耗尽
                    self.stats['failed_requests'] += 1
                    error_msg = f"User Management API Request Failed: {str(e)}"
                    logger.warning(error_msg)  # 使用warning级别，避免错误日志过于频繁
                    return {
                        'success': False,
                        'error': error_msg
                    }
    
    def _refresh_cache(self):
        """刷新缓存"""
        current_time = time.time()
        if current_time - self.cache['last_refresh'] > self.cache_ttl:
            logger.info("Refreshing user cache...")
            users_result = self._make_request('/api/users', method='GET')
            if users_result.get('success'):
                self.cache['users'] = {user['id']: user for user in users_result.get('users', [])}
                self.cache['last_refresh'] = current_time
                logger.info(f"Cache refreshed, {len(self.cache['users'])} users cached")
    
    def _get_cache_key(self, endpoint, method, data=None):
        """生成缓存键"""
        cache_key_data = f"{method}:{endpoint}:{json.dumps(data) if data else ''}"
        return hashlib.md5(cache_key_data.encode()).hexdigest()
    
    def _clear_cache(self):
        """清除缓存"""
        logger.info("Clearing user cache...")
        self.cache = {
            'users': {},
            'last_refresh': 0
        }
    
    def get_stats(self):
        """获取客户端统计信息"""
        return self.stats
    
    # 用户管理方法
    def create_user(self, username, email, password, role='user'):
        """
        创建用户，创建后清除缓存
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 角色
        
        Returns:
            dict: 响应数据
        """
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
        return result
    
    def get_user(self, user_id):
        """
        获取用户信息，使用缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 响应数据
        """
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
            # 更新缓存
            self.cache['users'][user_id] = result.get('user')
        return result
    
    def get_all_users(self):
        """
        获取所有用户，使用缓存
        
        Returns:
            dict: 响应数据
        """
        # 先检查缓存
        self._refresh_cache()
        if self.cache['users']:
            self.stats['cache_hits'] += 1
            return {
                'success': True,
                'users': list(self.cache['users'].values())
            }
        
        # 缓存未命中，从服务器获取
        self.stats['cache_misses'] += 1
        return self._make_request('/api/users', method='GET')
    
    def update_user(self, user_id, **kwargs):
        """
        更新用户信息，更新后清除缓存
        
        Args:
            user_id: 用户ID
            **kwargs: 用户属性（username, email, password, role, is_active, avatar）
        
        Returns:
            dict: 响应数据
        """
        result = self._make_request(f'/api/users/{user_id}', method='PUT', data=kwargs)
        if result.get('success'):
            # 更新成功，清除缓存
            self._clear_cache()
        return result
    
    def delete_user(self, user_id):
        """
        删除用户，删除后清除缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 响应数据
        """
        result = self._make_request(f'/api/users/{user_id}', method='DELETE')
        if result.get('success'):
            # 删除成功，清除缓存
            self._clear_cache()
        return result
    
    # 认证方法
    def login(self, username, password):
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            dict: 响应数据，包含token和用户信息
        """
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('/api/auth/login', method='POST', data=data)
    
    def verify_token(self, token):
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
        
        Returns:
            dict: 响应数据，包含用户信息
        """
        data = {'token': token}
        return self._make_request('/api/auth/verify', method='POST', data=data)
    
    # API密钥管理方法
    def create_api_key(self, description='', expires_at=None):
        """
        创建API密钥
        
        Args:
            description: API密钥描述
            expires_at: 过期时间（ISO格式字符串）
        
        Returns:
            dict: 响应数据，包含生成的API密钥
        """
        data = {
            'description': description
        }
        if expires_at:
            data['expires_at'] = expires_at
        return self._make_request('/api/keys', method='POST', data=data)
    
    def get_api_keys(self):
        """
        获取所有API密钥
        
        Returns:
            dict: 响应数据，包含所有API密钥
        """
        return self._make_request('/api/keys', method='GET')
    
    # 健康检查
    def health_check(self):
        """
        检查用户管理服务健康状态
        
        Returns:
            dict: 响应数据，包含服务状态
        """
        return self._make_request('/health', method='GET')

# 全局用户管理客户端实例
# 在应用初始化时配置和使用
user_management_client = None


def init_user_management_client(base_url='http://localhost:5001', api_key=None):
    """
    初始化全局用户管理客户端
    
    Args:
        base_url: 用户管理服务器基础URL
        api_key: 访问API密钥
    
    Returns:
        UserManagementClient: 用户管理客户端实例
    """
    global user_management_client
    user_management_client = UserManagementClient(base_url=base_url, api_key=api_key)
    logger.info(f"User Management Client initialized with base URL: {base_url}")
    return user_management_client


def get_user_management_client():
    """
    获取全局用户管理客户端实例
    
    Returns:
        UserManagementClient: 用户管理客户端实例
    """
    if not user_management_client:
        logger.error("User Management Client not initialized. Call init_user_management_client() first.")
        raise RuntimeError("User Management Client not initialized")
    return user_management_client