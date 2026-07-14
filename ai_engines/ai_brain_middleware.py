# -*- coding: utf-8 -*-
from flask import request, jsonify
from app.utils.logging import logger
from app.services.api_service import APIService
import time
import logging
import json

class AIBrainMiddleware:
    """AI脑库中间件"""

    @staticmethod
    def request_logger(app):
        """AI脑库请求日志记录中间件"""
        @app.before_request
        def log_ai_brain_request():
            if request.path.startswith('/api/ai-brain'):
                # 记录AI脑库请求
                request.start_time = time.time()
                logger.info(f"AI Brain Request: {request.method} {request.path} from {request.remote_addr}")
                logger.info(f"AI Brain Request Args: {request.args}")
                if request.method in ['POST', 'PUT', 'PATCH']:
                    logger.info(f"AI Brain Request JSON: {request.get_json(silent=True)}")

    def response_logger(app):
        """AI脑库响应日志记录中间件"""
        @app.after_request
        def log_ai_brain_response(response):
            if request.path.startswith('/api/ai-brain'):
                response_time = time.time() - getattr(request, 'start_time', time.time())
                logger.info(f"AI Brain Response: {request.method} {request.path} - Status: {response.status_code}, Time: {response_time:.2f}s")
            return response

    def api_rate_limiter(app):
        """AI自适应API速率限制中间件"""
        # 简单的内存速率限制,生产环境建议使用Redis等
        rate_limits = {}
        # 自适应速率限制配置
        adaptive_config = {
            'base_limit': 100,  # 基础速率限制
            'max_limit': 200,  # 最大速率限制
            'min_limit': 50,  # 最小速率限制
            'adjustment_factor': 0.1  # 调整因子
        }
        # 历史请求数据,用于AI学习
        request_history = []

        @app.before_request
        def limit_api_rate():
                config = APIService.get_api_config()

                base_limit = config.get('api_rate_limit', adaptive_config['base_limit'])

                # 基于历史请求数据自适应调整速率限制
                adaptive_limit = AIBrainMiddleware._calculate_adaptive_limit(
                    request_history, base_limit, adaptive_config
                )

                client_ip = request.remote_addr
                current_time = int(time.time())
                time_window = current_time // 60  # 每分钟一个时间窗口

                # 初始化速率限制记录
                if client_ip not in rate_limits:
                    rate_limits[client_ip] = {}
                if time_window not in rate_limits[client_ip]:
                    rate_limits[client_ip][time_window] = 0

                # 检查速率限制
                if rate_limits[client_ip][time_window] >= adaptive_limit:
                    logger.warning(f"API Rate Limit Exceeded for {client_ip}, limit: {adaptive_limit}")
                    return jsonify({
                        'error': 'API Rate Limit Exceeded',
                        'message': f'Rate limit of {adaptive_limit} requests per minute exceeded'
                    }), 429

                # 增加请求计数
                rate_limits[client_ip][time_window] += 1

                # 记录请求数据用于AI学习
                request_history.append({
                    'timestamp': current_time,
                    'client_ip': client_ip,
                    'path': request.path,
                    'method': request.method
                })

                # 只保留最近1000条请求记录
                if len(request_history) > 1000:
                    request_history = request_history[-1000:]

    def _calculate_adaptive_limit(request_history, base_limit, config):
        """基于AI学习计算自适应速率限制"""
        if not request_history:
            return base_limit

        # 计算最近1分钟的请求数
        current_time = int(time.time())
        one_minute_ago = current_time - 60
        recent_requests = [r for r in request_history if r['timestamp'] >= one_minute_ago]
        recent_request_count = len(recent_requests)

        # 计算最近5分钟的平均请求数
        five_minute_requests = [r for r in request_history if r['timestamp'] >= five_minutes_ago]
        five_minute_avg = len(five_minute_requests) / 5 if five_minute_requests else 0

        # 计算最近15分钟的平均请求数
        fifteen_minutes_ago = current_time - 900
        fifteen_minute_requests = [r for r in request_history if r['timestamp'] >= fifteen_minutes_ago]
        fifteen_minute_avg = len(fifteen_minute_requests) / 15 if fifteen_minute_requests else 0

        # 基于历史数据计算自适应限制
        # 如果最近请求数远低于基础限制,增加限制
        if recent_request_count < base_limit * 0.5 and fifteen_minute_avg < base_limit * 0.7:
            # 请求量低,提高速率限制
            adjustment = (base_limit - recent_request_count) * config['adjustment_factor']
            new_limit = base_limit + adjustment
        # 如果最近请求数接近基础限制,保持限制
        elif recent_request_count < base_limit * 0.9:
            new_limit = base_limit
        # 如果最近请求数超过基础限制,降低限制
        else:
            # 请求量高,降低速率限制
            adjustment = (recent_request_count - base_limit) * config['adjustment_factor']
            new_limit = base_limit - adjustment

        # 确保限制在合理范围内
        new_limit = max(config['min_limit'], min(config['max_limit'], new_limit))

        logger.debug(f"自适应速率限制计算: 最近请求数={recent_request_count}, 5分钟平均={five_minute_avg:.2f}, 15分钟平均={fifteen_minute_avg:.2f}, 基础限制={base_limit}, 新限制={new_limit:.2f}")

        return int(new_limit)

    def api_timeout_middleware(app):
        """AI自适应API超时中间件"""
        # 历史响应时间数据,用于AI学习
        response_times = []
        # 自适应超时配置
        adaptive_config = {
            'base_timeout': 30,  # 基础超时时间(秒)
            'max_timeout': 60,  # 最大超时时间
            'min_timeout': 10,  # 最小超时时间
            'percentile': 0.95  # 使用95%分位数作为超时参考
        }

        def set_api_timeout():
            if request.path.startswith('/api/ai-brain'):
                config = APIService.get_api_config()
                # 获取基础超时时间
                base_timeout = config.get('api_timeout', adaptive_config['base_timeout'])
                adaptive_timeout = AIBrainMiddleware._calculate_adaptive_timeout(
                    response_times, base_timeout, adaptive_config
                )

                # 设置请求超时
                request.timeout = adaptive_timeout
                request.start_time = time.time()

        @app.after_request
        def record_response_time(response):
            if request.path.startswith('/api/ai-brain') and hasattr(request, 'start_time'):
                # 记录响应时间
                duration = time.time() - request.start_time

                if len(response_times) > 1000:
                    response_times = response_times[-1000:]
            return response

    def _calculate_adaptive_timeout(response_times, base_timeout, config):
        """基于AI学习计算自适应超时时间"""
        if not response_times:
            return base_timeout

        # 计算95%分位数响应时间
        p95_response_time = np.percentile(response_times, config['percentile'] * 100)

        # 计算平均响应时间
        avg_response_time = np.mean(response_times)

        # 计算响应时间标准差
        std_response_time = np.std(response_times) if len(response_times) > 1 else 0

        # 基于历史数据计算自适应超时
        # 如果95%响应时间远低于基础超时,降低超时
        if p95_response_time < base_timeout * 0.5:
            # 响应时间短,降低超时
            new_timeout = max(config['min_timeout'], p95_response_time + std_response_time)
        # 如果95%响应时间接近基础超时,保持超时
        elif p95_response_time < base_timeout * 0.9:
            new_timeout = base_timeout
        # 如果95%响应时间超过基础超时,增加超时
        else:
            # 响应时间长,增加超时
            new_timeout = min(config['max_timeout'], p95_response_time + 2 * std_response_time)

        logger.debug(f"自适应超时计算: 95%响应时间={p95_response_time:.2f}s, 平均响应时间={avg_response_time:.2f}s, 标准差={std_response_time:.2f}s, 基础超时={base_timeout}s, 新超时={new_timeout:.2f}s")

        return new_timeout

    def cors_middleware(app):
        """CORS中间件"""
        @app.after_request
        def enable_cors(response):
            config = APIService.get_api_config()
            if config.get('enable_cors', True):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            return response

    def register_all(app):
        """注册所有AI脑库中间件"""
        AIBrainMiddleware.request_logger(app)
        AIBrainMiddleware.api_rate_limiter(app)
        AIBrainMiddleware.api_timeout_middleware(app)
        AIBrainMiddleware.cors_middleware(app)
        logger.info("AI Brain中间件注册完成")
