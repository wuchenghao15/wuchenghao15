# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

ai_cluster_api_bp = Blueprint('ai_cluster_api', __name__)

@ai_cluster_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'ai_cluster': 'active'})

@ai_cluster_api_bp.route('/instances')
def instances():
    return jsonify({'instances': []})
