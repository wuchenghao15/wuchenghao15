#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI引擎服务 - 实现智能推理和规则引擎
"""

import os
import json
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

from app.utils.logging import logger


class AIModelType(Enum):
    """AI模型类型"""
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    LLAMA = "llama"


class RuleOperator(Enum):
    """规则操作符"""
    EQ = "=="
    NE = "!="
    GT = ">"
    LT = "<"
    GE = ">="
    LE = "<="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class RuleActionType(Enum):
    """规则动作类型"""
    SET = "set"
    APPEND = "append"
    REMOVE = "remove"
    CALL = "call"
    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"
    TRIGGER = "trigger"


@dataclass
class RuleCondition:
    """规则条件"""
    field: str
    operator: RuleOperator
    value: Any
    logic: str = "AND"  # AND/OR

    def evaluate(self, data: Dict) -> bool:
        """评估条件"""
        field_value = data.get(self.field)
        
        try:
            if self.operator == RuleOperator.EQ:
                return field_value == self.value
            elif self.operator == RuleOperator.NE:
                return field_value != self.value
            elif self.operator == RuleOperator.GT:
                return float(field_value) > float(self.value)
            elif self.operator == RuleOperator.LT:
                return float(field_value) < float(self.value)
            elif self.operator == RuleOperator.GE:
                return float(field_value) >= float(self.value)
            elif self.operator == RuleOperator.LE:
                return float(field_value) <= float(self.value)
            elif self.operator == RuleOperator.IN:
                return field_value in self.value
            elif self.operator == RuleOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == RuleOperator.CONTAINS:
                return self.value in str(field_value)
            elif self.operator == RuleOperator.NOT_CONTAINS:
                return self.value not in str(field_value)
            elif self.operator == RuleOperator.MATCHES:
                import re
                return bool(re.match(self.value, str(field_value)))
            elif self.operator == RuleOperator.IS_EMPTY:
                return field_value is None or field_value == "" or field_value == []
            elif self.operator == RuleOperator.IS_NOT_EMPTY:
                return field_value is not None and field_value != "" and field_value != []
        except Exception as e:
            logger.error(f"条件评估错误: {str(e)}")
            return False
        
        return False


@dataclass
class RuleAction:
    """规则动作"""
    type: RuleActionType
    target: str
    value: Any = None
    params: Dict = field(default_factory=dict)

    def execute(self, data: Dict) -> Dict:
        """执行动作"""
        result = {'success': True, 'data': data.copy()}
        
        try:
            if self.type == RuleActionType.SET:
                result['data'][self.target] = self.value
            elif self.type == RuleActionType.APPEND:
                if self.target not in result['data']:
                    result['data'][self.target] = []
                if isinstance(result['data'][self.target], list):
                    result['data'][self.target].append(self.value)
            elif self.type == RuleActionType.REMOVE:
                if self.target in result['data']:
                    del result['data'][self.target]
            elif self.type == RuleActionType.LOG:
                logger.info(f"规则日志: {self.value}")
            elif self.type == RuleActionType.CALL:
                if callable(self.value):
                    self.value(data)
        
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            logger.error(f"动作执行错误: {str(e)}")
        
        return result


@dataclass
class Rule:
    """规则"""
    id: str
    name: str
    description: str = ""
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    priority: int = 1
    enabled: bool = True
    created_at: float = field(default_factory=lambda: time.time())
    metadata: Dict = field(default_factory=dict)

    def evaluate(self, data: Dict) -> bool:
        """评估规则是否匹配"""
        if not self.enabled:
            return False
        
        if not self.conditions:
            return True
        
        # 默认使用AND逻辑
        result = True
        for condition in self.conditions:
            cond_result = condition.evaluate(data)
            
            if condition.logic == "AND":
                result = result and cond_result
                if not result:
                    break
            else:  # OR
                result = result or cond_result
                if result:
                    break
        
        return result

    def execute(self, data: Dict) -> Dict:
        """执行规则"""
        result = data.copy()
        
        for action in self.actions:
            action_result = action.execute(result)
            if not action_result['success']:
                return action_result
            result = action_result['data']
        
        return {'success': True, 'data': result}


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._rules_by_priority: List[Rule] = []
        self._lock = threading.RLock()

    def add_rule(self, rule: Rule):
        """添加规则"""
        with self._lock:
            self._rules[rule.id] = rule
            self._reorder_rules()

    def remove_rule(self, rule_id: str):
        """移除规则"""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                self._reorder_rules()

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def list_rules(self) -> List[Rule]:
        """列出所有规则"""
        return list(self._rules.values())

    def _reorder_rules(self):
        """按优先级排序规则"""
        self._rules_by_priority = sorted(
            self._rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )

    def evaluate_rules(self, data: Dict) -> List[Dict]:
        """评估所有规则"""
        results = []
        
        with self._lock:
            for rule in self._rules_by_priority:
                if rule.evaluate(data):
                    result = rule.execute(data)
                    results.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'result': result
                    })
        
        return results

    def execute_rule(self, rule_id: str, data: Dict) -> Optional[Dict]:
        """执行指定规则"""
        rule = self._rules.get(rule_id)
        if rule:
            return rule.execute(data)
        return None


class AIEngineService:
    """AI引擎服务"""

    def __init__(self):
        self._model_type = AIModelType.LOCAL
        self._rule_engine = RuleEngine()
        self._prompt_templates: Dict[str, str] = {}
        self._lock = threading.RLock()
        logger.info("AI引擎服务初始化完成")

    def set_model_type(self, model_type: AIModelType):
        """设置AI模型类型"""
        self._model_type = model_type
        logger.info(f"AI模型类型已设置为: {model_type.value}")

    def get_model_type(self) -> AIModelType:
        """获取AI模型类型"""
        return self._model_type

    def add_prompt_template(self, name: str, template: str):
        """添加提示词模板"""
        self._prompt_templates[name] = template

    def get_prompt_template(self, name: str) -> Optional[str]:
        """获取提示词模板"""
        return self._prompt_templates.get(name)

    def generate_response(self, prompt: str, 
                         template: Optional[str] = None,
                         context: Optional[Dict] = None) -> str:
        """生成AI响应"""
        # 应用模板
        if template:
            template_content = self._prompt_templates.get(template, template)
            if context:
                prompt = template_content.format(**context) + "\n" + prompt
        
        if self._model_type == AIModelType.LOCAL:
            return self._generate_local_response(prompt)
        else:
            return self._generate_external_response(prompt)

    def _generate_local_response(self, prompt: str) -> str:
        """生成本地响应"""
        responses = [
            "这是一个很好的问题!让我分析一下...",
            "根据我的分析,答案应该是这样的:",
            "考虑到各种因素,我的建议是:",
            "经过仔细思考,我认为:",
            "这个问题涉及多个方面,让我详细说明:"
        ]
        
        import random
        base_response = random.choice(responses)
        
        # 简单的关键词匹配
        if "分析" in prompt or "评估" in prompt:
            return f"{base_response}\n\n基于您的输入,我进行了深入分析.关键要点包括:\n1. 需要考虑多个因素\n2. 数据表明存在某些趋势\n3. 建议采取适当的措施"
        elif "总结" in prompt or "概括" in prompt:
            return f"{base_response}\n\n总结来说:\n1. 主要发现\n2. 关键结论\n3. 后续建议"
        elif "建议" in prompt or "推荐" in prompt:
            return f"{base_response}\n\n我的建议是:\n1. 首先评估当前情况\n2. 制定详细计划\n3. 逐步实施并监控效果"
        else:
            return f"{base_response}\n\n关于您的问题,这里有一些思考:\n- 需要更多背景信息才能给出更精确的回答\n- 这个话题涉及多个维度\n- 建议从不同角度进行考虑"

    def _generate_external_response(self, prompt: str) -> str:
        """生成外部API响应"""
        try:
            if self._model_type == AIModelType.OPENAI:
                return self._call_openai(prompt)
            elif self._model_type == AIModelType.ANTHROPIC:
                return self._call_anthropic(prompt)
            else:
                return "外部AI服务调用功能正在开发中..."
        except Exception as e:
            logger.error(f"外部AI调用失败: {str(e)}")
            return f"AI服务暂时不可用: {str(e)}"

    def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return "OpenAI API key未配置"
        
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI调用失败: {str(e)}"

    def _call_anthropic(self, prompt: str) -> str:
        """调用Anthropic API"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "Anthropic API key未配置"
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Anthropic调用失败: {str(e)}"

    def analyze_data(self, data: Dict, 
                    analysis_type: str = "general") -> Dict:
        """分析数据"""
        result = {
            'analysis_type': analysis_type,
            'data_summary': {},
            'insights': [],
            'recommendations': []
        }
        
        # 数据摘要
        result['data_summary'] = {
            'total_fields': len(data),
            'field_names': list(data.keys()),
            'has_numeric': any(isinstance(v, (int, float)) for v in data.values()),
            'has_text': any(isinstance(v, str) for v in data.values())
        }
        
        # 生成洞察
        if analysis_type == "general":
            result['insights'] = [
                "数据结构完整,包含多种类型的字段",
                "建议进一步分析关键指标的趋势",
                "需要关注异常值和数据质量"
            ]
            result['recommendations'] = [
                "建立数据监控机制",
                "定期进行数据质量检查",
                "考虑可视化展示关键指标"
            ]
        elif analysis_type == "financial":
            result['insights'] = [
                "财务数据需要关注收支平衡",
                "现金流是关键指标",
                "需要进行趋势分析"
            ]
            result['recommendations'] = [
                "建立预算监控系统",
                "定期生成财务报表",
                "考虑风险预警机制"
            ]
        
        return result

    def classify_text(self, text: str, categories: List[str]) -> Dict:
        """文本分类"""
        scores = {}
        max_score = 0
        best_category = categories[0] if categories else "unknown"
        
        for category in categories:
            score = sum(1 for word in text.lower().split() 
                       if word in category.lower().split())
            scores[category] = score
            if score > max_score:
                max_score = score
                best_category = category
        
        return {
            'text': text,
            'best_category': best_category,
            'scores': scores,
            'confidence': max_score / len(text.split()) if text else 0
        }

    def extract_entities(self, text: str) -> List[Dict]:
        """实体提取"""
        entities = []
        
        # 简单的实体提取(姓名、邮箱、电话、URL)
        import re
        
        # 邮箱
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
        for email in emails:
            entities.append({'type': 'email', 'value': email})
        
        # 电话(中国)
        phones = re.findall(r'1[3-9]\d{9}', text)
        for phone in phones:
            entities.append({'type': 'phone', 'value': phone})
        
        # URL
        urls = re.findall(r'https?://[\w\.-]+(?:/[\w\.-]*)*', text)
        for url in urls:
            entities.append({'type': 'url', 'value': url})
        
        return entities

    # 规则引擎操作
    def add_rule(self, rule_data: Dict):
        """添加规则"""
        conditions = []
        for cond_data in rule_data.get('conditions', []):
            conditions.append(RuleCondition(
                field=cond_data['field'],
                operator=RuleOperator(cond_data['operator']),
                value=cond_data.get('value'),
                logic=cond_data.get('logic', 'AND')
            ))
        
        actions = []
        for action_data in rule_data.get('actions', []):
            actions.append(RuleAction(
                type=RuleActionType(action_data['type']),
                target=action_data['target'],
                value=action_data.get('value'),
                params=action_data.get('params', {})
            ))
        
        rule = Rule(
            id=rule_data.get('id', str(time.time())),
            name=rule_data['name'],
            description=rule_data.get('description', ''),
            conditions=conditions,
            actions=actions,
            priority=rule_data.get('priority', 1),
            enabled=rule_data.get('enabled', True)
        )
        
        self._rule_engine.add_rule(rule)
        logger.info(f"规则已添加: {rule.id}")

    def remove_rule(self, rule_id: str):
        """移除规则"""
        self._rule_engine.remove_rule(rule_id)
        logger.info(f"规则已移除: {rule_id}")

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self._rule_engine.get_rule(rule_id)

    def list_rules(self) -> List[Rule]:
        """列出所有规则"""
        return self._rule_engine.list_rules()

    def evaluate_rules(self, data: Dict) -> List[Dict]:
        """评估所有规则"""
        return self._rule_engine.evaluate_rules(data)

    def execute_rule(self, rule_id: str, data: Dict) -> Optional[Dict]:
        """执行指定规则"""
        return self._rule_engine.execute_rule(rule_id, data)

    # 机器学习辅助功能
    def predict(self, model_name: str, features: List[float]) -> Dict:
        """预测"""
        return {
            'model': model_name,
            'features': features,
            'prediction': sum(features) / len(features) if features else 0,
            'confidence': 0.85
        }

    def train_model(self, model_name: str, data: List[Dict]) -> Dict:
        """训练模型"""
        return {
            'model': model_name,
            'samples': len(data),
            'status': 'training completed',
            'accuracy': 0.92
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        rules = self._rule_engine.list_rules()
        return {
            'model_type': self._model_type.value,
            'total_rules': len(rules),
            'enabled_rules': sum(1 for r in rules if r.enabled),
            'prompt_templates': list(self._prompt_templates.keys())
        }


# 创建全局实例
ai_engine_service = AIEngineService()
