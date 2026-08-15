# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

ai_cluster_api_bp = Blueprint(r'ai_cluster_api', __name__)

@ai_cluster_api_bp.route(r'/')
def index():
    return jsonify({r'status': r'ok', r'ai_cluster': r'active'})

@ai_cluster_api_bp.route(r'/instances')
def instances():
    return jsonify({r'instances': []})
