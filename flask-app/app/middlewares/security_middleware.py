# -*- coding: utf-8 -*-
# 安全中间件,用于增强系统安全性
from flask import request, g
from app.utils.logging import logger
from datetime import datetime

# 安全头中间件
def security_headers_middleware(app):
    """设置安全头,增强系统安全性"""
    @app.after_request
    def add_security_headers(response):
        # 防止点击劫持攻击
        response.headers['X-Frame-Options'] = 'DENY'

        # 防止XSS攻击
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # 防止MIME类型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # 启用严格的传输安全
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # 内容安全策略
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-src 'none';"

        # 引用策略
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 权限策略
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # 跨域资源共享策略
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'

        return response
    logger.info("安全头中间件已注册")

# 安全事件日志中间件
def security_event_logger_middleware(app):
    """记录安全事件,用于审计和监控"""
    @app.before_request
    def log_security_event():
        # 记录所有请求
        g.request_start_time = datetime.now()
        logger.info(f"安全事件: 请求开始 - IP: {request.remote_addr}, 方法: {request.method}, URL: {request.url}, 用户代理: {request.user_agent}")

    def log_security_event_after(response):
        # 记录请求结束
        request_time = (datetime.now() - g.request_start_time).total_seconds() * 1000
        logger.info(f"安全事件: 请求结束 - IP: {request.remote_addr}, 方法: {request.method}, URL: {request.url}, 状态码: {response.status_code}, 响应时间: {request_time:.2f}ms")
        return response

# 速率限制中间件
def rate_limiter_middleware(app):
    """简单的速率限制中间件,防止API滥用"""
    # 存储IP地址和请求计数
    rate_limit_store = {}
    
    # 本地IP白名单 - 完全跳过速率限制
    LOCAL_IPS = ['127.0.0.1', 'localhost', '::1']

    @app.before_request
    def rate_limit():
        ip = request.remote_addr
        
        # 本地IP完全跳过速率限制
        if ip in LOCAL_IPS:
            return None
        
        current_time = datetime.now().timestamp()

        # 初始化IP记录
        if ip not in rate_limit_store:
            rate_limit_store[ip] = {
                'requests': [],
                'last_cleanup': current_time
            }

        # 清理旧的请求记录(保留1分钟内的请求)
        cleanup_time = current_time - 60
        rate_limit_store[ip]['requests'] = [r for r in rate_limit_store[ip]['requests'] if r > cleanup_time]

        # 检查速率限制(每分钟最多100个请求)
        if len(rate_limit_store[ip]['requests']) >= 100:
            logger.warning(f"速率限制: IP {ip} 超过了请求限制")
            return '速率限制已达上限,请稍后再试', 429

        # 记录当前请求
        rate_limit_store[ip]['requests'].append(current_time)

    logger.info("速率限制中间件已注册")

# 增强的CSRF保护中间件
def enhanced_csrf_middleware(app):
    """增强的CSRF保护中间件"""
    @app.before_request
    def csrf_protection():
        if request.path.startswith('/api/'):
            return None
        
        if request.method in ['POST', 'PUT', 'DELETE']:
            # 检查CSRF令牌
            csrf_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
            if not csrf_token:
                logger.warning(f"CSRF保护: 缺少CSRF令牌 - IP: {request.remote_addr}, 方法: {request.method}, URL: {request.url}")
                from flask import jsonify
                return jsonify({'status': 'error', 'message': 'CSRF令牌缺失'}), 403

            # 验证CSRF令牌
            from app.utils.security import security_utils
            if not security_utils.verify_csrf_token(csrf_token):
                logger.warning(f"CSRF保护: 无效的CSRF令牌 - IP: {request.remote_addr}, 方法: {request.method}, URL: {request.url}")
                from flask import jsonify
                return jsonify({'status': 'error', 'message': 'CSRF令牌无效'}), 403

    logger.info("增强的CSRF保护中间件已注册")

# 安全中间件优先级
security_headers_middleware_priority = 10
security_event_logger_middleware_priority = 20
rate_limiter_middleware_priority = 30
enhanced_csrf_middleware_priority = 40
