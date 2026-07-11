# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
API中间件模块,实现API性能优化,安全措施和错误处理
"""

from flask import Flask, request, g, jsonify
import time
import uuid
from app.utils.logging import logger
import logging
import json


class RateLimiter:
    """简单的速率限制器"""

    def __init__(self, max_requests=100, window_seconds=60):
        """初始化速率限制器

        Args:
            max_requests: 时间窗口内的最大请求数
            window_seconds: 时间窗口大小(秒)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        self.local_ips = ['127.0.0.1', 'localhost', '::1']

    def allow_request(self, client_ip):
        """检查是否允许请求

        Args:
            client_ip: 客户端IP地址

        Returns:
            bool: 是否允许请求
        """
        # 本地IP完全跳过速率限制
        if client_ip in self.local_ips:
            return True
        
        current_time = time.time()

        # 清理过期的请求记录
        if client_ip in self.requests:
            # 过滤出时间窗口内的请求
            self.requests[client_ip] = [t for t in self.requests[client_ip]
                                      if current_time - t < self.window_seconds]
        else:
            self.requests[client_ip] = []

        # 检查请求数是否超过限制
        if len(self.requests[client_ip]) < self.max_requests:
            # 添加当前请求时间
            self.requests[client_ip].append(current_time)
            return True
        else:
            return False


class APIMiddleware:
    """API中间件类"""

    def __init__(self, app):
        """初始化中间件

        Args:
            app: Flask应用实例
        """
        self.app = app
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.setup_middleware()

    def setup_middleware(self):
        """设置中间件"""
        # 注册请求前中间件
        self.app.before_request(self.before_request)

        # 注册请求后中间件
        self.app.after_request(self.after_request)

        # 注册错误处理中间件
        self.app.errorhandler(404)(self.handle_404)
        self.app.errorhandler(403)(self.handle_403)
        self.app.errorhandler(429)(self.handle_429)
        self.app.errorhandler(Exception)(self.handle_exception)

    def before_request(self):
        """请求前处理"""
        # 生成请求ID
        g.request_id = str(uuid.uuid4())

        # 记录请求开始时间
        g.start_time = time.time()

        # 记录请求信息
        logger.info(f"[API] 开始请求: {request.method} {request.path}")

        # 检查请求方法
        if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']:
            return jsonify({
                'success': False,
                'error': '不支持的请求方法'
            }), 405

        # 检查内容类型
        if request.method in ['POST', 'PUT'] and request.is_json:
            try:
                # 预解析JSON数据
                request.json
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': '无效的JSON数据'
                }), 400

        # 速率限制
        client_ip = request.remote_addr
        if not self.rate_limiter.allow_request(client_ip):
            return jsonify({
                'success': False,
                'error': '请求过于频繁,请稍后重试'
            }), 429

        self._security_checks()

    def after_request(self, response):
        """请求后处理"""
        # 计算响应时间
        response_time = time.time() - g.start_time

        # 添加响应头
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        response.headers['X-API-Version'] = "v1"
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers['Access-Control-Allow-Headers'] = "Content-Type, X-Request-ID, X-API-Key, X-Session-ID"

        # 记录响应信息
        logger.info(f"[API] 请求完成: {request.method} {request.path} {response.status_code} {response_time:.3f}s")

        return response

    def _security_checks(self):
        """安全检查"""
        # 检查请求来源
        referer = request.headers.get('Referer')
        if referer:
            logger.debug(f"[API] 请求来源: {referer}")

        # 检查用户代理
        user_agent = request.headers.get('User-Agent')
        if user_agent:
            logger.debug(f"[API] 用户代理: {user_agent}")

        # 检查API密钥
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # 这里可以添加API密钥验证逻辑
            pass

        # 检查会话ID
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            # 这里可以添加会话验证逻辑
            pass

    def handle_404(self, error):
        """处理404错误"""
        return jsonify({
            'success': False,
            'error': '请求的资源不存在'
        }), 404

    def handle_403(self, error):
        """处理403错误"""
        return jsonify({
            'success': False,
            'error': '无权访问该资源'
        }), 403

    def handle_429(self, error):
        """处理429错误"""
        return jsonify({
            'success': False,
            'error': '请求过于频繁,请稍后重试'
        }), 429

    def handle_exception(self, error):
        """处理所有异常"""
        # 记录错误信息
        logger.error(f"[API] 未处理的异常: {str(error)}")

        # 返回统一的错误响应
        return jsonify({
            'success': False,
            'error': '服务器内部错误'
        }), 500
