#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务中心API接口
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.ai.task_center import (
    task_center,
    TaskPriority,
    TaskStatus,
    TaskType
)

logger = logging.getLogger('task_center_api')

task_bp = Blueprint('task_center', __name__, url_prefix='/api/tasks')


@task_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = task_center.get_system_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/overview', methods=['GET'])
def get_overview():
    """获取概览"""
    try:
        overview = task_center.ai_butler.get_overview()
        return jsonify({'success': True, 'overview': overview})
    except Exception as e:
        logger.error(f"获取概览失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('', methods=['GET'])
def list_tasks():
    """列出任务"""
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        task_type = request.args.get('type')
        
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的状态: {status}'}), 400
        
        priority_enum = None
        if priority:
            try:
                priority_enum = TaskPriority(priority)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的优先级: {priority}'}), 400
        
        type_enum = None
        if task_type:
            try:
                type_enum = TaskType(task_type)
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的任务类型: {task_type}'}), 400
        
        tasks = task_center.list_tasks(status_enum, priority_enum, type_enum)
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })
    except Exception as e:
        logger.error(f"列出任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        task = task_center.get_task(task_id)
        
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({'success': True, 'task': task.to_dict()})
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('', methods=['POST'])
def create_task():
    """创建任务"""
    try:
        data = request.get_json() or {}
        
        name = data.get('name')
        task_type = data.get('type')
        
        if not name or not task_type:
            return jsonify({'success': False, 'error': '缺少 name 或 type 参数'}), 400
        
        try:
            type_enum = TaskType(task_type)
        except ValueError:
            return jsonify({'success': False, 'error': f'无效的任务类型: {task_type}'}), 400
        
        kwargs = {}
        if 'description' in data:
            kwargs['description'] = data['description']
        if 'priority' in data:
            try:
                kwargs['priority'] = TaskPriority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的优先级: {data["priority"]}'}), 400
        if 'inputs' in data:
            kwargs['inputs'] = data['inputs']
        if 'required_skills' in data:
            kwargs['required_skills'] = data['required_skills']
        if 'preferred_ais' in data:
            kwargs['preferred_ais'] = data['preferred_ais']
        if 'metadata' in data:
            kwargs['metadata'] = data['metadata']
        if 'tags' in data:
            kwargs['tags'] = data['tags']
        
        task_id = task_center.create_task(name, type_enum, **kwargs)
        
        if task_id:
            task = task_center.get_task(task_id)
            return jsonify({
                'success': True,
                'task_id': task_id,
                'task': task.to_dict(),
                'message': '任务创建成功,AI管家已自动分配'
            })
        else:
            return jsonify({'success': False, 'error': '任务创建失败'}), 500
            
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    try:
        data = request.get_json() or {}
        
        kwargs = {}
        if 'name' in data:
            kwargs['name'] = data['name']
        if 'description' in data:
            kwargs['description'] = data['description']
        if 'priority' in data:
            try:
                kwargs['priority'] = TaskPriority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'无效的优先级: {data["priority"]}'}), 400
        if 'inputs' in data:
            kwargs['inputs'] = data['inputs']
        
        success = task_center.update_task(task_id, **kwargs)
        
        if success:
            return jsonify({'success': True, 'message': '任务更新成功'})
        else:
            return jsonify({'success': False, 'error': '任务更新失败'}), 404
            
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        success = task_center.delete_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务删除成功'})
        else:
            return jsonify({'success': False, 'error': '任务删除失败'}), 404
            
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """分配任务"""
    try:
        data = request.get_json() or {}
        ai_id = data.get('ai_id')
        
        if not ai_id:
            return jsonify({'success': False, 'error': '缺少 ai_id 参数'}), 400
        
        success = task_center.assign_task(task_id, ai_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务分配成功'})
        else:
            return jsonify({'success': False, 'error': '任务分配失败'}), 400
            
    except Exception as e:
        logger.error(f"分配任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/claim', methods=['POST'])
def claim_task(task_id):
    """认领任务"""
    try:
        data = request.get_json() or {}
        ai_id = data.get('ai_id')
        
        if not ai_id:
            return jsonify({'success': False, 'error': '缺少 ai_id 参数'}), 400
        
        success = task_center.claim_task(task_id, ai_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务认领成功'})
        else:
            return jsonify({'success': False, 'error': '任务认领失败'}), 400
            
    except Exception as e:
        logger.error(f"认领任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/start', methods=['POST'])
def start_task(task_id):
    """开始任务"""
    try:
        success = task_center.start_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务已开始执行'})
        else:
            return jsonify({'success': False, 'error': '任务开始失败'}), 400
            
    except Exception as e:
        logger.error(f"开始任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    try:
        data = request.get_json() or {}
        outputs = data.get('outputs', {})
        
        success = task_center.complete_task(task_id, outputs)
        
        if success:
            return jsonify({'success': True, 'message': '任务完成成功'})
        else:
            return jsonify({'success': False, 'error': '任务完成失败'}), 400
            
    except Exception as e:
        logger.error(f"完成任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/fail', methods=['POST'])
def fail_task(task_id):
    """任务失败"""
    try:
        data = request.get_json() or {}
        error_message = data.get('error_message', '')
        
        success = task_center.fail_task(task_id, error_message)
        
        if success:
            return jsonify({'success': True, 'message': '任务标记为失败'})
        else:
            return jsonify({'success': False, 'error': '任务标记失败'}), 400
            
    except Exception as e:
        logger.error(f"标记任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        success = task_center.cancel_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': '任务已取消'})
        else:
            return jsonify({'success': False, 'error': '任务取消失败'}), 400
            
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/workers', methods=['GET'])
def list_workers():
    """列出AI工作者"""
    try:
        status = request.args.get('status')
        workers = task_center.list_workers(status)
        
        return jsonify({
            'success': True,
            'workers': workers,
            'count': len(workers)
        })
    except Exception as e:
        logger.error(f"列出工作者失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/workers/<ai_id>', methods=['GET'])
def get_worker(ai_id):
    """获取AI工作者详情"""
    try:
        worker = task_center.get_worker(ai_id)
        
        if not worker:
            return jsonify({'success': False, 'error': 'AI工作者不存在'}), 404
        
        return jsonify({'success': True, 'worker': worker.to_dict()})
    except Exception as e:
        logger.error(f"获取工作者失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/workers', methods=['POST'])
def register_worker():
    """注册AI工作者"""
    try:
        data = request.get_json() or {}
        
        ai_id = data.get('ai_id')
        name = data.get('name')
        
        if not ai_id or not name:
            return jsonify({'success': False, 'error': '缺少 ai_id 或 name 参数'}), 400
        
        kwargs = {}
        if 'specialties' in data:
            kwargs['specialties'] = data['specialties']
        if 'skills' in data:
            kwargs['skills'] = data['skills']
        if 'metadata' in data:
            kwargs['metadata'] = data['metadata']
        
        success = task_center.register_worker(ai_id, name, **kwargs)
        
        if success:
            return jsonify({'success': True, 'message': 'AI工作者注册成功'})
        else:
            return jsonify({'success': False, 'error': 'AI工作者已存在'}), 409
            
    except Exception as e:
        logger.error(f"注册工作者失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/history', methods=['GET'])
def get_history():
    """获取任务历史"""
    try:
        ai_id = request.args.get('ai_id')
        limit = int(request.args.get('limit', 10))
        
        history = task_center.get_task_history(ai_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"获取任务历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/types', methods=['GET'])
def get_task_types():
    """获取任务类型"""
    try:
        types = [
            {'value': t.value, 'name': t.name}
            for t in TaskType
        ]
        return jsonify({'success': True, 'types': types})
    except Exception as e:
        logger.error(f"获取任务类型失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/priorities', methods=['GET'])
def get_priorities():
    """获取优先级"""
    try:
        priorities = [
            {'value': p.value, 'name': p.name}
            for p in TaskPriority
        ]
        return jsonify({'success': True, 'priorities': priorities})
    except Exception as e:
        logger.error(f"获取优先级失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/reassign-failed', methods=['POST'])
def reassign_failed():
    """重新分配失败任务"""
    try:
        task_center.ai_butler.reassign_failed_tasks()
        return jsonify({'success': True, 'message': '已尝试重新分配失败任务'})
    except Exception as e:
        logger.error(f"重新分配失败任务失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@task_bp.route('/balance-load', methods=['POST'])
def balance_load():
    """负载均衡"""
    try:
        task_center.ai_butler.balance_load()
        return jsonify({'success': True, 'message': '负载均衡已执行'})
    except Exception as e:
        logger.error(f"负载均衡失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
