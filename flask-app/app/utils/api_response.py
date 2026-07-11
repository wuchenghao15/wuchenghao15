# -*- coding: utf-8 -*-
"""
统一API响应工具函数
遵循MTSCOS开发规则5.1节响应格式规范
"""

from datetime import datetime
from flask import jsonify


def success_response(data=None, message='success', code=200):
    """成功响应"""
    response = {
        'code': code,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), code


def error_response(message, code=400, error_type=None, suggestion=None, details=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'error_id': str(hash(str(datetime.now()) + message))[:8],
        'timestamp': datetime.now().isoformat(),
        'category': 'business' if 400 <= code < 500 else 'system'
    }
    if error_type:
        response['error_type'] = error_type
    if suggestion:
        response['suggestion'] = suggestion
    if details:
        response['details'] = details
    return jsonify(response), code


def validation_error(message, field_errors=None):
    """验证错误响应"""
    return error_response(
        message=message,
        code=400,
        error_type='VALIDATION_ERROR',
        suggestion='请检查输入参数',
        details={'field_errors': field_errors or {}}
    )


def authentication_error(message='未授权'):
    """认证错误响应"""
    return error_response(
        message=message,
        code=401,
        error_type='AUTHENTICATION_ERROR',
        suggestion='请重新登录'
    )


def authorization_error(message='权限不足'):
    """授权错误响应"""
    return error_response(
        message=message,
        code=403,
        error_type='AUTHORIZATION_ERROR',
        suggestion='您没有权限访问此资源'
    )


def not_found_error(message='资源不存在'):
    """资源不存在响应"""
    return error_response(
        message=message,
        code=404,
        error_type='RESOURCE_NOT_FOUND',
        suggestion='请求的资源不存在'
    )


def business_error(message, suggestion=None):
    """业务逻辑错误响应"""
    return error_response(
        message=message,
        code=400,
        error_type='BUSINESS_ERROR',
        suggestion=suggestion or '操作失败，请稍后重试'
    )


def system_error(message='系统内部错误'):
    """系统错误响应"""
    return error_response(
        message=message,
        code=500,
        error_type='SYSTEM_ERROR',
        category='system',
        suggestion='如果问题持续存在，请联系管理员'
    )