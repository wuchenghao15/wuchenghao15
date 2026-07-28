# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""AI员工模块"""
import logging
from datetime import datetime
from typing import Dict, Any, List
logger = logging.getLogger(__name__)

# 智能赋能系统
try:
    from ai_engines.intelligent_empowerment import PersonalitySystem, NetworkLearningEngine
    from ai_engines.intelligent_empowerment import EMOTION_STATES, KNOWLEDGE_SOURCES
    _EMPOWERMENT_AVAILABLE = True
except ImportError:
    _EMPOWERMENT_AVAILABLE = False

import random

# 角色到性格和领域的映射
_ROLE_PERSONALITY = {
    'developer': 'creative', 'tester': 'analytical', 'designer': 'creative',
    'analyst': 'analytical', 'security': 'cautious', 'operations': 'driven',
    'writer': 'creative', 'manager': 'driven', 'version_manager': 'cautious',
    'automation_planner': 'driven', 'general': 'analytical',
}
_ROLE_DOMAIN = {
    'developer': 'general_programming', 'tester': 'validation', 'designer': 'general_programming',
    'analyst': 'system_admin', 'security': 'system_admin', 'operations': 'system_admin',
    'writer': 'education', 'manager': 'system_admin', 'version_manager': 'system_admin',
    'automation_planner': 'general_programming', 'general': 'general_programming',
}


class AIEmployee:
    def __init__(self, employee_id: str, name: str, role: str, skills: List[str]):
        self.employee_id = employee_id
        self.name = name
        self.role = role
        self.skills = skills
        self.status = 'active'
        self.created_at = datetime.now().isoformat()
        self.last_task = None

        # 智能赋能初始化
        self.empowerment_enabled = False
        self.personality = None
        self.learning_engine = None
        self.decision_history: List[Dict] = []
        if _EMPOWERMENT_AVAILABLE:
            try:
                ptype = _ROLE_PERSONALITY.get(role, 'analytical')
                domain = _ROLE_DOMAIN.get(role, 'general_programming')
                self.personality = PersonalitySystem(ptype)
                self.learning_engine = NetworkLearningEngine(employee_id, domain)
                self.empowerment_enabled = True
            except Exception as e:
                logger.warning(f"AI员工 {name} 智能赋能初始化失败: {e}")

        logger.info(f"AI员工创建: {name} ({role}) 赋能={'✓' if self.empowerment_enabled else '✗'}")

    def execute_task(self, task) -> Dict[str, Any]:
        self.last_task = task
        logger.info(f"AI员工 {self.name} 执行任务: {task}")
        result = {'success': True, 'employee_id': self.employee_id, 'employee_name': self.name, 'task': task, 'result': f"任务完成", 'timestamp': datetime.now().isoformat()}

        # 赋能执行
        if self.empowerment_enabled:
            success = result.get('success', False)
            self.personality.update_emotion('routine_task', success)
            self.learning_engine.learn_from_network(duration=random.randint(10, 20))
            style = self.personality.get_response_style()
            result['empowerment'] = {
                'personality_emoji': style['emoji'],
                'emotion': self.personality.emotion,
                'emotion_label': EMOTION_STATES.get(self.personality.emotion, {}).get('label', ''),
                'energy': style['energy'],
            }

        return result

    def empowered_execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """赋能执行任务"""
        if not self.empowerment_enabled:
            return self.execute_task(task_data.get('type', 'general'))
        task_str = task_data.get('type', str(task_data))
        self.last_task = task_str
        result = {'success': True, 'employee_id': self.employee_id, 'employee_name': self.name, 'task': task_str, 'result': f"任务完成", 'timestamp': datetime.now().isoformat()}

        success = result.get('success', False)
        self.personality.update_emotion('complex_task', success)
        self.learning_engine.learn_from_network(duration=random.randint(10, 30))
        upgrade = self.learning_engine.auto_upgrade_check()
        style = self.personality.get_response_style()
        if style['prefix']:
            result['message'] = f"{style['prefix']} 任务完成"
        result['empowerment'] = {
            'personality_emoji': style['emoji'],
            'emotion': self.personality.emotion,
            'emotion_label': EMOTION_STATES.get(self.personality.emotion, {}).get('label', ''),
            'energy': style['energy'],
            'performance_modifier': style['performance_modifier'],
            'upgrade_ready': upgrade.get('upgrade_ready', False),
        }
        return result

    def get_status(self) -> Dict[str, Any]:
        return {'employee_id': self.employee_id, 'name': self.name, 'role': self.role, 'status': self.status, 'skills': self.skills, 'last_task': self.last_task, 'created_at': self.created_at}

    def get_empowerment_profile(self) -> Dict[str, Any]:
        """获取智能赋能档案"""
        if not self.empowerment_enabled:
            return {'enabled': False, 'employee_id': self.employee_id, 'name': self.name, 'role': self.role}
        return {
            'enabled': True,
            'employee_id': self.employee_id,
            'name': self.name,
            'type': self.role,
            'personality': self.personality.get_personality_profile(),
            'learning_stats': self.learning_engine.get_learning_stats(),
            'knowledge_topics': len(self.learning_engine.knowledge_base),
            'certifications': self.learning_engine.certifications,
            'decision_count': len(self.decision_history),
        }

    def get_personality_detail(self) -> Dict[str, Any]:
        if not self.personality:
            return {}
        return self.personality.get_personality_profile()

    def get_learning_detail(self) -> Dict[str, Any]:
        if not self.learning_engine:
            return {}
        return {
            'stats': self.learning_engine.get_learning_stats(),
            'knowledge_base': self.learning_engine.get_knowledge_base(),
            'recent_history': self.learning_engine.get_learning_history(10),
            'upgrade_status': self.learning_engine.auto_upgrade_check(),
            'certifications': self.learning_engine.certifications,
        }

    def trigger_learning_session(self, topic=None, duration=30) -> Dict[str, Any]:
        if not self.learning_engine:
            return {'success': False, 'message': '学习引擎未初始化'}
        return self.learning_engine.learn_from_network(topic, duration)

    def rest_employee(self) -> Dict[str, Any]:
        if self.personality:
            self.personality.rest()
            return {'success': True, 'message': f'{self.name} 已休息，能量恢复至 {self.personality.energy}'}
        return {'success': False, 'message': '性格系统未初始化'}

