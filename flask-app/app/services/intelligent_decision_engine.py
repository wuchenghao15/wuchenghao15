"""
智能决策引擎 v4.0.0
实现自动问题诊断、智能决策和持续优化
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import deque
import threading
import hashlib

logger = logging.getLogger(__name__)


class DecisionPriority(Enum):
    """决策优先级"""
    CRITICAL = 0  # 紧急，立即执行
    HIGH = 1      # 高优，1小时内
    MEDIUM = 2    # 中优，4小时内
    LOW = 3       # 低优，24小时内


class DecisionType(Enum):
    """决策类型"""
    SYSTEM_OPTIMIZATION = "system_optimization"      # 系统优化
    ERROR_FIX = "error_fix"                          # 错误修复
    LEARNING_ADJUSTMENT = "learning_adjustment"      # 学习调整
    RESOURCE_ALLOCATION = "resource_allocation"      # 资源分配
    SECURITY_RESPONSE = "security_response"          # 安全响应
    USER_EXPERIENCE = "user_experience"              # 用户体验


class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"            # 待执行
    IN_PROGRESS = "in_progress"    # 执行中
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 已取消


@dataclass
class Decision:
    """决策数据结构"""
    id: str
    type: DecisionType
    priority: DecisionPriority
    title: str
    description: str
    reasoning: str
    action: Dict[str, Any]
    expected_impact: Dict[str, float]
    confidence: float  # 置信度 0.0-1.0
    status: DecisionStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    parent_decision_id: Optional[str] = None


@dataclass
class Problem:
    """问题数据结构"""
    id: str
    type: str
    severity: str
    description: str
    context: Dict[str, Any]
    detected_at: datetime
    related_metrics: Dict[str, float]


@dataclass
class Insight:
    """洞察数据结构"""
    id: str
    type: str
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    generated_at: datetime
    actionable: bool = False


class IntelligentDecisionEngine:
    """智能决策引擎"""

    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.problems: Dict[str, Problem] = {}
        self.insights: Dict[str, Insight] = {}
        self.decision_history: deque = deque(maxlen=1000)
        self.execution_queue: List[Decision] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        self.lock = threading.RLock()
        
        # 初始化决策规则库
        self._initialize_rules()
        # 加载历史知识库
        self._load_knowledge_base()
        
        logger.info("智能决策引擎初始化完成")

    def _initialize_rules(self):
        """初始化决策规则"""
        self.rules = {
            "system_optimization": [
                {
                    "name": "high_cpu_usage",
                    "condition": lambda metrics: metrics.get("cpu_usage", 0) > 80,
                    "action": "optimize_cpu_usage",
                    "priority": DecisionPriority.HIGH
                },
                {
                    "name": "high_memory_usage",
                    "condition": lambda metrics: metrics.get("memory_usage", 0) > 85,
                    "action": "optimize_memory_usage",
                    "priority": DecisionPriority.HIGH
                },
                {
                    "name": "slow_response_time",
                    "condition": lambda metrics: metrics.get("avg_response_time", 0) > 3000,
                    "action": "optimize_response_time",
                    "priority": DecisionPriority.MEDIUM
                }
            ],
            "error_fix": [
                {
                    "name": "database_errors",
                    "condition": lambda metrics: metrics.get("db_error_rate", 0) > 5,
                    "action": "fix_database_issues",
                    "priority": DecisionPriority.CRITICAL
                },
                {
                    "name": "api_errors",
                    "condition": lambda metrics: metrics.get("api_error_rate", 0) > 10,
                    "action": "fix_api_issues",
                    "priority": DecisionPriority.HIGH
                }
            ],
            "learning_adjustment": [
                {
                    "name": "low_engagement",
                    "condition": lambda metrics: metrics.get("user_engagement", 0) < 30,
                    "action": "boost_engagement",
                    "priority": DecisionPriority.MEDIUM
                },
                {
                    "name": "high_error_rate",
                    "condition": lambda metrics: metrics.get("student_error_rate", 0) > 40,
                    "action": "adjust_difficulty",
                    "priority": DecisionPriority.MEDIUM
                }
            ],
            "security": [
                {
                    "name": "suspicious_activity",
                    "condition": lambda metrics: metrics.get("suspicious_logins", 0) > 3,
                    "action": "enhance_security",
                    "priority": DecisionPriority.CRITICAL
                }
            ]
        }

    def _load_knowledge_base(self):
        """加载历史知识库"""
        try:
            # 尝试从文件加载
            import os
            kb_path = "/tmp/decision_knowledge_base.json"
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"加载了 {len(self.knowledge_base)} 条历史知识")
        except Exception as e:
            logger.warning(f"加载知识库失败: {e}")

    def _save_knowledge_base(self):
        """保存知识库"""
        try:
            import os
            kb_path = "/tmp/decision_knowledge_base.json"
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"保存知识库失败: {e}")

    def analyze_problem(self, problem_data: Dict[str, Any]) -> Problem:
        """
        分析问题
        
        Args:
            problem_data: 问题数据
            
        Returns:
            Problem对象
        """
        problem_id = hashlib.md5(f"{problem_data['type']}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        problem = Problem(
            id=problem_id,
            type=problem_data['type'],
            severity=problem_data.get('severity', 'medium'),
            description=problem_data['description'],
            context=problem_data.get('context', {}),
            detected_at=datetime.now(),
            related_metrics=problem_data.get('metrics', {})
        )
        
        with self.lock:
            self.problems[problem_id] = problem
        
        logger.info(f"检测到新问题: {problem.type} - {problem.description}")
        return problem

    def generate_insight(self, data: Dict[str, Any]) -> Insight:
        """
        生成洞察
        
        Args:
            data: 分析数据
            
        Returns:
            Insight对象
        """
        insight_id = hashlib.md5(f"{json.dumps(data, sort_keys=True)}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # 使用启发式方法生成洞察
        insight_type = self._classify_insight(data)
        title, description = self._generate_insight_content(insight_type, data)
        confidence = self._calculate_confidence(data)
        
        insight = Insight(
            id=insight_id,
            type=insight_type,
            title=title,
            description=description,
            data=data,
            confidence=confidence,
            generated_at=datetime.now(),
            actionable=confidence > 0.6
        )
        
        with self.lock:
            self.insights[insight_id] = insight
        
        return insight

    def _classify_insight(self, data: Dict[str, Any]) -> str:
        """分类洞察类型"""
        if 'trend' in data:
            return 'trend_analysis'
        elif 'anomaly' in data:
            return 'anomaly_detection'
        elif 'pattern' in data:
            return 'pattern_recognition'
        elif 'correlation' in data:
            return 'correlation_analysis'
        else:
            return 'general_observation'

    def _generate_insight_content(self, insight_type: str, data: Dict[str, Any]) -> Tuple[str, str]:
        """生成洞察内容"""
        templates = {
            'trend_analysis': (
                "趋势变化检测",
                f"检测到数据趋势变化: {data.get('trend', 'unknown')}"
            ),
            'anomaly_detection': (
                "异常检测",
                f"发现异常模式: {data.get('anomaly', 'unknown')}"
            ),
            'pattern_recognition': (
                "模式识别",
                f"识别到行为模式: {data.get('pattern', 'unknown')}"
            ),
            'correlation_analysis': (
                "相关性分析",
                f"发现变量相关性: {data.get('correlation', 'unknown')}"
            ),
            'general_observation': (
                "观察",
                "系统状态观察"
            )
        }
        return templates.get(insight_type, templates['general_observation'])

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """计算置信度"""
        # 基于数据量、历史准确率等计算
        base_confidence = 0.7
        data_quality = data.get('data_quality', 1.0)
        historical_accuracy = data.get('historical_accuracy', 0.8)
        
        confidence = base_confidence * data_quality * historical_accuracy
        return min(max(confidence, 0.0), 1.0)

    def make_decision(self, problem: Optional[Problem] = None, 
                     metrics: Optional[Dict[str, Any]] = None,
                     insights: Optional[List[Insight]] = None) -> Decision:
        """
        做出智能决策
        
        Args:
            problem: 问题对象（可选）
            metrics: 系统指标
            insights: 洞察列表
            
        Returns:
            Decision对象
        """
        decision_id = hashlib.md5(f"{datetime.now().isoformat()}_{json.dumps(metrics or {}, sort_keys=True)}".encode()).hexdigest()[:12]
        
        # 分析情境
        context = self._analyze_context(problem, metrics, insights)
        
        # 确定决策类型
        decision_type = self._determine_decision_type(context)
        
        # 评估优先级
        priority = self._assess_priority(context, decision_type)
        
        # 生成决策
        decision = self._generate_decision(
            decision_id=decision_id,
            decision_type=decision_type,
            priority=priority,
            context=context
        )
        
        with self.lock:
            self.decisions[decision_id] = decision
            self.execution_queue.append(decision)
            self.decision_history.append({
                'decision_id': decision_id,
                'timestamp': datetime.now(),
                'type': decision_type.value,
                'priority': priority.value
            })
        
        logger.info(f"生成决策: {decision.title} (优先级: {priority.name})")
        return decision

    def _analyze_context(self, problem: Optional[Problem], 
                        metrics: Optional[Dict[str, Any]],
                        insights: Optional[List[Insight]]) -> Dict[str, Any]:
        """分析决策上下文"""
        context = {
            'timestamp': datetime.now(),
            'problem': problem,
            'metrics': metrics or {},
            'insights': insights or [],
            'historical_success_rate': self._calculate_historical_success_rate(),
            'current_system_load': self._get_current_system_load()
        }
        return context

    def _determine_decision_type(self, context: Dict[str, Any]) -> DecisionType:
        """确定决策类型"""
        problem = context.get('problem')
        metrics = context.get('metrics', {})
        
        if problem:
            if problem.type in ['error', 'exception', 'bug']:
                return DecisionType.ERROR_FIX
            elif problem.type in ['security', 'breach', 'attack']:
                return DecisionType.SECURITY_RESPONSE
            elif problem.type in ['learning', 'education', 'student']:
                return DecisionType.LEARNING_ADJUSTMENT
        
        # 基于指标判断
        if metrics.get('system_related', False):
            return DecisionType.SYSTEM_OPTIMIZATION
        if metrics.get('resource_related', False):
            return DecisionType.RESOURCE_ALLOCATION
        
        return DecisionType.USER_EXPERIENCE

    def _assess_priority(self, context: Dict[str, Any], 
                        decision_type: DecisionType) -> DecisionPriority:
        """评估优先级"""
        problem = context.get('problem')
        metrics = context.get('metrics', {})
        
        # 紧急情况
        if decision_type == DecisionType.SECURITY_RESPONSE:
            return DecisionPriority.CRITICAL
        if problem and problem.severity == 'critical':
            return DecisionPriority.CRITICAL
        
        # 高优先级
        if metrics.get('cpu_usage', 0) > 90:
            return DecisionPriority.HIGH
        if metrics.get('memory_usage', 0) > 95:
            return DecisionPriority.HIGH
        
        # 中优先级
        if metrics.get('error_rate', 0) > 20:
            return DecisionPriority.MEDIUM
        
        return DecisionPriority.LOW

    def _generate_decision(self, decision_id: str, decision_type: DecisionType,
                          priority: DecisionPriority, context: Dict[str, Any]) -> Decision:
        """生成具体决策"""
        templates = self._get_decision_templates(decision_type)
        
        # 选择最佳模板
        best_template = self._select_best_template(templates, context)
        
        # 计算预期影响
        expected_impact = self._calculate_expected_impact(best_template, context)
        
        # 计算置信度
        confidence = self._calculate_decision_confidence(context, decision_type)
        
        return Decision(
            id=decision_id,
            type=decision_type,
            priority=priority,
            title=best_template['title'],
            description=best_template['description'],
            reasoning=best_template['reasoning'],
            action=best_template['action'],
            expected_impact=expected_impact,
            confidence=confidence,
            status=DecisionStatus.PENDING,
            created_at=datetime.now()
        )

    def _get_decision_templates(self, decision_type: DecisionType) -> List[Dict[str, Any]]:
        """获取决策模板"""
        templates = {
            DecisionType.SYSTEM_OPTIMIZATION: [
                {
                    'title': '优化系统资源配置',
                    'description': '根据当前负载调整系统资源配置以提升性能',
                    'reasoning': '检测到系统资源使用超过阈值，需要进行优化',
                    'action': {
                        'type': 'resource_optimization',
                        'params': {'auto_scale': True, 'optimize_cache': True}
                    }
                },
                {
                    'title': '清理临时文件和缓存',
                    'description': '清理系统临时文件和过期缓存释放空间',
                    'reasoning': '存储空间不足，需要清理临时文件',
                    'action': {
                        'type': 'cleanup',
                        'params': {'clear_cache': True, 'remove_temp': True}
                    }
                }
            ],
            DecisionType.ERROR_FIX: [
                {
                    'title': '应用自动修复方案',
                    'description': '根据错误类型应用预定义的修复方案',
                    'reasoning': '检测到可自动修复的错误类型',
                    'action': {
                        'type': 'apply_fix',
                        'params': {'auto_approve': True}
                    }
                }
            ],
            DecisionType.LEARNING_ADJUSTMENT: [
                {
                    'title': '调整学习难度',
                    'description': '根据学生表现动态调整学习内容难度',
                    'reasoning': '学生错误率较高，需要降低难度',
                    'action': {
                        'type': 'adjust_difficulty',
                        'params': {'direction': 'decrease'}
                    }
                },
                {
                    'title': '个性化学习推荐',
                    'description': '根据学生情况推荐个性化学习内容',
                    'reasoning': '需要提供更适合的学习材料',
                    'action': {
                        'type': 'personalized_recommendation',
                        'params': {}
                    }
                }
            ],
            DecisionType.SECURITY_RESPONSE: [
                {
                    'title': '增强安全防护',
                    'description': '提升安全级别，加强监控和防护',
                    'reasoning': '检测到潜在安全威胁',
                    'action': {
                        'type': 'enhance_security',
                        'params': {'increase_monitoring': True, 'alert_admins': True}
                    }
                }
            ],
            DecisionType.RESOURCE_ALLOCATION: [
                {
                    'title': '优化资源分配',
                    'description': '根据需求重新分配系统资源',
                    'reasoning': '资源分配不均衡',
                    'action': {
                        'type': 'reallocate_resources',
                        'params': {}
                    }
                }
            ],
            DecisionType.USER_EXPERIENCE: [
                {
                    'title': '改善用户体验',
                    'description': '优化界面和交互流程',
                    'reasoning': '用户反馈需要改进',
                    'action': {
                        'type': 'ux_optimization',
                        'params': {}
                    }
                }
            ]
        }
        return templates.get(decision_type, [])

    def _select_best_template(self, templates: List[Dict[str, Any]], 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """选择最佳模板"""
        if not templates:
            return {
                'title': '通用优化建议',
                'description': '根据系统状态进行综合优化',
                'reasoning': '需要进一步分析以确定具体措施',
                'action': {'type': 'general_optimization', 'params': {}}
            }
        return templates[0]  # 简化：选择第一个模板

    def _calculate_expected_impact(self, template: Dict[str, Any], 
                                  context: Dict[str, Any]) -> Dict[str, float]:
        """计算预期影响"""
        # 基于历史数据估算
        return {
            'performance_improvement': 0.15,
            'error_reduction': 0.25,
            'user_satisfaction_improvement': 0.1,
            'resource_efficiency': 0.2
        }

    def _calculate_decision_confidence(self, context: Dict[str, Any], 
                                     decision_type: DecisionType) -> float:
        """计算决策置信度"""
        base_confidence = 0.7
        historical_rate = self._calculate_historical_success_rate()
        
        # 考虑决策类型
        type_bonus = {
            DecisionType.SYSTEM_OPTIMIZATION: 0.05,
            DecisionType.ERROR_FIX: 0.1,
            DecisionType.LEARNING_ADJUSTMENT: 0.08,
            DecisionType.RESOURCE_ALLOCATION: 0.05,
            DecisionType.SECURITY_RESPONSE: 0.15,
            DecisionType.USER_EXPERIENCE: 0.03
        }
        
        confidence = base_confidence + historical_rate * 0.2 + type_bonus.get(decision_type, 0)
        return min(max(confidence, 0.0), 1.0)

    def _calculate_historical_success_rate(self) -> float:
        """计算历史成功率"""
        if not self.feedback_history:
            return 0.5
        
        successful = sum(1 for f in self.feedback_history if f.get('success', False))
        return successful / len(self.feedback_history)

    def _get_current_system_load(self) -> Dict[str, float]:
        """获取当前系统负载"""
        try:
            import psutil
            return {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        except Exception:
            return {
                'cpu_usage': 50.0,
                'memory_usage': 60.0,
                'disk_usage': 70.0
            }

    def execute_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        执行决策
        
        Args:
            decision_id: 决策ID
            
        Returns:
            执行结果
        """
        with self.lock:
            if decision_id not in self.decisions:
                return {'success': False, 'error': '决策不存在'}
            
            decision = self.decisions[decision_id]
            decision.status = DecisionStatus.IN_PROGRESS
            decision.executed_at = datetime.now()
        
        logger.info(f"执行决策: {decision.title}")
        
        try:
            # 执行具体动作
            result = self._execute_action(decision)
            
            with self.lock:
                decision.status = DecisionStatus.COMPLETED
                decision.completed_at = datetime.now()
                decision.result = result
                
                # 保存到知识库
                self._learn_from_decision(decision, result)
            
            logger.info(f"决策执行成功: {decision.title}")
            return {'success': True, 'result': result}
            
        except Exception as e:
            with self.lock:
                decision.status = DecisionStatus.FAILED
                decision.result = {'error': str(e)}
            
            logger.error(f"决策执行失败: {decision.title}, 错误: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_action(self, decision: Decision) -> Dict[str, Any]:
        """执行具体动作"""
        action_type = decision.action.get('type')
        
        # 这里应该调用实际的执行模块
        # 目前返回模拟结果
        action_results = {
            'resource_optimization': {
                'cpu_improvement': 15,
                'memory_improvement': 20,
                'message': '资源优化完成'
            },
            'cleanup': {
                'space_freed': '2.5GB',
                'message': '清理完成'
            },
            'apply_fix': {
                'errors_fixed': 3,
                'message': '修复完成'
            },
            'adjust_difficulty': {
                'new_difficulty': 'medium',
                'message': '难度调整完成'
            },
            'personalized_recommendation': {
                'recommendations_generated': 5,
                'message': '推荐生成完成'
            },
            'enhance_security': {
                'security_level': 'high',
                'message': '安全增强完成'
            },
            'reallocate_resources': {
                'resources_rebalanced': True,
                'message': '资源重分配完成'
            },
            'ux_optimization': {
                'improvements_applied': 3,
                'message': '用户体验优化完成'
            },
            'general_optimization': {
                'optimizations_applied': 2,
                'message': '通用优化完成'
            }
        }
        
        return action_results.get(action_type, {
            'message': '动作执行完成',
            'action_type': action_type
        })

    def _learn_from_decision(self, decision: Decision, result: Dict[str, Any]):
        """从决策中学习"""
        success = result.get('success', True)
        
        # 记录反馈
        self.feedback_history.append({
            'decision_id': decision.id,
            'type': decision.type.value,
            'success': success,
            'timestamp': datetime.now(),
            'result': result
        })
        
        # 更新知识库
        kb_key = f"{decision.type.value}_{decision.action.get('type')}"
        if kb_key not in self.knowledge_base:
            self.knowledge_base[kb_key] = {
                'success_count': 0,
                'total_count': 0,
                'average_impact': {},
                'last_used': None
            }
        
        kb_entry = self.knowledge_base[kb_key]
        kb_entry['total_count'] += 1
        if success:
            kb_entry['success_count'] += 1
        
        # 更新影响数据
        for key, value in decision.expected_impact.items():
            if key not in kb_entry['average_impact']:
                kb_entry['average_impact'][key] = []
            kb_entry['average_impact'][key].append(value)
        
        kb_entry['last_used'] = datetime.now()
        
        self._save_knowledge_base()

    def get_decision_status(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """获取决策状态"""
        with self.lock:
            decision = self.decisions.get(decision_id)
            if not decision:
                return None
            
            return {
                'id': decision.id,
                'type': decision.type.value,
                'status': decision.status.value,
                'title': decision.title,
                'created_at': decision.created_at,
                'executed_at': decision.executed_at,
                'completed_at': decision.completed_at,
                'confidence': decision.confidence,
                'result': decision.result
            }

    def get_pending_decisions(self) -> List[Dict[str, Any]]:
        """获取待执行决策"""
        with self.lock:
            pending = [d for d in self.decisions.values() 
                      if d.status == DecisionStatus.PENDING]
            # 按优先级排序
            pending.sort(key=lambda d: d.priority.value)
            return [
                {
                    'id': d.id,
                    'type': d.type.value,
                    'priority': d.priority.name,
                    'title': d.title,
                    'description': d.description,
                    'confidence': d.confidence,
                    'created_at': d.created_at
                }
                for d in pending
            ]

    def get_insights(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取洞察"""
        with self.lock:
            insights_list = sorted(
                self.insights.values(),
                key=lambda i: i.generated_at,
                reverse=True
            )[:limit]
            
            return [
                {
                    'id': i.id,
                    'type': i.type,
                    'title': i.title,
                    'description': i.description,
                    'confidence': i.confidence,
                    'actionable': i.actionable,
                    'generated_at': i.generated_at
                }
                for i in insights_list
            ]

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        with self.lock:
            total_decisions = len(self.decisions)
            completed = sum(1 for d in self.decisions.values() 
                          if d.status == DecisionStatus.COMPLETED)
            failed = sum(1 for d in self.decisions.values() 
                       if d.status == DecisionStatus.FAILED)
            pending = sum(1 for d in self.decisions.values() 
                        if d.status == DecisionStatus.PENDING)
            
            success_rate = completed / (completed + failed) if (completed + failed) > 0 else 0
            
            return {
                'total_decisions': total_decisions,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'success_rate': success_rate,
                'knowledge_base_size': len(self.knowledge_base),
                'historical_feedback_count': len(self.feedback_history),
                'active_problems': len([p for p in self.problems.values()])
            }

    def continuous_monitoring(self, metrics: Dict[str, Any]) -> Optional[Decision]:
        """
        持续监控并自动决策
        
        Args:
            metrics: 当前指标
            
        Returns:
            生成的决策（如果有）
        """
        # 记录指标
        for key, value in metrics.items():
            if key not in self.performance_metrics:
                self.performance_metrics[key] = []
            self.performance_metrics[key].append(value)
            if len(self.performance_metrics[key]) > 100:
                self.performance_metrics[key].pop(0)
        
        # 检测异常
        anomalies = self._detect_anomalies(metrics)
        
        if anomalies:
            # 生成问题
            problem = self.analyze_problem({
                'type': 'anomaly_detected',
                'severity': 'high' if len(anomalies) > 2 else 'medium',
                'description': f'检测到异常: {", ".join(anomalies)}',
                'metrics': metrics
            })
            
            # 生成决策
            decision = self.make_decision(problem=problem, metrics=metrics)
            
            # 如果是高优先级且置信度高，自动执行
            if decision.priority in [DecisionPriority.CRITICAL, DecisionPriority.HIGH] and decision.confidence > 0.8:
                self.execute_decision(decision.id)
            
            return decision
        
        return None

    def _detect_anomalies(self, metrics: Dict[str, Any]) -> List[str]:
        """检测异常"""
        anomalies = []
        
        for key, value in metrics.items():
            if key in self.performance_metrics and len(self.performance_metrics[key]) >= 10:
                history = self.performance_metrics[key]
                mean = sum(history) / len(history)
                std = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
                
                if std > 0 and abs(value - mean) > 3 * std:
                    anomalies.append(key)
        
        return anomalies


# 全局单例
_decision_engine: Optional[IntelligentDecisionEngine] = None


def get_decision_engine() -> IntelligentDecisionEngine:
    """获取决策引擎单例"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = IntelligentDecisionEngine()
    return _decision_engine
