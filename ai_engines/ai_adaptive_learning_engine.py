# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自适应学习引擎 v2.0.0
功能：基于知识图谱的智能学习路径规划和自适应难度调整
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ai_adaptive_learning')

class KnowledgeGraph:
    """知识图谱模块"""
    
    def __init__(self):
        self.nodes = {}  # 知识点节点
        self.edges = {}  # 知识点关系
        logger.info("知识图谱初始化完成")
    
    def add_knowledge_node(self, node_id: str, subject: str, topic: str, difficulty: int = 1):
        """添加知识点节点"""
        self.nodes[node_id] = {
            'id': node_id,
            'subject': subject,
            'topic': topic,
            'difficulty': difficulty,
            'mastery_level': 0.0,
            'prerequisites': [],
            'dependents': []
        }
    
    def add_edge(self, from_node: str, to_node: str, relation_type: str = 'prerequisite'):
        """添加知识点关系"""
        if from_node not in self.edges:
            self.edges[from_node] = []
        
        self.edges[from_node].append({
            'to': to_node,
            'relation': relation_type
        })
        
        # 更新节点的前置依赖和后继知识点
        if from_node in self.nodes and to_node in self.nodes:
            if from_node not in self.nodes[to_node]['prerequisites']:
                self.nodes[to_node]['prerequisites'].append(from_node)
            if to_node not in self.nodes[from_node]['dependents']:
                self.nodes[from_node]['dependents'].append(to_node)
    
    def get_prerequisites(self, node_id: str) -> List[str]:
        """获取知识点的前置依赖"""
        return self.nodes.get(node_id, {}).get('prerequisites', [])
    
    def get_dependents(self, node_id: str) -> List[str]:
        """获取依赖该知识点的后续知识点"""
        return self.nodes.get(node_id, {}).get('dependents', [])
    
    def build_curriculum(self, grade: str) -> List[str]:
        """构建对应年级的学习路径"""
        grade_nodes = self._get_nodes_for_grade(grade)
        return self._topological_sort(grade_nodes)
    
    def _get_nodes_for_grade(self, grade: str) -> List[str]:
        """获取对应年级的知识点"""
        grade_level = int(grade.replace('grade', ''))
        return [
            node_id for node_id, node in self.nodes.items()
            if node['difficulty'] <= grade_level
        ]
    
    def _topological_sort(self, node_ids: List[str]) -> List[str]:
        """拓扑排序构建学习路径"""
        in_degree = {node: 0 for node in node_ids}
        adjacency = defaultdict(list)
        
        for node in node_ids:
            for dep in self.get_dependents(node):
                if dep in node_ids:
                    adjacency[node].append(dep)
                    in_degree[dep] += 1
        
        queue = [node for node in node_ids if in_degree[node] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result

class AIAdaptiveLearningEngine:
    """AI自适应学习引擎"""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.user_knowledge = {}
        self.learning_paths = {}
        self._initialize_knowledge_graph()
        logger.info("AI自适应学习引擎 v2.0.0 初始化完成")
    
    def _initialize_knowledge_graph(self):
        """初始化知识图谱"""
        # 数学知识点
        math_topics = [
            ('math_arithmetic', '数学', '算术运算', 1),
            ('math_algebra', '数学', '代数基础', 2),
            ('math_equation', '数学', '方程求解', 3),
            ('math_geometry', '数学', '几何基础', 2),
            ('math_triangle', '数学', '三角形', 3),
            ('math_quadrilateral', '数学', '四边形', 4),
            ('math_function', '数学', '函数', 5),
            ('math_linear_func', '数学', '一次函数', 5),
            ('math_quadratic_func', '数学', '二次函数', 6),
            ('math_probability', '数学', '概率统计', 4),
            ('math_sequence', '数学', '数列', 6),
            ('math_trigonometry', '数学', '三角函数', 7)
        ]
        
        for node_id, subject, topic, difficulty in math_topics:
            self.knowledge_graph.add_knowledge_node(node_id, subject, topic, difficulty)
        
        # 数学知识点关系
        math_relations = [
            ('math_arithmetic', 'math_algebra'),
            ('math_arithmetic', 'math_geometry'),
            ('math_algebra', 'math_equation'),
            ('math_algebra', 'math_function'),
            ('math_geometry', 'math_triangle'),
            ('math_triangle', 'math_quadrilateral'),
            ('math_equation', 'math_linear_func'),
            ('math_linear_func', 'math_quadratic_func'),
            ('math_function', 'math_sequence'),
            ('math_function', 'math_trigonometry')
        ]
        
        for from_node, to_node in math_relations:
            self.knowledge_graph.add_edge(from_node, to_node)
        
        # 语文知识点
        chinese_topics = [
            ('chinese_pinyin', '语文', '拼音', 1),
            ('chinese_char', '语文', '汉字', 1),
            ('chinese_word', '语文', '词语', 2),
            ('chinese_sentence', '语文', '句子', 2),
            ('chinese_paragraph', '语文', '段落', 3),
            ('chinese_reading', '语文', '阅读理解', 4),
            ('chinese_writing', '语文', '写作', 5),
            ('chinese_classical', '语文', '文言文', 6),
            ('chinese_poetry', '语文', '诗词鉴赏', 5)
        ]
        
        for node_id, subject, topic, difficulty in chinese_topics:
            self.knowledge_graph.add_knowledge_node(node_id, subject, topic, difficulty)
        
        # 语文知识点关系
        chinese_relations = [
            ('chinese_pinyin', 'chinese_char'),
            ('chinese_char', 'chinese_word'),
            ('chinese_word', 'chinese_sentence'),
            ('chinese_sentence', 'chinese_paragraph'),
            ('chinese_paragraph', 'chinese_reading'),
            ('chinese_paragraph', 'chinese_writing'),
            ('chinese_classical', 'chinese_poetry')
        ]
        
        for from_node, to_node in chinese_relations:
            self.knowledge_graph.add_edge(from_node, to_node)
        
        # 英语知识点
        english_topics = [
            ('english_alphabet', '英语', '字母', 1),
            ('english_phonics', '英语', '音标', 2),
            ('english_vocab', '英语', '词汇', 2),
            ('english_grammar', '英语', '语法', 3),
            ('english_sentence', '英语', '句子结构', 3),
            ('english_reading', '英语', '阅读理解', 4),
            ('english_writing', '英语', '写作', 5),
            ('english_speaking', '英语', '口语', 4)
        ]
        
        for node_id, subject, topic, difficulty in english_topics:
            self.knowledge_graph.add_knowledge_node(node_id, subject, topic, difficulty)
        
        # 英语知识点关系
        english_relations = [
            ('english_alphabet', 'english_phonics'),
            ('english_phonics', 'english_vocab'),
            ('english_vocab', 'english_grammar'),
            ('english_grammar', 'english_sentence'),
            ('english_sentence', 'english_reading'),
            ('english_sentence', 'english_writing'),
            ('english_sentence', 'english_speaking')
        ]
        
        for from_node, to_node in english_relations:
            self.knowledge_graph.add_edge(from_node, to_node)
        
        logger.info("知识图谱初始化完成，共 %d 个知识点" % len(self.knowledge_graph.nodes))
    
    def assess_knowledge(self, user_id: str, answers: List[Dict[str, Any]]) -> Dict[str, float]:
        """评估用户知识掌握程度
        
        Args:
            user_id: 用户ID
            answers: 答题记录列表
            
        Returns:
            知识点掌握程度字典
        """
        logger.info(f"评估用户 {user_id} 的知识掌握程度")
        
        if user_id not in self.user_knowledge:
            self.user_knowledge[user_id] = {}
        
        subject_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            node_id = answer.get('node_id')
            if node_id not in self.knowledge_graph.nodes:
                continue
            
            subject = self.knowledge_graph.nodes[node_id]['subject']
            subject_stats[subject]['total'] += 1
            if answer.get('correct', False):
                subject_stats[subject]['correct'] += 1
        
        # 更新知识点掌握程度
        results = {}
        for subject, stats in subject_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            results[subject] = accuracy
            
            # 更新具体知识点
            for answer in answers:
                node_id = answer.get('node_id')
                if node_id and answer.get('correct', False):
                    self.user_knowledge[user_id][node_id] = accuracy
        
        return results
    
    def generate_adaptive_path(self, user_id: str, grade: str, subject: str = None) -> List[Dict[str, Any]]:
        """生成自适应学习路径
        
        Args:
            user_id: 用户ID
            grade: 用户年级
            subject: 科目（可选）
            
        Returns:
            学习路径列表
        """
        logger.info(f"为用户 {user_id} 生成自适应学习路径")
        
        # 获取年级对应的知识点
        grade_level = int(grade.replace('grade', ''))
        nodes_for_grade = [
            node_id for node_id, node in self.knowledge_graph.nodes.items()
            if node['difficulty'] <= grade_level and (subject is None or node['subject'] == subject)
        ]
        
        # 获取用户已掌握的知识点
        user_mastery = self.user_knowledge.get(user_id, {})
        
        # 计算每个知识点的推荐优先级
        priorities = []
        for node_id in nodes_for_grade:
            node = self.knowledge_graph.nodes[node_id]
            current_mastery = user_mastery.get(node_id, 0)
            
            # 检查前置依赖是否满足
            prereq_fulfilled = all(
                user_mastery.get(prereq, 0) >= 0.7 for prereq in node['prerequisites']
            )
            
            # 计算优先级：薄弱环节优先，前置依赖满足优先
            priority = (1 - current_mastery) * 10
            if prereq_fulfilled:
                priority += 5
            if current_mastery < 0.6:
                priority += 3
            
            priorities.append({
                'node_id': node_id,
                'subject': node['subject'],
                'topic': node['topic'],
                'difficulty': node['difficulty'],
                'current_mastery': current_mastery,
                'priority': priority,
                'prerequisites': node['prerequisites'],
                'prereq_fulfilled': prereq_fulfilled
            })
        
        # 按优先级排序
        priorities.sort(key=lambda x: -x['priority'])
        
        # 过滤前置依赖未满足的（除非是基础知识点）
        filtered = []
        for p in priorities:
            if p['prereq_fulfilled'] or len(p['prerequisites']) == 0:
                filtered.append(p)
        
        return filtered[:10]
    
    def adjust_difficulty(self, user_id: str, subject: str, recent_performance: float) -> int:
        """根据用户表现调整难度
        
        Args:
            user_id: 用户ID
            subject: 科目
            recent_performance: 近期表现（正确率）
            
        Returns:
            调整后的难度级别
        """
        # 获取当前难度
        grade = self._get_user_grade(user_id)
        grade_level = int(grade.replace('grade', '')) if grade else 5
        
        # 根据表现调整难度
        if recent_performance >= 0.9:
            # 表现优秀，提升难度
            return min(grade_level + 1, 12)
        elif recent_performance >= 0.7:
            # 表现良好，保持难度
            return grade_level
        elif recent_performance >= 0.5:
            # 表现一般，降低一个难度
            return max(grade_level - 1, 1)
        else:
            # 表现较差，降低两个难度
            return max(grade_level - 2, 1)
    
    def _get_user_grade(self, user_id: str) -> Optional[str]:
        """获取用户年级"""
        # 这里应该从用户配置中获取，临时返回默认值
        return 'grade8'
    
    def predict_learning_outcome(self, user_id: str, learning_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测学习结果
        
        Args:
            user_id: 用户ID
            learning_plan: 学习计划
            
        Returns:
            预测结果
        """
        user_mastery = self.user_knowledge.get(user_id, {})
        predictions = []
        
        for item in learning_plan:
            node_id = item.get('node_id')
            if not node_id:
                continue
            
            current_mastery = user_mastery.get(node_id, 0)
            difficulty = item.get('difficulty', 1)
            
            # 基于当前掌握程度和难度预测提升
            expected_improvement = min(0.3, (1 - current_mastery) * 0.5)
            
            # 如果难度过高，降低预期
            if difficulty > 6 and current_mastery < 0.5:
                expected_improvement *= 0.5
            
            predictions.append({
                'node_id': node_id,
                'topic': item.get('topic'),
                'current_mastery': current_mastery,
                'expected_mastery': min(1.0, current_mastery + expected_improvement),
                'confidence': min(0.95, 0.7 + current_mastery * 0.3)
            })
        
        return {
            'predictions': predictions,
            'overall_confidence': sum(p['confidence'] for p in predictions) / max(len(predictions), 1),
            'recommended_items': [p['node_id'] for p in predictions if p['expected_mastery'] < 0.8]
        }
    
    def identify_knowledge_gaps(self, user_id: str, grade: str) -> List[Dict[str, Any]]:
        """识别知识缺口
        
        Args:
            user_id: 用户ID
            grade: 用户年级
            
        Returns:
            知识缺口列表
        """
        user_mastery = self.user_knowledge.get(user_id, {})
        grade_level = int(grade.replace('grade', ''))
        
        gaps = []
        
        for node_id, node in self.knowledge_graph.nodes.items():
            if node['difficulty'] <= grade_level:
                mastery = user_mastery.get(node_id, 0)
                
                if mastery < 0.6:
                    # 检查是否是关键知识点（有很多后继知识点依赖）
                    is_critical = len(node['dependents']) >= 3
                    
                    gaps.append({
                        'node_id': node_id,
                        'subject': node['subject'],
                        'topic': node['topic'],
                        'current_mastery': mastery,
                        'difficulty': node['difficulty'],
                        'is_critical': is_critical,
                        'dependents_count': len(node['dependents']),
                        'priority': (1 - mastery) * (1 + (1 if is_critical else 0))
                    })
        
        # 按优先级排序
        gaps.sort(key=lambda x: -x['priority'])
        
        return gaps[:15]

# 创建全局实例
ai_adaptive_learning_engine = AIAdaptiveLearningEngine()

if __name__ == '__main__':
    engine = AIAdaptiveLearningEngine()
    
    # 测试知识评估
    test_answers = [
        {'node_id': 'math_arithmetic', 'correct': True},
        {'node_id': 'math_arithmetic', 'correct': True},
        {'node_id': 'math_algebra', 'correct': False},
        {'node_id': 'math_geometry', 'correct': True},
        {'node_id': 'math_triangle', 'correct': False},
        {'node_id': 'math_triangle', 'correct': False}
    ]
    
    mastery = engine.assess_knowledge('test_user', test_answers)
    print("知识掌握评估结果:")
    print(json.dumps(mastery, indent=2, ensure_ascii=False))
    
    # 测试生成学习路径
    path = engine.generate_adaptive_path('test_user', 'grade8', '数学')
    print("\n自适应学习路径:")
    print(json.dumps(path, indent=2, ensure_ascii=False))
    
    # 测试难度调整
    difficulty = engine.adjust_difficulty('test_user', '数学', 0.85)
    print(f"\n调整后的难度: {difficulty}")
    
    # 测试知识缺口识别
    gaps = engine.identify_knowledge_gaps('test_user', 'grade8')
    print("\n知识缺口识别:")
    print(json.dumps(gaps[:5], indent=2, ensure_ascii=False))
