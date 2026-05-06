#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI线程进程管理器API蓝图

from flask import Blueprint, jsonify, request
from app.ai.thread_process_manager import ai_thread_process_manager

# 创建API蓝图
thread_process_manager_api_bp = Blueprint('thread_process_manager_api', __name__)

@thread_process_manager_api_bp.route('/status', methods=['GET'])
def get_status():
    """获取AI线程进程管理器状态"""
    try:
        status = ai_thread_process_manager.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取状态失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/config', methods=['GET'])
def get_config():
    """获取AI线程进程管理器配置"""
    try:
        return jsonify({
            'data': status['config']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取配置失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/config', methods=['PUT'])
def update_config():
    """更新AI线程进程管理器配置"""
    try:
        if not isinstance(new_config, dict):
            return jsonify({
                'success': False,
                'error': '配置必须是JSON对象'
            }), 400

        ai_thread_process_manager.update_config(new_config)
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'更新配置失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/monitor-data', methods=['GET'])
def get_monitor_data():
    """获取监控数据"""
    try:
        return jsonify({
            'success': True,
            'data': status['monitor_data']
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取监控数据失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/start', methods=['POST'])
def start_manager():
    """启动AI线程进程管理器"""
    try:
        return jsonify({
            'success': True,
            'message': 'AI线程进程管理器已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'启动管理器失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/stop', methods=['POST'])
def stop_manager():
    """停止AI线程进程管理器"""
    try:
        return jsonify({
            'success': True,
            'message': 'AI线程进程管理器已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'停止管理器失败: {str(e)}'
        }), 500

@thread_process_manager_api_bp.route('/restart', methods=['POST'])
def restart_manager():
    """重启AI线程进程管理器"""
    try:
        ai_thread_process_manager.start()
        return jsonify({
            'success': True,
            'message': 'AI线程进程管理器已重启'
        })
    except Exception as e:
        return jsonify({
            'success': False,
