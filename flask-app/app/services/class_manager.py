import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
班级管理系统服务
实现学生自动分班功能,每45人组成一个班级
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class ClassManager:
    """班级管理系统核心服务"""
    
    DEFAULT_CLASS_SIZE = 45
    
    def __init__(self, db_path: str = "app.db", class_size: int = DEFAULT_CLASS_SIZE):
        self.db_path = db_path
        self.class_size = class_size
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化班级管理相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DROP TABLE IF EXISTS classes')
            cursor.execute('DROP TABLE IF EXISTS class_students')
            cursor.execute('DROP TABLE IF EXISTS class_history')
            
            cursor.execute('''
                CREATE TABLE classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT UNIQUE NOT NULL,
                    grade INTEGER NOT NULL,
                    stream TEXT,
                    max_students INTEGER DEFAULT 45,
                    current_students INTEGER DEFAULT 0,
                    teacher_id INTEGER,
                    teacher_name TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE class_students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    student_name TEXT,
                    enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    UNIQUE(class_id, student_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE class_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    student_id INTEGER,
                    action TEXT NOT NULL,
                    reason TEXT,
                    changed_by TEXT,
                    changed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def create_class(self, grade: int, stream: str = "", teacher_id: int = None, 
                    teacher_name: str = "", max_students: int = None) -> Dict:
        """创建班级"""
        class_count = self._get_class_count(grade, stream) + 1
        class_name = self._generate_class_name(grade, stream, class_count)
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO classes
                    (class_name, grade, stream, max_students, teacher_id, teacher_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (class_name, grade, stream, max_students or self.class_size, teacher_id, teacher_name))
                conn.commit()
                
                return {
                    'success': True,
                    'class_id': cursor.lastrowid,
                    'class_name': class_name,
                    'grade': grade,
                    'stream': stream
                }
        except Exception as e:
            return {'success': False, 'message': f"创建班级失败: {str(e)}"}
    
    def _generate_class_name(self, grade: int, stream: str, count: int) -> str:
        """生成班级名称"""
        stream_suffix = {
            'arts': '文',
            'science': '理',
            'both': '综'
        }.get(stream, '')
        
        return f"{grade}年级{stream_suffix}{count}班"
    
    def _get_class_count(self, grade: int, stream: str = "") -> int:
        """获取年级/分科的班级数量"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if stream:
                    cursor.execute('SELECT COUNT(*) FROM classes WHERE grade = ? AND stream = ? AND status = "active"',
                                 (grade, stream))
                else:
                    cursor.execute('SELECT COUNT(*) FROM classes WHERE grade = ? AND status = "active"', (grade,))
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    def add_student_to_class(self, student_id: int, student_name: str, grade: int, 
                           stream: str = "", auto_create: bool = True) -> Dict:
        """添加学生到班级(自动分组)"""
        class_info = self._find_or_create_class(grade, stream, auto_create)
        
        if not class_info['success']:
            return class_info
        
        class_id = class_info['class_id']
        class_name = class_info['class_name']
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM class_students WHERE class_id = ? AND student_id = ?',
                             (class_id, student_id))
                if cursor.fetchone():
                    return {'success': False, 'message': f"学生{student_name}已在{class_name}"}
                
                cursor.execute('''
                    INSERT INTO class_students (class_id, student_id, student_name)
                    VALUES (?, ?, ?)
                ''', (class_id, student_id, student_name))
                
                cursor.execute('UPDATE classes SET current_students = current_students + 1 WHERE id = ?',
                             (class_id,))
                
                cursor.execute('''
                    INSERT INTO class_history (class_id, student_id, action, reason)
                    VALUES (?, ?, ?, ?)
                ''', (class_id, student_id, 'enroll', '自动分班'))
                
                conn.commit()
                
                return {
                    'success': True,
                    'class_id': class_id,
                    'class_name': class_name,
                    'student_id': student_id,
                    'student_name': student_name,
                    'message': f"学生{student_name}已分配到{class_name}"
                }
        except Exception as e:
            return {'success': False, 'message': f"分配失败: {str(e)}"}
    
    def _find_or_create_class(self, grade: int, stream: str = "", auto_create: bool = True) -> Dict:
        """查找或创建班级"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if stream:
                    cursor.execute('''
                        SELECT id, class_name, current_students, max_students
                        FROM classes 
                        WHERE grade = ? AND stream = ? AND status = "active" AND current_students < max_students
                        ORDER BY current_students DESC LIMIT 1
                    ''', (grade, stream))
                else:
                    cursor.execute('''
                        SELECT id, class_name, current_students, max_students
                        FROM classes 
                        WHERE grade = ? AND status = "active" AND current_students < max_students
                        ORDER BY current_students DESC LIMIT 1
                    ''', (grade,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'success': True,
                        'class_id': row[0],
                        'class_name': row[1],
                        'current_students': row[2],
                        'max_students': row[3]
                    }
                
                if auto_create:
                    result = self.create_class(grade, stream)
                    if result['success']:
                        return {
                            'success': True,
                            'class_id': result['class_id'],
                            'class_name': result['class_name'],
                            'current_students': 0,
                            'max_students': self.class_size
                        }
                    return result
                
                return {'success': False, 'message': '没有可用班级且未启用自动创建'}
        except Exception as e:
            return {'success': False, 'message': f"查找班级失败: {str(e)}"}
    
    def batch_add_students(self, students: List[Dict], grade: int, stream: str = "") -> Dict:
        """批量添加学生并自动分班"""
        results = []
        success_count = 0
        fail_count = 0
        
        for student in students:
            result = self.add_student_to_class(
                student['student_id'],
                student['student_name'],
                grade,
                stream
            )
            results.append(result)
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
        
        return {
            'total': len(students),
            'success': success_count,
            'failed': fail_count,
            'results': results
        }
    
    def get_class_info(self, class_id: int) -> Optional[Dict]:
        """获取班级信息"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT class_name, grade, stream, max_students, current_students, 
                           teacher_id, teacher_name, status, created_at
                    FROM classes WHERE id = ?
                ''', (class_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'class_id': class_id,
                        'class_name': row[0],
                        'grade': row[1],
                        'stream': row[2],
                        'max_students': row[3],
                        'current_students': row[4],
                        'teacher_id': row[5],
                        'teacher_name': row[6],
                        'status': row[7],
                        'created_at': row[8]
                    }
                return None
        except Exception as e:
            print(f"获取班级信息失败: {e}")
            return None
    
    def get_class_students(self, class_id: int) -> List[Dict]:
        """获取班级学生列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_id, student_name, enrollment_date, status
                    FROM class_students WHERE class_id = ? AND status = "active"
                    ORDER BY enrollment_date
                ''', (class_id,))
                
                return [{
                    'student_id': row[0],
                    'student_name': row[1],
                    'enrollment_date': row[2],
                    'status': row[3]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取班级学生失败: {e}")
            return []
    
    def remove_student_from_class(self, class_id: int, student_id: int, reason: str = "主动退出") -> Dict:
        """从班级移除学生"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT student_name FROM class_students WHERE class_id = ? AND student_id = ?',
                             (class_id, student_id))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '学生不在该班级'}
                
                cursor.execute('UPDATE class_students SET status = "inactive" WHERE class_id = ? AND student_id = ?',
                             (class_id, student_id))
                
                cursor.execute('UPDATE classes SET current_students = current_students - 1 WHERE id = ?',
                             (class_id,))
                
                cursor.execute('''
                    INSERT INTO class_history (class_id, student_id, action, reason)
                    VALUES (?, ?, ?, ?)
                ''', (class_id, student_id, 'leave', reason))
                
                conn.commit()
                
                return {'success': True, 'message': f"学生{row[0]}已离开班级"}
        except Exception as e:
            return {'success': False, 'message': f"移除学生失败: {str(e)}"}
    
    def get_classes_by_grade(self, grade: int, stream: str = "") -> List[Dict]:
        """按年级获取班级列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if stream:
                    cursor.execute('''
                        SELECT id, class_name, max_students, current_students, teacher_name, status
                        FROM classes WHERE grade = ? AND stream = ? AND status = "active"
                        ORDER BY class_name
                    ''', (grade, stream))
                else:
                    cursor.execute('''
                        SELECT id, class_name, max_students, current_students, teacher_name, status
                        FROM classes WHERE grade = ? AND status = "active"
                        ORDER BY class_name
                    ''', (grade,))
                
                return [{
                    'class_id': row[0],
                    'class_name': row[1],
                    'max_students': row[2],
                    'current_students': row[3],
                    'teacher_name': row[4],
                    'status': row[5],
                    'full': row[3] >= row[2]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取班级列表失败: {e}")
            return []
    
    def get_student_class(self, student_id: int) -> Optional[Dict]:
        """获取学生所在班级"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.id, c.class_name, c.grade, c.stream, cs.enrollment_date
                    FROM class_students cs
                    JOIN classes c ON cs.class_id = c.id
                    WHERE cs.student_id = ? AND cs.status = "active" AND c.status = "active"
                ''', (student_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'class_id': row[0],
                        'class_name': row[1],
                        'grade': row[2],
                        'stream': row[3],
                        'enrollment_date': row[4]
                    }
                return None
        except Exception as e:
            print(f"获取学生班级失败: {e}")
            return None
    
    def get_class_summary(self, grade: int = None) -> Dict:
        """获取班级统计摘要"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if grade:
                    cursor.execute('''
                        SELECT stream, COUNT(*) as class_count, SUM(current_students) as total_students
                        FROM classes WHERE grade = ? AND status = "active"
                        GROUP BY stream
                    ''', (grade,))
                else:
                    cursor.execute('''
                        SELECT grade, stream, COUNT(*) as class_count, SUM(current_students) as total_students
                        FROM classes WHERE status = "active"
                        GROUP BY grade, stream
                    ''')
                
                summary = {}
                for row in cursor.fetchall():
                    if grade:
                        stream = row[0] or 'all'
                        summary[stream] = {'classes': row[1], 'students': row[2]}
                    else:
                        g = row[0]
                        s = row[1] or 'all'
                        if g not in summary:
                            summary[g] = {}
                        summary[g][s] = {'classes': row[2], 'students': row[3]}
                
                return summary
        except Exception as e:
            print(f"获取班级统计失败: {e}")
            return {}
    
    def assign_teacher(self, class_id: int, teacher_id: int, teacher_name: str) -> Dict:
        """分配教师到班级"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE classes SET teacher_id = ?, teacher_name = ? WHERE id = ?',
                             (teacher_id, teacher_name, class_id))
                conn.commit()
                
                class_info = self.get_class_info(class_id)
                return {
                    'success': True,
                    'class_name': class_info['class_name'],
                    'teacher_name': teacher_name,
                    'message': f"已为{class_info['class_name']}分配教师{teacher_name}"
                }
        except Exception as e:
            return {'success': False, 'message': f"分配教师失败: {str(e)}"}
    
    def initialize_sample_data(self):
        """初始化示例数据(100名学生自动分班)"""
        students = []
        for i in range(1, 101):
            students.append({
                'student_id': i,
                'student_name': f"学生{i:03d}"
            })
        
        result = self.batch_add_students(students, 9)
        print(f"初始化完成: {result['success']}人成功, {result['failed']}人失败")

if __name__ == "__main__":
    manager = ClassManager()
    
    print("=== 班级管理系统测试 ===\n")
    
    manager.initialize_sample_data()
    print("✓ 示例数据初始化完成")
    
    summary = manager.get_class_summary()
    print(f"\n班级统计摘要:")
    for grade, streams in summary.items():
        print(f"  第{grade}年级:")
        for stream, data in streams.items():
            stream_name = {'arts': '文科', 'science': '理科', 'all': '综合'}.get(stream, stream)
            print(f"    {stream_name}: {data['classes']}个班, {data['students']}名学生")
    
    classes = manager.get_classes_by_grade(9)
    print(f"\n9年级班级列表 ({len(classes)}个班):")
    for cls in classes:
        status = "已满" if cls['full'] else f"{cls['current_students']}/{cls['max_students']}"
        print(f"  - {cls['class_name']}: {status} | 班主任: {cls['teacher_name'] or '未分配'}")
    
    student_class = manager.get_student_class(1)
    print(f"\n学生1所在班级: {student_class['class_name']}")
    
    student_class = manager.get_student_class(46)
    print(f"学生46所在班级: {student_class['class_name']}")
    
    student_class = manager.get_student_class(91)
    print(f"学生91所在班级: {student_class['class_name']}")
    
    logger.info("\n == 测试完成 ===")
