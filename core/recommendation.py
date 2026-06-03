# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recommendation Engine - 智能推荐系统
基于协同过滤和内容分析的个性化推荐
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from datetime import datetime
import math

class User:
    """用户"""
    
    def __init__(self, user_id: str, profile: Dict[str, Any] = None):
        self.id = user_id
        self.profile = profile or {}
        self.history = []
        self.ratings = {}
        self.preferences = defaultdict(float)
    
    def add_rating(self, item_id: str, rating: float):
        self.ratings[item_id] = rating
        if item_id not in self.history:
            self.history.append(item_id)
    
    def get_history(self) -> List[str]:
        return self.history.copy()
    
    def update_preferences(self, item_features: Dict[str, float]):
        for feature, value in item_features.items():
            self.preferences[feature] += value


class Item:
    """物品"""
    
    def __init__(self, item_id: str, name: str, features: Dict[str, Any] = None, category: str = None):
        self.id = item_id
        self.name = name
        self.features = features or {}
        self.category = category
        self.attributes = defaultdict(float)
        self.created_at = datetime.now()
    
    def add_attribute(self, key: str, value: float):
        self.attributes[key] = value


class RatingMatrix:
    """评分矩阵"""
    
    def __init__(self):
        self.ratings: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.users: Set[str] = set()
        self.items: Set[str] = set()
    
    def add_rating(self, user_id: str, item_id: str, rating: float):
        self.ratings[user_id][item_id] = rating
        self.users.add(user_id)
        self.items.add(item_id)
    
    def get_rating(self, user_id: str, item_id: str) -> Optional[float]:
        return self.ratings.get(user_id, {}).get(item_id)
    
    def get_user_ratings(self, user_id: str) -> Dict[str, float]:
        return self.ratings.get(user_id, {}).copy()
    
    def get_item_ratings(self, item_id: str) -> Dict[str, float]:
        result = {}
        for user_id, ratings in self.ratings.items():
            if item_id in ratings:
                result[user_id] = ratings[item_id]
        return result
    
    def get_common_ratings(self, user1_id: str, user2_id: str) -> List[Tuple[float, float]]:
        ratings1 = self.ratings.get(user1_id, {})
        ratings2 = self.ratings.get(user2_id, {})
        
        common = []
        for item_id in ratings1:
            if item_id in ratings2:
                common.append((ratings1[item_id], ratings2[item_id]))
        
        return common


