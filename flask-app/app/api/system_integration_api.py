#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统整合与数据库上报API接口
提供跨系统数据整合、统一报表和数据库上报功能
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, List

from app.ai.system_integration import (
    system_integration_hub,
    enhanced_db_reporter,
    SystemType,
    ReportPriority
)

logger = logging.getLogger('system_integration_api')

integration_bp = Blueprint('system_integration', __name__, url_prefix='/api/integration')


@integration_bp.route('/status', methods=['GET'])
def get_integration_status():
    """获取系统整合状态"""
    try:
        subsystems = system_integration_hub.subsystems
        integrated_types = list(system_integration_hub.integrated_data.keys())
        relations_count = len(system_integration_hub.cross_system_relations)
        
        return jsonify({
            'success': True,
            'status': {
                'subsystems_count': len(subsystems),
                'registered_subsystems': subsystems,
                'integrated_data_types': integrated_types,
                'cross_system_relations': relations_count,
                'last_integration': system_integration_hub.last_integration_time,
                'running': system_integration_hub.running
            }
        })
    except Exception as e:
        logger.error(f"获取整合状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/subsystems', methods=['GET'])
def get_subsystems():
    """获取注册的子系统"""
    try:
        return jsonify({
            'success': True,
            'subsystems': system_integration_hub.subsystems,
            'count': len(system_integration_hub.subsystems)
        })
    except Exception as e:
        logger.error(f"获取子系统失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/subsystems', methods=['POST'])
def register_subsystem():
    """注册子系统"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        system_type_str = data.get('system_type')
        system_info = data.get('system_info', {})
        
        try:
            system_type = SystemType(system_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的系统类型: {system_type_str}'}), 400
        
        system_integration_hub.register_subsystem(system_type, system_info)
        
        return jsonify({
            'success': True,
            'message': f'子系统 {system_type.value} 已注册'
        })
    except Exception as e:
        logger.error(f"注册子系统失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/integrate', methods=['POST'])
def integrate_data():
    """整合数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        data_type = data.get('data_type')
        integration_data = data.get('data')
        metadata = data.get('metadata', {})
        
        if not data_type or not integration_data:
            return jsonify({'success': False, 'error': '缺少必需字段'}), 400
        
        system_integration_hub.integrate_data(data_type, integration_data, metadata)
        
        return jsonify({
            'success': True,
            'message': f'数据已整合: {data_type}'
        })
    except Exception as e:
        logger.error(f"整合数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/data', methods=['GET'])
def get_integrated_data():
    """获取已整合数据"""
    try:
        data_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        data = system_integration_hub.get_integrated_data(data_type, limit)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': sum(len(records) for records in data.values()) if isinstance(data, dict) else len(data)
        })
    except Exception as e:
        logger.error(f"获取整合数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/relations', methods=['GET'])
def get_cross_system_relations():
    """获取跨系统关联"""
    try:
        relation_type = request.args.get('relation_type')
        
        relations = system_integration_hub.get_cross_system_relations(relation_type)
        
        return jsonify({
            'success': True,
            'relations': relations,
            'count': sum(len(r) for r in relations.values()) if isinstance(relations, dict) else len(relations)
        })
    except Exception as e:
        logger.error(f"获取跨系统关联失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/report', methods=['GET'])
def get_cross_system_report():
    """获取跨系统综合报表"""
    try:
        report = system_integration_hub.generate_cross_system_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        logger.error(f"生成综合报表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/report', methods=['POST'])
def submit_report():
    """提交报表数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        report_type = data.get('report_type', 'general')
        report_data = data.get('data', {})
        priority_str = data.get('priority', 'normal')
        
        try:
            priority = ReportPriority[priority_str.upper()]
        except KeyError:
            priority = ReportPriority.NORMAL
        
        enhanced_db_reporter.report_data_point(report_type, report_data, priority)
        
        return jsonify({
            'success': True,
            'message': f'报表已提交: {report_type}'
        })
    except Exception as e:
        logger.error(f"提交报表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/status', methods=['GET'])
def get_reporting_status():
    """获取数据库上报状态"""
    try:
        summary = enhanced_db_reporter.get_report_summary()
        
        return jsonify({
            'success': True,
            'status': summary
        })
    except Exception as e:
        logger.error(f"获取上报状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/enable', methods=['POST'])
def enable_reporting():
    """启用数据库上报"""
    try:
        enhanced_db_reporter.enable_reporting()
        return jsonify({
            'success': True,
            'message': '数据库上报已启用'
        })
    except Exception as e:
        logger.error(f"启用上报失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/disable', methods=['POST'])
def disable_reporting():
    """禁用数据库上报"""
    try:
        enhanced_db_reporter.disable_reporting()
        return jsonify({
            'success': True,
            'message': '数据库上报已禁用'
        })
    except Exception as e:
        logger.error(f"禁用上报失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/flush', methods=['POST'])
def flush_reports():
    """刷新所有报表数据"""
    try:
        enhanced_db_reporter.flush_all()
        return jsonify({
            'success': True,
            'message': '报表数据已刷新'
        })
    except Exception as e:
        logger.error(f"刷新报表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/data', methods=['GET'])
def get_reporting_data():
    """获取已上报的数据"""
    try:
        data_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        if not data_type:
            return jsonify({'success': False, 'error': '缺少数据类型参数'}), 400
        
        data = enhanced_db_reporter.get_data_by_type(data_type, limit)
        
        return jsonify({
            'success': True,
            'data_type': data_type,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"获取上报数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/reporting/batch', methods=['POST'])
def submit_batch_report():
    """批量提交报表"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        data_type = data.get('data_type')
        data_list = data.get('data_list', [])
        
        if not data_type or not data_list:
            return jsonify({'success': False, 'error': '缺少必需字段'}), 400
        
        enhanced_db_reporter.report_batch(data_type, data_list)
        
        return jsonify({
            'success': True,
            'message': f'已批量提交 {len(data_list)} 条 {data_type} 数据'
        })
    except Exception as e:
        logger.error(f"批量提交失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/metrics/system', methods=['POST'])
def report_system_metrics():
    """上报系统指标"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        enhanced_db_reporter.report_system_metrics(data)
        
        return jsonify({
            'success': True,
            'message': f'已上报 {len(data)} 个系统指标'
        })
    except Exception as e:
        logger.error(f"上报系统指标失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/health', methods=['POST'])
def report_health_analysis():
    """上报健康分析"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        enhanced_db_reporter.report_health_analysis(data)
        
        return jsonify({
            'success': True,
            'message': '健康分析已上报'
        })
    except Exception as e:
        logger.error(f"上报健康分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/anomaly', methods=['POST'])
def report_anomaly():
    """上报异常"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        enhanced_db_reporter.report_anomaly(data)
        
        return jsonify({
            'success': True,
            'message': '异常已上报'
        })
    except Exception as e:
        logger.error(f"上报异常失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/alert', methods=['POST'])
def report_alert():
    """上报告警"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        enhanced_db_reporter.report_alert(data)
        
        return jsonify({
            'success': True,
            'message': '告警已上报'
        })
    except Exception as e:
        logger.error(f"上报告警失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/cross-system-event', methods=['POST'])
def report_cross_system_event():
    """上报跨系统事件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据'}), 400
        
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not event_type:
            return jsonify({'success': False, 'error': '缺少事件类型'}), 400
        
        enhanced_db_reporter.report_cross_system_event(event_type, event_data)
        
        return jsonify({
            'success': True,
            'message': f'跨系统事件已上报: {event_type}'
        })
    except Exception as e:
        logger.error(f"上报跨系统事件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integration_bp.route('/comprehensive', methods=['GET'])
def get_comprehensive_status():
    """获取综合状态(整合+上报)"""
    try:
        integration_report = system_integration_hub.generate_cross_system_report()
        reporting_summary = enhanced_db_reporter.get_report_summary()
        
        return jsonify({
            'success': True,
            'status': {
                'integration': integration_report,
                'reporting': reporting_summary,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取综合状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
