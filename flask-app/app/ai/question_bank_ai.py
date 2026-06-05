#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI题库优化员工
智能优化和管理题库内容
"""

import json
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from app.utils.logging import logger


class QuestionAnalyzer:
    """题目分析器"""
    
    def __init__(self):
        self.difficulty_keywords = {
            'easy': ['基础', '简单', '入门', '初级', '认识', '了解', '什么是', '定义'],
            'medium': ['理解', '掌握', '应用', '使用', '分析', '比较', '区别'],
            'hard': ['综合', '复杂', '创新', '设计', '评估', '深度', '探究', '研究']
        }
        
        self.type_keywords = {
            'choice': ['选择', '下列', '哪个', '哪项', '正确的是', '错误的是'],
            'fill': ['填空', '填写', '补全', '横线'],
            'essay': ['论述', '说明', '解释', '谈谈', '分析', '论述'],
            'code': ['代码', '程序', '编写', '实现', '函数', '算法']
        }
    
    def analyze_difficulty(self, question_content: str) -> str:
        """分析题目难度"""
        content_lower = question_content.lower()
        scores = {'easy': 0, 'medium': 0, 'hard': 0}
        
        for keyword in self.difficulty_keywords.get('easy', []):
            if keyword in content_lower:
                scores['easy'] += 1
        
        for keyword in self.difficulty_keywords.get('medium', []):
            if keyword in content_lower:
                scores['medium'] += 1
        
        for keyword in self.difficulty_keywords.get('hard', []):
            if keyword in content_lower:
                scores['hard'] += 1
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'medium'
        
        for level, score in scores.items():
            if score == max_score:
                return level
        
        return 'medium'
    
    def analyze_type(self, question_content: str) -> str:
        """分析题目类型"""
        content_lower = question_content.lower()
        
        for qtype, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return qtype
        
        return 'choice'
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词
        stop_words = {'的', '了', '是', '在', '和', '与', '或', '等', '以及', '包括', '对于', '关于', '一个', '一种'}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_words[:max_keywords]]
    
    def assess_quality(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """评估题目质量"""
        score = 0
        suggestions = []
        
        # 检查内容长度
        content = question.get('content', '')
        if len(content) < 10:
            score -= 10
            suggestions.append('题目内容过短，建议增加详细描述')
        elif len(content) > 500:
            score -= 5
            suggestions.append('题目内容过长，建议精简')
        else:
            score += 10
        
        # 检查选项
        options = question.get('options', [])
        if question.get('question_type') == 'choice':
            if len(options) < 2:
                score -= 20
                suggestions.append('选择题至少需要2个选项')
            elif len(options) < 4:
                score -= 5
                suggestions.append('建议提供4个选项以提高题目质量')
            else:
                score += 10
        
        # 检查答案
        if not question.get('answer'):
            score -= 30
            suggestions.append('题目缺少答案')
        else:
            score += 20
        
        # 检查解析
        if not question.get('explanation'):
            score -= 5
            suggestions.append('建议添加题目解析')
        else:
            score += 5
        
        # 检查标签
        tags = question.get('tags', [])
        if len(tags) == 0:
            score -= 5
            suggestions.append('建议添加题目标签')
        elif len(tags) < 3:
            score -= 2
        else:
            score += 5
        
        # 归一化分数到0-100
        quality_score = max(0, min(100, score + 50))
        
        return {
            'quality_score': quality_score,
            'suggestions': suggestions,
            'strengths': self._get_strengths(question)
        }
    
    def _get_strengths(self, question: Dict[str, Any]) -> List[str]:
        """获取题目优点"""
        strengths = []
        
        if len(question.get('content', '')) >= 50:
            strengths.append('题目描述详细')
        
        if question.get('explanation'):
            strengths.append('包含详细解析')
        
        if len(question.get('tags', [])) >= 3:
            strengths.append('标签分类清晰')
        
        if question.get('options') and len(question.get('options', [])) >= 4:
            strengths.append('选项设置完善')
        
        return strengths


class QuestionOptimizer:
    """题目优化器"""
    
    def __init__(self):
        self.analyzer = QuestionAnalyzer()
    
    def optimize_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化题目"""
        optimized = question.copy()
        
        # 自动分析难度
        if not question.get('difficulty'):
            optimized['difficulty'] = self.analyzer.analyze_difficulty(question.get('content', ''))
        
        # 自动分析类型
        if not question.get('question_type'):
            optimized['question_type'] = self.analyzer.analyze_type(question.get('content', ''))
        
        # 提取关键词作为标签
        if not question.get('tags') and question.get('content'):
            keywords = self.analyzer.extract_keywords(question.get('content', ''))
            optimized['tags'] = keywords[:5]
        
        # 清理内容格式
        if question.get('content'):
            optimized['content'] = self._clean_content(question['content'])
        
        # 标准化选项格式
        if question.get('options'):
            optimized['options'] = self._standardize_options(question['options'])
        
        # 添加优化标记
        optimized['optimized'] = True
        optimized['optimized_at'] = datetime.now().isoformat()
        
        return optimized
    
    def _clean_content(self, content: str) -> str:
        """清理内容格式"""
        # 移除多余空格
        content = re.sub(r'\s+', ' ', content)
        # 移除多余换行
        content = re.sub(r'\n+', '\n', content)
        # 首尾去空格
        content = content.strip()
        return content
    
    def _standardize_options(self, options: List[str]) -> List[str]:
        """标准化选项格式"""
        standardized = []
        for i, option in enumerate(options):
            option = option.strip()
            # 添加字母编号
            if not re.match(r'^[A-Za-z][\.、)】\]]', option):
                option = f"{chr(65 + i)}. {option}"
            standardized.append(option)
        return standardized
    
    def batch_optimize(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量优化题目"""
        return [self.optimize_question(q) for q in questions]


class QuestionStatistics:
    """题目统计分析"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.db_path = db_path
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_question_distribution(self) -> Dict[str, Any]:
        """获取题目分布统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 统计各难度级别
            cursor.execute("""
                SELECT difficulty, COUNT(*) as count 
                FROM questions 
                GROUP BY difficulty
            """)
            difficulty_dist = {row['difficulty']: row['count'] for row in cursor.fetchall()}
            
            # 统计各类型
            cursor.execute("""
                SELECT question_type, COUNT(*) as count 
                FROM questions 
                GROUP BY question_type
            """)
            type_dist = {row['question_type']: row['count'] for row in cursor.fetchall()}
            
            # 统计各科目
            cursor.execute("""
                SELECT subject, COUNT(*) as count 
                FROM questions 
                GROUP BY subject
            """)
            subject_dist = {row['subject']: row['count'] for row in cursor.fetchall()}
            
            return {
                'difficulty_distribution': difficulty_dist,
                'type_distribution': type_dist,
                'subject_distribution': subject_dist
            }
    
    def get_quality_report(self) -> Dict[str, Any]:
        """获取质量报告"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 统计有解析的题目
            cursor.execute("SELECT COUNT(*) as count FROM questions WHERE explanation IS NOT NULL AND explanation != ''")
            with_explanation = cursor.fetchone()['count']
            
            # 统计有标签的题目
            cursor.execute("SELECT COUNT(*) as count FROM questions WHERE tags IS NOT NULL AND tags != '[]'")
            with_tags = cursor.fetchone()['count']
            
            # 统计总题数
            cursor.execute("SELECT COUNT(*) as count FROM questions")
            total = cursor.fetchone()['count']
            
            return {
                'total_questions': total,
                'with_explanation': with_explanation,
                'explanation_rate': round(with_explanation / total * 100, 2) if total > 0 else 0,
                'with_tags': with_tags,
                'tag_rate': round(with_tags / total * 100, 2) if total > 0 else 0
            }
    
    def get_optimization_potential(self) -> List[Dict[str, Any]]:
        """获取优化潜力题目"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 找出缺少解析的题目
            cursor.execute("""
                SELECT id, content, difficulty, question_type
                FROM questions
                WHERE explanation IS NULL OR explanation = ''
                LIMIT 10
            """)
            needs_explanation = [dict(row) for row in cursor.fetchall()]
            
            # 找出标签不足的题目
            cursor.execute("""
                SELECT id, content, tags
                FROM questions
                WHERE tags IS NULL OR tags = '[]' OR json_array_length(tags) < 3
                LIMIT 10
            """)
            needs_tags = [dict(row) for row in cursor.fetchall()]
            
            return {
                'needs_explanation': needs_explanation,
                'needs_tags': needs_tags
            }


class QuestionBankAIEmployee:
    """AI题库优化员工"""
    
    def __init__(self, db_path: str = None):
        self.analyzer = QuestionAnalyzer()
        self.optimizer = QuestionOptimizer()
        self.statistics = QuestionStatistics(db_path)
        self.initialized_at = datetime.now().isoformat()
        
        logger.info("AI题库优化员工初始化完成")
    
    def analyze_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个题目"""
        analysis = {
            'original_question': question,
            'analyzed_at': datetime.now().isoformat()
        }
        
        # 难度分析
        analysis['difficulty'] = self.analyzer.analyze_difficulty(question.get('content', ''))
        
        # 类型分析
        analysis['question_type'] = self.analyzer.analyze_type(question.get('content', ''))
        
        # 关键词提取
        analysis['keywords'] = self.analyzer.extract_keywords(question.get('content', ''))
        
        # 质量评估
        analysis['quality'] = self.analyzer.assess_quality(question)
        
        return analysis
    
    def optimize_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """优化单个题目"""
        return self.optimizer.optimize_question(question)
    
    def batch_optimize_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量优化题目"""
        return self.optimizer.batch_optimize(questions)
    
    def generate_suggestions(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """生成优化建议"""
        analysis = self.analyze_question(question)
        quality = analysis['quality']
        
        suggestions = {
            'question_id': question.get('id'),
            'current_quality_score': quality['quality_score'],
            'suggestions': quality['suggestions'],
            'strengths': quality['strengths'],
            'recommended_actions': []
        }
        
        # 根据分析生成建议
        if quality['quality_score'] < 60:
            suggestions['recommended_actions'].append({
                'priority': 'high',
                'action': '添加详细解析',
                'reason': '题目缺少解析，影响学习效果'
            })
        
        if len(question.get('tags', [])) < 3:
            suggestions['recommended_actions'].append({
                'priority': 'medium',
                'action': '完善标签分类',
                'reason': f'当前标签数量: {len(question.get("tags", []))}, 建议至少3个'
            })
        
        if not question.get('options') and analysis['question_type'] == 'choice':
            suggestions['recommended_actions'].append({
                'priority': 'high',
                'action': '添加选项',
                'reason': '选择题需要提供选项'
            })
        
        return suggestions
    
    def get_statistics_report(self) -> Dict[str, Any]:
        """获取统计报告"""
        return {
            'distribution': self.statistics.get_question_distribution(),
            'quality': self.statistics.get_quality_report(),
            'optimization_potential': self.statistics.get_optimization_potential()
        }
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        report = self.get_statistics_report()
        
        quality = report['quality']
        potential = report['optimization_potential']
        
        return {
            'total_questions': quality['total_questions'],
            'average_quality_score': quality['quality']['average_score'] if 'average_score' in quality['quality'] else 0,
            'needs_optimization': len(potential['needs_explanation']) + len(potential['needs_tags']),
            'explanation_rate': quality['explanation_rate'],
            'tag_rate': quality['tag_rate'],
            'recommendations': self._generate_recommendations(report)
        }
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        quality = report['quality']
        if quality['explanation_rate'] < 50:
            recommendations.append(f"题库解析覆盖率仅 {quality['explanation_rate']}%，建议批量添加解析")
        
        if quality['tag_rate'] < 30:
            recommendations.append(f"题库标签覆盖率仅 {quality['tag_rate']}%，建议完善标签体系")
        
        dist = report['distribution']
        if 'difficulty_distribution' in dist:
            diffs = dist['difficulty_distribution']
            if diffs.get('hard', 0) < diffs.get('easy', 0) * 0.3:
                recommendations.append("高难度题目偏少，建议增加难题比例")
        
        return recommendations
    
    def process_question_batch(self, questions: List[Dict[str, Any]], 
                              optimize: bool = True) -> Dict[str, Any]:
        """批量处理题目"""
        results = {
            'total': len(questions),
            'analyzed': 0,
            'optimized': 0,
            'quality_scores': [],
            'suggestions': []
        }
        
        for question in questions:
            # 分析
            analysis = self.analyze_question(question)
            results['analyzed'] += 1
            results['quality_scores'].append(analysis['quality']['quality_score'])
            
            # 优化
            if optimize:
                optimized = self.optimize_question(question)
                results['optimized'] += 1
                
                # 生成建议
                suggestion = self.generate_suggestions(optimized)
                results['suggestions'].append(suggestion)
        
        # 计算平均质量分数
        if results['quality_scores']:
            results['average_quality_score'] = round(
                sum(results['quality_scores']) / len(results['quality_scores']), 2
            )
        
        return results


# 创建全局实例
question_bank_ai = QuestionBankAIEmployee()
