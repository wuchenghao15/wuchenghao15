# -*- coding: utf-8 -*-
from flask import request, g
import time
from app.utils.logging import logger
from app.ai.monitoring import ai_monitor
from app.utils.network import network_optimizer

def monitoring_middleware(app):
    """监控中间件，用于监控请求和响应"""

    @app.before_request
    def before_request():
        """请求前处理"""
        # 记录请求开始时间
        g.start_time = time.time()

        # 获取客户端IP
        g.client_ip = request.remote_addr

        # 检查速率限制，排除关键路径
        exclude_endpoints = ['auth.login', 'auth.guest_login', 'auth.auto_guest_login', 'auth.logout', 'main.index', 'main.unified_test', 'main.combined_test', 'static']
        if request.endpoint not in exclude_endpoints:
            if network_optimizer.rate_limit_check(g.client_ip):
                logger.warning(f"IP {g.client_ip} 超过速率限制")
                return "速率限制已达上限，请稍后再试", 429
        else:
            # 关键路径请求，跳过速率限制检查
            pass

        # 检查是否为重复请求，排除关键路径
            request_data = request.get_json(silent=True) or request.form.to_dict()
            if network_optimizer.is_duplicate_request(g.client_ip, request.endpoint, request_data):
                logger.warning(f"IP {g.client_ip} 发送重复请求到 {request.endpoint}")
                return "重复请求，请稍后再试", 409

        logger.info(f"请求开始: {request.method} {request.path} - IP: {g.client_ip}")

    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 计算响应时间，检查g.start_time是否存在
        start_time = getattr(g, 'start_time', None)
        if start_time:
            response_time = time.time() - start_time

            # 更新性能指标
            network_optimizer.update_performance_metrics(response_time)

            # 记录请求结束
            logger.info(f"请求结束: {request.method} {request.path} - 状态码: {response.status_code} - 响应时间: {response_time:.4f}s")
        else:
            response_time = 0
            logger.info(f"请求结束: {request.method} {request.path} - 状态码: {response.status_code} - 响应时间: {response_time:.4f}s")

        if response.status_code >= 400:
            error_type = "backend" if response.status_code >= 500 else "frontend"
            ai_monitor.log_error(
                error_type=error_type,
                error_message=f"请求失败: {request.method} {request.path} - 状态码: {response.status_code}",
                component="flask",
                error_stack=None
            )

        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """异常处理"""
        # 计算响应时间
        response_time = time.time() - getattr(g, 'start_time', time.time())

        # 记录异常信息
        logger.exception(f"请求异常: {request.method} {request.path} - 异常: {str(e)}")

        # 向AI监控报告异常
        ai_monitor.log_error(
            error_type="backend",
            error_message=str(e),
            error_stack=None
        )



# 监控应该在安全头和IP白名单之后，认证之前执行
monitoring_priority = 3
