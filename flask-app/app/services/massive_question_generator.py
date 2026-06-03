#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模题库生成服务 - 支持每个科目1000万道题目的高效生成和存储
"""

import os
import json
import time
import random
import threading
import multiprocessing
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class Subject(Enum):
    """科目枚举"""
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    ENGLISH = "english"
    CHINESE = "chinese"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    BIOLOGY = "biology"
    COMPUTER = "computer"
    ECONOMICS = "economics"
    POLITICS = "politics"
    PROGRAMMING = "programming"
    DATA_STRUCTURES = "data_structures"
    ALGORITHMS = "algorithms"
    DATABASE = "database"
    NETWORK = "network"


class QuestionType(Enum):
    """题型枚举"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    CALCULATION = "calculation"
    LOGIC_JUDGMENT = "logic_judgment"
    CODE_ANALYSIS = "code_analysis"


class DifficultyLevel(Enum):
    """难度等级"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    subject: Subject
    target_count: int
    status: str = "pending"
    generated_count: int = 0
    saved_count: int = 0
    batch_size: int = 1000
    progress: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    estimated_remaining: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'subject': self.subject.value,
            'target_count': self.target_count,
            'status': self.status,
            'generated_count': self.generated_count,
            'saved_count': self.saved_count,
            'batch_size': self.batch_size,
            'progress': round(self.progress, 2),
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'estimated_remaining': self.estimated_remaining
        }


class MassiveQuestionGenerator:
    """大规模题库生成器"""

    def __init__(self):
        self._tasks: Dict[str, GenerationTask] = {}
        self._lock = threading.RLock()
        self._workers = []
        self._subject_configs = self._load_subject_configs()
        
        logger.info("大规模题库生成服务初始化完成")

    def _load_subject_configs(self) -> Dict[str, Dict]:
        """加载科目配置"""
        return {
            'math': {
                'topics': ['代数', '几何', '概率统计', '三角函数', '数列', '导数', '积分', '矩阵'],
                'question_templates': {
                    'single_choice': [
                        ('{topic}中,{concept}的定义是?', ['定义']),
                        ('{topic}中,{concept}的性质是?', ['性质']),
                        ('下列关于{topic}的{concept},正确的是?', ['概念理解'])
                    ],
                    'calculation': [
                        ('计算:{expression}', ['计算']),
                        ('已知{condition},求{target}的值', ['综合计算'])
                    ],
                    'fill_blank': [
                        ('{topic}中,{concept}的公式是____', ['公式']),
                        ('{concept}的单位是____', ['单位'])
                    ]
                },
                'difficulty_weights': {'easy': 0.3, 'medium': 0.4, 'hard': 0.2, 'expert': 0.1}
            },
            'physics': {
                'topics': ['力学', '电磁学', '热学', '光学', '波动', '原子物理'],
                'question_templates': {
                    'single_choice': [
                        ('{law}适用于哪种情况?', ['定律应用']),
                        ('{concept}的物理意义是?', ['概念理解'])
                    ],
                    'calculation': [
                        ('一个{object},{condition},求{target}', ['物理计算'])
                    ]
                },
                'difficulty_weights': {'easy': 0.25, 'medium': 0.45, 'hard': 0.2, 'expert': 0.1}
            },
            'chemistry': {
                'topics': ['有机化学', '无机化学', '化学反应', '元素周期', '溶液'],
                'question_templates': {
                    'single_choice': [
                        ('{element}的原子序数是?', ['基础']),
                        ('{reaction}的反应类型是?', ['反应类型'])
                    ],
                    'fill_blank': [
                        ('{compound}的化学式是____', ['化学式'])
                    ]
                },
                'difficulty_weights': {'easy': 0.3, 'medium': 0.4, 'hard': 0.2, 'expert': 0.1}
            },
            'english': {
                'topics': ['词汇', '语法', '阅读理解', '完形填空', '翻译'],
                'question_templates': {
                    'single_choice': [
                        ('选择正确的{part_of_speech}:{word}', ['词汇']),
                        ('{sentence}的正确语法形式是?', ['语法'])
                    ],
                    'fill_blank': [
                        ('填入适当的词:{sentence}', ['词汇填空'])
                    ]
                },
                'difficulty_weights': {'easy': 0.35, 'medium': 0.4, 'hard': 0.2, 'expert': 0.05}
            },
            'computer': {
                'topics': ['计算机组成', '操作系统', '编程语言', '数据结构', '算法'],
                'question_templates': {
                    'single_choice': [
                        ('{component}的功能是?', ['基础']),
                        ('{concept}的特点是?', ['概念'])
                    ],
                    'code_analysis': [
                        ('以下代码的输出是:\n{code}', ['代码理解'])
                    ]
                },
                'difficulty_weights': {'easy': 0.25, 'medium': 0.4, 'hard': 0.25, 'expert': 0.1}
            },
            'programming': {
                'topics': ['Python', 'Java', 'C++', 'JavaScript', '算法实现'],
                'question_templates': {
                    'single_choice': [
                        ('{language}中,{keyword}的作用是?', ['语法']),
                        ('{concept}的时间复杂度是?', ['复杂度'])
                    ],
                    'code_analysis': [
                        ('分析代码:\n{code}', ['代码分析'])
                    ],
                    'calculation': [
                        ('实现{algorithm}算法', ['算法'])
                    ]
                },
                'difficulty_weights': {'easy': 0.2, 'medium': 0.35, 'hard': 0.3, 'expert': 0.15}
            },
            'database': {
                'topics': ['SQL', '数据库设计', '索引', '事务', '优化'],
                'question_templates': {
                    'single_choice': [
                        ('{operation}的SQL语句是?', ['SQL']),
                        ('{concept}的作用是?', ['概念'])
                    ],
                    'fill_blank': [
                        ('创建索引的SQL语句是____', ['SQL'])
                    ]
                },
                'difficulty_weights': {'easy': 0.25, 'medium': 0.4, 'hard': 0.25, 'expert': 0.1}
            },
            'network': {
                'topics': ['TCP/IP', 'HTTP', 'DNS', '网络安全', '协议'],
                'question_templates': {
                    'single_choice': [
                        ('{protocol}工作在OSI的哪一层?', ['协议']),
                        ('{concept}的特点是?', ['概念'])
                    ],
                    'fill_blank': [
                        ('TCP使用____次握手建立连接', ['协议'])
                    ]
                },
                'difficulty_weights': {'easy': 0.25, 'medium': 0.4, 'hard': 0.25, 'expert': 0.1}
            }
        }

    def _generate_task_id(self, subject: Subject) -> str:
        """生成任务ID"""
        import uuid
        return f"MG-{subject.value}-{int(time.time())}-{uuid.uuid4().hex[:4]}"

    def _generate_question_id(self) -> str:
        """生成题目ID"""
        import uuid
        return f"MQ-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def _generate_single_question(self, subject: str, q_type: str, difficulty: str) -> Dict:
        """生成单道题目"""
        config = self._subject_configs.get(subject, self._subject_configs['math'])
        topic = random.choice(config['topics'])
        
        templates = config['question_templates'].get(q_type, config['question_templates']['single_choice'])
        template, tags = random.choice(templates)
        
        question_data = {
            'question_id': self._generate_question_id(),
            'type': q_type,
            'category': self._get_category(q_type, difficulty),
            'difficulty': difficulty,
            'subject': subject,
            'topic': topic,
            'knowledge_points': [topic],
            'tags': tags,
            'score': self._get_score(difficulty),
            'source': 'AI自动生成',
            'created_at': time.time()
        }
        
        # 填充模板
        if q_type in ['single_choice', 'multiple_choice']:
            question_data['content'] = self._fill_template(template, topic, subject)
            question_data['options'] = self._generate_options()
            question_data['correct_answer'] = random.choice(['A', 'B', 'C', 'D'])
            question_data['explanation'] = f"本题考查{topic}相关知识"
            
        elif q_type == 'true_false':
            question_data['content'] = self._generate_true_false_question(topic)
            question_data['options'] = [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}]
            question_data['correct_answer'] = random.choice(['A', 'B'])
            
        elif q_type == 'fill_blank':
            question_data['content'] = self._fill_template(template, topic, subject)
            question_data['correct_answer'] = self._generate_fill_blank_answer(topic)
            
        elif q_type == 'calculation':
            question_data['content'] = self._fill_template(template, topic, subject)
            question_data['correct_answer'] = str(random.randint(1, 1000))
            question_data['formula_used'] = tags
            
        elif q_type == 'code_analysis':
            question_data['content'] = self._generate_code_question(topic)
            question_data['correct_answer'] = self._generate_code_answer()
            
        elif q_type == 'short_answer':
            question_data['content'] = f"请简述{topic}的主要特点和应用场景"
            question_data['correct_answer'] = f"{topic}的主要特点包括...应用场景包括..."
            
        return question_data

    def _fill_template(self, template: str, topic: str, subject: str) -> str:
        """填充题目模板"""
        concepts = {
            'math': ['导数', '积分', '极限', '方程', '函数', '矩阵', '向量'],
            'physics': ['牛顿定律', '能量守恒', '动量定理', '欧姆定律'],
            'chemistry': ['化学键', '化学反应', '元素周期', '溶液浓度'],
            'english': ['时态', '语态', '从句', '词汇辨析'],
            'computer': ['内存', 'CPU', '进程', '线程'],
            'programming': ['变量', '函数', '类', '继承', '多态'],
            'database': ['索引', '事务', '范式', 'SQL'],
            'network': ['TCP', 'UDP', 'HTTP', 'DNS']
        }
        
        concept_list = concepts.get(subject, concepts['math'])
        concept = random.choice(concept_list)
        
        expressions = {
            'math': ['2x + 3 = 7', 'x^2 - 4 = 0', 'sin(x) = 0.5', 'log2(8)'],
            'physics': ['F=ma', 'E=mc^2', 'P=IV', 'W=Fs'],
            'chemistry': ['H2 + O2 -> H2O', 'NaCl + AgNO3'],
            'programming': ['for i in range(10):', 'def func():', 'class Test:']
        }
        
        expression = random.choice(expressions.get(subject, expressions['math']))
        
        conditions = [
            "已知x = 5",
            "若x满足方程",
            "给定条件f(x)"
        ]
        
        return template.format(
            topic=topic,
            concept=concept,
            expression=expression,
            condition=random.choice(conditions),
            target=random.choice(['x', 'y', 'z', '结果']),
            law=random.choice(['牛顿第一定律', '能量守恒定律', '欧姆定律']),
            object=random.choice(['物体', '质点', '系统']),
            part_of_speech=random.choice(['名词', '动词', '形容词', '副词']),
            word=random.choice(['important', 'beautiful', 'difficult', 'necessary']),
            sentence='The weather is ___ today.',
            component=random.choice(['CPU', '内存', '硬盘', '网卡']),
            keyword=random.choice(['def', 'class', 'import', 'return']),
            language=random.choice(['Python', 'Java', 'C++']),
            algorithm=random.choice(['快速排序', '二分查找', '动态规划']),
            operation=random.choice(['查询', '插入', '更新', '删除']),
            protocol=random.choice(['HTTP', 'HTTPS', 'TCP', 'UDP'])
        )

    def _generate_options(self) -> List[Dict]:
        """生成选项"""
        option_values = [
            ['正确答案', '错误选项A', '错误选项B', '错误选项C'],
            ['选项A', '正确答案', '错误选项B', '错误选项C'],
            ['选项A', '选项B', '正确答案', '错误选项C'],
            ['选项A', '选项B', '选项C', '正确答案']
        ]
        selected = random.choice(option_values)
        return [{'key': k, 'value': v} for k, v in zip(['A', 'B', 'C', 'D'], selected)]

    def _generate_true_false_question(self, topic: str) -> str:
        """生成判断题"""
        statements = [
            f"{topic}是重要的基础概念",
            f"{topic}适用于所有情况",
            f"{topic}的时间复杂度为O(n)",
            f"{topic}可以提高系统性能"
        ]
        return random.choice(statements)

    def _generate_fill_blank_answer(self, topic: str) -> str:
        """生成填空题答案"""
        answers = {
            'math': ['2', '3', '4', 'π', 'e', '0'],
            'physics': ['9.8', '3e8', 'F=ma', 'E=mc²'],
            'chemistry': ['H2O', 'NaCl', 'CO2', 'O2'],
            'english': ['is', 'are', 'was', 'were', 'have'],
            'computer': ['CPU', 'RAM', 'ROM', 'GPU'],
            'programming': ['def', 'class', 'import', 'return'],
            'database': ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
            'network': ['3', '4', 'TCP', 'UDP']
        }
        return random.choice(answers.get(topic.split()[0], answers['math']))

    def _generate_code_question(self, topic: str) -> str:
        """生成代码题"""
        codes = {
            'Python': ['print("Hello")', 'for i in range(5):\n    print(i)', 'x = 1 + 2'],
            'Java': ['System.out.println("Hello");', 'int x = 1 + 2;'],
            '数据结构': ['arr.sort()', 'list.append(x)', 'dict[key] = value']
        }
        return f"分析以下{topic}代码的输出:\n{random.choice(codes.get(topic, codes['Python']))}"

    def _generate_code_answer(self) -> str:
        """生成代码题答案"""
        return random.choice(['Hello', '0 1 2 3 4', '3', 'None'])

    def _get_category(self, q_type: str, difficulty: str) -> str:
        """获取题目类别"""
        if difficulty in ['hard', 'expert']:
            return 'final' if random.random() > 0.5 else 'must_know'
        elif q_type == 'calculation':
            return 'calculation'
        elif q_type == 'logic_judgment':
            return 'logic'
        else:
            return 'special_topic'

    def _get_score(self, difficulty: str) -> float:
        """获取题目分值"""
        scores = {'easy': 3.0, 'medium': 5.0, 'hard': 8.0, 'expert': 12.0}
        return scores.get(difficulty, 5.0)

    def _generate_batch(self, subject: str, count: int) -> List[Dict]:
        """批量生成题目"""
        config = self._subject_configs.get(subject, self._subject_configs['math'])
        difficulty_weights = config['difficulty_weights']
        question_types = list(config['question_templates'].keys())
        
        questions = []
        for _ in range(count):
            # 选择难度
            difficulty = random.choices(
                list(difficulty_weights.keys()),
                weights=list(difficulty_weights.values())
            )[0]
            
            # 选择题型
            q_type = random.choice(question_types)
            
            question = self._generate_question_id()
            questions.append(self._generate_single_question(subject, q_type, difficulty))
        
        return questions

    def _save_batch(self, questions: List[Dict]) -> int:
        """批量保存题目"""
        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            
            success = 0
            for q in questions:
                try:
                    enhanced_question_bank_service.add_question(q)
                    success += 1
                except Exception:
                    continue
            
            return success
        except Exception as e:
            logger.error(f"批量保存失败: {str(e)}")
            return 0

    def generate_for_subject(self, subject: Subject, count: int = 10000000) -> str:
        """为指定科目生成题目"""
        task_id = self._generate_task_id(subject)
        
        task = GenerationTask(
            task_id=task_id,
            subject=subject,
            target_count=count,
            status="running",
            started_at=time.time()
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        logger.info(f"开始生成{subject.value}科目题目,目标: {count:,}道")
        
        batch_size = 1000
        total_batches = (count + batch_size - 1) // batch_size
        start_time = time.time()
        
        for batch_num in range(total_batches):
            # 检查任务是否被取消
            with self._lock:
                if self._tasks[task_id].status == "cancelled":
                    logger.info(f"任务{task_id}已取消")
                    return task_id
            
            # 生成批次
            remaining = count - task.generated_count
            current_batch_size = min(batch_size, remaining)
            
            questions = self._generate_batch(subject.value, current_batch_size)
            saved = self._save_batch(questions)
            
            # 更新任务状态
            with self._lock:
                task = self._tasks[task_id]
                task.generated_count += current_batch_size
                task.saved_count += saved
                task.progress = (task.generated_count / count) * 100
                
                elapsed = time.time() - start_time
                if task.generated_count > 0:
                    avg_time_per_batch = elapsed / (batch_num + 1)
                    remaining_batches = total_batches - batch_num - 1
                    task.estimated_remaining = avg_time_per_batch * remaining_batches / 60  # 分钟
            
            # 进度日志
            if (batch_num + 1) % 100 == 0:
                logger.info(f"{subject.value} - 已生成 {task.generated_count:,}/{count:,} ({task.progress:.1f}%)")
        
        # 完成任务
        with self._lock:
            task = self._tasks[task_id]
            task.status = "completed"
            task.completed_at = time.time()
        
        logger.info(f"{subject.value}科目题目生成完成,共生成{task.saved_count:,}道")
        
        return task_id

    def generate_for_all_subjects(self, count_per_subject: int = 10000000) -> List[str]:
        """为所有科目生成题目"""
        task_ids = []
        
        for subject in Subject:
            task_id = self.generate_for_subject(subject, count_per_subject)
            task_ids.append(task_id)
        
        return task_ids

    def get_task(self, task_id: str) -> Optional[GenerationTask]:
        """获取任务状态"""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[GenerationTask]:
        """列出所有任务"""
        return list(self._tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = "cancelled"
                return True
        return False

    def generate_concurrent(self, subjects: List[Subject], count_per_subject: int = 10000000):
        """并发生成多个科目"""
        processes = []
        
        for subject in subjects:
            p = multiprocessing.Process(
                target=self.generate_for_subject,
                args=(subject, count_per_subject)
            )
            processes.append(p)
            p.start()
        
        for p in processes:
            p.join()


# 创建全局实例
massive_question_generator = MassiveQuestionGenerator()


def generate_massive_question_bank(subjects: List[str] = None, count_per_subject: int = 10000000):
    """生成海量题库"""
    logger.info(f"开始生成海量题库,每个科目{count_per_subject:,}道题")
    
    if subjects is None:
        subjects_list = list(Subject)
    else:
        subjects_list = [Subject(s) for s in subjects if s in [e.value for e in Subject]]
    
    results = {}
    
    for subject in subjects_list:
        logger.info(f"正在生成{subject.value}科目...")
        task_id = massive_question_generator.generate_for_subject(subject, count_per_subject)
        task = massive_question_generator.get_task(task_id)
        results[subject.value] = {
            'task_id': task_id,
            'generated': task.generated_count,
            'saved': task.saved_count,
            'status': task.status
        }
    
    logger.info(f"海量题库生成完成: {results}")
    return results
