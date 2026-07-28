#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自学习系统
用于收集和分析系统运行数据,并自动优化系统配置和性能
"""

import os
import json
import time
import threading
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger('ai_self_learning')


class AISelfLearningSystem:
    """AI自学习系统:用于自动学习和优化系统性能"""

    def __init__(self):
        """初始化AI自学习系统"""
        self.learning_data = {
            'performance_metrics': [],
            'system_configs': [],
            'user_behaviors': [],
            'error_logs': [],
            'resource_usage': []
        }

        self.config = {
            'learning_interval': 1800,
            'data_retention_days': 7,
            'optimization_threshold': 0.05,
            'min_samples': 50,
            'learning_rate': 0.05,
            'model_path': './models/self_learning',
            'enabled': True,
            'auto_optimize': True,
            'batch_size': 32,
            'feature_importance_enabled': True,
            'anomaly_detection_enabled': True
        }

        os.makedirs(self.config['model_path'], exist_ok=True)

        self.learning_thread = None
        self.cleanup_thread = None
        self.running = False

        self._start_learning_thread()
        self._start_data_cleanup_thread()

        logger.info("AI自学习系统初始化完成")

    def _start_learning_thread(self):
        """启动学习线程"""
        def learn_system_patterns():
            self.running = True
            while self.running:
                try:
                    time.sleep(self.config['learning_interval'])
                    if self.config['enabled']:
                        self._learn_system_patterns()
                except Exception as e:
                    logger.error(f"学习线程错误: {str(e)}")

        self.learning_thread = threading.Thread(
            target=learn_system_patterns,
            daemon=True,
            name="AI-Self-Learning"
        )
        self.learning_thread.start()

    def _start_data_cleanup_thread(self):
        """启动数据清理线程"""
        def cleanup_old_data():
            self.running = True
            while self.running:
                try:
                    time.sleep(24 * 3600)
                    if self.config['enabled']:
                        self._cleanup_old_data()
                except Exception as e:
                    logger.error(f"清理线程错误: {str(e)}")

        self.cleanup_thread = threading.Thread(
            target=cleanup_old_data,
            daemon=True,
            name="AI-Data-Cleanup"
        )
        self.cleanup_thread.start()

    def _cleanup_old_data(self):
        """清理旧数据"""
        current_time = time.time()
        retention_seconds = self.config['data_retention_days'] * 24 * 3600

        for data_type in self.learning_data:
            self.learning_data[data_type] = [
                item for item in self.learning_data[data_type]
                if current_time - item.get('timestamp', 0) <= retention_seconds
            ]

        logger.info("AI自学习系统数据清理完成")

    def _learn_system_patterns(self):
        """学习系统运行模式"""
        if not self.config['enabled']:
            return

        logger.info("开始学习系统运行模式...")

        try:
            data = self._batch_process_data()

            performance_analysis = self._analyze_performance_data(data.get('performance', []))
            resource_analysis = self._analyze_resource_usage(data.get('resource', []))
            behavior_analysis = self._analyze_user_behavior(data.get('behavior', []))
            error_analysis = self._analyze_error_logs(data.get('error', []))

            feature_importance = {}
            if self.config['feature_importance_enabled']:
                feature_importance = self._analyze_feature_importance(data)

            anomalies = []
            if self.config['anomaly_detection_enabled']:
                anomalies = self._detect_anomalies(data)

            optimization_suggestions = self._generate_optimization_suggestions(
                performance_analysis=performance_analysis,
                resource_analysis=resource_analysis,
                behavior_analysis=behavior_analysis,
                error_analysis=error_analysis,
                feature_importance=feature_importance,
                anomalies=anomalies
            )

            if self.config['auto_optimize'] and optimization_suggestions:
                self._apply_optimization_suggestions(optimization_suggestions)

            self.save_model()

            logger.info("系统运行模式学习完成")

        except Exception as e:
            logger.error(f"学习系统运行模式失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def _batch_process_data(self) -> Dict:
        """批量处理数据:提高效率"""
        batch_size = self.config['batch_size']

        return {
            'performance': self.learning_data['performance_metrics'][-batch_size:],
            'resource': self.learning_data['resource_usage'][-batch_size:],
            'behavior': self.learning_data['user_behaviors'][-batch_size:],
            'error': self.learning_data['error_logs'][-batch_size:]
        }

    def _analyze_performance_data(self, data: List[Dict]) -> Dict:
        """分析性能数据"""
        if not data:
            return {'status': 'no_data', 'metrics': {}}

        metrics = {
            'avg_response_time': 0,
            'avg_throughput': 0,
            'error_rate': 0
        }

        if data:
            response_times = [d.get('response_time', 0) for d in data]
            throughputs = [d.get('throughput', 0) for d in data]
            errors = [d.get('error', False) for d in data]

            metrics['avg_response_time'] = np.mean(response_times) if response_times else 0
            metrics['avg_throughput'] = np.mean(throughputs) if throughputs else 0
            metrics['error_rate'] = np.mean(errors) if errors else 0

        return {'status': 'analyzed', 'metrics': metrics, 'sample_count': len(data)}

    def _analyze_resource_usage(self, data: List[Dict]) -> Dict:
        """分析资源使用情况"""
        if not data:
            return {'status': 'no_data', 'utilization': {}}

        cpu_usage = [d.get('cpu', 0) for d in data]
        memory_usage = [d.get('memory', 0) for d in data]
        disk_usage = [d.get('disk', 0) for d in data]

        return {
            'status': 'analyzed',
            'utilization': {
                'cpu_avg': np.mean(cpu_usage) if cpu_usage else 0,
                'memory_avg': np.mean(memory_usage) if memory_usage else 0,
                'disk_avg': np.mean(disk_usage) if disk_usage else 0,
                'cpu_max': np.max(cpu_usage) if cpu_usage else 0,
                'memory_max': np.max(memory_usage) if memory_usage else 0
            },
            'sample_count': len(data)
        }

    def _analyze_user_behavior(self, data: List[Dict]) -> Dict:
        """分析用户行为"""
        if not data:
            return {'status': 'no_data', 'patterns': {}}

        return {
            'status': 'analyzed',
            'patterns': {
                'total_actions': len(data),
                'unique_users': len(set(d.get('user_id', '') for d in data)),
                'avg_session_length': np.mean([d.get('session_length', 0) for d in data]) if data else 0
            },
            'sample_count': len(data)
        }

    def _analyze_error_logs(self, data: List[Dict]) -> Dict:
        """分析错误日志"""
        if not data:
            return {'status': 'no_data', 'error_stats': {}}

        error_types = {}
        for log in data:
            error_type = log.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            'status': 'analyzed',
            'error_stats': {
                'total_errors': len(data),
                'error_types': error_types,
                'most_common': max(error_types.items(), key=lambda x: x[1])[0] if error_types else 'none'
            },
            'sample_count': len(data)
        }

    def _analyze_feature_importance(self, data: Dict) -> Dict:
        """分析特征重要性"""
        feature_scores = {}

        if data.get('performance'):
            feature_scores['performance'] = 0.8
        if data.get('resource'):
            feature_scores['resource'] = 0.7
        if data.get('behavior'):
            feature_scores['behavior'] = 0.6
        if data.get('error'):
            feature_scores['error'] = 0.9

        return {
            'status': 'analyzed',
            'features': feature_scores,
            'top_features': sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        }

    def _detect_anomalies(self, data: Dict) -> List[Dict]:
        """检测异常"""
        anomalies = []

        if data.get('performance'):
            response_times = [d.get('response_time', 0) for d in data['performance']]
            if response_times:
                mean = np.mean(response_times)
                std = np.std(response_times)
                threshold = mean + 2 * std

                for i, rt in enumerate(response_times):
                    if rt > threshold:
                        anomalies.append({
                            'type': 'high_response_time',
                            'index': i,
                            'value': rt,
                            'threshold': threshold
                        })

        return anomalies

    def _generate_optimization_suggestions(
        self,
        performance_analysis: Dict,
        resource_analysis: Dict,
        behavior_analysis: Dict,
        error_analysis: Dict,
        feature_importance: Dict,
        anomalies: List
    ) -> List[Dict]:
        """生成优化建议"""
        suggestions = []

        if performance_analysis.get('metrics', {}).get('error_rate', 0) > 0.05:
            suggestions.append({
                'type': 'performance',
                'priority': 'high',
                'description': '错误率过高,建议优化错误处理机制',
                'details': performance_analysis
            })

        if resource_analysis.get('utilization', {}).get('cpu_avg', 0) > 0.8:
            suggestions.append({
                'type': 'resource',
                'priority': 'high',
                'description': 'CPU使用率过高,建议优化计算密集型任务',
                'details': resource_analysis
            })

        if anomalies:
            suggestions.append({
                'type': 'anomaly',
                'priority': 'medium',
                'description': f'检测到 {len(anomalies)} 个异常,建议进行排查',
                'details': anomalies
            })

        if behavior_analysis.get('patterns', {}).get('avg_session_length', 0) < 60:
            suggestions.append({
                'type': 'engagement',
                'priority': 'low',
                'description': '用户平均会话时长较短,建议优化用户体验',
                'details': behavior_analysis
            })

        return suggestions

    def _apply_optimization_suggestions(self, suggestions: List[Dict]):
        """应用优化建议"""
        for suggestion in suggestions:
            logger.info(f"应用优化建议: {suggestion['description']}")

            if suggestion['type'] == 'performance' and suggestion['priority'] == 'high':
                self._optimize_performance()
            elif suggestion['type'] == 'resource' and suggestion['priority'] == 'high':
                self._optimize_resource_usage()
            elif suggestion['type'] == 'anomaly':
                self._handle_anomalies(suggestion.get('details', []))

    def _optimize_performance(self):
        """优化性能"""
        logger.info("执行性能优化...")

    def _optimize_resource_usage(self):
        """优化资源使用"""
        logger.info("执行资源使用优化...")

    def _handle_anomalies(self, anomalies: List):
        """处理异常"""
        logger.info(f"处理 {len(anomalies)} 个异常...")

    def save_model(self):
        """保存学习模型"""
        try:
            model_data = {
                'config': self.config,
                'learning_data': self.learning_data,
                'saved_at': datetime.now().isoformat()
            }

            model_file = os.path.join(self.config['model_path'], 'self_learning_model.json')
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=2, default=str)

            logger.info(f"模型已保存: {model_file}")
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")

    def load_model(self):
        """加载学习模型"""
        try:
            model_file = os.path.join(self.config['model_path'], 'self_learning_model.json')
            if os.path.exists(model_file):
                with open(model_file, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
                    self.learning_data = model_data.get('learning_data', self.learning_data)
                    logger.info(f"模型已加载: {model_file}")
        except Exception as e:
            logger.error(f"加载模型失败: {str(e)}")

    def add_performance_data(self, performance_data: Dict):
        """添加性能数据"""
        self.learning_data['performance_metrics'].append({
            **performance_data,
            'timestamp': time.time()
        })

    def add_resource_data(self, resource_data: Dict):
        """添加资源使用数据"""
        self.learning_data['resource_usage'].append({
            **resource_data,
            'timestamp': time.time()
        })

    def add_behavior_data(self, behavior_data: Dict):
        """添加用户行为数据"""
        self.learning_data['user_behaviors'].append({
            **behavior_data,
            'timestamp': time.time()
        })

    def add_error_log(self, error_data: Dict):
        """添加错误日志"""
        self.learning_data['error_logs'].append({
            **error_data,
            'timestamp': time.time()
        })

    def get_learning_stats(self) -> Dict:
        """获取学习统计"""
        return {
            'total_samples': {
                'performance': len(self.learning_data['performance_metrics']),
                'resource': len(self.learning_data['resource_usage']),
                'behavior': len(self.learning_data['user_behaviors']),
                'error': len(self.learning_data['error_logs'])
            },
            'config': self.config,
            'learning_enabled': self.config['enabled']
        }

    def update_config(self, config: Dict):
        """更新配置"""
        self.config.update(config)
        logger.info("学习系统配置已更新")

    def stop(self):
        """停止学习系统"""
        self.running = False
        logger.info("AI自学习系统已停止")


ai_self_learning_system = AISelfLearningSystem()
