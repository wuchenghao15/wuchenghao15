# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
审批流程优化系统 - 完善审批规则和流程管理
"""

import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def log(message: str, symbol: str = '📋'):
    """日志记录"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} {message}")


def create_approval_tables():
    """创建审批相关表"""
    log('创建审批相关表...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS approval_requests (
            id TEXT PRIMARY KEY,
            type TEXT,
            title TEXT,
            description TEXT,
            requester_id INTEGER,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'normal',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS approval_flows (
            id TEXT PRIMARY KEY,
            request_id TEXT,
            step INTEGER,
            assignee_role TEXT,
            assignee_id INTEGER,
            action TEXT,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS approval_rules (
            id TEXT PRIMARY KEY,
            rule_code TEXT UNIQUE,
            rule_name TEXT,
            rule_description TEXT,
            rule_type TEXT,
            rule_value TEXT,
            is_active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 100,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS approval_notifications (
            id TEXT PRIMARY KEY,
            request_id TEXT,
            user_id INTEGER,
            type TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )'''
    ]
    
    for sql in tables:
        try:
            cursor.execute(sql)
            log(f'  ✅ 表创建成功', '✅')
        except Exception as e:
            log(f'  ❌ 表创建失败: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'审批表创建完成', '✅')


def optimize_approval_rules():
    """优化审批规则"""
    log('优化审批规则...', '📋')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    approval_rules = [
        # 审批类型配置
        ('approval_types', '审批类型', '支持的审批类型', 'json', json.dumps([
            {'type': 'exam_pause', 'name': '考试暂停申请', 'description': '学生申请暂停考试'},
            {'type': 'exam_extension', 'name': '考试延期申请', 'description': '申请延长考试时间'},
            {'type': 'score_appeal', 'name': '成绩申诉', 'description': '对考试成绩提出申诉'},
            {'type': 'question_review', 'name': '题目审核', 'description': '审核新题目'},
            {'type': 'user_registration', 'name': '用户注册审核', 'description': '审核新用户注册'},
            {'type': 'system_change', 'name': '系统变更', 'description': '系统配置变更审批'}
        ])),
        
        # 审批流程配置
        ('approval_flow_exam_pause', '考试暂停流程', '考试暂停申请的审批流程', 'json', json.dumps([
            {'step': 1, 'role': 'teacher', 'required': True, 'timeout': 30},
            {'step': 2, 'role': 'proctor', 'required': False, 'timeout': 15}
        ])),
        
        ('approval_flow_score_appeal', '成绩申诉流程', '成绩申诉的审批流程', 'json', json.dumps([
            {'step': 1, 'role': 'teacher', 'required': True, 'timeout': 120},
            {'step': 2, 'role': 'professor', 'required': False, 'timeout': 120}
        ])),
        
        ('approval_flow_question_review', '题目审核流程', '新题目审核流程', 'json', json.dumps([
            {'step': 1, 'role': 'teacher', 'required': True, 'timeout': 300},
            {'step': 2, 'role': 'researcher', 'required': True, 'timeout': 300}
        ])),
        
        # 审批超时配置
        ('approval_timeout_pending', '待处理超时', '等待审批超时时间(分钟)', 'number', '30'),
        ('approval_timeout_escalation', '升级超时', '超时后升级到上级审批(分钟)', 'number', '60'),
        ('approval_timeout_auto_approve', '自动批准超时', '自动批准超时时间(分钟)', 'number', '1440'),
        
        # 审批通知配置
        ('approval_notification_create', '创建通知', '创建审批时发送通知', 'boolean', 'true'),
        ('approval_notification_update', '更新通知', '审批状态变更时发送通知', 'boolean', 'true'),
        ('approval_notification_timeout', '超时通知', '审批超时时发送通知', 'boolean', 'true'),
        ('approval_notification_reminder', '提醒通知', '定期发送提醒通知', 'boolean', 'true'),
        ('approval_notification_interval', '提醒间隔', '提醒通知间隔(分钟)', 'number', '30'),
        
        # 审批权限配置
        ('approval_permission_student', '学生审批权限', '学生可发起的审批类型', 'json', json.dumps([
            {'type': 'exam_pause', 'allowed': True},
            {'type': 'exam_extension', 'allowed': True},
            {'type': 'score_appeal', 'allowed': True}
        ])),
        
        ('approval_permission_teacher', '教师审批权限', '教师可处理的审批类型', 'json', json.dumps([
            {'type': 'exam_pause', 'can_approve': True},
            {'type': 'score_appeal', 'can_approve': True},
            {'type': 'question_review', 'can_approve': True}
        ])),
        
        ('approval_permission_professor', '教授审批权限', '教授可处理的审批类型', 'json', json.dumps([
            {'type': 'score_appeal', 'can_approve': True},
            {'type': 'question_review', 'can_approve': True},
            {'type': 'system_change', 'can_approve': True}
        ])),
        
        ('approval_permission_admin', '管理员审批权限', '管理员可处理的审批类型', 'json', json.dumps([
            {'type': '*', 'can_approve': True}
        ])),
        
        # 审批优先级配置
        ('approval_priority_levels', '优先级等级', '审批优先级配置', 'json', json.dumps([
            {'level': 'low', 'name': '低', 'color': '#48bb78'},
            {'level': 'normal', 'name': '普通', 'color': '#4299e1'},
            {'level': 'high', 'name': '高', 'color': '#ed8936'},
            {'level': 'urgent', 'name': '紧急', 'color': '#fc8181'}
        ])),
        
        # 审批限制配置
        ('approval_max_pending_per_user', '用户待处理上限', '单个用户最大待处理审批数', 'number', '10'),
        ('approval_max_daily_requests', '每日申请上限', '单个用户每日最大申请数', 'number', '5'),
        ('approval_cool_down_period', '冷却期', '相同类型申请的冷却时间(分钟)', 'number', '30'),
        
        # 审批升级规则
        ('approval_escalation_enabled', '启用升级', '超时自动升级', 'boolean', 'true'),
        ('approval_escalation_levels', '升级层级', '升级审批层级配置', 'json', json.dumps([
            {'level': 1, 'role': 'teacher', 'timeout': 30},
            {'level': 2, 'role': 'professor', 'timeout': 60},
            {'level': 3, 'role': 'admin', 'timeout': 120}
        ])),
        
        # 审批统计配置
        ('approval_stats_enabled', '启用统计', '启用审批统计分析', 'boolean', 'true'),
        ('approval_stats_period', '统计周期', '统计分析周期(天)', 'number', '7'),
    ]
    
    for code, name, desc, rtype, value in approval_rules:
        try:
            cursor.execute('SELECT id FROM approval_rules WHERE rule_code = ?', (code,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE approval_rules 
                    SET rule_name = ?, rule_description = ?, rule_type = ?, rule_value = ?
                    WHERE rule_code = ?
                ''', (name, desc, rtype, value, code))
            else:
                cursor.execute('''
                    INSERT INTO approval_rules 
                    (id, rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), code, name, desc, rtype, value, 1, 100))
            
            log(f'  ✅ {name}', '✅')
        except Exception as e:
            log(f'  ❌ {name}: {str(e)}', '❌')
    
    conn.commit()
    conn.close()
    log(f'审批规则优化完成: {len(approval_rules)} 条规则', '✅')


def create_approval_api():
    """创建审批API代码"""
    api_code = '''#!/usr/bin/env python3
"""
审批流程API - Flask Blueprint
"""

from flask import Blueprint, request, jsonify, session
import json
import uuid
from datetime import datetime
import sqlite3

approval_api = Blueprint('approval_api', __name__, url_prefix='/api/approval')

DATABASE_PATH = 'app.db'


def get_db():
    return sqlite3.connect(DATABASE_PATH)


@approval_api.route('/request', methods=['POST'])
def create_request():
    """创建审批请求"""
    data = request.json
    user_id = session.get('user_id', 1)
    
    request_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO approval_requests (id, type, title, description, requester_id, status, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (request_id, data.get('type', 'exam_pause'), data.get('title', ''), data.get('description', ''), user_id, 'pending', data.get('priority', 'normal'), now, now)
    )
    
    # 创建审批流程第一步
    cursor.execute(
        'INSERT INTO approval_flows (id, request_id, step, assignee_role, action) VALUES (?, ?, ?, ?, ?)',
        (str(uuid.uuid4()), request_id, 1, 'teacher', 'pending')
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'request_id': request_id,
        'message': '审批请求已创建'
    })


@approval_api.route('/requests', methods=['GET'])
def get_requests():
    """获取审批列表"""
    status = request.args.get('status', 'all')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if status == 'all':
        cursor.execute('SELECT * FROM approval_requests ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC', (status,))
    
    requests = []
    for row in cursor.fetchall():
        requests.append({
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'requester_id': row[4],
            'status': row[5],
            'priority': row[6],
            'created_at': row[7]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': requests
    })


@approval_api.route('/request/<request_id>', methods=['GET'])
def get_request(request_id):
    """获取单个审批详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM approval_requests WHERE id = ?', (request_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'success': False, 'message': '审批不存在'}), 404
    
    # 获取审批流程
    cursor.execute('SELECT * FROM approval_flows WHERE request_id = ? ORDER BY step', (request_id,))
    flows = []
    for flow_row in cursor.fetchall():
        flows.append({
            'step': flow_row[2],
            'assignee_role': flow_row[3],
            'action': flow_row[5],
            'comment': flow_row[6],
            'created_at': flow_row[7]
        })
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'requester_id': row[4],
            'status': row[5],
            'priority': row[6],
            'created_at': row[7],
            'flows': flows
        }
    })


@approval_api.route('/request/<request_id>/action', methods=['POST'])
def approve_request(request_id):
    """处理审批请求"""
    data = request.json
    action = data.get('action')  # approve, reject
    comment = data.get('comment', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 更新审批状态
    cursor.execute('UPDATE approval_requests SET status = ?, updated_at = ? WHERE id = ?', 
                  (action, datetime.now().isoformat(), request_id))
    
    # 更新当前审批步骤
    cursor.execute('UPDATE approval_flows SET action = ?, comment = ? WHERE request_id = ? AND action = "pending"',
                  (action, comment, request_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '审批已处理'
    })


@approval_api.route('/types', methods=['GET'])
def get_types():
    """获取审批类型"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT rule_value FROM approval_rules WHERE rule_code = "approval_types"')
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return jsonify({'success': True, 'data': json.loads(row[0])})
    return jsonify({'success': False, 'data': []})


@approval_api.route('/stats', methods=['GET'])
def get_stats():
    """获取审批统计"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT status, COUNT(*) FROM approval_requests GROUP BY status')
    stats = {}
    for row in cursor.fetchall():
        stats[row[0]] = row[1]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': stats
    })
'''
    
    print('  ✅ 审批API代码已生成')
    return api_code


def create_approval_management_page():
    """创建审批管理页面"""
    page_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>审批管理系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .stat-card.pending { border-left: 4px solid #ed8936; }
        .stat-card.approved { border-left: 4px solid #48bb78; }
        .stat-card.rejected { border-left: 4px solid #fc8181; }
        .stat-card.total { border-left: 4px solid #4299e1; }
        .stat-value { font-size: 32px; font-weight: 700; color: #333; margin-bottom: 8px; }
        .stat-label { font-size: 14px; color: #666; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 12px 24px; background: white; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: 500; }
        .tab.active { background: #667eea; color: white; }
        .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
        .card h2 { font-size: 18px; margin-bottom: 16px; color: #333; }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        .table th { background: #f8fafc; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; }
        .badge.pending { background: #fefcbf; color: #744210; }
        .badge.approved { background: #c6f6d5; color: #276749; }
        .badge.rejected { background: #fed7d7; color: #c53030; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; }
        .btn-approve { background: #48bb78; color: white; }
        .btn-reject { background: #fc8181; color: white; }
        .btn-primary { background: #667eea; color: white; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 15% auto; padding: 24px; border-radius: 12px; width: 90%; max-width: 500px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 6px; }
        .form-group select, .form-group input, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 审批管理系统</h1>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card total"><div class="stat-value" id="total">0</div><div class="stat-label">总审批数</div></div>
            <div class="stat-card pending"><div class="stat-value" id="pending">0</div><div class="stat-label">待处理</div></div>
            <div class="stat-card approved"><div class="stat-value" id="approved">0</div><div class="stat-label">已通过</div></div>
            <div class="stat-card rejected"><div class="stat-value" id="rejected">0</div><div class="stat-label">已拒绝</div></div>
        </div>
        
        <div class="tabs">
            <button class="tab active" data-tab="requests">审批列表</button>
            <button class="tab" data-tab="create">发起审批</button>
            <button class="tab" data-tab="rules">审批规则</button>
        </div>
        
        <div id="requests" class="tab-content active">
            <div class="card">
                <h2>审批列表</h2>
                <div style="display: flex; gap: 10px; margin-bottom: 16px;">
                    <button class="btn btn-primary" onclick="filterRequests('all')">全部</button>
                    <button class="btn" style="background: #fefcbf;" onclick="filterRequests('pending')">待处理</button>
                    <button class="btn" style="background: #c6f6d5;" onclick="filterRequests('approved')">已通过</button>
                    <button class="btn" style="background: #fed7d7;" onclick="filterRequests('rejected')">已拒绝</button>
                </div>
                <table class="table">
                    <thead><tr><th>标题</th><th>类型</th><th>优先级</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
                    <tbody id="requestList"></tbody>
                </table>
            </div>
        </div>
        
        <div id="create" class="tab-content">
            <div class="card">
                <h2>发起审批</h2>
                <div class="form-group">
                    <label>审批类型</label>
                    <select id="reqType">
                        <option value="exam_pause">考试暂停申请</option>
                        <option value="exam_extension">考试延期申请</option>
                        <option value="score_appeal">成绩申诉</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>标题</label>
                    <input type="text" id="reqTitle" placeholder="请输入审批标题">
                </div>
                <div class="form-group">
                    <label>描述</label>
                    <textarea id="reqDesc" rows="4" placeholder="请详细描述申请原因"></textarea>
                </div>
                <div class="form-group">
                    <label>优先级</label>
                    <select id="reqPriority">
                        <option value="low">低</option>
                        <option value="normal">普通</option>
                        <option value="high">高</option>
                        <option value="urgent">紧急</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="createRequest()">提交申请</button>
            </div>
        </div>
        
        <div id="rules" class="tab-content">
            <div class="card">
                <h2>审批规则设置</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                        <h4>待处理超时</h4>
                        <p style="color: #666;">30分钟</p>
                    </div>
                    <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                        <h4>升级超时</h4>
                        <p style="color: #666;">60分钟</p>
                    </div>
                    <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                        <h4>自动批准超时</h4>
                        <p style="color: #666;">1440分钟</p>
                    </div>
                    <div style="padding: 16px; background: #f8fafc; border-radius: 8px;">
                        <h4>提醒间隔</h4>
                        <p style="color: #666;">30分钟</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="actionModal">
        <div class="modal-content">
            <h3>处理审批</h3>
            <input type="hidden" id="currentRequestId">
            <div class="form-group">
                <label>处理方式</label>
                <select id="actionType">
                    <option value="approve">通过</option>
                    <option value="reject">拒绝</option>
                </select>
            </div>
            <div class="form-group">
                <label>备注</label>
                <textarea id="actionComment" rows="3"></textarea>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="btn btn-approve" onclick="handleApproval()">确认处理</button>
                <button class="btn" style="background: #e2e8f0;" onclick="closeModal()">取消</button>
            </div>
        </div>
    </div>

    <script>
        const mockRequests = [
            { id: '1', title: '考试暂停申请', type: 'exam_pause', priority: 'high', status: 'pending', time: '2024-01-15 10:30' },
            { id: '2', title: '成绩申诉', type: 'score_appeal', priority: 'normal', status: 'pending', time: '2024-01-15 09:15' },
            { id: '3', title: '考试延期申请', type: 'exam_extension', priority: 'urgent', status: 'approved', time: '2024-01-14 16:45' },
            { id: '4', title: '成绩申诉', type: 'score_appeal', priority: 'normal', status: 'rejected', time: '2024-01-14 14:20' },
            { id: '5', title: '考试暂停申请', type: 'exam_pause', priority: 'low', status: 'pending', time: '2024-01-15 11:00' },
        ];
        
        function loadStats() {
            document.getElementById('total').textContent = mockRequests.length;
            document.getElementById('pending').textContent = mockRequests.filter(r => r.status === 'pending').length;
            document.getElementById('approved').textContent = mockRequests.filter(r => r.status === 'approved').length;
            document.getElementById('rejected').textContent = mockRequests.filter(r => r.status === 'rejected').length;
        }
        
        function filterRequests(status) {
            const filtered = status === 'all' ? mockRequests : mockRequests.filter(r => r.status == status);
            renderRequests(filtered);
        }
        
        function renderRequests(requests) {
            const tbody = document.getElementById('requestList');
            tbody.innerHTML = requests.map(req => `
                <tr>
                    <td>${req.title}</td>
                    <td>${req.type === 'exam_pause' ? '考试暂停' : req.type === 'score_appeal' ? '成绩申诉' : '考试延期'}</td>
                    <td><span class="badge" style="background: ${req.priority === 'urgent' ? '#fed7d7' : req.priority === 'high' ? '#fefcbf' : '#c6f6d5'}">${req.priority === 'urgent' ? '紧急' : req.priority === 'high' ? '高' : req.priority === 'low' ? '低' : '普通'}</span></td>
                    <td><span class="badge ${req.status}">${req.status === 'pending' ? '待处理' : req.status === 'approved' ? '已通过' : '已拒绝'}</span></td>
                    <td>${req.time}</td>
                    <td>${req.status === 'pending' ? '<button class="btn btn-approve" onclick="openActionModal(\'' + req.id + '\')">处理</button>' : '-'}</td>
                </tr>
            `).join('');
        }
        
        function openActionModal(id) {
            document.getElementById('currentRequestId').value = id;
            document.getElementById('actionModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('actionModal').style.display = 'none';
        }
        
        function handleApproval() {
            const id = document.getElementById('currentRequestId').value;
            const action = document.getElementById('actionType').value;
            const comment = document.getElementById('actionComment').value;
            alert(`审批 ${id} 已${action === 'approve' ? '通过' : '拒绝'}`);
            closeModal();
            loadStats();
            filterRequests('all');
        }
        
        function createRequest() {
            const type = document.getElementById('reqType').value;
            const title = document.getElementById('reqTitle').value;
            const desc = document.getElementById('reqDesc').value;
            const priority = document.getElementById('reqPriority').value;
            
            if (!title) {
                alert('请输入标题');
                return;
            }
            
            alert('审批申请已提交');
            document.getElementById('reqTitle').value = '';
            document.getElementById('reqDesc').value = '';
            loadStats();
        }
        
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                document.getElementById(this.dataset.tab).classList.add('active');
            });
        });
        
        loadStats();
        filterRequests('all');
    </script>
</body>
</html>'''
    
    with open('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/templates/approval_management.html', 'w', encoding='utf-8') as f:
        f.write(page_content)
    
    log('  ✅ 审批管理页面已创建', '✅')


def main():
    """主函数"""
    print('\n' + '='*60)
    print('📋 审批流程优化')
    print('='*60 + '\n')
    
    # 1. 创建审批相关表
    create_approval_tables()
    
    # 2. 优化审批规则
    optimize_approval_rules()
    
    # 3. 创建审批API
    create_approval_api()
    
    # 4. 创建审批管理页面
    create_approval_management_page()
    
    print('\n' + '='*60)
    log('审批流程优化完成!', '✅')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
