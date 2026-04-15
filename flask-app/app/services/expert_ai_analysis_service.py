#!/usr/bin/env python3
"""
专家AI分析服务
负责基于用户答题行为生成针对性的试卷
"""

import os
import sys
import sqlite3
import json
import random
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ExpertAIAnalysisService:
    """专家AI分析服务"""
    
    def __init__(self, db_path="app.db"):
        """初始化专家AI分析服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 试卷生成配置
        self.exam_config = {
            'weak_area_weight': 0.6,  # 薄弱环节题目占比
            'strong_area_weight': 0.3,  # 优势环节题目占比
            'challenge_weight': 0.1,  # 挑战题目占比
            'default_exam_size': 10,  # 默认试卷题目数量
            'max_weak_area_questions': 8,  # 薄弱环节题目最大数量
            'min_strong_area_questions': 2  # 优势环节题目最小数量
        }
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def analyze_user_performance(self, user_id):
        """分析用户表现
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户表现分析结果
        """
        if not self.connect():
            return None
        
        try:
            # 获取用户答题记录
            sql = """
            SELECT q.question_type, q.level_id, e.is_correct, e.time_spent
            FROM exam_answers e
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ?
            ORDER BY e.created_at DESC
            LIMIT 100
            """
            self.cursor.execute(sql, (user_id,))
            
            # 分析数据
            question_type_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            level_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            total_answers = 0
            correct_answers = 0
            
            for row in self.cursor.fetchall():
                question_type, level_id, is_correct, time_spent = row
                total_answers += 1
                
                # 统计题型表现
                question_type_performance[question_type]['total'] += 1
                if is_correct:
                    correct_answers += 1
                    question_type_performance[question_type]['correct'] += 1
                if time_spent:
                    question_type_performance[question_type]['time_spent'] += time_spent
                
                # 统计难度等级表现
                level_performance[level_id]['total'] += 1
                if is_correct:
                    level_performance[level_id]['correct'] += 1
                if time_spent:
                    level_performance[level_id]['time_spent'] += time_spent
            
            # 计算整体准确率
            overall_accuracy = correct_answers / total_answers if total_answers > 0 else 0
            
            # 分析薄弱环节和优势环节
            weak_areas = []
            strong_areas = []
            
            for q_type, stats in question_type_performance.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                
                area_info = {
                    'question_type': q_type,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': accuracy,
                    'average_time': avg_time
                }
                
                if accuracy < 0.6:
                    weak_areas.append(area_info)
                elif accuracy > 0.8:
                    strong_areas.append(area_info)
            
            # 按准确率排序
            weak_areas.sort(key=lambda x: x['accuracy'])
            strong_areas.sort(key=lambda x: x['accuracy'], reverse=True)
            
            # 分析难度等级表现
            level_analysis = []
            for level_id, stats in level_performance.items():
                accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                
                level_analysis.append({
                    'level_id': level_id,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': accuracy,
                    'average_time': avg_time
                })
            
            # 按等级排序
            level_analysis.sort(key=lambda x: x['level_id'])
            
            return {
                'overall_accuracy': overall_accuracy,
                'total_answers': total_answers,
                'weak_areas': weak_areas[:3],  # 前三个薄弱环节
                'strong_areas': strong_areas[:3],  # 前三个优势环节
                'level_analysis': level_analysis
            }
        except Exception as e:
            print(f"分析用户表现失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def generate_personalized_exam(self, user_id, exam_size=None, language='japanese'):
        """生成个性化试卷
        
        Args:
            user_id: 用户ID
            exam_size: 试卷题目数量
            language: 语言
            
        Returns:
            个性化试卷题目列表
        """
        if exam_size is None:
            exam_size = self.exam_config['default_exam_size']
        
        # 分析用户表现
        performance_analysis = self.analyze_user_performance(user_id)
        if not performance_analysis:
            # 如果没有足够的历史数据，使用基于等级的出题
            from app.services.level_based_question_generator import get_level_based_generator
            generator = get_level_based_generator()
            return generator.generate_exam(user_id, exam_size, language)
        
        # 计算各类型题目的数量
        weak_area_count = min(
            int(exam_size * self.exam_config['weak_area_weight']),
            self.exam_config['max_weak_area_questions']
        )
        strong_area_count = max(
            int(exam_size * self.exam_config['strong_area_weight']),
            self.exam_config['min_strong_area_questions']
        )
        challenge_count = exam_size - weak_area_count - strong_area_count
        
        # 确保数量不为负数
        challenge_count = max(0, challenge_count)
        
        # 调整数量，确保总和为exam_size
        if weak_area_count + strong_area_count + challenge_count != exam_size:
            weak_area_count += exam_size - (weak_area_count + strong_area_count + challenge_count)
        
        # 生成题目
        questions = []
        
        # 获取薄弱环节题目
        if weak_area_count > 0 and performance_analysis['weak_areas']:
            weak_questions = self._get_questions_by_areas(
                performance_analysis['weak_areas'],
                weak_area_count,
                language,
                prioritize_weak=True
            )
            questions.extend(weak_questions)
        
        # 获取优势环节题目
        if strong_area_count > 0 and performance_analysis['strong_areas']:
            strong_questions = self._get_questions_by_areas(
                performance_analysis['strong_areas'],
                strong_area_count,
                language,
                prioritize_weak=False
            )
            questions.extend(strong_questions)
        
        # 获取挑战题目
        if challenge_count > 0:
            challenge_questions = self._get_challenge_questions(
                user_id,
                challenge_count,
                language
            )
            questions.extend(challenge_questions)
        
        # 如果题目数量不足，补充基础题目
        while len(questions) < exam_size:
            additional_questions = self._get_generic_questions(1, language)
            if additional_questions:
                questions.extend(additional_questions)
            else:
                break
        
        # 打乱题目顺序
        random.shuffle(questions)
        
        return questions
    
    def _get_questions_by_areas(self, areas, count, language, prioritize_weak=True):
        """根据领域获取题目
        
        Args:
            areas: 领域列表
            count: 需要的题目数量
            language: 语言
            prioritize_weak: 是否优先获取薄弱环节的题目
            
        Returns:
            题目列表
        """
        if not self.connect():
            return []
        
        try:
            questions = []
            remaining_count = count
            
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            # 遍历领域
            for area in areas:
                if remaining_count <= 0:
                    break
                
                question_type = area['question_type']
                
                # 确定难度等级
                if prioritize_weak:
                    # 薄弱环节使用当前等级或略低等级
                    level_id = min(3, int(area.get('level_id', 2)))
                else:
                    # 优势环节使用当前等级或略高等级
                    level_id = max(1, int(area.get('level_id', 2)))
                
                # 查询题目，包含音频信息
                sql = """
                SELECT q.id, q.content, q.options, q.answer, q.explanation, q.question_type, q.level_id,
                       a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                FROM questions q
                LEFT JOIN audio_files a ON q.audio_id = a.id
                WHERE q.question_type = ? AND q.language_id = ? AND q.level_id = ?
                ORDER BY RANDOM()
                LIMIT ?
                """
                self.cursor.execute(sql, (question_type, language_id, level_id, remaining_count))
                
                for row in self.cursor.fetchall():
                    question = {
                        'id': row[0],
                        'content': row[1],
                        'options': json.loads(row[2]) if row[2] else [],
                        'answer': row[3],
                        'explanation': row[4],
                        'question_type': row[5],
                        'level_id': row[6]
                    }
                    
                    # 添加音频信息
                    if row[7]:  # 如果有音频ID
                        question['audio'] = {
                            'id': row[7],
                            'filename': row[8],
                            'url': row[9],
                            'accent': row[10],
                            'transcript': row[11]
                        }
                    
                    questions.append(question)
                    remaining_count -= 1
                    
                    if remaining_count <= 0:
                        break
            
            return questions
        except Exception as e:
            print(f"获取领域题目失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def _get_challenge_questions(self, user_id, count, language):
        """获取挑战题目
        
        Args:
            user_id: 用户ID
            count: 需要的题目数量
            language: 语言
            
        Returns:
            挑战题目列表
        """
        if not self.connect():
            return []
        
        try:
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            # 查询高难度题目，包含音频信息
            sql = """
            SELECT q.id, q.content, q.options, q.answer, q.explanation, q.question_type, q.level_id,
                   a.id as audio_id, a.filename, a.url, a.accent, a.transcript
            FROM questions q
            LEFT JOIN audio_files a ON q.audio_id = a.id
            WHERE q.language_id = ? AND q.level_id >= 3
            ORDER BY RANDOM()
            LIMIT ?
            """
            self.cursor.execute(sql, (language_id, count))
            
            questions = []
            for row in self.cursor.fetchall():
                question = {
                    'id': row[0],
                    'content': row[1],
                    'options': json.loads(row[2]) if row[2] else [],
                    'answer': row[3],
                    'explanation': row[4],
                    'question_type': row[5],
                    'level_id': row[6]
                }
                
                # 添加音频信息
                if row[7]:  # 如果有音频ID
                    question['audio'] = {
                        'id': row[7],
                        'filename': row[8],
                        'url': row[9],
                        'accent': row[10],
                        'transcript': row[11]
                    }
                
                questions.append(question)
            
            return questions
        except Exception as e:
            print(f"获取挑战题目失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def _get_generic_questions(self, count, language):
        """获取通用题目
        
        Args:
            count: 需要的题目数量
            language: 语言
            
        Returns:
            通用题目列表
        """
        if not self.connect():
            return []
        
        try:
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            # 查询中等难度题目，包含音频信息
            sql = """
            SELECT q.id, q.content, q.options, q.answer, q.explanation, q.question_type, q.level_id,
                   a.id as audio_id, a.filename, a.url, a.accent, a.transcript
            FROM questions q
            LEFT JOIN audio_files a ON q.audio_id = a.id
            WHERE q.language_id = ? AND q.level_id = 2
            ORDER BY RANDOM()
            LIMIT ?
            """
            self.cursor.execute(sql, (language_id, count))
            
            questions = []
            for row in self.cursor.fetchall():
                question = {
                    'id': row[0],
                    'content': row[1],
                    'options': json.loads(row[2]) if row[2] else [],
                    'answer': row[3],
                    'explanation': row[4],
                    'question_type': row[5],
                    'level_id': row[6]
                }
                
                # 添加音频信息
                if row[7]:  # 如果有音频ID
                    question['audio'] = {
                        'id': row[7],
                        'filename': row[8],
                        'url': row[9],
                        'accent': row[10],
                        'transcript': row[11]
                    }
                
                questions.append(question)
            
            return questions
        except Exception as e:
            print(f"获取通用题目失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def generate_analysis_report(self, user_id, exam_id):
        """生成考试分析报告
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            
        Returns:
            分析报告
        """
        if not self.connect():
            return None
        
        try:
            # 获取考试信息
            sql = """
            SELECT score, time_spent, correct_answers, total_questions, difficulty_level
            FROM exam_performance
            WHERE user_id = ? AND exam_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
            self.cursor.execute(sql, (user_id, exam_id))
            exam_info = self.cursor.fetchone()
            
            if not exam_info:
                return None
            
            score, time_spent, correct_answers, total_questions, difficulty_level = exam_info
            
            # 获取答题详情
            sql = """
            SELECT q.question_type, q.level_id, e.is_correct, e.time_spent
            FROM exam_answers e
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ? AND e.exam_id = ?
            """
            self.cursor.execute(sql, (user_id, exam_id))
            
            # 分析答题详情
            question_type_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            level_performance = defaultdict(lambda: {'total': 0, 'correct': 0, 'time_spent': 0})
            
            for row in self.cursor.fetchall():
                question_type, level_id, is_correct, time_spent = row
                
                # 统计题型表现
                question_type_performance[question_type]['total'] += 1
                if is_correct:
                    question_type_performance[question_type]['correct'] += 1
                if time_spent:
                    question_type_performance[question_type]['time_spent'] += time_spent
                
                # 统计难度等级表现
                level_performance[level_id]['total'] += 1
                if is_correct:
                    level_performance[level_id]['correct'] += 1
                if time_spent:
                    level_performance[level_id]['time_spent'] += time_spent
            
            # 计算准确率
            accuracy = correct_answers / total_questions if total_questions > 0 else 0
            avg_time_per_question = time_spent / total_questions if total_questions > 0 else 0
            
            # 分析薄弱和优势题型
            weak_types = []
            strong_types = []
            
            for q_type, stats in question_type_performance.items():
                type_accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                avg_type_time = stats['time_spent'] / stats['total'] if stats['total'] > 0 else 0
                
                type_info = {
                    'question_type': q_type,
                    'total': stats['total'],
                    'correct': stats['correct'],
                    'accuracy': type_accuracy,
                    'average_time': avg_type_time
                }
                
                if type_accuracy < 0.6:
                    weak_types.append(type_info)
                elif type_accuracy > 0.8:
                    strong_types.append(type_info)
            
            # 排序
            weak_types.sort(key=lambda x: x['accuracy'])
            strong_types.sort(key=lambda x: x['accuracy'], reverse=True)
            
            # 生成报告
            report = {
                'score': score,
                'accuracy': accuracy,
                'time_spent': time_spent,
                'average_time_per_question': avg_time_per_question,
                'difficulty_level': difficulty_level,
                'weak_types': weak_types,
                'strong_types': strong_types,
                'recommendations': []
            }
            
            # 生成建议
            if weak_types:
                report['recommendations'].append(f'建议加强 {weak_types[0]["question_type"]} 题型的练习')
            
            if accuracy < 0.6:
                report['recommendations'].append('建议增加练习量，提高基础知识掌握')
            elif accuracy > 0.8:
                report['recommendations'].append('表现优秀，建议尝试更高级别的题目')
            
            if avg_time_per_question < 10:
                report['recommendations'].append('答题速度过快，建议仔细审题')
            elif avg_time_per_question > 60:
                report['recommendations'].append('答题速度较慢，建议提高解题速度')
            
            return report
        except Exception as e:
            print(f"生成分析报告失败: {str(e)}")
            return None
        finally:
            self.close()

