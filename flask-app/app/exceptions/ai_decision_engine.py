# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI决策引擎 - 根据异常类型和上下文智能决定跳转页面

决策逻辑：
1. 根据异常类型决定基础跳转策略
2. 根据用户角色决定目标页面
3. 根据请求来源决定是否需要特殊处理
4. 支持动态规则配置
"""

import logging
from typing import Optional
from flask import Request
from app.exceptions import AppException, ErrorCategory

logger = logging.getLogger(__name__)


class AIDecisionEngine:
    """AI决策引擎 - 智能决定异常处理跳转页面"""
    
    @staticmethod
    def determine_redirect(exc: AppException, request: Request) -> Optional[str]:
        """根据异常和请求上下文决定跳转页面"""
        strategy = AIDecisionEngine._get_strategy(exc, request)
        
        if strategy:
            redirect_url = strategy(exc, request)
            if redirect_url:
                logger.info(
                    f"AI决策引擎: 异常 [{exc.error_id}] 跳转到 {redirect_url}"
                )
                return redirect_url
        
        return None
    
    @staticmethod
    def determine_redirect_for_system_error(request: Request) -> Optional[str]:
        """系统错误跳转决策"""
        user_role = request.session.get('role', 'user')
        user_id = request.session.get('user_id')
        
        if user_role == 'super_admin':
            return '/super_admin_dashboard'
        elif user_role == 'admin':
            return '/admin_dashboard'
        elif user_role == 'teacher':
            return '/teacher_dashboard'
        elif user_role == 'student':
            return '/student_dashboard'
        elif user_id:
            return '/'
        
        return None
    
    @staticmethod
    def _get_strategy(exc: AppException, request: Request):
        """获取决策策略"""
        strategies = {
            ErrorCategory.AUTHENTICATION: AIDecisionEngine._strategy_authentication,
            ErrorCategory.AUTHORIZATION: AIDecisionEngine._strategy_authorization,
            ErrorCategory.VALIDATION: AIDecisionEngine._strategy_validation,
            ErrorCategory.RESOURCE: AIDecisionEngine._strategy_resource,
            ErrorCategory.BUSINESS: AIDecisionEngine._strategy_business,
            ErrorCategory.QUOTA: AIDecisionEngine._strategy_quota,
            ErrorCategory.TIMEOUT: AIDecisionEngine._strategy_timeout,
            ErrorCategory.INTEGRATION: AIDecisionEngine._strategy_integration,
            ErrorCategory.CONCURRENCY: AIDecisionEngine._strategy_concurrency,
            ErrorCategory.UNKNOWN: AIDecisionEngine._strategy_unknown
        }
        
        return strategies.get(ErrorCategory(exc.category))
    
    @staticmethod
    def _strategy_authentication(exc: AppException, request: Request) -> Optional[str]:
        """认证异常策略 - 跳转登录页"""
        return '/auth/login'
    
    @staticmethod
    def _strategy_authorization(exc: AppException, request: Request) -> Optional[str]:
        """授权异常策略 - 根据用户角色决定"""
        user_role = request.session.get('role', 'user')
        
        redirect_map = {
            'super_admin': '/super_admin_dashboard',
            'admin': '/admin_dashboard',
            'teacher': '/teacher_dashboard',
            'student': '/student_dashboard',
            'parent': '/parent_dashboard',
            'hardware_admin': '/hardware/dashboard'
        }
        
        return redirect_map.get(user_role, '/')
    
    @staticmethod
    def _strategy_validation(exc: AppException, request: Request) -> Optional[str]:
        """验证异常策略 - 通常不跳转，显示错误信息"""
        referrer = request.referrer
        if referrer and not referrer.endswith(request.path):
            return referrer
        
        return None
    
    @staticmethod
    def _strategy_resource(exc: AppException, request: Request) -> Optional[str]:
        """资源不存在策略 - 跳转首页或上一页"""
        referrer = request.referrer
        if referrer:
            return referrer
        
        user_role = request.session.get('role', 'user')
        if user_role == 'super_admin':
            return '/super_admin_dashboard'
        elif user_role == 'admin':
            return '/admin_dashboard'
        
        return '/'
    
    @staticmethod
    def _strategy_business(exc: AppException, request: Request) -> Optional[str]:
        """业务异常策略 - 根据具体情况决定"""
        referrer = request.referrer
        
        if exc.redirect_url:
            return exc.redirect_url
        
        if referrer and not referrer.endswith(request.path):
            return referrer
        
        return None
    
    @staticmethod
    def _strategy_quota(exc: AppException, request: Request) -> Optional[str]:
        """配额异常策略 - 跳转设置页或联系管理员"""
        user_role = request.session.get('role', 'user')
        
        if user_role in ['super_admin', 'admin']:
            return '/system_settings'
        
        return '/contact'
    
    @staticmethod
    def _strategy_timeout(exc: AppException, request: Request) -> Optional[str]:
        """超时异常策略 - 重新加载当前页面或跳转首页"""
        return request.path
    
    @staticmethod
    def _strategy_integration(exc: AppException, request: Request) -> Optional[str]:
        """集成异常策略 - 跳转系统状态页"""
        user_role = request.session.get('role', 'user')
        
        if user_role in ['super_admin', 'admin']:
            return '/system_monitoring'
        
        return None
    
    @staticmethod
    def _strategy_concurrency(exc: AppException, request: Request) -> Optional[str]:
        """并发异常策略 - 刷新当前页面"""
        return request.path
    
    @staticmethod
    def _strategy_unknown(exc: AppException, request: Request) -> Optional[str]:
        """未知异常策略 - 跳转首页"""
        return '/'
    
    @staticmethod
    def get_decision_details(exc: AppException, request: Request) -> dict:
        """获取决策详情用于日志和调试"""
        return {
            'decision_engine': 'AIDecisionEngine',
            'error_id': exc.error_id,
            'error_code': exc.error_code,
            'category': exc.category,
            'user_role': request.session.get('role'),
            'user_id': request.session.get('user_id'),
            'request_path': request.path,
            'referrer': request.referrer,
            'determined_redirect': AIDecisionEngine.determine_redirect(exc, request)
        }