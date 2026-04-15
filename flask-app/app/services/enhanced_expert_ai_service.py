#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的专家AI分析服务
包含：
1. 优化的学生等级提升判断逻辑
2. 优化的提升试卷出题逻辑
3. 优化的题库要求逻辑
"""

import os
import sys
import sqlite3
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EnhancedExpertAIService:
    """优化后的专家AI分析服务"""
    
    def __init__(self, db_path="app.db"):
        """初始化服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 等级提升配置
        self.level_up_config = {
            'min_answers': 20,              # 最小答题数
            'min_accuracy': 0.75,           # 最低准确率
            'high_level_accuracy': 0.70,    # 高一级题目最低准确率
            'consecutive_exams': 2,         # 连续达标考试次数
            'time_window_days': 30,         # 时间窗口天数
            'min_improvement_trend': 0.05   # 最小提升趋势
        }
        
        # 提升试卷配置
        self.improvement_exam_config = {
            'current_level_weight': 0.40,    # 当前等级题目占比
            'next_level_weight': 0.35,       # 下一级题目占比
            'weak_area_weight': 0.15,         # 薄弱环节题目占比
            'review_weight': 0.10,            # 复习巩固题目占比
            'default_exam_size': 15,          # 默认试卷大小
            'include_listening': True,         # 包含听力题
            'include_writing': False,          # 包含写作题
            'adaptive_difficulty': True        # 自适应难度调整
        }
        
        # 题库要求配置
        self.question_bank_requirements = {
            'min_questions_per_level': 30,    # 每个等级最小题目数
            'min_questions_per_type': 15,     # 每个题型最小题目数
            'question_types': ['multiple_choice', 'fill_in_blank', 'true_false', 'short_answer', 'listening'],
            'min_audio_per_language': 10,     # 每种语言最小音频数
            'accents_required': {
                'english': ['british', 'american'],
                'japanese': ['kanto', 'kansai']
            },
            'difficulty_distribution': {
                1: 0.25,  # N5/初级
                2: 0.25,  # N4/中级入门
                3: 0.20,  # N3/中级
                4: 0.15,  # N2/高级入门
                5: 0.15   # N1/高级
            },
            'freshness_threshold_days': 180    # 题目新鲜度阈值
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
    
    # ========== 1. 优化的学生等级提升判断逻辑 ==========
    
    def analyze_level_eligibility(self, user_id, language='japanese'):
        """
        分析用户是否具备等级提升资格
        
        Args:
            user_id: 用户ID
            language: 语言
            
        Returns:
            等级提升分析结果
        """
        if not self.connect():
            return None
        
        try:
            # 获取用户当前等级
            current_level = self._get_user_level(user_id, language)
            if current_level >= 5:
                return {
                    'eligible': False,
                    'reason': '已达到最高等级',
                    'current_level': current_level
                }
            
            # 1. 检查答题数量
            answer_stats = self._get_user_answer_stats(user_id, language, current_level)
            if answer_stats['total_answers'] < self.level_up_config['min_answers']:
                return {
                    'eligible': False,
                    'reason': f'答题数量不足，需要至少{self.level_up_config["min_answers"]}题',
                    'current_level': current_level,
                    'current_answers': answer_stats['total_answers'],
                    'required_answers': self.level_up_config['min_answers']
                }
            
            # 2. 检查当前等级准确率
            if answer_stats['accuracy'] < self.level_up_config['min_accuracy']:
                return {
                    'eligible': False,
                    'reason': f'当前等级准确率不足，需要至少{self.level_up_config["min_accuracy"]*100:.0f}%',
                    'current_level': current_level,
                    'current_accuracy': answer_stats['accuracy'],
                    'required_accuracy': self.level_up_config['min_accuracy']
                }
            
            # 3. 检查高一级题目表现
            next_level_stats = self._get_user_answer_stats(user_id, language, current_level + 1)
            if next_level_stats['total_answers'] > 0 and \
               next_level_stats['accuracy'] < self.level_up_config['high_level_accuracy']:
                return {
                    'eligible': False,
                    'reason': f'高一级题目准确率不足，需要至少{self.level_up_config["high_level_accuracy"]*100:.0f}%',
                    'current_level': current_level,
                    'next_level_accuracy': next_level_stats['accuracy'],
                    'required_accuracy': self.level_up_config['high_level_accuracy']
                }
            
            # 4. 检查连续达标考试次数
            exam_stats = self._get_user_exam_stats(user_id, language)
            if exam_stats['consecutive_passed'] < self.level_up_config['consecutive_exams']:
                return {
                    'eligible': False,
                    'reason': f'连续达标考试次数不足，需要至少{self.level_up_config["consecutive_exams"]}次',
                    'current_level': current_level,
                    'consecutive_passed': exam_stats['consecutive_passed'],
                    'required_exams': self.level_up_config['consecutive_exams']
                }
            
            # 5. 检查提升趋势
            improvement_trend = self._calculate_improvement_trend(user_id, language)
            if improvement_trend < self.level_up_config['min_improvement_trend']:
                return {
                    'eligible': False,
                    'reason': f'提升趋势不足，需要至少{self.level_up_config["min_improvement_trend"]*100:.1f}%的提升率',
                    'current_level': current_level,
                    'improvement_trend': improvement_trend,
                    'required_trend': self.level_up_config['min_improvement_trend']
                }
            
            # 所有条件都满足
            return {
                'eligible': True,
                'current_level': current_level,
                'next_level': current_level + 1,
                'answer_stats': answer_stats,
                'next_level_stats': next_level_stats,
                'exam_stats': exam_stats,
                'improvement_trend': improvement_trend
            }
            
        except Exception as e:
            print(f"分析等级提升资格失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def _get_user_level(self, user_id, language):
        """获取用户当前等级"""
        try:
            sql = """
            SELECT level FROM user_levels 
            WHERE user_id = ? 
            ORDER BY updated_at DESC LIMIT 1
            """
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except:
            return 1
    
    def _get_user_answer_stats(self, user_id, language, level_id):
        """获取用户在特定等级的答题统计"""
        try:
            time_window = datetime.now() - timedelta(days=self.level_up_config['time_window_days'])
            
            sql = """
            SELECT COUNT(*), SUM(CASE WHEN e.is_correct THEN 1 ELSE 0 END)
            FROM exam_answers e
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ? 
              AND q.level_id = ?
              AND e.created_at >= ?
            """
            self.cursor.execute(sql, (user_id, level_id, time_window))
            total, correct = self.cursor.fetchone()
            
            return {
                'total_answers': total or 0,
                'correct_answers': correct or 0,
                'accuracy': (correct / total) if total > 0 else 0
            }
        except:
            return {'total_answers': 0, 'correct_answers': 0, 'accuracy': 0}
    
    def _get_user_exam_stats(self, user_id, language):
        """获取用户考试统计"""
        try:
            sql = """
            SELECT score, created_at
            FROM exam_performance
            WHERE user_id = ? 
            ORDER BY created_at DESC
            LIMIT 10
            """
            self.cursor.execute(sql, (user_id,))
            exams = self.cursor.fetchall()
            
            consecutive_passed = 0
            for score, _ in exams:
                if score >= 70:  # 70分以上算达标
                    consecutive_passed += 1
                else:
                    break
            
            return {
                'total_exams': len(exams),
                'consecutive_passed': consecutive_passed,
                'recent_scores': [score for score, _ in exams]
            }
        except:
            return {'total_exams': 0, 'consecutive_passed': 0, 'recent_scores': []}
    
    def _calculate_improvement_trend(self, user_id, language):
        """计算提升趋势"""
        try:
            sql = """
            SELECT score, created_at
            FROM exam_performance
            WHERE user_id = ? 
            ORDER BY created_at ASC
            LIMIT 10
            """
            self.cursor.execute(sql, (user_id,))
            exams = self.cursor.fetchall()
            
            if len(exams) < 3:
                return 0.1  # 数据不足时返回默认值
            
            # 计算前半部分和后半部分的平均分差
            mid = len(exams) // 2
            first_half_avg = sum(score for score, _ in exams[:mid]) / mid
            second_half_avg = sum(score for score, _ in exams[mid:]) / (len(exams) - mid)
            
            return (second_half_avg - first_half_avg) / 100  # 转换为小数
        except:
            return 0.1
    
    # ========== 2. 优化的提升试卷出题逻辑 ==========
    
    def generate_improvement_exam(self, user_id, exam_size=None, language='japanese'):
        """
        生成提升试卷
        
        Args:
            user_id: 用户ID
            exam_size: 试卷大小
            language: 语言
            
        Returns:
            提升试卷题目列表
        """
        if exam_size is None:
            exam_size = self.improvement_exam_config['default_exam_size']
        
        # 获取用户当前等级
        current_level = self._get_user_level_simple(user_id)
        
        # 计算各类题目数量
        current_level_count = int(exam_size * self.improvement_exam_config['current_level_weight'])
        next_level_count = int(exam_size * self.improvement_exam_config['next_level_weight'])
        weak_area_count = int(exam_size * self.improvement_exam_config['weak_area_weight'])
        review_count = exam_size - current_level_count - next_level_count - weak_area_count
        
        # 确保数量不为负
        review_count = max(0, review_count)
        
        # 调整数量确保总和
        total = current_level_count + next_level_count + weak_area_count + review_count
        if total != exam_size:
            current_level_count += exam_size - total
        
        # 获取题目
        questions = []
        
        # 1. 当前等级题目（巩固基础）
        if current_level_count > 0:
            current_level_questions = self._get_questions_by_level(
                current_level, current_level_count, language, 
                include_audio=self.improvement_exam_config['include_listening']
            )
            questions.extend(current_level_questions)
        
        # 2. 下一级题目（挑战提升）
        if next_level_count > 0 and current_level < 5:
            next_level_questions = self._get_questions_by_level(
                current_level + 1, next_level_count, language,
                include_audio=self.improvement_exam_config['include_listening']
            )
            questions.extend(next_level_questions)
        
        # 3. 薄弱环节题目（针对性提升）
        if weak_area_count > 0:
            weak_questions = self._get_weak_area_questions(user_id, weak_area_count, language)
            questions.extend(weak_questions)
        
        # 4. 复习题目（巩固之前学过的）
        if review_count > 0 and current_level > 1:
            review_questions = self._get_questions_by_level(
                max(1, current_level - 1), review_count, language,
                include_audio=self.improvement_exam_config['include_listening']
            )
            questions.extend(review_questions)
        
        # 补充题目
        while len(questions) < exam_size:
            additional = self._get_questions_by_level(current_level, 1, language, True)
            if additional:
                questions.extend(additional)
            else:
                break
        
        # 自适应难度调整
        if self.improvement_exam_config['adaptive_difficulty']:
            questions = self._adjust_questions_difficulty(questions, current_level)
        
        # 打乱顺序
        random.shuffle(questions)
        
        return questions[:exam_size]
    
    def _get_user_level_simple(self, user_id):
        """简单获取用户等级"""
        if not self.connect():
            return 1
        try:
            sql = "SELECT level FROM user_levels WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1"
            self.cursor.execute(sql, (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 1
        except:
            return 1
        finally:
            self.close()
    
    def _get_questions_by_level(self, level, count, language, include_audio=False):
        """根据等级获取题目"""
        if not self.connect():
            return []
        try:
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            questions = []
            remaining = count
            
            # 查询题目，包含音频
            sql = """
            SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                   q.question_type, q.level_id,
                   a.id as audio_id, a.filename, a.url, a.accent, a.transcript
            FROM questions q
            LEFT JOIN audio_files a ON q.audio_id = a.id
            WHERE q.language_id = ? AND q.level_id = ?
            """
            
            if not include_audio:
                sql += " AND q.audio_id IS NULL"
            
            sql += " ORDER BY RANDOM() LIMIT ?"
            
            self.cursor.execute(sql, (language_id, level, remaining))
            
            for row in self.cursor.fetchall():
                question = self._format_question(row)
                questions.append(question)
                remaining -= 1
            
            return questions
        except Exception as e:
            print(f"获取等级题目失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def _get_weak_area_questions(self, user_id, count, language):
        """获取薄弱环节题目"""
        # 分析用户薄弱环节
        performance = self._analyze_user_performance_simple(user_id)
        weak_types = performance.get('weak_areas', []) if performance else []
        
        if not self.connect():
            return []
        
        try:
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            questions = []
            remaining = count
            
            for weak_area in weak_types[:3]:
                if remaining <= 0:
                    break
                
                q_type = weak_area.get('question_type')
                level = weak_area.get('level_id', 2)
                
                sql = """
                SELECT q.id, q.content, q.options, q.answer, q.explanation, 
                       q.question_type, q.level_id,
                       a.id as audio_id, a.filename, a.url, a.accent, a.transcript
                FROM questions q
                LEFT JOIN audio_files a ON q.audio_id = a.id
                WHERE q.language_id = ? AND q.question_type = ? AND q.level_id = ?
                ORDER BY RANDOM() LIMIT ?
                """
                
                self.cursor.execute(sql, (language_id, q_type, level, remaining))
                
                for row in self.cursor.fetchall():
                    question = self._format_question(row)
                    questions.append(question)
                    remaining -= 1
            
            return questions
        except:
            return []
        finally:
            self.close()
    
    def _analyze_user_performance_simple(self, user_id):
        """简单分析用户表现"""
        if not self.connect():
            return None
        try:
            sql = """
            SELECT q.question_type, q.level_id, 
                   COUNT(*), SUM(CASE WHEN e.is_correct THEN 1 ELSE 0 END)
            FROM exam_answers e
            JOIN questions q ON e.question_id = q.id
            WHERE e.user_id = ?
            GROUP BY q.question_type, q.level_id
            ORDER BY e.created_at DESC
            LIMIT 50
            """
            self.cursor.execute(sql, (user_id,))
            
            weak_areas = []
            for q_type, level_id, total, correct in self.cursor.fetchall():
                accuracy = correct / total if total > 0 else 0
                if accuracy < 0.6:
                    weak_areas.append({
                        'question_type': q_type,
                        'level_id': level_id,
                        'accuracy': accuracy
                    })
            
            return {'weak_areas': weak_areas}
        except:
            return None
        finally:
            self.close()
    
    def _format_question(self, row):
        """格式化题目"""
        question = {
            'id': row[0],
            'content': row[1],
            'options': json.loads(row[2]) if row[2] else [],
            'answer': row[3],
            'explanation': row[4],
            'question_type': row[5],
            'level_id': row[6]
        }
        
        if row[7]:
            question['audio'] = {
                'id': row[7],
                'filename': row[8],
                'url': row[9],
                'accent': row[10],
                'transcript': row[11]
            }
        
        return question
    
    def _adjust_questions_difficulty(self, questions, target_level):
        """调整题目难度分布"""
        # 简单的难度调整逻辑
        level_counts = defaultdict(int)
        for q in questions:
            level_counts[q['level_id']] += 1
        
        return questions
    
    # ========== 3. 优化的题库要求逻辑 ==========
    
    def analyze_question_bank_health(self, language='japanese'):
        """
        分析题库健康状态
        
        Args:
            language: 语言
            
        Returns:
            题库健康分析报告
        """
        if not self.connect():
            return None
        
        try:
            language_id_map = {'japanese': 1, 'english': 2}
            language_id = language_id_map.get(language, 1)
            
            report = {
                'language': language,
                'overall_health': 'good',
                'issues': [],
                'recommendations': []
            }
            
            # 1. 检查每个等级的题目数量
            level_counts = {}
            for level in range(1, 6):
                sql = "SELECT COUNT(*) FROM questions WHERE language_id = ? AND level_id = ?"
                self.cursor.execute(sql, (language_id, level))
                count = self.cursor.fetchone()[0]
                level_counts[level] = count
                
                if count < self.question_bank_requirements['min_questions_per_level']:
                    report['issues'].append(
                        f'等级{level}题目数量不足：当前{count}题，需要至少{self.question_bank_requirements["min_questions_per_level"]}题'
                    )
                    report['overall_health'] = 'warning'
            
            # 2. 检查难度分布
            total_questions = sum(level_counts.values())
            if total_questions > 0:
                for level, expected_ratio in self.question_bank_requirements['difficulty_distribution'].items():
                    actual_ratio = level_counts.get(level, 0) / total_questions
                    if abs(actual_ratio - expected_ratio) > 0.1:
                        report['issues'].append(
                            f'等级{level}分布不均衡：预期{expected_ratio*100:.0f}%，实际{actual_ratio*100:.0f}%'
                        )
            
            # 3. 检查题型覆盖
            type_counts = {}
            for q_type in self.question_bank_requirements['question_types']:
                sql = "SELECT COUNT(*) FROM questions WHERE language_id = ? AND question_type = ?"
                self.cursor.execute(sql, (language_id, q_type))
                count = self.cursor.fetchone()[0]
                type_counts[q_type] = count
                
                if count < self.question_bank_requirements['min_questions_per_type']:
                    report['issues'].append(
                        f'题型{q_type}数量不足：当前{count}题，需要至少{self.question_bank_requirements["min_questions_per_type"]}题'
                    )
                    report['overall_health'] = 'warning'
            
            # 4. 检查音频资源
            required_accents = self.question_bank_requirements['accents_required'].get(language, [])
            if required_accents:
                for accent in required_accents:
                    sql = """
                    SELECT COUNT(*) FROM audio_files 
                    WHERE language_id = ? AND accent = ?
                    """
                    self.cursor.execute(sql, (language_id, accent))
                    count = self.cursor.fetchone()[0]
                    
                    if count < self.question_bank_requirements['min_audio_per_language']:
                        report['issues'].append(
                            f'{accent}口音音频不足：当前{count}个，需要至少{self.question_bank_requirements["min_audio_per_language"]}个'
                        )
                        report['overall_health'] = 'warning'
            
            # 5. 检查题目新鲜度
            freshness_threshold = datetime.now() - timedelta(
                days=self.question_bank_requirements['freshness_threshold_days']
            )
            sql = """
            SELECT COUNT(*) FROM questions 
            WHERE language_id = ? AND created_at < ?
            """
            self.cursor.execute(sql, (language_id, freshness_threshold))
            stale_count = self.cursor.fetchone()[0]
            
            if stale_count > total_questions * 0.3:
                report['issues'].append(
                    f'题目新鲜度不足：{stale_count}题超过{self.question_bank_requirements["freshness_threshold_days"]}天'
                )
                report['overall_health'] = 'warning'
            
            # 生成建议
            if not report['issues']:
                report['recommendations'].append('题库状态良好，继续保持')
            else:
                report['recommendations'].append('优先补充数量不足的题目类型')
                report['recommendations'].append('优化难度分布')
                report['recommendations'].append('定期更新题目，保持新鲜度')
            
            report['statistics'] = {
                'total_questions': total_questions,
                'level_counts': level_counts,
                'type_counts': type_counts,
                'stale_questions': stale_count
            }
            
            return report
            
        except Exception as e:
            print(f"分析题库健康失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def generate_question_bank_requirements(self, language='japanese'):
        """
        生成题库需求清单
        
        Args:
            language: 语言
            
        Returns:
            题库需求清单
        """
        health_report = self.analyze_question_bank_health(language)
        if not health_report:
            return None
        
        requirements = {
            'language': language,
            'priority_tasks': [],
            'normal_tasks': [],
            'long_term_tasks': []
        }
        
        # 根据健康报告生成需求
        for issue in health_report.get('issues', []):
            if '数量不足' in issue or '音频不足' in issue:
                requirements['priority_tasks'].append(issue)
            elif '分布不均衡' in issue:
                requirements['normal_tasks'].append(issue)
            else:
                requirements['long_term_tasks'].append(issue)
        
        # 添加常规需求
        requirements['normal_tasks'].extend([
            '定期审核题目质量',
            '更新题目解析',
            '收集用户反馈优化题目'
        ])
        
        requirements['long_term_tasks'].extend([
            '开发新题型',
            '建立题目难度自动评估系统',
            '实现题目推荐算法'
        ])
        
        return requirements


# 全局实例
_enhanced_expert_ai_service = None

def get_enhanced_expert_ai_service():
    """获取优化后的专家AI服务实例"""
    global _enhanced_expert_ai_service
    if _enhanced_expert_ai_service is None:
        _enhanced_expert_ai_service = EnhancedExpertAIService()
    return _enhanced_expert_ai_service


if __name__ == "__main__":
    # 测试优化后的专家AI服务
    print("=" * 60)
    print("测试优化后的专家AI服务")
    print("=" * 60)
    
    service = EnhancedExpertAIService()
    
    # 测试题库健康分析
    print("\n[1] 测试题库健康分析...")
    health_report = service.analyze_question_bank_health('japanese')
    if health_report:
        print(f"  整体状态: {health_report['overall_health']}")
        print(f"  问题数量: {len(health_report['issues'])}")
        print(f"  总题目数: {health_report['statistics']['total_questions']}")
    
    # 测试生成提升试卷
    print("\n[2] 测试生成提升试卷...")
    user_id = 1
    questions = service.generate_improvement_exam(user_id, exam_size=10, language='japanese')
    print(f"  生成题目数: {len(questions)}")
    for i, q in enumerate(questions[:3], 1):
        print(f"  题目{i}: 等级{q['level_id']}, 题型{q['question_type']}")
    
    # 测试生成题库需求
    print("\n[3] 测试生成题库需求...")
    requirements = service.generate_question_bank_requirements('japanese')
    if requirements:
        print(f"  高优先级任务: {len(requirements['priority_tasks'])}")
        print(f"  普通任务: {len(requirements['normal_tasks'])}")
        print(f"  长期任务: {len(requirements['long_term_tasks'])}")
    
    print("\n" + "=" * 60)
    print("优化后的专家AI服务测试完成！")
    print("=" * 60)
