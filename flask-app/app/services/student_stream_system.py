import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
学生分科系统服务
实现学生9年级分文科理科方向的功能
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class StudentStreamSystem:
    """学生分科系统核心服务"""
    
    STREAM_ARTS = "arts"
    STREAM_SCIENCE = "science"
    STREAM_BOTH = "both"
    
    STREAM_NAMES = {
        STREAM_ARTS: "文科",
        STREAM_SCIENCE: "理科",
        STREAM_BOTH: "文理兼修"
    }
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化学生分科相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DROP TABLE IF EXISTS student_streams')
            cursor.execute('DROP TABLE IF EXISTS student_stream_history')
            cursor.execute('DROP TABLE IF EXISTS stream_recommendations')
            
            cursor.execute('''
                CREATE TABLE student_streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    student_name TEXT,
                    grade INTEGER NOT NULL,
                    current_stream TEXT,
                    preferred_stream TEXT,
                    stream_score_arts REAL DEFAULT 0.0,
                    stream_score_science REAL DEFAULT 0.0,
                    decision_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE student_stream_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    from_stream TEXT,
import sys
                    to_stream TEXT,
                    change_reason TEXT,
                    changed_by TEXT,
                    change_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE stream_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    recommended_stream TEXT,
                    confidence REAL DEFAULT 0.0,
                    factors TEXT,
                    generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def check_eligible_for_stream(self, student_id: int, grade: int) -> bool:
        """检查是否符合分科条件(9年级及以上)"""
        return grade >= 9
    
    def calculate_stream_scores(self, student_id: int, grade: int, 
                              scores: Dict[str, float]) -> Dict[str, float]:
        """计算文理科分数"""
        arts_subjects = ['语文', '英语', '历史', '地理', '政治']
        science_subjects = ['数学', '物理', '化学', '生物', '计算机']
        
        arts_score = sum(scores.get(subject, 0) for subject in arts_subjects) / len(arts_subjects)
        science_score = sum(scores.get(subject, 0) for subject in science_subjects) / len(science_subjects)
        
        return {
            'arts': arts_score,
            'science': science_score,
            'difference': arts_score - science_score
        }
    
    def recommend_stream(self, student_id: int, student_name: str, grade: int,
                       scores: Dict[str, float]) -> Dict:
        """推荐分科方向"""
        if not self.check_eligible_for_stream(student_id, grade):
            return {
                'eligible': False,
                'message': f"年级{grade}未达到分科要求(需9年级及以上)",
                'recommendation': None
            }
        
        stream_scores = self.calculate_stream_scores(student_id, grade, scores)
        arts_score = stream_scores['arts']
        science_score = stream_scores['science']
        
        factors = []
        if arts_score >= 80:
            factors.append("文科成绩优秀")
        if science_score >= 80:
            factors.append("理科成绩优秀")
        if arts_score >= science_score + 10:
            factors.append("文科优势明显")
        elif science_score >= arts_score + 10:
            factors.append("理科优势明显")
        else:
            factors.append("文理均衡")
        
        if arts_score > science_score + 5:
            recommended = self.STREAM_ARTS
            confidence = min(95, 70 + (arts_score - science_score))
        elif science_score > arts_score + 5:
            recommended = self.STREAM_SCIENCE
            confidence = min(95, 70 + (science_score - arts_score))
        else:
            recommended = self.STREAM_BOTH
            confidence = 85
        
        result = {
            'eligible': True,
            'student_id': student_id,
            'student_name': student_name,
            'grade': grade,
            'arts_score': arts_score,
            'science_score': science_score,
            'recommended_stream': recommended,
            'recommended_stream_name': self.STREAM_NAMES[recommended],
            'confidence': confidence,
            'factors': factors,
            'generated_at': datetime.now().isoformat()
        }
        
        self._save_recommendation(student_id, recommended, confidence, factors)
        
        return result
    
    def _save_recommendation(self, student_id: int, stream: str, 
                           confidence: float, factors: List[str]):
        """保存推荐记录"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO stream_recommendations
                    (student_id, recommended_stream, confidence, factors)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, stream, confidence, json.dumps(factors)))
                conn.commit()
        except Exception:
            pass
    
    def set_stream(self, student_id: int, student_name: str, grade: int,
                  stream: str, changed_by: str = "system") -> Dict:
        """设置学生分科方向"""
        if not self.check_eligible_for_stream(student_id, grade):
            return {
                'success': False,
                'message': f"年级{grade}未达到分科要求(需9年级及以上)"
            }
        
        if stream not in [self.STREAM_ARTS, self.STREAM_SCIENCE, self.STREAM_BOTH]:
            return {
                'success': False,
                'message': f"无效的分科方向: {stream}"
            }
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT current_stream FROM student_streams WHERE student_id = ? AND status = "active"',
                             (student_id,))
                row = cursor.fetchone()
                old_stream = row[0] if row else None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO student_streams
                    (student_id, student_name, grade, current_stream, preferred_stream, decision_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (student_id, student_name, grade, stream, stream, datetime.now()))
                
                if old_stream and old_stream != stream:
                    cursor.execute('''
                        INSERT INTO student_stream_history
                        (student_id, from_stream, to_stream, change_reason, changed_by)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (student_id, old_stream, stream, "学生主动更改分科", changed_by))
                
                conn.commit()
                
                return {
                    'success': True,
                    'student_id': student_id,
                    'student_name': student_name,
                    'stream': stream,
                    'stream_name': self.STREAM_NAMES[stream],
                    'message': f"已成功设置为{self.STREAM_NAMES[stream]}方向"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"设置分科失败: {str(e)}"
            }
    
    def get_student_stream(self, student_id: int) -> Optional[Dict]:
        """获取学生当前分科信息"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT student_name, grade, current_stream, preferred_stream,
                           stream_score_arts, stream_score_science, decision_date, status
                    FROM student_streams WHERE student_id = ? AND status = "active"
                ''', (student_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'student_id': student_id,
                        'student_name': row[0],
                        'grade': row[1],
                        'current_stream': row[2],
                        'current_stream_name': self.STREAM_NAMES.get(row[2], row[2]),
                        'preferred_stream': row[3],
                        'stream_score_arts': row[4],
                        'stream_score_science': row[5],
                        'decision_date': row[6],
                        'status': row[7]
                    }
                return None
        except Exception as e:
            print(f"获取分科信息失败: {e}")
            return None
    
    def get_stream_history(self, student_id: int) -> List[Dict]:
        """获取学生分科变更历史"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT from_stream, to_stream, change_reason, changed_by, change_date
                    FROM student_stream_history WHERE student_id = ? ORDER BY change_date DESC
                ''', (student_id,))
                
                return [{
                    'from_stream': self.STREAM_NAMES.get(row[0], row[0]),
                    'to_stream': self.STREAM_NAMES.get(row[1], row[1]),
                    'reason': row[2],
                    'changed_by': row[3],
                    'change_date': row[4]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取分科历史失败: {e}")
            return []
    
    def get_recommendation_history(self, student_id: int) -> List[Dict]:
        """获取学生分科推荐历史"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT recommended_stream, confidence, factors, generated_at
                    FROM stream_recommendations WHERE student_id = ? ORDER BY generated_at DESC
                ''', (student_id,))
                
                return [{
                    'recommended_stream': self.STREAM_NAMES.get(row[0], row[0]),
                    'confidence': row[1],
                    'factors': json.loads(row[2]) if row[2] else [],
                    'generated_at': row[3]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取推荐历史失败: {e}")
            return []
    
    def get_stream_summary(self, grade: int = None) -> Dict:
        """获取分科统计摘要"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if grade:
                    cursor.execute('''
                        SELECT current_stream, COUNT(*) as count
                        FROM student_streams
                        WHERE status = "active" AND grade = ?
                        GROUP BY current_stream
                    ''', (grade,))
                else:
                    cursor.execute('''
                        SELECT current_stream, COUNT(*) as count
                        FROM student_streams WHERE status = "active"
                        GROUP BY current_stream
                    ''')
                
                stream_counts = {}
                total = 0
                for row in cursor.fetchall():
                    stream_counts[self.STREAM_NAMES.get(row[0], row[0])] = row[1]
                    total += row[1]
                
                return {
                    'total_students': total,
                    'by_stream': stream_counts
                }
        except Exception as e:
            print(f"获取分科统计失败: {e}")
            return {'total_students': 0, 'by_stream': {}}
    
    def update_stream_scores(self, student_id: int, arts_score: float, science_score: float) -> bool:
        """更新学生文理科分数"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE student_streams 
                    SET stream_score_arts = ?, stream_score_science = ?
                    WHERE student_id = ? AND status = "active"
                ''', (arts_score, science_score, student_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新分数失败: {e}")
            return False
    
    def initialize_sample_data(self):
        """初始化示例数据"""
        students = [
            (1001, "李明", 9, {"语文": 85, "数学": 92, "英语": 88, "物理": 90, "化学": 85, "生物": 80, "历史": 75, "地理": 70, "政治": 72}),
            (1002, "王芳", 9, {"语文": 92, "数学": 75, "英语": 90, "物理": 70, "化学": 65, "生物": 72, "历史": 88, "地理": 85, "政治": 82}),
            (1003, "张伟", 9, {"语文": 80, "数学": 88, "英语": 85, "物理": 85, "化学": 82, "生物": 88, "历史": 80, "地理": 78, "政治": 75}),
            (1004, "刘洋", 10, {"语文": 88, "数学": 95, "英语": 82, "物理": 92, "化学": 88, "生物": 85, "历史": 70, "地理": 65, "政治": 68}),
            (1005, "陈静", 10, {"语文": 95, "数学": 78, "英语": 92, "物理": 72, "化学": 68, "生物": 70, "历史": 90, "地理": 88, "政治": 85}),
        ]
        
        for student_id, name, grade, scores in students:
            recommendation = self.recommend_stream(student_id, name, grade, scores)
            if recommendation['eligible']:
                self.set_stream(student_id, name, grade, recommendation['recommended_stream'])

if __name__ == "__main__":
    stream_system = StudentStreamSystem()
    
    print("=== 学生分科系统测试 ===\n")
    
    stream_system.initialize_sample_data()
    print("✓ 示例数据初始化完成")
    
    summary = stream_system.get_stream_summary()
    print(f"\n分科统计:")
    print(f"  总人数: {summary['total_students']}")
    print(f"  分科分布: {summary['by_stream']}")
    
    student_info = stream_system.get_student_stream(1001)
    print(f"\n李明同学分科信息:")
    print(f"  年级: 9年级")
    print(f"  当前分科: {student_info['current_stream_name']}")
    print(f"  分科日期: {student_info['decision_date']}")
    
    history = stream_system.get_stream_history(1001)
    if history:
        print(f"\n李明同学分科历史:")
        for h in history:
            print(f"  - {h['change_date']}: {h['from_stream']} → {h['to_stream']}")
    
    scores = {"语文": 88, "数学": 90, "英语": 85, "物理": 88, "化学": 85, "生物": 82, "历史": 80, "地理": 78, "政治": 75}
    recommendation = stream_system.recommend_stream(1006, "赵强", 9, scores)
    print(f"\n赵强同学分科推荐:")
    print(f"  符合条件: {'是' if recommendation['eligible'] else '否'}")
    if recommendation['eligible']:
        print(f"  文科分数: {recommendation['arts_score']:.1f}")
        print(f"  理科分数: {recommendation['science_score']:.1f}")
        print(f"  推荐方向: {recommendation['recommended_stream_name']}")
        print(f"  置信度: {recommendation['confidence']:.1f}%")
        print(f"  推荐因素: {recommendation['factors']}")
    
    logger.info("\n == 测试完成 ===")
