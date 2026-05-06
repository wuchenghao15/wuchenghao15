#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版摸底测试系统 - 智能测试与用户数据整合"""

import os
import re
# import json removed - using database storage
import sqlite3
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('assessment_system')

class EnhancedAssessmentSystem:
    def __init__(self):
        self.db_path = 'app.db'
        self.init_database()
        self.test_types = self.init_test_types()
    
    def init_test_types(self):
        """初始化测试类型"""
        return {
            'placement': {'name': '摸底测试', 'description': '评估学生当前水平'},
            'diagnostic': {'name': '诊断测试', 'description': '识别学习难点'},
            'progress': {'name': '进度测试', 'description': '追踪学习进度'},
            'competence': {'name': '能力测试', 'description': '评估综合能力'}
        }
    
    def init_database(self):
        """初始化摸底测试相关数据表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS assessment_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT UNIQUE NOT NULL,
                test_name TEXT,
                test_type TEXT,
                subject TEXT,
                grade_level TEXT,
                duration INTEGER,
                question_count INTEGER,
                difficulty_range TEXT,
                created_at TEXT,
                updated_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS test_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT,
                question_id TEXT,
                question_order INTEGER,
                FOREIGN KEY(test_id) REFERENCES assessment_tests(test_id),
                FOREIGN KEY(question_id) REFERENCES questions(question_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS user_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                test_id TEXT,
                score INTEGER,
                max_score INTEGER,
                completed_at TEXT,
                duration_seconds INTEGER,
                answers TEXT,
                analysis TEXT,
                level_assessment TEXT,
                recommendations TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(test_id) REFERENCES assessment_tests(test_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS user_learning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                subject_proficiencies TEXT,
                learning_styles TEXT,
                weak_points TEXT,
                strong_points TEXT,
                progress_tracking TEXT,
                last_updated TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS assessment_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE,
                user_id TEXT,
                test_id TEXT,
                report_type TEXT,
                content TEXT,
                generated_at TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("摸底测试数据库表初始化完成")
    
    def create_placement_test(self, subject, grade_level, question_count=20):
        """创建摸底测试"""
        print(f"创建{subject}摸底测试...")
        
        test_id = f"placement_{subject}_{grade_level}_{int(time.time())}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO assessment_tests
                (test_id, test_name, test_type, subject, grade_level, 
                 duration, question_count, difficulty_range, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                f"{subject}摸底测试 ({grade_level})",
                'placement',
                subject,
                grade_level,
                question_count * 3 * 60,
                question_count,
                str([1, 5]),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # 从题库随机选取题目
            cursor.execute('''
                SELECT question_id FROM questions 
                WHERE category = ? 
                ORDER BY RANDOM() LIMIT ?
            ''', (subject, question_count))
            
            questions = cursor.fetchall()
            
            for i, (question_id,) in enumerate(questions, 1):
                cursor.execute('''
                    INSERT INTO test_questions (test_id, question_id, question_order)
                    VALUES (?, ?, ?)
                ''', (test_id, question_id, i))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 成功创建摸底测试: {test_id}")
            return test_id
        
        except Exception as e:
            logger.error(f"创建摸底测试失败: {e}")
            return None
    
    def create_diagnostic_test(self, user_id):
        """创建诊断测试（基于用户弱点）"""
        print(f"为用户 {user_id} 创建诊断测试...")
        
        profile = self.get_user_profile(user_id)
        weak_points = profile.get('weak_points', [])
        
        if not weak_points:
            print("  - 用户暂无弱点记录，使用默认题目")
            weak_points = ['基础']
        
        test_id = f"diagnostic_{user_id}_{int(time.time())}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO assessment_tests
                (test_id, test_name, test_type, subject, grade_level, 
                 duration, question_count, difficulty_range, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_id,
                f"诊断测试 - 用户{user_id}",
                'diagnostic',
                '综合',
                '自适应',
                15 * 60,
                15,
                str([2, 4]),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            # 根据弱点选择题目
            questions = []
            for weak_point in weak_points[:3]:
                cursor.execute('''
                    SELECT question_id FROM questions 
                    WHERE category LIKE ? 
                    ORDER BY RANDOM() LIMIT 5
                ''', (f'%{weak_point}%',))
                questions.extend([q[0] for q in cursor.fetchall()])
            
            questions = list(set(questions))[:15]
            
            for i, question_id in enumerate(questions, 1):
                cursor.execute('''
                    INSERT INTO test_questions (test_id, question_id, question_order)
                    VALUES (?, ?, ?)
                ''', (test_id, question_id, i))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 成功创建诊断测试: {test_id}")
            return test_id
        
        except Exception as e:
            logger.error(f"创建诊断测试失败: {e}")
            return None
    
    def get_user_profile(self, user_id):
        """获取用户学习档案"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT subject_proficiencies, weak_points, strong_points FROM user_learning_profiles WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {
                    'subject_proficiencies': eval(result[0]) if result[0] else {},
                    'weak_points': eval(result[1]) if result[1] else [],
                    'strong_points': eval(result[2]) if result[2] else []
                }
            
            return {'subject_proficiencies': {}, 'weak_points': [], 'strong_points': []}
        
        except Exception as e:
            logger.error(f"获取用户档案失败: {e}")
            return {'subject_proficiencies': {}, 'weak_points': [], 'strong_points': []}
    
    def update_user_profile(self, user_id, assessment_data):
        """更新用户学习档案"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            profile = self.get_user_profile(user_id)
            
            # 更新能力水平
            if 'subject_scores' in assessment_data:
                for subject, score in assessment_data['subject_scores'].items():
                    profile['subject_proficiencies'][subject] = score
            
            # 更新弱点和强项
            if 'weak_points' in assessment_data:
                profile['weak_points'] = list(set(profile['weak_points'] + assessment_data['weak_points']))
            
            if 'strong_points' in assessment_data:
                profile['strong_points'] = list(set(profile['strong_points'] + assessment_data['strong_points']))
            
            # 更新进度追踪
            profile['progress_tracking'] = {
                'last_assessment': datetime.now().isoformat(),
                'assessments_completed': profile.get('progress_tracking', {}).get('assessments_completed', 0) + 1
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_learning_profiles
                (user_id, subject_proficiencies, learning_styles, weak_points, 
                 strong_points, progress_tracking, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                str(profile['subject_proficiencies']),
                str([]),
                str(profile['weak_points']),
                str(profile['strong_points']),
                str(profile.get('progress_tracking', {})),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            logger.error(f"更新用户档案失败: {e}")
            return False
    
    def process_assessment(self, user_id, test_id, answers):
        """处理评估结果"""
        print(f"处理用户 {user_id} 的评估...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取测试信息
            cursor.execute('SELECT question_count FROM assessment_tests WHERE test_id = ?', (test_id,))
            result = cursor.fetchone()
            max_score = result[0] if result else 20
            
            # 获取题目和答案
            cursor.execute('''
                SELECT q.question_id, q.answer 
                FROM test_questions tq 
                JOIN questions q ON tq.question_id = q.question_id 
                WHERE tq.test_id = ? 
                ORDER BY tq.question_order
            ''', (test_id,))
            
            questions = cursor.fetchall()
            
            # 计算得分
            score = 0
            correct_answers = []
            incorrect_answers = []
            
            for i, (question_id, correct_answer) in enumerate(questions):
                user_answer = answers.get(str(i + 1), '')
                if user_answer.upper() == correct_answer.upper():
                    score += 1
                    correct_answers.append(question_id)
                else:
                    incorrect_answers.append(question_id)
            
            # 分析错误模式
            analysis = self.analyze_errors(incorrect_answers)
            
            # 评估等级
            level = self.assess_level(score, max_score)
            
            # 生成建议
            recommendations = self.generate_recommendations(level, analysis, incorrect_answers)
            
            # 保存评估结果
            cursor.execute('''
                INSERT INTO user_assessments
                (user_id, test_id, score, max_score, completed_at, duration_seconds, 
                 answers, analysis, level_assessment, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                test_id,
                score,
                max_score,
                datetime.now().isoformat(),
                0,
                str(answers),
                str(analysis),
                str(level),
                str(recommendations)
            ))
            
            # 更新用户档案
            self.update_user_profile(user_id, {
                'subject_scores': {'综合': score / max_score * 100},
                'weak_points': analysis.get('weak_categories', []),
                'strong_points': analysis.get('strong_categories', [])
            })
            
            conn.commit()
            conn.close()
            
            # 生成报告
            self.generate_report(user_id, test_id, score, max_score, analysis, level, recommendations)
            
            print(f"  ✓ 评估完成，得分: {score}/{max_score}")
            return {'score': score, 'max_score': max_score, 'level': level}
        
        except Exception as e:
            logger.error(f"处理评估失败: {e}")
            return None
    
    def analyze_errors(self, incorrect_questions):
        """分析错误模式"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            category_counts = defaultdict(int)
            difficulty_counts = defaultdict(int)
            
            for question_id in incorrect_questions:
                cursor.execute('SELECT category, difficulty FROM questions WHERE question_id = ?', (question_id,))
                result = cursor.fetchone()
                if result:
                    category_counts[result[0]] += 1
                    difficulty_counts[result[1]] += 1
            
            conn.close()
            
            # 识别最弱的分类
            weak_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            weak_categories = [cat for cat, _ in weak_categories]
            
            return {
                'total_incorrect': len(incorrect_questions),
                'category_breakdown': dict(category_counts),
                'difficulty_breakdown': dict(difficulty_counts),
                'weak_categories': weak_categories,
                'strong_categories': []
            }
        
        except Exception as e:
            logger.error(f"分析错误失败: {e}")
            return {}
    
    def assess_level(self, score, max_score):
        """评估等级"""
        percentage = score / max_score * 100
        
        if percentage >= 90:
            return {'level': 'A', 'description': '优秀', 'suggestion': '可以挑战更高难度'}
        elif percentage >= 80:
            return {'level': 'B', 'description': '良好', 'suggestion': '继续保持，加强薄弱环节'}
        elif percentage >= 70:
            return {'level': 'C', 'description': '中等', 'suggestion': '需要加强练习'}
        elif percentage >= 60:
            return {'level': 'D', 'description': '及格', 'suggestion': '需要重点复习'}
        else:
            return {'level': 'E', 'description': '需努力', 'suggestion': '建议从基础开始'}
    
    def generate_recommendations(self, level, analysis, incorrect_questions):
        """生成学习建议"""
        recommendations = []
        
        if level['level'] in ['D', 'E']:
            recommendations.append({
                'type': 'urgent',
                'title': '基础巩固',
                'content': '建议复习基础知识，从简单题目开始练习'
            })
        
        if analysis.get('weak_categories'):
            for category in analysis['weak_categories']:
                recommendations.append({
                    'type': 'focus',
                    'title': f'{category}专项练习',
                    'content': f'{category}方面较弱，建议进行专项练习'
                })
        
        recommendations.append({
            'type': 'general',
            'title': '定期练习',
            'content': '建议每周进行2-3次练习，保持学习节奏'
        })
        
        return recommendations
    
    def generate_report(self, user_id, test_id, score, max_score, analysis, level, recommendations):
        """生成评估报告"""
        report_id = f"report_{user_id}_{test_id}_{int(time.time())}"
        
        report_content = {
            'report_id': report_id,
            'user_id': user_id,
            'test_id': test_id,
            'generated_at': datetime.now().isoformat(),
            'score': {
                'current': score,
                'max': max_score,
                'percentage': score / max_score * 100,
                'level': level['level'],
                'level_description': level['description']
            },
            'analysis': analysis,
            'recommendations': recommendations
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO assessment_reports
                (report_id, user_id, test_id, report_type, content, generated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                user_id,
                test_id,
                'placement',
                str(report_content),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  ✓ 报告已生成: {report_id}")
            return report_id
        
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return None
    
    def integrate_user_database(self):
        """整合用户数据库"""
        print("\n整合用户数据库...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有用户
            cursor.execute('SELECT id, username FROM users')
            users = cursor.fetchall()
            
            # 为每个用户创建学习档案（如果不存在）
            for user_id, username in users:
                cursor.execute('SELECT COUNT(*) FROM user_learning_profiles WHERE user_id = ?', (str(user_id),))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO user_learning_profiles
                        (user_id, subject_proficiencies, learning_styles, weak_points, 
                         strong_points, progress_tracking, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(user_id),
                        str({}),
                        str([]),
                        str([]),
                        str([]),
                        str({'assessments_completed': 0}),
                        datetime.now().isoformat()
                    ))
                    print(f"  ✓ 为用户 {username} 创建学习档案")
            
            conn.commit()
            conn.close()
            
            print(f"\n用户数据库整合完成！")
            return len(users)
        
        except Exception as e:
            logger.error(f"整合用户数据库失败: {e}")
            return 0
    
    def run_demo_assessment(self):
        """运行演示评估"""
        print("\n" + "="*80)
        print("          摸底测试系统演示")
        print("="*80)
        
        # 创建测试
        test_id = self.create_placement_test('语文', '高中', 10)
        
        if test_id:
            # 模拟用户答题
            demo_answers = {str(i): random.choice(['A', 'B', 'C', 'D']) for i in range(1, 11)}
            demo_answers['1'] = 'A'
            demo_answers['2'] = 'B'
            demo_answers['3'] = 'C'
            demo_answers['4'] = 'A'
            demo_answers['5'] = 'B'
            
            # 处理评估
            result = self.process_assessment('1', test_id, demo_answers)
            
            if result:
                print(f"\n评估结果:")
                print(f"  得分: {result['score']}/{result['max_score']}")
                print(f"  等级: {result['level']['level']} - {result['level']['description']}")
                print(f"  建议: {result['level']['suggestion']}")
    
    def show_system_stats(self):
        """显示系统统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM assessment_tests')
            test_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_assessments')
            assessment_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_learning_profiles')
            profile_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM assessment_reports')
            report_count = cursor.fetchone()[0]
            
            conn.close()
            
            print("\n" + "="*80)
            print("          摸底测试系统统计")
            print("="*80)
            print(f"\n  测试数量: {test_count}")
            print(f"  评估记录: {assessment_count}")
            print(f"  用户档案: {profile_count}")
            print(f"  报告数量: {report_count}")
        
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
    
    def run_full_system(self):
        """运行完整系统"""
        print("="*80)
        print("          增强版摸底测试系统")
        print("="*80)
        
        print("\n[1/3] 整合用户数据库...")
        user_count = self.integrate_user_database()
        print(f"  已整合 {user_count} 个用户")
        
        print("\n[2/3] 创建示例测试...")
        subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理']
        for subject in subjects:
            self.create_placement_test(subject, '高中', 15)
        
        print("\n[3/3] 系统演示...")
        self.run_demo_assessment()
        
        self.show_system_stats()

def main():
    assessment_system = EnhancedAssessmentSystem()
    assessment_system.run_full_system()

if __name__ == "__main__":
    main()