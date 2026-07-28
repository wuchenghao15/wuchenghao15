# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
import json

ai_learning_bp = Blueprint('ai_learning', __name__, url_prefix='/api/ai-learning')

@ai_learning_bp.route('/status')
def status():
    """获取学习状态"""
    return jsonify({'status': 'active'})

@ai_learning_bp.route('/train', methods=['POST'])
def train():
    """训练AI模型"""
    data = request.get_json() or {}
    return jsonify({'success': True, 'message': '训练开始'})
