# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/management')
def management():
    """AI管理页面"""
    return render_template('ai_management.html')

@ai_bp.route('/instances')
def instances():
    """AI实例管理"""
    return render_template('ai_instances.html')

@ai_bp.route('/rules')
def rules():
    """AI规则管理"""
    return render_template('ai_rules.html')
