# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
import json

local_storage_bp = Blueprint('local_storage', __name__)

@local_storage_bp.route('/api/storage/save', methods=['POST'])
def save_data():
    """保存数据"""
    data = request.get_json() or {}
    return jsonify({'success': True, 'message': '数据保存成功'})

@local_storage_bp.route('/api/storage/load')
def load_data():
    """加载数据"""
    return jsonify({'success': True, 'data': {}})
