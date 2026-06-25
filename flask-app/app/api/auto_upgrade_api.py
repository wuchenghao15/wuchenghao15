#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能自动升级测试系统API接口
提供RESTful API访问自动升级、智能错误修复和AI学习功能
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, List, Any

try:
    from app.ai.auto_upgrade_test_system import (
        smart_auto_upgrade_test_system,
        ErrorType,
        ErrorSeverity
    )
except ImportError:
    try:
        from ai_engines.auto_upgrade_test_system import (
            smart_auto_upgrade_test_system,
            ErrorType,
            ErrorSeverity
        )
    except ImportError:
        smart_auto_upgrade_test_system = None
        ErrorType = None
        ErrorSeverity = None

logger = logging.getLogger('smart_auto_upgrade_api')

upgrade_bp = Blueprint('smart_auto_upgrade', __name__, url_prefix='/api/auto-upgrade')


@upgrade_bp.route('/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    try:
        status = smart_auto_upgrade_test_system.get_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/check', methods=['POST'])
def check_upgrades():
    """检查可用升级"""
    try:
        upgrades = smart_auto_upgrade_test_system.check_for_upgrades()
        return jsonify({
            'success': True,
            'upgrades': upgrades,
            'current_version': smart_auto_upgrade_test_system.current_version
        })
    except Exception as e:
        logger.error(f"检查升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/execute', methods=['POST'])
def execute_upgrade():
    """执行升级"""
    try:
        data = request.get_json() or {}
        version = data.get('version')

        result = smart_auto_upgrade_test_system.execute_upgrade(version)
        return jsonify(result)
    except Exception as e:
        logger.error(f"执行升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/detect-errors', methods=['POST'])
def detect_errors():
    """智能检测错误"""
    try:
        errors = smart_auto_upgrade_test_system.detect_errors()
        error_list = [e.to_dict() for e in errors]

        return jsonify({
            'success': True,
            'errors': error_list,
            'count': len(errors)
        })
    except Exception as e:
        logger.error(f"检测错误失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-fix', methods=['POST'])
def auto_fix_errors():
    """智能自动修复错误"""
    try:
        data = request.get_json() or {}
        error_ids = data.get('error_ids', [])

        errors = smart_auto_upgrade_test_system.detect_errors()

        if error_ids:
            errors = [e for e in errors if e.id in error_ids]

        result = smart_auto_upgrade_test_system.auto_fix_errors(errors)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"自动修复失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/maintenance', methods=['POST'])
def run_maintenance():
    """执行维护任务"""
    try:
        result = smart_auto_upgrade_test_system.run_daily_maintenance()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"执行维护失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/predictive-maintenance', methods=['POST'])
def run_predictive_maintenance():
    """执行预测性维护"""
    try:
        result = smart_auto_upgrade_test_system.run_predictive_maintenance()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"执行预测性维护失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/history/upgrades', methods=['GET'])
def get_upgrade_history():
    """获取升级历史"""
    try:
        limit = int(request.args.get('limit', 50))
        history = smart_auto_upgrade_test_system.get_upgrade_history(limit)
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取升级历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/history/errors', methods=['GET'])
def get_error_history():
    """获取错误历史"""
    try:
        limit = int(request.args.get('limit', 100))
        history = smart_auto_upgrade_test_system.get_error_history(limit)
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取错误历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/statistics/errors', methods=['GET'])
def get_error_statistics():
    """获取错误统计"""
    try:
        stats = smart_auto_upgrade_test_system.get_error_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"获取错误统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/ai-insights', methods=['GET'])
def get_ai_insights():
    """获取AI学习洞察"""
    try:
        insights = smart_auto_upgrade_test_system.get_ai_insights()
        return jsonify({
            'success': True,
            'insights': insights
        })
    except Exception as e:
        logger.error(f"获取AI洞察失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/system-metrics', methods=['GET'])
def get_system_metrics():
    """获取系统指标"""
    try:
        metrics = smart_auto_upgrade_test_system.get_system_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices', methods=['GET'])
def get_data_matrices():
    """获取数据矩阵"""
    try:
        matrix_type = request.args.get('type')
        matrices = smart_auto_upgrade_test_system.get_data_matrices(matrix_type)
        return jsonify({
            'success': True,
            'matrices': matrices
        })
    except Exception as e:
        logger.error(f"获取数据矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices/error-type', methods=['GET'])
def get_error_type_matrix():
    """获取错误类型矩阵"""
    try:
        matrix = smart_auto_upgrade_test_system.get_error_type_matrix()
        return jsonify({
            'success': True,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取错误类型矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices/performance', methods=['GET'])
def get_performance_matrix():
    """获取性能指标矩阵"""
    try:
        matrix = smart_auto_upgrade_test_system.get_performance_matrix()
        return jsonify({
            'success': True,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取性能指标矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices/correlation', methods=['GET'])
def get_correlation_matrix():
    """获取相关性矩阵"""
    try:
        matrix = smart_auto_upgrade_test_system.get_correlation_matrix()
        return jsonify({
            'success': True,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取相关性矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices/trend', methods=['GET'])
def get_trend_matrix():
    """获取趋势矩阵"""
    try:
        matrix = smart_auto_upgrade_test_system.get_trend_matrix()
        return jsonify({
            'success': True,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取趋势矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/data-matrices/heatmap', methods=['GET'])
def get_heatmap_matrix():
    """获取热图矩阵"""
    try:
        matrix = smart_auto_upgrade_test_system.get_heatmap_matrix()
        return jsonify({
            'success': True,
            'matrix': matrix
        })
    except Exception as e:
        logger.error(f"获取热图矩阵失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/config', methods=['GET'])
def get_config():
    """获取配置"""
    try:
        config = smart_auto_upgrade_test_system.config
        return jsonify({
            'success': True,
            'config': config,
            'ai_learning_enabled': smart_auto_upgrade_test_system.ai_learning_enabled,
            'auto_upgrade_enabled': smart_auto_upgrade_test_system.auto_upgrade_enabled
        })
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/config', methods=['PUT'])
def update_config():
    """更新配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的配置数据'}), 400

        smart_auto_upgrade_test_system.config.update(data)

        if 'ai_learning_enabled' in data:
            if data['ai_learning_enabled']:
                smart_auto_upgrade_test_system.enable_ai_learning()
            else:
                smart_auto_upgrade_test_system.disable_ai_learning()

        if 'auto_upgrade_enabled' in data:
            if data['auto_upgrade_enabled']:
                smart_auto_upgrade_test_system.enable_auto_upgrade()
            else:
                smart_auto_upgrade_test_system.disable_auto_upgrade()

        return jsonify({
            'success': True,
            'message': '配置已更新',
            'config': smart_auto_upgrade_test_system.config
        })
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/ai-learning/enable', methods=['POST'])
def enable_ai_learning():
    """启用AI学习"""
    try:
        smart_auto_upgrade_test_system.enable_ai_learning()
        return jsonify({
            'success': True,
            'message': 'AI学习已启用'
        })
    except Exception as e:
        logger.error(f"启用AI学习失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/ai-learning/disable', methods=['POST'])
def disable_ai_learning():
    """禁用AI学习"""
    try:
        smart_auto_upgrade_test_system.disable_ai_learning()
        return jsonify({
            'success': True,
            'message': 'AI学习已禁用'
        })
    except Exception as e:
        logger.error(f"禁用AI学习失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-upgrade/enable', methods=['POST'])
def enable_auto_upgrade():
    """启用自动升级"""
    try:
        smart_auto_upgrade_test_system.enable_auto_upgrade()
        return jsonify({
            'success': True,
            'message': '自动升级已启用'
        })
    except Exception as e:
        logger.error(f"启用自动升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-upgrade/disable', methods=['POST'])
def disable_auto_upgrade():
    """禁用自动升级"""
    try:
        smart_auto_upgrade_test_system.disable_auto_upgrade()
        return jsonify({
            'success': True,
            'message': '自动升级已禁用'
        })
    except Exception as e:
        logger.error(f"禁用自动升级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-maintenance/enable', methods=['POST'])
def enable_auto_maintenance():
    """启用自动维护"""
    try:
        smart_auto_upgrade_test_system.config['auto_maintenance_enabled'] = True
        return jsonify({
            'success': True,
            'message': '自动维护已启用'
        })
    except Exception as e:
        logger.error(f"启用自动维护失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-maintenance/disable', methods=['POST'])
def disable_auto_maintenance():
    """禁用自动维护"""
    try:
        smart_auto_upgrade_test_system.config['auto_maintenance_enabled'] = False
        return jsonify({
            'success': True,
            'message': '自动维护已禁用'
        })
    except Exception as e:
        logger.error(f"禁用自动维护失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/health', methods=['GET'])
def get_system_health():
    """获取系统健康状态"""
    try:
        health = smart_auto_upgrade_test_system.get_system_health()
        return jsonify({
            'success': True,
            'health': health
        })
    except Exception as e:
        logger.error(f"获取系统健康状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """获取检测到的异常"""
    try:
        anomalies = smart_auto_upgrade_test_system.get_anomalies()
        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'count': len(anomalies)
        })
    except Exception as e:
        logger.error(f"获取异常失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/risk-predictions', methods=['GET'])
def get_risk_predictions():
    """获取风险预测"""
    try:
        predictions = smart_auto_upgrade_test_system.get_risk_predictions()
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    except Exception as e:
        logger.error(f"获取风险预测失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/insights', methods=['GET'])
def get_insights_report():
    """获取综合洞察报告"""
    try:
        insights = smart_auto_upgrade_test_system.get_insights_report()
        return jsonify({
            'success': True,
            'insights': insights
        })
    except Exception as e:
        logger.error(f"获取洞察报告失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/insights/history', methods=['GET'])
def get_insights_history():
    """获取洞察历史"""
    try:
        limit = int(request.args.get('limit', 10))
        history = smart_auto_upgrade_test_system.get_insights_history(limit)
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取洞察历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """获取告警"""
    try:
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))
        alerts = smart_auto_upgrade_test_system.get_alerts(severity, limit)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        logger.error(f"获取告警失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/alerts', methods=['DELETE'])
def clear_alerts():
    """清除告警"""
    try:
        smart_auto_upgrade_test_system.clear_alerts()
        return jsonify({
            'success': True,
            'message': '告警已清除'
        })
    except Exception as e:
        logger.error(f"清除告警失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/matrix-info', methods=['GET'])
def get_matrix_info():
    """获取矩阵信息"""
    try:
        info = smart_auto_upgrade_test_system.get_matrix_info()
        return jsonify({
            'success': True,
            'info': info
        })
    except Exception as e:
        logger.error(f"获取矩阵信息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/comprehensive', methods=['GET'])
def get_comprehensive_status():
    """获取综合状态"""
    try:
        status = smart_auto_upgrade_test_system.get_comprehensive_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取综合状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-analytics/enable', methods=['POST'])
def enable_auto_analytics():
    """启用自动分析"""
    try:
        smart_auto_upgrade_test_system.config['auto_analytics'] = True
        return jsonify({
            'success': True,
            'message': '自动分析已启用'
        })
    except Exception as e:
        logger.error(f"启用自动分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/auto-analytics/disable', methods=['POST'])
def disable_auto_analytics():
    """禁用自动分析"""
    try:
        smart_auto_upgrade_test_system.config['auto_analytics'] = False
        return jsonify({
            'success': True,
            'message': '自动分析已禁用'
        })
    except Exception as e:
        logger.error(f"禁用自动分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/alerts/enable', methods=['POST'])
def enable_alerts():
    """启用告警"""
    try:
        smart_auto_upgrade_test_system.config['alert_enabled'] = True
        return jsonify({
            'success': True,
            'message': '告警已启用'
        })
    except Exception as e:
        logger.error(f"启用告警失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@upgrade_bp.route('/alerts/disable', methods=['POST'])
def disable_alerts():
    """禁用告警"""
    try:
        smart_auto_upgrade_test_system.config['alert_enabled'] = False
        return jsonify({
            'success': True,
            'message': '告警已禁用'
        })
    except Exception as e:
        logger.error(f"禁用告警失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
