#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控器模块
负责监控系统性能，检测性能瓶颈

import os
import psutil
import logging
import time
from typing import Dict, Any, List

# 配置日志
logger = logging.getLogger('performance_monitor')

class PerformanceMonitor:
    """性能监控器类"""

    def __init__(self):
        """初始化性能监控器"""
        self.process = psutil.Process(os.getpid())
        self.history = []
        self.max_history = 100
        logger.info("性能监控器初始化完成")

    def get_system_performance(self) -> Dict[str, Any]:
        """获取系统性能数据"""
        try:
            # 获取CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)

            # 获取内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # 获取磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent

            # 获取网络IO
            net_io = psutil.net_io_counters()

            # 获取进程信息
            process_cpu = self.process.cpu_percent(interval=1)
            process_memory = self.process.memory_percent()
            process_threads = self.process.num_threads()

            # 构建性能数据
            performance_data = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_sent': net_io.bytes_sent,
                'network_recv': net_io.bytes_recv,
                'process_cpu': process_cpu,
                'process_memory': process_memory,
                'process_threads': process_threads,
                'timestamp': time.time()
            }

            # 保存历史数据
            self._save_history(performance_data)

            logger.debug(f"系统性能: CPU={cpu_usage}%, 内存={memory_usage}%, 磁盘={disk_usage}%")
            return performance_data
        except Exception as e:
            logger.error(f"获取系统性能数据时出错: {str(e)}")
            return {}

    def get_process_performance(self) -> Dict[str, Any]:
        """获取当前进程性能数据"""
        try:
            cpu_usage = self.process.cpu_percent(interval=1)

            # 获取进程内存使用
            memory_info = self.process.memory_info()
            memory_usage = memory_info.rss / (1024 * 1024)  # MB

            # 获取进程线程数
            threads = self.process.num_threads()

            # 获取进程打开的文件数
            try:
            except Exception:
                open_files = 0

            # 构建进程性能数据
            process_data = {
                'cpu_usage': cpu_usage,
                'memory_usage_mb': memory_usage,
                'threads': threads,
                'timestamp': time.time()
            }

            logger.debug(f"进程性能: CPU={cpu_usage}%, 内存={memory_usage:.2f}MB, 线程={threads}")
        except Exception as e:
            return {}

    def detect_performance_bottlenecks(self) -> List[Dict[str, Any]]:
        """检测性能瓶颈"""

        try:
            # 检查CPU瓶颈
            if performance_data.get('cpu_usage', 0) > 80:
                bottlenecks.append({
                    'type': 'cpu',
                    'description': f"CPU使用率过高: {performance_data['cpu_usage']}%",
                    'severity': 'high',
                    'suggestion': '检查是否有耗时操作，考虑优化代码或增加CPU资源'
                })

            # 检查内存瓶颈
            if performance_data.get('memory_usage', 0) > 80:
                bottlenecks.append({
                    'type': 'memory',
                    'description': f"内存使用率过高: {performance_data['memory_usage']}%",
                    'severity': 'high',
                    'suggestion': '检查是否有内存泄漏，优化数据结构，考虑增加内存'
                })

            # 检查磁盘瓶颈
            if performance_data.get('disk_usage', 0) > 80:
                    'type': 'disk',
                    'description': f"磁盘使用率过高: {performance_data['disk_usage']}%",
                    'severity': 'medium',
                })

            if performance_data.get('process_cpu', 0) > 50:
                    'type': 'process_cpu',
                    'description': f"进程CPU使用率过高: {performance_data['process_cpu']}%",
                    'severity': 'medium',
                    'suggestion': '检查进程中的耗时操作，优化代码'
                })

            # 检查进程内存使用
                    'type': 'process_memory',
                    'description': f"进程内存使用率过高: {performance_data['process_memory']}%",
                    'severity': 'medium',
                    'suggestion': '检查是否有内存泄漏，优化数据结构'
                })

        except Exception as e:
            logger.error(f"检测性能瓶颈时出错: {str(e)}")
    def get_performance_trend(self, window: int = 10) -> Dict[str, Any]:
        """获取性能趋势"""
                return {}

            # 获取最近的历史数据
            recent_history = self.history[-window:]

            cpu_avg = sum(item['cpu_usage'] for item in recent_history) / window
            disk_avg = sum(item['disk_usage'] for item in recent_history) / window

            cpu_trend = recent_history[-1]['cpu_usage'] - recent_history[0]['cpu_usage']
            memory_trend = recent_history[-1]['memory_usage'] - recent_history[0]['memory_usage']
            disk_trend = recent_history[-1]['disk_usage'] - recent_history[0]['disk_usage']

            trend_data = {
                'cpu_avg': cpu_avg,
                'memory_avg': memory_avg,
                'disk_avg': disk_avg,
                'cpu_trend': cpu_trend,
                'memory_trend': memory_trend,
                'disk_trend': disk_trend,
                'window': window
            }

            return trend_data
        except Exception as e:
            logger.error(f"获取性能趋势时出错: {str(e)}")
            return {}

        """生成性能报告"""
        try:
            bottlenecks = self.detect_performance_bottlenecks()
            trend = self.get_performance_trend()
            report = {
                'timestamp': time.time(),
                'current_performance': current_perf,
                'bottlenecks': bottlenecks,
                'recommendations': self._generate_recommendations(bottlenecks, trend)
            }

            return report
        except Exception as e:
            logger.error(f"生成性能报告时出错: {str(e)}")
            return {}

    def _generate_recommendations(self, bottlenecks: List[Dict[str, Any]], trend: Dict[str, Any]) -> List[str]:
        recommendations = []

        # 基于瓶颈生成建议
        for bottleneck in bottlenecks:
            recommendations.append(bottleneck['suggestion'])
        # 基于趋势生成建议
        if trend:
            if trend.get('cpu_trend', 0) > 10:
                recommendations.append('CPU使用率呈上升趋势，建议检查并优化耗时操作')
            if trend.get('memory_trend', 0) > 10:
            if trend.get('disk_trend', 0) > 10:
                recommendations.append('磁盘使用率呈上升趋势，建议清理磁盘空间')

        # 通用建议
        recommendations.extend([
            '定期检查系统性能，及时发现并解决瓶颈',
            '优化数据库查询，使用索引提高查询效率',
            '使用缓存减少重复计算和IO操作',
            '考虑使用异步处理耗时操作',
            '定期清理临时文件和日志'
        ])

        return recommendations

    def _save_history(self, data: Dict[str, Any]):
        """保存历史数据"""
        self.history.append(data)
        # 限制历史数据长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def clear_history(self):
        """清空历史数据"""
        self.history = []

if __name__ == '__main__':
    # 测试性能监控器
    monitor = PerformanceMonitor()

    # 获取系统性能
    print("系统性能:")
    system_perf = monitor.get_system_performance()
    for key, value in system_perf.items():
        if key != 'timestamp':
            print(f"{key}: {value}")

    # 获取进程性能
    print("\n进程性能:")
    process_perf = monitor.get_process_performance()
    for key, value in process_perf.items():
        if key != 'timestamp':
            print(f"{key}: {value}")

    # 检测性能瓶颈
    print("\n性能瓶颈:")
    bottlenecks = monitor.detect_performance_bottlenecks()
    for bottleneck in bottlenecks:
        print(f"- {bottleneck['type']}: {bottleneck['description']} (严重程度: {bottleneck['severity']})")

    # 生成性能报告
    print("\n性能报告:")
    report = monitor.generate_performance_report()
    print(f"当前CPU使用率: {report['current_performance'].get('cpu_usage', 'N/A')}%")
    print(f"当前内存使用率: {report['current_performance'].get('memory_usage', 'N/A')}%")
    print(f"检测到 {len(report['bottlenecks'])} 个瓶颈")
    print("建议:")
    for recommendation in report['recommendations']:
        print(f"- {recommendation}")
