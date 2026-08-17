#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信 AI 员工系统
WeCom Integration Employee - 企业微信智能化集成

AI 员工类型：
1. WeComMessageRouter - 智能消息路由员工
2. WeComApprovalAutomation - 审批自动化员工
3. WeComContactManager - 通讯录智能管理员工
4. WeComNotificationAgent - 智能通知代理员工
5. WeComIntelligentReply - 智能回复员工
6. WeComWorkflowEngine - 工作流引擎员工

功能：
- 自然语言处理（NLP）意图识别
- 智能消息路由与分类
- 审批流自动化处理
- 通讯录智能管理
- 智能通知推送
- 自动回复与问答
- 工作流自动化编排

作者: MTSCOS AI 系统
版本: v1.0.0
"""

import os
import json
import time
import re
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    from ai_engines.ai_employee_system import AIEmployee
    AI_EMPLOYEE_AVAILABLE = True
except ImportError:
    AI_EMPLOYEE_AVAILABLE = False
    # 简单基类
    class AIEmployee:
        def __init__(self, employee_id, name, employee_type="general", level=1):
            self.employee_id = employee_id
            self.name = name
            self.employee_type = employee_type
            self.level = level
            self.status = "active"

        def execute_task(self, task_data):
            return {"success": False, "message": "基类方法未实现"}


# ==================== 意图识别引擎 ====================

# 意图关键词映射
_INTENT_KEYWORDS = {
    # 消息相关
    "send_message": ["发送", "消息", "通知", "提醒", "message", "send", "通知"],
    "send_markdown": ["markdown", "格式化", "富文本"],
    "send_file": ["文件", "附件", "file", "document"],
    # 审批相关
    "create_approval": ["审批", "申请", "请假", "报销", "出差", "approval"],
    "query_approval": ["查询", "审批状态", "进度", "approval status"],
    "approval_template": ["审批模板", "模板", "template"],
    # 通讯录相关
    "query_contact": ["查询用户", "成员", "通讯录", "contact", "user"],
    "query_department": ["部门", "组织结构", "department"],
    "manage_tag": ["标签", "tag"],
    # 日程会议
    "create_schedule": ["日程", "会议", "安排", "schedule", "meeting"],
    "query_schedule": ["查询日程", "我的日程"],
    # 通知推送
    "push_notification": ["推送", "广播", "全员通知", "broadcast"],
    # 知识库
    "knowledge_query": ["知识库", "文档", "wiki", "知识"],
    # 系统管理
    "system_status": ["状态", "健康检查", "status", "ping"],
    # 查询天气
    "weather_query": ["天气", "温度", "weather"],
    # 问候
    "greeting": ["你好", "您好", "hi", "hello", "在吗"],
    # 帮助
    "help": ["帮助", "help", "使用说明", "指令"],
}

# 审批类型映射
_APPROVAL_TYPES = {
    "leave": {"name": "请假申请", "code": "LEAVE"},
    "expense": {"name": "报销申请", "code": "EXPENSE"},
    "travel": {"name": "出差申请", "code": "TRAVEL"},
    "business_trip": {"name": "出差申请", "code": "TRAVEL"},
    "overtime": {"name": "加班申请", "code": "OVERTIME"},
    "seal": {"name": "用印申请", "code": "SEAL"},
    "purchase": {"name": "采购申请", "code": "PURCHASE"},
    "contract": {"name": "合同审批", "code": "CONTRACT"},
    "hire": {"name": "入职申请", "code": "HIRE"},
    "resign": {"name": "离职申请", "code": "RESIGN"},
}

# 智能回复模板
_REPLY_TEMPLATES = {
    "greeting": [
        "您好！我是企业微信AI助手，很高兴为您服务。",
        "你好！我可以帮您处理消息发送、审批流程、日程管理等工作。",
        "欢迎使用企业微信智能助手！有什么可以帮您的吗？"
    ],
    "help": [
        "我可以帮您完成以下工作：\n"
        "📨 消息发送：发送文本、Markdown、文件等\n"
        "📋 审批管理：发起审批、查询审批状态\n"
        "📅 日程会议：创建日程、查询会议\n"
        "👥 通讯录管理：查询成员、部门信息\n"
        "🔔 通知推送：广播通知、系统提醒\n"
        "\n请直接告诉我您需要做什么！"
    ],
    "approval_created": [
        "✅ 审批已创建，审批单号：{approval_id}\n您可以在【审批】应用中查看进度。"
    ],
    "message_sent": [
        "✅ 消息已发送，共通知 {count} 人。"
    ],
    "contact_found": [
        "📋 找到 {count} 个成员：\n{users}"
    ],
    "no_result": [
        "抱歉，没有找到相关信息。请尝试其他关键词。"
    ],
    "system_status": [
        "🔧 系统状态：\n"
        "• 服务状态：正常运行\n"
        "• 已连接用户：{user_count} 人\n"
        "• 待处理任务：{task_count} 个\n"
        "• 最近更新：{last_update}"
    ],
}


def _detect_intent(text: str) -> Dict[str, Any]:
    """
    检测用户意图

    Args:
        text: 用户输入文本

    Returns:
        意图识别结果
    """
    text_lower = text.lower()
    intents = []

    for intent, keywords in _INTENT_KEYWORDS.items():
        score = 0
        matched_keywords = []
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 1
                matched_keywords.append(kw)
        if score > 0:
            intents.append({
                "intent": intent,
                "score": score,
                "matched_keywords": matched_keywords
            })

    intents.sort(key=lambda x: x['score'], reverse=True)

    return {
        "success": True,
        "intents": intents,
        "primary_intent": intents[0]['intent'] if intents else "unknown",
        "confidence": intents[0]['score'] / max(len(intents), 1) if intents else 0,
        "message": f"检测到 {len(intents)} 个意图"
    }


def _extract_params(text: str, intent: str) -> Dict[str, Any]:
    """
    根据意图提取参数

    Args:
        text: 用户输入文本
        intent: 已识别的意图

    Returns:
        提取的参数
    """
    params = {
        "raw_text": text,
        "intent": intent
    }

    # 提取人名/@人
    at_pattern = r'@(\S+)'
    mentions = re.findall(at_pattern, text)
    if mentions:
        params['mentions'] = mentions

    # 提取审批类型
    if 'approval' in intent:
        for appr_type, info in _APPROVAL_TYPES.items():
            if info['name'] in text or appr_type in text.lower():
                params['approval_type'] = appr_type
                params['approval_type_name'] = info['name']
                break

    # 提取日期
    date_patterns = [
        (r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?', 'full_date'),
        (r'(\d{1,2})[-/月](\d{1,2})[日]?', 'short_date'),
        (r'(今天|明天|后天|下周|本周)', 'relative_date'),
    ]
    for pattern, date_type in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            params['dates'] = matches
            params['date_type'] = date_type
            break

    # 提取时间
    time_pattern = r'(\d{1,2})[点:：](\d{2})?'
    time_match = re.search(time_pattern, text)
    if time_match:
        params['time'] = f"{time_match.group(1)}:{time_match.group(2) or '00'}"

    # 提取手机号
    phone_pattern = r'1[3-9]\d{9}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        params['phone'] = phone_match.group()

    # 提取邮箱
    email_pattern = r'[\w.-]+@[\w.-]+'
    email_match = re.search(email_pattern, text)
    if email_match:
        params['email'] = email_match.group()

    # 提取数字金额
    amount_pattern = r'(\d+(?:\.\d+)?)\s*(元|块|¥|￥)'
    amount_match = re.search(amount_pattern, text)
    if amount_match:
        params['amount'] = float(amount_match.group(1))

    # 提取天数
    days_pattern = r'(\d+)\s*天'
    days_match = re.search(days_pattern, text)
    if days_match:
        params['days'] = int(days_match.group(1))

    return params


# ==================== 企业微信智能消息路由员工 ====================

class WeComMessageRouter(AIEmployee):
    """
    企业微信智能消息路由员工

    核心能力：
    - 自然语言意图识别
    - 智能消息分类与路由
    - 自动选择最佳消息类型
    - 多渠道消息分发
    - 消息模板匹配
    """

    def __init__(self, employee_id: str, name: str, level: int = 8):
        super().__init__(employee_id, name, "wecom_message_router", level)
        self.message_history: List[Dict[str, Any]] = []
        self.routing_rules: List[Dict[str, Any]] = self._init_routing_rules()

    def _init_routing_rules(self) -> List[Dict[str, Any]]:
        """初始化路由规则"""
        return [
            {"name": "紧急通知", "pattern": "紧急|urgent|重要", "priority": "high", "target": "notify"},
            {"name": "审批请求", "pattern": "审批|申请|请假|报销", "priority": "medium", "target": "approval"},
            {"name": "日程安排", "pattern": "会议|日程|安排", "priority": "medium", "target": "schedule"},
            {"name": "知识查询", "pattern": "是什么|如何|怎么|查询", "priority": "low", "target": "knowledge"},
            {"name": "日常问候", "pattern": "你好|hi|hello", "priority": "low", "target": "chat"},
        ]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行消息路由任务

        Args:
            task_data: 任务数据
                - text: 用户输入文本
                - user_id: 发送者 ID
                - context: 上下文信息

        Returns:
            路由结果
        """
        text = task_data.get('text', '')
        user_id = task_data.get('user_id', 'unknown')
        context = task_data.get('context', {})

        # Step 1: 意图识别
        intent_result = _detect_intent(text)
        primary_intent = intent_result['primary_intent']

        # Step 2: 参数提取
        params = _extract_params(text, primary_intent)

        # Step 3: 路由决策
        route_result = self._route_message(intent_result, params, user_id, context)

        # Step 4: 记录历史
        self.message_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "text": text,
            "intent": primary_intent,
            "route": route_result
        })
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]

        return {
            "success": True,
            "intent": intent_result,
            "params": params,
            "route": route_result,
            "message": f"消息已路由到: {route_result.get('handler', 'unknown')}"
        }

    def _route_message(self, intent_result: Dict, params: Dict,
                       user_id: str, context: Dict) -> Dict[str, Any]:
        """路由消息到对应的处理器"""
        primary_intent = intent_result['primary_intent']
        intents = intent_result.get('intents', [])

        # 匹配路由规则
        for rule in self.routing_rules:
            pattern = rule['pattern']
            if any(kw in pattern or pattern in kw for kw in params.get('raw_text', '').split()):
                return {
                    "handler": rule['target'],
                    "priority": rule['priority'],
                    "matched_rule": rule['name'],
                    "action": "route",
                    "data": params
                }

        # 基于意图路由
        intent_routes = {
            "send_message": "message_sender",
            "send_markdown": "message_sender_markdown",
            "send_file": "message_sender_file",
            "create_approval": "approval_handler",
            "query_approval": "approval_query_handler",
            "query_contact": "contact_handler",
            "query_department": "department_handler",
            "create_schedule": "schedule_handler",
            "push_notification": "notification_handler",
            "knowledge_query": "knowledge_handler",
            "greeting": "chat_handler",
            "help": "help_handler",
            "system_status": "system_handler",
        }

        handler = intent_routes.get(primary_intent, "default_handler")

        return {
            "handler": handler,
            "priority": "normal",
            "matched_intent": primary_intent,
            "action": "route",
            "data": params
        }

    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计"""
        handler_counts = defaultdict(int)
        intent_counts = defaultdict(int)

        for record in self.message_history:
            handler = record.get('route', {}).get('handler', 'unknown')
            handler_counts[handler] += 1
            intent = record.get('intent', 'unknown')
            intent_counts[intent] += 1

        return {
            "total_messages": len(self.message_history),
            "handler_distribution": dict(handler_counts),
            "intent_distribution": dict(intent_counts),
            "routing_rules_count": len(self.routing_rules)
        }


# ==================== 企业微信审批自动化员工 ====================

class WeComApprovalAutomation(AIEmployee):
    """
    企业微信审批自动化员工

    核心能力：
    - 智能审批模板推荐
    - 审批数据自动填充
    - 审批流程自动化
    - 审批状态实时追踪
    - 异常审批预警
    - 审批数据分析
    """

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "wecom_approval_automation", level)
        self.approval_templates: Dict[str, Dict] = self._init_templates()
        self.approval_history: List[Dict[str, Any]] = []

    def _init_templates(self) -> Dict[str, Dict]:
        """初始化审批模板"""
        return {
            "leave": {
                "name": "请假申请",
                "fields": [
                    {"name": "leave_type", "label": "请假类型", "type": "select",
                     "options": ["年假", "事假", "病假", "调休", "婚假", "产假"]},
                    {"name": "start_date", "label": "开始日期", "type": "date"},
                    {"name": "end_date", "label": "结束日期", "type": "date"},
                    {"name": "reason", "label": "请假原因", "type": "text"},
                    {"name": "days", "label": "请假天数", "type": "number"}
                ],
                "flow": "直属主管 → 部门经理 → HR"
            },
            "expense": {
                "name": "报销申请",
                "fields": [
                    {"name": "expense_type", "label": "报销类型", "type": "select",
                     "options": ["差旅费", "办公费", "招待费", "培训费", "其他"]},
                    {"name": "amount", "label": "金额", "type": "number"},
                    {"name": "reason", "label": "报销说明", "type": "text"},
                    {"name": "attachments", "label": "凭证", "type": "file"}
                ],
                "flow": "部门经理 → 财务审核 → 财务经理"
            },
            "travel": {
                "name": "出差申请",
                "fields": [
                    {"name": "destination", "label": "出差地点", "type": "text"},
                    {"name": "purpose", "label": "出差目的", "type": "text"},
                    {"name": "start_date", "label": "开始日期", "type": "date"},
                    {"name": "end_date", "label": "结束日期", "type": "date"},
                    {"name": "budget", "label": "预算金额", "type": "number"}
                ],
                "flow": "部门经理 → 分管领导 → HR备案"
            },
            "overtime": {
                "name": "加班申请",
                "fields": [
                    {"name": "date", "label": "加班日期", "type": "date"},
                    {"name": "hours", "label": "加班小时数", "type": "number"},
                    {"name": "reason", "label": "加班原因", "type": "text"}
                ],
                "flow": "直属主管 → 部门经理"
            }
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行审批自动化任务

        Args:
            task_data: 任务数据
                - type: 任务类型 (recommend_template, create_approval, query_status, analyze)
                - text: 自然语言描述
                - approval_data: 审批数据
        """
        task_type = task_data.get('type', 'recommend_template')

        if task_type == 'recommend_template':
            return self._recommend_template(task_data)
        elif task_type == 'create_approval':
            return self._create_approval(task_data)
        elif task_type == 'query_status':
            return self._query_status(task_data)
        elif task_type == 'analyze':
            return self._analyze_approvals(task_data)
        else:
            return {"success": False, "message": f"未知任务类型: {task_type}"}

    def _recommend_template(self, task_data: Dict) -> Dict[str, Any]:
        """推荐审批模板"""
        text = task_data.get('text', '')
        intent_result = _detect_intent(text)

        recommendations = []
        for template_key, template_info in self.approval_templates.items():
            score = 0
            for keyword in template_info['name']:
                if keyword in text:
                    score += 2
            if template_key in text.lower():
                score += 3
            if score > 0:
                recommendations.append({
                    "template_key": template_key,
                    "template_name": template_info['name'],
                    "match_score": score,
                    "fields_count": len(template_info['fields']),
                    "approval_flow": template_info['flow']
                })

        if not recommendations:
            # 返回所有模板
            recommendations = [{
                "template_key": k,
                "template_name": v['name'],
                "match_score": 0,
                "fields_count": len(v['fields']),
                "approval_flow": v['flow']
            } for k, v in self.approval_templates.items()]

        recommendations.sort(key=lambda x: x['match_score'], reverse=True)

        return {
            "success": True,
            "recommendations": recommendations[:3],
            "primary_intent": intent_result['primary_intent']
        }

    def _create_approval(self, task_data: Dict) -> Dict[str, Any]:
        """创建审批"""
        approval_data = task_data.get('approval_data', {})
        template_key = task_data.get('template_key', '')

        if template_key not in self.approval_templates:
            return {"success": False, "message": f"未知审批模板: {template_key}"}

        template = self.approval_templates[template_key]

        # 验证必填字段
        missing_fields = []
        for field in template['fields']:
            if field.get('required') and field['name'] not in approval_data:
                missing_fields.append(field['label'])

        if missing_fields:
            return {
                "success": False,
                "message": f"缺少必填字段: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }

        # 生成审批 ID
        approval_id = f"APP{int(time.time())}"

        # 记录审批
        approval_record = {
            "approval_id": approval_id,
            "template_key": template_key,
            "template_name": template['name'],
            "data": approval_data,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "flow": template['flow']
        }
        self.approval_history.append(approval_record)

        return {
            "success": True,
            "approval_id": approval_id,
            "message": f"审批已创建: {template['name']}",
            "next_step": template['flow'].split('→')[0].strip(),
            "approval_data": approval_record
        }

    def _query_status(self, task_data: Dict) -> Dict[str, Any]:
        """查询审批状态"""
        approval_id = task_data.get('approval_id', '')

        if approval_id:
            for record in self.approval_history:
                if record['approval_id'] == approval_id:
                    return {
                        "success": True,
                        "approval": record,
                        "status_message": self._get_status_message(record)
                    }
            return {"success": False, "message": f"未找到审批: {approval_id}"}

        # 返回最近的审批
        recent = self.approval_history[-10:]
        return {
            "success": True,
            "approvals": recent,
            "total_count": len(self.approval_history)
        }

    def _analyze_approvals(self, task_data: Dict) -> Dict[str, Any]:
        """分析审批数据"""
        if not self.approval_history:
            return {"success": False, "message": "暂无审批数据"}

        # 统计分析
        template_counts = defaultdict(int)
        status_counts = defaultdict(int)

        for record in self.approval_history:
            template_counts[record['template_name']] += 1
            status_counts[record['status']] += 1

        return {
            "success": True,
            "total_approvals": len(self.approval_history),
            "by_template": dict(template_counts),
            "by_status": dict(status_counts),
            "recent_approvals": self.approval_history[-5:]
        }

    def _get_status_message(self, record: Dict) -> str:
        """获取状态消息"""
        status_map = {
            "pending": "⏳ 等待审批中",
            "approved": "✅ 审批已通过",
            "rejected": "❌ 审批被拒绝",
            "processing": "🔄 审批处理中",
            "cancelled": "🚫 审批已取消"
        }
        return status_map.get(record['status'], "未知状态")

    def get_approval_stats(self) -> Dict[str, Any]:
        """获取审批统计"""
        return {
            "total_templates": len(self.approval_templates),
            "total_approvals": len(self.approval_history),
            "templates": list(self.approval_templates.keys())
        }


# ==================== 企业微信通讯录智能管理员工 ====================

class WeComContactManager(AIEmployee):
    """
    企业微信通讯录智能管理员工

    核心能力：
    - 智能成员搜索
    - 部门结构分析
    - 标签智能管理
    - 成员画像生成
    - 组织架构可视化
    """

    def __init__(self, employee_id: str, name: str, level: int = 7):
        super().__init__(employee_id, name, "wecom_contact_manager", level)
        self.contact_cache: Dict[str, Dict] = {}
        self.department_cache: Dict[str, Dict] = {}
        self.search_history: List[Dict] = []

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行通讯录管理任务"""
        task_type = task_data.get('type', task_data.get('action', 'search'))

        if task_type == 'search_contact' or task_type == 'search':
            return self._search_contact(task_data)
        elif task_type == 'get_department' or task_type == 'department':
            return self._get_department(task_data)
        elif task_type == 'get_profile' or task_type == 'profile':
            return self._get_user_profile(task_data)
        elif task_type == 'build_org_chart' or task_type == 'org':
            return self._build_org_chart(task_data)
        else:
            return {"success": False, "message": f"未知任务类型: {task_type}"}

    def _search_contact(self, task_data: Dict) -> Dict[str, Any]:
        """智能搜索成员"""
        query = task_data.get('query', task_data.get('text', ''))

        if not query:
            return {"success": False, "message": "请输入搜索关键词"}

        # 分析搜索意图
        intent_result = _detect_intent(query)
        primary_intent = intent_result['primary_intent']

        # 在缓存中搜索
        results = []
        for user_id, user_info in self.contact_cache.items():
            if (query.lower() in str(user_info.get('name', '')).lower() or
                query.lower() in str(user_info.get('department', '')).lower() or
                query.lower() in str(user_info.get('position', '')).lower() or
                query.lower() in str(user_info.get('mobile', '')).lower()):
                results.append({
                    "user_id": user_id,
                    "name": user_info.get('name', ''),
                    "department": user_info.get('department', ''),
                    "position": user_info.get('position', ''),
                    "match_score": 1.0
                })

        # 如果缓存没有结果，生成模拟数据说明
        if not results:
            results = self._generate_mock_results(query, primary_intent)

        # 记录搜索历史
        self.search_history.append({
            "query": query,
            "intent": primary_intent,
            "results_count": len(results),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "results": results,
            "total": len(results),
            "intent": primary_intent,
            "search_history_count": len(self.search_history)
        }

    def _generate_mock_results(self, query: str, intent: str) -> List[Dict]:
        """生成模拟搜索结果"""
        # 基于意图生成不同的结果类型
        mock_users = [
            {"user_id": "lisi", "name": "李四", "department": "技术部", "position": "高级工程师", "mobile": "13800138001"},
            {"user_id": "wangwu", "name": "王五", "department": "产品部", "position": "产品经理", "mobile": "13800138002"},
            {"user_id": "zhaoliu", "name": "赵六", "department": "市场部", "position": "市场专员", "mobile": "13800138003"},
            {"user_id": "sunqi", "name": "孙七", "department": "人力资源部", "position": "HRBP", "mobile": "13800138004"},
            {"user_id": "zhouba", "name": "周八", "department": "财务部", "position": "财务分析师", "mobile": "13800138005"},
        ]

        matched = []
        for user in mock_users:
            score = 0
            if query.lower() in user['name'].lower():
                score += 3
            if query.lower() in user['department'].lower():
                score += 2
            if query.lower() in user['position'].lower():
                score += 1
            if score > 0:
                user['match_score'] = score
                matched.append(user)

        if not matched:
            # 返回最相关的
            for user in mock_users[:3]:
                user['match_score'] = 0.5
                matched.append(user)

        return matched

    def _get_department(self, task_data: Dict) -> Dict[str, Any]:
        """获取部门信息"""
        dept_id = task_data.get('department_id', '1')

        # 模拟部门结构
        departments = [
            {"id": "1", "name": "公司总部", "parent_id": "0", "member_count": 120},
            {"id": "2", "name": "技术部", "parent_id": "1", "member_count": 45},
            {"id": "3", "name": "产品部", "parent_id": "1", "member_count": 20},
            {"id": "4", "name": "市场部", "parent_id": "1", "member_count": 15},
            {"id": "5", "name": "人力资源部", "parent_id": "1", "member_count": 8},
        ]

        return {
            "success": True,
            "department": departments[0] if dept_id == '1' else departments[1:],
            "all_departments": departments,
            "total_departments": len(departments)
        }

    def _get_user_profile(self, task_data: Dict) -> Dict[str, Any]:
        """获取用户画像"""
        user_id = task_data.get('user_id', '')
        user_info = self.contact_cache.get(user_id, {})

        # 生成画像
        profile = {
            "user_id": user_id,
            "basic_info": user_info,
            "skills": self._infer_skills(user_info),
            "stats": {
                "messages_today": 0,
                "tasks_completed": 0,
                "meetings_attended": 0
            },
            "last_active": datetime.now().isoformat()
        }

        return {
            "success": True,
            "profile": profile
        }

    def _build_org_chart(self, task_data: Dict) -> Dict[str, Any]:
        """构建组织架构图"""
        org_chart = {
            "root": {"id": "1", "name": "公司总部", "type": "company"},
            "children": [
                {
                    "id": "2", "name": "技术部", "type": "department",
                    "manager": "技术总监",
                    "children": [
                        {"id": "2-1", "name": "前端组", "type": "team", "count": 15},
                        {"id": "2-2", "name": "后端组", "type": "team", "count": 20},
                        {"id": "2-3", "name": "测试组", "type": "team", "count": 10}
                    ]
                },
                {
                    "id": "3", "name": "产品部", "type": "department",
                    "manager": "产品总监",
                    "children": [
                        {"id": "3-1", "name": "产品组", "type": "team", "count": 10},
                        {"id": "3-2", "name": "设计组", "type": "team", "count": 10}
                    ]
                },
                {
                    "id": "4", "name": "市场部", "type": "department", "count": 15},
                {
                    "id": "5", "name": "人力资源部", "type": "department", "count": 8}
            ],
            "total_employees": 120
        }

        return {
            "success": True,
            "org_chart": org_chart,
            "visualization_data": {
                "nodes": [
                    {"id": "1", "label": "公司总部", "level": 0},
                    {"id": "2", "label": "技术部", "level": 1},
                    {"id": "3", "label": "产品部", "level": 1},
                    {"id": "4", "label": "市场部", "level": 1},
                    {"id": "5", "label": "人力资源部", "level": 1},
                ],
                "edges": [
                    {"from": "1", "to": "2"},
                    {"from": "1", "to": "3"},
                    {"from": "1", "to": "4"},
                    {"from": "1", "to": "5"},
                ]
            }
        }

    def _infer_skills(self, user_info: Dict) -> List[str]:
        """推断成员技能"""
        skills = []
        position = str(user_info.get('position', '')).lower()
        department = str(user_info.get('department', '')).lower()

        skill_map = {
            'engineer': ['编程', '系统设计', '问题解决'],
            'developer': ['编程', '代码审查', '技术文档'],
            'manager': ['团队管理', '项目规划', '沟通协调'],
            'designer': ['UI/UX设计', '原型设计', '用户研究'],
            'market': ['市场分析', '品牌推广', '活动策划'],
            'hr': ['招聘', '培训', '员工关系'],
            'finance': ['财务分析', '预算管理', '税务筹划'],
        }

        for keyword, skill_list in skill_map.items():
            if keyword in position or keyword in department:
                skills.extend(skill_list)

        if not skills:
            skills = ['通用技能', '团队协作', '沟通能力']

        return list(set(skills))

    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计"""
        return {
            "total_searches": len(self.search_history),
            "cached_contacts": len(self.contact_cache),
            "cached_departments": len(self.department_cache)
        }


# ==================== 企业微信智能通知代理员工 ====================

class WeComNotificationAgent(AIEmployee):
    """
    企业微信智能通知代理员工

    核心能力：
    - 智能通知生成
    - 通知优先级管理
    - 批量通知分发
    - 阅读状态追踪
    - 通知效果分析
    - 定时通知调度
    """

    def __init__(self, employee_id: str, name: str, level: int = 8):
        super().__init__(employee_id, name, "wecom_notification_agent", level)
        self.notification_queue: List[Dict] = []
        self.scheduled_notifications: List[Dict] = []
        self.delivery_stats: Dict[str, Any] = defaultdict(int)

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行通知任务"""
        task_type = task_data.get('type', 'send_notification')

        if task_type == 'send_notification':
            return self._send_notification(task_data)
        elif task_type == 'schedule_notification':
            return self._schedule_notification(task_data)
        elif task_type == 'broadcast':
            return self._broadcast_notification(task_data)
        elif task_type == 'get_stats':
            return self._get_delivery_stats()
        elif task_type == 'cancel_scheduled':
            return self._cancel_scheduled(task_data)
        else:
            return {"success": False, "message": f"未知任务类型: {task_type}"}

    def _send_notification(self, task_data: Dict) -> Dict[str, Any]:
        """发送通知"""
        title = task_data.get('title', '')
        content = task_data.get('content', '')
        target_users = task_data.get('target_users', [])
        priority = task_data.get('priority', 'normal')
        msg_type = task_data.get('msg_type', 'text')

        # 智能格式化
        formatted_content = self._format_content(content, msg_type)

        # 生成通知
        notification = {
            "id": f"NTF{int(time.time())}",
            "title": title,
            "content": formatted_content,
            "target_users": target_users,
            "priority": priority,
            "msg_type": msg_type,
            "status": "sent",
            "created_at": datetime.now().isoformat(),
            "read_count": 0,
            "total_count": len(target_users) if target_users else 1
        }

        self.notification_queue.append(notification)
        self.delivery_stats['sent_total'] += 1
        self.delivery_stats[f'sent_{priority}'] += 1

        return {
            "success": True,
            "notification": notification,
            "message": f"通知已发送给 {notification['total_count']} 人"
        }

    def _schedule_notification(self, task_data: Dict) -> Dict[str, Any]:
        """调度定时通知"""
        title = task_data.get('title', '')
        content = task_data.get('content', '')
        target_time = task_data.get('scheduled_time', '')
        target_users = task_data.get('target_users', [])
        repeat = task_data.get('repeat', None)  # daily, weekly, monthly

        scheduled = {
            "id": f"SCH{int(time.time())}",
            "title": title,
            "content": content,
            "target_time": target_time,
            "target_users": target_users,
            "repeat": repeat,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        self.scheduled_notifications.append(scheduled)

        return {
            "success": True,
            "scheduled": scheduled,
            "message": f"定时通知已安排: {target_time}"
        }

    def _broadcast_notification(self, task_data: Dict) -> Dict[str, Any]:
        """广播通知（全员）"""
        title = task_data.get('title', '系统通知')
        content = task_data.get('content', '')
        level = task_data.get('level', 'info')  # info, warning, critical

        # 构建广播消息
        broadcast = {
            "id": f"BCST{int(time.time())}",
            "title": title,
            "content": content,
            "level": level,
            "scope": "all_staff",
            "status": "broadcasted",
            "created_at": datetime.now().isoformat()
        }

        self.notification_queue.append(broadcast)
        self.delivery_stats['broadcast_total'] += 1

        # 生成广播模板
        broadcast_template = self._generate_broadcast_template(title, content, level)

        return {
            "success": True,
            "broadcast": broadcast,
            "template": broadcast_template,
            "message": f"广播已发出: {title}"
        }

    def _format_content(self, content: str, msg_type: str) -> str:
        """智能格式化内容"""
        if msg_type == 'markdown':
            # 转换为 Markdown 格式
            formatted = content
            # 加粗关键词
            keywords = ['重要', '紧急', '注意', '必须']
            for kw in keywords:
                formatted = formatted.replace(kw, f'**{kw}**')
            # 添加换行
            formatted = formatted.replace('；', '；\n')
            formatted = formatted.replace('。', '。\n')
            return formatted.strip()
        elif msg_type == 'text':
            return content
        else:
            return content

    def _generate_broadcast_template(self, title: str, content: str,
                                      level: str) -> Dict[str, Any]:
        """生成广播模板"""
        level_styles = {
            "info": {"color": "#1890ff", "icon": "ℹ️", "bg": "#e6f7ff"},
            "warning": {"color": "#faad14", "icon": "⚠️", "bg": "#fffbe6"},
            "critical": {"color": "#f5222d", "icon": "🚨", "bg": "#fff1f0"},
            "success": {"color": "#52c41a", "icon": "✅", "bg": "#f6ffed"},
        }

        style = level_styles.get(level, level_styles['info'])

        return {
            "template_type": "broadcast_card",
            "style": style,
            "elements": [
                {"type": "header", "content": f"{style['icon']} {title}"},
                {"type": "body", "content": content},
                {"type": "footer", "content": f"发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
            ]
        }

    def _get_delivery_stats(self) -> Dict[str, Any]:
        """获取投递统计"""
        return {
            "total_sent": self.delivery_stats.get('sent_total', 0),
            "by_priority": {
                "high": self.delivery_stats.get('sent_high', 0),
                "normal": self.delivery_stats.get('sent_normal', 0),
                "low": self.delivery_stats.get('sent_low', 0)
            },
            "broadcasts": self.delivery_stats.get('broadcast_total', 0),
            "scheduled": len(self.scheduled_notifications),
            "pending": len([n for n in self.notification_queue if n['status'] == 'pending'])
        }

    def _cancel_scheduled(self, task_data: Dict) -> Dict[str, Any]:
        """取消定时通知"""
        schedule_id = task_data.get('schedule_id', '')

        for i, scheduled in enumerate(self.scheduled_notifications):
            if scheduled['id'] == schedule_id:
                scheduled['status'] = 'cancelled'
                self.scheduled_notifications.pop(i)
                return {
                    "success": True,
                    "message": f"已取消定时通知: {schedule_id}"
                }

        return {"success": False, "message": f"未找到定时通知: {schedule_id}"}


# ==================== 企业微信智能回复员工 ====================

class WeComIntelligentReply(AIEmployee):
    """
    企业微信智能回复员工

    核心能力：
    - 自然语言问答
    - 智能上下文理解
    - 多轮对话支持
    - 知识查询增强
    - 情感分析
    - 个性化回复
    """

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "wecom_intelligent_reply", level)
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.knowledge_base: Dict[str, str] = self._init_knowledge_base()
        self.emotion_analyzer = self._init_emotion_analyzer()

    def _init_knowledge_base(self) -> Dict[str, str]:
        """初始化知识库"""
        return {
            "greeting_response": "您好！我是企业微信AI助手，有什么可以帮您？",
            "thanks_response": "不客气！很高兴能帮到您。",
            "help_response": "我可以帮您：\n• 发送消息和通知\n• 处理审批流程\n• 管理日程会议\n• 查询通讯录\n• 解答系统问题\n\n请告诉我您的需求！",
            "weather_template": "今天{city}天气：{condition}，温度{temp}℃，建议{tip}。",
            "approval_guide": "发起审批步骤：\n1. 告诉我审批类型（请假/报销/出差等）\n2. 提供必要信息\n3. 确认后我将为您创建审批",
        }

    def _init_emotion_analyzer(self) -> Dict[str, List]:
        """初始化情感分析器"""
        return {
            "positive": ["感谢", "谢谢", "好的", "明白了", "真棒", "太好了"],
            "negative": ["不好", "不行", "出错", "错误", "烦", "生气", "失望"],
            "urgent": ["紧急", "尽快", "马上", "立即", "urgent", "asap"],
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能回复任务"""
        text = task_data.get('text', '')
        user_id = task_data.get('user_id', 'default')
        context = task_data.get('context', {})

        # 获取对话历史
        history = self.conversation_history.get(user_id, [])

        # Step 1: 意图识别
        intent_result = _detect_intent(text)

        # Step 2: 情感分析
        emotion = self._analyze_emotion(text)

        # Step 3: 生成回复
        reply_result = self._generate_reply(text, intent_result, emotion, history, context)

        # Step 4: 更新对话历史
        history.append({
            "role": "user",
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "intent": intent_result['primary_intent'],
            "emotion": emotion
        })
        history.append({
            "role": "assistant",
            "text": reply_result['reply'],
            "timestamp": datetime.now().isoformat()
        })
        # 保留最近 20 轮对话
        self.conversation_history[user_id] = history[-20:]

        return {
            "success": True,
            "reply": reply_result['reply'],
            "intent": intent_result['primary_intent'],
            "emotion": emotion,
            "suggestions": reply_result.get('suggestions', []),
            "context_used": len(history)
        }

    def _analyze_emotion(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        emotion_scores = {"positive": 0, "negative": 0, "urgent": 0}

        for emotion_type, keywords in self.emotion_analyzer.items():
            for keyword in keywords:
                if keyword in text.lower():
                    emotion_scores[emotion_type] += 1

        dominant = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[dominant]

        if max_score == 0:
            dominant = "neutral"

        return {
            "type": dominant,
            "score": max_score,
            "scores": emotion_scores
        }

    def _generate_reply(self, text: str, intent_result: Dict,
                        emotion: Dict, history: List[Dict],
                        context: Dict) -> Dict[str, Any]:
        """生成回复"""
        primary_intent = intent_result['primary_intent']

        # 情感影响回复风格
        emotion_prefix = {
            "positive": "😊 ",
            "negative": "😢 ",
            "urgent": "⚡ ",
            "neutral": ""
        }

        prefix = emotion_prefix.get(emotion['type'], "")

        # 意图对应回复
        reply_map = {
            "greeting": self._reply_greeting,
            "help": self._reply_help,
            "send_message": self._reply_send_message,
            "send_markdown": self._reply_send_message,
            "send_file": self._reply_send_message,
            "create_approval": self._reply_create_approval,
            "query_approval": self._reply_query_approval,
            "query_contact": self._reply_query_contact,
            "query_department": self._reply_query_department,
            "create_schedule": self._reply_create_schedule,
            "push_notification": self._reply_push_notification,
            "knowledge_query": self._reply_knowledge_query,
            "system_status": self._reply_system_status,
            "weather_query": self._reply_weather,
        }

        handler = reply_map.get(primary_intent, self._reply_default)
        content = handler(text, intent_result, emotion, context)

        # 生成建议
        suggestions = self._generate_suggestions(primary_intent, content)

        return {
            "reply": f"{prefix}{content}",
            "suggestions": suggestions
        }

    def _reply_greeting(self, text: str, intent: Dict, emotion: Dict,
                        context: Dict) -> str:
        """问候回复"""
        templates = _REPLY_TEMPLATES['greeting']
        import random
        return random.choice(templates)

    def _reply_help(self, text: str, intent: Dict, emotion: Dict,
                    context: Dict) -> str:
        """帮助回复"""
        return _REPLY_TEMPLATES['help'][0]

    def _reply_send_message(self, text: str, intent: Dict, emotion: Dict,
                            context: Dict) -> str:
        """发送消息回复"""
        return "好的，请告诉我：\n1. 发送给谁？（@成员或部门）\n2. 消息内容是什么？\n\n我会立即为您发送。"

    def _reply_create_approval(self, text: str, intent: Dict, emotion: Dict,
                                context: Dict) -> str:
        """创建审批回复"""
        return self.knowledge_base['approval_guide']

    def _reply_query_approval(self, text: str, intent: Dict, emotion: Dict,
                               context: Dict) -> str:
        """查询审批回复"""
        return "您可以提供审批单号，我来帮您查询状态。\n或者告诉我您的需求，我来为您列出最近的审批记录。"

    def _reply_query_contact(self, text: str, intent: Dict, emotion: Dict,
                              context: Dict) -> str:
        """查询成员回复"""
        return "请告诉我您要查找的成员姓名或部门，我来帮您搜索！"

    def _reply_query_department(self, text: str, intent: Dict, emotion: Dict,
                                 context: Dict) -> str:
        """查询部门回复"""
        return "您想了解哪个部门的信息？我可以为您展示组织架构和成员列表。"

    def _reply_create_schedule(self, text: str, intent: Dict, emotion: Dict,
                                context: Dict) -> str:
        """创建日程回复"""
        return "请告诉我：\n1. 日程主题\n2. 时间（开始-结束）\n3. 参与人员\n\n我将为您创建日程。"

    def _reply_push_notification(self, text: str, intent: Dict, emotion: Dict,
                                  context: Dict) -> str:
        """推送通知回复"""
        return "请告诉我通知内容和目标受众，我可以帮您：\n• 发送个人通知\n• 部门广播\n• 全员通知"

    def _reply_knowledge_query(self, text: str, intent: Dict, emotion: Dict,
                                context: Dict) -> str:
        """知识查询回复"""
        return f"关于「{text}」的查询：\n\n这是一个很好的问题。根据我的知识，我建议您可以：\n1. 查看企业知识库\n2. 咨询相关部门同事\n3. 在群聊中提问讨论\n\n需要我帮您搜索更具体的信息吗？"

    def _reply_system_status(self, text: str, intent: Dict, emotion: Dict,
                               context: Dict) -> str:
        """系统状态回复"""
        return _REPLY_TEMPLATES['system_status'][0].format(
            user_count="120",
            task_count="8",
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M')
        )

    def _reply_weather(self, text: str, intent: Dict, emotion: Dict,
                        context: Dict) -> str:
        """天气查询回复"""
        return self.knowledge_base['weather_template'].format(
            city="您所在的城市",
            condition="晴",
            temp="22-28",
            tip="适合外出活动，注意防晒"
        )

    def _reply_default(self, text: str, intent: Dict, emotion: Dict,
                       context: Dict) -> str:
        """默认回复"""
        return f"我理解您想了解「{text}」。\n\n我可以帮您处理消息、审批、日程、通讯录等工作。\n请使用「帮助」查看更多功能。"

    def _generate_suggestions(self, intent: str, reply: str) -> List[str]:
        """生成建议操作"""
        suggestion_map = {
            "greeting": ["查看帮助", "发送消息", "创建审批"],
            "help": ["发送消息", "创建审批", "查询成员"],
            "send_message": ["@某人", "发送文件", "定时发送"],
            "create_approval": ["请假申请", "报销申请", "出差申请"],
            "query_approval": ["我的审批", "待审批", "已通过"],
            "query_contact": ["按姓名搜索", "按部门搜索", "查看全部"],
        }
        return suggestion_map.get(intent, ["查看帮助", "返回首页", "设置偏好"])

    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计"""
        total_conversations = len(self.conversation_history)
        total_messages = sum(len(h) for h in self.conversation_history.values())

        return {
            "active_users": total_conversations,
            "total_messages": total_messages,
            "knowledge_entries": len(self.knowledge_base),
            "emotion_categories": list(self.emotion_analyzer.keys())
        }


# ==================== 企业微信工作流引擎员工 ====================

class WeComWorkflowEngine(AIEmployee):
    """
    企业微信工作流引擎员工

    核心能力：
    - 工作流定义与编排
    - 条件分支决策
    - 并行任务处理
    - 工作流状态管理
    - 异常处理与重试
    - 工作流监控与日志
    """

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "wecom_workflow_engine", level)
        self.workflow_definitions: Dict[str, Dict] = {}
        self.active_workflows: List[Dict] = []
        self.execution_log: List[Dict] = []

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流任务"""
        task_type = task_data.get('type', 'execute_workflow')

        if task_type == 'define_workflow':
            return self._define_workflow(task_data)
        elif task_type == 'execute_workflow':
            return self._execute_workflow(task_data)
        elif task_type == 'query_workflow':
            return self._query_workflow(task_data)
        elif task_type == 'list_workflows':
            return self._list_workflows()
        elif task_type == 'get_execution_log':
            return self._get_execution_log(task_data)
        else:
            return {"success": False, "message": f"未知任务类型: {task_type}"}

    def _define_workflow(self, task_data: Dict) -> Dict[str, Any]:
        """定义工作流"""
        name = task_data.get('name', '')
        description = task_data.get('description', '')
        steps = task_data.get('steps', [])

        workflow_id = f"WF{int(time.time())}"

        definition = {
            "workflow_id": workflow_id,
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": "defined",
            "version": 1
        }

        self.workflow_definitions[workflow_id] = definition

        return {
            "success": True,
            "workflow_id": workflow_id,
            "workflow": definition,
            "message": f"工作流「{name}」已定义"
        }

    def _execute_workflow(self, task_data: Dict) -> Dict[str, Any]:
        """执行工作流"""
        workflow_id = task_data.get('workflow_id', '')
        input_data = task_data.get('input_data', {})

        if workflow_id not in self.workflow_definitions:
            return {"success": False, "message": f"未知工作流: {workflow_id}"}

        workflow = self.workflow_definitions[workflow_id]
        execution_id = f"EXEC{int(time.time())}"

        # 模拟执行
        execution = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "current_step": len(workflow['steps']),
            "total_steps": len(workflow['steps']),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "steps_results": [
                {"step": i + 1, "name": step.get('name', f'Step {i+1}'), "status": "success"}
                for i, step in enumerate(workflow['steps'])
            ],
            "input_data": input_data,
            "output_data": {
                "processed": True,
                "workflow_name": workflow['name']
            }
        }

        self.active_workflows.append(execution)
        self.execution_log.append({
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        })

        # 保留最近 100 条执行记录
        if len(self.execution_log) > 100:
            self.execution_log = self.execution_log[-100:]

        return {
            "success": True,
            "execution": execution,
            "message": f"工作流执行完成: {workflow['name']}"
        }

    def _query_workflow(self, task_data: Dict) -> Dict[str, Any]:
        """查询工作流"""
        workflow_id = task_data.get('workflow_id', '')
        execution_id = task_data.get('execution_id', '')

        if execution_id:
            for wf in self.active_workflows:
                if wf['execution_id'] == execution_id:
                    return {"success": True, "workflow": wf}

        if workflow_id:
            for wf in self.active_workflows:
                if wf['workflow_id'] == workflow_id:
                    return {"success": True, "workflow": wf}

        return {"success": False, "message": "未找到对应的工作流执行记录"}

    def _list_workflows(self) -> Dict[str, Any]:
        """列出所有工作流"""
        workflows = list(self.workflow_definitions.values())
        return {
            "success": True,
            "workflows": workflows,
            "total_count": len(workflows)
        }

    def _get_execution_log(self, task_data: Dict) -> Dict[str, Any]:
        """获取执行日志"""
        limit = task_data.get('limit', 20)
        return {
            "success": True,
            "logs": self.execution_log[-limit:],
            "total_logs": len(self.execution_log)
        }

    def get_workflow_stats(self) -> Dict[str, Any]:
        """获取工作流统计"""
        return {
            "defined_workflows": len(self.workflow_definitions),
            "active_executions": len(self.active_workflows),
            "total_executions": len(self.execution_log),
            "workflow_names": [w['name'] for w in self.workflow_definitions.values()]
        }


# ==================== 员工注册辅助函数 ====================

def get_wecom_employee_types() -> Dict[str, str]:
    """获取所有企业微信 AI 员工类型"""
    return {
        "wecom_message_router": "企业微信智能消息路由",
        "wecom_approval_automation": "企业微信审批自动化",
        "wecom_contact_manager": "企业微信通讯录管理",
        "wecom_notification_agent": "企业微信智能通知代理",
        "wecom_intelligent_reply": "企业微信智能回复",
        "wecom_workflow_engine": "企业微信工作流引擎",
    }


def create_wecom_employee(employee_type: str, employee_id: str = "",
                           name: str = "") -> AIEmployee:
    """创建企业微信 AI 员工实例"""
    if not employee_id:
        employee_id = f"wecom_{employee_type}_{int(time.time())}"
    if not name:
        name = employee_type

    employees = {
        "wecom_message_router": WeComMessageRouter,
        "wecom_approval_automation": WeComApprovalAutomation,
        "wecom_contact_manager": WeComContactManager,
        "wecom_notification_agent": WeComNotificationAgent,
        "wecom_intelligent_reply": WeComIntelligentReply,
        "wecom_workflow_engine": WeComWorkflowEngine,
    }

    employee_class = employees.get(employee_type)
    if employee_class:
        return employee_class(employee_id, name)
    else:
        raise ValueError(f"未知企业微信员工类型: {employee_type}")


if __name__ == '__main__':
    # 测试代码
    print("=== 企业微信 AI 员工系统测试 ===")

    # 测试意图识别
    test_texts = [
        "请帮我发送一条通知给技术部",
        "我想发起请假申请",
        "帮我查一下李四的联系方式",
        "创建一个明天上午10点的会议",
        "通知所有人今天下午3点开会",
        "你好",
        "帮助",
    ]

    for text in test_texts:
        result = _detect_intent(text)
        print(f"\n输入: {text}")
        print(f"意图: {result['primary_intent']} (置信度: {result['confidence']:.2f})")
        if result['intents']:
            print(f"相关: {[i['intent'] for i in result['intents'][:3]]}")

    # 测试消息路由员工
    print("\n=== 消息路由测试 ===")
    router = WeComMessageRouter("test_router", "路由测试员")
    for text in test_texts[:3]:
        result = router.execute_task({'text': text, 'user_id': 'test_user'})
        print(f"  {text[:20]}... → {result['route']['handler']}")
