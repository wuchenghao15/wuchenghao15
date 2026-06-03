# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
监考API蓝图
提供监考相关的RESTful API接口
"""

from flask import Blueprint, request, jsonify, session
import json

from app.services.exam_proctor_service import get_exam_proctor_service

proctor_api = Blueprint('proctor_api', __name__)

@proctor_api.route('/api/proctor/session', methods=['POST'])
def create_session():
    """创建考试会话"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    data = request.get_json()
    exam_id = data.get('exam_id', '')
    
    service = get_exam_proctor_service()
    session_id = service.create_exam_session(user_id, exam_id)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': '会话创建成功'
    }), 201

@proctor_api.route('/api/proctor/session/<session_id>/verify', methods=['GET'])
def verify_session(session_id):
    """验证会话有效性"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    valid = service.verify_session(session_id, user_id)
    
    return jsonify({
        'success': True,
        'valid': valid,
        'message': '会话验证成功' if valid else '会话无效或已过期'
    })

@proctor_api.route('/api/proctor/session/<session_id>/activity', methods=['POST'])
def record_activity(session_id):
    """记录活动时间"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    service.record_activity(session_id)
    
    return jsonify({'success': True, 'message': '活动记录成功'})

@proctor_api.route('/api/proctor/session/<session_id>/refresh', methods=['POST'])
def record_refresh(session_id):
    """记录页面刷新"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    service.increment_refresh_count(session_id)
    
    blocked = service.check_refresh_attempts(session_id)
    
    if blocked:
        service.detect_suspicious_activity(session_id, 'refresh_abuse', '刷新次数超过限制')
        return jsonify({
            'success': False,
            'blocked': True,
            'message': '刷新次数过多,考试已被锁定,请联系监考教师'
        }), 403
    
    return jsonify({
        'success': True,
        'blocked': False,
        'message': '刷新记录成功'
    })

@proctor_api.route('/api/proctor/session/<session_id>/pause/request', methods=['POST'])
def request_pause(session_id):
    """请求暂停考试"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    data = request.get_json()
    reason = data.get('reason', '')
    
    service = get_exam_proctor_service()
    success = service.request_pause(session_id, user_id, reason)
    
    if success:
        return jsonify({
            'success': True,
            'message': '暂停申请已提交,请等待监考教师审批'
        })
    else:
        return jsonify({
            'success': False,
            'message': '已有待处理的暂停申请,请耐心等待'
        })

@proctor_api.route('/api/proctor/pause_requests', methods=['GET'])
def get_pause_requests():
    """获取暂停申请列表(监考教师)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    # 验证是否为监考教师(简化版)
    role = session.get('role', '')
    if role not in ['teacher', 'admin', 'exam_admin']:
        return jsonify({'error': 'Forbidden', 'message': '权限不足'}), 403
    
    status = request.args.get('status', 'pending')
    
    service = get_exam_proctor_service()
    requests = service.get_pause_requests(status)
    
    return jsonify({
        'success': True,
        'data': requests
    })

@proctor_api.route('/api/proctor/pause_request/<request_id>/approve', methods=['POST'])
def approve_pause(request_id):
    """审批暂停申请(监考教师)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    # 验证是否为监考教师
    role = session.get('role', '')
    if role not in ['teacher', 'admin', 'exam_admin']:
        return jsonify({'error': 'Forbidden', 'message': '权限不足'}), 403
    
    service = get_exam_proctor_service()
    success = service.approve_pause_request(int(request_id), user_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': '暂停申请已批准'
        })
    else:
        return jsonify({
            'success': False,
            'message': '审批失败,申请不存在或已处理'
        })

@proctor_api.route('/api/proctor/session/<session_id>/resume', methods=['POST'])
def resume_session(session_id):
    """恢复考试"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    success = service.resume_exam(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': '考试已恢复'
        })
    else:
        return jsonify({
            'success': False,
            'message': '恢复失败,会话状态不正确'
        })

@proctor_api.route('/api/proctor/session/<session_id>/info', methods=['GET'])
def get_session_info(session_id):
    """获取会话信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    info = service.get_session_info(session_id)
    
    if info:
        return jsonify({'success': True, 'data': info})
    else:
        return jsonify({'success': False, 'message': '会话不存在'}), 404

@proctor_api.route('/api/proctor/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """结束会话"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    service = get_exam_proctor_service()
    service.end_session(session_id)
    
    return jsonify({'success': True, 'message': '会话已结束'})

@proctor_api.route('/api/proctor/generate_token', methods=['POST'])
def generate_token():
    """生成唯一会话令牌"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    data = request.get_json()
    session_id = data.get('session_id', '')
    
    service = get_exam_proctor_service()
    token = service.generate_unique_session_token(session_id)
    
    return jsonify({'success': True, 'token': token})
