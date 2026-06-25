import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
API模块初始化文件,整合所有API蓝图
"""

from flask import Blueprint

try:
    from app.api.auto_update_api import auto_update_api_bp
except ImportError:
    auto_update_api_bp = None

try:
    from app.api.firewall_api import firewall_api_bp
except ImportError:
    firewall_api_bp = None

try:
    from app.api.server_system_api import server_system_api_bp
except ImportError:
    server_system_api_bp = None

try:
    from app.api.question_bank_ai_api import question_bank_ai_api
except ImportError:
    question_bank_ai_api = None

try:
    from app.api.student_learning_api import student_learning_api
except ImportError:
    student_learning_api = None

try:
    from app.api.version_api import version_api
except ImportError:
    version_api = None

# 创建主API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 注册子蓝图
if auto_update_api_bp:
    api_bp.register_blueprint(auto_update_api_bp, url_prefix='/auto-update')

if firewall_api_bp:
    api_bp.register_blueprint(firewall_api_bp, url_prefix='/firewall')

if server_system_api_bp:
    api_bp.register_blueprint(server_system_api_bp, url_prefix='/server')

if question_bank_ai_api:
    api_bp.register_blueprint(question_bank_ai_api, url_prefix='/question-bank-ai')

if student_learning_api:
    api_bp.register_blueprint(student_learning_api, url_prefix='/student')

if version_api:
    api_bp.register_blueprint(version_api, url_prefix='/version')

# 导入API路由
try:
    from app.api import routes
except ImportError:
    pass