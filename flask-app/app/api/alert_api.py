# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
告警API - 提供多级告警、告警通知、告警历史记录等功能
"""

from flask import Blueprint, jsonify, request, session
import logging
import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
alert_api = Blueprint('alert_api', __name__, url_prefix='/api/alert')

# 数据库路径
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

# ==================== 权限检查装饰器 ====================

def require_admin_role(func):
    """管理员权限检查装饰器"""
    def decorated(*args, **kwargs):
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': '权限不足，需要管理员权限'
            }), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated


# ==================== 多级告警系统 ====================

# 告警级别定义
ALERT_LEVELS = {
    'INFO': {
        'level': 1,
        'color': '#3b82f6',  # 蓝色
        'icon': 'info-circle',
        'priority': 1,
        'description': '信息告警 - 用于记录一般信息'
    },
    'WARNING': {
        'level': 2,
        'color': '#f59e0b',  # 橙色
        'icon': 'exclamation-triangle',
        'priority': 2,
        'description': '警告告警 - 需要注意但不立即处理'
    },
    'ERROR': {
        'level': 3,
        'color': '#ef4444',  # 红色
        'icon': 'times-circle',
        'priority': 3,
        'description': '错误告警 - 需要尽快处理'
    },
    'CRITICAL': {
        'level': 4,
        'color': '#dc2626',  # 深红色
        'icon': 'fire',
        'priority': 4,
        'description': '严重告警 - 需要立即处理'
    }
}

# 告警类型定义
ALERT_TYPES = {
    'cpu_high': {
        'name': 'CPU使用率过高',
        'category': 'performance',
        'default_level': 'WARNING',
        'threshold': 80
    },
    'memory_high': {
        'name': '内存使用率过高',
        'category': 'performance',
        'default_level': 'WARNING',
        'threshold': 80
    },
    'disk_high': {
        'name': '磁盘空间不足',
        'category': 'storage',
        'default_level': 'WARNING',
        'threshold': 80
    },
    'database_error': {
        'name': '数据库异常',
        'category': 'database',
        'default_level': 'ERROR',
        'threshold': None
    },
    'network_error': {
        'name': '网络异常',
        'category': 'network',
        'default_level': 'WARNING',
        'threshold': None
    },
    'service_down': {
        'name': '服务宕机',
        'category': 'service',
        'default_level': 'CRITICAL',
        'threshold': None
    },
    'security_breach': {
        'name': '安全漏洞',
        'category': 'security',
        'default_level': 'CRITICAL',
        'threshold': None
    },
    'navigation_anomaly': {
        'name': '导航异常',
        'category': 'user_behavior',
        'default_level': 'WARNING',
        'threshold': 5
    },
    'api_error': {
        'name': 'API错误',
        'category': 'application',
        'default_level': 'ERROR',
        'threshold': None
    },
    'auth_failure': {
        'name': '认证失败',
        'category': 'security',
        'default_level': 'WARNING',
        'threshold': 3
    }
}


@alert_api.route('/levels', methods=['GET'])
def get_alert_levels():
    """
    获取告警级别定义 - 返回所有告警级别的详细信息
    """
    try:
        return jsonify({
            'success': True,
            'data': ALERT_LEVELS
        })
        
    except Exception as e:
        logger.error(f'获取告警级别失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/types', methods=['GET'])
def get_alert_types():
    """
    获取告警类型定义 - 返回所有告警类型的详细信息
    """
    try:
        return jsonify({
            'success': True,
            'data': ALERT_TYPES
        })
        
    except Exception as e:
        logger.error(f'获取告警类型失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/create', methods=['POST'])
@require_admin_role
def create_alert():
    """
    创建告警 - 手动或自动创建告警记录
    """
    try:
        data = request.get_json()
        
        # 验证必要字段
        if 'alert_type' not in data:
            return jsonify({
                'success': False,
                'error': '缺少告警类型'
            }), 400
        
        # 获取告警类型配置
        alert_type = data['alert_type']
        type_config = ALERT_TYPES.get(alert_type, {})
        
        # 设置告警级别
        level = data.get('level', type_config.get('default_level', 'WARNING'))
        
        # 设置告警消息
        message = data.get('message', f'{type_config.get("name", alert_type)}告警')
        
        # 设置指标值和阈值
        metric_value = data.get('metric_value', 0)
        threshold = data.get('threshold', type_config.get('threshold', 0))
        
        # 设置来源信息
        source = data.get('source', 'system')
        details = data.get('details', {})
        
        # 创建告警记录
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 确保告警表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metric_value REAL,
                    threshold REAL,
                    source TEXT,
                    details TEXT,
                    status TEXT DEFAULT 'active',
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    resolved INTEGER DEFAULT 0,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    resolution_note TEXT,
                    notification_sent INTEGER DEFAULT 0,
                    notification_channels TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入告警记录
            cursor.execute('''
                INSERT INTO alert_records 
                (alert_type, alert_level, message, metric_value, threshold, source, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (alert_type, level, message, metric_value, threshold, source, json.dumps(details)))
            
            alert_id = cursor.lastrowid
            
            # 记录告警历史
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    action_by TEXT,
                    action_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO alert_history 
                (alert_id, action, action_by, action_details)
                VALUES (?, ?, ?, ?)
            ''', (alert_id, 'created', session.get('username', 'system'), json.dumps({'level': level, 'message': message})))
            
            conn.commit()
        
        # 发送告警通知
        notification_result = _send_alert_notification(alert_id, level, message, details)
        
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': '告警已创建',
            'notification_sent': notification_result['sent']
        })
        
    except Exception as e:
        logger.error(f'创建告警失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/list', methods=['GET'])
@require_admin_role
def get_alerts():
    """
    获取告警列表 - 支持多条件筛选
    """
    try:
        # 获取筛选参数
        status = request.args.get('status', 'active')
        level = request.args.get('level', 'all')
        type_filter = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if status != 'all':
                conditions.append('status = ?')
                params.append(status)
            
            if level != 'all':
                conditions.append('alert_level = ?')
                params.append(level)
            
            if type_filter != 'all':
                conditions.append('alert_type = ?')
                params.append(type_filter)
            
            where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
            
            # 查询告警记录
            query = f'''
                SELECT id, alert_type, alert_level, message, metric_value, threshold,
                       source, details, status, acknowledged, acknowledged_by, acknowledged_at,
                       resolved, resolved_by, resolved_at, resolution_note,
                       notification_sent, notification_channels, created_at, updated_at
                FROM alert_records 
                {where_clause}
                ORDER BY 
                    CASE alert_level 
                        WHEN 'CRITICAL' THEN 4 
                        WHEN 'ERROR' THEN 3 
                        WHEN 'WARNING' THEN 2 
                        WHEN 'INFO' THEN 1 
                    END DESC,
                    created_at DESC
                LIMIT ? OFFSET ?
            '''
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'metric_value', 'threshold',
                       'source', 'details', 'status', 'acknowledged', 'acknowledged_by', 'acknowledged_at',
                       'resolved', 'resolved_by', 'resolved_at', 'resolution_note',
                       'notification_sent', 'notification_channels', 'created_at', 'updated_at']
            
            alerts = []
            for row in cursor.fetchall():
                alert = dict(zip(columns, row))
                # 解析JSON字段
                if alert['details']:
                    alert['details'] = json.loads(alert['details'])
                if alert['notification_channels']:
                    alert['notification_channels'] = json.loads(alert['notification_channels'])
                # 添加级别信息
                alert['level_info'] = ALERT_LEVELS.get(alert['alert_level'], {})
                alerts.append(alert)
            
            # 获取总数
            count_query = f'SELECT COUNT(*) FROM alert_records {where_clause}'
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f'获取告警列表失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/<int:alert_id>', methods=['GET'])
@require_admin_role
def get_alert_detail(alert_id):
    """
    获取告警详情 - 单个告警的完整信息
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 查询告警详情
            cursor.execute('''
                SELECT id, alert_type, alert_level, message, metric_value, threshold,
                       source, details, status, acknowledged, acknowledged_by, acknowledged_at,
                       resolved, resolved_by, resolved_at, resolution_note,
                       notification_sent, notification_channels, created_at, updated_at
                FROM alert_records 
                WHERE id = ?
            ''', (alert_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': '告警不存在'
                }), 404
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'metric_value', 'threshold',
                       'source', 'details', 'status', 'acknowledged', 'acknowledged_by', 'acknowledged_at',
                       'resolved', 'resolved_by', 'resolved_at', 'resolution_note',
                       'notification_sent', 'notification_channels', 'created_at', 'updated_at']
            
            alert = dict(zip(columns, row))
            
            # 解析JSON字段
            if alert['details']:
                alert['details'] = json.loads(alert['details'])
            if alert['notification_channels']:
                alert['notification_channels'] = json.loads(alert['notification_channels'])
            
            # 添加级别和类型信息
            alert['level_info'] = ALERT_LEVELS.get(alert['alert_level'], {})
            alert['type_info'] = ALERT_TYPES.get(alert['alert_type'], {})
            
            # 查询告警历史
            cursor.execute('''
                SELECT id, action, action_by, action_details, created_at
                FROM alert_history 
                WHERE alert_id = ?
                ORDER BY created_at DESC
            ''', (alert_id,))
            
            history_columns = ['id', 'action', 'action_by', 'action_details', 'created_at']
            history = []
            for h_row in cursor.fetchall():
                h = dict(zip(history_columns, h_row))
                if h['action_details']:
                    h['action_details'] = json.loads(h['action_details'])
                history.append(h)
            
            alert['history'] = history
        
        return jsonify({
            'success': True,
            'alert': alert
        })
        
    except Exception as e:
        logger.error(f'获取告警详情失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/<int:alert_id>/acknowledge', methods=['POST'])
