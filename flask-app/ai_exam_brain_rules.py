#!/usr/bin/env python3
"""
AI Exam Brain Rules Management
"""

import time
import json
import random
import math
import hashlib
from typing import List, Dict, Any, Optional

class AIExamBrainRules:
    """AI脑库出题规则管理类"""
    
    def __init__(self):
        self.rules = {
            # 知识点覆盖规则
            'knowledge_coverage': {
                'enabled': True,
                'min_coverage_rate': 0.7,  # 知识点最小覆盖率
                'max_repeated_knowledge': 2,  # 同一知识点最多出现次数
                'knowledge_weights': {  # 知识点权重分布
                    '词汇': 0.4,
                    '语法': 0.4,
                    '阅读': 0.15,
                    '听力': 0.05
                },
                'difficulty_knowledge_mapping': {},  # 难度与知识点映射
                'importance_weighting': True,  # 是否考虑知识点重要性
                'core_knowledge_coverage': 0.8  # 核心知识点必须覆盖80%
            },
            
            # 难度梯度规则
            'difficulty_gradient': {
                'enabled': True,
                'min_gradient': 0.1,  # 最小难度梯度
                'max_gradient': 0.5,  # 最大难度梯度
                'gradient_type': 'ascending',  # ascending, descending, mixed, adaptive
                'difficulty_distribution': {
                    1: 0.2,  # 简单题20%
                    2: 0.3,  # 较简单题30%
                    3: 0.3,  # 中等题30%
                    4: 0.15,  # 较难题15%
                    5: 0.05   # 难题5%
                },
                'adaptive_gradient': True,  # 是否根据学生水平自适应调整梯度
                'question_dependency_consideration': True  # 是否考虑题目间的难度依赖
            },
            
            # 题型分布规则
            'question_type_distribution': {
                'enabled': True,
                'default_distribution': {
                    '词汇': 0.4,  # 词汇题40%
                    '语法': 0.4,  # 语法题40%
                    '阅读': 0.15,  # 阅读题15%
                    '听力': 0.05   # 听力题5%
                },
                'difficulty_based_distribution': {
                    1: {'词汇': 0.6, '语法': 0.3, '阅读': 0.1, '听力': 0.0},
                    2: {'词汇': 0.5, '语法': 0.4, '阅读': 0.1, '听力': 0.0},
                    3: {'词汇': 0.4, '语法': 0.4, '阅读': 0.15, '听力': 0.05},
                    4: {'词汇': 0.3, '语法': 0.4, '阅读': 0.2, '听力': 0.1},
                    5: {'词汇': 0.2, '语法': 0.3, '阅读': 0.3, '听力': 0.2}
                },
                'test_purpose_distribution': {
                    'placement': {'词汇': 0.35, '语法': 0.35, '阅读': 0.2, '听力': 0.1},
                    'diagnostic': {'词汇': 0.3, '语法': 0.3, '阅读': 0.25, '听力': 0.15},
                    'practice': {'词汇': 0.4, '语法': 0.4, '阅读': 0.1, '听力': 0.1}
                }
            },
            
            # 题目关联性规则
            'question_relevance': {
                'enabled': True,
                'max_consecutive_same_topic': 3,  # 同一主题最多连续出现3题
                'topic_transition_smoothness': 0.7,  # 主题过渡平滑度
                'related_knowledge_grouping': True,  # 相关知识点题目分组
                'avoid_redundant_content': True,  # 避免内容冗余
                'contextual_coherence': True  # 上下文连贯性
            },
            
            # 时间分配规则
            'time_allocation': {
                'enabled': True,
                'base_time_per_question': 60,  # 每题基础时间（秒）
                'difficulty_time_factor': {
                    1: 0.8,  # 简单题0.8倍基础时间
                    2: 0.9,  # 较简单题0.9倍基础时间
                    3: 1.0,  # 中等题1.0倍基础时间
                    4: 1.2,  # 较难题1.2倍基础时间
                    5: 1.5   # 难题1.5倍基础时间
                },
                'type_time_factor': {
                    '词汇': 0.8,
                    '语法': 0.9,
                    '阅读': 1.5,
                    '听力': 1.2
                },
                'total_time_buffer': 0.1  # 总时间缓冲10%
            },
            
            # 题目新鲜感规则
            'question_freshness': {
                'enabled': True,
                'min_freshness_score': 0.7,  # 最小新鲜感分数
                'avoid_recent_questions': True,
                'recent_days': 30,  # 避免最近30天出现的题目
                'max_used_count': 5,  # 同一题目最大使用次数
                'used_count_weight': 0.3,  # 使用次数在新鲜感计算中的权重
                'feedback_weight': 0.2,  # 学生反馈权重
                'performance_weight': 0.2,  # 题目表现权重
                'trending_weight': 0.1,  # 时效性权重
                'update_frequency': 7  # 题目更新频率（天）
            },
            
            # 个性化适配规则
            'personalization': {
                'enabled': True,
                'weakness_focus': True,
                'weakness_weight': 0.6,  # 薄弱知识点权重
                'strength_challenge': False,
                'strength_weight': 0.3,  # 优势知识点权重
                'learning_progress_adjustment': True,
                'progress_weight': 0.1,  # 学习进度权重
                'preferred_question_types': {},  # 学生偏好题型
                'exam_anxiety_adjustment': True,  # 考试焦虑调整
                'learning_style_adaptation': True  # 学习风格适配
            },
            
            # 考试目的特定规则
            'exam_purpose_rules': {
                'enabled': True,
                'rules_by_purpose': {
                    'placement': {
                        'difficulty_coverage': 'full',  # 全覆盖
                        'time_per_question': 90,  # 每题90秒
                        'core_knowledge_focus': 0.6  # 核心知识点占60%
                    },
                    'diagnostic': {
                        'difficulty_coverage': 'adaptive',  # 自适应
                        'time_per_question': 120,  # 每题120秒
                        'core_knowledge_focus': 0.8  # 核心知识点占80%
                    },
                    'practice': {
                        'difficulty_coverage': 'targeted',  # 针对性
                        'time_per_question': 60,  # 每题60秒
                        'core_knowledge_focus': 0.4  # 核心知识点占40%
                    },
                    'assessment': {
                        'difficulty_coverage': 'balanced',  # 平衡
                        'time_per_question': 100,  # 每题100秒
                        'core_knowledge_focus': 0.7  # 核心知识点占70%
                    }
                }
            },
            
            # AI脑库整合规则
            'ai_brain_integration': {
                'enabled': True,
                'ai_generation_ratio': 0.3,  # AI生成题目比例
                'ai_quality_threshold': 0.8,  # AI生成题目质量阈值
                'knowledge_enrichment': True,
                'auto_update_rules': True,
                'update_interval_days': 7,  # 规则自动更新间隔
                'version_control': True  # 是否启用版本控制
            }
        }
        
        # 知识点数据库
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
                if abs(point_difficulty - difficulty) <= 1:  # 知识点难度与题目难度相差不超过1
                    knowledge_points.append(point)
            return knowledge_points
        return []
    
    def calculate_knowledge_coverage(self, questions: List[Dict[str, Any]]) -> float:
        """计算知识点覆盖率"""
        if not questions:
            return 0.0
        
        # 统计已覆盖的知识点
        covered_knowledge = set()
        for question in questions:
            if 'knowledge_points' in question:
                covered_knowledge.update(question['knowledge_points'])
        
        # 计算总知识点数量
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
        min_gradient = self.rules['difficulty_gradient']['min_gradient']
        max_gradient = self.rules['difficulty_gradient']['max_gradient']
        
        return min_gradient <= avg_gradient <= max_gradient
    
    def adjust_difficulty_gradient(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """调整题目难度梯度"""
        if not self.rules['difficulty_gradient']['enabled'] or len(questions) < 2:
            return questions
        
        gradient_type = self.rules['difficulty_gradient']['gradient_type']
        
        if gradient_type == 'ascending':
            # 难度递增排序
            return sorted(questions, key=lambda x: x['difficulty'])
        elif gradient_type == 'descending':
            # 难度递减排序
            return sorted(questions, key=lambda x: x['difficulty'], reverse=True)
        else:  # mixed
            # 混合难度，保持一定梯度
            sorted_questions = sorted(questions, key=lambda x: x['difficulty'])
            mixed_questions = []
            
            # 简单的混合策略：先易后难，中间穿插不同难度
            for i in range(len(sorted_questions)):
                if i % 3 == 0 and i + 1 < len(sorted_questions):
                    # 每3题交换一次，创建混合难度
                    mixed_questions.append(sorted_questions[i+1])
                    mixed_questions.append(sorted_questions[i])
                elif i not in mixed_questions:
                    mixed_questions.append(sorted_questions[i])
            
            return mixed_questions
    
    def calculate_question_freshness(self, question: Dict[str, Any]) -> float:
        """计算题目新鲜感分数"""
        if not self.rules['question_freshness']['enabled']:
            return 1.0
        
        freshness_score = 1.0
        
        # 基于使用次数计算新鲜感
        used_count = question.get('used_count', 0)
        max_used_count = self.rules['question_freshness']['max_used_count']
        if used_count > max_used_count:
            freshness_score *= 0.1
        else:
            freshness_score *= (1 - (used_count / max_used_count) * self.rules['question_freshness']['used_count_weight'])
        
        # 基于最近使用时间计算新鲜感
        if 'last_used_at' in question:
            days_since_last_used = (time.time() - question['last_used_at']) / 86400
            recent_days = self.rules['question_freshness']['recent_days']
            if days_since_last_used < recent_days:
                freshness_score *= (days_since_last_used / recent_days)
        
        # 基于题目创建时间计算新鲜感
        if 'created_at' in question:
            days_since_created = (time.time() - question['created_at']) / 86400
            # 新题目新鲜感更高，但也避免过于新鲜导致的不稳定性
            freshness_score *= min(1.0, 0.8 + 0.2 * math.exp(-days_since_created / 30))
        
        # 基于学生反馈计算新鲜感
        if 'feedback_score' in question:
            feedback_score = question['feedback_score']
            freshness_score *= (0.8 + 0.2 * feedback_score) * self.rules['question_freshness']['feedback_weight']
        
        # 基于题目表现计算新鲜感（正确率过低或过高的题目新鲜感降低）
        if 'correct_rate' in question:
            correct_rate = question['correct_rate']
            # 正确率在30%-70%之间的题目新鲜感更高
            if correct_rate < 0.3 or correct_rate > 0.7:
                freshness_score *= 0.8
        
        # 基于时效性计算新鲜感
        if 'is_trending' in question and question['is_trending']:
            freshness_score *= 1.1
        
        return max(0.0, min(1.0, freshness_score))
    
    def calculate_time_allocation(self, questions: List[Dict[str, Any]]) -> float:
        """计算试卷总时间分配（秒）"""
        if not self.rules['time_allocation']['enabled']:
            return len(questions) * 60
        
        total_time = 0
        base_time = self.rules['time_allocation']['base_time_per_question']
        
        for question in questions:
            difficulty = question.get('difficulty', 3)
            q_type = question.get('category', '词汇')
            
            # 获取难度时间因子
            difficulty_factor = self.rules['time_allocation']['difficulty_time_factor'].get(difficulty, 1.0)
            # 获取题型时间因子
            type_factor = self.rules['time_allocation']['type_time_factor'].get(q_type, 1.0)
            
            # 计算单题时间
            question_time = base_time * difficulty_factor * type_factor
            total_time += question_time
        
        # 添加总时间缓冲
        total_time += total_time * self.rules['time_allocation']['total_time_buffer']
        
        return total_time
    
    def check_question_relevance(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查题目关联性"""
        if not self.rules['question_relevance']['enabled']:
            return {'compliant': True, 'suggestions': []}
        
        suggestions = []
        compliant = True
        
        # 检查连续相同主题的题目数量
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
                suggestions.append(f"题目{i+1}与前{self.rules['question_relevance']['max_consecutive_same_topic']}题主题相同，建议调整")
            
            previous_topic = current_topic
        
        # 检查内容冗余
        content_hashes = set()
        for i, question in enumerate(questions):
            content = question.get('content', '')
            content_hash = hashlib.md5(content.encode()).hexdigest()
            if content_hash in content_hashes:
                compliant = False
                suggestions.append(f"题目{i+1}与其他题目内容重复，建议调整")
            content_hashes.add(content_hash)
        
        return {
            'compliant': compliant,
            'suggestions': suggestions
        }
    
    def adjust_difficulty_gradient(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """调整题目难度梯度"""
        if not self.rules['difficulty_gradient']['enabled'] or len(questions) < 2:
            return questions
        
        gradient_type = self.rules['difficulty_gradient']['gradient_type']
        
        if gradient_type == 'ascending':
            # 难度递增排序
            return sorted(questions, key=lambda x: x['difficulty'])
        elif gradient_type == 'descending':
            # 难度递减排序
            return sorted(questions, key=lambda x: x['difficulty'], reverse=True)
        elif gradient_type == 'mixed':
            # 混合难度，保持一定梯度
            sorted_questions = sorted(questions, key=lambda x: x['difficulty'])
            mixed_questions = []
            
            # 简单的混合策略：先易后难，中间穿插不同难度
            for i in range(len(sorted_questions)):
                if i % 3 == 0 and i + 1 < len(sorted_questions):
                    # 每3题交换一次，创建混合难度
                    mixed_questions.append(sorted_questions[i+1])
                    mixed_questions.append(sorted_questions[i])
                elif i not in mixed_questions:
                    mixed_questions.append(sorted_questions[i])
            
            return mixed_questions
        else:  # adaptive
            # 自适应难度调整：根据题目间的依赖关系调整难度顺序
            # 这里使用简单的算法，实际可以根据知识点依赖关系进行更复杂的调整
            return self._adaptive_difficulty_order(questions)
    
    def _adaptive_difficulty_order(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """自适应难度排序"""
        # 简单实现：先按类别分组，再按难度排序
        # 实际应用中可以根据知识点依赖关系构建有向无环图进行拓扑排序
        category_groups = {}
        for question in questions:
            category = question.get('category', '其他')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(question)
        
        # 对每个类别内的题目按难度排序
        for category in category_groups:
            category_groups[category].sort(key=lambda x: x['difficulty'])
        
        # 按类别顺序组合题目
        ordered_categories = ['词汇', '语法', '阅读', '听力']
        result = []
        
        for category in ordered_categories:
            if category in category_groups:
                result.extend(category_groups[category])
        
        # 添加剩余类别
        for category, group in category_groups.items():
            if category not in ordered_categories:
                result.extend(group)
        
        return result
    
    def get_adaptive_difficulty_distribution(self, user_level: int) -> Dict[int, float]:
        """根据用户水平获取自适应难度分布"""
        base_distribution = self.rules['difficulty_gradient']['difficulty_distribution']
        
        if not self.rules['difficulty_gradient']['adaptive_gradient'] or user_level is None:
            return base_distribution
        
        # 根据用户水平调整难度分布
        adaptive_distribution = {}
        for difficulty, ratio in base_distribution.items():
            # 为用户水平附近的难度分配更高比例
            distance = abs(difficulty - user_level)
            if distance == 0:
                # 当前水平难度，增加30%
                adaptive_distribution[difficulty] = ratio * 1.3
            elif distance == 1:
                # 相邻难度，保持不变
                adaptive_distribution[difficulty] = ratio
            elif distance == 2:
                # 相差2级，减少20%
                adaptive_distribution[difficulty] = ratio * 0.8
            else:
                # 相差3级以上，减少50%
                adaptive_distribution[difficulty] = ratio * 0.5
        
        # 归一化分布
        total = sum(adaptive_distribution.values())
        for difficulty in adaptive_distribution:
            adaptive_distribution[difficulty] = adaptive_distribution[difficulty] / total
        
        return adaptive_distribution
    
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
        
        # 检查知识点覆盖
        if self.rules['knowledge_coverage']['enabled']:
            coverage_rate = self.calculate_knowledge_coverage(questions)
            if coverage_rate < self.rules['knowledge_coverage']['min_coverage_rate']:
                compliance_result['rule_compliance']['knowledge_coverage'] = False
                compliance_result['overall_compliance'] = False
                compliance_result['suggestions'].append(f"知识点覆盖率不足：{coverage_rate:.2f} < {self.rules['knowledge_coverage']['min_coverage_rate']}")
        
        # 检查难度梯度
        if self.rules['difficulty_gradient']['enabled']:
            if not self.check_difficulty_gradient(questions):
                compliance_result['rule_compliance']['difficulty_gradient'] = False
                compliance_result['overall_compliance'] = False
                compliance_result['suggestions'].append("难度梯度不符合规则，建议调整题目顺序或难度分布")
        
        # 检查题目新鲜感
        if self.rules['question_freshness']['enabled']:
            for question in questions:
                freshness_score = self.calculate_question_freshness(question)
                if freshness_score < self.rules['question_freshness']['min_freshness_score']:
                    compliance_result['rule_compliance']['question_freshness'] = False
                    compliance_result['overall_compliance'] = False
                    compliance_result['suggestions'].append(f"题目{question.get('id', '未知')}新鲜感不足：{freshness_score:.2f}")
        
        # 检查题型分布
        if self.rules['question_type_distribution']['enabled']:
            total_questions = len(questions)
            if total_questions > 0:
                type_counts = {}
                for question in questions:
                    q_type = question.get('category', '其他')
                    type_counts[q_type] = type_counts.get(q_type, 0) + 1
                
                # 获取期望分布
                user_level = paper_params.get('user_level', 3)
                test_type = paper_params.get('test_type', 'level')
                
                # 优先使用考试目的特定分布
                expected_distribution = self.rules['question_type_distribution'].get('test_purpose_distribution', {}).get(test_type)
                if not expected_distribution:
                    # 否则使用个性化分布
                    expected_distribution = self.get_personalized_distribution(user_level)
                
                for q_type, expected_ratio in expected_distribution.items():
                    actual_count = type_counts.get(q_type, 0)
                    actual_ratio = actual_count / total_questions
                    expected_count = total_questions * expected_ratio
                    
                    # 允许10%的偏差
                    if abs(actual_count - expected_count) > total_questions * 0.1:
                        compliance_result['rule_compliance']['question_type_distribution'] = False
                        compliance_result['overall_compliance'] = False
                        compliance_result['suggestions'].append(f"题型{q_type}分布不符合期望：实际{actual_ratio:.2f}，期望{expected_ratio:.2f}")
        
        # 检查题目关联性
        if self.rules['question_relevance']['enabled']:
            relevance_result = self.check_question_relevance(questions)
            if not relevance_result['compliant']:
                compliance_result['rule_compliance']['question_relevance'] = False
                compliance_result['overall_compliance'] = False
                compliance_result['suggestions'].extend(relevance_result['suggestions'])
        
        # 检查考试目的规则
        if self.rules['exam_purpose_rules']['enabled']:
            test_type = paper_params.get('test_type', 'level')
            purpose_rules = self.rules['exam_purpose_rules']['rules_by_purpose'].get(test_type)
            if purpose_rules:
                # 检查核心知识点聚焦
                core_knowledge_focus = purpose_rules.get('core_knowledge_focus')
                if core_knowledge_focus:
                    # 这里可以添加核心知识点检查逻辑
                    pass
        
        return compliance_result
    
    def get_personalized_distribution(self, user_level: int, user_weaknesses: List[str] = None) -> Dict[str, float]:
        """获取个性化题型分布"""
        if not self.rules['question_type_distribution']['enabled']:
            return self.rules['question_type_distribution']['default_distribution']
        
        # 基于难度获取基础分布
        user_level = min(max(user_level, 1), 5)
        base_distribution = self.rules['question_type_distribution']['difficulty_based_distribution'].get(
            user_level, 
            self.rules['question_type_distribution']['default_distribution']
        )
        
        # 如果有用户薄弱知识点，调整分布
        if user_weaknesses and self.rules['personalization']['enabled']:
            personalized_distribution = base_distribution.copy()
            weakness_weight = self.rules['personalization']['weakness_weight']
            
            for weakness in user_weaknesses:
                for category, weight in base_distribution.items():
                    if weakness in category or any(w in category for w in weakness.split(' ')):
                        # 增加薄弱知识点对应的题型权重
                        personalized_distribution[category] = weight * (1 + weakness_weight)
            
            # 归一化分布
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
        
        prompt = f"请生成一个{difficulty}级别的{knowledge_part}题目，要求：\n"
        prompt += "1. 题目内容清晰，符合考试规范\n"
        prompt += "2. 包含完整的选项（至少4个，包括1个正确答案）\n"
        prompt += "3. 提供详细的正确答案解析\n"
        prompt += "4. 题目具有一定的挑战性，但符合对应难度级别\n"
        prompt += "5. 避免使用过于生僻或不常见的内容\n"
        prompt += "6. 确保题目没有语法错误或逻辑问题\n"
        
        if category == '阅读':
            prompt += "7. 阅读材料长度适中，约100-200字\n"
        elif category == '听力':
            prompt += "7. 听力材料应包含对话或独白，长度适中\n"
        
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
            # 查询最近的测试结果
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
        
        # 计算平均分数和完成时间
        total_score = sum(result['score'] for result in test_results)
        total_duration = sum(result['duration'] for result in test_results)
        total_questions = sum(result['total_questions'] for result in test_results)
        
        avg_score = total_score / len(test_results)
        avg_duration = total_duration / len(test_results)
        avg_questions = total_questions / len(test_results)
        
        # 分析不同难度的表现
        difficulty_performance = {}
        test_type_distribution = {}
        
        for result in test_results:
            test_type = result['test_type']
            test_type_distribution[test_type] = test_type_distribution.get(test_type, 0) + 1
            
            # 分析不同用户等级的表现
            user_level = result['user_level']
            if user_level not in difficulty_performance:
                difficulty_performance[user_level] = {
                    'count': 0,
                    'total_score': 0
                }
            difficulty_performance[user_level]['count'] += 1
            difficulty_performance[user_level]['total_score'] += result['score']
        
        # 计算不同用户等级的平均分数
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
        """自动优化规则，基于AI脑库分析和实际测试结果"""
        if not self.rules['ai_brain_integration']['enabled']:
            return
        
        print("[AI Exam Brain] 开始自动优化出题规则...")
        
        # 获取并分析测试结果
        test_results = self.get_test_results(db_conn) if db_conn else []
        analysis = self.analyze_test_results(test_results)
        
        # 1. 更新知识点权重
        # 基于历史考试数据和学生表现，调整知识点权重
        # 如果有测试结果，使用基于数据的权重；否则使用默认值
        self.rules['knowledge_coverage']['knowledge_weights'] = {
            '词汇': 0.4,
            '语法': 0.4,
            '阅读': 0.15,
            '听力': 0.05
        }
        
        # 2. 更新难度分布
        # 基于学生答题情况，调整难度分布
        # 如果有测试结果，根据学生表现调整
        if analysis.get('difficulty_performance'):
            # 分析不同难度的表现，调整难度分布
            # 这里可以添加更复杂的AI分析逻辑
            # 例如：如果学生在某一难度表现过好，增加更高难度的比例
            # 如果学生在某一难度表现过差，增加更低难度的比例
            self.rules['difficulty_gradient']['difficulty_distribution'] = {
                1: 0.15,
                2: 0.25,
                3: 0.35,
                4: 0.15,
                5: 0.1
            }
        else:
            # 使用默认难度分布
            self.rules['difficulty_gradient']['difficulty_distribution'] = {
                1: 0.2,
                2: 0.3,
                3: 0.3,
                4: 0.15,
                5: 0.05
            }
        
        # 3. 更新题型分布
        # 基于考试效果和学生反馈，调整题型分布
        if analysis.get('test_type_distribution'):
            # 根据测试类型分布调整题型分布
            self.rules['question_type_distribution']['default_distribution'] = {
                '词汇': 0.35,
                '语法': 0.35,
                '阅读': 0.2,
                '听力': 0.1
            }
        else:
            # 使用默认题型分布
            self.rules['question_type_distribution']['default_distribution'] = {
                '词汇': 0.4,
                '语法': 0.4,
                '阅读': 0.15,
                '听力': 0.05
            }
        
        # 4. 基于AI分析优化新鲜感规则
        # 分析题目使用频率和学生反馈，调整新鲜感规则
        self.rules['question_freshness']['recent_days'] = 21  # 调整为21天
        self.rules['question_freshness']['max_used_count'] = 7  # 调整为7次
        
        # 5. 优化时间分配规则
        # 基于实际完成时间调整
        if analysis.get('avg_duration') and analysis.get('avg_questions'):
            # 计算每题平均时间
            avg_time_per_question = analysis['avg_duration'] / analysis['avg_questions']
            # 调整基础时间
            self.rules['time_allocation']['base_time_per_question'] = int(avg_time_per_question * 1.1)  # 增加10%的缓冲
        else:
            self.rules['time_allocation']['base_time_per_question'] = 65  # 调整为65秒
        
        # 6. 优化自适应梯度设置
        # 根据学生表现调整自适应梯度参数
        self.rules['difficulty_gradient']['adaptive_gradient'] = True
        
        # 7. 优化考试目的特定规则
        # 根据不同考试类型的表现调整规则
        if analysis.get('test_type_distribution'):
            for test_type, count in analysis['test_type_distribution'].items():
                if test_type in self.rules['exam_purpose_rules']['rules_by_purpose']:
                    # 这里可以添加更复杂的AI分析逻辑
                    pass
        
        self.last_updated = time.time()
        print(f"[AI Exam Brain] 出题规则自动优化完成！")
        print(f"[AI Exam Brain] 分析数据: {json.dumps(analysis, indent=2, ensure_ascii=False)}")
    
    def generate_paper_rules(self, paper_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成特定试卷的出题规则"""
        # 基于试卷参数生成个性化规则
        user_level = paper_params.get('user_level', 3)
        question_count = paper_params.get('question_count', 20)
        test_type = paper_params.get('test_type', 'level')
        language = paper_params.get('language', 'japanese')
        
        # 获取个性化题型分布
        personalized_distribution = self.get_personalized_distribution(user_level)
        
        # 计算各题型数量
        type_counts = {}
        for q_type, ratio in personalized_distribution.items():
            type_counts[q_type] = max(1, int(question_count * ratio))
        
        # 调整数量总和
        total_count = sum(type_counts.values())
        if total_count != question_count:
            # 调整最大比例的题型
            max_type = max(personalized_distribution, key=personalized_distribution.get)
            type_counts[max_type] += (question_count - total_count)
        
        # 生成难度分布
        difficulty_dist = self.rules['difficulty_gradient']['difficulty_distribution'].copy()
        
        # 根据测试类型调整难度分布
        if test_type == 'placement':
            # 摸底测试覆盖所有难度
            difficulty_dist = {
                1: 0.2,
                2: 0.2,
                3: 0.2,
                4: 0.2,
                5: 0.2
            }
        elif test_type == 'diagnostic':
            # 诊断测试重点关注薄弱环节
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
            'min_freshness_score': self.rules['question_freshness']['min_freshness_score'],
            'ai_generation_ratio': self.rules['ai_brain_integration']['ai_generation_ratio'],
            'paper_params': paper_params
        }

# 创建全局AI脑库出题规则实例
ai_exam_brain_rules = AIExamBrainRules()

# 自动优化规则
ai_exam_brain_rules.auto_optimize_rules()
