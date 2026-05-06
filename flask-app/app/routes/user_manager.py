#!/usr/bin/env python3
"""
用户管理路由

from flask import Blueprint, render_template, jsonify, request
from app.services.user_manager_service import get_user_manager_service

# 导入用户状态检查装饰器
from app.views.main import check_user_status

user_manager_bp = Blueprint('user_manager', __name__, url_prefix='/user-manager')

@user_manager_bp.route('/')
@check_user_status
def user_manager_dashboard():
    """用户管理仪表盘"""
    return render_template('user_manager/dashboard.html')

@user_manager_bp.route('/profile')
@check_user_status
    """用户个人信息页面"""
    return render_template('user_manager/profile.html')

@user_manager_bp.route('/auto-fill')
@check_user_status
    """自动填充设置页面"""
    return render_template('user_manager/auto_fill.html')

@user_manager_bp.route('/preferences')
@check_user_status
    """用户偏好设置页面"""
    return render_template('user_manager/preferences.html')

@user_manager_bp.route('/api/profile', methods=['GET', 'POST'])
@check_user_status
    """用户个人信息API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1

    if request.method == 'GET':
        profile = service.get_user_profile(user_id)
        return jsonify({
            'success': True,
            'profile': profile
        })
    else:
        data = request.get_json()
        if data:
            result = service.update_user_profile(user_id, data)
            return jsonify({
                'success': result,
                'message': '个人信息更新成功' if result else '个人信息更新失败'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400

@user_manager_bp.route('/api/auto-fill')
@check_user_status
    """自动填充数据API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1
    field_name = request.args.get('field')

    data = service.get_auto_fill_data(user_id, field_name)
    return jsonify({
        'data': data
    })

@user_manager_bp.route('/api/auto-fill/suggestions')
@check_user_status
    """自动填充建议API"""
    user_id = 1  # 假设当前用户ID为1
    field_name = request.args.get('field')

    if not field_name:
        return jsonify({
            'success': False,
        }), 400

    suggestions = service.get_auto_fill_suggestions(user_id, field_name)
    return jsonify({
        'suggestions': suggestions
    })

@user_manager_bp.route('/api/auto-fill/save', methods=['POST'])
@check_user_status
    """保存自动填充数据API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1

    if data:
        result = service.save_auto_fill_data(user_id, data)
        return jsonify({
            'success': result,
        })
    else:
        return jsonify({
            'success': False,
            'message': '无效的请求数据'
        }), 400

@user_manager_bp.route('/api/preferences', methods=['GET', 'POST'])
@check_user_status
    """用户偏好设置API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1
    category = request.args.get('category')

    if request.method == 'GET':
        preferences = service.get_user_preferences(user_id, category)
        return jsonify({
            'success': True,
            'preferences': preferences
    else:
        data = request.get_json()
        if data:
            for key, value in data.items():
                category = data.get('category')
                service.set_user_preference(user_id, key, value, category)
            return jsonify({
                'message': '偏好设置更新成功'
            })
        else:
                'success': False,
                'message': '无效的请求数据'
            }), 400

@user_manager_bp.route('/api/behavior')
@check_user_status
    """用户行为记录API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1
    offset = int(request.args.get('offset', 0))

    behaviors = service.get_user_behavior(user_id, limit, offset)
    return jsonify({
        'success': True,
        'behaviors': behaviors
    })
@user_manager_bp.route('/api/sync-browser', methods=['POST'])
@check_user_status
    """与浏览器同步API"""
    service = get_user_manager_service()
    user_id = 1  # 假设当前用户ID为1
    data = request.get_json()

    if data:
        result = service.sync_with_browser(user_id, data)
        return jsonify({
            'success': result,
            'message': '与浏览器同步成功' if result else '与浏览器同步失败'
    else:
            'success': False,
            'message': '无效的请求数据'
        }), 400