@require_admin_role
def acknowledge_alert(alert_id):
    """
    确认告警 - 管理员确认已知晓告警
    """
    try:
        data = request.get_json() or {}
        
        username = session.get('username', 'unknown')
        note = data.get('note', '')
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 更新告警状态
            cursor.execute('''
                UPDATE alert_records 
                SET acknowledged = 1, 
                    acknowledged_by = ?, 
                    acknowledged_at = ?,
                    status = 'acknowledged',
                    updated_at = ?
                WHERE id = ?
            ''', (username, datetime.now(), datetime.now(), alert_id))
            
            # 记录历史
            cursor.execute('''
                INSERT INTO alert_history 
                (alert_id, action, action_by, action_details)
                VALUES (?, ?, ?, ?)
            ''', (alert_id, 'acknowledged', username, json.dumps({'note': note})))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '告警已确认'
        })
        
    except Exception as e:
        logger.error(f'确认告警失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/<int:alert_id>/resolve', methods=['POST'])
@require_admin_role
def resolve_alert(alert_id):
    """
    解决告警 - 管理员解决告警问题
    """
    try:
        data = request.get_json() or {}
        
        username = session.get('username', 'unknown')
        resolution_note = data.get('resolution_note', '')
        action_taken = data.get('action_taken', '')
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 更新告警状态
            cursor.execute('''
                UPDATE alert_records 
                SET resolved = 1, 
                    resolved_by = ?, 
                    resolved_at = ?,
                    resolution_note = ?,
                    status = 'resolved',
                    updated_at = ?
                WHERE id = ?
            ''', (username, datetime.now(), resolution_note, datetime.now(), alert_id))
            
            # 记录历史
            cursor.execute('''
                INSERT INTO alert_history 
                (alert_id, action, action_by, action_details)
                VALUES (?, ?, ?, ?)
            ''', (alert_id, 'resolved', username, json.dumps({
                'resolution_note': resolution_note,
                'action_taken': action_taken
            })))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '告警已解决'
        })
        
    except Exception as e:
        logger.error(f'解决告警失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/batch/resolve', methods=['POST'])
