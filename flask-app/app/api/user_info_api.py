# -*- coding: utf-8 -*-
"""
用户信息API
提供用户IP地址等信息获取接口
"""

from flask import Blueprint, request
import logging
from app.utils.api_response import (
    success_response,
    authentication_error,
    system_error
)

logger = logging.getLogger(__name__)

user_info_api = Blueprint('user_info_api', __name__)


@user_info_api.route('/api/user/ip', methods=['GET'])
def get_user_ip():
    """获取用户IP地址（公开访问，无需登录）"""
    try:
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        elif request.headers.get('X-Real-IP'):
            ip = request.headers.get('X-Real-IP')
        else:
            ip = request.remote_addr or '127.0.0.1'
        
        if ip in ['127.0.0.1', '::1', 'localhost', None]:
            ip = '127.0.0.1 (本地开发)'
        
        return success_response(data={'ip': ip}, message='IP地址获取成功')
    
    except Exception as e:
        logger.error(f"获取IP地址失败: {e}")
        return success_response(data={'ip': '127.0.0.1 (默认)'}, message='获取失败，使用默认值')


@user_info_api.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取用户完整信息"""
    from flask import session
    
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        role = session.get('role', 'guest')
        
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip = request.remote_addr
        
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        return success_response(data={
            'user': {
                'user_id': user_id,
                'username': username,
                'role': role,
                'ip': ip,
                'user_agent': user_agent,
                'logged_in': bool(user_id)
            }
        })
    
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return system_error('获取失败')


@user_info_api.route('/api/users/current', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息（别名路由）"""
    from flask import session
    
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        role = session.get('role', 'guest')
        
        if not user_id:
            return authentication_error('用户未登录')
        
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip = request.remote_addr
        
        return success_response(data={
            'user_id': user_id,
            'username': username,
            'role': role,
            'ip': ip,
            'logged_in': True
        })
    
    except Exception as e:
        logger.error(f"获取当前用户失败: {e}")
        return system_error('获取失败')


@user_info_api.route('/api/user/session', methods=['GET'])
def get_session_info():
    """获取会话信息"""
    from flask import session
    from datetime import datetime
    
    try:
        session_id = session.get('session_id')
        login_time = session.get('login_time')
        
        duration = None
        if login_time:
            try:
                login_dt = datetime.fromisoformat(login_time)
                duration = str(datetime.now() - login_dt)
            except:
                duration = 'Unknown'
        
        return success_response(data={
            'session': {
                'session_id': session_id,
                'login_time': login_time,
                'duration': duration,
                'active': bool(session_id)
            }
        })
    
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        return system_error('获取失败')