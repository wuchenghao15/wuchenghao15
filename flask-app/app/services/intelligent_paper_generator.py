# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能组卷服务模块
根据难度分布、知识点覆盖率、题型比例自动组卷
"""

import json
import random
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PaperGenerationConfig:
    """试卷生成配置"""
    # 题目总数
    total_questions: int = 20
    # 总分
    total_points: float = 100.0
    # 题型比例配置 {题型: 比例}
    type_ratio: Dict[str, float] = field(default_factory=lambda: {
        'single_choice': 0.5,    # 单选题 50%
        'multiple_choice': 0.2,  # 多选题 20%
        'true_false': 0.1,       # 判断题 10%
        'fill_blank': 0.1,       # 填空题 10%
        'short_answer': 0.1      # 简答题 10%
    })
    # 难度分布配置 {难度等级: 比例}
    difficulty_distribution: Dict[int, float] = field(default_factory=lambda: {
        1: 0.15,  # 简单 15%
        2: 0.25,  # 较易 25%
        3: 0.35,  # 中等 35%
        4: 0.20,  # 较难 20%
        5: 0.05   # 困难 5%
    })
    # 必须覆盖的知识点列表
    required_knowledge_points: List[str] = field(default_factory=list)
    # 知识点最小覆盖率 (百分比)
    min_knowledge_coverage: float = 80.0
    # 是否打乱题目顺序
    shuffle_questions: bool = True
    # 是否打乱选项顺序
    shuffle_options: bool = True
    # 每道题的最小分值
    min_points_per_question: float = 1.0
    # 每道题的最大分值
    max_points_per_question: float = 10.0


class IntelligentPaperGenerator:
    """智能组卷生成器"""
    
    def __init__(self, db_manager=None):
        """初始化智能组卷生成器"""
        self.db_manager = db_manager
        self._init_default_config()
        logger.info("智能组卷生成器初始化完成")
    
    def _init_default_config(self):
        """初始化默认配置"""
        self.default_config = PaperGenerationConfig()
    
    def _get_question_pool(self, exam_id: Optional[str] = None, 
                           filters: Optional[Dict] = None) -> List[Dict]:
        """获取题目池"""
        try:
            questions = []
            
            if self.db_manager:
                # 从数据库获取题目
                query = "SELECT * FROM questions"
                conditions = []
                params = []
                
                if exam_id:
                    conditions.append("exam_id = ?")
                    params.append(exam_id)
                
                if filters:
                    if 'type' in filters:
                        conditions.append("type = ?")
                        params.append(filters['type'])
                    if 'difficulty' in filters:
                        conditions.append("difficulty = ?")
                        params.append(filters['difficulty'])
                    if 'tags' in filters:
                        # 标签筛选
                        conditions.append("tags LIKE ?")
                        params.append(f"%{filters['tags']}%")
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                query = f"{query} WHERE {where_clause}"
                
                results = self.db_manager.fetch_all(query, tuple(params) if params else ())
                
                for row in results:
                    if isinstance(row, dict):
                        questions.append({
                            'id': row['id'],
                            'type': row.get('type', 'single_choice'),
                            'content': row.get('content', ''),
                            'options': json.loads(row.get('options', '[]')),
                            'correct_answer': row.get('correct_answer', ''),
                            'difficulty': row.get('difficulty', 1),
                            'points': row.get('points', 1.0),
                            'tags': json.loads(row.get('tags', '[]')),
                            'explanation': row.get('explanation', '')
                        })
            
            return questions
        except Exception as e:
            logger.error(f"获取题目池失败: {str(e)}")
            return []
    
    def calculate_type_counts(self, config: PaperGenerationConfig) -> Dict[str, int]:
        """根据题型比例计算各题型题目数量"""
        type_counts = {}
        total = config.total_questions
        remaining = total
        
        # 按比例分配
        sorted_types = sorted(config.type_ratio.items(), key=lambda x: x[1], reverse=True)
        
        for type_name, ratio in sorted_types:
            count = int(round(total * ratio))
            # 确保不超过剩余数量
            count = min(count, remaining)
            if count > 0:
                type_counts[type_name] = count
                remaining -= count
        
        # 处理余数
        if remaining > 0:
            # 将余数分配给比例最大的题型
            max_type = sorted_types[0][0]
            type_counts[max_type] = type_counts.get(max_type, 0) + remaining
        
        return type_counts
    
    def calculate_difficulty_counts(self, config: PaperGenerationConfig) -> Dict[int, int]:
        """根据难度分布计算各难度题目数量"""
        difficulty_counts = {}
        total = config.total_questions
        remaining = total
        
        sorted_difficulties = sorted(config.difficulty_distribution.items(), 
                                     key=lambda x: x[1], reverse=True)
        
        for diff_level, ratio in sorted_difficulties:
            count = int(round(total * ratio))
            count = min(count, remaining)
            if count > 0:
                difficulty_counts[diff_level] = count
                remaining -= count
        
        if remaining > 0:
            # 将余数分配给中等难度
            difficulty_counts[3] = difficulty_counts.get(3, 0) + remaining
        
        return difficulty_counts
    
    def select_questions_by_type_and_difficulty(
        self, 
        question_pool: List[Dict],
        type_counts: Dict[str, int],
        difficulty_counts: Dict[int, int]
    ) -> List[Dict]:
        """根据题型和难度选择题目"""
        # 分类题目
        questions_by_type_diff = defaultdict(lambda: defaultdict(list))
        
        for q in question_pool:
            q_type = q.get('type', 'single_choice')
            q_diff = q.get('difficulty', 1)
            questions_by_type_diff[q_type][q_diff].append(q)
        
        selected_questions = []
        
        # 首先按题型选择
        for type_name, type_count in type_counts.items():
            type_questions_needed = type_count
            type_selected = []
            
            # 计算该题型下各难度需要的题目数
            type_diff_distribution = {}
            for diff_level, diff_count in difficulty_counts.items():
                # 按比例分配
                ratio = diff_count / sum(difficulty_counts.values())
                type_diff_count = int(round(type_count * ratio))
                if type_diff_count > 0:
                    type_diff_distribution[diff_level] = type_diff_count
            
            # 调整确保总数正确
            total_diff_for_type = sum(type_diff_distribution.values())
            diff_diff = type_count - total_diff_for_type
            if diff_diff != 0:
                # 将差值分配给中等难度
                type_diff_distribution[3] = type_diff_distribution.get(3, 0) + diff_diff
            
            # 从各难度级别选择题目
            for diff_level, diff_count in type_diff_distribution.items():
                available = questions_by_type_diff[type_name][diff_level]
                if len(available) >= diff_count:
                    # 随机选择
                    selected = random.sample(available, diff_count)
                else:
                    # 如果不够，选择所有可用题目
                    selected = available
                    # 从其他难度补充
                    shortage = diff_count - len(selected)
                    for other_diff in [2, 3, 4, 1, 5]:  # 优先从相邻难度补充
                        if other_diff != diff_level:
                            other_available = questions_by_type_diff[type_name][other_diff]
                            additional_needed = min(shortage, len(other_available) - 
                                                    len([q for q in other_available if q in type_selected]))
                            if additional_needed > 0:
                                additional = [q for q in other_available if q not in type_selected][:additional_needed]
                                selected.extend(additional)
                                shortage -= additional_needed
                                if shortage <= 0:
                                    break
                
                type_selected.extend(selected)
            
            selected_questions.extend(type_selected)
        
        return selected_questions
    
    def ensure_knowledge_coverage(
        self,
        selected_questions: List[Dict],
        question_pool: List[Dict],
        config: PaperGenerationConfig
    ) -> List[Dict]:
        """确保知识点覆盖率"""
        if not config.required_knowledge_points:
            return selected_questions
        
        # 分析已选题目覆盖的知识点
        covered_points = set()
        for q in selected_questions:
            tags = q.get('tags', [])
            covered_points.update(tags)
        
        # 计算覆盖率
        required_set = set(config.required_knowledge_points)
        coverage_ratio = len(covered_points.intersection(required_set)) / len(required_set) * 100
        
        # 如果覆盖率不足，补充题目
        if coverage_ratio < config.min_knowledge_coverage:
            uncovered_points = required_set - covered_points
            
            # 找出覆盖未覆盖知识点的题目
            candidate_questions = []
            for q in question_pool:
                q_tags = set(q.get('tags', []))
                if q_tags.intersection(uncovered_points) and q not in selected_questions:
                    # 计算覆盖的新知识点数量
                    new_coverage = len(q_tags.intersection(uncovered_points))
                    candidate_questions.append((q, new_coverage))
            
            # 按新覆盖知识点数量排序
            candidate_questions.sort(key=lambda x: x[1], reverse=True)
            
            # 替换已选题目中不覆盖关键知识点的题目
            questions_to_replace = []
            for q in selected_questions:
                q_tags = set(q.get('tags', []))
                if not q_tags.intersection(required_set):
                    questions_to_replace.append(q)
            
            # 执行替换
            for old_q in questions_to_replace:
                if candidate_questions:
                    new_q, _ = candidate_questions.pop(0)
                    idx = selected_questions.index(old_q)
                    selected_questions[idx] = new_q
                    
                    # 更新已覆盖知识点
                    covered_points.update(new_q.get('tags', []))
                    
                    # 检查是否达到覆盖率要求
                    coverage_ratio = len(covered_points.intersection(required_set)) / len(required_set) * 100
                    if coverage_ratio >= config.min_knowledge_coverage:
                        break
        
        return selected_questions
    
    def assign_points(
        self,
        selected_questions: List[Dict],
        config: PaperGenerationConfig
    ) -> List[Dict]:
        """分配题目分值"""
        # 根据难度分配分值
        total_points = config.total_points
        total_weight = 0
        
        # 计算难度权重总和
        difficulty_weights = {
            1: 1.0,   # 简单
            2: 1.5,   # 较易
            3: 2.0,   # 中等
            4: 2.5,   # 较难
            5: 3.0    # 困难
        }
        
        for q in selected_questions:
            diff = q.get('difficulty', 3)
            weight = difficulty_weights.get(diff, 2.0)
            total_weight += weight
        
        # 分配分值
        assigned_questions = []
        remaining_points = total_points
        
        for i, q in enumerate(selected_questions):
            diff = q.get('difficulty', 3)
            weight = difficulty_weights.get(diff, 2.0)
            
            # 计算基础分值
            base_points = (weight / total_weight) * total_points
            
            # 考虑题型因素
            q_type = q.get('type', 'single_choice')
            type_multipliers = {
                'single_choice': 1.0,
                'multiple_choice': 1.5,
                'true_false': 0.8,
                'fill_blank': 1.2,
                'short_answer': 2.0,
                'essay': 3.0
            }
            multiplier = type_multipliers.get(q_type, 1.0)
            
            calculated_points = base_points * multiplier
            
            # 限制分值范围
            if i == len(selected_questions) - 1:
                # 最后一道题，使用剩余分值
                points = remaining_points
            else:
                points = max(config.min_points_per_question, 
                            min(config.max_points_per_question, calculated_points))
            
            # 更新剩余分值
            remaining_points -= points
            
            # 创建带分值的题目副本
            q_copy = q.copy()
            q_copy['assigned_points'] = round(points, 1)
            assigned_questions.append(q_copy)
        
        # 确保总分正确（微调最后一道题）
        if assigned_questions:
            total_assigned = sum(q['assigned_points'] for q in assigned_questions)
            diff = total_points - total_assigned
            if diff != 0:
                assigned_questions[-1]['assigned_points'] += diff
        
        return assigned_questions
    
    def shuffle_questions_and_options(
        self,
        questions: List[Dict],
        config: PaperGenerationConfig
    ) -> List[Dict]:
        """打乱题目和选项顺序"""
        shuffled = questions.copy()
        
        if config.shuffle_questions:
            # 打乱题目顺序
            shuffled = random.sample(shuffled, len(shuffled))
        
        if config.shuffle_options:
            # 打乱选项顺序（仅对选择题和判断题）
            for q in shuffled:
                q_type = q.get('type', 'single_choice')
                if q_type in ['single_choice', 'multiple_choice', 'true_false']:
                    options = q.get('options', [])
                    if isinstance(options, list) and len(options) > 1:
                        # 保存正确答案信息
                        correct_answer = q.get('correct_answer', '')
                        
                        # 打乱选项
                        shuffled_options = random.sample(options, len(options))
                        q['options'] = shuffled_options
                        
                        # 如果选项包含正确答案标记，需要更新正确答案位置
                        if isinstance(options[0], dict) and 'is_correct' in options[0]:
                            # 找出正确答案的新位置
                            new_correct_key = None
                            for opt in shuffled_options:
                                if opt.get('is_correct'):
                                    new_correct_key = opt.get('key')
                                    break
                            if new_correct_key:
                                q['correct_answer'] = new_correct_key
        
        return shuffled
    
    def generate_paper(
        self,
        config: PaperGenerationConfig,
        exam_id: Optional[str] = None,
        question_pool: Optional[List[Dict]] = None
    ) -> Dict:
        """
        生成试卷
        
        Args:
            config: 试卷生成配置
            exam_id: 考试ID（可选）
            question_pool: 题目池（可选，如果不提供则从数据库获取）
        
        Returns:
            生成的试卷信息
        """
        try:
            # 获取题目池
            if question_pool is None:
                question_pool = self._get_question_pool(exam_id)
            
            if len(question_pool) < config.total_questions:
                logger.warning(f"题目池数量不足: 需要 {config.total_questions}, 可用 {len(question_pool)}")
                # 调整配置
                config.total_questions = min(config.total_questions, len(question_pool))
            
            # 计算各题型题目数量
            type_counts = self.calculate_type_counts(config)
            logger.info(f"题型分布: {type_counts}")
            
            # 计算各难度题目数量
            difficulty_counts = self.calculate_difficulty_counts(config)
            logger.info(f"难度分布: {difficulty_counts}")
            
            # 选择题目
            selected_questions = self.select_questions_by_type_and_difficulty(
                question_pool, type_counts, difficulty_counts
            )
            
            # 确保知识点覆盖率
            selected_questions = self.ensure_knowledge_coverage(
                selected_questions, question_pool, config
            )
            
            # 分配分值
            selected_questions = self.assign_points(selected_questions, config)
            
            # 打乱顺序
            selected_questions = self.shuffle_questions_and_options(selected_questions, config)
            
            # 生成试卷信息
            paper = {
                'paper_id': f"PAPER_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}",
                'generated_at': datetime.now().isoformat(),
                'total_questions': len(selected_questions),
                'total_points': config.total_points,
                'questions': selected_questions,
                'generation_config': {
                    'type_ratio': config.type_ratio,
                    'difficulty_distribution': config.difficulty_distribution,
                    'knowledge_coverage': config.min_knowledge_coverage
                },
                'statistics': self._calculate_paper_statistics(selected_questions)
            }
            
            logger.info(f"试卷生成成功: {paper['paper_id']}, 题目数: {len(selected_questions)}")
            return paper
            
        except Exception as e:
            logger.error(f"生成试卷失败: {str(e)}")
            return {
                'paper_id': None,
                'error': str(e),
                'questions': []
            }
    
    def _calculate_paper_statistics(self, questions: List[Dict]) -> Dict:
        """计算试卷统计信息"""
        stats = {
            'type_distribution': defaultdict(int),
            'difficulty_distribution': defaultdict(int),
            'knowledge_points': defaultdict(int),
            'total_points': 0,
            'avg_difficulty': 0,
            'avg_points': 0
        }
        
        for q in questions:
            q_type = q.get('type', 'single_choice')
            q_diff = q.get('difficulty', 3)
            q_points = q.get('assigned_points', q.get('points', 1.0))
            q_tags = q.get('tags', [])
            
            stats['type_distribution'][q_type] += 1
            stats['difficulty_distribution'][q_diff] += 1
            stats['total_points'] += q_points
            
            for tag in q_tags:
                stats['knowledge_points'][tag] += 1
        
        # 转换为普通字典
        stats['type_distribution'] = dict(stats['type_distribution'])
        stats['difficulty_distribution'] = dict(stats['difficulty_distribution'])
        stats['knowledge_points'] = dict(stats['knowledge_points'])
        
        # 计算平均值
        if questions:
            stats['avg_difficulty'] = sum(q.get('difficulty', 3) for q in questions) / len(questions)
            stats['avg_points'] = stats['total_points'] / len(questions)
        
        return stats
    
    def generate_paper_from_template(
        self,
        template: Dict,
        exam_id: Optional[str] = None
    ) -> Dict:
        """从模板生成试卷"""
        config = PaperGenerationConfig(
            total_questions=template.get('question_count', 20),
            total_points=template.get('total_points', 100.0),
            type_ratio=template.get('type_ratio', self.default_config.type_ratio),
            difficulty_distribution=template.get('difficulty_distribution', 
                                                 self.default_config.difficulty_distribution),
            required_knowledge_points=template.get('required_knowledge_points', []),
            min_knowledge_coverage=template.get('min_knowledge_coverage', 80.0),
            shuffle_questions=template.get('shuffle_questions', True),
            shuffle_options=template.get('shuffle_options', True)
        )
        
        return self.generate_paper(config, exam_id)
    
    def validate_paper_quality(self, paper: Dict) -> Dict:
        """验证试卷质量"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'score': 100
        }
        
        questions = paper.get('questions', [])
        
        # 检查题目数量
        expected_count = paper.get('total_questions', 0)
        actual_count = len(questions)
        if actual_count != expected_count:
            validation_result['issues'].append(
                f"题目数量不符: 期望 {expected_count}, 实际 {actual_count}"
            )
            validation_result['score'] -= 10
        
        # 检查总分
        expected_points = paper.get('total_points', 0)
        actual_points = sum(q.get('assigned_points', q.get('points', 1.0)) for q in questions)
        if abs(actual_points - expected_points) > 0.1:
            validation_result['warnings'].append(
                f"总分偏差: 期望 {expected_points}, 实际 {actual_points}"
            )
            validation_result['score'] -= 5
        
        # 检查难度分布
        stats = paper.get('statistics', {})
        diff_dist = stats.get('difficulty_distribution', {})
        expected_diff_dist = paper.get('generation_config', {}).get('difficulty_distribution', {})
        
        for level, expected_ratio in expected_diff_dist.items():
            actual_count = diff_dist.get(level, 0)
            expected_count = int(expected_count * expected_ratio)
            if abs(actual_count - expected_count) > 1:
                validation_result['warnings'].append(
                    f"难度{level}题目数量偏差: 期望 {expected_count}, 实际 {actual_count}"
                )
        
        # 检查知识点覆盖
        knowledge_points = stats.get('knowledge_points', {})
        if len(knowledge_points) < 3:
            validation_result['warnings'].append("知识点覆盖不足，建议增加更多知识点")
        
        # 检查重复题目
        question_ids = [q.get('id') for q in questions]
        if len(question_ids) != len(set(question_ids)):
            validation_result['issues'].append("试卷中存在重复题目")
            validation_result['is_valid'] = False
            validation_result['score'] -= 20
        
        # 计算最终评分
        validation_result['score'] = max(0, validation_result['score'])
        
        if validation_result['score'] < 70:
            validation_result['is_valid'] = False
        
        return validation_result
    
    def optimize_paper_difficulty(
        self,
        paper: Dict,
        target_difficulty: float = 3.0,
        tolerance: float = 0.3
    ) -> Dict:
        """优化试卷难度"""
        questions = paper.get('questions', [])
        stats = paper.get('statistics', {})
        current_avg_diff = stats.get('avg_difficulty', 3.0)
        
        # 如果当前难度与目标差异超过容忍范围，进行调整
        if abs(current_avg_diff - target_difficulty) > tolerance:
            logger.info(f"优化试卷难度: 当前 {current_avg_diff}, 目标 {target_difficulty}")
            
            # 需要调整的方向
            if current_avg_diff > target_difficulty:
                # 试卷太难，替换部分难题为简单题
                self._replace_for_difficulty(questions, 'down')
            else:
                # 试卷太简单，替换部分简单题为难题
                self._replace_for_difficulty(questions, 'up')
            
            # 重新计算统计信息
            paper['statistics'] = self._calculate_paper_statistics(questions)
        
        return paper
    
    def _replace_for_difficulty(self, questions: List[Dict], direction: str):
        """为调整难度替换题目"""
        # 找出需要替换的题目
        if direction == 'down':
            # 从难题开始替换
            sorted_questions = sorted(questions, key=lambda q: q.get('difficulty', 3), reverse=True)
        else:
            # 从简单题开始替换
            sorted_questions = sorted(questions, key=lambda q: q.get('difficulty', 3))
        
        # 替换前3道题（如果需要）
        for i in range(min(3, len(sorted_questions))):
            old_q = sorted_questions[i]
            old_diff = old_q.get('difficulty', 3)
            
            # 计算新难度目标
            if direction == 'down':
                new_diff_target = max(1, old_diff - 1)
            else:
                new_diff_target = min(5, old_diff + 1)
            
            # 这里需要从题目池中找到合适的新题目
            # 由于没有题目池，这里仅做演示
            logger.info(f"建议替换难度 {old_diff} 的题目为难度 {new_diff_target} 的题目")


