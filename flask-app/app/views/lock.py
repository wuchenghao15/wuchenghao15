# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify
import json

lock_bp = Blueprint('lock', __name__)

@lock_bp.route('/api/lock/status')
def lock_status():
    """获取锁定状态"""
    return jsonify({'locked': False})

@lock_bp.route('/api/lock/toggle', methods=['POST'])
def toggle_lock():
    """切换锁定状态"""
    return jsonify({'success': True, 'locked': True})
