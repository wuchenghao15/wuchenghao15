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

try:
    from app.api.config_api import config_api
except ImportError:
    config_api = None

try:
    from app.api.exam_api import exam_api
except ImportError:
    exam_api = None

try:
    from app.api.super_admin_data_api import super_admin_data_api
except ImportError:
    super_admin_data_api = None

# ==================== K12教育系统API ====================
try:
    from app.api.parent_api import parent_api
except ImportError:
    parent_api = None
    logger.warning("[API] 家长端API导入失败")

try:
    from app.api.teacher_k12_api import teacher_k12_api
except ImportError:
    teacher_k12_api = None
    logger.warning("[API] 教师端K12 API导入失败")

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

if config_api:
    api_bp.register_blueprint(config_api)

if exam_api:
    api_bp.register_blueprint(exam_api)

if super_admin_data_api:
    api_bp.register_blueprint(super_admin_data_api)

# 注册K12教育系统API蓝图
if parent_api:
    api_bp.register_blueprint(parent_api)
    logger.info("[API] 家长端API蓝图注册完成")

if teacher_k12_api:
    api_bp.register_blueprint(teacher_k12_api)
    logger.info("[API] 教师端K12 API蓝图注册完成")

# 导入API路由
try:
    from app.api import routes
except ImportError:
    pass