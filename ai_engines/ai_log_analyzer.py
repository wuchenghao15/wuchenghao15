#!/usr/bin/env python3
"""AI智能日志分析Agent"""

import os
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AILogAnalyzer(AIEmployee):
    """AI日志分析Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI日志分析专家"):
        super().__init__(employee_id, name, 'log_analyzer', 8)
        self.skills = [
            '日志收集', '日志解析', '日志过滤',
            '异常检测', '性能分析', '安全分析',
            '趋势分析', '日志报告', '告警生成'
        ]
        self.log_history = []
        self.total_logs = 0
        self.error_count = 0
        self.warning_count = 0
    
    def collect_logs(self, log_source: str, logs: List[str]) -> Dict[str, Any]:
        """收集日志"""
        collected = []
        for log in logs:
            parsed = self._parse_log(log)
            collected.append(parsed)
            self.log_history.append(parsed)
            self.total_logs += 1
            
            if parsed.get('level') == 'ERROR':
                self.error_count += 1
            elif parsed.get('level') == 'WARNING':
                self.warning_count += 1
        
        return {'success': True, 'collected_count': len(collected), 'total_logs': self.total_logs}
    
    def _parse_log(self, log_line: str) -> Dict[str, Any]:
        """解析日志行"""
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'\[(ERROR|WARNING|INFO|DEBUG|CRITICAL)\]',
            r'\[(\w+)\]',
            r'(\d+)ms',
            r'(Exception|Error|Traceback)'
        ]
        
        result = {
            'raw': log_line,
            'timestamp': '',
            'level': 'INFO',
            'source': '',
            'duration_ms': 0,
            'has_error': False,
            'parsed_at': datetime.now().isoformat()
        }
        
        for pattern in patterns:
            match = re.search(pattern, log_line)
            if match:
                if 'timestamp' not in result or not result['timestamp']:
                    try:
                        datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                        result['timestamp'] = match.group(1)
                        continue
                    except:
                        pass
                
                level = match.group(1).upper()
                if level in ['ERROR', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL']:
                    result['level'] = level
                    continue
                
                if not result['source']:
                    result['source'] = match.group(1)
                    continue
                
                if 'ms' in match.group(1):
                    result['duration_ms'] = int(match.group(1).replace('ms', ''))
                    continue
                
                if match.group(1) in ['Exception', 'Error', 'Traceback']:
                    result['has_error'] = True
        
        return result
    
    def filter_logs(self, **kwargs) -> Dict[str, Any]:
        """过滤日志"""
        filtered = self.log_history
        
        if 'level' in kwargs:
            filtered = [l for l in filtered if l.get('level') == kwargs['level']]
        
        if 'source' in kwargs:
            filtered = [l for l in filtered if l.get('source') == kwargs['source']]
        
        if 'has_error' in kwargs:
            filtered = [l for l in filtered if l.get('has_error') == kwargs['has_error']]
        
        if 'start_time' in kwargs:
            filtered = [l for l in filtered if l.get('timestamp', '') >= kwargs['start_time']]
        
        if 'end_time' in kwargs:
            filtered = [l for l in filtered if l.get('timestamp', '') <= kwargs['end_time']]
        
        return {'success': True, 'logs': filtered, 'count': len(filtered)}
    
    def detect_anomalies(self) -> Dict[str, Any]:
        """检测异常"""
        anomalies = []
        
        error_logs = [l for l in self.log_history if l.get('level') == 'ERROR']
        if len(error_logs) > 10:
            anomalies.append({
                'type': 'error_burst',
                'message': '错误日志数量异常',
                'count': len(error_logs),
                'severity': 'high'
            })
        
        slow_logs = [l for l in self.log_history if l.get('duration_ms', 0) > 1000]
        if slow_logs:
            anomalies.append({
                'type': 'performance_issue',
                'message': '存在慢请求',
                'count': len(slow_logs),
                'severity': 'medium'
            })
        
        critical_errors = [l for l in self.log_history if l.get('level') == 'CRITICAL']
        if critical_errors:
            anomalies.append({
                'type': 'critical_error',
                'message': '存在严重错误',
                'count': len(critical_errors),
                'severity': 'critical'
            })
        
        return {
            'success': True,
            'anomalies': anomalies,
            'total_anomalies': len(anomalies)
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        durations = [l.get('duration_ms', 0) for l in self.log_history if l.get('duration_ms', 0) > 0]
        
        if not durations:
            return {'success': True, 'message': '没有性能数据'}
        
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        p95_duration = sorted(durations)[int(len(durations) * 0.95)]
        
        return {
            'success': True,
            'performance': {
                'avg_duration_ms': round(avg_duration, 2),
                'max_duration_ms': max_duration,
                'min_duration_ms': min_duration,
                'p95_duration_ms': p95_duration,
                'sample_count': len(durations)
            }
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        errors = [l for l in self.log_history if l.get('level') == 'ERROR']
        warnings = [l for l in self.log_history if l.get('level') == 'WARNING']
        info = [l for l in self.log_history if l.get('level') == 'INFO']
        
        return {
            'success': True,
            'report': {
                'generated_at': datetime.now().isoformat(),
                'total_logs': self.total_logs,
                'error_count': len(errors),
                'warning_count': len(warnings),
                'info_count': len(info),
                'error_rate': round(len(errors) / max(self.total_logs, 1) * 100, 2),
                'sources': list(set(l.get('source', '') for l in self.log_history if l.get('source')))
            }
        }
    
    def generate_alert(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """生成告警"""
        alert = {
            'alert_id': f'alert_{datetime.now().timestamp()}',
            'type': anomaly.get('type', ''),
            'message': anomaly.get('message', ''),
            'severity': anomaly.get('severity', 'medium'),
            'created_at': datetime.now().isoformat(),
            'source': self.name
        }
        return {'success': True, 'alert': alert}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_logs': self.total_logs,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'log_history_count': len(self.log_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }