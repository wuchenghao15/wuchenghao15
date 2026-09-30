# -*- coding: utf-8 -*-
#!/usr/bin/env python3
r"""
AI智能路由中间件
根据请求模式和系统负载自动优化路由选择
r"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional
import numpy as np

from app.utils.logging import logger
from flask import request, g

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=r'%(asctime)s - AI Smart Routing - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'logs/ai_smart_routing.log'),
        logging.StreamHandler()
    ])

class AISmartRouting:
    r"""AI智能路由类r"""

    def __init__(self):
        self.route_stats = {}
        self.route_patterns = {}
        self.route_weights = {}

        self.config = {
            r'learning_interval': 3600,
            r'stats_window': 3600,
            r'error_penalty': 0.5,
            r'slow_penalty': 0.3,
            r'popular_boost': 0.2,
            r'min_weight': 0.1,
            r'max_weight': 2.0,
            r'load_threshold': 0.8,
            r'response_time_threshold': 1.0,
            r'error_rate_threshold': 0.1
        }

        self._start_learning_thread()

        logger.info(r"AI智能路由初始化完成")

    def _start_learning_thread(self):
        r"""启动AI学习线程r"""
        def learn_route_patterns():
            while True:
                time.sleep(self.config[r'learning_interval'])
                self._learn_route_patterns()

        learning_thread = threading.Thread(target=learn_route_patterns, daemon=True)
        learning_thread.start()

    def _learn_route_patterns(self):
        r"""学习路由使用模式r"""
        current_time = time.time()

        for route, stats in self.route_stats.items():
            recent_times = [t for t, ts in stats[r'response_times'] if current_time - ts <= self.config[r'stats_window']]

            if recent_times:
                avg_response_time = np.mean(recent_times)
                std_response_time = np.std(recent_times) if len(recent_times) > 1 else 0
                error_rate = stats[r'error_count'] / max(stats[r'request_count'], 1)
                request_frequency = len(recent_times) / (self.config[r'stats_window'] / 60)

                base_weight = 1.0

                if avg_response_time > self.config[r'response_time_threshold']:
                    time_penalty = (avg_response_time - self.config[r'response_time_threshold']) * self.config[r'slow_penalty']
                    base_weight -= time_penalty

                if error_rate > self.config[r'error_rate_threshold']:
                    error_penalty = error_rate * self.config[r'error_penalty']
                    base_weight -= error_penalty

                if request_frequency > 10:
                    popularity_boost = min(request_frequency / 100, self.config[r'popular_boost'])
                    base_weight += popularity_boost

                final_weight = max(self.config[r'min_weight'], min(self.config[r'max_weight'], base_weight))
                self.route_weights[route] = final_weight

                logger.info(fr"路由学习结果 - {route}: 平均响应时间={avg_response_time:.4f}s, 错误率={error_rate:.4f}, 频率={request_frequency:.2f}/min, 权重={final_weight:.4f}")

        logger.info(r"路由学习完成")

    def _update_route_stats(self, route: str, response_time: float, status_code: int):
        r"""更新路由统计信息r"""
        if route not in self.route_stats:
            self.route_stats[route] = {
                r'response_times': [],
                r'request_count': 0,
                r'error_count': 0
            }

        current_time = time.time()
        self.route_stats[route][r'response_times'].append((response_time, current_time))
        self.route_stats[route][r'request_count'] += 1

        if status_code >= 400:
            self.route_stats[route][r'error_count'] += 1

        if len(self.route_stats[route][r'response_times']) > 1000:
            self.route_stats[route][r'response_times'] = self.route_stats[route][r'response_times'][-1000:]

    def _get_route_key(self):
        r"""生成路由键r"""
        return fr"{request.method}:{request.path}"

    def _calculate_route_score(self, route_key):
        r"""计算路由评分r"""
        return self.route_weights.get(route_key, 1.0)

    def smart_routing_middleware(self, app):
        r"""智能路由中间件r"""
        @app.before_request
        def before_request():
            g.request_start_time = time.time()
            g.route_key = self._get_route_key()

            route_score = self._calculate_route_score(g.route_key)
            g.route_score = route_score

            logger.debug(fr"路由评分 - {g.route_key}: {route_score:.4f}")

        @app.after_request
        def after_request(response):
            response_time = time.time() - g.request_start_time

            self._update_route_stats(g.route_key, response_time, response.status_code)

            response.headers[r'X-Route-Score'] = str(g.route_score)
            response.headers[r'X-Route-Response-Time'] = str(response_time)

            return response

        def get_routing_stats():
            r"""获取路由统计信息r"""
            current_time = time.time()
            stats = {}
            for route, route_stats in self.route_stats.items():
                recent_times = [t for t, ts in route_stats[r'response_times'] if current_time - ts <= self.config[r'stats_window']]

                if recent_times:
                    avg_response_time = np.mean(recent_times)
                    std_response_time = np.std(recent_times) if len(recent_times) > 1 else 0
                    error_rate = route_stats[r'error_count'] / max(route_stats[r'request_count'], 1)
                    request_frequency = len(recent_times) / (self.config[r'stats_window'] / 60)

                    stats[route] = {
                        r'avg_response_time': avg_response_time,
                        r'error_rate': error_rate,
                        r'request_frequency': request_frequency,
                        r'weight': self.route_weights.get(route, 1.0),
                        r'request_count': route_stats[r'request_count'],
                        r'error_count': route_stats[r'error_count']
                    }

            import json
            return json.dumps(stats, indent=2)

        logger.info(r"AI智能路由中间件注册完成")
        return app

    def clear_stats(self):
        r"""清除统计信息r"""
        self.route_stats.clear()
        self.route_weights.clear()
        logger.info(r"路由统计信息已清除")


ai_smart_routing = AISmartRouting()


def ai_smart_routing_middleware(app):
    r"""AI智能路由中间件r"""
    return ai_smart_routing.smart_routing_middleware(app)
