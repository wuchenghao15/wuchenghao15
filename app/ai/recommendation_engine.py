#!/usr/bin/env python3
import sqlite3
import json
import os
import re
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class AIRecommendationEngine:
    """AI资源推荐引擎 - 根据用户画像和学习历史智能推荐学习资源"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def get_user_profile(self, user_id):
        """获取用户画像"""
        self.cursor.execute('''
            SELECT * FROM dwd_user_profile WHERE user_id = ?
        ''', (user_id,))
        profile = self.cursor.fetchone()
        if profile:
            return dict(profile)
        
        self.cursor.execute('''
            SELECT * FROM users WHERE id = ?
        ''', (user_id,))
        user = self.cursor.fetchone()
        if user:
            return {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'education_level': user['education_level'],
                'grade': user['grade'],
            }
        
        return None
    
    def get_user_learning_history(self, user_id, limit=50):
        """获取用户学习历史"""
        self.cursor.execute('''
            SELECT * FROM dwd_learning_behavior 
            WHERE user_id = ? 
            ORDER BY learned_date DESC LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def extract_keywords_from_history(self, learning_history):
        """从学习历史中提取关键词"""
        keywords = defaultdict(int)
        
        for record in learning_history:
            content = record.get('learning_content', '') + ' ' + record.get('learning_type', '')
            words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]+', content)
            
            for word in words:
                if len(word) >= 2:
                    keywords[word.lower()] += 1
        
        return sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]
    
    def recommend_resources(self, user_id, top_n=10):
        """根据用户画像推荐资源"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return self.get_popular_resources(top_n)
        
        learning_history = self.get_user_learning_history(user_id)
        keywords = self.extract_keywords_from_history(learning_history)
        
        recommended = []
        
        if keywords:
            keyword_list = [kw[0] for kw in keywords[:10]]
            
            for keyword in keyword_list:
                self.cursor.execute('''
                    SELECT * FROM collected_resources 
                    WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                    AND processed = 0
                    ORDER BY quality_score DESC LIMIT ?
                ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', top_n))
                
                for row in self.cursor.fetchall():
                    resource = dict(row)
                    if resource['url'] not in [r['url'] for r in recommended]:
                        resource['match_keyword'] = keyword
                        recommended.append(resource)
                
                if len(recommended) >= top_n:
                    break
        
        if len(recommended) < top_n:
            popular = self.get_popular_resources(top_n - len(recommended))
            for resource in popular:
                if resource['url'] not in [r['url'] for r in recommended]:
                    recommended.append(resource)
        
        return sorted(recommended[:top_n], key=lambda x: x['quality_score'], reverse=True)
    
    def get_popular_resources(self, limit=10):
        """获取热门资源"""
        self.cursor.execute('''
            SELECT * FROM collected_resources 
            ORDER BY quality_score DESC, view_count DESC, like_count DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_recent_resources(self, limit=10):
        """获取最新资源"""
        self.cursor.execute('''
            SELECT * FROM collected_resources 
            ORDER BY crawled_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def recommend_by_category(self, category, limit=10):
        """按类别推荐资源"""
        self.cursor.execute('''
            SELECT * FROM collected_resources 
            WHERE category = ? OR tags LIKE ?
            ORDER BY quality_score DESC 
            LIMIT ?
        ''', (category, f'%{category}%', limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def recommend_for_beginners(self, limit=10):
        """为初学者推荐资源"""
        self.cursor.execute('''
            SELECT * FROM collected_resources 
            WHERE (difficulty = 'beginner' OR difficulty = '入门' OR 
                   title LIKE '%入门%' OR title LIKE '%基础%' OR title LIKE '%零基础%')
            ORDER BY quality_score DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def recommend_for_advanced(self, limit=10):
        """为进阶学习者推荐资源"""
        self.cursor.execute('''
            SELECT * FROM collected_resources 
            WHERE (difficulty = 'advanced' OR difficulty = '进阶' OR difficulty = '高级' OR
                   title LIKE '%进阶%' OR title LIKE '%高级%' OR title LIKE '%实战%')
            ORDER BY quality_score DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def update_resource_processed(self, resource_id, result):
        """更新资源处理状态"""
        self.cursor.execute('''
            UPDATE collected_resources 
            SET processed = 1, process_result = ? 
            WHERE id = ?
        ''', (result, resource_id))
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    engine = AIRecommendationEngine()
    
    logger.info("=== 热门资源推荐 ===")
    popular = engine.get_popular_resources(5)
    for i, res in enumerate(popular, 1):
        logger.info(f"{i}. [{res['source']}] {res['title']}")
        logger.info(f"   质量分: {res['quality_score']}, URL: {res['url'][:60]}")
    
    logger.info("\n=== 最新资源推荐 ===")
    recent = engine.get_recent_resources(5)
    for i, res in enumerate(recent, 1):
        logger.info(f"{i}. [{res['source']}] {res['title']}")
        logger.info(f"   采集时间: {res['crawled_at'][:19]}")
    
    logger.info("\n=== 为用户推荐资源 ===")
    recommendations = engine.recommend_resources(1, 5)
    for i, res in enumerate(recommendations, 1):
        match_kw = res.get('match_keyword', '')
        logger.info(f"{i}. [{res['source']}] {res['title']}")
        logger.info(f"   质量分: {res['quality_score']}, 匹配关键词: {match_kw}")
    
    engine.close()