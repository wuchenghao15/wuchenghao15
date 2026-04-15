# MTSCOS AI Project 规则API
"""
规则API，提供RESTful接口来管理规则。
"""

from flask import Blueprint, request, jsonify
from app.rules import rule_system
from app.utils.logging import logger

# 创建规则API蓝图
rule_api = Blueprint('rule_api', __name__, url_prefix='/api/rules')


@rule_api.route('/', methods=['GET'])
def get_rules():
    """
    获取所有规则
    """
    try:
        # 获取查询参数
        rule_type = request.args.get('type')
        status = request.args.get('status')
        
        # 获取规则列表
        rules = rule_system.get_rules(rule_type)
        
        # 按状态过滤
        if status:
            rules = [rule for rule in rules if rule.get('status') == status]
        
        return jsonify({
            'success': True,
            'data': rules,
            'total': len(rules)
        }), 200
    except Exception as e:
        logger.error(f"获取规则列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取规则列表失败'
        }), 500


@rule_api.route('/<string:rule_id>', methods=['GET'])
def get_rule(rule_id):
    """
    获取指定规则
    """
    try:
        rule = rule_system.get_rule(rule_id)
        if rule:
            return jsonify({
                'success': True,
                'data': rule
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取规则失败'
        }), 500


@rule_api.route('/', methods=['POST'])
def create_rule():
    """
    创建新规则
    """
    try:
        # 获取请求数据
        rule_data = request.get_json()
        if not rule_data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 创建规则
        rule_id = rule_system.add_rule(rule_data)
        if rule_id:
            return jsonify({
                'success': True,
                'message': '规则创建成功',
                'rule_id': rule_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '规则创建失败'
            }), 400
    except Exception as e:
        logger.error(f"创建规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '创建规则失败'
        }), 500


@rule_api.route('/<string:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """
    更新规则
    """
    try:
        # 获取请求数据
        rule_data = request.get_json()
        if not rule_data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 更新规则
        success = rule_system.update_rule(rule_id, rule_data)
        if success:
            return jsonify({
                'success': True,
                'message': '规则更新成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '规则更新失败'
            }), 400
    except Exception as e:
        logger.error(f"更新规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '更新规则失败'
        }), 500


@rule_api.route('/<string:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """
    删除规则
    """
    try:
        # 删除规则
        success = rule_system.delete_rule(rule_id)
        if success:
            return jsonify({
                'success': True,
                'message': '规则删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '规则删除失败'
            }), 400
    except Exception as e:
        logger.error(f"删除规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除规则失败'
        }), 500


@rule_api.route('/execute/<string:rule_id>', methods=['POST'])
def execute_rule(rule_id):
    """
    执行指定规则
    """
    try:
        # 获取执行上下文
        context = request.get_json() or {}
        
        # 执行规则
        result = rule_system.execute_rule(rule_id, **context)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '规则执行成功'
        }), 200
    except Exception as e:
        logger.error(f"执行规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '执行规则失败'
        }), 500


@rule_api.route('/execute/type/<string:rule_type>', methods=['POST'])
def execute_rules_by_type(rule_type):
    """
    执行指定类型的所有规则
    """
    try:
        # 获取执行上下文
        context = request.get_json() or {}
        
        # 执行规则
        results = rule_system.execute_rules_by_type(rule_type, **context)
        
        return jsonify({
            'success': True,
            'data': results,
            'message': f'执行 {rule_type} 类型规则成功',
            'total_executed': len(results)
        }), 200
    except Exception as e:
        logger.error(f"执行规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '执行规则失败'
        }), 500


@rule_api.route('/types', methods=['GET'])
def get_rule_types():
    """
    获取所有规则类型
    """
    try:
        # 获取规则类型
        rule_types = rule_system.get_rule_manager().get_rule_types()
        
        return jsonify({
            'success': True,
            'data': rule_types
        }), 200
    except Exception as e:
        logger.error(f"获取规则类型失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取规则类型失败'
        }), 500


@rule_api.route('/count', methods=['GET'])
def get_rule_count():
    """
    获取规则统计信息
    """
    try:
        # 获取规则列表
        rules = rule_system.get_rules()
        
        # 统计信息
        total = len(rules)
        active_count = len([rule for rule in rules if rule.get('status') == 'active'])
        inactive_count = len([rule for rule in rules if rule.get('status') == 'inactive'])
        
        # 按类型统计
        type_count = {}
        for rule in rules:
            rule_type = rule.get('type', 'unknown')
            type_count[rule_type] = type_count.get(rule_type, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'active': active_count,
                'inactive': inactive_count,
                'by_type': type_count
            }
        }), 200
    except Exception as e:
        logger.error(f"获取规则统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取规则统计信息失败'
        }), 500


@rule_api.route('/refresh', methods=['POST'])
def refresh_rules():
    """
    刷新规则缓存
    """
    try:
        # 加载所有规则
        rule_system.get_rule_manager().load_all_rules()
        
        return jsonify({
            'success': True,
            'message': '规则刷新成功'
        }), 200
    except Exception as e:
        logger.error(f"刷新规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '刷新规则失败'
        }), 500
