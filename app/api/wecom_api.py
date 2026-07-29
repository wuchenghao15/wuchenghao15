#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信 API 接口模块
WeCom API - 提供企业微信集成的 RESTful 接口

功能：
- 配置管理（corpid/corpsecret/agentid）
- Webhook 回调（消息接收、事件推送）
- 消息发送 API
- 审批管理 API
- 通讯录管理 API
- 日程会议 API
- 智能 AI 员工接口
- 系统状态监控

作者: MTSCOS AI 系统
版本: v1.0.0
"""

import os
import sys
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

wecom_api = Blueprint('wecom_api', __name__)

# ==================== 全局状态 ====================

_wecom_client = None
_ai_employees = {}
_config_cache = {}


def _get_wecom_client():
    """获取企业微信客户端"""
    global _wecom_client
    if _wecom_client is None:
        try:
            from core.services.wecom_client import get_wecom_client
            _wecom_client = get_wecom_client()
        except Exception as e:
            logger.warning(f"[WeComAPI] 初始化客户端失败: {e}")
    return _wecom_client


def _init_ai_employees():
    """初始化 AI 员工"""
    global _ai_employees
    if not _ai_employees:
        try:
            from ai_engines.wecom_ai_employee import (
                WeComMessageRouter,
                WeComApprovalAutomation,
                WeComContactManager,
                WeComNotificationAgent,
                WeComIntelligentReply,
                WeComWorkflowEngine,
            )
            _ai_employees = {
                'router': WeComMessageRouter('api_router', '消息路由员'),
                'approval': WeComApprovalAutomation('api_approval', '审批管理员'),
                'contact': WeComContactManager('api_contact', '通讯录管理员'),
                'notification': WeComNotificationAgent('api_notification', '通知代理员'),
                'reply': WeComIntelligentReply('api_reply', '智能回复员'),
                'workflow': WeComWorkflowEngine('api_workflow', '工作流引擎员'),
            }
        except Exception as e:
            logger.warning(f"[WeComAPI] 初始化AI员工失败: {e}")
    return _ai_employees


# ==================== 配置管理 API ====================

@wecom_api.route('/api/wecom/config', methods=['GET'])
def get_config():
    """获取企业微信配置"""
    client = _get_wecom_client()
    if client:
        status = client.get_status()
        return jsonify({
            "success": True,
            "config": status
        })
    return jsonify({
        "success": False,
        "message": "企业微信客户端未初始化"
    })


@wecom_api.route('/api/wecom/config', methods=['POST'])
def update_config():
    """更新企业微信配置"""
    data = request.get_json() or {}

    # 验证必要字段
    if 'corpid' not in data and 'corpsecret' not in data:
        return jsonify({
            "success": False,
            "error": "需要提供 corpid 或 corpsecret"
        }), 400

    try:
        from core.services.wecom_client import WeComClient
        global _wecom_client

        # 创建新客户端
        _wecom_client = WeComClient(
            corpid=data.get('corpid', ''),
            corpsecret=data.get('corpsecret', ''),
            agentid=data.get('agentid', 0)
        )

        # 保存配置
        _wecom_client.save_config()

        return jsonify({
            "success": True,
            "message": "配置已更新",
            "status": _wecom_client.get_status()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@wecom_api.route('/api/wecom/test-connection', methods=['POST'])
def test_connection():
    """测试企业微信连接"""
    client = _get_wecom_client()
    if not client:
        return jsonify({
            "success": False,
            "message": "企业微信客户端未初始化"
        })

    result = client.ping()
    return jsonify(result)


# ==================== 消息发送 API ====================

@wecom_api.route('/api/wecom/message/send', methods=['POST'])
def send_message():
    """发送企业微信消息"""
    data = request.get_json() or {}
    user_ids = data.get('user_ids', [])
    content = data.get('content', '')
    msg_type = data.get('msg_type', 'text')

    if not content:
        return jsonify({
            "success": False,
            "error": "消息内容不能为空"
        }), 400

    client = _get_wecom_client()
    if not client:
        # 模拟模式
        return jsonify({
            "success": True,
            "mode": "simulated",
            "message": f"消息已发送给 {len(user_ids)} 人（模拟）",
            "content": content
        })

    try:
        if msg_type == 'text':
            result = client.send_text_message(user_ids, content)
        elif msg_type == 'markdown':
            result = client.send_markdown_message(user_ids, content)
        elif msg_type == 'image':
            media_id = data.get('media_id', '')
            result = client.send_image_message(user_ids, media_id)
        elif msg_type == 'file':
            media_id = data.get('media_id', '')
            result = client.send_file_message(user_ids, media_id)
        elif msg_type == 'textcard':
            result = client.send_textcard_message(
                user_ids,
                data.get('title', ''),
                data.get('description', ''),
                data.get('url', '')
            )
        elif msg_type == 'taskcard':
            result = client.send_taskcard_message(
                user_ids,
                data.get('title', ''),
                data.get('description', ''),
                data.get('task_id', '')
            )
        elif msg_type == 'template_card':
            result = client.send_template_card(user_ids, data.get('card_json', '{}'))
        else:
            return jsonify({
                "success": False,
                "error": f"不支持的消息类型: {msg_type}"
            }), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@wecom_api.route('/api/wecom/message/broadcast', methods=['POST'])
def broadcast_message():
    """广播消息（全员通知）"""
    data = request.get_json() or {}
    content = data.get('content', '')
    msg_type = data.get('msg_type', 'text')

    if not content:
        return jsonify({
            "success": False,
            "error": "广播内容不能为空"
        }), 400

    client = _get_wecom_client()
    if not client:
        # 模拟模式
        return jsonify({
            "success": True,
            "mode": "simulated",
            "message": "广播已发出（模拟）",
            "audience": "@all"
        })

    try:
        if msg_type == 'text':
            result = client.send_text_message(['@all'], content)
        elif msg_type == 'markdown':
            result = client.send_markdown_message(['@all'], content)
        else:
            return jsonify({
                "success": False,
                "error": f"广播暂不支持的消息类型: {msg_type}"
            }), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@wecom_api.route('/api/wecom/webhook/send', methods=['POST'])
def send_webhook():
    """发送企业微信群机器人 Webhook 消息"""
    data = request.get_json() or {}
    webhook_url = data.get('webhook_url', '')
    content = data.get('content', '')
    msg_type = data.get('msg_type', 'text')

    if not webhook_url:
        return jsonify({
            "success": False,
            "error": "Webhook URL 不能为空"
        }), 400

    if not content:
        return jsonify({
            "success": False,
            "error": "消息内容不能为空"
        }), 400

    try:
        from core.services.wecom_client import WeComClient
        result = WeComClient.send_webhook_message(webhook_url, content, msg_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 通讯录管理 API ====================

@wecom_api.route('/api/wecom/departments', methods=['GET'])
def get_departments():
    """获取部门列表"""
    department_id = request.args.get('id', '1')

    client = _get_wecom_client()
    if not client:
        # 模拟数据
        return jsonify({
            "success": True,
            "mode": "simulated",
            "departments": [
                {"id": 1, "name": "公司总部", "parent_id": 0, "member_count": 120},
                {"id": 2, "name": "技术部", "parent_id": 1, "member_count": 45},
                {"id": 3, "name": "产品部", "parent_id": 1, "member_count": 20},
                {"id": 4, "name": "市场部", "parent_id": 1, "member_count": 15},
                {"id": 5, "name": "人力资源部", "parent_id": 1, "member_count": 8},
            ]
        })

    try:
        result = client.get_department_list(int(department_id))
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wecom_api.route('/api/wecom/departments', methods=['POST'])
def create_department():
    """创建部门"""
    data = request.get_json() or {}
    name = data.get('name', '')

    if not name:
        return jsonify({
            "success": False,
            "error": "部门名称不能为空"
        }), 400

    client = _get_wecom_client()
    if not client:
        return jsonify({
            "success": True,
            "mode": "simulated",
            "message": f"部门「{name}」已创建（模拟）"
        })

    try:
        result = client.create_department(
            name=name,
            parent_id=data.get('parent_id', 1),
            order=data.get('order', 0),
            department_id=data.get('id')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wecom_api.route('/api/wecom/users', methods=['GET'])
def get_users():
    """获取成员列表"""
    department_id = request.args.get('department_id', '1')
    keyword = request.args.get('keyword', '')

    client = _get_wecom_client()
    if not client:
        # 模拟数据
        mock_users = [
            {"userid": "lisi", "name": "李四", "department": [2], "position": "高级工程师"},
            {"userid": "wangwu", "name": "王五", "department": [3], "position": "产品经理"},
            {"userid": "zhaoliu", "name": "赵六", "department": [4], "position": "市场专员"},
            {"userid": "sunqi", "name": "孙七", "department": [5], "position": "HRBP"},
        ]
        if keyword:
            mock_users = [u for u in mock_users
                          if keyword.lower() in u['name'].lower() or
                          keyword.lower() in u['position'].lower()]
        return jsonify({
            "success": True,
            "mode": "simulated",
            "userlist": mock_users,
            "total": len(mock_users)
        })

    try:
        result = client.get_user_list(int(department_id), key_word=keyword)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wecom_api.route('/api/wecom/users/search', methods=['POST'])
def search_users():
    """智能搜索成员"""
    data = request.get_json() or {}
    query = data.get('query', '')

    if not query:
        return jsonify({
            "success": False,
            "error": "搜索关键词不能为空"
        }), 400

    # 使用 AI 员工搜索
    employees = _init_ai_employees()
    contact_manager = employees.get('contact')

    if contact_manager:
        result = contact_manager.execute_task({
            'type': 'search_contact',
            'query': query
        })
        return jsonify(result)

    return jsonify({
        "success": False,
        "message": "通讯录管理员未初始化"
    })


@wecom_api.route('/api/wecom/tags', methods=['GET'])
def get_tags():
    """获取标签列表"""
    client = _get_wecom_client()
    if not client:
        return jsonify({
            "success": True,
            "mode": "simulated",
            "tags": [
                {"tagid": 1, "tagname": "技术团队", "count": 45},
                {"tagid": 2, "tagname": "管理团队", "count": 15},
                {"tagid": 3, "tagname": "新员工", "count": 8},
            ]
        })

    try:
        result = client.get_tag_list()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 审批管理 API ====================

@wecom_api.route('/api/wecom/approval/templates', methods=['GET'])
def get_approval_templates():
    """获取审批模板列表"""
    employees = _init_ai_employees()
    approval_employee = employees.get('approval')

    if approval_employee:
        result = approval_employee.execute_task({'type': 'recommend_template', 'text': '审批模板'})
        return jsonify(result)

    return jsonify({
        "success": True,
        "templates": [
            {"key": "leave", "name": "请假申请", "fields": 5},
            {"key": "expense", "name": "报销申请", "fields": 4},
            {"key": "travel", "name": "出差申请", "fields": 5},
            {"key": "overtime", "name": "加班申请", "fields": 3},
        ]
    })


@wecom_api.route('/api/wecom/approval', methods=['POST'])
def create_approval():
    """创建审批"""
    data = request.get_json() or {}
    template_key = data.get('template_key', '')
    approval_data = data.get('data', {})

    if not template_key:
        return jsonify({
            "success": False,
            "error": "审批模板不能为空"
        }), 400

    employees = _init_ai_employees()
    approval_employee = employees.get('approval')

    if approval_employee:
        result = approval_employee.execute_task({
            'type': 'create_approval',
            'template_key': template_key,
            'approval_data': approval_data
        })
        return jsonify(result)

    return jsonify({
        "success": True,
        "mode": "simulated",
        "approval_id": f"APP{int(time.time())}",
        "message": "审批已创建（模拟）"
    })


@wecom_api.route('/api/wecom/approval/<approval_id>', methods=['GET'])
def get_approval_status(approval_id):
    """查询审批状态"""
    employees = _init_ai_employees()
    approval_employee = employees.get('approval')

    if approval_employee:
        result = approval_employee.execute_task({
            'type': 'query_status',
            'approval_id': approval_id
        })
        return jsonify(result)

    return jsonify({
        "success": True,
        "mode": "simulated",
        "approval_id": approval_id,
        "status": "pending",
        "message": "审批状态：等待审批中（模拟）"
    })


@wecom_api.route('/api/wecom/approval/analyze', methods=['GET'])
def analyze_approvals():
    """分析审批数据"""
    employees = _init_ai_employees()
    approval_employee = employees.get('approval')

    if approval_employee:
        result = approval_employee.execute_task({'type': 'analyze'})
        return jsonify(result)

    return jsonify({
        "success": True,
        "mode": "simulated",
        "total": 0,
        "message": "暂无审批数据"
    })


# ==================== 日程管理 API ====================

@wecom_api.route('/api/wecom/schedules', methods=['POST'])
def create_schedule():
    """创建日程"""
    data = request.get_json() or {}
    title = data.get('title', '')
    start_time = data.get('start_time', '')
    end_time = data.get('end_time', '')
    attendees = data.get('attendees', [])

    if not title:
        return jsonify({
            "success": False,
            "error": "日程标题不能为空"
        }), 400

    client = _get_wecom_client()
    if not client:
        return jsonify({
            "success": True,
            "mode": "simulated",
            "schedule_id": f"SCH{int(time.time())}",
            "title": title,
            "message": f"日程「{title}」已创建（模拟）"
        })

    try:
        result = client.create_schedule({
            "summary": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees
        })
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wecom_api.route('/api/wecom/schedules', methods=['GET'])
def get_schedules():
    """获取日程列表"""
    user_id = request.args.get('user_id', '')
    client = _get_wecom_client()

    if not client:
        return jsonify({
            "success": True,
            "mode": "simulated",
            "schedules": [
                {
                    "id": "SCH001",
                    "title": "团队周会",
                    "start_time": "2026-07-29T14:00:00",
                    "end_time": "2026-07-29T15:00:00",
                    "attendees": ["lisi", "wangwu"]
                }
            ]
        })

    try:
        result = client.get_schedule_list(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== AI 智能员工 API ====================

@wecom_api.route('/api/wecom/ai/chat', methods=['POST'])
def ai_chat():
    """AI 智能对话"""
    data = request.get_json() or {}
    text = data.get('text', '')
    user_id = data.get('user_id', 'anonymous')
    context = data.get('context', {})

    if not text:
        return jsonify({
            "success": False,
            "error": "消息内容不能为空"
        }), 400

    employees = _init_ai_employees()

    # Step 1: 意图识别与路由
    router = employees.get('router')
    if router:
        route_result = router.execute_task({
            'text': text,
            'user_id': user_id,
            'context': context
        })
    else:
        route_result = {"route": {"handler": "default"}}

    # Step 2: 智能回复
    reply_employee = employees.get('reply')
    if reply_employee:
        reply_result = reply_employee.execute_task({
            'text': text,
            'user_id': user_id,
            'context': context
        })
    else:
        reply_result = {
            "reply": f"我收到您的消息：「{text}」。企业微信AI助手正在初始化中..."
        }

    return jsonify({
        "success": True,
        "route": route_result.get('route', {}),
        "intent": route_result.get('intent', {}).get('primary_intent', 'unknown'),
        "reply": reply_result.get('reply', ''),
        "suggestions": reply_result.get('suggestions', []),
        "employee_type": "wecom_intelligent_reply"
    })


@wecom_api.route('/api/wecom/ai/intent', methods=['POST'])
def ai_intent_recognition():
    """AI 意图识别"""
    data = request.get_json() or {}
    text = data.get('text', '')

    if not text:
        return jsonify({
            "success": False,
            "error": "文本内容不能为空"
        }), 400

    try:
        from ai_engines.wecom_ai_employee import _detect_intent
        result = _detect_intent(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wecom_api.route('/api/wecom/ai/notification', methods=['POST'])
def ai_notification():
    """AI 智能通知"""
    data = request.get_json() or {}
    employees = _init_ai_employees()
    notification_agent = employees.get('notification')

    if not notification_agent:
        return jsonify({
            "success": False,
            "message": "通知代理未初始化"
        })

    result = notification_agent.execute_task(data)
    return jsonify(result)


@wecom_api.route('/api/wecom/ai/approval-recommend', methods=['POST'])
def ai_approval_recommend():
    """AI 审批推荐"""
    data = request.get_json() or {}
    text = data.get('text', '')

    employees = _init_ai_employees()
    approval_employee = employees.get('approval')

    if not approval_employee:
        return jsonify({
            "success": False,
            "message": "审批员工未初始化"
        })

    result = approval_employee.execute_task({
        'type': 'recommend_template',
        'text': text
    })
    return jsonify(result)


@wecom_api.route('/api/wecom/ai/workflow/execute', methods=['POST'])
def ai_workflow_execute():
    """AI 工作流执行"""
    data = request.get_json() or {}
    employees = _init_ai_employees()
    workflow_employee = employees.get('workflow')

    if not workflow_employee:
        return jsonify({
            "success": False,
            "message": "工作流引擎未初始化"
        })

    result = workflow_employee.execute_task(data)
    return jsonify(result)


@wecom_api.route('/api/wecom/ai/stats', methods=['GET'])
def ai_stats():
    """获取 AI 员工统计"""
    employees = _init_ai_employees()

    stats = {}
    for name, emp in employees.items():
        if hasattr(emp, 'get_routing_stats'):
            stats['router'] = emp.get_routing_stats()
        elif hasattr(emp, 'get_approval_stats'):
            stats['approval'] = emp.get_approval_stats()
        elif hasattr(emp, 'get_search_stats'):
            stats['contact'] = emp.get_search_stats()
        elif hasattr(emp, 'get_conversation_stats'):
            stats['reply'] = emp.get_conversation_stats()
        elif hasattr(emp, 'get_workflow_stats'):
            stats['workflow'] = emp.get_workflow_stats()

    return jsonify({
        "success": True,
        "employees": list(employees.keys()),
        "stats": stats
    })


# ==================== Webhook 回调 API ====================

@wecom_api.route('/api/wecom/webhook/callback', methods=['GET', 'POST'])
def wecom_callback():
    """企业微信回调验证与消息接收"""
    if request.method == 'GET':
        # URL 验证
        msg_signature = request.args.get('msg_signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')

        # TODO: 实际生产中需要验证签名
        # 简化处理：直接返回 echostr
        if echostr:
            return echostr
        return jsonify({"success": True, "message": "WeCom callback endpoint is ready"})

    elif request.method == 'POST':
        # 接收消息
        try:
            data = request.get_json() or {}
            encrypt_type = data.get('EncryptType', '')
            msg_signature = data.get('MsgSignature', '')

            # 解析消息（简化）
            # 实际生产中需要解密消息内容
            events = data.get('events', [])
            messages = data.get('messages', [])

            # 处理事件
            processed_events = []
            for event in events:
                processed = _process_event(event)
                processed_events.append(processed)

            # 处理消息
            processed_messages = []
            for message in messages:
                processed = _process_message(message)
                processed_messages.append(processed)

            return jsonify({
                "success": True,
                "processed_events": processed_events,
                "processed_messages": processed_messages
            })
        except Exception as e:
            logger.error(f"[WeComAPI] 回调处理失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500


def _process_event(event: Dict) -> Dict:
    """处理企业微信事件"""
    event_type = event.get('EventType', '')

    event_handlers = {
        'change_contact': _handle_contact_change,
        'click': _handle_menu_click,
        'subscribe': _handle_subscribe,
    }

    handler = event_handlers.get(event_type, lambda e: {"status": "ignored", "reason": f"Unknown event: {event_type}"})
    return handler(event)


def _handle_contact_change(event: Dict) -> Dict:
    """处理通讯录变更事件"""
    return {
        "type": "contact_change",
        "action": event.get('ChangeType', ''),
        "user_id": event.get('UserID', ''),
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }


def _handle_menu_click(event: Dict) -> Dict:
    """处理菜单点击事件"""
    return {
        "type": "menu_click",
        "menu_key": event.get('EventKey', ''),
        "user_id": event.get('UserID', ''),
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }


def _handle_subscribe(event: Dict) -> Dict:
    """处理订阅事件"""
    return {
        "type": "subscribe",
        "user_id": event.get('UserID', ''),
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }


def _process_message(message: Dict) -> Dict:
    """处理企业微信消息"""
    msg_type = message.get('MsgType', '')
    content = message.get('Content', '')
    from_user = message.get('FromUserName', '')

    # 使用 AI 员工处理
    employees = _init_ai_employees()
    reply_employee = employees.get('reply')

    if reply_employee and content:
        result = reply_employee.execute_task({
            'text': content,
            'user_id': from_user,
            'context': message
        })
        ai_reply = result.get('reply', '')
    else:
        ai_reply = "收到您的消息，AI 助手正在初始化中..."

    return {
        "msg_type": msg_type,
        "from_user": from_user,
        "content": content,
        "ai_reply": ai_reply,
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }


# ==================== 系统状态 API ====================

@wecom_api.route('/api/wecom/status', methods=['GET'])
def get_system_status():
    """获取企业微信系统状态"""
    client = _get_wecom_client()
    employees = _init_ai_employees()

    status = {
        "server": {
            "status": "running",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        },
        "client": client.get_status() if client else {"status": "not_initialized"},
        "ai_employees": {
            name: {
                "type": emp.employee_type,
                "level": emp.level,
                "status": emp.status
            }
            for name, emp in employees.items()
        },
        "endpoints": [
            "/api/wecom/config",
            "/api/wecom/test-connection",
            "/api/wecom/message/send",
            "/api/wecom/message/broadcast",
            "/api/wecom/webhook/send",
            "/api/wecom/departments",
            "/api/wecom/users",
            "/api/wecom/users/search",
            "/api/wecom/approval/templates",
            "/api/wecom/approval",
            "/api/wecom/schedules",
            "/api/wecom/ai/chat",
            "/api/wecom/ai/intent",
            "/api/wecom/ai/notification",
            "/api/wecom/ai/approval-recommend",
            "/api/wecom/ai/workflow/execute",
            "/api/wecom/ai/stats",
            "/api/wecom/webhook/callback",
        ]
    }

    return jsonify({
        "success": True,
        "status": status
    })


# ==================== 初始化 ====================

def init_wecom_api():
    """初始化企业微信 API"""
    global _wecom_client, _ai_employees

    # 初始化客户端
    try:
        from core.services.wecom_client import get_wecom_client
        _wecom_client = get_wecom_client()
        logger.info("[WeComAPI] 企业微信客户端初始化成功")
    except Exception as e:
        logger.warning(f"[WeComAPI] 企业微信客户端初始化失败: {e}")

    # 初始化 AI 员工
    _init_ai_employees()
    logger.info("[WeComAPI] 企业微信 AI 员工初始化完成")

    return {
        "client_initialized": _wecom_client is not None,
        "ai_employees": list(_ai_employees.keys())
    }


if __name__ == '__main__':
    # 测试
    init_wecom_api()
    print("企业微信 API 模块初始化完成")
    print(f"可用员工: {list(_ai_employees.keys())}")
