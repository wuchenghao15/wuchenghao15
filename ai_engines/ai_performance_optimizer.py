#!/usr/bin/env python3
"""AI性能优化Agent"""

import os
import re
import logging
import time
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIPerformanceOptimizer(AIEmployee):
    """AI性能优化Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI性能优化专家"):
        super().__init__(employee_id, name, 'performance_optimizer', 8)
        self.skills = [
            '性能监控', '性能分析', '代码优化',
            '数据库优化', '缓存策略', '负载均衡',
            '资源管理', '性能测试', '性能报告'
        ]
        self.optimization_history = []
        self.total_optimizations = 0
        self.total_savings = 0
    
    def monitor_system(self) -> Dict[str, Any]:
        """监控系统性能"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            'memory': {
                'total': round(memory.total / 1024 / 1024 / 1024, 2),
                'used': round(memory.used / 1024 / 1024 / 1024, 2),
                'available': round(memory.available / 1024 / 1024 / 1024, 2),
                'percent': memory.percent
            },
            'disk': {
                'total': round(disk.total / 1024 / 1024 / 1024, 2),
                'used': round(disk.used / 1024 / 1024 / 1024, 2),
                'free': round(disk.free / 1024 / 1024 / 1024, 2),
                'percent': disk.percent
            },
            'network': {
                'bytes_sent': round(network.bytes_sent / 1024 / 1024, 2),
                'bytes_recv': round(network.bytes_recv / 1024 / 1024, 2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'processes': len(psutil.pids()),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_performance(self, code: str) -> Dict[str, Any]:
        """分析代码性能问题"""
        issues = []
        
        perf_patterns = [
            (r'\b(list|dict|set)\(\)', '使用空构造函数', 'memory', 'low', '使用字面量[] {} set()'),
            (r'\bstr\(\)', '使用str()转换', 'cpu', 'low', '考虑直接字符串操作'),
            (r'\bint\(\)', '使用int()转换', 'cpu', 'low', '考虑直接数值操作'),
            (r'\bfloat\(\)', '使用float()转换', 'cpu', 'low', '考虑直接浮点操作'),
            (r'\bmap\(|filter\(|reduce\(', '使用高阶函数', 'cpu', 'medium', '考虑列表推导式'),
            (r'\bsorted\(', '使用sorted()', 'cpu', 'medium', '考虑原地排序'),
            (r'\breversed\(', '使用reversed()', 'memory', 'low', '考虑索引访问'),
            (r'\benumerate\(', '使用enumerate()', 'memory', 'low', '考虑直接range'),
            (r'\bzip\(', '使用zip()', 'memory', 'medium', '注意内存使用'),
            (r'\bslice\(', '使用slice()', 'memory', 'low', '考虑直接切片'),
        ]
        
        for pattern, description, category, severity, suggestion in perf_patterns:
            if re.search(pattern, code):
                issues.append({
                    'category': category,
                    'severity': severity,
                    'description': description,
                    'suggestion': suggestion
                })
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'optimization_score': max(0, 100 - len(issues) * 5),
            'timestamp': datetime.now().isoformat()
        }
    
    def optimize_code(self, code: str) -> Dict[str, Any]:
        """优化代码"""
        optimizations = []
        
        original_code = code
        
        code = re.sub(r'\b(list)\(\)', '[]', code)
        optimizations.append('将list()替换为[]')
        
        code = re.sub(r'\b(dict)\(\)', '{}', code)
        optimizations.append('将dict()替换为{}')
        
        code = re.sub(r'\b(set)\(\)', 'set()', code)
        
        original_lines = len(original_code.split('\n'))
        optimized_lines = len(code.split('\n'))
        
        self.total_optimizations += 1
        
        optimization_result = {
            'original_code': original_code,
            'optimized_code': code,
            'optimizations': optimizations,
            'lines_saved': original_lines - optimized_lines,
            'estimated_performance_gain': len(optimizations) * 2,
            'timestamp': datetime.now().isoformat()
        }
        
        self.optimization_history.append(optimization_result)
        return optimization_result
    
    def optimize_database_query(self, query: str) -> Dict[str, Any]:
        """优化数据库查询"""
        optimizations = []
        
        if 'SELECT *' in query:
            optimizations.append('避免使用SELECT *，指定具体字段')
        
        if 'ORDER BY' in query and 'LIMIT' not in query:
            optimizations.append('考虑添加LIMIT限制结果数量')
        
        if 'WHERE' not in query and 'LIMIT' not in query:
            optimizations.append('考虑添加WHERE条件或LIMIT')
        
        if 'LIKE %' in query:
            optimizations.append('考虑使用索引优化LIKE查询')
        
        return {
            'original_query': query,
            'optimizations': optimizations,
            'suggested_query': query.replace('SELECT *', 'SELECT'),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict:
        """获取优化统计"""
        return {
            'total_optimizations': self.total_optimizations,
            'total_savings': self.total_savings,
            'recent_optimizations': self.optimization_history[-5:],
            'system_status': self.monitor_system()
        }

performance_optimizer = AIPerformanceOptimizer('ai_performance_001')