# 全局专家AI分析服务实例
expert_ai_analysis_service = None

def get_expert_ai_analysis_service():
    """获取专家AI分析服务实例"""
    global expert_ai_analysis_service
    if expert_ai_analysis_service is None:
        expert_ai_analysis_service = ExpertAIAnalysisService()
    return expert_ai_analysis_service

if __name__ == "__main__":
    # 测试专家AI分析服务
    service = ExpertAIAnalysisService()
    
    # 测试分析用户表现
    user_id = 1
    print("分析用户表现...")
    performance = service.analyze_user_performance(user_id)
    if performance:
        print(f"用户表现分析: {json.dumps(performance, indent=2, ensure_ascii=False)}")
    
    # 测试生成个性化试卷
    print("\n生成个性化试卷...")
    exam_questions = service.generate_personalized_exam(user_id, exam_size=10, language='japanese')
    print(f"生成题目数量: {len(exam_questions)}")
    for i, q in enumerate(exam_questions, 1):
        print(f"题目 {i}: 题型 {q['question_type']}, 难度等级 {q['level_id']}")
        print(f"内容: {q['content'][:50]}...")
        print()
    
    # 测试生成分析报告
    print("\n生成分析报告...")
    report = service.generate_analysis_report(user_id, 1)
    if report:
        print(f"分析报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
