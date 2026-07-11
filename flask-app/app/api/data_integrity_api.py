# -*- coding: utf-8 -*-
"""
数据完整性与并发控制API
"""

from flask import Blueprint, request, jsonify, session
import logging
import json
from app.utils.data_integrity_center import (
    data_integrity_center,
    DataValidator,
    LockType,
    LockLevel
)
from app.utils.logging import logger

data_integrity_api = Blueprint('data_integrity_api', __name__)


@data_integrity_api.route('/data-integrity/status', methods=['GET'])
def get_integrity_status():
    """获取数据完整性系统状态"""
    try:
        status = data_integrity_center.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取数据完整性状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/validate', methods=['POST'])
def validate_data():
    """校验数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        validate_data = data.get('data', {})
        rules = data.get('rules', {})
        
        is_valid, errors = data_integrity_center.validate_data(validate_data, rules)
        
        return jsonify({
            'success': True,
            'data': {
                'valid': is_valid,
                'errors': errors,
                'error_count': len(errors)
            }
        })
    except Exception as e:
        logger.error(f"数据校验失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/validate/fields', methods=['GET'])
def get_validation_field_types():
    """获取支持的校验字段类型"""
    try:
        field_types = [
            {'type': 'required', 'description': '必填校验'},
            {'type': 'type', 'description': '类型校验', 'params': ['value: string/int/float/bool/list/dict']},
            {'type': 'length', 'description': '长度校验', 'params': ['min', 'max']},
            {'type': 'range', 'description': '范围校验', 'params': ['min', 'max']},
            {'type': 'pattern', 'description': '正则校验', 'params': ['value: regex_pattern']},
            {'type': 'enum', 'description': '枚举校验', 'params': ['value: list']},
            {'type': 'email', 'description': '邮箱格式校验'},
            {'type': 'phone', 'description': '手机号校验', 'params': ['region: cn/us/intl']},
            {'type': 'url', 'description': 'URL格式校验'},
            {'type': 'sql_safe', 'description': 'SQL注入安全校验'},
            {'type': 'xss_safe', 'description': 'XSS安全校验'},
            {'type': 'custom', 'description': '自定义校验', 'params': ['validator: function']},
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'field_types': field_types,
                'total': len(field_types)
            }
        })
    except Exception as e:
        logger.error(f"获取校验字段类型失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/uniqueness/check', methods=['POST'])
def check_uniqueness():
    """检查数据唯一性"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        table_name = data.get('table_name')
        fields = data.get('fields', {})
        exclude_id = data.get('exclude_id')
        
        if not table_name or not fields:
            return jsonify({
                'success': False,
                'message': '缺少表名或字段'
            }), 400
        
        is_unique, message = data_integrity_center.check_uniqueness(
            table_name, fields, exclude_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'unique': is_unique,
                'message': message
            }
        })
    except Exception as e:
        logger.error(f"检查唯一性失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/uniqueness/constraints', methods=['GET'])
def get_unique_constraints():
    """获取唯一性约束列表"""
    try:
        table_name = request.args.get('table_name')
        constraints = data_integrity_center.unique_manager.get_constraints(table_name)
        
        return jsonify({
            'success': True,
            'data': {
                'constraints': constraints,
                'total': len(constraints)
            }
        })
    except Exception as e:
        logger.error(f"获取唯一性约束失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/uniqueness/constraints', methods=['POST'])
def register_unique_constraint():
    """注册唯一性约束"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        table_name = data.get('table_name')
        fields = data.get('fields', [])
        constraint_name = data.get('constraint_name')
        
        if not table_name or not fields:
            return jsonify({
                'success': False,
                'message': '缺少表名或字段'
            }), 400
        
        constraint_id = data_integrity_center.unique_manager.register_constraint(
            table_name, fields, constraint_name
        )
        
        return jsonify({
            'success': True,
            'data': {
                'constraint_id': constraint_id,
                'table_name': table_name,
                'fields': fields
            }
        })
    except Exception as e:
        logger.error(f"注册唯一性约束失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/locks', methods=['GET'])
def get_locks_status():
    """获取锁状态"""
    try:
        lock_manager = data_integrity_center.concurrency_controller.get_lock_manager()
        lock_info = lock_manager.get_lock_info()
        
        active_locks = sum(
            1 for info in lock_info.values() 
            if info.get('holders', [])
        )
        
        return jsonify({
            'success': True,
            'data': {
                'total_locks': len(lock_info),
                'active_locks': active_locks,
                'locks': lock_info,
                'active_transactions': data_integrity_center.concurrency_controller.get_active_transactions()
            }
        })
    except Exception as e:
        logger.error(f"获取锁状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/locks/acquire', methods=['POST'])
def acquire_lock():
    """获取锁"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        lock_key = data.get('lock_key')
        lock_type_str = data.get('lock_type', 'exclusive')
        timeout = data.get('timeout', 30.0)
        
        if not lock_key:
            return jsonify({
                'success': False,
                'message': '缺少锁键'
            }), 400
        
        lock_type = LockType.EXCLUSIVE if lock_type_str == 'exclusive' else LockType.SHARED
        
        success, lock_id = data_integrity_center.acquire_lock(
            lock_key, lock_type, timeout
        )
        
        return jsonify({
            'success': True,
            'data': {
                'acquired': success,
                'lock_id': lock_id,
                'lock_key': lock_key
            }
        })
    except Exception as e:
        logger.error(f"获取锁失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/locks/release', methods=['POST'])
def release_lock():
    """释放锁"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        lock_key = data.get('lock_key')
        lock_id = data.get('lock_id')
        
        if not lock_key or not lock_id:
            return jsonify({
                'success': False,
                'message': '缺少锁键或锁ID'
            }), 400
        
        success = data_integrity_center.release_lock(lock_key, lock_id)
        
        return jsonify({
            'success': True,
            'data': {
                'released': success,
                'lock_key': lock_key
            }
        })
    except Exception as e:
        logger.error(f"释放锁失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/locks/deadlocks', methods=['GET'])
def check_deadlocks():
    """检查死锁"""
    try:
        lock_manager = data_integrity_center.concurrency_controller.get_lock_manager()
        deadlocks = lock_manager.check_deadlocks()
        
        return jsonify({
            'success': True,
            'data': {
                'deadlocks': deadlocks,
                'count': len(deadlocks)
            }
        })
    except Exception as e:
        logger.error(f"检查死锁失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/locks/cleanup', methods=['POST'])
def cleanup_stale_locks():
    """清理过期锁"""
    try:
        data = request.get_json() or {}
        max_age = data.get('max_age', 3600)
        
        lock_manager = data_integrity_center.concurrency_controller.get_lock_manager()
        cleaned = lock_manager.cleanup_stale_locks(max_age)
        
        return jsonify({
            'success': True,
            'data': {
                'cleaned_count': cleaned
            }
        })
    except Exception as e:
        logger.error(f"清理过期锁失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/audit/logs', methods=['GET'])
def get_audit_logs():
    """获取审计日志"""
    try:
        table_name = request.args.get('table_name')
        operation = request.args.get('operation')
        limit = int(request.args.get('limit', 100))
        
        logs = data_integrity_center.audit_monitor.get_audit_log(
            table_name=table_name,
            operation=operation,
            limit=limit
        )
        
        serializable_logs = []
        for log in logs:
            log_copy = dict(log)
            log_copy['timestamp'] = log_copy['timestamp'].isoformat()
            serializable_logs.append(log_copy)
        
        return jsonify({
            'success': True,
            'data': {
                'logs': serializable_logs,
                'total': len(serializable_logs)
            }
        })
    except Exception as e:
        logger.error(f"获取审计日志失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/audit/violations', methods=['GET'])
def get_violation_stats():
    """获取违规统计"""
    try:
        stats = data_integrity_center.audit_monitor.get_violation_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'violations': stats,
                'total_types': len(stats),
                'total_violations': sum(stats.values())
            }
        })
    except Exception as e:
        logger.error(f"获取违规统计失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/audit/statistics', methods=['GET'])
def get_audit_statistics():
    """获取审计统计"""
    try:
        stats = data_integrity_center.audit_monitor.get_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取审计统计失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/sanitize', methods=['POST'])
def sanitize_data():
    """清理数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        input_data = data.get('data', '')
        max_length = data.get('max_length', 1000)
        sanitize_type = data.get('type', 'string')
        
        if sanitize_type == 'string':
            result = DataValidator.sanitize_string(input_data, max_length)
        elif sanitize_type == 'sql_identifier':
            result = DataValidator.sanitize_sql_identifier(input_data)
        else:
            result = input_data
        
        return jsonify({
            'success': True,
            'data': {
                'original': input_data,
                'sanitized': result,
                'type': sanitize_type
            }
        })
    except Exception as e:
        logger.error(f"清理数据失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@data_integrity_api.route('/data-integrity/test', methods=['GET'])
def test_integrity_system():
    """测试数据完整性系统"""
    try:
        # 测试数据校验
        test_data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'phone': '13800138000',
            'age': 25
        }
        
        test_rules = {
            'username': [
                {'type': 'required', 'message': '用户名不能为空'},
                {'type': 'length', 'min': 3, 'max': 20, 'message': '用户名长度应为3-20'}
            ],
            'email': [
                {'type': 'email', 'message': '邮箱格式不正确'}
            ],
            'phone': [
                {'type': 'phone', 'region': 'cn', 'message': '手机号格式不正确'}
            ],
            'age': [
                {'type': 'range', 'min': 18, 'max': 100, 'message': '年龄应在18-100之间'}
            ]
        }
        
        is_valid, errors = data_integrity_center.validate_data(test_data, test_rules)
        
        # 测试锁
        lock_success, lock_id = data_integrity_center.acquire_lock('test_lock_123', timeout=5)
        if lock_success and lock_id:
            data_integrity_center.release_lock('test_lock_123', lock_id)
        
        # 注册测试约束
        constraint_id = data_integrity_center.unique_manager.register_constraint(
            'test_table', ['username', 'email']
        )
        
        status = data_integrity_center.get_status()
        
        return jsonify({
            'success': True,
            'data': {
                'validation': {
                    'valid': is_valid,
                    'errors': errors
                },
                'lock_test': lock_success,
                'constraint_test': constraint_id,
                'status': status
            }
        })
    except Exception as e:
        logger.error(f"测试数据完整性系统失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
