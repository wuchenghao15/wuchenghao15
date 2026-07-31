#!/usr/bin/env python3
import sqlite3
import json
import os
import re
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AIIntelligentSearch:
    """AI智能搜索引擎 - 多维度搜索学习资源和知识"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def search(self, query, sources=None, limit=20):
        """综合搜索"""
        results = []
        
        if sources is None:
            sources = ['resources', 'knowledge', 'learning', 'exam']
        
        if 'resources' in sources:
            results.extend(self._search_resources(query, limit))
        
        if 'knowledge' in sources:
            results.extend(self._search_knowledge(query, limit))
        
        if 'learning' in sources:
            results.extend(self._search_learning_records(query, limit))
        
        if 'exam' in sources:
            results.extend(self._search_exam_papers(query, limit))
        
        results = sorted(results, key=lambda x: x.get('score', 0) * x.get('match_score', 1), reverse=True)[:limit]
        
        return results
    
    def _search_resources(self, query, limit=10):
        """搜索采集的资源"""
        results = []
        
        keywords = self._extract_keywords(query)
        
        for keyword in keywords:
            self.cursor.execute('''
                SELECT *, quality_score as score 
                FROM collected_resources 
                WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                ORDER BY quality_score DESC LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['source_type'] = 'resource'
                item['match_score'] = self._calculate_match_score(query, item['title'] + ' ' + item['description'])
                results.append(item)
        
        return results
    
    def _search_knowledge(self, query, limit=10):
        """搜索知识库"""
        results = []
        
        keywords = self._extract_keywords(query)
        
        for keyword in keywords:
            self.cursor.execute('''
                SELECT *, relevance_score as score 
                FROM ai_knowledge 
                WHERE (knowledge_title LIKE ? OR knowledge_content LIKE ? OR tags LIKE ?)
                ORDER BY relevance_score DESC LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['source_type'] = 'knowledge'
                item['match_score'] = self._calculate_match_score(query, item['knowledge_title'])
                results.append(item)
        
        return results
    
    def _search_learning_records(self, query, limit=10):
        """搜索学习记录"""
        results = []
        
        keywords = self._extract_keywords(query)
        
        for keyword in keywords:
            self.cursor.execute('''
                SELECT *, confidence_score as score 
                FROM learning_records 
                WHERE learning_content LIKE ?
                ORDER BY confidence_score DESC, learned_at DESC LIMIT ?
            ''', (f'%{keyword}%', limit))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['source_type'] = 'learning'
                item['match_score'] = self._calculate_match_score(query, item['learning_content'])
                results.append(item)
        
        return results
    
    def _search_exam_papers(self, query, limit=10):
        """搜索试卷"""
        results = []
        
        try:
            self.cursor.execute('''
                SELECT *, 1.0 as score 
                FROM exam_papers 
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['source_type'] = 'exam'
                item['match_score'] = 0.5
                item['title'] = f"试卷 {item.get('exam_id', item.get('id', ''))}"
                results.append(item)
        except Exception:
            pass
        
        return results
    
    def _extract_keywords(self, query):
        """提取搜索关键词"""
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]+', query)
        return [word for word in words if len(word) >= 2]
    
    def _calculate_match_score(self, query, content):
        """计算匹配分数"""
        keywords = self._extract_keywords(query)
        if not keywords:
            return 0
        
        match_count = sum(1 for kw in keywords if kw.lower() in content.lower())
        return match_count / len(keywords)
    
    def advanced_search(self, query, filters=None, sort_by='score', limit=20):
        """高级搜索"""
        results = self.search(query, limit=limit)
        
        if filters:
            if 'source_type' in filters:
                results = [r for r in results if r.get('source_type') == filters['source_type']]
            
            if 'difficulty' in filters:
                results = [r for r in results if r.get('difficulty') == filters['difficulty']]
            
            if 'language' in filters:
                results = [r for r in results if r.get('language') == filters['language']]
        
        if sort_by == 'date':
            results = sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'score':
            results = sorted(results, key=lambda x: x.get('score', 0) * x.get('match_score', 0), reverse=True)
        
        return results[:limit]
    
    def search_suggestions(self, query, limit=5):
        """搜索建议"""
        suggestions = []
        
        self.cursor.execute('''
            SELECT DISTINCT title FROM collected_resources 
            WHERE title LIKE ? LIMIT ?
        ''', (f'{query}%', limit))
        
        for row in self.cursor.fetchall():
            suggestions.append(row['title'])
        
        self.cursor.execute('''
            SELECT DISTINCT knowledge_title FROM ai_knowledge 
            WHERE knowledge_title LIKE ? LIMIT ?
        ''', (f'{query}%', limit))
        
        for row in self.cursor.fetchall():
            if row['knowledge_title'] not in suggestions:
                suggestions.append(row['knowledge_title'])
        
        return suggestions[:limit]
    
    def get_search_stats(self):
        """获取搜索统计"""
        stats = {
            'total_resources': 0,
            'total_knowledge': 0,
            'total_learning_records': 0,
            'total_exam_papers': 0
        }
        
        self.cursor.execute('SELECT COUNT(*) FROM collected_resources')
        stats['total_resources'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM ai_knowledge')
        stats['total_knowledge'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM learning_records')
        stats['total_learning_records'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM exam_papers')
        stats['total_exam_papers'] = self.cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    searcher = AIIntelligentSearch()
    
    logger.info("=== AI智能搜索引擎 ===")
    
    query = "Python机器学习"
    logger.info(f"\n搜索: {query}")
    
    results = searcher.search(query, limit=5)
    logger.info(f"\n找到 {len(results)} 条结果:")
    for i, result in enumerate(results, 1):
        source_type = result['source_type']
        score = result.get('score', 0)
        title = result.get('title', result.get('knowledge_title', ''))[:40]
        logger.info(f"{i}. [{source_type}] {title} - 分数: {score:.2f}")
    
    logger.info("\n=== 搜索建议 ===")
    suggestions = searcher.search_suggestions("Python")
    for i, suggestion in enumerate(suggestions, 1):
        logger.info(f"{i}. {suggestion}")
    
    logger.info("\n=== 搜索统计 ===")
    stats = searcher.get_search_stats()
    logger.info(f"资源总数: {stats['total_resources']}")
    logger.info(f"知识条目: {stats['total_knowledge']}")
    logger.info(f"学习记录: {stats['total_learning_records']}")
    logger.info(f"试卷数量: {stats['total_exam_papers']}")
    
    searcher.close()