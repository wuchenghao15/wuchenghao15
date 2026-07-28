#!/usr/bin/env python3
"""AI智能客户关系管理Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AICRMAgent(AIEmployee):
    """AI客户关系管理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI客户关系专家"):
        super().__init__(employee_id, name, 'crm', 7)
        self.skills = [
            '客户管理', '销售管理', '客户服务',
            '营销自动化', '客户分析', '销售预测',
            '客户分层', '忠诚度管理', 'CRM报表'
        ]
        self.customers = {}
        self.opportunities = {}
        self.crm_history = []
        self.total_customers = 0
    
    def add_customer(self, customer_data: Dict) -> Dict[str, Any]:
        """添加客户"""
        customer_id = f"cust_{datetime.now().timestamp()}"
        
        customer = {
            'customer_id': customer_id,
            'name': customer_data.get('name', ''),
            'email': customer_data.get('email', ''),
            'phone': customer_data.get('phone', ''),
            'company': customer_data.get('company', ''),
            'industry': customer_data.get('industry', ''),
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_contact': None,
            'value': customer_data.get('value', 0),
            'interactions': []
        }
        
        self.customers[customer_id] = customer
        self.total_customers += 1
        
        return customer
    
    def add_interaction(self, customer_id: str, interaction_data: Dict) -> Dict[str, Any]:
        """添加互动记录"""
        if customer_id not in self.customers:
            return {'error': '客户不存在'}
        
        customer = self.customers[customer_id]
        
        interaction = {
            'id': f"inter_{datetime.now().timestamp()}",
            'type': interaction_data.get('type', 'call'),
            'content': interaction_data.get('content', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        customer['interactions'].append(interaction)
        customer['last_contact'] = interaction['timestamp']
        
        return interaction
    
    def add_opportunity(self, opportunity_data: Dict) -> Dict[str, Any]:
        """添加销售机会"""
        opportunity_id = f"opp_{datetime.now().timestamp()}"
        
        opportunity = {
            'opportunity_id': opportunity_id,
            'customer_id': opportunity_data.get('customer_id', ''),
            'name': opportunity_data.get('name', ''),
            'value': opportunity_data.get('value', 0),
            'stage': opportunity_data.get('stage', 'lead'),
            'probability': opportunity_data.get('probability', 0),
            'expected_close_date': opportunity_data.get('expected_close_date', ''),
            'created_at': datetime.now().isoformat()
        }
        
        self.opportunities[opportunity_id] = opportunity
        
        return opportunity
    
    def analyze_customer(self, customer_id: str) -> Dict[str, Any]:
        """分析客户"""
        if customer_id not in self.customers:
            return {'error': '客户不存在'}
        
        customer = self.customers[customer_id]
        interactions = customer.get('interactions', [])
        
        recency = len(interactions)
        frequency = len(interactions)
        monetary = customer.get('value', 0)
        
        if monetary >= 10000:
            tier = 'VIP'
        elif monetary >= 1000:
            tier = 'Gold'
        else:
            tier = 'Standard'
        
        engagement_score = recency * 0.3 + frequency * 0.3 + (monetary / 1000) * 0.4
        
        return {
            'customer_id': customer_id,
            'name': customer['name'],
            'company': customer['company'],
            'industry': customer['industry'],
            'status': customer['status'],
            'tier': tier,
            'value': customer['value'],
            'engagement_score': round(engagement_score, 2),
            'interaction_count': len(interactions),
            'last_contact': customer['last_contact'],
            'timestamp': datetime.now().isoformat()
        }
    
    def sales_forecast(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """销售预测"""
        total_pipeline = sum(o.get('value', 0) for o in opportunities)
        weighted_forecast = sum(o.get('value', 0) * o.get('probability', 0) / 100 for o in opportunities)
        
        stages = {}
        for o in opportunities:
            stage = o.get('stage', 'unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        return {
            'total_pipeline': round(total_pipeline, 2),
            'weighted_forecast': round(weighted_forecast, 2),
            'opportunity_count': len(opportunities),
            'stage_distribution': stages,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_crm_report(self) -> str:
        """生成CRM报告"""
        report_lines = []
        report_lines.append("# CRM报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        active_customers = sum(1 for c in self.customers.values() if c['status'] == 'active')
        total_value = sum(c.get('value', 0) for c in self.customers.values())
        
        report_lines.append("## 客户统计")
        report_lines.append(f"- 总客户数: {self.total_customers}")
        report_lines.append(f"- 活跃客户: {active_customers}")
        report_lines.append(f"- 客户总价值: {round(total_value, 2)}")
        report_lines.append("")
        
        report_lines.append("## 销售机会")
        report_lines.append(f"- 总机会数: {len(self.opportunities)}")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        active_customers = sum(1 for c in self.customers.values() if c['status'] == 'active')
        
        return {
            'total_customers': self.total_customers,
            'active_customers': active_customers,
            'total_opportunities': len(self.opportunities),
            'recent_actions': self.crm_history[-5:]
        }

crm_agent = AICRMAgent('ai_crm_001')
