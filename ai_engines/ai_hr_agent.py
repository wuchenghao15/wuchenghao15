#!/usr/bin/env python3
"""AI智能人力资源Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIHRAgent(AIEmployee):
    """AI人力资源Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI人力资源专家"):
        super().__init__(employee_id, name, 'hr', 7)
        self.skills = [
            '员工管理', '招聘管理', '培训管理',
            '绩效考核', '薪酬管理', '考勤管理',
            '员工关怀', '离职管理', 'HR报表'
        ]
        self.employees = {}
        self.candidates = {}
        self.hr_history = []
        self.total_employees = 0
    
    def add_employee(self, employee_data: Dict) -> Dict[str, Any]:
        """添加员工"""
        employee_id = f"emp_{datetime.now().timestamp()}"
        
        employee = {
            'employee_id': employee_id,
            'name': employee_data.get('name', ''),
            'position': employee_data.get('position', ''),
            'department': employee_data.get('department', ''),
            'email': employee_data.get('email', ''),
            'hire_date': employee_data.get('hire_date', datetime.now().isoformat()),
            'status': 'active',
            'salary': employee_data.get('salary', 0),
            'skills': employee_data.get('skills', []),
            'performance_score': employee_data.get('performance_score', 0),
            'created_at': datetime.now().isoformat()
        }
        
        self.employees[employee_id] = employee
        self.total_employees += 1
        
        return employee
    
    def update_employee(self, employee_id: str, updates: Dict) -> Dict[str, Any]:
        """更新员工信息"""
        if employee_id not in self.employees:
            return {'error': '员工不存在'}
        
        employee = self.employees[employee_id]
        employee.update(updates)
        
        return employee
    
    def add_candidate(self, candidate_data: Dict) -> Dict[str, Any]:
        """添加候选人"""
        candidate_id = f"cand_{datetime.now().timestamp()}"
        
        candidate = {
            'candidate_id': candidate_id,
            'name': candidate_data.get('name', ''),
            'position': candidate_data.get('position', ''),
            'email': candidate_data.get('email', ''),
            'phone': candidate_data.get('phone', ''),
            'skills': candidate_data.get('skills', []),
            'experience': candidate_data.get('experience', 0),
            'status': 'applied',
            'created_at': datetime.now().isoformat()
        }
        
        self.candidates[candidate_id] = candidate
        
        return candidate
    
    def evaluate_candidate(self, candidate_id: str, criteria: Dict) -> Dict[str, Any]:
        """评估候选人"""
        if candidate_id not in self.candidates:
            return {'error': '候选人不存在'}
        
        candidate = self.candidates[candidate_id]
        skills = candidate.get('skills', [])
        
        score = 0
        for skill, weight in criteria.items():
            if skill in skills:
                score += weight
        
        max_score = sum(criteria.values())
        match_percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        return {
            'candidate_id': candidate_id,
            'name': candidate['name'],
            'position': candidate['position'],
            'score': round(score, 2),
            'match_percentage': round(match_percentage, 2),
            'recommendation': '推荐面试' if match_percentage >= 60 else '不推荐',
            'timestamp': datetime.now().isoformat()
        }
    
    def performance_review(self, employee_id: str, metrics: Dict) -> Dict[str, Any]:
        """绩效考核"""
        if employee_id not in self.employees:
            return {'error': '员工不存在'}
        
        employee = self.employees[employee_id]
        
        total_score = sum(metrics.values())
        avg_score = total_score / max(1, len(metrics))
        
        if avg_score >= 90:
            grade = 'A'
        elif avg_score >= 80:
            grade = 'B'
        elif avg_score >= 70:
            grade = 'C'
        elif avg_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        employee['performance_score'] = round(avg_score, 2)
        
        return {
            'employee_id': employee_id,
            'name': employee['name'],
            'department': employee['department'],
            'metrics': metrics,
            'total_score': round(total_score, 2),
            'avg_score': round(avg_score, 2),
            'grade': grade,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_salary(self, employee_id: str, base_salary: float, bonus: float = 0) -> Dict[str, Any]:
        """计算薪酬"""
        if employee_id not in self.employees:
            return {'error': '员工不存在'}
        
        employee = self.employees[employee_id]
        
        tax_rate = 0.2 if base_salary > 10000 else 0.15
        tax = base_salary * tax_rate
        net_salary = base_salary + bonus - tax
        
        return {
            'employee_id': employee_id,
            'name': employee['name'],
            'base_salary': round(base_salary, 2),
            'bonus': round(bonus, 2),
            'tax': round(tax, 2),
            'net_salary': round(net_salary, 2),
            'tax_rate': tax_rate * 100,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_hr_report(self) -> str:
        """生成HR报告"""
        report_lines = []
        report_lines.append("# HR报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        active_count = sum(1 for e in self.employees.values() if e['status'] == 'active')
        department_counts = {}
        
        for e in self.employees.values():
            dept = e.get('department', '未知')
            department_counts[dept] = department_counts.get(dept, 0) + 1
        
        report_lines.append("## 员工统计")
        report_lines.append(f"- 总员工数: {self.total_employees}")
        report_lines.append(f"- 在职员工: {active_count}")
        report_lines.append("")
        
        report_lines.append("## 部门分布")
        for dept, count in department_counts.items():
            report_lines.append(f"- {dept}: {count}人")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        active_count = sum(1 for e in self.employees.values() if e['status'] == 'active')
        
        return {
            'total_employees': self.total_employees,
            'active_employees': active_count,
            'candidates': len(self.candidates),
            'recent_actions': self.hr_history[-5:]
        }

hr_agent = AIHRAgent('ai_hr_001')
