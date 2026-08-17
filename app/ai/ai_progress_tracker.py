#!/usr/bin/env python3
"""
AI学习进度追踪系统
追踪学生学习进度，生成学习报告和统计分析
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

class AIProgressTracker:
    """AI学习进度追踪引擎"""
    
    SUBJECTS = ['数学', '英语', '物理', '化学', '语文', '生物', '历史', '地理']
    
    PROGRESS_STATUS = {
        'not_started': {'name': '未开始', 'color': '#999999'},
        'in_progress': {'name': '进行中', 'color': '#4CAF50'},
        'completed': {'name': '已完成', 'color': '#2196F3'},
        'mastered': {'name': '已掌握', 'color': '#FF9800'}
    }
    
    METRICS = {
        'study_time': {'name': '学习时长', 'unit': '分钟'},
        'completion_rate': {'name': '完成率', 'unit': '%'},
        'accuracy': {'name': '正确率', 'unit': '%'},
        'improvement': {'name': '进步幅度', 'unit': '%'},
        'activity': {'name': '活跃度', 'unit': '次'}
    }
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                progress_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                total_units INTEGER DEFAULT 0,
                completed_units INTEGER DEFAULT 0,
                started_at TEXT,
                last_studied_at TEXT,
                status TEXT DEFAULT 'not_started',
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT,
                activity_type TEXT NOT NULL,
                duration INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 100,
                completed INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                subject TEXT,
                target_study_time INTEGER DEFAULT 0,
                target_completion INTEGER DEFAULT 0,
                actual_study_time INTEGER DEFAULT 0,
                actual_completion INTEGER DEFAULT 0,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                report_type TEXT NOT NULL,
                period TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def track_study_activity(self, user_id: str, subject: str, topic: str = '', 
                             activity_type: str = 'study', duration: int = 0,
                             score: int = 0, total_score: int = 100,
                             completed: int = 0, total: int = 0) -> Dict:
        """记录学习活动"""
        record_id = hashlib.md5(f"{user_id}{subject}{activity_type}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_records 
            (record_id, user_id, subject, topic, activity_type, duration, 
             score, total_score, completed, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, user_id, subject, topic, activity_type, duration,
              score, total_score, completed, total, datetime.now().isoformat()))
        
        self._update_progress(user_id, subject, topic, completed, total)
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'record_id': record_id,
            'user_id': user_id,
            'subject': subject,
            'activity_type': activity_type,
            'created_at': datetime.now().isoformat()
        }
    
    def _update_progress(self, user_id: str, subject: str, topic: str, completed: int, total: int):
        """更新学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM learning_progress 
            WHERE user_id = ? AND subject = ? AND topic = ?
        ''', (user_id, subject, topic))
        
        row = cursor.fetchone()
        
        if row:
            new_completed = row[6] + completed
            new_total = row[5] + total if total > 0 else row[5]
            
            if new_total > 0:
                completion_rate = (new_completed / new_total) * 100
                if completion_rate >= 95:
                    status = 'mastered'
                elif completion_rate >= 80:
                    status = 'completed'
                elif completion_rate > 0:
                    status = 'in_progress'
                else:
                    status = 'not_started'
            else:
                status = row[9]
            
            cursor.execute('''
                UPDATE learning_progress 
                SET completed_units = ?, total_units = ?, last_studied_at = ?, status = ?
                WHERE id = ?
            ''', (new_completed, new_total, datetime.now().isoformat(), status, row[0]))
        else:
            progress_id = hashlib.md5(f"{user_id}{subject}{topic}".encode()).hexdigest()[:16]
            cursor.execute('''
                INSERT INTO learning_progress 
                (progress_id, user_id, subject, topic, total_units, completed_units, 
                 started_at, last_studied_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (progress_id, user_id, subject, topic, total, completed,
                  datetime.now().isoformat(), datetime.now().isoformat(),
                  'in_progress' if completed > 0 else 'not_started'))
        
        conn.commit()
        conn.close()
    
    def get_progress(self, user_id: str, subject: str = '', topic: str = '') -> Dict:
        """获取学习进度"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if subject and topic:
            cursor.execute('''
                SELECT * FROM learning_progress 
                WHERE user_id = ? AND subject = ? AND topic = ?
            ''', (user_id, subject, topic))
            row = cursor.fetchone()
            
            if row:
                return self._format_progress_row(row)
            return {'success': False, 'error': '进度记录不存在'}
        
        elif subject:
            cursor.execute('''
                SELECT * FROM learning_progress 
                WHERE user_id = ? AND subject = ?
            ''', (user_id, subject))
            rows = cursor.fetchall()
            
            if rows:
                return {'success': True, 'data': [self._format_progress_row(r) for r in rows]}
            return {'success': False, 'error': '进度记录不存在'}
        
        else:
            cursor.execute('SELECT * FROM learning_progress WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            
            if rows:
                return {'success': True, 'data': [self._format_progress_row(r) for r in rows]}
            return {'success': False, 'error': '进度记录不存在'}
        
        conn.close()
    
    def _format_progress_row(self, row) -> Dict:
        """格式化进度行"""
        completion_rate = 0
        if row[5] > 0:
            completion_rate = round((row[6] / row[5]) * 100, 2)
        
        return {
            'progress_id': row[1],
            'user_id': row[2],
            'subject': row[3],
            'topic': row[4],
            'total_units': row[5],
            'completed_units': row[6],
            'completion_rate': completion_rate,
            'started_at': row[7],
            'last_studied_at': row[8],
            'status': row[9],
            'status_info': self.PROGRESS_STATUS.get(row[9], {'name': '未知', 'color': '#999'})
        }
    
    def get_study_stats(self, user_id: str, period: str = 'week') -> Dict:
        """获取学习统计"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        if period == 'week':
            start_time = (now - timedelta(days=7)).isoformat()
        elif period == 'month':
            start_time = (now - timedelta(days=30)).isoformat()
        elif period == 'year':
            start_time = (now - timedelta(days=365)).isoformat()
        else:
            start_time = '2000-01-01T00:00:00'
        
        cursor.execute('''
            SELECT subject, activity_type, SUM(duration) as total_duration, 
                   AVG(score) as avg_score, COUNT(*) as count
            FROM study_records 
            WHERE user_id = ? AND created_at >= ?
            GROUP BY subject, activity_type
        ''', (user_id, start_time))
        
        rows = cursor.fetchall()
        
        stats = defaultdict(lambda: {'study_time': 0, 'exercises': 0, 'exams': 0, 'avg_score': 0, 'activities': 0})
        
        for row in rows:
            subject = row[0]
            activity_type = row[1]
            duration = row[2] or 0
            avg_score = row[3] or 0
            count = row[4] or 0
            
            if activity_type == 'study':
                stats[subject]['study_time'] += duration
            elif activity_type == 'exercise':
                stats[subject]['exercises'] += count
                stats[subject]['avg_score'] = avg_score
            elif activity_type == 'exam':
                stats[subject]['exams'] += count
                stats[subject]['avg_score'] = avg_score
            
            stats[subject]['activities'] += count
        
        subject_stats = []
        for subject, data in stats.items():
            subject_stats.append({
                'subject': subject,
                'study_time': data['study_time'],
                'exercises': data['exercises'],
                'exams': data['exams'],
                'avg_score': round(data['avg_score'], 2) if data['avg_score'] > 0 else 0,
                'activities': data['activities']
            })
        
        cursor.execute('''
            SELECT SUM(duration) as total_duration, COUNT(*) as total_activities
            FROM study_records 
            WHERE user_id = ? AND created_at >= ?
        ''', (user_id, start_time))
        
        total_row = cursor.fetchone()
        
        conn.close()
        
        return {
            'success': True,
            'period': period,
            'total_study_time': total_row[0] or 0,
            'total_activities': total_row[1] or 0,
            'subject_stats': subject_stats,
            'generated_at': now.isoformat()
        }
    
    def set_weekly_goal(self, user_id: str, subject: str = '', 
                        target_study_time: int = 0, target_completion: int = 0) -> Dict:
        """设置周目标"""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        week_end = (now + timedelta(days=6 - now.weekday())).strftime('%Y-%m-%d')
        
        goal_id = hashlib.md5(f"{user_id}{subject}{week_start}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO weekly_goals 
            (goal_id, user_id, subject, target_study_time, target_completion,
             actual_study_time, actual_completion, week_start, week_end, status)
            VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 'active')
        ''', (goal_id, user_id, subject, target_study_time, target_completion, week_start, week_end))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'goal_id': goal_id,
            'user_id': user_id,
            'subject': subject,
            'target_study_time': target_study_time,
            'target_completion': target_completion,
            'week_start': week_start,
            'week_end': week_end
        }
    
    def get_weekly_goals(self, user_id: str) -> Dict:
        """获取周目标"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM weekly_goals 
            WHERE user_id = ? AND week_start = ?
        ''', (user_id, week_start))
        
        rows = cursor.fetchall()
        
        goals = []
        for row in rows:
            time_progress = 0
            completion_progress = 0
            
            if row[4] > 0:
                time_progress = round((row[6] / row[4]) * 100, 2)
            if row[5] > 0:
                completion_progress = round((row[7] / row[5]) * 100, 2)
            
            goals.append({
                'goal_id': row[1],
                'user_id': row[2],
                'subject': row[3],
                'target_study_time': row[4],
                'target_completion': row[5],
                'actual_study_time': row[6],
                'actual_completion': row[7],
                'time_progress': time_progress,
                'completion_progress': completion_progress,
                'week_start': row[8],
                'week_end': row[9],
                'status': row[10]
            })
        
        conn.close()
        
        return {'success': True, 'data': goals}
    
    def generate_weekly_report(self, user_id: str) -> Dict:
        """生成周学习报告"""
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        week_end = (now + timedelta(days=6 - now.weekday())).strftime('%Y-%m-%d')
        
        stats = self.get_study_stats(user_id, 'week')
        goals = self.get_weekly_goals(user_id)
        
        report_content = self._generate_report_content(stats, goals, week_start, week_end)
        
        report_id = hashlib.md5(f"{user_id}{week_start}weekly".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO learning_reports 
            (report_id, user_id, report_type, period, content)
            VALUES (?, ?, 'weekly', ?, ?)
        ''', (report_id, user_id, week_start, json.dumps(report_content, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'report_id': report_id,
            'user_id': user_id,
            'report_type': 'weekly',
            'period': week_start,
            'content': report_content,
            'generated_at': now.isoformat()
        }
    
    def _generate_report_content(self, stats: Dict, goals: Dict, week_start: str, week_end: str) -> Dict:
        """生成报告内容"""
        total_time = stats.get('total_study_time', 0)
        total_activities = stats.get('total_activities', 0)
        subject_stats = stats.get('subject_stats', [])
        
        goal_list = goals.get('data', [])
        
        top_subject = None
        max_time = 0
        for s in subject_stats:
            if s['study_time'] > max_time:
                max_time = s['study_time']
                top_subject = s
        
        avg_score = 0
        scored_subjects = [s for s in subject_stats if s['avg_score'] > 0]
        if scored_subjects:
            avg_score = round(sum(s['avg_score'] for s in scored_subjects) / len(scored_subjects), 2)
        
        goal_progress = []
        for g in goal_list:
            overall_progress = round((g['time_progress'] + g['completion_progress']) / 2, 2)
            goal_progress.append({
                'subject': g['subject'],
                'target_study_time': g['target_study_time'],
                'actual_study_time': g['actual_study_time'],
                'time_progress': g['time_progress'],
                'completion_progress': g['completion_progress'],
                'overall_progress': overall_progress,
                'achieved': overall_progress >= 80
            })
        
        suggestions = self._generate_suggestions(subject_stats, goal_progress)
        
        return {
            'week_range': f'{week_start} - {week_end}',
            'summary': {
                'total_study_time': total_time,
                'total_activities': total_activities,
                'avg_score': avg_score,
                'top_subject': top_subject['subject'] if top_subject else '无'
            },
            'subject_stats': subject_stats,
            'goal_progress': goal_progress,
            'suggestions': suggestions,
            'insights': self._generate_insights(subject_stats, goal_progress)
        }
    
    def _generate_suggestions(self, subject_stats: List, goal_progress: List) -> List:
        """生成改进建议"""
        suggestions = []
        
        weak_subjects = [s for s in subject_stats if s.get('avg_score', 0) < 70]
        if weak_subjects:
            for s in weak_subjects:
                suggestions.append(f"{s['subject']}的成绩较低，建议增加练习时间，重点复习薄弱知识点。")
        
        for g in goal_progress:
            if g['overall_progress'] < 50:
                suggestions.append(f"{g['subject']}的周目标完成度较低，建议合理安排学习时间。")
        
        if not suggestions:
            suggestions = ['本周学习表现良好，继续保持！']
        
        return suggestions[:5]
    
    def _generate_insights(self, subject_stats: List, goal_progress: List) -> List:
        """生成学习洞察"""
        insights = []
        
        total_time = sum(s['study_time'] for s in subject_stats)
        if total_time > 3000:
            insights.append('本周学习时间充足，保持良好的学习习惯。')
        elif total_time < 600:
            insights.append('本周学习时间较少，建议适当增加学习时长。')
        
        completed_goals = [g for g in goal_progress if g['achieved']]
        if completed_goals:
            insights.append(f'成功完成{len(completed_goals)}个周目标，继续努力！')
        
        improving_subjects = [s for s in subject_stats if s.get('avg_score', 0) > 80]
        if improving_subjects:
            insights.append(f'{", ".join([s["subject"] for s in improving_subjects])}表现优秀，继续保持！')
        
        return insights[:3]
    
    def get_reports(self, user_id: str, report_type: str = '', limit: int = 10) -> Dict:
        """获取学习报告"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if report_type:
            cursor.execute('''
                SELECT * FROM learning_reports 
                WHERE user_id = ? AND report_type = ? 
                ORDER BY generated_at DESC LIMIT ?
            ''', (user_id, report_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM learning_reports 
                WHERE user_id = ? 
                ORDER BY generated_at DESC LIMIT ?
            ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        reports = []
        for row in rows:
            try:
                content = json.loads(row[4])
            except Exception as e:
                content = {}
            
            reports.append({
                'report_id': row[1],
                'user_id': row[2],
                'report_type': row[3],
                'period': row[4] if isinstance(row[4], str) else row[4].decode('utf-8')[:20],
                'content': content,
                'generated_at': row[5]
            })
        
        return {'success': True, 'data': reports}
    
    def get_progress_trend(self, user_id: str, subject: str = '', days: int = 7) -> Dict:
        """获取学习进度趋势"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        trend_data = []
        
        for i in range(days):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            
            if subject:
                cursor.execute('''
                    SELECT SUM(duration) as total_duration, COUNT(*) as count
                    FROM study_records 
                    WHERE user_id = ? AND subject = ? AND DATE(created_at) = ?
                ''', (user_id, subject, date))
            else:
                cursor.execute('''
                    SELECT SUM(duration) as total_duration, COUNT(*) as count
                    FROM study_records 
                    WHERE user_id = ? AND DATE(created_at) = ?
                ''', (user_id, date))
            
            row = cursor.fetchone()
            trend_data.append({
                'date': date,
                'study_time': row[0] or 0,
                'activities': row[1] or 0
            })
        
        conn.close()
        
        trend_data.reverse()
        
        return {'success': True, 'data': trend_data}

ai_progress_tracker = AIProgressTracker()