#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI模型管理服务
统一管理多个AI模型的配置、调用、切换和负载均衡
"""

import os
import sys
import json
import time
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class AIModel:
    """AI模型"""

    def __init__(self, model_id: str, name: str, provider: str,
                 model_type: str = 'llm', endpoint: str = '',
                 api_key: str = '', max_tokens: int = 4096,
                 temperature: float = 0.7, is_active: bool = True,
                 weight: int = 1):
        self.model_id = model_id
        self.name = name
        self.provider = provider  # openai, anthropic, local, custom
        self.model_type = model_type  # llm, vision, audio, embedding
        self.endpoint = endpoint
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.is_active = is_active
        self.weight = weight

        self.total_calls = 0
        self.total_tokens = 0
        self.total_errors = 0
        self.avg_latency = 0.0
        self.last_used = None
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'name': self.name,
            'provider': self.provider,
            'model_type': self.model_type,
            'endpoint': self.endpoint,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'is_active': self.is_active,
            'weight': self.weight,
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'total_errors': self.total_errors,
            'avg_latency': round(self.avg_latency, 3),
            'last_used': self.last_used,
            'created_at': self.created_at
        }


class ModelGroup:
    """模型组（用于负载均衡和故障转移）"""

    def __init__(self, group_id: str, name: str, strategy: str = 'weighted'):
        self.group_id = group_id
        self.name = name
        self.strategy = strategy  # weighted, round_robin, random, failover
        self.model_ids: List[str] = []
        self._rr_index = 0

    def select_model(self, models: Dict[str, AIModel]) -> Optional[str]:
        """选择模型"""
        active = [m for mid, m in models.items()
                  if mid in self.model_ids and m.is_active]

        if not active:
            return None

        if self.strategy == 'weighted':
            import random
            weights = [m.weight for m in active]
            selected = random.choices(active, weights=weights, k=1)[0]
            return selected.model_id

        elif self.strategy == 'round_robin':
            model = active[self._rr_index % len(active)]
            self._rr_index += 1
            return model.model_id

        elif self.strategy == 'random':
            import random
            return random.choice(active).model_id

        elif self.strategy == 'failover':
            return active[0].model_id

        return active[0].model_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            'group_id': self.group_id,
            'name': self.name,
            'strategy': self.strategy,
            'model_ids': self.model_ids
        }


class AIModelManager:
    """AI模型管理服务"""

    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.groups: Dict[str, ModelGroup] = {}
        self.default_model_id: Optional[str] = None
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_models()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model_type TEXT DEFAULT 'llm',
                    endpoint TEXT,
                    api_key_hash TEXT,
                    max_tokens INTEGER DEFAULT 4096,
                    temperature REAL DEFAULT 0.7,
                    is_active INTEGER DEFAULT 1,
                    weight INTEGER DEFAULT 1,
                    total_calls INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    avg_latency REAL DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    strategy TEXT DEFAULT 'weighted',
                    model_ids TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_call_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    group_id TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    latency REAL DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_models_id ON ai_models(model_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_call_logs_model ON ai_model_call_logs(model_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI模型] 初始化数据库失败: {e}")

    def _register_default_models(self):
        """注册默认模型"""
        defaults = [
            AIModel('model_gpt4', 'GPT-4', 'openai', 'llm',
                   'https://api.openai.com/v1', '', 8192, 0.7, True, 3),
            AIModel('model_gpt35', 'GPT-3.5 Turbo', 'openai', 'llm',
                   'https://api.openai.com/v1', '', 4096, 0.7, True, 2),
            AIModel('model_claude', 'Claude 3', 'anthropic', 'llm',
                   'https://api.anthropic.com', '', 8192, 0.7, True, 3),
            AIModel('model_local', 'Local LLM', 'local', 'llm',
                   'http://127.0.0.1:8080', '', 4096, 0.8, True, 1),
            AIModel('model_embedding', 'Embedding Model', 'local', 'embedding',
                   'http://127.0.0.1:8081', '', 0, 0, True, 1),
            AIModel('model_vision', 'Vision Model', 'local', 'vision',
                   'http://127.0.0.1:8082', '', 0, 0, True, 1),
        ]

        for model in defaults:
            if model.model_id not in self.models:
                self.models[model.model_id] = model
                self._save_model_to_db(model)

        self.default_model_id = 'model_gpt35'

        # 创建默认模型组
        llm_group = ModelGroup('group_llm', 'LLM模型组', 'weighted')
        llm_group.model_ids = ['model_gpt4', 'model_gpt35', 'model_claude', 'model_local']
        self.groups['group_llm'] = llm_group
        self._save_group_to_db(llm_group)

    def _save_model_to_db(self, model: AIModel):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            api_key_hash = hashlib.sha256(model.api_key.encode()).hexdigest()[:16] if model.api_key else ''

            cursor.execute('''
                INSERT OR REPLACE INTO ai_models
                (model_id, name, provider, model_type, endpoint, api_key_hash,
                 max_tokens, temperature, is_active, weight, total_calls,
                 total_tokens, total_errors, avg_latency, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model.model_id, model.name, model.provider, model.model_type,
                model.endpoint, api_key_hash, model.max_tokens, model.temperature,
                1 if model.is_active else 0, model.weight,
                model.total_calls, model.total_tokens, model.total_errors,
                model.avg_latency, model.last_used
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI模型] 保存模型失败: {e}")

    def _save_group_to_db(self, group: ModelGroup):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_model_groups
                (group_id, name, strategy, model_ids)
                VALUES (?, ?, ?, ?)
            ''', (group.group_id, group.name, group.strategy, json.dumps(group.model_ids)))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI模型] 保存模型组失败: {e}")

    def register_model(self, name: str, provider: str, model_type: str = 'llm',
                       endpoint: str = '', api_key: str = '',
                       max_tokens: int = 4096, temperature: float = 0.7,
                       weight: int = 1) -> str:
        """注册模型"""
        import uuid
        model_id = f"model_{uuid.uuid4().hex[:12]}"

        model = AIModel(
            model_id=model_id, name=name, provider=provider,
            model_type=model_type, endpoint=endpoint, api_key=api_key,
            max_tokens=max_tokens, temperature=temperature,
            is_active=True, weight=weight
        )

        with self.lock:
            self.models[model_id] = model

        self._save_model_to_db(model)
        logger(f"[AI模型] 注册模型: {name} ({provider})")

        return model_id

    def get_model(self, model_id: str) -> Optional[AIModel]:
        return self.models.get(model_id)

    def select_model(self, group_id: str = None,
                     model_type: str = None) -> Optional[AIModel]:
        """选择模型"""
        if group_id:
            group = self.groups.get(group_id)
            if group:
                model_id = group.select_model(self.models)
                if model_id:
                    return self.models.get(model_id)

        if model_type:
            candidates = [m for m in self.models.values()
                         if m.is_active and m.model_type == model_type]
            if candidates:
                import random
                weights = [m.weight for m in candidates]
                return random.choices(candidates, weights=weights, k=1)[0]

        return self.models.get(self.default_model_id)

    def call_model(self, model_id: str, prompt: str,
                   max_tokens: int = None, temperature: float = None,
                   **kwargs) -> Dict[str, Any]:
        """调用模型"""
        model = self.models.get(model_id)
        if not model:
            return {'success': False, 'error': 'model_not_found'}

        if not model.is_active:
            return {'success': False, 'error': 'model_inactive'}

        start_time = time.time()

        try:
            # 模拟模型调用
            response_text = f"[{model.name}] 处理请求: {prompt[:100]}..."
            input_tokens = len(prompt) // 4
            output_tokens = len(response_text) // 4
            latency = time.time() - start_time

            with self.lock:
                model.total_calls += 1
                model.total_tokens += input_tokens + output_tokens
                model.last_used = datetime.now().isoformat()

                # 更新平均延迟
                model.avg_latency = (
                    (model.avg_latency * (model.total_calls - 1) + latency) /
                    model.total_calls
                )

            self._log_call(model_id, '', input_tokens, output_tokens,
                          latency, True, '')
            self._save_model_to_db(model)

            return {
                'success': True,
                'model_id': model_id,
                'model_name': model.name,
                'response': response_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'latency': round(latency, 3)
            }

        except Exception as e:
            latency = time.time() - start_time

            with self.lock:
                model.total_errors += 1
                model.total_calls += 1

            self._log_call(model_id, '', 0, 0, latency, False, str(e))
            self._save_model_to_db(model)

            return {'success': False, 'error': str(e), 'model_id': model_id}

    def call_group(self, group_id: str, prompt: str,
                   **kwargs) -> Dict[str, Any]:
        """通过模型组调用（自动负载均衡）"""
        model = self.select_model(group_id)
        if not model:
            return {'success': False, 'error': 'no_available_model'}

        return self.call_model(model.model_id, prompt, **kwargs)

    def _log_call(self, model_id: str, group_id: str,
                  input_tokens: int, output_tokens: int,
                  latency: float, success: bool, error: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ai_model_call_logs
                (model_id, group_id, input_tokens, output_tokens,
                 latency, success, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_id, group_id, input_tokens, output_tokens,
                latency, 1 if success else 0, error
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def set_active(self, model_id: str, is_active: bool) -> bool:
        """启用/禁用模型"""
        with self.lock:
            model = self.models.get(model_id)
            if not model:
                return False
            model.is_active = is_active

        self._save_model_to_db(model)
        return True

    def set_default(self, model_id: str) -> bool:
        """设置默认模型"""
        if model_id not in self.models:
            return False
        self.default_model_id = model_id
        return True

    def create_group(self, name: str, strategy: str = 'weighted',
                     model_ids: List[str] = None) -> str:
        """创建模型组"""
        import uuid
        group_id = f"group_{uuid.uuid4().hex[:8]}"

        group = ModelGroup(group_id, name, strategy)
        group.model_ids = model_ids or []

        with self.lock:
            self.groups[group_id] = group

        self._save_group_to_db(group)
        return group_id

    def get_models(self, model_type: str = None,
                   active_only: bool = False) -> List[Dict[str, Any]]:
        with self.lock:
            models = list(self.models.values())

            if model_type:
                models = [m for m in models if m.model_type == model_type]
            if active_only:
                models = [m for m in models if m.is_active]

            return [m.to_dict() for m in models]

    def get_groups(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [g.to_dict() for g in self.groups.values()]

    def get_call_logs(self, model_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            if model_id:
                cursor.execute('''
                    SELECT * FROM ai_model_call_logs
                    WHERE model_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (model_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM ai_model_call_logs
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except:
            return []

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute('''
                SELECT
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(input_tokens + output_tokens) as total_tokens,
                    AVG(latency) as avg_latency
                FROM ai_model_call_logs
                WHERE created_at >= ?
            ''', (since,))

            row = cursor.fetchone()

            cursor.execute('''
                SELECT model_id, COUNT(*) as calls
                FROM ai_model_call_logs
                WHERE created_at >= ?
                GROUP BY model_id
                ORDER BY calls DESC
            ''', (since,))

            model_usage = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                'hours': hours,
                'total_calls': row[0] or 0,
                'success_rate': round((row[1] or 0) / max(1, row[0] or 1) * 100, 2),
                'total_tokens': row[2] or 0,
                'avg_latency': round(row[3] or 0, 3),
                'model_usage': model_usage
            }
        except:
            return {}

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            active = sum(1 for m in self.models.values() if m.is_active)

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_models': len(self.models),
                'active_models': active,
                'total_groups': len(self.groups),
                'default_model': self.default_model_id
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[AI模型] 模型管理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[AI模型] 模型管理服务已停止")


ai_model_manager = AIModelManager()
