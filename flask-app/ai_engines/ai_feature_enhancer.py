# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI功能增强脚本
为项目添加新的AI功能和智能特性
"""

import os
import sys
import logging
import time
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_feature_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AI_Feature_Enhancer')

class AIFeatureEnhancer:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.features_added = []

        logger.info("AI功能增强脚本初始化完成")

    def add_ai_log_analyzer(self):
        logger.info("开始添加AI日志分析功能")

        log_analyzer_path = os.path.join(self.project_root, 'app/ai/ai_log_analyzer.py')
        log_analyzer_code = '''
"""
自动分析日志文件,检测异常模式
"""
import os
import re
import logging
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger('AI_Log_Analyzer')

class AILogAnalyzer:

    def __init__(self, log_file_path=None):
        self.log_file_path = log_file_path
        self.log_patterns = {
            'error': r'ERROR|Error|error',
            'warning': r'WARNING|Warning|warning',
            'exception': r'Exception|Traceback|traceback',
            'critical': r'CRITICAL|Critical|critical'
        }
        self.recent_logs = deque(maxlen=1000)
        self.anomaly_count = defaultdict(int)

    def analyze_log_file(self, log_content=None):
        if log_content:
            logs = log_content.split('\\n')
        elif self.log_file_path and os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()
        else:
            logger.error("无法读取日志文件")
            return None

        analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'total_logs': len(logs),
            'anomalies': [],
            'stats': defaultdict(int)
        }

        for log in logs:
            log = log.strip()
            if not log:
                continue

            self.recent_logs.append(log)

            for anomaly_type, pattern in self.log_patterns.items():
                if re.search(pattern, log):
                    self.anomaly_count[anomaly_type] += 1
                    analysis_results['anomalies'].append({
                        'type': anomaly_type,
                        'log': log,
                        'timestamp': datetime.now().isoformat()
                    })
                    analysis_results['stats'][anomaly_type] += 1

        duplicate_errors = self._detect_duplicate_errors()
        if duplicate_errors:
            analysis_results['duplicate_errors'] = duplicate_errors

        return analysis_results

    def _detect_duplicate_errors(self):
        duplicate_errors = []
        error_counts = defaultdict(int)
        for log in self.recent_logs:
            for anomaly_type, pattern in self.log_patterns.items():
                if re.search(pattern, log):
                    error_counts[log] += 1

        for error, count in error_counts.items():
            if count > 2:
                duplicate_errors.append({
                    'error': error,
                    'count': count,
                    'type': 'duplicate_error'
                })

        return duplicate_errors

    def get_anomaly_summary(self):
        return dict(self.anomaly_count)

    def suggest_fixes(self, analysis_results):
        suggestions = []

        if analysis_results['stats']['error'] > 5:
            suggestions.append({
                'type': 'high_error_rate',
                'suggestion': '系统错误率较高,建议检查错误日志并修复主要问题',
                'priority': 'high'
            })

        if analysis_results['stats']['warning'] > 10:
            suggestions.append({
                'type': 'high_warning_rate',
                'suggestion': '系统警告较多,建议检查警告日志并优化系统配置',
                'priority': 'medium'
            })

        if 'duplicate_errors' in analysis_results and len(analysis_results['duplicate_errors']) > 2:
            suggestions.append({
                'type': 'duplicate_errors',
                'suggestion': '存在重复错误,建议修复根本原因以减少日志噪声',
                'priority': 'medium'
            })

        return suggestions
'''

        try:
            os.makedirs(os.path.dirname(log_analyzer_path), exist_ok=True)

            with open(log_analyzer_path, 'w', encoding='utf-8') as f:
                f.write(log_analyzer_code)
            logger.info(f"已创建AI日志分析器: {log_analyzer_path}")
            self.features_added.append('ai_log_analyzer')
            return True
        except Exception as e:
            logger.error(f"创建AI日志分析器失败: {e}")
            return False

    def add_ai_performance_monitor(self):
        logger.info("开始添加AI性能监控功能")

        performance_monitor_path = os.path.join(self.project_root, 'app/ai/ai_performance_monitor.py')
        performance_code = '''
"""
AI性能监控器
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger('AI_Performance_Monitor')

