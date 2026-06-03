# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI Exam Brain Rules Management
"""

import logging
logger = logging.getLogger(__name__)
import time
import json
import random
import math
import hashlib
from typing import List, Dict, Any, Optional
import os

class AIExamBrainRules:
    """AI脑库出题规则管理类"""

    def __init__(self):
        self.rules = {
            'knowledge_coverage': {
                'enabled': True,
                'min_coverage_rate': 0.7,
                'max_repeated_knowledge': 2,
                'knowledge_weights': {
                    '词汇': 0.4,
                    '语法': 0.4,
                    '阅读': 0.15,
                    '听力': 0.05
                },
                'difficulty_knowledge_mapping': {},
                'importance_weighting': True,
                'core_knowledge_coverage': 0.8
            },
            'difficulty_gradient': {
                'enabled': True,
                'min_gradient': 0.1,
                'max_gradient': 0.5,
                'gradient_type': 'ascending',
                'difficulty_distribution': {
                    1: 0.2,
                    2: 0.3,
                    3: 0.3,
                    4: 0.15,
                    5: 0.05
                },
                'adaptive_gradient': True,
            },
            'question_type_distribution': {
                'enabled': True,
                'default_distribution': {
                    '词汇': 0.4,
                    '语法': 0.4,
                    '阅读': 0.15,
                    '听力': 0.05
                },
                'difficulty_based_distribution': {
                    1: {'词汇': 0.6, '语法': 0.3, '阅读': 0.1, '听力': 0.0},
                    3: {'词汇': 0.4, '语法': 0.4, '阅读': 0.15, '听力': 0.05},
                    4: {'词汇': 0.3, '语法': 0.4, '阅读': 0.2, '听力': 0.1},
                    5: {'词汇': 0.2, '语法': 0.3, '阅读': 0.3, '听力': 0.2}
                },
                'test_purpose_distribution': {
                    'placement': {'词汇': 0.35, '语法': 0.35, '阅读': 0.2, '听力': 0.1},
                    'practice': {'词汇': 0.4, '语法': 0.4, '阅读': 0.1, '听力': 0.1}
                }
            },
            'question_relevance': {
                'enabled': True,
                'max_consecutive_same_topic': 3,
                'topic_transition_smoothness': 0.7,
                'related_knowledge_grouping': True,
                'avoid_redundant_content': True,
                'contextual_coherence': True
            },
            'time_allocation': {
                'enabled': True,
                'base_time_per_question': 60,
                'difficulty_time_factor': {
                    1: 0.8,
                    2: 0.9,
                    3: 1.0,
                    4: 1.2,
                    5: 1.5
                },
                'type_time_factor': {
                    '词汇': 0.8,
                    '语法': 0.9,
                    '阅读': 1.5,
                    '听力': 1.3
                },
                'total_time_buffer': 0.1
            },
            'question_freshness': {
                'enabled': True,
                'min_freshness_score': 0.3,
                'recent_days': 30,
                'max_used_count': 5,
                'used_count_weight': 0.3,
                'feedback_weight': 0.2,
                'performance_weight': 0.2,
                'trending_weight': 0.1,
                'update_frequency': 7
            },
            'personalization': {
                'enabled': True,
                'weakness_weight': 0.6,
                'strength_weight': 0.3,
                'learning_progress_adjustment': True,
                'progress_weight': 0.1,
                'preferred_question_types': {},
                'exam_anxiety_adjustment': True,
                'learning_style_adaptation': True
            },
            'exam_purpose_rules': {
                'enabled': True,
                'rules_by_purpose': {
                    'placement': {
                        'difficulty_coverage': 'full',
                        'core_knowledge_focus': 0.6
                    },
                    'diagnostic': {
                        'difficulty_coverage': 'adaptive',
                        'time_per_question': 120,
                        'core_knowledge_focus': 0.8
                    },
                    'practice': {
                        'difficulty_coverage': 'targeted',
                        'core_knowledge_focus': 0.4
                    },
                    'assessment': {
                        'difficulty_coverage': 'balanced',
                        'core_knowledge_focus': 0.7
                    }
                }
            },
            'ai_brain_integration': {
                'enabled': True,
                'ai_quality_threshold': 0.8,
                'ai_generation_ratio': 0.3,
                'knowledge_enrichment': True,
                'auto_update_rules': True,
                'version_control': True
            }
        }

        self.knowledge_base = {
            '词汇': {
                '基础词汇': 1,
                '核心词汇': 2,
                '进阶词汇': 3,
                '专业词汇': 4,
                '生僻词汇': 5
            },
            '语法': {
                '基础语法': 1,
                '核心语法': 2,
                '进阶语法': 3,
                '复杂语法': 4,
                '特殊语法': 5
            },
            '阅读': {
                '基础阅读': 1,
                '核心阅读': 2,
                '进阶阅读': 3,
                '复杂阅读': 4,
                '专业阅读': 5
            },
            '听力': {
                '基础听力': 1,
                '核心听力': 2,
                '进阶听力': 3,
                '复杂听力': 4,
                '专业听力': 5
            }
        }
        self.last_updated = time.time()

    def get_rule(self, rule_name: str, sub_rule: Optional[str] = None) -> Any:
        """获取规则"""
        if rule_name in self.rules:
            if sub_rule:
                return self.rules[rule_name].get(sub_rule)
            return self.rules[rule_name]
        return None

    def update_rule(self, rule_name: str, sub_rule: str, value: Any):
        """更新规则"""
        if rule_name in self.rules:
            self.rules[rule_name][sub_rule] = value
            self.last_updated = time.time()

    def get_knowledge_points(self, category: str, difficulty: int) -> List[str]:
        """获取指定类别和难度的知识点"""
        if category in self.knowledge_base:
            knowledge_points = []
            for point, point_difficulty in self.knowledge_base[category].items():
                if abs(point_difficulty - difficulty) <= 1:
                    knowledge_points.append(point)
            return knowledge_points
        return []

    def calculate_knowledge_coverage(self, questions: List[Dict[str, Any]]) -> float:
        """计算知识点覆盖率"""
        if not questions:
            return 0.0

        covered_knowledge = set()
        for question in questions:
            if 'knowledge_points' in question:
                covered_knowledge.update(question['knowledge_points'])

        total_knowledge = 0
        for category in self.knowledge_base.values():
            total_knowledge += len(category)

        if total_knowledge == 0:
            return 1.0

        return len(covered_knowledge) / total_knowledge

    def check_difficulty_gradient(self, questions: List[Dict[str, Any]]) -> bool:
        """检查难度梯度是否符合规则"""
        if not self.rules['difficulty_gradient']['enabled'] or len(questions) < 2:
            return True

        difficulty_values = [q['difficulty'] for q in questions]
        gradients = []

        for i in range(1, len(difficulty_values)):
            gradient = abs(difficulty_values[i] - difficulty_values[i-1])
            gradients.append(gradient)

        if not gradients:
            return True

        avg_gradient = sum(gradients) / len(gradients)
        min_gradient = self.rules['difficulty_gradient'].get('min_gradient', 0.1)
        max_gradient = self.rules['difficulty_gradient']['max_gradient']

        return min_gradient <= avg_gradient <= max_gradient

    def adjust_difficulty_gradient(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """调整题目难度梯度"""
        if not self.rules['difficulty_gradient']['enabled'] or len(questions) < 2:
            return questions

        gradient_type = self.rules['difficulty_gradient']['gradient_type']

        if gradient_type == 'ascending':
            return sorted(questions, key=lambda x: x['difficulty'])
        elif gradient_type == 'descending':
            return sorted(questions, key=lambda x: x['difficulty'], reverse=True)
        elif gradient_type == 'mixed':
            sorted_questions = sorted(questions, key=lambda x: x['difficulty'])
            mixed_questions = []

            for i in range(len(sorted_questions)):
                if i % 3 == 0 and i + 1 < len(sorted_questions):
                    mixed_questions.append(sorted_questions[i+1])
                elif i not in mixed_questions:
                    mixed_questions.append(sorted_questions[i])

            return mixed_questions
        else:
            return self._adaptive_difficulty_order(questions)

    def _adaptive_difficulty_order(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """自适应难度排序"""
        category_groups = {}
        for question in questions:
            category = question.get('category', '其他')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(question)

        for category in category_groups:
            category_groups[category].sort(key=lambda x: x['difficulty'])

        ordered_categories = ['词汇', '语法', '阅读', '听力']
        result = []

        for category in ordered_categories:
            if category in category_groups:
                result.extend(category_groups[category])

        for category, group in category_groups.items():
            if category not in ordered_categories:
                result.extend(group)

        return result

    def get_adaptive_difficulty_distribution(self, user_level: int) -> Dict[int, float]:
        """根据用户水平获取自适应难度分布"""
        base_distribution = self.rules['difficulty_gradient']['difficulty_distribution']
        if not self.rules['difficulty_gradient']['adaptive_gradient'] or user_level is None:
            return base_distribution

        adaptive_distribution = {}
        for difficulty, ratio in base_distribution.items():
            distance = abs(difficulty - user_level)
            if distance == 0:
                adaptive_distribution[difficulty] = ratio * 1.3
            elif distance == 1:
                adaptive_distribution[difficulty] = ratio
            elif distance == 2:
                adaptive_distribution[difficulty] = ratio * 0.8
            else:
                adaptive_distribution[difficulty] = ratio * 0.5

        total = sum(adaptive_distribution.values())
        for difficulty in adaptive_distribution:
            adaptive_distribution[difficulty] = adaptive_distribution[difficulty] / total

        return adaptive_distribution

    def calculate_question_freshness(self, question: Dict[str, Any]) -> float:
        """计算题目新鲜感分数"""
        if not self.rules['question_freshness']['enabled']:
            return 1.0

        freshness_score = 1.0

        used_count = question.get('used_count', 0)
        max_used_count = self.rules['question_freshness']['max_used_count']
        if used_count > max_used_count:
            freshness_score *= 0.1
        else:
            freshness_score *= (1 - (used_count / max_used_count) * self.rules['question_freshness']['used_count_weight'])

        if 'last_used_at' in question:
            days_since_last_used = (time.time() - question['last_used_at']) / 86400
            recent_days = self.rules['question_freshness']['recent_days']
            if days_since_last_used < recent_days:
                freshness_score *= (days_since_last_used / recent_days)

        if 'created_at' in question:
            days_since_created = (time.time() - question['created_at']) / 86400
            freshness_score *= min(1.0, 0.8 + 0.2 * math.exp(-days_since_created / 30))

        if 'feedback_score' in question:
            feedback_score = question['feedback_score']
            freshness_score *= (0.8 + 0.2 * feedback_score) * self.rules['question_freshness']['feedback_weight']

        if 'correct_rate' in question:
            correct_rate = question['correct_rate']
            if correct_rate < 0.3 or correct_rate > 0.7:
                freshness_score *= 0.8

        if 'is_trending' in question and question['is_trending']:
            freshness_score *= 1.1

        return max(0.0, min(1.0, freshness_score))

    def calculate_time_allocation(self, questions: List[Dict[str, Any]]) -> float:
        """计算试卷总时间分配(秒)"""
        if not self.rules['time_allocation']['enabled']:
            return len(questions) * 60

        total_time = 0
        base_time = self.rules['time_allocation']['base_time_per_question']

        for question in questions:
            difficulty = question.get('difficulty', 3)
            q_type = question.get('category', '词汇')

            difficulty_factor = self.rules['time_allocation']['difficulty_time_factor'].get(difficulty, 1.0)
            type_factor = self.rules['time_allocation']['type_time_factor'].get(q_type, 1.0)

            question_time = base_time * difficulty_factor * type_factor
            total_time += question_time

        total_time += total_time * self.rules['time_allocation']['total_time_buffer']

        return total_time

    def check_question_relevance(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查题目关联性"""
        if not self.rules['question_relevance']['enabled']:
            return {'compliant': True, 'suggestions': []}

        suggestions = []
        compliant = True

        consecutive_same_topic = 0
        previous_topic = None

        for i, question in enumerate(questions):
            current_topic = question.get('knowledge_points', [None])[0] if question.get('knowledge_points') else None

            if current_topic == previous_topic and current_topic is not None:
                consecutive_same_topic += 1
            else:
                consecutive_same_topic = 1

            if consecutive_same_topic > self.rules['question_relevance']['max_consecutive_same_topic']:
                compliant = False
                suggestions.append(f"题目{i+1}与前{self.rules['question_relevance']['max_consecutive_same_topic']}题主题相同,建议调整")

            previous_topic = current_topic

        content_hashes = set()
        for i, question in enumerate(questions):
            content = question.get('content', '')
            content_hash = hashlib.md5(content.encode()).hexdigest()
            if content_hash in content_hashes:
                compliant = False
                suggestions.append(f"题目{i+1}与其他题目内容重复,建议调整")
            content_hashes.add(content_hash)

        return {
            'compliant': compliant,
            'suggestions': suggestions
        }

    def check_rule_compliance(self, questions: List[Dict[str, Any]], paper_params: Dict[str, Any]) -> Dict[str, Any]:
        """检查题目是否符合所有规则"""
        compliance_result = {
            'overall_compliance': True,
            'rule_compliance': {
                'knowledge_coverage': True,
                'difficulty_gradient': True,
                'question_type_distribution': True,
                'question_freshness': True,
                'question_relevance': True,
                'time_allocation': True,
                'personalization': True,
                'exam_purpose': True
            },
            'suggestions': []
        }

        if self.rules['knowledge_coverage']['enabled']:
            coverage_rate = self.calculate_knowledge_coverage(questions)
            if coverage_rate < self.rules['knowledge_coverage']['min_coverage_rate']:
                compliance_result['rule_compliance']['knowledge_coverage'] = False
                compliance_result['suggestions'].append(f"知识点覆盖率不足:{coverage_rate:.2f} < {self.rules['knowledge_coverage']['min_coverage_rate']}")

        if self.rules['difficulty_gradient']['enabled']:
            if not self.check_difficulty_gradient(questions):
                compliance_result['rule_compliance']['difficulty_gradient'] = False
                compliance_result['overall_compliance'] = False
                compliance_result['suggestions'].append("难度梯度不符合规则,建议调整题目顺序或难度分布")

        if self.rules['question_freshness']['enabled']:
            for question in questions:
                freshness_score = self.calculate_question_freshness(question)
                if freshness_score < self.rules['question_freshness']['min_freshness_score']:
                    compliance_result['rule_compliance']['question_freshness'] = False
                    compliance_result['overall_compliance'] = False
                    compliance_result['suggestions'].append(f"题目{question.get('id', '未知')}新鲜感不足:{freshness_score:.2f}")

        if self.rules['question_relevance']['enabled']:
            relevance_result = self.check_question_relevance(questions)
            if not relevance_result['compliant']:
                compliance_result['rule_compliance']['question_relevance'] = False
                compliance_result['overall_compliance'] = False
                compliance_result['suggestions'].extend(relevance_result['suggestions'])

        return compliance_result

    def get_personalized_distribution(self, user_level: int, user_weaknesses: List[str] = None) -> Dict[str, float]:
        """获取个性化题型分布"""
        if not self.rules['question_type_distribution']['enabled']:
            return {}

        user_level = min(max(user_level, 1), 5)
        base_distribution = self.rules['question_type_distribution']['difficulty_based_distribution'].get(
            user_level,
            self.rules['question_type_distribution']['default_distribution']
        )

        if user_weaknesses and self.rules['personalization']['enabled']:
            personalized_distribution = base_distribution.copy()
            weakness_weight = self.rules['personalization']['weakness_weight']

            for weakness in user_weaknesses:
                for category, weight in base_distribution.items():
                    if weakness in category or any(w in category for w in weakness.split(' ')):
                        personalized_distribution[category] = weight * (1 + weakness_weight)

            total = sum(personalized_distribution.values())
            for category in personalized_distribution:
                personalized_distribution[category] /= total

            return personalized_distribution

        return base_distribution

    def generate_ai_prompt(self, category: str, difficulty: int, knowledge_points: List[str] = None) -> str:
        """生成AI出题提示"""
        if not knowledge_points:
            knowledge_points = self.get_knowledge_points(category, difficulty)

        if not knowledge_points:
            knowledge_part = f"{category}类别"
        else:
            selected_knowledge = random.choice(knowledge_points)
            knowledge_part = f"{category}类别的{selected_knowledge}知识点"
        
        prompt = f"请生成一个{difficulty}级别的{knowledge_part}题目,要求:\n"
        prompt += "1. 题目内容清晰,符合考试规范\n"
        prompt += "2. 包含完整的选项(至少4个,包括1个正确答案)\n"
        prompt += "3. 提供详细的正确答案解析\n"
        prompt += "4. 题目具有一定的挑战性,但符合对应难度级别\n"
        prompt += "5. 避免使用过于生僻或不常见的内容\n"
        prompt += "6. 确保题目没有语法错误或逻辑问题\n"
        if category == '阅读':
            prompt += "7. 阅读材料长度适中,约100-200字\n"
        elif category == '听力':
            prompt += "7. 听力材料应包含对话或独白,长度适中\n"

        return prompt

    def get_purpose_specific_rules(self, test_type: str) -> Dict[str, Any]:
        """获取特定考试目的的规则"""
        if not self.rules['exam_purpose_rules']['enabled']:
            return {}

        return self.rules['exam_purpose_rules']['rules_by_purpose'].get(test_type, {})

    def get_test_results(self, db_conn, limit=1000):
        """从数据库获取测试结果数据"""
        try:
            cursor = db_conn.cursor()
            cursor.execute('''
                SELECT id, user_id, test_type, language, score, total_questions, duration, user_level, created_at
                FROM user_tests
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            test_results = []
            for row in cursor.fetchall():
                test_results.append({
                    'id': row[0],
                    'user_id': row[1],
                    'test_type': row[2],
                    'language': row[3],
                    'score': row[4],
                    'total_questions': row[5],
                    'duration': row[6],
                    'user_level': row[7],
                    'created_at': row[8]
                })

            cursor.close()
            return test_results
        except Exception as e:
            print(f"[ERROR] 获取测试结果失败: {str(e)}")
            return []

    def analyze_test_results(self, test_results):
        """分析测试结果数据"""
        if not test_results:
            return {}

        total_score = sum(result['score'] for result in test_results)
        total_duration = sum(result['duration'] for result in test_results)
        total_questions = sum(result['total_questions'] for result in test_results)

        avg_score = total_score / len(test_results)
        avg_duration = total_duration / len(test_results)
        avg_questions = total_questions / len(test_results)

        difficulty_performance = {}
        test_type_distribution = {}

        for result in test_results:
            test_type = result['test_type']
            test_type_distribution[test_type] = test_type_distribution.get(test_type, 0) + 1

            user_level = result['user_level']
            if user_level not in difficulty_performance:
                difficulty_performance[user_level] = {
                    'count': 0,
                    'total_score': 0
                }
            difficulty_performance[user_level]['count'] += 1
            difficulty_performance[user_level]['total_score'] += result['score']

        for level, data in difficulty_performance.items():
            data['avg_score'] = data['total_score'] / data['count']

        return {
            'total_tests': len(test_results),
            'avg_score': avg_score,
            'avg_duration': avg_duration,
            'avg_questions': avg_questions,
            'difficulty_performance': difficulty_performance,
            'test_type_distribution': test_type_distribution
        }

    def auto_optimize_rules(self, db_conn=None):
        """自动优化规则,基于AI脑库分析和实际测试结果"""
        if not self.rules['ai_brain_integration']['enabled']:
            return

        print("[AI Exam Brain] 开始自动优化出题规则...")

        test_results = self.get_test_results(db_conn) if db_conn else []
        analysis = self.analyze_test_results(test_results)

        self.rules['knowledge_coverage']['knowledge_weights'] = {
            '词汇': 0.4,
            '语法': 0.4,
            '阅读': 0.15,
            '听力': 0.05
        }

        if analysis:
            self.rules['difficulty_gradient']['difficulty_distribution'] = {
                1: 0.15,
                2: 0.25,
                3: 0.35,
                4: 0.15,
                5: 0.1
            }
        else:
            self.rules['difficulty_gradient']['difficulty_distribution'] = {
                1: 0.2,
                2: 0.3,
                3: 0.3,
                4: 0.15,
                5: 0.05
            }

        if analysis.get('test_type_distribution'):
            self.rules['question_type_distribution']['default_distribution'] = {
                '词汇': 0.35,
                '语法': 0.35,
                '阅读': 0.2,
                '听力': 0.1
            }
        else:
            self.rules['question_type_distribution']['default_distribution'] = {
                '词汇': 0.4,
                '语法': 0.4,
                '阅读': 0.15,
                '听力': 0.05
            }

        self.rules['question_freshness']['recent_days'] = 21

        if analysis.get('avg_duration') and analysis.get('avg_questions'):
            avg_time_per_question = analysis['avg_duration'] / analysis['avg_questions']
            self.rules['time_allocation']['base_time_per_question'] = int(avg_time_per_question * 1.1)
        else:
            self.rules['time_allocation']['base_time_per_question'] = 65

        self.rules['difficulty_gradient']['adaptive_gradient'] = True

        self.last_updated = time.time()
        print(f"[AI Exam Brain] 出题规则自动优化完成!")
        print(f"[AI Exam Brain] 分析数据: {json.dumps(analysis, indent=2)}")

    def generate_paper_rules(self, paper_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成特定试卷的出题规则"""
        user_level = paper_params.get('user_level', 3)
        question_count = paper_params.get('question_count', 20)
        test_type = paper_params.get('test_type', 'level')
        language = paper_params.get('language', 'japanese')

        personalized_distribution = self.get_personalized_distribution(user_level)

        type_counts = {}
        for q_type, ratio in personalized_distribution.items():
            type_counts[q_type] = max(1, int(question_count * ratio))

        total_count = sum(type_counts.values())
        if total_count != question_count:
            max_type = max(personalized_distribution, key=personalized_distribution.get)
            type_counts[max_type] += (question_count - total_count)

        difficulty_dist = self.rules['difficulty_gradient']['difficulty_distribution'].copy()

        if test_type == 'placement':
            difficulty_dist = {
                1: 0.2,
                2: 0.2,
                3: 0.2,
                4: 0.2,
                5: 0.2
            }
        elif test_type == 'diagnostic':
            difficulty_dist = {
                1: 0.1,
                2: 0.2,
                3: 0.4,
                4: 0.2,
                5: 0.1
            }

        return {
            'type_counts': type_counts,
            'difficulty_distribution': difficulty_dist,
            'knowledge_coverage_rate': self.rules['knowledge_coverage']['min_coverage_rate'],
            'difficulty_gradient_type': self.rules['difficulty_gradient']['gradient_type'],
            'ai_generation_ratio': self.rules['ai_brain_integration']['ai_generation_ratio'],
        }

ai_exam_brain_rules = AIExamBrainRules()

ai_exam_brain_rules.auto_optimize_rules()
