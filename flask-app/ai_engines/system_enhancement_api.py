#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SystemEnhancementApi — 系统增强管理器 Blueprint
=============================================
modular_start.py stage 4 调用：
  from ai_engines.system_enhancement_api import register_enhancement_blueprint
  register_enhancement_blueprint(app)

注册后提供 /api/enhancement/* 下的查询接口：
  - GET /api/enhancement/stats              统计
  - GET /api/enhancement/ports              端口列表
  - GET /api/enhancement/db_cluster          集群节点
  - GET /api/enhancement/ai_nodes            AI 节点
  - GET /api/enhancement/layouts             布局
  - GET /api/enhancement/permission_rules   权限规则
  - GET /api/enhancement/models             AI 模型
"""

from __future__ import annotations

from flask import Blueprint, jsonify
from app.middlewares.system_container import system_container


def register_enhancement_blueprint(app) -> bool:
    """注册系统增强管理器 Blueprint 到 app

    Args:
        app: Flask 应用对象

    Returns:
        bool: True 表示注册成功
    """
    try:
        from ai_engines.system_enhancement_manager import system_enhancement_manager
    except Exception as e:
        # 模块缺失时打印错误但返回 False（让上层走 WARNING 路径）
        print(f"  ! system_enhancement_manager 加载失败: {e}")
        return False

    bp = Blueprint('system_enhancement', __name__, url_prefix='/api/enhancement')

    @system_container(require_auth='login')
    @bp.route('/stats', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_stats():
        return jsonify({'success': True, 'stats': system_enhancement_manager.stats()})

    @bp.route('/ports', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_ports():
        return jsonify({'success': True, 'ports': system_enhancement_manager.list_ports()})

    @bp.route('/db_cluster', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_db_cluster():
        return jsonify({'success': True, 'nodes': system_enhancement_manager.list_db_cluster()})

    @bp.route('/ai_nodes', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_ai_nodes():
        return jsonify({'success': True, 'nodes': system_enhancement_manager.list_ai_nodes()})

    @bp.route('/layouts', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_layouts():
        return jsonify({'success': True, 'layouts': system_enhancement_manager.list_layouts()})

    @bp.route('/permission_rules', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_permission_rules():
        return jsonify({'success': True, 'rules': system_enhancement_manager.list_permission_rules()})

    @bp.route('/models', methods=['GET'])
    @system_container(require_auth='login')
    def enhancement_models():
        return jsonify({'success': True, 'models': system_enhancement_manager.list_models()})

    app.register_blueprint(bp)
    return True


__all__ = ['register_enhancement_blueprint']
