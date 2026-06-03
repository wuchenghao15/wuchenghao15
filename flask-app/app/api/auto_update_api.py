# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

auto_update_api_bp = Blueprint('auto_update_api', __name__)

@auto_update_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'auto_update_api_bp API is running'})

