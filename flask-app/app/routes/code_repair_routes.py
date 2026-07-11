#!/usr/bin/env python3
"""
代码修复API路由 - 提供代码错误检测和修复接口
"""

import os
from flask import Blueprint, jsonify, request
from ..services.code_repair_service import (
    init_repair_tables,
    create_repair_employee,
    get_repair_employee,
    detect_file_errors,
    fix_file_errors,
    scan_directory_for_errors,
    auto_repair_directory,
    get_repair_stats,
    get_pending_errors,
    PROJECT_ROOT
)

repair_bp = Blueprint('repair', __name__, url_prefix='/api/repair')


@repair_bp.route('/employee', methods=['GET'])
def employee_info():
    """获取代码修复AI员工信息"""
    employee = get_repair_employee()
    if employee:
        return jsonify({
            'status': 'success',
            'data': employee
        })
    return jsonify({
        'status': 'error',
        'message': '代码修复员工不存在'
    }), 404


@repair_bp.route('/scan', methods=['POST'])
def scan_errors():
    """扫描目录中的错误"""
    data = request.get_json() or {}
    directory = data.get('directory', PROJECT_ROOT)
    extensions = data.get('extensions', ['.py', '.js', '.css', '.json', '.sql', '.html', '.bak'])
    
    if not os.path.exists(directory):
        return jsonify({
            'status': 'error',
            'message': '目录不存在'
        }), 400
    
    errors = scan_directory_for_errors(directory, extensions)
    return jsonify({
        'status': 'success',
        'data': errors,
        'count': len(errors),
        'directory': directory
    })


@repair_bp.route('/repair', methods=['POST'])
def repair_file():
    """修复指定文件"""
    data = request.get_json() or {}
    file_path = data.get('file_path', '')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({
            'status': 'error',
            'message': '文件不存在'
        }), 400
    
    repair_id, status, message = fix_file_errors(file_path)
    return jsonify({
        'status': 'success' if status == 'success' else 'error',
        'repair_id': repair_id,
        'file_path': file_path,
        'result': status,
        'message': message
    })


@repair_bp.route('/repair-directory', methods=['POST'])
def repair_directory():
    """批量修复目录中的错误"""
    data = request.get_json() or {}
    directory = data.get('directory', PROJECT_ROOT)
    extensions = data.get('extensions', ['.py', '.js', '.css', '.json', '.sql', '.html', '.bak'])
    
    if not os.path.exists(directory):
        return jsonify({
            'status': 'error',
            'message': '目录不存在'
        }), 400
    
    results = auto_repair_directory(directory, extensions)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    no_errors_count = sum(1 for r in results if r['status'] == 'no_errors')
    
    return jsonify({
        'status': 'success',
        'data': results,
        'summary': {
            'total_files': len(results),
            'success': success_count,
            'failed': failed_count,
            'no_errors': no_errors_count,
            'directory': directory
        }
    })


@repair_bp.route('/stats', methods=['GET'])
def stats():
    """获取修复统计"""
    result = get_repair_stats()
    return jsonify({
        'status': 'success',
        'data': result
    })


@repair_bp.route('/errors', methods=['GET'])
def errors():
    """获取未修复的错误列表"""
    limit = int(request.args.get('limit', 50))
    errors = get_pending_errors(limit)
    return jsonify({
        'status': 'success',
        'data': errors,
        'count': len(errors)
    })


@repair_bp.route('/detect', methods=['POST'])
def detect_errors():
    """检测单个文件的错误"""
    data = request.get_json() or {}
    file_path = data.get('file_path', '')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({
            'status': 'error',
            'message': '文件不存在'
        }), 400
    
    errors = detect_file_errors(file_path)
    return jsonify({
        'status': 'success',
        'data': errors,
        'count': len(errors),
        'file_path': file_path
    })
