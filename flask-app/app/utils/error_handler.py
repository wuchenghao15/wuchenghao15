# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
错误处理器模块 - 增强版
支持友好页面显示、数据库上报、AI自动处理
"""

from flask import jsonify, render_template, request, g, session
import traceback
import time
import sqlite3
import os
from datetime import datetime
from app.utils.logging import logger
import logging


class ErrorHandler:
    """统一错误处理类"""

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
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')

        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化错误处理器"""
        self.app = app

        # 注册错误处理器
        app.errorhandler(400)(self.bad_request)
        app.errorhandler(401)(self.unauthorized)
        app.errorhandler(403)(self.forbidden)
        app.errorhandler(404)(self.not_found)
        app.errorhandler(500)(self.internal_server_error)
        app.errorhandler(Exception)(self.general_exception)

        logger.info("统一错误处理器注册成功")

    def _format_error_response(self, error_code, error_message, error):
        """格式化错误响应"""
        # 检查是否接受HTML响应
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            return self._render_error_page(error_code, error_message, error)
        
        response = {
            'success': False,
            'error': error_message,
            'code': error_code,
            'timestamp': g.get('request_id', str(int(time.time()))),
            'error_id': g.get('error_id')
        }
        return jsonify(response), error_code

    def _render_error_page(self, error_code, error_message, error):
        """渲染友好的错误页面"""
        error_messages = {
            400: {
                'title': '请求错误',
                'message': '您发送的请求格式不正确',
                'suggestion': '请检查输入信息后重试'
            },
            401: {
                'title': '未授权访问',
                'message': '您需要先登录才能访问此页面',
                'suggestion': '请登录您的账号'
            },
            403: {
                'title': '权限不足',
                'message': '您没有权限访问此资源',
                'suggestion': '如需访问，请联系管理员'
            },
            404: {
                'title': '页面未找到',
                'message': '您访问的页面不存在或已被移除',
                'suggestion': '请检查网址是否正确'
            },
            500: {
                'title': '服务器错误',
                'message': '服务器遇到了一些问题',
                'suggestion': '我们的技术团队已收到通知，正在修复中'
            }
        }

        error_info = error_messages.get(error_code, {
            'title': '系统错误',
            'message': '发生了未知错误',
            'suggestion': '请稍后再试'
        })

        return render_template('error.html',
                             error_code=error_code,
                             error_title=error_info['title'],
                             error_message=error_info['message'],
                             error_suggestion=error_info['suggestion'],
                             error_id=g.get('error_id', ''),
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), error_code

    def _log_error(self, error_code, error_message, error):
        """记录错误日志并上报数据库"""
        error_type = type(error).__name__ if error else 'Unknown'
        stack_trace = traceback.format_exc()
        
        # 生成错误ID
        import uuid
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        g.error_id = error_id
        
        # 记录日志
        logger.error(f"[{error_code}] {error_type}: {error_message} | ErrorID: {error_id}")
        
        # 更新统计
        self.error_stats[str(error_code)] = self.error_stats.get(str(error_code), 0) + 1
        
        # 获取用户信息
        user_id = session.get('user_id')
        username = session.get('username')
        role = session.get('role', 'guest')
        
        # 上报到数据库
        self._report_to_database(error_id, error_code, error_type, error_message, 
                                stack_trace, user_id, username, role)
        
        # 触发AI自动处理
        self._trigger_ai_handler(error_id, error_code, error_type, error_message, stack_trace)

    def _report_to_database(self, error_id, error_code, error_type, error_message, 
                           stack_trace, user_id, username, role):
        """上报错误到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建错误日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_id TEXT UNIQUE NOT NULL,
                        error_code INTEGER,
                        error_type TEXT,
                        error_message TEXT,
                        stack_trace TEXT,
                        user_id INTEGER,
                        username TEXT,
                        role TEXT,
                        request_path TEXT,
                        request_method TEXT,
                        request_url TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        ai_processed INTEGER DEFAULT 0,
                        ai_solution TEXT,
                        resolved_at TIMESTAMP,
                        resolved_by TEXT
                    )
                ''')
                
                # 插入错误记录
                cursor.execute('''
                    INSERT INTO error_logs 
                    (error_id, error_code, error_type, error_message, stack_trace,
                     user_id, username, role, request_path, request_method, 
                     request_url, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (error_id, error_code, error_type, error_message, stack_trace,
                      user_id, username, role, request.path, request.method,
                      request.url, request.remote_addr, request.user_agent.string))
                
                conn.commit()
                logger.info(f"错误已上报数据库: {error_id}")
                
        except Exception as e:
            logger.error(f"错误上报数据库失败: {e}")

    def _trigger_ai_handler(self, error_id, error_code, error_type, error_message, stack_trace):
        """触发AI自动处理"""
        try:
            # 尝试导入AI错误处理服务
            from app.services.error_report_service import error_report_service, ErrorLevel, ErrorCategory
            
            # 创建错误报告
            report = error_report_service.report_error(
                message=error_message,
                error_type=error_type,
                level=ErrorLevel.ERROR if error_code >= 500 else ErrorLevel.WARNING,
                category=ErrorCategory.SYSTEM,
                stack_trace=stack_trace,
                context={
                    'error_code': error_code,
                    'error_id': error_id,
                    'request_path': request.path,
                    'request_method': request.method
                }
            )
            
            logger.info(f"AI错误处理已触发: {error_id}, 报告ID: {report.error_id}")
            
        except ImportError:
            logger.warning("错误上报服务未找到，跳过AI处理")
        except Exception as e:
            logger.error(f"AI错误处理触发失败: {e}")

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
        error_message = str(error) if str(error) else '服务器内部错误'
        self._log_error(error_code, error_message, error)
        return self._format_error_response(error_code, error_message, error)

    def get_error_stats(self):
        """获取错误统计信息"""
        return self.error_stats.copy()

    def reset_error_stats(self):
        """重置错误统计信息"""
        self.error_stats = {
            '400': 0,
            '401': 0,
            '403': 0,
            '404': 0,
            '500': 0,
            'other': 0
        }


def register_error_handlers(app):
    """注册全局错误处理器"""
    error_handler = ErrorHandler(app)
    error_handler.init_app(app)
    logger.info("统一错误处理器注册成功")
    return error_handler

error_handler = ErrorHandler()