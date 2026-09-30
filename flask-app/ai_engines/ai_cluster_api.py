# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
from app.middlewares.system_container import system_container
import json

ai_cluster_api_bp = Blueprint('ai_cluster_api', __name__)

@system_container(require_auth='login')
@ai_cluster_api_bp.route('/')
@system_container(require_auth='login')
def index():
    return jsonify({'status': 'ok', 'ai_cluster': 'active'})

@ai_cluster_api_bp.route('/instances')
@system_container(require_auth='login')
def instances():
    return jsonify({'instances': []})
