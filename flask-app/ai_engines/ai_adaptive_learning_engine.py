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

class AIAdaptiveLearningEngine:
    def __init__(self):
        self.knowledge_graph = {
            'math_arithmetic': {'difficulty': 1, 'subject': '数学', 'prerequisites': [], 'dependents': ['math_algebra', 'math_geometry']},
            'math_algebra': {'difficulty': 2, 'subject': '数学', 'prerequisites': ['math_arithmetic'], 'dependents': ['math_triangle']},
            'math_geometry': {'difficulty': 2, 'subject': '数学', 'prerequisites': ['math_arithmetic'], 'dependents': ['math_triangle']},
            'math_triangle': {'difficulty': 3, 'subject': '数学', 'prerequisites': ['math_algebra', 'math_geometry'], 'dependents': []}
        }
        self.user_knowledge = {}

    def assess_knowledge(self, user_id: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        if user_id not in self.user_knowledge:
            self.user_knowledge[user_id] = {}

        subject_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

        for answer in answers:
            node_id = answer.get('node_id')
            if node_id not in self.knowledge_graph:
                continue

            subject = self.knowledge_graph[node_id]['subject']
            subject_stats[subject]['total'] += 1
            if answer.get('correct', False):
                subject_stats[subject]['correct'] += 1

        results = {}
        for subject, stats in subject_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            results[subject] = accuracy

            for answer in answers:
                node_id = answer.get('node_id')
                if node_id and answer.get('correct', False):
                    self.user_knowledge[user_id][node_id] = accuracy

        return results

    def generate_adaptive_path(self, user_id: str, grade: str, subject: str = None) -> List[Dict[str, Any]]:
        grade_level = int(grade.replace('grade', ''))
        nodes_for_grade = [node_id for node_id, node in self.knowledge_graph.items() if node['difficulty'] <= grade_level and (subject is None or node['subject'] == subject)]

        user_mastery = self.user_knowledge.get(user_id, {})

        priorities = []
        for node_id in nodes_for_grade:
            node = self.knowledge_graph[node_id]
            current_mastery = user_mastery.get(node_id, 0)

            prereq_fulfilled = all(user_mastery.get(prereq, 0) >= 0.7 for prereq in node['prerequisites'])

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

        priorities.sort(key=lambda x: -x['priority'])
        filtered = [p for p in priorities if p['prereq_fulfilled'] or len(p['prerequisites']) == 0]
        return filtered[:10]

    def adjust_difficulty(self, user_id: str, subject: str, recent_performance: float) -> int:
        grade = 'grade8'
        grade_level = int(grade.replace('grade', ''))

        if recent_performance >= 0.9:
            return min(grade_level + 1, 12)
        elif recent_performance >= 0.7:
            return grade_level
        elif recent_performance >= 0.5:
            return max(grade_level - 1, 1)
        else:
            return max(grade_level - 2, 1)

    def _get_user_grade(self, user_id: str) -> Optional[str]:
        return 'grade8'

    def predict_learning_outcome(self, user_id: str, learning_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        user_mastery = self.user_knowledge.get(user_id, {})
        predictions = []

        for item in learning_plan:
            node_id = item.get('node_id')
            if not node_id:
                continue

            current_mastery = user_mastery.get(node_id, 0)
            difficulty = item.get('difficulty', 1)

            expected_improvement = min(0.3, (1 - current_mastery) * 0.5)
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
        user_mastery = self.user_knowledge.get(user_id, {})
        grade_level = int(grade.replace('grade', ''))

        gaps = []

        for node_id, node in self.knowledge_graph.items():
            if node['difficulty'] <= grade_level:
                mastery = user_mastery.get(node_id, 0)

                if mastery < 0.6:
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

        gaps.sort(key=lambda x: -x['priority'])
        return gaps[:15]

# 创建全局实例
ai_adaptive_learning_engine = AIAdaptiveLearningEngine()

if __name__ == '__main__':
    engine = AIAdaptiveLearningEngine()

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

    path = engine.generate_adaptive_path('test_user', 'grade8', '数学')
    print("\n自适应学习路径:")
    print(json.dumps(path, indent=2, ensure_ascii=False))

    difficulty = engine.adjust_difficulty('test_user', '数学', 0.85)
    print(f"\n调整后的难度: {difficulty}")

    gaps = engine.identify_knowledge_gaps('test_user', 'grade8')
    print("\n知识缺口识别:")
    print(json.dumps(gaps[:5], indent=2, ensure_ascii=False))

class adaptive_upgrade_service:
    pass
