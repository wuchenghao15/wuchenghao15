#!/usr/bin/env python3
"""
AI中间件学习系统
用于监控和分析中间件性能，实现AI驱动的中间件优化
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import sqlite3

from app.utils.logging import logger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AI Middleware Learning - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_middleware_learning.log'),
        logging.StreamHandler()
    ]
)

class AIMiddlewareLearningSystem:
    """AI中间件学习系统"""
    
    def __init__(self):
        self.performance_data = []
        self.lock = threading.Lock()
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../dev.db')
        self.ai_brain_integration = None
        
        # 初始化数据库表
        self._init_database()
        
        logger.info("AI中间件学习系统初始化完成")
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建中间件性能表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS middleware_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                middleware_name TEXT NOT NULL,
                request_path TEXT NOT NULL,
                method TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL NOT NULL,
                status_code INTEGER NOT NULL,
                client_ip TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                cpu_usage REAL,
                memory_usage REAL
            )
        ''')
        
        # 创建中间件优化建议表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS middleware_optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                middleware_name TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at DATETIME NOT NULL,
                applied BOOLEAN DEFAULT 0,
                effectiveness REAL DEFAULT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def monitor_middleware_performance(self, middleware_name: str, app):
        """监控中间件性能的装饰器"""
        @app.before_request
        def before_middleware():
            if hasattr(request, 'middleware_start_times'):
                request.middleware_start_times[middleware_name] = time.time()
            else:
                request.middleware_start_times = {middleware_name: time.time()}
        
        @app.after_request
        def after_middleware(response):
            if hasattr(request, 'middleware_start_times') and middleware_name in request.middleware_start_times:
                start_time = request.middleware_start_times[middleware_name]
                end_time = time.time()
                duration = end_time - start_time
                
                # 收集性能数据
                performance_data = {
                    'middleware_name': middleware_name,
                    'request_path': request.path,
                    'method': request.method,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'status_code': response.status_code,
                    'client_ip': request.remote_addr,
                    'timestamp': datetime.now().isoformat(),
                    'cpu_usage': None,  # 可以添加CPU使用率监控
                    'memory_usage': None  # 可以添加内存使用率监控
                }
                
                # 保存性能数据
                self.save_performance_data(performance_data)
                
                # 分析性能数据
                self.analyze_performance_data(middleware_name)
            
            return response
    
    def save_performance_data(self, data: Dict):
        """保存性能数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO middleware_performance (
                middleware_name, request_path, method, start_time, end_time, 
                duration, status_code, client_ip, timestamp, cpu_usage, memory_usage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['middleware_name'],
            data['request_path'],
            data['method'],
            data['start_time'],
            data['end_time'],
            data['duration'],
            data['status_code'],
            data['client_ip'],
            data['timestamp'],
            data['cpu_usage'],
            data['memory_usage']
        ))
        
        conn.commit()
        conn.close()
    
    def analyze_performance_data(self, middleware_name: str):
        """分析中间件性能数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最近1000条数据
        cursor.execute('''
            SELECT duration, status_code
            FROM middleware_performance
            WHERE middleware_name = ?
            ORDER BY timestamp DESC
            LIMIT 1000
        ''', (middleware_name,))
        
        data = cursor.fetchall()
        conn.close()
        
        if len(data) < 10:
            return  # 数据不足，跳过分析
        
        # 计算性能指标
        durations = [row[0] for row in data]
        status_codes = [row[1] for row in data]
        
        avg_duration = np.mean(durations)
        median_duration = np.median(durations)
        max_duration = np.max(durations)
        min_duration = np.min(durations)
        p95_duration = np.percentile(durations, 95)
        
        error_rate = len([code for code in status_codes if code >= 400]) / len(status_codes)
        
        logger.info(f"中间件 {middleware_name} 性能分析:")
        logger.info(f"  平均响应时间: {avg_duration:.4f}s")
        logger.info(f"  中位数响应时间: {median_duration:.4f}s")
        logger.info(f"  95%分位数响应时间: {p95_duration:.4f}s")
        logger.info(f"  最大响应时间: {max_duration:.4f}s")
        logger.info(f"  错误率: {error_rate:.4f}")
        
        # 生成优化建议
        self.generate_optimization_suggestions(middleware_name, {
            'avg_duration': avg_duration,
            'median_duration': median_duration,
            'p95_duration': p95_duration,
            'max_duration': max_duration,
            'error_rate': error_rate
        })
    
    def generate_optimization_suggestions(self, middleware_name: str, metrics: Dict):
        """生成优化建议"""
        suggestions = []
        
        # 根据性能指标生成建议
        if metrics['p95_duration'] > 0.1:  # 95%响应时间超过100ms
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 95%响应时间较长 ({metrics['p95_duration']:.4f}s)，建议优化算法或增加缓存",
                'confidence': 0.8
            })
        
        if metrics['error_rate'] > 0.05:  # 错误率超过5%
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 错误率较高 ({metrics['error_rate']:.4f})，建议检查错误处理逻辑",
                'confidence': 0.9
            })
        
        if metrics['avg_duration'] > 0.05:  # 平均响应时间超过50ms
            suggestions.append({
                'suggestion': f"中间件 {middleware_name} 平均响应时间较长 ({metrics['avg_duration']:.4f}s)，建议优化代码或增加异步处理",
                'confidence': 0.7
            })
        
        # 保存建议到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for suggestion in suggestions:
            cursor.execute('''
                INSERT INTO middleware_optimization_suggestions (
                    middleware_name, suggestion, confidence, created_at
                ) VALUES (?, ?, ?, ?)
            ''', (
                middleware_name,
                suggestion['suggestion'],
                suggestion['confidence'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        # 如果有建议，记录日志
        if suggestions:
            logger.info(f"为中间件 {middleware_name} 生成了 {len(suggestions)} 条优化建议")
    
    def get_optimization_suggestions(self, middleware_name: Optional[str] = None) -> List[Dict]:
        """获取优化建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if middleware_name:
            cursor.execute('''
                SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
                FROM middleware_optimization_suggestions
                WHERE middleware_name = ?
                ORDER BY confidence DESC
            ''', (middleware_name,))
        else:
            cursor.execute('''
                SELECT id, middleware_name, suggestion, confidence, created_at, applied, effectiveness
                FROM middleware_optimization_suggestions
                ORDER BY confidence DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        suggestions = []
        for row in rows:
            suggestions.append({
                'id': row[0],
                'middleware_name': row[1],
                'suggestion': row[2],
                'confidence': row[3],
                'created_at': row[4],
                'applied': bool(row[5]),
                'effectiveness': row[6]
            })
        
        return suggestions
    
    def apply_optimization_suggestion(self, suggestion_id: int, effectiveness: Optional[float] = None):
        """应用优化建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE middleware_optimization_suggestions
            SET applied = 1, effectiveness = ?
            WHERE id = ?
        ''', (effectiveness, suggestion_id))
        
        conn.commit()
        conn.close()
    
    def get_performance_report(self, middleware_name: Optional[str] = None, days: int = 7) -> Dict:
        """获取性能报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        time_filter = f"timestamp >= datetime('now', '-{days} days')"
        
        if middleware_name:
            query = f'''
                SELECT AVG(duration), MEDIAN(duration), MAX(duration), MIN(duration), 
                       PERCENTILE(duration, 0.95), 
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
                FROM middleware_performance
                WHERE middleware_name = ? AND {time_filter}
            '''
            cursor.execute(query, (middleware_name,))
        else:
            query = f'''
                SELECT AVG(duration), MEDIAN(duration), MAX(duration), MIN(duration), 
                       PERCENTILE(duration, 0.95), 
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
                FROM middleware_performance
                WHERE {time_filter}
            '''
            cursor.execute(query)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'avg_duration': result[0],
                'median_duration': result[1],
                'max_duration': result[2],
                'min_duration': result[3],
                'p95_duration': result[4],
                'error_rate': result[5],
                'days': days
            }
        else:
            return {
                'avg_duration': 0,
                'median_duration': 0,
                'max_duration': 0,
                'min_duration': 0,
                'p95_duration': 0,
                'error_rate': 0,
                'days': days
            }

# 创建全局实例
ai_middleware_learning_system = AIMiddlewareLearningSystem()


def ai_middleware_learning_middleware(app):
    """AI中间件学习中间件"""
    # 注册性能监控
    learning_system = ai_middleware_learning_system
    
    @app.before_request
    def before_request_middleware():
        request.middleware_start_times = {}
        request.start_time = time.time()
    
    @app.after_request
    def after_request_middleware(response):
        # 记录总请求时间
        if hasattr(request, 'start_time'):
            total_duration = time.time() - request.start_time
            
            # 记录请求信息
            logging.info(f"请求完成: {request.method} {request.path} {response.status_code} {total_duration:.4f}s")
        
        return response
    
    logger.info("AI中间件学习中间件注册完成")
    
    return app

# 优先级配置
ai_middleware_learning_priority = 10
