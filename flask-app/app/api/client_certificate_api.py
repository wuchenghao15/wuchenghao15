#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端证书管理API接口
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.ai.client_certificate_manager import (
    client_certificate_manager,
    CertificateStatus,
    ExitType,
    OperationType
)

logger = logging.getLogger('client_certificate_api')

cert_bp = Blueprint('client_certificate', __name__, url_prefix='/api/certificate')


@cert_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = client_certificate_manager.get_system_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/certificates', methods=['GET'])
def list_certificates():
    """列出所有证书"""
    try:
        certificates = [
            cert.to_dict() for cert in client_certificate_manager.certificates.values()
        ]
        return jsonify({
            'success': True,
            'certificates': certificates,
            'count': len(certificates)
        })
    except Exception as e:
        logger.error(f"列出证书失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/certificates/<client_id>', methods=['GET'])
def get_certificate(client_id):
    """获取客户端证书"""
    try:
        cert = client_certificate_manager.get_certificate(client_id)
        
        if not cert:
            return jsonify({'success': False, 'error': '证书不存在'}), 404
        
        return jsonify({'success': True, 'certificate': cert.to_dict()})
    except Exception as e:
        logger.error(f"获取证书失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/certificates', methods=['POST'])
def issue_certificate():
    """发放证书"""
    try:
        data = request.get_json() or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': '缺少 client_id 参数'}), 400
        
        cert = client_certificate_manager.issue_certificate(client_id)
        
        if cert:
            return jsonify({
                'success': True,
                'certificate': cert.to_dict(),
                'message': '证书发放成功'
            })
        else:
            return jsonify({'success': False, 'error': '证书发放失败'}), 500
            
    except Exception as e:
        logger.error(f"发放证书失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/certificates/<client_id>/revoke', methods=['POST'])
def revoke_certificate(client_id):
    """吊销证书"""
    try:
        success = client_certificate_manager.revoke_certificate(client_id)
        
        if success:
            return jsonify({'success': True, 'message': '证书已吊销'})
        else:
            return jsonify({'success': False, 'error': '吊销失败'}), 404
            
    except Exception as e:
        logger.error(f"吊销证书失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/certificates/<client_id>/renew', methods=['POST'])
def renew_certificate(client_id):
    """续期证书"""
    try:
        success = client_certificate_manager.renew_certificate(client_id)
        
        if success:
            return jsonify({'success': True, 'message': '证书已续期'})
        else:
            return jsonify({'success': False, 'error': '续期失败'}), 404
            
    except Exception as e:
        logger.error(f"续期证书失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions', methods=['POST'])
def create_session():
    """创建会话"""
    try:
        data = request.get_json() or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': '缺少 client_id 参数'}), 400
        
        session = client_certificate_manager.create_session(client_id)
        
        if session:
            return jsonify({
                'success': True,
                'session': session.to_dict(),
                'message': '会话创建成功'
            })
        else:
            return jsonify({'success': False, 'error': '会话创建失败'}), 500
            
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话"""
    try:
        session = client_certificate_manager.get_session(session_id)
        
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        return jsonify({'success': True, 'session': session.to_dict()})
    except Exception as e:
        logger.error(f"获取会话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """关闭会话"""
    try:
        data = request.get_json() or {}
        
        exit_type_str = data.get('exit_type', 'normal')
        reason = data.get('reason', '')
        
        try:
            exit_type = ExitType(exit_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的退出类型: {exit_type_str}'}), 400
        
        package = client_certificate_manager.close_session(session_id, exit_type, reason)
        
        if package:
            return jsonify({
                'success': True,
                'package': package,
                'message': '会话已关闭并打包上传'
            })
        else:
            return jsonify({'success': False, 'error': '会话关闭失败'}), 404
            
    except Exception as e:
        logger.error(f"关闭会话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>/activity', methods=['POST'])
def update_activity(session_id):
    """更新会话活动"""
    try:
        session = client_certificate_manager.get_session(session_id)
        
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        session.update_activity()
        client_certificate_manager.sessions[session_id] = session.to_dict()
        client_certificate_manager._save_data()
        
        return jsonify({'success': True, 'message': '活动时间已更新'})
    except Exception as e:
        logger.error(f"更新活动失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>/log', methods=['POST'])
def add_log(session_id):
    """添加日志"""
    try:
        data = request.get_json() or {}
        level = data.get('level', 'info')
        message = data.get('message', '')
        context = data.get('context', {})
        
        session = client_certificate_manager.get_session(session_id)
        
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        log_method = getattr(session.info_container.log_unit, level.lower(), None)
        if log_method:
            log_method(message, context)
            client_certificate_manager.sessions[session_id] = session.to_dict()
            client_certificate_manager._save_data()
        
        return jsonify({'success': True, 'message': '日志已添加'})
    except Exception as e:
        logger.error(f"添加日志失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>/operation', methods=['POST'])
def record_operation(session_id):
    """记录操作"""
    try:
        data = request.get_json() or {}
        op_type_str = data.get('type')
        resource = data.get('resource', '')
        details = data.get('details', {})
        
        if not op_type_str:
            return jsonify({'success': False, 'error': '缺少 type 参数'}), 400
        
        try:
            op_type = OperationType(op_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的操作类型: {op_type_str}'}), 400
        
        session = client_certificate_manager.get_session(session_id)
        
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        session.info_container.operation_unit.record_operation(op_type, resource, details)
        client_certificate_manager.sessions[session_id] = session.to_dict()
        client_certificate_manager._save_data()
        
        return jsonify({'success': True, 'message': '操作已记录'})
    except Exception as e:
        logger.error(f"记录操作失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/sessions/<session_id>/record', methods=['POST'])
def update_record(session_id):
    """更新记录单元"""
    try:
        data = request.get_json() or {}
        
        session = client_certificate_manager.get_session(session_id)
        
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        record_unit = session.info_container.record_unit
        
        if 'user_info' in data:
            record_unit.update_user_info(data['user_info'])
        if 'device_info' in data:
            record_unit.update_device_info(data['device_info'])
        if 'session_info' in data:
            record_unit.update_session_info(data['session_info'])
        if 'connection_info' in data:
            record_unit.update_connection_info(data['connection_info'])
        
        client_certificate_manager.sessions[session_id] = session.to_dict()
        client_certificate_manager._save_data()
        
        return jsonify({'success': True, 'message': '记录已更新'})
    except Exception as e:
        logger.error(f"更新记录失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/client/<client_id>', methods=['GET'])
def get_client_info(client_id):
    """获取客户端完整信息"""
    try:
        info = client_certificate_manager.get_client_info(client_id)
        return jsonify({'success': True, 'client_info': info})
    except Exception as e:
        logger.error(f"获取客户端信息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/packages', methods=['GET'])
def list_packages():
    """列出所有包"""
    try:
        packages = list(client_certificate_manager.packages.values())
        return jsonify({
            'success': True,
            'packages': packages,
            'count': len(packages)
        })
    except Exception as e:
        logger.error(f"列出包失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/exit-types', methods=['GET'])
def get_exit_types():
    """获取退出类型"""
    try:
        exit_types = [
            {'value': et.value, 'name': et.name}
            for et in ExitType
        ]
        return jsonify({'success': True, 'exit_types': exit_types})
    except Exception as e:
        logger.error(f"获取退出类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@cert_bp.route('/operation-types', methods=['GET'])
def get_operation_types():
    """获取操作类型"""
    try:
        op_types = [
            {'value': ot.value, 'name': ot.name}
            for ot in OperationType
        ]
        return jsonify({'success': True, 'operation_types': op_types})
    except Exception as e:
        logger.error(f"获取操作类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
