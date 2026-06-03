# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

thread_process_manager_api_bp = Blueprint('thread_process_manager_api', __name__)

@thread_process_manager_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'manager': 'running'})

@thread_process_manager_api_bp.route('/threads')
def threads():
    return jsonify({'threads': []})
