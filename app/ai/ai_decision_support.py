#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
import math
from datetime import datetime, timedelta
from collections import defaultdict

class AIDecisionSupportSystem:
    DECISION_TYPES = ['learning_path', 'resource_allocation', 'risk_mitigation', 'optimization', 'strategic']
    DECISION_PRIORITIES = ['critical', 'high', 'medium', 'low']
    
    def __init__(self):
        self.decisions = {}
        self.predictions = {}
        self.risk_assessments = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    decision_type TEXT NOT NULL,
                    decision_title TEXT NOT NULL,
                    decision_content TEXT,
                    priority TEXT DEFAULT 'medium',
                    data_sources TEXT,
                    analysis_result TEXT,
                    recommendation TEXT,
                    confidence REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'pending',
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    executed_at TEXT,
                    execution_result TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT NOT NULL UNIQUE,
                    prediction_type TEXT NOT NULL,
                    prediction_target TEXT,
                    prediction_content TEXT,
                    predicted_value TEXT,
                    confidence REAL DEFAULT 0.0,
                    prediction_date TEXT,
                    actual_value TEXT,
                    accuracy REAL,
                    status TEXT DEFAULT 'predicted',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    risk_id TEXT NOT NULL UNIQUE,
                    risk_category TEXT NOT NULL,
                    risk_title TEXT NOT NULL,
                    risk_description TEXT,
                    risk_level TEXT DEFAULT 'medium',
                    probability REAL DEFAULT 0.0,
                    impact REAL DEFAULT 0.0,
                    risk_score REAL DEFAULT 0.0,
                    mitigation_strategy TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    context TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trend_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trend_type TEXT NOT NULL,
                    trend_name TEXT NOT NULL,
                    data_point TEXT NOT NULL,
                    data_value REAL NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[AI Decision Support] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Decision Support] 创建表失败: {e}")
    
    def generate_decision(self, decision_type, title, data_sources, created_by):
        decision_id = f"DEC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        analysis_result = self._analyze_data(data_sources)
        recommendation = self._generate_recommendation(decision_type, analysis_result)
        confidence = self._calculate_confidence(analysis_result)
        
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO decision_records
                (decision_id, decision_type, decision_title, decision_content, priority,
                 data_sources, analysis_result, recommendation, confidence, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_id,
                decision_type,
                title,
                json.dumps({'type': decision_type, 'title': title}),
                self._determine_priority(decision_type, confidence),
                json.dumps(data_sources),
                json.dumps(analysis_result),
                recommendation,
                confidence,
                'pending',
                created_by
            ))
            conn.commit()
            conn.close()
            
            self.decisions[decision_id] = {
                'type': decision_type,
                'title': title,
                'analysis': analysis_result,
                'recommendation': recommendation,
                'confidence': confidence,
                'status': 'pending',
                'created_by': created_by,
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'decision_id': decision_id,
                'type': decision_type,
                'title': title,
                'analysis': analysis_result,
                'recommendation': recommendation,
                'confidence': confidence,
                'priority': self._determine_priority(decision_type, confidence)
            }
        except Exception as e:
            logger.info(f"[AI Decision Support] 生成决策失败: {e}")
            return {'error': str(e)}
    
    def _analyze_data(self, data_sources):
        analysis = {
            'data_points': len(data_sources),
            'trends': [],
            'anomalies': [],
            'patterns': []
        }
        
        for source in data_sources:
            if isinstance(source, dict):
                metric = source.get('metric', '')
                values = source.get('values', [])
                
                if values:
                    avg_value = sum(values) / len(values)
                    variance = sum((v - avg_value) ** 2 for v in values) / len(values) if len(values) > 1 else 0
                    
                    analysis['trends'].append({
                        'metric': metric,
                        'average': avg_value,
                        'variance': variance,
                        'trend': 'increasing' if len(values) >= 2 and values[-1] > values[-2] else 'decreasing' if len(
                        values) >= 2 and values[-1] < values[-2] else 'stable'
                    })
                    
                    if variance > avg_value * 0.3:
                        analysis['anomalies'].append({
                            'metric': metric,
                            'reason': '高波动',
                            'value': avg_value
                        })
        
        return analysis
    
    def _generate_recommendation(self, decision_type, analysis):
        recommendations = {
            'learning_path': self._generate_learning_path_recommendation(analysis),
            'resource_allocation': self._generate_resource_allocation_recommendation(analysis),
            'risk_mitigation': self._generate_risk_mitigation_recommendation(analysis),
            'optimization': self._generate_optimization_recommendation(analysis),
            'strategic': self._generate_strategic_recommendation(analysis)
        }
        return recommendations.get(decision_type, '需要进一步分析数据')
    
    def _generate_learning_path_recommendation(self, analysis):
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            weak_areas = [a['metric'] for a in anomalies]
            return f"发现学习薄弱环节: {', '.join(weak_areas)}。建议加强这些知识点的专项训练，调整学习路径以弥补短板。"
        return "学习进度正常，建议保持当前学习节奏，可尝试拓展进阶内容。"
    
    def _generate_resource_allocation_recommendation(self, analysis):
        trends = analysis.get('trends', [])
        if trends:
            high_variance = [t['metric'] for t in trends if t['variance'] > 0.1]
            if high_variance:
                return f"资源分配建议：{', '.join(high_variance)} 波动较大，建议增加资源投入以稳定表现。"
        return "资源分配均衡，建议维持当前配置并持续监控。"
    
    def _generate_risk_mitigation_recommendation(self, analysis):
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            return f"风险预警：检测到 {len(anomalies)} 个异常指标。建议立即采取措施：1) 排查异常原因；2) 制定应急预案；3) 加强监控频率。"
        return "当前风险水平正常，建议继续保持常规监控。"
    
    def _generate_optimization_recommendation(self, analysis):
        trends = analysis.get('trends', [])
        if trends:
            improving = [t['metric'] for t in trends if t['trend'] == 'increasing']
            declining = [t['metric'] for t in trends if t['trend'] == 'decreasing']
            
            recommendations = []
            if improving:
                recommendations.append(f"优化机会：{', '.join(improving)} 呈上升趋势，可加大投入扩大优势。")
            if declining:
                recommendations.append(f"优化重点：{', '.join(declining)} 呈下降趋势，需立即分析原因并采取改进措施。")
            
            return ' '.join(recommendations) if recommendations else "系统运行良好，建议持续优化以保持效率。"
        return "数据不足，建议积累更多数据后进行优化分析。"
    
    def _generate_strategic_recommendation(self, analysis):
        return f"战略分析完成：数据点 {analysis.get('data_points', 0)} 个，趋势 {len(analysis.get('trends',[]))} 个，异常 {len(analysis.get('anomalies', []))} 个。基于当前数据分析，建议制定中长期发展规划，关注高潜力领域的战略布局。"
    
    def _calculate_confidence(self, analysis):
        data_points = analysis.get('data_points', 0)
        trends = len(analysis.get('trends', []))
        anomalies = len(analysis.get('anomalies', []))
        
        confidence = min(1.0, 0.3 + (data_points * 0.05) + (trends * 0.02))
        if anomalies > data_points * 0.5:
            confidence *= 0.7
        
        return round(confidence, 2)
    
    def _determine_priority(self, decision_type, confidence):
        if decision_type == 'risk_mitigation' and confidence > 0.7:
            return 'critical'
        if confidence > 0.8:
            return 'high'
        if confidence > 0.5:
            return 'medium'
        return 'low'
    
    def execute_decision(self, decision_id, execution_params=None):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM decision_records WHERE decision_id = ?', (decision_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '决策不存在'}
            
            cursor.execute('''
                UPDATE decision_records 
                SET status = ?, executed_at = ?, execution_result = ? 
                WHERE decision_id = ?
            ''', ('executed', datetime.now().isoformat(), json.dumps(execution_params or {}), decision_id))
            conn.commit()
            conn.close()
            
            if decision_id in self.decisions:
                self.decisions[decision_id]['status'] = 'executed'
                self.decisions[decision_id]['executed_at'] = datetime.now().isoformat()
            
            return {'success': True, 'decision_id': decision_id, 'status': 'executed'}
        except Exception as e:
            logger.info(f"[AI Decision Support] 执行决策失败: {e}")
            return {'error': str(e)}
    
    def predict_trend(self, prediction_type, target, historical_data):
        prediction_id = f"PRED{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not historical_data:
            return {'error': '历史数据不足'}
        
        prediction = self._predict_value(historical_data)
        
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions
                (prediction_id, prediction_type, prediction_target, prediction_content,
                 predicted_value, confidence, prediction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction_id,
                prediction_type,
                target,
                json.dumps(historical_data),
                str(prediction['value']),
                prediction['confidence'],
                (datetime.now() + timedelta(days=7)).isoformat()
            ))
            conn.commit()
            conn.close()
            
            self.predictions[prediction_id] = {
                'type': prediction_type,
                'target': target,
                'predicted_value': prediction['value'],
                'confidence': prediction['confidence'],
                'status': 'predicted'
            }
            
            return {
                'prediction_id': prediction_id,
                'type': prediction_type,
                'target': target,
                'predicted_value': prediction['value'],
                'confidence': prediction['confidence'],
                'prediction_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            }
        except Exception as e:
            logger.info(f"[AI Decision Support] 预测趋势失败: {e}")
            return {'error': str(e)}
    
    def _predict_value(self, historical_data):
        values = [d['value'] for d in historical_data if isinstance(d.get('value'), (int, float))]
        
        if len(values) < 3:
            return {'value': sum(values) / len(values) if values else 0, 'confidence': 0.5}
        
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        next_x = n
        predicted_value = slope * next_x + intercept
        
        variance = sum((values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n)) / n
        confidence = max(0.3, min(1.0, 1 - variance / (sum(values) / n) if sum(values) > 0 else 0.5))
        
        return {'value': round(predicted_value, 2), 'confidence': round(confidence, 2)}
    
    def assess_risk(self, category, title, description, probability=0.5, impact=0.5):
        risk_id = f"RISK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        risk_score = probability * impact
        
        risk_level = 'low'
        if risk_score >= 0.7:
            risk_level = 'critical'
        elif risk_score >= 0.5:
            risk_level = 'high'
        elif risk_score >= 0.3:
            risk_level = 'medium'
        
        mitigation = self._generate_mitigation_strategy(category, risk_level, probability, impact)
        
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_assessments
                (risk_id, risk_category, risk_title, risk_description, risk_level,
                 probability, impact, risk_score, mitigation_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                risk_id,
                category,
                title,
                description,
                risk_level,
                probability,
                impact,
                risk_score,
                mitigation
            ))
            conn.commit()
            conn.close()
            
            self.risk_assessments[risk_id] = {
                'category': category,
                'title': title,
                'level': risk_level,
                'score': risk_score,
                'probability': probability,
                'impact': impact,
                'mitigation': mitigation,
                'status': 'active'
            }
            
            return {
                'risk_id': risk_id,
                'category': category,
                'title': title,
                'level': risk_level,
                'score': round(risk_score, 2),
                'probability': probability,
                'impact': impact,
                'mitigation': mitigation
            }
        except Exception as e:
            logger.info(f"[AI Decision Support] 评估风险失败: {e}")
            return {'error': str(e)}
    
    def _generate_mitigation_strategy(self, category, risk_level, probability, impact):
        strategies = {
            'critical': f"紧急措施：{category} 领域存在高风险，建议立即启动应急预案，组建专项小组进行风险管控，24小时内完成风险排查。",
            'high': f"重要措施：{category} 领域存在较高风险，建议制定详细的风险缓解计划，分配专人负责监控，每周进行风险评估更新。",
            'medium': f"常规措施：{category} 领域存在中等风险，建议加强监控频率，建立预警机制，定期进行风险回顾。",
            'low': f"监控措施：{category} 领域风险较低，建议保持常规监控，纳入周期性风险评估体系。"
        }
        return strategies.get(risk_level, "建议保持常规监控")
    
    def get_decision_by_id(self, decision_id):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM decision_records WHERE decision_id = ?', (decision_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            conn.close()
            return {
                'decision_id': row[1],
                'type': row[2],
                'title': row[3],
                'content': row[4],
                'priority': row[5],
                'data_sources': json.loads(row[6]) if row[6] else [],
                'analysis': json.loads(row[7]) if row[7] else {},
                'recommendation': row[8],
                'confidence': row[9],
                'status': row[10],
                'created_by': row[11],
                'created_at': row[12],
                'executed_at': row[13],
                'execution_result': row[14]
            }
        except Exception as e:
            logger.info(f"[AI Decision Support] 获取决策失败: {e}")
            return None
    
    def get_all_decisions(self, status=None):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            
            if status:
                cursor.execute('SELECT * FROM decision_records WHERE status = ? ORDER BY created_at DESC', (status,))
            else:
                cursor.execute('SELECT * FROM decision_records ORDER BY created_at DESC')
            
            rows = cursor.fetchall()
            conn.close()
            
            decisions = []
            for row in rows:
                decisions.append({
                    'decision_id': row[1],
                    'type': row[2],
                    'title': row[3],
                    'priority': row[5],
                    'confidence': row[9],
                    'status': row[10],
                    'created_by': row[11],
                    'created_at': row[12]
                })
            
            return decisions
        except Exception as e:
            logger.info(f"[AI Decision Support] 获取所有决策失败: {e}")
            return []
    
    def get_all_predictions(self):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM predictions ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            predictions = []
            for row in rows:
                predictions.append({
                    'prediction_id': row[1],
                    'type': row[2],
                    'target': row[3],
                    'predicted_value': row[5],
                    'confidence': row[6],
                    'prediction_date': row[7],
                    'actual_value': row[8],
                    'accuracy': row[9],
                    'status': row[10],
                    'created_at': row[11]
                })
            
            return predictions
        except Exception as e:
            logger.info(f"[AI Decision Support] 获取所有预测失败: {e}")
            return []
    
    def get_all_risks(self, level=None):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            
            if level:
                cursor.execute('SELECT * FROM risk_assessments WHERE risk_level = ? ORDER BY risk_score DESC', (level,))
            else:
                cursor.execute('SELECT * FROM risk_assessments ORDER BY risk_score DESC')
            
            rows = cursor.fetchall()
            conn.close()
            
            risks = []
            for row in rows:
                risks.append({
                    'risk_id': row[1],
                    'category': row[2],
                    'title': row[3],
                    'description': row[4],
                    'level': row[5],
                    'probability': row[6],
                    'impact': row[7],
                    'score': row[8],
                    'mitigation': row[9],
                    'status': row[10],
                    'created_at': row[11]
                })
            
            return risks
        except Exception as e:
            logger.info(f"[AI Decision Support] 获取所有风险失败: {e}")
            return []
    
    def update_prediction_accuracy(self, prediction_id, actual_value):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('SELECT predicted_value FROM predictions WHERE prediction_id = ?', (prediction_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '预测不存在'}
            
            predicted = float(row[0])
            actual = float(actual_value)
            accuracy = 1 - abs(predicted - actual) / max(abs(predicted), abs(actual), 1)
            
            cursor.execute('''
                UPDATE predictions 
                SET actual_value = ?, accuracy = ?, status = ? 
                WHERE prediction_id = ?
            ''', (str(actual_value), round(accuracy, 2), 'completed', prediction_id))
            conn.commit()
            conn.close()
            
            if prediction_id in self.predictions:
                self.predictions[prediction_id]['actual_value'] = actual_value
                self.predictions[prediction_id]['accuracy'] = accuracy
                self.predictions[prediction_id]['status'] = 'completed'
            
            return {'success': True, 'accuracy': round(accuracy, 2)}
        except Exception as e:
            logger.info(f"[AI Decision Support] 更新预测准确性失败: {e}")
            return {'error': str(e)}
    
    def close_risk(self, risk_id, review_notes=''):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE risk_assessments 
                SET status = ?, reviewed_at = ? 
                WHERE risk_id = ?
            ''', ('closed', datetime.now().isoformat(), risk_id))
            conn.commit()
            conn.close()
            
            if risk_id in self.risk_assessments:
                self.risk_assessments[risk_id]['status'] = 'closed'
            
            return {'success': True, 'risk_id': risk_id}
        except Exception as e:
            logger.info(f"[AI Decision Support] 关闭风险失败: {e}")
            return {'error': str(e)}
    
    def get_dashboard_summary(self):
        try:
            conn = sqlite3.connect('decision_support.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM decision_records')
            total_decisions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM decision_records WHERE status = "executed"')
            executed_decisions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM predictions')
            total_predictions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM risk_assessments WHERE status = "active"')
            active_risks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM risk_assessments WHERE risk_level = "critical" AND status = "active"')
            critical_risks = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence) FROM decision_records')
            avg_confidence = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT AVG(accuracy) FROM predictions WHERE status = "completed"')
            avg_accuracy = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_decisions': total_decisions,
                'executed_decisions': executed_decisions,
                'decision_execution_rate': (executed_decisions / total_decisions * 100) if total_decisions > 0 else 0,
                'total_predictions': total_predictions,
                'avg_prediction_accuracy': round(avg_accuracy * 100, 1),
                'active_risks': active_risks,
                'critical_risks': critical_risks,
                'avg_decision_confidence': round(avg_confidence * 100, 1)
            }
        except Exception as e:
            logger.info(f"[AI Decision Support] 获取仪表板摘要失败: {e}")
            return {}

decision_support_system = AIDecisionSupportSystem()