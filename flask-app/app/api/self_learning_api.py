# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

self_learning_api = Blueprint('self_learning_api', __name__)

@self_learning_api.route('/')
def index():
    return jsonify({'status': 'ok', 'learning': 'active'})

@self_learning_api.route('/progress')
def progress():
    return jsonify({'progress': 0})
