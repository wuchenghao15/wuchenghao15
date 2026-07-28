#!/usr/bin/env python3
"""AI智能推荐Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIRecommendationAgent(AIEmployee):
    """AI推荐Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI推荐专家"):
        super().__init__(employee_id, name, 'recommendation', 7)
        self.skills = [
            '个性化推荐', '协同过滤', '内容推荐',
            '混合推荐', '实时推荐', '离线推荐',
            '推荐评估', '冷启动', '推荐解释'
        ]
        self.user_profiles = {}
        self.item_profiles = {}
        self.recommendation_history = []
        self.total_recommendations = 0
    
    def create_user_profile(self, user_id: str, preferences: Dict = None) -> Dict[str, Any]:
        """创建用户画像"""
        self.user_profiles[user_id] = {
            'user_id': user_id,
            'preferences': preferences or {},
            'history': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return self.user_profiles[user_id]
    
    def update_user_profile(self, user_id: str, updates: Dict) -> Dict[str, Any]:
        """更新用户画像"""
        if user_id not in self.user_profiles:
            return {'error': '用户不存在'}
        
        profile = self.user_profiles[user_id]
        profile.update(updates)
        profile['updated_at'] = datetime.now().isoformat()
        
        return profile
    
    def add_item_profile(self, item_id: str, attributes: Dict) -> Dict[str, Any]:
        """添加物品画像"""
        self.item_profiles[item_id] = {
            'item_id': item_id,
            'attributes': attributes,
            'created_at': datetime.now().isoformat()
        }
        
        return self.item_profiles[item_id]
    
    def recommend(self, user_id: str, top_n: int = 5) -> Dict[str, Any]:
        """生成推荐"""
        if user_id not in self.user_profiles:
            return {'error': '用户不存在'}
        
        profile = self.user_profiles[user_id]
        preferences = profile.get('preferences', {})
        
        recommendations = []
        items = list(self.item_profiles.values())
        
        for item in items[:top_n]:
            score = 0
            attributes = item.get('attributes', {})
            
            for key, value in preferences.items():
                if key in attributes and attributes[key] == value:
                    score += 0.3
                elif key in attributes:
                    score += 0.1
            
            recommendations.append({
                'item_id': item['item_id'],
                'score': round(score, 2),
                'attributes': attributes
            })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        self.total_recommendations += 1
        
        result = {
            'user_id': user_id,
            'recommendations': recommendations,
            'total_items': len(items),
            'timestamp': datetime.now().isoformat()
        }
        
        self.recommendation_history.append(result)
        
        return result
    
    def collaborative_filtering(self, user_id: str, similar_users: List[str], top_n: int = 5) -> Dict[str, Any]:
        """协同过滤推荐"""
        recommendations = []
        
        for sim_user in similar_users[:3]:
            if sim_user in self.user_profiles:
                history = self.user_profiles[sim_user].get('history', [])
                for item in history[:top_n]:
                    recommendations.append({
                        'item_id': item,
                        'source': sim_user,
                        'score': 0.7
                    })
        
        return {
            'user_id': user_id,
            'similar_users': similar_users,
            'recommendations': recommendations[:top_n],
            'timestamp': datetime.now().isoformat()
        }
    
    def content_based(self, item_id: str, top_n: int = 5) -> Dict[str, Any]:
        """基于内容推荐"""
        if item_id not in self.item_profiles:
            return {'error': '物品不存在'}
        
        target_item = self.item_profiles[item_id]
        target_attrs = target_item.get('attributes', {})
        
        recommendations = []
        for item_id, item in self.item_profiles.items():
            if item_id == target_item['item_id']:
                continue
            
            attrs = item.get('attributes', {})
            score = 0
            
            for key in target_attrs:
                if key in attrs and target_attrs[key] == attrs[key]:
                    score += 0.2
            
            if score > 0:
                recommendations.append({
                    'item_id': item_id,
                    'score': round(score, 2),
                    'attributes': attrs
                })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'item_id': item_id,
            'recommendations': recommendations[:top_n],
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_recommendations(self, recommendations: List[Dict], actual_clicks: List[str]) -> Dict[str, Any]:
        """评估推荐效果"""
        recommended_ids = [r['item_id'] for r in recommendations]
        
        hits = len(set(recommended_ids) & set(actual_clicks))
        precision = hits / max(1, len(recommended_ids))
        recall = hits / max(1, len(actual_clicks))
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        
        return {
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'f1': round(f1, 2),
            'hits': hits,
            'total_recommended': len(recommended_ids),
            'total_clicked': len(actual_clicks),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_recommendations': self.total_recommendations,
            'total_users': len(self.user_profiles),
            'total_items': len(self.item_profiles),
            'recent_recommendations': self.recommendation_history[-5:]
        }

recommendation_agent = AIRecommendationAgent('ai_recommendation_001')
