# MTSCOS AI Project - AI学习API
"""
AI学习和升级的API接口
"""

from flask import Blueprint, request, jsonify
from app.services.ai_learning import ai_learning_system
from app.utils.logging import logger

# 创建AI学习API蓝图
ai_learning_bp = Blueprint('ai_learning', __name__, url_prefix='/api/ai-learning')


@ai_learning_bp.route('/learn', methods=['POST'])
def learn_from_experience():
    """
    从经验中学习
    
    Request Body:
    {
        "task": "任务描述",
        "result": "任务结果",
        "feedback": 1,  # 1表示正面反馈，-1表示负面反馈
        "context": {}
    }
    
    Response:
    {
        "success": true,
        "message": "学习成功",
        "data": {
            "knowledge_count": 100
        }
    }
    """
    try:
        data = request.get_json()
        result = ai_learning_system.learn_from_experience(data)
        
        if result:
            status = ai_learning_system.get_learning_status()
            return jsonify({
                'success': True,
                'message': '学习成功',
                'data': {
                    'knowledge_count': status['knowledge_count']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '学习失败'
            }), 400
    except Exception as e:
        logger.error(f"学习API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/upgrade', methods=['POST'])
def self_upgrade():
    """
    执行AI自我升级
    
    Response:
    {
        "success": true,
        "message": "升级成功",
        "data": {
            "current_version": "1.0.0.100"
        }
    }
    """
    try:
        result = ai_learning_system.self_upgrade()
        
        if result:
            status = ai_learning_system.get_learning_status()
            return jsonify({
                'success': True,
                'message': '升级成功',
                'data': {
                    'current_version': status['current_version']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '升级失败'
            }), 400
    except Exception as e:
        logger.error(f"升级API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/status', methods=['GET'])
def get_learning_status():
    """
    获取学习状态
    
    Response:
    {
        "success": true,
        "message": "状态获取成功",
        "data": {
            "last_learning_time": 1234567890,
            "knowledge_count": 100,
            "current_version": "1.0.0.100"
        }
    }
    """
    try:
        status = ai_learning_system.get_learning_status()
        
        return jsonify({
            'success': True,
            'message': '状态获取成功',
            'data': status
        }), 200
    except Exception as e:
        logger.error(f"获取状态API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/knowledge/summary', methods=['GET'])
def get_knowledge_summary():
    """
    获取知识库摘要
    
    Response:
    {
        "success": true,
        "message": "摘要获取成功",
        "data": {
            "total_knowledge": 100,
            "knowledge_by_type": {
                "general": 50,
                "file_management": 30
            },
            "avg_confidence": 0.8
        }
    }
    """
    try:
        summary = ai_learning_system.get_knowledge_summary()
        
        return jsonify({
            'success': True,
            'message': '摘要获取成功',
            'data': summary
        }), 200
    except Exception as e:
        logger.error(f"获取知识库摘要API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/adapt', methods=['POST'])
def adapt_to_project():
    """
    适配到特定项目
    
    Request Body:
    {
        "type": "web_application",
        "goals": ["performance", "scalability"],
        "constraints": ["time", "budget"]
    }
    
    Response:
    {
        "success": true,
        "message": "适配成功"
    }
    """
    try:
        data = request.get_json()
        result = ai_learning_system.adapt_to_project(data)
        
        if result:
            return jsonify({
                'success': True,
                'message': '适配成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '适配失败'
            }), 400
    except Exception as e:
        logger.error(f"项目适配API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/associations', methods=['POST'])
def generate_associations():
    """
    生成功能联想
    
    Request Body:
    {
        "current_features": ["file_management", "rule_management"]
    }
    
    Response:
    {
        "success": true,
        "message": "联想生成成功",
        "data": {
            "associations": [
                {
                    "feature": "ai_learning",
                    "score": 2,
                    "reason": "与file_management共享关键词: files..."
                }
            ]
        }
    }
    """
    try:
        data = request.get_json()
        current_features = data.get('current_features', [])
        associations = ai_learning_system.generate_feature_associations(current_features)
        
        return jsonify({
            'success': True,
            'message': '联想生成成功',
            'data': {
                'associations': associations
            }
        }), 200
    except Exception as e:
        logger.error(f"功能联想API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/expand', methods=['POST'])
def auto_expand():
    """
    自动拓展能力
    
    Request Body:
    {
        "current_capabilities": ["file_management", "ai_learning"]
    }
    
    Response:
    {
        "success": true,
        "message": "能力拓展成功",
        "data": {
            "expansions": [
                {
                    "capability": "advanced_search",
                    "description": "高级文件搜索",
                    "complexity": "medium"
                }
            ]
        }
    }
    """
    try:
        data = request.get_json()
        current_capabilities = data.get('current_capabilities', [])
        expansions = ai_learning_system.auto_expand_capabilities(current_capabilities)
        
        return jsonify({
            'success': True,
            'message': '能力拓展成功',
            'data': {
                'expansions': expansions
            }
        }), 200
    except Exception as e:
        logger.error(f"能力拓展API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/upgrade-history', methods=['GET'])
def get_upgrade_history():
    """
    获取升级历史
    
    Response:
    {
        "success": true,
        "message": "获取升级历史成功",
        "data": {
            "upgrades": [
                {
                    "version": "1.0.0.100",
                    "result": true,
                    "completed_at": 1234567890
                }
            ]
        }
    }
    """
    try:
        # 这里可以实现获取升级历史的逻辑
        return jsonify({
            'success': True,
            'message': '获取升级历史成功',
            'data': {
                'upgrades': []
            }
        }), 200
    except Exception as e:
        logger.error(f"获取升级历史API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/knowledge/<knowledge_id>', methods=['GET'])
def get_knowledge(knowledge_id):
    """
    获取特定知识
    
    Response:
    {
        "success": true,
        "message": "获取知识成功",
        "data": {
            "knowledge": {}
        }
    }
    """
    try:
        # 这里可以实现获取特定知识的逻辑
        return jsonify({
            'success': True,
            'message': '获取知识成功',
            'data': {
                'knowledge': {}
            }
        }), 200
    except Exception as e:
        logger.error(f"获取知识API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_learning_bp.route('/knowledge', methods=['DELETE'])
def clear_knowledge():
    """
    清空知识库
    
    Response:
    {
        "success": true,
        "message": "清空知识库成功"
    }
    """
    try:
        # 这里可以实现清空知识库的逻辑
        return jsonify({
            'success': True,
            'message': '清空知识库成功'
        }), 200
    except Exception as e:
        logger.error(f"清空知识库API失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500