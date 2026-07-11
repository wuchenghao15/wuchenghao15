#!/usr/bin/env python3
"""
监控中间件 - 拦截所有请求并记录接入日志
"""

import time
from flask import request, after_this_request
from ..services.client_monitor_service import log_access, check_brute_force, check_rate_limit, check_session_hijacking


class ClientMonitorMiddleware:
    """客户端监控中间件"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.errorhandler(Exception)(self.handle_exception)
    
    def before_request(self):
        """请求处理前"""
        request.start_time = time.time()
        
        ip_address = request.remote_addr
        session_id = request.cookies.get('session_id', '')
        
        check_rate_limit(ip_address)
        
        if session_id:
            check_session_hijacking(session_id)
    
    def after_request(self, response):
        """请求处理后"""
        response_time = time.time() - getattr(request, 'start_time', time.time())
        
        request_size = len(request.get_data()) if request.get_data() else 0
        
        try:
            response_size = len(response.data) if response.data else 0
        except RuntimeError:
            response_size = 0
        
        log_access(
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            response_time=round(response_time, 4),
            request_size=request_size,
            response_size=response_size
        )
        
        return response
    
    def handle_exception(self, error):
        """异常处理"""
        ip_address = request.remote_addr
        
        from ..services.client_monitor_service import log_anomaly
        
        log_anomaly(
            client_id='',
            ip_address=ip_address,
            anomaly_type='request_error',
            message=f'请求异常: {str(error)}',
            details={
                'endpoint': request.path,
                'method': request.method,
                'error': str(error),
                'status_code': getattr(error, 'code', 500)
            },
            severity='high'
        )
        
        from flask import jsonify
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误',
            'error': str(error)
        }), getattr(error, 'code', 500)
