#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理API接口
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.ai.settings_manager import (
    settings_manager,
    SettingScope,
    SettingType,
    SettingSyncStatus
)

logger = logging.getLogger('settings_api')

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = settings_manager.get_system_status()
        consistency = settings_manager.sync_manager.check_consistency()
        
        return jsonify({
            'success': True,
            'status': status,
            'consistency': consistency
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('', methods=['GET'])
def list_settings():
    """列出设置"""
    try:
        scope = request.args.get('scope')
        setting_type = request.args.get('type')
        
        scope_enum = None
        if scope:
            try:
                scope_enum = SettingScope(scope)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的作用域: {scope}'}), 400
        
        type_enum = None
        if setting_type:
            try:
                type_enum = SettingType(setting_type)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的类型: {setting_type}'}), 400
        
        settings = settings_manager.list_settings(scope_enum, type_enum)
        
        return jsonify({
            'success': True,
            'settings': settings,
            'count': len(settings)
        })
    except Exception as e:
        logger.error(f"列出设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['GET'])
def get_setting(key):
    """获取设置"""
    try:
        setting = settings_manager.get_setting(key)
        
        if not setting:
            return jsonify({'success': False, 'error': '设置不存在'}), 404
        
        return jsonify({'success': True, 'setting': setting.to_dict()})
    except Exception as e:
        logger.error(f"获取设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['PUT'])
def update_setting(key):
    """更新设置"""
    try:
        data = request.get_json() or {}
        value = data.get('value')
        user_id = data.get('user_id')
        
        if value is None:
            return jsonify({'success': False, 'error': '缺少 value 参数'}), 400
        
        success = settings_manager.set_setting(key, value, user_id)
        
        if success:
            setting = settings_manager.get_setting(key)
            return jsonify({
                'success': True,
                'setting': setting.to_dict(),
                'message': '设置更新成功'
            })
        else:
            return jsonify({'success': False, 'error': '设置更新失败'}), 404
            
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"更新设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('', methods=['POST'])
def create_setting():
    """创建设置"""
    try:
        data = request.get_json() or {}
        
        key = data.get('key')
        name = data.get('name')
        setting_type = data.get('type')
        
        if not key or not name or not setting_type:
            return jsonify({'success': False, 'error': '缺少 key、name 或 type 参数'}), 400
        
        try:
            type_enum = SettingType(setting_type)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的类型: {setting_type}'}), 400
        
        kwargs = {}
        if 'scope' in data:
            try:
                kwargs['scope'] = SettingScope(data['scope'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的作用域: {data["scope"]}'}), 400
        if 'default_value' in data:
            kwargs['default_value'] = data['default_value']
        if 'description' in data:
            kwargs['description'] = data['description']
        if 'options' in data:
            kwargs['options'] = data['options']
        if 'metadata' in data:
            kwargs['metadata'] = data['metadata']
        
        success = settings_manager.create_setting(key, name, type_enum, **kwargs)
        
        if success:
            return jsonify({'success': True, 'message': '设置创建成功'})
        else:
            return jsonify({'success': False, 'error': '设置已存在'}), 409
            
    except Exception as e:
        logger.error(f"创建设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/<key>', methods=['DELETE'])
def delete_setting(key):
    """删除设置"""
    try:
        success = settings_manager.delete_setting(key)
        
        if success:
            return jsonify({'success': True, 'message': '设置删除成功'})
        else:
            return jsonify({'success': False, 'error': '设置删除失败'}), 404
            
    except Exception as e:
        logger.error(f"删除设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/sync', methods=['POST'])
def force_sync():
    """强制同步"""
    try:
        data = request.get_json() or {}
        key = data.get('key')
        
        success = settings_manager.sync_manager.force_sync(key)
        
        if success:
            return jsonify({'success': True, 'message': '同步成功'})
        else:
            return jsonify({'success': False, 'error': '同步失败'}), 400
            
    except Exception as e:
        logger.error(f"强制同步失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """获取同步状态"""
    try:
        status = settings_manager.get_system_status()
        consistency = settings_manager.sync_manager.check_consistency()
        
        return jsonify({
            'success': True,
            'last_sync': status.get('last_sync'),
            'pending_sync': status.get('pending_sync'),
            'synced': status.get('synced'),
            'conflict': status.get('conflict'),
            'consistency': consistency
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/consistency/check', methods=['GET'])
def check_consistency():
    """检查数据一致性"""
    try:
        result = settings_manager.sync_manager.check_consistency()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"检查一致性失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/consistency/resolve', methods=['POST'])
def resolve_conflicts():
    """解决冲突"""
    try:
        result = settings_manager.sync_manager.resolve_conflicts()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"解决冲突失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/ai/recommendations', methods=['GET'])
def get_ai_recommendations():
    """获取AI推荐"""
    try:
        recommendations = settings_manager.get_ai_recommendations()
        analysis = settings_manager.ai_optimizer.analyze_settings()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"获取AI推荐失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/ai/apply', methods=['POST'])
def apply_ai_recommendations():
    """应用AI推荐"""
    try:
        recommendations = settings_manager.apply_ai_recommendations()
        
        return jsonify({
            'success': True,
            'applied': recommendations,
            'count': len(recommendations),
            'message': f'已应用 {len(recommendations)} 个AI推荐'
        })
    except Exception as e:
        logger.error(f"应用AI推荐失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/ai/analyze', methods=['GET'])
def analyze_settings():
    """分析设置"""
    try:
        analysis = settings_manager.ai_optimizer.analyze_settings()
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        logger.error(f"分析设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/history', methods=['GET'])
def get_history():
    """获取变更日志"""
    try:
        limit = int(request.args.get('limit', 50))
        history = settings_manager.get_change_log(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取变更日志失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/scopes', methods=['GET'])
def get_scopes():
    """获取作用域列表"""
    try:
        scopes = [
            {'value': scope.value, 'name': scope.name}
            for scope in SettingScope
        ]
        return jsonify({'success': True, 'scopes': scopes})
    except Exception as e:
        logger.error(f"获取作用域失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/types', methods=['GET'])
def get_types():
    """获取类型列表"""
    try:
        types = [
            {'value': t.value, 'name': t.name}
            for t in SettingType
        ]
        return jsonify({'success': True, 'types': types})
    except Exception as e:
        logger.error(f"获取类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/sync/enable', methods=['POST'])
def enable_sync():
    """启用同步"""
    try:
        settings_manager.sync_manager.enabled = True
        return jsonify({'success': True, 'message': '同步已启用'})
    except Exception as e:
        logger.error(f"启用同步失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/sync/disable', methods=['POST'])
def disable_sync():
    """禁用同步"""
    try:
        settings_manager.sync_manager.enabled = False
        return jsonify({'success': True, 'message': '同步已禁用'})
    except Exception as e:
        logger.error(f"禁用同步失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/ai/enable', methods=['POST'])
def enable_ai():
    """启用AI优化"""
    try:
        settings_manager.ai_optimizer.enabled = True
        return jsonify({'success': True, 'message': 'AI优化已启用'})
    except Exception as e:
        logger.error(f"启用AI优化失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/ai/disable', methods=['POST'])
def disable_ai():
    """禁用AI优化"""
    try:
        settings_manager.ai_optimizer.enabled = False
        return jsonify({'success': True, 'message': 'AI优化已禁用'})
    except Exception as e:
        logger.error(f"禁用AI优化失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
