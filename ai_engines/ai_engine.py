# -*- coding: utf-8 -*-
"""
MTSCOS AI引擎 v5.0 - 升级版本
支持多模型、智能路由、自动故障转移、响应缓存
新增：脑库知识检索、系统规则合规校验、学习反馈闭环
"""

import os
import time
import json
import hashlib
import logging
import sqlite3
import uuid
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from threading import Lock
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ai_engine')

class AIModelType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    CUSTOM = "custom"

class AIRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

class RuleType(Enum):
    VALIDATION = "validation"
    DECISION = "decision"
    FILTER = "filter"
    TRANSFORM = "transform"
    ROUTING = "routing"
    SECURITY = "security"
    RATE_LIMIT = "rate_limit"

class RuleOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    MATCHES = "matches"
    IN = "in"
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"

class ModelStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class AIResponse:
    def __init__(self, content: str, model: str, tokens_used: int = 0, latency: float = 0.0, cached: bool = False):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.latency = latency
        self.cached = cached
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'latency': self.latency,
            'cached': self.cached,
            'timestamp': self.timestamp
        }

class ResponseCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = Lock()
    
    def _generate_key(self, prompt: str, model: str, system_prompt: str = "") -> str:
        return hashlib.md5(f"{prompt}:{model}:{system_prompt}".encode()).hexdigest()
    
    def get(self, prompt: str, model: str, system_prompt: str = "") -> Optional[AIResponse]:
        key = self._generate_key(prompt, model, system_prompt)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self._ttl:
                    return entry['response']
                else:
                    del self._cache[key]
        return None
    
    def set(self, prompt: str, model: str, system_prompt: str, response: AIResponse):
        key = self._generate_key(prompt, model, system_prompt)
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            self._cache[key] = {
                'response': response,
                'timestamp': time.time()
            }
    
    def _evict_oldest(self):
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
        del self._cache[oldest_key]
    
    def clear(self):
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self._max_size
            }

