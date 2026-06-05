"""
AI智能服务模块
集成了智能决策引擎、知识图谱、预测分析和编排系统
"""

from .intelligent_decision_engine import (
    IntelligentDecisionEngine,
    get_decision_engine,
    DecisionType,
    DecisionStatus,
    DecisionPriority
)

from .enhanced_knowledge_graph import (
    EnhancedKnowledgeGraph,
    get_knowledge_graph,
    initialize_learning_knowledge,
    KnowledgeType,
    EntityType,
    RelationType
)

from .intelligent_predictor import (
    IntelligentPredictor,
    get_predictor,
    PredictionType,
    RiskLevel,
    PredictionResult
)

from .ai_orchestrator import (
    AIOrchestrator,
    get_orchestrator,
    TaskStatus,
    AlertLevel,
    AITask,
    Alert
)

__all__ = [
    # 智能决策引擎
    'IntelligentDecisionEngine',
    'get_decision_engine',
    'DecisionType',
    'DecisionStatus',
    'DecisionPriority',
    
    # 知识图谱
    'EnhancedKnowledgeGraph',
    'get_knowledge_graph',
    'initialize_learning_knowledge',
    'KnowledgeType',
    'EntityType',
    'RelationType',
    
    # 预测分析
    'IntelligentPredictor',
    'get_predictor',
    'PredictionType',
    'RiskLevel',
    'PredictionResult',
    
    # 编排系统
    'AIOrchestrator',
    'get_orchestrator',
    'TaskStatus',
    'AlertLevel',
    'AITask',
    'Alert',
    
    # 快捷初始化
    'initialize_all_ai_services'
]


def initialize_all_ai_services(start_orchestrator: bool = True):
    """
    初始化所有AI智能服务
    
    Args:
        start_orchestrator: 是否启动编排器
    """
    # 初始化知识图谱
    kg = get_knowledge_graph()
    initialize_learning_knowledge()
    
    # 初始化决策引擎
    de = get_decision_engine()
    
    # 初始化预测器
    pr = get_predictor()
    
    # 初始化编排器
    orc = get_orchestrator()
    
    if start_orchestrator:
        orc.start()
    
    return {
        'knowledge_graph': kg,
        'decision_engine': de,
        'predictor': pr,
        'orchestrator': orc
    }
