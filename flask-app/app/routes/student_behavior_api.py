#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学生行为管理系统 - API路由"""
from flask import Blueprint, request, jsonify
from app.utils.logging import logger
from app.models.student_behavior import (
    BehaviorCategory, BehaviorRecord, BehaviorGoal, init_behavior_system
)

student_behavior_bp = Blueprint('student_behavior', __name__, 
                                 url_prefix='/api/student-behavior')


@student_behavior_bp.route('/init', methods=['POST'])
def init_system():
    """初始化学生行为管理系统"""
    try:
        success = init_behavior_system()
        return jsonify({
            'success': success,
            'message': '学生行为管理系统初始化完成' if success else '初始化失败'
        })
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取行为分类列表"""
    try:
        categories = BehaviorCategory.get_all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in categories]
        })
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/categories', methods=['POST'])
def create_category():
    """创建行为分类"""
    try:
        data = request.json
        category = BehaviorCategory(
            name=data.get('name'),
            description=data.get('description'),
            points_default=data.get('points_default', 0),
            is_active=data.get('is_active', 1),
            created_by=data.get('created_by')
        )
        success = category.save()
        return jsonify({
            'success': success,
            'data': category.to_dict() if success else None,
            'message': '创建成功' if success else '创建失败'
        })
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建分类失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """更新行为分类"""
    try:
        data = request.json
        category = BehaviorCategory(
            category_id=category_id,
            name=data.get('name'),
            description=data.get('description'),
            points_default=data.get('points_default'),
            is_active=data.get('is_active')
        )
        success = category.save()
        return jsonify({
            'success': success,
            'message': '更新成功' if success else '更新失败'
        })
    except Exception as e:
        logger.error(f"更新分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新分类失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/records', methods=['POST'])
def create_record():
    """创建行为记录"""
    try:
        data = request.json
        record = BehaviorRecord(
            student_id=data.get('student_id'),
            category_id=data.get('category_id'),
            behavior_type=data.get('behavior_type'),
            points=data.get('points'),
            description=data.get('description'),
            recorded_by=data.get('recorded_by'),
            notes=data.get('notes')
        )
        success = record.save()
        return jsonify({
            'success': success,
            'data': record.to_dict() if success else None,
            'message': '记录成功' if success else '记录失败'
        })
    except Exception as e:
        logger.error(f"创建记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建记录失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/records/student/<int:student_id>', methods=['GET'])
def get_student_records(student_id):
    """获取学生的行为记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        records = BehaviorRecord.get_by_student(student_id, limit)
        total_points = BehaviorRecord.get_student_points(student_id)
        
        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'total_points': total_points
            }
        })
    except Exception as e:
        logger.error(f"获取记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取记录失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/records/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新行为记录"""
    try:
        data = request.json
        record = BehaviorRecord(
            record_id=record_id,
            student_id=data.get('student_id'),
            category_id=data.get('category_id'),
            behavior_type=data.get('behavior_type'),
            points=data.get('points'),
            description=data.get('description'),
            recorded_by=data.get('recorded_by'),
            notes=data.get('notes')
        )
        success = record.save()
        return jsonify({
            'success': success,
            'message': '更新成功' if success else '更新失败'
        })
    except Exception as e:
        logger.error(f"更新记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新记录失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除行为记录"""
    try:
        from app.utils.db import db_manager
        db_manager.execute('DELETE FROM behavior_records WHERE id = ?', (record_id,))
        logger.info(f"删除行为记录: {record_id}")
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        logger.error(f"删除记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除记录失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/ranking', methods=['GET'])
def get_ranking():
    """获取学生积分排名"""
    try:
        limit = request.args.get('limit', 20, type=int)
        ranking = BehaviorRecord.get_all_students_ranking(limit)
        return jsonify({
            'success': True,
            'data': ranking
        })
    except Exception as e:
        logger.error(f"获取排名失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取排名失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/goals', methods=['POST'])
def create_goal():
    """创建行为目标"""
    try:
        data = request.json
        goal = BehaviorGoal(
            student_id=data.get('student_id'),
            category_id=data.get('category_id'),
            target_points=data.get('target_points'),
            current_points=data.get('current_points', 0),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            status=data.get('status', 'active')
        )
        success = goal.save()
        return jsonify({
            'success': success,
            'message': '目标创建成功' if success else '目标创建失败'
        })
    except Exception as e:
        logger.error(f"创建目标失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建目标失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/goals/student/<int:student_id>', methods=['GET'])
def get_student_goals(student_id):
    """获取学生的行为目标"""
    try:
        goals = BehaviorGoal.get_by_student(student_id)
        return jsonify({
            'success': True,
            'data': goals
        })
    except Exception as e:
        logger.error(f"获取目标失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取目标失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/goals/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """更新行为目标"""
    try:
        data = request.json
        goal = BehaviorGoal(
            goal_id=goal_id,
            student_id=data.get('student_id'),
            category_id=data.get('category_id'),
            target_points=data.get('target_points'),
            current_points=data.get('current_points'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            status=data.get('status')
        )
        success = goal.save()
        return jsonify({
            'success': success,
            'message': '目标更新成功' if success else '目标更新失败'
        })
    except Exception as e:
        logger.error(f"更新目标失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新目标失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    try:
        from app.utils.db import db_manager
        
        # 获取总记录数
        total_records = db_manager.fetch_one('''
            SELECT COUNT(*) as count FROM behavior_records
        ''')
        
        # 获取学生总数
        total_students = db_manager.fetch_one('''
            SELECT COUNT(DISTINCT student_id) as count FROM behavior_records
        ''')
        
        # 获取积极/消极记录数
        type_stats = db_manager.fetch_all('''
            SELECT behavior_type, COUNT(*) as count, SUM(points) as total_points
            FROM behavior_records
            GROUP BY behavior_type
        ''')
        
        # 获取分类统计
        category_stats = db_manager.fetch_all('''
            SELECT bc.name, COUNT(*) as count, SUM(br.points) as total_points
            FROM behavior_records br
            LEFT JOIN behavior_categories bc ON br.category_id = bc.id
            GROUP BY bc.id
        ''')
        
        positive_stats = {}
        negative_stats = {}
        
        for stat in type_stats:
            if isinstance(stat, dict):
                if stat.get('behavior_type') == 'positive':
                    positive_stats = stat
                else:
                    negative_stats = stat
            else:
                if stat[0] == 'positive':
                    positive_stats = {'count': stat[1], 'total_points': stat[2]}
                else:
                    negative_stats = {'count': stat[1], 'total_points': stat[2]}
        
        return jsonify({
            'success': True,
            'data': {
                'total_records': total_records['count'] if isinstance(total_records, dict) else total_records[0],
                'total_students': total_students['count'] if isinstance(total_students, dict) else total_students[0],
                'positive': positive_stats,
                'negative': negative_stats,
                'categories': category_stats
            }
        })
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500


@student_behavior_bp.route('/statistics/student/<int:student_id>', methods=['GET'])
def get_student_statistics(student_id):
    """获取学生个人统计"""
    try:
        from app.utils.db import db_manager
        
        # 获取学生的分类统计
        category_stats = db_manager.fetch_all('''
            SELECT bc.name, br.behavior_type, COUNT(*) as count, SUM(br.points) as total_points
            FROM behavior_records br
            LEFT JOIN behavior_categories bc ON br.category_id = bc.id
            WHERE br.student_id = ?
            GROUP BY bc.id, br.behavior_type
        ''', (student_id,))
        
        # 获取学生的月度统计
        monthly_stats = db_manager.fetch_all('''
            SELECT 
                strftime('%Y-%m', recorded_at) as month,
                behavior_type,
                COUNT(*) as count,
                SUM(points) as total_points
            FROM behavior_records
            WHERE student_id = ?
            GROUP BY strftime('%Y-%m', recorded_at), behavior_type
            ORDER BY month DESC
        ''', (student_id,))
        
        total_points = BehaviorRecord.get_student_points(student_id)
        
        return jsonify({
            'success': True,
            'data': {
                'total_points': total_points,
                'categories': category_stats,
                'monthly': monthly_stats
            }
        })
    except Exception as e:
        logger.error(f"获取学生统计失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取学生统计失败: {str(e)}'
        }), 500