class BrainKnowledgeRetriever:
    """脑库知识检索模块 - 在推理前查询相关知识"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask-app', 'app.db')
        self._lock = Lock()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def search_knowledge(self, query: str, max_results: int = 5, knowledge_type: str = None) -> List[Dict]:
        """搜索脑库知识"""
        results = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            keywords = [k.strip() for k in query.split() if len(k.strip()) > 1]
            
            if knowledge_type:
                cursor.execute('''
                    SELECT knowledge_id, title, content, knowledge_type, tags, priority, created_at
                    FROM ai_brain_knowledge
                    WHERE knowledge_type = ? AND status = 'active'
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                ''', (knowledge_type, max_results))
            else:
                cursor.execute('''
                    SELECT knowledge_id, title, content, knowledge_type, tags, priority, created_at
                    FROM ai_brain_knowledge
                    WHERE status = 'active'
                    ORDER BY priority DESC, created_at DESC
                    LIMIT ?
                ''', (max_results,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                content = row[2][:500] if len(row[2]) > 500 else row[2]
                results.append({
                    'knowledge_id': row[0],
                    'title': row[1],
                    'content': content,
                    'knowledge_type': row[3],
                    'tags': row[4],
                    'priority': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            logger.info(f"[脑库检索] 查询 '{query}' 找到 {len(results)} 条知识")
            
        except Exception as e:
            logger.error(f"[脑库检索] 查询失败: {e}")
        
        return results
    
    def get_system_rules(self) -> List[Dict]:
        """获取系统规则文档"""
        return self.search_knowledge('系统规则', max_results=2, knowledge_type='system_docs')
    
    def get_system_specs(self) -> List[Dict]:
        """获取系统规范文档"""
        return self.search_knowledge('系统规范', max_results=2, knowledge_type='system_docs')
    
    def get_recent_knowledge(self, limit: int = 10) -> List[Dict]:
        """获取最近添加的知识"""
        results = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT knowledge_id, title, content, knowledge_type, tags, priority, created_at
                FROM ai_brain_knowledge
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                content = row[2][:300] if len(row[2]) > 300 else row[2]
                results.append({
                    'knowledge_id': row[0],
                    'title': row[1],
                    'content': content,
                    'knowledge_type': row[3],
                    'tags': row[4],
                    'priority': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[脑库检索] 获取最近知识失败: {e}")
        
        return results
    
    def build_context_prompt(self, query: str) -> str:
        """构建上下文提示词，包含相关脑库知识"""
        knowledge_items = self.search_knowledge(query, max_results=3)
        
        if not knowledge_items:
            return ""
        
        context_parts = ["## 相关知识库内容:\n"]
        for item in knowledge_items:
            context_parts.append(f"- **{item['title']}** (类型: {item['knowledge_type']}, 优先级: {item['priority']}):")
            context_parts.append(f"  {item['content'][:300]}...")
            context_parts.append("")
        
        return "\n".join(context_parts)

class SystemRuleValidator:
    """系统规则合规校验模块 - 在推理过程中检查合规性"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask-app', 'app.db')
        self._lock = Lock()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_active_rules(self) -> List[Dict]:
        """获取所有激活的系统规则"""
        rules = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rule_code, rule_name, rule_value, rule_type, description, priority, is_active
                FROM system_rules
                WHERE is_active = 1
                ORDER BY priority DESC
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                rules.append({
                    'rule_code': row[0],
                    'rule_name': row[1],
                    'rule_value': row[2],
                    'rule_type': row[3],
                    'description': row[4],
                    'priority': row[5],
                    'is_active': row[6]
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[规则校验] 获取规则失败: {e}")
        
        return rules
    
    def validate_response(self, content: str) -> Dict:
        """校验AI响应是否符合系统规则"""
        violations = []
        warnings = []
        
        active_rules = self.get_active_rules()
        
        for rule in active_rules:
            if self._check_rule_violation(rule, content):
                if rule['priority'] >= 8:
                    violations.append({
                        'rule_code': rule['rule_code'],
                        'rule_name': rule['rule_name'],
                        'description': rule['description'],
                        'priority': rule['priority'],
                        'severity': 'critical'
                    })
                elif rule['priority'] >= 5:
                    warnings.append({
                        'rule_code': rule['rule_code'],
                        'rule_name': rule['rule_name'],
                        'description': rule['description'],
                        'priority': rule['priority'],
                        'severity': 'warning'
                    })
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'checked_rules': len(active_rules)
        }
    
    def _check_rule_violation(self, rule: Dict, content: str) -> bool:
        """检查单个规则是否被违反"""
        sensitive_keywords = ['password', '密钥', 'token', '私钥', 'secret']
        
        description_lower = rule.get('description', '').lower()
        
        for keyword in sensitive_keywords:
            if keyword in description_lower and keyword in content.lower():
                return True
        
        if '安全' in rule.get('rule_name', '') or '安全' in description_lower:
            if any(k in content.lower() for k in ['password', '密钥', 'token']):
                return True
        
        return False
    
    def get_compliance_score(self, content: str) -> float:
        """计算合规分数(0-100)"""
        validation = self.validate_response(content)
        
        if len(validation['violations']) > 0:
            return 0.0
        
        total_rules = validation['checked_rules']
        warning_count = len(validation['warnings'])
        
        if total_rules == 0:
            return 100.0
        
        score = 100.0 - (warning_count * 5.0)
        
        return max(0.0, min(100.0, score))

class LearningFeedbackRecorder:
    """学习反馈模块 - 记录推理结果用于自我学习"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flask-app', 'app.db')
        self._lock = Lock()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def record_inference(self, prompt: str, response: str, model: str, latency: float, 
                         compliance_score: float, knowledge_used: List[Dict] = None):
        """记录推理结果"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            inference_id = f"INF-{uuid.uuid4().hex[:12]}"
            knowledge_ids = ",".join(k['knowledge_id'] for k in knowledge_used) if knowledge_used else ""
            
            cursor.execute('''
                INSERT INTO ai_inference_records
                (inference_id, prompt, response, model, latency, compliance_score, 
                 knowledge_used, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                inference_id,
                prompt[:2000],
                response[:5000],
                model,
                latency,
                compliance_score,
                knowledge_ids,
                'completed',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[学习反馈] 记录推理 {inference_id} - 模型: {model}, 延迟: {latency:.2f}s, 合规分数: {compliance_score:.1f}")
            
        except Exception as e:
            logger.error(f"[学习反馈] 记录推理失败: {e}")
    
    def record_learning_opportunity(self, insight: str, topic: str, domain: str, priority: int = 5):
        """记录学习机会"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            insight_id = f"INSIGHT-{uuid.uuid4().hex[:8]}"
            
            cursor.execute('''
                INSERT INTO ai_learning_insights
                (insight_id, insight, topic, domain, priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                insight_id,
                insight,
                topic,
                domain,
                priority,
                'pending',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"[学习反馈] 记录学习机会 {insight_id} - 主题: {topic}, 优先级: {priority}")
            
        except Exception as e:
            logger.error(f"[学习反馈] 记录学习机会失败: {e}")
    
    def get_recent_inferences(self, limit: int = 20) -> List[Dict]:
        """获取最近的推理记录"""
        results = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT inference_id, prompt, response, model, latency, compliance_score, 
                       knowledge_used, status, created_at
                FROM ai_inference_records
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                results.append({
                    'inference_id': row[0],
                    'prompt': row[1][:100],
                    'response': row[2][:200],
                    'model': row[3],
                    'latency': row[4],
                    'compliance_score': row[5],
                    'knowledge_used': row[6],
                    'status': row[7],
                    'created_at': row[8]
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[学习反馈] 获取推理记录失败: {e}")
        
        return results
    
    def get_learning_insights(self, status: str = None) -> List[Dict]:
        """获取学习机会"""
        results = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT insight_id, insight, topic, domain, priority, status, created_at
                    FROM ai_learning_insights
                    WHERE status = ?
                    ORDER BY priority DESC, created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT insight_id, insight, topic, domain, priority, status, created_at
                    FROM ai_learning_insights
                    ORDER BY priority DESC, created_at DESC
                ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                results.append({
                    'insight_id': row[0],
                    'insight': row[1],
                    'topic': row[2],
                    'domain': row[3],
                    'priority': row[4],
                    'status': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[学习反馈] 获取学习机会失败: {e}")
        
        return results

class AIModel:
    def __init__(self, model_type: AIModelType, config: Dict):
        self.type = model_type
        self.name = config.get('name', model_type.value)
        self.endpoint = config.get('endpoint', '')
        self.enabled = config.get('enabled', True)
        self.priority = config.get('priority', 1)
        self.api_key = config.get('api_key', '')
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        self.status = ModelStatus.HEALTHY
        self.last_health_check = None
        self.error_count = 0
        self.consecutive_errors = 0
        self._lock = Lock()
    
    def update_status(self, success: bool, latency: float = 0.0):
        with self._lock:
            if success:
                self.consecutive_errors = 0
                if latency < 1.0:
                    self.status = ModelStatus.HEALTHY
                elif latency < 3.0:
                    self.status = ModelStatus.DEGRADED
                else:
                    self.status = ModelStatus.DEGRADED
            else:
                self.consecutive_errors += 1
                self.error_count += 1
                if self.consecutive_errors >= 3:
                    self.status = ModelStatus.UNHEALTHY
                elif self.consecutive_errors >= 1:
                    self.status = ModelStatus.DEGRADED
            
            self.last_health_check = time.time()
    
    def is_available(self) -> bool:
        with self._lock:
            return self.enabled and self.status != ModelStatus.UNHEALTHY
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'name': self.name,
            'endpoint': self.endpoint,
            'enabled': self.enabled,
            'priority': self.priority,
            'status': self.status.value,
            'error_count': self.error_count,
            'consecutive_errors': self.consecutive_errors
        }

class AIEngine:
    """AI引擎核心类 - v5.0升级版本"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._models: Dict[str, AIModel] = {}
        self._active_model = None
        self._conversation_history: List[Dict] = []
        self._max_history = self.config.get('max_history', 100)
        self._cache = ResponseCache(
            max_size=self.config.get('cache_max_size', 1000),
            ttl_seconds=self.config.get('cache_ttl', 3600)
        )
        self._model_lock = Lock()
        
        self._brain_retriever = BrainKnowledgeRetriever(
            self.config.get('database_path')
        )
        self._rule_validator = SystemRuleValidator(
            self.config.get('database_path')
        )
        self._learning_recorder = LearningFeedbackRecorder(
            self.config.get('database_path')
        )
        
        self._init_models()
    
    def _init_models(self):
        model_configs = self.config.get('models', {})
        
        default_models = {
            AIModelType.OPENAI.value: {
                'name': 'OpenAI GPT-4',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'enabled': True,
                'priority': 1,
                'max_tokens': 8192,
                'temperature': 0.7
            },
            AIModelType.ANTHROPIC.value: {
                'name': 'Anthropic Claude 3',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'enabled': True,
                'priority': 2,
                'max_tokens': 200000,
                'temperature': 0.7
            },
            AIModelType.GOOGLE.value: {
                'name': 'Google Gemini Advanced',
                'endpoint': 'https://generativelanguage.googleapis.com/v1/models',
                'enabled': True,
                'priority': 3,
                'max_tokens': 32768,
                'temperature': 0.7
            },
            AIModelType.LOCAL.value: {
                'name': '本地模型',
                'endpoint': 'http://localhost:8000/v1/chat/completions',
                'enabled': True,
                'priority': 10,
                'max_tokens': 4096,
                'temperature': 0.7
            }
        }
        
        for model_type, config in {**default_models, **model_configs}.items():
            try:
                ai_model_type = AIModelType(model_type)
                self._models[model_type] = AIModel(ai_model_type, config)
            except ValueError:
                logger.warning(f"未知模型类型: {model_type}")
    
    def _select_best_model(self, preferred_model: str = None) -> AIModel:
        with self._model_lock:
            if preferred_model and preferred_model in self._models:
                model = self._models[preferred_model]
                if model.is_available():
                    return model
            
            available_models = [
                m for m in self._models.values()
                if m.is_available()
            ]
            
            if not available_models:
                raise RuntimeError("没有可用的AI模型")
            
            healthy_models = [m for m in available_models if m.status == ModelStatus.HEALTHY]
            if healthy_models:
                return sorted(healthy_models, key=lambda m: m.priority)[0]
            
            return sorted(available_models, key=lambda m: (m.priority, m.consecutive_errors))[0]
    
    def set_active_model(self, model_type: str) -> bool:
        if model_type in self._models:
            with self._model_lock:
                self._active_model = model_type
            logger.info(f"活动模型已切换为: {self._models[model_type].name}")
            return True
        return False
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time()
        }
        if metadata:
            message['metadata'] = metadata
        
        self._conversation_history.append(message)
        
        while len(self._conversation_history) > self._max_history:
            self._conversation_history.pop(0)
    
    def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict]:
        """搜索脑库知识"""
        return self._brain_retriever.search_knowledge(query, max_results)
    
    def validate_compliance(self, content: str) -> Dict:
        """校验合规性"""
        return self._rule_validator.validate_response(content)
    
    def get_compliance_score(self, content: str) -> float:
        """获取合规分数"""
        return self._rule_validator.get_compliance_score(content)
    
    def generate(self, prompt: str, model_type: str = None, **kwargs) -> AIResponse:
        """生成AI响应(支持脑库知识检索和合规校验)"""
        start_time = time.time()
        
        system_prompt = kwargs.get('system_prompt', '你是一个智能助手')
        
        target_model = model_type or self._active_model
        cached_response = self._cache.get(prompt, target_model or "default", system_prompt)
        if cached_response:
            latency = time.time() - start_time
            cached_response.latency = latency
            logger.info(f"缓存命中 - 延迟: {latency:.2f}ms")
            return cached_response
        
        knowledge_context = self._brain_retriever.build_context_prompt(prompt)
        if knowledge_context:
            system_prompt = f"{system_prompt}\n\n{knowledge_context}"
        
        attempts = 0
        max_attempts = len(self._models)
        last_error = None
        
        while attempts < max_attempts:
            try:
                model = self._select_best_model(target_model)
                
                messages = self._build_messages(prompt, system_prompt)
                
                response_content = self._call_model(model, messages, **kwargs)
                
                compliance_score = self._rule_validator.get_compliance_score(response_content)
                validation_result = self._rule_validator.validate_response(response_content)
                
                if not validation_result['is_valid']:
                    logger.warning(f"[合规校验] 响应不合规 - 违反规则: {[v['rule_code'] for v in validation_result['violations']]}")
                    attempts += 1
                    last_error = "响应不合规"
                    continue
                
                latency = time.time() - start_time
                
                model.update_status(True, latency)
                
                response = AIResponse(
                    content=response_content,
                    model=model.name,
                    tokens_used=len(prompt) + len(response_content),
                    latency=latency,
                    cached=False
                )
                
                self._cache.set(prompt, model.type.value, system_prompt, response)
                
                self.add_message(AIRole.ASSISTANT.value, response_content)
                
                used_knowledge = self._brain_retriever.search_knowledge(prompt, max_results=3)
                self._learning_recorder.record_inference(
                    prompt, response_content, model.name, latency,
                    compliance_score, used_knowledge
                )
                
                logger.info(f"AI响应生成完成 - 模型: {response.model}, 延迟: {latency:.2f}s, 合规分数: {compliance_score:.1f}")
                
                return response
            
            except Exception as e:
                attempts += 1
                last_error = e
                
                if target_model and target_model in self._models:
                    self._models[target_model].update_status(False)
                    logger.warning(f"模型 {target_model} 调用失败,尝试备用模型 ({attempts}/{max_attempts}): {str(e)}")
                    target_model = None
                else:
                    logger.error(f"AI调用失败 ({attempts}/{max_attempts}): {str(e)}")
        
        raise RuntimeError(f"所有AI模型调用失败: {str(last_error)}")
    
    def _build_messages(self, prompt: str, system_prompt: str) -> List[Dict]:
        messages = []
        
        messages.append({'role': AIRole.SYSTEM.value, 'content': system_prompt})
        
        history_count = min(10, len(self._conversation_history))
        messages.extend(self._conversation_history[-history_count:])
        
        messages.append({'role': AIRole.USER.value, 'content': prompt})
        
        return messages
    
    def _call_model(self, model: AIModel, messages: List[Dict], **kwargs) -> str:
        return self._simulate_ai_response(messages, model)
    
    def _simulate_ai_response(self, messages: List[Dict], model: AIModel) -> str:
        prompt = messages[-1]['content'] if messages else ""
        
        responses = {
            'question': f"这是一个很好的问题!基于 {model.name} 的分析,答案如下:\n\n根据您的问题,我理解您需要关于'{prompt}'的信息.\n\n要点分析:\n1. 问题核心\n2. 相关背景\n3. 解决方案建议\n\n如需更详细的信息,请告诉我!",
            'help': f"您好!{model.name} 可以帮助您:\n\n🎯 问题解答\n📝 内容生成\n🔍 数据分析\n🤝 智能对话\n\n请问有什么可以帮您的?",
            'generate': f"{model.name} 正在生成内容...\n\n根据您的需求,我已生成以下内容:\n\n---\n生成的内容示例\n---\n\n如果需要调整,请告诉我!",
            'analyze': f"{model.name} 分析结果:\n\n📊 数据分析\n🔍 关键发现\n💡 建议措施\n\n分析完成!",
            'translate': f"{model.name} 翻译结果:\n\n'{prompt}'\n\n(翻译内容)\n\n如需其他语言翻译,请指定目标语言."
        }
        
        if '问题' in prompt or '什么' in prompt or '如何' in prompt:
            return responses['question']
        elif '帮助' in prompt or '你能' in prompt or '功能' in prompt:
            return responses['help']
        elif '生成' in prompt or '创建' in prompt or '写' in prompt:
            return responses['generate']
        elif '分析' in prompt or '评估' in prompt or '报告' in prompt:
            return responses['analyze']
        elif '翻译' in prompt or '英文' in prompt or '中文' in prompt:
            return responses['translate']
        else:
            return f"{model.name} 响应:\n\n'{prompt}'\n\n这是一个有趣的话题!\n\n详细解答和分析如下:\n\n[详细内容]\n\n如有进一步问题,请继续提问."
    
    def clear_history(self):
        self._conversation_history = []
        logger.info("对话历史已清空")
    
    def clear_cache(self):
        self._cache.clear()
        logger.info("响应缓存已清空")
    
    def get_models(self) -> Dict[str, Dict]:
        return {k: v.to_dict() for k, v in self._models.items()}
    
    def get_model_status(self, model_type: str) -> Optional[Dict]:
        if model_type in self._models:
            return self._models[model_type].to_dict()
        return None
    
    def get_history(self) -> List[Dict]:
        return self._conversation_history
    
    def get_cache_stats(self) -> Dict[str, int]:
        return self._cache.get_stats()
    
    def get_recent_knowledge(self, limit: int = 10) -> List[Dict]:
        return self._brain_retriever.get_recent_knowledge(limit)
    
    def get_system_rules(self) -> List[Dict]:
        return self._brain_retriever.get_system_rules()

class Rule:
    def __init__(self, name: str, rule_type: str, condition: Dict, action: Callable, 
                 priority: int = 1, description: str = ""):
        self.name = name
        self.rule_type = rule_type
        self.condition = condition
        self.action = action
        self.priority = priority
        self.description = description
        self.enabled = True
        self.execution_count = 0
        self.last_execution = None
        self.success_count = 0
        self.failure_count = 0
    
    def evaluate(self, data: Dict, context: Dict = None) -> bool:
        if not self.enabled:
            return False
        
        ctx = context or {}
        merged_data = {**ctx, **data}
        
        return self._evaluate_condition(self.condition, merged_data)
    
    def _evaluate_condition(self, condition: Dict, data: Dict) -> bool:
        condition_type = condition.get('type', 'simple')
        
        if condition_type == 'simple':
            return self._evaluate_simple_condition(condition, data)
        elif condition_type == 'compound':
            return self._evaluate_compound_condition(condition, data)
        elif condition_type == 'expression':
            return self._evaluate_expression_condition(condition, data)
        else:
            logger.error(f"不支持的条件类型: {condition_type}")
            return False
    
    def _evaluate_simple_condition(self, condition: Dict, data: Dict) -> bool:
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        case_sensitive = condition.get('case_sensitive', True)
        
        if field not in data:
            return False
        
        data_value = data[field]
        
        try:
            if not case_sensitive and isinstance(data_value, str):
                data_value = str(data_value).lower()
                value = str(value).lower()
            
            if operator == RuleOperator.EQUALS.value:
                return data_value == value
            elif operator == RuleOperator.NOT_EQUALS.value:
                return data_value != value
            elif operator == RuleOperator.CONTAINS.value:
                return value in str(data_value)
            elif operator == RuleOperator.NOT_CONTAINS.value:
                return value not in str(data_value)
            elif operator == RuleOperator.GREATER_THAN.value:
                return float(data_value) > float(value)
            elif operator == RuleOperator.LESS_THAN.value:
                return float(data_value) < float(value)
            elif operator == RuleOperator.GREATER_EQUAL.value:
                return float(data_value) >= float(value)
            elif operator == RuleOperator.LESS_EQUAL.value:
                return float(data_value) <= float(value)
            elif operator == RuleOperator.MATCHES.value:
                import re
                return bool(re.match(value, str(data_value)))
            elif operator == RuleOperator.IN.value:
                return data_value in value
            elif operator == RuleOperator.NOT_IN.value:
                return data_value not in value
            elif operator == RuleOperator.IS_EMPTY.value:
                return data_value is None or str(data_value).strip() == ''
            elif operator == RuleOperator.IS_NOT_EMPTY.value:
                return data_value is not None and str(data_value).strip() != ''
            elif operator == RuleOperator.STARTS_WITH.value:
                return str(data_value).startswith(str(value))
            elif operator == RuleOperator.ENDS_WITH.value:
                return str(data_value).endswith(str(value))
            elif operator == RuleOperator.BETWEEN.value:
                if isinstance(value, list) and len(value) == 2:
                    return float(value[0]) <= float(data_value) <= float(value[1])
                return False
            else:
                logger.error(f"不支持的操作符: {operator}")
                return False
        except Exception as e:
            logger.error(f"条件评估失败: {str(e)}")
            return False
    
    def _evaluate_compound_condition(self, condition: Dict, data: Dict) -> bool:
        operator = condition.get('operator', 'AND').upper()
        conditions = condition.get('conditions', [])
        
        results = [self._evaluate_condition(c, data) for c in conditions]
        
        if operator == 'AND':
            return all(results)
        elif operator == 'OR':
            return any(results)
        elif operator == 'NOT':
            return not all(results)
        else:
            logger.error(f"不支持的复合操作符: {operator}")
            return False
    
    def _evaluate_expression_condition(self, condition: Dict, data: Dict) -> bool:
        expression = condition.get('expression')
        if not expression:
            return False
        
        try:
            local_vars = {k: v for k, v in data.items() if isinstance(v, (int, float, str, bool, list, dict))}
            return eval(expression, {}, local_vars)
        except Exception as e:
            logger.error(f"表达式评估失败: {str(e)}")
            return False
    
    def execute(self, data: Dict, context: Dict = None) -> Any:
        self.execution_count += 1
        self.last_execution = time.time()
        
        if self.evaluate(data, context):
            try:
                result = self.action(data, context)
                self.success_count += 1
                return result
            except Exception as e:
                self.failure_count += 1
                logger.error(f"规则执行失败 [{self.name}]: {e}")
                return None
        return None
    
    def get_stats(self) -> Dict:
        return {
            'name': self.name,
            'type': self.rule_type,
            'enabled': self.enabled,
            'priority': self.priority,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_execution': self.last_execution
        }

class RuleEngine:
    def __init__(self):
        self._rules: Dict[str, List[Rule]] = {}
        self._rule_index: Dict[str, Rule] = {}
        self._rule_sets: Dict[str, List[str]] = {}
        self._lock = Lock()
    
    def add_rule(self, rule: Rule):
        with self._lock:
            if rule.rule_type not in self._rules:
                self._rules[rule.rule_type] = []
            
            self._rules[rule.rule_type].append(rule)
            self._rule_index[rule.name] = rule
            
            self._rules[rule.rule_type].sort(key=lambda r: r.priority, reverse=True)
        
        logger.info(f"规则添加成功: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        with self._lock:
            if rule_name in self._rule_index:
                rule = self._rule_index[rule_name]
                if rule.rule_type in self._rules:
                    self._rules[rule.rule_type] = [r for r in self._rules[rule.rule_type] if r.name != rule_name]
                del self._rule_index[rule_name]
        
        logger.info(f"规则已移除: {rule_name}")
    
    def execute_rules(self, rule_type: str, data: Dict, context: Dict = None) -> List[Dict[str, Any]]:
        results = []
        
        if rule_type not in self._rules:
            return results
        
        for rule in self._rules[rule_type]:
            result = rule.execute(data, context)
            if result is not None:
                results.append({
                    'rule_name': rule.name,
                    'rule_type': rule.rule_type,
                    'priority': rule.priority,
                    'result': result
                })
        
        return results
    
    def execute_all_rules(self, data: Dict, context: Dict = None) -> Dict[str, List[Dict]]:
        results = {}
        
        for rule_type, rule_list in self._rules.items():
            type_results = []
            for rule in rule_list:
                result = rule.execute(data, context)
                if result is not None:
                    type_results.append({
                        'rule_name': rule.name,
                        'priority': rule.priority,
                        'result': result
                    })
            
            if type_results:
                results[rule_type] = type_results
        
        return results
    
    def execute_with_priority(self, data: Dict, context: Dict = None, max_results: int = None) -> List[Dict]:
        all_results = []
        
        for rule_type, rule_list in self._rules.items():
            for rule in rule_list:
                result = rule.execute(data, context)
                if result is not None:
                    all_results.append({
                        'rule_name': rule.name,
                        'rule_type': rule_type,
                        'priority': rule.priority,
                        'result': result
                    })
        
        all_results.sort(key=lambda r: r['priority'], reverse=True)
        
        if max_results:
            return all_results[:max_results]
        
        return all_results
    
    def get_rules(self, rule_type: str = None) -> List[Rule]:
        if rule_type:
            return self._rules.get(rule_type, [])
        else:
            all_rules = []
            for rule_list in self._rules.values():
                all_rules.extend(rule_list)
            return sorted(all_rules, key=lambda r: r.priority, reverse=True)
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        return self._rule_index.get(rule_name)
    
    def enable_rule(self, rule_name: str) -> bool:
        rule = self._rule_index.get(rule_name)
        if rule:
            rule.enabled = True
            logger.info(f"规则已启用: {rule_name}")
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        rule = self._rule_index.get(rule_name)
        if rule:
            rule.enabled = False
            logger.info(f"规则已禁用: {rule_name}")
            return True
        return False
    
    def get_rules_by_priority(self, min_priority: int = None, max_priority: int = None) -> List[Rule]:
        all_rules = []
        for rule_list in self._rules.values():
            for rule in rule_list:
                if (min_priority is None or rule.priority >= min_priority) and \
                   (max_priority is None or rule.priority <= max_priority):
                    all_rules.append(rule)
        return sorted(all_rules, key=lambda r: r.priority, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            'total_rules': 0,
            'rules_by_type': {},
            'enabled_rules': 0,
            'disabled_rules': 0,
            'total_executions': 0,
            'total_successes': 0,
            'total_failures': 0
        }
        
        for rule_type, rule_list in self._rules.items():
            stats['rules_by_type'][rule_type] = len(rule_list)
            stats['total_rules'] += len(rule_list)
            
            for rule in rule_list:
                if rule.enabled:
                    stats['enabled_rules'] += 1
                else:
                    stats['disabled_rules'] += 1
                
                stats['total_executions'] += rule.execution_count
                stats['total_successes'] += rule.success_count
                stats['total_failures'] += rule.failure_count
        
        return stats

class AIEngineManager:
    """AI引擎管理器 - v5.0升级版本"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        self._ai_engine = AIEngine(self.config.get('ai', {}))
        
        self._rule_engine = RuleEngine()
        
        self._init_default_rules()
        
        logger.info("AI引擎管理器 v5.0 初始化完成")
    
    def _init_default_rules(self):
        security_rules = [
            Rule(
                name='block_sensitive_data',
                rule_type=RuleType.SECURITY.value,
                condition={
                    'type': 'compound',
                    'operator': 'OR',
                    'conditions': [
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': 'password'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '密钥'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': 'token'}
                    ]
                },
                action=lambda d, c: {'blocked': True, 'reason': '包含敏感数据'},
                priority=10,
                description='阻止包含敏感信息的请求'
            ),
            Rule(
                name='block_sql_injection',
                rule_type=RuleType.SECURITY.value,
                condition={
                    'type': 'simple',
                    'field': 'content',
                    'operator': 'matches',
                    'value': r'(SELECT|INSERT|UPDATE|DELETE|DROP).*FROM'
                },
                action=lambda d, c: {'blocked': True, 'reason': '疑似SQL注入攻击'},
                priority=10,
                description='阻止疑似SQL注入的请求'
            ),
            Rule(
                name='block_xss_attack',
                rule_type=RuleType.SECURITY.value,
                condition={
                    'type': 'simple',
                    'field': 'content',
                    'operator': 'matches',
                    'value': r'<script[^>]*>.*</script>'
                },
                action=lambda d, c: {'blocked': True, 'reason': '疑似XSS攻击'},
                priority=10,
                description='阻止疑似XSS攻击的请求'
            )
        ]
        
        validation_rules = [
            Rule(
                name='validate_length',
                rule_type=RuleType.VALIDATION.value,
                condition={
                    'type': 'simple',
                    'field': 'content',
                    'operator': 'greater_than',
                    'value': 10000
                },
                action=lambda d, c: {'warning': '内容过长', 'length': len(d.get('content', '')), 'max_allowed': 10000},
                priority=5,
                description='验证内容长度'
            ),
            Rule(
                name='validate_empty',
                rule_type=RuleType.VALIDATION.value,
                condition={
                    'type': 'simple',
                    'field': 'content',
                    'operator': 'is_empty',
                    'value': None
                },
                action=lambda d, c: {'error': '内容不能为空'},
                priority=8,
                description='验证内容非空'
            ),
            Rule(
                name='validate_language',
                rule_type=RuleType.VALIDATION.value,
                condition={
                    'type': 'expression',
                    'expression': "len([c for c in content if '\u4e00' <= c <= '\u9fff']) / len(content) < 0.1 if content else False"
                },
                action=lambda d, c: {'warning': '内容可能不是中文'},
                priority=3,
                description='验证内容语言'
            )
        ]
        
        routing_rules = [
            Rule(
                name='route_to_exam',
                rule_type=RuleType.ROUTING.value,
                condition={
                    'type': 'compound',
                    'operator': 'OR',
                    'conditions': [
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '考试'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '测验'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '试题'}
                    ]
                },
                action=lambda d, c: {'route_to': 'exam_service', 'confidence': 0.9},
                priority=3,
                description='路由到考试服务'
            ),
            Rule(
                name='route_to_search',
                rule_type=RuleType.ROUTING.value,
                condition={
                    'type': 'compound',
                    'operator': 'OR',
                    'conditions': [
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '搜索'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '查找'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '查询'}
                    ]
                },
                action=lambda d, c: {'route_to': 'search_service', 'confidence': 0.8},
                priority=3,
                description='路由到搜索服务'
            ),
            Rule(
                name='route_to_analytics',
                rule_type=RuleType.ROUTING.value,
                condition={
                    'type': 'compound',
                    'operator': 'OR',
                    'conditions': [
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '分析'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '报告'},
                        {'type': 'simple', 'field': 'content', 'operator': 'contains', 'value': '统计'}
                    ]
                },
                action=lambda d, c: {'route_to': 'analytics_service', 'confidence': 0.85},
                priority=3,
                description='路由到分析服务'
            )
        ]
        
        rate_limit_rules = [
            Rule(
                name='rate_limit_check',
                rule_type=RuleType.RATE_LIMIT.value,
                condition={
                    'type': 'simple',
                    'field': 'request_count',
                    'operator': 'greater_than',
                    'value': 100
                },
                action=lambda d, c: {'blocked': True, 'reason': '请求频率超限', 'limit': 100},
                priority=7,
                description='检查请求频率限制'
            )
        ]
        
        for rule in security_rules + validation_rules + routing_rules + rate_limit_rules:
            self._rule_engine.add_rule(rule)
    
    def generate_response(self, prompt: str, **kwargs) -> Dict:
        """生成AI响应(带规则检查和脑库知识检索)"""
        data = {'content': prompt}
        context = kwargs.get('context', {})
        
        security_results = self._rule_engine.execute_rules(RuleType.SECURITY.value, data, context)
        if security_results:
            return {
                'success': False,
                'error': '安全检查失败',
                'details': security_results
            }
        
        rate_limit_results = self._rule_engine.execute_rules(RuleType.RATE_LIMIT.value, data, context)
        if rate_limit_results:
            return {
                'success': False,
                'error': '请求频率超限',
                'details': rate_limit_results
            }
        
        validation_results = self._rule_engine.execute_rules(RuleType.VALIDATION.value, data, context)
        
        routing_results = self._rule_engine.execute_rules(RuleType.ROUTING.value, data, context)
        
        best_route = None
        if routing_results:
            best_route = max(routing_results, key=lambda r: r['result'].get('confidence', 0))
        
        try:
            response = self._ai_engine.generate(prompt, **kwargs)
            
            compliance_score = self._ai_engine.get_compliance_score(response.content)
            compliance_validation = self._ai_engine.validate_compliance(response.content)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': []
            }
        
        result = {
            'success': True,
            'response': response.to_dict(),
            'validation_warnings': validation_results,
            'routing_suggestions': routing_results,
            'selected_route': best_route,
            'compliance_score': compliance_score,
            'compliance_validation': compliance_validation,
            'knowledge_used': self._ai_engine.search_knowledge(prompt, max_results=3)
        }
        
        return result
    
    def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict]:
        """搜索脑库知识"""
        return self._ai_engine.search_knowledge(query, max_results)
    
    def get_system_rules(self) -> List[Dict]:
        """获取系统规则文档"""
        return self._ai_engine.get_system_rules()
    
    def get_recent_knowledge(self, limit: int = 10) -> List[Dict]:
        """获取最近知识"""
        return self._ai_engine.get_recent_knowledge(limit)
    
    def validate_compliance(self, content: str) -> Dict:
        """校验合规性"""
        return self._ai_engine.validate_compliance(content)
    
    def get_compliance_score(self, content: str) -> float:
        """获取合规分数"""
        return self._ai_engine.get_compliance_score(content)
    
    def set_model(self, model_type: str) -> bool:
        return self._ai_engine.set_active_model(model_type)
    
    def get_models(self) -> Dict:
        return self._ai_engine.get_models()
    
    def get_model_status(self, model_type: str) -> Optional[Dict]:
        return self._ai_engine.get_model_status(model_type)
    
    def add_rule(self, rule: Rule):
        self._rule_engine.add_rule(rule)
    
    def get_rules(self, rule_type: str = None) -> List[Rule]:
        return self._rule_engine.get_rules(rule_type)
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        return self._rule_engine.get_rule(rule_name)
    
    def enable_rule(self, rule_name: str) -> bool:
        return self._rule_engine.enable_rule(rule_name)
    
    def disable_rule(self, rule_name: str) -> bool:
        return self._rule_engine.disable_rule(rule_name)
    
    def execute_rules(self, data: Dict, context: Dict = None) -> Dict:
        return self._rule_engine.execute_all_rules(data, context)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'ai_engine': {
                'models': self._ai_engine.get_models(),
                'cache_stats': self._ai_engine.get_cache_stats()
            },
            'rule_engine': self._rule_engine.get_stats(),
            'brain_knowledge': {
                'recent_knowledge_count': len(self._ai_engine.get_recent_knowledge(100))
            }
        }
    
    def clear_cache(self):
        self._ai_engine.clear_cache()
    
    def clear_history(self):
        self._ai_engine.clear_history()

