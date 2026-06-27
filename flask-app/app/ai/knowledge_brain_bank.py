# -*- coding: utf-8 -*-
"""
AI脑库系统 - Knowledge Brain Bank
- 知识自动积累与分类
- 智能触发条件学习
- 知识共享与赋能
- 脑库增强AI决策
- 最大化脑库价值
"""

import os
import re
import json
import time
import uuid
import hashlib
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举定义
# ============================================================================

class KnowledgeType(Enum):
    """知识类型"""
    EXPERIENCE = "experience"         # 经验知识
    PATTERN = "pattern"               # 模式知识
    RULE = "rule"                     # 规则知识
    SOLUTION = "solution"             # 解决方案
    INSIGHT = "insight"               # 洞见知识
    BEST_PRACTICE = "best_practice"   # 最佳实践
    LESSON_LEARNED = "lesson"         # 教训知识
    HEURISTIC = "heuristic"           # 启发式知识
    PREDICTIVE = "predictive"         # 预测性知识
    CAUSAL = "causal"                 # 因果知识


class KnowledgeDomain(Enum):
    """知识领域"""
    ERROR_FIX = "error_fix"           # 错误修复
    PERFORMANCE = "performance"       # 性能优化
    SECURITY = "security"             # 安全
    DATABASE = "database"             # 数据库
    FRONTEND = "frontend"             # 前端
    BACKEND = "backend"               # 后端
    DEVOPS = "devops"                 # 运维
    AI_ML = "ai_ml"                   # AI/ML
    UX = "ux"                         # 用户体验
    BUSINESS = "business"             # 业务
    GENERAL = "general"               # 通用


class TriggerConditionType(Enum):
    """触发条件类型"""
    ERROR_OCCURRED = "error_occurred"         # 错误发生
    PERFORMANCE_DEGRADED = "perf_degraded"    # 性能下降
    USER_ACTION = "user_action"               # 用户行为
    TIME_BASED = "time_based"                 # 时间触发
    THRESHOLD = "threshold"                   # 阈值触发
    PATTERN_MATCH = "pattern_match"           # 模式匹配
    STATE_CHANGE = "state_change"             # 状态变化
    EVENT_CHAIN = "event_chain"               # 事件链
    ANOMALY_DETECTED = "anomaly_detected"     # 异常检测
    PREDICTED_RISK = "predicted_risk"         # 预测风险


class KnowledgeValue(Enum):
    """知识价值等级"""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 50
    LOW = 20
    TRIVIAL = 5


class BrainBankStatus(Enum):
    """脑库状态"""
    ACTIVE = "active"
    LEARNING = "learning"
    OPTIMIZING = "optimizing"
    CONSOLIDATING = "consolidating"
    MAINTENANCE = "maintenance"


# ============================================================================
# 知识条目
# ============================================================================

class KnowledgeEntry:
    """知识条目"""

    def __init__(self, title: str, content: str, 
                 knowledge_type: KnowledgeType,
                 domain: KnowledgeDomain,
                 source: str = "auto_discovered",
                 value: KnowledgeValue = KnowledgeValue.MEDIUM,
                 tags: List[str] = None):
        self.knowledge_id = f"kb_{uuid.uuid4().hex[:12]}"
        self.title = title
        self.content = content
        self.knowledge_type = knowledge_type
        self.domain = domain
        self.source = source
        self.value = value
        self.tags = tags or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.access_count = 0
        self.useful_count = 0
        self.last_accessed = None
        self.version = 1
        self.related_knowledge: List[str] = []
        self.trigger_count = 0
        self.success_rate = 0.0
        self.embedding_hash = None
        self.metadata: Dict[str, Any] = {}
        self.author = "ai_system"
        self.is_validated = False
        self.validation_count = 0

    def to_dict(self) -> Dict:
        return {
            'knowledge_id': self.knowledge_id,
            'title': self.title,
            'content_preview': self.content[:200],
            'knowledge_type': self.knowledge_type.value,
            'domain': self.domain.value,
            'source': self.source,
            'value_level': self.value.value,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'access_count': self.access_count,
            'useful_count': self.useful_count,
            'version': self.version,
            'trigger_count': self.trigger_count,
            'success_rate': self.success_rate,
            'related_count': len(self.related_knowledge),
            'is_validated': self.is_validated
        }


# ============================================================================
# 智能触发条件
# ============================================================================

