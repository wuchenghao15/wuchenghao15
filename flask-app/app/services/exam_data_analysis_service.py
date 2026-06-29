# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试数据分析服务模块
提供成绩分布分析、题目难度分析、知识点掌握度分析等数据统计功能
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
import logging
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class ScoreDistribution:
    """成绩分布数据"""
    score_ranges: Dict[str, int] = field(default_factory=dict)  # 分数段分布
    mean: float = 0.0  # 平均分
    median: float = 0.0  # 中位数
    std_dev: float = 0.0  # 标准差
    min_score: float = 0.0  # 最低分
    max_score: float = 0.0  # 最高分
    mode: float = 0.0  # 众数
    percentile_25: float = 0.0  # 25%分位数
    percentile_75: float = 0.0  # 75%分位数


@dataclass
class QuestionDifficultyAnalysis:
    """题目难度分析数据"""
    question_id: str = ""
    difficulty_level: int = 1
    correct_rate: float = 0.0  # 正确率
    avg_time_spent: float = 0.0  # 平均答题时间
    discrimination_index: float = 0.0  # 区分度指数
    difficulty_index: float = 0.0  # 难度指数
    point_biserial: float = 0.0  # 点双序列相关系数
    analysis_result: str = ""  # 分析结果描述


@dataclass
class KnowledgePointMastery:
    """知识点掌握度数据"""
    knowledge_point: str = ""
    total_questions: int = 0  # 该知识点总题目数
    correct_count: int = 0  # 正确答题数
    mastery_rate: float = 0.0  # 掌握率
    avg_time: float = 0.0  # 平均答题时间
    difficulty_avg: float = 0.0  # 平均难度
    mastery_level: str = ""  # 掌握程度评级


