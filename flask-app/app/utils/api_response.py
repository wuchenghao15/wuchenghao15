"""统一API响应封装 - MTSCOS AI项目"""

from datetime import datetime
from flask import jsonify, Response
from typing import Any, Optional, Dict


class APIResponse:
    """统一API响应类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "success",
        code: int = 200
    ) -> Response:
        """成功响应"""
        response = {
            "code": code,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response)
    
    @staticmethod
    def error(
        message: str,
        code: int = 400,
        error_id: Optional[str] = None,
        error_type: Optional[str] = None,
        suggestion: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Response:
        """错误响应"""
        response = {
            "code": code,
            "message": message,
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "category": "BUSINESS" if code < 500 else "SYSTEM",
            "error_type": error_type,
            "suggestion": suggestion,
            "details": details or {}
        }
        return jsonify(response)
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        error_type: str = "RESOURCE_NOT_FOUND"
    ) -> Response:
        """资源不存在响应"""
        return APIResponse.error(
            message=message,
            code=404,
            error_type=error_type,
            suggestion="请检查请求参数是否正确"
        )
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        error_type: str = "AUTHENTICATION_ERROR"
    ) -> Response:
        """未授权响应"""
        return APIResponse.error(
            message=message,
            code=401,
            error_type=error_type,
            suggestion="请先登录后再操作"
        )
    
    @staticmethod
    def forbidden(
        message: str = "权限不足",
        error_type: str = "AUTHORIZATION_ERROR"
    ) -> Response:
        """权限不足响应"""
        return APIResponse.error(
            message=message,
            code=403,
            error_type=error_type,
            suggestion="请联系管理员获取更高权限"
        )
    
    @staticmethod
    def validation_error(
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Response:
        """参数验证错误响应"""
        return APIResponse.error(
            message=message,
            code=400,
            error_type="VALIDATION_ERROR",
            suggestion="请检查输入参数",
            details=details or {"field": field} if field else {}
        )
    
    @staticmethod
    def server_error(
        message: str = "服务器内部错误",
        error_id: Optional[str] = None
    ) -> Response:
        """服务器错误响应"""
        return APIResponse.error(
            message=message,
            code=500,
            error_id=error_id,
            error_type="SYSTEM_ERROR",
            suggestion="请稍后重试，如问题持续请联系管理员"
        )
    
    @staticmethod
    def pagination(
        data: Any,
        total: int,
        page: int = 1,
        page_size: int = 10,
        message: str = "success"
    ) -> Response:
        """分页响应"""
        response = {
            "code": 200,
            "message": message,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            },
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response)


def api_response_decorator(func):
    """API响应装饰器"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Response):
                return result
            return APIResponse.success(result)
        except Exception as e:
            return APIResponse.server_error(str(e))
    return wrapper