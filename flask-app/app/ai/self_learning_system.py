#!/usr/bin/env python3
"""
AI自学习系统，用于收集和分析系统运行数据，并自动优化系统配置和性能

import os
import time
import threading
# JSON import removed - using database
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from app.utils.logging import logger

class AISelfLearningSystem:
    """AI自学习系统，用于自动学习和优化系统性能"""

    def __init__(self):
        # 学习数据存储，使用更高效的数据结构
        self.learning_data = {
            'performance_metrics': [],  # 性能指标数据
            'system_configs': [],  # 系统配置历史
            'user_behaviors': [],  # 用户行为数据
            'error_logs': [],  # 错误日志
            'resource_usage': [],  # 资源使用情况

        }

        # 学习模型配置，优化参数提高学习效率
        self.config = {
            'learning_interval': 1800,  # 学习间隔（秒），从3600改为1800
            'data_retention_days': 7,  # 数据保留天数
            'optimization_threshold': 0.05,  # 优化阈值，从0.1改为0.05，更敏感
            'min_samples': 50,  # 最小样本数，从100改为50，更快开始学习
            'learning_rate': 0.05,  # 学习率，从0.01改为0.05，更快收敛
            'model_path': './models/self_learning',  # 模型保存路径
            'enabled': True,  # 是否启用自学习
            'auto_optimize': True,  # 是否自动优化
            'batch_size': 32,  # 新增：批量处理大小
            'feature_importance_enabled': True,  # 新增：启用特征重要性分析
            'anomaly_detection_enabled': True,  # 新增：启用异常检测
        }
        # 初始化模型目录
        os.makedirs(self.config['model_path'], exist_ok=True)

        # 启动学习线程
        self._start_learning_thread()
        # 启动数据清理线程
        self._start_data_cleanup_thread()

        logger.info("AI自学习系统初始化完成")

    def _start_learning_thread(self):
        """启动学习线程"""
        def learn_system_patterns():
            while self.config['enabled']:
                time.sleep(self.config['learning_interval'])
                self._learn_system_patterns()

        learning_thread = threading.Thread(target=learn_system_patterns, daemon=True)
        learning_thread.start()

    def _start_data_cleanup_thread(self):
        """启动数据清理线程"""
        def cleanup_old_data():
            while self.config['enabled']:
                time.sleep(24 * 3600)  # 每天清理一次

        cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
        cleanup_thread.start()

    def _cleanup_old_data(self):
        """清理旧数据"""
        current_time = time.time()
        retention_seconds = self.config['data_retention_days'] * 24 * 3600

        for data_type in self.learning_data:
            self.learning_data[data_type] = [
                item for item in self.learning_data[data_type]
                if current_time - item['timestamp'] <= retention_seconds
            ]

        logger.info("AI自学习系统数据清理完成")

    def _learn_system_patterns(self):
        """学习系统运行模式"""
        if not self.config['enabled']:
            return

        logger.info("开始学习系统运行模式...")

        try:
            # 1. 批量处理数据，提高效率
            data = self._batch_process_data()

            # 2. 分析性能数据
            performance_analysis = self._analyze_performance_data(data['performance'])

            # 3. 分析资源使用情况
            resource_analysis = self._analyze_resource_usage(data['resource'])

            # 4. 分析用户行为
            behavior_analysis = self._analyze_user_behavior(data['behavior'])

            # 5. 分析错误日志
            error_analysis = self._analyze_error_logs(data['error'])



            # 8. 特征重要性分析（新增）
            feature_importance = {}  # 初始化特征重要性字典
            if self.config['feature_importance_enabled']:
                feature_importance = self._analyze_feature_importance(data)

            # 9. 异常检测（新增）
            anomalies = []
            if self.config['anomaly_detection_enabled']:
                anomalies = self._detect_anomalies(data)


            # 10. 生成优化建议，结合特征重要性和异常检测
            optimization_suggestions = self._generate_optimization_suggestions(
                performance_analysis, resource_analysis, behavior_analysis, error_analysis,
                feature_importance, anomalies
            )

            # 11. 应用优化建议
            if self.config['auto_optimize'] and optimization_suggestions:
                self._apply_optimization_suggestions(optimization_suggestions)

            # 12. 保存学习结果
            self.save_model()

            logger.info("系统运行模式学习完成")

        except Exception as e:
            logger.error(f"学习系统运行模式失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def _batch_process_data(self) -> Dict:
        """批量处理数据，提高效率"""
        batch_size = self.config['batch_size']

        # 从学习数据中获取最新的数据批次
        performance_data = self.learning_data['performance_metrics'][-batch_size:]
        resource_data = self.learning_data['resource_usage'][-batch_size:]
        behavior_data = self.learning_data['user_behaviors'][-batch_size:]
        error_data = self.learning_data['error_logs'][-batch_size:]

        return {
            'performance': performance_data,
            'resource': resource_data,
            'behavior': behavior_data,
            'error': error_data
        }
    def _analyze_performance_data(self, data: List[Dict] = None) -> Dict:
        """分析性能数据"""
        performance_metrics = data if data else self.learning_data['performance_metrics']
        if not performance_metrics:
            return {}

        # 提取响应时间数据
        response_times = [m['response_time'] for m in performance_metrics if 'response_time' in m]

        if not response_times:
            return {}

        analysis = {
            'avg_response_time': np.mean(response_times),
            'max_response_time': np.max(response_times),
            'min_response_time': np.min(response_times),
            'p95_response_time': np.percentile(response_times, 95),
            'p99_response_time': np.percentile(response_times, 99),
            'total_requests': len(performance_metrics),
        }
        logger.debug(f"性能分析结果: {analysis}")
        return analysis

    def _analyze_resource_usage(self, data: List[Dict] = None) -> Dict:
        """分析资源使用情况"""
        resource_usage = data if data else self.learning_data['resource_usage']
        if not resource_usage:
            return {}

        # 提取CPU和内存使用率
        cpu_usages = [r['cpu_usage'] for r in resource_usage if 'cpu_usage' in r]
        memory_usages = [r['memory_usage'] for r in resource_usage if 'memory_usage' in r]
        analysis = {
            'avg_cpu_usage': np.mean(cpu_usages) if cpu_usages else 0,
            'avg_memory_usage': np.mean(memory_usages) if memory_usages else 0,
            'max_cpu_usage': np.max(cpu_usages) if cpu_usages else 0,
            'max_memory_usage': np.max(memory_usages) if memory_usages else 0,
            'cpu_spikes': len([u for u in cpu_usages if u > 90]) if cpu_usages else 0,
            'memory_spikes': len([u for u in memory_usages if u > 90]) if memory_usages else 0,
        logger.debug(f"资源使用分析结果: {analysis}")
        return analysis

    def _analyze_user_behavior(self, data: List[Dict] = None) -> Dict:
        """分析用户行为"""
        user_behaviors = data if data else self.learning_data['user_behaviors']
        if not user_behaviors:
            return {}

        # 按路径分组统计请求次数
        for behavior in user_behaviors:
            path = behavior.get('path', '/unknown')

        # 找出最热门的路径
        top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        analysis = {
            'total_user_actions': len(user_behaviors),
            'top_paths': top_paths,
            'unique_paths': len(path_counts),
        }
        logger.debug(f"用户行为分析结果: {analysis}")
        return analysis

    def _analyze_error_logs(self, data: List[Dict] = None) -> Dict:
        error_logs = data if data else self.learning_data['error_logs']
        if not error_logs:
            return {}

        # 按错误类型分组统计
        error_counts = {}
        for error in error_logs:
            error_type = error.get('error_type', 'unknown')
        # 找出最常见的错误类型
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        analysis = {
            'total_errors': len(error_logs),
            'top_errors': top_errors,
            'unique_error_types': len(error_counts),
        }
        logger.debug(f"错误日志分析结果: {analysis}")
        return analysis


    def _analyze_feature_importance(self, data: Dict) -> Dict:
        """分析特征重要性"""
        # 例如使用随机森林或梯度提升树计算特征重要性
        feature_importance = {
            'performance': 0.3,
            'resource': 0.3,
            'behavior': 0.2,
            'error': 0.2
        }
        # 基于实际数据调整特征重要性
        if data['performance']:
        if data['resource'] and any(r['cpu_usage'] > 80 for r in data['resource']):
            feature_importance['resource'] += 0.1
        if data['error'] and len(data['error']) > 5:
            feature_importance['error'] += 0.1

        logger.debug(f"特征重要性分析结果: {feature_importance}")
        return feature_importance

    def _detect_anomalies(self, data: Dict) -> List[Dict]:
        """检测异常数据"""
        anomalies = []

        # 检测性能异常
        for perf in data['performance']:
            response_time = perf.get('response_time', 0)
            if response_time > 3.0:  # 响应时间超过3秒
                anomalies.append({
                    'type': 'performance_anomaly',
                    'description': f'响应时间异常: {response_time:.2f}s',
                })

        # 检测资源使用异常
        for resource in data['resource']:
            cpu = resource.get('cpu_usage', 0)
            memory = resource.get('memory_usage', 0)
            if cpu > 95:
                anomalies.append({
                    'type': 'resource_anomaly',
                    'description': f'CPU使用率异常: {cpu:.1f}%',
                    'data': resource
                })
            if memory > 95:
                anomalies.append({
                    'type': 'resource_anomaly',
                    'description': f'内存使用率异常: {memory:.1f}%',
                    'data': resource
                })

        logger.debug(f"异常检测结果: 发现 {len(anomalies)} 个异常")
        return anomalies

    def _generate_optimization_suggestions(self, performance_analysis: Dict, resource_analysis: Dict,
                                           behavior_analysis: Dict, error_analysis: Dict,
                                           feature_importance: Dict = None, anomalies: List[Dict] = None) -> List[Dict]:
        """生成优化建议"""
        suggestions = []
        anomalies = anomalies or []

        # 1. 基于异常检测的优化建议（新增，优先级最高）
        if anomalies:
                    suggestions.append({
                        'type': 'anomaly',
                        'priority': 'critical',
                        'action': 'fix_performance_anomaly',
                            'anomaly_data': anomaly['data'],
                        }
                elif anomaly['type'] == 'resource_anomaly':
                    suggestions.append({
                        'type': 'anomaly',
                        'priority': 'critical',
                        'description': f'检测到资源使用异常: {anomaly["description"]}',
                        'action': 'fix_resource_anomaly',
                        'parameters': {
                            'anomaly_data': anomaly['data'],
                            'urgent': True
                        }

        # 2. 基于性能数据的优化建议
        if performance_analysis:
            avg_response_time = performance_analysis.get('avg_response_time', 0)
            if avg_response_time > 1.0:  # 响应时间超过1秒
                suggestions.append({
                    'type': 'performance',
                    'priority': 'high',
                    'description': f'平均响应时间过高 ({avg_response_time:.2f}s)，建议优化慢查询和增加缓存',
                    'action': 'optimize_response_time',
                    'parameters': {
                        'target_response_time': 0.5,
                        'increase_cache': True
                    }

        # 3. 基于资源使用的优化建议
        if resource_analysis:
            avg_cpu = resource_analysis.get('avg_cpu_usage', 0)
                suggestions.append({
                    'priority': 'high',
                    'parameters': {
                        'target_cpu_usage': 50,
                        'optimize_code': True,
                    }
            avg_memory = resource_analysis.get('avg_memory_usage', 0)
                suggestions.append({
                    'type': 'resource',
                    'description': f'内存使用率过高 ({avg_memory:.1f}%)，建议优化内存使用或增加内存',
                    'action': 'optimize_memory_usage',
                    'parameters': {
                        'optimize_memory': True,
                        'increase_memory': True
                    }

        # 4. 基于用户行为的优化建议
            top_paths = behavior_analysis.get('top_paths', [])
            if top_paths:
                suggestions.append({
                    'type': 'user_behavior',
                    'priority': 'medium',
                    'description': f'热门路径: {top_paths[0][0]} (访问次数: {top_paths[0][1]})，建议优化该路径性能',
                    'parameters': {
                        'path': top_paths[0][0],
                        'preload_data': True
                    }

        # 5. 基于错误日志的优化建议
        if error_analysis:
            top_errors = error_analysis.get('top_errors', [])
            if top_errors and top_errors[0][1] > 10:  # 同一错误类型出现超过10次
                    'type': 'error',
                    'description': f'频繁出现的错误类型: {top_errors[0][0]} (出现次数: {top_errors[0][1]})，建议修复该错误',
                    'parameters': {
                        'fix_urgently': True
                    }

        # 6. 基于特征重要性的优化建议
        if feature_importance:
            # 找出最重要的特征
            most_important_feature = max(feature_importance.items(), key=lambda x: x[1])[0]
            suggestions.append({
                'type': 'feature_based',
                'description': f'基于特征重要性分析，建议优先关注 {most_important_feature} 方面的优化',
                'action': 'optimize_based_on_feature_importance',
                    'target_feature': most_important_feature,

        return suggestions

    def _apply_optimization_suggestions(self, suggestions: List[Dict]):
        """应用优化建议"""
        for suggestion in suggestions:
            logger.info(f"应用优化建议: {suggestion['description']}")
            # 这里可以实现具体的优化建议应用逻辑
            # 例如调用相应的系统API或修改配置文件

    def save_model(self):
        # 保存学习数据和模型参数
        model_data = {
            'config': self.config,
        }
        model_file = os.path.join(self.config['model_path'], 'self_learning_model.json')
            json.dump(model_data, f, indent=2, default=str)

    def load_model(self):
        """加载学习模型"""
        model_file = os.path.join(self.config['model_path'], 'self_learning_model.json')
        if os.path.exists(model_file):
            with open(model_file, 'r') as f:
                model_data = json.load(f)
                self.learning_data = model_data['learning_data']

        """添加性能数据"""
        self.learning_data['performance_metrics'].append({
            **performance_data,
        })

    def add_resource_data(self, resource_data: Dict):
        """添加资源使用数据"""
        self.learning_data['resource_usage'].append({
            **resource_data,
            'timestamp': time.time()
        })

        """添加用户行为数据"""
        self.learning_data['user_behaviors'].append({
            **behavior_data,
            'timestamp': time.time()
        })

    def add_error_log(self, error_data: Dict):
        """添加错误日志"""
            **error_data,
            'timestamp': time.time()
        })

    def generate_optimization_suggestions(self):
        """生成优化建议（外部调用接口）"""
        # 获取最新数据批次
        data = self._batch_process_data()

        # 分析性能数据
        performance_analysis = self._analyze_performance_data(data['performance'])

        resource_analysis = self._analyze_resource_usage(data['resource'])

        # 分析用户行为
        behavior_analysis = self._analyze_user_behavior(data['behavior'])

        # 分析错误日志

        # 特征重要性分析
        feature_importance = self._analyze_feature_importance(data)

        # 异常检测

        return self._generate_optimization_suggestions(
            feature_importance, anomalies
        )

        """分析特征重要性（外部调用接口）"""
        data = self._batch_process_data()
    def detect_anomalies(self):
        """检测异常（外部调用接口）"""
        data = self._batch_process_data()

        """启动自学习系统"""
        logger.info("AI自学习系统已启动")

    def stop(self):
        """停止自学习系统"""
        logger.info("AI自学习系统已停止")

        """获取学习状态"""
        return {
            'data_counts': {
                'user_behaviors': len(self.learning_data['user_behaviors']),
            },
            'config': self.config
        }

# 初始化自学习系统实例
self_learning_system = AISelfLearningSystem()

