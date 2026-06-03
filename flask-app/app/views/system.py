# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
import sys

system_bp = Blueprint('system', __name__, url_prefix='/system')

@system_bp.route('/config')
def config():
    """系统配置页面"""
    return render_template('system_config.html')

@system_bp.route('/settings')
def settings():
    """系统设置页面"""
    return render_template('settings.html')

@system_bp.route('/monitoring')
def monitoring():
    """系统监控页面"""
    return render_template('monitoring.html')
