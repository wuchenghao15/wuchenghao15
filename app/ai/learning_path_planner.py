#!/usr/bin/env python3
import sqlite3
import json
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AILearningPathPlanner:
    """AI学习路径规划器 - 根据用户能力和目标制定个性化学习路径"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def get_user_skills(self, user_id):
        """获取用户技能水平"""
        skills = defaultdict(float)
        
        self.cursor.execute('''
            SELECT * FROM learning_records 
            WHERE learning_type LIKE ?
        ''', ('%学习%',))
        
        for record in self.cursor.fetchall():
            record_dict = dict(record)
            content = record_dict.get('learning_content', '')
            score = record_dict.get('confidence_score', 0.5)
            
            keywords = ['Python', '机器学习', '深度学习', '算法', '数据', '神经网络', 'NLP', '计算机视觉']
            for kw in keywords:
                if kw in content:
                    skills[kw] = max(skills[kw], score)
        
        return dict(skills)
    
    def get_knowledge_points(self):
        """获取知识图谱节点"""
        self.cursor.execute('SELECT * FROM ai_knowledge')
        return [dict(row) for row in self.cursor.fetchall()]
    
    def analyze_skill_gaps(self, user_id, target_skills=None):
        """分析技能差距"""
        current_skills = self.get_user_skills(user_id)
        
        if target_skills is None:
            target_skills = {
                'Python': 0.9,
                '机器学习': 0.85,
                '深度学习': 0.8,
                '算法': 0.85,
                '数据科学': 0.8,
            }
        
        gaps = {}
        for skill, target in target_skills.items():
            current = current_skills.get(skill, 0.3)
            gap = target - current
            if gap > 0.1:
                gaps[skill] = {
                    'current': current,
                    'target': target,
                    'gap': gap,
                    'priority': gap * (1 - current)
                }
        
        return dict(sorted(gaps.items(), key=lambda x: x[1]['priority'], reverse=True))
    
    def generate_learning_path(self, user_id, goals=None, duration_days=30):
        """生成个性化学习路径"""
        gaps = self.analyze_skill_gaps(user_id)
        if not gaps:
            return self._generate_maintenance_path(user_id, duration_days)
        
        path = {
            'user_id': user_id,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d'),
            'duration_days': duration_days,
            'goals': goals or list(gaps.keys()),
            'skill_gaps': gaps,
            'phases': []
        }
        
        total_gap = sum(g['gap'] for g in gaps.values())
        phase_duration = duration_days // 3
        
        phases = [
            {'name': '基础巩固', 'duration': phase_duration, 'focus': '薄弱基础'},
            {'name': '技能提升', 'duration': phase_duration, 'focus': '核心技能'},
            {'name': '实战应用', 'duration': duration_days - phase_duration * 2, 'focus': '项目实战'},
        ]
        
        current_date = datetime.now()
        skills_list = list(gaps.keys())
        
        for phase in phases:
            phase_start = current_date
            phase_end = current_date + timedelta(days=phase['duration'])
            
            daily_tasks = []
            for day in range(phase['duration']):
                day_date = phase_start + timedelta(days=day)
                day_tasks = self._generate_daily_tasks(
                    user_id, skills_list, gaps, phase['name'], day, phase['duration']
                )
                daily_tasks.append({
                    'date': day_date.strftime('%Y-%m-%d'),
                    'tasks': day_tasks
                })
            
            path['phases'].append({
                'name': phase['name'],
                'focus': phase['focus'],
                'start_date': phase_start.strftime('%Y-%m-%d'),
                'end_date': phase_end.strftime('%Y-%m-%d'),
                'duration_days': phase['duration'],
                'daily_tasks': daily_tasks
            })
            
            current_date = phase_end
        
        return path
    
    def _generate_daily_tasks(self, user_id, skills, gaps, phase_name, day, total_days):
        """生成每日学习任务"""
        tasks = []
        progress = day / total_days
        
        if phase_name == '基础巩固':
            for skill in skills[:2]:
                gap = gaps.get(skill, {})
                tasks.append({
                    'skill': skill,
                    'type': 'video',
                    'duration_minutes': 45,
                    'description': f"{skill}基础知识回顾",
                    'resources': self._find_resources(skill, ['入门', '基础'])
                })
        
        elif phase_name == '技能提升':
            for i, skill in enumerate(skills):
                if i % 2 == day % 2:
                    gap = gaps.get(skill, {})
                    difficulty = '进阶' if progress > 0.5 else '入门'
                    tasks.append({
                        'skill': skill,
                        'type': 'practice',
                        'duration_minutes': 60,
                        'description': f"{skill}{difficulty}练习",
                        'resources': self._find_resources(skill, [difficulty])
                    })
        
        elif phase_name == '实战应用':
            tasks.append({
                'skill': '综合实战',
                'type': 'project',
                'duration_minutes': 90,
                'description': "综合项目实战",
                'resources': self._find_resources('项目', ['实战'])
            })
        
        return tasks
    
    def _find_resources(self, skill, keywords):
        """查找相关资源"""
        results = []
        for kw in keywords:
            self.cursor.execute('''
                SELECT title, url, source, quality_score 
                FROM collected_resources 
                WHERE (title LIKE ? OR title LIKE ? OR description LIKE ?)
                ORDER BY quality_score DESC LIMIT 3
            ''', (f'%{skill}%', f'%{kw}%', f'%{skill}%'))
            
            for row in self.cursor.fetchall():
                results.append({
                    'title': row['title'],
                    'url': row['url'],
                    'source': row['source'],
                    'quality_score': row['quality_score']
                })
        
        return results[:5]
    
    def _generate_maintenance_path(self, user_id, duration_days):
        """生成维护性学习路径（技能差距较小）"""
        return {
            'user_id': user_id,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'end_date': (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d'),
            'duration_days': duration_days,
            'goals': ['技能保持', '知识扩展'],
            'skill_gaps': {},
            'phases': [{
                'name': '知识扩展',
                'focus': '拓展知识面',
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'end_date': (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d'),
                'duration_days': duration_days,
                'daily_tasks': [{
                    'date': (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d'),
                    'tasks': [{
                        'skill': '知识扩展',
                        'type': 'reading',
                        'duration_minutes': 30,
                        'description': '浏览技术文章',
                        'resources': self._find_resources('AI', ['最新', '前沿'])
                    }]
                } for d in range(duration_days)]
            }]
        }
    
    def save_learning_path(self, path):
        """保存学习路径"""
        self.cursor.execute('''
            INSERT INTO adult_study_plans 
            (user_id, plan_name, subject, target_level, start_date, end_date, 
             weekly_hours, status, progress, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            path['user_id'],
            f"AI学习路径计划-{path['start_date']}",
            ','.join(path['goals']),
            'advanced',
            path['start_date'],
            path['end_date'],
            10,
            'active',
            0
        ))
        
        path_json = json.dumps(path)
        import uuid
        knowledge_id = str(uuid.uuid4())[:8]
        self.cursor.execute('''
            INSERT INTO ai_knowledge 
            (knowledge_id, knowledge_category, knowledge_title, knowledge_content, 
             knowledge_source, relevance_score, confidence_level, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (knowledge_id, 'learning_path', f"学习路径计划-{path['start_date']}", path_json, 'AI生成', 0.9, 'high', ','.join(path['goals'])))
        
        self.conn.commit()
    
    def get_user_learning_path(self, user_id):
        """获取用户学习路径"""
        self.cursor.execute('''
            SELECT * FROM adult_study_plans WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        return self.cursor.fetchone()
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    planner = AILearningPathPlanner()
    
    logger.info("=== 分析技能差距 ===")
    gaps = planner.analyze_skill_gaps(1)
    for skill, gap_info in gaps.items():
        logger.info(f"{skill}: 当前={gap_info['current']:.2f}, 目标={gap_info['target']:.2f}, 差距={gap_info['gap']:.2f}")
    
    logger.info("\n=== 生成学习路径 ===")
    path = planner.generate_learning_path(1, duration_days=14)
    logger.info(f"计划周期: {path['start_date']} ~ {path['end_date']} ({path['duration_days']}天)")
    logger.info(f"学习目标: {path['goals']}")
    
    for phase in path['phases']:
        logger.info(f"\n  阶段: {phase['name']} ({phase['duration_days']}天)")
        logger.info(f"  重点: {phase['focus']}")
        
        sample_day = phase['daily_tasks'][0]
        logger.info(f"  第1天任务:")
        for task in sample_day['tasks']:
            logger.info(f"    - {task['type']}: {task['description']} ({task['duration_minutes']}分钟)")
            if task['resources']:
                for res in task['resources'][:2]:
                    logger.info(f"      资源: [{res['source']}] {res['title'][:30]}")
    
    planner.save_learning_path(path)
    logger.info("\n学习路径已保存！")
    
    planner.close()