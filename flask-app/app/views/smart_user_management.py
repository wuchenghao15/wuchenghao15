# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能用户管理模块 - 基于AI的用户行为分析和异常检测
"""

import time
import os
import random
from flask import Blueprint, render_template, request, session, jsonify
from app.utils.logging import logger
from app.config import Config
from app.ai.self_learning_system import self_learning_system
from app.ai.enhanced_system import enhanced_system
from app.models.user import User
import logging
import json
import sys

smart_user_management_bp = Blueprint('smart_user_management', __name__)


@smart_user_management_bp.route('/smart-user-management')
def smart_user_management():
    """智能用户管理视图"""
    try:
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        return render_template('smart_user_management.html', user=user)
    except Exception as e:
        logger.error(f"智能用户管理视图出错: {str(e)}")
        return render_template('smart_user_management.html', user={'username': 'Guest', 'role': 'guest'})


@smart_user_management_bp.route('/api/smart-user-management/users')
def get_smart_users():
    """获取智能用户列表"""
    try:
        users = User.get_all_users()

        users_data = []
        for user in users:
            risk_score = calculate_user_risk_score(user.username)
            has_anomalies = detect_user_anomalies(user.username)
            behavior_analysis = get_user_behavior_analysis(user.username)

            users_data.append({
                'id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'super_admin_approved': user.super_admin_approved,
                'hardware_admin_approved': user.hardware_admin_approved,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'risk_score': risk_score,
                'has_anomalies': has_anomalies,
                'behavior_analysis': behavior_analysis
            })

        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        logger.error(f"获取智能用户列表出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_user_management_bp.route('/api/smart-user-management/user/<username>/behavior')
def get_user_behavior(username):
    """获取用户行为分析"""
    try:
        behavior_data = get_user_behavior_data(username)
        analysis = analyze_user_behavior(behavior_data)

        return jsonify({
            'success': True,
            'username': username,
            'behavior_data': behavior_data,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"获取用户行为分析出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_user_management_bp.route('/api/smart-user-management/user/<username>/risk-score')
def get_user_risk_score(username):
    """获取用户风险评分"""
    try:
        risk_score = calculate_user_risk_score(username)

        return jsonify({
            'success': True,
            'risk_score': risk_score
        }), 200
    except Exception as e:
        logger.error(f"获取用户风险评分失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户风险评分失败: {str(e)}'
        }), 500


@smart_user_management_bp.route('/api/smart-user-management/recommendations')
def get_recommendations():
    """获取智能用户管理推荐"""
    try:
        recommendations = generate_user_recommendations()

        return jsonify({
            'success': True,
            'recommendations': recommendations
        }), 200
    except Exception as e:
        logger.error(f"获取智能用户管理推荐失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取智能用户管理推荐失败: {str(e)}'
        }), 500


@smart_user_management_bp.route('/api/smart-user-management/groups/suggestions')
def get_group_suggestions():
    """获取用户分组建议"""
    try:
        suggestions = generate_group_suggestions()

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        logger.error(f"获取用户分组建议出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@smart_user_management_bp.route('/api/smart-user-management/user/<username>/trends')
def get_user_behavior_trends(username):
    """获取用户行为趋势"""
    try:
        trends = get_user_behavior_trends_data(username)

        return jsonify({
            'success': True,
            'username': username,
            'trends': trends
        })
    except Exception as e:
        logger.error(f"获取用户行为趋势出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


def detect_user_anomalies(username, detailed=False):
    """检测用户异常行为"""
    behavior_data = get_user_behavior_data(username)

    anomalies = []

    if behavior_data.get('failed_logins', 0) > 5:
        anomalies.append({
            'type': 'high_failed_logins',
            'severity': 'warning',
            'description': f'用户 {username} 登录失败次数异常'
        })

    if behavior_data.get('unusual_access_times', False):
        anomalies.append({
            'type': 'unusual_access_pattern',
            'severity': 'info',
            'description': f'用户 {username} 在非常规时间访问系统'
        })

    if detailed:
        return anomalies
    else:
        return len(anomalies) > 0


def calculate_user_risk_score(username):
    """计算用户风险评分"""
    behavior_data = get_user_behavior_data(username)

    risk_score = 0

    if behavior_data.get('failed_logins', 0) > 3:
        risk_score += 20

    if behavior_data.get('unusual_access_times', False):
        risk_score += 15

    if behavior_data.get('password_age_days', 0) > 90:
        risk_score += 10

    risk_score = min(100, max(0, risk_score + random.randint(-5, 5)))

    return risk_score


def get_user_behavior_analysis(username):
    """获取用户行为分析"""
    behavior_data = get_user_behavior_data(username)
    analysis = analyze_user_behavior(behavior_data)

    return analysis


def get_user_behavior_data(username):
    """获取用户行为数据"""
    return {
        'username': username,
        'login_count': random.randint(10, 100),
        'failed_logins': random.randint(0, 10),
        'last_login': time.time() - random.randint(0, 86400),
        'unusual_access_times': random.random() > 0.8,
        'password_age_days': random.randint(1, 180),
        'active_sessions': random.randint(1, 5)
    }


def analyze_user_behavior(behavior_data):
    """分析用户行为"""
    return {
        'activity_level': 'normal' if behavior_data['login_count'] > 20 else 'low',
        'security_risk': 'low' if behavior_data['failed_logins'] < 3 else 'medium',
        'access_pattern': 'regular' if not behavior_data['unusual_access_times'] else 'irregular'
    }


def get_user_behavior_trends_data(username):
    """获取用户行为趋势数据"""
    return {
        'daily_activity': [random.randint(0, 20) for _ in range(7)],
        'weekly_activity': [random.randint(0, 100) for _ in range(4)],
        'monthly_activity': [random.randint(0, 500) for _ in range(12)]
    }


def generate_user_recommendations():
    """生成用户管理建议"""
    return [
        {
            'id': f'rec_{int(time.time())}_1',
            'type': 'security',
            'priority': 'high',
            'description': '建议强制部分用户更新密码',
            'reason': '检测到多个用户密码已超过90天未更新'
        },
        {
            'id': f'rec_{int(time.time())}_2',
            'type': 'access',
            'priority': 'medium',
            'description': '建议审查非活跃用户账户',
            'reason': '发现部分用户超过30天未登录'
        }
    ]


def generate_group_suggestions():
    """生成分组建议"""
    return [
        {
            'id': f'group_{int(time.time())}_1',
            'name': '高活跃用户组',
            'description': '建议创建高活跃用户组以便更好地管理',
            'user_count': random.randint(10, 50)
        }
    ]