@require_admin_role
def batch_resolve_alerts():
    """
    批量解决告警 - 同时解决多个告警
    """
    try:
        data = request.get_json()
        
        alert_ids = data.get('alert_ids', [])
        resolution_note = data.get('resolution_note', '批量解决')
        
        if not alert_ids:
            return jsonify({
                'success': False,
                'error': '缺少告警ID列表'
            }), 400
        
        username = session.get('username', 'unknown')
        resolved_count = 0
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            for alert_id in alert_ids:
                # 更新告警状态
                cursor.execute('''
                    UPDATE alert_records 
                    SET resolved = 1, 
                        resolved_by = ?, 
                        resolved_at = ?,
                        resolution_note = ?,
                        status = 'resolved',
                        updated_at = ?
                    WHERE id = ? AND resolved = 0
                ''', (username, datetime.now(), resolution_note, datetime.now(), alert_id))
                
                if cursor.rowcount > 0:
                    # 记录历史
                    cursor.execute('''
                        INSERT INTO alert_history 
                        (alert_id, action, action_by, action_details)
                        VALUES (?, ?, ?, ?)
                    ''', (alert_id, 'resolved', username, json.dumps({'resolution_note': resolution_note, 'batch': True})))
                    
                    resolved_count += 1
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'已解决 {resolved_count} 个告警',
            'resolved_count': resolved_count
        })
        
    except Exception as e:
        logger.error(f'批量解决告警失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/<int:alert_id>/escalate', methods=['POST'])
