#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AILearningTracker:
    """AI学习效果追踪系统 - 全方位追踪用户学习行为和效果"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def track_learning_session(self, user_id, session_data):
        """追踪学习会话"""
        self.cursor.execute('''
            INSERT INTO learning_records 
            (learning_type, learning_source, learning_content, learning_result, 
             confidence_score, learned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_data.get('type', 'study'),
            session_data.get('source', 'system'),
            session_data.get('content', ''),
            session_data.get('result', 'completed'),
            session_data.get('confidence', 0.5),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        self.conn.commit()
    
    def get_daily_stats(self, user_id, date=None):
        """获取每日学习统计"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        self.cursor.execute('''
            SELECT COUNT(*) as session_count, AVG(confidence_score) as avg_confidence
            FROM learning_records 
            WHERE learned_at LIKE ?
        ''', (f'{date}%',))
        
        row = self.cursor.fetchone()
        return {
            'date': date,
            'session_count': row['session_count'] or 0,
            'avg_confidence': round(row['avg_confidence'] or 0, 2)
        }
    
    def get_weekly_stats(self, user_id):
        """获取本周学习统计"""
        stats = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            stats.append(self.get_daily_stats(user_id, date))
        return stats
    
    def get_monthly_progress(self, user_id):
        """获取月度学习进度"""
        self.cursor.execute('''
            SELECT strftime('%Y-%m-%d', learned_at) as day, 
                   COUNT(*) as count, 
                   AVG(confidence_score) as avg_score
            FROM learning_records 
            WHERE strftime('%Y-%m', learned_at) = strftime('%Y-%m', 'now')
            GROUP BY day
            ORDER BY day
        ''')
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'day': row['day'],
                'count': row['count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })
        
        return results
    
    def get_learning_trend(self, user_id, days=30):
        """获取学习趋势"""
        trend = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            self.cursor.execute('''
                SELECT COUNT(*) as count, AVG(confidence_score) as avg_score
                FROM learning_records 
                WHERE learned_at LIKE ?
            ''', (f'{date}%',))
            row = self.cursor.fetchone()
            trend.append({
                'date': date,
                'session_count': row['count'] or 0,
                'avg_score': round(row['avg_score'] or 0, 2)
            })
        return trend[::-1]
    
    def get_learning_summary(self, user_id):
        """获取学习综合摘要"""
        total_sessions = self.cursor.execute('SELECT COUNT(*) FROM learning_records').fetchone()[0]
        
        self.cursor.execute('SELECT AVG(confidence_score) FROM learning_records')
        avg_score = round(self.cursor.execute('SELECT AVG(confidence_score) FROM learning_records').fetchone()[0] or 0,
        2)
        
        self.cursor.execute('''
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d', learned_at)) 
            FROM learning_records
        ''')
        active_days = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            SELECT learning_content, COUNT(*) as count 
            FROM learning_records 
            GROUP BY learning_content 
            ORDER BY count DESC LIMIT 5
        ''')
        top_topics = [dict(row) for row in self.cursor.fetchall()]
        
        return {
            'total_sessions': total_sessions,
            'avg_confidence_score': avg_score,
            'active_days': active_days,
            'top_topics': top_topics,
            'weekly_stats': self.get_weekly_stats(user_id),
            'monthly_progress': self.get_monthly_progress(user_id)
        }
    
    def get_user_ranking(self):
        """获取用户学习排行榜"""
        self.cursor.execute('''
            SELECT lr.learning_content, COUNT(*) as total_sessions, 
                   AVG(lr.confidence_score) as avg_score
            FROM learning_records lr
            JOIN users u ON lr.id = u.id
            GROUP BY lr.id
            ORDER BY total_sessions DESC, avg_score DESC
            LIMIT 10
        ''')
        
        ranking = []
        for i, row in enumerate(self.cursor.fetchall(), 1):
            ranking.append({
                'rank': i,
                'user': row['learning_content'][:20],
                'total_sessions': row['total_sessions'],
                'avg_score': round(row['avg_score'], 2)
            })
        
        return ranking
    
    def generate_progress_report(self, user_id):
        """生成学习进度报告"""
        summary = self.get_learning_summary(user_id)
        trend = self.get_learning_trend(user_id, 14)
        
        report = {
            'user_id': user_id,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': summary,
            'trend': trend,
            'insights': self._generate_insights(summary, trend),
            'recommendations': self._generate_recommendations(summary)
        }
        
        return report
    
    def _generate_insights(self, summary, trend):
        """生成学习洞察"""
        insights = []
        
        avg_score = summary['avg_confidence_score']
        if avg_score > 0.7:
            insights.append({
                'type': 'positive',
                'title': '学习效果良好',
                'content': f'平均置信度 {avg_score}，学习效果优秀'
            })
        elif avg_score < 0.5:
            insights.append({
                'type': 'warning',
                'title': '需要加强练习',
                'content': f'平均置信度 {avg_score}，建议增加练习次数'
            })
        
        recent_activity = trend[-7:] if len(trend) >= 7 else trend
        avg_sessions = sum(t['session_count'] for t in recent_activity) / len(recent_activity)
        if avg_sessions >= 2:
            insights.append({
                'type': 'positive',
                'title': '学习活跃度高',
                'content': f'最近7天平均每天{avg_sessions:.1f}次学习'
            })
        
        return insights
    
    def _generate_recommendations(self, summary):
        """生成学习建议"""
        recommendations = []
        
        if summary['active_days'] < 5:
            recommendations.append({
                'type': 'frequency',
                'title': '增加学习频率',
                'content': '建议每周至少学习5天',
                'action': '制定学习计划，每天固定时间学习'
            })
        
        if summary['top_topics']:
            top_topic = summary['top_topics'][0]['learning_content']
            recommendations.append({
                'type': 'focus',
                'title': '深入学习',
                'content': f'{top_topic}学习次数最多，可以深入学习相关知识',
                'action': '查找{top_topic}的进阶资源'
            })
        
        return recommendations
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    tracker = AILearningTracker()
    
    logger.info("=== AI学习效果追踪系统 ===")
    
    logger.info("\n=== 每日统计 ===")
    daily = tracker.get_daily_stats(1)
    logger.info(f"日期: {daily['date']}")
    logger.info(f"学习次数: {daily['session_count']}")
    logger.info(f"平均置信度: {daily['avg_confidence']}")
    
    logger.info("\n=== 本周统计 ===")
    weekly = tracker.get_weekly_stats(1)
    for day in weekly:
        logger.info(f"{day['date']}: {day['session_count']}次, 置信度: {day['avg_confidence']}")
    
    logger.info("\n=== 学习综合摘要 ===")
    summary = tracker.get_learning_summary(1)
    logger.info(f"总学习次数: {summary['total_sessions']}")
    logger.info(f"平均置信度: {summary['avg_confidence_score']}")
    logger.info(f"活跃天数: {summary['active_days']}")
    
    logger.info("\n=== 学习排行榜 ===")
    ranking = tracker.get_user_ranking()
    for item in ranking:
        logger.info(f"{item['rank']}. {item['user']}: {item['total_sessions']}次, {item['avg_score']}分")
    
    logger.info("\n=== 学习进度报告 ===")
    report = tracker.generate_progress_report(1)
    logger.info(f"洞察: {[i['title'] for i in report['insights']]}")
    logger.info(f"建议: {[r['title'] for r in report['recommendations']]}")
    
    tracker.close()