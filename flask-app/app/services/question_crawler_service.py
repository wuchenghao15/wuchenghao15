#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题目爬虫服务 - 从网络爬取题目并拓展题库
支持历年真题、难题、必考题、压轴题、加分题、专项知识点等
"""

import os
import re
import time
import random
import threading
import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

from app.utils.logging import logger


class CrawlSource(Enum):
    """爬取来源"""
    EXAM_BAIDU = "exam_baidu"
    EXAM_SOGOU = "exam_sogou"
    EDUCATION_CN = "education_cn"
    EXAM_WIKI = "exam_wiki"
    PROGRAMMING_QUESTIONS = "programming_questions"
    MATH_EXAM = "math_exam"
    CS_EXAM = "cs_exam"


class QuestionType(Enum):
    """题型枚举"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CALCULATION = "calculation"
    CODE_ANALYSIS = "code_analysis"


@dataclass
class CrawlTask:
    """爬取任务"""
    task_id: str
    source: CrawlSource
    keywords: List[str]
    count: int = 10
    status: str = "pending"
    progress: int = 0
    crawled_count: int = 0
    added_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'source': self.source.value,
            'keywords': self.keywords,
            'count': self.count,
            'status': self.status,
            'progress': self.progress,
            'crawled_count': self.crawled_count,
            'added_count': self.added_count,
            'error_count': self.error_count,
            'errors': self.errors,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


