# -*- coding: utf-8 -*-
"""
AI员工增强系统
包含：自动生成、协作通信、组织层级、思维逻辑矩阵
"""

import os
import json
import logging
import sqlite3
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from flask import jsonify

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'app.db')


class ThinkingMatrix:
    """思维逻辑矩阵 - 多维度思考框架"""
    
    # 思维维度定义
    DIMENSIONS = {
        'logical': {
            'name': '逻辑推理维度',
            'sub_dimensions': ['演绎推理', '归纳推理', '类比推理', '因果推理'],
            'weight': 0.25
        },
        'analytical': {
            'name': '分析分解维度',
            'sub_dimensions': ['问题分解', '因素分析', '数据解析', '结构分析'],
            'weight': 0.20
        },
        'creative': {
            'name': '创新创造维度',
            'sub_dimensions': ['方案创新', '技术革新', '流程优化', '策略设计'],
            'weight': 0.15
        },
        'critical': {
            'name': '批判评估维度',
            'sub_dimensions': ['质量评估', '风险判断', '优劣对比', '决策建议'],
            'weight': 0.15
        },
        'systemic': {
            'name': '系统整合维度',
            'sub_dimensions': ['全局视角', '关联分析', '整体优化', '协同整合'],
            'weight': 0.15
        },
        'practical': {
            'name': '实践执行维度',
            'sub_dimensions': ['方案落地', '执行监控', '效果评估', '迭代改进'],
            'weight': 0.10
        }
    }
    
    def __init__(self):
        self.matrix_scores = {}
        self.thinking_history = []
        
    def evaluate_thinking(self, employee_id: str, task_type: str, context: Dict) -> Dict:
        """评估思维过程"""
        scores = {}
        
        for dim_key, dim_info in self.DIMENSIONS.items():
            sub_scores = {}
            for sub_dim in dim_info['sub_dimensions']:
                # 基于任务类型和上下文评估每个子维度
                score = self._calculate_sub_dimension_score(
                    dim_key, sub_dim, task_type, context
                )
                sub_scores[sub_dim] = score
            
            # 计算维度总分
            avg_score = sum(sub_scores.values()) / len(sub_scores)
            scores[dim_key] = {
                'score': avg_score,
                'sub_scores': sub_scores,
                'weight': dim_info['weight']
            }
        
        # 计算综合思维评分
        total_score = sum(
            s['score'] * s['weight'] for s in scores.values()
        )
        
        return {
            'employee_id': employee_id,
            'task_type': task_type,
            'scores': scores,
            'total_score': round(total_score, 2),
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._generate_recommendations(scores)
        }
    
    def _calculate_sub_dimension_score(self, dimension: str, sub_dim: str, 
                                        task_type: str, context: Dict) -> float:
        """计算子维度评分"""
        # 基础评分
        base_scores = {
            'code_fix': {'logical': 90, 'analytical': 95, 'creative': 70, 
                        'critical': 85, 'systemic': 80, 'practical': 90},
            'maintenance': {'logical': 85, 'analytical': 80, 'creative': 60, 
                           'critical': 90, 'systemic': 95, 'practical': 85},
            'optimization': {'logical': 80, 'analytical': 90, 'creative': 85, 
                            'critical': 80, 'systemic': 90, 'practical': 75},
            'analysis': {'logical': 95, 'analytical': 95, 'creative': 50, 
                        'critical': 90, 'systemic': 85, 'practical': 70},
            'collaboration': {'logical': 75, 'analytical': 80, 'creative': 80, 
                             'critical': 70, 'systemic': 95, 'practical': 90}
        }
        
        task_scores = base_scores.get(task_type, base_scores['code_fix'])
        base = task_scores.get(dimension, 70)
        
        # 根据上下文调整
        if context.get('complexity') == 'high':
            base = min(base + 5, 100)
        if context.get('urgency') == 'high':
            base = min(base + 3, 100)
        if context.get('previous_failures', 0) > 0:
            base = max(base - context['previous_failures'] * 2, 50)
        
        return round(base + (hash(sub_dim) % 10 - 5) / 10, 1)
    
    def _generate_recommendations(self, scores: Dict) -> List[str]:
        """生成思维改进建议"""
        recommendations = []
        
        for dim_key, dim_data in scores.items():
            if dim_data['score'] < 75:
                weak_subs = [
                    sub for sub, score in dim_data['sub_scores'].items() 
                    if score < 70
                ]
                if weak_subs:
                    recommendations.append(
                        f"建议加强{self.DIMENSIONS[dim_key]['name']}中的{weak_subs[0]}能力"
                    )
        
        if not recommendations:
            recommendations.append("思维矩阵评分良好，继续保持")
        
        return recommendations
    
    def get_thinking_report(self, employee_id: str) -> Dict:
        """获取思维报告"""
        history = [
            h for h in self.thinking_history 
            if h['employee_id'] == employee_id
        ]
        
        if not history:
            return {'message': '暂无思维评估记录'}
        
        # 计算平均分
        avg_scores = {}
        for dim_key in self.DIMENSIONS.keys():
            scores = [h['scores'][dim_key]['score'] for h in history]
            avg_scores[dim_key] = round(sum(scores) / len(scores), 2)
        
        return {
            'employee_id': employee_id,
            'total_evaluations': len(history),
            'average_scores': avg_scores,
            'latest_evaluation': history[-1],
            'improvement_trend': self._calculate_improvement_trend(history)
        }
    
    def _calculate_improvement_trend(self, history: List) -> str:
        """计算改进趋势"""
        if len(history) < 2:
            return "需要更多评估数据"
        
        recent_avg = sum(h['total_score'] for h in history[-5:]) / min(5, len(history))
        earlier_avg = sum(h['total_score'] for h in history[:5]) / min(5, len(history))
        
        if recent_avg > earlier_avg + 2:
            return "持续进步"
        elif recent_avg < earlier_avg - 2:
            return "需要关注"
        else:
            return "稳定发展"