class RecommendationEngine:
    """推荐引擎"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.items: Dict[str, Item] = {}
        self.rating_matrix = RatingMatrix()
        self.item_similarity_cache = {}
    
    def add_user(self, user_id: str, profile: Dict[str, Any] = None) -> User:
        user = User(user_id, profile)
        self.users[user_id] = user
        return user
    
    def add_item(self, item_id: str, name: str, features: Dict[str, Any] = None, category: str = None) -> Item:
        item = Item(item_id, name, features, category)
        self.items[item_id] = item
        return item
    
    def rate_item(self, user_id: str, item_id: str, rating: float):
        if user_id not in self.users:
            self.add_user(user_id)
        if item_id not in self.items:
            self.add_item(item_id, f"Item_{item_id}")
        
        self.users[user_id].add_rating(item_id, rating)
        self.rating_matrix.add_rating(user_id, item_id, rating)
        
        item = self.items[item_id]
        if item.features:
            user_profile = {}
            for key, value in item.features.items():
                if isinstance(value, (int, float)):
                    user_profile[key] = value * rating
            self.users[user_id].update_preferences(user_profile)
    
    def calculate_user_similarity(self, user1_id: str, user2_id: str) -> float:
        """计算用户相似度（皮尔逊相关系数）"""
        common = self.rating_matrix.get_common_ratings(user1_id, user2_id)
        
        if len(common) < 2:
            return 0.0
        
        ratings1, ratings2 = zip(*common)
        
        mean1 = sum(ratings1) / len(ratings1)
        mean2 = sum(ratings2) / len(ratings2)
        
        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in common)
        
        sum1 = sum((r1 - mean1) ** 2 for r1 in ratings1)
        sum2 = sum((r2 - mean2) ** 2 for r2 in ratings2)
        
        denominator = math.sqrt(sum1 * sum2)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def calculate_item_similarity(self, item1_id: str, item2_id: str) -> float:
        """计算物品相似度（余弦相似度）"""
        cache_key = f"{item1_id}:{item2_id}"
        if cache_key in self.item_similarity_cache:
            return self.item_similarity_cache[cache_key]
        
        ratings1 = self.rating_matrix.get_item_ratings(item1_id)
        ratings2 = self.rating_matrix.get_item_ratings(item2_id)
        
        common_users = set(ratings1.keys()) & set(ratings2.keys())
        
        if not common_users:
            return 0.0
        
        vec1 = [ratings1[user_id] for user_id in common_users]
        vec2 = [ratings2[user_id] for user_id in common_users]
        
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(v ** 2 for v in vec1))
        magnitude2 = math.sqrt(sum(v ** 2 for v in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        
        self.item_similarity_cache[cache_key] = similarity
        return similarity
    
    def collaborative_filtering(self, user_id: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """基于用户的协同过滤推荐"""
        if user_id not in self.users:
            return []
        
        user_ratings = self.rating_matrix.get_user_ratings(user_id)
        rated_items = set(user_ratings.keys())
        
        similarities = []
        for other_user_id in self.users:
            if other_user_id == user_id:
                continue
            
            similarity = self.calculate_user_similarity(user_id, other_user_id)
            if similarity > 0:
                similarities.append((other_user_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for other_user_id, similarity in similarities[:20]:
            other_ratings = self.rating_matrix.get_user_ratings(other_user_id)
            
            for item_id, rating in other_ratings.items():
                if item_id not in rated_items:
                    predicted_rating = similarity * rating
                    recommendations.append((item_id, predicted_rating))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_n]
    
    def item_based_filtering(self, user_id: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """基于物品的协同过滤推荐"""
        if user_id not in self.users:
            return []
        
        user_ratings = self.rating_matrix.get_user_ratings(user_id)
        
        recommendations = []
        
        for rated_item_id, rating in user_ratings.items():
            for candidate_item_id in self.items:
                if candidate_item_id in user_ratings:
                    continue
                
                similarity = self.calculate_item_similarity(rated_item_id, candidate_item_id)
                if similarity > 0:
                    predicted_rating = similarity * rating
                    recommendations.append((candidate_item_id, predicted_rating))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_n]
    
    def content_based_filtering(self, user_id: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """基于内容的推荐"""
        if user_id not in self.users:
            return []
        
        user = self.users[user_id]
        user_preferences = user.preferences
        
        recommendations = []
        
        for item_id, item in self.items.items():
            if item_id in user.ratings:
                continue
            
            score = 0.0
            for feature, value in item.features.items():
                if isinstance(value, (int, float)) and feature in user_preferences:
                    score += value * user_preferences[feature]
            
            if item.category:
                category_key = f"category_{item.category}"
                if category_key in user_preferences:
                    score += user_preferences[category_key]
            
            recommendations.append((item_id, score))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_n]
    
    def hybrid_recommendation(self, user_id: str, top_n: int = 10, 
                              weights: Dict[str, float] = None) -> List[Tuple[str, float]]:
        """混合推荐"""
        if weights is None:
            weights = {
                "collaborative": 0.4,
                "item_based": 0.3,
                "content": 0.3
            }
        
        cf_recs = self.collaborative_filtering(user_id, top_n * 2)
        ib_recs = self.item_based_filtering(user_id, top_n * 2)
        cb_recs = self.content_based_filtering(user_id, top_n * 2)
        
        scores = defaultdict(float)
        total_weight = sum(weights.values())
        
        for item_id, score in cf_recs:
            scores[item_id] += score * weights.get("collaborative", 0) / len(cf_recs) if cf_recs else 0
        
        for item_id, score in ib_recs:
            scores[item_id] += score * weights.get("item_based", 0) / len(ib_recs) if ib_recs else 0
        
        for item_id, score in cb_recs:
            scores[item_id] += score * weights.get("content", 0) / len(cb_recs) if cb_recs else 0
        
        recommendations = [(item_id, score) for item_id, score in scores.items()]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_n]
    
    def get_popular_items(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """获取热门物品"""
        item_counts = defaultdict(int)
        
        for user_id, ratings in self.rating_matrix.ratings.items():
            for item_id in ratings:
                item_counts[item_id] += 1
        
        popular = [(item_id, count) for item_id, count in item_counts.items()]
        popular.sort(key=lambda x: x[1], reverse=True)
        
        return popular[:top_n]
    
    def get_user_recommendations_for_category(self, user_id: str, category: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """获取特定类别的推荐"""
        all_recs = self.hybrid_recommendation(user_id, top_n * 2)
        
        category_recs = []
        for item_id, score in all_recs:
            if item_id in self.items and self.items[item_id].category == category:
                category_recs.append((item_id, score))
        
        return category_recs[:top_n]
    
    def explain_recommendation(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """解释推荐原因"""
        if user_id not in self.users or item_id not in self.items:
            return {}
        
        item = self.items[item_id]
        user = self.users[user_id]
        
        reasons = []
        
        if item.category and f"category_{item.category}" in user.preferences:
            reasons.append(f"您喜欢{item.category}类别的内容")
        
        for rated_item_id in user.ratings:
            if rated_item_id in self.items:
                similarity = self.calculate_item_similarity(rated_item_id, item_id)
                if similarity > 0.5:
                    rated_item = self.items[rated_item_id]
                    reasons.append(f"与您喜欢的'{rated_item.name}'相似")
                    break
        
        return {
            "item_id": item_id,
            "item_name": item.name,
            "reasons": reasons
        }


# 全局实例
recommendation_engine = RecommendationEngine()
