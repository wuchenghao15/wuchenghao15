#!/usr/bin/env python3
"""AI智能项目管理Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIProjectManagementAgent(AIEmployee):
    """AI项目管理Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI项目管理专家"):
        super().__init__(employee_id, name, 'project_management', 8)
        self.skills = [
            '项目规划', '任务管理', '进度跟踪',
            '资源分配', '风险评估', '团队协作',
            '里程碑管理', '项目报告', '成本控制'
        ]
        self.projects = {}
        self.tasks = {}
        self.project_history = []
        self.total_projects = 0
    
    def create_project(self, project_data: Dict) -> Dict[str, Any]:
        """创建项目"""
        project_id = f"proj_{datetime.now().timestamp()}"
        
        project = {
            'project_id': project_id,
            'name': project_data.get('name', ''),
            'description': project_data.get('description', ''),
            'status': 'planning',
            'start_date': project_data.get('start_date', datetime.now().isoformat()),
            'end_date': project_data.get('end_date', ''),
            'budget': project_data.get('budget', 0),
            'team': project_data.get('team', []),
            'progress': 0,
            'created_at': datetime.now().isoformat()
        }
        
        self.projects[project_id] = project
        self.total_projects += 1
        
        return project
    
    def add_task(self, task_data: Dict) -> Dict[str, Any]:
        """添加任务"""
        task_id = f"task_{datetime.now().timestamp()}"
        
        task = {
            'task_id': task_id,
            'project_id': task_data.get('project_id', ''),
            'name': task_data.get('name', ''),
            'description': task_data.get('description', ''),
            'status': 'pending',
            'priority': task_data.get('priority', 'medium'),
            'assignee': task_data.get('assignee', ''),
            'due_date': task_data.get('due_date', ''),
            'created_at': datetime.now().isoformat()
        }
        
        self.tasks[task_id] = task
        
        return task
    
    def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """更新任务状态"""
        if task_id not in self.tasks:
            return {'error': '任务不存在'}
        
        task = self.tasks[task_id]
        task['status'] = status
        task['updated_at'] = datetime.now().isoformat()
        
        self._update_project_progress(task['project_id'])
        
        return task
    
    def _update_project_progress(self, project_id: str):
        """更新项目进度"""
        if project_id not in self.projects:
            return
        
        project = self.projects[project_id]
        project_tasks = [t for t in self.tasks.values() if t['project_id'] == project_id]
        
        if project_tasks:
            completed = sum(1 for t in project_tasks if t['status'] == 'completed')
            project['progress'] = round((completed / len(project_tasks)) * 100, 2)
    
    def analyze_project(self, project_id: str) -> Dict[str, Any]:
        """分析项目"""
        if project_id not in self.projects:
            return {'error': '项目不存在'}
        
        project = self.projects[project_id]
        project_tasks = [t for t in self.tasks.values() if t['project_id'] == project_id]
        
        total_tasks = len(project_tasks)
        completed_tasks = sum(1 for t in project_tasks if t['status'] == 'completed')
        pending_tasks = sum(1 for t in project_tasks if t['status'] == 'pending')
        in_progress_tasks = sum(1 for t in project_tasks if t['status'] == 'in_progress')
        
        risk_level = 'low'
        if project['progress'] < 30 and total_tasks > 10:
            risk_level = 'medium'
        if pending_tasks > completed_tasks * 2:
            risk_level = 'high'
        
        return {
            'project_id': project_id,
            'name': project['name'],
            'status': project['status'],
            'progress': project['progress'],
            'budget': project['budget'],
            'task_summary': {
                'total': total_tasks,
                'completed': completed_tasks,
                'in_progress': in_progress_tasks,
                'pending': pending_tasks
            },
            'risk_level': risk_level,
            'team_size': len(project.get('team', [])),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_project_report(self, project_id: str) -> str:
        """生成项目报告"""
        analysis = self.analyze_project(project_id)
        
        report_lines = []
        report_lines.append(f"# 项目报告 - {analysis['name']}")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("## 项目概览")
        report_lines.append(f"- 项目ID: {analysis['project_id']}")
        report_lines.append(f"- 状态: {analysis['status']}")
        report_lines.append(f"- 进度: {analysis['progress']}%")
        report_lines.append(f"- 风险等级: {analysis['risk_level']}")
        report_lines.append("")
        
        report_lines.append("## 任务统计")
        ts = analysis['task_summary']
        report_lines.append(f"- 总任务: {ts['total']}")
        report_lines.append(f"- 已完成: {ts['completed']}")
        report_lines.append(f"- 进行中: {ts['in_progress']}")
        report_lines.append(f"- 待处理: {ts['pending']}")
        
        return '\n'.join(report_lines)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        active_projects = sum(1 for p in self.projects.values() if p['status'] != 'completed')
        
        return {
            'total_projects': self.total_projects,
            'active_projects': active_projects,
            'total_tasks': len(self.tasks),
            'recent_projects': self.project_history[-5:]
        }

project_management_agent = AIProjectManagementAgent('ai_project_management_001')
