#!/usr/bin/env python3
"""
基于用户等级的出题服务
负责根据用户等级生成合适难度的题目，实现向上兼容的出题逻辑
"""

import os
import sys
import sqlite3
import json
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LevelBasedQuestionGenerator:
    """基于用户等级的题目生成器"""
    
    def __init__(self, db_path="app.db"):
        """初始化题目生成器"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 题目难度分布配置
        self.difficulty_distribution = {
            'user_level': 0.7,  # 用户等级难度的题目占比
            'user_level_plus_1': 0.2,  # 用户等级+1难度的题目占比
            'user_level_plus_2': 0.1   # 用户等级+2难度的题目占比
        }
        
        # 等级映射
        self.level_map = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        
        # 反向等级映射
        self.reverse_level_map = {
            1: 'beginner',
            2: 'intermediate',
            3: 'advanced',
            4: 'expert'
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
    
    def get_user_level(self, user_id):
        """获取用户等级
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户等级（数字），默认为1（beginner）
        """
        if not self.connect():
            return 1
        
        try:
            # 首先尝试从用户等级表中获取
            sql = """
            SELECT level FROM user_levels WHERE user_id = ?
            """
            self.cursor.execute(sql, (user_id,))
            row = self.cursor.fetchone()
            
            if row:
                return row[0]
            
            # 如果没有等级记录，尝试从用户考试表现中计算
            sql = """
            SELECT AVG(difficulty_level) FROM exam_performance WHERE user_id = ?
            """
            self.cursor.execute(sql, (user_id,))
            row = self.cursor.fetchone()
            
            if row and row[0]:
                # 根据平均难度计算等级
                avg_difficulty = row[0]
                if avg_difficulty >= 3.5:
                    return 4  # expert
                elif avg_difficulty >= 2.5:
                    return 3  # advanced
                elif avg_difficulty >= 1.5:
                    return 2  # intermediate
            
            # 默认返回1（beginner）
            return 1
        except Exception as e:
            print(f"获取用户等级失败: {str(e)}")
            return 1
        finally:
            self.close()
    
    def update_user_level(self, user_id, new_level):
        """更新用户等级
        
        Args:
            user_id: 用户ID
            new_level: 新等级（数字）
            
        Returns:
            是否更新成功
        """
        if not self.connect():
            return False
        
        try:
            # 确保等级在有效范围内
            new_level = max(1, min(4, new_level))
            
            # 检查是否已存在等级记录
            sql = """
            SELECT id FROM user_levels WHERE user_id = ?
            """
            self.cursor.execute(sql, (user_id,))
            row = self.cursor.fetchone()
            
            if row:
                # 更新现有记录
                sql = """
                UPDATE user_levels SET level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """
                self.cursor.execute(sql, (new_level, user_id))
            else:
                # 插入新记录
                sql = """
                INSERT INTO user_levels (user_id, level, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                self.cursor.execute(sql, (user_id, new_level))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"更新用户等级失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def generate_exam(self, user_id, exam_size=10, language='japanese'):
        """根据用户等级生成考试题目
        
        Args:
            user_id: 用户ID
            exam_size: 考试题目数量
            language: 语言（japanese或english）
            
        Returns:
            题目列表
        """
        # 获取用户等级
        user_level = self.get_user_level(user_id)
        
        # 计算各难度级别的题目数量
        user_level_count = int(exam_size * self.difficulty_distribution['user_level'])
        user_level_plus_1_count = int(exam_size * self.difficulty_distribution['user_level_plus_1'])
        user_level_plus_2_count = exam_size - user_level_count - user_level_plus_1_count
        
        # 确保数量不为负数
        user_level_plus_2_count = max(0, user_level_plus_2_count)
        
        # 调整数量，确保总和为exam_size
        if user_level_count + user_level_plus_1_count + user_level_plus_2_count != exam_size:
            user_level_count += exam_size - (user_level_count + user_level_plus_1_count + user_level_plus_2_count)
        
        # 生成题目
        questions = []
        
        # 获取用户等级难度的题目
        if user_level_count > 0:
            level_questions = self._get_questions_by_level(user_level, user_level_count, language)
            questions.extend(level_questions)
        
        # 获取用户等级+1难度的题目
        if user_level_plus_1_count > 0 and user_level < 4:
            level_plus_1_questions = self._get_questions_by_level(user_level + 1, user_level_plus_1_count, language)
            questions.extend(level_plus_1_questions)
        
        # 获取用户等级+2难度的题目
        if user_level_plus_2_count > 0 and user_level < 3:
            level_plus_2_questions = self._get_questions_by_level(user_level + 2, user_level_plus_2_count, language)
            questions.extend(level_plus_2_questions)
        
        # 如果题目数量不足，补充用户等级难度的题目
        while len(questions) < exam_size:
            additional_questions = self._get_questions_by_level(user_level, 1, language)
            if additional_questions:
                questions.extend(additional_questions)
            else:
                break
        
        # 打乱题目顺序
        random.shuffle(questions)
        
        return questions
    
    def _get_questions_by_level(self, level, count, language):
        """根据难度等级获取题目
        
        Args:
            level: 难度等级（数字）
            count: 需要的题目数量
            language: 语言
            
        Returns:
            题目列表
        """
        if not self.connect():
            return []
        
        try:
            # 语言ID映射
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            # 查询题目，包含音频信息
            sql = """
            SELECT q.id, q.content, q.options, q.answer, q.explanation, q.question_type, 
                   a.id as audio_id, a.filename, a.url, a.accent, a.transcript
            FROM questions q
            LEFT JOIN audio_files a ON q.audio_id = a.id
            WHERE q.level_id = ? AND q.language_id = ?
            ORDER BY RANDOM()
            LIMIT ?
            """
            self.cursor.execute(sql, (level, language_id, count))
            
            questions = []
            for row in self.cursor.fetchall():
                question = {
                    'id': row[0],
                    'content': row[1],
                    'options': json.loads(row[2]) if row[2] else [],
                    'answer': row[3],
                    'explanation': row[4],
                    'question_type': row[5],
                    'level_id': level
                }
                
                # 添加音频信息
                if row[6]:  # 如果有音频ID
                    question['audio'] = {
                        'id': row[6],
                        'filename': row[7],
                        'url': row[8],
                        'accent': row[9],
                        'transcript': row[10]
                    }
                
                questions.append(question)
            
            return questions
        except Exception as e:
            print(f"获取题目失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def analyze_user_performance(self, user_id, exam_id):
        """分析用户考试表现并更新等级
        
        Args:
            user_id: 用户ID
            exam_id: 考试ID
            
        Returns:
            分析结果
        """
        if not self.connect():
            return None
        
        try:
            # 获取考试表现
            sql = """
            SELECT score, difficulty_level, correct_answers, total_questions
            FROM exam_performance
            WHERE user_id = ? AND exam_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
            self.cursor.execute(sql, (user_id, exam_id))
            row = self.cursor.fetchone()
            
            if not row:
                return None
            
            score, difficulty_level, correct_answers, total_questions = row
            
            # 计算准确率
            accuracy = correct_answers / total_questions if total_questions > 0 else 0
            
            # 分析结果
            analysis = {
                'score': score,
                'accuracy': accuracy,
                'difficulty_level': difficulty_level,
                'recommendations': []
            }
            
            # 根据表现更新用户等级
            current_level = self.get_user_level(user_id)
            new_level = current_level
            
            # 如果准确率高且难度适中，考虑提升等级
            if accuracy >= 0.8 and difficulty_level >= current_level:
                if current_level < 4:
                    new_level = current_level + 1
                    analysis['recommendations'].append(f'表现优秀，等级已提升至 {self.reverse_level_map[new_level]}')
            # 如果准确率低且难度高于当前等级，考虑降低等级
            elif accuracy < 0.4 and difficulty_level > current_level:
                if current_level > 1:
                    new_level = current_level - 1
                    analysis['recommendations'].append(f'建议加强基础，等级调整至 {self.reverse_level_map[new_level]}')
            elif accuracy >= 0.6:
                analysis['recommendations'].append('表现良好，继续保持')
            else:
                analysis['recommendations'].append('建议加强练习，提高准确率')
            
            # 更新用户等级
            if new_level != current_level:
                self.update_user_level(user_id, new_level)
            
            return analysis
        except Exception as e:
            print(f"分析用户表现失败: {str(e)}")
            return None
        finally:
            self.close()

# 全局基于等级的题目生成器实例
level_based_generator = None

def get_level_based_generator():
    """获取基于等级的题目生成器实例"""
    global level_based_generator
    if level_based_generator is None:
        level_based_generator = LevelBasedQuestionGenerator()
    return level_based_generator

if __name__ == "__main__":
    # 测试基于等级的题目生成器
    generator = LevelBasedQuestionGenerator()
    
    # 测试获取用户等级
    user_id = 1
    level = generator.get_user_level(user_id)
    print(f"用户等级: {level} ({generator.reverse_level_map[level]})")
    
    # 测试生成考试题目
    print("\n生成考试题目...")
    questions = generator.generate_exam(user_id, exam_size=10, language='japanese')
    print(f"生成题目数量: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"题目 {i}: 难度等级 {q['level_id']}, 题型 {q['question_type']}")
        print(f"内容: {q['content'][:50]}...")
        print()
    
    # 测试更新用户等级
    print("\n更新用户等级...")
    result = generator.update_user_level(user_id, 2)
    print(f"更新结果: {result}")
    
    # 测试分析用户表现
    print("\n分析用户表现...")
    analysis = generator.analyze_user_performance(user_id, 1)
    if analysis:
        print(f"分析结果: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
