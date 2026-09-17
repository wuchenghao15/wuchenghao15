# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
from app.middlewares.system_container import system_container
from .internal_instruction_handler import dispatch_ai_internal_instruction
from .ai_fix_handler import auto_detect_and_process_code_fix

ai_bp = Blueprint(r'ai', __name__, url_prefix=r'/ai')

@system_container(require_auth='login')
@ai_bp.route('/internal/instruction', methods=['POST'])
@system_container(require_auth='login')
def internal_instruction_entry():
    r"""AI内部指令统一调度入口，自动识别普通对话和代码修复任务"""
    req_data = request.get_json(silent=True) or {}
    # 自动判断是否为代码修改/修复任务
    is_code_fix_task = (
        req_data.get('task_type') == 'code_fix'
        or 'target_file' in req_data
        or 'error_trace' in req_data
        or (isinstance(req_data.get('prompt'), str) and any(
            keyword in req_data['prompt'].lower()
            for keyword in ['fix code', '修复代码', '修正代码', '修改代码', '调试代码', 'debug', '代码报错', '代码问题']
        ))
    )
    if is_code_fix_task:
        resp_data = auto_detect_and_process_code_fix(req_data)
    else:
        resp_data = dispatch_ai_internal_instruction(req_data)
    return jsonify(resp_data)

@ai_bp.route(r'/management')
@system_container(require_auth='login')
def management():
    r"""AI管理页面"""
    return render_template(r'ai_management.html')

@ai_bp.route(r'/instances')
@system_container(require_auth='login')
def instances():
    r"""AI实例管理"""
    return render_template(r'ai_instances.html')

@ai_bp.route(r'/rules')
@system_container(require_auth='login')
def rules():
    r"""AI规则管理"""
    return render_template(r'ai_rules.html')

@ai_bp.route(r'/new_feature')
@system_container(require_auth='login')
def new_feature():
    r"""新功能管理"""
    return render_template(r'ai_new_feature.html')
