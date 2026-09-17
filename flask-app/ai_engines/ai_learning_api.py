# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from app.middlewares.system_container import system_container
import json

ai_learning_bp = Blueprint('ai_learning', __name__, url_prefix='/api/ai-learning')

@ai_learning_bp.route('/status')
def status():
    """获取学习状态"""
    return jsonify({'status': 'active'})

@system_container(require_auth='login')
@ai_learning_bp.route('/run', methods=['POST', 'GET'])
def run_learning():
    """主动触发 AI 学习周期 (run_learning_cycle)"""
    try:
        from ai_engines.ai_learning_system import AILearningSystem, AILearningAgent
        from ai_engines.ai_service import ai_service_manager
        sysm = AILearningSystem(ai_service_manager=ai_service_manager)
        result = sysm.run_learning_cycle()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@system_container(require_auth='login')
@ai_learning_bp.route('/train', methods=['POST'])
@system_container(require_auth='login')
def train():
    """训练AI模型"""
    data = request.get_json() or {}
    return jsonify({'success': True, 'message': '训练开始'})
