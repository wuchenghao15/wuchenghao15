# -*- coding: utf-8 -*-
# Services package
# 使用延迟导入,避免循环导入问题

_rule_management_service = None
_system_version_service = None
_javascript_optimization_service = None
_adaptive_upgrade_service = None
_ai_brain_service = None
_login_route_service = None
_enhanced_ai_service = None
_data_upload_service = None
_config_service = None
_error_report_service = None
_ai_auto_fix_service = None
_backend_maintenance_ai = None


def get_rule_management_service():
    """获取规则管理服务实例"""
    global _rule_management_service
    if _rule_management_service is None:
        from app.services.rule_management import rule_management_service
        _rule_management_service = rule_management_service
    return _rule_management_service


def get_system_version_service():
    """获取系统版本服务实例"""
    global _system_version_service
    if _system_version_service is None:
        from app.services.system_version_service import system_version_service
        _system_version_service = system_version_service
    return _system_version_service


def get_javascript_optimization_service():
    """获取JavaScript优化服务实例"""
    global _javascript_optimization_service
    if _javascript_optimization_service is None:
        from app.services.javascript_optimization_service import javascript_optimization_service
        _javascript_optimization_service = javascript_optimization_service
    return _javascript_optimization_service


def get_adaptive_upgrade_service():
    """获取自适应升级服务实例"""
    global _adaptive_upgrade_service
    if _adaptive_upgrade_service is None:
        from app.services.adaptive_upgrade_service import adaptive_upgrade_service
        _adaptive_upgrade_service = adaptive_upgrade_service
    return _adaptive_upgrade_service


def get_ai_brain_service():
    """获取AI脑库服务实例"""
    global _ai_brain_service
    if _ai_brain_service is None:
        from app.services.ai_brain_service import ai_brain_service
        _ai_brain_service = ai_brain_service
    return _ai_brain_service


def get_login_route_service():
    """获取登录路由服务实例"""
    global _login_route_service
    if _login_route_service is None:
        from app.services.login_route_service import login_route_service
        _login_route_service = login_route_service
    return _login_route_service


def get_enhanced_ai_service():
    """获取增强AI服务实例"""
    global _enhanced_ai_service
    if _enhanced_ai_service is None:
        from app.services.enhanced_ai_service import enhanced_ai_service
        _enhanced_ai_service = enhanced_ai_service
    return _enhanced_ai_service


def get_data_upload_service():
    """获取数据上传服务实例"""
    global _data_upload_service
    if _data_upload_service is None:
        from app.services.data_upload_service import data_upload_service
        _data_upload_service = data_upload_service
    return _data_upload_service


def get_config_service():
    """获取配置服务实例"""
    global _config_service
    if _config_service is None:
        from app.services.config_service import config_service
        _config_service = config_service
    return _config_service


def get_error_report_service():
    """获取错误上报服务实例"""
    global _error_report_service
    if _error_report_service is None:
        from app.services.error_report_service import error_report_service
        _error_report_service = error_report_service
    return _error_report_service


def get_ai_auto_fix_service():
    """获取AI自动修复服务实例"""
    global _ai_auto_fix_service
    if _ai_auto_fix_service is None:
        from app.services.ai_auto_fix_service import ai_auto_fix_service
        _ai_auto_fix_service = ai_auto_fix_service
    return _ai_auto_fix_service


def get_backend_maintenance_ai():
    """获取后台维护AI服务实例"""
    global _backend_maintenance_ai
    if _backend_maintenance_ai is None:
        from app.services.backend_maintenance_ai import backend_maintenance_ai
        _backend_maintenance_ai = backend_maintenance_ai
    return _backend_maintenance_ai