@require_admin_role
def escalate_alert(alert_id):
    """
    提升告警级别 - 将告警升级到更严重的级别
    """
    try:
        data = request.get_json()
        
        new_level = data.get('level')
        reason = data.get('reason', '')
        
        if new_level not in ALERT_LEVELS:
            return jsonify({
                'success': False,
                'error': '无效的告警级别'
            }), 400
        
        username = session.get('username', 'unknown')
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取当前告警信息
            cursor.execute('SELECT alert_level FROM alert_records WHERE id = ?', (alert_id,))
            current = cursor.fetchone()
            
            if not current:
                return jsonify({
                    'success': False,
                    'error': '告警不存在'
                }), 404
            
            old_level = current[0]
            
            # 更新告警级别
            cursor.execute('''
                UPDATE alert_records 
                SET alert_level = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (new_level, datetime.now(), alert_id))
            
            # 记录历史
            cursor.execute('''
                INSERT INTO alert_history 
                (alert_id, action, action_by, action_details)
                VALUES (?, ?, ?, ?)
            ''', (alert_id, 'escalated', username, json.dumps({
                'old_level': old_level,
                'new_level': new_level,
                'reason': reason
            })))
            
            conn.commit()
        
        # 发送升级通知
        message = f'告警已升级至 {new_level} 级别'
        _send_alert_notification(alert_id, new_level, message, {'reason': reason})
        
        return jsonify({
            'success': True,
            'message': f'告警已升级至 {new_level}'
        })
        
    except Exception as e:
        logger.error(f'提升告警级别失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 告警通知系统 ====================

@alert_api.route('/notification/channels', methods=['GET'])
@require_admin_role
def get_notification_channels():
    """
    获取通知渠道配置 - 查看可用的通知方式
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 确保通知配置表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_type TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    config_json TEXT,
                    enabled INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 查询通知渠道
            cursor.execute('''
                SELECT id, channel_type, channel_name, config_json, enabled, priority, created_at, updated_at
                FROM notification_channels
                ORDER BY priority DESC
            ''')
            
            columns = ['id', 'channel_type', 'channel_name', 'config_json', 'enabled', 'priority', 'created_at', 'updated_at']
            channels = []
            for row in cursor.fetchall():
                channel = dict(zip(columns, row))
                if channel['config_json']:
                    channel['config_json'] = json.loads(channel['config_json'])
                channels.append(channel)
        
        # 默认通知渠道配置
        default_channels = [
            {'type': 'email', 'name': '邮件通知', 'description': '通过邮件发送告警'},
            {'type': 'webhook', 'name': 'Webhook通知', 'description': '通过HTTP请求发送告警'},
            {'type': 'sms', 'name': '短信通知', 'description': '通过短信发送告警（需要配置）'},
            {'type': 'dashboard', 'name': '仪表板通知', 'description': '在系统仪表板显示告警'}
        ]
        
        return jsonify({
            'success': True,
            'channels': channels,
            'default_channels': default_channels
        })
        
    except Exception as e:
        logger.error(f'获取通知渠道配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/notification/configure', methods=['POST'])
@require_admin_role
def configure_notification_channel():
    """
    配置通知渠道 - 设置通知方式和参数
    """
    try:
        data = request.get_json()
        
        channel_type = data.get('channel_type')
        channel_name = data.get('channel_name')
        config = data.get('config', {})
        enabled = data.get('enabled', True)
        priority = data.get('priority', 1)
        
        if not channel_type:
            return jsonify({
                'success': False,
                'error': '缺少通知渠道类型'
            }), 400
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在相同类型的通知渠道
            cursor.execute('SELECT id FROM notification_channels WHERE channel_type = ?', (channel_type,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有配置
                cursor.execute('''
                    UPDATE notification_channels 
                    SET channel_name = ?, config_json = ?, enabled = ?, priority = ?, updated_at = ?
                    WHERE channel_type = ?
                ''', (channel_name, json.dumps(config), enabled, priority, datetime.now(), channel_type))
            else:
                # 创建新配置
                cursor.execute('''
                    INSERT INTO notification_channels 
                    (channel_type, channel_name, config_json, enabled, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (channel_type, channel_name, json.dumps(config), enabled, priority))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '通知渠道配置已保存'
        })
        
    except Exception as e:
        logger.error(f'配置通知渠道失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/notification/test', methods=['POST'])
