# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
from app.models.learning_system import LearningSystem
import json
import sys

learning_system_api = Blueprint('learning_system_api', __name__, url_prefix='/api/learning')

@learning_system_api.route('/')
def index():
    return jsonify({'status': 'ok', 'system': 'learning'})

@learning_system_api.route('/courses')
def courses():
    return jsonify({'courses': []})

@learning_system_api.route('/progress/<user_id>')
def progress(user_id):
    return jsonify({'progress': {}})