# 全局实例
_intelligent_paper_generator = None

def get_intelligent_paper_generator(db_manager=None) -> IntelligentPaperGenerator:
    """获取智能组卷生成器实例"""
    global _intelligent_paper_generator
    if _intelligent_paper_generator is None:
        _intelligent_paper_generator = IntelligentPaperGenerator(db_manager)
    return _intelligent_paper_generator


if __name__ == "__main__":
    # 测试智能组卷
    generator = IntelligentPaperGenerator()
    
    # 创建测试题目池
    test_pool = []
    for i in range(100):
        test_pool.append({
            'id': f"Q{i+1}",
            'type': random.choice(['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer']),
            'content': f"测试题目 {i+1}",
            'options': [
                {'key': 'A', 'text': '选项A', 'is_correct': random.choice([True, False])},
                {'key': 'B', 'text': '选项B', 'is_correct': random.choice([True, False])},
                {'key': 'C', 'text': '选项C', 'is_correct': random.choice([True, False])},
                {'key': 'D', 'text': '选项D', 'is_correct': random.choice([True, False])}
            ],
            'correct_answer': 'A',
            'difficulty': random.randint(1, 5),
            'tags': [f"知识点{random.randint(1, 10)}"],
            'explanation': f"题目 {i+1} 的解析"
        })
    
    # 生成试卷
    config = PaperGenerationConfig(
        total_questions=20,
        total_points=100.0,
        required_knowledge_points=['知识点1', '知识点2', '知识点3', '知识点4', '知识点5'],
        min_knowledge_coverage=80.0
    )
    
    paper = generator.generate_paper(config, question_pool=test_pool)
    
    print("=" * 60)
    print("智能组卷测试结果")
    print("=" * 60)
    print(f"试卷ID: {paper['paper_id']}")
    print(f"题目数量: {paper['total_questions']}")
    print(f"总分: {paper['total_points']}")
    print("\n统计信息:")
    print(json.dumps(paper['statistics'], indent=2, ensure_ascii=False))
    
    # 验证试卷质量
    validation = generator.validate_paper_quality(paper)
    print("\n质量验证:")
    print(f"有效: {validation['is_valid']}")
    print(f"评分: {validation['score']}")
    if validation['issues']:
        print(f"问题: {validation['issues']}")
    if validation['warnings']:
        print(f"警告: {validation['warnings']}")
    
    logger.info("智能组卷测试完成")