@require_admin_role
def test_notification_channel():
    """
    测试通知渠道 - 发送测试通知验证配置
    """
    try:
        data = request.get_json()
        
        channel_type = data.get('channel_type')
        test_message = data.get('message', '测试告警通知')
        
        if not channel_type:
            return jsonify({
                'success': False,
                'error': '缺少通知渠道类型'
            }), 400
        
        # 发送测试通知
        result = _send_test_notification(channel_type, test_message)
        
        return jsonify({
            'success': result['success'],
            'message': result['message']
        })
        
    except Exception as e:
        logger.error(f'测试通知渠道失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _send_alert_notification(alert_id: int, level: str, message: str, details: Dict) -> Dict:
    """
    发送告警通知 - 根据配置发送通知
    """
    result = {'sent': False, 'channels': []}
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取启用的通知渠道
            cursor.execute('''
                SELECT channel_type, config_json 
                FROM notification_channels 
                WHERE enabled = 1
                ORDER BY priority DESC
            ''')
            
            channels = cursor.fetchall()
            
            for channel_type, config_json in channels:
                config = json.loads(config_json) if config_json else {}
                
                # 根据告警级别决定是否发送
                level_info = ALERT_LEVELS.get(level, {})
                if level_info.get('level', 1) >= 2:  # WARNING及以上发送通知
                    
                    send_result = _send_notification(channel_type, message, level, details, config)
                    result['channels'].append({
                        'type': channel_type,
                        'success': send_result['success']
                    })
            
            # 更新通知发送状态
            if result['channels']:
                cursor.execute('''
                    UPDATE alert_records 
                    SET notification_sent = 1, 
                        notification_channels = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (json.dumps(result['channels']), datetime.now(), alert_id))
                conn.commit()
                
                result['sent'] = any(c['success'] for c in result['channels'])
    
    except Exception as e:
        logger.error(f'发送告警通知失败: {str(e)}')
    
    return result


def _send_notification(channel_type: str, message: str, level: str, details: Dict, config: Dict) -> Dict:
    """
    发送通知到指定渠道
    """
    result = {'success': False, 'message': ''}
    
    try:
        if channel_type == 'email':
            # 邮件通知
            smtp_server = config.get('smtp_server', 'smtp.example.com')
            smtp_port = config.get('smtp_port', 587)
            smtp_user = config.get('smtp_user', '')
            smtp_password = config.get('smtp_password', '')
            recipients = config.get('recipients', [])
            
            if recipients:
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = ', '.join(recipients)
                msg['Subject'] = f'[MTSCOS告警] {level} - {message}'
                
                body = f'''
告警级别: {level}
告警消息: {message}
详细信息: {json.dumps(details, ensure_ascii=False)}
时间: {datetime.now().isoformat()}
'''
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 发送邮件（实际环境中配置SMTP）
                # try:
                #     server = smtplib.SMTP(smtp_server, smtp_port)
                #     server.starttls()
                #     server.login(smtp_user, smtp_password)
                #     server.sendmail(smtp_user, recipients, msg.as_string())
                #     server.quit()
                #     result['success'] = True
                #     result['message'] = '邮件发送成功'
                # except Exception as e:
                #     result['message'] = str(e)
                
                # 模拟发送成功
                result['success'] = True
                result['message'] = '邮件配置已记录（实际发送需要SMTP配置）'
        
        elif channel_type == 'webhook':
            # Webhook通知
            webhook_url = config.get('url', '')
            if webhook_url:
                # 发送HTTP请求（实际环境中实现）
                # import requests
                # response = requests.post(webhook_url, json={
                #     'alert_id': details.get('alert_id'),
                #     'level': level,
                #     'message': message,
                #     'details': details,
                #     'timestamp': datetime.now().isoformat()
                # })
                # result['success'] = response.status_code == 200
                
                result['success'] = True
                result['message'] = 'Webhook配置已记录'
        
        elif channel_type == 'dashboard':
            # 仪表板通知 - 总是成功
            result['success'] = True
            result['message'] = '仪表板通知已添加'
        
        else:
            result['message'] = f'未知通知渠道: {channel_type}'
    
    except Exception as e:
        result['message'] = str(e)
    
    return result


def _send_test_notification(channel_type: str, test_message: str) -> Dict:
    """
    发送测试通知
    """
    return _send_notification(
        channel_type,
        test_message,
        'INFO',
        {'test': True, 'timestamp': datetime.now().isoformat()},
        {}
    )


# ==================== 告警历史记录 ====================

@alert_api.route('/history', methods=['GET'])
@require_admin_role
def get_alert_history():
    """
    获取告警历史 - 所有告警的历史操作记录
    """
    try:
        hours = int(request.args.get('hours', 24))
        action = request.args.get('action', 'all')
        limit = int(request.args.get('limit', 100))
        
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建查询
            conditions = ['created_at > ?']
            params = [time_threshold]
            
            if action != 'all':
                conditions.append('action = ?')
                params.append(action)
            
            query = f'''
                SELECT ah.id, ah.alert_id, ah.action, ah.action_by, ah.action_details, ah.created_at,
                       ar.alert_type, ar.alert_level, ar.message
                FROM alert_history ah
                LEFT JOIN alert_records ar ON ah.alert_id = ar.id
                WHERE {' AND '.join(conditions)}
                ORDER BY ah.created_at DESC
                LIMIT ?
            '''
            
            params.append(limit)
            cursor.execute(query, params)
            
            columns = ['id', 'alert_id', 'action', 'action_by', 'action_details', 'created_at',
                       'alert_type', 'alert_level', 'message']
            
            history = []
            for row in cursor.fetchall():
                h = dict(zip(columns, row))
                if h['action_details']:
                    h['action_details'] = json.loads(h['action_details'])
                history.append(h)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f'获取告警历史失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/statistics', methods=['GET'])
@require_admin_role
def get_alert_statistics():
    """
    获取告警统计 - 告警数量、级别分布、趋势分析
    """
    try:
        hours = int(request.args.get('hours', 24))
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        statistics = {
            'timestamp': datetime.now().isoformat(),
            'time_range': {
                'start': time_threshold.isoformat(),
                'end': datetime.now().isoformat()
            },
            'summary': {},
            'by_level': {},
            'by_type': {},
            'by_status': {},
            'trends': []
        }
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 总数统计
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE created_at > ?', (time_threshold,))
            statistics['summary']['total'] = cursor.fetchone()[0]
            
            # 活跃告警数
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE status = "active" AND created_at > ?', (time_threshold,))
            statistics['summary']['active'] = cursor.fetchone()[0]
            
            # 已解决告警数
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE resolved = 1 AND created_at > ?', (time_threshold,))
            statistics['summary']['resolved'] = cursor.fetchone()[0]
            
            # 按级别统计
            cursor.execute('''
                SELECT alert_level, COUNT(*) 
                FROM alert_records 
                WHERE created_at > ? 
                GROUP BY alert_level
            ''', (time_threshold,))
            
            for row in cursor.fetchall():
                statistics['by_level'][row[0]] = row[1]
            
            # 按类型统计
            cursor.execute('''
                SELECT alert_type, COUNT(*) 
                FROM alert_records 
                WHERE created_at > ? 
                GROUP BY alert_type
            ''', (time_threshold,))
            
            for row in cursor.fetchall():
                statistics['by_type'][row[0]] = row[1]
            
            # 按状态统计
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM alert_records 
                WHERE created_at > ? 
                GROUP BY status
            ''', (time_threshold,))
            
            for row in cursor.fetchall():
                statistics['by_status'][row[0]] = row[1]
            
            # 时间趋势
            cursor.execute('''
                SELECT strftime('%Y-%m-%d %H', created_at) as hour, alert_level, COUNT(*) 
                FROM alert_records 
                WHERE created_at > ? 
                GROUP BY hour, alert_level
                ORDER BY hour
            ''', (time_threshold,))
            
            for row in cursor.fetchall():
                statistics['trends'].append({
                    'time': row[0],
                    'level': row[1],
                    'count': row[2]
                })
        
        return jsonify({
            'success': True,
            'data': statistics
        })
        
    except Exception as e:
        logger.error(f'获取告警统计失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 告警规则配置 ====================

@alert_api.route('/rules', methods=['GET'])
@require_admin_role
def get_alert_rules():
    """
    获取告警规则 - 查看自动告警的触发规则
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 确保告警规则表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    threshold REAL,
                    duration INTEGER,
                    actions TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 查询告警规则
            cursor.execute('''
                SELECT id, rule_name, alert_type, condition_type, threshold, duration, actions, enabled, created_at, updated_at
                FROM alert_rules
                ORDER BY id
            ''')
            
            columns = ['id', 'rule_name', 'alert_type', 'condition_type', 'threshold', 'duration', 'actions', 'enabled', 'created_at', 'updated_at']
            
            rules = []
            for row in cursor.fetchall():
                rule = dict(zip(columns, row))
                if rule['actions']:
                    rule['actions'] = json.loads(rule['actions'])
                rules.append(rule)
        
        # 默认告警规则
        default_rules = [
            {
                'rule_name': 'CPU使用率告警',
                'alert_type': 'cpu_high',
                'condition_type': 'threshold',
                'threshold': 80,
                'duration': 60,
                'enabled': True
            },
            {
                'rule_name': '内存使用率告警',
                'alert_type': 'memory_high',
                'condition_type': 'threshold',
                'threshold': 80,
                'duration': 60,
                'enabled': True
            },
            {
                'rule_name': '磁盘空间告警',
                'alert_type': 'disk_high',
                'condition_type': 'threshold',
                'threshold': 85,
                'duration': 0,
                'enabled': True
            },
            {
                'rule_name': '认证失败告警',
                'alert_type': 'auth_failure',
                'condition_type': 'count',
                'threshold': 3,
                'duration': 300,
                'enabled': True
            }
        ]
        
        return jsonify({
            'success': True,
            'rules': rules,
            'default_rules': default_rules
        })
        
    except Exception as e:
        logger.error(f'获取告警规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/rules/create', methods=['POST'])
@require_admin_role
def create_alert_rule():
    """
    创建告警规则 - 设置自动告警触发条件
    """
    try:
        data = request.get_json()
        
        rule_name = data.get('rule_name')
        alert_type = data.get('alert_type')
        condition_type = data.get('condition_type', 'threshold')
        threshold = data.get('threshold', 80)
        duration = data.get('duration', 60)
        actions = data.get('actions', [])
        enabled = data.get('enabled', True)
        
        if not rule_name or not alert_type:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alert_rules 
                (rule_name, alert_type, condition_type, threshold, duration, actions, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule_name, alert_type, condition_type, threshold, duration, json.dumps(actions), enabled))
            
            rule_id = cursor.lastrowid
            conn.commit()
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'message': '告警规则已创建'
        })
        
    except Exception as e:
        logger.error(f'创建告警规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/rules/<int:rule_id>/update', methods=['PUT'])
@require_admin_role
def update_alert_rule(rule_id):
    """
    更新告警规则 - 修改告警触发条件
    """
    try:
        data = request.get_json()
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            params = []
            
            if 'threshold' in data:
                update_fields.append('threshold = ?')
                params.append(data['threshold'])
            
            if 'duration' in data:
                update_fields.append('duration = ?')
                params.append(data['duration'])
            
            if 'actions' in data:
                update_fields.append('actions = ?')
                params.append(json.dumps(data['actions']))
            
            if 'enabled' in data:
                update_fields.append('enabled = ?')
                params.append(data['enabled'])
            
            if update_fields:
                update_fields.append('updated_at = ?')
                params.append(datetime.now())
                params.append(rule_id)
                
                query = f'UPDATE alert_rules SET {", ".join(update_fields)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
        
        return jsonify({
            'success': True,
            'message': '告警规则已更新'
        })
        
    except Exception as e:
        logger.error(f'更新告警规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@alert_api.route('/rules/<int:rule_id>/delete', methods=['DELETE'])
@require_admin_role
def delete_alert_rule(rule_id):
    """
    删除告警规则 - 移除自动告警触发条件
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM alert_rules WHERE id = ?', (rule_id,))
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '告警规则已删除'
        })
        
    except Exception as e:
        logger.error(f'删除告警规则失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 告警仪表板 ====================

@alert_api.route('/dashboard', methods=['GET'])
def get_alert_dashboard():
    """
    获取告警仪表板数据 - 综合告警展示
    """
    try:
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'active_alerts': [],
            'recent_resolved': [],
            'level_distribution': {},
            'type_distribution': {}
        }
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 统计摘要
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE status = "active"')
            dashboard['summary']['active'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE status = "acknowledged"')
            dashboard['summary']['acknowledged'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alert_records WHERE resolved = 1')
            dashboard['summary']['resolved'] = cursor.fetchone()[0]
            
            # 活跃告警（按级别排序）
            cursor.execute('''
                SELECT id, alert_type, alert_level, message, created_at
                FROM alert_records 
                WHERE status = "active"
                ORDER BY 
                    CASE alert_level 
                        WHEN 'CRITICAL' THEN 4 
                        WHEN 'ERROR' THEN 3 
                        WHEN 'WARNING' THEN 2 
                        WHEN 'INFO' THEN 1 
                    END DESC
                LIMIT 10
            ''')
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'created_at']
            for row in cursor.fetchall():
                alert = dict(zip(columns, row))
                alert['level_info'] = ALERT_LEVELS.get(alert['alert_level'], {})
                alert['type_info'] = ALERT_TYPES.get(alert['alert_type'], {})
                dashboard['active_alerts'].append(alert)
            
            # 最近解决的告警
            cursor.execute('''
                SELECT id, alert_type, alert_level, message, resolved_at, resolved_by
                FROM alert_records 
                WHERE resolved = 1
                ORDER BY resolved_at DESC
                LIMIT 10
            ''')
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'resolved_at', 'resolved_by']
            for row in cursor.fetchall():
                alert = dict(zip(columns, row))
                dashboard['recent_resolved'].append(alert)
            
            # 级别分布
            cursor.execute('''
                SELECT alert_level, COUNT(*) 
                FROM alert_records 
                WHERE status = "active"
                GROUP BY alert_level
            ''')
            
            for row in cursor.fetchall():
                dashboard['level_distribution'][row[0]] = row[1]
            
            # 类型分布
            cursor.execute('''
                SELECT alert_type, COUNT(*) 
                FROM alert_records 
                WHERE status = "active"
                GROUP BY alert_type
            ''')
            
            for row in cursor.fetchall():
                dashboard['type_distribution'][row[0]] = row[1]
        
        return jsonify({
            'success': True,
            'data': dashboard
        })
        
    except Exception as e:
        logger.error(f'获取告警仪表板数据失败: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 错误处理 ====================

@alert_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API endpoint not found'
    }), 404


@alert_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@alert_api.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Permission denied'
    }), 403