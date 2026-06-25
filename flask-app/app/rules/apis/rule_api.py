import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
规则管理API - 提供完整的CRUD操作
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any, List

rule_api = Blueprint('rule_api', __name__, url_prefix='/api/rules')

try:
    from app.rules.managers.rule_manager import RuleManager
    from app.rules.engines.rule_engine import RuleEngine
    
    rule_manager = RuleManager()
    rule_engine = RuleEngine(rule_manager)
except ImportError:
    rule_manager = None
    rule_engine = None
    logger.info("警告: 规则模块未找到")

@rule_api.route('/', methods=['GET'])
def get_rules():
    """获取规则列表"""
    try:
        rule_type = request.args.get('type')
        status = request.args.get('status')
        min_priority = request.args.get('min_priority', type=int)
        max_priority = request.args.get('max_priority', type=int)

        rules = []
        if rule_manager:
            rules = rule_manager.get_rules(rule_type)
            
            if status:
                rules = [r for r in rules if r.get('status') == status]
            
            if min_priority is not None:
                rules = [r for r in rules if r.get('priority', 1) >= min_priority]
            
            if max_priority is not None:
                rules = [r for r in rules if r.get('priority', 1) <= max_priority]

        return jsonify({
            'success': True,
            'data': rules,
            'count': len(rules)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """获取单个规则"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        rule = rule_manager.get_rule(rule_id)
        
        if not rule:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        return jsonify({
            'success': True,
            'data': rule
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/', methods=['POST'])
def create_rule():
    """创建规则"""
    try:
        data = request.get_json() or {}
        
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        required_fields = ['name', 'type', 'description', 'conditions', 'actions']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'缺少必要字段: {", ".join(missing_fields)}'
            }), 400

        rule_id = rule_manager.add_rule(data)

        return jsonify({
            'success': True,
            'message': '规则创建成功',
            'rule_id': rule_id
        }), 201
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """更新规则"""
    try:
        data = request.get_json() or {}
        
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        success = rule_manager.update_rule(rule_id, data)
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在或更新失败'}), 404

        return jsonify({
            'success': True,
            'message': '规则更新成功'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """删除规则"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        success = rule_manager.delete_rule(rule_id)
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        return jsonify({
            'success': True,
            'message': '规则删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>/enable', methods=['POST'])
def enable_rule(rule_id):
    """启用规则"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        success = rule_manager.enable_rule(rule_id)
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        return jsonify({
            'success': True,
            'message': '规则已启用'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>/disable', methods=['POST'])
def disable_rule(rule_id):
    """禁用规则"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        success = rule_manager.disable_rule(rule_id)
        
        if not success:
            return jsonify({'success': False, 'error': '规则不存在'}), 404

        return jsonify({
            'success': True,
            'message': '规则已禁用'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>/execute', methods=['POST'])
def execute_rule(rule_id):
    """执行规则"""
    try:
        if not rule_engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'}), 500

        context = request.get_json() or {}
        result = rule_engine.execute_rule(rule_id, **context)

        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/execute/all', methods=['POST'])
def execute_all_rules():
    """执行所有激活的规则"""
    try:
        if not rule_engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'}), 500

        context = request.get_json() or {}
        results = rule_engine.execute_all_rules(**context)

        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/execute/type/<rule_type>', methods=['POST'])
def execute_rules_by_type(rule_type):
    """执行指定类型的规则"""
    try:
        if not rule_engine:
            return jsonify({'success': False, 'error': '规则引擎未初始化'}), 500

        context = request.get_json() or {}
        results = rule_engine.execute_rules_by_type(rule_type, **context)

        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/conflicts', methods=['GET'])
def get_conflicts():
    """检测规则冲突"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        conflicts = rule_manager.find_conflicts()

        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'count': len(conflicts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/conflicts/resolve', methods=['POST'])
def resolve_conflicts():
    """解决规则冲突"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        conflicts = rule_manager.find_conflicts()
        
        if not conflicts:
            return jsonify({
                'success': True,
                'message': '没有冲突需要解决',
                'resolved': []
            })

        resolved = rule_manager.resolve_conflicts(conflicts)

        return jsonify({
            'success': True,
            'message': f'已解决 {len(resolved)} 个冲突',
            'resolved': resolved
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>/versions', methods=['GET'])
def get_rule_versions(rule_id):
    """获取规则版本历史"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        versions = rule_manager.get_rule_versions(rule_id)

        return jsonify({
            'success': True,
            'versions': versions,
            'count': len(versions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/<rule_id>/versions/<version>', methods=['POST'])
def restore_rule_version(rule_id, version):
    """恢复规则到指定版本"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        success = rule_manager.restore_rule_version(rule_id, version)
        
        if not success:
            return jsonify({'success': False, 'error': '版本不存在'}), 404

        return jsonify({
            'success': True,
            'message': f'规则已恢复到版本 {version}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/stats', methods=['GET'])
def get_stats():
    """获取规则统计信息"""
    try:
        if not rule_manager or not rule_engine:
            return jsonify({'success': False, 'error': '规则模块未初始化'}), 500

        manager_stats = rule_manager.get_stats()
        engine_stats = rule_engine.get_stats()

        return jsonify({
            'success': True,
            'data': {
                'manager': manager_stats,
                'engine': engine_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rule_api.route('/types', methods=['GET'])
def get_rule_types():
    """获取规则类型列表"""
    try:
        if not rule_manager:
            return jsonify({'success': False, 'error': '规则管理器未初始化'}), 500

        types = rule_manager.get_rule_types()

        return jsonify({
            'success': True,
            'types': types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500