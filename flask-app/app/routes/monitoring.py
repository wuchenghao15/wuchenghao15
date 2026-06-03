# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template
import json

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/')
def index():
    return render_template('monitoring.html')

@monitoring_bp.route('/status')
def status():
    return jsonify({'status': 'ok', 'message': 'Monitoring is active'})

@monitoring_bp.route('/logs')
def logs():
    return jsonify({'logs': []})