@dataclass
class ExamAnalysisReport:
    """考试分析报告"""
    exam_id: str = ""
    total_participants: int = 0
    score_distribution: ScoreDistribution = field(default_factory=ScoreDistribution)
    question_analyses: List[QuestionDifficultyAnalysis] = field(default_factory=list)
    knowledge_mastery: List[KnowledgePointMastery] = field(default_factory=list)
    overall_statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ExamDataAnalysisService:
    """考试数据分析服务"""
    
    # 掌握程度评级阈值
    MASTERY_THRESHOLDS = {
        'excellent': {'min': 90, 'label': '优秀掌握'},
        'good': {'min': 75, 'label': '良好掌握'},
        'average': {'min': 60, 'label': '基本掌握'},
        'weak': {'min': 40, 'label': '掌握薄弱'},
        'poor': {'min': 0, 'label': '严重不足'}
    }
    
    # 题目难度评估标准
    DIFFICULTY_STANDARDS = {
        'easy': {'correct_rate_min': 0.7, 'label': '简单'},
        'medium_easy': {'correct_rate_min': 0.6, 'label': '较易'},
        'medium': {'correct_rate_min': 0.5, 'label': '中等'},
        'medium_hard': {'correct_rate_min': 0.4, 'label': '较难'},
        'hard': {'correct_rate_min': 0, 'label': '困难'}
    }
    
    # 分数段配置
    SCORE_RANGES = [
        ('0-59', 0, 59, '不及格'),
        ('60-69', 60, 69, '及格'),
        ('70-79', 70, 79, '中等'),
        ('80-89', 80, 89, '良好'),
        ('90-100', 90, 100, '优秀')
    ]
    
    def __init__(self, db_path="app.db"):
        """初始化数据分析服务"""
        self.db_path = db_path
        self._init_tables()
        logger.info("考试数据分析服务初始化完成")
    
    def _connect(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化数据分析相关表"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 分析结果缓存表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_analysis_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analysis_data TEXT NOT NULL,
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        UNIQUE(exam_id, analysis_type)
                    )
                ''')
                
                # 题目统计汇总表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS question_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_id TEXT NOT NULL,
                        exam_id TEXT NOT NULL,
                        total_attempts INTEGER DEFAULT 0,
                        correct_attempts INTEGER DEFAULT 0,
                        correct_rate REAL DEFAULT 0.0,
                        avg_time_spent REAL DEFAULT 0.0,
                        discrimination_index REAL DEFAULT 0.0,
                        difficulty_index REAL DEFAULT 0.0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(question_id, exam_id)
                    )
                ''')
                
                # 知识点统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_point_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        knowledge_point TEXT NOT NULL,
                        exam_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        total_questions INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        mastery_rate REAL DEFAULT 0.0,
                        avg_time REAL DEFAULT 0.0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(knowledge_point, exam_id, user_id)
                    )
                ''')
                
                conn.commit()
                logger.info("数据分析数据表初始化完成")
        except Exception as e:
            logger.error(f"初始化数据分析数据表失败: {str(e)}")
    
    def analyze_score_distribution(self, exam_id: str) -> ScoreDistribution:
        """
        分析成绩分布
        
        Args:
            exam_id: 考试ID
        
        Returns:
            成绩分布数据
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 获取所有成绩
                cursor.execute('''
                    SELECT total_score FROM exam_results WHERE exam_id = ?
                ''', (exam_id,))
                
                scores = [row[0] for row in cursor.fetchall()]
                
                if not scores:
                    return ScoreDistribution()
                
                distribution = ScoreDistribution()
                
                # 计算基本统计量
                distribution.mean = sum(scores) / len(scores)
                distribution.min_score = min(scores)
                distribution.max_score = max(scores)
                
                # 计算标准差
                variance = sum((s - distribution.mean) ** 2 for s in scores) / len(scores)
                distribution.std_dev = math.sqrt(variance)
                
                # 计算中位数
                sorted_scores = sorted(scores)
                n = len(sorted_scores)
                if n % 2 == 0:
                    distribution.median = (sorted_scores[n//2 - 1] + sorted_scores[n//2]) / 2
                else:
                    distribution.median = sorted_scores[n//2]
                
                # 计算众数
                score_counts = defaultdict(int)
                for s in scores:
                    score_counts[s] += 1
                distribution.mode = max(score_counts.items(), key=lambda x: x[1])[0]
                
                # 计算分位数
                distribution.percentile_25 = sorted_scores[int(n * 0.25)]
                distribution.percentile_75 = sorted_scores[int(n * 0.75)]
                
                # 计算分数段分布
                for range_name, min_val, max_val, label in self.SCORE_RANGES:
                    count = sum(1 for s in scores if min_val <= s <= max_val)
                    distribution.score_ranges[range_name] = {
                        'count': count,
                        'percentage': count / len(scores) * 100,
                        'label': label
                    }
                
                logger.info(f"成绩分布分析完成: 平均分 {distribution.mean:.2f}")
                
                return distribution
                
        except Exception as e:
            logger.error(f"成绩分布分析失败: {str(e)}")
            return ScoreDistribution()
    
    def analyze_question_difficulty(self, exam_id: str) -> List[QuestionDifficultyAnalysis]:
        """
        分析题目难度
        
        Args:
            exam_id: 考试ID
        
        Returns:
            题目难度分析列表
        """
        try:
            analyses = []
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 获取该考试的所有题目及其答题情况
                cursor.execute('''
                    SELECT qa.question_id, qa.is_correct, qa.time_spent, qa.difficulty,
                           qa.correct_answer, qa.selected_answer
                    FROM question_analysis qa
                    WHERE qa.exam_id = ?
                ''', (exam_id,))
                
                question_data = defaultdict(lambda: {
                    'attempts': [],
                    'correct_count': 0,
                    'total_count': 0,
                    'time_spents': [],
                    'difficulty': 1
                })
                
                for row in cursor.fetchall():
                    question_id = row[0]
                    is_correct = row[1]
                    time_spent = row[2]
                    difficulty = row[3]
                    
                    question_data[question_id]['attempts'].append({
                        'is_correct': is_correct,
                        'time_spent': time_spent
                    })
                    question_data[question_id]['total_count'] += 1
                    if is_correct:
                        question_data[question_id]['correct_count'] += 1
                    question_data[question_id]['time_spents'].append(time_spent)
                    question_data[question_id]['difficulty'] = difficulty
                
                # 计算每道题的难度指标
                for question_id, data in question_data.items():
                    analysis = QuestionDifficultyAnalysis()
                    analysis.question_id = question_id
                    analysis.difficulty_level = data['difficulty']
                    
                    # 计算正确率（难度指数）
                    if data['total_count'] > 0:
                        analysis.correct_rate = data['correct_count'] / data['total_count']
                        analysis.difficulty_index = 1 - analysis.correct_rate
                    
                    # 计算平均答题时间
                    if data['time_spents']:
                        analysis.avg_time_spent = sum(data['time_spents']) / len(data['time_spents'])
                    
                    # 计算区分度指数（简化版本）
                    # 区分度 = 高分组正确率 - 低分组正确率
                    analysis.discrimination_index = self._calculate_discrimination_index(
                        data['attempts']
                    )
                    
                    # 确定难度评级
                    analysis.analysis_result = self._evaluate_difficulty_level(analysis)
                    
                    analyses.append(analysis)
            
            logger.info(f"题目难度分析完成: 分析了 {len(analyses)} 道题目")
            
            return analyses
            
        except Exception as e:
            logger.error(f"题目难度分析失败: {str(e)}")
            return []
    
    def _calculate_discrimination_index(self, attempts: List[Dict]) -> float:
        """计算区分度指数"""
        if len(attempts) < 10:
            return 0.0
        
        # 按总分排序答题记录（这里简化处理）
        # 将答题记录分为高分组和低分组（各27%）
        sorted_attempts = sorted(attempts, key=lambda x: x.get('total_score', 0) if 'total_score' in x else x['is_correct'])
        
        n = len(sorted_attempts)
        high_group = sorted_attempts[int(n * 0.73):]
        low_group = sorted_attempts[:int(n * 0.27)]
        
        if high_group and low_group:
            high_correct_rate = sum(1 for a in high_group if a['is_correct']) / len(high_group)
            low_correct_rate = sum(1 for a in low_group if a['is_correct']) / len(low_group)
            return high_correct_rate - low_correct_rate
        
        return 0.0
    
    def _evaluate_difficulty_level(self, analysis: QuestionDifficultyAnalysis) -> str:
        """评估题目难度"""
        # 根据正确率判断实际难度
        if analysis.correct_rate >= 0.7:
            level = '简单'
        elif analysis.correct_rate >= 0.6:
            level = '较易'
        elif analysis.correct_rate >= 0.5:
            level = '中等'
        elif analysis.correct_rate >= 0.4:
            level = '较难'
        else:
            level = '困难'
        
        # 根据区分度判断题目质量
        if analysis.discrimination_index >= 0.3:
            quality = '区分度良好'
        elif analysis.discrimination_index >= 0.2:
            quality = '区分度一般'
        else:
            quality = '区分度不足'
        
        # 检查难度与预期是否匹配
        expected_difficulty = {
            1: '简单', 2: '较易', 3: '中等', 4: '较难', 5: '困难'
        }
        expected = expected_difficulty.get(analysis.difficulty_level, '中等')
        
        if level == expected:
            match = '难度与预期匹配'
        else:
            match = f'实际难度({level})与预期({expected})不匹配'
        
        return f"{level}，{quality}，{match}"
    
    def analyze_knowledge_mastery(
        self,
        exam_id: str,
        user_id: Optional[str] = None
    ) -> List[KnowledgePointMastery]:
        """
        分析知识点掌握度
        
        Args:
            exam_id: 考试ID
            user_id: 用户ID（可选，如果不提供则分析整体）
        
        Returns:
            知识点掌握度列表
        """
        try:
            mastery_list = []
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    # 分析单个用户的知识点掌握度
                    cursor.execute('''
                        SELECT qa.tags, qa.is_correct, qa.time_spent, qa.difficulty
                        FROM question_analysis qa
                        WHERE qa.exam_id = ? AND qa.user_id = ?
                    ''', (exam_id, user_id))
                else:
                    # 分析整体知识点掌握度
                    cursor.execute('''
                        SELECT qa.tags, qa.is_correct, qa.time_spent, qa.difficulty
                        FROM question_analysis qa
                        WHERE qa.exam_id = ?
                    ''', (exam_id,))
                
                knowledge_data = defaultdict(lambda: {
                    'total': 0,
                    'correct': 0,
                    'time_spents': [],
                    'difficulties': []
                })
                
                for row in cursor.fetchall():
                    tags_json = row[0]
                    is_correct = row[1]
                    time_spent = row[2]
                    difficulty = row[3]
                    
                    try:
                        tags = json.loads(tags_json) if tags_json else []
                    except json.JSONDecodeError:
                        tags = []
                    
                    for tag in tags:
                        knowledge_data[tag]['total'] += 1
                        if is_correct:
                            knowledge_data[tag]['correct'] += 1
                        knowledge_data[tag]['time_spents'].append(time_spent)
                        knowledge_data[tag]['difficulties'].append(difficulty)
                
                # 计算每个知识点的掌握度
                for knowledge_point, data in knowledge_data.items():
                    mastery = KnowledgePointMastery()
                    mastery.knowledge_point = knowledge_point
                    mastery.total_questions = data['total']
                    mastery.correct_count = data['correct']
                    
                    if data['total'] > 0:
                        mastery.mastery_rate = data['correct'] / data['total'] * 100
                    
                    if data['time_spents']:
                        mastery.avg_time = sum(data['time_spents']) / len(data['time_spents'])
                    
                    if data['difficulties']:
                        mastery.difficulty_avg = sum(data['difficulties']) / len(data['difficulties'])
                    
                    # 确定掌握程度评级
                    mastery.mastery_level = self._determine_mastery_level(mastery.mastery_rate)
                    
                    mastery_list.append(mastery)
            
            logger.info(f"知识点掌握度分析完成: 分析了 {len(mastery_list)} 个知识点")
            
            return mastery_list
            
        except Exception as e:
            logger.error(f"知识点掌握度分析失败: {str(e)}")
            return []
    
    def _determine_mastery_level(self, mastery_rate: float) -> str:
        """确定掌握程度评级"""
        for level, config in self.MASTERY_THRESHOLDS.items():
            if mastery_rate >= config['min']:
                return config['label']
        return '严重不足'
    
    def generate_exam_analysis_report(self, exam_id: str) -> ExamAnalysisReport:
        """
        生成考试分析报告
        
        Args:
            exam_id: 考试ID
        
        Returns:
            考试分析报告
        """
        try:
            report = ExamAnalysisReport()
            report.exam_id = exam_id
            
            # 获取参与人数
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(DISTINCT user_id) FROM exam_results WHERE exam_id = ?
                ''', (exam_id,))
                report.total_participants = cursor.fetchone()[0]
            
            # 分析成绩分布
            report.score_distribution = self.analyze_score_distribution(exam_id)
            
            # 分析题目难度
            report.question_analyses = self.analyze_question_difficulty(exam_id)
            
            # 分析知识点掌握度
            report.knowledge_mastery = self.analyze_knowledge_mastery(exam_id)
            
            # 计算总体统计
            report.overall_statistics = self._calculate_overall_statistics(report)
            
            # 生成建议
            report.recommendations = self._generate_recommendations(report)
            
            # 缓存分析结果
            self._cache_analysis_result(exam_id, 'full_report', report)
            
            logger.info(f"考试分析报告生成完成: {exam_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"生成考试分析报告失败: {str(e)}")
            return ExamAnalysisReport(exam_id=exam_id)
    
    def _calculate_overall_statistics(self, report: ExamAnalysisReport) -> Dict:
        """计算总体统计信息"""
        stats = {
            'pass_rate': 0.0,
            'avg_correct_rate': 0.0,
            'question_count': len(report.question_analyses),
            'knowledge_point_count': len(report.knowledge_mastery),
            'difficulty_balance': {},
            'quality_issues': []
        }
        
        # 计算通过率
        if report.score_distribution.score_ranges:
            pass_count = sum(
                r['count'] for range_name, r in report.score_distribution.score_ranges.items()
                if range_name in ['60-69', '70-79', '80-89', '90-100']
            )
            if report.total_participants > 0:
                stats['pass_rate'] = pass_count / report.total_participants * 100
        
        # 计算平均正确率
        if report.question_analyses:
            stats['avg_correct_rate'] = sum(
                qa.correct_rate for qa in report.question_analyses
            ) / len(report.question_analyses) * 100
        
        # 分析难度平衡
        difficulty_balance = defaultdict(int)
        for qa in report.question_analyses:
            level = qa.difficulty_level
            difficulty_balance[level] += 1
        stats['difficulty_balance'] = dict(difficulty_balance)
        
        # 检查质量问题
        for qa in report.question_analyses:
            if qa.discrimination_index < 0.2:
                stats['quality_issues'].append({
                    'question_id': qa.question_id,
                    'issue': '区分度不足'
                })
            if qa.correct_rate < 0.2 or qa.correct_rate > 0.95:
                stats['quality_issues'].append({
                    'question_id': qa.question_id,
                    'issue': f'正确率异常({qa.correct_rate:.2%})'
                })
        
        return stats
    
    def _generate_recommendations(self, report: ExamAnalysisReport) -> List[str]:
        """生成教学建议"""
        recommendations = []
        
        # 根据成绩分布生成建议
        if report.score_distribution.mean < 60:
            recommendations.append("整体成绩偏低，建议加强基础知识讲解和练习")
        elif report.score_distribution.mean > 85:
            recommendations.append("整体成绩优秀，可考虑增加挑战性题目")
        
        if report.score_distribution.std_dev > 20:
            recommendations.append("成绩差异较大，建议分层教学，关注学习困难学生")
        
        # 根据题目难度生成建议
        difficult_questions = [qa for qa in report.question_analyses if qa.correct_rate < 0.4]
        if len(difficult_questions) > len(report.question_analyses) * 0.3:
            recommendations.append("较多题目难度过高，建议调整题目难度分布或加强相关知识点教学")
        
        easy_questions = [qa for qa in report.question_analyses if qa.correct_rate > 0.9]
        if len(easy_questions) > len(report.question_analyses) * 0.4:
            recommendations.append("较多题目过于简单，建议增加中等难度题目")
        
        # 根据知识点掌握度生成建议
        weak_knowledge = [km for km in report.knowledge_mastery if km.mastery_rate < 60]
        if weak_knowledge:
            weak_points = [km.knowledge_point for km in weak_knowledge]
            recommendations.append(f"以下知识点掌握度较低，需要重点讲解: {', '.join(weak_points[:5])}")
        
        # 根据质量问题生成建议
        if report.overall_statistics.get('quality_issues'):
            recommendations.append("部分题目存在质量问题（区分度不足或正确率异常），建议重新审核")
        
        return recommendations
    
    def _cache_analysis_result(self, exam_id: str, analysis_type: str, data: Any):
        """缓存分析结果"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 将数据序列化为JSON
                if isinstance(data, (ScoreDistribution, QuestionDifficultyAnalysis, 
                                     KnowledgePointMastery, ExamAnalysisReport)):
                    data_dict = self._serialize_analysis_data(data)
                else:
                    data_dict = data
                
                # 删除旧缓存
                cursor.execute('''
                    DELETE FROM exam_analysis_cache WHERE exam_id = ? AND analysis_type = ?
                ''', (exam_id, analysis_type))
                
                # 插入新缓存
                cursor.execute('''
                    INSERT INTO exam_analysis_cache 
                    (exam_id, analysis_type, analysis_data, generated_at)
                    VALUES (?, ?, ?, ?)
                ''', (exam_id, analysis_type, json.dumps(data_dict), datetime.now(timezone.utc).isoformat()))
                
                conn.commit()
        except Exception as e:
            logger.error(f"缓存分析结果失败: {str(e)}")
    
    def _serialize_analysis_data(self, data: Any) -> Dict:
        """序列化分析数据"""
        if isinstance(data, ScoreDistribution):
            return {
                'score_ranges': data.score_ranges,
                'mean': data.mean,
                'median': data.median,
                'std_dev': data.std_dev,
                'min_score': data.min_score,
                'max_score': data.max_score,
                'mode': data.mode,
                'percentile_25': data.percentile_25,
                'percentile_75': data.percentile_75
            }
        elif isinstance(data, QuestionDifficultyAnalysis):
            return {
                'question_id': data.question_id,
                'difficulty_level': data.difficulty_level,
                'correct_rate': data.correct_rate,
                'avg_time_spent': data.avg_time_spent,
                'discrimination_index': data.discrimination_index,
                'difficulty_index': data.difficulty_index,
                'analysis_result': data.analysis_result
            }
        elif isinstance(data, KnowledgePointMastery):
            return {
                'knowledge_point': data.knowledge_point,
                'total_questions': data.total_questions,
                'correct_count': data.correct_count,
                'mastery_rate': data.mastery_rate,
                'avg_time': data.avg_time,
                'difficulty_avg': data.difficulty_avg,
                'mastery_level': data.mastery_level
            }
        elif isinstance(data, ExamAnalysisReport):
            return {
                'exam_id': data.exam_id,
                'total_participants': data.total_participants,
                'score_distribution': self._serialize_analysis_data(data.score_distribution),
                'question_analyses': [self._serialize_analysis_data(qa) for qa in data.question_analyses],
                'knowledge_mastery': [self._serialize_analysis_data(km) for km in data.knowledge_mastery],
                'overall_statistics': data.overall_statistics,
                'recommendations': data.recommendations,
                'generated_at': data.generated_at.isoformat()
            }
        return {}
    
    def get_cached_analysis(self, exam_id: str, analysis_type: str) -> Optional[Dict]:
        """获取缓存的分析结果"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT analysis_data, generated_at FROM exam_analysis_cache 
                    WHERE exam_id = ? AND analysis_type = ?
                ''', (exam_id, analysis_type))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'data': json.loads(result[0]),
                        'generated_at': result[1]
                    }
                return None
        except Exception as e:
            logger.error(f"获取缓存分析失败: {str(e)}")
            return None
    
    def analyze_user_exam_history(self, user_id: str, limit: int = 20) -> Dict:
        """分析用户考试历史"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # 获取用户所有考试结果
                cursor.execute('''
                    SELECT exam_id, total_score, correct_count, total_count, 
                           accuracy, time_taken, passed, created_at
                    FROM exam_results 
                    WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (user_id, limit))
                
                exam_history = []
                for row in cursor.fetchall():
                    exam_history.append({
                        'exam_id': row[0],
                        'score': row[1],
                        'correct_count': row[2],
                        'total_count': row[3],
                        'accuracy': row[4],
                        'time_taken': row[5],
                        'passed': row[6],
                        'date': row[7]
                    })
                
                # 计算趋势分析
                trend_analysis = self._calculate_performance_trend(exam_history)
                
                # 分析知识点掌握趋势
                cursor.execute('''
                    SELECT tags, COUNT(*) as total, SUM(is_correct) as correct
                    FROM question_analysis 
                    WHERE user_id = ?
                    GROUP BY tags
                ''', (user_id,))
                
                knowledge_progress = []
                for row in cursor.fetchall():
                    tags = json.loads(row[0]) if row[0] else []
                    total = row[1]
                    correct = row[2]
                    for tag in tags:
                        if tag:
                            knowledge_progress.append({
                                'knowledge_point': tag,
                                'total': total,
                                'correct': correct,
                                'rate': correct / total * 100 if total > 0 else 0
                            })
                
                # 合并相同知识点的统计
                merged_knowledge = defaultdict(lambda: {'total': 0, 'correct': 0})
                for kp in knowledge_progress:
                    merged_knowledge[kp['knowledge_point']]['total'] += kp['total']
                    merged_knowledge[kp['knowledge_point']]['correct'] += kp['correct']
                
                knowledge_analysis = []
                for kp, data in merged_knowledge.items():
                    knowledge_analysis.append({
                        'knowledge_point': kp,
                        'total': data['total'],
                        'correct': data['correct'],
                        'mastery_rate': data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
                    })
                
                return {
                    'user_id': user_id,
                    'exam_count': len(exam_history),
                    'exam_history': exam_history,
                    'trend_analysis': trend_analysis,
                    'knowledge_progress': knowledge_analysis,
                    'avg_score': sum(e['score'] for e in exam_history) / len(exam_history) if exam_history else 0,
                    'pass_rate': sum(1 for e in exam_history if e['passed']) / len(exam_history) * 100 if exam_history else 0
                }
                
        except Exception as e:
            logger.error(f"分析用户考试历史失败: {str(e)}")
            return {'user_id': user_id, 'error': str(e)}
    
    def _calculate_performance_trend(self, exam_history: List[Dict]) -> Dict:
        """计算成绩趋势"""
        if len(exam_history) < 2:
            return {'trend': 'insufficient_data', 'description': '数据不足，无法分析趋势'}
        
        # 按时间排序（已经是倒序）
        scores = [e['score'] for e in exam_history]
        
        # 计算最近几次的趋势
        recent_scores = scores[:min(5, len(scores))]
        
        if len(recent_scores) >= 3:
            # 计算平均趋势
            avg_improvement = (recent_scores[0] - recent_scores[-1]) / len(recent_scores)
            
            if avg_improvement > 2:
                return {'trend': 'improving', 'description': '成绩呈上升趋势，进步明显'}
            elif avg_improvement < -2:
                return {'trend': 'declining', 'description': '成绩呈下降趋势，需要关注'}
            else:
                return {'trend': 'stable', 'description': '成绩保持稳定'}
        
        return {'trend': 'unknown', 'description': '趋势不明显'}
    
    def generate_comparison_report(self, exam_id: str, user_ids: List[str]) -> Dict:
        """生成用户对比报告"""
        try:
            comparison_data = []
            
            for user_id in user_ids:
                # 获取用户在该考试的表现
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT total_score, correct_count, accuracy, time_taken, passed
                        FROM exam_results 
                        WHERE exam_id = ? AND user_id = ?
                        ORDER BY created_at DESC LIMIT 1
                    ''', (exam_id, user_id))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        comparison_data.append({
                            'user_id': user_id,
                            'score': result[0],
                            'correct_count': result[1],
                            'accuracy': result[2],
                            'time_taken': result[3],
                            'passed': result[4]
                        })
            
            # 计算排名
            sorted_by_score = sorted(comparison_data, key=lambda x: x['score'], reverse=True)
            for i, data in enumerate(sorted_by_score):
                data['rank'] = i + 1
            
            # 计算统计对比
            if comparison_data:
                avg_score = sum(d['score'] for d in comparison_data) / len(comparison_data)
                avg_time = sum(d['time_taken'] for d in comparison_data) / len(comparison_data)
                pass_count = sum(1 for d in comparison_data if d['passed'])
            else:
                avg_score = 0
                avg_time = 0
                pass_count = 0
            
            return {
                'exam_id': exam_id,
                'total_users': len(user_ids),
                'comparison_data': sorted_by_score,
                'statistics': {
                    'avg_score': avg_score,
                    'avg_time': avg_time,
                    'pass_count': pass_count,
                    'pass_rate': pass_count / len(user_ids) * 100 if user_ids else 0
                }
            }
            
        except Exception as e:
            logger.error(f"生成对比报告失败: {str(e)}")
            return {'exam_id': exam_id, 'error': str(e)}


# 全局实例
_exam_data_analysis_service = None

def get_exam_data_analysis_service(db_path="app.db") -> ExamDataAnalysisService:
    """获取数据分析服务实例"""
    global _exam_data_analysis_service
    if _exam_data_analysis_service is None:
        _exam_data_analysis_service = ExamDataAnalysisService(db_path)
    return _exam_data_analysis_service


if __name__ == "__main__":
    # 测试数据分析服务
    service = get_exam_data_analysis_service()
    
    print("=" * 60)
    print("考试数据分析服务测试")
    print("=" * 60)
    
    # 测试成绩分布分析
    distribution = service.analyze_score_distribution("EXAM_001")
    print(f"\n✓ 成绩分布分析:")
    print(f"  平均分: {distribution.mean:.2f}")
    print(f"  中位数: {distribution.median:.2f}")
    print(f"  标准差: {distribution.std_dev:.2f}")
    print(f"  分数段分布: {distribution.score_ranges}")
    
    # 测试题目难度分析
    question_analyses = service.analyze_question_difficulty("EXAM_001")
    print(f"\n✓ 题目难度分析: 分析了 {len(question_analyses)} 道题目")
    
    # 测试知识点掌握度分析
    knowledge_mastery = service.analyze_knowledge_mastery("EXAM_001")
    print(f"\n✓ 知识点掌握度分析: 分析了 {len(knowledge_mastery)} 个知识点")
    
    # 测试生成完整报告
    report = service.generate_exam_analysis_report("EXAM_001")
    print(f"\n✓ 考试分析报告生成完成:")
    print(f"  参与人数: {report.total_participants}")
    print(f"  建议: {report.recommendations}")
    
    logger.info("考试数据分析服务测试完成")