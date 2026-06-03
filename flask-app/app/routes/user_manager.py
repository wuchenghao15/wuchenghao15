# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template
import json

user_manager_bp = Blueprint('user_manager', __name__, url_prefix='/user-manager')

@user_manager_bp.route('/')
def index():
    """用户管理页面"""
    return render_template('smart_user_management.html')

@user_manager_bp.route('/users')
def users():
    """获取用户列表"""
    return jsonify({'users': []})

@user_manager_bp.route('/groups')
def groups():
    """用户组管理"""
    return render_template('user_groups.html')
