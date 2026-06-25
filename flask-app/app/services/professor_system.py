import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
教授系统服务
深度完善的教授级功能,包含学术研究、课程设计、教学指导等高级功能
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class ProfessorSystem:
    """教授系统核心服务"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化教授系统相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DROP TABLE IF EXISTS professor_research')
            cursor.execute('DROP TABLE IF EXISTS professor_publications')
            cursor.execute('DROP TABLE IF EXISTS professor_projects')
            cursor.execute('DROP TABLE IF EXISTS professor_course_design')
            cursor.execute('DROP TABLE IF EXISTS professor_advising')
            cursor.execute('DROP TABLE IF EXISTS professor_mentoring')
            cursor.execute('DROP TABLE IF EXISTS professor_reviews')
            cursor.execute('DROP TABLE IF EXISTS professor_awards')
            cursor.execute('DROP TABLE IF EXISTS professor_delegations')
            cursor.execute('DROP TABLE IF EXISTS professor_teacher_evaluations')
            cursor.execute('DROP TABLE IF EXISTS professor_teacher_qualifications')
            cursor.execute('DROP TABLE IF EXISTS professor_qualification_upgrades')
            cursor.execute('DROP TABLE IF EXISTS professor_question_bank')
            
            cursor.execute('''
                CREATE TABLE professor_research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    research_title TEXT NOT NULL,
                    field TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    start_date TEXT,
                    end_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    journal TEXT,
                    year INTEGER,
                    authors TEXT,
                    citation_count INTEGER DEFAULT 0,
                    doi TEXT,
                    abstract TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    project_name TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    funding_source TEXT,
                    funding_amount REAL DEFAULT 0.0,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_course_design (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    course_level TEXT,
                    objectives TEXT,
                    curriculum TEXT,
                    teaching_methods TEXT,
                    assessment_methods TEXT,
                    resources TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_advising (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    student_name TEXT,
                    program TEXT,
                    thesis_title TEXT,
                    status TEXT DEFAULT 'active',
                    start_date TEXT,
                    expected_completion TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_mentoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    mentee_id INTEGER,
                    mentee_name TEXT,
                    mentor_type TEXT,
                    goals TEXT,
                    progress TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    review_type TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    reviewer_info TEXT,
                    review_result TEXT,
                    comments TEXT,
                    review_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_awards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    award_name TEXT NOT NULL,
                    awarding_body TEXT,
                    year INTEGER,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_delegations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    teacher_name TEXT,
                    subject TEXT NOT NULL,
                    grade_level TEXT,
                    delegation_type TEXT NOT NULL,
                    responsibilities TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_teacher_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    teacher_name TEXT,
                    current_title TEXT,
                    target_title TEXT,
                    evaluation_type TEXT NOT NULL,
                    criteria_scores TEXT,
                    total_score REAL,
                    evaluation_result TEXT,
                    comments TEXT,
                    evaluator_name TEXT,
                    evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_teacher_qualifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER NOT NULL,
                    teacher_name TEXT,
                    qualification_level INTEGER DEFAULT 1,
                    qualification_name TEXT,
                    major_subject TEXT,
                    minor_subjects TEXT,
                    experience_years INTEGER DEFAULT 0,
                    acquired_date TEXT,
                    expiry_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_qualification_upgrades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    teacher_name TEXT,
                    from_level INTEGER NOT NULL,
                    to_level INTEGER NOT NULL,
                    upgrade_type TEXT NOT NULL,
                    requirements_met TEXT,
                    upgrade_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'approved',
                    comments TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE professor_question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT,
                    difficulty_level TEXT,
                    question_type TEXT,
                    question_content TEXT NOT NULL,
                    options TEXT,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    source TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def add_research(self, professor_id: int, title: str, field: str, 
                    description: str = "", start_date: str = None) -> bool:
        """添加研究项目"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_research
                    (professor_id, research_title, field, description, start_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (professor_id, title, field, description, start_date))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加研究项目失败: {e}")
            return False
    
    def get_research_list(self, professor_id: int) -> List[Dict]:
        """获取研究项目列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, research_title, field, description, status, start_date, end_date
                    FROM professor_research WHERE professor_id = ? ORDER BY start_date DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'title': row[1],
                    'field': row[2],
                    'description': row[3],
                    'status': row[4],
                    'start_date': row[5],
                    'end_date': row[6]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取研究项目失败: {e}")
            return []
    
    def add_publication(self, professor_id: int, title: str, journal: str = "", 
                      year: int = None, authors: str = "", citation_count: int = 0,
                      doi: str = "", abstract: str = "") -> bool:
        """添加学术论文"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_publications
                    (professor_id, title, journal, year, authors, citation_count, doi, abstract)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, title, journal, year, authors, citation_count, doi, abstract))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加论文失败: {e}")
            return False
    
    def get_publications(self, professor_id: int) -> List[Dict]:
        """获取学术论文列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, journal, year, authors, citation_count, doi, abstract
                    FROM professor_publications WHERE professor_id = ? ORDER BY year DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'title': row[1],
                    'journal': row[2],
                    'year': row[3],
                    'authors': row[4],
                    'citations': row[5],
                    'doi': row[6],
                    'abstract': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取论文失败: {e}")
            return []
    
    def add_project(self, professor_id: int, name: str, project_type: str,
                   funding_source: str = "", funding_amount: float = 0.0,
                   start_date: str = None, end_date: str = None) -> bool:
        """添加科研项目"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_projects
                    (professor_id, project_name, project_type, funding_source, 
                     funding_amount, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, name, project_type, funding_source,
                      funding_amount, start_date, end_date))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加项目失败: {e}")
            return False
    
    def get_projects(self, professor_id: int) -> List[Dict]:
        """获取科研项目列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, project_name, project_type, funding_source, 
                           funding_amount, status, start_date, end_date
                    FROM professor_projects WHERE professor_id = ? ORDER BY start_date DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'funding_source': row[3],
                    'funding_amount': row[4],
                    'status': row[5],
                    'start_date': row[6],
                    'end_date': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取项目失败: {e}")
            return []
    
    def design_course(self, professor_id: int, course_name: str, course_level: str = "",
                     objectives: str = "", curriculum: str = "", teaching_methods: str = "",
                     assessment_methods: str = "", resources: str = "") -> bool:
        """设计课程"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_course_design
                    (professor_id, course_name, course_level, objectives, curriculum,
                     teaching_methods, assessment_methods, resources)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, course_name, course_level, objectives, curriculum,
                      teaching_methods, assessment_methods, resources))
                conn.commit()
                return True
        except Exception as e:
            print(f"设计课程失败: {e}")
            return False
    
    def get_course_designs(self, professor_id: int) -> List[Dict]:
        """获取课程设计列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, course_name, course_level, objectives, curriculum,
                           teaching_methods, assessment_methods, resources, created_at
                    FROM professor_course_design WHERE professor_id = ? ORDER BY created_at DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'course_name': row[1],
                    'course_level': row[2],
                    'objectives': row[3],
                    'curriculum': row[4],
                    'teaching_methods': row[5],
                    'assessment_methods': row[6],
                    'resources': row[7],
                    'created_at': row[8]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取课程设计失败: {e}")
            return []
    
    def add_advising(self, professor_id: int, student_id: int, student_name: str,
                    program: str = "", thesis_title: str = "", start_date: str = None,
                    expected_completion: str = None) -> bool:
        """添加指导学生"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_advising
                    (professor_id, student_id, student_name, program, thesis_title, start_date, expected_completion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, student_id, student_name, program, thesis_title, start_date, expected_completion))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加指导学生失败: {e}")
            return False
    
    def get_advising_students(self, professor_id: int) -> List[Dict]:
        """获取指导学生列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, student_id, student_name, program, thesis_title, 
                           status, start_date, expected_completion
                    FROM professor_advising WHERE professor_id = ? ORDER BY start_date DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'student_id': row[1],
                    'student_name': row[2],
                    'program': row[3],
                    'thesis_title': row[4],
                    'status': row[5],
                    'start_date': row[6],
                    'expected_completion': row[7]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取指导学生失败: {e}")
            return []
    
    def add_mentoring(self, professor_id: int, mentee_name: str, mentor_type: str,
                     goals: str = "", progress: str = "") -> bool:
        """添加导师指导"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_mentoring
                    (professor_id, mentee_name, mentor_type, goals, progress)
                    VALUES (?, ?, ?, ?, ?)
                ''', (professor_id, mentee_name, mentor_type, goals, progress))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加导师指导失败: {e}")
            return False
    
    def add_review(self, professor_id: int, review_type: str, target_title: str,
                  reviewer_info: str = "", review_result: str = "", comments: str = "") -> bool:
        """添加评审记录"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_reviews
                    (professor_id, review_type, target_title, reviewer_info, review_result, comments)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (professor_id, review_type, target_title, reviewer_info, review_result, comments))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加评审记录失败: {e}")
            return False
    
    def add_award(self, professor_id: int, award_name: str, awarding_body: str = "",
                 year: int = None, description: str = "") -> bool:
        """添加获奖记录"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_awards
                    (professor_id, award_name, awarding_body, year, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (professor_id, award_name, awarding_body, year, description))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加获奖记录失败: {e}")
            return False
    
    def get_awards(self, professor_id: int) -> List[Dict]:
        """获取获奖记录"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, award_name, awarding_body, year, description
                    FROM professor_awards WHERE professor_id = ? ORDER BY year DESC
                ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'award_name': row[1],
                    'awarding_body': row[2],
                    'year': row[3],
                    'description': row[4]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取获奖记录失败: {e}")
            return []
    
    def add_delegation(self, professor_id: int, teacher_id: int, teacher_name: str,
                      subject: str, grade_level: str = "", delegation_type: str = "teaching",
                      responsibilities: str = "", start_date: str = None, end_date: str = None) -> bool:
        """添加教师委派"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_delegations
                    (professor_id, teacher_id, teacher_name, subject, grade_level,
                     delegation_type, responsibilities, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, teacher_id, teacher_name, subject, grade_level,
                      delegation_type, responsibilities, start_date, end_date))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加教师委派失败: {e}")
            return False
    
    def get_delegations(self, professor_id: int, status: str = None) -> List[Dict]:
        """获取委派列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT id, teacher_id, teacher_name, subject, grade_level,
                               delegation_type, responsibilities, status, start_date, end_date, created_at
                        FROM professor_delegations
                        WHERE professor_id = ? AND status = ? ORDER BY created_at DESC
                    ''', (professor_id, status))
                else:
                    cursor.execute('''
                        SELECT id, teacher_id, teacher_name, subject, grade_level,
                               delegation_type, responsibilities, status, start_date, end_date, created_at
                        FROM professor_delegations WHERE professor_id = ? ORDER BY created_at DESC
                    ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'teacher_id': row[1],
                    'teacher_name': row[2],
                    'subject': row[3],
                    'grade_level': row[4],
                    'delegation_type': row[5],
                    'responsibilities': row[6],
                    'status': row[7],
                    'start_date': row[8],
                    'end_date': row[9],
                    'created_at': row[10]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取委派列表失败: {e}")
            return []
    
    def update_delegation_status(self, delegation_id: int, status: str) -> bool:
        """更新委派状态"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE professor_delegations SET status = ? WHERE id = ?',
                             (status, delegation_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"更新委派状态失败: {e}")
            return False
    
    def get_delegation_by_teacher(self, teacher_id: int) -> List[Dict]:
        """获取教师的委派信息"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, professor_id, subject, grade_level, delegation_type,
                           responsibilities, status, start_date, end_date
                    FROM professor_delegations WHERE teacher_id = ? AND status = 'active'
                ''', (teacher_id,))
                
                return [{
                    'id': row[0],
                    'professor_id': row[1],
                    'subject': row[2],
                    'grade_level': row[3],
                    'delegation_type': row[4],
                    'responsibilities': row[5],
                    'status': row[6],
                    'start_date': row[7],
                    'end_date': row[8]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取教师委派信息失败: {e}")
            return []
    
    def get_delegation_summary(self, professor_id: int) -> Dict:
        """获取委派统计摘要"""
        delegations = self.get_delegations(professor_id)
        
        active_count = sum(1 for d in delegations if d['status'] == 'active')
        by_subject = {}
        by_type = {}
        
        for d in delegations:
            by_subject[d['subject']] = by_subject.get(d['subject'], 0) + 1
            by_type[d['delegation_type']] = by_type.get(d['delegation_type'], 0) + 1
        
        return {
            'total_delegations': len(delegations),
            'active_delegations': active_count,
            'by_subject': by_subject,
            'by_type': by_type
        }
    
    def create_evaluation(self, professor_id: int, teacher_id: int, teacher_name: str,
                         current_title: str, target_title: str, evaluation_type: str = "promotion",
                         criteria_scores: Dict = None, evaluator_name: str = "") -> bool:
        """创建教师职称测评"""
        try:
            criteria_scores = criteria_scores or {}
            total_score = sum(criteria_scores.values())
            
            result = "通过" if total_score >= 80 else "待评审" if total_score >= 60 else "不通过"
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_teacher_evaluations
                    (professor_id, teacher_id, teacher_name, current_title, target_title,
                     evaluation_type, criteria_scores, total_score, evaluation_result,
                     evaluator_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, teacher_id, teacher_name, current_title, target_title,
                      evaluation_type, json.dumps(criteria_scores), total_score, result, evaluator_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"创建职称测评失败: {e}")
            return False
    
    def get_evaluations(self, professor_id: int, status: str = None) -> List[Dict]:
        """获取测评列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                        SELECT id, teacher_id, teacher_name, current_title, target_title,
                               evaluation_type, criteria_scores, total_score, evaluation_result,
                               comments, evaluator_name, status, evaluation_date
                        FROM professor_teacher_evaluations
                        WHERE professor_id = ? AND status = ? ORDER BY evaluation_date DESC
                    ''', (professor_id, status))
                else:
                    cursor.execute('''
                        SELECT id, teacher_id, teacher_name, current_title, target_title,
                               evaluation_type, criteria_scores, total_score, evaluation_result,
                               comments, evaluator_name, status, evaluation_date
                        FROM professor_teacher_evaluations WHERE professor_id = ? ORDER BY evaluation_date DESC
                    ''', (professor_id,))
                
                return [{
                    'id': row[0],
                    'teacher_id': row[1],
                    'teacher_name': row[2],
                    'current_title': row[3],
                    'target_title': row[4],
                    'evaluation_type': row[5],
                    'criteria_scores': json.loads(row[6]) if row[6] else {},
                    'total_score': row[7],
                    'evaluation_result': row[8],
                    'comments': row[9],
                    'evaluator_name': row[10],
                    'status': row[11],
                    'evaluation_date': row[12]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取测评列表失败: {e}")
            return []
    
    def update_evaluation(self, evaluation_id: int, comments: str = "", status: str = None) -> bool:
        """更新测评结果"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('UPDATE professor_teacher_evaluations SET comments = ?, status = ? WHERE id = ?',
                                 (comments, status, evaluation_id))
                else:
                    cursor.execute('UPDATE professor_teacher_evaluations SET comments = ? WHERE id = ?',
                                 (comments, evaluation_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"更新测评失败: {e}")
            return False
    
    def get_teacher_evaluations(self, teacher_id: int) -> List[Dict]:
        """获取教师的测评记录"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, professor_id, current_title, target_title, evaluation_type,
                           total_score, evaluation_result, comments, evaluation_date, status
                    FROM professor_teacher_evaluations WHERE teacher_id = ? ORDER BY evaluation_date DESC
                ''', (teacher_id,))
                
                return [{
                    'id': row[0],
                    'professor_id': row[1],
                    'current_title': row[2],
                    'target_title': row[3],
                    'evaluation_type': row[4],
                    'total_score': row[5],
                    'evaluation_result': row[6],
                    'comments': row[7],
                    'evaluation_date': row[8],
                    'status': row[9]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取教师测评记录失败: {e}")
            return []
    
    def get_evaluation_summary(self, professor_id: int) -> Dict:
        """获取测评统计摘要"""
        evaluations = self.get_evaluations(professor_id)
        
        by_result = {}
        by_type = {}
        
        for e in evaluations:
            by_result[e['evaluation_result']] = by_result.get(e['evaluation_result'], 0) + 1
            by_type[e['evaluation_type']] = by_type.get(e['evaluation_type'], 0) + 1
        
        avg_score = sum(e['total_score'] for e in evaluations) / len(evaluations) if evaluations else 0
        
        return {
            'total_evaluations': len(evaluations),
            'average_score': avg_score,
            'by_result': by_result,
            'by_type': by_type
        }
    
    def generate_evaluation_report(self, teacher_id: int) -> Dict:
        """生成教师职称测评报告"""
        evaluations = self.get_teacher_evaluations(teacher_id)
        
        if not evaluations:
            return {
                'teacher_id': teacher_id,
                'has_evaluations': False,
                'message': '暂无测评记录'
            }
        
        recent = evaluations[0]
        history_scores = [e['total_score'] for e in evaluations]
        avg_score = sum(history_scores) / len(history_scores)
        
        report = {
            'teacher_id': teacher_id,
            'has_evaluations': True,
            'current_title': recent['current_title'],
            'target_title': recent['target_title'],
            'recent_score': recent['total_score'],
            'average_score': avg_score,
            'evaluation_count': len(evaluations),
            'recent_result': recent['evaluation_result'],
            'history_scores': history_scores,
            'suggestion': self._generate_evaluation_suggestion(recent),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_evaluation_suggestion(self, evaluation: Dict) -> str:
        """生成测评建议"""
        score = evaluation['total_score']
        if score >= 90:
            return "表现优秀,建议推荐晋升"
        elif score >= 80:
            return "表现良好,符合晋升要求"
        elif score >= 70:
            return "基本符合要求,建议继续提升教学水平"
        elif score >= 60:
            return "需要加强教学能力,建议参加培训"
        else:
            return "未达到要求,建议进行针对性提升"
    
    def add_qualification(self, teacher_id: int, teacher_name: str, level: int = 1,
                         qualification_name: str = "", major_subject: str = "",
                         minor_subjects: List[str] = None, experience_years: int = 0,
                         acquired_date: str = None, expiry_date: str = None) -> bool:
        """添加教师资格"""
        try:
            level_name = self._get_level_name(level)
            qualification_name = qualification_name or level_name
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_teacher_qualifications
                    (teacher_id, teacher_name, qualification_level, qualification_name,
                     major_subject, minor_subjects, experience_years, acquired_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (teacher_id, teacher_name, level, qualification_name,
                      major_subject, json.dumps(minor_subjects or []), experience_years,
                      acquired_date, expiry_date))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加教师资格失败: {e}")
            return False
    
    def _get_level_name(self, level: int) -> str:
        """获取级别名称"""
        level_names = {
            1: "初级教师资格",
            2: "中级教师资格",
            3: "高级教师资格",
            4: "特级教师资格",
            5: "首席教师资格"
        }
        return level_names.get(level, f"第{level}级教师资格")
    
    def get_qualification(self, teacher_id: int) -> Optional[Dict]:
        """获取教师当前资格"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, qualification_level, qualification_name, major_subject,
                           minor_subjects, experience_years, acquired_date, expiry_date, status
                    FROM professor_teacher_qualifications
                    WHERE teacher_id = ? AND status = 'active'
                    ORDER BY qualification_level DESC LIMIT 1
                ''', (teacher_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'level': row[1],
                        'name': row[2],
                        'major_subject': row[3],
                        'minor_subjects': json.loads(row[4]) if row[4] else [],
                        'experience_years': row[5],
                        'acquired_date': row[6],
                        'expiry_date': row[7],
                        'status': row[8]
                    }
                return None
        except Exception as e:
            print(f"获取教师资格失败: {e}")
            return None
    
    def check_upgrade_requirements(self, teacher_id: int, target_level: int) -> Dict:
        """检查升级资格要求"""
        current = self.get_qualification(teacher_id)
        if not current:
            return {'eligible': False, 'reason': '暂无教师资格'}
        
        current_level = current['level']
        if target_level <= current_level:
            return {'eligible': False, 'reason': '目标级别不高于当前级别'}
        
        requirements = self._get_upgrade_requirements(current_level, target_level)
        experience = current['experience_years']
        
        met = []
        not_met = []
        
        for req in requirements:
            if experience >= req['min_experience']:
                met.append(req)
            else:
                not_met.append(req)
        
        return {
            'eligible': len(not_met) == 0,
            'current_level': current_level,
            'target_level': target_level,
            'current_experience': experience,
            'requirements_met': met,
            'requirements_not_met': not_met
        }
    
    def _get_upgrade_requirements(self, from_level: int, to_level: int) -> List[Dict]:
        """获取升级要求"""
        requirements = {
            (1, 2): [{'name': '初级升中级', 'min_experience': 3, 'description': '至少3年教学经验'}],
            (2, 3): [{'name': '中级升高级', 'min_experience': 5, 'description': '至少5年教学经验'}],
            (3, 4): [{'name': '高级升特级', 'min_experience': 8, 'description': '至少8年教学经验'},
                     {'name': '教学成果要求', 'min_experience': 8, 'description': '需有显著教学成果'}],
            (4, 5): [{'name': '特级升首席', 'min_experience': 10, 'description': '至少10年教学经验'},
                     {'name': '学术成果要求', 'min_experience': 10, 'description': '需有重要学术成果'}],
        }
        
        key = (from_level, to_level)
        return requirements.get(key, [])
    
    def upgrade_qualification(self, professor_id: int, teacher_id: int, teacher_name: str,
                            target_level: int) -> Dict:
        """升级教师资格"""
        check_result = self.check_upgrade_requirements(teacher_id, target_level)
        
        if not check_result['eligible']:
            return {
                'success': False,
                'reason': check_result['reason'],
                'requirements': check_result
            }
        
        current = self.get_qualification(teacher_id)
        from_level = current['level']
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE professor_teacher_qualifications SET status = "inactive" WHERE teacher_id = ?',
                             (teacher_id,))
                
                cursor.execute('''
                    INSERT INTO professor_teacher_qualifications
                    (teacher_id, teacher_name, qualification_level, qualification_name,
                     major_subject, minor_subjects, experience_years, acquired_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (teacher_id, teacher_name, target_level, self._get_level_name(target_level),
                      current['major_subject'], json.dumps(current['minor_subjects']),
                      current['experience_years'], datetime.now()))
                
                cursor.execute('''
                    INSERT INTO professor_qualification_upgrades
                    (professor_id, teacher_id, teacher_name, from_level, to_level,
                     upgrade_type, requirements_met)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, teacher_id, teacher_name, from_level, target_level,
                      'automatic', json.dumps(check_result['requirements_met'])))
                
                conn.commit()
                
                return {
                    'success': True,
                    'from_level': from_level,
                    'to_level': target_level,
                    'from_name': self._get_level_name(from_level),
                    'to_name': self._get_level_name(target_level),
                    'message': f"资格已从{self._get_level_name(from_level)}升级为{self._get_level_name(target_level)}"
                }
        except Exception as e:
            print(f"升级资格失败: {e}")
            return {'success': False, 'reason': str(e)}
    
    def get_upgrade_history(self, teacher_id: int) -> List[Dict]:
        """获取教师升级历史"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT from_level, to_level, upgrade_type, upgrade_date, status, comments
                    FROM professor_qualification_upgrades WHERE teacher_id = ? ORDER BY upgrade_date DESC
                ''', (teacher_id,))
                
                return [{
                    'from_level': row[0],
                    'from_name': self._get_level_name(row[0]),
                    'to_level': row[1],
                    'to_name': self._get_level_name(row[1]),
                    'upgrade_type': row[2],
                    'upgrade_date': row[3],
                    'status': row[4],
                    'comments': row[5]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取升级历史失败: {e}")
            return []
    
    def get_qualification_summary(self, professor_id: int = None) -> Dict:
        """获取资格统计摘要"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if professor_id:
                    cursor.execute('''
                        SELECT q.qualification_level, COUNT(*) as count
                        FROM professor_teacher_qualifications q
                        JOIN professor_delegations d ON q.teacher_id = d.teacher_id
                        WHERE q.status = 'active' AND d.professor_id = ?
                        GROUP BY q.qualification_level
                    ''', (professor_id,))
                else:
                    cursor.execute('''
                        SELECT qualification_level, COUNT(*) as count
                        FROM professor_teacher_qualifications WHERE status = 'active'
                        GROUP BY qualification_level
                    ''')
                
                level_counts = {}
                total = 0
                for row in cursor.fetchall():
                    level_counts[self._get_level_name(row[0])] = row[1]
                    total += row[1]
                
                return {
                    'total_teachers': total,
                    'by_level': level_counts
                }
        except Exception as e:
            print(f"获取资格统计失败: {e}")
            return {'total_teachers': 0, 'by_level': {}}
    
    def add_question(self, professor_id: int, subject: str, question_content: str, 
                    correct_answer: str, topic: str = "", difficulty_level: str = "medium",
                    question_type: str = "choice", options: List[str] = None, 
                    explanation: str = "", source: str = "", tags: List[str] = None) -> Dict:
        """添加题目到题库"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO professor_question_bank
                    (professor_id, subject, topic, difficulty_level, question_type,
                     question_content, options, correct_answer, explanation, source, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (professor_id, subject, topic, difficulty_level, question_type,
                      question_content, json.dumps(options or []), correct_answer,
                      explanation, source, json.dumps(tags or [])))
                conn.commit()
                
                return {
                    'success': True,
                    'question_id': cursor.lastrowid,
                    'subject': subject,
                    'message': f"题目已成功添加到{subject}题库"
                }
        except Exception as e:
            return {'success': False, 'message': f"添加题目失败: {str(e)}"}
    
    def batch_add_questions(self, professor_id: int, questions: List[Dict]) -> Dict:
        """批量添加题目"""
        success_count = 0
        failed_count = 0
        results = []
        
        for question in questions:
            result = self.add_question(
                professor_id=professor_id,
                subject=question['subject'],
                question_content=question['question_content'],
                correct_answer=question['correct_answer'],
                topic=question.get('topic', ''),
                difficulty_level=question.get('difficulty_level', 'medium'),
                question_type=question.get('question_type', 'choice'),
                options=question.get('options', []),
                explanation=question.get('explanation', ''),
                source=question.get('source', ''),
                tags=question.get('tags', [])
            )
            results.append(result)
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'total': len(questions),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }
    
    def get_questions(self, professor_id: int, subject: str = "", topic: str = "",
                     difficulty_level: str = "", question_type: str = "") -> List[Dict]:
        """获取题库题目列表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT id, subject, topic, difficulty_level, question_type,
                           question_content, options, correct_answer, explanation,
                           source, tags, usage_count, status, created_at
                    FROM professor_question_bank
                    WHERE professor_id = ? AND status = 'active'
                '''
                params = [professor_id]
                
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if topic:
                    query += ' AND topic = ?'
                    params.append(topic)
                if difficulty_level:
                    query += ' AND difficulty_level = ?'
                    params.append(difficulty_level)
                if question_type:
                    query += ' AND question_type = ?'
                    params.append(question_type)
                
                query += ' ORDER BY created_at DESC'
                
                cursor.execute(query, params)
                
                return [{
                    'id': row[0],
                    'subject': row[1],
                    'topic': row[2],
                    'difficulty_level': row[3],
                    'question_type': row[4],
                    'question_content': row[5],
                    'options': json.loads(row[6]) if row[6] else [],
                    'correct_answer': row[7],
                    'explanation': row[8],
                    'source': row[9],
                    'tags': json.loads(row[10]) if row[10] else [],
                    'usage_count': row[11],
                    'status': row[12],
                    'created_at': row[13]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取题目失败: {e}")
            return []
    
    def update_question(self, question_id: int, **kwargs) -> Dict:
        """更新题目"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                set_clause = []
                params = []
                
                for key, value in kwargs.items():
                    if key in ['subject', 'topic', 'difficulty_level', 'question_type',
                               'question_content', 'correct_answer', 'explanation', 'source', 'status']:
                        set_clause.append(f"{key} = ?")
                        params.append(value)
                    elif key == 'options':
                        set_clause.append("options = ?")
                        params.append(json.dumps(value))
                    elif key == 'tags':
                        set_clause.append("tags = ?")
                        params.append(json.dumps(value))
                
                if not set_clause:
                    return {'success': False, 'message': '没有要更新的字段'}
                
                params.append(question_id)
                query = f"UPDATE professor_question_bank SET {', '.join(set_clause)} WHERE id = ?"
                
                cursor.execute(query, params)
                conn.commit()
                
                return {'success': True, 'message': '题目已更新'}
        except Exception as e:
            return {'success': False, 'message': f"更新题目失败: {str(e)}"}
    
    def delete_question(self, question_id: int) -> Dict:
        """删除题目"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE professor_question_bank SET status = "deleted" WHERE id = ?',
                             (question_id,))
                conn.commit()
                
                return {'success': True, 'message': '题目已删除'}
        except Exception as e:
            return {'success': False, 'message': f"删除题目失败: {str(e)}"}
    
    def get_question_bank_summary(self, professor_id: int) -> Dict:
        """获取题库统计摘要"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT subject, difficulty_level, COUNT(*) as count
                    FROM professor_question_bank
                    WHERE professor_id = ? AND status = 'active'
                    GROUP BY subject, difficulty_level
                ''', (professor_id,))
                
                summary = {}
                total = 0
                for row in cursor.fetchall():
                    subject = row[0]
                    difficulty = row[1]
                    count = row[2]
                    
                    if subject not in summary:
                        summary[subject] = {'total': 0, 'by_difficulty': {}}
                    summary[subject]['by_difficulty'][difficulty] = count
                    summary[subject]['total'] += count
                    total += count
                
                return {
                    'total_questions': total,
                    'by_subject': summary
                }
        except Exception as e:
            print(f"获取题库统计失败: {e}")
            return {'total_questions': 0, 'by_subject': {}}
    
    def generate_professional_questions(self, professor_id: int, subject: str, count: int,
                                       difficulty_level: str = "medium") -> List[Dict]:
        """生成专业领域题目"""
        generated = []
        
        question_templates = {
            '数学': [
                {'template': '已知函数 f(x) = {a}x² + {b}x + {c},求 f({x}) 的值.',
                 'answer': lambda a, b, c, x: a*x*x + b*x + c, 'type': 'calculation'},
                {'template': '解方程:{a}x + {b} = {c}',
                 'answer': lambda a, b, c: (c - b) / a if a != 0 else 0, 'type': 'equation'},
                {'template': '计算:{a} × {b} + {c} = ?',
                 'answer': lambda a, b, c: a * b + c, 'type': 'arithmetic'},
                {'template': '求:{a}² + {b}² = ?',
                 'answer': lambda a, b: a*a + b*b, 'type': 'square_sum'},
            ],
            '物理': [
                {'template': '一个物体从高度{h}米处自由下落,落地时的速度是多少?(g={g}m/s²)',
                 'answer': lambda h, g: (2*g*h)**0.5, 'type': 'mechanics'},
                {'template': '电阻{R1}Ω和{R2}Ω串联,总电阻是多少?',
                 'answer': lambda R1, R2: R1 + R2, 'type': 'electricity'},
                {'template': '质量为{m}kg的物体受到{F}N的力,加速度是多少?',
                 'answer': lambda m, F: F / m, 'type': 'newton'},
            ],
            '化学': [
                {'template': '计算{mol}摩尔的物质质量.(摩尔质量={mw}g/mol)',
                 'answer': lambda mol, mw: mol * mw, 'type': 'stoichiometry'},
                {'template': 'pH={ph}的溶液中,H+浓度是多少?',
                 'answer': lambda ph: 10**(-ph), 'type': 'acid-base'},
            ],
            '计算机': [
                {'template': '时间复杂度为O({complexity})的算法,处理{n}个元素的时间复杂度是?',
                 'answer': lambda complexity, n: f'O({complexity})', 'type': 'algorithm'},
                {'template': '二进制{bin}转换为十进制是多少?',
                 'answer': lambda bin_str: int(bin_str, 2), 'type': 'conversion'},
            ],
            '英语': [
                {'template': '"{word}"的中文意思是?',
                 'answer': lambda word: f"'{word}'的中文释义", 'type': 'vocabulary'},
                {'template': '选择正确的时态:He {verb} to school every day.',
                 'answer': lambda verb: 'goes', 'type': 'grammar'},
            ],
            '语文': [
                {'template': '"{poem}"出自哪位诗人?',
                 'answer': lambda poem: '著名诗人', 'type': 'literature'},
                {'template': '"{idiom}"的含义是?',
                 'answer': lambda idiom: f'"{idiom}"的释义', 'type': 'idiom'},
            ],
        }
        
        templates = question_templates.get(subject, question_templates['数学'])
        
        for _ in range(count):
            import random
            template = random.choice(templates)
            template_type = template['type']
            
            if subject == '数学':
                if template_type == 'calculation':
                    a, b, c, x = random.randint(1, 10), random.randint(1, 20), random.randint(1, 10), random.randint(1, 10)
                    content = template['template'].format(a=a, b=b, c=c, x=x)
                    answer = str(template['answer'](a, b, c, x))
                elif template_type == 'equation':
                    a, b, c = random.randint(1, 10), random.randint(1, 20), random.randint(1, 100)
                    content = template['template'].format(a=a, b=b, c=c)
                    answer = str(int(template['answer'](a, b, c)))
                elif template_type == 'arithmetic':
                    a, b, c = random.randint(1, 50), random.randint(1, 20), random.randint(1, 100)
                    content = template['template'].format(a=a, b=b, c=c)
                    answer = str(template['answer'](a, b, c))
                elif template_type == 'square_sum':
                    a, b = random.randint(1, 20), random.randint(1, 20)
                    content = template['template'].format(a=a, b=b)
                    answer = str(template['answer'](a, b))
                else:
                    content = f"数学综合题示例"
                    answer = "答案"
            elif subject == '物理':
                if template_type == 'mechanics':
                    h, g = random.randint(10, 100), 9.8
                    content = template['template'].format(h=h, g=g)
                    answer = str(round(template['answer'](h, g), 2))
                elif template_type == 'electricity':
                    R1, R2 = random.randint(10, 100), random.randint(10, 100)
                    content = template['template'].format(R1=R1, R2=R2)
                    answer = str(template['answer'](R1, R2))
                elif template_type == 'newton':
                    m, F = random.randint(1, 10), random.randint(10, 100)
                    content = template['template'].format(m=m, F=F)
                    answer = str(round(template['answer'](m, F), 2))
                else:
                    content = f"物理综合题示例"
                    answer = "答案"
            elif subject == '化学':
                if template_type == 'stoichiometry':
                    mol, mw = random.randint(1, 10), random.randint(20, 200)
                    content = template['template'].format(mol=mol, mw=mw)
                    answer = str(template['answer'](mol, mw))
                elif template_type == 'acid-base':
                    ph = random.randint(1, 13)
                    content = template['template'].format(ph=ph)
                    answer = str(template['answer'](ph))
                else:
                    content = f"化学综合题示例"
                    answer = "答案"
            elif subject == '计算机':
                if template_type == 'algorithm':
                    complexity = random.choice(['n', 'n²', 'log n', 'n log n'])
                    n = random.randint(100, 1000)
                    content = template['template'].format(complexity=complexity, n=n)
                    answer = template['answer'](complexity, n)
                elif template_type == 'conversion':
                    bin_str = bin(random.randint(1, 255))[2:]
                    content = template['template'].format(bin=bin_str)
                    answer = str(template['answer'](bin_str))
                else:
                    content = f"计算机综合题示例"
                    answer = "答案"
            else:
                content = f"{subject}专业题目示例"
                answer = "答案"
            
            options = [answer, "错误选项A", "错误选项B", "错误选项C"]
            random.shuffle(options)
            
            generated.append({
                'subject': subject,
                'topic': f"{subject}基础",
                'difficulty_level': difficulty_level,
                'question_type': 'choice',
                'question_content': content,
                'options': options,
                'correct_answer': answer,
                'explanation': f"{content}的解析",
                'tags': [subject, difficulty_level, 'auto-generated']
            })
        
        return generated
    
    def expand_question_bank(self, professor_id: int, subject: str, count: int,
                            difficulty_level: str = "medium") -> Dict:
        """扩充题库"""
        questions = self.generate_professional_questions(professor_id, subject, count, difficulty_level)
        return self.batch_add_questions(professor_id, questions)
    
    def get_professor_profile(self, professor_id: int) -> Dict:
        """获取教授完整资料"""
        research = self.get_research_list(professor_id)
        publications = self.get_publications(professor_id)
        projects = self.get_projects(professor_id)
        advising = self.get_advising_students(professor_id)
        awards = self.get_awards(professor_id)
        
        total_citations = sum(p['citations'] for p in publications)
        total_funding = sum(p['funding_amount'] for p in projects)
        
        return {
            'professor_id': professor_id,
            'research_count': len(research),
            'publication_count': len(publications),
            'total_citations': total_citations,
            'project_count': len(projects),
            'total_funding': total_funding,
            'advising_count': len(advising),
            'award_count': len(awards),
            'research': research[:3],
            'publications': publications[:3],
            'projects': projects[:2],
            'awards': awards[:3]
        }
    
    def generate_research_summary(self, professor_id: int) -> Dict:
        """生成研究总结报告"""
        profile = self.get_professor_profile(professor_id)
        
        summary = {
            'professor_id': professor_id,
            'summary': f"教授目前正在进行{profile['research_count']}项研究,发表{profile['publication_count']}篇论文,引用次数达{profile['total_citations']}次.",
            'highlights': [],
            'suggestions': [],
            'generated_at': datetime.now().isoformat()
        }
        
        if profile['total_citations'] > 100:
            summary['highlights'].append("学术影响力较高,论文引用次数超过100次")
        if profile['project_count'] > 5:
            summary['highlights'].append("主持多项科研项目,研究活跃度高")
        if profile['award_count'] > 3:
            summary['highlights'].append("获得多项学术奖项,学术成就显著")
        
        if profile['publication_count'] < 5:
            summary['suggestions'].append("建议增加学术论文发表数量")
        if profile['advising_count'] < 3:
            summary['suggestions'].append("建议指导更多研究生")
        
        return summary
    
    def initialize_sample_data(self, professor_id: int = 1):
        """初始化示例数据"""
        self.add_research(professor_id, "人工智能教育应用研究", "教育技术",
                         "研究AI在教育领域的创新应用", "2024-01-01")
        self.add_research(professor_id, "机器学习算法优化", "计算机科学",
                         "深度学习算法性能优化研究", "2024-06-01")
        
        self.add_publication(professor_id, "AI-Powered Learning Analytics", 
                           "Journal of Educational Technology", 2024, 
                           "Zhang Wei et al.", 45, "10.1234/jet.2024.1234")
        self.add_publication(professor_id, "Deep Learning for Intelligent Tutoring",
                           "IEEE Transactions on Education", 2023,
                           "Zhang Wei, Li Ming", 89, "10.5678/ieee.2023.5678")
        
        self.add_project(professor_id, "智能教育系统研发", "国家级",
                        "国家自然科学基金", 5000000.0, "2024-01-01", "2027-12-31")
        self.add_project(professor_id, "个性化学习推荐系统", "省部级",
                        "省教育厅", 1000000.0, "2024-06-01", "2026-05-31")
        
        self.add_advising(professor_id, 2021001, "李明", "博士",
                         "基于AI的学习路径规划研究", "2021-09-01", "2025-06-30")
        self.add_advising(professor_id, 2022001, "王芳", "硕士",
                         "智能答疑系统设计", "2022-09-01", "2025-03-31")
        
        self.add_award(professor_id, "优秀教学成果一等奖", "教育部", 2023,
                      "智能教育系统开发与应用")
        self.add_award(professor_id, "学术论文优秀奖", "省教育学会", 2024,
                      "AI教育应用研究系列论文")
        
        self.add_delegation(professor_id, 101, "张老师", "数学", "高一", "teaching",
                           "负责高一数学教学、备课、批改作业", "2024-09-01", "2025-06-30")
        self.add_delegation(professor_id, 102, "李老师", "物理", "高二", "teaching",
                           "负责高二物理教学、实验指导", "2024-09-01", "2025-06-30")
        self.add_delegation(professor_id, 103, "王老师", "化学", "高三", "teaching",
                           "负责高三化学教学、高考备考指导", "2024-09-01", "2025-06-30")
        self.add_delegation(professor_id, 104, "赵老师", "计算机", "高一", "teaching",
                           "负责高一信息技术教学", "2024-09-01", "2025-06-30")
        
        self.create_evaluation(professor_id, 101, "张老师", "讲师", "副教授", "promotion",
                              {"教学能力": 90, "科研成果": 85, "师德师风": 95, "学生评价": 88, "教学改革": 82}, "王教授")
        self.create_evaluation(professor_id, 102, "李老师", "助教", "讲师", "promotion",
                              {"教学能力": 85, "科研成果": 75, "师德师风": 90, "学生评价": 82, "教学改革": 78}, "王教授")
        self.create_evaluation(professor_id, 103, "王老师", "副教授", "教授", "promotion",
                              {"教学能力": 92, "科研成果": 95, "师德师风": 98, "学生评价": 90, "教学改革": 93}, "王教授")
        
        self.add_qualification(101, "张老师", 2, "", "数学", ["物理"], 6, "2018-09-01")
        self.add_qualification(102, "李老师", 1, "", "物理", ["数学"], 3, "2021-09-01")
        self.add_qualification(103, "王老师", 4, "", "化学", ["生物"], 12, "2012-09-01")
        self.add_qualification(104, "赵老师", 1, "", "计算机", [], 2, "2022-09-01")

if __name__ == "__main__":
    prof_system = ProfessorSystem()
    
    print("=== 教授系统测试 ===\n")
    
    prof_system.initialize_sample_data()
    print("✓ 示例数据初始化完成")
    
    profile = prof_system.get_professor_profile(1)
    print(f"\n教授资料概览:")
    print(f"  研究项目: {profile['research_count']}项")
    print(f"  学术论文: {profile['publication_count']}篇")
    print(f"  总引用数: {profile['total_citations']}次")
    print(f"  科研项目: {profile['project_count']}项")
    print(f"  科研经费: {profile['total_funding']:,.0f}元")
    print(f"  指导学生: {profile['advising_count']}人")
    print(f"  获得奖项: {profile['award_count']}项")
    
    delegation_summary = prof_system.get_delegation_summary(1)
    print(f"\n教师委派统计:")
    print(f"  总委派数: {delegation_summary['total_delegations']}")
    print(f"  活跃委派: {delegation_summary['active_delegations']}")
    print(f"  按科目分布: {delegation_summary['by_subject']}")
    
    delegations = prof_system.get_delegations(1)
    print(f"\n教师委派列表:")
    for d in delegations:
        print(f"  - {d['teacher_name']}: {d['subject']} ({d['grade_level']}) - {d['status']}")
    
    evaluation_summary = prof_system.get_evaluation_summary(1)
    print(f"\n职称测评统计:")
    print(f"  总测评数: {evaluation_summary['total_evaluations']}")
    print(f"  平均分: {evaluation_summary['average_score']:.1f}")
    print(f"  测评结果分布: {evaluation_summary['by_result']}")
    
    evaluations = prof_system.get_evaluations(1)
    print(f"\n职称测评列表:")
    for e in evaluations:
        print(f"  - {e['teacher_name']}: {e['current_title']} → {e['target_title']} ({e['total_score']}分) - {e['evaluation_result']}")
    
    report = prof_system.generate_evaluation_report(103)
    print(f"\n王老师职称测评报告:")
    print(f"  当前职称: {report['current_title']}")
    print(f"  目标职称: {report['target_title']}")
    print(f"  最近得分: {report['recent_score']}")
    print(f"  平均得分: {report['average_score']:.1f}")
    print(f"  测评结果: {report['recent_result']}")
    print(f"  建议: {report['suggestion']}")
    
    qual_summary = prof_system.get_qualification_summary(1)
    print(f"\n教师资格统计:")
    print(f"  教师总数: {qual_summary['total_teachers']}")
    print(f"  级别分布: {qual_summary['by_level']}")
    
    qual = prof_system.get_qualification(101)
    print(f"\n张老师资格信息:")
    print(f"  级别: {qual['level']} - {qual['name']}")
    print(f"  主科: {qual['major_subject']}")
    print(f"  副科: {qual['minor_subjects']}")
    print(f"  教龄: {qual['experience_years']}年")
    
    upgrade_check = prof_system.check_upgrade_requirements(101, 3)
    print(f"\n张老师升级到高级教师检查:")
    print(f"  符合条件: {'是' if upgrade_check['eligible'] else '否'}")
    if upgrade_check['requirements_not_met']:
        print(f"  未满足要求:")
        for req in upgrade_check['requirements_not_met']:
            print(f"    ✗ {req['description']}")
    
    upgrade_result = prof_system.upgrade_qualification(1, 101, "张老师", 3)
    print(f"\n张老师资格升级结果:")
    print(f"  成功: {'是' if upgrade_result['success'] else '否'}")
    if upgrade_result['success']:
        print(f"  {upgrade_result['message']}")
    
    new_qual = prof_system.get_qualification(101)
    print(f"\n张老师更新后资格:")
    print(f"  级别: {new_qual['level']} - {new_qual['name']}")
    
    history = prof_system.get_upgrade_history(101)
    print(f"\n张老师升级历史:")
    for h in history:
        print(f"  - {h['upgrade_date']}: {h['from_name']} → {h['to_name']}")
    
    qb_summary = prof_system.get_question_bank_summary(1)
    print(f"\n题库统计:")
    print(f"  总题目数: {qb_summary['total_questions']}")
    for subject, data in qb_summary['by_subject'].items():
        print(f"  - {subject}: {data['total']}题")
        if data['by_difficulty']:
            for diff, cnt in data['by_difficulty'].items():
                print(f"      {diff}: {cnt}题")
    
    expand_result = prof_system.expand_question_bank(1, "数学", 10, "hard")
    print(f"\n扩充数学题库结果:")
    print(f"  成功: {expand_result['success']}题")
    print(f"  失败: {expand_result['failed']}题")
    
    qb_summary = prof_system.get_question_bank_summary(1)
    print(f"\n更新后题库统计:")
    print(f"  总题目数: {qb_summary['total_questions']}")
    
    questions = prof_system.get_questions(1, subject="数学", difficulty_level="hard")
    print(f"\n数学难题列表 ({len(questions)}题):")
    for q in questions[:3]:
        print(f"  - {q['question_content'][:50]}...")
        print(f"    答案: {q['correct_answer']}")
    
    add_result = prof_system.add_question(
        professor_id=1,
        subject="物理",
        question_content="一个物体从高度50米处自由下落,落地时的速度是多少?(g=9.8m/s²)",
        correct_answer="31.3",
        topic="力学",
        difficulty_level="medium",
        options=["31.3", "25.6", "45.2", "28.7"],
        explanation="根据自由落体公式 v = sqrt(2gh) = sqrt(2*9.8*50) ≈ 31.3m/s",
        tags=["力学", "自由落体"]
    )
    print(f"\n添加题目结果: {'成功' if add_result['success'] else '失败'}")
    
    summary = prof_system.generate_research_summary(1)
    print(f"\n研究总结:")
    print(f"  {summary['summary']}")
    if summary['highlights']:
        print("\n  亮点:")
        for highlight in summary['highlights']:
            print(f"    ✓ {highlight}")
    if summary['suggestions']:
        print("\n  建议:")
        for suggestion in summary['suggestions']:
            print(f"    💡 {suggestion}")
    
    logger.info("\n=== 测试完成 ===")
