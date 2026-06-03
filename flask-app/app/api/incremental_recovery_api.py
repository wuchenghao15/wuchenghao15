#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量恢复镜像系统API接口
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.ai.incremental_recovery_system import (
    incremental_recovery_system,
    BackupType,
    MirrorStatus
)

logger = logging.getLogger('incremental_recovery_api')

recovery_bp = Blueprint('incremental_recovery', __name__, url_prefix='/api/recovery')


@recovery_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = incremental_recovery_system.get_system_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/mirrors', methods=['GET'])
def list_mirrors():
    """列出所有镜像"""
    try:
        backup_type = request.args.get('type')
        status = request.args.get('status')
        
        bt_enum = None
        if backup_type:
            try:
                bt_enum = BackupType(backup_type)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的备份类型: {backup_type}'}), 400
        
        st_enum = None
        if status:
            try:
                st_enum = MirrorStatus(status)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的状态: {status}'}), 400
        
        mirrors = incremental_recovery_system.list_mirrors(bt_enum, st_enum)
        
        return jsonify({
            'success': True,
            'mirrors': mirrors,
            'count': len(mirrors)
        })
    except Exception as e:
        logger.error(f"列出镜像失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/mirrors/<mirror_id>', methods=['GET'])
def get_mirror_info(mirror_id):
    """获取镜像详情"""
    try:
        info = incremental_recovery_system.get_mirror_info(mirror_id)
        
        if not info:
            return jsonify({'success': False, 'error': '镜像不存在'}), 404
        
        return jsonify({
            'success': True,
            'mirror': info
        })
    except Exception as e:
        logger.error(f"获取镜像详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/backup/full', methods=['POST'])
def create_full_backup():
    """创建完整备份"""
    try:
        data = request.get_json() or {}
        
        source_paths = data.get('source_paths', [])
        if not source_paths:
            return jsonify({'success': False, 'error': '缺少 source_paths 参数'}), 400
        
        description = data.get('description', '')
        tags = data.get('tags', [])
        exclude_patterns = data.get('exclude_patterns', [])
        
        mirror_id = incremental_recovery_system.create_full_backup(
            source_paths=source_paths,
            description=description,
            tags=tags,
            exclude_patterns=exclude_patterns
        )
        
        if mirror_id:
            return jsonify({
                'success': True,
                'mirror_id': mirror_id,
                'message': '完整备份创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '备份创建失败'
            }), 500
            
    except Exception as e:
        logger.error(f"创建完整备份失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/backup/incremental', methods=['POST'])
def create_incremental_backup():
    """创建增量备份"""
    try:
        data = request.get_json() or {}
        
        source_paths = data.get('source_paths', [])
        if not source_paths:
            return jsonify({'success': False, 'error': '缺少 source_paths 参数'}), 400
        
        base_mirror_id = data.get('base_mirror_id')
        description = data.get('description', '')
        tags = data.get('tags', [])
        exclude_patterns = data.get('exclude_patterns', [])
        
        mirror_id = incremental_recovery_system.create_incremental_backup(
            source_paths=source_paths,
            base_mirror_id=base_mirror_id,
            description=description,
            tags=tags,
            exclude_patterns=exclude_patterns
        )
        
        if mirror_id:
            return jsonify({
                'success': True,
                'mirror_id': mirror_id,
                'message': '增量备份创建成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '增量备份创建失败'
            }), 500
            
    except Exception as e:
        logger.error(f"创建增量备份失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/restore/<mirror_id>', methods=['POST'])
def restore_mirror(mirror_id):
    """恢复镜像"""
    try:
        data = request.get_json() or {}
        restore_path = data.get('restore_path')
        
        success = incremental_recovery_system.restore_mirror(
            mirror_id=mirror_id,
            restore_path=restore_path
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '镜像恢复成功',
                'mirror_id': mirror_id
            })
        else:
            return jsonify({
                'success': False,
                'error': '镜像恢复失败'
            }), 500
            
    except Exception as e:
        logger.error(f"恢复镜像失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/validate/<mirror_id>', methods=['POST'])
def validate_mirror(mirror_id):
    """验证镜像完整性"""
    try:
        validation = incremental_recovery_system.validate_mirror(mirror_id)
        
        return jsonify({
            'success': True,
            'validation': validation
        })
    except Exception as e:
        logger.error(f"验证镜像失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/recovery-chain/<mirror_id>', methods=['GET'])
def get_recovery_chain(mirror_id):
    """获取恢复链"""
    try:
        chain = incremental_recovery_system.get_recovery_chain(mirror_id)
        
        return jsonify({
            'success': True,
            'chain': chain,
            'chain_length': len(chain)
        })
    except Exception as e:
        logger.error(f"获取恢复链失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/cleanup', methods=['POST'])
def cleanup_old_mirrors():
    """清理过期镜像"""
    try:
        result = incremental_recovery_system.cleanup_old_mirrors()
        
        return jsonify({
            'success': True,
            'cleanup_result': result
        })
    except Exception as e:
        logger.error(f"清理镜像失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@recovery_bp.route('/backup-types', methods=['GET'])
def get_backup_types():
    """获取支持的备份类型"""
    try:
        types = [
            {
                'value': bt.value,
                'name': bt.name,
                'description': get_backup_type_description(bt)
            }
            for bt in BackupType
        ]
        
        return jsonify({
            'success': True,
            'backup_types': types
        })
    except Exception as e:
        logger.error(f"获取备份类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_backup_type_description(backup_type: BackupType) -> str:
    """获取备份类型描述"""
    descriptions = {
        BackupType.FULL: '完整备份:备份所有文件',
        BackupType.INCREMENTAL: '增量备份:仅备份自上次备份后变更的文件',
        BackupType.DIFFERENTIAL: '差异备份:备份自上次完整备份后变更的文件'
    }
    return descriptions.get(backup_type, '未知类型')
