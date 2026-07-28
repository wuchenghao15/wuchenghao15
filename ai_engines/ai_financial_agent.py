#!/usr/bin/env python3
"""AI智能财务分析Agent"""

import os
import re
import logging
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIFinancialAgent(AIEmployee):
    """AI财务分析Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI财务分析专家"):
        super().__init__(employee_id, name, 'financial', 8)
        self.skills = [
            '财务分析', '预算管理', '成本控制',
            '投资分析', '风险评估', '财务报告',
            '现金流分析', '利润分析', '财务预测'
        ]
        self.financial_data = {}
        self.analysis_history = []
        self.total_analyses = 0
    
    def add_financial_record(self, record_type: str, data: Dict) -> Dict[str, Any]:
        """添加财务记录"""
        record_id = f"record_{datetime.now().timestamp()}"
        
        self.financial_data[record_id] = {
            'record_id': record_id,
            'type': record_type,
            'data': data,
            'created_at': datetime.now().isoformat()
        }
        
        return self.financial_data[record_id]
    
    def analyze_profit(self, revenue: List[float], expenses: List[float]) -> Dict[str, Any]:
        """分析利润"""
        if len(revenue) != len(expenses):
            return {'error': '收入和支出数据长度不一致'}
        
        profits = [r - e for r, e in zip(revenue, expenses)]
        total_revenue = sum(revenue)
        total_expenses = sum(expenses)
        total_profit = sum(profits)
        
        avg_profit = statistics.mean(profits) if profits else 0
        max_profit = max(profits) if profits else 0
        min_profit = min(profits) if profits else 0
        
        profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
        
        return {
            'total_revenue': round(total_revenue, 2),
            'total_expenses': round(total_expenses, 2),
            'total_profit': round(total_profit, 2),
            'avg_profit': round(avg_profit, 2),
            'max_profit': round(max_profit, 2),
            'min_profit': round(min_profit, 2),
            'profit_margin': round(profit_margin, 2),
            'monthly_profits': [round(p, 2) for p in profits],
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_cash_flow(self, inflows: List[float], outflows: List[float]) -> Dict[str, Any]:
        """分析现金流"""
        net_cash_flow = [i - o for i, o in zip(inflows, outflows)]
        cumulative_cash = []
        current = 0
        
        for ncf in net_cash_flow:
            current += ncf
            cumulative_cash.append(current)
        
        return {
            'total_inflows': round(sum(inflows), 2),
            'total_outflows': round(sum(outflows), 2),
            'net_cash_flow': [round(n, 2) for n in net_cash_flow],
            'cumulative_cash': [round(c, 2) for c in cumulative_cash],
            'final_cash_position': round(cumulative_cash[-1], 2) if cumulative_cash else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def budget_analysis(self, budget: Dict[str, float], actual: Dict[str, float]) -> Dict[str, Any]:
        """预算分析"""
        results = []
        
        for category in set(budget.keys()) | set(actual.keys()):
            budget_amount = budget.get(category, 0)
            actual_amount = actual.get(category, 0)
            variance = actual_amount - budget_amount
            variance_percent = (variance / budget_amount) * 100 if budget_amount > 0 else 0
            
            results.append({
                'category': category,
                'budget': round(budget_amount, 2),
                'actual': round(actual_amount, 2),
                'variance': round(variance, 2),
                'variance_percent': round(variance_percent, 2)
            })
        
        total_budget = sum(budget.values())
        total_actual = sum(actual.values())
        total_variance = total_actual - total_budget
        total_variance_percent = (total_variance / total_budget) * 100 if total_budget > 0 else 0
        
        return {
            'details': results,
            'total_budget': round(total_budget, 2),
            'total_actual': round(total_actual, 2),
            'total_variance': round(total_variance, 2),
            'total_variance_percent': round(total_variance_percent, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def investment_analysis(self, investments: List[Dict]) -> Dict[str, Any]:
        """投资分析"""
        results = []
        
        for inv in investments:
            initial = inv.get('initial', 0)
            current = inv.get('current', 0)
            return_rate = (current - initial) / initial * 100 if initial > 0 else 0
            
            results.append({
                'name': inv.get('name', ''),
                'initial': round(initial, 2),
                'current': round(current, 2),
                'return_rate': round(return_rate, 2),
                'risk_level': inv.get('risk', 'medium')
            })
        
        results.sort(key=lambda x: x['return_rate'], reverse=True)
        
        return {
            'investments': results,
            'best_performer': results[0] if results else None,
            'worst_performer': results[-1] if results else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_financial_report(self, data: Dict) -> str:
        """生成财务报告"""
        report_lines = []
        report_lines.append("# 财务分析报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        if 'profit' in data:
            p = data['profit']
            report_lines.append("## 利润分析")
            report_lines.append(f"- 总收入: {p['total_revenue']}")
            report_lines.append(f"- 总支出: {p['total_expenses']}")
            report_lines.append(f"- 总利润: {p['total_profit']}")
            report_lines.append(f"- 利润率: {p['profit_margin']}%")
            report_lines.append("")
        
        if 'cash_flow' in data:
            cf = data['cash_flow']
            report_lines.append("## 现金流分析")
            report_lines.append(f"- 总流入: {cf['total_inflows']}")
            report_lines.append(f"- 总流出: {cf['total_outflows']}")
            report_lines.append(f"- 期末现金: {cf['final_cash_position']}")
            report_lines.append("")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_analyses': self.total_analyses,
            'financial_records': len(self.financial_data),
            'recent_analyses': self.analysis_history[-5:]
        }

financial_agent = AIFinancialAgent('ai_financial_001')
