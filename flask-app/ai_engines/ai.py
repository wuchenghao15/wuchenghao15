# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

ai_bp = Blueprint(r'ai', __name__, url_prefix=r'/ai')

@ai_bp.route(r'/management')
def management():
    r"""AI管理页面r"""
    return render_template(r'ai_management.html')

@ai_bp.route(r'/instances')
def instances():
    r"""AI实例管理r"""
    return render_template(r'ai_instances.html')

@ai_bp.route(r'/rules')
def rules():
    r"""AI规则管理r"""
    return render_template(r'ai_rules.html')
