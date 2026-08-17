#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.recommendation_engine import AIRecommendationEngine
from app.ai.learning_path_planner import AILearningPathPlanner

ai_resource_api = Bluelogger.info('ai_resource_api', __name__)

@ai_resource_api.route('/api/ai/resources/recommend', methods=['GET'])
def recommend_resources():
    """根据用户画像推荐学习资源"""
    user_id = request.args.get('user_id', '1')
    limit = int(request.args.get('limit', 10))
    
    try:
        engine = AIRecommendationEngine()
        recommendations = engine.recommend_resources(user_id, limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/popular', methods=['GET'])
def get_popular_resources():
    """获取热门资源"""
    limit = int(request.args.get('limit', 10))
    
    try:
        engine = AIRecommendationEngine()
        resources = engine.get_popular_resources(limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/recent', methods=['GET'])
def get_recent_resources():
    """获取最新资源"""
    limit = int(request.args.get('limit', 10))
    
    try:
        engine = AIRecommendationEngine()
        resources = engine.get_recent_resources(limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/category', methods=['GET'])
def get_resources_by_category():
    """按类别获取资源"""
    category = request.args.get('category', '')
    limit = int(request.args.get('limit', 10))
    
    if not category:
        return jsonify({
            'success': False,
            'error': 'category参数不能为空'
        }), 400
    
    try:
        engine = AIRecommendationEngine()
        resources = engine.recommend_by_category(category, limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/beginners', methods=['GET'])
def get_beginners_resources():
    """获取初学者资源"""
    limit = int(request.args.get('limit', 10))
    
    try:
        engine = AIRecommendationEngine()
        resources = engine.recommend_for_beginners(limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/advanced', methods=['GET'])
def get_advanced_resources():
    """获取进阶资源"""
    limit = int(request.args.get('limit', 10))
    
    try:
        engine = AIRecommendationEngine()
        resources = engine.recommend_for_advanced(limit)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/learning-path/skill-gaps', methods=['GET'])
def analyze_skill_gaps():
    """分析用户技能差距"""
    user_id = request.args.get('user_id', '1')
    
    try:
        planner = AILearningPathPlanner()
        gaps = planner.analyze_skill_gaps(user_id)
        planner.close()
        
        return jsonify({
            'success': True,
            'data': gaps,
            'count': len(gaps)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/learning-path/generate', methods=['POST'])
def generate_learning_path():
    """生成个性化学习路径"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    goals = data.get('goals')
    duration_days = int(data.get('duration_days', 30))
    
    try:
        planner = AILearningPathPlanner()
        path = planner.generate_learning_path(user_id, goals, duration_days)
        planner.save_learning_path(path)
        planner.close()
        
        return jsonify({
            'success': True,
            'data': path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/learning-path/<user_id>', methods=['GET'])
def get_user_learning_path(user_id):
    """获取用户学习路径"""
    try:
        planner = AILearningPathPlanner()
        path = planner.get_user_learning_path(user_id)
        planner.close()
        
        if path:
            return jsonify({
                'success': True,
                'data': dict(path)
            })
        else:
            return jsonify({
                'success': False,
                'error': '未找到学习路径'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_resource_api.route('/api/ai/resources/stats', methods=['GET'])
def get_resource_stats():
    """获取资源统计信息"""
    try:
        engine = AIRecommendationEngine()
        stats = engine.get_resource_stats()
        engine.close()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500