class OrganizationHierarchy:
    """AI员工组织层级架构"""
    
    # 层级定义
    HIERARCHY_LEVELS = {
        'commander': {
            'level': 1,
            'name': '指挥官',
            'description': '全局决策和战略制定',
            'authority': ['create_employee', 'dismiss_employee', 'assign_task', 
                         'set_strategy', 'override_decision'],
            'max_subordinates': 10
        },
        'director': {
            'level': 2,
            'name': '总监',
            'description': '领域管理和任务分配',
            'authority': ['assign_task', 'monitor_progress', 'report_status',
                         'coordinate_team', 'request_resources'],
            'max_subordinates': 5
        },
        'manager': {
            'level': 3,
            'name': '经理',
            'description': '团队管理和执行监督',
            'authority': ['execute_task', 'delegate_task', 'monitor_member',
                         'report_progress', 'request_help'],
            'max_subordinates': 3
        },
        'specialist': {
            'level': 4,
            'name': '专家',
            'description': '专业领域执行',
            'authority': ['execute_task', 'report_result', 'suggest_improvement',
                         'request_guidance'],
            'max_subordinates': 0
        },
        'worker': {
            'level': 5,
            'name': '执行者',
            'description': '具体任务执行',
            'authority': ['execute_task', 'report_result'],
            'max_subordinates': 0
        }
    }
    
    def __init__(self):
        self.organization_tree = {}
        self.relationships = defaultdict(list)
        
    def add_employee_to_hierarchy(self, employee: Dict, level: str, 
                                   supervisor_id: Optional[str] = None) -> Dict:
        """添加员工到组织架构"""
        level_info = self.HIERARCHY_LEVELS.get(level)
        if not level_info:
            return {'success': False, 'error': '无效的层级'}
        
        employee_id = employee.get('employee_id', str(uuid.uuid4()))
        
        # 检查上级是否有效
        if supervisor_id:
            supervisor = self.organization_tree.get(supervisor_id)
            if not supervisor:
                return {'success': False, 'error': '上级不存在'}
            
            # 检查上级下属数量限制
            current_subordinates = len(self.relationships[supervisor_id])
            if current_subordinates >= supervisor['level_info']['max_subordinates']:
                return {'success': False, 'error': '上级下属数量已达上限'}
        
        # 添加到组织树
        self.organization_tree[employee_id] = {
            'employee': employee,
            'level': level,
            'level_info': level_info,
            'supervisor_id': supervisor_id,
            'subordinates': [],
            'joined_at': datetime.now().isoformat()
        }
        
        # 建立上下级关系
        if supervisor_id:
            self.relationships[supervisor_id].append(employee_id)
            self.organization_tree[supervisor_id]['subordinates'].append(employee_id)
        
        return {
            'success': True,
            'employee_id': employee_id,
            'level': level,
            'level_info': level_info,
            'supervisor_id': supervisor_id
        }
    
    def get_organization_structure(self) -> Dict:
        """获取组织结构"""
        structure = {
            'levels': self.HIERARCHY_LEVELS,
            'tree': {},
            'relationships': dict(self.relationships)
        }
        
        # 构建树形结构
        for emp_id, emp_data in self.organization_tree.items():
            if emp_data['supervisor_id'] is None:
                # 顶层员工
                structure['tree'][emp_id] = self._build_subtree(emp_id)
        
        return structure
    
    def _build_subtree(self, employee_id: str) -> Dict:
        """构建子树"""
        emp_data = self.organization_tree.get(employee_id)
        if not emp_data:
            return {}
        
        subtree = {
            'employee_id': employee_id,
            'name': emp_data['employee'].get('name', 'Unknown'),
            'level': emp_data['level'],
            'level_name': emp_data['level_info']['name'],
            'subordinates': []
        }
        
        for sub_id in emp_data['subordinates']:
            subtree['subordinates'].append(self._build_subtree(sub_id))
        
        return subtree
    
    def can_execute_action(self, employee_id: str, action: str) -> Tuple[bool, str]:
        """检查员工是否有权限执行某动作"""
        emp_data = self.organization_tree.get(employee_id)
        if not emp_data:
            return False, '员工不存在'
        
        if action in emp_data['level_info']['authority']:
            return True, '有权限'
        
        return False, '无权限执行此操作'
    
    def delegate_task(self, from_id: str, to_id: str, task: Dict) -> Dict:
        """任务委派"""
        # 检查委派权限
        can_delegate, reason = self.can_execute_action(from_id, 'delegate_task')
        if not can_delegate:
            return {'success': False, 'error': reason}
        
        # 检查是否是下属
        emp_data = self.organization_tree.get(from_id)
        if to_id not in emp_data['subordinates']:
            return {'success': False, 'error': '只能委派给下属'}
        
        return {
            'success': True,
            'task': task,
            'from': from_id,
            'to': to_id,
            'delegated_at': datetime.now().isoformat()
        }


