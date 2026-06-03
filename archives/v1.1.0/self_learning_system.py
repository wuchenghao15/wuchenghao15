#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI self-learning system for collecting and analyzing system data"""

import os
import time
import threading
import json
import numpy as np
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AISelfLearningSystem:
    """AI自学习系统,用于自动学习和优化系统性能"""

    def __init__(self):
        # 学习数据存储,使用更高效的数据结构
        self.learning_data = {
            'performance_metrics': [],
            'system_configs': [],
            'user_behaviors': [],
            'error_logs': [],
            'resource_usage': [],
            'asphalt_performance': [],
            'asphalt_maintenance': [],
            'asphalt_upgrades': []
        }

        # 学习模型配置,优化参数提高学习效率
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
            'anomaly_detection_enabled': True,
        }
        os.makedirs(self.config['model_path'], exist_ok=True)

        self._start_learning_thread()
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
                time.sleep(24 * 3600)
                self._cleanup_old_data()

        cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
        cleanup_thread.start()

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

    def _batch_process_data(self) -> Dict:
        """批量处理数据"""
        return {
            'performance': self.learning_data['performance_metrics'],
            'resource': self.learning_data['resource_usage'],
            'behavior': self.learning_data['user_behaviors'],
            'error': self.learning_data['error_logs'],
            'asphalt_performance': self.learning_data['asphalt_performance'],
            'asphalt_maintenance': self.learning_data['asphalt_maintenance'],
            'asphalt_upgrade': self.learning_data['asphalt_upgrades']
        }

    def _learn_system_patterns(self):
        """学习系统运行模式"""
        if not self.config['enabled']:
            return

        logger.info("开始学习系统运行模式...")

        try:
            data = self._batch_process_data()
            performance_analysis = self._analyze_performance_data(data['performance'])
            resource_analysis = self._analyze_resource_usage(data['resource'])
            behavior_analysis = self._analyze_user_behavior(data['behavior'])
            error_analysis = self._analyze_error_logs(data['error'])
            asphalt_performance_analysis = self._analyze_asphalt_performance_data(data['asphalt_performance'])
            asphalt_maintenance_analysis = self._analyze_asphalt_maintenance_data(data['asphalt_maintenance'])
            asphalt_upgrade_analysis = self._analyze_asphalt_upgrade_data(data['asphalt_upgrade'])

            feature_importance = {}
            if self.config['feature_importance_enabled']:
                feature_importance = self._analyze_feature_importance(data)

            anomalies = []
            if self.config['anomaly_detection_enabled']:
                anomalies = self._detect_anomalies(data)
                asphalt_anomalies = self._detect_asphalt_anomalies(data)
                anomalies.extend(asphalt_anomalies)

            optimization_suggestions = self._generate_optimization_suggestions(
                performance_analysis, resource_analysis, behavior_analysis, error_analysis,
                feature_importance, anomalies, asphalt_performance_analysis,
                asphalt_maintenance_analysis, asphalt_upgrade_analysis
            )

            if self.config['auto_optimize'] and optimization_suggestions:
                self._apply_optimization_suggestions(optimization_suggestions)

            self.save_model()
            logger.info("系统运行模式学习完成")

        except Exception as e:
            logger.error(f"学习系统运行模式失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def _analyze_performance_data(self, data: List[Dict] = None) -> Dict:
        """分析性能数据"""
        performance_data = data if data else self.learning_data['performance_metrics']
        if not performance_data:
            return {}

        analysis = {
            'avg_response_time': np.mean([p.get('response_time', 0) for p in performance_data]) if performance_data else 0,
            'total_requests': len(performance_data)
        }
        return analysis

    def _analyze_resource_usage(self, data: List[Dict] = None) -> Dict:
        """分析资源使用情况"""
        resource_usage = data if data else self.learning_data['resource_usage']
        if not resource_usage:
            return {}

        cpu_usages = [r.get('cpu_usage', 0) for r in resource_usage]
        memory_usages = [r.get('memory_usage', 0) for r in resource_usage]
        analysis = {
            'avg_cpu_usage': np.mean(cpu_usages) if cpu_usages else 0,
            'avg_memory_usage': np.mean(memory_usages) if memory_usages else 0,
            'max_cpu_usage': np.max(cpu_usages) if cpu_usages else 0,
            'max_memory_usage': np.max(memory_usages) if memory_usages else 0,
            'cpu_spikes': len([u for u in cpu_usages if u > 90]),
            'memory_spikes': len([u for u in memory_usages if u > 90]),
        }
        return analysis

    def _analyze_user_behavior(self, data: List[Dict] = None) -> Dict:
        """Analyze user behavior"""
        user_behaviors = data if data else self.learning_data['user_behaviors']
        if not user_behaviors:
            return {}

        path_counts = {}
        for behavior in user_behaviors:
            path = behavior.get('path', '/unknown')
            path_counts[path] = path_counts.get(path, 0) + 1

        top_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        analysis = {
            'total_user_actions': len(user_behaviors),
            'top_paths': top_paths,
            'unique_paths': len(path_counts),
        }
        return analysis

    def _analyze_error_logs(self, data: List[Dict] = None) -> Dict:
        """分析错误日志"""
        error_logs = data if data else self.learning_data['error_logs']
        if not error_logs:
            return {}

        error_counts = {}
        for error in error_logs:
            error_type = error.get('error_type', 'unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        analysis = {
            'total_errors': len(error_logs),
            'top_errors': top_errors,
            'unique_error_types': len(error_counts),
        }
        return analysis

    def _analyze_asphalt_performance_data(self, data: List[Dict] = None) -> Dict:
        """Analyze asphalt performance data"""
        asphalt_performance = data if data else self.learning_data['asphalt_performance']
        if not asphalt_performance:
            return {}

        type_performance = {}
        for perf in asphalt_performance:
            asphalt_type = perf.get('asphalt_type_id', 'unknown')
            if asphalt_type not in type_performance:
                type_performance[asphalt_type] = []
            type_performance[asphalt_type].append(perf)

        performance_analysis = {}
        for asphalt_type, perfs in type_performance.items():
            stability_values = [
                p.get('performance_data', {}).get('stability', 0) for p in perfs
                if isinstance(p.get('performance_data'), dict)
            ]
            durability_values = [
                p.get('performance_data', {}).get('durability', 0) for p in perfs
                if isinstance(p.get('performance_data'), dict)
            ]
            viscosity_values = [
                p.get('performance_data', {}).get('viscosity', 0) for p in perfs
                if isinstance(p.get('performance_data'), dict)
            ]

            performance_analysis[asphalt_type] = {
                'total_samples': len(perfs),
                'stability': {
                    'avg': np.mean(stability_values) if stability_values else 0,
                    'max': np.max(stability_values) if stability_values else 0,
                    'min': np.min(stability_values) if stability_values else 0,
                },
                'durability': {
                    'avg': np.mean(durability_values) if durability_values else 0,
                    'max': np.max(durability_values) if durability_values else 0,
                    'min': np.min(durability_values) if durability_values else 0,
                    'std': np.std(durability_values) if durability_values else 0
                },
                'viscosity': {
                    'avg': np.mean(viscosity_values) if viscosity_values else 0,
                    'max': np.max(viscosity_values) if viscosity_values else 0,
                    'min': np.min(viscosity_values) if viscosity_values else 0,
                    'std': np.std(viscosity_values) if viscosity_values else 0
                }
            }
        return performance_analysis

    def _analyze_asphalt_maintenance_data(self, data: List[Dict] = None) -> Dict:
        """分析沥青维护记录"""
        asphalt_maintenance = data if data else self.learning_data['asphalt_maintenance']
        if not asphalt_maintenance:
            return {}

        type_maintenance = {}
        for maintenance in asphalt_maintenance:
            asphalt_type = maintenance.get('asphalt_type_id', 'unknown')
            if asphalt_type not in type_maintenance:
                type_maintenance[asphalt_type] = []
            type_maintenance[asphalt_type].append(maintenance)

        maintenance_analysis = {}
        for asphalt_type, maintenances in type_maintenance.items():
            maintenance_type_counts = {}
            for m in maintenances:
                m_type = m.get('maintenance_type', 'unknown')
                maintenance_type_counts[m_type] = maintenance_type_counts.get(m_type, 0) + 1

            total_cost = sum(m.get('cost', 0) for m in maintenances)
            avg_cost = total_cost / len(maintenances) if maintenances else 0

            maintenance_analysis[asphalt_type] = {
                'total_maintenances': len(maintenances),
                'maintenance_type_distribution': maintenance_type_counts,
                'total_cost': total_cost,
                'avg_cost': avg_cost
            }

        return maintenance_analysis

    def _analyze_asphalt_upgrade_data(self, data: List[Dict] = None) -> Dict:
        """分析沥青升级记录"""
        asphalt_upgrades = data if data else self.learning_data['asphalt_upgrades']
        if not asphalt_upgrades:
            return {}

        type_upgrades = {}
        for upgrade in asphalt_upgrades:
            asphalt_type = upgrade.get('asphalt_type_id', 'unknown')
            if asphalt_type not in type_upgrades:
                type_upgrades[asphalt_type] = []
            type_upgrades[asphalt_type].append(upgrade)

        upgrade_analysis = {}
        for asphalt_type, upgrades in type_upgrades.items():
            upgrade_type_counts = {}
            for u in upgrades:
                u_type = u.get('upgrade_type', 'unknown')
                upgrade_type_counts[u_type] = upgrade_type_counts.get(u_type, 0) + 1

            total_cost = sum(u.get('cost', 0) for u in upgrades)
            avg_cost = total_cost / len(upgrades) if upgrades else 0

            upgrade_analysis[asphalt_type] = {
                'total_upgrades': len(upgrades),
                'upgrade_type_distribution': upgrade_type_counts,
                'total_cost': total_cost,
                'avg_cost': avg_cost
            }

        return upgrade_analysis

    def _analyze_feature_importance(self, data: Dict) -> Dict:
        """分析特征重要性"""
        return {}

    def _detect_anomalies(self, data: Dict) -> List:
        """检测异常"""
        return []

    def _detect_asphalt_anomalies(self, data: Dict) -> List:
        """检测沥青异常"""
        return []

    def _generate_optimization_suggestions(self, *args) -> List:
        """生成优化建议"""
        return []

    def _apply_optimization_suggestions(self, suggestions: List):
        """应用优化建议"""
        pass

    def save_model(self):
        """保存模型"""
        pass

    def add_performance_data(self, data: Dict):
        """添加性能数据"""
        data['timestamp'] = time.time()
        self.learning_data['performance_metrics'].append(data)

    def add_resource_usage(self, data: Dict):
        """添加资源使用数据"""
        data['timestamp'] = time.time()
        self.learning_data['resource_usage'].append(data)

    def add_user_behavior(self, data: Dict):
        """添加用户行为数据"""
        data['timestamp'] = time.time()
        self.learning_data['user_behaviors'].append(data)

    def add_error_log(self, data: Dict):
        """添加错误日志"""
        data['timestamp'] = time.time()
        self.learning_data['error_logs'].append(data)

    def add_asphalt_performance_data(self, data: Dict):
        """添加沥青性能数据"""
        data['timestamp'] = time.time()
        self.learning_data['asphalt_performance'].append(data)

    def add_asphalt_maintenance_data(self, data: Dict):
        """添加沥青维护数据"""
        data['timestamp'] = time.time()
        self.learning_data['asphalt_maintenance'].append(data)

    def add_asphalt_upgrade_data(self, data: Dict):
        """添加沥青升级数据"""
        data['timestamp'] = time.time()
        self.learning_data['asphalt_upgrades'].append(data)

self_learning_system = AISelfLearningSystem()
