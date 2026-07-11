# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
摸底测试服务模块
负责评估用户知识水平,生成个性化学习路径
"""

import sqlite3
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

class PlacementTestService:
    """摸底测试服务类"""
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
    
    def _connect(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)
    
    def create_placement_test(self, user_id: int, subject: str = None) -> Dict:
        """创建摸底测试
        
        Args:
            user_id: 用户ID
            subject: 学科(可选,为空则综合测试)
        
        Returns:
            测试信息
        """
        test_id = self._generate_test_id()
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO placement_tests 
                (id, user_id, subject, status, created_at, estimated_duration)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (test_id, user_id, subject or '综合', 'created', datetime.now(), 30))
            
            conn.commit()
        
        questions = self._generate_placement_questions(user_id, subject)
        
        # 质量保证:去重、验证选项、确保干扰项质量
        questions = self._ensure_question_quality(questions)
        
        self._save_test_questions(test_id, questions)
        
        return {
            'test_id': test_id,
            'user_id': user_id,
            'subject': subject or '综合',
            'status': 'created',
            'estimated_duration': 30,
            'question_count': len(questions),
            'created_at': datetime.now().isoformat()
        }
    
    def _ensure_question_quality(self, questions: List[Dict]) -> List[Dict]:
        """
        确保题目质量:
        1. 移除重复题目
        2. 验证选项(移除重复选项)
        3. 确保干扰项具有混淆性
        """
        try:
            from app.services.question_quality_service import get_question_quality_service
            quality_service = get_question_quality_service()
            result = quality_service.validate_question_quality(questions)
            return result['validated_questions']
        except Exception as e:
            import logging
            logging.error(f"题目质量验证失败: {e}")
            # 如果验证失败,返回原始题目
            return questions
    
    def _generate_test_id(self) -> str:
        """生成唯一测试ID"""
        return f"PT_{int(time.time())}_{random.randint(1000, 9999)}"
    
    def _generate_placement_questions(self, user_id: int, subject: str = None) -> List[Dict]:
        """生成摸底测试题目"""
        questions = []
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            if subject:
                # 根据tags搜索包含该学科的题目
                cursor.execute('''
                    SELECT id, type, content, options, correct_answer, difficulty, points, tags, audio_url
                    FROM questions
                    WHERE tags LIKE ?
                    ORDER BY RANDOM()
                    LIMIT 20
                ''', (f'%{subject}%',))
            else:
                cursor.execute('''
                    SELECT id, type, content, options, correct_answer, difficulty, points, tags, audio_url
                    FROM questions
                    ORDER BY RANDOM()
                    LIMIT 30
                ''')
            
            for row in cursor.fetchall():
                # 从tags中解析学科分类
                tags = json.loads(row[7])
                category = tags[0] if tags else '综合'
                
                questions.append({
                    'question_id': row[0],
                    'question_type': row[1],
                    'question_text': row[2],
                    'options': json.loads(row[3]),
                    'correct_answer': row[4],
                    'difficulty': row[5],
                    'points': row[6],
                    'category': category,
                    'tags': tags,
                    'audio_url': row[8]
                })
        
        return questions
    
    def _save_test_questions(self, test_id: str, questions: List[Dict]):
        """保存测试题目"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 先检查表结构是否包含新增字段
            cursor.execute("PRAGMA table_info(placement_test_questions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'question_type' in columns and 'tags' in columns and 'audio_url' in columns:
                for idx, q in enumerate(questions):
                    cursor.execute('''
                        INSERT INTO placement_test_questions
                        (test_id, question_id, question_type, question_text, options, correct_answer, 
                         difficulty, points, category, order_index, tags, audio_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_id, q['question_id'], q['question_type'], q['question_text'], 
                        json.dumps(q['options']), q['correct_answer'],
                        q['difficulty'], q['points'], q['category'], idx + 1,
                        json.dumps(q['tags']), q['audio_url']
                    ))
            else:
                # 向后兼容
                for idx, q in enumerate(questions):
                    cursor.execute('''
                        INSERT INTO placement_test_questions
                        (test_id, question_id, question_text, options, correct_answer, 
                         difficulty, points, category, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_id, q['question_id'], q['question_text'], 
                        json.dumps(q['options']), q['correct_answer'],
                        q['difficulty'], q['points'], q['category'], idx + 1
                    ))
            
            conn.commit()
    
    def get_placement_test(self, test_id: str) -> Optional[Dict]:
        """获取摸底测试信息"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, subject, status, created_at, started_at, completed_at, 
                       estimated_duration, actual_duration
                FROM placement_tests
                WHERE id = ?
            ''', (test_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 检查表结构是否有新增字段
            cursor.execute("PRAGMA table_info(placement_test_questions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'question_type' in columns and 'tags' in columns and 'audio_url' in columns:
                cursor.execute('''
                    SELECT question_id, question_type, question_text, options, correct_answer, 
                           difficulty, points, category, order_index, user_answer, is_correct, tags, audio_url
                    FROM placement_test_questions
                    WHERE test_id = ?
                    ORDER BY order_index
                ''', (test_id,))
                
                questions = []
                for q_row in cursor.fetchall():
                    tags = json.loads(q_row[11]) if q_row[11] else []
                    questions.append({
                        'question_id': q_row[0],
                        'question_type': q_row[1],
                        'question_text': q_row[2],
                        'options': json.loads(q_row[3]),
                        'correct_answer': q_row[4],
                        'difficulty': q_row[5],
                        'points': q_row[6],
                        'category': q_row[7],
                        'order_index': q_row[8],
                        'user_answer': q_row[9],
                        'is_correct': q_row[10],
                        'tags': tags,
                        'audio_url': q_row[12]
                    })
            else:
                # 向后兼容
                cursor.execute('''
                    SELECT question_id, question_text, options, correct_answer, 
                           difficulty, points, category, order_index, user_answer, is_correct
                    FROM placement_test_questions
                    WHERE test_id = ?
                    ORDER BY order_index
                ''', (test_id,))
                
                questions = []
                for q_row in cursor.fetchall():
                    questions.append({
                        'question_id': q_row[0],
                        'question_text': q_row[1],
                        'options': json.loads(q_row[2]),
                        'correct_answer': q_row[3],
                        'difficulty': q_row[4],
                        'points': q_row[5],
                        'category': q_row[6],
                        'order_index': q_row[7],
                        'user_answer': q_row[8],
                        'is_correct': q_row[9],
                        'question_type': 'single_choice',
                        'tags': [],
                        'audio_url': ''
                    })
            
            return {
                'test_id': row[0],
                'user_id': row[1],
                'subject': row[2],
                'status': row[3],
                'created_at': row[4],
                'started_at': row[5],
                'completed_at': row[6],
                'estimated_duration': row[7],
                'actual_duration': row[8],
                'questions': questions
            }
    
    def start_test(self, test_id: str) -> bool:
        """开始测试"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE placement_tests
                SET status = ?, started_at = ?
                WHERE id = ? AND status = ?
            ''', ('in_progress', datetime.now(), test_id, 'created'))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def submit_answer(self, test_id: str, question_id: int, user_answer: str) -> bool:
        """提交答案"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT correct_answer FROM placement_test_questions
                WHERE test_id = ? AND question_id = ?
            ''', (test_id, question_id))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            is_correct = (user_answer == row[0])
            
            cursor.execute('''
                UPDATE placement_test_questions
                SET user_answer = ?, is_correct = ?, answered_at = ?
                WHERE test_id = ? AND question_id = ?
            ''', (user_answer, is_correct, datetime.now(), test_id, question_id))
            
            conn.commit()
            return True
    
    def complete_test(self, test_id: str) -> Dict:
        """完成测试并生成评估报告"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE placement_tests
                SET status = ?, completed_at = ?
                WHERE id = ? AND status = ?
            ''', ('completed', datetime.now(), test_id, 'in_progress'))
            
            conn.commit()
        
        return self.generate_placement_report(test_id)
    
    def generate_placement_report(self, test_id: str) -> Dict:
        """生成摸底测试报告"""
        test = self.get_placement_test(test_id)
        if not test or test['status'] != 'completed':
            return {}
        
        questions = test['questions']
        total_questions = len(questions)
        correct_count = sum(1 for q in questions if q['is_correct'])
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        
        # 按学科统计
        category_stats = {}
        for q in questions:
            cat = q['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'correct': 0}
            category_stats[cat]['total'] += 1
            if q['is_correct']:
                category_stats[cat]['correct'] += 1
        
        # 按难度统计
        difficulty_stats = {}
        for q in questions:
            diff = q['difficulty']
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {'total': 0, 'correct': 0}
            difficulty_stats[diff]['total'] += 1
            if q['is_correct']:
                difficulty_stats[diff]['correct'] += 1
        
        # 计算综合水平
        level = self._calculate_level(accuracy, difficulty_stats)
        
        # 生成建议
        suggestions = self._generate_suggestions(category_stats, difficulty_stats)
        
        report = {
            'test_id': test_id,
            'user_id': test['user_id'],
            'subject': test['subject'],
            'completed_at': test['completed_at'],
            'total_questions': total_questions,
            'correct_count': correct_count,
            'accuracy': round(accuracy * 100, 2),
            'overall_level': level,
            'category_stats': {
                cat: {
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': round(stats['correct'] / stats['total'] * 100, 2) if stats['total'] > 0 else 0
                } for cat, stats in category_stats.items()
            },
            'difficulty_stats': {
                diff: {
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': round(stats['correct'] / stats['total'] * 100, 2) if stats['total'] > 0 else 0
                } for diff, stats in difficulty_stats.items()
            },
            'suggestions': suggestions,
            'recommended_exams': self._get_recommended_exams(level, test['subject']),
            'learning_path': self._generate_learning_path(level, category_stats)
        }
        
        self._save_report(test_id, report)
        return report
    
    def _calculate_level(self, accuracy: float, difficulty_stats: Dict) -> str:
        """计算用户水平等级"""
        if accuracy >= 0.9:
            return '高级'
        elif accuracy >= 0.75:
            return '中高级'
        elif accuracy >= 0.6:
            return '中级'
        elif accuracy >= 0.4:
            return '初级'
        else:
            return '入门'
    
    def _generate_suggestions(self, category_stats: Dict, difficulty_stats: Dict) -> List[str]:
        """生成学习建议"""
        suggestions = []
        
        # 根据学科表现生成建议
        for cat, stats in category_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            if accuracy < 0.5:
                suggestions.append(f"🔴 建议重点学习「{cat}」,当前正确率仅{accuracy*100:.0f}%")
            elif accuracy < 0.7:
                suggestions.append(f"🟡 「{cat}」需要加强练习,当前正确率{accuracy*100:.0f}%")
            else:
                suggestions.append(f"🟢 「{cat}」表现良好,正确率{accuracy*100:.0f}%")
        
        # 根据难度表现生成建议
        easy_accuracy = difficulty_stats.get(1, {}).get('correct', 0) / (difficulty_stats.get(1, {}).get('total', 1) or 1)
        hard_accuracy = difficulty_stats.get(3, {}).get('correct', 0) / (difficulty_stats.get(3, {}).get('total', 1) or 1)
        
        if easy_accuracy < 0.7:
            suggestions.append("建议先巩固基础知识,再挑战更高难度题目")
        if hard_accuracy > 0.7:
            suggestions.append("可以尝试更具挑战性的题目,突破当前水平")
        
        return suggestions
    
    def _get_recommended_exams(self, level: str, subject: str) -> List[Dict]:
        """获取推荐考试"""
        level_map = {
            '入门': ['基础测试', '入门练习'],
            '初级': ['基础测试', '进阶练习'],
            '中级': ['进阶测试', '模拟考试'],
            '中高级': ['高级测试', '模拟考试'],
            '高级': ['高级测试', '挑战测试']
        }
        
        exams = []
        for exam_name in level_map.get(level, ['基础测试']):
            exams.append({
                'name': exam_name,
                'subject': subject,
                'level': level,
                'estimated_duration': 30
            })
        
        return exams
    
    def _generate_learning_path(self, level: str, category_stats: Dict) -> List[Dict]:
        """生成学习路径"""
        path = []
        
        # 找出需要加强的学科
        weak_categories = [
            cat for cat, stats in category_stats.items()
            if (stats['correct'] / stats['total'] if stats['total'] > 0 else 0) < 0.7
        ]
        
        # 生成学习步骤
        step = 1
        for cat in weak_categories[:3]:
            path.append({
                'step': step,
                'subject': cat,
                'goal': f"提升{cat}能力",
                'duration_days': 7,
                'activities': [
                    f"完成{cat}基础知识点学习",
                    f"每日练习10道{cat}题目",
                    f"完成{cat}专项测试"
                ]
            })
            step += 1
        
        if not weak_categories:
            path.append({
                'step': 1,
                'subject': '综合提升',
                'goal': '挑战更高难度',
                'duration_days': 14,
                'activities': [
                    '尝试提高难度题目',
                    '完成模拟考试',
                    '分析错题并总结'
                ]
            })
        
        return path
    
    def _save_report(self, test_id: str, report: Dict):
        """保存评估报告"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO placement_reports
                (test_id, user_id, report_data, generated_at)
                VALUES (?, ?, ?, ?)
            ''', (test_id, report['user_id'], json.dumps(report), datetime.now()))
            
            conn.commit()
    
    def get_user_reports(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户的摸底测试报告"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pr.report_data, pr.generated_at, pt.subject
                FROM placement_reports pr
                JOIN placement_tests pt ON pr.test_id = pt.id
                WHERE pr.user_id = ?
                ORDER BY pr.generated_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            reports = []
            for row in cursor.fetchall():
                report_data = json.loads(row[0])
                report_data['subject'] = row[2]
                report_data['generated_at'] = row[1]
                reports.append(report_data)
            
            return reports
    
    def get_user_current_level(self, user_id: int) -> Optional[str]:
        """获取用户当前水平"""
        reports = self.get_user_reports(user_id, 1)
        if reports:
            return reports[0].get('overall_level')
        return None
    
    def create_adaptive_placement_test(self, user_id: int, initial_difficulty: str = '中级') -> Dict:
        """创建自适应摸底测试"""
        test_id = self._generate_test_id()
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO placement_tests 
                (id, user_id, subject, status, created_at, estimated_duration, is_adaptive)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_id, user_id, '自适应综合', 'created', datetime.now(), 20, True))
            
            conn.commit()
        
        # 自适应生成题目
        questions = self._generate_adaptive_questions(user_id, initial_difficulty)
        self._save_test_questions(test_id, questions)
        
        return {
            'test_id': test_id,
            'user_id': user_id,
            'subject': '自适应综合',
            'status': 'created',
            'is_adaptive': True,
            'estimated_duration': 20,
            'question_count': len(questions)
        }
    
    def _generate_adaptive_questions(self, user_id: int, initial_difficulty: str) -> List[Dict]:
        """自适应生成题目"""
        questions = []
        # 转换难度字符串为数值
        difficulty_map = {'入门': 1, '基础': 2, '提高': 3, '拓展': 4}
        current_diff = difficulty_map.get(initial_difficulty, 2)
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            for _ in range(15):
                cursor.execute('''
                    SELECT id, content, options, correct_answer, difficulty, points, tags
                    FROM questions
                    WHERE difficulty = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                ''', (current_diff,))
                
                row = cursor.fetchone()
                if row:
                    # 从tags中解析学科分类
                    tags = json.loads(row[6])
                    category = tags[0] if tags else '综合'
                    
                    questions.append({
                        'question_id': row[0],
                        'question_text': row[1],
                        'options': json.loads(row[2]),
                        'correct_answer': row[3],
                        'difficulty': row[4],
                        'points': row[5],
                        'category': category
                    })
                    
                    # 模拟自适应调整(简化版)
                    if random.random() > 0.5 and current_diff < 4:
                        current_diff += 1
                    elif random.random() < 0.2 and current_diff > 1:
                        current_diff -= 1
        
        return questions
    
    def init_database(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 创建摸底测试表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_tests (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    subject TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    is_adaptive BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # 创建摸底测试题目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_test_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    question_id INTEGER,
                    question_text TEXT,
                    options TEXT,
                    correct_answer TEXT,
                    difficulty TEXT,
                    points INTEGER,
                    category TEXT,
                    order_index INTEGER,
                    user_answer TEXT,
                    is_correct BOOLEAN,
                    answered_at TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES placement_tests(id)
                )
            ''')
            
            # 创建摸底测试报告表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    user_id INTEGER,
                    report_data TEXT,
                    generated_at TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES placement_tests(id)
                )
            ''')
            
            conn.commit()

# 全局摸底测试服务实例
placement_test_service = None

def get_placement_test_service():
    """获取摸底测试服务实例"""
    global placement_test_service
    if placement_test_service is None:
        placement_test_service = PlacementTestService()
    return placement_test_service

if __name__ == "__main__":
    import os
    # 设置正确的数据库路径 - 需要向上三层目录到 flask-app
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    print(f"数据库路径: {db_path}")
    service = PlacementTestService(db_path)
    
    # 先初始化数据库表
    print("初始化数据库表...")
    service.init_database()
    print("数据库表初始化完成")
    
    # 测试创建摸底测试
    print("\n创建摸底测试...")
    test = service.create_placement_test(1, '数学')
    print(f"创建成功: {test}")
    
    # 测试开始测试
    print("\n开始测试...")
    service.start_test(test['test_id'])
    
    # 测试提交答案
    print("\n提交答案...")
    questions = service.get_placement_test(test['test_id'])['questions']
    for q in questions[:5]:
        service.submit_answer(test['test_id'], q['question_id'], q['correct_answer'])
    
    # 测试完成测试
    print("\n完成测试...")
    report = service.complete_test(test['test_id'])
    logger.info(f"评估报告:\n{json.dumps(report, ensure_ascii=False, indent=2)}")
