# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
摸底测试API蓝图
提供摸底测试的RESTful API接口
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
import json

from app.services.placement_test_service import get_placement_test_service

placement_test_api = Blueprint('placement_test_api', __name__)

@placement_test_api.route('/api/placement/test', methods=['POST'])
def create_placement_test():
    """创建摸底测试"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
        
        data = request.get_json() or {}
        subject = data.get('subject')
        
        service = get_placement_test_service()
        test = service.create_placement_test(user_id, subject)
        
        return jsonify({'success': True, **test}), 201
    except Exception as e:
        import traceback
        print(f"创建摸底测试失败: {type(e).__name__}: {e}")
        print(f"堆栈:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@placement_test_api.route('/api/placement/test/adaptive', methods=['POST'])
def create_adaptive_test():
    """创建自适应摸底测试"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    data = request.get_json()
    initial_difficulty = data.get('initial_difficulty', '中级')
    
    service = get_placement_test_service()
    test = service.create_adaptive_placement_test(user_id, initial_difficulty)
    
    return jsonify(test), 201

@placement_test_api.route('/api/placement/test/<test_id>', methods=['GET'])
def get_placement_test(test_id):
    """获取摸底测试信息"""
    service = get_placement_test_service()
    test = service.get_placement_test(test_id)
    
    if not test:
        return jsonify({'error': 'NotFound', 'message': '测试不存在'}), 404
    
    return jsonify(test)

@placement_test_api.route('/api/placement/test/<test_id>/start', methods=['POST'])
def start_placement_test(test_id):
    """开始摸底测试"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_placement_test_service()
    success = service.start_test(test_id)
    
    if not success:
        return jsonify({'error': 'Failed', 'message': '无法开始测试'}), 400
    
    return jsonify({'success': True, 'message': '测试已开始'})

@placement_test_api.route('/api/placement/test/<test_id>/answer', methods=['POST'])
def submit_answer(test_id):
    """提交答案"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    
    service = get_placement_test_service()
    success = service.submit_answer(test_id, question_id, user_answer)
    
    if not success:
        return jsonify({'error': 'Failed', 'message': '提交失败'}), 400
    
    return jsonify({'success': True, 'message': '答案已提交'})

@placement_test_api.route('/api/placement/test/<test_id>/complete', methods=['POST'])
def complete_placement_test(test_id):
    """完成摸底测试"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_placement_test_service()
    report = service.complete_test(test_id)
    
    if not report:
        return jsonify({'error': 'Failed', 'message': '无法生成报告'}), 400
    
    return jsonify(report)

@placement_test_api.route('/api/placement/reports', methods=['GET'])
def get_user_reports():
    """获取用户的摸底测试报告"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    limit = int(request.args.get('limit', 10))
    
    service = get_placement_test_service()
    reports = service.get_user_reports(user_id, limit)
    
    return jsonify(reports)

@placement_test_api.route('/api/placement/level', methods=['GET'])
def get_user_level():
    """获取用户当前水平"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_placement_test_service()
    level = service.get_user_current_level(user_id)
    
    return jsonify({'level': level})

@placement_test_api.route('/exam/placement')
def placement_test_page():
    """摸底测试页面"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    return jsonify({'message': '摸底测试页面', 'user_id': user_id})
