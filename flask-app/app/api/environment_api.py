#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理系统API接口
提供RESTful API访问多环境管理系统
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, List, Any

from app.ai.multi_environment_manager import (
    multi_env_manager,
    EnvironmentType,
    SystemType
)

logger = logging.getLogger('env_api')

env_bp = Blueprint('environment', __name__, url_prefix='/api/environments')


@env_bp.route('/', methods=['GET'])
def list_environments():
    """列出所有环境"""
    try:
        include_status = request.args.get('include_status', 'true').lower() == 'true'
        environments = multi_env_manager.list_environments(include_status)
        return jsonify({
            'success': True,
            'environments': environments,
            'current': multi_env_manager.current_environment
        })
    except Exception as e:
        logger.error(f"获取环境列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/current', methods=['GET'])
def get_current():
    """获取当前环境"""
    try:
        current = multi_env_manager.get_current_environment()
        if not current:
            return jsonify({'success': False, 'error': '无激活环境'}), 404

        return jsonify({
            'success': True,
            'environment': current
        })
    except Exception as e:
        logger.error(f"获取当前环境失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/activate', methods=['POST'])
def activate_environment(env_id: str):
    """激活指定环境"""
    try:
        success = multi_env_manager.activate_environment(env_id)
        if success:
            return jsonify({
                'success': True,
                'message': f'环境 {env_id} 已激活',
                'environment': multi_env_manager.get_current_environment()
            })
        else:
            return jsonify({'success': False, 'error': '环境激活失败'}), 400
    except Exception as e:
        logger.error(f"激活环境失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/config', methods=['GET'])
def get_environment_config(env_id: str):
    """获取环境配置"""
    try:
        config = multi_env_manager.get_environment_config(env_id)
        if config is None:
            return jsonify({'success': False, 'error': '环境不存在'}), 404

        return jsonify({
            'success': True,
            'environment_id': env_id,
            'config': config
        })
    except Exception as e:
        logger.error(f"获取环境配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/config', methods=['PUT'])
def update_environment_config(env_id: str):
    """更新环境配置"""
    try:
        config = request.get_json()
        if not config:
            return jsonify({'success': False, 'error': '无效的配置数据'}), 400

        success = multi_env_manager.update_environment_config(env_id, config)
        if success:
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'config': multi_env_manager.get_environment_config(env_id)
            })
        else:
            return jsonify({'success': False, 'error': '环境不存在'}), 404
    except Exception as e:
        logger.error(f"更新环境配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/validate', methods=['POST'])
def validate_environment(env_id: str):
    """验证环境"""
    try:
        validation = multi_env_manager.validate_environment(env_id)
        return jsonify({
            'success': True,
            'validation': validation
        })
    except Exception as e:
        logger.error(f"验证环境失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/execute', methods=['POST'])
def execute_in_environment(env_id: str):
    """在环境中执行代码"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        timeout = data.get('timeout', 30)

        result = multi_env_manager.execute_in_environment(env_id, code, timeout)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"在环境中执行代码失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/<env_id>/test', methods=['POST'])
def run_tests_in_environment(env_id: str):
    """在环境中运行测试"""
    try:
        data = request.get_json() or {}
        suite_id = data.get('suite_id')

        result = multi_env_manager.run_tests_in_environment(env_id, suite_id)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"在环境中运行测试失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/sandbox', methods=['GET'])
def list_sandboxes():
    """列出所有沙盒"""
    try:
        status = multi_env_manager.get_system_status(SystemType.SANDBOX)
        return jsonify({
            'success': True,
            'sandboxes': status['sandboxes'],
            'active_sandbox': status['active_sandbox']
        })
    except Exception as e:
        logger.error(f"获取沙盒列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/sandbox/<sandbox_id>/activate', methods=['POST'])
def activate_sandbox(sandbox_id: str):
    """激活沙盒"""
    try:
        success = multi_env_manager.sandbox_manager.activate_sandbox(sandbox_id)
        return jsonify({
            'success': success,
            'message': f'沙盒 {sandbox_id} 已激活' if success else '激活失败'
        })
    except Exception as e:
        logger.error(f"激活沙盒失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/shadow', methods=['GET'])
def list_shadows():
    """列出所有影子系统"""
    try:
        status = multi_env_manager.get_system_status(SystemType.SHADOW)
        return jsonify({
            'success': True,
            'shadows': status['shadows']
        })
    except Exception as e:
        logger.error(f"获取影子系统列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/test/suites', methods=['GET'])
def list_test_suites():
    """列出所有测试套件"""
    try:
        suites = [
            {
                'id': suite_id,
                'total_tests': suite['total_tests'],
                'passed': suite['passed'],
                'failed': suite['failed']
            }
            for suite_id, suite in multi_env_manager.test_system.test_suites.items()
        ]
        return jsonify({
            'success': True,
            'suites': suites
        })
    except Exception as e:
        logger.error(f"获取测试套件列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/test/<suite_id>/run', methods=['POST'])
def run_test_suite(suite_id: str):
    """运行测试套件"""
    try:
        result = multi_env_manager.test_system.run_test(suite_id)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"运行测试套件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/test/stats', methods=['GET'])
def get_test_stats():
    """获取测试统计"""
    try:
        stats = multi_env_manager.test_system.get_test_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"获取测试统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """获取仪表板"""
    try:
        dashboard = multi_env_manager.get_dashboard()
        return jsonify({
            'success': True,
            'dashboard': dashboard
        })
    except Exception as e:
        logger.error(f"获取仪表板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/export/<env_id>', methods=['GET'])
def export_environment(env_id: str):
    """导出环境配置"""
    try:
        config = multi_env_manager.export_environment_config(env_id)
        if config is None:
            return jsonify({'success': False, 'error': '环境不存在'}), 404

        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        logger.error(f"导出环境配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@env_bp.route('/import', methods=['POST'])
def import_environment():
    """导入环境配置"""
    try:
        config = request.get_json()
        if not config:
            return jsonify({'success': False, 'error': '无效的配置数据'}), 400

        success = multi_env_manager.import_environment_config(json.dumps(config))
        return jsonify({
            'success': success,
            'message': '环境配置已导入' if success else '导入失败'
        })
    except Exception as e:
        logger.error(f"导入环境配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
