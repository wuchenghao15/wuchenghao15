# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

firewall_api_bp = Blueprint('firewall_api', __name__)

@firewall_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'firewall_api_bp API is running'})

