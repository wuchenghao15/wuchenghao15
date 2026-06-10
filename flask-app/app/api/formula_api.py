# -*- coding: utf-8 -*-
"""数学公式API路由"""
from flask import Blueprint, request, jsonify
import json
import logging

from app.services.math_formula_service import formula_service

logger = logging.getLogger(__name__)

formula_api_bp = Blueprint('formula_api', __name__, url_prefix='/api/formulas')

@formula_api_bp.route('/', methods=['GET'])
def get_formulas():
    """获取公式列表"""
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        formula_type = request.args.get('type', '')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        formulas = formula_service.search_formulas(keyword, category, formula_type, limit, offset)
        count = formula_service.get_formula_count(category)
        
        return jsonify({
            'success': True,
            'data': formulas,
            'count': count,
            'message': '获取公式列表成功'
        })
    except Exception as e:
        logger.error(f"获取公式列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/<int:formula_id>', methods=['GET'])
def get_formula(formula_id):
    """获取单个公式"""
    try:
        formula = formula_service.get_formula(formula_id)
        if formula:
            return jsonify({'success': True, 'data': formula})
        return jsonify({'success': False, 'message': '公式不存在'}), 404
    except Exception as e:
        logger.error(f"获取公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/', methods=['POST'])
def add_formula():
    """添加公式"""
    try:
        data = request.get_json()
        
        required_fields = ['formula']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        formula_id = formula_service.add_formula(
            formula=data['formula'],
            latex=data.get('latex', ''),
            name=data.get('name', ''),
            category=data.get('category', ''),
            formula_type=data.get('formula_type', 'basic'),
            description=data.get('description', ''),
            variables=data.get('variables'),
            examples=data.get('examples'),
            derivation_steps=data.get('derivation_steps'),
            source=data.get('source', ''),
            difficulty_level=data.get('difficulty_level', 1)
        )
        
        return jsonify({
            'success': True,
            'data': {'id': formula_id},
            'message': '公式添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/<int:formula_id>', methods=['PUT'])
def update_formula(formula_id):
    """更新公式"""
    try:
        data = request.get_json()
        
        formula_service.update_formula(formula_id, **data)
        
        return jsonify({'success': True, 'message': '公式更新成功'})
    except Exception as e:
        logger.error(f"更新公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/<int:formula_id>', methods=['DELETE'])
def delete_formula(formula_id):
    """删除公式"""
    try:
        success = formula_service.delete_formula(formula_id)
        if success:
            return jsonify({'success': True, 'message': '公式删除成功'})
        return jsonify({'success': False, 'message': '公式不存在'}), 404
    except Exception as e:
        logger.error(f"删除公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = formula_service.get_all_categories()
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/categories', methods=['POST'])
def add_category():
    """添加分类"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'success': False, 'message': '缺少必要字段: name'}), 400
        
        category_id = formula_service.add_category(
            name=data['name'],
            parent_id=data.get('parent_id'),
            description=data.get('description', ''),
            color=data.get('color', '#667eea')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': category_id},
            'message': '分类添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加分类失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/import', methods=['POST'])
def import_formulas():
    """批量导入公式"""
    try:
        data = request.get_json()
        
        if not isinstance(data, list):
            return jsonify({'success': False, 'message': '数据格式错误，应为数组'}), 400
        
        imported_count = 0
        failed_count = 0
        
        for formula_data in data:
            try:
                formula_service.add_formula(
                    formula=formula_data.get('formula', ''),
                    latex=formula_data.get('latex', ''),
                    name=formula_data.get('name', ''),
                    category=formula_data.get('category', ''),
                    description=formula_data.get('description', ''),
                    variables=formula_data.get('variables'),
                    examples=formula_data.get('examples'),
                    source=formula_data.get('source', ''),
                    difficulty_level=formula_data.get('difficulty_level', 1)
                )
                imported_count += 1
            except Exception as e:
                logger.warning(f"导入公式失败: {formula_data.get('name', 'unknown')} - {str(e)}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'data': {
                'imported_count': imported_count,
                'failed_count': failed_count
            },
            'message': f'批量导入完成，成功: {imported_count}，失败: {failed_count}'
        })
    except Exception as e:
        logger.error(f"批量导入公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@formula_api_bp.route('/count', methods=['GET'])
def get_formula_count():
    """获取公式数量"""
    try:
        category = request.args.get('category', '')
        count = formula_service.get_formula_count(category)
        return jsonify({'success': True, 'data': {'count': count}})
    except Exception as e:
        logger.error(f"获取公式数量失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
