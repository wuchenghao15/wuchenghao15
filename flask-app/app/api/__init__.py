#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API模块初始化文件，整合所有API蓝图

from flask import Blueprint
from app.api.auto_update_api import auto_update_api_bp
from app.api.firewall_api import firewall_api_bp
from app.api.server_system_api import server_system_api_bp

# 创建主API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 注册子蓝图
api_bp.register_blueprint(auto_update_api_bp, url_prefix='/auto-update')
api_bp.register_blueprint(firewall_api_bp, url_prefix='/firewall')
api_bp.register_blueprint(server_system_api_bp, url_prefix='/server')

# 导入API路由
from app.api import routes

"""