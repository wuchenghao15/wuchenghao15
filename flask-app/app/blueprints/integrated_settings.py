# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
import sys

integrated_settings_bp = Blueprint('integrated_settings', __name__, url_prefix='/settings')

@integrated_settings_bp.route('/')
def index():
    """集成设置页面"""
    return render_template('integrated_settings.html')

@integrated_settings_bp.route('/system')
def system_settings():
    """系统设置"""
    return render_template('system_config.html')

@integrated_settings_bp.route('/security')
def security_settings():
    """安全设置"""
    return render_template('security_settings.html')
