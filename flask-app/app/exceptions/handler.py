# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
统一异常处理中间件

功能：
1. 捕获所有请求异常
2. 区分业务异常和系统异常
3. 根据AI决策引擎决定跳转页面
4. 返回统一格式的响应
5. 记录详细日志
"""

import logging
import uuid
from datetime import datetime
from typing import Dict
from flask import request, jsonify, render_template, redirect, session
from app.exceptions import (
    AppException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    ResourceNotFoundException,
    BusinessException,
    QuotaException,
    TimeoutException,
    IntegrationException,
    ConcurrencyException,
    ErrorCategory
)

logger = logging.getLogger(__name__)


def _get_ai_analysis(error: Exception, error_code: int, error_message: str, 
                     request_info: Dict) -> Dict:
    """获取AI错误分析"""
    try:
        from app.services.ai_error_analysis_service import analyze_error
        return analyze_error(error, error_code, error_message, request_info)
    except Exception as e:
        logger.warning(f"AI错误分析调用失败: {e}")
        return {'analyzed': False, 'items': []}


class ExceptionHandler:
    """统一异常处理中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        app.errorhandler(Exception)(self.handle_exception)
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(401, self.handle_unauthorized)
        app.register_error_handler(403, self.handle_forbidden)
        app.register_error_handler(404, self.handle_not_found)
        app.register_error_handler(409, self.handle_conflict)
        app.register_error_handler(429, self.handle_rate_limit)
        app.register_error_handler(500, self.handle_internal_error)
        app.register_error_handler(502, self.handle_bad_gateway)
        app.register_error_handler(504, self.handle_gateway_timeout)
        
        logger.info("✓ 统一异常处理中间件已注册")
    
    def handle_exception(self, error):
        """处理所有异常"""
        error_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        request_info = self._get_request_info()
        
        if isinstance(error, AppException):
            return self._handle_app_exception(error, request_info)
        else:
            return self._handle_system_exception(error, error_id, timestamp, request_info)
    
    def _get_request_info(self) -> dict:
        """获取请求信息"""
        return {
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string.decode('utf-8') if request.query_string else '',
            'headers': {k: v for k, v in request.headers.items() if k not in ['Cookie', 'Authorization']},
            'client_ip': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else '',
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
    
    def _handle_app_exception(self, exc: AppException, request_info: dict):
        """处理业务异常"""
        logger.log(
            getattr(logging, exc.log_level.upper(), logging.ERROR),
            f"业务异常 [{exc.error_id}]: {exc.message} | 分类: {exc.category} | 请求: {request_info['method']} {request_info['path']}"
        )
        
        response_data = exc.to_dict()
        
        if self._is_api_request():
            return jsonify(response_data), exc.error_code
        else:
            redirect_url = self._determine_redirect(exc)
            if redirect_url:
                return redirect(redirect_url)
            
            return render_template(
                'unified_error.html',
                **self._build_error_template_context(exc)
            ), exc.error_code
    
    def _handle_system_exception(self, error: Exception, error_id: str, timestamp: str, request_info: dict):
        """处理系统异常"""
        logger.error(
            f"系统异常 [{error_id}]: {str(error)} | 请求: {request_info['method']} {request_info['path']}",
            exc_info=True
        )
        
        response_data = {
            'success': False,
            'error_id': error_id,
            'timestamp': timestamp,
            'error_code': 500,
            'error_type': 'system_error',
            'category': 'unknown',
            'message': '系统内部错误，请稍后重试',
            'suggestion': '如果问题持续存在，请联系管理员',
            'details': {}
        }
        
        if self._is_api_request():
            return jsonify(response_data), 500
        else:
            redirect_url = self._determine_redirect_for_system_error()
            if redirect_url:
                return redirect(redirect_url)
            
            return render_template(
                'unified_error.html',
                **self._build_system_error_template_context(error_id, timestamp, str(error))
            ), 500
    
    def _is_api_request(self) -> bool:
        """判断是否为API请求"""
        path = request.path.lower()
        return path.startswith('/api/') or \
               path.startswith('/auth/') and request.method == 'POST' or \
               request.headers.get('Accept') == 'application/json' or \
               request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    def _determine_redirect(self, exc: AppException) -> str:
        """根据异常类型决定跳转页面（AI决策）"""
        if exc.redirect_url:
            return exc.redirect_url
        
        from app.exceptions.ai_decision_engine import AIDecisionEngine
        return AIDecisionEngine.determine_redirect(exc, request)
    
    def _determine_redirect_for_system_error(self) -> str:
        """系统错误跳转决策（AI决策）"""
        from app.exceptions.ai_decision_engine import AIDecisionEngine
        return AIDecisionEngine.determine_redirect_for_system_error(request)
    
    def _build_error_template_context(self, exc: AppException) -> dict:
        """构建错误页面模板上下文"""
        request_info = self._get_request_info()
        ai_analysis = _get_ai_analysis(exc, exc.error_code, exc.message, request_info)
        
        return {
            'error_id': exc.error_id,
            'error_code': exc.error_code,
            'error_title': self._get_error_title(exc.error_code),
            'error_message': exc.message,
            'error_type': exc.error_type,
            'category': exc.category,
            'suggestion': exc.suggestion,
            'timestamp': exc.timestamp,
            'redirect_url': exc.redirect_url,
            'details': exc.details,
            'request_info': request_info,
            'is_app_exception': True,
            'ai_analysis': ai_analysis
        }
    
    def _build_system_error_template_context(self, error_id: str, timestamp: str, message: str) -> dict:
        """构建系统错误页面模板上下文"""
        request_info = self._get_request_info()
        ai_analysis = _get_ai_analysis(Exception(message), 500, message, request_info)
        
        return {
            'error_id': error_id,
            'error_code': 500,
            'error_title': '系统内部错误',
            'error_message': '系统内部错误，请稍后重试',
            'error_type': 'system_error',
            'category': 'unknown',
            'suggestion': '如果问题持续存在，请联系管理员',
            'timestamp': timestamp,
            'redirect_url': None,
            'details': {'original_error': message},
            'request_info': request_info,
            'is_app_exception': False,
            'ai_analysis': ai_analysis
        }
    
    def _get_error_title(self, error_code: int) -> str:
        """根据错误码获取错误标题"""
        titles = {
            400: '请求错误',
            401: '未授权',
            403: '禁止访问',
            404: '资源不存在',
            409: '冲突',
            429: '请求频繁',
            500: '系统错误',
            502: '网关错误',
            504: '网关超时'
        }
        return titles.get(error_code, '未知错误')
    
    def handle_bad_request(self, error):
        """处理400错误"""
        exc = ValidationException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_unauthorized(self, error):
        """处理401错误"""
        exc = AuthenticationException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_forbidden(self, error):
        """处理403错误"""
        exc = AuthorizationException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_not_found(self, error):
        """处理404错误"""
        exc = ResourceNotFoundException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_conflict(self, error):
        """处理409错误"""
        exc = ConcurrencyException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_rate_limit(self, error):
        """处理429错误"""
        exc = QuotaException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_internal_error(self, error):
        """处理500错误"""
        return self.handle_exception(error)
    
    def handle_bad_gateway(self, error):
        """处理502错误"""
        exc = IntegrationException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())
    
    def handle_gateway_timeout(self, error):
        """处理504错误"""
        exc = TimeoutException(str(error))
        return self._handle_app_exception(exc, self._get_request_info())


exception_handler = ExceptionHandler()