class TriggerCondition:
    """智能触发条件"""

    def __init__(self, name: str, condition_type: TriggerConditionType,
                 rule: Dict[str, Any], action: str,
                 related_knowledge: List[str] = None):
        self.trigger_id = f"trig_{uuid.uuid4().hex[:12]}"
        self.name = name
        self.condition_type = condition_type
        self.rule = rule
        self.action = action
        self.related_knowledge = related_knowledge or []
        self.created_at = datetime.now()
        self.last_triggered = None
        self.trigger_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.confidence = 0.5
        self.auto_generated = False
        self.is_active = True
        self.priority = 50
        self.cooldown = 60
        self.metadata: Dict[str, Any] = {}

    def should_trigger(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """判断是否应该触发，返回(是否触发, 置信度)"""
        if not self.is_active:
            return False, 0.0
        
        if self.last_triggered:
            elapsed = (datetime.now() - self.last_triggered).total_seconds()
            if elapsed < self.cooldown:
                return False, 0.0
        
        try:
            matched, confidence = self._evaluate_rule(context)
            return matched, confidence * self.confidence
        except Exception as e:
            logger.error(f"触发条件评估失败: {self.name}, {e}")
            return False, 0.0

    def _evaluate_rule(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """评估规则"""
        rule_type = self.rule.get('type', 'threshold')
        
        if rule_type == 'threshold':
            return self._evaluate_threshold(context)
        elif rule_type == 'pattern':
            return self._evaluate_pattern(context)
        elif rule_type == 'state_change':
            return self._evaluate_state_change(context)
        elif rule_type == 'event_chain':
            return self._evaluate_event_chain(context)
        elif rule_type == 'anomaly':
            return self._evaluate_anomaly(context)
        else:
            return False, 0.0

    def _evaluate_threshold(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """阈值评估"""
        metric = self.rule.get('metric')
        threshold = self.rule.get('threshold')
        operator = self.rule.get('operator', '>')
        
        if not metric or threshold is None:
            return False, 0.0
        
        value = context.get(metric)
        if value is None:
            return False, 0.0
        
        try:
            value = float(value)
            threshold = float(threshold)
            
            if operator == '>':
                matched = value > threshold
                confidence = min(1.0, (value - threshold) / threshold + 0.5) if matched else 0.0
            elif operator == '<':
                matched = value < threshold
                confidence = min(1.0, (threshold - value) / threshold + 0.5) if matched else 0.0
            elif operator == '>=':
                matched = value >= threshold
                confidence = min(1.0, (value - threshold) / threshold + 0.5) if matched else 0.0
            elif operator == '<=':
                matched = value <= threshold
                confidence = min(1.0, (threshold - value) / threshold + 0.5) if matched else 0.0
            elif operator == '==':
                matched = value == threshold
                confidence = 1.0 if matched else 0.0
            else:
                matched = False
                confidence = 0.0
            
            return matched, max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            return False, 0.0

    def _evaluate_pattern(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """模式匹配评估"""
        pattern = self.rule.get('pattern')
        target = self.rule.get('target', 'message')
        
        if not pattern:
            return False, 0.0
        
        text = str(context.get(target, ''))
        if not text:
            return False, 0.0
        
        try:
            if isinstance(pattern, str):
                pattern = re.compile(pattern, re.IGNORECASE)
            
            matches = pattern.findall(text)
            if matches:
                confidence = min(1.0, len(matches) * 0.3)
                return True, confidence
            return False, 0.0
        except re.error:
            return False, 0.0

    def _evaluate_state_change(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """状态变化评估"""
        metric = self.rule.get('metric')
        from_state = self.rule.get('from')
        to_state = self.rule.get('to')
        
        if not metric:
            return False, 0.0
        
        current = context.get(f'current_{metric}')
        previous = context.get(f'previous_{metric}')
        
        if current is None or previous is None:
            return False, 0.0
        
        matched = True
        if from_state and previous != from_state:
            matched = False
        if to_state and current != to_state:
            matched = False
        
        return matched, 0.8 if matched else 0.0

    def _evaluate_event_chain(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """事件链评估"""
        events = self.rule.get('events', [])
        recent_events = context.get('recent_events', [])
        
        if not events:
            return False, 0.0
        
        event_count = len([e for e in events if e in recent_events])
        if event_count == 0:
            return False, 0.0
        
        ratio = event_count / len(events)
        if ratio >= 0.7:
            return True, ratio
        
        return False, ratio

    def _evaluate_anomaly(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """异常检测评估"""
        metric = self.rule.get('metric')
        baseline = self.rule.get('baseline')
        deviation = self.rule.get('max_deviation', 0.5)
        
        if not metric or baseline is None:
            return False, 0.0
        
        value = context.get(metric)
        if value is None:
            return False, 0.0
        
        try:
            value = float(value)
            baseline = float(baseline)
            
            if baseline == 0:
                return False, 0.0
            
            diff_ratio = abs(value - baseline) / baseline
            
            if diff_ratio > deviation:
                confidence = min(1.0, diff_ratio)
                return True, confidence
            return False, diff_ratio
        except (ValueError, TypeError):
            return False, 0.0

    def record_result(self, success: bool):
        """记录触发结果"""
        self.trigger_count += 1
        self.last_triggered = datetime.now()
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        if self.trigger_count >= 5:
            self.confidence = self.success_count / self.trigger_count
        
        if self.auto_generated and self.trigger_count >= 10:
            if self.confidence < 0.3:
                self.is_active = False
                logger.info(f"低质量触发条件已禁用: {self.name}")

    def to_dict(self) -> Dict:
        return {
            'trigger_id': self.trigger_id,
            'name': self.name,
            'condition_type': self.condition_type.value,
            'action': self.action,
            'trigger_count': self.trigger_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'confidence': self.confidence,
            'auto_generated': self.auto_generated,
            'is_active': self.is_active,
            'priority': self.priority,
            'cooldown': self.cooldown,
            'related_knowledge_count': len(self.related_knowledge)
        }


# ============================================================================
# 知识存储引擎
# ============================================================================

class KnowledgeStorageEngine:
    """知识存储引擎"""

    def __init__(self):
        self._knowledge: Dict[str, KnowledgeEntry] = {}
        self._indexes: Dict[str, Dict[str, List[str]]] = {
            'type': defaultdict(list),
            'domain': defaultdict(list),
            'tag': defaultdict(list),
            'value': defaultdict(list)
        }
        self._full_text_index: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.Lock()
        self._knowledge_count = 0

    def add_knowledge(self, entry: KnowledgeEntry) -> str:
        """添加知识"""
        with self._lock:
            self._knowledge[entry.knowledge_id] = entry
            self._knowledge_count += 1
            
            # 更新索引
            self._indexes['type'][entry.knowledge_type.value].append(entry.knowledge_id)
            self._indexes['domain'][entry.domain.value].append(entry.knowledge_id)
            self._indexes['value'][str(entry.value.value)].append(entry.knowledge_id)
            
            for tag in entry.tags:
                self._indexes['tag'][tag.lower()].append(entry.knowledge_id)
            
            # 全文索引（简单分词）
            words = self._tokenize(entry.title + ' ' + entry.content)
            for word in words:
                if len(word) >= 2:
                    self._full_text_index[word.lower()].append(entry.knowledge_id)
            
            logger.debug(f"知识已添加: {entry.title}")
            return entry.knowledge_id

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        return list(set(words))

    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeEntry]:
        """获取知识"""
        entry = self._knowledge.get(knowledge_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now()
        return entry

    def search_knowledge(self, query: str, 
                        knowledge_type: Optional[str] = None,
                        domain: Optional[str] = None,
                        min_value: int = 0,
                        limit: int = 20) -> List[KnowledgeEntry]:
        """搜索知识"""
        results = set()
        
        query_words = self._tokenize(query)
        
        with self._lock:
            if query_words:
                for word in query_words:
                    word_lower = word.lower()
                    if word_lower in self._full_text_index:
                        results.update(self._full_text_index[word_lower])
            else:
                results = set(self._knowledge.keys())
            
            # 类型过滤
            if knowledge_type:
                type_ids = set(self._indexes['type'].get(knowledge_type, []))
                results &= type_ids
            
            # 领域过滤
            if domain:
                domain_ids = set(self._indexes['domain'].get(domain, []))
                results &= domain_ids
            
            # 价值过滤
            if min_value > 0:
                value_ids = set()
                for val_str, ids in self._indexes['value'].items():
                    if int(val_str) >= min_value:
                        value_ids.update(ids)
                results &= value_ids
            
            # 获取知识条目并排序
            entries = [self._knowledge[kid] for kid in results if kid in self._knowledge]
            entries.sort(key=lambda e: (e.value.value, e.useful_count, e.access_count), reverse=True)
            
            return entries[:limit]

    def get_by_domain(self, domain: str, limit: int = 50) -> List[KnowledgeEntry]:
        """按领域获取知识"""
        with self._lock:
            ids = self._indexes['domain'].get(domain, [])
            entries = [self._knowledge[kid] for kid in ids if kid in self._knowledge]
            entries.sort(key=lambda e: (e.value.value, e.useful_count), reverse=True)
            return entries[:limit]

    def get_by_type(self, knowledge_type: str, limit: int = 50) -> List[KnowledgeEntry]:
        """按类型获取知识"""
        with self._lock:
            ids = self._indexes['type'].get(knowledge_type, [])
            entries = [self._knowledge[kid] for kid in ids if kid in self._knowledge]
            entries.sort(key=lambda e: (e.value.value, e.useful_count), reverse=True)
            return entries[:limit]

    def get_top_knowledge(self, limit: int = 10) -> List[KnowledgeEntry]:
        """获取最有价值的知识"""
        with self._lock:
            entries = list(self._knowledge.values())
            entries.sort(key=lambda e: (e.value.value, e.success_rate, e.useful_count), reverse=True)
            return entries[:limit]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            return {
                'total_knowledge': self._knowledge_count,
                'by_type': {k: len(v) for k, v in self._indexes['type'].items()},
                'by_domain': {k: len(v) for k, v in self._indexes['domain'].items()},
                'indexed_words': len(self._full_text_index)
            }

    def consolidate_knowledge(self) -> int:
        """知识整合 - 合并相似知识，提升质量"""
        consolidated = 0
        # 简化版：标记低质量知识
        with self._lock:
            for entry in self._knowledge.values():
                if entry.access_count == 0 and entry.value == KnowledgeValue.TRIVIAL:
                    entry.is_validated = False
                    consolidated += 1
        logger.info(f"知识整合完成，处理 {consolidated} 条知识")
        return consolidated


# ============================================================================
# 智能触发学习器
# ============================================================================

class TriggerLearner:
    """智能触发条件学习器"""

    def __init__(self, knowledge_engine: KnowledgeStorageEngine):
        self._triggers: Dict[str, TriggerCondition] = {}
        self._trigger_history: deque = deque(maxlen=1000)
        self._learning_rate = 0.1
        self._lock = threading.Lock()
        self._knowledge_engine = knowledge_engine
        self._auto_generation_enabled = True
        self._min_confidence_for_auto = 0.6
        self._pattern_memory: Dict[str, List[Dict]] = defaultdict(list)

    def add_trigger(self, trigger: TriggerCondition) -> str:
        """添加触发条件"""
        with self._lock:
            self._triggers[trigger.trigger_id] = trigger
            logger.info(f"触发条件已添加: {trigger.name}")
            return trigger.trigger_id

    def evaluate_all_triggers(self, context: Dict[str, Any]) -> List[Tuple[TriggerCondition, float]]:
        """评估所有触发条件，返回按置信度排序的列表"""
        results = []
        
        with self._lock:
            triggers = list(self._triggers.values())
        
        for trigger in triggers:
            should, confidence = trigger.should_trigger(context)
            if should and confidence > 0.3:
                results.append((trigger, confidence))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def learn_from_event(self, event: Dict[str, Any], outcome: bool):
        """从事件中学习"""
        event_type = event.get('type', 'unknown')
        event_data = event.get('data', {})
        
        with self._lock:
            self._pattern_memory[event_type].append({
                'timestamp': datetime.now(),
                'data': event_data,
                'outcome': outcome
            })
            
            if len(self._pattern_memory[event_type]) >= 5 and self._auto_generation_enabled:
                self._try_generate_trigger(event_type)

    def _try_generate_trigger(self, event_type: str):
        """尝试自动生成触发条件"""
        patterns = self._pattern_memory[event_type][-20:]
        
        successful = [p for p in patterns if p['outcome']]
        success_rate = len(successful) / len(patterns) if patterns else 0
        
        if success_rate >= self._min_confidence_for_auto:
            trigger_name = f"auto_{event_type}_{int(time.time())}"
            
            rule = self._extract_rule(patterns, event_type)
            
            if rule:
                trigger = TriggerCondition(
                    name=trigger_name,
                    condition_type=TriggerConditionType.PATTERN_MATCH,
                    rule=rule,
                    action=f"auto_handle_{event_type}",
                )
                trigger.auto_generated = True
                trigger.confidence = success_rate
                
                self._triggers[trigger.trigger_id] = trigger
                logger.info(f"自动生成触发条件: {trigger_name} (置信度: {success_rate:.2f})")

    def _extract_rule(self, patterns: List[Dict], event_type: str) -> Optional[Dict]:
        """从模式中提取规则"""
        if not patterns:
            return None
        
        common_keys = set()
        first = True
        
        for pattern in patterns:
            data = pattern.get('data', {})
            keys = set(data.keys())
            if first:
                common_keys = keys
                first = False
            else:
                common_keys &= keys
        
        if not common_keys:
            return {
                'type': 'pattern',
                'pattern': event_type,
                'target': 'type'
            }
        
        rule = {
            'type': 'pattern',
            'pattern': '|'.join(list(common_keys)[:5]),
            'target': 'message'
        }
        
        return rule

    def get_trigger_stats(self) -> Dict:
        """获取触发条件统计"""
        with self._lock:
            auto_count = sum(1 for t in self._triggers.values() if t.auto_generated)
            active_count = sum(1 for t in self._triggers.values() if t.is_active)
            total_triggers = len(self._triggers)
            
            avg_confidence = 0.0
            if total_triggers > 0:
                avg_confidence = sum(t.confidence for t in self._triggers.values()) / total_triggers
            
            return {
                'total_triggers': total_triggers,
                'active_triggers': active_count,
                'auto_generated': auto_count,
                'manual': total_triggers - auto_count,
                'average_confidence': avg_confidence,
                'total_trigger_count': sum(t.trigger_count for t in self._triggers.values()),
                'by_type': defaultdict(int)
            }

    def get_all_triggers(self, active_only: bool = False, limit: int = 50) -> List[TriggerCondition]:
        """获取所有触发条件"""
        with self._lock:
            triggers = list(self._triggers.values())
            if active_only:
                triggers = [t for t in triggers if t.is_active]
            triggers.sort(key=lambda t: (t.priority, t.confidence), reverse=True)
            return triggers[:limit]


# ============================================================================
# 知识共享与赋能引擎
# ============================================================================

class KnowledgeEmpowermentEngine:
    """知识共享与赋能引擎"""

    def __init__(self, knowledge_engine: KnowledgeStorageEngine):
        self._knowledge_engine = knowledge_engine
        self._empowerment_cache: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
        self._ai_skill_boost: Dict[str, float] = defaultdict(lambda: 1.0)
        self._cross_domain_insights: List[Dict] = []

    def get_relevant_knowledge(self, task_context: Dict[str, Any], 
                              limit: int = 5) -> List[KnowledgeEntry]:
        """获取相关知识用于赋能"""
        query_parts = []
        
        if 'task_type' in task_context:
            query_parts.append(task_context['task_type'])
        if 'domain' in task_context:
            query_parts.append(task_context['domain'])
        if 'error_type' in task_context:
            query_parts.append(task_context['error_type'])
        if 'description' in task_context:
            query_parts.append(task_context['description'][:100])
        
        query = ' '.join(query_parts) if query_parts else 'general'
        domain = task_context.get('domain')
        
        results = self._knowledge_engine.search_knowledge(
            query=query,
            domain=domain,
            min_value=KnowledgeValue.LOW.value,
            limit=limit
        )
        
        return results

    def empower_decision(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """用脑库知识增强决策"""
        relevant_knowledge = self.get_relevant_knowledge(decision_context, limit=10)
        
        empowered_decision = {
            'original_context': decision_context,
            'knowledge_used': [k.knowledge_id for k in relevant_knowledge],
            'knowledge_count': len(relevant_knowledge),
            'confidence_boost': 0.0,
            'suggestions': [],
            'warnings': [],
            'best_practices': []
        }
        
        for knowledge in relevant_knowledge:
            knowledge.access_count += 1
            knowledge.last_accessed = datetime.now()
            
            if knowledge.knowledge_type == KnowledgeType.BEST_PRACTICE:
                empowered_decision['best_practices'].append({
                    'id': knowledge.knowledge_id,
                    'title': knowledge.title
                })
            
            if knowledge.knowledge_type == KnowledgeType.LESSON_LEARNED:
                empowered_decision['warnings'].append({
                    'id': knowledge.knowledge_id,
                    'title': knowledge.title
                })
            
            if knowledge.knowledge_type == KnowledgeType.SOLUTION:
                empowered_decision['suggestions'].append({
                    'id': knowledge.knowledge_id,
                    'title': knowledge.title
                })
            
            empowered_decision['confidence_boost'] += knowledge.value.value / 1000
        
        empowered_decision['confidence_boost'] = min(0.5, empowered_decision['confidence_boost'])
        
        return empowered_decision

    def cross_pollinate(self, source_domain: str, target_domain: str) -> List[Dict]:
        """跨领域知识迁移"""
        source_knowledge = self._knowledge_engine.get_by_domain(source_domain, limit=20)
        target_knowledge = self._knowledge_engine.get_by_domain(target_domain, limit=20)
        
        insights = []
        
        for src in source_knowledge:
            if src.value.value >= KnowledgeValue.MEDIUM.value:
                insight = {
                    'source_knowledge_id': src.knowledge_id,
                    'source_domain': source_domain,
                    'target_domain': target_domain,
                    'applicability': self._calculate_applicability(src, target_domain),
                    'insight': f"将 {src.domain.value} 领域的 {src.title} 应用到 {target_domain}"
                }
                if insight['applicability'] > 0.3:
                    insights.append(insight)
                    self._cross_domain_insights.append(insight)
        
        insights.sort(key=lambda x: x['applicability'], reverse=True)
        return insights[:10]

    def _calculate_applicability(self, knowledge: KnowledgeEntry, target_domain: str) -> float:
        """计算知识在目标领域的适用性"""
        applicability = 0.3
        
        if knowledge.knowledge_type in [KnowledgeType.PATTERN, KnowledgeType.HEURISTIC]:
            applicability += 0.2
        
        if 'general' in knowledge.tags or '通用' in knowledge.tags:
            applicability += 0.2
        
        if len(knowledge.tags) >= 3:
            applicability += 0.1
        
        return min(1.0, applicability)

    def get_empowerment_stats(self) -> Dict:
        """获取赋能统计"""
        with self._lock:
            return {
                'cached_empowerments': len(self._empowerment_cache),
                'cross_domain_insights': len(self._cross_domain_insights),
                'skill_boost_categories': len(self._ai_skill_boost)
            }


# ============================================================================
# AI脑库中心
# ============================================================================

class KnowledgeBrainBank:
    """AI脑库中心"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化脑库"""
        self.storage = KnowledgeStorageEngine()
        self.trigger_learner = TriggerLearner(self.storage)
        self.empowerment = KnowledgeEmpowermentEngine(self.storage)
        self._status = BrainBankStatus.ACTIVE
        self._start_time = datetime.now()
        self._total_queries = 0
        self._successful_empowerments = 0
        self._lock = threading.Lock()
        
        self._bootstrap_knowledge()
        self._bootstrap_triggers()
        
        logger.info("AI脑库系统初始化完成")

    def _bootstrap_knowledge(self):
        """初始化基础知识"""
        bootstrap_knowledge = [
            {
                'title': '错误日志分析方法论',
                'content': '分析错误日志时，首先统计错误类型分布，找出高频错误，然后分析根因模式，最后制定预防措施。',
                'type': KnowledgeType.BEST_PRACTICE,
                'domain': KnowledgeDomain.ERROR_FIX,
                'value': KnowledgeValue.HIGH,
                'tags': ['方法论', '错误分析', '最佳实践']
            },
            {
                'title': '性能优化通用框架',
                'content': '性能优化五步法：1.测量基线 2.定位瓶颈 3.分析原因 4.实施优化 5.验证效果。循环迭代。',
                'type': KnowledgeType.BEST_PRACTICE,
                'domain': KnowledgeDomain.PERFORMANCE,
                'value': KnowledgeValue.HIGH,
                'tags': ['性能优化', '方法论', '通用']
            },
            {
                'title': '数据库索引设计原则',
                'content': '索引设计三原则：1.高频查询列优先 2.联合索引注意顺序 3.避免过度索引。',
                'type': KnowledgeType.RULE,
                'domain': KnowledgeDomain.DATABASE,
                'value': KnowledgeValue.MEDIUM,
                'tags': ['数据库', '索引', '优化']
            },
            {
                'title': '安全漏洞预防清单',
                'content': '安全检查清单：输入验证、身份认证、权限控制、数据加密、日志审计、错误处理。',
                'type': KnowledgeType.CHECKLIST if hasattr(KnowledgeType, 'CHECKLIST') else KnowledgeType.RULE,
                'domain': KnowledgeDomain.SECURITY,
                'value': KnowledgeValue.HIGH,
                'tags': ['安全', '检查清单', '预防']
            },
            {
                'title': '从失败中学习的价值',
                'content': '每一次失败都是学习机会。记录失败原因、分析根因、制定预防措施，是AI能力提升的关键。',
                'type': KnowledgeType.INSIGHT,
                'domain': KnowledgeDomain.AI_ML,
                'value': KnowledgeValue.MEDIUM,
                'tags': ['学习', '失败', 'AI成长']
            },
            {
                'title': '用户体验设计黄金法则',
                'content': 'UX设计三原则：1.一致性 2.简洁性 3.反馈及时。始终以用户为中心。',
                'type': KnowledgeType.BEST_PRACTICE,
                'domain': KnowledgeDomain.UX,
                'value': KnowledgeValue.MEDIUM,
                'tags': ['UX', '设计', '用户体验']
            },
            {
                'title': '系统监控关键指标',
                'content': '四大黄金指标：延迟、流量、错误率、饱和度。关注这些指标可以快速发现系统问题。',
                'type': KnowledgeType.HEURISTIC,
                'domain': KnowledgeDomain.DEVOPS,
                'value': KnowledgeValue.HIGH,
                'tags': ['监控', '运维', '指标']
            },
            {
                'title': '代码审查要点',
                'content': '代码审查关注：可读性、正确性、性能、安全、可维护性。质量优先于数量。',
                'type': KnowledgeType.BEST_PRACTICE,
                'domain': KnowledgeDomain.BACKEND,
                'value': KnowledgeValue.MEDIUM,
                'tags': ['代码审查', '质量', '最佳实践']
            },
        ]
        
        for item in bootstrap_knowledge:
            entry = KnowledgeEntry(
                title=item['title'],
                content=item['content'],
                knowledge_type=item['type'],
                domain=item['domain'],
                source='bootstrap',
                value=item['value'],
                tags=item['tags']
            )
            entry.is_validated = True
            self.storage.add_knowledge(entry)
        
        logger.info(f"脑库初始化知识: {len(bootstrap_knowledge)} 条")

    def _bootstrap_triggers(self):
        """初始化触发条件"""
        bootstrap_triggers = [
            {
                'name': 'CPU使用率过高告警',
                'type': TriggerConditionType.THRESHOLD,
                'rule': {'type': 'threshold', 'metric': 'cpu_percent', 'threshold': 90, 'operator': '>'},
                'action': 'trigger_performance_optimization',
                'priority': 80,
                'cooldown': 300
            },
            {
                'name': '内存使用率过高告警',
                'type': TriggerConditionType.THRESHOLD,
                'rule': {'type': 'threshold', 'metric': 'memory_percent', 'threshold': 90, 'operator': '>'},
                'action': 'trigger_memory_optimization',
                'priority': 80,
                'cooldown': 300
            },
            {
                'name': '磁盘空间不足预警',
                'type': TriggerConditionType.THRESHOLD,
                'rule': {'type': 'threshold', 'metric': 'disk_percent', 'threshold': 85, 'operator': '>'},
                'action': 'trigger_storage_management',
                'priority': 70,
                'cooldown': 600
            },
            {
                'name': '错误率异常检测',
                'type': TriggerConditionType.ANOMALY_DETECTED,
                'rule': {'type': 'anomaly', 'metric': 'error_rate', 'baseline': 0.01, 'max_deviation': 2.0},
                'action': 'trigger_error_analysis',
                'priority': 90,
                'cooldown': 120
            },
            {
                'name': '高频错误模式',
                'type': TriggerConditionType.PATTERN_MATCH,
                'rule': {'type': 'pattern', 'pattern': r'(error|exception|failed)', 'target': 'message'},
                'action': 'analyze_error_pattern',
                'priority': 60,
                'cooldown': 60
            },
        ]
        
        for item in bootstrap_triggers:
            trigger = TriggerCondition(
                name=item['name'],
                condition_type=item['type'],
                rule=item['rule'],
                action=item['action'],
            )
            trigger.priority = item['priority']
            trigger.cooldown = item['cooldown']
            trigger.is_active = True
            self.trigger_learner.add_trigger(trigger)
        
        logger.info(f"脑库初始化触发条件: {len(bootstrap_triggers)} 条")

    def add_knowledge_from_experience(self, experience: Dict[str, Any]) -> str:
        """从经验中提取并添加知识"""
        title = experience.get('title', '')
        content = experience.get('content', '')
        exp_type = experience.get('type', 'experience')
        domain = experience.get('domain', 'general')
        outcome = experience.get('outcome', 'neutral')
        
        type_map = {
            'success': KnowledgeType.EXPERIENCE,
            'failure': KnowledgeType.LESSON_LEARNED,
            'solution': KnowledgeType.SOLUTION,
            'insight': KnowledgeType.INSIGHT,
            'pattern': KnowledgeType.PATTERN
        }
        
        domain_map = {
            'error_fix': KnowledgeDomain.ERROR_FIX,
            'performance': KnowledgeDomain.PERFORMANCE,
            'database': KnowledgeDomain.DATABASE,
            'security': KnowledgeDomain.SECURITY,
            'frontend': KnowledgeDomain.FRONTEND,
            'backend': KnowledgeDomain.BACKEND,
            'devops': KnowledgeDomain.DEVOPS,
            'ai_ml': KnowledgeDomain.AI_ML,
            'ux': KnowledgeDomain.UX,
        }
        
        knowledge_type = type_map.get(exp_type, KnowledgeType.EXPERIENCE)
        knowledge_domain = domain_map.get(domain, KnowledgeDomain.GENERAL)
        
        if outcome == 'success':
            value = KnowledgeValue.HIGH
        elif outcome == 'failure':
            value = KnowledgeValue.MEDIUM
        else:
            value = KnowledgeValue.LOW
        
        tags = experience.get('tags', [])
        if outcome == 'success':
            tags.append('成功经验')
        elif outcome == 'failure':
            tags.append('教训')
        
        entry = KnowledgeEntry(
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            domain=knowledge_domain,
            source='auto_learned',
            value=value,
            tags=tags
        )
        
        knowledge_id = self.storage.add_knowledge(entry)
        
        if outcome == 'success':
            entry.useful_count += 1
        
        return knowledge_id

    def evaluate_and_trigger(self, context: Dict[str, Any]) -> List[Dict]:
        """评估并触发动作"""
        triggers = self.trigger_learner.evaluate_all_triggers(context)
        
        results = []
        for trigger, confidence in triggers:
            result = {
                'trigger_id': trigger.trigger_id,
                'trigger_name': trigger.name,
                'confidence': confidence,
                'action': trigger.action,
                'knowledge_available': []
            }
            
            if trigger.related_knowledge:
                for kid in trigger.related_knowledge:
                    k = self.storage.get_knowledge(kid)
                    if k:
                        result['knowledge_available'].append(k.title)
            
            results.append(result)
        
        self._total_queries += 1
        if results:
            self._successful_empowerments += 1
        
        return results

    def get_brain_stats(self) -> Dict:
        """获取脑库统计"""
        with self._lock:
            storage_stats = self.storage.get_stats()
            trigger_stats = self.trigger_learner.get_trigger_stats()
            empowerment_stats = self.empowerment.get_empowerment_stats()
            
            uptime = (datetime.now() - self._start_time).total_seconds()
            
            return {
                'status': self._status.value,
                'uptime_seconds': uptime,
                'total_queries': self._total_queries,
                'successful_empowerments': self._successful_empowerments,
                'empowerment_rate': self._successful_empowerments / max(1, self._total_queries),
                'knowledge': storage_stats,
                'triggers': trigger_stats,
                'empowerment': empowerment_stats,
                'top_knowledge': [k.to_dict() for k in self.storage.get_top_knowledge(5)]
            }

    def set_status(self, status: BrainBankStatus):
        """设置脑库状态"""
        self._status = status
        logger.info(f"脑库状态变更为: {status.value}")


# 全局单例
knowledge_brain_bank = KnowledgeBrainBank()
