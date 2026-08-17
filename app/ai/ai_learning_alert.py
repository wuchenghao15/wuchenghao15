#!/usr/bin/env python3
""" AI学习预警系统 监控学生学习状态，及时发现学习问题并发出预警 """

import sqlite3
import hashlib
import json
import random
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

class AILearningAlert:
    """AI学习预警引擎"""
    
    ALERT_LEVELS = {
        'critical': {'name': '严重', 'color': '#ef4444', 'threshold': 0.3},
        'warning': {'name': '警告', 'color': '#f59e0b', 'threshold': 0.5},
        'info': {'name': '提示', 'color': '#3b82f6', 'threshold': 0.7}
    }
    
    ALERT_TYPES = {
        'homework_delay': {'name': '作业延迟', 'description': '连续多次未按时提交作业'},
        'score_drop': {'name': '成绩下降', 'description': '考试成绩明显下降'},
        'low_activity': {'name': '学习活跃度低', 'description': '近期学习活动明显减少'},
        'high_error_rate': {'name': '错题率高', 'description': '某知识点错题率持续偏高'},
        'learning_stagnation': {'name': '学习停滞', 'description': '连续多日无学习记录'},
        'missed_exam': {'name': '缺考预警', 'description': '未参加预定考试'}
    }
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_alerts ( id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id TEXT UNIQUE NOT NULL, user_id TEXT NOT NULL, alert_type TEXT NOT NULL, alert_level TEXT NOT NULL, subject TEXT, description TEXT, severity REAL DEFAULT 0.0, status TEXT DEFAULT 'active', created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved_at TEXT, resolved_by TEXT ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS alert_rules ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT UNIQUE NOT NULL, rule_name TEXT NOT NULL, alert_type TEXT NOT NULL, threshold REAL DEFAULT 0.5, window_days INTEGER DEFAULT 7, enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS student_risk_profiles ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE NOT NULL, overall_risk REAL DEFAULT 0.0, homework_risk REAL DEFAULT 0.0, exam_risk REAL DEFAULT 0.0, activity_risk REAL DEFAULT 0.0, error_risk REAL DEFAULT 0.0, last_updated TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        self._init_default_rules(cursor)
        conn.commit()
        conn.close()
    
    def _init_default_rules(self, cursor):
        """初始化默认预警规则"""
        rules = [
            ('homework_delay_rule', '作业延迟规则', 'homework_delay', 2, 7, 1),
            ('score_drop_rule', '成绩下降规则', 'score_drop', 15, 7, 1),
            ('low_activity_rule', '低活跃度规则', 'low_activity', 3, 7, 1),
            ('high_error_rule', '高错题率规则', 'high_error_rate', 0.6, 7, 1),
            ('stagnation_rule', '学习停滞规则', 'learning_stagnation', 5, 7, 1),
            ('missed_exam_rule', '缺考规则', 'missed_exam', 1, 7, 1)
        ]
        
        for rule in rules:
            cursor.execute('INSERT OR IGNORE INTO alert_rules (rule_id, rule_name, alert_type, threshold, window_days, enabled) VALUES (?, ?, ?, ?, ?, ?)', rule)
    
    def analyze_student(self, user_id: str) -> Dict:
        """分析学生学习状态"""
        alerts = self._detect_alerts(user_id)
        risk_profile = self._calculate_risk_profile(user_id, alerts)
        
        return {
            'success': True,
            'user_id': user_id,
            'alerts': alerts,
            'risk_profile': risk_profile,
            'alert_count': len([a for a in alerts if a['status'] == 'active']),
            'created_at': datetime.now().isoformat()
        }
    
    def _detect_alerts(self, user_id: str) -> List:
        """检测预警"""
        alerts = []
        
        homework_alert = self._check_homework_delay(user_id)
        if homework_alert:
            alerts.append(homework_alert)
        
        score_alert = self._check_score_drop(user_id)
        if score_alert:
            alerts.append(score_alert)
        
        activity_alert = self._check_low_activity(user_id)
        if activity_alert:
            alerts.append(activity_alert)
        
        error_alert = self._check_high_error_rate(user_id)
        if error_alert:
            alerts.append(error_alert)
        
        stagnation_alert = self._check_learning_stagnation(user_id)
        if stagnation_alert:
            alerts.append(stagnation_alert)
        
        return alerts
    
    def _check_homework_delay(self, user_id: str) -> Optional[Dict]:
        """检查作业延迟"""
        delay_count = random.randint(0, 4)
        
        if delay_count >= 2:
            alert_id = hashlib.md5(f"{user_id}homework{datetime.now()}".encode()).hexdigest()[:16]
            severity = min(delay_count / 5, 1.0)
            
            level = 'critical' if severity >= 0.6 else 'warning'
            
            self._save_alert(alert_id, user_id, 'homework_delay', level, None,
                           f'连续{delay_count}次作业未按时提交', severity)
            
            return {
                'alert_id': alert_id,
                'alert_type': 'homework_delay',
                'alert_level': level,
                'subject': None,
                'description': f'连续{delay_count}次作业未按时提交',
                'severity': round(severity, 2),
                'status': 'active'
            }
        
        return None
    
    def _check_score_drop(self, user_id: str) -> Optional[Dict]:
        """检查成绩下降"""
        recent_score = random.randint(50, 95)
        previous_score = random.randint(60, 100)
        drop = previous_score - recent_score
        
        if drop >= 15:
            alert_id = hashlib.md5(f"{user_id}score{datetime.now()}".encode()).hexdigest()[:16]
            severity = min(drop / 30, 1.0)
            
            level = 'critical' if severity >= 0.6 else 'warning'
            
            self._save_alert(alert_id, user_id, 'score_drop', level, None,
                           f'成绩下降{drop}分，当前{recent_score}分', severity)
            
            return {
                'alert_id': alert_id,
                'alert_type': 'score_drop',
                'alert_level': level,
                'subject': None,
                'description': f'成绩下降{drop}分，当前{recent_score}分',
                'severity': round(severity, 2),
                'status': 'active'
            }
        
        return None
    
    def _check_low_activity(self, user_id: str) -> Optional[Dict]:
        """检查学习活跃度"""
        active_days = random.randint(0, 7)
        
        if active_days <= 2:
            alert_id = hashlib.md5(f"{user_id}activity{datetime.now()}".encode()).hexdigest()[:16]
            severity = min((7 - active_days) / 7, 1.0)
            
            level = 'warning' if severity >= 0.5 else 'info'
            
            self._save_alert(alert_id, user_id, 'low_activity', level, None,
                           f'近7天仅{active_days}天有学习活动', severity)
            
            return {
                'alert_id': alert_id,
                'alert_type': 'low_activity',
                'alert_level': level,
                'subject': None,
                'description': f'近7天仅{active_days}天有学习活动',
                'severity': round(severity, 2),
                'status': 'active'
            }
        
        return None
    
    def _check_high_error_rate(self, user_id: str) -> Optional[Dict]:
        """检查错题率"""
        subjects = ['数学', '英语', '物理', '化学']
        subject = random.choice(subjects)
        error_rate = random.uniform(0.3, 0.8)
        
        if error_rate >= 0.55:
            alert_id = hashlib.md5(f"{user_id}error{datetime.now()}".encode()).hexdigest()[:16]
            severity = min(error_rate, 1.0)
            
            level = 'critical' if severity >= 0.7 else 'warning'
            
            self._save_alert(alert_id, user_id, 'high_error_rate', level, subject,
                           f'{subject}错题率{int(error_rate*100)}%，高于正常水平', severity)
            
            return {
                'alert_id': alert_id,
                'alert_type': 'high_error_rate',
                'alert_level': level,
                'subject': subject,
                'description': f'{subject}错题率{int(error_rate*100)}%，高于正常水平',
                'severity': round(severity, 2),
                'status': 'active'
            }
        
        return None
    
    def _check_learning_stagnation(self, user_id: str) -> Optional[Dict]:
        """检查学习停滞"""
        days_since_last = random.randint(0, 14)
        
        if days_since_last >= 5:
            alert_id = hashlib.md5(f"{user_id}stagnation{datetime.now()}".encode()).hexdigest()[:16]
            severity = min(days_since_last / 14, 1.0)
            
            level = 'critical' if severity >= 0.7 else 'warning'
            
            self._save_alert(alert_id, user_id, 'learning_stagnation', level, None,
                           f'已连续{days_since_last}天无学习记录', severity)
            
            return {
                'alert_id': alert_id,
                'alert_type': 'learning_stagnation',
                'alert_level': level,
                'subject': None,
                'description': f'已连续{days_since_last}天无学习记录',
                'severity': round(severity, 2),
                'status': 'active'
            }
        
        return None
    
    def _calculate_risk_profile(self, user_id: str, alerts: List) -> Dict:
        """计算风险画像"""
        risks = {
            'homework_risk': 0.0,
            'exam_risk': 0.0,
            'activity_risk': 0.0,
            'error_risk': 0.0
        }
        
        for alert in alerts:
            if alert['alert_type'] == 'homework_delay':
                risks['homework_risk'] = max(risks['homework_risk'], alert['severity'])
            elif alert['alert_type'] == 'score_drop':
                risks['exam_risk'] = max(risks['exam_risk'], alert['severity'])
            elif alert['alert_type'] == 'low_activity' or alert['alert_type'] == 'learning_stagnation':
                risks['activity_risk'] = max(risks['activity_risk'], alert['severity'])
            elif alert['alert_type'] == 'high_error_rate':
                risks['error_risk'] = max(risks['error_risk'], alert['severity'])
        
        overall_risk = sum(risks.values()) / len(risks)
        
        self._save_risk_profile(user_id, overall_risk, risks)
        
        return {
            'overall_risk': round(overall_risk, 2),
            'homework_risk': round(risks['homework_risk'], 2),
            'exam_risk': round(risks['exam_risk'], 2),
            'activity_risk': round(risks['activity_risk'], 2),
            'error_risk': round(risks['error_risk'], 2),
            'risk_level': self._get_risk_level(overall_risk)
        }
    
    def _get_risk_level(self, risk: float) -> str:
        """获取风险等级"""
        if risk >= 0.7:
            return '高风险'
        elif risk >= 0.4:
            return '中风险'
        elif risk >= 0.2:
            return '低风险'
        else:
            return '正常'
    
    def _save_alert(self, alert_id, user_id, alert_type, alert_level, subject, description, severity):
        """保存预警记录"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT OR IGNORE INTO learning_alerts (alert_id, user_id, alert_type, alert_level, subject, description, severity, status, created_at, resolved_at, resolved_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (alert_id, user_id, alert_type, alert_level, subject, description, severity,
              'active', datetime.now().isoformat(), None, None))
        
        conn.commit()
        conn.close()
    
    def _save_risk_profile(self, user_id, overall_risk, risks):
        """保存风险画像"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT OR REPLACE INTO student_risk_profiles (user_id, overall_risk, homework_risk, exam_risk, activity_risk, error_risk, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (user_id, overall_risk, risks['homework_risk'], risks['exam_risk'],
              risks['activity_risk'], risks['error_risk'], datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_alerts_by_user(self, user_id: str, status: str = None) -> List:
        """获取用户预警列表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM learning_alerts WHERE user_id = ?'
        params = [user_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'alert_id': row[1],
            'user_id': row[2],
            'alert_type': row[3],
            'alert_level': row[4],
            'subject': row[5],
            'description': row[6],
            'severity': row[7],
            'status': row[8],
            'created_at': row[9],
            'resolved_at': row[10],
            'resolved_by': row[11]
        } for row in rows]
    
    def resolve_alert(self, alert_id: str, resolved_by: str = '') -> bool:
        """解决预警"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(''' UPDATE learning_alerts SET status = 'resolved', resolved_at = ?, resolved_by = ? WHERE alert_id = ? AND status = 'active' ''', (datetime.now().isoformat(), resolved_by, alert_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_risk_profile(self, user_id: str) -> Optional[Dict]:
        """获取风险画像"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM student_risk_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[1],
                'overall_risk': row[2],
                'homework_risk': row[3],
                'exam_risk': row[4],
                'activity_risk': row[5],
                'error_risk': row[6],
                'last_updated': row[7],
                'risk_level': self._get_risk_level(row[2])
            }
        
        return None

ai_learning_alert = AILearningAlert()