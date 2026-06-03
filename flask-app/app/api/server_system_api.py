# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json
import sys

server_system_bp = Blueprint('server_system', __name__)

@server_system_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'system': 'server'})

@server_system_bp.route('/status')
def status():
    return jsonify({'status': 'running'})