class AIPerformanceMonitor:

    def __init__(self):
        self.metrics_history = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': []
        }
        self.metric_window = 60
        self.optimization_suggestions = []

    def get_system_metrics(self) -> Dict[str, Any]:
        current_time = time.time()

        try:
            import psutil

            cpu_usage = psutil.cpu_percent(interval=0.1)

            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available = memory.available / (1024 * 1024)

            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            disk_free = disk.free / (1024 * 1024 * 1024)

            network = psutil.net_io_counters()
            network_sent = network.bytes_sent / (1024 * 1024)
            network_recv = network.bytes_recv / (1024 * 1024)

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_usage
                },
                'memory': {
                    'usage_percent': memory_usage,
                    'available_mb': memory_available
                },
                'disk': {
                    'usage_percent': disk_usage,
                    'free_gb': disk_free
                },
                'network': {
                    'sent_mb': network_sent,
                    'recv_mb': network_recv
                }
            }
        except ImportError:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {'usage_percent': 0},
                'memory': {'usage_percent': 0, 'available_mb': 0},
                'disk': {'usage_percent': 0, 'free_gb': 0},
                'network': {'sent_mb': 0, 'recv_mb': 0}
            }

        self._update_metrics_history(metrics)

        anomalies = self._detect_performance_anomalies(metrics)
        if anomalies:
            metrics['anomalies'] = anomalies
            metrics['suggestions'] = self._generate_optimization_suggestions(anomalies)

        return metrics

    def _update_metrics_history(self, metrics: Dict[str, Any]):
        current_time = time.time()

        for metric_type in self.metrics_history:
            self.metrics_history[metric_type] = [
                m for m in self.metrics_history[metric_type]
                if current_time - m['timestamp'] < self.metric_window
            ]

        for metric_type, data in metrics.items():
            if metric_type != 'timestamp' and isinstance(data, dict):
                self.metrics_history[metric_type].append({
                    'timestamp': current_time,
                    'data': data
                })

    def _detect_performance_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []

        if metrics['cpu']['usage_percent'] > 80:
            anomalies.append({
                'type': 'high_cpu_usage',
                'value': metrics['cpu']['usage_percent'],
                'threshold': 80,
                'message': f'CPU使用率过高: {metrics["cpu"]["usage_percent"]}%'
            })

        if metrics['memory']['usage_percent'] > 85:
            anomalies.append({
                'type': 'high_memory_usage',
                'value': metrics['memory']['usage_percent'],
                'threshold': 85,
                'message': f'内存使用率过高: {metrics["memory"]["usage_percent"]}%'
            })

        if metrics['disk']['usage_percent'] > 90:
            anomalies.append({
                'type': 'high_disk_usage',
                'value': metrics['disk']['usage_percent'],
                'threshold': 90,
                'message': f'磁盘使用率过高: {metrics["disk"]["usage_percent"]}%'
            })

        return anomalies

    def _generate_optimization_suggestions(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        suggestions = []

        for anomaly in anomalies:
            if anomaly['type'] == 'high_cpu_usage':
                suggestions.append({
                    'type': 'optimize_cpu',
                    'suggestion': '检查CPU密集型任务,优化算法或增加计算资源',
                    'priority': 'high',
                    'related_anomaly': anomaly['message']
                })
            elif anomaly['type'] == 'high_memory_usage':
                suggestions.append({
                    'type': 'optimize_memory',
                    'suggestion': '检查内存泄漏,或增加系统内存',
                    'priority': 'high',
                    'related_anomaly': anomaly['message']
                })
            elif anomaly['type'] == 'high_disk_usage':
                suggestions.append({
                    'type': 'optimize_disk',
                    'suggestion': '清理磁盘空间,或扩展磁盘容量',
                    'priority': 'medium',
                    'related_anomaly': anomaly['message']
                })

        return suggestions

    def get_performance_trend(self) -> Dict[str, Any]:
        trend = {
            'timestamp': datetime.now().isoformat(),
            'trends': {}
        }

        for metric_type, history in self.metrics_history.items():
            if history:
                avg_values = {}
                for metric in history:
                    for key, value in metric['data'].items():
                        if key not in avg_values:
                            avg_values[key] = []
                        avg_values[key].append(value)

                trend['trends'][metric_type] = {
                    key: sum(values) / len(values) for key, values in avg_values.items()
                }

        return trend
'''

        try:
            os.makedirs(os.path.dirname(performance_monitor_path), exist_ok=True)

            with open(performance_monitor_path, 'w', encoding='utf-8') as f:
                f.write(performance_code)
            logger.info(f"已创建AI性能监控器: {performance_monitor_path}")
            self.features_added.append('ai_performance_monitor')
            return True
        except Exception as e:
            logger.error(f"创建AI性能监控器失败: {e}")
            return False

    def add_ai_config_optimizer(self):
        logger.info("开始添加AI配置优化器")

        config_optimizer_path = os.path.join(self.project_root, 'app/ai/ai_config_optimizer.py')
        config_code = '''
"""
AI配置优化器
智能优化系统配置
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger('AI_Config_Optimizer')

class AIConfigOptimizer:

    def __init__(self):
        self.optimal_configs = {
            'flask': {
                'debug': False,
                'secret_key': 'secure_random_key',
                'session_cookie_httponly': True,
                'session_cookie_samesite': 'Strict',
                'permanent_session_lifetime': 3600
            },
            'database': {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'max_overflow': 20
            },
            'security': {
                'rate_limit': 100,
                'csrf_protection': True,
                'xss_protection': True
            }
        }

    def analyze_config(self, config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        if config_type not in self.optimal_configs:
            logger.error(f"不支持的配置类型: {config_type}")
            return None

        optimal_config = self.optimal_configs[config_type]
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'config_type': config_type,
            'current_config': config,
            'suggestions': []
        }

        for key, optimal_value in optimal_config.items():
            if key in config:
                current_value = config[key]
                if current_value != optimal_value:
                    suggestion = {
                        'config_key': key,
                        'current_value': current_value,
                        'optimal_value': optimal_value,
                        'reason': self._get_optimization_reason(config_type, key, optimal_value),
                        'priority': self._get_suggestion_priority(config_type, key)
                    }
                    analysis['suggestions'].append(suggestion)
            else:
                analysis['suggestions'].append({
                    'config_key': key,
                    'current_value': None,
                    'optimal_value': optimal_value,
                    'reason': f'缺少推荐的配置项 {key}',
                    'priority': 'medium'
                })
        return analysis

    def _get_optimization_reason(self, config_type: str, key: str, optimal_value: Any) -> str:
        reasons = {
            'flask': {
                'debug': '生产环境中应关闭调试模式以提高安全性',
                'secret_key': '应使用安全的随机密钥保护会话',
                'session_cookie_secure': '安全的Cookie应仅通过HTTPS传输',
                'session_cookie_httponly': 'HTTPOnly Cookie可防止XSS攻击窃取会话',
                'session_cookie_samesite': 'Strict SameSite策略可防止CSRF攻击',
                'permanent_session_lifetime': '合理的会话生命周期可提高安全性'
            },
            'database': {
                'pool_size': '适当的连接池大小可提高数据库性能',
                'pool_timeout': '合理的连接超时可防止长时间等待',
                'pool_recycle': '定期回收连接可防止连接泄漏',
                'max_overflow': '适当的溢出连接数可处理峰值流量'
            },
            'security': {
                'csrf_protection': 'CSRF保护可防止跨站请求伪造攻击',
                'xss_protection': 'XSS保护可防止跨站脚本攻击'
            }
        }

        return reasons.get(config_type, {}).get(key, f'优化 {key} 可提高系统性能或安全性')

    def _get_suggestion_priority(self, config_type: str, key: str) -> str:
        high_priority = {
            'flask': ['secret_key', 'debug', 'session_cookie_secure'],
            'database': ['pool_size', 'pool_recycle'],
            'security': ['csrf_protection', 'xss_protection']
        }

        if key in high_priority.get(config_type, []):
            return 'high'
        return 'medium'

    def optimize_config(self, config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        analysis = self.analyze_config(config, config_type)
        if not analysis:
            return config

        optimized_config = config.copy()

        for suggestion in analysis['suggestions']:
            if suggestion['priority'] == 'high':
                optimized_config[suggestion['config_key']] = suggestion['optimal_value']

        return optimized_config

    def load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return None

    def save_optimized_config(self, config: Dict[str, Any], output_path: str):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"优化后的配置已保存到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
'''

        try:
            os.makedirs(os.path.dirname(config_optimizer_path), exist_ok=True)

            with open(config_optimizer_path, 'w', encoding='utf-8') as f:
                f.write(config_code)

            logger.info(f"已创建AI配置优化器: {config_optimizer_path}")
            self.features_added.append('ai_config_optimizer')
            return True
        except Exception as e:
            logger.error(f"创建AI配置优化器失败: {e}")
            return False

    def add_ai_feature_integration(self):
        logger.info("开始集成AI功能到主应用")

        app_file_path = os.path.join(self.project_root, 'app.py')

        try:
            with open(app_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'from app.ai.ai_log_analyzer import AILogAnalyzer' not in content:
                content = content.replace(
                    'from app.utils.database import get_db_connection',
                    'from app.utils.database import get_db_connection\nfrom app.ai.ai_log_analyzer import AILogAnalyzer\nfrom app.ai.ai_performance_monitor import AIPerformanceMonitor\nfrom app.ai.ai_config_optimizer import AIConfigOptimizer'
                )

                if 'app = Flask(__name__)' in content:
                    content = content.replace(
                        'app = Flask(__name__)',
                        'app = Flask(__name__)\n\n# 初始化AI功能\nai_log_analyzer = AILogAnalyzer()\nai_performance_monitor = AIPerformanceMonitor()\nai_config_optimizer = AIConfigOptimizer()'
                    )

                ai_api_endpoints = '''

# ------------------------------
# AI功能API端点
# ------------------------------

@app.route('/api/ai/logs/analyze', methods=['POST'])
def analyze_logs():
    """AI日志分析API"""
    data = request.get_json() or {}
    log_content = data.get('log_content')
    
    analysis = ai_log_analyzer.analyze_log_file(log_content)
    if analysis:
        return custom_json_response(analysis, status_code=200)
    return custom_json_response({'error': '日志分析失败'}, status_code=500)

@app.route('/api/ai/performance', methods=['GET'])
def get_performance_metrics():
    """获取AI性能监控指标"""
    metrics = ai_performance_monitor.get_system_metrics()
    return custom_json_response(metrics, status_code=200)

@app.route('/api/ai/config/analyze', methods=['POST'])
def analyze_config():
    """分析配置并提供优化建议"""
    data = request.get_json() or {}
    config = data.get('config')
    config_type = data.get('config_type')
    
    if not config or not config_type:
        return custom_json_response({'error': '缺少配置或配置类型'}, status_code=400)
    
    analysis = ai_config_optimizer.analyze_config(config, config_type)
    if analysis:
        return custom_json_response(analysis, status_code=200)
    return custom_json_response({'error': '配置分析失败'}, status_code=500)

@app.route('/api/ai/config/optimize', methods=['POST'])
def optimize_config():
    """自动优化配置"""
    data = request.get_json() or {}
    config = data.get('config')
    config_type = data.get('config_type')
    
    if not config or not config_type:
        return custom_json_response({'error': '缺少配置或配置类型'}, status_code=400)
    
    optimized_config = ai_config_optimizer.optimize_config(config, config_type)
    return custom_json_response({'optimized_config': optimized_config}, status_code=200)
'''
                if 'if __name__ ==' in content:
                    content = content.replace(
                        'if __name__ ==',
                        ai_api_endpoints + '\nif __name__ =='
                    )

                with open(app_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                logger.info("已集成AI功能到主应用")
                self.features_added.append('ai_feature_integration')
                return True
            else:
                logger.info("AI功能已集成,跳过")
                return True
        except Exception as e:
            logger.error(f"集成AI功能失败: {e}")
            return False

    def run_comprehensive_enhancement(self):
        logger.info("开始执行全面的AI功能增强")

        self.add_ai_log_analyzer()

        self.add_ai_performance_monitor()

        self.add_ai_config_optimizer()

        self.add_ai_feature_integration()

        logger.info(f"AI功能增强完成,添加了以下功能: {', '.join(self.features_added)}")

        return {
            'success': True,
            'features_added': self.features_added,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

if __name__ == "__main__":
    enhancer = AIFeatureEnhancer()
    result = enhancer.run_comprehensive_enhancement()
    print(f"AI功能增强结果: {result}")
