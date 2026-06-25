import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能题库标记服务 - 三维标记系统
支持自动动态标记、特征提取、快速出题和题目调阅
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field


class DimensionType(Enum):
    SUBJECT = "subject"
    QUESTION_TYPE = "question_type"
    DIFFICULTY = "difficulty"
    KNOWLEDGE = "knowledge"
    CATEGORY = "category"


@dataclass
class QuestionTag:
    tag_id: str
    dimension: str
    value: str
    weight: float = 1.0
    confidence: float = 1.0
    auto_generated: bool = True


@dataclass
class TaggedQuestion:
    question_id: str
    content: str
    tags: List[QuestionTag] = field(default_factory=list)
    feature_vector: Dict[str, float] = field(default_factory=dict)
    usage_count: int = 0
    last_used: Optional[float] = None


class SmartQuestionTagger:
    """智能题库标记服务"""

    def __init__(self):
        self._questions: Dict[str, TaggedQuestion] = {}
        self._index_3d: Dict[str, List[str]] = {}
        self._index_by_dim: Dict[str, Dict[str, List[str]]] = {}
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'question_tags_3d.json')
        self._load()
        print("智能题库标记服务初始化完成")

    def _load(self):
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for q in data.get('questions', []):
                        tags = [QuestionTag(**t) for t in q.get('tags', [])]
                        self._questions[q['question_id']] = TaggedQuestion(
                            question_id=q['question_id'],
                            content=q['content'],
                            tags=tags,
                            feature_vector=q.get('feature_vector', {}),
                            usage_count=q.get('usage_count', 0),
                            last_used=q.get('last_used')
                        )
                self._rebuild_index()
                print(f"已加载 {len(self._questions)} 个标记题目")
            except Exception as e:
                print(f"加载失败: {e}")

    def _save(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        data = {
            'last_updated': time.time(),
            'questions': [
                {
                    'question_id': q.question_id,
                    'content': q.content,
                    'tags': [{'tag_id': t.tag_id, 'dimension': t.dimension, 'value': t.value, 
                             'weight': t.weight, 'confidence': t.confidence, 'auto_generated': t.auto_generated} 
                            for t in q.tags],
                    'feature_vector': q.feature_vector,
                    'usage_count': q.usage_count,
                    'last_used': q.last_used
                }
                for q in self._questions.values()
            ]
        }
        with open(self._db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _rebuild_index(self):
        self._index_3d = {}
        self._index_by_dim = {'subject': {}, 'question_type': {}, 'difficulty': {}, 'knowledge': {}, 'category': {}}
        
        for q in self._questions.values():
            dims = {}
            for tag in q.tags:
                if tag.dimension not in self._index_by_dim:
                    self._index_by_dim[tag.dimension] = {}
                if tag.value not in self._index_by_dim[tag.dimension]:
                    self._index_by_dim[tag.dimension][tag.value] = []
                self._index_by_dim[tag.dimension][tag.value].append(q.question_id)
                dims[tag.dimension] = tag.value
            
            if len(dims) >= 3:
                key = f"{dims.get('subject', 'unk')}:{dims.get('question_type', 'unk')}:{dims.get('difficulty', 'unk')}"
                if key not in self._index_3d:
                    self._index_3d[key] = []
                self._index_3d[key].append(q.question_id)

    def tag_question(self, question_id: str, content: str,
                     subject: str = None, question_type: str = None, difficulty: str = None,
                     knowledge_points: List[str] = None, category: str = None) -> TaggedQuestion:
        """标记题目"""
        tags = []
        if subject:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='subject', value=subject))
        if question_type:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='question_type', value=question_type))
        if difficulty:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='difficulty', value=difficulty))
        if knowledge_points:
            for kp in knowledge_points:
                tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='knowledge', value=kp, auto_generated=True))
        if category:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='category', value=category))
        
        question = TaggedQuestion(question_id=question_id, content=content, tags=tags)
        question.feature_vector = self._compute_vector(content, tags)
        
        self._questions[question_id] = question
        
        for tag in tags:
            if tag.value not in self._index_by_dim.get(tag.dimension, {}):
                self._index_by_dim.setdefault(tag.dimension, {})[tag.value] = []
            self._index_by_dim[tag.dimension][tag.value].append(question_id)
        
        dims = {t.dimension: t.value for t in tags}
        key = f"{dims.get('subject', 'unk')}:{dims.get('question_type', 'unk')}:{dims.get('difficulty', 'unk')}"
        if key not in self._index_3d:
            self._index_3d[key] = []
        self._index_3d[key].append(question_id)
        
        self._save()
        print(f"题目已标记: {question_id} ({subject}/{question_type}/{difficulty})")
        return question

    def _compute_vector(self, content: str, tags: List[QuestionTag]) -> Dict[str, float]:
        vector = {}
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        for i in range(0, min(len(content_hash), 16), 2):
            vector[f'c{content_hash[i:i+2]}'] = int(content_hash[i:i+2], 16) / 255.0
        for tag in tags:
            vector[f"{tag.dimension}_{tag.value}"] = tag.weight
        return vector

    def auto_tag(self, question_id: str, content: str) -> TaggedQuestion:
        """自动标记"""
        tags = []
        keywords = {
            'math': ['计算', '求', '函数', '导数', '积分', '方程', '几何'],
            'physics': ['力', '能量', '速度', '电场', '磁场', '光'],
            'chemistry': ['反应', '元素', '分子', '原子', '化学键'],
            'computer': ['CPU', '内存', '算法', '数据结构', '编程'],
            'programming': ['Python', 'Java', '代码', '函数', '类'],
            'database': ['SQL', '查询', '索引', '表', '数据库'],
            'network': ['TCP', 'HTTP', '网络', '协议', 'IP']
        }
        
        for subject, words in keywords.items():
            if any(w in content for w in words):
                tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='subject', value=subject, auto_generated=True))
                break
        
        if '选择' in content or '选项' in content:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='question_type', value='single_choice', auto_generated=True))
        elif '判断' in content:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='question_type', value='true_false', auto_generated=True))
        elif '计算' in content:
            tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='question_type', value='calculation', auto_generated=True))
        
        difficulty_map = {'基础': 'easy', '简单': 'easy', '中等': 'medium', '困难': 'hard', '复杂': 'hard', '专家': 'expert'}
        for word, diff in difficulty_map.items():
            if word in content:
                tags.append(QuestionTag(tag_id=f"T-{int(time.time())}", dimension='difficulty', value=diff, auto_generated=True))
                break
        
        question = TaggedQuestion(question_id=question_id, content=content, tags=tags)
        self._questions[question_id] = question
        self._rebuild_index()
        self._save()
        print(f"自动标记: {question_id} -> {[t.value for t in tags]}")
        return question

    def search(self, subject: str = None, question_type: str = None, difficulty: str = None, 
               knowledge_point: str = None, limit: int = 10) -> List[TaggedQuestion]:
        """快速搜索"""
        sets = []
        for dim, val in [('subject', subject), ('question_type', question_type), 
                         ('difficulty', difficulty), ('knowledge', knowledge_point)]:
            if val and dim in self._index_by_dim and val in self._index_by_dim[dim]:
                sets.append(set(self._index_by_dim[dim][val]))
        
        if not sets:
            return list(self._questions.values())[:limit]
        
        result = sets[0]
        for s in sets[1:]:
            result = result.intersection(s)
        
        questions = [self._questions[qid] for qid in result if qid in self._questions]
        questions.sort(key=lambda x: x.usage_count, reverse=True)
        return questions[:limit]

    def get_by_3d(self, subject: str, question_type: str, difficulty: str) -> List[TaggedQuestion]:
        """通过三维标记获取"""
        key = f"{subject}:{question_type}:{difficulty}"
        qids = self._index_3d.get(key, [])
        return [self._questions[qid] for qid in qids if qid in self._questions]

    def generate_paper(self, subject: str, question_type: str, 
                       diff_distribution: Dict[str, float] = None,
                       count: int = 10) -> List[TaggedQuestion]:
        """快速组卷"""
        if diff_distribution is None:
            diff_distribution = {'easy': 0.2, 'medium': 0.5, 'hard': 0.2, 'expert': 0.1}
        
        questions = self.search(subject=subject, question_type=question_type, limit=1000)
        if not questions:
            return []
        
        grouped = {'easy': [], 'medium': [], 'hard': [], 'expert': []}
        for q in questions:
            for tag in q.tags:
                if tag.dimension == 'difficulty':
                    if tag.value in grouped:
                        grouped[tag.value].append(q)
                    break
        
        selected = []
        for diff, ratio in diff_distribution.items():
            selected.extend(grouped.get(diff, [])[:int(count * ratio)])
        
        remaining = count - len(selected)
        for q in questions:
            if q not in selected and remaining > 0:
                selected.append(q)
                remaining -= 1
        
        for q in selected:
            q.usage_count += 1
            q.last_used = time.time()
        
        self._save()
        logger.info(f"生成试卷: {len(selected)} 道题目")
        return selected[:count]

    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total': len(self._questions),
            'by_subject': {k: len(v) for k, v in self._index_by_dim.get('subject', {}).items()},
            'by_type': {k: len(v) for k, v in self._index_by_dim.get('question_type', {}).items()},
            'by_difficulty': {k: len(v) for k, v in self._index_by_dim.get('difficulty', {}).items()},
            'total_usages': sum(q.usage_count for q in self._questions.values()),
            '3d_combinations': len(self._index_3d)
        }

    def maintain(self) -> Dict:
        """题库维护"""
        hashes = set()
        duplicates = 0
        for q in list(self._questions.values()):
            h = hashlib.md5(q.content.encode('utf-8')).hexdigest()
            if h in hashes:
                del self._questions[q.question_id]
                duplicates += 1
            else:
                hashes.add(h)
        self._rebuild_index()
        self._save()
        return {'duplicates_removed': duplicates, 'remaining': len(self._questions)}


smart_question_tagger = SmartQuestionTagger()
