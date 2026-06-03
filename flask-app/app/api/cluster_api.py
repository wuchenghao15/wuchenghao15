# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

cluster_api_bp = Blueprint('cluster_api', __name__)

@cluster_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'cluster': 'ready'})

@cluster_api_bp.route('/nodes')
def nodes():
    return jsonify({'nodes': []})
