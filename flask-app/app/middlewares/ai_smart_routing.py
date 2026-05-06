#!/usr/bin/env python3
"""
AI智能路由中间件
根据请求模式和系统负载自动优化路由选择

import os
import time
# JSON import removed - using database
import logging
import threading
from typing import Dict, List, Optional
import numpy as np

from app.utils.logging import logger
from flask import request, g

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Smart Routing - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_smart_routing.log'),
        logging.StreamHandler()
    ]
)

class AISmartRouting:
    """AI智能路由类"""

    def __init__(self):
        # 路由性能统计，格式：{route: {response_times: [time1, time2, ...], request_count: int, error_count: int}}
        self.route_stats = {}
        # 路由使用模式，格式：{route: {time_bucket: count}}
        self.route_patterns = {}
        # 动态路由权重，格式：{route: weight}
        self.route_weights = {}

        # 智能路由配置
        self.config = {
            'learning_interval': 3600,  # 学习间隔（秒）
            'stats_window': 3600,  # 统计窗口（秒）
            'error_penalty': 0.5,  # 错误惩罚系数
            'slow_penalty': 0.3,  # 慢响应惩罚系数
            'popular_boost': 0.2,  # 热门路由提升系数
            'min_weight': 0.1,  # 最小路由权重
            'max_weight': 2.0,  # 最大路由权重
            'load_threshold': 0.8,  # 负载阈值，超过该值触发负载均衡
            'response_time_threshold': 1.0,  # 响应时间阈值（秒）
            'error_rate_threshold': 0.1,  # 错误率阈值
        }

        # 启动AI学习线程
        self._start_learning_thread()

        logger.info("AI智能路由初始化完成")

    def _start_learning_thread(self):
        """启动AI学习线程"""
        def learn_route_patterns():
            while True:
                time.sleep(self.config['learning_interval'])
                self._learn_route_patterns()

        learning_thread = threading.Thread(target=learn_route_patterns, daemon=True)
        learning_thread.start()

    def _learn_route_patterns(self):
        """学习路由使用模式"""
        current_time = time.time()

        # 分析路由性能
        for route, stats in self.route_stats.items():
            # 过滤掉旧的响应时间数据
            recent_times = [t for t, ts in stats['response_times'] if current_time - ts <= self.config['stats_window']]

            if recent_times:
                # 计算平均响应时间
                avg_response_time = np.mean(recent_times)
                # 计算响应时间标准差
                std_response_time = np.std(recent_times) if len(recent_times) > 1 else 0
                # 计算错误率
                error_rate = stats['error_count'] / max(stats['request_count'], 1)
                # 计算请求频率
                request_frequency = len(recent_times) / (self.config['stats_window'] / 60)  # 每分钟请求数

                # 计算路由权重
                base_weight = 1.0

                # 根据响应时间调整权重
                if avg_response_time > self.config['response_time_threshold']:
                    # 响应时间越长，权重越低
                    time_penalty = (avg_response_time - self.config['response_time_threshold']) * self.config['slow_penalty']
                    base_weight -= time_penalty

                # 根据错误率调整权重
                if error_rate > self.config['error_rate_threshold']:
                    # 错误率越高，权重越低
                    error_penalty = error_rate * self.config['error_penalty']
                    base_weight -= error_penalty

                # 根据请求频率调整权重
                if request_frequency > 10:  # 热门路由
                    # 热门路由增加权重
                    popularity_boost = min(request_frequency / 100, self.config['popular_boost'])
                    base_weight += popularity_boost

                # 确保权重在合理范围内
                final_weight = max(self.config['min_weight'], min(self.config['max_weight'], base_weight))
                self.route_weights[route] = final_weight

                logger.info(f"路由学习结果 - {route}: 平均响应时间={avg_response_time:.4f}s, 错误率={error_rate:.4f}, 频率={request_frequency:.2f}/min, 权重={final_weight:.4f}")

        logger.info("路由学习完成")

    def _update_route_stats(self, route: str, response_time: float, status_code: int):
        """更新路由统计信息"""
        if route not in self.route_stats:
            self.route_stats[route] = {
                'response_times': [],
                'request_count': 0,
                'error_count': 0
            }
        current_time = time.time()
        self.route_stats[route]['response_times'].append((response_time, current_time))

        # 记录错误
        if status_code >= 400:
            self.route_stats[route]['error_count'] += 1

        # 限制响应时间数据量
        if len(self.route_stats[route]['response_times']) > 1000:
            self.route_stats[route]['response_times'] = self.route_stats[route]['response_times'][-1000:]

    def _get_route_key(self):
        """生成路由键"""
        return f"{request.method}:{request.path}"

    def _calculate_route_score(self, route: str) -> float:
        """计算路由评分"""
        # 初始评分
        score = 1.0

        # 如果有历史权重，使用权重调整评分
        if route in self.route_weights:
            score = self.route_weights[route]

        # 考虑当前系统负载
        system_load = os.getloadavg()[0]  # 获取1分钟系统负载
        if system_load > self.config['load_threshold']:
            # 系统负载高，降低所有路由评分
            score *= (1 - (system_load - self.config['load_threshold']) * 0.5)

        return max(0.1, score)

    def smart_routing_middleware(self, app):
        """智能路由中间件"""
        @app.before_request
        def before_request():
            # 记录请求开始时间
            g.request_start_time = time.time()
            g.route_key = self._get_route_key()

            # 计算路由评分
            route_score = self._calculate_route_score(g.route_key)
            g.route_score = route_score

            # 记录路由评分
            logger.debug(f"路由评分 - {g.route_key}: {route_score:.4f}")

            # 可以在这里实现智能路由选择逻辑
            # 例如：根据路由评分选择不同的处理函数或服务

        @app.after_request
        def after_request(response):
            # 计算响应时间
            response_time = time.time() - g.request_start_time

            # 更新路由统计
            self._update_route_stats(g.route_key, response_time, response.status_code)

            # 添加路由评分和响应时间到响应头
            response.headers['X-Route-Score'] = str(g.route_score)
            response.headers['X-Route-Response-Time'] = str(response_time)

            return response

        # 添加路由统计API
        @app.route('/api/routing/stats')
        def get_routing_stats():
            """获取路由统计信息"""
            current_time = time.time()
            stats = {}
            for route, route_stats in self.route_stats.items():
                # 过滤最近的数据
                recent_times = [t for t, ts in route_stats['response_times'] if current_time - ts <= self.config['stats_window']]

                if recent_times:
                    avg_response_time = np.mean(recent_times)
                    std_response_time = np.std(recent_times) if len(recent_times) > 1 else 0
                    error_rate = route_stats['error_count'] / max(route_stats['request_count'], 1)

                        'avg_response_time': avg_response_time,
                        'error_rate': error_rate,
                        'request_frequency': request_frequency,
                        'weight': self.route_weights.get(route, 1.0),
                        'request_count': route_stats['request_count'],
                        'error_count': route_stats['error_count']
                    }
            return str(stats, indent=2)

        logger.info("AI智能路由中间件注册完成")
        return app

    def get_route_stats(self) -> Dict:
        """获取路由统计信息"""
        return self.route_stats

    def get_route_weights(self) -> Dict:
        """获取路由权重"""
        return self.route_weights

    def clear_stats(self):
        self.route_stats.clear()
        self.route_weights.clear()
        logger.info("路由统计信息已清除")


# 创建全局AI智能路由实例
ai_smart_routing = AISmartRouting()


def ai_smart_routing_middleware(app):
    """AI智能路由中间件"""
    return ai_smart_routing.smart_routing_middleware(app)


# 优先级配置
ai_smart_routing_priority = 20
