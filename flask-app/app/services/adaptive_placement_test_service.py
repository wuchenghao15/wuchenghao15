#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应初次等级评测服务
实现优化的初次等级评测逻辑
"""

import sqlite3
import json
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptivePlacementTestService:
    """自适应初次等级评测服务"""
    
    def __init__(self):
        """初始化服务"""
        self.db_path = Config.DATABASE_PATH
        self.levels = {
            1: {'name': 'N5/初级', 'min_score': 0, 'max_score': 59},
            2: {'name': 'N4/中级入门', 'min_score': 60, 'max_score': 69},
            3: {'name': 'N3/中级', 'min_score': 70, 'max_score': 79},
            4: {'name': 'N2/高级入门', 'min_score': 80, 'max_score': 89},
            5: {'name': 'N1/高级', 'min_score': 90, 'max_score': 100}
        }
        
        # 难度范围配置
        self.difficulty_ranges = {
            'start': 1,           # 起始难度
            'min': 1,             # 最小难度
            'max': 5,             # 最大难度
            'step': 1             # 难度调整步长
        }
        
        # 题目分布配置
        self.question_distribution = {
            'vocabulary': 0.35,   # 词汇占比
            'grammar': 0.35,      # 语法占比
            'reading': 0.20,      # 阅读占比
            'listening': 0.10     # 听力占比
        }
        
        # 自适应参数
        self.adaptive_params = {
            'initial_questions': 5,    # 初始题目数
            'consecutive_correct': 3,  # 连续正确次数提升难度
            'consecutive_wrong': 3,    # 连续错误次数降低难度
            'min_difficulty_stay': 2,  # 每个难度最少停留题数
            'total_questions': 30       # 总题数
        }
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def generate_initial_test(self, language: str = 'japanese') -> Dict[str, Any]:
        """
        生成初次等级评测的初始试卷
        
        Args:
            language: 语言类型 (japanese/english)
            
        Returns:
            初始试卷数据
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            # 生成初始难度的题目（难度1）
            questions = []
            question_count = self.adaptive_params['initial_questions']
            
            # 按类别分配题目
            for category, ratio in self.question_distribution.items():
                category_count = max(1, int(question_count * ratio))
                
                # 查询题目
                sql = """
                SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                       q.question_type, q.level_id,
                       a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                FROM questions q
                LEFT JOIN audio_files a ON q.audio_id = a.id
                WHERE q.language_id = ? AND q.level_id = 1
                ORDER BY RANDOM()
                LIMIT ?
                """
                cursor.execute(sql, (language_id, category_count))
                
                for row in cursor.fetchall():
                    question = self._format_question(row)
                    question['category'] = category
                    questions.append(question)
            
            # 调整题目数量
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)
            elif len(questions) < question_count:
                # 补充题目
                while len(questions) < question_count:
                    sql = """
                    SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                           q.question_type, q.level_id,
                           a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                    FROM questions q
                    LEFT JOIN audio_files a ON q.audio_id = a.id
                    WHERE q.language_id = ? AND q.level_id = 1
                    ORDER BY RANDOM()
                    LIMIT 1
                    """
                    cursor.execute(sql, (language_id,))
                    row = cursor.fetchone()
                    if row:
                        question = self._format_question(row)
                        question['category'] = 'vocabulary'
                        questions.append(question)
            
            conn.close()
            
            return {
                'success': True,
                'test_id': f'placement_{int(random.random() * 1000000)}',
                'language': language,
                'current_difficulty': 1,
                'questions': questions,
                'total_questions': self.adaptive_params['total_questions'],
                'current_question': 0,
                'adaptive_state': {
                    'consecutive_correct': 0,
                    'consecutive_wrong': 0,
                    'difficulty_stay_count': 0,
                    'scores_by_difficulty': {}
                }
            }
            
        except Exception as e:
            logger.error(f"生成初始测试失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_next_questions(self, 
                         test_state: Dict[str, Any],
                         answers: Dict[str, str],
                         language: str = 'japanese') -> Dict[str, Any]:
        """
        根据答题情况获取下一组题目（自适应难度调整）
        
        Args:
            test_state: 当前测试状态
            answers: 用户答案
            language: 语言类型
            
        Returns:
            下一组题目和更新后的测试状态
        """
        try:
            current_difficulty = test_state.get('current_difficulty', 1)
            adaptive_state = test_state.get('adaptive_state', {})
            current_question = test_state.get('current_question', 0)
            
            # 计算当前答题正确率
            correct_count = 0
            for question_id, user_answer in answers.items():
                # 这里需要查询正确答案进行比对
                is_correct = self._check_answer(question_id, user_answer)
                if is_correct:
                    correct_count += 1
                    adaptive_state['consecutive_correct'] += 1
                    adaptive_state['consecutive_wrong'] = 0
                else:
                    adaptive_state['consecutive_wrong'] += 1
                    adaptive_state['consecutive_correct'] = 0
            
            # 记录当前难度的得分
            if current_difficulty not in adaptive_state['scores_by_difficulty']:
                adaptive_state['scores_by_difficulty'][current_difficulty] = []
            accuracy = correct_count / len(answers) if answers else 0
            adaptive_state['scores_by_difficulty'][current_difficulty].append(accuracy)
            
            # 自适应调整难度
            new_difficulty = self._adjust_difficulty(current_difficulty, adaptive_state)
            
            # 记录难度停留次数
            if new_difficulty == current_difficulty:
                adaptive_state['difficulty_stay_count'] += 1
            else:
                adaptive_state['difficulty_stay_count'] = 0
            
            # 生成下一组题目
            questions = self._generate_questions_by_difficulty(new_difficulty, language)
            
            # 更新当前题目计数
            current_question += len(answers)
            
            # 检查是否完成测试
            is_complete = current_question >= self.adaptive_params['total_questions']
            
            result = {
                'success': True,
                'current_difficulty': new_difficulty,
                'questions': questions,
                'current_question': current_question,
                'total_questions': self.adaptive_params['total_questions'],
                'adaptive_state': adaptive_state,
                'is_complete': is_complete
            }
            
            # 如果完成测试，计算最终等级
            if is_complete:
                final_level = self._calculate_final_level(adaptive_state)
                result['final_level'] = final_level
                result['level_name'] = self.levels[final_level]['name']
            
            return result
            
        except Exception as e:
            logger.error(f"获取下一组题目失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _adjust_difficulty(self, current_difficulty: int, adaptive_state: Dict[str, Any]) -> int:
        """
        根据答题情况自适应调整难度
        
        Args:
            current_difficulty: 当前难度
            adaptive_state: 自适应状态
            
        Returns:
            新的难度
        """
        new_difficulty = current_difficulty
        
        # 检查连续正确次数
        if adaptive_state['consecutive_correct'] >= self.adaptive_params['consecutive_correct']:
            new_difficulty = min(self.difficulty_ranges['max'], 
                                current_difficulty + self.difficulty_ranges['step'])
        
        # 检查连续错误次数
        elif adaptive_state['consecutive_wrong'] >= self.adaptive_params['consecutive_wrong']:
            new_difficulty = max(self.difficulty_ranges['min'], 
                                current_difficulty - self.difficulty_ranges['step'])
        
        # 检查难度停留时间
        elif adaptive_state['difficulty_stay_count'] >= self.adaptive_params['min_difficulty_stay']:
            # 如果在当前难度停留太久，且正确率较高，适当提升难度
            scores = adaptive_state['scores_by_difficulty'].get(current_difficulty, [])
            avg_accuracy = sum(scores) / len(scores) if scores else 0
            if avg_accuracy > 0.8:
                new_difficulty = min(self.difficulty_ranges['max'], 
                                    current_difficulty + self.difficulty_ranges['step'])
            elif avg_accuracy < 0.3:
                new_difficulty = max(self.difficulty_ranges['min'], 
                                    current_difficulty - self.difficulty_ranges['step'])
        
        return new_difficulty
    
    def _calculate_final_level(self, adaptive_state: Dict[str, Any]) -> int:
        """
        计算最终等级
        
        Args:
            adaptive_state: 自适应状态
            
        Returns:
            最终等级 (1-5)
        """
        scores_by_difficulty = adaptive_state.get('scores_by_difficulty', {})
        
        if not scores_by_difficulty:
            return 1
        
        # 计算各难度的平均正确率
        weighted_score = 0
        total_weight = 0
        
        for difficulty, scores in scores_by_difficulty.items():
            avg_accuracy = sum(scores) / len(scores)
            # 难度越高，权重越大
            weight = difficulty
            weighted_score += avg_accuracy * weight
            total_weight += weight
        
        # 计算综合得分
        overall_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        
        # 根据得分确定等级
        for level in sorted(self.levels.keys(), reverse=True):
            level_config = self.levels[level]
            if overall_score >= level_config['min_score']:
                return level
        
        return 1
    
    def _generate_questions_by_difficulty(self, difficulty: int, language: str) -> List[Dict[str, Any]]:
        """
        根据难度生成题目
        
        Args:
            difficulty: 难度等级
            language: 语言类型
            
        Returns:
            题目列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            questions = []
            question_count = 5  # 每次返回5题
            
            # 按类别分配题目
            for category, ratio in self.question_distribution.items():
                category_count = max(1, int(question_count * ratio))
                
                # 查询题目
                sql = """
                SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                       q.question_type, q.level_id,
                       a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                FROM questions q
                LEFT JOIN audio_files a ON q.audio_id = a.id
                WHERE q.language_id = ? AND q.level_id = ?
                ORDER BY RANDOM()
                LIMIT ?
                """
                cursor.execute(sql, (language_id, difficulty, category_count))
                
                for row in cursor.fetchall():
                    question = self._format_question(row)
                    question['category'] = category
                    questions.append(question)
            
            # 调整题目数量
            if len(questions) > question_count:
                questions = random.sample(questions, question_count)
            elif len(questions) < question_count:
                # 补充题目
                while len(questions) < question_count:
                    # 尝试相邻难度的题目
                    for diff in [difficulty, difficulty - 1, difficulty + 1]:
                        if diff < self.difficulty_ranges['min'] or diff > self.difficulty_ranges['max']:
                            continue
                        
                        sql = """
                        SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                               q.question_type, q.level_id,
                               a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                        FROM questions q
                        LEFT JOIN audio_files a ON q.audio_id = a.id
                        WHERE q.language_id = ? AND q.level_id = ?
                        ORDER BY RANDOM()
                        LIMIT 1
                        """
                        cursor.execute(sql, (language_id, diff))
                        row = cursor.fetchone()
                        if row:
                            question = self._format_question(row)
                            question['category'] = 'vocabulary'
                            questions.append(question)
                            break
            
            conn.close()
            return questions
            
        except Exception as e:
            logger.error(f"生成题目失败: {str(e)}")
            return []
    
    def _format_question(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        格式化题目数据
        
        Args:
            row: 数据库行
            
        Returns:
            格式化后的题目
        """
        question = {
            'id': row['id'],
            'content': row['content'],
            'options': json.loads(row['options']) if row['options'] else [],
            'answer': row['answer'],
            'explanation': row['explanation'],
            'question_type': row['question_type'],
            'level_id': row['level_id']
        }
        
        # 添加音频信息
        if row['audio_id']:
            question['audio'] = {
                'id': row['audio_id'],
                'filename': row['filename'],
                'url': row['url'],
                'accent': row['accent'],
                'transcript': row['transcript']
            }
        
        return question
    
    def _check_answer(self, question_id: str, user_answer: str) -> bool:
        """
        检查答案是否正确
        
        Args:
            question_id: 题目ID
            user_answer: 用户答案
            
        Returns:
            是否正确
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT answer, question_type FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            correct_answer = row['answer']
            question_type = row['question_type']
            
            # 根据题型判断答案正确性
            if question_type == 'true_false':
                # 判断题：处理多种可能的正确答案格式
                is_correct = user_answer == correct_answer or \
                            (correct_answer.lower() == 'true' and user_answer in ['true', 'True', '正确', '✓']) or \
                            (correct_answer.lower() == 'false' and user_answer in ['false', 'False', '错误', '✗'])
            elif question_type in ['fill_in_blank', 'short_answer']:
                # 填空题和简答题：允许一定的灵活性
                is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            else:
                # 选择题：精确匹配
                is_correct = user_answer == correct_answer
            
            conn.close()
            return is_correct
            
        except Exception as e:
            logger.error(f"检查答案失败: {str(e)}")
            return False
    
    def save_test_result(self, user_id: int, language: str, final_level: int, 
                        test_data: Dict[str, Any]) -> bool:
        """
        保存测试结果
        
        Args:
            user_id: 用户ID
            language: 语言类型
            final_level: 最终等级
            test_data: 测试数据
            
        Returns:
            是否保存成功
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 保存到用户等级表
            cursor.execute('''
                INSERT OR REPLACE INTO user_levels 
                (user_id, level, level_name, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, final_level, self.levels[final_level]['name']))
            
            # 保存测试记录
            cursor.execute('''
                INSERT INTO level_assessment_tests 
                (user_id, test_type, language, level, test_data, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, 'placement', language, final_level, json.dumps(test_data)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"用户 {user_id} 的 {language} 初次等级评测完成，等级: {final_level}")
            return True
            
        except Exception as e:
            logger.error(f"保存测试结果失败: {str(e)}")
            return False


# 单例实例
_adaptive_placement_test_service = None

def get_adaptive_placement_test_service() -> AdaptivePlacementTestService:
    """获取自适应初次等级评测服务单例"""
    global _adaptive_placement_test_service
    if _adaptive_placement_test_service is None:
        _adaptive_placement_test_service = AdaptivePlacementTestService()
    return _adaptive_placement_test_service
