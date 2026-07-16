#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
from datetime import datetime
from collections import defaultdict

class AISelfLearningSystem:
    def __init__(self):
        self.learning_data = {}
        self.patterns = {}
        self.insights = []
        self.performance_metrics = defaultdict(list)
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_name TEXT NOT NULL,
                    pattern_data TEXT,
                    confidence REAL DEFAULT 0.0,
                    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_verified TEXT,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    context TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT NOT NULL,
                    insight_content TEXT NOT NULL,
                    priority TEXT DEFAULT 'medium',
                    source_metrics TEXT,
                    recommended_action TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_type TEXT NOT NULL,
                    learning_data TEXT,
                    outcome TEXT,
                    success_rate REAL,
                    learned_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("[AI Self-Learning] 数据库表创建完成")
        except Exception as e:
            print(f"[AI Self-Learning] 创建表失败: {e}")
    
    def record_metric(self, metric_name, metric_value, metric_unit='', context=''):
        with self._lock:
            self.performance_metrics[metric_name].append({
                'value': metric_value,
                'timestamp': datetime.now().isoformat(),
                'unit': metric_unit,
                'context': context
            })
            
            try:
                conn = sqlite3.connect('self_learning.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO performance_metrics 
                    (metric_name, metric_value, metric_unit, recorded_at, context)
                    VALUES (?, ?, ?, ?, ?)
                ''', (metric_name, metric_value, metric_unit, datetime.now().isoformat(), context))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI Self-Learning] 记录指标失败: {e}")
    
    def analyze_patterns(self):
        with self._lock:
            patterns = []
            
            for metric_name, data in self.performance_metrics.items():
                if len(data) >= 10:
                    values = [d['value'] for d in data[-20:]]
                    avg_value = sum(values) / len(values)
                    variance = sum((v - avg_value) ** 2 for v in values) / len(values)
                    
                    pattern = {
                        'metric': metric_name,
                        'pattern_type': 'trend' if variance < avg_value * 0.1 else 'volatile',
                        'average': avg_value,
                        'variance': variance,
                        'sample_size': len(values),
                        'confidence': min(1.0, len(values) / 50)
                    }
                    patterns.append(pattern)
                    
                    self.patterns[metric_name] = pattern
            
            self._save_patterns(patterns)
            return patterns
    
    def _save_patterns(self, patterns):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            
            for pattern in patterns:
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_patterns
                    (pattern_type, pattern_name, pattern_data, confidence, last_verified, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pattern['pattern_type'],
                    pattern['metric'],
                    json.dumps(pattern),
                    pattern['confidence'],
                    datetime.now().isoformat(),
                    pattern.get('usage_count', 0) + 1
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI Self-Learning] 保存模式失败: {e}")
    
    def generate_insights(self):
        insights = []
        
        patterns = self.analyze_patterns()
        
        for pattern in patterns:
            if pattern['pattern_type'] == 'volatile':
                insights.append({
                    'type': 'performance_alert',
                    'content': f"指标 '{pattern['metric']}' 波动较大，建议关注",
                    'priority': 'high',
                    'source': json.dumps(pattern),
                    'action': f"检查 {pattern['metric']} 的数据源和计算逻辑"
                })
            
            if pattern['average'] < 0.5:
                insights.append({
                    'type': 'performance_warning',
                    'content': f"指标 '{pattern['metric']}' 平均值低于阈值",
                    'priority': 'medium',
                    'source': json.dumps(pattern),
                    'action': f"优化 {pattern['metric']} 相关功能"
                })
        
        self.insights.extend(insights)
        self._save_insights(insights)
        return insights
    
    def _save_insights(self, insights):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            
            for insight in insights:
                cursor.execute('''
                    INSERT INTO insights
                    (insight_type, insight_content, priority, source_metrics, recommended_action)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    insight['type'],
                    insight['content'],
                    insight['priority'],
                    insight.get('source', ''),
                    insight.get('action', '')
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI Self-Learning] 保存洞察失败: {e}")
    
    def learn_from_history(self, history_data):
        with self._lock:
            learning_results = []
            
            for record in history_data:
                outcome = record.get('outcome', 'unknown')
                success = outcome == 'success'
                
                learning_results.append({
                    'type': record.get('type', 'generic'),
                    'outcome': outcome,
                    'success': success,
                    'data': record.get('data', {}),
                    'timestamp': datetime.now().isoformat()
                })
            
            try:
                conn = sqlite3.connect('self_learning.db')
                cursor = conn.cursor()
                
                for result in learning_results:
                    success_rate = 1.0 if result['success'] else 0.0
                    cursor.execute('''
                        INSERT INTO learning_history
                        (learning_type, learning_data, outcome, success_rate)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        result['type'],
                        json.dumps(result['data']),
                        result['outcome'],
                        success_rate
                    ))
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI Self-Learning] 学习历史数据失败: {e}")
            
            return learning_results
    
    def get_insights_summary(self):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM insights WHERE resolved = 0 ORDER BY priority DESC, created_at DESC')
            rows = cursor.fetchall()
            
            summary = []
            for row in rows:
                summary.append({
                    'id': row[0],
                    'type': row[1],
                    'content': row[2],
                    'priority': row[3],
                    'action': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            return summary
        except Exception as e:
            print(f"[AI Self-Learning] 获取洞察摘要失败: {e}")
            return []
    
    def get_performance_summary(self):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT metric_name, AVG(metric_value), COUNT(*) 
                FROM performance_metrics 
                GROUP BY metric_name 
                ORDER BY COUNT(*) DESC
            ''')
            rows = cursor.fetchall()
            
            summary = []
            for row in rows:
                summary.append({
                    'metric': row[0],
                    'average': row[1],
                    'count': row[2]
                })
            
            conn.close()
            return summary
        except Exception as e:
            print(f"[AI Self-Learning] 获取性能摘要失败: {e}")
            return []
    
    def resolve_insight(self, insight_id):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE insights SET resolved = 1 WHERE id = ?', (insight_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AI Self-Learning] 解决洞察失败: {e}")
            return False
    
    def get_patterns(self):
        try:
            conn = sqlite3.connect('self_learning.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM learning_patterns ORDER BY confidence DESC')
            rows = cursor.fetchall()
            
            patterns = []
            for row in rows:
                patterns.append({
                    'id': row[0],
                    'type': row[1],
                    'name': row[2],
                    'data': json.loads(row[3]) if row[3] else {},
                    'confidence': row[4],
                    'discovered_at': row[5],
                    'usage_count': row[7]
                })
            
            conn.close()
            return patterns
        except Exception as e:
            print(f"[AI Self-Learning] 获取模式失败: {e}")
            return []

self_learning_system = AISelfLearningSystem()