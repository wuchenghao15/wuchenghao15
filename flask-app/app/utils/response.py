"""API响应封装工具 - MTSCOS AI项目"""

from datetime import datetime
from flask import jsonify


def api_response(code: int = 200, message: str = 'success', data: any = None) -> dict:
    """
    统一API响应格式
    
    Args:
        code: 状态码，200表示成功
        message: 消息描述
        data: 响应数据
    
    Returns:
        标准格式的响应字典
    """
    response = {
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    return response


def success_response(data: any = None, message: str = 'success') -> tuple:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
    
    Returns:
        Flask响应对象
    """
    return jsonify(api_response(200, message, data)), 200


def created_response(data: any = None, message: str = '创建成功') -> tuple:
    """
    资源创建成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
    
    Returns:
        Flask响应对象
    """
    return jsonify(api_response(201, message, data)), 201


def error_response(code: int = 400, message: str = '请求错误', 
                   error_type: str = None, suggestion: str = None, details: dict = None) -> tuple:
    """
    错误响应
    
    Args:
        code: 错误状态码
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
        details: 详细信息
    
    Returns:
        Flask响应对象
    """
    import uuid
    response = {
        'code': code,
        'message': message,
        'error_id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now().isoformat(),
        'category': 'BUSINESS',
        'error_type': error_type,
        'suggestion': suggestion,
        'details': details or {}
    }
    return jsonify(response), code


def bad_request(message: str = '请求参数错误', error_type: str = 'VALIDATION_ERROR', 
                suggestion: str = None, details: dict = None) -> tuple:
    """
    400 Bad Request响应
    
    Args:
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
        details: 详细信息
    
    Returns:
        Flask响应对象
    """
    return error_response(400, message, error_type, suggestion, details)


def unauthorized(message: str = '未授权', error_type: str = 'AUTHENTICATION_ERROR',
                 suggestion: str = '请先登录') -> tuple:
    """
    401 Unauthorized响应
    
    Args:
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
    
    Returns:
        Flask响应对象
    """
    return error_response(401, message, error_type, suggestion)


def forbidden(message: str = '权限不足', error_type: str = 'AUTHORIZATION_ERROR',
              suggestion: str = '请联系管理员') -> tuple:
    """
    403 Forbidden响应
    
    Args:
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
    
    Returns:
        Flask响应对象
    """
    return error_response(403, message, error_type, suggestion)


def not_found(message: str = '资源不存在', error_type: str = 'RESOURCE_NOT_FOUND',
              suggestion: str = '请检查资源ID是否正确') -> tuple:
    """
    404 Not Found响应
    
    Args:
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
    
    Returns:
        Flask响应对象
    """
    return error_response(404, message, error_type, suggestion)


def server_error(message: str = '服务器内部错误', error_type: str = 'SYSTEM_ERROR',
                 suggestion: str = '请稍后重试') -> tuple:
    """
    500 Internal Server Error响应
    
    Args:
        message: 错误消息
        error_type: 错误类型
        suggestion: 解决建议
    
    Returns:
        Flask响应对象
    """
    return error_response(500, message, error_type, suggestion)