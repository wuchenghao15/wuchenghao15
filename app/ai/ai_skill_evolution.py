#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
from datetime import datetime
from collections import defaultdict

class AISkillEvolutionSystem:
    SKILL_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert', 'master']
    SKILL_LEVEL_NAMES = {
        'beginner': '初级',
        'intermediate': '中级',
        'advanced': '高级',
        'expert': '专家',
        'master': '大师'
    }
    
    def __init__(self):
        self.employee_skills = defaultdict(dict)
        self.skill_scores = defaultdict(lambda: defaultdict(float))
        self.thinking_focus = defaultdict(list)
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    employee_name TEXT,
                    skill_name TEXT NOT NULL,
                    skill_level TEXT DEFAULT 'beginner',
                    skill_score REAL DEFAULT 0.0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    improvement_rate REAL DEFAULT 0.0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    old_score REAL,
                    new_score REAL,
                    old_level TEXT,
                    new_level TEXT,
                    task_type TEXT,
                    task_result TEXT,
                    score_change REAL,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS thinking_focus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    focus_area TEXT NOT NULL,
                    focus_score REAL DEFAULT 0.0,
                    trend TEXT DEFAULT 'stable',
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    recommendation_type TEXT,
                    recommendation_content TEXT,
                    priority TEXT DEFAULT 'medium',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    implemented INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[AI Skill Evolution] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 创建表失败: {e}")
    
    def track_task_outcome(self, employee_id, employee_name, task_type, skill_name, success, score_change=0.0):
        with self._lock:
            current_score = self.skill_scores[employee_id].get(skill_name, 0.0)
            
            if success:
                current_score = min(100.0, current_score + abs(score_change))
            else:
                current_score = max(0.0, current_score - abs(score_change))
            
            self.skill_scores[employee_id][skill_name] = current_score
            
            old_level = self._get_level(current_score - abs(score_change) if success else current_score + abs(
            score_change))
            new_level = self._get_level(current_score)
            
            self.employee_skills[employee_id][skill_name] = {
                'level': new_level,
                'score': current_score,
                'last_updated': datetime.now().isoformat()
            }
            
            try:
                conn = sqlite3.connect('skill_evolution.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO employee_skills
                    (employee_id, employee_name, skill_name, skill_level, skill_score, last_updated, improvement_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id,
                    employee_name,
                    skill_name,
                    new_level,
                    current_score,
                    datetime.now().isoformat(),
                    self._calculate_improvement_rate(employee_id, skill_name, current_score)
                ))
                
                cursor.execute('''
                    INSERT INTO skill_history
                    (employee_id, skill_name, old_score, new_score, old_level, new_level, task_type, task_result,
                    score_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id,
                    skill_name,
                    current_score - abs(score_change) if success else current_score + abs(score_change),
                    current_score,
                    old_level,
                    new_level,
                    task_type,
                    'success' if success else 'failure',
                    score_change if success else -score_change
                ))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[AI Skill Evolution] 跟踪任务结果失败: {e}")
            
            return {
                'employee_id': employee_id,
                'skill_name': skill_name,
                'old_level': old_level,
                'new_level': new_level,
                'old_score': current_score - abs(score_change) if success else current_score + abs(score_change),
                'new_score': current_score,
                'level_changed': old_level != new_level
            }
    
    def _get_level(self, score):
        if score >= 90:
            return 'master'
        elif score >= 75:
            return 'expert'
        elif score >= 60:
            return 'advanced'
        elif score >= 40:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _calculate_improvement_rate(self, employee_id, skill_name, current_score):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT new_score, recorded_at 
                FROM skill_history 
                WHERE employee_id = ? AND skill_name = ? 
                ORDER BY recorded_at DESC LIMIT 10
            ''', (employee_id, skill_name))
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) >= 2:
                first_score = rows[-1][0]
                improvement = current_score - first_score
                return min(100.0, improvement / max(1, first_score) * 100) if first_score > 0 else 0.0
            return 0.0
        except Exception:
            return 0.0
    
    def evolve_thinking_focus(self, employee_id, focus_areas):
        with self._lock:
            for area, score in focus_areas.items():
                self.thinking_focus[employee_id].append({
                    'area': area,
                    'score': score,
                    'timestamp': datetime.now().isoformat()
                })
            
            try:
                conn = sqlite3.connect('skill_evolution.db')
                cursor = conn.cursor()
                
                for area, score in focus_areas.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO thinking_focus
                        (employee_id, focus_area, focus_score, trend, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        employee_id,
                        area,
                        score,
                        self._determine_trend(employee_id, area, score),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.info(f"[AI Skill Evolution] 进化思维焦点失败: {e}")
    
    def _determine_trend(self, employee_id, area, current_score):
        history = [f for f in self.thinking_focus[employee_id] if f['area'] == area]
        if len(history) >= 3:
            recent_scores = [h['score'] for h in history[-3:]]
            if recent_scores[-1] > recent_scores[-2]:
                return 'increasing'
            elif recent_scores[-1] < recent_scores[-2]:
                return 'decreasing'
        return 'stable'
    
    def get_employee_skills(self, employee_id):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employee_skills WHERE employee_id = ?', (employee_id,))
            rows = cursor.fetchall()
            
            skills = {}
            for row in rows:
                skills[row[2]] = {
                    'level': row[3],
                    'level_name': self.SKILL_LEVEL_NAMES.get(row[3], row[3]),
                    'score': row[4],
                    'last_updated': row[5],
                    'improvement_rate': row[6]
                }
            
            conn.close()
            return skills
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 获取员工技能失败: {e}")
            return {}
    
    def generate_skill_recommendations(self, employee_id):
        skills = self.get_employee_skills(employee_id)
        recommendations = []
        
        for skill_name, data in skills.items():
            if data['score'] < 60:
                recommendations.append({
                    'skill': skill_name,
                    'type': 'improvement',
                    'content': f"技能 '{skill_name}' 当前评分为 {data['score']:.1f}，建议加强训练",
                    'priority': 'high'
                })
            
            if data['improvement_rate'] < 5:
                recommendations.append({
                    'skill': skill_name,
                    'type': 'stagnation',
                    'content': f"技能 '{skill_name}' 进步缓慢，建议尝试新的学习方法",
                    'priority': 'medium'
                })
        
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            
            for rec in recommendations:
                cursor.execute('''
                    INSERT INTO skill_recommendations
                    (employee_id, skill_name, recommendation_type, recommendation_content, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (employee_id, rec['skill'], rec['type'], rec['content'], rec['priority']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 生成技能建议失败: {e}")
        
        return recommendations
    
    def get_skill_recommendations(self, employee_id):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            cursor.execute(
            'SELECT * FROM skill_recommendations WHERE employee_id = ? AND implemented = 0 ORDER BY priority DESC',
            (employee_id,))
            rows = cursor.fetchall()
            
            recommendations = []
            for row in rows:
                recommendations.append({
                    'id': row[0],
                    'skill': row[2],
                    'type': row[3],
                    'content': row[4],
                    'priority': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            return recommendations
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 获取技能建议失败: {e}")
            return []
    
    def get_all_employees_summary(self):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT employee_id, employee_name, skill_name, skill_level, skill_score
                FROM employee_skills
                ORDER BY employee_id, skill_score DESC
            ''')
            rows = cursor.fetchall()
            
            employees = defaultdict(lambda: {'name': '', 'skills': [], 'avg_score': 0.0})
            for row in rows:
                emp_id, emp_name, skill, level, score = row
                employees[emp_id]['name'] = emp_name
                employees[emp_id]['skills'].append({
                    'name': skill,
                    'level': level,
                    'level_name': self.SKILL_LEVEL_NAMES.get(level, level),
                    'score': score
                })
            
            for emp_id in employees:
                scores = [s['score'] for s in employees[emp_id]['skills']]
                employees[emp_id]['avg_score'] = sum(scores) / len(scores) if scores else 0.0
                employees[emp_id]['skills'].sort(key=lambda x: x['score'], reverse=True)
            
            conn.close()
            return dict(employees)
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 获取所有员工摘要失败: {e}")
            return {}
    
    def get_thinking_focus(self, employee_id):
        try:
            conn = sqlite3.connect('skill_evolution.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM thinking_focus WHERE employee_id = ?', (employee_id,))
            rows = cursor.fetchall()
            
            focus = []
            for row in rows:
                focus.append({
                    'area': row[2],
                    'score': row[3],
                    'trend': row[4],
                    'last_updated': row[5]
                })
            
            conn.close()
            return focus
        except Exception as e:
            logger.info(f"[AI Skill Evolution] 获取思维焦点失败: {e}")
            return []

skill_evolution_system = AISkillEvolutionSystem()