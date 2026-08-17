#!/usr/bin/env python3
"""AI智能客服Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AICustomerServiceAgent(AIEmployee):
    """AI客服Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI客服专家"):
        super().__init__(employee_id, name, 'customer_service', 6)
        self.skills = [
            '客户咨询', '问题解答', '投诉处理',
            '订单查询', '退换货处理', '售后服务',
            '满意度调查', '工单管理', '知识库查询'
        ]
        self.tickets = {}
        self.ticket_history = []
        self.total_tickets = 0
        self.resolved_tickets = 0
    
    def create_ticket(self, ticket_data: Dict) -> Dict[str, Any]:
        """创建工单"""
        ticket_id = f"ticket_{datetime.now().timestamp()}"
        
        ticket = {
            'ticket_id': ticket_id,
            'customer_id': ticket_data.get('customer_id', ''),
            'customer_name': ticket_data.get('customer_name', ''),
            'type': ticket_data.get('type', 'question'),
            'priority': ticket_data.get('priority', 'medium'),
            'subject': ticket_data.get('subject', ''),
            'description': ticket_data.get('description', ''),
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        
        self.tickets[ticket_id] = ticket
        self.total_tickets += 1
        
        return ticket
    
    def add_message(self, ticket_id: str, role: str, content: str) -> Dict[str, Any]:
        """添加消息"""
        if ticket_id not in self.tickets:
            return {'error': '工单不存在'}
        
        ticket = self.tickets[ticket_id]
        message = {
            'id': f"msg_{datetime.now().timestamp()}",
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        ticket['messages'].append(message)
        ticket['updated_at'] = message['timestamp']
        
        return message
    
    def resolve_ticket(self, ticket_id: str, resolution: str) -> Dict[str, Any]:
        """解决工单"""
        if ticket_id not in self.tickets:
            return {'error': '工单不存在'}
        
        ticket = self.tickets[ticket_id]
        ticket['status'] = 'resolved'
        ticket['resolution'] = resolution
        ticket['resolved_at'] = datetime.now().isoformat()
        
        self.resolved_tickets += 1
        
        return ticket
    
    def escalate_ticket(self, ticket_id: str, reason: str) -> Dict[str, Any]:
        """升级工单"""
        if ticket_id not in self.tickets:
            return {'error': '工单不存在'}
        
        ticket = self.tickets[ticket_id]
        ticket['status'] = 'escalated'
        ticket['escalation_reason'] = reason
        ticket['escalated_at'] = datetime.now().isoformat()
        
        return ticket
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """回答问题"""
        faq = {
            'shipping': {
                'keywords': ['shipping', 'delivery', '发货', '配送', '物流'],
                'answer': '我们提供多种配送方式，标准配送一般需要3-5个工作日，加急配送1-2个工作日。具体配送时间取决于您的位置。'
            },
            'return': {
                'keywords': ['return', 'refund', '退货', '退款', '退换'],
                'answer': '您可以在收到商品后7天内申请退货退款。请确保商品完好无损，并保留原始包装。'
            },
            'order': {
                'keywords': ['order', 'order status', '订单', '状态', '查询'],
                'answer': '您可以在个人中心查看订单状态。如果您有任何问题，请提供订单号以便我们查询。'
            },
            'payment': {
                'keywords': ['payment', 'pay', '支付', '结算'],
                'answer': '我们支持多种支付方式，包括支付宝、微信支付、银行卡等。支付过程安全可靠。'
            },
            'product': {
                'keywords': ['product', 'item', '商品', '产品'],
                'answer': '我们的产品均经过严格质量检测。如需了解产品详情，请访问产品页面或联系客服。'
            }
        }
        
        matched_category = None
        for category, data in faq.items():
            for keyword in data['keywords']:
                if keyword in question.lower():
                    matched_category = category
                    break
            if matched_category:
                break
        
        if matched_category:
            answer = faq[matched_category]['answer']
        else:
            answer = '感谢您的提问！我已记录您的问题，客服人员将尽快与您联系。'
        
        return {
            'question': question,
            'category': matched_category or 'other',
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_ticket_stats(self) -> Dict:
        """获取工单统计"""
        open_count = sum(1 for t in self.tickets.values() if t['status'] == 'open')
        resolved_count = sum(1 for t in self.tickets.values() if t['status'] == 'resolved')
        escalated_count = sum(1 for t in self.tickets.values() if t['status'] == 'escalated')
        
        return {
            'total_tickets': self.total_tickets,
            'open_tickets': open_count,
            'resolved_tickets': resolved_count,
            'escalated_tickets': escalated_count,
            'resolution_rate': round(resolved_count / max(1, self.total_tickets) * 100, 2),
            'recent_tickets': self.ticket_history[-5:]
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.get_ticket_stats()

customer_service_agent = AICustomerServiceAgent('ai_customer_service_001')