class CollaborationSystem:
    """AI员工协作通信系统"""
    
    MESSAGE_TYPES = {
        'task_request': '任务请求',
        'task_response': '任务响应',
        'help_request': '协助请求',
        'help_response': '协助响应',
        'status_report': '状态报告',
        'knowledge_share': '知识共享',
        'alert': '告警通知',
        'coordination': '协调指令',
        'feedback': '反馈建议',
        'learning': '学习交流'
    }
    
    def __init__(self):
        self.message_queue = []
        self.collaboration_sessions = {}
        self.employee_channels = defaultdict(list)
        self.lock = threading.Lock()
        
    def send_message(self, from_id: str, to_id: str, 
                     message_type: str, content: Dict) -> Dict:
        """发送消息"""
        if message_type not in self.MESSAGE_TYPES:
            return {'success': False, 'error': '无效的消息类型'}
        
        message = {
            'message_id': str(uuid.uuid4()),
            'from': from_id,
            'to': to_id,
            'type': message_type,
            'type_name': self.MESSAGE_TYPES[message_type],
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent',
            'read': False
        }
        
        with self.lock:
            self.message_queue.append(message)
            self.employee_channels[to_id].append(message)
        
        return {
            'success': True,
            'message_id': message['message_id'],
            'timestamp': message['timestamp']
        }
    
    def receive_messages(self, employee_id: str, unread_only: bool = True) -> List[Dict]:
        """接收消息"""
        with self.lock:
            messages = self.employee_channels.get(employee_id, [])
            
            if unread_only:
                messages = [m for m in messages if not m['read']]
            
            # 标记为已读
            for m in messages:
                m['read'] = True
        
        return messages
    
    def broadcast_message(self, from_id: str, to_group: List[str], 
                          message_type: str, content: Dict) -> Dict:
        """广播消息"""
        results = []
        for to_id in to_group:
            result = self.send_message(from_id, to_id, message_type, content)
            results.append(result)
        
        return {
            'success': True,
            'broadcast_count': len(results),
            'results': results
        }
    
    def create_collaboration_session(self, participants: List[str], 
                                      task: Dict) -> Dict:
        """创建协作会话"""
        session_id = str(uuid.uuid4())
        
        session = {
            'session_id': session_id,
            'participants': participants,
            'task': task,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'contributions': defaultdict(dict),
            'decisions': []
        }
        
        # 通知所有参与者
        for participant in participants:
            self.send_message(
                'system', participant, 'coordination',
                {'session_id': session_id, 'task': task, 'action': 'join'}
            )
        
        self.collaboration_sessions[session_id] = session
        
        return {
            'success': True,
            'session_id': session_id,
            'participants': participants
        }
    
    def add_contribution(self, session_id: str, employee_id: str, 
                         contribution: Dict) -> Dict:
        """添加协作贡献"""
        session = self.collaboration_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}
        
        if employee_id not in session['participants']:
            return {'success': False, 'error': '非参与者'}
        
        contribution_id = str(uuid.uuid4())
        session['contributions'][employee_id][contribution_id] = {
            'contribution': contribution,
            'timestamp': datetime.now().isoformat()
        }
        
        # 通知其他参与者
        others = [p for p in session['participants'] if p != employee_id]
        self.broadcast_message(
            employee_id, others, 'knowledge_share',
            {'session_id': session_id, 'contribution': contribution}
        )
        
        return {
            'success': True,
            'contribution_id': contribution_id,
            'session_id': session_id
        }
    
    def make_decision(self, session_id: str, decision: Dict, 
                      decision_maker: str) -> Dict:
        """协作决策"""
        session = self.collaboration_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}
        
        decision_record = {
            'decision_id': str(uuid.uuid4()),
            'decision': decision,
            'decision_maker': decision_maker,
            'timestamp': datetime.now().isoformat(),
            'consensus': self._calculate_consensus(session, decision)
        }
        
        session['decisions'].append(decision_record)
        
        # 通知所有参与者
        self.broadcast_message(
            decision_maker, session['participants'], 'coordination',
            {'session_id': session_id, 'decision': decision, 'action': 'decided'}
        )
        
        return {
            'success': True,
            'decision': decision_record
        }
    
    def _calculate_consensus(self, session: Dict, decision: Dict) -> float:
        """计算共识度"""
        total = len(session['participants'])
        if total == 0:
            return 0
        
        # 基于贡献数量计算共识度
        contributing = len(session['contributions'])
        consensus = (contributing / total) * 100
        
        return round(min(consensus, 100), 2)
    
    def get_collaboration_report(self, session_id: str) -> Dict:
        """获取协作报告"""
        session = self.collaboration_sessions.get(session_id)
        if not session:
            return {'success': False, 'error': '会话不存在'}
        
        return {
            'success': True,
            'session': session,
            'statistics': {
                'participants_count': len(session['participants']),
                'contributions_count': sum(
                    len(c) for c in session['contributions'].values()
                ),
                'decisions_count': len(session['decisions']),
                'duration': self._calculate_session_duration(session)
            }
        }
    
    def _calculate_session_duration(self, session: Dict) -> str:
        """计算会话持续时间"""
        start = datetime.fromisoformat(session['created_at'])
        end = datetime.now()
        duration = end - start
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        return f"{hours}小时{minutes}分钟"


