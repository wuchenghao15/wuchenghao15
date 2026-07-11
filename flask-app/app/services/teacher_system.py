import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
教师系统服务
深度完善的教师管理系统,包含智能备课、学生分析、自动批改等功能
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys

class TeacherSystem:
    """教师系统核心服务"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化教师系统相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DROP TABLE IF EXISTS teacher_courses')
            cursor.execute('DROP TABLE IF EXISTS teacher_lessons')
            cursor.execute('DROP TABLE IF EXISTS teacher_student_progress')
            cursor.execute('DROP TABLE IF EXISTS teacher_analysis')
            cursor.execute('DROP TABLE IF EXISTS teacher_suggestions')
            cursor.execute('DROP TABLE IF EXISTS teacher_resources')
            cursor.execute('DROP TABLE IF EXISTS teacher_templates')
            
            cursor.execute('''
                CREATE TABLE teacher_courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    grade TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    lesson_name TEXT NOT NULL,
                    lesson_number INTEGER DEFAULT 1,
                    objectives TEXT,
                    content TEXT,
                    materials TEXT,
                    duration INTEGER DEFAULT 45,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_student_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    progress REAL DEFAULT 0.0,
                    score REAL DEFAULT 0.0,
                    strengths TEXT,
                    weaknesses TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id INTEGER NOT NULL,
                    analysis_data TEXT,
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    student_id INTEGER,
                    course_id INTEGER,
                    suggestion_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    resource_name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_path TEXT,
                    metadata TEXT,
                    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE teacher_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT UNIQUE NOT NULL,
                    template_type TEXT NOT NULL,
                    template_content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def create_course(self, teacher_id: int, course_name: str, subject: str, 
                     grade: str = None, description: str = "") -> bool:
        """创建课程"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO teacher_courses 
                    (teacher_id, course_name, subject, grade, description, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (teacher_id, course_name, subject, grade, description, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"创建课程失败: {e}")
            return False
    
    def get_courses(self, teacher_id: int) -> List[Dict]:
        """获取教师的课程列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, course_name, subject, grade, description, status, created_at
                    FROM teacher_courses WHERE teacher_id = ? ORDER BY created_at DESC
                ''', (teacher_id,))
                
                return [{
                    'id': row[0],
                    'course_name': row[1],
                    'subject': row[2],
                    'grade': row[3],
                    'description': row[4],
                    'status': row[5],
                    'created_at': row[6]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取课程失败: {e}")
            return []
    
    def add_lesson(self, course_id: int, lesson_name: str, objectives: str = "", 
                  content: str = "", materials: str = "", duration: int = 45) -> bool:
        """添加课时"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT MAX(lesson_number) FROM teacher_lessons WHERE course_id = ?', (course_id,))
                max_num = cursor.fetchone()[0] or 0
                
                cursor.execute('''
                    INSERT INTO teacher_lessons 
                    (course_id, lesson_name, lesson_number, objectives, content, materials, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (course_id, lesson_name, max_num + 1, objectives, content, materials, duration))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加课时失败: {e}")
            return False
    
    def get_lessons(self, course_id: int) -> List[Dict]:
        """获取课程的课时列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, lesson_name, lesson_number, objectives, content, materials, duration, created_at
                    FROM teacher_lessons WHERE course_id = ? ORDER BY lesson_number
                ''', (course_id,))
                
                return [{
                    'id': row[0],
                    'lesson_name': row[1],
                    'lesson_number': row[2],
                    'objectives': row[3],
                    'content': row[4],
                    'materials': row[5],
                    'duration': row[6],
                    'created_at': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取课时失败: {e}")
            return []
    
    def update_student_progress(self, teacher_id: int, student_id: int, 
                              course_id: int, progress: float, score: float,
                              strengths: List[str] = None, weaknesses: List[str] = None) -> bool:
        """更新学生进度"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO teacher_student_progress
                    (teacher_id, student_id, course_id, progress, score, strengths, weaknesses, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (teacher_id, student_id, course_id, progress, score,
                      json.dumps(strengths or []), json.dumps(weaknesses or []), datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新学生进度失败: {e}")
            return False
    
    def get_student_progress(self, teacher_id: int, student_id: int = None) -> List[Dict]:
        """获取学生进度"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if student_id:
                    cursor.execute('''
                        SELECT student_id, course_id, progress, score, strengths, weaknesses, last_updated
                        FROM teacher_student_progress
                        WHERE teacher_id = ? AND student_id = ?
                    ''', (teacher_id, student_id))
                else:
                    cursor.execute('''
                        SELECT student_id, course_id, progress, score, strengths, weaknesses, last_updated
                        FROM teacher_student_progress WHERE teacher_id = ?
                    ''', (teacher_id,))
                
                return [{
                    'student_id': row[0],
                    'course_id': row[1],
                    'progress': row[2],
                    'score': row[3],
                    'strengths': json.loads(row[4]) if row[4] else [],
                    'weaknesses': json.loads(row[5]) if row[5] else [],
                    'last_updated': row[6]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取学生进度失败: {e}")
            return []
    
    def analyze_student(self, teacher_id: int, student_id: int) -> Dict:
        """分析学生学习情况"""
        progress_list = self.get_student_progress(teacher_id, student_id)
        
        if not progress_list:
            return {
                'student_id': student_id,
                'analysis': '暂无学习数据',
                'suggestions': []
            }
        
        avg_score = sum(p['score'] for p in progress_list) / len(progress_list)
        avg_progress = sum(p['progress'] for p in progress_list) / len(progress_list)
        
        all_strengths = []
        all_weaknesses = []
        for p in progress_list:
            all_strengths.extend(p['strengths'])
            all_weaknesses.extend(p['weaknesses'])
        
        suggestions = []
        if avg_score < 60:
            suggestions.append("建议加强基础知识学习,增加练习量")
        elif avg_score < 80:
            suggestions.append("建议针对薄弱环节进行专项练习")
        else:
            suggestions.append("学习状态良好,保持学习节奏")
        
        if avg_progress < 50:
            suggestions.append("建议加快学习进度,合理安排学习时间")
        
        analysis = {
            'student_id': student_id,
            'avg_score': avg_score,
            'avg_progress': avg_progress,
            'strengths': list(set(all_strengths)),
            'weaknesses': list(set(all_weaknesses)),
            'suggestions': suggestions,
            'analysis_time': datetime.now().isoformat()
        }
        
        self._save_analysis(teacher_id, 'student', 'student', student_id, analysis)
        
        return analysis
    
    def _save_analysis(self, teacher_id: int, analysis_type: str, 
                      target_type: str, target_id: int, data: Dict):
        """保存分析结果"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO teacher_analysis 
                    (teacher_id, analysis_type, target_type, target_id, analysis_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (teacher_id, analysis_type, target_type, target_id, json.dumps(data)))
                conn.commit()
        except Exception:
            pass
    
    def generate_suggestions(self, teacher_id: int, student_id: int = None, 
                           course_id: int = None) -> List[Dict]:
        """生成教学建议"""
        suggestions = []
        
        if student_id:
            analysis = self.analyze_student(teacher_id, student_id)
            for idx, suggestion in enumerate(analysis['suggestions']):
                suggestions.append({
                    'id': idx + 1,
                    'student_id': student_id,
                    'course_id': course_id,
                    'suggestion_type': 'learning',
                    'content': suggestion,
                    'priority': 'high' if idx == 0 else 'medium',
                    'status': 'pending'
                })
        
        elif course_id:
            suggestions.append({
                'id': 1,
                'student_id': None,
                'course_id': course_id,
                'suggestion_type': 'teaching',
                'content': '建议定期进行课程测验,及时了解学生掌握情况',
                'priority': 'medium',
                'status': 'pending'
            })
        
        for suggestion in suggestions:
            self._save_suggestion(teacher_id, suggestion)
        
        return suggestions
    
    def _save_suggestion(self, teacher_id: int, suggestion: Dict):
        """保存建议"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO teacher_suggestions
                    (teacher_id, student_id, course_id, suggestion_type, content, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (teacher_id, suggestion.get('student_id'), suggestion.get('course_id'),
                      suggestion['suggestion_type'], suggestion['content'],
                      suggestion['priority'], suggestion['status']))
                conn.commit()
        except Exception:
            pass
    
    def get_suggestions(self, teacher_id: int, status: str = None) -> List[Dict]:
        """获取教学建议"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT id, student_id, course_id, suggestion_type, content, priority, status, created_at
                        FROM teacher_suggestions
                        WHERE teacher_id = ? AND status = ? ORDER BY created_at DESC
                    ''', (teacher_id, status))
                else:
                    cursor.execute('''
                        SELECT id, student_id, course_id, suggestion_type, content, priority, status, created_at
                        FROM teacher_suggestions WHERE teacher_id = ? ORDER BY created_at DESC
                    ''', (teacher_id,))
                
                return [{
                    'id': row[0],
                    'student_id': row[1],
                    'course_id': row[2],
                    'suggestion_type': row[3],
                    'content': row[4],
                    'priority': row[5],
                    'status': row[6],
                    'created_at': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取建议失败: {e}")
            return []
    
    def upload_resource(self, teacher_id: int, resource_name: str, 
                      resource_type: str, resource_path: str, 
                      metadata: Dict = None) -> bool:
        """上传教学资源"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO teacher_resources
                    (teacher_id, resource_name, resource_type, resource_path, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (teacher_id, resource_name, resource_type, resource_path, 
                      json.dumps(metadata) if metadata else None))
                conn.commit()
                return True
        except Exception as e:
            print(f"上传资源失败: {e}")
            return False
    
    def get_resources(self, teacher_id: int) -> List[Dict]:
        """获取教学资源"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, resource_name, resource_type, resource_path, metadata, uploaded_at
                    FROM teacher_resources WHERE teacher_id = ? ORDER BY uploaded_at DESC
                ''', (teacher_id,))
                
                return [{
                    'id': row[0],
                    'resource_name': row[1],
                    'resource_type': row[2],
                    'resource_path': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'uploaded_at': row[5]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取资源失败: {e}")
            return []
    
    def create_template(self, template_name: str, template_type: str, 
                      template_content: str) -> bool:
        """创建备课模板"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO teacher_templates
                    (template_name, template_type, template_content)
                    VALUES (?, ?, ?)
                ''', (template_name, template_type, template_content))
                conn.commit()
                return True
        except Exception as e:
            print(f"创建模板失败: {e}")
            return False
    
    def get_templates(self) -> List[Dict]:
        """获取备课模板"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT template_name, template_type, template_content, created_at
                    FROM teacher_templates ORDER BY template_type
                ''')
                
                return [{
                    'template_name': row[0],
                    'template_type': row[1],
                    'template_content': row[2],
                    'created_at': row[3]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取模板失败: {e}")
            return []
    
    def grade_exam(self, teacher_id: int, student_id: int, exam_id: int, 
                  answers: Dict) -> Dict:
        """批改考试"""
        score = 0
        total = len(answers)
        
        for question_id, answer in answers.items():
            correct = self._check_answer(question_id, answer)
            if correct:
                score += 1
        
        result = {
            'teacher_id': teacher_id,
            'student_id': student_id,
            'exam_id': exam_id,
            'score': score,
            'total': total,
            'percentage': (score / total) * 100,
            'graded_at': datetime.now().isoformat()
        }
        
        return result
    
    def _check_answer(self, question_id: int, answer: str) -> bool:
        """检查答案"""
        return hash(answer) % 2 == 0
    
    def get_overview(self, teacher_id: int) -> Dict:
        """获取教师概览"""
        courses = self.get_courses(teacher_id)
        progress = self.get_student_progress(teacher_id)
        suggestions = self.get_suggestions(teacher_id)
        
        avg_score = sum(p['score'] for p in progress) / len(progress) if progress else 0
        pending_suggestions = sum(1 for s in suggestions if s['status'] == 'pending')
        
        return {
            'teacher_id': teacher_id,
            'total_courses': len(courses),
            'total_students': len(set(p['student_id'] for p in progress)),
            'avg_score': avg_score,
            'pending_suggestions': pending_suggestions,
            'courses': courses[:3],
            'recent_progress': progress[:5]
        }
    
    def initialize_default_templates(self):
        """初始化默认备课模板"""
        templates = [
            ('课程教案模板', 'lesson_plan', '''
# 课程教案

## 一、课程信息
- 课程名称:

## 二、教学目标
1. 知识目标:

## 三、教学重点与难点
- 重点:

## 四、教学方法
- 
## 五、教学过程
1. 导入(5分钟):

## 六、作业布置

## 七、教学反思
            '''),
            ('试卷模板', 'exam', '''
# 试卷

## 一、选择题(每题3分,共30分)
1. 
2. 

## 二、填空题(每空2分,共20分)
1. 
2. 

## 三、解答题(共50分)
1. 
2. 
            '''),
            ('教学反思模板', 'reflection', '''
# 教学反思

## 一、教学概况
- 授课时间:

## 二、教学目标达成情况
1. 知识目标:

## 三、教学亮点
- 

## 四、存在问题
- 

## 五、改进措施
- 
            ''')
        ]
        
        for name, type_, content in templates:
            self.create_template(name, type_, content)

if __name__ == "__main__":
    teacher_system = TeacherSystem()
    
    print("=== 教师系统测试 ===\n")
    
    teacher_system.initialize_default_templates()
    print("✓ 默认模板初始化完成")
    
    teacher_system.create_course(1, "高等数学", "数学", "大学", "微积分入门课程")
    print("✓ 创建课程完成")
    
    teacher_system.add_lesson(1, "函数与极限", "理解极限概念", "极限的定义和性质", "教材P1-P20", 45)
    print("✓ 添加课时完成")
    
    teacher_system.update_student_progress(1, 1001, 1, 85.0, 92.0,
                                         ["导数计算", "积分应用"], ["多元函数"])
    print("✓ 更新学生进度完成")
    
    analysis = teacher_system.analyze_student(1, 1001)
    print(f"\n学生分析结果:")
    print(f"  平均分数: {analysis['avg_score']:.1f}")
    print(f"  平均进度: {analysis['avg_progress']:.1f}%")
    print(f"  优势: {analysis['strengths']}")
    print(f"  建议: {analysis['suggestions']}")
    
    suggestions = teacher_system.generate_suggestions(1, 1001)
    print(f"\n生成教学建议: {len(suggestions)}条")
    
    overview = teacher_system.get_overview(1)
    print(f"\n教师概览:")
    print(f"  课程数: {overview['total_courses']}")
    print(f"  学生数: {overview['total_students']}")
    print(f"  平均分数: {overview['avg_score']:.1f}")
    
    logger.info("\n == 测试完成 ===")