ai_engine_manager = AIEngineManager()

def get_ai_engine_manager() -> AIEngineManager:
    return ai_engine_manager

if __name__ == '__main__':
    print("🚀 AI引擎 v5.0 升级测试")
    print("=" * 70)
    
    manager = AIEngineManager()
    
    print("\n📝 可用AI模型")
    models = manager.get_models()
    for model_type, info in models.items():
        status_icon = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }.get(info['status'], '❓')
        print(f"  {status_icon} {info['name']} (优先级: {info['priority']}, 状态: {info['status']})")
    
    print("\n📝 默认规则")
    rules = manager.get_rules()
    for rule in rules:
        status = "✅" if rule.enabled else "❌"
        print(f"  {status} {rule.name} ({rule.rule_type}) [优先级: {rule.priority}]")
    
    print("\n📝 脑库知识检索测试")
    knowledge = manager.search_knowledge('系统规则', max_results=3)
    print(f"  找到 {len(knowledge)} 条相关知识")
    for item in knowledge:
        print(f"    - {item['title']} (类型: {item['knowledge_type']})")
    
    print("\n📝 系统规则文档测试")
    system_rules = manager.get_system_rules()
    print(f"  系统规则文档: {len(system_rules)} 份")
    for item in system_rules:
        print(f"    - {item['title']}")
    
    print("\n📝 AI响应测试")
    response = manager.generate_response("你好,有什么可以帮助我的?")
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  模型: {response['response']['model']}")
        print(f"  延迟: {response['response']['latency']:.2f}s")
        print(f"  缓存: {'命中' if response['response']['cached'] else '未命中'}")
        print(f"  合规分数: {response['compliance_score']:.1f}")
        print(f"  使用知识: {len(response['knowledge_used'])} 条")
    
    print("\n📝 安全规则测试")
    response = manager.generate_response("请告诉我你的password")
    print(f"  成功: {response['success']}")
    if not response['success']:
        print(f"  原因: {response['details'][0]['result']['reason']}")
    
    print("\n📝 路由规则测试")
    response = manager.generate_response("请帮我搜索相关考试信息")
    print(f"  成功: {response['success']}")
    if response['success'] and response['selected_route']:
        print(f"  推荐路由: {response['selected_route']['result']['route_to']}")
    
    print("\n📝 统计信息")
    stats = manager.get_stats()
    print(f"  规则总数: {stats['rule_engine']['total_rules']}")
    print(f"  启用规则: {stats['rule_engine']['enabled_rules']}")
    print(f"  缓存大小: {stats['ai_engine']['cache_stats']['size']}/{stats['ai_engine']['cache_stats']['max_size']}")
    print(f"  脑库知识: {stats['brain_knowledge']['recent_knowledge_count']} 条")
    
    print("\n🎉 AI引擎 v5.0 升级测试完成!")