class AIEmployeeAutoGenerator:
    """AI员工自动生成器"""
    
    # AI员工模板库
    EMPLOYEE_TEMPLATES = {
        'code_fixer': {
            'name_prefix': '代码修复',
            'category': 'development',
            'capabilities': ['语法错误检测', '逻辑错误修复', '代码优化'],
            'thinking_focus': ['logical', 'analytical'],
            'min_level': 'specialist'
        },
        'system_maintenance': {
            'name_prefix': '系统维护',
            'category': 'maintenance',
            'capabilities': ['数据库清理', '日志管理', '健康检查'],
            'thinking_focus': ['systemic', 'practical'],
            'min_level': 'specialist'
        },
        'data_analyzer': {
            'name_prefix': '数据分析',
            'category': 'analysis',
            'capabilities': ['数据统计', '趋势分析', '可视化生成'],
            'thinking_focus': ['analytical', 'critical'],
            'min_level': 'specialist'
        },
        'security_guard': {
            'name_prefix': '安全守护',
            'category': 'security',
            'capabilities': ['入侵检测', '漏洞扫描', '安全加固'],
            'thinking_focus': ['critical', 'systemic'],
            'min_level': 'manager'
        },
        'performance_optimizer': {
            'name_prefix': '性能优化',
            'category': 'optimization',
            'capabilities': ['性能监控', '瓶颈识别', '优化建议'],
            'thinking_focus': ['analytical', 'creative'],
            'min_level': 'specialist'
        },
        'qa_validator': {
            'name_prefix': '质量验证',
            'category': 'quality',
            'capabilities': ['功能测试', '回归测试', '缺陷报告'],
            'thinking_focus': ['critical', 'practical'],
            'min_level': 'worker'
        },
        'knowledge_manager': {
            'name_prefix': '知识管理',
            'category': 'knowledge',
            'capabilities': ['知识提取', '知识分类', '知识更新'],
            'thinking_focus': ['systemic', 'creative'],
            'min_level': 'specialist'
        },
        'coordinator': {
            'name_prefix': '任务协调',
            'category': 'coordination',
            'capabilities': ['任务分配', '进度跟踪', '资源调度'],
            'thinking_focus': ['systemic', 'practical'],
            'min_level': 'manager'
        },
        'version_upgrader': {
            'name_prefix': '版本升级',
            'category': 'development',
            'capabilities': ['版本规划', '升级执行', '回滚操作', '发布管理'],
            'thinking_focus': ['systemic', 'practical'],
            'min_level': 'manager'
        },
        'dependency_manager': {
            'name_prefix': '依赖管理',
            'category': 'maintenance',
            'capabilities': ['依赖扫描', '安全更新', '兼容性测试', '版本锁定'],
            'thinking_focus': ['analytical', 'critical'],
            'min_level': 'specialist'
        },
        'frontend_engineer': {
            'name_prefix': '前端开发',
            'category': 'development',
            'capabilities': ['页面开发', '性能优化', '用户体验', '响应式设计'],
            'thinking_focus': ['creative', 'analytical'],
            'min_level': 'specialist'
        },
        'backend_engineer': {
            'name_prefix': '后端开发',
            'category': 'development',
            'capabilities': ['API开发', '数据库设计', '业务逻辑', '系统架构'],
            'thinking_focus': ['logical', 'systemic'],
            'min_level': 'specialist'
        },
        'devops_engineer': {
            'name_prefix': 'DevOps',
            'category': 'maintenance',
            'capabilities': ['自动化部署', 'CI/CD', '监控告警', '故障排查'],
            'thinking_focus': ['systemic', 'practical'],
            'min_level': 'manager'
        },
        'ai_trainer': {
            'name_prefix': 'AI训练',
            'category': 'ai',
            'capabilities': ['模型训练', '参数调优', '模型评估', '知识注入'],
            'thinking_focus': ['creative', 'analytical'],
            'min_level': 'specialist'
        },
        'git_manager': {
            'name_prefix': 'Git管理',
            'category': 'development',
            'capabilities': ['分支管理', '代码提交', '合并冲突解决', '版本控制'],
            'thinking_focus': ['systemic', 'logical'],
            'min_level': 'specialist'
        },
        'monitoring_analyst': {
            'name_prefix': '监控分析',
            'category': 'maintenance',
            'capabilities': ['系统监控', '异常检测', '性能分析', '告警处理'],
            'thinking_focus': ['analytical', 'critical'],
            'min_level': 'specialist'
        },
        'exam_system_expert': {
            'name_prefix': '考试系统',
            'category': 'business',
            'capabilities': ['试卷生成', '考试管理', '成绩分析', '题库优化'],
            'thinking_focus': ['systemic', 'practical'],
            'min_level': 'specialist'
        },
        'learning_analyst': {
            'name_prefix': '学习分析',
            'category': 'business',
            'capabilities': ['学习路径规划', '知识图谱', '错题分析', '个性化推荐'],
            'thinking_focus': ['analytical', 'creative'],
            'min_level': 'specialist'
        },
        'diagnostics_repair': {
            'name_prefix': '诊断修复',
            'category': 'maintenance',
            'capabilities': ['系统诊断', '问题检测', '自动修复', '健康监控', '报告生成', '根因分析'],
            'thinking_focus': ['analytical', 'critical', 'systemic'],
            'min_level': 'specialist'
        }
    }
    
    def __init__(self):
        self.generated_employees = {}
        self.generation_history = []
        
    def analyze_system_needs(self) -> Dict:
        """分析系统需求"""
        needs = {
            'code_quality': 0,
            'system_health': 0,
            'data_processing': 0,
            'security_level': 0,
            'performance': 0,
            'quality_assurance': 0,
            'knowledge_management': 0,
            'coordination': 0,
            'version_upgrade': 0,
            'dependency_update': 0,
            'frontend_development': 0,
            'backend_development': 0,
            'devops_automation': 0,
            'ai_training': 0,
            'git_management': 0,
            'monitoring_analysis': 0,
            'exam_system': 0,
            'learning_analysis': 0
        }
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # 分析错误数量
            cursor.execute('SELECT COUNT(*) FROM error_types WHERE status != "resolved"')
            unresolved_errors = cursor.fetchone()[0] or 0
            needs['code_quality'] = min(unresolved_errors / 10, 10)
            
            # 分析系统日志
            cursor.execute('SELECT COUNT(*) FROM system_logs WHERE level = "ERROR"')
            error_logs = cursor.fetchone()[0] or 0
            needs['system_health'] = min(error_logs / 20, 10)
            
            # 分析用户数量
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0] or 0
            needs['data_processing'] = min(user_count / 100, 10)
            
            # 分析安全事件
            cursor.execute('SELECT COUNT(*) FROM security_logs WHERE severity >= 3')
            security_events = cursor.fetchone()[0] or 0
            needs['security_level'] = min(security_events / 5, 10)
            
            # 分析性能指标
            cursor.execute('SELECT AVG(response_time) FROM api_metrics')
            avg_response_time = cursor.fetchone()[0] or 0
            needs['performance'] = min(avg_response_time / 500, 10)
            
            # 分析版本历史
            cursor.execute('SELECT COUNT(*) FROM version_history')
            version_count = cursor.fetchone()[0] or 0
            needs['version_upgrade'] = min(version_count / 10, 10)
            
            # 分析考试数据
            cursor.execute('SELECT COUNT(*) FROM exams')
            exam_count = cursor.fetchone()[0] or 0
            needs['exam_system'] = min(exam_count / 50, 10)
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"分析系统需求时出错: {e}")
        
        return needs
    
    def generate_employee(self, template_key: str, custom_config: Optional[Dict] = None) -> Dict:
        """生成AI员工"""
        template = self.EMPLOYEE_TEMPLATES.get(template_key)
        if not template:
            return {'success': False, 'error': '无效的模板'}
        
        employee_id = f"emp_{template_key}_{uuid.uuid4().hex[:8]}"
        
        # 合合配置
        config = {**template}
        if custom_config:
            config.update(custom_config)
        
        employee = {
            'employee_id': employee_id,
            'name': f"{config['name_prefix']}员工_{uuid.uuid4().hex[:4]}",
            'category': config['category'],
            'capabilities': config['capabilities'],
            'thinking_focus': config['thinking_focus'],
            'status': 'active',
            'efficiency': 85 + (hash(employee_id) % 15),
            'workload': 0,
            'created_at': datetime.now().isoformat(),
            'generation_source': 'auto_generator',
            'template_key': template_key
        }
        
        # 保存到数据库
        self._save_employee_to_db(employee)
        
        # 记录生成历史
        self.generation_history.append({
            'employee_id': employee_id,
            'template_key': template_key,
            'generated_at': datetime.now().isoformat(),
            'reason': custom_config.get('reason', '系统需求') if custom_config else '系统需求'
        })
        
        self.generated_employees[employee_id] = employee
        
        return {
            'success': True,
            'employee': employee,
            'message': f"成功生成AI员工: {employee['name']}"
        }
    
    def _save_employee_to_db(self, employee: Dict):
        """保存员工到数据库"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    capabilities TEXT,
                    efficiency INTEGER,
                    workload INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    status TEXT,
                    thinking_focus TEXT,
                    generation_source TEXT,
                    template_key TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_employees VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                employee['employee_id'],
                employee['name'],
                f"{employee['category']}专家",
                f"自动生成的{employee['category']}领域AI员工",
                employee['category'],
                json.dumps(employee['capabilities']),
                employee['efficiency'],
                employee['workload'],
                employee['created_at'],
                employee['created_at'],
                employee['status'],
                json.dumps(employee['thinking_focus']),
                employee['generation_source'],
                employee['template_key']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存AI员工到数据库失败: {e}")
    
    def auto_generate_based_needs(self) -> Dict:
        """基于系统需求自动生成"""
        needs = self.analyze_system_needs()
        
        generated = []
        
        # 根据需求生成员工
        need_template_mapping = {
            'code_quality': 'code_fixer',
            'system_health': 'system_maintenance',
            'data_processing': 'data_analyzer',
            'security_level': 'security_guard',
            'performance': 'performance_optimizer',
            'quality_assurance': 'qa_validator',
            'knowledge_management': 'knowledge_manager',
            'coordination': 'coordinator',
            'version_upgrade': 'version_upgrader',
            'dependency_update': 'dependency_manager',
            'frontend_development': 'frontend_engineer',
            'backend_development': 'backend_engineer',
            'devops_automation': 'devops_engineer',
            'ai_training': 'ai_trainer',
            'git_management': 'git_manager',
            'monitoring_analysis': 'monitoring_analyst',
            'exam_system': 'exam_system_expert',
            'learning_analysis': 'learning_analyst'
        }
        
        for need_key, template_key in need_template_mapping.items():
            need_value = needs.get(need_key, 0)
            
            # 需求超过阈值时生成
            if need_value > 3:
                result = self.generate_employee(
                    template_key,
                    {'reason': f'{need_key}需求较高({need_value})'}
                )
                if result['success']:
                    generated.append(result)
        
        return {
            'success': True,
            'needs_analysis': needs,
            'generated_count': len(generated),
            'generated_employees': generated
        }
    
    def get_generation_statistics(self) -> Dict:
        """获取生成统计"""
        return {
            'total_generated': len(self.generated_employees),
            'generation_history': self.generation_history[-20:],  # 最近20条
            'templates_used': dict(
                (k, len([h for h in self.generation_history if h['template_key'] == k]))
                for k in self.EMPLOYEE_TEMPLATES.keys()
            )
        }


class EnhancedAIEmployeeSystem:
    """增强型AI员工系统"""
    
    def __init__(self):
        self.thinking_matrix = ThinkingMatrix()
        self.organization = OrganizationHierarchy()
        self.collaboration = CollaborationSystem()
        self.generator = AIEmployeeAutoGenerator()
        self.active_employees = {}
        
        # 初始化默认组织结构
        self._init_default_organization()
        
    def _init_default_organization(self):
        """初始化默认组织结构"""
        # 创建指挥官
        commander = {
            'employee_id': 'emp_commander_001',
            'name': '系统指挥官',
            'capabilities': ['全局决策', '资源调配', '战略制定']
        }
        self.organization.add_employee_to_hierarchy(commander, 'commander')
        
        # 创建总监
        directors = [
            ('emp_dev_director', '开发总监', 'development'),
            ('emp_ops_director', '运维总监', 'operations'),
            ('emp_data_director', '数据总监', 'data')
        ]
        
        for emp_id, name, category in directors:
            director = {
                'employee_id': emp_id,
                'name': name,
                'capabilities': ['领域管理', '任务分配', '进度监控']
            }
            self.organization.add_employee_to_hierarchy(
                director, 'director', 'emp_commander_001'
            )
    
    def create_full_employee(self, template_key: str, level: str = 'specialist',
                             supervisor_id: Optional[str] = None) -> Dict:
        """创建完整的AI员工（包含所有维度）"""
        # 生成员工
        gen_result = self.generator.generate_employee(template_key)
        if not gen_result['success']:
            return gen_result
        
        employee = gen_result['employee']
        
        # 加入组织架构
        org_result = self.organization.add_employee_to_hierarchy(
            employee, level, supervisor_id
        )
        
        # 初始化思维矩阵
        thinking_eval = self.thinking_matrix.evaluate_thinking(
            employee['employee_id'],
            template_key,
            {'complexity': 'medium'}
        )
        
        self.thinking_matrix.thinking_history.append(thinking_eval)
        
        return {
            'success': True,
            'employee': employee,
            'organization': org_result,
            'thinking_evaluation': thinking_eval,
            'message': f"成功创建完整AI员工: {employee['name']}"
        }
    
    def assign_collaborative_task(self, task: Dict, 
                                   participants: List[str]) -> Dict:
        """分配协作任务"""
        # 创建协作会话
        session_result = self.collaboration.create_collaboration_session(
            participants, task
        )
        
        if not session_result['success']:
            return session_result
        
        session_id = session_result['session_id']
        
        # 通知所有参与者开始任务
        self.collaboration.broadcast_message(
            'system', participants, 'task_request',
            {'session_id': session_id, 'task': task, 'action': 'start'}
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'participants': participants,
            'task': task
        }
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            'organization_structure': self.organization.get_organization_structure(),
            'active_collaborations': len(self.collaboration.collaboration_sessions),
            'total_employees': len(self.organization.organization_tree),
            'generation_stats': self.generator.get_generation_statistics(),
            'pending_messages': sum(
                len([m for m in msgs if not m['read']])
                for msgs in self.collaboration.employee_channels.values()
            )
        }
    
    def train_employee(self, employee_id: str, training_type: str) -> Dict:
        """培训员工"""
        emp_data = self.organization.organization_tree.get(employee_id)
        if not emp_data:
            return {'success': False, 'error': '员工不存在'}
        
        # 增强思维能力
        thinking_eval = self.thinking_matrix.evaluate_thinking(
            employee_id,
            training_type,
            {'complexity': 'high', 'urgency': 'medium'}
        )
        
        self.thinking_matrix.thinking_history.append(thinking_eval)
        
        # 更新效率
        new_efficiency = min(emp_data['employee'].get('efficiency', 85) + 5, 100)
        emp_data['employee']['efficiency'] = new_efficiency
        
        return {
            'success': True,
            'employee_id': employee_id,
            'training_type': training_type,
            'thinking_evaluation': thinking_eval,
            'new_efficiency': new_efficiency,
            'message': f"培训完成，效率提升至{new_efficiency}%"
        }


# 全局实例
enhanced_system = None

def get_enhanced_system():
    """获取增强系统实例"""
    global enhanced_system
    if enhanced_system is None:
        enhanced_system = EnhancedAIEmployeeSystem()
    return enhanced_system


def init_enhanced_system():
    """初始化增强系统"""
    system = get_enhanced_system()
    logger.info("[AI员工增强系统] 初始化完成")
    return system


if __name__ == '__main__':
    init_enhanced_system()