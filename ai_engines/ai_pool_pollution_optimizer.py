# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI池污染优化系统 - 检测和清理AI池中的数据污染、模型污染和缓存污染
"""

import logging
import os
import json
import time
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_pool_pollution_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PollutionType(Enum):
    DATA_POLLUTION = "数据污染"
    MODEL_POLLUTION = "模型污染"
    CACHE_POLLUTION = "缓存污染"
    PARAMETER_POLLUTION = "参数污染"
    KNOWLEDGE_POLLUTION = "知识污染"

class PollutionSeverity(Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "严重"

class PollutionDetector:
    """污染检测器"""
    
    def __init__(self):
        self.pollution_signatures = {
            'data_anomaly': ['nan_value', 'outlier', 'duplicate', 'invalid_format', 'missing_required'],
            'model_drift': ['concept_drift', 'data_drift', 'performance_degradation', 'prediction_shift'],
            'cache_stale': ['expired_entry', 'inconsistent_data', 'orphaned_cache', 'memory_leak'],
            'param_corruption': ['invalid_value', 'out_of_range', 'type_mismatch', 'dependency_conflict'],
            'knowledge_pollution': ['outdated_knowledge', 'contradictory_facts', 'misinformation']
        }
        
    def detect_data_pollution(self, data: Any) -> List[Dict]:
        """检测数据污染"""
        issues = []
        
        if data is None:
            issues.append({'type': 'missing_required', 'severity': 'high', 'message': '数据为空'})
            return issues
            
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    issues.append({
                        'type': 'nan_value',
                        'severity': 'medium',
                        'message': f'字段 {key} 值为空',
                        'field': key
                    })
                elif isinstance(value, str) and len(value.strip()) == 0:
                    issues.append({
                        'type': 'invalid_format',
                        'severity': 'low',
                        'message': f'字段 {key} 为空字符串',
                        'field': key
                    })
                    
        elif isinstance(data, list):
            seen = set()
            for i, item in enumerate(data):
                item_hash = hashlib.md5(str(item).encode()).hexdigest()
                if item_hash in seen:
                    issues.append({
                        'type': 'duplicate',
                        'severity': 'low',
                        'message': f'列表第 {i} 项重复',
                        'index': i
                    })
                seen.add(item_hash)
                
        return issues
    
    def detect_model_pollution(self, model_metrics: Dict) -> List[Dict]:
        """检测模型污染"""
        issues = []
        
        if 'accuracy' in model_metrics:
            if model_metrics['accuracy'] < 0.7:
                issues.append({
                    'type': 'performance_degradation',
                    'severity': 'high',
                    'message': f'模型准确率 {model_metrics["accuracy"]} 低于阈值',
                    'current_value': model_metrics['accuracy'],
                    'threshold': 0.7
                })
                
        if 'drift_score' in model_metrics:
            if model_metrics['drift_score'] > 0.3:
                issues.append({
                    'type': 'concept_drift',
                    'severity': 'medium',
                    'message': f'模型漂移分数 {model_metrics["drift_score"]} 超过阈值',
                    'current_value': model_metrics['drift_score'],
                    'threshold': 0.3
                })
                
        if 'prediction_shift' in model_metrics:
            if abs(model_metrics['prediction_shift']) > 0.2:
                issues.append({
                    'type': 'prediction_shift',
                    'severity': 'high',
                    'message': f'预测分布偏移 {model_metrics["prediction_shift"]} 超过阈值',
                    'current_value': model_metrics['prediction_shift'],
                    'threshold': 0.2
                })
                
        return issues
    
    def detect_cache_pollution(self, cache_entry: Dict) -> List[Dict]:
        """检测缓存污染"""
        issues = []
        
        if 'expires_at' in cache_entry:
            try:
                expiry = datetime.fromisoformat(cache_entry['expires_at'])
                if expiry < datetime.now():
                    issues.append({
                        'type': 'expired_entry',
                        'severity': 'medium',
                        'message': f'缓存项已过期: {cache_entry.get("key", "unknown")}',
                        'expired_at': cache_entry['expires_at']
                    })
            except Exception:
                issues.append({
                    'type': 'invalid_format',
                    'severity': 'low',
                    'message': f'缓存过期时间格式无效: {cache_entry.get("key", "unknown")}'
                })
                
        if 'data_hash' in cache_entry and 'original_hash' in cache_entry:
            if cache_entry['data_hash'] != cache_entry['original_hash']:
                issues.append({
                    'type': 'inconsistent_data',
                    'severity': 'high',
                    'message': f'缓存数据与原始数据不一致: {cache_entry.get("key", "unknown")}'
                })
                
        return issues
    
    def detect_parameter_pollution(self, params: Dict) -> List[Dict]:
        """检测参数污染"""
        issues = []
        
        for param_name, param_info in params.items():
            value = param_info.get('value')
            param_type = param_info.get('type')
            
            try:
                if param_type == 'int' and not isinstance(value, int):
                    issues.append({
                        'type': 'type_mismatch',
                        'severity': 'medium',
                        'message': f'参数 {param_name} 类型错误，期望 int，实际 {type(value).__name__}',
                        'param_name': param_name,
                        'expected_type': 'int',
                        'actual_type': type(value).__name__
                    })
                elif param_type == 'float' and not isinstance(value, float):
                    issues.append({
                        'type': 'type_mismatch',
                        'severity': 'medium',
                        'message': f'参数 {param_name} 类型错误，期望 float，实际 {type(value).__name__}',
                        'param_name': param_name,
                        'expected_type': 'float',
                        'actual_type': type(value).__name__
                    })
                elif param_type == 'bool' and not isinstance(value, bool):
                    issues.append({
                        'type': 'type_mismatch',
                        'severity': 'medium',
                        'message': f'参数 {param_name} 类型错误，期望 bool，实际 {type(value).__name__}',
                        'param_name': param_name,
                        'expected_type': 'bool',
                        'actual_type': type(value).__name__
                    })
                    
                if isinstance(value, (int, float)):
                    if value < 0 and param_name not in ['error_rate', 'loss']:
                        issues.append({
                            'type': 'out_of_range',
                            'severity': 'low',
                            'message': f'参数 {param_name} 值为负数',
                            'param_name': param_name,
                            'value': value
                        })
                        
            except Exception as e:
                issues.append({
                    'type': 'invalid_value',
                    'severity': 'high',
                    'message': f'参数 {param_name} 验证失败: {str(e)}',
                    'param_name': param_name
                })
                
        return issues

class PollutionCleaner:
    """污染清理器"""
    
    def __init__(self):
        self.cleanup_strategies = {
            'nan_value': self._clean_nan_value,
            'outlier': self._clean_outlier,
            'duplicate': self._clean_duplicate,
            'invalid_format': self._clean_invalid_format,
            'missing_required': self._clean_missing_required,
            'expired_entry': self._clean_expired_entry,
            'inconsistent_data': self._clean_inconsistent_data,
            'type_mismatch': self._clean_type_mismatch,
            'out_of_range': self._clean_out_of_range
        }
        
    def _clean_nan_value(self, data: Dict, issue: Dict) -> Dict:
        """清理空值"""
        field = issue.get('field')
        if field in data:
            data[field] = '' if isinstance(data[field], str) else 0
            logger.info(f'清理空值: {field} -> {data[field]}')
        return data
        
    def _clean_outlier(self, data: List, issue: Dict) -> List:
        """清理异常值"""
        index = issue.get('index')
        if index is not None and 0 <= index < len(data):
            del data[index]
            logger.info(f'清理异常值: 索引 {index}')
        return data
        
    def _clean_duplicate(self, data: List, issue: Dict) -> List:
        """清理重复项"""
        index = issue.get('index')
        if index is not None and 0 <= index < len(data):
            del data[index]
            logger.info(f'清理重复项: 索引 {index}')
        return data
        
    def _clean_invalid_format(self, data: Dict, issue: Dict) -> Dict:
        """清理无效格式"""
        field = issue.get('field')
        if field in data:
            if isinstance(data[field], str):
                data[field] = data[field].strip()
            logger.info(f'清理无效格式: {field}')
        return data
        
    def _clean_missing_required(self, data: Dict, issue: Dict) -> Dict:
        """清理缺失必填项"""
        return data
        
    def _clean_expired_entry(self, cache: Dict, issue: Dict) -> Dict:
        """清理过期缓存"""
        key = issue.get('key', issue.get('message', 'unknown').split(':')[-1].strip())
        if key in cache:
            del cache[key]
            logger.info(f'清理过期缓存: {key}')
        return cache
        
    def _clean_inconsistent_data(self, cache: Dict, issue: Dict) -> Dict:
        """清理不一致数据"""
        key = issue.get('key', issue.get('message', 'unknown').split(':')[-1].strip())
        if key in cache:
            del cache[key]
            logger.info(f'清理不一致缓存: {key}')
        return cache
        
    def _clean_type_mismatch(self, params: Dict, issue: Dict) -> Dict:
        """清理类型不匹配"""
        param_name = issue.get('param_name')
        expected_type = issue.get('expected_type')
        
        if param_name in params:
            try:
                if expected_type == 'int':
                    params[param_name]['value'] = int(params[param_name]['value'])
                elif expected_type == 'float':
                    params[param_name]['value'] = float(params[param_name]['value'])
                elif expected_type == 'bool':
                    params[param_name]['value'] = bool(params[param_name]['value'])
                logger.info(f'修复类型不匹配: {param_name} -> {expected_type}')
            except Exception:
                logger.warning(f'无法修复类型不匹配: {param_name}')
                
        return params
        
    def _clean_out_of_range(self, params: Dict, issue: Dict) -> Dict:
        """清理超出范围的值"""
        param_name = issue.get('param_name')
        if param_name in params:
            params[param_name]['value'] = max(0, params[param_name]['value'])
            logger.info(f'修复超出范围: {param_name} -> {params[param_name]["value"]}')
        return params
        
    def clean(self, data: Any, issues: List[Dict]) -> Any:
        """执行清理"""
        for issue in issues:
            issue_type = issue.get('type')
            if issue_type in self.cleanup_strategies:
                data = self.cleanup_strategies[issue_type](data, issue)
        return data

class AIPoolPollutionOptimizer:
    """AI池污染优化器"""
    
    def __init__(self, db_path='ai_pool_pollution.db'):
        self.db_path = db_path
        self.detector = PollutionDetector()
        self.cleaner = PollutionCleaner()
        self._init_db()
        
        self.pollution_stats = {
            'detected': 0,
            'cleaned': 0,
            'pending': 0,
            'last_cleanup': None
        }
        
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pollution_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT NOT NULL,
            pollution_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cleaned_at TIMESTAMP,
            cleaned BOOLEAN DEFAULT FALSE,
            cleanup_method TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleanup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT NOT NULL,
            total_issues INTEGER NOT NULL,
            cleaned_issues INTEGER NOT NULL,
            failed_issues INTEGER NOT NULL,
            cleanup_time REAL NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS pool_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT UNIQUE NOT NULL,
            health_score REAL DEFAULT 1.0,
            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'healthy'
            )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pollution_events_pool ON pollution_events(pool_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pollution_events_cleaned ON pollution_events(cleaned)')
            
            conn.commit()
            
    def scan_pool(self, pool_name: str, pool_data: Dict) -> Dict:
        """扫描AI池检测污染"""
        logger.info(f'开始扫描AI池: {pool_name}')
        
        all_issues = []
        
        if 'data' in pool_data:
            data_issues = self.detector.detect_data_pollution(pool_data['data'])
            for issue in data_issues:
                all_issues.append({
                    'pollution_type': 'DATA_POLLUTION',
                    'severity': issue['severity'],
                    'issue_type': issue['type'],
                    'message': issue['message'],
                    'details': json.dumps(issue)
                })
                
        if 'model_metrics' in pool_data:
            model_issues = self.detector.detect_model_pollution(pool_data['model_metrics'])
            for issue in model_issues:
                all_issues.append({
                    'pollution_type': 'MODEL_POLLUTION',
                    'severity': issue['severity'],
                    'issue_type': issue['type'],
                    'message': issue['message'],
                    'details': json.dumps(issue)
                })
                
        if 'cache' in pool_data:
            for key, entry in pool_data['cache'].items():
                cache_issues = self.detector.detect_cache_pollution(entry)
                for issue in cache_issues:
                    issue['key'] = key
                    all_issues.append({
                        'pollution_type': 'CACHE_POLLUTION',
                        'severity': issue['severity'],
                        'issue_type': issue['type'],
                        'message': issue['message'],
                        'details': json.dumps(issue)
                    })
                    
        if 'parameters' in pool_data:
            param_issues = self.detector.detect_parameter_pollution(pool_data['parameters'])
            for issue in param_issues:
                all_issues.append({
                    'pollution_type': 'PARAMETER_POLLUTION',
                    'severity': issue['severity'],
                    'issue_type': issue['type'],
                    'message': issue['message'],
                    'details': json.dumps(issue)
                })
                
        self._save_pollution_events(pool_name, all_issues)
        self._update_pool_health(pool_name, len(all_issues))
        
        self.pollution_stats['detected'] += len(all_issues)
        self.pollution_stats['pending'] += len(all_issues)
        
        return {
            'pool_name': pool_name,
            'total_issues': len(all_issues),
            'issues': all_issues,
            'scan_time': datetime.now().isoformat()
        }
        
    def _save_pollution_events(self, pool_name: str, issues: List[Dict]):
        """保存污染事件到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for issue in issues:
                cursor.execute('''
                    INSERT INTO pollution_events
                    (pool_name, pollution_type, severity, issue_type, message, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pool_name,
                    issue['pollution_type'],
                    issue['severity'],
                    issue['issue_type'],
                    issue['message'],
                    issue['details']
                ))
                
            conn.commit()
            
    def _update_pool_health(self, pool_name: str, issue_count: int):
        """更新池健康状态"""
        health_score = max(0, 1.0 - (issue_count * 0.05))
        status = 'healthy' if health_score >= 0.8 else 'warning' if health_score >= 0.5 else 'critical'
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO pool_health
                (pool_name, health_score, last_check, status)
                VALUES (?, ?, ?, ?)
            ''', (pool_name, health_score, datetime.now().isoformat(), status))
            
            conn.commit()
            
    def clean_pool(self, pool_name: str, pool_data: Dict) -> Dict:
        """清理AI池污染"""
        logger.info(f'开始清理AI池: {pool_name}')
        start_time = time.time()
        
        scan_result = self.scan_pool(pool_name, pool_data)
        total_issues = scan_result['total_issues']
        cleaned_count = 0
        failed_count = 0
        
        if 'data' in pool_data and pool_data['data']:
            data_issues = self.detector.detect_data_pollution(pool_data['data'])
            pool_data['data'] = self.cleaner.clean(pool_data['data'], data_issues)
            cleaned_count += len(data_issues)
            
        if 'cache' in pool_data and pool_data['cache']:
            for key, entry in list(pool_data['cache'].items()):
                cache_issues = self.detector.detect_cache_pollution(entry)
                if cache_issues:
                    pool_data['cache'] = self.cleaner.clean(pool_data['cache'], cache_issues)
                    cleaned_count += len(cache_issues)
                    
        if 'parameters' in pool_data and pool_data['parameters']:
            param_issues = self.detector.detect_parameter_pollution(pool_data['parameters'])
            pool_data['parameters'] = self.cleaner.clean(pool_data['parameters'], param_issues)
            cleaned_count += len(param_issues)
            
        self._mark_issues_cleaned(pool_name, cleaned_count)
        
        cleanup_time = time.time() - start_time
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cleanup_history
                (pool_name, total_issues, cleaned_issues, failed_issues, cleanup_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (pool_name, total_issues, cleaned_count, total_issues - cleaned_count, cleanup_time))
            conn.commit()
            
        self.pollution_stats['cleaned'] += cleaned_count
        self.pollution_stats['pending'] -= cleaned_count
        self.pollution_stats['last_cleanup'] = datetime.now().isoformat()
        
        return {
            'pool_name': pool_name,
            'total_issues': total_issues,
            'cleaned_issues': cleaned_count,
            'failed_issues': total_issues - cleaned_count,
            'cleanup_time': round(cleanup_time, 2),
            'cleaned_data': pool_data,
            'cleanup_time': datetime.now().isoformat()
        }
        
    def _mark_issues_cleaned(self, pool_name: str, count: int):
        """标记问题已清理"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pollution_events
                SET cleaned = TRUE, cleaned_at = ?, cleanup_method = 'automatic'
                WHERE pool_name = ? AND cleaned = FALSE
                LIMIT ?
            ''', (datetime.now().isoformat(), pool_name, count))
            conn.commit()
            
    def clean_all_pools(self, pools: Dict[str, Dict]) -> Dict:
        """清理所有AI池"""
        results = []
        total_cleaned = 0
        
        for pool_name, pool_data in pools.items():
            result = self.clean_pool(pool_name, pool_data)
            results.append(result)
            total_cleaned += result['cleaned_issues']
            
        return {
            'total_pools': len(pools),
            'total_cleaned': total_cleaned,
            'pool_results': results,
            'cleanup_time': datetime.now().isoformat()
        }
        
    def get_pollution_summary(self) -> Dict:
        """获取污染摘要"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pollution_type, severity, COUNT(*) as count
                FROM pollution_events
                WHERE cleaned = FALSE
                GROUP BY pollution_type, severity
            ''')
            
            summary = {}
            for row in cursor.fetchall():
                pollution_type, severity, count = row
                if pollution_type not in summary:
                    summary[pollution_type] = {}
                summary[pollution_type][severity] = count
                
            cursor.execute('''
                SELECT pool_name, health_score, status, last_check
                FROM pool_health
            ''')
            
            pools = []
            for row in cursor.fetchall():
                pools.append({
                    'pool_name': row[0],
                    'health_score': row[1],
                    'status': row[2],
                    'last_check': row[3]
                })
                
        return {
            'pollution_summary': summary,
            'pool_health': pools,
            'stats': self.pollution_stats
        }
        
    def get_pending_issues(self, pool_name: Optional[str] = None) -> List[Dict]:
        """获取待处理的污染问题"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if pool_name:
                cursor.execute('''
                    SELECT * FROM pollution_events
                    WHERE cleaned = FALSE AND pool_name = ?
                    ORDER BY detected_at DESC
                ''', (pool_name,))
            else:
                cursor.execute('''
                    SELECT * FROM pollution_events
                    WHERE cleaned = FALSE
                    ORDER BY detected_at DESC
                ''')
                
            issues = []
            for row in cursor.fetchall():
                issues.append({
                    'id': row[0],
                    'pool_name': row[1],
                    'pollution_type': row[2],
                    'severity': row[3],
                    'issue_type': row[4],
                    'message': row[5],
                    'details': json.loads(row[6]) if row[6] else None,
                    'detected_at': row[7]
                })
                
        return issues
        
    def run_optimization(self, pools: Dict[str, Dict]) -> Dict:
        """执行完整的优化流程"""
        logger.info("=== AI池污染优化开始 ===")
        
        logger.info("1. 扫描所有AI池...")
        for pool_name in pools:
            self.scan_pool(pool_name, pools[pool_name])
        
        logger.info("2. 清理污染...")
        result = self.clean_all_pools(pools)
        
        logger.info("3. 生成优化报告...")
        summary = self.get_pollution_summary()
        
        logger.info("=== AI池污染优化完成 ===")
        
        return {
            'cleanup_result': result,
            'summary': summary,
            'optimization_time': datetime.now().isoformat()
        }


if __name__ == "__main__":
    optimizer = AIPoolPollutionOptimizer()
    
    test_pools = {
        'teacher_ai_pool': {
            'data': {'name': 'teacher_ai', 'version': '3.0.0', 'active': True, 'last_used': None},
            'model_metrics': {'accuracy': 0.85, 'drift_score': 0.15, 'prediction_shift': 0.05},
            'cache': {
                'user_prefs': {'data': {}, 'expires_at': (datetime.now() - timedelta(days=1)).isoformat()},
                'lesson_cache': {'data': {}, 'expires_at': (datetime.now() + timedelta(days=1)).isoformat()}
            },
            'parameters': {
                'learning_rate': {'value': 0.01, 'type': 'float'},
                'difficulty_factor': {'value': 0.5, 'type': 'float'},
                'enabled': {'value': True, 'type': 'bool'}
            }
        },
        'student_ai_pool': {
            'data': {'name': 'student_ai', 'version': '3.0.0', 'active': True, 'level': ''},
            'model_metrics': {'accuracy': 0.65, 'drift_score': 0.35, 'prediction_shift': 0.25},
            'cache': {
                'progress': {'data': {}, 'expires_at': (datetime.now() - timedelta(hours=5)).isoformat()}
            },
            'parameters': {
                'assistance_level': {'value': 'high', 'type': 'int'},
                'knowledge_depth': {'value': 4, 'type': 'int'}
            }
        }
    }
    
    print("=== AI池污染优化测试 ===")
    print("\n1. 初始扫描...")
    for pool_name, pool_data in test_pools.items():
        result = optimizer.scan_pool(pool_name, pool_data)
        print(f"   {pool_name}: 检测到 {result['total_issues']} 个问题")
        
    print("\n2. 清理污染...")
    result = optimizer.clean_all_pools(test_pools)
    print(f"   清理完成: {result['total_cleaned']} 个问题已修复")
    
    print("\n3. 污染摘要:")
    summary = optimizer.get_pollution_summary()
    print(f"   检测总数: {summary['stats']['detected']}")
    print(f"   已清理: {summary['stats']['cleaned']}")
    print(f"   待处理: {summary['stats']['pending']}")
    
    print("\n4. 池健康状态:")
    for pool in summary['pool_health']:
        print(f"   {pool['pool_name']}: 健康分数 {pool['health_score']:.2f}, 状态: {pool['status']}")