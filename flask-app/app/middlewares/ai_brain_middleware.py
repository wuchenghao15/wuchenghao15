# -*- coding: utf-8 -*-
# AI脑库中间件

import logging
from flask import request, g
import time

logger = logging.getLogger(__name__)

class AIBrainMiddleware:
    """AI脑库中间件类"""
    
    @staticmethod
    def request_logger(app):
        """请求日志记录中间件"""
        @app.before_request
        def log_request():
            g.start_time = time.time()
            logger.info(f"[AI脑库] 请求开始: {request.method} {request.path}")
        
        @app.after_request
        def log_response(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                logger.info(f"[AI脑库] 请求完成: {request.method} {request.path} - {response.status_code} ({duration:.2f}ms)")
            return response
        
        return app
    
    @staticmethod
    def response_logger(app):
        """响应日志记录中间件"""
        @app.after_request
        def log_response_details(response):
            logger.debug(f"[AI脑库] 响应详情: {response.status}, Content-Type: {response.content_type}")
            return response
        
        return app
    
    @staticmethod
    def api_rate_limiter(app):
        """API限流中间件"""
        @app.before_request
        def rate_limit():
            pass
        return app
    
    @staticmethod
    def cors_middleware(app):
        """CORS中间件"""
        @app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        return app


def init_ai_brain_middleware(app):
    """初始化AI大脑中间件"""
    AIBrainMiddleware.request_logger(app)
    AIBrainMiddleware.response_logger(app)
    AIBrainMiddleware.api_rate_limiter(app)
    AIBrainMiddleware.cors_middleware(app)
    logger.info("AI大脑中间件已注册")
    return app