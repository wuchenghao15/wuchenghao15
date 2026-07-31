#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AIDataVisualization:
    """AI数据可视化引擎 - 生成各类可视化数据"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def generate_learning_chart_data(self, user_id, days=30):
        """生成学习趋势图表数据"""
        data = {
            'labels': [],
            'datasets': [{
                'label': '学习次数',
                'data': [],
                'borderColor': '#4f46e5',
                'backgroundColor': 'rgba(79, 70, 229, 0.1)',
                'fill': True
            }, {
                'label': '平均置信度',
                'data': [],
                'borderColor': '#10b981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'fill': True,
                'yAxisID': 'y1'
            }]
        }
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            self.cursor.execute('''
                SELECT COUNT(*) as count, AVG(confidence_score) as avg_score
                FROM learning_records 
                WHERE learned_at LIKE ?
            ''', (f'{date}%',))
            row = self.cursor.fetchone()
            
            data['labels'].append(date[5:])
            data['datasets'][0]['data'].append(row['count'] or 0)
            data['datasets'][1]['data'].append(round(row['avg_score'] or 0, 2))
        
        data['labels'] = data['labels'][::-1]
        data['datasets'][0]['data'] = data['datasets'][0]['data'][::-1]
        data['datasets'][1]['data'] = data['datasets'][1]['data'][::-1]
        
        return data
    
    def generate_resource_pie_data(self):
        """生成资源来源分布饼图数据"""
        self.cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM collected_resources 
            GROUP BY source
        ''')
        
        data = {
            'labels': [],
            'datasets': [{
                'data': [],
                'backgroundColor': [
                    '#4f46e5', '#10b981', '#f59e0b', '#ef4444', 
                    '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'
                ]
            }]
        }
        
        for row in self.cursor.fetchall():
            data['labels'].append(row['source'])
            data['datasets'][0]['data'].append(row['count'])
        
        return data
    
    def generate_skill_radar_data(self, user_id):
        """生成技能雷达图数据"""
        skills = ['Python', '机器学习', '深度学习', '算法', '数据科学', '神经网络', 'NLP']
        scores = []
        
        for skill in skills:
            self.cursor.execute('''
                SELECT AVG(confidence_score) as avg_score
                FROM learning_records 
                WHERE learning_content LIKE ?
            ''', (f'%{skill}%',))
            row = self.cursor.fetchone()
            scores.append(round(row['avg_score'] or 0.3, 2))
        
        data = {
            'labels': skills,
            'datasets': [{
                'label': '技能掌握程度',
                'data': scores,
                'borderColor': '#4f46e5',
                'backgroundColor': 'rgba(79, 70, 229, 0.2)',
                'pointBackgroundColor': '#4f46e5'
            }]
        }
        
        return data
    
    def generate_user_activity_bar_data(self):
        """生成用户活跃度柱状图数据"""
        self.cursor.execute('''
            SELECT u.username, COUNT(*) as count 
            FROM learning_records lr
            JOIN users u ON lr.id = u.id
            GROUP BY lr.id
            ORDER BY count DESC LIMIT 10
        ''')
        
        data = {
            'labels': [],
            'datasets': [{
                'label': '学习次数',
                'data': [],
                'backgroundColor': '#4f46e5',
                'borderRadius': 8
            }]
        }
        
        for row in self.cursor.fetchall():
            data['labels'].append(row['username'][:10])
            data['datasets'][0]['data'].append(row['count'])
        
        return data
    
    def generate_knowledge_category_data(self):
        """生成知识分类数据"""
        self.cursor.execute('''
            SELECT knowledge_category, COUNT(*) as count 
            FROM ai_knowledge 
            GROUP BY knowledge_category
        ''')
        
        data = {
            'labels': [],
            'values': []
        }
        
        for row in self.cursor.fetchall():
            data['labels'].append(row['knowledge_category'])
            data['values'].append(row['count'])
        
        return data
    
    def generate_dashboard_summary(self):
        """生成仪表板摘要数据"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        user_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM learning_records')
        learning_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM collected_resources')
        resource_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM ai_knowledge')
        knowledge_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM exam_papers')
        exam_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(confidence_score) FROM learning_records')
        avg_score = round(self.cursor.fetchone()[0] or 0, 2)
        
        return {
            'users': user_count,
            'learning_records': learning_count,
            'resources': resource_count,
            'knowledge': knowledge_count,
            'exams': exam_count,
            'avg_confidence': avg_score,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_weekly_heatmap_data(self):
        """生成学习热力图数据"""
        data = []
        
        for day_offset in range(30):
            date = datetime.now() - timedelta(days=day_offset)
            self.cursor.execute('''
                SELECT COUNT(*) as count 
                FROM learning_records 
                WHERE learned_at LIKE ?
            ''', (f'{date.strftime("%Y-%m-%d")}%',))
            count = self.cursor.fetchone()[0]
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'day': date.strftime('%A'),
                'count': count,
                'level': min(count // 2 + 1, 4)
            })
        
        return data
    
    def generate_system_metrics(self):
        """生成系统指标数据"""
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        admin_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "super_admin"')
        super_admin_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "teacher"')
        teacher_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE role = "student"')
        student_count = self.cursor.fetchone()[0]
        
        return {
            'admin_users': admin_count,
            'super_admin_users': super_admin_count,
            'teacher_users': teacher_count,
            'student_users': student_count,
            'total_users': admin_count + super_admin_count + teacher_count + student_count,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    viz = AIDataVisualization()
    
    logger.info("=== AI数据可视化引擎 ===")
    
    logger.info("\n=== 仪表板摘要 ===")
    summary = viz.generate_dashboard_summary()
    logger.info(f"用户数: {summary['users']}")
    logger.info(f"学习记录: {summary['learning_records']}")
    logger.info(f"资源数: {summary['resources']}")
    logger.info(f"知识条目: {summary['knowledge']}")
    logger.info(f"试卷数: {summary['exams']}")
    logger.info(f"平均置信度: {summary['avg_confidence']}")
    
    logger.info("\n=== 资源来源分布 ===")
    pie_data = viz.generate_resource_pie_data()
    for label, value in zip(pie_data['labels'], pie_data['datasets'][0]['data']):
        logger.info(f"  {label}: {value}")
    
    logger.info("\n=== 技能雷达数据 ===")
    radar_data = viz.generate_skill_radar_data(1)
    for skill, score in zip(radar_data['labels'], radar_data['datasets'][0]['data']):
        logger.info(f"  {skill}: {score}")
    
    logger.info("\n=== 用户活跃度 ===")
    bar_data = viz.generate_user_activity_bar_data()
    for user, count in zip(bar_data['labels'], bar_data['datasets'][0]['data']):
        logger.info(f"  {user}: {count}次")
    
    logger.info("\n=== 系统指标 ===")
    metrics = viz.generate_system_metrics()
    logger.info(f"管理员: {metrics['admin_users']}")
    logger.info(f"超级管理员: {metrics['super_admin_users']}")
    logger.info(f"教师: {metrics['teacher_users']}")
    logger.info(f"学生: {metrics['student_users']}")
    
    viz.close()