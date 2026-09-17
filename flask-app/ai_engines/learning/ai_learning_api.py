# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from app.middlewares.system_container import system_container
import json

ai_learning_bp = Blueprint(r'ai_learning', __name__, url_prefix=r'/api/ai-learning')

@ai_learning_bp.route(r'/status')
def status():
    r"""获取学习状态r"""
    return jsonify({r'status': r'active'})

@system_container(require_auth='login')
@ai_learning_bp.route(r'/train', methods=[r'POST'])
@system_container(require_auth='login')
def train():
    r"""训练AI模型r"""
    data = request.get_json() or {}
    return jsonify({r'success': True, r'message': r'训练开始'})
