#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业技能AI系统API接口
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.ai.skill_ai_system import (
    skill_ai_system,
    SkillCategory,
    SkillStatus,
    SkillLevel
)

logger = logging.getLogger('skill_ai_api')

skill_bp = Blueprint('skill_ai', __name__, url_prefix='/api/skills')


@skill_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        stats = skill_ai_system.get_skill_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('', methods=['GET'])
def list_skills():
    """列出技能"""
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        level = request.args.get('level')
        
        cat_enum = None
        if category:
            try:
                cat_enum = SkillCategory(category)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的分类: {category}'}), 400
        
        status_enum = None
        if status:
            try:
                status_enum = SkillStatus(status)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的状态: {status}'}), 400
        
        level_enum = None
        if level:
            try:
                level_enum = SkillLevel(level)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的级别: {level}'}), 400
        
        skills = skill_ai_system.list_skills(cat_enum, status_enum, level_enum)
        
        return jsonify({
            'success': True,
            'skills': skills,
            'count': len(skills)
        })
    except Exception as e:
        logger.error(f"列出技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/search', methods=['GET'])
def search_skills():
    """搜索技能"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'success': False, 'error': '缺少查询参数'}), 400
        
        skills = skill_ai_system.search_skills(query)
        
        return jsonify({
            'success': True,
            'skills': skills,
            'count': len(skills)
        })
    except Exception as e:
        logger.error(f"搜索技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>', methods=['GET'])
def get_skill(skill_id):
    """获取技能详情"""
    try:
        skill = skill_ai_system.get_skill(skill_id)
        
        if not skill:
            return jsonify({'success': False, 'error': '技能不存在'}), 404
        
        return jsonify({'success': True, 'skill': skill.to_dict()})
    except Exception as e:
        logger.error(f"获取技能详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('', methods=['POST'])
def register_skill():
    """注册技能"""
    try:
        data = request.get_json() or {}
        
        name = data.get('name')
        category = data.get('category')
        
        if not name or not category:
            return jsonify({'success': False, 'error': '缺少 name 或 category 参数'}), 400
        
        try:
            cat_enum = SkillCategory(category)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的分类: {category}'}), 400
        
        kwargs = {}
        if 'description' in data:
            kwargs['description'] = data['description']
        if 'version' in data:
            kwargs['version'] = data['version']
        if 'level' in data:
            try:
                kwargs['level'] = SkillLevel(data['level'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的级别: {data["level"]}'}), 400
        if 'input_schema' in data:
            kwargs['input_schema'] = data['input_schema']
        if 'output_schema' in data:
            kwargs['output_schema'] = data['output_schema']
        if 'parameters' in data:
            kwargs['parameters'] = data['parameters']
        if 'dependencies' in data:
            kwargs['dependencies'] = data['dependencies']
        if 'tags' in data:
            kwargs['tags'] = data['tags']
        if 'metadata' in data:
            kwargs['metadata'] = data['metadata']
        
        skill_id = skill_ai_system.register_skill(name, cat_enum, **kwargs)
        
        if skill_id:
            return jsonify({
                'success': True,
                'skill_id': skill_id,
                'message': '技能注册成功'
            })
        else:
            return jsonify({'success': False, 'error': '技能注册失败'}), 500
            
    except Exception as e:
        logger.error(f"注册技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>', methods=['PUT'])
def update_skill(skill_id):
    """更新技能"""
    try:
        data = request.get_json() or {}
        
        kwargs = {}
        if 'name' in data:
            kwargs['name'] = data['name']
        if 'description' in data:
            kwargs['description'] = data['description']
        if 'category' in data:
            try:
                kwargs['category'] = SkillCategory(data['category'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的分类: {data["category"]}'}), 400
        if 'level' in data:
            try:
                kwargs['level'] = SkillLevel(data['level'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的级别: {data["level"]}'}), 400
        if 'input_schema' in data:
            kwargs['input_schema'] = data['input_schema']
        if 'output_schema' in data:
            kwargs['output_schema'] = data['output_schema']
        if 'parameters' in data:
            kwargs['parameters'] = data['parameters']
        if 'tags' in data:
            kwargs['tags'] = data['tags']
        
        success = skill_ai_system.update_skill(skill_id, **kwargs)
        
        if success:
            return jsonify({'success': True, 'message': '技能更新成功'})
        else:
            return jsonify({'success': False, 'error': '技能更新失败'}), 404
            
    except Exception as e:
        logger.error(f"更新技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>/activate', methods=['POST'])
def activate_skill(skill_id):
    """激活技能"""
    try:
        success = skill_ai_system.activate_skill(skill_id)
        
        if success:
            return jsonify({'success': True, 'message': '技能已激活'})
        else:
            return jsonify({'success': False, 'error': '技能激活失败'}), 404
            
    except Exception as e:
        logger.error(f"激活技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>/deactivate', methods=['POST'])
def deactivate_skill(skill_id):
    """停用技能"""
    try:
        success = skill_ai_system.deactivate_skill(skill_id)
        
        if success:
            return jsonify({'success': True, 'message': '技能已停用'})
        else:
            return jsonify({'success': False, 'error': '技能停用失败'}), 404
            
    except Exception as e:
        logger.error(f"停用技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>/execute', methods=['POST'])
def execute_skill(skill_id):
    """执行技能"""
    try:
        data = request.get_json() or {}
        
        inputs = data.get('inputs', {})
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        result = skill_ai_system.execute_skill(skill_id, inputs, user_id, session_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"执行技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/<skill_id>/history', methods=['GET'])
def get_skill_history(skill_id):
    """获取技能执行历史"""
    try:
        limit = int(request.args.get('limit', 10))
        
        history = skill_ai_system.get_skill_history(skill_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取技能历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/recommend', methods=['GET'])
def recommend_skills():
    """推荐技能"""
    try:
        skills = skill_ai_system.recommend_skills()
        
        return jsonify({
            'success': True,
            'recommendations': skills
        })
    except Exception as e:
        logger.error(f"推荐技能失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取技能分类"""
    try:
        categories = [
            {'value': cat.value, 'name': cat.name}
            for cat in SkillCategory
        ]
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/levels', methods=['GET'])
def get_levels():
    """获取技能级别"""
    try:
        levels = [
            {'value': level.value, 'name': level.name}
            for level in SkillLevel
        ]
        return jsonify({'success': True, 'levels': levels})
    except Exception as e:
        logger.error(f"获取级别失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@skill_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取技能统计"""
    try:
        stats = skill_ai_system.get_skill_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
