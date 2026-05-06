#!/usr/bin/env python3
"""
错误处理器模块

from flask # JSON import removed - using database
ify, render_template, request, g
import traceback
from app.utils.logging import logger
from app.ai.monitoring import ai_monitor


class ErrorHandler:
    统一错误处理类

    def __init__(self, app=None):
        self.app = app
        self.error_stats = {
            '400': 0,
            '401': 0,
            '403': 0,
            '404': 0,
            '500': 0,
            'other': 0
        }

        if app:
            self.init_app(app)

    def init_app(self, app):
        初始化错误处理器

        Args:
            app: Flask应用实例
        self.app = app

        # 注册错误处理器
        app.errorhandler(400)(self.bad_request)
        app.errorhandler(401)(self.unauthorized)
        app.errorhandler(404)(self.not_found)
        app.errorhandler(500)(self.internal_server_error)
        app.errorhandler(Exception)(self.general_exception)

        logger.info("统一错误处理器注册成功")

    def _format_error_response(self, error_code, error_message, error):
        格式化错误响应

        Args:
            error_code: 错误码
            error_message: 错误信息
            error: 错误对象

        Returns:
            错误响应
        if str(error_code) in self.error_stats:
            self.error_stats[str(error_code)] += 1
        else:
            self.error_stats['other'] += 1

        # 构建错误详情
        error_detail = {
            'success': False,
            'error': error_message,
            'code': error_code,
            'timestamp': g.get('start_time', None),
            'path': request.path,
            'method': request.method,
            'client_ip': g.get('client_ip', request.remote_addr)
        }

        # API请求返回JSON响应
        if request.path.startswith('/api/'):
            return jsonify(error_detail), error_code

        # Web请求返回HTML响应
        return render_template('error.html',
                              error_message=error_message,
                              error_detail=error_detail), error_code

    def _log_error(self, error_code, error_message, error):
        记录错误日志

        Args:
            error_code: 错误码
            error_message: 错误信息
            error: 错误对象
        # 获取请求详情
        request_details = {
            'method': request.method,
            'path': request.path,
            'client_ip': g.get('client_ip', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', ''),
            'form_data': request.form.to_dict() if request.form else {},
            'json_data': request.get_json(silent=True) or {}

        logger.error(f"{error_code}错误: {error_message}", extra={
            'error_message': str(error),
            'request_details': request_details,
            'traceback': traceback.format_exc()
        })
        ai_monitor.log_error(
            error_type=error_type,
            error_message=f"{error_code}: {error_message}",
            component="flask",
            error_stack=traceback.format_exc()
        )

    def bad_request(self, error):
        """处理400错误"""
        error_code = 400
        error_message = '请求参数错误'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def unauthorized(self, error):
        """处理401错误"""
        error_code = 401
        error_message = '未授权访问'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def forbidden(self, error):
        """处理403错误"""
        error_code = 403
        error_message = '权限不足'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def not_found(self, error):
        """处理404错误"""
        error_code = 404
        error_message = '资源未找到'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def internal_server_error(self, error):
        """处理500错误"""
        error_code = 500
        error_message = '服务器内部错误'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def general_exception(self, error):
        """处理所有未捕获的异常"""
        error_code = 500
        error_message = '服务器内部错误'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def get_error_stats(self):
        获取错误统计信息

        Returns:
            错误统计字典
        return self.error_stats


# 创建全局错误处理器实例
error_handler = ErrorHandler()


def register_error_handlers(app):
    """注册全局错误处理器"""
    return error_handler