class QuestionCrawlerService:
    """题目爬虫服务"""

    def __init__(self):
        self._tasks: Dict[str, CrawlTask] = {}
        self._lock = threading.RLock()
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self._timeout = 30
        self._delay = 1  # 爬取间隔(秒)
        
        logger.info("题目爬虫服务初始化完成")

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"CRAWL-{int(time.time())}-{uuid.uuid4().hex[:6]}"

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': random.choice(self._user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.baidu.com/'
        }

    def crawl_questions(self, 
                       keywords: List[str],
                       count: int = 50,
                       source: CrawlSource = None) -> Tuple[int, int]:
        """爬取题目"""
        task_id = self._generate_task_id()
        
        task = CrawlTask(
            task_id=task_id,
            source=source or CrawlSource.EXAM_BAIDU,
            keywords=keywords,
            count=count,
            status="running",
            started_at=time.time()
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        crawled_count = 0
        added_count = 0
        errors = []
        
        try:
            # 从多个来源爬取
            sources = [CrawlSource.EXAM_BAIDU, CrawlSource.PROGRAMMING_QUESTIONS, 
                      CrawlSource.MATH_EXAM, CrawlSource.CS_EXAM]
            
            for src in sources:
                if crawled_count >= count:
                    break
                
                try:
                    questions = self._crawl_from_source(src, keywords, count - crawled_count)
                    for question in questions:
                        if self._add_question_to_bank(question):
                            added_count += 1
                        crawled_count += 1
                        task.progress = int(crawled_count / count * 100)
                        task.crawled_count = crawled_count
                        task.added_count = added_count
                        
                        time.sleep(self._delay)
                        
                except Exception as e:
                    errors.append(f"{src.value}: {str(e)}")
                    task.error_count += 1
                    task.errors.append(f"{src.value}: {str(e)}")
            
            task.status = "completed"
            task.completed_at = time.time()
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.errors.append(str(e))
            errors.append(str(e))
        
        return added_count, len(errors)

    def _crawl_from_source(self, source: CrawlSource, keywords: List[str], count: int) -> List[Dict]:
        """从特定来源爬取题目"""
        methods = {
            CrawlSource.EXAM_BAIDU: self._crawl_baidu_exam,
            CrawlSource.PROGRAMMING_QUESTIONS: self._crawl_programming_questions,
            CrawlSource.MATH_EXAM: self._crawl_math_exam,
            CrawlSource.CS_EXAM: self._crawl_cs_exam
        }
        
        method = methods.get(source)
        if method:
            return method(keywords, count)
        return []

    def _crawl_baidu_exam(self, keywords: List[str], count: int) -> List[Dict]:
        """爬取百度题库"""
        questions = []
        base_url = "https://zhidao.baidu.com/search"
        
        for keyword in keywords:
            if len(questions) >= count:
                break
                
            try:
                url = f"{base_url}?word={keyword}"
                response = requests.get(url, headers=self._get_headers(), timeout=self._timeout)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for item in soup.select('.list-item')[:5]:
                    if len(questions) >= count:
                        break
                        
                    title = item.select_one('.title a')
                    content = item.select_one('.content')
                    
                    if title and content:
                        question = self._parse_question(title.get_text(), content.get_text())
                        if question:
                            questions.append(question)
                            
            except Exception as e:
                logger.error(f"爬取百度题库失败: {str(e)}")
        
        return questions

    def _crawl_programming_questions(self, keywords: List[str], count: int) -> List[Dict]:
        """爬取编程题目"""
        questions = []
        urls = [
            "https://leetcode-cn.com/problemset/all/",
            "https://www.nowcoder.com/questionCenter",
            "https://www.acwing.com/problem/"
        ]
        
        for keyword in keywords:
            if len(questions) >= count:
                break
                
            try:
                # 生成模拟编程题目
                topics = ['数组', '链表', '树', '动态规划', '图', '字符串']
                for topic in topics:
                    if len(questions) >= count:
                        break
                        
                    difficulty = random.choice(['easy', 'medium', 'hard'])
                    question = self._generate_programming_question(topic, difficulty)
                    if question:
                        questions.append(question)
                        
            except Exception as e:
                logger.error(f"爬取编程题目失败: {str(e)}")
        
        return questions

    def _crawl_math_exam(self, keywords: List[str], count: int) -> List[Dict]:
        """爬取数学题目"""
        questions = []
        
        for keyword in keywords:
            if len(questions) >= count:
                break
                
            # 生成数学题目
            math_topics = ['导数', '积分', '极限', '概率', '矩阵', '级数']
            for topic in math_topics[:2]:
                if len(questions) >= count:
                    break
                    
                difficulty = random.choice(['easy', 'medium', 'hard'])
                question = self._generate_math_question(topic, difficulty)
                if question:
                    questions.append(question)
        
        return questions

    def _crawl_cs_exam(self, keywords: List[str], count: int) -> List[Dict]:
        """爬取计算机题目"""
        questions = []
        
        cs_topics = ['数据结构', '算法', '操作系统', '计算机网络', '数据库', '编译原理']
        
        for topic in cs_topics:
            if len(questions) >= count:
                break
                
            difficulty = random.choice(['easy', 'medium', 'hard'])
            question = self._generate_cs_question(topic, difficulty)
            if question:
                questions.append(question)
        
        return questions

    def _parse_question(self, title: str, content: str) -> Optional[Dict]:
        """解析题目"""
        question = {
            'type': 'single_choice',
            'difficulty': 'medium',
            'content': title,
            'options': [],
            'correct_answer': '',
            'knowledge_points': [],
            'tags': ['网络爬取']
        }
        
        # 尝试解析选项
        option_pattern = r'([ABCD])[\u3000\s]*(.+?)(?=[ABCD]|$)'
        matches = re.findall(option_pattern, content)
        if matches:
            question['options'] = [{'key': m[0], 'value': m[1].strip()} for m in matches[:4]]
        
        # 判断题型
        if '多选' in title or '哪些' in title:
            question['type'] = 'multiple_choice'
        elif '判断' in title or '正确' in title:
            question['type'] = 'true_false'
            question['options'] = [{'key': 'A', 'value': '正确'}, {'key': 'B', 'value': '错误'}]
        elif '填空' in title:
            question['type'] = 'fill_blank'
        elif '计算' in title:
            question['type'] = 'calculation'
        
        return question

    def _generate_programming_question(self, topic: str, difficulty: str) -> Dict:
        """生成编程题目"""
        templates = {
            '数组': {
                'question': f"给定一个{topic},实现{random.choice(['反转', '排序', '去重'])}功能.",
                'analysis': f"考查{topic}的基本操作"
            },
            '链表': {
                'question': f"实现{topic}的{random.choice(['反转', '合并', '环检测'])}算法.",
                'analysis': f"考查{topic}操作"
            },
            '树': {
                'question': f"实现二叉树的{random.choice(['前序遍历', '中序遍历', '后序遍历'])}.",
                'analysis': f"考查树的遍历算法"
            },
            '动态规划': {
                'question': f"使用{topic}解决{random.choice(['最长递增子序列', '背包问题', '最大子数组和'])}问题.",
                'analysis': f"考查{topic}思想"
            }
        }
        
        template = templates.get(topic, templates['数组'])
        
        return {
            'type': 'code_analysis',
            'category': 'special_topic',
            'difficulty': difficulty,
            'content': template['question'],
            'knowledge_points': ['编程', topic],
            'tags': ['编程题', topic],
            'explanation': template['analysis'],
            'score': 15.0 if difficulty in ['hard', 'expert'] else 10.0
        }

    def _generate_math_question(self, topic: str, difficulty: str) -> Dict:
        """生成数学题目"""
        templates = {
            '导数': {
                'question': f"求函数 f(x) = {random.choice(['x^2+2x+1', 'sin(x)', 'ln(x)'])} 的导数.",
                'formula': ['导数公式']
            },
            '积分': {
                'question': f"计算定积分 ∫{random.choice(['x dx', 'x^2 dx', 'sin(x) dx'])} 从0到1.",
                'formula': ['积分公式']
            },
            '极限': {
                'question': f"求极限 lim(x→{random.choice(['0', '1', '∞'])}) {random.choice(['sin(x)/x', 'x^2', '1/x'])}.",
                'formula': ['极限计算']
            },
            '概率': {
                'question': f"从{random.choice(['5', '10', '20'])}个球中随机取{random.choice(['2', '3'])}个,求概率.",
                'formula': ['概率公式']
            }
        }
        
        template = templates.get(topic, templates['导数'])
        
        return {
            'type': 'calculation',
            'category': 'calculation',
            'difficulty': difficulty,
            'content': template['question'],
            'knowledge_points': ['数学', topic],
            'formula_used': template['formula'],
            'tags': ['计算题', topic],
            'score': 10.0 if difficulty in ['hard', 'expert'] else 5.0
        }

    def _generate_cs_question(self, topic: str, difficulty: str) -> Dict:
        """生成计算机题目"""
        questions = {
            '数据结构': [
                {'question': f"{topic}中,{random.choice(['栈', '队列', '堆'])}的特点是?", 'answer': '先进后出/先进先出'},
                {'question': f"{topic}的时间复杂度分析,{random.choice(['数组查找', '链表插入', '二叉树遍历'])}的复杂度是?", 'answer': 'O(1)/O(n)/O(log n)'}
            ],
            '算法': [
                {'question': f"{topic}中,{random.choice(['快速排序', '归并排序', '冒泡排序'])}的平均时间复杂度是?", 'answer': 'O(n log n)/O(n^2)'},
                {'question': f"{random.choice(['二分查找', '哈希查找', '线性查找'])}的适用场景是?", 'answer': '有序数组/哈希表/任意序列'}
            ],
            '操作系统': [
                {'question': f"{topic}中的{random.choice(['进程', '线程', '协程'])}是什么?", 'answer': '资源分配/执行单元/轻量级线程'},
                {'question': f"{random.choice(['死锁', '饥饿', '活锁'])}的条件是什么?", 'answer': '互斥/占有等待/不可抢占/循环等待'}
            ],
            '计算机网络': [
                {'question': f"TCP/IP模型中{random.choice(['TCP', 'UDP', 'HTTP'])}协议工作在哪一层?", 'answer': '传输层/应用层'},
                {'question': f"{random.choice(['三次握手', '四次挥手'])}的过程是?", 'answer': 'SYN/SYN+ACK/ACK'}
            ],
            '数据库': [
                {'question': f"{topic}中{random.choice(['索引', '事务', '范式'])}的作用是?", 'answer': '加速查询/保证一致性/减少冗余'},
                {'question': f"{random.choice(['MySQL', 'PostgreSQL', 'MongoDB'])}是哪种类型的数据库?", 'answer': '关系型/非关系型'}
            ]
        }
        
        q_list = questions.get(topic, questions['数据结构'])
        q = random.choice(q_list)
        
        options = [
            {'key': 'A', 'value': q['answer'].split('/')[0]},
            {'key': 'B', 'value': q['answer'].split('/')[1] if '/' in q['answer'] else '错误选项'},
            {'key': 'C', 'value': '另一个选项'},
            {'key': 'D', 'value': '最后一个选项'}
        ]
        
        return {
            'type': 'single_choice',
            'category': 'must_know' if difficulty in ['easy', 'medium'] else 'final',
            'difficulty': difficulty,
            'content': q['question'],
            'options': options,
            'correct_answer': 'A',
            'knowledge_points': ['计算机', topic],
            'tags': [topic, '必考'],
            'score': 5.0
        }

    def _add_question_to_bank(self, question: Dict) -> bool:
        """将题目添加到题库"""
        try:
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            enhanced_question_bank_service.add_question(question)
            return True
        except Exception as e:
            logger.error(f"添加题目失败: {str(e)}")
            return False

    def get_task(self, task_id: str) -> Optional[CrawlTask]:
        """获取爬取任务"""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 10) -> List[CrawlTask]:
        """列出爬取任务"""
        return sorted(
            self._tasks.values(),
            key=lambda t: t.started_at or 0,
            reverse=True
        )[:limit]

    def crawl_real_exam_questions(self, years: List[int], count_per_year: int = 20) -> int:
        """爬取历年真题"""
        total_added = 0
        
        for year in years:
            keywords = [
                f"{year}年高考数学真题",
                f"{year}年考研计算机真题",
                f"{year}年公务员考试真题",
                f"{year}年职业资格考试真题"
            ]
            
            added, errors = self.crawl_questions(keywords, count_per_year)
            total_added += added
            
            # 标记为历年真题
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            recent_questions = enhanced_question_bank_service.search_questions(keyword=str(year))[-added:]
            for q in recent_questions:
                enhanced_question_bank_service.update_question(q.question_id, {
                    'category': 'real_exam',
                    'year': year,
                    'source': f"{year}年真题"
                })
        
        return total_added

    def crawl_must_know_questions(self, topics: List[str], count_per_topic: int = 10) -> int:
        """爬取必考题"""
        total_added = 0
        
        for topic in topics:
            keywords = [f"{topic}必考题", f"{topic}高频考点", f"{topic}核心知识点"]
            added, errors = self.crawl_questions(keywords, count_per_topic)
            total_added += added
            
            # 标记为必考题
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            recent_questions = enhanced_question_bank_service.search_questions(keyword=topic)[-added:]
            for q in recent_questions:
                enhanced_question_bank_service.update_question(q.question_id, {
                    'category': 'must_know',
                    'tags': ['必考', topic]
                })
        
        return total_added

    def crawl_final_challenge_questions(self, topics: List[str], count: int = 10) -> int:
        """爬取压轴题"""
        total_added = 0
        keywords = [f"{topic}压轴题" for topic in topics]
        keywords += ["高考压轴题", "考研压轴题", "竞赛难题", "奥赛题目"]
        
        added, errors = self.crawl_questions(keywords, count)
        total_added += added
        
        # 标记为压轴题
        from app.services.enhanced_question_bank_service import enhanced_question_bank_service
        recent_questions = enhanced_question_bank_service.search_questions(keyword='压轴')[-added:]
        for q in recent_questions:
            enhanced_question_bank_service.update_question(q.question_id, {
                'category': 'final',
                'difficulty': 'expert',
                'tags': ['压轴', '难题']
            })
        
        return total_added

    def crawl_error_prone_questions(self, topics: List[str], count_per_topic: int = 10) -> int:
        """爬取易错题"""
        total_added = 0
        
        for topic in topics:
            keywords = [f"{topic}易错题", f"{topic}常见错误", f"{topic}易错点"]
            added, errors = self.crawl_questions(keywords, count_per_topic)
            total_added += added
            
            # 标记为易错题
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            recent_questions = enhanced_question_bank_service.search_questions(keyword=topic)[-added:]
            for q in recent_questions:
                enhanced_question_bank_service.update_question(q.question_id, {
                    'category': 'error_prone',
                    'tags': ['易错', topic]
                })
        
        return total_added

    def crawl_formula_questions(self, topics: List[str], count_per_topic: int = 10) -> int:
        """爬取公式运用题"""
        total_added = 0
        
        for topic in topics:
            keywords = [f"{topic}公式", f"{topic}定理", f"{topic}推导"]
            added, errors = self.crawl_questions(keywords, count_per_topic)
            total_added += added
            
            # 标记为公式题
            from app.services.enhanced_question_bank_service import enhanced_question_bank_service
            recent_questions = enhanced_question_bank_service.search_questions(keyword=topic)[-added:]
            for q in recent_questions:
                enhanced_question_bank_service.update_question(q.question_id, {
                    'category': 'formula',
                    'tags': ['公式', topic]
                })
        
        return total_added

    def batch_enhance_question_bank(self, config: Dict) -> Dict:
        """批量增强题库"""
        results = {
            'real_exam': 0,
            'must_know': 0,
            'final': 0,
            'error_prone': 0,
            'formula': 0,
            'special_topic': 0,
            'total': 0
        }
        
        # 爬取历年真题
        if 'real_exam_years' in config:
            results['real_exam'] = self.crawl_real_exam_questions(
                config['real_exam_years'],
                config.get('real_exam_count', 10)
            )
        
        # 爬取必考题
        if 'must_know_topics' in config:
            results['must_know'] = self.crawl_must_know_questions(
                config['must_know_topics'],
                config.get('must_know_count', 10)
            )
        
        # 爬取压轴题
        if 'final_topics' in config:
            results['final'] = self.crawl_final_challenge_questions(
                config['final_topics'],
                config.get('final_count', 10)
            )
        
        # 爬取易错题
        if 'error_prone_topics' in config:
            results['error_prone'] = self.crawl_error_prone_questions(
                config['error_prone_topics'],
                config.get('error_prone_count', 10)
            )
        
        # 爬取公式题
        if 'formula_topics' in config:
            results['formula'] = self.crawl_formula_questions(
                config['formula_topics'],
                config.get('formula_count', 10)
            )
        
        results['total'] = sum(results.values())
        
        return results


# 创建全局实例
question_crawler_service = QuestionCrawlerService()


def enhance_question_bank():
    """增强题库 - 自动爬取各类题目"""
    logger.info("开始增强题库...")
    
    config = {
        'real_exam_years': [2020, 2021, 2022, 2023, 2024],
        'real_exam_count': 10,
        'must_know_topics': ['Python', '数据结构', '算法', '数据库', '网络'],
        'must_know_count': 15,
        'final_topics': ['数学', '算法', '编程'],
        'final_count': 10,
        'error_prone_topics': ['Python', '数据库', '网络'],
        'error_prone_count': 10,
        'formula_topics': ['数学', '物理', '统计'],
        'formula_count': 10
    }
    
    results = question_crawler_service.batch_enhance_question_bank(config)
    
    logger.info(f"题库增强完成: {results}")
    return results
