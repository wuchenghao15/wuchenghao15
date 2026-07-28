#!/usr/bin/env python3
"""AI智能数据分析Agent"""

import os
import re
import logging
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIDataAnalyzer(AIEmployee):
    """AI数据分析Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI数据分析专家"):
        super().__init__(employee_id, name, 'data_analyzer', 7)
        self.skills = [
            '数据分析', '数据可视化', '数据清洗',
            '统计分析', '趋势分析', '异常检测',
            '数据报告', '数据挖掘', '数据预测'
        ]
        self.analysis_history = []
        self.total_analyses = 0
    
    def analyze_numeric_data(self, data: List[float]) -> Dict[str, Any]:
        """分析数值数据"""
        if not data:
            return {'error': '数据为空'}
        
        analysis = {
            'count': len(data),
            'sum': sum(data),
            'min': min(data),
            'max': max(data),
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'variance': statistics.variance(data) if len(data) > 1 else 0,
            'std_dev': statistics.stdev(data) if len(data) > 1 else 0,
            'range': max(data) - min(data),
            'skewness': self._calculate_skewness(data),
            'kurtosis': self._calculate_kurtosis(data),
            'outliers': self._detect_outliers(data),
            'timestamp': datetime.now().isoformat()
        }
        
        self.total_analyses += 1
        self.analysis_history.append({'type': 'numeric', 'summary': analysis})
        
        return analysis
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """计算偏度"""
        if len(data) < 3:
            return 0
        
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        
        if std_dev == 0:
            return 0
        
        n = len(data)
        skewness = sum((x - mean) ** 3 for x in data) / (n * std_dev ** 3)
        
        return skewness
    
    def _calculate_kurtosis(self, data: List[float]) -> float:
        """计算峰度"""
        if len(data) < 4:
            return 0
        
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        
        if std_dev == 0:
            return 0
        
        n = len(data)
        kurtosis = sum((x - mean) ** 4 for x in data) / (n * std_dev ** 4) - 3
        
        return kurtosis
    
    def _detect_outliers(self, data: List[float]) -> List[float]:
        """检测异常值"""
        if len(data) < 4:
            return []
        
        q1 = self._percentile(data, 25)
        q3 = self._percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        
        return outliers
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        data_sorted = sorted(data)
        n = len(data_sorted)
        index = (percentile / 100) * (n - 1)
        
        if index.is_integer():
            return data_sorted[int(index)]
        
        lower_index = int(index)
        upper_index = lower_index + 1
        weight = index - lower_index
        
        return data_sorted[lower_index] * (1 - weight) + data_sorted[upper_index] * weight
    
    def analyze_text_data(self, text: str) -> Dict[str, Any]:
        """分析文本数据"""
        words = re.findall(r'\w+', text)
        sentences = re.split(r'[。！？;；]', text)
        
        analysis = {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / max(1, len(words)),
            'avg_sentence_length': sum(len(s) for s in sentences if s.strip()) / max(1, len([s for s in sentences if s.strip()])),
            'unique_words': len(set(words)),
            'word_density': len(set(words)) / max(1, len(words)),
            'top_words': self._get_top_words(words, 10),
            'timestamp': datetime.now().isoformat()
        }
        
        self.total_analyses += 1
        self.analysis_history.append({'type': 'text', 'summary': analysis})
        
        return analysis
    
    def _get_top_words(self, words: List[str], n: int = 10) -> List[Dict]:
        """获取高频词"""
        word_counts = {}
        for word in words:
            word_counts[word.lower()] = word_counts.get(word.lower(), 0) + 1
        
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{'word': word, 'count': count} for word, count in sorted_words[:n]]
    
    def analyze_trend(self, data: List[Dict], time_field: str = 'timestamp', value_field: str = 'value') -> Dict[str, Any]:
        """分析趋势数据"""
        if not data:
            return {'error': '数据为空'}
        
        values = [d[value_field] for d in data if value_field in d]
        times = [d[time_field] for d in data if time_field in d]
        
        if not values:
            return {'error': '没有有效的数值数据'}
        
        analysis = {
            'total_points': len(data),
            'first_value': values[0],
            'last_value': values[-1],
            'change': values[-1] - values[0],
            'change_percent': ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0,
            'trend': self._detect_trend(values),
            'seasonality': self._detect_seasonality(values),
            'correlation': self._calculate_correlation(values),
            'timestamp': datetime.now().isoformat()
        }
        
        self.total_analyses += 1
        self.analysis_history.append({'type': 'trend', 'summary': analysis})
        
        return analysis
    
    def _detect_trend(self, values: List[float]) -> str:
        """检测趋势"""
        if len(values) < 2:
            return 'stable'
        
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 0:
            return 'upward'
        elif avg_change < 0:
            return 'downward'
        else:
            return 'stable'
    
    def _detect_seasonality(self, values: List[float]) -> bool:
        """检测季节性"""
        if len(values) < 12:
            return False
        
        return True
    
    def _calculate_correlation(self, values: List[float]) -> float:
        """计算自相关"""
        if len(values) < 2:
            return 0
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        if std_dev == 0:
            return 0
        
        n = len(values)
        lag1_values = values[:-1]
        lag1_values_shifted = values[1:]
        
        correlation = sum((lag1_values[i] - mean) * (lag1_values_shifted[i] - mean) for i in range(len(lag1_values))) / ((n - 1) * std_dev ** 2)
        
        return correlation
    
    def generate_report(self, analysis: Dict) -> str:
        """生成分析报告"""
        report_lines = []
        report_lines.append("# 数据分析报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        for key, value in analysis.items():
            if key != 'timestamp' and key != 'outliers' and key != 'top_words':
                report_lines.append(f"- {key}: {value}")
        
        if 'outliers' in analysis and analysis['outliers']:
            report_lines.append("")
            report_lines.append("## 异常值")
            for outlier in analysis['outliers'][:10]:
                report_lines.append(f"- {outlier}")
        
        if 'top_words' in analysis and analysis['top_words']:
            report_lines.append("")
            report_lines.append("## 高频词")
            for item in analysis['top_words']:
                report_lines.append(f"- {item['word']}: {item['count']}次")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取分析统计"""
        return {
            'total_analyses': self.total_analyses,
            'recent_analyses': self.analysis_history[-5:]
        }

data_analyzer = AIDataAnalyzer('ai_data_analyzer_001')
