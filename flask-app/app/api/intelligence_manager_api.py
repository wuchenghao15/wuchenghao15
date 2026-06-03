# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智体管家API接口,用于查询和管理智体管家的状态和配置
"""

from flask import Blueprint, jsonify, request
from app.ai.intelligence_manager import intelligence_manager
from app.utils.logging import logger
import logging
import json
import sys

# 创建蓝图
intelligence_manager_api_bp = Blueprint('intelligence_manager_api', __name__)


@intelligence_manager_api_bp.route('/status', methods=['GET'])
def get_intelligence_manager_status():
    """获取智体管家的状态信息
    GET /api/intelligence-manager/status
    """
    try:
        status = intelligence_manager.get_status()
        return jsonify({
            'success': True,
            'data': status
        }), 200
    except Exception as e:
        logger.error(f"获取智体管家状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"获取智体管家状态失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/config', methods=['GET'])
def get_intelligence_manager_config():
    """获取智体管家的配置信息
    GET /api/intelligence-manager/config
    """
    try:
        config = intelligence_manager.config
        return jsonify({
            'success': True,
            'data': config
        }), 200
    except Exception as e:
        logger.error(f"获取智体管家配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"获取智体管家配置失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/config', methods=['PUT'])
def update_intelligence_manager_config():
    """更新智体管家的配置信息
    PUT /api/intelligence-manager/config
    """
    try:
        new_config = request.json
        if not isinstance(new_config, dict):
            return jsonify({
                'success': False,
                'error': '配置必须是JSON对象'
            }), 400

        intelligence_manager.update_config(new_config)
        return jsonify({
            'success': True,
            'message': '智体管家配置更新成功',
            'data': intelligence_manager.config
        }), 200
    except Exception as e:
        logger.error(f"更新智体管家配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"更新智体管家配置失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/restart-component/<component_name>', methods=['POST'])
def restart_component(component_name):
    """重启单个AI组件
    POST /api/intelligence-manager/restart-component/<component_name>
    """
    try:
        intelligence_manager.restart_component(component_name)
        return jsonify({
            'success': True,
            'message': f"组件 {component_name} 重启成功"
        }), 200
    except Exception as e:
        logger.error(f"重启组件 {component_name} 失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"重启组件 {component_name} 失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/optimize-system', methods=['POST'])
def optimize_system():
    """优化整个系统
    POST /api/intelligence-manager/optimize-system
    """
    try:
        intelligence_manager.optimize_system()
        return jsonify({
            'success': True,
            'message': "系统优化完成"
        }), 200
    except Exception as e:
        logger.error(f"优化系统失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"优化系统失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/report', methods=['GET'])
def get_system_report():
    """获取当前系统报告
    GET /api/intelligence-manager/report
    """
    try:
        report = intelligence_manager.generate_report()
        return jsonify({
            'success': True,
            'data': report
        }), 200
    except Exception as e:
        logger.error(f"生成系统报告失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"生成系统报告失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/start', methods=['POST'])
def start_intelligence_manager():
    """启动智体管家
    POST /api/intelligence-manager/start
    """
    try:
        intelligence_manager.start()
        return jsonify({
            'success': True,
            'message': "智体管家启动成功"
        }), 200
    except Exception as e:
        logger.error(f"启动智体管家失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"启动智体管家失败: {str(e)}"
        }), 500


@intelligence_manager_api_bp.route('/stop', methods=['POST'])
def stop_intelligence_manager():
    """停止智体管家
    POST /api/intelligence-manager/stop
    """
    try:
        intelligence_manager.stop()
        return jsonify({
            'success': True,
            'message': "智体管家停止成功"
        }), 200
    except Exception as e:
        logger.error(f"停止智体管家失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"停止智体管家失败: {str(e)}"
        }), 500
