#!/usr/bin/env python3
import sqlite3
import json
import os
import re
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AIIntelligentQNA:
    """AI智能问答系统 - 基于知识库的智能问答"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def query_knowledge(self, question, top_n=3):
        """查询知识库"""
        keywords = self._extract_keywords(question)
        if not keywords:
            return []
        
        results = []
        for keyword in keywords:
            self.cursor.execute('''
                SELECT knowledge_title, knowledge_content, relevance_score, tags
                FROM ai_knowledge 
                WHERE (knowledge_title LIKE ? OR knowledge_content LIKE ? OR tags LIKE ?)
                ORDER BY relevance_score DESC LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', top_n))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['match_score'] = self._calculate_match_score(question,
                item['knowledge_title'] + ' ' + item['knowledge_content'])
                results.append(item)
        
        results = sorted(results, key=lambda x: x['match_score'] * x.get('relevance_score', 0.5), reverse=True)[:top_n]
        return results
    
    def get_collected_resources(self, question, top_n=3):
        """查询采集的资源"""
        keywords = self._extract_keywords(question)
        if not keywords:
            return []
        
        results = []
        for keyword in keywords:
            self.cursor.execute('''
                SELECT title, description, url, source, quality_score, tags
                FROM collected_resources 
                WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                ORDER BY quality_score DESC LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', top_n))
            
            for row in self.cursor.fetchall():
                item = dict(row)
                item['match_score'] = self._calculate_match_score(question, item['title'] + ' ' + item['description'])
                results.append(item)
        
        results = sorted(results, key=lambda x: x['match_score'] * x.get('quality_score', 0.5), reverse=True)[:top_n]
        return results
    
    def answer_question(self, question):
        """回答问题"""
        knowledge_results = self.query_knowledge(question, 3)
        resource_results = self.get_collected_resources(question, 3)
        
        answer = {
            'question': question,
            'answered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'knowledge_sources': knowledge_results,
            'resource_sources': resource_results,
            'answer_summary': self._generate_summary(question, knowledge_results, resource_results),
            'confidence': self._calculate_confidence(knowledge_results, resource_results)
        }
        
        return answer
    
    def _extract_keywords(self, query):
        """提取关键词"""
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]+', query)
        return [word for word in words if len(word) >= 2]
    
    def _calculate_match_score(self, query, content):
        """计算匹配分数"""
        keywords = self._extract_keywords(query)
        if not keywords:
            return 0
        
        match_count = sum(1 for kw in keywords if kw.lower() in content.lower())
        return match_count / len(keywords)
    
    def _generate_summary(self, question, knowledge_results, resource_results):
        """生成回答摘要"""
        if knowledge_results:
            best_knowledge = knowledge_results[0]
            content = best_knowledge['knowledge_content']
            if len(content) > 200:
                content = content[:200] + '...'
            return f"根据知识库: {content}"
        
        if resource_results:
            best_resource = resource_results[0]
            return f"建议参考资源: {best_resource['title']} - {best_resource['url']}"
        
        return "暂无相关知识，请尝试其他关键词"
    
    def _calculate_confidence(self, knowledge_results, resource_results):
        """计算置信度"""
        confidence = 0.3
        
        if knowledge_results:
            confidence += sum(r.get('relevance_score', 0.5) * r.get('match_score',
            0) for r in knowledge_results) / len(knowledge_results) * 0.4
        
        if resource_results:
            confidence += sum(r.get('quality_score', 0.5) * r.get('match_score',
            0) for r in resource_results) / len(resource_results) * 0.3
        
        return min(round(confidence, 2), 0.95)
    
    def save_question_answer(self, question, answer):
        """保存问答记录"""
        import uuid
        knowledge_id = str(uuid.uuid4())[:8] + '_' + datetime.now().strftime('%H%M%S')
        
        self.cursor.execute('''
            INSERT INTO ai_knowledge 
            (knowledge_id, knowledge_category, knowledge_title, knowledge_content, 
             knowledge_source, relevance_score, confidence_level, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            knowledge_id,
            'qna',
            f"问答: {question[:50]}",
            json.dumps({'question': question, 'answer': answer}),
            'AI问答',
            answer.get('confidence', 0.5),
            'medium',
            '问答记录'
        ))
        
        self.conn.commit()
    
    def get_frequent_questions(self, limit=10):
        """获取常见问题"""
        self.cursor.execute('''
            SELECT knowledge_title, COUNT(*) as count 
            FROM ai_knowledge 
            WHERE knowledge_category = 'qna'
            GROUP BY knowledge_title 
            ORDER BY count DESC LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    qna = AIIntelligentQNA()
    
    logger.info("=== AI智能问答系统 ===")
    
    questions = [
        "Python机器学习入门",
        "深度学习算法有哪些",
        "如何学习数据科学"
    ]
    
    for question in questions:
        logger.info(f"\n问题: {question}")
        answer = qna.answer_question(question)
        logger.info(f"置信度: {answer['confidence']}")
        logger.info(f"回答摘要: {answer['answer_summary']}")
        
        if answer['knowledge_sources']:
            logger.info("知识库来源:")
            for i, source in enumerate(answer['knowledge_sources'], 1):
                logger.info(f"  {i}. {source['knowledge_title'][:30]}")
        
        if answer['resource_sources']:
            logger.info("资源来源:")
            for i, source in enumerate(answer['resource_sources'], 1):
                logger.info(f"  {i}. [{source['source']}] {source['title'][:30]}")
        
        qna.save_question_answer(question, answer)
    
    logger.info("\n=== 常见问题 ===")
    frequent = qna.get_frequent_questions(5)
    for i, item in enumerate(frequent, 1):
        logger.info(f"{i}. {item['knowledge_title']}")
    
    qna.close()