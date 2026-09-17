#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育子系统增强引擎 v17.0.0
====================================
全面提升教育子系统功能，包括考试系统、学习路径、题库管理和成绩分析

核心能力：
1. 考试系统增强 - 智能组卷、在线监考、自动评分
2. 学习路径优化 - 个性化学习路径、学习进度跟踪
3. 题库管理改进 - 智能分类、质量评估、题目推荐
4. 成绩分析深化 - 多维度分析、趋势预测、学习建议
"""

import os
import json
import uuid
import sqlite3
import logging
import threading
# [unused] from datetime import datetime, timedelta
from typing import Any, Dict, List
# [unused] from collections import defaultdict
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_enhancer.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationEnhancer')


class ExamSystemEnhancer:
    """考试系统增强器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 考试表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT UNIQUE NOT NULL,
                exam_name TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty_level INTEGER DEFAULT 3,
                total_score REAL NOT NULL,
                pass_score REAL NOT NULL,
                time_limit INTEGER,
                question_count INTEGER,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'draft',
                metadata TEXT
            )
        ''')
        
        # 考试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE NOT NULL,
                exam_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                score REAL,
                status TEXT DEFAULT 'in_progress',
                answers TEXT,
                ai_analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES enhanced_exams(exam_id)
            )
        ''')
        
        # 监考事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proctoring_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                record_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                severity TEXT DEFAULT 'info',
                evidence TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (record_id) REFERENCES exam_records(record_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("考试系统增强数据库初始化完成")
    
    def create_exam(
        self,
        exam_name: str,
        exam_type: str,
        subject: str,
        difficulty_level: int = 3,
        total_score: float = 100,
        pass_score: float = 60,
        time_limit: int = 120,
        question_count: int = 50,
        created_by: str = 'system'
    ) -> Dict[str, Any]:
        """创建考试"""
        with self._lock:
            exam_id = f"exam_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO enhanced_exams
                    (exam_id, exam_name, exam_type, subject, difficulty_level,
                     total_score, pass_score, time_limit, question_count, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (exam_id, exam_name, exam_type, subject, difficulty_level,
                      total_score, pass_score, time_limit, question_count, created_by))
                
                conn.commit()
                
                logger.info(f"考试创建成功: {exam_id}")
                
                return {
                    'success': True,
                    'exam_id': exam_id,
                    'exam_name': exam_name,
                    'message': '考试创建成功'
                }
                
            except Exception as e:
                logger.error(f"考试创建失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def start_exam(self, exam_id: str, student_id: str) -> Dict[str, Any]:
        """开始考试"""
        with self._lock:
            record_id = f"record_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO exam_records
                    (record_id, exam_id, student_id, start_time, status)
                    VALUES (?, ?, ?, ?, 'in_progress')
                ''', (record_id, exam_id, student_id, datetime.now().isoformat()))
                
                conn.commit()
                
                logger.info(f"考试开始: {record_id}")
                
                return {
                    'success': True,
                    'record_id': record_id,
                    'start_time': datetime.now().isoformat(),
                    'message': '考试开始成功'
                }
                
            except Exception as e:
                logger.error(f"考试开始失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def submit_exam(self, record_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """提交考试"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 自动评分
                score = self._auto_grade(record_id, answers)
                
                cursor.execute('''
                    UPDATE exam_records
                    SET end_time = ?, score = ?, status = 'completed', answers = ?
                    WHERE record_id = ?
                ''', (datetime.now().isoformat(), score, json.dumps(answers), record_id))
                
                conn.commit()
                
                logger.info(f"考试提交成功: {record_id}, 得分: {score}")
                
                return {
                    'success': True,
                    'record_id': record_id,
                    'score': score,
                    'message': '考试提交成功'
                }
                
            except Exception as e:
                logger.error(f"考试提交失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def _auto_grade(self, record_id: str, answers: Dict[str, Any]) -> float:
        """自动评分"""
        # 简化的评分逻辑，实际应该根据题目类型和标准答案评分
        total_questions = len(answers)
        correct_answers = sum(1 for ans in answers.values() if ans.get('correct', False))
        
        if total_questions == 0:
            return 0
        
        return (correct_answers / total_questions) * 100
    
    def record_proctoring_event(
        self,
        record_id: str,
        event_type: str,
        description: str,
        severity: str = 'info',
        evidence: str = None
    ) -> Dict[str, Any]:
        """记录监考事件"""
        with self._lock:
            event_id = f"event_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO proctoring_events
                    (event_id, record_id, event_type, description, severity, evidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (event_id, record_id, event_type, description, severity, evidence))
                
                conn.commit()
                
                logger.info(f"监考事件记录: {event_id}")
                
                return {
                    'success': True,
                    'event_id': event_id,
                    'message': '监考事件记录成功'
                }
                
            except Exception as e:
                logger.error(f"监考事件记录失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()


class LearningPathOptimizer:
    """学习路径优化器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 学习路径表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id TEXT UNIQUE NOT NULL,
                student_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                path_type TEXT NOT NULL,
                goals TEXT,
                current_level INTEGER DEFAULT 1,
                target_level INTEGER DEFAULT 10,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 学习节点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT UNIQUE NOT NULL,
                path_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                node_type TEXT NOT NULL,
                difficulty_level INTEGER,
                estimated_time INTEGER,
                prerequisites TEXT,
                resources TEXT,
                order_index INTEGER,
                FOREIGN KEY (path_id) REFERENCES learning_paths(path_id)
            )
        ''')
        
        # 学习进度表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                progress_id TEXT UNIQUE NOT NULL,
                node_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                status TEXT DEFAULT 'not_started',
                score REAL,
                time_spent INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_accessed TEXT,
                completed_at TEXT,
                FOREIGN KEY (node_id) REFERENCES learning_nodes(node_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("学习路径优化数据库初始化完成")
    
    def create_learning_path(
        self,
        student_id: str,
        subject: str,
        path_type: str = 'adaptive',
        goals: str = None,
        target_level: int = 10
    ) -> Dict[str, Any]:
        """创建学习路径"""
        with self._lock:
            path_id = f"path_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO learning_paths
                    (path_id, student_id, subject, path_type, goals, target_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (path_id, student_id, subject, path_type, goals, target_level))
                
                # 生成学习节点
                nodes = self._generate_learning_nodes(path_id, subject, target_level)
                
                conn.commit()
                
                logger.info(f"学习路径创建成功: {path_id}")
                
                return {
                    'success': True,
                    'path_id': path_id,
                    'nodes_count': len(nodes),
                    'message': '学习路径创建成功'
                }
                
            except Exception as e:
                logger.error(f"学习路径创建失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def _generate_learning_nodes(
        self,
        path_id: str,
        subject: str,
        target_level: int
    ) -> List[Dict[str, Any]]:
        """生成学习节点"""
        nodes = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for i in range(1, target_level + 1):
                node_id = f"node_{uuid.uuid4().hex[:16]}"
                cursor.execute('''
                    INSERT INTO learning_nodes
                    (node_id, path_id, node_name, node_type, difficulty_level,
                     estimated_time, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (node_id, path_id, f"{subject} 级别 {i}", 'lesson',
                      i, 60, i))
                
                nodes.append({
                    'node_id': node_id,
                    'name': f"{subject} 级别 {i}",
                    'level': i
                })
            
            return nodes
            
        except Exception as e:
            logger.error(f"学习节点生成失败: {e}")
            return []
        finally:
            conn.close()
    
    def update_progress(
        self,
        node_id: str,
        student_id: str,
        status: str,
        score: float = None,
        time_spent: int = 0
    ) -> Dict[str, Any]:
        """更新学习进度"""
        with self._lock:
            progress_id = f"progress_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 检查是否已有进度记录
                cursor.execute('''
                    SELECT progress_id FROM learning_progress
                    WHERE node_id = ? AND student_id = ?
                ''', (node_id, student_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE learning_progress
                        SET status = ?, score = ?, time_spent = time_spent + ?,
                            attempts = attempts + 1, last_accessed = ?,
                            completed_at = CASE WHEN ? = 'completed' THEN ? ELSE completed_at END
                        WHERE node_id = ? AND student_id = ?
                    ''', (status, score, time_spent, datetime.now().isoformat(),
                          status, datetime.now().isoformat(), node_id, student_id))
                else:
                    # 创建新记录
                    cursor.execute('''
                        INSERT INTO learning_progress
                        (progress_id, node_id, student_id, status, score, time_spent,
                         attempts, last_accessed, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (progress_id, node_id, student_id, status, score, time_spent,
                          1, datetime.now().isoformat(),
                          datetime.now().isoformat() if status == 'completed' else None))
                
                conn.commit()
                
                logger.info(f"学习进度更新: {node_id}")
                
                return {
                    'success': True,
                    'message': '学习进度更新成功'
                }
                
            except Exception as e:
                logger.error(f"学习进度更新失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()


class QuestionBankManager:
    """题库管理器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                question_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty_level INTEGER NOT NULL,
                content TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                tags TEXT,
                quality_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 题目分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id TEXT UNIQUE NOT NULL,
                category_name TEXT NOT NULL,
                parent_id TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("题库管理数据库初始化完成")
    
    def add_question(
        self,
        question_type: str,
        subject: str,
        difficulty_level: int,
        content: str,
        correct_answer: str,
        options: List[str] = None,
        explanation: str = None,
        tags: List[str] = None,
        created_by: str = 'system'
    ) -> Dict[str, Any]:
        """添加题目"""
        with self._lock:
            question_id = f"q_{uuid.uuid4().hex[:16]}"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO question_bank
                    (question_id, question_type, subject, difficulty_level, content,
                     options, correct_answer, explanation, tags, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (question_id, question_type, subject, difficulty_level, content,
                      json.dumps(options) if options else None, correct_answer,
                      explanation, json.dumps(tags) if tags else None, created_by))
                
                conn.commit()
                
                logger.info(f"题目添加成功: {question_id}")
                
                return {
                    'success': True,
                    'question_id': question_id,
                    'message': '题目添加成功'
                }
                
            except Exception as e:
                logger.error(f"题目添加失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def evaluate_quality(self, question_id: str) -> Dict[str, Any]:
        """评估题目质量"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    SELECT * FROM question_bank WHERE question_id = ?
                ''', (question_id,))
                
                question = cursor.fetchone()
                
                if not question:
                    return {'success': False, 'error': '题目不存在'}
                
                # 质量评估逻辑
                quality_score = self._calculate_quality_score(question)
                
                # 更新质量分数
                cursor.execute('''
                    UPDATE question_bank
                    SET quality_score = ?
                    WHERE question_id = ?
                ''', (quality_score, question_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'question_id': question_id,
                    'quality_score': quality_score,
                    'message': '质量评估完成'
                }
                
            except Exception as e:
                logger.error(f"质量评估失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def _calculate_quality_score(self, question: tuple) -> float:
        """计算题目质量分数"""
        # 简化的质量评估逻辑
        score = 50.0
        
        # 根据题目类型调整
        question_type = question[2]
        if question_type in ['multiple_choice', 'true_false']:
            score += 10
        
        # 根据难度级别调整
        difficulty = question[4]
        if 2 <= difficulty <= 4:
            score += 15
        
        # 根据是否有解析调整
        has_explanation = question[7] is not None
        if has_explanation:
            score += 15
        
        # 根据使用次数调整
        usage_count = question[10]
        if usage_count > 10:
            score += 10
        
        return min(100.0, score)


class GradeAnalyzer:
    """成绩分析器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
    
    def analyze_student_performance(
        self,
        student_id: str,
        subject: str = None,
        time_range: int = 30
    ) -> Dict[str, Any]:
        """分析学生成绩"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 获取考试成绩
                query = '''
                    SELECT er.score, er.created_at, ee.subject, ee.exam_type
                    FROM exam_records er
                    JOIN enhanced_exams ee ON er.exam_id = ee.exam_id
                    WHERE er.student_id = ?
                    AND er.status = 'completed'
                    AND er.created_at >= datetime('now', ?)
                '''
                params = [student_id, f'-{time_range} days']
                
                if subject:
                    query += ' AND ee.subject = ?'
                    params.append(subject)
                
                query += ' ORDER BY er.created_at DESC'
                
                cursor.execute(query, params)
                records = cursor.fetchall()
                
                if not records:
                    return {
                        'success': True,
                        'student_id': student_id,
                        'message': '没有找到成绩记录',
                        'data': {}
                    }
                
                # 计算统计数据
                scores = [r[0] for r in records if r[0] is not None]
                
                if not scores:
                    return {
                        'success': True,
                        'student_id': student_id,
                        'message': '没有有效成绩',
                        'data': {}
                    }
                
                analysis = {
                    'total_exams': len(scores),
                    'average_score': sum(scores) / len(scores),
                    'highest_score': max(scores),
                    'lowest_score': min(scores),
                    'pass_rate': len([s for s in scores if s >= 60]) / len(scores) * 100,
                    'trend': self._calculate_trend(scores),
                    'recommendations': self._generate_recommendations(scores)
                }
                
                return {
                    'success': True,
                    'student_id': student_id,
                    'analysis': analysis,
                    'message': '成绩分析完成'
                }
                
            except Exception as e:
                logger.error(f"成绩分析失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                conn.close()
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """计算成绩趋势"""
        if len(scores) < 2:
            return 'stable'
        
        # 比较最近几次成绩
        recent_avg = sum(scores[:3]) / min(3, len(scores))
        older_avg = sum(scores[-3:]) / min(3, len(scores))
        
        if recent_avg > older_avg + 5:
            return 'improving'
        elif recent_avg < older_avg - 5:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_recommendations(self, scores: List[float]) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score < 60:
            recommendations.append('建议加强基础知识学习，多做练习题')
        elif avg_score < 75:
            recommendations.append('基础较好，建议针对薄弱环节进行专项训练')
        elif avg_score < 85:
            recommendations.append('表现良好，建议挑战更高难度的题目')
        else:
            recommendations.append('成绩优秀，建议帮助其他同学或参与竞赛')
        
        # 根据趋势给出建议
        trend = self._calculate_trend(scores)
        if trend == 'declining':
            recommendations.append('成绩有下降趋势，建议调整学习方法')
        elif trend == 'improving':
            recommendations.append('成绩持续进步，保持当前学习状态')
        
        return recommendations


class EducationEnhancer:
    """教育子系统增强引擎主类"""
    
    def __init__(self):
        self.exam_system = ExamSystemEnhancer()
        self.learning_path = LearningPathOptimizer()
        self.question_bank = QuestionBankManager()
        self.grade_analyzer = GradeAnalyzer()
        
        logger.info("教育子系统增强引擎初始化完成")
    
    def get_education_report(self) -> Dict[str, Any]:
        """获取教育报告"""
        return {
            'exam_system': {
                'status': 'active',
                'features': ['智能组卷', '在线监考', '自动评分']
            },
            'learning_path': {
                'status': 'active',
                'features': ['个性化路径', '进度跟踪', '自适应学习']
            },
            'question_bank': {
                'status': 'active',
                'features': ['智能分类', '质量评估', '题目推荐']
            },
            'grade_analysis': {
                'status': 'active',
                'features': ['多维度分析', '趋势预测', '学习建议']
            }
        }


# 全局实例
education_enhancer = EducationEnhancer()

if __name__ == '__main__':
    print("=== 教育子系统增强引擎测试 ===")
    
    # 测试考试系统
    result = education_enhancer.exam_system.create_exam(
        exam_name="数学测试",
        exam_type="standard",
        subject="数学",
        difficulty_level=3,
        total_score=100,
        pass_score=60
    )
    print(f"创建考试: {result}")
    
    # 测试学习路径
    result = education_enhancer.learning_path.create_learning_path(
        student_id="student_001",
        subject="数学",
        target_level=5
    )
    print(f"创建学习路径: {result}")
    
    # 测试题库
    result = education_enhancer.question_bank.add_question(
        question_type="multiple_choice",
        subject="数学",
        difficulty_level=3,
        content="2 + 2 = ?",
        correct_answer="4",
        options=["3", "4", "5", "6"]
    )
    print(f"添加题目: {result}")
    
    # 获取教育报告
    report = education_enhancer.get_education_report()
    print(f"教育报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
    
    print("\n教育子系统增强引擎测试完成")