class AIEmployeeManager:
    def __init__(self):
        self.employees = {}
        logger.info("AI员工管理器初始化完成")

    def add_employee(self, employee: AIEmployee):
        self.employees[employee.employee_id] = employee
        logger.info(f"AI员工已添加: {employee.name}")

    def get_employee(self, employee_id: str) -> AIEmployee:
        return self.employees.get(employee_id)

    def list_employees(self) -> List[Dict[str, Any]]:
        return [emp.get_status() for emp in self.employees.values()]

    def assign_task(self, employee_id: str, task: str) -> Dict[str, Any]:
        employee = self.get_employee(employee_id)
        if not employee:
            return {'success': False, 'message': 'AI员工不存在'}
        return employee.execute_task(task)

ai_employee_manager = AIEmployeeManager()

def init_ai_employees():
    logger.info("初始化AI员工...")
    employees = [
        AIEmployee('ai_dev_001', 'AI开发工程师', 'developer', ['Python', 'Flask', '机器学习']),
        AIEmployee('ai_tester_001', 'AI测试工程师', 'tester', ['自动化测试', '性能测试', '安全测试']),
        AIEmployee('ai_designer_001', 'AI设计师', 'designer', ['UI设计', 'UX设计', '前端开发']),
        AIEmployee('ai_analyst_001', 'AI数据分析师', 'analyst', ['数据分析', '数据可视化', '统计分析']),
        AIEmployee('ai_security_001', 'AI安全专家', 'security', ['网络安全', '渗透测试', '安全审计']),
        AIEmployee('ai_ops_001', 'AI运维工程师', 'operations', ['系统运维', 'DevOps', '云服务']),
        AIEmployee('ai_writer_001', 'AI文案撰写师', 'writer', ['内容创作', '技术文档', 'SEO优化']),
        AIEmployee('ai_manager_001', 'AI项目经理', 'manager', ['项目管理', '团队协调', '进度跟踪']),
        AIEmployee('version_agent_001', '系统版本管理Agent', 'version_manager', 
                   ['版本监控', '规则维护', '版本显示', '版本存储', '更新触发', '处罚规则', '自动维护']),
        AIEmployee('automation_plan_agent_001', '自动化计划拓展Agent', 'automation_planner', 
                   ['计划分析', '功能拓展', '计划优化', '自动补全', '计划创建', '效率提升', '智能调度'])
    ]
    for emp in employees:
        ai_employee_manager.add_employee(emp)
    logger.info(f"AI员工初始化完成,共 {len(employees)} 名员工")

if __name__ == "__main__":
    init_ai_employees()
